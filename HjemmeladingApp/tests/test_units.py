from HjemmeladingApp.utils import units


def test_unit_conversions():
    assert abs(units.km_to_miles(1.0) - 0.62137119) < 1e-8
    assert abs(units.miles_to_km(0.62137119) - 1.0) < 1e-6
    assert abs(units.kg_to_lbs(1.0) - 2.2046226218) < 1e-9
    assert abs(units.lbs_to_kg(2.2046226218) - 1.0) < 1e-6
    assert abs(units.celsius_to_fahrenheit(0) - 32.0) < 1e-9
    assert abs(units.fahrenheit_to_celsius(32.0) - 0.0) < 1e-9
    assert abs(units.inches_to_mm(1.0) - 25.4) < 1e-9
    assert abs(units.mm_to_inches(25.4) - 1.0) < 1e-9
    assert abs(units.grains_to_grams(100.0) - 6.479891) < 1e-6
    assert abs(units.grams_to_grains(6.479891) - 100.0) < 1e-6
    assert abs(units.fps_to_mps(1000.0) - 304.8) < 1e-9
    assert abs(units.mps_to_fps(304.8) - 1000.0) < 1e-9
    assert abs(units.yards_to_meters(100.0) - 91.44) < 1e-9
    assert abs(units.meters_to_yards(91.44) - 100.0) < 1e-9
    assert abs(units.psi_to_bar(1000.0) - 68.9475729) < 1e-7
    assert abs(units.bar_to_psi(68.9475729) - 1000.0) < 1e-6
