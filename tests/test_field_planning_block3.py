"""Block 3 tests: BulletJourneyData — visualization data layer (no Qt required).

Verifies that from_trajectory() correctly:
- Builds phase regions
- Places markers (zero, transonic, subsonic, ethical)
- Computes summary lines
- Provides point_at() lookup
- Handles empty / single-point input gracefully
- Interpolates terrain
"""

from __future__ import annotations

from src.field_planning.journey_data import (
    PHASE_COLORS,
    BulletJourneyData,
    _build_markers,
    _build_phase_regions,
    _interpolate_terrain,
)
from src.field_planning.models import AtmosphereLayer, EnrichedTrajectoryPoint

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _layer() -> AtmosphereLayer:
    return AtmosphereLayer(
        altitude_m=0.0,
        temperature_c=15.0,
        pressure_hpa=1013.25,
        humidity_pct=50.0,
        wind_speed_mps=0.0,
        wind_dir_deg=0.0,
        density_ratio=1.0,
        density_altitude_m=0.0,
    )


def _pt(
    dist: float,
    vel_fps: float = 2600.0,
    mach: float = 2.3,
    phase: str = "supersonic",
    drop_cm: float = 0.0,
    windage_cm: float = 0.0,
    energy_j: float = 3000.0,
    sg: float = 1.6,
) -> EnrichedTrajectoryPoint:
    return EnrichedTrajectoryPoint(
        distance_m=dist,
        time_s=dist / 800.0,
        velocity_fps=vel_fps,
        velocity_mps=vel_fps * 0.3048,
        mach=mach,
        phase=phase,
        drop_cm=drop_cm,
        drop_moa=0.0,
        drop_mrad=0.0,
        windage_cm=windage_cm,
        windage_moa=0.0,
        windage_mrad=0.0,
        energy_ftlbs=energy_j / 1.356,
        energy_joules=energy_j,
        stability_sg=sg,
        stability_status="stable",
        bullet_altitude_m=0.0,
        height_above_ground_m=5.0,
        atmosphere_layer=_layer(),
        wind_drift_cm=windage_cm * 0.8,
        spin_drift_cm=windage_cm * 0.15,
        coriolis_cm=windage_cm * 0.05,
    )


def _make_points(n=10, max_dist=500.0) -> list[EnrichedTrajectoryPoint]:
    points = []
    for i in range(n):
        d = i * (max_dist / (n - 1)) if n > 1 else 0.0
        vel = 2650.0 - i * 30.0
        mach = vel * 0.3048 / 341.0
        phase = (
            "supersonic" if mach >= 1.2 else "transonic" if mach >= 0.9 else "subsonic"
        )
        points.append(
            _pt(
                d,
                vel_fps=vel,
                mach=mach,
                phase=phase,
                drop_cm=-i * 5.0,
                energy_j=3000.0 - i * 200.0,
            )
        )
    return points


# ---------------------------------------------------------------------------
# from_trajectory — basic construction
# ---------------------------------------------------------------------------


def test_from_trajectory_populates_all_series():
    pts = _make_points(10, 500.0)
    data = BulletJourneyData.from_trajectory(pts)
    assert len(data.distances_m) == 10
    assert len(data.drop_cm) == 10
    assert len(data.velocity_fps) == 10
    assert len(data.mach) == 10
    assert len(data.energy_joules) == 10
    assert len(data.stability_sg) == 10


def test_from_trajectory_empty_returns_empty():
    data = BulletJourneyData.from_trajectory([])
    assert data.distances_m == []
    assert data.phase_regions == []
    assert data.markers == []


def test_from_trajectory_single_point():
    pts = [_pt(100.0, mach=2.0, phase="supersonic")]
    data = BulletJourneyData.from_trajectory(pts)
    assert len(data.distances_m) == 1
    assert data.max_distance_m == 100.0


def test_from_trajectory_max_distance():
    pts = _make_points(5, 800.0)
    data = BulletJourneyData.from_trajectory(pts)
    assert data.max_distance_m == 800.0


def test_from_trajectory_min_energy_correct():
    pts = [
        _pt(100.0, energy_j=3000.0),
        _pt(500.0, energy_j=1500.0),
        _pt(800.0, energy_j=800.0),
    ]
    data = BulletJourneyData.from_trajectory(pts)
    assert data.min_energy_j == 800.0


# ---------------------------------------------------------------------------
# Phase regions
# ---------------------------------------------------------------------------


def test_phase_regions_single_phase():
    pts = [_pt(d, mach=2.0, phase="supersonic") for d in [0, 100, 200, 300]]
    regions = _build_phase_regions(pts)
    assert len(regions) == 1
    assert regions[0].label == "supersonic"
    assert regions[0].color == PHASE_COLORS["supersonic"]


def test_phase_regions_transition():
    pts = [
        _pt(0.0, mach=2.0, phase="supersonic"),
        _pt(100.0, mach=2.0, phase="supersonic"),
        _pt(200.0, mach=1.1, phase="transonic"),
        _pt(300.0, mach=0.8, phase="subsonic"),
    ]
    regions = _build_phase_regions(pts)
    labels = [r.label for r in regions]
    assert "supersonic" in labels
    assert "transonic" in labels
    assert "subsonic" in labels


def test_phase_regions_boundaries():
    pts = [
        _pt(0.0, phase="supersonic"),
        _pt(200.0, phase="supersonic"),
        _pt(300.0, phase="transonic"),
        _pt(500.0, phase="transonic"),
    ]
    regions = _build_phase_regions(pts)
    super_region = next(r for r in regions if r.label == "supersonic")
    assert super_region.x_end == 300.0


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------


def test_markers_zero_always_present():
    pts = [_pt(d, mach=2.0, phase="supersonic") for d in [0, 100, 200]]
    markers = _build_markers(pts, zero_distance_m=100.0, ethical_energy_j=None)
    assert any(m.label == "Zero" and m.distance_m == 100.0 for m in markers)


def test_markers_transonic_when_phase_change():
    pts = [
        _pt(0.0, phase="supersonic"),
        _pt(100.0, phase="supersonic"),
        _pt(200.0, phase="transonic"),
        _pt(300.0, phase="subsonic"),
    ]
    markers = _build_markers(pts, zero_distance_m=100.0, ethical_energy_j=None)
    labels = [m.label for m in markers]
    assert any("Transonic" in lbl for lbl in labels)
    assert any("Subsonic" in lbl for lbl in labels)


def test_markers_ethical_when_energy_provided():
    pts = [
        _pt(100.0, energy_j=3000.0),
        _pt(300.0, energy_j=1500.0),
        _pt(500.0, energy_j=800.0),
    ]
    markers = _build_markers(pts, zero_distance_m=100.0, ethical_energy_j=1500.0)
    assert any("etisk" in m.label.lower() or "Max" in m.label for m in markers)


def test_markers_no_ethical_when_none():
    pts = [_pt(d, energy_j=3000.0) for d in [100, 200, 300]]
    markers = _build_markers(pts, zero_distance_m=100.0, ethical_energy_j=None)
    assert not any("etisk" in m.label.lower() for m in markers)


# ---------------------------------------------------------------------------
# point_at lookup
# ---------------------------------------------------------------------------


def test_point_at_exact():
    pts = _make_points(5, 400.0)
    data = BulletJourneyData.from_trajectory(pts)
    pt = data.point_at(0.0)
    assert pt["distance_m"] == 0.0


def test_point_at_nearest():
    pts = [_pt(0.0), _pt(100.0), _pt(200.0), _pt(300.0)]
    data = BulletJourneyData.from_trajectory(pts)
    pt = data.point_at(95.0)
    assert pt["distance_m"] == 100.0


def test_point_at_empty_returns_empty_dict():
    data = BulletJourneyData.from_trajectory([])
    assert data.point_at(100.0) == {}


def test_point_at_contains_all_fields():
    pts = _make_points(3, 200.0)
    data = BulletJourneyData.from_trajectory(pts)
    pt = data.point_at(100.0)
    for key in (
        "distance_m",
        "drop_cm",
        "windage_cm",
        "velocity_fps",
        "mach",
        "energy_joules",
        "stability_sg",
        "wind_drift_cm",
        "spin_drift_cm",
        "coriolis_cm",
    ):
        assert key in pt, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Terrain interpolation
# ---------------------------------------------------------------------------


def test_terrain_interpolation_flat():
    terrain = [(0.0, 100.0), (500.0, 100.0)]
    result = _interpolate_terrain([0.0, 100.0, 250.0, 500.0], terrain)
    assert all(abs(r) < 0.1 for r in result)  # normalized to 0


def test_terrain_interpolation_slope():
    terrain = [(0.0, 100.0), (500.0, 150.0)]
    result = _interpolate_terrain([0.0, 250.0, 500.0], terrain)
    assert abs(result[1] - 25.0) < 1.0  # midpoint = +25m


def test_terrain_interpolation_clamps_beyond_range():
    terrain = [(100.0, 200.0), (300.0, 210.0)]
    result = _interpolate_terrain([0.0, 500.0], terrain)
    # Beyond range → uses end values
    assert result[0] == terrain[0][1] - terrain[0][1]  # normalized = 0
    assert result[1] == terrain[1][1] - terrain[0][1]  # = 10


def test_terrain_interpolation_empty_terrain():
    result = _interpolate_terrain([0.0, 100.0, 200.0], [])
    assert result == [0.0, 0.0, 0.0]


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_has_transonic_zone_true():
    pts = [
        _pt(0.0, phase="supersonic"),
        _pt(100.0, phase="transonic"),
    ]
    data = BulletJourneyData.from_trajectory(pts)
    assert data.has_transonic_zone is True


def test_has_transonic_zone_false():
    pts = [_pt(d, phase="supersonic") for d in [0, 100, 200]]
    data = BulletJourneyData.from_trajectory(pts)
    assert data.has_transonic_zone is False


def test_sg_warning_when_marginal():
    pts = [_pt(0.0, sg=1.6), _pt(100.0, sg=1.2)]
    data = BulletJourneyData.from_trajectory(pts)
    assert data.sg_warning is True


def test_sg_warning_false_when_all_stable():
    pts = [_pt(d, sg=1.8) for d in [0, 100, 200]]
    data = BulletJourneyData.from_trajectory(pts)
    assert data.sg_warning is False


# ---------------------------------------------------------------------------
# Integration: from_trajectory + build_field_solution pipeline
# ---------------------------------------------------------------------------


def test_pipeline_from_real_trajectory():
    """Full pipeline: build_field_solution → BulletJourneyData."""
    from src.field_planning.models import (
        AtmosphereLayer,
        FieldSession,
        FieldTarget,
        GeoPoint,
        LayeredAtmosphere,
        WeaponBallisticProfile,
    )
    from src.field_planning.services import build_field_solution

    profile = WeaponBallisticProfile(
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
    layer = AtmosphereLayer(0.0, 8.0, 1008.0, 70.0, 2.0, 270.0, 1.0, 0.0)
    sess = FieldSession(profile=profile, atmosphere=LayeredAtmosphere(layers=[layer]))
    tgt = FieldTarget(
        position=GeoPoint(61.0, 10.1),
        distance_m=600.0,
        slant_distance_m=600.0,
        inclination_deg=0.0,
        bearing_deg=90.0,
    )
    pts = build_field_solution(sess, tgt, step_m=50.0)
    data = BulletJourneyData.from_trajectory(pts, zero_distance_m=100.0)

    assert len(data.distances_m) > 5
    assert data.phase_regions
    assert any(m.label == "Zero" for m in data.markers)
    assert data.min_energy_j > 0
    assert data.summary_lines
