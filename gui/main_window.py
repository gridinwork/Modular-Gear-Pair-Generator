"""Главное окно приложения."""

from __future__ import annotations

from typing import Optional

import trimesh
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QPushButton,
    QSplitter,
    QScrollArea,
    QFileDialog,
    QMessageBox,
    QStatusBar,
    QSpinBox,
    QLabel,
)

from core.export import export_stl
from core.gear_builder import build_gear
from core.composite_builder import build_composite_gear
from core.print_optimize import (
    PrintMaterial,
    SHRINKAGE,
    compensation_scale,
    optimize_mesh_for_material,
)
from core.gear_math import (
    GearParams,
    GearType,
    HelicalSystem,
    DEFAULT_GEAR_TYPE,
    DEFAULT_TEETH,
    DEFAULT_OUTER_DIAMETER_MM,
    DEFAULT_GEAR_LENGTH_MM,
    GEAR_TYPE_LABELS,
    GEAR_TYPES_UI_ORDER,
    HELICAL_SYSTEM_LABELS,
    helix_angle_from_offset,
    default_stl_filename,
)
from gui.dark_theme import DARK_STYLESHEET
from gui.preview_widget import PreviewWidget
from gui.gear_type_preview import GearTypePreviewWidget
from gui.hole_fields import HoleFieldsWidget


def _optional_float(text: str) -> Optional[float]:
    text = text.strip()
    if not text:
        return None
    return float(text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор STL-шестерён")
        self.setMinimumSize(1180, 720)
        self.setStyleSheet(DARK_STYLESHEET)

        self._base_mesh: Optional[trimesh.Trimesh] = None
        self._mesh: Optional[trimesh.Trimesh] = None
        self._last_params: Optional[GearParams] = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        left = self._build_params_panel()
        splitter.addWidget(left)

        self.preview = PreviewWidget()
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([420, 760])

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Готово")

        self._on_gear_type_changed()
        self._on_composite_toggled()

    def _build_params_panel(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(380)
        scroll.setMaximumWidth(480)

        container = QWidget()
        layout = QVBoxLayout(container)

        layout.addWidget(self._group_gear_type())
        layout.addWidget(self._group_dimensions())
        layout.addWidget(self._group_gear2_dimensions())
        layout.addWidget(self._group_helical())
        layout.addWidget(self._group_holes())
        layout.addWidget(self._group_helix_calc())
        layout.addWidget(self._group_actions())
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _group_gear_type(self) -> QGroupBox:
        g = QGroupBox("Шестерня")
        v = QVBoxLayout(g)

        form = QFormLayout()
        self.cmb_gear_type = QComboBox()
        for gt in GEAR_TYPES_UI_ORDER:
            self.cmb_gear_type.addItem(GEAR_TYPE_LABELS[gt], gt.value)
        self.cmb_gear_type.currentIndexChanged.connect(self._on_gear_type_changed)
        self._select_gear_type(DEFAULT_GEAR_TYPE)
        form.addRow("Тип шестерни:", self.cmb_gear_type)

        self.chk_auto = QCheckBox("Автоматический расчёт параметров")
        self.chk_auto.setChecked(True)
        form.addRow("", self.chk_auto)

        self.chk_composite = QCheckBox("Составная шестерня (2 части: сверху + снизу)")
        self.chk_composite.toggled.connect(self._on_composite_toggled)
        form.addRow("", self.chk_composite)

        v.addLayout(form)

        self.gear_type_preview = GearTypePreviewWidget()
        v.addWidget(self.gear_type_preview)

        hint = QLabel("Фото выбранного типа зубчатого венца (для ориентира).")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #808090; font-size: 9pt;")
        v.addWidget(hint)

        return g

    def _group_dimensions(self) -> QGroupBox:
        self.grp_dims1 = QGroupBox("Размеры")
        form = QFormLayout(self.grp_dims1)

        self.spin_teeth = QSpinBox()
        self.spin_teeth.setRange(6, 500)
        self.spin_teeth.setValue(DEFAULT_TEETH)
        form.addRow("Число зубьев:", self.spin_teeth)

        self.edit_od = QLineEdit(f"{DEFAULT_OUTER_DIAMETER_MM:g}")
        form.addRow("Наружный диаметр, мм:", self.edit_od)

        self.edit_module = QLineEdit("")
        form.addRow("Модуль, мм:", self.edit_module)
        mod_hint = QLabel(
            "Модуль — размер зуба (мм), не «внутрь/наружу». "
            "Направление зубьев задаёт тип шестерни выше."
        )
        mod_hint.setWordWrap(True)
        mod_hint.setStyleSheet("color: #808090; font-size: 9pt;")
        form.addRow("", mod_hint)

        self.edit_pa = QLineEdit("20")
        form.addRow("Угол зацепления, °:", self.edit_pa)

        self.edit_length = QLineEdit(f"{DEFAULT_GEAR_LENGTH_MM:g}")
        form.addRow("Длина / высота, мм:", self.edit_length)

        self.edit_shift = QLineEdit("")
        form.addRow("Смещение профиля:", self.edit_shift)

        return self.grp_dims1

    def _group_gear2_dimensions(self) -> QGroupBox:
        self.grp_dims2 = QGroupBox("Шестерня 2 (снизу)")
        form = QFormLayout(self.grp_dims2)

        self.spin_teeth2 = QSpinBox()
        self.spin_teeth2.setRange(6, 500)
        self.spin_teeth2.setValue(20)
        form.addRow("Число зубьев:", self.spin_teeth2)

        self.edit_od2 = QLineEdit("44")
        form.addRow("Наружный диаметр, мм:", self.edit_od2)

        self.edit_length2 = QLineEdit("10")
        form.addRow("Длина / высота, мм:", self.edit_length2)

        return self.grp_dims2

    def _group_helical(self) -> QGroupBox:
        g = QGroupBox("Косозубость")
        form = QFormLayout(g)

        self.edit_helix = QLineEdit("")
        form.addRow("Угол наклона зуба, °:", self.edit_helix)

        self.chk_cw = QCheckBox("Наклон по часовой стрелке")
        self.chk_cw.setChecked(True)
        form.addRow("", self.chk_cw)

        self.cmb_helical_sys = QComboBox()
        for hs in HelicalSystem:
            self.cmb_helical_sys.addItem(HELICAL_SYSTEM_LABELS[hs], hs.value)
        form.addRow("Система косозубости:", self.cmb_helical_sys)

        return g

    def _group_holes(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)

        self.chk_same_holes = QCheckBox("Одинаковые отверстия у обеих частей")
        self.chk_same_holes.setChecked(True)
        self.chk_same_holes.toggled.connect(self._on_same_holes_toggled)
        v.addWidget(self.chk_same_holes)

        self.holes1 = HoleFieldsWidget("Отверстие — шестерня 1 (сверху)")
        self.holes2 = HoleFieldsWidget("Отверстие — шестерня 2 (снизу)")
        v.addWidget(self.holes1)
        v.addWidget(self.holes2)

        self.holes1.cmb_hole.currentIndexChanged.connect(self._sync_holes_if_linked)
        for w in (
            self.holes1.edit_hole_d,
            self.holes1.edit_sq,
            self.holes1.edit_hex,
            self.holes1.edit_key_bore,
            self.holes1.edit_key_w,
            self.holes1.edit_key_h,
        ):
            w.textChanged.connect(self._sync_holes_if_linked)

        return wrap

    def _group_helix_calc(self) -> QGroupBox:
        g = QGroupBox("Калькулятор угла наклона зуба")
        form = QFormLayout(g)

        self.edit_offset = QLineEdit("0")
        form.addRow("Боковое смещение зуба, мм:", self.edit_offset)

        btn = QPushButton("Рассчитать угол наклона")
        btn.clicked.connect(self._on_calc_helix)
        form.addRow("", btn)

        return g

    def _group_actions(self) -> QGroupBox:
        g = QGroupBox("Действия")
        v = QVBoxLayout(g)

        btn_gen = QPushButton("Создать предпросмотр")
        btn_gen.clicked.connect(self._on_generate)
        v.addWidget(btn_gen)

        exp_label = QLabel("Скачать STL (предпросмотр всегда без усадки):")
        exp_label.setStyleSheet("color: #a0a0b0; font-weight: normal;")
        v.addWidget(exp_label)

        self.btn_exp_nominal = QPushButton("Скачать STL — номинальный размер")
        self.btn_exp_nominal.clicked.connect(
            lambda: self._on_export_material(PrintMaterial.NOMINAL)
        )
        v.addWidget(self.btn_exp_nominal)

        self.btn_exp_abs = QPushButton("Скачать STL — для ABS (усадка 0,8 %)")
        self.btn_exp_abs.clicked.connect(
            lambda: self._on_export_material(PrintMaterial.ABS)
        )
        v.addWidget(self.btn_exp_abs)

        self.btn_exp_petg = QPushButton("Скачать STL — для PETG (усадка 0,5 %)")
        self.btn_exp_petg.clicked.connect(
            lambda: self._on_export_material(PrintMaterial.PETG)
        )
        v.addWidget(self.btn_exp_petg)

        for b in (self.btn_exp_nominal, self.btn_exp_abs, self.btn_exp_petg):
            b.setEnabled(False)

        self._export_buttons = (self.btn_exp_nominal, self.btn_exp_abs, self.btn_exp_petg)

        btn_rst = QPushButton("Сброс")
        btn_rst.setObjectName("btnReset")
        btn_rst.clicked.connect(self._on_reset)
        v.addWidget(btn_rst)

        return g

    def _select_gear_type(self, gear_type: GearType) -> None:
        for i in range(self.cmb_gear_type.count()):
            if self.cmb_gear_type.itemData(i) == gear_type.value:
                self.cmb_gear_type.setCurrentIndex(i)
                return

    def _on_gear_type_changed(self) -> None:
        gt = GearType(self.cmb_gear_type.currentData())
        self.gear_type_preview.set_gear_type(gt)

    def _on_composite_toggled(self) -> None:
        composite = self.chk_composite.isChecked()
        self.grp_dims2.setVisible(composite)
        self.grp_dims1.setTitle(
            "Шестерня 1 (сверху)" if composite else "Размеры"
        )
        self.holes1.setTitle(
            "Отверстие — шестерня 1 (сверху)" if composite else "Отверстие"
        )
        self.holes2.setVisible(composite)
        self.chk_same_holes.setVisible(composite)
        if composite:
            self._on_same_holes_toggled()
        else:
            self.holes2.setEnabled(True)

    def _on_same_holes_toggled(self) -> None:
        if not self.chk_composite.isChecked():
            return
        linked = self.chk_same_holes.isChecked()
        self.holes2.setEnabled(not linked)
        if linked:
            self.holes2.copy_values_from(self.holes1)

    def _sync_holes_if_linked(self) -> None:
        if self.chk_composite.isChecked() and self.chk_same_holes.isChecked():
            self.holes2.copy_values_from(self.holes1)

    def _common_params(self) -> dict:
        gear_type = GearType(self.cmb_gear_type.currentData())
        helical_sys = HelicalSystem(self.cmb_helical_sys.currentData())
        return dict(
            gear_type=gear_type,
            module_mm=_optional_float(self.edit_module.text()),
            pressure_angle_deg=_optional_float(self.edit_pa.text()),
            helix_angle_deg=_optional_float(self.edit_helix.text()),
            clockwise_helix=self.chk_cw.isChecked(),
            helical_system=helical_sys,
            profile_shift=_optional_float(self.edit_shift.text()),
            auto_parameters=self.chk_auto.isChecked(),
        )

    def _params_from_dims(
        self,
        teeth: int,
        od: float,
        length: float,
        holes: HoleFieldsWidget,
    ) -> GearParams:
        p = GearParams(
            **self._common_params(),
            teeth=teeth,
            outer_diameter_mm=od,
            gear_length_mm=length,
        )
        return holes.apply_to_params(p)

    def _collect_params(self) -> GearParams | tuple[GearParams, GearParams]:
        if not self.chk_composite.isChecked():
            return self._params_from_dims(
                self.spin_teeth.value(),
                float(self.edit_od.text().strip() or str(DEFAULT_OUTER_DIAMETER_MM)),
                float(self.edit_length.text().strip() or str(DEFAULT_GEAR_LENGTH_MM)),
                self.holes1,
            )

        upper = self._params_from_dims(
            self.spin_teeth.value(),
            float(self.edit_od.text().strip() or str(DEFAULT_OUTER_DIAMETER_MM)),
            float(self.edit_length.text().strip() or str(DEFAULT_GEAR_LENGTH_MM)),
            self.holes1,
        )
        lower = self._params_from_dims(
            self.spin_teeth2.value(),
            float(self.edit_od2.text().strip() or "44"),
            float(self.edit_length2.text().strip() or "10"),
            self.holes2,
        )
        return upper, lower

    def _set_mesh_ready(self, base_mesh: trimesh.Trimesh, params_info: str) -> None:
        self._base_mesh = base_mesh
        self._mesh = base_mesh.copy()
        self.preview.set_mesh(self._mesh)
        for b in self._export_buttons:
            b.setEnabled(True)
        self.status.showMessage(params_info)

    def _on_calc_helix(self) -> None:
        try:
            offset = float(self.edit_offset.text().strip() or "0")
            length = float(self.edit_length.text().strip() or "10")
            angle = helix_angle_from_offset(offset, length)
            self.edit_helix.setText(f"{angle:.3f}")
            self.status.showMessage(f"Угол наклона зуба: {angle:.3f}°")
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка расчёта", str(exc))

    def _on_generate(self) -> None:
        try:
            collected = self._collect_params()
            self.status.showMessage("Построение модели…")
            self.repaint()

            if isinstance(collected, tuple):
                upper, lower = collected
                upper_r, lower_r = upper.resolve(), lower.resolve()
                mesh = build_composite_gear(upper_r, lower_r)
                self._last_params = upper_r
                info = (
                    f"Составная: верх {upper_r.teeth} зуб. × {upper_r.gear_length_mm:.1f} мм + "
                    f"низ {lower_r.teeth} зуб. × {lower_r.gear_length_mm:.1f} мм, "
                    f"{len(mesh.vertices)} вершин"
                )
            else:
                resolved = collected.resolve()
                self._last_params = resolved
                mesh = build_gear(resolved)
                mod = resolved.module_mm or 0
                info = (
                    f"Готово: {resolved.teeth} зуб., модуль {mod:.3f} мм, "
                    f"{len(mesh.vertices)} вершин"
                )

            self._set_mesh_ready(mesh, info)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка генерации", str(exc))
            self.status.showMessage("Ошибка генерации")

    def _default_export_basename(self) -> str:
        if self.chk_composite.isChecked():
            return "gear_composite"
        params = self._last_params
        if params is None:
            collected = self._collect_params()
            if isinstance(collected, tuple):
                params = collected[0].resolve()
            else:
                params = collected.resolve()
        return default_stl_filename(params).removesuffix(".stl")

    def _on_export_material(self, material: PrintMaterial) -> None:
        if self._base_mesh is None or len(self._base_mesh.vertices) == 0:
            QMessageBox.warning(
                self,
                "Экспорт",
                "Нет модели для экспорта. Сначала нажмите «Создать предпросмотр».",
            )
            return

        suffix = ""
        title = "Экспорт STL — номинальный размер"
        if material == PrintMaterial.ABS:
            suffix = "_ABS"
            title = "Экспорт STL — компенсация усадки ABS (0,8 %)"
        elif material == PrintMaterial.PETG:
            suffix = "_PETG"
            title = "Экспорт STL — компенсация усадки PETG (0,5 %)"

        default_name = self._default_export_basename() + suffix + ".stl"

        path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            default_name,
            "Файлы STL (*.stl)",
        )
        if not path:
            return

        try:
            mesh = optimize_mesh_for_material(self._base_mesh, material)
            export_stl(mesh, path)
            shrink = SHRINKAGE[material] * 100
            scale = compensation_scale(SHRINKAGE[material])
            extra = (
                f"\nМасштаб ×{scale:.4f} (компенсация усадки {shrink:.2f} %)"
                if material != PrintMaterial.NOMINAL
                else "\nБез компенсации усадки"
            )
            self.status.showMessage(f"Экспортировано: {path}")
            QMessageBox.information(
                self,
                "Экспорт",
                f"Файл сохранён:\n{path}{extra}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка экспорта", str(exc))

    def _on_reset(self) -> None:
        self._select_gear_type(DEFAULT_GEAR_TYPE)
        self.chk_auto.setChecked(True)
        self.chk_composite.setChecked(False)
        self.spin_teeth.setValue(DEFAULT_TEETH)
        self.edit_od.setText(f"{DEFAULT_OUTER_DIAMETER_MM:g}")
        self.edit_module.clear()
        self.edit_pa.setText("20")
        self.edit_length.setText(f"{DEFAULT_GEAR_LENGTH_MM:g}")
        self.edit_shift.clear()
        self.spin_teeth2.setValue(20)
        self.edit_od2.setText("44")
        self.edit_length2.setText("10")
        self.edit_helix.clear()
        self.chk_cw.setChecked(True)
        self.cmb_helical_sys.setCurrentIndex(0)
        self.chk_same_holes.setChecked(True)
        self.holes1.reset_defaults()
        self.holes2.reset_defaults()
        self.edit_offset.setText("0")
        self._base_mesh = None
        self._mesh = None
        self._last_params = None
        for b in self._export_buttons:
            b.setEnabled(False)
        self.preview.clear()
        self._on_gear_type_changed()
        self._on_composite_toggled()
        self.status.showMessage("Параметры сброшены")
