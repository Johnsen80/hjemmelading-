"""Block 5 tests: Monte Carlo dispersion analysis."""

from __future__ import annotations

from src.field_planning.atmosphere import build_layered_atmosphere
from src.field_planning.models import WeaponBallisticProfile
from src.field_planning.monte_carlo import (
    run_monte_carlo_at_distance,
    run_monte_carlo_profile,
)


def _profile(**kwargs) -> WeaponBallisticProfile:
    defaults = dict(
        rifle_id=1,
        rifle_name="Test",
        caliber="308 Win",
        barrel_configuration_id=None,
        twist_rate_in=10.0,
        twist_direction="RIGHT",
        sight_height_mm=38.0,
        zero_distance_m=100.0,
        learned_mv_fps=2650.0,
        learned_mv_sd_fps=10.0,
        learned_bc=0.223,
        learned_bc_type="G7",
        bc_source="ammo_profile",
        mv_source="chrono_sessions",
        bullet_diameter_mm=7.82,
        bullet_length_mm=32.0,
        bullet_mass_gr=175.0,
    )
    defaults.update(kwargs)
    return WeaponBallisticProfile(**defaults)


def _atm(temp=15.0, wind=2.0):
    return build_layered_atmosphere(temp, 1013.25, 50.0, wind, 270.0)


# ---------------------------------------------------------------------------
# Basic results
# ---------------------------------------------------------------------------


def test_monte_carlo_returns_result():
    r = run_monte_carlo_at_distance(_profile(), _atm(), 500.0, iterations=200)
    assert r.distance_m == 500.0
    assert r.iterations > 0


def test_monte_carlo_cep_order():
    r = run_monte_carlo_at_distance(_profile(), _atm(), 500.0, iterations=300)
    assert r.cep50_cm <= r.cep90_cm <= r.cep99_cm


def test_monte_carlo_cep_positive():
    r = run_monte_carlo_at_distance(_profile(), _atm(), 500.0, iterations=300)
    assert r.cep50_cm > 0.0
    assert r.cep90_cm > 0.0


def test_monte_carlo_contributions_sum_near_100():
    r = run_monte_carlo_at_distance(_profile(), _atm(), 500.0, iterations=300)
    total = r.mv_contribution_pct + r.bc_contribution_pct + r.wind_contribution_pct
    # Not exactly 100 due to covariance, but should be in range
    assert 50.0 < total < 250.0


def test_monte_carlo_has_scatter_points():
    r = run_monte_carlo_at_distance(
        _profile(), _atm(), 500.0, iterations=300, scatter_sample=50
    )
    assert len(r.impact_points) > 0


# ---------------------------------------------------------------------------
# Sensitivity: higher SD → larger CEP
# ---------------------------------------------------------------------------


def test_higher_mv_sd_gives_larger_cep():
    r_tight = run_monte_carlo_at_distance(
        _profile(learned_mv_sd_fps=5.0),
        _atm(),
        600.0,
        mv_sd_fps=5.0,
        iterations=400,
    )
    r_loose = run_monte_carlo_at_distance(
        _profile(learned_mv_sd_fps=30.0),
        _atm(),
        600.0,
        mv_sd_fps=30.0,
        iterations=400,
    )
    assert r_loose.cep90_cm > r_tight.cep90_cm


def test_cep_grows_with_distance():
    r_close = run_monte_carlo_at_distance(_profile(), _atm(), 200.0, iterations=300)
    r_far = run_monte_carlo_at_distance(_profile(), _atm(), 800.0, iterations=300)
    assert r_far.cep90_cm > r_close.cep90_cm


def test_no_wind_uncertainty_reduces_horizontal_sd():
    r_nowind = run_monte_carlo_at_distance(
        _profile(),
        _atm(wind=0.0),
        500.0,
        wind_uncertainty_mps=0.0,
        iterations=300,
    )
    r_wind = run_monte_carlo_at_distance(
        _profile(),
        _atm(wind=3.0),
        500.0,
        wind_uncertainty_mps=2.0,
        iterations=300,
    )
    assert r_wind.horizontal_sd_cm >= r_nowind.horizontal_sd_cm


# ---------------------------------------------------------------------------
# Profile (multiple distances)
# ---------------------------------------------------------------------------


def test_monte_carlo_profile_returns_all_distances():
    distances = [200.0, 400.0, 600.0]
    prof = run_monte_carlo_profile(
        _profile(), _atm(), distances_m=distances, iterations=200
    )
    result_dists = [r.distance_m for r in prof.results]
    for d in distances:
        assert d in result_dists


def test_monte_carlo_profile_cep_increases_with_distance():
    distances = [200.0, 500.0, 800.0]
    prof = run_monte_carlo_profile(
        _profile(), _atm(), distances_m=distances, iterations=300
    )
    ceps = [r.cep90_cm for r in prof.results]
    assert ceps[0] < ceps[-1]


def test_monte_carlo_profile_stores_parameters():
    prof = run_monte_carlo_profile(
        _profile(),
        _atm(),
        distances_m=[300.0],
        mv_sd_fps=12.0,
        bc_uncertainty_pct=0.03,
        wind_uncertainty_mps=1.0,
        iterations=200,
    )
    assert prof.mv_sd_fps == 12.0
    assert prof.bc_uncertainty_pct == 0.03
    assert prof.wind_uncertainty_mps == 1.0


# ---------------------------------------------------------------------------
# Determinism with seed
# ---------------------------------------------------------------------------


def test_monte_carlo_deterministic_with_seed():
    r1 = run_monte_carlo_at_distance(_profile(), _atm(), 500.0, iterations=200, seed=99)
    r2 = run_monte_carlo_at_distance(_profile(), _atm(), 500.0, iterations=200, seed=99)
    assert abs(r1.cep50_cm - r2.cep50_cm) < 0.01
    assert abs(r1.vertical_sd_cm - r2.vertical_sd_cm) < 0.01


def test_monte_carlo_different_seeds_differ():
    r1 = run_monte_carlo_at_distance(_profile(), _atm(), 500.0, iterations=500, seed=1)
    r2 = run_monte_carlo_at_distance(_profile(), _atm(), 500.0, iterations=500, seed=99)
    # Not necessarily different but extremely unlikely to match exactly
    assert not (
        abs(r1.cep50_cm - r2.cep50_cm) < 0.001
        and abs(r1.cep90_cm - r2.cep90_cm) < 0.001
    )
