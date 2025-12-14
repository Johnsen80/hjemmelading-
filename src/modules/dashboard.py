"""
Dashboard
Oversikt over lagerstatus, nylige aktiviteter og statistikk
"""

# Temporary: duplicate definitions were present; deduplicated selectively

import importlib
import json
import os
import uuid
from datetime import datetime, timedelta

from src.utils.optional_deps import Figure as Figure
from src.utils.optional_deps import FigureCanvas as FigureCanvas
from src.utils.optional_deps import plt

try:
    from matplotlib.backends.backend_pdf import PdfPages
except Exception:
    PdfPages = None
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.database.database import get_database
from src.logging_config import configure_logging, get_logger
from src.modules.weapon_profile_dialog import WeaponProfileDialog
from src.ui.modern_card import ModernCard
from src.utils.i18n import tr

configure_logging()
logger = get_logger(__name__)


class Dashboard(QWidget):
    def create_ai_tips_widget(self):
        widget = QGroupBox("AI-tips og ammo-match")
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Spør AI om ammo, batch, test...")
        layout.addWidget(self.ai_input)
        ai_btn = QPushButton("Få AI-anbefaling")
        ai_btn.clicked.connect(self.get_ai_tip)
        layout.addWidget(ai_btn)
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        layout.addWidget(self.ai_output)
        # Demo: vis beste ammo/batch
        best = self.get_best_ammo()
        if best:
            layout.addWidget(
                QLabel(
                    f"Beste ammo: {best['ammo']} batch {best['batch']} ({best['group']} mm samling)"
                )
            )
        return widget

    def get_ai_tip(self):
        question = self.ai_input.text().strip()
        lots = getattr(self, "test_history", [])
        if not question:
            self.ai_output.setText("Skriv inn et spørsmål!")
            return
        if "presisjon" in question.lower():
            best = self.get_best_ammo()
            if best:
                self.ai_output.setText(
                    f"Beste presisjon: {best['ammo']} batch {best['batch']} med samling {best['group']} mm."
                )
            else:
                self.ai_output.setText("Ingen testdata for presisjon.")
        elif "hastighet" in question.lower():
            fastest = sorted(
                lots, key=lambda e: float(e.get("velocity", 0)), reverse=True
            )[:1]
            if fastest:
                self.ai_output.setText(
                    f"Høyeste hastighet: {fastest[0]['ammo']} batch {fastest[0]['batch']} med {fastest[0]['velocity']} fps."
                )
            else:
                self.ai_output.setText("Ingen testdata for hastighet.")
        elif "anbefal" in question.lower() or "match" in question.lower():
            best = self.get_best_ammo()
            if best:
                self.ai_output.setText(
                    f"Anbefalt ammo: {best['ammo']} batch {best['batch']} (samling {best['group']} mm)"
                )
            else:
                self.ai_output.setText("Ingen testdata for anbefaling.")
        else:
            self.ai_output.setText(
                "AI: Spør om presisjon, hastighet, anbefaling eller match!"
            )

    def get_best_ammo(self):
        lots = getattr(self, "test_history", [])
        if not lots:
            return None
        best = sorted(lots, key=lambda e: float(e.get("group", 9999)))[:1]
        return best[0] if best else None

    def load_dashboard_profile(self):
        import json

        from PyQt6.QtWidgets import QFileDialog

        fname, _ = QFileDialog.getOpenFileName(
            self, "Last dashboard-oppsett", "", "JSON-filer (*.json)"
        )
        if fname:
            with open(fname, "r", encoding="utf-8") as f:
                profile = json.load(f)
            if hasattr(self.display_options, "set_state"):
                self.display_options.set_state(profile.get("display_options", {}))
            self.favorites = profile.get("favorites", [])
            self.test_history = profile.get("test_history", [])
            # Oppdater widgets hvis nødvendig
            self.update_dashboard_widgets()

    def update_dashboard_widgets(self):
        # Oppdater dashboard-widgets basert på profil
        pass

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.current_language = "no"  # Standard språk
        self.init_ui()

    def init_ui(self):
        # ...existing code...
        # ...existing code...
        # Scroll area for å håndtere mye innhold
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        scroll.setWidget(container)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(scroll)

        # Visuelle widgets for hurtigstatistikk, ammo-sammenligning og batchanalyse
        layout.addWidget(self.create_quick_stats_widget())
        layout.addWidget(self.create_ammo_comparison_widget())
        layout.addWidget(self.create_batch_analysis_widget())

    def create_quick_stats_widget(self):
        widget = QGroupBox("Hurtigstatistikk")
        layout = QHBoxLayout()
        widget.setLayout(layout)
        lots = getattr(self, "test_history", [])
        if not lots:
            layout.addWidget(QLabel("Ingen testdata tilgjengelig."))
            return widget
        # Statistikk: beste gruppe, snitt MOA, total treff
        best_group = min(
            [
                float(e.get("group_size_mm", 9999))
                for e in lots
                if e.get("group_size_mm")
            ],
            default=None,
        )
        avg_moa = round(
            sum([float(e.get("moa", 0)) for e in lots if e.get("moa")])
            / max(1, len([e for e in lots if e.get("moa")])),
            2,
        )
        total_hits = sum(
            [int(e.get("shot_count", 0)) for e in lots if e.get("shot_count")]
        )
        layout.addWidget(
            QLabel(f"Beste gruppe: {best_group if best_group is not None else '-'} mm")
        )
        layout.addWidget(QLabel(f"Snitt MOA: {avg_moa}"))
        layout.addWidget(QLabel(f"Totalt antall treff: {total_hits}"))
        return widget

    def create_ammo_comparison_widget(self):
        widget = QGroupBox("Ammo-sammenligning")
        layout = QVBoxLayout()
        widget.setLayout(layout)
        lots = getattr(self, "test_history", [])
        if not lots:
            layout.addWidget(QLabel("Ingen testdata tilgjengelig."))
            return widget
        # Sammenlign ammo på gruppe og MOA
        ammo_stats = {}
        for e in lots:
            ammo = e.get("ammo", "Ukjent")
            if ammo not in ammo_stats:
                ammo_stats[ammo] = {"groups": [], "moas": []}
            if e.get("group_size_mm"):
                ammo_stats[ammo]["groups"].append(float(e["group_size_mm"]))
            if e.get("moa"):
                ammo_stats[ammo]["moas"].append(float(e["moa"]))
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Ammo", "Snitt gruppe (mm)", "Snitt MOA"])
        table.setRowCount(len(ammo_stats))
        for i, (ammo, stats) in enumerate(ammo_stats.items()):
            avg_group = (
                round(sum(stats["groups"]) / max(1, len(stats["groups"])), 2)
                if stats["groups"]
                else "-"
            )
            avg_moa = (
                round(sum(stats["moas"]) / max(1, len(stats["moas"])), 2)
                if stats["moas"]
                else "-"
            )
            table.setItem(i, 0, QTableWidgetItem(ammo))
            table.setItem(i, 1, QTableWidgetItem(str(avg_group)))
            table.setItem(i, 2, QTableWidgetItem(str(avg_moa)))
        layout.addWidget(table)
        return widget

    def create_batch_analysis_widget(self):
        widget = QGroupBox("Batchanalyse")
        layout = QVBoxLayout()
        widget.setLayout(layout)
        lots = getattr(self, "test_history", [])
        if not lots:
            layout.addWidget(QLabel("Ingen batchdata tilgjengelig."))
            return widget
        # Vis batcher med bildeanalyse og statistikk
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["Batch", "Ammo", "Gruppe (mm)", "MOA", "Treff", "Bilde"]
        )
        table.setRowCount(len(lots))
        for i, e in enumerate(lots):
            table.setItem(i, 0, QTableWidgetItem(str(e.get("batch", ""))))
            table.setItem(i, 1, QTableWidgetItem(str(e.get("ammo", ""))))
            table.setItem(i, 2, QTableWidgetItem(str(e.get("group_size_mm", ""))))
            table.setItem(i, 3, QTableWidgetItem(str(e.get("moa", ""))))
            table.setItem(i, 4, QTableWidgetItem(str(e.get("shot_count", ""))))
            # Scroll area for å håndtere mye innhold
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            container = QWidget()
            layout = QVBoxLayout()
            container.setLayout(layout)
            scroll.setWidget(container)

            main_layout = QVBoxLayout()
            self.setLayout(main_layout)
            main_layout.addWidget(scroll)

            # Visuelle widgets for hurtigstatistikk, ammo-sammenligning og batchanalyse
            layout.addWidget(self.create_quick_stats_widget())
            layout.addWidget(self.create_ammo_comparison_widget())
            layout.addWidget(self.create_batch_analysis_widget())

            # Tittel
            title = QLabel(tr("dashboard_title", self.current_language))
            title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            title.setStyleSheet("margin: 20px;")
            layout.addWidget(title)

            # Velkommen
            welcome = QLabel(tr("dashboard_welcome", self.current_language))
            welcome.setFont(QFont("Arial", 14))
            layout.addWidget(welcome)

            # HERO SECTION: Smart Loading Wizard
            hero_section = self.create_hero_section()
            layout.addWidget(hero_section)

            # Statistikk-kort
            stats_layout = QHBoxLayout()
            layout.addLayout(stats_layout)

            stats_layout.addWidget(
                self.create_stat_card(
                    tr("dashboard_rifles", self.current_language), self.count_rifles()
                )
            )
            stats_layout.addWidget(
                self.create_stat_card(
                    tr("dashboard_ammo_profiles", self.current_language),
                    self.count_ammo_profiles(),
                )
            )
            stats_layout.addWidget(
                self.create_stat_card(
                    tr("dashboard_ladder_tests", self.current_language),
                    self.count_ladder_tests(),
                )
            )
            stats_layout.addWidget(
                self.create_stat_card(
                    tr("dashboard_loading_sessions", self.current_language),
                    self.count_loading_sessions(),
                )
            )

            # Lagerstatus
            layout.addWidget(self.create_inventory_status())

            # Nylige aktiviteter
            layout.addWidget(self.create_recent_activity())

            # Quick tips
            layout.addWidget(self.create_quick_tips())

            layout.addStretch()

            # Visningsalternativer og AI Chat
            self.display_options = DisplayOptionsWidget(self)
            layout.addWidget(self.display_options)

            # Lagring/lasting dashboard-oppsett
            save_btn = QPushButton("Lagre dashboard-oppsett")
            save_btn.clicked.connect(self.save_dashboard_profile)
            layout.addWidget(save_btn)
            load_btn = QPushButton("Last dashboard-oppsett")
            load_btn.clicked.connect(self.load_dashboard_profile)
            layout.addWidget(load_btn)

            # AI-tips og ammo-match-widget
            layout.addWidget(self.create_ai_tips_widget())

            # Visuell widget for bildeanalyse (gruppe, MOA, treff)
            layout.addWidget(self.create_image_analysis_widget())
        layout.addWidget(self.create_ai_tips_widget())

        # Visuell widget for bildeanalyse (gruppe, MOA, treff)
        layout.addWidget(self.create_image_analysis_widget())

    from PyQt6.QtGui import QPixmap

    def create_image_analysis_widget(self):
        widget = QGroupBox("Automatisk bildeanalyse: Gruppe, MOA, Treff")
        layout = QVBoxLayout()
        widget.setLayout(layout)
        # Hent batch/test-historikk med bildeanalyse
        lots = getattr(self, "test_history", [])
        analyzed = [
            e
            for e in lots
            if e.get("group_size_mm") or e.get("moa") or e.get("shot_count")
        ]
        if not analyzed:
            layout.addWidget(QLabel("Ingen analyserte bilder funnet i testhistorikk."))
            return widget
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Ammo", "Batch", "Gruppe (mm)", "MOA", "Treff"]
        )
        table.setRowCount(len(analyzed))
        for i, e in enumerate(analyzed):
            table.setItem(i, 0, QTableWidgetItem(str(e.get("ammo", ""))))
            table.setItem(i, 1, QTableWidgetItem(str(e.get("batch", ""))))
            table.setItem(i, 2, QTableWidgetItem(str(e.get("group_size_mm", ""))))
            table.setItem(i, 3, QTableWidgetItem(str(e.get("moa", ""))))
            table.setItem(i, 4, QTableWidgetItem(str(e.get("shot_count", ""))))
        layout.addWidget(table)
        # Vis siste bilde med analyse
        last = analyzed[-1]
        img_path = last.get("img", None)
        if img_path:
            img_label = QLabel()
            img_label.setPixmap(
                QPixmap(img_path).scaledToWidth(
                    200, Qt.TransformationMode.SmoothTransformation
                )
            )
            layout.addWidget(img_label)
        return widget

    def create_stat_card(self, title, value):
        """Oppretter et statistikk-kort med moderne stil"""
        return ModernCard(title, str(value), icon_path=None)

    def create_hero_section(self):
        """Lager hero section med Smart Loading Wizard"""
        group = QGroupBox()
        group.setStyleSheet(
            """
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                padding: 30px;
                margin: 10px;
            }
        """
        )

        layout = QVBoxLayout()
        group.setLayout(layout)

        # Title
        title = QLabel("🧙 Smart Loading Wizard")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "AI-drevet ladningsveiledning fra nybegynner til ekspert\n"
            "Velg rifle → Velg formål → Få optimal anbefaling"
        )
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9); margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Features
        features_layout = QHBoxLayout()

        feature1 = QLabel("✅ Analyserer\nhistorikk")
        feature1.setStyleSheet("color: white; font-size: 12px;")
        feature1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(feature1)

        feature2 = QLabel("🎯 Optimerer for\nformål")
        feature2.setStyleSheet("color: white; font-size: 12px;")
        feature2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(feature2)

        feature3 = QLabel("🤖 AI-drevne\nanbefalinger")
        feature3.setStyleSheet("color: white; font-size: 12px;")
        feature3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(feature3)

        feature4 = QLabel("📚 Steg-for-steg\nveiledning")
        feature4.setStyleSheet("color: white; font-size: 12px;")
        feature4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(feature4)

        layout.addLayout(features_layout)

        # Big CTA button
        btn_start = QPushButton("🚀 START LOADING WIZARD")
        btn_start.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        btn_start.setMinimumHeight(60)
        btn_start.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """
        )
        btn_start.clicked.connect(self.launch_wizard)
        layout.addWidget(btn_start)

        return group

    def launch_wizard(self):
        """Start Smart Loading Wizard"""
        from src.modules.smart_loading_wizard import SmartLoadingWizard

        self.wizard = SmartLoadingWizard(self)
        self.wizard.show()

    def create_inventory_status(self):
        """Lager lagerstatus-oversikt"""
        group = QGroupBox(tr("dashboard_inventory_status", self.current_language))
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Sjekk krutt
        powders = self.db.get_all("powder")
        low_powder = [
            p for p in powders if p["quantity_grams"] and p["quantity_grams"] < 500
        ]

        # Sjekk kuler
        bullets = self.db.get_all("bullets")
        low_bullets = [b for b in bullets if b["quantity"] and b["quantity"] < 100]

        # Sjekk tennhetter
        primers = self.db.get_all("primers")
        low_primers = [p for p in primers if p["quantity"] and p["quantity"] < 100]

        # Sjekk hylser
        cases = self.db.get_all("cases")
        worn_cases = [c for c in cases if c["times_fired"] and c["times_fired"] > 5]

        if not low_powder and not low_bullets and not low_primers and not worn_cases:
            status = QLabel(tr("dashboard_all_ok", self.current_language))
            status.setStyleSheet("color: green; font-size: 12pt;")
            layout.addWidget(status)
        else:
            # Advarsler
            if low_powder:
                warning = QLabel(
                    f"⚠️ <b>{len(low_powder)} krutt</b> har lavt lager (< 500g)"
                )
                warning.setStyleSheet("color: orange;")
                layout.addWidget(warning)

            if low_bullets:
                warning = QLabel(
                    f"⚠️ <b>{len(low_bullets)} kuler</b> har lavt lager (< 100 stk)"
                )
                warning.setStyleSheet("color: orange;")
                layout.addWidget(warning)

            if low_primers:
                warning = QLabel(
                    f"⚠️ <b>{len(low_primers)} tennhetter</b> har lavt lager (< 100 stk)"
                )
                warning.setStyleSheet("color: orange;")
                layout.addWidget(warning)

            if worn_cases:
                warning = QLabel(
                    f"⚠️ <b>{len(worn_cases)} hylser</b> er brukt > 5 ganger (vurder utsortering)"
                )
                warning.setStyleSheet("color: orange;")
                layout.addWidget(warning)

        return group

    def create_recent_activity(self):
        """Viser nylige aktiviteter"""
        group = QGroupBox(tr("dashboard_recent_activity", self.current_language))
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Hent nylige ladeøkter
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        loading_sessions = self.db.execute_query(
            "SELECT * FROM loading_sessions WHERE date >= ? ORDER BY date DESC LIMIT 5",
            (week_ago,),
        )

        shooting_sessions = self.db.execute_query(
            "SELECT * FROM shooting_sessions WHERE date >= ? ORDER BY date DESC LIMIT 5",
            (week_ago,),
        )

        ladder_tests = self.db.execute_query(
            "SELECT * FROM ladder_tests WHERE date >= ? ORDER BY date DESC LIMIT 5",
            (week_ago,),
        )

        if not loading_sessions and not shooting_sessions and not ladder_tests:
            no_activity = QLabel(tr("dashboard_no_activity", self.current_language))
            no_activity.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(no_activity)
        else:
            # Ladeøkter
            if loading_sessions:
                layout.addWidget(QLabel("<b>Ladeøkter:</b>"))
                for session in loading_sessions:
                    ammo_name = "Ukjent"
                    if session["ammo_profile_id"]:
                        ammo = self.db.get_by_id(
                            "ammo_profiles", session["ammo_profile_id"]
                        )
                        if ammo:
                            ammo_name = ammo["name"]

                    item = QLabel(
                        f"  • {session['date']}: {session['quantity']} stk {ammo_name}"
                    )
                    layout.addWidget(item)

            # Skyteøkter
            if shooting_sessions:
                layout.addWidget(QLabel("<b>Skyteøkter:</b>"))
                for session in shooting_sessions:
                    rifle_name = "Ukjent"
                    if session["rifle_id"]:
                        rifle = self.db.get_by_id("rifles", session["rifle_id"])
                        if rifle:
                            rifle_name = rifle["name"]

                    item = QLabel(
                        f"  • {session['date']}: {rifle_name} - {session['rounds_fired']} skudd"
                    )
                    layout.addWidget(item)

            # Ladder tests
            if ladder_tests:
                layout.addWidget(QLabel("<b>Ladder Tests:</b>"))
                for test in ladder_tests:
                    item = QLabel(f"  • {test['date']}: {test['name']}")
                    layout.addWidget(item)

        return group

    def create_quick_tips(self):
        """Viser nyttige tips"""
        group = QGroupBox(tr("dashboard_quick_tips", self.current_language))
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        tips = [
            "Bruk <b>Zero Shift Calculator</b> (Verktøy-menyen) for å beregne optikk-justeringer ved ammunisjonsskifte",
            "Start alltid med minimum ladning og arbeid deg opp gradvis",
            "Dokumenter alle ladeøkter grundig - det er gull verdt senere",
            "Hold alltid oversikt over hvor mange ganger hylsene er brukt",
            "Test nye ladninger på 100m før du går til lengre hold",
            "Bruk Ladder Test for å finne optimale kruttvekter",
            "Sjekk lager regelmessig - bestill komponenter i god tid",
        ]

        import random

        tip = random.choice(tips)

        tip_label = QLabel(f"💡 {tip}")
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(
            "font-size: 11pt; padding: 10px; background-color: #ffffcc; border-radius: 5px;"
        )
        layout.addWidget(tip_label)

        return group

    # Hjelpemetoder for telling

    def count_rifles(self):
        """Teller rifles"""
        rifles = self.db.get_all("rifles")
        return len(rifles)

    def count_ammo_profiles(self):
        """Teller ammunisjonsprofiler"""
        profiles = self.db.get_all("ammo_profiles")
        return len(profiles)

    def count_ladder_tests(self):
        """Teller ladder tests"""
        tests = self.db.get_all("ladder_tests")
        return len(tests)

    def count_loading_sessions(self):
        """Teller ladeøkter"""
        sessions = self.db.get_all("loading_sessions")
        return len(sessions)


class AmmoTestReport:
    """Modul for logging, sammenligning og rapportering av ammunisjonstester"""

    def __init__(self, db, language="no"):
        self.db = db
        self.language = language

    def log_test(
        self,
        lot_number,
        manufacturer,
        model,
        caliber,
        velocity_list,
        group_size_list,
        case_spec,
        bullet_spec,
        powder_spec,
        primer_spec,
        weapon_weight,
        notes="",
        image_path=None,
    ):
        """Lagrer testdata med full spesifikasjon, unik test-ID, dato og tid"""
        test_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        test_date = now.strftime("%Y-%m-%d")
        log_time = now.strftime("%H:%M:%S")
        data = {
            "test_id": test_id,
            "lot_number": lot_number,
            "manufacturer": manufacturer,
            "model": model,
            "caliber": caliber,
            "test_date": test_date,
            "log_time": log_time,
            "velocity_list": str(velocity_list),
            "group_size_list": str(group_size_list),
            "case_spec": str(case_spec),
            "bullet_spec": str(bullet_spec),
            "powder_spec": str(powder_spec),
            "primer_spec": str(primer_spec),
            "weapon_weight": weapon_weight,
            "notes": notes,
            "image_path": image_path,
        }
        self.db.insert("ammo_test_reports", data)
        return test_id

    def compare_lots(self, caliber, manufacturer=None):
        """Henter og sammenligner alle tester for valgt kaliber og evt. produsent"""
        query = "SELECT * FROM ammo_test_reports WHERE caliber = ?"
        params = (caliber,)
        if manufacturer:
            query += " AND manufacturer = ?"
            params += (manufacturer,)
        return self.db.execute_query(query, params)

    def calculate_energy(self, velocity, bullet_weight):
        """Beregner anslagsenergi (Joule)"""
        # bullet_weight i gram, velocity i m/s
        return 0.5 * bullet_weight * velocity**2

    def calculate_recoil(self, bullet_weight, powder_weight, velocity, weapon_weight):
        """Beregner rekyl (Joule)"""
        # Forenklet formel
        return (bullet_weight + powder_weight) * velocity / weapon_weight

    def simulate_ballistics(self, velocity, bullet_weight, distances):
        """Simulerer anslagsenergi og drop på ulike hold"""
        results = []
        for d in distances:
            energy = self.calculate_energy(velocity, bullet_weight)
            drop = d * 0.01  # Forenklet drop, kan kobles til ballistikkmodul
            results.append({"distance": d, "energy": energy, "drop": drop})
        return results

    def generate_report(self, test_id, report_type="private"):
        """Genererer rapport med alle spesifikasjoner, grafer, bilde og beregninger"""
        import matplotlib.image as mpimg
        import matplotlib.pyplot as plt

        tests = self.db.execute_query(
            "SELECT * FROM ammo_test_reports WHERE test_id = ?", (test_id,)
        )
        if not tests:
            return tr("no_test_data", self.language)
        velocities = eval(tests[0]["velocity_list"])
        group_sizes = eval(tests[0]["group_size_list"])
        image_path = tests[0].get("image_path")
        weapon_weight = float(tests[0].get("weapon_weight", 0))
        bullet_spec = eval(tests[0]["bullet_spec"])
        powder_spec = eval(tests[0]["powder_spec"])
        bullet_weight = (
            float(bullet_spec.get("weight_grains", 0)) * 0.0648
        )  # grains til gram
        powder_weight = float(powder_spec.get("weight_grains", 0)) * 0.0648
        velocity = float(velocities[0]) if velocities else 0
        energy = self.calculate_energy(velocity, bullet_weight)
        recoil = self.calculate_recoil(
            bullet_weight, powder_weight, velocity, weapon_weight
        )
        fig, ax = plt.subplots()
        ax.plot(velocities, label=tr("velocity", self.language))
        ax.plot(group_sizes, label=tr("group_size", self.language))
        ax.set_title(tr("ammo_test_report_title", self.language))
        ax.legend()
        # Tilpass rapporten etter type
        if report_type == "store":
            ax.set_xlabel(tr("store_report_x_label", self.language))
            ax.set_ylabel(tr("store_report_y_label", self.language))
            plt.figtext(
                0.5,
                0.01,
                tr("store_report_footer", self.language),
                ha="center",
                fontsize=10,
            )
        elif report_type == "supplier":
            ax.set_xlabel(tr("supplier_report_x_label", self.language))
            ax.set_ylabel(tr("supplier_report_y_label", self.language))
            plt.figtext(
                0.5,
                0.01,
                tr("supplier_report_footer", self.language),
                ha="center",
                fontsize=10,
            )
        else:
            ax.set_xlabel(tr("private_report_x_label", self.language))
            ax.set_ylabel(tr("private_report_y_label", self.language))
        # Legg til bilde hvis tilgjengelig
        if image_path:
            try:
                img = mpimg.imread(image_path)
                newax = fig.add_axes([0.7, 0.6, 0.25, 0.25], anchor="NE", zorder=1)
                newax.imshow(img)
                newax.axis("off")
            except Exception as e:
                logger.error("Bilde-feil: %s", e)
        # Legg til beregninger
        plt.figtext(
            0.1,
            0.01,
            f"Anslagsenergi: {energy:.1f} J | Rekyl: {recoil:.2f} J",
            ha="left",
            fontsize=10,
        )
        plt.savefig(f"ammo_test_report_{test_id}_{report_type}.png")
        return f"Rapport generert: ammo_test_report_{test_id}_{report_type}.png"

    def compare_previous_tests(self, lot_number, caliber, manufacturer, model):
        """Henter og sammenligner alle tidligere tester på samme type ammo"""
        query = "SELECT * FROM ammo_test_reports WHERE caliber = ? AND manufacturer = ? AND model = ? ORDER BY test_date DESC"
        params = (caliber, manufacturer, model)
        tests = self.db.execute_query(query, params)
        current_test = [t for t in tests if t["lot_number"] == lot_number]
        previous_tests = [t for t in tests if t["lot_number"] != lot_number]
        return current_test, previous_tests

    def analyze_differences(self, current_test, previous_tests):
        """Analyserer forskjeller mellom nåværende og tidligere tester"""
        import numpy as np

        results = {}
        if not current_test or not previous_tests:
            return results
        curr_vel = np.mean(eval(current_test[0]["velocity_list"]))
        curr_group = np.mean(eval(current_test[0]["group_size_list"]))
        prev_vels = [np.mean(eval(t["velocity_list"])) for t in previous_tests]
        prev_groups = [np.mean(eval(t["group_size_list"])) for t in previous_tests]
        results["velocity_diff"] = curr_vel - np.mean(prev_vels) if prev_vels else 0
        results["group_size_diff"] = (
            curr_group - np.mean(prev_groups) if prev_groups else 0
        )
        results["trend"] = "Bedre" if results["group_size_diff"] < 0 else "Dårligere"
        return results

    def generate_comparison_report(
        self, lot_number, caliber, manufacturer, model, report_type="private"
    ):
        """Genererer rapport med sammenligning og analyse av tidligere tester"""
        current_test, previous_tests = self.compare_previous_tests(
            lot_number, caliber, manufacturer, model
        )
        _differences = self.analyze_differences(current_test, previous_tests)
        # ...existing code for rapportgenerering...
        # Legg til sammenligningsdata og trendanalyse i rapporten
        # Eksempel: velocity_diff, group_size_diff, trend
        # ...existing code...


class SystemWeaponManager(QWidget):
    """UI for administrasjon av systemvåpen og testvåpen"""

    def __init__(self, db, language="no"):
        super().__init__()
        self.db = db
        self.language = language
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        title = QLabel(tr("system_weapon_title", self.language))
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        self.rifle_list = QComboBox()
        self.update_rifle_list()
        layout.addWidget(self.rifle_list)
        add_btn = QPushButton(tr("add_system_weapon", self.language))
        add_btn.clicked.connect(self.add_system_weapon_dialog)
        layout.addWidget(add_btn)
        self.barrel_table = QTableWidget()
        self.barrel_table.setColumnCount(4)
        self.barrel_table.setHorizontalHeaderLabels(
            [
                tr("barrel_name", self.language),
                tr("profile", self.language),
                tr("caliber", self.language),
                tr("actions", self.language),
            ]
        )
        layout.addWidget(self.barrel_table)
        self.update_barrel_table()

    def update_rifle_list(self):
        rifles = self.db.execute_query("SELECT id, name FROM rifles")
        self.rifle_list.clear()
        for r in rifles:
            self.rifle_list.addItem(r["name"], r["id"])

    def update_barrel_table(self):
        rifle_id = self.rifle_list.currentData()
        barrels = self.db.execute_query(
            "SELECT * FROM barrel_profiles WHERE id IN (SELECT barrel_profile_id FROM rifles WHERE id = ?)",
            (rifle_id,),
        )
        self.barrel_table.setRowCount(len(barrels))
        for i, b in enumerate(barrels):
            self.barrel_table.setItem(i, 0, QTableWidgetItem(b["name"]))
            self.barrel_table.setItem(i, 1, QTableWidgetItem(b["category"]))
            self.barrel_table.setItem(i, 2, QTableWidgetItem(b["typical_calibers"]))
            self.barrel_table.setItem(i, 3, QTableWidgetItem(tr("edit", self.language)))

    def add_system_weapon_dialog(self):
        # Her kan du lage en dialog for å legge til systemvåpen med flere løp/profiler/kalibere
        pass


class AmmoTestReportUI(QWidget):
    """Visuell og enkel UI for logging av ammunisjonstester med bransjestandard felter"""

    def __init__(self, db, language="no"):
        super().__init__()
        self.db = db
        self.language = language
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        title = QLabel(tr("ammo_test_ui_title", self.language))
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        # Felter for bransjestandard data
        self.lot_input = QLineEdit()
        self.manufacturer_input = QLineEdit()
        self.model_input = QLineEdit()
        self.caliber_input = QLineEdit()
        self.velocity_input = QLineEdit()
        self.group_size_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.image_btn = QPushButton(tr("add_image", self.language))
        self.image_btn.clicked.connect(self.add_image)
        self.image_path = None
        # Legg til felter i layout
        layout.addWidget(QLabel(tr("lot_number", self.language)))
        layout.addWidget(self.lot_input)
        layout.addWidget(QLabel(tr("manufacturer", self.language)))
        layout.addWidget(self.manufacturer_input)
        layout.addWidget(QLabel(tr("model", self.language)))
        layout.addWidget(self.model_input)
        layout.addWidget(QLabel(tr("caliber", self.language)))
        layout.addWidget(self.caliber_input)
        layout.addWidget(QLabel(tr("velocity", self.language)))
        layout.addWidget(self.velocity_input)
        layout.addWidget(QLabel(tr("group_size", self.language)))
        layout.addWidget(self.group_size_input)
        layout.addWidget(QLabel(tr("notes", self.language)))
        layout.addWidget(self.notes_input)
        layout.addWidget(self.image_btn)
        # Knapp for lagring
        save_btn = QPushButton(tr("save_test", self.language))
        save_btn.clicked.connect(self.save_test)
        layout.addWidget(save_btn)

    def add_image(self):
        # Enkel bildeopplasting
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("select_image", self.language), "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.image_path = file_path

    def save_test(self):
        # Lagre alle data til AmmoTestReport
        _velocity_list = [
            float(v) for v in self.velocity_input.text().split(",") if v.strip()
        ]
        _group_size_list = [
            float(g) for g in self.group_size_input.text().split(",") if g.strip()
        ]
        # ...hent og lagre alle andre felter...
        # Koble til testutstyr/API hvis tilgjengelig
        # ...forbered integrasjon...
        # ...kall AmmoTestReport.log_test(...)
        pass


class CaseBatchPrepUI(QWidget):
    """UI for hylse batch og prepping med gløding-valg"""

    def __init__(self, db, language="no"):
        super().__init__()
        self.db = db
        self.language = language
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        title = QLabel(tr("case_batch_title", self.language))
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        self.batch_name_input = QLineEdit()
        self.glow_checkbox = QCheckBox(tr("annealed", self.language))
        self.trim_length_input = QDoubleSpinBox()
        self.trim_length_input.setSuffix(" mm")
        self.trim_length_input.setRange(0, 100)
        self.neck_in_checkbox = QCheckBox(tr("neck_in_prep", self.language))
        self.neck_out_checkbox = QCheckBox(tr("neck_out_prep", self.language))
        self.primer_pocket_checkbox = QCheckBox(tr("primer_pocket_prep", self.language))
        layout.addWidget(QLabel(tr("batch_name", self.language)))
        layout.addWidget(self.batch_name_input)
        layout.addWidget(self.glow_checkbox)
        layout.addWidget(QLabel(tr("trim_length", self.language)))
        layout.addWidget(self.trim_length_input)
        layout.addWidget(self.neck_in_checkbox)
        layout.addWidget(self.neck_out_checkbox)
        layout.addWidget(self.primer_pocket_checkbox)
        save_btn = QPushButton(tr("save_batch", self.language))
        save_btn.clicked.connect(self.save_batch)
        layout.addWidget(save_btn)

    def save_batch(self):
        _batch_name = self.batch_name_input.text()
        annealed = self.glow_checkbox.isChecked()
        trim_length = self.trim_length_input.value()
        neck_in = self.neck_in_checkbox.isChecked()
        neck_out = self.neck_out_checkbox.isChecked()
        primer_pocket = self.primer_pocket_checkbox.isChecked()
        # ...lagre batch med alle preppingsteg...
        advice = []
        if annealed:
            advice.append(tr("annealed_advice", self.language))
        else:
            advice.append(tr("not_annealed_advice", self.language))
        advice.append(tr("trim_advice", self.language) + f" {trim_length:.2f} mm")
        if neck_in:
            advice.append(tr("neck_in_advice", self.language))
        if neck_out:
            advice.append(tr("neck_out_advice", self.language))
        if primer_pocket:
            advice.append(tr("primer_pocket_advice", self.language))
        QMessageBox.information(
            self, tr("prep_advice_title", self.language), "\n".join(advice)
        )
        # ...videre logging og visuelle anbefalinger...
        pass


class WeaponProfileWidget(QWidget):
    """Widget for å vise og redigere våpenprofiler, inkludert løp, optikk og innstillinger"""

    def __init__(self, db, language="no"):
        super().__init__()
        self.db = db
        self.language = language
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        title = QLabel(tr("weapon_profile_title", self.language))
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        # Velg rifle
        self.rifle_select = QComboBox()
        self.update_rifle_list()
        layout.addWidget(QLabel(tr("select_rifle", self.language)))
        layout.addWidget(self.rifle_select)
        # Løp og kaliber
        self.barrel_info = QLabel()
        layout.addWidget(self.barrel_info)
        # Buttons to create/edit/delete rifle profiles
        btn_row = QHBoxLayout()
        self.new_profile_btn = QPushButton("Ny profil")
        self.new_profile_btn.clicked.connect(self.create_new_profile)
        btn_row.addWidget(self.new_profile_btn)

        self.edit_profile_btn = QPushButton("Rediger profil")
        self.edit_profile_btn.clicked.connect(self.edit_current_profile)
        btn_row.addWidget(self.edit_profile_btn)

        self.delete_profile_btn = QPushButton("Slett profil")
        self.delete_profile_btn.clicked.connect(self.delete_current_profile)
        btn_row.addWidget(self.delete_profile_btn)

        layout.addLayout(btn_row)
        # Demo helper button (quickly open a demo profile as if a user created it)
        self.open_demo_btn = QPushButton("Vis demo profil")
        self.open_demo_btn.setToolTip(
            "Åpne demo-våpenprofilen i redigeringsdialog (hvis tilgjengelig)"
        )
        self.open_demo_btn.clicked.connect(self.open_demo_profile)
        layout.addWidget(self.open_demo_btn)
        # Optikker
        self.optics_list = QListWidget()
        self.add_optic_btn = QPushButton("Legg til optikk")
        self.add_optic_btn.clicked.connect(self.add_optic)
        layout.addWidget(QLabel("Optikker for denne rifla:"))
        layout.addWidget(self.optics_list)
        layout.addWidget(self.add_optic_btn)
        self.optic_settings_btn = QPushButton("Optikk-innstillinger")
        self.optic_settings_btn.clicked.connect(self.show_optic_settings)
        layout.addWidget(self.optic_settings_btn)
        # AI veileder og autofyll
        self.ai_helper_btn = QPushButton("AI veileder og autofyll")
        self.ai_helper_btn.clicked.connect(self.open_ai_helper)
        layout.addWidget(self.ai_helper_btn)
        # Velg løp og kaliber for ballistisk analyse
        self.barrel_select = QComboBox()
        self.caliber_select = QComboBox()
        self.ballistics_btn = QPushButton("Vis ballistisk analyse")
        self.ballistics_btn.clicked.connect(self.show_ballistics)
        layout.addWidget(QLabel("Velg løp:"))
        layout.addWidget(self.barrel_select)
        layout.addWidget(QLabel("Velg kaliber:"))
        layout.addWidget(self.caliber_select)
        layout.addWidget(self.ballistics_btn)
        self.ballistics_result = QLabel()
        layout.addWidget(self.ballistics_result)
        # Visningsalternativer for ballistisk analyse
        self.display_options = {
            "Klikktabell": QCheckBox("Klikktabell"),
            "Ballistisk kurve": QCheckBox("Ballistisk kurve"),
            "Vindavdrift": QCheckBox("Vindavdrift"),
            "Energi": QCheckBox("Energi"),
            "Hastighet": QCheckBox("Hastighet"),
        }
        for cb in self.display_options.values():
            cb.setChecked(True)
            layout.addWidget(cb)
        self.update_display_btn = QPushButton("Oppdater visning")
        self.update_display_btn.clicked.connect(self.update_display)
        layout.addWidget(self.update_display_btn)
        # Handling av riflevalg
        self.rifle_select.currentIndexChanged.connect(self.update_barrel_info)
        self.update_barrel_info()
        # Knapp for å vise optikk-historikk graf
        self.show_optic_graph_btn = QPushButton("Vis optikk-graf")
        self.show_optic_graph_btn.clicked.connect(self.show_optic_graph)
        layout.addWidget(self.show_optic_graph_btn)
        self.display_options_file = os.path.join(
            os.path.expanduser("~"), "weapon_display_options.json"
        )
        self.load_display_options()
        # Enkel/Avansert visning bryter
        self.simple_mode = QCheckBox("Enkel visning")
        self.simple_mode.setChecked(True)
        self.simple_mode.stateChanged.connect(self.toggle_simple_mode)
        layout.addWidget(self.simple_mode)

    def update_rifle_list(self):
        rifles = self.db.execute_query("SELECT id, name FROM rifles")
        self.rifle_select.clear()
        for r in rifles:
            self.rifle_select.addItem(r["name"], r["id"])
        # Add a placeholder when no rifles
        if not rifles:
            self.rifle_select.addItem("<Ingen våpen>", None)

    def update_barrel_info(self):
        rifle_id = self.rifle_select.currentData()
        if not rifle_id:
            return
        # Hent og vis informasjon om valgt løp og kaliber
        barrel = self.db.execute_query(
            "SELECT * FROM barrel_profiles WHERE id IN (SELECT barrel_profile_id FROM rifles WHERE id = ?)",
            (rifle_id,),
        )
        if barrel:
            barrel = barrel[0]
            self.barrel_info.setText(
                f"Navn: {barrel['name']}\nProfil: {barrel['category']}\nKaliber: {barrel['typical_calibers']}"
            )
        else:
            self.barrel_info.setText("")
        # Oppdater optikk liste
        self.update_optics_list(rifle_id)
        # Oppdater løp og kaliber valg for ballistisk analyse
        self.update_barrel_caliber_options(rifle_id)

    def update_optics_list(self, rifle_id):
        optics = self.db.execute_query(
            "SELECT * FROM optics WHERE id IN (SELECT optic_id FROM rifle_optics WHERE rifle_id = ?)",
            (rifle_id,),
        )
        self.optics_list.clear()
        for o in optics:
            self.optics_list.addItem(o["name"], o["id"])

    def update_barrel_caliber_options(self, rifle_id):
        # Oppdaterer valg for løp og kaliber basert på valgt rifle
        barrels = self.db.execute_query(
            "SELECT * FROM barrel_profiles WHERE id IN (SELECT barrel_profile_id FROM rifles WHERE id = ?)",
            (rifle_id,),
        )
        self.barrel_select.clear()
        self.caliber_select.clear()
        for b in barrels:
            self.barrel_select.addItem(b["name"], b["id"])
            # Anta at kaliber er lagret som en kommaseparert liste i barrel_profiles
            for cal in b["typical_calibers"].split(","):
                self.caliber_select.addItem(cal.strip(), cal.strip())

    def add_optic(self):
        # ...dialog for å legge til ny optikk...
        pass

    def create_new_profile(self):
        dlg = WeaponProfileDialog(db=self.db, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.update_rifle_list()

    def edit_current_profile(self):
        rifle_id = self.rifle_select.currentData()
        if not rifle_id:
            QMessageBox.information(
                self, "Ingen valgt", "Velg et våpen å redigere først."
            )
            return
        dlg = WeaponProfileDialog(db=self.db, rifle_id=rifle_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.update_rifle_list()
            # Reselect edited rifle if still present
            for i in range(self.rifle_select.count()):
                if self.rifle_select.itemData(i) == rifle_id:
                    self.rifle_select.setCurrentIndex(i)
                    break

    def delete_current_profile(self):
        rifle_id = self.rifle_select.currentData()
        if not rifle_id:
            QMessageBox.information(
                self, "Ingen valgt", "Velg et våpen å slette først."
            )
            return
        ok = QMessageBox.question(
            self,
            "Bekreft sletting",
            "Er du sikker på at du vil slette denne våpenprofilen? Dette kan ikke angres.",
        )
        if ok == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete("rifles", "id = ?", (rifle_id,))
                logger.info("User deleted rifle id %s", rifle_id)
                self.update_rifle_list()
            except Exception as e:
                logger.exception("Failed to delete rifle id %s: %s", rifle_id, e)
                QMessageBox.critical(self, "Feil", f"Kunne ikke slette våpen: {e}")

    def open_demo_profile(self):
        """Find a demo rifle and open it in the editor. Looks for 'VALKYRIE Demo' first, then 'Demo'."""
        # Try exact name then fallback
        demo = self.db.execute_query(
            "SELECT id FROM rifles WHERE name LIKE ? LIMIT 1", ("%VALKYRIE Demo%",)
        )
        if not demo:
            demo = self.db.execute_query(
                "SELECT id FROM rifles WHERE name LIKE ? LIMIT 1", ("%Demo%",)
            )
        if not demo:
            QMessageBox.information(
                self,
                "Demo ikke funnet",
                "Ingen demo-våpen funnet i databasen. Kjør scripts/insert_demo_weapon.py først.",
            )
            return
        rifle_id = demo[0]["id"]
        dlg = WeaponProfileDialog(db=self.db, rifle_id=rifle_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.update_rifle_list()
            # Reselect demo item if still present
            for i in range(self.rifle_select.count()):
                if self.rifle_select.itemData(i) == rifle_id:
                    self.rifle_select.setCurrentIndex(i)
                    break

    def show_optic_settings(self):
        # ...vis nullpunkt, innstillinger og historikk for valgt optikk...
        pass

    def load_display_options(self):
        if os.path.exists(self.display_options_file):
            with open(self.display_options_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for k, cb in self.display_options.items():
                cb.setChecked(saved.get(k, True))

    def save_display_options(self):
        opts = {k: cb.isChecked() for k, cb in self.display_options.items()}
        with open(self.display_options_file, "w", encoding="utf-8") as f:
            json.dump(opts, f)

    def update_display(self):
        self.save_display_options()
        self.show_ballistics()

    def show_optic_graph(self):
        # Dummy historikkdata
        optics = ["Swarovski", "Zeiss", "Leupold"]
        clicks = [0, 5, -3]
        fig, ax = plt.subplots()
        ax.bar(optics, clicks)
        ax.set_ylabel("Klikk-differanse")
        ax.set_title("Optikkhistorikk og klikkjusteringer")
        canvas = FigureCanvas(fig)
        self.layout().addWidget(canvas)
        pass

    def open_ai_helper(self):
        dlg = AIWeaponProfileHelperDialog(self)
        dlg.exec()

    def show_ballistics(self):
        barrel = self.barrel_select.currentText()
        caliber = self.caliber_select.currentText()
        selected = [k for k, cb in self.display_options.items() if cb.isChecked()]
        result = f"Ballistisk analyse for {barrel}, {caliber}:\n"
        if "Klikktabell" in selected:
            result += "Klikktabell: ...\n"
        if "Ballistisk kurve" in selected:
            result += "Ballistisk kurve: ...\n"
        if "Vindavdrift" in selected:
            result += "Vindavdrift: ...\n"
        if "Energi" in selected:
            result += "Energi: ...\n"
        if "Hastighet" in selected:
            result += "Hastighet: ...\n"
        self.ballistics_result.setText(result)
        # ...vis grafer og analyser basert på valg...
        pass

    def toggle_simple_mode(self):
        simple = self.simple_mode.isChecked()
        for k, cb in self.display_options.items():
            cb.setVisible(not simple)
        self.update_display_btn.setVisible(not simple)
        # Skjul avanserte grafer og data hvis enkel modus er valgt
        if simple:
            self.ballistics_result.setText(
                "Ballistisk analyse: Klikktabell og grunnleggende data"
            )
        else:
            self.show_ballistics()


class AIWeaponProfileHelperDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI veileder for våpenprofil")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.search_input = QLineEdit()
        self.search_btn = QPushButton("Søk og autofyll")
        self.search_btn.clicked.connect(self.search_and_fill)
        self.result_label = QLabel()
        layout.addWidget(QLabel("Søk etter løpsinnfestning, profil osv:"))
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_btn)
        layout.addWidget(self.result_label)

    def search_and_fill(self):
        query = self.search_input.text()
        # ...her kobles til AI backend for å hente og foreslå data...
        # Eksempel: Foreslå "threaded, 1-16 gjenger, 4 festeskruer, bedding: glass" osv.
        self.result_label.setText(f"AI forslag: (placeholder for {query})")
        # ...her kan du autofylle felter i våpenprofilen...
        pass


class DisplayOptionsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.options = {
            "Ballistisk kurve": QCheckBox("Ballistisk kurve"),
            "Klikktabell": QCheckBox("Klikktabell"),
            "Optikkhistorikk": QCheckBox("Optikkhistorikk"),
            "Testdata": QCheckBox("Testdata"),
            "Batchstatistikk": QCheckBox("Batchstatistikk"),
        }
        for cb in self.options.values():
            cb.setChecked(True)
            layout.addWidget(cb)
        self.apply_btn = QPushButton("Bruk valg")
        self.apply_btn.clicked.connect(self.apply_options)
        layout.addWidget(self.apply_btn)
        self.ai_chat_btn = QPushButton("AI chat og veiledning")
        self.ai_chat_btn.clicked.connect(self.open_ai_chat)
        layout.addWidget(self.ai_chat_btn)

    def apply_options(self):
        # ...vis/skjul moduler basert på brukerens valg...
        pass

    def open_ai_chat(self):
        # ...åpne AI chat for råd og veiledning...
        self.chat_dialog = AIChatDialog(self)
        self.chat_dialog.show()


class AIChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI chat og veiledning")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.question_input = QLineEdit()
        self.ask_btn = QPushButton("Spør AI")
        self.ask_btn.clicked.connect(self.ask_ai)
        self.answer_label = QLabel()
        layout.addWidget(QLabel("Skriv ditt spørsmål:"))
        layout.addWidget(self.question_input)
        layout.addWidget(self.ask_btn)
        layout.addWidget(self.answer_label)

    def ask_ai(self):
        _question = self.question_input.text()
        # ...koble til AI backend, få svar...
        self.answer_label.setText("AI svar: (placeholder)")
        pass


class WeaponDashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Våpen- og testdashboard"))
        self.weapon_select = QComboBox()
        layout.addWidget(QLabel("Velg våpen:"))
        layout.addWidget(self.weapon_select)
        self.test_select = QComboBox()
        layout.addWidget(QLabel("Velg test:"))
        layout.addWidget(self.test_select)
        self.show_graph_btn = QPushButton("Vis grafer")
        self.show_graph_btn.clicked.connect(self.show_graphs)
        layout.addWidget(self.show_graph_btn)
        self.graph_canvas = None

    def show_graphs(self):
        # Dummy data for eksempel
        x = [100, 200, 300, 400, 500]
        y_grouping = [30, 25, 20, 18, 15]  # Treffgruppe diameter
        y_velocity = [820, 800, 780, 765, 750]  # Utgangshastighet
        fig, ax = plt.subplots()
        ax.plot(x, y_grouping, label="Treffgruppe (mm)", marker="o")
        ax.plot(x, y_velocity, label="Utgangshastighet (m/s)", marker="x")
        ax.set_xlabel("Avstand (m)")
        ax.set_title("Testresultater")
        ax.legend()
        if self.graph_canvas:
            self.layout().removeWidget(self.graph_canvas)
            self.graph_canvas.deleteLater()
        self.graph_canvas = FigureCanvas(fig)
        self.layout().addWidget(self.graph_canvas)
        fig.tight_layout()


class ReportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Rapportmodul"))
        self.export_pdf_btn = QPushButton("Eksporter rapport til PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        layout.addWidget(self.export_pdf_btn)
        self.content_options = {
            "Grafer": QCheckBox("Grafer"),
            "Tabeller": QCheckBox("Tabeller"),
            "Testdata": QCheckBox("Testdata"),
            "Ballistikk": QCheckBox("Ballistikk"),
        }
        for cb in self.content_options.values():
            cb.setChecked(True)
            layout.addWidget(cb)
        self.filetype_select = QComboBox()
        self.filetype_select.addItems(["PDF", "Word", "Excel"])
        layout.addWidget(QLabel("Velg filtype:"))
        layout.addWidget(self.filetype_select)
        self.export_btn = QPushButton("Eksporter rapport")
        self.export_btn.clicked.connect(self.export_report)
        layout.addWidget(self.export_btn)

    def export_report(self):
        filetype = self.filetype_select.currentText()
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Lagre {filetype}", "", f"{filetype} Files (*.{filetype.lower()})"
        )
        if not file_path:
            return
        selected = [k for k, cb in self.content_options.items() if cb.isChecked()]
        data = {
            "Avstand": [100, 200, 300],
            "Treffgruppe": [30, 25, 20],
            "Hastighet": [820, 800, 780],
        }
        fallback = False
        if filetype == "PDF":
            fig = plt.figure()
            plt.plot(data["Avstand"], data["Treffgruppe"])
            plt.title("Treffgruppe")
            with PdfPages(file_path) as pdf:
                pdf.savefig(fig)
            plt.close(fig)
        elif filetype == "Word":
            if importlib.util.find_spec("docx") is None:
                QMessageBox.warning(
                    self,
                    "Word ikke tilgjengelig",
                    "Word-eksport krever python-docx. Eksporterer som PDF i stedet.",
                )
                filetype = "PDF"
                fallback = True
            else:
                from docx import Document

                doc = Document()
                doc.add_heading("Rapport", 0)
                if "Tabeller" in selected:
                    table = doc.add_table(rows=1, cols=len(data))
                    hdr_cells = table.rows[0].cells
                    for i, key in enumerate(data.keys()):
                        hdr_cells[i].text = key
                    for i in range(len(data["Avstand"])):
                        row_cells = table.add_row().cells
                        for j, key in enumerate(data.keys()):
                            row_cells[j].text = str(data[key][i])
                doc.save(file_path)
        elif filetype == "Excel":
            if importlib.util.find_spec("pandas") is None:
                QMessageBox.warning(
                    self,
                    "Excel ikke tilgjengelig",
                    "Excel-eksport krever pandas. Eksporterer som PDF i stedet.",
                )
                filetype = "PDF"
                fallback = True
            else:
                import pandas as pd

                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)
        if fallback:
            # PDF fallback
            fig = plt.figure()
            plt.plot(data["Avstand"], data["Treffgruppe"])
            plt.title("Treffgruppe")
            with PdfPages(file_path) as pdf:
                pdf.savefig(fig)
            plt.close(fig)
        QMessageBox.information(self, "Eksport", f"Rapport lagret til {file_path}")

    def export_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lagre PDF", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return
        # Eksempel: lagre matplotlib-figur til PDF
        fig = plt.figure()
        plt.plot([1, 2, 3], [4, 5, 6])
        plt.title("Eksempelrapport")
        with PdfPages(file_path) as pdf:
            pdf.savefig(fig)
        plt.close(fig)
        QMessageBox.information(self, "PDF eksport", f"Rapport lagret til {file_path}")


class OnboardingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.steps = [
            "Velkommen til Hjemmelading!",
            "Steg 1: Opprett våpenprofil og legg inn kaliber.",
            "Steg 2: Registrer kuler, krutt og hylser i lageret.",
            "Steg 3: Utforsk ballistikk og preppingmoduler.",
            "Steg 4: Kjør tester og se grafer på dashboardet.",
            "Steg 5: Eksporter rapporter og del med andre.",
            "Trenger du hjelp? Klikk på hjelpetekst eller AI chat!",
        ]
        self.step_index = 0
        self.step_label = QLabel(self.steps[self.step_index])
        layout.addWidget(self.step_label)
        self.next_btn = QPushButton("Neste steg")
        self.next_btn.clicked.connect(self.next_step)
        layout.addWidget(self.next_btn)
        self.help_btn = QPushButton("Hjelpetekst")
        self.help_btn.clicked.connect(self.show_help)
        layout.addWidget(self.help_btn)

    def next_step(self):
        self.step_index += 1
        if self.step_index < len(self.steps):
            self.step_label.setText(self.steps[self.step_index])
        else:
            self.step_label.setText("Onboarding fullført!")
            self.next_btn.setEnabled(False)

    def show_help(self):
        QMessageBox.information(
            self,
            "Hjelpetekst",
            "Her finner du tips og forklaringer til hvert steg. Du kan også bruke AI chat for mer hjelp.",
        )


class ResponsiveHelper:
    """
    Hjelpeklasse for responsiv design og mobilvennlig UI.
    Kan brukes til å tilpasse widgets og layout for mobil/nettbrett.
    """

    @staticmethod
    def apply_responsive(widget):
        # Eksempel: juster fontstørrelse og knappestørrelse for mobil
        widget.setStyleSheet("font-size: 16px; padding: 10px;")
        # ...utvid med flere mobilvennlige tilpasninger...


# Eksempel på bruk:
# ResponsiveHelper.apply_responsive(some_widget)

# For API-integrasjon:
# def get_api_data(endpoint):
#     # Placeholder for fremtidig API-kall
#     pass


class ExternalDeviceAPI:
    """
    API-modul for eksterne systemer og sensorer.
    Støtter sending av ballistiske data til Leica Rangemaster, vindmålere og avstandsmålere.
    """

    @staticmethod
    def send_ballistics_to_leica(data):
        # Placeholder: send data til Leica via Bluetooth, USB eller app
        # Eksempel: data = {"range": 400, "clicks": 12, "wind": 2.5}
        logger.info("Sender til Leica: %s", data)
        # ...her kan du implementere Bluetooth/serial kommunikasjon...
        return True

    @staticmethod
    def send_to_windmeter(data):
        # Placeholder for vindmåler-integrasjon
        logger.info("Sender til vindmåler: %s", data)
        return True

    @staticmethod
    def send_to_rangefinder(data):
        # Placeholder for avstandsmåler-integrasjon
        logger.info("Sender til avstandsmåler: %s", data)
        return True


class ExternalDeviceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Send ballistiske data til eksterne enheter:"))
        self.range_input = QSpinBox()
        self.range_input.setRange(0, 3000)
        self.wind_input = QDoubleSpinBox()
        self.wind_input.setRange(0, 50)
        self.clicks_input = QSpinBox()
        self.clicks_input.setRange(-100, 100)
        layout.addWidget(QLabel("Avstand (m):"))
        layout.addWidget(self.range_input)
        layout.addWidget(QLabel("Vind (m/s):"))
        layout.addWidget(self.wind_input)
        layout.addWidget(QLabel("Klikk (høyde):"))
        layout.addWidget(self.clicks_input)
        self.send_leica_btn = QPushButton("Send til Leica")
        self.send_leica_btn.clicked.connect(self.send_leica)
        layout.addWidget(self.send_leica_btn)
        self.send_wind_btn = QPushButton("Send til vindmåler")
        self.send_wind_btn.clicked.connect(self.send_wind)
        layout.addWidget(self.send_wind_btn)
        self.send_rangefinder_btn = QPushButton("Send til avstandsmåler")
        self.send_rangefinder_btn.clicked.connect(self.send_rangefinder)
        layout.addWidget(self.send_rangefinder_btn)

    def send_leica(self):
        data = {
            "range": self.range_input.value(),
            "wind": self.wind_input.value(),
            "clicks": self.clicks_input.value(),
        }
        ExternalDeviceAPI.send_ballistics_to_leica(data)
        QMessageBox.information(self, "Sendt", "Data sendt til Leica!")

    def send_wind(self):
        data = {"wind": self.wind_input.value()}
        ExternalDeviceAPI.send_to_windmeter(data)
        QMessageBox.information(self, "Sendt", "Data sendt til vindmåler!")

    def send_rangefinder(self):
        data = {"range": self.range_input.value()}
        ExternalDeviceAPI.send_to_rangefinder(data)
        QMessageBox.information(self, "Sendt", "Data sendt til avstandsmåler!")


class StyleHelper:
    """
    Felles stilark og design for hele programmet.
    Brukes til å sikre konsistent utseende og layout.
    """

    @staticmethod
    def apply_style(widget):
        widget.setStyleSheet(
            """
            QWidget {
                font-family: Arial, sans-serif;
                font-size: 14px;
                background: #f8f8f8;
                color: #222;
            }
            QPushButton {
                background: #2d5c88;
                color: #fff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QCheckBox {
                font-size: 13px;
            }
            QLabel {
                font-size: 14px;
            }
        """
        )
        # ...utvid med flere stilvalg etter behov...
