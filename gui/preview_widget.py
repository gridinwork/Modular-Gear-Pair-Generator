"""3D preview widget using PyVistaQt."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pyvista as pv
import trimesh
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QSizePolicy, QLabel

try:
    from pyvistaqt import QtInteractor

    PYVISTAQT_AVAILABLE = True
except ImportError:
    QtInteractor = None
    PYVISTAQT_AVAILABLE = False


class PreviewWidget(QFrame):
    """Embedded PyVista 3D viewer with orbit controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._placeholder = QLabel("Здесь появится 3D-предпросмотр после нажатия «Создать предпросмотр»")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._placeholder)

        self._plotter: Optional[QtInteractor] = None
        self._actor = None
        self._mesh: Optional[trimesh.Trimesh] = None

        if PYVISTAQT_AVAILABLE:
            self._init_plotter(layout)
        else:
            self._placeholder.setText(
                "Модуль 3D-предпросмотра недоступен.\n"
                "Переустановите приложение через install.bat."
            )

    def _init_plotter(self, layout: QVBoxLayout) -> None:
        self._placeholder.hide()
        self._plotter = QtInteractor(self)
        self._plotter.set_background("#121218", top="#1a1a22")
        self._plotter.enable_mesh_picking = False
        self._plotter.show_axes()
        self._plotter.show_grid(
            color="#404050",
            location="origin",
        )
        self._plotter.enable_anti_aliasing()
        layout.addWidget(self._plotter.interactor)

    @property
    def current_mesh(self) -> Optional[trimesh.Trimesh]:
        return self._mesh

    def set_mesh(self, mesh: Optional[trimesh.Trimesh]) -> None:
        """Display a trimesh in the viewer."""
        self._mesh = mesh
        if not PYVISTAQT_AVAILABLE or self._plotter is None:
            if mesh is not None:
                self._placeholder.setText(
                    f"Модель: {len(mesh.vertices)} вершин\n"
                    f"(для предпросмотра нужен pyvistaqt)"
                )
                self._placeholder.show()
            return

        self._plotter.clear()
        self._plotter.show_axes()
        self._plotter.show_grid(color="#404050", location="origin")

        if mesh is None or len(mesh.vertices) == 0:
            self._plotter.render()
            return

        vertices = np.asarray(mesh.vertices, dtype=np.float64)
        faces = np.asarray(mesh.faces, dtype=np.int64)
        pv_faces = np.hstack(
            [np.full((len(faces), 1), 3, dtype=np.int64), faces]
        ).ravel()

        poly = pv.PolyData(vertices, pv_faces)
        self._actor = self._plotter.add_mesh(
            poly,
            color="#6a9fd8",
            show_edges=True,
            edge_color="#2a3550",
            smooth_shading=False,
            opacity=1.0,
        )
        self._plotter.reset_camera()
        self._plotter.render()

    def clear(self) -> None:
        self._mesh = None
        if self._plotter is not None:
            self._plotter.clear()
            self._plotter.show_axes()
            self._plotter.show_grid(color="#404050", location="origin")
            self._plotter.render()
