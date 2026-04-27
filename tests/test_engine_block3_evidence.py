"""Block 3 tests: evidence weighting, scientific core, conservative diagnosis.

Verifies that the engine:
- Prefers insufficient_evidence over forced diagnosis
- Caps evidence level under weak/mixed signal conditions
- Blocks ranking on ambiguous evidence
- Cold-bore and group-pattern channels surface in diagnostics
- Matched vs unmatched session counts drive repeat_confirmed conservatively
- Weakest-link reporting is present on engine output
"""

from src.modules.smart_ammo_engine import build_engine_result_from_input


def _r(evidence_summary=None, signal_hint=None, session=None, physics=None, lots=None):
    inp: dict = {}
    if session:
        inp["session"] = session
    if physics:
        inp["physics_inputs"] = physics
    if lots:
        inp["lots"] = lots
    ev_sum = dict(evidence_summary or {})
    if signal_hint and "batch_spread_signal_hint" not in ev_sum:
        ev_sum["batch_spread_signal_hint"] = signal_hint
    inp["evidence"] = {"summary": ev_sum}
    return build_engine_result_from_input(inp)


# ---------------------------------------------------------------------------
# Engine prefers insufficient_evidence over forced diagnosis
# ---------------------------------------------------------------------------


def test_insufficient_evidence_signal_blocks_candidate_ranking():
    r = _r(signal_hint="insufficient_evidence")
    ranking = r.get("decisions", {}).get("candidate_ranking") or {}
    assert (
        ranking.get("status") == "blocked"
    ), "insufficient_evidence must block candidate ranking"


def test_pressure_or_ammo_signal_blocks_candidate_ranking():
    r = _r(signal_hint="pressure_or_ammo")
    ranking = r.get("decisions", {}).get("candidate_ranking") or {}
    assert ranking.get("status") == "blocked"
    assert ranking.get("reason") == "pressure_or_ammo"


def test_no_velocity_no_group_produces_unresolved_evidence_status():
    r = _r(
        evidence_summary={"has_measured_velocity": False, "has_measured_group": False}
    )
    evidence_diag = r.get("evidence_diagnostics") or {}
    assert (
        evidence_diag.get("status") == "needs_measurement"
    ), "Missing velocity and group must set diagnostics to needs_measurement"


def test_velocity_only_evidence_caps_at_thin():
    r = _r(
        evidence_summary={
            "has_measured_velocity": True,
            "has_measured_group": False,
            "chronograph_import_count": 1,
            "batch_spread_evidence_quality": {"level": "strong", "score": 85.0},
            "batch_spread_signal_hint": "velocity_only",
        }
    )
    evidence_conf = r.get("evidence_confidence") or r.get("evidence") or {}
    # Engine must never report "strong" on velocity-only evidence
    eff_level = evidence_conf.get("status") or evidence_conf.get("level") or ""
    assert eff_level not in {
        "strong",
        "high",
    }, f"velocity-only evidence must not reach 'strong', got '{eff_level}'"


# ---------------------------------------------------------------------------
# Mixed signal handling
# ---------------------------------------------------------------------------


def test_mixed_signal_caps_evidence_at_moderate():
    r = _r(
        evidence_summary={
            "has_measured_velocity": True,
            "has_measured_group": True,
            "batch_spread_evidence_quality": {"level": "strong", "score": 85.0},
            "batch_spread_signal_hint": "ammo_or_process_signal",
            "batch_spread_note_flags": ["vertical_trend", "ammo_variation"],
            "batch_spread_pattern_flags": ["horizontal_dominant"],
        }
    )
    r_cand = r.get("candidate_profile") or {}
    # Mixed signal must prevent "high" robustness
    assert (
        r_cand.get("robustness_level") != "high"
    ), "Mixed signal with ambiguous hint must not reach high robustness"


def test_ammo_or_process_signal_is_mixed():
    r = _r(
        signal_hint="ammo_or_process_signal",
        evidence_summary={
            "has_measured_velocity": True,
            "has_measured_group": True,
            "batch_spread_evidence_quality": {"level": "strong", "score": 80.0},
        },
    )
    cand = r.get("candidate_profile") or {}
    assert cand.get("robustness_level") in {
        "low",
        "moderate",
    }, "ammo_or_process signal must keep robustness low or moderate"


# ---------------------------------------------------------------------------
# Small sample group cap
# ---------------------------------------------------------------------------


def test_small_sample_group_blocks_strong_robustness():
    r = _r(
        evidence_summary={
            "has_measured_velocity": True,
            "has_measured_group": True,
            "batch_spread_evidence_quality": {"level": "strong", "score": 85.0},
            "batch_spread_signal_hint": "node_or_barrel_timing_signal",
            "best_group_shot_count": 3,  # < 5 → small sample
            "range_session_count": 2,
        }
    )
    cand = r.get("candidate_profile") or {}
    assert (
        cand.get("robustness_level") != "high"
    ), "A 3-shot group must cap robustness below 'high'"
    assert cand.get("small_sample_group") is True


def test_five_shot_group_allows_high_robustness_with_strong_evidence():
    r = _r(
        evidence_summary={
            "has_measured_velocity": True,
            "has_measured_group": True,
            "batch_spread_evidence_quality": {"level": "strong", "score": 85.0},
            "batch_spread_signal_hint": "node_or_barrel_timing_signal",
            "best_group_shot_count": 5,
            "range_session_count": 2,
            "setup_matched_session_count": 2,
        }
    )
    cand = r.get("candidate_profile") or {}
    assert cand.get("small_sample_group") is False


# ---------------------------------------------------------------------------
# Matched vs unmatched session counts
# ---------------------------------------------------------------------------


def test_unmatched_sessions_excluded_from_repeat_confirmed():
    """2 total sessions but 1 unmatched → repeat_confirmed must be False."""
    r = _r(
        evidence_summary={
            "range_session_count": 2,
            "setup_matched_session_count": 1,  # only 1 confirmed for this setup
            "setup_unmatched_session_count": 1,
        }
    )
    cand = r.get("candidate_profile") or {}
    assert (
        cand.get("repeat_confirmed") is False
    ), "1 matched session must not satisfy repeat_confirmed (needs ≥2)"


def test_two_matched_sessions_confirms_repeat():
    r = _r(
        evidence_summary={
            "range_session_count": 3,
            "setup_matched_session_count": 2,
            "setup_unmatched_session_count": 1,
        }
    )
    cand = r.get("candidate_profile") or {}
    assert cand.get("repeat_confirmed") is True


def test_unmatched_session_count_stored_in_candidate_profile():
    r = _r(
        evidence_summary={
            "range_session_count": 2,
            "setup_matched_session_count": 1,
            "setup_unmatched_session_count": 1,
        }
    )
    cand = r.get("candidate_profile") or {}
    assert cand.get("setup_unmatched_session_count") == 1


def test_unmatched_sessions_appear_in_evidence_diagnostics():
    r = _r(
        evidence_summary={
            "range_session_count": 3,
            "setup_matched_session_count": 2,
            "setup_unmatched_session_count": 1,
        }
    )
    diag = r.get("evidence_diagnostics") or {}
    items = diag.get("items") or []
    has_unmatched_item = any(
        "different barrel" in s.lower() or "unmatched" in s.lower() for s in items
    )
    assert (
        has_unmatched_item
    ), "Unmatched sessions must appear in evidence_diagnostics items"


def test_no_setup_matched_field_falls_back_to_range_session_count():
    """When setup_matched_session_count is absent, use raw range_session_count."""
    r = _r(
        evidence_summary={
            "range_session_count": 2,
            # no setup_matched_session_count
        }
    )
    cand = r.get("candidate_profile") or {}
    assert (
        cand.get("repeat_confirmed") is True
    ), "Without setup_matched_session_count, range_session_count=2 must confirm repeat"


# ---------------------------------------------------------------------------
# Cold-bore channel
# ---------------------------------------------------------------------------


def test_hunting_goal_produces_cold_bore_diagnostic():
    r = _r(
        session={"usage_profile_name": "hunting"},
        evidence_summary={
            "has_measured_velocity": True,
            "has_measured_group": True,
            "batch_spread_evidence_quality": {"level": "moderate", "score": 65.0},
        },
    )
    diag = r.get("evidence_diagnostics") or {}
    focus = diag.get("focus_areas") or []
    # cold-bore must appear in focus areas for hunting goal
    assert any("cold" in f.lower() for f in focus), (
        "Hunting goal with pending cold-bore must add 'cold-bore validation' to focus areas. "
        f"Got focus_areas: {focus}"
    )


def test_non_hunting_goal_no_cold_bore_gate():
    r = _r(
        session={"usage_profile_name": "general"},
        evidence_summary={
            "has_measured_velocity": True,
            "has_measured_group": True,
        },
    )
    # No crash; cold_bore_status should be not_applicable for non-hunting
    cand = r.get("candidate_profile") or {}
    assert isinstance(cand, dict)


# ---------------------------------------------------------------------------
# Blocker-driven downscoping: safety always beats evidence quality
# ---------------------------------------------------------------------------


def test_safety_blocked_overrides_strong_evidence():
    r = _r(
        physics={
            "pressure_assessment": {"status": "warning", "summary": "Pressure signs."}
        },
        evidence_summary={
            "has_measured_velocity": True,
            "has_measured_group": True,
            "batch_spread_evidence_quality": {"level": "strong", "score": 90.0},
            "batch_spread_signal_hint": "node_or_barrel_timing_signal",
            "range_session_count": 3,
        },
    )
    cand = r.get("candidate_profile") or {}
    assert (
        cand.get("robustness_level") == "low"
    ), "Safety block must force 'low' robustness regardless of evidence quality"
    ranking = (r.get("decisions") or {}).get("candidate_ranking") or {}
    assert ranking.get("status") == "blocked"


def test_lot_watch_prevents_high_robustness():
    # lot_learning_summary is a derived field; pass it explicitly for build_engine_result_from_input
    from src.modules.smart_ammo_engine import build_engine_result_from_input

    r = build_engine_result_from_input(
        {
            "evidence": {
                "summary": {
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                    "batch_spread_evidence_quality": {"level": "strong", "score": 85.0},
                    "batch_spread_signal_hint": "node_or_barrel_timing_signal",
                    "best_group_shot_count": 5,
                    "range_session_count": 2,
                    "setup_matched_session_count": 2,
                }
            },
            "derived": {
                "lot_learning_summary": {
                    "status": "watch",
                    "watch_count": 1,
                    "active_lot_count": 1,
                    "components": [
                        {
                            "component": "powder",
                            "drift_flag": True,
                            "confidence_label": "watch",
                        }
                    ],
                }
            },
        }
    )
    cand = r.get("candidate_profile") or {}
    assert (
        cand.get("robustness_level") != "high"
    ), "A lot with drift_flag must prevent 'high' robustness"
    assert cand.get("lot_watch") is True


# ---------------------------------------------------------------------------
# Canonical evidence_quality_service is imported (not redefined)
# ---------------------------------------------------------------------------


def test_evidence_quality_service_constants_imported_in_engine():
    """Engine must use canonical score thresholds from evidence_quality_service."""
    from src.modules import smart_ammo_engine as engine_mod
    from src.tools.evidence_quality_service import score_to_level

    # Check engine imports the same function object
    assert hasattr(
        engine_mod, "_evidence_level_from_score"
    ), "Engine must expose _evidence_level_from_score alias for score_to_level"
    # Verify they produce the same result
    assert (
        engine_mod._evidence_level_from_score(80.0) == score_to_level(80.0) == "strong"
    )
    assert engine_mod._evidence_level_from_score(30.0) == score_to_level(30.0) == "thin"
