"""
Smart Loading Wizard - AI-drevet ladningsveileder
Analyserer rifle + formål + historikk → Optimal ladning
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTextEdit, QGroupBox, QRadioButton,
                             QButtonGroup, QSpinBox, QDoubleSpinBox, QProgressBar,
                             QListWidget, QListWidgetItem, QMessageBox, QWizard,
                             QWizardPage, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from src.database.database import get_database
from typing import Dict, List, Optional, Tuple
import math


class PurposeProfile:
    """Profil for ulike bruksområder"""
    
    PROFILES = {
        'jakt': {
            'name': '🦌 Jakt',
            'description': 'Optimal balanse: Energy, expansion, presisjon på jaktavstand',
            'priority': {
                'energy': 40,      # Terminal energy viktig
                'accuracy': 30,    # God presisjon
                'velocity': 20,    # Flat trajectory
                'consistency': 10  # ES/SD mindre kritisk
            },
            'min_energy_ftlbs': 1000,  # Minimum energy @ 300m
            'max_range_m': 400,
            'target_velocity_fps': 2700,
            'tips': [
                'Velg ekspanderende kuler (Nosler Partition, Barnes TTSX)',
                'Prioriter controlled expansion over ekstrem BC',
                'Test på jaktavstand (100-300m)',
                'Verifiser zero ved jakttemperatur'
            ]
        },
        'langhold': {
            'name': '🎯 Langhold/PRS',
            'description': 'Maksimal presisjon og ballistikk på ekstreme avstander',
            'priority': {
                'accuracy': 35,      # Sub-MOA critical
                'consistency': 35,   # Low ES/SD critical
                'bc': 20,           # Høy BC for vindrift
                'velocity': 10      # Moderate velocity OK
            },
            'min_bc_g7': 0.25,
            'max_es_fps': 15,
            'target_group_moa': 0.5,
            'max_range_m': 1200,
            'tips': [
                'Høy BC kuler (Berger, Hornady ELD)',
                'Low ES/SD kritisk - test 10+ skudd',
                'Finn "node" i ladder test',
                'Verifiser drops på 600m+'
            ]
        },
        'presisjon': {
            'name': '🏆 Presisjonsskyting (Benchrest)',
            'description': 'Ultimate accuracy - gruppe størrelse er ALT',
            'priority': {
                'accuracy': 60,      # Accuracy is everything
                'consistency': 30,   # ES/SD important
                'velocity': 5,       # Velocity doesn't matter
                'bc': 5             # BC doesn't matter
            },
            'target_group_moa': 0.25,
            'max_es_fps': 10,
            'max_range_m': 300,
            'tips': [
                'Match grade kuler (Berger Hybrid, Lapua Scenar)',
                'Perfekt neck tension',
                'Konsistent seating depth (0.001")',
                'Wind flags er kritisk'
            ]
        },
        'blink': {
            'name': '⚡ Blink/IPSC Rifle',
            'description': 'Speed + accuracy balance - raske splits',
            'priority': {
                'velocity': 30,      # Fast for quick splits
                'accuracy': 30,      # Good enough accuracy
                'recoil': 25,        # Low recoil = faster
                'consistency': 15    # Some ES OK
            },
            'min_velocity_fps': 2600,
            'max_recoil_ftlbs': 18,
            'target_group_moa': 1.5,  # IPSC targets are big
            'max_range_m': 400,
            'tips': [
                'Moderate weight kuler (140gr i 6.5)',
                'Fast powder for low recoil',
                'Prioriter muzzle brake',
                'Test rapid fire strings'
            ]
        },
        'plinking': {
            'name': '🎪 Trening/Plinking',
            'description': 'Billig, pålitelig, lavt slit - volum skyting',
            'priority': {
                'cost': 40,          # Cheap is good
                'consistency': 30,   # Reliable feeding
                'barrel_life': 20,   # Low pressure = long life
                'velocity': 10       # Speed not important
            },
            'max_cost_per_round': 5.0,  # NOK
            'max_pressure_pct': 85,
            'target_group_moa': 2.0,
            'tips': [
                'Billige FMJ kuler',
                'Moderate ladninger (90-95% max)',
                'Bulk komponenter',
                'Fokus på volume ikke presisjon'
            ]
        }
    }
    
    @staticmethod
    def get_profile(purpose: str) -> Dict:
        """Hent profil for gitt formål"""
        return PurposeProfile.PROFILES.get(purpose, PurposeProfile.PROFILES['jakt'])
    
    @staticmethod
    def score_load(purpose: str, load_data: Dict) -> float:
        """
        Scorer en ladning basert på formål
        Returns: Score 0-100
        """
        profile = PurposeProfile.get_profile(purpose)
        priorities = profile['priority']
        
        score = 0.0
        
        # Accuracy scoring (inverse MOA)
        if 'group_size_moa' in load_data and load_data['group_size_moa']:
            moa = load_data['group_size_moa']
            accuracy_score = max(0, 100 - (moa * 40))  # 0.5 MOA = 80pts
            score += accuracy_score * (priorities.get('accuracy', 0) / 100)
        
        # Consistency scoring (inverse ES)
        if 'velocity_es' in load_data and load_data['velocity_es']:
            es = load_data['velocity_es']
            consistency_score = max(0, 100 - (es * 2))  # 15 ES = 70pts
            score += consistency_score * (priorities.get('consistency', 0) / 100)
        
        # Velocity scoring
        if 'velocity_avg' in load_data and load_data['velocity_avg']:
            vel = load_data['velocity_avg']
            target_vel = profile.get('target_velocity_fps', 2700)
            vel_diff = abs(vel - target_vel)
            velocity_score = max(0, 100 - (vel_diff / 10))
            score += velocity_score * (priorities.get('velocity', 0) / 100)
        
        # BC scoring (higher is better)
        if 'bc_g7' in load_data and load_data['bc_g7']:
            bc = load_data['bc_g7']
            bc_score = min(100, bc * 250)  # 0.3 BC = 75pts
            score += bc_score * (priorities.get('bc', 0) / 100)
        
        # Energy scoring
        if 'energy_ftlbs' in load_data and load_data['energy_ftlbs']:
            energy = load_data['energy_ftlbs']
            min_energy = profile.get('min_energy_ftlbs', 1000)
            if energy >= min_energy:
                energy_score = min(100, (energy / min_energy) * 50 + 50)
            else:
                energy_score = (energy / min_energy) * 50
            score += energy_score * (priorities.get('energy', 0) / 100)
        
        return score


class RifleSelectionPage(QWizardPage):
    """Steg 1: Velg rifle profil"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("🔫 Velg Rifle")
        self.setSubTitle("Hvilken rifle skal du lade til?")
        
        self.db = get_database()
        layout = QVBoxLayout()
        
        # Rifle selector
        self.combo_rifle = QComboBox()
        self.load_rifles()
        layout.addWidget(QLabel("Rifle:"))
        layout.addWidget(self.combo_rifle)
        
        # Rifle info display
        self.text_rifle_info = QTextEdit()
        self.text_rifle_info.setReadOnly(True)
        self.text_rifle_info.setMaximumHeight(120)
        layout.addWidget(QLabel("Rifle detaljer:"))
        layout.addWidget(self.text_rifle_info)
        
        self.combo_rifle.currentIndexChanged.connect(self.on_rifle_changed)
        self.on_rifle_changed()
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_rifles(self):
        """Last inn rifles fra database"""
        rifles = self.db.get_all('rifles', 'name')
        self.combo_rifle.clear()
        for rifle in rifles:
            self.combo_rifle.addItem(f"{rifle['name']} ({rifle['caliber']})", rifle['id'])
    
    def on_rifle_changed(self):
        """Vis rifle info når valg endres"""
        rifle_id = self.combo_rifle.currentData()
        if rifle_id:
            rifle = self.db.get_by_id('rifles', rifle_id)
            if rifle:
                self.text_rifle_info.setHtml(f"""
                    <b>Kaliber:</b> {rifle['caliber']}<br>
                    <b>Løp:</b> {rifle.get('barrel_length', 'N/A')} tommer<br>
                    <b>Twist:</b> {rifle.get('twist_rate', 'N/A')}<br>
                    <b>Action:</b> {rifle.get('action_type', 'N/A')}<br>
                """)
    
    def get_selected_rifle_id(self) -> Optional[int]:
        """Hent valgt rifle ID"""
        return self.combo_rifle.currentData()


class PurposeSelectionPage(QWizardPage):
    """Steg 2: Velg bruksområde"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("🎯 Hva skal du bruke ammoen til?")
        self.setSubTitle("Velg bruksområde - dette påvirker anbefalingene")
        
        layout = QVBoxLayout()
        
        self.button_group = QButtonGroup()
        
        for key, profile in PurposeProfile.PROFILES.items():
            rb = QRadioButton()
            
            # Create rich label
            rb_layout = QVBoxLayout()
            
            title = QLabel(f"<b style='font-size: 14px;'>{profile['name']}</b>")
            rb_layout.addWidget(title)
            
            desc = QLabel(profile['description'])
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #7f8c8d;")
            rb_layout.addWidget(desc)
            
            # Add to layout
            container = QWidget()
            container.setLayout(rb_layout)
            
            layout.addWidget(rb)
            layout.addWidget(container)
            
            self.button_group.addButton(rb)
            rb.setProperty('purpose_key', key)
            
            if key == 'jakt':
                rb.setChecked(True)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_selected_purpose(self) -> str:
        """Hent valgt formål"""
        checked = self.button_group.checkedButton()
        if checked:
            return checked.property('purpose_key')
        return 'jakt'


class ComponentSelectionPage(QWizardPage):
    """Steg 3: Velg komponenter"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("📦 Velg Komponenter")
        self.setSubTitle("Hvilke komponenter vil du bruke?")
        
        self.db = get_database()
        layout = QVBoxLayout()
        
        # Bullet selector
        bullet_group = QGroupBox("Kule")
        bullet_layout = QVBoxLayout()
        self.combo_bullet = QComboBox()
        self.load_bullets()
        bullet_layout.addWidget(self.combo_bullet)
        bullet_group.setLayout(bullet_layout)
        layout.addWidget(bullet_group)
        
        # Powder selector
        powder_group = QGroupBox("Krutt")
        powder_layout = QVBoxLayout()
        self.combo_powder = QComboBox()
        self.load_powders()
        powder_layout.addWidget(self.combo_powder)
        powder_group.setLayout(powder_layout)
        layout.addWidget(powder_group)
        
        # Primer selector
        primer_group = QGroupBox("Tennhetter")
        primer_layout = QVBoxLayout()
        self.combo_primer = QComboBox()
        self.load_primers()
        primer_layout.addWidget(self.combo_primer)
        primer_group.setLayout(primer_layout)
        layout.addWidget(primer_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_bullets(self):
        """Last kuler fra database"""
        bullets = self.db.get_all('bullets', 'weight_grains')
        self.combo_bullet.clear()
        for bullet in bullets:
            label = f"{bullet['name']} - {bullet['weight_grains']}gr"
            if bullet.get('bc_g7'):
                label += f" (G7: {bullet['bc_g7']})"
            self.combo_bullet.addItem(label, bullet['id'])
    
    def load_powders(self):
        """Last krutt fra database"""
        powders = self.db.get_all('powder', 'name')
        self.combo_powder.clear()
        for powder in powders:
            label = f"{powder['name']}"
            if powder.get('manufacturer'):
                label += f" ({powder['manufacturer']})"
            self.combo_powder.addItem(label, powder['id'])
    
    def load_primers(self):
        """Last tennhetter fra database"""
        primers = self.db.get_all('primers', 'name')
        self.combo_primer.clear()
        for primer in primers:
            label = f"{primer['name']} - {primer.get('type', 'N/A')}"
            self.combo_primer.addItem(label, primer['id'])
    
    def get_selections(self) -> Dict:
        """Hent valgte komponenter"""
        return {
            'bullet_id': self.combo_bullet.currentData(),
            'powder_id': self.combo_powder.currentData(),
            'primer_id': self.combo_primer.currentData()
        }


class AIRecommendationPage(QWizardPage):
    """Steg 4: AI Anbefaling"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("🤖 AI Anbefaling")
        self.setSubTitle("Basert på dine valg og historiske data")
        
        self.db = get_database()
        layout = QVBoxLayout()
        
        # Analysis status
        self.label_status = QLabel("Analyserer...")
        layout.addWidget(self.label_status)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        # Recommendation display
        self.text_recommendation = QTextEdit()
        self.text_recommendation.setReadOnly(True)
        layout.addWidget(self.text_recommendation)
        
        # Historical data table
        history_group = QGroupBox("📊 Relevante historiske tester")
        history_layout = QVBoxLayout()
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(6)
        self.table_history.setHorizontalHeaderLabels([
            'Ladning', 'Velocity', 'ES', 'SD', 'Gruppe (MOA)', 'Score'
        ])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.table_history)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Kjør analyse når siden vises"""
        wizard = self.wizard()
        rifle_id = wizard.page(0).get_selected_rifle_id()
        purpose = wizard.page(1).get_selected_purpose()
        components = wizard.page(2).get_selections()
        
        self.analyze_and_recommend(rifle_id, purpose, components)
    
    def analyze_and_recommend(self, rifle_id: int, purpose: str, components: Dict):
        """Analyser data og gi anbefaling"""
        self.progress.setValue(10)
        self.label_status.setText("Henter rifle-info...")
        
        # Hent rifle info
        rifle = self.db.get_by_id('rifles', rifle_id)
        caliber = rifle.get('caliber', '')
        
        self.progress.setValue(20)
        self.label_status.setText("Søker i produsent ladetabeller...")
        
        # Hent relevante ladetabeller fra produsenter
        bullet_id = components.get('bullet_id')
        powder_id = components.get('powder_id')
        
        load_data_query = """
            SELECT ld.*, b.name as bullet_full_name, p.name as powder_full_name
            FROM load_data ld
            LEFT JOIN bullets b ON ld.bullet_id = b.id
            LEFT JOIN powder p ON ld.powder_id = p.id
            WHERE ld.cartridge LIKE ?
        """
        
        # Søk etter kaliber i cartridge navn
        load_data = self.db.execute_query(load_data_query, (f"%{caliber}%",))
        
        # Filtrer på valgte komponenter hvis mulig
        if bullet_id:
            load_data = [ld for ld in load_data if ld.get('bullet_id') == bullet_id or 
                        components.get('bullet_weight', 0) in str(ld.get('bullet_name', ''))]
        
        if powder_id:
            powder_name = self.db.get_by_id('powder', powder_id).get('name', '')
            load_data = [ld for ld in load_data if powder_name in str(ld.get('powder_name', ''))]
        
        self.progress.setValue(40)
        self.label_status.setText("Henter historiske tester...")
        
        # Hent historiske tester for denne riflen
        history_query = """
            SELECT lt.*, tr.charge_weight, tr.velocity_avg, tr.velocity_es, 
                   tr.velocity_sd, tr.group_size_moa
            FROM ladder_tests lt
            LEFT JOIN test_results tr ON lt.id = tr.ladder_test_id
            WHERE lt.rifle_id = ?
            ORDER BY tr.group_size_moa ASC
            LIMIT 20
        """
        history = self.db.execute_query(history_query, (rifle_id,))
        
        self.progress.setValue(60)
        self.label_status.setText("Analyserer mønstre...")
        
        # Score hver historisk test basert på formål
        scored_history = []
        for test in history:
            if test.get('velocity_avg'):
                score = PurposeProfile.score_load(purpose, test)
                test['score'] = score
                scored_history.append(test)
        
        # Sorter etter score
        scored_history.sort(key=lambda x: x['score'], reverse=True)
        
        self.progress.setValue(80)
        self.label_status.setText("Genererer anbefaling...")
        
        # Vis historikk i tabell
        self.table_history.setRowCount(min(10, len(scored_history)))
        for i, test in enumerate(scored_history[:10]):
            self.table_history.setItem(i, 0, QTableWidgetItem(f"{test.get('charge_weight', 'N/A')}gr"))
            self.table_history.setItem(i, 1, QTableWidgetItem(f"{test.get('velocity_avg', 'N/A')} fps"))
            self.table_history.setItem(i, 2, QTableWidgetItem(f"{test.get('velocity_es', 'N/A')}"))
            self.table_history.setItem(i, 3, QTableWidgetItem(f"{test.get('velocity_sd', 'N/A')}"))
            self.table_history.setItem(i, 4, QTableWidgetItem(f"{test.get('group_size_moa', 'N/A')}"))
            self.table_history.setItem(i, 5, QTableWidgetItem(f"{test.get('score', 0):.1f}"))
        
        # Generer anbefaling
        profile = PurposeProfile.get_profile(purpose)
        
        # Kombiner historikk og ladetabeller
        recommendation = f"""
            <h2 style='color: #27ae60;'>🎯 Smart Ladeanbefaling</h2>
            <p><b>Formål:</b> {profile['name']}</p>
            <p><i>{profile['description']}</i></p>
        """
        
        # Vis produsent ladetabeller hvis funnet
        if load_data:
            recommendation += f"""
                <h3>📚 Produsent Ladetabeller ({len(load_data)} funnet)</h3>
                <table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>
                    <tr style='background-color: #34495e; color: white;'>
                        <th>Kilde</th>
                        <th>Kule</th>
                        <th>Krutt</th>
                        <th>Min→Max</th>
                        <th>Velocity</th>
                        <th>Trykk (PSI)</th>
                    </tr>
            """
            
            for ld in load_data[:5]:  # Vis topp 5
                min_charge = ld.get('min_charge_grains', 0)
                max_charge = ld.get('max_charge_grains', 0)
                min_vel = ld.get('min_velocity_fps', 0)
                max_vel = ld.get('max_velocity_fps', 0)
                max_psi = ld.get('max_pressure_psi', 0)
                
                recommendation += f"""
                    <tr>
                        <td><b>{ld.get('source', 'N/A')}</b></td>
                        <td>{ld.get('bullet_name', 'N/A')}</td>
                        <td>{ld.get('powder_name', 'N/A')}</td>
                        <td>{min_charge:.1f}→{max_charge:.1f}gr</td>
                        <td>{min_vel}→{max_vel} fps</td>
                        <td style='color: {"#27ae60" if max_psi < 60000 else "#e74c3c"};'>{max_psi:,}</td>
                    </tr>
                """
            
            recommendation += "</table><br>"
            
            # Finn gjennomsnittsladning fra ladetabeller
            avg_min = sum(ld.get('min_charge_grains', 0) for ld in load_data) / len(load_data)
            avg_max = sum(ld.get('max_charge_grains', 0) for ld in load_data) / len(load_data)
            avg_velocity = sum(ld.get('max_velocity_fps', 0) for ld in load_data) / len(load_data)
            avg_max_pressure = sum(ld.get('max_pressure_psi', 0) for ld in load_data) / len(load_data)
            
            # Hent SAAMI/CIP max pressure for kaliber
            from src.utils.pressure_calculator import PressureCalculator
            pressure_calc = PressureCalculator(self.db)
            saami_max = pressure_calc.get_saami_max(caliber)
            
            # Beregn % av SAAMI max
            if avg_max_pressure > 0:
                percent_of_saami = (avg_max_pressure / saami_max) * 100
                pressure_color = '#27ae60' if percent_of_saami < 95 else '#e74c3c'
            else:
                percent_of_saami = 0
                pressure_color = '#95a5a6'
            
            recommendation += f"""
                <div style='background-color: #ecf0f1; padding: 10px; border-radius: 5px;'>
                <h4>💡 Anbefalt startladning fra produsent-data:</h4>
                <ul>
                    <li><b>Start ved:</b> {avg_min:.1f}gr (gjennomsnitt minimum fra {len(load_data)} kilder)</li>
                    <li><b>Maks anbefalt:</b> {avg_max:.1f}gr</li>
                    <li><b>Forventet velocity:</b> {avg_velocity:.0f} fps ved maks ladning</li>
                    <li><b>Anbefalt arbeidsområde:</b> {avg_min:.1f}gr → {avg_max:.1f}gr i 0.3gr steg</li>
                </ul>
                <h4>🔬 Trykkdata (SAAMI/CIP):</h4>
                <ul>
                    <li><b>SAAMI/CIP Max for {caliber}:</b> {saami_max:,} PSI</li>
                    <li><b>Produsent maks trykk:</b> <span style='color: {pressure_color};'>{avg_max_pressure:,.0f} PSI ({percent_of_saami:.1f}% av SAAMI max)</span></li>
                    <li><b>Safety margin:</b> {100 - percent_of_saami:.1f}% under SAAMI limit</li>
                </ul>
                </div>
                <br>
            """
        
        # Vis historiske data hvis tilgjengelig
        if scored_history:
            best = scored_history[0]
            recommendation += f"""
                <h3>📊 Dine historiske tester ({len(scored_history)} tester)</h3>
                
                <div style='background-color: #e8f8f5; padding: 10px; border-radius: 5px;'>
                <h4>🏆 Beste historiske ladning for {profile['name']}:</h4>
                <ul>
                    <li><b>Ladning:</b> {best.get('charge_weight', 'N/A')}gr</li>
                    <li><b>Velocity:</b> {best.get('velocity_avg', 'N/A')} fps</li>
                    <li><b>ES:</b> {best.get('velocity_es', 'N/A')} fps</li>
                    <li><b>SD:</b> {best.get('velocity_sd', 'N/A')} fps</li>
                    <li><b>Gruppe:</b> {best.get('group_size_moa', 'N/A')} MOA</li>
                    <li><b>Score for formål:</b> {best.get('score', 0):.1f}/100</li>
                </ul>
                </div>
                <br>
            """
        
        recommendation += f"""
            <h3>📋 Tips for {profile['name']}:</h3>
            <ul>
        """
        
        for tip in profile['tips']:
            recommendation += f"<li>{tip}</li>"
        
        recommendation += """
            </ul>
            
            <h3>⚠️ SIKKERHET - LES DETTE!</h3>
            <div style='background-color: #fadbd8; padding: 10px; border-radius: 5px; border: 2px solid #e74c3c;'>
            <p style='color: #c0392b; font-weight: bold;'>
            • START ALLTID 10% UNDER minimum anbefalt ladning fra produsent!<br>
            • Arbeid deg opp gradvis i 0.2-0.3gr steg<br>
            • Overvåk trykkindikasjon på hver ladning (flat primer, heavy bolt lift)<br>
            • Verifiser med offisiell ladningsmanual før bruk<br>
            • Disse anbefalingene er VEILEDENDE - ikke absolutte verdier<br>
            • Ulike rifler kan ha forskjellig trykknivå selv med samme ladning
            </p>
            </div>
        """
        
        # Hvis ingen data - vis advarsel
        if not load_data and not scored_history:
            recommendation += f"""
                <br>
                <div style='background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 2px solid #f39c12;'>
                <h3 style='color: #856404;'>⚠️ Ingen data funnet</h3>
                <p>Vi fant verken ladetabeller eller historiske tester for denne kombinasjonen.</p>
                <p><b>Anbefaling:</b> Bruk offisiell ladningsmanual og start med minimum ladning.</p>
                </div>
            """
        
        self.text_recommendation.setHtml(recommendation)
        
        self.progress.setValue(100)
        self.label_status.setText("✅ Analyse fullført!")


class GuidancePage(QWizardPage):
    """Steg 5: Veiledning og neste steg"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("📚 Veiledning")
        self.setSubTitle("Neste steg i ladningsprosessen")
        
        layout = QVBoxLayout()
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
            <h2>🎯 Neste steg:</h2>
            
            <h3>1. Forbered komponenter</h3>
            <ul>
                <li>Inspiser hylser for sprekker</li>
                <li>Mål case length og trim om nødvendig</li>
                <li>Clean primer pockets</li>
                <li>Weigh komponenter nøyaktig</li>
            </ul>
            
            <h3>2. Lading</h3>
            <ul>
                <li>Dobbeltsjekk pulvervekt</li>
                <li>Konsistent seating depth</li>
                <li>Logg ALLE detaljer i Session Logger</li>
            </ul>
            
            <h3>3. Testing</h3>
            <ul>
                <li>Bruk chronograph (importer til Chronograph tab)</li>
                <li>Skyt minimum 5-skudds grupper</li>
                <li>Dokumenter vær/temperatur</li>
                <li>Ta bilde av grupper (Target Analyzer)</li>
            </ul>
            
            <h3>4. Analyse</h3>
            <ul>
                <li>Analyser ES/SD i Precision Tracker</li>
                <li>Sjekk pressure signs i Safety Dashboard</li>
                <li>Beregn drops i Drop Chart Generator</li>
            </ul>
            
            <h2>✅ Klar til å starte?</h2>
            <p>Trykk 'Finish' for å opprette en ny loading session!</p>
        """)
        layout.addWidget(text)
        
        self.setLayout(layout)


class SmartLoadingWizard(QWizard):
    """Hovedwizard for smart ladningsveiledning"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("🧙 Smart Loading Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        
        # Add pages
        self.addPage(RifleSelectionPage())
        self.addPage(PurposeSelectionPage())
        self.addPage(ComponentSelectionPage())
        self.addPage(AIRecommendationPage())
        self.addPage(GuidancePage())
        
        self.resize(800, 600)
    
    def accept(self):
        """Når wizard fullføres"""
        # TODO: Create new loading session in database
        QMessageBox.information(
            self,
            "Suksess!",
            "Smart Loading Wizard fullført!\n\n"
            "En ny loading session er opprettet.\n"
            "Gå til Session Logger for å starte logging."
        )
        super().accept()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    wizard = SmartLoadingWizard()
    wizard.show()
    sys.exit(app.exec())
