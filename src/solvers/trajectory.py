from dataclasses import dataclass
from typing import Optional

from src.ballistics.types import BallisticInput, BallisticSolution, ShotScenario
from src.utils.environment import BallisticEnvironment


@dataclass
class AtmosphereSnapshot:
    temperature_c: float
    pressure_hpa: float
    humidity_pct: float
    altitude_m: float
    wind_speed_mps: Optional[float] = None
    wind_dir_deg: Optional[float] = None
    density_ratio: float = 1.0
    density_altitude_m: float = 0.0


def solve_trajectory(
    input: BallisticInput, scenario: ShotScenario, atm: AtmosphereSnapshot
) -> BallisticSolution:
    # Placeholder for trajectory solving logic
    return BallisticSolution(
        elevation_correction=0.0,
        windage_correction=0.0,
        drop_m=0.0,
        drift_m=0.0,
        tof_s=0.0,
        impact_velocity_mps=0.0,
    )


def build_atmosphere(
    temp_c, pressure_hpa, humidity_pct, altitude_m
) -> AtmosphereSnapshot:
    environment = BallisticEnvironment(
        temperature_c=float(temp_c),
        pressure_hpa=float(pressure_hpa),
        humidity_percent=float(humidity_pct),
        altitude_m=float(altitude_m),
        temperature_source="provided",
        pressure_source="provided",
        humidity_source="provided",
        altitude_source="provided",
    )
    return AtmosphereSnapshot(
        temperature_c=temp_c,
        pressure_hpa=pressure_hpa,
        humidity_pct=humidity_pct,
        altitude_m=altitude_m,
        density_ratio=environment.density_ratio(),
        density_altitude_m=environment.density_altitude_m(),
    )
