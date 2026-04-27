import pytest

from src.utils.gp_optimizer import suggest_next_charge


@pytest.mark.core
def test_suggest_next_charge_heuristic():
    # simple observed ladder: velocities increase with charge up to 42.5
    charges = [41.5, 42.0, 42.5]
    velocities = [2750.0, 2775.0, 2790.0]
    bounds = (41.0, 44.0)
    s = suggest_next_charge(charges, velocities, bounds)
    # heuristic should suggest 43.0 (base 42.5 + 0.5)
    assert 41.0 <= s <= 44.0
    assert abs(s - 43.0) < 1.0
