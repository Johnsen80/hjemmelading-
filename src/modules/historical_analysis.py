"""
Historical Analysis System
View trends, compare sessions, find patterns
For the shooters who track everything!
"""

import csv
import json
import math
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from HjemmeladingApp.utils import units

from ..database.database import get_database
from ..utils.i18n import tr

EXPORT_SCHEMA_VERSION = "historical_sessions.v1"


def _get_global_unit_system() -> str:
    from PyQt6.QtCore import QSettings

    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return str(settings.value("units/global", "metric") or "metric").strip().lower()


def _format_velocity_fps(value: object, decimals: int = 1) -> str:
    try:
        fps = float(value)
    except Exception:
        return str(value) if value not in (None, "") else "-"
    if _get_global_unit_system() == "imperial":
        return f"{fps:.{decimals}f} fps"
    return f"{units.fps_to_mps(fps):.{decimals}f} m/s ({fps:.{decimals}f} fps)"


def _format_distance_m(value: object) -> str:
    try:
        distance_m = float(value)
    except Exception:
        return str(value) if value not in (None, "") else "-"
    if _get_global_unit_system() == "imperial":
        return f"{units.meters_to_yards(distance_m):.0f} yd ({distance_m:.0f} m)"
    return f"{distance_m:.0f} m"


def _format_velocity_slope_per_day(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    if _get_global_unit_system() == "imperial":
        return f"{value:+.3f} fps/day"
    return f"{units.fps_to_mps(value):+.3f} m/s/day"


def _build_export_metadata(
    export_filters: dict[str, str],
    selection_mode: str,
    exported_at: str,
) -> dict[str, object]:
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "exported_at": exported_at,
        "selection_mode": selection_mode,
        "filters": dict(export_filters),
    }


def _build_export_rows(
    sessions: list[dict[str, Any]],
    export_filters: dict[str, str],
    selection_mode: str,
    exported_at: str,
) -> list[dict[str, Any]]:
    export_rows: list[dict[str, Any]] = []
    for session in sessions:
        row = dict(session)
        import_meta = row.get("import_meta") or {}
        row["export_schema_version"] = EXPORT_SCHEMA_VERSION
        row["audit_source_path"] = import_meta.get("source_path")
        row["audit_raw_sha256"] = import_meta.get("raw_sha256")
        row["exported_at"] = exported_at
        row["export_filter_caliber"] = export_filters["caliber"]
        row["export_filter_powder"] = export_filters["powder"]
        row["export_filter_bullet"] = export_filters["bullet"]
        row["export_filter_project"] = export_filters["project"]
        row["export_filter_date_from"] = export_filters["date_from"]
        row["export_filter_date_to"] = export_filters["date_to"]
        row["export_selection_mode"] = selection_mode
        export_rows.append(row)
    return export_rows


def _build_export_payload(
    sessions: list[dict[str, Any]],
    export_filters: dict[str, str],
    selection_mode: str,
    exported_at: str,
) -> dict[str, object]:
    return {
        "meta": _build_export_metadata(export_filters, selection_mode, exported_at),
        "sessions": _build_export_rows(
            sessions, export_filters, selection_mode, exported_at
        ),
    }


class HistoricalAnalysisViewer(QWidget):
    """
    View and analyze historical load development data
    Find patterns, track improvements, compare sessions
    """

    session_selected = pyqtSignal(str)  # load_id

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.sessions: List[Dict[str, Any]] = []
        self.filtered_sessions: List[Dict[str, Any]] = []
        self.init_ui()
        self.load_sessions()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel(tr("history_title"))
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        # Filters
        filter_group = QGroupBox(tr("history_filters"))
        filter_layout = QHBoxLayout()
        filter_group.setLayout(filter_layout)

        # Caliber filter
        filter_layout.addWidget(QLabel(tr("history_caliber")))
        self.filter_caliber = QComboBox()
        self.filter_caliber.addItem(tr("history_all"))
        self.filter_caliber.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_caliber)

        # Date range
        filter_layout.addWidget(QLabel(tr("history_from")))
        self.filter_date_from = QDateEdit()
        self.filter_date_from.setDate(QDate.currentDate().addDays(-90))
        self.filter_date_from.setCalendarPopup(True)
        self.filter_date_from.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_date_from)

        filter_layout.addWidget(QLabel(tr("history_to")))
        self.filter_date_to = QDateEdit()
        self.filter_date_to.setDate(QDate.currentDate())
        self.filter_date_to.setCalendarPopup(True)
        self.filter_date_to.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_date_to)

        # Powder filter
        filter_layout.addWidget(QLabel(tr("history_powder")))
        self.filter_powder = QComboBox()
        self.filter_powder.addItem(tr("history_all"))
        self.filter_powder.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_powder)

        # Bullet filter
        filter_layout.addWidget(QLabel(tr("history_bullet")))
        self.filter_bullet = QComboBox()
        self.filter_bullet.addItem(tr("history_all"))
        self.filter_bullet.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_bullet)

        # Project filter
        filter_layout.addWidget(QLabel(tr("history_project")))
        self.filter_project = QComboBox()
        self.filter_project.addItem(tr("history_all"))
        self.filter_project.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_project)

        filter_layout.addStretch()

        btn_reset = QPushButton(tr("history_reset_filters"))
        btn_reset.clicked.connect(self.reset_filters)
        filter_layout.addWidget(btn_reset)

        layout.addWidget(filter_group)

        # Main content: Splitter with list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # LEFT: Sessions list
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        left_layout.addWidget(QLabel(tr("history_sessions")))

        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(8)
        self.sessions_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Project",
                "Load ID",
                "Caliber",
                "Powder/Charge",
                "Velocity",
                "SD",
                "MOA",
            ]
        )
        self.sessions_table.currentCellChanged.connect(self.on_session_selected)
        self.sessions_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.sessions_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.sessions_table.setAlternatingRowColors(True)
        left_layout.addWidget(self.sessions_table)

        splitter.addWidget(left_widget)

        # RIGHT: Session details
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        right_layout.addWidget(QLabel(tr("history_session_details")))

        self.detail_tabs = QTabWidget()
        right_layout.addWidget(self.detail_tabs)

        # Tab 1: Summary
        self.tab_summary = QTextEdit()
        self.tab_summary.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_summary, tr("history_summary_tab"))

        # Tab 2: Environmental
        self.tab_environmental = QTextEdit()
        self.tab_environmental.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_environmental, tr("history_environmental_tab"))

        # Tab 3: Components
        self.tab_components = QTextEdit()
        self.tab_components.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_components, tr("history_components_tab"))

        # Tab 4: Results
        self.tab_results = QTextEdit()
        self.tab_results.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_results, tr("history_results_tab"))

        # Tab 5: Notes
        self.tab_notes = QTextEdit()
        self.tab_notes.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_notes, tr("history_notes_tab"))

        # Tab 6: Audit
        self.tab_audit = QTextEdit()
        self.tab_audit.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_audit, tr("history_audit_tab"))

        # Comparison buttons
        btn_layout = QHBoxLayout()

        self.btn_compare = QPushButton(tr("history_compare_selected"))
        self.btn_compare.clicked.connect(self.compare_sessions)
        btn_layout.addWidget(self.btn_compare)

        self.btn_trends = QPushButton(tr("history_show_trends"))
        self.btn_trends.clicked.connect(self.show_trends)
        btn_layout.addWidget(self.btn_trends)

        self.btn_export = QPushButton(tr("history_export_selection"))
        self.btn_export.clicked.connect(self.export_selection)
        btn_layout.addWidget(self.btn_export)

        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)

        # Set splitter sizes
        splitter.setSizes([400, 600])

    def load_sessions(self):
        """Load historical sessions from database"""
        rows = self.db.execute_query(
            """
            SELECT
                cs.id AS session_id,
                cs.session_date,
                cs.session_name,
                cs.device_type,
                cs.avg_velocity_fps,
                cs.sd_fps,
                cs.es_fps,
                cs.min_velocity_fps,
                cs.max_velocity_fps,
                cs.shot_count,
                cs.temperature_f,
                cs.notes,
                cs.import_source,
                cs.import_meta_json,
                cs.created_date,
                ap.id AS ammo_profile_id,
                ap.name AS ammo_name,
                ap.caliber,
                ap.powder_charge,
                ap.bullet_weight,
                p.name AS powder_name,
                b.name AS bullet_name
            FROM chronograph_sessions cs
            LEFT JOIN ammo_profiles ap ON cs.ammo_profile_id = ap.id
            LEFT JOIN powder p ON ap.powder_id = p.id
            LEFT JOIN bullets b ON ap.bullet_id = b.id
            ORDER BY cs.session_date DESC, cs.id DESC
            """
        )

        self.sessions = []
        for row in rows:
            load_id = row.get("session_name") or f"CHRONO-{row.get('session_id')}"
            import_meta = self._parse_json(row.get("import_meta_json"))
            imported_at = import_meta.get("imported_at") or row.get("created_date")
            workspace = import_meta.get("workspace", {})
            if not isinstance(workspace, dict):
                workspace = {}
            project_name = (
                workspace.get("project_name")
                or import_meta.get("project_name")
                or "Default Project"
            )
            uncertainty = self._calc_uncertainty(
                row.get("avg_velocity_fps"),
                row.get("sd_fps"),
                row.get("shot_count"),
            )
            self.sessions.append(
                {
                    "load_id": load_id,
                    "date": row.get("session_date"),
                    "project_name": project_name,
                    "caliber": row.get("caliber") or "-",
                    "powder": row.get("powder_name") or "-",
                    "charge": row.get("powder_charge"),
                    "bullet": row.get("bullet_name") or "-",
                    "velocity": row.get("avg_velocity_fps"),
                    "sd": row.get("sd_fps"),
                    "es": row.get("es_fps"),
                    "moa": None,
                    "notes": row.get("notes") or "",
                    "device_type": row.get("device_type"),
                    "shot_count": row.get("shot_count"),
                    "min_velocity": row.get("min_velocity_fps"),
                    "max_velocity": row.get("max_velocity_fps"),
                    "temperature_f": row.get("temperature_f"),
                    "import_source": row.get("import_source"),
                    "imported_at": imported_at,
                    "import_meta": import_meta,
                    **uncertainty,
                }
            )

        calibers = {s["caliber"] for s in self.sessions if s.get("caliber")}
        powders = {s["powder"] for s in self.sessions if s.get("powder")}
        bullets = {s["bullet"] for s in self.sessions if s.get("bullet")}
        projects = {s["project_name"] for s in self.sessions if s.get("project_name")}

        self.filter_caliber.clear()
        self.filter_caliber.addItem("All")
        self.filter_caliber.addItems(sorted(calibers))

        self.filter_powder.clear()
        self.filter_powder.addItem("All")
        self.filter_powder.addItems(sorted(powders))

        self.filter_bullet.clear()
        self.filter_bullet.addItem("All")
        self.filter_bullet.addItems(sorted(bullets))

        self.filter_project.clear()
        self.filter_project.addItem("All")
        self.filter_project.addItems(sorted(projects))

        self.apply_filters()

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_json(value: Optional[str]) -> Dict[str, Any]:
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
        return {}

    @staticmethod
    def _ci95_multiplier(sample_count: int) -> float:
        df = max(sample_count - 1, 1)
        t_table = {
            1: 12.706,
            2: 4.303,
            3: 3.182,
            4: 2.776,
            5: 2.571,
            6: 2.447,
            7: 2.365,
            8: 2.306,
            9: 2.262,
            10: 2.228,
            11: 2.201,
            12: 2.179,
            13: 2.160,
            14: 2.145,
            15: 2.131,
            16: 2.120,
            17: 2.110,
            18: 2.101,
            19: 2.093,
            20: 2.086,
            21: 2.080,
            22: 2.074,
            23: 2.069,
            24: 2.064,
            25: 2.060,
            26: 2.056,
            27: 2.052,
            28: 2.048,
            29: 2.045,
            30: 2.042,
        }
        return t_table.get(df, 1.96)

    def _calc_uncertainty(
        self, mean: Optional[float], sd: Optional[float], sample_count: Optional[int]
    ) -> Dict[str, Optional[float]]:
        if mean is None or sd is None or not sample_count or sample_count < 2:
            return {
                "velocity_sem": None,
                "velocity_ci95_margin": None,
                "velocity_ci95_low": None,
                "velocity_ci95_high": None,
            }
        sem = sd / math.sqrt(sample_count)
        margin = self._ci95_multiplier(sample_count) * sem
        return {
            "velocity_sem": sem,
            "velocity_ci95_margin": margin,
            "velocity_ci95_low": mean - margin,
            "velocity_ci95_high": mean + margin,
        }

    def apply_filters(self):
        """Apply current filters to sessions list"""
        filtered = self.sessions

        # Filter by caliber
        if self.filter_caliber.currentText() != "All":
            filtered = [
                s for s in filtered if s["caliber"] == self.filter_caliber.currentText()
            ]

        # Filter by powder
        if self.filter_powder.currentText() != "All":
            filtered = [
                s for s in filtered if s["powder"] == self.filter_powder.currentText()
            ]

        # Filter by bullet
        if self.filter_bullet.currentText() != "All":
            filtered = [
                s for s in filtered if s["bullet"] == self.filter_bullet.currentText()
            ]

        # Filter by project
        if self.filter_project.currentText() != "All":
            filtered = [
                s
                for s in filtered
                if s.get("project_name") == self.filter_project.currentText()
            ]

        # Filter by date range
        date_from = self.filter_date_from.date().toPyDate()
        date_to = self.filter_date_to.date().toPyDate()

        filtered_sessions = []
        for session in filtered:
            parsed = self._parse_date(session.get("date"))
            if parsed is None:
                filtered_sessions.append(session)
                continue
            if date_from <= parsed.date() <= date_to:
                filtered_sessions.append(session)

        filtered = filtered_sessions

        self.filtered_sessions = filtered
        self.populate_sessions_table(filtered)

    def populate_sessions_table(self, sessions: List[Dict]):
        """Populate sessions table"""
        self.sessions_table.setRowCount(0)

        for session in sessions:
            row = self.sessions_table.rowCount()
            self.sessions_table.insertRow(row)

            self.sessions_table.setItem(row, 0, QTableWidgetItem(session["date"]))
            self.sessions_table.setItem(
                row, 1, QTableWidgetItem(session.get("project_name", "-"))
            )
            self.sessions_table.setItem(row, 2, QTableWidgetItem(session["load_id"]))
            self.sessions_table.setItem(row, 3, QTableWidgetItem(session["caliber"]))

            charge = session.get("charge")
            if charge is None:
                powder_charge = f"{session['powder']} / -"
            else:
                powder_charge = f"{session['powder']} / {charge:.1f}gr"
            self.sessions_table.setItem(row, 4, QTableWidgetItem(powder_charge))

            velocity = session.get("velocity")
            velocity_text = (
                _format_velocity_fps(velocity) if velocity is not None else "-"
            )
            self.sessions_table.setItem(row, 5, QTableWidgetItem(velocity_text))

            sd_value = session.get("sd")
            sd_item = QTableWidgetItem(
                f"{sd_value:.1f}" if sd_value is not None else "-"
            )
            if sd_value is not None:
                if sd_value < 6:
                    sd_item.setBackground(QColor("#d5f4e6"))  # Green
                elif sd_value < 10:
                    sd_item.setBackground(QColor("#fff9c4"))  # Yellow
                else:
                    sd_item.setBackground(QColor("#ffcccc"))  # Red
            self.sessions_table.setItem(row, 6, sd_item)

            moa_value = session.get("moa")
            moa_item = QTableWidgetItem(
                f"{moa_value:.2f}" if isinstance(moa_value, (int, float)) else "-"
            )
            if isinstance(moa_value, (int, float)):
                if moa_value < 0.75:
                    moa_item.setBackground(QColor("#d5f4e6"))  # Green
                elif moa_value < 1.0:
                    moa_item.setBackground(QColor("#fff9c4"))  # Yellow
                else:
                    moa_item.setBackground(QColor("#ffcccc"))  # Red
            self.sessions_table.setItem(row, 7, moa_item)

        self.sessions_table.resizeColumnsToContents()

    def on_session_selected(self, row, col, prev_row, prev_col):
        """Handle session selection"""
        if row < 0:
            return

        load_id_item = self.sessions_table.item(row, 2)
        if not load_id_item:
            return

        load_id = load_id_item.text()

        # Find session data
        session = next((s for s in self.sessions if s["load_id"] == load_id), None)
        if not session:
            return

        self.display_session_details(session)

    def display_session_details(self, session: Dict):
        """Display detailed session information"""
        # Summary tab
        velocity = session.get("velocity")
        sd_value = session.get("sd")
        es_value = session.get("es")
        moa_value = session.get("moa")
        charge = session.get("charge")
        sem_value = session.get("velocity_sem")
        ci_low = session.get("velocity_ci95_low")
        ci_high = session.get("velocity_ci95_high")

        velocity_text = _format_velocity_fps(velocity) if velocity is not None else "-"
        sd_text = _format_velocity_fps(sd_value) if sd_value is not None else "-"
        es_text = _format_velocity_fps(es_value) if es_value is not None else "-"
        moa_text = (
            f"{moa_value:.2f} MOA" if isinstance(moa_value, (int, float)) else "-"
        )
        sem_text = _format_velocity_fps(sem_value, 2) if sem_value is not None else "-"
        if ci_low is not None and ci_high is not None:
            ci_text = (
                f"{_format_velocity_fps(ci_low)} - {_format_velocity_fps(ci_high)}"
            )
        else:
            ci_text = "-"
        powder_text = session.get("powder") or "-"
        charge_text = f"{charge:.1f} gr" if charge is not None else "-"

        summary_html = f"""
        <h2>{session.get('load_id')}</h2>
        <p><b>Date:</b> {session.get('date', '-')}</p>
        <p><b>Project:</b> {session.get('project_name', '-')}</p>
        <p><b>Caliber:</b> {session.get('caliber', '-')}</p>
        <p><b>Device:</b> {session.get('device_type', '-')}</p>

        <h3>Performance</h3>
        <table border='1' cellpadding='5' style='border-collapse: collapse;'>
            <tr><td><b>Average Velocity</b></td><td>{velocity_text}</td></tr>
            <tr><td><b>Standard Deviation</b></td><td>{sd_text}</td></tr>
            <tr><td><b>Extreme Spread</b></td><td>{es_text}</td></tr>
            <tr><td><b>SEM</b></td><td>{sem_text}</td></tr>
            <tr><td><b>95% CI (mean)</b></td><td>{ci_text}</td></tr>
            <tr><td><b>Accuracy</b></td><td>{moa_text}</td></tr>
        </table>

        <h3>Components</h3>
        <p><b>Powder:</b> {powder_text} @ {charge_text}</p>
        <p><b>Bullet:</b> {session.get('bullet', '-')}</p>
        """
        self.tab_summary.setHtml(summary_html)

        # Environmental tab
        temp_text = (
            f"{session.get('temperature_f')} F"
            if session.get("temperature_f") is not None
            else "-"
        )
        env_text = f"Temperature: {temp_text}\n" "Other environmental data: -"
        self.tab_environmental.setPlainText(env_text)

        # Components tab
        components_text = (
            f"Powder: {powder_text} @ {charge_text}\n"
            f"Bullet: {session.get('bullet', '-')}\n"
            f"Caliber: {session.get('caliber', '-')}"
        )
        self.tab_components.setPlainText(components_text)

        # Results tab
        min_velocity = session.get("min_velocity")
        max_velocity = session.get("max_velocity")
        min_text = (
            _format_velocity_fps(min_velocity) if min_velocity is not None else "-"
        )
        max_text = (
            _format_velocity_fps(max_velocity) if max_velocity is not None else "-"
        )
        results_text = (
            f"Average velocity: {velocity_text}\n"
            f"SD: {sd_text}\n"
            f"ES: {es_text}\n"
            f"Min velocity: {min_text}\n"
            f"Max velocity: {max_text}\n"
            f"Shot count: {session.get('shot_count', '-')}"
        )
        if sem_value is not None:
            results_text += f"\nSEM: {sem_text}"
        if ci_low is not None and ci_high is not None:
            results_text += f"\n95% CI (mean): {ci_text}"
        self.tab_results.setPlainText(results_text)

        # Notes tab
        self.tab_notes.setPlainText(session.get("notes") or "")

        # Audit tab
        import_meta = session.get("import_meta") or {}
        imported_at = (
            import_meta.get("imported_at") or session.get("imported_at") or "-"
        )
        source_file = (
            import_meta.get("source_file") or session.get("import_source") or "-"
        )
        source_path = import_meta.get("source_path")
        raw_hash = import_meta.get("raw_sha256")
        audit_lines = [
            f"Imported at: {imported_at}",
            f"Source file: {source_file}",
            f"Device: {session.get('device_type') or '-'}",
            f"Shot count: {session.get('shot_count') or '-'}",
        ]
        if source_path:
            audit_lines.append(f"Source path: {source_path}")
        if raw_hash:
            audit_lines.append(f"Raw hash (sha256): {raw_hash}")
        self.tab_audit.setPlainText("\n".join(audit_lines))

    def reset_filters(self):
        """Reset all filters"""
        self.filter_caliber.setCurrentIndex(0)
        self.filter_powder.setCurrentIndex(0)
        self.filter_bullet.setCurrentIndex(0)
        self.filter_project.setCurrentIndex(0)
        self.filter_date_from.setDate(QDate.currentDate().addDays(-90))
        self.filter_date_to.setDate(QDate.currentDate())

    def _get_selected_sessions(self) -> List[Dict[str, Any]]:
        selected = self.sessions_table.selectionModel().selectedRows()
        if not selected:
            return []
        row_indices = sorted({idx.row() for idx in selected})
        sessions = []
        for row in row_indices:
            load_id_item = self.sessions_table.item(row, 2)
            if not load_id_item:
                continue
            load_id = load_id_item.text()
            session = next((s for s in self.sessions if s["load_id"] == load_id), None)
            if session:
                sessions.append(session)
        return sessions

    @staticmethod
    def _format_value(value: Any, precision: int = 1, suffix: str = "") -> str:
        if value is None:
            return "-"
        if isinstance(value, (int, float)):
            return f"{value:.{precision}f}{suffix}"
        return str(value)

    @staticmethod
    def _linear_slope(xs: List[float], ys: List[float]) -> Optional[float]:
        if len(xs) < 2 or len(ys) < 2:
            return None
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        denom = sum((x - mean_x) ** 2 for x in xs)
        if denom == 0:
            return None
        return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom

    def compare_sessions(self):
        """Compare multiple selected sessions"""
        from PyQt6.QtWidgets import QMessageBox

        sessions = self._get_selected_sessions()
        if not sessions:
            QMessageBox.information(
                self,
                tr("history_compare_dialog"),
                tr("history_select_sessions"),
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("history_compare_dialog"))
        dialog.resize(900, 480)
        layout = QVBoxLayout(dialog)

        summary = QLabel(dialog)
        summary.setWordWrap(True)

        best_sd = min(
            (s for s in sessions if s.get("sd") is not None),
            key=lambda s: s.get("sd"),
            default=None,
        )
        best_es = min(
            (s for s in sessions if s.get("es") is not None),
            key=lambda s: s.get("es"),
            default=None,
        )
        best_velocity = max(
            (s for s in sessions if s.get("velocity") is not None),
            key=lambda s: s.get("velocity"),
            default=None,
        )
        best_ci = min(
            (s for s in sessions if s.get("velocity_ci95_margin") is not None),
            key=lambda s: s.get("velocity_ci95_margin"),
            default=None,
        )

        summary_lines = [tr("history_quick_comparison")]
        if best_sd:
            summary_lines.append(
                f"{tr('history_best_sd')}: {best_sd['load_id']} ({_format_velocity_fps(best_sd.get('sd'))})"
            )
        if best_es:
            summary_lines.append(
                f"{tr('history_best_es')}: {best_es['load_id']} ({_format_velocity_fps(best_es.get('es'))})"
            )
        if best_velocity:
            summary_lines.append(
                f"{tr('history_highest_velocity')}: {best_velocity['load_id']} ({_format_velocity_fps(best_velocity.get('velocity'))})"
            )
        if best_ci:
            summary_lines.append(
                f"{tr('history_tightest_ci')}: "
                f"{best_ci['load_id']} ({_format_velocity_fps(best_ci.get('velocity_ci95_margin'))})"
            )
        summary.setText("\n".join(summary_lines))
        layout.addWidget(summary)

        table = QTableWidget(dialog)
        table.setColumnCount(12)
        table.setHorizontalHeaderLabels(
            [
                "Load ID",
                "Date",
                "Caliber",
                "Powder/Charge",
                "Bullet",
                "Avg Vel",
                "SD",
                "ES",
                "SEM",
                "CI95 +/-",
                "Shots",
                "Temp (F)",
            ]
        )
        table.setRowCount(len(sessions))
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)

        for row, session in enumerate(sessions):
            charge = session.get("charge")
            powder = session.get("powder") or "-"
            powder_charge = (
                f"{powder} / {charge:.1f}gr" if charge is not None else f"{powder} / -"
            )
            table.setItem(row, 0, QTableWidgetItem(session.get("load_id", "-")))
            table.setItem(row, 1, QTableWidgetItem(session.get("date", "-")))
            table.setItem(row, 2, QTableWidgetItem(session.get("caliber", "-")))
            table.setItem(row, 3, QTableWidgetItem(powder_charge))
            table.setItem(row, 4, QTableWidgetItem(session.get("bullet", "-")))
            table.setItem(
                row, 5, QTableWidgetItem(_format_velocity_fps(session.get("velocity")))
            )
            table.setItem(
                row, 6, QTableWidgetItem(_format_velocity_fps(session.get("sd")))
            )
            table.setItem(
                row, 7, QTableWidgetItem(_format_velocity_fps(session.get("es")))
            )
            table.setItem(
                row,
                8,
                QTableWidgetItem(_format_velocity_fps(session.get("velocity_sem"), 2)),
            )
            table.setItem(
                row,
                9,
                QTableWidgetItem(
                    _format_velocity_fps(session.get("velocity_ci95_margin"), 2)
                ),
            )
            table.setItem(
                row, 10, QTableWidgetItem(str(session.get("shot_count", "-")))
            )
            table.setItem(
                row,
                11,
                QTableWidgetItem(self._format_value(session.get("temperature_f"), 1)),
            )

        table.resizeColumnsToContents()
        layout.addWidget(table)

        dialog.exec()

    def show_trends(self):
        """Show trends over time"""
        from PyQt6.QtWidgets import QMessageBox

        sessions = self.filtered_sessions or self.sessions
        sessions = [s for s in sessions if self._parse_date(s.get("date"))]
        if len(sessions) < 2:
            QMessageBox.information(
                self,
                tr("history_trends_dialog"),
                tr("history_not_enough_trends"),
            )
            return

        sessions.sort(key=lambda s: self._parse_date(s.get("date")) or datetime.min)

        velocity_points = [
            (s, s.get("velocity")) for s in sessions if s.get("velocity") is not None
        ]
        sd_points = [(s, s.get("sd")) for s in sessions if s.get("sd") is not None]
        es_points = [(s, s.get("es")) for s in sessions if s.get("es") is not None]
        moa_points = [(s, s.get("moa")) for s in sessions if s.get("moa") is not None]

        def slope_for(points: List[tuple[Dict[str, Any], Any]]) -> Optional[float]:
            if len(points) < 2:
                return None
            ys = [p[1] for p in points if isinstance(p[1], (int, float))]
            xs_local = [
                (self._parse_date(p[0].get("date")) or datetime.min).toordinal()
                for p in points
            ]
            return self._linear_slope(xs_local, ys)

        velocity_slope = slope_for(velocity_points)
        sd_slope = slope_for(sd_points)
        es_slope = slope_for(es_points)
        moa_slope = slope_for(moa_points)

        powder_counts = Counter(
            s.get("powder") for s in sessions if s.get("powder") not in (None, "-")
        )
        bullet_counts = Counter(
            s.get("bullet") for s in sessions if s.get("bullet") not in (None, "-")
        )
        caliber_counts = Counter(
            s.get("caliber") for s in sessions if s.get("caliber") not in (None, "-")
        )

        def top_counts(counter: Counter) -> str:
            if not counter:
                return "-"
            return ", ".join(
                f"{name} ({count})" for name, count in counter.most_common(3)
            )

        def _trend_line(value: Optional[float], suffix: str) -> str:
            if value is None:
                return "N/A"
            return f"{value:+.3f}{suffix}"

        summary_lines = [
            tr("history_trends_summary"),
            f"{tr('history_velocity_trend')}: {_format_velocity_slope_per_day(velocity_slope)}",
            f"{tr('history_sd_trend')}: {_format_velocity_slope_per_day(sd_slope)}",
            f"{tr('history_es_trend')}: {_format_velocity_slope_per_day(es_slope)}",
            f"{tr('history_accuracy_trend')}: {_trend_line(moa_slope, ' MOA/day')}",
            f"{tr('history_most_used_powders')}: {top_counts(powder_counts)}",
            f"{tr('history_most_used_bullets')}: {top_counts(bullet_counts)}",
            f"{tr('history_most_used_calibers')}: {top_counts(caliber_counts)}",
        ]

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("history_trends_dialog"))
        dialog.resize(900, 600)
        layout = QVBoxLayout(dialog)

        summary_box = QTextEdit(dialog)
        summary_box.setReadOnly(True)
        summary_box.setMaximumHeight(180)
        summary_box.setPlainText("\n".join(summary_lines))
        layout.addWidget(summary_box)

        table = QTableWidget(dialog)
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["Date", "Load ID", "Velocity", "SD", "ES", "Shots", "Temp (F)"]
        )
        table.setRowCount(len(sessions))
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)

        for row, session in enumerate(sessions):
            table.setItem(row, 0, QTableWidgetItem(session.get("date", "-")))
            table.setItem(row, 1, QTableWidgetItem(session.get("load_id", "-")))
            table.setItem(
                row,
                2,
                QTableWidgetItem(
                    self._format_value(session.get("velocity"), 1, " fps")
                ),
            )
            table.setItem(
                row, 3, QTableWidgetItem(self._format_value(session.get("sd"), 1))
            )
            table.setItem(
                row, 4, QTableWidgetItem(self._format_value(session.get("es"), 1))
            )
            table.setItem(row, 5, QTableWidgetItem(str(session.get("shot_count", "-"))))
            table.setItem(
                row,
                6,
                QTableWidgetItem(self._format_value(session.get("temperature_f"), 1)),
            )

        table.resizeColumnsToContents()
        layout.addWidget(table)

        dialog.exec()

    def export_selection(self):
        """Export selected sessions"""
        from PyQt6.QtWidgets import QMessageBox

        sessions = self._get_selected_sessions()
        selection_mode = "selected" if sessions else "filtered"
        if not sessions:
            sessions = self.filtered_sessions or self.sessions

        if not sessions:
            QMessageBox.information(
                self, tr("history_export"), tr("history_no_sessions_to_export")
            )
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            tr("history_export_sessions"),
            "",
            "CSV Files (*.csv);;JSON Files (*.json)",
        )

        if not file_path:
            return

        export_filters = {
            "caliber": self.filter_caliber.currentText(),
            "powder": self.filter_powder.currentText(),
            "bullet": self.filter_bullet.currentText(),
            "project": self.filter_project.currentText(),
            "date_from": self.filter_date_from.date().toString("yyyy-MM-dd"),
            "date_to": self.filter_date_to.date().toString("yyyy-MM-dd"),
        }
        exported_at = datetime.now().isoformat(timespec="seconds")
        export_rows = _build_export_rows(
            sessions, export_filters, selection_mode, exported_at
        )

        if selected_filter.startswith("JSON") or file_path.lower().endswith(".json"):
            if not file_path.lower().endswith(".json"):
                file_path += ".json"
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(
                        _build_export_payload(
                            sessions, export_filters, selection_mode, exported_at
                        ),
                        f,
                        indent=2,
                        ensure_ascii=False,
                    )
            except Exception as exc:
                QMessageBox.critical(
                    self,
                    tr("history_export"),
                    tr("history_export_failed", error=str(exc)),
                )
                return
        else:
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    fieldnames = [
                        "export_schema_version",
                        "date",
                        "load_id",
                        "caliber",
                        "powder",
                        "charge",
                        "bullet",
                        "velocity",
                        "sd",
                        "es",
                        "min_velocity",
                        "max_velocity",
                        "shot_count",
                        "temperature_f",
                        "notes",
                        "device_type",
                        "velocity_sem",
                        "velocity_ci95_low",
                        "velocity_ci95_high",
                        "velocity_ci95_margin",
                        "imported_at",
                        "import_source",
                        "audit_source_path",
                        "audit_raw_sha256",
                        "exported_at",
                        "export_filter_caliber",
                        "export_filter_powder",
                        "export_filter_bullet",
                        "export_filter_project",
                        "export_filter_date_from",
                        "export_filter_date_to",
                        "export_selection_mode",
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in export_rows:
                        writer.writerow({k: row.get(k) for k in fieldnames})
            except Exception as exc:
                QMessageBox.critical(
                    self,
                    tr("history_export"),
                    tr("history_export_failed", error=str(exc)),
                )
                return

        QMessageBox.information(
            self, tr("history_export"), tr("history_export_completed")
        )


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    viewer = HistoricalAnalysisViewer()
    viewer.show()
    viewer.resize(1200, 700)

    sys.exit(app.exec())
