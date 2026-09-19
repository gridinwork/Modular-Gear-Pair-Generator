"""Hole and bore cutting for gear meshes."""

from __future__ import annotations

import logging
import math

import numpy as np
import trimesh

from core.gear_math import GearParams, HoleType

logger = logging.getLogger(__name__)


def _normalize_polygon(poly):
    """Один Polygon с сохранением внутренних контуров (отверстий)."""
    from shapely.geometry import Polygon

    if poly.is_empty:
        raise ValueError("Контур шестерни пуст после вырезания отверстия.")
    if poly.geom_type == "Polygon":
        return poly
    if poly.geom_type == "MultiPolygon":
        return max(poly.geoms, key=lambda g: g.area)
    return Polygon(poly.convex_hull.exterior.coords)


def prepare_gear_polygon(profile: np.ndarray, params: GearParams):
    """
    Shapely-полигон для экструзии: внешний контур + отверстия (interiors).
    """
    from shapely.geometry import Point, Polygon

    poly = _normalize_polygon(Polygon(profile[:, :2]).buffer(0))

    hole_type = params.hole_type
    if hole_type == HoleType.NONE:
        return poly

    cutter = None

    if hole_type == HoleType.CIRCULAR:
        r = max(0.0, params.hole_diameter_mm / 2.0)
        if r > 0:
            cutter = Point(0, 0).buffer(r, resolution=64)

    elif hole_type == HoleType.HOLLOW:
        r_outer = max(0.0, params.hole_diameter_mm / 2.0)
        wall = max(params.module_mm or 1.0, 1.0)
        r_inner = max(0.0, r_outer - wall)
        if r_outer > 0:
            outer = Point(0, 0).buffer(r_outer, resolution=64)
            inner = Point(0, 0).buffer(r_inner, resolution=64) if r_inner > 0 else None
            cutter = outer if inner is None else outer.difference(inner)

    elif hole_type == HoleType.SQUARE:
        half = max(0.0, params.square_hole_size_mm / 2.0)
        if half > 0:
            cutter = Polygon([(-half, -half), (half, -half), (half, half), (-half, half)])

    elif hole_type == HoleType.HEXAGONAL:
        flat = max(0.0, params.hex_hole_size_mm)
        if flat > 0:
            circum = flat / math.sqrt(3.0)
            angles = np.linspace(0, 2 * math.pi, 6, endpoint=False) + math.pi / 6
            pts = [(circum * math.cos(a), circum * math.sin(a)) for a in angles]
            cutter = Polygon(pts)

    if cutter is None or cutter.is_empty:
        return poly

    try:
        result = _normalize_polygon(poly.difference(cutter))
        if result.is_empty:
            raise ValueError(
                "Отверстие слишком большое для этой шестерни. Уменьшите диаметр отверстия."
            )
        return result
    except ValueError:
        raise
    except Exception as exc:
        logger.warning("2D cut hole failed: %s", exc)
        return poly


def cut_hole_in_profile(profile: np.ndarray, params: GearParams) -> np.ndarray:
    """Совместимость: только внешний контур (без отверстий)."""
    poly = prepare_gear_polygon(profile, params)
    return np.asarray(poly.exterior.coords, dtype=np.float64)


def _extrude_polygon_2d(points: np.ndarray, height: float) -> trimesh.Trimesh:
    from shapely.geometry import Polygon

    poly = Polygon(points[:, :2] if points.ndim > 1 else points)
    return trimesh.creation.extrude_polygon(poly, height=height)


def _regular_polygon(radius: float, sides: int) -> np.ndarray:
    angles = np.linspace(0, 2 * math.pi, sides, endpoint=False) + math.pi / sides
    return np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])


def _cylinder_cutter(radius: float, height: float, segments: int = 64) -> trimesh.Trimesh:
    return trimesh.creation.cylinder(radius=radius, height=height * 1.05, sections=segments)


def _keyway_cutter(
    bore_radius: float,
    key_width: float,
    key_depth: float,
    height: float,
) -> trimesh.Trimesh:
    w = key_width
    d = key_depth
    r = bore_radius
    box = trimesh.creation.box(extents=[w, d * 2, height * 1.05])
    box.apply_translation([r + d / 2, 0, 0])
    return box


def _boolean_difference(mesh: trimesh.Trimesh, cutter: trimesh.Trimesh) -> trimesh.Trimesh:
    """3D-boolean: сначала manifold, затем встроенный difference."""
    try:
        out = trimesh.boolean.difference([mesh, cutter], engine="manifold")
        if isinstance(out, trimesh.Trimesh) and len(out.vertices) > 0:
            return out
    except Exception as exc:
        logger.debug("manifold difference failed: %s", exc)

    try:
        out = mesh.difference(cutter)
        if isinstance(out, trimesh.Trimesh) and len(out.vertices) > 0:
            return out
    except Exception as exc:
        logger.debug("trimesh difference failed: %s", exc)

    return mesh


def apply_hole(mesh: trimesh.Trimesh, params: GearParams) -> trimesh.Trimesh:
    """
    3D-вырез (шпоночный паз и запасной путь).
    Круглые/квадратные/шестигранные отверстия режутся в 2D до экструзии.
    """
    h = params.gear_length_mm
    hole_type = params.hole_type

    if hole_type == HoleType.NONE:
        return mesh

    if hole_type in (HoleType.CIRCULAR, HoleType.SQUARE, HoleType.HEXAGONAL, HoleType.HOLLOW):
        return mesh

    cutters: list[trimesh.Trimesh] = []

    if hole_type == HoleType.KEYWAY:
        bore_r = max(0.1, params.keyway_bore_diameter_mm / 2.0)
        bore = _cylinder_cutter(bore_r, h)
        key = _keyway_cutter(bore_r, params.key_width_mm, params.key_height_mm, h)
        try:
            combined = bore.union(key)
            cutters.append(combined if isinstance(combined, trimesh.Trimesh) else bore)
        except Exception:
            cutters.append(bore)

    if not cutters:
        return mesh

    result = mesh.copy()
    z0, z1 = float(result.bounds[0][2]), float(result.bounds[1][2])
    cz = (z0 + z1) / 2.0

    for cutter in cutters:
        cutter = cutter.copy()
        cutter.apply_translation([0.0, 0.0, cz - h / 2.0])
        result = _boolean_difference(result, cutter)

    if len(result.vertices) == 0:
        raise ValueError("Не удалось вырезать отверстие. Уменьшите диаметр отверстия.")
    return result
