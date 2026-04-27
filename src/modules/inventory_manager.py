"""Inventory module for components."""

import json

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
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

from ..database.database import get_database
from ..utils.drag_models import parse_bc_segments


def _format_bullet_bc_summary(bullet: dict) -> str:
    segments = parse_bc_segments(bullet.get("bc_segments_json"))
    if segments:
        first = segments[0]
        bc_value = first.get("bc_g7") or first.get("bc_g1") or first.get("bc")
        min_v = first.get("velocity_fps_min")
        max_v = first.get("velocity_fps_max")
        if isinstance(bc_value, (int, float)):
            if max_v is not None:
                return f"SEG {float(bc_value):.3f} @ {float(min_v or 0):.0f}-{float(max_v):.0f}"
            return f"SEG {float(bc_value):.3f} @ {float(min_v or 0):.0f}+"
        return "Segmented BC"
    if bullet.get("bc_g7"):
        return f"G7 {float(bullet['bc_g7']):.3f}"
    if bullet.get("bc_g1"):
        return f"G1 {float(bullet['bc_g1']):.3f}"
    return "-"


def _normalize_bc_segments_json(raw_text: str) -> str | None:
    text = raw_text.strip()
    if not text:
        return None
    parsed = parse_bc_segments(text)
    if not parsed:
        return None
    return json.dumps(parsed, ensure_ascii=True)


class InventoryManager(QWidget):
    """Inventory management widget."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Inventory")
        title.setProperty("variant", "cardTitle")
        layout.addWidget(title)

        subtitle = QLabel("Powder, bullets, primers, and cases.")
        subtitle.setProperty("variant", "cardSubtitle")
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self.create_powder_tab(), "Powder")
        self.tabs.addTab(self.create_bullets_tab(), "Bullets")
        self.tabs.addTab(self.create_primers_tab(), "Primers")
        self.tabs.addTab(self.create_cases_tab(), "Cases")

    def create_powder_tab(self):
        """Create the powder tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Powder")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_powder)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_powder)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("variant", "ghost")
        delete_btn.clicked.connect(self.delete_powder)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.powder_table = QTableWidget()
        self.powder_table.setColumnCount(6)
        self.powder_table.setHorizontalHeaderLabels(
            ["Name", "Manufacturer", "Type", "Quantity (g)", "Cost/kg", "Status"]
        )
        self.powder_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.powder_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.powder_table)

        return widget

    def create_bullets_tab(self):
        """Create the bullets tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Bullets")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_bullet)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_bullet)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("variant", "ghost")
        delete_btn.clicked.connect(self.delete_bullet)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.bullets_table = QTableWidget()
        self.bullets_table.setColumnCount(7)
        self.bullets_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Manufacturer",
                "Caliber",
                "Weight (gr)",
                "BC (G1)",
                "Quantity",
                "Status",
            ]
        )
        self.bullets_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.bullets_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.bullets_table)

        return widget

    def create_primers_tab(self):
        """Create the primers tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Primers")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_primer)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_primer)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("variant", "ghost")
        delete_btn.clicked.connect(self.delete_primer)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.primers_table = QTableWidget()
        self.primers_table.setColumnCount(5)
        self.primers_table.setHorizontalHeaderLabels(
            ["Name", "Manufacturer", "Type", "Quantity", "Status"]
        )
        self.primers_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.primers_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.primers_table)

        return widget

    def create_cases_tab(self):
        """Create the cases tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Cases")
        add_btn.setProperty("variant", "primary")
        add_btn.clicked.connect(self.add_case)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.clicked.connect(self.edit_case)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("variant", "ghost")
        delete_btn.clicked.connect(self.delete_case)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(6)
        self.cases_table.setHorizontalHeaderLabels(
            ["Name", "Manufacturer", "Caliber", "Material", "Quantity", "Times Fired"]
        )
        self.cases_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.cases_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.cases_table)

        return widget

    def load_data(self):
        """Load all component data."""
        self.load_powder()
        self.load_bullets()
        self.load_primers()
        self.load_cases()

    def load_powder(self):
        """Load powder data from the database."""
        powders = self.db.get_all("powder", "name")
        self.powder_table.setRowCount(len(powders))

        for i, powder in enumerate(powders):
            self.powder_table.setItem(i, 0, QTableWidgetItem(powder["name"]))
            mfg = powder["manufacturer"] if powder["manufacturer"] else "-"
            self.powder_table.setItem(i, 1, QTableWidgetItem(mfg))
            ptype = powder["type"] if powder["type"] else "-"
            self.powder_table.setItem(i, 2, QTableWidgetItem(ptype))
            qty = f"{powder['quantity_grams']:.0f}"
            self.powder_table.setItem(i, 3, QTableWidgetItem(qty))
            cost = f"{powder['cost_per_unit']:.2f}" if powder["cost_per_unit"] else "-"
            self.powder_table.setItem(i, 4, QTableWidgetItem(cost))

            status_item = QTableWidgetItem(
                self.get_powder_status(powder["quantity_grams"])
            )
            if powder["quantity_grams"] < 100:
                status_item.setBackground(QColor(255, 200, 200))
            elif powder["quantity_grams"] < 500:
                status_item.setBackground(QColor(255, 255, 200))
            else:
                status_item.setBackground(QColor(200, 255, 200))
            self.powder_table.setItem(i, 5, status_item)

            self.powder_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, powder["id"])

    def load_bullets(self):
        """Load bullet data from the database."""
        bullets = self.db.get_all("bullets", "caliber, weight_grains")
        self.bullets_table.setRowCount(len(bullets))

        for i, bullet in enumerate(bullets):
            self.bullets_table.setItem(i, 0, QTableWidgetItem(bullet["name"]))
            mfg = bullet["manufacturer"] if bullet["manufacturer"] else "-"
            self.bullets_table.setItem(i, 1, QTableWidgetItem(mfg))
            self.bullets_table.setItem(i, 2, QTableWidgetItem(bullet["caliber"]))
            self.bullets_table.setItem(
                i, 3, QTableWidgetItem(f"{bullet['weight_grains']}")
            )
            bc = _format_bullet_bc_summary(bullet)
            self.bullets_table.setItem(i, 4, QTableWidgetItem(bc))
            self.bullets_table.setItem(i, 5, QTableWidgetItem(str(bullet["quantity"])))

            status_item = QTableWidgetItem(self.get_bullet_status(bullet["quantity"]))
            if bullet["quantity"] < 50:
                status_item.setBackground(QColor(255, 200, 200))
            elif bullet["quantity"] < 200:
                status_item.setBackground(QColor(255, 255, 200))
            else:
                status_item.setBackground(QColor(200, 255, 200))
            self.bullets_table.setItem(i, 6, status_item)

            self.bullets_table.item(i, 0).setData(
                Qt.ItemDataRole.UserRole, bullet["id"]
            )

    def load_primers(self):
        """Load primer data from the database."""
        primers = self.db.get_all("primers", "type, name")
        self.primers_table.setRowCount(len(primers))

        for i, primer in enumerate(primers):
            self.primers_table.setItem(i, 0, QTableWidgetItem(primer["name"]))
            mfg = primer["manufacturer"] if primer["manufacturer"] else "-"
            self.primers_table.setItem(i, 1, QTableWidgetItem(mfg))
            ptype = primer["type"] if primer["type"] else "-"
            self.primers_table.setItem(i, 2, QTableWidgetItem(ptype))
            self.primers_table.setItem(i, 3, QTableWidgetItem(str(primer["quantity"])))

            status_item = QTableWidgetItem(self.get_primer_status(primer["quantity"]))
            if primer["quantity"] < 100:
                status_item.setBackground(QColor(255, 200, 200))
            elif primer["quantity"] < 500:
                status_item.setBackground(QColor(255, 255, 200))
            else:
                status_item.setBackground(QColor(200, 255, 200))
            self.primers_table.setItem(i, 4, status_item)

            self.primers_table.item(i, 0).setData(
                Qt.ItemDataRole.UserRole, primer["id"]
            )

    def load_cases(self):
        """Load case data from the database."""
        cases = self.db.get_all("cases", "caliber, name")
        self.cases_table.setRowCount(len(cases))

        for i, case in enumerate(cases):
            self.cases_table.setItem(i, 0, QTableWidgetItem(case["name"]))
            mfg = case["manufacturer"] if case["manufacturer"] else "-"
            self.cases_table.setItem(i, 1, QTableWidgetItem(mfg))
            self.cases_table.setItem(i, 2, QTableWidgetItem(case["caliber"]))
            mat = case["material"] if case["material"] else "brass"
            self.cases_table.setItem(i, 3, QTableWidgetItem(mat))
            self.cases_table.setItem(i, 4, QTableWidgetItem(str(case["quantity"])))
            self.cases_table.setItem(i, 5, QTableWidgetItem(str(case["times_fired"])))

            self.cases_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, case["id"])

    def get_powder_status(self, qty):
        """Return stock status text for powder."""
        if qty < 100:
            return "Very Low"
        elif qty < 500:
            return "Low"
        elif qty < 2000:
            return "OK"
        else:
            return "Good"

    def get_bullet_status(self, qty):
        """Return stock status text for bullets."""
        if qty < 50:
            return "Very Low"
        elif qty < 200:
            return "Low"
        elif qty < 500:
            return "OK"
        else:
            return "Good"

    def get_primer_status(self, qty):
        """Return stock status text for primers."""
        if qty < 100:
            return "Very Low"
        elif qty < 500:
            return "Low"
        elif qty < 1000:
            return "OK"
        else:
            return "Good"

    def add_powder(self):
        dialog = PowderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("powder", data)
            self.load_powder()
            QMessageBox.information(self, "Success", "Powder added.")

    def edit_powder(self):
        selected = self.powder_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Nothing Selected", "Select a powder first.")
            return

        powder_id = self.powder_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        powder = self.db.get_by_id("powder", powder_id)
        if not powder:
            QMessageBox.warning(
                self,
                "Powder Missing",
                "The selected powder no longer exists in the database.",
            )
            self.load_powder()
            return

        dialog = PowderDialog(self, powder)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("powder", data, "id = ?", (powder_id,))
            self.load_powder()
            QMessageBox.information(self, "Success", "Powder updated.")

    def delete_powder(self):
        selected = self.powder_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Nothing Selected", "Select a powder first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this powder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            powder_id = self.powder_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("powder", "id = ?", (powder_id,))
            self.load_powder()
            QMessageBox.information(self, "Success", "Powder deleted.")

    def add_bullet(self):
        dialog = BulletDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("bullets", data)
            self.load_bullets()
            QMessageBox.information(self, "Success", "Bullets added.")

    def edit_bullet(self):
        selected = self.bullets_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Nothing Selected", "Select bullets first.")
            return

        bullet_id = self.bullets_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        bullet = self.db.get_by_id("bullets", bullet_id)
        if not bullet:
            QMessageBox.warning(
                self,
                "Bullet Missing",
                "The selected bullet no longer exists in the database.",
            )
            self.load_bullets()
            return

        dialog = BulletDialog(self, bullet)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("bullets", data, "id = ?", (bullet_id,))
            self.load_bullets()
            QMessageBox.information(self, "Success", "Bullets updated.")

    def delete_bullet(self):
        selected = self.bullets_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Nothing Selected", "Select bullets first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete these bullets?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            bullet_id = self.bullets_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("bullets", "id = ?", (bullet_id,))
            self.load_bullets()
            QMessageBox.information(self, "Success", "Bullets deleted.")

    def add_primer(self):
        dialog = PrimerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("primers", data)
            self.load_primers()
            QMessageBox.information(self, "Success", "Primers added.")

    def edit_primer(self):
        selected = self.primers_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Nothing Selected", "Select primers first.")
            return

        primer_id = self.primers_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        primer = self.db.get_by_id("primers", primer_id)
        if not primer:
            QMessageBox.warning(
                self,
                "Primer Missing",
                "The selected primer no longer exists in the database.",
            )
            self.load_primers()
            return

        dialog = PrimerDialog(self, primer)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("primers", data, "id = ?", (primer_id,))
            self.load_primers()
            QMessageBox.information(self, "Success", "Primers updated.")

    def delete_primer(self):
        selected = self.primers_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Nothing Selected", "Select primers first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete these primers?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            primer_id = self.primers_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("primers", "id = ?", (primer_id,))
            self.load_primers()
            QMessageBox.information(self, "Success", "Primers deleted.")

    def add_case(self):
        dialog = CaseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("cases", data)
            self.load_cases()
            QMessageBox.information(self, "Success", "Cases added.")

    def edit_case(self):
        selected = self.cases_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Nothing Selected", "Select cases first.")
            return

        case_id = self.cases_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        case = self.db.get_by_id("cases", case_id)
        if not case:
            QMessageBox.warning(
                self,
                "Case Missing",
                "The selected case no longer exists in the database.",
            )
            self.load_cases()
            return

        dialog = CaseDialog(self, case)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("cases", data, "id = ?", (case_id,))
            self.load_cases()
            QMessageBox.information(self, "Success", "Cases updated.")

    def delete_case(self):
        selected = self.cases_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Nothing Selected", "Select cases first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete these cases?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            case_id = self.cases_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete("cases", "id = ?", (case_id,))
            self.load_cases()
            QMessageBox.information(self, "Success", "Cases deleted.")


class PowderDialog(QDialog):
    """Dialog for powder."""

    def __init__(self, parent=None, powder=None):
        super().__init__(parent)
        self.powder = powder
        self.init_ui()
        if powder:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Powder")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Name:", self.name)

        self.manufacturer = QLineEdit()
        layout.addRow("Manufacturer:", self.manufacturer)

        self.type = QComboBox()
        self.type.addItems(["Rifle", "Pistol", "Shotgun", "Other"])
        layout.addRow("Type:", self.type)

        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setSuffix(" g")
        layout.addRow("Quantity:", self.quantity)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 10000)
        self.cost.setSuffix(" NOK/kg")
        layout.addRow("Cost:", self.cost)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notes:", self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("variant", "ghost")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def load_data(self):
        self.name.setText(self.powder["name"])
        if self.powder["manufacturer"]:
            self.manufacturer.setText(self.powder["manufacturer"])
        if self.powder["type"]:
            idx = self.type.findText(self.powder["type"])
            if idx >= 0:
                self.type.setCurrentIndex(idx)
        self.quantity.setValue(self.powder["quantity_grams"])
        if self.powder["cost_per_unit"]:
            self.cost.setValue(self.powder["cost_per_unit"])
        if self.powder["notes"]:
            self.notes.setText(self.powder["notes"])

    def get_data(self):
        return {
            "name": self.name.text(),
            "manufacturer": self.manufacturer.text(),
            "type": self.type.currentText(),
            "quantity_grams": self.quantity.value(),
            "cost_per_unit": self.cost.value(),
            "notes": self.notes.toPlainText(),
        }


class BulletDialog(QDialog):
    """Dialog for bullets."""

    def __init__(self, parent=None, bullet=None):
        super().__init__(parent)
        self.bullet = bullet
        self.init_ui()
        if bullet:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Bullets")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Name:", self.name)

        self.manufacturer = QLineEdit()
        layout.addRow("Manufacturer:", self.manufacturer)

        self.caliber = QLineEdit()
        self.caliber.setPlaceholderText("e.g. .308, 6.5 Creedmoor")
        layout.addRow("Caliber:", self.caliber)

        self.weight = QSpinBox()
        self.weight.setRange(20, 500)
        self.weight.setSuffix(" gr")
        layout.addRow("Weight:", self.weight)

        self.bc_g1 = QDoubleSpinBox()
        self.bc_g1.setRange(0.1, 1.0)
        self.bc_g1.setDecimals(3)
        self.bc_g1.setSingleStep(0.001)
        layout.addRow("BC (G1):", self.bc_g1)

        self.bc_g7 = QDoubleSpinBox()
        self.bc_g7.setRange(0.1, 1.0)
        self.bc_g7.setDecimals(3)
        self.bc_g7.setSingleStep(0.001)
        layout.addRow("BC (G7):", self.bc_g7)

        self.bc_segments = QTextEdit()
        self.bc_segments.setMaximumHeight(90)
        self.bc_segments.setPlaceholderText(
            '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]'
        )
        layout.addRow("Segmented BC (JSON):", self.bc_segments)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Match", "Hunting", "FMJ", "HP", "Other"])
        layout.addRow("Type:", self.type_combo)

        self.quantity = QSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setSuffix(" pcs")
        layout.addRow("Quantity:", self.quantity)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 100)
        self.cost.setSuffix(" NOK/pc")
        self.cost.setDecimals(2)
        layout.addRow("Cost:", self.cost)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notes:", self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("variant", "ghost")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def load_data(self):
        self.name.setText(self.bullet["name"])
        if self.bullet["manufacturer"]:
            self.manufacturer.setText(self.bullet["manufacturer"])
        self.caliber.setText(self.bullet["caliber"])
        self.weight.setValue(int(self.bullet["weight_grains"]))
        if self.bullet["bc_g1"]:
            self.bc_g1.setValue(self.bullet["bc_g1"])
        if self.bullet["bc_g7"]:
            self.bc_g7.setValue(self.bullet["bc_g7"])
        if self.bullet.get("bc_segments_json"):
            self.bc_segments.setPlainText(
                str(self.bullet.get("bc_segments_json") or "")
            )
        if self.bullet["type"]:
            idx = self.type_combo.findText(self.bullet["type"])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        self.quantity.setValue(self.bullet["quantity"])
        if self.bullet["cost_per_unit"]:
            self.cost.setValue(self.bullet["cost_per_unit"])
        if self.bullet["notes"]:
            self.notes.setText(self.bullet["notes"])

    def get_data(self):
        return {
            "name": self.name.text(),
            "manufacturer": self.manufacturer.text(),
            "caliber": self.caliber.text(),
            "weight_grains": self.weight.value(),
            "bc_g1": self.bc_g1.value(),
            "bc_g7": self.bc_g7.value(),
            "bc_segments_json": _normalize_bc_segments_json(
                self.bc_segments.toPlainText()
            ),
            "type": self.type_combo.currentText(),
            "quantity": self.quantity.value(),
            "cost_per_unit": self.cost.value(),
            "notes": self.notes.toPlainText(),
        }


class PrimerDialog(QDialog):
    """Dialog for primers."""

    def __init__(self, parent=None, primer=None):
        super().__init__(parent)
        self.primer = primer
        self.init_ui()
        if primer:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Primers")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Name:", self.name)

        self.manufacturer = QLineEdit()
        layout.addRow("Manufacturer:", self.manufacturer)

        self.type_combo = QComboBox()
        self.type_combo.addItems(
            [
                "Small Rifle",
                "Large Rifle",
                "Small Pistol",
                "Large Pistol",
                "Magnum Rifle",
                "Magnum Pistol",
            ]
        )
        layout.addRow("Type:", self.type_combo)

        self.quantity = QSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setSuffix(" pcs")
        layout.addRow("Quantity:", self.quantity)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 10)
        self.cost.setSuffix(" NOK/pc")
        self.cost.setDecimals(2)
        layout.addRow("Cost:", self.cost)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notes:", self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("variant", "ghost")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def load_data(self):
        self.name.setText(self.primer["name"])
        if self.primer["manufacturer"]:
            self.manufacturer.setText(self.primer["manufacturer"])
        if self.primer["type"]:
            idx = self.type_combo.findText(self.primer["type"])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        self.quantity.setValue(self.primer["quantity"])
        if self.primer["cost_per_unit"]:
            self.cost.setValue(self.primer["cost_per_unit"])
        if self.primer["notes"]:
            self.notes.setText(self.primer["notes"])

    def get_data(self):
        return {
            "name": self.name.text(),
            "manufacturer": self.manufacturer.text(),
            "type": self.type_combo.currentText(),
            "quantity": self.quantity.value(),
            "cost_per_unit": self.cost.value(),
            "notes": self.notes.toPlainText(),
        }


class CaseDialog(QDialog):
    """Dialog for cases."""

    def __init__(self, parent=None, case=None):
        super().__init__(parent)
        self.case = case
        self.init_ui()
        if case:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Cases")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Name:", self.name)

        self.manufacturer = QLineEdit()
        layout.addRow("Manufacturer:", self.manufacturer)

        self.caliber = QLineEdit()
        layout.addRow("Caliber:", self.caliber)

        self.material = QComboBox()
        self.material.addItems(["brass", "nickel brass", "steel"])
        layout.addRow("Material:", self.material)

        self.quantity = QSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setSuffix(" pcs")
        layout.addRow("Quantity:", self.quantity)

        self.times_fired = QSpinBox()
        self.times_fired.setRange(0, 50)
        layout.addRow("Times fired:", self.times_fired)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notes:", self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("variant", "ghost")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def load_data(self):
        self.name.setText(self.case["name"])
        if self.case["manufacturer"]:
            self.manufacturer.setText(self.case["manufacturer"])
        self.caliber.setText(self.case["caliber"])
        if self.case["material"]:
            idx = self.material.findText(self.case["material"])
            if idx >= 0:
                self.material.setCurrentIndex(idx)
        self.quantity.setValue(self.case["quantity"])
        self.times_fired.setValue(self.case["times_fired"])
        if self.case["notes"]:
            self.notes.setText(self.case["notes"])

    def get_data(self):
        return {
            "name": self.name.text(),
            "manufacturer": self.manufacturer.text(),
            "caliber": self.caliber.text(),
            "material": self.material.currentText(),
            "quantity": self.quantity.value(),
            "times_fired": self.times_fired.value(),
            "notes": self.notes.toPlainText(),
        }
