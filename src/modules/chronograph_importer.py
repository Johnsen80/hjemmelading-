"""
Chronograph Auto-Import System
Supports LabRadar, Garmin Xero, and MagnetoSpeed
"""

import csv
import hashlib
import importlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..logging_config import configure_logging, get_logger
from ..tools.load_session_runtime_service import (
    build_active_workflow_context_from_settings,
    refresh_load_session_measurement_summary,
)
from ..utils.i18n import tr
from ..utils.unit_preferences import format_temperature_c, format_velocity_fps
from .batch_workspace import recompute_batch_analysis_from_db

_safe_logger_module = importlib.import_module("HjemmeladingApp.utils.safe_logger")
append_exception = getattr(_safe_logger_module, "append_exception")

configure_logging()
logger = get_logger(__name__)


def _get_active_workflow_context() -> dict[str, object]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    try:
        database = get_database()
    except Exception:
        database = None
    return build_active_workflow_context_from_settings(settings, database)


def _get_active_import_focus() -> dict[str, str]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    focus = str(settings.value("workflow_context/import_focus", "") or "").strip()
    reason = str(
        settings.value("workflow_context/import_focus_reason", "") or ""
    ).strip()
    if not focus and not reason:
        return {}
    return {"focus": focus, "reason": reason}


def _get_global_unit_system() -> str:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return str(settings.value("units/global", "metric") or "metric").strip().lower()


def _format_velocity(fps_value: float) -> str:
    if _get_global_unit_system() == "metric":
        return format_velocity_fps(fps_value)
    return format_velocity_fps(fps_value)


def _format_temperature(temp_c: float | None) -> str:
    if temp_c is None:
        return "N/A"
    return format_temperature_c(temp_c)


def _get_active_batch_context() -> dict[str, object]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    batch_id = settings.value("batch_context/batch_id")
    if batch_id in (None, ""):
        return {}
    try:
        batch_id = int(batch_id)
    except Exception:
        pass
    powder_component_lot_id = settings.value("batch_context/powder_component_lot_id")
    try:
        powder_component_lot_id = (
            int(powder_component_lot_id)
            if powder_component_lot_id not in (None, "")
            else None
        )
    except Exception:
        powder_component_lot_id = None
    return {
        "batch_id": batch_id,
        "batch_number": str(
            settings.value("batch_context/batch_number", "") or ""
        ).strip(),
        "batch_name": str(settings.value("batch_context/batch_name", "") or "").strip(),
        "powder_id": settings.value("batch_context/powder_id"),
        "powder_name": str(
            settings.value("batch_context/powder_name", "") or ""
        ).strip(),
        "powder_lot_number": str(
            settings.value("batch_context/powder_lot_number", "") or ""
        ).strip(),
        "powder_component_lot_id": powder_component_lot_id,
    }


def build_chronograph_quality_summary(session: "ChronographSession") -> dict[str, str]:
    shot_count = int(session.shot_count or 0)
    es = float(session.es or 0.0)
    sd = float(session.sd or 0.0)

    if shot_count < 5:
        return {
            "level": "needs_more_data",
            "title": tr("chrono_quality_needs_more_title"),
            "message": tr("chrono_quality_needs_more_message"),
        }
    if es >= 40 or sd >= 15:
        return {
            "level": "unstable",
            "title": tr("chrono_quality_unstable_title"),
            "message": tr("chrono_quality_unstable_message"),
        }
    if es <= 20 and sd <= 8:
        return {
            "level": "ready",
            "title": tr("chrono_quality_ready_title"),
            "message": tr("chrono_quality_ready_message"),
        }
    return {
        "level": "watch",
        "title": tr("chrono_quality_watch_title"),
        "message": tr("chrono_quality_watch_message"),
    }


def build_chronograph_evidence_basis(session: "ChronographSession") -> dict[str, str]:
    measured_parts = [
        tr(
            "chrono_evidence_measured_shots",
            count=int(session.shot_count or 0),
            device=session.device_type or "chrono",
        ),
        tr("chrono_evidence_measured_es_sd"),
    ]
    if session.temperature is not None:
        measured_parts.append(tr("chrono_evidence_measured_temp"))

    modeled_parts = [
        tr("chrono_evidence_modeled"),
    ]

    recommended_parts = [
        tr("chrono_evidence_recommended_quality"),
    ]
    if int(session.shot_count or 0) < 5:
        recommended_parts.append(tr("chrono_evidence_recommended_more"))
    else:
        recommended_parts.append(tr("chrono_evidence_recommended_compare"))

    return {
        "title": tr("chrono_evidence_title"),
        "message": (
            f"{tr('evidence_measured')}: {', '.join(measured_parts)}. "
            f"{tr('evidence_modeled')}: {', '.join(modeled_parts)}. "
            f"{tr('evidence_recommended')}: {', '.join(recommended_parts)}."
        ),
    }


@dataclass
class ChronographReading:
    """A single velocity reading."""

    shot_number: int
    velocity_fps: float
    timestamp: Optional[str] = None
    temperature: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class ChronographSession:
    """A complete chronograph session."""

    device_type: str  # "LabRadar", "Garmin", "MagnetoSpeed"
    session_name: str
    date: str
    velocities: List[float]
    avg_velocity: float
    es: float  # Extreme Spread
    sd: float  # Standard Deviation
    min_velocity: float
    max_velocity: float
    shot_count: int
    raw_data: List[ChronographReading]
    temperature: Optional[float] = None
    notes: str = ""


class LabRadarImporter:
    """Import LabRadar CSV data"""

    @staticmethod
    def parse_csv(file_path: str) -> Optional[ChronographSession]:
        """
        Parse the LabRadar CSV format.
        Format: Series, Shot, V0, V0 Units, Time, Date, Temperature, etc.
        """
        try:
            readings = []
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")

                for row in reader:
                    try:
                        shot_num = int(row.get("Shot", 0))
                        velocity = float(row.get("V0", 0))
                        timestamp = row.get("Time", "")
                        temp = (
                            float(row.get("Temperature", 0))
                            if row.get("Temperature")
                            else None
                        )

                        if velocity > 0:  # Valid reading
                            readings.append(
                                ChronographReading(
                                    shot_number=shot_num,
                                    velocity_fps=velocity,
                                    timestamp=timestamp,
                                    temperature=temp,
                                )
                            )
                    except (ValueError, KeyError):
                        continue

            if not readings:
                return None

            # Calculate statistics
            velocities = [r.velocity_fps for r in readings]
            avg = sum(velocities) / len(velocities)
            es = max(velocities) - min(velocities)

            # Standard deviation
            variance = sum((v - avg) ** 2 for v in velocities) / len(velocities)
            sd = variance**0.5

            # Get session info from the filename
            session_name = os.path.basename(file_path).replace(".csv", "")
            date = datetime.now().strftime("%Y-%m-%d")

            # Try to extract the date from the filename or data
            if readings[0].timestamp:
                try:
                    date = readings[0].timestamp.split()[0]
                except Exception as e:
                    logger.exception("MagnetoSpeed parse error: %s", e)
                    try:
                        append_exception("MagnetoSpeed parse error", e)
                    except Exception:
                        pass

            return ChronographSession(
                device_type="LabRadar",
                session_name=session_name,
                date=date,
                velocities=velocities,
                avg_velocity=avg,
                es=es,
                sd=sd,
                min_velocity=min(velocities),
                max_velocity=max(velocities),
                shot_count=len(readings),
                raw_data=readings,
                temperature=readings[0].temperature if readings else None,
            )

        except Exception as e:
            logger.exception("LabRadar import error: %s", e)
            return None


class GarminXeroImporter:
    """Import Garmin Xero C1 data"""

    @staticmethod
    def parse_csv(file_path: str) -> Optional[ChronographSession]:
        """
        Parse the Garmin Xero CSV format.
        Format: Shot #, Velocity (fps), Timestamp
        """
        try:
            readings = []
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        # Garmin format variations
                        shot_num = int(row.get("Shot #", row.get("Shot", 0)))
                        velocity_str = row.get(
                            "Velocity (fps)", row.get("Velocity", "0")
                        )

                        # Remove any non-numeric characters except the decimal point
                        velocity_str = re.sub(r"[^\d.]", "", str(velocity_str))
                        velocity = float(velocity_str)

                        timestamp = row.get("Timestamp", row.get("Time", ""))

                        if velocity > 0:
                            readings.append(
                                ChronographReading(
                                    shot_number=shot_num,
                                    velocity_fps=velocity,
                                    timestamp=timestamp,
                                )
                            )
                    except (ValueError, KeyError) as e:
                        logger.debug("Row parse error: %s", e)
                        continue

            if not readings:
                return None

            velocities = [r.velocity_fps for r in readings]
            avg = sum(velocities) / len(velocities)
            es = max(velocities) - min(velocities)
            variance = sum((v - avg) ** 2 for v in velocities) / len(velocities)
            sd = variance**0.5

            session_name = os.path.basename(file_path).replace(".csv", "")
            date = datetime.now().strftime("%Y-%m-%d")

            return ChronographSession(
                device_type="Garmin Xero",
                session_name=session_name,
                date=date,
                velocities=velocities,
                avg_velocity=avg,
                es=es,
                sd=sd,
                min_velocity=min(velocities),
                max_velocity=max(velocities),
                shot_count=len(readings),
                raw_data=readings,
            )

        except Exception as e:
            logger.exception("Garmin import error: %s", e)
            return None


class MagnetoSpeedImporter:
    """Import MagnetoSpeed data"""

    @staticmethod
    def parse_txt(file_path: str) -> Optional[ChronographSession]:
        """
        Parse the MagnetoSpeed TXT/CSV format.
        Format: Shot, Velocity, etc.
        """
        try:
            readings = []

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                # Skip header lines
                _data_started = False
                shot_num = 0

                for line in lines:
                    line = line.strip()

                    if not line or line.startswith("#") or line.startswith("//"):
                        continue

                    # Look for velocity data.
                    # Format: "Shot X: YYYY fps" or just numbers.
                    velocity_match = re.search(
                        r"(\d+\.?\d*)\s*fps", line, re.IGNORECASE
                    )
                    if velocity_match:
                        velocity = float(velocity_match.group(1))
                        shot_num += 1
                        readings.append(
                            ChronographReading(
                                shot_number=shot_num, velocity_fps=velocity
                            )
                        )
                        continue

                    # Try a simple number format
                    try:
                        parts = line.split(",")
                        for part in parts:
                            part = part.strip()
                            if part.replace(".", "").isdigit():
                                velocity = float(part)
                                if 500 < velocity < 5000:  # Reasonable velocity range
                                    shot_num += 1
                                    readings.append(
                                        ChronographReading(
                                            shot_number=shot_num, velocity_fps=velocity
                                        )
                                    )
                    except ValueError:
                        continue

            if not readings:
                # Try CSV format
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        shot_num = 0
                        for row in reader:
                            for cell in row:
                                try:
                                    velocity = float(cell.strip())
                                    if 500 < velocity < 5000:
                                        shot_num += 1
                                        readings.append(
                                            ChronographReading(
                                                shot_number=shot_num,
                                                velocity_fps=velocity,
                                            )
                                        )
                                except ValueError:
                                    continue
                except Exception:
                    pass

            if not readings:
                return None

            velocities = [r.velocity_fps for r in readings]
            avg = sum(velocities) / len(velocities)
            es = max(velocities) - min(velocities)
            variance = sum((v - avg) ** 2 for v in velocities) / len(velocities)
            sd = variance**0.5

            session_name = (
                os.path.basename(file_path).replace(".txt", "").replace(".csv", "")
            )
            date = datetime.now().strftime("%Y-%m-%d")

            return ChronographSession(
                device_type="MagnetoSpeed",
                session_name=session_name,
                date=date,
                velocities=velocities,
                avg_velocity=avg,
                es=es,
                sd=sd,
                min_velocity=min(velocities),
                max_velocity=max(velocities),
                shot_count=len(readings),
                raw_data=readings,
            )

        except Exception as e:
            logger.exception("MagnetoSpeed import error: %s", e)
            return None


class ChronographImporter(QWidget):
    """Main chronograph import widget"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.current_session: Optional[ChronographSession] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self.setLayout(layout)

        # Title
        header = QFrame()
        header.setObjectName("sectionHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(4)

        title = QLabel(tr("chrono_import_title"))
        title.setObjectName("sectionTitle")
        header_layout.addWidget(title)

        subtitle = QLabel(tr("chrono_import_subtitle"))
        subtitle.setObjectName("sectionSubtitle")
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        import_focus = _get_active_import_focus()
        if import_focus.get("focus") == "workflow_data_capture":
            focus_text = import_focus.get("reason") or (
                tr("chrono_data_capture_reason")
            )
            self.focus_label = QLabel(f"{tr('chrono_data_capture')}: {focus_text}")
            self.focus_label.setObjectName("sectionSubtitle")
            self.focus_label.setWordWrap(True)
            self.focus_label.setStyleSheet(
                "background-color: #e8f4fd; color: #0b5394; border: 1px solid #9fc5e8; "
                "border-radius: 6px; padding: 8px;"
            )
            layout.addWidget(self.focus_label)

        self.quality_label = QLabel(tr("chrono_quality_intro"))
        self.quality_label.setWordWrap(True)
        self.quality_label.setStyleSheet(
            "background-color: #f5f5f5; color: #444; border: 1px solid #d9d9d9; "
            "border-radius: 6px; padding: 8px;"
        )
        layout.addWidget(self.quality_label)

        self.evidence_basis_label = QLabel(f"{tr('bw_evidence_basis')}: --")
        self.evidence_basis_label.setWordWrap(True)
        self.evidence_basis_label.setStyleSheet(
            "background-color: #f5f5f5; color: #444; border: 1px solid #d9d9d9; "
            "border-radius: 6px; padding: 8px;"
        )
        layout.addWidget(self.evidence_basis_label)

        # Device selector and import
        import_group = QGroupBox(tr("chrono_import_group"))
        import_layout = QVBoxLayout()
        import_group.setLayout(import_layout)

        device_row = QHBoxLayout()
        device_label = QLabel(tr("chrono_device"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(
            ["LabRadar (CSV)", "Garmin Xero (CSV)", "MagnetoSpeed (TXT/CSV)"]
        )
        device_row.addWidget(device_label)
        device_row.addWidget(self.device_combo, 1)
        import_layout.addLayout(device_row)

        file_row = QHBoxLayout()
        file_label = QLabel(tr("chrono_file"))
        self.file_path_input = QLineEdit()
        self.file_path_input.setObjectName("filePathInput")
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText(tr("chrono_no_file_selected"))
        import_btn = QPushButton(tr("chrono_import_button"))
        import_btn.setMinimumHeight(40)
        import_btn.setProperty("variant", "primary")
        import_btn.clicked.connect(self.import_file)
        file_row.addWidget(file_label)
        file_row.addWidget(self.file_path_input, 1)
        file_row.addWidget(import_btn)
        import_layout.addLayout(file_row)

        hint = QLabel(tr("chrono_file_hint"))
        hint.setObjectName("statLabel")
        import_layout.addWidget(hint)

        layout.addWidget(import_group)

        # Results display
        results_group = QGroupBox(tr("chrono_results"))
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)

        stats_row = QHBoxLayout()
        left_stats = QFormLayout()
        left_stats.setContentsMargins(0, 0, 0, 0)
        right_stats = QFormLayout()
        right_stats.setContentsMargins(0, 0, 0, 0)

        self.stat_fields = {}

        def add_stat(form: QFormLayout, label: str, key: str) -> None:
            label_widget = QLabel(label)
            label_widget.setObjectName("statLabel")
            value_widget = QLabel("--")
            value_widget.setObjectName("statValue")
            form.addRow(label_widget, value_widget)
            self.stat_fields[key] = value_widget

        add_stat(left_stats, "Device", "device")
        add_stat(left_stats, "Session", "session")
        add_stat(left_stats, "Date", "date")
        add_stat(left_stats, "Shot Count", "shots")
        add_stat(left_stats, "Temperature (F)", "temperature")

        add_stat(right_stats, "Average", "avg")
        add_stat(right_stats, "Minimum", "min")
        add_stat(right_stats, "Maximum", "max")
        add_stat(right_stats, "ES", "es")
        add_stat(right_stats, "SD", "sd")

        stats_row.addLayout(left_stats, 1)
        stats_row.addLayout(right_stats, 1)
        results_layout.addLayout(stats_row)

        layout.addWidget(results_group)

        # Shot data table
        table_group = QGroupBox(tr("chrono_shot_data"))
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.shots_table = QTableWidget()
        self.shots_table.setColumnCount(4)
        self.shots_table.setHorizontalHeaderLabels(
            ["Shot #", "Velocity (fps)", "Time", "Notes"]
        )
        self.shots_table.setAlternatingRowColors(True)
        self.shots_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.shots_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.shots_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.shots_table.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        table_layout.addWidget(self.shots_table)

        layout.addWidget(table_group)

        # Save section
        save_group = QGroupBox(tr("chrono_save_to_ammo"))
        save_layout = QFormLayout()
        save_group.setLayout(save_layout)

        self.ammo_combo = QComboBox()
        self.ammo_combo.addItem(tr("chrono_select_ammo"), None)
        self.load_ammo_profiles()
        save_layout.addRow("Ammunition:", self.ammo_combo)

        self.session_notes = QTextEdit()
        self.session_notes.setPlaceholderText(tr("chrono_session_notes"))
        self.session_notes.setMaximumHeight(120)
        save_layout.addRow("Notes:", self.session_notes)

        save_btn_layout = QHBoxLayout()

        update_velocity_btn = QPushButton(tr("chrono_update_velocity"))
        update_velocity_btn.setProperty("variant", "secondary")
        update_velocity_btn.clicked.connect(self.update_ammo_velocity)
        save_btn_layout.addWidget(update_velocity_btn)

        save_session_btn = QPushButton(tr("chrono_save_session"))
        save_session_btn.setProperty("variant", "primary")
        save_session_btn.clicked.connect(self.save_session)
        save_btn_layout.addWidget(save_session_btn)

        save_layout.addRow(save_btn_layout)

        layout.addWidget(save_group)

    def import_file(self):
        """Import a chronograph file."""
        device = self.device_combo.currentText()

        if "LabRadar" in device:
            file_filter = "CSV Files (*.csv);;All Files (*.*)"
        elif "Garmin" in device:
            file_filter = "CSV Files (*.csv);;All Files (*.*)"
        else:  # MagnetoSpeed
            file_filter = "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("chrono_choose_file"), "", file_filter
        )

        if not file_path:
            return

        self.file_path_input.setText(file_path)

        # Import based on device
        session = None

        if "LabRadar" in device:
            session = LabRadarImporter.parse_csv(file_path)
        elif "Garmin" in device:
            session = GarminXeroImporter.parse_csv(file_path)
        elif "MagnetoSpeed" in device:
            session = MagnetoSpeedImporter.parse_txt(file_path)

        if session:
            self.current_session = session
            self.display_session(session)
            QMessageBox.information(
                self,
                tr("chrono_import_success"),
                f"Imported {session.shot_count} shots from {session.device_type}\n\n"
                f"Average: {session.avg_velocity:.1f} fps\n"
                f"ES: {session.es:.1f} fps\n"
                f"SD: {session.sd:.2f} fps",
            )
        else:
            QMessageBox.warning(
                self,
                tr("chrono_import_failed"),
                f"Could not read data from the file.\n\n"
                f"Check that:\n"
                f"- The file format is correct for {device}\n"
                f"- The file contains valid velocity data\n"
                f"- The file is not corrupted",
            )

    def display_session(self, session: ChronographSession):
        """Display imported session data."""
        summary = build_chronograph_quality_summary(session)
        if hasattr(self, "quality_label"):
            self.quality_label.setText(f"{summary['title']}: {summary['message']}")
        if hasattr(self, "evidence_basis_label"):
            evidence_basis = build_chronograph_evidence_basis(session)
            self.evidence_basis_label.setText(
                f"{evidence_basis['title']}: {evidence_basis['message']}"
            )
        if "device" in self.stat_fields:
            self.stat_fields["device"].setText(session.device_type)
        if "session" in self.stat_fields:
            self.stat_fields["session"].setText(session.session_name)
        if "date" in self.stat_fields:
            self.stat_fields["date"].setText(session.date)
        if "shots" in self.stat_fields:
            self.stat_fields["shots"].setText(str(session.shot_count))
        if "temperature" in self.stat_fields:
            self.stat_fields["temperature"].setText(
                _format_temperature(session.temperature)
            )
        if "avg" in self.stat_fields:
            self.stat_fields["avg"].setText(_format_velocity(session.avg_velocity))
        if "min" in self.stat_fields:
            self.stat_fields["min"].setText(_format_velocity(session.min_velocity))
        if "max" in self.stat_fields:
            self.stat_fields["max"].setText(_format_velocity(session.max_velocity))
        if "es" in self.stat_fields:
            self.stat_fields["es"].setText(_format_velocity(session.es))
        if "sd" in self.stat_fields:
            self.stat_fields["sd"].setText(_format_velocity(session.sd))

        if hasattr(self, "session_notes"):
            if self.session_notes.toPlainText().strip() == "":
                self.session_notes.setPlainText(session.notes or "")

        # Table
        self.shots_table.setRowCount(len(session.raw_data))

        for idx, reading in enumerate(session.raw_data):
            self.shots_table.setItem(idx, 0, QTableWidgetItem(str(reading.shot_number)))
            self.shots_table.setItem(
                idx, 1, QTableWidgetItem(f"{reading.velocity_fps:.1f}")
            )
            self.shots_table.setItem(idx, 2, QTableWidgetItem(reading.timestamp or ""))
            self.shots_table.setItem(idx, 3, QTableWidgetItem(reading.notes or ""))

        self.shots_table.resizeColumnsToContents()

    def load_ammo_profiles(self):
        """Load ammunition profiles."""
        ammos = self.db.execute_query(
            """
            SELECT id, name, caliber, velocity_fps
            FROM ammo_profiles
            ORDER BY name
        """
        )

        for row in ammos:
            ammo_id = row.get("id")
            name = row.get("name")
            caliber = row.get("caliber")
            velocity = row.get("velocity_fps")
            if ammo_id is None or name is None:
                continue
            display = f"{name} ({caliber})" + (f" - {velocity} fps" if velocity else "")
            self.ammo_combo.addItem(display, ammo_id)

    def update_ammo_velocity(self):
        """Update the ammunition profile with the new velocity."""
        if not self.current_session:
            QMessageBox.warning(self, tr("msg_no_data"), tr("chrono_import_first"))
            return

        ammo_id = self.ammo_combo.currentData()
        if not ammo_id:
            QMessageBox.warning(self, tr("msg_no_selection"), tr("chrono_select_ammo"))
            return
        ammo_profile = self.db.get_by_id("ammo_profiles", ammo_id)
        if not ammo_profile:
            QMessageBox.warning(
                self,
                tr("chrono_profile_missing_title"),
                tr("chrono_profile_missing_message"),
            )
            return

        try:
            self.db.update(
                "ammo_profiles",
                {"velocity_fps": self.current_session.avg_velocity},
                "id = ?",
                (ammo_id,),
            )

            QMessageBox.information(
                self,
                tr("chrono_profile_updated_title"),
                tr(
                    "chrono_profile_updated_message",
                    velocity=self.current_session.avg_velocity,
                    es=self.current_session.es,
                    sd=self.current_session.sd,
                ),
            )

        except Exception as e:
            QMessageBox.critical(
                self, tr("msg_error"), tr("chrono_profile_update_failed", error=str(e))
            )

    def save_session(self):
        """Save the full session to the database."""
        if not self.current_session:
            QMessageBox.warning(self, tr("msg_no_data"), tr("chrono_import_first"))
            return

        if hasattr(self, "session_notes"):
            self.current_session.notes = self.session_notes.toPlainText().strip()

        ammo_id = self.ammo_combo.currentData()
        if ammo_id and not self.db.get_by_id("ammo_profiles", ammo_id):
            QMessageBox.warning(
                self,
                tr("chrono_profile_missing_title"),
                tr("chrono_profile_missing_message"),
            )
            return
        raw_payload = [
            {
                "shot_number": reading.shot_number,
                "velocity_fps": reading.velocity_fps,
                "timestamp": reading.timestamp,
                "temperature": reading.temperature,
                "notes": reading.notes,
            }
            for reading in self.current_session.raw_data
        ]
        raw_json = json.dumps(raw_payload, ensure_ascii=False)
        source_path = self.file_path_input.text().strip()
        source_file = os.path.basename(source_path) if source_path else None
        raw_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
        workflow_context = _get_active_workflow_context()
        batch_context = _get_active_batch_context()
        import_meta = {
            "imported_at": datetime.now().isoformat(timespec="seconds"),
            "source_file": source_file,
            "source_path": source_path or None,
            "device_type": self.current_session.device_type,
            "shot_count": self.current_session.shot_count,
            "raw_sha256": raw_hash,
            "workflow_context": workflow_context,
            "batch_context": batch_context,
        }

        session_id = self.db.insert(
            "chronograph_sessions",
            {
                "ammo_profile_id": ammo_id,
                "device_type": self.current_session.device_type,
                "session_name": self.current_session.session_name,
                "session_date": self.current_session.date,
                "avg_velocity_fps": self.current_session.avg_velocity,
                "es_fps": self.current_session.es,
                "sd_fps": self.current_session.sd,
                "min_velocity_fps": self.current_session.min_velocity,
                "max_velocity_fps": self.current_session.max_velocity,
                "shot_count": self.current_session.shot_count,
                "temperature_f": self.current_session.temperature,
                "notes": self.current_session.notes,
                "raw_data_json": raw_json,
                "import_source": source_file,
                "import_meta_json": json.dumps(import_meta, ensure_ascii=False),
            },
        )
        if session_id is None:
            QMessageBox.critical(
                self, "Error", "Could not save session: database insert failed."
            )
            return

        for reading in self.current_session.raw_data:
            self.db.insert(
                "chronograph_readings",
                {
                    "session_id": session_id,
                    "shot_number": reading.shot_number,
                    "velocity_fps": reading.velocity_fps,
                    "timestamp": reading.timestamp,
                    "temperature_f": reading.temperature,
                    "notes": reading.notes,
                },
            )

        rifle_id = workflow_context.get("rifle_id")
        if rifle_id in (None, "") and ammo_id:
            ammo_profile = self.db.get_by_id("ammo_profiles", int(ammo_id))
            rifle_id = ammo_profile.get("rifle_id") if ammo_profile else None
        try:
            rifle_id_int = int(rifle_id) if rifle_id not in (None, "") else None
        except Exception:
            rifle_id_int = None
        if rifle_id_int:
            self.db.record_barrel_chronograph_observation(
                rifle_id_int,
                workflow_context.get("barrel_id"),
                workflow_context.get("barrel_name"),
                {
                    "session_name": self.current_session.session_name,
                    "session_date": self.current_session.date,
                    "avg_velocity_fps": self.current_session.avg_velocity,
                    "es_fps": self.current_session.es,
                    "sd_fps": self.current_session.sd,
                    "temperature_f": self.current_session.temperature,
                },
                barrel_configuration_id=workflow_context.get("barrel_configuration_id"),
                barrel_configuration_name=workflow_context.get(
                    "barrel_configuration_name"
                ),
            )
        batch_id = batch_context.get("batch_id")
        if batch_id not in (None, ""):
            try:
                recompute_batch_analysis_from_db(self.db, batch_id)
            except Exception:
                pass
        refresh_load_session_measurement_summary(
            self.db,
            workflow_context.get("load_session_id"),
            source="chronograph_importer.save_session",
        )
        powder_component_lot_id = batch_context.get("powder_component_lot_id")
        if powder_component_lot_id not in (None, ""):
            try:
                self.db.refresh_powder_lot_learning_profile(
                    int(powder_component_lot_id)
                )
            except Exception:
                pass

        QMessageBox.information(
            self,
            "Session Saved",
            "The chronograph session was saved to the database.",
        )
