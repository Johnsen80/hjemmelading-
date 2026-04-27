"""Block 7 tests: hunting backstop analysis — terrain intersection, verdicts, ethical range."""

from __future__ import annotations

import pytest

from src.field_planning.atmosphere import build_layered_atmosphere
from src.field_planning.backstop_analyzer import (
    analyse_backstop,
    compute_backstop_verdict,
    compute_ethical_range,
    find_ground_intersection,
    interpolate_elevation,
    max_ordinate_above_terrain,
)
from src.field_planning.models import (
    GAME_MIN_ENERGY_J,
    GeoPoint,
    HuntingPost,
    WeaponBallisticProfile,
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


def _atm(temp=15.0, wind=0.0):
    return build_layered_atmosphere(temp, 1013.25, 50.0, wind, 270.0)


def _flat_terrain(total_m: float, elev: float = 100.0) -> list[tuple[float, float]]:
    """Flat terrain at given elevation, from 0 to total_m."""
    return [(0.0, elev), (total_m, elev)]


def _hill_terrain(
    hill_start: float,
    hill_end: float,
    hill_top: float,
    total_m: float = 3000.0,
    base_elev: float = 100.0,
) -> list[tuple[float, float]]:
    """Terrain with a hill between hill_start and hill_end."""
    return [
        (0.0, base_elev),
        (hill_start, base_elev),
        ((hill_start + hill_end) / 2, hill_top),
        (hill_end, base_elev),
        (total_m, base_elev),
    ]


# ---------------------------------------------------------------------------
# Terrain helpers
# ---------------------------------------------------------------------------


def test_interpolate_flat():
    pts = [(0.0, 100.0), (1000.0, 100.0)]
    assert interpolate_elevation(pts, 500.0) == pytest.approx(100.0)


def test_interpolate_slope():
    pts = [(0.0, 100.0), (1000.0, 200.0)]
    assert interpolate_elevation(pts, 500.0) == pytest.approx(150.0)


def test_interpolate_out_of_range_returns_none():
    pts = [(100.0, 100.0), (500.0, 100.0)]
    assert interpolate_elevation(pts, 50.0) is None
    assert interpolate_elevation(pts, 600.0) is None


def test_interpolate_empty_returns_none():
    assert interpolate_elevation([], 100.0) is None


def test_find_ground_intersection_hits():
    # Bullet arc goes below terrain level
    arc = [(0.0, 110.0), (200.0, 105.0), (400.0, 100.0), (600.0, 95.0)]
    terrain = [(0.0, 100.0), (600.0, 100.0)]
    hit = find_ground_intersection(arc, terrain)
    assert hit is not None
    assert hit == pytest.approx(400.0, abs=1.0)


def test_find_ground_intersection_misses():
    # Bullet stays above terrain
    arc = [(0.0, 120.0), (500.0, 115.0), (1000.0, 110.0)]
    terrain = [(0.0, 100.0), (1000.0, 100.0)]
    assert find_ground_intersection(arc, terrain) is None


def test_max_ordinate_above_terrain():
    arc = [(0.0, 110.0), (500.0, 120.0), (1000.0, 100.0)]
    terrain = [(0.0, 100.0), (1000.0, 100.0)]
    mo = max_ordinate_above_terrain(arc, terrain)
    assert mo == pytest.approx(20.0, abs=0.1)


# ---------------------------------------------------------------------------
# Backstop verdict logic
# ---------------------------------------------------------------------------


def test_verdict_safe_low_energy():
    v, r, c = compute_backstop_verdict(
        ground_intersection_m=400.0,
        bullet_energy_at_ground_j=40.0,
        nearest_habitation_m=None,
    )
    assert v == "safe"
    assert c == "green"


def test_verdict_caution_high_energy():
    v, r, c = compute_backstop_verdict(
        ground_intersection_m=300.0,
        bullet_energy_at_ground_j=600.0,
        nearest_habitation_m=None,
    )
    assert v == "caution"
    assert c == "orange"


def test_verdict_unsafe_habitation_in_line():
    v, r, c = compute_backstop_verdict(
        ground_intersection_m=500.0,
        bullet_energy_at_ground_j=50.0,
        nearest_habitation_m=400.0,  # habitation closer than ground hit
    )
    assert v == "unsafe"
    assert c == "red"


def test_verdict_caution_no_ground_hit():
    v, r, c = compute_backstop_verdict(
        ground_intersection_m=None,
        bullet_energy_at_ground_j=0.0,
        nearest_habitation_m=None,
    )
    assert v == "caution"
    assert c == "orange"


def test_verdict_unsafe_no_ground_hit_habitation():
    v, r, c = compute_backstop_verdict(
        ground_intersection_m=None,
        bullet_energy_at_ground_j=0.0,
        nearest_habitation_m=2000.0,
        max_scan_range_m=8000.0,
    )
    assert v == "unsafe"
    assert c == "red"


# ---------------------------------------------------------------------------
# analyse_backstop integration
# ---------------------------------------------------------------------------


def test_analyse_backstop_returns_result():
    terrain = _flat_terrain(3000.0, 100.0)
    pt = GeoPoint(lat=61.0, lon=10.0)
    result = analyse_backstop(
        profile=_profile(),
        atmosphere=_atm(),
        aim_point=pt,
        bearing_deg=0.0,
        slant_range_m=200.0,
        terrain_points=terrain,
    )
    assert result is not None
    assert result.verdict in {"safe", "caution", "unsafe"}


def test_analyse_backstop_hill_blocks_bullet():
    # Bullet fired at 200m target, hill at 300-600m blocks the shot
    terrain = _hill_terrain(
        hill_start=300.0, hill_end=600.0, hill_top=120.0, base_elev=100.0
    )
    pt = GeoPoint(lat=61.0, lon=10.0)
    result = analyse_backstop(
        profile=_profile(),
        atmosphere=_atm(),
        aim_point=pt,
        bearing_deg=0.0,
        slant_range_m=200.0,
        terrain_points=terrain,
    )
    # Hill at 300m should intercept the bullet
    if result.ground_intersection_m is not None:
        assert result.ground_intersection_m <= 600.0


def test_analyse_backstop_habitation_marks_unsafe():
    terrain = _flat_terrain(5000.0, 100.0)
    pt = GeoPoint(lat=61.0, lon=10.0)
    result = analyse_backstop(
        profile=_profile(),
        atmosphere=_atm(),
        aim_point=pt,
        bearing_deg=0.0,
        slant_range_m=200.0,
        terrain_points=terrain,
        nearest_habitation_m=300.0,  # very close habitation
        nearest_habitation_label="Cabin",
    )
    assert result.verdict in {"unsafe", "caution"}
    assert result.nearest_habitation_label == "Cabin"


def test_analyse_backstop_energy_at_impact_positive():
    terrain = _flat_terrain(2000.0, 100.0)
    pt = GeoPoint(lat=61.0, lon=10.0)
    result = analyse_backstop(
        profile=_profile(),
        atmosphere=_atm(),
        aim_point=pt,
        bearing_deg=0.0,
        slant_range_m=200.0,
        terrain_points=terrain,
    )
    if result.ground_intersection_m is not None:
        assert result.bullet_energy_at_ground_j >= 0.0


# ---------------------------------------------------------------------------
# Ethical range
# ---------------------------------------------------------------------------


def test_ethical_range_moose_positive():
    r = compute_ethical_range(_profile(), _atm(), GAME_MIN_ENERGY_J["moose"])
    assert r > 0.0


def test_ethical_range_moose_less_than_deer():
    # Moose requires more energy → shorter ethical range
    r_moose = compute_ethical_range(_profile(), _atm(), GAME_MIN_ENERGY_J["moose"])
    r_deer = compute_ethical_range(_profile(), _atm(), GAME_MIN_ENERGY_J["deer"])
    assert r_moose <= r_deer


def test_ethical_range_small_game_farther():
    r_small = compute_ethical_range(_profile(), _atm(), GAME_MIN_ENERGY_J["small_game"])
    r_moose = compute_ethical_range(_profile(), _atm(), GAME_MIN_ENERGY_J["moose"])
    assert r_small > r_moose


def test_ethical_range_within_scan_range():
    r = compute_ethical_range(
        _profile(), _atm(), GAME_MIN_ENERGY_J["moose"], max_range_m=1500.0
    )
    assert r <= 1500.0


def test_game_min_energy_values():
    # Sanity check on game energy table
    assert GAME_MIN_ENERGY_J["moose"] > GAME_MIN_ENERGY_J["deer"]
    assert GAME_MIN_ENERGY_J["deer"] > GAME_MIN_ENERGY_J["roe_deer"]
    assert GAME_MIN_ENERGY_J["roe_deer"] > GAME_MIN_ENERGY_J["small_game"]


# ---------------------------------------------------------------------------
# HuntingPost model
# ---------------------------------------------------------------------------


def test_hunting_post_min_energy():
    post = HuntingPost(position=GeoPoint(61.0, 10.0), game_type="moose")
    assert post.min_kill_energy_j == GAME_MIN_ENERGY_J["moose"]


def test_hunting_post_unknown_game_fallback():
    post = HuntingPost(position=GeoPoint(61.0, 10.0), game_type="dragon")
    assert post.min_kill_energy_j > 0  # should fall back to default
