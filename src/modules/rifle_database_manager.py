"""
Komplett Rifle Database Manager
Håndterer alle rifle data inkl. harmonikk, skuddteller, bullet jump, vedlikehold
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QTableWidget, QTableWidgetItem, QLabel, QDialog,
                            QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox,
                            QTextEdit, QSpinBox, QGroupBox, QMessageBox,
                            QTabWidget, QDateEdit, QCheckBox, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont
from src.database.database import get_database
from datetime import datetime
from typing import Optional, Dict, List


class RifleDatabaseManager(QWidget):
    """
    Hovedvindu for rifle database management
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.init_ui()
        self.load_rifles()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🎯 Våpen Database")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        desc = QLabel(
            "Komplett database over dine våpen med pipe-data, harmonikk, skuddteller, "
            "bullet jump målinger og vedlikehold."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        layout.addWidget(desc)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("➕ Nytt Våpen")
        self.btn_add.clicked.connect(self.add_rifle)
        self.btn_add.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold;")
        
        self.btn_edit = QPushButton("✏️ Rediger")
        self.btn_edit.clicked.connect(self.edit_rifle)
        self.btn_edit.setStyleSheet("background-color: #3498db; color: white; padding: 8px;")
        
        self.btn_view_details = QPushButton("🔍 Detaljer")
        self.btn_view_details.clicked.connect(self.view_rifle_details)
        self.btn_view_details.setStyleSheet("background-color: #9b59b6; color: white; padding: 8px;")
        
        self.btn_add_rounds = QPushButton("🎯 Legg til Skudd")
        self.btn_add_rounds.clicked.connect(self.add_rounds_fired)
        self.btn_add_rounds.setStyleSheet("background-color: #e67e22; color: white; padding: 8px;")
        
        self.btn_maintenance = QPushButton("🔧 Vedlikehold")
        self.btn_maintenance.clicked.connect(self.log_maintenance)
        self.btn_maintenance.setStyleSheet("background-color: #16a085; color: white; padding: 8px;")
        
        self.btn_accuracy_test = QPushButton("📊 Accuracy Test")
        self.btn_accuracy_test.clicked.connect(self.manage_accuracy_tests)
        self.btn_accuracy_test.setStyleSheet("background-color: #8e44ad; color: white; padding: 8px; font-weight: bold;")
        
        self.btn_delete = QPushButton("🗑️ Slett")
        self.btn_delete.clicked.connect(self.delete_rifle)
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px;")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_view_details)
        btn_layout.addWidget(self.btn_add_rounds)
        btn_layout.addWidget(self.btn_maintenance)
        btn_layout.addWidget(self.btn_accuracy_test)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_delete)
        
        layout.addLayout(btn_layout)
        
        # Rifles table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Navn", "Produsent", "Modell", "Kaliber", 
            "Pipe Lengde", "Skudd Fyrt", "Status", "Siste Vedlikehold"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.view_rifle_details)
        
        layout.addWidget(self.table)
        
        # Status bar
        self.status_label = QLabel("Klar.")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_rifles(self):
        """Load all rifles from database"""
        rifles = self.db.get_all('rifles', 'name')
        
        self.table.setRowCount(len(rifles))
        
        for row, rifle in enumerate(rifles):
            self.table.setItem(row, 0, QTableWidgetItem(str(rifle.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(rifle.get('name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(rifle.get('manufacturer', '')))
            self.table.setItem(row, 3, QTableWidgetItem(rifle.get('model', '')))
            self.table.setItem(row, 4, QTableWidgetItem(rifle.get('caliber', '')))
            
            # Barrel length
            barrel_length = rifle.get('barrel_length_inches', rifle.get('barrel_length_mm'))
            if barrel_length:
                length_str = f"{barrel_length:.1f}\""
            else:
                length_str = "-"
            self.table.setItem(row, 5, QTableWidgetItem(length_str))
            
            # Round count
            round_count = rifle.get('round_count', 0) or 0
            round_item = QTableWidgetItem(str(round_count))
            
            # Check if case measurement warning should be triggered
            accuracy_life = rifle.get('accuracy_life_estimate', 2000)
            if round_count >= 500 and round_count % 500 < 100:  # Near 500 round intervals
                round_item.setBackground(QColor(255, 200, 0, 100))  # Yellow warning
                round_item.setToolTip("⚠️ Tid for hylse-måling!")
            elif round_count > accuracy_life * 0.8:  # 80% of barrel life
                round_item.setBackground(QColor(255, 100, 100, 100))  # Red warning
                round_item.setToolTip("⚠️ Pipe nærmer seg slutten av levetiden!")
            
            self.table.setItem(row, 6, round_item)
            
            # Status
            bore_condition = rifle.get('bore_condition', 'unknown')
            status_colors = {
                'excellent': ('#27ae60', '✓ Utmerket'),
                'good': ('#3498db', '✓ God'),
                'fair': ('#f39c12', '⚠ OK'),
                'worn': ('#e74c3c', '⚠ Slitt'),
                'unknown': ('#95a5a6', '? Ukjent')
            }
            color, text = status_colors.get(bore_condition, status_colors['unknown'])
            status_item = QTableWidgetItem(text)
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 7, status_item)
            
            # Last maintenance
            last_maint = rifle.get('last_maintenance_date', '-')
            self.table.setItem(row, 8, QTableWidgetItem(last_maint if last_maint else '-'))
        
        self.status_label.setText(f"Lastet {len(rifles)} våpen.")
    
    def add_rifle(self):
        """Add new rifle"""
        dialog = RifleEditorDialog(self, rifle_id=None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rifles()
    
    def edit_rifle(self):
        """Edit selected rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen Valgt", "Velg et våpen å redigere.")
            return
        
        rifle_id = int(self.table.item(selected, 0).text())
        dialog = RifleEditorDialog(self, rifle_id=rifle_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rifles()
    
    def view_rifle_details(self):
        """View detailed rifle information"""
        selected = self.table.currentRow()
        if selected < 0:
            return
        
        rifle_id = int(self.table.item(selected, 0).text())
        dialog = RifleDetailsDialog(self, rifle_id=rifle_id)
        dialog.exec()
    
    def add_rounds_fired(self):
        """Add rounds fired to rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen Valgt", "Velg et våpen.")
            return
        
        rifle_id = int(self.table.item(selected, 0).text())
        rifle = self.db.get_by_id('rifles', rifle_id)
        
        dialog = AddRoundsFiredDialog(self, rifle)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rifles()
    
    def log_maintenance(self):
        """Log maintenance for rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen Valgt", "Velg et våpen.")
            return
        
        rifle_id = int(self.table.item(selected, 0).text())
        rifle = self.db.get_by_id('rifles', rifle_id)
        
        dialog = MaintenanceLogDialog(self, rifle)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rifles()
    
    def manage_accuracy_tests(self):
        """Open accuracy test manager for selected rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen Valgt", "Velg et våpen.")
            return
        
        rifle_id = int(self.table.item(selected, 0).text())
        rifle = self.db.get_by_id('rifles', rifle_id)
        
        from src.modules.rifle_accuracy_test_system import RifleAccuracyTestManager
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📊 Accuracy Tests - {rifle.get('name', '')}")
        dialog.setMinimumSize(1000, 600)
        
        layout = QVBoxLayout()
        test_manager = RifleAccuracyTestManager(dialog, rifle_id=rifle_id)
        layout.addWidget(test_manager)
        
        btn_close = QPushButton("✓ Lukk")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def delete_rifle(self):
        """Delete selected rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen Valgt", "Velg et våpen å slette.")
            return
        
        rifle_name = self.table.item(selected, 1).text()
        reply = QMessageBox.question(
            self, 
            "Bekreft Sletting",
            f"Er du sikker på at du vil slette '{rifle_name}'?\n\nDette vil også slette alle relaterte data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            rifle_id = int(self.table.item(selected, 0).text())
            self.db.delete('rifles', 'id = ?', (rifle_id,))
            self.load_rifles()
            self.status_label.setText(f"Slettet '{rifle_name}'.")


class RifleEditorDialog(QDialog):
    """
    Comprehensive rifle editor dialog with ALL database fields
    """
    
    def __init__(self, parent=None, rifle_id: Optional[int] = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id
        self.rifle_data = {}
        
        self.setWindowTitle("🎯 Rifle Editor" if rifle_id is None else "✏️ Rediger Rifle")
        self.setMinimumSize(900, 700)
        
        self.init_ui()
        
        if rifle_id:
            self.load_rifle_data()
    
    def init_ui(self):
        """Initialize UI with tabs"""
        layout = QVBoxLayout()
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_basic_tab(), "📋 Grunnleggende")
        self.tabs.addTab(self.create_barrel_tab(), "🔫 Pipe/Løp")
        self.tabs.addTab(self.create_chamber_tab(), "⚙️ Kammer & Twist")
        self.tabs.addTab(self.create_status_tab(), "📊 Status & Tilstand")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("💾 Lagre")
        self.btn_save.clicked.connect(self.save_rifle)
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        
        self.btn_cancel = QPushButton("❌ Avbryt")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setStyleSheet("background-color: #95a5a6; color: white; padding: 10px;")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_basic_tab(self):
        """Create basic information tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("F.eks. 'Min 6.5 Creedmoor'")
        layout.addRow("📝 Navn:", self.input_name)
        
        self.input_manufacturer = QLineEdit()
        self.input_manufacturer.setPlaceholderText("F.eks. 'Tikka', 'Remington', 'Sauer'")
        layout.addRow("🏭 Produsent:", self.input_manufacturer)
        
        self.input_model = QLineEdit()
        self.input_model.setPlaceholderText("F.eks. 'T3x', '700', '100'")
        layout.addRow("🔢 Modell:", self.input_model)
        
        self.input_caliber = QComboBox()
        self.input_caliber.setEditable(True)
        calibers = [
            '.223 Rem', '5.56 NATO', '.22-250', '.243 Win', '6mm Creedmoor',
            '6mm BR', '6.5 Creedmoor', '6.5x55 Swedish', '.260 Rem', '6.5 PRC',
            '.270 Win', '7mm-08', '7mm Rem Mag', '.308 Win', '.30-06', 
            '.300 Win Mag', '.338 Lapua Mag'
        ]
        self.input_caliber.addItems(calibers)
        layout.addRow("🎯 Kaliber:", self.input_caliber)
        
        self.input_action = QComboBox()
        self.input_action.addItems(['bolt', 'semi-auto', 'lever', 'single-shot', 'pump'])
        layout.addRow("🔩 Action Type:", self.input_action)
        
        self.input_serial = QLineEdit()
        self.input_serial.setPlaceholderText("Serienummer")
        layout.addRow("🔢 Serienummer:", self.input_serial)
        
        self.input_purchase_date = QDateEdit()
        self.input_purchase_date.setDate(QDate.currentDate())
        self.input_purchase_date.setCalendarPopup(True)
        layout.addRow("📅 Kjøpsdato:", self.input_purchase_date)
        
        self.input_notes = QTextEdit()
        self.input_notes.setMaximumHeight(100)
        self.input_notes.setPlaceholderText("Notater...")
        layout.addRow("📝 Notater:", self.input_notes)
        
        widget.setLayout(layout)
        return widget
    
    def create_barrel_tab(self):
        """Create barrel specifications tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Barrel Profile Selection
        profile_group = QGroupBox("🎯 Pipe Profil")
        profile_layout = QFormLayout()
        
        self.input_barrel_profile = QComboBox()
        profiles = self.db.execute_query("SELECT id, name, category, stiffness_rating FROM barrel_profiles ORDER BY name")
        self.input_barrel_profile.addItem("-- Velg Profil --", None)
        for profile in profiles:
            display_text = f"{profile['name']} ({profile['category']}, {profile['stiffness_rating']})"
            self.input_barrel_profile.addItem(display_text, profile['id'])
        self.input_barrel_profile.currentIndexChanged.connect(self.on_profile_selected)
        profile_layout.addRow("Profil:", self.input_barrel_profile)
        
        self.input_barrel_contour = QComboBox()
        self.input_barrel_contour.setEditable(True)
        contours = ['light', 'medium', 'heavy', 'varmint', 'bull', 'sendero', 'palma', 'custom']
        self.input_barrel_contour.addItems(contours)
        profile_layout.addRow("Kontur:", self.input_barrel_contour)
        
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)
        
        # Dimensions
        dim_group = QGroupBox("📏 Dimensjoner")
        dim_layout = QFormLayout()
        
        self.input_barrel_length = QDoubleSpinBox()
        self.input_barrel_length.setRange(10, 50)
        self.input_barrel_length.setValue(24)
        self.input_barrel_length.setSuffix(' "')
        self.input_barrel_length.setDecimals(1)
        dim_layout.addRow("Pipe Lengde:", self.input_barrel_length)
        
        self.input_muzzle_diameter = QDoubleSpinBox()
        self.input_muzzle_diameter.setRange(0.5, 2.0)
        self.input_muzzle_diameter.setValue(0.75)
        self.input_muzzle_diameter.setSuffix(' "')
        self.input_muzzle_diameter.setDecimals(3)
        dim_layout.addRow("Muzzle Diameter:", self.input_muzzle_diameter)
        
        self.input_breech_diameter = QDoubleSpinBox()
        self.input_breech_diameter.setRange(0.8, 2.0)
        self.input_breech_diameter.setValue(1.2)
        self.input_breech_diameter.setSuffix(' "')
        self.input_breech_diameter.setDecimals(3)
        dim_layout.addRow("Breech Diameter:", self.input_breech_diameter)
        
        dim_group.setLayout(dim_layout)
        layout.addWidget(dim_group)
        
        # Material & Finish
        mat_group = QGroupBox("🔧 Material & Finish")
        mat_layout = QFormLayout()
        
        self.input_barrel_material = QComboBox()
        self.input_barrel_material.addItems(['chrome-moly', 'stainless', 'carbon-fiber'])
        mat_layout.addRow("Material:", self.input_barrel_material)
        
        self.input_barrel_finish = QComboBox()
        self.input_barrel_finish.setEditable(True)
        self.input_barrel_finish.addItems(['blued', 'stainless', 'cerakote', 'nitride', 'parkerized'])
        mat_layout.addRow("Finish:", self.input_barrel_finish)
        
        self.input_barrel_manufacturer = QLineEdit()
        self.input_barrel_manufacturer.setPlaceholderText("F.eks. 'Bartlein', 'Krieger', 'Proof'")
        mat_layout.addRow("Pipe Produsent:", self.input_barrel_manufacturer)
        
        mat_group.setLayout(mat_layout)
        layout.addWidget(mat_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_chamber_tab(self):
        """Create chamber & twist specifications tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Twist Rate
        twist_group = QGroupBox("🌀 Twist Rate & Rifling")
        twist_layout = QFormLayout()
        
        self.input_twist_rate = QComboBox()
        self.input_twist_rate.setEditable(True)
        twist_rates = ['1:7', '1:7.5', '1:8', '1:8.5', '1:9', '1:9.5', '1:10', '1:11', '1:12', '1:14']
        self.input_twist_rate.addItems(twist_rates)
        twist_layout.addRow("Twist Rate:", self.input_twist_rate)
        
        self.input_twist_direction = QComboBox()
        self.input_twist_direction.addItems(['right', 'left'])
        twist_layout.addRow("Twist Direction:", self.input_twist_direction)
        
        self.input_rifling_type = QComboBox()
        self.input_rifling_type.setEditable(True)
        self.input_rifling_type.addItems(['conventional', 'polygonal', '5R', 'button', 'cut', 'broach'])
        twist_layout.addRow("Rifling Type:", self.input_rifling_type)
        
        twist_group.setLayout(twist_layout)
        layout.addWidget(twist_group)
        
        # Chamber
        chamber_group = QGroupBox("⚙️ Kammer Detaljer")
        chamber_layout = QFormLayout()
        
        self.input_chamber_spec = QComboBox()
        self.input_chamber_spec.addItems(['SAAMI', 'CIP', 'match', 'custom', 'minimum'])
        chamber_layout.addRow("Chamber Spec:", self.input_chamber_spec)
        
        self.input_freebore = QDoubleSpinBox()
        self.input_freebore.setRange(0, 10)
        self.input_freebore.setValue(0)
        self.input_freebore.setSuffix(' mm')
        self.input_freebore.setDecimals(2)
        chamber_layout.addRow("Freebore:", self.input_freebore)
        
        self.input_throat_angle = QDoubleSpinBox()
        self.input_throat_angle.setRange(0, 5)
        self.input_throat_angle.setValue(1.5)
        self.input_throat_angle.setSuffix(' °')
        self.input_throat_angle.setDecimals(1)
        chamber_layout.addRow("Throat Angle:", self.input_throat_angle)
        
        self.input_max_coal = QDoubleSpinBox()
        self.input_max_coal.setRange(40, 100)
        self.input_max_coal.setValue(70)
        self.input_max_coal.setSuffix(' mm')
        self.input_max_coal.setDecimals(2)
        chamber_layout.addRow("Max COAL (Magasin):", self.input_max_coal)
        
        chamber_group.setLayout(chamber_layout)
        layout.addWidget(chamber_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_status_tab(self):
        """Create status & condition tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Round Count
        count_group = QGroupBox("🎯 Skuddteller")
        count_layout = QFormLayout()
        
        self.input_round_count = QSpinBox()
        self.input_round_count.setRange(0, 50000)
        self.input_round_count.setValue(0)
        self.input_round_count.setSuffix(' skudd')
        count_layout.addRow("Totalt Skudd Fyrt:", self.input_round_count)
        
        self.input_accuracy_life = QSpinBox()
        self.input_accuracy_life.setRange(500, 10000)
        self.input_accuracy_life.setValue(2000)
        self.input_accuracy_life.setSuffix(' skudd')
        count_layout.addRow("Estimert Pipe-Liv:", self.input_accuracy_life)
        
        count_group.setLayout(count_layout)
        layout.addWidget(count_group)
        
        # Condition
        cond_group = QGroupBox("📊 Tilstand")
        cond_layout = QFormLayout()
        
        self.input_bore_condition = QComboBox()
        self.input_bore_condition.addItems(['excellent', 'good', 'fair', 'worn'])
        cond_layout.addRow("Bore Condition:", self.input_bore_condition)
        
        self.input_throat_erosion = QDoubleSpinBox()
        self.input_throat_erosion.setRange(0, 5)
        self.input_throat_erosion.setValue(0)
        self.input_throat_erosion.setSuffix(' mm')
        self.input_throat_erosion.setDecimals(2)
        cond_layout.addRow("Throat Erosion:", self.input_throat_erosion)
        
        self.input_accuracy_baseline = QDoubleSpinBox()
        self.input_accuracy_baseline.setRange(0.1, 5)
        self.input_accuracy_baseline.setValue(1.0)
        self.input_accuracy_baseline.setSuffix(' MOA')
        self.input_accuracy_baseline.setDecimals(2)
        cond_layout.addRow("Baseline Accuracy:", self.input_accuracy_baseline)
        
        cond_group.setLayout(cond_layout)
        layout.addWidget(cond_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def on_profile_selected(self, index):
        """When barrel profile is selected, populate fields"""
        profile_id = self.input_barrel_profile.currentData()
        if profile_id is None:
            return
        
        profile = self.db.get_by_id('barrel_profiles', profile_id)
        if profile:
            self.input_muzzle_diameter.setValue(profile.get('muzzle_diameter_inches', 0.75))
            self.input_breech_diameter.setValue(profile.get('breech_diameter_inches', 1.2))
            
            # Set contour based on profile name
            contour = profile.get('name', '').lower()
            if 'sporter' in contour:
                self.input_barrel_contour.setCurrentText('medium')
            elif 'varmint' in contour:
                self.input_barrel_contour.setCurrentText('varmint')
            elif 'bull' in contour:
                self.input_barrel_contour.setCurrentText('bull')
            elif 'palma' in contour:
                self.input_barrel_contour.setCurrentText('palma')
    
    def load_rifle_data(self):
        """Load existing rifle data"""
        rifle = self.db.get_by_id('rifles', self.rifle_id)
        if not rifle:
            return
        
        # Basic tab
        self.input_name.setText(rifle.get('name', ''))
        self.input_manufacturer.setText(rifle.get('manufacturer', ''))
        self.input_model.setText(rifle.get('model', ''))
        self.input_caliber.setCurrentText(rifle.get('caliber', ''))
        self.input_action.setCurrentText(rifle.get('action_type', 'bolt'))
        self.input_serial.setText(rifle.get('serial_number', ''))
        
        if rifle.get('purchase_date'):
            date = QDate.fromString(rifle['purchase_date'], 'yyyy-MM-dd')
            self.input_purchase_date.setDate(date)
        
        self.input_notes.setPlainText(rifle.get('notes', ''))
        
        # Barrel tab
        if rifle.get('barrel_profile_id'):
            for i in range(self.input_barrel_profile.count()):
                if self.input_barrel_profile.itemData(i) == rifle['barrel_profile_id']:
                    self.input_barrel_profile.setCurrentIndex(i)
                    break
        
        self.input_barrel_contour.setCurrentText(rifle.get('barrel_contour', 'medium'))
        self.input_barrel_length.setValue(rifle.get('barrel_length_inches', 24.0))
        self.input_muzzle_diameter.setValue(rifle.get('muzzle_diameter_mm', 19.05) / 25.4)
        self.input_breech_diameter.setValue(rifle.get('breech_diameter_mm', 30.48) / 25.4)
        self.input_barrel_material.setCurrentText(rifle.get('barrel_material', 'stainless'))
        self.input_barrel_finish.setCurrentText(rifle.get('barrel_finish', 'stainless'))
        self.input_barrel_manufacturer.setText(rifle.get('barrel_manufacturer', ''))
        
        # Chamber tab
        self.input_twist_rate.setCurrentText(rifle.get('twist_rate', '1:8'))
        self.input_twist_direction.setCurrentText(rifle.get('twist_direction', 'right'))
        self.input_rifling_type.setCurrentText(rifle.get('rifling_type', 'conventional'))
        self.input_chamber_spec.setCurrentText(rifle.get('chamber_spec', 'SAAMI'))
        self.input_freebore.setValue(rifle.get('freebore_mm', 0))
        self.input_throat_angle.setValue(rifle.get('throat_angle_deg', 1.5))
        self.input_max_coal.setValue(rifle.get('max_coal_magazine_mm', 70))
        
        # Status tab
        self.input_round_count.setValue(rifle.get('round_count', 0) or 0)
        self.input_accuracy_life.setValue(rifle.get('accuracy_life_estimate', 2000) or 2000)
        self.input_bore_condition.setCurrentText(rifle.get('bore_condition', 'excellent'))
        self.input_throat_erosion.setValue(rifle.get('throat_erosion_mm', 0) or 0)
        self.input_accuracy_baseline.setValue(rifle.get('accuracy_baseline_moa', 1.0) or 1.0)
    
    def save_rifle(self):
        """Save rifle to database"""
        data = {
            'name': self.input_name.text(),
            'manufacturer': self.input_manufacturer.text(),
            'model': self.input_model.text(),
            'caliber': self.input_caliber.currentText(),
            'action_type': self.input_action.currentText(),
            'serial_number': self.input_serial.text(),
            'purchase_date': self.input_purchase_date.date().toString('yyyy-MM-dd'),
            'notes': self.input_notes.toPlainText(),
            
            # Barrel
            'barrel_profile_id': self.input_barrel_profile.currentData(),
            'barrel_contour': self.input_barrel_contour.currentText(),
            'barrel_length_inches': self.input_barrel_length.value(),
            'barrel_length_mm': self.input_barrel_length.value() * 25.4,
            'muzzle_diameter_mm': self.input_muzzle_diameter.value() * 25.4,
            'breech_diameter_mm': self.input_breech_diameter.value() * 25.4,
            'barrel_material': self.input_barrel_material.currentText(),
            'barrel_finish': self.input_barrel_finish.currentText(),
            'barrel_manufacturer': self.input_barrel_manufacturer.text(),
            
            # Chamber & Twist
            'twist_rate': self.input_twist_rate.currentText(),
            'twist_direction': self.input_twist_direction.currentText(),
            'rifling_type': self.input_rifling_type.currentText(),
            'chamber_spec': self.input_chamber_spec.currentText(),
            'freebore_mm': self.input_freebore.value(),
            'throat_angle_deg': self.input_throat_angle.value(),
            'max_coal_magazine_mm': self.input_max_coal.value(),
            
            # Status
            'round_count': self.input_round_count.value(),
            'accuracy_life_estimate': self.input_accuracy_life.value(),
            'bore_condition': self.input_bore_condition.currentText(),
            'throat_erosion_mm': self.input_throat_erosion.value(),
            'accuracy_baseline_moa': self.input_accuracy_baseline.value(),
            
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Validation
        if not data['name']:
            QMessageBox.warning(self, "Mangler Navn", "Vennligst legg inn et navn.")
            return
        
        if not data['caliber']:
            QMessageBox.warning(self, "Mangler Kaliber", "Vennligst velg kaliber.")
            return
        
        try:
            if self.rifle_id:
                self.db.update('rifles', data, 'id = ?', (self.rifle_id,))
                QMessageBox.information(self, "Lagret", f"Rifle '{data['name']}' oppdatert!")
            else:
                data['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.db.insert('rifles', data)
                QMessageBox.information(self, "Lagret", f"Rifle '{data['name']}' lagret!")
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Kunne ikke lagre: {str(e)}")


class RifleDetailsDialog(QDialog):
    """
    View comprehensive rifle details
    """
    
    def __init__(self, parent=None, rifle_id: int = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id
        
        self.setWindowTitle("🔍 Rifle Detaljer")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
        self.load_details()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_info_tab(), "ℹ️ Info")
        self.tabs.addTab(self.create_harmonics_tab(), "🌊 Harmonikk")
        self.tabs.addTab(self.create_bullet_jump_tab(), "📏 Bullet Jump")
        self.tabs.addTab(self.create_accuracy_tests_tab(), "📊 Accuracy Tests")
        self.tabs.addTab(self.create_maintenance_tab(), "🔧 Vedlikehold")
        
        layout.addWidget(self.tabs)
        
        btn_close = QPushButton("✓ Lukk")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
    
    def create_info_tab(self):
        """Create info display tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        layout.addWidget(self.info_display)
        
        widget.setLayout(layout)
        return widget
    
    def create_harmonics_tab(self):
        """Create harmonics analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("🌊 Harmonisk Analyse")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        self.harmonics_display = QTextEdit()
        self.harmonics_display.setReadOnly(True)
        layout.addWidget(self.harmonics_display)
        
        widget.setLayout(layout)
        return widget
    
    def create_bullet_jump_tab(self):
        """Create bullet jump measurements tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("📏 Bullet Jump Målinger")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        self.bullet_jump_table = QTableWidget()
        self.bullet_jump_table.setColumnCount(6)
        self.bullet_jump_table.setHorizontalHeaderLabels([
            "Dato", "Kule", "Jam COAL", "Jam CBTO", "Metode", "Skudd ved Måling"
        ])
        layout.addWidget(self.bullet_jump_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_accuracy_tests_tab(self):
        """Create accuracy tests tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("📊 Accuracy Tests")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        self.accuracy_table = QTableWidget()
        self.accuracy_table.setColumnCount(6)
        self.accuracy_table.setHorizontalHeaderLabels([
            "Dato", "Skudd ved Test", "Avg MOA", "ES fps", "SD fps", "Grupper"
        ])
        layout.addWidget(self.accuracy_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_maintenance_tab(self):
        """Create maintenance log tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("🔧 Vedlikeholdslogg")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        self.maintenance_table = QTableWidget()
        self.maintenance_table.setColumnCount(5)
        self.maintenance_table.setHorizontalHeaderLabels([
            "Dato", "Type", "Skudd", "Bore Condition", "Notater"
        ])
        layout.addWidget(self.maintenance_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_details(self):
        """Load rifle details"""
        rifle = self.db.get_by_id('rifles', self.rifle_id)
        if not rifle:
            return
        
        # Info tab
        info_html = f"""
        <h2>🎯 {rifle.get('name', 'N/A')}</h2>
        <h3>Grunnleggende Info</h3>
        <ul>
            <li><b>Produsent:</b> {rifle.get('manufacturer', '-')}</li>
            <li><b>Modell:</b> {rifle.get('model', '-')}</li>
            <li><b>Kaliber:</b> {rifle.get('caliber', '-')}</li>
            <li><b>Action:</b> {rifle.get('action_type', '-')}</li>
            <li><b>Serienummer:</b> {rifle.get('serial_number', '-')}</li>
        </ul>
        
        <h3>Pipe Detaljer</h3>
        <ul>
            <li><b>Lengde:</b> {rifle.get('barrel_length_inches', 0):.1f}" / {rifle.get('barrel_length_mm', 0):.1f} mm</li>
            <li><b>Kontur:</b> {rifle.get('barrel_contour', '-')}</li>
            <li><b>Material:</b> {rifle.get('barrel_material', '-')}</li>
            <li><b>Finish:</b> {rifle.get('barrel_finish', '-')}</li>
            <li><b>Twist Rate:</b> {rifle.get('twist_rate', '-')} ({rifle.get('twist_direction', 'right')})</li>
            <li><b>Rifling:</b> {rifle.get('rifling_type', '-')}</li>
        </ul>
        
        <h3>Status</h3>
        <ul>
            <li><b>Skudd Fyrt:</b> {rifle.get('round_count', 0)} / {rifle.get('accuracy_life_estimate', 0)} estimert</li>
            <li><b>Bore Condition:</b> {rifle.get('bore_condition', '-')}</li>
            <li><b>Throat Erosion:</b> {rifle.get('throat_erosion_mm', 0):.2f} mm</li>
            <li><b>Baseline Accuracy:</b> {rifle.get('accuracy_baseline_moa', 0):.2f} MOA</li>
        </ul>
        """
        
        self.info_display.setHtml(info_html)
        
        # Harmonics tab
        barrel_length_mm = rifle.get('barrel_length_mm', 600)
        muzzle_dia = rifle.get('muzzle_diameter_mm', 19.05)
        breech_dia = rifle.get('breech_diameter_mm', 30.48)
        
        # Simple harmonic calculation (simplified)
        harmonics_html = f"""
        <h3>Harmonisk Data</h3>
        <p><b>Pipe Lengde:</b> {barrel_length_mm:.1f} mm</p>
        <p><b>Muzzle Diameter:</b> {muzzle_dia:.2f} mm</p>
        <p><b>Breech Diameter:</b> {breech_dia:.2f} mm</p>
        <p><b>Stivhetsrating:</b> {'Tung' if breech_dia > 30 else 'Medium' if breech_dia > 25 else 'Lett'}</p>
        
        <h4>📊 Harmonisk Analyse</h4>
        <p>En tyngre pipe (større diameter) vil ha lavere harmonisk frekvens og være mer stabil.</p>
        <p>Pipeharmonikk påvirker hvor kulen forlater pipen i vibrasjonssyklusen.</p>
        <p><i>Detaljert harmonisk beregning kommer i neste versjon...</i></p>
        """
        
        self.harmonics_display.setHtml(harmonics_html)
        
        # Bullet Jump tab
        jump_measurements = self.db.execute_query(
            "SELECT * FROM rifle_bullet_jump_measurements WHERE rifle_id = ? ORDER BY measurement_date DESC",
            (self.rifle_id,)
        )
        
        self.bullet_jump_table.setRowCount(len(jump_measurements))
        for row, meas in enumerate(jump_measurements):
            self.bullet_jump_table.setItem(row, 0, QTableWidgetItem(meas.get('measurement_date', '-')))
            
            # Get bullet name
            bullet = self.db.get_by_id('bullets', meas.get('bullet_id'))
            bullet_name = f"{bullet['name']}" if bullet else f"ID: {meas.get('bullet_id')}"
            self.bullet_jump_table.setItem(row, 1, QTableWidgetItem(bullet_name))
            
            self.bullet_jump_table.setItem(row, 2, QTableWidgetItem(f"{meas.get('jam_coal_mm', 0):.2f} mm"))
            self.bullet_jump_table.setItem(row, 3, QTableWidgetItem(f"{meas.get('jam_cbto_mm', 0):.2f} mm"))
            self.bullet_jump_table.setItem(row, 4, QTableWidgetItem(meas.get('measurement_method', '-')))
            self.bullet_jump_table.setItem(row, 5, QTableWidgetItem(str(meas.get('rounds_fired_at_measurement', 0))))
        
        # Accuracy Tests tab
        accuracy_tests = self.db.execute_query(
            "SELECT * FROM rifle_accuracy_tests WHERE rifle_id = ? ORDER BY test_date DESC LIMIT 10",
            (self.rifle_id,)
        )
        
        self.accuracy_table.setRowCount(len(accuracy_tests))
        for row, test in enumerate(accuracy_tests):
            self.accuracy_table.setItem(row, 0, QTableWidgetItem(test.get('test_date', '-')))
            self.accuracy_table.setItem(row, 1, QTableWidgetItem(str(test.get('round_count_at_test', 0))))
            
            avg_moa = test.get('average_moa', 0)
            moa_item = QTableWidgetItem(f"{avg_moa:.3f}" if avg_moa else "-")
            if avg_moa:
                if avg_moa < 0.5:
                    moa_item.setForeground(QColor('#27ae60'))
                elif avg_moa < 1.0:
                    moa_item.setForeground(QColor('#3498db'))
                elif avg_moa < 1.5:
                    moa_item.setForeground(QColor('#f39c12'))
            self.accuracy_table.setItem(row, 2, moa_item)
            
            self.accuracy_table.setItem(row, 3, QTableWidgetItem(str(test.get('extreme_spread_fps', 0) or '-')))
            self.accuracy_table.setItem(row, 4, QTableWidgetItem(f"{test.get('standard_deviation_fps', 0):.1f}" if test.get('standard_deviation_fps') else '-'))
            self.accuracy_table.setItem(row, 5, QTableWidgetItem(str(test.get('groups_fired', 0))))
        
        # Maintenance tab
        maintenance_logs = self.db.execute_query(
            "SELECT * FROM rifle_maintenance_log WHERE rifle_id = ? ORDER BY maintenance_date DESC LIMIT 20",
            (self.rifle_id,)
        )
        
        self.maintenance_table.setRowCount(len(maintenance_logs))
        for row, log in enumerate(maintenance_logs):
            self.maintenance_table.setItem(row, 0, QTableWidgetItem(log.get('maintenance_date', '-')))
            self.maintenance_table.setItem(row, 1, QTableWidgetItem(log.get('maintenance_type', '-')))
            self.maintenance_table.setItem(row, 2, QTableWidgetItem(str(log.get('rounds_fired_before', 0))))
            self.maintenance_table.setItem(row, 3, QTableWidgetItem(log.get('throat_condition', '-')))
            self.maintenance_table.setItem(row, 4, QTableWidgetItem(log.get('notes', '-')[:50]))


class AddRoundsFiredDialog(QDialog):
    """Dialog for adding rounds fired"""
    
    def __init__(self, parent=None, rifle: Dict = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle = rifle
        
        self.setWindowTitle(f"🎯 Legg til Skudd - {rifle.get('name', '')}")
        self.setMinimumWidth(400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        current_count = self.rifle.get('round_count', 0) or 0
        label = QLabel(f"Nåværende skuddteller: <b>{current_count}</b>")
        layout.addWidget(label)
        
        self.input_rounds = QSpinBox()
        self.input_rounds.setRange(1, 1000)
        self.input_rounds.setValue(20)
        self.input_rounds.setSuffix(' skudd')
        form.addRow("Legg til skudd:", self.input_rounds)
        
        self.input_notes = QTextEdit()
        self.input_notes.setMaximumHeight(80)
        self.input_notes.setPlaceholderText("Notater om økten...")
        form.addRow("Notater:", self.input_notes)
        
        layout.addLayout(form)
        
        # Warning check
        accuracy_life = self.rifle.get('accuracy_life_estimate', 2000)
        new_count = current_count + self.input_rounds.value()
        
        if new_count >= 500 and (new_count // 500) > (current_count // 500):
            warning = QLabel("⚠️ Du passerer 500 skudd! Husk å måle hylser for slitasje.")
            warning.setStyleSheet("background-color: #fff3cd; padding: 10px; border-radius: 5px; color: #856404;")
            warning.setWordWrap(True)
            layout.addWidget(warning)
        
        if new_count > accuracy_life * 0.8:
            warning2 = QLabel(f"⚠️ Pipen nærmer seg estimert levetid ({accuracy_life} skudd)!")
            warning2.setStyleSheet("background-color: #f8d7da; padding: 10px; border-radius: 5px; color: #721c24;")
            warning2.setWordWrap(True)
            layout.addWidget(warning2)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Lagre")
        btn_save.clicked.connect(self.save_rounds)
        btn_save.setStyleSheet("background-color: #27ae60; color: white; padding: 8px;")
        
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def save_rounds(self):
        """Save rounds fired"""
        rounds_to_add = self.input_rounds.value()
        current_count = self.rifle.get('round_count', 0) or 0
        new_count = current_count + rounds_to_add
        
        # Update rifle
        self.db.update('rifles', {'round_count': new_count}, 'id = ?', (self.rifle['id'],))
        
        # Log maintenance entry
        log_data = {
            'rifle_id': self.rifle['id'],
            'maintenance_date': datetime.now().strftime('%Y-%m-%d'),
            'maintenance_type': 'shooting_session',
            'rounds_fired_before': current_count,
            'rounds_fired_after': new_count,
            'notes': self.input_notes.toPlainText()
        }
        self.db.insert('rifle_maintenance_log', log_data)
        
        QMessageBox.information(
            self, 
            "Lagret", 
            f"Skuddteller oppdatert: {current_count} → {new_count}"
        )
        
        self.accept()


class MaintenanceLogDialog(QDialog):
    """Dialog for logging maintenance"""
    
    def __init__(self, parent=None, rifle: Dict = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle = rifle
        
        self.setWindowTitle(f"🔧 Vedlikehold - {rifle.get('name', '')}")
        self.setMinimumWidth(500)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.input_date = QDateEdit()
        self.input_date.setDate(QDate.currentDate())
        self.input_date.setCalendarPopup(True)
        form.addRow("Dato:", self.input_date)
        
        self.input_type = QComboBox()
        self.input_type.addItems([
            'cleaning', 'deep_clean', 'inspection', 
            'repair', 'accuracy_test', 'barrel_break_in'
        ])
        form.addRow("Type:", self.input_type)
        
        self.input_bore_cleaned = QCheckBox()
        form.addRow("Løp rengjort:", self.input_bore_cleaned)
        
        self.input_carbon_removed = QCheckBox()
        form.addRow("Carbon fjernet:", self.input_carbon_removed)
        
        self.input_copper_removed = QCheckBox()
        form.addRow("Copper fjernet:", self.input_copper_removed)
        
        self.input_bore_condition = QComboBox()
        self.input_bore_condition.addItems(['excellent', 'good', 'fair', 'worn'])
        self.input_bore_condition.setCurrentText(self.rifle.get('bore_condition', 'good'))
        form.addRow("Bore Condition:", self.input_bore_condition)
        
        self.input_accuracy = QDoubleSpinBox()
        self.input_accuracy.setRange(0.1, 10)
        self.input_accuracy.setValue(1.0)
        self.input_accuracy.setSuffix(' MOA')
        self.input_accuracy.setDecimals(2)
        form.addRow("Accuracy Test:", self.input_accuracy)
        
        self.input_notes = QTextEdit()
        self.input_notes.setMaximumHeight(100)
        form.addRow("Notater:", self.input_notes)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Lagre")
        btn_save.clicked.connect(self.save_maintenance)
        btn_save.setStyleSheet("background-color: #27ae60; color: white; padding: 8px;")
        
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def save_maintenance(self):
        """Save maintenance log"""
        log_data = {
            'rifle_id': self.rifle['id'],
            'maintenance_date': self.input_date.date().toString('yyyy-MM-dd'),
            'maintenance_type': self.input_type.currentText(),
            'rounds_fired_before': self.rifle.get('round_count', 0),
            'bore_cleaned': 1 if self.input_bore_cleaned.isChecked() else 0,
            'carbon_removed': 1 if self.input_carbon_removed.isChecked() else 0,
            'copper_removed': 1 if self.input_copper_removed.isChecked() else 0,
            'bore_condition_rating': ['worn', 'fair', 'good', 'excellent'].index(self.input_bore_condition.currentText()) + 1,
            'throat_condition': self.input_bore_condition.currentText(),
            'accuracy_test_performed': 1,
            'accuracy_result_moa': self.input_accuracy.value(),
            'notes': self.input_notes.toPlainText()
        }
        
        self.db.insert('rifle_maintenance_log', log_data)
        
        # Update rifle
        update_data = {
            'last_maintenance_date': log_data['maintenance_date'],
            'bore_condition': self.input_bore_condition.currentText(),
            'current_accuracy_moa': self.input_accuracy.value()
        }
        
        if self.input_bore_cleaned.isChecked():
            update_data['last_cleaning_date'] = log_data['maintenance_date']
            update_data['last_cleaned_round_count'] = self.rifle.get('round_count', 0)
        
        self.db.update('rifles', update_data, 'id = ?', (self.rifle['id'],))
        
        QMessageBox.information(self, "Lagret", "Vedlikehold logget!")
        
        self.accept()
