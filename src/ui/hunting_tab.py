"""Hunting tab — hunting post, game selection, backstop safety analysis.

Shows:
- Game type selector + ethical range display
- Aim point list with backstop verdict badges (green/orange/red)
- Distance and bearing to each point
- Nearest habitation warning if set

Usage::

    tab = HuntingTab(parent)
    tab.set_session(session)   # FieldSession with profile + atmosphere
    tab.set_post(post)         # HuntingPost
"""

from __future__ import annotations

from ..field_planning.backstop_analyzer import analyse_backstop, compute_ethical_range
from ..field_planning.models import (
    GAME_MIN_ENERGY_J,
    BackstopAnalysis,
    FieldSession,
    GeoPoint,
    HuntingPost,
)
from ..qt_compat import (
    QComboBox,
    QFont,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_GAME_TYPES = [
    ("Moose", "moose"),
    ("Deer", "deer"),
    ("Reindeer", "reindeer"),
    ("Rådyr", "roe_deer"),
    ("Boar", "boar"),
    ("Småvilt", "small_game"),
]

_VERDICT_COLORS = {
    "safe": ("#0a3a0a", "#60d060"),
    "caution": ("#3a2a00", "#d0a030"),
    "unsafe": ("#3a0a0a", "#d04040"),
    "unknown": ("#2a2a2a", "#888888"),
}


class HuntingTab(QWidget):
    """Hunting post + backstop safety analysis tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session: FieldSession | None = None
        self._post: HuntingPost | None = None
        self._analyses: list[BackstopAnalysis] = []
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_session(self, session: FieldSession) -> None:
        self._session = session
        self._refresh_ethical_range()

    def add_aim_point(self, label: str, slant_m: float, bearing_deg: float) -> None:
        """Add an aim point programmatically (e.g. from map click)."""
        n = self._aim_table.rowCount()
        self._aim_table.insertRow(n)
        self._aim_table.setItem(n, 0, QTableWidgetItem(label))
        self._aim_table.setItem(n, 1, QTableWidgetItem(f"{slant_m:.0f}"))
        self._aim_table.setItem(n, 2, QTableWidgetItem(f"{bearing_deg:.1f}"))
        self._aim_table.setItem(n, 3, QTableWidgetItem(""))

    def set_post(self, post: HuntingPost) -> None:
        self._post = post
        game_key = post.game_type
        for i, (_, key) in enumerate(_GAME_TYPES):
            if key == game_key:
                self._game_combo.setCurrentIndex(i)
                break
        self._refresh_ethical_range()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(4, 4, 4, 4)

        # Toolbar
        tb = QHBoxLayout()
        title = QLabel("Hunting — safety assessment")
        f = QFont()
        f.setBold(True)
        f.setPointSize(11)
        title.setFont(f)
        tb.addWidget(title)
        tb.addStretch()
        root.addLayout(tb)

        # Game type + ethical range row
        game_row = QHBoxLayout()
        game_row.addWidget(QLabel("Game type:"))
        self._game_combo = QComboBox()
        for label, _ in _GAME_TYPES:
            self._game_combo.addItem(label)
        self._game_combo.currentIndexChanged.connect(self._on_game_changed)
        game_row.addWidget(self._game_combo)

        game_row.addWidget(QLabel("Min. energy:"))
        self._energy_label = QLabel("2500 J")
        self._energy_label.setStyleSheet("color: #80d080; font-weight: bold;")
        game_row.addWidget(self._energy_label)

        game_row.addWidget(QLabel("Ethical range:"))
        self._ethical_range_label = QLabel("—")
        self._ethical_range_label.setStyleSheet(
            "color: #80a0ff; font-weight: bold; font-size: 11pt;"
        )
        game_row.addWidget(self._ethical_range_label)
        game_row.addStretch()

        recalc_btn = QPushButton("Calculate Backstop")
        recalc_btn.setStyleSheet(
            "background: #27ae60; color: white; font-weight: bold;"
        )
        recalc_btn.clicked.connect(self._recompute_all)
        game_row.addWidget(recalc_btn)
        root.addLayout(game_row)

        # Summary bar
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #b0b6be; font-size: 10pt;")
        root.addWidget(self._summary_label)

        # Splitter: aim point editor (left) + safety verdict table (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: aim point input
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)

        aim_hdr = QHBoxLayout()
        aim_hdr.addWidget(QLabel("Aim points:"))
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self._add_aim_point)
        aim_hdr.addWidget(add_btn)
        rem_btn = QPushButton("– Fjern")
        rem_btn.clicked.connect(self._remove_aim_point)
        aim_hdr.addWidget(rem_btn)
        aim_hdr.addStretch()
        lv.addLayout(aim_hdr)

        self._aim_table = QTableWidget()
        self._aim_table.setColumnCount(4)
        self._aim_table.setHorizontalHeaderLabels(
            ["Navn", "Slant\nm", "Retning\n°", "Nærmeste\nbebygg. m"]
        )
        hh = self._aim_table.horizontalHeader()
        if hh:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._aim_table.setAlternatingRowColors(True)
        self._aim_table.setStyleSheet("font-size: 10pt;")
        lv.addWidget(self._aim_table)

        # Quick-add presets
        preset_row = QHBoxLayout()
        for dist in [50, 100, 150, 200, 250, 300]:
            btn = QPushButton(f"{dist}m")
            btn.setFixedWidth(46)
            btn.setStyleSheet("padding: 2px 4px; font-size: 9pt;")
            btn.clicked.connect(lambda checked, d=dist: self._add_preset(d))
            preset_row.addWidget(btn)
        preset_row.addStretch()
        lv.addLayout(preset_row)

        splitter.addWidget(left)

        # Right: safety verdict table
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.addWidget(QLabel("Backstop analysis:"))

        self._verdict_table = QTableWidget()
        self._verdict_table.setColumnCount(6)
        self._verdict_table.setHorizontalHeaderLabels(
            ["Navn", "Slant m", "Terrengtreffer", "Energi J", "Bebygg. m", "Kjennelse"]
        )
        vh = self._verdict_table.horizontalHeader()
        if vh:
            vh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            vh.setStretchLastSection(True)
        self._verdict_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._verdict_table.setAlternatingRowColors(True)
        self._verdict_table.setStyleSheet("font-size: 10pt;")
        rv.addWidget(self._verdict_table)

        self._verdict_status = QLabel("")
        self._verdict_status.setStyleSheet("font-size: 9.5pt; color: #888;")
        rv.addWidget(self._verdict_status)

        splitter.addWidget(right)
        splitter.setSizes([260, 480])
        root.addWidget(splitter)

    # ------------------------------------------------------------------
    # Internal data
    # ------------------------------------------------------------------

    def _current_game_key(self) -> str:
        idx = self._game_combo.currentIndex()
        if 0 <= idx < len(_GAME_TYPES):
            return _GAME_TYPES[idx][1]
        return "deer"

    def _current_min_energy(self) -> float:
        return GAME_MIN_ENERGY_J.get(self._current_game_key(), 1500.0)

    def _on_game_changed(self) -> None:
        min_j = self._current_min_energy()
        self._energy_label.setText(f"{min_j:.0f} J")
        self._refresh_ethical_range()

    def _refresh_ethical_range(self) -> None:
        if self._session is None or self._session.atmosphere is None:
            self._ethical_range_label.setText("—")
            return
        try:
            r = compute_ethical_range(
                profile=self._session.profile,
                atmosphere=self._session.atmosphere,
                min_energy_j=self._current_min_energy(),
                bearing_deg=self._session.azimuth_deg,
                latitude_deg=self._session.latitude_deg,
            )
            self._ethical_range_label.setText(f"{r:.0f} m")
        except Exception:
            self._ethical_range_label.setText("error")

    # ------------------------------------------------------------------
    # Aim points
    # ------------------------------------------------------------------

    def _get_aim_rows(self) -> list[tuple[str, float, float, float | None]]:
        rows = []
        for i in range(self._aim_table.rowCount()):
            try:
                label = (
                    self._aim_table.item(i, 0) or QTableWidgetItem("")
                ).text() or f"P{i+1}"
                slant = float(
                    (self._aim_table.item(i, 1) or QTableWidgetItem("100")).text()
                )
                bearing = float(
                    (self._aim_table.item(i, 2) or QTableWidgetItem("0")).text()
                )
                hab_text = (
                    (self._aim_table.item(i, 3) or QTableWidgetItem("")).text().strip()
                )
                hab = float(hab_text) if hab_text else None
                rows.append((label, slant, bearing, hab))
            except (ValueError, AttributeError):
                pass
        return rows

    def _add_aim_point(self) -> None:
        n = self._aim_table.rowCount()
        self._aim_table.insertRow(n)
        self._aim_table.setItem(n, 0, QTableWidgetItem(f"Point {n+1}"))
        self._aim_table.setItem(n, 1, QTableWidgetItem("100"))
        self._aim_table.setItem(n, 2, QTableWidgetItem("0"))
        self._aim_table.setItem(n, 3, QTableWidgetItem(""))

    def _add_preset(self, distance_m: int) -> None:
        n = self._aim_table.rowCount()
        self._aim_table.insertRow(n)
        self._aim_table.setItem(n, 0, QTableWidgetItem(f"{distance_m}m"))
        self._aim_table.setItem(n, 1, QTableWidgetItem(str(distance_m)))
        self._aim_table.setItem(n, 2, QTableWidgetItem("0"))
        self._aim_table.setItem(n, 3, QTableWidgetItem(""))

    def _remove_aim_point(self) -> None:
        rows = sorted(
            {idx.row() for idx in self._aim_table.selectedIndexes()}, reverse=True
        )
        for row in rows:
            self._aim_table.removeRow(row)

    # ------------------------------------------------------------------
    # Backstop computation
    # ------------------------------------------------------------------

    def _recompute_all(self) -> None:
        if self._session is None or self._session.atmosphere is None:
            self._verdict_status.setText("Ingen sesjon konfigurert.")
            return

        aim_rows = self._get_aim_rows()
        if not aim_rows:
            self._verdict_status.setText("Add aim points first.")
            return

        profile = self._session.profile
        atm = self._session.atmosphere
        self._analyses = []

        for label, slant, bearing, hab in aim_rows:
            # Flat terrain proxy: shooter at 100m ASL, extends 5km
            terrain = [(0.0, 100.0), (slant * 3, 100.0)]
            try:
                analysis = analyse_backstop(
                    profile=profile,
                    atmosphere=atm,
                    aim_point=GeoPoint(lat=60.0, lon=10.0),
                    bearing_deg=bearing,
                    slant_range_m=slant,
                    terrain_points=terrain,
                    nearest_habitation_m=hab,
                    latitude_deg=self._session.latitude_deg,
                )
            except Exception:
                analysis = None
            self._analyses.append((label, slant, bearing, hab, analysis))

        self._render_verdicts()

    def _render_verdicts(self) -> None:
        rows = self._analyses
        self._verdict_table.setRowCount(len(rows))
        safe_n = caution_n = unsafe_n = 0

        for i, row_data in enumerate(rows):
            label, slant, bearing, hab, analysis = row_data
            if analysis is None:
                verdict, bg, fg = "error", "#2a2a2a", "#888888"
                ground_str, energy_str, hab_str, reason = (
                    "—",
                    "—",
                    "—",
                    "Calculation error",
                )
            else:
                verdict = analysis.verdict
                bg, fg = _VERDICT_COLORS.get(verdict, _VERDICT_COLORS["unknown"])
                ground_str = (
                    f"{analysis.ground_intersection_m:.0f}m"
                    if analysis.ground_intersection_m
                    else "> scan"
                )
                energy_str = f"{analysis.bullet_energy_at_ground_j:.0f}"
                hab_str = (
                    f"{analysis.nearest_habitation_m:.0f}m"
                    if analysis.nearest_habitation_m
                    else "—"
                )
                if verdict == "safe":
                    safe_n += 1
                elif verdict == "caution":
                    caution_n += 1
                else:
                    unsafe_n += 1

                reason = analysis.verdict_reason

            def _c(text: str, right: bool = True) -> QTableWidgetItem:
                it = QTableWidgetItem(text)
                it.setTextAlignment(
                    (
                        Qt.AlignmentFlag.AlignRight
                        if right
                        else Qt.AlignmentFlag.AlignCenter
                    )
                    | Qt.AlignmentFlag.AlignVCenter
                )
                return it

            verdict_label = {
                "safe": "TRYGT",
                "caution": "FORSIKTIG",
                "unsafe": "UTRYGT",
            }.get(verdict, verdict.upper())
            cells = [
                _c(label, right=False),
                _c(f"{slant:.0f}"),
                _c(ground_str),
                _c(energy_str),
                _c(hab_str),
                _c(verdict_label, right=False),
            ]

            for col, cell in enumerate(cells):
                if col == 5:
                    try:
                        from ..qt_compat import QtGui

                        cell.setBackground(QtGui.QColor(bg))
                        cell.setForeground(QtGui.QColor(fg))
                    except Exception:
                        pass
                cell.setToolTip(reason if analysis else "Feil")
                self._verdict_table.setItem(i, col, cell)

        self._verdict_status.setText(
            f"✅ {safe_n} trygge  ⚠️ {caution_n} forsiktig  ❌ {unsafe_n} utrygt"
        )
        self._summary_label.setText(
            f"Min. energi {self._current_min_energy():.0f}J ({_GAME_TYPES[self._game_combo.currentIndex()][0]})  "
            f"— etisk rekkevidde vises over"
        )
