"""
Harmonic Wizard - Settedybde og harmonikkanalyse
AI-assistert analyse av settedybde vs presisjon for å finne harmoniske noder
"""

from datetime import datetime

import numpy as np
from src.utils.optional_deps import Figure as Figure, FigureCanvas as FigureCanvas
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

from src.database.database import get_database


class HarmonicWizard(QWidget):
    """Hovedwidget for Harmonic Wizard"""

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
        title = QLabel("🎯 Harmonic Wizard - Settedybde Assistent")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        disclaimer = QLabel(
            """
        <b style='color: #d9534f;'>⚠️ VIKTIG:</b> Dette verktøyet analyserer <i>dine faktiske testresultater</i>
        og foreslår settedybder som har høy sannsynlighet for god presisjon.
        Det beregner IKKE teoretisk harmonikk - det lærer av dine skudd.<br>
        <b>Du har alltid ansvar for sikker lading innenfor ladebokens grenser.</b>
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

        # Knapper
        btn_layout = QHBoxLayout()

        new_test_btn = QPushButton("🆕 Ny Settedybde-test")
        new_test_btn.setMinimumHeight(40)
        new_test_btn.setStyleSheet(
            "background-color: #5cb85c; color: white; font-weight: bold;"
        )
        new_test_btn.clicked.connect(self.start_new_test)
        btn_layout.addWidget(new_test_btn)

        analyze_btn = QPushButton("📊 Analyser Test")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.analyze_test)
        btn_layout.addWidget(analyze_btn)

        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_test)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Info
        info = QLabel(
            """
        <h3>Hvordan det fungerer:</h3>
        <ol>
            <li><b>Opprett test:</b> Definer løpsprofil, kule, og settedybder å teste</li>
            <li><b>Skyt testen:</b> 3-5 skudd per settedybde, legg inn gruppestørrelse og ES/SD</li>
            <li><b>Analyser:</b> AI finner "harmoniske noder" - områder der presisjon er stabil</li>
            <li><b>Forfin:</b> Test anbefalt område med finjustering (±0.05mm)</li>
        </ol>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tabell med tester
        self.tests_table = QTableWidget()
        self.tests_table.setColumnCount(7)
        self.tests_table.setHorizontalHeaderLabels(
            ["Navn", "Dato", "Rifle", "Kule", "Krutt", "Testpunkter", "Status"]
        )
        self.tests_table.horizontalHeader().setStretchLastSection(True)
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
            self.tests_table.setItem(i, 5, QTableWidgetItem(f"{count} punkter"))

            # Status
            status = "✅ Ferdig" if count >= 3 else "⏳ Ikke ferdig"
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
        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en test først!")
            return

        test_id = self.tests_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)

        # Hent test og resultater
        test = self.db.execute_query(
            "SELECT * FROM seating_depth_tests WHERE id = ?", (test_id,)
        )[0]

        results = self.db.execute_query(
            "SELECT * FROM seating_depth_results WHERE test_id = ? ORDER BY coal",
            (test_id,),
        )

        if len(results) < 3:
            QMessageBox.warning(
                self,
                "For lite data",
                "Du trenger minst 3 testpunkter for å kjøre analyse!",
            )
            return

        # Åpne analyse-vindu
        dialog = HarmonicAnalysisDialog(self, test, results)
        dialog.exec()

    def delete_test(self):
        """Sletter valgt test"""
        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en test først!")
            return

        reply = QMessageBox.question(
            self,
            "Bekreft sletting",
            "Er du sikker på at du vil slette denne testen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            test_id = self.tests_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete("seating_depth_results", "test_id = ?", (test_id,))
            self.db.delete("seating_depth_tests", "id = ?", (test_id,))
            self.load_tests()


class SeatingDepthWizard(QWizard):
    """Wizard for å sette opp settedybde-test"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.setWindowTitle("Ny Settedybde-test - Oppsett")
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
                "Test opprettet!",
                f"Settedybde-test opprettet med {len(coal_values)} testpunkter!\n\n"
                f"Nå kan du skyte testen og legge inn resultater.",
            )


class BarrelProfilePage(QWizardPage):
    """Side 1: Løpsinformasjon"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Steg 1: Løpsprofil og konfigurasjon")
        self.setSubTitle(
            "Angi løpets fysiske egenskaper. Dette brukes for å forbedre "
            "AI-modellens forståelse av ditt våpens dynamikk."
        )

        self.db = get_database()
        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Rifle
        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem("-- Velg rifle --", None)
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
        form.addRow("Løpslengde:", self.barrel_length)

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
        form.addRow("Løpskontur:", self.barrel_contour)

        layout.addLayout(form)

        # Munningsmiddel
        muzzle_group = QGroupBox("Munningsmiddel (Demper/Brems)")
        muzzle_layout = QFormLayout()
        muzzle_group.setLayout(muzzle_layout)

        self.muzzle_device = QComboBox()
        self.muzzle_device.addItems(
            [
                "Ingen",
                "Muzzle Brake",
                "Suppressor (Liten)",
                "Suppressor (Mellom)",
                "Suppressor (Tung)",
            ]
        )
        muzzle_layout.addRow("Type:", self.muzzle_device)

        self.muzzle_weight = QSpinBox()
        self.muzzle_weight.setRange(0, 1000)
        self.muzzle_weight.setValue(0)
        self.muzzle_weight.setSuffix(" g")
        muzzle_layout.addRow("Vekt (ca):", self.muzzle_weight)

        layout.addWidget(muzzle_group)

        # Registrer felt
        self.registerField("rifle_id", self.rifle_combo, "currentData")
        self.registerField("barrel_length", self.barrel_length)
        self.registerField("barrel_contour", self.barrel_contour, "currentText")
        self.registerField("muzzle_device", self.muzzle_device, "currentText")
        self.registerField("muzzle_weight", self.muzzle_weight)


class ComponentsPage(QWizardPage):
    """Side 2: Komponenter"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Steg 2: Ammunisjonskomponenter")
        self.setSubTitle("Velg de komponentene du bruker i denne testen")

        self.db = get_database()
        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Kule
        self.bullet_combo = QComboBox()
        self.bullet_combo.addItem("-- Velg kule --", None)
        bullets = self.db.get_all("bullets")
        for bullet in bullets:
            self.bullet_combo.addItem(
                f"{bullet['name']} - {bullet['weight_grains']}gr", bullet["id"]
            )
        form.addRow("Kule:", self.bullet_combo)

        # Krutt
        self.powder_combo = QComboBox()
        self.powder_combo.addItem("-- Velg krutt --", None)
        powders = self.db.get_all("powder")
        for powder in powders:
            self.powder_combo.addItem(powder["name"], powder["id"])
        form.addRow("Krutt:", self.powder_combo)

        # Kruttvekt
        self.powder_charge = QDoubleSpinBox()
        self.powder_charge.setRange(10, 100)
        self.powder_charge.setDecimals(1)
        self.powder_charge.setSuffix(" gr")
        form.addRow("Kruttvekt:", self.powder_charge)

        # Tennhette
        self.primer_combo = QComboBox()
        self.primer_combo.addItem("-- Velg tennhette --", None)
        primers = self.db.get_all("primers")
        for primer in primers:
            self.primer_combo.addItem(primer["name"], primer["id"])
        form.addRow("Tennhette:", self.primer_combo)

        # Hylse
        self.case_combo = QComboBox()
        self.case_combo.addItem("-- Velg hylse --", None)
        cases = self.db.get_all("cases")
        for case in cases:
            self.case_combo.addItem(f"{case['name']} - {case['caliber']}", case["id"])
        form.addRow("Hylse:", self.case_combo)

        layout.addLayout(form)

        # Registrer felt
        self.registerField("bullet_id*", self.bullet_combo, "currentData")
        self.registerField("powder_id*", self.powder_combo, "currentData")
        self.registerField("powder_charge", self.powder_charge)
        self.registerField("primer_id", self.primer_combo, "currentData")
        self.registerField("case_id", self.case_combo, "currentData")


class TestSetupPage(QWizardPage):
    """Side 3: Test-oppsett"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Steg 3: Definer testområde")
        self.setSubTitle(
            "Angi COAL-område du vil teste. Tips: Start med 0.2-0.3mm steg, "
            "forfin senere i lovende områder."
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Testnavn
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Testnavn:"))
        self.test_name = QLineEdit()
        self.test_name.setPlaceholderText("F.eks. 6.5CM ELD-M Settedybde #1")
        name_layout.addWidget(self.test_name)
        layout.addLayout(name_layout)

        # COAL-område
        coal_group = QGroupBox("COAL-område (Cartridge Overall Length)")
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
        coal_layout.addRow("Slutt COAL:", self.end_coal)

        self.coal_step = QDoubleSpinBox()
        self.coal_step.setRange(0.05, 1.0)
        self.coal_step.setDecimals(2)
        self.coal_step.setValue(0.20)
        self.coal_step.setSuffix(" mm")
        coal_layout.addRow("Steg-størrelse:", self.coal_step)

        # Antall testpunkter
        self.test_points_label = QLabel()
        self.update_test_points()
        coal_layout.addRow("Antall testpunkter:", self.test_points_label)

        self.start_coal.valueChanged.connect(self.update_test_points)
        self.end_coal.valueChanged.connect(self.update_test_points)
        self.coal_step.valueChanged.connect(self.update_test_points)

        layout.addWidget(coal_group)

        # Test-parametere
        test_group = QGroupBox("Test-parametere")
        test_layout = QFormLayout()
        test_group.setLayout(test_layout)

        self.rounds_per_coal = QSpinBox()
        self.rounds_per_coal.setRange(3, 10)
        self.rounds_per_coal.setValue(3)
        self.rounds_per_coal.setSuffix(" skudd")
        test_layout.addRow("Skudd per COAL:", self.rounds_per_coal)

        self.distance = QSpinBox()
        self.distance.setRange(50, 500)
        self.distance.setValue(100)
        self.distance.setSuffix(" m")
        test_layout.addRow("Testdistanse:", self.distance)

        layout.addWidget(test_group)

        # Notater
        layout.addWidget(QLabel("Notater:"))
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Ekstra notater om testen...")
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
                f"<b>{points} punkter</b> = <b>{total_rounds} patroner</b> totalt"
            )
        else:
            self.test_points_label.setText("<b>0 punkter</b>")


class SummaryPage(QWizardPage):
    """Side 4: Oppsummering"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Steg 4: Oppsummering")
        self.setSubTitle("Sjekk at alt er riktig før du oppretter testen")

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

        <h4>Løpsprofil:</h4>
        <ul>
            <li>Lengde: {wizard.field('barrel_length')} cm</li>
            <li>Kontur: {wizard.field('barrel_contour')}</li>
            <li>Munningsmiddel: {wizard.field('muzzle_device')} ({wizard.field('muzzle_weight')} g)</li>
        </ul>

        <h4>Testområde:</h4>
        <ul>
            <li>COAL: {start} - {end} mm (steg: {step} mm)</li>
            <li><b>{points} testpunkter</b></li>
            <li>{wizard.field('rounds_per_coal')} skudd per punkt</li>
            <li><b>Totalt: {total_rounds} patroner</b></li>
            <li>Avstand: {wizard.field('distance')} m</li>
        </ul>

        <p style='color: #5cb85c; font-weight: bold;'>
        ✅ Klar til å opprette test! Etter opprettelse kan du legge inn resultater etter hvert som du skyter.
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
        title = QLabel(f"<h2>📊 {self.test['name']}</h2>")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Data & input
        tabs.addTab(self.create_data_tab(), "📝 Testdata")

        # Tab 2: Graf & analyse
        tabs.addTab(self.create_analysis_tab(), "📈 AI-Analyse")

        # Tab 3: Anbefaling
        tabs.addTab(self.create_recommendation_tab(), "🎯 Anbefalinger")

        # Lukk-knapp
        close_btn = QPushButton("Lukk")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def create_data_tab(self):
        """Oppretter data-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            f"""
        <b>Test:</b> {self.test['name']}<br>
        <b>Dato:</b> {self.test['date']}<br>
        <b>Avstand:</b> {self.test['distance_meters']}m
        """
        )
        layout.addWidget(info)

        # Tabell med resultater
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["COAL (mm)", "Gruppe (mm)", "Snitt V (fps)", "ES", "SD", "Notater"]
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

        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        # Knapp for å oppdatere data
        update_btn = QPushButton("✏️ Rediger testdata")
        update_btn.clicked.connect(self.edit_test_data)
        layout.addWidget(update_btn)

        return widget

    def create_analysis_tab(self):
        """Oppretter analyse-tab med grafer"""
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
                QLabel(
                    "⚠️ For lite data for å kjøre analyse. Legg inn flere resultater."
                )
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
        ax1.set_ylabel("Gruppestørrelse (mm)", fontsize=11)
        ax1.set_title("Gruppestørrelse vs Settedybde", fontsize=12, fontweight="bold")
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
                "Hastighets-konsistens vs Settedybde", fontsize=12, fontweight="bold"
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
            label="Presisjon (normalisert)",
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
                    label="Potensielle noder",
                )

        ax3.set_xlabel("COAL (mm)", fontsize=11)
        ax3.set_ylabel("Presisjonsscore (høyere = bedre)", fontsize=11)
        ax3.set_title(
            'AI-identifiserte "Harmoniske Noder"', fontsize=12, fontweight="bold"
        )
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(-0.1, 1.1)

        fig.tight_layout()
        layout.addWidget(canvas)

        return widget

    def create_recommendation_tab(self):
        """Oppretter anbefalings-tab"""
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
            layout.addWidget(QLabel("⚠️ For lite data for anbefalinger"))
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
        rec_html = "<h2>🎯 AI-Anbefalinger</h2>"

        rec_html += f"""
        <div style='background-color: #d4edda; border: 2px solid #28a745; border-radius: 5px; padding: 15px; margin: 10px 0;'>
            <h3 style='color: #155724;'>✅ Beste presisjon observert:</h3>
            <p style='font-size: 14pt;'>
                <b>COAL: {best_coal:.2f} mm</b><br>
                Gruppestørrelse: {best_group:.1f} mm
            </p>
        </div>
        """

        if len(peaks) > 0:
            rec_html += "<h3>🔍 Identifiserte harmoniske noder:</h3><ul>"

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
                    (Gruppe: {peak_group:.1f} mm, Score: {score:.2f})</li>
                """

            rec_html += "</ul>"
        else:
            rec_html += (
                "<p>⚠️ Ingen tydelige harmoniske noder funnet. Dette kan bety:</p><ul>"
            )
            rec_html += "<li>For få testpunkter</li>"
            rec_html += "<li>For stort steg mellom COAL-verdier</li>"
            rec_html += (
                "<li>Våpenet er ikke følsomt for settedybde i dette området</li></ul>"
            )

        # Neste steg
        rec_html += f"""
        <hr>
        <h3>📋 Anbefalte neste steg:</h3>
        <ol>
            <li><b>Forfin beste område:</b> Test COAL {best_coal-0.10:.2f} - {best_coal+0.10:.2f} mm
                med 0.05mm steg (5 punkter)</li>
            <li><b>Øk antall skudd:</b> Skyt 5-10 skudd per COAL for bedre statistikk</li>
            <li><b>Verifiser på lengre hold:</b> Test beste COAL på {self.test['distance_meters']*2}m</li>
            <li><b>Sjekk robusthet:</b> Test i ulike værforhold og temperaturer</li>
        </ol>

        <div style='background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 5px; padding: 10px; margin: 10px 0;'>
            <b>⚠️ Viktig:</b> Disse anbefalingene er basert på <i>dine faktiske testresultater</i>.
            AI har ikke beregnet teoretisk harmonikk, men identifisert mønstre i dataene dine.
            Alltid verifiser med videre testing før du tar endelig valg.
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
            "Funksjon kommer",
            "Funksjon for å redigere testdata kommer snart!\n\n"
            "Foreløpig kan du redigere direkte i databasen eller legge til nye tester.",
        )
