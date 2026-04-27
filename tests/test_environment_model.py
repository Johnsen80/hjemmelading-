from src.solvers.trajectory import build_atmosphere
from src.utils.advanced_ballistics import AtmosphericConditions
from src.utils.environment import BallisticEnvironment


def test_ballistic_environment_standard_conditions_are_near_isa():
    environment = BallisticEnvironment(
        temperature_c=15.0,
        pressure_hpa=1013.25,
        humidity_percent=0.0,
        altitude_m=0.0,
        temperature_source="provided",
        pressure_source="provided",
        humidity_source="provided",
        altitude_source="provided",
    )

    assert abs(environment.density_ratio() - 1.0) < 0.02
    assert abs(environment.density_altitude_m()) < 100.0


def test_build_atmosphere_exposes_density_metrics():
    atmosphere = build_atmosphere(20.0, 1000.0, 60.0, 250.0)

    assert atmosphere.density_ratio > 0.0
    assert isinstance(atmosphere.density_altitude_m, float)


def test_advanced_ballistics_uses_same_density_ratio_source():
    environment = BallisticEnvironment(
        temperature_c=10.0,
        pressure_hpa=990.0,
        humidity_percent=35.0,
        altitude_m=400.0,
        temperature_source="provided",
        pressure_source="provided",
        humidity_source="provided",
        altitude_source="provided",
    )
    conditions = AtmosphericConditions(
        temperature_f=50.0,
        pressure_inhg=990.0 / 33.8638866667,
        humidity_percent=35.0,
        altitude_ft=400.0 / 0.3048,
    )

    assert abs(environment.density_ratio() - conditions.get_density_ratio()) < 1e-6
