"""
Chronograph Auto-Import System
Støtter LabRadar, Garmin Xero, MagnetoSpeed
"""

import csv
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from HjemmeladingApp.utils.safe_logger import append_exception
from src.database.database import get_database
from src.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@dataclass
class ChronographReading:
    """En enkelt hastighets-måling"""

    shot_number: int
    velocity_fps: float
    timestamp: Optional[str] = None
    temperature: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class ChronographSession:
    """En komplett chrono-sesjon"""

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
        Parser LabRadar CSV format
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

            # Get session info from filename
            session_name = os.path.basename(file_path).replace(".csv", "")
            date = datetime.now().strftime("%Y-%m-%d")

            # Try to extract date from filename or data
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
        Parser Garmin Xero CSV format
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

                        # Remove any non-numeric characters except decimal point
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
        Parser MagnetoSpeed TXT/CSV format
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

                    # Look for velocity data
                    # Format: "Shot X: YYYY fps" or just numbers
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

                    # Try simple number format
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
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel("📊 Chronograph Auto-Import")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Import data fra LabRadar, Garmin Xero, MagnetoSpeed")
        subtitle.setStyleSheet("color: gray; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Device selector og import
        import_group = QGroupBox("📁 Import Data")
        import_layout = QHBoxLayout()
        import_group.setLayout(import_layout)

        self.device_combo = QComboBox()
        self.device_combo.addItems(
            ["LabRadar (CSV)", "Garmin Xero (CSV)", "MagnetoSpeed (TXT/CSV)"]
        )
        import_layout.addWidget(QLabel("Enhet:"))
        import_layout.addWidget(self.device_combo, 1)

        import_btn = QPushButton("📂 Velg fil og importer")
        import_btn.setMinimumHeight(40)
        import_btn.setStyleSheet(
            "font-size: 12pt; font-weight: bold; background-color: #4CAF50; color: white;"
        )
        import_btn.clicked.connect(self.import_file)
        import_layout.addWidget(import_btn)

        layout.addWidget(import_group)

        # Results display
        results_group = QGroupBox("📈 Import-resultat")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)

        layout.addWidget(results_group)

        # Shot data table
        table_group = QGroupBox("🎯 Skudd-data")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.shots_table = QTableWidget()
        self.shots_table.setColumnCount(4)
        self.shots_table.setHorizontalHeaderLabels(
            ["Skudd #", "Hastighet (fps)", "Tid", "Notater"]
        )
        table_layout.addWidget(self.shots_table)

        layout.addWidget(table_group)

        # Save section
        save_group = QGroupBox("💾 Lagre til ammunisjonsprofil")
        save_layout = QFormLayout()
        save_group.setLayout(save_layout)

        self.ammo_combo = QComboBox()
        self.ammo_combo.addItem("Velg ammunisjonsprofil...", None)
        self.load_ammo_profiles()
        save_layout.addRow("Ammunisjon:", self.ammo_combo)

        save_btn_layout = QHBoxLayout()

        update_velocity_btn = QPushButton("✅ Oppdater hastighet")
        update_velocity_btn.clicked.connect(self.update_ammo_velocity)
        save_btn_layout.addWidget(update_velocity_btn)

        save_session_btn = QPushButton("💾 Lagre sesjon")
        save_session_btn.clicked.connect(self.save_session)
        save_btn_layout.addWidget(save_session_btn)

        save_layout.addRow(save_btn_layout)

        layout.addWidget(save_group)

    def import_file(self):
        """Import fil fra chronograph"""
        device = self.device_combo.currentText()

        if "LabRadar" in device:
            file_filter = "CSV Files (*.csv);;All Files (*.*)"
        elif "Garmin" in device:
            file_filter = "CSV Files (*.csv);;All Files (*.*)"
        else:  # MagnetoSpeed
            file_filter = "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Velg chronograph-fil", "", file_filter
        )

        if not file_path:
            return

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
                "Import vellykket!",
                f"Importert {session.shot_count} skudd fra {session.device_type}\n\n"
                f"Gj.snitt: {session.avg_velocity:.1f} fps\n"
                f"ES: {session.es:.1f} fps\n"
                f"SD: {session.sd:.2f} fps",
            )
        else:
            QMessageBox.warning(
                self,
                "Import feilet",
                f"Kunne ikke lese data fra filen.\n\n"
                f"Sjekk at:\n"
                f"- Filen er riktig format for {device}\n"
                f"- Filen inneholder gyldige hastighets-data\n"
                f"- Filen ikke er korrupt",
            )

    def display_session(self, session: ChronographSession):
        """Viser sesjon-data"""
        # Results text
        results_html = f"""
<h3>📊 {session.device_type} - {session.session_name}</h3>
<p><b>Dato:</b> {session.date}</p>
<p><b>Antall skudd:</b> {session.shot_count}</p>

<h4>Statistikk:</h4>
<ul>
<li><b>Gjennomsnitt:</b> {session.avg_velocity:.1f} fps</li>
<li><b>Minimum:</b> {session.min_velocity:.1f} fps</li>
<li><b>Maksimum:</b> {session.max_velocity:.1f} fps</li>
<li><b>Extreme Spread (ES):</b> {session.es:.1f} fps</li>
<li><b>Standard Deviation (SD):</b> {session.sd:.2f} fps</li>
</ul>
"""

        if session.temperature:
            results_html += f"<p><b>Temperatur:</b> {session.temperature:.1f}°F</p>"

        self.results_text.setHtml(results_html)

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
        """Laster ammunisjonsprofiler"""
        ammos = self.db.execute_query(
            """
            SELECT id, name, caliber, velocity_fps
            FROM ammo_profiles
            ORDER BY name
        """
        )

        for row in ammos:
            ammo_id, name, caliber, velocity = row
            display = f"{name} ({caliber})" + (f" - {velocity} fps" if velocity else "")
            self.ammo_combo.addItem(display, ammo_id)

    def update_ammo_velocity(self):
        """Oppdaterer ammunisjonsprofil med ny hastighet"""
        if not self.current_session:
            QMessageBox.warning(self, "Ingen data", "Importer chronograph-data først!")
            return

        ammo_id = self.ammo_combo.currentData()
        if not ammo_id:
            QMessageBox.warning(self, "Ingen profil", "Velg ammunisjonsprofil!")
            return

        try:
            self.db.execute_query(
                """
                UPDATE ammo_profiles
                SET velocity_fps = ?
                WHERE id = ?
            """,
                (self.current_session.avg_velocity, ammo_id),
            )

            QMessageBox.information(
                self,
                "Oppdatert!",
                f"Ammunisjonsprofil oppdatert med ny hastighet:\n\n"
                f"{self.current_session.avg_velocity:.1f} fps\n"
                f"(ES: {self.current_session.es:.1f}, SD: {self.current_session.sd:.2f})",
            )

        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Kunne ikke oppdatere: {str(e)}")

    def save_session(self):
        """Lagrer hele sesjonen til database"""
        if not self.current_session:
            QMessageBox.warning(self, "Ingen data", "Importer chronograph-data først!")
            return

        # TODO: Implementer saving til dedicated chronograph_sessions table
        QMessageBox.information(
            self,
            "Funksjon kommer snart",
            "Full sesjon-lagring kommer i neste oppdatering.\n\n"
            "Bruk 'Oppdater hastighet' for å lagre gjennomsnittet til ammunisjonsprofilen.",
        )
