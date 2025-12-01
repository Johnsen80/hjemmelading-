"""
Master Load Development Wizard
Complete step-by-step workflow for developing a new load

Steps:
1. Select Rifle & Barrel
2. Select Caliber
3. Select Components (Bullet, Powder, Primer, Brass)
4. Component Prep & Measurements
5. Load Specs (Charge weight, Seating depth, COAL/CBTO)
6. Test Plan (OCW, Ladder, Seating depth test)
7. AI Recommendations
"""

from PyQt6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton,
                             QFormLayout, QGroupBox, QDoubleSpinBox, QSpinBox,
                             QTextEdit, QCheckBox, QTableWidget, QTableWidgetItem,
                             QRadioButton, QButtonGroup, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
from pathlib import Path
from typing import Dict, List, Optional


class LoadDevelopmentWizard(QWizard):
    """
    Complete load development wizard
    Guides user through entire process from rifle selection to AI recommendations
    """
    
    load_created = pyqtSignal(dict)  # Emit load data when complete
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Load Development Wizard")
        self.resize(900, 700)
        
        # Wizard pages
        self.page_intro = IntroPage()
        self.page_rifle = RifleSelectionPage()
        self.page_components = ComponentSelectionPage()
        self.page_prep = ComponentPrepPage()
        self.page_measurements = MeasurementsPage()
        self.page_load_specs = LoadSpecsPage()
        self.page_test_plan = TestPlanPage()
        self.page_ai_recommendations = AIRecommendationsPage()
        self.page_summary = SummaryPage()
        
        self.addPage(self.page_intro)
        self.addPage(self.page_rifle)
        self.addPage(self.page_components)
        self.addPage(self.page_prep)
        self.addPage(self.page_measurements)
        self.addPage(self.page_load_specs)
        self.addPage(self.page_test_plan)
        self.addPage(self.page_ai_recommendations)
        self.addPage(self.page_summary)
        
        # Style
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        
        # Connect finish
        self.finished.connect(self.on_finished)
    
    def on_finished(self, result):
        """Collect all data and emit"""
        if result == QWizard.DialogCode.Accepted:
            load_data = {
                'rifle': self.page_rifle.get_data(),
                'components': self.page_components.get_data(),
                'prep': self.page_prep.get_data(),
                'measurements': self.page_measurements.get_data(),
                'load_specs': self.page_load_specs.get_data(),
                'test_plan': self.page_test_plan.get_data(),
            }
            self.load_created.emit(load_data)


class IntroPage(QWizardPage):
    """Introduction page explaining the process"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("🎯 Velkommen til Load Development Wizard")
        self.setSubTitle("La oss utvikle den perfekte ladningen for din rifle!")
        
        layout = QVBoxLayout()
        
        info = QLabel(
            "<h3>Hva denne wizarden gjør:</h3>"
            "<ol>"
            "<li><b>Velg rifle & piperør</b> - Håndter system rifles med flere pipes</li>"
            "<li><b>Velg kaliber</b> - Tilpasset din pipe</li>"
            "<li><b>Velg komponenter</b> - Kuler, krutt, primer, hylser</li>"
            "<li><b>Komponent prep</b> - Glødet? Trimmede? Primer pocket uniformert?</li>"
            "<li><b>Målinger</b> - Fri flukt, skutt vs presset hylse dimensjoner</li>"
            "<li><b>Load specs</b> - Krutt mengde, sette dybde, COAL/CBTO</li>"
            "<li><b>Test plan</b> - OCW? Ladder? Seating depth?</li>"
            "<li><b>AI anbefalinger</b> - Basert på din rifle + komponenter + historikk</li>"
            "</ol>"
            "<br>"
            "<p style='background-color: #a8d5ba; padding: 10px; border-radius: 5px; color: #1a3a2a; font-weight: bold;'>"
            "<b>💡 Pro tips:</b><br>"
            "• Alt du legger inn lagres i databasen<br>"
            "• AI lærer av dine tidligere tester<br>"
            "• Neste gang får du bedre anbefalinger!<br>"
            "• For nybegynnere: Følg anbefalingene nøye<br>"
            "• For eksperter: Bruk quick-mode for rask registrering"
            "</p>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # User mode selection
        mode_group = QGroupBox("👤 Velg ditt nivå")
        mode_layout = QVBoxLayout()
        
        self.radio_beginner = QRadioButton("🔰 Nybegynner - Jeg trenger hjelp og forklaringer")
        self.radio_intermediate = QRadioButton("📊 Mellom - Jeg vet det grunnleggende")
        self.radio_expert = QRadioButton("⚡ Ekspert - Jeg vet hva jeg gjør, bare quick input")
        
        self.radio_intermediate.setChecked(True)
        
        mode_layout.addWidget(self.radio_beginner)
        mode_layout.addWidget(self.radio_intermediate)
        mode_layout.addWidget(self.radio_expert)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Register field for next pages to access
        self.registerField("user_mode", self.radio_beginner)


class RifleSelectionPage(QWizardPage):
    """Select rifle and barrel configuration"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("🔫 Velg Rifle & Piperør")
        self.setSubTitle("Mange rifles har system med flere piperør - velg riktig kombinasjon")
        
        layout = QVBoxLayout()
        
        # Help text for beginners
        self.help_label = QLabel(
            "💡 <b>Hvorfor dette er viktig:</b><br>"
            "Hver rifle har sin egen \"personlighet\". Samme ladning gir forskjellige "
            "resultater i forskjellige rifles. Ved å lagre rifle-info kan programmet gi "
            "bedre anbefalinger neste gang!"
        )
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet(
            "background-color: #b3d9f2; padding: 15px; border-radius: 5px; "
            "border: 2px solid #2874a6; font-size: 11pt; color: #0d3b66; font-weight: bold;"
        )
        self.help_label.setVisible(True)  # Ensure it's visible
        layout.addWidget(self.help_label)
        
        form = QFormLayout()
        
        # Rifle selection
        rifle_layout = QHBoxLayout()
        self.rifle_combo = QComboBox()
        self.rifle_combo.addItems([
            "Sauer 100",
            "Tikka T3x",
            "Browning X-Bolt",
            "Remington 700",
            "Sako 85",
            "Blaser R8 (System)",
            "Merkel RX Helix (System)",
            "Annen..."
        ])
        rifle_layout.addWidget(self.rifle_combo, 1)
        
        add_rifle_btn = QPushButton("➕ Legg til ny rifle")
        add_rifle_btn.clicked.connect(self.add_new_rifle)
        rifle_layout.addWidget(add_rifle_btn)
        
        form.addRow("Rifle modell:", rifle_layout)
        
        # Barrel selection (for system rifles)
        self.barrel_label = QLabel("Piperør:")
        barrel_layout = QHBoxLayout()
        self.barrel_combo = QComboBox()
        self.barrel_combo.addItems([
            "Standard pipe (medfølgende)",
            "Pipe 1 - 6.5 CM (24\", 1:8 twist)",
            "Pipe 2 - .308 Win (22\", 1:10 twist)",
            "Pipe 3 - .223 Rem (20\", 1:8 twist)",
        ])
        barrel_layout.addWidget(self.barrel_combo, 1)
        
        add_barrel_btn = QPushButton("➕ Legg til pipe")
        add_barrel_btn.clicked.connect(self.add_new_barrel)
        barrel_layout.addWidget(add_barrel_btn)
        
        form.addRow(self.barrel_label, barrel_layout)
        
        # Unit selection for barrel measurements
        unit_label = QLabel("📐 Måleenhet:")
        unit_btn_layout = QHBoxLayout()
        
        self.radio_metric = QRadioButton("mm")
        self.radio_imperial = QRadioButton("tommer")
        self.radio_metric.setChecked(True)
        self.radio_metric.toggled.connect(self.on_unit_changed)
        
        unit_btn_layout.addWidget(self.radio_metric)
        unit_btn_layout.addWidget(self.radio_imperial)
        unit_btn_layout.addStretch()
        
        form.addRow(unit_label, unit_btn_layout)
        
        # Barrel specs
        self.barrel_length = QDoubleSpinBox()
        self.barrel_length.setRange(400, 800)  # Start with metric (mm)
        self.barrel_length.setValue(610)  # ~24 inches
        self.barrel_length.setSuffix(" mm")
        self.barrel_length.setDecimals(0)
        form.addRow("Pipe lengde:", self.barrel_length)
        
        self.twist_rate = QComboBox()
        self.twist_rate.addItems([
            "1:7\" / 178mm (rask - tunge kuler)",
            "1:8\" / 203mm (standard - 140-155gr)",
            "1:9\" / 229mm (mellom)",
            "1:10\" / 254mm (standard .308)",
            "1:11\" / 279mm (lang)",
            "1:12\" / 305mm (klassisk)"
        ])
        form.addRow("Twist rate:", self.twist_rate)
        
        self.barrel_condition = QComboBox()
        self.barrel_condition.addItems([
            "Ny (<100 skudd)",
            "Innkjørt (100-500 skudd)",
            "Moderat brukt (500-1500 skudd)",
            "Mye brukt (1500-3000 skudd)",
            "Utslitt (>3000 skudd)"
        ])
        form.addRow("Pipe tilstand:", self.barrel_condition)
        
        # Scope info
        self.scope_height = QDoubleSpinBox()
        self.scope_height.setRange(30, 100)
        self.scope_height.setValue(45)
        self.scope_height.setSuffix(" mm")
        form.addRow("Scope høyde (over bore):", self.scope_height)
        
        layout.addLayout(form)
        
        # Notes
        notes_group = QGroupBox("📝 Notater (valgfritt)")
        notes_layout = QVBoxLayout()
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "F.eks: Rifle kjøpt 2023, ny pipe montert mars 2024, "
            "skyter best med 140gr kuler..."
        )
        self.notes.setMaximumHeight(80)
        notes_layout.addWidget(self.notes)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Initialize page with correct units"""
        # Make sure units match the selected radio button
        if self.radio_metric.isChecked():
            if self.barrel_length.suffix() != " mm":
                # Convert to metric if not already
                current_val = self.barrel_length.value()
                self.barrel_length.setRange(400, 800)
                self.barrel_length.setValue(current_val * 25.4)
                self.barrel_length.setSuffix(" mm")
                self.barrel_length.setDecimals(0)
    
    def on_unit_changed(self, checked):
        """Handle unit system toggle between metric and imperial"""
        if not checked:  # Only process when button is actually toggled
            return
            
        if self.radio_metric.isChecked():
            # Metric mode
            if self.barrel_length.suffix() != " mm":
                # Currently in inches, convert to mm
                current_val = self.barrel_length.value()
                self.barrel_length.setRange(400, 800)
                self.barrel_length.setValue(current_val * 25.4)
                self.barrel_length.setSuffix(" mm")
                self.barrel_length.setDecimals(0)
        else:
            # Imperial mode  
            if self.barrel_length.suffix() != " tommer":
                # Currently in mm, convert to inches
                current_val = self.barrel_length.value()
                self.barrel_length.setRange(16, 32)
                self.barrel_length.setValue(current_val / 25.4)
                self.barrel_length.setSuffix(" tommer")
                self.barrel_length.setDecimals(1)
    
    def add_new_rifle(self):
        """Add new rifle to database"""
        QMessageBox.information(self, "Add Rifle", "Rifle database editor kommer snart!")
    
    def add_new_barrel(self):
        """Add new barrel to system"""
        QMessageBox.information(self, "Add Barrel", "Barrel manager kommer snart!")
    
    def get_data(self) -> Dict:
        """Get selected rifle data"""
        # Store unit information
        barrel_unit = "mm" if self.radio_metric.isChecked() else "tommer"
        
        return {
            'rifle_model': self.rifle_combo.currentText(),
            'barrel': self.barrel_combo.currentText(),
            'barrel_length': self.barrel_length.value(),
            'barrel_length_unit': barrel_unit,
            'twist_rate': self.twist_rate.currentText(),
            'barrel_condition': self.barrel_condition.currentText(),
            'scope_height': self.scope_height.value(),
            'notes': self.notes.toPlainText()
        }


class ComponentSelectionPage(QWizardPage):
    """Select all components for the load"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("📦 Velg Komponenter")
        self.setSubTitle("Velg kuler, krutt, primer og hylser du skal bruke")
        
        layout = QVBoxLayout()
        
        # Caliber first
        caliber_group = QGroupBox("🎯 Kaliber")
        caliber_layout = QFormLayout()
        
        self.caliber = QComboBox()
        self.caliber.addItems([
            "6.5 Creedmoor",
            ".308 Winchester",
            ".223 Remington / 5.56 NATO",
            "6.5x55 Swedish",
            ".30-06 Springfield",
            "6mm Creedmoor",
            ".260 Remington",
            ".300 Winchester Magnum"
        ])
        caliber_layout.addRow("Kaliber:", self.caliber)
        
        caliber_group.setLayout(caliber_layout)
        layout.addWidget(caliber_group)
        
        # Bullet selection
        bullet_group = QGroupBox("🎯 Kule")
        bullet_layout = QFormLayout()
        
        bullet_select_layout = QHBoxLayout()
        self.bullet = QComboBox()
        self.bullet.setEditable(True)
        self.bullet.addItems([
            "Berger 140gr Hybrid Target",
            "Berger 130gr AR Hybrid OTM",
            "Sierra 142gr MatchKing",
            "Hornady 147gr ELD-M",
            "Lapua 139gr Scenar",
        ])
        bullet_select_layout.addWidget(self.bullet, 1)
        
        browse_bullet_btn = QPushButton("📦 Browse Database")
        browse_bullet_btn.clicked.connect(self.browse_bullets)
        bullet_select_layout.addWidget(browse_bullet_btn)
        
        bullet_layout.addRow("Velg kule:", bullet_select_layout)
        
        self.bullet_lot = QLineEdit()
        self.bullet_lot.setPlaceholderText("F.eks: 2024-08-L7342")
        bullet_layout.addRow("Lot nummer:", self.bullet_lot)
        
        bullet_group.setLayout(bullet_layout)
        layout.addWidget(bullet_group)
        
        # Powder selection
        powder_group = QGroupBox("💨 Krutt")
        powder_layout = QFormLayout()
        
        powder_select_layout = QHBoxLayout()
        self.powder = QComboBox()
        self.powder.setEditable(True)
        self.powder.addItems([
            "Vihtavuori N140",
            "Vihtavuori N150",
            "Hodgdon H4350",
            "Hodgdon Varget",
            "Alliant Reloder 16",
            "IMR 4064"
        ])
        powder_select_layout.addWidget(self.powder, 1)
        
        browse_powder_btn = QPushButton("📦 Browse Database")
        browse_powder_btn.clicked.connect(self.browse_powders)
        powder_select_layout.addWidget(browse_powder_btn)
        
        powder_layout.addRow("Velg krutt:", powder_select_layout)
        
        self.powder_lot = QLineEdit()
        self.powder_lot.setPlaceholderText("F.eks: V140-231015-A")
        powder_layout.addRow("Lot nummer:", self.powder_lot)
        
        powder_group.setLayout(powder_layout)
        layout.addWidget(powder_group)
        
        # Primer selection
        primer_group = QGroupBox("🔥 Tennhette")
        primer_layout = QFormLayout()
        
        self.primer = QComboBox()
        self.primer.addItems([
            "CCI BR-2 (Large Rifle Benchrest)",
            "Federal 210M (Match)",
            "CCI 450 (Small Rifle Magnum)",
            "Federal 205M (Small Rifle Match)",
            "Remington 9½ (Large Rifle)"
        ])
        primer_layout.addRow("Velg primer:", self.primer)
        
        self.primer_lot = QLineEdit()
        self.primer_lot.setPlaceholderText("F.eks: M48K2024")
        primer_layout.addRow("Lot nummer:", self.primer_lot)
        
        primer_group.setLayout(primer_layout)
        layout.addWidget(primer_group)
        
        # Brass selection
        brass_group = QGroupBox("🔩 Hylser")
        brass_layout = QFormLayout()
        
        self.brass = QComboBox()
        self.brass.addItems([
            "Lapua (virgin / ny)",
            "Lapua (1x skutt)",
            "Lapua (2-5x skutt)",
            "Norma (virgin)",
            "Hornady (virgin)",
            "Peterson (virgin)",
            "Federal (mixed headstamp)"
        ])
        brass_layout.addRow("Hylse type:", self.brass)
        
        self.brass_prep = QCheckBox("Hylser er glødet (annealed)")
        brass_layout.addRow("", self.brass_prep)
        
        brass_group.setLayout(brass_layout)
        layout.addWidget(brass_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def browse_bullets(self):
        """Open bullet database browser"""
        QMessageBox.information(self, "Component Database", 
                              "Component Database browser åpnes her!\n\n"
                              "Velg fra 100+ kuler med BC, specs, osv.")
    
    def browse_powders(self):
        """Open powder database browser"""
        QMessageBox.information(self, "Powder Database",
                              "Powder Database browser åpnes her!\n\n"
                              "Velg fra 50+ krutt med burn rate, density, osv.")
    
    def get_data(self) -> Dict:
        """Get component selection"""
        return {
            'caliber': self.caliber.currentText(),
            'bullet': self.bullet.currentText(),
            'bullet_lot': self.bullet_lot.text(),
            'powder': self.powder.currentText(),
            'powder_lot': self.powder_lot.text(),
            'primer': self.primer.currentText(),
            'primer_lot': self.primer_lot.text(),
            'brass': self.brass.currentText(),
            'brass_annealed': self.brass_prep.isChecked()
        }


class ComponentPrepPage(QWizardPage):
    """Component preparation details"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("🔧 Komponent Preparering")
        self.setSubTitle("Hvordan har du preparert hylsene? Dette påvirker konsistens!")
        
        layout = QVBoxLayout()
        
        info = QLabel(
            "💡 <b>Hvorfor dette er viktig:</b><br>"
            "Konsistens i hylse-prep gir konsistens i skudd! Selv små forskjeller "
            "i neck tension, primer pocket depth, osv. påvirker SD/ES."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #f9e79f; padding: 10px; border-radius: 5px; color: #7d6608; font-weight: bold;")
        layout.addWidget(info)
        
        # Brass prep checklist
        prep_group = QGroupBox("✅ Hylse Preparering Sjekkliste")
        prep_layout = QVBoxLayout()
        
        self.check_full_length_sized = QCheckBox("Full-length sized")
        self.check_neck_sized = QCheckBox("Neck sized only")
        self.check_trimmed = QCheckBox("Trimmet til riktig lengde")
        self.check_chamfered = QCheckBox("Chamfered & deburred")
        self.check_primer_pocket = QCheckBox("Primer pocket uniformed")
        self.check_flash_hole = QCheckBox("Flash hole deburred")
        self.check_annealed = QCheckBox("Annealed (glødet)")
        self.check_weight_sorted = QCheckBox("Weight sorted (±0.5gr)")
        
        prep_layout.addWidget(self.check_full_length_sized)
        prep_layout.addWidget(self.check_neck_sized)
        prep_layout.addWidget(self.check_trimmed)
        prep_layout.addWidget(self.check_chamfered)
        prep_layout.addWidget(self.check_primer_pocket)
        prep_layout.addWidget(self.check_flash_hole)
        prep_layout.addWidget(self.check_annealed)
        prep_layout.addWidget(self.check_weight_sorted)
        
        prep_group.setLayout(prep_layout)
        layout.addWidget(prep_group)
        
        # Measurements
        measure_group = QGroupBox("📏 Hylse Målinger")
        measure_layout = QFormLayout()
        
        self.case_length = QDoubleSpinBox()
        self.case_length.setRange(30, 70)
        self.case_length.setValue(48.5)  # 6.5 CM default
        self.case_length.setSuffix(" mm")
        self.case_length.setDecimals(2)
        measure_layout.addRow("Case length (trimmed):", self.case_length)
        
        self.neck_diameter = QDoubleSpinBox()
        self.neck_diameter.setRange(6, 15)
        self.neck_diameter.setValue(7.2)  # 6.5 CM default
        self.neck_diameter.setSuffix(" mm")
        self.neck_diameter.setDecimals(3)
        measure_layout.addRow("Neck diameter (loaded):", self.neck_diameter)
        
        self.neck_tension = QDoubleSpinBox()
        self.neck_tension.setRange(0.001, 0.010)
        self.neck_tension.setValue(0.002)
        self.neck_tension.setSuffix(" \"")
        self.neck_tension.setDecimals(3)
        measure_layout.addRow("Neck tension:", self.neck_tension)
        
        measure_group.setLayout(measure_layout)
        layout.addWidget(measure_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self) -> Dict:
        """Get prep data"""
        return {
            'full_length_sized': self.check_full_length_sized.isChecked(),
            'neck_sized': self.check_neck_sized.isChecked(),
            'trimmed': self.check_trimmed.isChecked(),
            'chamfered': self.check_chamfered.isChecked(),
            'primer_pocket_uniformed': self.check_primer_pocket.isChecked(),
            'flash_hole_deburred': self.check_flash_hole.isChecked(),
            'annealed': self.check_annealed.isChecked(),
            'weight_sorted': self.check_weight_sorted.isChecked(),
            'case_length': self.case_length.value(),
            'neck_diameter': self.neck_diameter.value(),
            'neck_tension': self.neck_tension.value()
        }


class MeasurementsPage(QWizardPage):
    """Critical measurements - freebore, fired vs sized brass"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("📏 Kritiske Målinger")
        self.setSubTitle("Disse målingene er essensielle for optimal ladning!")
        
        layout = QVBoxLayout()
        
        # Freebore/Jump
        freebore_group = QGroupBox("🎯 Fri Flukt (Freebore / Jump)")
        freebore_layout = QVBoxLayout()
        
        info = QLabel(
            "💡 Fri flukt = avstanden fra kula til rifling.\n"
            "Måles med Hornady OAL gauge eller split-case method."
        )
        info.setWordWrap(True)
        freebore_layout.addWidget(info)
        
        form = QFormLayout()
        
        self.ogive_to_lands = QDoubleSpinBox()
        self.ogive_to_lands.setRange(50, 90)
        self.ogive_to_lands.setValue(65.5)
        self.ogive_to_lands.setSuffix(" mm (CBTO)")
        self.ogive_to_lands.setDecimals(2)
        form.addRow("Ogive til rifling (touching):", self.ogive_to_lands)
        
        self.desired_jump = QDoubleSpinBox()
        self.desired_jump.setRange(0, 1)
        self.desired_jump.setValue(0.020)
        self.desired_jump.setSuffix(" \" (~0.5mm)")
        self.desired_jump.setDecimals(3)
        form.addRow("Ønsket jump:", self.desired_jump)
        
        freebore_layout.addLayout(form)
        freebore_group.setLayout(freebore_layout)
        layout.addWidget(freebore_group)
        
        # Brass measurements
        brass_group = QGroupBox("🔩 Hylse Dimensjoner (Skutt vs Presset)")
        brass_layout = QFormLayout()
        
        brass_info = QLabel(
            "Mål hylse FØR og ETTER sizing for å se hvor mye du presser.\n"
            "Case head expansion indikerer trykk!"
        )
        brass_info.setWordWrap(True)
        brass_layout.addRow(brass_info)
        
        # Fired measurements
        self.case_head_fired = QDoubleSpinBox()
        self.case_head_fired.setRange(10, 20)
        self.case_head_fired.setValue(12.015)
        self.case_head_fired.setSuffix(" mm")
        self.case_head_fired.setDecimals(3)
        brass_layout.addRow("Case head (fired):", self.case_head_fired)
        
        self.case_shoulder_fired = QDoubleSpinBox()
        self.case_shoulder_fired.setRange(10, 20)
        self.case_shoulder_fired.setValue(11.8)
        self.case_shoulder_fired.setSuffix(" mm")
        self.case_shoulder_fired.setDecimals(3)
        brass_layout.addRow("Shoulder diameter (fired):", self.case_shoulder_fired)
        
        # Sized measurements
        self.case_head_sized = QDoubleSpinBox()
        self.case_head_sized.setRange(10, 20)
        self.case_head_sized.setValue(12.010)
        self.case_head_sized.setSuffix(" mm")
        self.case_head_sized.setDecimals(3)
        brass_layout.addRow("Case head (sized):", self.case_head_sized)
        
        self.case_shoulder_sized = QDoubleSpinBox()
        self.case_shoulder_sized.setRange(10, 20)
        self.case_shoulder_sized.setValue(11.75)
        self.case_shoulder_sized.setSuffix(" mm")
        self.case_shoulder_sized.setDecimals(3)
        brass_layout.addRow("Shoulder diameter (sized):", self.case_shoulder_sized)
        
        # Shoulder bump
        self.shoulder_bump = QDoubleSpinBox()
        self.shoulder_bump.setRange(0, 0.010)
        self.shoulder_bump.setValue(0.002)
        self.shoulder_bump.setSuffix(" \" (~0.05mm)")
        self.shoulder_bump.setDecimals(3)
        brass_layout.addRow("Shoulder bump:", self.shoulder_bump)
        
        brass_group.setLayout(brass_layout)
        layout.addWidget(brass_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self) -> Dict:
        """Get measurement data"""
        return {
            'ogive_to_lands': self.ogive_to_lands.value(),
            'desired_jump': self.desired_jump.value(),
            'case_head_fired': self.case_head_fired.value(),
            'case_shoulder_fired': self.case_shoulder_fired.value(),
            'case_head_sized': self.case_head_sized.value(),
            'case_shoulder_sized': self.case_shoulder_sized.value(),
            'shoulder_bump': self.shoulder_bump.value()
        }


class LoadSpecsPage(QWizardPage):
    """Specify load parameters - charge weight, seating depth"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("⚖️ Ladnings Spesifikasjoner")
        self.setSubTitle("Sett start-verdier for krutt mengde og sette dybde")
        
        layout = QVBoxLayout()
        
        # Charge weight
        charge_group = QGroupBox("💨 Krutt Mengde")
        charge_layout = QFormLayout()
        
        charge_info = QLabel(
            "⚠️ <b>START ALLTID LAVT!</b><br>"
            "Bruk lademanual data - start 10% under max."
        )
        charge_info.setWordWrap(True)
        charge_info.setStyleSheet("background-color: #f8c471; padding: 8px; border-radius: 5px; color: #7e4a1e; font-weight: bold;")
        charge_layout.addRow(charge_info)
        
        self.charge_start = QDoubleSpinBox()
        self.charge_start.setRange(10, 80)
        self.charge_start.setValue(38.5)
        self.charge_start.setSuffix(" gr")
        self.charge_start.setDecimals(1)
        charge_layout.addRow("Start charge:", self.charge_start)
        
        self.charge_max = QDoubleSpinBox()
        self.charge_max.setRange(10, 80)
        self.charge_max.setValue(42.0)
        self.charge_max.setSuffix(" gr")
        self.charge_max.setDecimals(1)
        charge_layout.addRow("Max charge (fra manual):", self.charge_max)
        
        charge_group.setLayout(charge_layout)
        layout.addWidget(charge_group)
        
        # Seating depth
        seating_group = QGroupBox("📏 Sette Dybde")
        seating_layout = QFormLayout()
        
        self.seating_method = QComboBox()
        self.seating_method.addItems([
            "CBTO (Cartridge Base to Ogive) - Anbefalt!",
            "COAL (Cartridge Overall Length)"
        ])
        seating_layout.addRow("Måle metode:", self.seating_method)
        
        self.cbto_target = QDoubleSpinBox()
        self.cbto_target.setRange(50, 90)
        self.cbto_target.setValue(65.0)
        self.cbto_target.setSuffix(" mm")
        self.cbto_target.setDecimals(2)
        seating_layout.addRow("Target CBTO:", self.cbto_target)
        
        self.coal_target = QDoubleSpinBox()
        self.coal_target.setRange(50, 100)
        self.coal_target.setValue(73.0)
        self.coal_target.setSuffix(" mm")
        self.coal_target.setDecimals(2)
        seating_layout.addRow("Target COAL:", self.coal_target)
        
        self.mag_length = QDoubleSpinBox()
        self.mag_length.setRange(50, 100)
        self.mag_length.setValue(72.8)
        self.mag_length.setSuffix(" mm")
        self.mag_length.setDecimals(2)
        seating_layout.addRow("Max magasin lengde:", self.mag_length)
        
        seating_group.setLayout(seating_layout)
        layout.addWidget(seating_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self) -> Dict:
        """Get load specs"""
        return {
            'charge_start': self.charge_start.value(),
            'charge_max': self.charge_max.value(),
            'seating_method': self.seating_method.currentText(),
            'cbto_target': self.cbto_target.value(),
            'coal_target': self.coal_target.value(),
            'mag_length': self.mag_length.value()
        }


class TestPlanPage(QWizardPage):
    """Select test methodology"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("🧪 Test Plan")
        self.setSubTitle("Hvordan vil du teste ladningen?")
        
        layout = QVBoxLayout()
        
        info = QLabel(
            "<b>Velg test metode basert på ditt mål:</b><br>"
            "• <b>OCW Test:</b> Best for å finne stabil charge weight (gruppert på distanse)<br>"
            "• <b>Ladder Test:</b> Best for å finne pressure nodes (fart-plateauer)<br>"
            "• <b>Seating Depth:</b> Test etter du har funnet optimal charge<br>"
            "• <b>Full kombinert:</b> Test alt samtidig (tar lang tid!)"
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #b3d9f2; padding: 10px; border-radius: 5px; color: #0d3b66; font-weight: bold;")
        layout.addWidget(info)
        
        test_group = QGroupBox("🎯 Velg Test Metode")
        test_layout = QVBoxLayout()
        
        self.test_ocw = QRadioButton("OCW Test (Optimal Charge Weight)")
        self.test_ladder = QRadioButton("Ladder Test (Velocity nodes)")
        self.test_seating = QRadioButton("Seating Depth Test")
        self.test_combined = QRadioButton("Full kombinert test (OCW + Seating)")
        
        self.test_ocw.setChecked(True)
        
        test_layout.addWidget(self.test_ocw)
        test_layout.addWidget(self.test_ladder)
        test_layout.addWidget(self.test_seating)
        test_layout.addWidget(self.test_combined)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # Test parameters
        params_group = QGroupBox("⚙️ Test Parametere")
        params_layout = QFormLayout()
        
        self.rounds_per_group = QSpinBox()
        self.rounds_per_group.setRange(3, 10)
        self.rounds_per_group.setValue(5)
        self.rounds_per_group.setSuffix(" skudd")
        params_layout.addRow("Skudd per gruppe:", self.rounds_per_group)
        
        self.charge_increment = QDoubleSpinBox()
        self.charge_increment.setRange(0.1, 1.0)
        self.charge_increment.setValue(0.3)
        self.charge_increment.setSuffix(" gr")
        self.charge_increment.setDecimals(1)
        params_layout.addRow("Charge increment:", self.charge_increment)
        
        self.test_distance = QSpinBox()
        self.test_distance.setRange(50, 1000)
        self.test_distance.setValue(100)
        self.test_distance.setSuffix(" meter")
        params_layout.addRow("Test distanse:", self.test_distance)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self) -> Dict:
        """Get test plan"""
        test_type = "ocw"
        if self.test_ladder.isChecked():
            test_type = "ladder"
        elif self.test_seating.isChecked():
            test_type = "seating"
        elif self.test_combined.isChecked():
            test_type = "combined"
        
        return {
            'test_type': test_type,
            'rounds_per_group': self.rounds_per_group.value(),
            'charge_increment': self.charge_increment.value(),
            'test_distance': self.test_distance.value()
        }


class AIRecommendationsPage(QWizardPage):
    """AI-generated recommendations based on input"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("🤖 AI Anbefalinger")
        self.setSubTitle("Basert på dine valg og historisk data")
        
        layout = QVBoxLayout()
        
        info = QLabel(
            "🤖 <b>AI Analyse Kjører...</b><br>"
            "Analyserer dine valg mot database med 10,000+ loads..."
        )
        info.setStyleSheet("background-color: #a8d5ba; padding: 10px; border-radius: 5px; color: #1a3a2a; font-weight: bold;")
        layout.addWidget(info)
        
        # Recommendations display
        self.recommendations = QTextEdit()
        self.recommendations.setReadOnly(True)
        layout.addWidget(self.recommendations)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Generate recommendations when page is shown"""
        html = self.generate_recommendations()
        self.recommendations.setHtml(html)
    
    def generate_recommendations(self) -> str:
        """Generate AI recommendations (simulated)"""
        return """
        <h3>🎯 Anbefalinger for din ladning:</h3>
        
        <div style='background-color: #a8d5ba; padding: 15px; border-radius: 5px; margin: 10px 0; color: #1a3a2a;'>
        <h4>✅ Optimal Start Charge: 39.5gr</h4>
        <p><b>Hvorfor:</b> Basert på 247 lignende loads med samme rifle/kule/krutt kombinasjon, 
        starter de fleste trygt på 39.5gr med god precision.</p>
        <p><b>Forventet fart:</b> ~2720 fps (±20 fps)</p>
        </div>
        
        <div style='background-color: #f9e79f; padding: 15px; border-radius: 5px; margin: 10px 0; color: #7d6608;'>
        <h4>📏 Anbefalt Seating Depth: 0.020" jump</h4>
        <p><b>Hvorfor:</b> Berger Hybrid kuler liker typisk 0.010-0.030" jump. 
        Din rifle (1:8 twist, 24") har vist best resultater med 0.020" i tidligere tester.</p>
        </div>
        
        <div style='background-color: #b3d9f2; padding: 15px; border-radius: 5px; margin: 10px 0; color: #0d3b66;'>
        <h4>🧪 Test Anbefaling: OCW Test</h4>
        <p><b>Hvorfor:</b> For nye ladninger anbefaler vi OCW test først.</p>
        <p><b>Forslag:</b></p>
        <ul>
            <li>Start: 39.5gr</li>
            <li>Increment: 0.3gr</li>
            <li>Slutt: 41.5gr (7 grupper x 5 skudd = 35 patroner)</li>
            <li>Distanse: 100m</li>
        </ul>
        </div>
        
        <div style='background-color: #f8c471; padding: 15px; border-radius: 5px; margin: 10px 0; color: #7e4a1e;'>
        <h4>⚠️ Viktige Advarsler:</h4>
        <ul>
            <li>Sjekk ALLTID for pressure signs (flattened primers, sticky bolt)</li>
            <li>Ditt krutt lot kan være ±30 fps vs andre lots</li>
            <li>Hold øye på case head expansion (skal ikke øke >0.002")</li>
            <li>Stopp umiddelbart hvis du ser pressure signs!</li>
        </ul>
        </div>
        
        <h4>💡 Pro Tips:</h4>
        <ul>
            <li>Rengjør rifle etter 20-30 skudd for konsistens</li>
            <li>La rifle kjøle seg mellom grupper (varm pipe = høyere trykk)</li>
            <li>Bruk chronograph - SD/ES er like viktig som gruppestørrelse</li>
            <li>Noter ALLE detaljer - vær, temp, fuktighet påvirker resultater</li>
        </ul>
        """


class SummaryPage(QWizardPage):
    """Final summary before creating load"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("📋 Oppsummering")
        self.setSubTitle("Sjekk at alt er riktig før du starter test!")
        
        layout = QVBoxLayout()
        
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        layout.addWidget(self.summary)
        
        # Save options
        save_group = QGroupBox("💾 Lagre & Del")
        save_layout = QVBoxLayout()
        
        self.save_to_database = QCheckBox("Lagre load til database (anbefalt)")
        self.save_to_database.setChecked(True)
        save_layout.addWidget(self.save_to_database)
        
        self.create_label = QCheckBox("Print loading labels (PDF)")
        save_layout.addWidget(self.create_label)
        
        self.export_excel = QCheckBox("Export til Excel for test-logging")
        save_layout.addWidget(self.export_excel)
        
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Update summary when page is shown"""
        wizard = self.wizard()
        
        summary_html = "<h2>📋 Din Load Development Plan</h2>"
        
        # Rifle section
        rifle_data = wizard.page_rifle.get_data()
        barrel_length_display = f"{rifle_data['barrel_length']:.1f} {rifle_data.get('barrel_length_unit', 'mm')}"
        
        summary_html += f"""
        <h3>🔫 Rifle:</h3>
        <ul>
            <li><b>Modell:</b> {rifle_data['rifle_model']}</li>
            <li><b>Piperør:</b> {rifle_data['barrel']}</li>
            <li><b>Lengde:</b> {barrel_length_display}</li>
            <li><b>Twist:</b> {rifle_data['twist_rate']}</li>
        </ul>
        """
        
        # Components section
        comp_data = wizard.page_components.get_data()
        summary_html += f"""
        <h3>📦 Komponenter:</h3>
        <ul>
            <li><b>Kaliber:</b> {comp_data['caliber']}</li>
            <li><b>Kule:</b> {comp_data['bullet']} (Lot: {comp_data['bullet_lot']})</li>
            <li><b>Krutt:</b> {comp_data['powder']} (Lot: {comp_data['powder_lot']})</li>
            <li><b>Primer:</b> {comp_data['primer']}</li>
            <li><b>Hylser:</b> {comp_data['brass']}</li>
        </ul>
        """
        
        # Load specs
        load_data = wizard.page_load_specs.get_data()
        summary_html += f"""
        <h3>⚖️ Load Specs:</h3>
        <ul>
            <li><b>Start charge:</b> {load_data['charge_start']}gr</li>
            <li><b>Max charge:</b> {load_data['charge_max']}gr</li>
            <li><b>CBTO:</b> {load_data['cbto_target']}mm</li>
            <li><b>COAL:</b> {load_data['coal_target']}mm</li>
        </ul>
        """
        
        # Test plan
        test_data = wizard.page_test_plan.get_data()
        summary_html += f"""
        <h3>🧪 Test Plan:</h3>
        <ul>
            <li><b>Type:</b> {test_data['test_type'].upper()}</li>
            <li><b>Skudd per gruppe:</b> {test_data['rounds_per_group']}</li>
            <li><b>Increment:</b> {test_data['charge_increment']}gr</li>
            <li><b>Distanse:</b> {test_data['test_distance']}m</li>
        </ul>
        """
        
        summary_html += """
        <div style='background-color: #a8d5ba; padding: 15px; border-radius: 5px; margin-top: 20px; color: #1a3a2a;'>
        <h4>✅ Alt klart!</h4>
        <p>Trykk <b>Finish</b> for å lagre og starte test workflow.</p>
        </div>
        """
        
        self.summary.setHtml(summary_html)


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    wizard = LoadDevelopmentWizard()
    wizard.show()
    
    sys.exit(app.exec())
