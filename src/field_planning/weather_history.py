"""Weather history and climate data for field planning.

Sources (priority order):
1. Own session history — chrono sessions + temperatures from the user's DB
2. Frost API (met.no) — historical climate normals for nearest station
3. Manual / no data

The Frost API is free (Norwegian open data), returns monthly climate normals.
Endpoint: https://frost.met.no/observations/v0.jsonld
Requires a client ID (free registration at frost.met.no).

This module provides both the data models and a pure-computation analysis
layer that works offline (no network calls). Network fetching is delegated
to the calling UI code to keep this module testable without network access.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class MonthlyClimateSummary:
    """Climate statistics for one month at one location."""

    month: int  # 1–12
    year_count: int  # how many years of data
    temp_mean_c: float
    temp_min_c: float
    temp_max_c: float
    pressure_mean_hpa: float
    wind_mean_mps: float
    wind_max_mps: float
    humidity_mean_pct: float
    source: str = "frost_api"  # "frost_api", "session_history", "manual"


@dataclass
class SessionWeatherRecord:
    """One weather observation recorded at a shooting session."""

    session_id: int
    date: str  # ISO date string
    temperature_c: float
    pressure_hpa: float
    humidity_pct: float
    wind_speed_mps: float
    wind_dir_deg: float
    source: str = "chrono_session"


@dataclass
class WeatherHistoryReport:
    """Complete weather history analysis for a location and date."""

    location_label: str
    target_date: str  # ISO date
    month: int
    # Historical climate normals
    climate_monthly: MonthlyClimateSummary | None
    # User's own session history
    session_records: list[SessionWeatherRecord]
    # Anomaly analysis
    anomaly_temp_c: float | None  # today minus monthly mean
    anomaly_pressure_hpa: float | None
    anomaly_wind_mps: float | None
    # Warnings
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Climate analysis (pure, no network)
# ---------------------------------------------------------------------------


def compute_anomaly(
    current_value: float,
    monthly_mean: float,
    monthly_std: float | None = None,
) -> tuple[float, str]:
    """Compute anomaly and severity label.

    Returns (anomaly, severity) where severity is "normal", "notable", "extreme".
    """
    anomaly = current_value - monthly_mean
    if monthly_std and monthly_std > 0:
        z = abs(anomaly) / monthly_std
        if z > 2.0:
            return anomaly, "extreme"
        if z > 1.0:
            return anomaly, "notable"
        return anomaly, "normal"
    # Fallback: use fixed thresholds
    if abs(anomaly) > 10.0:
        return anomaly, "extreme"
    if abs(anomaly) > 5.0:
        return anomaly, "notable"
    return anomaly, "normal"


def filter_sessions_by_month(
    records: list[SessionWeatherRecord],
    month: int,
    temp_tolerance_c: float = 10.0,
    current_temp_c: float | None = None,
) -> list[SessionWeatherRecord]:
    """Filter session records to same month, optionally by temperature similarity."""
    result = []
    for r in records:
        try:
            d = date.fromisoformat(r.date)
        except (ValueError, AttributeError):
            continue
        if d.month != month:
            continue
        if current_temp_c is not None:
            if abs(r.temperature_c - current_temp_c) > temp_tolerance_c:
                continue
        result.append(r)
    return result


def summarize_session_weather(
    records: list[SessionWeatherRecord],
) -> dict[str, float | int]:
    """Compute summary statistics from session records."""
    if not records:
        return {}
    n = len(records)
    return {
        "count": n,
        "temp_mean_c": sum(r.temperature_c for r in records) / n,
        "temp_min_c": min(r.temperature_c for r in records),
        "temp_max_c": max(r.temperature_c for r in records),
        "pressure_mean_hpa": sum(r.pressure_hpa for r in records) / n,
        "wind_mean_mps": sum(r.wind_speed_mps for r in records) / n,
    }


def build_weather_warnings(
    report: WeatherHistoryReport,
    current_temp_c: float | None = None,
    current_pressure_hpa: float | None = None,
    current_wind_mps: float | None = None,
) -> list[str]:
    """Generate human-readable warnings based on weather anomalies."""
    warnings: list[str] = []

    if report.climate_monthly is None:
        return warnings

    climate = report.climate_monthly

    if current_temp_c is not None:
        anom, severity = compute_anomaly(current_temp_c, climate.temp_mean_c)
        if severity == "extreme":
            direction = "varmere" if anom > 0 else "kaldere"
            warnings.append(
                f"⚠️  Temperatur {abs(anom):.1f}°C {direction} enn månedsnormal "
                f"({climate.temp_mean_c:.1f}°C). Stor MV-endring mulig."
            )
        elif severity == "notable":
            direction = "varmere" if anom > 0 else "kaldere"
            warnings.append(
                f"ℹ️  Temperatur {abs(anom):.1f}°C {direction} enn normalt for {_month_name(report.month)}."
            )

    if current_pressure_hpa is not None:
        anom, severity = compute_anomaly(
            current_pressure_hpa, climate.pressure_mean_hpa
        )
        if severity in ("extreme", "notable"):
            direction = "høyere" if anom > 0 else "lavere"
            warnings.append(
                f"ℹ️  Lufttrykk {abs(anom):.0f} hPa {direction} enn normalt "
                f"({climate.pressure_mean_hpa:.0f} hPa)."
            )

    if current_wind_mps is not None and current_wind_mps > climate.wind_max_mps * 0.8:
        warnings.append(
            f"⚠️  Vindstyrke {current_wind_mps:.1f} m/s nær historisk månedsmaks "
            f"({climate.wind_max_mps:.1f} m/s). Ustabile forhold."
        )

    return warnings


def _month_name(month: int) -> str:
    names = [
        "jan",
        "feb",
        "mar",
        "apr",
        "mai",
        "jun",
        "jul",
        "aug",
        "sep",
        "okt",
        "nov",
        "des",
    ]
    return names[month - 1] if 1 <= month <= 12 else str(month)


# ---------------------------------------------------------------------------
# Frost API response parser (pure — no HTTP calls)
# ---------------------------------------------------------------------------


def parse_frost_monthly_normals(
    frost_response: dict,
    month: int,
) -> MonthlyClimateSummary | None:
    """Parse a Frost API observations response into MonthlyClimateSummary.

    The caller is responsible for the HTTP fetch. This function only parses.

    Parameters
    ----------
    frost_response:
        Parsed JSON from Frost API /observations endpoint.
    month:
        Target month (1–12) to extract.
    """
    try:
        data = frost_response.get("data", [])
        if not data:
            return None

        temps, pressures, winds, humidities = [], [], [], []
        for obs in data:
            obs_month = None
            ref_time = obs.get("referenceTime", "")
            try:
                obs_month = int(ref_time[5:7])
            except (ValueError, IndexError):
                pass
            if obs_month != month:
                continue
            for elem in obs.get("observations", []):
                eid = elem.get("elementId", "")
                val = elem.get("value")
                if val is None:
                    continue
                try:
                    val = float(val)
                except (TypeError, ValueError):
                    continue
                if "air_temperature" in eid:
                    temps.append(val)
                elif "air_pressure" in eid:
                    pressures.append(val)
                elif "wind_speed" in eid:
                    winds.append(val)
                elif "relative_humidity" in eid:
                    humidities.append(val)

        if not temps and not pressures:
            return None

        def _mean(lst: list) -> float:
            return sum(lst) / len(lst) if lst else 0.0

        return MonthlyClimateSummary(
            month=month,
            year_count=len(
                set(
                    ref_time[:4]
                    for obs in data
                    for ref_time in [obs.get("referenceTime", "")]
                )
            ),
            temp_mean_c=_mean(temps),
            temp_min_c=min(temps) if temps else 0.0,
            temp_max_c=max(temps) if temps else 0.0,
            pressure_mean_hpa=_mean(pressures) if pressures else 1013.25,
            wind_mean_mps=_mean(winds),
            wind_max_mps=max(winds) if winds else 0.0,
            humidity_mean_pct=_mean(humidities),
            source="frost_api",
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# CDM calibration from multi-range drop measurements
# ---------------------------------------------------------------------------


@dataclass
class DropMeasurement:
    """One measured drop at a specific distance (user measured, not factory)."""

    distance_m: float
    measured_drop_cm: float  # actual impact below zero line
    conditions_temp_c: float = 15.0
    conditions_pressure_hpa: float = 1013.25
    notes: str = ""


def calibrate_bc_from_drops(
    measurements: list[DropMeasurement],
    nominal_mv_fps: float,
    zero_distance_m: float = 100.0,
    bc_type: str = "G7",
    initial_bc: float = 0.200,
    tolerance_cm: float = 0.5,
    max_iterations: int = 50,
) -> tuple[float, float]:
    """Back-calculate BC from real drop measurements using bisection search.

    Tries to find BC such that computed drop matches measured drop across
    all measurement distances. Uses weighted least-squares minimization.

    Parameters
    ----------
    measurements:
        List of drop measurements at various distances.
    nominal_mv_fps:
        Muzzle velocity to use (from chrono sessions).
    tolerance_cm:
        Convergence threshold (cm RMS error).

    Returns (calibrated_bc, rms_error_cm).
    """
    from ..utils.advanced_ballistics import (
        AdvancedBallisticsEngine,
        AtmosphericConditions,
    )

    if not measurements or len(measurements) < 1:
        return initial_bc, 999.9

    engine = AdvancedBallisticsEngine()

    def _compute_rms(bc_candidate: float) -> float:
        errors = []
        for m in measurements:
            cond = AtmosphericConditions(
                temperature_f=m.conditions_temp_c * 9 / 5 + 32,
                pressure_inhg=m.conditions_pressure_hpa * 0.02953,
                humidity_percent=50.0,
                altitude_ft=0.0,
            )
            pts = engine.calculate_trajectory(
                velocity_fps=nominal_mv_fps,
                bc=bc_candidate,
                weight_grains=168.0,
                zero_distance_m=zero_distance_m,
                max_distance_m=m.distance_m + 5.0,
                step_size_m=max(1.0, m.distance_m / 100.0),
                bc_type=bc_type,
                conditions=cond,
                wind_speed_mph=0.0,
                wind_angle_deg=90.0,
                latitude_deg=60.0,
                azimuth_deg=0.0,
                twist_rate=10.0,
                twist_direction="RIGHT",
            )
            if not pts:
                continue
            pt = min(pts, key=lambda p: abs(p.distance_m - m.distance_m))
            computed_drop = pt.drop_cm
            errors.append((computed_drop - m.measured_drop_cm) ** 2)
        if not errors:
            return 999.9
        return math.sqrt(sum(errors) / len(errors))

    best_bc = initial_bc
    best_rms = _compute_rms(initial_bc)

    # Grid search first (coarse)
    for bc_try in [x * 0.05 for x in range(1, 30)]:
        rms = _compute_rms(bc_try)
        if rms < best_rms:
            best_rms = rms
            best_bc = bc_try

    # Fine-grain grid search around best (0.005 steps over ±0.15 window)
    fine_lo = max(0.05, best_bc - 0.15)
    fine_hi = min(1.50, best_bc + 0.15)
    n_fine = int((fine_hi - fine_lo) / 0.005) + 1
    for i in range(n_fine):
        bc_try = round(fine_lo + i * 0.005, 4)
        rms = _compute_rms(bc_try)
        if rms < best_rms:
            best_rms = rms
            best_bc = bc_try

    # Golden-section refinement in ±0.01 around fine best
    _gr = (math.sqrt(5) - 1) / 2
    lo, hi = max(0.05, best_bc - 0.01), min(1.50, best_bc + 0.01)
    for _ in range(max_iterations):
        c = hi - _gr * (hi - lo)
        d = lo + _gr * (hi - lo)
        if _compute_rms(c) < _compute_rms(d):
            hi = d
        else:
            lo = c
        if (hi - lo) < 0.0005:
            break
    best_bc = (lo + hi) / 2.0
    best_rms = _compute_rms(best_bc)

    return best_bc, best_rms
