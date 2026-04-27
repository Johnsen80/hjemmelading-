from __future__ import annotations

from datetime import date as _date
from typing import Any, Dict, Optional

from src.utils.i18n import tr

from ..database.database import get_database
from ..database.saami_seed import lookup as saami_lookup
from ..database.saami_seed import seed_if_empty as saami_seed
from ..modules.component_database import load_component_database_json
from ..qt_compat import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QtWidgets,
    QVBoxLayout,
    QWidget,
)


def _seed_components_if_empty(db) -> None:
    """Import powder / bullets / primers from bundled JSON if SQL tables are empty."""
    try:
        if not db:
            return
        if db.execute_query("SELECT COUNT(*) AS n FROM powder")[0]["n"] == 0:
            components = load_component_database_json()
            for p in components.get("powders", []):
                db.insert(
                    "powder",
                    {
                        "name": p.get("name", ""),
                        "manufacturer": p.get("manufacturer", ""),
                        "type": p.get("type", ""),
                        "burn_rate": p.get("burn_rate", ""),
                        "density": p.get("density"),
                        "notes": p.get("notes", ""),
                    },
                )
        if db.execute_query("SELECT COUNT(*) AS n FROM bullets")[0]["n"] == 0:
            components = load_component_database_json()
            for b in components.get("bullets", []):
                db.insert(
                    "bullets",
                    {
                        "name": b.get("name", ""),
                        "manufacturer": b.get("manufacturer", ""),
                        "caliber": b.get("caliber", ""),
                        "weight_grains": b.get("weight", 0),
                        "bc_g1": b.get("bc_g1"),
                        "bc_g7": b.get("bc_g7"),
                        "bullet_type": b.get("type", ""),
                        "notes": b.get("notes", ""),
                    },
                )
        if db.execute_query("SELECT COUNT(*) AS n FROM primers")[0]["n"] == 0:
            components = load_component_database_json()
            for pr in components.get("primers", []):
                db.insert(
                    "primers",
                    {
                        "name": pr.get("name", ""),
                        "manufacturer": pr.get("manufacturer", ""),
                        "type": pr.get("type", ""),
                        "size": pr.get("size", ""),
                        "notes": pr.get("notes", ""),
                    },
                )
    except Exception:
        pass


BARREL_PROFILE_PRESETS: dict[str, dict[str, Any]] = {
    "custom": {
        "label_key": "barrel_profile_custom_label",
        "description_key": "barrel_profile_custom_description",
        "silhouette": "[==== user defined ====]",
        "defaults": {},
    },
    "sporter": {
        "label_key": "barrel_profile_sporter_label",
        "description_key": "barrel_profile_sporter_description",
        "silhouette": "[======----]",
        "defaults": {"barrel_profile": "light", "usage_type": "hunting"},
    },
    "medium": {
        "label_key": "barrel_profile_medium_label",
        "description_key": "barrel_profile_medium_description",
        "silhouette": "[========--]",
        "defaults": {"barrel_profile": "medium", "usage_type": "general"},
    },
    "heavy": {
        "label_key": "barrel_profile_heavy_label",
        "description_key": "barrel_profile_heavy_description",
        "silhouette": "[==========]",
        "defaults": {"barrel_profile": "heavy", "usage_type": "competition"},
    },
    "bull": {
        "label_key": "barrel_profile_bull_label",
        "description_key": "barrel_profile_bull_description",
        "silhouette": "[############]",
        "defaults": {"barrel_profile": "bull", "usage_type": "competition"},
    },
    "pistol_standard": {
        "label_key": "barrel_profile_pistol_standard_label",
        "description_key": "barrel_profile_pistol_standard_description",
        "silhouette": "[==== pistol ====]",
        "defaults": {"barrel_profile": "medium", "usage_type": "general"},
    },
    "pistol_match": {
        "label_key": "barrel_profile_pistol_match_label",
        "description_key": "barrel_profile_pistol_match_description",
        "silhouette": "[====== pistol+]",
        "defaults": {"barrel_profile": "heavy", "usage_type": "competition"},
    },
}

BARREL_ATTACHMENT_PRESETS: dict[str, dict[str, Any]] = {
    "unknown": {
        "label_key": "barrel_attachment_unknown_label",
        "description_key": "barrel_attachment_unknown_description",
        "silhouette": "[ ? ] receiver ? barrel",
        "defaults": {},
    },
    "threaded": {
        "label_key": "barrel_attachment_threaded_label",
        "description_key": "barrel_attachment_threaded_description",
        "silhouette": "[receiver]==////==[barrel]",
        "defaults": {
            "barrel_attachment_type": "threaded",
            "mount_type": "threaded",
            "action_stiffness": "normal",
        },
    },
    "barrel_nut": {
        "label_key": "barrel_attachment_barrel_nut_label",
        "description_key": "barrel_attachment_barrel_nut_description",
        "silhouette": "[receiver]=={nut}==[barrel]",
        "defaults": {
            "barrel_attachment_type": "barrel_nut",
            "mount_type": "barrel_nut",
            "action_stiffness": "normal",
        },
    },
    "quick_change": {
        "label_key": "barrel_attachment_quick_change_label",
        "description_key": "barrel_attachment_quick_change_description",
        "silhouette": "[receiver]==<clamp>==[barrel]",
        "defaults": {
            "barrel_attachment_type": "quick_change",
            "mount_type": "quick_change",
            "action_stiffness": "rigid",
        },
    },
    "press_fit": {
        "label_key": "barrel_attachment_press_fit_label",
        "description_key": "barrel_attachment_press_fit_description",
        "silhouette": "[receiver]==(press)==[barrel]",
        "defaults": {
            "barrel_attachment_type": "press_fit",
            "mount_type": "press_fit",
            "action_stiffness": "normal",
        },
    },
    "integrated_pistol": {
        "label_key": "barrel_attachment_integrated_pistol_label",
        "description_key": "barrel_attachment_integrated_pistol_description",
        "silhouette": "[slide/frame]==[barrel]",
        "defaults": {
            "barrel_attachment_type": "integrated_pistol",
            "mount_type": "pistol_standard",
            "action_stiffness": "normal",
        },
    },
}


def get_caliber_library_options(db=None) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    try:
        database = db or get_database()
        standards = database.list_cartridge_standards()
    except Exception:
        standards = []

    for row in standards:
        for key in ("caliber_name", "alt_name"):
            value = str(row.get(key) or "").strip()
            normalized = value.casefold()
            if value and normalized not in seen:
                seen.add(normalized)
                values.append(value)
    return sorted(values, key=str.casefold)


def build_caliber_combo(current_value: str = "", db=None) -> QComboBox:
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItems(get_caliber_library_options(db))
    combo.setCurrentText(current_value or "")
    return combo


class BarrelEditorDialog(QDialog):
    """Simple dialog to edit a barrel dict.

    The dialog expects a barrel-like dict and returns the updated dict via
    `gather()` if accepted. For now measurement points can be edited as JSON
    in a textarea (simple and robust for first iteration).
    """

    def __init__(
        self, barrel: Optional[Dict[str, Any]] = None, parent=None, db=None
    ) -> None:
        super().__init__(parent)
        self._db = db or getattr(parent, "db", None)
        try:
            from src.ui.theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            pass
        self.setWindowTitle(tr("barrel_editor_title"))
        self.resize(680, 720)
        self._barrel = barrel.copy() if barrel else {}
        # Seed SAAMI data if table is empty
        try:
            _startup_db = self._db or get_database()
            saami_seed(_startup_db)
            _seed_components_if_empty(_startup_db)
        except Exception:
            pass
        self.init_ui()

    def init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tabs = QTabWidget(self)
        tabs.setDocumentMode(True)
        root.addWidget(tabs, 1)

        # ── Tab 0: Pipe ──────────────────────────────────────────────────────
        tab_pipe = QWidget()
        pipe_outer = QVBoxLayout(tab_pipe)
        pipe_outer.setContentsMargins(0, 0, 0, 0)
        scroll_pipe = QtWidgets.QScrollArea()
        scroll_pipe.setWidgetResizable(True)
        try:
            scroll_pipe.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        except Exception:
            pass
        pipe_inner = QWidget()
        form_pipe = QFormLayout(pipe_inner)
        form_pipe.setContentsMargins(16, 16, 16, 16)
        form_pipe.setSpacing(10)
        scroll_pipe.setWidget(pipe_inner)
        pipe_outer.addWidget(scroll_pipe)
        tabs.addTab(tab_pipe, tr("barrel_editor_tab_pipe"))

        self.profile_combo = QComboBox()
        for profile_id, meta in BARREL_PROFILE_PRESETS.items():
            self.profile_combo.addItem(tr(str(meta["label_key"])), profile_id)
        current_profile_id = self._barrel.get("barrel_profile_id") or "custom"
        self.profile_combo.setCurrentIndex(
            max(0, self.profile_combo.findData(current_profile_id))
        )
        self.profile_combo.currentIndexChanged.connect(self.update_profile_preview)
        form_pipe.addRow(tr("barrel_editor_profile"), self.profile_combo)

        self.profile_preview = QLabel()
        self.profile_preview.setWordWrap(True)
        self.profile_preview.setStyleSheet(
            "padding: 8px; border: 1px solid #3c4250; border-radius: 6px;"
        )
        form_pipe.addRow("", self.profile_preview)

        self.attachment_combo = QComboBox()
        for attachment_id, meta in BARREL_ATTACHMENT_PRESETS.items():
            self.attachment_combo.addItem(tr(str(meta["label_key"])), attachment_id)
        current_attachment_id = self._barrel.get("barrel_attachment_type") or "unknown"
        self.attachment_combo.setCurrentIndex(
            max(0, self.attachment_combo.findData(current_attachment_id))
        )
        self.attachment_combo.currentIndexChanged.connect(
            self.update_attachment_preview
        )
        form_pipe.addRow(tr("barrel_editor_attachment"), self.attachment_combo)

        self.attachment_preview = QLabel()
        self.attachment_preview.setWordWrap(True)
        self.attachment_preview.setStyleSheet(
            "padding: 8px; border: 1px solid #3c4250; border-radius: 6px;"
        )
        form_pipe.addRow("", self.attachment_preview)

        self.name_edit = QLineEdit(self._barrel.get("name", ""))
        self.name_edit.setPlaceholderText(tr("barrel_editor_name_placeholder"))
        form_pipe.addRow(tr("barrel_editor_name"), self.name_edit)

        self.caliber_edit = build_caliber_combo(
            self._barrel.get("caliber", ""), db=self._db
        )
        self.caliber_edit.currentTextChanged.connect(self._on_caliber_changed)
        form_pipe.addRow(tr("barrel_editor_caliber"), self.caliber_edit)

        self.saami_label = QLabel("", self)
        self.saami_label.setWordWrap(True)
        self.saami_label.setStyleSheet(
            "padding: 6px 10px; border-left: 3px solid #2980b9; color: #b0b6be; font-size: 10pt;"
        )
        self.saami_label.setVisible(False)
        form_pipe.addRow("SAAMI / CIP", self.saami_label)

        self.length_edit = QLineEdit(str(self._barrel.get("length_mm", "")))
        self.length_edit.setPlaceholderText("mm — f.eks. 610 (24 tommer = 609.6 mm)")
        form_pipe.addRow(tr("barrel_editor_length_mm"), self.length_edit)

        self.twist_edit = QLineEdit(self._barrel.get("twist", ""))
        self.twist_edit.setPlaceholderText(tr("barrel_editor_twist_placeholder"))
        form_pipe.addRow(tr("barrel_editor_twist"), self.twist_edit)

        self.material_edit = QComboBox()
        self.material_edit.setEditable(True)
        self.material_edit.addItems(
            [
                "",
                "416R rustfritt stål",
                "CM4140 / 4140 krom-molybden stål",
                "CM4150 stål",
                "17-4PH rustfritt stål",
                "Lothar Walther (rustfritt)",
                "Lothar Walther (legert stål)",
                "Krieger (rustfritt)",
                "Bartlein (rustfritt)",
                "Shilen (rustfritt)",
                "Karbonfiber-innpakket",
                "Titan",
            ]
        )
        self.material_edit.setCurrentText(self._barrel.get("material", "") or "")
        form_pipe.addRow(tr("barrel_editor_material"), self.material_edit)

        self.usage_type_edit = QComboBox()
        for _key, _label in [
            ("", tr("barrel_editor_usage_select")),
            ("hunting", tr("barrel_editor_usage_hunting")),
            ("precision", tr("barrel_editor_usage_precision")),
            ("competition", tr("barrel_editor_usage_competition")),
            ("varmint", tr("barrel_editor_usage_varmint")),
            ("general", tr("barrel_editor_usage_general")),
            ("home_defense", tr("barrel_editor_usage_home_defense")),
            ("sport", tr("barrel_editor_usage_sport")),
        ]:
            self.usage_type_edit.addItem(_label, _key)
        _cur_usage = self._barrel.get("usage_type", "") or ""
        _idx_usage = self.usage_type_edit.findData(_cur_usage)
        self.usage_type_edit.setCurrentIndex(_idx_usage if _idx_usage >= 0 else 0)
        form_pipe.addRow(tr("barrel_editor_usage_type"), self.usage_type_edit)

        self.status_edit = QComboBox()
        for _key, _label in [
            ("active", tr("barrel_editor_status_active")),
            ("testing", tr("barrel_editor_status_testing")),
            ("retired", tr("barrel_editor_status_retired")),
        ]:
            self.status_edit.addItem(_label, _key)
        _cur_status = self._barrel.get("status", "active") or "active"
        _idx_status = self.status_edit.findData(_cur_status)
        self.status_edit.setCurrentIndex(_idx_status if _idx_status >= 0 else 0)
        form_pipe.addRow(tr("barrel_editor_status"), self.status_edit)

        self.mount_edit = QComboBox()
        for _key, _label in [
            ("", tr("barrel_editor_mount_unknown")),
            ("threaded", tr("barrel_editor_mount_threaded")),
            ("barrel_nut", tr("barrel_editor_mount_barrel_nut")),
            ("quick_change", tr("barrel_editor_mount_quick_change")),
            ("press_fit", tr("barrel_editor_mount_press_fit")),
            ("integrated_pistol", tr("barrel_editor_mount_integrated_pistol")),
        ]:
            self.mount_edit.addItem(_label, _key)
        _cur_mount = self._barrel.get("mount_type", "") or ""
        _idx_mount = self.mount_edit.findData(_cur_mount)
        self.mount_edit.setCurrentIndex(_idx_mount if _idx_mount >= 0 else 0)
        form_pipe.addRow(tr("barrel_editor_mount_type"), self.mount_edit)

        self.action_stiffness_edit = QComboBox()
        for _key, _label in [
            ("", tr("barrel_editor_stiffness_unknown")),
            ("normal", tr("barrel_editor_stiffness_normal")),
            ("rigid", tr("barrel_editor_stiffness_rigid")),
            ("loose", tr("barrel_editor_stiffness_loose")),
        ]:
            self.action_stiffness_edit.addItem(_label, _key)
        _cur_stiff = self._barrel.get("action_stiffness", "") or ""
        _idx_stiff = self.action_stiffness_edit.findData(_cur_stiff)
        self.action_stiffness_edit.setCurrentIndex(_idx_stiff if _idx_stiff >= 0 else 0)
        form_pipe.addRow(
            tr("barrel_editor_action_stiffness"), self.action_stiffness_edit
        )

        self.torque_edit = QLineEdit(str(self._barrel.get("barrel_torque_nm", "")))
        self.torque_edit.setPlaceholderText(tr("barrel_editor_torque_placeholder"))
        form_pipe.addRow(tr("barrel_editor_torque_nm"), self.torque_edit)

        self.repeatability_edit = QLineEdit(
            self._barrel.get("barrel_return_to_zero", "")
        )
        self.repeatability_edit.setPlaceholderText(
            tr("barrel_editor_return_to_zero_placeholder")
        )
        form_pipe.addRow(tr("barrel_editor_return_to_zero"), self.repeatability_edit)

        # ── Tab 1: Munnstykke ────────────────────────────────────────────────
        tab_muzzle = QWidget()
        muzzle_form = QFormLayout(tab_muzzle)
        muzzle_form.setContentsMargins(16, 16, 16, 16)
        muzzle_form.setSpacing(10)
        tabs.addTab(tab_muzzle, tr("barrel_editor_tab_muzzle"))

        _muzzle_info = QLabel(tr("barrel_editor_muzzle_info"))
        _muzzle_info.setWordWrap(True)
        _muzzle_info.setStyleSheet(
            "color: #b0b6be; font-style: italic; margin-bottom: 8px;"
        )
        muzzle_form.addRow(_muzzle_info)

        self.muzzle_type_combo = QComboBox()
        for key, label in [
            ("none", tr("barrel_editor_muzzle_type_none")),
            ("suppressor", tr("barrel_editor_muzzle_type_suppressor")),
            ("brake", tr("barrel_editor_muzzle_type_brake")),
            ("compensator", tr("barrel_editor_muzzle_type_compensator")),
            ("flash_hider", tr("barrel_editor_muzzle_type_flash_hider")),
            ("other", tr("barrel_editor_muzzle_type_other")),
        ]:
            self.muzzle_type_combo.addItem(label, key)
        _cur_type = self._barrel.get("muzzle_device_type") or "none"
        self.muzzle_type_combo.setCurrentIndex(
            max(0, self.muzzle_type_combo.findData(_cur_type))
        )
        muzzle_form.addRow(
            tr("barrel_editor_muzzle_type_combo"), self.muzzle_type_combo
        )

        self.muzzle_mount_combo = QComboBox()
        for key, label in [
            ("direct", tr("barrel_editor_muzzle_mount_direct")),
            ("qd", tr("barrel_editor_muzzle_mount_qd")),
            ("clamp", tr("barrel_editor_muzzle_mount_clamp")),
        ]:
            self.muzzle_mount_combo.addItem(label, key)
        _cur_mount = self._barrel.get("muzzle_mount_type") or "direct"
        self.muzzle_mount_combo.setCurrentIndex(
            max(0, self.muzzle_mount_combo.findData(_cur_mount))
        )
        muzzle_form.addRow(tr("barrel_editor_muzzle_mount"), self.muzzle_mount_combo)

        self.muzzle_model_edit = QLineEdit(self._barrel.get("muzzle_device_model", ""))
        self.muzzle_model_edit.setPlaceholderText(
            tr("barrel_editor_muzzle_model_placeholder")
        )
        muzzle_form.addRow(
            tr("barrel_editor_muzzle_device_model"), self.muzzle_model_edit
        )

        self.muzzle_thread_edit = QComboBox()
        self.muzzle_thread_edit.setEditable(True)
        self.muzzle_thread_edit.addItems(
            [
                "",
                # ── Imperial / SAE (UNEF) ─────────────────────────────────────────
                "1/2×28 UNEF",  # .22LR, .223/5.56 — AR-15, Ruger 10/22 m.fl.
                "9/16×24 UNEF",  # 9 mm pistolkaliber
                "9/16×28 UNEF",  # alternativ 9 mm
                "5/8×24 UNEF",  # .30-kaliber — .308, 300WM, 6.5CM m.fl. (vanligst)
                "5/8×32 UNEF",  # alternativ .30-kaliber
                "11/16×24 UNEF",  # .40 S&W pistol
                "3/4×24 UNEF",  # .338, .375 og større bore
                "3/4×32 UNEF",  # stor bore, alternativ
                "13/16×16 UNEF",  # .45 ACP pistol
                "1×28 UNEF",  # stor bore gevær
                "1/2×36 UNEF",  # .22LR alternativ
                # ── Metrisk (høyrehånds) ─────────────────────────────────────────
                "M12×0.75",  # .22/9mm pistol, noen europeiske modeller
                "M13×1 LH",  # venstregjenget, noen europeiske geværer
                "M13.5×1 LH",  # CZ pistol (.40/.45), venstregjenget
                "M14×1",  # AK-varianter, europeiske rifler
                "M14×1 LH",  # venstregjenget versjon (SIG, MP5 m.fl.)
                "M15×1",  # CZ og noen tsjekkiske/slovakiske rifler
                "M16×1",  # større pistolkaliber, europeisk
                "M18×1",  # .308 / 6.5-kaliber europeisk gevær
                "M18×1.5",  # stor bore europeisk
                "M20×1",  # .338 og oppover, nordeuropeisk
                "M22×1.5",  # store kalibre
                "M24×1.5",  # store kalibre, .375 og oppover
                # ── Nordisk / Skandinavisk ──────────────────────────────────────
                "M15×1 (Sauer/Blaser)",
                "M18×1 (Tikka/Sako)",
                "M19×1",  # noen Sako-modeller
                # ── Andre standarder ────────────────────────────────────────────
                "A2 flash hider (5/8×24 innebygd)",
                "Ikke gjenget (glatt munnstykke)",
            ]
        )
        self.muzzle_thread_edit.setCurrentText(
            self._barrel.get("muzzle_thread_pitch", "") or ""
        )
        muzzle_form.addRow(
            tr("barrel_editor_muzzle_thread_pitch"), self.muzzle_thread_edit
        )

        self.muzzle_weight_edit = QLineEdit(
            str(self._barrel.get("muzzle_device_weight_g", ""))
        )
        self.muzzle_weight_edit.setPlaceholderText(
            tr("barrel_editor_muzzle_weight_placeholder")
        )
        muzzle_form.addRow(
            tr("barrel_editor_muzzle_device_weight_g"), self.muzzle_weight_edit
        )

        self.muzzle_length_edit = QLineEdit(
            str(self._barrel.get("muzzle_device_length_mm", ""))
        )
        self.muzzle_length_edit.setPlaceholderText(
            tr("barrel_editor_muzzle_length_placeholder")
        )
        muzzle_form.addRow(
            tr("barrel_editor_muzzle_device_length_mm"), self.muzzle_length_edit
        )

        self.muzzle_protrusion_edit = QLineEdit(
            str(self._barrel.get("muzzle_protrusion_mm", ""))
        )
        self.muzzle_protrusion_edit.setPlaceholderText(
            tr("barrel_editor_muzzle_protrusion_placeholder")
        )
        muzzle_form.addRow(
            tr("barrel_editor_muzzle_protrusion_mm"), self.muzzle_protrusion_edit
        )

        # ── Tab 2: Skutt messing ─────────────────────────────────────────────
        tab_brass = QWidget()
        brass_outer = QVBoxLayout(tab_brass)
        brass_outer.setContentsMargins(0, 0, 0, 0)
        scroll_brass = QtWidgets.QScrollArea()
        scroll_brass.setWidgetResizable(True)
        try:
            scroll_brass.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        except Exception:
            pass
        brass_inner = QWidget()
        brass_layout = QVBoxLayout(brass_inner)
        brass_layout.setContentsMargins(16, 16, 16, 16)
        brass_layout.setSpacing(12)
        scroll_brass.setWidget(brass_inner)
        brass_outer.addWidget(scroll_brass)
        tabs.addTab(tab_brass, tr("barrel_editor_tab_brass"))

        brass_info = QLabel(tr("barrel_editor_brass_info"))
        brass_info.setWordWrap(True)
        brass_info.setStyleSheet(
            "padding: 10px 12px; border-left: 4px solid #2980b9; color: #b0b6be; font-size: 10pt;"
        )
        brass_layout.addWidget(brass_info)

        # H2O capacity
        h2o_group = QGroupBox(tr("barrel_editor_h2o_group"))
        h2o_outer = QVBoxLayout(h2o_group)
        h2o_outer.setSpacing(6)
        h2o_outer.setContentsMargins(8, 8, 8, 8)

        case_data = self._barrel.get("case_measurements", {}) or {}

        # Summary row: gjennomsnitt + live stats
        h2o_summary_row = QHBoxLayout()
        _avg_lbl = QLabel(tr("barrel_editor_h2o_avg_label"))
        h2o_summary_row.addWidget(_avg_lbl)
        self.h2o_capacity_edit = QLineEdit(
            str(case_data.get("h2o_capacity_grains", ""))
        )
        self.h2o_capacity_edit.setPlaceholderText(
            tr("barrel_editor_h2o_auto_placeholder")
        )
        self.h2o_capacity_edit.setMaximumWidth(90)
        h2o_summary_row.addWidget(self.h2o_capacity_edit)
        h2o_summary_row.addWidget(QLabel("gr"))
        self.h2o_stats_label = QLabel(tr("barrel_editor_h2o_no_measurements"))
        self.h2o_stats_label.setStyleSheet(
            "color: #b0b6be; font-size: 10pt; margin-left: 10px;"
        )
        h2o_summary_row.addWidget(self.h2o_stats_label)
        h2o_summary_row.addStretch()
        h2o_outer.addLayout(h2o_summary_row)

        # Measurement table: Nr | Tørr (gr) | Våt (gr) | H₂O (gr)
        _h2o_cols = [
            tr("barrel_editor_h2o_col_nr"),
            tr("barrel_editor_h2o_col_dry"),
            tr("barrel_editor_h2o_col_wet"),
            tr("barrel_editor_h2o_col_h2o"),
        ]
        self.h2o_table = QTableWidget(0, len(_h2o_cols))
        self.h2o_table.setHorizontalHeaderLabels(_h2o_cols)
        _h2o_hdr = self.h2o_table.horizontalHeader()
        if _h2o_hdr:
            for _ci in range(len(_h2o_cols)):
                _h2o_hdr.setSectionResizeMode(
                    _ci, QHeaderView.ResizeMode.ResizeToContents
                )
            _h2o_hdr.setStretchLastSection(True)
        self.h2o_table.setMinimumHeight(180)
        self.h2o_table.setMaximumHeight(320)
        self.h2o_table.setAlternatingRowColors(True)
        self.h2o_table.itemChanged.connect(self._on_h2o_table_changed)
        h2o_outer.addWidget(self.h2o_table)

        # Buttons
        h2o_btn_row = QHBoxLayout()
        _add_h2o_btn = QPushButton(tr("barrel_editor_h2o_add_row"))
        _add_h2o_btn.clicked.connect(self._on_add_h2o_row)
        _remove_h2o_btn = QPushButton(tr("barrel_editor_h2o_remove_row"))
        _remove_h2o_btn.clicked.connect(self._on_remove_h2o_row)
        _fill10_btn = QPushButton(tr("barrel_editor_h2o_fill_rows"))
        _fill10_btn.clicked.connect(lambda: self._on_fill_h2o_rows(10))
        h2o_btn_row.addWidget(_add_h2o_btn)
        h2o_btn_row.addWidget(_remove_h2o_btn)
        h2o_btn_row.addWidget(_fill10_btn)
        h2o_btn_row.addStretch()
        h2o_outer.addLayout(h2o_btn_row)

        brass_layout.addWidget(h2o_group)

        # Load existing H2O measurements into table
        self._load_h2o_table(case_data)

        # Brass measurement table
        brass_table_hdr = QLabel(tr("barrel_editor_brass_dim_header"))
        brass_table_hdr.setStyleSheet("font-size: 11pt; margin-top: 4px;")
        brass_layout.addWidget(brass_table_hdr)

        brass_col_hint = QLabel(tr("barrel_editor_brass_col_hint"))
        brass_col_hint.setWordWrap(True)
        brass_col_hint.setStyleSheet(
            "color: #b0b6be; font-size: 10pt; font-style: italic;"
        )
        brass_layout.addWidget(brass_col_hint)

        _brass_cols = [
            tr("barrel_editor_brass_col_date"),
            tr("barrel_editor_brass_col_firings"),
            tr("barrel_editor_brass_col_trim"),
            tr("barrel_editor_brass_col_neck"),
            tr("barrel_editor_brass_col_shoulder"),
            tr("barrel_editor_brass_col_headspace"),
            tr("barrel_editor_brass_col_velocity"),
            tr("barrel_editor_brass_col_notes"),
        ]
        self.brass_table = QTableWidget(0, len(_brass_cols))
        self.brass_table.setHorizontalHeaderLabels(_brass_cols)
        _bh = self.brass_table.horizontalHeader()
        if _bh:
            _bh.setStretchLastSection(True)
            for _ci in range(len(_brass_cols) - 1):
                _bh.setSectionResizeMode(_ci, QHeaderView.ResizeMode.ResizeToContents)
        self.brass_table.setMinimumHeight(200)
        self.brass_table.setAlternatingRowColors(True)
        self.brass_table.itemChanged.connect(self._on_brass_table_changed)
        brass_layout.addWidget(self.brass_table)

        # Load legacy data into table
        self._load_brass_table(case_data)

        brass_btn_row = QHBoxLayout()
        _add_brass_btn = QPushButton(tr("barrel_editor_brass_add_session"))
        _add_brass_btn.clicked.connect(self._on_add_brass_row)
        _remove_brass_btn = QPushButton(tr("barrel_editor_brass_remove_row"))
        _remove_brass_btn.clicked.connect(self._on_remove_brass_row)
        _calc_brass_btn = QPushButton(tr("barrel_editor_brass_calc_stats"))
        _calc_brass_btn.clicked.connect(self._recalc_brass_stats)
        brass_btn_row.addWidget(_add_brass_btn)
        brass_btn_row.addWidget(_remove_brass_btn)
        brass_btn_row.addWidget(_calc_brass_btn)
        brass_btn_row.addStretch()
        brass_layout.addLayout(brass_btn_row)

        self.brass_stats_label = QLabel("")
        self.brass_stats_label.setWordWrap(True)
        self.brass_stats_label.setStyleSheet(
            "padding: 8px; border: 1px solid #3c4250; border-radius: 6px; "
            "color: #b0b6be; font-size: 10pt;"
        )
        self.brass_stats_label.setVisible(False)
        brass_layout.addWidget(self.brass_stats_label)

        # SAAMI inline comparison (mirrors Pipe-fane's saami_label)
        self.brass_saami_label = QLabel("")
        self.brass_saami_label.setWordWrap(True)
        self.brass_saami_label.setStyleSheet(
            "padding: 8px; background: #1a2a1a; border-left: 3px solid #27ae60; "
            "border-radius: 4px; color: #b0e0b0; font-size: 10pt;"
        )
        self.brass_saami_label.setVisible(False)
        brass_layout.addWidget(self.brass_saami_label)

        self.case_notes_edit = QTextEdit()
        self.case_notes_edit.setPlaceholderText(
            tr("barrel_editor_case_notes_placeholder")
        )
        self.case_notes_edit.setPlainText(str(case_data.get("notes", "") or ""))
        self.case_notes_edit.setMaximumHeight(70)
        _cnf = QFormLayout()
        _cnf.addRow(tr("barrel_editor_case_notes"), self.case_notes_edit)
        brass_layout.addLayout(_cnf)
        brass_layout.addStretch()

        # ── Tab 3: Referanseladning ──────────────────────────────────────────
        tab_ref = QWidget()
        ref_outer = QVBoxLayout(tab_ref)
        ref_outer.setContentsMargins(0, 0, 0, 0)
        scroll_ref = QtWidgets.QScrollArea()
        scroll_ref.setWidgetResizable(True)
        try:
            scroll_ref.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        except Exception:
            pass
        ref_inner = QWidget()
        ref_layout = QVBoxLayout(ref_inner)
        ref_layout.setContentsMargins(16, 16, 16, 16)
        ref_layout.setSpacing(12)
        scroll_ref.setWidget(ref_inner)
        ref_outer.addWidget(scroll_ref)
        tabs.addTab(tab_ref, tr("barrel_editor_tab_refload"))

        ref_group = QGroupBox(tr("barrel_editor_refload_group"))
        ref_form = QFormLayout(ref_group)
        ref_form.setSpacing(8)
        ref_data = self._barrel.get("reference_load", {}) or {}

        _ref_db = self._db or get_database()

        self.ref_primer_combo = QComboBox()
        self.ref_primer_combo.setEditable(True)
        self.ref_primer_combo.addItem(tr("barrel_editor_ref_primer_placeholder"), None)
        for _pr in _ref_db.execute_query(
            "SELECT id, name, manufacturer, size FROM primers ORDER BY manufacturer, name"
        ):
            _lbl = _pr["name"]
            if _pr.get("manufacturer"):
                _lbl = f"{_pr['manufacturer']} {_lbl}"
            if _pr.get("size"):
                _lbl += f" ({_pr['size']})"
            self.ref_primer_combo.addItem(_lbl, _pr["id"])
        _exist_primer = str(ref_data.get("primer", "") or "")
        if _exist_primer:
            _idx = self.ref_primer_combo.findText(
                _exist_primer, Qt.MatchFlag.MatchContains
            )
            if _idx >= 0:
                self.ref_primer_combo.setCurrentIndex(_idx)
            else:
                self.ref_primer_combo.setCurrentText(_exist_primer)
        ref_form.addRow(tr("barrel_editor_ref_primer_label"), self.ref_primer_combo)

        self.ref_powder_combo = QComboBox()
        self.ref_powder_combo.setEditable(True)
        self.ref_powder_combo.addItem(tr("barrel_editor_ref_powder_placeholder"), None)
        self._ref_bullet_db: list = []
        for _p in _ref_db.execute_query(
            "SELECT id, name, manufacturer FROM powder ORDER BY manufacturer, name"
        ):
            _lbl = _p["name"]
            if _p.get("manufacturer"):
                _lbl += f" ({_p['manufacturer']})"
            self.ref_powder_combo.addItem(_lbl, _p["id"])
        _exist_pid = ref_data.get("powder_id")
        _exist_pname = str(ref_data.get("powder_type", "") or "")
        if _exist_pid is not None:
            _idx = self.ref_powder_combo.findData(_exist_pid)
            self.ref_powder_combo.setCurrentIndex(_idx if _idx >= 0 else 0)
        elif _exist_pname:
            self.ref_powder_combo.setCurrentText(_exist_pname)
        ref_form.addRow(tr("barrel_editor_ref_powder_label"), self.ref_powder_combo)

        self.ref_charge_edit = QLineEdit(str(ref_data.get("powder_charge_gr", "")))
        self.ref_charge_edit.setPlaceholderText(
            tr("barrel_editor_ref_charge_placeholder")
        )
        ref_form.addRow(tr("barrel_editor_ref_charge_label"), self.ref_charge_edit)

        self.ref_bullet_combo = QComboBox()
        self.ref_bullet_combo.setEditable(True)
        self.ref_bullet_combo.addItem(tr("barrel_editor_ref_bullet_placeholder"), None)
        self._ref_bullet_db = _ref_db.execute_query(
            "SELECT id, name, manufacturer, weight_grains, caliber"
            " FROM bullets ORDER BY manufacturer, weight_grains, name"
        )
        for _b in self._ref_bullet_db:
            _lbl = _b["name"]
            if _b.get("weight_grains"):
                _lbl += f" {float(_b['weight_grains']):.0f}gr"
            if _b.get("caliber"):
                _lbl += f" ({_b['caliber']})"
            self.ref_bullet_combo.addItem(_lbl, _b["id"])
        self.ref_bullet_combo.currentIndexChanged.connect(self._on_ref_bullet_selected)
        _exist_bid = ref_data.get("bullet_id")
        _exist_bname = str(ref_data.get("bullet_type", "") or "")
        if _exist_bid is not None:
            _idx = self.ref_bullet_combo.findData(_exist_bid)
            self.ref_bullet_combo.setCurrentIndex(_idx if _idx >= 0 else 0)
        elif _exist_bname:
            self.ref_bullet_combo.setCurrentText(_exist_bname)
        ref_form.addRow(tr("barrel_editor_ref_bullet_label"), self.ref_bullet_combo)

        self.ref_bullet_weight_edit = QLineEdit(
            str(ref_data.get("bullet_weight_gr", ""))
        )
        self.ref_bullet_weight_edit.setPlaceholderText(
            tr("barrel_editor_ref_bullet_weight_placeholder")
        )
        ref_form.addRow(
            tr("barrel_editor_ref_bullet_weight_label"), self.ref_bullet_weight_edit
        )

        self.ref_coal_edit = QLineEdit(str(ref_data.get("coal_mm", "")))
        self.ref_coal_edit.setPlaceholderText(tr("barrel_editor_ref_coal_placeholder"))
        ref_form.addRow(tr("barrel_editor_ref_coal_label"), self.ref_coal_edit)

        ref_img_row = QHBoxLayout()
        self._ref_image_path: str = str(ref_data.get("group_image_path", "") or "")
        self.ref_img_label = QLabel(
            self._ref_image_path
            if self._ref_image_path
            else tr("barrel_editor_ref_no_image")
        )
        self.ref_img_label.setStyleSheet("color: #b0b6be;")
        ref_img_browse = QPushButton(tr("barrel_editor_ref_browse_image"))
        ref_img_browse.clicked.connect(self._on_browse_ref_image)
        ref_img_row.addWidget(self.ref_img_label, 1)
        ref_img_row.addWidget(ref_img_browse)
        ref_form.addRow(tr("barrel_editor_ref_group_image_label"), ref_img_row)

        self.ref_notes_edit = QTextEdit()
        self.ref_notes_edit.setPlainText(str(ref_data.get("notes", "") or ""))
        self.ref_notes_edit.setMaximumHeight(70)
        self.ref_notes_edit.setPlaceholderText(
            tr("barrel_editor_ref_notes_placeholder")
        )
        ref_form.addRow(tr("barrel_editor_ref_notes_label"), self.ref_notes_edit)
        ref_layout.addWidget(ref_group)

        # OD diameter profile
        diam_group = QGroupBox(tr("barrel_editor_diam_group"))
        diam_layout_v = QVBoxLayout(diam_group)

        diam_info = QLabel(tr("barrel_editor_diam_info"))
        diam_info.setWordWrap(True)
        diam_info.setStyleSheet("color: #b0b6be; font-style: italic;")
        diam_layout_v.addWidget(diam_info)

        self.diam_table = QTableWidget(0, 2)
        self.diam_table.setHorizontalHeaderLabels(
            [tr("barrel_editor_diam_col_pos"), tr("barrel_editor_diam_col_od")]
        )
        _dh = self.diam_table.horizontalHeader()
        if _dh:
            _dh.setStretchLastSection(True)
        self.diam_table.setMaximumHeight(200)
        for pt in self._barrel.get("measurement_points", []) or []:
            if isinstance(pt, dict):
                _r = self.diam_table.rowCount()
                self.diam_table.insertRow(_r)
                self.diam_table.setItem(
                    _r, 0, QTableWidgetItem(str(pt.get("position_mm", "")))
                )
                self.diam_table.setItem(
                    _r, 1, QTableWidgetItem(str(pt.get("od_mm", "")))
                )
        diam_layout_v.addWidget(self.diam_table)

        diam_btn_row = QHBoxLayout()
        _add_diam = QPushButton(tr("barrel_editor_diam_add"))
        _add_diam.clicked.connect(self._on_add_diam_row)
        _rem_diam = QPushButton(tr("barrel_editor_diam_remove"))
        _rem_diam.clicked.connect(self._on_remove_diam_row)
        diam_btn_row.addWidget(_add_diam)
        diam_btn_row.addWidget(_rem_diam)
        diam_btn_row.addStretch()
        diam_layout_v.addLayout(diam_btn_row)
        ref_layout.addWidget(diam_group)
        ref_layout.addStretch()

        # ── Bottom action bar ────────────────────────────────────────────────
        btn_bar = QWidget(self)
        btn_bar.setStyleSheet("background: #2c313a; border-top: 1px solid #3c4250;")
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(16, 8, 16, 8)
        btn_layout.setSpacing(8)

        self.load_library_btn = QPushButton(tr("barrel_editor_load_from_library"))
        self.load_library_btn.clicked.connect(self._on_load_from_library)
        btn_layout.addWidget(self.load_library_btn)

        self.apply_profile_btn = QPushButton(tr("barrel_editor_apply_profile"))
        self.apply_profile_btn.clicked.connect(self.apply_profile_preset)
        btn_layout.addWidget(self.apply_profile_btn)

        self.apply_attachment_btn = QPushButton(tr("barrel_editor_apply_attachment"))
        self.apply_attachment_btn.clicked.connect(self.apply_attachment_preset)
        btn_layout.addWidget(self.apply_attachment_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton(tr("btn_ok"))
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton(tr("btn_cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        root.addWidget(btn_bar)

        self.update_profile_preview()
        self.update_attachment_preview()
        self.calculate_h2o_average()
        self._recalc_brass_stats()

    # ── Brass table helpers ──────────────────────────────────────────────────

    def _load_brass_table(self, case_data: dict) -> None:
        """Populate brass_table from barrel case_measurements data."""
        sessions = case_data.get("brass_sessions", []) or []
        if sessions:
            for s in sessions:
                self._append_brass_row(
                    date=str(s.get("date", "")),
                    firings=str(s.get("firings", "")),
                    trim=str(s.get("trim_mm", "")),
                    neck=str(s.get("neck_od_mm", "")),
                    shoulder=str(s.get("shoulder_mm", "")),
                    headspace=str(s.get("headspace_mm", "")),
                    velocity=str(s.get("velocity_ms", "")),
                    notes=str(s.get("notes", "")),
                )
            return
        # Legacy: zip separate sample arrays
        trim_vals = case_data.get("trim_length_samples") or []
        neck_vals = case_data.get("neck_diameter_samples") or []
        shoulder_vals = case_data.get("shoulder_bump_samples") or []
        datum_vals = case_data.get("base_to_datum_samples") or []
        max_len = max(
            len(trim_vals), len(neck_vals), len(shoulder_vals), len(datum_vals), 0
        )

        def _g(lst, i):
            return str(lst[i]) if i < len(lst) else ""

        for i in range(max_len):
            self._append_brass_row(
                trim=_g(trim_vals, i),
                neck=_g(neck_vals, i),
                shoulder=_g(shoulder_vals, i),
                headspace=_g(datum_vals, i),
            )

    def _append_brass_row(
        self,
        date: str = "",
        firings: str = "",
        trim: str = "",
        neck: str = "",
        shoulder: str = "",
        headspace: str = "",
        velocity: str = "",
        notes: str = "",
    ) -> None:
        self.brass_table.blockSignals(True)
        row = self.brass_table.rowCount()
        self.brass_table.insertRow(row)
        for col, val in enumerate(
            [date, firings, trim, neck, shoulder, headspace, velocity, notes]
        ):
            text = str(val) if val not in (None, "None") else ""
            self.brass_table.setItem(row, col, QTableWidgetItem(text))
        self.brass_table.blockSignals(False)

    def _on_add_brass_row(self) -> None:
        today = _date.today().strftime("%Y-%m-%d")
        self._append_brass_row(date=today)

    def _on_remove_brass_row(self) -> None:
        row = self.brass_table.currentRow()
        if row >= 0:
            self.brass_table.removeRow(row)
        self._recalc_brass_stats()

    def _on_brass_table_changed(self) -> None:
        self._recalc_brass_stats()

    def _brass_col_values(self, col_idx: int) -> list[float]:
        vals: list[float] = []
        for r in range(self.brass_table.rowCount()):
            item = self.brass_table.item(r, col_idx)
            if item:
                try:
                    vals.append(float(item.text().replace(",", ".")))
                except ValueError:
                    pass
        return vals

    def _recalc_brass_stats(self) -> None:
        """Recalculate averages from the brass table and update SAAMI comparison."""
        lines: list[str] = []
        col_defs = [
            (2, "Trim-lengde"),
            (3, "Hals OD"),
            (4, "Skulder"),
            (5, "Headspace / datum"),
            (6, "Hastighet"),
        ]
        for col_idx, label in col_defs:
            vals = self._brass_col_values(col_idx)
            if vals:
                avg = sum(vals) / len(vals)
                mn, mx = min(vals), max(vals)
                spread = mx - mn
                lines.append(
                    f"<b>{label}:</b> snitt {avg:.3f} mm &nbsp;|&nbsp; "
                    f"spredning {spread:.3f} mm &nbsp;({mn:.3f}–{mx:.3f}) &nbsp;|&nbsp; "
                    f"n={len(vals)}"
                )
        if lines:
            self.brass_stats_label.setText("<br>".join(lines))
            self.brass_stats_label.setVisible(True)
        else:
            self.brass_stats_label.setVisible(False)
        self._update_saami_comparison()

    # ------------------------------------------------------------------
    # H2O table helpers
    # ------------------------------------------------------------------

    def _load_h2o_table(self, case_data: dict) -> None:
        """Populate the H2O table from saved case_measurements."""
        self.h2o_table.blockSignals(True)
        self.h2o_table.setRowCount(0)
        existing = case_data.get("h2o_measurements", []) or []
        for sample in existing:
            if not isinstance(sample, dict):
                continue
            dry = sample.get("dry_weight_gr")
            wet = sample.get("wet_weight_gr")
            if dry is None or wet is None:
                continue
            self._h2o_append_row(self.h2o_table.rowCount() + 1, dry, wet)
        self.h2o_table.blockSignals(False)
        self._recalc_h2o_stats()

    def _h2o_append_row(
        self,
        nr: int,
        dry: float | None = None,
        wet: float | None = None,
    ) -> None:
        row = self.h2o_table.rowCount()
        self.h2o_table.insertRow(row)

        nr_item = QTableWidgetItem(str(nr))
        nr_item.setFlags(nr_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.h2o_table.setItem(row, 0, nr_item)

        self.h2o_table.setItem(
            row, 1, QTableWidgetItem(f"{dry:.3f}" if dry is not None else "")
        )
        self.h2o_table.setItem(
            row, 2, QTableWidgetItem(f"{wet:.3f}" if wet is not None else "")
        )

        h2o_val = (wet - dry) if (dry is not None and wet is not None) else None
        h2o_item = QTableWidgetItem(f"{h2o_val:.3f}" if h2o_val is not None else "")
        h2o_item.setFlags(h2o_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.h2o_table.setItem(row, 3, h2o_item)

    def _on_add_h2o_row(self) -> None:
        nr = self.h2o_table.rowCount() + 1
        self._h2o_append_row(nr)
        self.h2o_table.scrollToBottom()
        self.h2o_table.setCurrentCell(self.h2o_table.rowCount() - 1, 1)

    def _on_remove_h2o_row(self) -> None:
        rows = sorted(
            {idx.row() for idx in self.h2o_table.selectedIndexes()},
            reverse=True,
        )
        if not rows:
            cur = self.h2o_table.currentRow()
            if cur >= 0:
                rows = [cur]
        for r in rows:
            self.h2o_table.removeRow(r)
        self._h2o_renumber()
        self._recalc_h2o_stats()

    def _on_fill_h2o_rows(self, count: int) -> None:
        start_nr = self.h2o_table.rowCount() + 1
        for i in range(count):
            self._h2o_append_row(start_nr + i)
        self.h2o_table.scrollToBottom()
        self.h2o_table.setCurrentCell(self.h2o_table.rowCount() - 1, 1)

    def _h2o_renumber(self) -> None:
        self.h2o_table.blockSignals(True)
        for r in range(self.h2o_table.rowCount()):
            item = self.h2o_table.item(r, 0)
            if item:
                item.setText(str(r + 1))
            else:
                nr_item = QTableWidgetItem(str(r + 1))
                nr_item.setFlags(nr_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.h2o_table.setItem(r, 0, nr_item)
        self.h2o_table.blockSignals(False)

    def _on_h2o_table_changed(self, changed_item: Any) -> None:
        col = changed_item.column()
        row = changed_item.row()
        if col not in (1, 2):
            return
        dry_item = self.h2o_table.item(row, 1)
        wet_item = self.h2o_table.item(row, 2)
        dry_text = dry_item.text().strip() if dry_item else ""
        wet_text = wet_item.text().strip() if wet_item else ""
        self.h2o_table.blockSignals(True)
        try:
            dry = float(dry_text) if dry_text else None
            wet = float(wet_text) if wet_text else None
            h2o_val = (
                round(wet - dry, 4)
                if (dry is not None and wet is not None and wet >= dry)
                else None
            )
            h2o_item = self.h2o_table.item(row, 3)
            if not h2o_item:
                h2o_item = QTableWidgetItem()
                h2o_item.setFlags(h2o_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.h2o_table.setItem(row, 3, h2o_item)
            h2o_item.setText(f"{h2o_val:.3f}" if h2o_val is not None else "")
        except (ValueError, TypeError):
            h2o_item = self.h2o_table.item(row, 3)
            if h2o_item:
                h2o_item.setText("")
        finally:
            self.h2o_table.blockSignals(False)
        self._recalc_h2o_stats()

    def _recalc_h2o_stats(self) -> None:
        """Recompute average, spread and stats label from H₂O column."""
        capacities: list[float] = []
        for r in range(self.h2o_table.rowCount()):
            item = self.h2o_table.item(r, 3)
            if item and item.text().strip():
                try:
                    capacities.append(float(item.text()))
                except ValueError:
                    pass
        if not capacities:
            self.h2o_capacity_edit.clear()
            self.h2o_stats_label.setText("Ingen målinger ennå")
            return
        average = sum(capacities) / len(capacities)
        minimum = min(capacities)
        maximum = max(capacities)
        spread = maximum - minimum
        if spread <= 0.30:
            quality = "god konsistens"
        elif spread <= 0.75:
            quality = "akseptabel spredning"
        else:
            quality = "høy spredning — sjekk hylsekvalitet"
        self.h2o_capacity_edit.setText(f"{average:.3f}")
        self.h2o_stats_label.setText(
            f"n={len(capacities)}  |  snitt {average:.3f} gr  |  "
            f"spredning {spread:.3f} gr  (min {minimum:.3f} – maks {maximum:.3f})  |  {quality}"
        )

    def _parse_h2o_samples(self) -> list[dict[str, float]]:
        """Collect H2O measurement rows from the table as dicts."""
        samples: list[dict[str, float]] = []
        for r in range(self.h2o_table.rowCount()):
            dry_item = self.h2o_table.item(r, 1)
            wet_item = self.h2o_table.item(r, 2)
            dry_text = dry_item.text().strip() if dry_item else ""
            wet_text = wet_item.text().strip() if wet_item else ""
            if not dry_text and not wet_text:
                continue  # skip completely empty rows
            if not dry_text or not wet_text:
                raise ValueError(
                    f"Rad {r + 1}: begge verdier (Tørr og Våt) må fylles ut, eller la raden stå tom."
                )
            try:
                dry = float(dry_text)
                wet = float(wet_text)
            except ValueError:
                raise ValueError(
                    f"Rad {r + 1}: ugyldig tallverdi — bruk punktum som desimalskilletegn."
                )
            if wet < dry:
                raise ValueError(
                    f"Rad {r + 1}: Våt vekt ({wet:.3f} gr) kan ikke være lavere enn Tørr vekt ({dry:.3f} gr)."
                )
            samples.append(
                {
                    "dry_weight_gr": dry,
                    "wet_weight_gr": wet,
                    "h2o_capacity_grains": round(wet - dry, 4),
                }
            )
        return samples

    def calculate_h2o_average(self) -> None:
        """Kept for backwards-compatibility; delegates to _recalc_h2o_stats."""
        self._recalc_h2o_stats()

    def update_profile_preview(self) -> None:
        profile_id = self.profile_combo.currentData()
        meta = BARREL_PROFILE_PRESETS.get(profile_id, BARREL_PROFILE_PRESETS["custom"])
        label = tr(str(meta["label_key"]))
        description = tr(str(meta["description_key"]))
        self.profile_preview.setText(
            f"<b>{label}</b><br><pre>{meta['silhouette']}</pre>{description}"
        )

    def update_attachment_preview(self) -> None:
        attachment_id = self.attachment_combo.currentData()
        meta = BARREL_ATTACHMENT_PRESETS.get(
            attachment_id, BARREL_ATTACHMENT_PRESETS["unknown"]
        )
        label = tr(str(meta["label_key"]))
        description = tr(str(meta["description_key"]))
        self.attachment_preview.setText(
            f"<b>{label}</b><br><pre>{meta['silhouette']}</pre>{description}"
        )

    def apply_profile_preset(self) -> None:
        profile_id = self.profile_combo.currentData()
        meta = BARREL_PROFILE_PRESETS.get(profile_id)
        if not meta:
            return

        defaults = meta.get("defaults", {})
        usage_type = defaults.get("usage_type")

        if usage_type:
            _idx = self.usage_type_edit.findData(usage_type)
            self.usage_type_edit.setCurrentIndex(_idx if _idx >= 0 else 0)

        if profile_id == "pistol_match":
            idx = self.muzzle_type_combo.findData("compensator")
            if idx >= 0:
                self.muzzle_type_combo.setCurrentIndex(idx)

        if profile_id == "bull" and not self.status_edit.text().strip():
            self.status_edit.setText("active")

    def apply_attachment_preset(self) -> None:
        attachment_id = self.attachment_combo.currentData()
        meta = BARREL_ATTACHMENT_PRESETS.get(attachment_id)
        if not meta:
            return

        defaults = meta.get("defaults", {})
        mount_type = defaults.get("mount_type")
        action_stiffness = defaults.get("action_stiffness")

        if mount_type:
            _idx = self.mount_edit.findData(mount_type)
            self.mount_edit.setCurrentIndex(_idx if _idx >= 0 else 0)
        if action_stiffness:
            _idx = self.action_stiffness_edit.findData(action_stiffness)
            self.action_stiffness_edit.setCurrentIndex(_idx if _idx >= 0 else 0)

        if (
            attachment_id == "quick_change"
            and not self.repeatability_edit.text().strip()
        ):
            self.repeatability_edit.setText("needs verification after barrel swap")
        elif attachment_id == "threaded" and not self.repeatability_edit.text().strip():
            self.repeatability_edit.setText("stable")

    def _parse_dim_samples(self, text: str) -> list[float]:
        values: list[float] = []
        for line in text.strip().splitlines():
            line = line.strip().replace(",", ".")
            if not line:
                continue
            try:
                values.append(float(line))
            except ValueError:
                continue
        return values

    def _dim_stats_text(self, values: list[float]) -> str:
        if not values:
            return tr("case_no_measurements")
        n = len(values)
        avg = sum(values) / n
        mn = min(values)
        mx = max(values)
        spread = mx - mn
        sd = (sum((v - avg) ** 2 for v in values) / n) ** 0.5 if n > 1 else 0.0
        return tr(
            "case_stats_result",
            count=n,
            avg=f"{avg:.3f}",
            mn=f"{mn:.3f}",
            mx=f"{mx:.3f}",
            spread=f"{spread:.3f}",
            sd=f"{sd:.3f}",
        )

    def calculate_dim_averages(self) -> None:
        self._recalc_brass_stats()

    def _on_caliber_changed(self, _text: str = "") -> None:
        self._update_saami_comparison()

    def _update_saami_comparison(self) -> None:
        """Look up SAAMI data for the current caliber and show deltas vs brass table."""
        caliber = self.caliber_edit.currentText().strip()
        if not caliber:
            self.saami_label.setVisible(False)
            return
        try:
            db = self._db or get_database()
            std = saami_lookup(caliber, db)
        except Exception:
            std = None
        if not std:
            self.saami_label.setVisible(False)
            return

        lines: list[str] = [f"<b>SAAMI / CIP — {std['caliber_name']}</b>"]

        def _delta_line(label: str, col_idx: int, field_key: str) -> str:
            saami_v = std.get(field_key)
            if saami_v is None:
                return ""
            vals = self._brass_col_values(col_idx)
            if vals:
                avg = sum(vals) / len(vals)
                delta = avg - saami_v
                sign = "+" if delta >= 0 else ""
                color = (
                    "#27ae60"
                    if abs(delta) < 0.10
                    else "#e67e22" if abs(delta) < 0.30 else "#e74c3c"
                )
                return (
                    f"{label}: <b>{avg:.3f}</b> | SAAMI: {saami_v:.2f} "
                    f"| <span style='color:{color}'>{sign}{delta:.3f} mm</span>"
                )
            else:
                return f"{label}: — | SAAMI: {saami_v:.2f} mm"

        for line in [
            _delta_line("Trim-lengde", 2, "case_length_mm"),
            _delta_line("Hals-Ø (OD)", 3, "neck_diameter_mm"),
            _delta_line("Headspace (datum)", 5, "headspace_go_mm"),
        ]:
            if line:
                lines.append(line)

        pressure = std.get("max_pressure_bar")
        if pressure:
            lines.append(f"Maks trykk: {pressure} bar")

        html = "<br>".join(lines)
        self.saami_label.setText(html)
        self.saami_label.setVisible(True)
        # Mirror to Skutt messing-fane
        if hasattr(self, "brass_saami_label"):
            self.brass_saami_label.setText(html)
            self.brass_saami_label.setVisible(True)

    def _on_add_diam_row(self) -> None:
        row = self.diam_table.rowCount()
        self.diam_table.insertRow(row)
        self.diam_table.setItem(row, 0, QTableWidgetItem(""))
        self.diam_table.setItem(row, 1, QTableWidgetItem(""))

    def _on_remove_diam_row(self) -> None:
        row = self.diam_table.currentRow()
        if row >= 0:
            self.diam_table.removeRow(row)

    def _on_ref_bullet_selected(self, idx: int) -> None:
        bullet_id = self.ref_bullet_combo.itemData(idx)
        if bullet_id is None:
            return
        for _b in self._ref_bullet_db:
            if _b["id"] == bullet_id:
                wt = _b.get("weight_grains")
                if wt is not None:
                    self.ref_bullet_weight_edit.setText(str(float(wt)))
                break

    def _on_browse_ref_image(self) -> None:
        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Velg gruppe-bilde", "", "Bilder (*.png *.jpg *.jpeg *.bmp *.tif)"
            )
            if path:
                self._ref_image_path = path
                import os

                self.ref_img_label.setText(os.path.basename(path))
        except Exception:
            pass

    def _on_load_from_library(self) -> None:
        try:
            db = self._db or get_database()
            rows = db.execute_query(
                "SELECT * FROM barrel_profiles ORDER BY category, name"
            )
        except Exception:
            rows = []
        if not rows:
            QMessageBox.information(
                self, tr("barrel_library_title"), tr("barrel_library_empty")
            )
            return
        dlg = _BarrelLibraryPickerDialog(rows, parent=self)
        if dlg.exec():
            selected = dlg.selected_profile
            if selected:
                self._apply_library_profile(selected)

    def _apply_library_profile(self, profile: Dict[str, Any]) -> None:
        stiffness = str(profile.get("stiffness_rating") or "").lower()
        stiffness_to_preset = {
            "very-light": "sporter",
            "light": "sporter",
            "medium": "medium",
            "heavy": "heavy",
            "very-heavy": "bull",
            "bull": "bull",
        }
        preset_id = stiffness_to_preset.get(stiffness, "custom")
        idx = self.profile_combo.findData(preset_id)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        recommended = str(profile.get("recommended_for") or "").strip()
        if recommended:
            _rec = recommended.split(",")[0].strip()
            _idx = self.usage_type_edit.findData(_rec)
            self.usage_type_edit.setCurrentIndex(_idx if _idx >= 0 else 0)
        typical_length = profile.get("typical_length_inches")
        if (
            isinstance(typical_length, (int, float))
            and not self.length_edit.text().strip()
        ):
            self.length_edit.setText(str(round(typical_length * 25.4)))
        self.update_profile_preview()

    def gather(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        data["id"] = self._barrel.get("id", "")
        data["barrel_profile_id"] = self.profile_combo.currentData() or "custom"
        data["barrel_attachment_type"] = (
            self.attachment_combo.currentData() or "unknown"
        )
        data["name"] = self.name_edit.text().strip()
        data["caliber"] = self.caliber_edit.currentText().strip()
        data["usage_type"] = self.usage_type_edit.currentData() or "general"
        data["status"] = self.status_edit.currentData() or "active"
        try:
            data["length_mm"] = (
                float(self.length_edit.text())
                if self.length_edit.text().strip()
                else None
            )
        except ValueError:
            data["length_mm"] = None
        data["twist"] = self.twist_edit.text().strip()
        _preset_id = data.get("barrel_profile_id") or "custom"
        data["barrel_profile"] = (
            BARREL_PROFILE_PRESETS.get(_preset_id, {})
            .get("defaults", {})
            .get("barrel_profile")
            or _preset_id
        )
        data["material"] = self.material_edit.currentText().strip()
        data["mount_type"] = self.mount_edit.currentData() or ""
        data["action_stiffness"] = self.action_stiffness_edit.currentData() or ""
        data["barrel_return_to_zero"] = self.repeatability_edit.text().strip()
        try:
            data["barrel_torque_nm"] = (
                float(self.torque_edit.text())
                if self.torque_edit.text().strip()
                else None
            )
        except ValueError:
            data["barrel_torque_nm"] = None
        # muzzle device
        try:
            data["muzzle_device_weight_g"] = (
                float(self.muzzle_weight_edit.text())
                if self.muzzle_weight_edit.text().strip()
                else None
            )
        except ValueError:
            data["muzzle_device_weight_g"] = None
        try:
            data["muzzle_device_length_mm"] = (
                float(self.muzzle_length_edit.text())
                if self.muzzle_length_edit.text().strip()
                else None
            )
        except ValueError:
            data["muzzle_device_length_mm"] = None
        data["muzzle_device_type"] = self.muzzle_type_combo.currentData() or "none"
        data["muzzle_mount_type"] = self.muzzle_mount_combo.currentData() or "direct"
        data["muzzle_device_model"] = self.muzzle_model_edit.text().strip()
        data["muzzle_thread_pitch"] = self.muzzle_thread_edit.currentText().strip()
        try:
            data["muzzle_protrusion_mm"] = (
                float(self.muzzle_protrusion_edit.text())
                if self.muzzle_protrusion_edit.text().strip()
                else None
            )
        except ValueError:
            data["muzzle_protrusion_mm"] = None
        case_measurements: Dict[str, Any] = {}
        try:
            case_measurements["h2o_capacity_grains"] = (
                float(self.h2o_capacity_edit.text())
                if self.h2o_capacity_edit.text().strip()
                else None
            )
        except ValueError:
            case_measurements["h2o_capacity_grains"] = None

        def _avg_or_none(values: list[float]):
            return round(sum(values) / len(values), 4) if values else None

        def _cell_text(r: int, c: int) -> str:
            item = self.brass_table.item(r, c)
            return item.text().strip() if item else ""

        # New sessions format
        sessions: list[dict] = []
        for r in range(self.brass_table.rowCount()):
            sessions.append(
                {
                    "date": _cell_text(r, 0),
                    "firings": _cell_text(r, 1),
                    "trim_mm": _cell_text(r, 2),
                    "neck_od_mm": _cell_text(r, 3),
                    "shoulder_mm": _cell_text(r, 4),
                    "headspace_mm": _cell_text(r, 5),
                    "velocity_ms": _cell_text(r, 6),
                    "notes": _cell_text(r, 7),
                }
            )
        case_measurements["brass_sessions"] = sessions

        # Legacy arrays for backwards compatibility
        trim_vals = self._brass_col_values(2)
        case_measurements["trim_length_samples"] = trim_vals
        case_measurements["trim_length_mm"] = _avg_or_none(trim_vals)

        neck_vals = self._brass_col_values(3)
        case_measurements["neck_diameter_samples"] = neck_vals
        case_measurements["neck_diameter_mm"] = _avg_or_none(neck_vals)

        shoulder_vals = self._brass_col_values(4)
        case_measurements["shoulder_bump_samples"] = shoulder_vals
        case_measurements["shoulder_bump_mm"] = _avg_or_none(shoulder_vals)

        datum_vals = self._brass_col_values(5)
        case_measurements["base_to_datum_samples"] = datum_vals
        case_measurements["base_to_datum_mm"] = _avg_or_none(datum_vals)

        case_measurements["notes"] = self.case_notes_edit.toPlainText().strip()
        data["case_measurements"] = case_measurements

        # Diameter-profil (structured table)
        mp: list[dict] = []
        for row in range(self.diam_table.rowCount()):
            pos_item = self.diam_table.item(row, 0)
            od_item = self.diam_table.item(row, 1)
            try:
                pos_mm = float((pos_item.text() if pos_item else "").replace(",", "."))
                od_mm = float((od_item.text() if od_item else "").replace(",", "."))
                mp.append({"position_mm": pos_mm, "od_mm": od_mm})
            except ValueError:
                pass
        data["measurement_points"] = mp

        # Referanseladning
        def _float_or_none(s: str):
            try:
                return float(s.strip().replace(",", ".")) if s.strip() else None
            except ValueError:
                return None

        data["reference_load"] = {
            "primer": self.ref_primer_combo.currentText().strip(),
            "primer_id": self.ref_primer_combo.currentData(),
            "powder_id": self.ref_powder_combo.currentData(),
            "powder_type": self.ref_powder_combo.currentText().strip(),
            "powder_charge_gr": _float_or_none(self.ref_charge_edit.text()),
            "bullet_id": self.ref_bullet_combo.currentData(),
            "bullet_type": self.ref_bullet_combo.currentText().strip(),
            "bullet_weight_gr": _float_or_none(self.ref_bullet_weight_edit.text()),
            "coal_mm": _float_or_none(self.ref_coal_edit.text()),
            "group_image_path": self._ref_image_path,
            "notes": self.ref_notes_edit.toPlainText().strip(),
        }

        try:
            data["case_measurements"]["h2o_measurements"] = self._parse_h2o_samples()
        except ValueError as exc:
            QMessageBox.warning(self, tr("barrel_editor_invalid_h2o_title"), str(exc))
            data["case_measurements"]["h2o_measurements"] = []
        return data


class _BarrelLibraryPickerDialog(QDialog):
    """Dialog that shows predefined barrel profiles from the database."""

    def __init__(self, profiles: list, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("barrel_library_title"))
        self.resize(820, 480)
        try:
            from src.ui.theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            pass
        self.selected_profile: Optional[Dict[str, Any]] = None
        self._profiles = profiles
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._table = QTableWidget()
        cols = [
            ("barrel_library_col_name", "name"),
            ("barrel_library_col_category", "category"),
            ("barrel_library_col_stiffness", "stiffness_rating"),
            ("barrel_library_col_muzzle_mm", "muzzle_diameter_mm"),
            ("barrel_library_col_breech_mm", "breech_diameter_mm"),
            ("barrel_library_col_weight_g", "typical_total_weight_grams"),
            ("barrel_library_col_calibers", "typical_calibers"),
        ]
        self._col_keys = [c[1] for c in cols]
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels([tr(c[0]) for c in cols])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self._table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            header.setStretchLastSection(True)

        for row_data in self._profiles:
            r = self._table.rowCount()
            self._table.insertRow(r)
            for c, key in enumerate(self._col_keys):
                val = row_data.get(key)
                text = f"{val:.1f}" if isinstance(val, float) else str(val or "")
                self._table.setItem(r, c, QTableWidgetItem(text))

        self._table.selectionModel().selectionChanged.connect(self._on_selection)
        self._table.doubleClicked.connect(self._on_apply)
        layout.addWidget(self._table, stretch=2)

        self._detail = QLabel()
        self._detail.setWordWrap(True)
        if Qt is not None:
            self._detail.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._detail.setStyleSheet(
            "padding: 10px; border: 1px solid #d0d7de; border-radius: 6px;"
        )
        self._detail.setMinimumHeight(80)
        layout.addWidget(self._detail, stretch=1)

        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton(tr("barrel_library_apply"))
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._on_apply)
        cancel_btn = QPushButton(tr("close"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _on_selection(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            self._detail.setText("")
            self.apply_btn.setEnabled(False)
            return
        r = rows[0].row()
        profile = self._profiles[r]
        desc = str(profile.get("description") or "")
        harmonics = str(profile.get("harmonic_characteristics") or "")
        length = profile.get("typical_length_inches")
        length_str = (
            tr("barrel_library_typical_length", value=f"{length:.0f}")
            if isinstance(length, (int, float))
            else ""
        )
        parts = [
            tr("barrel_library_description", value=desc) if desc else "",
            tr("barrel_library_harmonics", value=harmonics) if harmonics else "",
            length_str,
        ]
        self._detail.setText("\n\n".join(p for p in parts if p))
        self.apply_btn.setEnabled(True)

    def _on_apply(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        self.selected_profile = self._profiles[rows[0].row()]
        self.accept()
