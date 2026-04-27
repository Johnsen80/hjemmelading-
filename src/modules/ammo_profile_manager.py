"""
Ammo Profile Manager
Handles creation and administration of ammo profiles.
"""

import importlib
import json

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.drag_models import parse_bc_segments
from ..utils.i18n import tr
from ..utils.unit_preferences import (
    format_velocity_fps,
    format_weight_grains,
    get_velocity_suffix,
    get_weight_suffix,
    velocity_display_to_fps,
    velocity_fps_to_display_value,
    weight_display_to_grains,
    weight_grains_to_display_value,
)
from .load_data_service import (
    build_load_card_summary,
    build_profile_evidence_summary,
    build_profile_health_summary,
    build_profile_trust_map,
)


def _status_pill(label: str, level: str | None) -> str:
    palette = {
        "critical": ("#fee2e2", "#991b1b"),
        "warning": ("#fef3c7", "#92400e"),
        "ok": ("#dcfce7", "#166534"),
        "info": ("#dbeafe", "#1d4ed8"),
        "unknown": ("#f3f4f6", "#374151"),
        "neutral": ("#f3f4f6", "#374151"),
    }
    bg, fg = palette.get(
        str(level or "unknown").strip().lower(), ("#f3f4f6", "#374151")
    )
    return (
        f"<span style='display:inline-block; margin:0 6px 4px 0; padding:2px 8px; "
        f"border-radius:999px; background:{bg}; color:{fg}; font-size:8pt; font-weight:700;'>{label}</span>"
    )


def _load_ammo_test_dialog():
    module = importlib.import_module("src.ammo_test")
    return getattr(module, "AmmoTestReportDialog")


def _derive_ammo_type(profile: dict, db) -> str:
    rifle_id = profile.get("rifle_id")
    if rifle_id:
        rifle = db.get_by_id("rifles", rifle_id)
        if rifle:
            caliber = str(rifle.get("caliber") or "").strip().lower().replace(" ", "")
            if caliber in {
                "22lr",
                ".22lr",
                ".22l.r.",
                ".22longrifle",
                "17hmr",
                ".17hmr",
            }:
                return "rimfire"
            if str(rifle.get("weapon_type") or "rifle").strip().lower() == "pistol":
                return "centerfire_pistol"
    caliber = str(profile.get("caliber") or "").strip().lower().replace(" ", "")
    if caliber in {"22lr", ".22lr", ".22l.r.", ".22longrifle", "17hmr", ".17hmr"}:
        return "rimfire"
    return "centerfire_rifle"


def _format_bc_summary(
    bc_g1: float | None,
    bc_g7: float | None,
    bc_segments_json: str | None = None,
) -> str:
    segments = parse_bc_segments(bc_segments_json)
    if segments:
        return _format_bc_segments_summary(bc_segments_json)
    if bc_g7 and bc_g1:
        return tr(
            "ammo_profiles_bc_summary_both",
            g7=f"{float(bc_g7):.3f}",
            g1=f"{float(bc_g1):.3f}",
        )
    if bc_g7:
        return tr("ammo_profiles_bc_summary_g7_only", g7=f"{float(bc_g7):.3f}")
    if bc_g1:
        return tr("ammo_profiles_bc_summary_g1_only", g1=f"{float(bc_g1):.3f}")
    return tr("ammo_profiles_bc_summary_missing")


def _normalize_bc_segments_json(raw_text: str) -> str | None:
    text = str(raw_text or "").strip()
    if not text:
        return None
    parsed = parse_bc_segments(text)
    if not parsed:
        return None
    return json.dumps(parsed, ensure_ascii=False)


def _format_bc_segments_summary(raw_value: str | None) -> str:
    segments = parse_bc_segments(raw_value)
    if not segments:
        return tr("ammo_profiles_bc_segments_missing")
    parts: list[str] = []
    for segment in segments[:3]:
        model = str(segment.get("model") or "AUTO")
        min_v = segment.get("velocity_fps_min")
        max_v = segment.get("velocity_fps_max")
        bc_value = segment.get("bc_g7") or segment.get("bc_g1") or segment.get("bc")
        if bc_value is None:
            continue
        if max_v is not None:
            parts.append(
                f"{model} {float(bc_value):.3f} @ {float(min_v or 0):.0f}-{float(max_v):.0f} fps"
            )
        else:
            parts.append(
                f"{model} {float(bc_value):.3f} @ {float(min_v or 0):.0f}+ fps"
            )
    if not parts:
        return tr("ammo_profiles_bc_segments_missing")
    summary = "; ".join(parts)
    if len(segments) > 3:
        summary += tr("ammo_profiles_bc_segments_more", count=str(len(segments) - 3))
    return summary


class AmmoProfileManager(QWidget):
    """Widget for ammo profile management."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel(tr("ammo_profiles_title"))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(tr("ammo_profiles_subtitle"))
        layout.addWidget(desc)

        # Knapper
        btn_layout = QHBoxLayout()
        add_btn = QPushButton(tr("ammo_profiles_new"))
        add_btn.setMinimumHeight(40)
        add_btn.clicked.connect(self.add_profile)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton(tr("ammo_profiles_edit"))
        edit_btn.setMinimumHeight(40)
        edit_btn.clicked.connect(self.edit_profile)
        btn_layout.addWidget(edit_btn)

        copy_btn = QPushButton(tr("ammo_profiles_copy"))
        copy_btn.setMinimumHeight(40)
        copy_btn.clicked.connect(self.copy_profile)
        btn_layout.addWidget(copy_btn)

        test_btn = QPushButton(tr("ammo_profiles_open_lot_tests"))
        test_btn.setMinimumHeight(40)
        test_btn.clicked.connect(self.open_lot_tests)
        btn_layout.addWidget(test_btn)

        delete_btn = QPushButton(tr("ammo_profiles_delete"))
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_profile)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                tr("ammo_profiles_col_name"),
                "Firearm",
                tr("ammo_profiles_col_caliber"),
                tr("ammo_profiles_col_bullet"),
                tr("ammo_profiles_col_powder"),
                tr("ammo_profiles_col_charge"),
                tr("ammo_profiles_col_velocity"),
                tr("ammo_profiles_col_bc"),
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self.edit_profile)
        self.table.itemSelectionChanged.connect(self.refresh_profile_evidence_panel)
        layout.addWidget(self.table)

        evidence_group = QGroupBox("Load Evidence")
        evidence_layout = QVBoxLayout()
        self.load_card_label = QLabel("Select a load to view the load card.")
        self.load_card_label.setWordWrap(True)
        evidence_layout.addWidget(self.load_card_label)
        self.profile_evidence_label = QLabel(
            "Select a load to view chrono, groups, pressure, and reference data."
        )
        self.profile_evidence_label.setWordWrap(True)
        evidence_layout.addWidget(self.profile_evidence_label)
        self.profile_health_label = QLabel("Profile Health: --")
        self.profile_health_label.setWordWrap(True)
        self.profile_health_label.setTextFormat(Qt.TextFormat.RichText)
        evidence_layout.addWidget(self.profile_health_label)
        self.profile_lot_label = QLabel("Lots: --")
        self.profile_lot_label.setWordWrap(True)
        evidence_layout.addWidget(self.profile_lot_label)
        self.profile_lot_quality_label = QLabel("Lot Quality: --")
        self.profile_lot_quality_label.setWordWrap(True)
        evidence_layout.addWidget(self.profile_lot_quality_label)
        self.profile_projectile_label = QLabel("Projectile Fit: --")
        self.profile_projectile_label.setWordWrap(True)
        evidence_layout.addWidget(self.profile_projectile_label)
        self.profile_trend_label = QLabel("Trend: --")
        self.profile_trend_label.setWordWrap(True)
        evidence_layout.addWidget(self.profile_trend_label)
        self.profile_trust_label = QLabel("Trust Map: --")
        self.profile_trust_label.setWordWrap(True)
        self.profile_trust_label.setTextFormat(Qt.TextFormat.RichText)
        evidence_layout.addWidget(self.profile_trust_label)
        evidence_group.setLayout(evidence_layout)
        layout.addWidget(evidence_group)

        # Info-tekst
        info = QLabel(tr("ammo_profiles_tip_html"))
        info.setWordWrap(True)
        layout.addWidget(info)

    def load_data(self):
        """Load ammo profiles from the database."""
        profiles = self.db.get_all("ammo_profiles", "caliber, name")
        self.table.setRowCount(len(profiles))

        for i, profile in enumerate(profiles):
            self.table.setItem(i, 0, QTableWidgetItem(profile["name"]))

            # Firearm name
            rifle_name = "-"
            if profile["rifle_id"]:
                rifle = self.db.get_by_id("rifles", profile["rifle_id"])
                if rifle:
                    rifle_name = rifle["name"]
            self.table.setItem(i, 1, QTableWidgetItem(rifle_name))

            self.table.setItem(i, 2, QTableWidgetItem(profile["caliber"]))
            bullet_weight = (
                format_weight_grains(profile["bullet_weight"], "bullet")
                if profile.get("bullet_weight") not in (None, "")
                else "-"
            )
            self.table.setItem(i, 3, QTableWidgetItem(bullet_weight))

            # Krutt navn
            powder_name = "-"
            if profile["powder_id"]:
                powder = self.db.get_by_id("powder", profile["powder_id"])
                if powder:
                    powder_name = powder["name"]
            self.table.setItem(i, 4, QTableWidgetItem(powder_name))

            powder_charge = (
                format_weight_grains(profile["powder_charge"], "powder")
                if profile.get("powder_charge") not in (None, "")
                else "-"
            )
            self.table.setItem(i, 5, QTableWidgetItem(powder_charge))

            vel = (
                format_velocity_fps(profile["velocity_fps"])
                if profile["velocity_fps"]
                else "-"
            )
            self.table.setItem(i, 6, QTableWidgetItem(vel))

            bc = _format_bc_summary(
                profile.get("bc_g1"),
                profile.get("bc_g7"),
                profile.get("bc_segments_json"),
            )
            self.table.setItem(i, 7, QTableWidgetItem(bc))

            # Lagre ID
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, profile["id"])

        self.refresh_profile_evidence_panel()

    def refresh_profile_evidence_panel(self):
        row = self.table.currentRow()
        if row < 0:
            self.load_card_label.setText("Select a load to view the load card.")
            self.profile_evidence_label.setText(
                "Select a load to view chrono, groups, pressure, and reference data."
            )
            self.profile_health_label.setText("Profile Health: --")
            self.profile_lot_label.setText("Lots: --")
            self.profile_lot_quality_label.setText("Lot Quality: --")
            self.profile_projectile_label.setText("Projectile Fit: --")
            self.profile_trend_label.setText("Trend: --")
            self.profile_trust_label.setText("Trust Map: --")
            return

        item = self.table.item(row, 0)
        profile_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not profile_id:
            self.load_card_label.setText("Could not read the selected load.")
            self.profile_evidence_label.setText("Could not read the selected profile.")
            self.profile_health_label.setText("Profile Health: --")
            self.profile_lot_label.setText("Lots: --")
            self.profile_lot_quality_label.setText("Lot Quality: --")
            self.profile_projectile_label.setText("Projectile Fit: --")
            self.profile_trend_label.setText("Trend: --")
            self.profile_trust_label.setText("Trust Map: --")
            return
        load_card = build_load_card_summary(self.db, int(profile_id))
        summary = build_profile_evidence_summary(self.db, int(profile_id))
        details = load_card.get("detail_lines") or []
        self.load_card_label.setText(
            f"<b>{load_card.get('title') or 'Load Card'}</b>"
            + (
                f"<br><span style='color:#6b7280'>{load_card.get('subtitle')}</span>"
                if load_card.get("subtitle")
                else ""
            )
            + (
                f"<br>{load_card.get('component_line')}"
                if load_card.get("component_line")
                else ""
            )
            + (
                f"<br>{load_card.get('measurement_line')}"
                if load_card.get("measurement_line")
                else ""
            )
            + (
                f"<br><span style='color:#6b7280'>{load_card.get('status_line')}</span>"
                if load_card.get("status_line")
                else ""
            )
            + (
                "<br><span style='color:#6b7280'>"
                + " | ".join(str(item) for item in details[:6] if str(item).strip())
                + "</span>"
                if details
                else ""
            )
        )
        self.profile_evidence_label.setText(
            "Evidence: " + str(summary.get("evidence_label") or "no data yet")
        )
        health = build_profile_health_summary(summary)
        health_pills = [
            _status_pill("History", health.get("history_level")),
            _status_pill("Lots", health.get("lot_level")),
            _status_pill("Brass", health.get("brass_level")),
            _status_pill("Projectile", health.get("projectile_level")),
            _status_pill("Reference", health.get("reference_level")),
            _status_pill("Pressure", health.get("pressure_level")),
        ]
        health_summary = []
        health_title = str(health.get("title") or "").strip()
        if health_title:
            health_summary.append(health_title)
        health_summary_text = str(health.get("summary") or "").strip()
        if health_summary_text and health_summary_text != health_title:
            health_summary.append(health_summary_text)
        self.profile_health_label.setText(
            "<b>Profile Health</b><br>"
            + "".join(health_pills)
            + (
                "<br><span style='color:#6b7280'>"
                + " | ".join(health_summary[:2])
                + "</span>"
                if health_summary
                else ""
            )
        )
        self.profile_lot_label.setText(
            "Lots: " + str(summary.get("lot_label") or "no active lots registered")
        )
        self.profile_lot_quality_label.setText(
            "Lot Quality: "
            + str(summary.get("lot_title") or "lots not verified")
            + (
                " | Next: " + str((summary.get("lot_actions") or [""])[0]).strip()
                if isinstance(summary.get("lot_actions"), list)
                and any(
                    str(item).strip() for item in (summary.get("lot_actions") or [])
                )
                else ""
            )
        )
        self.profile_projectile_label.setText(
            "Projectile Fit: "
            + str(
                load_card.get("projectile_line")
                or summary.get("projectile_label")
                or summary.get("projectile_title")
                or "no projectile fit data yet"
            )
        )
        self.profile_trend_label.setText(
            "Trend: " + str(summary.get("trend_label") or "no trend data yet")
        )
        trust = build_profile_trust_map(summary)
        trust_pills = [
            _status_pill("Measured", trust.get("measured_level")),
            _status_pill("Simulated", trust.get("simulated_level")),
            _status_pill("Derived", trust.get("derived_level")),
            _status_pill("Assumed", trust.get("assumed_level")),
        ]
        self.profile_trust_label.setText(
            "<b>Trust Map</b><br>"
            + "".join(trust_pills)
            + (
                "<br><span style='color:#6b7280'>"
                + str(trust.get("summary") or "")
                + "</span>"
                if str(trust.get("summary") or "").strip()
                else ""
            )
        )

    def add_profile(self):
        """Add a new ammo profile."""
        rifles = self.db.get_all("rifles")
        powders = self.db.get_all("powder")
        bullets = self.db.get_all("bullets")
        primers = self.db.get_all("primers")
        cases = self.db.get_all("cases")

        dialog = AmmoProfileDialog(
            self,
            rifles=rifles,
            powders=powders,
            bullets=bullets,
            primers=primers,
            cases=cases,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("ammo_profiles", data)
            self.load_data()
            QMessageBox.information(self, tr("msg_success"), tr("ammo_profiles_added"))

    def edit_profile(self):
        """Edit the selected profile."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("ammo_profiles_select_first")
            )
            return

        profile_id = self.table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        profile = self.db.get_by_id("ammo_profiles", profile_id)
        if not profile:
            QMessageBox.warning(
                self,
                tr("ammo_profiles_missing_title"),
                tr("ammo_profiles_missing_message"),
            )
            self.load_data()
            return

        rifles = self.db.get_all("rifles")
        powders = self.db.get_all("powder")
        bullets = self.db.get_all("bullets")
        primers = self.db.get_all("primers")
        cases = self.db.get_all("cases")

        dialog = AmmoProfileDialog(
            self, profile, rifles, powders, bullets, primers, cases
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("ammo_profiles", data, "id = ?", (profile_id,))
            self.load_data()
            QMessageBox.information(
                self, tr("msg_success"), tr("ammo_profiles_updated")
            )

    def copy_profile(self):
        """Copy the selected profile."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("ammo_profiles_select_first")
            )
            return

        profile_id = self.table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        profile = self.db.get_by_id("ammo_profiles", profile_id)
        if not profile:
            QMessageBox.warning(
                self,
                tr("ammo_profiles_missing_title"),
                tr("ammo_profiles_missing_message"),
            )
            self.load_data()
            return

        # Fjern ID og endre navn
        profile = dict(profile)
        if "id" in profile:
            del profile["id"]
        if "created_date" in profile:
            del profile["created_date"]
        profile["name"] = profile["name"] + tr("ammo_profiles_copy_suffix")

        self.db.insert("ammo_profiles", profile)
        self.load_data()
        QMessageBox.information(self, tr("msg_success"), tr("ammo_profiles_copied"))

    def delete_profile(self):
        """Delete the selected profile."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("ammo_profiles_select_first")
            )
            return

        reply = QMessageBox.question(
            self,
            tr("msg_confirm_delete"),
            tr("ammo_profiles_confirm_delete"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            profile_id = self.table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete("ammo_profiles", "id = ?", (profile_id,))
            self.load_data()
            QMessageBox.information(
                self, tr("msg_success"), tr("ammo_profiles_deleted")
            )

    def open_lot_tests(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("ammo_profiles_select_first")
            )
            return
        profile_id = self.table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        profile = self.db.get_by_id("ammo_profiles", profile_id)
        if not profile:
            QMessageBox.warning(
                self,
                tr("ammo_profiles_missing_title"),
                tr("ammo_profiles_missing_message"),
            )
            self.load_data()
            return
        dialog_cls = _load_ammo_test_dialog()
        dialog = dialog_cls(
            db=self.db,
            language="en",
            rifle_id=profile.get("rifle_id"),
            ammo_profile_id=profile.get("id"),
            ammo_type=_derive_ammo_type(profile, self.db),
            parent=self,
        )
        dialog.exec()


class AmmoProfileDialog(QDialog):
    """Dialog for an ammo profile."""

    def __init__(
        self,
        parent=None,
        profile=None,
        rifles=None,
        powders=None,
        bullets=None,
        primers=None,
        cases=None,
    ):
        super().__init__(parent)
        self.profile = profile
        self.rifles = rifles or []
        self.powders = powders or []
        self.bullets = bullets or []
        self.primers = primers or []
        self.cases = cases or []
        self._all_bullets = list(self.bullets)
        self._all_cases = list(self.cases)
        self.init_ui()
        if profile:
            self.load_data()

    def init_ui(self):
        """Initialize the dialog."""
        self.setWindowTitle(tr("ammo_profiles_dialog_title"))
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Grunnleggende info
        basic_group = QGroupBox(tr("ammo_profiles_basic_info"))
        basic_layout = QFormLayout()
        basic_group.setLayout(basic_layout)

        self.name = QLineEdit()
        basic_layout.addRow(tr("ammo_profiles_name"), self.name)

        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem("No firearm profile", None)
        for rifle in self.rifles:
            self.rifle_combo.addItem(
                f"{rifle['name']} ({rifle['caliber']})", rifle["id"]
            )
        self.rifle_combo.currentIndexChanged.connect(self._sync_caliber_from_rifle)
        basic_layout.addRow("Firearm", self.rifle_combo)

        self.caliber = QLineEdit()
        basic_layout.addRow(tr("ammo_profiles_caliber"), self.caliber)

        layout.addWidget(basic_group)

        # Komponenter
        comp_group = QGroupBox(tr("ammo_profiles_components"))
        comp_layout = QFormLayout()
        comp_group.setLayout(comp_layout)

        # Kuler
        bullet_layout = QHBoxLayout()
        self.bullet_combo = QComboBox()
        self.bullet_combo.addItem(tr("ammo_profiles_select_bullet"), None)
        for bullet in self.bullets:
            self.bullet_combo.addItem(
                f"{bullet['name']} - {format_weight_grains(bullet.get('weight_grains'), 'bullet')} ({bullet['caliber']})",
                bullet["id"],
            )
        self.bullet_combo.currentIndexChanged.connect(self.on_bullet_selected)
        bullet_layout.addWidget(self.bullet_combo)
        comp_layout.addRow(tr("ammo_profiles_bullet"), bullet_layout)

        self.bullet_weight = QDoubleSpinBox()
        self.bullet_weight.setRange(20, 500)
        self.bullet_weight.setDecimals(3)
        self.bullet_weight.setSuffix(get_weight_suffix("bullet"))
        comp_layout.addRow(tr("ammo_profiles_bullet_weight"), self.bullet_weight)

        # Krutt
        powder_layout = QHBoxLayout()
        self.powder_combo = QComboBox()
        self.powder_combo.addItem(tr("ammo_profiles_select_powder"), None)
        for powder in self.powders:
            self.powder_combo.addItem(
                f"{powder['name']} ({powder['manufacturer'] if powder['manufacturer'] else 'Unknown'})",
                powder["id"],
            )
        powder_layout.addWidget(self.powder_combo)
        comp_layout.addRow(tr("ammo_profiles_powder"), powder_layout)

        self.powder_charge = QDoubleSpinBox()
        self.powder_charge.setRange(5, 100)
        self.powder_charge.setDecimals(3)
        self.powder_charge.setSingleStep(0.1)
        self.powder_charge.setSuffix(get_weight_suffix("powder"))
        comp_layout.addRow(tr("ammo_profiles_powder_charge"), self.powder_charge)

        # Tennhetter
        self.primer_combo = QComboBox()
        self.primer_combo.addItem(tr("ammo_profiles_select_primer"), None)
        for primer in self.primers:
            self.primer_combo.addItem(
                f"{primer['name']} ({primer['type'] if primer['type'] else 'Unknown'})",
                primer["id"],
            )
        comp_layout.addRow(tr("ammo_profiles_primer"), self.primer_combo)

        # Hylser
        self.case_combo = QComboBox()
        self.case_combo.addItem(tr("ammo_profiles_select_case"), None)
        for case in self.cases:
            self.case_combo.addItem(f"{case['name']} - {case['caliber']}", case["id"])
        comp_layout.addRow(tr("ammo_profiles_case"), self.case_combo)

        layout.addWidget(comp_group)

        # Settedybde og ballistikk
        bal_group = QGroupBox(tr("ammo_profiles_ballistics"))
        bal_layout = QFormLayout()
        bal_group.setLayout(bal_layout)

        self.coal = QDoubleSpinBox()
        self.coal.setRange(1.0, 5.0)
        self.coal.setDecimals(3)
        self.coal.setSingleStep(0.001)
        self.coal.setSuffix(' "')
        bal_layout.addRow(tr("ammo_profiles_coal"), self.coal)

        self.cbto = QDoubleSpinBox()
        self.cbto.setRange(1.0, 5.0)
        self.cbto.setDecimals(3)
        self.cbto.setSingleStep(0.001)
        self.cbto.setSuffix(' "')
        bal_layout.addRow(tr("ammo_profiles_cbto"), self.cbto)

        self.velocity = QSpinBox()
        self.velocity.setRange(500, 4500)
        self.velocity.setSuffix(get_velocity_suffix())
        bal_layout.addRow(tr("ammo_profiles_velocity"), self.velocity)

        self.bc_g1 = QDoubleSpinBox()
        self.bc_g1.setRange(0.1, 1.0)
        self.bc_g1.setDecimals(3)
        self.bc_g1.setSingleStep(0.001)
        bal_layout.addRow(tr("ammo_profiles_bc_g1"), self.bc_g1)

        self.bc_g7 = QDoubleSpinBox()
        self.bc_g7.setRange(0.1, 1.0)
        self.bc_g7.setDecimals(3)
        self.bc_g7.setSingleStep(0.001)
        bal_layout.addRow(tr("ammo_profiles_bc_g7"), self.bc_g7)

        self.bc_summary = QLabel(tr("ammo_profiles_bc_summary_missing"))
        self.bc_summary.setWordWrap(True)
        self.bc_summary.setStyleSheet("color: gray; font-size: 9pt;")
        bal_layout.addRow(tr("ammo_profiles_bc_summary_label"), self.bc_summary)

        self.bc_segments = QTextEdit()
        self.bc_segments.setMaximumHeight(80)
        self.bc_segments.setPlaceholderText(tr("ammo_profiles_bc_segments_placeholder"))
        bal_layout.addRow(tr("ammo_profiles_bc_segments"), self.bc_segments)

        self.bc_segments_summary = QLabel(tr("ammo_profiles_bc_segments_missing"))
        self.bc_segments_summary.setWordWrap(True)
        self.bc_segments_summary.setStyleSheet("color: gray; font-size: 9pt;")
        bal_layout.addRow(
            tr("ammo_profiles_bc_segments_summary_label"), self.bc_segments_summary
        )

        layout.addWidget(bal_group)

        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText(tr("ammo_profiles_notes_placeholder"))
        layout.addWidget(QLabel(tr("ammo_profiles_notes")))
        layout.addWidget(self.notes)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("ammo_profiles_save"))
        save_btn.clicked.connect(self.on_save)
        cancel_btn = QPushButton(tr("ammo_profiles_cancel"))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.bc_g1.valueChanged.connect(self._update_bc_summary)
        self.bc_g7.valueChanged.connect(self._update_bc_summary)
        self.bc_segments.textChanged.connect(self._update_bc_summary)
        self._apply_unit_preferences()

    def _apply_unit_preferences(self):
        bullet_in_display = weight_grains_to_display_value(20, "bullet")
        bullet_max_display = weight_grains_to_display_value(500, "bullet")
        self.bullet_weight.setRange(
            min(bullet_in_display or 20.0, bullet_max_display or 500.0),
            max(bullet_in_display or 20.0, bullet_max_display or 500.0),
        )
        self.bullet_weight.setSingleStep(
            0.1 if " g" in get_weight_suffix("bullet") else 1.0
        )
        self.bullet_weight.setSuffix(get_weight_suffix("bullet"))

        powder_min_display = weight_grains_to_display_value(5, "powder")
        powder_max_display = weight_grains_to_display_value(100, "powder")
        self.powder_charge.setRange(
            min(powder_min_display or 5.0, powder_max_display or 100.0),
            max(powder_min_display or 5.0, powder_max_display or 100.0),
        )
        self.powder_charge.setSingleStep(
            0.01 if " g" in get_weight_suffix("powder") else 0.1
        )
        self.powder_charge.setSuffix(get_weight_suffix("powder"))

        velocity_min_display = velocity_fps_to_display_value(500)
        velocity_max_display = velocity_fps_to_display_value(4500)
        self.velocity.setRange(
            int(min(velocity_min_display or 500.0, velocity_max_display or 4500.0)),
            int(max(velocity_min_display or 500.0, velocity_max_display or 4500.0)),
        )
        self.velocity.setSuffix(get_velocity_suffix())
        self._update_bc_summary()
        self._sync_caliber_from_rifle()

    def _selected_rifle_caliber(self) -> str:
        rifle_id = self.rifle_combo.currentData()
        if not rifle_id:
            return str(self.caliber.text() or "").strip()
        rifle = next((r for r in self.rifles if r.get("id") == rifle_id), None)
        return str((rifle or {}).get("caliber") or "").strip()

    def _sync_caliber_from_rifle(self):
        caliber = self._selected_rifle_caliber()
        if caliber:
            self.caliber.setText(caliber)
        self._refresh_component_filters(caliber)

    def _refresh_component_filters(self, caliber: str):
        current_bullet = self.bullet_combo.currentData()
        current_case = self.case_combo.currentData()

        self.bullet_combo.blockSignals(True)
        self.bullet_combo.clear()
        self.bullet_combo.addItem(tr("ammo_profiles_select_bullet"), None)
        for bullet in self._all_bullets:
            bullet_caliber = str(bullet.get("caliber") or "").strip()
            if caliber and bullet_caliber and bullet_caliber != caliber:
                continue
            self.bullet_combo.addItem(
                f"{bullet['name']} - {format_weight_grains(bullet.get('weight_grains'), 'bullet')} ({bullet['caliber']})",
                bullet["id"],
            )
            if current_bullet == bullet["id"]:
                self.bullet_combo.setCurrentIndex(self.bullet_combo.count() - 1)
        self.bullet_combo.blockSignals(False)

        self.case_combo.clear()
        self.case_combo.addItem(tr("ammo_profiles_select_case"), None)
        for case in self._all_cases:
            case_caliber = str(case.get("caliber") or "").strip()
            if caliber and case_caliber and case_caliber != caliber:
                continue
            self.case_combo.addItem(f"{case['name']} - {case['caliber']}", case["id"])
            if current_case == case["id"]:
                self.case_combo.setCurrentIndex(self.case_combo.count() - 1)

    def on_bullet_selected(self, index):
        """When a bullet is selected, fill weight and BC automatically."""
        bullet_id = self.bullet_combo.currentData()
        if bullet_id:
            bullet = self.db.get_by_id("bullets", bullet_id)
            if bullet:
                display_weight = weight_grains_to_display_value(
                    bullet["weight_grains"], "bullet"
                )
                if display_weight is not None:
                    self.bullet_weight.setValue(display_weight)
                if bullet["bc_g1"]:
                    self.bc_g1.setValue(bullet["bc_g1"])
                if bullet["bc_g7"]:
                    self.bc_g7.setValue(bullet["bc_g7"])
                self.bc_segments.setPlainText(str(bullet.get("bc_segments_json") or ""))
        self._update_bc_summary()

    def _update_bc_summary(self):
        self.bc_summary.setText(
            _format_bc_summary(
                self.bc_g1.value() if self.bc_g1.value() > 0 else None,
                self.bc_g7.value() if self.bc_g7.value() > 0 else None,
                self.bc_segments.toPlainText(),
            )
        )
        self.bc_segments_summary.setText(
            _format_bc_segments_summary(self.bc_segments.toPlainText())
        )

    def load_data(self):
        """Load profile data."""
        self.name.setText(self.profile["name"])

        # Firearm
        if self.profile["rifle_id"]:
            for i in range(self.rifle_combo.count()):
                if self.rifle_combo.itemData(i) == self.profile["rifle_id"]:
                    self.rifle_combo.setCurrentIndex(i)
                    break

        self.caliber.setText(self.profile["caliber"])

        # Bullet
        if self.profile["bullet_id"]:
            for i in range(self.bullet_combo.count()):
                if self.bullet_combo.itemData(i) == self.profile["bullet_id"]:
                    self.bullet_combo.setCurrentIndex(i)
                    break

        bullet_weight_display = weight_grains_to_display_value(
            self.profile["bullet_weight"], "bullet"
        )
        if bullet_weight_display is not None:
            self.bullet_weight.setValue(bullet_weight_display)

        # Powder
        if self.profile["powder_id"]:
            for i in range(self.powder_combo.count()):
                if self.powder_combo.itemData(i) == self.profile["powder_id"]:
                    self.powder_combo.setCurrentIndex(i)
                    break

        powder_charge_display = weight_grains_to_display_value(
            self.profile["powder_charge"], "powder"
        )
        if powder_charge_display is not None:
            self.powder_charge.setValue(powder_charge_display)

        # Primer
        if self.profile["primer_id"]:
            for i in range(self.primer_combo.count()):
                if self.primer_combo.itemData(i) == self.profile["primer_id"]:
                    self.primer_combo.setCurrentIndex(i)
                    break

        # Case
        if self.profile["case_id"]:
            for i in range(self.case_combo.count()):
                if self.case_combo.itemData(i) == self.profile["case_id"]:
                    self.case_combo.setCurrentIndex(i)
                    break

        # Ballistikk
        if self.profile["coal"]:
            self.coal.setValue(self.profile["coal"])
        if self.profile["cbto"]:
            self.cbto.setValue(self.profile["cbto"])
        if self.profile["velocity_fps"]:
            velocity_display = velocity_fps_to_display_value(
                self.profile["velocity_fps"]
            )
            if velocity_display is not None:
                self.velocity.setValue(int(round(velocity_display)))
        if self.profile["bc_g1"]:
            self.bc_g1.setValue(self.profile["bc_g1"])
        if self.profile["bc_g7"]:
            self.bc_g7.setValue(self.profile["bc_g7"])
        if self.profile.get("bc_segments_json"):
            self.bc_segments.setPlainText(
                str(self.profile.get("bc_segments_json") or "")
            )
        self._update_bc_summary()
        if self.profile["notes"]:
            self.notes.setText(self.profile["notes"])

    def on_save(self):
        caliber = (
            self._selected_rifle_caliber() or str(self.caliber.text() or "").strip()
        )
        bullet_id = self.bullet_combo.currentData()
        case_id = self.case_combo.currentData()
        if bullet_id:
            bullet = self.db.get_by_id("bullets", bullet_id)
            bullet_caliber = str((bullet or {}).get("caliber") or "").strip()
            if caliber and bullet_caliber and bullet_caliber != caliber:
                QMessageBox.warning(
                    self, tr("msg_warning"), tr("ammo_profiles_caliber_mismatch")
                )
                return
        if case_id:
            case = self.db.get_by_id("cases", case_id)
            case_caliber = str((case or {}).get("caliber") or "").strip()
            if caliber and case_caliber and case_caliber != caliber:
                QMessageBox.warning(
                    self, tr("msg_warning"), tr("ammo_profiles_caliber_mismatch")
                )
                return
        self.accept()

    def get_data(self):
        """Return profile data."""
        locked_caliber = self._selected_rifle_caliber() or self.caliber.text()
        bullet_weight_gr = weight_display_to_grains(
            self.bullet_weight.value(), "bullet"
        )
        powder_charge_gr = weight_display_to_grains(
            self.powder_charge.value(), "powder"
        )
        velocity_fps = velocity_display_to_fps(self.velocity.value())
        return {
            "name": self.name.text(),
            "rifle_id": self.rifle_combo.currentData(),
            "caliber": locked_caliber,
            "bullet_id": self.bullet_combo.currentData(),
            "bullet_weight": (
                bullet_weight_gr
                if bullet_weight_gr is not None
                else self.bullet_weight.value()
            ),
            "powder_id": self.powder_combo.currentData(),
            "powder_charge": (
                powder_charge_gr
                if powder_charge_gr is not None
                else self.powder_charge.value()
            ),
            "primer_id": self.primer_combo.currentData(),
            "case_id": self.case_combo.currentData(),
            "coal": self.coal.value() if self.coal.value() > 0 else None,
            "cbto": self.cbto.value() if self.cbto.value() > 0 else None,
            "velocity_fps": (
                velocity_fps if velocity_fps and velocity_fps > 0 else None
            ),
            "bc_g1": self.bc_g1.value() if self.bc_g1.value() > 0 else None,
            "bc_g7": self.bc_g7.value() if self.bc_g7.value() > 0 else None,
            "bc_segments_json": _normalize_bc_segments_json(
                self.bc_segments.toPlainText()
            ),
            "notes": self.notes.toPlainText(),
        }
