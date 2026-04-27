"""
Advanced Rifle Profile Editor
Comprehensive rifle configuration for precision load development
"""

import json
import re
from datetime import datetime
from typing import Any, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.barrel_configuration import build_derived_barrel_configuration_context
from ..utils.rifle_harmonics import calculate_harmonics_profile, normalize_node_bands

BORE_CONDITION_MAP = {
    "Ny (<100 skudd)": "excellent",
    "Innkjørt (100-500)": "good",
    "Moderat brukt (500-1500)": "fair",
    "Mye brukt (1500-3000)": "worn",
    "Utslitt (>3000)": "worn",
    "New (<100 shots)": "excellent",
    "Broken in (100-500)": "good",
    "Moderately used (500-1500)": "fair",
    "Heavily used (1500-3000)": "worn",
    "Worn out (>3000)": "worn",
}

BORE_CONDITION_REVERSE = {
    "excellent": "New (<100 shots)",
    "good": "Broken in (100-500)",
    "fair": "Moderately used (500-1500)",
    "worn": "Heavily used (1500-3000)",
}


class RifleProfileEditor(QDialog):
    """
    Comprehensive rifle profile editor
    Captures ALL data needed for precision load development & harmonics
    """

    rifle_saved = pyqtSignal(dict)

    def __init__(
        self, parent=None, rifle_id: Optional[int] = None, user_mode: str = "beginner"
    ):
        super().__init__(parent)
        try:
            from src.ui.theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            pass
        # ...existing code...
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id
        self.rifle_data: dict[str, Any] = {}
        self._loaded_profile_details: dict[str, Any] = {}
        self._bullet_profiles_current_barrel_id: Optional[str] = None
        self._chamber_current_barrel_id: Optional[str] = None
        self._muzzle_current_barrel_id: Optional[str] = None
        self.user_mode = user_mode  # "beginner" or "expert"

        self.setWindowTitle("Rifle Profile Editor")
        self.setMinimumSize(1000, 800)

        self.init_ui()

        if rifle_id:
            self.load_rifle_data()

    def init_ui(self):
        """Initialize comprehensive UI"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("Complete Firearm Profile")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        # User mode toggle
        mode_layout = QHBoxLayout()
        mode_label = QLabel("User Mode:")
        mode_layout.addWidget(mode_label)

        self.mode_beginner = QRadioButton("Beginner (Simple)")
        self.mode_expert = QRadioButton("Expert (Full details)")

        if self.user_mode == "expert":
            self.mode_expert.setChecked(True)
        else:
            self.mode_beginner.setChecked(True)

        self.mode_beginner.toggled.connect(self.on_mode_changed)

        mode_layout.addWidget(self.mode_beginner)
        mode_layout.addWidget(self.mode_expert)
        mode_layout.addStretch()

        mode_widget = QWidget()
        mode_widget.setLayout(mode_layout)
        mode_widget.setStyleSheet(
            """
            QWidget {
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
            }
            QRadioButton {
                font-weight: bold;
            }
        """
        )
        layout.addWidget(mode_widget)

        desc = QLabel(
            "Create a detailed profile of your firearm. The more data you add, the better recommendations "
            "the AI can provide for load development, harmonics, and precision."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Tabs for organized input - conditional based on user mode
        self.tabs = QTabWidget()

        # Tab 1: Basic Info (always shown)
        self.tabs.addTab(self.create_basic_tab(), "Basic")

        if self.user_mode == "beginner":
            self.tabs.addTab(self.create_barrel_tab_simple(), "Barrel")
        else:
            self.tabs.addTab(self.create_barrel_tab(), "Barrel Details")
            self.tabs.addTab(self.create_harmonics_tab(), "Harmonics Scorecard")
            self.tabs.addTab(self.create_muzzle_tab(), "Suppressor/Brake")
            self.tabs.addTab(self.create_chamber_tab(), "Chamber & Tolerances")
            self.tabs.addTab(self.create_bullet_profiles_tab(), "Bullet Profiles")
            self.tabs.addTab(self.create_preview_tab(), "Visual Overview")
            self.tabs.addTab(self.create_digital_twin_tab(), "Digital Twin")

        layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Profile")
        save_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """
        )
        save_btn.clicked.connect(self.save_profile)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def create_digital_twin_tab(self) -> QWidget:
        """Digital twin sandbox for load development."""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel(
            "<b>Digital Twin:</b> Real-time modeling of firearm, ammunition, and environment. "
            "Changes provide immediate feedback on harmonics, robustness, and warnings."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #e8f7d5; color: #0d3b66; padding: 10px; border-radius: 5px; font-weight: bold;"
        )
        layout.addWidget(info)

        form = QFormLayout()
        self.dt_barrel_length = QDoubleSpinBox()
        self.dt_barrel_length.setRange(100, 900)
        self.dt_barrel_length.setValue(610)
        self.dt_barrel_length.setSuffix(" mm")
        form.addRow("Barrel length:", self.dt_barrel_length)

        self.dt_powder_charge = QDoubleSpinBox()
        self.dt_powder_charge.setRange(0, 200)
        self.dt_powder_charge.setValue(42.0)
        self.dt_powder_charge.setSuffix(" gr")
        form.addRow("Powder charge:", self.dt_powder_charge)

        self.dt_temperature = QDoubleSpinBox()
        self.dt_temperature.setRange(-40, 60)
        self.dt_temperature.setValue(15)
        self.dt_temperature.setSuffix(" °C")
        form.addRow("Temperature:", self.dt_temperature)

        self.dt_bullet_weight = QDoubleSpinBox()
        self.dt_bullet_weight.setRange(30, 250)
        self.dt_bullet_weight.setValue(140)
        self.dt_bullet_weight.setSuffix(" gr")
        form.addRow("Bullet weight:", self.dt_bullet_weight)

        self.dt_coal = QDoubleSpinBox()
        self.dt_coal.setRange(40, 120)
        self.dt_coal.setValue(75)
        self.dt_coal.setSuffix(" mm")
        form.addRow("COAL:", self.dt_coal)

        self.dt_pressure = QDoubleSpinBox()
        self.dt_pressure.setRange(900, 1100)
        self.dt_pressure.setValue(1013)
        self.dt_pressure.setSuffix(" hPa")
        form.addRow("Air pressure:", self.dt_pressure)

        layout.addLayout(form)

        self.dt_result_text = QTextEdit()
        self.dt_result_text.setReadOnly(True)
        self.dt_result_text.setMaximumHeight(220)
        layout.addWidget(self.dt_result_text)

        self.dt_plot_label = QLabel("[Plot: velocity, pressure, harmonics]")
        self.dt_plot_label.setStyleSheet(
            "background-color: #f7e8d5; color: #0d3b66; padding: 8px; border-radius: 5px; font-weight: bold;"
        )
        layout.addWidget(self.dt_plot_label)

        button_row = QHBoxLayout()
        update_btn = QPushButton("Update Digital Twin")
        update_btn.clicked.connect(self.update_digital_twin)
        button_row.addWidget(update_btn)

        save_btn = QPushButton("Save Simulation")
        save_btn.clicked.connect(self.save_digital_twin_simulation)
        button_row.addWidget(save_btn)
        layout.addLayout(button_row)

        self.dt_sim_table = QTableWidget()
        self.dt_sim_table.setColumnCount(8)
        self.dt_sim_table.setHorizontalHeaderLabels(
            [
                "Pipe (mm)",
                "Powder (gr)",
                "Temp (°C)",
                "Bullet weight (gr)",
                "COAL (mm)",
                "Pressure (hPa)",
                "Result",
                "Include",
            ]
        )
        self.dt_sim_table.setMaximumHeight(160)
        layout.addWidget(self.dt_sim_table)

        widget.setLayout(layout)
        return widget

    def save_digital_twin_simulation(self):
        """Persist the current digital twin snapshot into the profile JSON."""
        if not getattr(self, "rifle_id", None):
            return

        result = (
            self.dt_result_text.toPlainText() if hasattr(self, "dt_result_text") else ""
        )
        sim_data = {
            "barrel_length": self.dt_barrel_length.value(),
            "powder_charge": self.dt_powder_charge.value(),
            "temperature": self.dt_temperature.value(),
            "bullet_weight": self.dt_bullet_weight.value(),
            "coal": self.dt_coal.value(),
            "pressure": self.dt_pressure.value(),
            "result": result,
        }

        rows = self.db.execute_query(
            "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
            (self.rifle_id,),
        )
        details: dict[str, Any] = {}
        if rows and rows[0].get("profile_json"):
            try:
                details = json.loads(rows[0]["profile_json"])
            except json.JSONDecodeError:
                details = {}

        sims = details.get("digital_twin_sims", [])
        if not isinstance(sims, list):
            sims = []
        sims.append(sim_data)
        details["digital_twin_sims"] = sims
        self._save_profile_details(self.rifle_id, details)

        if hasattr(self, "dt_sim_table"):
            row = self.dt_sim_table.rowCount()
            self.dt_sim_table.insertRow(row)
            values = [
                sim_data["barrel_length"],
                sim_data["powder_charge"],
                sim_data["temperature"],
                sim_data["bullet_weight"],
                sim_data["coal"],
                sim_data["pressure"],
                sim_data["result"],
            ]
            for col, value in enumerate(values):
                self.dt_sim_table.setItem(row, col, QTableWidgetItem(str(value)))
            include = QCheckBox()
            include.setChecked(True)
            self.dt_sim_table.setCellWidget(row, 7, include)

    def update_digital_twin(self):
        """Update the digital twin preview from the current sliders."""
        try:
            from .digital_twin import DigitalTwin

            rifle_state = {
                "barrel_length_mm": self.dt_barrel_length.value(),
                "barrel_contour": (
                    getattr(self, "barrel_profile", None).currentText()
                    if hasattr(self, "barrel_profile")
                    else "medium"
                ),
                "barrel_weight_grams": (
                    getattr(self, "barrel_weight", None).value()
                    if hasattr(self, "barrel_weight")
                    else 2200
                ),
            }
            ammo_state = {
                "powder_charge": self.dt_powder_charge.value(),
                "bullet_weight": self.dt_bullet_weight.value(),
                "coal_mm": self.dt_coal.value(),
            }
            env_state = {
                "temperature_c": self.dt_temperature.value(),
                "pressure_hpa": self.dt_pressure.value(),
            }
            twin = DigitalTwin(rifle_state, ammo_state, env_state)
            state = twin.get_state()
            result, plot = twin.simulate_with_plot()
            self.dt_result_text.setPlainText(
                self._build_digital_twin_result_text(result, state)
            )
            self.dt_plot_label.setText(plot)
        except Exception as exc:
            self.dt_result_text.setPlainText(f"Error: {exc}")
            self.dt_plot_label.setText("[Plot unavailable]")

    def _build_digital_twin_result_text(
        self, result: str, state: dict[str, Any] | None
    ) -> str:
        state = state or {}
        guidance = (
            state.get("guidance") if isinstance(state.get("guidance"), dict) else {}
        )
        warnings = (
            state.get("warnings") if isinstance(state.get("warnings"), list) else []
        )

        summary_lines = [result.strip()]
        recommended_baseline = str(guidance.get("recommended_baseline") or "").strip()
        if recommended_baseline:
            summary_lines.append(f"Baseline target: {recommended_baseline}")

        charge_target = str(guidance.get("charge_return_target") or "").strip()
        if charge_target:
            charge_baseline_label = str(
                guidance.get("charge_baseline_label")
                or guidance.get("charge_baseline_kind")
                or "modeled baseline"
            ).strip()
            summary_lines.append(
                f"Charge return target ({charge_baseline_label}): {charge_target}"
            )

        seating_target = str(guidance.get("seating_return_target") or "").strip()
        if seating_target:
            seating_baseline_label = str(
                guidance.get("seating_baseline_label")
                or guidance.get("seating_baseline_kind")
                or "modeled baseline"
            ).strip()
            summary_lines.append(
                f"Seating return target ({seating_baseline_label}): {seating_target}"
            )

        if warnings:
            summary_lines.append(
                "Warnings: "
                + " | ".join(
                    str(item).strip() for item in warnings if str(item).strip()
                )
            )

        return "\n".join(line for line in summary_lines if line)

    def create_harmonics_tab(self) -> QWidget:
        """Harmonics Quick + Scorecard tab for barrel profile."""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel(
            "<b>Harmonics Scorecard:</b> Shows estimated base frequency, node positions, and robustness. "
            "Changes in barrel length, suppressor, tuner, and support point affect node bands."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #e8f7d5; color: #0d3b66; padding: 10px; border-radius: 5px; font-weight: bold;"
        )
        layout.addWidget(info)

        form = QFormLayout()
        self.barrel_profile_id = QLineEdit()
        form.addRow("Barrel profile ID:", self.barrel_profile_id)
        self.free_float_length_mm = QDoubleSpinBox()
        self.free_float_length_mm.setRange(0, 1000)
        self.free_float_length_mm.setSuffix(" mm")
        form.addRow("Free-float length:", self.free_float_length_mm)
        self.tuner_mass_g = QDoubleSpinBox()
        self.tuner_mass_g.setRange(0, 1000)
        self.tuner_mass_g.setSuffix(" g")
        form.addRow("Tuner mass:", self.tuner_mass_g)
        self.tuner_position_mm = QDoubleSpinBox()
        self.tuner_position_mm.setRange(0, 1000)
        self.tuner_position_mm.setSuffix(" mm")
        form.addRow("Tuner position:", self.tuner_position_mm)
        self.action_stiffness = QComboBox()
        self.action_stiffness.addItems(["soft", "normal", "rigid"])
        form.addRow("Action stiffness:", self.action_stiffness)
        self.support_type = QComboBox()
        self.support_type.addItems(["bipod", "rest", "freehand"])
        form.addRow("Support type:", self.support_type)
        self.harmonic_score = QDoubleSpinBox()
        self.harmonic_score.setRange(0, 20)
        form.addRow("Harmonic score:", self.harmonic_score)

        layout.addLayout(form)

        node_bands_label = QLabel("<b>Node bands:</b>")
        layout.addWidget(node_bands_label)
        self.node_bands_text = QTextEdit()
        self.node_bands_text.setPlaceholderText(
            'Example: [{"start_mm":120, "end_mm":140, "robustness":0.8}]'
        )
        self.node_bands_text.setMaximumHeight(80)
        layout.addWidget(self.node_bands_text)

        widget.setLayout(layout)
        return widget

    def create_basic_tab(self) -> QWidget:
        """Basic rifle information"""
        container = QWidget()
        layout = QVBoxLayout()

        form = QFormLayout()

        # Weapon type
        self.weapon_type = QComboBox()
        self.weapon_type.addItems(["Rifle", "Pistol"])
        self.weapon_type.currentTextChanged.connect(self.on_weapon_type_changed)
        form.addRow("Firearm Type:", self.weapon_type)

        # Name
        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g. Tikka T3X CTR .308 or Pardini SP .22LR")
        form.addRow("Firearm Name:", self.name)

        # Manufacturer
        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText(
            "Tikka, Sako, Bergara, Pardini, Walther, etc."
        )
        form.addRow("Manufacturer:", self.manufacturer)

        # Caliber
        self.caliber = QComboBox()
        self.caliber.setEditable(True)
        self.caliber.addItems(
            [
                ".308 Winchester",
                "6.5 Creedmoor",
                ".223 Remington",
                "6.5x55 Swedish",
                ".30-06 Springfield",
                "6mm Creedmoor",
                ".300 Win Mag",
                ".22LR",
                ".32 S&W Long",
                ".38 Special",
                "9mm Luger",
                ".45 ACP",
            ]
        )
        form.addRow("Caliber:", self.caliber)

        # Action type
        self.action_type = QComboBox()
        self.action_type.addItems(
            [
                "Bolt Action",
                "Semi-Auto",
                "Lever Action",
                "Single Shot",
                "Revolver",
                "Pistol",
            ]
        )
        form.addRow("Action:", self.action_type)

        # Serial number
        self.serial = QLineEdit()
        self.serial.setPlaceholderText("Optional - for identification")
        form.addRow("Serial Number:", self.serial)

        # Dynamisk pistolspesifikke felter
        self.pistol_fields: dict[str, Any] = {}
        self.pistol_fields["sikte"] = QLineEdit()
        self.pistol_fields["sikte"].setPlaceholderText("e.g. Red Dot, Iron Sights")
        self.pistol_fields["avtrekk"] = QLineEdit()
        self.pistol_fields["avtrekk"].setPlaceholderText("e.g. 1000g, adjustable")
        self.pistol_fields["magasin"] = QSpinBox()
        self.pistol_fields["magasin"].setRange(1, 20)
        # Skjules for rifle, vises for pistol
        for label, field_widget in self.pistol_fields.items():
            form.addRow(f"Pistol {label.capitalize()}:", field_widget)
            field_widget.hide()

        layout.addLayout(form)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "e.g. Bought in 2023, custom trigger, bedding job done..."
        )
        self.notes.setMaximumHeight(100)
        notes_layout.addWidget(self.notes)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        layout.addStretch()
        container.setLayout(layout)
        return container

    def on_weapon_type_changed(self, value):
        is_pistol = value == "Pistol"
        for widget in self.pistol_fields.values():
            widget.setVisible(is_pistol)

    def create_barrel_tab_simple(self) -> QWidget:
        """Simplified barrel tab for beginners"""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel(
            "This is the simplified view. Switch to Expert mode for detailed "
            "harmonics calculations and chamber tolerances."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            """
            QLabel {
                background-color: #d5e8f7;
                color: #0d3b66;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """
        )
        layout.addWidget(info)

        # Simple form - just the essentials
        form = QFormLayout()

        # Length
        length_layout = QHBoxLayout()
        self.barrel_length = QDoubleSpinBox()
        self.barrel_length.setRange(250, 900)
        self.barrel_length.setValue(610)
        self.barrel_length.setSuffix(" mm")
        self.barrel_length.setDecimals(0)
        length_layout.addWidget(self.barrel_length)

        self.radio_metric = QRadioButton("mm")
        self.radio_imperial = QRadioButton("inches")
        self.radio_metric.setChecked(True)
        length_layout.addWidget(self.radio_metric)
        length_layout.addWidget(self.radio_imperial)
        length_layout.addStretch()

        form.addRow("Barrel Length:", length_layout)

        # Twist rate
        self.twist_rate = QComboBox()
        self.twist_rate.setEditable(True)
        self.twist_rate.addItems(
            [
                '1:7" / 178mm',
                '1:8" / 203mm',
                '1:9" / 229mm',
                '1:10" / 254mm',
                '1:11" / 279mm',
                '1:12" / 305mm',
            ]
        )
        form.addRow("Twist Rate:", self.twist_rate)

        # Profile (simple)
        self.barrel_profile_simple = QComboBox()
        self.barrel_profile_simple.addItems(
            ["Standard/Sporter", "Medium/Varmint", "Heavy", "Bull Barrel"]
        )
        form.addRow("Barrel Type:", self.barrel_profile_simple)

        layout.addLayout(form)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_barrel_tab(self) -> QWidget:
        """Detailed barrel specifications"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Barrel dimensions
        dim_group = QGroupBox("Barrel Dimensions")
        dim_form = QFormLayout()

        # Length
        length_layout = QHBoxLayout()
        self.barrel_length = QDoubleSpinBox()
        self.barrel_length.setRange(250, 900)
        self.barrel_length.setValue(610)
        self.barrel_length.setSuffix(" mm")
        self.barrel_length.setDecimals(0)
        length_layout.addWidget(self.barrel_length)

        self.radio_metric = QRadioButton("mm")
        self.radio_imperial = QRadioButton("inches")
        self.radio_metric.setChecked(True)
        length_layout.addWidget(self.radio_metric)
        length_layout.addWidget(self.radio_imperial)
        length_layout.addStretch()

        dim_form.addRow("Barrel Length:", length_layout)

        # Twist rate
        self.twist_rate = QComboBox()
        self.twist_rate.setEditable(True)
        self.twist_rate.addItems(
            [
                '1:7" / 178mm',
                '1:8" / 203mm',
                '1:9" / 229mm',
                '1:10" / 254mm',
                '1:11" / 279mm',
                '1:12" / 305mm',
            ]
        )
        dim_form.addRow("Twist Rate:", self.twist_rate)

        dim_group.setLayout(dim_form)
        layout.addWidget(dim_group)

        # Barrel profile
        profile_group = QGroupBox("Barrel Profile & Construction")
        profile_form = QFormLayout()

        self.barrel_profile = QComboBox()
        self.barrel_profile.addItems(
            [
                "Straight/Cylinder (Heavy)",
                "Light Taper (Sporter)",
                "Medium Taper (Hunting)",
                "Heavy Taper (Varmint)",
                "Bull Barrel",
                "Fluted",
            ]
        )
        profile_form.addRow("Profile Type:", self.barrel_profile)

        # Muzzle diameter
        self.muzzle_diameter = QDoubleSpinBox()
        self.muzzle_diameter.setRange(10, 30)
        self.muzzle_diameter.setValue(18)
        self.muzzle_diameter.setSuffix(" mm")
        self.muzzle_diameter.setDecimals(1)
        profile_form.addRow("Muzzle Diameter:", self.muzzle_diameter)

        # Breech diameter
        self.breech_diameter = QDoubleSpinBox()
        self.breech_diameter.setRange(15, 35)
        self.breech_diameter.setValue(25)
        self.breech_diameter.setSuffix(" mm")
        self.breech_diameter.setDecimals(1)
        profile_form.addRow("Breech Diameter:", self.breech_diameter)

        # Material
        self.barrel_material = QComboBox()
        self.barrel_material.addItems(
            [
                "Chrome-Moly Steel",
                "Stainless Steel (416R)",
                "Stainless Steel (17-4PH)",
                "Carbon Fiber Wrapped",
                "Other",
            ]
        )
        profile_form.addRow("Material:", self.barrel_material)

        # Weight
        self.barrel_weight = QSpinBox()
        self.barrel_weight.setRange(500, 5000)
        self.barrel_weight.setValue(1200)
        self.barrel_weight.setSuffix(" g")
        profile_form.addRow("Barrel Weight (approx):", self.barrel_weight)

        profile_group.setLayout(profile_form)
        layout.addWidget(profile_group)

        # Mounting & Bedding
        mount_group = QGroupBox("Mounting & Bedding")
        mount_form = QFormLayout()

        self.free_float = QCheckBox("Yes, the barrel is free floated")
        self.free_float.setChecked(True)
        mount_form.addRow("Free Floating:", self.free_float)

        self.bedding_type = QComboBox()
        self.bedding_type.addItems(
            [
                "Factory (no custom work)",
                "Pillar Bedded",
                "Glass Bedded",
                "Aluminum Block",
                "Chassis System",
            ]
        )
        mount_form.addRow("Bedding Type:", self.bedding_type)

        self.stock_material = QComboBox()
        self.stock_material.addItems(
            [
                "Synthetic/Plastic",
                "Wood (Walnut/Beech)",
                "Laminate",
                "Carbon Fiber",
                "Aluminum Chassis",
            ]
        )
        mount_form.addRow("Stock Material:", self.stock_material)

        mount_group.setLayout(mount_form)
        layout.addWidget(mount_group)

        # Barrel condition
        condition_group = QGroupBox("Barrel Condition")
        condition_form = QFormLayout()

        self.round_count = QSpinBox()
        self.round_count.setRange(0, 10000)
        self.round_count.setSuffix(" shots")
        condition_form.addRow("Total Round Count:", self.round_count)

        self.barrel_condition = QComboBox()
        self.barrel_condition.addItems(
            [
                "New (<100 shots)",
                "Broken in (100-500)",
                "Moderately used (500-1500)",
                "Heavily used (1500-3000)",
                "Worn out (>3000)",
            ]
        )
        condition_form.addRow("Condition:", self.barrel_condition)

        self.throat_erosion = QComboBox()
        self.throat_erosion.addItems(
            [
                "No measurable erosion",
                'Minimal (<0.020")',
                'Moderate (0.020-0.050")',
                'Significant (>0.050")',
            ]
        )
        condition_form.addRow("Throat Erosion:", self.throat_erosion)

        condition_group.setLayout(condition_form)
        layout.addWidget(condition_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_muzzle_tab(self) -> QWidget:
        """Muzzle devices (suppressor, brake, etc.)"""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel(
            "<b>Why is this important?</b><br>"
            "Suppressors and brakes affect barrel harmonics significantly. "
            "Weight and length change barrel nodes and can shift POI (Point of Impact)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #b3d9f2; padding: 10px; border-radius: 5px; color: #0d3b66;"
        )
        layout.addWidget(info)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Barrel context:"))
        self.muzzle_barrel_combo = QComboBox()
        self.muzzle_barrel_combo.currentIndexChanged.connect(
            self.on_muzzle_barrel_changed
        )
        selector_layout.addWidget(self.muzzle_barrel_combo)
        self.muzzle_barrel_hint = QLabel(
            "Suppressor, brake and POI data are stored per selected barrel."
        )
        self.muzzle_barrel_hint.setWordWrap(True)
        selector_layout.addWidget(self.muzzle_barrel_hint, 1)
        layout.addLayout(selector_layout)

        configuration_layout = QHBoxLayout()
        configuration_layout.addWidget(QLabel("Setup:"))
        self.muzzle_configuration_combo = QComboBox()
        self.muzzle_configuration_combo.currentIndexChanged.connect(
            self.on_muzzle_configuration_changed
        )
        configuration_layout.addWidget(self.muzzle_configuration_combo)
        self.active_muzzle_configuration_name = QLineEdit()
        self.active_muzzle_configuration_name.setPlaceholderText(
            "e.g. Match Suppressed, Brake Training Setup"
        )
        self.active_muzzle_configuration_name.editingFinished.connect(
            self.on_muzzle_configuration_name_edited
        )
        configuration_layout.addWidget(self.active_muzzle_configuration_name, 1)
        layout.addLayout(configuration_layout)

        device_group = QGroupBox("Muzzle Device")
        device_form = QFormLayout()

        self.has_device = QCheckBox("Uses suppressor/brake")
        self.has_device.toggled.connect(self.toggle_device_fields)
        device_form.addRow("Har device:", self.has_device)

        self.device_type = QComboBox()
        self.device_type.addItems(
            [
                "None",
                "Suppressor",
                "Muzzle Brake",
                "Flash Hider",
                "Compensator",
            ]
        )
        device_form.addRow("Type:", self.device_type)

        self.device_manufacturer = QLineEdit()
        self.device_manufacturer.setPlaceholderText("e.g. A-TEC, Stalon, SilencerCo")
        device_form.addRow("Manufacturer/Model:", self.device_manufacturer)

        self.device_length = QSpinBox()
        self.device_length.setRange(0, 300)
        self.device_length.setSuffix(" mm")
        device_form.addRow("Length:", self.device_length)

        self.device_weight = QSpinBox()
        self.device_weight.setRange(0, 1000)
        self.device_weight.setSuffix(" g")
        device_form.addRow("Weight:", self.device_weight)

        self.device_diameter = QDoubleSpinBox()
        self.device_diameter.setRange(0, 60)
        self.device_diameter.setSuffix(" mm")
        self.device_diameter.setDecimals(1)
        device_form.addRow("Diameter:", self.device_diameter)

        self.thread_pitch = QComboBox()
        self.thread_pitch.setEditable(True)
        self.thread_pitch.addItems(
            ["M15x1", "M18x1", "5/8-24 UNF", "1/2-28 UNF", "M14x1"]
        )
        device_form.addRow("Thread Pitch:", self.thread_pitch)

        device_group.setLayout(device_form)
        layout.addWidget(device_group)

        # POI shift tracking
        poi_group = QGroupBox("POI Shift (Point of Impact)")
        poi_form = QFormLayout()

        self.poi_tested = QCheckBox("Har testet POI shift")
        poi_form.addRow("Tested:", self.poi_tested)

        self.poi_shift_h = QDoubleSpinBox()
        self.poi_shift_h.setRange(-10, 10)
        self.poi_shift_h.setSuffix(" cm @ 100m")
        self.poi_shift_h.setDecimals(1)
        poi_form.addRow("Horizontal Shift:", self.poi_shift_h)

        self.poi_shift_v = QDoubleSpinBox()
        self.poi_shift_v.setRange(-10, 10)
        self.poi_shift_v.setSuffix(" cm @ 100m")
        self.poi_shift_v.setDecimals(1)
        poi_form.addRow("Vertical Shift:", self.poi_shift_v)

        poi_group.setLayout(poi_form)
        layout.addWidget(poi_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_chamber_tab(self) -> QWidget:
        """Chamber specs and tolerances"""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel(
            "<b>Chamber tolerances affect ES/SD.</b><br>"
            "Tighter chambers usually improve accuracy. Looser chambers can increase ES. "
            "Measure fired and sized cases to find clearance."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #f9e79f; padding: 10px; border-radius: 5px; color: #7d6608;"
        )
        layout.addWidget(info)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Barrel context:"))
        self.chamber_barrel_combo = QComboBox()
        self.chamber_barrel_combo.currentIndexChanged.connect(
            self.on_chamber_barrel_changed
        )
        selector_layout.addWidget(self.chamber_barrel_combo)
        chamber_hint = QLabel(
            "Chamber measurements are stored per selected barrel and mirrored to the active barrel snapshot."
        )
        chamber_hint.setWordWrap(True)
        selector_layout.addWidget(chamber_hint, 1)
        layout.addLayout(selector_layout)

        chamber_group = QGroupBox("Chamber Specifications")
        chamber_form = QFormLayout()

        self.chamber_spec = QComboBox()
        self.chamber_spec.addItems(
            [
                "SAAMI Standard",
                "CIP Standard",
                "Match Chamber",
                "Custom Reamer",
                "Unknown",
            ]
        )
        chamber_form.addRow("Chamber Spec:", self.chamber_spec)

        self.headspace = QDoubleSpinBox()
        self.headspace.setRange(0, 5)
        self.headspace.setSuffix(" mm")
        self.headspace.setDecimals(3)
        self.headspace.setSpecialValueText("Not measured")
        chamber_form.addRow("Headspace (measured):", self.headspace)

        chamber_group.setLayout(chamber_form)
        layout.addWidget(chamber_group)

        # Fired case measurements
        fired_group = QGroupBox("Fired Case Measurements (average)")
        fired_form = QFormLayout()

        fired_info = QLabel(
            "Measure 5-10 fired cases immediately after shooting. "
            "This shows the chamber's actual dimensions."
        )
        fired_info.setWordWrap(True)
        fired_info.setStyleSheet("font-style: italic; color: #7f8c8d;")
        fired_form.addRow("", fired_info)

        self.fired_base = QDoubleSpinBox()
        self.fired_base.setRange(0, 20)
        self.fired_base.setSuffix(" mm")
        self.fired_base.setDecimals(3)
        self.fired_base.setSpecialValueText("Not measured")
        fired_form.addRow("Case Base Diameter:", self.fired_base)

        self.fired_shoulder = QDoubleSpinBox()
        self.fired_shoulder.setRange(0, 20)
        self.fired_shoulder.setSuffix(" mm")
        self.fired_shoulder.setDecimals(3)
        self.fired_shoulder.setSpecialValueText("Not measured")
        fired_form.addRow("Shoulder Diameter:", self.fired_shoulder)

        self.fired_length = QDoubleSpinBox()
        self.fired_length.setRange(0, 100)
        self.fired_length.setSuffix(" mm")
        self.fired_length.setDecimals(3)
        self.fired_length.setSpecialValueText("Not measured")
        fired_form.addRow("Case Length:", self.fired_length)

        fired_group.setLayout(fired_form)
        layout.addWidget(fired_group)

        # Sized case measurements
        sized_group = QGroupBox("Sized Case Measurements")
        sized_form = QFormLayout()

        sized_info = QLabel(
            "Measure the cases AFTER full-length sizing. "
            "The difference between fired and sized equals chamber clearance."
        )
        sized_info.setWordWrap(True)
        sized_info.setStyleSheet("font-style: italic; color: #7f8c8d;")
        sized_form.addRow("", sized_info)

        self.sized_base = QDoubleSpinBox()
        self.sized_base.setRange(0, 20)
        self.sized_base.setSuffix(" mm")
        self.sized_base.setDecimals(3)
        self.sized_base.setSpecialValueText("Not measured")
        sized_form.addRow("Case Base Diameter:", self.sized_base)

        self.sized_shoulder = QDoubleSpinBox()
        self.sized_shoulder.setRange(0, 20)
        self.sized_shoulder.setSuffix(" mm")
        self.sized_shoulder.setDecimals(3)
        self.sized_shoulder.setSpecialValueText("Not measured")
        sized_form.addRow("Shoulder Diameter:", self.sized_shoulder)

        self.shoulder_bump = QDoubleSpinBox()
        self.shoulder_bump.setRange(0, 1)
        self.shoulder_bump.setSuffix(" mm")
        self.shoulder_bump.setDecimals(3)
        self.shoulder_bump.setSpecialValueText("Auto")
        sized_form.addRow("Shoulder Bump:", self.shoulder_bump)

        sized_group.setLayout(sized_form)
        layout.addWidget(sized_group)

        # Calculated clearances (auto-filled)
        clear_group = QGroupBox("Calculated Clearance")
        clear_form = QFormLayout()

        self.clearance_base = QLabel("- (enter measurements)")
        clear_form.addRow("Base Clearance:", self.clearance_base)

        self.clearance_shoulder = QLabel("- (enter measurements)")
        clear_form.addRow("Shoulder Clearance:", self.clearance_shoulder)

        # Connect spinboxes to auto-calculate
        self.fired_base.valueChanged.connect(self.calculate_clearances)
        self.sized_base.valueChanged.connect(self.calculate_clearances)
        self.fired_shoulder.valueChanged.connect(self.calculate_clearances)
        self.sized_shoulder.valueChanged.connect(self.calculate_clearances)

        clear_group.setLayout(clear_form)
        layout.addWidget(clear_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_bullet_profiles_tab(self) -> QWidget:
        """Bullet-specific freebore measurements"""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel(
            "<b>Each bullet type has different freebore.</b><br>"
            "Sierra TMK and Berger Hybrid have different ogive shapes. "
            "Measure and save the optimal jump for each bullet you use."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #a8d5ba; padding: 10px; border-radius: 5px; color: #1a3a2a;"
        )
        layout.addWidget(info)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Barrel context:"))
        self.bullet_profile_barrel_combo = QComboBox()
        self.bullet_profile_barrel_combo.currentIndexChanged.connect(
            self.on_bullet_profile_barrel_changed
        )
        selector_layout.addWidget(self.bullet_profile_barrel_combo)
        self.bullet_profile_barrel_hint = QLabel(
            "Bullet profiles and jump measurements are stored per selected barrel."
        )
        self.bullet_profile_barrel_hint.setWordWrap(True)
        selector_layout.addWidget(self.bullet_profile_barrel_hint, 1)
        layout.addLayout(selector_layout)

        # Add bullet profile button
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Bullet Profile")
        add_btn.clicked.connect(self.add_bullet_profile)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Table of bullet profiles
        self.bullet_profiles_table = QTableWidget()
        self.bullet_profiles_table.setColumnCount(8)
        self.bullet_profiles_table.setHorizontalHeaderLabels(
            [
                "Bullet",
                "Weight (gr)",
                "Jam Length (COAL)",
                "Jam Length (CBTO)",
                "Optimal Jump",
                "Mag Max COAL",
                "Method",
                "Delete",
            ]
        )
        hdr = self.bullet_profiles_table.horizontalHeader()
        if hdr is not None:
            hdr.setStretchLastSection(True)
        layout.addWidget(self.bullet_profiles_table)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_preview_tab(self) -> QWidget:
        """Visual preview of rifle configuration"""
        widget = QWidget()
        layout = QVBoxLayout()

        preview_label = QLabel("<b>Visual Overview</b>")
        preview_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(preview_label)

        # Summary display
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setHtml(self.generate_preview_html())
        layout.addWidget(self.preview_text)

        # Update preview button
        update_btn = QPushButton("Update Preview")
        update_btn.clicked.connect(self.update_preview)
        layout.addWidget(update_btn)

        widget.setLayout(layout)
        return widget

    def toggle_device_fields(self, checked):
        """Enable/disable device fields"""
        self.device_type.setEnabled(checked)
        self.device_manufacturer.setEnabled(checked)
        self.device_length.setEnabled(checked)
        self.device_weight.setEnabled(checked)
        self.device_diameter.setEnabled(checked)
        self.thread_pitch.setEnabled(checked)

    def calculate_clearances(self):
        """Auto-calculate chamber clearances"""
        if self.fired_base.value() > 0 and self.sized_base.value() > 0:
            clearance = (
                self.fired_base.value() - self.sized_base.value()
            ) * 1000  # Convert to microns
            self.clearance_base.setText(f'{clearance:.0f} μm ({clearance/25.4:.4f}")')

            # Color code based on value
            if clearance < 50:
                self.clearance_base.setStyleSheet("color: green; font-weight: bold;")
            elif clearance < 100:
                self.clearance_base.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.clearance_base.setStyleSheet("color: red; font-weight: bold;")

        if self.fired_shoulder.value() > 0 and self.sized_shoulder.value() > 0:
            clearance = (
                self.fired_shoulder.value() - self.sized_shoulder.value()
            ) * 1000
            self.clearance_shoulder.setText(
                f'{clearance:.0f} μm ({clearance/25.4:.4f}")'
            )

            if clearance < 25:
                self.clearance_shoulder.setStyleSheet(
                    "color: green; font-weight: bold;"
                )
            elif clearance < 75:
                self.clearance_shoulder.setStyleSheet(
                    "color: orange; font-weight: bold;"
                )
            else:
                self.clearance_shoulder.setStyleSheet("color: red; font-weight: bold;")

    def add_bullet_profile(self):
        """Add a bullet profile entry"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Bullet Profile")
        dialog_layout = QFormLayout()

        bullet_name = QLineEdit()
        bullet_weight = QDoubleSpinBox()
        bullet_weight.setRange(40, 250)
        bullet_weight.setSuffix(" gr")

        jam_length_coal = QDoubleSpinBox()
        jam_length_coal.setRange(50, 100)
        jam_length_coal.setSuffix(" mm")
        jam_length_coal.setDecimals(3)

        jam_length = QDoubleSpinBox()
        jam_length.setRange(40, 80)
        jam_length.setSuffix(" mm")
        jam_length.setDecimals(3)

        optimal_jump = QDoubleSpinBox()
        optimal_jump.setRange(0, 2)
        optimal_jump.setSuffix(" mm")
        optimal_jump.setDecimals(3)

        mag_max = QDoubleSpinBox()
        mag_max.setRange(50, 100)
        mag_max.setSuffix(" mm")
        mag_max.setDecimals(2)

        measurement_method = QComboBox()
        measurement_method.addItems(
            [
                "hornady_oal_gauge",
                "comparator",
                "fired_case_method",
                "split_neck",
                "manual",
            ]
        )

        dialog_layout.addRow("Bullet Name:", bullet_name)
        dialog_layout.addRow("Weight:", bullet_weight)
        dialog_layout.addRow("Jam Length (COAL):", jam_length_coal)
        dialog_layout.addRow("Jam Length (CBTO):", jam_length)
        dialog_layout.addRow("Optimal Jump:", optimal_jump)
        dialog_layout.addRow("Magazine Max COAL:", mag_max)
        dialog_layout.addRow("Method:", measurement_method)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addRow(buttons)

        dialog.setLayout(dialog_layout)

        if dialog.exec():
            row = self.bullet_profiles_table.rowCount()
            self.bullet_profiles_table.insertRow(row)

            self.bullet_profiles_table.setItem(
                row, 0, QTableWidgetItem(bullet_name.text())
            )
            self.bullet_profiles_table.setItem(
                row, 1, QTableWidgetItem(f"{bullet_weight.value()}")
            )
            self.bullet_profiles_table.setItem(
                row, 2, QTableWidgetItem(f"{jam_length_coal.value():.3f}")
            )
            self.bullet_profiles_table.setItem(
                row, 3, QTableWidgetItem(f"{jam_length.value():.3f}")
            )
            self.bullet_profiles_table.setItem(
                row, 4, QTableWidgetItem(f"{optimal_jump.value():.3f}")
            )
            self.bullet_profiles_table.setItem(
                row, 5, QTableWidgetItem(f"{mag_max.value():.2f}")
            )
            self.bullet_profiles_table.setItem(
                row, 6, QTableWidgetItem(measurement_method.currentText())
            )

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(
                lambda: self.bullet_profiles_table.removeRow(row)
            )
            self.bullet_profiles_table.setCellWidget(row, 7, delete_btn)

    def generate_preview_html(self) -> str:
        """Generate visual preview HTML"""
        return """
        <h2>Firearm Profile Overview</h2>
        <p>Fill out the fields in the other tabs, then click "Update Preview" to see the summary.</p>
        """

    def update_preview(self):
        """Update preview with current data"""
        html = "<h2>Firearm Profile Summary</h2>"

        html += f"<h3>{self.name.text() or 'Unknown Firearm'}</h3>"
        html += f"<p><b>Manufacturer:</b> {self.manufacturer.text()}<br>"
        html += f"<b>Caliber:</b> {self.caliber.currentText()}<br>"
        html += f"<b>Action:</b> {self.action_type.currentText()}</p>"

        html += "<h3>Barrel Specs</h3>"
        html += f"<p><b>Length:</b> {self.barrel_length.value():.0f} mm<br>"
        html += f"<b>Twist:</b> {self.twist_rate.currentText()}<br>"

        # Barrel profile - check which mode we're in
        if self.user_mode == "beginner":
            html += f"<b>Profile:</b> {self.barrel_profile_simple.currentText()}</p>"
        else:
            html += f"<b>Profile:</b> {self.barrel_profile.currentText()}<br>"
            html += f"<b>Material:</b> {self.barrel_material.currentText()}<br>"
            html += f"<b>Weight:</b> {self.barrel_weight.value()} g</p>"

        # Expert-only fields
        if self.user_mode == "expert":
            if self.has_device.isChecked():
                html += "<h3>Muzzle Device</h3>"
                html += f"<p><b>Type:</b> {self.device_type.currentText()}<br>"
                html += f"<b>Model:</b> {self.device_manufacturer.text()}<br>"
                html += f"<b>Length:</b> {self.device_length.value()} mm<br>"
                html += f"<b>Weight:</b> {self.device_weight.value()} g</p>"

            if self.fired_base.value() > 0:
                html += "<h3>Chamber Tolerances</h3>"
                html += f"<p>{self.clearance_base.text()}<br>"
                html += f"{self.clearance_shoulder.text()}</p>"

        self.preview_text.setHtml(html)

    def on_mode_changed(self, checked):
        """Handle user mode toggle"""
        if not checked:  # Only respond to button being checked, not unchecked
            return

        # Determine new mode
        new_mode = "beginner" if self.mode_beginner.isChecked() else "expert"

        if new_mode == self.user_mode:
            return  # No change

        # Warn if switching from expert to beginner
        if new_mode == "beginner":
            reply = QMessageBox.question(
                self,
                "Switch to Beginner Mode",
                "This will hide advanced fields for harmonics calculations, "
                "chamber tolerances, and bullet profiles.\n\n"
                "Data will not be deleted, only hidden. You can switch back at any time.\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                # Revert radio button
                self.mode_expert.setChecked(True)
                return

        # Update mode and rebuild tabs
        self.user_mode = new_mode
        self.rebuild_tabs()

    def rebuild_tabs(self):
        """Rebuild tabs based on current user mode"""
        # Clear all tabs
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

        # Re-add tabs based on mode
        self.tabs.addTab(self.create_basic_tab(), "Basic")

        if self.user_mode == "beginner":
            self.tabs.addTab(self.create_barrel_tab_simple(), "Barrel")
        else:
            self.tabs.addTab(self.create_barrel_tab(), "Barrel Details")
            self.tabs.addTab(self.create_muzzle_tab(), "Suppressor/Brake")
            self.tabs.addTab(self.create_chamber_tab(), "Chamber & Tolerances")
            self.tabs.addTab(self.create_bullet_profiles_tab(), "Bullet Profiles")
            self.tabs.addTab(self.create_preview_tab(), "Visual Overview")

    def _set_user_mode(self, mode: str) -> None:
        if mode not in {"beginner", "expert"}:
            return
        if mode == self.user_mode:
            return
        self.user_mode = mode
        self.mode_beginner.blockSignals(True)
        self.mode_expert.blockSignals(True)
        self.mode_beginner.setChecked(mode == "beginner")
        self.mode_expert.setChecked(mode == "expert")
        self.mode_beginner.blockSignals(False)
        self.mode_expert.blockSignals(False)
        self.rebuild_tabs()

    @staticmethod
    def _parse_twist_inches(text: str) -> Optional[float]:
        match = re.search(r"1:([0-9]+(?:\.[0-9]+)?)", text)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _parse_optional_float(value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_optional_int(value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _set_combo_value(self, combo: QComboBox, value: Optional[str]) -> None:
        if not value:
            return
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            if combo.isEditable():
                combo.setCurrentText(value)
            else:
                combo.addItem(value)
                combo.setCurrentIndex(combo.count() - 1)

    def _get_barrel_length_mm(self) -> float:
        value = self.barrel_length.value()
        if getattr(self, "radio_imperial", None) and self.radio_imperial.isChecked():
            return value * 25.4
        return value

    def _collect_bullet_profiles(self) -> list[dict[str, Any]]:
        profiles = []
        if not hasattr(self, "bullet_profiles_table"):
            return profiles

        for row in range(self.bullet_profiles_table.rowCount()):
            name_item = self.bullet_profiles_table.item(row, 0)
            if name_item is None or not name_item.text().strip():
                continue
            profiles.append(
                {
                    "bullet_name": name_item.text().strip(),
                    "bullet_weight_gr": (
                        self.bullet_profiles_table.item(row, 1).text()
                        if self.bullet_profiles_table.item(row, 1)
                        else ""
                    ),
                    "jam_length_coal_mm": (
                        self.bullet_profiles_table.item(row, 2).text()
                        if self.bullet_profiles_table.item(row, 2)
                        else ""
                    ),
                    "jam_length_cbto_mm": (
                        self.bullet_profiles_table.item(row, 3).text()
                        if self.bullet_profiles_table.item(row, 3)
                        else ""
                    ),
                    "optimal_jump_mm": (
                        self.bullet_profiles_table.item(row, 4).text()
                        if self.bullet_profiles_table.item(row, 4)
                        else ""
                    ),
                    "mag_max_coal_mm": (
                        self.bullet_profiles_table.item(row, 5).text()
                        if self.bullet_profiles_table.item(row, 5)
                        else ""
                    ),
                    "measurement_method": (
                        self.bullet_profiles_table.item(row, 6).text()
                        if self.bullet_profiles_table.item(row, 6)
                        else "manual"
                    ),
                }
            )
        return profiles

    def _load_existing_profile_details(self, rifle_id: int) -> dict[str, Any]:
        existing = self.db.execute_query(
            "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
            (rifle_id,),
        )
        if not existing or not existing[0].get("profile_json"):
            return {}
        try:
            parsed = json.loads(existing[0]["profile_json"])
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _save_profile_details(
        self, rifle_id: int, details: dict[str, Any]
    ) -> dict[str, Any]:
        merged = self._load_existing_profile_details(rifle_id)
        merged.update(details)
        merged = self._sync_explicit_barrel_configurations(merged)
        payload = {
            "rifle_id": rifle_id,
            "profile_json": json.dumps(merged, ensure_ascii=False),
            "updated_at": datetime.now().isoformat(),
        }
        existing = self.db.execute_query(
            "SELECT id FROM rifle_profile_details WHERE rifle_id = ?",
            (rifle_id,),
        )
        if existing:
            self.db.update(
                "rifle_profile_details", payload, "rifle_id = ?", (rifle_id,)
            )
        else:
            self.db.insert("rifle_profile_details", payload)
        return merged

    def _resolve_active_barrel_context(
        self, details: dict[str, Any]
    ) -> tuple[Optional[str], Optional[str]]:
        active_barrel_id = str(details.get("active_barrel_id") or "").strip() or None
        barrels = details.get("barrels", [])
        if active_barrel_id and isinstance(barrels, list):
            for barrel in barrels:
                if (
                    isinstance(barrel, dict)
                    and str(barrel.get("id") or "").strip() == active_barrel_id
                ):
                    barrel_name = str(barrel.get("name") or "").strip() or None
                    return active_barrel_id, barrel_name
        return active_barrel_id, None

    def _sync_explicit_barrel_configurations(
        self, details: dict[str, Any]
    ) -> dict[str, Any]:
        working = dict(details)
        active_barrel_id, active_barrel_name = self._resolve_active_barrel_context(
            working
        )
        configurations = working.get("barrel_configurations", [])
        normalized_configurations = [
            dict(configuration)
            for configuration in configurations
            if isinstance(configuration, dict)
        ]
        explicit_active_id = (
            str(working.get("active_barrel_configuration_id") or "").strip() or None
        )
        explicit_active_name = (
            str(working.get("active_barrel_configuration_name") or "").strip() or None
        )

        if not active_barrel_id:
            if normalized_configurations:
                working["barrel_configurations"] = normalized_configurations
            else:
                working.pop("barrel_configurations", None)
            return working

        active_barrel = {}
        for barrel in working.get("barrels", []):
            if (
                isinstance(barrel, dict)
                and str(barrel.get("id") or "").strip() == active_barrel_id
            ):
                active_barrel = dict(barrel)
                break

        derived_context = build_derived_barrel_configuration_context(
            barrel_id=active_barrel_id,
            barrel=active_barrel,
            rifle_data=working,
        )
        derived_configuration_id = (
            str(derived_context.get("barrel_configuration_id") or "").strip() or None
        )
        target_configuration_id = explicit_active_id or derived_configuration_id
        if not target_configuration_id:
            if normalized_configurations:
                working["barrel_configurations"] = normalized_configurations
            return working

        existing_configuration = None
        for configuration in normalized_configurations:
            configuration_id = str(configuration.get("id") or "").strip() or None
            if configuration_id and configuration_id == target_configuration_id:
                existing_configuration = configuration
                break
        if existing_configuration is None and derived_configuration_id:
            for configuration in normalized_configurations:
                configuration_id = str(configuration.get("id") or "").strip() or None
                configuration_barrel_id = (
                    str(configuration.get("barrel_id") or "").strip() or None
                )
                if configuration_id == derived_configuration_id or (
                    configuration_barrel_id == active_barrel_id
                    and bool(configuration.get("is_active"))
                ):
                    existing_configuration = configuration
                    target_configuration_id = (
                        configuration_id or target_configuration_id
                    )
                    break

        merged_snapshot = {}
        if isinstance((existing_configuration or {}).get("snapshot"), dict):
            merged_snapshot.update(existing_configuration.get("snapshot") or {})
        merged_snapshot.update(
            derived_context.get("barrel_configuration_snapshot") or {}
        )
        merged_snapshot["barrel_id"] = active_barrel_id
        merged_snapshot["barrel_name"] = active_barrel_name

        configuration_name = (
            str(
                explicit_active_name
                or (existing_configuration or {}).get("name")
                or derived_context.get("barrel_configuration_name")
                or ""
            ).strip()
            or None
        )

        synced_configuration = {
            "id": target_configuration_id,
            "name": configuration_name,
            "barrel_id": active_barrel_id,
            "barrel_name": active_barrel_name,
            "is_active": True,
            "muzzle_device_type": merged_snapshot.get("muzzle_device_type"),
            "muzzle_device_model": merged_snapshot.get("muzzle_device_model"),
            "snapshot": merged_snapshot,
        }

        updated_configurations = []
        replaced = False
        for configuration in normalized_configurations:
            configuration_copy = dict(configuration)
            configuration_id = str(configuration_copy.get("id") or "").strip() or None
            configuration_barrel_id = (
                str(configuration_copy.get("barrel_id") or "").strip() or None
            )
            if configuration_id == target_configuration_id:
                updated_configurations.append(synced_configuration)
                replaced = True
                continue
            if configuration_barrel_id == active_barrel_id:
                configuration_copy["is_active"] = False
            updated_configurations.append(configuration_copy)
        if not replaced:
            updated_configurations.append(synced_configuration)

        working["barrel_configurations"] = updated_configurations
        working["active_barrel_configuration_id"] = target_configuration_id
        working["active_barrel_configuration_name"] = configuration_name
        return working

    def _get_selected_bullet_profile_barrel_id(self) -> Optional[str]:
        combo = getattr(self, "bullet_profile_barrel_combo", None)
        if combo is None:
            return None
        selected = combo.currentData()
        if selected in (None, ""):
            return None
        return str(selected)

    def _get_selected_chamber_barrel_id(self) -> Optional[str]:
        combo = getattr(self, "chamber_barrel_combo", None)
        if combo is None:
            return None
        selected = combo.currentData()
        if selected in (None, ""):
            return None
        return str(selected)

    def _get_selected_muzzle_barrel_id(self) -> Optional[str]:
        combo = getattr(self, "muzzle_barrel_combo", None)
        if combo is None:
            return None
        selected = combo.currentData()
        if selected in (None, ""):
            return None
        return str(selected)

    def _refresh_bullet_profile_barrel_selector(self, details: dict[str, Any]) -> None:
        combo = getattr(self, "bullet_profile_barrel_combo", None)
        if combo is None:
            return
        combo.blockSignals(True)
        combo.clear()
        barrels = details.get("barrels", [])
        active_barrel_id = str(details.get("active_barrel_id") or "").strip() or None
        if isinstance(barrels, list) and barrels:
            for barrel in barrels:
                if not isinstance(barrel, dict):
                    continue
                barrel_id = str(barrel.get("id") or "").strip()
                if not barrel_id:
                    continue
                combo.addItem(
                    str(barrel.get("name") or barrel_id).strip() or barrel_id, barrel_id
                )
            target_id = active_barrel_id or str(combo.itemData(0) or "").strip() or None
            for index in range(combo.count()):
                if str(combo.itemData(index) or "").strip() == str(target_id or ""):
                    combo.setCurrentIndex(index)
                    break
            self._bullet_profiles_current_barrel_id = target_id
            if target_id:
                details["active_barrel_id"] = target_id
        else:
            combo.addItem("Primary barrel", "")
            self._bullet_profiles_current_barrel_id = None
        combo.blockSignals(False)

    def _refresh_chamber_barrel_selector(self, details: dict[str, Any]) -> None:
        combo = getattr(self, "chamber_barrel_combo", None)
        if combo is None:
            return
        combo.blockSignals(True)
        combo.clear()
        barrels = details.get("barrels", [])
        active_barrel_id = str(details.get("active_barrel_id") or "").strip() or None
        if isinstance(barrels, list) and barrels:
            for barrel in barrels:
                if not isinstance(barrel, dict):
                    continue
                barrel_id = str(barrel.get("id") or "").strip()
                if not barrel_id:
                    continue
                combo.addItem(
                    str(barrel.get("name") or barrel_id).strip() or barrel_id, barrel_id
                )
            target_id = active_barrel_id or str(combo.itemData(0) or "").strip() or None
            for index in range(combo.count()):
                if str(combo.itemData(index) or "").strip() == str(target_id or ""):
                    combo.setCurrentIndex(index)
                    break
            self._chamber_current_barrel_id = target_id
            if target_id:
                details["active_barrel_id"] = target_id
        else:
            combo.addItem("Primary barrel", "")
            self._chamber_current_barrel_id = None
        combo.blockSignals(False)

    def _refresh_muzzle_barrel_selector(self, details: dict[str, Any]) -> None:
        combo = getattr(self, "muzzle_barrel_combo", None)
        if combo is None:
            return
        combo.blockSignals(True)
        combo.clear()
        barrels = details.get("barrels", [])
        active_barrel_id = str(details.get("active_barrel_id") or "").strip() or None
        if isinstance(barrels, list) and barrels:
            for barrel in barrels:
                if not isinstance(barrel, dict):
                    continue
                barrel_id = str(barrel.get("id") or "").strip()
                if not barrel_id:
                    continue
                combo.addItem(
                    str(barrel.get("name") or barrel_id).strip() or barrel_id, barrel_id
                )
            target_id = active_barrel_id or str(combo.itemData(0) or "").strip() or None
            for index in range(combo.count()):
                if str(combo.itemData(index) or "").strip() == str(target_id or ""):
                    combo.setCurrentIndex(index)
                    break
            self._muzzle_current_barrel_id = target_id
            if target_id:
                details["active_barrel_id"] = target_id
        else:
            combo.addItem("Primary barrel", "")
            self._muzzle_current_barrel_id = None
        combo.blockSignals(False)

    def _get_selected_muzzle_configuration_id(self) -> Optional[str]:
        combo = getattr(self, "muzzle_configuration_combo", None)
        if combo is None:
            return None
        selected = combo.currentData()
        if selected in (None, ""):
            return None
        return str(selected)

    def _get_active_muzzle_configuration_entry(
        self,
        details: dict[str, Any],
        *,
        barrel_id: Optional[str] = None,
        configuration_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        target_barrel_id = barrel_id
        if not target_barrel_id:
            selector = getattr(self, "_get_selected_muzzle_barrel_id", None)
            target_barrel_id = selector() if callable(selector) else None
        if not target_barrel_id:
            target_barrel_id, _ = self._resolve_active_barrel_context(details)

        target_configuration_id = configuration_id
        if not target_configuration_id:
            selector = getattr(self, "_get_selected_muzzle_configuration_id", None)
            target_configuration_id = selector() if callable(selector) else None
        if not target_configuration_id:
            target_configuration_id = (
                str(details.get("active_barrel_configuration_id") or "").strip() or None
            )

        configurations = details.get("barrel_configurations", [])
        matching = []
        if isinstance(configurations, list):
            for configuration in configurations:
                if not isinstance(configuration, dict):
                    continue
                configuration_barrel_id = (
                    str(configuration.get("barrel_id") or "").strip() or None
                )
                if (
                    target_barrel_id
                    and configuration_barrel_id
                    and configuration_barrel_id != target_barrel_id
                ):
                    continue
                if target_barrel_id and not configuration_barrel_id:
                    continue
                matching.append(dict(configuration))

        if target_configuration_id:
            for configuration in matching:
                configuration_key = str(configuration.get("id") or "").strip() or None
                if configuration_key == target_configuration_id:
                    return configuration
        for configuration in matching:
            if bool(configuration.get("is_active")):
                return configuration
        return matching[0] if matching else None

    def _refresh_muzzle_configuration_selector(self, details: dict[str, Any]) -> None:
        combo = getattr(self, "muzzle_configuration_combo", None)
        if combo is None:
            return
        combo.blockSignals(True)
        combo.clear()

        barrel_id = (
            self._get_selected_muzzle_barrel_id()
            or self._resolve_active_barrel_context(details)[0]
        )
        matching_configurations = []
        configurations = details.get("barrel_configurations", [])
        if isinstance(configurations, list):
            for configuration in configurations:
                if not isinstance(configuration, dict):
                    continue
                configuration_barrel_id = (
                    str(configuration.get("barrel_id") or "").strip() or None
                )
                if (
                    barrel_id
                    and configuration_barrel_id
                    and configuration_barrel_id != barrel_id
                ):
                    continue
                if barrel_id and not configuration_barrel_id:
                    continue
                matching_configurations.append(dict(configuration))

        if matching_configurations:
            for configuration in matching_configurations:
                configuration_id = str(configuration.get("id") or "").strip()
                configuration_name = str(
                    configuration.get("name") or configuration_id or "Current setup"
                ).strip()
                combo.addItem(configuration_name or "Current setup", configuration_id)
            target_configuration_id = (
                str(details.get("active_barrel_configuration_id") or "").strip()
                or str(combo.itemData(0) or "").strip()
            )
        else:
            active_barrel = {}
            barrels = details.get("barrels", [])
            if barrel_id and isinstance(barrels, list):
                for barrel in barrels:
                    if (
                        isinstance(barrel, dict)
                        and str(barrel.get("id") or "").strip() == barrel_id
                    ):
                        active_barrel = dict(barrel)
                        break
            derived_context = build_derived_barrel_configuration_context(
                barrel_id=barrel_id,
                barrel=active_barrel,
                rifle_data=details,
            )
            fallback_id = str(
                derived_context.get("barrel_configuration_id") or "current-setup"
            ).strip()
            fallback_name = str(
                details.get("active_barrel_configuration_name")
                or derived_context.get("barrel_configuration_name")
                or "Current setup"
            ).strip()
            combo.addItem(fallback_name or "Current setup", fallback_id)
            target_configuration_id = fallback_id

        for index in range(combo.count()):
            if str(combo.itemData(index) or "").strip() == str(
                target_configuration_id or ""
            ):
                combo.setCurrentIndex(index)
                break
        details["active_barrel_configuration_id"] = target_configuration_id or None
        details["active_barrel_configuration_name"] = (
            str(combo.currentText() or "").strip() or None
        )
        combo.blockSignals(False)

    def _collect_muzzle_details(self) -> dict[str, Any]:
        has_device = (
            self.has_device.isChecked() if hasattr(self, "has_device") else False
        )
        return {
            "has_muzzle_device": has_device,
            "device_type": (
                self.device_type.currentText()
                if hasattr(self, "device_type") and has_device
                else None
            ),
            "device_manufacturer": (
                self.device_manufacturer.text()
                if hasattr(self, "device_manufacturer") and has_device
                else None
            ),
            "device_length": (
                self.device_length.value()
                if hasattr(self, "device_length") and has_device
                else None
            ),
            "device_weight": (
                self.device_weight.value()
                if hasattr(self, "device_weight") and has_device
                else None
            ),
            "device_diameter": (
                self.device_diameter.value()
                if hasattr(self, "device_diameter")
                and has_device
                and self.device_diameter.value() > 0
                else None
            ),
            "thread_pitch": (
                self.thread_pitch.currentText()
                if hasattr(self, "thread_pitch")
                else None
            ),
            "poi_tested": (
                self.poi_tested.isChecked() if hasattr(self, "poi_tested") else False
            ),
            "poi_shift_h": (
                self.poi_shift_h.value() if hasattr(self, "poi_shift_h") else 0.0
            ),
            "poi_shift_v": (
                self.poi_shift_v.value() if hasattr(self, "poi_shift_v") else 0.0
            ),
            "active_barrel_configuration_name": (
                self.active_muzzle_configuration_name.text().strip()
                if hasattr(self, "active_muzzle_configuration_name")
                else None
            ),
        }

    def _populate_muzzle_fields(self, details: dict[str, Any]) -> None:
        has_device = bool(details.get("has_muzzle_device"))
        if hasattr(self, "has_device"):
            self.has_device.setChecked(has_device)
        if hasattr(self, "device_type"):
            self._set_combo_value(
                self.device_type, details.get("device_type") or "None"
            )
        if hasattr(self, "device_manufacturer"):
            self.device_manufacturer.setText(
                str(details.get("device_manufacturer") or "")
            )
        if hasattr(self, "device_length"):
            self.device_length.setValue(int(details.get("device_length") or 0))
        if hasattr(self, "device_weight"):
            self.device_weight.setValue(int(details.get("device_weight") or 0))
        if hasattr(self, "device_diameter"):
            self.device_diameter.setValue(float(details.get("device_diameter") or 0))
        if hasattr(self, "thread_pitch"):
            self._set_combo_value(self.thread_pitch, details.get("thread_pitch"))
        if hasattr(self, "poi_tested"):
            self.poi_tested.setChecked(bool(details.get("poi_tested", False)))
        if hasattr(self, "poi_shift_h"):
            self.poi_shift_h.setValue(float(details.get("poi_shift_h") or 0))
        if hasattr(self, "poi_shift_v"):
            self.poi_shift_v.setValue(float(details.get("poi_shift_v") or 0))
        if hasattr(self, "active_muzzle_configuration_name"):
            self.active_muzzle_configuration_name.blockSignals(True)
            self.active_muzzle_configuration_name.setText(
                str(details.get("active_barrel_configuration_name") or "").strip()
            )
            self.active_muzzle_configuration_name.blockSignals(False)
        if hasattr(self, "toggle_device_fields"):
            self.toggle_device_fields(has_device)

    def _get_active_barrel_muzzle_details(
        self, details: dict[str, Any]
    ) -> dict[str, Any]:
        selector = getattr(self, "_get_selected_muzzle_barrel_id", None)
        barrel_id = selector() if callable(selector) else None
        if not barrel_id:
            barrel_id, _ = self._resolve_active_barrel_context(details)
        configuration_selector = getattr(
            self, "_get_selected_muzzle_configuration_id", None
        )
        configuration_id = (
            configuration_selector() if callable(configuration_selector) else None
        )
        configuration = self._get_active_muzzle_configuration_entry(
            details,
            barrel_id=barrel_id,
            configuration_id=configuration_id,
        )
        barrels = details.get("barrels", [])
        if barrel_id and isinstance(barrels, list):
            for barrel in barrels:
                if not isinstance(barrel, dict):
                    continue
                if str(barrel.get("id") or "").strip() != barrel_id:
                    continue
                resolved = {
                    "has_muzzle_device": bool(
                        barrel.get("has_muzzle_device")
                        or barrel.get("muzzle_device_type")
                        or details.get("has_muzzle_device")
                    ),
                    "device_type": barrel.get("muzzle_device_type")
                    or details.get("device_type"),
                    "device_manufacturer": barrel.get("muzzle_device_model")
                    or details.get("device_manufacturer"),
                    "device_length": (
                        barrel.get("muzzle_device_length_mm")
                        if barrel.get("muzzle_device_length_mm") is not None
                        else details.get("device_length")
                    ),
                    "device_weight": (
                        barrel.get("muzzle_device_weight_g")
                        if barrel.get("muzzle_device_weight_g") is not None
                        else details.get("device_weight")
                    ),
                    "device_diameter": (
                        barrel.get("muzzle_device_diameter_mm")
                        if barrel.get("muzzle_device_diameter_mm") is not None
                        else details.get("device_diameter")
                    ),
                    "thread_pitch": barrel.get("thread_pitch")
                    or details.get("thread_pitch"),
                    "poi_tested": (
                        barrel.get("poi_tested")
                        if barrel.get("poi_tested") is not None
                        else details.get("poi_tested", False)
                    ),
                    "poi_shift_h": (
                        barrel.get("poi_shift_h")
                        if barrel.get("poi_shift_h") is not None
                        else details.get("poi_shift_h")
                    ),
                    "poi_shift_v": (
                        barrel.get("poi_shift_v")
                        if barrel.get("poi_shift_v") is not None
                        else details.get("poi_shift_v")
                    ),
                    "active_barrel_configuration_name": str(
                        (configuration or {}).get("name")
                        or details.get("active_barrel_configuration_name")
                        or ""
                    ).strip()
                    or None,
                }
                snapshot = (configuration or {}).get("snapshot")
                if isinstance(snapshot, dict):
                    resolved.update(
                        {
                            "has_muzzle_device": bool(
                                snapshot.get("muzzle_device_type")
                                and str(snapshot.get("muzzle_device_type"))
                                .strip()
                                .lower()
                                != "none"
                            ),
                            "device_type": snapshot.get("muzzle_device_type")
                            or resolved.get("device_type"),
                            "device_manufacturer": snapshot.get("muzzle_device_model")
                            or resolved.get("device_manufacturer"),
                            "device_weight": (
                                snapshot.get("muzzle_device_weight_g")
                                if snapshot.get("muzzle_device_weight_g") is not None
                                else resolved.get("device_weight")
                            ),
                            "thread_pitch": snapshot.get("thread_pitch")
                            or resolved.get("thread_pitch"),
                            "poi_shift_h": (
                                snapshot.get("poi_shift_h")
                                if snapshot.get("poi_shift_h") is not None
                                else resolved.get("poi_shift_h")
                            ),
                            "poi_shift_v": (
                                snapshot.get("poi_shift_v")
                                if snapshot.get("poi_shift_v") is not None
                                else resolved.get("poi_shift_v")
                            ),
                        }
                    )
                return resolved
        return {
            "has_muzzle_device": details.get("has_muzzle_device", False),
            "device_type": details.get("device_type"),
            "device_manufacturer": details.get("device_manufacturer"),
            "device_length": details.get("device_length"),
            "device_weight": details.get("device_weight"),
            "device_diameter": details.get("device_diameter"),
            "thread_pitch": details.get("thread_pitch"),
            "poi_tested": details.get("poi_tested", False),
            "poi_shift_h": details.get("poi_shift_h"),
            "poi_shift_v": details.get("poi_shift_v"),
            "active_barrel_configuration_name": details.get(
                "active_barrel_configuration_name"
            ),
        }

    def _store_active_barrel_muzzle_details(
        self, details: dict[str, Any], muzzle_details: dict[str, Any]
    ) -> dict[str, Any]:
        normalized = dict(muzzle_details)
        selector = getattr(self, "_get_selected_muzzle_barrel_id", None)
        barrel_id = selector() if callable(selector) else None
        if not barrel_id:
            barrel_id, _ = self._resolve_active_barrel_context(details)
        barrels = details.get("barrels", [])
        if isinstance(barrels, list):
            updated_barrels = []
            matched = False
            for barrel in barrels:
                if not isinstance(barrel, dict):
                    updated_barrels.append(barrel)
                    continue
                barrel_copy = dict(barrel)
                if barrel_id and str(barrel_copy.get("id") or "").strip() == barrel_id:
                    barrel_copy.update(
                        {
                            "has_muzzle_device": bool(
                                normalized.get("has_muzzle_device")
                            ),
                            "muzzle_device_type": normalized.get("device_type"),
                            "muzzle_device_model": normalized.get(
                                "device_manufacturer"
                            ),
                            "muzzle_device_length_mm": normalized.get("device_length"),
                            "muzzle_device_weight_g": normalized.get("device_weight"),
                            "muzzle_device_diameter_mm": normalized.get(
                                "device_diameter"
                            ),
                            "thread_pitch": normalized.get("thread_pitch"),
                            "poi_tested": normalized.get("poi_tested"),
                            "poi_shift_h": normalized.get("poi_shift_h"),
                            "poi_shift_v": normalized.get("poi_shift_v"),
                        }
                    )
                    matched = True
                updated_barrels.append(barrel_copy)
            if barrel_id and not matched:
                updated_barrels.append(
                    {
                        "id": barrel_id,
                        "has_muzzle_device": bool(normalized.get("has_muzzle_device")),
                        "muzzle_device_type": normalized.get("device_type"),
                        "muzzle_device_model": normalized.get("device_manufacturer"),
                        "muzzle_device_length_mm": normalized.get("device_length"),
                        "muzzle_device_weight_g": normalized.get("device_weight"),
                        "muzzle_device_diameter_mm": normalized.get("device_diameter"),
                        "thread_pitch": normalized.get("thread_pitch"),
                        "poi_tested": normalized.get("poi_tested"),
                        "poi_shift_h": normalized.get("poi_shift_h"),
                        "poi_shift_v": normalized.get("poi_shift_v"),
                    }
                )
            details["barrels"] = updated_barrels
        if barrel_id:
            details["active_barrel_id"] = barrel_id
        configuration_name = (
            str(normalized.get("active_barrel_configuration_name") or "").strip()
            or None
        )
        if configuration_name:
            details["active_barrel_configuration_name"] = configuration_name
        details.update(normalized)
        return self._sync_explicit_barrel_configurations(details)

    def _stage_current_muzzle_details(
        self, details: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        staged = (
            dict(details)
            if isinstance(details, dict)
            else dict(self._loaded_profile_details)
        )
        if self._muzzle_current_barrel_id:
            staged["active_barrel_id"] = self._muzzle_current_barrel_id
        return self._store_active_barrel_muzzle_details(
            staged, self._collect_muzzle_details()
        )

    def on_muzzle_barrel_changed(self) -> None:
        details = self._stage_current_muzzle_details(self._loaded_profile_details)
        selected_barrel_id = self._get_selected_muzzle_barrel_id()
        if selected_barrel_id:
            details["active_barrel_id"] = selected_barrel_id
        else:
            details.pop("active_barrel_id", None)
        self._loaded_profile_details = details
        self._muzzle_current_barrel_id = selected_barrel_id
        self._refresh_muzzle_configuration_selector(self._loaded_profile_details)
        self._refresh_bullet_profile_barrel_selector(self._loaded_profile_details)
        self._refresh_chamber_barrel_selector(self._loaded_profile_details)
        self._populate_bullet_profiles_table(
            self._get_active_barrel_bullet_profiles(self._loaded_profile_details)
        )
        self._populate_chamber_fields(
            self._get_active_barrel_chamber_details(self._loaded_profile_details)
        )
        self._populate_muzzle_fields(
            self._get_active_barrel_muzzle_details(self._loaded_profile_details)
        )

    def on_muzzle_configuration_changed(self) -> None:
        details = self._stage_current_muzzle_details(self._loaded_profile_details)
        selected_configuration_id = self._get_selected_muzzle_configuration_id()
        if selected_configuration_id:
            details["active_barrel_configuration_id"] = selected_configuration_id
        else:
            details.pop("active_barrel_configuration_id", None)
        configuration = self._get_active_muzzle_configuration_entry(
            details,
            configuration_id=selected_configuration_id,
        )
        details["active_barrel_configuration_name"] = (
            str(
                (configuration or {}).get("name")
                or self.muzzle_configuration_combo.currentText()
                or ""
            ).strip()
            or None
        )
        self._loaded_profile_details = details
        self._populate_muzzle_fields(
            self._get_active_barrel_muzzle_details(self._loaded_profile_details)
        )

    def on_muzzle_configuration_name_edited(self) -> None:
        details = self._stage_current_muzzle_details(self._loaded_profile_details)
        self._loaded_profile_details = details
        self._refresh_muzzle_configuration_selector(self._loaded_profile_details)
        self._populate_muzzle_fields(
            self._get_active_barrel_muzzle_details(self._loaded_profile_details)
        )

    def _collect_chamber_details(self) -> dict[str, Any]:
        return {
            "chamber_spec": (
                self.chamber_spec.currentText()
                if hasattr(self, "chamber_spec")
                else None
            ),
            "headspace": self.headspace.value() if hasattr(self, "headspace") else None,
            "fired_base_dia": (
                self.fired_base.value()
                if hasattr(self, "fired_base") and self.fired_base.value() > 0
                else None
            ),
            "fired_shoulder_dia": (
                self.fired_shoulder.value()
                if hasattr(self, "fired_shoulder") and self.fired_shoulder.value() > 0
                else None
            ),
            "fired_length": (
                self.fired_length.value()
                if hasattr(self, "fired_length") and self.fired_length.value() > 0
                else None
            ),
            "sized_base_dia": (
                self.sized_base.value()
                if hasattr(self, "sized_base") and self.sized_base.value() > 0
                else None
            ),
            "sized_shoulder_dia": (
                self.sized_shoulder.value()
                if hasattr(self, "sized_shoulder") and self.sized_shoulder.value() > 0
                else None
            ),
            "shoulder_bump": (
                self.shoulder_bump.value()
                if hasattr(self, "shoulder_bump") and self.shoulder_bump.value() > 0
                else None
            ),
        }

    def _populate_chamber_fields(self, details: dict[str, Any]) -> None:
        if hasattr(self, "chamber_spec"):
            self._set_combo_value(self.chamber_spec, details.get("chamber_spec"))
        if hasattr(self, "headspace"):
            self.headspace.setValue(float(details.get("headspace") or 0))
        if hasattr(self, "fired_base"):
            self.fired_base.setValue(float(details.get("fired_base_dia") or 0))
        if hasattr(self, "fired_shoulder"):
            self.fired_shoulder.setValue(float(details.get("fired_shoulder_dia") or 0))
        if hasattr(self, "fired_length"):
            self.fired_length.setValue(float(details.get("fired_length") or 0))
        if hasattr(self, "sized_base"):
            self.sized_base.setValue(float(details.get("sized_base_dia") or 0))
        if hasattr(self, "sized_shoulder"):
            self.sized_shoulder.setValue(float(details.get("sized_shoulder_dia") or 0))
        if hasattr(self, "shoulder_bump"):
            self.shoulder_bump.setValue(float(details.get("shoulder_bump") or 0))
        if hasattr(self, "calculate_clearances"):
            self.calculate_clearances()

    def _get_active_barrel_chamber_details(
        self, details: dict[str, Any]
    ) -> dict[str, Any]:
        selector = getattr(self, "_get_selected_chamber_barrel_id", None)
        barrel_id = selector() if callable(selector) else None
        if not barrel_id:
            barrel_id, _ = self._resolve_active_barrel_context(details)
        mapping = details.get("chamber_details_by_barrel")
        if barrel_id and isinstance(mapping, dict):
            scoped = mapping.get(barrel_id)
            if isinstance(scoped, dict):
                return dict(scoped)
        return {
            "chamber_spec": details.get("chamber_spec"),
            "headspace": details.get("headspace"),
            "fired_base_dia": details.get("fired_base_dia"),
            "fired_shoulder_dia": details.get("fired_shoulder_dia"),
            "fired_length": details.get("fired_length"),
            "sized_base_dia": details.get("sized_base_dia"),
            "sized_shoulder_dia": details.get("sized_shoulder_dia"),
            "shoulder_bump": details.get("shoulder_bump"),
        }

    def _store_active_barrel_chamber_details(
        self, details: dict[str, Any], chamber_details: dict[str, Any]
    ) -> dict[str, Any]:
        normalized = dict(chamber_details)
        selector = getattr(self, "_get_selected_chamber_barrel_id", None)
        barrel_id = selector() if callable(selector) else None
        if not barrel_id:
            barrel_id, _ = self._resolve_active_barrel_context(details)
        mapping = details.get("chamber_details_by_barrel")
        if not isinstance(mapping, dict):
            mapping = {}
        else:
            mapping = dict(mapping)
        if barrel_id:
            mapping[barrel_id] = normalized
            details["active_barrel_id"] = barrel_id
        details["chamber_details_by_barrel"] = mapping
        details.update(normalized)
        return details

    def _stage_current_chamber_details(
        self, details: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        staged = (
            dict(details)
            if isinstance(details, dict)
            else dict(self._loaded_profile_details)
        )
        if self._chamber_current_barrel_id:
            staged["active_barrel_id"] = self._chamber_current_barrel_id
        return self._store_active_barrel_chamber_details(
            staged, self._collect_chamber_details()
        )

    def on_chamber_barrel_changed(self) -> None:
        details = self._stage_current_chamber_details(self._loaded_profile_details)
        selected_barrel_id = self._get_selected_chamber_barrel_id()
        if selected_barrel_id:
            details["active_barrel_id"] = selected_barrel_id
        else:
            details.pop("active_barrel_id", None)
        self._loaded_profile_details = details
        self._chamber_current_barrel_id = selected_barrel_id
        self._refresh_bullet_profile_barrel_selector(self._loaded_profile_details)
        self._refresh_muzzle_barrel_selector(self._loaded_profile_details)
        self._populate_chamber_fields(
            self._get_active_barrel_chamber_details(self._loaded_profile_details)
        )
        self._populate_muzzle_fields(
            self._get_active_barrel_muzzle_details(self._loaded_profile_details)
        )

    def _populate_bullet_profiles_table(self, profiles: list[dict[str, Any]]) -> None:
        if not hasattr(self, "bullet_profiles_table"):
            return
        self.bullet_profiles_table.setRowCount(0)
        for profile in profiles:
            row = self.bullet_profiles_table.rowCount()
            self.bullet_profiles_table.insertRow(row)
            self.bullet_profiles_table.setItem(
                row, 0, QTableWidgetItem(profile.get("bullet_name", ""))
            )
            self.bullet_profiles_table.setItem(
                row, 1, QTableWidgetItem(str(profile.get("bullet_weight_gr", "")))
            )
            self.bullet_profiles_table.setItem(
                row,
                2,
                QTableWidgetItem(str(profile.get("jam_length_coal_mm", ""))),
            )
            self.bullet_profiles_table.setItem(
                row,
                3,
                QTableWidgetItem(str(profile.get("jam_length_cbto_mm", ""))),
            )
            self.bullet_profiles_table.setItem(
                row, 4, QTableWidgetItem(str(profile.get("optimal_jump_mm", "")))
            )
            self.bullet_profiles_table.setItem(
                row, 5, QTableWidgetItem(str(profile.get("mag_max_coal_mm", "")))
            )
            self.bullet_profiles_table.setItem(
                row,
                6,
                QTableWidgetItem(str(profile.get("measurement_method", "manual"))),
            )
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(
                lambda _, r=row: self.bullet_profiles_table.removeRow(r)
            )
            self.bullet_profiles_table.setCellWidget(row, 7, delete_btn)

    def _stage_current_bullet_profiles(
        self, details: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        staged = (
            dict(details)
            if isinstance(details, dict)
            else dict(self._loaded_profile_details)
        )
        if not hasattr(self, "bullet_profiles_table"):
            return staged
        if self._bullet_profiles_current_barrel_id:
            staged["active_barrel_id"] = self._bullet_profiles_current_barrel_id
        return self._store_active_barrel_bullet_profiles(
            staged, self._collect_bullet_profiles()
        )

    def on_bullet_profile_barrel_changed(self) -> None:
        details = self._stage_current_bullet_profiles(self._loaded_profile_details)
        selected_barrel_id = self._get_selected_bullet_profile_barrel_id()
        if selected_barrel_id:
            details["active_barrel_id"] = selected_barrel_id
        else:
            details.pop("active_barrel_id", None)
        self._loaded_profile_details = details
        self._bullet_profiles_current_barrel_id = selected_barrel_id
        self._refresh_chamber_barrel_selector(self._loaded_profile_details)
        self._refresh_muzzle_barrel_selector(self._loaded_profile_details)
        self._populate_chamber_fields(
            self._get_active_barrel_chamber_details(self._loaded_profile_details)
        )
        self._populate_muzzle_fields(
            self._get_active_barrel_muzzle_details(self._loaded_profile_details)
        )
        self._populate_bullet_profiles_table(
            self._get_active_barrel_bullet_profiles(self._loaded_profile_details)
        )

    def _get_active_barrel_bullet_profiles(
        self, details: dict[str, Any]
    ) -> list[dict[str, Any]]:
        selector = getattr(self, "_get_selected_bullet_profile_barrel_id", None)
        barrel_id = selector() if callable(selector) else None
        if not barrel_id:
            barrel_id, _ = self._resolve_active_barrel_context(details)
        mapping = details.get("bullet_profiles_by_barrel")
        if barrel_id and isinstance(mapping, dict):
            scoped = mapping.get(barrel_id)
            if isinstance(scoped, list):
                return [dict(item) for item in scoped if isinstance(item, dict)]
        profiles = details.get("bullet_profiles", [])
        if isinstance(profiles, list):
            return [dict(item) for item in profiles if isinstance(item, dict)]
        return []

    def _store_active_barrel_bullet_profiles(
        self, details: dict[str, Any], profiles: list[dict[str, Any]]
    ) -> dict[str, Any]:
        normalized_profiles = [
            dict(item) for item in profiles if isinstance(item, dict)
        ]
        barrel_id, _ = self._resolve_active_barrel_context(details)
        mapping = details.get("bullet_profiles_by_barrel")
        if not isinstance(mapping, dict):
            mapping = {}
        else:
            mapping = dict(mapping)
        if barrel_id:
            mapping[barrel_id] = normalized_profiles
        details["bullet_profiles_by_barrel"] = mapping
        details["bullet_profiles"] = normalized_profiles
        return details

    def _find_bullet_id_for_profile(self, profile: dict[str, Any]) -> Optional[int]:
        bullet_name = str(profile.get("bullet_name") or "").strip()
        if not bullet_name:
            return None

        rows = self.db.execute_query(
            "SELECT id, weight_grains FROM bullets WHERE LOWER(name) = LOWER(?) ORDER BY id",
            (bullet_name,),
        )
        if not rows:
            return None

        target_weight = self._parse_optional_float(profile.get("bullet_weight_gr"))
        if target_weight is None:
            return int(rows[0].get("id")) if rows[0].get("id") is not None else None

        best_row = None
        best_delta = None
        for row in rows:
            row_weight = self._parse_optional_float(row.get("weight_grains"))
            if row_weight is None:
                continue
            delta = abs(row_weight - target_weight)
            if best_delta is None or delta < best_delta:
                best_delta = delta
                best_row = row
        if best_row is not None and best_delta is not None and best_delta <= 1.0:
            return int(best_row.get("id")) if best_row.get("id") is not None else None
        return int(rows[0].get("id")) if rows[0].get("id") is not None else None

    def _sync_bullet_profiles_to_jump_measurements(
        self, rifle_id: int, details: dict[str, Any]
    ) -> None:
        if not rifle_id:
            return

        barrel_id, barrel_name = self._resolve_active_barrel_context(details)
        if barrel_id:
            self.db.delete(
                "rifle_bullet_jump_measurements",
                "rifle_id = ? AND measurement_tool = ? AND COALESCE(barrel_id, '') = ?",
                (rifle_id, "rifle_profile_editor", barrel_id),
            )
        else:
            self.db.delete(
                "rifle_bullet_jump_measurements",
                "rifle_id = ? AND measurement_tool = ? AND (barrel_id IS NULL OR barrel_id = '')",
                (rifle_id, "rifle_profile_editor"),
            )

        profiles = self._get_active_barrel_bullet_profiles(details)
        if not isinstance(profiles, list):
            return

        measurement_date = datetime.now().date().isoformat()
        for profile in profiles:
            if not isinstance(profile, dict):
                continue
            jam_cbto_mm = self._parse_optional_float(profile.get("jam_length_cbto_mm"))
            jam_coal_mm = self._parse_optional_float(profile.get("jam_length_coal_mm"))
            if jam_cbto_mm is None or jam_coal_mm is None:
                continue

            bullet_id = self._find_bullet_id_for_profile(profile)
            if bullet_id is None:
                continue

            optimal_jump_mm = self._parse_optional_float(profile.get("optimal_jump_mm"))
            method = (
                str(profile.get("measurement_method") or "manual").strip() or "manual"
            )
            notes = f"Synced from rifle profile editor bullet profile for {str(profile.get('bullet_name') or '').strip()}"
            self.db.insert(
                "rifle_bullet_jump_measurements",
                {
                    "rifle_id": rifle_id,
                    "barrel_id": barrel_id,
                    "barrel_name": barrel_name,
                    "bullet_id": bullet_id,
                    "measurement_date": measurement_date,
                    "jam_coal_mm": jam_coal_mm,
                    "jam_cbto_mm": jam_cbto_mm,
                    "measurement_method": method,
                    "measurement_tool": "rifle_profile_editor",
                    "recommended_jam_minus_010_mm": jam_cbto_mm - 0.254,
                    "recommended_jam_minus_020_mm": jam_cbto_mm - 0.508,
                    "recommended_jam_minus_030_mm": jam_cbto_mm - 0.762,
                    "recommended_jam_minus_040_mm": jam_cbto_mm - 1.016,
                    "notes": (
                        f"{notes}. Saved optimal jump {optimal_jump_mm:.3f} mm."
                        if optimal_jump_mm is not None
                        else notes
                    ),
                },
            )

    def load_rifle_data(self):
        """Load existing rifle data"""
        rifle = self.db.get_by_id("rifles", self.rifle_id)
        if not rifle:
            return

        details_rows = self.db.execute_query(
            "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
            (self.rifle_id,),
        )
        details: dict[str, Any] = {}
        if details_rows:
            raw = details_rows[0].get("profile_json")
            if raw:
                try:
                    details = json.loads(raw)
                except json.JSONDecodeError:
                    details = {}
        self._loaded_profile_details = details if isinstance(details, dict) else {}

        harmonics = details.get("harmonics", {})
        if not isinstance(harmonics, dict):
            harmonics = {}

        mode = details.get("user_mode") or self.user_mode
        self._set_user_mode(mode)

        self.name.setText(rifle.get("name", ""))
        self.manufacturer.setText(rifle.get("manufacturer", ""))
        self._set_combo_value(self.caliber, rifle.get("caliber"))
        self._set_combo_value(self.action_type, rifle.get("action_type"))
        self.serial.setText(rifle.get("serial_number", ""))

        weapon_type = details.get("weapon_type")
        if weapon_type:
            self._set_combo_value(self.weapon_type, weapon_type)
            self.on_weapon_type_changed(weapon_type)

        if rifle.get("barrel_length_mm"):
            self.barrel_length.setValue(float(rifle.get("barrel_length_mm")))
        elif rifle.get("barrel_length_inches"):
            mm_value = float(rifle.get("barrel_length_inches")) * 25.4
            self.barrel_length.setValue(mm_value)

        self._set_combo_value(self.twist_rate, rifle.get("twist_rate"))
        self.notes.setText(rifle.get("notes", ""))

        barrel_profile = details.get("barrel_profile")
        barrel_profile_simple = details.get("barrel_profile_simple")
        if hasattr(self, "barrel_profile") and barrel_profile:
            self._set_combo_value(self.barrel_profile, barrel_profile)
        if hasattr(self, "barrel_profile_simple") and barrel_profile_simple:
            self._set_combo_value(self.barrel_profile_simple, barrel_profile_simple)

        if hasattr(self, "barrel_material"):
            self._set_combo_value(self.barrel_material, details.get("barrel_material"))
        if hasattr(self, "barrel_weight") and details.get("barrel_weight") is not None:
            self.barrel_weight.setValue(float(details.get("barrel_weight")))

        if hasattr(self, "muzzle_diameter") and details.get("muzzle_diameter"):
            self.muzzle_diameter.setValue(float(details.get("muzzle_diameter")))
        if hasattr(self, "breech_diameter") and details.get("breech_diameter"):
            self.breech_diameter.setValue(float(details.get("breech_diameter")))

        if hasattr(self, "free_float"):
            self.free_float.setChecked(bool(details.get("free_float", True)))
        if hasattr(self, "bedding_type"):
            self._set_combo_value(self.bedding_type, details.get("bedding_type"))
        if hasattr(self, "stock_material"):
            self._set_combo_value(self.stock_material, details.get("stock_material"))

        if hasattr(self, "round_count") and details.get("round_count") is not None:
            self.round_count.setValue(int(details.get("round_count")))

        if hasattr(self, "barrel_condition"):
            value = details.get("barrel_condition")
            if not value:
                value = BORE_CONDITION_REVERSE.get(rifle.get("bore_condition"))
            self._set_combo_value(self.barrel_condition, value)

        if hasattr(self, "throat_erosion") and details.get("throat_erosion"):
            self._set_combo_value(self.throat_erosion, details.get("throat_erosion"))

        pistol_fields = details.get("pistol_fields", {})
        if pistol_fields and hasattr(self, "pistol_fields"):
            if "sikte" in pistol_fields:
                self.pistol_fields["sikte"].setText(str(pistol_fields.get("sikte")))
            if "avtrekk" in pistol_fields:
                self.pistol_fields["avtrekk"].setText(str(pistol_fields.get("avtrekk")))
            if "magasin" in pistol_fields:
                self.pistol_fields["magasin"].setValue(
                    int(pistol_fields.get("magasin") or 0)
                )

        if hasattr(self, "bullet_profiles_table"):
            self._refresh_bullet_profile_barrel_selector(self._loaded_profile_details)
            self._populate_bullet_profiles_table(
                self._get_active_barrel_bullet_profiles(self._loaded_profile_details)
            )
        if hasattr(self, "muzzle_barrel_combo"):
            self._refresh_muzzle_barrel_selector(self._loaded_profile_details)
        if hasattr(self, "muzzle_configuration_combo"):
            self._refresh_muzzle_configuration_selector(self._loaded_profile_details)
        if any(
            hasattr(self, name)
            for name in (
                "has_device",
                "device_type",
                "device_manufacturer",
                "device_length",
                "device_weight",
                "device_diameter",
                "thread_pitch",
                "poi_tested",
                "poi_shift_h",
                "poi_shift_v",
                "active_muzzle_configuration_name",
            )
        ):
            self._populate_muzzle_fields(
                self._get_active_barrel_muzzle_details(self._loaded_profile_details)
            )
        if hasattr(self, "chamber_barrel_combo"):
            self._refresh_chamber_barrel_selector(self._loaded_profile_details)
        if any(
            hasattr(self, name)
            for name in (
                "chamber_spec",
                "headspace",
                "fired_base",
                "fired_shoulder",
                "fired_length",
                "sized_base",
                "sized_shoulder",
                "shoulder_bump",
            )
        ):
            self._populate_chamber_fields(
                self._get_active_barrel_chamber_details(self._loaded_profile_details)
            )

        if hasattr(self, "barrel_profile_id"):
            self.barrel_profile_id.setText(str(harmonics.get("barrel_profile_id", "")))
        if hasattr(self, "free_float_length_mm"):
            self.free_float_length_mm.setValue(
                self._parse_optional_float(harmonics.get("free_float_length_mm")) or 0.0
            )
        if hasattr(self, "tuner_mass_g"):
            self.tuner_mass_g.setValue(
                self._parse_optional_float(harmonics.get("tuner_mass_g")) or 0.0
            )
        if hasattr(self, "tuner_position_mm"):
            self.tuner_position_mm.setValue(
                self._parse_optional_float(harmonics.get("tuner_position_mm")) or 0.0
            )
        if hasattr(self, "action_stiffness"):
            self.action_stiffness.setCurrentText(
                str(harmonics.get("action_stiffness", "normal"))
            )
        if hasattr(self, "support_type"):
            self.support_type.setCurrentText(
                str(harmonics.get("support_type", "bipod"))
            )
        if hasattr(self, "harmonic_score"):
            score = harmonics.get("harmonic_score")
            if score is None and isinstance(harmonics.get("summary"), dict):
                score = harmonics["summary"].get("harmonic_score")
            self.harmonic_score.setValue(self._parse_optional_float(score) or 0.0)
        if hasattr(self, "node_bands_text"):
            node_bands = harmonics.get("node_bands", [])
            if not isinstance(node_bands, list):
                node_bands = normalize_node_bands(node_bands)
            self.node_bands_text.setPlainText(
                json.dumps(node_bands, ensure_ascii=False, indent=2)
                if node_bands
                else ""
            )

    def save_profile(self):
        """Save complete rifle profile"""
        if not self.name.text():
            QMessageBox.warning(self, "Missing Name", "The firearm must have a name!")
            return

        # Collect basic data (always available)
        rifle_data = {
            "weapon_type": self.weapon_type.currentText(),
            "name": self.name.text(),
            "manufacturer": self.manufacturer.text(),
            "caliber": self.caliber.currentText(),
            "action_type": self.action_type.currentText(),
            "serial_number": self.serial.text(),
            "barrel_length": self._get_barrel_length_mm(),
            "twist_rate": self.twist_rate.currentText(),
            "notes": self.notes.toPlainText(),
            "user_mode": self.user_mode,
        }

        # Add beginner mode simplified data
        if self.user_mode == "beginner":
            rifle_data["barrel_profile"] = self.barrel_profile_simple.currentText()
        else:
            # Expert mode: all detailed data
            rifle_data.update(
                {
                    "barrel_profile": self.barrel_profile.currentText(),
                    "barrel_material": self.barrel_material.currentText(),
                    "barrel_weight": self.barrel_weight.value(),
                    "muzzle_diameter": self.muzzle_diameter.value(),
                    "breech_diameter": self.breech_diameter.value(),
                    "free_float": self.free_float.isChecked(),
                    "bedding_type": self.bedding_type.currentText(),
                    "stock_material": self.stock_material.currentText(),
                    "round_count": self.round_count.value(),
                    "barrel_condition": self.barrel_condition.currentText(),
                    "throat_erosion": self.throat_erosion.currentText(),
                }
            )

        rifle_data["pistol_fields"] = {
            "sikte": self.pistol_fields["sikte"].text(),
            "avtrekk": self.pistol_fields["avtrekk"].text(),
            "magasin": self.pistol_fields["magasin"].value(),
        }
        self._loaded_profile_details = self._stage_current_muzzle_details(
            self._loaded_profile_details
        )
        self._loaded_profile_details = self._stage_current_chamber_details(
            self._loaded_profile_details
        )
        self._loaded_profile_details = self._stage_current_bullet_profiles(
            self._loaded_profile_details
        )
        active_muzzle_details = self._get_active_barrel_muzzle_details(
            self._loaded_profile_details
        )
        active_chamber_details = self._get_active_barrel_chamber_details(
            self._loaded_profile_details
        )
        rifle_data.update(active_muzzle_details)
        rifle_data.update(active_chamber_details)
        rifle_data["bullet_profiles"] = list(
            self._loaded_profile_details.get("bullet_profiles", [])
        )
        if isinstance(
            self._loaded_profile_details.get("chamber_details_by_barrel"), dict
        ):
            rifle_data["chamber_details_by_barrel"] = dict(
                self._loaded_profile_details.get("chamber_details_by_barrel") or {}
            )
        if isinstance(
            self._loaded_profile_details.get("bullet_profiles_by_barrel"), dict
        ):
            rifle_data["bullet_profiles_by_barrel"] = dict(
                self._loaded_profile_details.get("bullet_profiles_by_barrel") or {}
            )
        if self._loaded_profile_details.get("active_barrel_id") not in (None, ""):
            rifle_data["active_barrel_id"] = self._loaded_profile_details.get(
                "active_barrel_id"
            )

        harmonics = {
            "version": "2.0",
            "rifle_id": self.rifle_id,
            "rifle_name": self.name.text(),
            "barrel_profile_id": self._parse_optional_int(
                self.barrel_profile_id.text()
                if hasattr(self, "barrel_profile_id")
                else None
            ),
            "free_float_length_mm": (
                self.free_float_length_mm.value()
                if hasattr(self, "free_float_length_mm")
                else 0.0
            ),
            "tuner_mass_g": (
                self.tuner_mass_g.value() if hasattr(self, "tuner_mass_g") else 0.0
            ),
            "tuner_position_mm": (
                self.tuner_position_mm.value()
                if hasattr(self, "tuner_position_mm")
                else 0.0
            ),
            "action_stiffness": (
                self.action_stiffness.currentText()
                if hasattr(self, "action_stiffness")
                else "normal"
            ),
            "support_type": (
                self.support_type.currentText()
                if hasattr(self, "support_type")
                else "bipod"
            ),
            "harmonic_score": (
                self.harmonic_score.value() if hasattr(self, "harmonic_score") else 0.0
            ),
            "node_bands": (
                normalize_node_bands(self.node_bands_text.toPlainText())
                if hasattr(self, "node_bands_text")
                else []
            ),
            "calibration_state": (
                "calibrated"
                if (
                    hasattr(self, "node_bands_text")
                    and self.node_bands_text.toPlainText().strip()
                )
                else "heuristic"
            ),
        }
        harmonics["summary"] = calculate_harmonics_profile(
            rifle_data, {**rifle_data, "harmonics": harmonics}
        )
        if not harmonics["node_bands"]:
            harmonics["node_bands"] = harmonics["summary"]["node_bands"]
        rifle_data["harmonics"] = harmonics
        rifle_data["digital_twin"] = {
            "harmonics": harmonics["summary"],
            "rifle_id": self.rifle_id,
            "source": "rifle_profile_editor",
            "updated_at": datetime.now().isoformat(),
        }

        twist_inches = self._parse_twist_inches(rifle_data["twist_rate"])
        barrel_length_mm = float(rifle_data["barrel_length"])
        rifle_payload = {
            "name": rifle_data["name"],
            "manufacturer": rifle_data["manufacturer"],
            "caliber": rifle_data["caliber"],
            "action_type": rifle_data["action_type"],
            "serial_number": rifle_data["serial_number"],
            "barrel_length_mm": barrel_length_mm,
            "barrel_length_inches": barrel_length_mm / 25.4,
            "barrel_contour": rifle_data.get("barrel_profile"),
            "barrel_material": rifle_data.get("barrel_material"),
            "barrel_weight_grams": rifle_data.get("barrel_weight"),
            "twist_rate": rifle_data["twist_rate"],
            "twist_rate_inches": twist_inches,
            "notes": rifle_data.get("notes"),
            "last_updated": datetime.now().isoformat(),
        }

        if self.user_mode == "expert":
            rifle_payload.update(
                {
                    "muzzle_diameter_mm": rifle_data.get("muzzle_diameter"),
                    "breech_diameter_mm": rifle_data.get("breech_diameter"),
                    "thread_pitch": rifle_data.get("thread_pitch"),
                    "chamber_spec": rifle_data.get("chamber_spec"),
                    "round_count": rifle_data.get("round_count"),
                    "bore_condition": BORE_CONDITION_MAP.get(
                        rifle_data.get("barrel_condition", ""),
                        rifle_data.get("barrel_condition"),
                    ),
                }
            )

        if self.rifle_id:
            self.db.update("rifles", rifle_payload, "id = ?", (self.rifle_id,))
        else:
            self.rifle_id = self.db.insert("rifles", rifle_payload)
            if self.rifle_id is None:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    "Could not save firearm profile: database insert failed.",
                )
                return

        if self.rifle_id:
            stored_details = self._load_existing_profile_details(self.rifle_id)
            stored_details = self._store_active_barrel_muzzle_details(
                stored_details,
                active_muzzle_details,
            )
            stored_details = self._store_active_barrel_chamber_details(
                stored_details,
                active_chamber_details,
            )
            stored_details = self._store_active_barrel_bullet_profiles(
                stored_details,
                rifle_data["bullet_profiles"],
            )
            stored_details.update(rifle_data)
            saved_details = self._save_profile_details(self.rifle_id, stored_details)
            self._sync_bullet_profiles_to_jump_measurements(
                self.rifle_id, saved_details
            )

        self.rifle_saved.emit(rifle_data)

        QMessageBox.information(
            self,
            "Profile Saved",
            f"Firearm profile '{self.name.text()}' has been saved.\n\n"
            "This profile will now be available in the Load Development Wizard, "
            "and the AI will use this data to provide better recommendations.",
        )

        self.accept()
