from modules.hjemmelading import (
    grams_to_grains,
    grains_to_grams,
    powder_mass_from_volume,
    powder_mass_from_volume_ml,
    safe_parse_float,
)


def test_grams_grains_roundtrip():
    g = 10.0
    gr = grams_to_grains(g)
    assert abs(grains_to_grams(gr) - g) < 1e-9


def test_powder_mass_simple():
    # density 1 g/cm3 -> mass equals volume (cm3)
    assert powder_mass_from_volume(5.0, 1.0) == 5.0
    assert powder_mass_from_volume_ml(12.3, 0.95) == powder_mass_from_volume(12.3, 0.95)


def test_safe_parse_float():
    assert safe_parse_float("3.14") == 3.14
    assert safe_parse_float(None, default=1.5) == 1.5
    assert safe_parse_float("not-a-number", default=2.0) == 2.0
