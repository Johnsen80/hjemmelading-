"""ChronographWidget — register and review chronograph sessions for a rifle.

Shows existing sessions in a table and allows adding new sessions by typing
individual velocities (fps). Computes avg/SD/ES automatically.

Usage::

    w = ChronographWidget(db=database, parent=main_window)
    w.set_rifle(rifle_id)
    w.show()
"""

from __future__ import annotations

import json
import math
from datetime import date
from typing import Any

from ..qt_compat import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFont,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    Signal,
)


def _stats(velocities: list[float]) -> tuple[float, float, float, float, float]:
    """Return (avg, sd, es, min, max) for a list of velocities."""
    n = len(velocities)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    avg = sum(velocities) / n
    sd = math.sqrt(sum((v - avg) ** 2 for v in velocities) / (n - 1)) if n > 1 else 0.0
    return avg, sd, max(velocities) - min(velocities), min(velocities), max(velocities)


class ChronographWidget(QDialog):
    """Dialog for registering and reviewing chronograph sessions."""

    session_saved = Signal(int)  # emits session_id after save

    def __init__(self, db: Any = None, parent=None):
        super().__init__(parent)
        self._db = db
        self._rifle_id: int | None = None
        self._sessions: list[dict] = []

        self.setWindowTitle("Kronograf — sesjoner")
        self.resize(960, 640)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint,
        )
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_rifle(self, rifle_id: int) -> None:
        self._rifle_id = rifle_id
        self._load_sessions()
        self._populate_ammo_combo()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(8, 8, 8, 8)

        # Title
        title = QLabel("KRONOGRAF — registrer og analyser hastigheter")
        f = QFont()
        f.setBold(True)
        f.setPointSize(12)
        title.setFont(f)
        root.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: session list ──────────────────────────────────────
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 4, 0)

        lv.addWidget(QLabel("Lagrede sesjoner:"))
        self._session_table = QTableWidget()
        self._session_table.setColumnCount(7)
        self._session_table.setHorizontalHeaderLabels(
            ["Dato", "Ammo", "Enhet", "n", "Avg fps", "SD fps", "ES fps"]
        )
        hh = self._session_table.horizontalHeader()
        if hh:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            hh.setStretchLastSection(True)
        self._session_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._session_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._session_table.setAlternatingRowColors(True)
        self._session_table.setStyleSheet("font-size: 10pt;")
        self._session_table.itemSelectionChanged.connect(self._on_session_selected)
        lv.addWidget(self._session_table)

        del_btn = QPushButton("🗑 Slett valgt sesjon")
        del_btn.clicked.connect(self._delete_session)
        lv.addWidget(del_btn)

        splitter.addWidget(left)

        # ── Right: new session entry ────────────────────────────────
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 0, 0, 0)
        rv.setSpacing(8)

        hdr2 = QLabel("Ny sesjon")
        f2 = QFont()
        f2.setBold(True)
        hdr2.setFont(f2)
        rv.addWidget(hdr2)

        # Meta row
        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel("Dato:"))
        self._date_edit = QLineEdit(date.today().isoformat())
        self._date_edit.setFixedWidth(100)
        meta_row.addWidget(self._date_edit)

        meta_row.addWidget(QLabel("Ammo:"))
        self._ammo_combo = QComboBox()
        self._ammo_combo.setMinimumWidth(160)
        meta_row.addWidget(self._ammo_combo)

        meta_row.addWidget(QLabel("Enhet:"))
        self._device_combo = QComboBox()
        self._device_combo.addItems(
            ["Magnetospeed", "Labradar", "ProChrono", "Caldwell", "Annen"]
        )
        self._device_combo.setFixedWidth(120)
        meta_row.addWidget(self._device_combo)

        meta_row.addWidget(QLabel("Temp °F:"))
        self._temp_spin = QDoubleSpinBox()
        self._temp_spin.setRange(-40, 140)
        self._temp_spin.setValue(59.0)
        self._temp_spin.setFixedWidth(65)
        meta_row.addWidget(self._temp_spin)
        meta_row.addStretch()
        rv.addLayout(meta_row)

        # Notes
        notes_row = QHBoxLayout()
        notes_row.addWidget(QLabel("Notater:"))
        self._notes_edit = QLineEdit()
        self._notes_edit.setPlaceholderText("Ladning, lot, vær, posisjon…")
        notes_row.addWidget(self._notes_edit)
        rv.addLayout(notes_row)

        # Velocity entry table
        rv.addWidget(QLabel("Hastigheter (fps) — en per linje:"))
        self._vel_table = QTableWidget()
        self._vel_table.setColumnCount(2)
        self._vel_table.setHorizontalHeaderLabels(["Skudd #", "Fps"])
        self._vel_table.setRowCount(10)
        vh = self._vel_table.horizontalHeader()
        if vh:
            vh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            vh.setStretchLastSection(True)
        for i in range(10):
            self._vel_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
        self._vel_table.itemChanged.connect(self._on_vel_changed)
        rv.addWidget(self._vel_table)

        add_row_btn = QPushButton("+ Legg til rad")
        add_row_btn.setFixedWidth(120)
        add_row_btn.clicked.connect(self._add_vel_row)
        rv.addWidget(add_row_btn)

        # Live stats
        self._stats_label = QLabel("Statistikk: — ")
        self._stats_label.setStyleSheet(
            "background: #1a2a1a; color: #80e080; padding: 4px 8px; "
            "border-radius: 4px; font-size: 10.5pt; font-family: monospace;"
        )
        rv.addWidget(self._stats_label)

        # Save
        save_btn = QPushButton("💾 Lagre sesjon")
        save_btn.setStyleSheet(
            "background: #27ae60; color: white; font-weight: bold; padding: 6px;"
        )
        save_btn.clicked.connect(self._save_session)
        rv.addWidget(save_btn)

        self._save_status = QLabel("")
        self._save_status.setStyleSheet("color: #80c080; font-size: 9.5pt;")
        rv.addWidget(self._save_status)
        rv.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([480, 420])
        root.addWidget(splitter)

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _load_sessions(self) -> None:
        if self._db is None or self._rifle_id is None:
            return
        try:
            rows = (
                self._db.execute_query(
                    """
                SELECT cs.id, cs.session_date, cs.device_type,
                       cs.shot_count, cs.avg_velocity_fps, cs.sd_fps, cs.es_fps,
                       ap.name as ammo_name, cs.notes, cs.raw_data_json
                FROM chronograph_sessions cs
                LEFT JOIN ammo_profiles ap ON cs.ammo_profile_id = ap.id
                WHERE ap.rifle_id = ? OR cs.ammo_profile_id IS NULL
                ORDER BY cs.session_date DESC
                """,
                    (self._rifle_id,),
                )
                or []
            )
            self._sessions = [
                {
                    "id": r[0],
                    "date": r[1],
                    "device": r[2],
                    "n": r[3],
                    "avg": r[4],
                    "sd": r[5],
                    "es": r[6],
                    "ammo": r[7] or "—",
                    "notes": r[8],
                    "raw": r[9],
                }
                for r in rows
            ]
        except Exception:
            self._sessions = []
        self._render_session_table()

    def _populate_ammo_combo(self) -> None:
        self._ammo_combo.clear()
        self._ammo_combo.addItem("— ingen ammo valgt —", userData=None)
        if self._db is None or self._rifle_id is None:
            return
        try:
            rows = (
                self._db.execute_query(
                    "SELECT id, name FROM ammo_profiles WHERE rifle_id=? ORDER BY name",
                    (self._rifle_id,),
                )
                or []
            )
            for row in rows:
                self._ammo_combo.addItem(row[1], userData=row[0])
        except Exception:
            pass

    def _render_session_table(self) -> None:
        self._session_table.setRowCount(len(self._sessions))
        for i, s in enumerate(self._sessions):

            def _c(text: str) -> QTableWidgetItem:
                it = QTableWidgetItem(text)
                it.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                return it

            self._session_table.setItem(i, 0, _c(s["date"] or "—"))
            self._session_table.setItem(i, 1, _c(s["ammo"]))
            self._session_table.setItem(i, 2, _c(s["device"] or "—"))
            self._session_table.setItem(i, 3, _c(str(s["n"] or "—")))
            self._session_table.setItem(
                i, 4, _c(f"{s['avg']:.0f}" if s["avg"] else "—")
            )
            self._session_table.setItem(i, 5, _c(f"{s['sd']:.1f}" if s["sd"] else "—"))
            self._session_table.setItem(i, 6, _c(f"{s['es']:.0f}" if s["es"] else "—"))

    # ------------------------------------------------------------------
    # Velocity entry
    # ------------------------------------------------------------------

    def _add_vel_row(self) -> None:
        n = self._vel_table.rowCount()
        self._vel_table.insertRow(n)
        self._vel_table.setItem(n, 0, QTableWidgetItem(str(n + 1)))

    def _get_velocities(self) -> list[float]:
        vals = []
        for i in range(self._vel_table.rowCount()):
            item = self._vel_table.item(i, 1)
            if item and item.text().strip():
                try:
                    vals.append(float(item.text().strip()))
                except ValueError:
                    pass
        return vals

    def _on_vel_changed(self) -> None:
        vels = self._get_velocities()
        if not vels:
            self._stats_label.setText("Statistikk: —")
            return
        avg, sd, es, vmin, vmax = _stats(vels)
        self._stats_label.setText(
            f"n={len(vels)}  Avg: {avg:.0f} fps  SD: {sd:.1f} fps  "
            f"ES: {es:.0f} fps  [{vmin:.0f}–{vmax:.0f}]"
        )

    # ------------------------------------------------------------------
    # Save / delete
    # ------------------------------------------------------------------

    def _save_session(self) -> None:
        if self._db is None:
            self._save_status.setText("Ingen database koblet.")
            return
        vels = self._get_velocities()
        if not vels:
            self._save_status.setText("Ingen hastigheter registrert.")
            return

        avg, sd, es, vmin, vmax = _stats(vels)
        ammo_id = self._ammo_combo.currentData()
        raw = json.dumps({"velocities_fps": vels})

        try:
            self._db.execute_query(
                """
                INSERT INTO chronograph_sessions
                  (ammo_profile_id, device_type, session_name, session_date,
                   avg_velocity_fps, es_fps, sd_fps,
                   min_velocity_fps, max_velocity_fps, shot_count,
                   temperature_f, notes, raw_data_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    ammo_id,
                    self._device_combo.currentText(),
                    self._notes_edit.text() or None,
                    self._date_edit.text(),
                    avg,
                    es,
                    sd,
                    vmin,
                    vmax,
                    len(vels),
                    self._temp_spin.value(),
                    self._notes_edit.text() or None,
                    raw,
                ),
            )
            self._save_status.setText(
                f"✔ Lagret {len(vels)} skudd — Avg {avg:.0f} fps  SD {sd:.1f}"
            )
            self._load_sessions()
            # Clear velocity table
            for i in range(self._vel_table.rowCount()):
                item = self._vel_table.item(i, 1)
                if item:
                    item.setText("")
        except Exception as exc:
            self._save_status.setText(f"Feil: {exc}")

    def _delete_session(self) -> None:
        rows = list({idx.row() for idx in self._session_table.selectedIndexes()})
        if not rows or self._db is None:
            return
        for r in sorted(rows, reverse=True):
            if 0 <= r < len(self._sessions):
                sid = self._sessions[r]["id"]
                try:
                    self._db.execute_query(
                        "DELETE FROM chronograph_sessions WHERE id=?", (sid,)
                    )
                except Exception:
                    pass
        self._load_sessions()

    def _on_session_selected(self) -> None:
        rows = list({idx.row() for idx in self._session_table.selectedIndexes()})
        if not rows or rows[0] >= len(self._sessions):
            return
        s = self._sessions[rows[0]]
        detail = (
            f"Sesjon {s['date']}  |  {s['ammo']}  |  {s['device']}\n"
            f"n={s['n']}  Avg={s['avg']:.0f} fps  SD={s['sd']:.1f}  ES={s['es']:.0f}\n"
        )
        try:
            raw = json.loads(s["raw"] or "{}")
            vels = raw.get("velocities_fps", [])
            if vels:
                detail += "  ".join(f"{v:.0f}" for v in vels)
        except Exception:
            pass
        self._save_status.setText(detail)
