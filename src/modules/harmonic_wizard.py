"""Harmonics Lab.

Seating-depth and harmonics analysis based on measured test results.
"""

from datetime import datetime

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from ..utils.optional_deps import Figure as Figure
from ..utils.optional_deps import FigureCanvas as FigureCanvas

try:
    from scipy.interpolate import UnivariateSpline
    from scipy.signal import find_peaks

    HAS_SCIPY = True
except Exception:  # pragma: no cover - optional dep
    # Provide safe fallbacks so module can import in headless/CI environments.
    UnivariateSpline = None  # type: ignore

    def find_peaks(*args, **kwargs):
        # Minimal placeholder: return empty peaks array and empty properties dict
        return ([], {})

    HAS_SCIPY = False

from ..database.database import get_database


class HarmonicWizard(QWidget):
    """Main widget for Harmonics Lab."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_tests()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel med disclaimer
        title = QLabel("Harmonics Lab - Seating Depth Assistant")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        disclaimer = QLabel(
            """
        <b style='color: #d9534f;'>IMPORTANT:</b> This tool analyzes <i>your actual test results</i>
        and suggests seating depths with a high probability of good precision.
        It does NOT calculate theoretical harmonics. It learns from your shots.<br>
        <b>You are always responsible for safe loading within published load data limits.</b>
        """
        )
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet(
            """
            background-color: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0px;
        """
        )
        layout.addWidget(disclaimer)

        # Scipy-status-banner — vis tydelig om analyse er tilgjengelig
        if not HAS_SCIPY:
            scipy_warning = QLabel(
                "<b>⚠ Harmonisk analyse er deaktivert</b> — <tt>scipy</tt>-biblioteket mangler.<br>"
                "Installer det med: <tt>pip install scipy</tt> og start programmet på nytt.<br>"
                "Testdata kan fortsatt registreres og lagres for analyse når scipy er installert."
            )
            scipy_warning.setWordWrap(True)
            scipy_warning.setStyleSheet(
                "background-color:#f8d7da; border:2px solid #f5c6cb;"
                "border-radius:5px; padding:10px; margin:4px 0;"
            )
            layout.addWidget(scipy_warning)

        # Knapper
        btn_layout = QHBoxLayout()

        new_test_btn = QPushButton("New Seating Depth Test")
        new_test_btn.setMinimumHeight(40)
        new_test_btn.setStyleSheet(
            "background-color: #5cb85c; color: white; font-weight: bold;"
        )
        new_test_btn.clicked.connect(self.start_new_test)
        btn_layout.addWidget(new_test_btn)

        analyze_btn = QPushButton("Analyze Test")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.analyze_test)
        btn_layout.addWidget(analyze_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_test)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Info
        info = QLabel(
            """
        <h3>How it works:</h3>
        <ol>
            <li><b>Create test:</b> Define the barrel profile, bullet, and seating depths to test</li>
            <li><b>Shoot the test:</b> Fire 3-5 shots per seating depth and log group size and ES/SD</li>
            <li><b>Analyze:</b> The guide finds harmonic nodes, areas where precision looks stable</li>
            <li><b>Refine:</b> Test the recommended area with fine adjustments (±0.05 mm)</li>
        </ol>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tabell med tester
        self.tests_table = QTableWidget()
        self.tests_table.setColumnCount(7)
        self.tests_table.setHorizontalHeaderLabels(
            ["Name", "Date", "Rifle", "Bullet", "Powder", "Test Points", "Status"]
        )
        self.tests_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.tests_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tests_table.doubleClicked.connect(self.analyze_test)
        layout.addWidget(self.tests_table)

    def load_tests(self):
        """Laster settedybde-tester"""
        # Vi bruker en egen tabell for dette
        tests = self.db.execute_query(
            """
            SELECT * FROM seating_depth_tests ORDER BY date DESC
        """
        )

        if not tests:
            tests = []

        self.tests_table.setRowCount(len(tests))

        for i, test in enumerate(tests):
            self.tests_table.setItem(i, 0, QTableWidgetItem(test["name"]))
            self.tests_table.setItem(i, 1, QTableWidgetItem(test["date"]))

            # Rifle
            rifle_name = "-"
            if test["rifle_id"]:
                rifle = self.db.get_by_id("rifles", test["rifle_id"])
                if rifle:
                    rifle_name = rifle["name"]
            self.tests_table.setItem(i, 2, QTableWidgetItem(rifle_name))

            # Kule
            bullet_name = "-"
            if test["bullet_id"]:
                bullet = self.db.get_by_id("bullets", test["bullet_id"])
                if bullet:
                    bullet_name = f"{bullet['name']} {bullet['weight_grains']}gr"
            self.tests_table.setItem(i, 3, QTableWidgetItem(bullet_name))

            # Krutt
            powder_name = "-"
            if test["powder_id"]:
                powder = self.db.get_by_id("powder", test["powder_id"])
                if powder:
                    powder_name = powder["name"]
            self.tests_table.setItem(i, 4, QTableWidgetItem(powder_name))

            # Tell testpunkter
            results = self.db.execute_query(
                "SELECT COUNT(*) as count FROM seating_depth_results WHERE test_id = ?",
                (test["id"],),
            )
            count = results[0]["count"] if results else 0
            self.tests_table.setItem(i, 5, QTableWidgetItem(f"{count} points"))

            # Status
            status = "Complete" if count >= 3 else "Incomplete"
            status_item = QTableWidgetItem(status)
            if count >= 3:
                status_item.setForeground(QColor("green"))
            self.tests_table.setItem(i, 6, status_item)

            self.tests_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, test["id"])

    def start_new_test(self):
        """Starter wizard for ny test"""
        wizard = SeatingDepthWizard(self)
        wizard.exec()
        self.load_tests()

    def analyze_test(self):
        """Analyserer valgt test"""
        if not HAS_SCIPY:
            QMessageBox.warning(
                self,
                "Analyse utilgjengelig",
                "Harmonisk analyse krever scipy-biblioteket.\n\n"
                "Installer det med:\n    pip install scipy\n\n"
                "Start programmet på nytt etter installasjonen.\n"
                "Testdata du har registrert er trygt lagret.",
            )
            return

        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No selection", "Select a test first.")
            return

        test_id = self.tests_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)

        # Hent test og resultater
        test_rows = self.db.execute_query(
            "SELECT * FROM seating_depth_tests WHERE id = ?", (test_id,)
        )
        if not test_rows:
            QMessageBox.warning(
                self,
                "Test missing",
                "The selected seating depth test no longer exists in the database.",
            )
            self.load_tests()
            return
        test = test_rows[0]

        results = self.db.execute_query(
            "SELECT * FROM seating_depth_results WHERE test_id = ? ORDER BY coal",
            (test_id,),
        )

        if len(results) < 3:
            QMessageBox.warning(
                self,
                "Not enough data",
                "You need at least 3 test points to run the analysis.",
            )
            return

        # Åpne analyse-vindu
        dialog = HarmonicAnalysisDialog(self, test, results)
        dialog.exec()

    def delete_test(self):
        """Sletter valgt test"""
        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No selection", "Select a test first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm delete",
            "Are you sure you want to delete this test?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            test_id = self.tests_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete("seating_depth_results", "test_id = ?", (test_id,))
            self.db.delete("seating_depth_tests", "id = ?", (test_id,))
            self.load_tests()


class SeatingDepthWizard(QWizard):
    """Wizard for setting up a seating depth test."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.setWindowTitle("New Seating Depth Test - Setup")
        self.setMinimumSize(700, 600)

        # Legg til sider
        self.addPage(BarrelProfilePage(self))
        self.addPage(ComponentsPage(self))
        self.addPage(TestSetupPage(self))
        self.addPage(SummaryPage(self))

        self.finished.connect(self.save_test)

    def save_test(self, result):
        """Lagrer testen"""
        if result == QWizard.DialogCode.Accepted:
            # Hent data fra wizarden
            data = {
                "name": self.field("test_name"),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "rifle_id": self.field("rifle_id"),
                "barrel_length": self.field("barrel_length"),
                "barrel_contour": self.field("barrel_contour"),
                "muzzle_device": self.field("muzzle_device"),
                "muzzle_device_weight": self.field("muzzle_weight"),
                "bullet_id": self.field("bullet_id"),
                "powder_id": self.field("powder_id"),
                "powder_charge": self.field("powder_charge"),
                "primer_id": self.field("primer_id"),
                "case_id": self.field("case_id"),
                "start_coal": self.field("start_coal"),
                "end_coal": self.field("end_coal"),
                "coal_step": self.field("coal_step"),
                "rounds_per_coal": self.field("rounds_per_coal"),
                "distance_meters": self.field("distance"),
                "notes": self.field("notes"),
            }

            test_id = self.db.insert("seating_depth_tests", data)

            # Generer testpunkter
            start = data["start_coal"]
            end = data["end_coal"]
            step = data["coal_step"]

            coal_values = []
            current = start
            while current <= end + 0.001:  # +0.001 for floating point
                coal_values.append(round(current, 2))
                current += step

            # Opprett placeholder-resultater
            for coal in coal_values:
                self.db.insert(
                    "seating_depth_results",
                    {
                        "test_id": test_id,
                        "coal": coal,
                        "group_size_mm": None,
                        "velocity_avg": None,
                        "velocity_es": None,
                        "velocity_sd": None,
                        "notes": None,
                    },
                )

            QMessageBox.information(
                self,
                "Test created",
                f"Seating depth test created with {len(coal_values)} test points.\n\n"
                f"You can now shoot the test and enter results.",
            )


class BarrelProfilePage(QWizardPage):
    """Step 1: barrel information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 1: Barrel Profile and Configuration")
        self.setSubTitle(
            "Enter the barrel's physical characteristics. This is used to improve "
            "the local model's understanding of your firearm dynamics."
        )

        self.db = get_database()
        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Rifle
        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem("-- Select rifle --", None)
        rifles = self.db.get_all("rifles")
        for rifle in rifles:
            self.rifle_combo.addItem(
                f"{rifle['name']} ({rifle['caliber']})", rifle["id"]
            )
        form.addRow("Rifle:", self.rifle_combo)

        # Løpslengde
        self.barrel_length = QDoubleSpinBox()
        self.barrel_length.setRange(30, 100)
        self.barrel_length.setValue(61)
        self.barrel_length.setDecimals(1)
        self.barrel_length.setSuffix(" cm")
        form.addRow("Barrel length:", self.barrel_length)

        # Kontur
        self.barrel_contour = QComboBox()
        self.barrel_contour.addItems(
            [
                "Light Sporter",
                "Medium Sporter",
                "Heavy Sporter",
                "Medium Palma",
                "Heavy Palma",
                "Varmint",
                "MTU/PRS",
                "Bull Barrel",
            ]
        )
        self.barrel_contour.setCurrentText("Medium Sporter")
        form.addRow("Barrel contour:", self.barrel_contour)

        layout.addLayout(form)

        # Munningsmiddel
        muzzle_group = QGroupBox("Muzzle Device (Suppressor/Brake)")
        muzzle_layout = QFormLayout()
        muzzle_group.setLayout(muzzle_layout)

        self.muzzle_device = QComboBox()
        self.muzzle_device.addItems(
            [
                "None",
                "Muzzle Brake",
                "Suppressor (Light)",
                "Suppressor (Medium)",
                "Suppressor (Heavy)",
            ]
        )
        muzzle_layout.addRow("Type:", self.muzzle_device)

        self.muzzle_weight = QSpinBox()
        self.muzzle_weight.setRange(0, 1000)
        self.muzzle_weight.setValue(0)
        self.muzzle_weight.setSuffix(" g")
        muzzle_layout.addRow("Weight (approx):", self.muzzle_weight)

        layout.addWidget(muzzle_group)

        # Registrer felt
        self.registerField("rifle_id", self.rifle_combo, "currentData")
        self.registerField("barrel_length", self.barrel_length)
        self.registerField("barrel_contour", self.barrel_contour, "currentText")
        self.registerField("muzzle_device", self.muzzle_device, "currentText")
        self.registerField("muzzle_weight", self.muzzle_weight)


class ComponentsPage(QWizardPage):
    """Step 2: components."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 2: Ammunition Components")
        self.setSubTitle("Select the components used in this test")

        self.db = get_database()
        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Kule
        self.bullet_combo = QComboBox()
        self.bullet_combo.addItem("-- Select bullet --", None)
        bullets = self.db.get_all("bullets")
        for bullet in bullets:
            self.bullet_combo.addItem(
                f"{bullet['name']} - {bullet['weight_grains']}gr", bullet["id"]
            )
        form.addRow("Bullet:", self.bullet_combo)

        # Krutt
        self.powder_combo = QComboBox()
        self.powder_combo.addItem("-- Select powder --", None)
        powders = self.db.get_all("powder")
        for powder in powders:
            self.powder_combo.addItem(powder["name"], powder["id"])
        form.addRow("Powder:", self.powder_combo)

        # Kruttvekt
        self.powder_charge = QDoubleSpinBox()
        self.powder_charge.setRange(10, 100)
        self.powder_charge.setDecimals(1)
        self.powder_charge.setSuffix(" gr")
        form.addRow("Powder charge:", self.powder_charge)

        # Tennhette
        self.primer_combo = QComboBox()
        self.primer_combo.addItem("-- Select primer --", None)
        primers = self.db.get_all("primers")
        for primer in primers:
            self.primer_combo.addItem(primer["name"], primer["id"])
        form.addRow("Primer:", self.primer_combo)

        # Hylse
        self.case_combo = QComboBox()
        self.case_combo.addItem("-- Select case --", None)
        cases = self.db.get_all("cases")
        for case in cases:
            self.case_combo.addItem(f"{case['name']} - {case['caliber']}", case["id"])
        form.addRow("Case:", self.case_combo)

        layout.addLayout(form)

        # Registrer felt
        self.registerField("bullet_id*", self.bullet_combo, "currentData")
        self.registerField("powder_id*", self.powder_combo, "currentData")
        self.registerField("powder_charge", self.powder_charge)
        self.registerField("primer_id", self.primer_combo, "currentData")
        self.registerField("case_id", self.case_combo, "currentData")


class TestSetupPage(QWizardPage):
    """Step 3: test setup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 3: Define Test Range")
        self.setSubTitle(
            "Enter the COAL range you want to test. Tip: start with 0.2-0.3 mm steps "
            "and refine later in promising regions."
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Testnavn
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Test name:"))
        self.test_name = QLineEdit()
        self.test_name.setPlaceholderText("e.g. 6.5CM ELD-M Seating Depth #1")
        name_layout.addWidget(self.test_name)
        layout.addLayout(name_layout)

        # COAL-område
        coal_group = QGroupBox("COAL Range (Cartridge Overall Length)")
        coal_layout = QFormLayout()
        coal_group.setLayout(coal_layout)

        self.start_coal = QDoubleSpinBox()
        self.start_coal.setRange(50, 100)
        self.start_coal.setDecimals(2)
        self.start_coal.setValue(73.50)
        self.start_coal.setSuffix(" mm")
        coal_layout.addRow("Start COAL:", self.start_coal)

        self.end_coal = QDoubleSpinBox()
        self.end_coal.setRange(50, 100)
        self.end_coal.setDecimals(2)
        self.end_coal.setValue(74.50)
        self.end_coal.setSuffix(" mm")
        coal_layout.addRow("End COAL:", self.end_coal)

        self.coal_step = QDoubleSpinBox()
        self.coal_step.setRange(0.05, 1.0)
        self.coal_step.setDecimals(2)
        self.coal_step.setValue(0.20)
        self.coal_step.setSuffix(" mm")
        coal_layout.addRow("Step size:", self.coal_step)

        # Antall testpunkter
        self.test_points_label = QLabel()
        self.update_test_points()
        coal_layout.addRow("Test point count:", self.test_points_label)

        self.start_coal.valueChanged.connect(self.update_test_points)
        self.end_coal.valueChanged.connect(self.update_test_points)
        self.coal_step.valueChanged.connect(self.update_test_points)

        layout.addWidget(coal_group)

        # Test-parametere
        test_group = QGroupBox("Test Parameters")
        test_layout = QFormLayout()
        test_group.setLayout(test_layout)

        self.rounds_per_coal = QSpinBox()
        self.rounds_per_coal.setRange(3, 10)
        self.rounds_per_coal.setValue(3)
        self.rounds_per_coal.setSuffix(" shots")
        test_layout.addRow("Shots per COAL:", self.rounds_per_coal)

        self.distance = QSpinBox()
        self.distance.setRange(50, 500)
        self.distance.setValue(100)
        self.distance.setSuffix(" m")
        test_layout.addRow("Test distance:", self.distance)

        layout.addWidget(test_group)

        # Notater
        layout.addWidget(QLabel("Notes:"))
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Additional notes about the test...")
        layout.addWidget(self.notes)

        # Registrer felt
        self.registerField("test_name*", self.test_name)
        self.registerField("start_coal", self.start_coal)
        self.registerField("end_coal", self.end_coal)
        self.registerField("coal_step", self.coal_step)
        self.registerField("rounds_per_coal", self.rounds_per_coal)
        self.registerField("distance", self.distance)
        self.registerField("notes", self.notes, "plainText")

    def update_test_points(self):
        """Oppdaterer antall testpunkter"""
        start = self.start_coal.value()
        end = self.end_coal.value()
        step = self.coal_step.value()

        if step > 0 and end >= start:
            points = int((end - start) / step) + 1
            total_rounds = points * self.rounds_per_coal.value()
            self.test_points_label.setText(
                f"<b>{points} points</b> = <b>{total_rounds} cartridges</b> total"
            )
        else:
            self.test_points_label.setText("<b>0 points</b>")


class SummaryPage(QWizardPage):
    """Step 4: summary."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 4: Summary")
        self.setSubTitle("Check that everything is correct before creating the test")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

    def initializePage(self):
        """Viser oppsummering"""
        wizard = self.wizard()

        start = wizard.field("start_coal")
        end = wizard.field("end_coal")
        step = wizard.field("coal_step")
        points = int((end - start) / step) + 1
        total_rounds = points * wizard.field("rounds_per_coal")

        summary = f"""
        <h3>{wizard.field('test_name')}</h3>

        <h4>Barrel profile:</h4>
        <ul>
            <li>Length: {wizard.field('barrel_length')} cm</li>
            <li>Contour: {wizard.field('barrel_contour')}</li>
            <li>Muzzle device: {wizard.field('muzzle_device')} ({wizard.field('muzzle_weight')} g)</li>
        </ul>

        <h4>Test range:</h4>
        <ul>
            <li>COAL: {start} - {end} mm (step: {step} mm)</li>
            <li><b>{points} test points</b></li>
            <li>{wizard.field('rounds_per_coal')} shots per point</li>
            <li><b>Total: {total_rounds} cartridges</b></li>
            <li>Distance: {wizard.field('distance')} m</li>
        </ul>

        <p style='color: #5cb85c; font-weight: bold;'>
        Ready to create the test. After creation, you can enter results as you shoot.
        </p>
        """

        self.summary_label.setText(summary)


class HarmonicAnalysisDialog(QDialog):
    """Dialog for analyse av settedybde-test"""

    def __init__(self, parent=None, test=None, results=None):
        super().__init__(parent)
        self.test = test
        self.results = results or []
        self.setWindowTitle(f"Harmonikk-analyse: {test['name']}")
        self.setMinimumSize(1100, 800)

        self.init_ui()

    def init_ui(self):
        """Initialiserer analyse-vindu"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel(f"<h2>{self.test['name']}</h2>")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Data & input
        tabs.addTab(self.create_data_tab(), "Testdata")

        # Tab 2: Graf & analyse
        tabs.addTab(self.create_analysis_tab(), "AI-Analyse")

        # Tab 3: Recommendation
        tabs.addTab(self.create_recommendation_tab(), "Recommendations")

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def create_data_tab(self):
        """Create the data tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            f"""
        <b>Test:</b> {self.test['name']}<br>
        <b>Date:</b> {self.test['date']}<br>
        <b>Distance:</b> {self.test['distance_meters']}m
        """
        )
        layout.addWidget(info)

        # Tabell med resultater
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["COAL (mm)", "Group (mm)", "Avg V (fps)", "ES", "SD", "Notes"]
        )

        table.setRowCount(len(self.results))

        for i, result in enumerate(self.results):
            table.setItem(i, 0, QTableWidgetItem(f"{result['coal']:.2f}"))

            group = f"{result['group_size_mm']:.1f}" if result["group_size_mm"] else "-"
            table.setItem(i, 1, QTableWidgetItem(group))

            vel = f"{result['velocity_avg']:.0f}" if result["velocity_avg"] else "-"
            table.setItem(i, 2, QTableWidgetItem(vel))

            es = f"{result['velocity_es']:.0f}" if result["velocity_es"] else "-"
            table.setItem(i, 3, QTableWidgetItem(es))

            sd = f"{result['velocity_sd']:.1f}" if result["velocity_sd"] else "-"
            table.setItem(i, 4, QTableWidgetItem(sd))

            notes = result["notes"] if result["notes"] else ""
            table.setItem(i, 5, QTableWidgetItem(notes))

        table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        layout.addWidget(table)

        # Knapp for å oppdatere data
        update_btn = QPushButton("Edit test data")
        update_btn.clicked.connect(self.edit_test_data)
        layout.addWidget(update_btn)

        return widget

    def create_analysis_tab(self):
        """Create the analysis tab with charts."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Matplotlib figur
        fig = Figure(figsize=(12, 10))
        canvas = FigureCanvas(fig)

        # Hent data
        coal_values = []
        group_sizes = []
        velocities = []
        sd_values = []

        for result in self.results:
            if result["group_size_mm"]:
                coal_values.append(result["coal"])
                group_sizes.append(result["group_size_mm"])

                if result["velocity_avg"]:
                    velocities.append(result["velocity_avg"])
                else:
                    velocities.append(None)

                if result["velocity_sd"]:
                    sd_values.append(result["velocity_sd"])
                else:
                    sd_values.append(None)

        if len(coal_values) < 3:
            layout.addWidget(
                QLabel("Not enough data to run the analysis. Enter more results.")
            )
            return widget

        # Plot 1: Gruppestørrelse vs COAL med spline
        ax1 = fig.add_subplot(2, 2, 1)
        ax1.scatter(coal_values, group_sizes, s=100, c="blue", alpha=0.6, zorder=3)

        # Fit spline
        if len(coal_values) >= 4:
            coal_smooth = np.linspace(min(coal_values), max(coal_values), 100)
            try:
                spl = UnivariateSpline(
                    coal_values, group_sizes, k=3, s=len(coal_values) * 2
                )
                group_smooth = spl(coal_smooth)
                ax1.plot(coal_smooth, group_smooth, "b-", alpha=0.3, linewidth=2)
            except Exception:
                pass

        ax1.set_xlabel("COAL (mm)", fontsize=11)
        ax1.set_ylabel("Group Size (mm)", fontsize=11)
        ax1.set_title("Group Size vs Seating Depth", fontsize=12, fontweight="bold")
        ax1.grid(True, alpha=0.3)

        # Plot 2: SD vs COAL
        ax2 = fig.add_subplot(2, 2, 2)
        valid_sd = [(c, s) for c, s in zip(coal_values, sd_values) if s is not None]
        if valid_sd:
            sd_coal, sd_vals = zip(*valid_sd)
            ax2.scatter(sd_coal, sd_vals, s=100, c="green", alpha=0.6)
            ax2.set_xlabel("COAL (mm)", fontsize=11)
            ax2.set_ylabel("SD (fps)", fontsize=11)
            ax2.set_title(
                "Velocity Consistency vs Seating Depth", fontsize=12, fontweight="bold"
            )
            ax2.grid(True, alpha=0.3)

        # Plot 3: Kombinert "sweet spot" analyse
        ax3 = fig.add_subplot(2, 1, 2)

        # Normaliser gruppestørrelse (invertert - mindre er bedre)
        group_norm = np.array(group_sizes)
        group_norm = 1 - (group_norm - min(group_norm)) / (
            max(group_norm) - min(group_norm) + 0.001
        )

        ax3.plot(
            coal_values,
            group_norm,
            "b-o",
            linewidth=2,
            markersize=8,
            label="Precision (normalized)",
        )

        # Finn lokale maksima (= gode områder)
        if len(group_norm) >= 3:
            peaks, properties = find_peaks(group_norm, prominence=0.1)
            if len(peaks) > 0:
                ax3.plot(
                    np.array(coal_values)[peaks],
                    group_norm[peaks],
                    "r*",
                    markersize=15,
                    label="Potential nodes",
                )

        ax3.set_xlabel("COAL (mm)", fontsize=11)
        ax3.set_ylabel("Precision Score (higher = better)", fontsize=11)
        ax3.set_title('Identified "Harmonic Nodes"', fontsize=12, fontweight="bold")
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(-0.1, 1.1)

        fig.tight_layout()
        layout.addWidget(canvas)

        return widget

    def create_recommendation_tab(self):
        """Create the recommendations tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Kjør AI-analyse
        coal_values = []
        group_sizes = []
        sd_values = []

        for result in self.results:
            if result["group_size_mm"]:
                coal_values.append(result["coal"])
                group_sizes.append(result["group_size_mm"])
                if result["velocity_sd"]:
                    sd_values.append(result["velocity_sd"])
                else:
                    sd_values.append(999)  # Høy verdi hvis missing

        if len(coal_values) < 3:
            layout.addWidget(QLabel("Not enough data for recommendations"))
            return widget

        # Finn beste gruppe
        best_idx = np.argmin(group_sizes)
        best_coal = coal_values[best_idx]
        best_group = group_sizes[best_idx]

        # Normaliser og finn peaks
        group_norm = np.array(group_sizes)
        group_norm_inv = 1 - (group_norm - min(group_norm)) / (
            max(group_norm) - min(group_norm) + 0.001
        )

        peaks, properties = find_peaks(group_norm_inv, prominence=0.1)

        # Generer anbefaling
        rec_html = "<h2>Guided Recommendations</h2>"

        rec_html += f"""
        <div style='background-color: #d4edda; border: 2px solid #28a745; border-radius: 5px; padding: 15px; margin: 10px 0;'>
            <h3 style='color: #155724;'>Best observed precision:</h3>
            <p style='font-size: 14pt;'>
                <b>COAL: {best_coal:.2f} mm</b><br>
                Group size: {best_group:.1f} mm
            </p>
        </div>
        """

        if len(peaks) > 0:
            rec_html += "<h3>Identified harmonic nodes:</h3><ul>"

            # Sorter peaks etter score
            peak_scores = group_norm_inv[peaks]
            sorted_peaks = sorted(
                zip(peaks, peak_scores), key=lambda x: x[1], reverse=True
            )

            for i, (peak_idx, score) in enumerate(sorted_peaks[:3], 1):
                peak_coal = coal_values[peak_idx]
                peak_group = group_sizes[peak_idx]
                rec_html += f"""
                <li><b>Node {i}:</b> COAL {peak_coal:.2f} mm
                    (Group: {peak_group:.1f} mm, Score: {score:.2f})</li>
                """

            rec_html += "</ul>"
        else:
            rec_html += "<p>No clear harmonic nodes were found. This may mean:</p><ul>"
            rec_html += "<li>Too few test points</li>"
            rec_html += "<li>Step size is too large between COAL values</li>"
            rec_html += "<li>The firearm is not very sensitive to seating depth in this range</li></ul>"

        # Neste steg
        rec_html += f"""
        <hr>
        <h3>Recommended next steps:</h3>
        <ol>
            <li><b>Refine the best zone:</b> Test COAL {best_coal-0.10:.2f} - {best_coal+0.10:.2f} mm
                in 0.05 mm steps (5 points)</li>
            <li><b>Increase shot count:</b> Fire 5-10 shots per COAL for stronger statistics</li>
            <li><b>Verify at longer range:</b> Test the best COAL at {self.test['distance_meters']*2}m</li>
            <li><b>Check robustness:</b> Test across different weather conditions and temperatures</li>
        </ol>

        <div style='background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 5px; padding: 10px; margin: 10px 0;'>
            <b>Important:</b> These recommendations are based on <i>your actual test results</i>.
            The guide has not calculated theoretical harmonics, but identified patterns in your data.
            Always verify with more testing before making a final choice.
        </div>
        """

        rec_label = QLabel(rec_html)
        rec_label.setWordWrap(True)
        layout.addWidget(rec_label)
        layout.addStretch()

        return widget

    def edit_test_data(self):
        """Åpner dialog for å redigere testdata"""
        QMessageBox.information(
            self,
            "Coming soon",
            "A dedicated test-data editor is coming soon.\n\n"
            "For now, edit directly in the database or add new tests.",
        )
