"""Block 6 tests: range session calculator — slant correction, click tables."""

from __future__ import annotations

import math

import pytest

from src.field_planning.atmosphere import build_layered_atmosphere
from src.field_planning.models import RangeSession, RangeTarget, WeaponBallisticProfile
from src.field_planning.range_calculator import (
    build_range_click_table,
    compute_target_solution,
    inclination_correction_factor,
    slant_range_to_horizontal,
    wind_crosswind_factor,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _profile(**kw) -> WeaponBallisticProfile:
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
    defaults.update(kw)
    return WeaponBallisticProfile(**defaults)


def _atm(temp=15.0, wind=2.0, wind_dir=270.0):
    return build_layered_atmosphere(temp, 1013.25, 50.0, wind, wind_dir)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def test_slant_flat_equals_slant():
    assert slant_range_to_horizontal(500.0, 0.0) == pytest.approx(500.0, abs=0.01)


def test_slant_uphill_reduces_horizontal():
    h = slant_range_to_horizontal(500.0, 30.0)
    assert h < 500.0
    assert h == pytest.approx(500.0 * math.cos(math.radians(30.0)), abs=0.01)


def test_slant_downhill_same_as_uphill():
    # cos is symmetric
    assert slant_range_to_horizontal(300.0, 20.0) == pytest.approx(
        slant_range_to_horizontal(300.0, -20.0), abs=0.01
    )


def test_inclination_factor_zero():
    assert inclination_correction_factor(0.0) == pytest.approx(1.0, abs=1e-6)


def test_inclination_factor_30deg():
    f = inclination_correction_factor(30.0)
    assert f == pytest.approx(math.cos(math.radians(30.0)), abs=1e-6)
    assert 0.8 < f < 0.9


def test_inclination_factor_45deg():
    assert inclination_correction_factor(45.0) == pytest.approx(
        math.sqrt(2) / 2, abs=1e-5
    )


def test_wind_crosswind_pure_crosswind():
    # Wind from N (0°), shot to E (90°) → pure crosswind
    assert wind_crosswind_factor(0.0, 90.0) == pytest.approx(1.0, abs=1e-6)


def test_wind_crosswind_headwind():
    # Wind from N (0°), shot to N (0°) → headwind → 0 crosswind
    assert wind_crosswind_factor(0.0, 0.0) == pytest.approx(0.0, abs=1e-6)


def test_wind_crosswind_tailwind():
    # Wind from N (0°), shot to S (180°) → tailwind → 0 crosswind
    assert wind_crosswind_factor(0.0, 180.0) == pytest.approx(0.0, abs=1e-6)


def test_wind_crosswind_partial():
    # Wind from W (270°), shot to N (0°) → 90° difference → full crosswind
    assert wind_crosswind_factor(270.0, 0.0) == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# RangeTarget model
# ---------------------------------------------------------------------------


def test_range_target_horizontal_range_flat():
    t = RangeTarget("T1", slant_range_m=400.0, inclination_deg=0.0)
    assert t.horizontal_range_m == pytest.approx(400.0, abs=0.01)


def test_range_target_horizontal_range_inclined():
    t = RangeTarget("T2", slant_range_m=400.0, inclination_deg=30.0)
    assert t.horizontal_range_m < 400.0


# ---------------------------------------------------------------------------
# compute_target_solution: basic correctness
# ---------------------------------------------------------------------------


def test_target_solution_returns_result():
    sol = compute_target_solution(_profile(), _atm(), slant_range_m=300.0)
    assert sol is not None
    assert sol.velocity_mps > 0


def test_target_solution_elevation_clicks_positive():
    # Shot beyond zero → positive (up) elevation correction
    sol = compute_target_solution(_profile(), _atm(), slant_range_m=500.0)
    assert sol.correction.elevation_moa > 0


def test_target_solution_at_zero_near_zero():
    sol = compute_target_solution(_profile(), _atm(), slant_range_m=100.0)
    assert abs(sol.correction.elevation_moa) < 1.0


def test_target_solution_phase_supersonic_close():
    sol = compute_target_solution(_profile(), _atm(), slant_range_m=200.0)
    assert sol.phase == "supersonic"


def test_target_solution_has_wind_reference():
    sol = compute_target_solution(_profile(), _atm(wind=0.0), slant_range_m=500.0)
    assert sol.wind_10mps_windage_moa > 0


def test_target_solution_energy_decreases_with_distance():
    sol_close = compute_target_solution(_profile(), _atm(), slant_range_m=200.0)
    sol_far = compute_target_solution(_profile(), _atm(), slant_range_m=600.0)
    assert sol_far.energy_joules < sol_close.energy_joules


# ---------------------------------------------------------------------------
# Slant correction
# ---------------------------------------------------------------------------


def test_uphill_needs_less_elevation_than_flat():
    flat = compute_target_solution(
        _profile(), _atm(), slant_range_m=500.0, inclination_deg=0.0
    )
    uphill = compute_target_solution(
        _profile(), _atm(), slant_range_m=500.0, inclination_deg=25.0
    )
    # Cosine correction → uphill needs less elevation MOA
    assert uphill.correction.elevation_moa < flat.correction.elevation_moa


def test_downhill_needs_less_elevation_than_flat():
    flat = compute_target_solution(
        _profile(), _atm(), slant_range_m=500.0, inclination_deg=0.0
    )
    downhill = compute_target_solution(
        _profile(), _atm(), slant_range_m=500.0, inclination_deg=-25.0
    )
    assert downhill.correction.elevation_moa < flat.correction.elevation_moa


def test_correction_factor_matches_geometry():
    flat = compute_target_solution(
        _profile(), _atm(), slant_range_m=500.0, inclination_deg=0.0
    )
    uphill = compute_target_solution(
        _profile(), _atm(), slant_range_m=500.0, inclination_deg=20.0
    )
    expected_ratio = inclination_correction_factor(20.0)
    actual_ratio = uphill.correction.elevation_moa / flat.correction.elevation_moa
    assert actual_ratio == pytest.approx(expected_ratio, abs=0.01)


def test_slant_correction_factor_stored():
    sol = compute_target_solution(
        _profile(), _atm(), slant_range_m=400.0, inclination_deg=30.0
    )
    assert sol.inclination_correction_factor == pytest.approx(
        math.cos(math.radians(30.0)), abs=1e-5
    )


# ---------------------------------------------------------------------------
# build_range_click_table
# ---------------------------------------------------------------------------


def test_range_click_table_returns_one_per_target():
    targets = [
        RangeTarget("T1", 200.0),
        RangeTarget("T2", 400.0),
        RangeTarget("T3", 600.0),
    ]
    session = RangeSession(profile=_profile(), atmosphere=_atm(), targets=targets)
    solutions = build_range_click_table(session)
    assert len(solutions) == 3


def test_range_click_table_order_preserved():
    targets = [
        RangeTarget("near", 200.0),
        RangeTarget("far", 800.0),
        RangeTarget("mid", 500.0),
    ]
    session = RangeSession(profile=_profile(), atmosphere=_atm(), targets=targets)
    solutions = build_range_click_table(session)
    assert solutions[0].target.label == "near"
    assert solutions[1].target.label == "far"
    assert solutions[2].target.label == "mid"


def test_range_click_table_elevation_increases_with_distance():
    targets = [RangeTarget(f"T{d}", float(d)) for d in [200, 400, 600, 800]]
    session = RangeSession(profile=_profile(), atmosphere=_atm(), targets=targets)
    solutions = build_range_click_table(session)
    moas = [s.correction.elevation_moa for s in solutions]
    for i in range(1, len(moas)):
        assert moas[i] > moas[i - 1], f"MOA at index {i} not > {i-1}"


def test_range_click_table_mrad_scope():
    targets = [RangeTarget("T1", 500.0)]
    session = RangeSession(
        profile=_profile(),
        atmosphere=_atm(),
        targets=targets,
        scope_unit="mrad",
        clicks_per_moa=10.0,
    )
    solutions = build_range_click_table(session)
    assert solutions[0].correction.unit == "mrad"


def test_range_click_table_different_bearings_different_wind():
    # Two targets at same distance but 90° different bearings in a crosswind
    atm = _atm(wind=5.0, wind_dir=90.0)  # wind from E
    targets = [
        RangeTarget("north", 500.0, bearing_deg=0.0),  # wind from side
        RangeTarget("east", 500.0, bearing_deg=90.0),  # wind from behind (headwind)
    ]
    session = RangeSession(profile=_profile(), atmosphere=atm, targets=targets)
    solutions = build_range_click_table(session)
    # Shooting east (into headwind): less windage than shooting north (crosswind)
    assert abs(solutions[0].correction.windage_moa) != pytest.approx(
        abs(solutions[1].correction.windage_moa), abs=0.1
    )
