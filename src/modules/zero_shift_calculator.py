"""
Zero Shift Calculator - Widget
Calculates optic adjustments when switching ammunition
"""

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.ballistics import BallisticData, BallisticsCalculator
from ..utils.drag_models import resolve_drag_choice
from ..utils.environment import BallisticEnvironment
from ..utils.i18n import tr


def _preferred_drag_model() -> str:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return (
        str(settings.value("ballistics/drag_model", "AUTO") or "AUTO").strip().upper()
    )


def _zero_shift_bc_label() -> str:
    preferred = _preferred_drag_model()
    if preferred == "G7":
        return "BC (G7):"
    if preferred == "AUTO":
        return "BC (Auto/G7):"
    return "BC (G1):"


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


def _format_segment_match(
    segment_match: dict[str, object] | None, drag_model: str
) -> str:
    if not isinstance(segment_match, dict):
        return ""
    model = str(segment_match.get("model") or drag_model or "AUTO").strip().upper()
    if model == "AUTO":
        model = str(drag_model or "AUTO").strip().upper()
    bc_value = (
        segment_match.get("bc_g7")
        or segment_match.get("bc_g1")
        or segment_match.get("bc")
    )
    min_v = segment_match.get("velocity_fps_min")
    max_v = segment_match.get("velocity_fps_max")
    if bc_value is None:
        return ""
    if max_v is not None:
        return (
            f"{model} {float(bc_value):.3f} @ "
            f"{float(min_v or 0):.0f}-{float(max_v):.0f} fps"
        )
    return f"{model} {float(bc_value):.3f} @ {float(min_v or 0):.0f}+ fps"


def _resolve_profile_drag(
    profile: dict | None, preferred_drag_model: str, velocity_fps: float | None
) -> tuple[str, float | None, str]:
    if not profile:
        drag_model = "G7" if preferred_drag_model == "G7" else "G1"
        return drag_model, None, ""
    resolved = resolve_drag_choice(
        profile.get("bc_g1"),
        profile.get("bc_g7"),
        preferred_drag_model,
        profile.get("bc_segments_json"),
        velocity_fps=velocity_fps,
    )
    drag_model = str(resolved.get("resolved_model") or "G1")
    return (
        drag_model,
        resolved.get("bc_value"),
        _format_segment_match(resolved.get("segment_match"), drag_model),
    )


class ZeroShiftCalculator(QWidget):
    """Widget for zero-shift calculations."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.calc = BallisticsCalculator()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel(tr("zero_shift_title"))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(tr("zero_shift_desc"))
        layout.addWidget(desc)

        # Main content in a horizontal layout
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)

        # Left side - Input
        left_widget = self.create_input_section()
        main_layout.addWidget(left_widget, 1)

        # Right side - Results
        right_widget = self.create_result_section()
        main_layout.addWidget(right_widget, 1)

        self.load_optics()
        self.load_ammo_profiles()

    def create_input_section(self):
        """Create the input section."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Ammunition 1 (zeroed with)
        ammo1_group = QGroupBox(tr("zero_shift_ammo1"))
        ammo1_layout = QVBoxLayout()
        ammo1_group.setLayout(ammo1_layout)

        # Profile dropdown
        ammo1_layout.addWidget(QLabel(tr("zero_shift_select_profile")))
        self.ammo1_combo = QComboBox()
        self.ammo1_combo.addItem(tr("zero_shift_manual_input"))
        self.ammo1_combo.currentIndexChanged.connect(self.on_ammo1_selected)
        ammo1_layout.addWidget(self.ammo1_combo)

        # Manual fields
        ammo1_layout.addWidget(QLabel(tr("zero_shift_velocity")))
        self.ammo1_velocity = QSpinBox()
        self.ammo1_velocity.setRange(1000, 4000)
        self.ammo1_velocity.setValue(2700)
        self.ammo1_velocity.setSuffix(" fps")
        ammo1_layout.addWidget(self.ammo1_velocity)

        ammo1_layout.addWidget(QLabel(_zero_shift_bc_label()))
        self.ammo1_bc = QDoubleSpinBox()
        self.ammo1_bc.setRange(0.1, 1.0)
        self.ammo1_bc.setValue(0.450)
        self.ammo1_bc.setDecimals(3)
        self.ammo1_bc.setSingleStep(0.001)
        ammo1_layout.addWidget(self.ammo1_bc)

        ammo1_layout.addWidget(QLabel(tr("zero_shift_weight")))
        self.ammo1_weight = QSpinBox()
        self.ammo1_weight.setRange(40, 300)
        self.ammo1_weight.setValue(140)
        self.ammo1_weight.setSuffix(" gr")
        ammo1_layout.addWidget(self.ammo1_weight)

        ammo1_layout.addWidget(QLabel(tr("zero_shift_zero_distance")))
        self.ammo1_zero = QSpinBox()
        self.ammo1_zero.setRange(25, 500)
        self.ammo1_zero.setValue(100)
        self.ammo1_zero.setSuffix(" m")
        ammo1_layout.addWidget(self.ammo1_zero)

        layout.addWidget(ammo1_group)

        # Ammunition 2 (switching to)
        ammo2_group = QGroupBox(tr("zero_shift_ammo2"))
        ammo2_layout = QVBoxLayout()
        ammo2_group.setLayout(ammo2_layout)

        ammo2_layout.addWidget(QLabel(tr("zero_shift_select_profile")))
        self.ammo2_combo = QComboBox()
        self.ammo2_combo.addItem(tr("zero_shift_manual_input"))
        self.ammo2_combo.currentIndexChanged.connect(self.on_ammo2_selected)
        ammo2_layout.addWidget(self.ammo2_combo)

        ammo2_layout.addWidget(QLabel(tr("zero_shift_velocity")))
        self.ammo2_velocity = QSpinBox()
        self.ammo2_velocity.setRange(1000, 4000)
        self.ammo2_velocity.setValue(2620)
        self.ammo2_velocity.setSuffix(" fps")
        ammo2_layout.addWidget(self.ammo2_velocity)

        ammo2_layout.addWidget(QLabel(_zero_shift_bc_label()))
        self.ammo2_bc = QDoubleSpinBox()
        self.ammo2_bc.setRange(0.1, 1.0)
        self.ammo2_bc.setValue(0.497)
        self.ammo2_bc.setDecimals(3)
        self.ammo2_bc.setSingleStep(0.001)
        ammo2_layout.addWidget(self.ammo2_bc)

        ammo2_layout.addWidget(QLabel(tr("zero_shift_weight")))
        self.ammo2_weight = QSpinBox()
        self.ammo2_weight.setRange(40, 300)
        self.ammo2_weight.setValue(147)
        self.ammo2_weight.setSuffix(" gr")
        ammo2_layout.addWidget(self.ammo2_weight)

        ammo2_layout.addWidget(QLabel(tr("zero_shift_zero_distance")))
        self.ammo2_zero = QSpinBox()
        self.ammo2_zero.setRange(25, 500)
        self.ammo2_zero.setValue(100)
        self.ammo2_zero.setSuffix(" m")
        ammo2_layout.addWidget(self.ammo2_zero)

        layout.addWidget(ammo2_group)

        # Optic settings
        optic_group = QGroupBox(tr("zero_shift_optic_settings"))
        optic_layout = QVBoxLayout()
        optic_group.setLayout(optic_layout)

        optic_layout.addWidget(QLabel(tr("zero_shift_select_optic")))
        self.optic_combo = QComboBox()
        self.optic_combo.addItem(tr("zero_shift_manual_input"))
        self.optic_combo.currentTextChanged.connect(self.on_optic_selected)
        optic_layout.addWidget(self.optic_combo)

        optic_layout.addWidget(QLabel(tr("zero_shift_click_value")))
        h_layout = QHBoxLayout()
        self.click_value = QDoubleSpinBox()
        self.click_value.setRange(0.01, 1.0)
        self.click_value.setValue(0.25)
        self.click_value.setDecimals(2)
        self.click_value.setSingleStep(0.01)
        h_layout.addWidget(self.click_value)

        self.click_unit = QComboBox()
        self.click_unit.addItems(["MOA", "MRAD"])
        h_layout.addWidget(self.click_unit)
        optic_layout.addLayout(h_layout)

        optic_layout.addWidget(QLabel(tr("zero_shift_shooting_distance")))
        self.shooting_distance = QSpinBox()
        self.shooting_distance.setRange(50, 1000)
        self.shooting_distance.setValue(300)
        self.shooting_distance.setSuffix(" m")
        optic_layout.addWidget(self.shooting_distance)

        optic_layout.addWidget(QLabel(tr("common_temperature")))
        self.env_temp = QDoubleSpinBox()
        self.env_temp.setRange(-40.0, 60.0)
        self.env_temp.setValue(15.0)
        self.env_temp.setSuffix(" °C")
        optic_layout.addWidget(self.env_temp)

        optic_layout.addWidget(QLabel(tr("common_pressure")))
        self.env_pressure = QDoubleSpinBox()
        self.env_pressure.setRange(800.0, 1100.0)
        self.env_pressure.setValue(1013.25)
        self.env_pressure.setDecimals(2)
        self.env_pressure.setSuffix(" hPa")
        optic_layout.addWidget(self.env_pressure)

        optic_layout.addWidget(QLabel(tr("common_humidity")))
        self.env_humidity = QSpinBox()
        self.env_humidity.setRange(0, 100)
        self.env_humidity.setValue(50)
        self.env_humidity.setSuffix(" %")
        optic_layout.addWidget(self.env_humidity)

        optic_layout.addWidget(QLabel(tr("common_altitude")))
        self.env_altitude = QSpinBox()
        self.env_altitude.setRange(-500, 5000)
        self.env_altitude.setValue(0)
        self.env_altitude.setSuffix(" m")
        optic_layout.addWidget(self.env_altitude)

        layout.addWidget(optic_group)

        # Calculate button
        calculate_btn = QPushButton(tr("zero_shift_calculate"))
        calculate_btn.setMinimumHeight(50)
        calculate_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        calculate_btn.clicked.connect(self.calculate_adjustment)
        layout.addWidget(calculate_btn)

        layout.addStretch()

        return widget

    def create_result_section(self):
        """Create the results section."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Main result
        result_group = QGroupBox(tr("zero_shift_result_group"))
        result_layout = QVBoxLayout()
        result_group.setLayout(result_layout)

        self.result_label = QLabel()
        self.result_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            """
            QLabel {
                padding: 20px;
                background-color: #E3F2FD;
                border-radius: 5px;
                border: 2px solid #2196F3;
            }
        """
        )
        self.result_label.setText(tr("zero_shift_result_placeholder"))
        result_layout.addWidget(self.result_label)

        layout.addWidget(result_group)

        # Details
        details_group = QGroupBox(tr("zero_shift_details_group"))
        details_layout = QVBoxLayout()
        details_group.setLayout(details_layout)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)

        layout.addWidget(details_group)

        # Table with multiple distances
        table_group = QGroupBox(tr("zero_shift_distances_group"))
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.distance_table = QTableWidget()
        self.distance_table.setColumnCount(4)
        self.distance_table.setHorizontalHeaderLabels(
            [
                tr("zero_shift_col_distance"),
                tr("zero_shift_col_difference"),
                tr("zero_shift_col_adjustment"),
                tr("zero_shift_col_clicks"),
            ]
        )
        self.distance_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        table_layout.addWidget(self.distance_table)

        layout.addWidget(table_group)

        return widget

    def on_optic_selected(self, text):
        """Handle optic selection."""
        optic_id = self.optic_combo.currentData()
        if not optic_id:
            return

        optic = self.db.get_by_id("optics", optic_id)
        if not optic:
            return

        click_value = optic.get("click_value_elevation")
        if click_value:
            self.click_value.setValue(float(click_value))

        click_unit = optic.get("click_unit")
        if click_unit:
            index = self.click_unit.findText(click_unit)
            if index >= 0:
                self.click_unit.setCurrentIndex(index)

        zero_distance = optic.get("zero_distance")
        if zero_distance:
            self.ammo1_zero.setValue(int(zero_distance))
            self.ammo2_zero.setValue(int(zero_distance))

    def _format_ammo_profile_label(self, profile: dict) -> str:
        name = str(profile.get("name") or "").strip()
        caliber = str(profile.get("caliber") or "").strip()
        velocity = profile.get("velocity_fps")
        parts = [part for part in [name, caliber] if part]
        label = " | ".join(parts) if parts else tr("zero_shift_manual_input")
        if velocity:
            label = f"{label} ({float(velocity):.0f} fps)"
        return label

    def _apply_ammo_profile(self, profile: dict | None, *, side: str) -> None:
        if not profile:
            return
        velocity_widget = (
            self.ammo1_velocity if side == "ammo1" else self.ammo2_velocity
        )
        bc_widget = self.ammo1_bc if side == "ammo1" else self.ammo2_bc
        weight_widget = self.ammo1_weight if side == "ammo1" else self.ammo2_weight
        zero_widget = self.ammo1_zero if side == "ammo1" else self.ammo2_zero

        velocity = profile.get("velocity_fps")
        if velocity:
            velocity_widget.setValue(int(round(float(velocity))))

        drag_model, bc_value, _segment_label = _resolve_profile_drag(
            profile,
            _preferred_drag_model(),
            velocity_widget.value(),
        )
        if isinstance(bc_value, (int, float)):
            bc_widget.setValue(float(bc_value))
        elif drag_model == "G7" and profile.get("bc_g7"):
            bc_widget.setValue(float(profile["bc_g7"]))
        elif profile.get("bc_g1"):
            bc_widget.setValue(float(profile["bc_g1"]))

        weight = profile.get("bullet_weight")
        if weight:
            weight_widget.setValue(int(round(float(weight))))

        zero_distance = profile.get("zero_distance")
        if zero_distance:
            zero_widget.setValue(int(round(float(zero_distance))))

    def on_ammo1_selected(self, _index: int) -> None:
        profile = self.ammo1_combo.currentData()
        if isinstance(profile, dict):
            self._apply_ammo_profile(profile, side="ammo1")

    def on_ammo2_selected(self, _index: int) -> None:
        profile = self.ammo2_combo.currentData()
        if isinstance(profile, dict):
            self._apply_ammo_profile(profile, side="ammo2")

    def load_optics(self):
        """Load optics from the database."""
        self.optic_combo.blockSignals(True)
        self.optic_combo.clear()
        self.optic_combo.addItem(tr("zero_shift_manual_input"), None)

        optics = self.db.get_all("optics", "name")
        for optic in optics:
            name = optic.get("name", "")
            manufacturer = optic.get("manufacturer") or ""
            label = f"{manufacturer} {name}".strip()
            click_value = optic.get("click_value_elevation")
            click_unit = optic.get("click_unit") or ""
            zero_distance = optic.get("zero_distance") or 100
            if click_value:
                label = f"{label} ({click_value} {click_unit}, {zero_distance}m)"
            self.optic_combo.addItem(label, optic.get("id"))

        self.optic_combo.blockSignals(False)

    def load_ammo_profiles(self):
        """Load ammunition profiles from the database."""
        profiles = self.db.get_ammo_profiles_for_rifle()
        for combo in (self.ammo1_combo, self.ammo2_combo):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(tr("zero_shift_manual_input"), None)
            for profile in profiles:
                combo.addItem(self._format_ammo_profile_label(profile), profile)
            combo.blockSignals(False)

    def calculate_adjustment(self):
        """Calculate the required adjustment."""
        preferred_drag_model = _preferred_drag_model()
        environment = _build_environment(
            self.env_temp.value(),
            self.env_pressure.value(),
            self.env_humidity.value(),
            self.env_altitude.value(),
        )
        ammo1_profile = self.ammo1_combo.currentData()
        ammo2_profile = self.ammo2_combo.currentData()
        ammo1_drag_model, ammo1_bc_resolved, ammo1_segment = _resolve_profile_drag(
            ammo1_profile if isinstance(ammo1_profile, dict) else None,
            preferred_drag_model,
            self.ammo1_velocity.value(),
        )
        ammo2_drag_model, ammo2_bc_resolved, ammo2_segment = _resolve_profile_drag(
            ammo2_profile if isinstance(ammo2_profile, dict) else None,
            preferred_drag_model,
            self.ammo2_velocity.value(),
        )
        # Hent data fra inputs
        ammo1 = BallisticData(
            velocity=self.ammo1_velocity.value(),
            bc=(
                float(ammo1_bc_resolved)
                if isinstance(ammo1_bc_resolved, (int, float))
                else self.ammo1_bc.value()
            ),
            weight=self.ammo1_weight.value(),
            zero_distance=self.ammo1_zero.value(),
            bc_type=ammo1_drag_model,
        )

        ammo2 = BallisticData(
            velocity=self.ammo2_velocity.value(),
            bc=(
                float(ammo2_bc_resolved)
                if isinstance(ammo2_bc_resolved, (int, float))
                else self.ammo2_bc.value()
            ),
            weight=self.ammo2_weight.value(),
            zero_distance=self.ammo2_zero.value(),
            bc_type=ammo2_drag_model,
        )

        distance = self.shooting_distance.value()
        click_value = self.click_value.value()
        click_unit = self.click_unit.currentText()

        # Beregn zero shift
        shift = self.calc.calculate_zero_shift(
            ammo1, ammo2, distance, density_ratio=environment.density_ratio()
        )

        # Finn riktig justering basert på enhet
        if click_unit == "MOA":
            adjustment_value = shift["difference_moa"]
        else:
            adjustment_value = shift["difference_mrad"]

        # Beregn klikk
        clicks = self.calc.calculate_clicks(adjustment_value, click_value, click_unit)

        # Retning
        if clicks > 0:
            direction = tr("zero_shift_direction_up")
            color = "#4CAF50"
        elif clicks < 0:
            direction = tr("zero_shift_direction_down")
            color = "#F44336"
            clicks = abs(clicks)
        else:
            direction = tr("zero_shift_direction_none")
            color = "#2196F3"

        # Vis hovedresultat
        result_text = f"""
        <div style='text-align: center;'>
            <h2 style='color: {color}; margin: 5px;'>{tr("zero_shift_clicks_line", clicks=clicks, direction=direction)}</h2>
            <p style='font-size: 12px; margin: 5px;'>
                {tr("zero_shift_adjustment_at_distance", value=f"{adjustment_value:.2f}", unit=click_unit, distance=distance)}
            </p>
        </div>
        """
        self.result_label.setText(result_text)

        # Vis detaljer
        ammo1_segment_line = (
            f"  • {tr('zero_shift_segmented_bc')}: {ammo1_segment}\n"
            if ammo1_segment
            else ""
        )
        ammo2_segment_line = (
            f"  • {tr('zero_shift_segmented_bc')}: {ammo2_segment}\n"
            if ammo2_segment
            else ""
        )
        details = f"""
<b>{tr("zero_shift_detailed_analysis")}:</b>

<b>{tr("zero_shift_ammo1_label")}:</b>
  • {tr("zero_shift_velocity_label")}: {ammo1.velocity} fps
  • BC ({ammo1.bc_type}): {ammo1.bc}
{ammo1_segment_line}  • {tr("zero_shift_weight_label")}: {ammo1.weight} grains
  • {tr("zero_shift_drop_at_distance", distance=distance)}: {shift['drop_ammo1_cm']:.1f} cm

<b>{tr("zero_shift_ammo2_label")}:</b>
  • {tr("zero_shift_velocity_label")}: {ammo2.velocity} fps
  • BC ({ammo2.bc_type}): {ammo2.bc}
{ammo2_segment_line}  • {tr("zero_shift_weight_label")}: {ammo2.weight} grains
  • {tr("zero_shift_drop_at_distance", distance=distance)}: {shift['drop_ammo2_cm']:.1f} cm

<b>{tr("zero_shift_difference_label")}:</b>
  • {shift['difference_cm']:.1f} cm
  • {shift['difference_moa']:.2f} MOA
  • {shift['difference_mrad']:.3f} MRAD

<b>{tr("zero_shift_recommendation_label")}:</b>
  {tr("zero_shift_active_drag_standard", value=preferred_drag_model)}
  {tr("zero_shift_environment_basis_user")}
  {tr("zero_shift_density_altitude_line", meters=f"{environment.density_altitude_m():.0f}", feet=f"{environment.density_altitude_ft():.0f}")}
  {tr("zero_shift_density_ratio_line", value=f"{environment.density_ratio():.3f}")}
  {tr("zero_shift_note_original_zero")}
  {tr("zero_shift_test_short_range")}
        """
        self.details_text.setText(details)

        # Generer tabell for flere avstander
        distances = [100, 200, 300, 400, 500]
        table_data = self.calc.generate_adjustment_table(
            ammo1,
            ammo2,
            distances,
            click_value,
            click_unit,
            density_ratio=environment.density_ratio(),
        )

        self.distance_table.setRowCount(len(table_data))
        for i, row in enumerate(table_data):
            self.distance_table.setItem(
                i, 0, QTableWidgetItem(f"{row['distance_m']} m")
            )
            self.distance_table.setItem(
                i, 1, QTableWidgetItem(f"{row['difference_cm']:.1f} cm")
            )
            self.distance_table.setItem(
                i, 2, QTableWidgetItem(f"{row['adjustment_value']:.2f} {click_unit}")
            )

            clicks_str = f"{abs(row['clicks'])} {row['direction']}"
            self.distance_table.setItem(i, 3, QTableWidgetItem(clicks_str))
