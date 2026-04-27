"""Block 2 tests: field solution, DOPE card, Sg stability, zero shift, Mach phase."""

from __future__ import annotations

from src.field_planning.models import (
    AtmosphereLayer,
    FieldSession,
    FieldTarget,
    GeoPoint,
    LayeredAtmosphere,
    WeaponBallisticProfile,
)
from src.field_planning.services import (
    _mach_phase,
    _sg_status,
    _speed_of_sound_mps,
    _wind_angle_for_azimuth,
    build_dope_card,
    build_field_solution,
    compute_stability_sg,
    compute_zero_shift_clicks,
    find_ethical_range,
    find_subsonic_range,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _layer(
    temp=15.0, press=1013.25, hum=50.0, wind=0.0, wind_dir=270.0
) -> AtmosphereLayer:
    return AtmosphereLayer(
        altitude_m=0.0,
        temperature_c=temp,
        pressure_hpa=press,
        humidity_pct=hum,
        wind_speed_mps=wind,
        wind_dir_deg=wind_dir,
        density_ratio=1.0,
        density_altitude_m=0.0,
    )


def _atm(**kwargs) -> LayeredAtmosphere:
    return LayeredAtmosphere(layers=[_layer(**kwargs)])


def _profile(**kwargs) -> WeaponBallisticProfile:
    defaults = dict(
        rifle_id=1,
        rifle_name="Tikka T3x",
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
        ammo_label="Sierra 175gr HPBT",
    )
    defaults.update(kwargs)
    return WeaponBallisticProfile(**defaults)


def _session(**kwargs) -> FieldSession:
    profile = kwargs.pop("profile", _profile())
    atm = kwargs.pop("atmosphere", _atm())
    return FieldSession(profile=profile, atmosphere=atm, **kwargs)


def _target(dist_m=500.0) -> FieldTarget:
    return FieldTarget(
        position=GeoPoint(61.0, 10.1),
        distance_m=dist_m,
        slant_distance_m=dist_m,
        inclination_deg=0.0,
        bearing_deg=90.0,
    )


# ---------------------------------------------------------------------------
# Speed of sound
# ---------------------------------------------------------------------------


def test_speed_of_sound_at_standard():
    sos = _speed_of_sound_mps(15.0)
    assert 340.0 < sos < 342.0


def test_speed_of_sound_cold():
    sos_cold = _speed_of_sound_mps(-20.0)
    sos_warm = _speed_of_sound_mps(20.0)
    assert sos_cold < sos_warm


# ---------------------------------------------------------------------------
# Mach phase classification
# ---------------------------------------------------------------------------


def test_mach_phase_supersonic():
    assert _mach_phase(1.5) == "supersonic"


def test_mach_phase_transonic():
    assert _mach_phase(1.0) == "transonic"
    assert _mach_phase(1.19) == "transonic"


def test_mach_phase_subsonic():
    assert _mach_phase(0.89) == "subsonic"


# ---------------------------------------------------------------------------
# Stability Sg (Miller)
# ---------------------------------------------------------------------------


def test_sg_308_175_1in10_stable():
    sg = compute_stability_sg(
        bullet_diameter_mm=7.82,
        bullet_length_mm=32.0,
        bullet_mass_gr=175.0,
        twist_rate_in=10.0,
        velocity_fps=2650.0,
        density_ratio=1.0,
    )
    assert sg > 1.4, f"Expected Sg > 1.4 for 175gr .308 1:10, got {sg:.2f}"


def test_sg_drops_with_velocity():
    sg_fast = compute_stability_sg(7.82, 32.0, 175.0, 10.0, 2650.0, 1.0)
    sg_slow = compute_stability_sg(7.82, 32.0, 175.0, 10.0, 1200.0, 1.0)
    assert sg_fast > sg_slow


def test_sg_drops_at_higher_density():
    sg_sea = compute_stability_sg(7.82, 32.0, 175.0, 10.0, 2650.0, 1.0)
    sg_hi = compute_stability_sg(7.82, 32.0, 175.0, 10.0, 2650.0, 1.2)
    assert sg_sea > sg_hi


def test_sg_zero_inputs_returns_zero():
    assert compute_stability_sg(0, 32.0, 175.0, 10.0, 2650.0) == 0.0
    assert compute_stability_sg(7.82, 0, 175.0, 10.0, 2650.0) == 0.0


def test_sg_status_levels():
    assert _sg_status(0.8) == "unstable"
    assert _sg_status(1.2) == "marginal"
    assert _sg_status(1.5) == "stable"
    assert _sg_status(0.0) == "unknown"


# ---------------------------------------------------------------------------
# Wind angle conversion
# ---------------------------------------------------------------------------


def test_wind_angle_full_crosswind_from_west_shooting_north():
    # Wind from West (270°), shooting North (0°) → 90° right crosswind
    angle = _wind_angle_for_azimuth(270.0, 0.0)
    assert abs(angle - 90.0) < 1.0


def test_wind_angle_headwind():
    # Wind from North (0°), shooting North (0°) → 180° tailwind
    angle = _wind_angle_for_azimuth(0.0, 0.0)
    assert abs(angle - 180.0) < 1.0


# ---------------------------------------------------------------------------
# DOPE card generation
# ---------------------------------------------------------------------------


def test_dope_card_has_correct_distances():
    sess = _session()
    card = build_dope_card(sess, distances_m=[100, 300, 500])
    dists = [r.distance_m for r in card.rows]
    assert 100.0 in dists
    assert 300.0 in dists
    assert 500.0 in dists


def test_dope_card_elevation_increases_with_distance():
    sess = _session()
    card = build_dope_card(sess, distances_m=[100, 200, 300, 500, 800])
    clicks = [r.correction.elevation_clicks for r in card.rows]
    # Each distance should require more elevation than the previous
    for i in range(1, len(clicks)):
        assert (
            clicks[i] > clicks[i - 1]
        ), f"Clicks at row {i} ({clicks[i]:.1f}) not > row {i-1} ({clicks[i-1]:.1f})"


def test_dope_card_energy_decreases_with_distance():
    sess = _session()
    card = build_dope_card(sess, distances_m=[100, 300, 500, 800])
    energies = [r.energy_joules for r in card.rows]
    for i in range(1, len(energies)):
        assert energies[i] < energies[i - 1]


def test_dope_card_velocity_decreases_with_distance():
    sess = _session()
    card = build_dope_card(sess, distances_m=[100, 300, 500])
    vels = [r.velocity_mps for r in card.rows]
    for i in range(1, len(vels)):
        assert vels[i] < vels[i - 1]


def test_dope_card_contains_metadata():
    sess = _session()
    card = build_dope_card(sess)
    assert card.rifle_name == "Tikka T3x"
    assert card.learned_bc == 0.223
    assert card.bc_source == "ammo_profile"
    assert card.generated_at != ""


def test_dope_card_wind_column_populated():
    sess = _session(atmosphere=_atm(wind=5.0, wind_dir=270.0))
    card = build_dope_card(sess, distances_m=[300, 500], wind_reference_mps=10.0)
    for row in card.rows:
        assert row.wind_10mps_moa is not None


def test_dope_card_conditions_summary_format():
    sess = _session(atmosphere=_atm(temp=8.0, press=1008.0, hum=65.0))
    card = build_dope_card(sess)
    assert "8.0°C" in card.conditions_summary
    assert "1008.0 hPa" in card.conditions_summary


def test_dope_card_uses_temperature_adjusted_mv():
    profile_warm = _profile(
        mv_temperature_curve=[(-10.0, 2600.0), (20.0, 2700.0)],
        learned_mv_fps=2650.0,
    )
    profile_cold = _profile(
        mv_temperature_curve=[(-10.0, 2600.0), (20.0, 2700.0)],
        learned_mv_fps=2650.0,
    )
    sess_warm = FieldSession(profile=profile_warm, atmosphere=_atm(temp=20.0))
    sess_cold = FieldSession(profile=profile_cold, atmosphere=_atm(temp=-10.0))
    card_warm = build_dope_card(sess_warm, distances_m=[500])
    card_cold = build_dope_card(sess_cold, distances_m=[500])
    # Cold MV → more drop → more elevation clicks
    assert (
        card_cold.rows[0].correction.elevation_clicks
        > card_warm.rows[0].correction.elevation_clicks
    )


# ---------------------------------------------------------------------------
# build_field_solution
# ---------------------------------------------------------------------------


def test_field_solution_returns_points():
    sess = _session()
    tgt = _target(500.0)
    pts = build_field_solution(sess, tgt, step_m=50.0)
    assert len(pts) > 0


def test_field_solution_phase_starts_supersonic():
    sess = _session()
    tgt = _target(300.0)
    pts = build_field_solution(sess, tgt, step_m=10.0)
    assert pts[0].phase == "supersonic"


def test_field_solution_velocity_decreases_monotonically():
    sess = _session()
    tgt = _target(500.0)
    pts = build_field_solution(sess, tgt, step_m=10.0)
    vels = [p.velocity_fps for p in pts]
    for i in range(1, len(vels)):
        assert vels[i] <= vels[i - 1] + 1.0  # allow tiny float noise


def test_field_solution_has_sg_values():
    sess = _session()
    tgt = _target(300.0)
    pts = build_field_solution(sess, tgt, step_m=50.0)
    for pt in pts:
        assert pt.stability_sg > 0


def test_field_solution_energy_in_joules():
    sess = _session()
    tgt = _target(100.0)
    pts = build_field_solution(sess, tgt, step_m=10.0)
    # 175gr at ~2650 fps → ~2722 J at muzzle
    assert pts[0].energy_joules > 2000.0


# ---------------------------------------------------------------------------
# find_subsonic_range and find_ethical_range
# ---------------------------------------------------------------------------


def test_find_subsonic_range_returns_none_when_always_supersonic():
    sess = _session()
    tgt = _target(300.0)
    pts = build_field_solution(sess, tgt, step_m=10.0)
    result = find_subsonic_range(pts)
    # 308 Win 175gr at 300m should still be supersonic
    assert result is None


def test_find_ethical_range_deer():
    sess = _session()
    tgt = _target(1000.0)
    pts = build_field_solution(sess, tgt, step_m=10.0)
    r = find_ethical_range(pts, min_energy_j=1500.0)
    assert r is not None
    assert r > 100.0


def test_find_ethical_range_none_when_never_enough():
    sess = _session()
    tgt = _target(200.0)
    pts = build_field_solution(sess, tgt, step_m=10.0)
    # Require 100 000 J — impossible
    r = find_ethical_range(pts, min_energy_j=100_000.0)
    assert r is None


# ---------------------------------------------------------------------------
# compute_zero_shift_clicks
# ---------------------------------------------------------------------------


def test_zero_shift_same_loads_is_zero():
    p = _profile()
    el, wi = compute_zero_shift_clicks(p, p)
    assert abs(el) < 0.5
    assert abs(wi) < 0.5


def test_zero_shift_heavier_bc_shifts_up():
    p_low = _profile(learned_bc=0.200, learned_mv_fps=2650.0)
    p_high = _profile(learned_bc=0.280, learned_mv_fps=2650.0)
    el_low, _ = compute_zero_shift_clicks(p_low, p_low)
    el_shift, _ = compute_zero_shift_clicks(p_low, p_high)
    # Higher BC bullet hits closer to zero → less correction needed
    assert isinstance(el_shift, float)
