"""STL export utilities."""

from __future__ import annotations

from pathlib import Path

import trimesh


def export_stl(mesh: trimesh.Trimesh, filepath: str | Path) -> None:
    """Export mesh to binary STL."""
    if mesh is None or len(mesh.vertices) == 0:
        raise ValueError("Нет модели для экспорта. Сначала создайте предпросмотр.")
    path = Path(filepath)
    if path.suffix.lower() != ".stl":
        path = path.with_suffix(".stl")
    mesh.export(str(path), file_type="stl")
