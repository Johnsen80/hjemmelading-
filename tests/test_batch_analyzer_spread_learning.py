from src.modules.batch_analyzer import BatchAnalyzer


def _analyze(*, sessions, chrono, notes=None, batch=None):
    analyzer = BatchAnalyzer(
        batch or {"batch_name": "Spread Batch"},
        sessions=sessions,
        notes=notes or [],
        attachments=[],
        chronograph_stats=chrono,
    )
    return analyzer.analyze()


def test_low_es_sd_large_group_marks_possible_shooter_or_setup_signal():
    analysis = _analyze(
        sessions=[{"group_size_mm": 34.0}],
        chrono={"count": 6, "avg": 2800.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "possible_shooter_or_setup_signal"
    assert analysis.metrics["spread_confidence"] == "medium"
    assert "controlled group" in " ".join(analysis.next_steps).lower()
    assert any("Do not reject the load" in item for item in analysis.watchouts)


def test_high_es_sd_large_group_marks_ammo_or_process_signal():
    analysis = _analyze(
        sessions=[{"group_size_mm": 36.0}],
        chrono={"count": 7, "avg": 2790.0, "es": 58.0, "sd": 22.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "ammo_or_process_signal"
    assert "loading process" in analysis.metrics["spread_reason"]
    assert "Ammo/process" in analysis.next_focus
    assert (
        analysis.metrics["spread_control_plan"]["title"]
        == "Ammo/process control series"
    )
    assert analysis.metrics["spread_control_priority"] == "high"
    assert (
        "same-setup control series"
        in analysis.metrics["spread_control_plan"]["primary_action"]
    )


def test_pressure_note_marks_pressure_or_ammo_signal():
    analysis = _analyze(
        sessions=[{"group_size_mm": 14.0}],
        chrono={"count": 6, "avg": 2810.0, "es": 14.0, "sd": 5.0},
        notes=[{"note_text": "Slight sticky bolt and flattened primer on shot 5."}],
    )

    assert analysis.metrics["spread_signal_hint"] == "pressure_or_ammo"
    assert analysis.next_focus == "Safety margin and lower powder spread"
    assert "pressure signs" in analysis.metrics["spread_reason"]
    assert analysis.metrics["spread_control_plan"]["priority"] == "safety"
    assert (
        "Stop precision tuning"
        in analysis.metrics["spread_control_plan"]["primary_action"]
    )
    assert analysis.metrics["spread_decision_state"] == "safety_stop"
    assert analysis.metrics["spread_can_optimize"] is False
    assert analysis.metrics["spread_can_reject_load"] is False


def test_session_notes_can_mark_shooter_or_setup_signal():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 31.0,
                "notes": "Called flyer and bad trigger rhythm on the last shots.",
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "possible_shooter_or_setup_signal"
    assert "shooter_series" in analysis.metrics["spread_note_flags"]
    assert any(
        "Session notes point to possible shooter" in item for item in analysis.watchouts
    )
    assert analysis.metrics["spread_decision_state"] == "repeat_before_rejecting"
    assert analysis.metrics["spread_can_reject_load"] is False


def test_norwegian_shooter_notes_mark_shooter_series_signal():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 29.0,
                "notes": "Dårlig avtrekk, napp og brutt serie.",
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "possible_shooter_or_setup_signal"
    assert "shooter_series" in analysis.metrics["spread_note_flags"]


def test_setup_equipment_notes_mark_setup_drift_watch():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 28.0,
                "notes": "Kikkert montasje kan være løst, demper ble tatt av og på.",
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "setup_drift_watch"
    assert "setup_equipment" in analysis.metrics["spread_note_flags"]
    assert "support, optic, torque" in analysis.metrics["spread_reason"]


def test_environment_notes_mark_condition_signal():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 28.0,
                "notes": "Skiftende vind og mye mirage.",
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "environment_or_condition_signal"
    assert "environment" in analysis.metrics["spread_note_flags"]
    assert "Environment-controlled repeat" in analysis.next_focus


def test_high_recorded_wind_marks_condition_signal():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 28.0,
                "wind_speed_mps": 6.2,
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "environment_or_condition_signal"
    assert analysis.metrics["spread_max_wind_mps"] == 6.2
    assert "6.2 m/s" in analysis.metrics["spread_reason"]


def test_horizontal_dominant_group_pattern_marks_condition_signal():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 22.0,
                "vertical_spread": 10.0,
                "horizontal_spread": 29.0,
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "environment_or_condition_signal"
    assert "horizontal_dominant" in analysis.metrics["spread_pattern_flags"]
    assert analysis.metrics["spread_axis_ratio"] == 2.9
    assert "horizontal-dominant" in analysis.metrics["spread_reason"]
    assert analysis.metrics["spread_decision_state"] == "condition_control_required"
    assert analysis.metrics["spread_can_optimize"] is False


def test_stable_chrono_with_vertical_pattern_marks_node_or_barrel_timing_signal():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 18.0,
                "analysis_json": {
                    "target": {
                        "vertical_spread_mm": 30.0,
                        "horizontal_spread_mm": 12.0,
                    }
                },
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "node_or_barrel_timing_signal"
    assert "vertical_dominant" in analysis.metrics["spread_pattern_flags"]
    assert "barrel timing" in analysis.metrics["spread_reason"]
    assert "Seating depth and barrel timing" in analysis.next_focus
    assert (
        analysis.metrics["spread_control_plan"]["title"]
        == "Vertical pattern and barrel timing check"
    )
    assert (
        "small seating-depth bracket"
        in analysis.metrics["spread_control_plan"]["primary_action"]
    )


def test_insufficient_evidence_gets_matched_evidence_control_plan():
    analysis = _analyze(
        sessions=[],
        chrono={"count": 2, "avg": 2800.0, "es": 10.0, "sd": 4.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "insufficient_evidence"
    assert (
        analysis.metrics["spread_control_plan"]["title"] == "Collect matched evidence"
    )
    assert (
        "matched chrono and group evidence"
        in analysis.metrics["spread_control_plan"]["primary_action"]
    )
    assert analysis.metrics["spread_decision_state"] == "collect_matched_evidence"
    assert analysis.metrics["spread_decision"]["paired_evidence"] is False
    quality = analysis.metrics["spread_evidence_quality"]
    assert quality["level"] == "very_thin"
    assert "measured_group" in quality["missing"]
    assert any("measured group" in item for item in quality["recommended_logging"])


def test_mixed_stable_paired_evidence_allows_cautious_optimization():
    analysis = _analyze(
        sessions=[
            {"group_size_mm": 14.0},
            {"group_size_mm": 13.5},
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 24.0, "sd": 9.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "mixed_but_stable"
    assert (
        analysis.metrics["spread_decision_state"] == "ready_for_cautious_optimization"
    )
    assert analysis.metrics["spread_can_optimize"] is True
    assert analysis.metrics["spread_decision"]["paired_evidence"] is True
    assert analysis.metrics["spread_evidence_quality"]["level"] == "moderate"
    assert (
        "paired_chrono_group"
        in analysis.metrics["spread_evidence_quality"]["strengths"]
    )
    validation = analysis.metrics["spread_validation_status"]
    assert validation["status"] == "cautious_validation_candidate"
    assert validation["ready_now"] is True


def test_rich_spread_evidence_quality_can_be_strong():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 14.0,
                "vertical_spread": 13.0,
                "horizontal_spread": 12.0,
                "wind_speed_mps": 2.0,
                "notes": "Rolig serie.",
            },
            {
                "group_size_mm": 13.5,
                "vertical_spread": 12.0,
                "horizontal_spread": 11.0,
                "wind_speed_mps": 2.5,
                "notes": "Lik støtte.",
            },
            {
                "group_size_mm": 13.8,
                "vertical_spread": 12.5,
                "horizontal_spread": 12.0,
                "wind_speed_mps": 2.2,
                "notes": "Ingen flyer.",
            },
        ],
        chrono={"count": 10, "avg": 2810.0, "es": 22.0, "sd": 8.0},
    )

    quality = analysis.metrics["spread_evidence_quality"]

    assert quality["level"] == "strong"
    assert quality["score"] >= 75.0
    assert quality["paired_evidence"] is True
    assert "target_pattern_context" in quality["strengths"]


def test_hunting_profile_guidance_prioritizes_cold_bore_field_validation():
    analysis = _analyze(
        batch={"batch_name": "Hunting Batch", "usage_profile_name": "Jakt"},
        sessions=[{"group_size_mm": 31.0}],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    guidance = analysis.metrics["spread_profile_guidance"]

    assert analysis.metrics["spread_usage_goal"] == "hunting"
    assert guidance["title"] == "Hunting validation focus"
    assert "cold-bore point of impact" in guidance["emphasis"]
    assert "realistic support" in guidance["recommended_check"]
    checklist = analysis.metrics["spread_capture_checklist"]
    assert checklist["title"] == "Next capture checklist"
    assert checklist["highest_priority"] in {
        "Cold-bore validation",
        "5+ shot chrono string",
        "Repeat measured group",
    }
    assert any(item["key"] == "cold_bore" for item in checklist["items"])
    validation = analysis.metrics["spread_validation_status"]
    assert validation["status"] == "field_validation_pending"
    assert validation["label"] == "Not field-ready yet"
    assert "cold-bore shot" in validation["next_gate"]
    assert validation["ready_now"] is False


def test_competition_profile_guidance_prioritizes_repeatability():
    analysis = _analyze(
        batch={"batch_name": "Match Batch", "usage_profile_name": "Konkurranse"},
        sessions=[{"group_size_mm": 36.0}],
        chrono={"count": 7, "avg": 2790.0, "es": 58.0, "sd": 22.0},
    )

    guidance = analysis.metrics["spread_profile_guidance"]

    assert analysis.metrics["spread_usage_goal"] == "competition"
    assert guidance["title"] == "Competition repeatability focus"
    assert "loading-process variation" in guidance["emphasis"]
    assert "same-setup control strings" in guidance["recommended_check"]
    validation = analysis.metrics["spread_validation_status"]
    assert validation["status"] == "ranking_validation_pending"
    assert validation["label"] == "Not ranking-ready yet"
    assert validation["ready_now"] is False


def test_learning_profile_guidance_uses_teaching_language():
    analysis = _analyze(
        batch={"batch_name": "Learning Batch", "usage_profile_name": "Læring / hobby"},
        sessions=[],
        chrono={"count": 2, "avg": 2800.0, "es": 10.0, "sd": 4.0},
    )

    guidance = analysis.metrics["spread_profile_guidance"]

    assert analysis.metrics["spread_usage_goal"] == "learning"
    assert guidance["title"] == "Learning and hobby focus"
    assert "Build understanding" in guidance["emphasis"]
    assert guidance["explanation_style"] == "teaching"
    explanation = analysis.metrics["spread_learning_explanation"]
    assert explanation["complexity"] == "teaching"
    assert explanation["title"] == "The system needs paired evidence"
    assert "Chrono alone cannot prove precision." in explanation["causal_chain"]
    assert "keep the next test small" in explanation["user_takeaway"]
    validation = analysis.metrics["spread_validation_status"]
    assert validation["status"] == "collect_more_data"
    assert validation["label"] == "Needs one clearer example"
    assert validation["ready_now"] is False


def test_competition_stable_evidence_can_be_cautious_ranking_candidate():
    analysis = _analyze(
        batch={"batch_name": "Match Stable", "usage_profile_name": "Competition"},
        sessions=[
            {"group_size_mm": 14.0, "vertical_spread": 13.0, "horizontal_spread": 12.0},
            {"group_size_mm": 13.8, "vertical_spread": 12.5, "horizontal_spread": 12.2},
            {"group_size_mm": 13.6, "vertical_spread": 12.2, "horizontal_spread": 12.0},
        ],
        chrono={"count": 10, "avg": 2810.0, "es": 22.0, "sd": 8.0},
    )

    validation = analysis.metrics["spread_validation_status"]

    assert validation["status"] == "cautious_ranking_candidate"
    assert validation["label"] == "Candidate for cautious ranking"
    assert validation["ready_now"] is True
    assert validation["readiness_score"] >= 70.0


def test_competition_learning_explanation_mentions_process_variation():
    analysis = _analyze(
        batch={"batch_name": "Match Batch", "usage_profile_name": "Konkurranse"},
        sessions=[{"group_size_mm": 36.0}],
        chrono={"count": 7, "avg": 2790.0, "es": 58.0, "sd": 22.0},
    )

    explanation = analysis.metrics["spread_learning_explanation"]

    assert explanation["complexity"] == "technical"
    assert (
        explanation["title"]
        == "Velocity spread and group spread can point to process variation"
    )
    assert "charge consistency" in explanation["watch_next"]
    assert "prove repeatability" in explanation["user_takeaway"]
    checklist = analysis.metrics["spread_capture_checklist"]
    assert any(item["key"] == "same_setup_repeat" for item in checklist["items"])
    assert any(item["key"] == "process_check" for item in checklist["items"])


def test_poi_shift_between_sessions_marks_setup_drift_watch():
    analysis = _analyze(
        sessions=[
            {
                "id": 1,
                "session_date": "2026-04-01",
                "group_size_mm": 16.0,
                "poi_x_mm": 0.0,
                "poi_y_mm": 2.0,
            },
            {
                "id": 2,
                "session_date": "2026-04-02",
                "group_size_mm": 17.0,
                "poi_x_mm": 24.0,
                "poi_y_mm": 3.0,
            },
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "setup_drift_watch"
    assert "poi_shift_watch" in analysis.metrics["spread_pattern_flags"]
    assert analysis.metrics["spread_poi_shift_mm"] == 24.0
    assert "Point of impact shifts" in analysis.metrics["spread_reason"]


def test_norwegian_pressure_note_overrides_condition_signal():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 28.0,
                "notes": "Skiftende vind, men også tung hevarm og flat tennhette.",
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "pressure_or_ammo"
    assert "pressure" in analysis.metrics["spread_note_flags"]
    assert analysis.next_focus == "Safety margin and lower powder spread"


def test_pressure_note_overrides_shooter_or_setup_note():
    analysis = _analyze(
        sessions=[
            {
                "group_size_mm": 31.0,
                "notes": "Called flyer, but also sticky bolt and flattened primer.",
            }
        ],
        chrono={"count": 6, "avg": 2810.0, "es": 18.0, "sd": 6.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "pressure_or_ammo"
    assert analysis.next_focus == "Safety margin and lower powder spread"


def test_thin_data_marks_insufficient_evidence():
    analysis = _analyze(
        sessions=[],
        chrono={"count": 3, "avg": 2800.0, "es": 10.0, "sd": 4.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "insufficient_evidence"
    assert analysis.metrics["spread_confidence"] == "low"
    assert (
        "too little measured group and chrono evidence"
        in analysis.metrics["spread_reason"]
    )


def test_worsening_group_trend_marks_setup_drift_watch():
    analysis = _analyze(
        sessions=[
            {"id": 1, "session_date": "2026-04-01", "group_size_mm": 12.0},
            {"id": 2, "session_date": "2026-04-02", "group_size_mm": 18.0},
            {"id": 3, "session_date": "2026-04-03", "group_size_mm": 27.0},
        ],
        chrono={"count": 6, "avg": 2800.0, "es": 26.0, "sd": 11.0},
    )

    assert analysis.metrics["spread_signal_hint"] == "setup_drift_watch"
    assert "drift" in analysis.metrics["spread_reason"]
    assert any("Worsening groups" in item for item in analysis.watchouts)


def test_html_mentions_spread_signal():
    analyzer = BatchAnalyzer(
        {"batch_name": "Spread Batch"},
        sessions=[{"group_size_mm": 34.0}],
        notes=[],
        attachments=[],
        chronograph_stats={"count": 6, "avg": 2800.0, "es": 18.0, "sd": 6.0},
    )

    html = analyzer.to_html()

    assert "<b>Spread Signal:</b>" in html
    assert "possible_shooter_or_setup_signal" in html
    assert "<b>Validation:</b>" in html
