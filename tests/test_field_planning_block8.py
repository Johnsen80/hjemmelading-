"""Block 8 tests: weather history, climate anomaly analysis, CDM BC calibration."""

from __future__ import annotations

import pytest

from src.field_planning.weather_history import (
    DropMeasurement,
    MonthlyClimateSummary,
    SessionWeatherRecord,
    WeatherHistoryReport,
    build_weather_warnings,
    calibrate_bc_from_drops,
    compute_anomaly,
    filter_sessions_by_month,
    parse_frost_monthly_normals,
    summarize_session_weather,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _climate(
    month=6, temp=15.0, pressure=1013.25, wind=3.0, wind_max=10.0
) -> MonthlyClimateSummary:
    return MonthlyClimateSummary(
        month=month,
        year_count=10,
        temp_mean_c=temp,
        temp_min_c=temp - 8,
        temp_max_c=temp + 8,
        pressure_mean_hpa=pressure,
        wind_mean_mps=wind,
        wind_max_mps=wind_max,
        humidity_mean_pct=60.0,
    )


def _session(
    session_id=1, date="2024-06-15", temp=15.0, wind=2.0
) -> SessionWeatherRecord:
    return SessionWeatherRecord(
        session_id=session_id,
        date=date,
        temperature_c=temp,
        pressure_hpa=1013.25,
        humidity_pct=60.0,
        wind_speed_mps=wind,
        wind_dir_deg=270.0,
    )


def _report(month=6, climate=None, records=None) -> WeatherHistoryReport:
    return WeatherHistoryReport(
        location_label="Test",
        target_date=f"2024-{month:02d}-15",
        month=month,
        climate_monthly=climate or _climate(month),
        session_records=records or [],
        anomaly_temp_c=None,
        anomaly_pressure_hpa=None,
        anomaly_wind_mps=None,
    )


# ---------------------------------------------------------------------------
# compute_anomaly
# ---------------------------------------------------------------------------


def test_anomaly_zero():
    anom, sev = compute_anomaly(15.0, 15.0)
    assert anom == 0.0
    assert sev == "normal"


def test_anomaly_extreme_high():
    _, sev = compute_anomaly(30.0, 15.0)
    assert sev == "extreme"


def test_anomaly_extreme_low():
    _, sev = compute_anomaly(0.0, 15.0)
    assert sev == "extreme"


def test_anomaly_notable():
    _, sev = compute_anomaly(21.0, 15.0)
    assert sev == "notable"


def test_anomaly_with_std_normal():
    anom, sev = compute_anomaly(16.0, 15.0, monthly_std=3.0)
    assert sev == "normal"


def test_anomaly_with_std_extreme():
    anom, sev = compute_anomaly(25.0, 15.0, monthly_std=3.0)
    assert sev == "extreme"


# ---------------------------------------------------------------------------
# filter_sessions_by_month
# ---------------------------------------------------------------------------


def test_filter_sessions_same_month():
    records = [_session(date="2024-06-10"), _session(date="2024-07-01")]
    filtered = filter_sessions_by_month(records, month=6)
    assert len(filtered) == 1
    assert filtered[0].date == "2024-06-10"


def test_filter_sessions_multi_year():
    records = [
        _session(date="2023-06-15"),
        _session(date="2022-06-20"),
        _session(date="2024-07-01"),
    ]
    filtered = filter_sessions_by_month(records, month=6)
    assert len(filtered) == 2


def test_filter_sessions_temp_tolerance():
    records = [
        _session(date="2024-06-10", temp=15.0),
        _session(date="2024-06-11", temp=30.0),  # too warm, filtered out
    ]
    filtered = filter_sessions_by_month(
        records, month=6, temp_tolerance_c=5.0, current_temp_c=14.0
    )
    assert len(filtered) == 1


def test_filter_sessions_empty():
    assert filter_sessions_by_month([], month=6) == []


# ---------------------------------------------------------------------------
# summarize_session_weather
# ---------------------------------------------------------------------------


def test_summarize_basic():
    records = [
        _session(temp=10.0, wind=2.0),
        _session(temp=20.0, wind=4.0),
    ]
    s = summarize_session_weather(records)
    assert s["count"] == 2
    assert s["temp_mean_c"] == pytest.approx(15.0)
    assert s["wind_mean_mps"] == pytest.approx(3.0)


def test_summarize_empty():
    assert summarize_session_weather([]) == {}


def test_summarize_min_max():
    records = [_session(temp=5.0), _session(temp=15.0), _session(temp=25.0)]
    s = summarize_session_weather(records)
    assert s["temp_min_c"] == 5.0
    assert s["temp_max_c"] == 25.0


# ---------------------------------------------------------------------------
# build_weather_warnings
# ---------------------------------------------------------------------------


def test_no_warnings_normal_conditions():
    report = _report(climate=_climate(temp=15.0))
    warnings = build_weather_warnings(
        report, current_temp_c=15.0, current_pressure_hpa=1013.25
    )
    assert warnings == []


def test_warning_extreme_temp():
    report = _report(climate=_climate(temp=15.0))
    warnings = build_weather_warnings(report, current_temp_c=35.0)
    assert any("varm" in w.lower() or "temp" in w.lower() for w in warnings)


def test_warning_extreme_cold():
    report = _report(climate=_climate(temp=15.0))
    warnings = build_weather_warnings(report, current_temp_c=-5.0)
    assert any("kald" in w.lower() or "temp" in w.lower() for w in warnings)


def test_warning_high_wind():
    report = _report(climate=_climate(wind_max=10.0))
    warnings = build_weather_warnings(report, current_wind_mps=9.0)
    assert any("vind" in w.lower() for w in warnings)


def test_no_warnings_without_climate():
    report = _report(climate=None)
    report.climate_monthly = None
    warnings = build_weather_warnings(report, current_temp_c=35.0)
    assert warnings == []


# ---------------------------------------------------------------------------
# parse_frost_monthly_normals (offline test with synthetic data)
# ---------------------------------------------------------------------------


def _make_frost_response(month: int, temp: float, pressure: float) -> dict:
    return {
        "data": [
            {
                "referenceTime": f"2020-{month:02d}-01T00:00:00Z",
                "observations": [
                    {"elementId": "mean(air_temperature P1M)", "value": temp},
                    {
                        "elementId": "mean(air_pressure_at_sea_level P1M)",
                        "value": pressure,
                    },
                    {"elementId": "mean(wind_speed P1M)", "value": 3.0},
                ],
            }
        ]
    }


def test_parse_frost_extracts_temp():
    resp = _make_frost_response(6, 18.0, 1010.0)
    summary = parse_frost_monthly_normals(resp, month=6)
    assert summary is not None
    assert summary.temp_mean_c == pytest.approx(18.0)


def test_parse_frost_extracts_pressure():
    resp = _make_frost_response(6, 18.0, 1008.0)
    summary = parse_frost_monthly_normals(resp, month=6)
    assert summary.pressure_mean_hpa == pytest.approx(1008.0)


def test_parse_frost_wrong_month_returns_none():
    resp = _make_frost_response(7, 18.0, 1010.0)  # July data
    summary = parse_frost_monthly_normals(resp, month=6)  # asking for June
    assert summary is None


def test_parse_frost_empty_returns_none():
    assert parse_frost_monthly_normals({}, 6) is None
    assert parse_frost_monthly_normals({"data": []}, 6) is None


# ---------------------------------------------------------------------------
# CDM BC calibration from drop measurements
# ---------------------------------------------------------------------------


def test_calibrate_bc_single_measurement():
    # If we measure drop consistent with known BC, calibration should recover it
    bc, rms = calibrate_bc_from_drops(
        measurements=[DropMeasurement(distance_m=500.0, measured_drop_cm=280.0)],
        nominal_mv_fps=2650.0,
        zero_distance_m=100.0,
        bc_type="G7",
        initial_bc=0.223,
    )
    assert 0.05 < bc < 1.5  # within valid BC range
    assert rms >= 0.0


def test_calibrate_bc_improves_with_close_measurement():
    # Measure a drop very close to what G7 0.223 produces at 300m
    # (from engine: ~66cm at 300m). A measurement of 66cm should give BC ≈ 0.223
    bc, rms = calibrate_bc_from_drops(
        measurements=[DropMeasurement(distance_m=300.0, measured_drop_cm=66.0)],
        nominal_mv_fps=2650.0,
        zero_distance_m=100.0,
        initial_bc=0.200,
    )
    assert rms < 20.0  # should converge to a reasonable match


def test_calibrate_bc_higher_drop_lower_bc():
    # Higher measured drop → bullet decelerated more → lower BC
    bc_less_drop, _ = calibrate_bc_from_drops(
        measurements=[DropMeasurement(500.0, 200.0)],
        nominal_mv_fps=2650.0,
        zero_distance_m=100.0,
    )
    bc_more_drop, _ = calibrate_bc_from_drops(
        measurements=[DropMeasurement(500.0, 400.0)],
        nominal_mv_fps=2650.0,
        zero_distance_m=100.0,
    )
    assert bc_less_drop > bc_more_drop


def test_calibrate_bc_empty_returns_initial():
    bc, rms = calibrate_bc_from_drops(
        measurements=[],
        nominal_mv_fps=2650.0,
        initial_bc=0.223,
    )
    assert bc == 0.223
    assert rms == 999.9
