"""BulletJourneyWidget — 3-panel visualization of a bullet's flight from muzzle to target.

Panel 1 (side view):  Drop curve + terrain profile, colored by ballistic phase.
Panel 2 (top view):   Lateral drift (wind + spin + Coriolis), colored by phase.
Panel 3 (graphs):     4 synchronized sub-graphs: velocity/Mach, energy, Sg stability.

A vertical cursor links all panels on mouse hover.
Import-safe: falls back to a placeholder QLabel if pyqtgraph is unavailable.
"""

from __future__ import annotations

try:
    import pyqtgraph as pg
    from pyqtgraph import mkBrush, mkPen

    _HAS_PG = True
except Exception:
    pg = None  # type: ignore[assignment]
    _HAS_PG = False

from ..field_planning.journey_data import (
    PHASE_COLORS,
    SG_COLORS,
    BulletJourneyData,
    ColoredRegion,
)
from ..qt_compat import (
    QColor,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSplitter,
    Qt,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Public widget
# ---------------------------------------------------------------------------


class BulletJourneyWidget(QWidget):
    """Full bullet-journey visualization.

    Usage::

        widget = BulletJourneyWidget(parent)
        widget.set_data(journey_data, ethical_energy_j=1500.0)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: BulletJourneyData | None = None
        self._ethical_energy_j: float | None = None
        self._cursor_lines: list = []
        self._init_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_data(
        self,
        data: BulletJourneyData,
        ethical_energy_j: float | None = None,
    ) -> None:
        self._data = data
        self._ethical_energy_j = ethical_energy_j
        self._refresh()

    def clear(self) -> None:
        self._data = None
        if _HAS_PG:
            for plot in self._all_plots():
                plot.clear()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Summary header
        self._summary_label = QLabel("")
        self._summary_label.setWordWrap(True)
        self._summary_label.setStyleSheet(
            "font-size: 11px; color: #2c3e50; padding: 4px 8px;"
            "background: #ecf0f1; border-radius: 3px;"
        )
        layout.addWidget(self._summary_label)

        if not _HAS_PG:
            layout.addWidget(
                QLabel(
                    "pyqtgraph ikke tilgjengelig — installer med: pip install pyqtgraph"
                )
            )
            return

        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "#2c3e50")

        # Splitter: side/top on top, graphs below
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(splitter)

        # Row 1: side view + top view side by side
        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(4)

        self._side_plot = self._make_plot(
            "Side-visning", "Avstand (m)", "Høyde / Fall (cm)"
        )
        self._top_plot = self._make_plot(
            "Topp-visning (drift)", "Avstand (m)", "Lateral drift (cm)"
        )

        top_layout.addWidget(self._side_plot)
        top_layout.addWidget(self._top_plot)
        splitter.addWidget(top_row)

        # Row 2: stacked graphs
        graphs_widget = QWidget()
        graphs_layout = QVBoxLayout(graphs_widget)
        graphs_layout.setContentsMargins(0, 0, 0, 0)
        graphs_layout.setSpacing(2)

        self._vel_plot = self._make_plot("", "Avstand (m)", "Hastighet (fps)")
        self._vel_plot.setMaximumHeight(120)
        self._energy_plot = self._make_plot("", "Avstand (m)", "Energi (J)")
        self._energy_plot.setMaximumHeight(120)
        self._sg_plot = self._make_plot("", "Avstand (m)", "Sg (stabilitet)")
        self._sg_plot.setMaximumHeight(100)

        for p in (self._vel_plot, self._energy_plot, self._sg_plot):
            graphs_layout.addWidget(p)

        splitter.addWidget(graphs_widget)
        splitter.setSizes([300, 250])

        # Link X axes
        self._top_plot.setXLink(self._side_plot)
        self._vel_plot.setXLink(self._side_plot)
        self._energy_plot.setXLink(self._side_plot)
        self._sg_plot.setXLink(self._side_plot)

        # Hover cursor
        self._side_plot.scene().sigMouseMoved.connect(self._on_mouse_moved)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        if not _HAS_PG or self._data is None:
            return
        d = self._data
        if not d.distances_m:
            return

        for plot in self._all_plots():
            plot.clear()

        # --- Phase regions (background) ---
        for plot in self._all_plots():
            for region in d.phase_regions:
                _add_region(plot, region)

        # --- Side view ---
        self._draw_terrain(d)
        self._draw_drop_curve(d)
        self._draw_zero_line(d)

        # --- Top view ---
        self._draw_drift(d)

        # --- Graphs ---
        self._draw_velocity(d)
        self._draw_energy(d)
        self._draw_sg(d)

        # --- Markers (vertical lines on side view) ---
        for marker in d.markers:
            line = pg.InfiniteLine(
                pos=marker.distance_m,
                angle=90,
                pen=mkPen(color=marker.color, width=1, style=Qt.PenStyle.DashLine),
                label=marker.label,
                labelOpts={
                    "color": marker.color,
                    "position": 0.95,
                    "fill": (255, 255, 255, 180),
                },
            )
            self._side_plot.addItem(line)

        # --- Summary ---
        self._summary_label.setText("   |   ".join(d.summary_lines))

    def _draw_terrain(self, d: BulletJourneyData) -> None:
        if all(h == 0.0 for h in d.terrain_elevations_m):
            # Draw flat ground line
            self._side_plot.addItem(
                pg.InfiniteLine(
                    pos=0.0,
                    angle=0,
                    pen=mkPen(color="#7f8c8d", width=2),
                )
            )
            return
        # Filled terrain
        xs = d.distances_m
        ys_terrain = [h * 100 for h in d.terrain_elevations_m]  # m → cm for same axis
        terrain_fill = pg.FillBetweenItem(
            pg.PlotDataItem(xs, ys_terrain),
            pg.PlotDataItem(xs, [min(ys_terrain) - 50] * len(xs)),
            brush=mkBrush(color=(139, 119, 101, 120)),
        )
        self._side_plot.addItem(terrain_fill)
        self._side_plot.plot(xs, ys_terrain, pen=mkPen(color="#7f8c8d", width=2))

    def _draw_drop_curve(self, d: BulletJourneyData) -> None:
        xs = d.distances_m

        # Draw colored segments by phase
        regions = d.phase_regions
        for region in regions:
            seg_xs = [x for x in xs if region.x_start <= x <= region.x_end]
            seg_ys = [
                d.drop_cm[i]
                for i, x in enumerate(xs)
                if region.x_start <= x <= region.x_end
            ]
            if seg_xs:
                self._side_plot.plot(
                    seg_xs,
                    seg_ys,
                    pen=mkPen(color=region.color, width=3),
                )

    def _draw_zero_line(self, d: BulletJourneyData) -> None:
        self._side_plot.addItem(
            pg.InfiniteLine(
                pos=0.0,
                angle=0,
                pen=mkPen(color="#95a5a6", width=1, style=Qt.PenStyle.DashLine),
            )
        )

    def _draw_drift(self, d: BulletJourneyData) -> None:
        xs = d.distances_m
        pen_total = mkPen(color="#2c3e50", width=3)
        pen_wind = mkPen(color="#3498db", width=1, style=Qt.PenStyle.DashLine)
        pen_spin = mkPen(color="#e74c3c", width=1, style=Qt.PenStyle.DotLine)
        pen_cor = mkPen(color="#9b59b6", width=1, style=Qt.PenStyle.DotLine)

        self._top_plot.plot(xs, d.total_windage_cm, pen=pen_total, name="Total")
        self._top_plot.plot(xs, d.wind_drift_cm, pen=pen_wind, name="Vind")
        self._top_plot.plot(xs, d.spin_drift_cm, pen=pen_spin, name="Spindrift")
        self._top_plot.plot(xs, d.coriolis_cm, pen=pen_cor, name="Coriolis")
        self._top_plot.addItem(
            pg.InfiniteLine(
                pos=0.0,
                angle=0,
                pen=mkPen(color="#95a5a6", width=1, style=Qt.PenStyle.DashLine),
            )
        )

    def _draw_velocity(self, d: BulletJourneyData) -> None:
        xs = d.distances_m
        self._vel_plot.plot(
            xs, d.velocity_fps, pen=mkPen(color="#2c3e50", width=2), name="fps"
        )
        # Mach 1.0 as fraction of fps — approximate using 1125 fps
        mach1_fps = 1125.0
        self._vel_plot.addItem(
            pg.InfiniteLine(
                pos=mach1_fps,
                angle=0,
                pen=mkPen(
                    color=PHASE_COLORS["transonic"], width=1, style=Qt.PenStyle.DashLine
                ),
                label="Mach 1",
                labelOpts={"color": PHASE_COLORS["transonic"], "position": 0.05},
            )
        )

    def _draw_energy(self, d: BulletJourneyData) -> None:
        xs = d.distances_m
        self._energy_plot.plot(xs, d.energy_joules, pen=mkPen(color="#e67e22", width=2))
        if self._ethical_energy_j is not None:
            self._energy_plot.addItem(
                pg.InfiniteLine(
                    pos=self._ethical_energy_j,
                    angle=0,
                    pen=mkPen(color="#8e44ad", width=1, style=Qt.PenStyle.DashLine),
                    label=f"Etisk grense {self._ethical_energy_j:.0f}J",
                    labelOpts={"color": "#8e44ad", "position": 0.05},
                )
            )

    def _draw_sg(self, d: BulletJourneyData) -> None:
        xs = d.distances_m
        ys = d.stability_sg

        # Danger band Sg < 1.0
        danger = pg.LinearRegionItem(
            [0.0, 1.0],
            orientation="horizontal",
            brush=mkBrush(231, 76, 60, 40),
            movable=False,
        )
        # Marginal band 1.0–1.4
        marginal = pg.LinearRegionItem(
            [1.0, 1.4],
            orientation="horizontal",
            brush=mkBrush(230, 126, 34, 30),
            movable=False,
        )
        self._sg_plot.addItem(danger)
        self._sg_plot.addItem(marginal)

        # Line colored by stability
        for i in range(len(xs) - 1):
            sg_val = ys[i]
            color = (
                SG_COLORS["unstable"]
                if sg_val < 1.0
                else SG_COLORS["marginal"] if sg_val < 1.4 else SG_COLORS["stable"]
            )
            self._sg_plot.plot(
                xs[i : i + 2],
                ys[i : i + 2],
                pen=mkPen(color=color, width=2),
            )

        self._sg_plot.addItem(
            pg.InfiniteLine(
                pos=1.4,
                angle=0,
                pen=mkPen(
                    color=SG_COLORS["stable"], width=1, style=Qt.PenStyle.DashLine
                ),
                label="Sg 1.4",
                labelOpts={"color": SG_COLORS["stable"], "position": 0.02},
            )
        )

    # ------------------------------------------------------------------
    # Cursor
    # ------------------------------------------------------------------

    def _on_mouse_moved(self, pos) -> None:
        if not _HAS_PG or self._data is None:
            return
        vb = self._side_plot.plotItem.vb
        if not self._side_plot.sceneBoundingRect().contains(pos):
            return
        mouse_point = vb.mapSceneToView(pos)
        x = mouse_point.x()

        # Remove old cursor lines
        for item in self._cursor_lines:
            try:
                for plot in self._all_plots():
                    plot.removeItem(item)
            except Exception:
                pass
        self._cursor_lines.clear()

        # Add new cursor lines
        for plot in self._all_plots():
            line = pg.InfiniteLine(
                pos=x,
                angle=90,
                pen=mkPen(color="#2c3e50", width=1, style=Qt.PenStyle.DotLine),
            )
            plot.addItem(line)
            self._cursor_lines.append(line)

        # Update summary with point data
        pt = self._data.point_at(x)
        if pt:
            self._summary_label.setText(
                f"@{pt['distance_m']:.0f}m  |  "
                f"V: {pt['velocity_fps']:.0f} fps (Mach {pt['mach']:.2f})  |  "
                f"Fall: {abs(pt['drop_cm']):.1f} cm  |  "
                f"Drift: {pt['windage_cm']:.1f} cm  |  "
                f"Energi: {pt['energy_joules']:.0f} J  |  "
                f"Sg: {pt['stability_sg']:.2f}"
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_plot(self, title: str, xlabel: str, ylabel: str) -> "pg.PlotWidget":
        plot = pg.PlotWidget(title=title)
        plot.setBackground("w")
        plot.setLabel("bottom", xlabel)
        plot.setLabel("left", ylabel)
        plot.showGrid(x=True, y=True, alpha=0.15)
        plot.addLegend(offset=(10, 10))
        return plot

    def _all_plots(self):
        if not _HAS_PG:
            return []
        plots = [
            self._side_plot,
            self._top_plot,
            self._vel_plot,
            self._energy_plot,
            self._sg_plot,
        ]
        return [p for p in plots if hasattr(self, "_side_plot")]


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------


def _add_region(plot: "pg.PlotWidget", region: ColoredRegion) -> None:
    c = QColor(region.color)
    c.setAlphaF(region.alpha)
    item = pg.LinearRegionItem(
        [region.x_start, region.x_end],
        brush=mkBrush(c),
        movable=False,
        pen=mkPen(None),
    )
    item.setZValue(-10)
    plot.addItem(item)
