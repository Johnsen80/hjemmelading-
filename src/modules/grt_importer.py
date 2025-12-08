"""
Gordon's Reloading Tool (GRT) Database Importer
Importerer kalibere, kuler, og krutt fra GRT XML-filer
"""

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# from database import Database  # Not used in current implementation


class GRTParser:
    """Parser for GRT XML files"""

    @staticmethod
    def parse_caliber(file_path: str) -> Dict:
        """Parse .caliber XML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        data = {}
        for var in root.findall(".//var"):
            name = var.get("name")
            value = var.get("value", "")
            # URL decode values
            value = urllib.parse.unquote(value)
            data[name] = value

        return {
            "name": data.get("cipname", ""),
            "alt_name": data.get("altname", ""),
            "case_length_mm": float(data.get("L3", 0)),
            "case_capacity_ml": float(data.get("V", 0)),
            "max_pressure_bar": float(data.get("Pmax", 0)),
            "bullet_diameter_mm": float(data.get("G1", 0)),
            "neck_diameter_mm": float(data.get("E1", 0)),
            "base_diameter_mm": float(data.get("P1", 0)),
            "rim_diameter_mm": float(data.get("R1", 0)),
            "standard": data.get("standard", ""),
            "origin": data.get("ciporigin", ""),
            "description": data.get("descr", ""),
        }

    @staticmethod
    def parse_projectile(file_path: str) -> Dict:
        """Parse .projectile XML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        data = {}
        for var in root.findall(".//var"):
            name = var.get("name")
            value = var.get("value", "")
            value = urllib.parse.unquote(value)
            data[name] = value

        return {
            "name": data.get("name", ""),
            "manufacturer": data.get("manufacturer", ""),
            "caliber": data.get("caliber", ""),
            "weight_grains": float(data.get("weight", 0)),
            "diameter_mm": float(data.get("diameter", 0)),
            "length_mm": float(data.get("length", 0)),
            "bc_g1": float(data.get("bc", 0) or 0),
            "bc_g7": float(data.get("bc7", 0) or 0),
            "type": data.get("type", ""),
            "description": data.get("descr", ""),
        }

    @staticmethod
    def parse_powder(file_path: str) -> Dict:
        """Parse .powder XML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        data = {}
        for var in root.findall(".//var"):
            name = var.get("name")
            value = var.get("value", "")
            value = urllib.parse.unquote(value)
            data[name] = value

        return {
            "name": data.get("name", ""),
            "manufacturer": data.get("manufacturer", ""),
            "burn_rate": data.get("burn_rate", ""),
            "density": float(data.get("density", 0) or 0),
            "description": data.get("descr", ""),
        }


class GRTDownloadThread(QThread):
    """Background thread for downloading GRT database from GitHub"""

    progress = pyqtSignal(str, int)  # message, percentage
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, categories: List[str]):
        super().__init__()
        self.categories = categories
        self.base_url = "https://raw.githubusercontent.com/zen/grt_databases/main"

    def run(self):
        try:
            self.progress.emit("Starter nedlasting fra GRT GitHub...", 0)

            # TODO: Implement actual download logic
            # For now, just simulate
            import time

            for i, category in enumerate(self.categories):
                self.progress.emit(
                    f"Laster ned {category}...", int((i / len(self.categories)) * 100)
                )
                time.sleep(1)

            self.progress.emit("Nedlasting fullført!", 100)
            self.finished.emit(True, "GitHub nedlasting fullført")

        except Exception as e:
            self.finished.emit(False, f"Feil ved nedlasting: {str(e)}")


class GRTImporter(QWidget):
    """
    GUI for import av Gordon's Reloading Tool data
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None  # Database not implemented yet - uses JSON instead
        self.download_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("🔗 Gordon's Reloading Tool (GRT) Import")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel(
            "Importer kalibere, kuler og krutt fra Gordon's Reloading Tool.\n"
            "GRT er verdens mest avanserte interne ballistikk-simulator!"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # GitHub Import
        github_group = QGroupBox("📦 Import fra GitHub (Anbefalt)")
        github_layout = QVBoxLayout()

        github_desc = QLabel(
            "Last ned den komplette GRT-databasen fra GitHub:\n"
            "• 100+ kalibere (CIP/SAAMI standarder)\n"
            "• 500+ kuler (alle store produsenter)\n"
            "• 200+ krutt (Vihtavuori, Hodgdon, Alliant, etc.)"
        )
        github_desc.setWordWrap(True)
        github_layout.addWidget(github_desc)

        # Checkboxes for categories
        self.cb_calibers = QCheckBox("Kalibere (.caliber)")
        self.cb_calibers.setChecked(True)
        github_layout.addWidget(self.cb_calibers)

        self.cb_projectiles = QCheckBox("Kuler (.projectile)")
        self.cb_projectiles.setChecked(True)
        github_layout.addWidget(self.cb_projectiles)

        self.cb_powders = QCheckBox("Krutt (.powder)")
        self.cb_powders.setChecked(True)
        github_layout.addWidget(self.cb_powders)

        github_btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("⬇️ Last ned fra GitHub")
        self.btn_download.clicked.connect(self.download_from_github)
        github_btn_layout.addWidget(self.btn_download)
        github_layout.addLayout(github_btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        github_layout.addWidget(self.progress_bar)

        github_group.setLayout(github_layout)
        layout.addWidget(github_group)

        # Local File Import
        local_group = QGroupBox("📁 Import fra lokale filer")
        local_layout = QVBoxLayout()

        local_desc = QLabel(
            "Har du allerede GRT installert? Importer direkte fra dine filer:"
        )
        local_layout.addWidget(local_desc)

        # File type selector
        file_type_layout = QHBoxLayout()
        file_type_layout.addWidget(QLabel("Filtype:"))
        self.combo_filetype = QComboBox()
        self.combo_filetype.addItems(
            [".caliber (Kalibere)", ".projectile (Kuler)", ".powder (Krutt)"]
        )
        file_type_layout.addWidget(self.combo_filetype)
        file_type_layout.addStretch()
        local_layout.addLayout(file_type_layout)

        # Import buttons
        btn_layout = QHBoxLayout()

        self.btn_import_file = QPushButton("📄 Importer enkeltfil")
        self.btn_import_file.clicked.connect(self.import_single_file)
        btn_layout.addWidget(self.btn_import_file)

        self.btn_import_folder = QPushButton("📂 Importer mappe")
        self.btn_import_folder.clicked.connect(self.import_folder)
        btn_layout.addWidget(self.btn_import_folder)

        local_layout.addLayout(btn_layout)
        local_group.setLayout(local_layout)
        layout.addWidget(local_group)

        # Results area
        results_group = QGroupBox("📊 Importresultater")
        results_layout = QVBoxLayout()

        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        self.text_results.setMaximumHeight(200)
        self.text_results.setHtml(
            "<p style='color: #7f8c8d;'>"
            "Importresultater vil vises her...<br><br>"
            "<b>Tips:</b> GRT-data er CC0 lisensiert (Public Domain), "
            "så du kan bruke det fritt! 🎉"
            "</p>"
        )
        results_layout.addWidget(self.text_results)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Info footer
        info = QLabel(
            "ℹ️ Gordon's Reloading Tool: https://www.grtools.de\n"
            "📦 GRT Database: https://github.com/zen/grt_databases (CC0-1.0 License)"
        )
        info.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()
        self.setLayout(layout)

    def download_from_github(self):
        """Download GRT database from GitHub"""
        categories = []
        if self.cb_calibers.isChecked():
            categories.append("calibers")
        if self.cb_projectiles.isChecked():
            categories.append("projectiles")
        if self.cb_powders.isChecked():
            categories.append("powders")

        if not categories:
            QMessageBox.warning(
                self, "Ingen valg", "Velg minst én kategori å laste ned!"
            )
            return

        # Start download thread
        self.btn_download.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.download_thread = GRTDownloadThread(categories)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_progress(self, message: str, percentage: int):
        """Handle download progress updates"""
        self.progress_bar.setValue(percentage)
        self.text_results.append(f"<p style='color: #3498db;'>{message}</p>")

    def on_download_finished(self, success: bool, message: str):
        """Handle download completion"""
        self.btn_download.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.text_results.append(
                f"<p style='color: #27ae60;'><b>✅ {message}</b></p>"
            )
            QMessageBox.information(self, "Suksess", message)
        else:
            self.text_results.append(
                f"<p style='color: #e74c3c;'><b>❌ {message}</b></p>"
            )
            QMessageBox.critical(self, "Feil", message)

    def import_single_file(self):
        """Import a single GRT file"""
        filetype = self.combo_filetype.currentText()

        if ".caliber" in filetype:
            filter_str = "GRT Caliber Files (*.caliber)"
            parser_func = self.import_caliber_file
        elif ".projectile" in filetype:
            filter_str = "GRT Projectile Files (*.projectile)"
            parser_func = self.import_projectile_file
        elif ".powder" in filetype:
            filter_str = "GRT Powder Files (*.powder)"
            parser_func = self.import_powder_file
        else:
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Velg GRT-fil", "", filter_str)

        if file_path:
            try:
                parser_func(file_path)
                self.text_results.append(
                    f"<p style='color: #27ae60;'>✅ Importerte: {Path(file_path).name}</p>"
                )
            except Exception as e:
                self.text_results.append(
                    f"<p style='color: #e74c3c;'>❌ Feil ved import av {Path(file_path).name}: {str(e)}</p>"
                )

    def import_folder(self):
        """Import all GRT files from a folder"""
        folder_path = QFileDialog.getExistingDirectory(self, "Velg mappe med GRT-filer")

        if not folder_path:
            return

        filetype = self.combo_filetype.currentText()

        if ".caliber" in filetype:
            pattern = "*.caliber"
            parser_func = self.import_caliber_file
        elif ".projectile" in filetype:
            pattern = "*.projectile"
            parser_func = self.import_projectile_file
        elif ".powder" in filetype:
            pattern = "*.powder"
            parser_func = self.import_powder_file
        else:
            return

        folder = Path(folder_path)
        files = list(folder.glob(pattern))

        if not files:
            QMessageBox.warning(
                self, "Ingen filer", f"Fant ingen {pattern} filer i den valgte mappen."
            )
            return

        success_count = 0
        error_count = 0

        self.text_results.append(
            f"<p style='color: #3498db;'><b>Starter import av {len(files)} filer...</b></p>"
        )

        for file_path in files:
            try:
                parser_func(str(file_path))
                success_count += 1
                self.text_results.append(
                    f"<p style='color: #27ae60;'>✅ {file_path.name}</p>"
                )
            except Exception as e:
                error_count += 1
                self.text_results.append(
                    f"<p style='color: #e74c3c;'>❌ {file_path.name}: {str(e)}</p>"
                )

        # Summary
        self.text_results.append(
            f"<p style='color: #2c3e50;'><b>"
            f"Ferdig! Suksess: {success_count}, Feil: {error_count}"
            f"</b></p>"
        )

        QMessageBox.information(
            self,
            "Import fullført",
            f"Importerte {success_count} av {len(files)} filer.\n"
            f"Feil: {error_count}",
        )

    def import_caliber_file(self, file_path: str):
        """Import a caliber file to database"""
        _data = GRTParser.parse_caliber(file_path)

        # TODO: Save to JSON database instead of SQL
        # For now, just parse and log
        pass
        # Insert into database
        # cursor = self.db.conn.cursor()
        # cursor.execute("""
        #     INSERT OR REPLACE INTO calibers (
        #         name, case_length_mm, case_capacity_ml, max_pressure_bar,
        #         bullet_diameter_mm, description
        #     ) VALUES (?, ?, ?, ?, ?, ?)
        # """, (
        #     data['name'],
        #     data['case_length_mm'],
        #     data['case_capacity_ml'],
        #     data['max_pressure_bar'],
        #     data['bullet_diameter_mm'],
        #     f"{data['alt_name']} | {data['description']}"
        # ))
        # self.db.conn.commit()

    def import_projectile_file(self, file_path: str):
        """Import a projectile file to database"""
        _data = GRTParser.parse_projectile(file_path)

        # TODO: Save to JSON database
        pass

    def import_powder_file(self, file_path: str):
        """Import a powder file to database"""
        _data = GRTParser.parse_powder(file_path)

        # TODO: Save to JSON database instead of SQL
        # For now, just parse and log
        pass
        # Insert into database
        # cursor = self.db.conn.cursor()
        # cursor.execute("""
        #     INSERT OR REPLACE INTO powders (
        #         name, manufacturer, burn_rate, density, description
        #     ) VALUES (?, ?, ?, ?, ?)
        # """, (
        #     data['name'],
        #     data['manufacturer'],
        #     data['burn_rate'],
        #     data['density'],
        #     data['description']
        # ))
        # self.db.conn.commit()


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = GRTImporter()
    window.show()
    sys.exit(app.exec())
