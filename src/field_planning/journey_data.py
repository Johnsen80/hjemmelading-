"""Bullet journey visualization data — pure computation, no Qt dependency.

BulletJourneyData is built from trajectory points and terrain profile.
It pre-computes all series needed by the rendering widget so the widget
only does drawing, never physics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple

from .models import EnrichedTrajectoryPoint, TerrainProfile

# ---------------------------------------------------------------------------
# Color scheme (used by both the widget and PDF export)
# ---------------------------------------------------------------------------

PHASE_COLORS = {
    "supersonic": "#27ae60",  # green
    "transonic": "#e67e22",  # orange
    "subsonic": "#e74c3c",  # red
}

SG_COLORS = {
    "stable": "#27ae60",
    "marginal": "#e67e22",
    "unstable": "#e74c3c",
    "unknown": "#95a5a6",
}

TERRAIN_COLORS = {
    "rock": "#7f8c8d",
    "water": "#3498db",
    "swamp": "#1abc9c",
    "forest": "#27ae60",
    "snow": "#ecf0f1",
    "field": "#f0d06a",
    "urban": "#e74c3c",
    "unknown": "#bdc3c7",
}


# ---------------------------------------------------------------------------
# Segment — colored region between two X values
# ---------------------------------------------------------------------------


class ColoredRegion(NamedTuple):
    x_start: float
    x_end: float
    color: str
    alpha: float = 0.18
    label: str = ""


# ---------------------------------------------------------------------------
# Marker — annotated point on the trajectory
# ---------------------------------------------------------------------------


@dataclass
class TrajectoryMarker:
    distance_m: float
    label: str
    color: str = "#2c3e50"
    symbol: str = "v"  # pyqtgraph symbol: 'v', 'o', 's', 't', '+'


# ---------------------------------------------------------------------------
# Main data container
# ---------------------------------------------------------------------------


@dataclass
class BulletJourneyData:
    """All pre-computed series for the bullet journey visualization.

    Build via BulletJourneyData.from_trajectory().
    """

    # X axis (shared by all panels)
    distances_m: list[float]

    # Side view — elevation
    drop_cm: list[float]  # negative = below zero line
    terrain_elevations_m: list[float]  # terrain height along path (relative to shooter)
    bullet_height_above_ground_m: list[float]

    # Top view — lateral
    total_windage_cm: list[float]  # combined drift
    wind_drift_cm: list[float]
    spin_drift_cm: list[float]
    coriolis_cm: list[float]

    # Graph 1 — velocity
    velocity_fps: list[float]
    mach: list[float]

    # Graph 2 — energy
    energy_joules: list[float]

    # Graph 3 — stability
    stability_sg: list[float]

    # Colored phase regions (for all panels)
    phase_regions: list[ColoredRegion]

    # Markers
    markers: list[TrajectoryMarker]

    # Metadata
    zero_distance_m: float
    subsonic_distance_m: float | None
    transonic_distance_m: float | None
    max_distance_m: float
    max_drop_cm: float
    max_windage_cm: float
    min_sg: float
    min_energy_j: float

    # Summary text lines (shown in widget header)
    summary_lines: list[str] = field(default_factory=list)

    @classmethod
    def from_trajectory(
        cls,
        points: list[EnrichedTrajectoryPoint],
        terrain: TerrainProfile | None = None,
        zero_distance_m: float = 100.0,
        ethical_energy_j: float | None = None,
    ) -> "BulletJourneyData":
        if not points:
            return cls._empty()

        distances = [p.distance_m for p in points]
        drop = [p.drop_cm for p in points]
        windage = [p.windage_cm for p in points]
        wind_drift = [p.wind_drift_cm for p in points]
        spin_drift = [p.spin_drift_cm for p in points]
        coriolis = [p.coriolis_cm for p in points]
        velocity = [p.velocity_fps for p in points]
        mach_vals = [p.mach for p in points]
        energy = [p.energy_joules for p in points]
        sg = [p.stability_sg for p in points]

        # Terrain heights relative to shooter (0 = shooter altitude)
        if terrain and terrain.elevation_points:
            terrain_h = _interpolate_terrain(distances, terrain.elevation_points)
        else:
            terrain_h = [0.0] * len(distances)

        # Bullet clearance above ground (approximation without full 3D path)
        bullet_clearance = [max(0.0, -d / 100.0 + t) for d, t in zip(drop, terrain_h)]

        phase_regions = _build_phase_regions(points)
        markers = _build_markers(points, zero_distance_m, ethical_energy_j)

        subsonic_m = next((p.distance_m for p in points if p.phase == "subsonic"), None)
        transonic_m = next(
            (p.distance_m for p in points if p.phase == "transonic"), None
        )

        summary = _build_summary(points, zero_distance_m, subsonic_m, ethical_energy_j)

        return cls(
            distances_m=distances,
            drop_cm=drop,
            terrain_elevations_m=terrain_h,
            bullet_height_above_ground_m=bullet_clearance,
            total_windage_cm=windage,
            wind_drift_cm=wind_drift,
            spin_drift_cm=spin_drift,
            coriolis_cm=coriolis,
            velocity_fps=velocity,
            mach=mach_vals,
            energy_joules=energy,
            stability_sg=sg,
            phase_regions=phase_regions,
            markers=markers,
            zero_distance_m=zero_distance_m,
            subsonic_distance_m=subsonic_m,
            transonic_distance_m=transonic_m,
            max_distance_m=max(distances) if distances else 0.0,
            max_drop_cm=max(abs(d) for d in drop) if drop else 0.0,
            max_windage_cm=max(abs(w) for w in windage) if windage else 0.0,
            min_sg=min(sg) if sg else 0.0,
            min_energy_j=min(energy) if energy else 0.0,
            summary_lines=summary,
        )

    @classmethod
    def _empty(cls) -> "BulletJourneyData":
        return cls(
            distances_m=[],
            drop_cm=[],
            terrain_elevations_m=[],
            bullet_height_above_ground_m=[],
            total_windage_cm=[],
            wind_drift_cm=[],
            spin_drift_cm=[],
            coriolis_cm=[],
            velocity_fps=[],
            mach=[],
            energy_joules=[],
            stability_sg=[],
            phase_regions=[],
            markers=[],
            zero_distance_m=100.0,
            subsonic_distance_m=None,
            transonic_distance_m=None,
            max_distance_m=0.0,
            max_drop_cm=0.0,
            max_windage_cm=0.0,
            min_sg=0.0,
            min_energy_j=0.0,
        )

    def point_at(self, distance_m: float) -> dict:
        """Return all values at the closest distance to `distance_m`."""
        if not self.distances_m:
            return {}
        idx = min(
            range(len(self.distances_m)),
            key=lambda i: abs(self.distances_m[i] - distance_m),
        )
        return {
            "distance_m": self.distances_m[idx],
            "drop_cm": self.drop_cm[idx],
            "windage_cm": self.total_windage_cm[idx],
            "velocity_fps": self.velocity_fps[idx],
            "mach": self.mach[idx],
            "energy_joules": self.energy_joules[idx],
            "stability_sg": self.stability_sg[idx],
            "wind_drift_cm": self.wind_drift_cm[idx],
            "spin_drift_cm": self.spin_drift_cm[idx],
            "coriolis_cm": self.coriolis_cm[idx],
        }

    def phase_at(self, distance_m: float) -> str:
        """Return phase string at the closest distance."""
        if not self.distances_m:
            return "unknown"
        idx = min(
            range(len(self.distances_m)),
            key=lambda i: abs(self.distances_m[i] - distance_m),
        )
        m = self.mach[idx]
        if m >= 1.2:
            return "supersonic"
        if m >= 0.9:
            return "transonic"
        return "subsonic"

    @property
    def has_transonic_zone(self) -> bool:
        return self.transonic_distance_m is not None

    @property
    def has_subsonic_zone(self) -> bool:
        return self.subsonic_distance_m is not None

    @property
    def sg_warning(self) -> bool:
        """True if any point has Sg < 1.4 (marginal or unstable)."""
        return any(s < 1.4 for s in self.stability_sg if s > 0)


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------


def _build_phase_regions(points: list[EnrichedTrajectoryPoint]) -> list[ColoredRegion]:
    """Build contiguous colored regions by phase."""
    if not points:
        return []
    regions: list[ColoredRegion] = []
    current_phase = points[0].phase
    start = points[0].distance_m

    for pt in points[1:]:
        if pt.phase != current_phase:
            regions.append(
                ColoredRegion(
                    x_start=start,
                    x_end=pt.distance_m,
                    color=PHASE_COLORS.get(current_phase, "#95a5a6"),
                    label=current_phase,
                )
            )
            current_phase = pt.phase
            start = pt.distance_m

    regions.append(
        ColoredRegion(
            x_start=start,
            x_end=points[-1].distance_m,
            color=PHASE_COLORS.get(current_phase, "#95a5a6"),
            label=current_phase,
        )
    )
    return regions


def _build_markers(
    points: list[EnrichedTrajectoryPoint],
    zero_distance_m: float,
    ethical_energy_j: float | None,
) -> list[TrajectoryMarker]:
    markers: list[TrajectoryMarker] = []

    # Zero crossing
    markers.append(
        TrajectoryMarker(
            distance_m=zero_distance_m,
            label="Zero",
            color="#2c3e50",
            symbol="o",
        )
    )

    # Transonic boundary
    for i, pt in enumerate(points):
        if pt.phase == "transonic" and (i == 0 or points[i - 1].phase == "supersonic"):
            markers.append(
                TrajectoryMarker(
                    distance_m=pt.distance_m,
                    label=f"Transonic\n{pt.distance_m:.0f}m",
                    color=PHASE_COLORS["transonic"],
                    symbol="v",
                )
            )
            break

    # Subsonic boundary
    for i, pt in enumerate(points):
        if pt.phase == "subsonic" and (i == 0 or points[i - 1].phase != "subsonic"):
            markers.append(
                TrajectoryMarker(
                    distance_m=pt.distance_m,
                    label=f"Subsonic\n{pt.distance_m:.0f}m",
                    color=PHASE_COLORS["subsonic"],
                    symbol="v",
                )
            )
            break

    # Ethical kill limit
    if ethical_energy_j is not None:
        last_ok = None
        for pt in points:
            if pt.energy_joules >= ethical_energy_j:
                last_ok = pt
        if last_ok is not None:
            markers.append(
                TrajectoryMarker(
                    distance_m=last_ok.distance_m,
                    label=f"Max etisk\n{last_ok.distance_m:.0f}m",
                    color="#8e44ad",
                    symbol="s",
                )
            )

    return markers


def _interpolate_terrain(
    distances_m: list[float],
    terrain_points: list[tuple[float, float]],
) -> list[float]:
    """Interpolate terrain elevation at each trajectory distance."""
    if not terrain_points:
        return [0.0] * len(distances_m)

    t_dist = [d for d, _ in terrain_points]
    t_elev = [e for _, e in terrain_points]
    # Normalize to shooter altitude
    base = t_elev[0] if t_elev else 0.0

    result = []
    for d in distances_m:
        if d <= t_dist[0]:
            result.append(t_elev[0] - base)
            continue
        if d >= t_dist[-1]:
            result.append(t_elev[-1] - base)
            continue
        for i in range(len(t_dist) - 1):
            if t_dist[i] <= d <= t_dist[i + 1]:
                frac = (d - t_dist[i]) / (t_dist[i + 1] - t_dist[i])
                interp = t_elev[i] + frac * (t_elev[i + 1] - t_elev[i])
                result.append(interp - base)
                break
        else:
            result.append(0.0)
    return result


def _build_summary(
    points: list[EnrichedTrajectoryPoint],
    zero_m: float,
    subsonic_m: float | None,
    ethical_j: float | None,
) -> list[str]:
    if not points:
        return []
    last = points[-1]
    lines = [
        f"Maks avstand: {last.distance_m:.0f}m",
        f"Slutthastig.: {last.velocity_mps:.0f} m/s  (Mach {last.mach:.2f})",
        f"Slutt-energi: {last.energy_joules:.0f} J",
    ]
    if subsonic_m is not None:
        lines.append(f"Subsonic ved: {subsonic_m:.0f}m")
    if ethical_j is not None:
        last_ok = next(
            (p for p in reversed(points) if p.energy_joules >= ethical_j), None
        )
        if last_ok:
            lines.append(f"Etisk grense: {last_ok.distance_m:.0f}m ({ethical_j:.0f}J)")
    min_sg = min((p.stability_sg for p in points if p.stability_sg > 0), default=0.0)
    if min_sg > 0:
        lines.append(f"Min Sg: {min_sg:.2f}")
    return lines
