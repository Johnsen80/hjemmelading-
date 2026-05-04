"""
Real-time Ballistics Simulator.

Shows pressure curves, velocity curves, and barrel time with live updates.
"""

import json
import logging

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    import pyqtgraph as pg
    from pyqtgraph import mkPen
except Exception:
    pg = None

    class _PlotWidgetFallback(QWidget):
        def setBackground(self, *args, **kwargs):
            pass

        def setLabel(self, *args, **kwargs):
            pass

        def setTitle(self, *args, **kwargs):
            pass

        def addLegend(self, *args, **kwargs):
            pass

        def addItem(self, *args, **kwargs):
            pass

        def clear(self):
            pass

        def plot(self, *args, **kwargs):
            return None

        def addLine(self, *args, **kwargs):
            return None

    class _InfiniteLineFallback:
        def __init__(self, *args, **kwargs):
            self.value = kwargs.get("pos")

        def setValue(self, value):
            self.value = value

    class _PyqtgraphFallback:
        PlotWidget = _PlotWidgetFallback
        InfiniteLine = _InfiniteLineFallback

        @staticmethod
        def mkPen(*args, **kwargs):
            return None

    pg = _PyqtgraphFallback()

    def mkPen(*args, **kwargs):
        return None


from ..database.database import get_database
from ..utils.i18n import tr
from ..utils.rifle_harmonics import calculate_harmonics_profile
from .ballistics_engine import get_ballistics_engine

_logger = logging.getLogger(__name__)


class BallisticsSimulator(QWidget):
    """
    Interactive ballistics simulator with real-time graphs
    Integrated with the app database and workflow tools
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = get_ballistics_engine()
        self.db = get_database()

        # Current simulation state
        self.rifle_id = None
        self.bullet_id = None
        self.powder_id = None
        self.current_charge = 42.0
        self.coal_mm = 70.0
        self.cbto_mm = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()

        # Title
        title = QLabel(tr("ballistics_sim_title"), self)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)

        # Component Selection
        selection_group = self.create_selection_panel()
        layout.addWidget(selection_group)

        # Charge Weight Slider (main control)
        slider_group = self.create_slider_panel()
        layout.addWidget(slider_group)

        # Tabs for different graphs
        self.tabs = QTabWidget(self)

        # Tab 1: Pressure Curve
        self.pressure_tab = self.create_pressure_tab()
        self.tabs.addTab(self.pressure_tab, tr("ballistics_pressure_curve_tab"))

        # Tab 2: Velocity Curve
        self.velocity_tab = self.create_velocity_tab()
        self.tabs.addTab(self.velocity_tab, tr("ballistics_velocity_curve_tab"))

        # Tab 3: Combined View
        self.combined_tab = self.create_combined_tab()
        self.tabs.addTab(self.combined_tab, tr("ballistics_combined_analysis_tab"))

        # Tab 4: Barrel Harmonics (future)
        self.harmonics_tab = self.create_harmonics_tab()
        self.tabs.addTab(self.harmonics_tab, tr("ballistics_barrel_harmonics_tab"))

        layout.addWidget(self.tabs)

        # Stats Display
        stats_group = self.create_stats_panel()
        layout.addWidget(stats_group)

        self.setLayout(layout)

    def create_selection_panel(self):
        """Create component selection panel"""
        group = QGroupBox(tr("ballistics_load_components"), self)
        layout = QHBoxLayout()

        # Rifle selection
        rifle_layout = QFormLayout()
        self.rifle_combo = QComboBox(group)
        self.rifle_combo.currentIndexChanged.connect(self.on_rifle_changed)
        rifle_layout.addRow(tr("ballistics_rifle_label"), self.rifle_combo)
        self.barrel_combo = QComboBox(group)
        self.barrel_combo.currentIndexChanged.connect(self.on_barrel_changed)
        rifle_layout.addRow(tr("ballistics_barrel_label"), self.barrel_combo)
        layout.addLayout(rifle_layout)

        # Bullet selection
        bullet_layout = QFormLayout()
        self.bullet_combo = QComboBox(group)
        self.bullet_combo.currentIndexChanged.connect(self.update_simulation)
        bullet_layout.addRow(tr("ballistics_bullet_label"), self.bullet_combo)
        layout.addLayout(bullet_layout)

        # Powder selection
        powder_layout = QFormLayout()
        self.powder_combo = QComboBox(group)
        self.powder_combo.currentIndexChanged.connect(self.update_simulation)
        powder_layout.addRow(tr("ballistics_powder_label"), self.powder_combo)
        layout.addLayout(powder_layout)

        # COAL input
        coal_layout = QFormLayout()
        self.coal_spin = QDoubleSpinBox(group)
        self.coal_spin.setRange(30.0, 100.0)
        self.coal_spin.setValue(70.0)
        self.coal_spin.setDecimals(2)
        self.coal_spin.setSuffix(" mm")
        self.coal_spin.valueChanged.connect(self.on_coal_changed)
        coal_layout.addRow(tr("ballistics_coal_label"), self.coal_spin)
        layout.addLayout(coal_layout)

        group.setLayout(layout)

        # Load initial data
        self.load_rifles()
        self.load_bullets()
        self.load_powders()

        return group

    def create_slider_panel(self):
        """Create charge weight slider"""
        group = QGroupBox(tr("ballistics_charge_weight_control"), self)
        layout = QVBoxLayout()

        # Slider with value display
        slider_row = QHBoxLayout()

        self.charge_label = QLabel(self._format_charge_label(self.current_charge), group)
        self.charge_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #27ae60;")
        slider_row.addWidget(self.charge_label)

        self.charge_slider = QSlider(Qt.Orientation.Horizontal, group)
        self.charge_slider.setMinimum(200)  # 20.0 gr
        self.charge_slider.setMaximum(600)  # 60.0 gr
        self.charge_slider.setValue(420)  # 42.0 gr
        self.charge_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.charge_slider.setTickInterval(50)
        self.charge_slider.valueChanged.connect(self.on_slider_changed)
        slider_row.addWidget(self.charge_slider, 1)

        layout.addLayout(slider_row)

        # Min/Max labels
        limits_row = QHBoxLayout()
        limits_row.addWidget(QLabel(self._format_charge_label(20.0), group))
        limits_row.addStretch()
        limits_row.addWidget(QLabel(self._format_charge_label(60.0), group))
        layout.addLayout(limits_row)

        group.setLayout(layout)
        return group

    @staticmethod
    def _format_charge_label(charge_grains: float) -> str:
        return tr("ballistics_charge_weight_value", charge=f"{charge_grains:.1f}")

    def create_pressure_tab(self):
        """Create pressure curve graph"""
        widget = QWidget(self)
        layout = QVBoxLayout()

        # PyQtGraph plot widget
        self.pressure_plot = pg.PlotWidget(widget)
        self.pressure_plot.setBackground("w")
        self.pressure_plot.setLabel("left", tr("ballistics_pressure_label"), units="PSI")
        self.pressure_plot.setLabel("bottom", tr("ballistics_time_label"), units="ms")
        self.pressure_plot.setTitle(tr("ballistics_chamber_pressure_vs_time"), color="k", size="12pt")
        self.pressure_plot.addLegend()

        # Add max pressure line
        self.pressure_max_line = pg.InfiniteLine(
            pos=62000,
            angle=0,
            pen=pg.mkPen("r", width=2, style=Qt.PenStyle.DashLine),
            label=tr("ballistics_saami_max"),
        )
        self.pressure_plot.addItem(self.pressure_max_line)

        layout.addWidget(self.pressure_plot)
        widget.setLayout(layout)
        return widget

    def create_velocity_tab(self):
        """Create velocity curve graph"""
        widget = QWidget(self)
        layout = QVBoxLayout()

        self.velocity_plot = pg.PlotWidget(widget)
        self.velocity_plot.setBackground("w")
        self.velocity_plot.setLabel("left", tr("ballistics_velocity_label"), units="fps")
        self.velocity_plot.setLabel("bottom", tr("ballistics_barrel_position_label"), units="inches")
        self.velocity_plot.setTitle(tr("ballistics_bullet_velocity_in_barrel"), color="k", size="12pt")
        self.velocity_plot.addLegend()

        layout.addWidget(self.velocity_plot)
        widget.setLayout(layout)
        return widget

    def create_combined_tab(self):
        """Create combined analysis view"""
        widget = QWidget(self)
        layout = QVBoxLayout()

        # Multi-charge comparison
        self.comparison_plot = pg.PlotWidget(widget)
        self.comparison_plot.setBackground("w")
        self.comparison_plot.setLabel("left", tr("ballistics_pressure_label"), units="PSI")
        self.comparison_plot.setLabel("bottom", tr("ballistics_charge_weight_label"), units="grains")
        self.comparison_plot.setTitle(tr("ballistics_pressure_vs_charge_weight"), color="k", size="12pt")

        # Add SAAMI max line
        self.comp_max_line = pg.InfiniteLine(
            pos=62000,
            angle=0,
            pen=pg.mkPen("r", width=2, style=Qt.PenStyle.DashLine),
            label=tr("ballistics_saami_max"),
        )
        self.comparison_plot.addItem(self.comp_max_line)

        layout.addWidget(self.comparison_plot)

        # Velocity vs charge
        self.velocity_comparison_plot = pg.PlotWidget(widget)
        self.velocity_comparison_plot.setBackground("w")
        self.velocity_comparison_plot.setLabel("left", tr("ballistics_velocity_label"), units="fps")
        self.velocity_comparison_plot.setLabel("bottom", tr("ballistics_charge_weight_label"), units="grains")
        self.velocity_comparison_plot.setTitle(tr("ballistics_velocity_vs_charge_weight"), color="k", size="12pt")

        layout.addWidget(self.velocity_comparison_plot)

        widget.setLayout(layout)
        return widget

    def create_harmonics_tab(self):
        """Create barrel harmonics visualization (placeholder)"""
        widget = QWidget(self)
        layout = QVBoxLayout()

        self.harmonics_plot = pg.PlotWidget(widget)
        self.harmonics_plot.setBackground("w")
        self.harmonics_plot.setLabel("left", tr("ballistics_muzzle_displacement_label"), units="mm")
        self.harmonics_plot.setLabel("bottom", tr("ballistics_time_label"), units="ms")
        self.harmonics_plot.setTitle(tr("ballistics_barrel_harmonics_timing"), color="k", size="12pt")

        layout.addWidget(self.harmonics_plot)
        self.harmonics_summary_label = QLabel(tr("ballistics_select_rifle_for_harmonics"))
        self.harmonics_summary_label.setStyleSheet("padding: 8px; color: #2c3e50; font-weight: bold;")
        layout.addWidget(self.harmonics_summary_label)

        # Hent harmonics-data fra rifleprofil/barrel
        harmonics = getattr(self, "harmonics", None) or {}
        node_bands = []
        harmonic_score = None
        if harmonics:
            node_bands = harmonics.get("node_bands", [])
            harmonic_score = harmonics.get("harmonic_score", None)

        # Visualiser node_bands
        if node_bands:
            for node in node_bands:
                start = float(node.get("start_mm", 0))
                end = float(node.get("end_mm", 0))
                robustness = float(node.get("robustness", 0))
                self.harmonics_plot.addLine(x=start, pen=(0, 255, 0, int(robustness * 255)))
                self.harmonics_plot.addLine(x=end, pen=(0, 255, 0, int(robustness * 255)))

        # Vis harmonic_score
        score_label = QLabel(
            tr(
                "ballistics_harmonic_score",
                score=harmonic_score if harmonic_score is not None else "N/A",
            )
        )
        score_label.setStyleSheet("padding: 10px; color: #2c3e50; font-weight: bold;")
        layout.addWidget(score_label)
        self.harmonics_score_label = score_label

        info = QLabel(tr("ballistics_harmonics_info"), widget)
        info.setStyleSheet("padding: 20px; color: #7f8c8d;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        widget.setLayout(layout)
        self._refresh_harmonics_tab()
        return widget

    def _refresh_harmonics_tab(self):
        """Refresh harmonics labels from the current rifle profile."""
        if not hasattr(self, "harmonics_summary_label"):
            return

        harmonics = getattr(self, "harmonics", None) or {}
        if not harmonics:
            self.harmonics_summary_label.setText(tr("ballistics_select_rifle_for_harmonics"))
            if hasattr(self, "harmonics_score_label"):
                self.harmonics_score_label.setText(tr("ballistics_harmonic_score", score=tr("common_na")))
            return

        barrel_name = harmonics.get("barrel_name") or tr("ballistics_standard_barrel")
        attachment = harmonics.get("barrel_attachment_type") or tr("common_unknown")
        profile = harmonics.get("barrel_profile") or tr("common_unknown")
        stability = harmonics.get("stability_tier") or tr("common_unknown")
        confidence = harmonics.get("harmonics_confidence") or tr("common_unknown")
        self.harmonics_summary_label.setText(
            tr(
                "ballistics_harmonics_summary",
                barrel=barrel_name,
                attachment=attachment,
                profile=profile,
                frequency=harmonics.get("estimated_frequency_hz", 0),
                stability=stability,
                confidence=confidence,
            )
        )
        if hasattr(self, "harmonics_score_label"):
            missing = harmonics.get("missing_required_inputs", [])
            score = harmonics.get("harmonic_score", tr("common_na"))
            if missing:
                self.harmonics_score_label.setText(
                    tr(
                        "ballistics_harmonic_score_missing",
                        score=score,
                        missing=", ".join(missing[:2]),
                    )
                )
                return
            self.harmonics_score_label.setText(tr("ballistics_harmonic_score", score=score))

    def create_stats_panel(self):
        """Create statistics display panel"""
        group = QGroupBox(tr("ballistics_current_load_statistics"), self)
        layout = QHBoxLayout()

        self.stat_pressure = QLabel(tr("ballistics_pressure_stat_placeholder"), group)
        self.stat_velocity = QLabel(tr("ballistics_velocity_stat_placeholder"), group)
        self.stat_energy = QLabel(tr("ballistics_energy_stat_placeholder"), group)
        self.stat_barrel_time = QLabel(tr("ballistics_barrel_time_stat_placeholder"), group)
        self.stat_safety = QLabel(tr("ballistics_safety_margin_stat_placeholder"), group)

        for label in [
            self.stat_pressure,
            self.stat_velocity,
            self.stat_energy,
            self.stat_barrel_time,
            self.stat_safety,
        ]:
            label.setStyleSheet("font-size: 11pt; padding: 5px; color: #2c3e50;")
            layout.addWidget(label)

        group.setLayout(layout)
        return group

    def load_rifles(self):
        """Load rifles from database"""
        rifles = self.db.execute_query("SELECT * FROM rifles ORDER BY name")
        self.rifle_combo.clear()
        self.rifle_combo.addItem(tr("ballistics_select_rifle"), None)
        for rifle in rifles:
            self.rifle_combo.addItem(f"{rifle['name']} ({rifle['caliber']})", rifle)

    def load_bullets(self, caliber: str = ""):
        """Load bullets from database, optionally filtered by caliber."""
        import re as _re

        bullets = None
        if caliber:
            # Exact match
            bullets = self.db.execute_query(
                "SELECT * FROM bullets WHERE caliber = ? ORDER BY weight_grains",
                (caliber,),
            )
            # Numeric-prefix fallback: handles "308 Winchester" → ".308"
            if not bullets:
                m = _re.match(r"\.?(\d+\.?\d*)", caliber.strip())
                if m:
                    diam = m.group(1)
                    bullets = self.db.execute_query(
                        "SELECT * FROM bullets WHERE caliber LIKE ? OR caliber LIKE ? OR caliber = ?"
                        " ORDER BY weight_grains",
                        (f"{diam}%", f".{diam}%", caliber),
                    )
        if not bullets:
            bullets = self.db.execute_query("SELECT * FROM bullets ORDER BY weight_grains")
        self.bullet_combo.clear()
        self.bullet_combo.addItem(tr("ballistics_select_bullet"), None)
        for bullet in bullets or []:
            self.bullet_combo.addItem(
                f"{bullet['weight_grains']}gr {bullet['manufacturer']} {bullet['name']}",
                bullet,
            )

    def load_powders(self):
        """Load powders from database"""
        powders = self.db.execute_query("SELECT * FROM powder ORDER BY name")
        self.powder_combo.clear()
        self.powder_combo.addItem(tr("ballistics_select_powder"), None)
        for powder in powders:
            self.powder_combo.addItem(f"{powder['manufacturer']} {powder['name']}", powder)

    def _load_rifle_profile_details(self, rifle_id):
        """Load stored rifle profile details for the selected rifle."""
        if not rifle_id:
            return {}
        try:
            rows = self.db.execute_query(
                "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
                (rifle_id,),
            )
            if rows and rows[0].get("profile_json"):
                details = json.loads(rows[0]["profile_json"])
                return details if isinstance(details, dict) else {}
        except Exception:
            pass
        return {}

    def populate_barrel_options(self, rifle_id, details=None):
        """Populate barrel/løp combo from rifle profile details."""
        self.barrel_combo.blockSignals(True)
        self.barrel_combo.clear()

        details = details or self._load_rifle_profile_details(rifle_id)
        barrels = details.get("barrels", []) if isinstance(details, dict) else []
        active_barrel_id = details.get("active_barrel_id") if isinstance(details, dict) else None

        if isinstance(barrels, list) and barrels:
            active_index = 0
            for index, barrel in enumerate(barrels):
                if not isinstance(barrel, dict):
                    continue
                name = barrel.get("name") or f"Pipe {index + 1}"
                caliber = barrel.get("caliber") or ""
                label = name if not caliber else f"{name} ({caliber})"
                self.barrel_combo.addItem(label, barrel)
                if active_barrel_id and str(barrel.get("id")) == str(active_barrel_id):
                    active_index = self.barrel_combo.count() - 1
            self.barrel_combo.setCurrentIndex(active_index)
        else:
            self.barrel_combo.addItem(tr("ballistics_standard_barrel"), None)

        self.barrel_combo.blockSignals(False)

    def _selected_barrel(self):
        """Return selected barrel profile from the combo box."""
        barrel = self.barrel_combo.currentData()
        return barrel if isinstance(barrel, dict) else {}

    def _current_harmonics_details(self, rifle, details):
        """Build harmonics input using the currently selected barrel/løp."""
        merged = dict(details or {})
        barrel = self._selected_barrel()
        if barrel:
            merged["selected_barrel_id"] = barrel.get("id")
            merged["selected_barrel_name"] = barrel.get("name")
        merged.setdefault("rifle_id", rifle.get("id"))
        merged.setdefault("rifle_name", rifle.get("name"))
        return merged

    def on_rifle_changed(self, index):
        """Handle rifle selection change"""
        try:
            self._on_rifle_changed_impl(index)
        except Exception:
            import traceback as _tb

            try:
                _logger.critical("on_rifle_changed crashed: %s", _tb.format_exc())
            except Exception:
                pass
            raise

    def _on_rifle_changed_impl(self, index):
        rifle = self.rifle_combo.currentData()
        if rifle:
            self.rifle_id = rifle["id"]
            details = self._load_rifle_profile_details(self.rifle_id)
            self.populate_barrel_options(self.rifle_id, details)
            self.harmonics = calculate_harmonics_profile(rifle, self._current_harmonics_details(rifle, details))
            # Update COAL if rifle has max_coal
            if rifle.get("max_coal_magazine_mm"):
                self.coal_spin.setValue(rifle["max_coal_magazine_mm"] - 2.0)
            # Filter bullets by rifle caliber
            self.load_bullets(caliber=str(rifle.get("caliber") or ""))
        else:
            self.barrel_combo.clear()
            self.barrel_combo.addItem(tr("ballistics_standard_barrel"), None)
            self.harmonics = {}
            self.load_bullets()
        self._refresh_harmonics_tab()
        self.update_simulation()

    def on_barrel_changed(self, index):
        """Refresh harmonics and simulation when selected barrel changes."""
        try:
            self._on_barrel_changed_impl(index)
        except Exception:
            import traceback as _tb

            try:
                _logger.critical("on_barrel_changed crashed: %s", _tb.format_exc())
            except Exception:
                pass
            raise

    def _on_barrel_changed_impl(self, index):
        rifle = self.rifle_combo.currentData()
        if not rifle:
            self.harmonics = {}
            self._refresh_harmonics_tab()
            return

        details = self._load_rifle_profile_details(rifle["id"])
        self.harmonics = calculate_harmonics_profile(rifle, self._current_harmonics_details(rifle, details))
        self._refresh_harmonics_tab()
        self.update_simulation()

    def on_slider_changed(self, value):
        """Handle slider value change"""
        self.current_charge = value / 10.0  # Convert to grains
        self.charge_label.setText(self._format_charge_label(self.current_charge))
        self.update_simulation()

    def on_coal_changed(self, value):
        """Handle COAL change"""
        self.coal_mm = value
        self.update_simulation()

    def update_simulation(self):
        """Update all graphs with current parameters"""
        # Check if we have all required data
        rifle = self.rifle_combo.currentData()
        bullet = self.bullet_combo.currentData()
        powder = self.powder_combo.currentData()

        if not rifle or not bullet or not powder:
            return

        barrel = self._selected_barrel()

        # Calculate ballistics
        try:
            result = self.engine.calculate_load(
                rifle["id"],
                bullet["id"],
                powder["id"],
                self.current_charge,
                self.coal_mm,
                self.cbto_mm,
                barrel_id=barrel.get("id"),
            )
        except Exception:
            import traceback as _tb

            _logger.warning("update_simulation engine crash: %s", _tb.format_exc())
            return

        if "error" in result:
            return

        try:
            # Update pressure curve
            self.update_pressure_graph(result)

            # Update velocity curve
            self.update_velocity_graph(result)

            # Update combined analysis
            self.update_combined_graphs(rifle, bullet, powder, barrel)

            # Update statistics
            self.update_stats(result)

            # Update SAAMI max line for caliber
            max_pressure = result.get("max_pressure_psi") or 0
            self.pressure_max_line.setValue(max_pressure)
            self.comp_max_line.setValue(max_pressure)
        except Exception:
            import traceback as _tb

            _logger.warning("update_simulation graph update failed: %s", _tb.format_exc())

    def update_pressure_graph(self, result):
        """Update pressure vs time graph"""
        self.pressure_plot.clear()

        # Re-add max line
        self.pressure_plot.addItem(self.pressure_max_line)

        # Plot pressure curve
        times = [p[0] for p in result["pressure_curve"]]
        pressures = [p[1] for p in result["pressure_curve"]]

        self.pressure_plot.plot(
            times,
            pressures,
            pen=mkPen(color="#3498db", width=3),
            name=tr("ballistics_chamber_pressure_name"),
        )

        # Mark peak pressure
        peak_idx = pressures.index(max(pressures))
        self.pressure_plot.plot(
            [times[peak_idx]],
            [pressures[peak_idx]],
            pen=None,
            symbol="o",
            symbolSize=12,
            symbolBrush="#e74c3c",
            name=tr(
                "ballistics_peak_point_name",
                value=f'{result["peak_pressure_psi"]:.0f}',
            ),
        )

    def update_velocity_graph(self, result):
        """Update velocity vs barrel position graph"""
        self.velocity_plot.clear()

        # Plot velocity curve
        positions = [v[0] for v in result["velocity_curve"]]
        velocities = [v[1] for v in result["velocity_curve"]]

        self.velocity_plot.plot(
            positions,
            velocities,
            pen=mkPen(color="#27ae60", width=3),
            name=tr("ballistics_bullet_velocity_name"),
        )

        # Mark muzzle velocity
        self.velocity_plot.plot(
            [positions[-1]],
            [velocities[-1]],
            pen=None,
            symbol="o",
            symbolSize=12,
            symbolBrush="#e74c3c",
            name=tr(
                "ballistics_muzzle_point_name",
                value=f'{result["muzzle_velocity_fps"]:.0f}',
            ),
        )

    def update_combined_graphs(self, rifle, bullet, powder, barrel=None):
        """Update combined analysis graphs with multiple charges"""
        self.comparison_plot.clear()
        self.velocity_comparison_plot.clear()

        # Re-add max line
        self.comparison_plot.addItem(self.comp_max_line)

        # Calculate for range of charges
        charges = np.linspace(20.0, 55.0, 30)
        pressures = []
        velocities = []

        for charge in charges:
            result = self.engine.calculate_load(
                rifle["id"],
                bullet["id"],
                powder["id"],
                charge,
                self.coal_mm,
                self.cbto_mm,
                barrel_id=(barrel or {}).get("id"),
            )
            if "error" not in result:
                pressures.append(result["peak_pressure_psi"])
                velocities.append(result["muzzle_velocity_fps"])
            else:
                pressures.append(0)
                velocities.append(0)

        # Plot pressure vs charge
        self.comparison_plot.plot(
            charges,
            pressures,
            pen=mkPen(color="#e74c3c", width=3),
            name=tr("ballistics_peak_pressure_name"),
        )

        # Mark current charge
        current_idx = min(range(len(charges)), key=lambda i: abs(charges[i] - self.current_charge))
        self.comparison_plot.plot(
            [charges[current_idx]],
            [pressures[current_idx]],
            pen=None,
            symbol="o",
            symbolSize=15,
            symbolBrush="#f39c12",
            name=tr("ballistics_current_charge_name", charge=f"{self.current_charge:.1f}"),
        )

        # Plot velocity vs charge
        self.velocity_comparison_plot.plot(
            charges,
            velocities,
            pen=mkPen(color="#27ae60", width=3),
            name=tr("ballistics_muzzle_velocity_name"),
        )

        # Mark current charge
        self.velocity_comparison_plot.plot(
            [charges[current_idx]],
            [velocities[current_idx]],
            pen=None,
            symbol="o",
            symbolSize=15,
            symbolBrush="#f39c12",
            name=tr("ballistics_current_charge_name", charge=f"{self.current_charge:.1f}"),
        )

    def update_stats(self, result):
        """Update statistics display"""
        # Color code safety margin
        safety_margin = result["safety_margin_percent"]
        if safety_margin < 10:
            safety_color = "#e74c3c"
            safety_emoji = "🔴"
        elif safety_margin < 20:
            safety_color = "#e67e22"
            safety_emoji = "🟠"
        else:
            safety_color = "#27ae60"
            safety_emoji = "🟢"

        self.stat_pressure.setText(tr("ballistics_pressure_stat", value=f"{result['peak_pressure_psi']:.0f}"))
        self.stat_velocity.setText(tr("ballistics_velocity_stat", value=f"{result['muzzle_velocity_fps']:.0f}"))
        self.stat_energy.setText(tr("ballistics_energy_stat", value=f"{result['energy_ft_lbs']:.0f}"))
        self.stat_barrel_time.setText(tr("ballistics_barrel_time_stat", value=f"{result['barrel_time_ms']:.2f}"))
        self.stat_safety.setText(
            tr(
                "ballistics_safety_stat",
                emoji=safety_emoji,
                value=f"{safety_margin:.1f}",
            )
        )
        self.stat_safety.setStyleSheet(f"font-size: 11pt; padding: 5px; color: {safety_color}; font-weight: bold;")


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    simulator = BallisticsSimulator()
    simulator.setWindowTitle(tr("ballistics_window_title"))
    simulator.resize(1400, 900)
    simulator.show()
    sys.exit(app.exec())
