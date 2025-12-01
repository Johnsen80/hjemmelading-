"""
Session Logger
Loggføring av ladeøkter og skyteøkter
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QDialog, QFormLayout, QLineEdit, QComboBox,
                            QDoubleSpinBox, QTextEdit, QMessageBox, QGroupBox,
                            QSpinBox, QTabWidget, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from src.database.database import get_database
from datetime import datetime


class SessionLogger(QWidget):
    """Widget for logging av ladeøkter og skyteøkter"""
    
    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
    
    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Tittel
        title = QLabel("📝 Loggbok")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Tab 1: Ladeøkter
        tabs.addTab(self.create_loading_tab(), "🔧 Ladeøkter")
        
        # Tab 2: Skyteøkter
        tabs.addTab(self.create_shooting_tab(), "🎯 Skyteøkter")
    
    def create_loading_tab(self):
        """Oppretter ladeøkt-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Knapper
        btn_layout = QHBoxLayout()
        new_btn = QPushButton("➕ Ny Ladeøkt")
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self.new_loading_session)
        btn_layout.addWidget(new_btn)
        
        edit_btn = QPushButton("✏️ Rediger")
        edit_btn.setMinimumHeight(40)
        edit_btn.clicked.connect(self.edit_loading_session)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_loading_session)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Tabell
        self.loading_table = QTableWidget()
        self.loading_table.setColumnCount(6)
        self.loading_table.setHorizontalHeaderLabels([
            "Dato", "Ammunisjonsprofil", "Antall", "Tid (min)", "Kostnad", "Notater"
        ])
        self.loading_table.horizontalHeader().setStretchLastSection(True)
        self.loading_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.loading_table.doubleClicked.connect(self.edit_loading_session)
        layout.addWidget(self.loading_table)
        
        self.load_loading_sessions()
        
        return widget
    
    def create_shooting_tab(self):
        """Oppretter skyteøkt-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Knapper
        btn_layout = QHBoxLayout()
        new_btn = QPushButton("➕ Ny Skyteøkt")
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self.new_shooting_session)
        btn_layout.addWidget(new_btn)
        
        edit_btn = QPushButton("✏️ Rediger")
        edit_btn.setMinimumHeight(40)
        edit_btn.clicked.connect(self.edit_shooting_session)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_shooting_session)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Tabell
        self.shooting_table = QTableWidget()
        self.shooting_table.setColumnCount(7)
        self.shooting_table.setHorizontalHeaderLabels([
            "Dato", "Ammunisjonsprofil", "Rifle", "Skudd", "Avstand", "Vær", "Notater"
        ])
        self.shooting_table.horizontalHeader().setStretchLastSection(True)
        self.shooting_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.shooting_table.doubleClicked.connect(self.edit_shooting_session)
        layout.addWidget(self.shooting_table)
        
        self.load_shooting_sessions()
        
        return widget
    
    # LADEØKTER
    
    def load_loading_sessions(self):
        """Laster ladeøkter fra database"""
        sessions = self.db.get_all("loading_sessions", "date DESC")
        self.loading_table.setRowCount(len(sessions))
        
        for i, session in enumerate(sessions):
            self.loading_table.setItem(i, 0, QTableWidgetItem(session['date']))
            
            # Hent ammunisjonsprofil navn
            ammo_name = "-"
            if session['ammo_profile_id']:
                ammo = self.db.get_by_id("ammo_profiles", session['ammo_profile_id'])
                if ammo:
                    ammo_name = ammo['name']
            self.loading_table.setItem(i, 1, QTableWidgetItem(ammo_name))
            
            self.loading_table.setItem(i, 2, QTableWidgetItem(str(session['quantity'])))
            
            time_str = f"{session['time_minutes']}" if session['time_minutes'] else "-"
            self.loading_table.setItem(i, 3, QTableWidgetItem(time_str))
            
            cost_str = f"{session['total_cost']:.2f} kr" if session['total_cost'] else "-"
            self.loading_table.setItem(i, 4, QTableWidgetItem(cost_str))
            
            notes = session['notes'][:50] if session['notes'] else ""
            self.loading_table.setItem(i, 5, QTableWidgetItem(notes))
            
            self.loading_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, session['id'])
    
    def new_loading_session(self):
        """Oppretter ny ladeøkt"""
        ammo_profiles = self.db.get_all("ammo_profiles")
        dialog = LoadingSessionDialog(self, ammo_profiles=ammo_profiles)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("loading_sessions", data)
            self.load_loading_sessions()
            QMessageBox.information(self, "Suksess", "Ladeøkt lagret!")
    
    def edit_loading_session(self):
        """Redigerer valgt ladeøkt"""
        selected = self.loading_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en ladeøkt først!")
            return
        
        session_id = self.loading_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        session = self.db.get_by_id("loading_sessions", session_id)
        ammo_profiles = self.db.get_all("ammo_profiles")
        
        dialog = LoadingSessionDialog(self, session=session, ammo_profiles=ammo_profiles)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("loading_sessions", session_id, data)
            self.load_loading_sessions()
            QMessageBox.information(self, "Suksess", "Ladeøkt oppdatert!")
    
    def delete_loading_session(self):
        """Sletter valgt ladeøkt"""
        selected = self.loading_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en ladeøkt først!")
            return
        
        reply = QMessageBox.question(self, 'Bekreft sletting',
            "Er du sikker på at du vil slette denne ladeøkten?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            session_id = self.loading_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete("loading_sessions", "id = ?", (session_id,))
            self.load_loading_sessions()
            QMessageBox.information(self, "Suksess", "Ladeøkt slettet!")
    
    # SKYTEØKTER
    
    def load_shooting_sessions(self):
        """Laster skyteøkter fra database"""
        sessions = self.db.get_all("shooting_sessions", "date DESC")
        self.shooting_table.setRowCount(len(sessions))
        
        for i, session in enumerate(sessions):
            self.shooting_table.setItem(i, 0, QTableWidgetItem(session['date']))
            
            # Hent ammunisjonsprofil navn
            ammo_name = "-"
            if session['ammo_profile_id']:
                ammo = self.db.get_by_id("ammo_profiles", session['ammo_profile_id'])
                if ammo:
                    ammo_name = ammo['name']
            self.shooting_table.setItem(i, 1, QTableWidgetItem(ammo_name))
            
            # Hent rifle navn
            rifle_name = "-"
            if session['rifle_id']:
                rifle = self.db.get_by_id("rifles", session['rifle_id'])
                if rifle:
                    rifle_name = rifle['name']
            self.shooting_table.setItem(i, 2, QTableWidgetItem(rifle_name))
            
            self.shooting_table.setItem(i, 3, QTableWidgetItem(str(session['rounds_fired'])))
            
            dist = f"{session['distance_meters']}m" if session['distance_meters'] else "-"
            self.shooting_table.setItem(i, 4, QTableWidgetItem(dist))
            
            weather = f"{session['temperature']}°C" if session['temperature'] else "-"
            self.shooting_table.setItem(i, 5, QTableWidgetItem(weather))
            
            notes = session['notes'][:50] if session['notes'] else ""
            self.shooting_table.setItem(i, 6, QTableWidgetItem(notes))
            
            self.shooting_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, session['id'])
    
    def new_shooting_session(self):
        """Oppretter ny skyteøkt"""
        rifles = self.db.get_all("rifles")
        ammo_profiles = self.db.get_all("ammo_profiles")
        dialog = ShootingSessionDialog(self, rifles=rifles, ammo_profiles=ammo_profiles)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("shooting_sessions", data)
            self.load_shooting_sessions()
            QMessageBox.information(self, "Suksess", "Skyteøkt lagret!")
    
    def edit_shooting_session(self):
        """Redigerer valgt skyteøkt"""
        selected = self.shooting_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en skyteøkt først!")
            return
        
        session_id = self.shooting_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        session = self.db.get_by_id("shooting_sessions", session_id)
        rifles = self.db.get_all("rifles")
        ammo_profiles = self.db.get_all("ammo_profiles")
        
        dialog = ShootingSessionDialog(self, session=session, rifles=rifles, 
                                      ammo_profiles=ammo_profiles)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("shooting_sessions", session_id, data)
            self.load_shooting_sessions()
            QMessageBox.information(self, "Suksess", "Skyteøkt oppdatert!")
    
    def delete_shooting_session(self):
        """Sletter valgt skyteøkt"""
        selected = self.shooting_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en skyteøkt først!")
            return
        
        reply = QMessageBox.question(self, 'Bekreft sletting',
            "Er du sikker på at du vil slette denne skyteøkten?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            session_id = self.shooting_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete("shooting_sessions", "id = ?", (session_id,))
            self.load_shooting_sessions()
            QMessageBox.information(self, "Suksess", "Skyteøkt slettet!")


class LoadingSessionDialog(QDialog):
    """Dialog for ladeøkt"""
    
    def __init__(self, parent=None, session=None, ammo_profiles=None):
        super().__init__(parent)
        self.session = session
        self.ammo_profiles = ammo_profiles or []
        self.init_ui()
        
        if session:
            self.load_session_data()
    
    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle("Ladeøkt")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form = QFormLayout()
        
        # Dato
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        self.date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Dato:", self.date)
        
        # Ammunisjonsprofil
        self.ammo_combo = QComboBox()
        self.ammo_combo.addItem("-- Velg ammunisjonsprofil --", None)
        for ammo in self.ammo_profiles:
            self.ammo_combo.addItem(ammo['name'], ammo['id'])
        form.addRow("Ammunisjonsprofil:", self.ammo_combo)
        
        # Antall
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 10000)
        self.quantity.setValue(50)
        self.quantity.setSuffix(" stk")
        form.addRow("Antall ladet:", self.quantity)
        
        # COAL min/max
        coal_group = QGroupBox("COAL Spredning")
        coal_layout = QFormLayout()
        coal_group.setLayout(coal_layout)
        
        self.coal_min = QDoubleSpinBox()
        self.coal_min.setRange(0, 100)
        self.coal_min.setDecimals(2)
        self.coal_min.setSuffix(" mm")
        coal_layout.addRow("COAL Min:", self.coal_min)
        
        self.coal_max = QDoubleSpinBox()
        self.coal_max.setRange(0, 100)
        self.coal_max.setDecimals(2)
        self.coal_max.setSuffix(" mm")
        coal_layout.addRow("COAL Max:", self.coal_max)
        
        layout.addLayout(form)
        layout.addWidget(coal_group)
        
        # Krutt min/max
        powder_group = QGroupBox("Kruttvekt Spredning")
        powder_layout = QFormLayout()
        powder_group.setLayout(powder_layout)
        
        self.powder_min = QDoubleSpinBox()
        self.powder_min.setRange(0, 100)
        self.powder_min.setDecimals(2)
        self.powder_min.setSuffix(" gr")
        powder_layout.addRow("Krutt Min:", self.powder_min)
        
        self.powder_max = QDoubleSpinBox()
        self.powder_max.setRange(0, 100)
        self.powder_max.setDecimals(2)
        self.powder_max.setSuffix(" gr")
        powder_layout.addRow("Krutt Max:", self.powder_max)
        
        layout.addWidget(powder_group)
        
        # Annen info
        form2 = QFormLayout()
        
        self.time_minutes = QSpinBox()
        self.time_minutes.setRange(0, 600)
        self.time_minutes.setSuffix(" min")
        form2.addRow("Tid brukt:", self.time_minutes)
        
        self.total_cost = QDoubleSpinBox()
        self.total_cost.setRange(0, 100000)
        self.total_cost.setDecimals(2)
        self.total_cost.setSuffix(" kr")
        form2.addRow("Total kostnad:", self.total_cost)
        
        layout.addLayout(form2)
        
        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText("Notater om ladeøkten...")
        layout.addWidget(QLabel("Notater:"))
        layout.addWidget(self.notes)
        
        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def load_session_data(self):
        """Laster eksisterende session data"""
        self.date.setDate(QDate.fromString(self.session['date'], "yyyy-MM-dd"))
        
        # Sett ammunisjonsprofil
        for i in range(self.ammo_combo.count()):
            if self.ammo_combo.itemData(i) == self.session['ammo_profile_id']:
                self.ammo_combo.setCurrentIndex(i)
                break
        
        self.quantity.setValue(self.session['quantity'])
        
        if self.session['coal_min']:
            self.coal_min.setValue(self.session['coal_min'])
        if self.session['coal_max']:
            self.coal_max.setValue(self.session['coal_max'])
        if self.session['powder_weight_min']:
            self.powder_min.setValue(self.session['powder_weight_min'])
        if self.session['powder_weight_max']:
            self.powder_max.setValue(self.session['powder_weight_max'])
        if self.session['time_minutes']:
            self.time_minutes.setValue(self.session['time_minutes'])
        if self.session['total_cost']:
            self.total_cost.setValue(self.session['total_cost'])
        if self.session['notes']:
            self.notes.setPlainText(self.session['notes'])
    
    def get_data(self):
        """Returnerer session data"""
        return {
            'date': self.date.date().toString("yyyy-MM-dd"),
            'ammo_profile_id': self.ammo_combo.currentData(),
            'quantity': self.quantity.value(),
            'coal_min': self.coal_min.value() if self.coal_min.value() > 0 else None,
            'coal_max': self.coal_max.value() if self.coal_max.value() > 0 else None,
            'powder_weight_min': self.powder_min.value() if self.powder_min.value() > 0 else None,
            'powder_weight_max': self.powder_max.value() if self.powder_max.value() > 0 else None,
            'time_minutes': self.time_minutes.value() if self.time_minutes.value() > 0 else None,
            'total_cost': self.total_cost.value() if self.total_cost.value() > 0 else None,
            'notes': self.notes.toPlainText()
        }


class ShootingSessionDialog(QDialog):
    """Dialog for skyteøkt"""
    
    def __init__(self, parent=None, session=None, rifles=None, ammo_profiles=None):
        super().__init__(parent)
        self.session = session
        self.rifles = rifles or []
        self.ammo_profiles = ammo_profiles or []
        self.init_ui()
        
        if session:
            self.load_session_data()
    
    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle("Skyteøkt")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form = QFormLayout()
        
        # Dato
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        self.date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Dato:", self.date)
        
        # Rifle
        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem("-- Velg rifle --", None)
        for rifle in self.rifles:
            self.rifle_combo.addItem(f"{rifle['name']} ({rifle['caliber']})", rifle['id'])
        form.addRow("Rifle:", self.rifle_combo)
        
        # Ammunisjonsprofil
        self.ammo_combo = QComboBox()
        self.ammo_combo.addItem("-- Velg ammunisjonsprofil --", None)
        for ammo in self.ammo_profiles:
            self.ammo_combo.addItem(ammo['name'], ammo['id'])
        form.addRow("Ammunisjonsprofil:", self.ammo_combo)
        
        # Skudd avfyrt
        self.rounds_fired = QSpinBox()
        self.rounds_fired.setRange(1, 1000)
        self.rounds_fired.setValue(20)
        self.rounds_fired.setSuffix(" skudd")
        form.addRow("Skudd avfyrt:", self.rounds_fired)
        
        # Avstand
        self.distance = QSpinBox()
        self.distance.setRange(25, 1500)
        self.distance.setValue(100)
        self.distance.setSuffix(" m")
        form.addRow("Avstand:", self.distance)
        
        layout.addLayout(form)
        
        # Værforhold
        weather_group = QGroupBox("Værforhold")
        weather_layout = QFormLayout()
        weather_group.setLayout(weather_layout)
        
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(-30, 50)
        self.temperature.setValue(15)
        self.temperature.setSuffix(" °C")
        weather_layout.addRow("Temperatur:", self.temperature)
        
        self.wind_speed = QSpinBox()
        self.wind_speed.setRange(0, 50)
        self.wind_speed.setSuffix(" m/s")
        weather_layout.addRow("Vind:", self.wind_speed)
        
        self.humidity = QSpinBox()
        self.humidity.setRange(0, 100)
        self.humidity.setValue(50)
        self.humidity.setSuffix(" %")
        weather_layout.addRow("Luftfuktighet:", self.humidity)
        
        layout.addWidget(weather_group)
        
        # Prestasjon
        perf_group = QGroupBox("Prestasjon")
        perf_layout = QFormLayout()
        perf_group.setLayout(perf_layout)
        
        self.best_group = QDoubleSpinBox()
        self.best_group.setRange(0, 500)
        self.best_group.setDecimals(1)
        self.best_group.setSuffix(" mm")
        perf_layout.addRow("Beste gruppe:", self.best_group)
        
        self.avg_group = QDoubleSpinBox()
        self.avg_group.setRange(0, 500)
        self.avg_group.setDecimals(1)
        self.avg_group.setSuffix(" mm")
        perf_layout.addRow("Snitt gruppe:", self.avg_group)
        
        layout.addWidget(perf_group)
        
        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText("Notater om skyteøkten...")
        layout.addWidget(QLabel("Notater:"))
        layout.addWidget(self.notes)
        
        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def load_session_data(self):
        """Laster eksisterende session data"""
        self.date.setDate(QDate.fromString(self.session['date'], "yyyy-MM-dd"))
        
        # Sett rifle
        for i in range(self.rifle_combo.count()):
            if self.rifle_combo.itemData(i) == self.session['rifle_id']:
                self.rifle_combo.setCurrentIndex(i)
                break
        
        # Sett ammunisjonsprofil
        for i in range(self.ammo_combo.count()):
            if self.ammo_combo.itemData(i) == self.session['ammo_profile_id']:
                self.ammo_combo.setCurrentIndex(i)
                break
        
        self.rounds_fired.setValue(self.session['rounds_fired'])
        
        if self.session['distance_meters']:
            self.distance.setValue(self.session['distance_meters'])
        if self.session['temperature']:
            self.temperature.setValue(self.session['temperature'])
        if self.session['wind_speed']:
            self.wind_speed.setValue(self.session['wind_speed'])
        if self.session['humidity']:
            self.humidity.setValue(self.session['humidity'])
        if self.session['best_group_mm']:
            self.best_group.setValue(self.session['best_group_mm'])
        if self.session['avg_group_mm']:
            self.avg_group.setValue(self.session['avg_group_mm'])
        if self.session['notes']:
            self.notes.setPlainText(self.session['notes'])
    
    def get_data(self):
        """Returnerer session data"""
        return {
            'date': self.date.date().toString("yyyy-MM-dd"),
            'rifle_id': self.rifle_combo.currentData(),
            'ammo_profile_id': self.ammo_combo.currentData(),
            'rounds_fired': self.rounds_fired.value(),
            'distance_meters': self.distance.value() if self.distance.value() > 0 else None,
            'temperature': self.temperature.value(),
            'wind_speed': self.wind_speed.value() if self.wind_speed.value() > 0 else None,
            'humidity': self.humidity.value(),
            'best_group_mm': self.best_group.value() if self.best_group.value() > 0 else None,
            'avg_group_mm': self.avg_group.value() if self.avg_group.value() > 0 else None,
            'notes': self.notes.toPlainText()
        }
