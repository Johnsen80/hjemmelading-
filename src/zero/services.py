# Zero services
from src.ballistics.services import predict_poi_shift


def test_new_load(zero_profile, new_load, target_distance_m, env):
    """Test a new load and calculate POI shift."""
    poi_shift = predict_poi_shift(zero_profile, new_load, target_distance_m, env)
    return poi_shift


def log_scenario(snapshot):
    """Log all inputs to reproduce the scenario."""
    # Placeholder for logging logic
    pass
