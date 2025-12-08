"""
Comprehensive Data Logging System
Tracks EVERYTHING for load development - for the OCD shooters! 😄

Categories:
1. Environmental Conditions (temp, humidity, pressure, wind)
2. Ammo Details (batch #, components, case prep, measurements)
3. Rifle Condition (barrel rounds, cleaning history, wear)
4. Shot Data (velocity, accuracy, pressure signs)
5. Notes & Observations (qualitative data)
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from PyQt6.QtCore import QDate, QTime, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)


class ComprehensiveDataLogger(QWidget):
    """
    Comprehensive data logging for load development
    Tracks EVERYTHING that can affect accuracy
    """

    data_saved = pyqtSignal(dict)  # Emitted when data is saved

    def __init__(self, load_id: Optional[str] = None, load_name: Optional[str] = None):
        super().__init__()
        self.load_id = load_id or self._generate_load_id()
        self.load_name = load_name or "Unnamed Load"
        self.session_data: Dict[str, Any] = {}
        self.init_ui()

    def _generate_load_id(self) -> str:
        """Generate unique load development ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"LD_{timestamp}"

    def init_ui(self):
        """Initialize comprehensive logging UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header with Load ID
        header = QGroupBox()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)

        title = QLabel("📊 Comprehensive Data Log")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Load ID (prominent display)
        self.label_load_id = QLabel(f"🔖 Load ID: <b>{self.load_id}</b>")
        self.label_load_id.setStyleSheet(
            """
            background-color: #3498db;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
        """
        )
        header_layout.addWidget(self.label_load_id)

        layout.addWidget(header)

        # Tabs for different data categories
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Session Info
        self.tabs.addTab(self.create_session_tab(), "📋 Session Info")

        # Tab 2: Environmental
        self.tabs.addTab(self.create_environmental_tab(), "🌡️ Environmental")

        # Tab 3: Ammo Details
        self.tabs.addTab(self.create_ammo_tab(), "🎯 Ammo Details")

        # Tab 4: Rifle Condition
        self.tabs.addTab(self.create_rifle_tab(), "🔫 Rifle Condition")

        # Tab 5: Shot Data
        self.tabs.addTab(self.create_shot_data_tab(), "📊 Shot Data")

        # Tab 6: Notes & Observations
        self.tabs.addTab(self.create_notes_tab(), "📝 Notes")

        # Bottom buttons
        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Save Session")
        self.btn_save.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """
        )
        self.btn_save.clicked.connect(self.save_session)
        btn_layout.addWidget(self.btn_save)

        self.btn_export = QPushButton("📄 Export to Excel")
        self.btn_export.clicked.connect(self.export_to_excel)
        btn_layout.addWidget(self.btn_export)

        self.btn_print = QPushButton("🖨️ Print Data Sheet")
        self.btn_print.clicked.connect(self.print_data_sheet)
        btn_layout.addWidget(self.btn_print)

        layout.addLayout(btn_layout)

    def create_session_tab(self) -> QWidget:
        """Session info - when, where, who"""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)

        # Date & Time
        self.session_date = QDateEdit()
        self.session_date.setDate(QDate.currentDate())
        self.session_date.setCalendarPopup(True)
        layout.addRow("📅 Date:", self.session_date)

        self.session_time = QTimeEdit()
        self.session_time.setTime(QTime.currentTime())
        layout.addRow("🕐 Time:", self.session_time)

        # Location
        self.session_location = QLineEdit()
        self.session_location.setPlaceholderText("e.g., Bodø Skyttersenter")
        layout.addRow("📍 Location:", self.session_location)

        # Shooter
        self.session_shooter = QLineEdit()
        self.session_shooter.setPlaceholderText("Your name")
        layout.addRow("👤 Shooter:", self.session_shooter)

        # Session Type
        self.session_type = QComboBox()
        self.session_type.addItems(
            [
                "Load Development",
                "OCW Test",
                "Ladder Test",
                "Seating Depth Test",
                "Verification",
                "Competition Prep",
                "Zero Confirmation",
                "Other",
            ]
        )
        layout.addRow("🎯 Session Type:", self.session_type)

        # Distance
        self.session_distance = QSpinBox()
        self.session_distance.setRange(25, 1500)
        self.session_distance.setValue(100)
        self.session_distance.setSuffix(" meters")
        layout.addRow("📏 Distance:", self.session_distance)

        return widget

    def create_environmental_tab(self) -> QWidget:
        """Environmental conditions - critical for consistency"""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)

        # Temperature
        self.env_temp = QDoubleSpinBox()
        self.env_temp.setRange(-30, 50)
        self.env_temp.setValue(15)
        self.env_temp.setSuffix(" °C")
        layout.addRow("🌡️ Temperature:", self.env_temp)

        # Humidity
        self.env_humidity = QSpinBox()
        self.env_humidity.setRange(0, 100)
        self.env_humidity.setValue(50)
        self.env_humidity.setSuffix(" %")
        layout.addRow("💧 Humidity:", self.env_humidity)

        # Barometric Pressure
        self.env_pressure = QDoubleSpinBox()
        self.env_pressure.setRange(950, 1050)
        self.env_pressure.setValue(1013)
        self.env_pressure.setSuffix(" hPa")
        layout.addRow("🌍 Pressure:", self.env_pressure)

        # Altitude
        self.env_altitude = QSpinBox()
        self.env_altitude.setRange(0, 3000)
        self.env_altitude.setValue(0)
        self.env_altitude.setSuffix(" m")
        layout.addRow("⛰️ Altitude:", self.env_altitude)

        # Wind
        self.env_wind_speed = QDoubleSpinBox()
        self.env_wind_speed.setRange(0, 30)
        self.env_wind_speed.setValue(0)
        self.env_wind_speed.setSuffix(" m/s")
        layout.addRow("💨 Wind Speed:", self.env_wind_speed)

        self.env_wind_direction = QComboBox()
        self.env_wind_direction.addItems(
            [
                "Calm",
                "12 o'clock (headwind)",
                "1 o'clock",
                "2 o'clock",
                "3 o'clock (right)",
                "4 o'clock",
                "5 o'clock",
                "6 o'clock (tailwind)",
                "7 o'clock",
                "8 o'clock",
                "9 o'clock (left)",
                "10 o'clock",
                "11 o'clock",
            ]
        )
        layout.addRow("🧭 Wind Direction:", self.env_wind_direction)

        # Light conditions
        self.env_light = QComboBox()
        self.env_light.addItems(
            [
                "Bright sun",
                "Partly cloudy",
                "Overcast",
                "Light rain",
                "Heavy rain",
                "Snow",
                "Dawn/Dusk",
                "Night (artificial light)",
            ]
        )
        layout.addRow("☀️ Light Conditions:", self.env_light)

        # Mirage
        self.env_mirage = QComboBox()
        self.env_mirage.addItems(["None", "Light", "Moderate", "Heavy"])
        layout.addRow("🌊 Mirage:", self.env_mirage)

        return widget

    def create_ammo_tab(self) -> QWidget:
        """Ammo details - components and measurements"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        layout = QFormLayout()
        widget.setLayout(layout)

        # Batch Number
        self.ammo_batch = QLineEdit()
        self.ammo_batch.setPlaceholderText("e.g., BATCH_2024_001")
        layout.addRow("🔢 Batch Number:", self.ammo_batch)

        # Caliber
        self.ammo_caliber = QLineEdit()
        self.ammo_caliber.setPlaceholderText("e.g., 6.5 Creedmoor")
        layout.addRow("📐 Caliber:", self.ammo_caliber)

        # Bullet
        self.ammo_bullet = QLineEdit()
        self.ammo_bullet.setPlaceholderText("e.g., Berger 140gr Hybrid")
        layout.addRow("🎯 Bullet:", self.ammo_bullet)

        self.ammo_bullet_weight = QDoubleSpinBox()
        self.ammo_bullet_weight.setRange(20, 500)
        self.ammo_bullet_weight.setValue(140)
        self.ammo_bullet_weight.setSuffix(" gr")
        layout.addRow("⚖️ Bullet Weight:", self.ammo_bullet_weight)

        self.ammo_bullet_lot = QLineEdit()
        self.ammo_bullet_lot.setPlaceholderText("Bullet lot number")
        layout.addRow("📦 Bullet Lot:", self.ammo_bullet_lot)

        # Powder
        self.ammo_powder = QLineEdit()
        self.ammo_powder.setPlaceholderText("e.g., Vihtavuori N140")
        layout.addRow("💊 Powder:", self.ammo_powder)

        self.ammo_powder_charge = QDoubleSpinBox()
        self.ammo_powder_charge.setRange(10, 100)
        self.ammo_powder_charge.setValue(42.0)
        self.ammo_powder_charge.setSuffix(" gr")
        self.ammo_powder_charge.setDecimals(1)
        layout.addRow("⚖️ Powder Charge:", self.ammo_powder_charge)

        self.ammo_powder_lot = QLineEdit()
        self.ammo_powder_lot.setPlaceholderText("Powder lot number")
        layout.addRow("📦 Powder Lot:", self.ammo_powder_lot)

        # Primer
        self.ammo_primer = QLineEdit()
        self.ammo_primer.setPlaceholderText("e.g., CCI BR-2")
        layout.addRow("💥 Primer:", self.ammo_primer)

        self.ammo_primer_lot = QLineEdit()
        self.ammo_primer_lot.setPlaceholderText("Primer lot number")
        layout.addRow("📦 Primer Lot:", self.ammo_primer_lot)

        # Brass
        self.ammo_brass = QLineEdit()
        self.ammo_brass.setPlaceholderText("e.g., Lapua")
        layout.addRow("🥉 Brass:", self.ammo_brass)

        self.ammo_brass_firings = QSpinBox()
        self.ammo_brass_firings.setRange(0, 20)
        self.ammo_brass_firings.setValue(0)
        self.ammo_brass_firings.setSuffix("x fired")
        layout.addRow("♻️ Brass Firings:", self.ammo_brass_firings)

        self.ammo_brass_lot = QLineEdit()
        self.ammo_brass_lot.setPlaceholderText("Brass lot number")
        layout.addRow("📦 Brass Lot:", self.ammo_brass_lot)

        # Case Prep
        layout.addRow(QLabel("<b>Case Preparation:</b>"))

        self.prep_full_length_sized = QCheckBox("Full-length sized")
        layout.addRow("", self.prep_full_length_sized)

        self.prep_neck_sized = QCheckBox("Neck sized only")
        layout.addRow("", self.prep_neck_sized)

        self.prep_annealed = QCheckBox("Annealed")
        layout.addRow("", self.prep_annealed)

        self.prep_trimmed = QCheckBox("Trimmed")
        layout.addRow("", self.prep_trimmed)

        self.prep_chamfered = QCheckBox("Chamfered/Deburred")
        layout.addRow("", self.prep_chamfered)

        self.prep_primer_pocket = QCheckBox("Primer pockets uniformed")
        layout.addRow("", self.prep_primer_pocket)

        self.prep_flash_hole = QCheckBox("Flash holes deburred")
        layout.addRow("", self.prep_flash_hole)

        # Measurements
        layout.addRow(QLabel("<b>Measurements:</b>"))

        self.measure_case_length = QDoubleSpinBox()
        self.measure_case_length.setRange(30, 100)
        self.measure_case_length.setValue(48.0)
        self.measure_case_length.setSuffix(" mm")
        self.measure_case_length.setDecimals(2)
        layout.addRow("📏 Case Length:", self.measure_case_length)

        self.measure_coal = QDoubleSpinBox()
        self.measure_coal.setRange(40, 100)
        self.measure_coal.setValue(70.0)
        self.measure_coal.setSuffix(" mm")
        self.measure_coal.setDecimals(2)
        layout.addRow("📏 COAL:", self.measure_coal)

        self.measure_cbto = QDoubleSpinBox()
        self.measure_cbto.setRange(30, 90)
        self.measure_cbto.setValue(55.0)
        self.measure_cbto.setSuffix(" mm")
        self.measure_cbto.setDecimals(2)
        layout.addRow("📏 CBTO:", self.measure_cbto)

        self.measure_jump = QDoubleSpinBox()
        self.measure_jump.setRange(-0.5, 5.0)
        self.measure_jump.setValue(0.020)
        self.measure_jump.setSuffix(" mm")
        self.measure_jump.setDecimals(3)
        layout.addRow("🎯 Jump to Lands:", self.measure_jump)

        self.measure_neck_tension = QDoubleSpinBox()
        self.measure_neck_tension.setRange(0.001, 0.010)
        self.measure_neck_tension.setValue(0.002)
        self.measure_neck_tension.setSuffix(" in")
        self.measure_neck_tension.setDecimals(3)
        layout.addRow("🔧 Neck Tension:", self.measure_neck_tension)

        container = QWidget()
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)
        container_layout.addWidget(scroll)

        return container

    def create_rifle_tab(self) -> QWidget:
        """Rifle condition - barrel life, cleaning, etc"""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)

        # Rifle ID
        self.rifle_name = QLineEdit()
        self.rifle_name.setPlaceholderText("e.g., Tikka T3X CTR")
        layout.addRow("🔫 Rifle:", self.rifle_name)

        # Barrel info
        self.rifle_barrel_make = QLineEdit()
        self.rifle_barrel_make.setPlaceholderText("e.g., Factory / Bartlein")
        layout.addRow("🎯 Barrel:", self.rifle_barrel_make)

        self.rifle_barrel_length = QSpinBox()
        self.rifle_barrel_length.setRange(10, 36)
        self.rifle_barrel_length.setValue(24)
        self.rifle_barrel_length.setSuffix(" inches")
        layout.addRow("📏 Barrel Length:", self.rifle_barrel_length)

        self.rifle_twist_rate = QComboBox()
        self.rifle_twist_rate.addItems(
            [
                "1:7",
                "1:7.5",
                "1:8",
                "1:8.5",
                "1:9",
                "1:10",
                "1:11",
                "1:12",
                "1:14",
                "Other",
            ]
        )
        layout.addRow("🌀 Twist Rate:", self.rifle_twist_rate)

        # Barrel condition
        self.rifle_round_count = QSpinBox()
        self.rifle_round_count.setRange(0, 10000)
        self.rifle_round_count.setValue(0)
        self.rifle_round_count.setSuffix(" rounds")
        layout.addRow("🔢 Total Round Count:", self.rifle_round_count)

        self.rifle_rounds_since_clean = QSpinBox()
        self.rifle_rounds_since_clean.setRange(0, 500)
        self.rifle_rounds_since_clean.setValue(0)
        self.rifle_rounds_since_clean.setSuffix(" rounds")
        layout.addRow("🧹 Rounds Since Cleaning:", self.rifle_rounds_since_clean)

        self.rifle_cleaned_before_session = QCheckBox("Cleaned before this session")
        layout.addRow("", self.rifle_cleaned_before_session)

        self.rifle_fouling_shots = QSpinBox()
        self.rifle_fouling_shots.setRange(0, 20)
        self.rifle_fouling_shots.setValue(0)
        self.rifle_fouling_shots.setSuffix(" shots")
        layout.addRow("🎯 Fouling Shots:", self.rifle_fouling_shots)

        # Barrel temp
        self.rifle_barrel_temp = QComboBox()
        self.rifle_barrel_temp.addItems(
            [
                "Cold (ambient temp)",
                "Warm (1-2 shots)",
                "Hot (3-5 shots rapid)",
                "Very hot (>5 shots rapid)",
            ]
        )
        layout.addRow("🌡️ Barrel Temp:", self.rifle_barrel_temp)

        # Scope/Optic
        self.rifle_scope = QLineEdit()
        self.rifle_scope.setPlaceholderText("e.g., Vortex Viper PST 5-25x50")
        layout.addRow("🔭 Scope:", self.rifle_scope)

        self.rifle_scope_zero = QLineEdit()
        self.rifle_scope_zero.setPlaceholderText("e.g., 100m, 1.5 MRAD up")
        layout.addRow("🎯 Zero:", self.rifle_scope_zero)

        # Rest/Support
        self.rifle_support = QComboBox()
        self.rifle_support.addItems(
            [
                "Bipod + Rear Bag",
                "Front + Rear Bag",
                "Lead Sled",
                "Benchrest",
                "Prone (no support)",
                "Other",
            ]
        )
        layout.addRow("🛠️ Support:", self.rifle_support)

        return widget

    def create_shot_data_tab(self) -> QWidget:
        """Shot data - velocity, accuracy, pressure signs"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Instructions
        info = QLabel(
            """
        <b>📊 Shot Data Entry</b><br>
        Enter velocity and group data here. For detailed shot-by-shot tracking,
        use the Live Testing tab in your workflow.
        """
        )
        info.setStyleSheet(
            "background-color: #ecf0f1; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        form = QFormLayout()

        # Velocity stats
        form.addRow(QLabel("<b>Velocity Data:</b>"))

        self.shot_avg_velocity = QSpinBox()
        self.shot_avg_velocity.setRange(500, 4000)
        self.shot_avg_velocity.setValue(2700)
        self.shot_avg_velocity.setSuffix(" fps")
        form.addRow("📈 Average Velocity:", self.shot_avg_velocity)

        self.shot_es = QSpinBox()
        self.shot_es.setRange(0, 200)
        self.shot_es.setValue(15)
        self.shot_es.setSuffix(" fps")
        form.addRow("📊 ES:", self.shot_es)

        self.shot_sd = QDoubleSpinBox()
        self.shot_sd.setRange(0, 100)
        self.shot_sd.setValue(6.5)
        self.shot_sd.setSuffix(" fps")
        self.shot_sd.setDecimals(1)
        form.addRow("📊 SD:", self.shot_sd)

        self.shot_count = QSpinBox()
        self.shot_count.setRange(1, 100)
        self.shot_count.setValue(5)
        self.shot_count.setSuffix(" shots")
        form.addRow("🔢 Shot Count:", self.shot_count)

        # Accuracy
        form.addRow(QLabel("<b>Accuracy Data:</b>"))

        self.shot_group_size = QDoubleSpinBox()
        self.shot_group_size.setRange(0, 100)
        self.shot_group_size.setValue(25.0)
        self.shot_group_size.setSuffix(" mm")
        self.shot_group_size.setDecimals(1)
        form.addRow("🎯 Group Size:", self.shot_group_size)

        self.shot_moa = QDoubleSpinBox()
        self.shot_moa.setRange(0, 10)
        self.shot_moa.setValue(0.75)
        self.shot_moa.setSuffix(" MOA")
        self.shot_moa.setDecimals(2)
        form.addRow("🎯 MOA:", self.shot_moa)

        # Pressure signs
        form.addRow(QLabel("<b>Pressure Signs:</b>"))

        self.pressure_none = QCheckBox("No pressure signs")
        form.addRow("", self.pressure_none)

        self.pressure_flattened = QCheckBox("Flattened primers")
        form.addRow("", self.pressure_flattened)

        self.pressure_cratered = QCheckBox("Cratered primers")
        form.addRow("", self.pressure_cratered)

        self.pressure_ejector_mark = QCheckBox("Ejector marks")
        form.addRow("", self.pressure_ejector_mark)

        self.pressure_heavy_bolt = QCheckBox("Heavy bolt lift")
        form.addRow("", self.pressure_heavy_bolt)

        self.pressure_sticky_extraction = QCheckBox("Sticky extraction")
        form.addRow("", self.pressure_sticky_extraction)

        layout.addLayout(form)
        layout.addStretch()

        return widget

    def create_notes_tab(self) -> QWidget:
        """Notes & observations - qualitative data"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        label = QLabel("<b>📝 Notes & Observations</b>")
        label.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addWidget(label)

        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText(
            """
Enter any observations here:
- How did the rifle feel?
- Any unusual sounds or behavior?
- Ejection pattern?
- Primer appearance?
- Brass condition?
- Wind calls?
- Personal performance notes?
- Ideas for next session?

Example:
"Groups opened up after 5 shots - barrel heating issue?
Need to test with more cool-down time.
ES looking good though, powder charge seems promising."
        """
        )
        layout.addWidget(self.notes_text)

        return widget

    def collect_all_data(self) -> Dict[str, Any]:
        """Collect all data from all tabs"""
        data = {
            "load_id": self.load_id,
            "load_name": self.load_name,
            "timestamp": datetime.now().isoformat(),
            # Session info
            "session": {
                "date": self.session_date.date().toString("yyyy-MM-dd"),
                "time": self.session_time.time().toString("HH:mm:ss"),
                "location": self.session_location.text(),
                "shooter": self.session_shooter.text(),
                "type": self.session_type.currentText(),
                "distance_meters": self.session_distance.value(),
            },
            # Environmental
            "environmental": {
                "temperature_c": self.env_temp.value(),
                "humidity_percent": self.env_humidity.value(),
                "pressure_hpa": self.env_pressure.value(),
                "altitude_m": self.env_altitude.value(),
                "wind_speed_ms": self.env_wind_speed.value(),
                "wind_direction": self.env_wind_direction.currentText(),
                "light_conditions": self.env_light.currentText(),
                "mirage": self.env_mirage.currentText(),
            },
            # Ammo details
            "ammo": {
                "batch_number": self.ammo_batch.text(),
                "caliber": self.ammo_caliber.text(),
                "bullet": self.ammo_bullet.text(),
                "bullet_weight_gr": self.ammo_bullet_weight.value(),
                "bullet_lot": self.ammo_bullet_lot.text(),
                "powder": self.ammo_powder.text(),
                "powder_charge_gr": self.ammo_powder_charge.value(),
                "powder_lot": self.ammo_powder_lot.text(),
                "primer": self.ammo_primer.text(),
                "primer_lot": self.ammo_primer_lot.text(),
                "brass": self.ammo_brass.text(),
                "brass_firings": self.ammo_brass_firings.value(),
                "brass_lot": self.ammo_brass_lot.text(),
                "case_prep": {
                    "full_length_sized": self.prep_full_length_sized.isChecked(),
                    "neck_sized": self.prep_neck_sized.isChecked(),
                    "annealed": self.prep_annealed.isChecked(),
                    "trimmed": self.prep_trimmed.isChecked(),
                    "chamfered": self.prep_chamfered.isChecked(),
                    "primer_pocket_uniformed": self.prep_primer_pocket.isChecked(),
                    "flash_hole_deburred": self.prep_flash_hole.isChecked(),
                },
                "measurements": {
                    "case_length_mm": self.measure_case_length.value(),
                    "coal_mm": self.measure_coal.value(),
                    "cbto_mm": self.measure_cbto.value(),
                    "jump_mm": self.measure_jump.value(),
                    "neck_tension_in": self.measure_neck_tension.value(),
                },
            },
            # Rifle condition
            "rifle": {
                "name": self.rifle_name.text(),
                "barrel_make": self.rifle_barrel_make.text(),
                "barrel_length_in": self.rifle_barrel_length.value(),
                "twist_rate": self.rifle_twist_rate.currentText(),
                "total_round_count": self.rifle_round_count.value(),
                "rounds_since_clean": self.rifle_rounds_since_clean.value(),
                "cleaned_before_session": self.rifle_cleaned_before_session.isChecked(),
                "fouling_shots": self.rifle_fouling_shots.value(),
                "barrel_temp": self.rifle_barrel_temp.currentText(),
                "scope": self.rifle_scope.text(),
                "scope_zero": self.rifle_scope_zero.text(),
                "support": self.rifle_support.currentText(),
            },
            # Shot data
            "shot_data": {
                "avg_velocity_fps": self.shot_avg_velocity.value(),
                "es_fps": self.shot_es.value(),
                "sd_fps": self.shot_sd.value(),
                "shot_count": self.shot_count.value(),
                "group_size_mm": self.shot_group_size.value(),
                "moa": self.shot_moa.value(),
                "pressure_signs": {
                    "none": self.pressure_none.isChecked(),
                    "flattened_primers": self.pressure_flattened.isChecked(),
                    "cratered_primers": self.pressure_cratered.isChecked(),
                    "ejector_marks": self.pressure_ejector_mark.isChecked(),
                    "heavy_bolt_lift": self.pressure_heavy_bolt.isChecked(),
                    "sticky_extraction": self.pressure_sticky_extraction.isChecked(),
                },
            },
            # Notes
            "notes": self.notes_text.toPlainText(),
        }

        return data

    def save_session(self):
        """Save session data"""
        data = self.collect_all_data()

        # TODO: Save to database
        # For now, just emit signal
        self.data_saved.emit(data)

        QMessageBox.information(
            self,
            "Session Saved",
            f"✅ Session data saved!\n\nLoad ID: {self.load_id}\n\nData logged:\n"
            + f"• Session: {data['session']['type']} @ {data['session']['location']}\n"
            + f"• Ammo: {data['ammo']['caliber']} - {data['ammo']['powder_charge_gr']}gr {data['ammo']['powder']}\n"
            + f"• Results: {data['shot_data']['avg_velocity_fps']} fps, SD {data['shot_data']['sd_fps']}, {data['shot_data']['moa']} MOA",
        )

    def export_to_excel(self):
        """Export data to Excel format"""
        # TODO: Implement Excel export
        QMessageBox.information(
            self,
            "Excel Export",
            "📄 Excel export coming soon!\n\nWill generate range-ready data sheet with QR code.",
        )

    def print_data_sheet(self):
        """Print data sheet for range use"""
        # TODO: Implement printing
        QMessageBox.information(
            self,
            "Print Data Sheet",
            "🖨️ Print function coming soon!\n\nWill generate printable data sheet with:\n"
            + "• Load ID & QR code\n"
            + "• Pre-filled component info\n"
            + "• Blank shot data table\n"
            + "• Environmental checklist",
        )

    def load_from_dict(self, data: Dict[str, Any]):
        """Load data from dictionary"""
        # Session
        if "session" in data:
            s = data["session"]
            self.session_location.setText(s.get("location", ""))
            self.session_shooter.setText(s.get("shooter", ""))
            # etc...

        # Environmental
        if "environmental" in data:
            e = data["environmental"]
            self.env_temp.setValue(e.get("temperature_c", 15))
            self.env_humidity.setValue(e.get("humidity_percent", 50))
            # etc...

        # Continue for other tabs...


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    logger = ComprehensiveDataLogger(
        load_id="LD_20241123_001", load_name="6.5 Creedmoor - Berger 140gr Hybrid Test"
    )

    def on_data_saved(data):
        from src.logging_config import configure_logging, get_logger

        configure_logging()
        logger = get_logger(__name__)
        logger.info("Data saved!")
        logger.debug(json.dumps(data, indent=2))

    logger.data_saved.connect(on_data_saved)

    logger.show()
    logger.resize(900, 700)

    sys.exit(app.exec())
