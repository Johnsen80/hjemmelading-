"""
Real-time Ballistics Simulator - Interactive visualization like Gordon's Reloading Tool
Shows pressure curves, velocity curves, and barrel time with live updates
"""

import numpy as np
import pyqtgraph as pg
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
from pyqtgraph import mkPen

from src.database.database import get_database
from src.modules.ballistics_engine import get_ballistics_engine


class BallisticsSimulator(QWidget):
    """
    Interactive ballistics simulator with real-time graphs
    Similar to Gordon's Reloading Tool but integrated with database
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
        title = QLabel("🔬 Real-Time Ballistics Simulator", self)
        title.setStyleSheet(
            "font-size: 18pt; font-weight: bold; color: #2c3e50; padding: 10px;"
        )
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
        self.tabs.addTab(self.pressure_tab, "📈 Pressure Curve")

        # Tab 2: Velocity Curve
        self.velocity_tab = self.create_velocity_tab()
        self.tabs.addTab(self.velocity_tab, "🚀 Velocity Curve")

        # Tab 3: Combined View
        self.combined_tab = self.create_combined_tab()
        self.tabs.addTab(self.combined_tab, "📊 Combined Analysis")

        # Tab 4: Barrel Harmonics (future)
        self.harmonics_tab = self.create_harmonics_tab()
        self.tabs.addTab(self.harmonics_tab, "🎵 Barrel Harmonics")

        layout.addWidget(self.tabs)

        # Stats Display
        stats_group = self.create_stats_panel()
        layout.addWidget(stats_group)

        self.setLayout(layout)

    def create_selection_panel(self):
        """Create component selection panel"""
        group = QGroupBox("🎯 Load Components", self)
        layout = QHBoxLayout()

        # Rifle selection
        rifle_layout = QFormLayout()
        self.rifle_combo = QComboBox(group)
        self.rifle_combo.currentIndexChanged.connect(self.on_rifle_changed)
        rifle_layout.addRow("Rifle:", self.rifle_combo)
        layout.addLayout(rifle_layout)

        # Bullet selection
        bullet_layout = QFormLayout()
        self.bullet_combo = QComboBox(group)
        self.bullet_combo.currentIndexChanged.connect(self.update_simulation)
        bullet_layout.addRow("Bullet:", self.bullet_combo)
        layout.addLayout(bullet_layout)

        # Powder selection
        powder_layout = QFormLayout()
        self.powder_combo = QComboBox(group)
        self.powder_combo.currentIndexChanged.connect(self.update_simulation)
        powder_layout.addRow("Powder:", self.powder_combo)
        layout.addLayout(powder_layout)

        # COAL input
        coal_layout = QFormLayout()
        self.coal_spin = QDoubleSpinBox(group)
        self.coal_spin.setRange(30.0, 100.0)
        self.coal_spin.setValue(70.0)
        self.coal_spin.setDecimals(2)
        self.coal_spin.setSuffix(" mm")
        self.coal_spin.valueChanged.connect(self.on_coal_changed)
        coal_layout.addRow("COAL:", self.coal_spin)
        layout.addLayout(coal_layout)

        group.setLayout(layout)

        # Load initial data
        self.load_rifles()
        self.load_bullets()
        self.load_powders()

        return group

    def create_slider_panel(self):
        """Create charge weight slider"""
        group = QGroupBox("⚖️ Charge Weight Control", self)
        layout = QVBoxLayout()

        # Slider with value display
        slider_row = QHBoxLayout()

        self.charge_label = QLabel(f"{self.current_charge:.1f} gr", group)
        self.charge_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; color: #27ae60;"
        )
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
        limits_row.addWidget(QLabel("20.0 gr", group))
        limits_row.addStretch()
        limits_row.addWidget(QLabel("60.0 gr", group))
        layout.addLayout(limits_row)

        group.setLayout(layout)
        return group

    def create_pressure_tab(self):
        """Create pressure curve graph"""
        widget = QWidget(self)
        layout = QVBoxLayout()

        # PyQtGraph plot widget
        self.pressure_plot = pg.PlotWidget(widget)
        self.pressure_plot.setBackground("w")
        self.pressure_plot.setLabel("left", "Pressure", units="PSI")
        self.pressure_plot.setLabel("bottom", "Time", units="ms")
        self.pressure_plot.setTitle("Chamber Pressure vs Time", color="k", size="12pt")
        self.pressure_plot.addLegend()

        # Add max pressure line
        self.pressure_max_line = pg.InfiniteLine(
            pos=62000,
            angle=0,
            pen=pg.mkPen("r", width=2, style=Qt.PenStyle.DashLine),
            label="SAAMI Max",
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
        self.velocity_plot.setLabel("left", "Velocity", units="fps")
        self.velocity_plot.setLabel("bottom", "Barrel Position", units="inches")
        self.velocity_plot.setTitle("Bullet Velocity in Barrel", color="k", size="12pt")
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
        self.comparison_plot.setLabel("left", "Pressure", units="PSI")
        self.comparison_plot.setLabel("bottom", "Charge Weight", units="grains")
        self.comparison_plot.setTitle(
            "Pressure vs Charge Weight", color="k", size="12pt"
        )

        # Add SAAMI max line
        self.comp_max_line = pg.InfiniteLine(
            pos=62000,
            angle=0,
            pen=pg.mkPen("r", width=2, style=Qt.PenStyle.DashLine),
            label="SAAMI Max",
        )
        self.comparison_plot.addItem(self.comp_max_line)

        layout.addWidget(self.comparison_plot)

        # Velocity vs charge
        self.velocity_comparison_plot = pg.PlotWidget(widget)
        self.velocity_comparison_plot.setBackground("w")
        self.velocity_comparison_plot.setLabel("left", "Velocity", units="fps")
        self.velocity_comparison_plot.setLabel(
            "bottom", "Charge Weight", units="grains"
        )
        self.velocity_comparison_plot.setTitle(
            "Velocity vs Charge Weight", color="k", size="12pt"
        )

        layout.addWidget(self.velocity_comparison_plot)

        widget.setLayout(layout)
        return widget

    def create_harmonics_tab(self):
        """Create barrel harmonics visualization (placeholder)"""
        widget = QWidget(self)
        layout = QVBoxLayout()

        self.harmonics_plot = pg.PlotWidget(widget)
        self.harmonics_plot.setBackground("w")
        self.harmonics_plot.setLabel("left", "Muzzle Displacement", units="mm")
        self.harmonics_plot.setLabel("bottom", "Time", units="ms")
        self.harmonics_plot.setTitle(
            "Barrel Harmonics & Bullet Exit Timing", color="k", size="12pt"
        )

        info = QLabel(
            "🎵 Barrel harmonics visualization\n\n"
            "Shows optimal charge windows (OCW nodes) where bullet exits at same point in vibration cycle.\n"
            "Coming soon: Animated barrel vibration with bullet travel.",
            widget,
        )
        info.setStyleSheet("padding: 20px; color: #7f8c8d;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.harmonics_plot)
        layout.addWidget(info)

        widget.setLayout(layout)
        return widget

    def create_stats_panel(self):
        """Create statistics display panel"""
        group = QGroupBox("📊 Current Load Statistics", self)
        layout = QHBoxLayout()

        self.stat_pressure = QLabel("Pressure: -- PSI", group)
        self.stat_velocity = QLabel("Velocity: -- fps", group)
        self.stat_energy = QLabel("Energy: -- ft-lbs", group)
        self.stat_barrel_time = QLabel("Barrel Time: -- ms", group)
        self.stat_safety = QLabel("Safety Margin: --%", group)

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
        self.rifle_combo.addItem("-- Select Rifle --", None)
        for rifle in rifles:
            self.rifle_combo.addItem(f"{rifle['name']} ({rifle['caliber']})", rifle)

    def load_bullets(self):
        """Load bullets from database"""
        bullets = self.db.execute_query("SELECT * FROM bullets ORDER BY weight_grains")
        self.bullet_combo.clear()
        self.bullet_combo.addItem("-- Select Bullet --", None)
        for bullet in bullets:
            self.bullet_combo.addItem(
                f"{bullet['weight_grains']}gr {bullet['manufacturer']} {bullet['name']}",
                bullet,
            )

    def load_powders(self):
        """Load powders from database"""
        powders = self.db.execute_query("SELECT * FROM powder ORDER BY name")
        self.powder_combo.clear()
        self.powder_combo.addItem("-- Select Powder --", None)
        for powder in powders:
            self.powder_combo.addItem(
                f"{powder['manufacturer']} {powder['name']}", powder
            )

    def on_rifle_changed(self, index):
        """Handle rifle selection change"""
        rifle = self.rifle_combo.currentData()
        if rifle:
            self.rifle_id = rifle["id"]
            # Update COAL if rifle has max_coal
            if rifle.get("max_coal_magazine_mm"):
                self.coal_spin.setValue(rifle["max_coal_magazine_mm"] - 2.0)
        self.update_simulation()

    def on_slider_changed(self, value):
        """Handle slider value change"""
        self.current_charge = value / 10.0  # Convert to grains
        self.charge_label.setText(f"{self.current_charge:.1f} gr")
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

        # Calculate ballistics
        result = self.engine.calculate_load(
            rifle["id"],
            bullet["id"],
            powder["id"],
            self.current_charge,
            self.coal_mm,
            self.cbto_mm,
        )

        if "error" in result:
            return

        # Update pressure curve
        self.update_pressure_graph(result)

        # Update velocity curve
        self.update_velocity_graph(result)

        # Update combined analysis
        self.update_combined_graphs(rifle, bullet, powder)

        # Update statistics
        self.update_stats(result)

        # Update SAAMI max line for caliber
        max_pressure = result["max_pressure_psi"]
        self.pressure_max_line.setValue(max_pressure)
        self.comp_max_line.setValue(max_pressure)

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
            name="Chamber Pressure",
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
            name=f'Peak: {result["peak_pressure_psi"]:.0f} PSI',
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
            name="Bullet Velocity",
        )

        # Mark muzzle velocity
        self.velocity_plot.plot(
            [positions[-1]],
            [velocities[-1]],
            pen=None,
            symbol="o",
            symbolSize=12,
            symbolBrush="#e74c3c",
            name=f'Muzzle: {result["muzzle_velocity_fps"]:.0f} fps',
        )

    def update_combined_graphs(self, rifle, bullet, powder):
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
            name="Peak Pressure",
        )

        # Mark current charge
        current_idx = min(
            range(len(charges)), key=lambda i: abs(charges[i] - self.current_charge)
        )
        self.comparison_plot.plot(
            [charges[current_idx]],
            [pressures[current_idx]],
            pen=None,
            symbol="o",
            symbolSize=15,
            symbolBrush="#f39c12",
            name=f"Current: {self.current_charge:.1f} gr",
        )

        # Plot velocity vs charge
        self.velocity_comparison_plot.plot(
            charges,
            velocities,
            pen=mkPen(color="#27ae60", width=3),
            name="Muzzle Velocity",
        )

        # Mark current charge
        self.velocity_comparison_plot.plot(
            [charges[current_idx]],
            [velocities[current_idx]],
            pen=None,
            symbol="o",
            symbolSize=15,
            symbolBrush="#f39c12",
            name=f"Current: {self.current_charge:.1f} gr",
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

        self.stat_pressure.setText(f"Pressure: {result['peak_pressure_psi']:.0f} PSI")
        self.stat_velocity.setText(f"Velocity: {result['muzzle_velocity_fps']:.0f} fps")
        self.stat_energy.setText(f"Energy: {result['energy_ft_lbs']:.0f} ft-lbs")
        self.stat_barrel_time.setText(f"Barrel Time: {result['barrel_time_ms']:.2f} ms")
        self.stat_safety.setText(f"{safety_emoji} Safety: {safety_margin:.1f}%")
        self.stat_safety.setStyleSheet(
            f"font-size: 11pt; padding: 5px; color: {safety_color}; font-weight: bold;"
        )


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    simulator = BallisticsSimulator()
    simulator.setWindowTitle("Ballistics Simulator - Reloading Workshop Manager")
    simulator.resize(1400, 900)
    simulator.show()
    sys.exit(app.exec())
