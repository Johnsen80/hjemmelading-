"""
Safety Dashboard - Trykksignal tracking og sikkerhet
Systematisk logging og analyse av trykkindikasjon
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QGroupBox, QTableWidget, QDialog,
                            QTableWidgetItem, QCheckBox, QDoubleSpinBox,
                            QTextEdit, QComboBox, QSpinBox, QFormLayout,
                            QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from src.database.database import get_database
from src.utils.i18n import tr
from datetime import datetime


class SafetyDashboard(QWidget):
    """Widget for sikkerhet og trykkindikasjon"""
    
    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
    
    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Tittel
        title = QLabel("⚠️ Sikkerhet & Trykksignal Dashboard")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        subtitle = QLabel("Systematisk logging av trykkindikasjon for sikker ladeutvikling")
        subtitle.setStyleSheet("color: gray; font-size: 11pt;")
        layout.addWidget(subtitle)
        
        # Advarsel
        warning = QLabel("""
        <p style='background-color: #fff3cd; padding: 15px; border-left: 5px solid #ffc107; border-radius: 5px;'>
        <b>⚠️ VIKTIG:</b> Dette systemet er et verktøy for å dokumentere observasjoner.
        <b>DU</b> har alltid ansvar for å laste innenfor publiserte ladningsbøker og stoppe ved første tegn på trykk.
        </p>
        """)
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        tabs.addTab(self.create_overview_tab(), "📊 Oversikt")
        tabs.addTab(self.create_log_tab(), "📝 Logg Trykksignal")
        tabs.addTab(self.create_history_tab(), "📜 Historikk")
        tabs.addTab(self.create_analysis_tab(), "🔍 Analyse")
    
    def create_overview_tab(self):
        """Oppretter oversiktsfane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Status-kort
        cards_layout = QHBoxLayout()
        layout.addLayout(cards_layout)
        
        self.safe_loads_card = self.create_status_card("✅ Trygge ladninger", "0", "#d4edda")
        cards_layout.addWidget(self.safe_loads_card)
        
        self.moderate_card = self.create_status_card("⚠️ Moderat trykk", "0", "#fff3cd")
        cards_layout.addWidget(self.moderate_card)
        
        self.high_card = self.create_status_card("🔴 Høyt trykk", "0", "#f8d7da")
        cards_layout.addWidget(self.high_card)
        
        self.critical_card = self.create_status_card("🚨 KRITISK", "0", "#dc3545")
        self.critical_card.setStyleSheet(self.critical_card.styleSheet() + "color: white;")
        cards_layout.addWidget(self.critical_card)
        
        # Siste varsler
        alerts_group = QGroupBox("🚨 Siste trykkvarsler")
        alerts_layout = QVBoxLayout()
        alerts_group.setLayout(alerts_layout)
        
        self.recent_alerts_table = QTableWidget()
        self.recent_alerts_table.setColumnCount(5)
        self.recent_alerts_table.setHorizontalHeaderLabels([
            "Dato", "Ammunisjon", "Ladning", "Alvorlighet", "Signaler"
        ])
        self.recent_alerts_table.setMaximumHeight(250)
        alerts_layout.addWidget(self.recent_alerts_table)
        
        layout.addWidget(alerts_group)
        
        # Quick reference guide
        guide_group = QGroupBox("📚 Trykksignal-guide")
        guide_layout = QVBoxLayout()
        guide_group.setLayout(guide_layout)
        
        guide_text = QLabel("""
        <table style='width: 100%; border-collapse: collapse;'>
        <tr style='background-color: #f0f0f0;'>
            <th style='padding: 5px; text-align: left;'>Signal</th>
            <th style='padding: 5px; text-align: left;'>Beskrivelse</th>
            <th style='padding: 5px; text-align: left;'>Handling</th>
        </tr>
        <tr>
            <td style='padding: 5px;'><b>Flat Primer</b></td>
            <td style='padding: 5px;'>Tennhette flatet ut, mister avrunding</td>
            <td style='padding: 5px;'>⚠️ Moderat trykk - vær forsiktig</td>
        </tr>
        <tr style='background-color: #f9f9f9;'>
            <td style='padding: 5px;'><b>Primer Crater</b></td>
            <td style='padding: 5px;'>Fordypning fra slagstift i tennhette</td>
            <td style='padding: 5px;'>🔴 Høyt trykk - reduser ladning</td>
        </tr>
        <tr>
            <td style='padding: 5px;'><b>Ejector Mark</b></td>
            <td style='padding: 5px;'>Merke fra utkastefjær på hylsebunn</td>
            <td style='padding: 5px;'>🔴 Høyt trykk - reduser ladning</td>
        </tr>
        <tr style='background-color: #f9f9f9;'>
            <td style='padding: 5px;'><b>Heavy Bolt Lift</b></td>
            <td style='padding: 5px;'>Tungt å åpne sluttstykke</td>
            <td style='padding: 5px;'>🚨 STOPP - For høyt trykk!</td>
        </tr>
        <tr>
            <td style='padding: 5px;'><b>Case Head Expansion</b></td>
            <td style='padding: 5px;'>Hylsebunn utvider seg (måles med kaliber)</td>
            <td style='padding: 5px;'>🚨 STOPP - Farlig trykk!</td>
        </tr>
        </table>
        """)
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text)
        
        layout.addWidget(guide_group)
        
        # Last inn data
        self.refresh_overview()
        
        return widget
    
    def create_log_tab(self):
        """Oppretter logg-fane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        info = QLabel("""
        <h3>Logg trykksignaler under testing</h3>
        <p>Dokumenter alle observasjoner for å bygge en sikker database over hva som fungerer for DIN rifle.</p>
        """)
        layout.addWidget(info)
        
        # Knapper
        btn_layout = QHBoxLayout()
        
        new_btn = QPushButton("➕ Logg ny observasjon")
        new_btn.setMinimumHeight(50)
        new_btn.clicked.connect(self.log_pressure_sign)
        btn_layout.addWidget(new_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Tabell over siste observasjoner
        table_group = QGroupBox("Siste observasjoner")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels([
            "Dato", "Ammunisjon", "Ladning", "Score", "Alvorlighet", "Notater"
        ])
        table_layout.addWidget(self.log_table)
        
        layout.addWidget(table_group)
        
        self.refresh_log_table()
        
        return widget
    
    def create_history_tab(self):
        """Oppretter historikk-fane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Filter
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Ammunisjon:"))
        self.history_ammo_filter = QComboBox()
        self.history_ammo_filter.addItem("Alle", None)
        self.load_ammo_profiles_to_filter()
        self.history_ammo_filter.currentIndexChanged.connect(self.refresh_history)
        filter_layout.addWidget(self.history_ammo_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Historikk-tabell
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Dato", "Ammunisjon", "Ladning (gr)", "Flat Primer",
            "Crater", "Ejector", "Heavy Bolt", "Score"
        ])
        layout.addWidget(self.history_table)
        
        self.refresh_history()
        
        return widget
    
    def create_analysis_tab(self):
        """Oppretter analysefane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        info = QLabel("""
        <h3>Analyse av trykk-terskler</h3>
        <p>Basert på loggede data, finn sikre maksladninger for dine ammunisjoner.</p>
        """)
        layout.addWidget(info)
        
        # Analyse-resultater
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        self.analysis_results.setMinimumHeight(400)
        layout.addWidget(self.analysis_results)
        
        # Analyser-knapp
        analyze_btn = QPushButton("🔍 Kjør analyse")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.run_analysis)
        layout.addWidget(analyze_btn)
        
        return widget
    
    def create_status_card(self, title, value, color):
        """Oppretter status-kort"""
        card = QGroupBox()
        card.setMinimumHeight(100)
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: {color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        card_layout = QVBoxLayout()
        card.setLayout(card_layout)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)
        
        card.value_label = value_label
        
        return card
    
    def load_ammo_profiles_to_filter(self):
        """Laster ammunisjonsprofiler"""
        ammos = self.db.execute_query("SELECT id, name FROM ammo_profiles ORDER BY name")
        for ammo_id, name in ammos:
            self.history_ammo_filter.addItem(name, ammo_id)
    
    def log_pressure_sign(self):
        """Åpner dialog for å logge trykksignal"""
        dialog = PressureSignDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.save_pressure_sign(data)
            self.refresh_overview()
            self.refresh_log_table()
            self.refresh_history()
    
    def save_pressure_sign(self, data):
        """Lagrer trykksignal til database"""
        # Beregn pressure score
        score = 0
        if data['flat_primer']:
            score += 2
        if data['primer_crater']:
            score += 3
        if data['ejector_mark']:
            score += 3
        if data['extractor_mark']:
            score += 2
        if data['heavy_bolt_lift']:
            score += 5
        if data['velocity_spike']:
            score += 2
        
        # Bestem alvorlighet
        if score >= 8:
            severity = "KRITISK"
        elif score >= 5:
            severity = "HØY"
        elif score >= 3:
            severity = "MODERAT"
        else:
            severity = "LAV"
        
        query = """
            INSERT INTO pressure_signs (
                ammo_profile_id, charge_weight, flat_primer, primer_crater,
                ejector_mark, extractor_mark, heavy_bolt_lift, case_head_expansion,
                velocity_spike, pressure_score, severity_level, notes, date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            data['ammo_id'],
            data['charge_weight'],
            1 if data['flat_primer'] else 0,
            1 if data['primer_crater'] else 0,
            1 if data['ejector_mark'] else 0,
            1 if data['extractor_mark'] else 0,
            1 if data['heavy_bolt_lift'] else 0,
            data.get('case_head_expansion'),
            1 if data['velocity_spike'] else 0,
            score,
            severity,
            data['notes'],
            datetime.now().strftime("%Y-%m-%d")
        )
        
        self.db.execute_update(query, params)
        
        QMessageBox.information(
            self, "Lagret",
            f"Trykksignal lagret!\n\nScore: {score}\nAlvorlighet: {severity}"
        )
    
    def refresh_overview(self):
        """Oppdaterer oversikt"""
        # Tell opp etter alvorlighet
        safe_result = self.db.execute_query(
            "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'LAV'"
        )
        safe = safe_result[0] if safe_result and len(safe_result) > 0 else [0]
        safe = safe[0] if isinstance(safe, (list, tuple)) else safe
        
        moderate_result = self.db.execute_query(
            "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'MODERAT'"
        )
        moderate = moderate_result[0] if moderate_result and len(moderate_result) > 0 else [0]
        moderate = moderate[0] if isinstance(moderate, (list, tuple)) else moderate
        
        high_result = self.db.execute_query(
            "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'HØY'"
        )
        high = high_result[0] if high_result and len(high_result) > 0 else [0]
        high = high[0] if isinstance(high, (list, tuple)) else high
        
        critical_result = self.db.execute_query(
            "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'KRITISK'"
        )
        critical = critical_result[0] if critical_result and len(critical_result) > 0 else [0]
        critical = critical[0] if isinstance(critical, (list, tuple)) else critical
        
        self.safe_loads_card.value_label.setText(str(safe))
        self.moderate_card.value_label.setText(str(moderate))
        self.high_card.value_label.setText(str(high))
        self.critical_card.value_label.setText(str(critical))
        
        # Siste varsler
        recent = self.db.execute_query("""
            SELECT ps.date, ap.name, ps.charge_weight, ps.severity_level,
                   ps.flat_primer, ps.primer_crater, ps.ejector_mark, ps.heavy_bolt_lift
            FROM pressure_signs ps
            LEFT JOIN ammo_profiles ap ON ps.ammo_profile_id = ap.id
            WHERE ps.severity_level IN ('HØY', 'KRITISK')
            ORDER BY ps.date DESC
            LIMIT 10
        """)
        
        self.recent_alerts_table.setRowCount(len(recent))
        
        for i, row in enumerate(recent):
            date, ammo, charge, severity, flat, crater, ejector, bolt = row
            
            signals = []
            if flat: signals.append("Flat")
            if crater: signals.append("Crater")
            if ejector: signals.append("Ejector")
            if bolt: signals.append("Heavy Bolt")
            
            self.recent_alerts_table.setItem(i, 0, QTableWidgetItem(date))
            self.recent_alerts_table.setItem(i, 1, QTableWidgetItem(ammo or "N/A"))
            self.recent_alerts_table.setItem(i, 2, QTableWidgetItem(f"{charge:.1f} gr"))
            self.recent_alerts_table.setItem(i, 3, QTableWidgetItem(severity))
            self.recent_alerts_table.setItem(i, 4, QTableWidgetItem(", ".join(signals)))
            
            # Fargelegg
            color = QColor(220, 53, 69, 100) if severity == "KRITISK" else QColor(255, 193, 7, 100)
            for col in range(5):
                self.recent_alerts_table.item(i, col).setBackground(color)
    
    def refresh_log_table(self):
        """Oppdaterer logg-tabell"""
        logs = self.db.execute_query("""
            SELECT ps.date, ap.name, ps.charge_weight, ps.pressure_score,
                   ps.severity_level, ps.notes
            FROM pressure_signs ps
            LEFT JOIN ammo_profiles ap ON ps.ammo_profile_id = ap.id
            ORDER BY ps.date DESC
            LIMIT 20
        """)
        
        self.log_table.setRowCount(len(logs))
        
        for i, row in enumerate(logs):
            for j, value in enumerate(row):
                if j == 2 and value:  # Charge weight
                    self.log_table.setItem(i, j, QTableWidgetItem(f"{value:.1f} gr"))
                else:
                    self.log_table.setItem(i, j, QTableWidgetItem(str(value) if value else ""))
    
    def refresh_history(self):
        """Oppdaterer historikk"""
        ammo_id = self.history_ammo_filter.currentData()
        
        query = """
            SELECT ps.date, ap.name, ps.charge_weight, ps.flat_primer,
                   ps.primer_crater, ps.ejector_mark, ps.heavy_bolt_lift,
                   ps.pressure_score
            FROM pressure_signs ps
            LEFT JOIN ammo_profiles ap ON ps.ammo_profile_id = ap.id
        """
        
        if ammo_id:
            query += " WHERE ps.ammo_profile_id = ?"
            history = self.db.execute_query(query + " ORDER BY ps.charge_weight", (ammo_id,))
        else:
            history = self.db.execute_query(query + " ORDER BY ps.date DESC")
        
        self.history_table.setRowCount(len(history))
        
        for i, row in enumerate(history):
            for j, value in enumerate(row):
                if j == 2 and value:  # Charge weight
                    self.history_table.setItem(i, j, QTableWidgetItem(f"{value:.1f}"))
                elif j >= 3 and j <= 6:  # Boolean checkboxes
                    self.history_table.setItem(i, j, QTableWidgetItem("✓" if value else ""))
                else:
                    self.history_table.setItem(i, j, QTableWidgetItem(str(value) if value else ""))
    
    def run_analysis(self):
        """Kjører analyse av trykk-terskler"""
        # Grupper per ammunisjon
        ammos = self.db.execute_query("""
            SELECT DISTINCT ap.id, ap.name
            FROM pressure_signs ps
            JOIN ammo_profiles ap ON ps.ammo_profile_id = ap.id
            ORDER BY ap.name
        """)
        
        if not ammos:
            self.analysis_results.setText("Ingen data å analysere ennå. Logg noen trykksignaler først!")
            return
        
        results = "<h2>Trykk-analyse</h2>"
        
        for ammo_id, ammo_name in ammos:
            results += f"<h3>{ammo_name}</h3>"
            
            # Finn høyeste sikre ladning (score < 3)
            safe_loads = self.db.execute_query("""
                SELECT MAX(charge_weight)
                FROM pressure_signs
                WHERE ammo_profile_id = ? AND pressure_score < 3
            """, (ammo_id,))
            
            max_safe = safe_loads[0][0] if safe_loads and safe_loads[0][0] else None
            
            # Finn første tegn på trykk
            first_pressure = self.db.execute_query("""
                SELECT MIN(charge_weight)
                FROM pressure_signs
                WHERE ammo_profile_id = ? AND pressure_score >= 3
            """, (ammo_id,))
            
            first_sign = first_pressure[0][0] if first_pressure and first_pressure[0][0] else None
            
            if max_safe:
                results += f"<p><b>✅ Høyeste sikre ladning:</b> {max_safe:.1f} gr (ingen betydelige trykksignaler)</p>"
            
            if first_sign:
                results += f"<p><b>⚠️ Første trykktegn ved:</b> {first_sign:.1f} gr</p>"
                if max_safe:
                    margin = first_sign - max_safe
                    results += f"<p><b>Sikkerhetsmargin:</b> {margin:.1f} gr</p>"
            
            if not max_safe and not first_sign:
                results += "<p><i>Ikke nok data for denne ammunisjonen.</i></p>"
            
            results += "<hr>"
        
        self.analysis_results.setHtml(results)


class PressureSignDialog(QDialog):
    """Dialog for å logge trykksignal"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.setWindowTitle("Logg Trykksignal")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        """Initialiserer dialog"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Info
        info = QLabel("Dokumenter alle observerte trykksignaler:")
        layout.addWidget(info)
        
        # Form
        form = QFormLayout()
        
        # Ammunisjon
        self.ammo_combo = QComboBox()
        self.load_ammo_profiles()
        form.addRow("Ammunisjon:", self.ammo_combo)
        
        # Ladning
        self.charge_weight = QDoubleSpinBox()
        self.charge_weight.setRange(10, 100)
        self.charge_weight.setValue(40.0)
        self.charge_weight.setDecimals(1)
        self.charge_weight.setSuffix(" gr")
        form.addRow("Kruttvekt:", self.charge_weight)
        
        layout.addLayout(form)
        
        # Checkboxes for signaler
        signals_group = QGroupBox("Observerte signaler")
        signals_layout = QVBoxLayout()
        signals_group.setLayout(signals_layout)
        
        self.flat_primer = QCheckBox("Flat Primer (avrunding forsvinner)")
        signals_layout.addWidget(self.flat_primer)
        
        self.primer_crater = QCheckBox("Primer Crater (fordypning fra slagstift)")
        signals_layout.addWidget(self.primer_crater)
        
        self.ejector_mark = QCheckBox("Ejector Mark (merke fra utkastefjær)")
        signals_layout.addWidget(self.ejector_mark)
        
        self.extractor_mark = QCheckBox("Extractor Mark (merke fra uttrekker)")
        signals_layout.addWidget(self.extractor_mark)
        
        self.heavy_bolt_lift = QCheckBox("Heavy Bolt Lift (tungt å åpne sluttstykke)")
        signals_layout.addWidget(self.heavy_bolt_lift)
        
        self.velocity_spike = QCheckBox("Velocity Spike (uventet høy hastighet)")
        signals_layout.addWidget(self.velocity_spike)
        
        layout.addWidget(signals_group)
        
        # Case head expansion (optional)
        case_form = QFormLayout()
        self.case_head = QDoubleSpinBox()
        self.case_head.setRange(0, 1)
        self.case_head.setValue(0)
        self.case_head.setDecimals(4)
        self.case_head.setSuffix(" inches")
        case_form.addRow("Case Head Expansion (valgfritt):", self.case_head)
        layout.addLayout(case_form)
        
        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText("Tilleggsnotater...")
        layout.addWidget(QLabel("Notater:"))
        layout.addWidget(self.notes)
        
        # Knapper
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Lagre")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Avbryt")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def load_ammo_profiles(self):
        """Laster ammunisjonsprofiler"""
        ammos = self.db.execute_query("SELECT id, name FROM ammo_profiles ORDER BY name")
        for ammo_id, name in ammos:
            self.ammo_combo.addItem(name, ammo_id)
    
    def get_data(self):
        """Returnerer data"""
        return {
            'ammo_id': self.ammo_combo.currentData(),
            'charge_weight': self.charge_weight.value(),
            'flat_primer': self.flat_primer.isChecked(),
            'primer_crater': self.primer_crater.isChecked(),
            'ejector_mark': self.ejector_mark.isChecked(),
            'extractor_mark': self.extractor_mark.isChecked(),
            'heavy_bolt_lift': self.heavy_bolt_lift.isChecked(),
            'velocity_spike': self.velocity_spike.isChecked(),
            'case_head_expansion': self.case_head.value() if self.case_head.value() > 0 else None,
            'notes': self.notes.toPlainText()
        }
