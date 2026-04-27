"""Atmospheric modelling for field planning.

Builds a LayeredAtmosphere from available data sources:
  1. Surface conditions (from Yr.no or manual input)
  2. Aloft layers from radiosonde data (met.no) when network available
  3. Standard lapse rate estimate when offline

Also detects inversion, katabatic risk, and thermal hazard from terrain.
"""

from __future__ import annotations

import math

from .models import AtmosphereLayer, LayeredAtmosphere

# ---------------------------------------------------------------------------
# ICAO standard atmosphere constants
# ---------------------------------------------------------------------------

_ICAO_TEMP_C = 15.0
_ICAO_PRESS_HPA = 1013.25
_ICAO_LAPSE_RATE = 6.5  # °C per 1000m (environmental lapse rate)
_DRY_ADIABATIC_LAPSE = 9.8  # °C per 1000m (dry adiabatic)
_WATER_VAPOR_MOLAR = 18.015
_DRY_AIR_MOLAR = 28.966
_STANDARD_DENSITY = 1.225  # kg/m³ at ICAO sea level


# ---------------------------------------------------------------------------
# Density altitude
# ---------------------------------------------------------------------------


def compute_density_altitude(
    temperature_c: float,
    pressure_hpa: float,
    humidity_pct: float = 0.0,
) -> float:
    """Return density altitude in metres.

    Uses the FAA formula with humidity correction (water vapour reduces density).
    """
    temp_k = temperature_c + 273.15
    # Saturation vapour pressure (Magnus formula)
    e_sat = 6.1078 * math.exp(17.27 * temperature_c / (temperature_c + 237.3))
    e_actual = (humidity_pct / 100.0) * e_sat
    # Virtual temperature correction (water vapour is lighter than dry air)
    tv_k = temp_k / (
        1.0 - (e_actual / pressure_hpa) * (1.0 - _WATER_VAPOR_MOLAR / _DRY_AIR_MOLAR)
    )
    # Pressure altitude (ft) then correct for temperature
    pressure_alt_ft = 145_442.156 * (1.0 - (pressure_hpa / _ICAO_PRESS_HPA) ** 0.190261)
    # Density altitude
    isa_temp_k = (
        _ICAO_TEMP_C + 273.15 - 0.00198 * pressure_alt_ft
    )  # ISA temp at that PA
    da_ft = pressure_alt_ft + 118.8 * (tv_k - isa_temp_k)
    return da_ft * 0.3048  # feet → metres


def compute_density_ratio(
    temperature_c: float,
    pressure_hpa: float,
    humidity_pct: float = 0.0,
) -> float:
    """Air density relative to ICAO standard (1.0 = standard day)."""
    temp_k = temperature_c + 273.15
    # Saturation vapour pressure
    e_sat = 6.1078 * math.exp(17.27 * temperature_c / (temperature_c + 237.3))
    e_actual = (humidity_pct / 100.0) * e_sat
    p_dry = pressure_hpa - e_actual
    # Actual density via ideal gas law (partial pressures)
    rho_dry = (p_dry * 100) / (287.058 * temp_k)  # Pa / (R_dry * T)
    rho_vap = (e_actual * 100) / (461.495 * temp_k)  # Pa / (R_vap * T)
    rho = rho_dry + rho_vap
    return rho / _STANDARD_DENSITY


# ---------------------------------------------------------------------------
# Layer builder from surface conditions
# ---------------------------------------------------------------------------


def build_surface_layer(
    temperature_c: float,
    pressure_hpa: float,
    humidity_pct: float,
    wind_speed_mps: float,
    wind_dir_deg: float,
    altitude_m: float = 0.0,
    source: str = "surface",
) -> AtmosphereLayer:
    da = compute_density_altitude(temperature_c, pressure_hpa, humidity_pct)
    dr = compute_density_ratio(temperature_c, pressure_hpa, humidity_pct)
    return AtmosphereLayer(
        altitude_m=altitude_m,
        temperature_c=temperature_c,
        pressure_hpa=pressure_hpa,
        humidity_pct=humidity_pct,
        wind_speed_mps=wind_speed_mps,
        wind_dir_deg=wind_dir_deg,
        density_ratio=dr,
        density_altitude_m=da,
        source=source,
    )


def build_lapse_rate_layers(
    surface: AtmosphereLayer,
    max_altitude_m: float = 2000.0,
    step_m: float = 500.0,
    lapse_rate: float = _ICAO_LAPSE_RATE,
) -> list[AtmosphereLayer]:
    """Estimate atmospheric layers above surface using standard lapse rate.

    Returns a list starting from surface (altitude=0) up to max_altitude_m.
    """
    layers = [surface]
    alt = surface.altitude_m + step_m
    while alt <= surface.altitude_m + max_altitude_m:
        delta_t = lapse_rate * (alt - surface.altitude_m) / 1000.0
        temp = surface.temperature_c - delta_t
        # Pressure: hypsometric formula
        press = surface.pressure_hpa * math.exp(
            -0.0289644
            * 9.80665
            * (alt - surface.altitude_m)
            / (8.31432 * (surface.temperature_c + 273.15))
        )
        hum = max(0.0, surface.humidity_pct - 5.0 * (alt - surface.altitude_m) / 1000.0)
        # Wind increases logarithmically with height (log wind profile)
        if surface.wind_speed_mps > 0 and alt > 10.0:
            z0 = 0.03  # roughness length for open terrain (m)
            wind = surface.wind_speed_mps * math.log(alt / z0) / math.log(10.0 / z0)
            wind = min(wind, surface.wind_speed_mps * 2.5)  # cap
        else:
            wind = surface.wind_speed_mps
        layer = build_surface_layer(
            temperature_c=temp,
            pressure_hpa=press,
            humidity_pct=hum,
            wind_speed_mps=wind,
            wind_dir_deg=surface.wind_dir_deg,
            altitude_m=alt,
            source="lapse_rate",
        )
        layers.append(layer)
        alt += step_m
    return layers


# ---------------------------------------------------------------------------
# Inversion and stability detection
# ---------------------------------------------------------------------------


def detect_inversion(layers: list[AtmosphereLayer]) -> tuple[bool, float | None]:
    """Detect temperature inversion (temp increases with altitude).

    Returns (inversion_detected, inversion_base_altitude_m).
    """
    if len(layers) < 2:
        return False, None
    for i in range(len(layers) - 1):
        if layers[i + 1].temperature_c > layers[i].temperature_c:
            return True, layers[i].altitude_m
    return False, None


def katabatic_risk(
    valley_depth_m: float | None,
    wind_speed_mps: float,
    hour_of_day: int | None,
    cloud_cover_oktas: int | None,
) -> bool:
    """Estimate whether cold air pooling in a valley is likely.

    Conditions: calm wind, clear sky, nighttime/early morning, valley present.
    """
    if valley_depth_m is None or valley_depth_m < 30.0:
        return False
    if wind_speed_mps > 3.0:
        return False
    if cloud_cover_oktas is not None and cloud_cover_oktas >= 6:
        return False
    if hour_of_day is not None and 8 <= hour_of_day <= 18:
        return False  # daytime → thermal mixing suppresses inversion
    return True


# ---------------------------------------------------------------------------
# Thermal risk from terrain surface
# ---------------------------------------------------------------------------

# Thermal contribution per surface type at high solar radiation
_THERMAL_WEIGHT = {
    "rock": 3,  # dark granite absorbs strongly → strong thermals
    "urban": 2,
    "field": 1,
    "swamp": 2,  # wet surface → evaporation AND convection
    "water": 1,
    "forest": 0,  # canopy damps thermals
    "snow": 0,  # reflective + cold → no thermals
    "unknown": 1,
}

_THERMAL_LEVELS = ["low", "moderate", "high"]


def compute_thermal_risk(
    surface_types: list[str],
    segment_lengths_m: list[float],
    solar_factor: float = 1.0,  # 0–1: 0=overcast, 1=full sun
    wind_speed_mps: float = 0.0,
) -> str:
    """Return thermal risk level: 'low', 'moderate', or 'high'.

    Higher wind damps thermals. Overcast (solar_factor=0) → always low.
    """
    if solar_factor < 0.2:
        return "low"
    if wind_speed_mps > 5.0:
        return "low"

    total_len = sum(segment_lengths_m) or 1.0
    weighted_score = (
        sum(
            _THERMAL_WEIGHT.get(st, 1) * seg_len
            for st, seg_len in zip(surface_types, segment_lengths_m)
        )
        / total_len
    )

    # High wind partially damps: reduce score
    wind_damp = max(0.0, 1.0 - wind_speed_mps / 5.0)
    score = weighted_score * solar_factor * wind_damp

    if score >= 2.0:
        return "high"
    if score >= 1.0:
        return "moderate"
    return "low"


# ---------------------------------------------------------------------------
# Warning generator
# ---------------------------------------------------------------------------


def build_atmosphere_warnings(
    atm: LayeredAtmosphere,
    surface_types: list[str] | None = None,
    segment_lengths_m: list[float] | None = None,
    valley_depth_m: float | None = None,
    hour_of_day: int | None = None,
    cloud_cover_oktas: int | None = None,
) -> list[str]:
    """Build human-readable warning strings from atmospheric state."""
    warnings: list[str] = []
    surface = atm.surface_layer

    # Inversion / katabatic
    if atm.inversion_detected:
        alt = atm.inversion_altitude_m
        alt_str = f" (fra ~{alt:.0f}m)" if alt is not None else ""
        warnings.append(
            f"⚠️  Temperaturinversjon detektert{alt_str} — "
            f"kaldere luft under → økt drag, subsonic-grense rykker nærmere."
        )
    if atm.katabatic_risk:
        depth_str = f" ({valley_depth_m:.0f}m dyp dal)" if valley_depth_m else ""
        warnings.append(
            f"⚠️  Katabatisk kaldluft sannsynlig{depth_str} "
            f"(stille vind, klar himmel, lav tid). "
            f"Lufttetthet kan være 2–8% høyere i dalbunn."
        )

    # Thermal risk
    if atm.thermal_risk_level == "high":
        warnings.append(
            "⚠️  HØYT termikk-nivå (sol + varme overflater i skuddlinje). "
            "Forventet vertikal spredning +15–28 cm ved 1000m+. "
            "Beste tid: tidlig morgen eller overskyet."
        )
    elif atm.thermal_risk_level == "moderate":
        warnings.append(
            "ℹ️  Moderat termikk-risiko. "
            "Kan gi noe økt vertikal spredning ved lange skudd."
        )

    # Humidity
    hum = surface.humidity_pct
    if hum >= 70.0:
        density_effect_pct = (1.0 - surface.density_ratio) * 100.0
        sign = "lavere" if density_effect_pct > 0 else "høyere"
        warnings.append(
            f"ℹ️  Luftfuktighet {hum:.0f}% "
            f"→ lufttetthet {abs(density_effect_pct):.1f}% {sign} enn standard. "
            f"Kompensert i beregningen."
        )

    # Density altitude note
    da = surface.density_altitude_m
    if abs(da) > 300.0:
        direction = "over" if da > 0 else "under"
        warnings.append(
            f"ℹ️  Densitets-altitude: {da:.0f}m ({direction} faktisk høyde). "
            f"Redusert drag — flater bane."
        )

    return warnings


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------


def build_layered_atmosphere(
    temperature_c: float,
    pressure_hpa: float,
    humidity_pct: float,
    wind_speed_mps: float,
    wind_dir_deg: float,
    altitude_m: float = 0.0,
    surface_types: list[str] | None = None,
    segment_lengths_m: list[float] | None = None,
    valley_depth_m: float | None = None,
    hour_of_day: int | None = None,
    cloud_cover_oktas: int | None = None,
    solar_factor: float = 0.8,
    radiosonde_layers: list[dict] | None = None,
) -> LayeredAtmosphere:
    """Build a complete LayeredAtmosphere from surface conditions.

    If radiosonde_layers is provided (list of dicts from met.no API), those
    are used for aloft layers instead of the lapse rate estimate.
    """
    surface = build_surface_layer(
        temperature_c,
        pressure_hpa,
        humidity_pct,
        wind_speed_mps,
        wind_dir_deg,
        altitude_m,
    )

    if radiosonde_layers:
        layers = [surface] + [_dict_to_layer(d) for d in radiosonde_layers]
        layers.sort(key=lambda layer: layer.altitude_m)
    else:
        layers = build_lapse_rate_layers(surface)

    inversion, inv_alt = detect_inversion(layers)
    kat = katabatic_risk(valley_depth_m, wind_speed_mps, hour_of_day, cloud_cover_oktas)

    st = surface_types or ["field"]
    sl = segment_lengths_m or [1000.0]
    thermal = compute_thermal_risk(st, sl, solar_factor, wind_speed_mps)

    dominant = _dominant_surface(st, sl)

    atm = LayeredAtmosphere(
        layers=layers,
        inversion_detected=inversion,
        inversion_altitude_m=inv_alt,
        thermal_risk_level=thermal,
        surface_type_primary=dominant,
        katabatic_risk=kat,
    )

    atm.warnings = build_atmosphere_warnings(
        atm, st, sl, valley_depth_m, hour_of_day, cloud_cover_oktas
    )

    return atm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dominant_surface(
    types: list[str],
    lengths: list[float],
) -> str:
    totals: dict[str, float] = {}
    for t, seg_len in zip(types, lengths):
        totals[t] = totals.get(t, 0.0) + seg_len
    return max(totals, key=totals.get) if totals else "unknown"


def _dict_to_layer(d: dict) -> AtmosphereLayer:
    temp = float(d.get("temperature_c", 0.0))
    press = float(d.get("pressure_hpa", 1013.25))
    hum = float(d.get("humidity_pct", 50.0))
    wind = float(d.get("wind_speed_mps", 0.0))
    wind_dir = float(d.get("wind_dir_deg", 0.0))
    alt = float(d.get("altitude_m", 0.0))
    return build_surface_layer(
        temp, press, hum, wind, wind_dir, alt, source="radiosonde"
    )
