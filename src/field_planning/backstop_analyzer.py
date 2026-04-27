"""Backstop safety analysis for hunting scenarios.

Analyses the bullet trajectory beyond the target to determine whether the shot
is safe. For each aim point, extends the shot line past the target, intersects
the bullet arc with the terrain profile, and checks habitation proximity.

Safety verdicts:
  "safe"    — bullet hits ground within acceptable range, low energy at impact
  "caution" — bullet flies long or hits ground with high energy
  "unsafe"  — bullet may reach known habitation, or trajectory unclear

Input: lists of (distance_m, elevation_m) terrain points beyond the target.
Elevation profile must extend at least to max_effective_range_m past the target.
"""

from __future__ import annotations

import math

from ..utils.advanced_ballistics import AdvancedBallisticsEngine, AtmosphericConditions
from .models import (
    AtmosphereLayer,
    BackstopAnalysis,
    GeoPoint,
    LayeredAtmosphere,
    WeaponBallisticProfile,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FPS_TO_MPS = 0.3048
_FT_LBS_TO_J = 1.35582
_MIN_SAFE_ENERGY_J = 80.0  # below this at ground impact → safe (legal standard)
_MAX_SCAN_RANGE_M = 8000.0  # stop looking for ground impact beyond this


# ---------------------------------------------------------------------------
# Terrain helpers
# ---------------------------------------------------------------------------


def interpolate_elevation(
    terrain_points: list[tuple[float, float]],
    distance_m: float,
) -> float | None:
    """Interpolate terrain elevation at given distance. Returns None if out of range."""
    if not terrain_points:
        return None
    if distance_m < terrain_points[0][0]:
        return None
    if distance_m > terrain_points[-1][0]:
        return None
    for i in range(len(terrain_points) - 1):
        d0, e0 = terrain_points[i]
        d1, e1 = terrain_points[i + 1]
        if d0 <= distance_m <= d1:
            frac = (distance_m - d0) / (d1 - d0) if d1 != d0 else 0.0
            return e0 + frac * (e1 - e0)
    return terrain_points[-1][1]


def find_ground_intersection(
    trajectory_arc: list[tuple[float, float]],
    terrain_points: list[tuple[float, float]],
) -> float | None:
    """Find the distance where bullet arc first crosses terrain elevation.

    Parameters
    ----------
    trajectory_arc:
        List of (distance_m, bullet_height_m_above_origin) tuples.
    terrain_points:
        List of (distance_m, terrain_elevation_m_above_origin) tuples.

    Returns distance_m of first intersection, or None if no hit found.
    """
    for dist, bullet_h in trajectory_arc:
        terrain_h = interpolate_elevation(terrain_points, dist)
        if terrain_h is not None and bullet_h <= terrain_h:
            return dist
    return None


def max_ordinate_above_terrain(
    trajectory_arc: list[tuple[float, float]],
    terrain_points: list[tuple[float, float]],
) -> float:
    """Return the maximum height of bullet above terrain along the trajectory."""
    max_clearance = 0.0
    for dist, bullet_h in trajectory_arc:
        terrain_h = interpolate_elevation(terrain_points, dist)
        if terrain_h is not None:
            clearance = bullet_h - terrain_h
            max_clearance = max(max_clearance, clearance)
    return max_clearance


# ---------------------------------------------------------------------------
# Backstop verdict
# ---------------------------------------------------------------------------


def compute_backstop_verdict(
    ground_intersection_m: float | None,
    bullet_energy_at_ground_j: float,
    nearest_habitation_m: float | None,
    max_scan_range_m: float = _MAX_SCAN_RANGE_M,
) -> tuple[str, str, str]:
    """Determine verdict, reason, and color for a backstop analysis.

    Returns (verdict, reason, color):
      "safe"    / "green"
      "caution" / "orange"
      "unsafe"  / "red"
    """
    if ground_intersection_m is None:
        # Bullet flies beyond scan range → unknown
        if nearest_habitation_m is not None and nearest_habitation_m < max_scan_range_m:
            return (
                "unsafe",
                "Kule treffer ingen terrenghindrning innen rekkevidde — bebyggelse i skuddlinje",
                "red",
            )
        return (
            "caution",
            f"Kule treffer ikke terrenget innen {max_scan_range_m:.0f}m — langt skuddlinje",
            "orange",
        )

    # Bullet hits ground
    if (
        nearest_habitation_m is not None
        and nearest_habitation_m < ground_intersection_m * 1.1
    ):
        return (
            "unsafe",
            (
                f"Bebyggelse {nearest_habitation_m:.0f}m unna — for nær kulebanen "
                f"(terrengtreffer ved {ground_intersection_m:.0f}m)"
            ),
            "red",
        )

    if bullet_energy_at_ground_j > 500.0:
        return (
            "caution",
            (
                f"Kule treffer terreng ved {ground_intersection_m:.0f}m med "
                f"{bullet_energy_at_ground_j:.0f}J — høy restenergi"
            ),
            "orange",
        )

    if bullet_energy_at_ground_j > _MIN_SAFE_ENERGY_J:
        return (
            "caution",
            (
                f"Kule treffer terreng ved {ground_intersection_m:.0f}m med "
                f"{bullet_energy_at_ground_j:.0f}J"
            ),
            "orange",
        )

    return (
        "safe",
        (
            f"Kule treffer terreng ved {ground_intersection_m:.0f}m, "
            f"restenergi {bullet_energy_at_ground_j:.0f}J"
        ),
        "green",
    )


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------


def analyse_backstop(
    profile: WeaponBallisticProfile,
    atmosphere: LayeredAtmosphere,
    aim_point: GeoPoint,
    bearing_deg: float,
    slant_range_m: float,
    terrain_points: list[tuple[float, float]],
    nearest_habitation_m: float | None = None,
    nearest_habitation_bearing_deg: float | None = None,
    nearest_habitation_label: str = "",
    max_scan_range_m: float = _MAX_SCAN_RANGE_M,
    latitude_deg: float = 60.0,
) -> BackstopAnalysis:
    """Perform full backstop safety analysis for one aim point.

    Parameters
    ----------
    terrain_points:
        (distance_m, elevation_m_above_origin) pairs along the shot line,
        starting from the shooter position (distance_m=0 = shooter).
    """
    surface = atmosphere.surface_layer
    mv_fps = profile.mv_at_temperature(surface.temperature_c)
    conditions = _layer_to_conditions(surface)
    engine = AdvancedBallisticsEngine()

    wind_angle = _wind_angle(surface.wind_dir_deg, bearing_deg)
    wind_mph = surface.wind_speed_mps * 2.23694

    raw = engine.calculate_trajectory(
        velocity_fps=max(100.0, mv_fps),
        bc=max(0.05, profile.learned_bc),
        weight_grains=profile.bullet_mass_gr or 168.0,
        zero_distance_m=profile.zero_distance_m,
        max_distance_m=min(max_scan_range_m, _MAX_SCAN_RANGE_M) + 5.0,
        step_size_m=max(10.0, min(max_scan_range_m, _MAX_SCAN_RANGE_M) / 200.0),
        bc_type=(
            profile.learned_bc_type if profile.learned_bc_type in {"G1", "G7"} else "G7"
        ),
        conditions=conditions,
        wind_speed_mph=wind_mph,
        wind_angle_deg=wind_angle,
        latitude_deg=latitude_deg,
        azimuth_deg=bearing_deg,
        twist_rate=profile.twist_rate_in,
        twist_direction=profile.twist_direction,
    )

    if not raw:
        return _empty_analysis(aim_point, bearing_deg, slant_range_m)

    # Build bullet arc: (distance_m, height_above_origin_m)
    # The bullet "height" is: shooter_height + cumulative_elevation_change - drop
    # Since drop_cm is measured relative to zero (sight line), and we don't have
    # shooter/terrain elevation in this function, we use drop_cm inverted as height.
    # terrain_points are (distance_m, height_m) where height=0 at shooter.
    shooter_elev = interpolate_elevation(terrain_points, 0.0) or 0.0

    bullet_arc: list[tuple[float, float]] = []
    for pt in raw:
        # Bullet height above origin: zero at shooter position, corrected for drop
        # drop_cm > 0 means bullet is below zero line → below sight line
        # Shooter's sight line at distance d: shooter_elev (approx flat for backstop)
        bullet_h = shooter_elev - pt.drop_cm / 100.0
        bullet_arc.append((pt.distance_m, bullet_h))

    ground_intersection_m = find_ground_intersection(bullet_arc, terrain_points)
    max_ord_m = max_ordinate_above_terrain(bullet_arc, terrain_points)

    # Energy and velocity at ground intersection
    energy_at_ground_j = 0.0
    velocity_at_ground_mps = 0.0
    is_subsonic = False

    if ground_intersection_m is not None:
        pt_ground = min(raw, key=lambda p: abs(p.distance_m - ground_intersection_m))
        energy_at_ground_j = pt_ground.energy_ftlbs * _FT_LBS_TO_J
        velocity_at_ground_mps = pt_ground.velocity_fps * _FPS_TO_MPS
        sos = 331.3 * math.sqrt(1.0 + surface.temperature_c / 273.15)
        is_subsonic = (velocity_at_ground_mps / sos) < 1.0

    verdict, reason, color = compute_backstop_verdict(
        ground_intersection_m,
        energy_at_ground_j,
        nearest_habitation_m,
        max_scan_range_m,
    )

    return BackstopAnalysis(
        point=aim_point,
        bearing_deg=bearing_deg,
        slant_range_m=slant_range_m,
        ground_intersection_m=ground_intersection_m,
        max_ordinate_m=max_ord_m,
        bullet_energy_at_ground_j=energy_at_ground_j,
        bullet_velocity_at_ground_mps=velocity_at_ground_mps,
        is_subsonic_at_ground=is_subsonic,
        nearest_habitation_m=nearest_habitation_m,
        nearest_habitation_bearing_deg=nearest_habitation_bearing_deg,
        nearest_habitation_label=nearest_habitation_label,
        verdict=verdict,
        verdict_reason=reason,
        color=color,
    )


# ---------------------------------------------------------------------------
# Ethical range computation
# ---------------------------------------------------------------------------


def compute_ethical_range(
    profile: WeaponBallisticProfile,
    atmosphere: LayeredAtmosphere,
    min_energy_j: float,
    bearing_deg: float = 0.0,
    latitude_deg: float = 60.0,
    max_range_m: float = 2000.0,
) -> float:
    """Return maximum range (m) where bullet energy >= min_energy_j."""
    surface = atmosphere.surface_layer
    mv_fps = profile.mv_at_temperature(surface.temperature_c)
    conditions = _layer_to_conditions(surface)
    engine = AdvancedBallisticsEngine()

    raw = engine.calculate_trajectory(
        velocity_fps=max(100.0, mv_fps),
        bc=max(0.05, profile.learned_bc),
        weight_grains=profile.bullet_mass_gr or 168.0,
        zero_distance_m=profile.zero_distance_m,
        max_distance_m=max_range_m + 5.0,
        step_size_m=max(5.0, max_range_m / 200.0),
        bc_type=(
            profile.learned_bc_type if profile.learned_bc_type in {"G1", "G7"} else "G7"
        ),
        conditions=conditions,
        wind_speed_mph=0.0,
        wind_angle_deg=90.0,
        latitude_deg=latitude_deg,
        azimuth_deg=bearing_deg,
        twist_rate=profile.twist_rate_in,
        twist_direction=profile.twist_direction,
    )

    last_ok = 0.0
    for pt in raw:
        energy_j = pt.energy_ftlbs * _FT_LBS_TO_J
        if energy_j >= min_energy_j:
            last_ok = pt.distance_m
    return last_ok


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _layer_to_conditions(layer: AtmosphereLayer) -> AtmosphericConditions:
    return AtmosphericConditions(
        temperature_f=layer.temperature_c * 9 / 5 + 32,
        pressure_inhg=layer.pressure_hpa * 0.02953,
        humidity_percent=layer.humidity_pct,
        altitude_ft=layer.altitude_m * 3.28084,
    )


def _wind_angle(wind_dir_deg: float, bearing_deg: float) -> float:
    return (wind_dir_deg - bearing_deg + 180) % 360


def _empty_analysis(
    aim_point: GeoPoint,
    bearing_deg: float,
    slant_range_m: float,
) -> BackstopAnalysis:
    return BackstopAnalysis(
        point=aim_point,
        bearing_deg=bearing_deg,
        slant_range_m=slant_range_m,
        ground_intersection_m=None,
        max_ordinate_m=0.0,
        bullet_energy_at_ground_j=0.0,
        bullet_velocity_at_ground_mps=0.0,
        is_subsonic_at_ground=False,
        nearest_habitation_m=None,
        nearest_habitation_bearing_deg=None,
        verdict="unknown",
        verdict_reason="Ingen data",
        color="gray",
    )
