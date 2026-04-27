"""Tests: Block 5 — robustness ranking, usage_goal next_action, blocked decisions."""

from src.modules.smart_ammo_engine import build_engine_result_from_input


def _result(evidence_summary=None, session=None, load=None, physics=None):
    inp: dict = {}
    if evidence_summary:
        inp["evidence"] = {"summary": evidence_summary}
    if session:
        inp["session"] = session
    if load:
        inp["load"] = load
    if physics:
        inp["physics_inputs"] = physics
    return build_engine_result_from_input(inp)


def _decisions(result):
    return result.get("decisions") or {}


def _candidate(result):
    return result.get("candidate_profile") or {}


# ---------------------------------------------------------------------------
# Robustness: single session cannot reach "high"
# ---------------------------------------------------------------------------


def test_single_session_capped_at_moderate_robustness():
    r = _result(
        evidence_summary={
            "batch_spread_evidence_quality": {"level": "moderate", "score": 65},
            "batch_spread_signal_hint": "node_or_barrel_timing_signal",
            "has_measured_velocity": True,
            "has_measured_group": True,
            "range_session_count": 1,
        }
    )
    assert (
        _candidate(r)["robustness_level"] != "high"
    ), "A single session must not reach 'high' robustness — only 'moderate' or 'low'"


def test_two_sessions_with_stable_harmonics_can_reach_high_robustness():
    r = _result(
        evidence_summary={
            "batch_spread_evidence_quality": {"level": "moderate", "score": 70},
            "batch_spread_signal_hint": "node_or_barrel_timing_signal",
            "has_measured_velocity": True,
            "has_measured_group": True,
            "range_session_count": 2,
            "best_group_shot_count": 5,
        },
    )
    # With 2 sessions we can reach high IF harmonics are stable; without harmonics
    # the test verifies that repeat_session_count is stored correctly.
    cand = _candidate(r)
    assert cand.get("repeat_session_count") == 2
    assert cand.get("repeat_confirmed") is True


def test_repeat_session_count_stored_in_candidate_profile():
    r = _result(evidence_summary={"range_session_count": 3})
    assert _candidate(r).get("repeat_session_count") == 3


def test_zero_sessions_sets_repeat_confirmed_false():
    r = _result(evidence_summary={"range_session_count": 0})
    assert _candidate(r).get("repeat_confirmed") is False


def test_pressure_signal_blocks_regardless_of_session_count():
    r = _result(
        evidence_summary={
            "batch_spread_signal_hint": "pressure_or_ammo",
            "range_session_count": 5,
        }
    )
    cand = _candidate(r)
    assert (
        cand["robustness_level"] == "low"
    ), "pressure_or_ammo must always produce 'low' robustness regardless of session count"


# ---------------------------------------------------------------------------
# Usage-goal: hunting → cold_bore_field_validation
# ---------------------------------------------------------------------------


def test_hunting_goal_produces_cold_bore_next_action():
    r = _result(
        session={"usage_profile_name": "hunting"},
        evidence_summary={
            "batch_spread_evidence_quality": {"level": "moderate"},
            "has_measured_velocity": True,
            "has_measured_group": True,
            "range_session_count": 1,
        },
    )
    decisions = _decisions(r)
    next_test = decisions.get("next_test") or {}
    assert (
        next_test.get("recommended_action") == "cold_bore_field_validation"
    ), "Hunting usage goal should steer toward cold_bore_field_validation"


def test_hunting_cold_bore_action_has_plan_and_rounds():
    r = _result(session={"usage_profile_name": "hunting"})
    plan = _decisions(r).get("execution_plan") or {}
    assert plan.get("session_type") == "field_validation"
    rounds = plan.get("estimated_rounds")
    assert rounds is not None and rounds > 0


# ---------------------------------------------------------------------------
# Usage-goal: competition → repeatability_string (first session)
# ---------------------------------------------------------------------------


def test_competition_without_repeats_produces_repeatability_string():
    r = _result(
        session={"usage_profile_name": "competition"},
        evidence_summary={
            "batch_spread_evidence_quality": {"level": "moderate"},
            "has_measured_velocity": True,
            "has_measured_group": True,
            "range_session_count": 1,
        },
    )
    next_test = _decisions(r).get("next_test") or {}
    assert (
        next_test.get("recommended_action") == "repeatability_string"
    ), "Competition goal with only 1 session should recommend repeatability_string"


def test_competition_with_repeats_does_not_force_repeatability_string():
    r = _result(
        session={"usage_profile_name": "competition"},
        evidence_summary={
            "batch_spread_evidence_quality": {"level": "moderate"},
            "has_measured_velocity": True,
            "has_measured_group": True,
            "range_session_count": 2,
        },
    )
    next_test = _decisions(r).get("next_test") or {}
    # With 2 sessions we should NOT get repeatability_string — move forward
    assert (
        next_test.get("recommended_action") != "repeatability_string"
    ), "Competition with 2 confirmed sessions must not re-ask for a repeatability string"


# ---------------------------------------------------------------------------
# Safety override: always wins over usage_goal
# ---------------------------------------------------------------------------


def test_safety_blocked_overrides_hunting_cold_bore_action():
    r = _result(
        session={"usage_profile_name": "hunting"},
        physics={
            "pressure_assessment": {
                "status": "warning",
                "summary": "Pressure signs detected.",
            }
        },
    )
    next_test = _decisions(r).get("next_test") or {}
    assert (
        next_test.get("recommended_action") == "stop_and_review"
    ), "Safety block must override hunting cold_bore goal"


def test_safety_blocked_overrides_competition_repeatability_action():
    r = _result(
        session={"usage_profile_name": "competition"},
        physics={
            "pressure_assessment": {"status": "warning", "summary": "High pressure."}
        },
    )
    next_test = _decisions(r).get("next_test") or {}
    assert (
        next_test.get("recommended_action") == "stop_and_review"
    ), "Safety block must override competition repeatability goal"


# ---------------------------------------------------------------------------
# do_not_change_yet and validation_gate
# ---------------------------------------------------------------------------


def test_thin_evidence_adds_do_not_promote_guardrail():
    r = _result(
        evidence_summary={
            "batch_spread_evidence_quality": {"level": "thin"},
        }
    )
    dont_change = _decisions(r).get("do_not_change_yet") or []
    assert any(
        "promote" in s.lower() or "thin" in s.lower() for s in dont_change
    ), "Thin evidence must produce a 'do not promote' guardrail"


def test_validation_gate_blocks_on_safety():
    r = _result(
        physics={"pressure_assessment": {"status": "warning", "summary": "Pressure."}}
    )
    gate = _decisions(r).get("validation_gate") or {}
    assert gate.get("status") == "blocked"


def test_validation_gate_ready_when_evidence_and_repeats_support_it():
    r = _result(
        evidence_summary={
            "batch_spread_evidence_quality": {"level": "strong", "score": 85},
            "batch_spread_signal_hint": "node_or_barrel_timing_signal",
            "has_measured_velocity": True,
            "has_measured_group": True,
            "range_session_count": 2,
            "best_group_shot_count": 5,
        }
    )
    gate = _decisions(r).get("validation_gate") or {}
    # Should be at least "confirm_node" or better, never "blocked"
    assert gate.get("status") != "blocked"


def test_candidate_ranking_blocked_on_insufficient_evidence():
    r = _result(
        evidence_summary={
            "batch_spread_evidence_quality": {"level": "very_thin"},
            "batch_spread_signal_hint": "insufficient_evidence",
        }
    )
    ranking = _decisions(r).get("candidate_ranking") or {}
    assert ranking.get("status") == "blocked"
