"""Компенсация усадки пластика при 3D-печати."""

from __future__ import annotations

from enum import Enum

import numpy as np
import trimesh


class PrintMaterial(str, Enum):
    NOMINAL = "nominal"
    ABS = "abs"
    PETG = "petg"


SHRINKAGE: dict[PrintMaterial, float] = {
    PrintMaterial.NOMINAL: 0.0,
    PrintMaterial.ABS: 0.008,
    PrintMaterial.PETG: 0.005,
}

MATERIAL_LABELS = {
    PrintMaterial.NOMINAL: "Номинальный размер",
    PrintMaterial.ABS: "ABS",
    PrintMaterial.PETG: "PETG",
}


def compensation_scale(shrinkage: float) -> float:
    """Множитель масштаба STL: после печати деталь совпадёт с номиналом."""
    if shrinkage <= 0:
        return 1.0
    if shrinkage >= 0.5:
        raise ValueError("Недопустимое значение усадки.")
    return 1.0 / (1.0 - shrinkage)


def optimize_mesh_for_material(
    mesh: trimesh.Trimesh,
    material: PrintMaterial,
) -> trimesh.Trimesh:
    """Равномерно масштабировать сетку с учётом усадки материала."""
    shrink = SHRINKAGE[material]
    scale = compensation_scale(shrink)
    if abs(scale - 1.0) < 1e-9:
        return mesh.copy()
    out = mesh.copy()
    out.apply_transform(np.diag([scale, scale, scale, 1.0]))
    return out
