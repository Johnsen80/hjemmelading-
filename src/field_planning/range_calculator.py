"""Shooting range click-table calculator.

Computes per-target solutions for a range session with multiple targets at
varying distances, inclinations, and bearings.

Slant correction method: cosine rule applied to drop MOA.
  corrected_elevation_moa = drop_moa_at_slant_range × cos(inclination_deg)

This is the same method used by Applied Ballistics, Kestrel, and Hornady 4DOF.
It is more accurate than rifleman's rule (horizontal range substitution) because
it accounts for the full flight path length (velocity loss, air resistance).
"""

from __future__ import annotations

import math

from ..utils.advanced_ballistics import AdvancedBallisticsEngine, AtmosphericConditions
from .models import (
    AtmosphereLayer,
    ClickCorrection,
    LayeredAtmosphere,
    RangeSession,
    RangeTarget,
    TargetSolution,
    WeaponBallisticProfile,
)

# ---------------------------------------------------------------------------
# Pure geometry helpers
# ---------------------------------------------------------------------------


def slant_range_to_horizontal(slant_range_m: float, inclination_deg: float) -> float:
    """Horizontal distance for a target at given slant range and inclination."""
    return slant_range_m * math.cos(math.radians(inclination_deg))


def inclination_correction_factor(inclination_deg: float) -> float:
    """Cosine factor for slant correction: multiply standard drop MOA by this value."""
    return math.cos(math.radians(inclination_deg))


def wind_crosswind_factor(wind_dir_deg: float, bearing_deg: float) -> float:
    """Fractional crosswind component (0–1) for a shot toward bearing_deg.

    Returns 1.0 for pure crosswind (90° difference), 0.0 for head/tailwind.
    """
    relative = (wind_dir_deg - bearing_deg) % 360
    return abs(math.sin(math.radians(relative)))


# ---------------------------------------------------------------------------
# Per-target solution
# ---------------------------------------------------------------------------


def compute_target_solution(
    profile: WeaponBallisticProfile,
    atmosphere: LayeredAtmosphere,
    slant_range_m: float,
    inclination_deg: float = 0.0,
    bearing_deg: float = 0.0,
    label: str = "",
    clicks_per_moa: float = 4.0,
    scope_unit: str = "moa",
    latitude_deg: float = 60.0,
) -> TargetSolution:
    """Compute click solution for one target with slant and wind correction.

    Parameters
    ----------
    profile:        Weapon + ammo ballistic profile with calibrated BC/MV.
    atmosphere:     Active atmospheric conditions.
    slant_range_m:  Line-of-sight distance to target.
    inclination_deg: Positive = uphill, negative = downhill.
    bearing_deg:    Compass bearing to target (for Coriolis and wind angle).
    clicks_per_moa: Scope click adjustment per MOA.
    scope_unit:     "moa" or "mrad".
    """
    target = RangeTarget(
        label=label,
        slant_range_m=slant_range_m,
        inclination_deg=inclination_deg,
        bearing_deg=bearing_deg,
    )
    return _solve_target(
        target=target,
        profile=profile,
        atmosphere=atmosphere,
        clicks_per_moa=clicks_per_moa,
        scope_unit=scope_unit,
        latitude_deg=latitude_deg,
    )


def build_range_click_table(
    session: RangeSession,
) -> list[TargetSolution]:
    """Compute click solutions for all targets in a range session.

    Returns list in same order as session.targets.
    """
    atm = session.atmosphere or _default_atmosphere()
    return [
        _solve_target(
            target=t,
            profile=session.profile,
            atmosphere=atm,
            clicks_per_moa=session.clicks_per_moa,
            scope_unit=session.scope_unit,
            latitude_deg=session.latitude_deg,
        )
        for t in session.targets
    ]


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _solve_target(
    target: RangeTarget,
    profile: WeaponBallisticProfile,
    atmosphere: LayeredAtmosphere,
    clicks_per_moa: float,
    scope_unit: str,
    latitude_deg: float,
) -> TargetSolution:
    surface = atmosphere.surface_layer
    mv_fps = profile.mv_at_temperature(surface.temperature_c)
    conditions = _layer_to_conditions(surface)
    engine = AdvancedBallisticsEngine()

    wind_angle = _wind_angle_for_bearing(surface.wind_dir_deg, target.bearing_deg)
    wind_mph = surface.wind_speed_mps * 2.23694

    raw = engine.calculate_trajectory(
        velocity_fps=max(100.0, mv_fps),
        bc=max(0.05, profile.learned_bc),
        weight_grains=profile.bullet_mass_gr or 168.0,
        zero_distance_m=profile.zero_distance_m,
        max_distance_m=target.slant_range_m + 5.0,
        step_size_m=max(1.0, target.slant_range_m / 100.0),
        bc_type=(
            profile.learned_bc_type if profile.learned_bc_type in {"G1", "G7"} else "G7"
        ),
        conditions=conditions,
        wind_speed_mph=wind_mph,
        wind_angle_deg=wind_angle,
        latitude_deg=latitude_deg,
        azimuth_deg=target.bearing_deg,
        twist_rate=profile.twist_rate_in,
        twist_direction=profile.twist_direction,
    )

    pt = _nearest_point(raw, target.slant_range_m)
    if pt is None:
        return _empty_solution(target, clicks_per_moa, scope_unit)

    # Slant correction: multiply elevation MOA by cos(inclination)
    cos_inc = inclination_correction_factor(target.inclination_deg)
    corrected_drop_moa = pt.drop_moa * cos_inc
    corrected_drop_mrad = pt.drop_mrad * cos_inc

    corr = _make_click_correction(
        elevation_moa=corrected_drop_moa,
        elevation_mrad=corrected_drop_mrad,
        windage_moa=pt.windage_moa,
        windage_mrad=pt.windage_mrad,
        clicks_per_moa=clicks_per_moa,
        scope_unit=scope_unit,
    )

    # 10 m/s reference wind column (full crosswind, independent of current wind)
    ref_wind = engine.calculate_trajectory(
        velocity_fps=max(100.0, mv_fps),
        bc=max(0.05, profile.learned_bc),
        weight_grains=profile.bullet_mass_gr or 168.0,
        zero_distance_m=profile.zero_distance_m,
        max_distance_m=target.slant_range_m + 5.0,
        step_size_m=max(1.0, target.slant_range_m / 100.0),
        bc_type=(
            profile.learned_bc_type if profile.learned_bc_type in {"G1", "G7"} else "G7"
        ),
        conditions=conditions,
        wind_speed_mph=10.0 * 2.23694,
        wind_angle_deg=90.0,
        latitude_deg=latitude_deg,
        azimuth_deg=target.bearing_deg,
        twist_rate=profile.twist_rate_in,
        twist_direction=profile.twist_direction,
    )
    ref_pt = _nearest_point(ref_wind, target.slant_range_m)
    wind_10_windage_moa = ref_pt.windage_moa if ref_pt else 0.0

    sos = _speed_of_sound_mps(surface.temperature_c)
    vel_mps = pt.velocity_fps * 0.3048
    mach = vel_mps / sos if sos > 0 else 0.0
    energy_j = pt.energy_ftlbs * 1.35582

    sg = _compute_sg(profile, pt.velocity_fps, surface.density_ratio)

    return TargetSolution(
        target=target,
        correction=corr,
        wind_10mps_elevation_moa=0.0,
        wind_10mps_windage_moa=wind_10_windage_moa,
        velocity_mps=vel_mps,
        energy_joules=energy_j,
        time_of_flight_s=pt.time_s,
        mach=mach,
        phase=_mach_phase(mach),
        stability_sg=sg,
        slant_correction_applied=True,
        inclination_correction_factor=cos_inc,
    )


def _nearest_point(points: list, distance_m: float):
    if not points:
        return None
    return min(points, key=lambda p: abs(p.distance_m - distance_m))


def _wind_angle_for_bearing(wind_dir_deg: float, bearing_deg: float) -> float:
    """Convert met wind direction + shot bearing → engine wind angle.

    Engine: 0° = headwind, 90° = right crosswind, 180° = tailwind.
    """
    return (wind_dir_deg - bearing_deg + 180) % 360


def _layer_to_conditions(layer: AtmosphereLayer) -> AtmosphericConditions:
    return AtmosphericConditions(
        temperature_f=layer.temperature_c * 9 / 5 + 32,
        pressure_inhg=layer.pressure_hpa * 0.02953,
        humidity_percent=layer.humidity_pct,
        altitude_ft=layer.altitude_m * 3.28084,
    )


def _default_atmosphere() -> LayeredAtmosphere:
    layer = AtmosphereLayer(
        altitude_m=0.0,
        temperature_c=15.0,
        pressure_hpa=1013.25,
        humidity_pct=50.0,
        wind_speed_mps=0.0,
        wind_dir_deg=0.0,
        density_ratio=1.0,
        density_altitude_m=0.0,
        source="default",
    )
    return LayeredAtmosphere(layers=[layer])


def _speed_of_sound_mps(temperature_c: float) -> float:
    return 331.3 * math.sqrt(1.0 + temperature_c / 273.15)


def _mach_phase(mach: float) -> str:
    if mach >= 1.2:
        return "supersonic"
    if mach >= 0.9:
        return "transonic"
    return "subsonic"


def _compute_sg(
    profile: WeaponBallisticProfile,
    velocity_fps: float,
    density_ratio: float,
) -> float:
    d_in = (profile.bullet_diameter_mm or 7.82) / 25.4
    l_in = (profile.bullet_length_mm or 32.0) / 25.4
    m_gr = profile.bullet_mass_gr or 168.0
    t_in = profile.twist_rate_in or 10.0
    rho = max(density_ratio, 0.1)
    if d_in <= 0 or l_in <= 0 or t_in <= 0 or velocity_fps <= 0:
        return 0.0
    numerator = 30.0 * m_gr * (velocity_fps / t_in) ** 2
    denominator = rho * (d_in**3) * l_in * (1.0 + (l_in / d_in) ** 2)
    return numerator / denominator if denominator > 0 else 0.0


def _make_click_correction(
    elevation_moa: float,
    elevation_mrad: float,
    windage_moa: float,
    windage_mrad: float,
    clicks_per_moa: float,
    scope_unit: str,
) -> ClickCorrection:
    if scope_unit == "mrad":
        return ClickCorrection(
            elevation_moa=elevation_moa,
            elevation_mrad=elevation_mrad,
            elevation_clicks=elevation_mrad * clicks_per_moa,
            windage_moa=windage_moa,
            windage_mrad=windage_mrad,
            windage_clicks=windage_mrad * clicks_per_moa,
            clicks_per_unit=clicks_per_moa,
            unit="mrad",
        )
    return ClickCorrection(
        elevation_moa=elevation_moa,
        elevation_mrad=elevation_moa * 0.2909,
        elevation_clicks=elevation_moa * clicks_per_moa,
        windage_moa=windage_moa,
        windage_mrad=windage_moa * 0.2909,
        windage_clicks=windage_moa * clicks_per_moa,
        clicks_per_unit=clicks_per_moa,
        unit="moa",
    )


def _empty_solution(
    target: RangeTarget,
    clicks_per_moa: float,
    scope_unit: str,
) -> TargetSolution:
    zero_corr = _make_click_correction(0.0, 0.0, 0.0, 0.0, clicks_per_moa, scope_unit)
    return TargetSolution(
        target=target,
        correction=zero_corr,
        wind_10mps_elevation_moa=0.0,
        wind_10mps_windage_moa=0.0,
        velocity_mps=0.0,
        energy_joules=0.0,
        time_of_flight_s=0.0,
        mach=0.0,
        phase="unknown",
        stability_sg=0.0,
        slant_correction_applied=True,
        inclination_correction_factor=inclination_correction_factor(
            target.inclination_deg
        ),
    )
