"""CDM Calibration Panel — back-calculate BC from measured bullet drops.

User enters real drop measurements at various distances from their own rifle.
The panel uses grid-search + bisection to find the G7 BC that best matches
the measured drops, then offers to save it back to the weapon profile.

Usage::

    panel = CDMCalibrationPanel(db=database, parent=window)
    panel.set_profile(weapon_ballistic_profile)
    panel.show()
"""

from __future__ import annotations

from typing import Any

from ..field_planning.models import WeaponBallisticProfile
from ..field_planning.weather_history import DropMeasurement, calibrate_bc_from_drops
from ..qt_compat import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFont,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QSplitter,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QTimer,
    QVBoxLayout,
    QWidget,
    Signal,
)

try:
    import pyqtgraph as pg

    _HAS_PG = True
except Exception:
    pg = None  # type: ignore[assignment]
    _HAS_PG = False


class CDMCalibrationPanel(QDialog):
    """Back-calculate BC from field-measured bullet drops."""

    bc_calibrated = Signal(float, float)  # (bc, rms_cm)

    def __init__(self, db: Any = None, parent=None):
        super().__init__(parent)
        self._db = db
        self._profile: WeaponBallisticProfile | None = None
        self._result_bc: float | None = None
        self._result_rms: float | None = None

        self.setWindowTitle(
            "CDM BC-kalibrering — tilbakebereging fra egne drop-målinger"
        )
        self.resize(900, 620)
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

    def set_profile(self, profile: WeaponBallisticProfile) -> None:
        self._profile = profile
        self._profile_label.setText(
            f"{profile.rifle_name}  |  BC {profile.learned_bc:.4f} ({profile.bc_source})"
            f"  |  MV {profile.learned_mv_fps:.0f} fps"
        )
        self._mv_spin.setValue(profile.learned_mv_fps)
        self._bc_type_combo.setCurrentText(profile.learned_bc_type or "G7")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(8, 8, 8, 8)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("CDM BC-KALIBRERING")
        f = QFont()
        f.setBold(True)
        f.setPointSize(12)
        title.setFont(f)
        hdr.addWidget(title)
        hdr.addStretch()
        self._profile_label = QLabel("Ingen profil valgt")
        self._profile_label.setStyleSheet("color: #80b0ff; font-size: 9.5pt;")
        hdr.addWidget(self._profile_label)
        root.addLayout(hdr)

        # Instructions
        info = QLabel(
            "Mål faktisk treffpunkt under nulllinja på banen din. "
            "Legg inn avstand + målt dropp nedenfor, trykk Kalibrér."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #b0b6be; font-size: 9.5pt;")
        root.addWidget(info)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: input ──────────────────────────────────────────────
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 4, 0)
        lv.setSpacing(6)

        # MV + BC type row
        meta = QHBoxLayout()
        meta.addWidget(QLabel("MV fps:"))
        self._mv_spin = QDoubleSpinBox()
        self._mv_spin.setRange(500, 5000)
        self._mv_spin.setValue(2650.0)
        self._mv_spin.setDecimals(0)
        self._mv_spin.setFixedWidth(80)
        meta.addWidget(self._mv_spin)

        meta.addWidget(QLabel("BC-type:"))
        self._bc_type_combo = QComboBox()
        self._bc_type_combo.addItems(["G7", "G1"])
        self._bc_type_combo.setFixedWidth(60)
        meta.addWidget(self._bc_type_combo)

        meta.addWidget(QLabel("Null m:"))
        self._zero_spin = QDoubleSpinBox()
        self._zero_spin.setRange(25, 300)
        self._zero_spin.setValue(100.0)
        self._zero_spin.setDecimals(0)
        self._zero_spin.setFixedWidth(65)
        meta.addWidget(self._zero_spin)

        meta.addWidget(QLabel("Temp °C:"))
        self._temp_spin = QDoubleSpinBox()
        self._temp_spin.setRange(-40, 50)
        self._temp_spin.setValue(15.0)
        self._temp_spin.setDecimals(1)
        self._temp_spin.setFixedWidth(65)
        meta.addWidget(self._temp_spin)

        meta.addWidget(QLabel("Trykk hPa:"))
        self._press_spin = QDoubleSpinBox()
        self._press_spin.setRange(850, 1080)
        self._press_spin.setValue(1013.25)
        self._press_spin.setDecimals(1)
        self._press_spin.setFixedWidth(80)
        meta.addWidget(self._press_spin)
        meta.addStretch()
        lv.addLayout(meta)

        # Drop table
        lv.addWidget(QLabel("Drop-målinger (treffpunkt under nulllinja):"))
        self._drop_table = QTableWidget()
        self._drop_table.setColumnCount(3)
        self._drop_table.setHorizontalHeaderLabels(
            ["Avstand m", "Målt dropp cm", "Notater"]
        )
        hh = self._drop_table.horizontalHeader()
        if hh:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            hh.setStretchLastSection(True)
        self._drop_table.setAlternatingRowColors(True)
        self._drop_table.setStyleSheet("font-size: 10pt;")
        lv.addWidget(self._drop_table)

        # Preset distances + add/remove
        btn_row = QHBoxLayout()
        for dist in [200, 300, 400, 500, 600, 800]:
            b = QPushButton(f"{dist}m")
            b.setFixedWidth(46)
            b.setStyleSheet("padding: 2px 3px; font-size: 9pt;")
            b.clicked.connect(lambda _, d=dist: self._add_row(d))
            btn_row.addWidget(b)
        btn_row.addStretch()
        rem_btn = QPushButton("– Fjern")
        rem_btn.setFixedWidth(60)
        rem_btn.clicked.connect(self._remove_row)
        btn_row.addWidget(rem_btn)
        lv.addLayout(btn_row)

        # Calibrate button + progress
        cal_btn = QPushButton("⚡ Kalibrér BC")
        cal_btn.setStyleSheet(
            "background: #1a6abf; color: white; font-weight: bold; padding: 7px; font-size: 11pt;"
        )
        cal_btn.clicked.connect(self._run_calibration)
        lv.addWidget(cal_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setVisible(False)
        lv.addWidget(self._progress)

        splitter.addWidget(left)

        # ── Right: results ──────────────────────────────────────────
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 0, 0, 0)
        rv.setSpacing(6)

        res_hdr = QLabel("Resultat")
        f2 = QFont()
        f2.setBold(True)
        res_hdr.setFont(f2)
        rv.addWidget(res_hdr)

        self._result_label = QLabel("—")
        self._result_label.setStyleSheet(
            "background: #1a2a3a; color: #80d0ff; padding: 8px 12px; "
            "border-radius: 6px; font-size: 13pt; font-weight: bold;"
        )
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setMinimumHeight(60)
        rv.addWidget(self._result_label)

        self._rms_label = QLabel("")
        self._rms_label.setStyleSheet("color: #b0b6be; font-size: 10pt;")
        self._rms_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rv.addWidget(self._rms_label)

        # Comparison table: measured vs computed
        rv.addWidget(QLabel("Målt vs beregnet drop:"))
        self._compare_table = QTableWidget()
        self._compare_table.setColumnCount(4)
        self._compare_table.setHorizontalHeaderLabels(
            ["Avstand m", "Målt cm", "Beregnet cm", "Diff cm"]
        )
        ch = self._compare_table.horizontalHeader()
        if ch:
            ch.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            ch.setStretchLastSection(True)
        self._compare_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._compare_table.setAlternatingRowColors(True)
        self._compare_table.setStyleSheet("font-size: 10pt;")
        rv.addWidget(self._compare_table)

        # Drop chart
        if _HAS_PG:
            self._chart = pg.PlotWidget()
            self._chart.setBackground("#161a1f")
            self._chart.setTitle(
                "Drop-kurve (cm under null)", color="#b0b6be", size="9pt"
            )
            self._chart.getAxis("bottom").setLabel("Avstand m", color="#b0b6be")
            self._chart.getAxis("left").setLabel("Drop cm", color="#b0b6be")
            self._chart.setMaximumHeight(180)
            rv.addWidget(self._chart)
        else:
            self._chart = None

        # Save to profile button
        self._save_btn = QPushButton("💾 Lagre kalibrert BC til profil")
        self._save_btn.setEnabled(False)
        self._save_btn.setStyleSheet(
            "background: #27ae60; color: white; font-weight: bold; padding: 6px;"
        )
        self._save_btn.clicked.connect(self._save_to_profile)
        rv.addWidget(self._save_btn)

        self._save_status = QLabel("")
        self._save_status.setStyleSheet("color: #80e080; font-size: 9.5pt;")
        rv.addWidget(self._save_status)
        rv.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([420, 420])
        root.addWidget(splitter)

    # ------------------------------------------------------------------
    # Drop table
    # ------------------------------------------------------------------

    def _add_row(self, dist_m: float = 300.0) -> None:
        n = self._drop_table.rowCount()
        self._drop_table.insertRow(n)
        self._drop_table.setItem(n, 0, QTableWidgetItem(str(int(dist_m))))
        self._drop_table.setItem(n, 1, QTableWidgetItem(""))
        self._drop_table.setItem(n, 2, QTableWidgetItem(""))

    def _remove_row(self) -> None:
        rows = sorted(
            {idx.row() for idx in self._drop_table.selectedIndexes()}, reverse=True
        )
        for r in rows:
            self._drop_table.removeRow(r)

    def _get_measurements(self) -> list[DropMeasurement]:
        out = []
        for i in range(self._drop_table.rowCount()):
            try:
                dist = float(
                    (self._drop_table.item(i, 0) or QTableWidgetItem("0")).text()
                )
                drop = float(
                    (self._drop_table.item(i, 1) or QTableWidgetItem("")).text()
                )
                out.append(
                    DropMeasurement(
                        distance_m=dist,
                        measured_drop_cm=drop,
                        conditions_temp_c=self._temp_spin.value(),
                        conditions_pressure_hpa=self._press_spin.value(),
                    )
                )
            except (ValueError, AttributeError):
                pass
        return out

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def _run_calibration(self) -> None:
        measurements = self._get_measurements()
        if not measurements:
            self._result_label.setText("Ingen målinger")
            return
        self._progress.setVisible(True)
        self._result_label.setText("Beregner…")
        # Defer to next event loop tick so UI updates before the heavy computation
        QTimer.singleShot(50, self._do_calibrate)

    def _do_calibrate(self) -> None:
        measurements = self._get_measurements()
        mv = self._mv_spin.value()
        zero = self._zero_spin.value()
        bc_type = self._bc_type_combo.currentText()
        initial = self._profile.learned_bc if self._profile else 0.200

        try:
            bc, rms = calibrate_bc_from_drops(
                measurements=measurements,
                nominal_mv_fps=mv,
                zero_distance_m=zero,
                bc_type=bc_type,
                initial_bc=initial,
            )
        except Exception as exc:
            self._result_label.setText(f"Feil: {exc}")
            self._progress.setVisible(False)
            return

        self._result_bc = bc
        self._result_rms = rms
        self._progress.setVisible(False)

        quality = (
            "Utmerket"
            if rms < 1.0
            else ("God" if rms < 3.0 else "Svak — mer data anbefalt")
        )
        self._result_label.setText(f"BC {bc_type} = {bc:.4f}")
        self._rms_label.setText(f"RMS-feil: {rms:.2f} cm  |  Kvalitet: {quality}")
        if self._profile:
            delta = bc - self._profile.learned_bc
            self._rms_label.setText(
                self._rms_label.text() + f"  |  Endring fra profil: {delta:+.4f}"
            )

        self._fill_compare_table(measurements, bc, mv, zero, bc_type)
        self._draw_chart(measurements, bc, mv, zero, bc_type)
        self._save_btn.setEnabled(True)
        self.bc_calibrated.emit(bc, rms)

    def _fill_compare_table(
        self,
        measurements: list[DropMeasurement],
        bc: float,
        mv: float,
        zero: float,
        bc_type: str,
    ) -> None:
        from ..utils.advanced_ballistics import (
            AdvancedBallisticsEngine,
            AtmosphericConditions,
        )

        engine = AdvancedBallisticsEngine()
        self._compare_table.setRowCount(len(measurements))
        for i, m in enumerate(measurements):
            cond = AtmosphericConditions(
                temperature_f=m.conditions_temp_c * 9 / 5 + 32,
                pressure_inhg=m.conditions_pressure_hpa * 0.02953,
                humidity_percent=50.0,
                altitude_ft=0.0,
            )
            computed = None
            try:
                pts = engine.calculate_trajectory(
                    velocity_fps=mv,
                    bc=bc,
                    weight_grains=168.0,
                    zero_distance_m=zero,
                    max_distance_m=m.distance_m + 5.0,
                    step_size_m=max(1.0, m.distance_m / 100.0),
                    bc_type=bc_type,
                    conditions=cond,
                    wind_speed_mph=0.0,
                    wind_angle_deg=90.0,
                    latitude_deg=60.0,
                    azimuth_deg=0.0,
                    twist_rate=10.0,
                    twist_direction="RIGHT",
                )
                if pts:
                    pt = min(pts, key=lambda p: abs(p.distance_m - m.distance_m))
                    computed = pt.drop_cm
            except Exception:
                pass

            diff = (computed - m.measured_drop_cm) if computed is not None else None

            def _c(text: str, color: str | None = None) -> QTableWidgetItem:
                it = QTableWidgetItem(text)
                it.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                if color:
                    try:
                        from ..qt_compat import QtGui

                        it.setForeground(QtGui.QColor(color))
                    except Exception:
                        pass
                return it

            diff_color = None
            if diff is not None:
                diff_color = (
                    "#80e080"
                    if abs(diff) < 1.5
                    else ("#f0c040" if abs(diff) < 4.0 else "#e06060")
                )

            self._compare_table.setItem(i, 0, _c(f"{m.distance_m:.0f}"))
            self._compare_table.setItem(i, 1, _c(f"{m.measured_drop_cm:.1f}"))
            self._compare_table.setItem(
                i, 2, _c(f"{computed:.1f}" if computed is not None else "—")
            )
            self._compare_table.setItem(
                i, 3, _c(f"{diff:+.1f}" if diff is not None else "—", diff_color)
            )

    def _draw_chart(
        self,
        measurements: list[DropMeasurement],
        bc: float,
        mv: float,
        zero: float,
        bc_type: str,
    ) -> None:
        if not _HAS_PG or self._chart is None:
            return
        from ..utils.advanced_ballistics import (
            AdvancedBallisticsEngine,
            AtmosphericConditions,
        )

        engine = AdvancedBallisticsEngine()
        max_dist = max(m.distance_m for m in measurements) + 50
        cond = AtmosphericConditions(
            temperature_f=self._temp_spin.value() * 9 / 5 + 32,
            pressure_inhg=self._press_spin.value() * 0.02953,
            humidity_percent=50.0,
            altitude_ft=0.0,
        )
        try:
            pts = engine.calculate_trajectory(
                velocity_fps=mv,
                bc=bc,
                weight_grains=168.0,
                zero_distance_m=zero,
                max_distance_m=max_dist,
                step_size_m=5.0,
                bc_type=bc_type,
                conditions=cond,
                wind_speed_mph=0.0,
                wind_angle_deg=90.0,
                latitude_deg=60.0,
                azimuth_deg=0.0,
                twist_rate=10.0,
                twist_direction="RIGHT",
            )
        except Exception:
            pts = []

        self._chart.clear()
        if pts:
            xs = [p.distance_m for p in pts]
            ys = [p.drop_cm for p in pts]
            self._chart.plot(xs, ys, pen=pg.mkPen("#4080ff", width=2), name="Beregnet")

        # Scatter: measured points
        mx = [m.distance_m for m in measurements]
        my = [m.measured_drop_cm for m in measurements]
        scatter = pg.ScatterPlotItem(
            x=mx,
            y=my,
            symbol="o",
            size=10,
            pen=pg.mkPen("#ff6600", width=2),
            brush=pg.mkBrush("#ff6600"),
        )
        self._chart.addItem(scatter)

    # ------------------------------------------------------------------
    # Save to profile
    # ------------------------------------------------------------------

    def _save_to_profile(self) -> None:
        if self._result_bc is None or self._db is None or self._profile is None:
            return
        try:
            self._db.execute_query(
                """UPDATE load_development_sessions
                   SET learning_state_json = json_set(
                       COALESCE(learning_state_json, '{}'),
                       '$.calibrated_bc', ?,
                       '$.bc_source', 'CDM-kalibrering fra drop-målinger'
                   )
                   WHERE rifle_id = ?
                   ORDER BY created_date DESC
                   LIMIT 1""",
                (self._result_bc, self._profile.rifle_id),
            )
            self._save_status.setText(
                f"✔ BC {self._result_bc:.4f} lagret til profil for rifle_id={self._profile.rifle_id}"
            )
        except Exception as exc:
            # Fallback: show the value so user can note it manually
            self._save_status.setText(
                f"Kalibrert BC: {self._result_bc:.4f}  (lagring feilet: {exc})"
            )
