"""
Innstillinger
Konfigurasjon og preferanser
"""

import os
import shutil
from datetime import datetime

from PyQt6.QtCore import QSettings, Qt
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
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SettingsWidget(QWidget):
    """Innstillinger-widget"""

    def __init__(self):
        super().__init__()
        self.settings = QSettings("ReloadingWorkshop", "ReloadingManager")
        self.init_ui()
        self.load_settings()

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
        title = QLabel("⚙️ Innstillinger")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Enheter
        units_group = self.create_units_section()
        layout.addWidget(units_group)

        # Standardverdier
        defaults_group = self.create_defaults_section()
        layout.addWidget(defaults_group)

        # Sikkerhet
        safety_group = self.create_safety_section()
        layout.addWidget(safety_group)

        # Database
        database_group = self.create_database_section()
        layout.addWidget(database_group)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre innstillinger")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)

        reset_btn = QPushButton("🔄 Tilbakestill til standard")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset_settings)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def create_units_section(self):
        """Oppretter enheter-seksjon"""
        group = QGroupBox("📏 Enheter")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        form = QFormLayout()
        group.setLayout(form)

        # Språk
        self.language = QComboBox()
        self.language.addItems(["Norsk", "English"])
        self.language.currentIndexChanged.connect(self.on_language_changed)
        form.addRow("🌐 Språk / Language:", self.language)

        # Optikk klikk-enhet
        self.click_unit = QComboBox()
        self.click_unit.addItems(["MOA", "MRAD"])
        form.addRow("Standard optikk klikk-enhet:", self.click_unit)

        # Avstand
        self.distance_unit = QComboBox()
        self.distance_unit.addItems(["Meter", "Yards"])
        form.addRow("Avstandsenhet:", self.distance_unit)

        # Temperatur
        self.temp_unit = QComboBox()
        self.temp_unit.addItems(["Celsius", "Fahrenheit"])
        form.addRow("Temperaturenhet:", self.temp_unit)

        # Måleenhet for alle relevante felt (mm/tommer)
        self.measurement_unit = QComboBox()
        self.measurement_unit.addItems(["Millimeter (mm)", "Tommer (inches)"])
        form.addRow("Måleenhet (mm/tommer):", self.measurement_unit)

        # Info: Løps-twist skal alltid være i tommer
        twist_info = QLabel("Løps-twist skal alltid legges inn i tommer (inches)")
        twist_info.setStyleSheet("color: #ffc107; font-size: 12px;")
        form.addRow("", twist_info)

        return group

    def create_defaults_section(self):
        """Oppretter standardverdier-seksjon"""
        group = QGroupBox("🎯 Standardverdier")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        form = QFormLayout()
        group.setLayout(form)

        # Standard zero distance
        self.default_zero = QSpinBox()
        self.default_zero.setRange(25, 500)
        self.default_zero.setValue(100)
        self.default_zero.setSuffix(" m")
        form.addRow("Standard zero-avstand:", self.default_zero)

        # Standard test distance
        self.default_test_distance = QSpinBox()
        self.default_test_distance.setRange(25, 1000)
        self.default_test_distance.setValue(100)
        self.default_test_distance.setSuffix(" m")
        form.addRow("Standard test-avstand:", self.default_test_distance)

        # Standard ladder step
        self.default_ladder_step = QDoubleSpinBox()
        self.default_ladder_step.setRange(0.1, 2.0)
        self.default_ladder_step.setValue(0.3)
        self.default_ladder_step.setDecimals(1)
        self.default_ladder_step.setSuffix(" gr")
        form.addRow("Standard ladder test steg:", self.default_ladder_step)

        return group

    def create_safety_section(self):
        """Oppretter sikkerhets-seksjon"""
        group = QGroupBox("⚠️ Sikkerhetsinnstillinger")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Advarsler
        self.warn_high_charge = QCheckBox("Advarsel ved høy kruttvekt (> max book)")
        self.warn_high_charge.setChecked(True)
        layout.addWidget(self.warn_high_charge)

        self.warn_pressure = QCheckBox("Advarsel ved potensielle trykkegn")
        self.warn_pressure.setChecked(True)
        layout.addWidget(self.warn_pressure)

        self.warn_old_cases = QCheckBox("Advarsel for hylser brukt > 5 ganger")
        self.warn_old_cases.setChecked(True)
        layout.addWidget(self.warn_old_cases)

        self.confirm_delete = QCheckBox("Bekreft sletting av data")
        self.confirm_delete.setChecked(True)
        layout.addWidget(self.confirm_delete)

        # Lageradvarsler
        form = QFormLayout()

        self.low_powder_threshold = QSpinBox()
        self.low_powder_threshold.setRange(0, 5000)
        self.low_powder_threshold.setValue(500)
        self.low_powder_threshold.setSuffix(" g")
        form.addRow("Lavt krutt-lager varsling:", self.low_powder_threshold)

        self.low_bullet_threshold = QSpinBox()
        self.low_bullet_threshold.setRange(0, 1000)
        self.low_bullet_threshold.setValue(100)
        self.low_bullet_threshold.setSuffix(" stk")
        form.addRow("Lavt kule-lager varsling:", self.low_bullet_threshold)

        self.low_primer_threshold = QSpinBox()
        self.low_primer_threshold.setRange(0, 1000)
        self.low_primer_threshold.setValue(100)
        self.low_primer_threshold.setSuffix(" stk")
        form.addRow("Lavt tennhette-lager varsling:", self.low_primer_threshold)

        layout.addLayout(form)

        return group

    def create_database_section(self):
        """Oppretter database-seksjon"""
        group = QGroupBox("💾 Database og Backup")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Database info
        db_path = os.path.abspath("data/reloading.db")
        info = QLabel(f"Database-plassering: <b>{db_path}</b>")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Backup-knapper
        btn_layout = QHBoxLayout()

        backup_btn = QPushButton("📦 Lag backup")
        backup_btn.clicked.connect(self.create_backup)
        btn_layout.addWidget(backup_btn)

        restore_btn = QPushButton("♻️ Gjenopprett backup")
        restore_btn.clicked.connect(self.restore_backup)
        btn_layout.addWidget(restore_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Auto-backup
        self.auto_backup = QCheckBox("Automatisk backup ved programstart")
        layout.addWidget(self.auto_backup)

        return group

    def load_settings(self):
        """Laster innstillinger"""
        # Språk
        language = self.settings.value("language", "Norsk")
        self.language.setCurrentText(language)

        # Enheter
        click_unit = self.settings.value("units/click_unit", "MOA")
        self.click_unit.setCurrentText(click_unit)

        distance_unit = self.settings.value("units/distance", "Meter")
        self.distance_unit.setCurrentText(distance_unit)

        temp_unit = self.settings.value("units/temperature", "Celsius")
        self.temp_unit.setCurrentText(temp_unit)

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

    def save_settings(self):
        """Lagrer innstillinger"""
        # Språk
        self.settings.setValue("language", self.language.currentText())

        # Enheter
        self.settings.setValue("units/click_unit", self.click_unit.currentText())
        self.settings.setValue("units/distance", self.distance_unit.currentText())
        self.settings.setValue("units/temperature", self.temp_unit.currentText())

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

        QMessageBox.information(self, "Suksess", "Innstillinger lagret!")

    def reset_settings(self):
        """Tilbakestiller innstillinger til standard"""
        reply = QMessageBox.question(
            self,
            "Bekreft tilbakestilling",
            "Er du sikker på at du vil tilbakestille alle innstillinger til standard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.settings.clear()
            self.load_settings()
            QMessageBox.information(self, "Suksess", "Innstillinger tilbakestilt!")

    def create_backup(self):
        """Lager backup av database"""
        db_path = "data/reloading.db"
        if not os.path.exists(db_path):
            QMessageBox.warning(self, "Feil", "Database-fil ikke funnet!")
            return

        # Generer backup-filnavn med timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"reloading_backup_{timestamp}.db"

        # Velg lagringsplass
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Lagre backup",
            default_name,
            "Database filer (*.db);;Alle filer (*.*)",
        )

        if file_path:
            try:
                shutil.copy2(db_path, file_path)
                QMessageBox.information(
                    self, "Suksess", f"Backup opprettet:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Feil", f"Kunne ikke opprette backup:\n{str(e)}"
                )

    def restore_backup(self):
        """Gjenoppretter database fra backup"""
        reply = QMessageBox.warning(
            self,
            "ADVARSEL",
            "Gjenoppretting av backup vil OVERSKRIVE nåværende database!\n\n"
            "Alle endringer siden backupen vil gå tapt.\n\n"
            "Er du SIKKER på at du vil fortsette?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Velg backup-fil
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Velg backup-fil", "", "Database filer (*.db);;Alle filer (*.*)"
        )

        if file_path:
            try:
                # Lag sikkerhetskopi av nåværende database først
                db_path = "data/reloading.db"
                safety_backup = f"data/reloading_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, safety_backup)

                # Gjenopprett fra backup
                shutil.copy2(file_path, db_path)

                QMessageBox.information(
                    self,
                    "Suksess",
                    f"Database gjenopprettet fra backup!\n\n"
                    f"Sikkerhetskopi av gammel database:\n{safety_backup}\n\n"
                    f"Du må starte programmet på nytt for å se endringene.",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Feil", f"Kunne ikke gjenopprette backup:\n{str(e)}"
                )

    def on_language_changed(self, index):
        """Håndterer språkendring"""
        from src.utils.i18n import set_language

        language_map = {"Norsk": "no", "English": "en"}

        selected = self.language.currentText()
        lang_code = language_map.get(selected, "no")
        set_language(lang_code)

        # Informer brukeren
        if lang_code == "no":
            msg = "Språk endret til Norsk.\n\nDu må starte programmet på nytt for å se alle endringene."
        else:
            msg = "Language changed to English.\n\nYou must restart the program to see all changes."

        QMessageBox.information(self, "Language / Språk", msg)
