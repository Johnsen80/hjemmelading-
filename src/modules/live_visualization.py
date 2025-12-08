"""
Live Visualization Widgets
Real-time graphs med interactive updates
"""

# Guard matplotlib imports — plotting backend may be unavailable in some environments
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    # Import under a different alias during type-checking so we don't create
    # the name `BaseCanvas` as a type here — it will be assigned at runtime
    # below and that assignment would otherwise confuse mypy ("Cannot assign
    # to a type").
    try:  # pragma: no cover - typing-only
        from matplotlib.backends.backend_qtagg import (
            FigureCanvasQTAgg as _TypingBaseCanvas,
        )  # type: ignore
    except Exception:  # pragma: no cover - typing-only
        from typing import Any as _Any

        _TypingBaseCanvas = _Any  # type: ignore

# At runtime we will bind `BaseCanvas` to either the real FigureCanvasQTAgg
# class or to the local fallback class below. Declare it as `Any` here so
# mypy does not treat it as a fixed type and complain about later assignment.
BaseCanvas: Any

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure

    _HAS_MPL = True
except Exception:
    FigureCanvasQTAgg: Any = None  # type: ignore[no-redef]
    Figure: Any = None  # type: ignore[no-redef]
    plt: Any = None  # type: ignore[no-redef]
    _HAS_MPL = False
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

# Provide a safe BaseCanvas when matplotlib/qtagg backend is missing
if _HAS_MPL:
    BaseCanvas = FigureCanvasQTAgg
else:

    class BaseCanvas(QWidget):  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            # Accept either parent or a Figure object; keep API small
            parent = None
            if args:
                # If parent passed positionally, use it
                parent = args[0]
            parent = kwargs.get("parent", parent)
            super().__init__(parent)
            layout = QVBoxLayout()
            label = QLabel("Plotting unavailable in this environment")
            layout.addWidget(label)
            self.setLayout(layout)

        def draw(self):
            return


class LiveVelocityGraph(BaseCanvas):
    """
    Live velocity graph for Ladder Tests
    Updates in real-time etter hvert shot
    """

    def __init__(self, parent=None, width=8, height=5, dpi=100):
        if _HAS_MPL:
            self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="#ecf0f1")
            self.ax = self.fig.add_subplot(111)
            super().__init__(self.fig)
        else:
            # fallback canvas
            self.fig = None
            self.ax = None
            super().__init__(parent)

        self.data_x = []  # Powder charge
        self.data_y = []  # Velocity

        self._setup_plot()

    def _setup_plot(self):
        """Setup initial plot"""
        if self.ax is None:
            return
        self.ax.clear()
        self.ax.set_xlabel("Powder Charge (gr)", fontsize=12, fontweight="bold")
        self.ax.set_ylabel("Velocity (fps)", fontsize=12, fontweight="bold")
        # Avoid emoji in matplotlib title to prevent missing-glyph warnings
        self.ax.set_title(
            "Live Velocity Ladder", fontsize=14, fontweight="bold", pad=20
        )
        self.ax.grid(True, alpha=0.3, linestyle="--")

        # Styling
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_linewidth(2)
        self.ax.spines["bottom"].set_linewidth(2)

        self.fig.tight_layout()
        self.draw()

    def add_point(self, charge: float, velocity: float):
        """Add data point - updates graph live"""
        self.data_x.append(charge)
        self.data_y.append(velocity)
        self._update_plot()

    def _update_plot(self):
        """Update plot with new data"""
        if self.ax is None:
            return
        self.ax.clear()

        # Scatter plot
        self.ax.scatter(
            self.data_x,
            self.data_y,
            s=100,
            c="#3498db",
            edgecolors="#2c3e50",
            linewidths=2,
            zorder=3,
            label="Shots",
        )

        # If enough points, draw trend line
        if len(self.data_x) >= 3:
            x_arr = np.array(self.data_x)
            y_arr = np.array(self.data_y)

            # Linear regression
            z = np.polyfit(x_arr, y_arr, 1)
            p = np.poly1d(z)

            x_line = np.linspace(min(x_arr), max(x_arr), 100)
            y_line = p(x_line)

            self.ax.plot(
                x_line,
                y_line,
                "r--",
                linewidth=2,
                alpha=0.7,
                label=f"Trend: {z[0]:.1f} fps/gr",
            )

            # Highlight potential nodes (flat spots)
            if len(self.data_x) >= 5:
                self._detect_nodes()

        # Labels and styling
        self.ax.set_xlabel("Powder Charge (gr)", fontsize=12, fontweight="bold")
        self.ax.set_ylabel("Velocity (fps)", fontsize=12, fontweight="bold")
        self.ax.set_title(
            "Live Velocity Ladder", fontsize=14, fontweight="bold", pad=20
        )
        self.ax.grid(True, alpha=0.3, linestyle="--")
        self.ax.legend(loc="upper left", framealpha=0.9)

        # Styling
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        self.fig.tight_layout()
        self.draw()

    def _detect_nodes(self):
        """Detect pressure nodes (flat spots in velocity)"""
        if len(self.data_x) < 5:
            return

        _x_arr = np.array(self.data_x)
        y_arr = np.array(self.data_y)

        # Calculate velocity increase per charge step
        vel_deltas = np.diff(y_arr)

        # Find where velocity increase is minimal (nodes)
        threshold = np.mean(vel_deltas) * 0.5  # 50% of average increase

        nodes = []
        for i in range(len(vel_deltas)):
            if vel_deltas[i] < threshold:
                nodes.append(i + 1)  # Index in original array

        # Highlight nodes
        if nodes:
            node_x = [self.data_x[i] for i in nodes]
            node_y = [self.data_y[i] for i in nodes]

            self.ax.scatter(
                node_x,
                node_y,
                s=200,
                facecolors="none",
                edgecolors="#27ae60",
                linewidths=3,
                zorder=4,
                label="⭐ Pressure Nodes",
            )

    def clear_data(self):
        """Clear all data"""
        self.data_x = []
        self.data_y = []
        self._setup_plot()


class LiveGroupOverlay(BaseCanvas):
    """
    Live group overlay for OCW tests
    Shows all shots accumulating
    """

    def __init__(self, parent=None, width=7, height=7, dpi=100):
        if _HAS_MPL:
            self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="#ecf0f1")
            self.ax = self.fig.add_subplot(111)
            super().__init__(self.fig)
        else:
            self.fig = None
            self.ax = None
            super().__init__(parent)

        self.groups = {}  # {charge: [(x, y), ...]}
        self.colors = [
            "#3498db",
            "#e74c3c",
            "#2ecc71",
            "#f39c12",
            "#9b59b6",
            "#1abc9c",
            "#34495e",
            "#e67e22",
            "#95a5a6",
            "#d35400",
        ]

        self._setup_plot()

    def _setup_plot(self):
        """Setup target overlay"""
        if self.ax is None:
            return
        self.ax.clear()
        self.ax.set_xlim(-3, 3)
        self.ax.set_ylim(-3, 3)
        self.ax.set_aspect("equal")
        self.ax.set_xlabel("Horizontal (inches)", fontsize=10)
        self.ax.set_ylabel("Vertical (inches)", fontsize=10)
        # Use plain text title to avoid emoji glyph warnings
        self.ax.set_title("Live Group Overlay", fontsize=14, fontweight="bold", pad=15)

        # Draw target circles
        for radius in [1, 2, 3]:
            if plt is not None and self.ax is not None:
                try:
                    circle = plt.Circle(
                        (0, 0),
                        radius,
                        fill=False,
                        color="gray",
                        linestyle="--",
                        linewidth=1,
                        alpha=0.5,
                    )
                    self.ax.add_patch(circle)
                except Exception:
                    pass

        # Crosshair
        self.ax.axhline(0, color="gray", linestyle="-", linewidth=0.5, alpha=0.3)
        self.ax.axvline(0, color="gray", linestyle="-", linewidth=0.5, alpha=0.3)

        self.ax.grid(True, alpha=0.2)
        if _HAS_MPL:
            self.fig.tight_layout()
            self.draw()

    def add_shot(self, charge: float, x: float, y: float):
        """Add shot to group"""
        if charge not in self.groups:
            self.groups[charge] = []

        self.groups[charge].append((x, y))
        self._update_plot()

    def _update_plot(self):
        """Update overlay"""
        self._setup_plot()

        # Plot each group
        charge_list = sorted(self.groups.keys())

        for idx, charge in enumerate(charge_list):
            color = self.colors[idx % len(self.colors)]
            shots = self.groups[charge]

            x_vals = [s[0] for s in shots]
            y_vals = [s[1] for s in shots]

            # Plot shots
            self.ax.scatter(
                x_vals,
                y_vals,
                s=80,
                c=color,
                alpha=0.7,
                edgecolors="black",
                linewidths=1.5,
                label=f"{charge}gr (n={len(shots)})",
            )

            # Draw group size circle
            if len(shots) >= 3:
                # Calculate extreme spread
                min_x, max_x = min(x_vals), max(x_vals)
                min_y, max_y = min(y_vals), max(y_vals)

                # Center and radius
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                radius = max(max_x - min_x, max_y - min_y) / 2

                if plt is not None:
                    try:
                        circle = plt.Circle(
                            (center_x, center_y),
                            radius,
                            fill=False,
                            color=color,
                            linestyle="-",
                            linewidth=2,
                            alpha=0.5,
                        )
                        self.ax.add_patch(circle)
                    except Exception:
                        pass

                # Add group size text
                self.ax.text(
                    center_x,
                    center_y + radius + 0.2,
                    f'{radius*2:.3f}"',
                    ha="center",
                    fontsize=9,
                    fontweight="bold",
                    color=color,
                )

        if self.groups:
            self.ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

        self.fig.tight_layout()
        self.draw()

    def clear_data(self):
        """Clear all groups"""
        self.groups = {}
        self._setup_plot()


class LiveStatisticsDisplay(QWidget):
    """
    Live statistics display - updates as data comes in
    Shows SD, ES, mean in real-time
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("📊 Live Statistics")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Stats grid
        stats_layout = QHBoxLayout()

        # Mean
        self.label_mean = self._create_stat_label("Mean", "---", "#3498db")
        stats_layout.addWidget(self.label_mean)

        # SD
        self.label_sd = self._create_stat_label("SD", "---", "#e74c3c")
        stats_layout.addWidget(self.label_sd)

        # ES
        self.label_es = self._create_stat_label("ES", "---", "#f39c12")
        stats_layout.addWidget(self.label_es)

        # Count
        self.label_count = self._create_stat_label("Shots", "0", "#27ae60")
        stats_layout.addWidget(self.label_count)

        layout.addLayout(stats_layout)

        self.setLayout(layout)

    def _create_stat_label(self, name: str, value: str, color: str) -> QWidget:
        """Create stat display widget"""
        widget = QWidget()
        widget.setStyleSheet(
            f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self._darken(color)});
                border-radius: 10px;
                padding: 15px;
            }}
        """
        )

        layout = QVBoxLayout()

        name_label = QLabel(name)
        name_label.setStyleSheet(
            "color: white; font-size: 12px; background: transparent;"
        )
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            "color: white; font-size: 24px; font-weight: bold; background: transparent;"
        )
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setObjectName(f"{name}_value")
        layout.addWidget(value_label)

        widget.setLayout(layout)
        return widget

    def _darken(self, color: str) -> str:
        """Darken color"""
        color = color.lstrip("#")
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def add_value(self, value: float):
        """Add value and update stats"""
        self.values.append(value)
        self._update_display()

    def _update_display(self):
        """Update all stat displays"""
        if not self.values:
            return

        # Calculate stats
        mean = np.mean(self.values)
        sd = np.std(self.values, ddof=1) if len(self.values) > 1 else 0
        es = max(self.values) - min(self.values) if len(self.values) > 1 else 0
        count = len(self.values)

        # Update labels
        self.label_mean.findChild(QLabel, "Mean_value").setText(f"{mean:.1f}")
        self.label_sd.findChild(QLabel, "SD_value").setText(f"{sd:.1f}")
        self.label_es.findChild(QLabel, "ES_value").setText(f"{es:.1f}")
        self.label_count.findChild(QLabel, "Shots_value").setText(f"{count}")

    def clear_data(self):
        """Clear all data"""
        self.values = []
        self.label_mean.findChild(QLabel, "Mean_value").setText("---")
        self.label_sd.findChild(QLabel, "SD_value").setText("---")
        self.label_es.findChild(QLabel, "ES_value").setText("---")
        self.label_count.findChild(QLabel, "Shots_value").setText("0")


class LiveHistogram(BaseCanvas):
    """
    Live histogram for Batch QC
    Shows distribution as measurements come in
    """

    def __init__(self, parent=None, width=8, height=5, dpi=100):
        if _HAS_MPL:
            self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="#ecf0f1")
            self.ax = self.fig.add_subplot(111)
            super().__init__(self.fig)
        else:
            self.fig = None
            self.ax = None
            super().__init__(parent)

        self.data = []
        self.target = None
        self.tolerance = None
        self.unit = ""

        self._setup_plot()

    def _setup_plot(self):
        """Setup histogram"""
        if self.ax is None:
            return
        self.ax.clear()
        self.ax.set_xlabel("Value", fontsize=12, fontweight="bold")
        self.ax.set_ylabel("Frequency", fontsize=12, fontweight="bold")
        self.ax.set_title("Live Distribution", fontsize=14, fontweight="bold", pad=20)
        self.ax.grid(True, alpha=0.3, axis="y")

        if _HAS_MPL:
            self.fig.tight_layout()
            self.draw()

    def set_target(self, target: float, tolerance: float, unit: str):
        """Set target and tolerance"""
        self.target = target
        self.tolerance = tolerance
        self.unit = unit

    def add_value(self, value: float):
        """Add measurement"""
        self.data.append(value)
        self._update_plot()

    def _update_plot(self):
        """Update histogram"""
        if not self.data or self.target is None:
            return

        self.ax.clear()

        # Histogram
        n, bins, patches = self.ax.hist(
            self.data, bins=20, color="#3498db", alpha=0.7, edgecolor="black"
        )

        # Color outliers
        if self.tolerance:
            lower = self.target - self.tolerance
            upper = self.target + self.tolerance

            for i, patch in enumerate(patches):
                bin_center = (bins[i] + bins[i + 1]) / 2
                if bin_center < lower or bin_center > upper:
                    patch.set_facecolor("#e74c3c")

        # Target line
        if self.target:
            self.ax.axvline(
                self.target,
                color="#27ae60",
                linestyle="--",
                linewidth=2,
                label=f"Target: {self.target}{self.unit}",
            )

        # Tolerance lines
        if self.tolerance:
            self.ax.axvline(
                self.target - self.tolerance,
                color="#f39c12",
                linestyle=":",
                linewidth=2,
                label="Tolerance",
            )
            self.ax.axvline(
                self.target + self.tolerance,
                color="#f39c12",
                linestyle=":",
                linewidth=2,
            )

        # Stats text
        if len(self.data) > 1:
            mean = np.mean(self.data)
            std = np.std(self.data, ddof=1)
            outliers = (
                sum(1 for v in self.data if abs(v - self.target) > self.tolerance)
                if self.tolerance
                else 0
            )
            outlier_pct = (outliers / len(self.data)) * 100

            stats_text = f"n={len(self.data)}  μ={mean:.3f}  σ={std:.3f}\nOutliers: {outliers} ({outlier_pct:.1f}%)"

            self.ax.text(
                0.98,
                0.98,
                stats_text,
                transform=self.ax.transAxes,
                fontsize=10,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            )

        self.ax.set_xlabel(f"Value ({self.unit})", fontsize=12, fontweight="bold")
        self.ax.set_ylabel("Frequency", fontsize=12, fontweight="bold")
        self.ax.set_title(
            "📊 Live Distribution", fontsize=14, fontweight="bold", pad=20
        )
        self.ax.legend(loc="upper left")
        self.ax.grid(True, alpha=0.3, axis="y")

        self.fig.tight_layout()
        self.draw()

    def clear_data(self):
        """Clear data"""
        self.data = []
        self._setup_plot()


# Import matplotlib.pyplot for circle patch
import matplotlib.pyplot as plt

if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Test live velocity graph
    graph = LiveVelocityGraph()
    graph.show()

    # Simulate data coming in
    def add_test_data():
        charges = [42.0, 42.5, 43.0, 43.5, 44.0, 44.5, 45.0]
        velocities = [2650, 2680, 2710, 2730, 2740, 2745, 2780]

        timer = QTimer()
        idx = [0]

        def add_point():
            if idx[0] < len(charges):
                graph.add_point(charges[idx[0]], velocities[idx[0]])
                idx[0] += 1
            else:
                timer.stop()

        timer.timeout.connect(add_point)
        timer.start(1000)  # Add point every second

    add_test_data()

    sys.exit(app.exec())
