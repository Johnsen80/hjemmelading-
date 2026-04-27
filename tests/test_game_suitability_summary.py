from src.ballistics.services import build_game_suitability_summary


def test_game_suitability_summary_is_ok_for_healthy_medium_game_window() -> None:
    summary = build_game_suitability_summary(
        usage_profile="hunting_medium",
        terminal_summary={
            "level": "ok",
            "message": "Impact velocity and energy look usable.",
            "projectile_profile": {
                "confidence": "high",
                "profile_summary": "bonded, hunting",
                "minimum_expansion_fps": 1700.0,
                "preferred_impact_min_fps": 1800.0,
                "preferred_impact_max_fps": 2600.0,
            },
        },
    )

    assert summary["level"] == "ok"
    assert summary["game_label"] == "Roe deer / medium game"
    assert summary["confidence_label"] == "Medium confidence"


def test_game_suitability_summary_warns_for_large_game_when_terminal_window_warns() -> (
    None
):
    summary = build_game_suitability_summary(
        usage_profile="hunting_large",
        terminal_summary={
            "level": "warning",
            "message": "Impact velocity is below the estimated minimum working window.",
            "projectile_profile": {
                "confidence": "medium",
                "profile_summary": "match",
                "minimum_expansion_fps": 1900.0,
                "preferred_impact_min_fps": 2000.0,
            },
        },
    )

    assert summary["level"] == "warning"
    assert "Conditional fit" in str(summary["title"])
    assert "below the estimated minimum" in str(summary["message"])


def test_game_suitability_summary_is_neutral_without_hunting_profile() -> None:
    summary = build_game_suitability_summary(
        usage_profile="precision",
        terminal_summary={"level": "ok", "projectile_profile": {}},
    )

    assert summary["level"] == "neutral"
    assert summary["game_label"] is None
