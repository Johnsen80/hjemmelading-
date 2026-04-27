"""
Component Inventory & Cost Tracking System
Track EVERYTHING you own + costs + usage + ROI!

The #1 most requested feature by reloaders!
"""

from collections import defaultdict

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
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

from ..database.database import get_database
from ..ui.reloading_theme import ReloadingTheme
from ..utils.i18n import tr


class ComponentType:
    """Component type constants"""

    BULLET = "bullet"
    POWDER = "powder"
    PRIMER = "primer"
    BRASS = "brass"
    OTHER = "other"


LOW_STOCK_THRESHOLDS = {
    ComponentType.BULLET: 100,
    ComponentType.POWDER: 500,
    ComponentType.PRIMER: 100,
    ComponentType.BRASS: 100,
    ComponentType.OTHER: 1,
}

DEFAULT_STOCK_TARGETS = {
    ComponentType.BULLET: 1000,
    ComponentType.POWDER: 5000,
    ComponentType.PRIMER: 1000,
    ComponentType.BRASS: 200,
    ComponentType.OTHER: 10,
}


class InventoryDashboard(QWidget):
    """
    Main inventory dashboard with visual overview
    Shows stock levels, warnings, quick stats
    """

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self._inventory_items = []
        self.init_ui()
        self.load_inventory_data()

    def init_ui(self):
        """Initialize dashboard UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel(tr("component_inventory_title"), self)
        header.setProperty("role", "title")
        header.setWordWrap(True)
        layout.addWidget(header)

        # Quick stats row
        stats_layout = QHBoxLayout()

        # Total value card
        self.card_total_value = self.create_stat_card(
            tr("component_inventory_total_value"), "$2,847.50", ReloadingTheme.ACCENT
        )
        stats_layout.addWidget(self.card_total_value)

        # Savings vs factory
        self.card_savings = self.create_stat_card(
            tr("component_inventory_savings_vs_factory"),
            "$1,234.00",
            ReloadingTheme.SUCCESS,
        )
        stats_layout.addWidget(self.card_savings)

        # Low stock warnings
        self.card_warnings = self.create_stat_card(
            tr("component_inventory_low_stock_items"), "3 items", ReloadingTheme.WARNING
        )
        stats_layout.addWidget(self.card_warnings)

        # Rounds can make
        self.card_rounds = self.create_stat_card(
            tr("component_inventory_rounds_available"),
            "1,247 rounds",
            ReloadingTheme.INFO,
        )
        stats_layout.addWidget(self.card_rounds)

        layout.addLayout(stats_layout)

        # Component overview (grid of progress bars)
        component_group = QGroupBox(tr("component_inventory_stock_levels"), self)
        component_group.setProperty("variant", "panel")
        component_layout = QGridLayout()
        component_group.setLayout(component_layout)

        # Bullets
        component_layout.addWidget(
            QLabel(f"<b>{tr('component_inventory_bullets')}:</b>", self), 0, 0
        )
        (
            self.bullets_bar_layout,
            self.bullets_bar_label,
            self.bullets_bar,
        ) = self.create_stock_bar(0, 1, tr("component_inventory_bullets"))
        component_layout.addLayout(self.bullets_bar_layout, 0, 1)

        # Powder
        component_layout.addWidget(
            QLabel(f"<b>{tr('component_inventory_powder')}:</b>", self), 1, 0
        )
        (
            self.powder_bar_layout,
            self.powder_bar_label,
            self.powder_bar,
        ) = self.create_stock_bar(0, 1, tr("component_inventory_powder"))
        component_layout.addLayout(self.powder_bar_layout, 1, 1)

        # Primers
        component_layout.addWidget(
            QLabel(f"<b>{tr('component_inventory_primers')}:</b>", self), 2, 0
        )
        (
            self.primers_bar_layout,
            self.primers_bar_label,
            self.primers_bar,
        ) = self.create_stock_bar(0, 1, tr("component_inventory_primers"))
        component_layout.addLayout(self.primers_bar_layout, 2, 1)

        # Brass
        component_layout.addWidget(
            QLabel(f"<b>{tr('component_inventory_brass')}:</b>", self), 3, 0
        )
        (
            self.brass_bar_layout,
            self.brass_bar_label,
            self.brass_bar,
        ) = self.create_stock_bar(0, 1, tr("component_inventory_brass"))
        component_layout.addLayout(self.brass_bar_layout, 3, 1)

        layout.addWidget(component_group)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.btn_add_component = QPushButton(
            tr("component_inventory_add_component"), self
        )
        self.btn_add_component.setProperty("variant", "primary")
        self.btn_add_component.clicked.connect(self.add_component)
        btn_layout.addWidget(self.btn_add_component)

        self.btn_record_purchase = QPushButton(
            tr("component_inventory_record_purchase"), self
        )
        self.btn_record_purchase.setProperty("variant", "secondary")
        self.btn_record_purchase.clicked.connect(self.record_purchase)
        btn_layout.addWidget(self.btn_record_purchase)

        self.btn_usage_history = QPushButton(
            tr("component_inventory_usage_history"), self
        )
        self.btn_usage_history.clicked.connect(self.show_usage_history)
        btn_layout.addWidget(self.btn_usage_history)

        self.btn_cost_analysis = QPushButton(
            tr("component_inventory_cost_analysis"), self
        )
        self.btn_cost_analysis.clicked.connect(self.show_cost_analysis)
        btn_layout.addWidget(self.btn_cost_analysis)

        layout.addLayout(btn_layout)

        # Detailed inventory table
        table_label = QLabel(tr("component_inventory_detailed_inventory"), self)
        table_label.setProperty("role", "subtitle")
        layout.addWidget(table_label)

        self.inventory_table = QTableWidget(self)
        self.inventory_table.setColumnCount(10)
        self.inventory_table.setHorizontalHeaderLabels(
            [
                "Component",
                tr("component_inventory_type"),
                tr("component_inventory_lot_number"),
                tr("component_inventory_quantity"),
                tr("component_inventory_unit"),
                tr("component_inventory_cost_per_unit"),
                tr("component_inventory_total_value"),
                tr("component_inventory_location"),
                tr("component_inventory_expiry"),
                tr("component_inventory_actions"),
            ]
        )
        self.inventory_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        layout.addWidget(self.inventory_table)

    def create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create colored stat card"""
        card = QFrame(self)
        card.setProperty("variant", "statCard")

        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(10)
        card.setLayout(card_layout)

        accent = QFrame(card)
        accent.setFixedWidth(4)
        accent.setStyleSheet(
            f"background-color: {color}; border: none; border-radius: 2px; padding: 0px;"
        )
        card_layout.addWidget(accent)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(4)
        card_layout.addLayout(content, 1)

        title_label = QLabel(title, card)
        title_label.setProperty("variant", "statTitle")
        content.addWidget(title_label)

        value_label = QLabel(value, card)
        value_label.setProperty("variant", "statValue")
        content.addWidget(value_label)

        card.value_label = value_label

        return card

    def create_stock_bar(
        self, current: int, maximum: int, label: str
    ) -> tuple[QHBoxLayout, QLabel, QProgressBar]:
        """Create stock level progress bar with label"""
        layout = QHBoxLayout()
        layout.setSpacing(8)
        # Descriptive label (parented) placed next to the progress bar
        desc = QLabel(label, self)
        desc.setProperty("role", "muted")

        bar = QProgressBar(self)
        bar.setTextVisible(True)
        self.update_stock_bar(desc, bar, current, maximum, label)

        layout.addWidget(desc)
        layout.addWidget(bar)

        return layout, desc, bar

    def update_stock_bar(
        self,
        label: QLabel,
        bar: QProgressBar,
        current: float,
        maximum: float,
        text: str,
    ) -> None:
        safe_max = max(int(maximum), 1)
        safe_current = min(int(current), safe_max)
        label.setText(text)
        bar.setMinimum(0)
        bar.setMaximum(safe_max)
        bar.setValue(safe_current)
        bar.setFormat(f"{safe_current}/{safe_max}")

        percentage = (safe_current / safe_max) * 100 if safe_max else 0
        if percentage < 10:
            bar.setStyleSheet(
                """
                QProgressBar { border: 2px solid #e74c3c; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #e74c3c; }
            """
            )
        elif percentage < 25:
            bar.setStyleSheet(
                """
                QProgressBar { border: 2px solid #f39c12; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #f39c12; }
            """
            )
        else:
            bar.setStyleSheet(
                """
                QProgressBar { border: 2px solid #27ae60; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #27ae60; }
            """
            )

    def _normalize_type(self, value: str) -> str:
        return value.strip().lower()

    def _display_type(self, value: str) -> str:
        return value.strip().capitalize()

    def _format_currency(self, value: float, decimals: int = 2) -> str:
        return f"${value:,.{decimals}f}"

    def _fetch_inventory_items(self) -> list[dict]:
        self._inventory_items = self.db.execute_query(
            "SELECT * FROM inventory_items ORDER BY component_type, component_name"
        )
        return self._inventory_items

    def load_inventory_data(self):
        """Load inventory from database"""
        items = self._fetch_inventory_items()
        totals_by_type = {
            ComponentType.BULLET: 0.0,
            ComponentType.POWDER: 0.0,
            ComponentType.PRIMER: 0.0,
            ComponentType.BRASS: 0.0,
            ComponentType.OTHER: 0.0,
        }
        total_value = 0.0
        warnings_count = 0

        for item in items:
            comp_type = self._normalize_type(item.get("component_type", ""))
            quantity = float(item.get("quantity", 0) or 0)
            totals_by_type[comp_type] = totals_by_type.get(comp_type, 0.0) + quantity
            cost_per_unit = float(item.get("cost_per_unit", 0) or 0)
            total_value += quantity * cost_per_unit

            threshold = LOW_STOCK_THRESHOLDS.get(comp_type, 1)
            if quantity < threshold:
                warnings_count += 1

        bullets_qty = int(totals_by_type.get(ComponentType.BULLET, 0))
        primers_qty = int(totals_by_type.get(ComponentType.PRIMER, 0))
        brass_qty = int(totals_by_type.get(ComponentType.BRASS, 0))
        rounds_available = 0
        if bullets_qty > 0 and primers_qty > 0:
            rounds_available = min(bullets_qty, primers_qty)
            if brass_qty > 0:
                rounds_available = min(rounds_available, brass_qty)

        self.card_total_value.value_label.setText(self._format_currency(total_value))
        self.card_savings.value_label.setText("$0.00")
        self.card_warnings.value_label.setText(
            tr("component_inventory_items_count", count=warnings_count)
        )
        self.card_rounds.value_label.setText(
            tr("component_inventory_rounds_count", count=rounds_available)
        )

        self.update_stock_bar(
            self.bullets_bar_label,
            self.bullets_bar,
            totals_by_type.get(ComponentType.BULLET, 0),
            max(
                totals_by_type.get(ComponentType.BULLET, 0),
                DEFAULT_STOCK_TARGETS[ComponentType.BULLET],
            ),
            tr("component_inventory_bullets"),
        )
        self.update_stock_bar(
            self.powder_bar_label,
            self.powder_bar,
            totals_by_type.get(ComponentType.POWDER, 0),
            max(
                totals_by_type.get(ComponentType.POWDER, 0),
                DEFAULT_STOCK_TARGETS[ComponentType.POWDER],
            ),
            tr("component_inventory_powder"),
        )
        self.update_stock_bar(
            self.primers_bar_label,
            self.primers_bar,
            totals_by_type.get(ComponentType.PRIMER, 0),
            max(
                totals_by_type.get(ComponentType.PRIMER, 0),
                DEFAULT_STOCK_TARGETS[ComponentType.PRIMER],
            ),
            tr("component_inventory_primers"),
        )
        self.update_stock_bar(
            self.brass_bar_label,
            self.brass_bar,
            totals_by_type.get(ComponentType.BRASS, 0),
            max(
                totals_by_type.get(ComponentType.BRASS, 0),
                DEFAULT_STOCK_TARGETS[ComponentType.BRASS],
            ),
            tr("component_inventory_brass"),
        )

        self.inventory_table.setRowCount(0)

        for item in items:
            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)

            name = item.get("component_name", "")
            comp_type = self._normalize_type(item.get("component_type", ""))
            display_type = self._display_type(comp_type)
            lot_number = item.get("lot_number") or "-"
            quantity = float(item.get("quantity", 0) or 0)
            unit = item.get("unit") or "-"
            cost_per_unit = float(item.get("cost_per_unit", 0) or 0)
            total_item_value = quantity * cost_per_unit
            location = item.get("location") or "-"
            expiry = item.get("expiry_date") or "N/A"

            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, item.get("id"))
            self.inventory_table.setItem(row, 0, name_item)

            type_item = QTableWidgetItem(display_type)
            # Color code by type
            if comp_type == ComponentType.BULLET:
                type_item.setBackground(QColor("#e8f4f8"))
            elif comp_type == ComponentType.POWDER:
                type_item.setBackground(QColor("#fff9c4"))
            elif comp_type == ComponentType.PRIMER:
                type_item.setBackground(QColor("#ffcccc"))
            elif comp_type == ComponentType.BRASS:
                type_item.setBackground(QColor("#d5f4e6"))
            self.inventory_table.setItem(row, 1, type_item)

            # Lot number
            lot_item = QTableWidgetItem(lot_number)
            lot_item.setFont(QFont("Courier New", 9))  # Monospace for lot numbers
            self.inventory_table.setItem(row, 2, lot_item)

            qty_item = QTableWidgetItem(f"{int(quantity)}")
            # Warning if low stock
            threshold = LOW_STOCK_THRESHOLDS.get(comp_type, 1)
            if quantity < threshold:
                qty_item.setBackground(QColor("#ffcccc"))
                qty_item.setForeground(QColor("#c0392b"))
            self.inventory_table.setItem(row, 3, qty_item)

            self.inventory_table.setItem(row, 4, QTableWidgetItem(unit))
            cost_text = self._format_currency(cost_per_unit, decimals=3)
            total_text = self._format_currency(total_item_value, decimals=2)
            self.inventory_table.setItem(row, 5, QTableWidgetItem(cost_text))
            self.inventory_table.setItem(row, 6, QTableWidgetItem(total_text))
            self.inventory_table.setItem(row, 7, QTableWidgetItem(location))
            self.inventory_table.setItem(row, 8, QTableWidgetItem(expiry))

            # Actions button
            btn_edit = QPushButton(tr("component_inventory_edit"))
            btn_edit.setMaximumWidth(60)
            self.inventory_table.setCellWidget(row, 9, btn_edit)

        self.inventory_table.resizeColumnsToContents()

    def add_component(self):
        """Add new component to inventory"""
        dialog = AddComponentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["component_name"]:
                QMessageBox.warning(
                    self,
                    tr("component_inventory_missing_name_title"),
                    tr("component_inventory_missing_name_message"),
                )
                return
            self.db.insert("inventory_items", data)
            self.load_inventory_data()
            QMessageBox.information(
                self, tr("msg_success"), tr("component_inventory_component_added")
            )

    def record_purchase(self):
        """Record a purchase"""
        components = self._get_component_choices()
        if not components:
            QMessageBox.warning(
                self,
                tr("component_inventory_no_components_title"),
                tr("component_inventory_no_components_message"),
            )
            return

        dialog = RecordPurchaseDialog(self, components)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data:
                self.db.insert("inventory_items", data)
            self.load_inventory_data()
            QMessageBox.information(
                self, tr("msg_success"), tr("component_inventory_purchase_recorded")
            )

    def _get_component_choices(self) -> list[dict]:
        items = self.db.execute_query(
            "SELECT * FROM inventory_items ORDER BY created_date DESC"
        )
        choices = []
        seen = set()
        for item in items:
            key = (item.get("component_name"), item.get("component_type"))
            if key in seen:
                continue
            seen.add(key)
            choices.append(item)
        return choices

    def show_usage_history(self):
        """Show component usage history"""
        QMessageBox.information(
            self,
            tr("component_inventory_usage_history"),
            tr("component_inventory_usage_history_coming"),
        )

    def show_cost_analysis(self):
        """Show detailed cost analysis"""
        dialog = CostAnalysisDialog(self)
        dialog.exec()


class AddComponentDialog(QDialog):
    """Dialog for adding new component"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("component_inventory_add_component"))
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QFormLayout()
        self.setLayout(layout)

        # Component type
        self.component_type = QComboBox()
        self.component_type.addItem(
            tr("component_inventory_type_bullet"), ComponentType.BULLET
        )
        self.component_type.addItem(
            tr("component_inventory_type_powder"), ComponentType.POWDER
        )
        self.component_type.addItem(
            tr("component_inventory_type_primer"), ComponentType.PRIMER
        )
        self.component_type.addItem(
            tr("component_inventory_type_brass"), ComponentType.BRASS
        )
        self.component_type.addItem(
            tr("component_inventory_type_other"), ComponentType.OTHER
        )
        layout.addRow(
            tr("component_inventory_component_type_label"), self.component_type
        )

        # Name
        self.component_name = QLineEdit()
        self.component_name.setPlaceholderText(
            tr("component_inventory_name_placeholder")
        )
        layout.addRow(tr("component_inventory_name_label"), self.component_name)

        # Manufacturer
        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText(
            tr("component_inventory_manufacturer_placeholder")
        )
        layout.addRow(tr("component_inventory_manufacturer_label"), self.manufacturer)

        # Lot number
        self.lot_number = QLineEdit()
        self.lot_number.setPlaceholderText(tr("component_inventory_lot_placeholder"))
        layout.addRow(tr("component_inventory_lot_number_label"), self.lot_number)

        # Quantity
        self.quantity = QSpinBox()
        self.quantity.setRange(0, 999999)
        self.quantity.setValue(100)
        layout.addRow(tr("component_inventory_quantity_label"), self.quantity)

        # Unit
        self.unit = QComboBox()
        self.unit.addItems(["pcs", "gr", "lb", "kg", "box"])
        layout.addRow(tr("component_inventory_unit_label"), self.unit)

        # Cost per unit
        self.cost_per_unit = QDoubleSpinBox()
        self.cost_per_unit.setRange(0, 999.99)
        self.cost_per_unit.setValue(0.50)
        self.cost_per_unit.setPrefix("$")
        self.cost_per_unit.setDecimals(3)
        layout.addRow(tr("component_inventory_cost_per_unit_label"), self.cost_per_unit)

        # Location
        self.location = QLineEdit()
        self.location.setPlaceholderText(tr("component_inventory_location_placeholder"))
        layout.addRow(tr("component_inventory_storage_location_label"), self.location)

        # Purchase date
        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.currentDate())
        self.purchase_date.setCalendarPopup(True)
        layout.addRow(tr("component_inventory_purchase_date_label"), self.purchase_date)

        # Expiry date (optional for powder)
        self.expiry_date = QDateEdit()
        self.expiry_date.setDate(QDate.currentDate().addYears(5))
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setSpecialValueText("N/A")
        layout.addRow(tr("component_inventory_expiry_date_label"), self.expiry_date)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText(tr("component_inventory_notes_placeholder"))
        layout.addRow(tr("component_inventory_notes_label"), self.notes)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        return {
            "component_name": self.component_name.text().strip(),
            "component_type": self.component_type.currentData(),
            "manufacturer": self.manufacturer.text().strip(),
            "lot_number": self.lot_number.text().strip(),
            "quantity": self.quantity.value(),
            "unit": self.unit.currentText(),
            "cost_per_unit": self.cost_per_unit.value(),
            "location": self.location.text().strip(),
            "purchase_date": self.purchase_date.date().toString("yyyy-MM-dd"),
            "expiry_date": self.expiry_date.date().toString("yyyy-MM-dd"),
            "notes": self.notes.toPlainText().strip(),
        }


class RecordPurchaseDialog(QDialog):
    """Dialog for recording a purchase"""

    def __init__(self, parent=None, components: list[dict] | None = None):
        super().__init__(parent)
        self.components = components or []
        self.setWindowTitle(tr("component_inventory_record_purchase"))
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QFormLayout()
        self.setLayout(layout)

        # Existing component (dropdown)
        self.existing_component = QComboBox()
        for comp in self.components:
            name = comp.get("component_name", "")
            comp_type = str(comp.get("component_type", "")).capitalize()
            label = f"{name} ({comp_type})"
            self.existing_component.addItem(label, comp)
        layout.addRow(
            tr("component_inventory_component_label"), self.existing_component
        )

        # Quantity purchased
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 999999)
        self.quantity.setValue(100)
        layout.addRow(tr("component_inventory_quantity_label"), self.quantity)

        # Total cost
        self.total_cost = QDoubleSpinBox()
        self.total_cost.setRange(0, 9999.99)
        self.total_cost.setValue(52.00)
        self.total_cost.setPrefix("$")
        self.total_cost.setDecimals(2)
        layout.addRow(tr("component_inventory_total_cost_label"), self.total_cost)

        # Cost per unit (auto-calculated)
        self.cost_per_unit_label = QLabel("$0.520")
        self.cost_per_unit_label.setStyleSheet("font-weight: bold;")
        layout.addRow(
            tr("component_inventory_cost_per_unit_label"), self.cost_per_unit_label
        )

        # Update cost per unit when values change
        self.quantity.valueChanged.connect(self.update_cost_per_unit)
        self.total_cost.valueChanged.connect(self.update_cost_per_unit)

        # Supplier
        self.supplier = QLineEdit()
        self.supplier.setPlaceholderText(tr("component_inventory_supplier_placeholder"))
        layout.addRow(tr("component_inventory_supplier_label"), self.supplier)

        # Purchase date
        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.currentDate())
        self.purchase_date.setCalendarPopup(True)
        layout.addRow(tr("component_inventory_purchase_date_label"), self.purchase_date)

        # Lot number (for this purchase)
        self.lot_number = QLineEdit()
        self.lot_number.setPlaceholderText(
            tr("component_inventory_purchase_lot_placeholder")
        )
        layout.addRow(tr("component_inventory_lot_number_label"), self.lot_number)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText(
            tr("component_inventory_purchase_notes_placeholder")
        )
        layout.addRow(tr("component_inventory_notes_label"), self.notes)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def update_cost_per_unit(self):
        """Update cost per unit calculation"""
        if self.quantity.value() > 0:
            cpu = self.total_cost.value() / self.quantity.value()
            self.cost_per_unit_label.setText(f"${cpu:.3f}")

    def get_data(self) -> dict:
        comp = self.existing_component.currentData()
        if not comp:
            return {}

        quantity = self.quantity.value()
        cost_per_unit = self.total_cost.value() / quantity if quantity > 0 else 0.0

        return {
            "component_name": comp.get("component_name", ""),
            "component_type": comp.get("component_type", ""),
            "manufacturer": comp.get("manufacturer", ""),
            "lot_number": self.lot_number.text().strip(),
            "quantity": quantity,
            "unit": comp.get("unit", ""),
            "cost_per_unit": cost_per_unit,
            "location": comp.get("location", ""),
            "purchase_date": self.purchase_date.date().toString("yyyy-MM-dd"),
            "expiry_date": comp.get("expiry_date", ""),
            "notes": self.notes.toPlainText().strip(),
        }


class CostAnalysisDialog(QDialog):
    """Detailed cost analysis and ROI"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = getattr(parent, "db", None) or get_database()
        self.inventory_items = self.db.execute_query(
            """
            SELECT *
            FROM inventory_items
            ORDER BY COALESCE(purchase_date, created_date) DESC, id DESC
            """
        )
        self.loading_sessions = self.db.execute_query(
            """
            SELECT date, quantity, total_cost, powder_weight_min, powder_weight_max
            FROM loading_sessions
            ORDER BY date DESC, id DESC
            """
        )
        self.setWindowTitle(tr("component_inventory_cost_analysis_roi"))
        self.resize(800, 600)
        self.init_ui()

    @staticmethod
    def _safe_float(value) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _format_currency(value: float, decimals: int = 2) -> str:
        return f"${value:,.{decimals}f}"

    @staticmethod
    def _format_change(change: float, percent: float | None) -> str:
        if percent is None:
            return f"{change:+.3f}"
        return f"{change:+.3f} ({percent:+.1f}%)"

    @staticmethod
    def _format_quantity(value: float) -> str:
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.2f}"

    def _component_usage_assumptions(self) -> dict[str, tuple[float, str]]:
        powder_charge = 42.0
        charge_samples = []
        for session in self.loading_sessions:
            powder_min = self._safe_float(session.get("powder_weight_min"))
            powder_max = self._safe_float(session.get("powder_weight_max"))
            if powder_min > 0 and powder_max > 0:
                charge_samples.append((powder_min + powder_max) / 2)
            elif powder_min > 0:
                charge_samples.append(powder_min)
            elif powder_max > 0:
                charge_samples.append(powder_max)
        if charge_samples:
            powder_charge = sum(charge_samples) / len(charge_samples)

        return {
            ComponentType.BULLET: (1.0, "1 bullet"),
            ComponentType.PRIMER: (1.0, "1 primer"),
            ComponentType.POWDER: (powder_charge, f"{powder_charge:.1f} gr powder"),
            ComponentType.BRASS: (0.1, "1 case amortized over 10 firings"),
        }

    def _latest_cost_rows(self) -> dict[str, dict]:
        rows: dict[str, dict] = {}
        for item in self.inventory_items:
            comp_type = str(item.get("component_type", "")).strip().lower()
            if comp_type in rows:
                continue
            if self._safe_float(item.get("cost_per_unit")) <= 0:
                continue
            rows[comp_type] = item
        return rows

    def _actual_cost_per_round_stats(self) -> dict[str, float | int | None]:
        values = []
        total_rounds = 0
        total_spend = 0.0
        for session in self.loading_sessions:
            quantity = int(self._safe_float(session.get("quantity")))
            total_cost = self._safe_float(session.get("total_cost"))
            if quantity <= 0 or total_cost <= 0:
                continue
            total_rounds += quantity
            total_spend += total_cost
            values.append(total_cost / quantity)

        if not values:
            return {
                "session_count": 0,
                "total_rounds": 0,
                "total_spend": 0.0,
                "avg_cost_per_round": None,
                "min_cost_per_round": None,
                "max_cost_per_round": None,
            }

        return {
            "session_count": len(values),
            "total_rounds": total_rounds,
            "total_spend": total_spend,
            "avg_cost_per_round": total_spend / total_rounds if total_rounds else None,
            "min_cost_per_round": min(values),
            "max_cost_per_round": max(values),
        }

    def _inventory_summary(self) -> dict[str, object]:
        totals_by_type: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"quantity": 0.0, "value": 0.0, "entries": 0}
        )
        total_value = 0.0
        for item in self.inventory_items:
            comp_type = str(item.get("component_type", "")).strip().lower() or "other"
            quantity = self._safe_float(item.get("quantity"))
            cost_per_unit = self._safe_float(item.get("cost_per_unit"))
            totals_by_type[comp_type]["quantity"] += quantity
            totals_by_type[comp_type]["value"] += quantity * cost_per_unit
            totals_by_type[comp_type]["entries"] += 1
            total_value += quantity * cost_per_unit
        return {"total_value": total_value, "by_type": dict(totals_by_type)}

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel(tr("component_inventory_cost_analysis_return"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Cost per Round
        tabs.addTab(
            self.create_cost_per_round_tab(),
            tr("component_inventory_cost_per_round_tab"),
        )

        # Tab 2: Savings vs Factory
        tabs.addTab(
            self.create_savings_tab(), tr("component_inventory_savings_analysis_tab")
        )

        # Tab 3: Purchase History
        tabs.addTab(
            self.create_purchase_history_tab(),
            tr("component_inventory_purchase_history_tab"),
        )

        # Tab 4: Price Trends
        tabs.addTab(
            self.create_price_trends_tab(), tr("component_inventory_price_trends_tab")
        )

        # Close button
        close_btn = QPushButton(tr("btn_close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def create_cost_per_round_tab(self) -> QWidget:
        """Cost breakdown per round"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        assumptions = self._component_usage_assumptions()
        latest_rows = self._latest_cost_rows()
        stats = self._actual_cost_per_round_stats()

        summary_label = QLabel(self)
        summary_label.setWordWrap(True)
        if stats["avg_cost_per_round"] is not None:
            summary_label.setText(
                tr("component_inventory_actual_cost_per_round_prefix")
                + f"{self._format_currency(float(stats['avg_cost_per_round']), 3)} "
                + tr(
                    "component_inventory_actual_cost_per_round_suffix",
                    sessions=stats["session_count"],
                    rounds=stats["total_rounds"],
                )
            )
        else:
            summary_label.setText(tr("component_inventory_no_loading_sessions_cost"))
        layout.addWidget(summary_label)

        table = QTableWidget(widget)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            [
                tr("component_inventory_type"),
                "Component",
                tr("component_inventory_lot_number"),
                tr("component_inventory_usage_basis"),
                tr("component_inventory_cost_per_unit"),
                tr("component_inventory_cost_per_round"),
            ]
        )

        component_order = [
            ComponentType.BULLET,
            ComponentType.POWDER,
            ComponentType.PRIMER,
            ComponentType.BRASS,
        ]
        total_estimated = 0.0
        row_count = 0
        for comp_type in component_order:
            item = latest_rows.get(comp_type)
            if not item:
                continue
            usage_amount, usage_label = assumptions[comp_type]
            cost_per_unit = self._safe_float(item.get("cost_per_unit"))
            cost_per_round = cost_per_unit * usage_amount
            total_estimated += cost_per_round

            table.insertRow(row_count)
            table.setItem(row_count, 0, QTableWidgetItem(comp_type.capitalize()))
            table.setItem(
                row_count, 1, QTableWidgetItem(item.get("component_name") or "-")
            )
            table.setItem(row_count, 2, QTableWidgetItem(item.get("lot_number") or "-"))
            table.setItem(row_count, 3, QTableWidgetItem(usage_label))
            unit = item.get("unit") or "unit"
            table.setItem(
                row_count,
                4,
                QTableWidgetItem(f"{self._format_currency(cost_per_unit, 3)} / {unit}"),
            )
            table.setItem(
                row_count,
                5,
                QTableWidgetItem(self._format_currency(cost_per_round, 3)),
            )
            row_count += 1

        if row_count == 0:
            table.setRowCount(1)
            table.setItem(
                0,
                0,
                QTableWidgetItem("No inventory cost data available yet."),
            )

        header = table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(table)

        totals_label = QLabel(self)
        totals_label.setWordWrap(True)
        totals_text = (
            f"Estimated current component cost per round: {self._format_currency(total_estimated, 3)}."
            if total_estimated > 0
            else "Estimated current component cost per round will appear when inventory items include cost data."
        )
        if stats["avg_cost_per_round"] is not None and total_estimated > 0:
            delta = total_estimated - float(stats["avg_cost_per_round"])
            totals_text += (
                f" Delta vs logged average: {self._format_currency(delta, 3)} "
                f"({self._format_currency(float(stats['avg_cost_per_round']), 3)} actual)."
            )
        totals_label.setText(totals_text)
        layout.addWidget(totals_label)

        return widget

    def create_savings_tab(self) -> QWidget:
        """ROI and savings analysis"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        stats = self._actual_cost_per_round_stats()
        summary = QLabel(widget)
        summary.setWordWrap(True)
        if stats["session_count"]:
            summary.setText(
                f"Logged loading sessions: {stats['session_count']}. "
                f"Total spend: {self._format_currency(float(stats['total_spend']))}. "
                f"Average actual cost per round: {self._format_currency(float(stats['avg_cost_per_round']), 3)}."
            )
        else:
            summary.setText(
                "Savings analysis becomes more useful after logging loading sessions with quantity and total cost."
            )
        layout.addWidget(summary)

        summary_table = QTableWidget(widget)
        summary_table.setColumnCount(2)
        summary_table.setHorizontalHeaderLabels(["Metric", "Value"])

        summary_rows = [
            ("Logged sessions", str(stats["session_count"])),
            ("Rounds loaded", str(stats["total_rounds"])),
            ("Total spend", self._format_currency(float(stats["total_spend"]))),
            (
                "Average cost / round",
                (
                    self._format_currency(float(stats["avg_cost_per_round"]), 3)
                    if stats["avg_cost_per_round"] is not None
                    else "-"
                ),
            ),
            (
                "Lowest logged cost / round",
                (
                    self._format_currency(float(stats["min_cost_per_round"]), 3)
                    if stats["min_cost_per_round"] is not None
                    else "-"
                ),
            ),
            (
                "Highest logged cost / round",
                (
                    self._format_currency(float(stats["max_cost_per_round"]), 3)
                    if stats["max_cost_per_round"] is not None
                    else "-"
                ),
            ),
        ]
        summary_table.setRowCount(len(summary_rows))
        for row, (label, value) in enumerate(summary_rows):
            summary_table.setItem(row, 0, QTableWidgetItem(label))
            summary_table.setItem(row, 1, QTableWidgetItem(value))
        header = summary_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(summary_table)

        inventory = self._inventory_summary()
        breakdown_label = QLabel("Current inventory value by component type")
        breakdown_label.setProperty("role", "subtitle")
        layout.addWidget(breakdown_label)

        breakdown_table = QTableWidget(widget)
        breakdown_table.setColumnCount(4)
        breakdown_table.setHorizontalHeaderLabels(
            ["Type", "Entries", "Quantity", "Inventory Value"]
        )
        type_rows = sorted(inventory["by_type"].items())
        breakdown_table.setRowCount(len(type_rows) + 1)
        for row, (comp_type, totals) in enumerate(type_rows):
            breakdown_table.setItem(row, 0, QTableWidgetItem(comp_type.capitalize()))
            breakdown_table.setItem(row, 1, QTableWidgetItem(str(totals["entries"])))
            breakdown_table.setItem(
                row,
                2,
                QTableWidgetItem(self._format_quantity(float(totals["quantity"]))),
            )
            breakdown_table.setItem(
                row,
                3,
                QTableWidgetItem(self._format_currency(float(totals["value"]))),
            )
        total_row = len(type_rows)
        breakdown_table.setItem(total_row, 0, QTableWidgetItem("Total"))
        breakdown_table.setItem(
            total_row, 1, QTableWidgetItem(str(len(self.inventory_items)))
        )
        breakdown_table.setItem(total_row, 2, QTableWidgetItem("-"))
        breakdown_table.setItem(
            total_row,
            3,
            QTableWidgetItem(self._format_currency(float(inventory["total_value"]))),
        )
        header = breakdown_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(breakdown_table)

        return widget

    def create_purchase_history_tab(self) -> QWidget:
        """Purchase history with trends"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        layout.addWidget(QLabel("<b>Recent Purchases:</b>"))

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["Date", "Component", "Lot #", "Qty", "Cost", "Supplier", "Notes"]
        )

        table.setRowCount(max(len(self.inventory_items), 1))
        if self.inventory_items:
            for row, item in enumerate(self.inventory_items):
                quantity = self._safe_float(item.get("quantity"))
                cost_per_unit = self._safe_float(item.get("cost_per_unit"))
                total_cost = quantity * cost_per_unit
                table.setItem(
                    row,
                    0,
                    QTableWidgetItem(
                        item.get("purchase_date") or item.get("created_date") or "-"
                    ),
                )
                table.setItem(
                    row,
                    1,
                    QTableWidgetItem(item.get("component_name") or "-"),
                )
                table.setItem(row, 2, QTableWidgetItem(item.get("lot_number") or "-"))
                unit = item.get("unit") or ""
                table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        f"{self._format_quantity(quantity)} {unit}".strip()
                    ),
                )
                table.setItem(
                    row, 4, QTableWidgetItem(self._format_currency(total_cost))
                )
                table.setItem(row, 5, QTableWidgetItem(item.get("manufacturer") or "-"))
                table.setItem(row, 6, QTableWidgetItem(item.get("notes") or "-"))
        else:
            table.setItem(0, 0, QTableWidgetItem("No inventory purchases logged yet."))

        header = table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(table)

        return widget

    def create_price_trends_tab(self) -> QWidget:
        """Price trending over time"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        intro = QLabel(
            "Latest recorded price changes per component based on inventory purchase history."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        grouped_rows: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for item in self.inventory_items:
            if self._safe_float(item.get("cost_per_unit")) <= 0:
                continue
            key = (
                item.get("component_name") or "Unknown",
                item.get("unit") or "unit",
            )
            grouped_rows[key].append(item)

        trend_rows = []
        for (component_name, unit), rows in grouped_rows.items():
            if len(rows) < 2:
                continue
            latest = rows[0]
            previous = rows[1]
            latest_cost = self._safe_float(latest.get("cost_per_unit"))
            previous_cost = self._safe_float(previous.get("cost_per_unit"))
            if previous_cost <= 0:
                percent = None
            else:
                percent = ((latest_cost - previous_cost) / previous_cost) * 100
            trend_rows.append(
                (
                    latest.get("purchase_date") or latest.get("created_date") or "-",
                    component_name,
                    unit,
                    self._format_currency(latest_cost, 3),
                    self._format_currency(previous_cost, 3),
                    self._format_change(latest_cost - previous_cost, percent),
                )
            )

        table = QTableWidget(widget)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["Latest Date", "Component", "Unit", "Latest", "Previous", "Change"]
        )
        table.setRowCount(max(len(trend_rows), 1))
        if trend_rows:
            for row, values in enumerate(trend_rows):
                for column, value in enumerate(values):
                    table.setItem(row, column, QTableWidgetItem(value))
        else:
            table.setItem(
                0,
                0,
                QTableWidgetItem(
                    "Need at least two priced purchases of the same component to show a trend."
                ),
            )

        header = table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(table)

        return widget


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dashboard = InventoryDashboard()
    dashboard.show()
    dashboard.resize(1200, 800)

    sys.exit(app.exec())
