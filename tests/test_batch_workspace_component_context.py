from src.modules import batch_workspace as batch_workspace_module


class _FakeSettings:
    store = {}

    def __init__(self, *args, **kwargs):
        pass

    def value(self, key, default=None):
        return self.store.get(key, default)

    def setValue(self, key, value):
        self.store[key] = value

    def sync(self):
        return None


def test_format_component_context_summary_prefers_saved_summary_html():
    summary = batch_workspace_module._format_component_context_summary(
        {
            "component_context": {
                "summary_html": "Kule: ELD-M | Målt lot-snitt aktivt<br>Krutt: N540 | Lot N540-24A"
            }
        },
        {},
    )

    assert "Kule: ELD-M" in summary
    assert "Krutt: N540" in summary


def test_format_component_context_summary_falls_back_to_context_fields():
    summary = batch_workspace_module._format_component_context_summary(
        {
            "component_context": {
                "bullet": {
                    "name": "ELD-M",
                    "lot_number": "LOT-140A",
                    "uses_measured_lot_stats": True,
                },
                "powder": {
                    "name": "N540",
                    "lot_number": "N540-24A",
                    "lot_learning_title": "Merkbart lotavvik",
                },
            }
        },
        {},
    )

    assert "measured lot average" in summary
    assert "Merkbart lotavvik" in summary


def test_build_retest_session_prefill_uses_saved_retest_advisory():
    prefill = batch_workspace_module._build_retest_session_prefill(
        {
            "retest_advisory": {
                "usage_profile": "precision",
                "suggested_control_shots": 5,
                "focus": "Chrono en full verifiseringsserie og se spesielt etter vertikalspredning og repeterbarhet.",
                "protocol_steps": [
                    "5 chrono-skudd i verifiseringsserie",
                    "Skyt minst én ekstra gruppe for repeterbarhet og vertikalspredning",
                    "Lås node først når ES/SD og treffpunkt gjentar seg",
                ],
            }
        }
    )

    assert prefill["session_name"] == "Retest - chrono and precision verification"
    assert prefill["distance_m"] == 100
    assert prefill["shot_count"] == 5
    assert "Fokus:" in prefill["notes"]
    assert "vertikalspredning" in prefill["notes"]


def test_build_subsonic_batch_hint_uses_saved_context():
    hint = batch_workspace_module._build_subsonic_batch_hint(
        {
            "subsonic_context": {
                "enabled": True,
                "target_velocity_fps": 1050.0,
                "advisory": {
                    "title": "Thin sonic margin",
                    "message": "Kun 18 fps margin under målet.",
                },
            }
        }
    )

    assert "Subsonic mode active" in hint
    assert "1050" in hint
    assert "Thin sonic margin" in hint


def test_format_subsonic_session_observations_compacts_flags():
    text = batch_workspace_module._format_subsonic_session_observations(
        {
            "subsonic_observations": {
                "cycling_status": "marginal",
                "sonic_crack": True,
                "keyhole": True,
                "suppressor_used": True,
            }
        }
    )

    assert "cycle=marginal" in text
    assert "sonic crack" in text
    assert "keyhole" in text
    assert "suppressor" in text


def test_format_model_match_summary_uses_title_message_and_first_check():
    text = batch_workspace_module._format_model_match_summary(
        {
            "model_match_advisory": {
                "title": "Modell stemmer godt",
                "message": "Predikert hastighet ligger tett på målt historikk.",
                "checks": [
                    "Avvik mot modell er ca 9 fps.",
                    "Charge-delta mot referanse er 0.00 gr.",
                ],
                "bias_direction": "neutral",
                "bias_fps": 4.0,
            }
        }
    )

    assert "Modell stemmer godt" in text
    assert "målt historikk" in text
    assert "9 fps" in text
    assert "no clear bias" in text


def test_build_direct_model_match_summary_uses_predicted_and_measured_velocity():
    summary = batch_workspace_module._build_direct_model_match_summary(
        {"predicted_result_summary": {"muzzle_velocity_fps": 2810.0}},
        {"avg": 2798.0},
    )

    assert "Direct model match" in summary["title"]
    assert "2798 fps" in summary["message"]
    assert "2810 fps" in summary["message"]


def test_build_direct_model_match_advisory_returns_structured_delta():
    advisory = batch_workspace_module._build_direct_model_match_advisory(
        {"predicted_result_summary": {"muzzle_velocity_fps": 2810.0}},
        {"avg": 2798.0},
    )

    assert advisory["level"] == "ok"
    assert advisory["delta_fps"] == 12.0
    assert advisory["predicted_velocity_fps"] == 2810.0
    assert advisory["measured_velocity_fps"] == 2798.0


def test_build_batch_evidence_basis_mentions_predicted_velocity_reference():
    summary = batch_workspace_module._build_batch_evidence_basis(
        {"charge_weight_grains": 43.0, "coal_mm": 71.2},
        {
            "predicted_result_summary": {"muzzle_velocity_fps": 2810.0},
        },
        [],
        {"avg": 2798.0},
    )

    assert "saved predicted velocity" in summary["message"]


def test_batch_workspace_reads_active_workflow_context_with_named_setup(monkeypatch):
    class _FakeSettings:
        def value(self, key, default=None):
            mapping = {
                "workflow_context/workflow_id": "12",
                "workflow_context/workflow_name": "OCW Test",
                "workflow_context/load_session_id": "33",
                "workflow_context/rifle_id": "7",
                "workflow_context/barrel_id": "B1",
                "workflow_context/barrel_name": "24in Match",
                "workflow_context/barrel_configuration_id": "cfg-supp",
                "workflow_context/barrel_configuration_name": "Suppressed",
                "workflow_context/created_date": "2026-03-20",
            }
            return mapping.get(key, default)

    monkeypatch.setattr(
        batch_workspace_module, "QSettings", lambda *args, **kwargs: _FakeSettings()
    )
    monkeypatch.setattr(
        batch_workspace_module,
        "get_database",
        lambda: type("_Db", (), {"get_by_id": lambda self, table, row_id: None})(),
    )

    context = batch_workspace_module._get_active_workflow_context()

    assert context["workflow_id"] == 12
    assert context["load_session_id"] == 33
    assert context["rifle_id"] == "7"
    assert context["barrel_id"] == "B1"
    assert context["barrel_name"] == "24in Match"
    assert context["barrel_configuration_id"] == "cfg-supp"
    assert context["barrel_configuration_name"] == "Suppressed"


def test_build_batch_evidence_basis_mentions_model_match_and_follow_up():
    summary = batch_workspace_module._build_batch_evidence_basis(
        {
            "charge_weight_grains": 43.0,
            "coal_mm": 71.2,
            "barrel_name": "26in Match Pipe",
            "barrel_configuration_name": "Suppressed",
        },
        {
            "score": 78.0,
            "model_match_advisory": {
                "level": "critical",
                "title": "Modell avviker",
                "message": "Historikken viser stort fartavvik.",
            },
        },
        [],
        {},
    )

    assert "Setup: 26in Match Pipe / Suppressed." in summary["message"]
    assert "model-vs-measured check" in summary["message"]
    assert "model deviation should be followed up with chrono" in summary["message"]


def test_build_batch_evidence_basis_mentions_spread_signal():
    summary = batch_workspace_module._build_batch_evidence_basis(
        {"charge_weight_grains": 43.0, "coal_mm": 71.2},
        {
            "score": 78.0,
            "metrics": {
                "spread_signal_hint": "possible_shooter_or_setup_signal",
                "spread_confidence": "medium",
                "spread_reason": "Chrono is stable while groups are open.",
                "spread_note_flags": ["shooter_series", "environment"],
                "spread_max_wind_mps": 6.2,
                "spread_pattern_flags": ["horizontal_dominant"],
                "spread_axis_ratio": 2.1,
                "spread_poi_shift_mm": 24.0,
                "spread_control_plan": {
                    "title": "Known-condition repeat",
                    "primary_action": "Repeat in calmer wind before changing charge.",
                },
                "spread_decision": {
                    "state": "condition_control_required",
                    "label": "Confirm conditions before judging load",
                },
                "spread_profile_guidance": {
                    "title": "Hunting validation focus",
                    "emphasis": "Confirm cold-bore point of impact from realistic field support.",
                },
                "spread_evidence_quality": {
                    "level": "thin",
                    "score": 41.0,
                },
                "spread_learning_explanation": {
                    "title": "Conditions can create false load signals",
                    "user_takeaway": "For hunting, prove safe cold-bore field behavior before trusting the load.",
                },
                "spread_capture_checklist": {
                    "title": "Next capture checklist",
                    "items": [
                        {"label": "Cold-bore validation"},
                    ],
                },
                "spread_validation_status": {
                    "label": "Not field-ready yet",
                    "summary": "The load still needs a controlled repeat and a conservative field-style confirmation before it should be trusted for hunting.",
                    "readiness_score": 54.0,
                },
            },
        },
        [{"group_size_mm": 34.0}],
        {"avg": 2798.0, "es": 18.0, "sd": 6.0},
    )

    assert "Spread: possible_shooter_or_setup_signal (medium)" in summary["message"]
    assert "Chrono is stable while groups are open." in summary["message"]
    assert "context flags: shooter_series, environment" in summary["message"]
    assert "max wind: 6.2 m/s" in summary["message"]
    assert "pattern flags: horizontal_dominant" in summary["message"]
    assert "axis ratio: 2.1" in summary["message"]
    assert "POI shift: 24.0 mm" in summary["message"]
    assert "control: Known-condition repeat" in summary["message"]
    assert (
        "next control: Repeat in calmer wind before changing charge."
        in summary["message"]
    )
    assert "decision: Confirm conditions before judging load" in summary["message"]
    assert "profile: Hunting validation focus" in summary["message"]
    assert (
        "profile focus: Confirm cold-bore point of impact from realistic field support."
        in summary["message"]
    )
    assert "evidence quality: thin (41.0/100)" in summary["message"]
    assert "lesson: Conditions can create false load signals" in summary["message"]
    assert (
        "takeaway: For hunting, prove safe cold-bore field behavior before trusting the load."
        in summary["message"]
    )
    assert "checklist: Next capture checklist" in summary["message"]
    assert "first capture: Cold-bore validation" in summary["message"]
    assert "validation: Not field-ready yet (54.0/100)" in summary["message"]
    assert (
        "validation summary: The load still needs a controlled repeat"
        in summary["message"]
    )


def test_build_batch_evidence_basis_mentions_smart_engine_summary():
    summary = batch_workspace_module._build_batch_evidence_basis(
        {"charge_weight_grains": 43.0, "coal_mm": 71.2},
        {"score": 78.0},
        [],
        {},
        {
            "summary": "Smart engine: robustness moderate, node fit developing, harmonics stable",
            "next": "Smart engine next: confirm_node_window - Confirm the current node window conservatively.",
            "gate": "Smart engine gate: Needs node confirmation - Run one same-setup confirmation string.",
            "protocol": "Smart engine protocol: Confirm the current node window conservatively. Keep constant: Keep charge, seating, and component lots fixed.",
            "hold": "Smart engine hold: Do not call the node proven until one same-setup repeat confirms it.",
            "blocker": "Smart engine blocker: Node confirmation block",
            "confidence": "Smart engine confidence: moderate (58.0/100) - The engine sees a usable direction, but the candidate still needs confirmation.",
        },
    )

    assert "Smart engine: robustness moderate" in summary["message"]
    assert "Smart engine next: confirm_node_window" in summary["message"]
    assert "Smart engine gate: Needs node confirmation" in summary["message"]
    assert (
        "Smart engine protocol: Confirm the current node window conservatively."
        in summary["message"]
    )
    assert (
        "Smart engine hold: Do not call the node proven until one same-setup repeat confirms it."
        in summary["message"]
    )
    assert "Smart engine blocker: Node confirmation block" in summary["message"]
    assert "Smart engine confidence: moderate (58.0/100)" in summary["message"]


def test_get_batch_smart_engine_summary_reads_runtime_engine(monkeypatch):
    monkeypatch.setattr(
        batch_workspace_module,
        "build_load_session_runtime",
        lambda db, session_id: {
            "smart_engine": {
                "engine_result": {
                    "evidence_diagnostics": {
                        "status": "needs_measurement",
                        "items": [
                            "Session still lacks measured chronograph data for the active setup."
                        ],
                    },
                    "bullet_fit": {
                        "level": "warning",
                        "message": "The setup may work, but the margin is limited.",
                    },
                    "chamber_jump": {
                        "summary": "Current jump 0.100 mm sits in tight.",
                    },
                    "candidate_profile": {
                        "robustness_level": "moderate",
                        "node_fit": "developing",
                    },
                    "harmonics": {
                        "stability_tier": "stable",
                    },
                    "safety": {
                        "state": "ok",
                        "blocked": False,
                    },
                    "decisions": {
                        "validation_gate": {
                            "label": "Needs node confirmation",
                            "next_gate": "Run one same-setup confirmation string.",
                        },
                        "execution_plan": {
                            "summary": "Confirm the current node window conservatively.",
                            "keep_constant": [
                                "Keep charge, seating, and component lots fixed."
                            ],
                        },
                        "do_not_change_yet": [
                            "Do not call the node proven until one same-setup repeat confirms it."
                        ],
                        "blocked_by": [
                            {
                                "kind": "node_confirmation",
                                "title": "Node confirmation block",
                            }
                        ],
                        "recommendation_confidence": {
                            "level": "moderate",
                            "score": 58.0,
                            "summary": "The engine sees a usable direction, but the candidate still needs confirmation.",
                        },
                        "next_test": {
                            "recommended_action": "confirm_node_window",
                            "why": "Confirm the current node window conservatively.",
                        },
                    },
                }
            }
        },
    )

    summary = batch_workspace_module._get_batch_smart_engine_summary(
        object(),
        {"load_session_id": 44},
    )

    assert "robustness moderate" in summary["summary"]
    assert "harmonics stable" in summary["summary"]
    assert summary["next_action"] == "confirm_node_window"
    assert "Confirm the current node window conservatively." in summary["next"]
    assert (
        summary["gate"]
        == "Smart engine gate: Needs node confirmation - Run one same-setup confirmation string."
    )
    assert (
        "Keep constant: Keep charge, seating, and component lots fixed."
        in summary["protocol"]
    )
    assert (
        summary["hold"]
        == "Smart engine hold: Do not call the node proven until one same-setup repeat confirms it."
    )
    assert summary["blocker"] == "Smart engine blocker: Node confirmation block"
    assert "58.0/100" in summary["confidence"]
    assert (
        summary["evidence"]
        == "Smart engine evidence: needs_measurement - Session still lacks measured chronograph data for the active setup."
    )
    assert (
        summary["bullet_fit"]
        == "Smart engine bullet fit: warning - The setup may work, but the margin is limited."
    )
    assert summary["jump"] == "Smart engine jump: Current jump 0.100 mm sits in tight."


def test_get_batch_smart_engine_summary_exposes_baseline_return_signal(monkeypatch):
    monkeypatch.setattr(
        batch_workspace_module,
        "build_load_session_runtime",
        lambda db, session_id: {
            "smart_engine": {
                "engine_result": {
                    "baseline_diagnostics": {
                        "status": "return_to_baseline",
                        "items": [
                            "Charge 42.40 gr is 0.40 gr away from the frozen learned recommendation baseline (42.00 gr)."
                        ],
                    },
                    "baseline_control": {
                        "charge_alignment": "outside",
                        "charge_target_label": "42.00 gr",
                        "active_return_line": "Return charge toward 42.00 gr before treating this as the same candidate.",
                    },
                    "branch_advisory": {
                        "display_line": "Custom branch (return_before_compare)",
                    },
                    "candidate_profile": {
                        "robustness_level": "moderate",
                        "node_fit": "strong",
                    },
                    "harmonics": {
                        "stability_tier": "stable",
                    },
                    "decisions": {
                        "next_test": {
                            "recommended_action": "return_to_charge_baseline",
                            "why": "Current charge is outside the frozen learned baseline; return to 42.00 gr or validate a fresh charge node first.",
                        },
                        "recommendation_confidence": {
                            "level": "moderate",
                            "score": 58.0,
                            "summary": "The engine sees a usable direction, but the candidate still needs confirmation.",
                        },
                    },
                }
            }
        },
    )

    summary = batch_workspace_module._get_batch_smart_engine_summary(
        object(), {"load_session_id": 45}
    )

    assert (
        summary["baseline"]
        == "Smart engine baseline: Return charge toward 42.00 gr before treating this as the same candidate."
    )
    assert (
        summary["branch"]
        == "Smart engine branch: Custom branch (return_before_compare)"
    )
    assert summary["baseline_status"] == "return_to_baseline"


def test_build_batch_comparison_basis_penalizes_provisional_batch():
    comparison = batch_workspace_module._build_batch_comparison_basis(
        {
            "id": 10,
            "batch_name": "Current Batch",
            "load_session_id": 33,
            "analysis_json": {
                "metrics": {
                    "group_avg_mm": 13.5,
                    "spread_signal_hint": "possible_shooter_or_setup_signal",
                    "spread_evidence_quality": {"score": 42.0, "level": "thin"},
                    "spread_validation_status": {
                        "status": "ranking_validation_pending",
                        "label": "Not ranking-ready yet",
                        "readiness_score": 48.0,
                        "ready_now": False,
                    },
                }
            },
        },
        [
            {
                "id": 11,
                "batch_name": "Proven Batch",
                "load_session_id": 33,
                "analysis_json": {
                    "metrics": {
                        "group_avg_mm": 14.2,
                        "spread_signal_hint": "mixed_but_stable",
                        "spread_evidence_quality": {"score": 82.0, "level": "strong"},
                        "spread_validation_status": {
                            "status": "cautious_ranking_candidate",
                            "label": "Candidate for cautious ranking",
                            "readiness_score": 78.0,
                            "ready_now": True,
                        },
                    }
                },
            }
        ],
    )

    assert comparison["available"] is True
    assert comparison["ranking_state"] == "trailing_candidate"
    assert comparison["current_rank"] == 2
    assert comparison["leader_batch_name"] == "Proven Batch"
    assert any("provisional" in item.lower() for item in comparison["watchouts"])


def test_build_batch_comparison_basis_can_mark_ready_batch_as_leading_candidate():
    comparison = batch_workspace_module._build_batch_comparison_basis(
        {
            "id": 20,
            "batch_name": "Match Node A",
            "load_session_id": 44,
            "analysis_json": {
                "metrics": {
                    "group_avg_mm": 12.8,
                    "spread_signal_hint": "mixed_but_stable",
                    "spread_evidence_quality": {"score": 84.0, "level": "strong"},
                    "spread_validation_status": {
                        "status": "cautious_ranking_candidate",
                        "label": "Candidate for cautious ranking",
                        "readiness_score": 79.0,
                        "ready_now": True,
                    },
                    "spread_decision": {"can_optimize": True},
                }
            },
        },
        [
            {
                "id": 21,
                "batch_name": "Match Node B",
                "load_session_id": 44,
                "analysis_json": {
                    "metrics": {
                        "group_avg_mm": 14.0,
                        "spread_signal_hint": "mixed_but_stable",
                        "spread_evidence_quality": {"score": 70.0, "level": "moderate"},
                        "spread_validation_status": {
                            "status": "cautious_ranking_candidate",
                            "label": "Candidate for cautious ranking",
                            "readiness_score": 68.0,
                            "ready_now": True,
                        },
                    }
                },
            }
        ],
    )

    assert comparison["available"] is True
    assert comparison["ranking_state"] == "leading_candidate"
    assert comparison["current_rank"] == 1
    assert comparison["summary"].startswith("Match Node A leads")


def test_build_batch_comparison_advisory_for_trailing_candidate_is_conservative():
    advisory = batch_workspace_module._build_batch_comparison_advisory(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "summary": "Current Batch currently ranks 2 of 3 comparable batches and trails Proven Batch by about 7.5 score points.",
            "leader_batch_name": "Proven Batch",
            "next_gate": "Not ranking-ready yet",
            "watchouts": [
                "Do not let a provisional batch outrank better-validated evidence."
            ],
        }
    )

    assert advisory["level"] == "warning"
    assert advisory["title"] == "Trailing stronger evidence"
    assert advisory["promotion_ready"] is False
    assert advisory["recommended_action"] == "Not ranking-ready yet"
    assert "provisional batch" in advisory["watchouts"][0]


def test_build_batch_comparison_advisory_for_leading_candidate_can_be_ready():
    advisory = batch_workspace_module._build_batch_comparison_advisory(
        {
            "available": True,
            "ranking_state": "leading_candidate",
            "summary": "Match Node A leads 2 comparable batches on combined precision, evidence quality, and readiness.",
            "next_gate": "Confirm one more same-setup repeat string before treating the ranking as durable across sessions or matches.",
            "watchouts": [],
        }
    )

    assert advisory["level"] == "ok"
    assert advisory["title"] == "Leading comparison candidate"
    assert advisory["promotion_ready"] is True
    assert "Confirm one more same-setup repeat string" in advisory["recommended_action"]


def test_build_batch_comparison_protocol_for_trailing_candidate_is_head_to_head():
    protocol = batch_workspace_module._build_batch_comparison_protocol(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "leader_batch_name": "Proven Batch",
            "current_batch": {
                "usage_goal": "competition",
                "setup_label": "24in Match / Suppressed",
            },
        }
    )

    assert protocol["title"] == "Head-to-head catch-up test"
    assert "Proven Batch" in protocol["primary_action"]
    assert "same rifle setup" in protocol["shot_plan"]


def test_build_batch_comparison_protocol_for_leading_candidate_requires_confirmation():
    protocol = batch_workspace_module._build_batch_comparison_protocol(
        {
            "available": True,
            "ranking_state": "leading_candidate",
            "current_batch": {
                "usage_goal": "competition",
                "setup_label": "24in Match / Suppressed",
            },
        }
    )

    assert protocol["title"] == "Confirmation before promotion"
    assert "runner-up" in protocol["primary_action"]
    assert "alternating order" in protocol["shot_plan"]


def test_build_batch_comparison_explanation_identifies_validation_depth_bottleneck():
    explanation = batch_workspace_module._build_batch_comparison_explanation(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "leader_batch_name": "Proven Batch",
            "leader_gap_score": 7.5,
            "current_batch": {
                "quality_level": "moderate",
                "validation_state": "ranking_validation_pending",
                "signal_hint": "mixed_but_stable",
                "ready_now": False,
                "group_avg_mm": 13.8,
                "quality_score": 68.0,
                "validation_score": 54.0,
            },
        }
    )

    assert explanation["title"] == "Comparison explanation"
    assert explanation["limiting_factor"] == "validation_depth"
    assert "trails Proven Batch" in explanation["reason"]
    assert "matched chrono and measured groups" in explanation["next_measurement"]


def test_build_batch_comparison_verdict_marks_trailing_batch_as_do_not_promote():
    verdict = batch_workspace_module._build_batch_comparison_verdict(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "leader_batch_name": "Proven Batch",
        },
        {"promotion_ready": False},
    )

    assert verdict["state"] == "do_not_promote_yet"
    assert verdict["label"] == "Do not promote yet"
    assert verdict["promote_now"] is False


def test_build_batch_comparison_checklist_targets_validation_depth():
    checklist = batch_workspace_module._build_batch_comparison_checklist(
        {"available": True, "ranking_state": "trailing_candidate"},
        {"shot_plan": "Shoot both batches in the same session."},
        {"limiting_factor": "validation_depth"},
    )

    assert checklist["title"] == "Comparison checklist"
    assert checklist["highest_priority"] in {
        "Same setup on both batches",
        "Matched chrono and measured groups",
        "Repeat the current batch once more",
    }
    assert any(item["key"] == "repeat_string" for item in checklist["items"])


def test_build_batch_comparison_scorecard_identifies_evidence_quality_swing():
    scorecard = batch_workspace_module._build_batch_comparison_scorecard(
        {
            "available": True,
            "current_rank": 2,
            "current_batch": {
                "batch_name": "Current Batch",
                "group_avg_mm": 13.2,
                "quality_score": 45.0,
                "validation_score": 62.0,
            },
            "top_candidates": [
                {
                    "batch_name": "Leader Batch",
                    "group_avg_mm": 13.8,
                    "quality_score": 82.0,
                    "validation_score": 74.0,
                    "comparison_score": 78.0,
                }
            ],
        }
    )

    assert scorecard["title"] == "Comparison scorecard"
    assert scorecard["swing_factor"] == "evidence_quality"
    assert "evidence quality" in scorecard["summary"].lower()
    assert scorecard["delta_evidence_quality"] < 0


def test_build_batch_comparison_confidence_can_be_thin():
    confidence = batch_workspace_module._build_batch_comparison_confidence(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "leader_gap_score": 7.5,
            "current_batch": {
                "quality_score": 45.0,
                "validation_score": 52.0,
            },
        },
        {"limiting_factor": "validation_depth"},
        {"promote_now": False},
    )

    assert confidence["title"] == "Comparison confidence"
    assert confidence["level"] in {"thin", "very_thin"}
    assert confidence["score"] < 55.0


def test_build_batch_comparison_learning_note_can_explain_evidence_quality():
    note = batch_workspace_module._build_batch_comparison_learning_note(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "current_batch": {"usage_goal": "competition"},
        },
        {"swing_factor": "evidence_quality"},
        {"limiting_factor": "validation_depth"},
    )

    assert note["title"] == "Comparison learning note"
    assert "Evidence quality" in note["plain_summary"]
    assert "competition" in note["takeaway"].lower()


def test_build_batch_comparison_acceptance_can_hold_hunting_candidate():
    acceptance = batch_workspace_module._build_batch_comparison_acceptance(
        {
            "available": True,
            "ranking_state": "leading_but_provisional",
            "leader_batch_name": "Current batch",
            "current_batch": {"usage_goal": "hunting"},
        },
        {"recommended_action": "Not field-ready yet"},
        {"limiting_factor": "field_validation"},
        {"state": "hold_leader", "promote_now": False},
        {"level": "moderate", "score": 61.0},
    )

    assert acceptance["title"] == "Comparison acceptance gate"
    assert acceptance["state"] == "provisional_acceptance"
    assert acceptance["label"] == "Almost accepted, but still provisional"
    assert acceptance["next_gate"] == "Not field-ready yet"
    assert acceptance["candidate_type"] == "field candidate"
    assert any("Cold-bore" in item for item in acceptance["must_be_true"])
    assert any(
        "field validation" in item.lower() for item in acceptance["remaining_gaps"]
    )


def test_build_batch_comparison_acceptance_progress_can_score_partial_state():
    progress = batch_workspace_module._build_batch_comparison_acceptance_progress(
        {
            "state": "provisional_acceptance",
            "must_be_true": [
                "Same setup must match.",
                "Cold-bore must validate.",
                "No safety watch can remain.",
                "Point of impact must hold.",
            ],
            "remaining_gaps": [
                "Cold-bore or realistic field validation is still missing.",
            ],
            "next_gate": "Not field-ready yet",
        },
        {"highest_priority": "Cold-bore confirmation"},
        {"score": 61.0},
    )

    assert progress["title"] == "Comparison acceptance progress"
    assert progress["level"] in {"advancing", "partial"}
    assert progress["passed_count"] == 3
    assert progress["total_count"] == 4
    assert progress["next_target"] == "Not field-ready yet"


def test_build_batch_comparison_status_and_next_test_can_summarize_trailing_batch():
    next_test = batch_workspace_module._build_batch_comparison_next_test(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "leader_batch_name": "Leader Batch",
        },
        {
            "title": "Head-to-head catch-up test",
            "primary_action": "Run a same-day head-to-head against Leader Batch before promoting this batch.",
            "shot_plan": "Shoot both batches with the same setup.",
        },
        {
            "state": "acceptance_pending",
            "next_gate": "Repeat the same setup with matched chrono and measured groups.",
        },
        {
            "level": "partial",
            "score": 44.5,
        },
        {
            "highest_priority": "Same setup on both batches",
        },
    )
    status = batch_workspace_module._build_batch_comparison_status_board(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "leader_batch_name": "Leader Batch",
            "current_rank": 2,
            "count": 3,
        },
        {"label": "Do not promote yet"},
        {"state": "acceptance_pending", "ready_for_acceptance": False},
        {"level": "partial", "score": 44.5},
        next_test,
    )

    assert next_test["title"] == "Catch-up test vs Leader Batch"
    assert next_test["test_type"] == "head_to_head"
    assert status["title"] == "Comparison status board"
    assert status["state"] == "catch_up"
    assert status["readiness_band"] == "behind"
    assert "Leader: Leader Batch" in status["summary"]


def test_build_batch_comparison_profile_and_mission_can_reflect_hunting_goal():
    profile = batch_workspace_module._build_batch_comparison_profile_priority(
        {
            "available": True,
            "current_batch": {"usage_goal": "hunting"},
        },
        {
            "state": "provisional_acceptance",
            "next_gate": "Not field-ready yet",
        },
        {
            "primary_action": "Repeat the current leader under the same setup before promoting it.",
        },
    )
    mission = batch_workspace_module._build_batch_comparison_mission_brief(
        {"available": True},
        {"headline": "Close, but still provisional", "readiness_band": "near_ready"},
        profile,
        {
            "summary": "The batch is close, but one last matched confirmation should close the final gap before promotion.",
            "primary_action": "Repeat the current leader under the same setup before promoting it.",
            "check_first": "Cold-bore confirmation",
        },
        {"next_gate": "Not field-ready yet"},
    )

    assert profile["title"] == "Hunting comparison priority"
    assert "cold-bore" in profile["guardrail"].lower()
    assert mission["title"] == "Comparison mission brief"
    assert "field-trust check" in mission["mission"]
    assert mission["check_first"] == "Cold-bore confirmation"


def test_build_batch_comparison_portfolio_and_session_strategy_can_reflect_competition():
    portfolio = batch_workspace_module._build_batch_comparison_portfolio(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "leader_batch_name": "Node A",
            "top_candidates": [
                {"batch_name": "Node A", "comparison_score": 81.0},
                {"batch_name": "Current Batch", "comparison_score": 74.0},
            ],
        },
        {"headline": "Still chasing the leader"},
        {"ready_for_acceptance": False},
    )
    strategy = batch_workspace_module._build_batch_comparison_session_strategy(
        {
            "available": True,
            "ranking_state": "trailing_candidate",
            "current_batch": {"usage_goal": "competition"},
        },
        {
            "guardrail": "Do not rank a batch higher until the same-day repeat and matched chrono/group evidence agree.",
        },
        {
            "primary_action": "Run a same-day head-to-head against Node A before promoting this batch.",
        },
        {
            "test_type": "head_to_head",
            "check_first": "Same setup on both batches",
        },
    )

    assert portfolio["title"] == "Comparison portfolio"
    assert portfolio["rows"][0]["batch_name"] == "Node A"
    assert "close the gap" in portfolio["focus"].lower()
    assert strategy["title"] == "Comparison session strategy"
    assert strategy["mode"] == "ranking_session"
    assert "Challenge the current leader" in strategy["objective"]


def test_build_batch_comparison_campaign_and_action_plan_can_summarize_set():
    campaign = batch_workspace_module._build_batch_comparison_campaign_view(
        {
            "title": "Comparison portfolio",
            "leader_batch_name": "Node A",
        },
        {
            "title": "Comparison session strategy",
            "mode": "ranking_session",
            "objective": "Challenge the current leader under matched conditions.",
        },
        {
            "readiness_band": "behind",
        },
        {
            "title": "Catch-up test vs Node A",
            "primary_action": "Run a same-day head-to-head against Node A before promoting this batch.",
        },
    )
    action_plan = batch_workspace_module._build_batch_comparison_action_plan(
        campaign,
        {
            "mission": "Still chasing the leader: Treat the next outing as a matched ranking test, not a free-form tuning session.",
            "primary_action": "Run a same-day head-to-head against Node A before promoting this batch.",
            "success_marker": "A matched repeat string that still holds precision and consistency against the current leader.",
        },
        {
            "items": [
                {"label": "Same setup on both batches"},
                {"label": "Matched chrono and measured groups"},
            ]
        },
    )

    assert campaign["title"] == "Comparison campaign view"
    assert "Leader Node A" in campaign["summary"]
    assert action_plan["title"] == "Comparison action plan"
    assert action_plan["first_steps"][0] == "Same setup on both batches"


def test_build_batch_comparison_campaign_board_and_queue_can_prioritize_batches():
    board = batch_workspace_module._build_batch_comparison_campaign_board(
        {
            "available": True,
            "ranked_batches": [
                {
                    "batch_name": "Leader",
                    "rank": 1,
                    "ready_now": True,
                    "comparison_score": 82.0,
                    "validation_state": "",
                    "signal_hint": "",
                },
                {
                    "batch_name": "Candidate",
                    "rank": 2,
                    "ready_now": False,
                    "comparison_score": 76.0,
                    "validation_state": "ranking_validation_pending",
                    "signal_hint": "",
                },
                {
                    "batch_name": "Watch",
                    "rank": 3,
                    "ready_now": False,
                    "comparison_score": 40.0,
                    "validation_state": "safety_block",
                    "signal_hint": "pressure_or_ammo",
                },
            ],
        },
        {
            "summary": "Leader Node A | band behind | mode ranking_session | Challenge the current leader under matched conditions."
        },
        {"summary": "Challenge the current leader under matched conditions."},
    )
    queue = batch_workspace_module._build_batch_comparison_session_queue(
        board,
        {
            "mode": "ranking_session",
            "objective": "Challenge the current leader under matched conditions.",
        },
    )

    assert board["title"] == "Comparison campaign board"
    assert board["rows"][0]["priority"] == "shoot_now"
    assert any(row["priority"] == "reject_watch" for row in board["rows"])
    assert board["preview"][0] == "shoot_now: Leader"
    assert queue["title"] == "Comparison session queue"
    assert queue["first_batch_name"] == "Leader"
    assert queue["preview"][0] == "1. Leader (shoot_now)"


def test_build_batch_comparison_session_manifest_summarizes_priority_buckets():
    manifest = batch_workspace_module._build_batch_comparison_session_manifest(
        {
            "title": "Comparison campaign board",
            "summary": "Leader Node A | band behind | mode ranking_session | Challenge the current leader under matched conditions.",
            "rows": [
                {
                    "batch_name": "Leader",
                    "priority": "shoot_now",
                    "rank": 1,
                    "rationale": "Run first.",
                },
                {
                    "batch_name": "Candidate",
                    "priority": "confirm",
                    "rank": 2,
                    "rationale": "Needs one more repeat.",
                },
                {
                    "batch_name": "Watch",
                    "priority": "reject_watch",
                    "rank": 3,
                    "rationale": "Pressure watch.",
                },
            ],
        },
        {
            "title": "Comparison session queue",
            "mode": "ranking_session",
            "objective": "Challenge the current leader under matched conditions.",
            "first_batch_name": "Leader",
            "queue": [
                {
                    "slot": 1,
                    "batch_name": "Leader",
                    "priority": "shoot_now",
                    "rationale": "Run first.",
                },
            ],
        },
        {
            "title": "Comparison action plan",
            "primary_action": "Run a same-day head-to-head against Leader before promoting any other batch.",
        },
        {
            "mode": "ranking_session",
            "objective": "Challenge the current leader under matched conditions.",
        },
    )

    assert manifest["title"] == "Comparison session manifest"
    assert manifest["primary_bucket"] == "shoot_now"
    assert manifest["first_batch_name"] == "Leader"
    assert manifest["primary_action"].startswith("Run a same-day head-to-head")
    assert manifest["buckets"]["confirm"][0]["batch_name"] == "Candidate"
    assert "Ready now: 1" in manifest["summary"]
    assert manifest["queue_preview"][0] == "1. Leader (shoot_now)"
    assert manifest["lane_summaries"][0]["summary"] == "shoot_now: Leader"


def test_build_batch_comparison_next_session_brief_points_to_first_action_and_hold_back():
    brief = batch_workspace_module._build_batch_comparison_next_session_brief(
        {
            "title": "Comparison session manifest",
            "primary_bucket": "shoot_now",
            "first_batch_name": "Leader",
            "primary_action": "Run a same-day head-to-head against Leader before promoting any other batch.",
            "queue_preview": ["1. Leader (shoot_now)", "2. Candidate (confirm)"],
            "lane_summaries": [
                {"bucket": "shoot_now", "summary": "shoot_now: Leader"},
                {"bucket": "hold", "summary": "hold: Candidate"},
            ],
        },
        {
            "title": "Comparison session queue",
            "first_batch_name": "Leader",
        },
        {
            "highest_priority": "Same setup on both batches",
        },
        {
            "primary_action": "Run a same-day head-to-head against Leader before promoting any other batch.",
        },
    )

    assert brief["title"] == "Comparison next session brief"
    assert brief["first_batch_name"] == "Leader"
    assert brief["primary_bucket"] == "shoot_now"
    assert brief["compare_first"] == "Same setup on both batches"
    assert brief["hold_back"] == "hold: Candidate"


def test_build_batch_comparison_today_plan_summarizes_today_priority():
    plan = batch_workspace_module._build_batch_comparison_today_plan(
        {
            "title": "Comparison next session brief",
            "first_batch_name": "Leader",
            "primary_bucket": "shoot_now",
            "primary_action": "Run a same-day head-to-head against Leader before promoting any other batch.",
            "compare_first": "Same setup on both batches",
            "hold_back": "hold: Candidate",
        },
        {
            "first_batch_name": "Leader",
            "primary_bucket": "shoot_now",
        },
    )

    assert plan["title"] == "Comparison today plan"
    assert (
        plan["summary"]
        == "Run Leader first | verify Same setup on both batches | hold back hold: Candidate"
    )
    assert plan["primary_action"].startswith("Run a same-day head-to-head")


def test_build_batch_comparison_workboard_collects_top_level_session_state():
    workboard = batch_workspace_module._build_batch_comparison_workboard(
        {"first_batch_name": "Leader", "summary": "Leader board summary"},
        {
            "first_batch_name": "Leader",
            "primary_bucket": "shoot_now",
            "summary": "Manifest summary",
            "primary_action": "Run a same-day head-to-head against Leader before promoting any other batch.",
            "lane_summaries": [{"bucket": "shoot_now", "summary": "shoot_now: Leader"}],
            "queue_preview": ["1. Leader (shoot_now)"],
        },
        {
            "first_batch_name": "Leader",
            "primary_bucket": "shoot_now",
            "primary_action": "Run a same-day head-to-head against Leader before promoting any other batch.",
            "hold_back": "hold: Candidate",
        },
        {
            "summary": "Run Leader first | verify Same setup on both batches | hold back hold: Candidate",
            "primary_action": "Run a same-day head-to-head against Leader before promoting any other batch.",
        },
    )

    assert workboard["title"] == "Comparison workboard"
    assert workboard["first_batch_name"] == "Leader"
    assert workboard["primary_bucket"] == "shoot_now"
    assert workboard["hold_back"] == "hold: Candidate"
    assert workboard["status_label"] == "Ready to run"


def test_format_batch_comparison_workboard_summary_compacts_core_state():
    summary = batch_workspace_module._format_batch_comparison_workboard_summary(
        {
            "status_label": "Ready to run",
            "first_batch_name": "Leader",
            "primary_bucket": "shoot_now",
            "hold_back": "hold: Candidate",
        }
    )

    assert (
        summary
        == "Ready to run | run Leader first | bucket shoot_now | hold back hold: Candidate"
    )


def test_build_batch_comparison_workboard_lane_map_fills_known_lanes():
    lane_map = batch_workspace_module._build_batch_comparison_workboard_lane_map(
        {
            "lane_summaries": [
                {"bucket": "shoot_now", "summary": "shoot_now: Leader"},
                {"bucket": "confirm", "summary": "confirm: Candidate"},
                {"bucket": "pause", "summary": "pause: Safety Watch"},
            ]
        }
    )

    assert lane_map["shoot_now"] == "shoot_now: Leader"
    assert lane_map["confirm"] == "confirm: Candidate"
    assert lane_map["hold"] == "-"
    assert lane_map["pause"] == "pause: Safety Watch"
    assert lane_map["reject_watch"] == "-"


def test_build_batch_comparison_workboard_display_builds_today_and_queue_text():
    display = batch_workspace_module._build_batch_comparison_workboard_display(
        {
            "status_label": "Ready to run",
            "summary": "Run Leader first | verify Same setup on both batches | hold back hold: Candidate",
            "first_batch_name": "Leader",
            "primary_bucket": "shoot_now",
            "primary_action": "Run a same-day head-to-head against Leader before promoting any other batch.",
            "hold_back": "hold: Candidate",
            "queue_preview": ["1. Leader (shoot_now)", "2. Candidate (confirm)"],
            "counts": {"shoot_now": 1, "confirm": 1, "hold": 1},
            "lane_summaries": [
                {"bucket": "shoot_now", "summary": "shoot_now: Leader"},
                {"bucket": "confirm", "summary": "confirm: Candidate"},
                {"bucket": "hold", "summary": "hold: Candidate"},
            ],
        }
    )

    assert display["today_summary"].startswith("Ready to run | Run Leader first")
    assert display["queue_text"] == "1. Leader (shoot_now) | 2. Candidate (confirm)"
    assert display["counts_text"] == "shoot_now 1 | confirm 1 | hold 1"
    assert (
        display["lanes_summary"]
        == "shoot_now: Leader | confirm: Candidate | hold: Candidate"
    )
    assert display["primary_lane_text"] == "shoot_now: Leader"
    assert display["board_hint"].startswith(
        "shoot_now: Leader | Run a same-day head-to-head"
    )
    assert display["tone"] == "ready"
    assert display["confirm"] == "confirm: Candidate"


def test_build_batch_comparison_workboard_copy_text_supports_today_and_queue_modes():
    display = {
        "status": "Ready to run",
        "today_summary": "Ready to run | Run Leader first",
        "primary_lane_text": "shoot_now: Leader",
        "action": "Run a same-day head-to-head against Leader before promoting any other batch.",
        "hold_back": "hold: Candidate",
        "counts_text": "shoot_now 1 | confirm 1 | hold 1",
        "queue_text": "1. Leader (shoot_now) | 2. Candidate (confirm)",
        "lanes_summary": "shoot_now: Leader | confirm: Candidate | hold: Candidate",
    }

    today_text = batch_workspace_module._build_batch_comparison_workboard_copy_text(
        display,
        mode="today",
    )
    queue_text = batch_workspace_module._build_batch_comparison_workboard_copy_text(
        display,
        mode="queue",
    )
    full_text = batch_workspace_module._build_batch_comparison_workboard_copy_text(
        display,
        mode="full",
    )

    assert "Ready to run" in today_text
    assert "shoot_now: Leader" in today_text
    assert "hold: Candidate" in today_text
    assert "shoot_now 1 | confirm 1 | hold 1" in queue_text
    assert "1. Leader (shoot_now)" in queue_text
    assert "shoot_now: Leader | confirm: Candidate | hold: Candidate" in queue_text
    assert "Ready to run | Run Leader first" in full_text
    assert (
        "Run a same-day head-to-head against Leader before promoting any other batch."
        in full_text
    )


def test_build_batch_comparison_lane_title_marks_focus_and_done_state():
    title = batch_workspace_module._build_batch_comparison_lane_title(
        "confirm",
        2,
        completed=True,
        selected=True,
    )

    assert title == "confirm (2) [focused, done]"


def test_workboard_lane_ui_state_roundtrips_via_settings(monkeypatch):
    _FakeSettings.store = {}
    monkeypatch.setattr(batch_workspace_module, "QSettings", _FakeSettings)

    batch_workspace_module._store_workboard_lane_ui_state(
        44,
        {"confirm", "shoot_now"},
        "confirm",
    )
    completed, selected = batch_workspace_module._load_workboard_lane_ui_state(44)

    assert completed == {"confirm", "shoot_now"}
    assert selected == "confirm"


def test_workboard_lane_ui_state_filters_invalid_values(monkeypatch):
    _FakeSettings.store = {
        "batch_workspace/workboard/44/completed": "confirm,invalid,pause",
        "batch_workspace/workboard/44/selected": "not-a-lane",
    }
    monkeypatch.setattr(batch_workspace_module, "QSettings", _FakeSettings)

    completed, selected = batch_workspace_module._load_workboard_lane_ui_state(44)

    assert completed == {"confirm", "pause"}
    assert selected == ""


def test_store_workboard_lane_ui_state_can_clear_values(monkeypatch):
    _FakeSettings.store = {}
    monkeypatch.setattr(batch_workspace_module, "QSettings", _FakeSettings)

    batch_workspace_module._store_workboard_lane_ui_state(
        44,
        set(),
        "",
    )
    completed, selected = batch_workspace_module._load_workboard_lane_ui_state(44)

    assert completed == set()
    assert selected == ""


def test_build_batch_evidence_basis_mentions_batch_comparison_summary():
    summary = batch_workspace_module._build_batch_evidence_basis(
        {"charge_weight_grains": 43.0, "coal_mm": 71.2},
        {
            "score": 81.0,
            "batch_comparison_basis": {
                "available": True,
                "ranking_state": "trailing_candidate",
                "current_rank": 2,
                "count": 3,
                "leader_batch_name": "Proven Batch",
                "leader_gap_score": 7.5,
                "summary": "Current Batch currently ranks 2 of 3 comparable batches and trails Proven Batch by about 7.5 score points.",
                "top_candidates": [{"batch_name": "Proven Batch"}],
            },
            "batch_comparison_advisory": {
                "title": "Trailing stronger evidence",
                "message": "Current Batch currently ranks 2 of 3 comparable batches and trails Proven Batch by about 7.5 score points.",
                "recommended_action": "Not ranking-ready yet",
            },
            "batch_comparison_protocol": {
                "title": "Head-to-head catch-up test",
                "primary_action": "Run a same-day head-to-head against Proven Batch before promoting this batch.",
                "shot_plan": "Shoot the current batch and the leader with the same rifle setup, same distance, same support, and matched chrono plus measured groups.",
            },
            "batch_comparison_explanation": {
                "limiting_factor": "validation_depth",
                "reason": "The batch trails Proven Batch by about 7.5 weighted comparison-score points.",
                "next_measurement": "Repeat the same setup with matched chrono and measured groups.",
            },
            "batch_comparison_verdict": {
                "label": "Do not promote yet",
                "summary": "This batch should stay behind Proven Batch until the comparison gap is tested under matched conditions.",
            },
            "batch_comparison_acceptance": {
                "label": "Not accepted yet",
                "summary": "This batch should not replace the current leading candidate until the remaining comparison gaps are closed.",
                "next_gate": "Repeat the same setup with matched chrono and measured groups.",
                "remaining_gaps": [
                    "The batch still trails Proven Batch under the weighted comparison.",
                ],
            },
            "batch_comparison_acceptance_progress": {
                "level": "partial",
                "score": 44.5,
                "summary": "Acceptance progress is still partial, so the batch should keep earning evidence before replacement.",
                "next_target": "Repeat the same setup with matched chrono and measured groups.",
            },
            "batch_comparison_next_test": {
                "title": "Catch-up test vs Proven Batch",
                "summary": "Run the current batch directly against Proven Batch under matched conditions before it is allowed to move up.",
                "primary_action": "Run a same-day head-to-head against Proven Batch before promoting this batch.",
                "check_first": "Same setup on both batches",
            },
            "batch_comparison_status_board": {
                "headline": "Still chasing the leader",
                "readiness_band": "behind",
                "summary": "Still chasing the leader | Rank 2/3 | Leader: Proven Batch | Progress: partial (44.5/100) | Verdict: Do not promote yet",
            },
            "batch_comparison_profile_priority": {
                "title": "Competition comparison priority",
                "emphasis": "Favor repeatability, matched evidence, and setup control over one attractive result.",
                "guardrail": "Do not rank a batch higher until the same-day repeat and matched chrono/group evidence agree.",
            },
            "batch_comparison_mission_brief": {
                "title": "Comparison mission brief",
                "mission": "Still chasing the leader: Treat the next outing as a matched ranking test, not a free-form tuning session.",
                "primary_action": "Run a same-day head-to-head against Proven Batch before promoting this batch.",
                "success_marker": "A matched repeat string that still holds precision and consistency against the current leader.",
            },
            "batch_comparison_portfolio": {
                "title": "Comparison portfolio",
                "focus": "Use the next session to test whether the current batch can close the gap to Proven Batch.",
                "status_headline": "Still chasing the leader",
            },
            "batch_comparison_session_strategy": {
                "title": "Comparison session strategy",
                "mode": "ranking_session",
                "objective": "Challenge the current leader under matched conditions.",
            },
            "batch_comparison_campaign_view": {
                "title": "Comparison campaign view",
                "summary": "Leader Proven Batch | band behind | mode ranking_session | Challenge the current leader under matched conditions.",
            },
            "batch_comparison_action_plan": {
                "title": "Comparison action plan",
                "summary": "Challenge the current leader under matched conditions.",
                "primary_action": "Run a same-day head-to-head against Proven Batch before promoting this batch.",
            },
            "batch_comparison_campaign_board": {
                "title": "Comparison campaign board",
                "summary": "Leader Proven Batch | band behind | mode ranking_session | Challenge the current leader under matched conditions.",
                "preview": ["shoot_now: Proven Batch", "confirm: Current Batch"],
            },
            "batch_comparison_session_queue": {
                "title": "Comparison session queue",
                "mode": "ranking_session",
                "first_batch_name": "Proven Batch",
                "preview": [
                    "1. Proven Batch (shoot_now)",
                    "2. Current Batch (confirm)",
                ],
            },
            "batch_comparison_session_manifest": {
                "title": "Comparison session manifest",
                "summary": "Leader Proven Batch | band behind | mode ranking_session | Challenge the current leader under matched conditions. | Ready now: 1 | Confirm next: 1",
                "primary_bucket": "shoot_now",
                "first_batch_name": "Proven Batch",
                "queue_preview": [
                    "1. Proven Batch (shoot_now)",
                    "2. Current Batch (confirm)",
                ],
                "lane_summaries": [
                    {
                        "bucket": "shoot_now",
                        "count": 1,
                        "summary": "shoot_now: Proven Batch",
                    },
                    {
                        "bucket": "confirm",
                        "count": 1,
                        "summary": "confirm: Current Batch",
                    },
                ],
            },
            "batch_comparison_next_session_brief": {
                "title": "Comparison next session brief",
                "summary": "Start with Proven Batch | bucket shoot_now | check Same setup on both batches",
                "first_batch_name": "Proven Batch",
                "primary_bucket": "shoot_now",
                "primary_action": "Run a same-day head-to-head against Proven Batch before promoting this batch.",
                "hold_back": "hold: Current Batch",
            },
            "batch_comparison_today_plan": {
                "title": "Comparison today plan",
                "summary": "Run Proven Batch first | verify Same setup on both batches | hold back hold: Current Batch",
                "first_batch_name": "Proven Batch",
                "primary_bucket": "shoot_now",
                "primary_action": "Run a same-day head-to-head against Proven Batch before promoting this batch.",
            },
            "batch_comparison_workboard": {
                "title": "Comparison workboard",
                "summary": "Run Proven Batch first | verify Same setup on both batches | hold back hold: Current Batch",
                "status_label": "Ready to run",
                "first_batch_name": "Proven Batch",
                "primary_bucket": "shoot_now",
                "primary_action": "Run a same-day head-to-head against Proven Batch before promoting this batch.",
                "hold_back": "hold: Current Batch",
            },
            "batch_comparison_checklist": {
                "title": "Comparison checklist",
                "highest_priority": "Same setup on both batches",
            },
            "batch_comparison_scorecard": {
                "swing_factor": "evidence_quality",
                "summary": "Current Batch mainly trails Proven Batch on evidence quality.",
                "delta_precision": 0.6,
                "delta_evidence_quality": -37.0,
                "delta_readiness": -12.0,
            },
            "batch_comparison_confidence": {
                "level": "thin",
                "score": 48.0,
                "summary": "The current batch comparison is directionally useful, but still too thin for hard promotion decisions.",
            },
            "batch_comparison_learning_note": {
                "plain_summary": "Evidence quality is currently the biggest separator between the compared batches.",
                "takeaway": "When evidence quality is the swing factor, add cleaner matched data before trusting the leaderboard.",
            },
        },
        [{"group_size_mm": 14.0}],
        {"avg": 2798.0},
    )

    assert "comparison state: trailing_candidate" in summary["message"]
    assert "batch rank: 2/3" in summary["message"]
    assert (
        "comparison: Current Batch currently ranks 2 of 3 comparable batches"
        in summary["message"]
    )
    assert "comparison leader: Proven Batch (7.5 score ahead)" in summary["message"]
    assert "top candidate: Proven Batch" in summary["message"]
    assert "comparison advisory: Trailing stronger evidence" in summary["message"]
    assert "comparison next gate: Not ranking-ready yet" in summary["message"]
    assert "comparison protocol: Head-to-head catch-up test" in summary["message"]
    assert (
        "comparison action: Run a same-day head-to-head against Proven Batch before promoting this batch."
        in summary["message"]
    )
    assert "comparison bottleneck: validation_depth" in summary["message"]
    assert (
        "comparison next measurement: Repeat the same setup with matched chrono and measured groups."
        in summary["message"]
    )
    assert "comparison verdict: Do not promote yet" in summary["message"]
    assert "comparison acceptance: Not accepted yet" in summary["message"]
    assert (
        "comparison acceptance gate: Repeat the same setup with matched chrono and measured groups."
        in summary["message"]
    )
    assert (
        "comparison acceptance gap: The batch still trails Proven Batch under the weighted comparison."
        in summary["message"]
    )
    assert "acceptance progress: partial (44.5/100)" in summary["message"]
    assert (
        "acceptance next target: Repeat the same setup with matched chrono and measured groups."
        in summary["message"]
    )
    assert "comparison next test: Catch-up test vs Proven Batch" in summary["message"]
    assert "comparison board: Still chasing the leader" in summary["message"]
    assert "comparison readiness band: behind" in summary["message"]
    assert "comparison profile: Competition comparison priority" in summary["message"]
    assert (
        "comparison mission brief: Still chasing the leader: Treat the next outing as a matched ranking test"
        in summary["message"]
    )
    assert "comparison portfolio: Comparison portfolio" in summary["message"]
    assert (
        "comparison session strategy: Comparison session strategy" in summary["message"]
    )
    assert "comparison campaign: Comparison campaign view" in summary["message"]
    assert "comparison action plan: Comparison action plan" in summary["message"]
    assert "comparison campaign board: Comparison campaign board" in summary["message"]
    assert (
        "comparison board preview: shoot_now: Proven Batch | confirm: Current Batch"
        in summary["message"]
    )
    assert "comparison session queue: Comparison session queue" in summary["message"]
    assert (
        "comparison queue preview: 1. Proven Batch (shoot_now) | 2. Current Batch (confirm)"
        in summary["message"]
    )
    assert (
        "comparison session manifest: Comparison session manifest" in summary["message"]
    )
    assert "comparison manifest bucket: shoot_now" in summary["message"]
    assert (
        "comparison manifest preview: 1. Proven Batch (shoot_now) | 2. Current Batch (confirm)"
        in summary["message"]
    )
    assert (
        "comparison manifest lanes: shoot_now: Proven Batch | confirm: Current Batch"
        in summary["message"]
    )
    assert (
        "comparison next session brief: Comparison next session brief"
        in summary["message"]
    )
    assert (
        "comparison next session hold-back: hold: Current Batch" in summary["message"]
    )
    assert "comparison today plan: Comparison today plan" in summary["message"]
    assert (
        "comparison today summary: Run Proven Batch first | verify Same setup on both batches | hold back hold: Current Batch"
        in summary["message"]
    )
    assert "comparison workboard: Comparison workboard" in summary["message"]
    assert "comparison workboard status: Ready to run" in summary["message"]
    assert "comparison workboard hold-back: hold: Current Batch" in summary["message"]
    assert "comparison checklist: Comparison checklist" in summary["message"]
    assert "comparison swing factor: evidence_quality" in summary["message"]
    assert (
        "comparison scorecard: Current Batch mainly trails Proven Batch on evidence quality."
        in summary["message"]
    )
    assert "comparison confidence: thin (48.0/100)" in summary["message"]
    assert (
        "comparison lesson: Evidence quality is currently the biggest separator"
        in summary["message"]
    )


def test_format_batch_setup_label_combines_barrel_and_configuration():
    assert (
        batch_workspace_module._format_batch_setup_label(
            {
                "barrel_name": "26in Match Pipe",
                "barrel_configuration_name": "Suppressed",
            }
        )
        == "26in Match Pipe / Suppressed"
    )


def test_build_batch_session_primer_payload_uses_batch_and_workflow_context():
    payload = batch_workspace_module._build_batch_session_primer_payload(
        {
            "id": 41,
            "ammo_profile_id": 19,
            "rifle_id": 7,
            "charge_weight_grains": 42.4,
            "load_session_id": 33,
            "batch_name": "Node A",
        },
        {"workflow_id": 12, "load_session_id": 33},
        batch_session_id=99,
        session_name="Batch A",
        session_date="2026-04-08",
        primer_review_enabled=True,
        primer_image_paths=["reports/primer-a.jpg", "reports/primer-b.jpg"],
        primer_image_quality="good",
        primer_image_observation="normal reference for this rifle",
        primer_image_confidence="medium",
    )

    assert payload["ammo_profile_id"] == 19
    assert payload["charge_weight"] == 42.4
    assert payload["workflow_id"] == 12
    assert payload["load_session_id"] == 33
    assert payload["session_name"] == "Batch A"
    assert payload["primer_image_path"] == "reports/primer-a.jpg"
    assert payload["batch_id"] == 41
    assert payload["batch_session_id"] == 99
    assert payload["rifle_id"] == 7
    assert "2 primer images in this reference set" in payload["notes"]


def test_build_batch_session_primer_payload_skips_when_feature_disabled():
    payload = batch_workspace_module._build_batch_session_primer_payload(
        {
            "id": 41,
            "ammo_profile_id": 19,
            "rifle_id": 7,
            "charge_weight_grains": 42.4,
        },
        {"workflow_id": 12},
        batch_session_id=99,
        session_name="Batch A",
        session_date="2026-04-08",
        primer_review_enabled=False,
        primer_image_paths=["reports/primer-a.jpg"],
        primer_image_quality="good",
        primer_image_observation="ignored because disabled",
        primer_image_confidence="medium",
    )

    assert payload == {}


def test_build_batch_evidence_basis_mentions_primer_reference_images():
    summary = batch_workspace_module._build_batch_evidence_basis(
        {"charge_weight_grains": 43.0, "coal_mm": 71.2},
        {},
        [
            {
                "analysis_json": {
                    "primer_image_review": {
                        "images": ["reports/primer-a.jpg", "reports/primer-b.jpg"],
                        "observation": "normal reference for this rifle",
                    }
                }
            }
        ],
        {},
    )

    assert (
        "2 primer reference images are linked across 1 batch session"
        in summary["message"]
    )


def test_format_batch_session_primer_summary_mentions_image_count():
    summary = batch_workspace_module._format_batch_session_primer_summary(
        {
            "primer_image_review": {
                "images": [
                    "reports/primer-a.jpg",
                    "reports/primer-b.jpg",
                    "reports/primer-c.jpg",
                ],
                "observation": "normal reference for this rifle",
            }
        }
    )

    assert "3 images" in summary
    assert "normal reference for this rifle" in summary


def test_format_batch_session_primer_summary_mentions_disabled_state():
    summary = batch_workspace_module._format_batch_session_primer_summary(
        {"primer_image_review": {"enabled": False}}
    )

    assert summary == "primer review disabled for this session"
