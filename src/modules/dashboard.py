"""
Dashboard
Oversikt over lagerstatus, nylige aktiviteter og statistikk
"""

# Temporary: duplicate definitions were present; deduplicated selectively

import json
from datetime import datetime, timedelta

from ..database.database import get_database
from ..logging_config import configure_logging, get_logger
from ..qt_compat import QPixmap, Qt, QtWidgets
from ..ui.modern_card import ModernCard
from ..utils.i18n import get_current_language, tr
from ..utils.optional_deps import Figure as Figure

QCheckBox = QtWidgets.QCheckBox
QComboBox = QtWidgets.QComboBox
QDialog = QtWidgets.QDialog
QDoubleSpinBox = QtWidgets.QDoubleSpinBox
QFileDialog = QtWidgets.QFileDialog
QGroupBox = QtWidgets.QGroupBox
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QListWidget = QtWidgets.QListWidget
QMessageBox = QtWidgets.QMessageBox
QPushButton = QtWidgets.QPushButton
QScrollArea = QtWidgets.QScrollArea
QSpinBox = QtWidgets.QSpinBox
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QTextEdit = QtWidgets.QTextEdit
QVBoxLayout = QtWidgets.QVBoxLayout
QWidget = QtWidgets.QWidget

configure_logging()
logger = get_logger(__name__)


class DisplayOptionsWidget(QWidget):
    """Simple display-options panel for the dashboard (checkbox toggles)."""

    _DEFAULTS = {
        "show_recent_activity": True,
        "show_quick_tips": True,
        "show_stats": True,
        "show_ammo_comparison": True,
        "show_batch_analysis": True,
    }
    _LABELS = {
        "show_recent_activity": "Nylig aktivitet",
        "show_quick_tips": "Hurtigtips",
        "show_stats": "Statistikk",
        "show_ammo_comparison": "Ammo-sammenligning",
        "show_batch_analysis": "Batch-analyse",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.options: dict = {}
        for key, label in self._LABELS.items():
            cb = QCheckBox(label, self)
            cb.setChecked(self._DEFAULTS.get(key, True))
            self.options[key] = cb
            layout.addWidget(cb)
        layout.addStretch()

    def get_state(self) -> dict:
        return {key: cb.isChecked() for key, cb in self.options.items()}

    def set_state(self, state: dict) -> None:
        for key, cb in self.options.items():
            if key in state:
                cb.setChecked(bool(state[key]))


class Dashboard(QWidget):
    def create_ai_tips_widget(self):
        widget = QGroupBox("Guidance Tips and Load Match", self)
        widget.setProperty("variant", "panel")
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.ai_input = QLineEdit(widget)
        self.ai_input.setPlaceholderText("Ask about ammo, batches, or test results...")
        layout.addWidget(self.ai_input)
        ai_btn = QPushButton("Get Guidance", widget)
        ai_btn.clicked.connect(self.get_ai_tip)
        layout.addWidget(ai_btn)
        self.ai_output = QTextEdit(widget)
        self.ai_output.setReadOnly(True)
        layout.addWidget(self.ai_output)
        # Demo: show the strongest load match from local test history.
        best = self.get_best_ammo()
        if best:
            layout.addWidget(
                QLabel(
                    f"Best load: {best['ammo']} batch {best['batch']} ({best['group']} mm group)",
                    widget,
                )
            )
        return widget

    def get_ai_tip(self):
        question = self.ai_input.text().strip()
        lots = getattr(self, "test_history", [])
        if not question:
            self.ai_output.setText("Enter a question first.")
            return
        question_lower = question.lower()
        if any(
            keyword in question_lower
            for keyword in ("precision", "presisjon", "accuracy")
        ):
            best = self.get_best_ammo()
            if best:
                self.ai_output.setText(
                    f"Best precision: {best['ammo']} batch {best['batch']} with a {best['group']} mm group."
                )
            else:
                self.ai_output.setText("No precision test data available.")
        elif any(
            keyword in question_lower for keyword in ("velocity", "hastighet", "speed")
        ):
            fastest = sorted(
                lots, key=lambda e: float(e.get("velocity", 0)), reverse=True
            )[:1]
            if fastest:
                self.ai_output.setText(
                    f"Highest velocity: {fastest[0]['ammo']} batch {fastest[0]['batch']} at {fastest[0]['velocity']} fps."
                )
            else:
                self.ai_output.setText("No velocity test data available.")
        elif any(
            keyword in question_lower
            for keyword in ("recommend", "anbefal", "match", "suggest")
        ):
            best = self.get_best_ammo()
            if best:
                self.ai_output.setText(
                    f"Recommended load: {best['ammo']} batch {best['batch']} ({best['group']} mm group)."
                )
            else:
                self.ai_output.setText("No recommendation data available.")
        else:
            self.ai_output.setText(
                "Ask about precision, velocity, recommendations, or matching."
            )

    def get_best_ammo(self):
        lots = getattr(self, "test_history", [])
        if not lots:
            return None
        best = sorted(lots, key=lambda e: float(e.get("group", 9999)))[:1]
        return best[0] if best else None

    def load_dashboard_profile(self):
        import json

        fname, _ = QFileDialog.getOpenFileName(
            self, "Load dashboard layout", "", "JSON files (*.json)"
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

    def save_dashboard_profile(self):
        from PyQt6.QtWidgets import QFileDialog

        fname, _ = QFileDialog.getSaveFileName(
            self, "Save dashboard layout", "", "JSON files (*.json)"
        )
        if not fname:
            return

        display_state = {}
        if hasattr(self, "display_options"):
            if hasattr(self.display_options, "get_state"):
                display_state = self.display_options.get_state()
            elif hasattr(self.display_options, "options"):
                display_state = {
                    key: cb.isChecked()
                    for key, cb in self.display_options.options.items()
                }

        profile = {
            "display_options": display_state,
            "favorites": getattr(self, "favorites", []),
            "test_history": getattr(self, "test_history", []),
        }
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=True, indent=2)

    def update_dashboard_widgets(self):
        # Oppdater dashboard-widgets basert på profil
        pass

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.current_language = get_current_language() or "en"
        self.init_ui()

    def init_ui(self):
        # ...existing code...
        # ...existing code...
        # Scroll area for å håndtere mye innhold
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget(self)
        layout = QVBoxLayout()
        container.setLayout(layout)
        scroll.setWidget(container)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(scroll)

        # Hero + key stats
        layout.addWidget(self.create_hero_section())

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

        layout.addWidget(self.create_inventory_status())
        layout.addWidget(self.create_recent_activity())
        layout.addWidget(self.create_quick_tips())

        # Test insights
        layout.addWidget(self.create_quick_stats_widget())
        layout.addWidget(self.create_ammo_comparison_widget())
        layout.addWidget(self.create_batch_analysis_widget())

        self.display_options = DisplayOptionsWidget(self)
        layout.addWidget(self.display_options)

        actions = QHBoxLayout()
        save_btn = QPushButton("Save dashboard layout")
        save_btn.clicked.connect(self.save_dashboard_profile)
        actions.addWidget(save_btn)
        load_btn = QPushButton("Load dashboard layout")
        load_btn.clicked.connect(self.load_dashboard_profile)
        actions.addWidget(load_btn)
        layout.addLayout(actions)

        layout.addWidget(self.create_ai_tips_widget())
        layout.addWidget(self.create_image_analysis_widget())

        layout.addStretch()

    def create_quick_stats_widget(self):
        widget = QGroupBox("Quick Statistics", self)
        widget.setProperty("variant", "panel")
        layout = QHBoxLayout()
        widget.setLayout(layout)
        lots = getattr(self, "test_history", [])
        if not lots:
            layout.addWidget(QLabel("No test data available.", widget))
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
            QLabel(
                f"Best group: {best_group if best_group is not None else '-'} mm",
                widget,
            )
        )
        layout.addWidget(QLabel(f"Average MOA: {avg_moa}", widget))
        layout.addWidget(QLabel(f"Total hits: {total_hits}", widget))
        return widget

    def create_ammo_comparison_widget(self):
        widget = QGroupBox("Ammo Comparison", self)
        widget.setProperty("variant", "panel")
        layout = QVBoxLayout()
        widget.setLayout(layout)
        lots = getattr(self, "test_history", [])
        if not lots:
            layout.addWidget(QLabel("No test data available.", widget))
            return widget
        # Sammenlign ammo på gruppe og MOA
        ammo_stats = {}
        for e in lots:
            ammo = e.get("ammo", "Unknown")
            if ammo not in ammo_stats:
                ammo_stats[ammo] = {"groups": [], "moas": []}
            if e.get("group_size_mm"):
                ammo_stats[ammo]["groups"].append(float(e["group_size_mm"]))
            if e.get("moa"):
                ammo_stats[ammo]["moas"].append(float(e["moa"]))
        table = QTableWidget(widget)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Ammo", "Avg Group (mm)", "Avg MOA"])
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
        widget = QGroupBox("Batch Analysis")
        widget.setProperty("variant", "panel")
        layout = QVBoxLayout()
        widget.setLayout(layout)
        lots = getattr(self, "test_history", [])
        if not lots:
            layout.addWidget(QLabel("No batch data available."))
            return widget

        # Vis batcher med bildeanalyse og statistikk
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["Batch", "Ammo", "Group (mm)", "MOA", "Hits", "Image"]
        )
        table.setRowCount(len(lots))
        for i, e in enumerate(lots):
            table.setItem(i, 0, QTableWidgetItem(str(e.get("batch", ""))))
            table.setItem(i, 1, QTableWidgetItem(str(e.get("ammo", ""))))
            table.setItem(i, 2, QTableWidgetItem(str(e.get("group_size_mm", ""))))
            table.setItem(i, 3, QTableWidgetItem(str(e.get("moa", ""))))
            table.setItem(i, 4, QTableWidgetItem(str(e.get("shot_count", ""))))
            table.setItem(i, 5, QTableWidgetItem(str(e.get("img", ""))))

        layout.addWidget(table)
        return widget

    from PyQt6.QtGui import QPixmap

    def create_image_analysis_widget(self):
        widget = QGroupBox("Automatic Image Analysis: Group, MOA, Hits")
        widget.setProperty("variant", "panel")
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
            layout.addWidget(QLabel("No analyzed images were found in test history."))
            return widget
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Ammo", "Batch", "Group (mm)", "MOA", "Hits"])
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
        """Create the hero section for the load guidance flow."""
        group = QGroupBox()
        group.setProperty("variant", "panel")

        layout = QVBoxLayout()
        group.setLayout(layout)

        # Title
        title = QLabel("Load Guidance")
        title.setProperty("variant", "heroTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Evidence-driven load guidance from first setup to expert tuning\n"
            "Select rifle -> select purpose -> review the recommended path"
        )
        subtitle.setProperty("variant", "heroSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Features
        features_layout = QHBoxLayout()

        feature1 = QLabel("Analyzes\nhistory")
        feature1.setProperty("variant", "cardSubtitle")
        feature1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(feature1)

        feature2 = QLabel("Optimizes for\npurpose")
        feature2.setProperty("variant", "cardSubtitle")
        feature2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(feature2)

        feature3 = QLabel("Evidence-based\nrecommendations")
        feature3.setProperty("variant", "cardSubtitle")
        feature3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(feature3)

        feature4 = QLabel("Step-by-step\nguidance")
        feature4.setProperty("variant", "cardSubtitle")
        feature4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(feature4)

        layout.addLayout(features_layout)

        # Big CTA button
        btn_start = QPushButton("Start Load Guidance Wizard")
        btn_start.setProperty("variant", "primary")
        btn_start.setProperty("size", "lg")
        btn_start.clicked.connect(self.launch_wizard)
        layout.addWidget(btn_start)

        return group

    def launch_wizard(self):
        """Start the load guidance wizard."""
        from .smart_loading_wizard import SmartLoadingWizard

        self.wizard = SmartLoadingWizard(self)
        self.wizard.show()

    def create_inventory_status(self):
        """Lager lagerstatus-oversikt"""
        group = QGroupBox(tr("dashboard_inventory_status", self.current_language))
        group.setProperty("variant", "panel")
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
            status.setProperty("variant", "successText")
            layout.addWidget(status)
        else:
            # Advarsler
            if low_powder:
                warning = QLabel(
                    f"{len(low_powder)} powders are low in stock (< 500 g)"
                )
                warning.setProperty("variant", "warningText")
                layout.addWidget(warning)

            if low_bullets:
                warning = QLabel(
                    f"{len(low_bullets)} bullets are low in stock (< 100 pcs)"
                )
                warning.setProperty("variant", "warningText")
                layout.addWidget(warning)

            if low_primers:
                warning = QLabel(
                    f"{len(low_primers)} primers are low in stock (< 100 pcs)"
                )
                warning.setProperty("variant", "warningText")
                layout.addWidget(warning)

            if worn_cases:
                warning = QLabel(
                    f"{len(worn_cases)} cases have been fired more than 5 times (consider sorting them out)"
                )
                warning.setProperty("variant", "warningText")
                layout.addWidget(warning)

        return group

    def create_recent_activity(self):
        """Viser nylige aktiviteter"""
        group = QGroupBox(tr("dashboard_recent_activity", self.current_language))
        group.setProperty("variant", "panel")
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
            no_activity.setProperty("role", "muted")
            no_activity.setProperty("emphasis", "placeholder")
            layout.addWidget(no_activity)
        else:
            # Ladeøkter
            if loading_sessions:
                layout.addWidget(QLabel("<b>Loading Sessions:</b>"))
                for session in loading_sessions:
                    ammo_name = "Unknown"
                    if session["ammo_profile_id"]:
                        ammo = self.db.get_by_id(
                            "ammo_profiles", session["ammo_profile_id"]
                        )
                        if ammo:
                            ammo_name = ammo["name"]

                    item = QLabel(
                        f"{session['date']}: {session['quantity']} pcs {ammo_name}"
                    )
                    layout.addWidget(item)

            # Skyteøkter
            if shooting_sessions:
                layout.addWidget(QLabel("<b>Shooting Sessions:</b>"))
                for session in shooting_sessions:
                    rifle_name = "Unknown"
                    if session["rifle_id"]:
                        rifle = self.db.get_by_id("rifles", session["rifle_id"])
                        if rifle:
                            rifle_name = rifle["name"]

                    item = QLabel(
                        f"{session['date']}: {rifle_name} - {session['rounds_fired']} shots"
                    )
                    layout.addWidget(item)

            # Ladder tests
            if ladder_tests:
                layout.addWidget(QLabel("<b>Ladder Tests:</b>"))
                for test in ladder_tests:
                    item = QLabel(f"{test['date']}: {test['name']}")
                    layout.addWidget(item)

        return group

    def create_quick_tips(self):
        """Viser nyttige tips"""
        group = QGroupBox(tr("dashboard_quick_tips", self.current_language))
        group.setProperty("variant", "panel")
        layout = QVBoxLayout()
        group.setLayout(layout)

        tips = [
            "Use <b>Zero Shift Calculator</b> (Tools menu) to calculate optic adjustments when switching ammunition",
            "Always start at the minimum charge and work upward gradually",
            "Document every loading session carefully; it pays off later",
            "Always keep track of how many times your brass has been fired",
            "Test new loads at 100 m before moving to longer distances",
            "Use Ladder Test to find optimal powder charges",
            "Check inventory regularly and order components in good time",
        ]

        import random

        tip = random.choice(tips)

        tip_label = QLabel(tip)
        tip_label.setWordWrap(True)
        tip_label.setProperty("variant", "callout")
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


# AmmoTestReport, AmmoTestReportUI, AmmoTestReportDialog moved to src/ammo_test/ (2026-04-21)
