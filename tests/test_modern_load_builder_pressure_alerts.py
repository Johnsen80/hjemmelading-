from types import SimpleNamespace

from src.modules import modern_load_builder as mlb_module


def test_summarize_pressure_risk_reports_near_max_warning():
    summary = mlb_module.summarize_pressure_risk(
        {
            "peak_pressure_psi": 58000,
            "max_pressure_psi": 62000,
            "safety_margin_percent": 6.0,
            "warnings": [],
        }
    )

    assert summary["level"] == "critical"
    assert "High pressure risk" in summary["title"]


def test_summarize_pressure_risk_prioritizes_spike_warning():
    summary = mlb_module.summarize_pressure_risk(
        {
            "peak_pressure_psi": 50000,
            "max_pressure_psi": 62000,
            "safety_margin_percent": 19.0,
            "warnings": [
                'Neck tension 0.0060" er for STRAM! Kan gi ES 25-40 fps og trykkspiker.'
            ],
        }
    )

    assert summary["level"] == "critical"
    assert summary["title"] == "Pressure spike risk"
    assert "trykkspiker" in summary["message"]


def test_update_visualization_applies_profile_scoped_calibration(monkeypatch):
    captured: dict[str, object] = {}

    class _Label:
        def setText(self, value):
            captured["fit_summary"] = value

    class _FakeDb:
        def execute_query(self, query, params=()):
            normalized = " ".join(query.split())
            if "FROM engine_calibrations" in normalized:
                assert params == (11,)
                return [{"slope": 1.01, "intercept": 5.0, "mse": 4.0}]
            return []

    class _Widget(mlb_module.ModernLoadBuilder):
        def __init__(self):
            super().__init__()
            self.rifle_data = {"id": 1}
            self.bullet_data = {"id": 2}
            self.powder_data = {"id": 3}
            self.current_charge = 42.0
            self.coal_mm = 71.0
            self.cbto_mm = 68.0
            self.current_ammo_profile_id = 11
            self.component_fit_label = _Label()
            self.db = _FakeDb()
            self._get_active_barrel_id = lambda: None
            self._refresh_bullet_action_button = lambda: None
            self._build_service_analysis = lambda: None
            self._refresh_runtime_context_summary = lambda: None
            self._refresh_service_recommendation_callout = lambda: None
            self._refresh_recommendation_state_panel = lambda: None
            self.update_pressure_graph = lambda result: captured.__setitem__(
                "pressure", result
            )
            self.update_velocity_graph = lambda result: captured.__setitem__(
                "velocity", result
            )
            self.update_stats = lambda result: captured.__setitem__("stats", result)

        @property
        def engine(self):
            return SimpleNamespace(
                calculate_load=lambda *args, **kwargs: {
                    "pressure_curve": [(0.0, 1000.0), (1.0, 2000.0)],
                    "velocity_curve": [(0.0, 0.0), (24.0, 2800.0)],
                    "muzzle_velocity_fps": 2800.0,
                    "peak_pressure_psi": 55000.0,
                    "max_pressure_psi": 62000.0,
                }
            )

        def _build_component_fit_assessment(self, result=None):
            return ("fit ok", [])

        def _refresh_seating_depth_advisor(self, result=None):
            return None

    widget = _Widget()

    monkeypatch.setattr(mlb_module, "air_density_ratio", None, raising=False)

    mlb_module.ModernLoadBuilder.update_visualization(widget)

    assert widget._latest_visual_result["muzzle_velocity_fps"] == 2833.0
    assert widget._latest_visual_result["velocity_curve"][1][1] == 2833.0
    assert widget._latest_visual_result["_calibration_mse"] == 4.0


def test_list_rifles_for_selection_uses_mm_schema_and_derives_cm():
    class _FakeDb:
        def __init__(self):
            self.query = ""

        def execute_query(self, query, params=()):
            self.query = query
            return [
                {
                    "id": 1,
                    "name": "Match Rifle",
                    "caliber": "6.5 Creedmoor",
                    "twist_rate": "1:8",
                    "barrel_length_mm": 610.0,
                }
            ]

    class _Widget(mlb_module.ModernLoadBuilder):
        def __init__(self):
            super().__init__()
            self.db = _FakeDb()
            self._coerce_float = mlb_module.ModernLoadBuilder._coerce_float

    widget = _Widget()
    rifles = widget._list_rifles_for_selection()

    assert "barrel_length_mm" in widget.db.query
    assert "barrel_length_cm" not in widget.db.query
    assert rifles[0]["barrel_length_cm"] == 61.0


def test_build_learning_workflow_guidance_prioritizes_powder_lot_verification():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "learning": {
                "aggregate": {
                    "confidence_label": "tidlig læring",
                    "weakest_link": "kruttlot",
                    "next_focus": "verify_component_lot",
                },
                "session": {
                    "summary": {
                        "next_focus": "verify_component_lot",
                    }
                },
            }
        }
    )

    assert "Learning priority" in guidance["header"]
    assert "powder lot" in guidance["header"]
    assert "0.2 gr under" in guidance["setup"]
    assert "chrono the first 5 shots" in guidance["card_hint"]


def test_build_learning_workflow_guidance_can_use_smart_engine_guidance_without_learning_focus():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "smart_engine": {
                "engine_result": {
                    "candidate_profile": {
                        "robustness_level": "low",
                        "node_fit": "unclear",
                    },
                    "harmonics": {
                        "stability_tier": "sensitive",
                    },
                    "bullet_fit": {
                        "level": "warning",
                        "fit_score": 63.0,
                        "message": "The setup may work, but the margin is limited.",
                    },
                    "chamber_jump": {
                        "jump_band": "tight",
                        "current_jump_mm": 0.1,
                        "summary": "Current jump 0.100 mm sits in tight.",
                    },
                    "decisions": {
                        "next_test": {
                            "recommended_action": "collect_matched_group_and_chrono",
                            "why": "Thin evidence should be strengthened before stronger tuning.",
                        },
                        "guidance": {
                            "title": "Collect matched evidence before stronger claims",
                            "setup_line": "Capture one matched chrono string and one measured group under the same setup and conditions.",
                        },
                        "validation_gate": {
                            "label": "Needs matched evidence",
                            "next_gate": "Collect one clean matched evidence pass.",
                        },
                        "execution_plan": {
                            "summary": "Collect matched evidence before stronger claims: Shoot one matched chrono string and one measured group under the same setup and conditions.",
                            "session_type": "evidence_control",
                            "keep_constant": [
                                "Keep charge and seating fixed for the control string."
                            ],
                            "capture": ["One matched chrono string"],
                            "success_criteria": "The engine gets one clean matched evidence set before stronger conclusions are made.",
                        },
                        "do_not_change_yet": [
                            "Do not promote or reject the load from thin evidence alone."
                        ],
                        "blocked_by": [
                            {
                                "kind": "evidence",
                                "title": "Evidence block",
                            }
                        ],
                        "recommendation_confidence": {
                            "level": "low",
                            "score": 44.0,
                            "summary": "The engine recommendation is still conservative because one or more gates remain open.",
                            "uncertainty": "evidence",
                        },
                    },
                }
            },
            "learning": {
                "aggregate": {},
                "session": {"summary": {}},
            },
        }
    )

    assert (
        "collect matched evidence before stronger claims" in guidance["header"].lower()
    )
    assert (
        "Capture one matched chrono string and one measured group" in guidance["setup"]
    )
    assert "Engine next test: collect_matched_group_and_chrono" in guidance["card_hint"]
    assert "Engine gate: Needs matched evidence" in guidance["card_hint"]
    assert (
        "Engine protocol: Collect matched evidence before stronger claims"
        in guidance["card_hint"]
    )
    assert (
        "Engine keep constant: Keep charge and seating fixed for the control string."
        in guidance["card_hint"]
    )
    assert (
        "Engine hold: Do not promote or reject the load from thin evidence alone."
        in guidance["card_hint"]
    )
    assert "Engine blocker: Evidence block" in guidance["card_hint"]
    assert (
        "Engine confidence: low (44.0/100) - uncertainty evidence"
        in guidance["card_hint"]
    )
    assert "Engine bullet fit: warning (63.0/100)" in guidance["card_hint"]
    assert "Engine jump: tight (0.100 mm)" in guidance["card_hint"]
    assert "Capture: One matched chrono string" in guidance["setup"]


def test_build_learning_workflow_guidance_prioritizes_velocity_capture():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "smart_engine": {
                "engine_result": {
                    "candidate_profile": {
                        "robustness_level": "moderate",
                        "node_fit": "developing",
                    },
                    "harmonics": {
                        "stability_tier": "stable",
                    },
                    "decisions": {
                        "next_test": {
                            "recommended_action": "confirm_node_window",
                            "why": "Confirm the current node window conservatively.",
                        }
                    },
                }
            },
            "learning": {
                "aggregate": {
                    "confidence_label": "rå modell",
                    "weakest_link": "pipe",
                    "next_focus": "capture_measured_velocity",
                },
                "session": {
                    "summary": {
                        "next_focus": "capture_measured_velocity",
                    }
                },
            },
        }
    )

    assert "capture measured velocity" in guidance["header"]
    assert "5-shot chrono confirmation" in guidance["setup"]
    assert (
        "Engine robustness: moderate, node fit developing, harmonics stable"
        in guidance["card_hint"]
    )
    assert "Engine next test: confirm_node_window" in guidance["card_hint"]


def test_build_learning_workflow_guidance_shows_engine_baseline_return_target():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "smart_engine": {
                "engine_result": {
                    "branch_advisory": {
                        "label": "Custom branch",
                        "compare_mode": "return_before_compare",
                        "display_line": "Custom branch (return_before_compare)",
                        "action_line": "Return charge toward 42.00 gr before treating this as the same candidate.",
                    },
                    "return_targets": {
                        "charge": {
                            "label": "42.00 gr",
                            "return_line": "Return charge toward 42.00 gr before treating this as the same candidate.",
                        }
                    },
                    "baseline_control": {
                        "charge_alignment": "outside",
                        "charge_target_label": "42.00 gr",
                        "active_return_line": "Return charge toward 42.00 gr before treating this as the same candidate.",
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
                        "guidance": {
                            "title": "Return to the frozen charge baseline first",
                            "setup_line": "Return to the frozen charge baseline before trusting the comparison, or prove a new charge node as a fresh branch.",
                        },
                        "validation_gate": {
                            "label": "Return to frozen baseline",
                            "next_gate": "Return to the frozen baseline or prove a fresh custom baseline.",
                        },
                        "execution_plan": {
                            "summary": "Return to the frozen charge baseline or run a fresh charge confirmation before treating the setup as the same candidate.",
                            "session_type": "charge_baseline_recovery",
                            "keep_constant": [
                                "Do not change seating while re-establishing the charge baseline."
                            ],
                            "capture": [
                                "One short confirmation string at the frozen charge baseline"
                            ],
                            "success_criteria": "The baseline charge repeats cleanly enough that later charge comparisons can be trusted again.",
                        },
                    },
                }
            },
            "learning": {
                "aggregate": {},
                "session": {"summary": {}},
            },
        }
    )

    assert "return to the frozen charge baseline first" in guidance["header"].lower()
    assert "Charge target: 42.00 gr" in guidance["setup"]
    assert (
        "Baseline control: Return charge toward 42.00 gr before treating this as the same candidate."
        in guidance["setup"]
    )
    assert (
        "Engine branch: Custom branch (return_before_compare)" in guidance["card_hint"]
    )
    assert (
        "Engine baseline control: Return charge toward 42.00 gr before treating this as the same candidate."
        in guidance["card_hint"]
    )


def test_build_learning_workflow_guidance_uses_engine_evidence_diagnostics_for_missing_measurements():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "smart_engine": {
                "engine_result": {
                    "evidence_diagnostics": {
                        "status": "needs_measurement",
                        "items": [
                            "Session still lacks measured chronograph data for the active setup.",
                            "Session still lacks measured grouping data for the active setup.",
                        ],
                        "focus_areas": [
                            "velocity validation",
                            "grouping",
                            "data trust",
                        ],
                        "suggested_action": "Capture a chronograph string for the current setup before treating the node as verified.",
                    },
                    "candidate_profile": {
                        "robustness_level": "low",
                        "node_fit": "unclear",
                    },
                    "harmonics": {
                        "stability_tier": "sensitive",
                    },
                }
            },
            "learning": {
                "aggregate": {},
                "session": {"summary": {}},
            },
        }
    )

    assert "close the missing evidence first" in guidance["header"].lower()
    assert (
        "Capture a chronograph string for the current setup before treating the node as verified."
        in guidance["setup"]
    )
    assert (
        "Engine evidence: needs_measurement - Session still lacks measured chronograph data for the active setup."
        in guidance["card_hint"]
    )
    assert "Engine evidence focus: velocity validation" in guidance["card_hint"]


def test_build_learning_workflow_guidance_prioritizes_pressure_confirmation():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "context": {
                "usage_profile_name": "Competition",
            },
            "learning": {
                "aggregate": {
                    "confidence_label": "tidlig læring",
                    "weakest_link": "kruttlot",
                },
                "session": {
                    "summary": {
                        "pressure_level": "warning",
                        "input_quality_level": "medium",
                    }
                },
            },
            "evidence": {
                "summary": {
                    "chronograph_import_count": 1,
                    "test_result_count": 1,
                }
            },
            "recommendation": {
                "control_state": {
                    "trust_label": "medium",
                }
            },
        }
    )

    assert "verify pressure before optimization" in guidance["header"]
    assert "chrono the first 5 shots" in guidance["setup"]
    assert "Pressure state: warning" in guidance["card_hint"]


def test_build_learning_workflow_guidance_prioritizes_hunting_cold_bore_validation():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "context": {
                "usage_profile_name": "Hunting",
            },
            "learning": {
                "aggregate": {
                    "confidence_label": "brukbar trygghet",
                },
                "session": {
                    "summary": {
                        "input_quality_level": "medium",
                    }
                },
            },
            "evidence": {
                "summary": {
                    "chronograph_import_count": 2,
                    "test_result_count": 0,
                }
            },
        }
    )

    assert "capture cold-bore hunting validation" in guidance["header"]
    assert "1 cold-bore shot" in guidance["setup"]
    assert "field ready" in guidance["setup"]


def test_build_learning_workflow_guidance_uses_shooter_or_setup_spread_signal():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "learning": {
                "aggregate": {
                    "confidence_label": "delvis kalibrert",
                },
                "session": {
                    "summary": {
                        "signal_hint": "possible_shooter_or_setup_signal",
                        "batch_spread_reason": "Chrono is stable while groups are open.",
                    }
                },
            },
            "evidence": {
                "summary": {
                    "chronograph_import_count": 2,
                    "test_result_count": 2,
                }
            },
        }
    )

    assert "repeat before rejecting the load" in guidance["header"]
    assert "repeat one controlled group" in guidance["setup"]
    assert "before blaming the load" in guidance["setup"]
    assert "Signal: possible_shooter_or_setup_signal" in guidance["card_hint"]
    assert "Chrono is stable while groups are open." in guidance["card_hint"]


def test_build_learning_workflow_guidance_uses_ammo_or_process_spread_signal():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "learning": {
                "aggregate": {
                    "confidence_label": "tidlig læring",
                },
                "session": {
                    "summary": {
                        "signal_hint": "ammo_or_process_signal",
                    }
                },
            },
            "evidence": {
                "summary": {
                    "chronograph_import_count": 2,
                    "test_result_count": 2,
                }
            },
        }
    )

    assert "confirm ammo and loading process" in guidance["header"]
    assert "chrono every shot" in guidance["setup"]
    assert "neck tension" in guidance["setup"]


def test_build_learning_workflow_guidance_uses_environment_spread_signal():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "learning": {
                "aggregate": {
                    "confidence_label": "tidlig læring",
                },
                "session": {
                    "summary": {
                        "signal_hint": "environment_or_condition_signal",
                        "batch_spread_reason": "Recorded wind reached about 6.2 m/s.",
                    }
                },
            },
            "evidence": {
                "summary": {
                    "chronograph_import_count": 2,
                    "test_result_count": 2,
                }
            },
        }
    )

    assert "confirm environmental repeatability" in guidance["header"]
    assert "record wind and mirage" in guidance["setup"]
    assert "avoid changing charge or seating" in guidance["setup"]
    assert "Signal: environment_or_condition_signal" in guidance["card_hint"]


def test_build_learning_workflow_guidance_uses_node_or_barrel_timing_signal():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "learning": {
                "aggregate": {
                    "confidence_label": "tidlig læring",
                },
                "session": {
                    "summary": {
                        "signal_hint": "node_or_barrel_timing_signal",
                        "batch_spread_reason": "Chronograph spread is controlled but target pattern is vertical-dominant.",
                        "batch_spread_control_plan": {
                            "primary_action": "Repeat the same load with careful tracking before changing powder.",
                            "shot_plan": "Fire one control group, then test two seating-depth steps.",
                        },
                        "batch_spread_decision": {
                            "state": "focused_tuning_after_repeat",
                            "label": "Repeat, then tune seating/timing",
                        },
                        "batch_spread_profile_guidance": {
                            "title": "Competition repeatability focus",
                            "emphasis": "Use repeatable ES/SD, vertical pattern, and seating-depth brackets to isolate the tuning direction.",
                            "recommended_check": "Use same-setup control strings before final ranking.",
                        },
                        "batch_spread_evidence_quality": {
                            "level": "moderate",
                            "score": 58.0,
                        },
                        "batch_spread_learning_explanation": {
                            "title": "Stable velocity with vertical spread can be timing or tracking",
                            "user_takeaway": "For competition, prove repeatability before ranking or tuning aggressively.",
                        },
                        "batch_spread_capture_checklist": {
                            "title": "Next capture checklist",
                            "items": [
                                {"label": "Same-setup repeat string"},
                                {"label": "Small seating-depth bracket"},
                            ],
                        },
                        "batch_spread_validation_status": {
                            "status": "tuning_validation_pending",
                            "label": "Repeat before ranking or tuning harder",
                            "summary": "Stable ES/SD is promising, but the vertical pattern still needs repeat confirmation before seating-depth ranking.",
                            "next_gate": "Repeat one same-setup control group, then use a narrow seating-depth bracket if the vertical pattern remains.",
                            "readiness_score": 66.0,
                        },
                        "batch_comparison_basis": {
                            "ranking_state": "trailing_candidate",
                            "current_rank": 2,
                            "count": 3,
                            "summary": "Current batch currently ranks 2 of 3 comparable batches and trails Match Node A by about 6.5 score points.",
                        },
                        "batch_comparison_advisory": {
                            "title": "Trailing stronger evidence",
                            "message": "Current batch currently ranks 2 of 3 comparable batches and trails Match Node A by about 6.5 score points.",
                            "recommended_action": "Repeat one same-setup control group before promoting this batch over Match Node A.",
                        },
                        "batch_comparison_protocol": {
                            "title": "Head-to-head catch-up test",
                            "primary_action": "Run a same-day head-to-head against Match Node A before promoting this batch.",
                            "shot_plan": "Shoot the current batch and the leader with the same rifle setup, same distance, same support, and matched chrono plus measured groups.",
                        },
                        "batch_comparison_explanation": {
                            "limiting_factor": "validation_depth",
                            "reason": "The batch trails Match Node A by about 6.5 weighted comparison-score points.",
                            "next_measurement": "Repeat the same setup with matched chrono and measured groups.",
                        },
                        "batch_comparison_verdict": {
                            "label": "Do not promote yet",
                            "summary": "This batch should stay behind Match Node A until the comparison gap is tested under matched conditions.",
                        },
                        "batch_comparison_acceptance": {
                            "label": "Not accepted yet",
                            "summary": "This batch should not replace the current match candidate until the remaining comparison gaps are closed.",
                            "next_gate": "Repeat one same-setup control group before promoting this batch over Match Node A.",
                            "remaining_gaps": [
                                "The batch still trails Match Node A under the weighted comparison.",
                            ],
                        },
                        "batch_comparison_acceptance_progress": {
                            "level": "partial",
                            "score": 44.5,
                            "passed_count": 3,
                            "total_count": 5,
                            "summary": "Acceptance progress is still partial, so the batch should keep earning evidence before replacement.",
                            "next_target": "Repeat one same-setup control group before promoting this batch over Match Node A.",
                        },
                        "batch_comparison_next_test": {
                            "title": "Catch-up test vs Match Node A",
                            "summary": "Run the current batch directly against Match Node A under matched conditions before it is allowed to move up.",
                            "primary_action": "Run a same-day head-to-head against Match Node A before promoting this batch.",
                            "check_first": "Same setup on both batches",
                        },
                        "batch_comparison_status_board": {
                            "headline": "Still chasing the leader",
                            "readiness_band": "behind",
                            "summary": "Still chasing the leader | Rank 2/3 | Leader: Match Node A | Progress: partial (44.5/100) | Verdict: Do not promote yet",
                        },
                        "batch_comparison_profile_priority": {
                            "title": "Competition comparison priority",
                            "emphasis": "Favor repeatability, matched evidence, and setup control over one attractive result.",
                            "guardrail": "Do not rank a batch higher until the same-day repeat and matched chrono/group evidence agree.",
                        },
                        "batch_comparison_mission_brief": {
                            "title": "Comparison mission brief",
                            "mission": "Still chasing the leader: Treat the next outing as a matched ranking test, not a free-form tuning session.",
                            "primary_action": "Run a same-day head-to-head against Match Node A before promoting this batch.",
                            "success_marker": "A matched repeat string that still holds precision and consistency against the current leader.",
                        },
                        "batch_comparison_portfolio": {
                            "title": "Comparison portfolio",
                            "focus": "Use the next session to test whether the current batch can close the gap to Match Node A.",
                        },
                        "batch_comparison_session_strategy": {
                            "title": "Comparison session strategy",
                            "mode": "ranking_session",
                            "objective": "Challenge the current leader under matched conditions.",
                        },
                        "batch_comparison_campaign_view": {
                            "title": "Comparison campaign view",
                            "summary": "Leader Match Node A | band behind | mode ranking_session | Challenge the current leader under matched conditions.",
                        },
                        "batch_comparison_action_plan": {
                            "title": "Comparison action plan",
                            "summary": "Challenge the current leader under matched conditions.",
                            "primary_action": "Run a same-day head-to-head against Match Node A before promoting this batch.",
                        },
                        "batch_comparison_campaign_board": {
                            "title": "Comparison campaign board",
                            "summary": "Leader Match Node A | band behind | mode ranking_session | Challenge the current leader under matched conditions.",
                            "preview": [
                                "shoot_now: Match Node A",
                                "confirm: Current batch",
                            ],
                        },
                        "batch_comparison_session_queue": {
                            "title": "Comparison session queue",
                            "mode": "ranking_session",
                            "first_batch_name": "Match Node A",
                            "preview": [
                                "1. Match Node A (shoot_now)",
                                "2. Current batch (confirm)",
                            ],
                        },
                        "batch_comparison_session_manifest": {
                            "title": "Comparison session manifest",
                            "summary": "Leader Match Node A | band behind | mode ranking_session | Challenge the current leader under matched conditions. | Ready now: 1 | Confirm next: 1",
                            "primary_bucket": "shoot_now",
                            "first_batch_name": "Match Node A",
                            "queue_preview": [
                                "1. Match Node A (shoot_now)",
                                "2. Current batch (confirm)",
                            ],
                            "lane_summaries": [
                                {
                                    "bucket": "shoot_now",
                                    "count": 1,
                                    "summary": "shoot_now: Match Node A",
                                },
                                {
                                    "bucket": "confirm",
                                    "count": 1,
                                    "summary": "confirm: Current batch",
                                },
                            ],
                        },
                        "batch_comparison_next_session_brief": {
                            "title": "Comparison next session brief",
                            "summary": "Start with Match Node A | bucket shoot_now | check Same setup on both batches",
                            "first_batch_name": "Match Node A",
                            "primary_bucket": "shoot_now",
                            "primary_action": "Run a same-day head-to-head against Match Node A before promoting this batch.",
                            "hold_back": "hold: Current batch",
                        },
                        "batch_comparison_today_plan": {
                            "title": "Comparison today plan",
                            "summary": "Run Match Node A first | verify Same setup on both batches | hold back hold: Current batch",
                            "first_batch_name": "Match Node A",
                            "primary_bucket": "shoot_now",
                            "primary_action": "Run a same-day head-to-head against Match Node A before promoting this batch.",
                        },
                        "batch_comparison_workboard": {
                            "title": "Comparison workboard",
                            "summary": "Run Match Node A first | verify Same setup on both batches | hold back hold: Current batch",
                            "status_label": "Ready to run",
                            "first_batch_name": "Match Node A",
                            "primary_bucket": "shoot_now",
                            "primary_action": "Run a same-day head-to-head against Match Node A before promoting this batch.",
                            "counts": {"shoot_now": 1, "confirm": 1, "hold": 1},
                            "lane_summaries": [
                                {
                                    "bucket": "shoot_now",
                                    "summary": "shoot_now: Match Node A",
                                },
                                {
                                    "bucket": "confirm",
                                    "summary": "confirm: Current batch",
                                },
                                {"bucket": "hold", "summary": "hold: Current batch"},
                            ],
                        },
                        "batch_comparison_checklist": {
                            "title": "Comparison checklist",
                            "highest_priority": "Same setup on both batches",
                        },
                        "batch_comparison_scorecard": {
                            "swing_factor": "evidence_quality",
                            "summary": "Current batch mainly trails Match Node A on evidence quality.",
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
                    }
                },
            },
            "evidence": {
                "summary": {
                    "chronograph_import_count": 2,
                    "test_result_count": 2,
                }
            },
        }
    )

    assert "confirm vertical pattern and barrel timing" in guidance["header"]
    assert (
        "Repeat the same load with careful tracking before changing powder"
        in guidance["setup"]
    )
    assert "test two seating-depth steps" in guidance["setup"]
    assert "same-setup control strings" in guidance["setup"]
    assert "Signal: node_or_barrel_timing_signal" in guidance["card_hint"]
    assert "Decision: Repeat, then tune seating/timing" in guidance["card_hint"]
    assert "Profile: Competition repeatability focus" in guidance["card_hint"]
    assert "Evidence quality: moderate (58.0/100)" in guidance["card_hint"]
    assert (
        "Lesson: Stable velocity with vertical spread can be timing or tracking"
        in guidance["card_hint"]
    )
    assert "Takeaway: For competition, prove repeatability" in guidance["card_hint"]
    assert (
        "Checklist: Next capture checklist -> Same-setup repeat string"
        in guidance["card_hint"]
    )
    assert (
        "Validation: Repeat before ranking or tuning harder (66.0/100)"
        in guidance["card_hint"]
    )
    assert "Batch comparison: trailing_candidate (2/3)" in guidance["card_hint"]
    assert "Comparison advisory: Trailing stronger evidence" in guidance["card_hint"]
    assert "Comparison protocol: Head-to-head catch-up test" in guidance["card_hint"]
    assert "Comparison bottleneck: validation_depth" in guidance["card_hint"]
    assert "Comparison verdict: Do not promote yet" in guidance["card_hint"]
    assert "Comparison acceptance: Not accepted yet" in guidance["card_hint"]
    assert (
        "Acceptance gap: The batch still trails Match Node A under the weighted comparison."
        in guidance["card_hint"]
    )
    assert "Acceptance progress: partial (44.5/100) 3/5" in guidance["card_hint"]
    assert "Next test: Catch-up test vs Match Node A" in guidance["card_hint"]
    assert (
        "Comparison board: Still chasing the leader (behind)" in guidance["card_hint"]
    )
    assert (
        "Comparison profile: Competition comparison priority" in guidance["card_hint"]
    )
    assert (
        "Mission brief: Still chasing the leader: Treat the next outing as a matched ranking test"
        in guidance["card_hint"]
    )
    assert (
        "Portfolio: Comparison portfolio - Use the next session to test whether the current batch can close the gap to Match Node A."
        in guidance["card_hint"]
    )
    assert (
        "Session strategy: Comparison session strategy (ranking_session) - Challenge the current leader under matched conditions."
        in guidance["card_hint"]
    )
    assert (
        "Campaign view: Comparison campaign view - Leader Match Node A | band behind | mode ranking_session | Challenge the current leader under matched conditions."
        in guidance["card_hint"]
    )
    assert (
        "Action plan: Comparison action plan - Challenge the current leader under matched conditions."
        in guidance["card_hint"]
    )
    assert (
        "Campaign board: Comparison campaign board - Leader Match Node A | band behind | mode ranking_session | Challenge the current leader under matched conditions. - shoot_now: Match Node A | confirm: Current batch"
        in guidance["card_hint"]
    )
    assert (
        "Session queue: Comparison session queue - first Match Node A - 1. Match Node A (shoot_now) | 2. Current batch (confirm)"
        in guidance["card_hint"]
    )
    assert (
        "Session manifest: Comparison session manifest (shoot_now)"
        in guidance["card_hint"]
    )
    assert (
        "1. Match Node A (shoot_now) | 2. Current batch (confirm)"
        in guidance["card_hint"]
    )
    assert "shoot_now: Match Node A | confirm: Current batch" in guidance["card_hint"]
    assert (
        "Next session brief: Comparison next session brief - Start with Match Node A | bucket shoot_now | check Same setup on both batches - hold back hold: Current batch"
        in guidance["card_hint"]
    )
    assert (
        "Today plan: Comparison today plan - Run Match Node A first | verify Same setup on both batches | hold back hold: Current batch"
        in guidance["card_hint"]
    )
    assert (
        "Workboard: Comparison workboard - Run Match Node A first | verify Same setup on both batches | hold back hold: Current batch"
        in guidance["card_hint"]
    )
    assert "lane shoot_now" in guidance["card_hint"]
    assert "first Match Node A" in guidance["card_hint"]
    assert "shoot_now 1 | confirm 1 | hold 1" in guidance["card_hint"]
    assert (
        "shoot_now: Match Node A | confirm: Current batch | hold: Current batch"
        in guidance["card_hint"]
    )
    assert "Ready to run" in guidance["card_hint"]
    assert (
        "Comparison checklist: Comparison checklist -> Same setup on both batches"
        in guidance["card_hint"]
    )
    assert "Comparison scorecard: evidence_quality" in guidance["card_hint"]
    assert "Comparison confidence: thin (48.0/100)" in guidance["card_hint"]
    assert (
        "Comparison learning: Evidence quality is currently the biggest separator"
        in guidance["card_hint"]
    )
    assert "Validation gate: Repeat one same-setup control group" in guidance["setup"]
    assert (
        "Comparison gate: Repeat one same-setup control group before promoting this batch over Match Node A."
        in guidance["setup"]
    )
    assert (
        "Head-to-head: Run a same-day head-to-head against Match Node A before promoting this batch."
        in guidance["setup"]
    )
    assert (
        "Bottleneck check: Repeat the same setup with matched chrono and measured groups."
        in guidance["setup"]
    )
    assert (
        "Acceptance gate: Repeat one same-setup control group before promoting this batch over Match Node A."
        in guidance["setup"]
    )
    assert (
        "Progress target: Repeat one same-setup control group before promoting this batch over Match Node A."
        in guidance["setup"]
    )
    assert (
        "Next test: Run a same-day head-to-head against Match Node A before promoting this batch."
        in guidance["setup"]
    )
    assert (
        "Mission action: Run a same-day head-to-head against Match Node A before promoting this batch."
        in guidance["setup"]
    )
    assert (
        "Session objective: Challenge the current leader under matched conditions."
        in guidance["setup"]
    )
    assert (
        "Action plan: Run a same-day head-to-head against Match Node A before promoting this batch."
        in guidance["setup"]
    )
    assert "Session bucket: shoot_now" in guidance["setup"]
    assert "Manifest first: Match Node A" in guidance["setup"]
    assert (
        "Session brief: Run a same-day head-to-head against Match Node A before promoting this batch."
        in guidance["setup"]
    )
    assert (
        "Today plan: Run a same-day head-to-head against Match Node A before promoting this batch."
        in guidance["setup"]
    )
    assert (
        "Workboard: Run a same-day head-to-head against Match Node A before promoting this batch."
        in guidance["setup"]
    )
    assert "Workboard lane: shoot_now" in guidance["setup"]
    assert "Workboard first: Match Node A" in guidance["setup"]
    assert "Workboard counts: shoot_now 1 | confirm 1 | hold 1" in guidance["setup"]
    assert (
        "Workboard lanes: shoot_now: Match Node A | confirm: Current batch | hold: Current batch"
        in guidance["setup"]
    )
    assert "Compare first: Same setup on both batches" in guidance["setup"]


def test_build_learning_workflow_guidance_pressure_still_overrides_spread_signal():
    guidance = mlb_module.build_learning_workflow_guidance(
        {
            "context": {"usage_profile_name": "Competition"},
            "learning": {
                "aggregate": {
                    "confidence_label": "tidlig læring",
                },
                "session": {
                    "summary": {
                        "pressure_level": "warning",
                        "signal_hint": "possible_shooter_or_setup_signal",
                    }
                },
            },
            "evidence": {
                "summary": {
                    "chronograph_import_count": 2,
                    "test_result_count": 2,
                }
            },
        }
    )

    assert "verify pressure before optimization" in guidance["header"]
    assert "confirm pressure behavior" in guidance["setup"]


def test_summarize_runtime_primer_review_reports_disabled_state():
    summary = mlb_module.summarize_runtime_primer_review(
        {
            "evidence": {
                "primer_review": {
                    "status": "disabled",
                    "disabled_session_count": 2,
                },
                "summary": {
                    "primer_review_status": "disabled",
                },
            }
        }
    )

    assert summary["level"] == "info"
    assert summary["title"] == "Primer review disabled"
    assert "intentional" in summary["message"]
    assert "should not drive accuracy decisions" in summary["message"]
    assert "2 sessions" in summary["summary"]


def test_summarize_runtime_primer_review_reports_captured_state():
    summary = mlb_module.summarize_runtime_primer_review(
        {
            "context": {
                "barrel_name": "24in Match",
                "barrel_configuration_name": "Suppressed",
            },
            "identity": {
                "barrel": {
                    "label": "24in Match",
                    "configuration_label": "Suppressed",
                }
            },
            "evidence": {
                "primer_review": {
                    "status": "captured",
                    "reviewed_session_count": 1,
                    "review_image_count": 3,
                    "pressure_sign_review_count": 2,
                }
            },
        }
    )

    assert summary["level"] == "ok"
    assert summary["title"] == "Primer review linked"
    assert "current rifle" in summary["message"]
    assert "24in Match / Suppressed" in summary["message"]
    assert "not as a direct accuracy signal" in summary["message"]
    assert "3 images" in summary["summary"]


def test_resolve_runtime_learning_context_prefers_runtime_payload():
    resolved = mlb_module.resolve_runtime_learning_context(
        {
            "learning": {
                "session": {
                    "analysis": {
                        "barrel_context": {
                            "title": "Runtime barrel",
                            "level": "ok",
                        }
                    }
                }
            }
        },
        {
            "barrel_context": {
                "title": "Legacy barrel",
                "level": "warning",
            }
        },
        "barrel_context",
    )

    assert resolved["title"] == "Runtime barrel"
    assert resolved["level"] == "ok"


def test_resolve_runtime_learning_context_falls_back_to_analysis():
    resolved = mlb_module.resolve_runtime_learning_context(
        {},
        {
            "brass_context": {
                "title": "Legacy brass",
                "level": "info",
            }
        },
        "brass_context",
    )

    assert resolved["title"] == "Legacy brass"
    assert resolved["level"] == "info"


def test_build_runtime_analysis_context_prefers_runtime_recommendation_payload():
    context = mlb_module.build_runtime_analysis_context(
        {
            "recommendation": {
                "pressure_assessment": {
                    "level": "warning",
                    "title": "Runtime pressure",
                },
                "internal_ballistics": {"level": "ok", "title": "Runtime burn"},
            },
            "evidence": {
                "primer_review": {
                    "status": "captured",
                    "reviewed_session_count": 1,
                    "review_image_count": 2,
                }
            },
            "learning": {
                "session": {
                    "analysis": {
                        "brass_context": {"level": "ok", "title": "Runtime brass"},
                        "stability_assessment": {
                            "level": "stable",
                            "title": "Runtime stability",
                        },
                    }
                }
            },
        },
        {
            "pressure_assessment": {"level": "critical", "title": "Legacy pressure"},
            "internal_ballistics": {"level": "warning", "title": "Legacy burn"},
            "brass_context": {"level": "info", "title": "Legacy brass"},
            "stability_assessment": {"level": "warning", "title": "Legacy stability"},
        },
    )

    assert context["pressure_assessment"]["title"] == "Runtime pressure"
    assert context["internal_ballistics"]["title"] == "Runtime burn"
    assert context["brass_context"]["title"] == "Runtime brass"
    assert context["stability_assessment"]["title"] == "Runtime stability"
    assert context["primer_review"]["title"] == "Primer review linked"


def test_build_runtime_analysis_context_falls_back_when_runtime_missing():
    context = mlb_module.build_runtime_analysis_context(
        {},
        {
            "pressure_assessment": {"level": "critical", "title": "Legacy pressure"},
            "internal_ballistics": {"level": "warning", "title": "Legacy burn"},
            "brass_context": {"level": "info", "title": "Legacy brass"},
        },
    )

    assert context["pressure_assessment"]["title"] == "Legacy pressure"
    assert context["internal_ballistics"]["title"] == "Legacy burn"
    assert context["brass_context"]["title"] == "Legacy brass"
    assert context["primer_review"]["status"] == "none"


def test_format_learning_runtime_label_includes_data_and_pressure_state():

    class _Widget(mlb_module.ModernLoadBuilder):
        def __init__(self):
            super().__init__()

    widget = _Widget()
    label = widget._format_learning_runtime_label(
        {
            "learning": {
                "aggregate": {
                    "confidence_label": "brukbar trygghet",
                    "confidence_score": 72.5,
                    "weakest_link": "kruttlot",
                },
                "session": {
                    "summary": {
                        "next_focus": "verify_component_lot",
                        "pressure_level": "warning",
                        "data_strength": "medium",
                        "drift_state": "watch",
                        "signal_hint": "pressure_or_ammo",
                    }
                },
            },
            "evidence": {
                "summary": {
                    "chronograph_import_count": 3,
                    "test_result_count": 2,
                }
            },
        },
    )

    assert "Model: brukbar trygghet (72.5)" in label
    assert "Data: 3 chrono / 2 tests" in label
    assert "Strength: medium" in label
    assert "Weakest link: kruttlot" in label
    assert "Pressure: warning" in label
    assert "Drift: watch" in label
    assert "Signal: pressure_or_ammo" in label


def test_build_evidence_recommendation_baseline_prefers_learned_seating():
    baseline = mlb_module.build_evidence_recommendation_baseline(
        analysis={
            "rifle_context": {
                "barrel_name": "26in Match Pipe",
                "barrel_configuration_id": "pipe-1:suppressed",
                "barrel_configuration_name": "Suppressed",
            },
            "recommendation": {
                "charge_window_gr": [41.8, 42.2],
                "seating_window_mm": [-0.05, 0.05],
            },
            "input_quality": {"level": "high", "score": 82.0},
        },
        current_charge_gr=42.0,
        coal_mm=71.5,
        cbto_mm=68.8,
        seating_summary={
            "promotion_candidate": {
                "eligible": True,
                "promoted_cbto_mm": 68.92,
            }
        },
        signature=(1, 2, 3),
    )

    assert baseline["available"] is True
    assert baseline["charge_gr"] == 42.0
    assert baseline["seating_source"] == "learned"
    assert baseline["cbto_mm"] == 68.92
    assert baseline["coal_mm"] == 71.62
    assert baseline["setup_label"] == "26in Match Pipe / Suppressed"
    assert "setup 26in Match Pipe / Suppressed" in baseline["summary"]


def test_summarize_charge_promotion_candidate_flags_learned_charge_when_history_is_strong():
    candidate = mlb_module.summarize_charge_promotion_candidate(
        current_charge_gr=42.02,
        history_result={
            "suggested_charge": 42.0,
            "sample_count": 5,
            "observed_range": (41.5, 42.5),
            "model": {"a": 0.25, "r2": 0.81},
        },
    )

    assert candidate["eligible"] is True
    assert candidate["promoted_charge_gr"] == 42.0
    assert "learned charge" in candidate["title"].lower()


def test_build_evidence_recommendation_baseline_prefers_learned_charge_when_available():
    baseline = mlb_module.build_evidence_recommendation_baseline(
        analysis={
            "recommendation": {
                "charge_window_gr": [41.8, 42.2],
            },
            "input_quality": {"level": "high", "score": 82.0},
        },
        current_charge_gr=42.02,
        coal_mm=71.5,
        cbto_mm=68.8,
        charge_promotion_candidate={
            "eligible": True,
            "promoted_charge_gr": 42.0,
        },
        seating_summary={},
        signature=(1, 2, 3),
    )

    assert baseline["available"] is True
    assert baseline["charge_source"] == "learned"
    assert baseline["charge_gr"] == 42.0
    assert "learned charge" in baseline["summary"]


def test_build_evidence_recommendation_baseline_requires_measured_support_before_freezing_recommended_windows():
    baseline = mlb_module.build_evidence_recommendation_baseline(
        analysis={
            "recommendation": {
                "charge_window_gr": [41.8, 42.2],
                "seating_window_mm": [-0.05, 0.05],
            },
            "input_quality": {"level": "low", "score": 1.75},
            "observations": {"summary": {"chrono_count": 0, "accuracy_count": 0}},
        },
        current_charge_gr=42.0,
        coal_mm=71.5,
        cbto_mm=68.8,
        seating_summary={},
        charge_promotion_candidate={},
        signature=(1, 2, 3),
    )

    assert baseline["available"] is False
    assert baseline["charge_source"] == "current"
    assert baseline["seating_source"] == "current"
    assert baseline["summary"] == ""


def test_build_evidence_recommendation_baseline_only_freezes_charge_when_chrono_exists_without_groups():
    baseline = mlb_module.build_evidence_recommendation_baseline(
        analysis={
            "recommendation": {
                "charge_window_gr": [41.8, 42.2],
                "seating_window_mm": [-0.05, 0.05],
                "baseline_readiness": {
                    "charge_can_freeze": True,
                    "seating_can_freeze": False,
                },
            },
            "input_quality": {"level": "medium", "score": 3.1},
            "observations": {"summary": {"chrono_count": 2, "accuracy_count": 0}},
        },
        current_charge_gr=42.0,
        coal_mm=71.5,
        cbto_mm=68.8,
        seating_summary={},
        charge_promotion_candidate={},
        signature=(1, 2, 3),
    )

    assert baseline["available"] is True
    assert baseline["charge_source"] == "recommended"
    assert baseline["charge_gr"] == 42.0
    assert baseline["seating_source"] == "current"
    assert baseline["coal_mm"] == 71.5
    assert "charge 42.00 gr" in baseline["summary"]


def test_build_recommendation_control_state_reports_custom_mode_when_user_moves_off_baseline():
    state = mlb_module.build_recommendation_control_state(
        current_charge_gr=42.6,
        coal_mm=71.7,
        cbto_mm=68.8,
        baseline={
            "available": True,
            "charge_gr": 42.0,
            "coal_mm": 71.5,
            "cbto_mm": 68.92,
            "charge_source": "recommended",
            "seating_source": "learned",
            "trust_label": "high",
            "setup_label": "26in Match Pipe / Suppressed",
        },
    )

    assert state["available"] is True
    assert state["can_apply"] is True
    assert state["charge_state"] == "custom"
    assert state["seating_state"] == "custom"
    assert "custom mode" in state["message"].lower()
    assert "modeled baseline" in state["message"].lower()
    assert "26in Match Pipe / Suppressed" in state["message"]


def test_build_recommendation_control_state_reports_learned_charge_when_aligned():
    state = mlb_module.build_recommendation_control_state(
        current_charge_gr=42.0,
        coal_mm=71.5,
        cbto_mm=68.92,
        baseline={
            "available": True,
            "charge_gr": 42.0,
            "coal_mm": 71.5,
            "cbto_mm": 68.92,
            "charge_source": "learned",
            "seating_source": "learned",
            "trust_label": "high",
        },
    )

    assert state["charge_state"] == "learned"
    assert state["seating_state"] == "learned"
    assert state["can_apply"] is False
    assert state["charge_source_label"] == "learned baseline"
    assert state["seating_source_label"] == "learned baseline"


def test_summarize_recommendation_evidence_basis_distinguishes_measured_modeled_and_learned():
    summary = mlb_module.summarize_recommendation_evidence_basis(
        {
            "rifle_context": {
                "barrel_name": "26in Match Pipe",
                "barrel_configuration_name": "Suppressed",
            },
            "recommendation": {
                "charge_window_gr": [41.8, 42.2],
                "seating_window_mm": [-0.05, 0.05],
                "baseline_readiness": {
                    "charge_can_freeze": True,
                    "seating_can_freeze": False,
                },
            },
            "observations": {
                "summary": {
                    "chrono_count": 2,
                    "accuracy_count": 0,
                }
            },
            "input_quality": {
                "title": "Brukbar inputkvalitet",
                "level": "medium",
                "score": 3.1,
            },
        },
        {
            "available": True,
            "charge_source": "recommended",
            "seating_source": "current",
        },
    )

    assert summary["title"] == "Recommendation Basis"
    assert "Setup: 26in Match Pipe / Suppressed." in summary["message"]
    assert "Measured:" in summary["message"]
    assert "2 chrono series support charge guidance" in summary["message"]
    assert "no group data supports seating guidance yet" in summary["message"]
    assert "Modeled:" in summary["message"]
    assert "charge window is engine-modeled" in summary["message"]
    assert "Learned:" in summary["message"]
    assert (
        "charge baseline has measured support but is not learned history yet"
        in summary["message"]
    )
    assert "seating baseline is still modeled only" in summary["message"]
    assert "Setup 26in Match Pipe / Suppressed" in summary["compact"]


def test_summarize_recommendation_return_targets_uses_learned_cbto_target():
    lines = mlb_module.summarize_recommendation_return_targets(
        {
            "charge_target_gr": 42.0,
            "cbto_target_mm": 68.92,
        },
        {
            "available": True,
            "charge_source": "learned",
            "seating_source": "learned",
        },
    )

    assert lines == [
        "Charge target (learned baseline): 42.00 gr",
        "Seating target (learned baseline): 68.92 mm CBTO",
    ]


def test_summarize_recommendation_return_targets_falls_back_to_recommended_coal():
    lines = mlb_module.summarize_recommendation_return_targets(
        {},
        {
            "available": True,
            "charge_gr": 44.5,
            "coal_mm": 71.0,
            "charge_source": "recommended",
            "seating_source": "recommended",
        },
    )

    assert lines == [
        "Charge target (modeled baseline): 44.50 gr",
        "Seating target (modeled baseline): 71.00 mm COAL",
    ]


def test_summarize_stability_advisor_flags_subsonic_suppressor_risk():
    summary = mlb_module.summarize_stability_advisor(
        {"sg": 1.12, "velocity_fps": 1020.0},
        result={"muzzle_velocity_fps": 1020.0},
        subsonic_mode=True,
        twist_inches=8.0,
        bullet={"length_mm": 38.7},
        barrel_details={"muzzle_device_type": "suppressor"},
    )

    assert summary["level"] == "critical"
    assert (
        "suppressor" in summary["title"].lower()
        or "subsonic" in summary["title"].lower()
    )
    assert any("suppressor" in check.lower() for check in summary["checks"])


def test_summarize_stability_advisor_reports_healthy_margin():
    summary = mlb_module.summarize_stability_advisor(
        {"sg": 1.63, "velocity_fps": 2810.0},
        result={"muzzle_velocity_fps": 2810.0},
        subsonic_mode=False,
        twist_inches=8.0,
        bullet={"length_mm": 31.2},
    )

    assert summary["level"] == "ok"
    assert "healthy" in summary["title"].lower()


def test_summarize_subsonic_advisor_flags_over_target_and_low_fill():
    summary = mlb_module.summarize_subsonic_advisor(
        {
            "muzzle_velocity_fps": 1088.0,
            "load_density_percent": 48.0,
        },
        enabled=True,
        target_velocity_fps=1050.0,
        stability={"sg": 1.28},
    )

    assert summary["level"] == "critical"
    assert (
        "low fill" in summary["title"].lower()
        or "over subsonic target" in summary["title"].lower()
    )
    assert any("Fyllgrad" in check for check in summary["checks"])


def test_summarize_subsonic_advisor_reports_usable_window():
    summary = mlb_module.summarize_subsonic_advisor(
        {
            "muzzle_velocity_fps": 1015.0,
            "load_density_percent": 72.0,
        },
        enabled=True,
        target_velocity_fps=1050.0,
        stability={"sg": 1.34},
    )

    assert summary["level"] == "ok"
    assert "usable" in summary["title"].lower()
    assert abs(summary["margin_fps"] - 35.0) < 1e-6


def test_summarize_subsonic_history_advisory_reports_promising_history():
    db = _FakeDb(
        batch_rows=[
            {
                "batch_analysis_json": '{"subsonic_context":{"enabled":true}}',
                "session_analysis_json": '{"subsonic_observations":{"cycling_status":"cycled","sonic_crack":false,"keyhole":false,"suppressor_used":true}}',
            },
            {
                "batch_analysis_json": '{"subsonic_context":{"enabled":true}}',
                "session_analysis_json": '{"subsonic_observations":{"cycling_status":"cycled","sonic_crack":false,"keyhole":false,"suppressor_used":false}}',
            },
        ]
    )

    summary = mlb_module.summarize_subsonic_history_advisory(db, 1, 2, 3)

    assert summary["level"] == "ok"
    assert "promising" in summary["title"].lower()
    assert any("2 subsonic sessions" in check.lower() for check in summary["checks"])


def test_summarize_subsonic_history_advisory_flags_keyhole_history():
    db = _FakeDb(
        batch_rows=[
            {
                "batch_analysis_json": '{"subsonic_context":{"enabled":true}}',
                "session_analysis_json": '{"subsonic_observations":{"cycling_status":"failed","sonic_crack":true,"keyhole":true,"suppressor_used":true}}',
            }
        ]
    )

    summary = mlb_module.summarize_subsonic_history_advisory(db, 1, 2, 3)

    assert summary["level"] == "critical"
    assert "stability warning" in summary["title"].lower()
    assert any("keyhole" in check.lower() for check in summary["checks"])


def test_summarize_builder_confidence_model_scores_verified_setup_higher():
    summary = mlb_module.summarize_builder_confidence_model(
        {"muzzle_velocity_fps": 2810.0, "_calibration_mse": 16.0},
        workflow_data={"rifle_id": 1, "bullet_id": 2},
        observations={"chronograph_sessions": [{"avg_velocity_fps": 2810.0}]},
        bullet_data={"bc_g7": 0.315},
        powder_data={"usable_for_simulation": 1},
        tracked_brass=True,
        seating_evidence={"confidence": "high"},
        subsonic_history={"level": "ok"},
        model_match={"level": "ok", "bias_direction": "neutral", "bias_fps": 4.0},
    )

    assert summary["level"] in {"medium", "high"}
    assert summary["score"] >= 4.0
    assert any("powder model" in check.lower() for check in summary["checks"])


def test_summarize_builder_confidence_model_flags_thin_setup():
    summary = mlb_module.summarize_builder_confidence_model(
        {},
        workflow_data={},
        observations={},
        bullet_data={},
        powder_data={"usable_for_simulation": 0},
        tracked_brass=False,
        seating_evidence=None,
        subsonic_history={"level": "warning"},
        model_match={
            "level": "critical",
            "bias_direction": "model_higher",
            "bias_fps": -18.0,
        },
    )

    assert summary["level"] == "low"
    assert summary["score"] < 4.0


def test_summarize_builder_confidence_model_mentions_readable_bias():
    summary = mlb_module.summarize_builder_confidence_model(
        {"muzzle_velocity_fps": 2810.0},
        workflow_data={"rifle_id": 1},
        observations={},
        bullet_data={},
        powder_data={"usable_for_simulation": 1},
        tracked_brass=True,
        seating_evidence={"confidence": "medium"},
        subsonic_history={"level": "ok"},
        model_match={
            "level": "warning",
            "bias_direction": "model_higher",
            "bias_fps": -16.0,
        },
    )

    assert any("model bias" in check.lower() for check in summary["checks"])


def test_get_subsonic_history_windows_extracts_success_and_problem_ranges():
    db = _FakeDb(
        batch_rows=[
            {
                "charge_weight_grains": 12.0,
                "cbto_mm": 56.00,
                "batch_analysis_json": '{"subsonic_context":{"enabled":true}}',
                "session_analysis_json": '{"subsonic_observations":{"cycling_status":"cycled","sonic_crack":false,"keyhole":false}}',
            },
            {
                "charge_weight_grains": 12.2,
                "cbto_mm": 56.04,
                "batch_analysis_json": '{"subsonic_context":{"enabled":true}}',
                "session_analysis_json": '{"subsonic_observations":{"cycling_status":"failed","sonic_crack":true,"keyhole":false}}',
            },
        ]
    )

    windows = mlb_module.get_subsonic_history_windows(db, 1, 2, 3)

    assert windows["successful_charge_range"] == (12.0, 12.0)
    assert windows["problem_charge_range"] == (12.2, 12.2)
    assert windows["successful_cbto_range"] == (56.0, 56.0)
    assert windows["problem_cbto_range"] == (56.04, 56.04)


def test_summarize_model_vs_measured_advisory_reports_good_match():
    db = _FakeDb(
        batch_rows=[
            {
                "batch_id": 11,
                "charge_weight_grains": 43.0,
                "cbto_mm": 56.10,
                "powder_id": 3,
                "component_snapshot_json": '{"powder":{"id":3}}',
                "batch_analysis_json": '{"subsonic_context":{"enabled":false}}',
                "session_id": 101,
                "session_analysis_json": '{"stats":{"avg":2812.0},"group_size_moa":0.42}',
                "group_size_moa": 0.42,
            }
        ]
    )

    summary = mlb_module.summarize_model_vs_measured_advisory(
        db,
        1,
        2,
        3,
        current_charge_grains=43.0,
        current_cbto_mm=56.12,
        predicted_velocity_fps=2805.0,
        subsonic_mode=False,
    )

    assert summary["level"] == "ok"
    assert "matches well" in summary["title"].lower()
    assert any(
        "deviation from the model" in check.lower() for check in summary["checks"]
    )


def test_summarize_model_vs_measured_advisory_flags_large_velocity_delta():
    db = _FakeDb(
        batch_rows=[
            {
                "batch_id": 12,
                "charge_weight_grains": 12.0,
                "cbto_mm": 56.00,
                "powder_id": 3,
                "component_snapshot_json": '{"powder":{"id":3}}',
                "batch_analysis_json": '{"subsonic_context":{"enabled":true}}',
                "session_id": 201,
                "session_analysis_json": '{"stats":{"avg":980.0}}',
                "group_size_moa": None,
            }
        ]
    )

    summary = mlb_module.summarize_model_vs_measured_advisory(
        db,
        1,
        2,
        3,
        current_charge_grains=12.1,
        current_cbto_mm=56.02,
        predicted_velocity_fps=1055.0,
        subsonic_mode=True,
    )

    assert summary["level"] == "critical"
    assert "differs" in summary["title"].lower()


def test_summarize_model_vs_measured_advisory_prefers_same_lot_and_temperature():
    db = _FakeDb(
        batch_rows=[
            {
                "batch_id": 21,
                "charge_weight_grains": 43.0,
                "cbto_mm": 56.10,
                "powder_id": 3,
                "component_snapshot_json": '{"powder":{"id":3,"lot_number":"LOT-A"}}',
                "batch_analysis_json": '{"subsonic_context":{"enabled":false},"seating_context":{"temperature_c":12.0}}',
                "session_id": 301,
                "session_analysis_json": '{"stats":{"avg":2810.0}}',
                "group_size_moa": None,
            },
            {
                "batch_id": 22,
                "charge_weight_grains": 43.0,
                "cbto_mm": 56.10,
                "powder_id": 3,
                "component_snapshot_json": '{"powder":{"id":3,"lot_number":"LOT-B"}}',
                "batch_analysis_json": '{"subsonic_context":{"enabled":false},"seating_context":{"temperature_c":28.0}}',
                "session_id": 302,
                "session_analysis_json": '{"stats":{"avg":2810.0}}',
                "group_size_moa": None,
            },
        ]
    )

    summary = mlb_module.summarize_model_vs_measured_advisory(
        db,
        1,
        2,
        3,
        current_charge_grains=43.0,
        current_cbto_mm=56.10,
        predicted_velocity_fps=2811.0,
        subsonic_mode=False,
        current_powder_lot_number="LOT-A",
        target_temperature_c=13.0,
    )

    assert summary["reference"]["batch_id"] == 21
    assert any("same powder lot" in check.lower() for check in summary["checks"])


def test_summarize_model_vs_measured_advisory_reports_bias_direction():
    db = _FakeDb(
        batch_rows=[
            {
                "batch_id": 31,
                "charge_weight_grains": 43.0,
                "cbto_mm": 56.10,
                "powder_id": 3,
                "component_snapshot_json": '{"powder":{"id":3,"lot_number":"LOT-A"}}',
                "batch_analysis_json": '{"subsonic_context":{"enabled":false},"seating_context":{"temperature_c":12.0}}',
                "session_id": 401,
                "session_analysis_json": '{"stats":{"avg":2840.0}}',
                "group_size_moa": None,
            },
            {
                "batch_id": 32,
                "charge_weight_grains": 43.1,
                "cbto_mm": 56.12,
                "powder_id": 3,
                "component_snapshot_json": '{"powder":{"id":3,"lot_number":"LOT-A"}}',
                "batch_analysis_json": '{"subsonic_context":{"enabled":false},"seating_context":{"temperature_c":13.0}}',
                "session_id": 402,
                "session_analysis_json": '{"stats":{"avg":2832.0}}',
                "group_size_moa": None,
            },
        ]
    )

    summary = mlb_module.summarize_model_vs_measured_advisory(
        db,
        1,
        2,
        3,
        current_charge_grains=43.0,
        current_cbto_mm=56.10,
        predicted_velocity_fps=2800.0,
        subsonic_mode=False,
        current_powder_lot_number="LOT-A",
        target_temperature_c=12.0,
    )

    assert summary["bias_direction"] == "measured_higher"
    assert summary["bias_fps"] > 20.0
    assert any("fps low" in check for check in summary["checks"])


def test_builder_internal_ballistics_summary_prefers_selected_case_context_and_trim():
    class _CasePriorityDb:
        def execute_query(self, query, params=()):
            normalized = " ".join(query.split())
            if "FROM ammo_profiles" in normalized:
                return [{"id": 7, "case_id": 11}]
            if "FROM cases" in normalized:
                return [
                    {"id": 11, "case_capacity_gr_h2o": 53.8, "trim_length_mm": 48.77}
                ]
            return []

        def refresh_case_learning_profile(self, case_id):
            return {"avg_case_capacity_h2o": 53.8, "h2o_samples": 4}

    class _Widget(mlb_module.ModernLoadBuilder):
        def __init__(self):
            super().__init__()
            self.db = _CasePriorityDb()
            self.brass_data = {}
            self.powder_data = {"name": "N550"}
            self.current_charge = 41.5
            self.current_ammo_profile_id = 7
            self._latest_visual_result = {
                "barrel_length_inches": 24.0,
                "powder_density": 0.95,
                "powder_volume_ml": 2.85,
                "available_volume_ml": 3.25,
                "burn_rate_position": "medium",
                "load_density_percent": 92.0,
            }

        def _fetch_ammo_profile(self, ammo_profile_id):
            return mlb_module.ModernLoadBuilder._fetch_ammo_profile(
                self, ammo_profile_id
            )

        def _get_selected_case_row(self, ammo_profile_id=None):
            return mlb_module.ModernLoadBuilder._get_selected_case_row(
                self, ammo_profile_id=ammo_profile_id
            )

        def _coerce_float(self, value):
            return mlb_module.ModernLoadBuilder._coerce_float(value)

    widget = _Widget()
    summary = widget._build_current_internal_ballistics_summary()

    assert summary["title"] == "Internballistikk"
    assert any("selected case" in check for check in summary["checks"])
    assert any("trim length 48.77 mm" in check.lower() for check in summary["checks"])
    assert any(
        metric.get("name") == "Hylsevolum" and "3.49" in str(metric.get("value"))
        for metric in summary["metrics"]
    )


def test_summarize_builder_evidence_basis_uses_supplied_internal_ballistics_summary():
    summary = mlb_module.summarize_builder_evidence_basis(
        {
            "peak_pressure_psi": 58000,
            "charge_weight_grains": 41.5,
            "powder_name": "N550",
            "case_capacity_ml": 3.2,
            "safety_margin_percent": 8.0,
        },
        internal_ballistics_summary={
            "level": "warning",
            "title": "Internballistikk",
            "message": "selected case brukes som grunnlag",
            "metrics": [],
            "checks": [],
        },
    )

    assert "selected case brukes som grunnlag" in summary["message"]


class _FakeDb:
    def __init__(
        self,
        rows=None,
        comparison=None,
        bullet_rows=None,
        bullet_comparison=None,
        primer_rows=None,
        primer_comparison=None,
        component_lot_rows=None,
        component_lot_stats=None,
        batch_rows=None,
    ):
        self._rows = rows or []
        self._comparison = comparison or {}
        self._bullet_rows = bullet_rows or []
        self._bullet_comparison = bullet_comparison or {}
        self._primer_rows = primer_rows or []
        self._primer_comparison = primer_comparison or {}
        self._component_lot_rows = component_lot_rows or []
        self._component_lot_stats = component_lot_stats or {}
        self._batch_rows = batch_rows or []

    def execute_query(self, query, params=()):
        normalized = " ".join(query.split())
        if "FROM batch_projects" in normalized:
            return list(self._batch_rows)
        if "FROM bullet_lots" in normalized:
            return list(self._bullet_rows)
        if "FROM component_lots" in normalized and "component_type = ?" in normalized:
            return list(self._component_lot_rows)
        if (
            "FROM component_lots" in normalized
            and "component_type = 'powder'" in normalized
        ):
            return list(self._rows)
        if "component_type = 'primers'" in normalized:
            return list(self._primer_rows)
        return list(self._rows)

    def compare_powder_lots(self, component_id, current_lot_id):
        return dict(self._comparison)

    def compare_bullet_lots(self, bullet_id, current_lot_id):
        return dict(self._bullet_comparison)

    def compare_primer_lots(self, component_id, current_lot_id):
        return dict(self._primer_comparison)

    def get_component_lot_stats(self, component_lot_id):
        return dict(self._component_lot_stats.get(component_lot_id) or {})

    def get_by_id(self, table, record_id):
        if table == "load_development_workflows":
            return {
                "id": record_id,
                "usage_profile": "hunting_medium",
                "bullet_id": 2,
            }
        if table == "bullets":
            return {
                "id": record_id,
                "manufacturer": "Hornady",
                "name": "ELD-X",
                "weight_grains": 143,
                "bc_g1": 0.625,
                "bullet_type": "bonded hunting",
            }
        return None

    def refresh_powder_lot_learning_profile(self, component_lot_id):
        return {}

    def refresh_primer_lot_learning_profile(self, component_lot_id):
        return {}

    def list_cartridge_standards(self):
        return []

    def get_seating_depth_profile(
        self, rifle_id, bullet_id, component_lot_id=None, barrel_id=None
    ):
        return None

    def list_seating_depth_profiles(self, rifle_id, bullet_id, barrel_id=None):
        return []

    def get_best_seating_depth_evidence(
        self,
        rifle_id,
        bullet_id,
        component_lot_id=None,
        lot_number=None,
        target_temperature_c=None,
        target_distance_m=None,
        target_throat_erosion_mm=None,
        barrel_id=None,
        include_ranked=False,
    ):
        return None


def test_summarize_powder_lot_advisory_reports_retest_guidance():
    db = _FakeDb(
        rows=[{"id": 7}],
        comparison={
            "severity": "high",
            "title": "Tydelig lotavvik",
            "message": "Sammenlignet med forrige lot: Snittfart +26.0 fps",
            "current_profile": {"confidence_label": "middels"},
            "verification_plan": {
                "focus": "Start 0.2 gr under forrige bekreftede ladning og chrono de første 5 skuddene før videre testing.",
                "start_delta_grains": -0.2,
            },
        },
    )

    summary = mlb_module.summarize_powder_lot_advisory(db, 123)

    assert summary["level"] == "critical"
    assert summary["title"] == "Tydelig lotavvik"
    assert "Snittfart +26.0 fps" in summary["message"]
    assert "middels" in summary["message"].lower()
    assert "Uncertainty" in summary["message"]
    assert "0.20 gr" in summary["message"]


def test_summarize_seating_depth_advisor_flags_into_lands():
    class _SeatingDb(_FakeDb):
        def list_cartridge_standards(self):
            return [
                {
                    "caliber_name": "6.5 Creedmoor",
                    "standard_body": "CIP",
                    "oal_mm": 71.1,
                }
            ]

    summary = mlb_module.summarize_seating_depth_advisor(
        _SeatingDb(),
        {"id": 4, "caliber": "6.5 Creedmoor", "jam_length_cbto_mm": 56.2},
        {"id": 7, "name": "ELD-M", "caliber": "6.5 Creedmoor"},
        coal_mm=71.4,
        cbto_mm=56.5,
        harmonics={"sensitivity": {"seating_depth": 1.6}},
    )

    assert summary["level"] == "critical"
    assert summary["jump_mm"] < 0
    assert "into the lands" in summary["title"].lower()
    assert any("COAL 71.40 mm" in item for item in summary["checks"])


def test_summarize_seating_depth_advisor_reports_working_window_with_harmonics_context():
    class _SeatingDb(_FakeDb):
        def list_cartridge_standards(self):
            return [
                {
                    "caliber_name": ".308 Winchester",
                    "standard_body": "SAAMI",
                    "oal_mm": 71.12,
                    "case_length_mm": 51.18,
                    "freebore_mm": 0.10,
                    "neck_diameter_mm": 8.72,
                }
            ]

    summary = mlb_module.summarize_seating_depth_advisor(
        _SeatingDb(),
        {
            "id": 8,
            "caliber": ".308 Winchester",
            "jam_length_cbto_mm": 57.0,
            "freebore_mm": 0.22,
        },
        {"id": 11, "name": "SMK", "caliber": ".308 Winchester"},
        coal_mm=71.0,
        cbto_mm=56.2,
        profile_details={"chamber_neck_diameter_mm": 8.69},
        barrel_details={
            "throat_erosion_mm": 0.12,
            "freebore_mm": 0.22,
            "muzzle_device_type": "suppressor",
        },
        harmonics={"sensitivity": {"seating_depth": 1.2}},
        subsonic_mode=True,
        stability_context={"level": "warning"},
        subsonic_context={"level": "ok"},
        subsonic_history={"level": "warning"},
    )

    assert summary["level"] == "ok"
    assert 0.35 <= summary["jump_mm"] <= 1.2
    assert "working window" in summary["title"].lower()
    assert any("throat erosion" in item.lower() for item in summary["checks"])
    assert any("neck clearance" in item.lower() for item in summary["checks"])
    assert any(
        "freebore" in item.lower()
        and ("deviation" in item.lower() or "delta" in item.lower())
        for item in summary["checks"]
    )
    assert "Jump +0.80 mm" in summary["visualization_html"]
    assert "Cartridge / chamber view" in summary["visualization_html"]
    assert "M mouth, O ogive, L lands, S standard" in summary["visualization_html"]
    assert "neck est" in summary["visualization_html"]
    assert "freebore" in summary["visualization_html"]
    assert "seat sens" in summary["visualization_html"]
    assert "Sub" in summary["visualization_html"]
    assert "History" in summary["visualization_html"]
    assert "Suppressor" in summary["visualization_html"]


def test_summarize_seating_depth_advisor_uses_saved_lot_profile_when_available():
    class _SeatingDb(_FakeDb):
        def list_cartridge_standards(self):
            return [
                {
                    "caliber_name": "6.5 Creedmoor",
                    "standard_body": "CIP",
                    "oal_mm": 71.10,
                }
            ]

        def get_seating_depth_profile(
            self, rifle_id, bullet_id, component_lot_id=None, barrel_id=None
        ):
            assert barrel_id == "pipe-b"
            return {
                "preferred_jump_mm": 0.22,
                "preferred_cbto_mm": 56.05,
                "jam_cbto_mm": 56.27,
            }

    summary = mlb_module.summarize_seating_depth_advisor(
        _SeatingDb(),
        {"id": 4, "caliber": "6.5 Creedmoor"},
        {
            "id": 7,
            "name": "ELD-M",
            "caliber": "6.5 Creedmoor",
            "selected_lot_id": 99,
            "selected_lot_number": "LOT-A",
        },
        coal_mm=71.0,
        cbto_mm=56.05,
        profile_details={"selected_barrel_id": "pipe-b"},
        barrel_details={"id": "pipe-b"},
    )

    assert abs(summary["jump_mm"] - 0.22) < 1e-6
    assert any("Lagret seating-profil" in item for item in summary["checks"])
    assert any("lot LOT-A" in item for item in summary["checks"])


def test_summarize_seating_depth_advisor_prefers_matching_barrel_jump_history():
    class _SeatingDb(_FakeDb):
        def list_cartridge_standards(self):
            return []

        def execute_query(self, query, params=()):
            normalized = " ".join(query.split())
            if "FROM rifle_bullet_jump_measurements" in normalized:
                assert params == (4, 7, "pipe-b", "pipe-b", "pipe-b")
                return [{"jam_cbto_mm": 56.18}]
            return []

    summary = mlb_module.summarize_seating_depth_advisor(
        _SeatingDb(),
        {"id": 4, "caliber": "6.5 Creedmoor"},
        {"id": 7, "name": "ELD-M", "caliber": "6.5 Creedmoor"},
        coal_mm=71.0,
        cbto_mm=55.98,
        profile_details={"selected_barrel_id": "pipe-b"},
        barrel_details={"id": "pipe-b"},
    )

    assert abs(summary["jam_cbto_mm"] - 56.18) < 1e-6
    assert abs(summary["jump_mm"] - 0.20) < 1e-6


def test_build_seating_profile_compare_text_reports_active_lot_vs_reference():
    class _CompareDb(_FakeDb):
        def list_seating_depth_profiles(self, rifle_id, bullet_id, barrel_id=None):
            assert barrel_id == "pipe-b"
            return [
                {
                    "barrel_id": "pipe-b",
                    "component_lot_id": 99,
                    "preferred_jump_mm": 0.18,
                    "preferred_cbto_mm": 56.02,
                    "notes": "Aktiv lot satt litt kortere for stabil mating.",
                },
                {
                    "barrel_id": None,
                    "component_lot_id": None,
                    "preferred_jump_mm": 0.24,
                    "preferred_cbto_mm": 55.96,
                    "notes": "Generell referanseprofil.",
                },
                {
                    "barrel_id": "pipe-x",
                    "component_lot_id": None,
                    "preferred_jump_mm": 0.40,
                    "preferred_cbto_mm": 55.70,
                    "notes": "Annet løp skal ikke vises her.",
                },
            ]

    class _Widget(mlb_module.ModernLoadBuilder):
        def __init__(self):
            super().__init__()
            self.db = _CompareDb()
            self.rifle_data = {"id": 5}
            self.bullet_data = {
                "id": 7,
                "selected_lot_id": 99,
                "selected_lot_number": "LOT-A",
            }
            self._get_active_barrel_id = lambda: "pipe-b"

    widget = _Widget()
    text = widget._build_seating_profile_compare_text()

    assert "aktiv lot LOT-A" in text
    assert "Jump 0.18 mm vs 0.24 mm (-0.06 mm)." in text
    assert "Generell referanseprofil." in text


def test_summarize_seating_depth_advisor_reports_best_known_history_match():
    class _HistoryDb(_FakeDb):
        def list_cartridge_standards(self):
            return [
                {
                    "caliber_name": "6.5 Creedmoor",
                    "standard_body": "CIP",
                    "oal_mm": 71.10,
                }
            ]

        def get_best_seating_depth_evidence(
            self,
            rifle_id,
            bullet_id,
            component_lot_id=None,
            lot_number=None,
            target_temperature_c=None,
            target_distance_m=None,
            target_throat_erosion_mm=None,
            barrel_id=None,
            include_ranked=False,
        ):
            assert barrel_id == "pipe-b"
            return {
                "cbto_mm": 56.00,
                "coal_mm": 71.02,
                "lot_number": "LOT-A",
                "matches_selected_lot": True,
                "best_group_moa": 0.31,
                "best_es_fps": 8.0,
                "best_sd_fps": 3.5,
                "confidence": "high",
                "temperature_delta_c": 2.0,
                "distance_delta_m": 0.0,
                "throat_delta_mm": 0.01,
                "ranked_candidates": [
                    {"cbto_mm": 55.98, "best_group_moa": 0.42},
                    {"cbto_mm": 56.00, "best_group_moa": 0.31},
                    {"cbto_mm": 56.04, "best_group_moa": 0.36},
                ],
            }

    summary = mlb_module.summarize_seating_depth_advisor(
        _HistoryDb(),
        {"id": 4, "caliber": "6.5 Creedmoor", "jam_length_cbto_mm": 56.25},
        {
            "id": 7,
            "name": "ELD-M",
            "caliber": "6.5 Creedmoor",
            "selected_lot_id": 99,
            "selected_lot_number": "LOT-A",
        },
        coal_mm=71.06,
        cbto_mm=56.08,
        profile_details={"selected_barrel_id": "pipe-b"},
        barrel_details={"id": "pipe-b", "throat_erosion_mm": 0.12},
        current_temperature_c=14.0,
        current_distance_m=100.0,
    )

    assert summary["best_known_evidence"]["matches_selected_lot"] is True
    assert any(
        "Best known seating from active lot LOT-A" in item for item in summary["checks"]
    )
    assert any("The current CBTO is +0.08 mm" in item for item in summary["checks"])
    assert any(
        "Temperature match versus history: 2.0 °C deviation." in item
        for item in summary["checks"]
    )
    assert any(
        "Throat erosion versus history: 0.01 mm deviation." in item
        for item in summary["checks"]
    )
    assert any("Ready for sweet spot" in item for item in summary["checks"])
    assert "Best known CBTO 56.00 mm" in summary["summary"]
    assert "Sweet spot ready" in summary["summary"]
    assert "High Evidence" in summary["confidence_html"]
    assert "green = sweet spot" in summary["history_visualization_html"]
    assert "Trend window: 55.98-56.04 mm CBTO" in summary["trend_summary_html"]
    assert summary["promotion_candidate"]["eligible"] is True


def test_summarize_seating_promotion_candidate_requires_strong_cluster():
    promotion = mlb_module._summarize_seating_promotion_candidate(
        {
            "confidence": "high",
            "cbto_mm": 56.00,
            "best_group_moa": 0.52,
            "best_es_fps": 15.0,
            "best_sd_fps": 7.0,
            "ranked_candidates": [
                {"cbto_mm": 55.90},
                {"cbto_mm": 56.00},
                {"cbto_mm": 56.15},
            ],
        },
        56.00,
    )

    assert promotion["eligible"] is False


def test_build_seating_sandbox_html_shows_delta_table():
    class _Engine:
        def calculate_load(
            self,
            rifle_id,
            bullet_id,
            powder_id,
            charge,
            coal_mm,
            cbto_mm,
            barrel_id=None,
        ):
            delta = float(cbto_mm) - 56.00
            return {
                "peak_pressure_psi": 58000 - delta * 12000,
                "muzzle_velocity_fps": 2810 - delta * 120,
                "barrel_time_ms": 1.245 + delta * 0.08,
                "jump_mm": 0.20 - delta,
            }

    html = mlb_module.build_seating_sandbox_html(
        _Engine(),
        1,
        2,
        3,
        41.5,
        71.0,
        56.0,
        current_result={
            "peak_pressure_psi": 58000,
            "muzzle_velocity_fps": 2810,
            "barrel_time_ms": 1.245,
            "jump_mm": 0.20,
        },
        barrel_id="B1",
        ranked_candidates=[
            {"cbto_mm": 55.98},
            {"cbto_mm": 56.00},
            {"cbto_mm": 56.04},
        ],
    )

    assert "Seating sandbox" in html
    assert "Barrel time" in html
    assert "+0.05 mm" in html
    assert "Now" in html
    assert "Sweet spot" in html
    assert "In Sweet Spot" in html


def test_build_seating_sandbox_html_marks_subsonic_history_windows():
    class _Engine:
        def calculate_load(
            self,
            rifle_id,
            bullet_id,
            powder_id,
            charge,
            coal_mm,
            cbto_mm,
            barrel_id=None,
        ):
            delta = float(cbto_mm) - 56.00
            return {
                "peak_pressure_psi": 58000 - delta * 12000,
                "muzzle_velocity_fps": 1020 - delta * 50,
                "barrel_time_ms": 1.245 + delta * 0.08,
                "jump_mm": 0.20 - delta,
            }

    html = mlb_module.build_seating_sandbox_html(
        _Engine(),
        1,
        2,
        3,
        12.0,
        57.0,
        56.0,
        current_result={
            "peak_pressure_psi": 58000,
            "muzzle_velocity_fps": 1020,
            "barrel_time_ms": 1.245,
            "jump_mm": 0.20,
        },
        subsonic_history={
            "successful_cbto_range": (55.99, 56.01),
            "problem_cbto_range": (56.09, 56.11),
            "successful_count": 2,
            "problem_count": 1,
        },
    )

    assert "History" in html
    assert "Similar to a Working Sub" in html
    assert "Near a Known Problem Area" in html


def test_get_published_powder_charge_window_averages_matching_sources():
    db = _FakeDb(
        rows=[
            {
                "source": "VV",
                "bullet_weight_grains": 140.0,
                "min_charge_grains": 40.0,
                "max_charge_grains": 42.0,
            },
            {
                "source": "Hodgdon",
                "bullet_weight_grains": 141.0,
                "min_charge_grains": 40.5,
                "max_charge_grains": 42.5,
            },
        ]
    )

    window = mlb_module.get_published_powder_charge_window(
        db, "6.5 Creedmoor", "N555", bullet_weight_gr=140.0
    )

    assert window is not None
    assert abs(window["avg_min_charge_grains"] - 40.25) < 1e-6
    assert abs(window["avg_max_charge_grains"] - 42.25) < 1e-6
    assert window["source_count"] == 2


def test_build_powder_sandbox_html_marks_compressed_and_published_window():
    class _Engine:
        def calculate_load(
            self,
            rifle_id,
            bullet_id,
            powder_id,
            charge,
            coal_mm,
            cbto_mm,
            barrel_id=None,
        ):
            delta = float(charge) - 41.5
            return {
                "peak_pressure_psi": 56000 + delta * 5000,
                "muzzle_velocity_fps": 2750 + delta * 60,
                "load_density_percent": 96.0 + delta * 20,
            }

    html = mlb_module.build_powder_sandbox_html(
        _Engine(),
        1,
        2,
        3,
        41.5,
        71.0,
        56.0,
        current_result={
            "peak_pressure_psi": 56000,
            "muzzle_velocity_fps": 2750,
            "load_density_percent": 96.0,
        },
        published_window={
            "avg_min_charge_grains": 41.35,
            "avg_max_charge_grains": 41.65,
        },
    )

    assert "Powder sandbox" in html
    assert "41.35 gr-41.65 gr." in html
    assert "Compressed" in html
    assert "Published" in html


def test_build_powder_sandbox_html_marks_subsonic_history_windows():
    class _Engine:
        def calculate_load(
            self,
            rifle_id,
            bullet_id,
            powder_id,
            charge,
            coal_mm,
            cbto_mm,
            barrel_id=None,
        ):
            delta = float(charge) - 12.0
            return {
                "peak_pressure_psi": 22000 + delta * 3000,
                "muzzle_velocity_fps": 1020 + delta * 80,
                "load_density_percent": 68.0 + delta * 10,
            }

    html = mlb_module.build_powder_sandbox_html(
        _Engine(),
        1,
        2,
        3,
        12.0,
        57.0,
        56.0,
        current_result={
            "peak_pressure_psi": 22000,
            "muzzle_velocity_fps": 1020,
            "load_density_percent": 68.0,
        },
        subsonic_history={
            "successful_charge_range": (11.85, 12.05),
            "problem_charge_range": (12.15, 12.30),
            "successful_count": 2,
            "problem_count": 1,
        },
    )

    assert "History" in html
    assert "Similar to a Working Sub" in html
    assert "Near a Known Problem Area" in html


def test_summarize_powder_model_advisory_reports_missing_simulation_profile():
    summary = mlb_module.summarize_powder_model_advisory(
        {
            "name": "N540",
            "validation_status": "catalog_only",
            "usable_for_simulation": 0,
            "quickload_ba_value": None,
            "qex_kj_per_kg": None,
            "k_ratio": None,
            "a0": None,
            "z1": 0.48,
            "z2": 0.83,
            "eta_cm3_per_kg": 1.0,
            "pc_kg_m3": 1620.0,
            "pcd_kg_m3": 940.0,
        }
    )

    assert summary["level"] == "critical"
    assert summary["title"] == "Powder Model Missing"
    assert "not verified" in summary["message"]
    assert "Ba" in summary["message"]


def test_summarize_powder_model_advisory_accepts_verified_profile():
    summary = mlb_module.summarize_powder_model_advisory(
        {
            "name": "N540",
            "validation_status": "verified_seed",
            "usable_for_simulation": 1,
            "data_source": "grtload:test.grtload",
        }
    )

    assert summary["level"] == "ok"
    assert summary["title"] == "Powder Model Ready"
    assert "simulation" in summary["message"]


def test_collect_safety_advisories_combines_critical_sources():
    advisories = mlb_module.collect_safety_advisories(
        {
            "peak_pressure_psi": 58000,
            "max_pressure_psi": 62000,
            "safety_margin_percent": 6.0,
            "warnings": [],
        },
        powder_context={
            "name": "N540",
            "validation_status": "catalog_only",
            "usable_for_simulation": 0,
            "quickload_ba_value": None,
            "qex_kj_per_kg": None,
            "k_ratio": None,
            "a0": None,
            "z1": 0.48,
            "z2": 0.83,
            "eta_cm3_per_kg": 1.0,
            "pc_kg_m3": 1620.0,
            "pcd_kg_m3": 940.0,
        },
        primer_context={
            "manufacturer": "CCI",
            "name": "400",
            "size": "small rifle",
        },
        internal_ballistics={
            "level": "warning",
            "title": "Internballistikk",
            "message": "Kompresjon observert.",
        },
    )

    assert len(advisories) == 4
    assert advisories[0]["title"] == "High pressure risk"
    assert advisories[1]["title"] == "Powder Model Missing"
    assert advisories[2]["title"] == "Primer Above Pressure Window"
    assert advisories[3]["title"] == "Internballistikk"


def test_summarize_retest_advisor_flags_component_and_charge_changes_against_latest_batch():
    db = _FakeDb(
        batch_rows=[
            {
                "batch_number": "BATCH-20260330-001",
                "batch_name": "Dasher baseline",
                "created_date": "2026-03-30 12:00:00",
                "charge_weight_grains": 32.2,
                "coal_mm": 59.5,
                "cbto_mm": 46.1,
                "component_snapshot_json": '{"bullet":{"id":11,"name":"105 Hybrid"},"powder":{"id":21,"name":"N540","selected_lot_number":"LOT-A"},"primer":{"id":31,"name":"CCI 450","selected_lot_number":"P-A"}}',
                "analysis_json": '{"component_context":{"bullet":{"id":11,"name":"105 Hybrid","lot_number":"B-A"},"powder":{"id":21,"name":"N540","lot_number":"LOT-A"},"primer":{"id":31,"name":"CCI 450","lot_number":"P-A"}}}',
            }
        ],
        comparison={
            "severity": "high",
            "message": "Sammenlignet med forrige lot: Snittfart +22 fps",
        },
    )

    summary = mlb_module.summarize_retest_advisor(
        db,
        rifle_id=5,
        bullet_data={"id": 12, "name": "109 LRHT", "selected_lot_number": "B-B"},
        powder_data={
            "id": 21,
            "name": "N540",
            "selected_lot_number": "LOT-B",
            "lot_comparison": {
                "severity": "high",
                "message": "Sammenlignet med forrige lot: Snittfart +22 fps",
            },
        },
        primer_data={"id": 31, "name": "CCI 450", "selected_lot_number": "P-A"},
        current_charge=32.6,
        coal_mm=59.5,
        cbto_mm=46.1,
        result={"peak_pressure_psi": 58500, "max_pressure_psi": 62000, "warnings": []},
    )

    assert summary["level"] == "critical"
    assert summary["suggested_control_shots"] == 10
    assert summary["reference_batch_number"] == "BATCH-20260330-001"
    assert any("Bullet changed" in item for item in summary["changes"])
    assert any("Charge changed" in item for item in summary["changes"])
    assert "A retest is recommended" in summary["message"]


def test_summarize_retest_advisor_reports_ok_when_no_reference_delta_is_found():
    db = _FakeDb(
        batch_rows=[
            {
                "batch_number": "BATCH-20260330-002",
                "batch_name": "Stable load",
                "created_date": "2026-03-30 12:00:00",
                "charge_weight_grains": 41.5,
                "coal_mm": 71.2,
                "cbto_mm": 55.8,
                "component_snapshot_json": '{"bullet":{"id":7,"name":"ELD-M"},"powder":{"id":8,"name":"N160","selected_lot_number":"N160-A"},"primer":{"id":9,"name":"Fed 210M","selected_lot_number":"210M-A"}}',
                "analysis_json": '{"component_context":{"bullet":{"id":7,"name":"ELD-M","lot_number":"B-1"},"powder":{"id":8,"name":"N160","lot_number":"N160-A"},"primer":{"id":9,"name":"Fed 210M","lot_number":"210M-A"}}}',
            }
        ]
    )

    summary = mlb_module.summarize_retest_advisor(
        db,
        rifle_id=9,
        bullet_data={"id": 7, "name": "ELD-M", "selected_lot_number": "B-1"},
        powder_data={"id": 8, "name": "N160", "selected_lot_number": "N160-A"},
        primer_data={"id": 9, "name": "Fed 210M", "selected_lot_number": "210M-A"},
        current_charge=41.5,
        coal_mm=71.2,
        cbto_mm=55.8,
        result={"peak_pressure_psi": 50000, "max_pressure_psi": 62000, "warnings": []},
    )

    assert summary["level"] == "ok"
    assert summary["suggested_control_shots"] == 3
    assert "No clear changes" in summary["message"]


def test_summarize_retest_advisor_uses_hunting_profile_to_raise_verification_floor():
    summary = mlb_module.summarize_retest_advisor(
        _FakeDb(),
        rifle_id=12,
        bullet_data={"id": 1, "name": "TTSX"},
        powder_data={"id": 2, "name": "N150"},
        primer_data={"id": 3, "name": "Fed 210M"},
        current_charge=46.0,
        coal_mm=71.0,
        cbto_mm=55.0,
        result={"peak_pressure_psi": 48000, "max_pressure_psi": 62000, "warnings": []},
        usage_profile="hunting_medium",
        target_es=12,
    )

    assert summary["level"] == "ok"
    assert summary["suggested_control_shots"] == 4
    assert summary["usage_profile"] == "hunting_medium"
    assert "cold-bore confirmation" in summary["message"]
    assert "ES <= 12 fps" in summary["message"]
    assert "Suggested protocol:" in summary["message"]
    assert "1 cold-bore shot" in summary["protocol_summary"]
    assert any("impact window" in step.lower() for step in summary["protocol_steps"])


def test_summarize_retest_advisor_uses_precision_profile_for_es_sd_focus():
    summary = mlb_module.summarize_retest_advisor(
        _FakeDb(),
        rifle_id=13,
        bullet_data={"id": 4, "name": "Hybrid"},
        powder_data={"id": 5, "name": "N540"},
        primer_data={"id": 6, "name": "CCI 450"},
        current_charge=32.1,
        coal_mm=59.0,
        cbto_mm=45.8,
        result={"peak_pressure_psi": 52000, "max_pressure_psi": 62000, "warnings": []},
        usage_profile="precision",
        target_es=8,
    )

    assert summary["level"] == "ok"
    assert summary["suggested_control_shots"] == 5
    assert "ES/SD" in summary["message"]
    assert "ES <= 8 fps" in summary["message"]
    assert "chrono shots in the verification series" in summary["protocol_summary"]
    assert any("vertical spread" in step.lower() for step in summary["protocol_steps"])


def test_build_retest_session_payload_uses_profile_specific_name_and_notes():
    payload = mlb_module.build_retest_session_payload(
        {
            "usage_profile": "hunting_medium",
            "suggested_control_shots": 6,
            "focus": "Prioriter cold-bore confirmation og realistisk jaktavstand før du godkjenner ladningen.",
            "protocol_summary": "1 cold-bore shot | 5 chrono shots | Confirm impact window",
            "protocol_steps": [
                "1 cold-bore shot mot realistisk jaktoppsett",
                "5 chrono shots for fart og ES",
                "Bekreft treffpunkt og forventet impact-vindu",
            ],
        }
    )

    assert payload["session_name"] == "Retest - Cold-Bore and Hunting Verification"
    assert payload["shot_count"] == 6
    assert "Focus:" in payload["notes"]
    assert "cold-bore shot" in payload["notes"]
    assert (
        payload["analysis_json"]["created_from"] == "modern_load_builder_retest_advisor"
    )


def test_summarize_primer_profile_advisory_flags_moderate_srp_for_high_pressure():
    summary = mlb_module.summarize_primer_profile_advisory(
        {
            "manufacturer": "CCI",
            "name": "400",
            "size": "small rifle",
        },
        {
            "peak_pressure_psi": 58000,
            "max_pressure_psi": 62000,
        },
    )

    assert summary["level"] == "critical"
    assert summary["title"] == "Primer Above Pressure Window"
    assert "50000 PSI" in summary["message"]


def test_summarize_primer_profile_advisory_warns_that_hard_cup_can_mask_signs():
    summary = mlb_module.summarize_primer_profile_advisory(
        {
            "manufacturer": "CCI",
            "name": "450",
            "size": "small rifle magnum",
        },
        {
            "peak_pressure_psi": 60000,
            "max_pressure_psi": 62000,
        },
    )

    assert summary["level"] == "warning"
    assert summary["title"] == "Thick Primer Cups Can Hide Signs"
    assert "late primer signs" in summary["message"]


def test_infer_primer_reference_profile_enriches_with_manufacturer_fields():
    profile = mlb_module.infer_primer_reference_profile(
        {
            "manufacturer": "Federal",
            "name": "205M",
            "size": "small rifle",
        }
    )

    assert profile["product_line"] == "Gold Medal"
    assert profile["part_number"] == "GM205M"
    assert profile["source_kind"] == "manufacturer_published+reference_inferred"
    assert profile["match_grade"] == 1


def test_apply_bullet_lot_measurements_prefers_measured_lot_averages():
    fake = type(
        "_Builder",
        (),
        {
            "db": _FakeDb(
                component_lot_rows=[
                    {
                        "id": 41,
                        "lot_number": "LOT-140A",
                        "quantity_remaining": 180,
                    }
                ],
                component_lot_stats={
                    41: {
                        "sample_count": 5,
                        "weight_avg_grains": 139.8,
                        "length_avg_mm": 34.91,
                        "diameter_avg_mm": 6.72,
                    }
                },
            ),
            "_get_component_lot_record": mlb_module.ModernLoadBuilder._get_component_lot_record,
        },
    )()

    merged = mlb_module.ModernLoadBuilder._apply_bullet_lot_measurements(
        fake,
        {
            "id": 7,
            "name": "ELD-M",
            "weight_grains": 140.0,
            "length_mm": 34.8,
            "diameter_mm": 6.71,
        },
    )

    assert merged["selected_lot_number"] == "LOT-140A"
    assert merged["nominal_weight_grains"] == 140.0
    assert merged["weight_grains"] == 139.8
    assert merged["length_mm"] == 34.91
    assert merged["diameter_mm"] == 6.72


def test_get_component_lot_record_prefers_explicit_selected_lot():
    fake = type(
        "_Builder",
        (),
        {
            "db": _FakeDb(
                component_lot_rows=[
                    {"id": 41, "lot_number": "LOT-A"},
                    {"id": 52, "lot_number": "LOT-B"},
                ]
            ),
            "_selected_component_lot_id": lambda self, component_type: None,
        },
    )()

    row = mlb_module.ModernLoadBuilder._get_component_lot_record(
        fake,
        "bullet",
        7,
        preferred_lot_id=52,
    )

    assert row["id"] == 52
    assert row["lot_number"] == "LOT-B"


def test_apply_powder_lot_context_attaches_learning_and_comparison():
    class _PowderDb(_FakeDb):
        def refresh_powder_lot_learning_profile(self, component_lot_id):
            assert component_lot_id == 55
            return {"avg_velocity_fps": 2812.0, "confidence_label": "middels"}

        def compare_powder_lots(self, component_id, current_lot_id):
            assert component_id == 8
            assert current_lot_id == 55
            return {"severity": "watch", "title": "Merkbart lotavvik"}

    fake = type(
        "_Builder",
        (),
        {
            "db": _PowderDb(
                component_lot_rows=[
                    {"id": 55, "lot_number": "N540-24A", "quantity_remaining": 750}
                ]
            ),
            "_get_component_lot_record": mlb_module.ModernLoadBuilder._get_component_lot_record,
        },
    )()

    merged = mlb_module.ModernLoadBuilder._apply_powder_lot_context(
        fake,
        {"id": 8, "name": "N540"},
    )

    assert merged["selected_lot_number"] == "N540-24A"
    assert merged["lot_learning_profile"]["avg_velocity_fps"] == 2812.0
    assert merged["lot_comparison"]["title"] == "Merkbart lotavvik"


def test_apply_primer_lot_context_attaches_learning_and_comparison():
    class _PrimerDb(_FakeDb):
        def refresh_primer_lot_learning_profile(self, component_lot_id):
            assert component_lot_id == 77
            return {"typical_es_fps": 11.5}

        def compare_primer_lots(self, component_id, current_lot_id):
            assert component_id == 4
            assert current_lot_id == 77
            return {"severity": "high", "title": "Tydelig primerlotavvik"}

    fake = type(
        "_Builder",
        (),
        {
            "db": _PrimerDb(
                component_lot_rows=[
                    {"id": 77, "lot_number": "CCI-450B", "quantity_remaining": 900}
                ]
            ),
            "_get_component_lot_record": mlb_module.ModernLoadBuilder._get_component_lot_record,
        },
    )()

    merged = mlb_module.ModernLoadBuilder._apply_primer_lot_context(
        fake,
        {"id": 4, "name": "CCI 450"},
    )

    assert merged["selected_lot_number"] == "CCI-450B"
    assert merged["lot_learning_profile"]["typical_es_fps"] == 11.5
    assert merged["lot_comparison"]["title"] == "Tydelig primerlotavvik"


def test_format_component_lot_choice_label_includes_bullet_measurement_summary():
    fake = type(
        "_Builder",
        (),
        {
            "db": _FakeDb(
                component_lot_stats={
                    41: {
                        "sample_count": 5,
                        "weight_avg_grains": 139.8,
                        "length_avg_mm": 34.91,
                    }
                }
            ),
        },
    )()

    label = mlb_module.ModernLoadBuilder._format_component_lot_choice_label(
        fake,
        "bullet",
        {"id": 41, "lot_number": "LOT-140A", "quantity_remaining": 180},
    )

    assert "LOT-140A" in label
    assert "180 remaining" in label
    assert "n=5" in label
    assert "139.8 gr" in label
    assert "34.91 mm" in label


def test_format_component_lot_choice_label_includes_learning_signals_for_powder_and_primer():
    class _LearningDb(_FakeDb):
        def refresh_powder_lot_learning_profile(self, component_lot_id):
            assert component_lot_id == 55
            return {"confidence_label": "middels", "avg_velocity_fps": 2812.0}

        def refresh_primer_lot_learning_profile(self, component_lot_id):
            assert component_lot_id == 77
            return {"typical_es_fps": 11.5, "typical_sd_fps": 4.2}

    fake = type("_Builder", (), {"db": _LearningDb()})()

    powder_label = mlb_module.ModernLoadBuilder._format_component_lot_choice_label(
        fake,
        "powder",
        {
            "id": 55,
            "component_id": 8,
            "lot_number": "N540-24A",
            "quantity_remaining": 750,
        },
    )
    primer_label = mlb_module.ModernLoadBuilder._format_component_lot_choice_label(
        fake,
        "primers",
        {
            "id": 77,
            "component_id": 4,
            "lot_number": "CCI-450B",
            "quantity_remaining": 900,
        },
    )

    assert "N540-24A" in powder_label
    assert "750 remaining" in powder_label
    assert "learning middels" in powder_label
    assert "2812 fps" in powder_label

    assert "CCI-450B" in primer_label
    assert "900 remaining" in primer_label
    assert "ES 11.5" in primer_label
    assert "SD 4.2" in primer_label


def test_build_component_context_summary_marks_standard_measured_and_learned():
    summary = mlb_module.build_component_context_summary(
        bullet_data={
            "name": "ELD-M",
            "selected_lot_number": "LOT-140A",
            "measured_lot_stats": {"sample_count": 8},
        },
        powder_data={
            "name": "N540",
            "selected_lot_number": "N540-24A",
            "lot_comparison": {"title": "Merkbart lotavvik"},
            "gordon_reference_variant_count": 2,
        },
        primer_data={
            "name": "CCI 450",
            "selected_lot_number": "CCI-450B",
            "lot_comparison": {"title": "Tydelig primerlotavvik"},
        },
    )

    assert "Measured lot average active" in summary
    assert "Powder: N540 | Lot N540-24A | Learned lot context" in summary
    assert "Powder references: 2 internal Gordon variants" in summary
    assert "Primer: CCI 450 | Lot CCI-450B | Learned lot context" in summary


def test_build_active_component_context_payload_preserves_effective_values():
    payload = mlb_module.build_active_component_context_payload(
        bullet_data={
            "id": 7,
            "name": "ELD-M",
            "selected_lot_number": "LOT-140A",
            "measured_lot_stats": {"sample_count": 8},
            "nominal_weight_grains": 140.0,
            "weight_grains": 139.8,
            "nominal_length_mm": 34.8,
            "length_mm": 34.91,
            "bc_g7": 0.315,
            "bullet_type": "Match",
            "source_label": "Gordon snapshot",
        },
        powder_data={
            "id": 8,
            "name": "N540",
            "selected_lot_number": "N540-24A",
            "validation_status": "verified_seed",
            "usable_for_simulation": 1,
            "gordon_reference_snapshot_count": 6,
            "gordon_reference_variant_count": 2,
            "quickload_ba_value": 0.5816,
            "qex_kj_per_kg": 4000.0,
            "k_ratio": 1.228,
            "eta_cm3_per_kg": 1.0,
            "pc_kg_m3": 1620.0,
            "pt_c": 10.0,
            "temp_stable": 1,
            "data_source": "gordon_readable",
            "lot_comparison": {"title": "Merkbart lotavvik", "severity": "watch"},
        },
        primer_data={
            "id": 4,
            "name": "CCI 450",
            "selected_lot_number": "CCI-450B",
            "lot_comparison": {"title": "Tydelig primerlotavvik", "severity": "high"},
        },
    )

    assert payload["bullet"]["uses_measured_lot_stats"] is True
    assert payload["bullet"]["effective_weight_grains"] == 139.8
    assert payload["bullet"]["bc_g7"] == 0.315
    assert payload["bullet"]["bullet_type"] == "Match"
    assert payload["bullet"]["source_label"] == "Gordon snapshot"
    assert payload["powder"]["usable_for_simulation"] == 1
    assert payload["powder"]["gordon_reference_snapshot_count"] == 6
    assert payload["powder"]["gordon_reference_variant_count"] == 2
    assert payload["powder"]["quickload_ba_value"] == 0.5816
    assert payload["powder"]["qex_kj_per_kg"] == 4000.0
    assert payload["powder"]["temp_stable"] == 1
    assert payload["powder"]["data_source"] == "gordon_readable"
    assert payload["powder"]["lot_learning_title"] == "Merkbart lotavvik"
    assert payload["primer"]["lot_learning_severity"] == "high"


def test_summarize_primer_lot_advisory_reports_ignition_guidance():
    db = _FakeDb(
        primer_rows=[{"id": 9}],
        primer_comparison={
            "severity": "high",
            "title": "Tydelig primerlotavvik",
            "message": "Sammenlignet med forrige lot: ES +9.5",
            "current_profile": {"confidence_label": "lav"},
            "verification_plan": {
                "focus": "Chrono minst 5 kontrollskudd og følg spesielt med på ES/SD og tidlige trykktegn."
            },
        },
    )

    summary = mlb_module.summarize_primer_lot_advisory(db, 321)

    assert summary["level"] == "critical"
    assert summary["title"] == "Tydelig primerlotavvik"
    assert "ES +9.5" in summary["message"]
    assert "lav" in summary["message"].lower()
    assert "Uncertainty" in summary["message"]
    assert "ES/SD" in summary["message"]


def test_summarize_component_verification_plan_combines_multiple_lot_signals():
    db = _FakeDb(
        rows=[{"id": 7}],
        comparison={
            "severity": "watch",
            "title": "Merkbart lotavvik",
            "message": "Sammenlignet med forrige lot: Snittfart +14.0 fps",
            "current_profile": {"confidence_label": "middels"},
            "verification_plan": {
                "focus": "Start 0.1 gr under forrige ladning og chrono 3 kontrollskudd.",
                "start_delta_grains": -0.1,
            },
        },
        bullet_rows=[{"id": 12}],
        bullet_comparison={
            "severity": "watch",
            "title": "Merkbart kulelotavvik",
            "message": "Sammenlignet med forrige lot: Typisk gruppe +0.120 MOA",
            "current_profile": {"confidence_label": "høy"},
            "verification_plan": {
                "focus": "Skyt 3 kontrollskudd og se etter gruppedrift eller urolig seating-respons."
            },
        },
        primer_rows=[{"id": 9}],
        primer_comparison={
            "severity": "high",
            "title": "Tydelig primerlotavvik",
            "message": "Sammenlignet med forrige lot: ES +9.5",
            "current_profile": {"confidence_label": "lav"},
            "verification_plan": {
                "focus": "Chrono minst 5 kontrollskudd og følg spesielt med på ES/SD og tidlige trykktegn."
            },
        },
    )

    summary = mlb_module.summarize_component_verification_plan(db, 123, 456, 789)

    assert summary["level"] == "critical"
    assert summary["title"] == "Combined Verification"
    assert "Powder Lot" in summary["message"]
    assert "Bullet Lot" in summary["message"]
    assert "Primer Lot" in summary["message"]
    assert "confidence" in summary["message"].lower()
    assert "uncertainty" in summary["message"].lower()


def test_summarize_builder_impact_window_reports_hunting_margin():
    db = _FakeDb()

    summary = mlb_module.summarize_builder_impact_window(
        db,
        {"id": 2},
        {"muzzle_velocity_fps": 2700.0},
        usage_profile="hunting_medium",
    )

    assert summary["level"] in {"ok", "warning"}
    assert summary["title"] == "Impact Window"
    assert "fps" in summary["message"]


def test_summarize_builder_impact_window_is_neutral_for_non_hunting_profile():
    db = _FakeDb()

    summary = mlb_module.summarize_builder_impact_window(
        db,
        {"id": 2},
        {"muzzle_velocity_fps": 2700.0},
        usage_profile="precision",
    )

    assert summary["level"] == "neutral"
    assert "hunting-oriented" in summary["message"].lower()


def test_summarize_builder_calibration_profile_combines_workflow_learning():
    class _CalibrationDb(_FakeDb):
        def __init__(self):
            super().__init__()
            self._engine_rows = [{"samples_used": 9, "mse": 16.0}]

        def get_barrel_learning_profile(self, rifle_id, barrel_id, barrel_name):
            return {
                "calibration_offset_fps": 11.0,
                "temp_sensitivity_fps_per_c": 0.8,
                "cold_bore_shift_moa": 0.35,
                "confidence_label": "hoy",
            }

        def compare_powder_lots(self, component_id, current_lot_id):
            return {
                "current_profile": {
                    "velocity_offset_fps": 14.0,
                    "temp_sensitivity_fps_per_c": 0.5,
                    "confidence_score": 62.0,
                }
            }

        def compare_primer_lots(self, component_id, current_lot_id):
            return {
                "current_profile": {
                    "typical_es_fps": 12.0,
                    "confidence_score": 35.0,
                }
            }

        def execute_query(self, query, params=()):
            normalized = " ".join(query.split())
            if "FROM engine_calibrations" in normalized:
                return list(self._engine_rows)
            if (
                "FROM component_lots" in normalized
                and "component_type = 'powder'" in normalized
            ):
                return [{"id": 55}]
            if (
                "FROM component_lots" in normalized
                and "component_type = 'primers'" in normalized
            ):
                return [{"id": 77}]
            return super().execute_query(query, params)

    summary = mlb_module.summarize_builder_calibration_profile(
        _CalibrationDb(),
        {"id": 10},
        22,
        "Proof",
        123,
        456,
        789,
        321,
    )

    assert summary["level"] in {"ok", "warning", "critical"}
    assert summary["title"] == "Kalibreringsprofil"
    assert (
        "Powder Lot Offset" in summary["message"]
        or "Barrel offset" in summary["message"]
    )
    assert "Powder Lot Offset" in summary["message"]
    assert "Engine Calibration" in summary["message"]


def test_summarize_builder_evidence_basis_labels_measured_modeled_and_recommended():
    summary = mlb_module.summarize_builder_evidence_basis(
        {
            "muzzle_velocity_fps": 2700.0,
            "peak_pressure_psi": 56000.0,
            "safety_margin_percent": 12.5,
            "load_density_percent": 97.5,
            "powder_name": "H4350",
            "case_capacity_ml": 3.4,
            "barrel_length_inches": 24.0,
            "warnings": ["Near max pressure"],
        }
    )

    assert summary["title"] == "Data Foundation"
    assert "Measured:" in summary["message"]
    assert "Modeled:" in summary["message"]
    assert "Recommended:" in summary["message"]
    assert "Input quality:" in summary["message"]
    assert "Fyllrate" in summary["message"]


def test_builder_internal_ballistics_summary_reports_compression_window():
    summary = mlb_module.build_internal_ballistics_summary(
        load_density_percent=101.5,
        barrel_length_in=24.0,
        burn_rate_position="medium",
    )

    assert summary["title"] == "Internballistikk"
    assert summary["compression_ratio"] is not None
    assert summary["burn_completeness_percent"] is not None
