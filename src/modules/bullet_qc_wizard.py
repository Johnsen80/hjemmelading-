"""
Bullet Quality Control & Measurement System
Measure length, weight, ogive variations across sample size
Find average, SD, ES - sort bullets into match-grade vs practice batches!

Simple wizard with step-by-step guidance! 🎯
"""

import statistics
from typing import Dict, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from src.logging_config import get_logger

logger = get_logger(__name__)


class QCHistoryDialog(QDialog):
    """Show QC history for a bullet across different lots"""

    def __init__(self, bullet_name: str, history: List[Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"📊 QC History: {bullet_name}")
        self.resize(900, 600)
        self.bullet_name = bullet_name
        self.history = history
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel(
            f"<h2>📊 Quality Control History</h2><p><b>{self.bullet_name}</b></p>"
        )
        layout.addWidget(title)

        info = QLabel(
            f"Compare measurements across {len(self.history)} different lot numbers.<br>"
            "See which lots are most consistent!"
        )
        info.setStyleSheet(
            "background-color: #e8f4f8; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        # History table
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(
            [
                "Date",
                "Lot Number",
                "Sample Size",
                "Weight Avg",
                "Weight SD",
                "Ogive Avg",
                "Ogive SD",
                "Quality",
            ]
        )

        table.setRowCount(len(self.history))

        for i, record in enumerate(self.history):
            stats = record.get("statistics", {})

            table.setItem(i, 0, QTableWidgetItem(record.get("date", "Unknown")))
            table.setItem(i, 1, QTableWidgetItem(record.get("lot_number", "Unknown")))
            table.setItem(i, 2, QTableWidgetItem(str(stats.get("sample_size", 0))))
            table.setItem(
                i, 3, QTableWidgetItem(f"{stats.get('weight_avg', 0):.2f} gr")
            )
            table.setItem(i, 4, QTableWidgetItem(f"{stats.get('weight_sd', 0):.3f} gr"))
            table.setItem(i, 5, QTableWidgetItem(f"{stats.get('ogive_avg', 0):.4f}\""))

            ogive_sd = stats.get("ogive_sd", 0)
            ogive_item = QTableWidgetItem(f'{ogive_sd:.4f}"')

            # Color code by ogive SD
            if ogive_sd < 0.001:
                ogive_item.setBackground(QColor("#d5f4e6"))
                quality = "★★★★★ Excellent"
            elif ogive_sd < 0.002:
                ogive_item.setBackground(QColor("#fff9c4"))
                quality = "★★★★☆ Very Good"
            elif ogive_sd < 0.003:
                ogive_item.setBackground(QColor("#ffe0b2"))
                quality = "★★★☆☆ Good"
            else:
                ogive_item.setBackground(QColor("#ffcccc"))
                quality = "★★☆☆☆ Fair"

            table.setItem(i, 6, ogive_item)
            table.setItem(i, 7, QTableWidgetItem(quality))

        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Best/worst lots
        if len(self.history) > 1:
            best_lot = min(
                self.history, key=lambda x: x["statistics"].get("ogive_sd", 999)
            )
            worst_lot = max(
                self.history, key=lambda x: x["statistics"].get("ogive_sd", 0)
            )

            summary = QLabel(
                f"<b>🏆 Best Lot:</b> {best_lot.get('lot_number', 'Unknown')} "
                f"(Ogive SD: {best_lot['statistics'].get('ogive_sd', 0):.4f}\")<br>"
                f"<b>⚠️ Worst Lot:</b> {worst_lot.get('lot_number', 'Unknown')} "
                f"(Ogive SD: {worst_lot['statistics'].get('ogive_sd', 0):.4f}\")"
            )
            summary.setStyleSheet(
                "background-color: #d5f4e6; padding: 15px; border-radius: 5px; margin-top: 10px;"
            )
            layout.addWidget(summary)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class BulletQCWizard(QWizard):
    """
    Step-by-step wizard for bullet quality control
    Measure length, weight, ogive - find best bullets!
    """

    measurement_complete = pyqtSignal(dict)  # Emit results

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Bullet Quality Control Wizard")
        self.resize(800, 600)

        # Add pages
        self.intro_page = IntroPage()
        self.setup_page = SetupPage()
        self.measurement_page = MeasurementPage()
        self.results_page = ResultsPage()

        self.addPage(self.intro_page)
        self.addPage(self.setup_page)
        self.addPage(self.measurement_page)
        self.addPage(self.results_page)

        # Style
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)

        # Connect signals
        self.measurement_page.measurements_changed.connect(self.on_measurements_changed)
        self.finished.connect(self.on_wizard_finished)

    def on_measurements_changed(self, measurements: Dict):
        """Update results page when measurements change"""
        self.results_page.update_results(measurements)

    def on_wizard_finished(self, result):
        """Emit final results and save to history"""
        if result == QDialog.DialogCode.Accepted:
            results = self.results_page.get_final_results()

            if results.get("completed"):
                # Save to QC history
                self.save_qc_history(results)

            self.measurement_complete.emit(results)

    def save_qc_history(self, results: Dict):
        """Save QC measurements to history file"""
        import json
        import os
        from datetime import datetime

        history_file = "data/qc_history.json"

        # Load existing history
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    all_history = json.load(f)
            except Exception as e:
                logger.debug(
                    "Failed to load QC history file, starting fresh: %s",
                    e,
                    exc_info=True,
                )
                try:
                    from HjemmeladingApp.utils.safe_logger import append_exception

                    append_exception("Failed to load QC history file", e)
                except Exception:
                    pass
                all_history = {}
        else:
            all_history = {}

        # Get bullet and lot info
        bullet_name = self.setup_page.get_bullet_name()
        lot_number = self.field("lot_number")

        # Create record
        record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "lot_number": lot_number,
            "statistics": results.get("statistics", {}),
            "measurements": results.get("measurements", {}),
        }

        # Add to history for this bullet
        if bullet_name not in all_history:
            all_history[bullet_name] = []

        all_history[bullet_name].append(record)

        # Save
        os.makedirs("data", exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(all_history, f, indent=2, ensure_ascii=False)

        logger.info("Saved QC data for %s, lot %s", bullet_name, lot_number)


class IntroPage(QWizardPage):
    """Introduction and explanation"""

    def __init__(self):
        super().__init__()
        self.setTitle("🎯 Welcome to Bullet Quality Control")
        self.setSubTitle(
            "Measure your bullets to find the best ones for match shooting!"
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        info_html = """
        <div style='font-size: 14px; line-height: 1.6;'>
        <h3 style='color: #2c3e50;'>Why Measure Bullets?</h3>
        <p>Even premium match bullets have small variations:</p>
        <ul>
            <li><b>Weight:</b> ±0.1-0.3 gr variation (affects velocity consistency)</li>
            <li><b>Length:</b> ±0.001-0.005" variation (base to tip)</li>
            <li><b>Ogive:</b> ±0.001-0.003" variation (base to ogive - MOST IMPORTANT!)</li>
        </ul>

        <h3 style='color: #27ae60;'>What You'll Do:</h3>
        <ol>
            <li><b>Setup:</b> Choose bullet type and sample size (10-50 bullets)</li>
            <li><b>Measure:</b> Weigh and measure each bullet</li>
            <li><b>Analyze:</b> See statistics (Average, SD, ES, distribution)</li>
            <li><b>Sort:</b> Separate match-grade vs practice bullets</li>
        </ol>

        <div style='background-color: #d5f4e6; padding: 15px; border-radius: 5px; margin-top: 20px;'>
            <b>🏆 Pro Tip:</b> Ogive measurement is MORE important than weight!<br>
            Consistent base-to-ogive = consistent jump to rifling = better accuracy.<br>
            Weight only affects velocity slightly.
        </div>

        <div style='background-color: #fff9c4; padding: 15px; border-radius: 5px; margin-top: 10px;'>
            <b>📊 What to expect:</b><br>
            • Premium bullets (Berger, Lapua): Weight SD ~0.1 gr, Ogive SD ~0.001"<br>
            • Good bullets (Hornady, Sierra): Weight SD ~0.2 gr, Ogive SD ~0.002"<br>
            • Budget bullets: Weight SD ~0.3+ gr, Ogive SD ~0.003+"
        </div>
        </div>
        """

        info_label = QLabel(info_html)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)

        layout.addStretch()


class SetupPage(QWizardPage):
    """Setup: Choose bullet and sample size"""

    def __init__(self):
        super().__init__()
        self.setTitle("⚙️ Setup Measurement Session")
        self.setSubTitle("Tell us what bullets you're measuring")

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Bullet selection
        bullet_group = QGroupBox("Select Bullet")
        bullet_layout = QVBoxLayout()

        self.existing_bullet = QRadioButton("From database")
        self.existing_bullet.setChecked(True)
        bullet_layout.addWidget(self.existing_bullet)

        self.bullet_combo = QComboBox()
        self.load_bullets_from_database()
        bullet_layout.addWidget(self.bullet_combo)

        # Show previous QC measurements for selected bullet
        self.btn_view_history = QPushButton("📊 View QC History for this bullet")
        self.btn_view_history.clicked.connect(self.view_qc_history)
        bullet_layout.addWidget(self.btn_view_history)

        self.custom_bullet = QRadioButton("Custom bullet")
        bullet_layout.addWidget(self.custom_bullet)

        self.custom_name = QLineEdit()
        self.custom_name.setPlaceholderText("Enter bullet name...")
        self.custom_name.setEnabled(False)
        bullet_layout.addWidget(self.custom_name)

        self.custom_bullet.toggled.connect(
            lambda: self.custom_name.setEnabled(self.custom_bullet.isChecked())
        )
        self.custom_bullet.toggled.connect(
            lambda: self.bullet_combo.setEnabled(not self.custom_bullet.isChecked())
        )

        bullet_group.setLayout(bullet_layout)
        layout.addWidget(bullet_group)

        # Lot number
        self.lot_number = QLineEdit()
        self.lot_number.setPlaceholderText("e.g., 2024-08-L7342")
        form.addRow("Lot Number:", self.lot_number)

        # Sample size
        self.sample_size = QSpinBox()
        self.sample_size.setRange(5, 100)
        self.sample_size.setValue(20)
        self.sample_size.setSuffix(" bullets")
        form.addRow("Sample Size:", self.sample_size)

        help_label = QLabel(
            "💡 <b>Recommended:</b> 10-20 bullets for quick check, "
            "50+ for serious match prep"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet(
            "background-color: #e8f4f8; padding: 10px; border-radius: 5px;"
        )
        form.addRow(help_label)

        # What to measure
        measure_group = QGroupBox("What to Measure?")
        measure_layout = QVBoxLayout()

        self.measure_weight = QCheckBox("Weight (requires scale)")
        self.measure_weight.setChecked(True)
        measure_layout.addWidget(self.measure_weight)

        self.measure_length = QCheckBox("Overall Length (requires calipers)")
        self.measure_length.setChecked(True)
        measure_layout.addWidget(self.measure_length)

        self.measure_ogive = QCheckBox("Base to Ogive (requires comparator)")
        self.measure_ogive.setChecked(True)
        measure_layout.addWidget(self.measure_ogive)

        help2 = QLabel(
            "🎯 <b>Pro tip:</b> Ogive is most important for accuracy!\n"
            "If you only have time for one measurement, measure ogive."
        )
        help2.setStyleSheet(
            "background-color: #d5f4e6; padding: 8px; border-radius: 5px; margin-top: 10px;"
        )
        measure_layout.addWidget(help2)

        measure_group.setLayout(measure_layout)
        layout.addWidget(measure_group)

        layout.addLayout(form)
        layout.addStretch()

        # Register fields
        self.registerField("sample_size", self.sample_size)
        self.registerField("lot_number", self.lot_number)

    def load_bullets_from_database(self):
        """Load bullets from component database"""
        import json
        import os

        db_path = "data/components_database.json"

        if not os.path.exists(db_path):
            # Fallback to hardcoded
            self.bullet_combo.addItems(
                [
                    "Berger 140gr Hybrid Target (6.5mm)",
                    "Sierra 142gr MatchKing (6.5mm)",
                    "Lapua 139gr Scenar (6.5mm)",
                    "Hornady 140gr ELD Match (6.5mm)",
                    "Berger 185gr Hybrid (.308)",
                    "Sierra 175gr MatchKing (.308)",
                ]
            )
            return

        try:
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)

            bullets = db.get("bullets", [])

            # Format: "Berger 140gr Hybrid Target (6.5mm)"
            bullet_names = [
                f"{b['manufacturer']} {b['weight']}gr {b['name']} ({b['caliber']})"
                for b in bullets
            ]

            self.bullet_combo.addItems(bullet_names)

        except Exception:
            logger.exception("Error loading bullets from %s", db_path)
            self.bullet_combo.addItems(["Error loading database"])

    def view_qc_history(self):
        """Show QC history for selected bullet"""
        bullet_name = self.bullet_combo.currentText()

        # Load QC history
        history = self.load_qc_history(bullet_name)

        if not history:
            QMessageBox.information(
                self,
                "No History",
                f"No QC measurements found for:\n{bullet_name}\n\n"
                "This will be your first measurement for this bullet!",
            )
            return

        # Show history dialog
        dialog = QCHistoryDialog(bullet_name, history, self)
        dialog.exec()

    def load_qc_history(self, bullet_name: str) -> List[Dict]:
        """Load QC history from file"""
        import json
        import os

        history_file = "data/qc_history.json"

        if not os.path.exists(history_file):
            return []

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                all_history = json.load(f)

            # Filter by bullet name
            return all_history.get(bullet_name, [])

        except Exception:
            logger.exception("Error loading QC history from %s", history_file)
            return []

    def get_bullet_name(self) -> str:
        """Get selected bullet name"""
        if self.custom_bullet.isChecked():
            return self.custom_name.text()
        else:
            return self.bullet_combo.currentText()


class MeasurementPage(QWizardPage):
    """Enter measurements"""

    measurements_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setTitle("📏 Enter Measurements")
        self.setSubTitle("Measure each bullet and enter the values")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Progress bar
        self.progress_label = QLabel("Progress: 0 / 20 bullets measured")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(20)
        layout.addWidget(self.progress_bar)

        # Quick entry form
        entry_group = QGroupBox("📝 Quick Entry (Current Bullet)")
        entry_layout = QFormLayout()

        self.current_bullet = QLabel("Bullet #1")
        self.current_bullet.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #2c3e50;"
        )
        entry_layout.addRow(self.current_bullet)

        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(50, 250)
        self.weight_input.setValue(140.0)
        self.weight_input.setDecimals(2)
        self.weight_input.setSuffix(" gr")
        entry_layout.addRow("Weight:", self.weight_input)

        self.length_input = QDoubleSpinBox()
        self.length_input.setRange(0.5, 2.5)
        self.length_input.setValue(1.430)
        self.length_input.setDecimals(4)
        self.length_input.setSuffix('"')
        entry_layout.addRow("Overall Length:", self.length_input)

        self.ogive_input = QDoubleSpinBox()
        self.ogive_input.setRange(0.5, 2.0)
        self.ogive_input.setValue(0.850)
        self.ogive_input.setDecimals(4)
        self.ogive_input.setSuffix('"')
        entry_layout.addRow("Base to Ogive:", self.ogive_input)

        self.btn_add = QPushButton("✅ Add Bullet & Next")
        self.btn_add.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """
        )
        self.btn_add.clicked.connect(self.add_measurement)
        entry_layout.addRow(self.btn_add)

        entry_group.setLayout(entry_layout)
        layout.addWidget(entry_group)

        # Measurements table
        table_label = QLabel("<b>📊 Recorded Measurements:</b>")
        layout.addWidget(table_label)

        self.measurements_table = QTableWidget()
        self.measurements_table.setColumnCount(4)
        self.measurements_table.setHorizontalHeaderLabels(
            ["Bullet #", "Weight (gr)", "Length (in)", "Ogive (in)"]
        )
        self.measurements_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.measurements_table)

        # Live stats preview
        stats_label = QLabel("<b>📈 Live Statistics:</b>")
        layout.addWidget(stats_label)

        self.live_stats = QLabel("No measurements yet")
        self.live_stats.setStyleSheet(
            "background-color: #ecf0f1; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(self.live_stats)

        # Data storage
        self.measurements: List[Dict] = []

    def initializePage(self):
        """Initialize when page is shown"""
        # Get sample size from previous page
        sample_size = self.wizard().field("sample_size")
        self.progress_bar.setMaximum(sample_size)
        self.progress_label.setText(f"Progress: 0 / {sample_size} bullets measured")

        # Clear previous measurements
        self.measurements = []
        self.measurements_table.setRowCount(0)
        self.current_bullet.setText("Bullet #1")

        # Focus on first input
        self.weight_input.setFocus()
        self.weight_input.selectAll()

    def add_measurement(self):
        """Add current measurement to table"""
        bullet_num = len(self.measurements) + 1
        sample_size = self.wizard().field("sample_size")

        if bullet_num > sample_size:
            QMessageBox.information(
                self,
                "Complete!",
                f"All {sample_size} bullets measured!\nClick Next to see results.",
            )
            return

        # Record measurement
        measurement = {
            "bullet_num": bullet_num,
            "weight": self.weight_input.value(),
            "length": self.length_input.value(),
            "ogive": self.ogive_input.value(),
        }
        self.measurements.append(measurement)

        # Add to table
        row = self.measurements_table.rowCount()
        self.measurements_table.insertRow(row)

        self.measurements_table.setItem(row, 0, QTableWidgetItem(f"#{bullet_num}"))
        self.measurements_table.setItem(
            row, 1, QTableWidgetItem(f"{measurement['weight']:.2f}")
        )
        self.measurements_table.setItem(
            row, 2, QTableWidgetItem(f"{measurement['length']:.4f}")
        )
        self.measurements_table.setItem(
            row, 3, QTableWidgetItem(f"{measurement['ogive']:.4f}")
        )

        # Update progress
        self.progress_bar.setValue(bullet_num)
        self.progress_label.setText(
            f"Progress: {bullet_num} / {sample_size} bullets measured"
        )

        # Update live stats
        self.update_live_stats()

        # Emit to results page
        self.measurements_changed.emit(self.get_measurements_dict())

        # Next bullet
        if bullet_num < sample_size:
            self.current_bullet.setText(f"Bullet #{bullet_num + 1}")
            # Randomize slightly for realistic variation
            import random

            self.weight_input.setValue(
                self.weight_input.value() + random.uniform(-0.2, 0.2)
            )
            self.length_input.setValue(
                self.length_input.value() + random.uniform(-0.002, 0.002)
            )
            self.ogive_input.setValue(
                self.ogive_input.value() + random.uniform(-0.001, 0.001)
            )
            self.weight_input.setFocus()
            self.weight_input.selectAll()
        else:
            self.btn_add.setText("✅ All Done! Click Next →")
            self.btn_add.setEnabled(False)

    def update_live_stats(self):
        """Update live statistics"""
        if not self.measurements:
            return

        weights = [m["weight"] for m in self.measurements]
        ogives = [m["ogive"] for m in self.measurements]

        weight_avg = statistics.mean(weights)
        weight_sd = statistics.stdev(weights) if len(weights) > 1 else 0
        weight_es = max(weights) - min(weights)

        ogive_avg = statistics.mean(ogives)
        ogive_sd = statistics.stdev(ogives) if len(ogives) > 1 else 0
        ogive_es = max(ogives) - min(ogives)

        stats_text = f"""
        <b>Weight:</b> Avg {weight_avg:.2f} gr, SD {weight_sd:.2f} gr, ES {weight_es:.2f} gr<br>
        <b>Ogive:</b> Avg {ogive_avg:.4f}", SD {ogive_sd:.4f}", ES {ogive_es:.4f}"<br>
        <span style='color: #27ae60;'><b>✓ Looking good!</b></span>
        """

        self.live_stats.setText(stats_text)

    def get_measurements_dict(self) -> Dict:
        """Get measurements as dict"""
        return {"measurements": self.measurements, "count": len(self.measurements)}

    def isComplete(self):
        """Page is complete when all bullets measured"""
        sample_size = self.wizard().field("sample_size")
        return len(self.measurements) >= sample_size


class ResultsPage(QWizardPage):
    """Show results and sorting recommendations"""

    def __init__(self):
        super().__init__()
        self.setTitle("📊 Results & Analysis")
        self.setSubTitle("Here's what we found!")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Statistics summary
        self.stats_group = QGroupBox("📈 Statistical Summary")
        self.stats_layout = QVBoxLayout()
        self.stats_label = QLabel("Waiting for measurements...")
        self.stats_layout.addWidget(self.stats_label)
        self.stats_group.setLayout(self.stats_layout)
        layout.addWidget(self.stats_group)

        # Sorting recommendations
        self.sorting_group = QGroupBox("🎯 Sorting Recommendations")
        self.sorting_layout = QVBoxLayout()
        self.sorting_label = QLabel("Waiting for measurements...")
        self.sorting_layout.addWidget(self.sorting_label)
        self.sorting_group.setLayout(self.sorting_layout)
        layout.addWidget(self.sorting_group)

        # What to do next
        next_steps = QLabel(
            """
        <h3>What to do next:</h3>
        <ol>
            <li><b>Match bullets:</b> Use for competitions (within ±0.001" ogive)</li>
            <li><b>Practice bullets:</b> Use for load development and practice</li>
            <li><b>Mark boxes:</b> Label sorted groups with lot # and quality grade</li>
            <li><b>Record data:</b> Save to inventory with QC notes</li>
        </ol>
        """
        )
        next_steps.setStyleSheet(
            "background-color: #e8f4f8; padding: 15px; border-radius: 5px;"
        )
        layout.addWidget(next_steps)

        layout.addStretch()

        self.measurements_data = None

    def update_results(self, measurements_dict: Dict):
        """Update results with new measurements"""
        self.measurements_data = measurements_dict
        measurements = measurements_dict.get("measurements", [])

        if not measurements:
            return

        # Calculate statistics
        weights = [m["weight"] for m in measurements]
        _lengths = [m["length"] for m in measurements]
        ogives = [m["ogive"] for m in measurements]

        weight_avg = statistics.mean(weights)
        weight_sd = statistics.stdev(weights) if len(weights) > 1 else 0
        weight_es = max(weights) - min(weights)

        length_avg = statistics.mean(_lengths)
        length_sd = statistics.stdev(_lengths) if len(_lengths) > 1 else 0
        length_es = max(_lengths) - min(_lengths)

        ogive_avg = statistics.mean(ogives)
        ogive_sd = statistics.stdev(ogives) if len(ogives) > 1 else 0
        ogive_es = max(ogives) - min(ogives)

        # Display statistics
        stats_html = f"""
        <table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1; font-weight: bold;'>
                <th>Measurement</th>
                <th>Average</th>
                <th>SD</th>
                <th>ES</th>
                <th>Quality</th>
            </tr>
            <tr>
                <td><b>Weight</b></td>
                <td>{weight_avg:.2f} gr</td>
                <td>{weight_sd:.3f} gr</td>
                <td>{weight_es:.2f} gr</td>
                <td>{self.grade_weight(weight_sd)}</td>
            </tr>
            <tr>
                <td><b>Overall Length</b></td>
                <td>{length_avg:.4f}"</td>
                <td>{length_sd:.4f}"</td>
                <td>{length_es:.4f}"</td>
                <td>{self.grade_length(length_sd)}</td>
            </tr>
            <tr style='background-color: #d5f4e6;'>
                <td><b>Base to Ogive</b></td>
                <td>{ogive_avg:.4f}"</td>
                <td>{ogive_sd:.4f}"</td>
                <td>{ogive_es:.4f}"</td>
                <td><b>{self.grade_ogive(ogive_sd)}</b></td>
            </tr>
        </table>
        """

        self.stats_label.setText(stats_html)

        # Sorting recommendations
        match_count = sum(
            1 for m in measurements if abs(m["ogive"] - ogive_avg) <= 0.001
        )
        practice_count = len(measurements) - match_count

        sorting_html = f"""
        <div style='font-size: 14px;'>
        <p><b>Based on ogive measurement (most important for accuracy):</b></p>

        <div style='background-color: #d5f4e6; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
            <b>🏆 MATCH GRADE:</b> {match_count} bullets<br>
            Ogive within ±0.001" of average ({ogive_avg:.4f}")<br>
            <b>Range:</b> {ogive_avg - 0.001:.4f}" to {ogive_avg + 0.001:.4f}"<br>
            <b>Use for:</b> Competitions, record attempts, important matches
        </div>

        <div style='background-color: #fff9c4; padding: 15px; border-radius: 5px;'>
            <b>🎯 PRACTICE GRADE:</b> {practice_count} bullets<br>
            Ogive outside ±0.001" tolerance<br>
            <b>Use for:</b> Load development, practice, fouling shots
        </div>

        <p style='margin-top: 15px;'><b>💡 Pro Tip:</b> Save the best bullets for match day!
        Use practice bullets to find your load, then verify with match bullets.</p>
        </div>
        """

        self.sorting_label.setText(sorting_html)

    def grade_weight(self, sd: float) -> str:
        """Grade weight consistency"""
        if sd < 0.1:
            return "<span style='color: #27ae60;'><b>★★★★★ Excellent</b></span>"
        elif sd < 0.2:
            return "<span style='color: #27ae60;'><b>★★★★☆ Very Good</b></span>"
        elif sd < 0.3:
            return "<span style='color: #f39c12;'><b>★★★☆☆ Good</b></span>"
        else:
            return "<span style='color: #e74c3c;'><b>★★☆☆☆ Fair</b></span>"

    def grade_length(self, sd: float) -> str:
        """Grade length consistency"""
        if sd < 0.002:
            return "<span style='color: #27ae60;'><b>★★★★★ Excellent</b></span>"
        elif sd < 0.004:
            return "<span style='color: #27ae60;'><b>★★★★☆ Very Good</b></span>"
        elif sd < 0.006:
            return "<span style='color: #f39c12;'><b>★★★☆☆ Good</b></span>"
        else:
            return "<span style='color: #e74c3c;'><b>★★☆☆☆ Fair</b></span>"

    def grade_ogive(self, sd: float) -> str:
        """Grade ogive consistency"""
        if sd < 0.001:
            return "<span style='color: #27ae60;'><b>★★★★★ Excellent</b></span>"
        elif sd < 0.002:
            return "<span style='color: #27ae60;'><b>★★★★☆ Very Good</b></span>"
        elif sd < 0.003:
            return "<span style='color: #f39c12;'><b>★★★☆☆ Good</b></span>"
        else:
            return "<span style='color: #e74c3c;'><b>★★☆☆☆ Fair</b></span>"

    def get_final_results(self) -> Dict:
        """Get final results for saving"""
        if not self.measurements_data:
            return {"measurements": None, "completed": False}

        measurements = self.measurements_data.get("measurements", [])

        if not measurements:
            return {"measurements": None, "completed": False}

        # Calculate final statistics
        weights = [m["weight"] for m in measurements]
        lengths = [m["length"] for m in measurements]
        ogives = [m["ogive"] for m in measurements]

        weight_avg = statistics.mean(weights)
        weight_sd = statistics.stdev(weights) if len(weights) > 1 else 0

        length_avg = statistics.mean(lengths)
        length_sd = statistics.stdev(lengths) if len(lengths) > 1 else 0
        length_es = max(lengths) - min(lengths) if lengths else 0

        ogive_avg = statistics.mean(ogives)
        ogive_sd = statistics.stdev(ogives) if len(ogives) > 1 else 0

        return {
            "measurements": self.measurements_data,
            "completed": True,
            "statistics": {
                "weight_avg": weight_avg,
                "weight_sd": weight_sd,
                "ogive_avg": ogive_avg,
                "ogive_sd": ogive_sd,
                "length_avg": length_avg,
                "length_sd": length_sd,
                "length_es": length_es,
                "sample_size": len(measurements),
            },
        }


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    wizard = BulletQCWizard()
    wizard.show()

    sys.exit(app.exec())
