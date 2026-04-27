from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QSettings

from HjemmeladingApp.utils import units

GRAIN_TO_GRAM = 0.06479891
PSI_TO_BAR = 0.0689475729
PSI_TO_MPA = 0.00689475729


def _settings() -> QSettings:
    return QSettings("ReloadingWorkshop", "ReloadingManager")


def _global_system() -> str:
    return str(_settings().value("units/global", "metric") or "metric").strip().lower()


def get_distance_unit() -> str:
    value = str(_settings().value("units/distance", "") or "").strip()
    if value:
        return value
    return "Yards" if _global_system() == "imperial" else "Meter"


def get_temperature_unit() -> str:
    value = str(_settings().value("units/temperature", "") or "").strip()
    if value:
        return value
    return "Fahrenheit" if _global_system() == "imperial" else "Celsius"


def get_measurement_unit() -> str:
    value = str(_settings().value("units/measurement", "") or "").strip()
    if value:
        return value
    return "Tommer (inches)" if _global_system() == "imperial" else "Millimeter (mm)"


def get_velocity_unit() -> str:
    value = str(_settings().value("units/velocity", "") or "").strip()
    if value:
        return value
    return "fps" if _global_system() == "imperial" else "m/s"


def get_bullet_weight_unit() -> str:
    value = str(_settings().value("units/bullet_weight", "") or "").strip()
    if value:
        return value
    return "Grain (gr)"


def get_powder_weight_unit() -> str:
    value = str(_settings().value("units/powder_weight", "") or "").strip()
    if value:
        return value
    return "Grain (gr)"


def get_pressure_unit() -> str:
    value = str(_settings().value("units/pressure", "") or "").strip()
    if value:
        return value
    return "PSI"


def pressure_kpa_to_display_value(value_kpa: Any) -> float | None:
    try:
        kpa_value = float(value_kpa)
    except Exception:
        return None
    pressure_unit = get_pressure_unit().lower()
    if pressure_unit == "bar":
        return kpa_value / 100.0
    if pressure_unit == "mpa":
        return kpa_value / 1000.0
    if pressure_unit == "psi":
        return kpa_value * 0.1450377377
    return kpa_value


def pressure_display_to_kpa(value: Any) -> float | None:
    try:
        display_value = float(value)
    except Exception:
        return None
    pressure_unit = get_pressure_unit().lower()
    if pressure_unit == "bar":
        return display_value * 100.0
    if pressure_unit == "mpa":
        return display_value * 1000.0
    if pressure_unit == "psi":
        return display_value / 0.1450377377
    return display_value


def get_pressure_suffix() -> str:
    pressure_unit = get_pressure_unit().lower()
    if pressure_unit == "bar":
        return " bar"
    if pressure_unit == "mpa":
        return " MPa"
    if pressure_unit == "psi":
        return " psi"
    return " kPa"


def get_group_size_unit() -> str:
    value = str(_settings().value("units/group_size", "") or "").strip()
    if value:
        return value
    return "Millimeter (mm)"


def get_twist_unit() -> str:
    value = str(_settings().value("units/twist", "") or "").strip()
    if value:
        return value
    return 'Turns per inch (1:11")'


def format_velocity_fps(value_fps: Any) -> str:
    try:
        fps_value = float(value_fps)
    except Exception:
        return str(value_fps) if value_fps not in (None, "") else "N/A"
    velocity_unit = get_velocity_unit().lower()
    if velocity_unit == "m/s":
        return f"{units.fps_to_mps(fps_value):.1f} m/s ({fps_value:.1f} fps)"
    return f"{fps_value:.1f} fps"


def format_velocity_delta_fps(value_fps: Any) -> str:
    try:
        fps_value = float(value_fps)
    except Exception:
        return str(value_fps) if value_fps not in (None, "") else "N/A"
    velocity_unit = get_velocity_unit().lower()
    if velocity_unit == "m/s":
        return f"{units.fps_to_mps(fps_value):+.1f} m/s ({fps_value:+.1f} fps)"
    return f"{fps_value:+.1f} fps"


def format_velocity_rate_fps_per_gr(value_fps_per_gr: Any) -> str:
    try:
        rate = float(value_fps_per_gr)
    except Exception:
        return str(value_fps_per_gr) if value_fps_per_gr not in (None, "") else "N/A"
    velocity_unit = get_velocity_unit().lower()
    powder_unit = get_powder_weight_unit().lower()
    if velocity_unit == "m/s" and "gram" in powder_unit:
        converted = units.fps_to_mps(rate) / GRAIN_TO_GRAM
        return f"{converted:+.1f} m/s/g ({rate:+.1f} fps/gr)"
    if velocity_unit == "m/s":
        converted = units.fps_to_mps(rate)
        return f"{converted:+.1f} m/s/gr ({rate:+.1f} fps/gr)"
    if "gram" in powder_unit:
        converted = rate / GRAIN_TO_GRAM
        return f"{converted:+.1f} fps/g ({rate:+.1f} fps/gr)"
    return f"{rate:+.1f} fps/gr"


def format_velocity_rate_fps_per_c(value_fps_per_c: Any) -> str:
    try:
        rate = float(value_fps_per_c)
    except Exception:
        return str(value_fps_per_c) if value_fps_per_c not in (None, "") else "N/A"
    velocity_unit = get_velocity_unit().lower()
    temperature_unit = get_temperature_unit().lower()
    if velocity_unit == "m/s" and temperature_unit.startswith("f"):
        converted = units.fps_to_mps(rate) / 1.8
        return f"{converted:+.2f} m/s/°F ({rate:+.1f} fps/°C)"
    if velocity_unit == "m/s":
        converted = units.fps_to_mps(rate)
        return f"{converted:+.2f} m/s/°C ({rate:+.1f} fps/°C)"
    if temperature_unit.startswith("f"):
        converted = rate / 1.8
        return f"{converted:+.1f} fps/°F ({rate:+.1f} fps/°C)"
    return f"{rate:+.1f} fps/°C"


def format_temperature_c(value_c: Any) -> str:
    try:
        temp_c = float(value_c)
    except Exception:
        return str(value_c) if value_c not in (None, "") else "N/A"
    temperature_unit = get_temperature_unit().lower()
    if temperature_unit.startswith("f"):
        return f"{units.celsius_to_fahrenheit(temp_c):.1f} °F ({temp_c:.1f} °C)"
    return f"{temp_c:.1f} °C"


def format_temperature_delta_c(value_c: Any) -> str:
    try:
        temp_c = float(value_c)
    except Exception:
        return str(value_c) if value_c not in (None, "") else "N/A"
    temperature_unit = get_temperature_unit().lower()
    if temperature_unit.startswith("f"):
        return f"{(temp_c * 9.0 / 5.0):+.1f} °F ({temp_c:+.1f} °C)"
    return f"{temp_c:+.1f} °C"


def temperature_c_to_display_value(value_c: Any) -> float | None:
    try:
        temp_c = float(value_c)
    except Exception:
        return None
    temperature_unit = get_temperature_unit().lower()
    if temperature_unit.startswith("f"):
        return units.celsius_to_fahrenheit(temp_c)
    return temp_c


def temperature_display_to_c(value: Any) -> float | None:
    try:
        display_value = float(value)
    except Exception:
        return None
    temperature_unit = get_temperature_unit().lower()
    if temperature_unit.startswith("f"):
        return units.fahrenheit_to_celsius(display_value)
    return display_value


def get_temperature_suffix() -> str:
    temperature_unit = get_temperature_unit().lower()
    return " °F" if temperature_unit.startswith("f") else " °C"


def format_distance_m(value_m: Any) -> str:
    try:
        distance_m = float(value_m)
    except Exception:
        return str(value_m) if value_m not in (None, "") else "N/A"
    distance_unit = get_distance_unit().lower()
    if distance_unit.startswith("yard"):
        return f"{units.meters_to_yards(distance_m):.0f} yd ({distance_m:.0f} m)"
    return f"{distance_m:.0f} m"


def format_length_mm(value_mm: Any) -> str:
    try:
        length_mm = float(value_mm)
    except Exception:
        return str(value_mm) if value_mm not in (None, "") else "N/A"
    measurement_unit = get_measurement_unit().lower()
    if "inch" in measurement_unit or "tomm" in measurement_unit:
        return f"{units.mm_to_inches(length_mm):.2f} in ({length_mm:.1f} mm)"
    return f"{length_mm:.1f} mm"


def length_mm_to_display_value(value_mm: Any) -> float | None:
    try:
        length_mm = float(value_mm)
    except Exception:
        return None
    measurement_unit = get_measurement_unit().lower()
    if "inch" in measurement_unit or "tomm" in measurement_unit:
        return units.mm_to_inches(length_mm)
    return length_mm


def length_display_to_mm(value: Any) -> float | None:
    try:
        display_value = float(value)
    except Exception:
        return None
    measurement_unit = get_measurement_unit().lower()
    if "inch" in measurement_unit or "tomm" in measurement_unit:
        return units.inches_to_mm(display_value)
    return display_value


def get_length_suffix() -> str:
    measurement_unit = get_measurement_unit().lower()
    if "inch" in measurement_unit or "tomm" in measurement_unit:
        return " in"
    return " mm"


def format_length_delta_mm(value_mm: Any) -> str:
    try:
        length_mm = float(value_mm)
    except Exception:
        return str(value_mm) if value_mm not in (None, "") else "N/A"
    measurement_unit = get_measurement_unit().lower()
    if "inch" in measurement_unit or "tomm" in measurement_unit:
        return f"{units.mm_to_inches(length_mm):+.3f} in ({length_mm:+.2f} mm)"
    return f"{length_mm:+.2f} mm"


def format_weight_grains(value_gr: Any, category: str = "bullet") -> str:
    try:
        grains = float(value_gr)
    except Exception:
        return str(value_gr) if value_gr not in (None, "") else "N/A"
    unit_label = (
        get_powder_weight_unit().lower()
        if str(category).strip().lower() == "powder"
        else get_bullet_weight_unit().lower()
    )
    if "gram" in unit_label:
        grams = grains * GRAIN_TO_GRAM
        return f"{grams:.3f} g ({grains:.2f} gr)"
    return f"{grains:.2f} gr"


def weight_grains_to_display_value(
    value_gr: Any, category: str = "bullet"
) -> float | None:
    try:
        grains = float(value_gr)
    except Exception:
        return None
    unit_label = (
        get_powder_weight_unit().lower()
        if str(category).strip().lower() == "powder"
        else get_bullet_weight_unit().lower()
    )
    if "gram" in unit_label:
        return grains * GRAIN_TO_GRAM
    return grains


def weight_display_to_grains(value: Any, category: str = "bullet") -> float | None:
    try:
        display_value = float(value)
    except Exception:
        return None
    unit_label = (
        get_powder_weight_unit().lower()
        if str(category).strip().lower() == "powder"
        else get_bullet_weight_unit().lower()
    )
    if "gram" in unit_label:
        return display_value / GRAIN_TO_GRAM
    return display_value


def get_weight_suffix(category: str = "bullet") -> str:
    unit_label = (
        get_powder_weight_unit().lower()
        if str(category).strip().lower() == "powder"
        else get_bullet_weight_unit().lower()
    )
    return " g" if "gram" in unit_label else " gr"


def velocity_fps_to_display_value(value_fps: Any) -> float | None:
    try:
        fps_value = float(value_fps)
    except Exception:
        return None
    if get_velocity_unit().lower() == "m/s":
        return units.fps_to_mps(fps_value)
    return fps_value


def velocity_display_to_fps(value: Any) -> float | None:
    try:
        display_value = float(value)
    except Exception:
        return None
    if get_velocity_unit().lower() == "m/s":
        return units.mps_to_fps(display_value)
    return display_value


def get_velocity_suffix() -> str:
    return " m/s" if get_velocity_unit().lower() == "m/s" else " fps"


def format_pressure_psi(value_psi: Any) -> str:
    try:
        psi = float(value_psi)
    except Exception:
        return str(value_psi) if value_psi not in (None, "") else "N/A"
    pressure_unit = get_pressure_unit().lower()
    if pressure_unit == "bar":
        return f"{psi * PSI_TO_BAR:.0f} bar ({psi:.0f} psi)"
    if pressure_unit == "mpa":
        return f"{psi * PSI_TO_MPA:.1f} MPa ({psi:.0f} psi)"
    return f"{psi:.0f} psi"


def format_pressure_range_psi(min_psi: Any, max_psi: Any) -> str:
    try:
        low = float(min_psi)
        high = float(max_psi)
    except Exception:
        return "N/A"
    pressure_unit = get_pressure_unit().lower()
    if pressure_unit == "bar":
        return f"{low * PSI_TO_BAR:.0f}-{high * PSI_TO_BAR:.0f} bar ({low:.0f}-{high:.0f} psi)"
    if pressure_unit == "mpa":
        return f"{low * PSI_TO_MPA:.1f}-{high * PSI_TO_MPA:.1f} MPa ({low:.0f}-{high:.0f} psi)"
    return f"{low:.0f}-{high:.0f} psi"


def format_group_size_mm(value_mm: Any, distance_m: Any | None = None) -> str:
    try:
        group_mm = float(value_mm)
    except Exception:
        return str(value_mm) if value_mm not in (None, "") else "N/A"
    group_unit = get_group_size_unit().lower()
    if "inch" in group_unit or "tomm" in group_unit:
        return f"{units.mm_to_inches(group_mm):.2f} in ({group_mm:.1f} mm)"
    if group_unit == "moa":
        try:
            distance = float(distance_m)
            if distance > 0:
                moa = group_mm / (distance * 0.290888)
                return f"{moa:.2f} MOA ({group_mm:.1f} mm)"
        except Exception:
            pass
    if group_unit == "mil":
        try:
            distance = float(distance_m)
            if distance > 0:
                mil = group_mm / distance
                return f"{mil:.2f} mil ({group_mm:.1f} mm)"
        except Exception:
            pass
    return f"{group_mm:.1f} mm"
