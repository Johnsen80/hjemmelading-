# Zero models and data classes
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TurretUnit(Enum):
    MRAD = "MRAD"
    MOA = "MOA"


@dataclass
class AtmosphereSnapshot:
    temperature_c: float
    pressure_hpa: float
    humidity_pct: float
    altitude_m: float
    wind_speed_mps: Optional[float] = None
    wind_dir_deg: Optional[float] = None


@dataclass
class ZeroProfile:
    id: str
    firearm_id: int
    optic_id: int
    load_recipe_id: int
    zero_distance_m: int
    sight_height_mm: float
    turret_unit: TurretUnit
    click_value: float
    zero_env: AtmosphereSnapshot
    confirmed_at: datetime


@dataclass
class DopeEntry:
    distance_m: int
    elevation: float
    windage: float
    time_of_flight_s: float
    drop_cm: float
    drift_cm: float
