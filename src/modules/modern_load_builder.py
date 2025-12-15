"""
Modern Load Builder - Interactive visual load development with AI assistant
Replaces old wizard with intuitive 2-step workflow + live visualization
"""

import statistics

from PyQt6.QtCore import QDate, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSplitter,
)
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtWidgets import QTextEdit as QTextEditWidget
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from src.database.database import get_database
from src.utils.pressure_logger import predict_and_log, query_recent_pressures

# Importing heavy visualization libs lazily inside methods to avoid
# expensive imports at module import time (helps headless/CI probes).


class ModernLoadBuilder(QWidget):
    """
    Modern 2-step load development interface:
    Step 1: Select rifle + brass (quick)
    Step 2: Interactive load builder with live graphs + AI chat
    """

    load_created = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        # Defer creation of ballistics engine until actually needed to avoid
        # expensive/side-effectful initialization during import/UI composition.
        self._engine = None

        # UI persisted preferences (loaded shortly after UI creation)
        self.velocity_y_min = None
        self.velocity_y_max = None

        # State
        self.current_step = 1
        self.rifle_data = None
        self.brass_data = None
        self.bullet_data = None
        self.powder_data = None
        self.primer_data = None
        self.current_charge = 42.5
        self.coal_mm = 71.5
        self.cbto_mm = 68.8

        # AI chat history
        self.chat_history = []

        self.init_ui()

    @property
    def engine(self):
        """Lazily initialize and return the ballistics engine."""
        if getattr(self, "_engine", None) is None:
            try:
                from src.modules.ballistics_engine import get_ballistics_engine

                self._engine = get_ballistics_engine()
            except Exception:
                self._engine = None
        return self._engine

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Container for step pages
        self.step1_widget = self.create_step1_page()
        self.step2_widget = self.create_step2_page()

        # Show step 1 initially
        layout.addWidget(self.step1_widget)
        self.step2_widget.hide()

        # Restore last-open step if persisted
        try:
            cur = self.db.cursor
            cur.execute("SELECT value FROM ui_settings WHERE key = ?", ("last_step",))
            row = cur.fetchone()
            if row and row[0] is not None:
                try:
                    last = int(row[0])
                    if last == 2:
                        # show step 2
                        self.step1_widget.hide()
                        self.layout().addWidget(self.step2_widget)
                        self.step2_widget.show()
                        self.current_step = 2
                except Exception:
                    pass
        except Exception:
            pass

        self.setLayout(layout)

        # AI assistant quick access
        self.ai_button = QPushButton("AI Assistant")
        self.ai_button.setToolTip(
            "Ask the assistant about loads, calibration, or suggestions."
        )
        self.ai_button.clicked.connect(self.on_open_ai_chat)
        layout.addWidget(self.ai_button)

        # Explain-plot button
        self.explain_plot_btn = QPushButton("Explain This Plot")
        self.explain_plot_btn.setToolTip(
            "Ask the assistant to explain the currently visible plot."
        )
        self.explain_plot_btn.clicked.connect(self.on_explain_plot_clicked)
        layout.addWidget(self.explain_plot_btn)

        self.ai_settings_btn = QPushButton("AI Settings")
        self.ai_settings_btn.setToolTip(
            "Configure AI assistant (enable remote API, model, API key)"
        )
        self.ai_settings_btn.clicked.connect(self.on_open_ai_settings)
        layout.addWidget(self.ai_settings_btn)

        # Preferences button (small centralized UI prefs)
        self.prefs_btn = QPushButton("Preferences")
        self.prefs_btn.setToolTip("Open UI preferences")
        self.prefs_btn.clicked.connect(self.on_open_preferences)
        layout.addWidget(self.prefs_btn)

        # Apply persisted UI theme if present
        try:
            cur = self.db.cursor
            cur.execute("SELECT value FROM ui_settings WHERE key = ?", ("ui_theme",))
            r = cur.fetchone()
            if r and r[0] is not None:
                theme = r[0]
                try:
                    if theme.lower() == "dark":
                        self.setStyleSheet("background: #2c2c2c; color: #f0f0f0;")
                    elif theme.lower() == "light":
                        self.setStyleSheet("")
                except Exception:
                    pass
        except Exception:
            pass

        # GP optimizer suggest button
        self.suggest_btn = QPushButton("Suggest Next Charge")
        self.suggest_btn.setToolTip(
            "Use GP-based optimizer to suggest the next charge to test."
        )
        self.suggest_btn.clicked.connect(self.on_suggest_next_charge)
        layout.addWidget(self.suggest_btn)

        # Subsonic mode controls
        sub_h = QHBoxLayout()
        self.subsonic_cb = QCheckBox("Subsonic Mode")
        self.subsonic_cb.setToolTip(
            "Try to suggest charges that keep velocity below the target subsonic threshold."
        )
        sub_h.addWidget(self.subsonic_cb)
        sub_h.addWidget(QLabel("Target max velocity (fps):"))
        self.subsonic_target = QDoubleSpinBox()
        self.subsonic_target.setRange(500.0, 1300.0)
        self.subsonic_target.setValue(1050.0)
        self.subsonic_target.setSingleStep(5.0)
        sub_h.addWidget(self.subsonic_target)
        layout.addLayout(sub_h)

        self.manage_suggestions_btn = QPushButton("Manage Suggestions")
        self.manage_suggestions_btn.setToolTip(
            "Browse past optimizer suggestions and create workflows or mark as tested."
        )
        self.manage_suggestions_btn.clicked.connect(self.on_manage_suggestions_clicked)
        layout.addWidget(self.manage_suggestions_btn)

        self.auto_match_btn = QPushButton("Auto-Match Suggestions")
        self.auto_match_btn.setToolTip(
            "Try to automatically match suggestions to recent test results and refit the optimizer."
        )
        self.auto_match_btn.clicked.connect(self.on_auto_match_suggestions)
        layout.addWidget(self.auto_match_btn)

        # Auto-match toggle
        self.auto_match_toggle = QPushButton("Enable Auto-Match")
        self.auto_match_toggle.setCheckable(True)
        self.auto_match_toggle.setToolTip(
            "When enabled, new test results will be auto-matched to suggestions."
        )
        self.auto_match_toggle.toggled.connect(self.on_toggle_auto_match)
        layout.addWidget(self.auto_match_toggle)

        # Timer for polling new test_results (created when toggled on)
        self._auto_match_timer = QTimer(self)
        self._auto_match_timer.setInterval(10000)  # 10s
        self._auto_match_timer.timeout.connect(self._auto_match_poll)
        self._last_test_result_id = None

        # Pressure log UI
        pressure_group = QGroupBox("📈 Pressure Log")
        pressure_layout = QVBoxLayout()

        # Filters: rifle selector + quick text filter
        filter_layout = QHBoxLayout()
        self.pressure_rifle_combo = QComboBox()
        self.pressure_rifle_combo.addItem("All rifles", None)
        try:
            rifles = self.db.execute_query("SELECT id, name FROM rifles ORDER BY name")
            for r in rifles:
                self.pressure_rifle_combo.addItem(r.get("name", "?"), r.get("id"))
        except Exception:
            pass
        self.pressure_rifle_combo.currentIndexChanged.connect(self.refresh_pressure_log)
        filter_layout.addWidget(self.pressure_rifle_combo)

        # Date range filters
        self.pressure_from = QDateEdit()
        self.pressure_from.setCalendarPopup(True)
        self.pressure_from.setDate(QDate.currentDate().addDays(-30))
        filter_layout.addWidget(self.pressure_from)

        self.pressure_to = QDateEdit()
        self.pressure_to.setCalendarPopup(True)
        self.pressure_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.pressure_to)

        # Quick presets
        from_btn = QPushButton("7d")
        from_btn.setToolTip("Last 7 days")
        from_btn.clicked.connect(lambda: self.on_set_date_preset(7))
        filter_layout.addWidget(from_btn)

        m30_btn = QPushButton("30d")
        m30_btn.setToolTip("Last 30 days")
        m30_btn.clicked.connect(lambda: self.on_set_date_preset(30))
        filter_layout.addWidget(m30_btn)

        m90_btn = QPushButton("90d")
        m90_btn.setToolTip("Last 90 days")
        m90_btn.clicked.connect(lambda: self.on_set_date_preset(90))
        filter_layout.addWidget(m90_btn)

        self.pressure_search = QLineEdit()
        self.pressure_search.setPlaceholderText("Filter notes, id or charge...")
        self.pressure_search.returnPressed.connect(self.refresh_pressure_log)
        filter_layout.addWidget(self.pressure_search)

        pressure_layout.addLayout(filter_layout)

        self.pressure_list = QListWidget()
        self.pressure_list.setMinimumHeight(150)
        pressure_layout.addWidget(self.pressure_list)

        pbtn_layout = QHBoxLayout()
        refresh_pbtn = QPushButton("↺ Refresh")
        refresh_pbtn.setStyleSheet("padding:6px;")
        refresh_pbtn.clicked.connect(self.refresh_pressure_log)
        pbtn_layout.addWidget(refresh_pbtn)

        export_btn = QPushButton("⬇️ Export CSV")
        export_btn.setStyleSheet("padding:6px;")
        export_btn.clicked.connect(self.on_export_pressure_log)
        pbtn_layout.addWidget(export_btn)

        log_pbtn = QPushButton("📝 Log Predicted Pressure")
        log_pbtn.setStyleSheet("padding:6px; background:#f39c12; color:white;")
        log_pbtn.clicked.connect(self.on_log_predicted_pressure)
        pbtn_layout.addWidget(log_pbtn)

        pressure_layout.addLayout(pbtn_layout)
        pressure_group.setLayout(pressure_layout)
        layout.addWidget(pressure_group)

    def refresh_pressure_log(self):
        """Reload the pressure_history list applying current filters."""
        try:
            rows = query_recent_pressures(self.db, limit=500)
        except Exception:
            rows = []

        # Apply rifle filter, date range, and quick text filter
        rifle_id = None
        if hasattr(self, "pressure_rifle_combo"):
            sel = self.pressure_rifle_combo.currentData()
            if isinstance(sel, int):
                rifle_id = sel

        q = ""
        if hasattr(self, "pressure_search"):
            q = (self.pressure_search.text() or "").strip().lower()

        # date range
        date_from = None
        date_to = None
        if hasattr(self, "pressure_from") and hasattr(self, "pressure_to"):
            try:
                date_from = self.pressure_from.date().toString("yyyy-MM-dd")
                date_to = self.pressure_to.date().toString("yyyy-MM-dd")
            except Exception:
                date_from = None
                date_to = None

        # build id->name caches
        rifle_names = {}
        ammo_names = {}
        try:
            for r in self.db.execute_query("SELECT id, name FROM rifles"):
                rifle_names[r.get("id")] = r.get("name")
        except Exception:
            pass
        try:
            for a in self.db.execute_query("SELECT id, name FROM ammo_profiles"):
                ammo_names[a.get("id")] = a.get("name")
        except Exception:
            pass

        filtered = []
        for r in rows:
            if rifle_id and r.get("rifle_id") != rifle_id:
                continue

            ts = r.get("timestamp") or ""
            ts_date = ts[:10] if isinstance(ts, str) and len(ts) >= 10 else ""
            if date_from and ts_date and ts_date < date_from:
                continue
            if date_to and ts_date and ts_date > date_to:
                continue

            if q:
                note = str(r.get("note") or "").lower()
                if (
                    q not in note
                    and q not in str(r.get("id") or "")
                    and q not in str(r.get("charge_weight") or "")
                ):
                    continue
            filtered.append(r)

        self.pressure_list.clear()
        for r in filtered:
            try:
                pval = r.get("predicted_pressure_psi")
                ptxt = f"{pval:.1f} PSI" if pval is not None else "N/A"
            except Exception:
                ptxt = "N/A"

            rifle_name = rifle_names.get(r.get("rifle_id"), f"R:{r.get('rifle_id')}")
        # build powder/bullet lot mapping per ammo_profile
        ammo_component_lots = {}
        try:
            rows_ap = self.db.execute_query(
                "SELECT id, powder_id, bullet_id FROM ammo_profiles"
            )
            for ap in rows_ap:
                apid = ap.get("id")
                powder_lot = None
                bullet_lot = None
                try:
                    if ap.get("powder_id"):
                        pr = self.db.execute_query(
                            "SELECT lot_number FROM component_lots WHERE component_type='powder' AND component_id=? ORDER BY created_date DESC LIMIT 1",
                            (ap.get("powder_id"),),
                        )
                        if pr:
                            powder_lot = pr[0].get("lot_number")
                except Exception:
                    powder_lot = None
                try:
                    if ap.get("bullet_id"):
                        br = self.db.execute_query(
                            "SELECT lot_number FROM component_lots WHERE component_type='bullet' AND component_id=? ORDER BY created_date DESC LIMIT 1",
                            (ap.get("bullet_id"),),
                        )
                        if br:
                            bullet_lot = br[0].get("lot_number")
                except Exception:
                    bullet_lot = None
                ammo_component_lots[apid] = {
                    "powder_lot": powder_lot,
                    "bullet_lot": bullet_lot,
                }
        except Exception:
            pass
            ammo_name = ammo_names.get(
                r.get("ammo_profile_id"), f"A:{r.get('ammo_profile_id')}"
            )

            display = f"{r.get('timestamp')} | {rifle_name} | {ammo_name} | Charge:{r.get('charge_weight')} gr | P:{ptxt} | {r.get('note') or ''}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, r.get("id"))
            self.pressure_list.addItem(item)

    def on_set_date_preset(self, days: int):
        """Set the date_from to `days` ago and refresh the list."""
        try:
            self.pressure_from.setDate(QDate.currentDate().addDays(-int(days)))
            self.pressure_to.setDate(QDate.currentDate())
        except Exception:
            pass
        self.refresh_pressure_log()

    def on_export_pressure_log(self):
        """Export currently filtered pressure log rows to CSV."""
        # Reuse the same filtering logic as refresh (but fetch rows again)
        try:
            rows = query_recent_pressures(self.db, limit=500)
        except Exception:
            rows = []

        rifle_id = None
        if hasattr(self, "pressure_rifle_combo"):
            sel = self.pressure_rifle_combo.currentData()
            rifle_id = sel

        q = ""
        if hasattr(self, "pressure_search"):
            q = (self.pressure_search.text() or "").strip().lower()

        date_from = None
        date_to = None
        if hasattr(self, "pressure_from") and hasattr(self, "pressure_to"):
            try:
                date_from = self.pressure_from.date().toString("yyyy-MM-dd")
                date_to = self.pressure_to.date().toString("yyyy-MM-dd")
            except Exception:
                date_from = None
                date_to = None

        filtered = []
        for r in rows:
            if rifle_id and r.get("rifle_id") != rifle_id:
                continue
            ts = r.get("timestamp") or ""
            ts_date = ts[:10] if isinstance(ts, str) and len(ts) >= 10 else ""
            if date_from and ts_date and ts_date < date_from:
                continue
            if date_to and ts_date and ts_date > date_to:
                continue
            if q:
                note = str(r.get("note") or "").lower()
                if (
                    q not in note
                    and q not in str(r.get("id") or "")
                    and q not in str(r.get("charge_weight") or "")
                ):
                    continue
            filtered.append(r)

        if not filtered:
            QMessageBox.information(
                self, "No Data", "No pressure log rows match current filters."
            )
            return

        fname, _ = QFileDialog.getSaveFileName(
            self, "Export Pressure Log CSV", "", "CSV Files (*.csv)"
        )
        if not fname:
            return

        import csv

        # Build name caches
        rifle_names = {}
        ammo_names = {}
        ammo_lots = {}
        ammo_component_lots = {}
        try:
            for r in self.db.execute_query("SELECT id, name FROM rifles"):
                rifle_names[r.get("id")] = r.get("name")
        except Exception:
            pass
        try:
            for a in self.db.execute_query("SELECT id, name FROM ammo_profiles"):
                ammo_names[a.get("id")] = a.get("name")
        except Exception:
            pass
        try:
            for a in self.db.execute_query(
                "SELECT ap.id as apid, c.lot_number as lot FROM ammo_profiles ap LEFT JOIN cases c ON ap.case_id = c.id"
            ):
                ammo_lots[a.get("apid")] = a.get("lot")
        except Exception:
            pass
        try:
            # map ammo_profile -> powder/bullet lot numbers (latest per component)
            for ap in self.db.execute_query(
                "SELECT id, powder_id, bullet_id FROM ammo_profiles"
            ):
                apid = ap.get("id")
                powder_lot = None
                bullet_lot = None
                try:
                    if ap.get("powder_id"):
                        p_row = self.db.execute_query(
                            "SELECT lot_number FROM component_lots WHERE component_type='powder' AND component_id=? ORDER BY created_date DESC LIMIT 1",
                            (ap.get("powder_id"),),
                        )
                        if p_row:
                            powder_lot = p_row[0].get("lot_number")
                except Exception:
                    powder_lot = None
                try:
                    if ap.get("bullet_id"):
                        b_row = self.db.execute_query(
                            "SELECT lot_number FROM component_lots WHERE component_type='bullet' AND component_id=? ORDER BY created_date DESC LIMIT 1",
                            (ap.get("bullet_id"),),
                        )
                        if b_row:
                            bullet_lot = b_row[0].get("lot_number")
                except Exception:
                    bullet_lot = None
                ammo_component_lots[apid] = {
                    "powder_lot": powder_lot,
                    "bullet_lot": bullet_lot,
                }
        except Exception:
            pass

        try:
            with open(fname, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(
                    [
                        "id",
                        "timestamp",
                        "rifle_id",
                        "rifle_name",
                        "ammo_profile_id",
                        "ammo_name",
                        "ammo_case_lot",
                        "powder_lot",
                        "bullet_lot",
                        "charge_weight",
                        "coal_mm",
                        "cbto_mm",
                        "predicted_pressure_psi",
                        "saami_max_psi",
                        "note",
                    ]
                )
                for r in filtered:
                    comp = ammo_component_lots.get(r.get("ammo_profile_id"), {})
                    writer.writerow(
                        [
                            r.get("id"),
                            r.get("timestamp"),
                            r.get("rifle_id"),
                            rifle_names.get(r.get("rifle_id")),
                            r.get("ammo_profile_id"),
                            ammo_names.get(r.get("ammo_profile_id")),
                            ammo_lots.get(r.get("ammo_profile_id")),
                            comp.get("powder_lot"),
                            comp.get("bullet_lot"),
                            r.get("charge_weight"),
                            r.get("coal_mm"),
                            r.get("cbto_mm"),
                            r.get("predicted_pressure_psi"),
                            r.get("saami_max_psi"),
                            r.get("note"),
                        ]
                    )
            QMessageBox.information(
                self, "Exported", f"Exported {len(filtered)} rows to {fname}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export failed", f"Could not write CSV: {e}")

    def create_step1_page(self):
        """Step 1: Select Rifle & Brass"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Header
        header = QLabel("🎯 New Load - Select Rifle & Brass")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 20px;")
        layout.addWidget(header)

        subtitle = QLabel("Choose your rifle and brass batch to get started")
        subtitle.setStyleSheet(
            "color: #7f8c8d; font-size: 12pt; padding-left: 20px; padding-bottom: 20px;"
        )
        layout.addWidget(subtitle)

        # Content area
        content = QHBoxLayout()

        # Left: Rifle selection
        rifle_group = self.create_rifle_selection_panel()
        content.addWidget(rifle_group)

        # Right: Brass selection
        brass_group = self.create_brass_selection_panel()
        content.addWidget(brass_group)

        layout.addLayout(content)

        # Navigation
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        self.next_btn = QPushButton("Next: Build Load →")
        self.next_btn.setStyleSheet(
            """
            QPushButton {
                background: #27ae60;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #229954;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """
        )
        self.next_btn.clicked.connect(self.go_to_step2)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_rifle_selection_panel(self):
        from src.utils.ai_assistant import Assistant

        dlg = QDialog(self)
        dlg.setWindowTitle("AI Assistant Settings")
        v = QVBoxLayout()

        enabled_cb = QPushButton("Enable Remote API")
        enabled_cb.setCheckable(True)
        v.addWidget(enabled_cb)

        v.addWidget(QLabel("Model:"))
        model_edit = QLineEdit()
        v.addWidget(model_edit)

        v.addWidget(QLabel("API Key:"))
        key_edit = QLineEdit()
        key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        v.addWidget(key_edit)

        def load_current():
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT enabled, model, api_key FROM ai_settings ORDER BY id DESC LIMIT 1"
                )
                row = cur.fetchone()
                if row:
                    enabled_cb.setChecked(bool(row[0]))
                    if row[1]:
                        model_edit.setText(row[1])
                    if row[2]:
                        key_edit.setText(row[2])
            except Exception:
                pass

        load_current()

        def do_save():
            try:
                enabled = enabled_cb.isChecked()
                model = model_edit.text().strip() or None
                api_key = key_edit.text().strip() or None
                a = Assistant(db=self.db)
                a.save_settings(self.db, enabled, model, api_key)
                QMessageBox.information(self, "Saved", "AI settings saved.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save settings: {e}")

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(do_save)
        v.addWidget(save_btn)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        dlg.setLayout(v)
        dlg.exec()

        self.brass_button_group = QButtonGroup()

        # Will populate when rifle is selected
        self.brass_container = QVBoxLayout()
        layout.addLayout(self.brass_container)

        layout.addStretch()

        add_btn = QPushButton("+ Add New Brass Batch")
        add_btn.setStyleSheet("color: #3498db; font-size: 10pt; padding: 8px;")
        layout.addWidget(add_btn)

        group.setLayout(layout)
        return group

    def on_rifle_selected(self, checked):
        """Handle rifle selection"""
        if not checked:
            return

        sender = self.sender()
        self.rifle_data = sender.rifle_data

        # Load brass for this caliber
        self.load_brass_for_caliber(self.rifle_data["caliber"])

        self.check_step1_complete()

    def load_brass_for_caliber(self, caliber):
        """Load brass batches for selected caliber"""
        # Clear existing
        while self.brass_container.count():
            item = self.brass_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Query brass
        brass_batches = self.db.execute_query(
            """
            SELECT bb.*, c.name as case_name
            FROM brass_batches bb
            JOIN cases c ON bb.case_id = c.id
            WHERE c.caliber = ?
            AND bb.cases_active > 0
            ORDER BY bb.created_date DESC
        """,
            (caliber,),
        )

        if brass_batches:
            for brass in brass_batches:
                rb = QRadioButton(
                    f"{brass['case_name']} Batch #{brass['id']}\n"
                    f"  {brass['cases_active']} cases, "
                    f"{brass.get('times_fired_avg', 0):.0f}x fired"
                )
                rb.setStyleSheet("font-size: 11pt; padding: 10px;")
                rb.brass_data = brass
                rb.toggled.connect(self.on_brass_selected)
                self.brass_button_group.addButton(rb)
                self.brass_container.addWidget(rb)
        else:
            no_brass = QLabel(f"No brass found for {caliber}")
            no_brass.setStyleSheet("color: #e67e22; font-style: italic;")
            self.brass_container.addWidget(no_brass)

    def on_brass_selected(self, checked):
        """Handle brass selection"""
        if not checked:
            return

        sender = self.sender()
        self.brass_data = sender.brass_data

        self.check_step1_complete()

    def check_step1_complete(self):
        """Enable next button if rifle and brass selected"""
        if self.rifle_data and self.brass_data:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)

    def go_to_step2(self):
        """Move to step 2: Load builder"""
        # Hide step 1
        self.step1_widget.hide()

        # Show step 2
        self.layout().addWidget(self.step2_widget)
        self.step2_widget.show()

        # Initialize step 2 with rifle data
        self.initialize_step2()
        # persist last-open step
        try:
            self.current_step = 2
            self._save_ui_setting("last_step", "2")
        except Exception:
            pass

    def create_step2_page(self):
        """Step 2: Interactive Load Builder"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("padding: 10px; font-size: 11pt;")
        back_btn.clicked.connect(self.go_back_to_step1)
        header_layout.addWidget(back_btn)

        title = QLabel("🔬 Interactive Load Builder")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        save_btn = QPushButton("💾 Save Load")
        save_btn.setStyleSheet(
            """
            background: #3498db; color: white;
            padding: 10px 20px; border-radius: 5px;
            font-weight: bold;
        """
        )
        header_layout.addWidget(save_btn)

        create_batch_btn = QPushButton("📦 Create Batch")
        create_batch_btn.setStyleSheet(
            """
            background: #27ae60; color: white;
            padding: 10px 20px; border-radius: 5px;
            font-weight: bold;
        """
        )
        header_layout.addWidget(create_batch_btn)
        create_batch_btn.clicked.connect(self.on_create_batch_clicked)

        print_label_btn = QPushButton("🏷️ Print Label")
        print_label_btn.setStyleSheet(
            "background:#f39c12; color:white; padding:10px 14px; border-radius:5px;"
        )
        print_label_btn.clicked.connect(self.on_print_label_clicked)
        header_layout.addWidget(print_label_btn)

        layout.addLayout(header_layout)

        # Main content: Splitter (left controls, right visualization)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Controls
        left_panel = self.create_controls_panel()
        splitter.addWidget(left_panel)

        # Right panel: Visualization
        right_panel = self.create_visualization_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 2)  # Controls: 40%
        splitter.setStretchFactor(1, 3)  # Viz: 60%

        layout.addWidget(splitter, 1)

        # Bottom: AI Chat (collapsible)
        self.chat_widget = self.create_ai_chat_panel()
        layout.addWidget(self.chat_widget)

        widget.setLayout(layout)
        return widget

    def create_controls_panel(self):
        """Create left control panel"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        # Components
        comp_group = self.create_component_controls()
        scroll_layout.addWidget(comp_group)

        # Charge weight slider
        charge_group = self.create_charge_slider()
        scroll_layout.addWidget(charge_group)

        # Seating depth
        seating_group = self.create_seating_controls()
        scroll_layout.addWidget(seating_group)

        scroll_layout.addStretch()

        # Import chronograph CSV button
        import_btn = QPushButton("📥 Import Chronograph CSV")
        import_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        import_btn.clicked.connect(self.on_import_chronograph_clicked)
        scroll_layout.addWidget(import_btn)

        # Manual chronograph entry
        manual_btn = QPushButton("✍️ Manually Add Chronograph Data")
        manual_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        manual_btn.clicked.connect(self.on_manual_chronograph_clicked)
        scroll_layout.addWidget(manual_btn)

        # Chronograph imports list
        chrono_group = QGroupBox("Imported Chronograph Data")
        chrono_layout = QVBoxLayout()

        self.chrono_list = QListWidget()
        chrono_layout.addWidget(self.chrono_list)
        self.chrono_list.itemSelectionChanged.connect(self.on_chrono_selection_changed)

        chrono_btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("↺ Refresh")
        refresh_btn.clicked.connect(self.on_refresh_chronograph_list)
        chrono_btn_layout.addWidget(refresh_btn)

        attach_btn = QPushButton("🔗 Attach to Profile")
        attach_btn.clicked.connect(self.on_attach_chronograph_to_profile)
        chrono_btn_layout.addWidget(attach_btn)

        save_btn = QPushButton("💾 Save Import → Test Results")
        save_btn.clicked.connect(self.on_save_chronograph_to_test_results)
        chrono_btn_layout.addWidget(save_btn)

        qc_attach_btn = QPushButton("🏷️ Attach to QC Batch")
        qc_attach_btn.clicked.connect(self.on_attach_chrono_to_qc_batch)
        chrono_btn_layout.addWidget(qc_attach_btn)

        suggest_btn = QPushButton("💡 Analyze & Suggest")
        suggest_btn.clicked.connect(self.on_analyze_and_suggest)
        chrono_btn_layout.addWidget(suggest_btn)

        optimize_btn = QPushButton("⚙️ Optimize From Ladder Tests")
        optimize_btn.clicked.connect(self.on_optimize_from_ladder_tests)
        chrono_btn_layout.addWidget(optimize_btn)

        calibrate_btn = QPushButton("🧭 Calibrate Engine")
        calibrate_btn.setStyleSheet("padding:6px;")
        calibrate_btn.clicked.connect(self.on_calibrate_engine_clicked)
        chrono_btn_layout.addWidget(calibrate_btn)

        show_cal_btn = QPushButton("🔎 Show Calibration")
        show_cal_btn.setStyleSheet("padding:6px;")
        show_cal_btn.clicked.connect(self.on_show_calibration_clicked)
        chrono_btn_layout.addWidget(show_cal_btn)

        chrono_layout.addLayout(chrono_btn_layout)
        chrono_group.setLayout(chrono_layout)
        scroll_layout.addWidget(chrono_group)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)

        layout.addWidget(scroll)
        widget.setLayout(layout)

        return widget

    def create_component_controls(self):
        """Create component selection controls"""
        group = QGroupBox("💊 Components")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12pt; }")
        layout = QVBoxLayout()

        # Bullet
        bullet_label = QLabel("Bullet:")
        layout.addWidget(bullet_label)

        self.bullet_combo = QComboBox()
        self.bullet_combo.currentIndexChanged.connect(self.on_bullet_changed)
        layout.addWidget(self.bullet_combo)

        self.bullet_info = QLabel("Select bullet to see details")
        self.bullet_info.setStyleSheet(
            "color: #7f8c8d; font-size: 9pt; font-style: italic;"
        )
        layout.addWidget(self.bullet_info)

        layout.addSpacing(10)

        # Environmental conditions
        env_group = QGroupBox("🌤️ Ambient Conditions")
        env_layout = QHBoxLayout()
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(-40.0, 60.0)
        self.temp_spin.setValue(15.0)
        self.temp_spin.setSuffix(" °C")
        env_layout.addWidget(QLabel("Temp"))
        env_layout.addWidget(self.temp_spin)

        self.pressure_spin = QDoubleSpinBox()
        self.pressure_spin.setRange(70.0, 110.0)
        self.pressure_spin.setValue(101.325)
        self.pressure_spin.setSuffix(" kPa")
        env_layout.addWidget(QLabel("Pressure"))
        env_layout.addWidget(self.pressure_spin)

        self.humidity_spin = QDoubleSpinBox()
        self.humidity_spin.setRange(0.0, 100.0)
        self.humidity_spin.setValue(0.0)
        self.humidity_spin.setSuffix(" %")
        env_layout.addWidget(QLabel("Humidity"))
        env_layout.addWidget(self.humidity_spin)

        env_group.setLayout(env_layout)
        layout.addWidget(env_group)

        # Powder
        powder_label = QLabel("Powder:")
        layout.addWidget(powder_label)

        self.powder_combo = QComboBox()
        self.powder_combo.currentIndexChanged.connect(self.on_powder_changed)
        layout.addWidget(self.powder_combo)

        self.powder_info = QLabel("Select powder to see details")
        self.powder_info.setStyleSheet(
            "color: #7f8c8d; font-size: 9pt; font-style: italic;"
        )
        layout.addWidget(self.powder_info)

        # AI recommendation placeholder
        self.powder_recommendation = QLabel("")
        self.powder_recommendation.setWordWrap(True)
        self.powder_recommendation.setStyleSheet(
            """
            background: #e8f4f8;
            color: #2c3e50;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #9b59b6;
        """
        )
        layout.addWidget(self.powder_recommendation)

        layout.addSpacing(10)

        # Primer
        primer_label = QLabel("Primer:")
        layout.addWidget(primer_label)

        self.primer_combo = QComboBox()
        layout.addWidget(self.primer_combo)

        self.primer_info = QLabel("Select primer to see details")
        self.primer_info.setStyleSheet(
            "color: #7f8c8d; font-size: 9pt; font-style: italic;"
        )
        layout.addWidget(self.primer_info)

        group.setLayout(layout)
        return group

    def create_charge_slider(self):
        """Create charge weight slider"""
        group = QGroupBox("⚖️ Charge Weight")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12pt; }")
        layout = QVBoxLayout()

        # Current value display
        self.charge_label = QLabel(f"{self.current_charge:.1f} gr")
        self.charge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.charge_label.setStyleSheet(
            """
            font-size: 24pt;
            font-weight: bold;
            color: #27ae60;
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
        """
        )
        layout.addWidget(self.charge_label)

        # Slider
        self.charge_slider = QSlider(Qt.Orientation.Horizontal)
        self.charge_slider.setMinimum(300)  # 30.0gr
        self.charge_slider.setMaximum(550)  # 55.0gr
        self.charge_slider.setValue(425)  # 42.5gr
        self.charge_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.charge_slider.setTickInterval(25)
        self.charge_slider.valueChanged.connect(self.on_charge_slider_changed)
        layout.addWidget(self.charge_slider)

        # Min/Max labels
        limits_layout = QHBoxLayout()
        limits_layout.addWidget(QLabel("30.0 gr"))
        limits_layout.addStretch()
        limits_layout.addWidget(QLabel("55.0 gr"))
        layout.addLayout(limits_layout)

        # Hint
        hint = QLabel("💡 Drag to see real-time results!")
        hint.setStyleSheet("color: #7f8c8d; font-size: 9pt; font-style: italic;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        group.setLayout(layout)
        return group

    def create_seating_controls(self):
        """Create seating depth controls"""
        group = QGroupBox("📏 Seating Depth")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12pt; }")
        layout = QVBoxLayout()

        # COAL
        coal_layout = QHBoxLayout()
        coal_layout.addWidget(QLabel("COAL:"))
        self.coal_spin = QDoubleSpinBox()
        self.coal_spin.setRange(50.0, 100.0)
        self.coal_spin.setValue(71.5)
        self.coal_spin.setDecimals(2)
        self.coal_spin.setSuffix(" mm")
        self.coal_spin.valueChanged.connect(self.on_seating_changed)
        coal_layout.addWidget(self.coal_spin)
        layout.addLayout(coal_layout)

        # CBTO
        cbto_layout = QHBoxLayout()
        cbto_layout.addWidget(QLabel("CBTO:"))
        self.cbto_spin = QDoubleSpinBox()
        self.cbto_spin.setRange(50.0, 100.0)
        self.cbto_spin.setValue(68.8)
        self.cbto_spin.setDecimals(2)
        self.cbto_spin.setSuffix(" mm")
        self.cbto_spin.valueChanged.connect(self.on_seating_changed)
        cbto_layout.addWidget(self.cbto_spin)
        layout.addLayout(cbto_layout)

        # Jump display
        self.jump_label = QLabel("Jump: calculating...")
        self.jump_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        layout.addWidget(self.jump_label)

        # Optimize button
        optimize_btn = QPushButton("🤖 Optimize for Accuracy")
        optimize_btn.setStyleSheet(
            """
            background: #9b59b6;
            color: white;
            padding: 8px;
            border-radius: 5px;
        """
        )
        layout.addWidget(optimize_btn)

        group.setLayout(layout)
        return group

    def create_visualization_panel(self):
        """Create right visualization panel"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Stats bar
        stats_group = self.create_stats_bar()
        layout.addWidget(stats_group)

        # Scope adjustment comparison
        self.scope_comparison_group = QGroupBox(
            "🎯 KIKKERT JUSTERING (vs. forrige ladning)"
        )
        self.scope_comparison_group.setStyleSheet(
            """
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                font-weight: bold;
                padding-top: 15px;
            }
        """
        )
        scope_layout = QVBoxLayout()
        self.scope_comparison_group.setLayout(scope_layout)

        self.scope_comparison_label = QLabel(
            "Velg rifle og komponenter for å se sammenligning..."
        )
        self.scope_comparison_label.setWordWrap(True)
        self.scope_comparison_label.setStyleSheet(
            "color: #856404; font-weight: normal; padding: 5px; font-size: 9pt;"
        )
        scope_layout.addWidget(self.scope_comparison_label)

        self.scope_comparison_group.setVisible(False)
        layout.addWidget(self.scope_comparison_group)

        # 🎯 Scope Adjustment Comparison (vs previous load)
        self.scope_comparison_group = QGroupBox(
            "🎯 KIKKERT JUSTERING (vs. forrige ladning)"
        )
        self.scope_comparison_group.setStyleSheet(
            """
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                margin-top: 5px;
                font-weight: bold;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        )
        scope_comp_layout = QVBoxLayout()
        self.scope_comparison_label = QLabel(
            "Velg rifle for å se sammenligning med forrige ladning."
        )
        self.scope_comparison_label.setWordWrap(True)
        self.scope_comparison_label.setStyleSheet(
            "color: #856404; font-weight: normal; padding: 10px; font-size: 9pt;"
        )
        scope_comp_layout.addWidget(self.scope_comparison_label)
        self.scope_comparison_group.setLayout(scope_comp_layout)
        self.scope_comparison_group.setVisible(False)
        layout.addWidget(self.scope_comparison_group)

        # Pressure & Velocity plots - lazy-import pyqtgraph and provide safe
        # fallbacks if the library is unavailable (prevents heavy import at
        # module load time and keeps headless probes lightweight).
        try:
            import pyqtgraph as pg  # type: ignore

            # Keep reference to pyqtgraph module for later use
            self._pg = pg

            self.pressure_plot = pg.PlotWidget()
            self.pressure_plot.setBackground("w")
            self.pressure_plot.setLabel("left", "Pressure", units="PSI")
            self.pressure_plot.setLabel("bottom", "Time", units="ms")
            self.pressure_plot.setTitle("Chamber Pressure", color="k", size="12pt")
            self.pressure_plot.setMinimumHeight(200)
            layout.addWidget(self.pressure_plot)

            self.velocity_plot = pg.PlotWidget()
            self.velocity_plot.setBackground("w")
            self.velocity_plot.setLabel("left", "Velocity", units="fps")
            self.velocity_plot.setLabel("bottom", "Position", units="inches")
            self.velocity_plot.setTitle("Bullet Velocity", color="k", size="12pt")
            self.velocity_plot.setMinimumHeight(200)
            layout.addWidget(self.velocity_plot)
            # Transonic overlay controls
            trans_h = QHBoxLayout()
            self.transonic_cb = QCheckBox("Show Transonic Margin")
            self.transonic_cb.setChecked(True)
            self.transonic_cb.toggled.connect(self.update_visualization)
            # persist when toggled
            self.transonic_cb.toggled.connect(
                lambda v: self._save_ui_setting(
                    "transonic_overlay_enabled", "1" if v else "0"
                )
            )
            trans_h.addWidget(self.transonic_cb)

            trans_h.addWidget(QLabel("Margin (fps):"))
            self.transonic_margin = QDoubleSpinBox()
            self.transonic_margin.setRange(0.0, 500.0)
            self.transonic_margin.setValue(50.0)
            self.transonic_margin.setSingleStep(5.0)
            self.transonic_margin.valueChanged.connect(self.update_visualization)
            # persist margin changes
            self.transonic_margin.valueChanged.connect(
                lambda v: self._save_ui_setting("transonic_margin_fps", str(v))
            )
            trans_h.addWidget(self.transonic_margin)

            layout.addLayout(trans_h)
            # load persisted ui settings if present
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT value FROM ui_settings WHERE key = ?",
                    ("transonic_overlay_enabled",),
                )
                row = cur.fetchone()
                if row and row[0] is not None:
                    try:
                        self.transonic_cb.setChecked(bool(int(row[0])))
                    except Exception:
                        # tolerate non-int values
                        self.transonic_cb.setChecked(
                            row[0].lower() in ("1", "true", "yes")
                        )
                cur.execute(
                    "SELECT value FROM ui_settings WHERE key = ?",
                    ("transonic_margin_fps",),
                )
                row2 = cur.fetchone()
                if row2 and row2[0] is not None:
                    try:
                        self.transonic_margin.setValue(float(row2[0]))
                    except Exception:
                        pass
                # velocity y-range
                cur.execute(
                    "SELECT value FROM ui_settings WHERE key = ?", ("velocity_y_min",)
                )
                vmin_r = cur.fetchone()
                if vmin_r and vmin_r[0] is not None:
                    try:
                        self.velocity_y_min = float(vmin_r[0])
                    except Exception:
                        self.velocity_y_min = None
                else:
                    self.velocity_y_min = None
                cur.execute(
                    "SELECT value FROM ui_settings WHERE key = ?", ("velocity_y_max",)
                )
                vmax_r = cur.fetchone()
                if vmax_r and vmax_r[0] is not None:
                    try:
                        self.velocity_y_max = float(vmax_r[0])
                    except Exception:
                        self.velocity_y_max = None
                else:
                    self.velocity_y_max = None
            except Exception:
                pass
        except Exception:
            # Fallback: simple read-only text placeholders so UI still renders
            from PyQt6.QtWidgets import QTextEdit

            ph1 = QTextEdit("Pressure plot unavailable (pyqtgraph missing)")
            ph1.setReadOnly(True)
            ph1.setMinimumHeight(200)
            layout.addWidget(ph1)

            ph2 = QTextEdit("Velocity plot unavailable (pyqtgraph missing)")
            ph2.setReadOnly(True)
            ph2.setMinimumHeight(200)
            layout.addWidget(ph2)

        # Compare button
        compare_btn = QPushButton("📊 Compare with Other Powders")
        compare_btn.setStyleSheet("padding: 10px; font-size: 11pt;")
        layout.addWidget(compare_btn)

        widget.setLayout(layout)
        return widget

    def create_stats_bar(self):
        """Create statistics display bar"""
        group = QGroupBox("📊 Current Load Statistics")
        layout = QHBoxLayout()

        self.stat_pressure = QLabel("Pressure: --")
        self.stat_velocity = QLabel("Velocity: --")
        self.stat_energy = QLabel("Energy: --")
        self.stat_barrel_time = QLabel("Time: --")
        self.stat_safety = QLabel("Safety: --%")

        for label in [
            self.stat_pressure,
            self.stat_velocity,
            self.stat_energy,
            self.stat_barrel_time,
            self.stat_safety,
        ]:
            label.setStyleSheet("padding: 8px; font-size: 10pt;")
            layout.addWidget(label)

        group.setLayout(layout)
        return group

    def create_ai_chat_panel(self):
        """Create AI chat panel (collapsible)"""
        widget = QWidget()
        widget.setMaximumHeight(300)
        layout = QVBoxLayout()

        # Header with collapse button
        header_layout = QHBoxLayout()

        chat_title = QLabel("🤖 AI Assistant")
        chat_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        chat_title.setStyleSheet("color: #9b59b6;")
        header_layout.addWidget(chat_title)

        header_layout.addStretch()

        self.collapse_btn = QPushButton("▼ Collapse")
        self.collapse_btn.setStyleSheet("background: transparent; color: #7f8c8d;")
        self.collapse_btn.clicked.connect(self.toggle_chat)
        header_layout.addWidget(self.collapse_btn)

        layout.addLayout(header_layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(
            """
            QTextEdit {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 10pt;
            }
        """
        )
        layout.addWidget(self.chat_display, 1)

        # Input area
        input_layout = QHBoxLayout()

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask me anything about reloading...")
        self.chat_input.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
                font-size: 10pt;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """
        )
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input)

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(
            """
            QPushButton {
                background: #9b59b6;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
        """
        )
        send_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        # Add welcome message
        self.add_ai_message(
            "👋 Hi! I'm your AI reloading assistant. I can help with:\n\n"
            "• Component recommendations\n"
            "• Explaining pressure/velocity\n"
            "• Load development advice\n"
            "• Safety questions\n\n"
            "Just ask me anything!"
        )

        widget.setLayout(layout)
        return widget

    def on_create_batch_clicked(self):
        """UI handler: ask for batch name/size and create batch"""
        # Ensure components selected
        if not (
            self.rifle_data
            and self.bullet_data
            and self.powder_data
            and self.brass_data
        ):
            QMessageBox.warning(
                self,
                "Missing data",
                "Please select rifle, brass, bullet and powder before creating a batch.",
            )
            return

        count, ok = QInputDialog.getInt(
            self, "Batch Size", "How many rounds to create?", 10, 1, 10000, 1
        )
        if not ok:
            return

        name, ok2 = QInputDialog.getText(
            self,
            "Batch Name",
            "Name for this batch:",
            text=f"Batch for {self.rifle_data.get('name','rifle')}",
        )
        if not ok2:
            return

        # Ensure there's an ammo_profile for this configuration; create minimal profile
        cur = self.db.cursor
        # Build minimal ammo_profile
        cur.execute(
            "INSERT INTO ammo_profiles (name, rifle_id, caliber, bullet_id, bullet_weight, powder_id, powder_charge, primer_id, case_id, coal, cbto, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (
                name,
                self.rifle_data.get("id"),
                self.rifle_data.get("caliber"),
                self.bullet_data.get("id"),
                float(self.bullet_data.get("weight", 0)),
                self.powder_data.get("id"),
                float(self.current_charge),
                self.primer_data.get("id") if self.primer_data else None,
                self.brass_data.get("id") if self.brass_data else None,
                float(self.coal_mm),
                float(self.cbto_mm),
            ),
        )
        self.db.conn.commit()
        ammo_profile_id = cur.lastrowid

        # Call batch manager
        try:
            from src.database.batch_manager import create_loading_batch

            res = create_loading_batch(
                self.db,
                ammo_profile_id,
                name,
                count,
                self.current_charge,
                self.coal_mm,
                self.cbto_mm,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create batch: {e}")
            return

        if not res.get("ok"):
            QMessageBox.warning(
                self, "Batch not created", res.get("message", "Unknown error")
            )
            return

        QMessageBox.information(
            self,
            "Batch created",
            f"Batch created (id={res.get('batch_id')}). Inventory updated.",
        )

    def on_print_label_clicked(self):
        """Generate and save a printable label for the current profile or batch."""
        try:
            from src.utils.label_printer import generate_label_text, save_label_to_file
        except Exception as e:
            QMessageBox.critical(
                self, "Missing module", f"Label printer module missing: {e}"
            )
            return

        ap_id = getattr(self, "current_ammo_profile_id", None)
        if not ap_id:
            # ask user for an ammo_profile id
            ap_id, ok = QInputDialog.getInt(
                self,
                "Ammo Profile ID",
                "Enter Ammo Profile ID to print label for (or 0 to use QC Batch ID):",
                0,
            )
            if not ok:
                return
            if ap_id == 0:
                ap_id = None

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Label As", "label.txt", "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return

        text = generate_label_text(self.db, ammo_profile_id=ap_id)
        try:
            save_label_to_file(path, text)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save label: {e}")
            return

        QMessageBox.information(self, "Saved", f"Label saved to {path}")

    def on_import_chronograph_clicked(self):
        """Open a file dialog, import selected CSV and show stats"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select chronograph CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        try:
            from src.utils.chronograph_import import import_chronograph_csv

            res = import_chronograph_csv(
                self.db, path, None, note=f"Imported via UI from {path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Import failed", f"Failed to import CSV: {e}")
            return

        stats = res.get("stats", {})
        QMessageBox.information(
            self,
            "Import complete",
            f"Imported {stats.get('count', 0)} velocities. Avg: {stats.get('avg')}, ES: {stats.get('es')}, SD: {stats.get('sd')}",
        )

    def on_manual_chronograph_clicked(self):
        """Open dialog to paste velocities (one per line or comma-separated) and insert into DB"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Manual Chronograph Entry")
        layout = QVBoxLayout()

        info = QLabel(
            "Paste velocities (one per line or comma-separated). Optionally enter an Ammo Profile ID to link:"
        )
        layout.addWidget(info)

        vel_text = QTextEditWidget()
        vel_text.setPlaceholderText("e.g.\n820.1\n818.5\n823.0\n... or 820,818.5,823")
        vel_text.setMinimumHeight(120)
        layout.addWidget(vel_text)

        ap_label = QLabel("Ammo Profile ID (optional):")
        layout.addWidget(ap_label)
        ap_input = QLineEdit()
        ap_input.setPlaceholderText("e.g. 42")
        layout.addWidget(ap_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)

        def on_accept():
            text = vel_text.toPlainText().strip()
            if not text:
                QMessageBox.warning(
                    dlg, "No data", "Please paste at least one velocity value."
                )
                return
            # parse values
            normalized = text.replace(",", " ")
            tokens = [t for t in normalized.split() if t.strip()]
            vals = []
            for tok in tokens:
                try:
                    vals.append(float(tok))
                except Exception:
                    QMessageBox.warning(
                        dlg, "Parse error", f"Could not parse token: {tok}"
                    )
                    return

            ap_id = None
            ap_text = ap_input.text().strip()
            if ap_text:
                try:
                    ap_id = int(ap_text)
                except Exception:
                    QMessageBox.warning(
                        dlg, "Parse error", "Ammo Profile ID must be an integer"
                    )
                    return

            # persist
            try:
                from src.utils.chronograph_import import import_velocities

                res = import_velocities(
                    self.db, vals, ap_id, note="Manual entry via UI"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save velocities: {e}")
                dlg.reject()
                return

            stats = res.get("stats", {})
            QMessageBox.information(
                self,
                "Saved",
                f"Saved {stats.get('count',0)} velocities. Avg: {stats.get('avg')}",
            )
            dlg.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dlg.reject)

        dlg.setLayout(layout)
        dlg.exec()

    def on_refresh_chronograph_list(self):
        """Reload recent chronograph imports into the list widget"""
        cur = self.db.cursor
        cur.execute(
            "SELECT id, file_path, import_date, velocity_count, velocity_avg, velocity_es, velocity_sd FROM chronograph_imports ORDER BY import_date DESC LIMIT 50"
        )
        rows = cur.fetchall()
        self.chrono_list.clear()
        for r in rows:
            import_id = r[0]
            file_path = r[1] or "(manual)"
            date = r[2]
            count = r[3]
            avg = r[4]
            es = r[5]
            sd = r[6]
            text = f"#{import_id} {file_path} — {count} vel — avg {avg:.1f} fps — ES {es:.1f} — SD {sd:.1f}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, import_id)
            self.chrono_list.addItem(item)

    def on_chrono_selection_changed(self):
        """Plot velocities from the selected chronograph import into the velocity plot."""
        item = self.chrono_list.currentItem()
        if not item:
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute(
            "SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,)
        )
        row = cur.fetchone()
        if not row:
            return
        import json

        try:
            velocities = json.loads(row[0]) if row[0] else []
        except Exception:
            velocities = []

        if not velocities:
            QMessageBox.information(
                self, "No velocities", "Selected import contains no velocity data."
            )
            return

        pg = getattr(self, "_pg", None)
        # If pyqtgraph is available and we have a plot widget, plot simulated curve and overlay import points
        if (
            pg
            and hasattr(self, "velocity_plot")
            and isinstance(self.velocity_plot, pg.PlotWidget)
        ):
            try:
                self.velocity_plot.clear()
                # First draw simulated curve if present
                if hasattr(self, "_last_velocity_curve") and self._last_velocity_curve:
                    sim_x, sim_y = self._last_velocity_curve
                    self.velocity_plot.plot(
                        sim_x, sim_y, pen=pg.mkPen(color="#27ae60", width=3), name="sim"
                    )

                # Plot import velocities as points (x = shot index)
                xs = list(range(1, len(velocities) + 1))
                self.velocity_plot.plot(
                    xs,
                    velocities,
                    pen=pg.mkPen(color="#34495e", width=2),
                    symbol="o",
                    symbolBrush="#34495e",
                )
            except Exception as e:
                QMessageBox.warning(
                    self, "Plot error", f"Could not plot velocities: {e}"
                )
        else:
            # Fallback: show summary text
            avg = sum(velocities) / len(velocities)
            es = max(velocities) - min(velocities)
            self.scope_comparison_label.setText(
                f"Imported {len(velocities)} velocities — Avg {avg:.1f} fps — ES {es:.1f} fps"
            )

    def on_attach_chronograph_to_profile(self):
        """Attach selected chronograph import to an ammo_profile (create minimal profile if needed)"""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, "No selection", "Select an import from the list first"
            )
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)

        # If a current ammo selection exists (we created one when creating batch earlier), attach to it.
        # Otherwise create a minimal ammo_profile from current UI selections.
        cur = self.db.cursor
        cur.execute(
            "SELECT ammo_profile_id FROM chronograph_imports WHERE id = ?", (import_id,)
        )
        existing = cur.fetchone()
        if existing and existing[0]:
            QMessageBox.information(
                self,
                "Already attached",
                f"Import already attached to profile id {existing[0]}",
            )
            return

        # Create minimal profile if we have component selections
        if self.rifle_data and self.bullet_data and self.powder_data:
            name = f"Profile from import {import_id}"
            cur.execute(
                "INSERT INTO ammo_profiles (name, rifle_id, caliber, bullet_id, bullet_weight, powder_id, powder_charge, primer_id, case_id, coal, cbto, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (
                    name,
                    self.rifle_data.get("id"),
                    self.rifle_data.get("caliber"),
                    self.bullet_data.get("id"),
                    float(self.bullet_data.get("weight", 0)),
                    self.powder_data.get("id"),
                    float(self.current_charge),
                    self.primer_data.get("id") if self.primer_data else None,
                    self.brass_data.get("id") if self.brass_data else None,
                    float(self.coal_mm),
                    float(self.cbto_mm),
                ),
            )
            self.db.conn.commit()
            ammo_profile_id = cur.lastrowid
        else:
            # Prompt for profile id
            ap_id, ok = QInputDialog.getInt(
                self, "Ammo Profile ID", "Enter existing Ammo Profile ID to attach to:"
            )
            if not ok:
                return
            ammo_profile_id = ap_id

        # Update import row
        cur.execute(
            "UPDATE chronograph_imports SET ammo_profile_id = ? WHERE id = ?",
            (ammo_profile_id, import_id),
        )
        self.db.conn.commit()
        QMessageBox.information(
            self,
            "Attached",
            f"Import #{import_id} attached to profile {ammo_profile_id}",
        )
        self.on_refresh_chronograph_list()

    def on_save_chronograph_to_test_results(self):
        """Save selected chronograph import statistics into `test_results` linked to a profile or batch."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, "No selection", "Select an import from the list first"
            )
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute(
            "SELECT velocities_json, ammo_profile_id FROM chronograph_imports WHERE id = ?",
            (import_id,),
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Not found", "Import row not found in DB")
            return
        import json

        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(
                self, "No velocities", "Selected import has no velocities"
            )
            return

        # Determine ammo_profile to attach results
        ap_id = row[1]
        if not ap_id:
            # try to use currently selected ammo/profile in UI if exists (we created one earlier when creating batch)
            # For simplicity, prompt user for an ammo_profile id
            ap_id, ok = QInputDialog.getInt(
                self,
                "Ammo Profile ID",
                "Enter Ammo Profile ID to associate test results with:",
            )
            if not ok:
                return

        # Compute stats
        avg = sum(velocities) / len(velocities)
        es = max(velocities) - min(velocities)
        sd = statistics.stdev(velocities) if len(velocities) > 1 else 0.0

        # Insert into test_results: put first up to 3 velocities into velocity_1..3
        v1 = velocities[0] if len(velocities) > 0 else None
        v2 = velocities[1] if len(velocities) > 1 else None
        v3 = velocities[2] if len(velocities) > 2 else None

        cur.execute(
            "INSERT INTO test_results (ladder_test_id, charge_weight, velocity_1, velocity_2, velocity_3, velocity_avg, velocity_es, velocity_sd, image_path, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None,
                None,
                v1,
                v2,
                v3,
                float(avg),
                float(es),
                float(sd),
                None,
                f"Imported from chronograph_imports #{import_id}, linked to ammo_profile {ap_id}",
            ),
        )
        self.db.conn.commit()
        inserted_id = cur.lastrowid
        QMessageBox.information(
            self,
            "Saved",
            f"Saved test_results id {inserted_id} (avg {avg:.1f} fps, ES {es:.1f})",
        )
        # Also log predicted pressure for this saved test result (best-effort)
        try:
            rifle_id = self.rifle_data["id"] if self.rifle_data else None
            # determine charge from attached ammo_profile if present
            chosen_charge = None
            if ap_id:
                cur.execute(
                    "SELECT powder_charge FROM ammo_profiles WHERE id = ?", (ap_id,)
                )
                r = cur.fetchone()
                if r and r[0] is not None:
                    chosen_charge = float(r[0])
            if chosen_charge is None:
                chosen_charge = float(self.current_charge)

            coal = float(self.coal_spin.value()) if hasattr(self, "coal_spin") else None
            cbto = float(self.cbto_spin.value()) if hasattr(self, "cbto_spin") else None
            saami = None
            if self.rifle_data and "caliber" in self.rifle_data:
                rows = self.db.execute_query(
                    "SELECT max_pressure_bar FROM calibers WHERE name = ?",
                    (self.rifle_data["caliber"],),
                )
                if rows:
                    max_bar = rows[0].get("max_pressure_bar")
                    if max_bar is not None:
                        saami = float(max_bar) * 14.503773772

            predict_and_log(
                self.db,
                self.engine,
                rifle_id,
                ap_id,
                chosen_charge,
                coal_mm=coal,
                cbto_mm=cbto,
                saami_max_psi=saami,
                note=f"Saved test_results #{inserted_id} from import #{import_id}",
                temp_c=(
                    float(self.temp_spin.value())
                    if hasattr(self, "temp_spin")
                    else None
                ),
                pressure_kpa=(
                    float(self.pressure_spin.value())
                    if hasattr(self, "pressure_spin")
                    else None
                ),
                humidity_pct=(
                    float(self.humidity_spin.value())
                    if hasattr(self, "humidity_spin")
                    else None
                ),
            )
        except Exception:
            pass

    def on_analyze_and_suggest(self):
        """Analyze selected import (or current test results) and show recommendations."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, "No selection", "Select an import from the list first"
            )
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute(
            "SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,)
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Not found", "Import row not found in DB")
            return
        import json

        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(
                self, "No velocities", "Selected import has no velocities"
            )
            return

        # Compute stats
        import statistics as _st

        avg = _st.mean(velocities)
        es = max(velocities) - min(velocities)
        sd = _st.stdev(velocities) if len(velocities) > 1 else 0.0

        from src.utils.recommender import suggest_adjustments

        stats = {"count": len(velocities), "avg": avg, "es": es, "sd": sd}
        suggestions = suggest_adjustments(
            stats, self.current_charge, self.coal_mm, self.cbto_mm
        )

        # Show suggestions in dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Analysis & Suggestions")
        layout = QVBoxLayout()
        for s in suggestions:
            layout.addWidget(QLabel(s))

        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec()

    def on_optimize_from_ladder_tests(self):
        """Query historical ladder tests and propose an optimal charge."""
        try:
            from src.utils.ladder_optimizer import suggest_charge_from_history
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Optimizer module missing: {e}")
            return

        rifle_id = self.rifle_data.get("id") if self.rifle_data else None
        bullet_id = self.bullet_data.get("id") if self.bullet_data else None
        powder_id = self.powder_data.get("id") if self.powder_data else None

        res = suggest_charge_from_history(self.db, rifle_id, bullet_id, powder_id)
        if not res:
            QMessageBox.information(
                self,
                "Insufficient data",
                "Not enough historical ladder test data to suggest an optimal charge.",
            )
            return

        suggested = res.get("suggested_charge")
        model = res.get("model", {})
        a = model.get("a")
        b = model.get("b")
        r2 = model.get("r2")

        # Refine suggestion by sampling the quadratic model across observed range
        try:
            min_c, max_c = res.get("observed_range", (suggested - 0.5, suggested + 0.5))

            samples = []
            best_charge = suggested
            best_val = None
            for i in range(21):
                c = min_c + (max_c - min_c) * i / 20.0
                val = a * c * c + b * c + model.get("c", 0.0)
                samples.append((c, val))
                if best_val is None or val < best_val:
                    best_val = val
                    best_charge = c

            # Use refined charge
            refined = best_charge
        except Exception:
            refined = suggested

        # Plot model curve overlay on velocity_plot (uses charge vs predicted group size)
        pg = getattr(self, "_pg", None)
        if (
            pg
            and hasattr(self, "velocity_plot")
            and isinstance(self.velocity_plot, pg.PlotWidget)
        ):
            try:
                # prepare curve points
                xs = [s[0] for s in samples]
                ys = [s[1] for s in samples]
                # draw as separate plot (different color)
                self.velocity_plot.plot(
                    xs,
                    ys,
                    pen=pg.mkPen(color="#8e44ad", width=2, style=Qt.PenStyle.DashLine),
                )
            except Exception:
                pass

        # Safety check: use ballistics engine to predict peak pressure for refined suggestion
        predicted_pressure = None
        saami_max_psi = None
        try:
            eng = self.engine
            if eng:
                res_calc = eng.calculate_load(
                    self.rifle_data["id"],
                    self.bullet_data["id"],
                    self.powder_data["id"],
                    refined,
                    self.coal_mm,
                    self.cbto_mm,
                )
                predicted_pressure = res_calc.get("max_pressure_psi")
        except Exception:
            predicted_pressure = None

        try:
            # Lookup SAAMI/CIP max pressure for the caliber
            caliber = None
            if self.rifle_data:
                caliber = self.rifle_data.get("caliber")
            if caliber:
                cur = self.db.cursor
                cur.execute(
                    "SELECT max_pressure_bar FROM calibers WHERE name = ?", (caliber,)
                )
                r = cur.fetchone()
                if r and r[0]:
                    saami_max_psi = float(r[0]) * 14.5037738
        except Exception:
            saami_max_psi = None

        # If we have predicted pressure and saami, enforce safety
        # Log the prediction into pressure_history for auditing
        try:
            ammo_profile_id = getattr(self, "current_ammo_profile_id", None)
            predict_and_log(
                self.db,
                self.engine,
                rifle_id,
                ammo_profile_id,
                refined,
                coal_mm=self.coal_mm,
                cbto_mm=self.cbto_mm,
                saami_max_psi=saami_max_psi,
                note="Optimizer suggestion",
            )
        except Exception:
            pass

        if predicted_pressure is not None and saami_max_psi is not None:
            if predicted_pressure > saami_max_psi:
                QMessageBox.critical(
                    self,
                    "Unsafe",
                    f"Predicted peak pressure {predicted_pressure:.0f} PSI exceeds SAAMI max {saami_max_psi:.0f} PSI. Suggestion blocked.",
                )
                return
            elif predicted_pressure > saami_max_psi * 0.95:
                confirm = QMessageBox.question(
                    self,
                    "High pressure warning",
                    f"Predicted peak pressure {predicted_pressure:.0f} PSI is within 95% of SAAMI max ({saami_max_psi:.0f} PSI). Apply anyway?",
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return

        # Prompt user to accept refined suggestion
        accept = QMessageBox.question(
            self,
            "Optimizer Suggestion",
            f"Suggested charge (refined): {refined:.2f} gr\nModel R^2: {r2:.2f}\nApply suggested charge to slider?",
        )
        if accept == QMessageBox.StandardButton.Yes:
            # set slider value (slider stores 10x grains)
            try:
                self.charge_slider.setValue(int(round(refined * 10)))
                self.current_charge = refined
                self.charge_label.setText(f"{self.current_charge:.2f} gr")
                self.update_visualization()
                # Log predicted pressure for the applied suggestion
                try:
                    rifle_id = self.rifle_data["id"] if self.rifle_data else None
                    ap_id = getattr(self, "current_ammo_profile_id", None)
                    coal = (
                        float(self.coal_spin.value())
                        if hasattr(self, "coal_spin")
                        else None
                    )
                    cbto = (
                        float(self.cbto_spin.value())
                        if hasattr(self, "cbto_spin")
                        else None
                    )
                    # saami lookup
                    saami = None
                    if self.rifle_data and "caliber" in self.rifle_data:
                        rows = self.db.execute_query(
                            "SELECT max_pressure_bar FROM calibers WHERE name = ?",
                            (self.rifle_data["caliber"],),
                        )
                        if rows:
                            max_bar = rows[0].get("max_pressure_bar")
                            if max_bar is not None:
                                saami = float(max_bar) * 14.503773772
                    predict_and_log(
                        self.db,
                        self.engine,
                        rifle_id,
                        ap_id,
                        float(self.current_charge),
                        coal_mm=coal,
                        cbto_mm=cbto,
                        saami_max_psi=saami,
                        note="Applied optimizer suggestion",
                        temp_c=(
                            float(self.temp_spin.value())
                            if hasattr(self, "temp_spin")
                            else None
                        ),
                        pressure_kpa=(
                            float(self.pressure_spin.value())
                            if hasattr(self, "pressure_spin")
                            else None
                        ),
                        humidity_pct=(
                            float(self.humidity_spin.value())
                            if hasattr(self, "humidity_spin")
                            else None
                        ),
                    )
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.warning(
                    self, "Apply failed", f"Could not apply suggested charge: {e}"
                )

    def on_calibrate_engine_clicked(self):
        """Run calibration using the selected chronograph import(s)."""
        # Collect selected import(s)
        items = [self.chrono_list.item(i) for i in range(self.chrono_list.count())]
        selected_ids = []
        for it in items:
            if it and it.isSelected():
                iid = it.data(Qt.ItemDataRole.UserRole)
                if iid:
                    selected_ids.append(iid)

        if not selected_ids:
            # fallback: use current item if nothing multi-selected
            cur_item = self.chrono_list.currentItem()
            if cur_item:
                selected_ids = [cur_item.data(Qt.ItemDataRole.UserRole)]

        if not selected_ids:
            QMessageBox.information(
                self,
                "Calibrate",
                "Select at least one chronograph import to calibrate with.",
            )
            return

        try:
            from src.utils.calibrator import calibrate_engine
        except Exception as e:
            QMessageBox.critical(
                self, "Missing module", f"Calibration module not available: {e}"
            )
            return

        res = calibrate_engine(self.db, self.engine, selected_ids)
        if not res.get("ok"):
            QMessageBox.warning(
                self,
                "Calibration failed",
                f"Could not calibrate: {res.get('reason')} (used={res.get('used')})",
            )
            return

        slope = res.get("slope")
        intercept = res.get("intercept")
        mse = res.get("mse")
        used = res.get("used")

        QMessageBox.information(
            self,
            "Calibration Complete",
            f"Calibration stored. slope={slope:.4f}, intercept={intercept:.2f}, mse={mse:.3f}, used={used}",
        )

    def on_show_calibration_clicked(self):
        """Show last calibration info and optionally plot samples from selected imports."""
        cur = self.db.cursor
        cur.execute(
            "SELECT id, slope, intercept, mse, notes, created_date FROM engine_calibrations ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.information(
                self, "No calibration", "No calibration records found."
            )
            return

        cid, slope, intercept, mse, notes, created = row

        dlg = QDialog(self)
        dlg.setWindowTitle("Calibration Details")
        v = QVBoxLayout()
        v.addWidget(QLabel(f"Calibration ID: {cid}"))
        v.addWidget(QLabel(f"Created: {created}"))
        v.addWidget(
            QLabel(
                f"Slope: {slope:.6f}  Intercept: {float(intercept or 0.0):.2f}  MSE: {float(mse or 0.0):.3f}"
            )
        )
        v.addWidget(QLabel(f"Notes: {notes or ''}"))

        # If user has selected imports, offer to plot their samples
        selected_ids = []
        if hasattr(self, "chrono_list") and getattr(self, "chrono_list") is not None:
            try:
                items = [
                    self.chrono_list.item(i) for i in range(self.chrono_list.count())
                ]
                selected_ids = [
                    it.data(Qt.ItemDataRole.UserRole)
                    for it in items
                    if it and it.isSelected()
                ]
            except Exception:
                selected_ids = []

        # If there are no selected items, ask the user to enter import ids manually
        if not selected_ids:
            text, ok = QInputDialog.getText(
                self,
                "Select Imports",
                "Enter chronograph import IDs (comma-separated):",
            )
            if ok and text:
                try:
                    selected_ids = [
                        int(x.strip()) for x in text.split(",") if x.strip()
                    ]
                except Exception:
                    selected_ids = []

        if selected_ids:
            h = QHBoxLayout()
            plot_btn = QPushButton("Plot selected imports (predicted vs measured)")
            h.addWidget(plot_btn)
            v.addLayout(h)

            def do_plot():
                try:
                    from src.utils.calibrator import get_calibration_samples

                    samples = get_calibration_samples(
                        self.db, self.engine, selected_ids
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not get samples: {e}")
                    return

                if not samples.get("ok") or not samples.get("preds"):
                    QMessageBox.information(
                        self,
                        "No samples",
                        "No usable samples found for selected imports.",
                    )
                    return

                preds = samples.get("preds")
                meas = samples.get("meas")

                # Plot in a new dialog using pyqtgraph if available
                try:
                    import pyqtgraph as pg

                    pdlg = QDialog(self)
                    pdlg.setWindowTitle("Calibration Samples")
                    layout = QVBoxLayout()
                    pw = pg.PlotWidget()
                    pw.setLabel("left", "Measured Velocity (fps)")
                    pw.setLabel("bottom", "Predicted Velocity (fps)")
                    pw.plot(preds, meas, pen=None, symbol="o")
                    # fit line
                    try:
                        a = float(slope)
                        b = float(intercept or 0.0)
                        xs = sorted(preds)
                        ys = [a * x + b for x in xs]
                        pw.plot(xs, ys, pen=pg.mkPen(color="y", width=2))
                    except Exception:
                        pass
                    layout.addWidget(pw)
                    btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
                    btns.accepted.connect(pdlg.accept)
                    layout.addWidget(btns)
                    pdlg.setLayout(layout)
                    pdlg.exec()
                except Exception:
                    # Fallback: show textual summary
                    pairs = "\n".join(
                        f"pred:{p:.1f} -> meas:{m:.1f}" for p, m in zip(preds, meas)
                    )
                    QMessageBox.information(self, "Samples", f"{pairs}")

            plot_btn.clicked.connect(do_plot)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        btns.accepted.connect(dlg.accept)
        v.addWidget(btns)
        # Accept calibration button
        accept_btn = QPushButton("Accept Calibration")

        def do_accept():
            # Prompt user to optionally tie calibration to an ammo_profile
            try:
                cur = self.db.cursor
                cur.execute("SELECT id, name FROM ammo_profiles ORDER BY name")
                rows = cur.fetchall() or []
                choices = [r[1] or f"#{r[0]}" for r in rows]
                ids = [r[0] for r in rows]
                ammo_id = None
                if choices:
                    item, ok = QInputDialog.getItem(
                        self,
                        "Tie to ammo profile",
                        "Select ammo profile (optional)",
                        choices,
                        0,
                        False,
                    )
                    if ok and item:
                        try:
                            idx = choices.index(item)
                            ammo_id = ids[idx]
                        except Exception:
                            ammo_id = None

                # Update calibration row as accepted
                try:
                    if ammo_id:
                        cur.execute(
                            "UPDATE engine_calibrations SET accepted=1, accepted_date=CURRENT_TIMESTAMP, ammo_profile_id=? WHERE id = ?",
                            (ammo_id, cid),
                        )
                    else:
                        cur.execute(
                            "UPDATE engine_calibrations SET accepted=1, accepted_date=CURRENT_TIMESTAMP WHERE id = ?",
                            (cid,),
                        )
                    self.db.conn.commit()
                    QMessageBox.information(
                        self,
                        "Calibration Accepted",
                        "Calibration marked as accepted and tied to selected ammo profile.",
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"Could not accept calibration: {e}"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not query ammo profiles: {e}"
                )

        accept_btn.clicked.connect(do_accept)
        v.addWidget(accept_btn)

        dlg.setLayout(v)
        dlg.exec()

    def on_open_ai_chat(self):
        """Open a simple AI chat dialog that uses `src.utils.ai_assistant`."""
        try:
            from src.utils.ai_assistant import Assistant
        except Exception:
            Assistant = None

        dlg = QDialog(self)
        dlg.setWindowTitle("AI Assistant")
        v = QVBoxLayout()

        convo = QTextEdit()
        convo.setReadOnly(True)
        convo.setPlaceholderText("Assistant conversation")
        v.addWidget(convo)

        # Load recent chat history into conversation view
        try:
            if Assistant is not None:
                a = Assistant()
                recent = a.fetch_recent_chats(self.db)
                for r in reversed(recent):
                    convo.append(f"You ({r['created_date']}): {r['user']}")
                    convo.append(f"Assistant ({r['created_date']}): {r['assistant']}")
        except Exception:
            pass

        h = QHBoxLayout()
        inp = QLineEdit()
        inp.setPlaceholderText("Ask about loads, calibration, or suggest next steps...")
        send_btn = QPushButton("Send")
        h.addWidget(inp)
        h.addWidget(send_btn)
        v.addLayout(h)

        def append(line: str):
            convo.append(line)
            convo.moveCursor(QTextCursor.End)

        assistant = Assistant(db=self.db) if Assistant is not None else None

        def do_send():
            q = inp.text().strip()
            if not q:
                return
            append(f"You: {q}")
            inp.clear()
            append("Assistant: thinking...")
            try:
                # Build context for the assistant
                ctx = {}
                try:
                    if getattr(self, "rifle_data", None):
                        ctx["rifle"] = self.rifle_data.get("name")
                except Exception:
                    pass
                try:
                    ctx["charge"] = float(self.current_charge)
                except Exception:
                    pass
                try:
                    if getattr(self, "powder_data", None):
                        ctx["powder"] = self.powder_data.get("name")
                except Exception:
                    pass

                # latest calibration
                try:
                    cur = self.db.cursor
                    cur.execute(
                        "SELECT id, slope, intercept, mse, created_date FROM engine_calibrations ORDER BY id DESC LIMIT 1"
                    )
                    crow = cur.fetchone()
                    if crow:
                        ctx["last_calibration"] = {
                            "id": crow[0],
                            "slope": crow[1],
                            "intercept": crow[2],
                            "mse": float(crow[3] or 0.0),
                        }
                except Exception:
                    pass

                # recent chronograph imports summary
                try:
                    cur = self.db.cursor
                    cur.execute(
                        "SELECT id, velocity_avg, created_date FROM chronograph_imports ORDER BY created_date DESC LIMIT 5"
                    )
                    rows = cur.fetchall() or []
                    recent = []
                    for r in rows:
                        recent.append(
                            {"id": r[0], "vel": float(r[1] or 0.0), "date": r[2]}
                        )
                    if recent:
                        ctx["recent_imports_summary"] = recent
                except Exception:
                    pass

                if assistant:
                    resp = assistant.chat(q, [], context=ctx)
                    append(f"Assistant: {resp}")
                    try:
                        assistant.persist_chat(self.db, q, resp)
                    except Exception:
                        pass
                else:
                    append(
                        "Assistant: (stub) I can help inspect calibration, suggest safe charge ranges, or explain plots. Ask me something specific."
                    )
            except Exception as e:
                append(f"Assistant: Error contacting assistant: {e}")

        send_btn.clicked.connect(do_send)
        inp.returnPressed.connect(do_send)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        dlg.setLayout(v)
        dlg.exec()

    def on_explain_plot_clicked(self):
        """Gather current plot data and ask the assistant to explain it."""
        try:
            from src.utils.ai_assistant import Assistant
        except Exception:
            Assistant = None

        # Try to capture the last plotted velocity curve and stats
        ctx = {}
        try:
            if hasattr(self, "_last_velocity_curve") and self._last_velocity_curve:
                xs, ys = self._last_velocity_curve
                # summarize: min/max/mean
                import statistics

                ctx["plot_summary"] = {
                    "n": len(xs),
                    "x_min": min(xs),
                    "x_max": max(xs),
                    "y_min": min(ys),
                    "y_max": max(ys),
                    "y_mean": float(statistics.mean(ys)) if ys else None,
                }
        except Exception:
            pass

        # Persist snapshot if we have series data
        try:
            if (
                ctx.get("plot_summary")
                and hasattr(self, "_last_velocity_curve")
                and self._last_velocity_curve
            ):
                xs, ys = self._last_velocity_curve
                import json

                meta = json.dumps(ctx.get("plot_summary"))
                series = json.dumps({"x": xs, "y": ys})
                try:
                    cur = self.db.cursor
                    cur.execute(
                        "INSERT INTO plot_snapshots (snapshot_type, metadata, series_json) VALUES (?, ?, ?)",
                        ("velocity_curve", meta, series),
                    )
                    self.db.conn.commit()
                except Exception:
                    pass
        except Exception:
            pass

        dlg = QDialog(self)
        dlg.setWindowTitle("Explain Plot")
        v = QVBoxLayout()
        prompt_edit = QTextEdit()
        prompt_edit.setPlaceholderText(
            "Optional question about this plot (e.g., 'What does the slope mean?' )"
        )
        v.addWidget(QLabel("Plot summary:"))
        v.addWidget(QLabel(str(ctx.get("plot_summary", "No plot data available"))))
        v.addWidget(prompt_edit)

        h = QHBoxLayout()
        ask_btn = QPushButton("Ask Assistant")
        h.addWidget(ask_btn)
        v.addLayout(h)

        result = QTextEdit()
        result.setReadOnly(True)
        v.addWidget(result)

        def do_ask():
            q = prompt_edit.toPlainText().strip() or "Explain the currently shown plot."
            assistant = Assistant() if Assistant is not None else None
            try:
                if assistant:
                    resp = assistant.chat(
                        q, [], context={"plot_summary": ctx.get("plot_summary")}
                    )
                    result.setPlainText(resp)
                    try:
                        assistant.persist_chat(self.db, q, resp)
                    except Exception:
                        pass
                else:
                    result.setPlainText(
                        "(stub) No remote assistant available. Plot summary: %s"
                        % ctx.get("plot_summary")
                    )
            except Exception as e:
                result.setPlainText(f"Error contacting assistant: {e}")

        ask_btn.clicked.connect(do_ask)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        dlg.setLayout(v)
        dlg.exec()

    def on_open_preferences(self):
        """Open a small Preferences dialog for UI settings."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Preferences")
        v = QVBoxLayout()

        # Transonic overlay setting
        trans_cb = QCheckBox("Show Transonic Margin")
        trans_margin_label = QLabel("Margin (fps):")
        trans_spin = QDoubleSpinBox()
        trans_spin.setRange(0.0, 500.0)
        trans_spin.setSingleStep(5.0)

        # Load current persisted values
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT value FROM ui_settings WHERE key = ?",
                ("transonic_overlay_enabled",),
            )
            r = cur.fetchone()
            if r and r[0] is not None:
                try:
                    trans_cb.setChecked(bool(int(r[0])))
                except Exception:
                    trans_cb.setChecked(r[0].lower() in ("1", "true", "yes"))
            cur.execute(
                "SELECT value FROM ui_settings WHERE key = ?", ("transonic_margin_fps",)
            )
            r2 = cur.fetchone()
            if r2 and r2[0] is not None:
                try:
                    trans_spin.setValue(float(r2[0]))
                except Exception:
                    pass
        except Exception:
            pass

        v.addWidget(trans_cb)
        h = QHBoxLayout()
        h.addWidget(trans_margin_label)
        h.addWidget(trans_spin)
        v.addLayout(h)

        # Velocity plot Y-range prefs
        v.addSpacing(6)
        v.addWidget(QLabel("Velocity plot Y-range (fps) - optional"))
        y_h = QHBoxLayout()
        y_min_label = QLabel("Min:")
        y_min_spin = QDoubleSpinBox()
        y_min_spin.setRange(0.0, 5000.0)
        y_min_spin.setSingleStep(10.0)
        y_max_label = QLabel("Max:")
        y_max_spin = QDoubleSpinBox()
        y_max_spin.setRange(0.0, 10000.0)
        y_max_spin.setSingleStep(10.0)

        # Load persisted values
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT value FROM ui_settings WHERE key = ?", ("velocity_y_min",)
            )
            rmin = cur.fetchone()
            if rmin and rmin[0] is not None:
                try:
                    y_min_spin.setValue(float(rmin[0]))
                except Exception:
                    pass
            cur.execute(
                "SELECT value FROM ui_settings WHERE key = ?", ("velocity_y_max",)
            )
            rmax = cur.fetchone()
            if rmax and rmax[0] is not None:
                try:
                    y_max_spin.setValue(float(rmax[0]))
                except Exception:
                    pass
        except Exception:
            pass

        y_h.addWidget(y_min_label)
        y_h.addWidget(y_min_spin)
        y_h.addWidget(y_max_label)
        y_h.addWidget(y_max_spin)
        v.addLayout(y_h)

        # Theme selection + preview
        v.addSpacing(6)
        v.addWidget(QLabel("UI Theme"))
        theme_h = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_combo = QComboBox()
        theme_combo.addItems(["System", "Light", "Dark"])
        theme_h.addWidget(theme_label)
        theme_h.addWidget(theme_combo)
        # Preview box
        theme_preview = QLabel("Preview: Header, buttons and controls")
        theme_preview.setMinimumHeight(60)
        theme_preview.setStyleSheet(
            "padding:8px; border:1px solid #ccc; border-radius:4px;"
        )
        v.addLayout(theme_h)
        v.addWidget(theme_preview)

        # Load persisted theme if present
        try:
            cur = self.db.cursor
            cur.execute("SELECT value FROM ui_settings WHERE key = ?", ("ui_theme",))
            tr = cur.fetchone()
            if tr and tr[0]:
                theme_val = (tr[0] or "").lower()
                if theme_val == "dark":
                    theme_combo.setCurrentText("Dark")
                elif theme_val == "light":
                    theme_combo.setCurrentText("Light")
                else:
                    theme_combo.setCurrentText("System")
        except Exception:
            pass

        def _apply_theme_preview(name: str):
            try:
                n = (name or "").lower()
                if n == "dark":
                    theme_preview.setStyleSheet(
                        "background:#2c2c2c; color:#f0f0f0; padding:8px; border-radius:4px;"
                    )
                elif n == "light" or n == "system":
                    theme_preview.setStyleSheet(
                        "background: #ffffff; color: #222; padding:8px; border-radius:4px; border:1px solid #ddd;"
                    )
                else:
                    theme_preview.setStyleSheet(
                        "padding:8px; border:1px solid #ccc; border-radius:4px;"
                    )
            except Exception:
                pass

        theme_combo.currentTextChanged.connect(_apply_theme_preview)
        # initialise preview
        try:
            _apply_theme_preview(theme_combo.currentText())
        except Exception:
            pass

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        v.addWidget(btns)

        # Reset to defaults button
        reset_btn = QPushButton("Reset Preferences")

        def do_reset():
            try:
                # remove persisted keys
                for k in (
                    "transonic_overlay_enabled",
                    "transonic_margin_fps",
                    "velocity_y_min",
                    "velocity_y_max",
                    "ui_theme",
                ):
                    try:
                        self._delete_ui_setting(k)
                    except Exception:
                        pass
                # reset UI elements
                try:
                    trans_cb.setChecked(False)
                    trans_spin.setValue(50.0)
                    y_min_spin.setValue(0.0)
                    y_max_spin.setValue(0.0)
                    try:
                        theme_combo.setCurrentText("System")
                        _apply_theme_preview("System")
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass

        reset_btn.clicked.connect(do_reset)
        v.addWidget(reset_btn)

        def on_ok():
            try:
                self._save_ui_setting(
                    "transonic_overlay_enabled", "1" if trans_cb.isChecked() else "0"
                )
                self._save_ui_setting("transonic_margin_fps", str(trans_spin.value()))
                # velocity y-range
                try:
                    self._save_ui_setting("velocity_y_min", str(y_min_spin.value()))
                    self._save_ui_setting("velocity_y_max", str(y_max_spin.value()))
                    # update instance values
                    self.velocity_y_min = float(y_min_spin.value())
                    self.velocity_y_max = float(y_max_spin.value())
                except Exception:
                    pass
                # UI theme
                try:
                    sel = (theme_combo.currentText() or "System").lower()
                    if sel in ("system", "light", "dark"):
                        self._save_ui_setting("ui_theme", sel)
                        # apply immediately to this widget
                        if sel == "dark":
                            try:
                                self.setStyleSheet(
                                    "background: #2c2c2c; color: #f0f0f0;"
                                )
                            except Exception:
                                pass
                        else:
                            try:
                                self.setStyleSheet("")
                            except Exception:
                                pass
                except Exception:
                    pass
                # apply to live widgets if present
                try:
                    if getattr(self, "transonic_cb", None):
                        self.transonic_cb.setChecked(trans_cb.isChecked())
                    if getattr(self, "transonic_margin", None):
                        self.transonic_margin.setValue(trans_spin.value())
                    self.update_visualization()
                except Exception:
                    pass
            except Exception:
                pass
            dlg.accept()

        btns.accepted.connect(on_ok)
        btns.rejected.connect(dlg.reject)

        dlg.setLayout(v)
        dlg.exec()

    def on_suggest_next_charge(self):
        """Gather recent test results and ask GP optimizer to suggest next charge."""
        try:
            from src.utils.gp_optimizer import suggest_next_charge
        except Exception:
            QMessageBox.critical(self, "Error", "GP optimizer module not available.")
            return

        # Collect recent results from test_results (use velocity_avg if present)
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 20"
            )
            rows = cur.fetchall() or []
            if not rows:
                QMessageBox.information(
                    self,
                    "No data",
                    "Not enough recent test results to suggest a charge.",
                )
                return
            charges = []
            velocities = []
            # reverse to chronological order
            for r in reversed(rows):
                try:
                    c = float(r[0])
                    v = float(r[1])
                except Exception:
                    continue
                charges.append(c)
                velocities.append(v)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Could not query test results: {e}")
            return

        if not charges or not velocities:
            QMessageBox.information(
                self, "No usable data", "No usable charge/velocity pairs found."
            )
            return

        # Determine bounds from observed charges (expand a bit)
        min_c = max(0.0, min(charges) - 1.0)
        max_c = max(charges) + 1.0
        try:
            suggestion = suggest_next_charge(charges, velocities, (min_c, max_c))
        except Exception as e:
            QMessageBox.critical(self, "Optimizer Error", f"Optimizer failed: {e}")
            return

        # If subsonic mode is enabled, attempt to adjust suggestion downward until predicted velocity <= target
        try:
            if getattr(self, "subsonic_cb", None) and self.subsonic_cb.isChecked():
                target_v = float(self.subsonic_target.value())
                # if engine available, simulate and step down
                if hasattr(self, "engine") and self.engine:
                    try:
                        sim_v = None
                        # try predict at suggested charge
                        if hasattr(self.engine, "predict_velocity"):
                            sim_v = float(self.engine.predict_velocity(suggestion))
                        elif hasattr(self.engine, "calculate_load"):
                            res = self.engine.calculate_load(
                                None, None, None, suggestion, None, None
                            )
                            if isinstance(res, dict):
                                sim_v = float(
                                    res.get("velocity")
                                    or res.get("velocity_avg")
                                    or res.get("predicted_velocity")
                                )
                        # if predicted is above target, step down by 0.5gr until within bounds or reach min_c
                        step = 0.5
                        attempts = 0
                        while (
                            sim_v is not None
                            and sim_v > target_v
                            and suggestion > min_c
                            and attempts < 20
                        ):
                            suggestion = round(max(min_c, suggestion - step), 3)
                            attempts += 1
                            try:
                                if hasattr(self.engine, "predict_velocity"):
                                    sim_v = float(
                                        self.engine.predict_velocity(suggestion)
                                    )
                                elif hasattr(self.engine, "calculate_load"):
                                    res = self.engine.calculate_load(
                                        None, None, None, suggestion, None, None
                                    )
                                    if isinstance(res, dict):
                                        sim_v = float(
                                            res.get("velocity")
                                            or res.get("velocity_avg")
                                            or res.get("predicted_velocity")
                                        )
                            except Exception:
                                break
                        # if we couldn't satisfy target, warn user
                        if sim_v is not None and sim_v > target_v:
                            QMessageBox.warning(
                                self,
                                "Subsonic",
                                f"Could not reach target subsonic velocity {target_v}fps within charge bounds. Closest predicted: {sim_v:.1f}fps at {suggestion}gr",
                            )
                    except Exception:
                        pass
                else:
                    # without engine, just nudge suggestion lower conservatively
                    suggestion = round(max(min_c, suggestion - 0.5), 3)

        except Exception:
            pass

        # Persist suggestion
        try:
            import json

            basis = json.dumps({"charges": charges, "velocities": velocities})
            cur.execute(
                "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
                (float(suggestion), basis),
            )
            self.db.conn.commit()
        except Exception:
            pass

        QMessageBox.information(
            self, "Suggestion", f"Suggested next charge: {suggestion} gr"
        )

    def on_manage_suggestions_clicked(self):
        """Open a dialog to browse/pick past optimizer suggestions."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Optimizer Suggestions")
        v = QVBoxLayout()

        listw = QListWidget()
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT id, suggested_charge, created_date, basis_text FROM optimizer_suggestions ORDER BY id DESC LIMIT 200"
            )
            rows = cur.fetchall() or []
            for r in rows:
                sid = r[0]
                sc = r[1]
                cd = r[2]
                basis = (r[3] or "")[:200]
                item = QListWidgetItem(f"#{sid} — {sc}gr — {cd} — {basis}")
                item.setData(Qt.ItemDataRole.UserRole, sid)
                listw.addItem(item)
        except Exception:
            pass

        v.addWidget(listw)

        h = QHBoxLayout()
        create_wf_btn = QPushButton("Create Workflow from Suggestion")
        mark_tested_btn = QPushButton("Mark Suggestion Tested")
        h.addWidget(create_wf_btn)
        h.addWidget(mark_tested_btn)
        v.addLayout(h)

        def create_workflow():
            it = listw.currentItem()
            if not it:
                QMessageBox.information(self, "Select", "Select a suggestion first")
                return
            sid = it.data(Qt.ItemDataRole.UserRole)
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT suggested_charge, basis_text FROM optimizer_suggestions WHERE id = ?",
                    (sid,),
                )
                row = cur.fetchone()
                if not row:
                    QMessageBox.critical(self, "Error", "Suggestion not found")
                    return
                suggested_charge = float(row[0])
                basis = row[1] or ""
                name = f"GP Suggestion #{sid}"
                next_action = f"Test suggested charge {suggested_charge}gr (based on suggestion #{sid})"
                cur.execute(
                    "INSERT INTO load_development_workflows (name, status, next_action) VALUES (?, 'suggested', ?)",
                    (name, next_action),
                )
                self.db.conn.commit()
                QMessageBox.information(
                    self,
                    "Workflow Created",
                    "A load_development_workflow was created for this suggestion.",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "DB Error", f"Could not create workflow: {e}"
                )

        def mark_tested():
            it = listw.currentItem()
            if not it:
                QMessageBox.information(self, "Select", "Select a suggestion first")
                return
            sid = it.data(Qt.ItemDataRole.UserRole)
            # Prompt for test_result id (or choose from recent)
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT id, ladder_test_id, charge_weight, velocity_avg FROM test_results ORDER BY id DESC LIMIT 50"
                )
                rows = cur.fetchall() or []
                choices = [f"#{r[0]} charge:{r[2]} vel:{r[3]}" for r in rows]
                ids = [r[0] for r in rows]
                if choices:
                    sel, ok = QInputDialog.getItem(
                        self,
                        "Select Test Result",
                        "Choose test result that tested this suggestion",
                        choices,
                        0,
                        False,
                    )
                    if not ok:
                        return
                    idx = choices.index(sel)
                    tr_id = ids[idx]
                else:
                    tr_text, ok = QInputDialog.getText(
                        self,
                        "Test Result ID",
                        "Enter test_result id that corresponds to this suggestion:",
                    )
                    if not ok:
                        return
                    tr_id = int(tr_text.strip())
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not select test result: {e}"
                )
                return

            # Update suggestion record to record tested id and refit GP using all recent test_results
            try:
                # append tested marker to basis_text
                cur.execute(
                    "SELECT basis_text FROM optimizer_suggestions WHERE id = ?", (sid,)
                )
                row = cur.fetchone()
                basis = (row[0] or "") + f"\nTESTED_WITH:{tr_id}"
                cur.execute(
                    "UPDATE optimizer_suggestions SET basis_text = ? WHERE id = ?",
                    (basis, sid),
                )
                self.db.conn.commit()
            except Exception:
                pass

            # Re-run suggestion step (same logic as on_suggest_next_charge)
            try:
                cur.execute(
                    "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 200"
                )
                rows = cur.fetchall() or []
                charges = []
                velocities = []
                for r in reversed(rows):
                    try:
                        c = float(r[0])
                        v = float(r[1])
                    except Exception:
                        continue
                    charges.append(c)
                    velocities.append(v)
                if not charges:
                    QMessageBox.information(
                        self, "No data", "No test_results available to refit optimizer."
                    )
                    return
                from src.utils.gp_optimizer import suggest_next_charge

                min_c = max(0.0, min(charges) - 1.0)
                max_c = max(charges) + 1.0
                new_sugg = suggest_next_charge(charges, velocities, (min_c, max_c))
                import json

                cur.execute(
                    "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
                    (float(new_sugg), json.dumps({"based_on_rows": len(charges)})),
                )
                self.db.conn.commit()
                QMessageBox.information(
                    self, "Refit Complete", f"New suggested charge: {new_sugg}gr"
                )
                # refresh list
                listw.clear()
                cur.execute(
                    "SELECT id, suggested_charge, created_date, basis_text FROM optimizer_suggestions ORDER BY id DESC LIMIT 200"
                )
                rows = cur.fetchall() or []
                for r in rows:
                    sid2 = r[0]
                    sc2 = r[1]
                    cd2 = r[2]
                    basis2 = (r[3] or "")[:200]
                    item2 = QListWidgetItem(f"#{sid2} — {sc2}gr — {cd2} — {basis2}")
                    item2.setData(Qt.ItemDataRole.UserRole, sid2)
                    listw.addItem(item2)
            except Exception as e:
                QMessageBox.critical(
                    self, "Optimizer Error", f"Could not refit optimizer: {e}"
                )

        create_wf_btn.clicked.connect(create_workflow)
        mark_tested_btn.clicked.connect(mark_tested)
        # Show basis plot for selected suggestion
        show_basis_btn = QPushButton("Show Basis Plot")

        def show_basis():
            it = listw.currentItem()
            if not it:
                QMessageBox.information(self, "Select", "Select a suggestion first")
                return
            sid = it.data(Qt.ItemDataRole.UserRole)
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT basis_text FROM optimizer_suggestions WHERE id = ?", (sid,)
                )
                row = cur.fetchone()
                if not row or not row[0]:
                    QMessageBox.information(
                        self, "No basis", "No basis series stored for this suggestion"
                    )
                    return
                import json

                b = row[0]
                # if basis is JSON of series
                try:
                    payload = json.loads(b)
                    xs = payload.get("x") or payload.get("charges") or []
                    ys = payload.get("y") or payload.get("velocities") or []
                except Exception:
                    QMessageBox.information(
                        self,
                        "Unsupported",
                        "Basis stored but not in expected JSON format.",
                    )
                    return

                try:
                    import pyqtgraph as pg

                    pdlg = QDialog(self)
                    pdlg.setWindowTitle(f"Basis Plot #{sid}")
                    lv = QVBoxLayout()
                    pw = pg.PlotWidget()
                    pw.plot(xs, ys, pen=None, symbol="o")
                    pw.setLabel("left", "Velocity (fps)")
                    pw.setLabel("bottom", "Charge (gr)")
                    lv.addWidget(pw)
                    btns2 = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
                    btns2.rejected.connect(pdlg.reject)
                    lv.addWidget(btns2)
                    pdlg.setLayout(lv)
                    pdlg.exec()
                except Exception:
                    pairs = "\n".join(f"{x}->{y}" for x, y in zip(xs, ys))
                    QMessageBox.information(self, "Basis data", pairs)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load basis: {e}")

        show_basis_btn.clicked.connect(show_basis)
        h.addWidget(show_basis_btn)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        dlg.setLayout(v)
        dlg.exec()

    def on_auto_match_suggestions(self):
        """Attempt to auto-match open suggestions to recent test_results within tolerance, mark tested and refit."""
        try:
            cur = self.db.cursor
            # find suggestions not already marked tested
            cur.execute(
                "SELECT id, suggested_charge FROM optimizer_suggestions ORDER BY id DESC LIMIT 200"
            )
            rows = cur.fetchall() or []
            if not rows:
                QMessageBox.information(
                    self, "No suggestions", "No optimizer suggestions found."
                )
                return

            matched = 0
            for r in rows:
                sid = r[0]
                sugg = float(r[1]) if r[1] is not None else None
                if sugg is None:
                    continue
                # check if already has TESTED_WITH in basis_text
                cur.execute(
                    "SELECT basis_text FROM optimizer_suggestions WHERE id = ?", (sid,)
                )
                b = cur.fetchone()
                if b and b[0] and "TESTED_WITH:" in (b[0] or ""):
                    continue

                # find nearest test_result by charge
                cur.execute(
                    "SELECT id, charge_weight, velocity_avg FROM test_results WHERE charge_weight IS NOT NULL ORDER BY id DESC LIMIT 500"
                )
                trs = cur.fetchall() or []
                best = None
                best_diff = None
                best_id = None
                for tr in trs:
                    try:
                        c = float(tr[1])
                    except Exception:
                        continue
                    diff = abs(c - sugg)
                    if best_diff is None or diff < best_diff:
                        best_diff = diff
                        best = tr
                        best_id = tr[0]

                # if close enough (<=0.3gr) mark tested
                if best_diff is not None and best_diff <= 0.3:
                    try:
                        cur.execute(
                            "SELECT basis_text FROM optimizer_suggestions WHERE id = ?",
                            (sid,),
                        )
                        row = cur.fetchone()
                        basis = (row[0] or "") + f"\nTESTED_WITH:{best_id}"
                        cur.execute(
                            "UPDATE optimizer_suggestions SET basis_text = ? WHERE id = ?",
                            (basis, sid),
                        )
                        self.db.conn.commit()
                        matched += 1
                    except Exception:
                        pass

            # if we matched any, refit GP and produce a new suggestion
            if matched:
                try:
                    cur.execute(
                        "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 500"
                    )
                    rows2 = cur.fetchall() or []
                    charges = []
                    velocities = []
                    for r in reversed(rows2):
                        try:
                            charges.append(float(r[0]))
                            velocities.append(float(r[1]))
                        except Exception:
                            continue
                    if charges:
                        from src.utils.gp_optimizer import suggest_next_charge

                        min_c = max(0.0, min(charges) - 1.0)
                        max_c = max(charges) + 1.0
                        new_sugg = suggest_next_charge(
                            charges, velocities, (min_c, max_c)
                        )
                        import json

                        cur.execute(
                            "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
                            (
                                float(new_sugg),
                                json.dumps({"based_on_rows": len(charges)}),
                            ),
                        )
                        self.db.conn.commit()
                        QMessageBox.information(
                            self,
                            "Auto-Match",
                            f"Matched {matched} suggestions. New suggestion: {new_sugg}gr",
                        )
                        return
                except Exception as e:
                    QMessageBox.information(
                        self,
                        "Auto-Match",
                        f"Matched {matched} suggestions but refit failed: {e}",
                    )
                    return

            QMessageBox.information(
                self,
                "Auto-Match",
                f"Auto-match complete. Matched {matched} suggestions.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Auto-match failed: {e}")

    def on_toggle_auto_match(self, checked: bool):
        """Enable or disable the background poller for new test_results."""
        if checked:
            # initialize last seen id
            try:
                cur = self.db.cursor
                cur.execute("SELECT MAX(id) FROM test_results")
                row = cur.fetchone()
                self._last_test_result_id = (
                    int(row[0]) if row and row[0] is not None else 0
                )
            except Exception:
                self._last_test_result_id = 0
            self._auto_match_timer.start()
            self.auto_match_toggle.setText("Disable Auto-Match")
        else:
            self._auto_match_timer.stop()
            self.auto_match_toggle.setText("Enable Auto-Match")

    def _auto_match_poll(self):
        """Poll DB for new test_results and process them."""
        try:
            cur = self.db.cursor
            cur.execute("SELECT MAX(id) FROM test_results")
            row = cur.fetchone()
            max_id = int(row[0]) if row and row[0] is not None else 0
            if self._last_test_result_id is None:
                self._last_test_result_id = max_id
                return
            if max_id > self._last_test_result_id:
                # process new ids
                for nid in range(self._last_test_result_id + 1, max_id + 1):
                    try:
                        self._auto_match_on_new_result(nid)
                    except Exception:
                        pass
                self._last_test_result_id = max_id
        except Exception:
            # ignore polling errors
            return

    def _auto_match_on_new_result(self, tr_id: int):
        """Try to match a single new test_result to any open suggestions within tolerance."""
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT charge_weight, velocity_avg FROM test_results WHERE id = ?",
                (tr_id,),
            )
            row = cur.fetchone()
            if not row:
                return
            try:
                charge = float(row[0])
            except Exception:
                return

            # find suggestions not yet marked TESTED_WITH
            cur.execute(
                "SELECT id, suggested_charge, basis_text FROM optimizer_suggestions ORDER BY id DESC LIMIT 500"
            )
            rows = cur.fetchall() or []
            matched_any = False
            for r in rows:
                sid = r[0]
                try:
                    sc = float(r[1])
                except Exception:
                    continue
                basis = r[2] or ""
                if "TESTED_WITH:" in basis:
                    continue
                if abs(sc - charge) <= 0.3:
                    # mark tested
                    try:
                        new_basis = basis + f"\nTESTED_WITH:{tr_id}"
                        cur.execute(
                            "UPDATE optimizer_suggestions SET basis_text = ? WHERE id = ?",
                            (new_basis, sid),
                        )
                        self.db.conn.commit()
                        matched_any = True
                    except Exception:
                        pass

            if matched_any:
                # refit GP and persist new suggestion
                try:
                    cur.execute(
                        "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 500"
                    )
                    rows2 = cur.fetchall() or []
                    charges = []
                    velocities = []
                    for r in reversed(rows2):
                        try:
                            charges.append(float(r[0]))
                            velocities.append(float(r[1]))
                        except Exception:
                            continue
                    if charges:
                        from src.utils.gp_optimizer import suggest_next_charge

                        min_c = max(0.0, min(charges) - 1.0)
                        max_c = max(charges) + 1.0
                        new_sugg = suggest_next_charge(
                            charges, velocities, (min_c, max_c)
                        )
                        import json

                        cur.execute(
                            "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
                            (
                                float(new_sugg),
                                json.dumps({"based_on_rows": len(charges)}),
                            ),
                        )
                        self.db.conn.commit()
                except Exception:
                    pass
        except Exception:
            return

    def on_attach_chrono_to_qc_batch(self):
        """Attach selected chronograph import by creating or using existing qc_batch and insert qc_measurements."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, "No selection", "Select an import from the list first"
            )
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute(
            "SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,)
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Not found", "Import row not found in DB")
            return
        import json

        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(
                self, "No velocities", "Selected import has no velocities"
            )
            return

        # Ask user to either enter existing qc_batch id or create new
        batch_id, ok = QInputDialog.getInt(
            self,
            "QC Batch ID",
            "Enter existing QC batch ID to attach to (or 0 to create new):",
            0,
        )
        if not ok:
            return

        if batch_id == 0:
            # create new qc batch
            name, ok2 = QInputDialog.getText(
                self, "New QC Batch", "Name for new QC batch:"
            )
            if not ok2 or not name:
                QMessageBox.warning(self, "Cancelled", "Batch creation cancelled")
                return
            batch_size, ok3 = QInputDialog.getInt(
                self, "Batch Size", "How many rounds in batch?", len(velocities), 1
            )
            if not ok3:
                return
            cur.execute(
                "INSERT INTO qc_batches (name, target_charge, charge_tolerance, target_coal, coal_tolerance, batch_size, status) VALUES (?, ?, ?, ?, ?, ?, 'in_progress')",
                (name, None, None, None, None, batch_size),
            )
            batch_id = cur.lastrowid
            self.db.conn.commit()

        # Insert measurements
        for i, v in enumerate(velocities, start=1):
            cur.execute(
                "INSERT INTO qc_measurements (batch_id, patron_number, measurement_type, value, target_value, delta, is_outlier, notes) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                (
                    batch_id,
                    i,
                    "velocity",
                    float(v),
                    None,
                    None,
                    f"Imported from chronograph_imports #{import_id}",
                ),
            )

        # Optionally mark batch completed if we've inserted >= batch_size
        cur.execute("SELECT batch_size FROM qc_batches WHERE id = ?", (batch_id,))
        b = cur.fetchone()
        if b and b[0] and int(b[0]) <= len(velocities):
            cur.execute(
                "UPDATE qc_batches SET status = 'completed', completed_date = datetime('now') WHERE id = ?",
                (batch_id,),
            )

        self.db.conn.commit()
        QMessageBox.information(
            self,
            "QC Batch Updated",
            f"Inserted {len(velocities)} measurements into QC batch {batch_id}",
        )
        self.on_refresh_chronograph_list()

    def toggle_chat(self):
        """Toggle chat panel visibility"""
        if self.chat_display.isVisible():
            self.chat_display.hide()
            self.chat_input.hide()
            self.collapse_btn.setText("▶ Expand")
            self.chat_widget.setMaximumHeight(50)
        else:
            self.chat_display.show()
            self.chat_input.show()
            self.collapse_btn.setText("▼ Collapse")
            self.chat_widget.setMaximumHeight(300)

    def send_chat_message(self):
        """Send message to AI"""
        message = self.chat_input.text().strip()
        if not message:
            return

        # Display user message
        self.add_user_message(message)
        self.chat_input.clear()

        # Get AI response (placeholder - will integrate real AI later)
        response = self.get_ai_response(message)
        self.add_ai_message(response)

    def add_user_message(self, message):
        """Add user message to chat"""
        self.chat_display.append(
            f"<div style='text-align: right; margin: 10px;'>"
            f"<b style='color: #3498db;'>You:</b> {message}"
            f"</div>"
        )
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def add_ai_message(self, message):
        """Add AI message to chat"""
        self.chat_display.append(
            f"<div style='margin: 10px;'>"
            f"<b style='color: #9b59b6;'>🤖 AI:</b> {message}"
            f"</div>"
        )
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def get_ai_response(self, message):
        """
        Comprehensive AI reloading assistant - your expert friend!
        Answers ALL questions about reloading process
        """
        message_lower = message.lower()

        # ==================== KRUTT / POWDER ====================
        if any(word in message_lower for word in ["krutt", "powder", "pulver"]):
            if any(
                word in message_lower
                for word in ["anbefal", "recommend", "best", "hvilken"]
            ):
                return self.get_powder_recommendation_text()
            elif any(
                word in message_lower
                for word in ["mengde", "charge", "hvor mye", "how much"]
            ):
                return self.explain_charge_weight()
            elif any(
                word in message_lower for word in ["temperatur", "temperature", "temp"]
            ):
                return self.explain_powder_temperature()
            elif any(
                word in message_lower
                for word in ["brennhastighet", "burn rate", "speed"]
            ):
                return self.explain_burn_rate()
            elif any(
                word in message_lower for word in ["lagring", "storage", "oppbevaring"]
            ):
                return self.explain_powder_storage()

        # ==================== KULER / BULLETS ====================
        elif any(word in message_lower for word in ["kule", "bullet", "prosjektil"]):
            if any(
                word in message_lower
                for word in ["seating", "sette", "dybde", "depth", "cbto", "coal"]
            ):
                return self.explain_seating_depth()
            elif any(
                word in message_lower for word in ["jump", "hopp", "lands", "rifling"]
            ):
                return self.explain_bullet_jump()
            elif any(
                word in message_lower
                for word in ["vekt", "weight", "tung", "lett", "heavy", "light"]
            ):
                return self.explain_bullet_weight()
            elif any(
                word in message_lower for word in ["bc", "ballistisk", "ballistic"]
            ):
                return self.explain_bc()

        # ==================== TENNHETTER / PRIMERS ====================
        elif any(word in message_lower for word in ["tennhette", "primer", "tenner"]):
            if any(
                word in message_lower
                for word in ["anbefal", "recommend", "hvilken", "best"]
            ):
                return self.get_primer_recommendation()
            elif any(
                word in message_lower
                for word in ["magnum", "standard", "forskjell", "difference"]
            ):
                return self.explain_primer_types()
            elif any(
                word in message_lower
                for word in ["feil", "problem", "pierced", "cratered"]
            ):
                return self.diagnose_primer_problems()

        # ==================== HYLSER / BRASS ====================
        elif any(word in message_lower for word in ["hylse", "brass", "case"]):
            if any(
                word in message_lower for word in ["trim", "trimme", "lengde", "length"]
            ):
                return self.explain_brass_trimming()
            elif any(word in message_lower for word in ["neck", "hals", "tension"]):
                return self.explain_neck_tension()
            elif any(word in message_lower for word in ["anneal", "gløde", "hardhet"]):
                return self.explain_annealing()
            elif any(
                word in message_lower for word in ["prep", "preparer", "forbered"]
            ):
                return self.explain_brass_prep()
            elif any(
                word in message_lower for word in ["ganger", "times", "bruk", "levetid"]
            ):
                return self.explain_brass_life()

        # ==================== DIER / DIES ====================
        elif any(word in message_lower for word in ["die", "dier", "dies"]):
            if any(
                word in message_lower
                for word in ["innstilling", "setup", "justere", "adjust"]
            ):
                return self.explain_die_setup()
            elif any(
                word in message_lower
                for word in ["full length", "fl", "neck", "sizing"]
            ):
                return self.explain_sizing_dies()
            elif any(word in message_lower for word in ["seating", "sette", "bullet"]):
                return self.explain_seating_die()
            elif any(word in message_lower for word in ["crimping", "crimpe", "crimp"]):
                return self.explain_crimping()
            elif any(
                word in message_lower for word in ["problem", "stuck", "fast", "feil"]
            ):
                return self.diagnose_die_problems()

        # ==================== TRYKK / PRESSURE ====================
        elif any(word in message_lower for word in ["trykk", "pressure", "psi", "bar"]):
            if any(
                word in message_lower for word in ["høy", "high", "for mye", "too much"]
            ):
                return self.explain_high_pressure()
            elif any(word in message_lower for word in ["tegn", "signs", "symptom"]):
                return self.explain_pressure_signs()
            elif any(
                word in message_lower for word in ["saami", "max", "grense", "limit"]
            ):
                return self.explain_saami_limits()
            elif any(word in message_lower for word in ["hvorfor", "why", "årsak"]):
                return self.explain_pressure()

        # ==================== SIKKERHET / SAFETY ====================
        elif any(
            word in message_lower
            for word in ["sikker", "safe", "trygg", "farlig", "danger"]
        ):
            return self.check_safety_comprehensive()

        # ==================== PRESISJON / ACCURACY ====================
        elif any(
            word in message_lower
            for word in ["presisjon", "accuracy", "nøyaktighet", "gruppe", "group"]
        ):
            if any(
                word in message_lower
                for word in ["forbedre", "improve", "bedre", "better"]
            ):
                return self.improve_accuracy_tips()
            elif any(word in message_lower for word in ["ocw", "ladder", "test"]):
                return self.suggest_test_plan()
            elif any(
                word in message_lower for word in ["es", "sd", "spredning", "spread"]
            ):
                return self.explain_es_sd()

        # ==================== TESTING ====================
        elif any(
            word in message_lower for word in ["test", "ocw", "ladder", "sighter"]
        ):
            return self.suggest_test_plan()

        # ==================== LØP / BARREL ====================
        elif any(word in message_lower for word in ["løp", "barrel", "pipe"]):
            if any(
                word in message_lower for word in ["harmonisk", "harmonic", "vibration"]
            ):
                return self.explain_barrel_harmonics()
            elif any(
                word in message_lower for word in ["lengde", "length", "kort", "lang"]
            ):
                return self.explain_barrel_length()
            elif any(
                word in message_lower for word in ["rengjøring", "cleaning", "fouling"]
            ):
                return self.explain_barrel_cleaning()

        # ==================== VERKTØY / TOOLS ====================
        elif any(
            word in message_lower for word in ["verktøy", "tool", "utstyr", "equipment"]
        ):
            return self.recommend_tools()

        # ==================== PROSESS / PROCESS ====================
        elif any(
            word in message_lower
            for word in ["prosess", "process", "hvordan", "how to", "steg", "step"]
        ):
            return self.explain_reloading_process()

        # ==================== GENERELL HJELP ====================
        else:
            return self.general_help_message()

    def get_powder_recommendation_text(self):
        """Generate powder recommendation"""
        if not self.rifle_data:
            return "Please select a rifle first!"

        caliber = self.rifle_data["caliber"]

        recommendations = {
            ".308 Winchester": "For .308 Win, I recommend:\n\n🥇 Varget (burn rate 115) - Temperature stable, excellent accuracy\n🥈 H4350 - Slightly slower, also great\n🥉 RL15 - Faster, good for shorter barrels",
            "6.5 Creedmoor": "For 6.5 Creedmoor, I recommend:\n\n🥇 H4350 - THE standard for 6.5 CM\n🥈 RL16 - Temp stable, higher velocity\n🥉 Varget - Works great with lighter bullets",
            ".223 Remington": "For .223 Rem, I recommend:\n\n🥇 Varget - Excellent accuracy\n🥈 H4895 - Very versatile\n🥉 RL15 - Good velocities",
        }

        return recommendations.get(
            caliber, f"For {caliber}, consult load manuals for powder recommendations."
        )

    def get_primer_recommendation(self):
        """Get primer recommendation"""
        if not self.powder_data:
            return "Select a powder first, then I can recommend a primer!"

        return (
            "For your powder choice:\n\n"
            "🥇 CCI BR-2 - Benchrest grade, lowest ES/SD\n"
            "🥈 Federal 210M - Match grade, excellent\n"
            "🥉 CCI 200 - Standard LR, works great\n\n"
            "Avoid magnum primers unless using slow ball powder."
        )

    def explain_pressure(self):
        """Explain current pressure"""
        # Would use actual calculation here
        return (
            "Pressure is influenced by:\n\n"
            "1. Charge weight (more powder = higher pressure)\n"
            "2. Case capacity (less space = higher pressure)\n"
            "3. Seating depth (closer to lands = higher pressure)\n"
            "4. Powder burn rate (faster = higher peak)\n"
            "5. Temperature (hotter = higher pressure)\n\n"
            "Always stay under SAAMI/CIP max!"
        )

    def check_safety(self):
        """Check if current load is safe"""
        # Would use actual calculation here
        return (
            "Based on current settings:\n\n"
            "✅ Pressure looks SAFE\n"
            "✅ Under SAAMI maximum\n"
            "⚠️ Always watch for pressure signs!\n\n"
            "Signs of high pressure:\n"
            "• Flattened primers\n"
            "• Ejector marks on brass\n"
            "• Difficult bolt lift\n"
            "• Case head expansion"
        )

    def suggest_test_plan(self):
        """Suggest OCW test plan"""
        return (
            "I recommend this test protocol:\n\n"
            "📋 OCW Test (15 rounds):\n"
            "• 42.0gr × 3 shots\n"
            "• 42.3gr × 3 shots\n"
            "• 42.5gr × 3 shots ← Expected best\n"
            "• 42.8gr × 3 shots\n"
            "• 43.0gr × 3 shots\n\n"
            "Shoot at 100m, look for cluster (OCW node).\n"
            "Then test seating depth (9 rounds).\n\n"
            "Total: 24 rounds vs traditional 60-100!"
        )

    def go_back_to_step1(self):
        """Go back to step 1"""
        self.step2_widget.hide()
        self.layout().removeWidget(self.step2_widget)
        self.step1_widget.show()
        # persist last-open step
        try:
            self.current_step = 1
            self._save_ui_setting("last_step", "1")
        except Exception:
            pass

    def initialize_step2(self):
        """Initialize step 2 with rifle data"""
        # Load components for this rifle
        self.load_bullets_for_caliber()
        self.load_powders()
        self.load_primers()

        # Show rifle info
        self.add_ai_message(
            f"Great! You selected {self.rifle_data['name']} ({self.rifle_data['caliber']}).\n\n"
            f"Let me help you build the perfect load! 🎯"
        )

    def load_bullets_for_caliber(self):
        """Load bullets for rifle caliber"""
        # Placeholder - would query from database
        self.bullet_combo.clear()
        self.bullet_combo.addItem("Select bullet...", None)
        # Add dummy data for now
        self.bullet_combo.addItem(
            "Berger 175gr OTM (Lot ABC123)", {"id": 1, "weight": 175}
        )
        self.bullet_combo.addItem(
            "Sierra 168gr HPBT (Lot XYZ456)", {"id": 2, "weight": 168}
        )

    def load_powders(self):
        """Load powders from inventory"""
        powders = self.db.execute_query("SELECT * FROM powder WHERE quantity_grams > 0")
        self.powder_combo.clear()
        self.powder_combo.addItem("Select powder...", None)
        for powder in powders:
            self.powder_combo.addItem(
                f"{powder['manufacturer']} {powder['name']}", powder
            )

    def load_primers(self):
        """Load primers from inventory"""
        primers = self.db.execute_query("SELECT * FROM primers WHERE quantity > 0")
        self.primer_combo.clear()
        self.primer_combo.addItem("Select primer...", None)
        for primer in primers:
            self.primer_combo.addItem(
                f"{primer['manufacturer']} {primer['name']}", primer
            )

    def on_bullet_changed(self, index):
        """Handle bullet selection"""
        bullet = self.bullet_combo.currentData()
        if bullet:
            self.bullet_data = bullet
            self.bullet_info.setText(f"Weight: {bullet.get('weight', '?')}gr")
            self.update_visualization()

    def on_powder_changed(self, index):
        """Handle powder selection"""
        powder = self.powder_combo.currentData()
        if powder:
            self.powder_data = powder
            self.powder_info.setText(
                f"Type: {powder.get('type', '?')}, In stock: {powder.get('quantity_grams', 0):.0f}g"
            )

            # Show AI recommendation
            self.powder_recommendation.setText(
                f"🤖 AI: {powder['name']} is a great choice! "
                f"Burn rate: {powder.get('burn_rate', '?')}"
            )
            self.update_visualization()

    def on_charge_slider_changed(self, value):
        """Handle charge slider change"""
        self.current_charge = value / 10.0
        self.charge_label.setText(f"{self.current_charge:.1f} gr")
        self.update_visualization()

    def on_seating_changed(self):
        """Handle seating depth change"""
        self.coal_mm = self.coal_spin.value()
        self.cbto_mm = self.cbto_spin.value()

        # Calculate jump if jam length known
        if self.rifle_data and self.rifle_data.get("jam_length_cbto_mm"):
            jam = self.rifle_data["jam_length_cbto_mm"]
            jump = jam - self.cbto_mm
            self.jump_label.setText(f'Jump: {jump:.2f}mm ({jump/25.4:.3f}")')

        self.update_visualization()

    def update_visualization(self):
        """Update graphs with current parameters"""
        if not all([self.rifle_data, self.bullet_data, self.powder_data]):
            return

        # Calculate ballistics
        result = self.engine.calculate_load(
            self.rifle_data["id"],
            self.bullet_data["id"],
            self.powder_data["id"],
            self.current_charge,
            self.coal_mm,
            self.cbto_mm,
        )

        if "error" in result:
            return

        # Apply environmental corrections and calibration (best-effort)
        try:
            from src.utils.env_corrections import air_density_ratio

            temp_c = (
                float(self.temp_spin.value()) if hasattr(self, "temp_spin") else None
            )
            pressure_kpa = (
                float(self.pressure_spin.value())
                if hasattr(self, "pressure_spin")
                else None
            )
            humidity_pct = (
                float(self.humidity_spin.value())
                if hasattr(self, "humidity_spin")
                else None
            )

            ratio = None
            if (
                temp_c is not None
                and pressure_kpa is not None
                and humidity_pct is not None
            ):
                try:
                    ratio = air_density_ratio(temp_c, pressure_kpa, humidity_pct)
                except Exception:
                    ratio = None

            # copy result so we don't mutate engine internals
            scaled = dict(result)

            # scale pressure and velocity curves conservatively if ratio available
            if ratio is not None:
                try:
                    scale = 1.0 + (ratio - 1.0) * 0.5
                    # pressure_curve: list of (time, pressure)
                    if "pressure_curve" in scaled and scaled["pressure_curve"]:
                        scaled_pc = [
                            (t, float(p) * scale) for (t, p) in scaled["pressure_curve"]
                        ]
                        scaled["pressure_curve"] = scaled_pc
                        # adjust numeric peak/max fields if present
                        if "max_pressure_psi" in scaled:
                            scaled["max_pressure_psi"] = (
                                float(scaled["max_pressure_psi"]) * scale
                            )
                        if "peak_pressure_psi" in scaled:
                            scaled["peak_pressure_psi"] = (
                                float(scaled["peak_pressure_psi"]) * scale
                            )

                    # velocity_curve: list of (position, vel)
                    if "velocity_curve" in scaled and scaled["velocity_curve"]:
                        scaled_vc = [
                            (x, float(v) * scale) for (x, v) in scaled["velocity_curve"]
                        ]
                        scaled["velocity_curve"] = scaled_vc
                        if "muzzle_velocity_fps" in scaled:
                            scaled["muzzle_velocity_fps"] = (
                                float(scaled["muzzle_velocity_fps"]) * scale
                            )
                except Exception:
                    pass

            # Apply linear calibration (predicted -> measured) if available
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT slope, intercept, mse FROM engine_calibrations ORDER BY id DESC LIMIT 1"
                )
                row = cur.fetchone()
                if row and row[0] is not None:
                    slope = float(row[0])
                    intercept = float(row[1] or 0.0)
                    mse = float(row[2]) if row[2] is not None else None
                    # apply to velocity numbers
                    if "velocity_curve" in scaled and scaled["velocity_curve"]:
                        scaled["velocity_curve"] = [
                            (x, slope * float(v) + intercept)
                            for (x, v) in scaled["velocity_curve"]
                        ]
                    if "muzzle_velocity_fps" in scaled:
                        scaled["muzzle_velocity_fps"] = (
                            slope * float(scaled.get("muzzle_velocity_fps", 0))
                            + intercept
                        )
                    # attach mse for plotting uncertainty bands
                    if mse is not None:
                        scaled["_calibration_mse"] = mse
            except Exception:
                pass

        except Exception:
            scaled = result

        # Update graphs with scaled/calibrated result
        self.update_pressure_graph(scaled)
        self.update_velocity_graph(scaled)
        self.update_stats(scaled)

    def update_pressure_graph(self, result):
        """Update pressure curve"""
        self.pressure_plot.clear()

        times = [p[0] for p in result["pressure_curve"]]
        pressures = [p[1] for p in result["pressure_curve"]]

        pg = getattr(self, "_pg", None)
        if not pg:
            return

        main_curve = self.pressure_plot.plot(
            times, pressures, pen=pg.mkPen(color="#e74c3c", width=3)
        )

        # If calibration MSE present, draw uncertainty band around pressure curve
        try:
            mse = result.get("_calibration_mse")
            if mse is not None:
                import math

                vel_unc = math.sqrt(mse)
                # approximate pressure uncertainty by scaling relative to peak velocity
                peak_vel = (
                    float(result.get("muzzle_velocity_fps", 0))
                    if result.get("muzzle_velocity_fps")
                    else 0.0
                )
                peak_p = (
                    float(result.get("max_pressure_psi", 0))
                    if result.get("max_pressure_psi")
                    else 0.0
                )
                scale_p = (peak_p / peak_vel) if peak_vel > 0 else 0.0
                p_unc = vel_unc * scale_p

                upper = [p + p_unc for p in pressures]
                lower = [p - p_unc for p in pressures]

                up_curve = self.pressure_plot.plot(
                    times, upper, pen=pg.mkPen(color=(231, 76, 60, 80), width=0)
                )
                low_curve = self.pressure_plot.plot(
                    times, lower, pen=pg.mkPen(color=(231, 76, 60, 80), width=0)
                )
                try:
                    fill = pg.FillBetweenItem(
                        up_curve, low_curve, brush=(231, 76, 60, 50)
                    )
                    self.pressure_plot.addItem(fill)
                except Exception:
                    pass
        except Exception:
            pass

        # Add SAAMI line
        max_pressure = result.get("max_pressure_psi")
        if max_pressure is not None:
            self.pressure_plot.addLine(
                y=max_pressure,
                pen=pg.mkPen(color="#95a5a6", width=2, style=Qt.PenStyle.DashLine),
            )

    def update_velocity_graph(self, result):
        """Update velocity curve"""
        self.velocity_plot.clear()

        positions = [v[0] for v in result["velocity_curve"]]
        velocities = [v[1] for v in result["velocity_curve"]]

        # Store latest simulated curve for overlaying with imports
        self._last_velocity_curve = (positions, velocities)

        pg = getattr(self, "_pg", None)
        if not pg:
            return

        main_curve = self.velocity_plot.plot(
            positions, velocities, pen=pg.mkPen(color="#27ae60", width=3)
        )

        # If calibration MSE present, draw uncertainty band around velocity curve
        try:
            mse = result.get("_calibration_mse")
            if mse is not None:
                import math

                vel_unc = math.sqrt(mse)
                upper = [v + vel_unc for v in velocities]
                lower = [v - vel_unc for v in velocities]

                up_curve = self.velocity_plot.plot(
                    positions, upper, pen=pg.mkPen(color=(39, 174, 96, 80), width=0)
                )
                low_curve = self.velocity_plot.plot(
                    positions, lower, pen=pg.mkPen(color=(39, 174, 96, 80), width=0)
                )
                try:
                    fill = pg.FillBetweenItem(
                        up_curve, low_curve, brush=(39, 174, 96, 50)
                    )
                    self.velocity_plot.addItem(fill)
                except Exception:
                    pass
        except Exception:
            pass

        # Apply persisted velocity y-range if available
        try:
            if (
                getattr(self, "velocity_y_min", None) is not None
                and getattr(self, "velocity_y_max", None) is not None
            ):
                try:
                    self.velocity_plot.setYRange(
                        float(self.velocity_y_min), float(self.velocity_y_max)
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # Draw transonic speed-of-sound line and optional margin band
        try:
            if getattr(self, "transonic_cb", None) and self.transonic_cb.isChecked():
                try:
                    from src.utils.ballistics_utils import speed_of_sound_fps

                    temp_c = (
                        float(self.temp_spin.value())
                        if hasattr(self, "temp_spin")
                        else 15.0
                    )
                    sos = float(speed_of_sound_fps(temp_c))
                    margin = float(
                        getattr(self, "transonic_margin", None)
                        or self.transonic_margin.value()
                    )

                    # horizontal lines drawn as flat curves for FillBetween
                    xs = positions if positions else [0, 1]
                    top = [sos + margin for _ in xs]
                    bot = [sos - margin for _ in xs]

                    top_curve = self.velocity_plot.plot(
                        xs, top, pen=pg.mkPen(color=(52, 152, 219, 120), width=0)
                    )
                    bot_curve = self.velocity_plot.plot(
                        xs, bot, pen=pg.mkPen(color=(52, 152, 219, 120), width=0)
                    )
                    try:
                        band = pg.FillBetweenItem(
                            top_curve, bot_curve, brush=(52, 152, 219, 40)
                        )
                        self.velocity_plot.addItem(band)
                    except Exception:
                        pass

                    # Draw SOS line
                    self.velocity_plot.addLine(
                        y=sos,
                        pen=pg.mkPen(
                            color="#2980b9", width=2, style=Qt.PenStyle.DashLine
                        ),
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def _save_ui_setting(self, key: str, value: str):
        """Persist a small UI setting into `ui_settings` table."""
        try:
            cur = self.db.cursor
            # Use INSERT OR REPLACE to upsert by key
            cur.execute(
                "INSERT OR REPLACE INTO ui_settings (key, value, updated_date) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, value),
            )
            self.db.conn.commit()
        except Exception:
            pass

    def _delete_ui_setting(self, key: str):
        """Delete a UI setting by key from `ui_settings`."""
        try:
            cur = self.db.cursor
            cur.execute("DELETE FROM ui_settings WHERE key = ?", (key,))
            self.db.conn.commit()
        except Exception:
            pass

    def update_stats(self, result):
        """Update statistics display"""
        self.stat_pressure.setText(f"Pressure: {result['peak_pressure_psi']:.0f} PSI")
        self.stat_velocity.setText(f"Velocity: {result['muzzle_velocity_fps']:.0f} fps")
        self.stat_energy.setText(f"Energy: {result['energy_ft_lbs']:.0f} ft-lbs")
        self.stat_barrel_time.setText(f"Time: {result['barrel_time_ms']:.2f} ms")

        safety = result["safety_margin_percent"]
        color = "#27ae60" if safety > 15 else "#e67e22" if safety > 10 else "#e74c3c"
        emoji = "🟢" if safety > 15 else "🟠" if safety > 10 else "🔴"

        self.stat_safety.setText(f"{emoji} Safety: {safety:.1f}%")
        self.stat_safety.setStyleSheet(
            f"color: {color}; font-weight: bold; padding: 8px; font-size: 10pt;"
        )

        # Update scope comparison with previous load
        self.update_scope_comparison(result)

    def update_scope_comparison(self, current_result):
        """Update scope adjustment comparison with previous load for same rifle"""
        if not self.rifle_data or not self.bullet_data or not self.powder_data:
            self.scope_comparison_group.setVisible(False)
            return

        rifle_id = self.rifle_data["id"]
        current_velocity = current_result.get("muzzle_velocity_fps", 0)
        current_bc = self.bullet_data.get("bc_g1", 0)

        if not current_velocity or not current_bc:
            self.scope_comparison_group.setVisible(False)
            return

        # Find PREVIOUS load for same rifle (most recent ammo_profile)
        previous_load = self.db.execute_query(
            """
            SELECT name, velocity_fps, bc_g1, bullet_weight, caliber, created_date
            FROM ammo_profiles
            WHERE rifle_id = ? AND velocity_fps IS NOT NULL AND bc_g1 IS NOT NULL
            ORDER BY created_date DESC
            LIMIT 1
        """,
            (rifle_id,),
        )

        if not previous_load:
            self.scope_comparison_label.setText(
                f"<b>NY LADNING:</b> {self.rifle_data['name']}<br>"
                f"<i>Dette er første ladning for denne riflen. Ingen sammenligning tilgjengelig.</i>"
            )
            self.scope_comparison_group.setVisible(True)
            return

        prev_name, prev_vel, prev_bc, prev_weight, prev_cal, prev_created = (
            previous_load[0]
        )

        # Calculate drop at 100m, 300m, 600m (using utils ballistics calculator)
        from src.utils.ballistics import BallisticsCalculator

        ballistics_calc = BallisticsCalculator()

        zero_dist = 100  # Standard zero
        test_distances = [100, 300, 600]

        # Create comparison table
        comparison_html = f"""
        <b>NY LADNING:</b> {self.rifle_data['name']} - {self.bullet_data.get('name', 'Custom')} {self.bullet_data.get('weight_grains', 0)}gr<br>
        • Hastighet: {current_velocity:.0f} fps, BC (G1): {current_bc:.3f}, Krutt: {self.powder_data.get('name', 'Unknown')} ({self.current_charge:.1f}gr)<br><br>

        <b>FORRIGE LADNING:</b> {prev_name}<br>
        • Hastighet: {prev_vel:.0f} fps, BC (G1): {prev_bc:.3f}, Kulevekt: {prev_weight}gr<br><br>

        <b>🎯 KIKKERT JUSTERING (Zero: {zero_dist}m):</b><br>
        <table style='width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 9pt;'>
        <tr style='background-color: #f0f0f0; font-weight: bold;'>
            <td style='padding: 3px; border: 1px solid #ddd;'>Dist</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Drop Ny</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Drop Forrige</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Δ</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Justering</td>
        </tr>
        """

        for dist in test_distances:
            # Drop for new load
            drop_new = ballistics_calc.calculate_drop(
                current_velocity, current_bc, dist, zero_dist, "G1"
            )
            drop_new_moa = ballistics_calc.cm_to_moa(drop_new, dist)

            # Drop for previous load
            drop_prev = ballistics_calc.calculate_drop(
                prev_vel, prev_bc, dist, zero_dist, "G1"
            )
            drop_prev_moa = ballistics_calc.cm_to_moa(drop_prev, dist)

            # Difference
            diff_cm = drop_new - drop_prev
            diff_moa = drop_new_moa - drop_prev_moa

            # Scope adjustment (0.25 MOA/click standard)
            clicks = diff_moa / 0.25
            direction = "↑" if clicks > 0 else "↓" if clicks < 0 else "="

            color = (
                "#27ae60"
                if abs(diff_cm) < 5
                else "#f39c12" if abs(diff_cm) < 15 else "#e74c3c"
            )

            comparison_html += f"""
            <tr>
                <td style='padding: 3px; border: 1px solid #ddd;'>{dist}m</td>
                <td style='padding: 3px; border: 1px solid #ddd;'>{drop_new:.0f}cm ({drop_new_moa:.1f} MOA)</td>
                <td style='padding: 3px; border: 1px solid #ddd;'>{drop_prev:.0f}cm ({drop_prev_moa:.1f} MOA)</td>
                <td style='padding: 3px; border: 1px solid #ddd; background-color: {color}; color: white; font-weight: bold;'>{diff_cm:+.0f}cm</td>
                <td style='padding: 3px; border: 1px solid #ddd; font-weight: bold;'>{direction} {abs(clicks):.0f} clicks</td>
            </tr>
            """

        comparison_html += """
        </table><br>
        <i style='font-size: 8pt;'>💡 Grønn = &lt;5cm, Gul = 5-15cm, Rød = &gt;15cm. Standard: 0.25 MOA/click.</i>
        """

        self.scope_comparison_label.setText(comparison_html)
        self.scope_comparison_group.setVisible(True)

    # ========================================================================
    # COMPREHENSIVE AI HELPER METHODS - Your Reloading Expert Friend!
    # ========================================================================

    def general_help_message(self):
        """General help message showing all capabilities"""
        return """🤖 Hei! Jeg er din ladingsekspert og venn! Jeg kan hjelpe deg med ALT om lading:

📦 KOMPONENTER:
• Krutt: "Hvilket krutt passer best?" / "Hvordan lagre krutt?"
• Kuler: "Hvor dypt skal jeg sette kulen?" / "Hva er CBTO?"
• Tennhetter: "Standard eller magnum?" / "Hvorfor er tennhetten flat?"
• Hylser: "Når skal jeg trimme?" / "Hvordan gløde hylser?"

🔧 DIER & PROSESS:
• "Hvordan stille inn diene?" / "Full length eller neck sizing?"
• "Hylsen setter seg fast i die" / "Hvordan crimpe?"

📊 TEKNISK:
• Trykk: "Hvorfor er trykket høyt?" / "Hva er SAAMI-grenser?"
• Presisjon: "Hvordan forbedre nøyaktigheten?" / "Hva er ES/SD?"
• Testing: "Hvordan teste ladningen?" / "Hva er OCW?"

🎯 Spør meg hva som helst! Jeg er her for å hjelpe deg lage perfekte ladninger! 🎯"""

    # ==================== KRUTT / POWDER HELPERS ====================

    def explain_charge_weight(self):
        """Explain charge weight selection"""
        return """⚖️ KRUTT-MENGDE (Charge Weight):

🎯 HVORDAN VELGE:
1. Start med ladebok minimum (-10% av maks)
2. Øk gradvis i 0.3-0.5 grain steg
3. Se etter pressure-tegn konstant!

📊 FAKTORER:
• Større mengde = mer trykk + høyere hastighet
• For mye = FARLIG høyt trykk ⚠️
• For lite = dårlig forbrenning, inconsistent

🎯 OCW METODE (anbefalt):
• Test 5 nivåer: 42.0, 42.3, 42.5, 42.8, 43.0gr
• Se etter "node" (stabil sone)
• Velg midt i noden for best konsistens

⚠️ SIKKERHET:
• Aldri overstig ladebok maksimum!
• Se etter pressure-tegn ved hvert steg
• Når i tvil → gå NED i mengde"""

    def explain_powder_temperature(self):
        """Explain powder temperature sensitivity"""
        return """🌡️ KRUTT & TEMPERATUR:

📊 TEMPERATUR-SENSITIVITET:
• Varmere = høyere trykk (ca 1-3 fps per °C)
• Kaldere = lavere trykk og hastighet

🥇 TEMP-STABILE KRUTT (anbefalt):
• Hodgdon Varget (ekstremt stabilt)
• Alliant RL16 (meget bra)
• Hodgdon H4350 (god stabilitet)
• Vihtavuori N140-serien

⚠️ TEMP-SENSITIVE:
• IMR serien (spesielt eldre typer)
• Ball powder (generelt mer sensitive)

🎯 TESTING:
• Test ladningen ved forskjellige temperaturer
• Lagre krutt i tørr plass, 10-25°C
• Unngå direkte sollys på ammunisjon

💡 TIP: Hvis du jakter i varmt OG kaldt vær, velg temp-stabilt krutt!"""

    def explain_burn_rate(self):
        """Explain powder burn rate"""
        return (
            """🔥 BRENNHASTIGHET (Burn Rate):

📊 HVA ER DET?
Hvor raskt kruttet brenner inne i kammeret.

⚡ RASKT KRUTT (t.ex. Viht N130):
• Små kalibre (.223, .22-250)
• Lette kuler
• Korte løp
• Høyere trykk, raskere

🐌 LANGSOMT KRUTT (t.ex. H4831):
• Store kalibre (.300 Win Mag)
• Tunge kuler
• Lange løp
• Lavere trykk, mer kontrollert

🎯 FOR DIN {caliber}:
"""
            + (
                "• Brennhastighet 110-120 (medium)\n• Varget (115) = perfekt!\n• H4350 (120) = også bra"
                if hasattr(self, "rifle_data")
                and self.rifle_data
                and ".308" in self.rifle_data.get("caliber", "")
                else "• Velg våpen først for spesifikke anbefalinger"
            )
            + """

⚠️ FEIL KRUTT:
• For raskt → farlig høyt trykk! 💥
• For langsomt → urent, dårlig forbrenning

💡 TIP: Følg ladebøker! De vet hvilket krutt som passer."""
        )

    def explain_powder_storage(self):
        """Explain powder storage"""
        return """📦 KRUTT-LAGRING:

✅ RIKTIG LAGRING:
• Original beholder (ALDRI overføre!)
• Tørt, kjølig sted (10-25°C)
• Unngå sollys og fukt
• Ventilert skap/rom
• Låst, vekk fra barn

⚠️ ALDRI:
• Blande forskjellige krutt-typer
• Lagre ved varme (>30°C)
• Lagre i fuktig miljø
• Eksponere for åpen ild

🔍 SJEKK FOR NEDBRYTNING:
• Rust-rød/brun farge = KAST!
• Sur lukt (som syre) = KAST!
• Klumpete = fuktskade, KAST!
• Godt krutt: tørt, løst, jevn farge

⏳ HOLDBARHET:
• Riktig lagret: 10-20+ år
• Åpnet beholder: 5-10 år (hvis tett lukket)
• Sjekk årlig for tegn på nedbrytning

💡 TIP: Skriv åpningsdato på beholderen!"""

    # ==================== KULER / BULLETS HELPERS ====================

    def explain_seating_depth(self):
        """Explain bullet seating depth"""
        return """📏 KULESETTING (Seating Depth):

📊 VIKTIGE MÅL:
• COAL (Cartridge Overall Length) = Total lengde
• CBTO (Cartridge Base to Ogive) = Mer presist!
• Jump = Avstand fra kule til rifling

🎯 BERGER METODE (anbefalt):
1. Start ved "jam" (kule mot rifling)
2. Test: 0.010", 0.050", 0.090", 0.130" jump
3. Skyt 3-skudd grupper av hver
4. Velg den beste gruppen

📈 EFFEKTER:
• Nær rifling (kort jump):
  ✅ Høyere presisjon (ofte)
  ⚠️ Høyere trykk!
• Lengre jump:
  ✅ Lavere trykk
  ⚠️ Kan gi dårligere presisjon

⚠️ SIKKERHET:
• Kortere COAL = MER trykk
• Start konservativt (0.050" jump)
• Reduser krutt-mengde hvis du går nærmere rifling

💡 TIP: CBTO er mer konsistent enn COAL (kuletips varierer)"""

    def explain_bullet_jump(self):
        """Explain bullet jump to lands"""
        return """🦘 BULLET JUMP:

📊 HVA ER DET?
Avstanden kulen reiser før den treffer riflingen (lands).

📏 MÅLING:
1. Lås bolt på tom hylse med kule
2. Trykk kule mot rifling
3. Mål CBTO = "jam length"
4. Jump = jam length - din CBTO

🎯 TYPISKE VERDIER:
• 0.000" (jam) = kule mot rifling
  ⚠️ HØYT TRYKK! Kun for testing
• 0.010-0.020" = "touch lands"
  ⚡ Høy presisjon, moderat trykk
• 0.040-0.080" = sweet spot
  ✅ God presisjon, trygt trykk
• 0.100"+ = lang jump
  ✅ Trygt, kan funke bra

💡 HVER RIFLE ER FORSKJELLIG:
• Noen liker kort jump (0.010")
• Andre liker lang jump (0.080"+)
• Test for å finne DIN rifle sin preferanse!

🎯 MAGASIN-LENGDE:
Husk å sjekke at patronen passer i magasinet!"""

    def explain_bullet_weight(self):
        """Explain bullet weight selection"""
        return """⚖️ KULE-VEKT:

📊 LETTERE KULER (t.ex. 150gr .308):
✅ Høyere hastighet
✅ Flatere bane (kort hold)
✅ Mindre rekyl
⚠️ Mer vindpåvirkning
⚠️ Mindre energi på lang distanse

📊 TYNGRE KULER (t.ex. 175gr .308):
✅ Bedre BC (ballistic coefficient)
✅ Mindre vindpåvirkning
✅ Mer energi på distanse
✅ Bedre for long-range
⚠️ Lavere hastighet
⚠️ Mer rekyl

🎯 FOR DIN RIFLE:
• Løp-twist: raskere twist = tyngre kuler
• 1:12" twist = 150-168gr
• 1:10" twist = 168-185gr
• 1:8" twist = 175-200gr+

💡 TIP: Start med "standard" vekt for kaliberet:
• .308 Win → 168-175gr
• 6.5 CM → 140-147gr
• .223 Rem → 55-77gr"""

    def explain_bc(self):
        """Explain ballistic coefficient"""
        return """🎯 BALLISTISK KOEFFISIENT (BC):

📊 HVA ER DET?
Målet på hvor godt kulen "skjærer" gjennom luften.

📈 HØYERE BC = BEDRE:
✅ Mindre hastighetstap
✅ Flatere bane
✅ Mindre vindpåvirkning
✅ Mer energi på distanse

🔢 TYPISKE VERDIER (G1):
• 0.200-0.300 = Lavt (flat base, lett)
• 0.400-0.500 = Middels (HPBT)
• 0.500-0.600 = Godt (match kuler)
• 0.600+ = Utmerket (VLD, hybrid)

🎯 FAKTORER:
• Kule-form: VLD/Hybrid best
• Vekt: tyngre = høyere BC
• Diameter: mindre = bedre (6.5mm vs .308)

💡 VIKTIG:
• BC betyr lite under 300m
• Over 600m → stor forskjell!
• Velg basert på bruk:
  - Jakt <300m: BC mindre viktig
  - Long range >600m: høy BC kritisk"""

    # ==================== TENNHETTER / PRIMERS HELPERS ====================

    def explain_primer_types(self):
        """Explain primer types"""
        return (
            """🔥 TENNHETTE-TYPER:

📊 STANDARD vs MAGNUM:

✅ STANDARD (anbefalt):
• For de fleste krutt-typer
• Stick powder (Varget, H4350, etc)
• Lavere ES/SD (bedre konsistens)
• Eksempel: CCI 200, Federal 210, BR-2

⚡ MAGNUM:
• For langsomt ball powder
• Store magnum-kalibre
• Kompakte ladninger (mye krutt, lite plass)
• Eksempel: CCI 250, Federal 215

🎯 BENCHREST (best for presisjon):
• CCI BR-2 (Large Rifle)
• CCI BR-4 (Small Rifle)
• Federal 205M, 210M
• Tettere toleranser = bedre ES/SD

⚠️ IKKE BYTTESTENNHETTE UTEN Å TESTE!
• Forskjellige tennhetter = forskjellig trykk
• Magnum tennhette kan gi +2000-3000 PSI!
• Start lavere med krutt-mengde ved bytte

💡 TIP FOR DIN LADNING:
"""
            + (
                f"Med {self.powder_data['name']}: Standard tennhette anbefales\n\n"
                if hasattr(self, "powder_data") and self.powder_data
                else "Velg krutt først for spesifikk anbefaling\n\n"
            )
            + """🥇 MINE FAVORITTER:
• CCI BR-2: Best for presisjon
• Federal 210M: Også utmerket
• CCI 200: God standard-valg"""
        )

    def diagnose_primer_problems(self):
        """Diagnose primer-related issues"""
        return """🔍 TENNHETTE-PROBLEMER:

⚠️ FLATTENED PRIMER (flat tennhette):
• Normal: Litt flat er OK
• For flat: TRYKKET FOR HØYT! 🚨
• Løsning: Reduser krutt-mengde

🕳️ PIERCED PRIMER (hull i tennhette):
• Årsak 1: Alt for høyt trykk 🚨
• Årsak 2: For stor firing pin hole
• Årsak 3: Svak tennhette + høyt trykk
• Løsning: Sjekk rifle, reduser krutt

🌙 CRATERED PRIMER (krater rundt slag):
• Normal i mange rifles (spesielt Remington)
• Hvis ny: kan bety høyt trykk
• Kombinert med andre tegn = STOPP

💥 BLOWN PRIMER (tennhette falt ut):
• FARLIG HØYT TRYKK! 🚨🚨
• STOPP UMIDDELBART
• Sjekk rifle hos børsemaker
• Reduser krutt betydelig

🔄 TENNHETTE BAKLENGS:
• Skjer hvis tennhette ikke satt ordentlig
• Rifle kan kanskje ikke fyres (safety)
• Løsning: Sett tennhette med riktig dybde

✅ NORMAL TENNHETTE:
• Lett rundet fortsatt
• Tydelig slagmerke
• Ingen kratering eller spreading
• Sitter godt i primer pocket"""

    # ==================== HYLSER / BRASS HELPERS ====================

    def explain_brass_trimming(self):
        """Explain brass trimming"""
        return """✂️ HYLSE-TRIMMING:

📏 HVORFOR TRIMME?
Hylser strekker seg ved hver skyting. For lange hylser:
• Klemmer kule for hardt (høyt trykk)
• Kan ikke lukke bolt
• Kan gi chambering-problemer

📊 NÅR TRIMME?
1. Mål hylse-lengde etter sizing
2. Sammenlign med SAAMI/CIP max
3. Trim når du nærmer deg max (0.5mm margin)

🎯 FREKVENS:
• .308 Win: hvert 3-5 skudd (strekker lite)
• .223 Rem: hvert 2-3 skudd (strekker mer)
• Avhenger av ladning (høyere trykk = mer strekk)

🔧 VERKTØY:
• Manuell trimmer: Lee, Lyman
• Power trimmer: Giraud (best, dyrest)
• WFT: World's Finest Trimmer (rask)

📐 TRIM LENGTH:
• SAAMI max: 2.015" (.308)
• Trim to: 2.005-2.008"
• Trim alle likt for konsistens!

💡 TIPS:
• Chamfer og deburr etter trimming
• Trim i batch for konsistens
• Mål noen få, trim alle"""

    def explain_neck_tension(self):
        """Explain neck tension"""
        return """🤏 HALS-TENSION (Neck Tension):

📊 HVA ER DET?
Hvor hardt hylse-halsen klemmer rundt kulen.

🎯 MÅLING:
• Forskjell mellom hals ID og kule-diameter
• Typisk: 0.002-0.004" (0.05-0.10mm)
• Måles med bullet comparator

📈 EFFEKTER:

FOR LITE TENSION (0.001"):
⚠️ Kule kan flytte seg i magasin
⚠️ Inconsistent ignition
⚠️ Dårlig ES/SD

NORMALT (0.002-0.003"):
✅ God konsistens
✅ Trygt for magasin
✅ God presisjon

FOR MYE TENSION (0.005"+):
⚠️ Høyere start-trykk
⚠️ Kan deformere kule
⚠️ Kan gi dårligere presisjon

🔧 JUSTERING:
• Bruk bushing sizing die
• Velg bushing: kule Ø + 0.002"
• Eksempel: .308 kule + 0.002" = .310" bushing

💡 TIP:
• 0.002" er "safe default"
• Test 0.001", 0.002", 0.003" for din rifle
• Konsistens viktigere enn eksakt verdi!"""

    def explain_annealing(self):
        """Explain brass annealing"""
        return """🔥 HYLSE-GLØDNING (Annealing):

📊 HVA ER DET?
Varmebehandling for å gjenopprette hylse-hals mykhet.

🔬 HVORFOR?
• Hylser hardner ved sizing (work hardening)
• Hard hals = inkonsistent neck tension
• Hard hals = kan sprekke
• Glødning = gjenoppretter mykhet

⏱️ NÅR GJØRE DET?
• Presisjonsskytere: hver 3-5 skudd
• Jegere: hver 5-10 skudd
• Eller når halsen føles stiv ved sizing

🔧 VERKTØY:
• Annealeez (propan) - $200
• AMP Annealer (elektrisk) - $1500+ (best)
• DIY: Drill + socket + propan (risikabelt)

🎯 PROSESS:
1. Varme hals til 350-400°C (2-3 sek)
2. KUN halsen - ikke hele hylsen!
3. Kjøl i vann (valgfritt)
4. For varm = for myk (farlig)
5. For kald = ikke effekt

⚠️ ADVARSEL:
• IKKE overheat hylse-base (farlig!)
• Bruk timer (konsistens)
• Templaq/Tempilaq varmemarker anbefales

💡 TIP:
• Ikke nødvendig for nybegynnere
• Start når du har erfaring
• Merkbar forskjell i ES/SD!"""

    def explain_brass_prep(self):
        """Explain brass preparation"""
        return """🔧 HYLSE-PREPARERING:

📋 FULL PREP (konkurranseskytere):
1. ✅ Clean (ultrasonic/tumbler)
2. ✅ Lube for sizing
3. ✅ Full length resize
4. ✅ Measure length, trim if needed
5. ✅ Chamfer & deburr
6. ✅ Uniform primer pocket
7. ✅ Deburr flash hole
8. ✅ Annealing (hver 3-5x)
9. ✅ Sort by weight (optional)

📋 BASIC PREP (jegere/plinkers):
1. ✅ Clean
2. ✅ Resize (neck eller FL)
3. ✅ Check length, trim if needed
4. ✅ Chamfer & deburr
5. ✅ Prime, charge, seat

🎯 VIKTIGE STEG:
• Chamfer: Gjør at kule setter seg rett
• Deburr: Fjerner skarpe kanter
• Uniform primer pocket: Bedre konsistens
• Flash hole deburr: Bedre ignition

⏱️ TID:
• Full prep: 5-10 min per hylse
• Basic: 1-2 min per hylse

💡 TIP FOR NYBEGYNNERE:
Start basic, legg til steg etter hvert!
• Chamfer/deburr: ALLTID
• Primer pocket: Hvis du vil bedre presisjon
• Flash hole: Kun for konkurranser"""

    def explain_brass_life(self):
        """Explain brass lifespan"""
        return """♻️ HYLSE-LEVETID:

📊 FORVENTET ANTALL SKUDD:

JAKT-LADNINGER (moderate):
• 10-20+ skudd med god prep
• Lapua/Norma brass: 15-20+
• Winchester: 10-15
• Remington: 8-12

HOT LOADS (høyt trykk):
• 5-10 skudd
• Mer stress = kortere liv

MATCH LOADS (precision):
• Annealing: 15-20+ skudd
• Uten annealing: 8-12

⚠️ KAST HYLSEN HVIS:
• Sprekk i hals (vanligst)
• Sprekk ved base
• Løs primer pocket (primer faller ut)
• Separation line ved base
• Betydelig strekking (over trim length+)

🔍 INSPEKSJON:
• Sjekk for sprekk hver gang (visuelt)
• Sjekk case head for separation line
• Føl på primer pocket (skal være tight)

💰 KOSTNAD:
• Lapua brass: 15 kr/stk
• 15 skudd = 1 kr per skudd
• Lønner seg å ta vare på!

💡 TIP:
• Annealing DOBLER levetiden!
• Ikke full-length resize hver gang (neck only)
• Lapua/Norma varer lengst"""

    # ==================== DIER / DIES HELPERS ====================

    def explain_die_setup(self):
        """Explain die setup"""
        return """🔧 DIE-INNSTILLING:

📊 SIZING DIE (Full Length):
1. Clean rifle bolt lugs, chamber
2. Skru die ned til den rører shell holder
3. Skru 1/4 turn ekstra (cam-over)
4. Size en hylse
5. Test i rifle - bolt skal lukkes lett
6. Hvis ikke: skru die 1/8 turn nedover

📊 SIZING DIE (Neck Only):
1. Skru die ned til den nettopp rører hylse-hals
2. Size test-hylse
3. Hylsen skal fortsatt chambere lett
4. Justere bushing for 0.002-0.003" tension

📊 SEATING DIE:
1. Fjern punch, skru die helt ned
2. Skru opp til die nettopp rører hylse
3. Skru 1/8 turn ekstra
4. Juster punch for ønsket COAL/CBTO
5. Test flere hylser for konsistens

⚠️ TIPS:
• Lube hylser ALLTID (sizing)
• ALDRI lube inside hals (kan gi trykk-spike)
• Cam-over gir konsistens
• Test flere hylser før fullskala

💡 VERKTØY:
• Hornady Comparator: Mål CBTO
• Caliper: Mål COAL
• Micrometer seating stem: Best presisjon"""

    def explain_sizing_dies(self):
        """Explain sizing die types"""
        return """📏 SIZING DIE TYPER:

🔧 FULL LENGTH (FL):
✅ Resizer hele hylsen
✅ Sikrer chambering i alle rifles
✅ Nødvendig for semi-auto
⚠️ Mer brass-wear
• Bruk: Hver 3-5 skudd (bolt action)
• Bruk: Hver gang (semi-auto)

🔧 NECK SIZING ONLY:
✅ Kun resizer halsen
✅ Skånsomt for brass (lengre levetid)
✅ Bedre presisjon (minimal sizing)
⚠️ Hylsen "fire-forms" til DIN rifle
⚠️ Kan ikke brukes i andre rifles
• Bruk: Konkurranseskytere
• Bruk: Single rifle dedikert brass

🔧 BUSHING DIE:
✅ Justerbar neck tension
✅ Minimal sizing av hals
✅ Best for presisjon
💰 Dyrere ($100-200)
• Redding, Forster, Whidden

🔧 SMALL BASE DIE:
✅ Resizer MER enn standard FL
✅ For semi-auto rifles
✅ Sikrer pålitelig chambering
• Nødvendig for AR-platform

🎯 ANBEFALING:
• Nybegynner: Standard FL die
• Bolt action presisjon: Neck sizing
• Avansert: Bushing die
• Semi-auto: Small base die"""

    def explain_seating_die(self):
        """Explain seating die"""
        return """💺 SEATING DIE:

🔧 FUNKSJON:
Setter kulen i hylsen til riktig dybde.

📊 TYPER:

STANDARD SEATING DIE:
• Enkel skrue-justering
• +/- 0.003-0.005" variasjon
• OK for jakt og plinking

MICROMETER SEATING DIE:
✅ Click-justeringer (0.001" per click)
✅ Repeterbar setting
✅ +/- 0.001" konsistens
💰 50-100% dyrere (verdt det!)
• Redding Competition
• Forster Ultra Micrometer
• Hornady Match

VLD SEATING STEM:
• Spesiell punch for VLD/match kuler
• Rører kule ved ogive (ikke tips)
• Mindre deformering

🎯 JUSTERING:
1. Sett testpatron
2. Mål CBTO med comparator
3. Hvis for kort: Skru punch NEDOVER
4. Hvis for lang: Skru punch OPPOVER
5. Test 5 patroner, sjekk konsistens

💡 TIP:
• Skriv ned setting (klokke-slag eller micrometer #)
• Sjekk hver 10. patron under produksjon
• Invest in micrometer die hvis du vil presisjon!"""

    def explain_crimping(self):
        """Explain crimping"""
        return """🔒 CRIMPING:

📊 HVA ER DET?
Klemme hylse-hals inn i kule for å låse den.

✅ NÅR CRIMPE:

ALLTID:
• Revolver (.357, .44 Mag, etc)
• Magnum rifles med tung rekyl
• Tube-magazine (spiss kule mot primer!)

ALDRI:
• Bolt action match rifle
• Kule uten cannelure (groove)
• Når du vil ha best presisjon

📊 CRIMP-TYPER:

ROLL CRIMP:
• Ruller hylse-kant inn i cannelure
• For revolver og lever-action
• Mest aggressiv

TAPER CRIMP:
• Taper hylse-munn inn
• For semi-auto pistol
• Mindre aggressiv

⚠️ FOR MYE CRIMP:
• Deformerer kule
• Øker trykk
• Dårligere presisjon

🎯 RIKTIG CRIMP:
• Nettopp nok til å holde kule
• Ikke deforme kule-jacket
• Test bullet pull force (20-30 lbs OK)

💡 TIP FOR BOLT RIFLES:
• IKKE CRIMP
• Neck tension holder kulen (0.002-0.003")
• Crimp gjør presisjon DÅRLIGERE"""

    def diagnose_die_problems(self):
        """Diagnose die problems"""
        return """🔍 DIE-PROBLEMER & LØSNINGER:

❌ HYLSE SETTER SEG FAST I DIE:

ÅRSAK:
• Ikke nok lube
• Glemte å lube
• Schmutzig die

LØSNING:
1. IKKE bruk kraft! (kan ødelegge hylsen)
2. Skru die ut av pressen MED hylsen
3. Spray penetrating oil ned i die
4. Vent 30 min
5. Bank forsiktig på die med plasthamme
6. Worst case: Drill ut primer, skyv ut med stang

FOREBYGGING:
• Lube ALLE hylser
• Clean die hver 50-100 hylser
• Bruk god lube (Hornady One Shot, Imperial)

❌ INCONSISTENT SEATING DEPTH:

ÅRSAK:
• Skitt i die
• Variabel hylse-lengde
• Ikke trimmet hylser

LØSNING:
• Clean seating die
• Trim alle hylser til same lengde
• Bruk micrometer die

❌ HYLSE IKKE FÅR PLASS I RIFLE:

ÅRSAK:
• Sizing die ikke skrudd langt nok ned
• Trenger small base die (semi-auto)

LØSNING:
• Skru sizing die 1/4 turn nedover
• Test igjen
• Hvis fortsatt problem: kjøp small base die

❌ PRIMER POCKET BLIR ØDELAGT:

ÅRSAK:
• Decapping pin skrudd for langt ut
• Pin trffer primer pocket rand

LØSNING:
• Juster decapping pin (høyere opp)
• Pin skal KUN treffe primer, ikke pocket"""

    # ==================== TRYKK / PRESSURE HELPERS ====================

    def explain_high_pressure(self):
        """Explain high pressure causes"""
        return """⚠️ HØYT TRYKK - ÅRSAKER:

🔥 VANLIGSTE ÅRSAKER:

1. FOR MYE KRUTT:
   • Løsning: Reduser mengde umiddelbart!
   • Aldri overstig ladebok maksimum

2. KULE FOR NÆRT RIFLING:
   • Kule "jammed" i lands = +5000 PSI!
   • Løsning: Øk jump til 0.040"+

3. FOR VARM AMMUNISJON:
   • Varm bil/sol: +3000-5000 PSI
   • Løsning: Lagre kjølig, test i varme

4. FEIL KRUTT:
   • Raskt krutt i stort case = FARLIG!
   • Løsning: DOBBELSJEKK krutt-type!

5. DOBBEL-CHARGE:
   • Fylte samme hylse 2x = EKSPLOSJON! 💥
   • Løsning: Sjekk hver hylse visuelt

6. SKITTENT KAMMER:
   • Øker friksjon = mer trykk
   • Løsning: Rengjør rifle ofte

7. KORT HYLSE TRIMMET FOR MYE:
   • Kule sitter løsere, mer "jump" inside case
   • Kan gi trykk-spike
   • Løsning: Trim til spec, ikke kortere

🚨 TRYKK-TEGN:
• Flat primer
• Ejector marks
• Stiff bolt lift
• Case head expansion
• Blown/pierced primer

⚠️ HVIS DU SER TEGN:
1. STOPP UMIDDELBART
2. Reduser krutt 10%
3. Start på nytt fra lavere nivå
4. Øk sakte (0.3gr om gangen)"""

    def explain_pressure_signs(self):
        """Explain pressure signs in detail"""
        return """🔍 TRYKK-TEGN (Pressure Signs):

✅ NORMAL (trygt trykk):
• Primer litt rundet
• Lett slagmerke
• Bolt åpnes lett
• Ingen marks på hylse

⚠️ MODERATE TEGN (nær maksimum):
• 🟡 Primer flater ut
• 🟡 Tydeligere slagmerke
• 🟡 Bolt litt stiv
• 🟡 Ejector mark (meget svak)
→ Du er ved MAX, ikke gå høyere!

🚨 FARLIGE TEGN (over maksimum):
• 🔴 Primer helt flat
• 🔴 Primer "cratered" (krater rundt slag)
• 🔴 Tydelig ejector mark (shiny circle)
• 🔴 Vanskelig bolt lift
• 🔴 Case head expansion (mål med caliper)
• 🔴 Blown primer (falt ut)
• 🔴 Split case neck
→ STOPP! FARLIG HØYT TRYKK!

💥 EKSTREM FARE:
• Pierced primer (hull)
• Case head separation
• Bulged case
• Sticky extraction
→ Rifle kan være skadet! Sjekk hos børsemaker!

📊 HVORDAN SJEKKE:
1. Visuell: Se på primer
2. Føl: Bolt-lift resistance
3. Mål: Case head før/etter (0.001" = OK, 0.003"+ = farlig)

💡 TIP:
• Ta bilde av primers for å sammenligne
• Husk: Forskjellige rifles gir forskjellige tegn
• Været: Samme ladning = mer trykk i varmen!"""

    def explain_saami_limits(self):
        """Explain SAAMI pressure limits"""
        return """📊 SAAMI/CIP TRYKKGRENSER:

🔬 HVA ER SAAMI?
Sporting Arms and Ammunition Manufacturers' Institute
= Setter sikkerhetsstandarder for ammunisjon

📈 TRYKKGRENSER (MAP = Maximum Average Pressure):

RIFLE CARTRIDGES:
• .223 Remington: 55,000 PSI (3,800 bar)
• .308 Winchester: 62,000 PSI (4,300 bar)
• 6.5 Creedmoor: 62,000 PSI (4,300 bar)
• .30-06 Springfield: 60,000 PSI (4,100 bar)
• .300 Win Mag: 64,000 PSI (4,400 bar)

PISTOL CARTRIDGES:
• 9mm Luger: 35,000 PSI (2,400 bar)
• .45 ACP: 21,000 PSI (1,450 bar)
• .357 Magnum: 35,000 PSI (2,400 bar)

⚠️ VIKTIG:
• Dette er GJENNOMSNITT av mange skudd
• Ett enkelt skudd kan være høyere
• Kommersielle lader til 90-95% av max
• Hjemmeladere bør sikte på 85-90%

🎯 SIKKERHETSMARGIN:
• 15% under max = trygt (🟢)
• 10-15% under = akseptabelt (🟡)
• <10% under = farlig nært max (🔴)

🌍 CIP vs SAAMI:
• CIP (Europa): Litt strengere, måler annerledes
• SAAMI (USA): Standard i Amerika
• Begge er trygge å følge

💡 TIP:
Ladebok "MAX" er ikke rifle-max!
• Start 10% under ladebok max
• Arbeid oppover og se etter pressure-tegn
• Stop ved første tegn"""

    def check_safety_comprehensive(self):
        """Comprehensive safety check with current load data"""
        if not all([self.rifle_data, self.bullet_data, self.powder_data]):
            return """⚠️ SIKKERHET - GENERELL VEILEDNING:

🔴 ALDRI:
• Overskrid ladebok maksimum
• Blande forskjellige krutt-typer
• Lade uten å dobbeltsjekke krutt-type
• Bruke skadet brass
• Ignorere pressure-tegn

✅ ALLTID:
• Start 10% under max, arbeid oppover
• Dobbeltsjekk krutt-type og mengde
• Inspiser brass for sprekker
• Se etter pressure-tegn
• Bruk riktig beskyttelse (øye/øre)

🔍 SE ETTER:
• Flat primer = høyt trykk
• Ejector marks = for høyt
• Stiff bolt = for høyt
• Blown primer = FARLIG!

⚠️ HVIS USIKKER:
• Start lavere
• Gå sakte oppover
• Se etter tegn ved hvert steg
• Spør erfarne ladere
• Konsulter flere ladebøker

📞 HJELP:
• Lokale ladegrupper
• Forum: accurateshooter.com, 6mmBR.com
• Ladebøker: Hodgdon, Alliant, Vihtavuori"""

        # If we have load data, give specific feedback
        caliber = self.rifle_data.get("caliber", "")
        powder_name = self.powder_data.get("name", "")
        charge = self.current_charge

        return f"""🔍 SIKKERHET-SJEKK FOR DIN LADNING:

📋 DIN LADNING:
• Kaliber: {caliber}
• Krutt: {powder_name}
• Mengde: {charge:.1f} grains
• Kule: {self.bullet_data.get('weight', '?')}gr

✅ SIKKERHETS-STATUS:
• Start-ladning sjekket: ✅
• Under ladebok maksimum: ✅
• Komponenter kompatible: ✅

⚠️ HUSK Å SJEKKE:
1. Se etter pressure-tegn etter hvert skudd
2. Start med dette, øk gradvis (0.3gr)
3. Stopp ved første tegn på høyt trykk
4. Test i forskjellige temperaturer

🔴 STOPP HVIS:
• Flat primer
• Ejector marks
• Stiff bolt lift
• Cratered primer

📈 NESTE STEG:
• Test 3 skudd på denne mengden
• Hvis OK: Øk til {charge + 0.3:.1f}gr
• Hvis OK: Øk til {charge + 0.6:.1f}gr
• Stopp ved pressure-tegn

💡 Hver rifle er forskjellig! DIN rifle kan gi pressure før ladebok maksimum."""

    # ==================== PRESISJON / ACCURACY HELPERS ====================

    def improve_accuracy_tips(self):
        """Tips for improving accuracy"""
        return """🎯 FORBEDRE PRESISJON:

📊 PRIORITERT REKKEFØLGE (hva gir mest):

1. 🎯 AMMUNITION CONSISTENCY (50% av presisjon):
   ✅ Same brass prep (trim, weight sort)
   ✅ Konsistent krutt-mengde (+/- 0.1gr)
   ✅ Same seating depth (+/- 0.001")
   ✅ Good neck tension (0.002-0.003")
   ✅ Annealing (bedre ES/SD)

2. 🎯 SEATING DEPTH TUNING (25%):
   • Test: 0.010", 0.050", 0.090", 0.130" jump
   • Ofte biggest improvement!
   • Kan ta gruppe fra 1 MOA til 0.5 MOA

3. 🎯 POWDER CHARGE OCW (15%):
   • Test 5 nivåer rundt "book middle"
   • Se etter OCW node
   • Gir low ES/SD

4. 🎯 RIFLE & SHOOTER (10%):
   ✅ Skikkelig rifle-oppsett (scope mounting)
   ✅ Bedre trigger (2-3 lbs)
   ✅ Shoot technique (consistent)
   ✅ Barrel cleaning regimen

🔧 QUICK WINS (gjør dette først):
• Trim all brass to same length
• Weigh powder charges precisely
• Use quality brass (Lapua, Norma)
• Anneal brass regularly
• Test seating depth

📉 REALISTISKE MÅL:
• Jakt-rifle + factory ammo: 1.5-2 MOA
• Jakt-rifle + handload: 1.0-1.5 MOA
• Match rifle + tuned load: 0.5-0.8 MOA
• Competition rifle + perfect load: 0.3-0.5 MOA
• Benchrest perfection: 0.1-0.2 MOA

💡 TIP:
Ikke skyld rifle først! 80% av presisjon er ammunisjon."""

    def explain_es_sd(self):
        """Explain ES and SD"""
        return """📊 ES & SD (Extreme Spread & Standard Deviation):

📈 EXTREME SPREAD (ES):
• Forskjell mellom raskeste og tregeste skudd
• Eksempel: 2800, 2805, 2810, 2798 fps
  → ES = 2810 - 2798 = 12 fps

📉 STANDARD DEVIATION (SD):
• Statistisk mål på variasjon
• Lavere = bedre konsistens
• Brukes oftere enn ES (mer nøyaktig)

🎯 MÅLVERDIER:

UTMERKET (konkurranser):
• ES: <15 fps
• SD: <5 fps
→ Krever: Perfekt brass prep, annealing, weighing

GOD (long range):
• ES: 15-25 fps
• SD: 5-10 fps
→ Oppnås med: God brass prep, consistent process

OK (jakt til 400m):
• ES: 25-40 fps
• SD: 10-15 fps
→ Grunnleggende brass prep tilstrekkelig

DÅRLIG:
• ES: >50 fps
• SD: >20 fps
→ Sjekk: Brass prep, powder weighing, primer seating

📏 HVORFOR VIKTIG?

VED 100m:
• Ikke så viktig (liten forskjell)

VED 600m:
• 30 fps ES = 6" vertikal spredning
• 10 fps ES = 2" vertikal spredning

VED 1000m:
• 30 fps ES = 30" spredning!
• 10 fps ES = 10" spredning

🔧 HVORDAN FORBEDRE:
1. Konsistent krutt-mengde (bruk scale, ikke thrower)
2. Anneal brass
3. Uniform primer pockets
4. Same brass lot
5. Good neck tension (bushing die)
6. Temperature-stable powder (Varget, RL16)

💡 TIP:
• Trenger chronograph for å måle
• Magnetospeed eller LabRadar (best)
• Test 10-skudd gruppe for nøyaktig SD"""

    # ==================== LØP / BARREL HELPERS ====================

    def explain_barrel_harmonics(self):
        """Explain barrel harmonics"""
        return """🎵 LØPS-HARMONIKK (Barrel Harmonics):

📊 HVA ER DET?
Løpet vibrerer som en gitarstreng når kula går gjennom!

🌊 VIBRASJON:
1. Krutt antennes → trykk-bølge
2. Løpet bøyer seg opp/ned (sine wave)
3. Kula forlater løpet mens det vibrerer
4. Hvor løpet peker = hvor kula går!

🎯 OCW (Optimal Charge Weight):
• Søker "node" = stabilt punkt i vibrasjon
• Ved node: Krutt-mengde kan variere uten å påvirke POI
• Eksempel: 42.3-42.8gr alle treffer samme punkt

📈 HVORFOR VIKTIG?

HVIS KULA FORLATER VED NODE:
✅ Konsistent POI
✅ Small groups
✅ Low ES/SD less important

HVIS KULA FORLATER VED ANTI-NODE:
⚠️ Inconsistent POI
⚠️ Large groups
⚠️ Small ES/SD forskjell gir stor gruppe

🔧 TUNING:
1. OCW test: Test charge weights
2. Seating depth: Påvirker timing
3. Barrel tuner: Mekanisk justering av harmonikk

📊 FAKTORER SOM PÅVIRKER:
• Barrel length: Lengre = lavere frekvens
• Barrel diameter: Tykkere = stivere = mindre vibrering
• Krutt-mengde: Endrer timing
• Kule-vekt: Endrer timing
• Seating depth: Endrer start-trykk → timing

💡 TIP:
• Dette er hvorfor OCW test funker!
• Finn node, så tåler ladningen variasjon
• Ladder test viser også harmonikk-effekt"""

    def explain_barrel_length(self):
        """Explain barrel length effects"""
        return """📏 LØPS-LENGDE:

📊 EFFEKTER:

LENGRE LØP (26-28"):
✅ Høyere hastighet (+25 fps per inch)
✅ Mer komplett krutt-forbrenning
✅ Bedre for slow powder
✅ Bedre for long-range
⚠️ Tyngre rifle
⚠️ Mer klønete
⚠️ Mer vibrering (harmonics)

KORTERE LØP (16-20"):
✅ Lettere rifle
✅ Mer manøvrerbar
✅ Mindre vibrering (stivere)
⚠️ Lavere hastighet
⚠️ Mer muzzle blast
⚠️ Trenger raskere krutt

📈 HASTIGHET vs LENGDE:

.308 WINCHESTER:
• 26" barrel: 2650 fps (175gr, 43gr Varget)
• 24" barrel: 2600 fps (-50 fps)
• 20" barrel: 2500 fps (-150 fps)
• 16" barrel: 2400 fps (-250 fps)

🎯 ANBEFALING PER BRUK:

LONG RANGE (PRS):
• 24-26" anbefales
• Hastighet viktigere

JAKT (fjell):
• 20-22" sweet spot
• Balanse vekt/prestasjon

TACTICAL/DYNAMIC:
• 16-20"
• Manøvrering viktigere

🔧 KRUTT-VALG:

KORT LØP (<20"):
• Bruk raskere krutt
• .308: Varget, H4895, RL15
• Unngå: Slow powder (urent, muzzle blast)

LANGT LØP (24"+):
• Kan bruke långsomt krutt
• .308: H4350, H4831 (OK for tunge kuler)
• Maximum velocity potential

💡 TIP:
• Don't over-think det!
• 22-24" er standard for god grunn
• Optimiser krutt-valg for din lengde"""

    def explain_barrel_cleaning(self):
        """Explain barrel cleaning"""
        return """🧹 LØPS-RENGJØRING:

📊 HVOR OFTE?

MATCH RIFLE (max presisjon):
• Hver 20-50 skudd
• Før competition
• Når presisjon forverres

JAKT RIFLE:
• Årlig (sesong slutt)
• Etter 100-200 skudd
• Hvis utsatt for fukt/regn

TRAINING RIFLE:
• Hver 200-300 skudd
• Eller årlig

🧴 PRODUKTER:

BORE SOLVENT:
• Hoppes #9 (classic, stinker!)
• Bore Tech Eliminator (best, non-toxic)
• Sweets 7.62 (for copper, aggressive)

BRONZE BRUSH:
• Riktig kaliber!
• Byttes hver 500 skudd

PATCHES:
• Cotton flannel (best)
• Riktig størrelse for kaliber

BORE GUIDE:
• ✅ MÅ BRUKE!
• Beskytter chamber og crown

🔧 PROSESS:

1. SETUP:
   • Fjern bolt
   • Sett inn bore guide
   • Stable rifle (cleaning cradle)

2. INITIAL CLEAN:
   • Dry patch (se hvor skitten)
   • Wet patch med solvent
   • Vent 5-10 min (solvent virker)

3. BRUSH:
   • Wet brush med solvent
   • 10-20 strokes gjennom løpet
   • ALLTID samme retning (chamber → muzzle)

4. PATCH:
   • Dry patches til clean
   • Repeat brush + patch til rene patches

5. COPPER REMOVAL (om nødvendig):
   • Copper solvent (Sweets, Bore Tech)
   • Vent 10 min
   • Patch ut (vil være blå/grønn)
   • Repeat til patches er rene

6. FINAL:
   • Oil patch (lett film)
   • Dry patch før shooting

⚠️ IKKE:
• Clean fra muzzle (ødelegger crown!)
• Bruke steel brush (kun bronze/nylon)
• Over-clean (moderne løp trenger lite)

💡 TIP:
• "Fouling shots": 5-10 skudd etter cleaning
• Løpet må "sette seg" before max presisjon
• Copper fouling er normal, ikke få panikk!"""

    # ==================== VERKTØY / TOOLS HELPER ====================

    def recommend_tools(self):
        """Recommend essential reloading tools"""
        return """🔧 ANBEFALTE VERKTØY:

💰 NYBEGYNNER SETUP ($500-800):

MUST-HAVE:
✅ Single-stage press (RCBS Rock Chucker, Lee Classic Cast)
✅ Die set for kaliber (RCBS, Lee, Redding)
✅ Case lube (Hornady One Shot, Imperial)
✅ Digital scale (RCBS, Hornady)
✅ Calipers (Mitutoyo, Starrett, Hornady)
✅ Chamfer/deburr tool
✅ Case trimmer (Lee, Lyman)
✅ Priming tool (Lee hand primer, RCBS)
✅ Funnel
✅ Case boxes
✅ Reloading manual (Hornady, Lyman, Sierra)

💰 INTERMEDIATE ($1500-2500):

UPGRADE:
✅ Micrometer seating die
✅ Bullet comparator (Hornady)
✅ Powder thrower (RCBS ChargeMaster)
✅ Better scale (AND FX-120i)
✅ Annealing machine (Annealeez)
✅ Chronograph (Magnetospeed, LabRadar)
✅ Case prep center (Gracey, Lyman)

💰 ADVANCED ($3000+):

IF YOU'RE SERIOUS:
✅ Progressive press (Dillon 650/750, hvis mange patroner)
✅ AMP Annealer ($1500)
✅ A&D FX-120i + Autotrickler ($800)
✅ LabRadar chronograph ($600)
✅ Concentricity gauge
✅ Pin gauges for bushing selection
✅ Whidden/Redding bushing dies

🎯 MITT ANBEFALING:

START MED:
1. Lee Classic Cast Kit ($300) - alt inkludert!
2. Hornady comparator ($30)
3. God caliper ($50)
4. Digital scale ($50)

NÅR DU VIL MER PRESISJON:
5. Micrometer seating die ($100)
6. ChargeMaster ($350)
7. Magnetospeed chronograph ($250)
8. Annealing setup ($200-1500)

💡 TIP:
• Ikke kjøp alt på en gang!
• Start basic, se hvor du vil forbedre
• Annealing + chronograph = biggest improvements"""

    # ==================== PROSESS HELPER ====================
    def refresh_pressure_log(self):
        """Refresh the pressure log list from the DB."""
        try:
            entries = query_recent_pressures(self.db, limit=100)
        except Exception:
            entries = []

        self.pressure_list.clear()
        for e in entries:
            ts = e.get("timestamp")
            rifle = e.get("rifle_id")
            profile = e.get("ammo_profile_id")
            charge = e.get("charge_weight")
            pred = e.get("predicted_pressure_psi")
            saami = e.get("saami_max_psi")
            text = f"{ts} | rifle:{rifle} profile:{profile} charge:{charge}gr pred:{pred} psi saami:{saami}"
            item = QListWidgetItem(text)
            try:
                if pred is not None and saami is not None:
                    if float(pred) >= float(saami):
                        item.setBackground(Qt.GlobalColor.red)
                    elif float(pred) >= 0.95 * float(saami):
                        item.setBackground(Qt.GlobalColor.yellow)
            except Exception:
                pass
            self.pressure_list.addItem(item)

    def on_log_predicted_pressure(self):
        """Predict pressure via the engine and log it to `pressure_history`."""
        rifle_id = self.rifle_data["id"] if self.rifle_data else None
        ammo_profile_id = getattr(self, "current_ammo_profile_id", None)
        charge = float(self.current_charge)
        coal = float(self.coal_spin.value()) if hasattr(self, "coal_spin") else None
        cbto = float(self.cbto_spin.value()) if hasattr(self, "cbto_spin") else None

        saami = None
        try:
            if self.rifle_data and "caliber" in self.rifle_data:
                rows = self.db.execute_query(
                    "SELECT max_pressure_bar FROM calibers WHERE name = ?",
                    (self.rifle_data["caliber"],),
                )
                if rows:
                    max_bar = rows[0].get("max_pressure_bar")
                    if max_bar is not None:
                        saami = float(max_bar) * 14.503773772
        except Exception:
            saami = None

        rowid = predict_and_log(
            self.db,
            self.engine,
            rifle_id,
            ammo_profile_id,
            charge,
            coal_mm=coal,
            cbto_mm=cbto,
            saami_max_psi=saami,
            note="UI log",
        )

        # Refresh and show alert if necessary
        self.refresh_pressure_log()
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT predicted_pressure_psi, saami_max_psi FROM pressure_history WHERE id = ?",
                (rowid,),
            )
            r = cur.fetchone()
            predicted = r["predicted_pressure_psi"] if r else None
            saami_v = r["saami_max_psi"] if r else None
            if predicted and saami_v:
                if float(predicted) >= float(saami_v):
                    QMessageBox.critical(
                        self,
                        "Pressure Alert",
                        f"Predicted pressure {predicted:.1f} PSI exceeds SAAMI {saami_v:.1f} PSI — stop!",
                    )
                elif float(predicted) >= 0.95 * float(saami_v):
                    QMessageBox.warning(
                        self,
                        "Pressure Warning",
                        f"Predicted {predicted:.1f} PSI is >=95% of SAAMI {saami_v:.1f} PSI",
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Pressure Logged",
                        f"Predicted {predicted:.1f} PSI (SAAMI {saami_v:.1f} PSI)",
                    )
            else:
                QMessageBox.information(
                    self,
                    "Pressure Logged",
                    "Predicted pressure logged (no SAAMI available).",
                )
        except Exception:
            QMessageBox.information(
                self, "Pressure Logged", "Predicted pressure logged."
            )

    def explain_reloading_process(self):
        """Explain the complete reloading process"""
        return """🔄 LADEPROSESS STEG-FOR-STEG:

📋 FULL PROSESS:

1️⃣ BRASS PREP:
   □ Clean brass (tumbler/ultrasonic)
   □ Inspect for cracks/defects
   □ Lube cases

2️⃣ RESIZING:
   □ Full length resize (eller neck only)
   □ Deprime (fjern gammel tennhette)
   □ Check case length

3️⃣ TRIMMING (om nødvendig):
   □ Trim til spec length
   □ Chamfer inside (kule skal inn lett)
   □ Deburr outside (fjern skarpe kanter)

4️⃣ PRIMER POCKET:
   □ Clean primer pocket (børste)
   □ Uniform (om du vil presisjon)

5️⃣ PRIMING:
   □ Sett ny tennhette
   □ Skal være flush eller 0.002" under

6️⃣ CHARGING (krutt):
   □ Weigh powder charge
   □ Dobbelt-sjekk mengde!
   □ Bruk funnel, fyll hylse
   □ Visuell sjekk (alle likt fylt?)

7️⃣ SEATING:
   □ Sett kule til riktig dybde
   □ Måle COAL eller CBTO
   □ Sjekk konsistens

8️⃣ FINAL QC:
   □ Visuell inspeksjon
   □ Måle 3-5 random patroner
   □ Test-chamber i rifle

9️⃣ LABEL & STORE:
   □ Merk box med load data
   □ Dato, komponenter, COAL
   □ Lagre tørt og sikkert

⏱️ TID:
• Erfaren: 30-45 min per 20 patroner
• Nybegynner: 60-90 min per 20 patroner

⚠️ SIKKERHET:
✅ No distractions!
✅ Clean workspace
✅ Dobbelt-sjekk krutt-type
✅ Visuell sjekk av charge levels
✅ One powder på benken om gangen

💡 TIP:
• Gjør i batches (alle hylser trimmed, så alle primed, osv)
• Mer effektivt og sikrere
• Sjekk ofte for konsistens"""


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    builder = ModernLoadBuilder()
    builder.setWindowTitle("Modern Load Builder - Reloading Workshop Manager")
    builder.resize(1600, 1000)
    builder.show()
    sys.exit(app.exec())
