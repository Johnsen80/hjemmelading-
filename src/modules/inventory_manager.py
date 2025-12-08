"""
Lagermodul for komponenter
Håndterer krutt, kuler, tennhetter og hylser
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
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

from src.database.database import get_database


class InventoryManager(QWidget):
    """Widget for lagermodul"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel("📦 Lagermodul")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Tabs for ulike komponenter
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Legg til tabs
        self.tabs.addTab(self.create_powder_tab(), "💥 Krutt")
        self.tabs.addTab(self.create_bullets_tab(), "🎯 Kuler")
        self.tabs.addTab(self.create_primers_tab(), "💨 Tennhetter")
        self.tabs.addTab(self.create_cases_tab(), "🔩 Hylser")

    def create_powder_tab(self):
        """Oppretter krutt-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Knapper
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Legg til Krutt")
        add_btn.clicked.connect(self.add_powder)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Rediger")
        edit_btn.clicked.connect(self.edit_powder)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.clicked.connect(self.delete_powder)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.powder_table = QTableWidget()
        self.powder_table.setColumnCount(6)
        self.powder_table.setHorizontalHeaderLabels(
            ["Navn", "Produsent", "Type", "Mengde (g)", "Kostnad/kg", "Status"]
        )
        self.powder_table.horizontalHeader().setStretchLastSection(True)
        self.powder_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.powder_table)

        return widget

    def create_bullets_tab(self):
        """Oppretter kule-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Knapper
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Legg til Kuler")
        add_btn.clicked.connect(self.add_bullet)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Rediger")
        edit_btn.clicked.connect(self.edit_bullet)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.clicked.connect(self.delete_bullet)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.bullets_table = QTableWidget()
        self.bullets_table.setColumnCount(7)
        self.bullets_table.setHorizontalHeaderLabels(
            ["Navn", "Produsent", "Kaliber", "Vekt (gr)", "BC (G1)", "Antall", "Status"]
        )
        self.bullets_table.horizontalHeader().setStretchLastSection(True)
        self.bullets_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.bullets_table)

        return widget

    def create_primers_tab(self):
        """Oppretter tennhette-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Knapper
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Legg til Tennhetter")
        add_btn.clicked.connect(self.add_primer)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Rediger")
        edit_btn.clicked.connect(self.edit_primer)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.clicked.connect(self.delete_primer)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.primers_table = QTableWidget()
        self.primers_table.setColumnCount(5)
        self.primers_table.setHorizontalHeaderLabels(
            ["Navn", "Produsent", "Type", "Antall", "Status"]
        )
        self.primers_table.horizontalHeader().setStretchLastSection(True)
        self.primers_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.primers_table)

        return widget

    def create_cases_tab(self):
        """Oppretter hylse-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Knapper
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Legg til Hylser")
        add_btn.clicked.connect(self.add_case)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Rediger")
        edit_btn.clicked.connect(self.edit_case)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.clicked.connect(self.delete_case)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(6)
        self.cases_table.setHorizontalHeaderLabels(
            ["Navn", "Produsent", "Kaliber", "Materiale", "Antall", "Ganger Brukt"]
        )
        self.cases_table.horizontalHeader().setStretchLastSection(True)
        self.cases_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.cases_table)

        return widget

    def load_data(self):
        """Laster all data"""
        self.load_powder()
        self.load_bullets()
        self.load_primers()
        self.load_cases()

    def load_powder(self):
        """Laster krutt fra database"""
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

            # Status med farge
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
        """Laster kuler fra database"""
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
            bc = f"{bullet['bc_g1']:.3f}" if bullet["bc_g1"] else "-"
            self.bullets_table.setItem(i, 4, QTableWidgetItem(bc))
            self.bullets_table.setItem(i, 5, QTableWidgetItem(str(bullet["quantity"])))

            # Status
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
        """Laster tennhetter fra database"""
        primers = self.db.get_all("primers", "type, name")
        self.primers_table.setRowCount(len(primers))

        for i, primer in enumerate(primers):
            self.primers_table.setItem(i, 0, QTableWidgetItem(primer["name"]))
            mfg = primer["manufacturer"] if primer["manufacturer"] else "-"
            self.primers_table.setItem(i, 1, QTableWidgetItem(mfg))
            ptype = primer["type"] if primer["type"] else "-"
            self.primers_table.setItem(i, 2, QTableWidgetItem(ptype))
            self.primers_table.setItem(i, 3, QTableWidgetItem(str(primer["quantity"])))

            # Status
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
        """Laster hylser fra database"""
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
        """Returnerer status-tekst for krutt"""
        if qty < 100:
            return "⚠️ Svært lavt"
        elif qty < 500:
            return "⚠️ Lavt"
        elif qty < 2000:
            return "✓ OK"
        else:
            return "✓ God"

    def get_bullet_status(self, qty):
        """Returnerer status-tekst for kuler"""
        if qty < 50:
            return "⚠️ Svært lavt"
        elif qty < 200:
            return "⚠️ Lavt"
        elif qty < 500:
            return "✓ OK"
        else:
            return "✓ God"

    def get_primer_status(self, qty):
        """Returnerer status-tekst for tennhetter"""
        if qty < 100:
            return "⚠️ Svært lavt"
        elif qty < 500:
            return "⚠️ Lavt"
        elif qty < 1000:
            return "✓ OK"
        else:
            return "✓ God"

    # CRUD-operasjoner for Krutt
    def add_powder(self):
        dialog = PowderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("powder", data)
            self.load_powder()
            QMessageBox.information(self, "Suksess", "Krutt lagt til!")

    def edit_powder(self):
        selected = self.powder_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg et krutt først!")
            return

        powder_id = self.powder_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        powder = self.db.get_by_id("powder", powder_id)

        dialog = PowderDialog(self, powder)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("powder", data, "id = ?", (powder_id,))
            self.load_powder()
            QMessageBox.information(self, "Suksess", "Krutt oppdatert!")

    def delete_powder(self):
        selected = self.powder_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg et krutt først!")
            return

        reply = QMessageBox.question(
            self,
            "Bekreft sletting",
            "Er du sikker på at du vil slette dette kruttet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            powder_id = self.powder_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("powder", "id = ?", (powder_id,))
            self.load_powder()
            QMessageBox.information(self, "Suksess", "Krutt slettet!")

    # CRUD for Kuler
    def add_bullet(self):
        dialog = BulletDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("bullets", data)
            self.load_bullets()
            QMessageBox.information(self, "Suksess", "Kuler lagt til!")

    def edit_bullet(self):
        selected = self.bullets_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg kuler først!")
            return

        bullet_id = self.bullets_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        bullet = self.db.get_by_id("bullets", bullet_id)

        dialog = BulletDialog(self, bullet)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("bullets", data, "id = ?", (bullet_id,))
            self.load_bullets()
            QMessageBox.information(self, "Suksess", "Kuler oppdatert!")

    def delete_bullet(self):
        selected = self.bullets_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg kuler først!")
            return

        reply = QMessageBox.question(
            self,
            "Bekreft sletting",
            "Er du sikker på at du vil slette disse kulene?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            bullet_id = self.bullets_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("bullets", "id = ?", (bullet_id,))
            self.load_bullets()
            QMessageBox.information(self, "Suksess", "Kuler slettet!")

    # CRUD for Tennhetter
    def add_primer(self):
        dialog = PrimerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("primers", data)
            self.load_primers()
            QMessageBox.information(self, "Suksess", "Tennhetter lagt til!")

    def edit_primer(self):
        selected = self.primers_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg tennhetter først!")
            return

        primer_id = self.primers_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        primer = self.db.get_by_id("primers", primer_id)

        dialog = PrimerDialog(self, primer)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("primers", data, "id = ?", (primer_id,))
            self.load_primers()
            QMessageBox.information(self, "Suksess", "Tennhetter oppdatert!")

    def delete_primer(self):
        selected = self.primers_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg tennhetter først!")
            return

        reply = QMessageBox.question(
            self,
            "Bekreft sletting",
            "Er du sikker på at du vil slette disse tennhetterne?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            primer_id = self.primers_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("primers", "id = ?", (primer_id,))
            self.load_primers()
            QMessageBox.information(self, "Suksess", "Tennhetter slettet!")

    # CRUD for Hylser
    def add_case(self):
        dialog = CaseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("cases", data)
            self.load_cases()
            QMessageBox.information(self, "Suksess", "Hylser lagt til!")

    def edit_case(self):
        selected = self.cases_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg hylser først!")
            return

        case_id = self.cases_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        case = self.db.get_by_id("cases", case_id)

        dialog = CaseDialog(self, case)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("cases", data, "id = ?", (case_id,))
            self.load_cases()
            QMessageBox.information(self, "Suksess", "Hylser oppdatert!")

    def delete_case(self):
        selected = self.cases_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg hylser først!")
            return

        reply = QMessageBox.question(
            self,
            "Bekreft sletting",
            "Er du sikker på at du vil slette disse hylsene?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            case_id = self.cases_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete("cases", "id = ?", (case_id,))
            self.load_cases()
            QMessageBox.information(self, "Suksess", "Hylser slettet!")


class PowderDialog(QDialog):
    """Dialog for krutt"""

    def __init__(self, parent=None, powder=None):
        super().__init__(parent)
        self.powder = powder
        self.init_ui()
        if powder:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Krutt")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Navn:", self.name)

        self.manufacturer = QLineEdit()
        layout.addRow("Produsent:", self.manufacturer)

        self.type = QComboBox()
        self.type.addItems(["Rifle", "Pistol", "Shotgun", "Annet"])
        layout.addRow("Type:", self.type)

        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setSuffix(" g")
        layout.addRow("Mengde:", self.quantity)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 10000)
        self.cost.setSuffix(" kr/kg")
        layout.addRow("Kostnad:", self.cost)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notater:", self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
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
    """Dialog for kuler"""

    def __init__(self, parent=None, bullet=None):
        super().__init__(parent)
        self.bullet = bullet
        self.init_ui()
        if bullet:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Kuler")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Navn:", self.name)

        self.manufacturer = QLineEdit()
        layout.addRow("Produsent:", self.manufacturer)

        self.caliber = QLineEdit()
        self.caliber.setPlaceholderText("f.eks. .308, 6.5 Creedmoor")
        layout.addRow("Kaliber:", self.caliber)

        self.weight = QSpinBox()
        self.weight.setRange(20, 500)
        self.weight.setSuffix(" gr")
        layout.addRow("Vekt:", self.weight)

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

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Match", "Hunting", "FMJ", "HP", "Annet"])
        layout.addRow("Type:", self.type_combo)

        self.quantity = QSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setSuffix(" stk")
        layout.addRow("Antall:", self.quantity)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 100)
        self.cost.setSuffix(" kr/stk")
        self.cost.setDecimals(2)
        layout.addRow("Kostnad:", self.cost)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notater:", self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
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
            "type": self.type_combo.currentText(),
            "quantity": self.quantity.value(),
            "cost_per_unit": self.cost.value(),
            "notes": self.notes.toPlainText(),
        }


class PrimerDialog(QDialog):
    """Dialog for tennhetter"""

    def __init__(self, parent=None, primer=None):
        super().__init__(parent)
        self.primer = primer
        self.init_ui()
        if primer:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Tennhetter")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Navn:", self.name)

        self.manufacturer = QLineEdit()
        layout.addRow("Produsent:", self.manufacturer)

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
        self.quantity.setSuffix(" stk")
        layout.addRow("Antall:", self.quantity)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 10)
        self.cost.setSuffix(" kr/stk")
        self.cost.setDecimals(2)
        layout.addRow("Kostnad:", self.cost)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notater:", self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
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
    """Dialog for hylser"""

    def __init__(self, parent=None, case=None):
        super().__init__(parent)
        self.case = case
        self.init_ui()
        if case:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Hylser")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Navn:", self.name)

        self.manufacturer = QLineEdit()
        layout.addRow("Produsent:", self.manufacturer)

        self.caliber = QLineEdit()
        layout.addRow("Kaliber:", self.caliber)

        self.material = QComboBox()
        self.material.addItems(["brass", "nickel brass", "steel"])
        layout.addRow("Materiale:", self.material)

        self.quantity = QSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setSuffix(" stk")
        layout.addRow("Antall:", self.quantity)

        self.times_fired = QSpinBox()
        self.times_fired.setRange(0, 50)
        layout.addRow("Ganger brukt:", self.times_fired)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notater:", self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
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
