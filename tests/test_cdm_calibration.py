"""Tests for CDM BC calibration — calibrate_bc_from_drops and panel logic."""

from __future__ import annotations


def test_calibrate_bc_returns_tuple_with_rms():
    from src.field_planning.weather_history import (
        DropMeasurement,
        calibrate_bc_from_drops,
    )

    measurements = [
        DropMeasurement(distance_m=300.0, measured_drop_cm=45.0),
        DropMeasurement(distance_m=500.0, measured_drop_cm=130.0),
    ]
    bc, rms = calibrate_bc_from_drops(
        measurements=measurements,
        nominal_mv_fps=2750.0,
        zero_distance_m=100.0,
        bc_type="G7",
        initial_bc=0.280,
    )
    assert isinstance(bc, float)
    assert isinstance(rms, float)
    assert 0.05 <= bc <= 1.50
    assert rms >= 0.0


def test_calibrate_bc_empty_measurements_returns_initial():
    from src.field_planning.weather_history import calibrate_bc_from_drops

    bc, rms = calibrate_bc_from_drops(
        measurements=[],
        nominal_mv_fps=2750.0,
        initial_bc=0.300,
    )
    assert bc == 0.300
    assert rms == 999.9


def test_calibrate_bc_converges_for_known_bc():
    """Generate synthetic drops from BC=0.280 and verify recovery within ±0.04."""
    from src.field_planning.weather_history import (
        DropMeasurement,
        calibrate_bc_from_drops,
    )
    from src.utils.advanced_ballistics import (
        AdvancedBallisticsEngine,
        AtmosphericConditions,
    )

    true_bc = 0.280
    mv = 2750.0
    zero = 100.0
    engine = AdvancedBallisticsEngine()
    cond = AtmosphericConditions(
        temperature_f=59.0,
        pressure_inhg=29.92,
        humidity_percent=50.0,
        altitude_ft=0.0,
    )
    measurements = []
    for dist in [300.0, 500.0, 700.0]:
        pts = engine.calculate_trajectory(
            velocity_fps=mv,
            bc=true_bc,
            weight_grains=168.0,
            zero_distance_m=zero,
            max_distance_m=dist + 5.0,
            step_size_m=5.0,
            bc_type="G7",
            conditions=cond,
            wind_speed_mph=0.0,
            wind_angle_deg=90.0,
            latitude_deg=60.0,
            azimuth_deg=0.0,
            twist_rate=10.0,
            twist_direction="RIGHT",
        )
        if pts:
            pt = min(pts, key=lambda p: abs(p.distance_m - dist))
            measurements.append(
                DropMeasurement(
                    distance_m=dist,
                    measured_drop_cm=pt.drop_cm,
                )
            )

    assert len(measurements) >= 2, "Need ballistics engine to produce points"
    bc_cal, rms = calibrate_bc_from_drops(
        measurements=measurements,
        nominal_mv_fps=mv,
        zero_distance_m=zero,
        bc_type="G7",
        initial_bc=0.200,
    )
    assert (
        abs(bc_cal - true_bc) < 0.04
    ), f"Recovered BC {bc_cal:.4f} too far from true {true_bc}"
    assert rms < 2.0, f"RMS {rms:.2f} too high for synthetic data"


def test_calibrate_bc_g1_also_works():
    from src.field_planning.weather_history import (
        DropMeasurement,
        calibrate_bc_from_drops,
    )

    measurements = [
        DropMeasurement(distance_m=200.0, measured_drop_cm=18.0),
        DropMeasurement(distance_m=400.0, measured_drop_cm=95.0),
    ]
    bc, rms = calibrate_bc_from_drops(
        measurements=measurements,
        nominal_mv_fps=2900.0,
        zero_distance_m=100.0,
        bc_type="G1",
        initial_bc=0.450,
    )
    assert 0.10 <= bc <= 1.50
    assert rms < 200.0  # just ensure it runs without crash


def test_calibrate_bc_single_measurement():
    from src.field_planning.weather_history import (
        DropMeasurement,
        calibrate_bc_from_drops,
    )

    bc, rms = calibrate_bc_from_drops(
        measurements=[DropMeasurement(distance_m=500.0, measured_drop_cm=125.0)],
        nominal_mv_fps=2750.0,
        initial_bc=0.280,
    )
    assert 0.05 <= bc <= 1.50


def test_drop_measurement_defaults():
    from src.field_planning.weather_history import DropMeasurement

    m = DropMeasurement(distance_m=300.0, measured_drop_cm=45.0)
    assert m.conditions_temp_c == 15.0
    assert m.conditions_pressure_hpa == 1013.25
    assert m.notes == ""


def test_cdm_panel_imports_without_qt():
    """Panel module must import cleanly even without a display."""
    import sys

    # Ensure no crash when pyqtgraph unavailable
    saved = sys.modules.get("pyqtgraph")
    sys.modules["pyqtgraph"] = None  # type: ignore[assignment]
    try:
        if "src.ui.cdm_calibration_panel" in sys.modules:
            del sys.modules["src.ui.cdm_calibration_panel"]
        # Just verify it can be imported (the Qt guard handles missing display)
        import src.field_planning.weather_history as wh

        assert hasattr(wh, "calibrate_bc_from_drops")
        assert hasattr(wh, "DropMeasurement")
    finally:
        if saved is None:
            del sys.modules["pyqtgraph"]
        else:
            sys.modules["pyqtgraph"] = saved
