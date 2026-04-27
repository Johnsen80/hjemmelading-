# Geo services
from src.geo.models import GeoPoint, GeoShot, GeoSolution


def compute_geo_solution(shot: GeoShot) -> GeoSolution:
    """Compute the geographic solution for a shot."""
    # Placeholder logic for Haversine formula, bearing, etc.
    delta_alt = 0.0
    try:
        if shot.shooter.alt_m is not None and shot.target.alt_m is not None:
            delta_alt = float(shot.target.alt_m) - float(shot.shooter.alt_m)
    except Exception:
        delta_alt = 0.0
    return GeoSolution(
        slant_range_m=0.0,
        horizontal_range_m=0.0,
        delta_alt_m=delta_alt,
        inclination_deg=0.0,
        bearing_deg=0.0,
    )


def fetch_elevation(point: GeoPoint) -> float:
    """Fetch elevation for a given geographic point."""
    # Placeholder logic for DEM lookup or API call
    return float(point.alt_m) if point.alt_m is not None else 0.0
