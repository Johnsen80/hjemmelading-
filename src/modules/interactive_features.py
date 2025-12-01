"""
Interactive Graph Features
Hover tooltips, clickable data points, drag & drop
"""

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor
from typing import List, Dict, Tuple, Optional, Any, Callable


class InteractiveVelocityGraph(FigureCanvasQTAgg):
    """
    Enhanced velocity graph with interactive features:
    - Hover tooltips showing data details
    - Clickable data points
    - Drag to zoom
    - Right-click context menu
    """
    
    point_clicked = pyqtSignal(float, float, dict)  # charge, velocity, metadata
    
    def __init__(self, parent=None, width=8, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#ecf0f1')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        
        self.data_points = []  # List of (charge, velocity, metadata)
        self.annotations = []  # Store annotation objects
        
        # Enable hover events
        self.mpl_connect('motion_notify_event', self.on_hover)
        self.mpl_connect('button_press_event', self.on_click)
        
        self._setup_plot()
    
    def _setup_plot(self):
        """Setup initial plot"""
        self.ax.clear()
        self.ax.set_xlabel('Powder Charge (gr)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Velocity (fps)', fontsize=12, fontweight='bold')
        self.ax.set_title('📊 Interactive Velocity Graph', fontsize=14, fontweight='bold', pad=20)
        self.ax.grid(True, alpha=0.3, linestyle='--')
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.fig.tight_layout()
        self.draw()
    
    def add_point(self, charge: float, velocity: float, metadata: Optional[Dict] = None):
        """Add data point with metadata"""
        if metadata is None:
            metadata = {}
        
        metadata.setdefault('shot_number', len(self.data_points) + 1)
        metadata.setdefault('es', None)
        metadata.setdefault('sd', None)
        
        self.data_points.append((charge, velocity, metadata))
        self._update_plot()
    
    def _update_plot(self):
        """Update plot with interactive elements"""
        self.ax.clear()
        
        if not self.data_points:
            self._setup_plot()
            return
        
        charges = [p[0] for p in self.data_points]
        velocities = [p[1] for p in self.data_points]
        
        # Scatter plot with larger markers for easier clicking
        self.scatter = self.ax.scatter(
            charges, velocities, 
            s=150, c='#3498db',
            edgecolors='#2c3e50', linewidths=2, 
            zorder=3, picker=True, pickradius=10
        )
        
        # Trend line if enough points
        if len(charges) >= 3:
            z = np.polyfit(charges, velocities, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(charges), max(charges), 100)
            y_line = p(x_line)
            
            self.ax.plot(x_line, y_line, 'r--', linewidth=2, alpha=0.7,
                        label=f'Trend: {z[0]:.1f} fps/gr', zorder=2)
        
        # Node detection
        if len(charges) >= 5:
            self._detect_and_mark_nodes(charges, velocities)
        
        self.ax.set_xlabel('Powder Charge (gr)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Velocity (fps)', fontsize=12, fontweight='bold')
        self.ax.set_title('📊 Interactive Velocity Graph (Hover for details)', 
                         fontsize=14, fontweight='bold', pad=20)
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.legend(loc='upper left', framealpha=0.9)
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.fig.tight_layout()
        self.draw()
    
    def _detect_and_mark_nodes(self, charges, velocities):
        """Detect and mark pressure nodes"""
        vel_deltas = np.diff(velocities)
        threshold = np.mean(vel_deltas) * 0.5
        
        nodes = []
        for i in range(len(vel_deltas)):
            if vel_deltas[i] < threshold:
                nodes.append(i + 1)
        
        if nodes:
            node_charges = [charges[i] for i in nodes]
            node_vels = [velocities[i] for i in nodes]
            
            self.ax.scatter(node_charges, node_vels, s=300, facecolors='none',
                           edgecolors='#27ae60', linewidths=3, zorder=4,
                           label='⭐ Pressure Nodes')
    
    def on_hover(self, event):
        """Handle mouse hover"""
        if event.inaxes != self.ax:
            return
        
        # Find nearest data point
        if not self.data_points:
            return
        
        mouse_x, mouse_y = event.xdata, event.ydata
        if mouse_x is None or mouse_y is None:
            return
        
        # Find closest point
        min_dist = float('inf')
        closest_point = None
        
        for charge, velocity, metadata in self.data_points:
            # Normalize distances for fair comparison
            x_range = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
            y_range = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
            
            dx = (charge - mouse_x) / x_range
            dy = (velocity - mouse_y) / y_range
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist < min_dist:
                min_dist = dist
                closest_point = (charge, velocity, metadata)
        
        # Show tooltip if close enough
        if min_dist < 0.05:  # Within 5% of axis range
            self._show_tooltip(event, closest_point)
        else:
            self._hide_tooltip()
    
    def _show_tooltip(self, event, point_data):
        """Show tooltip for data point"""
        charge, velocity, metadata = point_data
        
        # Build tooltip text
        tooltip_lines = [
            f"<b>Shot #{metadata.get('shot_number', '?')}</b>",
            f"Charge: {charge:.1f} gr",
            f"Velocity: {velocity} fps"
        ]
        
        if metadata.get('es') is not None:
            tooltip_lines.append(f"ES: {metadata['es']:.0f} fps")
        
        if metadata.get('sd') is not None:
            tooltip_lines.append(f"SD: {metadata['sd']:.1f} fps")
        
        if metadata.get('group_size'):
            tooltip_lines.append(f"Group: {metadata['group_size']:.2f}\"")
        
        if metadata.get('notes'):
            tooltip_lines.append(f"<i>{metadata['notes']}</i>")
        
        tooltip_text = "<br>".join(tooltip_lines)
        
        # Show Qt tooltip at cursor
        QToolTip.showText(
            self.mapToGlobal(QPoint(int(event.x), int(event.y))),
            f"<div style='padding: 5px;'>{tooltip_text}</div>"
        )
    
    def _hide_tooltip(self):
        """Hide tooltip"""
        QToolTip.hideText()
    
    def on_click(self, event):
        """Handle mouse click on data point"""
        if event.inaxes != self.ax or event.button != 1:  # Left click only
            return
        
        if not self.data_points:
            return
        
        mouse_x, mouse_y = event.xdata, event.ydata
        if mouse_x is None or mouse_y is None:
            return
        
        # Find clicked point (same logic as hover)
        min_dist = float('inf')
        clicked_point = None
        
        for charge, velocity, metadata in self.data_points:
            x_range = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
            y_range = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
            
            dx = (charge - mouse_x) / x_range
            dy = (velocity - mouse_y) / y_range
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist < min_dist:
                min_dist = dist
                clicked_point = (charge, velocity, metadata)
        
        if min_dist < 0.05:
            charge, velocity, metadata = clicked_point
            self.point_clicked.emit(charge, velocity, metadata)
    
    def clear_data(self):
        """Clear all data"""
        self.data_points = []
        self._setup_plot()


class InteractivePowderChargeSlider(QWidget):
    """
    Interactive slider with live velocity/pressure estimation
    """
    
    charge_changed = pyqtSignal(float)  # Current charge
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        from PyQt6.QtWidgets import QSlider, QHBoxLayout, QLabel, QVBoxLayout
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🎚️ Interactive Charge Explorer")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        # Slider layout
        slider_layout = QHBoxLayout()
        
        # Min label
        self.label_min = QLabel("40.0 gr")
        self.label_min.setStyleSheet("color: #7f8c8d;")
        slider_layout.addWidget(self.label_min)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(400)  # 40.0 gr * 10
        self.slider.setMaximum(450)  # 45.0 gr * 10
        self.slider.setValue(425)    # 42.5 gr * 10
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(5)
        self.slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.slider)
        
        # Max label
        self.label_max = QLabel("45.0 gr")
        self.label_max.setStyleSheet("color: #7f8c8d;")
        slider_layout.addWidget(self.label_max)
        
        layout.addLayout(slider_layout)
        
        # Current value display
        value_layout = QHBoxLayout()
        
        value_layout.addWidget(QLabel("Current Charge:"))
        
        self.label_current = QLabel("42.5 gr")
        self.label_current.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #3498db;
            padding: 5px;
        """)
        value_layout.addWidget(self.label_current)
        
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        # Estimated values (would be calculated from model)
        est_layout = QHBoxLayout()
        
        self.label_est_velocity = QLabel("Est. Velocity: ~2680 fps")
        self.label_est_velocity.setStyleSheet("color: #27ae60; font-weight: bold;")
        est_layout.addWidget(self.label_est_velocity)
        
        self.label_est_pressure = QLabel("Est. Pressure: ~58,500 PSI")
        self.label_est_pressure.setStyleSheet("color: #f39c12; font-weight: bold;")
        est_layout.addWidget(self.label_est_pressure)
        
        est_layout.addStretch()
        layout.addLayout(est_layout)
        
        # Warning zone indicator
        self.label_warning = QLabel("")
        self.label_warning.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(self.label_warning)
        
        self.setLayout(layout)
    
    def on_slider_changed(self, value):
        """Handle slider change"""
        charge = value / 10.0
        self.label_current.setText(f"{charge:.1f} gr")
        
        # Estimate velocity (linear interpolation - would use real model)
        # Assume 40gr = 2600fps, 45gr = 2800fps (40 fps/gr)
        est_velocity = 2600 + (charge - 40.0) * 40.0
        self.label_est_velocity.setText(f"Est. Velocity: ~{est_velocity:.0f} fps")
        
        # Estimate pressure (would use real pressure model)
        # Assume 40gr = 55000 PSI, 45gr = 62000 PSI
        est_pressure = 55000 + (charge - 40.0) * 1400
        self.label_est_pressure.setText(f"Est. Pressure: ~{est_pressure:,.0f} PSI")
        
        # Warning if approaching max
        if charge >= 44.5:
            self.label_warning.setText("⚠️ WARNING: Approaching max charge!")
        elif charge >= 44.0:
            self.label_warning.setText("⚠️ CAUTION: High charge - watch for pressure signs")
        else:
            self.label_warning.setText("")
        
        self.charge_changed.emit(charge)
    
    def set_range(self, min_charge: float, max_charge: float):
        """Set slider range"""
        self.slider.setMinimum(int(min_charge * 10))
        self.slider.setMaximum(int(max_charge * 10))
        self.label_min.setText(f"{min_charge:.1f} gr")
        self.label_max.setText(f"{max_charge:.1f} gr")
    
    def set_value(self, charge: float):
        """Set current value"""
        self.slider.setValue(int(charge * 10))


class DragDropTrajectoryPlot(QWidget):
    """
    Drag & drop ammo profiles to see instant trajectory comparison
    """
    
    profile_dropped = pyqtSignal(int)  # profile_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.profiles = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Drop zone
        self.drop_label = QLabel("📦 Drag ammo profile here to see trajectory")
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #3498db;
                border-radius: 10px;
                padding: 40px;
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setMinimumHeight(150)
        layout.addWidget(self.drop_label)
        
        # Graph canvas
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor='#ecf0f1')
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)
        layout.addWidget(self.canvas)
        
        self._setup_empty_plot()
        
        self.setLayout(layout)
    
    def _setup_empty_plot(self):
        """Setup empty trajectory plot"""
        self.ax.clear()
        self.ax.set_xlabel('Distance (yards)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Drop (inches)', fontsize=12, fontweight='bold')
        self.ax.set_title('📊 Trajectory Comparison (Drag profiles here)', 
                         fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(0, color='black', linewidth=1, alpha=0.5)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def dragEnterEvent(self, event):
        """Accept drag events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 3px solid #27ae60;
                    border-radius: 10px;
                    padding: 40px;
                    background-color: #d5f4e6;
                    color: #27ae60;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """Reset style on drag leave"""
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #3498db;
                border-radius: 10px;
                padding: 40px;
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 16px;
                font-weight: bold;
            }
        """)
    
    def dropEvent(self, event):
        """Handle drop"""
        profile_id = int(event.mimeData().text())
        self.profile_dropped.emit(profile_id)
        self.dragLeaveEvent(event)
    
    def add_profile(self, profile_data: Dict):
        """Add profile trajectory to plot"""
        self.profiles.append(profile_data)
        self._update_plot()
    
    def _update_plot(self):
        """Update trajectory plot with all profiles"""
        self.ax.clear()
        
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        
        for idx, profile in enumerate(self.profiles):
            color = colors[idx % len(colors)]
            
            # Calculate trajectory (simplified - would use real ballistics)
            distances = np.linspace(0, 1000, 100)
            # Simple parabolic drop (would use real BC calculations)
            drop = -0.0001 * distances**2
            
            self.ax.plot(distances, drop, color=color, linewidth=2,
                        label=profile['name'], marker='o', markersize=4)
        
        self.ax.set_xlabel('Distance (yards)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Drop (inches)', fontsize=12, fontweight='bold')
        self.ax.set_title('📊 Trajectory Comparison', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(0, color='black', linewidth=1, alpha=0.5)
        self.ax.legend(loc='lower left')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def clear_profiles(self):
        """Clear all profiles"""
        self.profiles = []
        self._setup_empty_plot()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton
    import sys
    
    app = QApplication(sys.argv)
    
    # Test interactive graph
    window = QMainWindow()
    central = QWidget()
    layout = QVBoxLayout()
    
    # Graph
    graph = InteractiveVelocityGraph(width=10, height=6)
    
    # Add test data
    test_data = [
        (42.0, 2650, {'shot_number': 1, 'es': 15, 'sd': 6.2}),
        (42.5, 2680, {'shot_number': 2, 'es': 12, 'sd': 5.1}),
        (43.0, 2710, {'shot_number': 3, 'es': 18, 'sd': 7.3}),
        (43.5, 2730, {'shot_number': 4, 'es': 10, 'sd': 4.5}),
        (44.0, 2740, {'shot_number': 5, 'es': 8, 'sd': 3.2}),
        (44.5, 2745, {'shot_number': 6, 'es': 14, 'sd': 5.8}),
    ]
    
    for charge, vel, meta in test_data:
        graph.add_point(charge, vel, meta)
    
    def on_point_clicked(charge, velocity, metadata):
        from src.logging_config import configure_logging, get_logger
        configure_logging()
        logger = get_logger(__name__)
        logger.info("Clicked: %.1fgr @ %sfps", charge, velocity)
        logger.debug("Metadata: %s", metadata)
    
    graph.point_clicked.connect(on_point_clicked)
    layout.addWidget(graph)
    
    # Slider
    slider = InteractivePowderChargeSlider()
    layout.addWidget(slider)
    
    central.setLayout(layout)
    window.setCentralWidget(central)
    window.setWindowTitle("Interactive Features Demo")
    window.resize(1000, 800)
    window.show()
    
    sys.exit(app.exec())
