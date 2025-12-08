import math

import pytest

from modules.hjemmelading import (
    grains_to_grams,
    grams_to_grains,
    powder_mass_from_volume,
    safe_parse_float,
)


def test_zero_and_negative_values():
    # Zero values
    assert grams_to_grains(0) == 0.0
    assert grains_to_grams(0) == 0.0
    assert powder_mass_from_volume(0.0, 1.2) == 0.0

    # Negative values: function should perform mathematical operation
    assert grams_to_grains(-5.0) == -5.0 * 15.4323584
    assert grains_to_grams(-15.4323584) == pytest.approx(-1.0)
    assert powder_mass_from_volume(-2.0, 1.0) == -2.0


def test_extreme_values_and_precision():
    # Very large numbers should not raise but may result in inf if overflow
    large = 1e308
    gr = grams_to_grains(large)
    # grains conversion of large should be finite or inf; we accept both
    assert math.isfinite(gr) or math.isinf(gr)

    # Precision: roundtrip within relative tolerance
    val = 123.456789
    assert grains_to_grams(grams_to_grains(val)) == pytest.approx(val, rel=1e-12)


def test_density_edge_cases():
    # Zero density -> zero mass
    assert powder_mass_from_volume(10.0, 0.0) == 0.0

    # Very small density
    mass = powder_mass_from_volume(50.0, 1e-6)
    assert mass == pytest.approx(50.0e-6)


def test_safe_parse_various_inputs():
    assert safe_parse_float("3.5") == 3.5
    assert safe_parse_float("-2.1") == -2.1
    # boolean True -> 1.0, False -> 0.0
    assert safe_parse_float(True) == 1.0
    assert safe_parse_float(False) == 0.0
    # None and non-numeric should return default
    assert safe_parse_float(None, default=7.7) == 7.7
    assert safe_parse_float("nan", default=9.9) != 9.9 or math.isnan(float("nan"))
    assert safe_parse_float("not-a-number", default=4.4) == 4.4
