"""
Drop Chart Generator & Wind Drift Calculator
Genererer drop tables og DOPE cards med PDF export
"""

import math
from datetime import datetime

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
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
from src.utils.ballistics import BallisticsCalculator
from src.utils.i18n import tr


class DropChartGenerator(QWidget):
    """Widget for drop chart generering og wind drift beregning"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.ballistics_calc = BallisticsCalculator()
        self.current_language = "no"  # Default språk
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Tittel
        title = QLabel(tr("drop_chart_title", self.current_language))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        subtitle = QLabel(tr("drop_chart_subtitle", self.current_language))
        subtitle.setStyleSheet("color: gray; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Drop Chart
        tabs.addTab(
            self.create_drop_chart_tab(), tr("drop_chart_tab", self.current_language)
        )

        # Tab 2: Wind Drift
        tabs.addTab(
            self.create_wind_drift_tab(), tr("wind_drift_tab", self.current_language)
        )

        # Tab 3: Combined DOPE Card
        tabs.addTab(
            self.create_dope_card_tab(), tr("dope_card_tab", self.current_language)
        )

    def create_drop_chart_tab(self):
        """Oppretter drop chart tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Input seksjon
        input_group = QGroupBox("⚙️ Innstillinger")
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        # Ammunisjon
        self.drop_ammo = QComboBox()
        self.drop_ammo.addItem("Velg ammunisjon...", None)
        self.load_ammo_profiles(self.drop_ammo)
        self.drop_ammo.currentIndexChanged.connect(self.on_ammo_selected)
        input_layout.addRow("Ammunisjon:", self.drop_ammo)

        # Zero distance
        self.drop_zero = QSpinBox()
        self.drop_zero.setRange(25, 500)
        self.drop_zero.setValue(100)
        self.drop_zero.setSuffix(" m")
        self.drop_zero.valueChanged.connect(self.on_ammo_selected)
        input_layout.addRow("Zero-distanse:", self.drop_zero)

        # Distanse-område
        dist_layout = QHBoxLayout()

        self.drop_start = QSpinBox()
        self.drop_start.setRange(0, 2000)
        self.drop_start.setValue(100)
        self.drop_start.setSuffix(" m")
        dist_layout.addWidget(QLabel("Fra:"))
        dist_layout.addWidget(self.drop_start)

        self.drop_end = QSpinBox()
        self.drop_end.setRange(0, 2000)
        self.drop_end.setValue(1000)
        self.drop_end.setSuffix(" m")
        dist_layout.addWidget(QLabel("Til:"))
        dist_layout.addWidget(self.drop_end)

        self.drop_step = QSpinBox()
        self.drop_step.setRange(10, 200)
        self.drop_step.setValue(50)
        self.drop_step.setSuffix(" m")
        dist_layout.addWidget(QLabel("Steg:"))
        dist_layout.addWidget(self.drop_step)

        input_layout.addRow("Distanse-område:", dist_layout)

        # Enheter
        self.drop_units = QComboBox()
        self.drop_units.addItems(["MOA", "MRAD", "CM", "INCHES"])
        input_layout.addRow("Enhet:", self.drop_units)

        # Inkluder ekstra data
        self.drop_include_velocity = QCheckBox("Vis hastighet")
        self.drop_include_velocity.setChecked(True)
        input_layout.addRow(self.drop_include_velocity)

        self.drop_include_energy = QCheckBox("Vis energi")
        self.drop_include_energy.setChecked(True)
        input_layout.addRow(self.drop_include_energy)

        self.drop_include_tof = QCheckBox("Vis time of flight")
        self.drop_include_tof.setChecked(True)
        input_layout.addRow(self.drop_include_tof)

        layout.addWidget(input_group)

        # 🎯 KIKKERT JUSTERING - Sammenligning med forrige ladning
        self.scope_adjustment_group = QGroupBox(
            "🎯 KIKKERT JUSTERING (vs. forrige ladning)"
        )
        self.scope_adjustment_group.setStyleSheet(
            """
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        )
        scope_layout = QVBoxLayout()
        self.scope_adjustment_group.setLayout(scope_layout)

        self.scope_adjustment_label = QLabel(
            "Velg ammunisjon for å se sammenligning med forrige ladning for samme rifle."
        )
        self.scope_adjustment_label.setWordWrap(True)
        self.scope_adjustment_label.setStyleSheet(
            "color: #856404; font-weight: normal; padding: 10px;"
        )
        scope_layout.addWidget(self.scope_adjustment_label)

        self.scope_adjustment_group.setVisible(False)
        layout.addWidget(self.scope_adjustment_group)

        # Generer-knapp
        generate_btn = QPushButton("📊 Generer Drop Chart")
        generate_btn.setMinimumHeight(50)
        generate_btn.setStyleSheet(
            "font-size: 14pt; font-weight: bold; background-color: #2196F3; color: white;"
        )
        generate_btn.clicked.connect(self.generate_drop_chart)
        layout.addWidget(generate_btn)

        # Resultat-tabell
        self.drop_table = QTableWidget()
        layout.addWidget(self.drop_table)

        # Export-knapper
        export_layout = QHBoxLayout()

        export_csv_btn = QPushButton("💾 Export CSV")
        export_csv_btn.clicked.connect(lambda: self.export_drop_chart("csv"))
        export_layout.addWidget(export_csv_btn)

        export_pdf_btn = QPushButton("📄 Export PDF")
        export_pdf_btn.clicked.connect(lambda: self.export_drop_chart("pdf"))
        export_layout.addWidget(export_pdf_btn)

        print_btn = QPushButton("🖨️ Print")
        print_btn.clicked.connect(self.print_drop_chart)
        export_layout.addWidget(print_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

        return widget

    def create_wind_drift_tab(self):
        """Oppretter wind drift tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Info
        info = QLabel(
            """
        <b>Wind Drift Calculator:</b><br>
        Beregner lateral drift basert på vindforhold.<br>
        <i>Tips: Full-value wind = 90° til skuddretning (maksimal effekt)</i>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Input seksjon
        input_group = QGroupBox("⚙️ Innstillinger")
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        # Ammunisjon
        self.wind_ammo = QComboBox()
        self.wind_ammo.addItem("Velg ammunisjon...", None)
        self.load_ammo_profiles(self.wind_ammo)
        input_layout.addRow("Ammunisjon:", self.wind_ammo)

        # Distanse
        self.wind_distance = QSpinBox()
        self.wind_distance.setRange(100, 2000)
        self.wind_distance.setValue(600)
        self.wind_distance.setSuffix(" m")
        input_layout.addRow("Distanse:", self.wind_distance)

        # Vind-hastigheter
        wind_speeds_layout = QHBoxLayout()

        self.wind_speed_1 = QDoubleSpinBox()
        self.wind_speed_1.setRange(0, 30)
        self.wind_speed_1.setValue(2.5)
        self.wind_speed_1.setSuffix(" m/s")
        wind_speeds_layout.addWidget(QLabel("Vind 1:"))
        wind_speeds_layout.addWidget(self.wind_speed_1)

        self.wind_speed_2 = QDoubleSpinBox()
        self.wind_speed_2.setRange(0, 30)
        self.wind_speed_2.setValue(5.0)
        self.wind_speed_2.setSuffix(" m/s")
        wind_speeds_layout.addWidget(QLabel("Vind 2:"))
        wind_speeds_layout.addWidget(self.wind_speed_2)

        self.wind_speed_3 = QDoubleSpinBox()
        self.wind_speed_3.setRange(0, 30)
        self.wind_speed_3.setValue(10.0)
        self.wind_speed_3.setSuffix(" m/s")
        wind_speeds_layout.addWidget(QLabel("Vind 3:"))
        wind_speeds_layout.addWidget(self.wind_speed_3)

        input_layout.addRow("Vind-hastigheter:", wind_speeds_layout)

        # Vindretning (relativ til skudd)
        self.wind_angle = QSpinBox()
        self.wind_angle.setRange(0, 180)
        self.wind_angle.setValue(90)
        self.wind_angle.setSuffix(" °")
        input_layout.addRow("Vindvinkel:", self.wind_angle)

        wind_angle_help = QLabel(
            """
        <i>0° = Headwind/Tailwind (ingen lateral drift)<br>
        90° = Full-value crosswind (maksimal drift)<br>
        45° = Half-value crosswind (~70% drift)</i>
        """
        )
        wind_angle_help.setWordWrap(True)
        wind_angle_help.setStyleSheet("color: gray; font-size: 9pt;")
        input_layout.addRow("", wind_angle_help)

        # Quick presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Quick:"))

        for angle, label in [(0, "Head/Tail"), (45, "Half-value"), (90, "Full-value")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, a=angle: self.wind_angle.setValue(a))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        input_layout.addRow(preset_layout)

        layout.addWidget(input_group)

        # Generer-knapp
        calc_wind_btn = QPushButton("🌬️ Beregn Wind Drift")
        calc_wind_btn.setMinimumHeight(50)
        calc_wind_btn.setStyleSheet(
            "font-size: 14pt; font-weight: bold; background-color: #4CAF50; color: white;"
        )
        calc_wind_btn.clicked.connect(self.calculate_wind_drift)
        layout.addWidget(calc_wind_btn)

        # Resultat
        self.wind_result = QTextEdit()
        self.wind_result.setReadOnly(True)
        layout.addWidget(self.wind_result)

        return widget

    def create_dope_card_tab(self):
        """Oppretter kombinert DOPE card"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            """
        <h3>🎯 DOPE Card Generator</h3>
        <p><b>DOPE</b> = Data On Previous Engagement</p>
        <p>Kombinert drop chart + wind drift i ett kompakt format.<br>
        Perfekt for å laminere og ta med på jakt/konkurranse!</p>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Input
        input_group = QGroupBox("⚙️ Innstillinger")
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        self.dope_ammo = QComboBox()
        self.dope_ammo.addItem("Velg ammunisjon...", None)
        self.load_ammo_profiles(self.dope_ammo)
        input_layout.addRow("Ammunisjon:", self.dope_ammo)

        self.dope_rifle = QLineEdit()
        self.dope_rifle.setPlaceholderText("F.eks: Tikka T3X .308")
        input_layout.addRow("Rifle:", self.dope_rifle)

        self.dope_scope = QLineEdit()
        self.dope_scope.setPlaceholderText("F.eks: Vortex Viper PST 5-25x50")
        input_layout.addRow("Optikk:", self.dope_scope)

        self.dope_zero = QSpinBox()
        self.dope_zero.setRange(25, 500)
        self.dope_zero.setValue(100)
        self.dope_zero.setSuffix(" m")
        input_layout.addRow("Zero:", self.dope_zero)

        layout.addWidget(input_group)

        # Generer
        generate_dope_btn = QPushButton("📋 Generer DOPE Card")
        generate_dope_btn.setMinimumHeight(50)
        generate_dope_btn.setStyleSheet(
            "font-size: 14pt; font-weight: bold; background-color: #FF9800; color: white;"
        )
        generate_dope_btn.clicked.connect(self.generate_dope_card)
        layout.addWidget(generate_dope_btn)

        # Preview
        self.dope_preview = QTextEdit()
        self.dope_preview.setReadOnly(True)
        layout.addWidget(self.dope_preview)

        # Export
        export_dope_btn = QPushButton("📄 Export DOPE som PDF")
        export_dope_btn.clicked.connect(self.export_dope_pdf)
        layout.addWidget(export_dope_btn)

        return widget

    def load_ammo_profiles(self, combo_widget):
        """Laster ammunisjonsprofiler"""
        ammos = self.db.execute_query(
            """
            SELECT id, name, velocity_fps, bc_g1, caliber, bullet_weight
            FROM ammo_profiles
            ORDER BY name
        """
        )

        for row in ammos:
            ammo_id, name, velocity, bc, caliber, weight = row
            display = f"{name} ({caliber}) - {velocity} fps" if velocity else name
            combo_widget.addItem(display, ammo_id)

    def on_ammo_selected(self):
        """Håndterer ammunisjonsvalg og viser sammenligning med forrige ladning"""
        ammo_id = self.drop_ammo.currentData()
        if not ammo_id:
            self.scope_adjustment_group.setVisible(False)
            return

        # Hent valgt ammunisjon
        current_ammo = self.db.execute_query(
            """
            SELECT name, rifle_id, velocity_fps, bc_g1, bullet_weight, caliber, created_date
            FROM ammo_profiles
            WHERE id = ?
        """,
            (ammo_id,),
        )

        if not current_ammo:
            self.scope_adjustment_group.setVisible(False)
            return

        name, rifle_id, velocity, bc, weight, caliber, created = current_ammo[0]

        if not rifle_id or not velocity or not bc:
            self.scope_adjustment_group.setVisible(False)
            return

        # Finn FORRIGE ladning for samme rifle (ikke inkluder nåværende)
        previous_ammo = self.db.execute_query(
            """
            SELECT name, velocity_fps, bc_g1, bullet_weight, caliber, created_date
            FROM ammo_profiles
            WHERE rifle_id = ? AND id != ? AND velocity_fps IS NOT NULL AND bc_g1 IS NOT NULL
            ORDER BY created_date DESC
            LIMIT 1
        """,
            (rifle_id, ammo_id),
        )

        if not previous_ammo:
            self.scope_adjustment_label.setText(
                f"<b>NY LADNING:</b> {name}<br>"
                f"<i>Dette er første ladning for denne riflen. Ingen sammenligning tilgjengelig.</i>"
            )
            self.scope_adjustment_group.setVisible(True)
            return

        prev_name, prev_vel, prev_bc, prev_weight, prev_cal, prev_created = (
            previous_ammo[0]
        )

        # Beregn drop for begge ladninger ved 100m, 300m, 600m
        zero_dist = self.drop_zero.value()
        test_distances = [100, 300, 600]

        comparison_html = f"""
        <b>NY LADNING:</b> {name} ({caliber})<br>
        • Hastighet: {velocity} fps, BC (G1): {bc}, Kulevskt: {weight} gr<br><br>

        <b>FORRIGE LADNING:</b> {prev_name} ({prev_cal})<br>
        • Hastighet: {prev_vel} fps, BC (G1): {prev_bc}, Kulevekt: {prev_weight} gr<br><br>

        <b>🎯 KIKKERT JUSTERING (Zero: {zero_dist}m):</b><br>
        <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
        <tr style='background-color: #f0f0f0; font-weight: bold;'>
            <td style='padding: 5px; border: 1px solid #ddd;'>Distanse</td>
            <td style='padding: 5px; border: 1px solid #ddd;'>Drop Ny</td>
            <td style='padding: 5px; border: 1px solid #ddd;'>Drop Forrige</td>
            <td style='padding: 5px; border: 1px solid #ddd;'>Forskjell</td>
            <td style='padding: 5px; border: 1px solid #ddd;'>Justering</td>
        </tr>
        """

        for dist in test_distances:
            # Drop for ny ladning
            drop_new = self.ballistics_calc.calculate_drop(
                velocity, bc, dist, zero_dist, "G1"
            )
            drop_new_moa = self.ballistics_calc.cm_to_moa(drop_new, dist)

            # Drop for forrige ladning
            drop_prev = self.ballistics_calc.calculate_drop(
                prev_vel, prev_bc, dist, zero_dist, "G1"
            )
            drop_prev_moa = self.ballistics_calc.cm_to_moa(drop_prev, dist)

            # Forskjell (negativ = ny ladning dropper mindre)
            diff_cm = drop_new - drop_prev
            diff_moa = drop_new_moa - drop_prev_moa

            # Kikkertjustering (0.25 MOA/click standard)
            clicks = diff_moa / 0.25
            direction = "OPP ↑" if clicks > 0 else "NED ↓" if clicks < 0 else "INGEN"

            color = (
                "#27ae60"
                if abs(diff_cm) < 5
                else "#f39c12" if abs(diff_cm) < 15 else "#e74c3c"
            )

            comparison_html += f"""
            <tr>
                <td style='padding: 5px; border: 1px solid #ddd;'>{dist}m</td>
                <td style='padding: 5px; border: 1px solid #ddd;'>{drop_new:.1f} cm ({drop_new_moa:.2f} MOA)</td>
                <td style='padding: 5px; border: 1px solid #ddd;'>{drop_prev:.1f} cm ({drop_prev_moa:.2f} MOA)</td>
                <td style='padding: 5px; border: 1px solid #ddd; background-color: {color}; color: white; font-weight: bold;'>{diff_cm:+.1f} cm ({diff_moa:+.2f} MOA)</td>
                <td style='padding: 5px; border: 1px solid #ddd; font-weight: bold;'>{direction} {abs(clicks):.1f} clicks</td>
            </tr>
            """

        comparison_html += """
        </table><br>
        <i>💡 Tips: Grønn = minimal forskjell (&lt;5cm), Gul = moderat (5-15cm), Rød = stor (&gt;15cm)</i><br>
        <i>📏 Standard click-verdi: 0.25 MOA/click. Sjekk din kikkert sine spesifikasjoner!</i>
        """

        self.scope_adjustment_label.setText(comparison_html)
        self.scope_adjustment_group.setVisible(True)

    def generate_drop_chart(self):
        """Genererer drop chart"""
        ammo_id = self.drop_ammo.currentData()
        if not ammo_id:
            QMessageBox.warning(self, "Mangler data", "Velg ammunisjon!")
            return

        # Hent ammo data
        ammo_data = self.db.execute_query(
            "SELECT name, velocity_fps, bc_g1, bullet_weight, caliber FROM ammo_profiles WHERE id = ?",
            (ammo_id,),
        )

        if not ammo_data:
            return

        name, velocity, bc, weight, caliber = ammo_data[0]

        zero = self.drop_zero.value()
        start = self.drop_start.value()
        end = self.drop_end.value()
        step = self.drop_step.value()
        unit = self.drop_units.currentText()

        # Generer tabell
        distances = list(range(start, end + 1, step))

        # Sett opp kolonner
        columns = ["Distanse (m)"]
        if unit == "MOA":
            columns.append("Drop (MOA)")
        elif unit == "MRAD":
            columns.append("Drop (MRAD)")
        elif unit == "CM":
            columns.append("Drop (cm)")
        elif unit == "INCHES":
            columns.append("Drop (inches)")

        if self.drop_include_velocity.isChecked():
            columns.append("Velocity (fps)")
        if self.drop_include_energy.isChecked():
            columns.append("Energy (ft-lbs)")
        if self.drop_include_tof.isChecked():
            columns.append("TOF (s)")

        self.drop_table.setColumnCount(len(columns))
        self.drop_table.setHorizontalHeaderLabels(columns)
        self.drop_table.setRowCount(len(distances))

        # Beregn for hver distanse
        for idx, distance in enumerate(distances):
            # Drop
            drop_cm = self.ballistics_calc.calculate_drop(
                velocity, bc, distance, zero, "G1"
            )

            if unit == "MOA":
                value = self.ballistics_calc.cm_to_moa(drop_cm, distance)
            elif unit == "MRAD":
                value = self.ballistics_calc.cm_to_mrad(drop_cm, distance)
            elif unit == "CM":
                value = drop_cm
            elif unit == "INCHES":
                value = drop_cm / 2.54

            self.drop_table.setItem(idx, 0, QTableWidgetItem(str(distance)))
            self.drop_table.setItem(idx, 1, QTableWidgetItem(f"{value:.2f}"))

            col_idx = 2

            # Velocity
            if self.drop_include_velocity.isChecked():
                vel = self.ballistics_calc.calculate_velocity_at_distance(
                    velocity, bc, distance, "G1"
                )
                self.drop_table.setItem(idx, col_idx, QTableWidgetItem(f"{vel:.0f}"))
                col_idx += 1

            # Energy
            if self.drop_include_energy.isChecked():
                vel = self.ballistics_calc.calculate_velocity_at_distance(
                    velocity, bc, distance, "G1"
                )
                energy = self.ballistics_calc.calculate_energy(vel, weight)
                self.drop_table.setItem(idx, col_idx, QTableWidgetItem(f"{energy:.0f}"))
                col_idx += 1

            # Time of Flight
            if self.drop_include_tof.isChecked():
                tof = distance / (velocity * 0.3048)  # Simplified
                self.drop_table.setItem(idx, col_idx, QTableWidgetItem(f"{tof:.2f}"))

        self.drop_table.resizeColumnsToContents()

        QMessageBox.information(
            self,
            "Ferdig!",
            f"Drop chart generert for {name}!\n\n{len(distances)} distanser fra {start}m til {end}m.",
        )

    def calculate_wind_drift(self):
        """Beregner wind drift"""
        ammo_id = self.wind_ammo.currentData()
        if not ammo_id:
            QMessageBox.warning(self, "Mangler data", "Velg ammunisjon!")
            return

        # Hent ammo data
        ammo_data = self.db.execute_query(
            "SELECT name, velocity_fps, bc_g1, bullet_weight, caliber FROM ammo_profiles WHERE id = ?",
            (ammo_id,),
        )

        if not ammo_data:
            return

        name, velocity, bc, weight, caliber = ammo_data[0]

        distance = self.wind_distance.value()
        wind_speeds = [
            self.wind_speed_1.value(),
            self.wind_speed_2.value(),
            self.wind_speed_3.value(),
        ]
        wind_angle = self.wind_angle.value()

        # Wind value factor
        angle_rad = math.radians(wind_angle)
        wind_factor = abs(math.sin(angle_rad))  # 0° = 0, 90° = 1

        # Beregn wind drift for hver hastighet
        results_html = f"""
<h2>🌬️ Wind Drift Resultat</h2>

<h3>📊 Ammunisjon:</h3>
<p><b>{name}</b> ({caliber})<br>
Hastighet: {velocity} fps | BC: {bc} | Vekt: {weight} grains</p>

<h3>🎯 Scenario:</h3>
<p>Distanse: <b>{distance}m</b><br>
Vindvinkel: <b>{wind_angle}°</b> ({self.get_wind_description(wind_angle)})<br>
Wind value factor: <b>{wind_factor:.2f}</b></p>

<h3>📈 Drift-beregninger:</h3>
<table style='width: 100%; border: 1px solid #ddd;'>
<tr style='background-color: #f0f0f0;'><th>Vind (m/s)</th><th>Drift (cm)</th><th>Drift (MOA)</th><th>Drift (MRAD)</th></tr>
"""

        for wind_speed in wind_speeds:
            # Forenklet wind drift formel (Miller's formula approximation)
            # drift_inches = (wind_mph * range_yards) / (velocity_fps * BC)

            wind_mph = wind_speed * 2.237  # m/s to mph
            range_yards = distance * 1.094  # m to yards

            # Base drift
            drift_inches = (wind_mph * range_yards * 15) / (velocity * bc)

            # Apply wind angle factor
            drift_inches *= wind_factor

            drift_cm = drift_inches * 2.54
            drift_moa = self.ballistics_calc.cm_to_moa(drift_cm, distance)
            drift_mrad = self.ballistics_calc.cm_to_mrad(drift_cm, distance)

            results_html += f"""
<tr>
<td>{wind_speed:.1f} m/s</td>
<td>{drift_cm:.1f} cm</td>
<td>{drift_moa:.2f} MOA</td>
<td>{drift_mrad:.2f} MRAD</td>
</tr>
"""

        results_html += """
</table>

<h3>💡 Praktiske tips:</h3>
<ul>
<li><b>Clock method:</b> 12 o'clock = fra nord, 3 o'clock = fra øst</li>
<li><b>3 o'clock / 9 o'clock:</b> Full-value crosswind (90°)</li>
<li><b>1-2 / 10-11 o'clock:</b> Half-value (~70% drift)</li>
<li><b>12 / 6 o'clock:</b> Headwind/tailwind (ingen lateral drift, men påvirker drop)</li>
</ul>

<h3>🎯 Holdover-eksempel:</h3>
<p>Ved {wind_speeds[1]:.1f} m/s crosswind på {distance}m:<br>
<b>Hold {drift_cm:.0f} cm ({drift_moa:.1f} MOA / {drift_mrad:.2f} MRAD) mot vinden</b></p>
        """

        self.wind_result.setHtml(results_html)

    def get_wind_description(self, angle):
        """Gir beskrivelse av vindvinkel"""
        if angle == 0:
            return "Headwind/Tailwind"
        elif angle < 30:
            return "Slight crosswind"
        elif angle < 60:
            return "Half-value crosswind"
        elif angle < 120:
            return "Full-value crosswind"
        elif angle < 150:
            return "Half-value crosswind"
        else:
            return "Slight crosswind"

    def generate_dope_card(self):
        """Genererer DOPE card"""
        ammo_id = self.dope_ammo.currentData()
        if not ammo_id:
            QMessageBox.warning(self, "Mangler data", "Velg ammunisjon!")
            return

        # Hent ammo data
        ammo_data = self.db.execute_query(
            "SELECT name, velocity_fps, bc_g1, bullet_weight, caliber FROM ammo_profiles WHERE id = ?",
            (ammo_id,),
        )

        if not ammo_data:
            return

        name, velocity, bc, weight, caliber = ammo_data[0]
        zero = self.dope_zero.value()

        dope_html = f"""
<div style='border: 2px solid black; padding: 20px; font-family: monospace;'>
<h1 style='text-align: center;'>🎯 DOPE CARD 🎯</h1>
<hr>

<h2>📋 Rifle Setup:</h2>
<table style='width: 100%;'>
<tr><td><b>Rifle:</b></td><td>{self.dope_rifle.text() or 'Not specified'}</td></tr>
<tr><td><b>Optikk:</b></td><td>{self.dope_scope.text() or 'Not specified'}</td></tr>
<tr><td><b>Ammunisjon:</b></td><td>{name} ({caliber})</td></tr>
<tr><td><b>Hastighet:</b></td><td>{velocity} fps</td></tr>
<tr><td><b>BC (G1):</b></td><td>{bc}</td></tr>
<tr><td><b>Kulevekt:</b></td><td>{weight} grains</td></tr>
<tr><td><b>Zero:</b></td><td>{zero}m</td></tr>
<tr><td><b>Dato:</b></td><td>{datetime.now().strftime('%Y-%m-%d')}</td></tr>
</table>

<h2>📊 Drop Chart (MOA):</h2>
<table style='width: 100%; border: 1px solid black; border-collapse: collapse;'>
<tr style='background-color: #ccc;'><th>Dist (m)</th><th>Drop (MOA)</th><th>Vel (fps)</th><th>Energy (ft-lbs)</th></tr>
"""

        # Generer kompakt tabell
        for distance in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
            drop_cm = self.ballistics_calc.calculate_drop(
                velocity, bc, distance, zero, "G1"
            )
            drop_moa = self.ballistics_calc.cm_to_moa(drop_cm, distance)
            vel = self.ballistics_calc.calculate_velocity_at_distance(
                velocity, bc, distance, "G1"
            )
            energy = self.ballistics_calc.calculate_energy(vel, weight)

            dope_html += f"""
<tr style='border: 1px solid #999;'>
<td style='padding: 5px;'>{distance}</td>
<td style='padding: 5px;'><b>{drop_moa:.1f}</b></td>
<td style='padding: 5px;'>{vel:.0f}</td>
<td style='padding: 5px;'>{energy:.0f}</td>
</tr>
"""

        dope_html += """
</table>

<h2>🌬️ Wind Drift (5 m/s full-value):</h2>
<table style='width: 100%; border: 1px solid black; border-collapse: collapse;'>
<tr style='background-color: #ccc;'><th>Dist (m)</th><th>Drift (cm)</th><th>Drift (MOA)</th></tr>
"""

        # Wind drift tabell
        for distance in [100, 200, 300, 400, 500, 600, 700, 800]:
            wind_mph = 5 * 2.237
            range_yards = distance * 1.094
            drift_inches = (wind_mph * range_yards * 15) / (velocity * bc)
            drift_cm = drift_inches * 2.54
            drift_moa = self.ballistics_calc.cm_to_moa(drift_cm, distance)

            dope_html += f"""
<tr style='border: 1px solid #999;'>
<td style='padding: 5px;'>{distance}</td>
<td style='padding: 5px;'>{drift_cm:.0f}</td>
<td style='padding: 5px;'><b>{drift_moa:.1f}</b></td>
</tr>
"""

        dope_html += """
</table>

<h3>📝 Notater:</h3>
<p>_________________________________________________________________</p>
<p>_________________________________________________________________</p>
<p>_________________________________________________________________</p>

<p style='text-align: center; font-size: 10pt;'><i>Generated by Reloading Workshop Manager</i></p>
</div>
"""

        self.dope_preview.setHtml(dope_html)

        QMessageBox.information(
            self, "Ferdig!", "DOPE card generert!\n\nKlar for export til PDF."
        )

    def export_drop_chart(self, format_type):
        """Eksporterer drop chart"""
        if self.drop_table.rowCount() == 0:
            QMessageBox.warning(self, "Ingen data", "Generer drop chart først!")
            return

        if format_type == "csv":
            filename, _ = QFileDialog.getSaveFileName(
                self, "Lagre drop chart", "", "CSV Files (*.csv)"
            )

            if filename:
                with open(filename, "w") as f:
                    # Header
                    headers = []
                    for col in range(self.drop_table.columnCount()):
                        headers.append(self.drop_table.horizontalHeaderItem(col).text())
                    f.write(",".join(headers) + "\n")

                    # Data
                    for row in range(self.drop_table.rowCount()):
                        row_data = []
                        for col in range(self.drop_table.columnCount()):
                            item = self.drop_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        f.write(",".join(row_data) + "\n")

                QMessageBox.information(
                    self, "Lagret!", f"Drop chart lagret til {filename}"
                )

        elif format_type == "pdf":
            QMessageBox.information(
                self,
                "PDF Export",
                "PDF export kommer i neste versjon!\n\nBruk CSV export og konverter til PDF manuelt for nå.",
            )

    def export_dope_pdf(self):
        """Eksporterer DOPE card til PDF"""
        QMessageBox.information(
            self,
            "PDF Export",
            "PDF export kommer i neste versjon!\n\nBruk 'Print' funksjon og 'Print to PDF' for nå.",
        )

    def print_drop_chart(self):
        """Printer drop chart"""
        QMessageBox.information(
            self,
            "Print",
            "Print-funksjon kommer i neste versjon!\n\nBruk browser print eller export til CSV for nå.",
        )


class ReloadingSimulatorUI(QWidget):
    """UI for tilpasset visning av anslagsenergi, rekyl og simulering"""

    def __init__(self, ballistics_calc, language="no"):
        super().__init__()
        self.ballistics_calc = ballistics_calc
        self.language = language
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        title = QLabel(tr("reloading_sim_title", self.language))
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        # Valg for visning
        self.energy_checkbox = QCheckBox(tr("show_energy", self.language))
        self.recoil_checkbox = QCheckBox(tr("show_recoil", self.language))
        self.sim_checkbox = QCheckBox(tr("show_simulation", self.language))
        layout.addWidget(self.energy_checkbox)
        layout.addWidget(self.recoil_checkbox)
        layout.addWidget(self.sim_checkbox)
        # Input-felter
        self.bullet_weight_input = QDoubleSpinBox()
        self.bullet_weight_input.setSuffix(" gr")
        self.bullet_weight_input.setRange(1, 1000)
        self.velocity_input = QDoubleSpinBox()
        self.velocity_input.setSuffix(" m/s")
        self.velocity_input.setRange(100, 1500)
        self.powder_weight_input = QDoubleSpinBox()
        self.powder_weight_input.setSuffix(" gr")
        self.powder_weight_input.setRange(1, 200)
        self.weapon_weight_input = QDoubleSpinBox()
        self.weapon_weight_input.setSuffix(" kg")
        self.weapon_weight_input.setRange(1, 20)
        layout.addWidget(QLabel(tr("bullet_weight", self.language)))
        layout.addWidget(self.bullet_weight_input)
        layout.addWidget(QLabel(tr("velocity", self.language)))
        layout.addWidget(self.velocity_input)
        layout.addWidget(QLabel(tr("powder_weight", self.language)))
        layout.addWidget(self.powder_weight_input)
        layout.addWidget(QLabel(tr("weapon_weight", self.language)))
        layout.addWidget(self.weapon_weight_input)
        # Simuleringsknapp
        sim_btn = QPushButton(tr("simulate", self.language))
        sim_btn.clicked.connect(self.run_simulation)
        layout.addWidget(sim_btn)
        # Resultatvisning
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

    def run_simulation(self):
        bw = self.bullet_weight_input.value() * 0.0648  # grains til gram
        v = self.velocity_input.value()
        pw = self.powder_weight_input.value() * 0.0648
        ww = self.weapon_weight_input.value() * 1000  # kg til gram
        results = []
        if self.energy_checkbox.isChecked():
            energy = 0.5 * bw * v**2
            results.append(f"{tr('energy', self.language)}: {energy:.1f} J")
        if self.recoil_checkbox.isChecked():
            recoil = (bw + pw) * v / ww
            results.append(f"{tr('recoil', self.language)}: {recoil:.2f} J")
        if self.sim_checkbox.isChecked():
            sim = [f"{d}m: {0.5 * bw * v ** 2:.1f} J" for d in [100, 200, 300, 400]]
            results.append(tr("simulation", self.language) + ":\n" + "\n".join(sim))
        self.result_text.setText("\n".join(results))
