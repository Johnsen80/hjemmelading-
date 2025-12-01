"""
Component Inventory & Cost Tracking System
Track EVERYTHING you own + costs + usage + ROI!

The #1 most requested feature by reloaders! 💰
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QGroupBox, QLineEdit, QDoubleSpinBox, QSpinBox,
                            QComboBox, QDateEdit, QTextEdit, QDialog,
                            QDialogButtonBox, QFormLayout, QMessageBox,
                            QTabWidget, QProgressBar, QSplitter, QGridLayout,
                            QFrame)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json


class ComponentType:
    """Component type constants"""
    BULLET = "bullet"
    POWDER = "powder"
    PRIMER = "primer"
    BRASS = "brass"
    OTHER = "other"


class InventoryDashboard(QWidget):
    """
    Main inventory dashboard with visual overview
    Shows stock levels, warnings, quick stats
    """
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_inventory_data()
    
    def init_ui(self):
        """Initialize dashboard UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QLabel("💰 Component Inventory & Cost Tracking")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(header)
        
        # Quick stats row
        stats_layout = QHBoxLayout()
        
        # Total value card
        self.card_total_value = self.create_stat_card(
            "💵 Total Inventory Value",
            "$2,847.50",
            "#3498db"
        )
        stats_layout.addWidget(self.card_total_value)
        
        # Savings vs factory
        self.card_savings = self.create_stat_card(
            "🎯 Savings vs Factory",
            "$1,234.00",
            "#27ae60"
        )
        stats_layout.addWidget(self.card_savings)
        
        # Low stock warnings
        self.card_warnings = self.create_stat_card(
            "⚠️ Low Stock Items",
            "3 items",
            "#e74c3c"
        )
        stats_layout.addWidget(self.card_warnings)
        
        # Rounds can make
        self.card_rounds = self.create_stat_card(
            "📦 Rounds Available",
            "1,247 rounds",
            "#9b59b6"
        )
        stats_layout.addWidget(self.card_rounds)
        
        layout.addLayout(stats_layout)
        
        # Component overview (grid of progress bars)
        component_group = QGroupBox("📊 Component Stock Levels")
        component_layout = QGridLayout()
        component_group.setLayout(component_layout)
        
        # Bullets
        component_layout.addWidget(QLabel("<b>Bullets:</b>"), 0, 0)
        self.bullets_bar = self.create_stock_bar(850, 1000, "Berger 140gr Hybrid")
        component_layout.addLayout(self.bullets_bar, 0, 1)
        
        # Powder
        component_layout.addWidget(QLabel("<b>Powder:</b>"), 1, 0)
        self.powder_bar = self.create_stock_bar(420, 500, "Vihtavuori N140 (420gr / 8lb)")
        component_layout.addLayout(self.powder_bar, 1, 1)
        
        # Primers
        component_layout.addWidget(QLabel("<b>Primers:</b>"), 2, 0)
        self.primers_bar = self.create_stock_bar(87, 1000, "CCI BR-2 (⚠️ LOW!)")
        component_layout.addLayout(self.primers_bar, 2, 1)
        
        # Brass
        component_layout.addWidget(QLabel("<b>Brass:</b>"), 3, 0)
        self.brass_bar = self.create_stock_bar(200, 200, "Lapua 6.5 CM")
        component_layout.addLayout(self.brass_bar, 3, 1)
        
        layout.addWidget(component_group)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.btn_add_component = QPushButton("➕ Add Component")
        self.btn_add_component.setStyleSheet("""
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
        """)
        self.btn_add_component.clicked.connect(self.add_component)
        btn_layout.addWidget(self.btn_add_component)
        
        self.btn_record_purchase = QPushButton("🛒 Record Purchase")
        self.btn_record_purchase.clicked.connect(self.record_purchase)
        btn_layout.addWidget(self.btn_record_purchase)
        
        self.btn_usage_history = QPushButton("📊 Usage History")
        self.btn_usage_history.clicked.connect(self.show_usage_history)
        btn_layout.addWidget(self.btn_usage_history)
        
        self.btn_cost_analysis = QPushButton("💰 Cost Analysis")
        self.btn_cost_analysis.clicked.connect(self.show_cost_analysis)
        btn_layout.addWidget(self.btn_cost_analysis)
        
        layout.addLayout(btn_layout)
        
        # Detailed inventory table
        table_label = QLabel("<b>📋 Detailed Inventory</b>")
        table_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        layout.addWidget(table_label)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(10)
        self.inventory_table.setHorizontalHeaderLabels([
            "Component", "Type", "Lot #", "Quantity", "Unit", "Cost/Unit", "Total Value",
            "Location", "Expiry", "Actions"
        ])
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.inventory_table)
    
    def create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create colored stat card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        card_layout = QVBoxLayout()
        card.setLayout(card_layout)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.9);")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        card_layout.addWidget(value_label)
        
        return card
    
    def create_stock_bar(self, current: int, maximum: int, label: str) -> QHBoxLayout:
        """Create stock level progress bar with label"""
        layout = QHBoxLayout()
        
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(maximum)
        bar.setValue(current)
        bar.setTextVisible(True)
        bar.setFormat(f"{current}/{maximum} - {label}")
        
        # Color code based on level
        percentage = (current / maximum) * 100
        if percentage < 10:
            bar.setStyleSheet("""
                QProgressBar { border: 2px solid #e74c3c; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #e74c3c; }
            """)
        elif percentage < 25:
            bar.setStyleSheet("""
                QProgressBar { border: 2px solid #f39c12; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #f39c12; }
            """)
        else:
            bar.setStyleSheet("""
                QProgressBar { border: 2px solid #27ae60; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #27ae60; }
            """)
        
        layout.addWidget(bar)
        
        return layout
    
    def load_inventory_data(self):
        """Load inventory from database"""
        # Sample data
        sample_inventory = [
            {
                'name': 'Berger 140gr Hybrid Target',
                'type': 'Bullet',
                'lot': '2024-08-L7342',
                'quantity': 850,
                'unit': 'pcs',
                'cost_per_unit': 0.52,
                'total_value': 442.00,
                'location': 'Reloading Room - Shelf A',
                'expiry': 'N/A'
            },
            {
                'name': 'Vihtavuori N140',
                'type': 'Powder',
                'lot': 'V140-231015-A',
                'quantity': 3629,
                'unit': 'gr',
                'cost_per_unit': 0.045,
                'total_value': 163.31,
                'location': 'Powder Cabinet',
                'expiry': '2027-06'
            },
            {
                'name': 'CCI BR-2 Large Rifle Primer',
                'type': 'Primer',
                'lot': 'M48K2024',
                'quantity': 87,
                'unit': 'pcs',
                'cost_per_unit': 0.08,
                'total_value': 6.96,
                'location': 'Ammo Can - Primers',
                'expiry': 'N/A'
            },
            {
                'name': 'Lapua 6.5 Creedmoor Brass',
                'type': 'Brass',
                'lot': 'LP6524-R2',
                'quantity': 200,
                'unit': 'pcs',
                'cost_per_unit': 1.20,
                'total_value': 240.00,
                'location': 'Brass Box #1 (2x fired)',
                'expiry': 'N/A'
            },
        ]
        
        self.inventory_table.setRowCount(0)
        
        for item in sample_inventory:
            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)
            
            self.inventory_table.setItem(row, 0, QTableWidgetItem(item['name']))
            
            type_item = QTableWidgetItem(item['type'])
            # Color code by type
            if item['type'] == 'Bullet':
                type_item.setBackground(QColor("#e8f4f8"))
            elif item['type'] == 'Powder':
                type_item.setBackground(QColor("#fff9c4"))
            elif item['type'] == 'Primer':
                type_item.setBackground(QColor("#ffcccc"))
            elif item['type'] == 'Brass':
                type_item.setBackground(QColor("#d5f4e6"))
            self.inventory_table.setItem(row, 1, type_item)
            
            # Lot number
            lot_item = QTableWidgetItem(item['lot'])
            lot_item.setFont(QFont("Courier New", 9))  # Monospace for lot numbers
            self.inventory_table.setItem(row, 2, lot_item)
            
            qty_item = QTableWidgetItem(f"{item['quantity']}")
            # Warning if low stock
            if (item['type'] == 'Primer' and item['quantity'] < 100) or \
               (item['type'] == 'Bullet' and item['quantity'] < 100):
                qty_item.setBackground(QColor("#ffcccc"))
                qty_item.setForeground(QColor("#c0392b"))
            self.inventory_table.setItem(row, 3, qty_item)
            
            self.inventory_table.setItem(row, 4, QTableWidgetItem(item['unit']))
            self.inventory_table.setItem(row, 5, QTableWidgetItem(f"${item['cost_per_unit']:.3f}"))
            self.inventory_table.setItem(row, 6, QTableWidgetItem(f"${item['total_value']:.2f}"))
            self.inventory_table.setItem(row, 7, QTableWidgetItem(item['location']))
            self.inventory_table.setItem(row, 8, QTableWidgetItem(item['expiry']))
            
            # Actions button
            btn_edit = QPushButton("Edit")
            btn_edit.setMaximumWidth(60)
            self.inventory_table.setCellWidget(row, 9, btn_edit)
        
        self.inventory_table.resizeColumnsToContents()
    
    def add_component(self):
        """Add new component to inventory"""
        dialog = AddComponentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # TODO: Save to database
            self.load_inventory_data()
            QMessageBox.information(self, "Success", "Component added to inventory!")
    
    def record_purchase(self):
        """Record a purchase"""
        dialog = RecordPurchaseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # TODO: Save to database
            self.load_inventory_data()
            QMessageBox.information(self, "Success", "Purchase recorded!")
    
    def show_usage_history(self):
        """Show component usage history"""
        QMessageBox.information(
            self,
            "Usage History",
            "📊 Usage history feature coming!\n\n" +
            "Will show:\n" +
            "• Components used per month\n" +
            "• Cost per round trends\n" +
            "• Most used components\n" +
            "• Auto-deduct from loads"
        )
    
    def show_cost_analysis(self):
        """Show detailed cost analysis"""
        dialog = CostAnalysisDialog(self)
        dialog.exec()


class AddComponentDialog(QDialog):
    """Dialog for adding new component"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Component")
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QFormLayout()
        self.setLayout(layout)
        
        # Component type
        self.component_type = QComboBox()
        self.component_type.addItems(["Bullet", "Powder", "Primer", "Brass", "Other"])
        layout.addRow("Component Type:", self.component_type)
        
        # Name
        self.component_name = QLineEdit()
        self.component_name.setPlaceholderText("e.g., Berger 140gr Hybrid Target")
        layout.addRow("Name:", self.component_name)
        
        # Manufacturer
        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText("e.g., Berger, Vihtavuori, CCI")
        layout.addRow("Manufacturer:", self.manufacturer)
        
        # Lot number
        self.lot_number = QLineEdit()
        self.lot_number.setPlaceholderText("Component lot/batch number")
        layout.addRow("Lot Number:", self.lot_number)
        
        # Quantity
        self.quantity = QSpinBox()
        self.quantity.setRange(0, 999999)
        self.quantity.setValue(100)
        layout.addRow("Quantity:", self.quantity)
        
        # Unit
        self.unit = QComboBox()
        self.unit.addItems(["pcs", "gr", "lb", "kg", "box"])
        layout.addRow("Unit:", self.unit)
        
        # Cost per unit
        self.cost_per_unit = QDoubleSpinBox()
        self.cost_per_unit.setRange(0, 999.99)
        self.cost_per_unit.setValue(0.50)
        self.cost_per_unit.setPrefix("$")
        self.cost_per_unit.setDecimals(3)
        layout.addRow("Cost per Unit:", self.cost_per_unit)
        
        # Location
        self.location = QLineEdit()
        self.location.setPlaceholderText("e.g., Shelf A, Box 3, Gun Safe")
        layout.addRow("Storage Location:", self.location)
        
        # Purchase date
        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.currentDate())
        self.purchase_date.setCalendarPopup(True)
        layout.addRow("Purchase Date:", self.purchase_date)
        
        # Expiry date (optional for powder)
        self.expiry_date = QDateEdit()
        self.expiry_date.setDate(QDate.currentDate().addYears(5))
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setSpecialValueText("N/A")
        layout.addRow("Expiry Date:", self.expiry_date)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Any notes about this component...")
        layout.addRow("Notes:", self.notes)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class RecordPurchaseDialog(QDialog):
    """Dialog for recording a purchase"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Purchase")
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QFormLayout()
        self.setLayout(layout)
        
        # Existing component (dropdown)
        self.existing_component = QComboBox()
        self.existing_component.addItems([
            "Berger 140gr Hybrid Target",
            "Vihtavuori N140",
            "CCI BR-2 Large Rifle Primer",
            "Lapua 6.5 Creedmoor Brass"
        ])
        layout.addRow("Component:", self.existing_component)
        
        # Quantity purchased
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 999999)
        self.quantity.setValue(100)
        layout.addRow("Quantity:", self.quantity)
        
        # Total cost
        self.total_cost = QDoubleSpinBox()
        self.total_cost.setRange(0, 9999.99)
        self.total_cost.setValue(52.00)
        self.total_cost.setPrefix("$")
        self.total_cost.setDecimals(2)
        layout.addRow("Total Cost:", self.total_cost)
        
        # Cost per unit (auto-calculated)
        self.cost_per_unit_label = QLabel("$0.520")
        self.cost_per_unit_label.setStyleSheet("font-weight: bold;")
        layout.addRow("Cost per Unit:", self.cost_per_unit_label)
        
        # Update cost per unit when values change
        self.quantity.valueChanged.connect(self.update_cost_per_unit)
        self.total_cost.valueChanged.connect(self.update_cost_per_unit)
        
        # Supplier
        self.supplier = QLineEdit()
        self.supplier.setPlaceholderText("e.g., Brownells, MidwayUSA, Local gun shop")
        layout.addRow("Supplier:", self.supplier)
        
        # Purchase date
        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.currentDate())
        self.purchase_date.setCalendarPopup(True)
        layout.addRow("Purchase Date:", self.purchase_date)
        
        # Lot number (for this purchase)
        self.lot_number = QLineEdit()
        self.lot_number.setPlaceholderText("Lot/batch number from package")
        layout.addRow("Lot Number:", self.lot_number)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("e.g., Black Friday sale, free shipping")
        layout.addRow("Notes:", self.notes)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def update_cost_per_unit(self):
        """Update cost per unit calculation"""
        if self.quantity.value() > 0:
            cpu = self.total_cost.value() / self.quantity.value()
            self.cost_per_unit_label.setText(f"${cpu:.3f}")


class CostAnalysisDialog(QDialog):
    """Detailed cost analysis and ROI"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cost Analysis & ROI")
        self.resize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("💰 Cost Analysis & Return on Investment")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Tab 1: Cost per Round
        tabs.addTab(self.create_cost_per_round_tab(), "Cost per Round")
        
        # Tab 2: Savings vs Factory
        tabs.addTab(self.create_savings_tab(), "Savings Analysis")
        
        # Tab 3: Purchase History
        tabs.addTab(self.create_purchase_history_tab(), "Purchase History")
        
        # Tab 4: Price Trends
        tabs.addTab(self.create_price_trends_tab(), "Price Trends")
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def create_cost_per_round_tab(self) -> QWidget:
        """Cost breakdown per round"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        info_html = """
        <h3>Cost per Round Breakdown</h3>
        <p><b>Example: 6.5 Creedmoor Match Load</b></p>
        
        <table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Component</th>
                <th>Lot Number</th>
                <th>Quantity</th>
                <th>Cost/Unit</th>
                <th>Cost/Round</th>
            </tr>
            <tr>
                <td>Berger 140gr Hybrid</td>
                <td><code>2024-08-L7342</code></td>
                <td>1 pc</td>
                <td>$0.520</td>
                <td><b>$0.520</b></td>
            </tr>
            <tr>
                <td>Vihtavuori N140</td>
                <td><code>V140-231015-A</code></td>
                <td>42.0 gr</td>
                <td>$0.045/gr</td>
                <td><b>$1.890</b></td>
            </tr>
            <tr>
                <td>CCI BR-2 Primer</td>
                <td><code>M48K2024</code></td>
                <td>1 pc</td>
                <td>$0.080</td>
                <td><b>$0.080</b></td>
            </tr>
            <tr>
                <td>Lapua Brass (amortized)</td>
                <td><code>LP6524-R2</code></td>
                <td>1 pc / 10 firings</td>
                <td>$1.200</td>
                <td><b>$0.120</b></td>
            </tr>
            <tr style='background-color: #d5f4e6; font-weight: bold;'>
                <td colspan='3'>TOTAL COST PER ROUND</td>
                <td><b style='color: #27ae60; font-size: 16px;'>$2.61</b></td>
            </tr>
        </table>
        
        <br>
        <p><b>Compare to Factory Match:</b></p>
        <ul>
            <li>Hornady Match 140gr ELD: <b>$2.80/round</b> → Save $0.19/round</li>
            <li>Federal Gold Medal 140gr: <b>$3.20/round</b> → Save $0.59/round</li>
            <li>Lapua Scenar 139gr: <b>$3.50/round</b> → Save $0.89/round</li>
        </ul>
        
        <p style='background-color: #d5f4e6; padding: 15px; border-radius: 5px;'>
            <b>💡 At 1000 rounds/year:</b><br>
            Savings vs Hornady: <b>$190/year</b><br>
            Savings vs Federal: <b>$590/year</b><br>
            Savings vs Lapua: <b>$890/year</b>
        </p>
        
        <p style='background-color: #fff9c4; padding: 15px; border-radius: 5px; margin-top: 10px;'>
            <b>🎯 Why Lot Numbers Matter:</b><br>
            When you find a <b>winning combination</b>, lot numbers let you recreate it EXACTLY!<br>
            Different lots can vary in velocity by 20-50 fps even with same charge weight.<br>
            <br>
            <b>Example:</b> Your best load (SD 5.8, 0.68 MOA) used lot <code>V140-231015-A</code>.<br>
            When reordering powder, try to get the SAME lot for consistency! 🏆
        </p>
        """
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(info_html)
        layout.addWidget(text)
        
        return widget
    
    def create_savings_tab(self) -> QWidget:
        """ROI and savings analysis"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        roi_html = """
        <h3>📊 Return on Investment Analysis</h3>
        
        <h4>Initial Equipment Investment:</h4>
        <table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>
            <tr><td>Reloading Press (RCBS Rock Chucker)</td><td align='right'>$180</td></tr>
            <tr><td>Dies (Redding Match)</td><td align='right'>$85</td></tr>
            <tr><td>Scale (RCBS Chargemaster)</td><td align='right'>$350</td></tr>
            <tr><td>Calipers, tools, accessories</td><td align='right'>$150</td></tr>
            <tr style='font-weight: bold; background-color: #ecf0f1;'>
                <td>TOTAL EQUIPMENT</td><td align='right'>$765</td></tr>
        </table>
        
        <br>
        <h4>📈 Cumulative Savings (vs Federal Gold Medal @ $3.20/round):</h4>
        <p style='background-color: #ecf0f1; padding: 10px; border-radius: 5px;'>
            Your cost: <b>$2.61/round</b><br>
            Savings: <b>$0.59/round</b>
        </p>
        
        <table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1; font-weight: bold;'>
                <th>Rounds Loaded</th>
                <th>Total Savings</th>
                <th>Net ROI</th>
            </tr>
            <tr>
                <td>500</td>
                <td>$295</td>
                <td style='color: #e74c3c;'><b>-$470</b> (not yet profitable)</td>
            </tr>
            <tr>
                <td>1,000</td>
                <td>$590</td>
                <td style='color: #e74c3c;'><b>-$175</b> (not yet profitable)</td>
            </tr>
            <tr style='background-color: #d5f4e6;'>
                <td><b>1,297</b></td>
                <td><b>$765</b></td>
                <td style='color: #27ae60;'><b>$0</b> (BREAK-EVEN! 🎉)</td>
            </tr>
            <tr>
                <td>2,000</td>
                <td>$1,180</td>
                <td style='color: #27ae60;'><b>+$415</b></td>
            </tr>
            <tr style='background-color: #d5f4e6;'>
                <td><b>5,000</b></td>
                <td><b>$2,950</b></td>
                <td style='color: #27ae60; font-size: 16px;'><b>+$2,185</b> 💰</td>
            </tr>
        </table>
        
        <br>
        <p style='background-color: #d5f4e6; padding: 15px; border-radius: 5px; font-size: 14px;'>
            <b>🎯 YOUR STATUS:</b><br>
            Rounds loaded to date: <b>2,847 rounds</b><br>
            Total savings: <b>$1,680</b><br>
            Net ROI after equipment: <b style='color: #27ae60; font-size: 18px;'>+$915</b> 🏆<br>
            <br>
            <b>You broke even at round 1,297!</b><br>
            Every round since = pure savings! 💵
        </p>
        """
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(roi_html)
        layout.addWidget(text)
        
        return widget
    
    def create_purchase_history_tab(self) -> QWidget:
        """Purchase history with trends"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        layout.addWidget(QLabel("<b>Recent Purchases:</b>"))
        
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Date", "Component", "Lot #", "Qty", "Cost", "Supplier", "Notes"
        ])
        
        # Sample data
        purchases = [
            ("2024-11-15", "Vihtavuori N140 (8lb)", "V140-231015-A", "3629 gr", "$163.31", "Brownells", "Sale price!"),
            ("2024-10-28", "CCI BR-2 Primers", "M48K2024", "100", "$8.00", "Local shop", "Same lot as before"),
            ("2024-09-12", "Berger 140gr Hybrid", "2024-08-L7342", "500", "$260.00", "MidwayUSA", "Great lot!"),
        ]
        
        table.setRowCount(len(purchases))
        for i, purchase in enumerate(purchases):
            for j, value in enumerate(purchase):
                table.setItem(i, j, QTableWidgetItem(value))
        
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        
        return widget
    
    def create_price_trends_tab(self) -> QWidget:
        """Price trending over time"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        trends_html = """
        <h3>📈 Component Price Trends</h3>
        <p>Track how prices change over time - catch sales!</p>
        
        <h4>Vihtavuori N140 (per lb):</h4>
        <table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Date</th>
                <th>Price/lb</th>
                <th>Change</th>
            </tr>
            <tr>
                <td>Nov 2024</td>
                <td>$45.00</td>
                <td style='color: #27ae60;'>-5% (SALE! ✅)</td>
            </tr>
            <tr>
                <td>Aug 2024</td>
                <td>$47.50</td>
                <td style='color: #f39c12;'>+2%</td>
            </tr>
            <tr>
                <td>May 2024</td>
                <td>$46.50</td>
                <td>—</td>
            </tr>
        </table>
        
        <br>
        <h4>CCI BR-2 Primers (per 100):</h4>
        <table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Date</th>
                <th>Price/100</th>
                <th>Change</th>
            </tr>
            <tr>
                <td>Oct 2024</td>
                <td>$8.00</td>
                <td style='color: #e74c3c;'>+14% 😢</td>
            </tr>
            <tr>
                <td>Jul 2024</td>
                <td>$7.00</td>
                <td style='color: #e74c3c;'>+17%</td>
            </tr>
            <tr>
                <td>Mar 2024</td>
                <td>$6.00</td>
                <td>—</td>
            </tr>
        </table>
        
        <br>
        <p style='background-color: #fff9c4; padding: 10px; border-radius: 5px;'>
            <b>💡 Pro tip:</b> Set price alerts! App will notify when components drop below target price.
        </p>
        """
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(trends_html)
        layout.addWidget(text)
        
        return widget


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dashboard = InventoryDashboard()
    dashboard.show()
    dashboard.resize(1200, 800)
    
    sys.exit(app.exec())
