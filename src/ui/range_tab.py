"""Range tab — shooting range with multiple targets and per-target click tables.

Left pane:  Target list (editable slant range, inclination, bearing).
Right pane: Computed click corrections for each target.

Usage::

    tab = RangeTab(parent)
    tab.set_session(range_session)   # RangeSession with profile + atmosphere
"""

from __future__ import annotations

from ..field_planning.models import RangeSession, RangeTarget, WeaponBallisticProfile
from ..field_planning.range_calculator import build_range_click_table
from ..qt_compat import (
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

_SOLUTION_COLS = [
    ("Target", "label"),
    ("Slant\nm", "slant"),
    ("Horiz.\nm", "horiz"),
    ("Incline\n°", "incl"),
    ("Clicks ↑", "elev_clicks"),
    ("MOA ↑", "elev_moa"),
    ("Wind\n10m/s", "wind_10"),
    ("Vel\nm/s", "velocity"),
    ("Energy\nJ", "energy"),
    ("TOF\ns", "tof"),
    ("Phase", "phase"),
    ("Sg", "sg"),
]

_PHASE_COLORS = {
    "supersonic": ("#1a4a1a", "#80d080"),
    "transonic": ("#4a3a00", "#d0b040"),
    "subsonic": ("#4a1a1a", "#d06060"),
}


class RangeTab(QWidget):
    """Shooting range tab: add targets, compute click table."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session: RangeSession | None = None
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_session(self, session: RangeSession) -> None:
        self._session = session
        self._rebuild_target_rows()
        self._compute()

    def get_session(self) -> RangeSession | None:
        return self._session

    def add_map_target(self, label: str, slant_m: float, bearing_deg: float) -> None:
        """Add a target from a map click, creating a stub session if needed."""
        if self._session is None:
            self._add_target()
            if self._session is None:
                return
            self._session.targets.clear()
        self._session.targets.append(
            RangeTarget(
                label=label, slant_range_m=slant_m, bearing_deg=bearing_deg % 360
            )
        )
        self._rebuild_target_rows()
        self._compute()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(4, 4, 4, 4)

        # Toolbar
        tb = QHBoxLayout()
        title = QLabel("Range — targets and click table")
        f = QFont()
        f.setBold(True)
        f.setPointSize(11)
        title.setFont(f)
        tb.addWidget(title)
        tb.addStretch()

        self._add_btn = QPushButton("+ Add Target")
        self._add_btn.clicked.connect(self._add_target)
        tb.addWidget(self._add_btn)

        self._remove_btn = QPushButton("– Remove Selected")
        self._remove_btn.clicked.connect(self._remove_target)
        tb.addWidget(self._remove_btn)

        self._compute_btn = QPushButton("Calculate Clicks")
        self._compute_btn.setStyleSheet(
            "background: #27ae60; color: white; font-weight: bold;"
        )
        self._compute_btn.clicked.connect(self._compute)
        tb.addWidget(self._compute_btn)
        root.addLayout(tb)

        # Splitter: target editor (left) + click table (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: target editor
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.addWidget(QLabel("Target list (click to edit):"))

        self._target_table = QTableWidget()
        self._target_table.setColumnCount(4)
        self._target_table.setHorizontalHeaderLabels(
            ["Name", "Slant\nm", "Incline\n°", "Direction\n°"]
        )
        hh = self._target_table.horizontalHeader()
        if hh:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            hh.setStretchLastSection(False)
        self._target_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._target_table.setAlternatingRowColors(True)
        self._target_table.setStyleSheet("font-size: 10pt;")
        self._target_table.itemChanged.connect(self._on_target_changed)
        lv.addWidget(self._target_table)

        # Quick-add shortcuts
        preset_row = QHBoxLayout()
        for dist in [100, 200, 300, 500, 600, 800, 1000]:
            btn = QPushButton(f"{dist}m")
            btn.setFixedWidth(52)
            btn.setStyleSheet("padding: 2px 4px; font-size: 9pt;")
            btn.clicked.connect(lambda checked, d=dist: self._add_preset(d))
            preset_row.addWidget(btn)
        preset_row.addStretch()
        lv.addLayout(preset_row)

        splitter.addWidget(left)

        # Right: click table
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.addWidget(QLabel("Calculated corrections:"))

        self._result_table = QTableWidget()
        self._result_table.setColumnCount(len(_SOLUTION_COLS))
        self._result_table.setHorizontalHeaderLabels([c[0] for c in _SOLUTION_COLS])
        rh = self._result_table.horizontalHeader()
        if rh:
            rh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            rh.setStretchLastSection(True)
        self._result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._result_table.setAlternatingRowColors(True)
        self._result_table.setStyleSheet("font-size: 10pt;")
        rv.addWidget(self._result_table)

        self._status_label = QLabel("Ingen beregning utført.")
        self._status_label.setStyleSheet("color: #888; font-size: 9.5pt;")
        rv.addWidget(self._status_label)

        splitter.addWidget(right)
        splitter.setSizes([280, 500])
        root.addWidget(splitter)

    # ------------------------------------------------------------------
    # Target management
    # ------------------------------------------------------------------

    def _rebuild_target_rows(self) -> None:
        if self._session is None:
            return
        self._target_table.blockSignals(True)
        self._target_table.setRowCount(len(self._session.targets))
        for i, t in enumerate(self._session.targets):
            self._target_table.setItem(i, 0, QTableWidgetItem(t.label))
            self._target_table.setItem(i, 1, QTableWidgetItem(f"{t.slant_range_m:.0f}"))
            self._target_table.setItem(
                i, 2, QTableWidgetItem(f"{t.inclination_deg:.1f}")
            )
            self._target_table.setItem(i, 3, QTableWidgetItem(f"{t.bearing_deg:.0f}"))
        self._target_table.blockSignals(False)

    def _add_target(self) -> None:
        if self._session is None:
            self._session = RangeSession(
                profile=WeaponBallisticProfile(
                    rifle_id=0,
                    rifle_name="",
                    caliber="",
                    barrel_configuration_id=None,
                    twist_rate_in=10.0,
                    twist_direction="RIGHT",
                    sight_height_mm=38.0,
                    zero_distance_m=100.0,
                    learned_mv_fps=2650.0,
                    learned_mv_sd_fps=10.0,
                    learned_bc=0.223,
                    learned_bc_type="G7",
                    bc_source="",
                    mv_source="",
                ),
            )
        n = len(self._session.targets) + 1
        self._session.targets.append(RangeTarget(label=f"Mål {n}", slant_range_m=300.0))
        self._rebuild_target_rows()

    def _add_preset(self, distance_m: int) -> None:
        if self._session is None:
            self._add_target()
            if self._session is None:
                return
        self._session.targets.append(
            RangeTarget(label=f"{distance_m}m", slant_range_m=float(distance_m))
        )
        self._rebuild_target_rows()
        self._compute()

    def _remove_target(self) -> None:
        if self._session is None:
            return
        rows = {idx.row() for idx in self._target_table.selectedIndexes()}
        if not rows:
            return
        for i in sorted(rows, reverse=True):
            if 0 <= i < len(self._session.targets):
                self._session.targets.pop(i)
        self._rebuild_target_rows()
        self._compute()

    def _on_target_changed(self, item: QTableWidgetItem) -> None:
        if self._session is None:
            return
        row = item.row()
        col = item.column()
        if row >= len(self._session.targets):
            return
        t = self._session.targets[row]
        text = item.text().strip()
        try:
            if col == 0:
                self._session.targets[row] = RangeTarget(
                    label=text,
                    slant_range_m=t.slant_range_m,
                    inclination_deg=t.inclination_deg,
                    bearing_deg=t.bearing_deg,
                )
            elif col == 1:
                self._session.targets[row] = RangeTarget(
                    label=t.label,
                    slant_range_m=max(1.0, float(text)),
                    inclination_deg=t.inclination_deg,
                    bearing_deg=t.bearing_deg,
                )
            elif col == 2:
                self._session.targets[row] = RangeTarget(
                    label=t.label,
                    slant_range_m=t.slant_range_m,
                    inclination_deg=float(text),
                    bearing_deg=t.bearing_deg,
                )
            elif col == 3:
                self._session.targets[row] = RangeTarget(
                    label=t.label,
                    slant_range_m=t.slant_range_m,
                    inclination_deg=t.inclination_deg,
                    bearing_deg=float(text) % 360,
                )
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # Computation
    # ------------------------------------------------------------------

    def _compute(self) -> None:
        if self._session is None or not self._session.targets:
            self._result_table.setRowCount(0)
            self._status_label.setText("Ingen mål å beregne.")
            return

        try:
            solutions = build_range_click_table(self._session)
        except Exception as exc:
            self._status_label.setText(f"Calculation error: {exc}")
            return

        self._result_table.setRowCount(len(solutions))
        for row_idx, sol in enumerate(solutions):
            t = sol.target
            phase_bg, phase_fg = _PHASE_COLORS.get(sol.phase, ("#23272e", "#e0e6ed"))

            def _cell(text: str, right: bool = True) -> QTableWidgetItem:
                it = QTableWidgetItem(text)
                flag = (
                    Qt.AlignmentFlag.AlignRight
                    if right
                    else Qt.AlignmentFlag.AlignCenter
                )
                it.setTextAlignment(flag | Qt.AlignmentFlag.AlignVCenter)
                return it

            cells = [
                _cell(t.label, right=False),
                _cell(f"{t.slant_range_m:.0f}"),
                _cell(f"{t.horizontal_range_m:.0f}"),
                _cell(f"{t.inclination_deg:+.1f}"),
                _cell(f"{sol.correction.elevation_clicks:+.1f}"),
                _cell(f"{sol.correction.elevation_moa:+.2f}"),
                _cell(f"{sol.wind_10mps_windage_moa:+.2f}"),
                _cell(f"{sol.velocity_mps:.0f}"),
                _cell(f"{sol.energy_joules:.0f}"),
                _cell(f"{sol.time_of_flight_s:.3f}"),
                _cell(_phase_lbl(sol.phase), right=False),
                _cell(f"{sol.stability_sg:.1f}"),
            ]

            for col_idx, cell in enumerate(cells):
                if col_idx == 10:  # phase column
                    try:
                        from ..qt_compat import QtGui

                        cell.setBackground(QtGui.QColor(phase_bg))
                        cell.setForeground(QtGui.QColor(phase_fg))
                    except Exception:
                        pass
                self._result_table.setItem(row_idx, col_idx, cell)

        self._status_label.setText(
            f"{len(solutions)} mål beregnet — "
            f"MV {self._session.profile.learned_mv_fps:.0f} fps  "
            f"BC {self._session.profile.learned_bc:.4f}"
        )


def _phase_lbl(phase: str) -> str:
    return {"supersonic": "Super", "transonic": "Trans", "subsonic": "Sub"}.get(
        phase, phase
    )
