from PyQt6.QtWidgets import QApplication

from src.modules import zero_shift_calculator as zero_module
from src.utils.i18n import tr


def test_zero_shift_bc_label_uses_g7_when_preferred(monkeypatch):
    monkeypatch.setattr(zero_module, "_preferred_drag_model", lambda: "G7")

    assert zero_module._zero_shift_bc_label() == "BC (G7):"


def test_zero_shift_bc_label_uses_auto_hint_when_auto(monkeypatch):
    monkeypatch.setattr(zero_module, "_preferred_drag_model", lambda: "AUTO")

    assert zero_module._zero_shift_bc_label() == "BC (Auto/G7):"


def test_zero_shift_default_environment_uses_assumed_standard_atmosphere():
    environment = zero_module._default_environment()

    assert environment.temperature_source == "assumed"
    assert abs(environment.density_altitude_m()) < 100.0


def test_zero_shift_build_environment_marks_user_sources():
    environment = zero_module._build_environment(24.0, 950.0, 40.0, 1200.0)

    assert environment.pressure_source == "user"
    assert environment.density_altitude_m() > 0


def test_ballistics_density_ratio_changes_drop_and_shift():
    from src.utils.ballistics import BallisticData, BallisticsCalculator

    calc = BallisticsCalculator()
    standard_drop = calc.calculate_drop(
        2700.0, 0.45, 500.0, 100.0, "G1", density_ratio=1.0
    )
    thin_air_drop = calc.calculate_drop(
        2700.0, 0.45, 500.0, 100.0, "G1", density_ratio=0.85
    )

    assert thin_air_drop < standard_drop

    ammo1 = BallisticData(2700.0, 0.45, 140.0, 100.0, "G1")
    ammo2 = BallisticData(2620.0, 0.50, 147.0, 100.0, "G1")
    standard_shift = calc.calculate_zero_shift(ammo1, ammo2, 500.0, density_ratio=1.0)
    thin_air_shift = calc.calculate_zero_shift(ammo1, ammo2, 500.0, density_ratio=0.85)

    assert abs(thin_air_shift["difference_cm"]) < abs(standard_shift["difference_cm"])


def test_estimate_retained_velocity_uses_shared_ballistics_calculator():
    from src.utils.ballistics import (
        BallisticsCalculator,
        estimate_retained_velocity_fps,
    )

    calc = BallisticsCalculator()
    expected = round(
        calc.calculate_velocity_at_distance(
            2700.0, 0.315, 180.0, "G7", density_ratio=0.92
        ),
        1,
    )

    assert (
        estimate_retained_velocity_fps(2700.0, 180.0, 0.315, "G7", density_ratio=0.92)
        == expected
    )


def test_resolve_profile_drag_uses_segmented_bc_when_available():
    drag_model, bc_value, segment_label = zero_module._resolve_profile_drag(
        {
            "bc_g1": 0.462,
            "bc_g7": 0.235,
            "bc_segments_json": '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
        },
        "AUTO",
        2710.0,
    )

    assert drag_model == "G7"
    assert bc_value == 0.245
    assert segment_label == "G7 0.245 @ 2600-3000 fps"


def test_resolve_profile_drag_falls_back_to_requested_standard_without_profile():
    drag_model, bc_value, segment_label = zero_module._resolve_profile_drag(
        None,
        "G7",
        2700.0,
    )

    assert drag_model == "G7"
    assert bc_value is None
    assert segment_label == ""


def test_zero_shift_loads_ammo_profiles_and_applies_segmented_bc(monkeypatch):
    QApplication.instance() or QApplication([])

    class FakeDb:
        def get_ammo_profiles_for_rifle(self, rifle_id=None):
            return [
                {
                    "id": 7,
                    "name": "Match Load",
                    "caliber": ".308 Win",
                    "velocity_fps": 2710,
                    "bc_g1": 0.462,
                    "bc_g7": 0.235,
                    "bc_segments_json": '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
                    "bullet_weight": 175,
                    "zero_distance": 200,
                }
            ]

        def get_all(self, table, order_by=None):
            assert table == "optics"
            return []

        def get_by_id(self, table, record_id):
            return None

    monkeypatch.setattr(zero_module, "get_database", lambda: FakeDb())
    monkeypatch.setattr(zero_module, "_preferred_drag_model", lambda: "AUTO")

    widget = zero_module.ZeroShiftCalculator()
    try:
        assert widget.ammo1_combo.count() == 2
        assert "Match Load" in widget.ammo1_combo.itemText(1)

        widget.ammo1_combo.setCurrentIndex(1)

        assert widget.ammo1_velocity.value() == 2710
        assert widget.ammo1_bc.value() == 0.245
        assert widget.ammo1_weight.value() == 175
        assert widget.ammo1_zero.value() == 200
    finally:
        widget.close()


def test_zero_shift_environment_labels_have_translation_entries():
    assert tr("common_temperature") != "common_temperature"
    assert tr("common_pressure") != "common_pressure"
    assert tr("common_humidity") != "common_humidity"
    assert tr("common_altitude") != "common_altitude"


def test_zero_shift_detail_labels_have_translation_entries():
    assert tr("zero_shift_direction_up") != "zero_shift_direction_up"
    assert tr("zero_shift_detailed_analysis") != "zero_shift_detailed_analysis"
    assert (
        tr("zero_shift_active_drag_standard", value="AUTO")
        != "zero_shift_active_drag_standard"
    )
    assert (
        tr("zero_shift_clicks_line", clicks=3, direction="OPP ⬆")
        != "zero_shift_clicks_line"
    )
