"""
Safety Dashboard - pressure signal tracking and safety
Systematic logging and analysis of pressure indications
"""

from datetime import datetime

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..tools.load_session_runtime_service import (
    build_active_workflow_context_from_settings,
)
from ..ui.reloading_theme import ReloadingTheme
from ..utils.i18n import tr


def _label_primer_image_quality(quality: str | None) -> str:
    value = str(quality or "").strip().lower()
    return {
        "poor": tr("safety_dashboard_primer_image_quality_poor"),
        "ok": tr("safety_dashboard_primer_image_quality_ok"),
        "good": tr("safety_dashboard_primer_image_quality_good"),
    }.get(value, "")


def _label_primer_image_confidence(confidence: str | None) -> str:
    value = str(confidence or "").strip().lower()
    return {
        "low": tr("safety_dashboard_primer_image_confidence_low"),
        "medium": tr("safety_dashboard_primer_image_confidence_medium"),
        "high": tr("safety_dashboard_primer_image_confidence_high"),
    }.get(value, "")


def _format_primer_image_summary(
    path: str | None,
    quality: str | None,
    confidence: str | None,
    observation: str | None,
) -> str:
    path_text = str(path or "").strip()
    observation_text = str(observation or "").strip()
    if not path_text and not observation_text:
        return ""

    detail_parts = []
    quality_label = _label_primer_image_quality(quality)
    if quality_label:
        detail_parts.append(quality_label)
    confidence_label = _label_primer_image_confidence(confidence)
    if confidence_label:
        detail_parts.append(confidence_label)

    summary = tr("safety_dashboard_primer_image_summary_present")
    if detail_parts:
        summary += f" ({', '.join(detail_parts)})"
    if observation_text:
        summary += f": {observation_text}"
    return summary


def _coerce_optional_int(value) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def _coerce_optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _first_row_value(rows, column_name: str):
    if not rows:
        return None
    row = rows[0]
    if isinstance(row, dict):
        return row.get(column_name)
    try:
        return row[column_name]
    except Exception:
        pass
    try:
        return row[0]
    except Exception:
        return None


def _resolve_context_ammo_profile_id(db, context: dict[str, object]) -> int | None:
    direct_ammo_profile_id = _coerce_optional_int(context.get("ammo_profile_id"))
    if direct_ammo_profile_id is not None:
        return direct_ammo_profile_id

    load_session_id = _coerce_optional_int(context.get("load_session_id"))
    if load_session_id is not None and db is not None:
        rows = db.execute_query(
            "SELECT ammo_profile_id FROM load_development_sessions WHERE id = ?",
            (load_session_id,),
        )
        resolved = _coerce_optional_int(_first_row_value(rows, "ammo_profile_id"))
        if resolved is not None:
            return resolved

    workflow_id = _coerce_optional_int(context.get("workflow_id"))
    if workflow_id is not None and db is not None:
        rows = db.execute_query(
            """
            SELECT ammo_profile_id
            FROM batch_projects
            WHERE source_workflow = ? AND ammo_profile_id IS NOT NULL
            ORDER BY updated_date DESC, id DESC
            LIMIT 1
            """,
            (f"workflow:{workflow_id}",),
        )
        return _coerce_optional_int(_first_row_value(rows, "ammo_profile_id"))

    return None


def _get_active_workflow_context() -> dict[str, object]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    try:
        database = get_database()
    except Exception:
        database = None
    return build_active_workflow_context_from_settings(
        settings,
        database,
        int_fields=("ammo_profile_id", "rifle_id"),
    )


def _format_analysis_scope(
    ammo_name: str | None,
    rifle_id: int | None,
    barrel_id: str | None,
    barrel_name: str | None,
) -> str:
    ammo_label = str(ammo_name or tr("common_na")).strip() or tr("common_na")
    barrel_label = str(barrel_name or barrel_id or "").strip()
    if rifle_id is None:
        if barrel_label:
            return (
                f"{ammo_label} ({tr('safety_dashboard_analysis_scope_unlinked')}, "
                f"{tr('safety_dashboard_analysis_scope_barrel', barrel=barrel_label)})"
            )
        return f"{ammo_label} ({tr('safety_dashboard_analysis_scope_unlinked')})"
    if barrel_label:
        return (
            f"{ammo_label} ({tr('safety_dashboard_analysis_scope_rifle', rifle_id=rifle_id)}, "
            f"{tr('safety_dashboard_analysis_scope_barrel', barrel=barrel_label)})"
        )
    return f"{ammo_label} ({tr('safety_dashboard_analysis_scope_rifle', rifle_id=rifle_id)})"


def _build_analysis_scope_note(
    *,
    rifle_id: int | None,
    barrel_id: str | None,
    barrel_name: str | None,
    total_observations: int,
    linked_workflows: int,
    linked_sessions: int,
    distinct_days: int,
) -> str:
    barrel_label = str(barrel_name or barrel_id or "").strip()
    if rifle_id is None:
        if barrel_label:
            return tr(
                "safety_dashboard_analysis_unlinked_barrel_note", barrel=barrel_label
            )
        return tr("safety_dashboard_analysis_unlinked_note")

    parts = [
        tr(
            "safety_dashboard_analysis_rifle_note",
            rifle_id=rifle_id,
        )
    ]
    if barrel_label:
        parts.append(
            tr(
                "safety_dashboard_analysis_barrel_note",
                barrel=barrel_label,
            )
        )
    if linked_workflows or linked_sessions:
        parts.append(
            tr(
                "safety_dashboard_analysis_context_note",
                workflows=linked_workflows,
                sessions=linked_sessions,
                observations=total_observations,
                days=distinct_days,
            )
        )
    return " ".join(part for part in parts if part)


class SafetyDashboard(QWidget):
    """Widget for safety and pressure indications."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.active_workflow_context = _get_active_workflow_context()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel(tr("safety_dashboard_title"))
        title.setProperty("role", "title")
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel(tr("safety_dashboard_subtitle"))
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Warning
        warning_group = QGroupBox(tr("safety_dashboard_warning_title"))
        warning_group.setProperty("variant", "warning")
        warning_layout = QVBoxLayout()
        warning_group.setLayout(warning_layout)
        warning = QLabel(tr("safety_dashboard_warning_text"))
        warning.setWordWrap(True)
        warning_layout.addWidget(warning)
        layout.addWidget(warning_group)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        tabs.addTab(self.create_overview_tab(), tr("safety_dashboard_tab_overview"))
        tabs.addTab(self.create_log_tab(), tr("safety_dashboard_tab_log"))
        tabs.addTab(self.create_history_tab(), tr("safety_dashboard_tab_history"))
        tabs.addTab(self.create_analysis_tab(), tr("safety_dashboard_tab_analysis"))

    def create_overview_tab(self):
        """Create the overview tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Status cards
        cards_layout = QHBoxLayout()
        layout.addLayout(cards_layout)

        self.safe_loads_card = self.create_status_card(
            tr("safety_dashboard_card_safe"), "0", ReloadingTheme.SUCCESS
        )
        cards_layout.addWidget(self.safe_loads_card)

        self.moderate_card = self.create_status_card(
            tr("safety_dashboard_card_moderate"), "0", ReloadingTheme.WARNING
        )
        cards_layout.addWidget(self.moderate_card)

        self.high_card = self.create_status_card(
            tr("safety_dashboard_card_high"), "0", ReloadingTheme.DANGER
        )
        cards_layout.addWidget(self.high_card)

        self.critical_card = self.create_status_card(
            tr("safety_dashboard_card_critical"), "0", ReloadingTheme.DANGER
        )
        cards_layout.addWidget(self.critical_card)

        # Recent alerts
        alerts_group = QGroupBox(tr("safety_dashboard_recent_alerts_title"))
        alerts_group.setProperty("variant", "panel")
        alerts_layout = QVBoxLayout()
        alerts_group.setLayout(alerts_layout)

        self.recent_alerts_table = QTableWidget()
        self.recent_alerts_table.setColumnCount(6)
        self.recent_alerts_table.setHorizontalHeaderLabels(
            [
                tr("common_date"),
                tr("common_ammunition"),
                tr("common_charge"),
                tr("common_severity"),
                tr("common_signals"),
                tr("safety_dashboard_primer_image_column"),
            ]
        )
        self.recent_alerts_table.setMaximumHeight(250)
        alerts_layout.addWidget(self.recent_alerts_table)

        layout.addWidget(alerts_group)

        # Quick reference guide
        guide_group = QGroupBox(tr("safety_dashboard_guide_title"))
        guide_group.setProperty("variant", "panel")
        guide_layout = QVBoxLayout()
        guide_group.setLayout(guide_layout)

        guide_text = QLabel(tr("safety_dashboard_guide_html"))
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text)

        layout.addWidget(guide_group)

        # Load initial data
        self.refresh_overview()

        return widget

    def create_log_tab(self):
        """Oppretter logg-fane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(tr("safety_dashboard_log_info"))
        info.setWordWrap(True)
        info.setProperty("role", "muted")
        layout.addWidget(info)

        # Knapper
        btn_layout = QHBoxLayout()

        new_btn = QPushButton(tr("safety_dashboard_log_new"))
        new_btn.setProperty("variant", "primary")
        new_btn.setProperty("size", "lg")
        new_btn.clicked.connect(self.log_pressure_sign)
        btn_layout.addWidget(new_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell over siste observasjoner
        table_group = QGroupBox(tr("safety_dashboard_latest_observations"))
        table_group.setProperty("variant", "panel")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(7)
        self.log_table.setHorizontalHeaderLabels(
            [
                tr("common_date"),
                tr("common_ammunition"),
                tr("common_charge"),
                tr("common_score"),
                tr("common_severity"),
                tr("safety_dashboard_primer_image_column"),
                tr("common_notes"),
            ]
        )
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

        filter_layout.addWidget(QLabel(tr("common_ammunition") + ":"))
        self.history_ammo_filter = QComboBox()
        self.history_ammo_filter.addItem(tr("common_all"), None)
        self.load_ammo_profiles_to_filter()
        self.history_ammo_filter.currentIndexChanged.connect(self.refresh_history)
        filter_layout.addWidget(self.history_ammo_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Historikk-tabell
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels(
            [
                "Dato",
                tr("common_ammunition"),
                tr("safety_dashboard_charge_gr"),
                tr("safety_dashboard_signal_flat_primer_short"),
                tr("safety_dashboard_signal_primer_crater_short"),
                tr("safety_dashboard_signal_ejector_short"),
                tr("safety_dashboard_signal_heavy_bolt_short"),
                tr("safety_dashboard_primer_image_column"),
                tr("common_score"),
            ]
        )
        layout.addWidget(self.history_table)

        self.refresh_history()

        return widget

    def create_analysis_tab(self):
        """Oppretter analysefane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(tr("safety_dashboard_analysis_info"))
        info.setWordWrap(True)
        info.setProperty("role", "muted")
        layout.addWidget(info)

        # Analyse-resultater
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        self.analysis_results.setMinimumHeight(400)
        layout.addWidget(self.analysis_results)

        # Analyser-knapp
        analyze_btn = QPushButton(tr("safety_dashboard_run_analysis"))
        analyze_btn.setProperty("variant", "primary")
        analyze_btn.clicked.connect(self.run_analysis)
        layout.addWidget(analyze_btn)

        return widget

    def create_status_card(self, title, value, color):
        """Oppretter status-kort"""
        card = QFrame()
        card.setMinimumHeight(90)
        card.setProperty("variant", "statCard")

        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(10)
        card.setLayout(card_layout)

        accent_bar = QFrame(card)
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(
            f"background-color: {color}; border: none; border-radius: 2px;"
        )
        card_layout.addWidget(accent_bar)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(4)
        card_layout.addLayout(content, 1)

        value_label = QLabel(value)
        value_label.setProperty("variant", "statValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setProperty("variant", "statTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content.addWidget(title_label)

        card.value_label = value_label

        return card

    def load_ammo_profiles_to_filter(self):
        """Laster ammunisjonsprofiler"""
        ammos = self.db.execute_query(
            "SELECT id, name FROM ammo_profiles ORDER BY name"
        )
        for ammo_id, name in ammos:
            self.history_ammo_filter.addItem(name, ammo_id)

    def log_pressure_sign(self):
        """Åpner dialog for å logge trykksignal"""
        dialog = PressureSignDialog(self, context=self.active_workflow_context)
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
        if data["flat_primer"]:
            score += 2
        if data["primer_crater"]:
            score += 3
        if data["ejector_mark"]:
            score += 3
        if data["extractor_mark"]:
            score += 2
        if data["heavy_bolt_lift"]:
            score += 5
        if data["velocity_spike"]:
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
                velocity_spike, pressure_score, severity_level, notes, date,
                primer_image_path, primer_image_quality, primer_image_observation,
                primer_image_confidence, workflow_id, load_session_id, session_name,
                rifle_id, barrel_id, barrel_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            data["ammo_id"],
            data["charge_weight"],
            1 if data["flat_primer"] else 0,
            1 if data["primer_crater"] else 0,
            1 if data["ejector_mark"] else 0,
            1 if data["extractor_mark"] else 0,
            1 if data["heavy_bolt_lift"] else 0,
            data.get("case_head_expansion"),
            1 if data["velocity_spike"] else 0,
            score,
            severity,
            data["notes"],
            datetime.now().strftime("%Y-%m-%d"),
            str(data.get("primer_image_path") or "").strip() or None,
            str(data.get("primer_image_quality") or "").strip() or None,
            str(data.get("primer_image_observation") or "").strip() or None,
            str(data.get("primer_image_confidence") or "").strip() or None,
            _coerce_optional_int(data.get("workflow_id")),
            _coerce_optional_int(data.get("load_session_id")),
            str(data.get("session_name") or "").strip() or None,
            _coerce_optional_int(data.get("rifle_id")),
            _coerce_optional_text(data.get("barrel_id")),
            _coerce_optional_text(data.get("barrel_name")),
        )

        self.db.execute_update(query, params)

        QMessageBox.information(
            self,
            tr("common_saved"),
            tr(
                "safety_dashboard_saved_message",
                score=score,
                severity=self._severity_label(severity),
            ),
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
        moderate = (
            moderate_result[0] if moderate_result and len(moderate_result) > 0 else [0]
        )
        moderate = moderate[0] if isinstance(moderate, (list, tuple)) else moderate

        high_result = self.db.execute_query(
            "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'HØY'"
        )
        high = high_result[0] if high_result and len(high_result) > 0 else [0]
        high = high[0] if isinstance(high, (list, tuple)) else high

        critical_result = self.db.execute_query(
            "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'KRITISK'"
        )
        critical = (
            critical_result[0] if critical_result and len(critical_result) > 0 else [0]
        )
        critical = critical[0] if isinstance(critical, (list, tuple)) else critical

        self.safe_loads_card.value_label.setText(str(safe))
        self.moderate_card.value_label.setText(str(moderate))
        self.high_card.value_label.setText(str(high))
        self.critical_card.value_label.setText(str(critical))

        # Siste varsler
        recent = self.db.execute_query(
            """
            SELECT ps.date, ap.name, ps.charge_weight, ps.severity_level,
                 ps.flat_primer, ps.primer_crater, ps.ejector_mark, ps.heavy_bolt_lift,
                 ps.primer_image_path, ps.primer_image_quality,
                 ps.primer_image_observation, ps.primer_image_confidence
            FROM pressure_signs ps
            LEFT JOIN ammo_profiles ap ON ps.ammo_profile_id = ap.id
            WHERE ps.severity_level IN ('HØY', 'KRITISK')
            ORDER BY ps.date DESC
            LIMIT 10
        """
        )

        self.recent_alerts_table.setRowCount(len(recent))

        for i, row in enumerate(recent):
            (
                date,
                ammo,
                charge,
                severity,
                flat,
                crater,
                ejector,
                bolt,
                primer_image_path,
                primer_image_quality,
                primer_image_observation,
                primer_image_confidence,
            ) = row

            signals = []
            if flat:
                signals.append(tr("safety_dashboard_signal_flat_primer_short"))
            if crater:
                signals.append(tr("safety_dashboard_signal_primer_crater_short"))
            if ejector:
                signals.append(tr("safety_dashboard_signal_ejector_short"))
            if bolt:
                signals.append(tr("safety_dashboard_signal_heavy_bolt_short"))

            self.recent_alerts_table.setItem(i, 0, QTableWidgetItem(date))
            self.recent_alerts_table.setItem(
                i, 1, QTableWidgetItem(ammo or tr("common_na"))
            )
            self.recent_alerts_table.setItem(i, 2, QTableWidgetItem(f"{charge:.1f} gr"))
            self.recent_alerts_table.setItem(
                i, 3, QTableWidgetItem(self._severity_label(severity))
            )
            self.recent_alerts_table.setItem(i, 4, QTableWidgetItem(", ".join(signals)))
            self.recent_alerts_table.setItem(
                i,
                5,
                QTableWidgetItem(
                    _format_primer_image_summary(
                        primer_image_path,
                        primer_image_quality,
                        primer_image_confidence,
                        primer_image_observation,
                    )
                ),
            )

            # Fargelegg
            color = (
                QColor(220, 53, 69, 100)
                if severity == "KRITISK"
                else QColor(255, 193, 7, 100)
            )
            for col in range(6):
                self.recent_alerts_table.item(i, col).setBackground(color)

    def refresh_log_table(self):
        """Oppdaterer logg-tabell"""
        logs = self.db.execute_query(
            """
            SELECT ps.date, ap.name, ps.charge_weight, ps.pressure_score,
                   ps.severity_level, ps.primer_image_path,
                   ps.primer_image_quality, ps.primer_image_observation,
                   ps.primer_image_confidence, ps.notes
            FROM pressure_signs ps
            LEFT JOIN ammo_profiles ap ON ps.ammo_profile_id = ap.id
            ORDER BY ps.date DESC
            LIMIT 20
        """
        )

        self.log_table.setRowCount(len(logs))

        for i, row in enumerate(logs):
            (
                date,
                ammo,
                charge,
                score,
                severity,
                primer_image_path,
                primer_image_quality,
                primer_image_observation,
                primer_image_confidence,
                notes,
            ) = row

            values = [
                date or "",
                ammo or "",
                f"{charge:.1f} gr" if charge else "",
                str(score) if score is not None else "",
                self._severity_label(severity) if severity else "",
                _format_primer_image_summary(
                    primer_image_path,
                    primer_image_quality,
                    primer_image_confidence,
                    primer_image_observation,
                ),
                notes or "",
            ]
            for j, value in enumerate(values):
                self.log_table.setItem(i, j, QTableWidgetItem(value))

    def refresh_history(self):
        """Oppdaterer historikk"""
        ammo_id = self.history_ammo_filter.currentData()

        query = """
            SELECT ps.date, ap.name, ps.charge_weight, ps.flat_primer,
                   ps.primer_crater, ps.ejector_mark, ps.heavy_bolt_lift,
                   ps.primer_image_path, ps.primer_image_quality,
                   ps.primer_image_observation, ps.primer_image_confidence,
                   ps.pressure_score
            FROM pressure_signs ps
            LEFT JOIN ammo_profiles ap ON ps.ammo_profile_id = ap.id
        """

        if ammo_id:
            query += " WHERE ps.ammo_profile_id = ?"
            history = self.db.execute_query(
                query + " ORDER BY ps.charge_weight", (ammo_id,)
            )
        else:
            history = self.db.execute_query(query + " ORDER BY ps.date DESC")

        self.history_table.setRowCount(len(history))

        for i, row in enumerate(history):
            (
                date,
                ammo,
                charge,
                flat_primer,
                primer_crater,
                ejector_mark,
                heavy_bolt_lift,
                primer_image_path,
                primer_image_quality,
                primer_image_observation,
                primer_image_confidence,
                pressure_score,
            ) = row

            values = [
                date or "",
                ammo or "",
                f"{charge:.1f}" if charge else "",
                "✓" if flat_primer else "",
                "✓" if primer_crater else "",
                "✓" if ejector_mark else "",
                "✓" if heavy_bolt_lift else "",
                _format_primer_image_summary(
                    primer_image_path,
                    primer_image_quality,
                    primer_image_confidence,
                    primer_image_observation,
                ),
                str(pressure_score) if pressure_score is not None else "",
            ]
            for j, value in enumerate(values):
                self.history_table.setItem(i, j, QTableWidgetItem(value))

    def run_analysis(self):
        """Kjører analyse av trykk-terskler"""
        # Grupper per ammunisjon og riflekontekst. Ulenkede rader holdes adskilt.
        ammos = self.db.execute_query(
            """
            SELECT DISTINCT ap.id, ap.name, ps.rifle_id, ps.barrel_id, ps.barrel_name
            FROM pressure_signs ps
            JOIN ammo_profiles ap ON ps.ammo_profile_id = ap.id
            ORDER BY ap.name, ps.rifle_id, ps.barrel_name, ps.barrel_id
        """
        )

        if not ammos:
            self.analysis_results.setText(tr("safety_dashboard_analysis_no_data"))
            return

        results = f"<h2>{tr('safety_dashboard_analysis_heading')}</h2>"

        for ammo_id, ammo_name, rifle_id, barrel_id, barrel_name in ammos:
            scope_title = _format_analysis_scope(
                ammo_name, rifle_id, barrel_id, barrel_name
            )
            results += f"<h3>{scope_title}</h3>"

            if rifle_id is None and not str(barrel_id or "").strip():
                scope_clause = (
                    " AND rifle_id IS NULL AND (barrel_id IS NULL OR barrel_id = '')"
                )
                scope_params = (ammo_id,)
            else:
                scope_parts = []
                scope_params_list: list[object] = [ammo_id]
                if rifle_id is None:
                    scope_parts.append("(rifle_id IS NULL)")
                else:
                    scope_parts.append("rifle_id = ?")
                    scope_params_list.append(rifle_id)
                barrel_id_text = str(barrel_id or "").strip()
                if barrel_id_text:
                    scope_parts.append("barrel_id = ?")
                    scope_params_list.append(barrel_id_text)
                else:
                    scope_parts.append("(barrel_id IS NULL OR barrel_id = '')")
                scope_clause = " AND " + " AND ".join(scope_parts)
                scope_params = tuple(scope_params_list)

            # Finn høyeste sikre ladning (score < 3)
            safe_loads = self.db.execute_query(
                (
                    "SELECT MAX(charge_weight) "
                    "FROM pressure_signs "
                    "WHERE ammo_profile_id = ? AND pressure_score < 3" + scope_clause
                ),
                scope_params,
            )

            max_safe = safe_loads[0][0] if safe_loads and safe_loads[0][0] else None

            # Finn første tegn på trykk
            first_pressure = self.db.execute_query(
                (
                    "SELECT MIN(charge_weight) "
                    "FROM pressure_signs "
                    "WHERE ammo_profile_id = ? AND pressure_score >= 3" + scope_clause
                ),
                scope_params,
            )

            first_sign = (
                first_pressure[0][0]
                if first_pressure and first_pressure[0][0]
                else None
            )

            primer_image_stats = self.db.execute_query(
                (
                    "SELECT COUNT(*), "
                    "SUM( CASE "
                    "WHEN COALESCE(primer_image_path, '') != '' "
                    "OR COALESCE(primer_image_observation, '') != '' "
                    "THEN 1 ELSE 0 END ), "
                    "COUNT(DISTINCT workflow_id), "
                    "COUNT(DISTINCT load_session_id), "
                    "COUNT(DISTINCT date) "
                    "FROM pressure_signs "
                    "WHERE ammo_profile_id = ?" + scope_clause
                ),
                scope_params,
            )
            total_observations = 0
            primer_supported = 0
            linked_workflows = 0
            linked_sessions = 0
            distinct_days = 0
            if primer_image_stats:
                total_observations = int(primer_image_stats[0][0] or 0)
                primer_supported = int(primer_image_stats[0][1] or 0)
                linked_workflows = int(primer_image_stats[0][2] or 0)
                linked_sessions = int(primer_image_stats[0][3] or 0)
                distinct_days = int(primer_image_stats[0][4] or 0)

            scope_note = _build_analysis_scope_note(
                rifle_id=rifle_id,
                barrel_id=barrel_id,
                barrel_name=barrel_name,
                total_observations=total_observations,
                linked_workflows=linked_workflows,
                linked_sessions=linked_sessions,
                distinct_days=distinct_days,
            )

            results += (
                f"<p><b>{tr('safety_dashboard_analysis_scope_label')}</b> "
                f"{scope_title}</p>"
            )
            results += f"<p><i>{scope_note}</i></p>"

            if max_safe:
                results += (
                    "<p><b>"
                    + tr("safety_dashboard_analysis_max_safe_label")
                    + f"</b> {max_safe:.1f} gr "
                    + tr("safety_dashboard_analysis_max_safe_note")
                    + "</p>"
                )

            if first_sign:
                results += (
                    f"<p><b>{tr('safety_dashboard_analysis_first_sign_label')}</b> "
                    f"{first_sign:.1f} gr</p>"
                )
                if max_safe:
                    margin = first_sign - max_safe
                    results += (
                        f"<p><b>{tr('safety_dashboard_analysis_margin_label')}</b> "
                        f"{margin:.1f} gr</p>"
                    )

            if not max_safe and not first_sign:
                results += (
                    f"<p><i>{tr('safety_dashboard_analysis_insufficient_data')}</i></p>"
                )

            if primer_supported:
                results += (
                    f"<p><b>{tr('safety_dashboard_primer_image_analysis_label')}</b> "
                    f"{primer_supported}/{total_observations} "
                    f"{tr('safety_dashboard_primer_image_analysis_supported')}</p>"
                )
            else:
                results += (
                    f"<p><b>{tr('safety_dashboard_primer_image_analysis_label')}</b> "
                    f"{tr('safety_dashboard_primer_image_analysis_none')}</p>"
                )

            results += "<hr>"

        self.analysis_results.setHtml(results)

    def _severity_label(self, severity: str) -> str:
        return {
            "LAV": tr("safety_dashboard_severity_low"),
            "MODERAT": tr("safety_dashboard_severity_moderate"),
            "HØY": tr("safety_dashboard_severity_high"),
            "KRITISK": tr("safety_dashboard_severity_critical"),
        }.get(severity, severity)


class PressureSignDialog(QDialog):
    """Dialog for å logge trykksignal"""

    def __init__(self, parent=None, *, context: dict[str, object] | None = None):
        super().__init__(parent)
        self.db = get_database()
        self.context = dict(context or {})
        self.setWindowTitle(tr("safety_dashboard_dialog_title"))
        self.setMinimumWidth(500)
        self.init_ui()
        self._apply_context_defaults()

    def init_ui(self):
        """Initialiserer dialog"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Info
        info = QLabel(tr("safety_dashboard_dialog_info"))
        layout.addWidget(info)

        # Form
        form = QFormLayout()

        # Ammunisjon
        self.ammo_combo = QComboBox()
        self.load_ammo_profiles()
        form.addRow(tr("common_ammunition") + ":", self.ammo_combo)

        # Ladning
        self.charge_weight = QDoubleSpinBox()
        self.charge_weight.setRange(10, 100)
        self.charge_weight.setValue(40.0)
        self.charge_weight.setDecimals(1)
        self.charge_weight.setSuffix(" gr")
        form.addRow(tr("safety_dashboard_powder_weight") + ":", self.charge_weight)

        layout.addLayout(form)

        # Checkboxes for signaler
        signals_group = QGroupBox(tr("safety_dashboard_observed_signals"))
        signals_layout = QVBoxLayout()
        signals_group.setLayout(signals_layout)

        self.flat_primer = QCheckBox(tr("safety_dashboard_signal_flat_primer"))
        signals_layout.addWidget(self.flat_primer)

        self.primer_crater = QCheckBox(tr("safety_dashboard_signal_primer_crater"))
        signals_layout.addWidget(self.primer_crater)

        self.ejector_mark = QCheckBox(tr("safety_dashboard_signal_ejector"))
        signals_layout.addWidget(self.ejector_mark)

        self.extractor_mark = QCheckBox(tr("safety_dashboard_signal_extractor"))
        signals_layout.addWidget(self.extractor_mark)

        self.heavy_bolt_lift = QCheckBox(tr("safety_dashboard_signal_heavy_bolt"))
        signals_layout.addWidget(self.heavy_bolt_lift)

        self.velocity_spike = QCheckBox(tr("safety_dashboard_signal_velocity_spike"))
        signals_layout.addWidget(self.velocity_spike)

        layout.addWidget(signals_group)

        # Case head expansion (optional)
        case_form = QFormLayout()
        self.case_head = QDoubleSpinBox()
        self.case_head.setRange(0, 1)
        self.case_head.setValue(0)
        self.case_head.setDecimals(4)
        self.case_head.setSuffix(" inches")
        case_form.addRow(
            tr("safety_dashboard_case_head_expansion") + ":", self.case_head
        )
        layout.addLayout(case_form)

        primer_image_group = QGroupBox(tr("safety_dashboard_primer_image_title"))
        primer_image_layout = QFormLayout()
        primer_image_group.setLayout(primer_image_layout)

        primer_image_path_row = QHBoxLayout()
        self.primer_image_path = QLineEdit()
        self.primer_image_path.setPlaceholderText(
            tr("safety_dashboard_primer_image_path_placeholder")
        )
        primer_image_path_row.addWidget(self.primer_image_path)
        self.primer_image_browse_btn = QPushButton(tr("common_open"))
        self.primer_image_browse_btn.clicked.connect(self.browse_primer_image)
        primer_image_path_row.addWidget(self.primer_image_browse_btn)
        primer_image_layout.addRow(
            tr("safety_dashboard_primer_image_path") + ":", primer_image_path_row
        )

        self.primer_image_quality = QComboBox()
        self.primer_image_quality.addItem(
            tr("safety_dashboard_primer_image_quality_unknown"), "unknown"
        )
        self.primer_image_quality.addItem(
            tr("safety_dashboard_primer_image_quality_poor"), "poor"
        )
        self.primer_image_quality.addItem(
            tr("safety_dashboard_primer_image_quality_ok"), "ok"
        )
        self.primer_image_quality.addItem(
            tr("safety_dashboard_primer_image_quality_good"), "good"
        )
        primer_image_layout.addRow(
            tr("safety_dashboard_primer_image_quality") + ":", self.primer_image_quality
        )

        self.primer_image_confidence = QComboBox()
        self.primer_image_confidence.addItem(
            tr("safety_dashboard_primer_image_confidence_low"), "low"
        )
        self.primer_image_confidence.addItem(
            tr("safety_dashboard_primer_image_confidence_medium"), "medium"
        )
        self.primer_image_confidence.addItem(
            tr("safety_dashboard_primer_image_confidence_high"), "high"
        )
        primer_image_layout.addRow(
            tr("safety_dashboard_primer_image_confidence") + ":",
            self.primer_image_confidence,
        )

        self.primer_image_observation = QTextEdit()
        self.primer_image_observation.setMaximumHeight(80)
        self.primer_image_observation.setPlaceholderText(
            tr("safety_dashboard_primer_image_observation_placeholder")
        )
        primer_image_layout.addRow(
            tr("safety_dashboard_primer_image_observation") + ":",
            self.primer_image_observation,
        )

        layout.addWidget(primer_image_group)

        evidence_context_group = QGroupBox(
            tr("safety_dashboard_evidence_context_title")
        )
        evidence_context_layout = QFormLayout()
        evidence_context_group.setLayout(evidence_context_layout)

        self.workflow_id = QLineEdit()
        self.workflow_id.setPlaceholderText(
            tr("safety_dashboard_workflow_id_placeholder")
        )
        evidence_context_layout.addRow(
            tr("safety_dashboard_workflow_id") + ":", self.workflow_id
        )

        self.rifle_id = QLineEdit()
        self.rifle_id.setPlaceholderText(tr("safety_dashboard_rifle_id_placeholder"))
        evidence_context_layout.addRow(
            tr("safety_dashboard_rifle_id") + ":", self.rifle_id
        )

        self.barrel_id = QLineEdit()
        self.barrel_id.setPlaceholderText(tr("safety_dashboard_barrel_id_placeholder"))
        evidence_context_layout.addRow(
            tr("safety_dashboard_barrel_id") + ":", self.barrel_id
        )

        self.barrel_name = QLineEdit()
        self.barrel_name.setPlaceholderText(
            tr("safety_dashboard_barrel_name_placeholder")
        )
        evidence_context_layout.addRow(
            tr("safety_dashboard_barrel_name") + ":", self.barrel_name
        )

        self.load_session_id = QLineEdit()
        self.load_session_id.setPlaceholderText(
            tr("safety_dashboard_load_session_id_placeholder")
        )
        evidence_context_layout.addRow(
            tr("safety_dashboard_load_session_id") + ":", self.load_session_id
        )

        self.session_name = QLineEdit()
        self.session_name.setPlaceholderText(
            tr("safety_dashboard_session_name_placeholder")
        )
        evidence_context_layout.addRow(
            tr("safety_dashboard_session_name") + ":", self.session_name
        )

        layout.addWidget(evidence_context_group)

        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText(tr("safety_dashboard_notes_placeholder"))
        layout.addWidget(QLabel(tr("common_notes") + ":"))
        layout.addWidget(self.notes)

        # Knapper
        btn_layout = QHBoxLayout()

        save_btn = QPushButton(tr("btn_save"))
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton(tr("btn_cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def browse_primer_image(self):
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("safety_dashboard_primer_image_path"),
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if image_path:
            self.primer_image_path.setText(image_path)

    def load_ammo_profiles(self):
        """Laster ammunisjonsprofiler"""
        ammos = self.db.execute_query(
            "SELECT id, name FROM ammo_profiles ORDER BY name"
        )
        for ammo_id, name in ammos:
            self.ammo_combo.addItem(name, ammo_id)

    def _apply_context_defaults(self) -> None:
        ammo_profile_id = _resolve_context_ammo_profile_id(self.db, self.context)
        if ammo_profile_id is not None:
            ammo_index = self.ammo_combo.findData(ammo_profile_id)
            if ammo_index >= 0:
                self.ammo_combo.setCurrentIndex(ammo_index)

        workflow_id = self.context.get("workflow_id")
        if workflow_id not in (None, ""):
            self.workflow_id.setText(str(workflow_id))

        rifle_id = self.context.get("rifle_id")
        if rifle_id not in (None, ""):
            self.rifle_id.setText(str(rifle_id))

        barrel_id = str(self.context.get("barrel_id") or "").strip()
        if barrel_id:
            self.barrel_id.setText(barrel_id)

        barrel_name = str(self.context.get("barrel_name") or "").strip()
        if barrel_name:
            self.barrel_name.setText(barrel_name)

        load_session_id = self.context.get("load_session_id")
        if load_session_id not in (None, ""):
            self.load_session_id.setText(str(load_session_id))

        workflow_name = str(self.context.get("workflow_name") or "").strip()
        if workflow_name and not self.session_name.text().strip():
            self.session_name.setText(workflow_name)

    def get_data(self):
        """Returnerer data"""
        return {
            "ammo_id": self.ammo_combo.currentData(),
            "charge_weight": self.charge_weight.value(),
            "flat_primer": self.flat_primer.isChecked(),
            "primer_crater": self.primer_crater.isChecked(),
            "ejector_mark": self.ejector_mark.isChecked(),
            "extractor_mark": self.extractor_mark.isChecked(),
            "heavy_bolt_lift": self.heavy_bolt_lift.isChecked(),
            "velocity_spike": self.velocity_spike.isChecked(),
            "case_head_expansion": (
                self.case_head.value() if self.case_head.value() > 0 else None
            ),
            "primer_image_path": self.primer_image_path.text().strip(),
            "primer_image_quality": self.primer_image_quality.currentData(),
            "primer_image_observation": self.primer_image_observation.toPlainText().strip(),
            "primer_image_confidence": self.primer_image_confidence.currentData(),
            "workflow_id": self.workflow_id.text().strip(),
            "rifle_id": self.rifle_id.text().strip(),
            "barrel_id": self.barrel_id.text().strip(),
            "barrel_name": self.barrel_name.text().strip(),
            "load_session_id": self.load_session_id.text().strip(),
            "session_name": self.session_name.text().strip(),
            "notes": self.notes.toPlainText(),
        }
