"""Предпросмотр типа шестерни — фотографии из assets/gear_types."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy

from core.gear_math import GearType, GEAR_TYPE_LABELS

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "gear_types"

GEAR_TYPE_IMAGE_FILES: dict[GearType, str] = {
    GearType.SPUR: "spur.png",
    GearType.HELICAL: "helical.png",
    GearType.DOUBLE_HELICAL: "double_helical.png",
    GearType.INTERNAL_SPUR: "internal_spur.png",
    GearType.INTERNAL_HELICAL: "internal_helical.png",
    GearType.INTERNAL_DOUBLE_HELICAL: "internal_double_helical.png",
}


class GearTypePreviewWidget(QWidget):
    """Показывает изображение выбранного типа шестерни."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gear_type = GearType.SPUR
        self.setMinimumHeight(200)
        self.setMaximumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._image = QLabel()
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setMinimumHeight(160)
        self._image.setStyleSheet(
            "background-color: #1a1a22; border: 1px solid #3a3a48; border-radius: 6px;"
        )
        self._image.setScaledContents(False)
        layout.addWidget(self._image)

        self._caption = QLabel()
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._caption.setStyleSheet("color: #9090a8; font-size: 9pt;")
        self._caption.setWordWrap(True)
        layout.addWidget(self._caption)

        self.set_gear_type(GearType.SPUR)

    def set_gear_type(self, gear_type: GearType) -> None:
        self._gear_type = gear_type
        filename = GEAR_TYPE_IMAGE_FILES.get(gear_type, "spur.png")
        path = _ASSETS_DIR / filename
        label = GEAR_TYPE_LABELS.get(gear_type, "")

        if path.is_file():
            pix = QPixmap(str(path))
            if not pix.isNull():
                scaled = pix.scaled(
                    self._image.width() - 8 if self._image.width() > 50 else 360,
                    170,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._image.setPixmap(scaled)
                self._caption.setText(label)
                return

        self._image.setText("Изображение не найдено")
        self._image.setPixmap(QPixmap())
        self._caption.setText(label)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._image.pixmap() and not self._image.pixmap().isNull():
            self.set_gear_type(self._gear_type)
