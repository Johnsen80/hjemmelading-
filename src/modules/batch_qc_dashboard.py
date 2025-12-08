"""
Batch QC Dashboard - Production Quality Control
Real-time quality control during loading (som ammofabrikker gjør!)
"""

from datetime import datetime
from typing import Dict

import numpy as np
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
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
from src.modules.live_visualization import LiveHistogram


class QCMeasurementDialog(QDialog):
    """Dialog for å registrere QC-målinger"""

    def __init__(self, measurement_type: str, parent=None):
        super().__init__(parent)
        self.measurement_type = measurement_type

        self.setWindowTitle(f"QC Måling: {measurement_type}")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Patron number
        num_layout = QHBoxLayout()
        num_layout.addWidget(QLabel("Patron #:"))
        self.spin_number = QSpinBox()
        self.spin_number.setRange(1, 1000)
        num_layout.addWidget(self.spin_number)
        layout.addLayout(num_layout)

        # Measurement value
        val_layout = QHBoxLayout()
        val_layout.addWidget(QLabel(f"{self.measurement_type}:"))
        self.spin_value = QDoubleSpinBox()
        self.spin_value.setDecimals(3)

        if self.measurement_type == "Charge Weight":
            self.spin_value.setRange(20, 80)
            self.spin_value.setSuffix(" gr")
            self.spin_value.setSingleStep(0.1)
        elif self.measurement_type == "COAL":
            self.spin_value.setRange(2.0, 4.0)
            self.spin_value.setSuffix(' "')
            self.spin_value.setSingleStep(0.001)
        elif self.measurement_type == "Case Weight":
            self.spin_value.setRange(100, 300)
            self.spin_value.setSuffix(" gr")
            self.spin_value.setSingleStep(0.1)

        val_layout.addWidget(self.spin_value)
        layout.addLayout(val_layout)

        # Notes
        layout.addWidget(QLabel("Notater (hvis outlier):"))
        self.edit_notes = QTextEdit()
        self.edit_notes.setMaximumHeight(60)
        self.edit_notes.setPlaceholderText("Scratch on bullet, case dent, etc...")
        layout.addWidget(self.edit_notes)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self) -> Dict:
        """Hent måle-data"""
        return {
            "patron_number": self.spin_number.value(),
            "value": self.spin_value.value(),
            "notes": self.edit_notes.toPlainText(),
        }


class BatchQCDashboard(QWidget):
    """
    Batch Quality Control Dashboard
    Real-time QC under loading - som ammofabrikker!
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.current_batch_id = None
        self.qc_data = {"charge_weight": [], "coal": [], "case_weight": []}
        self.batch_specs = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("🎯 Batch QC Dashboard")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel(
            "Production Quality Control - Real-time QC during loading.\n"
            "Ammofabrikker måler 10-20% av hver batch. Du bør gjøre det samme!"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Batch setup section
        setup_group = QGroupBox("📦 Batch Setup")
        setup_layout = QVBoxLayout()

        # Batch info
        info_layout = QHBoxLayout()

        info_layout.addWidget(QLabel("Batch navn:"))
        self.edit_batch_name = QLineEdit()
        self.edit_batch_name.setPlaceholderText("6.5CM 140gr 43.5gr N140")
        info_layout.addWidget(self.edit_batch_name)

        info_layout.addWidget(QLabel("Antall patroner:"))
        self.spin_batch_size = QSpinBox()
        self.spin_batch_size.setRange(10, 1000)
        self.spin_batch_size.setValue(100)
        info_layout.addWidget(self.spin_batch_size)

        setup_layout.addLayout(info_layout)

        # Target specs
        specs_layout = QHBoxLayout()

        specs_layout.addWidget(QLabel("Target Charge:"))
        self.spin_target_charge = QDoubleSpinBox()
        self.spin_target_charge.setRange(20, 80)
        self.spin_target_charge.setDecimals(1)
        self.spin_target_charge.setSuffix(" gr")
        self.spin_target_charge.setValue(43.5)
        specs_layout.addWidget(self.spin_target_charge)

        specs_layout.addWidget(QLabel("Tolerance:"))
        self.spin_charge_tolerance = QDoubleSpinBox()
        self.spin_charge_tolerance.setRange(0.01, 1.0)
        self.spin_charge_tolerance.setDecimals(2)
        self.spin_charge_tolerance.setSuffix(" gr")
        self.spin_charge_tolerance.setValue(0.1)
        specs_layout.addWidget(self.spin_charge_tolerance)

        specs_layout.addStretch()
        setup_layout.addLayout(specs_layout)

        # COAL specs
        coal_layout = QHBoxLayout()

        coal_layout.addWidget(QLabel("Target COAL:"))
        self.spin_target_coal = QDoubleSpinBox()
        self.spin_target_coal.setRange(2.0, 4.0)
        self.spin_target_coal.setDecimals(3)
        self.spin_target_coal.setSuffix(' "')
        self.spin_target_coal.setValue(2.800)
        coal_layout.addWidget(self.spin_target_coal)

        coal_layout.addWidget(QLabel("Tolerance:"))
        self.spin_coal_tolerance = QDoubleSpinBox()
        self.spin_coal_tolerance.setRange(0.001, 0.050)
        self.spin_coal_tolerance.setDecimals(3)
        self.spin_coal_tolerance.setSuffix(' "')
        self.spin_coal_tolerance.setValue(0.005)
        coal_layout.addWidget(self.spin_coal_tolerance)

        coal_layout.addStretch()
        setup_layout.addLayout(coal_layout)

        # Start button
        btn_layout = QHBoxLayout()
        self.btn_start_batch = QPushButton("🚀 Start Batch QC")
        self.btn_start_batch.clicked.connect(self.start_batch)
        self.btn_start_batch.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """
        )
        btn_layout.addWidget(self.btn_start_batch)
        btn_layout.addStretch()
        setup_layout.addLayout(btn_layout)

        setup_group.setLayout(setup_layout)
        layout.addWidget(setup_group)

        # Progress section
        progress_group = QGroupBox("📊 Batch Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        # Quick stats
        stats_layout = QHBoxLayout()

        self.label_measured = QLabel("Målt: 0")
        self.label_measured.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.label_measured)

        self.label_outliers = QLabel("Outliers: 0")
        self.label_outliers.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #e74c3c;"
        )
        stats_layout.addWidget(self.label_outliers)

        self.label_status = QLabel("Status: Venter")
        self.label_status.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #7f8c8d;"
        )
        stats_layout.addWidget(self.label_status)

        stats_layout.addStretch()
        progress_layout.addLayout(stats_layout)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Measurement section
        measure_group = QGroupBox("📏 QC Målinger")
        measure_layout = QVBoxLayout()

        # Measurement buttons
        btn_measure_layout = QHBoxLayout()

        self.btn_charge = QPushButton("⚖️ Charge Weight")
        self.btn_charge.clicked.connect(lambda: self.add_measurement("charge_weight"))
        self.btn_charge.setEnabled(False)
        btn_measure_layout.addWidget(self.btn_charge)

        self.btn_coal = QPushButton("📏 COAL")
        self.btn_coal.clicked.connect(lambda: self.add_measurement("coal"))
        self.btn_coal.setEnabled(False)
        btn_measure_layout.addWidget(self.btn_coal)

        self.btn_case = QPushButton("📦 Case Weight")
        self.btn_case.clicked.connect(lambda: self.add_measurement("case_weight"))
        self.btn_case.setEnabled(False)
        btn_measure_layout.addWidget(self.btn_case)

        btn_measure_layout.addStretch()
        measure_layout.addLayout(btn_measure_layout)

        # Measurements table
        self.table_measurements = QTableWidget()
        self.table_measurements.setColumnCount(6)
        self.table_measurements.setHorizontalHeaderLabels(
            ["Patron #", "Type", "Verdi", "Target", "Delta", "Status"]
        )
        self.table_measurements.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        measure_layout.addWidget(self.table_measurements)

        measure_group.setLayout(measure_layout)
        layout.addWidget(measure_group)

        # Analysis section
        analysis_group = QGroupBox("📈 Batch Analyse")
        analysis_layout = QVBoxLayout()

        # LIVE HISTOGRAM TABS
        hist_tabs = QTabWidget()

        # Charge weight histogram
        self.live_hist_charge = LiveHistogram(width=8, height=4)
        hist_tabs.addTab(self.live_hist_charge, "⚖️ Charge Weight")

        # COAL histogram
        self.live_hist_coal = LiveHistogram(width=8, height=4)
        hist_tabs.addTab(self.live_hist_coal, "📏 COAL")

        # Case weight histogram
        self.live_hist_case = LiveHistogram(width=8, height=4)
        hist_tabs.addTab(self.live_hist_case, "📦 Case Weight")

        analysis_layout.addWidget(hist_tabs)

        # Analysis buttons
        analysis_btn_layout = QHBoxLayout()

        self.btn_analyze = QPushButton("🔍 Analyser Batch")
        self.btn_analyze.clicked.connect(self.analyze_batch)
        self.btn_analyze.setEnabled(False)
        analysis_btn_layout.addWidget(self.btn_analyze)

        self.btn_complete = QPushButton("✅ Godkjenn Batch")
        self.btn_complete.clicked.connect(self.complete_batch)
        self.btn_complete.setEnabled(False)
        analysis_btn_layout.addWidget(self.btn_complete)

        self.btn_reject = QPushButton("❌ Avvis Batch")
        self.btn_reject.clicked.connect(self.reject_batch)
        self.btn_reject.setEnabled(False)
        analysis_btn_layout.addWidget(self.btn_reject)

        analysis_btn_layout.addStretch()
        analysis_layout.addLayout(analysis_btn_layout)

        # Results
        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        self.text_results.setMaximumHeight(200)
        analysis_layout.addWidget(self.text_results)

        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        self.setLayout(layout)

    def start_batch(self):
        """Start ny batch QC"""
        if not self.edit_batch_name.text():
            QMessageBox.warning(self, "Mangler navn", "Angi batch navn!")
            return

        # Save batch to database
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO qc_batches (
                name, target_charge, charge_tolerance,
                target_coal, coal_tolerance, batch_size,
                created_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.edit_batch_name.text(),
                self.spin_target_charge.value(),
                self.spin_charge_tolerance.value(),
                self.spin_target_coal.value(),
                self.spin_coal_tolerance.value(),
                self.spin_batch_size.value(),
                datetime.now().isoformat(),
                "in_progress",
            ),
        )
        self.db.conn.commit()

        self.current_batch_id = cursor.lastrowid

        # Store specs
        self.batch_specs = {
            "target_charge": self.spin_target_charge.value(),
            "charge_tolerance": self.spin_charge_tolerance.value(),
            "target_coal": self.spin_target_coal.value(),
            "coal_tolerance": self.spin_coal_tolerance.value(),
            "batch_size": self.spin_batch_size.value(),
        }

        # Reset data
        self.qc_data = {"charge_weight": [], "coal": [], "case_weight": []}
        self.table_measurements.setRowCount(0)

        # Configure live histograms
        self.live_hist_charge.set_target(
            self.spin_target_charge.value(), self.spin_charge_tolerance.value(), "gr"
        )
        self.live_hist_charge.clear_data()

        self.live_hist_coal.set_target(
            self.spin_target_coal.value(), self.spin_coal_tolerance.value(), '"'
        )
        self.live_hist_coal.clear_data()

        self.live_hist_case.set_target(None, None, "gr")
        self.live_hist_case.clear_data()

        # Enable measurement buttons
        self.btn_charge.setEnabled(True)
        self.btn_coal.setEnabled(True)
        self.btn_case.setEnabled(True)
        self.btn_start_batch.setEnabled(False)

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(self.spin_batch_size.value())
        self.progress_bar.setValue(0)

        self.label_status.setText("Status: 🟢 QC i gang")
        self.label_status.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #27ae60;"
        )

        QMessageBox.information(
            self,
            "Batch startet",
            f"Batch QC startet!\n\n"
            f"Anbefaling: Mål 10-20% av patroner ({int(self.spin_batch_size.value() * 0.15)} stk)",
        )

    def add_measurement(self, measurement_type: str):
        """Legg til QC-måling"""
        if not self.current_batch_id:
            return

        type_names = {
            "charge_weight": "Charge Weight",
            "coal": "COAL",
            "case_weight": "Case Weight",
        }

        dialog = QCMeasurementDialog(type_names[measurement_type], self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            # Determine target and tolerance
            if measurement_type == "charge_weight":
                target = self.batch_specs["target_charge"]
                tolerance = self.batch_specs["charge_tolerance"]
            elif measurement_type == "coal":
                target = self.batch_specs["target_coal"]
                tolerance = self.batch_specs["coal_tolerance"]
            else:
                target = None
                tolerance = None

            # Calculate delta
            delta = data["value"] - target if target else 0
            is_outlier = abs(delta) > tolerance if tolerance else False

            # Save to database
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO qc_measurements (
                    batch_id, patron_number, measurement_type,
                    value, target_value, delta, is_outlier, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.current_batch_id,
                    data["patron_number"],
                    measurement_type,
                    data["value"],
                    target,
                    delta,
                    1 if is_outlier else 0,
                    data["notes"],
                ),
            )
            self.db.conn.commit()

            # Add to internal data
            self.qc_data[measurement_type].append(
                {
                    "patron": data["patron_number"],
                    "value": data["value"],
                    "delta": delta,
                    "outlier": is_outlier,
                }
            )

            # Update live histogram
            if measurement_type == "charge_weight":
                self.live_hist_charge.add_value(data["value"])
            elif measurement_type == "coal":
                self.live_hist_coal.add_value(data["value"])
            elif measurement_type == "case_weight":
                self.live_hist_case.add_value(data["value"])

            # Add to table
            row = self.table_measurements.rowCount()
            self.table_measurements.insertRow(row)

            self.table_measurements.setItem(
                row, 0, QTableWidgetItem(str(data["patron_number"]))
            )
            self.table_measurements.setItem(
                row, 1, QTableWidgetItem(type_names[measurement_type])
            )
            self.table_measurements.setItem(
                row, 2, QTableWidgetItem(f"{data['value']:.3f}")
            )
            self.table_measurements.setItem(
                row, 3, QTableWidgetItem(f"{target:.3f}" if target else "N/A")
            )

            delta_item = QTableWidgetItem(f"{delta:+.3f}" if target else "N/A")
            if is_outlier:
                delta_item.setBackground(QColor(255, 200, 200))
            self.table_measurements.setItem(row, 4, delta_item)

            status_item = QTableWidgetItem("❌ OUTLIER" if is_outlier else "✅ OK")
            if is_outlier:
                status_item.setForeground(QColor(231, 76, 60))
            else:
                status_item.setForeground(QColor(39, 174, 96))
            self.table_measurements.setItem(row, 5, status_item)

            # Update stats
            total_measured = sum(len(v) for v in self.qc_data.values())
            total_outliers = sum(
                1 for v in self.qc_data.values() for m in v if m["outlier"]
            )

            self.label_measured.setText(f"Målt: {total_measured}")
            self.label_outliers.setText(f"Outliers: {total_outliers}")

            if total_outliers > 0:
                self.label_outliers.setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #e74c3c;"
                )

            self.progress_bar.setValue(total_measured)

            # Enable analyze if we have enough data
            if total_measured >= 5:
                self.btn_analyze.setEnabled(True)

    def analyze_batch(self):
        """Analyser batch QC data"""
        if not self.qc_data["charge_weight"] and not self.qc_data["coal"]:
            QMessageBox.warning(self, "For lite data", "Trenger minst noen målinger!")
            return

        # Calculate statistics
        stats = {}

        for mtype, data in self.qc_data.items():
            if not data:
                continue

            values = [d["value"] for d in data]
            _deltas = [d["delta"] for d in data]
            outliers = [d for d in data if d["outlier"]]

            stats[mtype] = {
                "n": len(values),
                "mean": np.mean(values),
                "std": np.std(values),
                "min": min(values),
                "max": max(values),
                "range": max(values) - min(values),
                "outlier_count": len(outliers),
                "outlier_pct": (len(outliers) / len(values)) * 100,
            }

        # Plot distributions
        self.figure.clear()

        plot_count = len([s for s in stats.values() if s])
        if plot_count == 0:
            return

        for i, (mtype, stat) in enumerate(stats.items()):
            if not stat:
                continue

            ax = self.figure.add_subplot(1, plot_count, i + 1)

            values = [d["value"] for d in self.qc_data[mtype]]
            outliers = [d["value"] for d in self.qc_data[mtype] if d["outlier"]]

            # Histogram
            ax.hist(values, bins=15, alpha=0.7, color="blue", edgecolor="black")

            # Mark outliers
            if outliers:
                for outlier in outliers:
                    ax.axvline(
                        outlier, color="red", linestyle="--", linewidth=2, alpha=0.7
                    )

            # Target line
            if mtype == "charge_weight":
                target = self.batch_specs["target_charge"]
                ax.axvline(
                    target, color="green", linestyle="-", linewidth=2, label="Target"
                )
            elif mtype == "coal":
                target = self.batch_specs["target_coal"]
                ax.axvline(
                    target, color="green", linestyle="-", linewidth=2, label="Target"
                )

            ax.set_xlabel("Value")
            ax.set_ylabel("Count")
            ax.set_title(mtype.replace("_", " ").title())
            ax.legend()
            ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

        # Generate results
        results = self.generate_qc_report(stats)
        self.text_results.setHtml(results)

        # Enable completion buttons
        self.btn_complete.setEnabled(True)
        self.btn_reject.setEnabled(True)

    def generate_qc_report(self, stats: Dict) -> str:
        """Generate QC report HTML"""
        html = """
        <h2 style='color: #2c3e50;'>📊 Batch QC Report</h2>
        """

        for mtype, stat in stats.items():
            if not stat:
                continue

            type_name = mtype.replace("_", " ").title()

            # Determine pass/fail
            if stat["outlier_pct"] <= 5:
                status_color = "#27ae60"
                status_text = "✅ PASS"
            elif stat["outlier_pct"] <= 10:
                status_color = "#f39c12"
                status_text = "⚠️ MARGINAL"
            else:
                status_color = "#e74c3c"
                status_text = "❌ FAIL"

            html += f"""
            <h3>{type_name}: <span style='color: {status_color};'>{status_text}</span></h3>
            <ul>
                <li><b>Samples:</b> {stat['n']}</li>
                <li><b>Mean:</b> {stat['mean']:.3f}</li>
                <li><b>Std Dev:</b> {stat['std']:.4f}</li>
                <li><b>Range:</b> {stat['range']:.3f} ({stat['min']:.3f} - {stat['max']:.3f})</li>
                <li><b>Outliers:</b> {stat['outlier_count']} ({stat['outlier_pct']:.1f}%)</li>
            </ul>
            """

        # Factory comparison
        html += """
        <h3>🏭 Sammenligning mot ammofabrikker:</h3>
        <p style='color: #7f8c8d;'>
        """

        if "charge_weight" in stats:
            charge_std = stats["charge_weight"]["std"]
            if charge_std < 0.05:
                html += "✅ <b>Excellent!</b> Din konsistens er på factory-nivå (Federal: ±0.05gr)<br>"
            elif charge_std < 0.1:
                html += (
                    "👍 <b>Good!</b> Din konsistens er akseptabel (Hornady: ±0.1gr)<br>"
                )
            else:
                html += (
                    "⚠️ <b>Poor!</b> Fabrikk-ammo er bedre. Sjekk powder thrower!<br>"
                )

        if "coal" in stats:
            coal_std = stats["coal"]["std"]
            if coal_std < 0.002:
                html += '✅ <b>Excellent COAL!</b> Match-grade presisjon (±0.002")<br>'
            elif coal_std < 0.005:
                html += '👍 <b>Good COAL!</b> Hunting-grade (±0.005")<br>'
            else:
                html += "⚠️ <b>Poor COAL!</b> Sjekk seating die setup!<br>"

        html += "</p>"

        return html

    def complete_batch(self):
        """Godkjenn batch"""
        if not self.current_batch_id:
            return

        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            UPDATE qc_batches
            SET status = 'approved', completed_date = ?
            WHERE id = ?
        """,
            (datetime.now().isoformat(), self.current_batch_id),
        )
        self.db.conn.commit()

        QMessageBox.information(
            self,
            "Batch godkjent",
            "✅ Batch godkjent og klar for bruk!\n\n"
            "Batch har passert QC og er production-ready.",
        )

        self.reset_ui()

    def reject_batch(self):
        """Avvis batch"""
        if not self.current_batch_id:
            return

        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            UPDATE qc_batches
            SET status = 'rejected', completed_date = ?
            WHERE id = ?
        """,
            (datetime.now().isoformat(), self.current_batch_id),
        )
        self.db.conn.commit()

        QMessageBox.warning(
            self,
            "Batch avvist",
            "❌ Batch avvist!\n\n"
            "For mange outliers eller QC-feil.\n"
            "Identifiser problem og lad på nytt.",
        )

        self.reset_ui()

    def reset_ui(self):
        """Reset UI etter batch completion"""
        self.current_batch_id = None
        self.btn_start_batch.setEnabled(True)
        self.btn_charge.setEnabled(False)
        self.btn_coal.setEnabled(False)
        self.btn_case.setEnabled(False)
        self.btn_analyze.setEnabled(False)
        self.btn_complete.setEnabled(False)
        self.btn_reject.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.label_status.setText("Status: Venter")
        self.label_status.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #7f8c8d;"
        )


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = BatchQCDashboard()
    window.show()
    sys.exit(app.exec())
