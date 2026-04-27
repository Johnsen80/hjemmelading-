"""
Session Logger
Loggføring av ladeøkter og skyteøkter
"""

import os

from PyQt6.QtCore import QDate, QSettings, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from HjemmeladingApp.utils import units

from ..database.database import get_database
from ..tools.load_session_runtime_service import (
    get_active_load_session_id_from_settings,
)
from ..utils.i18n import tr


def _project_name_from_path(path: str) -> str:
    try:
        name = os.path.basename(str(path).rstrip("\\/"))
    except Exception:
        name = ""
    return name or str(path) or "Default Project"


def _get_active_project_context() -> dict[str, str]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    project_path = str(settings.value("workspace/current_project", "") or "").strip()
    return {
        "project_name": _project_name_from_path(project_path),
        "project_path": project_path,
    }


def _get_active_load_session_id() -> int | None:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return get_active_load_session_id_from_settings(settings)


def _get_global_unit_system() -> str:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return str(settings.value("units/global", "metric") or "metric").strip().lower()


def _format_distance_meters(value: object) -> str:
    try:
        distance_m = float(value)
    except Exception:
        return str(value) if value not in (None, "") else "-"
    if _get_global_unit_system() == "imperial":
        return f"{units.meters_to_yards(distance_m):.0f} yd ({distance_m:.0f} m)"
    return f"{distance_m:.0f} m"


def _format_temperature_c(value: object) -> str:
    try:
        temp_c = float(value)
    except Exception:
        return str(value) if value not in (None, "") else "-"
    if _get_global_unit_system() == "imperial":
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return f"{temp_f:.0f} °F ({temp_c:.0f} °C)"
    return f"{temp_c:.0f} °C"


def _format_wind_mps(value: object) -> str:
    try:
        wind_mps = float(value)
    except Exception:
        return str(value) if value not in (None, "") else "-"
    if _get_global_unit_system() == "imperial":
        return f"{wind_mps * 2.23694:.1f} mph ({wind_mps:.1f} m/s)"
    return f"{wind_mps:.1f} m/s"


def _format_group_mm(value: object) -> str:
    try:
        group_mm = float(value)
    except Exception:
        return str(value) if value not in (None, "") else "-"
    if _get_global_unit_system() == "imperial":
        return f"{units.mm_to_inches(group_mm):.2f} in ({group_mm:.1f} mm)"
    return f"{group_mm:.1f} mm"


def _to_display_distance(value_m: object) -> int:
    try:
        distance_m = float(value_m)
    except Exception:
        return 0
    if _get_global_unit_system() == "imperial":
        return int(round(units.meters_to_yards(distance_m)))
    return int(round(distance_m))


def _from_display_distance(value: int) -> float:
    if _get_global_unit_system() == "imperial":
        return float(units.yards_to_meters(float(value)))
    return float(value)


def _to_display_temperature(value_c: object) -> float:
    try:
        temp_c = float(value_c)
    except Exception:
        return 0.0
    if _get_global_unit_system() == "imperial":
        return temp_c * 9.0 / 5.0 + 32.0
    return temp_c


def _from_display_temperature(value: float) -> float:
    if _get_global_unit_system() == "imperial":
        return (float(value) - 32.0) * 5.0 / 9.0
    return float(value)


def _to_display_wind(value_mps: object) -> int:
    try:
        wind_mps = float(value_mps)
    except Exception:
        return 0
    if _get_global_unit_system() == "imperial":
        return int(round(wind_mps * 2.23694))
    return int(round(wind_mps))


def _from_display_wind(value: int) -> float:
    if _get_global_unit_system() == "imperial":
        return float(value) / 2.23694
    return float(value)


def _to_display_group(value_mm: object) -> float:
    try:
        group_mm = float(value_mm)
    except Exception:
        return 0.0
    if _get_global_unit_system() == "imperial":
        return units.mm_to_inches(group_mm)
    return group_mm


def _from_display_group(value: float) -> float:
    if _get_global_unit_system() == "imperial":
        return float(units.inches_to_mm(float(value)))
    return float(value)


def _resolve_shooting_session_load_session_id(
    session: dict | None = None,
) -> int | None:
    if session:
        existing_value = session.get("load_session_id")
        if existing_value not in (None, ""):
            try:
                return int(existing_value)
            except Exception:
                pass
    return _get_active_load_session_id()


class SessionLogger(QWidget):
    """Widget for logging av ladeøkter og skyteøkter"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel(tr("session_logger_title"))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Ladeøkter
        tabs.addTab(self.create_loading_tab(), tr("session_logger_loading_tab"))

        # Tab 2: Skyteøkter
        tabs.addTab(self.create_shooting_tab(), tr("session_logger_shooting_tab"))

    def create_loading_tab(self):
        """Oppretter ladeøkt-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Knapper
        btn_layout = QHBoxLayout()
        new_btn = QPushButton(tr("session_logger_new_loading"))
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self.new_loading_session)
        btn_layout.addWidget(new_btn)

        edit_btn = QPushButton(tr("session_logger_edit"))
        edit_btn.setMinimumHeight(40)
        edit_btn.clicked.connect(self.edit_loading_session)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton(tr("session_logger_delete"))
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_loading_session)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.loading_table = QTableWidget()
        self.loading_table.setColumnCount(7)
        self.loading_table.setHorizontalHeaderLabels(
            [
                "Dato",
                tr("session_logger_project_col"),
                tr("session_logger_ammo_profile_col"),
                tr("session_logger_quantity_col"),
                tr("session_logger_time_col"),
                tr("session_logger_cost_col"),
                tr("session_logger_notes_col"),
            ]
        )
        self.loading_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.loading_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.loading_table.doubleClicked.connect(self.edit_loading_session)
        layout.addWidget(self.loading_table)

        self.load_loading_sessions()

        return widget

    def create_shooting_tab(self):
        """Oppretter skyteøkt-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Knapper
        btn_layout = QHBoxLayout()
        new_btn = QPushButton(tr("session_logger_new_shooting"))
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self.new_shooting_session)
        btn_layout.addWidget(new_btn)

        edit_btn = QPushButton(tr("session_logger_edit"))
        edit_btn.setMinimumHeight(40)
        edit_btn.clicked.connect(self.edit_shooting_session)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton(tr("session_logger_delete"))
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_shooting_session)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.shooting_table = QTableWidget()
        self.shooting_table.setColumnCount(8)
        self.shooting_table.setHorizontalHeaderLabels(
            [
                "Dato",
                tr("session_logger_project_col"),
                tr("session_logger_ammo_profile_col"),
                tr("session_logger_rifle_col"),
                tr("session_logger_shots_col"),
                tr("session_logger_distance_col"),
                tr("session_logger_weather_col"),
                tr("session_logger_notes_col"),
            ]
        )
        self.shooting_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.shooting_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.shooting_table.doubleClicked.connect(self.edit_shooting_session)
        layout.addWidget(self.shooting_table)

        self.load_shooting_sessions()

        return widget

    # LADEØKTER

    def load_loading_sessions(self):
        """Laster ladeøkter fra database"""
        sessions = self.db.get_all("loading_sessions", "date DESC")
        self.loading_table.setRowCount(len(sessions))

        for i, session in enumerate(sessions):
            self.loading_table.setItem(i, 0, QTableWidgetItem(session["date"]))
            self.loading_table.setItem(
                i, 1, QTableWidgetItem(session.get("project_name") or "Default Project")
            )

            # Hent ammunisjonsprofil navn
            ammo_name = "-"
            if session["ammo_profile_id"]:
                ammo = self.db.get_by_id("ammo_profiles", session["ammo_profile_id"])
                if ammo:
                    ammo_name = ammo["name"]
            self.loading_table.setItem(i, 2, QTableWidgetItem(ammo_name))

            self.loading_table.setItem(i, 3, QTableWidgetItem(str(session["quantity"])))

            time_str = f"{session['time_minutes']}" if session["time_minutes"] else "-"
            self.loading_table.setItem(i, 4, QTableWidgetItem(time_str))

            cost_str = (
                f"{session['total_cost']:.2f} kr" if session["total_cost"] else "-"
            )
            self.loading_table.setItem(i, 5, QTableWidgetItem(cost_str))

            notes = session["notes"][:50] if session["notes"] else ""
            self.loading_table.setItem(i, 6, QTableWidgetItem(notes))

            self.loading_table.item(i, 0).setData(
                Qt.ItemDataRole.UserRole, session["id"]
            )

    def new_loading_session(self):
        """Oppretter ny ladeøkt"""
        ammo_profiles = self.db.get_all("ammo_profiles")
        dialog = LoadingSessionDialog(
            self,
            ammo_profiles=ammo_profiles,
            project_context=_get_active_project_context(),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("loading_sessions", data)
            self.load_loading_sessions()
            QMessageBox.information(
                self, tr("msg_success"), tr("session_logger_loading_saved")
            )

    def edit_loading_session(self):
        """Redigerer valgt ladeøkt"""
        selected = self.loading_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("session_logger_select_loading_first")
            )
            return

        session_id = self.loading_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        session = self.db.get_by_id("loading_sessions", session_id)
        ammo_profiles = self.db.get_all("ammo_profiles")

        dialog = LoadingSessionDialog(
            self,
            session=session,
            ammo_profiles=ammo_profiles,
            project_context=_get_active_project_context(),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("loading_sessions", data, "id = ?", (session_id,))
            self.load_loading_sessions()
            QMessageBox.information(
                self, tr("msg_success"), tr("session_logger_loading_updated")
            )

    def delete_loading_session(self):
        """Sletter valgt ladeøkt"""
        selected = self.loading_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("session_logger_select_loading_first")
            )
            return

        reply = QMessageBox.question(
            self,
            tr("msg_confirm_delete"),
            tr("session_logger_confirm_delete_loading"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            session_id = self.loading_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("loading_sessions", "id = ?", (session_id,))
            self.load_loading_sessions()
            QMessageBox.information(
                self, tr("msg_success"), tr("session_logger_loading_deleted")
            )

    # SKYTEØKTER

    def load_shooting_sessions(self):
        """Laster skyteøkter fra database"""
        sessions = self.db.get_all("shooting_sessions", "date DESC")
        self.shooting_table.setRowCount(len(sessions))

        for i, session in enumerate(sessions):
            self.shooting_table.setItem(i, 0, QTableWidgetItem(session["date"]))
            self.shooting_table.setItem(
                i, 1, QTableWidgetItem(session.get("project_name") or "Default Project")
            )

            # Hent ammunisjonsprofil navn
            ammo_name = "-"
            if session["ammo_profile_id"]:
                ammo = self.db.get_by_id("ammo_profiles", session["ammo_profile_id"])
                if ammo:
                    ammo_name = ammo["name"]
            self.shooting_table.setItem(i, 2, QTableWidgetItem(ammo_name))

            # Hent rifle navn
            rifle_name = "-"
            if session["rifle_id"]:
                rifle = self.db.get_by_id("rifles", session["rifle_id"])
                if rifle:
                    rifle_name = rifle["name"]
            self.shooting_table.setItem(i, 3, QTableWidgetItem(rifle_name))

            self.shooting_table.setItem(
                i, 4, QTableWidgetItem(str(session["rounds_fired"]))
            )

            dist = _format_distance_meters(session["distance_meters"])
            self.shooting_table.setItem(i, 5, QTableWidgetItem(dist))

            weather = _format_temperature_c(session["temperature"])
            self.shooting_table.setItem(i, 6, QTableWidgetItem(weather))

            notes = session["notes"][:50] if session["notes"] else ""
            self.shooting_table.setItem(i, 7, QTableWidgetItem(notes))

            self.shooting_table.item(i, 0).setData(
                Qt.ItemDataRole.UserRole, session["id"]
            )

    def new_shooting_session(self):
        """Oppretter ny skyteøkt"""
        rifles = self.db.get_all("rifles")
        ammo_profiles = self.db.get_all("ammo_profiles")
        dialog = ShootingSessionDialog(
            self,
            rifles=rifles,
            ammo_profiles=ammo_profiles,
            project_context=_get_active_project_context(),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("shooting_sessions", data)
            self.load_shooting_sessions()
            QMessageBox.information(
                self, tr("msg_success"), tr("session_logger_shooting_saved")
            )

    def edit_shooting_session(self):
        """Redigerer valgt skyteøkt"""
        selected = self.shooting_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("session_logger_select_shooting_first")
            )
            return

        session_id = self.shooting_table.item(selected, 0).data(
            Qt.ItemDataRole.UserRole
        )
        session = self.db.get_by_id("shooting_sessions", session_id)
        rifles = self.db.get_all("rifles")
        ammo_profiles = self.db.get_all("ammo_profiles")

        dialog = ShootingSessionDialog(
            self,
            session=session,
            rifles=rifles,
            ammo_profiles=ammo_profiles,
            project_context=_get_active_project_context(),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("shooting_sessions", data, "id = ?", (session_id,))
            self.load_shooting_sessions()
            QMessageBox.information(
                self, tr("msg_success"), tr("session_logger_shooting_updated")
            )

    def delete_shooting_session(self):
        """Sletter valgt skyteøkt"""
        selected = self.shooting_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("session_logger_select_shooting_first")
            )
            return

        reply = QMessageBox.question(
            self,
            tr("msg_confirm_delete"),
            tr("session_logger_confirm_delete_shooting"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            session_id = self.shooting_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("shooting_sessions", "id = ?", (session_id,))
            self.load_shooting_sessions()
            QMessageBox.information(
                self, tr("msg_success"), tr("session_logger_shooting_deleted")
            )


class LoadingSessionDialog(QDialog):
    """Dialog for ladeøkt"""

    def __init__(
        self, parent=None, session=None, ammo_profiles=None, project_context=None
    ):
        super().__init__(parent)
        self.session = session
        self.ammo_profiles = ammo_profiles or []
        self.project_context = project_context or _get_active_project_context()
        self.init_ui()

        if session:
            self.load_session_data()

    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle(tr("session_logger_loading_session_title"))
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Dato
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        self.date.setDisplayFormat("yyyy-MM-dd")
        form.addRow(tr("session_logger_date_label"), self.date)

        self.project_label = QLabel(
            self.project_context.get("project_name", "Default Project")
        )
        form.addRow(tr("session_logger_active_project_label"), self.project_label)

        # Ammunisjonsprofil
        self.ammo_combo = QComboBox()
        self.ammo_combo.addItem(tr("session_logger_select_ammo_profile"), None)
        for ammo in self.ammo_profiles:
            self.ammo_combo.addItem(ammo["name"], ammo["id"])
        form.addRow(tr("session_logger_ammo_profile_label"), self.ammo_combo)

        # Antall
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 10000)
        self.quantity.setValue(50)
        self.quantity.setSuffix(" stk")
        form.addRow(tr("session_logger_loaded_quantity_label"), self.quantity)

        # COAL min/max
        coal_group = QGroupBox(tr("session_logger_coal_spread"))
        coal_layout = QFormLayout()
        coal_group.setLayout(coal_layout)

        self.coal_min = QDoubleSpinBox()
        self.coal_min.setRange(0, 100)
        self.coal_min.setDecimals(2)
        self.coal_min.setSuffix(" mm")
        coal_layout.addRow(tr("session_logger_coal_min"), self.coal_min)

        self.coal_max = QDoubleSpinBox()
        self.coal_max.setRange(0, 100)
        self.coal_max.setDecimals(2)
        self.coal_max.setSuffix(" mm")
        coal_layout.addRow(tr("session_logger_coal_max"), self.coal_max)

        layout.addLayout(form)
        layout.addWidget(coal_group)

        # Krutt min/max
        powder_group = QGroupBox(tr("session_logger_powder_spread"))
        powder_layout = QFormLayout()
        powder_group.setLayout(powder_layout)

        self.powder_min = QDoubleSpinBox()
        self.powder_min.setRange(0, 100)
        self.powder_min.setDecimals(2)
        self.powder_min.setSuffix(" gr")
        powder_layout.addRow(tr("session_logger_powder_min"), self.powder_min)

        self.powder_max = QDoubleSpinBox()
        self.powder_max.setRange(0, 100)
        self.powder_max.setDecimals(2)
        self.powder_max.setSuffix(" gr")
        powder_layout.addRow(tr("session_logger_powder_max"), self.powder_max)

        layout.addWidget(powder_group)

        # Annen info
        form2 = QFormLayout()

        self.time_minutes = QSpinBox()
        self.time_minutes.setRange(0, 600)
        self.time_minutes.setSuffix(" min")
        form2.addRow(tr("session_logger_time_spent"), self.time_minutes)

        self.total_cost = QDoubleSpinBox()
        self.total_cost.setRange(0, 100000)
        self.total_cost.setDecimals(2)
        self.total_cost.setSuffix(" kr")
        form2.addRow(tr("session_logger_total_cost"), self.total_cost)

        layout.addLayout(form2)

        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText(tr("session_logger_loading_notes_placeholder"))
        layout.addWidget(QLabel(tr("session_logger_notes_label")))
        layout.addWidget(self.notes)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("btn_save"))
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(tr("btn_cancel"))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_session_data(self):
        """Laster eksisterende session data"""
        self.date.setDate(QDate.fromString(self.session["date"], "yyyy-MM-dd"))

        # Sett ammunisjonsprofil
        for i in range(self.ammo_combo.count()):
            if self.ammo_combo.itemData(i) == self.session["ammo_profile_id"]:
                self.ammo_combo.setCurrentIndex(i)
                break

        self.quantity.setValue(self.session["quantity"])

        if self.session["coal_min"]:
            self.coal_min.setValue(self.session["coal_min"])
        if self.session["coal_max"]:
            self.coal_max.setValue(self.session["coal_max"])
        if self.session["powder_weight_min"]:
            self.powder_min.setValue(self.session["powder_weight_min"])
        if self.session["powder_weight_max"]:
            self.powder_max.setValue(self.session["powder_weight_max"])
        if self.session["time_minutes"]:
            self.time_minutes.setValue(self.session["time_minutes"])
        if self.session["total_cost"]:
            self.total_cost.setValue(self.session["total_cost"])
        if self.session["notes"]:
            self.notes.setPlainText(self.session["notes"])

    def get_data(self):
        """Returnerer session data"""
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "project_name": self.project_context.get("project_name", "Default Project"),
            "project_path": self.project_context.get("project_path", ""),
            "ammo_profile_id": self.ammo_combo.currentData(),
            "quantity": self.quantity.value(),
            "coal_min": self.coal_min.value() if self.coal_min.value() > 0 else None,
            "coal_max": self.coal_max.value() if self.coal_max.value() > 0 else None,
            "powder_weight_min": (
                self.powder_min.value() if self.powder_min.value() > 0 else None
            ),
            "powder_weight_max": (
                self.powder_max.value() if self.powder_max.value() > 0 else None
            ),
            "time_minutes": (
                self.time_minutes.value() if self.time_minutes.value() > 0 else None
            ),
            "total_cost": (
                self.total_cost.value() if self.total_cost.value() > 0 else None
            ),
            "notes": self.notes.toPlainText(),
        }


class ShootingSessionDialog(QDialog):
    """Dialog for skyteøkt"""

    def __init__(
        self,
        parent=None,
        session=None,
        rifles=None,
        ammo_profiles=None,
        project_context=None,
    ):
        super().__init__(parent)
        self.session = session
        self.rifles = rifles or []
        self.ammo_profiles = ammo_profiles or []
        self.project_context = project_context or _get_active_project_context()
        self.init_ui()

        if session:
            self.load_session_data()

    def _configure_unit_fields(self):
        imperial = _get_global_unit_system() == "imperial"
        self.distance.setSuffix(" yd" if imperial else " m")
        self.distance.setRange(25, 1640 if imperial else 1500)
        self.temperature.setSuffix(" °F" if imperial else " °C")
        (
            self.temperature.setRange(-22, 122)
            if imperial
            else self.temperature.setRange(-30, 50)
        )
        self.wind_speed.setSuffix(" mph" if imperial else " m/s")
        self.best_group.setSuffix(" in" if imperial else " mm")
        self.avg_group.setSuffix(" in" if imperial else " mm")

    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle(tr("session_logger_shooting_session_title"))
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Dato
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        self.date.setDisplayFormat("yyyy-MM-dd")
        form.addRow(tr("session_logger_date_label"), self.date)

        self.project_label = QLabel(
            self.project_context.get("project_name", "Default Project")
        )
        form.addRow(tr("session_logger_active_project_label"), self.project_label)

        # Rifle
        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem(tr("session_logger_select_rifle"), None)
        for rifle in self.rifles:
            self.rifle_combo.addItem(
                f"{rifle['name']} ({rifle['caliber']})", rifle["id"]
            )
        form.addRow(tr("session_logger_rifle_label"), self.rifle_combo)

        # Ammunisjonsprofil
        self.ammo_combo = QComboBox()
        self.ammo_combo.addItem(tr("session_logger_select_ammo_profile"), None)
        for ammo in self.ammo_profiles:
            self.ammo_combo.addItem(ammo["name"], ammo["id"])
        form.addRow(tr("session_logger_ammo_profile_label"), self.ammo_combo)

        # Skudd avfyrt
        self.rounds_fired = QSpinBox()
        self.rounds_fired.setRange(1, 1000)
        self.rounds_fired.setValue(20)
        self.rounds_fired.setSuffix(" rounds")
        form.addRow(tr("session_logger_rounds_fired_label"), self.rounds_fired)

        # Avstand
        self.distance = QSpinBox()
        self.distance.setRange(25, 1500)
        self.distance.setValue(100)
        self.distance.setSuffix(" m")
        form.addRow(tr("session_logger_distance_label"), self.distance)

        layout.addLayout(form)

        # Værforhold
        weather_group = QGroupBox(tr("session_logger_weather_group"))
        weather_layout = QFormLayout()
        weather_group.setLayout(weather_layout)

        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(-30, 50)
        self.temperature.setValue(15)
        self.temperature.setSuffix(" °C")
        weather_layout.addRow(tr("session_logger_temperature_label"), self.temperature)

        self.wind_speed = QSpinBox()
        self.wind_speed.setRange(0, 50)
        self.wind_speed.setSuffix(" m/s")
        weather_layout.addRow(tr("session_logger_wind_label"), self.wind_speed)

        self.humidity = QSpinBox()
        self.humidity.setRange(0, 100)
        self.humidity.setValue(50)
        self.humidity.setSuffix(" %")
        weather_layout.addRow(tr("session_logger_humidity_label"), self.humidity)

        layout.addWidget(weather_group)

        # Prestasjon
        perf_group = QGroupBox(tr("session_logger_performance_group"))
        perf_layout = QFormLayout()
        perf_group.setLayout(perf_layout)

        self.best_group = QDoubleSpinBox()
        self.best_group.setRange(0, 500)
        self.best_group.setDecimals(1)
        self.best_group.setSuffix(" mm")
        perf_layout.addRow(tr("session_logger_best_group_label"), self.best_group)

        self.avg_group = QDoubleSpinBox()
        self.avg_group.setRange(0, 500)
        self.avg_group.setDecimals(1)
        self.avg_group.setSuffix(" mm")
        perf_layout.addRow(tr("session_logger_avg_group_label"), self.avg_group)

        self._configure_unit_fields()

        layout.addWidget(perf_group)

        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText(tr("session_logger_shooting_notes_placeholder"))
        layout.addWidget(QLabel(tr("session_logger_notes_label")))
        layout.addWidget(self.notes)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("btn_save"))
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(tr("btn_cancel"))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_session_data(self):
        """Laster eksisterende session data"""
        self.date.setDate(QDate.fromString(self.session["date"], "yyyy-MM-dd"))

        # Sett rifle
        for i in range(self.rifle_combo.count()):
            if self.rifle_combo.itemData(i) == self.session["rifle_id"]:
                self.rifle_combo.setCurrentIndex(i)
                break

        # Sett ammunisjonsprofil
        for i in range(self.ammo_combo.count()):
            if self.ammo_combo.itemData(i) == self.session["ammo_profile_id"]:
                self.ammo_combo.setCurrentIndex(i)
                break

        self.rounds_fired.setValue(self.session["rounds_fired"])

        if self.session["distance_meters"]:
            self.distance.setValue(
                _to_display_distance(self.session["distance_meters"])
            )
        if self.session["temperature"]:
            self.temperature.setValue(
                _to_display_temperature(self.session["temperature"])
            )
        if self.session["wind_speed"]:
            self.wind_speed.setValue(_to_display_wind(self.session["wind_speed"]))
        if self.session["humidity"]:
            self.humidity.setValue(self.session["humidity"])
        if self.session["best_group_mm"]:
            self.best_group.setValue(_to_display_group(self.session["best_group_mm"]))
        if self.session["avg_group_mm"]:
            self.avg_group.setValue(_to_display_group(self.session["avg_group_mm"]))
        if self.session["notes"]:
            self.notes.setPlainText(self.session["notes"])

    def get_data(self):
        """Returnerer session data"""
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "project_name": self.project_context.get("project_name", "Default Project"),
            "project_path": self.project_context.get("project_path", ""),
            "load_session_id": _resolve_shooting_session_load_session_id(self.session),
            "rifle_id": self.rifle_combo.currentData(),
            "ammo_profile_id": self.ammo_combo.currentData(),
            "rounds_fired": self.rounds_fired.value(),
            "distance_meters": (
                _from_display_distance(self.distance.value())
                if self.distance.value() > 0
                else None
            ),
            "temperature": _from_display_temperature(self.temperature.value()),
            "wind_speed": (
                _from_display_wind(self.wind_speed.value())
                if self.wind_speed.value() > 0
                else None
            ),
            "humidity": self.humidity.value(),
            "best_group_mm": (
                _from_display_group(self.best_group.value())
                if self.best_group.value() > 0
                else None
            ),
            "avg_group_mm": (
                _from_display_group(self.avg_group.value())
                if self.avg_group.value() > 0
                else None
            ),
            "notes": self.notes.toPlainText(),
        }
