"""Block 4 tests: atmosphere modelling, terrain classification, warning generator."""

from __future__ import annotations

from src.field_planning.atmosphere import (
    build_atmosphere_warnings,
    build_lapse_rate_layers,
    build_layered_atmosphere,
    build_surface_layer,
    compute_density_altitude,
    compute_density_ratio,
    compute_thermal_risk,
    detect_inversion,
    katabatic_risk,
)
from src.field_planning.terrain_classifier import (
    analyse_terrain_profile,
    build_segment,
    classify_from_elevation_profile,
    classify_from_osm_tags,
)

# ---------------------------------------------------------------------------
# Density altitude
# ---------------------------------------------------------------------------


def test_density_altitude_sea_level_standard():
    da = compute_density_altitude(15.0, 1013.25, 0.0)
    assert abs(da) < 50.0  # should be near 0m


def test_density_altitude_hot_low_pressure():
    da_hot = compute_density_altitude(40.0, 990.0, 0.0)
    da_std = compute_density_altitude(15.0, 1013.25, 0.0)
    assert da_hot > da_std  # hotter + lower pressure = higher DA


def test_density_altitude_high_elevation():
    da = compute_density_altitude(5.0, 900.0, 20.0)
    assert da > 500.0  # 900 hPa ~ 1000m altitude → DA should be significant


def test_density_ratio_standard_day():
    dr = compute_density_ratio(15.0, 1013.25, 0.0)
    assert abs(dr - 1.0) < 0.01


def test_density_ratio_hot_weather():
    dr_hot = compute_density_ratio(40.0, 1013.25, 0.0)
    dr_std = compute_density_ratio(15.0, 1013.25, 0.0)
    assert dr_hot < dr_std  # hot → less dense


def test_density_ratio_high_humidity_lower():
    dr_dry = compute_density_ratio(15.0, 1013.25, 0.0)
    dr_wet = compute_density_ratio(15.0, 1013.25, 90.0)
    assert dr_wet < dr_dry  # humid air is less dense


# ---------------------------------------------------------------------------
# Surface layer
# ---------------------------------------------------------------------------


def test_surface_layer_basic():
    layer = build_surface_layer(8.0, 1008.0, 65.0, 3.0, 270.0)
    assert layer.temperature_c == 8.0
    assert layer.pressure_hpa == 1008.0
    assert 0.9 < layer.density_ratio < 1.1


def test_surface_layer_computes_density_altitude():
    layer = build_surface_layer(30.0, 980.0, 20.0, 0.0, 0.0)
    assert layer.density_altitude_m > 500.0


# ---------------------------------------------------------------------------
# Lapse rate layers
# ---------------------------------------------------------------------------


def test_lapse_rate_layers_temperature_decreases():
    surface = build_surface_layer(15.0, 1013.25, 50.0, 2.0, 270.0)
    layers = build_lapse_rate_layers(surface, max_altitude_m=1500.0, step_m=500.0)
    temps = [lyr.temperature_c for lyr in layers]
    for i in range(1, len(temps)):
        assert temps[i] < temps[i - 1], f"Temp at layer {i} not < layer {i-1}"


def test_lapse_rate_layers_wind_increases():
    surface = build_surface_layer(15.0, 1013.25, 50.0, 3.0, 270.0)
    layers = build_lapse_rate_layers(surface, max_altitude_m=1000.0, step_m=500.0)
    winds = [lyr.wind_speed_mps for lyr in layers]
    assert winds[-1] > winds[0]  # wind should increase with height


def test_lapse_rate_layers_count():
    surface = build_surface_layer(15.0, 1013.25, 50.0, 0.0, 0.0)
    layers = build_lapse_rate_layers(surface, max_altitude_m=1000.0, step_m=500.0)
    # surface + 2 steps
    assert len(layers) == 3


# ---------------------------------------------------------------------------
# Inversion detection
# ---------------------------------------------------------------------------


def test_detect_inversion_normal_lapse():
    surface = build_surface_layer(15.0, 1013.25, 50.0, 0.0, 0.0)
    layers = build_lapse_rate_layers(surface)
    inv, alt = detect_inversion(layers)
    assert inv is False


def test_detect_inversion_when_warmer_above():
    l1 = build_surface_layer(2.0, 1008.0, 80.0, 0.0, 0.0, altitude_m=0.0)
    l2 = build_surface_layer(8.0, 980.0, 70.0, 0.0, 0.0, altitude_m=200.0)  # warmer!
    l3 = build_surface_layer(4.0, 960.0, 60.0, 0.0, 0.0, altitude_m=500.0)
    inv, alt = detect_inversion([l1, l2, l3])
    assert inv is True
    assert alt == 0.0  # inversion starts at layer 0


def test_detect_inversion_single_layer():
    layer = build_surface_layer(15.0, 1013.25, 50.0, 0.0, 0.0)
    inv, alt = detect_inversion([layer])
    assert inv is False
    assert alt is None


# ---------------------------------------------------------------------------
# Katabatic risk
# ---------------------------------------------------------------------------


def test_katabatic_risk_ideal_conditions():
    assert (
        katabatic_risk(
            valley_depth_m=80.0,
            wind_speed_mps=0.5,
            hour_of_day=5,
            cloud_cover_oktas=0,
        )
        is True
    )


def test_katabatic_no_valley():
    assert katabatic_risk(None, 0.5, 5, 0) is False
    assert katabatic_risk(20.0, 0.5, 5, 0) is False  # too shallow


def test_katabatic_high_wind():
    assert katabatic_risk(100.0, 5.0, 4, 0) is False


def test_katabatic_daytime():
    assert katabatic_risk(100.0, 1.0, 14, 0) is False


def test_katabatic_overcast():
    assert katabatic_risk(100.0, 0.5, 4, 7) is False


# ---------------------------------------------------------------------------
# Thermal risk
# ---------------------------------------------------------------------------


def test_thermal_risk_rock_full_sun():
    risk = compute_thermal_risk(["rock"], [500.0], solar_factor=1.0, wind_speed_mps=0.0)
    assert risk == "high"


def test_thermal_risk_forest_full_sun():
    risk = compute_thermal_risk(["forest"], [500.0], solar_factor=1.0)
    assert risk == "low"


def test_thermal_risk_overcast():
    risk = compute_thermal_risk(["rock"], [500.0], solar_factor=0.1)
    assert risk == "low"


def test_thermal_risk_high_wind_damps():
    risk = compute_thermal_risk(["rock"], [500.0], solar_factor=1.0, wind_speed_mps=6.0)
    assert risk == "low"


def test_thermal_risk_mixed_terrain():
    risk = compute_thermal_risk(
        ["forest", "rock", "forest"],
        [200.0, 100.0, 200.0],
        solar_factor=1.0,
    )
    # Mostly forest → moderate/low
    assert risk in {"low", "moderate"}


# ---------------------------------------------------------------------------
# Warning generator
# ---------------------------------------------------------------------------


def test_warnings_inversion():
    from src.field_planning.models import LayeredAtmosphere

    lyr = build_surface_layer(2.0, 1005.0, 70.0, 0.5, 270.0)
    atm = LayeredAtmosphere(
        layers=[lyr],
        inversion_detected=True,
        inversion_altitude_m=50.0,
        thermal_risk_level="low",
        katabatic_risk=False,
    )
    atm.warnings = []
    warnings = build_atmosphere_warnings(atm)
    assert any("inversjon" in w.lower() or "inversion" in w.lower() for w in warnings)


def test_warnings_katabatic():
    from src.field_planning.models import LayeredAtmosphere

    lyr = build_surface_layer(2.0, 1005.0, 70.0, 0.5, 270.0)
    atm = LayeredAtmosphere(
        layers=[lyr],
        katabatic_risk=True,
        inversion_detected=False,
        thermal_risk_level="low",
    )
    atm.warnings = []
    warnings = build_atmosphere_warnings(atm, valley_depth_m=80.0)
    assert any("katabatisk" in w.lower() or "kaldluft" in w.lower() for w in warnings)


def test_warnings_high_thermal():
    from src.field_planning.models import LayeredAtmosphere

    lyr = build_surface_layer(25.0, 1008.0, 30.0, 1.0, 270.0)
    atm = LayeredAtmosphere(
        layers=[lyr],
        thermal_risk_level="high",
        inversion_detected=False,
        katabatic_risk=False,
    )
    atm.warnings = []
    warnings = build_atmosphere_warnings(atm)
    assert any("termikk" in w.lower() for w in warnings)


def test_warnings_high_humidity():
    from src.field_planning.models import LayeredAtmosphere

    lyr = build_surface_layer(15.0, 1013.25, 82.0, 1.0, 270.0)
    atm = LayeredAtmosphere(
        layers=[lyr],
        thermal_risk_level="low",
        inversion_detected=False,
        katabatic_risk=False,
    )
    atm.warnings = []
    warnings = build_atmosphere_warnings(atm)
    assert any("fuktigh" in w.lower() or "82" in w for w in warnings)


def test_warnings_no_warnings_standard():
    from src.field_planning.models import LayeredAtmosphere

    lyr = build_surface_layer(15.0, 1013.25, 50.0, 3.0, 270.0)
    atm = LayeredAtmosphere(
        layers=[lyr],
        thermal_risk_level="low",
        inversion_detected=False,
        katabatic_risk=False,
    )
    atm.warnings = []
    warnings = build_atmosphere_warnings(atm)
    assert all("⚠️" not in w for w in warnings)


# ---------------------------------------------------------------------------
# build_layered_atmosphere integration
# ---------------------------------------------------------------------------


def test_build_layered_atmosphere_single_layer():
    atm = build_layered_atmosphere(15.0, 1013.25, 50.0, 2.0, 270.0)
    assert len(atm.layers) > 1  # should have multiple layers from lapse rate
    assert atm.surface_layer.temperature_c == 15.0


def test_build_layered_atmosphere_rock_sunny_gives_high_thermal():
    atm = build_layered_atmosphere(
        25.0,
        1008.0,
        30.0,
        0.5,
        270.0,
        surface_types=["rock", "rock"],
        segment_lengths_m=[300.0, 300.0],
        solar_factor=1.0,
    )
    assert atm.thermal_risk_level == "high"


def test_build_layered_atmosphere_katabatic_valley():
    atm = build_layered_atmosphere(
        3.0,
        1010.0,
        80.0,
        0.3,
        0.0,
        valley_depth_m=90.0,
        hour_of_day=4,
        cloud_cover_oktas=0,
    )
    assert atm.katabatic_risk is True


def test_build_layered_atmosphere_with_radiosonde():
    radiosonde = [
        {
            "altitude_m": 500.0,
            "temperature_c": 8.0,
            "pressure_hpa": 955.0,
            "humidity_pct": 60.0,
            "wind_speed_mps": 4.0,
            "wind_dir_deg": 280.0,
        },
        {
            "altitude_m": 1000.0,
            "temperature_c": 2.0,
            "pressure_hpa": 900.0,
            "humidity_pct": 50.0,
            "wind_speed_mps": 7.0,
            "wind_dir_deg": 290.0,
        },
    ]
    atm = build_layered_atmosphere(
        15.0,
        1013.25,
        55.0,
        2.0,
        270.0,
        radiosonde_layers=radiosonde,
    )
    assert len(atm.layers) == 3  # surface + 2 radiosonde
    assert atm.layers[1].altitude_m == 500.0
    assert atm.layers[1].source == "radiosonde"


# ---------------------------------------------------------------------------
# Terrain classifier
# ---------------------------------------------------------------------------


def test_classify_osm_tags_water():
    assert classify_from_osm_tags({"natural": "water"}) == "water"


def test_classify_osm_tags_forest():
    assert classify_from_osm_tags({"landuse": "forest"}) == "forest"


def test_classify_osm_tags_wetland():
    assert classify_from_osm_tags({"natural": "wetland"}) == "swamp"


def test_classify_osm_tags_building():
    assert classify_from_osm_tags({"building": "yes"}) == "urban"


def test_classify_osm_tags_unknown():
    assert classify_from_osm_tags({}) == "field"


def test_build_segment_rock_thermal():
    seg = build_segment(0.0, 200.0, "rock")
    assert seg.thermal_contribution == "high"
    assert seg.ricochet_risk is True
    assert seg.wind_factor > 1.0


def test_build_segment_forest_sheltered():
    seg = build_segment(0.0, 200.0, "forest")
    assert seg.wind_factor < 1.0
    assert seg.thermal_contribution == "none"


def test_classify_from_elevation_steep_is_rock():
    # 45° slope → rock
    pts = [(0.0, 100.0), (100.0, 200.0)]  # 45°
    segs = classify_from_elevation_profile(pts, 100.0, segment_size_m=100.0)
    assert segs[0].surface_type == "rock"


def test_classify_from_elevation_flat_is_field():
    pts = [(0.0, 100.0), (1000.0, 102.0)]  # nearly flat
    segs = classify_from_elevation_profile(pts, 1000.0, segment_size_m=200.0)
    assert all(s.surface_type == "field" for s in segs)


def test_analyse_terrain_profile_detects_valley():
    segs = [build_segment(0.0, 500.0, "field"), build_segment(500.0, 1000.0, "field")]
    elev_pts = [
        (0.0, 200.0),
        (250.0, 100.0),
        (500.0, 80.0),  # valley
        (750.0, 120.0),
        (1000.0, 200.0),
    ]
    result = analyse_terrain_profile(segs, elev_pts)
    assert result["valley_depth_m"] > 0


def test_analyse_terrain_profile_ricochet_zones():
    segs = [
        build_segment(0.0, 200.0, "field"),
        build_segment(200.0, 400.0, "water"),  # ricochet risk
        build_segment(400.0, 600.0, "forest"),
    ]
    elev_pts = [(0.0, 100.0), (600.0, 100.0)]
    result = analyse_terrain_profile(segs, elev_pts)
    assert len(result["ricochet_risk_zones"]) == 1
    assert result["ricochet_risk_zones"][0] == (200.0, 400.0)
