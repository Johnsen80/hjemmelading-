"""
Rifle Accuracy Test System
Systematisk testing av gruppesamlinger med dokumentasjon og utvikling over tid
"""

import json
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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

logger = logging.getLogger(__name__)


class RifleAccuracyTestManager(QWidget):
    """
    Håndterer accuracy tests per rifle over tid
    """

    def __init__(self, parent=None, rifle_id: Optional[int] = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id
        self.init_ui()
        if rifle_id:
            self.load_tests()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("🎯 Accuracy Test System")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel(
            "Systematisk testing av gruppesamlinger. Test ved baseline og hver 500 skudd "
            "for å tracke accuracy-utvikling over rifle-levetiden."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.btn_new_test = QPushButton("➕ Ny Accuracy Test")
        self.btn_new_test.clicked.connect(self.create_new_test)
        self.btn_new_test.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 8px; font-weight: bold;"
        )

        self.btn_view = QPushButton("🔍 Vis Detaljer")
        self.btn_view.clicked.connect(self.view_test_details)
        self.btn_view.setStyleSheet(
            "background-color: #3498db; color: white; padding: 8px;"
        )

        self.btn_print_sheet = QPushButton("🖨️ Print Test Ark")
        self.btn_print_sheet.clicked.connect(self.print_test_sheet)
        self.btn_print_sheet.setStyleSheet(
            "background-color: #9b59b6; color: white; padding: 8px;"
        )

        self.btn_chart = QPushButton("📈 Utviklingskurve")
        self.btn_chart.clicked.connect(self.show_development_chart)
        self.btn_chart.setStyleSheet(
            "background-color: #e67e22; color: white; padding: 8px;"
        )

        self.btn_delete = QPushButton("🗑️ Slett")
        self.btn_delete.clicked.connect(self.delete_test)
        self.btn_delete.setStyleSheet(
            "background-color: #e74c3c; color: white; padding: 8px;"
        )

        btn_layout.addWidget(self.btn_new_test)
        btn_layout.addWidget(self.btn_view)
        btn_layout.addWidget(self.btn_print_sheet)
        btn_layout.addWidget(self.btn_chart)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_delete)

        layout.addLayout(btn_layout)

        # Tests table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Dato",
                "Skudd ved Test",
                "Grupper",
                "Skudd/Gruppe",
                "Avg Gruppe (mm)",
                "Avg MOA",
                "ES fps",
                "SD fps",
                "Status",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.view_test_details)

        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_tests(self):
        """Load all accuracy tests for this rifle"""
        tests = self.db.execute_query(
            """SELECT * FROM rifle_accuracy_tests
               WHERE rifle_id = ?
               ORDER BY test_date DESC, round_count_at_test DESC""",
            (self.rifle_id,),
        )

        self.table.setRowCount(len(tests))

        for row, test in enumerate(tests):
            self.table.setItem(row, 0, QTableWidgetItem(str(test.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(test.get("test_date", "")))
            self.table.setItem(
                row, 2, QTableWidgetItem(str(test.get("round_count_at_test", 0)))
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(str(test.get("groups_fired", 0)))
            )
            self.table.setItem(
                row, 4, QTableWidgetItem(str(test.get("shots_per_group", 0)))
            )

            avg_size = test.get("average_group_size_mm", 0)
            self.table.setItem(
                row, 5, QTableWidgetItem(f"{avg_size:.2f}" if avg_size else "-")
            )

            avg_moa = test.get("average_moa", 0)
            self.table.setItem(
                row, 6, QTableWidgetItem(f"{avg_moa:.3f}" if avg_moa else "-")
            )

            es = test.get("extreme_spread_fps", 0)
            self.table.setItem(row, 7, QTableWidgetItem(str(es) if es else "-"))

            sd = test.get("standard_deviation_fps", 0)
            self.table.setItem(row, 8, QTableWidgetItem(f"{sd:.1f}" if sd else "-"))

            # Status based on results
            status = "📊 Komplett" if test.get("test_completed") else "⚠️ Ufullstendig"
            status_item = QTableWidgetItem(status)

            # Color code based on MOA
            if avg_moa:
                if avg_moa < 0.5:
                    status_item.setForeground(QColor("#27ae60"))  # Excellent
                elif avg_moa < 1.0:
                    status_item.setForeground(QColor("#3498db"))  # Good
                elif avg_moa < 1.5:
                    status_item.setForeground(QColor("#f39c12"))  # OK
                else:
                    status_item.setForeground(QColor("#e74c3c"))  # Poor

            self.table.setItem(row, 9, status_item)

    def create_new_test(self):
        """Create new accuracy test"""
        if not self.rifle_id:
            QMessageBox.warning(self, "Ingen Rifle", "Velg et rifle først.")
            return

        dialog = AccuracyTestDialog(self, rifle_id=self.rifle_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_tests()

    def view_test_details(self):
        """View test details"""
        selected = self.table.currentRow()
        if selected < 0:
            return

        test_id = int(self.table.item(selected, 0).text())
        dialog = AccuracyTestDetailsDialog(self, test_id=test_id)
        dialog.exec()

    def print_test_sheet(self):
        """Print test sheet for field use"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen Test", "Velg en test først.")
            return

        test_id = int(self.table.item(selected, 0).text())
        dialog = TestSheetPrinterDialog(self, test_id=test_id)
        dialog.exec()

    def show_development_chart(self):
        """Show accuracy development over barrel life"""
        dialog = AccuracyDevelopmentChartDialog(self, rifle_id=self.rifle_id)
        dialog.exec()

    def delete_test(self):
        """Delete selected test"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen Test", "Velg en test å slette.")
            return

        reply = QMessageBox.question(
            self,
            "Bekreft Sletting",
            "Er du sikker på at du vil slette denne testen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            test_id = int(self.table.item(selected, 0).text())
            self.db.delete("rifle_accuracy_tests", "id = ?", (test_id,))
            self.load_tests()


class AccuracyTestDialog(QDialog):
    """
    Dialog for creating/editing accuracy test
    """

    def __init__(
        self, parent=None, rifle_id: Optional[int] = None, test_id: Optional[int] = None
    ):
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id
        self.test_id = test_id

        self.setWindowTitle(
            "🎯 Ny Accuracy Test" if test_id is None else "✏️ Rediger Test"
        )
        self.setMinimumSize(900, 700)

        self.init_ui()

        if test_id:
            self.load_test_data()
        else:
            self.prefill_rifle_data()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_test_info_tab(), "📋 Test Info")
        self.tabs.addTab(self.create_load_data_tab(), "🔫 Ladning")
        self.tabs.addTab(self.create_groups_tab(), "🎯 Grupper")
        self.tabs.addTab(self.create_velocity_tab(), "⚡ Hastighet")
        self.tabs.addTab(self.create_photos_tab(), "📷 Bilder")

        layout.addWidget(self.tabs)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Lagre Test")
        self.btn_save.clicked.connect(self.save_test)
        self.btn_save.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 10px; font-weight: bold;"
        )

        self.btn_cancel = QPushButton("❌ Avbryt")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setStyleSheet(
            "background-color: #95a5a6; color: white; padding: 10px;"
        )

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def create_test_info_tab(self):
        """Create test info tab"""
        widget = QWidget()
        layout = QFormLayout()

        self.input_test_date = QDateEdit()
        self.input_test_date.setDate(QDate.currentDate())
        self.input_test_date.setCalendarPopup(True)
        layout.addRow("📅 Test Dato:", self.input_test_date)

        self.input_round_count = QSpinBox()
        self.input_round_count.setRange(0, 10000)
        self.input_round_count.setValue(0)
        self.input_round_count.setSuffix(" skudd")
        layout.addRow("🎯 Skudd ved Test:", self.input_round_count)

        self.input_test_type = QComboBox()
        self.input_test_type.addItems(
            [
                "baseline",  # Initial baseline
                "500_round_check",  # Every 500 rounds
                "load_development",  # Finding optimal load
                "verification",  # Verifying load
                "cold_bore",  # Cold bore accuracy
                "group_test",  # General group test
                "ladder_test",  # Ladder test
            ]
        )
        layout.addRow("📊 Test Type:", self.input_test_type)

        self.input_distance = QDoubleSpinBox()
        self.input_distance.setRange(10, 1000)
        self.input_distance.setValue(100)
        self.input_distance.setSuffix(" m")
        layout.addRow("📏 Distanse:", self.input_distance)

        self.input_groups_fired = QSpinBox()
        self.input_groups_fired.setRange(1, 20)
        self.input_groups_fired.setValue(3)
        self.input_groups_fired.valueChanged.connect(self.on_groups_changed)
        layout.addRow("🎯 Antall Grupper:", self.input_groups_fired)

        self.input_shots_per_group = QSpinBox()
        self.input_shots_per_group.setRange(3, 10)
        self.input_shots_per_group.setValue(5)
        layout.addRow("🔢 Skudd per Gruppe:", self.input_shots_per_group)

        self.input_temperature = QDoubleSpinBox()
        self.input_temperature.setRange(-30, 50)
        self.input_temperature.setValue(15)
        self.input_temperature.setSuffix(" °C")
        layout.addRow("🌡️ Temperatur:", self.input_temperature)

        self.input_wind = QComboBox()
        self.input_wind.addItems(["none", "light", "moderate", "strong"])
        layout.addRow("💨 Vind:", self.input_wind)

        self.input_conditions = QTextEdit()
        self.input_conditions.setMaximumHeight(80)
        self.input_conditions.setPlaceholderText("Værforhold, lysforhold, etc...")
        layout.addRow("📝 Forhold:", self.input_conditions)

        widget.setLayout(layout)
        return widget

    def create_load_data_tab(self):
        """Create load data tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel("🔫 <b>Ladningsdata for denne testen</b>")
        info.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(info)

        _form = QFormLayout()

        # Case info
        case_group = QGroupBox("📦 Hylse")
        case_layout = QFormLayout()

        self.input_case_id = QComboBox()
        cases = self.db.get_all("cases", "name")
        self.input_case_id.addItem("-- Velg Hylse --", None)
        for case in cases:
            self.input_case_id.addItem(
                f"{case['name']} ({case['manufacturer']})", case["id"]
            )
        case_layout.addRow("Hylse:", self.input_case_id)

        self.input_times_fired = QSpinBox()
        self.input_times_fired.setRange(0, 50)
        self.input_times_fired.setValue(1)
        case_layout.addRow("Ganger Fyrt:", self.input_times_fired)

        self.input_case_length = QDoubleSpinBox()
        self.input_case_length.setRange(30, 100)
        self.input_case_length.setValue(50)
        self.input_case_length.setSuffix(" mm")
        self.input_case_length.setDecimals(2)
        case_layout.addRow("Hylse Lengde:", self.input_case_length)

        case_group.setLayout(case_layout)
        layout.addWidget(case_group)

        # Powder
        powder_group = QGroupBox("💨 Krutt")
        powder_layout = QFormLayout()

        self.input_powder_id = QComboBox()
        powders = self.db.get_all("powder", "name")
        self.input_powder_id.addItem("-- Velg Krutt --", None)
        for powder in powders:
            self.input_powder_id.addItem(
                f"{powder['name']} ({powder['manufacturer']})", powder["id"]
            )
        powder_layout.addRow("Krutt:", self.input_powder_id)

        self.input_charge_weight = QDoubleSpinBox()
        self.input_charge_weight.setRange(10, 100)
        self.input_charge_weight.setValue(40)
        self.input_charge_weight.setSuffix(" gr")
        self.input_charge_weight.setDecimals(2)
        powder_layout.addRow("Krutt Mengde:", self.input_charge_weight)

        powder_group.setLayout(powder_layout)
        layout.addWidget(powder_group)

        # Bullet
        bullet_group = QGroupBox("🎯 Kule")
        bullet_layout = QFormLayout()

        self.input_bullet_id = QComboBox()
        bullets = self.db.get_all("bullets", "name")
        self.input_bullet_id.addItem("-- Velg Kule --", None)
        for bullet in bullets:
            self.input_bullet_id.addItem(
                f"{bullet['name']} - {bullet['weight_grains']}gr ({bullet['manufacturer']})",
                bullet["id"],
            )
        bullet_layout.addRow("Kule:", self.input_bullet_id)

        self.input_coal = QDoubleSpinBox()
        self.input_coal.setRange(40, 100)
        self.input_coal.setValue(70)
        self.input_coal.setSuffix(" mm")
        self.input_coal.setDecimals(2)
        bullet_layout.addRow("COAL:", self.input_coal)

        self.input_cbto = QDoubleSpinBox()
        self.input_cbto.setRange(30, 80)
        self.input_cbto.setValue(50)
        self.input_cbto.setSuffix(" mm")
        self.input_cbto.setDecimals(2)
        bullet_layout.addRow("CBTO:", self.input_cbto)

        self.input_jump = QDoubleSpinBox()
        self.input_jump.setRange(0, 5)
        self.input_jump.setValue(0.5)
        self.input_jump.setSuffix(" mm")
        self.input_jump.setDecimals(3)
        bullet_layout.addRow("Jump/Seating Depth:", self.input_jump)

        bullet_group.setLayout(bullet_layout)
        layout.addWidget(bullet_group)

        # Primer
        primer_group = QGroupBox("🔥 Tennhette")
        primer_layout = QFormLayout()

        self.input_primer_id = QComboBox()
        primers = self.db.get_all("primers", "name")
        self.input_primer_id.addItem("-- Velg Tennhette --", None)
        for primer in primers:
            self.input_primer_id.addItem(
                f"{primer['name']} ({primer['manufacturer']} - {primer['type']})",
                primer["id"],
            )
        primer_layout.addRow("Tennhette:", self.input_primer_id)

        primer_group.setLayout(primer_layout)
        layout.addWidget(primer_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_groups_tab(self):
        """Create groups data entry tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel(
            "🎯 <b>Gruppestørrelser</b> - Mål hver gruppe i mm (eller bruk MOA)"
        )
        info.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(info)

        # Dynamic group inputs
        self.groups_widget = QWidget()
        self.groups_layout = QGridLayout()
        self.groups_widget.setLayout(self.groups_layout)

        layout.addWidget(self.groups_widget)

        # Summary
        summary_group = QGroupBox("📊 Oppsummering")
        summary_layout = QFormLayout()

        self.label_avg_size = QLabel("-")
        summary_layout.addRow("Gjennomsnittlig Gruppe:", self.label_avg_size)

        self.label_avg_moa = QLabel("-")
        summary_layout.addRow("Gjennomsnittlig MOA:", self.label_avg_moa)

        self.label_best_group = QLabel("-")
        summary_layout.addRow("Beste Gruppe:", self.label_best_group)

        self.label_worst_group = QLabel("-")
        summary_layout.addRow("Verste Gruppe:", self.label_worst_group)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        layout.addStretch()
        widget.setLayout(layout)

        # Initialize group inputs
        self.on_groups_changed(3)

        return widget

    def create_velocity_tab(self):
        """Create velocity data tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel("⚡ <b>Hastighetsdata</b> - Legg inn hastigheter fra chronograph")
        info.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(info)

        self.velocity_text = QTextEdit()
        self.velocity_text.setPlaceholderText(
            "Legg inn hastigheter, en per linje:\n"
            "2750\n"
            "2755\n"
            "2748\n"
            "2752\n"
            "2750\n"
            "...\n\n"
            "Programmet beregner automatisk ES og SD."
        )
        self.velocity_text.textChanged.connect(self.calculate_velocity_stats)
        layout.addWidget(self.velocity_text)

        # Stats
        stats_group = QGroupBox("📊 Statistikk")
        stats_layout = QFormLayout()

        self.label_avg_velocity = QLabel("-")
        stats_layout.addRow("Gjennomsnitt:", self.label_avg_velocity)

        self.label_es = QLabel("-")
        stats_layout.addRow("ES (Extreme Spread):", self.label_es)

        self.label_sd = QLabel("-")
        stats_layout.addRow("SD (Standard Deviation):", self.label_sd)

        self.label_min_velocity = QLabel("-")
        stats_layout.addRow("Min:", self.label_min_velocity)

        self.label_max_velocity = QLabel("-")
        stats_layout.addRow("Max:", self.label_max_velocity)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        widget.setLayout(layout)
        return widget

    def create_photos_tab(self):
        """Create photos/documentation tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        info = QLabel("📷 <b>Dokumentasjon</b> - Last opp bilder av målskiver")
        info.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(info)

        # Upload buttons
        btn_layout = QHBoxLayout()

        self.btn_upload_target = QPushButton("📷 Last opp Målskive")
        self.btn_upload_target.clicked.connect(self.upload_target_photo)
        btn_layout.addWidget(self.btn_upload_target)

        self.btn_upload_setup = QPushButton("📷 Last opp Setup")
        self.btn_upload_setup.clicked.connect(self.upload_setup_photo)
        btn_layout.addWidget(self.btn_upload_setup)

        layout.addLayout(btn_layout)

        # Photo previews
        self.photos_list = QTextEdit()
        self.photos_list.setReadOnly(True)
        self.photos_list.setPlaceholderText("Ingen bilder lastet opp ennå...")
        layout.addWidget(self.photos_list)

        # Notes
        notes_label = QLabel("📝 Notater:")
        layout.addWidget(notes_label)

        self.input_notes = QTextEdit()
        self.input_notes.setPlaceholderText("Observasjoner, problemer, kommentarer...")
        layout.addWidget(self.input_notes)

        widget.setLayout(layout)
        return widget

    def on_groups_changed(self, num_groups):
        """Update group input fields"""
        # Clear existing inputs
        while self.groups_layout.count():
            child = self.groups_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create new inputs
        self.group_inputs = []

        for i in range(num_groups):
            label = QLabel(f"Gruppe {i+1}:")
            self.groups_layout.addWidget(label, i, 0)

            size_mm = QDoubleSpinBox()
            size_mm.setRange(0, 300)
            size_mm.setValue(0)
            size_mm.setSuffix(" mm")
            size_mm.setDecimals(2)
            size_mm.valueChanged.connect(self.calculate_group_stats)
            self.groups_layout.addWidget(size_mm, i, 1)

            size_moa = QDoubleSpinBox()
            size_moa.setRange(0, 10)
            size_moa.setValue(0)
            size_moa.setSuffix(" MOA")
            size_moa.setDecimals(3)
            size_moa.valueChanged.connect(self.calculate_group_stats)
            self.groups_layout.addWidget(size_moa, i, 2)

            self.group_inputs.append({"mm": size_mm, "moa": size_moa})

    def calculate_group_stats(self):
        """Calculate group statistics"""
        distance_m = self.input_distance.value()

        sizes_mm = []
        for group in self.group_inputs:
            size = group["mm"].value()
            if size > 0:
                sizes_mm.append(size)

        if not sizes_mm:
            self.label_avg_size.setText("-")
            self.label_avg_moa.setText("-")
            self.label_best_group.setText("-")
            self.label_worst_group.setText("-")
            return

        avg_size = sum(sizes_mm) / len(sizes_mm)
        avg_moa = (avg_size / distance_m) * 34.38  # mm to MOA at distance
        best = min(sizes_mm)
        worst = max(sizes_mm)

        self.label_avg_size.setText(f"{avg_size:.2f} mm")
        self.label_avg_moa.setText(f"{avg_moa:.3f} MOA")
        self.label_best_group.setText(
            f"{best:.2f} mm ({(best/distance_m)*34.38:.3f} MOA)"
        )
        self.label_worst_group.setText(
            f"{worst:.2f} mm ({(worst/distance_m)*34.38:.3f} MOA)"
        )

    def calculate_velocity_stats(self):
        """Calculate velocity statistics"""
        text = self.velocity_text.toPlainText()
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        velocities = []
        for line in lines:
            try:
                vel = float(line)
                velocities.append(vel)
            except ValueError:
                continue

        if not velocities:
            self.label_avg_velocity.setText("-")
            self.label_es.setText("-")
            self.label_sd.setText("-")
            self.label_min_velocity.setText("-")
            self.label_max_velocity.setText("-")
            return

        avg = sum(velocities) / len(velocities)
        min_v = min(velocities)
        max_v = max(velocities)
        es = max_v - min_v

        # Standard deviation
        variance = sum((x - avg) ** 2 for x in velocities) / len(velocities)
        sd = variance**0.5

        self.label_avg_velocity.setText(f"{avg:.1f} fps")
        self.label_es.setText(f"{es:.0f} fps")
        self.label_sd.setText(f"{sd:.1f} fps")
        self.label_min_velocity.setText(f"{min_v:.0f} fps")
        self.label_max_velocity.setText(f"{max_v:.0f} fps")

    def prefill_rifle_data(self):
        """Prefill data from rifle"""
        if not self.rifle_id:
            return

        rifle = self.db.get_by_id("rifles", self.rifle_id)
        if rifle:
            self.input_round_count.setValue(rifle.get("round_count", 0) or 0)

    def load_test_data(self):
        """Load existing test data"""
        test = self.db.get_by_id("rifle_accuracy_tests", self.test_id)
        if not test:
            return

        # Test info tab
        self.input_test_date.setDate(QDate.fromString(test["test_date"], "yyyy-MM-dd"))
        self.input_round_count.setValue(test.get("round_count_at_test", 0))
        self.input_test_type.setCurrentText(test.get("test_type", "group_test"))
        self.input_distance.setValue(test.get("distance_meters", 100))
        self.input_groups_fired.setValue(test.get("groups_fired", 3))
        self.input_shots_per_group.setValue(test.get("shots_per_group", 5))
        self.input_temperature.setValue(test.get("temperature_c", 15))
        self.input_wind.setCurrentText(test.get("wind_condition", "none"))
        self.input_conditions.setPlainText(test.get("conditions", ""))

        # Load data tab
        if test.get("case_id"):
            for i in range(self.input_case_id.count()):
                if self.input_case_id.itemData(i) == test["case_id"]:
                    self.input_case_id.setCurrentIndex(i)
                    break

        self.input_times_fired.setValue(test.get("case_times_fired", 1))
        self.input_case_length.setValue(test.get("case_length_mm", 50))

        # ... more loading logic

        self.input_notes.setPlainText(test.get("notes", ""))

    def upload_target_photo(self):
        """Upload target photo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Velg Målskive Bilde", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.photos_list.append(f"📷 Målskive: {file_path}\n")

    def upload_setup_photo(self):
        """Upload setup photo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Velg Setup Bilde", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.photos_list.append(f"📷 Setup: {file_path}\n")

    def save_test(self):
        """Save accuracy test"""
        # Collect group sizes
        group_sizes = []
        for group in self.group_inputs:
            size = group["mm"].value()
            if size > 0:
                group_sizes.append(size)

        if not group_sizes:
            QMessageBox.warning(
                self, "Mangler Data", "Legg inn minst én gruppestørrelse."
            )
            return

        avg_size = sum(group_sizes) / len(group_sizes)
        distance_m = self.input_distance.value()
        avg_moa = (avg_size / distance_m) * 34.38

        # Collect velocities
        velocities = []
        text = self.velocity_text.toPlainText()
        for line in text.split("\n"):
            try:
                vel = float(line.strip())
                velocities.append(vel)
            except Exception as e:
                logger.debug("Failed to parse velocity line: %s", e, exc_info=True)
                pass

        es = None
        sd = None
        avg_velocity = None

        if velocities:
            avg_velocity = sum(velocities) / len(velocities)
            es = max(velocities) - min(velocities)
            variance = sum((x - avg_velocity) ** 2 for x in velocities) / len(
                velocities
            )
            sd = variance**0.5

        data = {
            "rifle_id": self.rifle_id,
            "test_date": self.input_test_date.date().toString("yyyy-MM-dd"),
            "round_count_at_test": self.input_round_count.value(),
            "test_type": self.input_test_type.currentText(),
            "distance_meters": self.input_distance.value(),
            "groups_fired": len(group_sizes),
            "shots_per_group": self.input_shots_per_group.value(),
            "group_sizes_mm": json.dumps(group_sizes),
            "average_group_size_mm": avg_size,
            "best_group_mm": min(group_sizes),
            "worst_group_mm": max(group_sizes),
            "average_moa": avg_moa,
            "temperature_c": self.input_temperature.value(),
            "wind_condition": self.input_wind.currentText(),
            "conditions": self.input_conditions.toPlainText(),
            # Load data
            "case_id": self.input_case_id.currentData(),
            "case_times_fired": self.input_times_fired.value(),
            "case_length_mm": self.input_case_length.value(),
            "powder_id": self.input_powder_id.currentData(),
            "charge_weight_grains": self.input_charge_weight.value(),
            "bullet_id": self.input_bullet_id.currentData(),
            "coal_mm": self.input_coal.value(),
            "cbto_mm": self.input_cbto.value(),
            "seating_depth_jump_mm": self.input_jump.value(),
            "primer_id": self.input_primer_id.currentData(),
            # Velocity
            "velocities_fps": json.dumps(velocities) if velocities else None,
            "average_velocity_fps": avg_velocity,
            "extreme_spread_fps": es,
            "standard_deviation_fps": sd,
            "notes": self.input_notes.toPlainText(),
            "test_completed": True,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            if self.test_id:
                self.db.update("rifle_accuracy_tests", data, "id = ?", (self.test_id,))
                QMessageBox.information(self, "Lagret", "Test oppdatert!")
            else:
                self.db.insert("rifle_accuracy_tests", data)
                QMessageBox.information(self, "Lagret", "Test lagret!")

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Kunne ikke lagre: {str(e)}")


class AccuracyTestDetailsDialog(QDialog):
    """View detailed test results"""

    def __init__(self, parent=None, test_id: Optional[int] = None):
        super().__init__(parent)
        self.db = get_database()
        self.test_id = test_id

        self.setWindowTitle("🔍 Test Detaljer")
        self.setMinimumSize(700, 600)

        self.init_ui()
        self.load_details()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        self.details_display = QTextEdit()
        self.details_display.setReadOnly(True)
        layout.addWidget(self.details_display)

        btn_close = QPushButton("✓ Lukk")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)

    def load_details(self):
        """Load and display test details"""
        test = self.db.get_by_id("rifle_accuracy_tests", self.test_id)
        if not test:
            return

        # Get rifle name
        rifle = self.db.get_by_id("rifles", test["rifle_id"])
        rifle_name = rifle["name"] if rifle else "Unknown"

        html = f"""
        <h2>🎯 Accuracy Test</h2>
        <h3>{rifle_name}</h3>

        <h4>Test Info</h4>
        <ul>
            <li><b>Dato:</b> {test.get('test_date', '-')}</li>
            <li><b>Skudd ved test:</b> {test.get('round_count_at_test', 0)}</li>
            <li><b>Type:</b> {test.get('test_type', '-')}</li>
            <li><b>Distanse:</b> {test.get('distance_meters', 0)} m</li>
            <li><b>Temperatur:</b> {test.get('temperature_c', 0)}°C</li>
            <li><b>Vind:</b> {test.get('wind_condition', '-')}</li>
        </ul>

        <h4>Resultater</h4>
        <ul>
            <li><b>Grupper fyrt:</b> {test.get('groups_fired', 0)}</li>
            <li><b>Skudd per gruppe:</b> {test.get('shots_per_group', 0)}</li>
            <li><b>Gjennomsnittlig gruppe:</b> {test.get('average_group_size_mm', 0):.2f} mm</li>
            <li><b>Gjennomsnittlig MOA:</b> {test.get('average_moa', 0):.3f} MOA</li>
            <li><b>Beste gruppe:</b> {test.get('best_group_mm', 0):.2f} mm</li>
            <li><b>Verste gruppe:</b> {test.get('worst_group_mm', 0):.2f} mm</li>
        </ul>

        <h4>Hastighet</h4>
        <ul>
            <li><b>Gjennomsnitt:</b> {test.get('average_velocity_fps', 0):.0f} fps</li>
            <li><b>ES:</b> {test.get('extreme_spread_fps', 0):.0f} fps</li>
            <li><b>SD:</b> {test.get('standard_deviation_fps', 0):.1f} fps</li>
        </ul>

        <h4>Notater</h4>
        <p>{test.get('notes', '-')}</p>
        """

        self.details_display.setHtml(html)


class TestSheetPrinterDialog(QDialog):
    """Print test sheet for field use"""

    def __init__(self, parent=None, test_id: Optional[int] = None):
        super().__init__(parent)
        self.test_id = test_id

        self.setWindowTitle("🖨️ Print Test Ark")
        self.setMinimumSize(800, 1000)

        QMessageBox.information(
            self,
            "Print Test Ark",
            "Denne funksjonen vil generere et print-vennlig ark med:\n\n"
            "• Ladningsdata\n"
            "• Nummererte skudd (1, 2, 3...)\n"
            "• Plass for å notere resultater\n"
            "• QR-kode for rask data-entry senere\n\n"
            "Kommer snart...",
        )

        self.accept()


class AccuracyDevelopmentChartDialog(QDialog):
    """Show accuracy development over barrel life"""

    def __init__(self, parent=None, rifle_id: Optional[int] = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id

        self.setWindowTitle("📈 Accuracy Utvikling")
        self.setMinimumSize(800, 600)

        self.init_ui()
        self.load_chart_data()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        label = QLabel("📈 <b>Accuracy Utvikling Over Pipe-Levetid</b>")
        label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(label)

        self.chart_display = QTextEdit()
        self.chart_display.setReadOnly(True)
        layout.addWidget(self.chart_display)

        btn_close = QPushButton("✓ Lukk")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)

    def load_chart_data(self):
        """Load and display chart data"""
        tests = self.db.execute_query(
            """SELECT round_count_at_test, average_moa, average_group_size_mm, test_date
               FROM rifle_accuracy_tests
               WHERE rifle_id = ? AND test_completed = 1
               ORDER BY round_count_at_test""",
            (self.rifle_id,),
        )

        if not tests:
            self.chart_display.setHtml("<p>Ingen tester funnet ennå.</p>")
            return

        html = "<h3>Accuracy Trend</h3><table border='1' cellpadding='5'>"
        html += "<tr><th>Skudd</th><th>Dato</th><th>MOA</th><th>Gruppe (mm)</th><th>Trend</th></tr>"

        prev_moa = None
        for test in tests:
            rounds = test["round_count_at_test"]
            moa = test["average_moa"]
            group_mm = test["average_group_size_mm"]
            date = test["test_date"]

            trend = ""
            if prev_moa:
                if moa < prev_moa:
                    trend = "📈 Bedre"
                elif moa > prev_moa:
                    trend = "📉 Dårligere"
                else:
                    trend = "➡️ Lik"

            html += f"<tr><td>{rounds}</td><td>{date}</td><td>{moa:.3f}</td><td>{group_mm:.2f}</td><td>{trend}</td></tr>"
            prev_moa = moa

        html += "</table>"
        html += "<p><i>Implementer plotting med matplotlib senere...</i></p>"

        self.chart_display.setHtml(html)
