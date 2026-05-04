"""
Drop Chart Generator & Wind Drift Calculator
Genererer drop tables og DOPE cards med PDF export
"""

import logging
import math
from datetime import datetime

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
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
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from HjemmeladingApp.utils import units

from ..database.database import get_database
from ..utils.ballistics import (
    BallisticsCalculator,
    estimate_time_of_flight_seconds,
    estimate_wind_drift_cm,
)
from ..utils.drag_models import (
    parse_bc_segments,
    preferred_drag_model,
    resolve_drag_choice,
)
from ..utils.environment import BallisticEnvironment
from ..utils.i18n import get_current_language, tr


def _preferred_drag_model() -> str:
    return preferred_drag_model()


def _default_environment() -> BallisticEnvironment:
    return BallisticEnvironment(
        temperature_c=15.0,
        pressure_hpa=1013.25,
        humidity_percent=50.0,
        altitude_m=0.0,
        temperature_source="assumed",
        pressure_source="assumed",
        humidity_source="assumed",
        altitude_source="assumed",
    )


def _build_environment(
    temperature_c: float,
    pressure_hpa: float,
    humidity_percent: float,
    altitude_m: float,
) -> BallisticEnvironment:
    return BallisticEnvironment(
        temperature_c=float(temperature_c),
        pressure_hpa=float(pressure_hpa),
        humidity_percent=float(humidity_percent),
        altitude_m=float(altitude_m),
        temperature_source="user",
        pressure_source="user",
        humidity_source="user",
        altitude_source="user",
    )


_logger = logging.getLogger(__name__)


class DropChartGenerator(QWidget):
    """Widget for drop chart generering og wind drift beregning"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.ballistics_calc = BallisticsCalculator()
        self.current_language = get_current_language() or "en"
        self._last_drag_resolution: dict[str, str | float | None] | None = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Tittel
        title = QLabel(tr("drop_chart_title", self.current_language))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        subtitle = QLabel(tr("drop_chart_subtitle", self.current_language))
        subtitle.setStyleSheet("color: gray; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Drop Chart
        tabs.addTab(self.create_drop_chart_tab(), tr("drop_chart_tab", self.current_language))

        # Tab 2: Wind Drift
        tabs.addTab(self.create_wind_drift_tab(), tr("wind_drift_tab", self.current_language))

        # Tab 3: Combined DOPE Card
        tabs.addTab(self.create_dope_card_tab(), tr("dope_card_tab", self.current_language))

    def create_drop_chart_tab(self):
        """Oppretter drop chart tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Input seksjon
        input_group = QGroupBox(tr("common_settings"))
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        # Ammunisjon
        self.drop_ammo = QComboBox()
        self.drop_ammo.addItem(tr("drop_chart_select_ammo"), None)
        self.load_ammo_profiles(self.drop_ammo)
        self.drop_ammo.currentIndexChanged.connect(self.on_ammo_selected)
        input_layout.addRow(f"{tr('common_ammunition')}:", self.drop_ammo)

        # Zero distance
        self.drop_zero = QSpinBox()
        self.drop_zero.setRange(25, 500)
        self.drop_zero.setValue(100)
        self.drop_zero.setSuffix(" m")
        self.drop_zero.valueChanged.connect(self.on_ammo_selected)
        input_layout.addRow(tr("drop_chart_zero_distance"), self.drop_zero)

        # Distanse-område
        dist_layout = QHBoxLayout()

        self.drop_start = QSpinBox()
        self.drop_start.setRange(0, 2000)
        self.drop_start.setValue(100)
        self.drop_start.setSuffix(" m")
        dist_layout.addWidget(QLabel(tr("drop_chart_range_from")))
        dist_layout.addWidget(self.drop_start)

        self.drop_end = QSpinBox()
        self.drop_end.setRange(0, 2000)
        self.drop_end.setValue(1000)
        self.drop_end.setSuffix(" m")
        dist_layout.addWidget(QLabel(tr("drop_chart_range_to")))
        dist_layout.addWidget(self.drop_end)

        self.drop_step = QSpinBox()
        self.drop_step.setRange(10, 200)
        self.drop_step.setValue(50)
        self.drop_step.setSuffix(" m")
        dist_layout.addWidget(QLabel(tr("drop_chart_range_step")))
        dist_layout.addWidget(self.drop_step)

        input_layout.addRow(tr("drop_chart_distance_range"), dist_layout)

        # Enheter
        self.drop_units = QComboBox()
        self.drop_units.addItems(["MOA", "MRAD", "CM", "INCHES"])
        input_layout.addRow(tr("drop_chart_unit"), self.drop_units)

        self.drop_drag_model = QComboBox()
        self.drop_drag_model.addItem(tr("drop_chart_drag_model_auto", self.current_language), "AUTO")
        self.drop_drag_model.addItem("G1", "G1")
        self.drop_drag_model.addItem("G7", "G7")
        preferred_drag = _preferred_drag_model()
        for idx in range(self.drop_drag_model.count()):
            if self.drop_drag_model.itemData(idx) == preferred_drag:
                self.drop_drag_model.setCurrentIndex(idx)
                break
        self.drop_drag_model.currentIndexChanged.connect(self.on_ammo_selected)
        input_layout.addRow(tr("drop_chart_drag_model", self.current_language), self.drop_drag_model)

        self.drop_drag_info = QLabel(tr("drop_chart_drag_model_hint", self.current_language))
        self.drop_drag_info.setWordWrap(True)
        self.drop_drag_info.setStyleSheet("color: gray; font-size: 9pt;")
        input_layout.addRow("", self.drop_drag_info)

        env_layout = QHBoxLayout()
        self.drop_temp = QDoubleSpinBox()
        self.drop_temp.setRange(-40.0, 60.0)
        self.drop_temp.setValue(15.0)
        self.drop_temp.setSuffix(" °C")
        env_layout.addWidget(QLabel(tr("common_temperature")))
        env_layout.addWidget(self.drop_temp)

        self.drop_pressure = QDoubleSpinBox()
        self.drop_pressure.setRange(800.0, 1100.0)
        self.drop_pressure.setValue(1013.25)
        self.drop_pressure.setDecimals(2)
        self.drop_pressure.setSuffix(" hPa")
        env_layout.addWidget(QLabel(tr("common_pressure")))
        env_layout.addWidget(self.drop_pressure)

        self.drop_humidity = QSpinBox()
        self.drop_humidity.setRange(0, 100)
        self.drop_humidity.setValue(50)
        self.drop_humidity.setSuffix(" %")
        env_layout.addWidget(QLabel(tr("common_humidity_short")))
        env_layout.addWidget(self.drop_humidity)

        self.drop_altitude = QSpinBox()
        self.drop_altitude.setRange(-500, 5000)
        self.drop_altitude.setValue(0)
        self.drop_altitude.setSuffix(" m")
        env_layout.addWidget(QLabel(tr("common_altitude")))
        env_layout.addWidget(self.drop_altitude)
        input_layout.addRow(tr("common_environment"), env_layout)

        # Inkluder ekstra data
        self.drop_include_velocity = QCheckBox(tr("drop_chart_show_velocity"))
        self.drop_include_velocity.setChecked(True)
        input_layout.addRow(self.drop_include_velocity)

        self.drop_include_energy = QCheckBox(tr("drop_chart_show_energy"))
        self.drop_include_energy.setChecked(True)
        input_layout.addRow(self.drop_include_energy)

        self.drop_include_tof = QCheckBox(tr("drop_chart_show_tof"))
        self.drop_include_tof.setChecked(True)
        input_layout.addRow(self.drop_include_tof)

        layout.addWidget(input_group)

        # KIKKERT JUSTERING - Sammenligning med forrige ladning
        self.scope_adjustment_group = QGroupBox(tr("drop_chart_scope_adjustment_title"))
        self.scope_adjustment_group.setStyleSheet(
            """
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                margin-top: 10px;
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
        scope_layout = QVBoxLayout()
        self.scope_adjustment_group.setLayout(scope_layout)

        self.scope_adjustment_label = QLabel(tr("drop_chart_scope_adjustment_placeholder"))
        self.scope_adjustment_label.setWordWrap(True)
        self.scope_adjustment_label.setStyleSheet("color: #856404; font-weight: normal; padding: 10px;")
        scope_layout.addWidget(self.scope_adjustment_label)

        self.scope_adjustment_group.setVisible(False)
        layout.addWidget(self.scope_adjustment_group)

        # Generer-knapp
        generate_btn = QPushButton(tr("drop_chart_generate"))
        generate_btn.setMinimumHeight(50)
        generate_btn.setStyleSheet("font-size: 14pt; font-weight: bold; background-color: #2196F3; color: white;")
        generate_btn.clicked.connect(self.generate_drop_chart)
        layout.addWidget(generate_btn)

        # Resultat-tabell
        self.drop_table = QTableWidget()
        layout.addWidget(self.drop_table)

        # Export-knapper
        export_layout = QHBoxLayout()

        export_csv_btn = QPushButton(tr("common_export_csv"))
        export_csv_btn.clicked.connect(lambda: self.export_drop_chart("csv"))
        export_layout.addWidget(export_csv_btn)

        export_pdf_btn = QPushButton(tr("common_export_pdf"))
        export_pdf_btn.clicked.connect(lambda: self.export_drop_chart("pdf"))
        export_layout.addWidget(export_pdf_btn)

        print_btn = QPushButton(tr("common_print"))
        print_btn.clicked.connect(self.print_drop_chart)
        export_layout.addWidget(print_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

        return widget

    @staticmethod
    def _convert_drop_value(
        drop_cm: float,
        distance_m: int,
        unit: str,
        ballistics_calc: BallisticsCalculator,
    ) -> float:
        if unit == "MOA":
            return ballistics_calc.cm_to_moa(drop_cm, distance_m)
        if unit == "MRAD":
            return ballistics_calc.cm_to_mrad(drop_cm, distance_m)
        if unit == "INCHES":
            return units.mm_to_inches(drop_cm * 10.0)
        return drop_cm

    def create_wind_drift_tab(self):
        """Oppretter wind drift tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Info
        info = QLabel(tr("wind_drift_info_html"))
        info.setWordWrap(True)
        layout.addWidget(info)

        # Input seksjon
        input_group = QGroupBox(tr("common_settings"))
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        # Ammunisjon
        self.wind_ammo = QComboBox()
        self.wind_ammo.addItem(tr("drop_chart_select_ammo"), None)
        self.load_ammo_profiles(self.wind_ammo)
        input_layout.addRow(f"{tr('common_ammunition')}:", self.wind_ammo)

        # Distanse
        self.wind_distance = QSpinBox()
        self.wind_distance.setRange(100, 2000)
        self.wind_distance.setValue(600)
        self.wind_distance.setSuffix(" m")
        input_layout.addRow(tr("common_distance"), self.wind_distance)

        # Vind-hastigheter
        wind_speeds_layout = QHBoxLayout()

        self.wind_speed_1 = QDoubleSpinBox()
        self.wind_speed_1.setRange(0, 30)
        self.wind_speed_1.setValue(2.5)
        self.wind_speed_1.setSuffix(" m/s")
        wind_speeds_layout.addWidget(QLabel(tr("drop_chart_wind_1")))
        wind_speeds_layout.addWidget(self.wind_speed_1)

        self.wind_speed_2 = QDoubleSpinBox()
        self.wind_speed_2.setRange(0, 30)
        self.wind_speed_2.setValue(5.0)
        self.wind_speed_2.setSuffix(" m/s")
        wind_speeds_layout.addWidget(QLabel(tr("drop_chart_wind_2")))
        wind_speeds_layout.addWidget(self.wind_speed_2)

        self.wind_speed_3 = QDoubleSpinBox()
        self.wind_speed_3.setRange(0, 30)
        self.wind_speed_3.setValue(10.0)
        self.wind_speed_3.setSuffix(" m/s")
        wind_speeds_layout.addWidget(QLabel(tr("drop_chart_wind_3")))
        wind_speeds_layout.addWidget(self.wind_speed_3)

        input_layout.addRow(tr("drop_chart_wind_speeds"), wind_speeds_layout)

        # Vindretning (relativ til skudd)
        self.wind_angle = QSpinBox()
        self.wind_angle.setRange(0, 180)
        self.wind_angle.setValue(90)
        self.wind_angle.setSuffix(" °")
        input_layout.addRow(tr("drop_chart_wind_angle"), self.wind_angle)

        wind_angle_help = QLabel(tr("drop_chart_wind_angle_help_html"))
        wind_angle_help.setWordWrap(True)
        wind_angle_help.setStyleSheet("color: gray; font-size: 9pt;")
        input_layout.addRow("", wind_angle_help)

        # Quick presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel(tr("common_quick")))

        for angle, label_key in [
            (0, "drop_chart_wind_preset_head_tail"),
            (45, "drop_chart_wind_preset_half_value"),
            (90, "drop_chart_wind_preset_full_value"),
        ]:
            btn = QPushButton(tr(label_key))
            btn.clicked.connect(lambda checked, a=angle: self.wind_angle.setValue(a))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        input_layout.addRow(preset_layout)

        layout.addWidget(input_group)

        # Generer-knapp
        calc_wind_btn = QPushButton(tr("drop_chart_calculate_wind"))
        calc_wind_btn.setMinimumHeight(50)
        calc_wind_btn.setStyleSheet("font-size: 14pt; font-weight: bold; background-color: #4CAF50; color: white;")
        calc_wind_btn.clicked.connect(self.calculate_wind_drift)
        layout.addWidget(calc_wind_btn)

        # Resultat
        self.wind_result = QTextEdit()
        self.wind_result.setReadOnly(True)
        layout.addWidget(self.wind_result)

        return widget

    def create_dope_card_tab(self):
        """Oppretter kombinert DOPE card"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(tr("dope_card_info_html"))
        info.setWordWrap(True)
        layout.addWidget(info)

        # Input
        input_group = QGroupBox(tr("common_settings"))
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        self.dope_ammo = QComboBox()
        self.dope_ammo.addItem(tr("drop_chart_select_ammo"), None)
        self.load_ammo_profiles(self.dope_ammo)
        input_layout.addRow(f"{tr('common_ammunition')}:", self.dope_ammo)

        self.dope_rifle = QLineEdit()
        self.dope_rifle.setPlaceholderText(tr("dope_card_rifle_placeholder"))
        input_layout.addRow(tr("ballistics_rifle_label"), self.dope_rifle)

        self.dope_scope = QLineEdit()
        self.dope_scope.setPlaceholderText(tr("dope_card_scope_placeholder"))
        input_layout.addRow(tr("common_optic"), self.dope_scope)

        self.dope_zero = QSpinBox()
        self.dope_zero.setRange(25, 500)
        self.dope_zero.setValue(100)
        self.dope_zero.setSuffix(" m")
        input_layout.addRow(tr("common_zero"), self.dope_zero)

        layout.addWidget(input_group)

        # Generer
        generate_dope_btn = QPushButton(tr("dope_card_generate"))
        generate_dope_btn.setMinimumHeight(50)
        generate_dope_btn.setStyleSheet("font-size: 14pt; font-weight: bold; background-color: #FF9800; color: white;")
        generate_dope_btn.clicked.connect(self.generate_dope_card)
        layout.addWidget(generate_dope_btn)

        # Preview
        self.dope_preview = QTextEdit()
        self.dope_preview.setReadOnly(True)
        layout.addWidget(self.dope_preview)

        # Export
        export_dope_btn = QPushButton(tr("dope_card_export_pdf"))
        export_dope_btn.clicked.connect(self.export_dope_pdf)
        layout.addWidget(export_dope_btn)

        return widget

    def load_ammo_profiles(self, combo_widget):
        """Laster ammunisjonsprofiler"""
        ammos = self.db.execute_query(
            """
            SELECT id, name, velocity_fps, bc_g1, bc_g7, bc_segments_json, caliber, bullet_weight
            FROM ammo_profiles
            ORDER BY name
        """
        )

        for row in ammos:
            ammo_id, name, velocity, bc_g1, bc_g7, bc_segments_json, caliber, weight = row
            bc_label = ""
            if parse_bc_segments(bc_segments_json):
                bc_label = " | Segmented BC"
            elif bc_g7:
                bc_label = f" | G7 {bc_g7:.3f}"
            elif bc_g1:
                bc_label = f" | G1 {bc_g1:.3f}"
            display = f"{name} ({caliber}) - {velocity} fps" if velocity else name
            display += bc_label
            combo_widget.addItem(display, ammo_id)

    def _get_ammo_profile_row(self, ammo_id):
        if not ammo_id:
            return None
        ammo_data = self.db.execute_query(
            "SELECT name, velocity_fps, bc_g1, bc_g7, bc_segments_json, bullet_weight, caliber FROM ammo_profiles WHERE id = ?",
            (ammo_id,),
        )
        if ammo_data:
            return ammo_data[0]
        QMessageBox.warning(
            self,
            tr("drop_chart_profile_missing_title"),
            tr("drop_chart_profile_missing_message"),
        )
        return None

    def _warn_missing_bc(self):
        QMessageBox.warning(
            self,
            tr("msg_missing_data", self.current_language),
            tr("drop_chart_missing_bc", self.current_language),
        )

    def _resolve_drag_model(
        self,
        bc_g1: float | None,
        bc_g7: float | None,
        requested: str | None = None,
        bc_segments: str | None = None,
        velocity_fps: float | None = None,
    ) -> dict[str, str | float | None]:
        requested_model = str(requested or "AUTO").strip().upper()
        resolved = resolve_drag_choice(
            bc_g1,
            bc_g7,
            requested_model,
            bc_segments,
            velocity_fps=velocity_fps,
        )
        resolved_model = str(resolved["resolved_model"])
        note_key = "drop_chart_drag_using_g1"
        if requested_model == "AUTO":
            note_key = "drop_chart_drag_auto_g7" if resolved_model == "G7" else "drop_chart_drag_auto_g1"
        elif requested_model == "G7":
            note_key = "drop_chart_drag_using_g7" if resolved_model == "G7" else "drop_chart_drag_g7_missing"
        elif requested_model == "G1" and resolved_model != "G1":
            note_key = "drop_chart_drag_g1_missing"

        return {
            "requested_model": requested_model,
            "resolved_model": resolved_model,
            "bc_value": resolved["bc_value"],
            "source": resolved["source"],
            "note_key": note_key,
            "segment_match": resolved.get("segment_match"),
        }

    @staticmethod
    def _format_segment_match(segment_match: dict[str, object] | None, drag_model: str) -> str:
        if not segment_match:
            return ""
        model = str(segment_match.get("model") or drag_model or "AUTO").strip().upper()
        if model == "AUTO":
            model = str(drag_model or "AUTO").strip().upper()
        bc_value = segment_match.get("bc_g7") or segment_match.get("bc_g1") or segment_match.get("bc")
        min_v = segment_match.get("velocity_fps_min")
        max_v = segment_match.get("velocity_fps_max")
        if bc_value is None:
            return ""
        if max_v is not None:
            return f"{model} {float(bc_value):.3f} @ " f"{float(min_v or 0):.0f}-{float(max_v):.0f} fps"
        return f"{model} {float(bc_value):.3f} @ {float(min_v or 0):.0f}+ fps"

    def on_ammo_selected(self):
        """Håndterer ammunisjonsvalg og viser sammenligning med forrige ladning"""
        try:
            self._on_ammo_selected_impl()
        except Exception:
            import traceback as _tb

            try:
                _logger.critical("on_ammo_selected crashed: %s", _tb.format_exc())
            except Exception:
                pass
            raise

    def _on_ammo_selected_impl(self):
        ammo_id = self.drop_ammo.currentData()
        if not ammo_id:
            self.scope_adjustment_group.setVisible(False)
            self.drop_drag_info.setText(tr("drop_chart_drag_model_hint", self.current_language))
            return

        # Hent valgt ammunisjon
        current_ammo = self.db.execute_query(
            """
            SELECT name, rifle_id, velocity_fps, bc_g1, bc_g7, bc_segments_json, bullet_weight, caliber, created_date
            FROM ammo_profiles
            WHERE id = ?
        """,
            (ammo_id,),
        )

        if not current_ammo:
            self.scope_adjustment_group.setVisible(False)
            return

        (
            name,
            rifle_id,
            velocity,
            bc_g1,
            bc_g7,
            bc_segments_json,
            weight,
            caliber,
            created,
        ) = current_ammo[0]
        drag_resolution = self._resolve_drag_model(
            bc_g1,
            bc_g7,
            (self.drop_drag_model.currentData() if hasattr(self, "drop_drag_model") else "AUTO"),
            bc_segments_json,
            velocity,
        )
        self._last_drag_resolution = drag_resolution
        bc = drag_resolution["bc_value"]
        drag_model = str(drag_resolution["resolved_model"])
        segment_label = self._format_segment_match(drag_resolution.get("segment_match"), drag_model)
        drag_info_text = tr(
            str(drag_resolution["note_key"]),
            self.current_language,
            value=f"{float(bc or 0):.3f}",
        )
        if segment_label:
            drag_info_text += f"\nSegmentert BC aktiv: {segment_label}"
        self.drop_drag_info.setText(drag_info_text)

        if not rifle_id or not velocity or not bc:
            self.scope_adjustment_group.setVisible(False)
            return

        # Find the previous load for the same rifle (excluding the current one)
        previous_ammo = self.db.execute_query(
            """
            SELECT name, velocity_fps, bc_g1, bc_g7, bc_segments_json, bullet_weight, caliber, created_date
            FROM ammo_profiles
            WHERE rifle_id = ? AND id != ? AND velocity_fps IS NOT NULL AND (bc_g1 IS NOT NULL OR bc_g7 IS NOT NULL OR bc_segments_json IS NOT NULL)
            ORDER BY created_date DESC
            LIMIT 1
        """,
            (rifle_id, ammo_id),
        )

        if not previous_ammo:
            self.scope_adjustment_label.setText(
                f"<b>NEW LOAD:</b> {name}<br>"
                f"<i>This is the first load for this rifle. No comparison is available.</i>"
            )
            self.scope_adjustment_group.setVisible(True)
            return

        prev_name, prev_bc_g1, prev_bc_g7 = None, None, None
        (
            prev_name,
            prev_vel,
            prev_bc_g1,
            prev_bc_g7,
            prev_bc_segments_json,
            prev_weight,
            prev_cal,
            prev_created,
        ) = previous_ammo[0]
        prev_drag_resolution = self._resolve_drag_model(
            prev_bc_g1, prev_bc_g7, drag_model, prev_bc_segments_json, prev_vel
        )
        prev_bc = prev_drag_resolution["bc_value"]

        # Calculate drop for both loads at 100 m, 300 m, and 600 m
        zero_dist = self.drop_zero.value()
        test_distances = [100, 300, 600]

        comparison_html = f"""
        <b>NEW LOAD:</b> {name} ({caliber})<br>
        • Velocity: {velocity} fps, BC ({drag_model}): {bc}, Bullet Weight: {weight} gr<br><br>

        <b>PREVIOUS LOAD:</b> {prev_name} ({prev_cal})<br>
        • Velocity: {prev_vel} fps, BC ({drag_model}): {prev_bc}, Bullet Weight: {prev_weight} gr<br><br>

        <b>SCOPE ADJUSTMENT (Zero: {zero_dist}m | Drag: {drag_model}):</b><br>
        <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
        <tr style='background-color: #f0f0f0; font-weight: bold;'>
            <td style='padding: 5px; border: 1px solid #ddd;'>Distance</td>
            <td style='padding: 5px; border: 1px solid #ddd;'>New Drop</td>
            <td style='padding: 5px; border: 1px solid #ddd;'>Previous Drop</td>
            <td style='padding: 5px; border: 1px solid #ddd;'>Difference</td>
            <td style='padding: 5px; border: 1px solid #ddd;'>Adjustment</td>
        </tr>
        """

        for dist in test_distances:
            # Drop for the new load
            drop_new = self.ballistics_calc.calculate_drop(velocity, float(bc), dist, zero_dist, drag_model)
            drop_new_moa = self.ballistics_calc.cm_to_moa(drop_new, dist)

            # Drop for the previous load
            drop_prev = self.ballistics_calc.calculate_drop(prev_vel, float(prev_bc), dist, zero_dist, drag_model)
            drop_prev_moa = self.ballistics_calc.cm_to_moa(drop_prev, dist)

            # Difference (negative = the new load drops less)
            diff_cm = drop_new - drop_prev
            diff_moa = drop_new_moa - drop_prev_moa

            # Scope adjustment (0.25 MOA/click standard)
            clicks = diff_moa / 0.25
            direction = "UP ↑" if clicks > 0 else "DOWN ↓" if clicks < 0 else "NONE"

            color = "#27ae60" if abs(diff_cm) < 5 else "#f39c12" if abs(diff_cm) < 15 else "#e74c3c"

            comparison_html += f"""
            <tr>
                <td style='padding: 5px; border: 1px solid #ddd;'>{dist}m</td>
                <td style='padding: 5px; border: 1px solid #ddd;'>{drop_new:.1f} cm ({drop_new_moa:.2f} MOA)</td>
                <td style='padding: 5px; border: 1px solid #ddd;'>{drop_prev:.1f} cm ({drop_prev_moa:.2f} MOA)</td>
                <td style='padding: 5px; border: 1px solid #ddd; background-color: {color}; color: white; font-weight: bold;'>{diff_cm:+.1f} cm ({diff_moa:+.2f} MOA)</td>
                <td style='padding: 5px; border: 1px solid #ddd; font-weight: bold;'>{direction} {abs(clicks):.1f} clicks</td>
            </tr>
            """

        comparison_html += """
        </table><br>
        <i>Tip: Green = minimal difference (&lt;5 cm), Yellow = moderate (5-15 cm), Red = large (&gt;15 cm)</i><br>
        <i>Standard click value: 0.25 MOA/click. Check your scope specifications.</i>
        """

        self.scope_adjustment_label.setText(comparison_html)
        self.scope_adjustment_group.setVisible(True)

    def generate_drop_chart(self):
        """Generate the drop chart"""
        ammo_id = self.drop_ammo.currentData()
        if not ammo_id:
            QMessageBox.warning(
                self,
                tr("common_missing_data_title"),
                tr("drop_chart_select_ammo_warning"),
            )
            return

        ammo_row = self._get_ammo_profile_row(ammo_id)
        if not ammo_row:
            return

        name, velocity, bc_g1, bc_g7, weight, caliber = ammo_row
        requested_model = self.drop_drag_model.currentData() if hasattr(self, "drop_drag_model") else "AUTO"
        drag_resolution = self._resolve_drag_model(bc_g1, bc_g7, requested_model)
        drag_model = str(drag_resolution["resolved_model"])
        bc = drag_resolution["bc_value"]
        if not bc:
            self._warn_missing_bc()
            return

        zero = self.drop_zero.value()
        start = self.drop_start.value()
        end = self.drop_end.value()
        step = self.drop_step.value()
        unit = self.drop_units.currentText()
        environment = _build_environment(
            self.drop_temp.value(),
            self.drop_pressure.value(),
            self.drop_humidity.value(),
            self.drop_altitude.value(),
        )

        # Generer tabell
        distances = list(range(start, end + 1, step))

        # Sett opp kolonner
        columns = ["Distanse (m)"]
        if unit == "MOA":
            columns.append("Drop (MOA)")
        elif unit == "MRAD":
            columns.append("Drop (MRAD)")
        elif unit == "CM":
            columns.append("Drop (cm)")
        elif unit == "INCHES":
            columns.append("Drop (inches)")

        if self.drop_include_velocity.isChecked():
            columns.append("Velocity (fps)")
        if self.drop_include_energy.isChecked():
            columns.append("Energy (ft-lbs)")
        if self.drop_include_tof.isChecked():
            columns.append("TOF (s)")

        self.drop_table.setColumnCount(len(columns))
        self.drop_table.setHorizontalHeaderLabels(columns)
        self.drop_table.setRowCount(len(distances))

        # Beregn for hver distanse
        for idx, distance in enumerate(distances):
            # Drop
            drop_cm = self.ballistics_calc.calculate_drop(
                velocity,
                float(bc),
                distance,
                zero,
                drag_model,
                density_ratio=environment.density_ratio(),
            )

            value = self._convert_drop_value(drop_cm, distance, unit, self.ballistics_calc)

            self.drop_table.setItem(idx, 0, QTableWidgetItem(str(distance)))
            self.drop_table.setItem(idx, 1, QTableWidgetItem(f"{value:.2f}"))

            col_idx = 2

            # Velocity
            if self.drop_include_velocity.isChecked():
                vel = self.ballistics_calc.calculate_velocity_at_distance(
                    velocity,
                    float(bc),
                    distance,
                    drag_model,
                    density_ratio=environment.density_ratio(),
                )
                self.drop_table.setItem(idx, col_idx, QTableWidgetItem(f"{vel:.0f}"))
                col_idx += 1

            # Energy
            if self.drop_include_energy.isChecked():
                vel = self.ballistics_calc.calculate_velocity_at_distance(
                    velocity,
                    float(bc),
                    distance,
                    drag_model,
                    density_ratio=environment.density_ratio(),
                )
                energy = self.ballistics_calc.calculate_energy(vel, weight)
                self.drop_table.setItem(idx, col_idx, QTableWidgetItem(f"{energy:.0f}"))
                col_idx += 1

            # Time of Flight
            if self.drop_include_tof.isChecked():
                tof = estimate_time_of_flight_seconds(
                    float(velocity),
                    float(bc),
                    float(distance),
                    drag_model,
                    density_ratio=environment.density_ratio(),
                )
                self.drop_table.setItem(idx, col_idx, QTableWidgetItem(f"{tof:.2f}"))

        self.drop_table.resizeColumnsToContents()

        QMessageBox.information(
            self,
            tr("common_done_title"),
            tr(
                "drop_chart_generated_message",
                name=name,
                drag_model=drag_model,
                count=len(distances),
                start=start,
                end=end,
                density_altitude=f"{environment.density_altitude_m():.0f}",
            ),
        )

    def calculate_wind_drift(self):
        """Beregner wind drift"""
        ammo_id = self.wind_ammo.currentData()
        if not ammo_id:
            QMessageBox.warning(
                self,
                tr("common_missing_data_title"),
                tr("drop_chart_select_ammo_warning"),
            )
            return

        ammo_row = self._get_ammo_profile_row(ammo_id)
        if not ammo_row:
            return

        name, velocity, bc_g1, bc_g7, bc_segments_json, weight, caliber = ammo_row
        drag_resolution = self._resolve_drag_model(
            bc_g1,
            bc_g7,
            (self.drop_drag_model.currentData() if hasattr(self, "drop_drag_model") else "AUTO"),
            bc_segments_json,
            velocity,
        )
        drag_model = str(drag_resolution["resolved_model"])
        bc = drag_resolution["bc_value"]
        segment_label = self._format_segment_match(drag_resolution.get("segment_match"), drag_model)
        environment = _build_environment(
            self.drop_temp.value(),
            self.drop_pressure.value(),
            self.drop_humidity.value(),
            self.drop_altitude.value(),
        )
        if not bc:
            self._warn_missing_bc()
            return

        distance = self.wind_distance.value()
        wind_speeds = [
            self.wind_speed_1.value(),
            self.wind_speed_2.value(),
            self.wind_speed_3.value(),
        ]
        wind_angle = self.wind_angle.value()

        # Wind value factor
        angle_rad = math.radians(wind_angle)
        wind_factor = abs(math.sin(angle_rad))  # 0° = 0, 90° = 1

        # Beregn wind drift for hver hastighet
        segmented_bc_line = f"{tr('drop_chart_segmented_bc_line', value=segment_label)}<br>" if segment_label else ""
        results_html = f"""
<h2>{tr("drop_chart_wind_result_title")}</h2>

<h3>{tr("drop_chart_ammo_section_title")}</h3>
<p><b>{name}</b> ({caliber})<br>
{tr("drop_chart_wind_ammo_line", velocity=velocity, drag_model=drag_model, bc=bc, weight=weight)}<br>
{segmented_bc_line}</p>

<h3>{tr("drop_chart_scenario_title")}</h3>
<p>{tr("drop_chart_scenario_distance_line", distance=distance)}<br>
{tr("drop_chart_scenario_angle_line", angle=wind_angle, description=self.get_wind_description(wind_angle))}<br>
{tr("drop_chart_wind_value_factor_line", value=f"{wind_factor:.2f}")}<br>
{tr("drop_chart_environment_basis_user_html")}<br>
{tr("drop_chart_density_altitude_html", meters=f"{environment.density_altitude_m():.0f}")}</p>

<h3>{tr("drop_chart_drift_calculations_title")}</h3>
<table style='width: 100%; border: 1px solid #ddd;'>
<tr style='background-color: #f0f0f0;'><th>{tr("drop_chart_wind_speed_col")}</th><th>{tr("drop_chart_drift_cm_col")}</th><th>{tr("drop_chart_drift_moa_col")}</th><th>{tr("drop_chart_drift_mrad_col")}</th></tr>
"""

        for wind_speed in wind_speeds:
            drift_cm = estimate_wind_drift_cm(
                float(velocity),
                float(bc),
                float(distance),
                float(wind_speed),
                float(wind_angle),
                drag_model,
                density_ratio=environment.density_ratio(),
            )
            drift_moa = self.ballistics_calc.cm_to_moa(drift_cm, distance)
            drift_mrad = self.ballistics_calc.cm_to_mrad(drift_cm, distance)

            results_html += f"""
<tr>
<td>{wind_speed:.1f} m/s</td>
<td>{drift_cm:.1f} cm</td>
<td>{drift_moa:.2f} MOA</td>
<td>{drift_mrad:.2f} MRAD</td>
</tr>
"""

        results_html += f"""
</table>

<h3>{tr("drop_chart_practical_tips_title")}</h3>
<ul>
<li>{tr("drop_chart_tip_clock_method")}</li>
<li>{tr("drop_chart_tip_full_value")}</li>
<li>{tr("drop_chart_tip_half_value")}</li>
<li>{tr("drop_chart_tip_head_tail")}</li>
</ul>

<h3>{tr("drop_chart_holdover_example_title")}</h3>
<p>{tr("drop_chart_holdover_example_intro", wind_speed=f"{wind_speeds[1]:.1f}", distance=distance)}<br>
<b>{tr("drop_chart_holdover_example_value", drift_cm=f"{drift_cm:.0f}", drift_moa=f"{drift_moa:.1f}", drift_mrad=f"{drift_mrad:.2f}")}</b></p>
        """

        self.wind_result.setHtml(results_html)

    def get_wind_description(self, angle):
        """Gir beskrivelse av vindvinkel"""
        if angle == 0:
            return tr("drop_chart_wind_desc_head_tail")
        elif angle < 30:
            return tr("drop_chart_wind_desc_slight")
        elif angle < 60:
            return tr("drop_chart_wind_desc_half")
        elif angle < 120:
            return tr("drop_chart_wind_desc_full")
        elif angle < 150:
            return tr("drop_chart_wind_desc_half")
        else:
            return tr("drop_chart_wind_desc_slight")

    def generate_dope_card(self):
        """Genererer DOPE card"""
        ammo_id = self.dope_ammo.currentData()
        if not ammo_id:
            QMessageBox.warning(
                self,
                tr("common_missing_data_title"),
                tr("drop_chart_select_ammo_warning"),
            )
            return

        ammo_row = self._get_ammo_profile_row(ammo_id)
        if not ammo_row:
            return

        name, velocity, bc_g1, bc_g7, bc_segments_json, weight, caliber = ammo_row
        drag_resolution = self._resolve_drag_model(
            bc_g1,
            bc_g7,
            (self.drop_drag_model.currentData() if hasattr(self, "drop_drag_model") else "AUTO"),
            bc_segments_json,
            velocity,
        )
        drag_model = str(drag_resolution["resolved_model"])
        bc = drag_resolution["bc_value"]
        segment_label = self._format_segment_match(drag_resolution.get("segment_match"), drag_model)
        environment = _build_environment(
            self.drop_temp.value(),
            self.drop_pressure.value(),
            self.drop_humidity.value(),
            self.drop_altitude.value(),
        )
        if not bc:
            self._warn_missing_bc()
            return
        zero = self.dope_zero.value()

        rifle_name = self.dope_rifle.text() or tr("common_not_specified")
        scope_name = self.dope_scope.text() or tr("common_not_specified")
        dope_html = f"""
<div style='border: 2px solid black; padding: 20px; font-family: monospace;'>
<h1 style='text-align: center;'>{tr("dope_card_title")}</h1>
<hr>

<h2>{tr("dope_card_setup_title")}</h2>
<table style='width: 100%;'>
<tr><td><b>{tr("ballistics_rifle_label")}</b></td><td>{rifle_name}</td></tr>
<tr><td><b>{tr("common_optic")}</b></td><td>{scope_name}</td></tr>
<tr><td><b>{tr("common_ammunition")}:</b></td><td>{name} ({caliber})</td></tr>
<tr><td><b>{tr("zero_shift_velocity_label")}:</b></td><td>{velocity} fps</td></tr>
<tr><td><b>BC ({drag_model}):</b></td><td>{bc}</td></tr>
<tr><td><b>{tr("zero_shift_segmented_bc")}:</b></td><td>{segment_label or '-'}</td></tr>
<tr><td><b>{tr("zero_shift_weight_label")}:</b></td><td>{weight} grains</td></tr>
<tr><td><b>{tr("common_zero")}</b></td><td>{zero}m</td></tr>
<tr><td><b>{tr("common_environment")}</b></td><td>{tr("drop_chart_environment_basis_user_plain")}</td></tr>
<tr><td><b>{tr("drop_chart_density_altitude_label")}</b></td><td>{environment.density_altitude_m():.0f} m / {environment.density_altitude_ft():.0f} ft</td></tr>
<tr><td><b>{tr("common_date")}:</b></td><td>{datetime.now().strftime('%Y-%m-%d')}</td></tr>
</table>

<h2>{tr("dope_card_drop_chart_title")}</h2>
<table style='width: 100%; border: 1px solid black; border-collapse: collapse;'>
<tr style='background-color: #ccc;'><th>{tr("dope_card_dist_col")}</th><th>{tr("dope_card_drop_col")}</th><th>{tr("dope_card_vel_col")}</th><th>{tr("dope_card_energy_col")}</th></tr>
"""

        # Generer kompakt tabell
        for distance in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
            drop_cm = self.ballistics_calc.calculate_drop(
                velocity,
                float(bc),
                distance,
                zero,
                drag_model,
                density_ratio=environment.density_ratio(),
            )
            drop_moa = self.ballistics_calc.cm_to_moa(drop_cm, distance)
            vel = self.ballistics_calc.calculate_velocity_at_distance(
                velocity,
                float(bc),
                distance,
                drag_model,
                density_ratio=environment.density_ratio(),
            )
            energy = self.ballistics_calc.calculate_energy(vel, weight)

            dope_html += f"""
<tr style='border: 1px solid #999;'>
<td style='padding: 5px;'>{distance}</td>
<td style='padding: 5px;'><b>{drop_moa:.1f}</b></td>
<td style='padding: 5px;'>{vel:.0f}</td>
<td style='padding: 5px;'>{energy:.0f}</td>
</tr>
"""

        dope_html += f"""
</table>

<h2>{tr("dope_card_wind_title")}</h2>
<table style='width: 100%; border: 1px solid black; border-collapse: collapse;'>
<tr style='background-color: #ccc;'><th>{tr("dope_card_dist_col")}</th><th>{tr("dope_card_drift_col")}</th><th>{tr("dope_card_drift_moa_col")}</th></tr>
"""

        # Wind drift tabell
        for distance in [100, 200, 300, 400, 500, 600, 700, 800]:
            drift_cm = estimate_wind_drift_cm(
                float(velocity),
                float(bc),
                float(distance),
                5.0,
                90.0,
                drag_model,
                density_ratio=environment.density_ratio(),
            )
            drift_moa = self.ballistics_calc.cm_to_moa(drift_cm, distance)

            dope_html += f"""
<tr style='border: 1px solid #999;'>
<td style='padding: 5px;'>{distance}</td>
<td style='padding: 5px;'>{drift_cm:.0f}</td>
<td style='padding: 5px;'><b>{drift_moa:.1f}</b></td>
</tr>
"""

        dope_html += f"""
</table>

<h3>{tr("common_notes")}:</h3>
<p>_________________________________________________________________</p>
<p>_________________________________________________________________</p>
<p>_________________________________________________________________</p>

<p style='text-align: center; font-size: 10pt;'><i>{tr("dope_card_generated_by")}</i></p>
</div>
"""

        self.dope_preview.setHtml(dope_html)

        QMessageBox.information(
            self,
            tr("common_done_title"),
            tr("dope_card_generated_message"),
        )

    def export_drop_chart(self, format_type):
        """Eksporterer drop chart"""
        if self.drop_table.rowCount() == 0:
            QMessageBox.warning(
                self,
                tr("common_no_data_title"),
                tr("drop_chart_generate_first_warning"),
            )
            return

        if format_type == "csv":
            filename, _ = QFileDialog.getSaveFileName(
                self,
                tr("drop_chart_save_dialog_title"),
                "",
                tr("drop_chart_csv_file_filter"),
            )

            if filename:
                with open(filename, "w") as f:
                    # Header
                    headers = []
                    for col in range(self.drop_table.columnCount()):
                        headers.append(self.drop_table.horizontalHeaderItem(col).text())
                    f.write(",".join(headers) + "\n")

                    # Data
                    for row in range(self.drop_table.rowCount()):
                        row_data = []
                        for col in range(self.drop_table.columnCount()):
                            item = self.drop_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        f.write(",".join(row_data) + "\n")

                QMessageBox.information(
                    self,
                    tr("common_saved_title"),
                    tr("drop_chart_saved_message", filename=filename),
                )

        elif format_type == "pdf":
            QMessageBox.information(
                self,
                tr("common_pdf_export_title"),
                tr("drop_chart_pdf_export_pending"),
            )

    def export_dope_pdf(self):
        """Eksporterer DOPE card til PDF"""
        QMessageBox.information(
            self,
            tr("common_pdf_export_title"),
            tr("dope_card_pdf_export_pending"),
        )

    def print_drop_chart(self):
        """Printer drop chart"""
        QMessageBox.information(
            self,
            tr("common_print"),
            tr("drop_chart_print_pending"),
        )


class ReloadingSimulatorUI(QWidget):
    """UI for tilpasset visning av anslagsenergi, rekyl og simulering"""

    def __init__(self, ballistics_calc, language="en"):
        super().__init__()
        self.ballistics_calc = ballistics_calc
        self.language = language
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        title = QLabel(tr("reloading_sim_title", self.language))
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        # Valg for visning
        self.energy_checkbox = QCheckBox(tr("show_energy", self.language))
        self.recoil_checkbox = QCheckBox(tr("show_recoil", self.language))
        self.sim_checkbox = QCheckBox(tr("show_simulation", self.language))
        layout.addWidget(self.energy_checkbox)
        layout.addWidget(self.recoil_checkbox)
        layout.addWidget(self.sim_checkbox)
        # Input-felter
        self.bullet_weight_input = QDoubleSpinBox()
        self.bullet_weight_input.setSuffix(" gr")
        self.bullet_weight_input.setRange(1, 1000)
        self.velocity_input = QDoubleSpinBox()
        self.velocity_input.setSuffix(" m/s")
        self.velocity_input.setRange(100, 1500)
        self.powder_weight_input = QDoubleSpinBox()
        self.powder_weight_input.setSuffix(" gr")
        self.powder_weight_input.setRange(1, 200)
        self.weapon_weight_input = QDoubleSpinBox()
        self.weapon_weight_input.setSuffix(" kg")
        self.weapon_weight_input.setRange(1, 20)
        layout.addWidget(QLabel(tr("bullet_weight", self.language)))
        layout.addWidget(self.bullet_weight_input)
        layout.addWidget(QLabel(tr("velocity", self.language)))
        layout.addWidget(self.velocity_input)
        layout.addWidget(QLabel(tr("powder_weight", self.language)))
        layout.addWidget(self.powder_weight_input)
        layout.addWidget(QLabel(tr("weapon_weight", self.language)))
        layout.addWidget(self.weapon_weight_input)
        # Simuleringsknapp
        sim_btn = QPushButton(tr("simulate", self.language))
        sim_btn.clicked.connect(self.run_simulation)
        layout.addWidget(sim_btn)
        # Resultatvisning
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

    def run_simulation(self):
        bw = self.bullet_weight_input.value() * 0.0648  # grains til gram
        v = self.velocity_input.value()
        pw = self.powder_weight_input.value() * 0.0648
        ww = self.weapon_weight_input.value() * 1000  # kg til gram
        results = []
        if self.energy_checkbox.isChecked():
            energy = 0.5 * bw * v**2
            results.append(f"{tr('energy', self.language)}: {energy:.1f} J")
        if self.recoil_checkbox.isChecked():
            recoil = (bw + pw) * v / ww
            results.append(f"{tr('recoil', self.language)}: {recoil:.2f} J")
        if self.sim_checkbox.isChecked():
            sim = [f"{d}m: {0.5 * bw * v ** 2:.1f} J" for d in [100, 200, 300, 400]]
            results.append(tr("simulation", self.language) + ":\n" + "\n".join(sim))
        self.result_text.setText("\n".join(results))
