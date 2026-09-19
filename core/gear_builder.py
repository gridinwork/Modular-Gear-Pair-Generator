"""
Build 3D gear meshes — CadQuery when available, trimesh/numpy fallback otherwise.
"""

from __future__ import annotations

import logging
import math
from typing import Optional

import numpy as np
import trimesh

from core.gear_math import GearParams, GearType
from core.gear_profiles import full_gear_profile_2d
from core.holes import apply_hole, prepare_gear_polygon

logger = logging.getLogger(__name__)

_CADQUERY_AVAILABLE: Optional[bool] = None


def _check_cadquery() -> bool:
    global _CADQUERY_AVAILABLE
    if _CADQUERY_AVAILABLE is not None:
        return _CADQUERY_AVAILABLE
    try:
        import cadquery  # noqa: F401

        _CADQUERY_AVAILABLE = True
    except ImportError:
        _CADQUERY_AVAILABLE = False
        logger.info("CadQuery not available; using trimesh fallback.")
    return _CADQUERY_AVAILABLE


def _helix_twist_factor(params: GearParams) -> float:
    """Total twist in radians along gear length."""
    beta = math.radians(params.helix_angle_deg or 0.0)
    if not params.is_helical or beta == 0:
        return 0.0
    sign = -1.0 if params.clockwise_helix else 1.0
    r = params.pitch_radius_mm()
    if r <= 0:
        return 0.0
    return sign * math.tan(beta) * params.gear_length_mm / r


def _twist_vertices(
    vertices: np.ndarray,
    height: float,
    total_twist_rad: float,
    double_helical: bool = False,
) -> np.ndarray:
    """Apply linear helix twist along Z."""
    if abs(total_twist_rad) < 1e-9:
        return vertices

    out = vertices.copy()
    z0 = out[:, 2].min()
    z1 = out[:, 2].max()
    span = max(z1 - z0, 1e-6)

    for i, (x, y, z) in enumerate(out):
        t = (z - z0) / span
        if double_helical:
            mid = 0.5
            if t < mid:
                twist = total_twist_rad * (t / mid)
            else:
                twist = total_twist_rad * (1.0 - (t - mid) / mid)
        else:
            twist = total_twist_rad * t
        c, s = math.cos(twist), math.sin(twist)
        out[i, 0] = x * c - y * s
        out[i, 1] = x * s + y * c
    return out


def _finalize_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    try:
        mesh.merge_vertices()
        mesh.remove_unreferenced_vertices()
        mesh.fix_normals()
    except Exception:
        pass
    return mesh


def _extrude_profile(profile: np.ndarray, height: float, params: GearParams) -> trimesh.Trimesh:
    poly = prepare_gear_polygon(profile, params)
    mesh = trimesh.creation.extrude_polygon(poly, height=height)
    return _finalize_mesh(mesh)


def _build_internal_ring_polygon(params: GearParams):
    """Shapely ring: outer rim minus inner toothed cavity."""
    from shapely.geometry import Point, Polygon
    m = params.module_mm or 1.0
    pr = params.pitch_radius_mm()
    tip_r = pr - m
    valley_r = pr + 1.25 * m
    outer_r = params.outer_radius_mm()

    inner_tooth = full_gear_profile_2d(
        teeth=params.teeth,
        pitch_radius=pr,
        outer_radius=valley_r,
        root_radius=tip_r,
        base_radius=params.base_radius_mm(),
        profile_shift=params.profile_shift or 0.0,
        module=m,
        internal=False,
    )
    cavity = Polygon(inner_tooth[:, :2]).buffer(0)
    rim = Point(0, 0).buffer(outer_r)
    ring = rim.difference(cavity)
    if ring.is_empty:
        ring = rim
    if ring.geom_type == "MultiPolygon":
        ring = max(ring.geoms, key=lambda g: g.area)
    return ring


def _build_trimesh(params: GearParams) -> trimesh.Trimesh:
    """Primary mesh builder using trimesh."""
    p = params
    pr = p.pitch_radius_mm()
    orad = p.outer_radius_mm()
    rrad = p.root_radius_mm()
    br = p.base_radius_mm()
    mod = p.module_mm or 1.0
    h = p.gear_length_mm

    if p.is_internal:
        ring = _build_internal_ring_polygon(p)
        mesh = trimesh.creation.extrude_polygon(ring, height=h)
    else:
        profile = full_gear_profile_2d(
            teeth=p.teeth,
            pitch_radius=pr,
            outer_radius=orad,
            root_radius=rrad,
            base_radius=br,
            profile_shift=p.profile_shift or 0.0,
            module=mod,
            pressure_angle_deg=p.pressure_angle_deg or 20.0,
        )
        mesh = _extrude_profile(profile, h, p)

    twist = _helix_twist_factor(p)
    if p.is_helical and abs(twist) > 1e-9:
        mesh.vertices = _twist_vertices(
            mesh.vertices,
            h,
            twist,
            double_helical=p.is_double_helical,
        )
        mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=True)

    mesh = apply_hole(mesh, p)
    return _finalize_mesh(mesh)


def _build_cadquery(params: GearParams) -> trimesh.Trimesh:
    """Build with CadQuery and convert to trimesh."""
    import cadquery as cq

    p = params
    profile = full_gear_profile_2d(
        teeth=p.teeth,
        pitch_radius=p.pitch_radius_mm(),
        outer_radius=p.outer_radius_mm(),
        root_radius=p.root_radius_mm(),
        base_radius=p.base_radius_mm(),
        profile_shift=p.profile_shift or 0.0,
        module=p.module_mm or 1.0,
        internal=p.is_internal,
    )

    pts = [(float(x), float(y)) for x, y in profile[:-1]]
    wp = cq.Workplane("XY").polyline(pts).close()
    solid = wp.extrude(p.gear_length_mm)

    if p.is_helical and (p.helix_angle_deg or 0) != 0:
        beta = math.radians(p.helix_angle_deg or 0)
        twist_deg = math.degrees(
            math.tan(beta) * p.gear_length_mm / max(p.pitch_radius_mm(), 0.1)
        )
        if p.is_double_helical:
            half = p.gear_length_mm / 2
            wp2 = cq.Workplane("XY").polyline(pts).close()
            s1 = wp2.extrude(half, twist=twist_deg / 2)
            s2 = (
                cq.Workplane("XY")
                .workplane(offset=half)
                .polyline(pts)
                .close()
                .extrude(half, twist=-twist_deg / 2)
            )
            solid = s1.union(s2)
        else:
            sign = -1 if p.clockwise_helix else 1
            solid = cq.Workplane("XY").polyline(pts).close().extrude(
                p.gear_length_mm, twist=sign * twist_deg
            )

    mesh = _cq_to_trimesh(solid)
    mesh = apply_hole(mesh, p)
    return mesh


def _cq_to_trimesh(solid) -> trimesh.Trimesh:
    """Export CadQuery solid to trimesh via temporary STL in memory."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        stl_path = Path(tmp) / "part.stl"
        solid.val().exportStl(str(stl_path))
        return trimesh.load(str(stl_path), force="mesh")


def build_gear(params: GearParams, prefer_cadquery: bool = True) -> trimesh.Trimesh:
    """
    Build complete gear mesh.

    Внешняя прямозубая — trimesh (тот же контур, что в preview и STL).
    """
    resolved = params.resolve()

    if resolved.gear_type == GearType.SPUR and not resolved.is_internal:
        return _build_trimesh(resolved)

    if prefer_cadquery and _check_cadquery():
        try:
            return _build_cadquery(resolved)
        except Exception as exc:
            logger.warning("CadQuery build failed: %s", exc)

    return _build_trimesh(resolved)
