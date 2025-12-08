"""
Component Lot Tracking System
Track lot numbers for krutt, kuler, primers
Identifiser lot-variasjon (som ammofabrikker gjør!)
"""

from typing import Dict

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
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

from src.database.database import get_database


class AddLotDialog(QDialog):
    """Dialog for å legge til nytt lot"""

    def __init__(
        self, component_type: str, component_id: int, component_name: str, parent=None
    ):
        super().__init__(parent)
        self.component_type = component_type
        self.component_id = component_id
        self.component_name = component_name

        self.setWindowTitle(f"Legg til lot: {component_name}")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Lot number
        lot_layout = QHBoxLayout()
        lot_layout.addWidget(QLabel("Lot #:"))
        self.edit_lot = QLineEdit()
        self.edit_lot.setPlaceholderText("F-230815-42")
        lot_layout.addWidget(self.edit_lot)
        layout.addLayout(lot_layout)

        # Purchase date
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Kjøpsdato:"))
        self.date_purchase = QDateEdit()
        self.date_purchase.setDate(QDate.currentDate())
        self.date_purchase.setCalendarPopup(True)
        date_layout.addWidget(self.date_purchase)
        layout.addLayout(date_layout)

        # Quantity
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Mengde:"))
        self.spin_quantity = QDoubleSpinBox()
        self.spin_quantity.setRange(0, 100000)
        self.spin_quantity.setDecimals(1)

        if self.component_type == "powder":
            self.spin_quantity.setSuffix(" g")
        else:
            self.spin_quantity.setSuffix(" stk")

        qty_layout.addWidget(self.spin_quantity)
        layout.addLayout(qty_layout)

        # Notes
        layout.addWidget(QLabel("Notater:"))
        self.edit_notes = QTextEdit()
        self.edit_notes.setMaximumHeight(100)
        self.edit_notes.setPlaceholderText("Supplier, pris, observasjoner...")
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
        """Hent input data"""
        return {
            "lot_number": self.edit_lot.text(),
            "purchase_date": self.date_purchase.date().toString("yyyy-MM-dd"),
            "quantity": self.spin_quantity.value(),
            "notes": self.edit_notes.toPlainText(),
        }


class ComponentLotTracker(QWidget):
    """
    Component Lot Tracking System
    Track lot numbers og performance per lot
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("🏷️ Component Lot Tracker")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel(
            "Track lot numbers for krutt, kuler og primers.\n"
            "Ammofabrikker tester hvert lot - du bør også! Lot-variasjon kan gi ±0.3gr charge difference."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Tabs for each component type
        self.tabs = QTabWidget()

        self.tabs.addTab(self.create_component_tab("powder", "Krutt"), "🔥 Krutt")
        self.tabs.addTab(self.create_component_tab("bullets", "Kuler"), "📦 Kuler")
        self.tabs.addTab(
            self.create_component_tab("primers", "Tennhetter"), "💥 Tennhetter"
        )

        layout.addWidget(self.tabs)

        # Lot comparison section
        comparison_group = QGroupBox("📊 Lot Sammenligning & Advarsler")
        comparison_layout = QVBoxLayout()

        self.text_comparison = QTextEdit()
        self.text_comparison.setReadOnly(True)
        self.text_comparison.setMaximumHeight(200)
        self.text_comparison.setHtml(
            """
            <p style='color: #7f8c8d;'>
            Velg en komponent og legg til lots for å se sammenligning.<br><br>
            <b>Tips:</b> Lot-variasjon er REAL!
            <ul>
                <li>Krutt burn rate kan variere ±2% mellom lots</li>
                <li>Dette tilsvarer ±0.3-0.5gr charge weight difference</li>
                <li>Kuler kan ha ±0.0001\" diameter variasjon</li>
                <li>Alltid test på nytt ved lot-bytte!</li>
            </ul>
            </p>
        """
        )
        comparison_layout.addWidget(self.text_comparison)

        comparison_group.setLayout(comparison_layout)
        layout.addWidget(comparison_group)

        self.setLayout(layout)

    def create_component_tab(self, table_name: str, display_name: str) -> QWidget:
        """Opprett en tab for en komponenttype"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Component selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(f"{display_name}:"))

        combo = QComboBox()
        combo.setObjectName(f"combo_{table_name}")
        self.load_components(combo, table_name)
        combo.currentIndexChanged.connect(lambda: self.on_component_changed(table_name))
        selector_layout.addWidget(combo)

        btn_add_lot = QPushButton("➕ Legg til lot")
        btn_add_lot.clicked.connect(lambda: self.add_lot(table_name))
        selector_layout.addWidget(btn_add_lot)

        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # Lots table
        table = QTableWidget()
        table.setObjectName(f"table_{table_name}")
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            [
                "Lot #",
                "Mengde",
                "Kjøpsdato",
                "Status",
                "Performance",
                "Notater",
                "Handling",
            ]
        )
        hdr = table.horizontalHeader()
        if hdr is not None:
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        widget.setLayout(layout)
        return widget

    def load_components(self, combo: QComboBox, table_name: str):
        """Last komponenter"""
        components = self.db.get_all(table_name, "name")
        combo.clear()
        for comp in components:
            combo.addItem(comp["name"], comp["id"])

    def on_component_changed(self, table_name: str):
        """Når komponent velges"""
        combo = self.findChild(QComboBox, f"combo_{table_name}")
        table = self.findChild(QTableWidget, f"table_{table_name}")

        if not combo or not table:
            return

        component_id = combo.currentData()
        if not component_id:
            return

        # Load lots for this component
        self.load_lots(table, table_name, component_id)

        # Update comparison
        self.update_comparison(table_name, component_id)

    def load_lots(self, table: QTableWidget, table_name: str, component_id: int):
        """Last lots for komponent"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM component_lots
            WHERE component_type = ? AND component_id = ?
            ORDER BY purchase_date DESC
        """,
            (table_name, component_id),
        )

        lots = cursor.fetchall()
        table.setRowCount(len(lots))

        for i, lot in enumerate(lots):
            # Lot number
            table.setItem(i, 0, QTableWidgetItem(lot["lot_number"]))

            # Quantity
            qty = lot["quantity_remaining"]
            if table_name == "powder":
                qty_str = f"{qty:.1f} g"
            else:
                qty_str = f"{int(qty)} stk"

            item_qty = QTableWidgetItem(qty_str)
            if qty < 100:  # Low stock
                item_qty.setBackground(QColor(255, 200, 200))
            table.setItem(i, 1, item_qty)

            # Purchase date
            table.setItem(i, 2, QTableWidgetItem(lot["purchase_date"]))

            # Status
            status = "✅ Aktiv" if lot["is_active"] else "⏸️ Inaktiv"
            table.setItem(i, 3, QTableWidgetItem(status))

            # Performance rating
            rating = lot.get("performance_rating", "N/A")
            table.setItem(i, 4, QTableWidgetItem(str(rating)))

            # Notes
            notes = lot.get("notes", "")[:50]
            table.setItem(i, 5, QTableWidgetItem(notes))

            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)

            btn_deactivate = QPushButton("⏸️")
            btn_deactivate.setToolTip("Deaktiver lot")
            btn_deactivate.clicked.connect(
                lambda _, lid=lot["id"]: self.deactivate_lot(
                    lid, table_name, component_id
                )
            )
            btn_layout.addWidget(btn_deactivate)

            btn_widget.setLayout(btn_layout)
            table.setCellWidget(i, 6, btn_widget)

    def add_lot(self, table_name: str):
        """Legg til nytt lot"""
        combo = self.findChild(QComboBox, f"combo_{table_name}")
        if not combo:
            return

        component_id = combo.currentData()
        component_name = combo.currentText()

        if not component_id:
            QMessageBox.warning(
                self, "Ingen komponent valgt", f"Velg en {table_name} først!"
            )
            return

        dialog = AddLotDialog(table_name, component_id, component_name, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            # Save to database
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO component_lots (
                    component_type, component_id, lot_number,
                    purchase_date, quantity_initial, quantity_remaining,
                    is_active, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    table_name,
                    component_id,
                    data["lot_number"],
                    data["purchase_date"],
                    data["quantity"],
                    data["quantity"],
                    1,
                    data["notes"],
                ),
            )
            self.db.conn.commit()

            # Reload table
            table = self.findChild(QTableWidget, f"table_{table_name}")
            self.load_lots(table, table_name, component_id)

            QMessageBox.information(
                self, "Lot lagt til", f"Lot {data['lot_number']} lagt til!"
            )

    def deactivate_lot(self, lot_id: int, table_name: str, component_id: int):
        """Deaktiver lot (oppbrukt/utløpt)"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            UPDATE component_lots
            SET is_active = 0
            WHERE id = ?
        """,
            (lot_id,),
        )
        self.db.conn.commit()

        # Reload table
        table = self.findChild(QTableWidget, f"table_{table_name}")
        self.load_lots(table, table_name, component_id)

    def update_comparison(self, table_name: str, component_id: int):
        """Oppdater lot comparison"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT lot_number, performance_rating, notes
            FROM component_lots
            WHERE component_type = ? AND component_id = ?
            ORDER BY purchase_date DESC
            LIMIT 5
        """,
            (table_name, component_id),
        )

        lots = cursor.fetchall()

        if not lots:
            self.text_comparison.setHtml(
                """
                <p style='color: #7f8c8d;'>
                Ingen lots registrert ennå. Legg til lot for å starte tracking!
                </p>
            """
            )
            return

        html = """
        <h3 style='color: #2c3e50;'>📊 Lot Sammenligning</h3>
        <table border='1' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Lot #</th>
                <th>Performance</th>
                <th>Notater</th>
            </tr>
        """

        for lot in lots:
            rating = (
                lot["performance_rating"]
                if lot["performance_rating"]
                else "Ikke testet"
            )
            notes = lot["notes"][:50] if lot["notes"] else "-"

            html += f"""
            <tr>
                <td><b>{lot['lot_number']}</b></td>
                <td>{rating}</td>
                <td>{notes}</td>
            </tr>
            """

        html += """
        </table>

        <h3 style='color: #e67e22; margin-top: 15px;'>⚠️ Viktig ved lot-bytte:</h3>
        <ul>
            <li><b>Test på nytt!</b> Lot-variasjon kan endre optimal ladning</li>
            <li><b>Start konservativt:</b> 0.3-0.5gr under tidligere optimal</li>
            <li><b>Sjekk pressure signs:</b> Nytt lot kan gi høyere trykk</li>
            <li><b>Verifiser velocity:</b> Sammenlign med gammelt lot</li>
        </ul>
        """

        self.text_comparison.setHtml(html)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ComponentLotTracker()
    window.show()
    sys.exit(app.exec())
