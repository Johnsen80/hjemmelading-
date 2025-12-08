"""
Database Setup Tool - Legger til eksempeldata via GUI
"""

import sqlite3
import sys

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class PopulateThread(QThread):
    progress = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def run(self):
        try:
            self.progress.emit("📂 Opening database...")
            conn = sqlite3.connect("data/reloading.db")
            c = conn.cursor()

            # Check current counts
            bullets_before = c.execute("SELECT COUNT(*) FROM bullets").fetchone()[0]
            powder_before = c.execute("SELECT COUNT(*) FROM powder").fetchone()[0]
            primers_before = c.execute("SELECT COUNT(*) FROM primers").fetchone()[0]

            self.progress.emit(
                f"Current: {bullets_before} bullets, {powder_before} powders, {primers_before} primers"
            )

            if bullets_before > 0:
                self.progress.emit("⚠️ Database already has data. Skipping...")
                self.finished_signal.emit(True, "Database already populated")
                conn.close()
                return

            self.progress.emit("\n🎯 Adding bullets...")
            bullets = [
                (
                    "Lapua Scenar 139gr",
                    "Lapua",
                    "6.5mm",
                    139,
                    0.615,
                    0.290,
                    "Match",
                    "Very consistent",
                ),
                (
                    "Berger 140gr Hybrid",
                    "Berger",
                    "6.5mm",
                    140,
                    0.618,
                    0.287,
                    "Match",
                    "Forgiving seating",
                ),
                (
                    "Sierra MatchKing 142gr",
                    "Sierra",
                    "6.5mm",
                    142,
                    0.626,
                    0.295,
                    "Match",
                    "Classic",
                ),
                (
                    "Hornady ELD-M 147gr",
                    "Hornady",
                    "6.5mm",
                    147,
                    0.697,
                    0.351,
                    "Match",
                    "High BC",
                ),
                (
                    "Sierra MatchKing 168gr",
                    "Sierra",
                    "7.62mm",
                    168,
                    0.462,
                    0.231,
                    "Match",
                    ".308 standard",
                ),
                (
                    "Berger 175gr OTM",
                    "Berger",
                    "7.62mm",
                    175,
                    0.505,
                    0.243,
                    "Match",
                    "Tactical",
                ),
                (
                    "Lapua Scenar 185gr",
                    "Lapua",
                    "7.62mm",
                    185,
                    0.525,
                    0.259,
                    "Match",
                    "High BC .308",
                ),
                (
                    "Sierra MatchKing 77gr",
                    "Sierra",
                    "5.56mm",
                    77,
                    0.372,
                    0.196,
                    "Match",
                    "AR-15 standard",
                ),
                (
                    "Berger 73gr BT",
                    "Berger",
                    "5.56mm",
                    73,
                    0.370,
                    0.193,
                    "Match",
                    "Accurate",
                ),
                (
                    "Hornady ELD-M 80.5gr",
                    "Hornady",
                    "5.56mm",
                    80.5,
                    0.395,
                    0.210,
                    "Match",
                    "High BC",
                ),
            ]

            for name, mfg, cal, weight, bc_g1, bc_g7, btype, notes in bullets:
                c.execute(
                    """INSERT INTO bullets (name, manufacturer, caliber, weight_grains,
                           bc_g1, bc_g7, bullet_type, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name, mfg, cal, weight, bc_g1, bc_g7, btype, notes),
                )

            self.progress.emit(f"  ✅ Added {len(bullets)} bullets")

            self.progress.emit("\n💨 Adding powder...")
            powders = [
                (
                    "H4350",
                    "Hodgdon",
                    "Extruded",
                    0.52,
                    "6.5 Creedmoor favorite, temp stable",
                ),
                (
                    "Varget",
                    "Hodgdon",
                    "Extruded",
                    0.53,
                    ".308 Win king, very versatile",
                ),
                ("RL16", "Alliant", "Extruded", 0.50, "Temp stable, modern powder"),
                ("RL26", "Alliant", "Extruded", 0.48, "Slow burner, max velocity"),
                (
                    "N140",
                    "Vihtavuori",
                    "Extruded",
                    0.910,
                    "Versatile .223 to .375 H&H, very clean",
                ),
                (
                    "N160",
                    "Vihtavuori",
                    "Extruded",
                    0.920,
                    "6.5-284, .270 Win, temp stable",
                ),
                (
                    "N540",
                    "Vihtavuori",
                    "Extruded",
                    0.940,
                    "High energy for 6.5 CM, .308",
                ),
                (
                    "N555",
                    "Vihtavuori",
                    "Extruded",
                    0.900,
                    "Developed for 6.5 Creedmoor comp",
                ),
                (
                    "Norma 204",
                    "Norma",
                    "Extruded",
                    0.55,
                    ".308 Win, 6.5x55 Swedish standard",
                ),
                ("IMR 4064", "IMR", "Extruded", 0.54, "Classic .308 powder"),
                ("H4895", "Hodgdon", "Extruded", 0.54, ".223 service rifle standard"),
            ]

            for name, mfg, ptype, dens, notes in powders:
                c.execute(
                    "INSERT INTO powder (name, manufacturer, type, density, notes) VALUES (?, ?, ?, ?, ?)",
                    (name, mfg, ptype, dens, notes),
                )

            self.progress.emit(f"  ✅ Added {len(powders)} powders")

            self.progress.emit("\n💥 Adding primers...")
            primers = [
                (
                    "CCI BR-2",
                    "Large Rifle Benchrest",
                    "CCI",
                    "Benchrest primer, very consistent",
                ),
                (
                    "Federal 210M",
                    "Large Rifle Match",
                    "Federal",
                    "Gold standard match primer",
                ),
                ("CCI 200", "Large Rifle", "CCI", "Standard large rifle"),
                ("CCI 250", "Large Rifle Magnum", "CCI", "Magnum primer"),
                ("CCI 450", "Small Rifle Magnum", "CCI", "For .223 compressed loads"),
                (
                    "Federal 205M",
                    "Small Rifle Match",
                    "Federal",
                    "Match primer for .223",
                ),
                ("CCI BR-4", "Small Rifle Benchrest", "CCI", "Benchrest small rifle"),
                ("CCI 41", "Small Rifle", "CCI", "Mil-spec AR-15 primer"),
            ]

            for name, ptype, mfg, notes in primers:
                c.execute(
                    "INSERT INTO primers (name, type, manufacturer, notes) VALUES (?, ?, ?, ?)",
                    (name, ptype, mfg, notes),
                )

            self.progress.emit(f"  ✅ Added {len(primers)} primers")

            conn.commit()
            conn.close()

            self.progress.emit("\n" + "=" * 50)
            self.progress.emit("✅ DATABASE POPULATED SUCCESSFULLY!")
            self.progress.emit("=" * 50)
            self.progress.emit("\nYou can now use Smart Loading Wizard!")
            self.finished_signal.emit(True, "Success!")

        except Exception as e:
            self.progress.emit(f"\n❌ ERROR: {str(e)}")
            self.finished_signal.emit(False, str(e))


class DatabaseSetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Setup - Hjemmelading")
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("🗄️ Database Setup Tool")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        info = QLabel(
            "Dette scriptet legger til eksempeldata i databasen:\n"
            "• Bullets (10 stk)\n"
            "• Powder (8 stk)\n"
            "• Primers (8 stk)\n\n"
            "Klikk 'Populate Database' for å starte."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet(
            "background-color: #1e1e1e; color: #00ff00; font-family: Consolas;"
        )
        layout.addWidget(self.log)

        self.btn_populate = QPushButton("Populate Database")
        self.btn_populate.clicked.connect(self.start_populate)
        self.btn_populate.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #4CAF50; color: white;"
        )
        layout.addWidget(self.btn_populate)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setEnabled(False)
        layout.addWidget(self.btn_close)

        self.setLayout(layout)

    def start_populate(self):
        self.btn_populate.setEnabled(False)
        self.log.clear()

        self.thread = PopulateThread()
        self.thread.progress.connect(self.log.append)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.start()

    def on_finished(self, success, message):
        self.btn_close.setEnabled(True)
        if success:
            self.log.append("\n✅ Done! Close this window and restart the program.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = DatabaseSetupDialog()
    dialog.exec()
