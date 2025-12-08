"""
Environmental Data Logger - Manuell input av værdata
For bruk med egne instrumenter: Kronograf, vindmåler, termometer, barometer
"""

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

from src.database.database import get_database
from src.utils.i18n import tr

logger = logging.getLogger(__name__)
from HjemmeladingApp.utils.safe_logger import append_exception


class EnvironmentalLogger(QWidget):
    """Widget for logging av manuelle værdata"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.current_language = "no"  # Default språk
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
        <b>Logg dine egne målinger:</b><br>
        Bruk dette når du har egne instrumenter på skytebanen eller i felt.<br>
        Data lagres og kan sammenlignes med API-data (Yr.no, OpenWeatherMap).
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Lokasjon
        location_group = QGroupBox("📍 Lokasjon")
        location_layout = QFormLayout()
        location_group.setLayout(location_layout)

        self.location_name = QLineEdit()
        self.location_name.setPlaceholderText("F.eks: Øvingsfeltet, Rena, Hjerkinn...")
        location_layout.addRow("Navn:", self.location_name)

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
        time_group = QGroupBox("🕐 Tidspunkt")
        time_layout = QFormLayout()
        time_group.setLayout(time_layout)

        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setDateTime(QDateTime.currentDateTime())
        self.datetime_input.setCalendarPopup(True)
        time_layout.addRow("Dato & tid:", self.datetime_input)

        layout.addWidget(time_group)

        # Værdata
        weather_group = QGroupBox("🌦️ Værdata (Fra dine instrumenter)")
        weather_layout = QFormLayout()
        weather_group.setLayout(weather_layout)

        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(-50, 60)
        self.temperature.setDecimals(1)
        self.temperature.setSuffix(" °C")
        self.temperature.setValue(15.0)
        weather_layout.addRow("🌡️ Temperatur:", self.temperature)

        self.pressure = QDoubleSpinBox()
        self.pressure.setRange(900, 1100)
        self.pressure.setDecimals(1)
        self.pressure.setSuffix(" hPa")
        self.pressure.setValue(1013.25)
        weather_layout.addRow("🔽 Lufttrykk:", self.pressure)

        self.humidity = QSpinBox()
        self.humidity.setRange(0, 100)
        self.humidity.setSuffix(" %")
        self.humidity.setValue(65)
        weather_layout.addRow("💧 Luftfuktighet:", self.humidity)

        self.wind_speed = QDoubleSpinBox()
        self.wind_speed.setRange(0, 50)
        self.wind_speed.setDecimals(1)
        self.wind_speed.setSuffix(" m/s")
        self.wind_speed.setValue(0.0)
        weather_layout.addRow("🌬️ Vindhastighet:", self.wind_speed)

        self.wind_direction = QSpinBox()
        self.wind_direction.setRange(0, 360)
        self.wind_direction.setSuffix(" °")
        self.wind_direction.setValue(0)
        weather_layout.addRow("🧭 Vindretning:", self.wind_direction)

        wind_dir_help = QLabel(
            """
        <i>Tips: 0° = Nord, 90° = Øst, 180° = Sør, 270° = Vest<br>
        Eller bruk klokke-metoden: 12 = Nord, 3 = Øst, 6 = Sør, 9 = Vest</i>
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
            "Kan beregnes automatisk eller legges inn manuelt hvis du har Kestrel."
        )
        da_info.setWordWrap(True)
        da_layout.addWidget(da_info)

        da_form = QFormLayout()

        self.da_auto = QCheckBox("Beregn automatisk fra temp/trykk/elevation")
        self.da_auto.setChecked(True)
        self.da_auto.toggled.connect(self.toggle_da_manual)
        da_form.addRow(self.da_auto)

        self.da_manual = QDoubleSpinBox()
        self.da_manual.setRange(-3000, 15000)
        self.da_manual.setDecimals(0)
        self.da_manual.setSuffix(" ft")
        self.da_manual.setValue(0)
        self.da_manual.setEnabled(False)
        da_form.addRow("DA manuell:", self.da_manual)

        da_layout.addLayout(da_form)

        calc_da_btn = QPushButton("🧮 Beregn DA nå")
        calc_da_btn.clicked.connect(self.calculate_da_preview)
        da_layout.addWidget(calc_da_btn)

        self.da_result = QLabel("DA: -- ft (-- m)")
        self.da_result.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.da_result.setStyleSheet("color: blue;")
        da_layout.addWidget(self.da_result)

        layout.addWidget(da_group)

        # Instrumenter brukt
        instruments_group = QGroupBox("🔧 Instrumenter brukt")
        instruments_layout = QFormLayout()
        instruments_group.setLayout(instruments_layout)

        self.chronograph = QLineEdit()
        self.chronograph.setPlaceholderText("F.eks: Magnetospeed V3, LabRadar...")
        instruments_layout.addRow("Kronograf:", self.chronograph)

        self.anemometer = QLineEdit()
        self.anemometer.setPlaceholderText("F.eks: Kestrel 5700, WeatherFlow...")
        instruments_layout.addRow("Vindmåler:", self.anemometer)

        self.barometer = QLineEdit()
        self.barometer.setPlaceholderText("F.eks: Kestrel, Suunto...")
        instruments_layout.addRow("Barometer:", self.barometer)

        layout.addWidget(instruments_group)

        # Notater
        notes_group = QGroupBox("📝 Notater")
        notes_layout = QVBoxLayout()
        notes_group.setLayout(notes_layout)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "Ekstra observasjoner:\n"
            "- Mirage nivå (lett/moderat/kraftig)\n"
            "- Vindforhold (steady/gusty)\n"
            "- Skydekke\n"
            "- Spesielle forhold..."
        )
        self.notes.setMaximumHeight(100)
        notes_layout.addWidget(self.notes)

        layout.addWidget(notes_group)

        # Lagre-knapp
        save_btn = QPushButton("💾 Lagre måling")
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

        refresh_btn = QPushButton("🔄 Oppdater")
        refresh_btn.clicked.connect(self.load_history)
        controls.addWidget(refresh_btn)

        delete_btn = QPushButton("🗑️ Slett valgt")
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
                "Dato/Tid",
                "Lokasjon",
                "Temp (°C)",
                "Trykk (hPa)",
                "Fuktighet (%)",
                "Vind (m/s)",
                "Retning (°)",
                "DA (ft)",
                "Instrumenter",
                "Notater",
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
        <h3>⚖️ Sammenligning: Dine målinger vs API-data</h3>
        <p>Se hvor store avvik det er mellom dine instrumenter og værvarslinger.</p>
        <p>Dette hjelper deg å vurdere påliteligheten til forskjellige datakilder.</p>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Velg måling
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Velg måling:"))

        self.comparison_measurement = QComboBox()
        self.load_measurements_for_comparison()
        select_layout.addWidget(self.comparison_measurement, 1)

        compare_btn = QPushButton("🔍 Sammenlign")
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
        <h3>🧮 Density Altitude Calculator</h3>
        <p>Rask beregning av Density Altitude basert på værforhold.</p>
        <p><b>Hva er DA?</b> "Korrigert høyde" som tar hensyn til temp og trykk.<br>
        Høyere DA = tynnere luft = mindre luftmotstand = kulen flyr raskere.</p>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Quick input
        calc_group = QGroupBox("📊 Quick Calculator")
        calc_layout = QFormLayout()
        calc_group.setLayout(calc_layout)

        self.da_calc_temp = QDoubleSpinBox()
        self.da_calc_temp.setRange(-50, 60)
        self.da_calc_temp.setDecimals(1)
        self.da_calc_temp.setSuffix(" °C")
        self.da_calc_temp.setValue(15)
        calc_layout.addRow("Temperatur:", self.da_calc_temp)

        self.da_calc_pressure = QDoubleSpinBox()
        self.da_calc_pressure.setRange(900, 1100)
        self.da_calc_pressure.setDecimals(1)
        self.da_calc_pressure.setSuffix(" hPa")
        self.da_calc_pressure.setValue(1013.25)
        calc_layout.addRow("Lufttrykk:", self.da_calc_pressure)

        self.da_calc_elevation = QDoubleSpinBox()
        self.da_calc_elevation.setRange(0, 5000)
        self.da_calc_elevation.setDecimals(0)
        self.da_calc_elevation.setSuffix(" m")
        self.da_calc_elevation.setValue(0)
        calc_layout.addRow("Elevation:", self.da_calc_elevation)

        calc_btn = QPushButton("➡️ Beregn DA")
        calc_btn.clicked.connect(self.calculate_da_standalone)
        calc_layout.addRow(calc_btn)

        layout.addWidget(calc_group)

        # Resultat
        result_group = QGroupBox("📈 Resultat")
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
        <h4>📚 Hvordan tolke DA:</h4>
        <ul>
        <li><b>Positiv DA:</b> Luft tynnere enn standard → kulen flyr lengre</li>
        <li><b>Negativ DA:</b> Luft tettere enn standard → kulen flyr kortere</li>
        <li><b>Eksempel:</b> DA = 2000 ft betyr at lufta oppfører seg som på 2000 ft høyde (selv om du er på havnivå)</li>
        </ul>

        <h4>⚠️ Praktisk påvirkning:</h4>
        <ul>
        <li>Per 1000 ft DA: ~1% endring i luftmotstand</li>
        <li>Varm sommerdag (DA 3000 ft): Kulen treffer ~10 cm høyere ved 600m</li>
        <li>Kald vinterdag (DA -1000 ft): Kulen treffer ~3 cm lavere ved 600m</li>
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
<h2>📊 Density Altitude Resultat</h2>

<h3>Input:</h3>
<table style='width: 100%;'>
<tr><td><b>Temperatur:</b></td><td>{temp:.1f} °C</td></tr>
<tr><td><b>Lufttrykk:</b></td><td>{pressure:.1f} hPa</td></tr>
<tr><td><b>Faktisk elevation:</b></td><td>{elevation:.0f} m ({elevation * 3.28084:.0f} ft)</td></tr>
</table>

<h3>Beregnet:</h3>
<table style='width: 100%;'>
<tr><td><b>Pressure Altitude:</b></td><td>{pressure_alt_ft:.0f} ft ({pressure_alt_ft * 0.3048:.0f} m)</td></tr>
<tr><td><b>Density Altitude:</b></td><td style='color: blue; font-size: 16pt;'><b>{da_ft:.0f} ft ({da_m:.0f} m)</b></td></tr>
<tr><td><b>Differanse vs elevation:</b></td><td>{da_ft - (elevation * 3.28084):.0f} ft</td></tr>
</table>

<h3>🎯 Ballistisk effekt:</h3>
<p>Sammenlignet med standard atmosfære (15°C, 1013 hPa):</p>
<ul>
"""

        if da_ft > 5000:
            result_html += """
<li style='color: red;'><b>HØYT DA:</b> Betydelig tynnere luft</li>
<li>Kulen treffer <b>høyere</b> enn normalt (mindre luftmotstand)</li>
<li>Estimat: ~{:.1f}% redusert luftmotstand</li>
<li><b>Tips:</b> Hold litt lavere enn normalt, spesielt på lange hold</li>
""".format(
                (da_ft / 1000)
            )
        elif da_ft > 2000:
            result_html += """
<li style='color: orange;'><b>MODERAT DA:</b> Noe tynnere luft</li>
<li>Kulen treffer <b>litt høyere</b> enn normalt</li>
<li>Estimat: ~{:.1f}% redusert luftmotstand</li>
<li><b>Tips:</b> Små justeringer nødvendig</li>
""".format(
                (da_ft / 1000)
            )
        elif da_ft < -1000:
            result_html += """
<li style='color: blue;'><b>LAVT DA:</b> Tettere luft</li>
<li>Kulen treffer <b>lavere</b> enn normalt (mer luftmotstand)</li>
<li>Estimat: ~{:.1f}% økt luftmotstand</li>
<li><b>Tips:</b> Hold litt høyere enn normalt</li>
""".format(
                abs(da_ft / 1000)
            )
        else:
            result_html += """
<li style='color: green;'><b>NORMALT DA:</b> Nær standard atmosfære</li>
<li>Minimal påvirkning på ballistikk</li>
<li>Bruk standard DOPE-data</li>
"""

        result_html += """
</ul>

<h4>📐 Praktisk eksempel (600m skyting):</h4>
<p>Ved DA = {:.0f} ft vs standard (DA = 0):<br>
Forskjell i vertikal treffpunkt: <b>~{:.1f} cm</b></p>
""".format(
            da_ft, (da_ft / 1000) * 10
        )  # Rough estimate: 10cm per 1000ft DA at 600m

        self.da_standalone_result.setHtml(result_html)

    def save_measurement(self):
        """Lagrer måling til database"""
        # Valider
        if not self.location_name.text():
            QMessageBox.warning(self, "Mangler data", "Fyll inn lokasjonsnavn!")
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
            instruments.append(f"Kronograf: {self.chronograph.text()}")
        if self.anemometer.text():
            instruments.append(f"Vindmåler: {self.anemometer.text()}")
        if self.barometer.text():
            instruments.append(f"Barometer: {self.barometer.text()}")
        instruments_str = (
            " | ".join(instruments) if instruments else "Ingen spesifisert"
        )

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
                "Lagret!",
                f"Måling lagret!\n\nDA: {da_ft:.0f} ft\n\nData kan nå sammenlignes med API-kilder.",
            )

            # Oppdater historikk
            self.load_history()

            # Reset noen felter
            self.notes.clear()

        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Kunne ikke lagre: {str(e)}")

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
            QMessageBox.warning(self, "Feil", f"Kunne ikke laste historikk: {str(e)}")

    def delete_selected(self):
        """Sletter valgt rad"""
        current_row = self.history_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en rad først!")
            return

        measurement_id = self.history_table.item(current_row, 0).text()

        reply = QMessageBox.question(
            self,
            "Bekreft sletting",
            f"Slette måling ID {measurement_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query(
                    "DELETE FROM environmental_data WHERE id = ?", (measurement_id,)
                )
                self.load_history()
                QMessageBox.information(self, "Slettet", "Måling slettet!")
            except Exception as e:
                QMessageBox.critical(self, "Feil", f"Kunne ikke slette: {str(e)}")

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
            QMessageBox.warning(self, "Ingen valgt", "Velg en måling først!")
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
                return

            manual = manual[0]
            dt, location, lat, lon, temp, press, humid, wind_speed, wind_dir, da = (
                manual
            )

            # Hent Yr.no data (hvis tilgjengelig)
            # For nå: Simuler at vi ikke har API-data

            result_html = f"""
<h2>⚖️ Sammenligning: Manuell vs API</h2>

<h3>📍 Lokasjon: {location}</h3>
<p>Tidspunkt: {dt}<br>
Koordinater: {lat:.4f}, {lon:.4f}</p>

<h3>🌡️ Dine målinger (MANUAL):</h3>
<table style='width: 100%; border: 1px solid #ddd;'>
<tr style='background-color: #f0f0f0;'><th>Parameter</th><th>Verdi</th></tr>
<tr><td>Temperatur</td><td>{temp:.1f} °C</td></tr>
<tr><td>Lufttrykk</td><td>{press:.1f} hPa</td></tr>
<tr><td>Luftfuktighet</td><td>{humid} %</td></tr>
<tr><td>Vindhastighet</td><td>{wind_speed:.1f} m/s</td></tr>
<tr><td>Vindretning</td><td>{wind_dir}°</td></tr>
<tr><td>Density Altitude</td><td>{da:.0f} ft</td></tr>
</table>

<h3>☁️ API-data (Yr.no):</h3>
<p style='color: orange;'><i>⚠️ API-integrasjon kommer i neste versjon.</i></p>
<p>For nå kan du sammenligne manuelt mot yr.no eller andre værstasjoner.</p>

<h3>📊 Typiske avvik:</h3>
<ul>
<li><b>Temperatur:</b> ±2°C (værstasjoner er ofte noen km unna)</li>
<li><b>Lufttrykk:</b> ±5 hPa (høyde-korreksjon kan være unøyaktig)</li>
<li><b>Vind:</b> ±30% (mikro-klima varierer mye!)</li>
<li><b>Fuktighet:</b> ±10%</li>
</ul>

<h3>💡 Tips:</h3>
<ul>
<li>Dine egne målinger er <b>alltid</b> mest nøyaktige for DIN lokasjon</li>
<li>Bruk API-data som <b>backup</b> eller for planlegging</li>
<li>Kestrel-instrumenter er gold standard for felt-målinger</li>
<li>Logg alltid DA - det er viktigste parameter for ballistikk!</li>
</ul>
            """

            self.comparison_result.setHtml(result_html)

        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Sammenligning feilet: {str(e)}")
