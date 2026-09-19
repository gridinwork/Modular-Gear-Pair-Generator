"""Gear parameter calculations and auto-fill logic."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GearType(str, Enum):
    SPUR = "spur"
    HELICAL = "helical"
    DOUBLE_HELICAL = "double_helical"
    INTERNAL_SPUR = "internal_spur"
    INTERNAL_HELICAL = "internal_helical"
    INTERNAL_DOUBLE_HELICAL = "internal_double_helical"


class HelicalSystem(str, Enum):
    RADIAL = "radial"
    NORMAL = "normal"


class HoleType(str, Enum):
    NONE = "none"
    HOLLOW = "hollow"
    SQUARE = "square"
    HEXAGONAL = "hexagonal"
    CIRCULAR = "circular"
    KEYWAY = "keyway"


EXTERNAL_GEAR_TYPES: tuple[GearType, ...] = (
    GearType.SPUR,
    GearType.HELICAL,
    GearType.DOUBLE_HELICAL,
)

INTERNAL_GEAR_TYPES: tuple[GearType, ...] = (
    GearType.INTERNAL_SPUR,
    GearType.INTERNAL_HELICAL,
    GearType.INTERNAL_DOUBLE_HELICAL,
)

DEFAULT_GEAR_TYPE = GearType.SPUR
DEFAULT_TEETH = 10
DEFAULT_OUTER_DIAMETER_MM = 11.0
DEFAULT_GEAR_LENGTH_MM = 9.0

GEAR_TYPES_UI_ORDER: tuple[GearType, ...] = EXTERNAL_GEAR_TYPES + INTERNAL_GEAR_TYPES

GEAR_TYPE_LABELS = {
    GearType.SPUR: "Прямозубая (зубья снаружи)",
    GearType.HELICAL: "Косозубая (зубья снаружи)",
    GearType.DOUBLE_HELICAL: "Двойная косозубая (зубья снаружи)",
    GearType.INTERNAL_SPUR: "Прямозубая (зубья внутри)",
    GearType.INTERNAL_HELICAL: "Косозубая (зубья внутри)",
    GearType.INTERNAL_DOUBLE_HELICAL: "Двойная косозубая (зубья внутри)",
}

HOLE_TYPE_LABELS = {
    HoleType.NONE: "Без отверстия",
    HoleType.HOLLOW: "Пустотелая (облегчение)",
    HoleType.SQUARE: "Квадратное",
    HoleType.HEXAGONAL: "Шестигранное",
    HoleType.CIRCULAR: "Круглое",
    HoleType.KEYWAY: "Со шпоночным пазом",
}

HELICAL_SYSTEM_LABELS = {
    HelicalSystem.NORMAL: "Нормальный",
    HelicalSystem.RADIAL: "Радиальный",
}


def _is_helical(gear_type: GearType) -> bool:
    return gear_type in (
        GearType.HELICAL,
        GearType.DOUBLE_HELICAL,
        GearType.INTERNAL_HELICAL,
        GearType.INTERNAL_DOUBLE_HELICAL,
    )


def _is_internal(gear_type: GearType) -> bool:
    return gear_type in (
        GearType.INTERNAL_SPUR,
        GearType.INTERNAL_HELICAL,
        GearType.INTERNAL_DOUBLE_HELICAL,
    )


def _is_double_helical(gear_type: GearType) -> bool:
    return gear_type in (GearType.DOUBLE_HELICAL, GearType.INTERNAL_DOUBLE_HELICAL)


@dataclass
class GearParams:
    gear_type: GearType = GearType.SPUR
    teeth: int = 10
    outer_diameter_mm: float = 11.0
    module_mm: Optional[float] = None
    pressure_angle_deg: float = 20.0
    gear_length_mm: float = 9.0
    helix_angle_deg: Optional[float] = None
    clockwise_helix: bool = True
    helical_system: HelicalSystem = HelicalSystem.NORMAL
    profile_shift: Optional[float] = None
    auto_parameters: bool = True
    hole_type: HoleType = HoleType.NONE
    hole_diameter_mm: float = 10.0
    square_hole_size_mm: float = 8.0
    hex_hole_size_mm: float = 10.0
    keyway_bore_diameter_mm: float = 12.0
    key_width_mm: float = 4.0
    key_height_mm: float = 2.0

    pitch_diameter_mm: float = field(init=False, default=0.0)
    root_diameter_mm: float = field(init=False, default=0.0)
    tooth_depth_mm: float = field(init=False, default=0.0)

    def resolve(self) -> "GearParams":
        """Fill missing values and derived diameters."""
        teeth = max(6, int(self.teeth))
        od = max(1.0, float(self.outer_diameter_mm))
        length = max(0.5, float(self.gear_length_mm))

        module = self.module_mm
        if module is None or module <= 0:
            if self.auto_parameters:
                module = od / (teeth + 2)
            else:
                raise ValueError("Укажите модуль или включите автоматический расчёт параметров.")

        module = float(module)
        pressure = 20.0 if self.pressure_angle_deg is None else float(self.pressure_angle_deg)
        shift = 0.0 if self.profile_shift is None else float(self.profile_shift)

        helix = self.helix_angle_deg
        if helix is None:
            helix = 20.0 if _is_helical(self.gear_type) else 0.0
        helix = float(helix)

        if self.helical_system == HelicalSystem.NORMAL and _is_helical(self.gear_type) and helix != 0:
            beta_rad = math.radians(abs(helix))
            module = module / math.cos(beta_rad)

        pitch_d = module * teeth
        tooth_depth = 2.25 * module
        root_d = pitch_d - 2.5 * module
        canonical_od = module * (teeth + 2)
        if self.auto_parameters:
            outer_diameter_mm = od
        else:
            outer_diameter_mm = canonical_od

        resolved = GearParams(
            gear_type=self.gear_type,
            teeth=teeth,
            outer_diameter_mm=outer_diameter_mm,
            module_mm=module,
            pressure_angle_deg=pressure,
            gear_length_mm=length,
            helix_angle_deg=helix,
            clockwise_helix=self.clockwise_helix,
            helical_system=self.helical_system,
            profile_shift=shift,
            auto_parameters=self.auto_parameters,
            hole_type=self.hole_type,
            hole_diameter_mm=self.hole_diameter_mm,
            square_hole_size_mm=self.square_hole_size_mm,
            hex_hole_size_mm=self.hex_hole_size_mm,
            keyway_bore_diameter_mm=self.keyway_bore_diameter_mm,
            key_width_mm=self.key_width_mm,
            key_height_mm=self.key_height_mm,
        )
        resolved.pitch_diameter_mm = pitch_d
        resolved.root_diameter_mm = max(0.5, root_d)
        resolved.tooth_depth_mm = tooth_depth
        return resolved

    @property
    def is_internal(self) -> bool:
        return _is_internal(self.gear_type)

    @property
    def is_helical(self) -> bool:
        return _is_helical(self.gear_type)

    @property
    def is_double_helical(self) -> bool:
        return _is_double_helical(self.gear_type)

    def pitch_radius_mm(self) -> float:
        return self.pitch_diameter_mm / 2.0

    def outer_radius_mm(self) -> float:
        return self.outer_diameter_mm / 2.0

    def root_radius_mm(self) -> float:
        return self.root_diameter_mm / 2.0

    def base_radius_mm(self) -> float:
        pa = math.radians(self.pressure_angle_deg or 20.0)
        shift = self.profile_shift or 0.0
        rp = self.pitch_radius_mm() + shift * (self.module_mm or 1.0)
        return rp * math.cos(pa)


def helix_angle_from_offset(offset_mm: float, gear_length_mm: float) -> float:
    """Compute helix angle in degrees from lateral tooth offset and gear height."""
    if gear_length_mm <= 0:
        raise ValueError("Высота шестерни должна быть больше нуля.")
    return math.degrees(math.atan(abs(offset_mm) / gear_length_mm))


def default_stl_filename(params: GearParams) -> str:
    """Default export filename."""
    gtype = params.gear_type.value
    mod = params.module_mm or 0.0
    return f"gear_{gtype}_{params.teeth}T_{mod:.2f}M.stl"
