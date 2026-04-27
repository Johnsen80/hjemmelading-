"""Block 1 tests: field planning data models and ballistics profile bridge.

Verifies:
- All model dataclasses instantiate and behave correctly
- WeaponBallisticProfile priority chain for BC and MV
- MV temperature curve interpolation
- bridge handles missing/partial DB data gracefully
"""

from __future__ import annotations

from unittest.mock import MagicMock

from src.field_planning.models import (
    AtmosphereLayer,
    GeoPoint,
    HuntingPost,
    LayeredAtmosphere,
    WeaponBallisticProfile,
)
from src.utils.ballistics_profile_bridge import (
    _resolve_bc,
    _resolve_mv,
    _safe_float,
    build_weapon_ballistic_profile,
)

# ---------------------------------------------------------------------------
# LayeredAtmosphere
# ---------------------------------------------------------------------------


def _make_layer(alt=0.0, temp=8.0, press=1012.0, wind=2.0) -> AtmosphereLayer:
    return AtmosphereLayer(
        altitude_m=alt,
        temperature_c=temp,
        pressure_hpa=press,
        humidity_pct=60.0,
        wind_speed_mps=wind,
        wind_dir_deg=270.0,
        density_ratio=1.0,
        density_altitude_m=0.0,
    )


def test_atmosphere_surface_layer_is_first():
    atm = LayeredAtmosphere(layers=[_make_layer(0.0), _make_layer(500.0, temp=2.0)])
    assert atm.surface_layer.temperature_c == 8.0


def test_atmosphere_layer_at_altitude_returns_correct_layer():
    atm = LayeredAtmosphere(layers=[_make_layer(0.0), _make_layer(500.0, temp=2.0)])
    assert atm.layer_at_altitude(600.0).temperature_c == 2.0
    assert atm.layer_at_altitude(400.0).temperature_c == 8.0
    assert atm.layer_at_altitude(0.0).temperature_c == 8.0


def test_atmosphere_single_layer_always_returned():
    atm = LayeredAtmosphere(layers=[_make_layer(0.0, temp=15.0)])
    assert atm.layer_at_altitude(9999.0).temperature_c == 15.0


# ---------------------------------------------------------------------------
# WeaponBallisticProfile MV temperature curve
# ---------------------------------------------------------------------------


def _make_profile(**kwargs) -> WeaponBallisticProfile:
    defaults = dict(
        rifle_id=1,
        rifle_name="Test",
        caliber="308 Win",
        barrel_configuration_id=None,
        twist_rate_in=10.0,
        twist_direction="RIGHT",
        sight_height_mm=38.0,
        zero_distance_m=100.0,
        learned_mv_fps=2700.0,
        learned_mv_sd_fps=10.0,
        learned_bc=0.223,
        learned_bc_type="G7",
        bc_source="ammo_profile",
        mv_source="chrono_sessions",
    )
    defaults.update(kwargs)
    return WeaponBallisticProfile(**defaults)


def test_mv_at_temperature_interpolates():
    p = _make_profile(
        mv_temperature_curve=[(-10.0, 2650.0), (0.0, 2670.0), (20.0, 2710.0)]
    )
    assert p.mv_at_temperature(10.0) == 2690.0


def test_mv_at_temperature_clamps_low():
    p = _make_profile(mv_temperature_curve=[(-10.0, 2650.0), (20.0, 2720.0)])
    assert p.mv_at_temperature(-30.0) == 2650.0


def test_mv_at_temperature_clamps_high():
    p = _make_profile(mv_temperature_curve=[(-10.0, 2650.0), (20.0, 2720.0)])
    assert p.mv_at_temperature(40.0) == 2720.0


def test_mv_at_temperature_falls_back_to_learned_when_no_curve():
    p = _make_profile(learned_mv_fps=2700.0, mv_temperature_curve=[])
    assert p.mv_at_temperature(15.0) == 2700.0


def test_mv_at_temperature_falls_back_to_learned_when_single_point():
    p = _make_profile(learned_mv_fps=2700.0, mv_temperature_curve=[(10.0, 2700.0)])
    assert p.mv_at_temperature(15.0) == 2700.0


# ---------------------------------------------------------------------------
# HuntingPost min energy
# ---------------------------------------------------------------------------


def test_hunting_post_moose_energy():
    post = HuntingPost(position=GeoPoint(61.0, 10.0), game_type="moose")
    assert post.min_kill_energy_j == 2500.0


def test_hunting_post_deer_energy():
    post = HuntingPost(position=GeoPoint(61.0, 10.0), game_type="deer")
    assert post.min_kill_energy_j == 1500.0


def test_hunting_post_unknown_game_defaults_to_1500():
    post = HuntingPost(position=GeoPoint(61.0, 10.0), game_type="dragon")
    assert post.min_kill_energy_j == 1500.0


# ---------------------------------------------------------------------------
# _resolve_bc priority chain
# ---------------------------------------------------------------------------


def test_bc_prefers_calibrated_in_learning():
    learning = {"calibrated_bc": {"bc_g7": 0.280}}
    ammo = {"bc_g7": 0.220}
    bc, typ, src = _resolve_bc(ammo, {}, learning)
    assert bc == 0.280
    assert typ == "G7"
    assert src == "measured_drops"


def test_bc_falls_to_ammo_profile_g7_when_no_learning():
    bc, typ, src = _resolve_bc({"bc_g7": 0.225}, {}, {})
    assert bc == 0.225
    assert src == "ammo_profile"


def test_bc_falls_to_bullet_g7():
    bc, typ, src = _resolve_bc({}, {"bc_g7": 0.210}, {})
    assert bc == 0.210
    assert src == "bullet_library"


def test_bc_converts_g1_to_g7_approx():
    bc, typ, src = _resolve_bc({"bc_g1": 0.470}, {}, {})
    assert abs(bc - 0.470 * 0.47) < 1e-9
    assert typ == "G7"
    assert "g1_converted" in src


def test_bc_defaults_when_all_missing():
    bc, typ, src = _resolve_bc({}, {}, {})
    assert bc == 0.200
    assert typ == "G7"
    assert src == "default"


def test_bc_ignores_invalid_calibrated_value():
    learning = {"calibrated_bc": {"bc_g7": 0.001}}  # too small → skip
    bc, typ, src = _resolve_bc({"bc_g7": 0.225}, {}, learning)
    assert bc == 0.225
    assert src == "ammo_profile"


# ---------------------------------------------------------------------------
# _resolve_mv priority chain
# ---------------------------------------------------------------------------


def test_mv_computes_weighted_mean_from_sessions():
    sessions = [
        {
            "avg_velocity_fps": 2700.0,
            "sd_fps": 10.0,
            "shot_count": 10,
            "temperature_f": 59.0,
        },
        {
            "avg_velocity_fps": 2720.0,
            "sd_fps": 12.0,
            "shot_count": 10,
            "temperature_f": 77.0,
        },
    ]
    mv, sd, src, curve = _resolve_mv(sessions, {}, {})
    assert abs(mv - 2710.0) < 0.1
    assert src == "chrono_sessions"


def test_mv_builds_temperature_curve_from_sessions():
    sessions = [
        {
            "avg_velocity_fps": 2650.0,
            "sd_fps": 10.0,
            "shot_count": 5,
            "temperature_f": 14.0,
        },  # -10°C
        {
            "avg_velocity_fps": 2710.0,
            "sd_fps": 10.0,
            "shot_count": 5,
            "temperature_f": 68.0,
        },  # 20°C
    ]
    mv, sd, src, curve = _resolve_mv(sessions, {}, {})
    assert len(curve) == 2
    temps = [t for t, _ in curve]
    assert temps == sorted(temps)


def test_mv_falls_back_to_ammo_profile():
    mv, sd, src, _ = _resolve_mv([], {"velocity_fps": 2650.0}, {})
    assert mv == 2650.0
    assert src == "ammo_profile"


def test_mv_uses_default_when_all_missing():
    mv, sd, src, _ = _resolve_mv([], {}, {})
    assert src == "default"
    assert mv > 0


def test_mv_skips_invalid_zero_velocity_sessions():
    sessions = [
        {
            "avg_velocity_fps": 0.0,
            "sd_fps": 0.0,
            "shot_count": 5,
            "temperature_f": 59.0,
        },
        {
            "avg_velocity_fps": 2700.0,
            "sd_fps": 10.0,
            "shot_count": 5,
            "temperature_f": 59.0,
        },
    ]
    mv, sd, src, _ = _resolve_mv(sessions, {}, {})
    assert mv == 2700.0


# ---------------------------------------------------------------------------
# build_weapon_ballistic_profile — DB integration (mocked)
# ---------------------------------------------------------------------------


def _make_db(
    rifle=None,
    ammo=None,
    bullet=None,
    optic=None,
    chrono=None,
    learning_json=None,
) -> MagicMock:
    db = MagicMock()

    def eq(query, params=()):
        q = query.strip().lower()
        if "from rifles" in q:
            return [rifle] if rifle else []
        if "from ammo_profiles" in q:
            return [ammo] if ammo else []
        if "from bullets" in q:
            return [bullet] if bullet else []
        if "from optics" in q:
            return [optic] if optic else []
        if "from chronograph_sessions" in q:
            return chrono or []
        if "from load_development_sessions" in q:
            return [{"learning_state_json": learning_json or "{}"}]
        return []

    db.execute_query.side_effect = eq
    return db


def test_build_profile_uses_chrono_mv():
    db = _make_db(
        rifle={
            "id": 1,
            "name": "Tikka T3x",
            "caliber": "308 Win",
            "twist_rate_inches": 10.0,
            "twist_direction": "RIGHT",
        },
        ammo={"id": 10, "bc_g7": 0.225, "bullet_id": 20},
        bullet={
            "id": 20,
            "diameter_mm": 7.82,
            "length_mm": 32.0,
            "weight_grains": 175.0,
            "bc_g7": 0.225,
        },
        chrono=[
            {
                "avg_velocity_fps": 2650.0,
                "sd_fps": 9.0,
                "shot_count": 10,
                "temperature_f": 50.0,
            }
        ],
    )
    profile = build_weapon_ballistic_profile(db, rifle_id=1, ammo_profile_id=10)
    assert profile.learned_mv_fps == 2650.0
    assert profile.mv_source == "chrono_sessions"
    assert profile.learned_bc == 0.225
    assert profile.bc_source == "ammo_profile"


def test_build_profile_uses_calibrated_bc_from_learning():
    import json

    learning = json.dumps({"calibrated_bc": {"bc_g7": 0.272}})
    db = _make_db(
        rifle={
            "id": 1,
            "name": "Test",
            "caliber": "6.5 CM",
            "twist_rate_inches": 8.0,
            "twist_direction": "RIGHT",
        },
        ammo={"id": 5, "bc_g7": 0.220, "bullet_id": None},
        learning_json=learning,
    )
    profile = build_weapon_ballistic_profile(
        db, rifle_id=1, ammo_profile_id=5, load_session_id=99
    )
    assert profile.learned_bc == 0.272
    assert profile.bc_source == "measured_drops"


def test_build_profile_graceful_when_rifle_missing():
    db = _make_db()
    profile = build_weapon_ballistic_profile(db, rifle_id=999)
    assert profile.rifle_id == 999
    assert profile.learned_bc == 0.200  # default
    assert profile.bc_source == "default"


def test_build_profile_twist_defaults_when_missing():
    db = _make_db(rifle={"id": 1, "name": "Test", "caliber": "308 Win"})
    profile = build_weapon_ballistic_profile(db, rifle_id=1)
    assert profile.twist_rate_in == 10.0
    assert profile.twist_direction == "RIGHT"


# ---------------------------------------------------------------------------
# _safe_float edge cases
# ---------------------------------------------------------------------------


def test_safe_float_handles_none():
    assert _safe_float(None) is None


def test_safe_float_handles_string():
    assert _safe_float("3.14") == 3.14


def test_safe_float_handles_nan():
    assert _safe_float(float("nan")) is None


def test_safe_float_handles_inf():
    assert _safe_float(float("inf")) is None
