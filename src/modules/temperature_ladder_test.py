"""
Temperature Ladder Test System
Analyser hvordan ladninger presterer ved ulike temperaturer
Identifiser temperature-stable loads (som ammofabrikker gjør!)
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Tuple

import numpy as np

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
except Exception:  # pragma: no cover - optional plotting backend

    try:
        # Try to use a QWidget base if available so the stub can be added
        # to Qt layouts without type errors.
        from PyQt6.QtWidgets import QWidget as _QWidget
    except Exception:
        # Fallback stub when PyQt isn't available. Use a plain object
        # and silence type-assignment complaints to satisfy mypy.
        _QWidget = object  # type: ignore

    class FigureCanvasQTAgg(_QWidget):  # type: ignore
        def __init__(self, *args, **kwargs):
            if _QWidget is not object:
                super().__init__()

    class Figure:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass


if TYPE_CHECKING:
    from PyQt6.QtWidgets import (
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
else:
    try:
        from PyQt6.QtWidgets import (
            QComboBox,
            QDoubleSpinBox,
            QFileDialog,
            QGroupBox,
            QHBoxLayout,
            QHeaderView,
            QInputDialog,
            QLabel,
            QLineEdit,
            QMessageBox,
            QPushButton,
            QSpinBox,
            QTableWidget,
            QTableWidgetItem,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except Exception:  # pragma: no cover - headless test import fallback

        class _Stub:  # minimal import-time stand-ins
            def __init__(self, *args, **kwargs):
                return None

            def __getattr__(self, name):
                return _Stub

        # Use annotated Any assignments so runtime uses stubs while mypy sees types
        QComboBox: Any = _Stub
        QDoubleSpinBox: Any = _Stub
        QFileDialog: Any = _Stub
        QGroupBox: Any = _Stub
        QHBoxLayout: Any = _Stub
        QHeaderView: Any = _Stub
        QLabel: Any = _Stub
        QLineEdit: Any = _Stub
        QInputDialog: Any = _Stub
        QMessageBox: Any = _Stub
        QPushButton: Any = _Stub
        QSpinBox: Any = _Stub
        QTableWidget: Any = _Stub
        QTableWidgetItem: Any = _Stub
        QTextEdit: Any = _Stub
        QVBoxLayout: Any = _Stub
        QWidget: Any = object

from ..database.database import get_database


class TemperatureLadderTest(QWidget):
    """
    Temperature Ladder Test System
    Tests the same load at different temperatures to find temperature-stable loads
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.current_test_id = None
        self.test_data = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("Temperature Ladder Test")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel(
            "Test the same load at different temperatures to identify temperature-stable loads.\n"
            "Ammunition factories test from -20°C to +40°C to ensure safety in all conditions."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Test setup section
        setup_group = QGroupBox("Test Setup")
        setup_layout = QVBoxLayout()

        # Load selection
        load_layout = QHBoxLayout()
        load_layout.addWidget(QLabel("Ammunition Profile:"))
        self.combo_ammo = QComboBox()
        self.load_ammo_profiles()
        load_layout.addWidget(self.combo_ammo)
        load_layout.addStretch()
        setup_layout.addLayout(load_layout)

        # Test info
        info_layout = QHBoxLayout()

        info_layout.addWidget(QLabel("Rifle:"))
        self.combo_rifle = QComboBox()
        self.load_rifles()
        info_layout.addWidget(self.combo_rifle)

        info_layout.addWidget(QLabel("Test name:"))
        self.edit_test_name = QLineEdit()
        self.edit_test_name.setPlaceholderText("Temp test N140 43.5 gr")
        info_layout.addWidget(self.edit_test_name)

        setup_layout.addLayout(info_layout)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.btn_new_test = QPushButton("New Test")
        self.btn_new_test.clicked.connect(self.create_new_test)
        btn_layout.addWidget(self.btn_new_test)

        self.btn_load_test = QPushButton("Load Test")
        self.btn_load_test.clicked.connect(self.load_existing_test)
        btn_layout.addWidget(self.btn_load_test)

        btn_layout.addStretch()
        setup_layout.addLayout(btn_layout)

        setup_group.setLayout(setup_layout)
        layout.addWidget(setup_group)

        # Data entry section
        data_group = QGroupBox("Temperature & Velocity Data")
        data_layout = QVBoxLayout()

        # Entry row
        entry_layout = QHBoxLayout()

        entry_layout.addWidget(QLabel("Temp (°C):"))
        self.spin_temp = QDoubleSpinBox()
        self.spin_temp.setRange(-30, 50)
        self.spin_temp.setValue(15)
        self.spin_temp.setSuffix(" °C")
        entry_layout.addWidget(self.spin_temp)

        entry_layout.addWidget(QLabel("Velocity (fps):"))
        self.spin_velocity = QSpinBox()
        self.spin_velocity.setRange(500, 5000)
        self.spin_velocity.setValue(2700)
        self.spin_velocity.setSuffix(" fps")
        entry_layout.addWidget(self.spin_velocity)

        entry_layout.addWidget(QLabel("ES:"))
        self.spin_es = QSpinBox()
        self.spin_es.setRange(0, 200)
        self.spin_es.setSuffix(" fps")
        entry_layout.addWidget(self.spin_es)

        entry_layout.addWidget(QLabel("SD:"))
        self.spin_sd = QDoubleSpinBox()
        self.spin_sd.setRange(0, 100)
        self.spin_sd.setDecimals(1)
        entry_layout.addWidget(self.spin_sd)

        self.btn_add_data = QPushButton("Add")
        self.btn_add_data.clicked.connect(self.add_data_point)
        self.btn_add_data.setEnabled(False)
        entry_layout.addWidget(self.btn_add_data)

        entry_layout.addStretch()
        data_layout.addLayout(entry_layout)

        # Data table
        self.table_data = QTableWidget()
        self.table_data.setColumnCount(6)
        self.table_data.setHorizontalHeaderLabels(
            ["Temp (°C)", "Velocity (fps)", "ES", "SD", "Date", "Delete"]
        )
        self.table_data.horizontalHeader().setSectionResizeMode(  # type: ignore[union-attr]
            QHeaderView.ResizeMode.Stretch
        )
        data_layout.addWidget(self.table_data)

        data_group.setLayout(data_layout)
        layout.addWidget(data_group)

        # Analysis section
        analysis_group = QGroupBox("Analysis & Results")
        analysis_layout = QVBoxLayout()

        # Plot
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        analysis_layout.addWidget(self.canvas)

        # Analysis buttons
        analysis_btn_layout = QHBoxLayout()

        self.btn_analyze = QPushButton("Analyze")
        self.btn_analyze.clicked.connect(self.analyze_data)
        self.btn_analyze.setEnabled(False)
        analysis_btn_layout.addWidget(self.btn_analyze)

        self.btn_export = QPushButton("Export")
        self.btn_export.clicked.connect(self.export_results)
        self.btn_export.setEnabled(False)
        analysis_btn_layout.addWidget(self.btn_export)

        analysis_btn_layout.addStretch()
        analysis_layout.addLayout(analysis_btn_layout)

        # Results text
        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        self.text_results.setMaximumHeight(200)
        analysis_layout.addWidget(self.text_results)

        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        self.setLayout(layout)

    def load_ammo_profiles(self):
        """Last ammunisjonsprofiler"""
        profiles = self.db.get_all("ammo_profiles", "name")
        self.combo_ammo.clear()
        for profile in profiles:
            self.combo_ammo.addItem(profile["name"], profile["id"])

    def load_rifles(self):
        """Last rifles"""
        rifles = self.db.get_all("rifles", "name")
        self.combo_rifle.clear()
        for rifle in rifles:
            self.combo_rifle.addItem(
                f"{rifle['name']} ({rifle['caliber']})", rifle["id"]
            )

    def _format_date_label(self, date_value: Any) -> str:
        if not date_value:
            return ""
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                return date_value
        return str(date_value)

    def _append_data_row(
        self,
        temp: float,
        velocity: int,
        es: Any,
        sd: Any,
        test_date: Any,
        data_id: int,
    ):
        row = self.table_data.rowCount()
        self.table_data.insertRow(row)

        self.table_data.setItem(row, 0, QTableWidgetItem(f"{temp:.1f}"))
        self.table_data.setItem(row, 1, QTableWidgetItem(f"{velocity}"))
        self.table_data.setItem(
            row, 2, QTableWidgetItem("-" if es is None else f"{es}")
        )
        self.table_data.setItem(
            row, 3, QTableWidgetItem("-" if sd is None else f"{sd:.1f}")
        )
        self.table_data.setItem(
            row, 4, QTableWidgetItem(self._format_date_label(test_date))
        )

        btn_delete = QPushButton("Delete")
        btn_delete.setProperty("data_id", data_id)
        btn_delete.clicked.connect(self.delete_row)
        self.table_data.setCellWidget(row, 5, btn_delete)

        self.test_data.append(
            {"id": data_id, "temp": temp, "velocity": velocity, "es": es, "sd": sd}
        )

    def create_new_test(self):
        """Create a new temperature test"""
        if not self.edit_test_name.text():
            QMessageBox.warning(self, "Missing Name", "Enter a name for the test.")
            return

        ammo_id = self.combo_ammo.currentData()
        rifle_id = self.combo_rifle.currentData()

        if not ammo_id or not rifle_id:
            QMessageBox.warning(self, "Missing Data", "Select ammunition and firearm.")
            return

        # Create test in database
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO temperature_tests (
                name, ammo_profile_id, rifle_id, created_date
            ) VALUES (?, ?, ?, ?)
        """,
            (self.edit_test_name.text(), ammo_id, rifle_id, datetime.now().isoformat()),
        )
        self.db.conn.commit()

        self.current_test_id = cursor.lastrowid
        self.test_data = []
        self.table_data.setRowCount(0)

        self.btn_add_data.setEnabled(True)
        self.btn_analyze.setEnabled(False)
        self.btn_export.setEnabled(False)

        QMessageBox.information(
            self, "Test Created", f"Test ID: {self.current_test_id}"
        )

    def load_existing_test(self):
        """Load an existing test"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT
                tt.id,
                tt.name,
                tt.ammo_profile_id,
                tt.rifle_id,
                tt.created_date,
                ap.name AS ammo_name,
                r.name AS rifle_name,
                r.caliber AS rifle_caliber
            FROM temperature_tests tt
            LEFT JOIN ammo_profiles ap ON ap.id = tt.ammo_profile_id
            LEFT JOIN rifles r ON r.id = tt.rifle_id
            ORDER BY tt.created_date DESC
        """
        )
        tests = cursor.fetchall() or []

        if not tests:
            QMessageBox.information(
                self, "No Tests", "No saved temperature tests were found."
            )
            return

        choices = []
        for test in tests:
            ammo_name = test["ammo_name"] or "Unknown ammunition"
            rifle_name = test["rifle_name"] or "Unknown firearm"
            rifle_caliber = test["rifle_caliber"]
            if rifle_caliber:
                rifle_name = f"{rifle_name} ({rifle_caliber})"
            created_label = self._format_date_label(test["created_date"])
            choices.append(
                f"{test['name']} | {ammo_name} | {rifle_name} | {created_label}"
            )

        selected, ok = QInputDialog.getItem(
            self,
            "Select Test",
            "Select temperature test:",
            choices,
            0,
            False,
        )
        if not ok or not selected:
            return

        try:
            index = choices.index(selected)
        except ValueError:
            return

        test = tests[index]
        self.current_test_id = test["id"]
        self.edit_test_name.setText(test["name"])

        ammo_index = self.combo_ammo.findData(test["ammo_profile_id"])
        if ammo_index >= 0:
            self.combo_ammo.setCurrentIndex(ammo_index)

        rifle_index = self.combo_rifle.findData(test["rifle_id"])
        if rifle_index >= 0:
            self.combo_rifle.setCurrentIndex(rifle_index)

        cursor.execute(
            """
            SELECT id, temperature_c, velocity_fps, es_fps, sd_fps, test_date
            FROM temperature_test_data
            WHERE test_id = ?
            ORDER BY test_date
        """,
            (self.current_test_id,),
        )
        rows = cursor.fetchall() or []

        self.table_data.setRowCount(0)
        self.test_data = []
        for row in rows:
            self._append_data_row(
                row["temperature_c"],
                row["velocity_fps"],
                row["es_fps"],
                row["sd_fps"],
                row["test_date"],
                row["id"],
            )

        self.btn_add_data.setEnabled(True)
        self.btn_analyze.setEnabled(len(self.test_data) >= 2)
        self.btn_export.setEnabled(False)
        self.text_results.clear()
        self.figure.clear()
        self.canvas.draw()

    def add_data_point(self):
        """Add a data point"""
        if not self.current_test_id:
            return

        temp = self.spin_temp.value()
        velocity = self.spin_velocity.value()
        es = self.spin_es.value()
        sd = self.spin_sd.value()

        # Save to database
        cursor = self.db.conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO temperature_test_data (
                test_id, temperature_c, velocity_fps, es_fps, sd_fps, test_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (self.current_test_id, temp, velocity, es, sd, now_iso),
        )
        self.db.conn.commit()

        data_id = cursor.lastrowid
        test_date = now_iso

        if data_id is None:
            QMessageBox.warning(self, "Save Failed", "Could not save the data point.")
            return
        self._append_data_row(temp, velocity, es, sd, test_date, int(data_id))

        # Enable analyze if we have 2+ points
        if len(self.test_data) >= 2:
            self.btn_analyze.setEnabled(True)

        QMessageBox.information(
            self, "Added", f"Data point added: {temp}°C @ {velocity} fps"
        )

    def delete_row(self):
        """Delete a row"""
        btn = self.sender()
        if btn is None:
            return

        data_id = btn.property("data_id")
        if not data_id:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Do you want to delete this data point?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM temperature_test_data WHERE id = ?", (data_id,))
        self.db.conn.commit()

        for row_index in range(self.table_data.rowCount()):
            if self.table_data.cellWidget(row_index, 5) is btn:
                self.table_data.removeRow(row_index)
                break

        self.test_data = [d for d in self.test_data if d.get("id") != data_id]

        if len(self.test_data) < 2:
            self.btn_analyze.setEnabled(False)
        if not self.test_data:
            self.btn_export.setEnabled(False)
            self.text_results.clear()
            self.figure.clear()
            self.canvas.draw()

    def analyze_data(self):
        """Analyze temperature sensitivity"""
        if len(self.test_data) < 2:
            QMessageBox.warning(
                self, "Too Little Data", "At least 2 data points are required."
            )
            return

        # Extract data
        temps = [d["temp"] for d in self.test_data]
        velocities = [d["velocity"] for d in self.test_data]

        # Linear regression
        n = len(temps)
        sum_x = sum(temps)
        sum_y = sum(velocities)
        sum_xx = sum(x * x for x in temps)
        sum_xy = sum(x * y for x, y in zip(temps, velocities))

        # Slope (fps per °C)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)

        # Intercept
        intercept = (sum_y - slope * sum_x) / n

        # R-squared
        mean_y = sum_y / n
        ss_tot = sum((y - mean_y) ** 2 for y in velocities)
        ss_res = sum(
            (y - (slope * x + intercept)) ** 2 for x, y in zip(temps, velocities)
        )
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Plot
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Scatter plot
        ax.scatter(
            temps, velocities, s=100, alpha=0.6, color="blue", label="Measurements"
        )

        # Regression line
        temp_range = np.linspace(min(temps) - 5, max(temps) + 5, 100)
        vel_pred = slope * temp_range + intercept
        ax.plot(
            temp_range, vel_pred, "r--", linewidth=2, label=f"Trend: {slope:.2f} fps/°C"
        )

        # Styling
        ax.set_xlabel("Temperature (°C)", fontsize=12, fontweight="bold")
        ax.set_ylabel("Velocity (fps)", fontsize=12, fontweight="bold")
        ax.set_title("Temperature Sensitivity Analysis", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend()

        self.canvas.draw()

        # Generate results
        temp_stability_rating = self.rate_temp_stability(abs(slope))

        # Velocity prediction at extremes
        vel_at_minus20 = slope * -20 + intercept
        vel_at_plus40 = slope * 40 + intercept
        vel_spread = vel_at_plus40 - vel_at_minus20

        results = f"""
        <h2 style='color: #2c3e50;'>Analysis Results</h2>

        <h3>Temperature Sensitivity:</h3>
        <ul>
            <li><b>Slope:</b> {slope:.2f} fps/°C {self.get_slope_emoji(slope)}</li>
            <li><b>R² (fit quality):</b> {r_squared:.3f}</li>
            <li><b>Rating:</b> <span style='color: {temp_stability_rating[1]};'>
                <b>{temp_stability_rating[0]}</b></span></li>
        </ul>

        <h3>Velocity Predictions:</h3>
        <ul>
            <li><b>At -20°C:</b> {vel_at_minus20:.0f} fps</li>
            <li><b>At +40°C:</b> {vel_at_plus40:.0f} fps</li>
            <li><b>Total spread:</b> {vel_spread:.0f} fps (60°C range)</li>
        </ul>

        <h3>Comparison with factory ammunition:</h3>
        <p style='color: #7f8c8d;'>
        {self.compare_to_factory(abs(slope))}
        </p>

        <h3>Recommendations:</h3>
        {self.get_recommendations(slope, r_squared)}
        """

        self.text_results.setHtml(results)
        self.btn_export.setEnabled(True)

    def rate_temp_stability(self, abs_slope: float) -> Tuple[str, str]:
        """Rate temperature stability"""
        if abs_slope < 0.5:
            return ("EXCELLENT (Factory-grade)", "#27ae60")
        elif abs_slope < 1.0:
            return ("VERY GOOD", "#2ecc71")
        elif abs_slope < 2.0:
            return ("GOOD", "#f39c12")
        elif abs_slope < 3.0:
            return ("MODERATE", "#e67e22")
        else:
            return ("POOR", "#e74c3c")

    def get_slope_emoji(self, slope: float) -> str:
        """Get label for slope direction"""
        if slope > 0:
            return "(velocity increases with temperature)"
        else:
            return "(velocity decreases with temperature)"

    def compare_to_factory(self, abs_slope: float) -> str:
        """Compare to factory ammo standards"""
        if abs_slope < 0.5:
            return "Your load is BETTER than most factory ammunition. Federal Gold Medal: about 0.8 fps/°C"
        elif abs_slope < 1.0:
            return "Your load is ON PAR with premium factory ammunition. Hornady Match: about 1.0 fps/°C"
        elif abs_slope < 2.0:
            return "Your load is OK, but factory ammunition is better. Consider temperature-stable powder."
        else:
            return "Your load is WORSE than factory ammunition. This powder is temperature-sensitive."

    def get_recommendations(self, slope: float, r_squared: float) -> str:
        """Get recommendations based on results"""
        recs = "<ul>"

        if abs(slope) > 2.0:
            recs += """
            <li style='color: #e74c3c;'><b>High temperature sensitivity.</b> Consider:
                <ul>
                    <li>Hodgdon Extreme-series (H4350, Varget, H1000)</li>
                    <li>Vihtavuori N500-series (N540, N550, N560)</li>
                    <li>Alliant Reloder 16, 26</li>
                </ul>
            </li>
            """

        if r_squared < 0.8:
            recs += """
            <li style='color: #f39c12;'><b>Low R².</b> The data is not linear. Possible causes:
                <ul>
                    <li>Inconsistent loading (varying powder charges)</li>
                    <li>Pressure limit reached at higher temperatures</li>
                    <li>Chronograph measurement error</li>
                    <li>Test more shots per temperature for better data</li>
                </ul>
            </li>
            """

        if abs(slope) < 1.0:
            recs += """
            <li style='color: #27ae60;'><b>Excellent temperature stability.</b>
                <ul>
                    <li>This load is safe across all weather conditions</li>
                    <li>You can use the same zero from -20°C to +40°C</li>
                    <li>Typical of Hodgdon Extreme and Vihtavuori N500</li>
                </ul>
            </li>
            """

        recs += "</ul>"
        return recs

    def export_results(self):
        """Export results to a file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            f"temp_test_{datetime.now().strftime('%Y%m%d')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv)",
        )

        if filename:
            with open(filename, "w") as f:
                f.write("Temperature Ladder Test Results\n")
                f.write("================================\n\n")
                f.write(f"Test: {self.edit_test_name.text()}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

                f.write("Data:\n")
                for d in self.test_data:
                    f.write(
                        f"{d['temp']:.1f}°C: {d['velocity']} fps (ES: {d['es']}, SD: {d['sd']})\n"
                    )

            QMessageBox.information(self, "Exported", f"Results saved to:\n{filename}")


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = TemperatureLadderTest()
    window.show()
    sys.exit(app.exec())
