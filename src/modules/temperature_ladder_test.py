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

    class FigureCanvasQTAgg:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

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
        QMessageBox: Any = _Stub
        QPushButton: Any = _Stub
        QSpinBox: Any = _Stub
        QTableWidget: Any = _Stub
        QTableWidgetItem: Any = _Stub
        QTextEdit: Any = _Stub
        QVBoxLayout: Any = _Stub
        QWidget: Any = object

from src.database.database import get_database


class TemperatureLadderTest(QWidget):
    """
    Temperature Ladder Test System
    Tester samme ladning ved ulike temperaturer for å finne temp-stable loads
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
        header = QLabel("🌡️ Temperature Ladder Test")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel(
            "Test samme ladning ved ulike temperaturer for å identifisere temp-stable loads.\n"
            "Ammofabrikker tester -20°C til +40°C for å garantere sikkerhet i alle forhold!"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Test setup section
        setup_group = QGroupBox("🔧 Test Oppsett")
        setup_layout = QVBoxLayout()

        # Load selection
        load_layout = QHBoxLayout()
        load_layout.addWidget(QLabel("Ammunisjonsprofil:"))
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

        info_layout.addWidget(QLabel("Test navn:"))
        self.edit_test_name = QLineEdit()
        self.edit_test_name.setPlaceholderText("Temp test N140 43.5gr")
        info_layout.addWidget(self.edit_test_name)

        setup_layout.addLayout(info_layout)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.btn_new_test = QPushButton("🆕 Ny Test")
        self.btn_new_test.clicked.connect(self.create_new_test)
        btn_layout.addWidget(self.btn_new_test)

        self.btn_load_test = QPushButton("📂 Last Test")
        self.btn_load_test.clicked.connect(self.load_existing_test)
        btn_layout.addWidget(self.btn_load_test)

        btn_layout.addStretch()
        setup_layout.addLayout(btn_layout)

        setup_group.setLayout(setup_layout)
        layout.addWidget(setup_group)

        # Data entry section
        data_group = QGroupBox("📊 Temperatur & Velocity Data")
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

        self.btn_add_data = QPushButton("➕ Legg til")
        self.btn_add_data.clicked.connect(self.add_data_point)
        self.btn_add_data.setEnabled(False)
        entry_layout.addWidget(self.btn_add_data)

        entry_layout.addStretch()
        data_layout.addLayout(entry_layout)

        # Data table
        self.table_data = QTableWidget()
        self.table_data.setColumnCount(6)
        self.table_data.setHorizontalHeaderLabels(
            ["Temp (°C)", "Velocity (fps)", "ES", "SD", "Dato", "Slett"]
        )
        self.table_data.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        data_layout.addWidget(self.table_data)

        data_group.setLayout(data_layout)
        layout.addWidget(data_group)

        # Analysis section
        analysis_group = QGroupBox("📈 Analyse & Resultater")
        analysis_layout = QVBoxLayout()

        # Plot
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        analysis_layout.addWidget(self.canvas)

        # Analysis buttons
        analysis_btn_layout = QHBoxLayout()

        self.btn_analyze = QPushButton("🔍 Analyser")
        self.btn_analyze.clicked.connect(self.analyze_data)
        self.btn_analyze.setEnabled(False)
        analysis_btn_layout.addWidget(self.btn_analyze)

        self.btn_export = QPushButton("💾 Eksporter")
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

    def create_new_test(self):
        """Opprett ny temperature test"""
        if not self.edit_test_name.text():
            QMessageBox.warning(self, "Mangler navn", "Angi et navn for testen!")
            return

        ammo_id = self.combo_ammo.currentData()
        rifle_id = self.combo_rifle.currentData()

        if not ammo_id or not rifle_id:
            QMessageBox.warning(self, "Mangler data", "Velg ammunisjon og rifle!")
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
            self, "Test opprettet", f"Test ID: {self.current_test_id}"
        )

    def load_existing_test(self):
        """Last eksisterende test"""
        # TODO: Implement test selection dialog
        QMessageBox.information(
            self, "Under utvikling", "Load test dialog kommer snart!"
        )

    def add_data_point(self):
        """Legg til et datapunkt"""
        if not self.current_test_id:
            return

        temp = self.spin_temp.value()
        velocity = self.spin_velocity.value()
        es = self.spin_es.value()
        sd = self.spin_sd.value()

        # Save to database
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO temperature_test_data (
                test_id, temperature_c, velocity_fps, es_fps, sd_fps, test_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (self.current_test_id, temp, velocity, es, sd, datetime.now().isoformat()),
        )
        self.db.conn.commit()

        # Add to table
        row = self.table_data.rowCount()
        self.table_data.insertRow(row)

        self.table_data.setItem(row, 0, QTableWidgetItem(f"{temp:.1f}"))
        self.table_data.setItem(row, 1, QTableWidgetItem(f"{velocity}"))
        self.table_data.setItem(row, 2, QTableWidgetItem(f"{es}"))
        self.table_data.setItem(row, 3, QTableWidgetItem(f"{sd:.1f}"))
        self.table_data.setItem(
            row, 4, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M"))
        )

        # Delete button
        btn_delete = QPushButton("🗑️")
        btn_delete.clicked.connect(lambda: self.delete_row(row))
        self.table_data.setCellWidget(row, 5, btn_delete)

        # Add to test_data
        self.test_data.append({"temp": temp, "velocity": velocity, "es": es, "sd": sd})

        # Enable analyze if we have 2+ points
        if len(self.test_data) >= 2:
            self.btn_analyze.setEnabled(True)

        QMessageBox.information(
            self, "Lagt til", f"Datapunkt lagt til: {temp}°C @ {velocity} fps"
        )

    def delete_row(self, row: int):
        """Slett en rad"""
        # TODO: Delete from database
        self.table_data.removeRow(row)
        if row < len(self.test_data):
            self.test_data.pop(row)

    def analyze_data(self):
        """Analyser temperature sensitivity"""
        if len(self.test_data) < 2:
            QMessageBox.warning(self, "For lite data", "Trenger minst 2 datapunkter!")
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
        ax.scatter(temps, velocities, s=100, alpha=0.6, color="blue", label="Målinger")

        # Regression line
        temp_range = np.linspace(min(temps) - 5, max(temps) + 5, 100)
        vel_pred = slope * temp_range + intercept
        ax.plot(
            temp_range, vel_pred, "r--", linewidth=2, label=f"Trend: {slope:.2f} fps/°C"
        )

        # Styling
        ax.set_xlabel("Temperatur (°C)", fontsize=12, fontweight="bold")
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
        <h2 style='color: #2c3e50;'>📊 Analyse Resultater</h2>

        <h3>Temperature Sensitivity:</h3>
        <ul>
            <li><b>Slope:</b> {slope:.2f} fps/°C {self.get_slope_emoji(slope)}</li>
            <li><b>R² (fit quality):</b> {r_squared:.3f}</li>
            <li><b>Rating:</b> <span style='color: {temp_stability_rating[1]};'>
                <b>{temp_stability_rating[0]}</b></span></li>
        </ul>

        <h3>Velocity Predictions:</h3>
        <ul>
            <li><b>Ved -20°C:</b> {vel_at_minus20:.0f} fps</li>
            <li><b>Ved +40°C:</b> {vel_at_plus40:.0f} fps</li>
            <li><b>Total spread:</b> {vel_spread:.0f} fps (60°C range)</li>
        </ul>

        <h3>Sammenligning med ammofabrikker:</h3>
        <p style='color: #7f8c8d;'>
        {self.compare_to_factory(abs(slope))}
        </p>

        <h3>💡 Anbefalinger:</h3>
        {self.get_recommendations(slope, r_squared)}
        """

        self.text_results.setHtml(results)
        self.btn_export.setEnabled(True)

    def rate_temp_stability(self, abs_slope: float) -> Tuple[str, str]:
        """Rate temperature stability"""
        if abs_slope < 0.5:
            return ("🏆 EXCELLENT (Factory-grade)", "#27ae60")
        elif abs_slope < 1.0:
            return ("✅ VERY GOOD", "#2ecc71")
        elif abs_slope < 2.0:
            return ("👍 GOOD", "#f39c12")
        elif abs_slope < 3.0:
            return ("⚠️ MODERATE", "#e67e22")
        else:
            return ("❌ POOR", "#e74c3c")

    def get_slope_emoji(self, slope: float) -> str:
        """Get emoji for slope direction"""
        if slope > 0:
            return "📈 (velocity øker med temp)"
        else:
            return "📉 (velocity synker med temp)"

    def compare_to_factory(self, abs_slope: float) -> str:
        """Compare to factory ammo standards"""
        if abs_slope < 0.5:
            return "Din ladning er BEDRE enn de fleste fabrikk-ammunisjoner! Federal Gold Medal: ~0.8 fps/°C"
        elif abs_slope < 1.0:
            return "Din ladning er PÅ NIVÅ med premium fabrikk-ammo. Hornady Match: ~1.0 fps/°C"
        elif abs_slope < 2.0:
            return "Din ladning er OK, men fabrikk-ammo er bedre. Vurder temp-stable krutt."
        else:
            return "Din ladning er DÅRLIGERE enn fabrikk-ammo. Dette krutt er temp-sensitive!"

    def get_recommendations(self, slope: float, r_squared: float) -> str:
        """Get recommendations based on results"""
        recs = "<ul>"

        if abs(slope) > 2.0:
            recs += """
            <li style='color: #e74c3c;'><b>⚠️ Høy temp-sensitivitet!</b> Vurder:
                <ul>
                    <li>Hodgdon Extreme-series (H4350, Varget, H1000)</li>
                    <li>Vihtavuori N500-series (N540, N550, N560)</li>
                    <li>Alliant Reloder 16, 26</li>
                </ul>
            </li>
            """

        if r_squared < 0.8:
            recs += """
            <li style='color: #f39c12;'><b>⚠️ Lav R²!</b> Dataene er ikke lineære. Mulige årsaker:
                <ul>
                    <li>Inkonsistent lading (varying powder charges)</li>
                    <li>Pressure limit nådd ved høy temp</li>
                    <li>Måle-feil i kronograf</li>
                    <li>Test flere skudd per temp for bedre data</li>
                </ul>
            </li>
            """

        if abs(slope) < 1.0:
            recs += """
            <li style='color: #27ae60;'><b>✅ Excellent temp stability!</b>
                <ul>
                    <li>Denne ladningen er trygg i alle værforhold</li>
                    <li>Kan bruke samme zero fra -20°C til +40°C</li>
                    <li>Typisk for Hodgdon Extreme og Vihtavuori N500</li>
                </ul>
            </li>
            """

        recs += "</ul>"
        return recs

    def export_results(self):
        """Eksporter resultater til fil"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Eksporter resultater",
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

            QMessageBox.information(
                self, "Eksportert", f"Resultater lagret til:\n{filename}"
            )


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = TemperatureLadderTest()
    window.show()
    sys.exit(app.exec())
