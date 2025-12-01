"""
Load Development Wizard - Professional Load Development Interface
Wizard-style workflow: Select rifle → Brass → Bullet → Powder → AI Prediction → Test Protocol
Integrates with advanced batch management system
"""

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QSpinBox, QDoubleSpinBox, QTextEdit,
    QGroupBox, QFormLayout, QRadioButton, QButtonGroup, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QDateEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import json

from src.database.database import get_database


class LoadDevelopmentWizard(QWizard):
    """Professional Load Development Wizard - QuickLOAD/GRT style with AI"""
    
    batch_created = pyqtSignal(list)  # Emit list of created batch IDs
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        
        self.setWindowTitle("🎯 Load Development Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setFixedSize(1100, 750)
        
        # Wizard Data Storage
        self.rifle_data = {}
        self.brass_data = {}
        self.bullet_data = {}
        self.powder_data = {}
        self.primer_data = {}
        self.load_params = {}
        self.prediction_data = {}
        self.test_protocol = {}
        self.created_batches = []
        
        # Add pages
        self.page_intro = IntroPage(self)
        self.page_rifle = RifleSelectionPage(self)
        self.page_brass = BrassSelectionPage(self)
        self.page_bullet = BulletSelectionPage(self)
        self.page_powder_primer = PowderPrimerPage(self)
        self.page_load_data = LoadDataPage(self)
        self.page_prediction = AIPredictionPage(self)
        self.page_protocol = TestProtocolPage(self)
        self.page_batch = BatchCreationPage(self)
        
        self.addPage(self.page_intro)
        self.addPage(self.page_rifle)
        self.addPage(self.page_brass)
        self.addPage(self.page_bullet)
        self.addPage(self.page_powder_primer)
        self.addPage(self.page_load_data)
        self.addPage(self.page_prediction)
        self.addPage(self.page_protocol)
        self.addPage(self.page_batch)
        
        # Styling
        self.setStyleSheet("""
            QWizard {
                background: #f5f5f5;
            }
            QLabel {
                font-size: 11pt;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                padding: 8px 15px;
                font-size: 11pt;
            }
        """)
        
        # Connect finish button
        self.finished.connect(self.on_wizard_finished)
    
    def on_wizard_finished(self, result):
        """Emit signal when wizard completes"""
        if result == QWizard.DialogCode.Accepted and self.created_batches:
            self.batch_created.emit(self.created_batches)


class IntroPage(QWizardPage):
    """Introduction page with workflow explanation"""
    
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        
        self.setTitle("🎯 Professional Load Development")
        self.setSubTitle("AI-Assisted Load Development - Minimize Testing, Maximize Results")
        
        layout = QVBoxLayout()
        
        # Welcome text
        intro_text = QTextEdit()
        intro_text.setReadOnly(True)
        intro_text.setHtml("""
        <h2 style='color: #2c3e50;'>Welcome to the Load Development Wizard!</h2>
        
        <p style='font-size: 12pt;'>This wizard will guide you through creating an optimal load 
        for your rifle using AI-powered predictions and minimal ammunition waste.</p>
        
        <h3 style='color: #3498db;'>How It Works:</h3>
        <ol style='font-size: 11pt; line-height: 1.8;'>
            <li><b>Select Your Rifle</b> - Choose rifle and auto-load specifications</li>
            <li><b>Select Brass Batch</b> - Choose brass from inventory or create new batch</li>
            <li><b>Select Bullet</b> - Choose bullet with QC data from your lots</li>
            <li><b>Select Powder & Primer</b> - Choose components from inventory</li>
            <li><b>Enter Load Parameters</b> - COAL, charge weight range, seating depth</li>
            <li><b>AI Prediction</b> - Get optimal charge prediction from your historical data</li>
            <li><b>Test Protocol</b> - Bayesian optimization for minimal test rounds (15-20 rounds vs 60+)</li>
            <li><b>Create Batches</b> - Auto-generate batch numbers with full traceability</li>
        </ol>
        
        <h3 style='color: #e74c3c;'>What You'll Get:</h3>
        <ul style='font-size: 11pt; line-height: 1.8;'>
            <li>✅ <b>AI-Predicted Optimal Load</b> - Before firing a single round!</li>
            <li>✅ <b>Minimal Test Protocol</b> - Only 5-7 test charges (15-21 rounds)</li>
            <li>✅ <b>Full Batch Traceability</b> - Track every component lot number</li>
            <li>✅ <b>Sizing Guidance</b> - Calculate shoulder bump and neck tension from rifle data</li>
            <li>✅ <b>QC Standards</b> - Professional quality control per round</li>
            <li>✅ <b>Safety Analysis</b> - Pressure predictions and SAAMI compliance</li>
        </ul>
        
        <p style='font-size: 11pt; color: #27ae60; font-weight: bold;'>
        🎯 This system learns from YOUR rifle and YOUR results - it gets smarter every time you test!
        </p>
        """)
        intro_text.setMinimumHeight(500)
        layout.addWidget(intro_text)
        
        self.setLayout(layout)


class RifleSelectionPage(QWizardPage):
    """Page 1: Select Rifle"""
    
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        
        self.setTitle("Step 1: Select Rifle")
        self.setSubTitle("Choose the rifle you're developing a load for")
        
        layout = QVBoxLayout()
        
        # Rifle Selection
        rifle_group = QGroupBox("🔫 Rifle Selection")
        rifle_layout = QFormLayout()
        
        self.rifle_combo = QComboBox()
        self.load_rifles()
        self.rifle_combo.currentIndexChanged.connect(self.on_rifle_changed)
        rifle_layout.addRow("Select Rifle:", self.rifle_combo)
        
        rifle_group.setLayout(rifle_layout)
        layout.addWidget(rifle_group)
        
        # Rifle Info Display
        info_group = QGroupBox("📊 Rifle Specifications")
        self.info_layout = QFormLayout()
        
        self.caliber_label = QLabel("-")
        self.barrel_length_label = QLabel("-")
        self.twist_rate_label = QLabel("-")
        self.chamber_spec_label = QLabel("-")
        self.freebore_label = QLabel("-")
        self.round_count_label = QLabel("-")
        self.max_coal_label = QLabel("-")
        
        self.info_layout.addRow("Caliber:", self.caliber_label)
        self.info_layout.addRow("Barrel Length:", self.barrel_length_label)
        self.info_layout.addRow("Twist Rate:", self.twist_rate_label)
        self.info_layout.addRow("Chamber Spec:", self.chamber_spec_label)
        self.info_layout.addRow("Freebore:", self.freebore_label)
        self.info_layout.addRow("Round Count:", self.round_count_label)
        self.info_layout.addRow("Max COAL (Magazine):", self.max_coal_label)
        
        info_group.setLayout(self.info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_rifles(self):
        """Load rifles from database"""
        rifles = self.wizard.db.get_all('rifles', 'name')
        self.rifle_combo.addItem("-- Select Rifle --", None)
        for rifle in rifles:
            self.rifle_combo.addItem(f"{rifle['name']} ({rifle['caliber']})", rifle['id'])
    
    def on_rifle_changed(self, index):
        """Update rifle info when selection changes"""
        rifle_id = self.rifle_combo.currentData()
        if rifle_id is None:
            return
        
        rifle = self.wizard.db.get_by_id('rifles', rifle_id)
        if rifle:
            self.wizard.rifle_data = rifle
            
            # Update labels
            self.caliber_label.setText(rifle.get('caliber', '-'))
            
            barrel_length = rifle.get('barrel_length_inches', 0) or (rifle.get('barrel_length_mm', 0) / 25.4 if rifle.get('barrel_length_mm') else 0)
            self.barrel_length_label.setText(f"{barrel_length:.1f}\"" if barrel_length else "-")
            
            self.twist_rate_label.setText(rifle.get('twist_rate', '-'))
            self.chamber_spec_label.setText(rifle.get('chamber_spec', 'SAAMI'))
            
            freebore = rifle.get('freebore_mm', 0)
            self.freebore_label.setText(f"{freebore:.2f} mm" if freebore else "-")
            
            round_count = rifle.get('round_count', 0)
            self.round_count_label.setText(f"{round_count} rounds")
            
            max_coal = rifle.get('max_coal_magazine_mm', 0)
            self.max_coal_label.setText(f"{max_coal:.2f} mm" if max_coal else "-")
    
    def validatePage(self):
        """Validate rifle selection before proceeding"""
        if self.rifle_combo.currentData() is None:
            QMessageBox.warning(self, "No Rifle Selected", "Please select a rifle to continue.")
            return False
        return True


# Import remaining pages from separate file
from src.modules.load_wizard_pages import (
    BrassSelectionPage,
    BulletSelectionPage,
    PowderPrimerPage,
    LoadDataPage,
    AIPredictionPage,
    TestProtocolPage,
    BatchCreationPage
)


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    wizard = LoadDevelopmentWizard()
    wizard.show()
    sys.exit(app.exec())
