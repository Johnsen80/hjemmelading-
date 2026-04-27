"""Monte Carlo dispersion analysis for long-range ballistic solutions.

Runs N trajectory simulations varying MV, BC, and wind within their
uncertainty bounds. Returns CEP50/90/99 and per-source variance breakdown.

No heavy dependencies: uses only the standard library random module for
reproducibility and speed. scipy is used for percentile computation if
available, otherwise a simple sort-based fallback is used.
"""

from __future__ import annotations

import math
import random

from ..utils.advanced_ballistics import AdvancedBallisticsEngine, AtmosphericConditions
from .models import (
    AtmosphereLayer,
    LayeredAtmosphere,
    MonteCarloProfile,
    MonteCarloResult,
    WeaponBallisticProfile,
)

# ---------------------------------------------------------------------------
# Single-distance Monte Carlo
# ---------------------------------------------------------------------------


def run_monte_carlo_at_distance(
    profile: WeaponBallisticProfile,
    atmosphere: LayeredAtmosphere,
    distance_m: float,
    mv_sd_fps: float | None = None,
    bc_uncertainty_pct: float = 0.02,
    wind_uncertainty_mps: float = 0.5,
    iterations: int = 10_000,
    seed: int | None = 42,
    scatter_sample: int = 500,
) -> MonteCarloResult:
    """Run Monte Carlo simulation at one distance.

    Varies:
      - MV: normal distribution around learned_mv_fps with given SD
      - BC: uniform ±bc_uncertainty_pct around learned_bc
      - Wind: normal ±wind_uncertainty_mps around surface wind

    Returns MonteCarloResult with CEP50/90/99 and variance breakdown.
    """
    rng = random.Random(seed)
    surface = atmosphere.surface_layer
    base_mv = profile.mv_at_temperature(surface.temperature_c)
    sd = mv_sd_fps if mv_sd_fps is not None else profile.learned_mv_sd_fps
    sd = max(sd, 0.1)  # avoid zero SD

    conditions_base = _atm_layer_to_conditions(surface)
    base_wind_mph = surface.wind_speed_mps * 2.23694

    engine = AdvancedBallisticsEngine()

    impacts_x: list[float] = []  # windage (cm)
    impacts_y: list[float] = []  # elevation (cm)

    for _ in range(iterations):
        mv = rng.gauss(base_mv, sd)
        bc = profile.learned_bc * (
            1.0 + rng.uniform(-bc_uncertainty_pct, bc_uncertainty_pct)
        )
        wind_delta = rng.gauss(0.0, wind_uncertainty_mps)
        wind_mph = max(0.0, base_wind_mph + wind_delta * 2.23694)

        pts = engine.calculate_trajectory(
            velocity_fps=max(100.0, mv),
            bc=max(0.05, bc),
            weight_grains=profile.bullet_mass_gr or 168.0,
            zero_distance_m=profile.zero_distance_m,
            max_distance_m=distance_m + 5.0,
            step_size_m=distance_m / 2.0 if distance_m > 10 else 5.0,
            bc_type=(
                profile.learned_bc_type
                if profile.learned_bc_type in {"G1", "G7"}
                else "G7"
            ),
            conditions=conditions_base,
            wind_speed_mph=wind_mph,
            wind_angle_deg=90.0,
            latitude_deg=60.0,
            azimuth_deg=0.0,
            twist_rate=profile.twist_rate_in,
            twist_direction=profile.twist_direction,
        )
        pt = _nearest_point(pts, distance_m)
        if pt is None:
            continue
        impacts_x.append(pt.windage_cm)
        impacts_y.append(pt.drop_cm)

    if not impacts_x:
        return _empty_result(distance_m, iterations)

    # Compute radial offsets from mean
    mean_x = sum(impacts_x) / len(impacts_x)
    mean_y = sum(impacts_y) / len(impacts_y)
    radii = [
        math.sqrt((x - mean_x) ** 2 + (y - mean_y) ** 2)
        for x, y in zip(impacts_x, impacts_y)
    ]
    radii_sorted = sorted(radii)
    n = len(radii_sorted)

    cep50 = _percentile(radii_sorted, 0.50)
    cep90 = _percentile(radii_sorted, 0.90)
    cep99 = _percentile(radii_sorted, 0.99)

    v_sd = _std(impacts_y)
    h_sd = _std(impacts_x)

    # Variance attribution: run with each source fixed to mean, compare residual
    mv_var = _variance_from_mv(profile, conditions_base, distance_m, sd, rng, engine)
    bc_var = _variance_from_bc(
        profile, conditions_base, distance_m, bc_uncertainty_pct, rng, engine
    )
    wind_var = _variance_from_wind(
        profile,
        conditions_base,
        distance_m,
        base_wind_mph,
        wind_uncertainty_mps,
        rng,
        engine,
    )
    total_var = mv_var + bc_var + wind_var + 1e-9

    # Sample scatter points
    sample_idx = sorted(random.sample(range(n), min(scatter_sample, n)))
    scatter = [(impacts_x[i] - mean_x, impacts_y[i] - mean_y) for i in sample_idx]

    return MonteCarloResult(
        distance_m=distance_m,
        iterations=len(impacts_x),
        cep50_cm=cep50,
        cep90_cm=cep90,
        cep99_cm=cep99,
        vertical_sd_cm=v_sd,
        horizontal_sd_cm=h_sd,
        mv_contribution_pct=mv_var / total_var * 100.0,
        bc_contribution_pct=bc_var / total_var * 100.0,
        wind_contribution_pct=wind_var / total_var * 100.0,
        impact_points=scatter,
    )


def run_monte_carlo_profile(
    profile: WeaponBallisticProfile,
    atmosphere: LayeredAtmosphere,
    distances_m: list[float] | None = None,
    mv_sd_fps: float | None = None,
    bc_uncertainty_pct: float = 0.02,
    wind_uncertainty_mps: float = 0.5,
    iterations: int = 5_000,
    seed: int | None = 42,
) -> MonteCarloProfile:
    """Run Monte Carlo at multiple distances and return a full profile."""
    if distances_m is None:
        distances_m = [100, 300, 500, 700, 1000]

    results = [
        run_monte_carlo_at_distance(
            profile,
            atmosphere,
            d,
            mv_sd_fps,
            bc_uncertainty_pct,
            wind_uncertainty_mps,
            iterations,
            seed,
        )
        for d in distances_m
    ]
    return MonteCarloProfile(
        results=results,
        mv_sd_fps=mv_sd_fps or profile.learned_mv_sd_fps,
        bc_uncertainty_pct=bc_uncertainty_pct,
        wind_uncertainty_mps=wind_uncertainty_mps,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _atm_layer_to_conditions(layer: AtmosphereLayer) -> AtmosphericConditions:
    temp_f = layer.temperature_c * 9 / 5 + 32
    press_inhg = layer.pressure_hpa * 0.02953
    return AtmosphericConditions(
        temperature_f=temp_f,
        pressure_inhg=press_inhg,
        humidity_percent=layer.humidity_pct,
        altitude_ft=layer.altitude_m * 3.28084,
    )


def _nearest_point(points: list, distance_m: float):
    if not points:
        return None
    return min(points, key=lambda p: abs(p.distance_m - distance_m))


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = max(0, min(len(sorted_vals) - 1, int(p * len(sorted_vals))))
    return sorted_vals[idx]


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))


def _variance_from_mv(
    profile: WeaponBallisticProfile,
    conditions: AtmosphericConditions,
    distance_m: float,
    sd: float,
    rng: random.Random,
    engine: AdvancedBallisticsEngine,
    n: int = 500,
) -> float:
    """Variance in elevation-only from MV changes (BC and wind fixed to nominal)."""
    drops = []
    base_mv = profile.learned_mv_fps
    for _ in range(n):
        mv = rng.gauss(base_mv, sd)
        pts = engine.calculate_trajectory(
            velocity_fps=max(100.0, mv),
            bc=profile.learned_bc,
            weight_grains=profile.bullet_mass_gr or 168.0,
            zero_distance_m=profile.zero_distance_m,
            max_distance_m=distance_m + 5.0,
            step_size_m=max(5.0, distance_m / 2.0),
            bc_type=(
                profile.learned_bc_type
                if profile.learned_bc_type in {"G1", "G7"}
                else "G7"
            ),
            conditions=conditions,
            wind_speed_mph=0.0,
            wind_angle_deg=90.0,
            latitude_deg=60.0,
            azimuth_deg=0.0,
            twist_rate=profile.twist_rate_in,
            twist_direction=profile.twist_direction,
        )
        pt = _nearest_point(pts, distance_m)
        if pt:
            drops.append(pt.drop_cm)
    return _std(drops) ** 2


def _variance_from_bc(
    profile: WeaponBallisticProfile,
    conditions: AtmosphericConditions,
    distance_m: float,
    bc_pct: float,
    rng: random.Random,
    engine: AdvancedBallisticsEngine,
    n: int = 500,
) -> float:
    drops = []
    base_mv = profile.learned_mv_fps
    for _ in range(n):
        bc = profile.learned_bc * (1.0 + rng.uniform(-bc_pct, bc_pct))
        pts = engine.calculate_trajectory(
            velocity_fps=base_mv,
            bc=max(0.05, bc),
            weight_grains=profile.bullet_mass_gr or 168.0,
            zero_distance_m=profile.zero_distance_m,
            max_distance_m=distance_m + 5.0,
            step_size_m=max(5.0, distance_m / 2.0),
            bc_type=(
                profile.learned_bc_type
                if profile.learned_bc_type in {"G1", "G7"}
                else "G7"
            ),
            conditions=conditions,
            wind_speed_mph=0.0,
            wind_angle_deg=90.0,
            latitude_deg=60.0,
            azimuth_deg=0.0,
            twist_rate=profile.twist_rate_in,
            twist_direction=profile.twist_direction,
        )
        pt = _nearest_point(pts, distance_m)
        if pt:
            drops.append(pt.drop_cm)
    return _std(drops) ** 2


def _variance_from_wind(
    profile: WeaponBallisticProfile,
    conditions: AtmosphericConditions,
    distance_m: float,
    base_wind_mph: float,
    wind_sd_mps: float,
    rng: random.Random,
    engine: AdvancedBallisticsEngine,
    n: int = 500,
) -> float:
    drifts = []
    base_mv = profile.learned_mv_fps
    for _ in range(n):
        wind_delta = rng.gauss(0.0, wind_sd_mps)
        wind_mph = max(0.0, base_wind_mph + wind_delta * 2.23694)
        pts = engine.calculate_trajectory(
            velocity_fps=base_mv,
            bc=profile.learned_bc,
            weight_grains=profile.bullet_mass_gr or 168.0,
            zero_distance_m=profile.zero_distance_m,
            max_distance_m=distance_m + 5.0,
            step_size_m=max(5.0, distance_m / 2.0),
            bc_type=(
                profile.learned_bc_type
                if profile.learned_bc_type in {"G1", "G7"}
                else "G7"
            ),
            conditions=conditions,
            wind_speed_mph=wind_mph,
            wind_angle_deg=90.0,
            latitude_deg=60.0,
            azimuth_deg=0.0,
            twist_rate=profile.twist_rate_in,
            twist_direction=profile.twist_direction,
        )
        pt = _nearest_point(pts, distance_m)
        if pt:
            drifts.append(pt.windage_cm)
    return _std(drifts) ** 2


def _empty_result(distance_m: float, iterations: int) -> MonteCarloResult:
    return MonteCarloResult(
        distance_m=distance_m,
        iterations=iterations,
        cep50_cm=0.0,
        cep90_cm=0.0,
        cep99_cm=0.0,
        vertical_sd_cm=0.0,
        horizontal_sd_cm=0.0,
        mv_contribution_pct=0.0,
        bc_contribution_pct=0.0,
        wind_contribution_pct=0.0,
    )


# ---------------------------------------------------------------------------
# Add missing import to atmosphere.py (bridge function)
# ---------------------------------------------------------------------------


def _layer_to_conditions_dict(layer: AtmosphereLayer) -> dict:
    return {
        "temperature_c": layer.temperature_c,
        "pressure_hpa": layer.pressure_hpa,
        "humidity_pct": layer.humidity_pct,
        "altitude_m": layer.altitude_m,
    }
