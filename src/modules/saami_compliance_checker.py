"""
SAAMI/CIP Compliance Checker
Verify loads mot industry standards for sikkerhet og compatibility
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QComboBox, QDoubleSpinBox, QTextEdit,
                             QMessageBox, QLineEdit, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from src.database.database import get_database
from typing import Dict, List, Optional, Tuple


class SAAMISpecs:
    """SAAMI/CIP specifications database"""
    
    SPECS = {
        # .308 Winchester
        '.308 Winchester': {
            'standard': 'SAAMI',
            'max_coal': 2.800,
            'min_coal': 2.015,
            'max_pressure_psi': 62000,
            'case_length': 2.015,
            'case_length_trim': 2.005,
            'bullet_diameter': 0.308,
            'neck_diameter_loaded': 0.343,
            'base_diameter': 0.4709
        },
        
        # 6.5 Creedmoor
        '6.5 Creedmoor': {
            'standard': 'SAAMI',
            'max_coal': 2.825,
            'min_coal': 2.710,
            'max_pressure_psi': 62000,
            'case_length': 1.920,
            'case_length_trim': 1.910,
            'bullet_diameter': 0.264,
            'neck_diameter_loaded': 0.295,
            'base_diameter': 0.4703
        },
        
        # .223 Remington
        '.223 Remington': {
            'standard': 'SAAMI',
            'max_coal': 2.260,
            'min_coal': 1.760,
            'max_pressure_psi': 55000,
            'case_length': 1.760,
            'case_length_trim': 1.750,
            'bullet_diameter': 0.224,
            'neck_diameter_loaded': 0.253,
            'base_diameter': 0.3760
        },
        
        # .30-06 Springfield
        '.30-06 Springfield': {
            'standard': 'SAAMI',
            'max_coal': 3.340,
            'min_coal': 2.494,
            'max_pressure_psi': 60000,
            'case_length': 2.494,
            'case_length_trim': 2.484,
            'bullet_diameter': 0.308,
            'neck_diameter_loaded': 0.340,
            'base_diameter': 0.4698
        },
        
        # 6.5x55 Swedish
        '6.5x55 Swedish': {
            'standard': 'CIP',
            'max_coal': 3.150,
            'min_coal': 2.165,
            'max_pressure_bar': 3800,  # CIP uses bar
            'max_pressure_psi': 55114,  # Converted
            'case_length': 2.165,
            'case_length_trim': 2.155,
            'bullet_diameter': 0.264,
            'neck_diameter_loaded': 0.297,
            'base_diameter': 0.4803
        },
        
        # 7.62x51 NATO (similar to .308)
        '7.62x51 NATO': {
            'standard': 'NATO',
            'max_coal': 2.800,
            'min_coal': 2.015,
            'max_pressure_psi': 50000,  # NATO is lower than SAAMI
            'case_length': 2.015,
            'case_length_trim': 2.005,
            'bullet_diameter': 0.308,
            'neck_diameter_loaded': 0.343,
            'base_diameter': 0.4709,
            'note': 'NATO spec er MER konservativ enn SAAMI .308'
        }
    }
    
    @staticmethod
    def get_spec(caliber: str) -> Optional[Dict]:
        """Hent spec for kaliber"""
        return SAAMISpecs.SPECS.get(caliber)
    
    @staticmethod
    def get_all_calibers() -> List[str]:
        """Hent alle støttede kalibere"""
        return list(SAAMISpecs.SPECS.keys())


class SAAMIComplianceChecker(QWidget):
    """
    SAAMI/CIP Compliance Checker
    Verify loads mot industry standards
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.current_spec = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("✅ SAAMI/CIP Compliance Checker")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        desc = QLabel(
            "Verify din ladning mot SAAMI/CIP/NATO standards.\n"
            "Ammofabrikker MUST følge disse specs - du bør også for sikkerhet og compatibility!"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Caliber selection
        caliber_group = QGroupBox("🔍 Velg Kaliber")
        caliber_layout = QHBoxLayout()
        
        caliber_layout.addWidget(QLabel("Kaliber:"))
        self.combo_caliber = QComboBox()
        self.combo_caliber.addItems(SAAMISpecs.get_all_calibers())
        self.combo_caliber.currentTextChanged.connect(self.on_caliber_changed)
        caliber_layout.addWidget(self.combo_caliber)
        
        caliber_layout.addStretch()
        caliber_group.setLayout(caliber_layout)
        layout.addWidget(caliber_group)
        
        # Specification display
        spec_group = QGroupBox("📋 SAAMI/CIP Spesifikasjoner")
        spec_layout = QVBoxLayout()
        
        self.text_spec = QTextEdit()
        self.text_spec.setReadOnly(True)
        self.text_spec.setMaximumHeight(200)
        spec_layout.addWidget(self.text_spec)
        
        spec_group.setLayout(spec_layout)
        layout.addWidget(spec_group)
        
        # Load data input
        load_group = QGroupBox("📊 Din Ladning")
        load_layout = QVBoxLayout()
        
        # COAL
        coal_layout = QHBoxLayout()
        coal_layout.addWidget(QLabel("COAL:"))
        self.spin_coal = QDoubleSpinBox()
        self.spin_coal.setRange(1.0, 4.0)
        self.spin_coal.setDecimals(3)
        self.spin_coal.setSuffix(" \"")
        self.spin_coal.setValue(2.800)
        coal_layout.addWidget(self.spin_coal)
        coal_layout.addStretch()
        load_layout.addLayout(coal_layout)
        
        # Case length
        case_layout = QHBoxLayout()
        case_layout.addWidget(QLabel("Case Length:"))
        self.spin_case_length = QDoubleSpinBox()
        self.spin_case_length.setRange(1.0, 3.0)
        self.spin_case_length.setDecimals(3)
        self.spin_case_length.setSuffix(" \"")
        case_layout.addWidget(self.spin_case_length)
        case_layout.addStretch()
        load_layout.addLayout(case_layout)
        
        # Estimated pressure (optional)
        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(QLabel("Estimated Pressure:"))
        self.spin_pressure = QSpinBox()
        self.spin_pressure.setRange(0, 80000)
        self.spin_pressure.setSuffix(" PSI")
        self.spin_pressure.setSpecialValueText("Unknown")
        pressure_layout.addWidget(self.spin_pressure)
        
        pressure_layout.addWidget(QLabel("(fra GRT/QuickLOAD)"))
        pressure_layout.addStretch()
        load_layout.addLayout(pressure_layout)
        
        # Check button
        self.btn_check = QPushButton("🔍 Sjekk Compliance")
        self.btn_check.clicked.connect(self.check_compliance)
        self.btn_check.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        load_layout.addWidget(self.btn_check)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Results
        results_group = QGroupBox("📈 Compliance Resultater")
        results_layout = QVBoxLayout()
        
        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        results_layout.addWidget(self.text_results)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Initialize
        self.on_caliber_changed(self.combo_caliber.currentText())
        
        self.setLayout(layout)
    
    def on_caliber_changed(self, caliber: str):
        """Når kaliber velges"""
        self.current_spec = SAAMISpecs.get_spec(caliber)
        
        if not self.current_spec:
            return
        
        # Display spec
        html = f"""
        <h3 style='color: #2c3e50;'>{caliber} ({self.current_spec['standard']} Standard)</h3>
        
        <table border='1' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Parameter</th>
                <th>Minimum</th>
                <th>Maximum</th>
                <th>Unit</th>
            </tr>
            <tr>
                <td><b>COAL</b></td>
                <td>{self.current_spec.get('min_coal', 'N/A')}</td>
                <td>{self.current_spec['max_coal']}</td>
                <td>inches</td>
            </tr>
            <tr>
                <td><b>Case Length</b></td>
                <td>{self.current_spec.get('case_length_trim', 'N/A')}</td>
                <td>{self.current_spec['case_length']}</td>
                <td>inches</td>
            </tr>
            <tr>
                <td><b>Max Pressure</b></td>
                <td>-</td>
                <td>{self.current_spec['max_pressure_psi']:,}</td>
                <td>PSI</td>
            </tr>
            <tr>
                <td><b>Bullet Diameter</b></td>
                <td>{self.current_spec['bullet_diameter']}</td>
                <td>{self.current_spec['bullet_diameter']}</td>
                <td>inches</td>
            </tr>
        </table>
        """
        
        if 'note' in self.current_spec:
            html += f"""
            <p style='color: #f39c12; margin-top: 10px;'>
            <b>⚠️ Note:</b> {self.current_spec['note']}
            </p>
            """
        
        self.text_spec.setHtml(html)
        
        # Update default values
        self.spin_coal.setValue(self.current_spec['max_coal'])
        self.spin_case_length.setValue(self.current_spec['case_length'])
    
    def check_compliance(self):
        """Sjekk compliance"""
        if not self.current_spec:
            return
        
        coal = self.spin_coal.value()
        case_length = self.spin_case_length.value()
        pressure = self.spin_pressure.value()
        
        issues = []
        warnings = []
        ok = []
        
        # Check COAL
        if coal > self.current_spec['max_coal']:
            delta = coal - self.current_spec['max_coal']
            issues.append(f"❌ <b>COAL for lang!</b> {coal:.3f}\" > {self.current_spec['max_coal']:.3f}\" (+{delta:.3f}\")")
            issues.append(f"   <i>Risiko: Funker ikke i alle magasiner/kamre. Single-feed only!</i>")
        elif coal < self.current_spec.get('min_coal', 0):
            issues.append(f"❌ <b>COAL for kort!</b> {coal:.3f}\" < {self.current_spec['min_coal']:.3f}\"")
        else:
            ok.append(f"✅ <b>COAL OK:</b> {coal:.3f}\" (innenfor {self.current_spec.get('min_coal', 'N/A')} - {self.current_spec['max_coal']}\")")
        
        # Check case length
        if case_length > self.current_spec['case_length']:
            delta = case_length - self.current_spec['case_length']
            issues.append(f"❌ <b>Case for lang!</b> {case_length:.3f}\" > {self.current_spec['case_length']:.3f}\" (+{delta:.3f}\")")
            issues.append(f"   <i>Risiko: Kan gi høyt trykk (reduced case volume). TRIM NÅ!</i>")
        elif case_length < self.current_spec.get('case_length_trim', 0):
            warnings.append(f"⚠️ <b>Case veldig kort:</b> {case_length:.3f}\" < {self.current_spec['case_length_trim']:.3f}\"")
            warnings.append(f"   <i>OK å bruke, men uvanlig kort. Sjekk måling.</i>")
        else:
            ok.append(f"✅ <b>Case Length OK:</b> {case_length:.3f}\"")
        
        # Check pressure
        if pressure > 0:
            if pressure > self.current_spec['max_pressure_psi']:
                delta = pressure - self.current_spec['max_pressure_psi']
                issues.append(f"❌ <b>Pressure for høyt!</b> {pressure:,} PSI > {self.current_spec['max_pressure_psi']:,} PSI (+{delta:,} PSI)")
                issues.append(f"   <i>Risiko: FARLIG! Reduser ladning UMIDDELBART!</i>")
            elif pressure > self.current_spec['max_pressure_psi'] * 0.95:
                warnings.append(f"⚠️ <b>Pressure høyt:</b> {pressure:,} PSI ({(pressure/self.current_spec['max_pressure_psi']*100):.1f}% av max)")
                warnings.append(f"   <i>Vær obs på trykktegn. Minimal margin.</i>")
            else:
                ok.append(f"✅ <b>Pressure OK:</b> {pressure:,} PSI ({(pressure/self.current_spec['max_pressure_psi']*100):.1f}% av max)")
        
        # Generate report
        html = "<h2 style='color: #2c3e50;'>📊 Compliance Report</h2>"
        
        if issues:
            html += "<h3 style='color: #e74c3c;'>❌ CRITICAL ISSUES:</h3><ul>"
            for issue in issues:
                html += f"<li>{issue}</li>"
            html += "</ul>"
        
        if warnings:
            html += "<h3 style='color: #f39c12;'>⚠️ WARNINGS:</h3><ul>"
            for warning in warnings:
                html += f"<li>{warning}</li>"
            html += "</ul>"
        
        if ok:
            html += "<h3 style='color: #27ae60;'>✅ COMPLIANT:</h3><ul>"
            for item in ok:
                html += f"<li>{item}</li>"
            html += "</ul>"
        
        # Overall verdict
        if issues:
            html += """
            <h3 style='color: #e74c3c;'>🚫 OVERALL: FAIL</h3>
            <p><b>Din ladning følger IKKE {standard} specs!</b></p>
            <p>Risiko: Sikkerhetsproblemer eller compatibility issues.</p>
            <p><b>Anbefaling:</b> Korriger issues før bruk!</p>
            """.format(standard=self.current_spec['standard'])
        elif warnings:
            html += """
            <h3 style='color: #f39c12;'>⚠️ OVERALL: MARGINAL</h3>
            <p><b>Din ladning har noen warnings.</b></p>
            <p>Teknisk compliant, men vær forsiktig.</p>
            """.format(standard=self.current_spec['standard'])
        else:
            html += """
            <h3 style='color: #27ae60;'>✅ OVERALL: PASS</h3>
            <p><b>Din ladning følger {standard} specs! 🎉</b></p>
            <p>Safe å bruke i alle SAAMI-spec rifles/chambers.</p>
            <p>Ammofabrikk-grade compliance!</p>
            """.format(standard=self.current_spec['standard'])
        
        # Cross-rifle compatibility
        html += """
        <h3>🔄 Cross-Rifle Compatibility:</h3>
        <ul>
        """
        
        if coal <= self.current_spec['max_coal']:
            html += f"<li>✅ Fungerer i standard magasiner</li>"
        else:
            html += f"<li>❌ Single-feed only (for lang for magasin)</li>"
        
        if case_length <= self.current_spec['case_length']:
            html += f"<li>✅ Fungerer i alle SAAMI-kamre</li>"
        else:
            html += f"<li>❌ Kan ikke chambres (case for lang)</li>"
        
        if not pressure or pressure <= self.current_spec['max_pressure_psi']:
            html += f"<li>✅ Safe i alle rifles (pressure OK)</li>"
        else:
            html += f"<li>❌ FARLIG (over-pressure)</li>"
        
        html += "</ul>"
        
        self.text_results.setHtml(html)
        
        # Show dialog
        if issues:
            QMessageBox.critical(
                self,
                "Compliance FAIL",
                "❌ Din ladning har CRITICAL ISSUES!\n\nSe detaljer for å fikse."
            )
        elif warnings:
            QMessageBox.warning(
                self,
                "Compliance MARGINAL",
                "⚠️ Din ladning har warnings.\n\nSe detaljer for mer info."
            )
        else:
            QMessageBox.information(
                self,
                "Compliance PASS",
                "✅ Din ladning følger SAAMI/CIP specs!\n\nAmmofabrikk-grade compliance! 🎉"
            )


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = SAAMIComplianceChecker()
    window.show()
    sys.exit(app.exec())
