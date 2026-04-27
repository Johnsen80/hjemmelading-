from src.ballistics.services import build_bullet_fit_summary


def test_build_bullet_fit_summary_returns_ok_for_strong_match() -> None:
    summary = build_bullet_fit_summary(
        bullet={
            "length_mm": 32.4,
            "diameter_mm": 7.82,
            "geometry_confidence": "high",
        },
        bullet_geometry={
            "length_mm": 32.4,
            "diameter_mm": 7.82,
            "geometry_confidence": "high",
            "recommended_twist_in": 9.1,
            "twist_assessment": "compatible",
            "missing_fields": [],
            "notes": ["Boat-tail hunting profile."],
        },
        stability={"sg": 1.58, "velocity_fps": 2785.0},
        stability_assessment={"level": "ok", "title": "Stability looks healthy"},
        harmonics={"sensitivity": {"seating_depth": 1.15}},
        twist_inches=8.0,
        result={"muzzle_velocity_fps": 2785.0},
    )

    assert summary["level"] == "ok"
    assert float(summary["fit_score"]) >= 80.0
    assert "twist about 1:9.1 or faster" in str(summary["recommended_baseline"])


def test_build_bullet_fit_summary_returns_critical_for_unstable_match() -> None:
    summary = build_bullet_fit_summary(
        bullet={
            "length_mm": 37.8,
            "diameter_mm": 7.82,
            "geometry_confidence": "medium",
        },
        bullet_geometry={
            "length_mm": 37.8,
            "diameter_mm": 7.82,
            "geometry_confidence": "medium",
            "recommended_twist_in": 7.3,
            "twist_assessment": "slow_for_bullet",
            "missing_fields": ["tip-type"],
            "notes": ["Long VLD profile."],
        },
        stability={"sg": 0.94, "velocity_fps": 2460.0},
        stability_assessment={"level": "critical", "title": "High tumble risk"},
        harmonics={"sensitivity": {"seating_depth": 1.82}},
        twist_inches=10.0,
        result={"muzzle_velocity_fps": 2460.0},
    )

    assert summary["level"] == "critical"
    assert float(summary["fit_score"]) < 40.0
    assert (
        "unsafe" in str(summary["title"]).lower()
        or "poor" in str(summary["title"]).lower()
    )
