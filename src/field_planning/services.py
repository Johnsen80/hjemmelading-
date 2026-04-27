"""Field planning orchestration — build complete ballistic field solutions.

Primary entry points:
  build_field_solution()     — full trajectory + DOPE for one shooter/target pair
  build_dope_card()          — DOPE card rows for a range of distances
  compute_stability_sg()     — gyroscopic stability factor (Miller formula)
  compute_mach()             — Mach number from velocity and local speed of sound
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from ..ballistics.types import BallisticInput
from ..utils.advanced_ballistics import AdvancedBallisticsEngine, AtmosphericConditions
from .models import (
    AtmosphereLayer,
    ClickCorrection,
    DopeCard,
    DopeRow,
    EnrichedTrajectoryPoint,
    FieldSession,
    FieldTarget,
    LayeredAtmosphere,
    WeaponBallisticProfile,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FPS_TO_MPS = 0.3048
_MPS_TO_FPS = 1.0 / _FPS_TO_MPS
_FT_LBS_TO_J = 1.35582
_G7_REF_DENSITY = 1.225  # ICAO sea level air density kg/m³


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_field_solution(
    session: FieldSession,
    target: FieldTarget,
    step_m: float = 10.0,
) -> list[EnrichedTrajectoryPoint]:
    """Compute a full enriched trajectory for one shooter→target pair.

    Uses the weapon profile from session, shoots at target's slant range and
    inclination. Returns one EnrichedTrajectoryPoint per step_m.
    """
    profile = session.profile
    atm = session.atmosphere or _default_atmosphere()
    surface_layer = atm.surface_layer

    mv_fps = profile.mv_at_temperature(surface_layer.temperature_c)

    conditions = _layer_to_conditions(surface_layer)

    engine = AdvancedBallisticsEngine()
    max_dist = max(target.slant_distance_m or target.distance_m, step_m) + step_m

    raw_points = engine.calculate_trajectory(
        velocity_fps=mv_fps,
        bc=profile.learned_bc,
        weight_grains=profile.bullet_mass_gr or 168.0,
        zero_distance_m=profile.zero_distance_m,
        max_distance_m=max_dist,
        step_size_m=step_m,
        bc_type=(
            profile.learned_bc_type if profile.learned_bc_type in {"G1", "G7"} else "G7"
        ),
        conditions=conditions,
        wind_speed_mph=surface_layer.wind_speed_mps * 2.23694,
        wind_angle_deg=_wind_angle_for_azimuth(
            surface_layer.wind_dir_deg, session.azimuth_deg
        ),
        latitude_deg=session.latitude_deg,
        azimuth_deg=session.azimuth_deg,
        twist_rate=profile.twist_rate_in,
        twist_direction=profile.twist_direction,
    )

    sos = _speed_of_sound_mps(surface_layer.temperature_c)
    enriched = []
    for pt in raw_points:
        vel_mps = pt.velocity_fps * _FPS_TO_MPS
        mach = vel_mps / sos if sos > 0 else 0.0
        phase = _mach_phase(mach)
        sg = compute_stability_sg(
            bullet_diameter_mm=profile.bullet_diameter_mm or 7.82,
            bullet_length_mm=profile.bullet_length_mm or 32.0,
            bullet_mass_gr=profile.bullet_mass_gr or 168.0,
            twist_rate_in=profile.twist_rate_in,
            velocity_fps=pt.velocity_fps,
            density_ratio=surface_layer.density_ratio,
        )
        energy_j = pt.energy_ftlbs * _FT_LBS_TO_J

        etp = EnrichedTrajectoryPoint(
            distance_m=pt.distance_m,
            time_s=pt.time_s,
            velocity_fps=pt.velocity_fps,
            velocity_mps=vel_mps,
            mach=mach,
            phase=phase,
            drop_cm=pt.drop_cm,
            drop_moa=pt.drop_moa,
            drop_mrad=pt.drop_mrad,
            windage_cm=pt.windage_cm,
            windage_moa=pt.windage_moa,
            windage_mrad=pt.windage_mrad,
            energy_ftlbs=pt.energy_ftlbs,
            energy_joules=energy_j,
            stability_sg=sg,
            stability_status=_sg_status(sg),
            bullet_altitude_m=0.0,  # set by terrain enrichment in blokk 4
            height_above_ground_m=0.0,
            atmosphere_layer=surface_layer,
            wind_drift_cm=getattr(pt, "wind_drift_cm", pt.windage_cm),
            spin_drift_cm=getattr(pt, "drift_spin_cm", 0.0),
            coriolis_cm=getattr(pt, "drift_coriolis_cm", 0.0),
        )
        enriched.append(etp)

    return enriched


def build_dope_card(
    session: FieldSession,
    distances_m: list[float] | None = None,
    wind_reference_mps: float = 10.0,
) -> DopeCard:
    """Build a complete DOPE card for the given session.

    Parameters
    ----------
    session:
        Active FieldSession with profile + atmosphere set.
    distances_m:
        Distances to include. Defaults to [100, 200, 300, 400, 500, 600, 700, 800, 1000].
    wind_reference_mps:
        Wind speed to compute full-value wind column (default 10 m/s).
    """
    if distances_m is None:
        distances_m = [100, 200, 300, 400, 500, 600, 700, 800, 1000]

    max_dist = max(distances_m) + 10.0
    profile = session.profile
    atm = session.atmosphere or _default_atmosphere()
    surface = atm.surface_layer

    mv_fps = profile.mv_at_temperature(surface.temperature_c)
    conditions = _layer_to_conditions(surface)
    wind_mph = surface.wind_speed_mps * 2.23694
    wind_angle = _wind_angle_for_azimuth(surface.wind_dir_deg, session.azimuth_deg)
    wind_ref_mph = wind_reference_mps * 2.23694

    engine = AdvancedBallisticsEngine()

    raw_points = engine.calculate_trajectory(
        velocity_fps=mv_fps,
        bc=profile.learned_bc,
        weight_grains=profile.bullet_mass_gr or 168.0,
        zero_distance_m=profile.zero_distance_m,
        max_distance_m=max_dist,
        step_size_m=1.0,
        bc_type=(
            profile.learned_bc_type if profile.learned_bc_type in {"G1", "G7"} else "G7"
        ),
        conditions=conditions,
        wind_speed_mph=wind_mph,
        wind_angle_deg=wind_angle,
        latitude_deg=session.latitude_deg,
        azimuth_deg=session.azimuth_deg,
        twist_rate=profile.twist_rate_in,
        twist_direction=profile.twist_direction,
    )

    # Build reference wind trajectory (full-value 10 m/s)
    raw_wind_ref = engine.calculate_trajectory(
        velocity_fps=mv_fps,
        bc=profile.learned_bc,
        weight_grains=profile.bullet_mass_gr or 168.0,
        zero_distance_m=profile.zero_distance_m,
        max_distance_m=max_dist,
        step_size_m=1.0,
        bc_type=(
            profile.learned_bc_type if profile.learned_bc_type in {"G1", "G7"} else "G7"
        ),
        conditions=conditions,
        wind_speed_mph=wind_ref_mph,
        wind_angle_deg=90.0,  # full-value crosswind
        latitude_deg=session.latitude_deg,
        azimuth_deg=session.azimuth_deg,
        twist_rate=profile.twist_rate_in,
        twist_direction=profile.twist_direction,
    )

    # Index by distance
    by_dist = {round(p.distance_m): p for p in raw_points}
    wind_by_dist = {round(p.distance_m): p for p in raw_wind_ref}

    sos = _speed_of_sound_mps(surface.temperature_c)
    rows: list[DopeRow] = []

    for d in distances_m:
        pt = _nearest(by_dist, d)
        if pt is None:
            continue
        wind_pt = _nearest(wind_by_dist, d)

        mach = (pt.velocity_fps * _FPS_TO_MPS) / sos if sos > 0 else 0.0
        phase = _mach_phase(mach)

        corr = _make_click_correction(
            elevation_moa=pt.drop_moa,
            windage_moa=pt.windage_moa,
            clicks_per_moa=session.clicks_per_moa,
            unit=session.scope_unit,
        )

        wind_10_moa = wind_pt.windage_moa if wind_pt else None

        rows.append(
            DopeRow(
                distance_m=float(d),
                correction=corr,
                velocity_mps=pt.velocity_fps * _FPS_TO_MPS,
                energy_joules=pt.energy_ftlbs * _FT_LBS_TO_J,
                time_of_flight_s=pt.time_s,
                phase=phase,
                wind_10mps_moa=wind_10_moa,
            )
        )

    conditions_summary = _format_conditions(surface)

    return DopeCard(
        rifle_name=profile.rifle_name,
        ammo_label=profile.ammo_label,
        zero_distance_m=profile.zero_distance_m,
        conditions_summary=conditions_summary,
        rows=rows,
        learned_bc=profile.learned_bc,
        learned_mv_fps=mv_fps,
        learned_mv_sd_fps=profile.learned_mv_sd_fps,
        bc_source=profile.bc_source,
        mv_source=profile.mv_source,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        atmosphere_warnings=list(atm.warnings),
    )


def compute_zero_shift_clicks(
    profile_from: WeaponBallisticProfile,
    profile_to: WeaponBallisticProfile,
    atmosphere: LayeredAtmosphere | None = None,
    clicks_per_moa: float = 4.0,
) -> tuple[float, float]:
    """Return (elevation_clicks, windage_clicks) to move zero from one load to another.

    Both loads are evaluated at their respective MVs at current temperature.
    The difference at zero_distance_m gives the required correction.
    """
    atm = atmosphere or _default_atmosphere()
    surface = atm.surface_layer
    conditions = _layer_to_conditions(surface)
    engine = AdvancedBallisticsEngine()

    def _impact_at_zero(profile: WeaponBallisticProfile) -> tuple[float, float]:
        mv = profile.mv_at_temperature(surface.temperature_c)
        pts = engine.calculate_trajectory(
            velocity_fps=mv,
            bc=profile.learned_bc,
            weight_grains=profile.bullet_mass_gr or 168.0,
            zero_distance_m=profile.zero_distance_m,
            max_distance_m=profile.zero_distance_m + 10.0,
            step_size_m=1.0,
            bc_type=(
                profile.learned_bc_type
                if profile.learned_bc_type in {"G1", "G7"}
                else "G7"
            ),
            conditions=conditions,
            latitude_deg=60.0,
            azimuth_deg=0.0,
            twist_rate=profile.twist_rate_in,
            twist_direction=profile.twist_direction,
        )
        closest = _nearest(
            {round(p.distance_m): p for p in pts}, profile.zero_distance_m
        )
        if closest is None:
            return 0.0, 0.0
        return closest.drop_moa, closest.windage_moa

    drop_from, wind_from = _impact_at_zero(profile_from)
    drop_to, wind_to = _impact_at_zero(profile_to)

    delta_elev_moa = drop_to - drop_from
    delta_wind_moa = wind_to - wind_from

    return delta_elev_moa * clicks_per_moa, delta_wind_moa * clicks_per_moa


# ---------------------------------------------------------------------------
# Physics helpers
# ---------------------------------------------------------------------------


def compute_stability_sg(
    bullet_diameter_mm: float,
    bullet_length_mm: float,
    bullet_mass_gr: float,
    twist_rate_in: float,
    velocity_fps: float,
    density_ratio: float = 1.0,
) -> float:
    """Miller Twist Rule gyroscopic stability factor.

    Returns Sg. Values:
      Sg < 1.0  → unstable (tumbling)
      1.0–1.4   → marginal
      1.4–2.0   → optimal
      > 2.0     → over-stabilised (possible accuracy loss at long range)
    """
    if not all(
        [
            bullet_diameter_mm,
            bullet_length_mm,
            bullet_mass_gr,
            twist_rate_in,
            velocity_fps,
        ]
    ):
        return 0.0

    d_in = bullet_diameter_mm / 25.4  # inches
    l_in = bullet_length_mm / 25.4  # inches
    m_gr = bullet_mass_gr
    t_in = twist_rate_in  # inches per turn
    v_fps = velocity_fps
    rho = max(density_ratio, 0.1)

    if d_in <= 0 or l_in <= 0 or t_in <= 0 or v_fps <= 0:
        return 0.0

    l_over_d = l_in / d_in

    # Miller: Sg = (30 * m) / (rho * d³ * l * (1 + l²/d²)) × (v/t)²
    # where m in grains, d in inches, l in inches, t in in/turn, v in fps
    numerator = 30.0 * m_gr * (v_fps / t_in) ** 2
    denominator = rho * (d_in**3) * l_in * (1.0 + l_over_d**2)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def compute_mach(velocity_fps: float, temperature_c: float) -> float:
    """Mach number at given temperature."""
    sos = _speed_of_sound_mps(temperature_c) * _MPS_TO_FPS
    return velocity_fps / sos if sos > 0 else 0.0


def find_subsonic_range(
    trajectory: list[EnrichedTrajectoryPoint],
) -> float | None:
    """Return distance (m) where bullet first drops below Mach 1.0. None if always supersonic."""
    for pt in trajectory:
        if pt.mach < 1.0:
            return pt.distance_m
    return None


def find_ethical_range(
    trajectory: list[EnrichedTrajectoryPoint],
    min_energy_j: float,
) -> float | None:
    """Return max distance (m) where energy >= min_energy_j. None if never reached."""
    last_ok: float | None = None
    for pt in trajectory:
        if pt.energy_joules >= min_energy_j:
            last_ok = pt.distance_m
    return last_ok


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_ballistic_input(
    profile: WeaponBallisticProfile,
    mv_fps: float,
) -> BallisticInput:
    from ..ballistics.types import BCModel

    return BallisticInput(
        mv_mps=mv_fps * _FPS_TO_MPS,
        bc=profile.learned_bc,
        bc_model=BCModel.G7 if profile.learned_bc_type == "G7" else BCModel.G1,
        bullet_mass_gr=profile.bullet_mass_gr or 168.0,
        caliber_mm=profile.bullet_diameter_mm or 7.82,
        sight_height_mm=profile.sight_height_mm,
        zero_distance_m=profile.zero_distance_m,
        spin_twist=profile.twist_rate_in,
        drag_function=(
            profile.learned_bc_type if profile.learned_bc_type in {"G1", "G7"} else "G7"
        ),
    )


def _layer_to_conditions(layer: AtmosphereLayer) -> AtmosphericConditions:
    temp_f = layer.temperature_c * 9 / 5 + 32
    pressure_inhg = layer.pressure_hpa * 0.02953
    return AtmosphericConditions(
        temperature_f=temp_f,
        pressure_inhg=pressure_inhg,
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
    """Speed of sound in dry air at given temperature (m/s)."""
    return 331.3 * math.sqrt(1.0 + temperature_c / 273.15)


def _mach_phase(mach: float) -> str:
    if mach >= 1.2:
        return "supersonic"
    if mach >= 0.9:
        return "transonic"
    return "subsonic"


def _sg_status(sg: float) -> str:
    if sg <= 0:
        return "unknown"
    if sg < 1.0:
        return "unstable"
    if sg < 1.4:
        return "marginal"
    return "stable"


def _wind_angle_for_azimuth(wind_dir_deg: float, azimuth_deg: float) -> float:
    """Convert met wind direction + shooting azimuth → relative wind angle for engine.

    Engine uses: 0° = headwind, 90° = full right crosswind, 180° = tailwind.
    Wind direction is meteorological (direction wind comes FROM).
    """
    # Wind blows FROM wind_dir_deg. Bullet travels toward azimuth_deg.
    # Relative angle of wind hitting bullet
    relative = (wind_dir_deg - azimuth_deg + 180) % 360
    return relative


def _make_click_correction(
    elevation_moa: float,
    windage_moa: float,
    clicks_per_moa: float,
    unit: str,
) -> ClickCorrection:
    if unit == "mrad":
        elev_mrad = elevation_moa * 0.2909
        wind_mrad = windage_moa * 0.2909
        return ClickCorrection(
            elevation_moa=elevation_moa,
            elevation_mrad=elev_mrad,
            elevation_clicks=elev_mrad * clicks_per_moa,
            windage_moa=windage_moa,
            windage_mrad=wind_mrad,
            windage_clicks=wind_mrad * clicks_per_moa,
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


def _nearest(by_dist: dict[int, Any], target: float) -> Any | None:
    if not by_dist:
        return None
    key = min(by_dist.keys(), key=lambda k: abs(k - target))
    return by_dist[key]


def _format_conditions(layer: AtmosphereLayer) -> str:
    da = int(layer.density_altitude_m)
    return (
        f"{layer.temperature_c:.1f}°C, "
        f"{layer.pressure_hpa:.1f} hPa, "
        f"{int(layer.humidity_pct)}% RH, "
        f"DA {da}m"
    )
