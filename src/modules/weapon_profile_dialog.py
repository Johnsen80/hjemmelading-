import importlib
import json
import uuid
from datetime import datetime
from typing import Optional

from HjemmeladingApp.utils import units

from ..database.database import get_database
from ..logging_config import configure_logging, get_logger
from ..qt_compat import QtCore, QtWidgets

QCompleter = QtWidgets.QCompleter
from ..ui.barrel_editor import BarrelEditorDialog, build_caliber_combo
from ..ui.toast import show_toast
from ..utils.cartridge_standard_support import compare_chamber_to_cartridge_standard
from ..utils.i18n import get_current_language, tr
from ..utils.unit_preferences import (
    format_distance_m,
    format_length_mm,
    format_temperature_c,
    format_velocity_fps,
)

QComboBox = QtWidgets.QComboBox
QDialog = QtWidgets.QDialog
QFormLayout = QtWidgets.QFormLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QListWidget = QtWidgets.QListWidget
QListWidgetItem = QtWidgets.QListWidgetItem
QMessageBox = QtWidgets.QMessageBox
QPushButton = QtWidgets.QPushButton
QTextEdit = QtWidgets.QTextEdit
QVBoxLayout = QtWidgets.QVBoxLayout
QSettings = QtCore.QSettings

configure_logging()
logger = get_logger(__name__)


def _load_calibration_test_dialog():
    module = importlib.import_module("src.ui.calibration_test_dialog")
    return getattr(module, "CalibrationTestDialog")


def _load_ammo_test_dialog():
    module = importlib.import_module("src.ammo_test")
    return getattr(module, "AmmoTestReportDialog")


class WeaponProfileDialog(QDialog):
    """Dialog for creating/editing/deleting a weapon profile."""

    def __init__(
        self,
        db=None,
        rifle_id: Optional[int] = None,
        initial_barrel_id: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        try:
            from src.ui.theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            pass
        self.db = db or get_database()
        self.rifle_id = rifle_id
        self.initial_barrel_id = initial_barrel_id
        self.barrels: list[dict] = []
        self._rifle_row: dict = {}
        self.setWindowTitle(tr("weapon_profile_title"))
        self.resize(640, 560)
        self.init_ui()
        if self.rifle_id:
            self.load_rifle()

    def init_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setLayout(root)

        # ── Sidebar + stacked content ────────────────────────────────────────
        body = QtWidgets.QWidget(self)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left sidebar
        self._sidebar = QListWidget(body)
        self._sidebar.setFixedWidth(160)
        self._sidebar.setStyleSheet(
            "QListWidget { background: #2c313a; border: none; border-right: 1px solid #3c4250; }"
            "QListWidget::item { padding: 12px 16px; color: #b0b6be; font-size: 11pt; }"
            "QListWidget::item:selected { background: #2980b9; color: white; font-weight: 600; }"
            "QListWidget::item:hover { background: #353b45; }"
        )
        for section in ["Profil", "Optikk", "Piper"]:
            self._sidebar.addItem(section)
        self._sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        body_layout.addWidget(self._sidebar)

        # Right stacked pages
        self._stack = QtWidgets.QStackedWidget(body)
        body_layout.addWidget(self._stack, 1)

        root.addWidget(body, 1)

        # ── Page 0: Profil ───────────────────────────────────────────────────
        page_profil = QtWidgets.QWidget()
        p0_layout = QVBoxLayout(page_profil)
        p0_layout.setContentsMargins(20, 16, 20, 16)
        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("f.eks. Tikka UPR, Sauer 404 Synchro")
        form.addRow(tr("weapon_profile_name"), self.name_edit)

        self.manufacturer_edit = QLineEdit()
        self.manufacturer_edit.setPlaceholderText(
            "f.eks. Tikka, Sauer, Blaser, Bergara"
        )
        _rifle_makes = [
            "Tikka",
            "Sauer",
            "Blaser",
            "Bergara",
            "Remington",
            "Winchester",
            "Savage",
            "Ruger",
            "Browning",
            "CZ",
            "Howa",
            "Mauser",
            "Weatherby",
            "Christensen Arms",
            "Proof Research",
            "Accuracy International",
            "Anschütz",
            "Heym",
            "Merkel",
            "Steyr",
            "Sako",
        ]
        _make_completer = QCompleter(_rifle_makes, self)
        try:
            from ..qt_compat import QtCore as _qc

            _make_completer.setCaseSensitivity(_qc.Qt.CaseSensitivity.CaseInsensitive)
        except Exception:
            pass
        self.manufacturer_edit.setCompleter(_make_completer)
        form.addRow(tr("weapon_profile_manufacturer"), self.manufacturer_edit)

        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("f.eks. T3x CTR, 404 Synchro, X-Bolt")
        form.addRow(tr("weapon_profile_model"), self.model_edit)

        self.weapon_type = QComboBox()
        self.weapon_type.addItems(["rifle", "pistol"])
        form.addRow(tr("weapon_profile_type"), self.weapon_type)

        self.caliber_edit = build_caliber_combo(db=self.db)
        form.addRow(tr("weapon_profile_caliber"), self.caliber_edit)

        self.action_type = QComboBox()
        self.action_type.addItems(
            ["bolt", "semi-auto", "revolver", "lever", "single-shot", "other"]
        )
        form.addRow(tr("weapon_profile_action"), self.action_type)

        self.preferred_units = QComboBox()
        self.preferred_units.addItems(["metric", "imperial"])
        form.addRow(tr("weapon_profile_units"), self.preferred_units)

        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("Serienummer fra geværets kolbe eller løp")
        form.addRow(tr("weapon_profile_serial"), self.serial_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText(
            "Generelle notater om riflen, historikk, modifikasjoner..."
        )
        form.addRow(tr("weapon_profile_notes"), self.notes_edit)

        p0_layout.addLayout(form)
        p0_layout.addStretch()
        self._stack.addWidget(page_profil)

        # ── Page 1: Optikk ───────────────────────────────────────────────────
        page_optikk = QtWidgets.QWidget()
        p1_layout = QVBoxLayout(page_optikk)
        p1_layout.setContentsMargins(20, 16, 20, 16)
        opt_form = QFormLayout()
        opt_form.setSpacing(10)

        # Known optic manufacturers for autocomplete
        _optic_makes = [
            "Schmidt & Bender",
            "Vortex",
            "Nightforce",
            "Leupold",
            "Swarovski",
            "March",
            "Zeiss",
            "Kahles",
            "Steiner",
            "IOR",
            "US Optics",
            "Tangent Theta",
            "Hensoldt",
            "Athlon",
            "Primary Arms",
            "Bushnell",
            "Tract",
            "Tract Optics",
            "Sig Sauer",
        ]
        _optic_make_completer = QCompleter(_optic_makes, self)
        try:
            from ..qt_compat import QtCore as _qc

            _optic_make_completer.setCaseSensitivity(
                _qc.Qt.CaseSensitivity.CaseInsensitive
            )
        except Exception:
            pass

        # Known scope models for autocomplete
        _optic_models = [
            "PMII 5-25×56",
            "PMII 3-27×56",
            "PMII 12-50×56",
            "Razor HD Gen III 6-36×56",
            "Razor HD LHT 4.5-27×56",
            "ATACR 7-35×56",
            "ATACR 5-25×56",
            "BEAST 5.5-22×56",
            "Mark 5HD 5-25×56",
            "Mark 4 8.5-25×50",
            "VX-6HD 3-18×50",
            "dS 5-45×56",
            "X5i 3.5-18×50",
            "FX-3 6-24×42",
            "Conquest V4 4-16×44",
            "Victory HT 3-12×56",
            "GX2 8-32×56",
            "K328i 3.5-28×50",
        ]
        _optic_model_completer = QCompleter(_optic_models, self)
        try:
            from ..qt_compat import QtCore as _qc

            _optic_model_completer.setCaseSensitivity(
                _qc.Qt.CaseSensitivity.CaseInsensitive
            )
        except Exception:
            pass

        self.optic_name_edit = QLineEdit()
        self.optic_name_edit.setPlaceholderText("f.eks. PMII 5-25×56, Razor HD Gen III")
        self.optic_name_edit.setCompleter(_optic_model_completer)
        opt_form.addRow(tr("optic_name_label"), self.optic_name_edit)

        self.optic_manufacturer_edit = QLineEdit()
        self.optic_manufacturer_edit.setPlaceholderText(
            "f.eks. Schmidt & Bender, Vortex, Nightforce"
        )
        self.optic_manufacturer_edit.setCompleter(_optic_make_completer)
        opt_form.addRow(tr("manufacturer_label"), self.optic_manufacturer_edit)

        self.optic_zero_distance_edit = QLineEdit()
        self.optic_zero_distance_edit.setPlaceholderText(
            "100  (meter — avstand til null-punkt)"
        )
        opt_form.addRow(tr("zero_distance_label"), self.optic_zero_distance_edit)

        self.optic_unit_combo = QComboBox()
        self.optic_unit_combo.addItems([tr("mil"), tr("moa")])
        self.optic_unit_combo.currentIndexChanged.connect(self._on_turret_unit_changed)
        opt_form.addRow(tr("turret_units_label"), self.optic_unit_combo)

        self.optic_click_value_edit = QLineEdit()
        self.optic_click_value_edit.setPlaceholderText(
            "0.1  (MIL — én klikk = 0.1 MIL)"
        )
        opt_form.addRow(tr("click_value_label"), self.optic_click_value_edit)

        self.optic_clicks_per_rev_edit = QLineEdit()
        self.optic_clicks_per_rev_edit.setPlaceholderText(
            "100  (antall klikk per tårnrevolusjon)"
        )
        opt_form.addRow(tr("clicks_per_rev_label"), self.optic_clicks_per_rev_edit)

        self.view_optics_history_btn = QPushButton(tr("view_optics_history"))
        self.view_optics_history_btn.clicked.connect(self._on_view_optics_history)
        opt_form.addRow(self.view_optics_history_btn)

        p1_layout.addLayout(opt_form)
        p1_layout.addStretch()
        self._stack.addWidget(page_optikk)

        # ── Page 2: Piper ────────────────────────────────────────────────────
        page_piper = QtWidgets.QWidget()
        p2_layout = QVBoxLayout(page_piper)
        p2_layout.setContentsMargins(20, 16, 20, 16)
        p2_layout.setSpacing(8)

        barrels_label = QLabel(tr("weapon_profile_barrels_help"))
        barrels_label.setWordWrap(True)
        barrels_label.setStyleSheet("color: #b0b6be; font-size: 10pt;")
        p2_layout.addWidget(barrels_label)

        self.barrel_list = QListWidget()
        self.barrel_list.currentRowChanged.connect(self.refresh_selected_barrel_summary)
        p2_layout.addWidget(self.barrel_list, 1)

        self.barrel_summary_label = QLabel(tr("weapon_profile_barrel_summary_default"))
        self.barrel_summary_label.setWordWrap(True)
        self.barrel_summary_label.setStyleSheet(
            "padding: 6px 10px; border-left: 3px solid #2980b9; color: #b0b6be; font-size: 10pt;"
        )
        p2_layout.addWidget(self.barrel_summary_label)

        # Barrel action buttons
        barrel_actions = QHBoxLayout()
        self.add_barrel_btn = QPushButton(tr("weapon_profile_add_barrel"))
        self.add_barrel_btn.clicked.connect(self.add_barrel)
        self.edit_barrel_btn = QPushButton(tr("weapon_profile_edit_selected"))
        self.edit_barrel_btn.clicked.connect(self.edit_selected_barrel)
        self.remove_barrel_btn = QPushButton(tr("weapon_profile_remove_selected"))
        self.remove_barrel_btn.clicked.connect(self.remove_selected_barrel)
        self.set_active_barrel_btn = QPushButton(tr("weapon_profile_set_active_barrel"))
        self.set_active_barrel_btn.clicked.connect(self.set_selected_barrel_active)
        for b in [
            self.add_barrel_btn,
            self.edit_barrel_btn,
            self.remove_barrel_btn,
            self.set_active_barrel_btn,
        ]:
            barrel_actions.addWidget(b)
        barrel_actions.addStretch()
        p2_layout.addLayout(barrel_actions)

        # Barrel workflow buttons
        workflow_row = QHBoxLayout()
        self.add_calibration_btn = QPushButton(tr("weapon_profile_add_calibration"))
        self.add_calibration_btn.clicked.connect(
            self.add_calibration_to_selected_barrel
        )
        self.open_builder_btn = QPushButton(tr("weapon_profile_open_builder"))
        self.open_builder_btn.clicked.connect(self.open_builder_for_selected_barrel)
        self.open_ammo_test_btn = QPushButton(tr("weapon_profile_open_ammo_test"))
        self.open_ammo_test_btn.clicked.connect(self.open_ammo_test_for_selected_barrel)
        for b in [
            self.add_calibration_btn,
            self.open_builder_btn,
            self.open_ammo_test_btn,
        ]:
            workflow_row.addWidget(b)
        workflow_row.addStretch()
        p2_layout.addLayout(workflow_row)

        self._stack.addWidget(page_piper)

        # ── Bottom action bar ────────────────────────────────────────────────
        btn_bar = QtWidgets.QWidget(self)
        btn_bar.setStyleSheet("background: #2c313a; border-top: 1px solid #3c4250;")
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(16, 8, 16, 8)

        self.save_btn = QPushButton(tr("btn_save"))
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.on_save)

        self.cancel_btn = QPushButton(tr("btn_cancel"))
        self.cancel_btn.clicked.connect(self.reject)

        self.delete_btn = QPushButton(tr("weapon_profile_delete_profile"))
        self.delete_btn.setStyleSheet(
            "QPushButton { background: #e74c3c; } QPushButton:hover { background: #c0392b; }"
        )
        self.delete_btn.clicked.connect(self.on_delete)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.delete_btn)

        root.addWidget(btn_bar)

        # Start on first section
        self._sidebar.setCurrentRow(0)

        # If creating new, hide delete button
        if not self.rifle_id:
            self.delete_btn.setVisible(False)

    def _on_sidebar_changed(self, row: int) -> None:
        try:
            self._stack.setCurrentIndex(row)
        except Exception:
            pass

    def _on_turret_unit_changed(self, index: int) -> None:
        """Update click value and clicks-per-rev placeholders to match chosen turret unit."""
        try:
            unit_text = self.optic_unit_combo.currentText().upper()
            if "MOA" in unit_text:
                self.optic_click_value_edit.setPlaceholderText(
                    "0.25  (MOA — én klikk = ¼ MOA)"
                )
                self.optic_clicks_per_rev_edit.setPlaceholderText(
                    "60  (antall klikk per tårnrevolusjon ved MOA)"
                )
            else:
                self.optic_click_value_edit.setPlaceholderText(
                    "0.1  (MIL — én klikk = 0.1 MIL)"
                )
                self.optic_clicks_per_rev_edit.setPlaceholderText(
                    "100  (antall klikk per tårnrevolusjon ved MIL)"
                )
        except Exception:
            pass

    def _on_view_optics_history(self):
        """Stub — kept for compatibility with existing signal connections."""
        pass

    def load_rifle(self):
        row = self.db.get_by_id("rifles", self.rifle_id)
        if not row:
            QMessageBox.warning(self, tr("msg_error"), tr("weapon_profile_not_found"))
            return
        self._rifle_row = row
        self.name_edit.setText(row.get("name", ""))
        self.manufacturer_edit.setText(row.get("manufacturer", ""))
        self.model_edit.setText(row.get("model", ""))
        weapon_type = row.get("weapon_type", "rifle")
        idx = self.weapon_type.findText(weapon_type)
        if idx >= 0:
            self.weapon_type.setCurrentIndex(idx)
        self.caliber_edit.setCurrentText(row.get("caliber", ""))
        action = row.get("action_type", "")
        try:
            idx = self.action_type.findText(action)
            if idx >= 0:
                self.action_type.setCurrentIndex(idx)
        except Exception:
            pass
        preferred_units = row.get("preferred_units", "metric")
        idx = self.preferred_units.findText(preferred_units)
        if idx >= 0:
            self.preferred_units.setCurrentIndex(idx)
        self.serial_edit.setText(row.get("serial_number", "") or "")
        self.notes_edit.setPlainText(row.get("notes", "") or "")
        details_rows = self.db.execute_query(
            "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
            (self.rifle_id,),
        )
        if details_rows:
            try:
                details = json.loads(details_rows[0].get("profile_json", "{}"))
            except Exception:
                details = {}
            preferred_units = details.get("preferred_units")
            if preferred_units:
                idx = self.preferred_units.findText(preferred_units)
                if idx >= 0:
                    self.preferred_units.setCurrentIndex(idx)
            self.barrels = details.get("barrels", []) or []
            self.refresh_barrel_list()
            optic = details.get("optic", {}) or {}
            self.optic_name_edit.setText(optic.get("name", "") or "")
            self.optic_manufacturer_edit.setText(optic.get("manufacturer", "") or "")
            self.optic_zero_distance_edit.setText(
                optic.get("zero_distance_m", "") or ""
            )
            turret_unit = optic.get("turret_unit", "")
            if turret_unit:
                idx = self.optic_unit_combo.findText(turret_unit)
                if idx >= 0:
                    self.optic_unit_combo.setCurrentIndex(idx)
            self.optic_click_value_edit.setText(optic.get("click_value", "") or "")
            self.optic_clicks_per_rev_edit.setText(
                optic.get("clicks_per_rev", "") or ""
            )
        else:
            self.barrels = []
            self.refresh_barrel_list()

    def _get_rifle_reference_row(self) -> dict:
        if hasattr(self, "_rifle_row") and isinstance(self._rifle_row, dict):
            return self._rifle_row
        if self.rifle_id:
            try:
                row = self.db.get_by_id("rifles", self.rifle_id)
                if isinstance(row, dict):
                    self._rifle_row = row
                    return row
            except Exception:
                pass
        return {}

    def _build_chamber_comparison_lines(self, barrel: dict) -> list[str]:
        caliber = barrel.get("caliber") or self.caliber_edit.currentText().strip() or ""
        if not caliber:
            return []

        rifle = self._get_rifle_reference_row()
        case_data = barrel.get("case_measurements", {}) or {}
        measured = {
            "freebore_mm": rifle.get("freebore_mm"),
            "throat_angle_deg": rifle.get("throat_angle_deg"),
            "throat_erosion_mm": rifle.get("throat_erosion_mm"),
            "case_neck_diameter_mm": case_data.get("neck_diameter_mm"),
            "trim_length_mm": case_data.get("trim_length_mm"),
        }
        try:
            comparison = compare_chamber_to_cartridge_standard(
                self.db, caliber, measured
            )
        except Exception:
            comparison = {}
        notes = comparison.get("notes") or []
        if not notes:
            return []

        lines = ["<b>Standard vs Measured</b>"]
        status = str(comparison.get("status") or "").strip()
        if status == "watch":
            lines.append(
                "Deviation detected: check neck clearance, throat, and seating window extra carefully."
            )
        elif status == "ok":
            lines.append(
                "Measured data follows the standard reasonably well for this cartridge."
            )
        lines.extend(str(note) for note in notes[:5])
        return lines

    def refresh_barrel_list(self):
        self.barrel_list.clear()
        selected_row = -1
        for index, barrel in enumerate(self.barrels):
            item = QListWidgetItem(self._build_barrel_row_text(barrel))
            item.setToolTip(self._build_barrel_tooltip(barrel))
            self.barrel_list.addItem(item)
            if self.initial_barrel_id and str(barrel.get("id")) == str(
                self.initial_barrel_id
            ):
                selected_row = index
        if selected_row >= 0:
            self.barrel_list.setCurrentRow(selected_row)
        elif self.barrels:
            self.barrel_list.setCurrentRow(0)
        self.refresh_selected_barrel_summary()

    def _build_case_baseline_status(self, barrel: dict) -> tuple[str, str]:
        case_data = barrel.get("case_measurements", {}) or {}
        h2o_value = case_data.get("h2o_capacity_grains")
        h2o_measurements = case_data.get("h2o_measurements", []) or []
        trim_length = case_data.get("trim_length_mm")
        neck_diameter = case_data.get("neck_diameter_mm")
        shoulder_bump = case_data.get("shoulder_bump_mm")
        base_to_datum = case_data.get("base_to_datum_mm")

        count = sum(
            value not in (None, "", [])
            for value in (
                h2o_value,
                trim_length,
                neck_diameter,
                shoulder_bump,
                base_to_datum,
            )
        )

        if h2o_value not in (None, "") and len(h2o_measurements) >= 3 and count >= 4:
            return (
                "Strong Baseline",
                "An H2O series and several case measurements are recorded.",
            )
        if count >= 2:
            return (
                "Partial Baseline",
                "Some barrel and case measurements are recorded, but more measurements will improve the analysis.",
            )
        return (
            "Baseline Missing",
            "Enter H2O, trim length, neck diameter, shoulder bump, and base-to-datum.",
        )

    def _build_case_baseline_actions(self, barrel: dict) -> list[str]:
        case_data = barrel.get("case_measurements", {}) or {}
        h2o_value = case_data.get("h2o_capacity_grains")
        h2o_measurements = case_data.get("h2o_measurements", []) or []
        trim_length = case_data.get("trim_length_mm")
        neck_diameter = case_data.get("neck_diameter_mm")
        shoulder_bump = case_data.get("shoulder_bump_mm")
        base_to_datum = case_data.get("base_to_datum_mm")

        actions: list[str] = []
        if h2o_value in (None, ""):
            actions.append("Measure 3-5 H2O samples from fired cases in this barrel.")
        elif len(h2o_measurements) < 3:
            actions.append(
                "Expand the H2O series to at least 3-5 measurements for a better average and spread."
            )

        missing_dims: list[str] = []
        if neck_diameter in (None, ""):
            missing_dims.append("neck-diameter")
        if trim_length in (None, ""):
            missing_dims.append("trimlengde")
        if shoulder_bump in (None, ""):
            missing_dims.append("shoulder bump")
        if base_to_datum in (None, ""):
            missing_dims.append("base-to-datum")
        if missing_dims:
            actions.append(
                "Enter "
                + ", ".join(missing_dims[:4])
                + " for a better barrel and pressure model."
            )

        return actions

    @staticmethod
    def _muzzle_type_label(key: str) -> str:
        _map = {
            "none": "barrel_editor_muzzle_type_none",
            "suppressor": "barrel_editor_muzzle_type_suppressor",
            "brake": "barrel_editor_muzzle_type_brake",
            "compensator": "barrel_editor_muzzle_type_compensator",
            "flash_hider": "barrel_editor_muzzle_type_flash_hider",
            "other": "barrel_editor_muzzle_type_other",
        }
        i18n_key = _map.get(str(key or "none").lower())
        return (
            tr(i18n_key)
            if i18n_key
            else (str(key) if key else tr("weapon_profile_none"))
        )

    def _build_barrel_row_text(self, barrel: dict) -> str:
        name = barrel.get("name") or tr("weapon_profile_unnamed")
        caliber = (
            barrel.get("caliber")
            or self.caliber_edit.currentText().strip()
            or tr("weapon_profile_unknown")
        )
        usage = barrel.get("usage_type") or "general"
        muzzle = self._muzzle_type_label(barrel.get("muzzle_device_type"))
        calibration_tests = barrel.get("calibration_tests") or []
        series_count = (
            len(calibration_tests) if isinstance(calibration_tests, list) else 0
        )
        load_count = 0
        if isinstance(calibration_tests, list):
            for test in calibration_tests:
                if isinstance(test, dict):
                    loads = test.get("loads") or []
                    if isinstance(loads, list):
                        load_count += len(loads)
        calibration_text = (
            tr(
                "weapon_profile_calibration_counts",
                series_count=series_count,
                load_count=load_count,
            )
            if series_count
            else tr("weapon_profile_no_calibration")
        )
        baseline_status, _ = self._build_case_baseline_status(barrel)
        muzzle_type_key = str(barrel.get("muzzle_device_type") or "none").lower()
        parts = [name, caliber, usage]
        if muzzle_type_key not in ("none", ""):
            parts.append(muzzle)
        protrusion = barrel.get("muzzle_protrusion_mm")
        if protrusion is not None and muzzle_type_key not in ("none", ""):
            try:
                parts[-1] += f" +{float(protrusion):.0f}mm"
            except Exception:
                pass
        parts.append(calibration_text)
        base_text = " | ".join(parts)
        return f"{base_text} | {baseline_status}"

    def _get_preferred_units(self) -> str:
        try:
            if hasattr(self, "preferred_units"):
                return (
                    str(self.preferred_units.currentText() or "metric").strip().lower()
                )
        except Exception:
            pass
        return "metric"

    def _format_length_mm(self, value_mm: object) -> str:
        try:
            value = float(value_mm)
        except Exception:
            return str(value_mm) if value_mm not in (None, "") else "N/A"
        if self._get_preferred_units() == "imperial":
            return f"{units.mm_to_inches(value):.2f} in ({value:.1f} mm)"
        return format_length_mm(value)

    def _format_velocity_fps(self, value_fps: object) -> str:
        try:
            value = float(value_fps)
        except Exception:
            return str(value_fps) if value_fps not in (None, "") else "N/A"
        if self._get_preferred_units() == "imperial":
            return f"{value:.1f} fps"
        return format_velocity_fps(value)

    def _format_temperature_c(self, value_c: object) -> str:
        try:
            value = float(value_c)
        except Exception:
            return str(value_c) if value_c not in (None, "") else "N/A"
        if self._get_preferred_units() == "imperial":
            return f"{units.celsius_to_fahrenheit(value):.1f} °F ({value:.1f} °C)"
        return format_temperature_c(value)

    def _format_distance_m(self, value_m: object) -> str:
        try:
            value = float(value_m)
        except Exception:
            return str(value_m) if value_m not in (None, "") else "N/A"
        if self._get_preferred_units() == "imperial":
            return f"{units.meters_to_yards(value):.0f} yd ({value:.0f} m)"
        return format_distance_m(value)

    def _build_barrel_tooltip(self, barrel: dict) -> str:
        lines = [self._build_barrel_row_text(barrel)]
        _, baseline_note = self._build_case_baseline_status(barrel)
        if baseline_note:
            lines.append(f"Brass baseline: {baseline_note}")
        baseline_actions = self._build_case_baseline_actions(barrel)
        if baseline_actions:
            lines.append("Next measurement: " + " ".join(baseline_actions[:2]))
        length_mm = barrel.get("length_mm")
        if length_mm is not None:
            lines.append(
                tr(
                    "weapon_profile_barrel_length",
                    value=self._format_length_mm(length_mm),
                )
            )
        protrusion = barrel.get("muzzle_protrusion_mm")
        if protrusion is not None:
            try:
                lines.append(
                    tr(
                        "weapon_profile_muzzle_protrusion",
                        value=f"{float(protrusion):.0f}",
                    )
                )
            except Exception:
                pass
        case_data = barrel.get("case_measurements", {}) or {}
        h2o_value = case_data.get("h2o_capacity_grains")
        h2o_measurements = case_data.get("h2o_measurements", []) or []
        if h2o_value is not None:
            try:
                lines.append(
                    tr("weapon_profile_h2o_capacity", value=f"{float(h2o_value):.2f}")
                )
            except Exception:
                lines.append(tr("weapon_profile_h2o_capacity_raw", value=h2o_value))
        if h2o_measurements:
            lines.append(
                tr("weapon_profile_h2o_measurements_count", count=len(h2o_measurements))
            )
        calibration_tests = barrel.get("calibration_tests") or []
        if isinstance(calibration_tests, list) and calibration_tests:
            image_count = 0
            velocity_values = []
            for test in calibration_tests:
                if not isinstance(test, dict):
                    continue
                for load in test.get("loads", []) or []:
                    if not isinstance(load, dict):
                        continue
                    if load.get("group_image_path"):
                        image_count += 1
                    try:
                        if load.get("velocity_avg") is not None:
                            velocity_values.append(float(load["velocity_avg"]))
                    except Exception:
                        pass
            if velocity_values:
                lines.append(
                    tr(
                        "weapon_profile_v0_range",
                        minimum=self._format_velocity_fps(min(velocity_values)),
                        maximum=self._format_velocity_fps(max(velocity_values)),
                    )
                )
            if image_count:
                lines.append(tr("weapon_profile_target_images", count=image_count))
        learning = self._get_barrel_learning_profile(barrel)
        lines.extend(self._build_learning_profile_lines(learning))
        return "\n".join(lines)

    def _get_barrel_learning_profile(self, barrel: dict) -> dict:
        if not self.rifle_id:
            return {
                "status": "insufficient_data",
                "confidence_label": tr("weapon_profile_no_data_yet"),
                "data_points": 0,
                "chrono_samples": 0,
                "target_samples": 0,
                "temperature_samples": 0,
            }
        barrel_id = barrel.get("id")
        if not barrel_id:
            return {
                "status": "insufficient_data",
                "confidence_label": tr("weapon_profile_no_data_yet"),
                "data_points": 0,
                "chrono_samples": 0,
                "target_samples": 0,
                "temperature_samples": 0,
            }
        try:
            return self.db.get_barrel_learning_profile(
                self.rifle_id,
                str(barrel_id),
                barrel.get("name"),
            )
        except Exception as exc:
            logger.exception("Failed to load barrel learning profile: %s", exc)
            return {
                "status": "insufficient_data",
                "confidence_label": tr("weapon_profile_no_data_yet"),
                "data_points": 0,
                "chrono_samples": 0,
                "target_samples": 0,
                "temperature_samples": 0,
            }

    def _build_learning_profile_lines(self, learning: dict) -> list[str]:
        data_points = int(learning.get("data_points") or 0)
        chrono_samples = int(learning.get("chrono_samples") or 0)
        target_samples = int(learning.get("target_samples") or 0)
        temperature_samples = int(learning.get("temperature_samples") or 0)
        confidence = learning.get("confidence_label") or tr(
            "weapon_profile_no_data_yet"
        )

        lines = [
            tr("weapon_profile_learning_profile", confidence=confidence),
            tr(
                "weapon_profile_learning_data",
                data_points=data_points,
                chrono_samples=chrono_samples,
                target_samples=target_samples,
                temperature_samples=temperature_samples,
            ),
        ]
        drift_flag = learning.get("drift_flag")
        if drift_flag:
            lines.append(tr("weapon_profile_drift_status", drift_flag=drift_flag))
        cold_bore = learning.get("cold_bore_shift_moa")
        if cold_bore is not None:
            try:
                lines.append(
                    tr(
                        "weapon_profile_cold_bore_shift",
                        value=f"{float(cold_bore):.2f}",
                    )
                )
            except Exception:
                pass
        return lines

    def refresh_selected_barrel_summary(self):
        if not hasattr(self, "barrel_summary_label"):
            return
        row = self.barrel_list.currentRow()
        if row < 0 or row >= len(self.barrels):
            self.barrel_summary_label.setText(
                tr("weapon_profile_barrel_summary_default")
            )
            self.set_active_barrel_btn.setEnabled(False)
            self.add_calibration_btn.setEnabled(False)
            self.open_builder_btn.setEnabled(False)
            return

        barrel = self.barrels[row]
        self.set_active_barrel_btn.setEnabled(True)
        self.add_calibration_btn.setEnabled(bool(self.rifle_id))
        self.open_builder_btn.setEnabled(bool(self.rifle_id))
        case_data = barrel.get("case_measurements", {}) or {}
        h2o_value = case_data.get("h2o_capacity_grains")
        h2o_measurements = case_data.get("h2o_measurements", []) or []
        calibration_tests = barrel.get("calibration_tests") or []
        is_active = bool(self.initial_barrel_id) and str(barrel.get("id")) == str(
            self.initial_barrel_id
        )

        parts = [
            f"<b>{barrel.get('name') or tr('weapon_profile_unnamed')}</b>",
            tr(
                "weapon_profile_caliber_value",
                caliber=barrel.get("caliber")
                or self.caliber_edit.currentText().strip()
                or tr("weapon_profile_unknown"),
            ),
            tr(
                "weapon_profile_usage_value",
                usage=barrel.get("usage_type") or "general",
            ),
        ]
        parts.append(
            tr("weapon_profile_status_active")
            if is_active
            else tr("weapon_profile_status_inactive")
        )
        muzzle_type = barrel.get("muzzle_device_type")
        if muzzle_type and muzzle_type != "none":
            parts.append(
                tr(
                    "weapon_profile_muzzle_device",
                    muzzle=self._muzzle_type_label(muzzle_type),
                )
            )
        if barrel.get("length_mm") is not None:
            parts.append(
                tr(
                    "weapon_profile_barrel_length",
                    value=self._format_length_mm(barrel.get("length_mm")),
                )
            )

        if h2o_value is not None:
            try:
                parts.append(
                    tr("weapon_profile_h2o_capacity", value=f"{float(h2o_value):.2f}")
                )
            except Exception:
                parts.append(tr("weapon_profile_h2o_capacity_raw", value=h2o_value))
        if h2o_measurements:
            parts.append(tr("weapon_profile_h2o_basis", count=len(h2o_measurements)))
        baseline_status, baseline_note = self._build_case_baseline_status(barrel)
        parts.append(f"Brass baseline: {baseline_status}")
        if baseline_note:
            parts.append(baseline_note)
        baseline_actions = self._build_case_baseline_actions(barrel)
        if baseline_actions:
            parts.append("<b>Next Measurement</b>")
            parts.extend(baseline_actions[:2])

        if isinstance(calibration_tests, list) and calibration_tests:
            load_count = 0
            image_count = 0
            velocity_values = []
            temp_values = []
            distance_values = []
            for test in calibration_tests:
                if not isinstance(test, dict):
                    continue
                loads = test.get("loads", []) or []
                if isinstance(loads, list):
                    load_count += len(loads)
                try:
                    if test.get("temperature_c") is not None:
                        temp_values.append(float(test["temperature_c"]))
                except Exception:
                    pass
                try:
                    if test.get("distance_m") is not None:
                        distance_values.append(float(test["distance_m"]))
                except Exception:
                    pass
                for load in loads:
                    if not isinstance(load, dict):
                        continue
                    if load.get("group_image_path"):
                        image_count += 1
                    try:
                        if load.get("velocity_avg") is not None:
                            velocity_values.append(float(load["velocity_avg"]))
                    except Exception:
                        pass
            parts.append(
                tr(
                    "weapon_profile_calibration_summary",
                    series_count=len(calibration_tests),
                    load_count=load_count,
                )
            )
            if velocity_values:
                parts.append(
                    tr(
                        "weapon_profile_v0_range",
                        minimum=self._format_velocity_fps(min(velocity_values)),
                        maximum=self._format_velocity_fps(max(velocity_values)),
                    )
                )
            if temp_values:
                parts.append(
                    tr(
                        "weapon_profile_temperature_range",
                        minimum=self._format_temperature_c(min(temp_values)),
                        maximum=self._format_temperature_c(max(temp_values)),
                    )
                )
            if distance_values:
                parts.append(
                    tr(
                        "weapon_profile_distance_range",
                        minimum=self._format_distance_m(min(distance_values)),
                        maximum=self._format_distance_m(max(distance_values)),
                    )
                )
            if image_count:
                parts.append(tr("weapon_profile_target_images", count=image_count))
        else:
            parts.append(tr("weapon_profile_no_calibration_yet"))

        learning = self._get_barrel_learning_profile(barrel)
        parts.extend(self._build_learning_profile_lines(learning))
        parts.extend(self._build_chamber_comparison_lines(barrel))

        self.barrel_summary_label.setText("<br>".join(parts))

    def _build_details_payload(self) -> dict:
        return {
            "weapon_type": self.weapon_type.currentText(),
            "preferred_units": self.preferred_units.currentText(),
            "active_barrel_id": self.initial_barrel_id,
            "barrels": self.barrels,
        }

    def _save_profile_details(self) -> bool:
        if not self.rifle_id:
            return False
        payload = self._build_details_payload()
        try:
            existing = self.db.execute_query(
                "SELECT id FROM rifle_profile_details WHERE rifle_id = ?",
                (self.rifle_id,),
            )
            if existing:
                self.db.update(
                    "rifle_profile_details",
                    {"profile_json": json.dumps(payload, ensure_ascii=False)},
                    "rifle_id = ?",
                    (self.rifle_id,),
                )
            else:
                self.db.insert(
                    "rifle_profile_details",
                    {
                        "rifle_id": self.rifle_id,
                        "profile_json": json.dumps(payload, ensure_ascii=False),
                    },
                )
            return True
        except Exception as exc:
            logger.exception("Failed to save weapon profile details: %s", exc)
            return False

    def set_selected_barrel_active(self):
        row = self.barrel_list.currentRow()
        if row < 0 or row >= len(self.barrels):
            QMessageBox.information(
                self, tr("msg_no_selection"), tr("weapon_profile_select_barrel_first")
            )
            return
        barrel = self.barrels[row]
        self.initial_barrel_id = str(barrel.get("id") or "")
        if self.rifle_id and not self._save_profile_details():
            QMessageBox.warning(
                self,
                tr("weapon_profile_could_not_save"),
                tr("weapon_profile_active_barrel_not_saved"),
            )
            return
        self.refresh_barrel_list()
        self.barrel_list.setCurrentRow(row)
        QMessageBox.information(
            self,
            tr("weapon_profile_active_barrel_updated"),
            tr(
                "weapon_profile_active_barrel_updated_body",
                barrel_name=barrel.get("name") or tr("weapon_profile_selected_barrel"),
            ),
        )

    def add_calibration_to_selected_barrel(self):
        row = self.barrel_list.currentRow()
        if row < 0 or row >= len(self.barrels):
            QMessageBox.information(
                self, tr("msg_no_selection"), tr("weapon_profile_select_barrel_first")
            )
            return
        if not self.rifle_id:
            QMessageBox.information(
                self,
                tr("weapon_profile_save_first"),
                tr("weapon_profile_save_before_calibration"),
            )
            return
        try:
            CalibrationTestDialog = _load_calibration_test_dialog()
        except Exception as exc:
            QMessageBox.warning(
                self,
                tr("weapon_profile_could_not_open_calibration"),
                tr("weapon_profile_could_not_open_calibration_body", error=exc),
            )
            return

        barrel = dict(self.barrels[row])
        self.initial_barrel_id = str(barrel.get("id") or "")
        dialog = CalibrationTestDialog(
            parent=self,
            profile={
                "weapon_type": self.weapon_type.currentText(),
                "preferred_units": self.preferred_units.currentText(),
                "barrels": self.barrels,
                "active_barrel_id": self.initial_barrel_id,
            },
            existing={"bullet": "", "powder": "", "notes": ""},
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.gather()
        loads = data.get("loads", [])
        if not loads:
            QMessageBox.information(
                self,
                tr("weapon_profile_no_data_saved"),
                tr("weapon_profile_no_data_saved_body"),
            )
            return

        calibration_tests = list(barrel.get("calibration_tests") or [])
        calibration_tests.append(
            {
                "id": f"ct-{len(calibration_tests) + 1}",
                "barrel_id": barrel.get("id"),
                "barrel_name": barrel.get("name"),
                "created_date": datetime.now().isoformat(timespec="seconds"),
                "distance_m": data.get("distance_m"),
                "temperature_c": data.get("temperature_c"),
                "loads": loads,
                "notes": data.get("notes", ""),
            }
        )
        barrel["calibration_tests"] = calibration_tests
        self.barrels[row] = barrel
        if not self._save_profile_details():
            QMessageBox.warning(
                self,
                tr("weapon_profile_save_failed"),
                tr("weapon_profile_calibration_not_saved"),
            )
            return
        self.refresh_barrel_list()
        self.barrel_list.setCurrentRow(row)
        show_toast(
            self,
            f"Kalibrering lagret for {barrel.get('name') or 'pipe'}",
            kind="success",
        )

    def _find_builder_launcher(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "show_modern_load_builder"):
                return parent
            parent = parent.parent() if hasattr(parent, "parent") else None
        return None

    def open_builder_for_selected_barrel(self):
        row = self.barrel_list.currentRow()
        if row < 0 or row >= len(self.barrels):
            QMessageBox.information(
                self, tr("msg_no_selection"), tr("weapon_profile_select_barrel_first")
            )
            return
        if not self.rifle_id:
            QMessageBox.information(
                self,
                tr("weapon_profile_save_first"),
                tr("weapon_profile_save_before_builder"),
            )
            return

        barrel = self.barrels[row]
        self.initial_barrel_id = str(barrel.get("id") or "")
        if not self._save_profile_details():
            QMessageBox.warning(
                self,
                tr("weapon_profile_could_not_save"),
                tr("weapon_profile_builder_barrel_not_saved"),
            )
            return

        settings = QSettings("ReloadingWorkshop", "ReloadingManager")
        settings.setValue("pending_builder_rifle_id", self.rifle_id)
        settings.setValue("pending_builder_barrel_id", self.initial_barrel_id)

        launcher = self._find_builder_launcher()
        self.accept()
        if launcher is not None:
            try:
                launcher.show_modern_load_builder()
                return
            except Exception as exc:
                logger.exception("Failed to open builder from weapon profile: %s", exc)
        QMessageBox.information(
            self,
            tr("weapon_profile_builder_ready"),
            tr("weapon_profile_builder_ready_body"),
        )

    def open_ammo_test_for_selected_barrel(self):
        row = self.barrel_list.currentRow()
        if row < 0 or row >= len(self.barrels):
            QMessageBox.information(
                self, tr("msg_no_selection"), tr("weapon_profile_select_barrel_first")
            )
            return
        if not self.rifle_id:
            QMessageBox.information(
                self,
                tr("weapon_profile_save_first"),
                tr("weapon_profile_save_before_builder"),
            )
            return
        barrel = self.barrels[row]
        dialog_cls = _load_ammo_test_dialog()
        dialog = dialog_cls(
            db=self.db,
            language=get_current_language() or "en",
            rifle_id=self.rifle_id,
            barrel_id=barrel.get("id"),
            barrel_name=barrel.get("name") or tr("weapon_profile_selected_barrel"),
            ammo_type=(
                "rimfire"
                if self.caliber_edit.currentText().strip().lower()
                in {"22lr", ".22lr", ".22 lr"}
                else "centerfire"
            ),
            parent=self,
        )
        dialog.exec()

    def add_barrel(self):
        dialog = BarrelEditorDialog(
            {
                "id": str(uuid.uuid4()),
                "caliber": self.caliber_edit.currentText().strip(),
                "usage_type": "general",
                "status": "active",
            },
            self,
            db=self.db,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.barrels.append(dialog.gather())
            self.refresh_barrel_list()

    def edit_selected_barrel(self):
        row = self.barrel_list.currentRow()
        if row < 0 or row >= len(self.barrels):
            QMessageBox.information(
                self, tr("msg_no_selection"), tr("weapon_profile_select_barrel_first")
            )
            return
        dialog = BarrelEditorDialog(self.barrels[row], self, db=self.db)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.barrels[row] = dialog.gather()
            self.refresh_barrel_list()
            self.barrel_list.setCurrentRow(row)

    def remove_selected_barrel(self):
        row = self.barrel_list.currentRow()
        if row < 0 or row >= len(self.barrels):
            QMessageBox.information(
                self, tr("msg_no_selection"), tr("weapon_profile_select_barrel_first")
            )
            return
        del self.barrels[row]
        self.refresh_barrel_list()
        if not self.barrels:
            self.refresh_selected_barrel_summary()
            return
        self.barrel_list.setCurrentRow(min(row, len(self.barrels) - 1))
        self.refresh_selected_barrel_summary()

    def on_save(self):
        data = {
            "name": self.name_edit.text().strip(),
            "manufacturer": self.manufacturer_edit.text().strip(),
            "model": self.model_edit.text().strip(),
            "weapon_type": self.weapon_type.currentText(),
            "caliber": self.caliber_edit.currentText().strip(),
            "action_type": self.action_type.currentText(),
            "preferred_units": self.preferred_units.currentText(),
            "serial_number": self.serial_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
        }
        if not data["name"] or not data["caliber"]:
            QMessageBox.warning(
                self,
                tr("weapon_profile_missing_data"),
                tr("weapon_profile_missing_data_body"),
            )
            return

        optic_data = {
            "name": self.optic_name_edit.text().strip(),
            "manufacturer": self.optic_manufacturer_edit.text().strip(),
            "zero_distance_m": self.optic_zero_distance_edit.text().strip(),
            "turret_unit": self.optic_unit_combo.currentText(),
            "click_value": self.optic_click_value_edit.text().strip(),
            "clicks_per_rev": self.optic_clicks_per_rev_edit.text().strip(),
        }

        details_payload = {
            "weapon_type": data["weapon_type"],
            "preferred_units": data["preferred_units"],
            "active_barrel_id": self.initial_barrel_id,
            "barrels": self.barrels,
            "optic": optic_data,
        }

        # Remove empty keys not present in schema will be ignored by DB layer
        if self.rifle_id:
            self.db.update("rifles", data, "id = ?", (self.rifle_id,))
            existing = self.db.execute_query(
                "SELECT id FROM rifle_profile_details WHERE rifle_id = ?",
                (self.rifle_id,),
            )
            if existing:
                self.db.update(
                    "rifle_profile_details",
                    {"profile_json": json.dumps(details_payload, ensure_ascii=False)},
                    "rifle_id = ?",
                    (self.rifle_id,),
                )
            else:
                self.db.insert(
                    "rifle_profile_details",
                    {
                        "rifle_id": self.rifle_id,
                        "profile_json": json.dumps(details_payload, ensure_ascii=False),
                    },
                )
            logger.info("Updated rifle id %s", self.rifle_id)
            self.accept()
        else:
            new_id = self.db.insert("rifles", data)
            if new_id is None:
                logger.error("Failed to insert rifle")
                QMessageBox.critical(
                    self,
                    tr("msg_error"),
                    tr("weapon_profile_create_failed", error="insert returned None"),
                )
                return
            detail_id = self.db.insert(
                "rifle_profile_details",
                {
                    "rifle_id": new_id,
                    "profile_json": json.dumps(details_payload, ensure_ascii=False),
                },
            )
            if detail_id is None:
                logger.error(
                    "Failed to insert rifle_profile_details for rifle %s", new_id
                )
            logger.info("Inserted new rifle id %s", new_id)
            self.rifle_id = new_id
            self.accept()

    def on_delete(self):
        if not self.rifle_id:
            return
        ok = QMessageBox.question(
            self,
            tr("msg_confirm_delete"),
            tr("weapon_profile_confirm_delete"),
        )
        if ok == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete("rifles", "id = ?", (self.rifle_id,))
                logger.info("Deleted rifle id %s", self.rifle_id)
                self.accept()
            except Exception as e:
                logger.exception("Failed to delete rifle: %s", e)
                QMessageBox.critical(
                    self,
                    tr("msg_error"),
                    tr("weapon_profile_delete_failed", error=e),
                )
