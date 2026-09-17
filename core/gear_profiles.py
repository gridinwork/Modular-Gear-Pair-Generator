"""
2D involute spur gear profiles.

Один замкнутый контур: эвольвентные фланки + дуга вершины + дуга впадины.
Если окружность впадин ниже базовой (типично при z ≲ 42 и α=20°), эвольвента
не существует на этом радиусе — фланк доводится до корня радиальной прямой
на том же полярном угле. Так зубья остаются прикреплёнными к диску, а впадины
не затягиваются до базовой окружности.
"""

from __future__ import annotations

import math
from typing import List, Optional

import numpy as np


def _involute_t_at_radius(base_radius: float, radius: float) -> float:
    if base_radius <= 0 or radius <= base_radius:
        return 0.0
    return math.sqrt((radius / base_radius) ** 2 - 1.0)


def _involute_polar_angle(base_radius: float, t: float) -> float:
    if t <= 0:
        return 0.0
    return t - math.atan(t)


def _t_from_involute_angle(inv: float) -> float:
    """Решить t - atan(t) = inv, t ≥ 0."""
    if inv <= 1e-16:
        return 0.0
    t = math.sqrt(max(0.0, 2.0 * inv))
    for _ in range(20):
        f = t - math.atan(t) - inv
        df = (t * t) / (1.0 + t * t) if t else 1e-12
        t = max(0.0, t - f / max(df, 1e-12))
        if abs(f) < 1e-14:
            break
    return t


def _arc_points(radius: float, a0: float, a1: float, n: int) -> np.ndarray:
    """Дуга окружности от a0 к a1 без перехода на длинный путь (>π)."""
    da = a1 - a0
    while da > math.pi:
        da -= 2.0 * math.pi
    while da < -math.pi:
        da += 2.0 * math.pi
    if abs(da) < 1e-12:
        return np.array([[radius * math.cos(a0), radius * math.sin(a0)]])
    angles = np.linspace(a0, a0 + da, max(2, n))
    return np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])


def _tooth_half_angle(radius: float, pitch_radius: float, base_radius: float, psi: float) -> float:
    """
    Половина угловой толщины зуба на радиусе `radius`.

    Ниже базовой окружности эвольвенты нет: угол фиксируется (радиальный участок).
    """
    rb = max(base_radius, 1e-9)
    rp = max(pitch_radius, rb)
    t_p = _involute_t_at_radius(rb, rp)
    inv_p = _involute_polar_angle(rb, t_p)
    if radius <= rb:
        inv_r = 0.0
    else:
        inv_r = _involute_polar_angle(rb, _involute_t_at_radius(rb, radius))
    return psi + inv_p - inv_r


def _pointed_tip_radius(pitch_radius: float, base_radius: float, psi: float, outer_radius: float) -> float:
    """Радиус, на котором фланки сходятся в остриё (half_angle = 0)."""
    rb = max(base_radius, 1e-9)
    ha_outer = _tooth_half_angle(outer_radius, pitch_radius, rb, psi)
    if ha_outer >= 1e-6:
        return outer_radius
    inv_need = psi + _involute_polar_angle(rb, _involute_t_at_radius(rb, max(pitch_radius, rb)))
    t = _t_from_involute_angle(max(0.0, inv_need))
    r_point = rb * math.sqrt(1.0 + t * t)
    return min(outer_radius, max(rb, r_point))


def _flank_radii(root_radius: float, base_radius: float, tip_radius: float, n_flank: int) -> np.ndarray:
    """Радиусы вдоль фланка: радиальный участок (если есть) + эвольвента."""
    rb = max(base_radius, 1e-9)
    rr = max(root_radius, 1e-9)
    ro = max(tip_radius, rb * 1.0001)
    n_flank = max(4, int(n_flank))

    radii: List[float] = []
    if rr < rb * 0.999:
        n_rad = max(2, n_flank // 4)
        radii.extend(np.linspace(rr, rb, n_rad).tolist())
        t1 = _involute_t_at_radius(rb, ro)
        ts = np.linspace(0.0, t1, max(4, n_flank))[1:]
        radii.extend(rb * np.sqrt(1.0 + ts * ts))
    else:
        t0 = _involute_t_at_radius(rb, max(rr, rb))
        t1 = _involute_t_at_radius(rb, ro)
        ts = np.linspace(t0, t1, n_flank)
        radii.extend(rb * np.sqrt(1.0 + ts * ts))
        radii[0] = max(rr, rb)

    out = np.asarray(radii, dtype=np.float64)
    out[0] = rr
    out[-1] = ro
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def _xy(radius: float, angle: float) -> np.ndarray:
    return np.array([radius * math.cos(angle), radius * math.sin(angle)], dtype=np.float64)


def _append_ring(parts: List[np.ndarray], pts: np.ndarray, eps: float = 1e-9) -> None:
    """Добавить цепочку точек, отбрасывая дубликат стыка."""
    pts = np.asarray(pts, dtype=np.float64)
    if pts.size == 0:
        return
    if pts.ndim == 1:
        pts = pts.reshape(1, 2)
    if parts:
        last = parts[-1][-1]
        if np.linalg.norm(pts[0] - last) <= eps:
            pts = pts[1:]
    if len(pts):
        parts.append(pts)


def _force_closed(coords: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    """Уникальные соседние вершины и точное замыкание на первую точку."""
    coords = np.asarray(coords, dtype=np.float64)
    if coords.ndim != 2 or len(coords) < 3:
        return coords
    keep = [0]
    for i in range(1, len(coords)):
        if np.linalg.norm(coords[i] - coords[keep[-1]]) > eps:
            keep.append(i)
    coords = coords[keep]
    if np.linalg.norm(coords[-1] - coords[0]) <= eps:
        coords = coords[:-1]
    if len(coords) < 3:
        raise ValueError("Не удалось построить контур шестерни.")
    return np.vstack([coords, coords[0].copy()])


def _build_external_outline(
    teeth: int,
    pitch_radius: float,
    outer_radius: float,
    root_radius: float,
    base_radius: float,
    psi: float,
    *,
    n_flank: int,
    n_arc: int,
) -> np.ndarray:
    """Один CCW-контур внешней прямозубой шестерни."""
    z = int(teeth)
    pitch = 2.0 * math.pi / z
    rb = max(base_radius, 1e-9)
    rr = max(root_radius, 1e-6)
    ro = _pointed_tip_radius(pitch_radius, rb, psi, outer_radius)
    if ro <= rr:
        raise ValueError(
            "Наружный диаметр меньше диаметра впадин: зубья «переворачиваются» внутрь. "
            "Включите «Автоматический расчёт параметров» или уменьшите модуль / число зубьев."
        )

    radii = _flank_radii(rr, rb, ro, n_flank)
    ha_root = _tooth_half_angle(rr, pitch_radius, rb, psi)
    ha_tip = _tooth_half_angle(ro, pitch_radius, rb, psi)

    min_valley = max(math.radians(1.5), pitch * 0.04)
    if 2.0 * ha_root > pitch - min_valley:
        ha_root = 0.5 * (pitch - min_valley)
    ha_tip = max(0.0, ha_tip)

    parts: List[np.ndarray] = []
    root_clamped = 2.0 * _tooth_half_angle(rr, pitch_radius, rb, psi) > pitch - min_valley
    for i in range(z):
        alpha = i * pitch

        left = np.array(
            [_xy(float(r), alpha - _tooth_half_angle(float(r), pitch_radius, rb, psi)) for r in radii]
        )
        if root_clamped:
            left[0] = _xy(rr, alpha - ha_root)
        _append_ring(parts, left)

        if ha_tip > 1e-6:
            _append_ring(parts, _arc_points(ro, alpha - ha_tip, alpha + ha_tip, n_arc))
        else:
            _append_ring(parts, _xy(ro, alpha).reshape(1, 2))

        right = np.array(
            [_xy(float(r), alpha + _tooth_half_angle(float(r), pitch_radius, rb, psi)) for r in radii[::-1]]
        )
        if root_clamped:
            right[-1] = _xy(rr, alpha + ha_root)
        _append_ring(parts, right)

        _append_ring(
            parts,
            _arc_points(rr, alpha + ha_root, alpha + pitch - ha_root, max(3, n_arc)),
        )

    return _force_closed(np.vstack(parts))


def _clean_outline(loop: np.ndarray) -> np.ndarray:
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient

    poly = Polygon(loop[:, :2])
    if not poly.is_valid or poly.is_empty:
        poly = poly.buffer(0)
    if poly.is_empty:
        raise ValueError("Не удалось построить контур шестерни.")
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    elif poly.geom_type != "Polygon":
        poly = poly.convex_hull
    poly = orient(poly, sign=1.0)
    if poly.is_empty or poly.area <= 0:
        raise ValueError("Не удалось построить контур шестерни.")
    coords = np.asarray(poly.exterior.coords, dtype=np.float64)
    return _force_closed(coords)


def spur_gear_profile_2d(
    teeth: int,
    module: float,
    pressure_angle_deg: float = 20.0,
    profile_shift: float = 0.0,
    outer_radius: Optional[float] = None,
    root_radius: Optional[float] = None,
    pitch_radius: Optional[float] = None,
    *,
    n_flank: int = 20,
    n_arc: int = 6,
) -> np.ndarray:
    """Замкнутый 2D-контур внешней прямозубой шестерни — ровно `teeth` зубьев."""
    z = max(6, int(teeth))
    m = float(module)
    alpha = math.radians(pressure_angle_deg)

    rp = pitch_radius if pitch_radius is not None else m * z / 2.0
    ro = outer_radius if outer_radius is not None else m * (z + 2) / 2.0
    rr = root_radius if root_radius is not None else m * (z - 2.5) / 2.0
    rb = rp * math.cos(alpha)
    rr = max(rr, m * 0.2)
    if ro <= rr:
        raise ValueError(
            "Наружный диаметр меньше диаметра впадин: зубья «переворачиваются» внутрь. "
            "Включите «Автоматический расчёт параметров» или уменьшите модуль / число зубьев."
        )

    psi = math.pi / (2.0 * z) + profile_shift * math.tan(alpha) / z

    n_flank = max(8, min(28, 240 // z))
    n_arc = max(4, min(12, 120 // z))

    loop = _build_external_outline(
        z, rp, ro, rr, rb, psi, n_flank=n_flank, n_arc=n_arc,
    )
    return _clean_outline(loop)


def full_gear_profile_2d(
    teeth: int,
    pitch_radius: float,
    outer_radius: float,
    root_radius: float,
    base_radius: float,
    profile_shift: float = 0.0,
    module: float = 1.0,
    internal: bool = False,
    pressure_angle_deg: float = 20.0,
) -> np.ndarray:
    if internal:
        return spur_gear_profile_2d(
            teeth=teeth,
            module=module,
            profile_shift=profile_shift,
            outer_radius=root_radius,
            root_radius=outer_radius,
            pitch_radius=pitch_radius,
            pressure_angle_deg=pressure_angle_deg,
        )
    return spur_gear_profile_2d(
        teeth=teeth,
        module=module,
        profile_shift=profile_shift,
        outer_radius=outer_radius,
        root_radius=root_radius,
        pitch_radius=pitch_radius,
        pressure_angle_deg=pressure_angle_deg,
    )
