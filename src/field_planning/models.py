"""Data models for the field planning module.

All types are plain dataclasses — no Qt, no DB, no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Atmospheric modelling
# ---------------------------------------------------------------------------


@dataclass
class AtmosphereLayer:
    """One horizontal slice of the atmosphere at a given altitude."""

    altitude_m: float
    temperature_c: float
    pressure_hpa: float
    humidity_pct: float
    wind_speed_mps: float
    wind_dir_deg: float  # meteorological: 0=N, 90=E, 180=S, 270=W
    density_ratio: float  # relative to ICAO standard (1.225 kg/m³)
    density_altitude_m: float
    source: str = "surface"  # "surface", "radiosonde", "lapse_rate", "manual"


@dataclass
class LayeredAtmosphere:
    """Atmosphere split into altitude layers for multi-segment trajectory solving."""

    layers: list[AtmosphereLayer]  # sorted by altitude_m ascending, min 1 layer
    inversion_detected: bool = False
    inversion_altitude_m: float | None = None
    thermal_risk_level: str = "low"  # "low", "moderate", "high"
    surface_type_primary: str = "field"  # dominant terrain type under shot path
    katabatic_risk: bool = False  # cold air pooling in valley likely
    warnings: list[str] = field(default_factory=list)

    @property
    def surface_layer(self) -> AtmosphereLayer:
        return self.layers[0]

    def layer_at_altitude(self, altitude_m: float) -> AtmosphereLayer:
        """Return the layer that covers the given altitude."""
        for layer in reversed(self.layers):
            if altitude_m >= layer.altitude_m:
                return layer
        return self.layers[0]


# ---------------------------------------------------------------------------
# Terrain
# ---------------------------------------------------------------------------


@dataclass
class TerrainSegment:
    """A segment of terrain along the shot path with surface classification."""

    start_m: float  # distance along shot path
    end_m: float
    surface_type: str  # "rock", "water", "swamp", "forest", "snow",
    #                                 "field", "urban", "unknown"
    elevation_m: float  # mean terrain height in segment (ASL)
    thermal_contribution: str = "none"  # "none", "low", "moderate", "high"
    wind_factor: float = 1.0  # multiplier on reported wind
    ricochet_risk: bool = False


@dataclass
class TerrainProfile:
    """Complete terrain profile along the shot path."""

    segments: list[TerrainSegment]
    elevation_points: list[tuple[float, float]]  # [(distance_m, elevation_m), ...]
    min_clearance_m: float | None = None  # minimum bullet-to-ground clearance
    valley_depth_m: float | None = None  # max below shooter/target line
    source: str = "unknown"  # "kartverket", "srtm", "estimated"


# ---------------------------------------------------------------------------
# Enriched trajectory
# ---------------------------------------------------------------------------


@dataclass
class EnrichedTrajectoryPoint:
    """Full physical state of the bullet at one point along its trajectory."""

    distance_m: float
    time_s: float
    velocity_fps: float
    velocity_mps: float
    mach: float
    phase: str  # "supersonic", "transonic", "subsonic"
    drop_cm: float
    drop_moa: float
    drop_mrad: float
    windage_cm: float  # combined: wind + spin drift + Coriolis
    windage_moa: float
    windage_mrad: float
    energy_ftlbs: float
    energy_joules: float
    stability_sg: float  # gyroscopic stability factor (Miller formula)
    stability_status: str  # "stable", "marginal", "unstable"
    # Spatial context
    bullet_altitude_m: float  # ASL
    height_above_ground_m: float  # clearance above terrain
    atmosphere_layer: AtmosphereLayer | None = None
    terrain_segment: TerrainSegment | None = None
    # Breakdown of windage components (cm)
    wind_drift_cm: float = 0.0
    spin_drift_cm: float = 0.0
    coriolis_cm: float = 0.0
    eotvos_cm: float = 0.0


@dataclass
class ClickCorrection:
    """Elevation and windage correction in multiple units."""

    elevation_moa: float
    elevation_mrad: float
    elevation_clicks: float
    windage_moa: float
    windage_mrad: float
    windage_clicks: float
    clicks_per_unit: float = 4.0  # clicks per MOA (default Nightforce/Schmidt)
    unit: str = "moa"  # "moa" or "mrad"


# ---------------------------------------------------------------------------
# Monte Carlo dispersion
# ---------------------------------------------------------------------------


@dataclass
class MonteCarloResult:
    """Dispersion analysis from Monte Carlo simulation."""

    distance_m: float
    iterations: int
    cep50_cm: float  # 50% probability radius
    cep90_cm: float
    cep99_cm: float
    vertical_sd_cm: float
    horizontal_sd_cm: float
    mv_contribution_pct: float  # fraction of variance from MV SD
    bc_contribution_pct: float  # fraction of variance from BC uncertainty
    wind_contribution_pct: float  # fraction of variance from wind uncertainty
    impact_points: list[tuple[float, float]] = field(default_factory=list)
    # (x_cm, y_cm) offsets — sampled for scatter plot, not all 10k


@dataclass
class MonteCarloProfile:
    """CEP at multiple distances from a single Monte Carlo run."""

    results: list[MonteCarloResult]  # one per distance step
    mv_sd_fps: float
    bc_uncertainty_pct: float
    wind_uncertainty_mps: float


# ---------------------------------------------------------------------------
# DOPE
# ---------------------------------------------------------------------------


@dataclass
class DopeRow:
    """One row in a DOPE card."""

    distance_m: float
    correction: ClickCorrection
    velocity_mps: float
    energy_joules: float
    time_of_flight_s: float
    phase: str
    cep90_cm: float | None = None  # populated if Monte Carlo was run
    wind_10mps_moa: float | None = None  # full-value 10 m/s wind correction


@dataclass
class DopeCard:
    """Complete DOPE card for one weapon/ammo/conditions combination."""

    rifle_name: str
    ammo_label: str
    zero_distance_m: float
    conditions_summary: str  # "8°C, 1012 hPa, 62% RH, DA 423m"
    rows: list[DopeRow]
    learned_bc: float
    learned_mv_fps: float
    learned_mv_sd_fps: float
    bc_source: str  # "measured_drops", "chrono_backsolve", "profile", "library"
    mv_source: str  # "chrono_sessions", "manual"
    generated_at: str  # ISO datetime string
    atmosphere_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Weapon + ammo context (assembled from DB + learning)
# ---------------------------------------------------------------------------


@dataclass
class WeaponBallisticProfile:
    """Everything needed to build BallisticInput, extracted from DB and learning data."""

    rifle_id: int
    rifle_name: str
    caliber: str
    barrel_configuration_id: str | None
    twist_rate_in: float  # inches per turn
    twist_direction: str  # "RIGHT" or "LEFT"
    sight_height_mm: float
    zero_distance_m: float

    # Learned values (highest quality available)
    learned_mv_fps: float
    learned_mv_sd_fps: float
    learned_bc: float
    learned_bc_type: str  # "G7", "G1", "CDM"
    bc_source: str
    mv_source: str

    # MV temperature curve [(temp_c, mv_fps), ...]
    mv_temperature_curve: list[tuple[float, float]] = field(default_factory=list)

    # Cold bore correction (signed, in MOA — positive = above zero)
    cold_bore_offset_moa: float = 0.0
    cold_bore_sample_count: int = 0

    # Bullet physical data (for Sg calculation)
    bullet_diameter_mm: float = 0.0
    bullet_length_mm: float = 0.0
    bullet_mass_gr: float = 0.0

    # Ammo identification
    ammo_profile_id: int | None = None
    ammo_label: str = ""
    lot_label: str = ""

    def mv_at_temperature(self, temperature_c: float) -> float:
        """Interpolate MV from learned temperature curve. Falls back to learned_mv_fps."""
        if len(self.mv_temperature_curve) < 2:
            return self.learned_mv_fps
        temps = [t for t, _ in self.mv_temperature_curve]
        mvs = [m for _, m in self.mv_temperature_curve]
        if temperature_c <= temps[0]:
            return mvs[0]
        if temperature_c >= temps[-1]:
            return mvs[-1]
        for i in range(len(temps) - 1):
            if temps[i] <= temperature_c <= temps[i + 1]:
                frac = (temperature_c - temps[i]) / (temps[i + 1] - temps[i])
                return mvs[i] + frac * (mvs[i + 1] - mvs[i])
        return self.learned_mv_fps


# ---------------------------------------------------------------------------
# Geographic / field session
# ---------------------------------------------------------------------------


@dataclass
class GeoPoint:
    """Geographic point with optional altitude."""

    lat: float
    lon: float
    alt_m: float | None = None
    label: str = ""


@dataclass
class FieldTarget:
    """A single target on a shooting range or hunting area."""

    position: GeoPoint
    label: str = ""
    distance_m: float = 0.0  # computed from shooter position
    slant_distance_m: float = 0.0  # actual slant range
    inclination_deg: float = 0.0  # positive = uphill
    bearing_deg: float = 0.0
    correction: ClickCorrection | None = None
    trajectory: list[EnrichedTrajectoryPoint] | None = None
    monte_carlo: MonteCarloResult | None = None


@dataclass
class FieldSession:
    """Active field session — weapon, conditions, map state."""

    profile: WeaponBallisticProfile
    shooter_position: GeoPoint | None = None
    atmosphere: LayeredAtmosphere | None = None
    terrain_profile: TerrainProfile | None = None
    targets: list[FieldTarget] = field(default_factory=list)
    latitude_deg: float = 60.0  # for Coriolis (Norway default)
    azimuth_deg: float = 0.0  # shooting direction
    clicks_per_moa: float = 4.0
    scope_unit: str = "moa"  # "moa" or "mrad"
    extra: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Hunting
# ---------------------------------------------------------------------------

GAME_MIN_ENERGY_J: dict[str, float] = {
    "moose": 2500.0,
    "deer": 1500.0,
    "roe_deer": 800.0,
    "reindeer": 1500.0,
    "boar": 1500.0,
    "small_game": 200.0,
}


@dataclass
class HuntingPost:
    position: GeoPoint
    game_type: str = "deer"
    max_ethical_range_m: float = 300.0  # will be computed from energy threshold

    @property
    def min_kill_energy_j(self) -> float:
        return GAME_MIN_ENERGY_J.get(self.game_type, 1500.0)


@dataclass
class HuntingSector:
    post: HuntingPost
    polygon: list[GeoPoint] = field(default_factory=list)
    known_points: list[GeoPoint] = field(default_factory=list)


@dataclass
class BackstopAnalysis:
    """Safety analysis for one aim point from a hunting post."""

    point: GeoPoint
    bearing_deg: float
    slant_range_m: float
    # Bullet trajectory beyond target
    ground_intersection_m: (
        float | None
    )  # where bullet hits ground (None = no hit found)
    max_ordinate_m: float  # highest point of trajectory above ground
    bullet_energy_at_ground_j: float
    bullet_velocity_at_ground_mps: float
    is_subsonic_at_ground: bool
    # Habitation
    nearest_habitation_m: float | None
    nearest_habitation_bearing_deg: float | None
    nearest_habitation_label: str = ""
    # Verdict
    verdict: str = "unknown"  # "safe", "caution", "unsafe"
    verdict_reason: str = ""
    color: str = "gray"  # "green", "orange", "red", "gray"


# ---------------------------------------------------------------------------
# Range session (shooting range with multiple targets)
# ---------------------------------------------------------------------------


@dataclass
class RangeTarget:
    """One target on a shooting range, defined by slant range and inclination."""

    label: str
    slant_range_m: float  # actual line-of-sight distance
    inclination_deg: float = 0.0  # positive = uphill, negative = downhill
    bearing_deg: float = 0.0  # compass bearing from shooter to target
    notes: str = ""

    @property
    def horizontal_range_m(self) -> float:
        import math

        return self.slant_range_m * math.cos(math.radians(self.inclination_deg))


@dataclass
class TargetSolution:
    """Complete click solution for one target, with slant and wind corrections."""

    target: RangeTarget
    correction: ClickCorrection
    # Reference wind column (10 m/s full-value crosswind)
    wind_10mps_elevation_moa: float  # usually 0 — wind has no vertical component
    wind_10mps_windage_moa: float
    # Trajectory state at target
    velocity_mps: float
    energy_joules: float
    time_of_flight_s: float
    mach: float
    phase: str  # "supersonic", "transonic", "subsonic"
    stability_sg: float
    # Slant correction info
    slant_correction_applied: bool = True
    inclination_correction_factor: float = 1.0  # cos(inclination_deg)
    # Optional Monte Carlo
    cep90_cm: float | None = None
    cep50_cm: float | None = None


@dataclass
class RangeSession:
    """A shooting range session with multiple targets."""

    profile: WeaponBallisticProfile
    atmosphere: LayeredAtmosphere | None = None
    targets: list[RangeTarget] = field(default_factory=list)
    clicks_per_moa: float = 4.0
    scope_unit: str = "moa"  # "moa" or "mrad"
    latitude_deg: float = 60.0


@dataclass
class HuntingFieldAnalysis:
    """Complete analysis for a hunting session."""

    session: FieldSession
    post: HuntingPost
    sector: HuntingSector
    backstop_map: dict[str, BackstopAnalysis] = field(default_factory=dict)
    # key = f"{point.lat:.6f},{point.lon:.6f}"
    ethical_range_m: float = 0.0  # max range where energy >= min_kill_energy_j
    subsonic_range_m: float = 0.0  # range where bullet goes subsonic
