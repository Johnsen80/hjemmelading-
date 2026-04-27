import json
from pathlib import Path
from uuid import uuid4

from src.database.database import Database
from src.modules.smart_ammo_engine import (
    build_engine_input_from_runtime,
    build_engine_result_from_input,
    build_smart_ammo_engine,
)
from src.tools.load_development_session_service import create_load_development_session


def test_build_engine_input_from_runtime_normalizes_canonical_sections():
    runtime = {
        "session": {
            "id": 12,
            "workflow_id": 4,
            "usage_profile_key": "precision",
            "usage_profile_name": "Precision",
            "next_action": "confirm_node",
            "safety_status": "ok",
            "confidence_label": "medium",
            "confidence_score": 62.5,
        },
        "context": {
            "load_session_id": 12,
            "rifle_id": 7,
            "rifle_name": "Match Rifle",
            "rifle_caliber": "6.5 CM",
            "barrel_id": "pipe-1",
            "barrel_name": "26in Match",
            "barrel_configuration_id": "pipe-1:suppressed",
            "barrel_configuration_name": "Suppressed",
        },
        "barrel": {
            "barrel_id": "pipe-1",
            "barrel_name": "26in Match",
            "barrel_configuration_id": "pipe-1:suppressed",
            "barrel_configuration_name": "Suppressed",
            "learning_profile": {"harmonic_score": 78.0},
        },
        "components": {
            "selection": {
                "bullet_id": 1,
                "powder_id": 2,
                "primer_id": 3,
                "case_id": 4,
                "powder_lot_id": 8,
            },
            "bullet": {"id": 1, "name": "147 ELD-M"},
            "powder": {"id": 2, "name": "N555"},
        },
        "lots": {
            "powder": {"id": 8, "lot_number": "VV-1"},
        },
        "recommendation": {
            "active_settings": {
                "charge_weight_gr": 42.0,
                "coal_mm": 71.5,
                "cbto_mm": 68.92,
            },
            "baseline": {"charge_gr": 42.0, "coal_mm": 71.5, "cbto_mm": 68.92},
            "pressure_assessment": {"status": "ok"},
            "internal_ballistics": {"fill_ratio_percent": 91.0},
        },
        "evidence": {
            "summary": {
                "batch_spread_signal_hint": "node_or_barrel_timing_signal",
                "batch_spread_evidence_quality": {"level": "moderate", "score": 61.0},
            }
        },
        "learning": {
            "aggregate": {
                "model_status": "delvis kalibrert",
                "next_focus": "confirm_node",
            },
        },
    }

    engine_input = build_engine_input_from_runtime(runtime)

    assert engine_input["session"]["load_session_id"] == 12
    assert engine_input["weapon"]["rifle_name"] == "Match Rifle"
    assert engine_input["barrel"]["barrel_configuration_name"] == "Suppressed"
    assert engine_input["load"]["charge_weight_gr"] == 42.0
    assert (
        engine_input["physics_inputs"]["internal_ballistics"]["fill_ratio_percent"]
        == 91.0
    )
    assert (
        engine_input["evidence"]["summary"]["batch_spread_signal_hint"]
        == "node_or_barrel_timing_signal"
    )


def test_build_engine_input_from_runtime_resolves_component_lot_environment_and_measured_context():
    runtime = {
        "session": {
            "id": 12,
            "rifle_id": 7,
            "rifle_name": "Match Rifle",
            "rifle_caliber": "6.5 CM",
            "usage_profile_key": "precision",
            "usage_profile_name": "Precision",
        },
        "components": {
            "selection": {
                "bullet_id": 1,
                "powder_id": 2,
                "primer_id": 3,
                "case_id": 4,
            },
            "bullet": {"id": 1, "manufacturer": "Hornady", "name": "147 ELD-M"},
            "powder": {"id": 2, "manufacturer": "Vihtavuori", "name": "N555"},
            "primer": {"id": 3, "manufacturer": "CCI", "name": "BR-4"},
            "case": {"id": 4, "manufacturer": "Lapua", "name": "SRP"},
            "case_learning_profile": {"status": "stable", "confidence_score": 71.0},
        },
        "lots": {
            "bullet": {
                "id": 11,
                "lot_number": "B-LOT-1",
                "learning_profile": {"confidence_label": "high"},
            },
            "powder": {
                "id": 12,
                "lot_number": "P-LOT-9",
                "learning_profile": {"watch_flag": True, "confidence_label": "watch"},
            },
        },
        "recommendation": {
            "active_settings": {
                "temperature_c": 12.0,
                "pressure_hpa": 1008.0,
                "humidity_percent": 55.0,
                "altitude_m": 325.0,
            }
        },
        "evidence": {
            "summary": {
                "chronograph_import_count": 1,
                "test_result_count": 2,
                "range_session_count": 1,
                "pressure_sign_count": 0,
                "has_measured_velocity": True,
                "has_measured_group": True,
                "latest_avg_velocity_fps": 2812.4,
                "best_group_mm": 18.6,
                "primer_review_status": "captured",
                "batch_spread_signal_hint": "node_or_barrel_timing_signal",
                "batch_spread_evidence_quality": {"level": "moderate", "score": 61.0},
            },
            "primer_review": {"status": "captured"},
        },
    }

    engine_input = build_engine_input_from_runtime(runtime)

    assert engine_input["components"]["status"] == "known"
    assert engine_input["components"]["active_component_count"] == 4
    assert engine_input["components"]["bullet"]["label"] == "Hornady 147 ELD-M"
    assert engine_input["components"]["powder"]["selected"] is True
    assert engine_input["components"]["case_learning_profile"]["status"] == "stable"
    assert engine_input["lots"]["status"] == "watch"
    assert engine_input["lots"]["active_lot_count"] == 2
    assert engine_input["lots"]["powder"]["watch_flag"] is True
    assert engine_input["environment"]["status"] == "known"
    assert engine_input["environment"]["source"] == "active_settings"
    assert engine_input["environment"]["density_altitude_m"] is not None
    assert engine_input["evidence"]["status"] == "measured"
    assert engine_input["evidence"]["measured"]["chronograph_import_count"] == 1
    assert engine_input["evidence"]["measured"]["latest_avg_velocity_fps"] == 2812.4
    assert engine_input["evidence"]["measured"]["best_group_mm"] == 18.6


def test_build_engine_result_from_input_builds_explainable_local_output():
    engine_input = {
        "session": {
            "usage_profile_name": "Precision",
            "next_action": "confirm_node",
            "safety_status": "ok",
        },
        "weapon": {"rifle_name": "Match Rifle"},
        "barrel": {
            "barrel_name": "26in Match",
            "barrel_configuration_name": "Suppressed",
            "learning_profile": {
                "harmonic_score": 78.0,
                "node_bands": [{"label": "node-a"}],
            },
        },
        "components": {
            "bullet": {"id": 1},
            "powder": {"id": 2},
            "primer": {"id": 3},
            "case": {"id": 4},
        },
        "lots": {
            "bullet": {"id": 11},
            "powder": {"id": 12},
        },
        "load": {"coal_mm": 71.5, "cbto_mm": 68.92},
        "physics_inputs": {
            "pressure_assessment": {"status": "ok", "summary": "No pressure watch."},
            "internal_ballistics": {"fill_ratio_percent": 91.0},
        },
        "evidence": {
            "summary": {
                "batch_spread_signal_hint": "node_or_barrel_timing_signal",
                "batch_spread_evidence_quality": {"level": "moderate", "score": 61.0},
                "batch_spread_validation_status": {"status": "repeat_before_tuning"},
            }
        },
        "learning": {
            "aggregate": {
                "model_status": "delvis kalibrert",
                "next_focus": "confirm_node",
            },
        },
    }

    engine_result = build_engine_result_from_input(engine_input)

    assert engine_result["engine_state"]["offline_only"] is True
    assert engine_result["engine_state"]["external_ai_used"] is False
    assert engine_result["harmonics"]["status"] == "known"
    assert engine_result["seating_jump"]["recommended_next_change"] == "seating_first"
    assert (
        engine_result["decisions"]["next_test"]["recommended_action"]
        == "seating_depth_bracket"
    )
    assert engine_result["candidate_profile"]["node_fit"] == "developing"
    assert (
        engine_result["decisions"]["recommendation_stack"][0]["action"]
        == "seating_depth_bracket"
    )
    assert (
        engine_result["decisions"]["guidance"]["title"]
        == "Confirm seating depth before broader tuning"
    )
    assert (
        "small seating-depth bracket"
        in engine_result["decisions"]["guidance"]["setup_line"]
    )
    assert (
        engine_result["decisions"]["validation_gate"]["label"]
        == "Needs matched evidence"
    )
    assert (
        engine_result["decisions"]["execution_plan"]["session_type"]
        == "seating_validation"
    )
    assert engine_result["decisions"]["execution_plan"]["estimated_rounds"] == 9
    assert (
        "Keep charge weight fixed."
        in engine_result["decisions"]["execution_plan"]["keep_constant"]
    )
    assert (
        "One control group at current seating"
        in engine_result["decisions"]["execution_plan"]["capture"]
    )
    assert (
        "Do not change powder charge before the seating-depth check is complete."
        in engine_result["decisions"]["do_not_change_yet"]
    )
    assert engine_result["decisions"]["blocked_by"][0]["kind"] == "evidence"
    assert engine_result["decisions"]["recommendation_confidence"]["level"] == "low"
    assert (
        engine_result["decisions"]["recommendation_confidence"]["uncertainty"]
        == "evidence"
    )


def test_build_engine_result_from_input_blocks_on_pressure_and_internal_ballistics():
    engine_input = {
        "session": {
            "usage_profile_name": "Precision",
            "next_action": "confirm_node",
            "safety_status": "warning",
        },
        "weapon": {"rifle_name": "Pressure Rifle"},
        "components": {
            "bullet": {"id": 1},
            "powder": {"id": 2},
            "case": {"id": 4},
        },
        "physics_inputs": {
            "pressure_assessment": {
                "status": "warning",
                "summary": "Pressure signs detected.",
            },
        },
        "derived": {
            "internal_ballistics_summary": {
                "level": "critical",
                "message": "Compressed and high-risk.",
            }
        },
        "evidence": {"summary": {}},
        "learning": {"aggregate": {}},
    }

    engine_result = build_engine_result_from_input(engine_input)

    assert engine_result["safety"]["blocked"] is True
    assert engine_result["decisions"]["candidate_ranking"]["status"] == "blocked"
    assert (
        engine_result["decisions"]["next_test"]["recommended_action"]
        == "stop_and_review"
    )
    assert engine_result["decisions"]["recommendation_stack"][0]["area"] == "safety"
    assert engine_result["decisions"]["validation_gate"]["status"] == "blocked"
    assert (
        engine_result["decisions"]["execution_plan"]["session_type"] == "safety_review"
    )
    assert (
        "Any new pressure sign"
        in engine_result["decisions"]["execution_plan"]["stop_conditions"]
    )
    assert engine_result["decisions"]["blocked_by"][0]["kind"] == "safety"
    assert engine_result["decisions"]["recommendation_confidence"]["level"] == "low"


def test_build_engine_result_from_input_prefers_return_to_charge_baseline_before_new_tuning():
    engine_input = {
        "session": {
            "usage_profile_name": "Precision",
            "next_action": "confirm_node",
            "safety_status": "ok",
        },
        "weapon": {"rifle_name": "Baseline Rifle"},
        "barrel": {
            "barrel_name": "26in Match",
            "learning_profile": {
                "harmonic_score": 78.0,
                "node_bands": [{"label": "node-a"}],
            },
        },
        "components": {
            "bullet": {"id": 1},
            "powder": {"id": 2},
            "case": {"id": 4},
        },
        "load": {
            "charge_weight_gr": 42.4,
            "coal_mm": 71.5,
            "cbto_mm": 68.92,
            "baseline": {
                "charge_gr": 42.0,
                "charge_source": "learned",
                "cbto_mm": 68.92,
                "seating_source": "learned",
            },
            "control_state": {
                "charge_state": "custom",
                "seating_state": "learned",
            },
        },
        "physics_inputs": {
            "pressure_assessment": {"status": "ok", "summary": "No pressure watch."},
        },
        "evidence": {
            "summary": {
                "batch_spread_evidence_quality": {"level": "moderate", "score": 61.0},
            }
        },
        "learning": {
            "aggregate": {
                "model_status": "delvis kalibrert",
                "next_focus": "confirm_node",
            },
        },
        "derived": {
            "harmonics_profile": {
                "harmonic_score": 78.0,
                "stability_tier": "stable",
                "node_bands": [{"label": "node-a"}],
            }
        },
    }

    engine_result = build_engine_result_from_input(engine_input)

    assert (
        engine_result["decisions"]["next_test"]["recommended_action"]
        == "return_to_charge_baseline"
    )
    assert (
        engine_result["decisions"]["guidance"]["title"]
        == "Return to the frozen charge baseline first"
    )
    assert (
        engine_result["decisions"]["validation_gate"]["status"] == "return_to_baseline"
    )
    assert engine_result["baseline_control"]["charge_alignment"] == "outside"
    assert engine_result["baseline_control"]["branch_state"] == "custom_branch"
    assert engine_result["baseline_control"]["should_return_before_compare"] is True
    assert (
        engine_result["baseline_control"]["recovery_action"]
        == "return_to_charge_baseline"
    )
    assert (
        engine_result["baseline_control"]["charge_return_line"]
        == "Return charge toward 42.00 gr before treating this as the same candidate."
    )
    assert (
        engine_result["baseline_control"]["active_return_line"]
        == "Return charge toward 42.00 gr before treating this as the same candidate."
    )
    assert engine_result["return_targets"]["charge"]["label"] == "42.00 gr"
    assert (
        engine_result["return_targets"]["charge"]["return_line"]
        == "Return charge toward 42.00 gr before treating this as the same candidate."
    )
    assert engine_result["branch_advisory"]["label"] == "Custom branch"
    assert engine_result["branch_advisory"]["compare_mode"] == "return_before_compare"
    assert (
        engine_result["branch_advisory"]["display_line"]
        == "Custom branch (return_before_compare)"
    )
    assert (
        engine_result["branch_advisory"]["action_line"]
        == "Return charge toward 42.00 gr before treating this as the same candidate."
    )
    assert engine_result["baseline_diagnostics"]["status"] == "return_to_baseline"
    assert engine_result["baseline_diagnostics"]["items"][0].startswith(
        "Charge 42.40 gr is 0.40 gr away"
    )
    assert (
        engine_result["baseline_diagnostics"]["suggested_action"]
        == "Use the frozen learned charge baseline or confirm a new charge node before promoting this setup again."
    )
    assert engine_result["decisions"]["blocked_by"][0]["kind"] == "charge_baseline"
    assert (
        engine_result["decisions"]["recommendation_confidence"]["uncertainty"]
        == "baseline"
    )


def test_build_engine_result_from_input_exposes_evidence_diagnostics_for_thin_measurement_state():
    engine_input = {
        "session": {
            "usage_profile_name": "Precision",
            "next_action": "confirm_node",
            "safety_status": "ok",
            "confidence_label": "low",
            "confidence_score": 2.1,
        },
        "weapon": {"rifle_name": "Evidence Rifle"},
        "components": {
            "bullet": {"id": 1},
            "powder": {"id": 2},
            "case": {"id": 4},
        },
        "evidence": {
            "summary": {
                "has_measured_velocity": False,
                "has_measured_group": False,
                "batch_spread_evidence_quality": {"level": "thin", "score": 38.0},
            }
        },
        "learning": {"aggregate": {}},
    }

    engine_result = build_engine_result_from_input(engine_input)

    assert engine_result["evidence_diagnostics"]["status"] == "needs_measurement"
    assert (
        "Session still lacks measured chronograph data for the active setup."
        in engine_result["evidence_diagnostics"]["items"]
    )
    assert (
        "Session still lacks measured grouping data for the active setup."
        in engine_result["evidence_diagnostics"]["items"]
    )
    assert (
        "Confidence is still low, so current guidance depends on thin or partially assumed data."
        in engine_result["evidence_diagnostics"]["items"]
    )
    assert (
        engine_result["evidence_diagnostics"]["suggested_action"]
        == "Capture a chronograph string for the current setup before treating the node as verified."
    )


def test_build_engine_result_from_input_caps_unmatched_evidence_to_thin():
    engine_input = {
        "session": {
            "usage_profile_key": "precision",
            "usage_profile_name": "Precision",
            "next_action": "confirm_node",
            "safety_status": "ok",
        },
        "weapon": {"rifle_name": "Evidence Rifle"},
        "components": {
            "bullet": {"id": 1},
            "powder": {"id": 2},
            "case": {"id": 4},
        },
        "evidence": {
            "summary": {
                "has_measured_velocity": True,
                "has_measured_group": False,
                "chronograph_import_count": 1,
                "test_result_count": 0,
                "batch_spread_signal_hint": "velocity_only",
                "batch_spread_evidence_quality": {"level": "moderate", "score": 67.0},
            }
        },
        "learning": {"aggregate": {}},
    }

    engine_result = build_engine_result_from_input(engine_input)

    assert engine_result["evidence"]["status"] == "thin"
    assert engine_result["evidence"]["matched_status"] == "velocity_only"
    assert engine_result["candidate_profile"]["evidence_gate"] == "thin"
    assert engine_result["evidence_diagnostics"]["status"] == "needs_measurement"
    assert (
        engine_result["decisions"]["validation_gate"]["label"]
        == "Needs matched evidence"
    )


def test_build_engine_result_from_input_adds_cold_bore_and_mixed_signal_channels():
    engine_input = {
        "session": {
            "usage_profile_key": "hunting",
            "usage_profile_name": "Hunting",
            "next_action": "confirm_node",
            "safety_status": "ok",
        },
        "weapon": {"rifle_name": "Field Rifle"},
        "components": {
            "bullet": {"id": 1},
            "powder": {"id": 2},
            "case": {"id": 4},
        },
        "evidence": {
            "summary": {
                "has_measured_velocity": True,
                "has_measured_group": True,
                "chronograph_import_count": 1,
                "test_result_count": 1,
                "batch_spread_signal_hint": "environment_or_condition_signal",
                "batch_spread_evidence_quality": {"level": "moderate", "score": 61.0},
                "batch_spread_validation_status": {
                    "usage_goal": "hunting",
                    "status": "field_validation_pending",
                    "next_gate": "Resolve the current spread signal, then confirm one cold-bore shot plus a short realistic-support control series.",
                },
                "batch_spread_note_flags": ["environment"],
                "batch_spread_pattern_flags": ["horizontal_dominant"],
            }
        },
        "learning": {"aggregate": {}},
    }

    engine_result = build_engine_result_from_input(engine_input)

    assert (
        engine_result["evidence"]["cold_bore"]["status"] == "field_validation_pending"
    )
    assert engine_result["evidence"]["group_pattern"]["status"] == "horizontal_watch"
    assert engine_result["evidence"]["mixed_signal"]["status"] == "mixed_signal"
    assert engine_result["evidence_diagnostics"]["status"] == "mixed_signal"
    assert any(
        "cold-bore shot" in item
        for item in engine_result["evidence_diagnostics"]["items"]
    )
    assert any(
        "Horizontal dominance" in item
        for item in engine_result["evidence_diagnostics"]["items"]
    )


def test_build_engine_result_from_input_exposes_bullet_fit_and_chamber_jump_context():
    engine_input = {
        "session": {
            "usage_profile_name": "Precision",
            "next_action": "confirm_node",
            "safety_status": "ok",
        },
        "weapon": {"rifle_name": "Jump Rifle", "caliber": "6.5 CM"},
        "components": {
            "bullet": {"id": 1},
            "powder": {"id": 2},
            "case": {"id": 4},
        },
        "load": {"coal_mm": 71.5, "cbto_mm": 68.92},
        "learning": {"aggregate": {}},
        "derived": {
            "harmonics_profile": {
                "harmonic_score": 76.0,
                "stability_tier": "stable",
                "sensitivity": {"seating_depth": 1.4},
            },
            "bullet_fit_context": {
                "fit_summary": {
                    "fit_score": 63.0,
                    "level": "warning",
                    "message": "The setup may work, but the margin is limited.",
                    "twist_assessment": "borderline",
                    "geometry_confidence": "medium",
                }
            },
            "seating_depth_context": {
                "status": "known",
                "jam_cbto_mm": 69.02,
                "current_jump_mm": 0.10,
                "preferred_jump_mm": 0.18,
                "preferred_cbto_mm": 68.84,
                "jump_band": "tight",
                "source_label": "measured profile",
                "best_evidence": {"batch_id": 33},
            },
        },
        "evidence": {
            "summary": {
                "has_measured_velocity": True,
                "has_measured_group": True,
                "batch_spread_evidence_quality": {"level": "moderate", "score": 61.0},
            }
        },
        "physics_inputs": {
            "pressure_assessment": {"status": "ok"},
        },
    }

    engine_result = build_engine_result_from_input(engine_input)

    assert engine_result["bullet_fit"]["level"] == "warning"
    assert engine_result["bullet_fit"]["twist_assessment"] == "borderline"
    assert engine_result["chamber_jump"]["jump_band"] == "tight"
    assert engine_result["chamber_jump"]["best_evidence_batch_id"] == 33
    assert engine_result["seating_jump"]["preferred_jump_mm"] == 0.18
    assert engine_result["candidate_profile"]["bullet_fit_level"] == "warning"
    assert any(
        item["kind"] == "bullet_fit"
        for item in engine_result["decisions"]["blocked_by"]
    )


def test_build_smart_ammo_engine_builds_canonical_payload_from_session():
    db_path = Path(
        f"c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/smart_ammo_engine_{uuid4().hex}.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    database = Database(str(db_path))
    try:
        rifle_id = database.insert(
            "rifles",
            {
                "name": "Engine Rifle",
                "caliber": "6.5 CM",
                "twist_rate": "1:8",
            },
        )
        bullet_id = database.insert(
            "bullets",
            {
                "name": "147 ELD-M",
                "manufacturer": "Hornady",
                "caliber": "6.5 CM",
                "weight_grains": 147.0,
            },
        )
        powder_id = database.insert(
            "powder",
            {
                "name": "N555",
                "manufacturer": "Vihtavuori",
                "burn_rate": "medium",
            },
        )
        database.insert(
            "powder_database",
            {
                "powder_id": powder_id,
                "peak_pressure_timing": "medium",
                "temp_stable": 1,
                "qex_kj_per_kg": 3800.0,
                "k_ratio": 1.22,
                "validation_status": "verified",
                "usable_for_simulation": 1,
            },
        )
        case_id = database.insert(
            "cases",
            {
                "name": "Lapua SRP",
                "manufacturer": "Lapua",
                "caliber": "6.5 CM",
                "case_capacity_gr_h2o": 52.4,
            },
        )
        bullet_lot_id = database.insert(
            "bullet_lots",
            {
                "bullet_id": bullet_id,
                "lot_number": "B-LOT-1",
                "purchase_date": "2026-04-12",
                "quantity_purchased": 100,
                "quantity_remaining": 100,
                "is_active": 1,
            },
        )
        powder_lot_id = database.insert(
            "component_lots",
            {
                "component_type": "powder",
                "component_id": powder_id,
                "lot_number": "P-LOT-1",
                "purchase_date": "2026-04-12",
                "quantity_initial": 1.0,
                "quantity_remaining": 1.0,
                "is_active": 1,
            },
        )
        session_id = create_load_development_session(
            database,
            rifle_id=rifle_id,
            rifle_name="Engine Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="precision",
            usage_profile_name="Precision",
            component_selection={
                "bullet_id": bullet_id,
                "powder_id": powder_id,
                "case_id": case_id,
                "bullet_lot_id": bullet_lot_id,
                "powder_lot_id": powder_lot_id,
            },
            recommendation={
                "active_settings": {
                    "charge_weight_gr": 42.1,
                    "coal_mm": 71.5,
                    "cbto_mm": 68.9,
                    "temperature_c": 12.0,
                    "pressure_hpa": 1008.0,
                    "humidity_percent": 55.0,
                    "altitude_m": 325.0,
                },
                "pressure_assessment": {
                    "status": "ok",
                    "summary": "No pressure watch.",
                },
                "internal_ballistics": {
                    "fill_ratio_percent": 91.0,
                },
            },
            learning_state={
                "aggregate": {
                    "confidence_label": "delvis kalibrert",
                    "next_focus": "confirm_node",
                }
            },
            confidence_label="medium",
            confidence_score=61.0,
            safety_status="ok",
            next_action="confirm_node",
        )
        database.insert(
            "rifle_profile_details",
            {
                "rifle_id": rifle_id,
                "profile_json": json.dumps(
                    {
                        "rifle_id": rifle_id,
                        "rifle_name": "Engine Rifle",
                        "selected_barrel_id": "pipe-1",
                        "barrel_length_mm": 660.4,
                        "barrels": [
                            {
                                "id": "pipe-1",
                                "name": "26in Match",
                                "length_mm": 660.4,
                                "barrel_profile": "heavy",
                                "barrel_attachment_type": "threaded",
                                "support_type": "rest",
                                "muzzle_device_type": "suppressor",
                                "muzzle_device_weight_g": 380.0,
                                "harmonic_metadata": {
                                    "tuner_mass_g": 0,
                                },
                            }
                        ],
                    }
                ),
            },
        )
        database.insert(
            "chronograph_imports",
            {
                "load_session_id": session_id,
                "velocity_count": 10,
                "velocity_avg": 2815.0,
                "velocity_es": 12.0,
                "velocity_sd": 4.2,
            },
        )
        database.insert(
            "test_results",
            {
                "load_session_id": session_id,
                "charge_weight": 42.1,
                "velocity_avg": 2814.0,
                "group_size_mm": 18.4,
            },
        )
        database.update(
            "load_development_sessions",
            {
                "barrel_id": "pipe-1",
                "barrel_name": "26in Match",
                "barrel_configuration_id": "pipe-1:suppressed",
                "barrel_configuration_name": "Suppressed",
            },
            "id = ?",
            (session_id,),
        )

        payload = build_smart_ammo_engine(database, session_id)

        assert payload is not None
        assert payload["engine_input"]["weapon"]["rifle_name"] == "Engine Rifle"
        assert (
            payload["engine_input"]["barrel"]["barrel_configuration_name"]
            == "Suppressed"
        )
        assert payload["engine_input"]["components"]["status"] == "known"
        assert payload["engine_input"]["components"]["active_component_count"] == 3
        assert payload["engine_input"]["lots"]["active_lot_count"] == 2
        assert payload["engine_input"]["lots"]["powder"]["lot_number"] == "P-LOT-1"
        assert payload["engine_input"]["environment"]["status"] == "known"
        assert payload["engine_input"]["evidence"]["status"] == "measured"
        assert (
            payload["engine_input"]["evidence"]["measured"]["latest_avg_velocity_fps"]
            == 2815.0
        )
        assert payload["engine_input"]["evidence"]["measured"]["best_group_mm"] == 18.4
        assert payload["engine_input"]["derived"]["profile_available"] is True
        assert (
            payload["engine_input"]["derived"]["harmonics_profile"]["harmonic_score"]
            is not None
        )
        assert payload["engine_result"]["engine_state"]["status"] == "ready"
        assert payload["engine_result"]["safety"]["state"] == "ok"
        assert (
            payload["engine_result"]["physics"]["internal_ballistics"]["title"]
            == "Internballistikk"
        )
        assert (
            payload["engine_result"]["physics"]["component_interaction"][
                "case_capacity_gr_h2o"
            ]
            == 52.4
        )
        assert payload["engine_result"]["harmonics"]["status"] == "known"
        assert payload["engine_result"]["candidate_profile"]["robustness_level"] in {
            "low",
            "moderate",
            "high",
        }
        assert payload["engine_result"]["decisions"]["recommendation_stack"]
        assert payload["engine_result"]["decisions"]["next_test"][
            "recommended_action"
        ] in {
            "confirm_node_window",
            "confirm_current_load",
            "repeatability_string",  # Block 5: competition+single-session routes here
        }
    finally:
        database.close()
