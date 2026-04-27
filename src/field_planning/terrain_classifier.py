"""Terrain classification along the shot path.

Classifies terrain segments between shooter and target into surface types
(rock, water, swamp, forest, snow, field, urban) using:
  1. Cached Kartverket AR5 / OSM landuse data (when available)
  2. Elevation-only heuristics (offline fallback)

Assigns wind factors and thermal contributions per segment.
"""

from __future__ import annotations

import math

from .models import TerrainProfile, TerrainSegment

# ---------------------------------------------------------------------------
# OSM landuse → surface type mapping
# ---------------------------------------------------------------------------

_OSM_LANDUSE_MAP: dict[str, str] = {
    "forest": "forest",
    "wood": "forest",
    "farmland": "field",
    "meadow": "field",
    "grass": "field",
    "scrub": "field",
    "heath": "field",
    "wetland": "swamp",
    "marsh": "swamp",
    "bog": "swamp",
    "water": "water",
    "reservoir": "water",
    "basin": "water",
    "bare_rock": "rock",
    "scree": "rock",
    "cliff": "rock",
    "glacier": "snow",
    "snow": "snow",
    "residential": "urban",
    "commercial": "urban",
    "industrial": "urban",
    "retail": "urban",
    "construction": "urban",
}

# Kartverket AR5 arealtype → surface type
_AR5_AREALTYPE_MAP: dict[int, str] = {
    10: "field",  # Bebygd areal (urban)
    11: "urban",
    12: "urban",
    20: "field",  # Samferdsel
    30: "field",  # Jordbruksareal
    50: "forest",  # Skog
    60: "swamp",  # Myr
    70: "rock",  # Åpen fastmark
    81: "water",  # Ferskvann
    82: "water",  # Hav
    90: "snow",  # Is og snø
}

# Wind multiplier per surface type (Venturi/sheltering effects)
_WIND_FACTOR: dict[str, float] = {
    "rock": 1.3,  # acceleration over bare ridge
    "water": 1.1,
    "swamp": 1.0,
    "forest": 0.6,  # sheltered
    "snow": 1.0,
    "field": 1.0,
    "urban": 0.8,  # turbulent but lower mean
    "unknown": 1.0,
}

# Thermal contribution per surface type
_THERMAL: dict[str, str] = {
    "rock": "high",
    "urban": "moderate",
    "swamp": "moderate",
    "water": "low",
    "field": "low",
    "forest": "none",
    "snow": "none",
    "unknown": "low",
}

# Ricochet risk (flat smooth surfaces at shallow angles)
_RICOCHET_RISK: dict[str, bool] = {
    "rock": True,
    "water": True,
    "snow": False,
    "swamp": False,
    "forest": False,
    "field": False,
    "urban": False,
    "unknown": False,
}


# ---------------------------------------------------------------------------
# Segment builder from classification
# ---------------------------------------------------------------------------


def build_segment(
    start_m: float,
    end_m: float,
    surface_type: str,
    elevation_m: float = 0.0,
) -> TerrainSegment:
    st = surface_type if surface_type in _WIND_FACTOR else "unknown"
    return TerrainSegment(
        start_m=start_m,
        end_m=end_m,
        surface_type=st,
        elevation_m=elevation_m,
        thermal_contribution=_THERMAL.get(st, "low"),
        wind_factor=_WIND_FACTOR.get(st, 1.0),
        ricochet_risk=_RICOCHET_RISK.get(st, False),
    )


# ---------------------------------------------------------------------------
# OSM-based classification (online)
# ---------------------------------------------------------------------------


def classify_from_osm_tags(tags: dict) -> str:
    """Map OSM tag dict to surface type string."""
    for key in ("landuse", "natural", "wetland", "water"):
        val = tags.get(key, "")
        if val in _OSM_LANDUSE_MAP:
            return _OSM_LANDUSE_MAP[val]
    if tags.get("building"):
        return "urban"
    if tags.get("waterway"):
        return "water"
    return "field"


def classify_shot_path_from_osm(
    sample_points: list[dict],
    distances_m: list[float],
    total_distance_m: float,
    segment_size_m: float = 100.0,
) -> list[TerrainSegment]:
    """Build terrain segments from OSM sample data.

    Parameters
    ----------
    sample_points:
        List of dicts, each with 'distance_m', 'tags' (OSM tags), 'elevation_m'.
    distances_m:
        Distance along shot path for each sample point.
    """
    if not sample_points:
        return [build_segment(0.0, total_distance_m, "field")]

    segments: list[TerrainSegment] = []
    step = segment_size_m
    d = 0.0
    while d < total_distance_m:
        end = min(d + step, total_distance_m)
        # Find sample nearest to midpoint of this segment
        mid = (d + end) / 2.0
        nearest = min(sample_points, key=lambda p: abs(p.get("distance_m", 0.0) - mid))
        st = classify_from_osm_tags(nearest.get("tags", {}))
        elev = float(nearest.get("elevation_m", 0.0))
        segments.append(build_segment(d, end, st, elev))
        d = end

    return segments


# ---------------------------------------------------------------------------
# Elevation-only heuristic (offline fallback)
# ---------------------------------------------------------------------------


def classify_from_elevation_profile(
    elevation_points: list[tuple[float, float]],
    total_distance_m: float,
    segment_size_m: float = 100.0,
) -> list[TerrainSegment]:
    """Estimate terrain type from elevation gradient alone (offline fallback).

    Rules:
    - High gradient (>15°) → rock
    - Consistent flat low → swamp/water (heuristic, unreliable)
    - Otherwise → field
    """
    if not elevation_points:
        return [build_segment(0.0, total_distance_m, "field")]

    segments: list[TerrainSegment] = []
    d = 0.0
    while d < total_distance_m:
        end = min(d + segment_size_m, total_distance_m)
        elev_start = _elev_at(elevation_points, d)
        elev_end = _elev_at(elevation_points, end)
        mean_elev = (elev_start + elev_end) / 2.0
        delta = abs(elev_end - elev_start)
        run = end - d
        angle_deg = math.degrees(math.atan2(delta, run)) if run > 0 else 0.0

        if angle_deg > 15.0:
            st = "rock"
        else:
            st = "field"

        segments.append(build_segment(d, end, st, mean_elev))
        d = end

    return segments


# ---------------------------------------------------------------------------
# Profile analysis
# ---------------------------------------------------------------------------


def analyse_terrain_profile(
    segments: list[TerrainSegment],
    elevation_points: list[tuple[float, float]],
) -> dict:
    """Return a summary of terrain properties along the shot path.

    Returns dict with:
      valley_depth_m, max_uphill_m, dominant_surface,
      has_water, has_forest, has_rock, ricochet_risk_zones
    """
    if not elevation_points:
        return {}

    elevations = [e for _, e in elevation_points]
    start_e = elevations[0]
    end_e = elevations[-1]
    baseline = [
        start_e + (end_e - start_e) * i / (len(elevations) - 1)
        for i in range(len(elevations))
    ]
    below_baseline = [b - e for b, e in zip(baseline, elevations)]
    valley_depth = max(below_baseline) if below_baseline else 0.0

    surfaces = [s.surface_type for s in segments]
    lengths = [s.end_m - s.start_m for s in segments]
    total = sum(lengths) or 1.0
    surface_share: dict[str, float] = {}
    for st, seg_len in zip(surfaces, lengths):
        surface_share[st] = surface_share.get(st, 0.0) + seg_len / total

    dominant = max(surface_share, key=surface_share.get) if surface_share else "field"

    ricochet_zones = [(s.start_m, s.end_m) for s in segments if s.ricochet_risk]

    return {
        "valley_depth_m": valley_depth,
        "max_uphill_m": max(elevations) - elevations[0],
        "dominant_surface": dominant,
        "surface_share": surface_share,
        "has_water": surface_share.get("water", 0.0) > 0,
        "has_forest": surface_share.get("forest", 0.0) > 0,
        "has_rock": surface_share.get("rock", 0.0) > 0,
        "ricochet_risk_zones": ricochet_zones,
    }


def build_terrain_profile_from_segments(
    segments: list[TerrainSegment],
    elevation_points: list[tuple[float, float]],
    source: str = "estimated",
) -> TerrainProfile:
    """Wrap segments and elevation points into a TerrainProfile."""
    elevations = [e for _, e in elevation_points]
    if len(elevations) >= 2:
        baseline_end = elevations[-1]
        baseline_start = elevations[0]
        below = [
            (
                baseline_start
                + (baseline_end - baseline_start) * i / (len(elevations) - 1)
            )
            - e
            for i, e in enumerate(elevations)
        ]
        valley_depth = max(below) if below else None
    else:
        valley_depth = None

    clearances = [max(0.0, 5.0 - abs(e - elevations[0])) for e in elevations]
    min_clearance = min(clearances) if clearances else None

    return TerrainProfile(
        segments=segments,
        elevation_points=elevation_points,
        min_clearance_m=min_clearance,
        valley_depth_m=valley_depth,
        source=source,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _elev_at(points: list[tuple[float, float]], dist: float) -> float:
    """Interpolate elevation at given distance."""
    if not points:
        return 0.0
    if dist <= points[0][0]:
        return points[0][1]
    if dist >= points[-1][0]:
        return points[-1][1]
    for i in range(len(points) - 1):
        d0, e0 = points[i]
        d1, e1 = points[i + 1]
        if d0 <= dist <= d1:
            frac = (dist - d0) / (d1 - d0) if d1 != d0 else 0.0
            return e0 + frac * (e1 - e0)
    return points[-1][1]
