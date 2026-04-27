# Ballistics types and data classes
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class BCModel(Enum):
    G1 = "G1"
    G7 = "G7"


@dataclass
class BallisticInput:
    mv_mps: float
    bc: float
    bc_model: BCModel
    bullet_mass_gr: float
    caliber_mm: float
    sight_height_mm: float
    zero_distance_m: int
    spin_twist: Optional[str] = None
    drag_function: Optional[Callable] = None


@dataclass
class ShotScenario:
    range_m: float
    inclination_deg: float
    wind_speed_mps: float
    wind_dir_deg: float
    azimuth_deg: Optional[float] = None


@dataclass
class BallisticSolution:
    elevation_correction: float
    windage_correction: float
    drop_m: float
    drift_m: float
    tof_s: float
    impact_velocity_mps: float
