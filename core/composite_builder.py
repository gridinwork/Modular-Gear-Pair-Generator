"""Сборка составной шестерни из двух частей (верх + низ)."""

from __future__ import annotations

import trimesh

from core.gear_builder import build_gear
from core.gear_math import GearParams


def build_composite_gear(
    upper: GearParams,
    lower: GearParams,
    prefer_cadquery: bool = True,
) -> trimesh.Trimesh:
    """
    Построить две шестерни и объединить по оси Z.
    Верхняя часть: z ∈ [0, h₁], нижняя: z ∈ [h₁, h₁+h₂].
    """
    u = upper.resolve()
    l = lower.resolve()

    mesh_upper = build_gear(u, prefer_cadquery=prefer_cadquery)
    mesh_lower = build_gear(l, prefer_cadquery=prefer_cadquery)

    mesh_lower = mesh_lower.copy()
    z_shift = float(u.gear_length_mm)
    mesh_lower.apply_translation([0.0, 0.0, z_shift])

    combined = trimesh.util.concatenate([mesh_upper, mesh_lower])
    try:
        combined.merge_vertices()
    except Exception:
        pass
    return combined
