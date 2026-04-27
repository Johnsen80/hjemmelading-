"""Tests: BatchAnalyzer consumes canonical engine_result (Block 6)."""

from src.modules.batch_analyzer import BatchAnalyzer


def _make_engine_result(
    *,
    area="validation",
    action="collect_matched_group_and_chrono",
    reason="Thin evidence — collect matched chrono and group before ranking.",
    next_action="collect_matched_group_and_chrono",
    why="Not enough paired data.",
    node_fit="developing",
    safety_blocked=False,
    safety_summary=None,
) -> dict:
    stack = [{"priority": 1, "area": area, "action": action, "reason": reason}]
    return {
        "safety": {
            "blocked": safety_blocked,
            "pressure_summary": {"summary": safety_summary} if safety_summary else {},
        },
        "candidate_profile": {"node_fit": node_fit},
        "decisions": {
            "recommendation_stack": stack,
            "next_test": {
                "recommended_action": next_action,
                "blocked": safety_blocked,
                "why": why,
            },
        },
    }


def _analyzer(engine_result=None, sessions=None, chrono=None):
    return BatchAnalyzer(
        {"batch_name": "Test Batch"},
        sessions=sessions or [],
        notes=[],
        attachments=[],
        chronograph_stats=chrono or {},
        engine_result=engine_result,
    )


def test_engine_next_steps_prepended_when_engine_result_provided():
    engine = _make_engine_result(
        area="charge_baseline",
        reason="Return to frozen charge baseline before comparing loads.",
        next_action="return_to_charge_baseline",
    )
    analysis = _analyzer(engine_result=engine).analyze()
    assert any(
        "charge_baseline" in step for step in analysis.next_steps
    ), "Engine area should appear in next_steps"
    assert analysis.next_steps[0].startswith("Engine"), "Engine step should be first"


def test_engine_next_focus_used_when_no_spread_focus():
    engine = _make_engine_result(next_action="return_to_charge_baseline")
    analysis = _analyzer(engine_result=engine).analyze()
    assert analysis.metrics["next_focus"] == "return_to_charge_baseline"


def test_safety_blocked_inserts_safety_step_first():
    engine = _make_engine_result(
        safety_blocked=True,
        safety_summary="Pressure signs detected — stop and review.",
        area="safety",
        reason="Stop and review before any further testing.",
    )
    analysis = _analyzer(engine_result=engine).analyze()
    assert any(
        "Safety:" in step for step in analysis.next_steps
    ), "Safety step must appear in next_steps when engine is blocked"
    safety_idx = next(i for i, s in enumerate(analysis.next_steps) if "Safety:" in s)
    assert safety_idx == 0, "Safety step must be first"


def test_engine_node_fit_stored_in_metrics():
    engine = _make_engine_result(node_fit="confirmed")
    analysis = _analyzer(engine_result=engine).analyze()
    assert analysis.metrics.get("engine_node_fit") == "confirmed"


def test_no_engine_result_still_works():
    analysis = _analyzer(engine_result=None).analyze()
    assert isinstance(analysis.next_steps, list)
    assert analysis.metrics.get("engine_node_fit") is None


def test_empty_engine_result_still_works():
    analysis = _analyzer(engine_result={}).analyze()
    assert isinstance(analysis.next_steps, list)


def test_engine_steps_do_not_duplicate_existing():
    reason = "Return to frozen charge baseline before comparing loads."
    engine = _make_engine_result(area="charge_baseline", reason=reason)
    analysis = _analyzer(engine_result=engine).analyze()
    label = f"Engine (charge_baseline): {reason}"
    count = sum(1 for s in analysis.next_steps if s == label)
    assert count == 1, "Engine step should appear exactly once"


def test_top_3_engine_stack_items_extracted():
    stack = [
        {"priority": 1, "area": "safety", "action": "stop", "reason": "Stop first."},
        {
            "priority": 2,
            "area": "charge_baseline",
            "action": "return",
            "reason": "Return to baseline.",
        },
        {
            "priority": 3,
            "area": "evidence",
            "action": "collect",
            "reason": "Collect more data.",
        },
        {
            "priority": 4,
            "area": "lots",
            "action": "hold",
            "reason": "Hold lots constant.",
        },
    ]
    engine = {
        "safety": {"blocked": False, "pressure_summary": {}},
        "candidate_profile": {"node_fit": "developing"},
        "decisions": {
            "recommendation_stack": stack,
            "next_test": {"recommended_action": "stop", "blocked": False, "why": ""},
        },
    }
    analysis = _analyzer(engine_result=engine).analyze()
    engine_steps = [s for s in analysis.next_steps if s.startswith("Engine")]
    assert len(engine_steps) == 3, "Only top 3 engine stack items should appear"
    assert "lots" not in " ".join(engine_steps), "4th item must be excluded"
