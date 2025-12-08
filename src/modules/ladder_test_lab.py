"""
Ladder Test Lab
Planlegging og analyse av ladder tests
"""

from datetime import datetime

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
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
)

from src.database.database import get_database
from src.modules.interactive_features import (
    InteractivePowderChargeSlider,
    InteractiveVelocityGraph,
)
from src.modules.live_visualization import LiveStatisticsDisplay


class LadderTestLab(QWidget):
    """Widget for Ladder Test planlegging og analyse"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_tests()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel("🧪 Ladder Test Lab")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel("Planlegg og analyser systematiske ladder tests")
        layout.addWidget(desc)

        # Knapper
        btn_layout = QHBoxLayout()
        new_test_btn = QPushButton("➕ Ny Ladder Test")
        new_test_btn.setMinimumHeight(40)
        new_test_btn.clicked.connect(self.new_ladder_test)
        btn_layout.addWidget(new_test_btn)

        view_btn = QPushButton("📊 Vis/Analyser")
        view_btn.setMinimumHeight(40)
        view_btn.clicked.connect(self.view_test)
        btn_layout.addWidget(view_btn)

        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_test)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.tests_table = QTableWidget()
        self.tests_table.setColumnCount(7)
        self.tests_table.setHorizontalHeaderLabels(
            [
                "Navn",
                "Dato",
                "Rifle",
                "Kaliber",
                "Ladning (gr)",
                "Avstand",
                "Resultater",
            ]
        )
        self.tests_table.horizontalHeader().setStretchLastSection(True)
        self.tests_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tests_table.doubleClicked.connect(self.view_test)
        layout.addWidget(self.tests_table)

    def load_tests(self):
        """Laster ladder tests fra database"""
        tests = self.db.get_all("ladder_tests", "date DESC")
        self.tests_table.setRowCount(len(tests))

        for i, test in enumerate(tests):
            self.tests_table.setItem(i, 0, QTableWidgetItem(test["name"]))
            self.tests_table.setItem(i, 1, QTableWidgetItem(test["date"]))

            # Rifle navn
            rifle_name = "-"
            if test["rifle_id"]:
                rifle = self.db.get_by_id("rifles", test["rifle_id"])
                if rifle:
                    rifle_name = rifle["name"]
            self.tests_table.setItem(i, 2, QTableWidgetItem(rifle_name))

            self.tests_table.setItem(i, 3, QTableWidgetItem(test["caliber"]))

            charge_range = f"{test['start_charge']}-{test['end_charge']}"
            self.tests_table.setItem(i, 4, QTableWidgetItem(charge_range))

            dist = f"{test['distance_meters']}m" if test["distance_meters"] else "-"
            self.tests_table.setItem(i, 5, QTableWidgetItem(dist))

            # Tell resultater
            results = self.db.execute_query(
                "SELECT COUNT(*) as count FROM test_results WHERE ladder_test_id = ?",
                (test["id"],),
            )
            result_count = results[0]["count"] if results else 0
            self.tests_table.setItem(i, 6, QTableWidgetItem(f"{result_count} steg"))

            self.tests_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, test["id"])

    def new_ladder_test(self):
        """Oppretter ny ladder test"""
        rifles = self.db.get_all("rifles")
        powders = self.db.get_all("powder")
        bullets = self.db.get_all("bullets")
        primers = self.db.get_all("primers")
        cases = self.db.get_all("cases")

        dialog = LadderTestDialog(
            self,
            rifles=rifles,
            powders=powders,
            bullets=bullets,
            primers=primers,
            cases=cases,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            test_id = self.db.insert("ladder_tests", data)
            self.load_tests()

            # Åpne resultat-input dialog
            QMessageBox.information(
                self,
                "Test opprettet",
                "Ladder test opprettet! Nå kan du legge inn resultater.",
            )
            self.open_results_dialog(test_id)

    def view_test(self):
        """Viser og analyserer valgt test"""
        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en test først!")
            return

        test_id = self.tests_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        self.open_analysis_window(test_id)

    def open_results_dialog(self, test_id):
        """Åpner dialog for å legge inn testresultater"""
        test = self.db.get_by_id("ladder_tests", test_id)
        dialog = TestResultsDialog(self, test)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            for result in results:
                result["ladder_test_id"] = test_id
                self.db.insert("test_results", result)
            self.load_tests()
            QMessageBox.information(self, "Suksess", "Resultater lagret!")

    def open_analysis_window(self, test_id):
        """Åpner analyse-vindu for test"""
        test = self.db.get_by_id("ladder_tests", test_id)
        results = self.db.execute_query(
            "SELECT * FROM test_results WHERE ladder_test_id = ? ORDER BY charge_weight",
            (test_id,),
        )

        dialog = AnalysisWindow(self, test, results)
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
            "Er du sikker på at du vil slette denne testen og alle resultater?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            test_id = self.tests_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            # Slett resultater først
            self.db.delete("test_results", "ladder_test_id = ?", (test_id,))
            # Slett test
            self.db.delete("ladder_tests", "id = ?", (test_id,))
            self.load_tests()
            QMessageBox.information(self, "Suksess", "Test slettet!")


class LadderTestDialog(QDialog):
    """Dialog for å opprette ladder test"""

    def __init__(
        self,
        parent=None,
        rifles=None,
        powders=None,
        bullets=None,
        primers=None,
        cases=None,
    ):
        super().__init__(parent)
        self.rifles = rifles or []
        self.powders = powders or []
        self.bullets = bullets or []
        self.primers = primers or []
        self.cases = cases or []
        self.init_ui()

    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle("Ny Ladder Test")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Grunninfo
        basic_group = QGroupBox("Test-informasjon")
        basic_layout = QFormLayout()
        basic_group.setLayout(basic_layout)

        self.name = QLineEdit()
        self.name.setPlaceholderText("F.eks. .308 Varget Ladder")
        basic_layout.addRow("Testnavn:", self.name)

        self.date = QLineEdit()
        self.date.setText(datetime.now().strftime("%Y-%m-%d"))
        basic_layout.addRow("Dato:", self.date)

        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem("-- Ingen rifle --", None)
        for rifle in self.rifles:
            self.rifle_combo.addItem(
                f"{rifle['name']} ({rifle['caliber']})", rifle["id"]
            )
        basic_layout.addRow("Rifle:", self.rifle_combo)

        self.caliber = QLineEdit()
        basic_layout.addRow("Kaliber:", self.caliber)

        layout.addWidget(basic_group)

        # Komponenter
        comp_group = QGroupBox("Komponenter")
        comp_layout = QFormLayout()
        comp_group.setLayout(comp_layout)

        self.bullet_combo = QComboBox()
        self.bullet_combo.addItem("-- Velg kule --", None)
        for bullet in self.bullets:
            self.bullet_combo.addItem(
                f"{bullet['name']} - {bullet['weight_grains']}gr", bullet["id"]
            )
        comp_layout.addRow("Kule:", self.bullet_combo)

        self.powder_combo = QComboBox()
        self.powder_combo.addItem("-- Velg krutt --", None)
        for powder in self.powders:
            self.powder_combo.addItem(powder["name"], powder["id"])
        comp_layout.addRow("Krutt:", self.powder_combo)

        self.primer_combo = QComboBox()
        self.primer_combo.addItem("-- Velg tennhette --", None)
        for primer in self.primers:
            self.primer_combo.addItem(primer["name"], primer["id"])
        comp_layout.addRow("Tennhette:", self.primer_combo)

        self.case_combo = QComboBox()
        self.case_combo.addItem("-- Velg hylse --", None)
        for case in self.cases:
            self.case_combo.addItem(f"{case['name']} - {case['caliber']}", case["id"])
        comp_layout.addRow("Hylse:", self.case_combo)

        layout.addWidget(comp_group)

        # Ladder test parametere
        ladder_group = QGroupBox("Ladder Test Parametere")
        ladder_layout = QFormLayout()
        ladder_group.setLayout(ladder_layout)

        self.start_charge = QDoubleSpinBox()
        self.start_charge.setRange(5, 100)
        self.start_charge.setDecimals(1)
        self.start_charge.setSingleStep(0.1)
        self.start_charge.setSuffix(" gr")
        self.start_charge.setValue(40.0)
        ladder_layout.addRow("Start ladning:", self.start_charge)

        self.end_charge = QDoubleSpinBox()
        self.end_charge.setRange(5, 100)
        self.end_charge.setDecimals(1)
        self.end_charge.setSingleStep(0.1)
        self.end_charge.setSuffix(" gr")
        self.end_charge.setValue(44.0)
        ladder_layout.addRow("Slutt ladning:", self.end_charge)

        self.step_size = QDoubleSpinBox()
        self.step_size.setRange(0.1, 5.0)
        self.step_size.setDecimals(1)
        self.step_size.setSingleStep(0.1)
        self.step_size.setSuffix(" gr")
        self.step_size.setValue(0.3)
        ladder_layout.addRow("Steg størrelse:", self.step_size)

        # Beregn antall steg
        steps_label = QLabel()
        self.start_charge.valueChanged.connect(lambda: self.update_steps(steps_label))
        self.end_charge.valueChanged.connect(lambda: self.update_steps(steps_label))
        self.step_size.valueChanged.connect(lambda: self.update_steps(steps_label))
        self.update_steps(steps_label)
        ladder_layout.addRow("Antall steg:", steps_label)

        layout.addWidget(ladder_group)

        # Test-parametere
        test_group = QGroupBox("Test-parametere")
        test_layout = QFormLayout()
        test_group.setLayout(test_layout)

        self.distance = QSpinBox()
        self.distance.setRange(25, 1000)
        self.distance.setValue(100)
        self.distance.setSuffix(" m")
        test_layout.addRow("Avstand:", self.distance)

        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(-30, 50)
        self.temperature.setValue(15)
        self.temperature.setSuffix(" °C")
        test_layout.addRow("Temperatur:", self.temperature)

        self.humidity = QSpinBox()
        self.humidity.setRange(0, 100)
        self.humidity.setValue(50)
        self.humidity.setSuffix(" %")
        test_layout.addRow("Luftfuktighet:", self.humidity)

        layout.addWidget(test_group)

        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Notater om testen...")
        layout.addWidget(QLabel("Notater:"))
        layout.addWidget(self.notes)

        # Knapper
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("✅ Opprett Test")
        create_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def update_steps(self, label):
        """Oppdaterer antall steg"""
        start = self.start_charge.value()
        end = self.end_charge.value()
        step = self.step_size.value()

        if step > 0 and end > start:
            steps = int((end - start) / step) + 1
            label.setText(f"<b>{steps} steg</b>")
        else:
            label.setText("<b>0 steg</b>")

    def get_data(self):
        """Returnerer test-data"""
        return {
            "name": self.name.text(),
            "date": self.date.text(),
            "rifle_id": self.rifle_combo.currentData(),
            "caliber": self.caliber.text(),
            "bullet_id": self.bullet_combo.currentData(),
            "powder_id": self.powder_combo.currentData(),
            "primer_id": self.primer_combo.currentData(),
            "case_id": self.case_combo.currentData(),
            "start_charge": self.start_charge.value(),
            "end_charge": self.end_charge.value(),
            "step_size": self.step_size.value(),
            "distance_meters": self.distance.value(),
            "temperature": self.temperature.value(),
            "humidity": self.humidity.value(),
            "notes": self.notes.toPlainText(),
        }


class TestResultsDialog(QDialog):
    """Dialog for å legge inn testresultater"""

    def __init__(self, parent=None, test=None):
        super().__init__(parent)
        self.test = test
        self.init_ui()

    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle(f"Resultater: {self.test['name']}")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Info
        info = QLabel(
            f"""
        <b>Test:</b> {self.test['name']}<br>
        <b>Ladning:</b> {self.test['start_charge']} - {self.test['end_charge']} gr
        (steg: {self.test['step_size']} gr)
        """
        )
        layout.addWidget(info)

        # Tabell
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels(
            [
                "Ladning (gr)",
                "V1 (fps)",
                "V2 (fps)",
                "V3 (fps)",
                "ES",
                "SD",
                "Gruppe (mm)",
                "Notater",
            ]
        )

        # Generer rader basert på ladder parametere
        start = self.test["start_charge"]
        end = self.test["end_charge"]
        step = self.test["step_size"]

        charges = []
        current = start
        while current <= end:
            charges.append(round(current, 1))
            current += step

        self.results_table.setRowCount(len(charges))

        for i, charge in enumerate(charges):
            # Ladning (read-only)
            charge_item = QTableWidgetItem(f"{charge}")
            charge_item.setFlags(charge_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            charge_item.setBackground(QColor(240, 240, 240))
            self.results_table.setItem(i, 0, charge_item)

            # Resten er editerbare
            for j in range(1, 8):
                self.results_table.setItem(i, j, QTableWidgetItem(""))

        layout.addWidget(self.results_table)

        # Tips
        tips = QLabel(
            """
        <b>Tips:</b> Fyll inn hastigheter (V1-V3). ES og SD beregnes automatisk når du klikker Lagre.<br>
        Gruppe = gruppestørrelse i mm. La felter være tomme hvis du ikke har data.
        """
        )
        tips.setWordWrap(True)
        layout.addWidget(tips)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre Resultater")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_results(self):
        """Henter resultater fra tabell"""
        results = []

        for i in range(self.results_table.rowCount()):
            charge = float(self.results_table.item(i, 0).text())

            # Les hastigheter
            v1 = self.get_cell_value(i, 1)
            v2 = self.get_cell_value(i, 2)
            v3 = self.get_cell_value(i, 3)

            # Beregn ES og SD
            velocities = [v for v in [v1, v2, v3] if v is not None]
            es = None
            sd = None
            avg = None

            if len(velocities) > 0:
                avg = sum(velocities) / len(velocities)

            if len(velocities) >= 2:
                es = max(velocities) - min(velocities)
                # Beregn SD
                mean = sum(velocities) / len(velocities)
                variance = sum((x - mean) ** 2 for x in velocities) / len(velocities)
                sd = variance**0.5

            group_size = self.get_cell_value(i, 6)
            notes = (
                self.results_table.item(i, 7).text()
                if self.results_table.item(i, 7)
                else ""
            )

            result = {
                "charge_weight": charge,
                "velocity_1": v1,
                "velocity_2": v2,
                "velocity_3": v3,
                "velocity_avg": avg,
                "velocity_es": es,
                "velocity_sd": sd,
                "group_size_mm": group_size,
                "notes": notes,
            }

            results.append(result)

        return results

    def get_cell_value(self, row, col):
        """Henter numerisk verdi fra celle"""
        item = self.results_table.item(row, col)
        if item and item.text():
            try:
                return float(item.text())
            except ValueError:
                return None
        return None


class AnalysisWindow(QDialog):
    """Analyse-vindu for ladder test"""

    def __init__(self, parent=None, test=None, results=None):
        super().__init__(parent)
        self.test = test
        self.results = results or []
        self.init_ui()

    def init_ui(self):
        """Initialiserer analyse-vindu"""
        self.setWindowTitle(f"Analyse: {self.test['name']}")
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Test info
        info = QLabel(
            f"""
        <h3>{self.test['name']}</h3>
        <b>Dato:</b> {self.test['date']} |
        <b>Avstand:</b> {self.test['distance_meters']}m |
        <b>Ladning:</b> {self.test['start_charge']}-{self.test['end_charge']} gr
        """
        )
        layout.addWidget(info)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 0: Live Testing (NEW!)
        tabs.addTab(self.create_live_testing_tab(), "🔴 Live Testing")

        # Tab 1: Datatabell
        tabs.addTab(self.create_data_tab(), "📊 Data")

        # Tab 2: Grafer
        tabs.addTab(self.create_graphs_tab(), "📈 Grafer")

        # Tab 3: Anbefaling
        tabs.addTab(self.create_recommendation_tab(), "🎯 Anbefaling")

        # Lukk-knapp
        close_btn = QPushButton("Lukk")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def create_live_testing_tab(self):
        """🔴 LIVE TESTING TAB - Real-time data entry with live graphs"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Info banner
        info_banner = QLabel(
            "🔴 <b>LIVE TESTING MODE</b> - Enter data as you shoot, see graphs update in real-time!"
        )
        info_banner.setStyleSheet(
            """
            background-color: #e74c3c;
            color: white;
            padding: 15px;
            font-size: 14px;
            border-radius: 5px;
        """
        )
        info_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_banner)

        # Main content: Input on left, Live graphs on right
        content_layout = QHBoxLayout()

        # LEFT PANEL: Data Entry
        left_panel = QGroupBox("📝 Data Entry")
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(400)

        # Current charge selector
        charge_layout = QHBoxLayout()
        charge_layout.addWidget(QLabel("Current Charge:"))

        self.live_charge_combo = QComboBox()
        start = self.test["start_charge"]
        end = self.test["end_charge"]
        step = self.test["step_size"]

        current = start
        while current <= end:
            self.live_charge_combo.addItem(f"{current:.1f} gr", current)
            current += step

        charge_layout.addWidget(self.live_charge_combo)
        left_layout.addLayout(charge_layout)

        # Velocity input
        vel_layout = QHBoxLayout()
        vel_layout.addWidget(QLabel("Velocity (fps):"))
        self.live_velocity_spin = QSpinBox()
        self.live_velocity_spin.setRange(500, 4000)
        self.live_velocity_spin.setValue(2700)
        vel_layout.addWidget(self.live_velocity_spin)
        left_layout.addLayout(vel_layout)

        # Add shot button
        self.btn_add_shot = QPushButton("➕ Add Shot")
        self.btn_add_shot.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 15px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """
        )
        self.btn_add_shot.clicked.connect(self.add_live_shot)
        left_layout.addWidget(self.btn_add_shot)

        # Live statistics
        self.live_stats = LiveStatisticsDisplay()
        left_layout.addWidget(self.live_stats)

        # Shot log
        log_label = QLabel("<b>Shot Log:</b>")
        left_layout.addWidget(log_label)

        self.live_shot_log = QTableWidget()
        self.live_shot_log.setColumnCount(3)
        self.live_shot_log.setHorizontalHeaderLabels(
            ["#", "Charge (gr)", "Velocity (fps)"]
        )
        self.live_shot_log.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.live_shot_log)

        # Clear button
        clear_btn = QPushButton("🗑️ Clear Data")
        clear_btn.clicked.connect(self.clear_live_data)
        left_layout.addWidget(clear_btn)

        left_layout.addStretch()
        content_layout.addWidget(left_panel)

        # RIGHT PANEL: Live Graphs
        right_panel = QGroupBox("📊 Live Visualization")
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        # Live velocity graph (with hover tooltips and click handlers)
        self.live_velocity_graph = InteractiveVelocityGraph(width=7, height=5)
        self.live_velocity_graph.point_clicked.connect(self.on_velocity_point_clicked)
        right_layout.addWidget(self.live_velocity_graph)

        # Interactive powder charge slider
        self.charge_slider = InteractivePowderChargeSlider()
        self.charge_slider.set_range(self.test["start_charge"], self.test["end_charge"])
        self.charge_slider.charge_changed.connect(self.on_slider_charge_changed)
        right_layout.addWidget(self.charge_slider)

        # Instructions
        instructions = QLabel(
            """
        <b>How to use:</b><br>
        1. Select charge weight<br>
        2. Enter velocity from chronograph<br>
        3. Click "Add Shot"<br>
        4. Watch graph update in real-time!<br>
        <br>
        <b>Interactive Features:</b><br>
        🖱️ <b>Hover</b> over data points for details<br>
        👆 <b>Click</b> data points to see full shot info<br>
        🎚️ <b>Slider</b> to estimate velocity at any charge<br>
        ⭐ Automatic node detection (pressure sweet spots)<br>
        📈 Live trend line<br>
        📊 Real-time SD/ES calculation
        """
        )
        instructions.setStyleSheet(
            "background-color: #ecf0f1; padding: 10px; border-radius: 5px;"
        )
        instructions.setWordWrap(True)
        right_layout.addWidget(instructions)

        content_layout.addWidget(right_panel)
        layout.addLayout(content_layout)

        # Initialize shot counter
        self.shot_counter = 0

        return widget

    def add_live_shot(self):
        """Add shot to live testing"""
        charge = self.live_charge_combo.currentData()
        velocity = self.live_velocity_spin.value()

        # Get current statistics for metadata
        current_stats = self.live_stats.get_statistics()

        # Build metadata for hover tooltip
        metadata = {
            "shot_number": self.shot_counter + 1,
            "es": current_stats.get("es"),
            "sd": current_stats.get("sd"),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

        # Add to graph with metadata
        self.live_velocity_graph.add_point(charge, velocity, metadata)

        # Add to statistics
        self.live_stats.add_value(velocity)

        # Add to log
        self.shot_counter += 1
        row = self.live_shot_log.rowCount()
        self.live_shot_log.insertRow(row)

        self.live_shot_log.setItem(row, 0, QTableWidgetItem(f"{self.shot_counter}"))
        self.live_shot_log.setItem(row, 1, QTableWidgetItem(f"{charge:.1f}"))
        self.live_shot_log.setItem(row, 2, QTableWidgetItem(f"{velocity}"))

        # Auto-scroll to bottom
        self.live_shot_log.scrollToBottom()

        # Give feedback
        self.live_velocity_spin.selectAll()

        # Auto-save state (if state_manager is available)
        if hasattr(self, "state_manager") and self.state_manager:
            self.save_live_test_state()

    def save_live_test_state(self):
        """Save current live testing state"""
        if not hasattr(self, "state_manager") or not self.state_manager:
            return

        # Collect shot data
        shots = []
        for row in range(self.live_shot_log.rowCount()):
            charge = float(self.live_shot_log.item(row, 1).text())
            velocity = int(self.live_shot_log.item(row, 2).text())
            shots.append({"charge": charge, "velocity": velocity})

        # Save state
        state_data = {
            "test_name": self.test["name"],
            "test_id": self.test["id"],
            "rifle": self.test.get("rifle_name", "Unknown"),
            "caliber": self.test.get("caliber", ""),
            "shots": shots,
            "shot_count": self.shot_counter,
            "charge_range": [self.test["start_charge"], self.test["end_charge"]],
            "last_charge": self.live_charge_combo.currentData(),
            "last_velocity": self.live_velocity_spin.value(),
        }

        self.state_manager.save_state(
            f"ladder_test_{self.test['id']}",
            f"Ladder Test: {self.test['name']}",
            state_data,
        )

    def restore_live_test_state(self, state_data):
        """Restore live testing state"""
        if "shots" in state_data:
            self.shot_counter = 0
            for shot in state_data["shots"]:
                # Add to graph
                self.live_velocity_graph.add_point(shot["charge"], shot["velocity"])

                # Add to statistics
                self.live_stats.add_value(shot["velocity"])

                # Add to log
                self.shot_counter += 1
                row = self.live_shot_log.rowCount()
                self.live_shot_log.insertRow(row)

                self.live_shot_log.setItem(
                    row, 0, QTableWidgetItem(f"{self.shot_counter}")
                )
                self.live_shot_log.setItem(
                    row, 1, QTableWidgetItem(f"{shot['charge']:.1f}")
                )
                self.live_shot_log.setItem(
                    row, 2, QTableWidgetItem(f"{shot['velocity']}")
                )

        if "last_charge" in state_data:
            # Find and select the charge in combo
            for i in range(self.live_charge_combo.count()):
                if (
                    abs(self.live_charge_combo.itemData(i) - state_data["last_charge"])
                    < 0.01
                ):
                    self.live_charge_combo.setCurrentIndex(i)
                    break

        if "last_velocity" in state_data:
            self.live_velocity_spin.setValue(state_data["last_velocity"])

    def clear_live_data(self):
        """Clear live testing data"""
        reply = QMessageBox.question(
            self,
            "Clear Data?",
            "This will clear all live testing data. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.live_velocity_graph.clear_data()
            self.live_stats.clear_data()
            self.live_shot_log.setRowCount(0)
            self.shot_counter = 0

    def on_velocity_point_clicked(self, charge: float, velocity: float, metadata: dict):
        """Handle click on velocity data point"""
        shot_num = metadata.get("shot_number", "?")
        es = metadata.get("es", "N/A")
        sd = metadata.get("sd", "N/A")

        es_str = f"{es:.0f} fps" if isinstance(es, (int, float)) else es
        sd_str = f"{sd:.1f} fps" if isinstance(sd, (int, float)) else sd

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Shot Details")
        msg.setText(f"<h3>Shot #{shot_num}</h3>")
        msg.setInformativeText(
            f"""
        <b>Charge:</b> {charge:.1f} gr<br>
        <b>Velocity:</b> {velocity} fps<br>
        <b>ES:</b> {es_str}<br>
        <b>SD:</b> {sd_str}<br>
        """
        )

        # Add "Go to this charge" button
        btn_goto = msg.addButton("Go to this charge", QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Close)

        msg.exec()

        if msg.clickedButton() == btn_goto:
            # Set combo to this charge
            for i in range(self.live_charge_combo.count()):
                if abs(self.live_charge_combo.itemData(i) - charge) < 0.01:
                    self.live_charge_combo.setCurrentIndex(i)
                    break

    def on_slider_charge_changed(self, charge: float):
        """Handle charge slider movement - update live predictions"""
        # This would integrate with ballistics model for real predictions
        # For now, just highlight the charge in the combo if it exists
        for i in range(self.live_charge_combo.count()):
            if abs(self.live_charge_combo.itemData(i) - charge) < 0.01:
                # Could highlight this charge somehow
                pass

    def create_data_tab(self):
        """Oppretter data-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["Ladning", "Snitt V", "ES", "SD", "Gruppe (mm)", "Gruppe (MOA)", "Notater"]
        )

        table.setRowCount(len(self.results))

        for i, result in enumerate(self.results):
            table.setItem(i, 0, QTableWidgetItem(f"{result['charge_weight']} gr"))

            avg = f"{result['velocity_avg']:.0f}" if result["velocity_avg"] else "-"
            table.setItem(i, 1, QTableWidgetItem(avg))

            es = f"{result['velocity_es']:.0f}" if result["velocity_es"] else "-"
            table.setItem(i, 2, QTableWidgetItem(es))

            sd = f"{result['velocity_sd']:.1f}" if result["velocity_sd"] else "-"
            table.setItem(i, 3, QTableWidgetItem(sd))

            group_mm = (
                f"{result['group_size_mm']:.1f}" if result["group_size_mm"] else "-"
            )
            table.setItem(i, 4, QTableWidgetItem(group_mm))

            # Beregn MOA
            if result["group_size_mm"] and self.test["distance_meters"]:
                moa = (
                    (result["group_size_mm"] / 10)
                    / (self.test["distance_meters"] / 100)
                    / 2.908
                )
                table.setItem(i, 5, QTableWidgetItem(f"{moa:.2f}"))
            else:
                table.setItem(i, 5, QTableWidgetItem("-"))

            notes = result["notes"] if result["notes"] else ""
            table.setItem(i, 6, QTableWidgetItem(notes))

        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        return widget

    def create_graphs_tab(self):
        """Oppretter graf-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Matplotlib figure
        fig = Figure(figsize=(10, 8))
        canvas = FigureCanvas(fig)

        # Hent data
        _charges = [r["charge_weight"] for r in self.results]
        velocities = [r["velocity_avg"] for r in self.results if r["velocity_avg"]]
        es_values = [r["velocity_es"] for r in self.results if r["velocity_es"]]
        sd_values = [r["velocity_sd"] for r in self.results if r["velocity_sd"]]
        groups = [r["group_size_mm"] for r in self.results if r["group_size_mm"]]

        charges_v = [r["charge_weight"] for r in self.results if r["velocity_avg"]]
        charges_es = [r["charge_weight"] for r in self.results if r["velocity_es"]]
        charges_sd = [r["charge_weight"] for r in self.results if r["velocity_sd"]]
        charges_g = [r["charge_weight"] for r in self.results if r["group_size_mm"]]

        # Plot 1: Hastighet
        ax1 = fig.add_subplot(2, 2, 1)
        if velocities:
            ax1.plot(charges_v, velocities, "bo-", linewidth=2, markersize=8)
            ax1.set_xlabel("Ladning (gr)")
            ax1.set_ylabel("Hastighet (fps)")
            ax1.set_title("Hastighet vs Ladning")
            ax1.grid(True, alpha=0.3)

        # Plot 2: ES
        ax2 = fig.add_subplot(2, 2, 2)
        if es_values:
            ax2.plot(charges_es, es_values, "ro-", linewidth=2, markersize=8)
            ax2.set_xlabel("Ladning (gr)")
            ax2.set_ylabel("ES (fps)")
            ax2.set_title("Extreme Spread vs Ladning")
            ax2.grid(True, alpha=0.3)

        # Plot 3: SD
        ax3 = fig.add_subplot(2, 2, 3)
        if sd_values:
            ax3.plot(charges_sd, sd_values, "go-", linewidth=2, markersize=8)
            ax3.set_xlabel("Ladning (gr)")
            ax3.set_ylabel("SD (fps)")
            ax3.set_title("Standard Deviation vs Ladning")
            ax3.grid(True, alpha=0.3)

        # Plot 4: Gruppestørrelse
        ax4 = fig.add_subplot(2, 2, 4)
        if groups:
            ax4.plot(charges_g, groups, "mo-", linewidth=2, markersize=8)
            ax4.set_xlabel("Ladning (gr)")
            ax4.set_ylabel("Gruppestørrelse (mm)")
            ax4.set_title("Gruppestørrelse vs Ladning")
            ax4.grid(True, alpha=0.3)

        fig.tight_layout()

        layout.addWidget(canvas)

        return widget

    def create_recommendation_tab(self):
        """Oppretter anbefalings-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Finn beste ladning basert på SD og gruppestørrelse
        best_sd = None
        best_group = None

        for result in self.results:
            if result["velocity_sd"]:
                if (
                    best_sd is None
                    or result["velocity_sd"] < self.results[best_sd]["velocity_sd"]
                ):
                    best_sd = self.results.index(result)

            if result["group_size_mm"]:
                if (
                    best_group is None
                    or result["group_size_mm"]
                    < self.results[best_group]["group_size_mm"]
                ):
                    best_group = self.results.index(result)

        recommendation = QLabel()
        rec_text = "<h3>🎯 Anbefalinger:</h3>"

        if best_sd is not None:
            r = self.results[best_sd]
            rec_text += f"""
            <p><b>Beste konsistens (laveste SD):</b><br>
            Ladning: <b>{r['charge_weight']} gr</b><br>
            SD: {r['velocity_sd']:.1f} fps<br>
            ES: {r['velocity_es']:.0f} fps<br>
            Snitt hastighet: {r['velocity_avg']:.0f} fps</p>
            """

        if best_group is not None:
            r = self.results[best_group]
            moa = (
                (r["group_size_mm"] / 10) / (self.test["distance_meters"] / 100) / 2.908
                if self.test["distance_meters"]
                else 0
            )
            rec_text += f"""
            <p><b>Beste presisjon (minste gruppe):</b><br>
            Ladning: <b>{r['charge_weight']} gr</b><br>
            Gruppestørrelse: {r['group_size_mm']:.1f} mm ({moa:.2f} MOA)<br>
            SD: {r['velocity_sd']:.1f if r['velocity_sd'] else '-'} fps</p>
            """

        rec_text += """
        <hr>
        <p><b>Neste skritt:</b></p>
        <ul>
            <li>Test ladningen med flere skudd (5-10 stk)</li>
            <li>Verifiser på lengre hold</li>
            <li>Sjekk for trykkegn</li>
            <li>Test i ulike værforhold</li>
        </ul>
        """

        recommendation.setText(rec_text)
        recommendation.setWordWrap(True)
        layout.addWidget(recommendation)
        layout.addStretch()

        return widget
