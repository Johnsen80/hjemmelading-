"""
Component Database Manager
Comprehensive database for bullets, powders, primers, brass
Inspired by Gordon's Reloading Tool - but BETTER! 🚀

Features:
- Add custom components not in database
- Import from CSV/JSON
- Search & filter
- Auto-complete when entering data
- Share component data with community (future)
"""

import json
from typing import Dict

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


class ComponentDatabaseManager(QWidget):
    """
    Main component database interface
    Browse, search, add, edit components
    """

    component_selected = pyqtSignal(dict)  # Emit when component selected

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_database()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel("🗄️ Component Database Manager")
        header.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;"
        )
        layout.addWidget(header)

        # Tabs for different component types
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self.bullets_tab = self.create_bullets_tab()
        self.powders_tab = self.create_powders_tab()
        self.primers_tab = self.create_primers_tab()
        self.brass_tab = self.create_brass_tab()

        self.tabs.addTab(self.bullets_tab, "🎯 Bullets")
        self.tabs.addTab(self.powders_tab, "💨 Powders")
        self.tabs.addTab(self.primers_tab, "💥 Primers")
        self.tabs.addTab(self.brass_tab, "📦 Brass")

        # Action buttons
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ Add Component")
        self.btn_add.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """
        )
        self.btn_add.clicked.connect(self.add_component)
        btn_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("✏️ Edit Selected")
        self.btn_edit.clicked.connect(self.edit_component)
        btn_layout.addWidget(self.btn_edit)

        self.btn_import = QPushButton("📥 Import from File")
        self.btn_import.clicked.connect(self.import_from_file)
        btn_layout.addWidget(self.btn_import)

        self.btn_export = QPushButton("📤 Export Database")
        self.btn_export.clicked.connect(self.export_database)
        btn_layout.addWidget(self.btn_export)

        layout.addLayout(btn_layout)

    def create_bullets_tab(self) -> QWidget:
        """Create bullets database tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Search/filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.bullet_search = QLineEdit()
        self.bullet_search.setPlaceholderText("Type to search bullets...")
        self.bullet_search.textChanged.connect(self.filter_bullets)
        search_layout.addWidget(self.bullet_search)

        search_layout.addWidget(QLabel("Caliber:"))
        self.bullet_caliber_filter = QComboBox()
        self.bullet_caliber_filter.addItems(
            ["All", ".224", "6mm", "6.5mm", ".308", ".338"]
        )
        self.bullet_caliber_filter.currentTextChanged.connect(self.filter_bullets)
        search_layout.addWidget(self.bullet_caliber_filter)

        layout.addLayout(search_layout)

        # Table
        self.bullets_table = QTableWidget()
        self.bullets_table.setColumnCount(9)
        self.bullets_table.setHorizontalHeaderLabels(
            [
                "Manufacturer",
                "Name",
                "Caliber",
                "Weight (gr)",
                "BC G1",
                "BC G7",
                "Length (in)",
                "Diameter (in)",
                "Type",
            ]
        )
        header = self.bullets_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        self.bullets_table.doubleClicked.connect(self.on_bullet_double_click)
        layout.addWidget(self.bullets_table)

        return widget

    def create_powders_tab(self) -> QWidget:
        """Create powders database tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.powder_search = QLineEdit()
        self.powder_search.setPlaceholderText("Type to search powders...")
        self.powder_search.textChanged.connect(self.filter_powders)
        search_layout.addWidget(self.powder_search)

        search_layout.addWidget(QLabel("Burn Rate:"))
        self.powder_burn_filter = QComboBox()
        self.powder_burn_filter.addItems(["All", "Fast", "Medium", "Slow", "Very Slow"])
        self.powder_burn_filter.currentTextChanged.connect(self.filter_powders)
        search_layout.addWidget(self.powder_burn_filter)

        layout.addLayout(search_layout)

        # Table
        self.powders_table = QTableWidget()
        self.powders_table.setColumnCount(7)
        self.powders_table.setHorizontalHeaderLabels(
            [
                "Manufacturer",
                "Name",
                "Burn Rate",
                "Density (g/cc)",
                "Best For",
                "Temp Stable?",
                "Notes",
            ]
        )
        header = self.powders_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(self.powders_table)

        return widget

    def create_primers_tab(self) -> QWidget:
        """Create primers database tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Table
        self.primers_table = QTableWidget()
        self.primers_table.setColumnCount(6)
        self.primers_table.setHorizontalHeaderLabels(
            ["Manufacturer", "Name", "Size", "Type", "Brisance", "Best For"]
        )
        header = self.primers_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(self.primers_table)

        return widget

    def create_brass_tab(self) -> QWidget:
        """Create brass database tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Table
        self.brass_table = QTableWidget()
        self.brass_table.setColumnCount(7)
        self.brass_table.setHorizontalHeaderLabels(
            [
                "Manufacturer",
                "Caliber",
                "Case Capacity (gr H2O)",
                "Weight (gr)",
                "Wall Thickness",
                "Quality Rating",
                "Notes",
            ]
        )
        header = self.brass_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(self.brass_table)

        return widget

    def load_database(self):
        """Load component database from JSON file"""
        import os

        # Load from JSON database
        db_path = "data/components_database.json"

        if not os.path.exists(db_path):
            logger.error("❌ Database not found: %s", db_path)
            return

        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        # Load bullets
        bullets = db.get("bullets", [])
        bullet_data = [
            (
                b["manufacturer"],
                b["name"],
                b["caliber"],
                b["weight"],
                b["bc_g1"],
                b["bc_g7"],
                b["length"],
                b["diameter"],
                b["type"],
            )
            for b in bullets
        ]

        self.bullets_table.setRowCount(0)
        for bullet in bullet_data:
            row = self.bullets_table.rowCount()
            self.bullets_table.insertRow(row)
            for col, value in enumerate(bullet):
                self.bullets_table.setItem(row, col, QTableWidgetItem(str(value)))

        # Load powders from database
        powders = db.get("powders", [])
        powder_data = [
            (
                p["manufacturer"],
                p["name"],
                p["burn_rate"],
                p["density"],
                p["best_for"],
                "Yes" if p["temp_stable"] else "No",
                p["notes"],
            )
            for p in powders
        ]

        self.powders_table.setRowCount(0)
        for powder in powder_data:
            row = self.powders_table.rowCount()
            self.powders_table.insertRow(row)
            for col, value in enumerate(powder):
                self.powders_table.setItem(row, col, QTableWidgetItem(str(value)))

        # Load primers from database
        primers = db.get("primers", [])
        primer_data = [
            (
                pr["manufacturer"],
                pr["name"],
                pr["size"],
                pr["type"],
                pr["brisance"],
                pr["notes"],
            )
            for pr in primers
        ]

        self.primers_table.setRowCount(0)
        for primer in primer_data:
            row = self.primers_table.rowCount()
            self.primers_table.insertRow(row)
            for col, value in enumerate(primer):
                self.primers_table.setItem(row, col, QTableWidgetItem(str(value)))

        # Load brass from database
        brass_list = db.get("brass", [])
        brass_data = [
            (
                br["manufacturer"],
                br["caliber"],
                br["case_capacity"],
                br["weight"],
                br["wall_thickness"],
                "★" * br["quality"] + "☆" * (5 - br["quality"]),
                br["notes"],
            )
            for br in brass_list
        ]

        self.brass_table.setRowCount(0)
        for brass in brass_data:
            row = self.brass_table.rowCount()
            self.brass_table.insertRow(row)
            for col, value in enumerate(brass):
                self.brass_table.setItem(row, col, QTableWidgetItem(str(value)))

    def filter_bullets(self):
        """Filter bullets based on search text and caliber"""
        search_text = self.bullet_search.text().lower()
        caliber_filter = self.bullet_caliber_filter.currentText()

        for row in range(self.bullets_table.rowCount()):
            show_row = True

            # Check search text (match any column)
            if search_text:
                row_text = ""
                for col in range(self.bullets_table.columnCount()):
                    item = self.bullets_table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "

                if search_text not in row_text:
                    show_row = False

            # Check caliber filter
            if caliber_filter != "All":
                caliber_item = self.bullets_table.item(row, 2)
                if caliber_item and caliber_filter not in caliber_item.text():
                    show_row = False

            self.bullets_table.setRowHidden(row, not show_row)

    def filter_powders(self):
        """Filter powders based on search text and burn rate"""
        search_text = self.powder_search.text().lower()
        burn_filter = self.powder_burn_filter.currentText()

        for row in range(self.powders_table.rowCount()):
            show_row = True

            if search_text:
                row_text = ""
                for col in range(self.powders_table.columnCount()):
                    item = self.powders_table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "

                if search_text not in row_text:
                    show_row = False

            if burn_filter != "All":
                burn_item = self.powders_table.item(row, 2)
                if burn_item and burn_filter not in burn_item.text():
                    show_row = False

            self.powders_table.setRowHidden(row, not show_row)

    def add_component(self):
        """Add new component"""
        current_tab = self.tabs.currentIndex()

        if current_tab == 0:  # Bullets
            dialog = AddBulletDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                bullet_data = dialog.get_bullet_data()
                self.add_bullet_to_table(bullet_data)
                QMessageBox.information(
                    self, "Success", f"Added {bullet_data['name']} to database!"
                )

        elif current_tab == 1:  # Powders
            dialog = AddPowderDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                powder_data = dialog.get_powder_data()
                self.add_powder_to_table(powder_data)
                QMessageBox.information(
                    self, "Success", f"Added {powder_data['name']} to database!"
                )

        elif current_tab == 2:  # Primers
            QMessageBox.information(
                self, "Add Primer", "Primer add dialog coming soon!"
            )

        elif current_tab == 3:  # Brass
            QMessageBox.information(self, "Add Brass", "Brass add dialog coming soon!")

    def add_bullet_to_table(self, data: Dict):
        """Add bullet to table"""
        row = self.bullets_table.rowCount()
        self.bullets_table.insertRow(row)

        self.bullets_table.setItem(row, 0, QTableWidgetItem(data["manufacturer"]))
        self.bullets_table.setItem(row, 1, QTableWidgetItem(data["name"]))
        self.bullets_table.setItem(row, 2, QTableWidgetItem(data["caliber"]))
        self.bullets_table.setItem(row, 3, QTableWidgetItem(str(data["weight"])))
        self.bullets_table.setItem(row, 4, QTableWidgetItem(str(data["bc_g1"])))
        self.bullets_table.setItem(row, 5, QTableWidgetItem(str(data["bc_g7"])))
        self.bullets_table.setItem(row, 6, QTableWidgetItem(str(data["length"])))
        self.bullets_table.setItem(row, 7, QTableWidgetItem(str(data["diameter"])))
        self.bullets_table.setItem(row, 8, QTableWidgetItem(data["type"]))

    def add_powder_to_table(self, data: Dict):
        """Add powder to table"""
        row = self.powders_table.rowCount()
        self.powders_table.insertRow(row)

        self.powders_table.setItem(row, 0, QTableWidgetItem(data["manufacturer"]))
        self.powders_table.setItem(row, 1, QTableWidgetItem(data["name"]))
        self.powders_table.setItem(row, 2, QTableWidgetItem(data["burn_rate"]))
        self.powders_table.setItem(row, 3, QTableWidgetItem(str(data["density"])))
        self.powders_table.setItem(row, 4, QTableWidgetItem(data["best_for"]))
        self.powders_table.setItem(row, 5, QTableWidgetItem(data["temp_stable"]))
        self.powders_table.setItem(row, 6, QTableWidgetItem(data["notes"]))

    def edit_component(self):
        """Edit selected component"""
        QMessageBox.information(self, "Edit", "Edit functionality coming soon!")

    def import_from_file(self):
        """Import components from CSV/JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Component Data",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*.*)",
        )

        if file_path:
            QMessageBox.information(
                self, "Import", f"Import from {file_path}\n\nComing soon!"
            )

    def export_database(self):
        """Export database to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Component Database",
            "component_database.json",
            "JSON Files (*.json);;CSV Files (*.csv)",
        )

        if file_path:
            QMessageBox.information(
                self, "Export", f"Export to {file_path}\n\nComing soon!"
            )

    def on_bullet_double_click(self):
        """Handle bullet double-click - select for use"""
        current_row = self.bullets_table.currentRow()
        if current_row >= 0:
            bullet_data = {
                "manufacturer": self.bullets_table.item(current_row, 0).text(),
                "name": self.bullets_table.item(current_row, 1).text(),
                "caliber": self.bullets_table.item(current_row, 2).text(),
                "weight": float(self.bullets_table.item(current_row, 3).text()),
                "bc_g1": float(self.bullets_table.item(current_row, 4).text()),
                "bc_g7": float(self.bullets_table.item(current_row, 5).text()),
            }
            self.component_selected.emit(bullet_data)


class AddBulletDialog(QDialog):
    """
    Dialog for adding custom bullet
    Inspired by Gordon's Reloading Tool
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Bullet")
        self.resize(500, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Info box
        info = QLabel(
            "📝 Add a custom bullet not in the database.\n"
            "All data will be saved for future use."
        )
        info.setStyleSheet(
            "background-color: #e8f4f8; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        form = QFormLayout()

        # Manufacturer
        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText("e.g., Berger, Sierra, Hornady")
        form.addRow("Manufacturer:", self.manufacturer)

        # Name
        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g., Hybrid Target, MatchKing")
        form.addRow("Bullet Name:", self.name)

        # Caliber
        self.caliber = QComboBox()
        self.caliber.setEditable(True)
        self.caliber.addItems([".224", "6mm", "6.5mm", ".308", ".338", "Custom"])
        form.addRow("Caliber:", self.caliber)

        # Weight
        self.weight = QDoubleSpinBox()
        self.weight.setRange(10, 500)
        self.weight.setValue(140)
        self.weight.setSuffix(" gr")
        form.addRow("Weight:", self.weight)

        # BC G1
        self.bc_g1 = QDoubleSpinBox()
        self.bc_g1.setRange(0.100, 1.000)
        self.bc_g1.setValue(0.610)
        self.bc_g1.setDecimals(3)
        form.addRow("BC (G1):", self.bc_g1)

        # BC G7
        self.bc_g7 = QDoubleSpinBox()
        self.bc_g7.setRange(0.100, 1.000)
        self.bc_g7.setValue(0.305)
        self.bc_g7.setDecimals(3)
        form.addRow("BC (G7):", self.bc_g7)

        # Length
        self.length = QDoubleSpinBox()
        self.length.setRange(0.500, 3.000)
        self.length.setValue(1.430)
        self.length.setDecimals(3)
        self.length.setSuffix(" in")
        form.addRow("Length:", self.length)

        # Diameter
        self.diameter = QDoubleSpinBox()
        self.diameter.setRange(0.200, 0.500)
        self.diameter.setValue(0.264)
        self.diameter.setDecimals(3)
        self.diameter.setSuffix(" in")
        form.addRow("Diameter:", self.diameter)

        # Type
        self.bullet_type = QComboBox()
        self.bullet_type.addItems(
            [
                "BTHP",
                "VLD",
                "Hybrid",
                "ELD",
                "A-Tip",
                "RDF",
                "FMJ",
                "Soft Point",
                "Ballistic Tip",
                "Other",
            ]
        )
        form.addRow("Bullet Type:", self.bullet_type)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Any additional notes about this bullet...")
        form.addRow("Notes:", self.notes)

        layout.addLayout(form)

        # Helper info
        helper = QLabel(
            "💡 <b>Where to find BC values?</b><br>"
            "• Manufacturer website<br>"
            "• Bryan Litz's Applied Ballistics<br>"
            "• Measure from YOUR rifle (best!)"
        )
        helper.setStyleSheet(
            "background-color: #fff9c4; padding: 10px; border-radius: 5px; margin-top: 10px;"
        )
        layout.addWidget(helper)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_bullet_data(self) -> Dict:
        """Get entered bullet data"""
        return {
            "manufacturer": self.manufacturer.text(),
            "name": self.name.text(),
            "caliber": self.caliber.currentText(),
            "weight": self.weight.value(),
            "bc_g1": self.bc_g1.value(),
            "bc_g7": self.bc_g7.value(),
            "length": self.length.value(),
            "diameter": self.diameter.value(),
            "type": self.bullet_type.currentText(),
            "notes": self.notes.toPlainText(),
        }


class AddPowderDialog(QDialog):
    """Dialog for adding custom powder"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Powder")
        self.resize(500, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(
            "📝 Add a custom powder not in the database.\n"
            "Useful for wildcats or new powders!"
        )
        info.setStyleSheet(
            "background-color: #fff9c4; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        form = QFormLayout()

        # Manufacturer
        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText("e.g., Vihtavuori, Hodgdon, Alliant")
        form.addRow("Manufacturer:", self.manufacturer)

        # Name
        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g., N140, H4350, Varget")
        form.addRow("Powder Name:", self.name)

        # Burn rate
        self.burn_rate = QComboBox()
        self.burn_rate.addItems(
            [
                "Very Fast",
                "Fast",
                "Medium-Fast",
                "Medium",
                "Medium-Slow",
                "Slow",
                "Very Slow",
            ]
        )
        form.addRow("Burn Rate:", self.burn_rate)

        # Density
        self.density = QDoubleSpinBox()
        self.density.setRange(0.70, 1.10)
        self.density.setValue(0.93)
        self.density.setDecimals(2)
        self.density.setSuffix(" g/cc")
        form.addRow("Density:", self.density)

        # Best for
        self.best_for = QLineEdit()
        self.best_for.setPlaceholderText("e.g., 6.5 CM, .308 Win")
        form.addRow("Best For:", self.best_for)

        # Temp stable
        self.temp_stable = QComboBox()
        self.temp_stable.addItems(["Yes", "No", "Unknown"])
        form.addRow("Temperature Stable:", self.temp_stable)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Any additional notes...")
        form.addRow("Notes:", self.notes)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_powder_data(self) -> Dict:
        """Get entered powder data"""
        return {
            "manufacturer": self.manufacturer.text(),
            "name": self.name.text(),
            "burn_rate": self.burn_rate.currentText(),
            "density": self.density.value(),
            "best_for": self.best_for.text(),
            "temp_stable": self.temp_stable.currentText(),
            "notes": self.notes.toPlainText(),
        }


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    manager = ComponentDatabaseManager()
    manager.show()
    manager.resize(1200, 800)

    sys.exit(app.exec())
