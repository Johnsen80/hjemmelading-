from src.utils.ballistics import (
    BallisticData,
    BallisticsCalculator,
    estimate_retained_velocity_fps,
    estimate_time_of_flight_seconds,
    estimate_wind_drift_cm,
)


def test_zero_shift_difference_matches_shared_drop_calculation():
    calc = BallisticsCalculator()
    ammo1 = BallisticData(2700.0, 0.315, 175.0, 100.0, "G7")
    ammo2 = BallisticData(2620.0, 0.245, 175.0, 100.0, "G7")

    shift = calc.calculate_zero_shift(ammo1, ammo2, 500.0, density_ratio=0.92)
    drop1 = calc.calculate_drop(2700.0, 0.315, 500.0, 100.0, "G7", density_ratio=0.92)
    drop2 = calc.calculate_drop(2620.0, 0.245, 500.0, 100.0, "G7", density_ratio=0.92)

    assert round(shift["difference_cm"], 6) == round(drop2 - drop1, 6)


def test_shared_retained_velocity_and_time_of_flight_follow_same_velocity_model():
    calc = BallisticsCalculator()
    retained = estimate_retained_velocity_fps(
        2710.0, 700.0, 0.245, "G7", density_ratio=0.89
    )
    direct = calc.calculate_velocity_at_distance(
        2710.0, 0.245, 700.0, "G7", density_ratio=0.89
    )
    tof = estimate_time_of_flight_seconds(
        2710.0, 0.245, 700.0, "G7", density_ratio=0.89
    )
    avg_velocity_mps = ((2710.0 + retained) / 2.0) * calc.FEET_TO_METERS
    expected_tof = 700.0 / avg_velocity_mps * calc._drag_scale("G7") * max(0.89, 0.5)

    assert retained == round(direct, 1)
    assert tof == expected_tof


def test_shared_wind_drift_uses_same_retained_velocity_path():
    calc = BallisticsCalculator()
    retained = calc.calculate_velocity_at_distance(
        2680.0, 0.228, 600.0, "G7", density_ratio=0.94
    )
    avg_velocity_fps = (2680.0 + retained) / 2.0
    wind_mph = 5.0 * 2.237
    range_yards = 600.0 * 1.094
    expected = round(
        (wind_mph * range_yards * 15.0)
        / (avg_velocity_fps * 0.228)
        * max(0.94, 0.5)
        * 2.54,
        1,
    )

    assert (
        estimate_wind_drift_cm(
            2680.0, 0.228, 600.0, 5.0, 90.0, "G7", density_ratio=0.94
        )
        == expected
    )
