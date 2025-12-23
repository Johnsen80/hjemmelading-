"""Environmental correction helpers: air density and ratios.

Provides functions to compute air density from temperature (°C), pressure (kPa)
and relative humidity (%) and return a ratio relative to a standard reference.
"""

from math import exp

# Physical constants
_RD = 287.058  # specific gas constant for dry air J/(kg*K)
_EPS = 0.622


def _saturation_vapor_pressure_pa(temp_c: float) -> float:
    """Approximate saturation vapor pressure (Pa) using Magnus-Tetens formula."""
    t = float(temp_c)
    es_hpa = 6.112 * exp((17.67 * t) / (t + 243.5))
    return es_hpa * 100.0


def air_density_kg_m3(
    temp_c: float = 15.0, pressure_kpa: float = 101.325, rh_percent: float = 0.0
) -> float:
    """Compute air density (kg/m^3) given ambient conditions.

    Parameters:
    - temp_c: temperature in °C
    - pressure_kpa: ambient pressure in kPa
    - rh_percent: relative humidity in percent (0-100)

    Returns density in kg/m^3.
    """
    # Convert
    p_pa = float(pressure_kpa) * 1000.0
    t_k = float(temp_c) + 273.15

    # vapor pressure
    es = _saturation_vapor_pressure_pa(temp_c)
    e = (float(rh_percent) / 100.0) * es

    # mixing ratio (kg water vapor / kg dry air)
    # r = eps * e / (p - e)
    try:
        r = _EPS * e / max(p_pa - e, 1e-6)
    except Exception:
        r = 0.0

    # virtual temperature Tv = T * (1 + 0.61 * r)
    tv = t_k * (1.0 + 0.61 * r)

    # density = p / (Rd * Tv) * (1 - e/p) ??? Using ideal gas with virtual temp handles moisture
    rho = p_pa / (_RD * tv)
    return rho


def air_density_ratio(
    temp_c: float = 15.0, pressure_kpa: float = 101.325, rh_percent: float = 0.0
) -> float:
    """Return ratio of ambient air density to standard reference (15°C, 101.325 kPa, 0% RH)."""
    ref = air_density_kg_m3(15.0, 101.325, 0.0)
    val = air_density_kg_m3(temp_c, pressure_kpa, rh_percent)
    if ref <= 0:
        return 1.0
    return val / ref
