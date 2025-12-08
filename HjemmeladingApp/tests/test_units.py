from HjemmeladingApp.utils import units


def test_unit_conversions():
    assert abs(units.km_to_miles(1.0) - 0.62137119) < 1e-8
    assert abs(units.miles_to_km(0.62137119) - 1.0) < 1e-6
    assert abs(units.kg_to_lbs(1.0) - 2.2046226218) < 1e-9
    assert abs(units.lbs_to_kg(2.2046226218) - 1.0) < 1e-6
    assert abs(units.celsius_to_fahrenheit(0) - 32.0) < 1e-9
    assert abs(units.fahrenheit_to_celsius(32.0) - 0.0) < 1e-9
