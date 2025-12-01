
"""
Calibration & Ballistics Validation Workflow
Integrates rifle profile, ballistics, calibration test, zero standardization, and logging.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFormLayout,
                            QTextEdit, QSpinBox, QFileDialog, QGroupBox, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from src.modules.rifle_profile_editor import RifleProfileEditor
from src.modules.zero_shift_calculator import ZeroShiftCalculator
from src.modules.comprehensive_logger import ComprehensiveDataLogger
from src.modules.rifle_accuracy_test_system import RifleAccuracyTestManager

class CalibrationValidationDialog(QDialog):
    """
    Dialog for integrated calibration and ballistics validation workflow.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kalibrerings- og Ballistikkvalidering")
        self.setMinimumSize(900, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("🔬 Kalibrerings- og Ballistikkvalidering")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        # Rifle Profile Section
        rifle_group = QGroupBox("Rifleprofil")
        rifle_layout = QVBoxLayout()
        rifle_group.setLayout(rifle_layout)
        self.rifle_profile_btn = QPushButton("Velg/Rediger Rifleprofil")
        self.rifle_profile_btn.clicked.connect(self.open_rifle_profile)
        rifle_layout.addWidget(self.rifle_profile_btn)
        layout.addWidget(rifle_group)

        # Zero Standardization Section
        zero_group = QGroupBox("Standardiser Innskytingsavstand (Zero)")
        zero_layout = QVBoxLayout()
        zero_group.setLayout(zero_layout)
        self.zero_calc_btn = QPushButton("Zero Shift Kalkulator")
        self.zero_calc_btn.clicked.connect(self.open_zero_calculator)
        zero_layout.addWidget(self.zero_calc_btn)
        layout.addWidget(zero_group)

        # Calibration Test Section
        test_group = QGroupBox("Kalibrerings-skyte Test")
        test_layout = QVBoxLayout()
        test_group.setLayout(test_layout)
        self.test_manager_btn = QPushButton("Logg/Test Accuracy")
        self.test_manager_btn.clicked.connect(self.open_accuracy_test)
        test_layout.addWidget(self.test_manager_btn)
        layout.addWidget(test_group)

        # Data Logging Section
        log_group = QGroupBox("Logg Testdata, Avvik, Bilder og Distanse")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        self.logger_btn = QPushButton("Åpne Data Logger")
        self.logger_btn.clicked.connect(self.open_data_logger)
        log_layout.addWidget(self.logger_btn)
        layout.addWidget(log_group)

        # Notes
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Notater, observasjoner, avvik...")
        layout.addWidget(self.notes)

        # Save Button
        self.save_btn = QPushButton("Lagre Kalibreringsdata")
        self.save_btn.clicked.connect(self.save_data)
        layout.addWidget(self.save_btn)

    def open_rifle_profile(self):
        dlg = RifleProfileEditor(self)
        dlg.exec()

    def open_zero_calculator(self):
        dlg = ZeroShiftCalculator()
        dlg.exec()

    def open_accuracy_test(self):
        dlg = RifleAccuracyTestManager(self)
        dlg.exec()

    def open_data_logger(self):
        dlg = ComprehensiveDataLogger()
        dlg.exec()

    def save_data(self):
        # Placeholder for saving calibration/validation data
        QMessageBox.information(self, "Lagring", "Kalibreringsdata lagret!")
