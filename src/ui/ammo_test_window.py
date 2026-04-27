"""Ammo Test Module — main window with tabbed UI."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    import pyqtgraph as pg

    HAS_PG = True
except ImportError:
    HAS_PG = False

from ..ammo_test import services
from ..ammo_test.models import AmmoLot, AmmoTestSession, AmmoTestShot

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Colour palette (reused across panels)
# --------------------------------------------------------------------------
_ACCENT = "#2980b9"
_GREEN = "#27ae60"
_ORANGE = "#e67e22"
_RED = "#e74c3c"
_BG = "#1e2530"
_PANEL = "#252d3a"
_BORDER = "#3a4556"
_TEXT = "#ecf0f1"
_MUTED = "#95a5a6"

_STAT_CARD_CSS = """
    QFrame {{
        background: {bg};
        border: 1px solid {border};
        border-radius: 8px;
    }}
""".format(
    bg=_PANEL, border=_BORDER
)

_BTN_PRIMARY = f"""
    QPushButton {{
        background: {_ACCENT}; color: white;
        border: none; border-radius: 6px;
        padding: 6px 16px; font-weight: bold;
    }}
    QPushButton:hover {{ background: #3498db; }}
    QPushButton:pressed {{ background: #1a6fa3; }}
"""
_BTN_DANGER = f"""
    QPushButton {{
        background: {_RED}; color: white;
        border: none; border-radius: 6px;
        padding: 6px 16px; font-weight: bold;
    }}
    QPushButton:hover {{ background: #f05050; }}
"""
_BTN_NEUTRAL = f"""
    QPushButton {{
        background: {_BORDER}; color: {_TEXT};
        border: none; border-radius: 6px;
        padding: 6px 16px;
    }}
    QPushButton:hover {{ background: #4a5a70; }}
"""

_TABLE_CSS = f"""
    QTableWidget {{
        background: {_PANEL}; color: {_TEXT};
        gridline-color: {_BORDER};
        border: 1px solid {_BORDER}; border-radius: 4px;
    }}
    QTableWidget::item:selected {{ background: {_ACCENT}; }}
    QHeaderView::section {{
        background: {_BG}; color: {_MUTED};
        border: none; padding: 4px 8px; font-weight: bold;
    }}
"""


def _label(text: str, bold: bool = False, color: str = _TEXT) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {color};")
    if bold:
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
    return lbl


def _stat_card(title: str, value: str, unit: str = "", color: str = _TEXT) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(_STAT_CARD_CSS)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setStyleSheet(f"color: {_MUTED}; font-size: 9pt;")
    v = QLabel(value)
    v.setStyleSheet(f"color: {color}; font-size: 18pt; font-weight: bold;")
    u = QLabel(unit)
    u.setStyleSheet(f"color: {_MUTED}; font-size: 8pt;")
    lay.addWidget(t)
    lay.addWidget(v)
    if unit:
        lay.addWidget(u)
    return frame


# ==========================================================================
# Tab 1 — Ammo-lot registration
# ==========================================================================


class LotPanel(QWidget):
    lot_selected = pyqtSignal(int)  # lot_id

    def __init__(self, db: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = db
        self._editing_id: int | None = None
        self._build_ui()
        self._refresh_table()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Left: form
        form_group = QGroupBox("Register / Edit Lot")
        form_group.setStyleSheet(
            f"QGroupBox {{ color:{_TEXT}; border:1px solid {_BORDER}; border-radius:6px; margin-top:8px; padding-top:8px; }}"
        )
        form_group.setMinimumWidth(320)
        form_group.setMaximumWidth(380)
        form = QFormLayout(form_group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(8)

        def _fe(placeholder: str = "") -> QLineEdit:
            e = QLineEdit()
            e.setPlaceholderText(placeholder)
            e.setStyleSheet(
                f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px; padding:4px 8px;"
            )
            return e

        self._brand = _fe("e.g. Norma, Lapua, Federal")
        self._model = _fe("e.g. Oryx, Scenar, Gold Medal")
        self._caliber = _fe("e.g. .308 Win, 6.5 Creedmoor")
        self._weight = QDoubleSpinBox()
        self._weight.setRange(0, 999)
        self._weight.setSuffix(" gr")
        self._weight.setDecimals(1)
        self._weight.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._lot_num = _fe("Lot / batch number")
        self._purchase_date = _fe(date.today().isoformat())
        self._price = QDoubleSpinBox()
        self._price.setRange(0, 99999)
        self._price.setSuffix(" kr")
        self._price.setDecimals(2)
        self._price.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._store = _fe("Store / online shop")
        self._count = QSpinBox()
        self._count.setRange(0, 99999)
        self._count.setSuffix(" stk")
        self._count.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._remaining = QSpinBox()
        self._remaining.setRange(0, 99999)
        self._remaining.setSuffix(" stk")
        self._remaining.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._notes = QTextEdit()
        self._notes.setMaximumHeight(60)
        self._notes.setPlaceholderText("Notes about this lot...")
        self._notes.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )

        form.addRow(_label("Brand*"), self._brand)
        form.addRow(_label("Model*"), self._model)
        form.addRow(_label("Caliber*"), self._caliber)
        form.addRow(_label("Bullet weight"), self._weight)
        form.addRow(_label("Lot number*"), self._lot_num)
        form.addRow(_label("Purchase date"), self._purchase_date)
        form.addRow(_label("Price"), self._price)
        form.addRow(_label("Store"), self._store)
        form.addRow(_label("Qty purchased"), self._count)
        form.addRow(_label("Remaining"), self._remaining)
        form.addRow(_label("Notes"), self._notes)

        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("Save Lot")
        self._save_btn.setStyleSheet(_BTN_PRIMARY)
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setStyleSheet(_BTN_NEUTRAL)
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setStyleSheet(_BTN_DANGER)
        self._delete_btn.setVisible(False)
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._clear_btn)
        btn_row.addWidget(self._delete_btn)
        form.addRow("", btn_row)

        self._save_btn.clicked.connect(self._on_save)
        self._clear_btn.clicked.connect(self._clear_form)
        self._delete_btn.clicked.connect(self._on_delete)

        root.addWidget(form_group)

        # Right: lot list
        right = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(_label("Lot Inventory", bold=True))
        header.addStretch()
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Søk merke / kaliber...")
        self._filter_edit.setMaximumWidth(200)
        self._filter_edit.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px; padding:4px 8px;"
        )
        self._filter_edit.textChanged.connect(self._refresh_table)
        header.addWidget(self._filter_edit)
        right.addLayout(header)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Brand", "Model", "Caliber", "Weight", "Lot #", "Qty remaining"]
        )
        self._table.setStyleSheet(_TABLE_CSS)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        self._table.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        self._table.itemSelectionChanged.connect(self._on_table_select)
        right.addWidget(self._table)

        right_widget = QWidget()
        right_widget.setLayout(right)
        root.addWidget(right_widget, 1)

    def _refresh_table(self) -> None:
        filt = (
            self._filter_edit.text().strip().lower()
            if hasattr(self, "_filter_edit")
            else ""
        )
        lots = services.list_lots(self._db)
        if filt:
            lots = [
                lot
                for lot in lots
                if filt in lot.brand.lower()
                or filt in lot.caliber.lower()
                or filt in lot.model.lower()
            ]
        self._table.setRowCount(len(lots))
        self._lots_cache = lots
        for i, lot in enumerate(lots):

            def _item(v: Any) -> QTableWidgetItem:
                return QTableWidgetItem(str(v) if v is not None else "")

            self._table.setItem(i, 0, _item(lot.brand))
            self._table.setItem(i, 1, _item(lot.model))
            self._table.setItem(i, 2, _item(lot.caliber))
            self._table.setItem(
                i,
                3,
                _item(f"{lot.bullet_weight_gr} gr" if lot.bullet_weight_gr else ""),
            )
            self._table.setItem(i, 4, _item(lot.lot_number))
            remaining = lot.count_remaining
            item = _item(f"{remaining} stk" if remaining is not None else "")
            if remaining is not None and remaining < 20:
                item.setForeground(QColor(_ORANGE))
            self._table.setItem(i, 5, item)

    def _on_table_select(self) -> None:
        rows = self._table.selectedItems()
        if not rows:
            return
        row = self._table.currentRow()
        if row < 0 or row >= len(self._lots_cache):
            return
        lot = self._lots_cache[row]
        self._editing_id = lot.id
        self._brand.setText(lot.brand)
        self._model.setText(lot.model)
        self._caliber.setText(lot.caliber)
        self._weight.setValue(lot.bullet_weight_gr or 0)
        self._lot_num.setText(lot.lot_number)
        self._purchase_date.setText(lot.purchase_date or "")
        self._price.setValue(lot.purchase_price or 0)
        self._store.setText(lot.store or "")
        self._count.setValue(lot.count_purchased or 0)
        self._remaining.setValue(lot.count_remaining or 0)
        self._notes.setPlainText(lot.notes or "")
        self._delete_btn.setVisible(True)
        if lot.id is not None:
            self.lot_selected.emit(lot.id)

    def _on_save(self) -> None:
        brand = self._brand.text().strip()
        model = self._model.text().strip()
        caliber = self._caliber.text().strip()
        lot_num = self._lot_num.text().strip()
        if not (brand and model and caliber and lot_num):
            QMessageBox.warning(
                self,
                "Missing data",
                "Brand, model, caliber and lot number are required.",
            )
            return
        lot = AmmoLot(
            id=self._editing_id,
            brand=brand,
            model=model,
            caliber=caliber,
            bullet_weight_gr=self._weight.value() or None,
            lot_number=lot_num,
            purchase_date=self._purchase_date.text().strip() or None,
            purchase_price=self._price.value() or None,
            store=self._store.text().strip() or None,
            count_purchased=self._count.value() or None,
            count_remaining=self._remaining.value() or None,
            expiry_date=None,
            storage_notes=None,
            notes=self._notes.toPlainText().strip() or None,
        )
        lot_id = services.save_lot(self._db, lot)
        self._editing_id = lot_id
        self._delete_btn.setVisible(True)
        self._refresh_table()
        if lot_id and lot_id > 0:
            self.lot_selected.emit(lot_id)

    def _clear_form(self) -> None:
        self._editing_id = None
        self._brand.clear()
        self._model.clear()
        self._caliber.clear()
        self._weight.setValue(0)
        self._lot_num.clear()
        self._purchase_date.clear()
        self._price.setValue(0)
        self._store.clear()
        self._count.setValue(0)
        self._remaining.setValue(0)
        self._notes.clear()
        self._delete_btn.setVisible(False)

    def _on_delete(self) -> None:
        if self._editing_id is None:
            return
        if (
            QMessageBox.question(
                self,
                "Delete lot",
                "Er du sikker? Alle sesjoner tilknyttet dette lotet slettes også.",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        services.delete_lot(self._db, self._editing_id)
        self._clear_form()
        self._refresh_table()


# ==========================================================================
# Tab 2 — Test session
# ==========================================================================


class SessionPanel(QWidget):
    def __init__(
        self, db: Any, rifles: list[dict], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._db = db
        self._rifles = rifles
        self._active_session_id: int | None = None
        self._build_ui()

    def set_lot(self, lot_id: int) -> None:
        self._active_lot_id = lot_id
        self._refresh_sessions()

    def _build_ui(self) -> None:
        self._active_lot_id: int | None = None
        root = QSplitter(Qt.Orientation.Horizontal, self)
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.addWidget(root)

        # --- Left: session meta form ---
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 8, 0)

        meta = QGroupBox("Session Details")
        meta.setStyleSheet(
            f"QGroupBox {{ color:{_TEXT}; border:1px solid {_BORDER}; border-radius:6px; margin-top:8px; padding-top:8px; }}"
        )
        mf = QFormLayout(meta)
        mf.setSpacing(7)

        def _sp(lo: float, hi: float, suf: str = "", dec: int = 1) -> QDoubleSpinBox:
            w = QDoubleSpinBox()
            w.setRange(lo, hi)
            w.setSuffix(f" {suf}")
            w.setDecimals(dec)
            w.setStyleSheet(
                f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
            )
            return w

        def _fe(ph: str = "") -> QLineEdit:
            e = QLineEdit()
            e.setPlaceholderText(ph)
            e.setStyleSheet(
                f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px; padding:4px 8px;"
            )
            return e

        self._rifle_combo = QComboBox()
        self._rifle_combo.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._rifle_combo.addItem("— Select weapon —", None)
        for r in self._rifles:
            self._rifle_combo.addItem(r.get("name", ""), r.get("id"))

        self._session_date = _fe(date.today().isoformat())
        self._session_date.setText(date.today().isoformat())
        self._distance = _sp(0, 2000, "m", 0)
        self._temp = _sp(-40, 60, "°C", 1)
        self._wind = _sp(0, 30, "m/s", 1)
        self._pressure = _sp(800, 1100, "hPa", 1)
        self._barrel_state = QComboBox()
        self._barrel_state.addItems(["Cold bore", "Warm bore", "Unknown"])
        self._barrel_state.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._prior_shots = QSpinBox()
        self._prior_shots.setRange(0, 999)
        self._prior_shots.setSuffix(" skudd")
        self._prior_shots.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._group_size = _sp(0, 500, "mm", 2)
        self._poi_x = _sp(-500, 500, "mm", 1)
        self._poi_y = _sp(-500, 500, "mm", 1)
        self._session_notes = QTextEdit()
        self._session_notes.setMaximumHeight(60)
        self._session_notes.setPlaceholderText("Session notes...")
        self._session_notes.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )

        mf.addRow(_label("Weapon"), self._rifle_combo)
        mf.addRow(_label("Date"), self._session_date)
        mf.addRow(_label("Distance"), self._distance)
        mf.addRow(_label("Temperature"), self._temp)
        mf.addRow(_label("Wind"), self._wind)
        mf.addRow(_label("Barometric pressure"), self._pressure)
        mf.addRow(_label("Barrel state"), self._barrel_state)
        mf.addRow(_label("Prior shots in string"), self._prior_shots)
        mf.addRow(_label("Group size"), self._group_size)
        mf.addRow(_label("POI X (horizontal)"), self._poi_x)
        mf.addRow(_label("POI Y (vertical)"), self._poi_y)
        mf.addRow(_label("Notes"), self._session_notes)

        btn_row = QHBoxLayout()
        self._save_session_btn = QPushButton("Save Session")
        self._save_session_btn.setStyleSheet(_BTN_PRIMARY)
        self._new_session_btn = QPushButton("New Session")
        self._new_session_btn.setStyleSheet(_BTN_NEUTRAL)
        btn_row.addWidget(self._save_session_btn)
        btn_row.addWidget(self._new_session_btn)
        mf.addRow("", btn_row)

        self._save_session_btn.clicked.connect(self._on_save_session)
        self._new_session_btn.clicked.connect(self._clear_session)

        left_lay.addWidget(meta)
        left_lay.addStretch()
        root.addWidget(left)

        # --- Right: shot table + velocity graph ---
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(8, 0, 0, 0)

        # Session selector
        sess_header = QHBoxLayout()
        sess_header.addWidget(_label("Sessions for this lot", bold=True))
        self._sessions_table = QTableWidget()
        self._sessions_table.setColumnCount(5)
        self._sessions_table.setHorizontalHeaderLabels(
            ["Date", "Weapon", "Distance", "Snitt fps", "Gruppe"]
        )
        self._sessions_table.setStyleSheet(_TABLE_CSS)
        self._sessions_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        self._sessions_table.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        self._sessions_table.setMaximumHeight(150)
        self._sessions_table.itemSelectionChanged.connect(self._on_session_selected)

        right_lay.addWidget(_label("Sessions for this lot", bold=True))
        right_lay.addWidget(self._sessions_table)

        # Shot logger
        shot_group = QGroupBox("Shot Log")
        shot_group.setStyleSheet(
            f"QGroupBox {{ color:{_TEXT}; border:1px solid {_BORDER}; border-radius:6px; margin-top:8px; padding-top:8px; }}"
        )
        shot_lay = QVBoxLayout(shot_group)

        self._shot_table = QTableWidget()
        self._shot_table.setColumnCount(8)
        self._shot_table.setHorizontalHeaderLabels(
            [
                "#",
                "Velocity (fps)",
                "Cold bore",
                "Calibration",
                "Dud",
                "Light strike",
                "FTF",
                "FTE",
            ]
        )
        self._shot_table.setStyleSheet(_TABLE_CSS)
        self._shot_table.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        self._shot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # type: ignore[union-attr]
        self._shot_table.setMinimumHeight(200)

        shot_btn_row = QHBoxLayout()
        add_shot_btn = QPushButton("+ Add Shot")
        add_shot_btn.setStyleSheet(_BTN_PRIMARY)
        rm_shot_btn = QPushButton("Remove Selected")
        rm_shot_btn.setStyleSheet(_BTN_DANGER)
        save_shots_btn = QPushButton("Save Shots")
        save_shots_btn.setStyleSheet(_BTN_NEUTRAL)
        shot_btn_row.addWidget(add_shot_btn)
        shot_btn_row.addWidget(rm_shot_btn)
        shot_btn_row.addStretch()
        shot_btn_row.addWidget(save_shots_btn)

        add_shot_btn.clicked.connect(self._add_shot_row)
        rm_shot_btn.clicked.connect(self._remove_shot_row)
        save_shots_btn.clicked.connect(self._save_shots)

        shot_lay.addWidget(self._shot_table)
        shot_lay.addLayout(shot_btn_row)

        # Stats bar
        self._stats_bar = QHBoxLayout()
        self._stat_avg = _stat_card("Avg velocity", "—", "fps")
        self._stat_es = _stat_card("ES", "—", "fps")
        self._stat_sd = _stat_card("SD", "—", "fps")
        self._stat_rel = _stat_card("Reliability", "—", "%", _GREEN)
        for w in [self._stat_avg, self._stat_es, self._stat_sd, self._stat_rel]:
            self._stats_bar.addWidget(w)

        right_lay.addLayout(self._stats_bar)
        right_lay.addWidget(shot_group)

        # Velocity graph
        if HAS_PG:
            self._vel_plot = pg.PlotWidget(title="Velocity per shot")
            self._vel_plot.setBackground(_PANEL)
            self._vel_plot.setLabel("left", "fps")
            self._vel_plot.setLabel("bottom", "Shot #")
            self._vel_plot.setMaximumHeight(180)
            right_lay.addWidget(self._vel_plot)

        root.addWidget(right)
        root.setSizes([340, 660])

    def _refresh_sessions(self) -> None:
        if self._active_lot_id is None:
            return
        self._sessions_cache = services.get_sessions_for_lot(
            self._db, self._active_lot_id
        )
        self._sessions_table.setRowCount(len(self._sessions_cache))
        for i, s in enumerate(self._sessions_cache):

            def _it(v: Any) -> QTableWidgetItem:
                return QTableWidgetItem(str(v) if v is not None else "")

            self._sessions_table.setItem(i, 0, _it(s.test_date))
            self._sessions_table.setItem(i, 1, _it(s.rifle_name))
            self._sessions_table.setItem(
                i, 2, _it(f"{s.distance_m} m" if s.distance_m else "")
            )
            self._sessions_table.setItem(
                i, 3, _it(f"{s.avg_vel_fps}" if s.avg_vel_fps else "")
            )
            self._sessions_table.setItem(
                i, 4, _it(f"{s.group_size_mm} mm" if s.group_size_mm else "")
            )

    def _on_session_selected(self) -> None:
        row = self._sessions_table.currentRow()
        if (
            row < 0
            or not hasattr(self, "_sessions_cache")
            or row >= len(self._sessions_cache)
        ):
            return
        s = self._sessions_cache[row]
        self._active_session_id = s.id
        self._session_date.setText(s.test_date)
        self._distance.setValue(s.distance_m or 0)
        self._temp.setValue(s.temp_c or 0)
        self._wind.setValue(s.wind_mps or 0)
        self._pressure.setValue(s.barometric_pressure_hpa or 0)
        barrel_state_idx = {"cold": 0, "warm": 1, "unknown": 2}.get(
            s.barrel_state or "", 2
        )
        self._barrel_state.setCurrentIndex(barrel_state_idx)
        self._prior_shots.setValue(s.shots_in_prior_string or 0)
        self._group_size.setValue(s.group_size_mm or 0)
        self._poi_x.setValue(s.poi_x_mm or 0)
        self._poi_y.setValue(s.poi_y_mm or 0)
        self._session_notes.setPlainText(s.notes or "")
        # Restore rifle selection
        for i in range(self._rifle_combo.count()):
            if self._rifle_combo.itemData(i) == s.rifle_id:
                self._rifle_combo.setCurrentIndex(i)
                break
        if s.id is not None:
            self._load_shots(s.id)

    def _load_shots(self, session_id: int) -> None:
        shots = services.get_shots_for_session(self._db, session_id)
        self._shot_table.setRowCount(0)
        for shot in shots:
            self._append_shot_row(
                shot.shot_number,
                shot.velocity_fps,
                shot.is_cold_bore,
                shot.is_calibration,
                shot.is_dud,
                shot.is_light_strike,
                shot.is_ftf,
                shot.is_fte,
            )
        self._update_stats()

    def _add_shot_row(self) -> None:
        row = self._shot_table.rowCount()
        self._shot_table.insertRow(row)
        self._shot_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        vel = QDoubleSpinBox()
        vel.setRange(0, 5000)
        vel.setDecimals(1)
        vel.setStyleSheet(f"background:{_PANEL}; color:{_TEXT};")
        vel.valueChanged.connect(self._update_stats)
        self._shot_table.setCellWidget(row, 1, vel)
        for col in range(2, 8):
            cb = QCheckBox()
            cb.setStyleSheet("margin-left: 10px;")
            self._shot_table.setCellWidget(row, col, cb)

    def _append_shot_row(
        self,
        num: int,
        vel: float | None,
        cold: bool,
        cal: bool,
        dud: bool,
        ls: bool,
        ftf: bool,
        fte: bool,
    ) -> None:
        row = self._shot_table.rowCount()
        self._shot_table.insertRow(row)
        self._shot_table.setItem(row, 0, QTableWidgetItem(str(num)))
        v = QDoubleSpinBox()
        v.setRange(0, 5000)
        v.setDecimals(1)
        v.setValue(vel or 0)
        v.setStyleSheet(f"background:{_PANEL}; color:{_TEXT};")
        v.valueChanged.connect(self._update_stats)
        self._shot_table.setCellWidget(row, 1, v)
        for col, val in zip(range(2, 8), [cold, cal, dud, ls, ftf, fte]):
            cb = QCheckBox()
            cb.setChecked(bool(val))
            cb.setStyleSheet("margin-left: 10px;")
            self._shot_table.setCellWidget(row, col, cb)

    def _remove_shot_row(self) -> None:
        row = self._shot_table.currentRow()
        if row >= 0:
            self._shot_table.removeRow(row)
        self._update_stats()

    def _update_stats(self) -> None:
        vels = []
        for row in range(self._shot_table.rowCount()):
            dud_cb = self._shot_table.cellWidget(row, 4)
            v_w = self._shot_table.cellWidget(row, 1)
            if v_w and isinstance(v_w, QDoubleSpinBox) and v_w.value() > 0:
                if not (
                    dud_cb and isinstance(dud_cb, QCheckBox) and dud_cb.isChecked()
                ):
                    vels.append(v_w.value())
        if vels:
            import statistics as st

            avg = sum(vels) / len(vels)
            es = max(vels) - min(vels)
            sd = st.pstdev(vels) if len(vels) > 1 else 0.0
            self._stat_avg.findChildren(QLabel)[1].setText(f"{avg:.1f}")
            self._stat_es.findChildren(QLabel)[1].setText(f"{es:.1f}")
            self._stat_sd.findChildren(QLabel)[1].setText(f"{sd:.1f}")
        else:
            for w in [self._stat_avg, self._stat_es, self._stat_sd]:
                w.findChildren(QLabel)[1].setText("—")

        # Reliability
        total = self._shot_table.rowCount()
        duds = 0
        for row in range(total):
            for col in [4, 5, 6, 7]:
                cb = self._shot_table.cellWidget(row, col)
                if cb and isinstance(cb, QCheckBox) and cb.isChecked():
                    duds += 1
                    break
        if total:
            rel = 100 * (total - duds) / total
            color = _GREEN if rel >= 99 else _ORANGE if rel >= 95 else _RED
            lbl = self._stat_rel.findChildren(QLabel)[1]
            lbl.setText(f"{rel:.1f}")
            lbl.setStyleSheet(f"color: {color}; font-size: 18pt; font-weight: bold;")

        if HAS_PG and hasattr(self, "_vel_plot") and vels:
            self._vel_plot.clear()
            x = list(range(1, len(vels) + 1))
            self._vel_plot.plot(
                x,
                vels,
                pen=pg.mkPen(_ACCENT, width=2),
                symbol="o",
                symbolBrush=_ACCENT,
                symbolSize=7,
            )
            avg_line = pg.InfiniteLine(
                pos=sum(vels) / len(vels),
                angle=0,
                pen=pg.mkPen(_GREEN, width=1, style=Qt.PenStyle.DashLine),
            )
            self._vel_plot.addItem(avg_line)

    def _on_save_session(self) -> None:
        if self._active_lot_id is None:
            QMessageBox.warning(
                self, "Select lot", "Select an ammo lot from the Lot tab first."
            )
            return
        rifle_id = self._rifle_combo.currentData()
        rifle_name = self._rifle_combo.currentText() if rifle_id else ""
        barrel_state_map = {0: "cold", 1: "warm", 2: "unknown"}
        session = AmmoTestSession(
            id=self._active_session_id,
            lot_id=self._active_lot_id,
            rifle_id=rifle_id,
            rifle_name=rifle_name,
            barrel_configuration_id=None,
            barrel_name="",
            test_date=self._session_date.text().strip() or date.today().isoformat(),
            distance_m=self._distance.value() or None,
            temp_c=self._temp.value() or None,
            wind_mps=self._wind.value() or None,
            wind_dir_deg=None,
            barometric_pressure_hpa=self._pressure.value() or None,
            barrel_state=barrel_state_map.get(self._barrel_state.currentIndex()),
            shots_in_prior_string=self._prior_shots.value() or None,
            group_size_mm=self._group_size.value() or None,
            poi_x_mm=self._poi_x.value() or None,
            poi_y_mm=self._poi_y.value() or None,
            image_path=None,
            notes=self._session_notes.toPlainText().strip() or None,
        )
        sid = services.save_session(self._db, session)
        self._active_session_id = sid
        self._save_shots()
        self._refresh_sessions()

    def _save_shots(self) -> None:
        if self._active_session_id is None:
            return
        shots = []
        for row in range(self._shot_table.rowCount()):

            def _cb(col: int) -> bool:
                w = self._shot_table.cellWidget(row, col)
                return bool(w and isinstance(w, QCheckBox) and w.isChecked())

            v_w = self._shot_table.cellWidget(row, 1)
            vel = v_w.value() if isinstance(v_w, QDoubleSpinBox) else None
            shots.append(
                AmmoTestShot(
                    id=None,
                    session_id=self._active_session_id,
                    shot_number=row + 1,
                    velocity_fps=vel or None,
                    is_cold_bore=_cb(2),
                    is_calibration=_cb(3),
                    is_dud=_cb(4),
                    is_light_strike=_cb(5),
                    is_ftf=_cb(6),
                    is_fte=_cb(7),
                )
            )
        services.save_shots(self._db, self._active_session_id, shots)

    def _clear_session(self) -> None:
        self._active_session_id = None
        self._session_date.setText(date.today().isoformat())
        self._distance.setValue(0)
        self._temp.setValue(0)
        self._wind.setValue(0)
        self._group_size.setValue(0)
        self._poi_x.setValue(0)
        self._poi_y.setValue(0)
        self._session_notes.clear()
        self._shot_table.setRowCount(0)


# ==========================================================================
# Tab 3 — LOT comparison with graphs
# ==========================================================================


class ComparisonPanel(QWidget):
    def __init__(self, db: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = db
        self._build_ui()

    def refresh(self) -> None:
        self._reload_lots()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(_label("Compare Lots", bold=True))
        top.addStretch()
        self._brand_filter = QComboBox()
        self._brand_filter.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._brand_filter.setMinimumWidth(160)
        self._caliber_filter = QComboBox()
        self._caliber_filter.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
        )
        self._caliber_filter.setMinimumWidth(140)
        compare_btn = QPushButton("Compare")
        compare_btn.setStyleSheet(_BTN_PRIMARY)
        compare_btn.clicked.connect(self._run_comparison)
        top.addWidget(_label("Brand:"))
        top.addWidget(self._brand_filter)
        top.addWidget(_label("Caliber:"))
        top.addWidget(self._caliber_filter)
        top.addWidget(compare_btn)
        root.addLayout(top)

        # Summary table
        self._cmp_table = QTableWidget()
        self._cmp_table.setColumnCount(7)
        self._cmp_table.setHorizontalHeaderLabels(
            [
                "Lot #",
                "Purchased",
                "Avg fps",
                "ES (fps)",
                "SD (fps)",
                "Avg group (mm)",
                "Reliability %",
            ]
        )
        self._cmp_table.setStyleSheet(_TABLE_CSS)
        self._cmp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._cmp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        self._cmp_table.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        self._cmp_table.setMaximumHeight(180)
        root.addWidget(self._cmp_table)

        # Graphs
        if HAS_PG:
            graphs_row = QHBoxLayout()

            self._vel_bar = pg.PlotWidget(title="Avg velocity (fps)")
            self._vel_bar.setBackground(_PANEL)
            graphs_row.addWidget(self._vel_bar)

            self._es_bar = pg.PlotWidget(title="ES (fps) — lavere er bedre")
            self._es_bar.setBackground(_PANEL)
            graphs_row.addWidget(self._es_bar)

            self._group_bar = pg.PlotWidget(title="Snitt gruppe (mm) — lavere er bedre")
            self._group_bar.setBackground(_PANEL)
            graphs_row.addWidget(self._group_bar)

            root.addLayout(graphs_row)

            self._rel_bar = pg.PlotWidget(title="Reliability (%)")
            self._rel_bar.setBackground(_PANEL)
            self._rel_bar.setMaximumHeight(160)
            root.addWidget(self._rel_bar)
        else:
            root.addWidget(_label("Install pyqtgraph for graph display.", color=_MUTED))

        self._reload_lots()

    def _reload_lots(self) -> None:
        brands = ["— Alle merker —"] + services.list_brands(self._db)
        calibers = ["— Alle kalibre —"] + services.list_calibers(self._db)
        cur_brand = self._brand_filter.currentText()
        cur_cal = self._caliber_filter.currentText()
        self._brand_filter.clear()
        self._caliber_filter.clear()
        self._brand_filter.addItems(brands)
        self._caliber_filter.addItems(calibers)
        idx_b = self._brand_filter.findText(cur_brand)
        idx_c = self._caliber_filter.findText(cur_cal)
        if idx_b >= 0:
            self._brand_filter.setCurrentIndex(idx_b)
        if idx_c >= 0:
            self._caliber_filter.setCurrentIndex(idx_c)

    def _run_comparison(self) -> None:
        brand = self._brand_filter.currentText()
        caliber = self._caliber_filter.currentText()
        lots = services.list_lots(
            self._db,
            brand=None if brand.startswith("—") else brand,
            caliber=None if caliber.startswith("—") else caliber,
        )
        if not lots:
            self._cmp_table.setRowCount(0)
            return
        result = services.build_lot_comparison(self._db, [lot.id for lot in lots if lot.id])  # type: ignore[misc]

        rows_data = []
        for lot in result.lots:
            rows_data.append(
                {
                    "lot": lot,
                    "avg_vel": result.avg_vel(lot.id),  # type: ignore[arg-type]
                    "avg_es": result.avg_es(lot.id),  # type: ignore[arg-type]
                    "avg_group": result.avg_group(lot.id),  # type: ignore[arg-type]
                    "rel": result.reliability_pct(lot.id),  # type: ignore[arg-type]
                }
            )

        # SD per lot
        def _avg_sd(lot_id: int) -> float | None:
            sess = result.sessions_by_lot.get(lot_id, [])
            vals = [s.sd_fps for s in sess if s.sd_fps]
            return round(sum(vals) / len(vals), 1) if vals else None

        self._cmp_table.setRowCount(len(rows_data))
        labels = []
        vels, es_vals, groups, rels = [], [], [], []

        for i, rd in enumerate(rows_data):
            lot = rd["lot"]
            labels.append(lot.lot_number[:12])

            def _cell(v: Any, fmt: str = "") -> QTableWidgetItem:
                txt = (
                    fmt.format(v)
                    if fmt and v is not None
                    else (str(v) if v is not None else "—")
                )
                return QTableWidgetItem(txt)

            self._cmp_table.setItem(i, 0, _cell(lot.lot_number))
            self._cmp_table.setItem(i, 1, _cell(lot.purchase_date))
            self._cmp_table.setItem(i, 2, _cell(rd["avg_vel"], "{:.1f}"))
            self._cmp_table.setItem(i, 3, _cell(rd["avg_es"], "{:.1f}"))
            self._cmp_table.setItem(i, 4, _cell(_avg_sd(lot.id), "{:.1f}"))  # type: ignore[arg-type]
            group_item = _cell(rd["avg_group"], "{:.2f}")
            if rd["avg_group"] is not None:
                color = (
                    _GREEN
                    if rd["avg_group"] < 25
                    else _ORANGE if rd["avg_group"] < 50 else _RED
                )
                group_item.setForeground(QColor(color))
            self._cmp_table.setItem(i, 5, group_item)
            rel_item = _cell(rd["rel"], "{:.1f}")
            if rd["rel"] is not None:
                color = (
                    _GREEN if rd["rel"] >= 99 else _ORANGE if rd["rel"] >= 95 else _RED
                )
                rel_item.setForeground(QColor(color))
            self._cmp_table.setItem(i, 6, rel_item)

            vels.append(rd["avg_vel"] or 0)
            es_vals.append(rd["avg_es"] or 0)
            groups.append(rd["avg_group"] or 0)
            rels.append(rd["rel"] or 0)

        if not HAS_PG:
            return

        x = list(range(len(labels)))

        def _bar_chart(
            plot: Any, values: list[float], title: str, col: str = _ACCENT
        ) -> None:
            plot.clear()
            plot.setTitle(title)
            bar_item = pg.BarGraphItem(x=x, height=values, width=0.6, brush=col)
            plot.addItem(bar_item)
            ax = plot.getAxis("bottom")
            ax.setTicks([list(zip(x, labels))])

        _bar_chart(self._vel_bar, vels, "Avg velocity (fps)", _ACCENT)
        _bar_chart(self._es_bar, es_vals, "ES (fps) — lavere er bedre", _ORANGE)
        _bar_chart(self._group_bar, groups, "Avg gruppe (mm) — lavere er bedre", _GREEN)
        _bar_chart(self._rel_bar, rels, "Reliability (%)", _GREEN)


# ==========================================================================
# Tab 4 — Weapon matrix
# ==========================================================================


class WeaponMatrixPanel(QWidget):
    def __init__(self, db: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = db
        self._build_ui()

    def refresh(self) -> None:
        self._reload_lots()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(_label("Våpenmatrise — samme lot i flere våpen", bold=True))
        top.addStretch()
        self._lot_combo = QComboBox()
        self._lot_combo.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px; min-width:220px;"
        )
        run_btn = QPushButton("Show Matrix")
        run_btn.setStyleSheet(_BTN_PRIMARY)
        run_btn.clicked.connect(self._run_matrix)
        top.addWidget(_label("Lot:"))
        top.addWidget(self._lot_combo)
        top.addWidget(run_btn)
        root.addLayout(top)

        self._matrix_table = QTableWidget()
        self._matrix_table.setColumnCount(6)
        self._matrix_table.setHorizontalHeaderLabels(
            [
                "Weapon",
                "Sesjoner",
                "Snitt fps",
                "ES (fps)",
                "Snitt gruppe (mm)",
                "Reliabilitet %",
            ]
        )
        self._matrix_table.setStyleSheet(_TABLE_CSS)
        self._matrix_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        self._matrix_table.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        root.addWidget(self._matrix_table)

        if HAS_PG:
            self._matrix_plot = pg.PlotWidget(
                title="Gruppe per våpen (mm — lavere er bedre)"
            )
            self._matrix_plot.setBackground(_PANEL)
            root.addWidget(self._matrix_plot)

        self._reload_lots()

    def _reload_lots(self) -> None:
        lots = services.list_lots(self._db)
        self._matrix_lots = lots
        self._lot_combo.clear()
        for lot in lots:
            self._lot_combo.addItem(
                f"{lot.brand} {lot.model} — {lot.lot_number}", lot.id
            )

    def _run_matrix(self) -> None:
        lot_id = self._lot_combo.currentData()
        if lot_id is None:
            return
        rows = services.build_weapon_matrix(self._db, lot_id)
        self._matrix_table.setRowCount(len(rows))
        labels, groups = [], []
        for i, r in enumerate(rows):

            def _it(v: Any) -> QTableWidgetItem:
                return QTableWidgetItem(str(v) if v is not None else "—")

            self._matrix_table.setItem(i, 0, _it(r["rifle_name"]))
            self._matrix_table.setItem(i, 1, _it(r["session_count"]))
            self._matrix_table.setItem(
                i, 2, _it(f"{r['avg_vel_fps']:.1f}" if r["avg_vel_fps"] else "—")
            )
            self._matrix_table.setItem(
                i, 3, _it(f"{r['avg_es_fps']:.1f}" if r["avg_es_fps"] else "—")
            )
            grp_item = _it(f"{r['avg_group_mm']:.2f}" if r["avg_group_mm"] else "—")
            if r["avg_group_mm"]:
                color = (
                    _GREEN
                    if r["avg_group_mm"] < 25
                    else _ORANGE if r["avg_group_mm"] < 50 else _RED
                )
                grp_item.setForeground(QColor(color))
            self._matrix_table.setItem(i, 4, grp_item)
            rel_item = _it(
                f"{r['reliability_pct']:.1f}" if r["reliability_pct"] else "—"
            )
            if r["reliability_pct"] and r["reliability_pct"] >= 99:
                rel_item.setForeground(QColor(_GREEN))
            self._matrix_table.setItem(i, 5, rel_item)
            labels.append(r["rifle_name"][:14])
            groups.append(r["avg_group_mm"] or 0)

        if HAS_PG and hasattr(self, "_matrix_plot") and labels:
            self._matrix_plot.clear()
            x = list(range(len(labels)))
            bar = pg.BarGraphItem(x=x, height=groups, width=0.6, brush=_ACCENT)
            self._matrix_plot.addItem(bar)
            ax = self._matrix_plot.getAxis("bottom")
            ax.setTicks([list(zip(x, labels))])


# ==========================================================================
# Tab 5 — Report export
# ==========================================================================


class ReportPanel(QWidget):
    def __init__(self, db: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = db
        self._build_ui()

    def refresh(self) -> None:
        self._reload_lots()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(_label("Export Report", bold=True))
        root.addWidget(_label("Select lots to include in the report:", color=_MUTED))

        self._lot_list = QTableWidget()
        self._lot_list.setColumnCount(4)
        self._lot_list.setHorizontalHeaderLabels(
            ["✓", "Brand / model", "Caliber", "Lot #"]
        )
        self._lot_list.setStyleSheet(_TABLE_CSS)
        self._lot_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        self._lot_list.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        self._lot_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._lot_list.setMaximumHeight(220)
        root.addWidget(self._lot_list)

        btn_row = QHBoxLayout()
        prev_btn = QPushButton("Forhåndsvis")
        prev_btn.setStyleSheet(_BTN_NEUTRAL)
        prev_btn.clicked.connect(self._preview_report)
        csv_btn = QPushButton("Export CSV")
        csv_btn.setStyleSheet(_BTN_NEUTRAL)
        csv_btn.clicked.connect(self._export_csv)
        pdf_btn = QPushButton("Export PDF")
        pdf_btn.setStyleSheet(_BTN_PRIMARY)
        pdf_btn.clicked.connect(self._export_pdf)
        btn_row.addWidget(prev_btn)
        btn_row.addWidget(csv_btn)
        btn_row.addWidget(pdf_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setStyleSheet(
            f"background:{_PANEL}; color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px; font-family: monospace;"
        )
        root.addWidget(self._preview)

        self._reload_lots()

    def _reload_lots(self) -> None:
        self._lots = services.list_lots(self._db)
        self._lot_list.setRowCount(len(self._lots))
        for i, lot in enumerate(self._lots):
            cb = QCheckBox()
            cb.setChecked(True)
            cb.setStyleSheet("margin-left:10px;")
            self._lot_list.setCellWidget(i, 0, cb)
            self._lot_list.setItem(i, 1, QTableWidgetItem(f"{lot.brand} {lot.model}"))
            self._lot_list.setItem(i, 2, QTableWidgetItem(lot.caliber))
            self._lot_list.setItem(i, 3, QTableWidgetItem(lot.lot_number))

    def _selected_lot_ids(self) -> list[int]:
        ids = []
        for i, lot in enumerate(self._lots):
            cb = self._lot_list.cellWidget(i, 0)
            if cb and isinstance(cb, QCheckBox) and cb.isChecked() and lot.id:
                ids.append(lot.id)
        return ids

    def _preview_report(self) -> None:
        ids = self._selected_lot_ids()
        if not ids:
            QMessageBox.information(self, "None selected", "Select at least one lot.")
            return
        data = services.build_report_data(self._db, ids)
        self._preview.setHtml(self._build_report_html(data))

    def _export_csv(self) -> None:
        ids = self._selected_lot_ids()
        if not ids:
            QMessageBox.information(self, "None selected", "Select at least one lot.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "ammo_test_rapport.csv", "CSV (*.csv)"
        )
        if not path:
            return
        data = services.build_report_data(self._db, ids)
        lines = ["Lot #,Brand,Model,Caliber,Avg fps,ES fps,Avg group mm,Reliability %"]
        for rd in data["rows"]:
            lot = rd["lot"]
            lines.append(
                ",".join(
                    str(v or "")
                    for v in [
                        lot.lot_number,
                        lot.brand,
                        lot.model,
                        lot.caliber,
                        rd["avg_vel"],
                        rd["avg_es"],
                        rd["avg_group"],
                        rd["reliability"],
                    ]
                )
            )
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        self._preview.setPlainText("\n".join(lines))
        QMessageBox.information(self, "Exported", f"CSV lagret til {path}")

    def _export_pdf(self) -> None:
        ids = self._selected_lot_ids()
        if not ids:
            QMessageBox.information(self, "None selected", "Select at least one lot.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "ammo_test_rapport.pdf", "PDF (*.pdf)"
        )
        if not path:
            return
        data = services.build_report_data(self._db, ids)
        html = self._build_report_html(data)
        try:
            from PyQt6.QtGui import QTextDocument
            from PyQt6.QtPrintSupport import QPrinter

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print(printer)
            self._preview.setHtml(html)
            QMessageBox.information(self, "Exported", f"PDF lagret til {path}")
        except Exception as exc:
            QMessageBox.warning(
                self, "PDF feilet", f"Kunne ikke lage PDF: {exc}\n\nPrøv CSV-eksport."
            )

    def _build_report_html(self, data: dict) -> str:
        from datetime import date as _date

        rows_html = ""
        for rd in data["rows"]:
            lot = rd["lot"]
            avg_v = f"{rd['avg_vel']:.1f}" if rd["avg_vel"] else "—"
            avg_es = f"{rd['avg_es']:.1f}" if rd["avg_es"] else "—"
            avg_g = f"{rd['avg_group']:.2f}" if rd["avg_group"] else "—"
            rel = f"{rd['reliability']:.1f} %" if rd["reliability"] is not None else "—"
            rows_html += (
                f"<tr><td>{lot.brand} {lot.model}</td><td>{lot.caliber}</td>"
                f"<td>{lot.lot_number}</td><td>{avg_v}</td><td>{avg_es}</td>"
                f"<td>{avg_g}</td><td>{rel}</td></tr>"
            )
            for s in rd["sessions"]:
                rows_html += (
                    f"<tr style='background:#f5f5f5'><td colspan='2' style='padding-left:20px'>"
                    f"{s.test_date} — {s.rifle_name or '—'} @ {s.distance_m or '?'} m</td>"
                    f"<td></td>"
                    f"<td>{s.avg_vel_fps or '—'}</td><td>{s.es_fps or '—'}</td>"
                    f"<td>{s.group_size_mm or '—'}</td>"
                    f"<td>{s.shot_count} skudd</td></tr>"
                )
        return f"""
<html><head><style>
body {{ font-family: Arial, sans-serif; font-size: 10pt; }}
h1 {{ font-size: 16pt; color: #1a3050; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
th {{ background: #1a3050; color: white; padding: 6px 10px; text-align: left; }}
td {{ border-bottom: 1px solid #ddd; padding: 5px 10px; }}
</style></head><body>
<h1>Ammo Test Rapport</h1>
<p>Generert: {_date.today().isoformat()} &nbsp;|&nbsp; {data['lot_count']} lot(s)</p>
<table>
<tr><th>Merke / modell</th><th>Kaliber</th><th>Lot #</th>
<th>Snitt fps</th><th>ES fps</th><th>Snitt gruppe mm</th><th>Pålitelighet</th></tr>
{rows_html}
</table>
</body></html>"""


# ==========================================================================
# Main window
# ==========================================================================


class AmmoTestWindow(QWidget):
    def __init__(
        self, db: Any, rifles: list[dict] | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._db = db
        self._rifles = rifles or []
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(f"background: {_BG}; color: {_TEXT};")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Header
        header = QHBoxLayout()
        title = QLabel("Ammo Test")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {_TEXT};")
        sub = QLabel(
            "Registrer og sammenlign fabrikkammunisjon per lot, sesjon og våpen"
        )
        sub.setStyleSheet(f"color: {_MUTED}; font-size: 10pt;")
        header.addWidget(title)
        header.addSpacing(16)
        header.addWidget(sub)
        header.addStretch()
        root.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_BORDER};")
        root.addWidget(sep)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{ border: 1px solid {_BORDER}; border-radius: 6px; }}
            QTabBar::tab {{
                background: {_PANEL}; color: {_MUTED};
                padding: 8px 20px; border-radius: 4px 4px 0 0;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{ background: {_ACCENT}; color: white; }}
            QTabBar::tab:hover {{ background: #2c3a4f; color: {_TEXT}; }}
        """
        )

        self._lot_panel = LotPanel(self._db)
        self._session_panel = SessionPanel(self._db, self._rifles)
        self._comparison_panel = ComparisonPanel(self._db)
        self._matrix_panel = WeaponMatrixPanel(self._db)
        self._report_panel = ReportPanel(self._db)

        self._tabs.addTab(self._lot_panel, "📦  Ammo-lot")
        self._tabs.addTab(self._session_panel, "🎯  Test-sesjon")
        self._tabs.addTab(self._comparison_panel, "📊  LOT-sammenligning")
        self._tabs.addTab(self._matrix_panel, "🔫  Våpenmatrise")
        self._tabs.addTab(self._report_panel, "📄  Rapporter")

        # Wire lot selection → session panel
        self._lot_panel.lot_selected.connect(self._session_panel.set_lot)

        # Refresh data-dependent tabs when switching to them
        self._tabs.currentChanged.connect(self._on_tab_changed)

        root.addWidget(self._tabs)

    def _on_tab_changed(self, idx: int) -> None:
        if idx == 2:
            self._comparison_panel.refresh()
        elif idx == 3:
            self._matrix_panel.refresh()
        elif idx == 4:
            self._report_panel.refresh()
