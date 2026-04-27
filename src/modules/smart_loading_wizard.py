"""
Load guidance wizard.
Analyzes rifle, purpose, and history to build a practical recommendation.
"""

import json
from datetime import datetime
from typing import Dict, Optional

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from ..database.database import get_database
from ..tools.load_development_session_service import (
    create_load_development_session,
    link_legacy_loading_session,
)
from ..tools.load_session_runtime_service import store_workflow_context_in_settings
from ..utils.barrel_configuration import resolve_active_barrel_configuration_context
from ..utils.cartridge_standard_support import build_cartridge_standard_audit
from ..utils.drag_models import parse_bc_segments


def _load_rifle_profile_details_for_wizard(db, rifle_id: int | None) -> Dict:
    if rifle_id in (None, ""):
        return {}
    try:
        rows = db.execute_query(
            "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
            (rifle_id,),
        )
    except Exception:
        return {}
    if not rows or not rows[0].get("profile_json"):
        return {}
    try:
        parsed = json.loads(rows[0]["profile_json"])
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _get_available_wizard_barrel_configurations(
    db,
    rifle_id: int | None,
    rifle_data: Dict | None = None,
) -> list[Dict]:
    details = _load_rifle_profile_details_for_wizard(db, rifle_id)
    active_barrel_id = str(details.get("active_barrel_id") or "").strip() or None
    configurations = details.get("barrel_configurations", [])
    matching: list[Dict] = []
    if isinstance(configurations, list):
        for configuration in configurations:
            if not isinstance(configuration, dict):
                continue
            configuration_barrel_id = (
                str(configuration.get("barrel_id") or "").strip() or None
            )
            if (
                active_barrel_id
                and configuration_barrel_id
                and configuration_barrel_id != active_barrel_id
            ):
                continue
            if active_barrel_id and not configuration_barrel_id:
                continue
            matching.append(dict(configuration))
    if matching:
        return matching

    fallback = resolve_active_barrel_configuration_context(
        db,
        rifle_id,
        rifle_data=rifle_data,
        profile_details=details,
    )
    fallback_id = str(fallback.get("barrel_configuration_id") or "").strip() or None
    fallback_name = str(fallback.get("barrel_configuration_name") or "").strip() or None
    if not fallback_id and not fallback_name:
        return []
    return [
        {
            "id": fallback_id or "current-setup",
            "name": fallback_name or fallback_id or "Current setup",
            "barrel_id": fallback.get("barrel_id"),
            "barrel_name": fallback.get("barrel_name"),
            "derived": True,
        }
    ]


def _resolve_wizard_barrel_configuration_context(
    db,
    rifle_id: int | None,
    *,
    rifle_data: Dict | None = None,
    selected_configuration_id: str | None = None,
    selected_configuration_name: str | None = None,
) -> Dict:
    details = _load_rifle_profile_details_for_wizard(db, rifle_id)
    if selected_configuration_id:
        details = dict(details)
        details["active_barrel_configuration_id"] = selected_configuration_id
    if selected_configuration_name:
        details = dict(details)
        details["active_barrel_configuration_name"] = selected_configuration_name
    return resolve_active_barrel_configuration_context(
        db,
        rifle_id,
        rifle_data=rifle_data,
        profile_details=details,
    )


def _preferred_bc_for_scoring(load_data: Dict) -> float | None:
    segments = parse_bc_segments(load_data.get("bc_segments_json"))
    if segments:
        first = segments[0]
        bc_value = first.get("bc_g7") or first.get("bc_g1") or first.get("bc")
        if isinstance(bc_value, (int, float)):
            return float(bc_value)
    bc_g7 = load_data.get("bc_g7")
    if isinstance(bc_g7, (int, float)) and bc_g7 > 0:
        return float(bc_g7)
    bc_g1 = load_data.get("bc_g1")
    if isinstance(bc_g1, (int, float)) and bc_g1 > 0:
        return float(bc_g1)
    return None


def _format_bullet_label(bullet: Dict) -> str:
    label = f"{bullet['name']} - {bullet['weight_grains']}gr"
    segments = parse_bc_segments(bullet.get("bc_segments_json"))
    if segments:
        first = segments[0]
        bc_value = first.get("bc_g7") or first.get("bc_g1") or first.get("bc")
        min_v = first.get("velocity_fps_min")
        max_v = first.get("velocity_fps_max")
        if isinstance(bc_value, (int, float)):
            if max_v is not None:
                label += f" (Segmented BC: {float(bc_value):.3f} @ {float(min_v or 0):.0f}-{float(max_v):.0f} fps)"
            else:
                label += f" (Segmented BC: {float(bc_value):.3f} @ {float(min_v or 0):.0f}+ fps)"
        return label
    if bullet.get("bc_g7"):
        label += f" (G7: {bullet['bc_g7']})"
    elif bullet.get("bc_g1"):
        label += f" (G1: {bullet['bc_g1']})"
    return label


class PurposeProfile:
    """Profiles for different load-development use cases."""

    PROFILES = {
        "jakt": {
            "name": "Hunting",
            "description": "Balanced for terminal energy, expansion, and field accuracy.",
            "priority": {
                "energy": 40,  # Terminal energy viktig
                "accuracy": 30,  # God presisjon
                "velocity": 20,  # Flat trajectory
                "consistency": 10,  # ES/SD mindre kritisk
            },
            "min_energy_ftlbs": 1000,  # Minimum energy @ 300m
            "max_range_m": 400,
            "target_velocity_fps": 2700,
            "tips": [
                "Choose expanding bullets such as Nosler Partition or Barnes TTSX.",
                "Prioritize controlled expansion over extreme BC.",
                "Test at realistic hunting distances such as 100-300 m.",
                "Verify zero at expected hunting temperatures.",
            ],
        },
        "langhold": {
            "name": "Long Range / PRS",
            "description": "Optimized for precision and external ballistics at extended distance.",
            "priority": {
                "accuracy": 35,  # Sub-MOA critical
                "consistency": 35,  # Low ES/SD critical
                "bc": 20,  # Høy BC for vindrift
                "velocity": 10,  # Moderate velocity OK
            },
            "min_bc_g7": 0.25,
            "max_es_fps": 15,
            "target_group_moa": 0.5,
            "max_range_m": 1200,
            "tips": [
                "Favor high-BC bullets such as Berger or Hornady ELD.",
                "Low ES and SD are critical, so test 10+ rounds.",
                "Identify the most stable node during ladder testing.",
                "Verify drop data beyond 600 m.",
            ],
        },
        "presisjon": {
            "name": "Precision / Benchrest",
            "description": "Pure accuracy focus where group size dominates every tradeoff.",
            "priority": {
                "accuracy": 60,  # Accuracy is everything
                "consistency": 30,  # ES/SD important
                "velocity": 5,  # Velocity doesn't matter
                "bc": 5,  # BC doesn't matter
            },
            "target_group_moa": 0.25,
            "max_es_fps": 10,
            "max_range_m": 300,
            "tips": [
                "Use match-grade bullets such as Berger Hybrid or Lapua Scenar.",
                "Maintain extremely consistent neck tension.",
                'Hold seating depth consistency to about 0.001".',
                "Use wind flags when evaluating groups.",
            ],
        },
        "blink": {
            "name": "Practical / IPSC Rifle",
            "description": "Balanced for speed, controllability, and useful accuracy.",
            "priority": {
                "velocity": 30,  # Fast for quick splits
                "accuracy": 30,  # Good enough accuracy
                "recoil": 25,  # Low recoil = faster
                "consistency": 15,  # Some ES OK
            },
            "min_velocity_fps": 2600,
            "max_recoil_ftlbs": 18,
            "target_group_moa": 1.5,  # IPSC targets are big
            "max_range_m": 400,
            "tips": [
                "Use moderate bullet weights for the cartridge.",
                "Favor powder choices that keep recoil manageable.",
                "Set the rifle up for fast recovery between shots.",
                "Test rapid-fire strings, not only slow-fire groups.",
            ],
        },
        "plinking": {
            "name": "Training / Plinking",
            "description": "Low-cost, reliable, low-wear loads for volume shooting.",
            "priority": {
                "cost": 40,  # Cheap is good
                "consistency": 30,  # Reliable feeding
                "barrel_life": 20,  # Low pressure = long life
                "velocity": 10,  # Speed not important
            },
            "max_cost_per_round": 5.0,  # NOK
            "max_pressure_pct": 85,
            "target_group_moa": 2.0,
            "tips": [
                "Use affordable FMJ bullets where appropriate.",
                "Stay with moderate charges rather than chasing max velocity.",
                "Buy bulk components when lot consistency is acceptable.",
                "Optimize for volume and reliability before precision.",
            ],
        },
    }

    @staticmethod
    def get_profile(purpose: str) -> Dict:
        """Hent profil for gitt formål"""
        return PurposeProfile.PROFILES.get(purpose, PurposeProfile.PROFILES["jakt"])

    @staticmethod
    def score_load(purpose: str, load_data: Dict) -> float:
        """
        Scorer en ladning basert på formål
        Returns: Score 0-100
        """
        profile = PurposeProfile.get_profile(purpose)
        priorities = profile["priority"]

        score = 0.0

        # Accuracy scoring (inverse MOA)
        if "group_size_moa" in load_data and load_data["group_size_moa"]:
            moa = load_data["group_size_moa"]
            accuracy_score = max(0, 100 - (moa * 40))  # 0.5 MOA = 80pts
            score += accuracy_score * (priorities.get("accuracy", 0) / 100)

        # Consistency scoring (inverse ES)
        if "velocity_es" in load_data and load_data["velocity_es"]:
            es = load_data["velocity_es"]
            consistency_score = max(0, 100 - (es * 2))  # 15 ES = 70pts
            score += consistency_score * (priorities.get("consistency", 0) / 100)

        # Velocity scoring
        if "velocity_avg" in load_data and load_data["velocity_avg"]:
            vel = load_data["velocity_avg"]
            target_vel = profile.get("target_velocity_fps", 2700)
            vel_diff = abs(vel - target_vel)
            velocity_score = max(0, 100 - (vel_diff / 10))
            score += velocity_score * (priorities.get("velocity", 0) / 100)

        # BC scoring (higher is better)
        bc = _preferred_bc_for_scoring(load_data)
        if bc:
            bc_score = min(100, bc * 250)  # 0.3 BC = 75pts
            score += bc_score * (priorities.get("bc", 0) / 100)

        # Energy scoring
        if "energy_ftlbs" in load_data and load_data["energy_ftlbs"]:
            energy = load_data["energy_ftlbs"]
            min_energy = profile.get("min_energy_ftlbs", 1000)
            if energy >= min_energy:
                energy_score = min(100, (energy / min_energy) * 50 + 50)
            else:
                energy_score = (energy / min_energy) * 50
            score += energy_score * (priorities.get("energy", 0) / 100)

        return score


class RifleSelectionPage(QWizardPage):
    """Step 1: select the rifle profile."""

    def __init__(self):
        super().__init__()
        self.setTitle("Select Rifle")
        self.setSubTitle("Which rifle are you loading for?")

        self.db = get_database()
        layout = QVBoxLayout()

        # Rifle selector
        self.combo_rifle = QComboBox()
        self.load_rifles()
        layout.addWidget(QLabel("Rifle:"))
        layout.addWidget(self.combo_rifle)

        self.combo_setup = QComboBox()
        layout.addWidget(QLabel("Setup:"))
        layout.addWidget(self.combo_setup)

        # Rifle info display
        self.text_rifle_info = QTextEdit()
        self.text_rifle_info.setReadOnly(True)
        self.text_rifle_info.setMaximumHeight(120)
        layout.addWidget(QLabel("Rifle details:"))
        layout.addWidget(self.text_rifle_info)

        self.combo_rifle.currentIndexChanged.connect(self.on_rifle_changed)
        self.combo_setup.currentIndexChanged.connect(self.on_rifle_changed)
        self.on_rifle_changed()

        layout.addStretch()
        self.setLayout(layout)

    def load_rifles(self):
        """Last inn rifles fra database"""
        rifles = self.db.get_all("rifles", "name")
        self.combo_rifle.clear()
        for rifle in rifles:
            self.combo_rifle.addItem(
                f"{rifle['name']} ({rifle['caliber']})", rifle["id"]
            )

    def on_rifle_changed(self):
        """Vis rifle info når valg endres"""
        rifle_id = self.combo_rifle.currentData()
        if rifle_id:
            rifle = self.db.get_by_id("rifles", rifle_id)
            self._refresh_setup_choices(rifle)
            if rifle:
                barrel_context = self.get_selected_barrel_configuration_context()
                barrel_name = str(
                    barrel_context.get("barrel_name")
                    or rifle.get("barrel_length")
                    or "N/A"
                )
                setup_name = str(
                    barrel_context.get("barrel_configuration_name") or "Current setup"
                )
                self.text_rifle_info.setHtml(
                    f"""
                    <b>Caliber:</b> {rifle['caliber']}<br>
                    <b>Barrel:</b> {barrel_name}<br>
                    <b>Setup:</b> {setup_name}<br>
                    <b>Twist:</b> {rifle.get('twist_rate', 'N/A')}<br>
                    <b>Action:</b> {rifle.get('action_type', 'N/A')}<br>
                """
                )
        else:
            self.combo_setup.clear()

    def _refresh_setup_choices(self, rifle: Dict | None = None) -> None:
        rifle_id = self.combo_rifle.currentData()
        rifle_data = rifle or (
            self.db.get_by_id("rifles", rifle_id) if rifle_id else None
        )
        configurations = _get_available_wizard_barrel_configurations(
            self.db,
            rifle_id,
            rifle_data=rifle_data,
        )
        previous = self.combo_setup.currentData()
        self.combo_setup.blockSignals(True)
        self.combo_setup.clear()
        for configuration in configurations:
            configuration_id = str(configuration.get("id") or "").strip() or None
            configuration_name = str(
                configuration.get("name") or configuration_id or "Current setup"
            ).strip()
            self.combo_setup.addItem(
                configuration_name or "Current setup", configuration_id
            )
        target = previous or str(self.combo_setup.itemData(0) or "").strip() or None
        for index in range(self.combo_setup.count()):
            if str(self.combo_setup.itemData(index) or "").strip() == str(target or ""):
                self.combo_setup.setCurrentIndex(index)
                break
        self.combo_setup.setEnabled(self.combo_setup.count() > 0)
        self.combo_setup.blockSignals(False)

    def get_selected_rifle_id(self) -> Optional[int]:
        """Hent valgt rifle ID"""
        return self.combo_rifle.currentData()

    def get_selected_barrel_configuration_id(self) -> Optional[str]:
        selected = self.combo_setup.currentData()
        if selected in (None, ""):
            return None
        return str(selected)

    def get_selected_barrel_configuration_context(self) -> Dict:
        rifle_id = self.get_selected_rifle_id()
        rifle = self.db.get_by_id("rifles", rifle_id) if rifle_id else None
        return _resolve_wizard_barrel_configuration_context(
            self.db,
            rifle_id,
            rifle_data=rifle,
            selected_configuration_id=self.get_selected_barrel_configuration_id(),
            selected_configuration_name=self.combo_setup.currentText() or None,
        )


class PurposeSelectionPage(QWizardPage):
    """Step 2: select the intended use."""

    def __init__(self):
        super().__init__()
        self.setTitle("What is the load for?")
        self.setSubTitle("Choose the use case. It directly affects the recommendation.")

        layout = QVBoxLayout()

        self.button_group = QButtonGroup()

        for key, profile in PurposeProfile.PROFILES.items():
            rb = QRadioButton()

            # Create rich label
            rb_layout = QVBoxLayout()

            title = QLabel(f"<b style='font-size: 14px;'>{profile['name']}</b>")
            rb_layout.addWidget(title)

            desc = QLabel(profile["description"])
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #7f8c8d;")
            rb_layout.addWidget(desc)

            # Add to layout
            container = QWidget()
            container.setLayout(rb_layout)

            layout.addWidget(rb)
            layout.addWidget(container)

            self.button_group.addButton(rb)
            rb.setProperty("purpose_key", key)

            if key == "jakt":
                rb.setChecked(True)

        layout.addStretch()
        self.setLayout(layout)

    def get_selected_purpose(self) -> str:
        """Hent valgt formål"""
        checked = self.button_group.checkedButton()
        if checked:
            return checked.property("purpose_key")
        return "jakt"


class ComponentSelectionPage(QWizardPage):
    """Step 3: select components."""

    def __init__(self):
        super().__init__()
        self.setTitle("Select Components")
        self.setSubTitle("Which components do you want to use?")

        self.db = get_database()
        layout = QVBoxLayout()

        # Bullet selector
        bullet_group = QGroupBox("Bullet")
        bullet_layout = QVBoxLayout()
        self.combo_bullet = QComboBox()
        self.load_bullets()
        bullet_layout.addWidget(self.combo_bullet)
        bullet_group.setLayout(bullet_layout)
        layout.addWidget(bullet_group)

        # Powder selector
        powder_group = QGroupBox("Powder")
        powder_layout = QVBoxLayout()
        self.combo_powder = QComboBox()
        self.load_powders()
        powder_layout.addWidget(self.combo_powder)
        powder_group.setLayout(powder_layout)
        layout.addWidget(powder_group)

        # Primer selector
        primer_group = QGroupBox("Primers")
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
        bullets = self.db.get_all("bullets", "weight_grains")
        self.combo_bullet.clear()
        for bullet in bullets:
            self.combo_bullet.addItem(_format_bullet_label(bullet), bullet["id"])

    def load_powders(self):
        """Last krutt fra database"""
        powders = self.db.get_all("powder", "name")
        self.combo_powder.clear()
        for powder in powders:
            label = f"{powder['name']}"
            if powder.get("manufacturer"):
                label += f" ({powder['manufacturer']})"
            self.combo_powder.addItem(label, powder["id"])

    def load_primers(self):
        """Last tennhetter fra database"""
        primers = self.db.get_all("primers", "name")
        self.combo_primer.clear()
        for primer in primers:
            label = f"{primer['name']} - {primer.get('type', 'N/A')}"
            self.combo_primer.addItem(label, primer["id"])

    def get_selections(self) -> Dict:
        """Hent valgte komponenter"""
        return {
            "bullet_id": self.combo_bullet.currentData(),
            "powder_id": self.combo_powder.currentData(),
            "primer_id": self.combo_primer.currentData(),
        }


class AIRecommendationPage(QWizardPage):
    """Step 4: build the guided recommendation."""

    def __init__(self):
        super().__init__()
        self.setTitle("Guided Recommendation")
        self.setSubTitle("Based on your selections and historical data")

        self.db = get_database()
        self.recommendation_data: Dict[str, float] = {}
        self.best_history: Optional[Dict] = None
        self.standard_audit: Dict[str, object] = {}
        layout = QVBoxLayout()

        # Analysis status
        self.label_status = QLabel("Analyzing...")
        layout.addWidget(self.label_status)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Recommendation display
        self.text_recommendation = QTextEdit()
        self.text_recommendation.setReadOnly(True)
        layout.addWidget(self.text_recommendation)

        # Historical data table
        history_group = QGroupBox("Relevant Historical Tests")
        history_layout = QVBoxLayout()
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(6)
        self.table_history.setHorizontalHeaderLabels(
            ["Charge", "Velocity", "ES", "SD", "Group (MOA)", "Score"]
        )
        self.table_history.horizontalHeader().setSectionResizeMode(  # type: ignore[union-attr]
            QHeaderView.ResizeMode.Stretch
        )
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
        self.label_status.setText("Loading rifle data...")
        self.recommendation_data = {}
        self.best_history = None

        # Hent rifle info
        rifle = self.db.get_by_id("rifles", rifle_id)
        if not rifle:
            self.progress.setValue(100)
            self.label_status.setText("Rifle not found")
            self.text_recommendation.setPlainText(
                "The selected rifle could not be found in the database. Refresh the view or select the rifle again."
            )
            self.table_history.setRowCount(0)
            return
        caliber = rifle.get("caliber", "")

        self.progress.setValue(20)
        self.label_status.setText("Searching published load data...")
        self.standard_audit = build_cartridge_standard_audit(self.db)

        # Hent relevante ladetabeller fra produsenter
        bullet_id = components.get("bullet_id")
        powder_id = components.get("powder_id")

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
            load_data = [
                ld
                for ld in load_data
                if ld.get("bullet_id") == bullet_id
                or components.get("bullet_weight", 0) in str(ld.get("bullet_name", ""))
            ]

        if powder_id:
            powder = self.db.get_by_id("powder", powder_id)
            powder_name = str(powder.get("name", "")).strip() if powder else ""
            if powder_name:
                load_data = [
                    ld
                    for ld in load_data
                    if powder_name in str(ld.get("powder_name", ""))
                ]

        self.progress.setValue(40)
        self.label_status.setText("Loading historical test data...")

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
        self.label_status.setText("Analyzing patterns...")

        # Score hver historisk test basert på formål
        scored_history = []
        for test in history:
            if test.get("velocity_avg"):
                score = PurposeProfile.score_load(purpose, test)
                test["score"] = score
                scored_history.append(test)

        # Sorter etter score
        scored_history.sort(key=lambda x: x["score"], reverse=True)

        self.progress.setValue(80)
        self.label_status.setText("Generating recommendation...")

        # Vis historikk i tabell
        self.table_history.setRowCount(min(10, len(scored_history)))
        for i, test in enumerate(scored_history[:10]):
            self.table_history.setItem(
                i, 0, QTableWidgetItem(f"{test.get('charge_weight', 'N/A')}gr")
            )
            self.table_history.setItem(
                i, 1, QTableWidgetItem(f"{test.get('velocity_avg', 'N/A')} fps")
            )
            self.table_history.setItem(
                i, 2, QTableWidgetItem(f"{test.get('velocity_es', 'N/A')}")
            )
            self.table_history.setItem(
                i, 3, QTableWidgetItem(f"{test.get('velocity_sd', 'N/A')}")
            )
            self.table_history.setItem(
                i, 4, QTableWidgetItem(f"{test.get('group_size_moa', 'N/A')}")
            )
            self.table_history.setItem(
                i, 5, QTableWidgetItem(f"{test.get('score', 0):.1f}")
            )

        # Generer anbefaling
        profile = PurposeProfile.get_profile(purpose)

        # Kombiner historikk og ladetabeller
        recommendation = f"""
            <h2 style='color: #27ae60;'>Guided Load Recommendation</h2>
            <p><b>Purpose:</b> {profile['name']}</p>
            <p><i>{profile['description']}</i></p>
        """

        # Vis produsent ladetabeller hvis funnet
        if load_data:
            recommendation += f"""
                <h3>Published Load Tables ({len(load_data)} found)</h3>
                <table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>
                    <tr style='background-color: #34495e; color: white;'>
                        <th>Source</th>
                        <th>Bullet</th>
                        <th>Powder</th>
                        <th>Min→Max</th>
                        <th>Velocity</th>
                        <th>Pressure (PSI)</th>
                    </tr>
            """

            for ld in load_data[:5]:  # Vis topp 5
                min_charge = ld.get("min_charge_grains", 0)
                max_charge = ld.get("max_charge_grains", 0)
                min_vel = ld.get("min_velocity_fps", 0)
                max_vel = ld.get("max_velocity_fps", 0)
                max_psi = ld.get("max_pressure_psi", 0)

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
            avg_min = sum(ld.get("min_charge_grains", 0) for ld in load_data) / len(
                load_data
            )
            avg_max = sum(ld.get("max_charge_grains", 0) for ld in load_data) / len(
                load_data
            )
            avg_velocity = sum(ld.get("max_velocity_fps", 0) for ld in load_data) / len(
                load_data
            )
            avg_max_pressure = sum(
                ld.get("max_pressure_psi", 0) for ld in load_data
            ) / len(load_data)

            # Hent SAAMI/CIP max pressure for kaliber
            from ..utils.pressure_calculator import PressureCalculator

            pressure_calc = PressureCalculator(self.db)
            saami_max = pressure_calc.get_saami_max(caliber)

            # Beregn % av SAAMI max
            if avg_max_pressure > 0:
                percent_of_saami = (avg_max_pressure / saami_max) * 100
                pressure_color = "#27ae60" if percent_of_saami < 95 else "#e74c3c"
            else:
                percent_of_saami = 0
                pressure_color = "#95a5a6"

            self.recommendation_data = {
                "avg_min_charge": avg_min,
                "avg_max_charge": avg_max,
                "avg_velocity": avg_velocity,
                "avg_max_pressure": avg_max_pressure,
                "percent_of_saami": percent_of_saami,
                "source_count": float(len(load_data)),
            }

            recommendation += f"""
                <div style='background-color: #ecf0f1; padding: 10px; border-radius: 5px;'>
                <h4>Recommended starting point from published data:</h4>
                <ul>
                    <li><b>Start at:</b> {avg_min:.1f}gr (mean minimum from {len(load_data)} sources)</li>
                    <li><b>Recommended max:</b> {avg_max:.1f}gr</li>
                    <li><b>Expected velocity:</b> {avg_velocity:.0f} fps near max charge</li>
                    <li><b>Suggested working range:</b> {avg_min:.1f}gr → {avg_max:.1f}gr in 0.3gr steps</li>
                </ul>
                <h4>Pressure data (SAAMI/CIP):</h4>
                <ul>
                    <li><b>SAAMI/CIP max for {caliber}:</b> {saami_max:,} PSI</li>
                    <li><b>Published max pressure:</b> <span style='color: {pressure_color};'>{avg_max_pressure:,.0f} PSI ({percent_of_saami:.1f}% of SAAMI max)</span></li>
                    <li><b>Safety margin:</b> {100 - percent_of_saami:.1f}% below the SAAMI limit</li>
                </ul>
                </div>
                <br>
            """

        audit = self.standard_audit or {}
        audit_counts = audit.get("counts") or {}
        lift_areas = audit.get("lift_areas") or []
        if audit_counts:
            recommendation += f"""
                <div style='background-color: #f4f6f7; padding: 10px; border-radius: 5px;'>
                <h4>Cartridge standard coverage</h4>
                <ul>
                    <li><b>Cartridges in library:</b> {int(audit_counts.get('total', 0))}</li>
                    <li><b>With max pressure:</b> {int(audit_counts.get('with_pressure', 0))}</li>
                    <li><b>With case capacity:</b> {int(audit_counts.get('with_case_capacity', 0))}</li>
                    <li><b>With bullet diameter:</b> {int(audit_counts.get('with_bullet_diameter', 0))}</li>
                    <li><b>With neck diameter:</b> {int(audit_counts.get('with_neck_diameter', 0))}</li>
                    <li><b>With drawing/PDF:</b> {int(audit_counts.get('with_drawings', 0))}</li>
                </ul>
            """
            if lift_areas:
                recommendation += "<b>What new data would improve next:</b><ul>"
                for item in lift_areas:
                    recommendation += f"<li>{item}</li>"
                recommendation += "</ul>"
            recommendation += "</div><br>"

        # Vis historiske data hvis tilgjengelig
        if scored_history:
            best = scored_history[0]
            self.best_history = best
            recommendation += f"""
                <h3>Your historical tests ({len(scored_history)} total)</h3>

                <div style='background-color: #e8f8f5; padding: 10px; border-radius: 5px;'>
                <h4>Best historical result for {profile['name']}:</h4>
                <ul>
                    <li><b>Charge:</b> {best.get('charge_weight', 'N/A')}gr</li>
                    <li><b>Velocity:</b> {best.get('velocity_avg', 'N/A')} fps</li>
                    <li><b>ES:</b> {best.get('velocity_es', 'N/A')} fps</li>
                    <li><b>SD:</b> {best.get('velocity_sd', 'N/A')} fps</li>
                    <li><b>Group:</b> {best.get('group_size_moa', 'N/A')} MOA</li>
                    <li><b>Purpose score:</b> {best.get('score', 0):.1f}/100</li>
                </ul>
                </div>
                <br>
            """

        recommendation += f"""
            <h3>Tips for {profile['name']}:</h3>
            <ul>
        """

        for tip in profile["tips"]:
            recommendation += f"<li>{tip}</li>"

        recommendation += """
            </ul>

            <h3>SAFETY - READ THIS</h3>
            <div style='background-color: #fadbd8; padding: 10px; border-radius: 5px; border: 2px solid #e74c3c;'>
            <p style='color: #c0392b; font-weight: bold;'>
            • ALWAYS start at least 10% below the published minimum charge when no better source exists.<br>
            • Work upward gradually in 0.2-0.3gr steps.<br>
            • Watch for pressure signs on every charge level, including flat primers and heavy bolt lift.<br>
            • Verify against an official load manual before use.<br>
            • These recommendations are directional guidance, not absolute values.<br>
            • Different rifles can show different pressure behavior with the same load.
            </p>
            </div>
        """

        # Hvis ingen data - vis advarsel
        if not load_data and not scored_history:
            recommendation += """
                <br>
                <div style='background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 2px solid #f39c12;'>
                <h3 style='color: #856404;'>No data found</h3>
                <p>No published load tables or historical tests were found for this combination.</p>
                <p><b>Recommendation:</b> Use an official load manual and begin at the minimum published charge.</p>
                </div>
            """

        self.text_recommendation.setHtml(recommendation)

        self.progress.setValue(100)
        self.label_status.setText("Analysis complete.")


class GuidancePage(QWizardPage):
    """Step 5: guidance and next actions."""

    def __init__(self):
        super().__init__()
        self.setTitle("Guidance")
        self.setSubTitle("Next steps in the load development process")

        layout = QVBoxLayout()

        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(
            """
            <h2>Next steps</h2>

            <h3>1. Prepare components</h3>
            <ul>
                <li>Inspect brass for cracks or damage.</li>
                <li>Measure case length and trim if needed.</li>
                <li>Clean primer pockets.</li>
                <li>Weigh components accurately.</li>
            </ul>

            <h3>2. Load assembly</h3>
            <ul>
                <li>Double-check every powder charge.</li>
                <li>Keep seating depth consistent.</li>
                <li>Log all details in Session Logger.</li>
            </ul>

            <h3>3. Testing</h3>
            <ul>
                <li>Use a chronograph and import the data into the Chronograph tab.</li>
                <li>Shoot at least 5-round groups.</li>
                <li>Document weather and temperature.</li>
                <li>Capture target images for the Target Analyzer.</li>
            </ul>

            <h3>4. Analysis</h3>
            <ul>
                <li>Review ES and SD in Precision Tracker.</li>
                <li>Check pressure signs in Safety Dashboard.</li>
                <li>Calculate drop data in Drop Chart Generator.</li>
            </ul>

            <h2>Ready to begin?</h2>
            <p>Press Finish to create a new loading session.</p>
        """
        )
        layout.addWidget(text)

        self.setLayout(layout)


class SmartLoadingWizard(QWizard):
    """Primary wizard for guided load development."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Load Guidance Wizard")
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
        db = get_database()

        try:
            legacy_session_id, load_session_id = _create_loading_session_from_wizard(
                db,
                self.page(0),
                self.page(1),
                self.page(2),
                self.page(3),
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not create loading session: {exc}",
            )
            return

        settings = QSettings("ReloadingWorkshop", "ReloadingManager")
        barrel_context = self.page(0).get_selected_barrel_configuration_context()
        store_workflow_context_in_settings(
            settings,
            {
                "load_session_id": load_session_id,
                "rifle_id": self.page(0).get_selected_rifle_id(),
                "barrel_configuration_id": barrel_context.get(
                    "barrel_configuration_id"
                ),
                "barrel_configuration_name": barrel_context.get(
                    "barrel_configuration_name"
                ),
            },
        )

        QMessageBox.information(
            self,
            "Success",
            "Load guidance setup complete.\n\n"
            f"Canonical load session created (ID {load_session_id}).\n"
            f"Legacy loading session created (ID {legacy_session_id}).\n"
            "Open Session Logger to begin recording data.",
        )
        super().accept()


def _create_loading_session_from_wizard(
    db,
    rifle_page,
    purpose_page,
    component_page,
    recommendation_page,
) -> tuple[int, int]:
    rifle_id = rifle_page.get_selected_rifle_id()
    purpose_key = purpose_page.get_selected_purpose()
    profile = PurposeProfile.get_profile(purpose_key)

    rifle_name = "Unknown rifle"
    rifle_caliber = ""
    if rifle_id:
        rifle = db.get_by_id("rifles", rifle_id)
        if rifle:
            rifle_name = rifle.get("name") or rifle_name
            rifle_caliber = rifle.get("caliber") or ""

    bullet_id = component_page.combo_bullet.currentData()
    powder_id = component_page.combo_powder.currentData()
    primer_id = component_page.combo_primer.currentData()
    bullet_label = component_page.combo_bullet.currentText() or "Unknown bullet"
    powder_label = component_page.combo_powder.currentText() or "Unknown powder"
    primer_label = component_page.combo_primer.currentText() or "Unknown primer"

    notes_lines = [
        "Load Guidance Wizard",
        f"Purpose: {profile['name']}",
        f"Rifle: {rifle_name}{' (' + rifle_caliber + ')' if rifle_caliber else ''}",
        f"Bullet: {bullet_label}",
        f"Powder: {powder_label}",
        f"Primer: {primer_label}",
    ]

    rec_data = getattr(recommendation_page, "recommendation_data", {}) or {}
    powder_min = rec_data.get("avg_min_charge")
    powder_max = rec_data.get("avg_max_charge")
    source_count = rec_data.get("source_count")

    if powder_min is not None and powder_max is not None and source_count:
        notes_lines.append(
            "Suggested working range: "
            f"{powder_min:.1f}–{powder_max:.1f} gr "
            f"(snitt av {int(source_count)} kilder)"
        )

    best_history = getattr(recommendation_page, "best_history", None)
    if best_history:
        notes_lines.append(
            "Beste historiske test: "
            f"{best_history.get('charge_weight', 'N/A')}gr, "
            f"{best_history.get('group_size_moa', 'N/A')} MOA"
        )

    component_selection = {
        "bullet_id": bullet_id,
        "bullet_label": bullet_label,
        "powder_id": powder_id,
        "powder_label": powder_label,
        "primer_id": primer_id,
        "primer_label": primer_label,
    }
    intake_snapshot = {
        "source": "smart_loading_wizard",
        "created_from": "load_assistant",
        "selected_rifle_id": rifle_id,
        "selected_rifle_name": rifle_name,
        "selected_rifle_caliber": rifle_caliber,
        "usage_profile_key": purpose_key,
        "usage_profile_name": profile["name"],
    }
    recommendation = {
        "source_count": source_count,
        "charge_window_gr": {
            "min": powder_min,
            "max": powder_max,
        },
        "best_history": best_history or {},
        "raw": rec_data,
    }
    evidence_summary = {
        "has_historical_result": bool(best_history),
        "historical_group_moa": (best_history or {}).get("group_size_moa"),
        "historical_charge_gr": (best_history or {}).get("charge_weight"),
        "reference_source_count": source_count or 0,
    }

    confidence_label = "medium" if source_count or best_history else "low"
    confidence_score = 0.65 if best_history else (0.45 if source_count else 0.2)
    next_action = (
        "build_initial_test_batches"
        if powder_min is not None and powder_max is not None
        else "verify_manual_load_data"
    )
    if hasattr(rifle_page, "get_selected_barrel_configuration_context"):
        barrel_context = rifle_page.get_selected_barrel_configuration_context()
    else:
        barrel_context = _resolve_wizard_barrel_configuration_context(
            db,
            rifle_id,
            rifle_data=rifle if rifle_id else None,
        )

    setup_label = str(barrel_context.get("barrel_configuration_name") or "").strip()
    if setup_label:
        notes_lines.append(f"Setup: {setup_label}")

    notes = "\n".join(notes_lines)
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "ammo_profile_id": None,
        "quantity": 50,
        "coal_min": None,
        "coal_max": None,
        "powder_weight_min": powder_min,
        "powder_weight_max": powder_max,
        "time_minutes": None,
        "total_cost": None,
        "notes": notes,
    }

    legacy_session_id = db.insert("loading_sessions", data)

    load_session_id = create_load_development_session(
        db,
        rifle_id=rifle_id,
        rifle_name=rifle_name,
        rifle_caliber=rifle_caliber,
        usage_profile_key=purpose_key,
        usage_profile_name=profile["name"],
        barrel_id=barrel_context.get("barrel_id"),
        barrel_name=barrel_context.get("barrel_name"),
        barrel_configuration_id=barrel_context.get("barrel_configuration_id"),
        barrel_configuration_name=barrel_context.get("barrel_configuration_name"),
        barrel_configuration_snapshot=barrel_context.get(
            "barrel_configuration_snapshot"
        ),
        component_selection=component_selection,
        intake_snapshot=intake_snapshot,
        recommendation=recommendation,
        evidence_summary=evidence_summary,
        learning_state={"best_history": best_history or {}},
        quantity_target=50,
        recommended_charge_min_gr=powder_min,
        recommended_charge_max_gr=powder_max,
        confidence_label=confidence_label,
        confidence_score=confidence_score,
        safety_status="manual_verification_required",
        lifecycle_stage="recommendation_ready",
        next_action=next_action,
        legacy_loading_session_id=legacy_session_id,
        notes=notes,
    )
    link_legacy_loading_session(
        db,
        legacy_loading_session_id=legacy_session_id,
        load_session_id=load_session_id,
    )
    return legacy_session_id, load_session_id


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    wizard = SmartLoadingWizard()
    wizard.show()
    sys.exit(app.exec())
