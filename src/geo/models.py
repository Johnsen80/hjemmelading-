# Geo models and data classes
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeoPoint:
    lat: float
    lon: float
    alt_m: Optional[float] = None


@dataclass
class GeoShot:
    shooter: GeoPoint
    target: GeoPoint


@dataclass
class GeoSolution:
    slant_range_m: float
    horizontal_range_m: float
    delta_alt_m: float
    inclination_deg: float
    bearing_deg: float
