"""Environmental data logger for manual weather input.

Designed for use with your own instruments such as a chronograph, wind meter,
thermometer, or barometer.
"""

import importlib
import logging

from PyQt6.QtCore import QDateTime
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.i18n import get_current_language, tr

logger = logging.getLogger(__name__)

_safe_logger_module = importlib.import_module("HjemmeladingApp.utils.safe_logger")
append_exception = getattr(_safe_logger_module, "append_exception")


class EnvironmentalLogger(QWidget):
    """Widget for logging manual weather observations."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.current_language = get_current_language() or "en"
        self.init_ui()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel(tr("environmental_logger_title", self.current_language))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel(tr("environmental_logger_subtitle", self.current_language))
        subtitle.setStyleSheet("color: gray; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Ny måling
        tabs.addTab(self.create_input_tab(), tr("input_tab", self.current_language))

        # Tab 2: Historikk
        tabs.addTab(self.create_history_tab(), tr("history_tab", self.current_language))

        # Tab 3: Sammenligning (manual vs API)
        tabs.addTab(
            self.create_comparison_tab(), tr("comparison_tab", self.current_language)
        )

        # Tab 4: Quick DA Calculator
        tabs.addTab(
            self.create_da_calculator_tab(),
            tr("da_calculator_tab", self.current_language),
        )

    def create_input_tab(self):
        """Oppretter input-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Info
        info = QLabel(
            """
        <b>Log your own measurements:</b><br>
        Use this when you have your own instruments at the range or in the field.<br>
        Data is stored and can be compared with API sources (Yr.no, OpenWeatherMap).
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Lokasjon
        location_group = QGroupBox("Location")
        location_layout = QFormLayout()
        location_group.setLayout(location_layout)

        self.location_name = QLineEdit()
        self.location_name.setPlaceholderText("e.g. Training Range, Rena, Hjerkinn...")
        location_layout.addRow("Name:", self.location_name)

        self.latitude = QDoubleSpinBox()
        self.latitude.setRange(-90, 90)
        self.latitude.setDecimals(6)
        self.latitude.setValue(59.9139)
        location_layout.addRow("Latitude:", self.latitude)

        self.longitude = QDoubleSpinBox()
        self.longitude.setRange(-180, 180)
        self.longitude.setDecimals(6)
        self.longitude.setValue(10.7522)
        location_layout.addRow("Longitude:", self.longitude)

        self.elevation = QDoubleSpinBox()
        self.elevation.setRange(0, 5000)
        self.elevation.setDecimals(1)
        self.elevation.setSuffix(" m")
        location_layout.addRow("Elevation:", self.elevation)

        layout.addWidget(location_group)

        # Tidspunkt
        time_group = QGroupBox("Timestamp")
        time_layout = QFormLayout()
        time_group.setLayout(time_layout)

        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setDateTime(QDateTime.currentDateTime())
        self.datetime_input.setCalendarPopup(True)
        time_layout.addRow("Date & time:", self.datetime_input)

        layout.addWidget(time_group)

        # Værdata
        weather_group = QGroupBox("Weather data (from your instruments)")
        weather_layout = QFormLayout()
        weather_group.setLayout(weather_layout)

        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(-50, 60)
        self.temperature.setDecimals(1)
        self.temperature.setSuffix(" °C")
        self.temperature.setValue(15.0)
        weather_layout.addRow("Temperature:", self.temperature)

        self.pressure = QDoubleSpinBox()
        self.pressure.setRange(900, 1100)
        self.pressure.setDecimals(1)
        self.pressure.setSuffix(" hPa")
        self.pressure.setValue(1013.25)
        weather_layout.addRow("Pressure:", self.pressure)

        self.humidity = QSpinBox()
        self.humidity.setRange(0, 100)
        self.humidity.setSuffix(" %")
        self.humidity.setValue(65)
        weather_layout.addRow("Humidity:", self.humidity)

        self.wind_speed = QDoubleSpinBox()
        self.wind_speed.setRange(0, 50)
        self.wind_speed.setDecimals(1)
        self.wind_speed.setSuffix(" m/s")
        self.wind_speed.setValue(0.0)
        weather_layout.addRow("Wind speed:", self.wind_speed)

        self.wind_direction = QSpinBox()
        self.wind_direction.setRange(0, 360)
        self.wind_direction.setSuffix(" °")
        self.wind_direction.setValue(0)
        weather_layout.addRow("Wind direction:", self.wind_direction)

        wind_dir_help = QLabel(
            """
        <i>Tip: 0° = North, 90° = East, 180° = South, 270° = West<br>
        Or use the clock method: 12 = North, 3 = East, 6 = South, 9 = West</i>
        """
        )
        wind_dir_help.setWordWrap(True)
        wind_dir_help.setStyleSheet("color: gray; font-size: 9pt;")
        weather_layout.addRow("", wind_dir_help)

        layout.addWidget(weather_group)

        # Density Altitude (auto eller manuell)
        da_group = QGroupBox("✈️ Density Altitude")
        da_layout = QVBoxLayout()
        da_group.setLayout(da_layout)

        da_info = QLabel(
            "Can be calculated automatically or entered manually if you have a Kestrel."
        )
        da_info.setWordWrap(True)
        da_layout.addWidget(da_info)

        da_form = QFormLayout()

        self.da_auto = QCheckBox("Calculate automatically from temp/pressure/elevation")
        self.da_auto.setChecked(True)
        self.da_auto.toggled.connect(self.toggle_da_manual)
        da_form.addRow(self.da_auto)

        self.da_manual = QDoubleSpinBox()
        self.da_manual.setRange(-3000, 15000)
        self.da_manual.setDecimals(0)
        self.da_manual.setSuffix(" ft")
        self.da_manual.setValue(0)
        self.da_manual.setEnabled(False)
        da_form.addRow("Manual DA:", self.da_manual)

        da_layout.addLayout(da_form)

        calc_da_btn = QPushButton("Calculate DA now")
        calc_da_btn.clicked.connect(self.calculate_da_preview)
        da_layout.addWidget(calc_da_btn)

        self.da_result = QLabel("DA: -- ft (-- m)")
        self.da_result.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.da_result.setStyleSheet("color: blue;")
        da_layout.addWidget(self.da_result)

        layout.addWidget(da_group)

        # Instrumenter brukt
        instruments_group = QGroupBox("Instruments used")
        instruments_layout = QFormLayout()
        instruments_group.setLayout(instruments_layout)

        self.chronograph = QLineEdit()
        self.chronograph.setPlaceholderText("e.g. Magnetospeed V3, LabRadar...")
        instruments_layout.addRow("Chronograph:", self.chronograph)

        self.anemometer = QLineEdit()
        self.anemometer.setPlaceholderText("e.g. Kestrel 5700, WeatherFlow...")
        instruments_layout.addRow("Wind meter:", self.anemometer)

        self.barometer = QLineEdit()
        self.barometer.setPlaceholderText("e.g. Kestrel, Suunto...")
        instruments_layout.addRow("Barometer:", self.barometer)

        layout.addWidget(instruments_group)

        # Notater
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        notes_group.setLayout(notes_layout)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "Additional observations:\n"
            "- Mirage level (light/moderate/heavy)\n"
            "- Wind pattern (steady/gusty)\n"
            "- Cloud cover\n"
            "- Special conditions..."
        )
        self.notes.setMaximumHeight(100)
        notes_layout.addWidget(self.notes)

        layout.addWidget(notes_group)

        # Lagre-knapp
        save_btn = QPushButton("Save measurement")
        save_btn.setMinimumHeight(50)
        save_btn.setStyleSheet(
            "font-size: 14pt; font-weight: bold; background-color: #4CAF50; color: white;"
        )
        save_btn.clicked.connect(self.save_measurement)
        layout.addWidget(save_btn)

        layout.addStretch()

        return widget

    def create_history_tab(self):
        """Oppretter historikk-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Kontroller
        controls = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_history)
        controls.addWidget(refresh_btn)

        delete_btn = QPushButton("Delete selected")
        delete_btn.clicked.connect(self.delete_selected)
        controls.addWidget(delete_btn)

        controls.addStretch()

        layout.addLayout(controls)

        # Tabell
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(11)
        self.history_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Date/Time",
                "Location",
                "Temp (°C)",
                "Pressure (hPa)",
                "Humidity (%)",
                "Wind (m/s)",
                "Direction (°)",
                "DA (ft)",
                "Instruments",
                "Notes",
            ]
        )
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)

        # Last data
        self.load_history()

        return widget

    def create_comparison_tab(self):
        """Sammenligner manuelle målinger med API-data"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            """
        <h3>Comparison: your measurements vs API data</h3>
        <p>See how large the deviations are between your instruments and weather feeds.</p>
        <p>This helps you evaluate the reliability of different data sources.</p>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Velg måling
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Select measurement:"))

        self.comparison_measurement = QComboBox()
        self.load_measurements_for_comparison()
        select_layout.addWidget(self.comparison_measurement, 1)

        compare_btn = QPushButton("Compare")
        compare_btn.clicked.connect(self.run_comparison)
        select_layout.addWidget(compare_btn)

        layout.addLayout(select_layout)

        # Resultat
        self.comparison_result = QTextEdit()
        self.comparison_result.setReadOnly(True)
        layout.addWidget(self.comparison_result)

        return widget

    def create_da_calculator_tab(self):
        """Standalone DA-kalkulator"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            """
        <h3>Density Altitude Calculator</h3>
        <p>Rask beregning av Density Altitude basert på værforhold.</p>
        <p><b>What is DA?</b> A corrected altitude that accounts for temperature and pressure.<br>
        Higher DA = thinner air = less drag = the bullet flies flatter.</p>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Quick input
        calc_group = QGroupBox("Quick Calculator")
        calc_layout = QFormLayout()
        calc_group.setLayout(calc_layout)

        self.da_calc_temp = QDoubleSpinBox()
        self.da_calc_temp.setRange(-50, 60)
        self.da_calc_temp.setDecimals(1)
        self.da_calc_temp.setSuffix(" °C")
        self.da_calc_temp.setValue(15)
        calc_layout.addRow("Temperature:", self.da_calc_temp)

        self.da_calc_pressure = QDoubleSpinBox()
        self.da_calc_pressure.setRange(900, 1100)
        self.da_calc_pressure.setDecimals(1)
        self.da_calc_pressure.setSuffix(" hPa")
        self.da_calc_pressure.setValue(1013.25)
        calc_layout.addRow("Pressure:", self.da_calc_pressure)

        self.da_calc_elevation = QDoubleSpinBox()
        self.da_calc_elevation.setRange(0, 5000)
        self.da_calc_elevation.setDecimals(0)
        self.da_calc_elevation.setSuffix(" m")
        self.da_calc_elevation.setValue(0)
        calc_layout.addRow("Elevation:", self.da_calc_elevation)

        calc_btn = QPushButton("Calculate DA")
        calc_btn.clicked.connect(self.calculate_da_standalone)
        calc_layout.addRow(calc_btn)

        layout.addWidget(calc_group)

        # Resultat
        result_group = QGroupBox("Result")
        result_layout = QVBoxLayout()
        result_group.setLayout(result_layout)

        self.da_standalone_result = QTextEdit()
        self.da_standalone_result.setReadOnly(True)
        self.da_standalone_result.setMaximumHeight(300)
        result_layout.addWidget(self.da_standalone_result)

        layout.addWidget(result_group)

        # Forklaring
        explanation = QLabel(
            """
        <h4>How to interpret DA:</h4>
        <ul>
        <li><b>Positive DA:</b> Air is thinner than standard → the bullet flies flatter</li>
        <li><b>Negative DA:</b> Air is denser than standard → the bullet drops more</li>
        <li><b>Example:</b> DA = 2000 ft means the air behaves like it does at 2000 ft elevation, even if you are at sea level</li>
        </ul>

        <h4>Practical effect:</h4>
        <ul>
    <li>Per 1000 ft DA: about 1% change in air resistance</li>
        <li>Warm summer day (DA 3000 ft): impact may be ~10 cm higher at 600 m</li>
        <li>Cold winter day (DA -1000 ft): impact may be ~3 cm lower at 600 m</li>
        </ul>
        """
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        layout.addStretch()

        return widget

    def toggle_da_manual(self, checked):
        """Bytter mellom auto og manuell DA"""
        self.da_manual.setEnabled(not checked)

    def calculate_density_altitude(self, temp_c, pressure_hpa, elevation_m):
        """Beregner Density Altitude"""
        # ISA standard
        standard_pressure = 1013.25  # hPa ved havnivå
        standard_temp = 15  # °C ved havnivå

        # Pressure altitude
        pressure_alt_ft = (
            1 - (pressure_hpa / standard_pressure) ** 0.190284
        ) * 145366.45

        # Density altitude
        da_ft = pressure_alt_ft + (120 * (temp_c - standard_temp))

        return da_ft

    def calculate_da_preview(self):
        """Forhåndsviser DA-beregning"""
        temp = self.temperature.value()
        pressure = self.pressure.value()
        elevation = self.elevation.value()

        da_ft = self.calculate_density_altitude(temp, pressure, elevation)
        da_m = da_ft * 0.3048

        self.da_result.setText(f"DA: {da_ft:.0f} ft ({da_m:.0f} m)")

        # Color code
        if da_ft > 5000:
            self.da_result.setStyleSheet("color: red; font-weight: bold;")
        elif da_ft > 2000:
            self.da_result.setStyleSheet("color: orange; font-weight: bold;")
        elif da_ft < -1000:
            self.da_result.setStyleSheet("color: blue; font-weight: bold;")
        else:
            self.da_result.setStyleSheet("color: green; font-weight: bold;")

    def calculate_da_standalone(self):
        """Beregner DA i standalone-kalkulator"""
        temp = self.da_calc_temp.value()
        pressure = self.da_calc_pressure.value()
        elevation = self.da_calc_elevation.value()

        da_ft = self.calculate_density_altitude(temp, pressure, elevation)
        da_m = da_ft * 0.3048

        # ISA standard
        standard_pressure = 1013.25
        _standard_temp = 15

        # Pressure altitude
        pressure_alt_ft = (1 - (pressure / standard_pressure) ** 0.190284) * 145366.45

        result_html = f"""
<h2>Density Altitude Result</h2>

<h3>Input:</h3>
<table style='width: 100%;'>
<tr><td><b>Temperature:</b></td><td>{temp:.1f} °C</td></tr>
<tr><td><b>Pressure:</b></td><td>{pressure:.1f} hPa</td></tr>
<tr><td><b>Actual elevation:</b></td><td>{elevation:.0f} m ({elevation * 3.28084:.0f} ft)</td></tr>
</table>

<h3>Calculated:</h3>
<table style='width: 100%;'>
<tr><td><b>Pressure Altitude:</b></td><td>{pressure_alt_ft:.0f} ft ({pressure_alt_ft * 0.3048:.0f} m)</td></tr>
<tr><td><b>Density Altitude:</b></td><td style='color: blue; font-size: 16pt;'><b>{da_ft:.0f} ft ({da_m:.0f} m)</b></td></tr>
<tr><td><b>Difference vs elevation:</b></td><td>{da_ft - (elevation * 3.28084):.0f} ft</td></tr>
</table>

<h3>Ballistic effect:</h3>
<p>Compared with standard atmosphere (15°C, 1013 hPa):</p>
<ul>
"""

        if da_ft > 5000:
            result_html += """
<li style='color: red;'><b>HIGH DA:</b> Significantly thinner air</li>
<li>Impact will be <b>higher</b> than normal (less drag)</li>
<li>Estimate: ~{:.1f}% reduced drag</li>
<li><b>Tip:</b> Hold slightly lower than normal, especially at longer range</li>
""".format(
                (da_ft / 1000)
            )
        elif da_ft > 2000:
            result_html += """
<li style='color: orange;'><b>MODERATE DA:</b> Somewhat thinner air</li>
<li>Impact will be <b>slightly higher</b> than normal</li>
<li>Estimate: ~{:.1f}% reduced drag</li>
<li><b>Tip:</b> Small corrections may be needed</li>
""".format(
                (da_ft / 1000)
            )
        elif da_ft < -1000:
            result_html += """
<li style='color: blue;'><b>LOW DA:</b> Denser air</li>
<li>Impact will be <b>lower</b> than normal (more drag)</li>
<li>Estimate: ~{:.1f}% increased drag</li>
<li><b>Tip:</b> Hold slightly higher than normal</li>
""".format(
                abs(da_ft / 1000)
            )
        else:
            result_html += """
<li style='color: green;'><b>NORMAL DA:</b> Close to standard atmosphere</li>
<li>Minimal ballistic effect</li>
<li>Use standard DOPE data</li>
"""

        result_html += """
</ul>

<h4>Practical example (600 m shooting):</h4>
<p>At DA = {:.0f} ft versus standard (DA = 0):<br>
Estimated vertical impact difference: <b>~{:.1f} cm</b></p>
""".format(
            da_ft, (da_ft / 1000) * 10
        )  # Rough estimate: 10cm per 1000ft DA at 600m

        self.da_standalone_result.setHtml(result_html)

    def save_measurement(self):
        """Lagrer måling til database"""
        # Valider
        if not self.location_name.text():
            QMessageBox.warning(self, "Missing data", "Enter a location name first.")
            return

        # Beregn DA
        temp = self.temperature.value()
        pressure = self.pressure.value()
        elevation = self.elevation.value()

        if self.da_auto.isChecked():
            da_ft = self.calculate_density_altitude(temp, pressure, elevation)
        else:
            da_ft = self.da_manual.value()

        # Sett sammen instrumenter
        instruments = []
        if self.chronograph.text():
            instruments.append(f"Chronograph: {self.chronograph.text()}")
        if self.anemometer.text():
            instruments.append(f"Wind meter: {self.anemometer.text()}")
        if self.barometer.text():
            instruments.append(f"Barometer: {self.barometer.text()}")
        instruments_str = " | ".join(instruments) if instruments else "None specified"

        # Lagre
        try:
            self.db.execute_query(
                """
                INSERT INTO environmental_data
                (datetime, location_name, latitude, longitude, elevation_m,
                 temperature_c, pressure_hpa, humidity_percent,
                 wind_speed_ms, wind_direction_deg, density_altitude_ft,
                 instruments, notes, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.datetime_input.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
                    self.location_name.text(),
                    self.latitude.value(),
                    self.longitude.value(),
                    elevation,
                    temp,
                    pressure,
                    self.humidity.value(),
                    self.wind_speed.value(),
                    self.wind_direction.value(),
                    da_ft,
                    instruments_str,
                    self.notes.toPlainText(),
                    "MANUAL",
                ),
            )

            QMessageBox.information(
                self,
                "Saved",
                f"Measurement saved.\n\nDA: {da_ft:.0f} ft\n\nData can now be compared with API sources.",
            )

            # Refresh history
            self.load_history()

            # Reset a few fields
            self.notes.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save: {str(e)}")

    def load_history(self):
        """Laster historikk"""
        try:
            data = self.db.execute_query(
                """
                SELECT id, datetime, location_name, temperature_c, pressure_hpa,
                       humidity_percent, wind_speed_ms, wind_direction_deg,
                       density_altitude_ft, instruments, notes
                FROM environmental_data
                WHERE data_source = 'MANUAL'
                ORDER BY datetime DESC
                LIMIT 100
            """
            )

            self.history_table.setRowCount(len(data))

            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.history_table.setItem(row_idx, col_idx, item)

            self.history_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load history: {str(e)}")

    def delete_selected(self):
        """Sletter valgt rad"""
        current_row = self.history_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self,
                tr("msg_no_selection", self.current_language),
                tr("msg_select_first", self.current_language),
            )
            return

        measurement_id = self.history_table.item(current_row, 0).text()

        reply = QMessageBox.question(
            self,
            tr("msg_confirm_delete", self.current_language),
            tr(
                "environmental_confirm_delete_measurement",
                self.current_language,
                measurement_id=measurement_id,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query(
                    "DELETE FROM environmental_data WHERE id = ?", (measurement_id,)
                )
                self.load_history()
                QMessageBox.information(
                    self,
                    tr("msg_deleted", self.current_language),
                    tr("environmental_measurement_deleted", self.current_language),
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr("msg_error", self.current_language),
                    tr(
                        "environmental_delete_failed",
                        self.current_language,
                        error=str(e),
                    ),
                )

    def load_measurements_for_comparison(self):
        """Laster målinger for sammenligning"""
        try:
            data = self.db.execute_query(
                """
                SELECT id, datetime, location_name
                FROM environmental_data
                WHERE data_source = 'MANUAL'
                ORDER BY datetime DESC
                LIMIT 50
            """
            )

            self.comparison_measurement.clear()
            for row in data:
                measurement_id, dt, location = row
                self.comparison_measurement.addItem(
                    f"{dt} - {location}", measurement_id
                )
        except Exception as e:
            logger.debug(
                "Failed to load measurements for comparison: %s", e, exc_info=True
            )
            try:
                append_exception("Failed to load measurements for comparison", e)
            except Exception:
                pass

    def run_comparison(self):
        """Kjører sammenligning mot API-data"""
        measurement_id = self.comparison_measurement.currentData()

        if not measurement_id:
            QMessageBox.warning(
                self,
                tr("msg_no_selection", self.current_language),
                tr("environmental_select_measurement_first", self.current_language),
            )
            return

        try:
            # Hent manuell måling
            manual = self.db.execute_query(
                """
                SELECT datetime, location_name, latitude, longitude,
                       temperature_c, pressure_hpa, humidity_percent,
                       wind_speed_ms, wind_direction_deg, density_altitude_ft
                FROM environmental_data
                WHERE id = ?
            """,
                (measurement_id,),
            )

            if not manual:
                QMessageBox.warning(
                    self,
                    "Measurement Missing",
                    "The selected measurement no longer exists in the database.",
                )
                self.load_measurements_for_comparison()
                return

            manual = manual[0]
            dt, location, lat, lon, temp, press, humid, wind_speed, wind_dir, da = (
                manual
            )

            # Hent Yr.no data (hvis tilgjengelig)
            # For nå: Simuler at vi ikke har API-data

            result_html = f"""
<h2>Comparison: manual vs API</h2>

<h3>Location: {location}</h3>
<p>Timestamp: {dt}<br>
Coordinates: {lat:.4f}, {lon:.4f}</p>

<h3>Your measurements (MANUAL):</h3>
<table style='width: 100%; border: 1px solid #ddd;'>
<tr style='background-color: #f0f0f0;'><th>Parameter</th><th>Value</th></tr>
<tr><td>Temperature</td><td>{temp:.1f} °C</td></tr>
<tr><td>Pressure</td><td>{press:.1f} hPa</td></tr>
<tr><td>Humidity</td><td>{humid} %</td></tr>
<tr><td>Wind speed</td><td>{wind_speed:.1f} m/s</td></tr>
<tr><td>Wind direction</td><td>{wind_dir}°</td></tr>
<tr><td>Density Altitude</td><td>{da:.0f} ft</td></tr>
</table>

<h3>API-data (Yr.no):</h3>
<p style='color: orange;'><i>API integration is planned for a later version.</i></p>
<p>For now, compare manually against yr.no or other weather stations.</p>

<h3>Typical deviations:</h3>
<ul>
<li><b>Temperature:</b> ±2°C (weather stations are often several km away)</li>
<li><b>Pressure:</b> ±5 hPa (elevation correction may be inaccurate)</li>
<li><b>Wind:</b> ±30% (microclimate varies a lot)</li>
<li><b>Humidity:</b> ±10%</li>
</ul>

<h3>Tips:</h3>
<ul>
<li>Your own measurements are <b>always</b> the most accurate for your location</li>
<li>Use API data as a <b>backup</b> or for planning</li>
<li>Kestrel instruments are the gold standard for field measurements</li>
<li>Always log DA. It is the most important single environmental input for ballistics.</li>
</ul>
            """

            self.comparison_result.setHtml(result_html)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Comparison failed: {str(e)}")
