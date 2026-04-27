def fetch_lidar_profile(shooter_lat, shooter_lon, target_lat, target_lon, n_points=10):
    """
    Fetches an elevation profile (LiDAR/DEM) between shooter and target.
    Returns a list of (lat, lon, elevation).
    """
    import numpy as np
    import requests  # type: ignore[import-untyped]

    lats = np.linspace(shooter_lat, target_lat, n_points)
    lons = np.linspace(shooter_lon, target_lon, n_points)
    profile = []
    for lat, lon in zip(lats, lons):
        try:
            url = f"https://api.opentopodata.org/v1/srtm30m?locations={lat},{lon}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", []) if isinstance(data, dict) else []
            elevation = results[0].get("elevation") if results else None
        except Exception:
            elevation = None
        profile.append((lat, lon, elevation))
    return profile


"""Minimal shim re-exporting the canonical baseline implementation.

Keep this file intentionally small so language servers and editors
import it cleanly. The full implementation lives in
`src.modules.terrain_map_baseline`.
"""

from ..ballistics.types import ShotScenario
from ..geo.models import GeoPoint, GeoShot
from ..geo.services import compute_geo_solution
from ..solvers.trajectory import build_atmosphere, solve_trajectory
from .terrain_map_baseline import (
    PurposeSelectionDialog,
    TerrainMapViewer,
    _safe_add_marker,
    _safe_add_polyline,
    fetch_weather_data_owm,
    fetch_weather_for_viewer_async,
    get_elevation,
)

__all__ = [
    "TerrainMapViewer",
    "PurposeSelectionDialog",
    "_safe_add_marker",
    "_safe_add_polyline",
    "get_elevation",
    "fetch_weather_data_owm",
    "fetch_weather_for_viewer_async",
    "analyze_terrain_risk_from_profile",
]


def analyze_terrain_risk_from_profile(profile, env_data=None):
    """
    Practical terrain risk assessment based on an elevation profile.

    This is a conservative field assessment, not a full fluid-dynamics solver.
    """
    env_data = env_data or {}
    elevations = []
    for point in profile or []:
        elevation = None
        if isinstance(point, (list, tuple)) and len(point) >= 3:
            elevation = point[2]
        if isinstance(elevation, (int, float)):
            elevations.append(float(elevation))

    if len(elevations) < 3:
        return {
            "level": "unknown",
            "title": "Terrain Risk",
            "message": "Too few elevation points to assess terrain influence along the line of fire.",
            "checks": [
                "Collect a denser elevation profile before using terrain risk in field assessment.",
            ],
        }

    start = elevations[0]
    end = elevations[-1]
    minimum = min(elevations)
    maximum = max(elevations)
    relief = maximum - minimum
    valley_depth = min(start, end) - minimum
    ridge_height = maximum - max(start, end)

    score = 0.0
    checks = []

    if relief >= 120:
        score += 2.0
        checks.append(
            "Large elevation changes along the line of fire can create shifting wind and thermals."
        )
    elif relief >= 60:
        score += 1.0
        checks.append(
            "Moderate elevation changes can create local wind channeling and unstable air."
        )

    if valley_depth >= 25:
        score += 1.5
        checks.append(
            "The line of fire drops into a clear dip or valley that can create channeling winds."
        )

    if ridge_height >= 25:
        score += 1.5
        checks.append(
            "The line of fire crosses a distinct ridge that can create lee-side effects and turbulence."
        )

    flat_sections = 0
    for left, right in zip(elevations, elevations[1:]):
        if abs(right - left) <= 1.0:
            flat_sections += 1
    flat_ratio = flat_sections / max(1, len(elevations) - 1)
    if flat_ratio >= 0.6:
        score += 0.75
        checks.append(
            "A mostly flat profile can indicate open terrain with mirage and thermal drift."
        )

    wind_speed = env_data.get("wind_speed_mps")
    if (
        isinstance(wind_speed, (int, float))
        and float(wind_speed) >= 4.0
        and score >= 1.0
    ):
        score += 0.75
        checks.append(
            "Existing wind increases the likelihood of terrain influence along the line of fire."
        )

    if score >= 3.5:
        level = "high"
        message = (
            "The terrain profile indicates a high risk of local wind or thermal effects. "
            "Use extra caution, read mirage carefully, and consider additional confirmation shots."
        )
    elif score >= 1.5:
        level = "medium"
        message = (
            "The terrain profile may affect point of impact through local wind channeling or thermals. "
            "Use extra caution at longer distances."
        )
    else:
        level = "low"
        message = (
            "The terrain profile looks relatively calm. Normal wind and mirage reading is still required, "
            "but the terrain signal appears limited."
        )

    if not checks:
        checks.append(
            "No clear terrain signals beyond a normal elevation profile were found."
        )

    return {
        "level": level,
        "title": "Terrain Risk",
        "message": message,
        "score": round(score, 2),
        "checks": checks[:4],
        "profile_summary": {
            "relief_m": round(relief, 1),
            "valley_depth_m": round(valley_depth, 1),
            "ridge_height_m": round(ridge_height, 1),
            "flat_ratio": round(flat_ratio, 2),
        },
    }


def integrate_map_with_ballistics(
    shooter_lat, shooter_lon, target_lat, target_lon, env_data, ballistic_input
):
    """
    Integrate map data with ballistics calculations.

    Args:
        shooter_lat (float): Latitude of the shooter.
        shooter_lon (float): Longitude of the shooter.
        target_lat (float): Latitude of the target.
        target_lon (float): Longitude of the target.
        env_data (dict): Environmental data (temperature, pressure, etc.).
        ballistic_input (BallisticInput): Ballistic input data.

    Returns:
        dict: Combined GeoSolution and BallisticSolution.
    """
    # Create GeoShot object
    geo_shot = GeoShot(
        shooter=GeoPoint(lat=shooter_lat, lon=shooter_lon),
        target=GeoPoint(lat=target_lat, lon=target_lon),
    )

    # Compute GeoSolution
    geo_solution = compute_geo_solution(geo_shot)

    # Build AtmosphereSnapshot
    atmosphere = build_atmosphere(
        temp_c=env_data["temperature_c"],
        pressure_hpa=env_data["pressure_hpa"],
        humidity_pct=env_data["humidity_pct"],
        altitude_m=env_data["altitude_m"],
    )

    # Create ShotScenario
    shot_scenario = ShotScenario(
        range_m=geo_solution.slant_range_m,
        inclination_deg=geo_solution.inclination_deg,
        wind_speed_mps=env_data.get("wind_speed_mps", 0),
        wind_dir_deg=env_data.get("wind_dir_deg", 0),
    )

    # Solve trajectory
    ballistic_solution = solve_trajectory(ballistic_input, shot_scenario, atmosphere)
    terrain_risk = analyze_terrain_risk_from_profile(
        env_data.get("terrain_profile") or [],
        env_data,
    )

    return {
        "geo_solution": geo_solution,
        "ballistic_solution": ballistic_solution,
        "terrain_risk": terrain_risk,
    }
