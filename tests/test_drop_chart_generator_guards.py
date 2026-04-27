from types import SimpleNamespace

from src.modules import drop_chart_generator as drop_module
from src.utils.i18n import tr


class _MissingAmmoDb:
    def __init__(self):
        self.queries = []

    def execute_query(self, query, params=()):
        self.queries.append((query, params))
        return []


def test_get_ammo_profile_row_warns_when_profile_missing(monkeypatch):
    warnings = []
    fake_db = _MissingAmmoDb()
    monkeypatch.setattr(
        drop_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    widget = SimpleNamespace(db=fake_db)

    result = drop_module.DropChartGenerator._get_ammo_profile_row(widget, 55)

    assert result is None
    assert warnings
    assert fake_db.queries == [
        (
            "SELECT name, velocity_fps, bc_g1, bc_g7, bc_segments_json, bullet_weight, caliber FROM ammo_profiles WHERE id = ?",
            (55,),
        )
    ]


def test_convert_drop_value_uses_units_for_inches():
    value = drop_module.DropChartGenerator._convert_drop_value(
        2.54,
        100,
        "INCHES",
        SimpleNamespace(
            cm_to_moa=lambda drop, dist: 0.0,
            cm_to_mrad=lambda drop, dist: 0.0,
        ),
    )

    assert abs(value - 1.0) < 1e-9


def test_estimate_time_of_flight_seconds_uses_shared_ballistics_model():
    from src.utils.ballistics import estimate_time_of_flight_seconds

    tof = estimate_time_of_flight_seconds(1000.0, 0.3, 100.0, "G1", density_ratio=1.0)

    assert tof > (100 / 304.8)


def test_estimate_time_of_flight_seconds_changes_with_density_and_drag_model():
    from src.utils.ballistics import estimate_time_of_flight_seconds

    standard_g1 = estimate_time_of_flight_seconds(
        2700.0, 0.45, 500.0, "G1", density_ratio=1.0
    )
    thin_air_g1 = estimate_time_of_flight_seconds(
        2700.0, 0.45, 500.0, "G1", density_ratio=0.85
    )
    standard_g7 = estimate_time_of_flight_seconds(
        2700.0, 0.315, 500.0, "G7", density_ratio=1.0
    )

    assert thin_air_g1 < standard_g1
    assert standard_g7 != standard_g1


def test_resolve_drag_model_prefers_g7_in_auto_mode():
    result = drop_module.DropChartGenerator._resolve_drag_model(
        SimpleNamespace(),
        0.462,
        0.235,
        "AUTO",
    )

    assert result["resolved_model"] == "G7"
    assert result["bc_value"] == 0.235
    assert result["note_key"] == "drop_chart_drag_auto_g7"


def test_resolve_drag_model_falls_back_to_g1_when_g7_missing():
    result = drop_module.DropChartGenerator._resolve_drag_model(
        SimpleNamespace(),
        0.462,
        None,
        "G7",
    )

    assert result["resolved_model"] == "G1"
    assert result["bc_value"] == 0.462
    assert result["note_key"] == "drop_chart_drag_g7_missing"


def test_resolve_drag_model_uses_segmented_bc_when_velocity_matches():
    result = drop_module.DropChartGenerator._resolve_drag_model(
        SimpleNamespace(),
        0.462,
        0.235,
        "AUTO",
        '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
        2710.0,
    )

    assert result["resolved_model"] == "G7"
    assert result["bc_value"] == 0.245
    assert result["source"] == "bc_segments_g7"
    assert result["segment_match"] is not None


def test_drop_chart_default_environment_uses_assumed_standard_atmosphere():
    environment = drop_module._default_environment()

    assert environment.pressure_source == "assumed"
    assert abs(environment.density_altitude_m()) < 100.0


def test_drop_chart_build_environment_marks_user_sources():
    environment = drop_module._build_environment(5.0, 980.0, 70.0, 850.0)

    assert environment.temperature_source == "user"
    assert environment.altitude_source == "user"
    assert environment.density_altitude_m() > 0


def test_drop_chart_field_labels_have_translation_entries():
    assert tr("drop_chart_zero_distance") != "drop_chart_zero_distance"
    assert tr("drop_chart_distance_range") != "drop_chart_distance_range"
    assert tr("drop_chart_wind_1") != "drop_chart_wind_1"
    assert tr("common_environment") != "common_environment"
    assert tr("drop_chart_generate") != "drop_chart_generate"
    assert tr("dope_card_generate") != "dope_card_generate"
    assert tr("drop_chart_select_ammo_warning") != "drop_chart_select_ammo_warning"
    assert tr("drop_chart_pdf_export_pending") != "drop_chart_pdf_export_pending"
    assert tr("drop_chart_wind_result_title") != "drop_chart_wind_result_title"
    assert tr("dope_card_title") != "dope_card_title"
    assert tr("dope_card_rifle_placeholder") != "dope_card_rifle_placeholder"
    assert tr("drop_chart_profile_missing_title") != "drop_chart_profile_missing_title"


def test_estimate_wind_drift_cm_respects_wind_angle():
    from src.utils.ballistics import estimate_wind_drift_cm

    full_value = estimate_wind_drift_cm(2700.0, 0.315, 300.0, 4.0, 90.0, "G7")
    headwind = estimate_wind_drift_cm(2700.0, 0.315, 300.0, 4.0, 0.0, "G7")

    assert full_value > 0.0
    assert headwind == 0.0


def test_estimate_wind_drift_cm_changes_with_density_and_drag_model():
    from src.utils.ballistics import estimate_wind_drift_cm

    standard_g1 = estimate_wind_drift_cm(
        2700.0, 0.45, 500.0, 5.0, 90.0, "G1", density_ratio=1.0
    )
    thin_air_g1 = estimate_wind_drift_cm(
        2700.0, 0.45, 500.0, 5.0, 90.0, "G1", density_ratio=0.85
    )
    standard_g7 = estimate_wind_drift_cm(
        2700.0, 0.315, 500.0, 5.0, 90.0, "G7", density_ratio=1.0
    )

    assert thin_air_g1 < standard_g1
    assert standard_g7 != standard_g1
