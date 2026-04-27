"""
Innstillinger
Konfigurasjon og preferanser
"""

import importlib
import json
import os
import shutil
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Optional, Protocol, cast

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..database import get_database, get_default_db_path
from ..research.service import ResearchService
from ..research.transport import default_transport


class _WindowSettingsHooks(Protocol):
    def apply_theme_from_settings(self) -> None: ...
    def _sync_mode_combo_from_settings(self) -> None: ...
    def apply_ui_mode_from_settings(self) -> None: ...


def _get_app_settings_manager() -> Any:
    module = importlib.import_module("HjemmeladingApp.settings")
    return getattr(module, "settings")


def _get_app_config_module() -> Any:
    return importlib.import_module("HjemmeladingApp.config")


class SettingsWidget(QWidget):
    """Innstillinger-widget"""

    def __init__(self):
        super().__init__()
        self.settings = QSettings("ReloadingWorkshop", "ReloadingManager")
        self._research_error: Optional[Exception] = None
        self._research_service: Optional[ResearchService] = (
            self._init_research_service()
        )
        self.research_opt_in: Optional[QCheckBox] = None
        self.research_id_value: Optional[QLabel] = None
        self.research_stats_label: Optional[QLabel] = None
        self.research_send_btn: Optional[QPushButton] = None
        self.ui_mode: Optional[QComboBox] = None
        self.ui_theme: Optional[QComboBox] = None
        self.ui_button_style: Optional[QComboBox] = None
        self.ui_density: Optional[QComboBox] = None
        self.accent_color_btn: Optional[QPushButton] = None
        self.accent_color_preview: Optional[QFrame] = None
        self.accent_rgb: dict[str, int] = {"r": 60, "g": 120, "b": 200}
        self.init_ui()
        self.load_settings()

    def _init_research_service(self) -> Optional[ResearchService]:
        try:
            db = get_database()
        except Exception as exc:
            self._research_error = exc
            return None
        try:
            return ResearchService(db)
        except Exception as exc:
            self._research_error = exc
            return None

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        scroll.setWidget(container)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(scroll)

        # Tittel
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Enheter
        units_group = self.create_units_section()
        layout.addWidget(units_group)

        # Opplevelse og UI
        ui_group = self.create_ui_section()
        layout.addWidget(ui_group)

        # Standardverdier
        defaults_group = self.create_defaults_section()
        layout.addWidget(defaults_group)

        # Sikkerhet
        safety_group = self.create_safety_section()
        layout.addWidget(safety_group)

        # Database
        database_group = self.create_database_section()
        layout.addWidget(database_group)

        # Research / telemetry
        research_group = self.create_research_section()
        layout.addWidget(research_group)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset_settings)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def create_units_section(self):
        """Oppretter enheter-seksjon"""
        group = QGroupBox("Units")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        form = QFormLayout()
        group.setLayout(form)

        # Språk
        self.language = QComboBox()
        self.language.addItems(["English", "Norsk"])
        self.language.currentIndexChanged.connect(self.on_language_changed)
        form.addRow("Language:", self.language)

        # Optikk klikk-enhet
        self.click_unit = QComboBox()
        self.click_unit.addItems(["MOA", "MRAD"])
        form.addRow("Default scope click unit:", self.click_unit)

        # Avstand
        self.distance_unit = QComboBox()
        self.distance_unit.addItems(["Meters", "Yards"])
        form.addRow("Distance unit:", self.distance_unit)

        # Temperatur
        self.temp_unit = QComboBox()
        self.temp_unit.addItems(["Celsius", "Fahrenheit"])
        form.addRow("Temperature unit:", self.temp_unit)

        # Måleenhet for alle relevante felt (mm/tommer)
        self.measurement_unit = QComboBox()
        self.measurement_unit.addItems(["Millimeter (mm)", "Inches"])
        form.addRow("Measurement unit (mm/inches):", self.measurement_unit)

        detail_units_hint = QLabel(
            "You can also choose units separately per category. This lets you, for example, use twist in inches, "
            "case dimensions in mm, bullet weight in grains, and powder weight in grams."
        )
        detail_units_hint.setWordWrap(True)
        detail_units_hint.setStyleSheet("color: #6c757d; font-size: 11px;")
        form.addRow("", detail_units_hint)

        self.bullet_weight_unit = QComboBox()
        self.bullet_weight_unit.addItems(["Grain (gr)", "Gram (g)"])
        form.addRow("Bullet weight:", self.bullet_weight_unit)

        self.powder_weight_unit = QComboBox()
        self.powder_weight_unit.addItems(["Grain (gr)", "Gram (g)"])
        form.addRow("Powder weight:", self.powder_weight_unit)

        self.velocity_unit = QComboBox()
        self.velocity_unit.addItems(["fps", "m/s"])
        form.addRow("Velocity:", self.velocity_unit)

        self.pressure_unit = QComboBox()
        self.pressure_unit.addItems(["PSI", "bar", "MPa"])
        form.addRow("Pressure:", self.pressure_unit)

        self.group_size_unit = QComboBox()
        self.group_size_unit.addItems(["Millimeter (mm)", "MOA", "MIL", "Inches"])
        form.addRow("Group size:", self.group_size_unit)

        self.twist_unit = QComboBox()
        self.twist_unit.addItems(['Turns per inch (1:11")', "Turns per mm (1:279 mm)"])
        form.addRow("Twist display:", self.twist_unit)

        # Ballistisk dragmodell
        self.drag_model = QComboBox()
        self.drag_model.addItem("Auto (prefer G7)", "AUTO")
        self.drag_model.addItem("G1", "G1")
        self.drag_model.addItem("G7", "G7")
        form.addRow("Preferred drag model:", self.drag_model)

        drag_hint = QLabel(
            "Used as the default in ballistic views. Auto selects G7 when available, otherwise G1."
        )
        drag_hint.setWordWrap(True)
        drag_hint.setStyleSheet("color: #6c757d; font-size: 11px;")
        form.addRow("", drag_hint)

        # Info: Visning kan velges fritt, mens intern referanse fortsatt kan komme fra tomme-baserte twist-data
        twist_info = QLabel(
            'Twist can be shown in the preferred format. Internally, some reference data may still use a 1:11" basis.'
        )
        twist_info.setStyleSheet("color: #ffc107; font-size: 12px;")
        form.addRow("", twist_info)

        return group

    def create_ui_section(self):
        """Oppretter opplevelse- og UI-seksjon"""
        group = QGroupBox("Experience & UI")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        form = QFormLayout()
        group.setLayout(form)

        self.ui_mode = QComboBox()
        self.ui_mode.addItem("Beginner", "beginner")
        self.ui_mode.addItem("Expert", "expert")
        self.ui_mode.addItem("Research", "research")
        form.addRow("User mode:", self.ui_mode)

        self.ui_theme = QComboBox()
        self.ui_theme.addItem("Dark", "dark")
        self.ui_theme.addItem("Light", "light")
        self.ui_theme.addItem("High contrast", "high-contrast")
        form.addRow("Theme:", self.ui_theme)

        self.ui_button_style = QComboBox()
        self.ui_button_style.addItem("Filled", "filled")
        self.ui_button_style.addItem("Outlined", "outlined")
        form.addRow("Button style:", self.ui_button_style)

        self.ui_density = QComboBox()
        self.ui_density.addItem("Comfortable", "comfortable")
        self.ui_density.addItem("Compact", "compact")
        form.addRow("Density:", self.ui_density)

        self.accent_color_preview = QFrame()
        self.accent_color_preview.setFixedSize(36, 18)
        self.accent_color_preview.setFrameShape(QFrame.Shape.Box)
        self.accent_color_preview.setLineWidth(1)

        self.accent_color_btn = QPushButton("Choose color")
        self.accent_color_btn.clicked.connect(self._choose_accent_color)

        accent_row = QHBoxLayout()
        accent_row.addWidget(self.accent_color_preview)
        accent_row.addWidget(self.accent_color_btn)
        accent_row.addStretch()

        accent_widget = QWidget()
        accent_widget.setLayout(accent_row)
        form.addRow("Accent color:", accent_widget)

        hint = QLabel(
            "Display preferences for the interface. Theme and mode are used in Workflow Hub and the main menus."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6c757d; font-size: 11px;")
        form.addRow("", hint)

        return group

    def create_defaults_section(self):
        """Oppretter standardverdier-seksjon"""
        group = QGroupBox("Defaults")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        form = QFormLayout()
        group.setLayout(form)

        # Standard zero distance
        self.default_zero = QSpinBox()
        self.default_zero.setRange(25, 500)
        self.default_zero.setValue(100)
        self.default_zero.setSuffix(" m")
        form.addRow("Default zero distance:", self.default_zero)

        # Standard test distance
        self.default_test_distance = QSpinBox()
        self.default_test_distance.setRange(25, 1000)
        self.default_test_distance.setValue(100)
        self.default_test_distance.setSuffix(" m")
        form.addRow("Default test distance:", self.default_test_distance)

        # Standard ladder step
        self.default_ladder_step = QDoubleSpinBox()
        self.default_ladder_step.setRange(0.1, 2.0)
        self.default_ladder_step.setValue(0.3)
        self.default_ladder_step.setDecimals(1)
        self.default_ladder_step.setSuffix(" gr")
        form.addRow("Default ladder test step:", self.default_ladder_step)

        return group

    def create_safety_section(self):
        """Oppretter sikkerhets-seksjon"""
        group = QGroupBox("Safety Settings")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Advarsler
        self.warn_high_charge = QCheckBox("Warn on high powder charge (> book max)")
        self.warn_high_charge.setChecked(True)
        layout.addWidget(self.warn_high_charge)

        self.warn_pressure = QCheckBox("Warn on potential pressure signs")
        self.warn_pressure.setChecked(True)
        layout.addWidget(self.warn_pressure)

        self.warn_old_cases = QCheckBox(
            "Warn when brass has been used more than 5 times"
        )
        self.warn_old_cases.setChecked(True)
        layout.addWidget(self.warn_old_cases)

        self.confirm_delete = QCheckBox("Confirm data deletion")
        self.confirm_delete.setChecked(True)
        layout.addWidget(self.confirm_delete)

        # Lageradvarsler
        form = QFormLayout()

        self.low_powder_threshold = QSpinBox()
        self.low_powder_threshold.setRange(0, 5000)
        self.low_powder_threshold.setValue(500)
        self.low_powder_threshold.setSuffix(" g")
        form.addRow("Low powder inventory warning:", self.low_powder_threshold)

        self.low_bullet_threshold = QSpinBox()
        self.low_bullet_threshold.setRange(0, 1000)
        self.low_bullet_threshold.setValue(100)
        self.low_bullet_threshold.setSuffix(" pcs")
        form.addRow("Low bullet inventory warning:", self.low_bullet_threshold)

        self.low_primer_threshold = QSpinBox()
        self.low_primer_threshold.setRange(0, 1000)
        self.low_primer_threshold.setValue(100)
        self.low_primer_threshold.setSuffix(" pcs")
        form.addRow("Low primer inventory warning:", self.low_primer_threshold)

        layout.addLayout(form)

        return group

    def create_database_section(self):
        """Oppretter database-seksjon"""
        group = QGroupBox("Database & Backup")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Database info
        db_path = self._resolve_db_path()
        info = QLabel(f"Database location: <b>{db_path}</b>")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Backup-knapper
        btn_layout = QHBoxLayout()

        backup_btn = QPushButton("Create Backup")
        backup_btn.clicked.connect(self.create_backup)
        btn_layout.addWidget(backup_btn)

        restore_btn = QPushButton("Restore Backup")
        restore_btn.clicked.connect(self.restore_backup)
        btn_layout.addWidget(restore_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Auto-backup
        self.auto_backup = QCheckBox("Automatic backup on program start")
        layout.addWidget(self.auto_backup)

        return group

    def _resolve_db_path(self) -> str:
        try:
            return str(get_default_db_path())
        except Exception:
            return os.path.abspath("data/reloading.db")

    def create_research_section(self):
        """Oppretter forsknings-/telemetri-seksjonen"""
        group = QGroupBox("Research & Telemetry")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        desc = QLabel(
            "Help the project by sharing anonymized test results so we "
            "can improve ballistic recommendations and quality assurance."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        if not self._research_service:
            unavailable = QLabel(
                "ResearchService is not available in this installation."
            )
            unavailable.setWordWrap(True)
            if self._research_error:
                unavailable.setText(
                    f"ResearchService unavailable: {self._research_error}"
                )
            layout.addWidget(unavailable)
            return group

        self.research_opt_in = QCheckBox(
            "Share anonymized test sessions for research and quality assurance"
        )
        self.research_opt_in.toggled.connect(self._on_research_opt_in_changed)
        layout.addWidget(self.research_opt_in)

        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Research ID:"))
        self.research_id_value = QLabel("–")
        try:
            self.research_id_value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
        except Exception:
            pass
        id_layout.addWidget(self.research_id_value, 1)
        layout.addLayout(id_layout)

        self.research_stats_label = QLabel("No statistics available yet")
        self.research_stats_label.setWordWrap(True)
        layout.addWidget(self.research_stats_label)

        btn_row = QHBoxLayout()
        self.research_send_btn = QPushButton("Send pending now")
        self.research_send_btn.clicked.connect(self._send_pending_research)
        btn_row.addWidget(self.research_send_btn)

        retry_btn = QPushButton("Retry failed as pending")
        retry_btn.clicked.connect(self._retry_failed_research)
        btn_row.addWidget(retry_btn)

        refresh_btn = QPushButton("Refresh status")
        refresh_btn.clicked.connect(self._update_research_summary)
        btn_row.addWidget(refresh_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        hint = QLabel(
            "Data is only sent when you enable sharing. Without an endpoint, "
            "payloads are written to research_payloads.jsonl under the tool/log folder."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(hint)

        return group

    def load_settings(self):
        """Laster innstillinger"""
        # Språk
        from ..utils.i18n import normalize_language_code

        language = normalize_language_code(self.settings.value("language", "en"))
        self.language.setCurrentText("Norsk" if language == "no" else "English")

        try:
            app_settings = _get_app_settings_manager()
            cfg = app_settings.get()
        except Exception:
            cfg = {}

        def _select_by_data(combo: Optional[QComboBox], value: str) -> None:
            if combo is None:
                return
            for idx in range(combo.count()):
                if combo.itemData(idx) == value:
                    combo.setCurrentIndex(idx)
                    return

        # Enheter
        click_unit = self.settings.value("units/click_unit", "MOA")
        self.click_unit.setCurrentText(click_unit)

        distance_unit = self.settings.value("units/distance", "Meter")
        self.distance_unit.setCurrentText(distance_unit)

        temp_unit = self.settings.value("units/temperature", "Celsius")
        self.temp_unit.setCurrentText(temp_unit)

        measurement_unit = self.settings.value("units/measurement", "Millimeter (mm)")
        self.measurement_unit.setCurrentText(measurement_unit)
        self.bullet_weight_unit.setCurrentText(
            str(
                self.settings.value("units/bullet_weight", "Grain (gr)") or "Grain (gr)"
            )
        )
        self.powder_weight_unit.setCurrentText(
            str(
                self.settings.value("units/powder_weight", "Grain (gr)") or "Grain (gr)"
            )
        )
        self.velocity_unit.setCurrentText(
            str(self.settings.value("units/velocity", "fps") or "fps")
        )
        self.pressure_unit.setCurrentText(
            str(self.settings.value("units/pressure", "PSI") or "PSI")
        )
        self.group_size_unit.setCurrentText(
            str(
                self.settings.value("units/group_size", "Millimeter (mm)")
                or "Millimeter (mm)"
            )
        )
        self.twist_unit.setCurrentText(
            str(
                self.settings.value("units/twist", 'Turns per inch (1:11")')
                or 'Turns per inch (1:11")'
            )
        )
        preferred_drag_model = str(
            self.settings.value("ballistics/drag_model", "AUTO") or "AUTO"
        )
        for idx in range(self.drag_model.count()):
            if self.drag_model.itemData(idx) == preferred_drag_model:
                self.drag_model.setCurrentIndex(idx)
                break

        # UI / opplevelse
        ui_mode = self.settings.value("ui/mode", cfg.get("ui_mode", "beginner"))
        ui_theme = self.settings.value("theme", cfg.get("theme", "dark"))
        btn_style = self.settings.value(
            "button_style", cfg.get("button_style", "filled")
        )
        ui_density = self.settings.value(
            "ui/density", cfg.get("ui_density", "comfortable")
        )
        _select_by_data(self.ui_mode, str(ui_mode))
        _select_by_data(self.ui_theme, str(ui_theme))
        _select_by_data(self.ui_button_style, str(btn_style))
        _select_by_data(self.ui_density, str(ui_density))

        self.accent_rgb = self._load_accent_rgb(cfg)
        self._update_accent_preview()
        # Standardverdier
        default_zero = self.settings.value("defaults/zero_distance", 100, type=int)
        self.default_zero.setValue(default_zero)

        default_test = self.settings.value("defaults/test_distance", 100, type=int)
        self.default_test_distance.setValue(default_test)

        default_step = self.settings.value("defaults/ladder_step", 0.3, type=float)
        self.default_ladder_step.setValue(default_step)

        # Sikkerhet
        self.warn_high_charge.setChecked(
            self.settings.value("safety/warn_high_charge", True, type=bool)
        )
        self.warn_pressure.setChecked(
            self.settings.value("safety/warn_pressure", True, type=bool)
        )
        self.warn_old_cases.setChecked(
            self.settings.value("safety/warn_old_cases", True, type=bool)
        )
        self.confirm_delete.setChecked(
            self.settings.value("safety/confirm_delete", True, type=bool)
        )

        # Lageradvarsler
        self.low_powder_threshold.setValue(
            self.settings.value("inventory/low_powder", 500, type=int)
        )
        self.low_bullet_threshold.setValue(
            self.settings.value("inventory/low_bullet", 100, type=int)
        )
        self.low_primer_threshold.setValue(
            self.settings.value("inventory/low_primer", 100, type=int)
        )

        # Auto-backup
        self.auto_backup.setChecked(
            self.settings.value("database/auto_backup", False, type=bool)
        )

        self._load_research_settings()

    def save_settings(self):
        """Lagrer innstillinger"""
        # Språk
        language_code = "no" if self.language.currentText() == "Norsk" else "en"
        self.settings.setValue("language", language_code)

        # UI / opplevelse
        ui_mode = self.ui_mode.currentData() if self.ui_mode is not None else "beginner"
        ui_theme = self.ui_theme.currentData() if self.ui_theme is not None else "dark"
        ui_button_style = (
            self.ui_button_style.currentData()
            if self.ui_button_style is not None
            else "filled"
        )
        ui_density = (
            self.ui_density.currentData()
            if self.ui_density is not None
            else "comfortable"
        )
        self.settings.setValue("ui/mode", ui_mode)
        self.settings.setValue("theme", ui_theme)
        self.settings.setValue("button_style", ui_button_style)
        self.settings.setValue("ui/density", ui_density)

        # Enheter
        self.settings.setValue("units/click_unit", self.click_unit.currentText())
        self.settings.setValue("units/distance", self.distance_unit.currentText())
        self.settings.setValue("units/temperature", self.temp_unit.currentText())
        self.settings.setValue("units/measurement", self.measurement_unit.currentText())
        self.settings.setValue(
            "units/bullet_weight", self.bullet_weight_unit.currentText()
        )
        self.settings.setValue(
            "units/powder_weight", self.powder_weight_unit.currentText()
        )
        self.settings.setValue("units/velocity", self.velocity_unit.currentText())
        self.settings.setValue("units/pressure", self.pressure_unit.currentText())
        self.settings.setValue("units/group_size", self.group_size_unit.currentText())
        self.settings.setValue("units/twist", self.twist_unit.currentText())
        self.settings.setValue(
            "ballistics/drag_model",
            self.drag_model.currentData() if self.drag_model is not None else "AUTO",
        )

        if isinstance(self.accent_rgb, dict):
            self.settings.setValue("rgb", self.accent_rgb)

        # Standardverdier
        self.settings.setValue("defaults/zero_distance", self.default_zero.value())
        self.settings.setValue(
            "defaults/test_distance", self.default_test_distance.value()
        )
        self.settings.setValue("defaults/ladder_step", self.default_ladder_step.value())

        # Sikkerhet
        self.settings.setValue(
            "safety/warn_high_charge", self.warn_high_charge.isChecked()
        )
        self.settings.setValue("safety/warn_pressure", self.warn_pressure.isChecked())
        self.settings.setValue("safety/warn_old_cases", self.warn_old_cases.isChecked())
        self.settings.setValue("safety/confirm_delete", self.confirm_delete.isChecked())

        # Lageradvarsler
        self.settings.setValue(
            "inventory/low_powder", self.low_powder_threshold.value()
        )
        self.settings.setValue(
            "inventory/low_bullet", self.low_bullet_threshold.value()
        )
        self.settings.setValue(
            "inventory/low_primer", self.low_primer_threshold.value()
        )

        # Auto-backup
        self.settings.setValue("database/auto_backup", self.auto_backup.isChecked())

        self._save_research_settings()

        try:
            app_settings = _get_app_settings_manager()
            app_settings.set_theme(str(ui_theme), rgb=self.accent_rgb)
            app_settings.set_button_style(str(ui_button_style))
            app_settings.set_ui_mode(str(ui_mode))
            app_settings.set_ui_density(str(ui_density))
            app_settings.save()
        except Exception:
            pass

        self._apply_theme_changes()

        QMessageBox.information(self, "Success", "Settings saved!")

    def reset_settings(self):
        """Reset settings to default."""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset all settings to default?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.settings.clear()
            try:
                app_config = _get_app_config_module()
                app_settings = _get_app_settings_manager()
                app_settings.import_config(app_config.get_default_config())
            except Exception:
                pass
            self.load_settings()
            self._apply_theme_changes()
            QMessageBox.information(self, "Success", "Settings reset!")

    def create_backup(self):
        """Create a database backup."""
        db_path = self._resolve_db_path()
        if not os.path.exists(db_path):
            QMessageBox.warning(self, "Error", "Database file not found!")
            return

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"reloading_backup_{timestamp}.db"

        # Choose save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup",
            default_name,
            "Database files (*.db);;All files (*.*)",
        )

        if file_path:
            try:
                shutil.copy2(db_path, file_path)
                QMessageBox.information(
                    self, "Success", f"Backup created:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create backup:\n{str(e)}"
                )

    def restore_backup(self):
        """Restore database from backup."""
        reply = QMessageBox.warning(
            self,
            "WARNING",
            "Restoring a backup will OVERWRITE the current database!\n\n"
            "All changes since the backup will be lost.\n\n"
            "Are you SURE you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            "",
            "Database files (*.db);;All files (*.*)",
        )

        if not file_path:
            return

        db_path = self._resolve_db_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_dir = os.path.dirname(db_path) or os.getcwd()
        safety_backup = os.path.join(db_dir, f"reloading_before_restore_{timestamp}.db")

        try:
            if os.path.exists(db_path):
                shutil.copy2(db_path, safety_backup)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Backup",
                f"Could not create a safety backup of the current database: {exc}",
            )
            safety_backup = None

        try:
            shutil.copy2(file_path, db_path)
            msg = "Database restored from backup!"
            if safety_backup:
                msg += (
                    f"\n\nPrevious database was saved as:\n{safety_backup}\n"
                    "Restart the program to load the file."
                )
            QMessageBox.information(self, "Success", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not restore backup:\n{str(e)}")

    def _load_research_settings(self):
        if not (
            self._research_service and self.research_opt_in and self.research_id_value
        ):
            return
        try:
            opted_in = self._research_service.is_opted_in()
            self.research_opt_in.setChecked(opted_in)
            rid = self._research_service.get_research_id()
            if rid:
                self.research_id_value.setText(rid)
            else:
                self.research_id_value.setText("Generated on activation")
        except Exception as exc:
            if self.research_stats_label:
                self.research_stats_label.setText(
                    f"Could not load telemetry settings: {exc}"
                )
        self._update_research_summary()

    def _coerce_dict(self, value: object) -> Optional[dict[str, object]]:
        if isinstance(value, dict):
            return {str(k): v for k, v in value.items()}
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except Exception:
                return None
            if isinstance(parsed, dict):
                return {str(k): v for k, v in parsed.items()}
        return None

    def _load_accent_rgb(self, cfg: Mapping[str, object]) -> dict[str, int]:
        rgb = self._coerce_dict(self.settings.value("rgb", None))
        if not rgb:
            cfg_rgb = cfg.get("rgb")
            if isinstance(cfg_rgb, dict):
                rgb = {str(k): v for k, v in cfg_rgb.items()}
        if not rgb:
            rgb = {"r": 60, "g": 120, "b": 200}

        def _as_int(value: object, fallback: int) -> int:
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    return fallback
            return fallback

        return {
            "r": max(0, min(255, _as_int(rgb.get("r"), 60))),
            "g": max(0, min(255, _as_int(rgb.get("g"), 120))),
            "b": max(0, min(255, _as_int(rgb.get("b"), 200))),
        }

    def _choose_accent_color(self) -> None:
        rgb = self.accent_rgb or {"r": 60, "g": 120, "b": 200}
        sanitized_rgb = self._load_accent_rgb(rgb)
        red = int(sanitized_rgb.get("r", 60))
        green = int(sanitized_rgb.get("g", 120))
        blue = int(sanitized_rgb.get("b", 200))
        current = QColor(red, green, blue)
        color = QColorDialog.getColor(current, self, "Velg aksentfarge")
        if color.isValid():
            self.accent_rgb = {
                "r": color.red(),
                "g": color.green(),
                "b": color.blue(),
            }
            self._update_accent_preview()

    def _update_accent_preview(self) -> None:
        if not self.accent_color_preview:
            return
        rgb = self.accent_rgb or {"r": 60, "g": 120, "b": 200}
        self.accent_color_preview.setStyleSheet(
            f"background-color: rgb({rgb['r']}, {rgb['g']}, {rgb['b']}); border: 1px solid #444;"
        )

    def _apply_theme_changes(self) -> None:
        try:
            raw_window = self.window()
        except Exception:
            return
        if raw_window is None:
            return

        window = cast(_WindowSettingsHooks, raw_window)

        for hook_name in (
            "apply_theme_from_settings",
            "_sync_mode_combo_from_settings",
            "apply_ui_mode_from_settings",
        ):
            try:
                hook = getattr(window, hook_name, None)
                if callable(hook):
                    hook()
            except Exception:
                pass

    def _save_research_settings(self):
        if not (self._research_service and self.research_opt_in):
            return

        try:
            enabled = self.research_opt_in.isChecked()
            self._research_service.set_opt_in(enabled)
            if enabled and self.research_id_value:
                rid = self._research_service.ensure_research_id()
                self.research_id_value.setText(rid)
            elif not enabled and self.research_id_value:
                rid = self._research_service.get_research_id()
                if rid:
                    self.research_id_value.setText(f"{rid} (disabled)")
                else:
                    self.research_id_value.setText("Disabled")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Research Settings",
                f"Could not save research preferences: {exc}",
            )

    def _on_research_opt_in_changed(self, checked: bool):
        if not self._research_service:
            return
        if checked:
            try:
                rid = self._research_service.ensure_research_id()
                if self.research_id_value:
                    self.research_id_value.setText(rid)
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "Research Settings",
                    f"Could not enable sharing: {exc}",
                )
                if self.research_opt_in is not None:
                    self.research_opt_in.setChecked(False)
                return
        else:
            if self.research_id_value:
                rid_text = self._research_service.get_research_id() or "Disabled"
                self.research_id_value.setText(rid_text)
        self._update_research_summary()

    def _update_research_summary(self):
        if not (self._research_service and self.research_stats_label):
            return
        summary = {}
        try:
            summary = self._research_service.get_outbox_summary()
            pending = summary.get("pending", 0)
            sent = summary.get("sent", 0)
            failed = summary.get("failed", 0)
            total = summary.get("total", pending + sent + failed)
            self.research_stats_label.setText(
                f"Outbox — pending: {pending} · sent: {sent} · failed: {failed} · total: {total}"
            )
        except Exception as exc:
            self.research_stats_label.setText(f"Could not fetch outbox status: {exc}")

        if self.research_send_btn:
            self.research_send_btn.setEnabled(bool(summary.get("pending", 0)))

    def _send_pending_research(self):
        if not self._research_service:
            return
        try:
            self._research_service.send_pending(default_transport)
            QMessageBox.information(
                self,
                "Research Sharing",
                "All pending payloads were sent (or written to log).",
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Research Sharing",
                f"Could not send payloads: {exc}",
            )
        finally:
            self._update_research_summary()

    def _retry_failed_research(self):
        if not self._research_service:
            return
        try:
            self._research_service.retry_failed()
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Research Sharing",
                f"Could not prepare failed payloads: {exc}",
            )
        self._update_research_summary()

    def on_language_changed(self, index):
        """Handle language changes."""
        from ..utils.i18n import set_language

        language_map = {"Norsk": "no", "English": "en"}

        selected = self.language.currentText()
        lang_code = language_map.get(selected, "en")
        set_language(lang_code)

        # Inform the user
        if lang_code == "no":
            msg = "Language changed to Norwegian.\n\nYou must restart the program to see all changes."
        else:
            msg = "Language changed to English.\n\nYou must restart the program to see all changes."

        QMessageBox.information(self, "Language", msg)
