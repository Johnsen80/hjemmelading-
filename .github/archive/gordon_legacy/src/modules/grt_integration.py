"""
Reference and measurement integration for internal load data.
Collects predictions, pressure references, and actual measurements into our own loads.
"""

import json
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.i18n import tr
from ..utils.unit_preferences import (
    format_pressure_psi,
    format_velocity_fps,
    get_pressure_suffix,
    get_velocity_suffix,
)
from .load_data_service import build_profile_health_summary, build_reference_rows


def _health_color(level: str) -> QColor:
    level = str(level or "unknown").strip().lower()
    if level == "critical":
        return QColor("red")
    if level == "warning":
        return QColor("darkOrange")
    if level == "ok":
        return QColor("green")
    if level == "info":
        return QColor("blue")
    return QColor("gray")


class ReferenceDataIntegration(QWidget):
    """Widget for reference and measurement data."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_grt_profiles()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel("Reference & Measurement Data")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info om referansedata
        info = QLabel(
            f"""
        <b>What is this?</b><br>
        This is our combined overview of predictions, pressure references, and actual measurements:
        <ul>
            <li><b>Pressure</b>: Estimated max pressure in the selected pressure unit</li>
            <li><b>Velocity</b>: Predicted muzzle velocity in {get_velocity_suffix().strip()}</li>
            <li><b>Measurements</b>: Actual chrono and pressure traces</li>
            <li><b>Deviation</b>: The difference between predicted and measured</li>
        </ul>

        <b>How to use this view:</b><br>
        1. Build or import component and load data in Hjemmelading<br>
        2. Link predictions and references to our profiles<br>
        3. Record actual measurements in the same profile<br>
        4. Use the differences to improve your loads
        """
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            """
            background-color: #e7f3ff;
            border: 2px solid #2196F3;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0px;
        """
        )
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()

        import_btn = QPushButton("Import Reference Data")
        import_btn.setMinimumHeight(40)
        import_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold;"
        )
        import_btn.clicked.connect(self.import_reference_data)
        btn_layout.addWidget(import_btn)

        export_btn = QPushButton("Export Profile Data")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self.export_profile_data)
        btn_layout.addWidget(export_btn)

        analyze_btn = QPushButton("Analyze vs Actual Data")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.analyze_predictions_vs_actual)
        btn_layout.addWidget(analyze_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell med ladningsprofiler
        self.grt_table = QTableWidget()
        self.grt_table.setColumnCount(10)
        self.grt_table.setHorizontalHeaderLabels(
            [
                "Our Load",
                "Source",
                f"Predikert ({get_velocity_suffix().strip()})",
                f"Measured ({get_velocity_suffix().strip()})",
                f"Diff ({get_velocity_suffix().strip()})",
                f"Max Pressure ({get_pressure_suffix().strip()})",
                "Chrono",
                "Status",
                "Health",
                "Last Updated",
            ]
        )
        self.grt_table.horizontalHeader().setStretchLastSection(True)
        self.grt_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.grt_table)

        # Tips
        tips = QLabel(
            """
        <b>Tips:</b>
        <ul>
            <li>Use predicted pressure and measured velocity together, not separately</li>
            <li>A large difference between predicted and actual velocity often points to useful learning in the load</li>
            <li>Chrono and pressure traces should be tied to the same profile for best value</li>
            <li>This is our calibration workspace, not just an import view</li>
        </ul>
        """
        )
        tips.setWordWrap(True)
        layout.addWidget(tips)

    def load_grt_profiles(self):
        """Load reference and measurement data as our own load rows."""
        profiles = build_reference_rows(self.db)

        self.grt_table.setRowCount(len(profiles))

        for i, profile in enumerate(profiles):
            self.grt_table.setItem(i, 0, QTableWidgetItem(profile["name"]))
            self.grt_table.setItem(i, 1, QTableWidgetItem(profile["source_label"]))

            grt_vel = (
                format_velocity_fps(profile["predicted_velocity"])
                if profile["predicted_velocity"]
                else "-"
            )
            self.grt_table.setItem(i, 2, QTableWidgetItem(grt_vel))

            actual_vel = (
                format_velocity_fps(profile["velocity_fps"])
                if profile["velocity_fps"]
                else "-"
            )
            self.grt_table.setItem(i, 3, QTableWidgetItem(actual_vel))

            if profile["predicted_velocity"] and profile["velocity_fps"]:
                diff = profile["velocity_fps"] - profile["predicted_velocity"]
                diff_item = QTableWidgetItem(format_velocity_fps(diff))
                if abs(diff) < 30:
                    diff_item.setForeground(QColor("green"))
                elif abs(diff) < 60:
                    diff_item.setForeground(QColor("orange"))
                else:
                    diff_item.setForeground(QColor("red"))
                self.grt_table.setItem(i, 4, diff_item)
            else:
                self.grt_table.setItem(i, 4, QTableWidgetItem("-"))

            pressure = (
                format_pressure_psi(profile["max_pressure_psi"])
                if profile["max_pressure_psi"]
                else "-"
            )
            pressure_item = QTableWidgetItem(pressure)
            if profile["max_pressure_psi"]:
                if profile["max_pressure_psi"] > 60000:
                    pressure_item.setBackground(QColor(255, 200, 200))
                elif profile["max_pressure_psi"] > 55000:
                    pressure_item.setBackground(QColor(255, 255, 200))
                else:
                    pressure_item.setBackground(QColor(200, 255, 200))
            self.grt_table.setItem(i, 5, pressure_item)

            chrono_label = (
                f"{profile['evidence_summary'].get('chrono_count', 0)} chrono / "
                f"{profile['evidence_summary'].get('accuracy_count', 0)} pres."
                if isinstance(profile.get("evidence_summary"), dict)
                and (
                    profile["evidence_summary"].get("chrono_count")
                    or profile["evidence_summary"].get("accuracy_count")
                )
                else "-"
            )
            self.grt_table.setItem(i, 6, QTableWidgetItem(chrono_label))

            if profile.get("has_source_mismatch"):
                status = "Avvik i kildefil"
                status_color = QColor("red")
            else:
                status_text = str(profile.get("status_label") or "Profile")
                if status_text == "Verifisert hos oss":
                    status = "Verifisert hos oss"
                    status_color = QColor("green")
                elif status_text == "History shows risk":
                    status = "History shows risk"
                    status_color = QColor("red")
                elif status_text in {"Has reference + chrono", "Has measured data"}:
                    status = status_text
                    status_color = QColor("orange")
                elif status_text == "Has reference data":
                    status = "Has reference data"
                    status_color = QColor("orange")
                else:
                    status = "Profile"
                    status_color = QColor("gray")

            status_item = QTableWidgetItem(status)
            status_item.setForeground(status_color)
            self.grt_table.setItem(i, 7, status_item)

            evidence_summary = (
                profile.get("evidence_summary")
                if isinstance(profile.get("evidence_summary"), dict)
                else {}
            )
            health_summary = build_profile_health_summary(evidence_summary)
            health_level = str(health_summary.get("level") or "unknown")
            health_text = str(health_summary.get("summary") or "No health info yet")
            health_item = QTableWidgetItem(health_text)
            health_item.setForeground(_health_color(health_level))
            tooltip_parts = []
            if evidence_summary.get("evidence_label"):
                tooltip_parts.append(str(evidence_summary["evidence_label"]))
            if evidence_summary.get("trend_label"):
                tooltip_parts.append("Trend: " + str(evidence_summary["trend_label"]))
            projectile_label = str(
                evidence_summary.get("projectile_label") or ""
            ).strip()
            projectile_title = str(
                evidence_summary.get("projectile_title") or ""
            ).strip()
            if projectile_title:
                tooltip_parts.append("Projectile: " + projectile_title)
            elif projectile_label:
                tooltip_parts.append("Projectile: " + projectile_label)
            if tooltip_parts:
                health_item.setToolTip("\n".join(tooltip_parts))
            self.grt_table.setItem(i, 8, health_item)

            import_date = profile["import_date"] if profile["import_date"] else "-"
            self.grt_table.setItem(i, 9, QTableWidgetItem(import_date))

            self.grt_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, profile["id"])

    def import_reference_data(self):
        """Import reference data."""
        dialog = GRTImportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_grt_profiles()

    def export_profile_data(self):
        """Export profile data."""
        # Hent alle ammunisjonsprofiler
        profiles = self.db.get_all("ammo_profiles")

        if not profiles:
            QMessageBox.warning(
                self,
                "No profiles",
                "You do not have any ammunition profiles to export!",
            )
            return

        # Velg lagringsplass
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Profile Data",
            f"referanseexport_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON files (*.json);;CSV files (*.csv)",
        )

        if not file_path:
            return

        # Bygg eksportstruktur for videre analyse
        grt_export = []

        for profile in profiles:
            # Hent komponenter
            bullet = (
                self.db.get_by_id("bullets", profile["bullet_id"])
                if profile["bullet_id"]
                else None
            )
            powder = (
                self.db.get_by_id("powder", profile["powder_id"])
                if profile["powder_id"]
                else None
            )
            primer = (
                self.db.get_by_id("primers", profile["primer_id"])
                if profile["primer_id"]
                else None
            )
            case_data = (
                self.db.get_by_id("cases", profile["case_id"])
                if profile["case_id"]
                else None
            )

            grt_item = {
                "profile_name": profile["name"],
                "caliber": profile["caliber"],
                "bullet": {
                    "name": bullet["name"] if bullet else "",
                    "weight_grains": profile["bullet_weight"],
                    "diameter": None,
                    "length": None,
                    "construction_type": (
                        bullet.get("construction_type") if bullet else None
                    ),
                    "intended_use": bullet.get("intended_use") if bullet else None,
                    "minimum_expansion_fps": (
                        bullet.get("minimum_expansion_fps") if bullet else None
                    ),
                    "preferred_impact_min_fps": (
                        bullet.get("preferred_impact_min_fps") if bullet else None
                    ),
                    "preferred_impact_max_fps": (
                        bullet.get("preferred_impact_max_fps") if bullet else None
                    ),
                    "terminal_notes": bullet.get("terminal_notes") if bullet else None,
                },
                "powder": {
                    "name": powder["name"] if powder else "",
                    "charge_grains": profile["powder_charge"],
                    "type": powder["type"] if powder else None,
                },
                "primer": {
                    "name": primer["name"] if primer else "",
                    "type": primer["type"] if primer else "",
                },
                "case": {
                    "name": case_data["name"] if case_data else "",
                    "capacity": None,
                    "length": None,
                },
                "coal": profile["coal"],
                "actual_velocity": profile["velocity_fps"],
                "notes": profile["notes"],
            }

            grt_export.append(grt_item)

        # Lagre fil
        try:
            if file_path.endswith(".json"):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(grt_export, f, indent=2, ensure_ascii=False)
            else:  # CSV
                import csv

                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    if grt_export:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=[
                                "profile_name",
                                "caliber",
                                "bullet_weight",
                                "powder_name",
                                "powder_charge",
                                "coal",
                                "actual_velocity",
                            ],
                        )
                        writer.writeheader()
                        for item in grt_export:
                            writer.writerow(
                                {
                                    "profile_name": item["profile_name"],
                                    "caliber": item["caliber"],
                                    "bullet_weight": item["bullet"]["weight_grains"],
                                    "powder_name": item["powder"]["name"],
                                    "powder_charge": item["powder"]["charge_grains"],
                                    "coal": item["coal"],
                                    "actual_velocity": item["actual_velocity"],
                                }
                            )

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(grt_export)} profiles to:\n{file_path}\n\n"
                "You can now use this file in the analysis and reference workflow.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not export:\n{str(e)}")

    def analyze_predictions_vs_actual(self):
        """Analyze predictions vs actual results."""
        profiles = [
            row
            for row in build_reference_rows(self.db)
            if row.get("predicted_velocity") is not None
            and row.get("velocity_fps") is not None
        ]

        if not profiles:
            QMessageBox.information(
                self,
                tr("msg_no_data"),
                tr("grt_no_analysis_profiles"),
            )
            return

        # Åpne analyse-vindu
        dialog = GRTAnalysisDialog(self, profiles)
        dialog.exec()


class ReferenceImportDialog(QDialog):
    """Dialog for importing reference data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.setWindowTitle("Import Reference Data")
        self.setMinimumSize(700, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Forklaring
        info = QLabel(
            """
        <h3>How to import reference data:</h3>
        <ol>
            <li>Export or save reference data from the tool you use</li>
            <li>Run simulations or collect predictions for your loads</li>
            <li>Export the results (JSON recommended)</li>
            <li>Select the file below</li>
        </ol>

        <b>Expected format:</b> JSON or CSV with fields for bullet, powder, velocity, and pressure.
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Filvalg
        file_group = QGroupBox("1. Select Reference File")
        file_layout = QVBoxLayout()
        file_group.setLayout(file_layout)

        file_btn_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("No file selected...")
        self.file_path.setReadOnly(True)
        file_btn_layout.addWidget(self.file_path)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        file_btn_layout.addWidget(browse_btn)

        file_layout.addLayout(file_btn_layout)
        layout.addWidget(file_group)

        # Matching-strategi
        match_group = QGroupBox("2. Link to Existing Profiles")
        match_layout = QVBoxLayout()
        match_group.setLayout(match_layout)

        self.match_strategy = QComboBox()
        self.match_strategy.addItems(
            [
                "Match by name (exact)",
                "Match by name (fuzzy)",
                "Match by caliber + bullet weight + powder charge",
                "Create new profiles automatically",
            ]
        )
        match_layout.addWidget(QLabel("Matching strategy:"))
        match_layout.addWidget(self.match_strategy)

        layout.addWidget(match_group)

        # Preview
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(
            [
                "Reference Profile",
                f"Velocity ({get_velocity_suffix().strip()})",
                f"Pressure ({get_pressure_suffix().strip()})",
                "Fill %",
                "Matched To",
            ]
        )
        layout.addWidget(QLabel("3. Preview:"))
        layout.addWidget(self.preview_table)

        # Knapper
        btn_layout = QHBoxLayout()
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.do_import)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def browse_file(self):
        """Select a reference file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Reference File",
            "",
            "JSON files (*.json);;CSV files (*.csv);;All files (*.*)",
        )

        if file_path:
            self.file_path.setText(file_path)
            self.parse_and_preview(file_path)

    def parse_and_preview(self, file_path):
        """Parse and show preview."""
        try:
            if file_path.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                QMessageBox.warning(
                    self,
                    "Format Not Supported",
                    "Only JSON is supported for now. CSV is coming soon.",
                )
                return

            # Expected format (example):
            # [
            #   {
            #     "name": "6.5 CM ELD-M 140gr",
            #     "velocity_fps": 2750,
            #     "max_pressure_psi": 58000,
            #     "case_fill_percent": 98.5,
            #     ...
            #   }
            # ]

            if not isinstance(data, list):
                QMessageBox.warning(
                    self, "Invalid Format", "Expected a list of profiles."
                )
                return

            self.grt_data = data
            self.preview_table.setRowCount(len(data))

            for i, item in enumerate(data):
                # Reference profile name
                name = item.get("name", item.get("profile_name", f"Profile {i+1}"))
                self.preview_table.setItem(i, 0, QTableWidgetItem(name))

                # Velocity
                vel = item.get("velocity_fps", item.get("predicted_velocity", 0))
                self.preview_table.setItem(
                    i, 1, QTableWidgetItem(format_velocity_fps(vel))
                )

                # Trykk
                pressure = item.get("max_pressure_psi", item.get("pressure", 0))
                self.preview_table.setItem(
                    i, 2, QTableWidgetItem(format_pressure_psi(pressure))
                )

                # Fill
                fill = item.get("case_fill_percent", item.get("fill_ratio", 0))
                self.preview_table.setItem(i, 3, QTableWidgetItem(f"{fill:.1f}%"))

                # Find match
                match = self.find_matching_profile(item)
                match_text = match["name"] if match else "No match"
                match_item = QTableWidgetItem(match_text)
                if match:
                    match_item.setForeground(QColor("green"))
                else:
                    match_item.setForeground(QColor("red"))
                self.preview_table.setItem(i, 4, match_item)

            self.preview_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(
                self, "Parse Error", f"Could not read the file:\n{str(e)}"
            )

    def find_matching_profile(self, grt_item):
        """Finner matchende ammunisjonsprofil"""
        strategy = self.match_strategy.currentText()

        profiles = self.db.get_all("ammo_profiles")

        grt_name = grt_item.get("name", grt_item.get("profile_name", ""))

        if "exact" in strategy:
            # Exact name match
            for profile in profiles:
                if profile["name"].lower() == grt_name.lower():
                    return profile

        elif "caliber" in strategy:
            # Match on specs
            grt_caliber = grt_item.get("caliber", "")
            grt_bullet_weight = grt_item.get("bullet", {}).get("weight_grains", 0)
            grt_powder_charge = grt_item.get("powder", {}).get("charge_grains", 0)

            for profile in profiles:
                if (
                    profile["caliber"] == grt_caliber
                    and abs(profile["bullet_weight"] - grt_bullet_weight) < 1
                    and abs(profile["powder_charge"] - grt_powder_charge) < 0.5
                ):
                    return profile

        return None

    def do_import(self):
        """Run the import."""
        if not hasattr(self, "grt_data"):
            QMessageBox.warning(self, tr("msg_no_data"), tr("grt_select_file_first"))
            return

        imported = 0
        skipped = 0

        for item in self.grt_data:
            match = self.find_matching_profile(item)

            if match:
                # Update existing profile with reference data
                grt_record = {
                    "ammo_profile_id": match["id"],
                    "predicted_velocity": item.get(
                        "velocity_fps", item.get("predicted_velocity")
                    ),
                    "max_pressure_psi": item.get(
                        "max_pressure_psi", item.get("pressure")
                    ),
                    "case_fill_percent": item.get(
                        "case_fill_percent", item.get("fill_ratio")
                    ),
                    "predicted_accuracy_potential": item.get("accuracy_potential"),
                    "grt_data": json.dumps(item),
                    "import_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Check whether reference data already exists
                existing = self.db.execute_query(
                    "SELECT id FROM grt_data WHERE ammo_profile_id = ?", (match["id"],)
                )

                if existing:
                    self.db.update(
                        "grt_data", grt_record, "id = ?", (existing[0]["id"],)
                    )
                else:
                    self.db.insert("grt_data", grt_record)

                imported += 1
            else:
                skipped += 1

        QMessageBox.information(
            self,
            "Import Complete",
            f"Imported: {imported} profiles\n"
            f"Skipped (no match): {skipped} profiles\n\n"
            "Reference data is now linked to your ammunition profiles!",
        )

        self.accept()


class ReferenceAnalysisDialog(QDialog):
    """Dialog for analyzing predicted vs actual data."""

    def __init__(self, parent=None, profiles=None):
        super().__init__(parent)
        self.profiles = profiles or []
        self.setWindowTitle("Analysis: Predicted vs Actual")
        self.setMinimumSize(1000, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize the analysis window."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("<h2>Prediction vs Actual Results</h2>")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Velocity comparison
        tabs.addTab(self.create_velocity_tab(), "Velocity")

        # Tab 2: Pressure analysis
        tabs.addTab(self.create_pressure_tab(), "Pressure")

        # Tab 3: Accuracy
        tabs.addTab(self.create_accuracy_tab(), "Accuracy")

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def create_velocity_tab(self):
        """Velocity analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            """
        <b>Velocity Comparison:</b> How well do predictions match actual measurements?
        """
        )
        layout.addWidget(info)

        # Table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            [
                "Profile",
                f"Predicted Velocity ({get_velocity_suffix().strip()})",
                f"Actual Velocity ({get_velocity_suffix().strip()})",
                f"Difference ({get_velocity_suffix().strip()})",
                "Deviation %",
            ]
        )
        table.setRowCount(len(self.profiles))

        total_diff = 0

        for i, profile in enumerate(self.profiles):
            table.setItem(i, 0, QTableWidgetItem(profile["name"]))
            table.setItem(
                i,
                1,
                QTableWidgetItem(format_velocity_fps(profile["predicted_velocity"])),
            )
            table.setItem(
                i, 2, QTableWidgetItem(format_velocity_fps(profile["velocity_fps"]))
            )

            diff = profile["velocity_fps"] - profile["predicted_velocity"]
            diff_item = QTableWidgetItem(format_velocity_fps(diff))

            if abs(diff) < 30:
                diff_item.setBackground(QColor(200, 255, 200))
            elif abs(diff) < 60:
                diff_item.setBackground(QColor(255, 255, 200))
            else:
                diff_item.setBackground(QColor(255, 200, 200))

            table.setItem(i, 3, diff_item)

            pct = (diff / profile["predicted_velocity"]) * 100
            table.setItem(i, 4, QTableWidgetItem(f"{pct:+.1f}%"))

            total_diff += abs(diff)

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Statistics
        avg_diff = total_diff / len(self.profiles) if self.profiles else 0
        stats = QLabel(
            f"""
        <b>Statistics:</b><br>
        Average deviation: {format_velocity_fps(avg_diff)}<br>
        Number of profiles: {len(self.profiles)}
        """
        )
        layout.addWidget(stats)

        return widget

    def create_pressure_tab(self):
        """Pressure analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            f"""
        <b>Pressure Analysis:</b> The reference model calculates estimated max pressure. Compare it with pressure signs from shooting.
        Displayed here in {get_pressure_suffix().strip()}, even though internal thresholds are still evaluated on the standard basis.
        """
        )
        layout.addWidget(info)

        # Table
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(
            [
                "Profile",
                f"Estimated Max Pressure ({get_pressure_suffix().strip()})",
                "Fill %",
                "Status",
            ]
        )
        table.setRowCount(len(self.profiles))

        for i, profile in enumerate(self.profiles):
            table.setItem(i, 0, QTableWidgetItem(profile["name"]))

            pressure = profile["max_pressure_psi"]
            pressure_item = QTableWidgetItem(format_pressure_psi(pressure))

            # Color-coding against internal PSI thresholds, while displayed in the user's pressure unit
            if pressure > 62000:
                pressure_item.setBackground(QColor(255, 150, 150))
                status = "OVER SAAMI"
            elif pressure > 58000:
                pressure_item.setBackground(QColor(255, 220, 150))
                status = "High (check signs)"
            else:
                pressure_item.setBackground(QColor(200, 255, 200))
                status = "Safe zone"

            table.setItem(i, 1, pressure_item)
            table.setItem(
                i, 2, QTableWidgetItem(f"{profile['case_fill_percent']:.1f}%")
            )
            table.setItem(i, 3, QTableWidgetItem(status))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        warning = QLabel(
            """
        <b>Important:</b> Calculated pressure values are estimates. Always check for actual pressure signs:
        <ul>
            <li>Heavy primer opening</li>
            <li>Flattened primers</li>
            <li>Ejector marks</li>
            <li>Heavy bolt or action closing</li>
        </ul>
        """
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "background-color: #fff3cd; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(warning)

        return widget

    def create_accuracy_tab(self):
        """Accuracy analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            """
        <b>Accuracy Potential:</b> Some reference sets also estimate accuracy.
        Here you can see how that aligns with actual groups.
        """
        )
        layout.addWidget(info)

        note = QLabel(
            """
        <i>Note: Accuracy prediction is difficult. The model can provide hints, but actual shooting is required.</i>
        """
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()

        return widget


# Compatibility aliases kept temporarily while older imports are cleaned up.
GRTIntegration = ReferenceDataIntegration
GRTImportDialog = ReferenceImportDialog
GRTAnalysisDialog = ReferenceAnalysisDialog
