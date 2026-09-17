"""Виджет полей отверстия для одной шестерни."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QGroupBox,
)

from core.gear_math import HoleType, HOLE_TYPE_LABELS, GearParams


class HoleFieldsWidget(QGroupBox):
    """Параметры отверстия (тип и размеры)."""

    def __init__(self, title: str = "Отверстие", parent=None):
        super().__init__(title, parent)
        form = QFormLayout(self)

        self.cmb_hole = QComboBox()
        for ht in HoleType:
            self.cmb_hole.addItem(HOLE_TYPE_LABELS[ht], ht.value)
        self.cmb_hole.setCurrentIndex(list(HoleType).index(HoleType.NONE))
        form.addRow("Тип отверстия:", self.cmb_hole)

        self.edit_hole_d = QLineEdit("10")
        form.addRow("Диаметр, мм:", self.edit_hole_d)

        self.edit_sq = QLineEdit("8")
        form.addRow("Квадрат, мм:", self.edit_sq)

        self.edit_hex = QLineEdit("10")
        form.addRow("Шестигранник, мм:", self.edit_hex)

        self.edit_key_bore = QLineEdit("12")
        form.addRow("Диам. под шпонку, мм:", self.edit_key_bore)

        self.edit_key_w = QLineEdit("4")
        form.addRow("Ширина шпонки, мм:", self.edit_key_w)

        self.edit_key_h = QLineEdit("2")
        form.addRow("Глубина шпонки, мм:", self.edit_key_h)

    def apply_to_params(self, params: GearParams) -> GearParams:
        params.hole_type = HoleType(self.cmb_hole.currentData())
        params.hole_diameter_mm = float(self.edit_hole_d.text().strip() or "10")
        params.square_hole_size_mm = float(self.edit_sq.text().strip() or "8")
        params.hex_hole_size_mm = float(self.edit_hex.text().strip() or "10")
        params.keyway_bore_diameter_mm = float(self.edit_key_bore.text().strip() or "12")
        params.key_width_mm = float(self.edit_key_w.text().strip() or "4")
        params.key_height_mm = float(self.edit_key_h.text().strip() or "2")
        return params

    def load_from_params(self, params: GearParams) -> None:
        idx = list(HoleType).index(params.hole_type)
        self.cmb_hole.setCurrentIndex(idx)
        self.edit_hole_d.setText(str(params.hole_diameter_mm))
        self.edit_sq.setText(str(params.square_hole_size_mm))
        self.edit_hex.setText(str(params.hex_hole_size_mm))
        self.edit_key_bore.setText(str(params.keyway_bore_diameter_mm))
        self.edit_key_w.setText(str(params.key_width_mm))
        self.edit_key_h.setText(str(params.key_height_mm))

    def copy_values_from(self, other: "HoleFieldsWidget") -> None:
        self.cmb_hole.setCurrentIndex(other.cmb_hole.currentIndex())
        self.edit_hole_d.setText(other.edit_hole_d.text())
        self.edit_sq.setText(other.edit_sq.text())
        self.edit_hex.setText(other.edit_hex.text())
        self.edit_key_bore.setText(other.edit_key_bore.text())
        self.edit_key_w.setText(other.edit_key_w.text())
        self.edit_key_h.setText(other.edit_key_h.text())

    def reset_defaults(self) -> None:
        self.cmb_hole.setCurrentIndex(list(HoleType).index(HoleType.NONE))
        self.edit_hole_d.setText("10")
        self.edit_sq.setText("8")
        self.edit_hex.setText("10")
        self.edit_key_bore.setText("12")
        self.edit_key_w.setText("4")
        self.edit_key_h.setText("2")
