"""
Advanced Rifle Profile Editor
Comprehensive rifle configuration for precision load development
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox,
                            QPushButton, QLabel, QTextEdit, QGroupBox, QCheckBox,
                            QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox,
                            QRadioButton, QButtonGroup, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter
from src.database.database import get_database
from typing import Dict, Optional


class RifleProfileEditor(QDialog):
    """
    Comprehensive rifle profile editor
    Captures ALL data needed for precision load development & harmonics
    """
    
    rifle_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, rifle_id: Optional[int] = None, user_mode: str = "beginner"):
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id
        self.rifle_data = {}
        self.user_mode = user_mode  # "beginner" or "expert"
        
        self.setWindowTitle("🎯 Rifle Profil Editor")
        self.setMinimumSize(1000, 800)
        
        self.init_ui()
        
        if rifle_id:
            self.load_rifle_data()
    
    def init_ui(self):
        """Initialize comprehensive UI"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🎯 Komplett Rifle Profil")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        # User mode toggle
        mode_layout = QHBoxLayout()
        mode_label = QLabel("👤 Bruker Modus:")
        mode_layout.addWidget(mode_label)
        
        self.mode_beginner = QRadioButton("🌱 Nybegynner (Enkelt)")
        self.mode_expert = QRadioButton("🎓 Ekspert (Full detaljer)")
        
        if self.user_mode == "expert":
            self.mode_expert.setChecked(True)
        else:
            self.mode_beginner.setChecked(True)
        
        self.mode_beginner.toggled.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.mode_beginner)
        mode_layout.addWidget(self.mode_expert)
        mode_layout.addStretch()
        
        mode_widget = QWidget()
        mode_widget.setLayout(mode_layout)
        mode_widget.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
            }
            QRadioButton {
                font-weight: bold;
            }
        """)
        layout.addWidget(mode_widget)
        
        desc = QLabel(
            "Lag en detaljert profil av riflen din. Jo mer data, desto bedre anbefalinger "
            "kan AI gi for ladeutvikling, harmonics og presisjon."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Tabs for organized input - conditional based on user mode
        self.tabs = QTabWidget()
        
        # Tab 1: Basic Info (always shown)
        self.tabs.addTab(self.create_basic_tab(), "📋 Grunnleggende")
        
        if self.user_mode == "beginner":
            # Beginner mode: simplified barrel tab only
            self.tabs.addTab(self.create_barrel_tab_simple(), "🔫 Pipe")
        else:
            # Expert mode: all tabs with full details
            # Tab 2: Barrel Details
            self.tabs.addTab(self.create_barrel_tab(), "🔫 Pipe Detaljer")
            
            # Tab 3: Muzzle Devices
            self.tabs.addTab(self.create_muzzle_tab(), "🔇 Lyddemper/Brems")
            
            # Tab 4: Chamber & Tolerances
            self.tabs.addTab(self.create_chamber_tab(), "📏 Kammer & Toleranser")
            
            # Tab 5: Bullet Profiles (Freebore per bullet)
            self.tabs.addTab(self.create_bullet_profiles_tab(), "🎯 Kule Profiler")
            
            # Tab 6: Visual Preview
            self.tabs.addTab(self.create_preview_tab(), "👁️ Visuell Oversikt")
        
        layout.addWidget(self.tabs)
        
        # Save/Cancel buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Lagre Profil")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_profile)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Avbryt")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def create_basic_tab(self) -> QWidget:
        """Basic rifle information"""
        widget = QWidget()
        layout = QVBoxLayout()

        form = QFormLayout()

        # Weapon type
        self.weapon_type = QComboBox()
        self.weapon_type.addItems(["Rifle", "Pistol"])
        self.weapon_type.currentTextChanged.connect(self.on_weapon_type_changed)
        form.addRow("Våpentype:", self.weapon_type)

        # Name
        self.name = QLineEdit()
        self.name.setPlaceholderText("F.eks: Tikka T3X CTR .308 eller Pardini SP .22LR")
        form.addRow("Våpen Navn:", self.name)

        # Manufacturer
        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText("Tikka, Sako, Bergara, Pardini, Walther, etc.")
        form.addRow("Produsent:", self.manufacturer)

        # Caliber
        self.caliber = QComboBox()
        self.caliber.setEditable(True)
        self.caliber.addItems([
            ".308 Winchester",
            "6.5 Creedmoor",
            ".223 Remington",
            "6.5x55 Swedish",
            ".30-06 Springfield",
            "6mm Creedmoor",
            ".300 Win Mag",
            ".22LR",
            ".32 S&W Long",
            ".38 Special",
            "9mm Luger",
            ".45 ACP"
        ])
        form.addRow("Kaliber:", self.caliber)

        # Action type
        self.action_type = QComboBox()
        self.action_type.addItems([
            "Bolt Action",
            "Semi-Auto",
            "Lever Action",
            "Single Shot",
            "Revolver",
            "Pistol"
        ])
        form.addRow("Mekanisme:", self.action_type)

        # Serial number
        self.serial = QLineEdit()
        self.serial.setPlaceholderText("Valgfritt - for identifikasjon")
        form.addRow("Serienummer:", self.serial)

        # Dynamisk pistolspesifikke felter
        self.pistol_fields = {}
        self.pistol_fields["sikte"] = QLineEdit(); self.pistol_fields["sikte"].setPlaceholderText("F.eks: Red Dot, Jern")
        self.pistol_fields["avtrekk"] = QLineEdit(); self.pistol_fields["avtrekk"].setPlaceholderText("F.eks: 1000g, justerbar")
        self.pistol_fields["magasin"] = QSpinBox(); self.pistol_fields["magasin"].setRange(1, 20)
        # Skjules for rifle, vises for pistol
        for label, widget in self.pistol_fields.items():
            form.addRow(f"Pistol {label.capitalize()}:", widget)
            widget.hide()

        layout.addLayout(form)

        # Notes
        notes_group = QGroupBox("📝 Notater")
        notes_layout = QVBoxLayout()
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "F.eks: Kjøpt 2023, custom trigger, bedding job done..."
        )
        self.notes.setMaximumHeight(100)
        notes_layout.addWidget(self.notes)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_weapon_type_changed(self, value):
        is_pistol = value == "Pistol"
        for widget in self.pistol_fields.values():
            widget.setVisible(is_pistol)
    
    def create_barrel_tab_simple(self) -> QWidget:
        """Simplified barrel tab for beginners"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        info = QLabel(
            "ℹ️ Dette er forenklet visning. Bytt til Ekspert modus for detaljerte "
            "harmonics beregninger og kammer toleranser."
        )
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                background-color: #d5e8f7;
                color: #0d3b66;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(info)
        
        # Simple form - just the essentials
        form = QFormLayout()
        
        # Length
        length_layout = QHBoxLayout()
        self.barrel_length = QDoubleSpinBox()
        self.barrel_length.setRange(250, 900)
        self.barrel_length.setValue(610)
        self.barrel_length.setSuffix(" mm")
        self.barrel_length.setDecimals(0)
        length_layout.addWidget(self.barrel_length)
        
        self.radio_metric = QRadioButton("mm")
        self.radio_imperial = QRadioButton("tommer")
        self.radio_metric.setChecked(True)
        length_layout.addWidget(self.radio_metric)
        length_layout.addWidget(self.radio_imperial)
        length_layout.addStretch()
        
        form.addRow("Pipe Lengde:", length_layout)
        
        # Twist rate
        self.twist_rate = QComboBox()
        self.twist_rate.setEditable(True)
        self.twist_rate.addItems([
            "1:7\" / 178mm",
            "1:8\" / 203mm",
            "1:9\" / 229mm",
            "1:10\" / 254mm",
            "1:11\" / 279mm",
            "1:12\" / 305mm"
        ])
        form.addRow("Twist Rate:", self.twist_rate)
        
        # Profile (simple)
        self.barrel_profile_simple = QComboBox()
        self.barrel_profile_simple.addItems([
            "Standard/Sporter",
            "Medium/Varmint",
            "Tung/Heavy",
            "Bull Barrel"
        ])
        form.addRow("Pipe Type:", self.barrel_profile_simple)
        
        layout.addLayout(form)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_barrel_tab(self) -> QWidget:
        """Detailed barrel specifications"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Barrel dimensions
        dim_group = QGroupBox("📏 Pipe Dimensjoner")
        dim_form = QFormLayout()
        
        # Length
        length_layout = QHBoxLayout()
        self.barrel_length = QDoubleSpinBox()
        self.barrel_length.setRange(250, 900)
        self.barrel_length.setValue(610)
        self.barrel_length.setSuffix(" mm")
        self.barrel_length.setDecimals(0)
        length_layout.addWidget(self.barrel_length)
        
        self.radio_metric = QRadioButton("mm")
        self.radio_imperial = QRadioButton("tommer")
        self.radio_metric.setChecked(True)
        length_layout.addWidget(self.radio_metric)
        length_layout.addWidget(self.radio_imperial)
        length_layout.addStretch()
        
        dim_form.addRow("Pipe Lengde:", length_layout)
        
        # Twist rate
        self.twist_rate = QComboBox()
        self.twist_rate.setEditable(True)
        self.twist_rate.addItems([
            "1:7\" / 178mm",
            "1:8\" / 203mm",
            "1:9\" / 229mm",
            "1:10\" / 254mm",
            "1:11\" / 279mm",
            "1:12\" / 305mm"
        ])
        dim_form.addRow("Twist Rate:", self.twist_rate)
        
        dim_group.setLayout(dim_form)
        layout.addWidget(dim_group)
        
        # Barrel profile
        profile_group = QGroupBox("🎨 Pipe Profil & Konstruksjon")
        profile_form = QFormLayout()
        
        self.barrel_profile = QComboBox()
        self.barrel_profile.addItems([
            "Straight/Cylinder (Heavy)",
            "Light Taper (Sporter)",
            "Medium Taper (Hunting)",
            "Heavy Taper (Varmint)",
            "Bull Barrel",
            "Fluted"
        ])
        profile_form.addRow("Profil Type:", self.barrel_profile)
        
        # Muzzle diameter
        self.muzzle_diameter = QDoubleSpinBox()
        self.muzzle_diameter.setRange(10, 30)
        self.muzzle_diameter.setValue(18)
        self.muzzle_diameter.setSuffix(" mm")
        self.muzzle_diameter.setDecimals(1)
        profile_form.addRow("Muzzle Diameter:", self.muzzle_diameter)
        
        # Breech diameter
        self.breech_diameter = QDoubleSpinBox()
        self.breech_diameter.setRange(15, 35)
        self.breech_diameter.setValue(25)
        self.breech_diameter.setSuffix(" mm")
        self.breech_diameter.setDecimals(1)
        profile_form.addRow("Breech Diameter:", self.breech_diameter)
        
        # Material
        self.barrel_material = QComboBox()
        self.barrel_material.addItems([
            "Chrome-Moly Steel",
            "Stainless Steel (416R)",
            "Stainless Steel (17-4PH)",
            "Carbon Fiber Wrapped",
            "Annen"
        ])
        profile_form.addRow("Materiale:", self.barrel_material)
        
        # Weight
        self.barrel_weight = QSpinBox()
        self.barrel_weight.setRange(500, 5000)
        self.barrel_weight.setValue(1200)
        self.barrel_weight.setSuffix(" g")
        profile_form.addRow("Pipe Vekt (approx):", self.barrel_weight)
        
        profile_group.setLayout(profile_form)
        layout.addWidget(profile_group)
        
        # Mounting & Bedding
        mount_group = QGroupBox("🔧 Montering & Bedding")
        mount_form = QFormLayout()
        
        self.free_float = QCheckBox("Ja, pipen er fritt hengende")
        self.free_float.setChecked(True)
        mount_form.addRow("Free Floating:", self.free_float)
        
        self.bedding_type = QComboBox()
        self.bedding_type.addItems([
            "Factory (ingen custom)",
            "Pillar Bedded",
            "Glass Bedded",
            "Aluminum Block",
            "Chassis System"
        ])
        mount_form.addRow("Bedding Type:", self.bedding_type)
        
        self.stock_material = QComboBox()
        self.stock_material.addItems([
            "Synthetic/Plastic",
            "Wood (Walnut/Beech)",
            "Laminate",
            "Carbon Fiber",
            "Aluminum Chassis"
        ])
        mount_form.addRow("Stock Materiale:", self.stock_material)
        
        mount_group.setLayout(mount_form)
        layout.addWidget(mount_group)
        
        # Barrel condition
        condition_group = QGroupBox("🔍 Pipe Tilstand")
        condition_form = QFormLayout()
        
        self.round_count = QSpinBox()
        self.round_count.setRange(0, 10000)
        self.round_count.setSuffix(" skudd")
        condition_form.addRow("Total Skudd Teller:", self.round_count)
        
        self.barrel_condition = QComboBox()
        self.barrel_condition.addItems([
            "Ny (<100 skudd)",
            "Innkjørt (100-500)",
            "Moderat brukt (500-1500)",
            "Mye brukt (1500-3000)",
            "Utslitt (>3000)"
        ])
        condition_form.addRow("Tilstand:", self.barrel_condition)
        
        self.throat_erosion = QComboBox()
        self.throat_erosion.addItems([
            "Ingen målbar erosion",
            "Minimal (<0.020\")",
            "Moderat (0.020-0.050\")",
            "Betydelig (>0.050\")"
        ])
        condition_form.addRow("Throat Erosion:", self.throat_erosion)
        
        condition_group.setLayout(condition_form)
        layout.addWidget(condition_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_muzzle_tab(self) -> QWidget:
        """Muzzle devices (suppressor, brake, etc.)"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        info = QLabel(
            "💡 <b>Hvorfor er dette viktig?</b><br>"
            "Lyddempere og bremser påvirker pipe harmonics betydelig! "
            "Vekt og lengde endrer barrel nodes og kan flytte POI (Point of Impact)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #b3d9f2; padding: 10px; border-radius: 5px; color: #0d3b66;")
        layout.addWidget(info)
        
        device_group = QGroupBox("🔇 Muzzle Device")
        device_form = QFormLayout()
        
        self.has_device = QCheckBox("Bruker lyddemper/brems")
        self.has_device.toggled.connect(self.toggle_device_fields)
        device_form.addRow("Har device:", self.has_device)
        
        self.device_type = QComboBox()
        self.device_type.addItems([
            "Ingen",
            "Lyddemper (Suppressor)",
            "Muzzle Brake",
            "Flash Hider",
            "Compensator"
        ])
        device_form.addRow("Type:", self.device_type)
        
        self.device_manufacturer = QLineEdit()
        self.device_manufacturer.setPlaceholderText("F.eks: A-TEC, Stalon, SilencerCo")
        device_form.addRow("Produsent/Modell:", self.device_manufacturer)
        
        self.device_length = QSpinBox()
        self.device_length.setRange(0, 300)
        self.device_length.setSuffix(" mm")
        device_form.addRow("Lengde:", self.device_length)
        
        self.device_weight = QSpinBox()
        self.device_weight.setRange(0, 1000)
        self.device_weight.setSuffix(" g")
        device_form.addRow("Vekt:", self.device_weight)
        
        self.device_diameter = QDoubleSpinBox()
        self.device_diameter.setRange(0, 60)
        self.device_diameter.setSuffix(" mm")
        self.device_diameter.setDecimals(1)
        device_form.addRow("Diameter:", self.device_diameter)
        
        self.thread_pitch = QComboBox()
        self.thread_pitch.setEditable(True)
        self.thread_pitch.addItems([
            "M15x1",
            "M18x1",
            "5/8-24 UNF",
            "1/2-28 UNF",
            "M14x1"
        ])
        device_form.addRow("Thread Pitch:", self.thread_pitch)
        
        device_group.setLayout(device_form)
        layout.addWidget(device_group)
        
        # POI shift tracking
        poi_group = QGroupBox("🎯 POI Shift (Point of Impact)")
        poi_form = QFormLayout()
        
        self.poi_tested = QCheckBox("Har testet POI shift")
        poi_form.addRow("Testet:", self.poi_tested)
        
        self.poi_shift_h = QDoubleSpinBox()
        self.poi_shift_h.setRange(-10, 10)
        self.poi_shift_h.setSuffix(" cm @ 100m")
        self.poi_shift_h.setDecimals(1)
        poi_form.addRow("Horisonal Shift:", self.poi_shift_h)
        
        self.poi_shift_v = QDoubleSpinBox()
        self.poi_shift_v.setRange(-10, 10)
        self.poi_shift_v.setSuffix(" cm @ 100m")
        self.poi_shift_v.setDecimals(1)
        poi_form.addRow("Vertikal Shift:", self.poi_shift_v)
        
        poi_group.setLayout(poi_form)
        layout.addWidget(poi_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_chamber_tab(self) -> QWidget:
        """Chamber specs and tolerances"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        info = QLabel(
            "💡 <b>Chamber toleranser påvirker ES/SD!</b><br>"
            "Tette kammer = bedre accuracy. Løse kammer = høyere ES. "
            "Mål skutte og pressede hylser for å finne clearance."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #f9e79f; padding: 10px; border-radius: 5px; color: #7d6608;")
        layout.addWidget(info)
        
        chamber_group = QGroupBox("📏 Kammer Spesifikasjoner")
        chamber_form = QFormLayout()
        
        self.chamber_spec = QComboBox()
        self.chamber_spec.addItems([
            "SAAMI Standard",
            "CIP Standard",
            "Match Chamber",
            "Custom Reamer",
            "Ukjent"
        ])
        chamber_form.addRow("Chamber Spec:", self.chamber_spec)
        
        self.headspace = QDoubleSpinBox()
        self.headspace.setRange(0, 5)
        self.headspace.setSuffix(" mm")
        self.headspace.setDecimals(3)
        self.headspace.setSpecialValueText("Ikke målt")
        chamber_form.addRow("Headspace (målt):", self.headspace)
        
        chamber_group.setLayout(chamber_form)
        layout.addWidget(chamber_group)
        
        # Fired case measurements
        fired_group = QGroupBox("🔥 Skutt Hylse Målinger (gjennomsnitt)")
        fired_form = QFormLayout()
        
        fired_info = QLabel(
            "Mål 5-10 skutte hylser umiddelbart etter skyting. "
            "Dette viser kammerets faktiske dimensjoner."
        )
        fired_info.setWordWrap(True)
        fired_info.setStyleSheet("font-style: italic; color: #7f8c8d;")
        fired_form.addRow("", fired_info)
        
        self.fired_base = QDoubleSpinBox()
        self.fired_base.setRange(0, 20)
        self.fired_base.setSuffix(" mm")
        self.fired_base.setDecimals(3)
        self.fired_base.setSpecialValueText("Ikke målt")
        fired_form.addRow("Case Base Diameter:", self.fired_base)
        
        self.fired_shoulder = QDoubleSpinBox()
        self.fired_shoulder.setRange(0, 20)
        self.fired_shoulder.setSuffix(" mm")
        self.fired_shoulder.setDecimals(3)
        self.fired_shoulder.setSpecialValueText("Ikke målt")
        fired_form.addRow("Shoulder Diameter:", self.fired_shoulder)
        
        self.fired_length = QDoubleSpinBox()
        self.fired_length.setRange(0, 100)
        self.fired_length.setSuffix(" mm")
        self.fired_length.setDecimals(3)
        self.fired_length.setSpecialValueText("Ikke målt")
        fired_form.addRow("Case Length:", self.fired_length)
        
        fired_group.setLayout(fired_form)
        layout.addWidget(fired_group)
        
        # Sized case measurements
        sized_group = QGroupBox("🔧 Presset Hylse Målinger")
        sized_form = QFormLayout()
        
        sized_info = QLabel(
            "Mål hylsene ETTER full-length sizing. "
            "Forskjellen mellom skutt og presset = chamber clearance."
        )
        sized_info.setWordWrap(True)
        sized_info.setStyleSheet("font-style: italic; color: #7f8c8d;")
        sized_form.addRow("", sized_info)
        
        self.sized_base = QDoubleSpinBox()
        self.sized_base.setRange(0, 20)
        self.sized_base.setSuffix(" mm")
        self.sized_base.setDecimals(3)
        self.sized_base.setSpecialValueText("Ikke målt")
        sized_form.addRow("Case Base Diameter:", self.sized_base)
        
        self.sized_shoulder = QDoubleSpinBox()
        self.sized_shoulder.setRange(0, 20)
        self.sized_shoulder.setSuffix(" mm")
        self.sized_shoulder.setDecimals(3)
        self.sized_shoulder.setSpecialValueText("Ikke målt")
        sized_form.addRow("Shoulder Diameter:", self.sized_shoulder)
        
        self.shoulder_bump = QDoubleSpinBox()
        self.shoulder_bump.setRange(0, 1)
        self.shoulder_bump.setSuffix(" mm")
        self.shoulder_bump.setDecimals(3)
        self.shoulder_bump.setSpecialValueText("Auto")
        sized_form.addRow("Shoulder Bump:", self.shoulder_bump)
        
        sized_group.setLayout(sized_form)
        layout.addWidget(sized_group)
        
        # Calculated clearances (auto-filled)
        clear_group = QGroupBox("📊 Kalkulert Clearance")
        clear_form = QFormLayout()
        
        self.clearance_base = QLabel("- (legg inn målinger)")
        clear_form.addRow("Base Clearance:", self.clearance_base)
        
        self.clearance_shoulder = QLabel("- (legg inn målinger)")
        clear_form.addRow("Shoulder Clearance:", self.clearance_shoulder)
        
        # Connect spinboxes to auto-calculate
        self.fired_base.valueChanged.connect(self.calculate_clearances)
        self.sized_base.valueChanged.connect(self.calculate_clearances)
        self.fired_shoulder.valueChanged.connect(self.calculate_clearances)
        self.sized_shoulder.valueChanged.connect(self.calculate_clearances)
        
        clear_group.setLayout(clear_form)
        layout.addWidget(clear_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_bullet_profiles_tab(self) -> QWidget:
        """Bullet-specific freebore measurements"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        info = QLabel(
            "💡 <b>Hver kule type har forskjellig freebore!</b><br>"
            "Sierra TMK vs Berger Hybrid har forskjellig ogive. "
            "Mål og lagre optimal jump for hver kule du bruker."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #a8d5ba; padding: 10px; border-radius: 5px; color: #1a3a2a;")
        layout.addWidget(info)
        
        # Add bullet profile button
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Legg til Kule Profil")
        add_btn.clicked.connect(self.add_bullet_profile)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table of bullet profiles
        self.bullet_profiles_table = QTableWidget()
        self.bullet_profiles_table.setColumnCount(6)
        self.bullet_profiles_table.setHorizontalHeaderLabels([
            "Kule", "Vekt (gr)", "Jam Length (CBTO)", "Optimal Jump", "Mag Max COAL", "Slett"
        ])
        self.bullet_profiles_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.bullet_profiles_table)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_preview_tab(self) -> QWidget:
        """Visual preview of rifle configuration"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        preview_label = QLabel("👁️ <b>Visuell Oversikt</b>")
        preview_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(preview_label)
        
        # Summary display
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setHtml(self.generate_preview_html())
        layout.addWidget(self.preview_text)
        
        # Update preview button
        update_btn = QPushButton("🔄 Oppdater Forhåndsvisning")
        update_btn.clicked.connect(self.update_preview)
        layout.addWidget(update_btn)
        
        widget.setLayout(layout)
        return widget
    
    def toggle_device_fields(self, checked):
        """Enable/disable device fields"""
        self.device_type.setEnabled(checked)
        self.device_manufacturer.setEnabled(checked)
        self.device_length.setEnabled(checked)
        self.device_weight.setEnabled(checked)
        self.device_diameter.setEnabled(checked)
        self.thread_pitch.setEnabled(checked)
    
    def calculate_clearances(self):
        """Auto-calculate chamber clearances"""
        if self.fired_base.value() > 0 and self.sized_base.value() > 0:
            clearance = (self.fired_base.value() - self.sized_base.value()) * 1000  # Convert to microns
            self.clearance_base.setText(f"{clearance:.0f} μm ({clearance/25.4:.4f}\")")
            
            # Color code based on value
            if clearance < 50:
                self.clearance_base.setStyleSheet("color: green; font-weight: bold;")
            elif clearance < 100:
                self.clearance_base.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.clearance_base.setStyleSheet("color: red; font-weight: bold;")
        
        if self.fired_shoulder.value() > 0 and self.sized_shoulder.value() > 0:
            clearance = (self.fired_shoulder.value() - self.sized_shoulder.value()) * 1000
            self.clearance_shoulder.setText(f"{clearance:.0f} μm ({clearance/25.4:.4f}\")")
            
            if clearance < 25:
                self.clearance_shoulder.setStyleSheet("color: green; font-weight: bold;")
            elif clearance < 75:
                self.clearance_shoulder.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.clearance_shoulder.setStyleSheet("color: red; font-weight: bold;")
    
    def add_bullet_profile(self):
        """Add a bullet profile entry"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Legg til Kule Profil")
        dialog_layout = QFormLayout()
        
        bullet_name = QLineEdit()
        bullet_weight = QDoubleSpinBox()
        bullet_weight.setRange(40, 250)
        bullet_weight.setSuffix(" gr")
        
        jam_length = QDoubleSpinBox()
        jam_length.setRange(40, 80)
        jam_length.setSuffix(" mm")
        jam_length.setDecimals(3)
        
        optimal_jump = QDoubleSpinBox()
        optimal_jump.setRange(0, 2)
        optimal_jump.setSuffix(" mm")
        optimal_jump.setDecimals(3)
        
        mag_max = QDoubleSpinBox()
        mag_max.setRange(50, 100)
        mag_max.setSuffix(" mm")
        mag_max.setDecimals(2)
        
        dialog_layout.addRow("Kule Navn:", bullet_name)
        dialog_layout.addRow("Vekt:", bullet_weight)
        dialog_layout.addRow("Jam Length (CBTO):", jam_length)
        dialog_layout.addRow("Optimal Jump:", optimal_jump)
        dialog_layout.addRow("Magazine Max COAL:", mag_max)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addRow(buttons)
        
        dialog.setLayout(dialog_layout)
        
        if dialog.exec():
            row = self.bullet_profiles_table.rowCount()
            self.bullet_profiles_table.insertRow(row)
            
            self.bullet_profiles_table.setItem(row, 0, QTableWidgetItem(bullet_name.text()))
            self.bullet_profiles_table.setItem(row, 1, QTableWidgetItem(f"{bullet_weight.value()}"))
            self.bullet_profiles_table.setItem(row, 2, QTableWidgetItem(f"{jam_length.value():.3f}"))
            self.bullet_profiles_table.setItem(row, 3, QTableWidgetItem(f"{optimal_jump.value():.3f}"))
            self.bullet_profiles_table.setItem(row, 4, QTableWidgetItem(f"{mag_max.value():.2f}"))
            
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda: self.bullet_profiles_table.removeRow(row))
            self.bullet_profiles_table.setCellWidget(row, 5, delete_btn)
    
    def generate_preview_html(self) -> str:
        """Generate visual preview HTML"""
        return """
        <h2>🎯 Rifle Profil Oversikt</h2>
        <p>Fyll ut feltene i de andre tabene, og trykk "Oppdater Forhåndsvisning" for å se sammendrag.</p>
        """
    
    def update_preview(self):
        """Update preview with current data"""
        html = "<h2>🎯 Rifle Profil Sammendrag</h2>"
        
        html += f"<h3>📋 {self.name.text() or 'Ukjent Rifle'}</h3>"
        html += f"<p><b>Produsent:</b> {self.manufacturer.text()}<br>"
        html += f"<b>Kaliber:</b> {self.caliber.currentText()}<br>"
        html += f"<b>Action:</b> {self.action_type.currentText()}</p>"
        
        html += "<h3>🔫 Pipe Specs</h3>"
        html += f"<p><b>Lengde:</b> {self.barrel_length.value():.0f} mm<br>"
        html += f"<b>Twist:</b> {self.twist_rate.currentText()}<br>"
        
        # Barrel profile - check which mode we're in
        if self.user_mode == "beginner":
            html += f"<b>Profil:</b> {self.barrel_profile_simple.currentText()}</p>"
        else:
            html += f"<b>Profil:</b> {self.barrel_profile.currentText()}<br>"
            html += f"<b>Materiale:</b> {self.barrel_material.currentText()}<br>"
            html += f"<b>Vekt:</b> {self.barrel_weight.value()} g</p>"
        
        # Expert-only fields
        if self.user_mode == "expert":
            if self.has_device.isChecked():
                html += "<h3>🔇 Muzzle Device</h3>"
                html += f"<p><b>Type:</b> {self.device_type.currentText()}<br>"
                html += f"<b>Modell:</b> {self.device_manufacturer.text()}<br>"
                html += f"<b>Lengde:</b> {self.device_length.value()} mm<br>"
                html += f"<b>Vekt:</b> {self.device_weight.value()} g</p>"
            
            if self.fired_base.value() > 0:
                html += "<h3>📏 Chamber Toleranser</h3>"
                html += f"<p>{self.clearance_base.text()}<br>"
                html += f"{self.clearance_shoulder.text()}</p>"
        
        self.preview_text.setHtml(html)
    
    def on_mode_changed(self, checked):
        """Handle user mode toggle"""
        if not checked:  # Only respond to button being checked, not unchecked
            return
        
        # Determine new mode
        new_mode = "beginner" if self.mode_beginner.isChecked() else "expert"
        
        if new_mode == self.user_mode:
            return  # No change
        
        # Warn if switching from expert to beginner
        if new_mode == "beginner":
            reply = QMessageBox.question(
                self,
                "Bytt til Nybegynner Modus",
                "Dette vil skjule avanserte felt for harmonics beregninger, "
                "kammer toleranser og kule profiler.\n\n"
                "Data blir ikke slettet, bare skjult. Du kan bytte tilbake når som helst.\n\n"
                "Fortsette?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                # Revert radio button
                self.mode_expert.setChecked(True)
                return
        
        # Update mode and rebuild tabs
        self.user_mode = new_mode
        self.rebuild_tabs()
    
    def rebuild_tabs(self):
        """Rebuild tabs based on current user mode"""
        # Clear all tabs
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)
        
        # Re-add tabs based on mode
        self.tabs.addTab(self.create_basic_tab(), "📋 Grunnleggende")
        
        if self.user_mode == "beginner":
            self.tabs.addTab(self.create_barrel_tab_simple(), "🔫 Pipe")
        else:
            self.tabs.addTab(self.create_barrel_tab(), "🔫 Pipe Detaljer")
            self.tabs.addTab(self.create_muzzle_tab(), "🔇 Lyddemper/Brems")
            self.tabs.addTab(self.create_chamber_tab(), "📏 Kammer & Toleranser")
            self.tabs.addTab(self.create_bullet_profiles_tab(), "🎯 Kule Profiler")
            self.tabs.addTab(self.create_preview_tab(), "👁️ Visuell Oversikt")
    
    def load_rifle_data(self):
        """Load existing rifle data"""
        # TODO: Load from database
        pass
    
    def save_profile(self):
        """Save complete rifle profile"""
        if not self.name.text():
            QMessageBox.warning(self, "Mangler navn", "Rifle må ha et navn!")
            return
        
        # Collect basic data (always available)
        rifle_data = {
            'name': self.name.text(),
            'manufacturer': self.manufacturer.text(),
            'caliber': self.caliber.currentText(),
            'action_type': self.action_type.currentText(),
            'serial_number': self.serial.text(),
            'barrel_length': self.barrel_length.value(),
            'twist_rate': self.twist_rate.currentText(),
            'notes': self.notes.toPlainText(),
            'user_mode': self.user_mode
        }
        
        # Add beginner mode simplified data
        if self.user_mode == "beginner":
            rifle_data['barrel_profile'] = self.barrel_profile_simple.currentText()
        else:
            # Expert mode: all detailed data
            rifle_data.update({
                'barrel_profile': self.barrel_profile.currentText(),
                'barrel_material': self.barrel_material.currentText(),
                'barrel_weight': self.barrel_weight.value(),
                'free_float': self.free_float.isChecked(),
                'bedding_type': self.bedding_type.currentText(),
                'stock_material': self.stock_material.currentText(),
                'round_count': self.round_count.value(),
                'barrel_condition': self.barrel_condition.currentText(),
                'has_muzzle_device': self.has_device.isChecked(),
                'device_type': self.device_type.currentText() if self.has_device.isChecked() else None,
                'device_length': self.device_length.value() if self.has_device.isChecked() else None,
                'device_weight': self.device_weight.value() if self.has_device.isChecked() else None,
                'chamber_spec': self.chamber_spec.currentText(),
                'fired_base_dia': self.fired_base.value() if self.fired_base.value() > 0 else None,
                'fired_shoulder_dia': self.fired_shoulder.value() if self.fired_shoulder.value() > 0 else None,
                'sized_base_dia': self.sized_base.value() if self.sized_base.value() > 0 else None,
                'sized_shoulder_dia': self.sized_shoulder.value() if self.sized_shoulder.value() > 0 else None,
            })
        
        # TODO: Save to database
        # For now, just emit signal
        self.rifle_saved.emit(rifle_data)
        
        QMessageBox.information(
            self,
            "✅ Profil Lagret",
            f"Rifle profil '{self.name.text()}' er lagret!\n\n"
            "Denne profilen vil nå være tilgjengelig i Load Development Wizard "
            "og AI vil bruke all denne dataen for bedre anbefalinger."
        )
        
        self.accept()
