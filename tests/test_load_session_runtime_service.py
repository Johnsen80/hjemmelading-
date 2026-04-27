from pathlib import Path
from uuid import uuid4

from src.database.database import Database
from src.tools.load_development_session_service import create_load_development_session
from src.tools.load_session_runtime_service import (
    build_active_workflow_context_from_settings,
    build_load_session_runtime,
    build_load_session_runtime_delta,
    enrich_workflow_context_from_session,
    refresh_load_session_measurement_summary,
)


def test_build_load_session_runtime_assembles_canonical_context():
    db_path = Path(
        f"c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_session_runtime_service_{uuid4().hex}.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    database = Database(str(db_path))
    try:
        rifle_id = database.insert(
            "rifles",
            {
                "name": "Runtime Rifle",
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
            },
        )
        primer_id = database.insert(
            "primers",
            {
                "name": "BR-2",
                "manufacturer": "CCI",
            },
        )
        case_id = database.insert(
            "cases",
            {
                "name": "6.5 Creedmoor Brass",
                "manufacturer": "Lapua",
                "caliber": "6.5 CM",
            },
        )
        powder_lot_id = database.insert(
            "component_lots",
            {
                "component_type": "powder",
                "component_id": powder_id,
                "lot_number": "VV-N555-A1",
                "purchase_date": "2026-04-07",
                "quantity_initial": 1000,
                "quantity_remaining": 850,
            },
        )

        session_id = create_load_development_session(
            database,
            rifle_id=rifle_id,
            rifle_name="Runtime Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="precision",
            usage_profile_name="Presisjon / match",
            component_selection={
                "bullet_id": bullet_id,
                "powder_id": powder_id,
                "primer_id": primer_id,
                "case_id": case_id,
                "powder_lot_id": powder_lot_id,
            },
            learning_state={
                "best_history": {"group_size_moa": 0.56},
                "barrel_context": {"level": "ok", "title": "Known barrel"},
                "stability_assessment": {"level": "stable", "title": "Stable node"},
            },
            recommendation={
                "active_settings": {
                    "charge_weight_gr": 42.0,
                    "coal_mm": 71.5,
                    "cbto_mm": 68.92,
                },
                "baseline": {
                    "available": True,
                    "signature": [
                        rifle_id,
                        "pipe-1",
                        bullet_id,
                        None,
                        powder_id,
                        powder_lot_id,
                    ],
                    "charge_gr": 42.0,
                    "coal_mm": 71.5,
                    "cbto_mm": 68.92,
                    "charge_source": "recommended",
                    "seating_source": "learned",
                    "trust_label": "high",
                },
                "control_state": {
                    "available": True,
                    "charge_state": "recommended",
                    "seating_state": "learned",
                    "trust_label": "high",
                    "can_apply": False,
                },
            },
            confidence_label="medium",
            confidence_score=62.5,
            safety_status="review_required",
            next_action="build_initial_test_batches",
        )
        database.update(
            "load_development_sessions",
            {
                "barrel_id": "pipe-1",
                "barrel_name": "26in Match Pipe",
                "barrel_configuration_id": "pipe-1:suppressed",
                "barrel_configuration_name": "Suppressed",
            },
            "id = ?",
            (session_id,),
        )
        database.record_barrel_chronograph_observation(
            rifle_id,
            "pipe-1",
            "26in Match Pipe",
            {
                "session_name": "Bare validation",
                "session_date": "2026-04-06",
                "avg_velocity_fps": 2821.0,
                "es_fps": 16.0,
                "sd_fps": 6.1,
                "temperature_f": 60.0,
            },
            barrel_configuration_id="pipe-1:bare",
            barrel_configuration_name="Bare muzzle",
        )
        database.record_barrel_chronograph_observation(
            rifle_id,
            "pipe-1",
            "26in Match Pipe",
            {
                "session_name": "Suppressed validation",
                "session_date": "2026-04-07",
                "avg_velocity_fps": 2809.0,
                "es_fps": 10.0,
                "sd_fps": 4.2,
                "temperature_f": 61.0,
            },
            barrel_configuration_id="pipe-1:suppressed",
            barrel_configuration_name="Suppressed",
        )

        database.insert(
            "chronograph_imports",
            {
                "load_session_id": session_id,
                "file_path": "chrono.csv",
                "velocity_count": 5,
                "velocity_avg": 2812.4,
                "velocity_es": 14.2,
                "velocity_sd": 5.9,
            },
        )
        batch_id = database.insert(
            "batch_projects",
            {
                "batch_number": "B-1001",
                "batch_name": "Runtime Batch",
                "rifle_id": rifle_id,
                "load_session_id": session_id,
                "bullet_id": bullet_id,
                "powder_id": powder_id,
                "primer_id": primer_id,
                "case_id": case_id,
            },
        )
        database.insert(
            "batch_project_sessions",
            {
                "batch_id": batch_id,
                "load_session_id": session_id,
                "session_name": "Validation Session",
                "session_date": "2026-04-07",
                "group_size_mm": 16.4,
                "group_size_moa": 0.56,
                "analysis_json": '{"primer_image_review":{"enabled":true,"images":["reports/primer-a.jpg","reports/primer-b.jpg"],"observation":"normal reference for this rifle","batch_id":1,"rifle_id":1}}',
            },
        )
        database.insert(
            "pressure_signs",
            {
                "ammo_profile_id": None,
                "charge_weight": 42.2,
                "severity_level": "LAV",
                "notes": "Primer review reference saved from validation session.",
                "date": "2026-04-07",
                "primer_image_path": "reports/primer-a.jpg",
                "primer_image_quality": "good",
                "primer_image_observation": "normal reference for this rifle",
                "primer_image_confidence": "medium",
                "load_session_id": session_id,
                "batch_id": batch_id,
                "batch_session_id": 1,
                "rifle_id": rifle_id,
            },
        )
        database.insert(
            "test_results",
            {
                "load_session_id": session_id,
                "charge_weight": 42.2,
                "velocity_avg": 2810.0,
                "velocity_es": 15.0,
                "velocity_sd": 6.0,
                "group_size_mm": 18.2,
            },
        )

        runtime = build_load_session_runtime(database, session_id)

        assert runtime is not None
        assert runtime["session"]["id"] == session_id
        assert runtime["rifle"]["id"] == rifle_id
        assert runtime["barrel"]["barrel_id"] == "pipe-1"
        assert runtime["barrel"]["barrel_configuration_id"] == "pipe-1:suppressed"
        assert runtime["barrel"]["learning_profile"]["barrel_id"] == "pipe-1"
        assert (
            runtime["barrel"]["learning_profile"]["barrel_configuration_id"]
            == "pipe-1:suppressed"
        )
        assert runtime["barrel"]["learning_profile"]["chrono_samples"] == 1
        assert runtime["components"]["bullet"]["id"] == bullet_id
        assert runtime["components"]["case_learning_profile"]["case_id"] == case_id
        assert runtime["lots"]["powder"]["id"] == powder_lot_id
        assert runtime["lots"]["powder"]["source_table"] == "component_lots"
        assert runtime["context"]["load_session_id"] == session_id
        assert runtime["context"]["rifle_id"] == rifle_id
        assert runtime["context"]["barrel_id"] == "pipe-1"
        assert runtime["context"]["barrel_configuration_name"] == "Suppressed"
        assert runtime["context"]["powder_lot_number"] == "VV-N555-A1"
        assert runtime["identity"]["rifle"]["label"] == "Runtime Rifle"
        assert runtime["identity"]["barrel"]["configuration_label"] == "Suppressed"
        assert runtime["identity"]["components"]["powder"]["label"] == "Vihtavuori N555"
        assert runtime["identity"]["lots"]["powder"]["lot_number"] == "VV-N555-A1"
        assert runtime["learning"]["aggregate"]["confidence_label"]
        assert runtime["learning"]["aggregate"]["model_status"]
        assert runtime["learning"]["aggregate"]["weakest_link"]
        assert runtime["learning"]["barrel"]["status"]
        assert runtime["learning"]["case"]["status"]
        assert runtime["learning"]["lots"]["powder"]["lot_number"] == "VV-N555-A1"
        assert (
            runtime["learning"]["session"]["schema_version"] == "load_learning_state.v1"
        )
        assert (
            runtime["learning"]["session"]["analysis"]["barrel_context"]["title"]
            == "Known barrel"
        )
        assert (
            runtime["learning"]["session"]["analysis"]["stability_assessment"]["level"]
            == "stable"
        )
        assert (
            runtime["smart_engine"]["engine_result"]["engine_state"]["offline_only"]
            is True
        )
        assert (
            runtime["smart_engine"]["engine_result"]["identity"]["rifle_name"]
            == "Runtime Rifle"
        )
        assert runtime["delta"]["smart_engine"]["next_action"] is not None
        assert runtime["evidence"]["summary"]["chronograph_import_count"] == 1
        assert runtime["evidence"]["summary"]["batch_count"] == 1
        assert runtime["evidence"]["summary"]["pressure_sign_count"] == 1
        assert runtime["evidence"]["summary"]["latest_avg_velocity_fps"] == 2812.4
        assert runtime["evidence"]["summary"]["best_group_mm"] == 16.4
        assert runtime["evidence"]["summary"]["primer_review_status"] == "captured"
        assert runtime["evidence"]["summary"]["primer_review_session_count"] == 1
        assert runtime["evidence"]["summary"]["primer_review_image_count"] == 2
        assert runtime["evidence"]["summary"]["pressure_sign_primer_review_count"] == 1
        assert (
            runtime["evidence"]["batch_sessions"][0]["primer_image_review"]["enabled"]
            is True
        )
        assert runtime["evidence"]["batch_sessions"][0]["primer_image_images"] == [
            "reports/primer-a.jpg",
            "reports/primer-b.jpg",
        ]
        assert (
            runtime["evidence"]["primer_review"]["linked_pressure_sign_batch_count"]
            == 1
        )
        assert (
            runtime["evidence"]["primer_review"]["linked_pressure_sign_rifle_count"]
            == 1
        )
        assert runtime["status"]["next_action"] == "build_initial_test_batches"
        assert runtime["recommendation"]["baseline"]["charge_gr"] == 42.0
        assert runtime["recommendation"]["control_state"]["seating_state"] == "learned"
    finally:
        database.close()


def test_build_load_session_runtime_marks_primer_review_disabled_when_batch_sessions_opt_out():
    db_path = Path(
        f"c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_session_runtime_primer_disabled_{uuid4().hex}.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    database = Database(str(db_path))
    try:
        rifle_id = database.insert(
            "rifles",
            {
                "name": "Opt-out Rifle",
                "caliber": "308 Win",
            },
        )
        session_id = create_load_development_session(
            database,
            rifle_id=rifle_id,
            rifle_name="Opt-out Rifle",
            rifle_caliber="308 Win",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
        )
        batch_id = database.insert(
            "batch_projects",
            {
                "batch_number": "B-2001",
                "batch_name": "Opt-out Batch",
                "rifle_id": rifle_id,
                "load_session_id": session_id,
            },
        )
        database.insert(
            "batch_project_sessions",
            {
                "batch_id": batch_id,
                "load_session_id": session_id,
                "session_name": "No Primer Photos",
                "session_date": "2026-04-08",
                "analysis_json": '{"primer_image_review":{"enabled":false,"batch_id":1,"rifle_id":1}}',
            },
        )

        runtime = build_load_session_runtime(database, session_id)

        assert runtime is not None
        assert runtime["evidence"]["summary"]["primer_review_status"] == "disabled"
        assert (
            runtime["evidence"]["summary"]["primer_review_disabled_session_count"] == 1
        )
        assert runtime["evidence"]["primer_review"]["disabled_session_count"] == 1
        assert (
            runtime["evidence"]["batch_sessions"][0]["primer_image_review"]["enabled"]
            is False
        )
    finally:
        database.close()


def test_build_load_session_runtime_resolves_bullet_lot_from_legacy_table():
    db_path = Path(
        f"c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_session_runtime_legacy_lot_{uuid4().hex}.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    database = Database(str(db_path))
    try:
        bullet_id = database.insert(
            "bullets",
            {
                "name": "105 Hybrid",
                "manufacturer": "Berger",
                "caliber": "6mm",
                "weight_grains": 105.0,
            },
        )
        bullet_lot_id = database.insert(
            "bullet_lots",
            {
                "bullet_id": bullet_id,
                "lot_number": "BG-LOT-7",
                "purchase_date": "2026-04-07",
                "quantity_purchased": 500,
                "quantity_remaining": 500,
            },
        )

        session_id = create_load_development_session(
            database,
            rifle_id=None,
            rifle_name="Legacy Lot Rifle",
            rifle_caliber="6 BR",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
            component_selection={
                "bullet_id": bullet_id,
                "bullet_lot_id": bullet_lot_id,
            },
        )

        runtime = build_load_session_runtime(database, session_id)

        assert runtime is not None
        assert runtime["lots"]["bullet"]["id"] == bullet_lot_id
        assert runtime["lots"]["bullet"]["source_table"] == "bullet_lots"
        assert runtime["learning"]["lots"]["bullet"]["lot_number"] == "BG-LOT-7"
        assert runtime["components"]["bullet"]["id"] == bullet_id
    finally:
        database.close()


def test_build_load_session_runtime_accepts_plural_primer_component_type():
    db_path = Path(
        f"c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_session_runtime_primer_plural_{uuid4().hex}.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    database = Database(str(db_path))
    try:
        primer_id = database.insert(
            "primers",
            {
                "name": "205M",
                "manufacturer": "Federal",
            },
        )
        primer_lot_id = database.insert(
            "component_lots",
            {
                "component_type": "primers",
                "component_id": primer_id,
                "lot_number": "FED-205M-L1",
                "purchase_date": "2026-04-07",
                "quantity_initial": 1000,
                "quantity_remaining": 900,
            },
        )

        session_id = create_load_development_session(
            database,
            rifle_id=None,
            rifle_name="Primer Alias Rifle",
            rifle_caliber="223 Rem",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
            component_selection={
                "primer_id": primer_id,
                "primer_lot_id": primer_lot_id,
            },
        )

        runtime = build_load_session_runtime(database, session_id)

        assert runtime is not None
        assert runtime["lots"]["primer"]["id"] == primer_lot_id
        assert runtime["lots"]["primer"]["lot_number"] == "FED-205M-L1"
    finally:
        database.close()


def test_build_load_session_runtime_delta_reports_charge_and_coal_deviation():
    delta = build_load_session_runtime_delta(
        {
            "evidence": {
                "summary": {
                    "has_measured_velocity": False,
                    "has_measured_group": False,
                }
            },
            "session": {
                "recommended_charge_min_gr": 41.8,
                "recommended_charge_max_gr": 42.2,
                "recommended_coal_min": 70.8,
                "recommended_coal_max": 71.2,
                "safety_status": "caution",
                "confidence_label": "low",
                "confidence_score": 1.75,
                "intake_snapshot_json": {
                    "charge_weight_gr": 42.5,
                    "coal_mm": 70.5,
                },
                "evidence_summary_json": {
                    "latest_result": {
                        "load_density_percent": 104.2,
                    }
                },
            },
        }
    )

    assert delta["level"] == "warning"
    assert any("above the suggested window" in item for item in delta["items"])
    assert any(
        "shorter than the current recommended band" in item for item in delta["items"]
    )
    assert any("Safety state is caution" in item for item in delta["items"])
    assert delta["impacts"]
    assert "pressure margin" in delta["focus_areas"]
    assert "data trust" in delta["focus_areas"]
    assert "velocity validation" in delta["focus_areas"]
    assert isinstance(delta["suggested_action"], str)
    assert delta["suggested_action"]


def test_build_load_session_runtime_delta_reports_aligned_state():
    delta = build_load_session_runtime_delta(
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
                            "recommended_action": "confirm_node_window",
                            "why": "Confirm the current node window conservatively.",
                        },
                        "validation_gate": {
                            "label": "Needs node confirmation",
                            "next_gate": "Run one same-setup confirmation string.",
                        },
                        "execution_plan": {
                            "summary": "Confirm the current node window conservatively: Repeat the same charge and seating with a short confirmation string before ranking it higher.",
                            "session_type": "node_confirmation",
                            "estimated_rounds": 6,
                            "keep_constant": [
                                "Keep charge, seating, and component lots fixed."
                            ],
                            "capture": ["One short confirmation string"],
                            "success_criteria": "The same charge and seating repeat with similar POI and stable chrono behavior.",
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
                            "uncertainty": "node",
                        },
                        "recommendation_stack": [{"priority": 1}],
                    },
                }
            },
            "recommendation": {
                "baseline": {
                    "available": True,
                    "charge_gr": 42.0,
                    "coal_mm": 71.0,
                    "cbto_mm": 68.92,
                    "charge_source": "recommended",
                    "seating_source": "learned",
                },
                "control_state": {
                    "charge_state": "recommended",
                    "seating_state": "learned",
                    "trust_label": "high",
                },
            },
            "session": {
                "recommended_charge_min_gr": 41.8,
                "recommended_charge_max_gr": 42.2,
                "recommended_coal_min": 70.8,
                "recommended_coal_max": 71.2,
                "safety_status": "ok",
                "confidence_label": "medium",
                "confidence_score": 3.2,
                "intake_snapshot_json": {
                    "charge_weight_gr": 42.0,
                    "coal_mm": 71.0,
                    "cbto_mm": 68.92,
                },
                "evidence_summary_json": {
                    "latest_result": {
                        "load_density_percent": 96.0,
                    }
                },
            },
        }
    )

    assert delta["level"] == "warning"
    assert any("frozen recommendation baseline" in item for item in delta["items"])
    assert any("learned seating baseline" in item for item in delta["items"])
    assert delta["smart_engine"]["candidate_robustness"] == "moderate"
    assert delta["smart_engine"]["next_action"] == "confirm_node_window"
    assert delta["smart_engine"]["validation_label"] == "Needs node confirmation"
    assert delta["smart_engine"]["plan_session_type"] == "node_confirmation"
    assert delta["smart_engine"]["plan_estimated_rounds"] == 6
    assert delta["smart_engine"]["plan_keep_constant"] == [
        "Keep charge, seating, and component lots fixed."
    ]
    assert delta["smart_engine"]["do_not_change_yet"] == [
        "Do not call the node proven until one same-setup repeat confirms it."
    ]
    assert delta["smart_engine"]["confidence_level"] == "moderate"
    assert delta["smart_engine"]["confidence_uncertainty"] == "node"
    assert delta["smart_engine"]["bullet_fit_level"] == "warning"
    assert delta["smart_engine"]["jump_band"] == "tight"
    assert any("Smart engine sees" in item for item in delta["items"])
    assert any("Smart engine bullet fit: warning" in item for item in delta["items"])
    assert any("Smart engine jump: tight" in item for item in delta["items"])
    assert any(
        "Smart engine gate: Needs node confirmation" in item for item in delta["items"]
    )
    assert any("Smart engine protocol:" in item for item in delta["items"])
    assert any("Smart engine hold:" in item for item in delta["items"])
    assert any("Smart engine blocker:" in item for item in delta["items"])
    assert any("Smart engine confidence:" in item for item in delta["items"])
    assert delta["focus_areas"] == ["node fit"]
    assert (
        delta["suggested_action"] == "Confirm the current node window conservatively."
    )


def test_build_load_session_runtime_delta_can_fall_back_to_smart_engine_guidance():
    delta = build_load_session_runtime_delta(
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
                    "decisions": {
                        "next_test": {
                            "recommended_action": "collect_matched_group_and_chrono",
                            "why": "Thin evidence should be strengthened before stronger tuning.",
                        },
                        "guidance": {
                            "title": "Collect matched evidence before stronger claims",
                            "setup_line": "Capture one matched chrono string and one measured group under the same setup and conditions.",
                        },
                        "recommendation_stack": [{"priority": 1}],
                    },
                }
            },
            "evidence": {
                "summary": {
                    "has_measured_velocity": False,
                    "has_measured_group": False,
                }
            },
            "session": {
                "safety_status": "ok",
                "confidence_label": "medium",
                "confidence_score": 3.1,
                "intake_snapshot_json": {},
                "evidence_summary_json": {"latest_result": {}},
            },
        }
    )

    assert delta["level"] == "warning"
    assert (
        delta["smart_engine"]["guidance_title"]
        == "Collect matched evidence before stronger claims"
    )
    assert (
        delta["suggested_action"]
        == "Capture one matched chrono string and one measured group under the same setup and conditions."
    )


def test_build_load_session_runtime_delta_uses_engine_evidence_diagnostics_when_present():
    delta = build_load_session_runtime_delta(
        {
            "smart_engine": {
                "engine_result": {
                    "evidence_diagnostics": {
                        "status": "needs_measurement",
                        "items": [
                            "Session still lacks measured chronograph data for the active setup.",
                            "Session still lacks measured grouping data for the active setup.",
                            "Confidence is still low, so current guidance depends on thin or partially assumed data.",
                        ],
                        "impacts": [
                            "Velocity trends and pressure interpretation remain more model-driven than measured until chrono data is logged.",
                            "Grouping conclusions remain provisional until the barrel and seating behavior are confirmed on target.",
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
                    "decisions": {
                        "next_test": {
                            "recommended_action": "collect_matched_group_and_chrono",
                            "why": "Thin evidence should be strengthened before stronger tuning.",
                        },
                        "guidance": {
                            "title": "Collect matched evidence before stronger claims",
                            "setup_line": "Capture one matched chrono string and one measured group under the same setup and conditions.",
                        },
                        "recommendation_stack": [{"priority": 1}],
                    },
                }
            },
            "evidence": {
                "summary": {
                    "has_measured_velocity": False,
                    "has_measured_group": False,
                }
            },
            "session": {
                "safety_status": "ok",
                "confidence_label": "low",
                "confidence_score": 2.1,
                "intake_snapshot_json": {},
                "evidence_summary_json": {"latest_result": {}},
            },
        }
    )

    assert delta["smart_engine"]["evidence_status"] == "needs_measurement"
    assert (
        "Session still lacks measured chronograph data for the active setup."
        in delta["smart_engine"]["evidence_items"]
    )
    assert (
        "Session still lacks measured grouping data for the active setup."
        in delta["items"]
    )
    assert "data trust" in delta["focus_areas"]
    assert (
        delta["suggested_action"]
        == "Capture a chronograph string for the current setup before treating the node as verified."
    )


def test_build_load_session_runtime_delta_reports_smart_engine_baseline_recovery():
    delta = build_load_session_runtime_delta(
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
                            "estimated_rounds": 5,
                            "keep_constant": [
                                "Do not change seating while re-establishing the charge baseline."
                            ],
                            "capture": [
                                "One short confirmation string at the frozen charge baseline"
                            ],
                        },
                        "do_not_change_yet": [
                            "Do not keep tuning away from the frozen charge baseline until the new charge path is explicitly confirmed."
                        ],
                        "blocked_by": [
                            {
                                "kind": "charge_baseline",
                                "title": "Charge baseline block",
                            }
                        ],
                        "recommendation_confidence": {
                            "level": "moderate",
                            "score": 58.0,
                            "summary": "The engine sees a usable direction, but the candidate still needs confirmation.",
                            "uncertainty": "baseline",
                        },
                    },
                }
            },
            "session": {
                "safety_status": "ok",
                "confidence_label": "medium",
                "intake_snapshot_json": {},
                "evidence_summary_json": {"latest_result": {}},
            },
            "evidence": {"summary": {}},
        }
    )

    assert delta["smart_engine"]["next_action"] == "return_to_charge_baseline"
    assert delta["smart_engine"]["branch_label"] == "Custom branch"
    assert delta["smart_engine"]["branch_compare_mode"] == "return_before_compare"
    assert (
        delta["smart_engine"]["branch_display_line"]
        == "Custom branch (return_before_compare)"
    )
    assert delta["smart_engine"]["charge_alignment"] == "outside"
    assert delta["smart_engine"]["charge_target"] == "42.00 gr"
    assert (
        delta["smart_engine"]["active_return_line"]
        == "Return charge toward 42.00 gr before treating this as the same candidate."
    )
    assert (
        delta["smart_engine"]["preferred_action"]
        == "Return charge toward 42.00 gr before treating this as the same candidate."
    )
    assert (
        delta["suggested_action"]
        == "Return charge toward 42.00 gr before treating this as the same candidate."
    )
    assert any(
        "Smart engine branch: Custom branch (return_before_compare)" in item
        for item in delta["items"]
    )
    assert any(
        "Smart engine baseline control: Return charge toward 42.00 gr before treating this as the same candidate."
        in item
        for item in delta["items"]
    )


def test_build_load_session_runtime_delta_reports_frozen_baseline_deviation():
    delta = build_load_session_runtime_delta(
        {
            "recommendation": {
                "baseline": {
                    "available": True,
                    "charge_gr": 42.0,
                    "charge_source": "learned",
                    "cbto_mm": 68.92,
                    "seating_source": "learned",
                },
                "control_state": {
                    "charge_state": "custom",
                    "seating_state": "custom",
                    "trust_label": "high",
                },
            },
            "evidence": {
                "summary": {
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                }
            },
            "session": {
                "safety_status": "ok",
                "confidence_label": "medium",
                "confidence_score": 3.5,
                "intake_snapshot_json": {
                    "charge_weight_gr": 42.4,
                    "coal_mm": 71.4,
                    "cbto_mm": 68.80,
                },
                "evidence_summary_json": {
                    "latest_result": {
                        "load_density_percent": 96.0,
                    }
                },
            },
        }
    )

    assert delta["level"] == "warning"
    assert any("learned recommendation baseline" in item for item in delta["items"])
    assert any(
        "CBTO" in item and "learned recommendation baseline" in item
        for item in delta["items"]
    )
    assert any(
        "outside a learned session baseline" in item for item in delta["impacts"]
    )
    assert "jump" in delta["focus_areas"]
    assert isinstance(delta["suggested_action"], str)


def test_build_load_session_runtime_delta_reports_spread_shooter_or_setup_signal():
    delta = build_load_session_runtime_delta(
        {
            "evidence": {
                "summary": {
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                    "signal_hint": "possible_shooter_or_setup_signal",
                    "batch_spread_reason": "Chrono is stable while groups are open.",
                }
            },
            "session": {
                "safety_status": "ok",
                "confidence_label": "medium",
                "confidence_score": 3.2,
                "intake_snapshot_json": {},
                "evidence_summary_json": {},
            },
        }
    )

    assert delta["level"] == "warning"
    assert any("possible shooter" in item for item in delta["items"])
    assert "controlled group" in delta["focus_areas"]
    assert "shooter/setup separation" in delta["focus_areas"]
    assert "Repeat one controlled group" in delta["suggested_action"]


def test_build_load_session_runtime_delta_reports_ammo_process_spread_signal():
    delta = build_load_session_runtime_delta(
        {
            "evidence": {
                "summary": {
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                    "signal_hint": "ammo_or_process_signal",
                    "batch_spread_reason": "Large groups appear together with high ES/SD.",
                }
            },
            "session": {
                "safety_status": "ok",
                "confidence_label": "medium",
                "confidence_score": 3.2,
                "intake_snapshot_json": {},
                "evidence_summary_json": {},
            },
        }
    )

    assert delta["level"] == "warning"
    assert any("ammunition" in item for item in delta["items"])
    assert "ammo process" in delta["focus_areas"]
    assert "velocity consistency" in delta["focus_areas"]
    assert "control series" in delta["suggested_action"]


def test_build_load_session_runtime_delta_reports_environment_spread_signal():
    delta = build_load_session_runtime_delta(
        {
            "evidence": {
                "summary": {
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                    "signal_hint": "environment_or_condition_signal",
                    "batch_spread_reason": "Recorded wind reached about 6.2 m/s.",
                }
            },
            "session": {
                "safety_status": "ok",
                "confidence_label": "medium",
                "confidence_score": 3.2,
                "intake_snapshot_json": {},
                "evidence_summary_json": {},
            },
        }
    )

    assert delta["level"] == "warning"
    assert any("wind" in item.lower() for item in delta["items"])
    assert "environment control" in delta["focus_areas"]
    assert "repeatability" in delta["focus_areas"]
    assert "well-documented conditions" in delta["suggested_action"]


def test_build_load_session_runtime_delta_reports_node_or_barrel_timing_signal():
    delta = build_load_session_runtime_delta(
        {
            "evidence": {
                "summary": {
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                    "signal_hint": "node_or_barrel_timing_signal",
                    "batch_spread_reason": "Stable ES/SD with vertical-dominant spread.",
                    "batch_spread_control_plan": {
                        "primary_action": "Repeat vertical control before changing powder.",
                    },
                    "batch_spread_decision": {
                        "state": "focused_tuning_after_repeat",
                        "label": "Repeat, then tune seating/timing",
                        "rationale": "Stable ES/SD with vertical pattern should be repeated first.",
                    },
                    "batch_spread_profile_guidance": {
                        "title": "Competition repeatability focus",
                        "emphasis": "Demand repeatability before competition ranking.",
                    },
                    "batch_spread_evidence_quality": {
                        "level": "thin",
                        "score": 42.0,
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
                        "ready_now": False,
                        "usage_goal": "competition",
                    },
                    "batch_comparison_basis": {
                        "ranking_state": "trailing_candidate",
                        "current_rank": 2,
                        "count": 3,
                        "leader_batch_name": "Match Node A",
                        "leader_gap_score": 6.5,
                        "summary": "Current batch currently ranks 2 of 3 comparable batches and trails Match Node A by about 6.5 score points.",
                    },
                    "batch_comparison_advisory": {
                        "title": "Trailing stronger evidence",
                        "message": "Current batch currently ranks 2 of 3 comparable batches and trails Match Node A by about 6.5 score points.",
                        "recommended_action": "Repeat one same-setup control group before promoting this batch over Match Node A.",
                        "promotion_ready": False,
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
                        "status_headline": "Still chasing the leader",
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
                        "hold_back": "hold: Current batch",
                        "counts": {"shoot_now": 1, "confirm": 1, "hold": 1},
                        "lane_summaries": [
                            {
                                "bucket": "shoot_now",
                                "summary": "shoot_now: Match Node A",
                            },
                            {"bucket": "confirm", "summary": "confirm: Current batch"},
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
            "session": {
                "safety_status": "ok",
                "confidence_label": "medium",
                "confidence_score": 3.2,
                "intake_snapshot_json": {},
                "evidence_summary_json": {},
            },
        }
    )

    assert delta["level"] == "warning"
    assert any("vertical pattern" in item.lower() for item in delta["items"])
    assert "vertical pattern" in delta["focus_areas"]
    assert "seating depth" in delta["focus_areas"]
    assert "barrel timing" in delta["focus_areas"]
    assert "decision gate" in delta["focus_areas"]
    assert "evidence quality" in delta["focus_areas"]
    assert any("Decision gate" in item for item in delta["items"])
    assert any("Spread evidence quality is thin" in item for item in delta["items"])
    assert any("Competition repeatability focus" in item for item in delta["items"])
    assert any(
        "Learning note: Stable velocity with vertical spread can be timing or tracking"
        in item
        for item in delta["items"]
    )
    assert any(
        "Capture checklist: Next capture checklist. Start with Same-setup repeat string, Small seating-depth bracket."
        in item
        for item in delta["items"]
    )
    assert any(
        "Validation status: Repeat before ranking or tuning harder (66.0/100)." in item
        for item in delta["items"]
    )
    assert any(
        "Batch comparison: trailing_candidate. Rank 2/3." in item
        for item in delta["items"]
    )
    assert any(
        "Comparison advisory: Trailing stronger evidence." in item
        for item in delta["items"]
    )
    assert any(
        "Comparison protocol: Head-to-head catch-up test." in item
        for item in delta["items"]
    )
    assert any(
        "Comparison explanation: validation_depth." in item for item in delta["items"]
    )
    assert any(
        "Comparison verdict: Do not promote yet." in item for item in delta["items"]
    )
    assert any(
        "Comparison acceptance: Not accepted yet." in item for item in delta["items"]
    )
    assert any(
        "Comparison acceptance gap: The batch still trails Match Node A under the weighted comparison."
        in item
        for item in delta["items"]
    )
    assert any(
        "Acceptance progress: partial (44.5/100), conditions 3/5." in item
        for item in delta["items"]
    )
    assert any(
        "Comparison next test: Catch-up test vs Match Node A." in item
        for item in delta["items"]
    )
    assert any(
        "Comparison board: Still chasing the leader." in item for item in delta["items"]
    )
    assert any(
        "Comparison profile: Competition comparison priority." in item
        for item in delta["items"]
    )
    assert any(
        "Mission brief: Still chasing the leader: Treat the next outing as a matched ranking test"
        in item
        for item in delta["items"]
    )
    assert any(
        "Comparison portfolio: Comparison portfolio." in item for item in delta["items"]
    )
    assert any(
        "Session strategy: Comparison session strategy." in item
        for item in delta["items"]
    )
    assert any(
        "Campaign view: Comparison campaign view." in item for item in delta["items"]
    )
    assert any(
        "Action plan: Comparison action plan." in item for item in delta["items"]
    )
    assert any(
        "Campaign board: Comparison campaign board." in item for item in delta["items"]
    )
    assert any(
        "Preview: shoot_now: Match Node A | confirm: Current batch" in item
        for item in delta["items"]
    )
    assert any(
        "Session queue: Comparison session queue." in item for item in delta["items"]
    )
    assert any(
        "Queue: 1. Match Node A (shoot_now) | 2. Current batch (confirm)" in item
        for item in delta["items"]
    )
    assert any(
        "Session manifest: Comparison session manifest." in item
        for item in delta["items"]
    )
    assert any(
        "Queue: 1. Match Node A (shoot_now) | 2. Current batch (confirm)" in item
        for item in delta["items"]
    )
    assert any(
        "Lanes: shoot_now: Match Node A | confirm: Current batch" in item
        for item in delta["items"]
    )
    assert any(
        "Next session brief: Comparison next session brief." in item
        for item in delta["items"]
    )
    assert any("Today plan: Comparison today plan." in item for item in delta["items"])
    assert any("Workboard: Comparison workboard." in item for item in delta["items"])
    assert any("Primary lane: shoot_now" in item for item in delta["items"])
    assert any("Run first: Match Node A" in item for item in delta["items"])
    assert any(
        "Counts: shoot_now 1 | confirm 1 | hold 1" in item for item in delta["items"]
    )
    assert any(
        "Lanes: shoot_now: Match Node A | confirm: Current batch | hold: Current batch"
        in item
        for item in delta["items"]
    )
    assert any("Status: Ready to run" in item for item in delta["items"])
    assert any(
        "Comparison checklist: Comparison checklist." in item for item in delta["items"]
    )
    assert any(
        "Comparison scorecard: evidence_quality." in item for item in delta["items"]
    )
    assert any(
        "Comparison confidence: thin (48.0/100)." in item for item in delta["items"]
    )
    assert any(
        "Comparison learning: Evidence quality is currently the biggest separator"
        in item
        for item in delta["items"]
    )
    assert "validation gate" in delta["focus_areas"]
    assert "competition ranking" in delta["focus_areas"]
    assert "batch comparison" in delta["focus_areas"]
    assert "promotion gate" in delta["focus_areas"]
    assert "acceptance gate" in delta["focus_areas"]
    assert "acceptance progress" in delta["focus_areas"]
    assert "next comparison test" in delta["focus_areas"]
    assert "comparison board" in delta["focus_areas"]
    assert "comparison profile" in delta["focus_areas"]
    assert "mission brief" in delta["focus_areas"]
    assert "comparison portfolio" in delta["focus_areas"]
    assert "session strategy" in delta["focus_areas"]
    assert "campaign view" in delta["focus_areas"]
    assert "action plan" in delta["focus_areas"]
    assert "session manifest" in delta["focus_areas"]
    assert "comparison leader" in delta["focus_areas"]
    assert "head-to-head test" in delta["focus_areas"]
    assert "comparison bottleneck" in delta["focus_areas"]
    assert "today plan" in delta["focus_areas"]
    assert "workboard" in delta["focus_areas"]
    assert (
        delta["suggested_action"]
        == "Run a same-day head-to-head against Match Node A before promoting this batch."
    )


def test_enrich_workflow_context_from_session_prefers_canonical_runtime_fields(
    monkeypatch,
):
    class _FakeDb(Database):
        pass

    monkeypatch.setattr(
        "src.tools.load_session_runtime_service.build_load_session_runtime",
        lambda db, session_id: {
            "session": {
                "ammo_profile_id": 55,
            },
            "context": {
                "load_session_id": session_id,
                "rifle_id": 7,
                "rifle_name": "Canonical Rifle",
                "barrel_id": "pipe-1",
                "barrel_name": "24in Match",
                "barrel_configuration_id": "cfg-supp",
                "barrel_configuration_name": "Suppressed",
                "usage_profile_name": "Competition",
                "confidence_label": "high",
                "safety_status": "ok",
            },
            "identity": {
                "rifle": {"label": "Canonical Rifle"},
                "barrel": {"label": "24in Match", "configuration_label": "Suppressed"},
                "usage": {"label": "Competition"},
            },
        },
    )

    enriched = enrich_workflow_context_from_session(
        _FakeDb(),
        {
            "workflow_id": 12,
            "load_session_id": "33",
            "rifle_id": "legacy-rifle",
            "barrel_name": "Old Barrel",
        },
    )

    assert enriched["load_session_id"] == 33
    assert enriched["ammo_profile_id"] == 55
    assert enriched["rifle_id"] == 7
    assert enriched["rifle_name"] == "Canonical Rifle"
    assert enriched["barrel_id"] == "pipe-1"
    assert enriched["barrel_name"] == "24in Match"
    assert enriched["barrel_configuration_id"] == "cfg-supp"
    assert enriched["barrel_configuration_name"] == "Suppressed"
    assert enriched["usage_profile_name"] == "Competition"
    assert enriched["confidence_label"] == "high"
    assert enriched["safety_status"] == "ok"


def test_build_active_workflow_context_from_settings_returns_empty_without_active_ids():
    from PyQt6.QtCore import QSettings

    class _FakeSettings(QSettings):
        def value(self, key, defaultValue=None, type=None):
            return defaultValue

    assert build_active_workflow_context_from_settings(_FakeSettings(), None) == {}


def test_build_active_workflow_context_from_settings_coerces_requested_int_fields(
    monkeypatch,
):
    from PyQt6.QtCore import QSettings

    class _FakeSettings(QSettings):
        def value(self, key, defaultValue=None, type=None):
            mapping = {
                "workflow_context/workflow_id": "12",
                "workflow_context/load_session_id": "33",
                "workflow_context/workflow_name": "OCW Test",
                "workflow_context/ammo_profile_id": "8",
                "workflow_context/rifle_id": "7",
                "workflow_context/barrel_id": "B1",
                "workflow_context/barrel_name": "24in Match",
                "workflow_context/barrel_configuration_id": "cfg-supp",
                "workflow_context/barrel_configuration_name": "Suppressed",
                "workflow_context/created_date": "2026-03-20",
            }
            # Defensive: ensure key is str for mapping.get
            if not isinstance(key, str):
                try:
                    key = str(key)
                except Exception:
                    return defaultValue
            return mapping.get(key, defaultValue)

    monkeypatch.setattr(
        "src.tools.load_session_runtime_service.enrich_workflow_context_from_session",
        lambda db, context: {**context, "usage_profile_name": "Competition"},
    )

    # Use a Database instance for type correctness
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_session_runtime_service_typecheck.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    database = Database(str(db_path))

    context = build_active_workflow_context_from_settings(
        _FakeSettings(),
        database,
        int_fields=("ammo_profile_id", "rifle_id"),
    )

    assert context["workflow_id"] == 12
    assert context["load_session_id"] == 33
    assert context["ammo_profile_id"] == 8
    assert context["rifle_id"] == 7
    assert context["barrel_configuration_name"] == "Suppressed"
    assert context["usage_profile_name"] == "Competition"


def test_refresh_load_session_measurement_summary_writes_runtime_measurement_rollup(
    monkeypatch,
):
    class _FakeDb(Database):
        pass

    monkeypatch.setattr(
        "src.tools.load_session_runtime_service.build_load_session_runtime",
        lambda db, session_id: {
            "evidence": {
                "summary": {
                    "chronograph_import_count": 2,
                    "test_result_count": 3,
                    "batch_count": 1,
                    "pressure_sign_count": 0,
                    "primer_review_status": "captured",
                    "primer_review_session_count": 1,
                    "primer_review_enabled_session_count": 1,
                    "primer_review_disabled_session_count": 0,
                    "primer_review_image_count": 2,
                    "pressure_sign_primer_review_count": 1,
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                    "latest_avg_velocity_fps": 2812.4,
                    "best_group_mm": 12.4,
                }
            }
        },
    )
    captured = {}

    def _record_update(database, session_id, **kwargs):
        captured["session_id"] = session_id
        captured.update(kwargs)
        return {"id": session_id}

    monkeypatch.setattr(
        "src.tools.load_session_runtime_service.update_load_development_session",
        _record_update,
    )

    updated = refresh_load_session_measurement_summary(
        _FakeDb(),
        33,
        source="test.sync",
    )

    assert updated == {"id": 33}
    assert captured["session_id"] == 33
    assert captured["evidence_summary_updates"]["chronograph_import_count"] == 2
    assert captured["evidence_summary_updates"]["best_group_mm"] == 12.4
    assert (
        captured["evidence_summary_updates"]["measurement_sync_source"] == "test.sync"
    )
    assert captured["evidence_summary_updates"]["data_strength"] == "medium"
    assert captured["evidence_summary_updates"]["drift_state"] == "stable"
    assert captured["evidence_summary_updates"]["signal_hint"] == "mixed_but_stable"
    assert (
        captured["learning_state_updates"]["summary"]["has_measured_velocity"] is True
    )
    assert captured["learning_state_updates"]["summary"]["test_result_count"] == 3
    assert captured["learning_state_updates"]["summary"]["data_strength"] == "medium"
    assert captured["learning_state_updates"]["summary"]["drift_state"] == "stable"
    assert (
        captured["learning_state_updates"]["summary"]["signal_hint"]
        == "mixed_but_stable"
    )
    assert (
        captured["learning_state_updates"]["summary"]["measurement_sync_source"]
        == "test.sync"
    )


def test_refresh_load_session_measurement_summary_marks_ammo_watch_when_pressure_and_lot_drift_exist(
    monkeypatch,
):
    class _FakeDb(Database):
        pass

    monkeypatch.setattr(
        "src.tools.load_session_runtime_service.build_load_session_runtime",
        lambda db, session_id: {
            "evidence": {
                "summary": {
                    "chronograph_import_count": 3,
                    "test_result_count": 1,
                    "batch_count": 1,
                    "range_session_count": 2,
                    "pressure_sign_count": 1,
                    "primer_review_status": "captured",
                    "has_measured_velocity": True,
                    "has_measured_group": False,
                    "latest_avg_velocity_fps": 2790.0,
                    "best_group_mm": None,
                }
            },
            "learning": {
                "aggregate": {
                    "weakest_link": "kruttlot",
                },
                "barrel": {},
                "case": {},
                "lots": {
                    "powder": {"drift_flag": "pressure_watch"},
                },
            },
        },
    )
    captured = {}

    def _record_update(database, session_id, **kwargs):
        captured["session_id"] = session_id
        captured.update(kwargs)
        return {"id": session_id}

    monkeypatch.setattr(
        "src.tools.load_session_runtime_service.update_load_development_session",
        _record_update,
    )

    refresh_load_session_measurement_summary(_FakeDb(), 44, source="test.pressure")

    assert captured["evidence_summary_updates"]["data_strength"] == "medium"
    assert captured["evidence_summary_updates"]["drift_state"] == "watch"
    assert captured["evidence_summary_updates"]["signal_hint"] == "pressure_or_ammo"
    assert captured["evidence_summary_updates"]["drift_flags"] == ["pressure_watch"]
    assert captured["learning_state_updates"]["summary"]["weakest_link"] == "kruttlot"


def test_refresh_load_session_measurement_summary_prefers_batch_spread_signal_when_safe(
    monkeypatch,
):
    class _FakeDb(Database):
        pass

    monkeypatch.setattr(
        "src.tools.load_session_runtime_service.build_load_session_runtime",
        lambda db, session_id: {
            "evidence": {
                "summary": {
                    "chronograph_import_count": 1,
                    "test_result_count": 0,
                    "batch_count": 1,
                    "range_session_count": 1,
                    "pressure_sign_count": 0,
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                    "batch_spread_signal_hint": "possible_shooter_or_setup_signal",
                    "batch_spread_confidence": "medium",
                    "batch_spread_reason": "Chrono is stable while groups are open.",
                    "batch_spread_watchouts": ["Repeat controlled group."],
                    "batch_spread_note_flags": ["shooter_series"],
                    "batch_spread_max_wind_mps": 3.4,
                    "batch_spread_pattern_flags": ["horizontal_dominant"],
                    "batch_spread_axis_ratio": 2.1,
                    "batch_spread_poi_shift_mm": 24.0,
                    "batch_spread_control_plan": {
                        "title": "Controlled repeatability group",
                        "primary_action": "Repeat one controlled group before rejecting it.",
                    },
                    "batch_spread_decision": {
                        "state": "repeat_before_rejecting",
                        "label": "Repeat before rejecting",
                    },
                    "batch_spread_profile_guidance": {
                        "title": "Hunting validation focus",
                        "emphasis": "Confirm cold-bore point of impact before field approval.",
                    },
                    "batch_spread_evidence_quality": {
                        "level": "moderate",
                        "score": 56.0,
                    },
                    "batch_spread_learning_explanation": {
                        "title": "A bad group is not always a bad load",
                        "user_takeaway": "For hunting, prove safe cold-bore field behavior before trusting the load.",
                    },
                    "batch_spread_capture_checklist": {
                        "title": "Next capture checklist",
                        "items": [
                            {"label": "Cold-bore validation"},
                        ],
                    },
                    "batch_spread_validation_status": {
                        "status": "field_validation_pending",
                        "label": "Not field-ready yet",
                        "summary": "The load still needs a controlled repeat and a conservative field-style confirmation before it should be trusted for hunting.",
                        "next_gate": "Resolve the current spread signal, then confirm one cold-bore shot plus a short realistic-support control series.",
                        "readiness_score": 54.0,
                        "ready_now": False,
                        "usage_goal": "hunting",
                    },
                    "batch_comparison_basis": {
                        "ranking_state": "leading_but_provisional",
                        "current_rank": 1,
                        "count": 2,
                        "leader_batch_name": "Current batch",
                        "leader_gap_score": 0.0,
                        "summary": "Current batch currently leads 2 comparable batches, but the result is still provisional because validation is not complete.",
                    },
                    "batch_comparison_advisory": {
                        "title": "Leading but still provisional",
                        "message": "Current batch currently leads 2 comparable batches, but the result is still provisional because validation is not complete.",
                        "recommended_action": "Not field-ready yet",
                        "promotion_ready": False,
                    },
                    "batch_comparison_protocol": {
                        "title": "Provisional leader confirmation",
                        "primary_action": "Repeat the current leader under the same setup before promoting it over the rest of the batch set.",
                        "shot_plan": "Shoot one matched repeat string with chrono plus measured group, then compare it with the nearest competing batch if the result stays stable.",
                    },
                    "batch_comparison_explanation": {
                        "limiting_factor": "field_validation",
                        "reason": "The batch currently leads on score, but the lead is still fragile because validation is not finished.",
                        "next_measurement": "Capture one cold-bore and one realistic-support confirmation string.",
                    },
                    "batch_comparison_verdict": {
                        "label": "Hold, do not promote yet",
                        "summary": "This batch leads for now, but the lead is still too provisional to lock in.",
                    },
                    "batch_comparison_acceptance": {
                        "label": "Almost accepted, but still provisional",
                        "summary": "This batch is close to replacing the current field candidate, but the final acceptance bar is not met yet.",
                        "next_gate": "Not field-ready yet",
                        "remaining_gaps": [
                            "Cold-bore or realistic field validation is still missing.",
                        ],
                    },
                    "batch_comparison_acceptance_progress": {
                        "level": "advancing",
                        "score": 63.3,
                        "passed_count": 4,
                        "total_count": 5,
                        "summary": "The batch is moving in the right direction, but acceptance still depends on closing the last provisional gap.",
                        "next_target": "Not field-ready yet",
                    },
                    "batch_comparison_next_test": {
                        "title": "Close the last acceptance gap",
                        "summary": "The batch is close, but one last matched confirmation should close the final gap before promotion.",
                        "primary_action": "Repeat the current leader under the same setup before promoting it over the rest of the batch set.",
                        "check_first": "Cold-bore confirmation",
                    },
                    "batch_comparison_status_board": {
                        "headline": "Close, but still provisional",
                        "readiness_band": "near_ready",
                        "summary": "Close, but still provisional | Rank 1/2 | Progress: advancing (63.3/100) | Verdict: Hold, do not promote yet",
                    },
                    "batch_comparison_profile_priority": {
                        "title": "Hunting comparison priority",
                        "emphasis": "Protect cold-bore trust, field realism, and humane predictability before chasing the leaderboard.",
                        "guardrail": "Do not promote a hunting batch until first-shot behavior and realistic support are verified.",
                    },
                    "batch_comparison_mission_brief": {
                        "title": "Comparison mission brief",
                        "mission": "Close, but still provisional: Treat the next outing as a field-trust check before promotion.",
                        "primary_action": "Repeat the current leader under the same setup before promoting it over the rest of the batch set.",
                        "success_marker": "One calm, field-style confirmation that keeps impact and behavior predictable.",
                    },
                    "batch_comparison_portfolio": {
                        "title": "Comparison portfolio",
                        "focus": "The current leader is promising, but the portfolio still needs one last acceptance check.",
                        "status_headline": "Close, but still provisional",
                    },
                    "batch_comparison_session_strategy": {
                        "title": "Comparison session strategy",
                        "mode": "field_validation_session",
                        "objective": "Confirm hunting trust before promotion.",
                    },
                    "batch_comparison_campaign_view": {
                        "title": "Comparison campaign view",
                        "summary": "band near_ready | mode field_validation_session | Confirm hunting trust before promotion.",
                    },
                    "batch_comparison_action_plan": {
                        "title": "Comparison action plan",
                        "summary": "Confirm hunting trust before promotion.",
                        "primary_action": "Repeat the current leader under the same setup before promoting it over the rest of the batch set.",
                    },
                    "batch_comparison_session_manifest": {
                        "title": "Comparison session manifest",
                        "summary": "band near_ready | mode field_validation_session | Confirm hunting trust before promotion. | Ready now: 0 | Confirm next: 1 | Watch/pause: 1",
                        "primary_bucket": "confirm",
                        "first_batch_name": "Current batch",
                        "queue_preview": [
                            "1. Current batch (confirm)",
                            "2. Safety Watch (pause)",
                        ],
                        "lane_summaries": [
                            {
                                "bucket": "confirm",
                                "count": 1,
                                "summary": "confirm: Current batch",
                            },
                            {
                                "bucket": "pause",
                                "count": 1,
                                "summary": "pause: Safety Watch",
                            },
                        ],
                    },
                    "batch_comparison_next_session_brief": {
                        "title": "Comparison next session brief",
                        "summary": "Start with Current batch | bucket confirm | check Cold-bore confirmation",
                        "first_batch_name": "Current batch",
                        "primary_bucket": "confirm",
                        "primary_action": "Repeat the current leader under the same setup before promoting it over the rest of the batch set.",
                        "hold_back": "pause: Safety Watch",
                    },
                    "batch_comparison_today_plan": {
                        "title": "Comparison today plan",
                        "summary": "Run Current batch first | verify Cold-bore confirmation | hold back pause: Safety Watch",
                        "first_batch_name": "Current batch",
                        "primary_bucket": "confirm",
                        "primary_action": "Repeat the current leader under the same setup before promoting it over the rest of the batch set.",
                    },
                    "batch_comparison_workboard": {
                        "title": "Comparison workboard",
                        "summary": "Run Current batch first | verify Cold-bore confirmation | hold back pause: Safety Watch",
                        "status_label": "Confirmation session",
                        "first_batch_name": "Current batch",
                        "primary_bucket": "confirm",
                        "primary_action": "Repeat the current leader under the same setup before promoting it over the rest of the batch set.",
                        "hold_back": "pause: Safety Watch",
                    },
                    "batch_comparison_checklist": {
                        "title": "Comparison checklist",
                        "highest_priority": "Cold-bore confirmation",
                    },
                    "batch_comparison_scorecard": {
                        "swing_factor": "field_validation",
                        "summary": "Current batch mainly trails the ideal promotion state on readiness for field validation.",
                    },
                    "batch_comparison_confidence": {
                        "level": "moderate",
                        "score": 61.0,
                        "summary": "The current batch comparison is useful, but it still benefits from one more matched confirmation.",
                    },
                    "batch_comparison_learning_note": {
                        "plain_summary": "Readiness or validation depth is currently the biggest separator between the compared batches.",
                        "takeaway": "For hunting, a batch must prove realistic first-shot and field behavior before promotion is honest.",
                    },
                }
            },
            "learning": {
                "aggregate": {
                    "weakest_link": "kruttlot",
                },
                "barrel": {},
                "case": {},
                "lots": {},
            },
        },
    )
    captured = {}

    def _record_update(database, session_id, **kwargs):
        captured["session_id"] = session_id
        captured.update(kwargs)
        return {"id": session_id}

    monkeypatch.setattr(
        "src.tools.load_session_runtime_service.update_load_development_session",
        _record_update,
    )

    refresh_load_session_measurement_summary(_FakeDb(), 45, source="test.batch")

    assert (
        captured["evidence_summary_updates"]["signal_hint"]
        == "possible_shooter_or_setup_signal"
    )
    assert captured["evidence_summary_updates"]["batch_spread_confidence"] == "medium"
    assert captured["evidence_summary_updates"]["batch_spread_note_flags"] == [
        "shooter_series"
    ]
    assert captured["evidence_summary_updates"]["batch_spread_max_wind_mps"] == 3.4
    assert captured["evidence_summary_updates"]["batch_spread_pattern_flags"] == [
        "horizontal_dominant"
    ]
    assert captured["evidence_summary_updates"]["batch_spread_axis_ratio"] == 2.1
    assert captured["evidence_summary_updates"]["batch_spread_poi_shift_mm"] == 24.0
    assert (
        captured["evidence_summary_updates"]["batch_spread_control_plan"]["title"]
        == "Controlled repeatability group"
    )
    assert (
        captured["evidence_summary_updates"]["batch_spread_decision"]["state"]
        == "repeat_before_rejecting"
    )
    assert (
        captured["evidence_summary_updates"]["batch_spread_profile_guidance"]["title"]
        == "Hunting validation focus"
    )
    assert (
        captured["evidence_summary_updates"]["batch_spread_evidence_quality"]["level"]
        == "moderate"
    )
    assert (
        captured["evidence_summary_updates"]["batch_spread_learning_explanation"][
            "title"
        ]
        == "A bad group is not always a bad load"
    )
    assert (
        captured["evidence_summary_updates"]["batch_spread_capture_checklist"]["title"]
        == "Next capture checklist"
    )
    assert (
        captured["evidence_summary_updates"]["batch_spread_validation_status"]["status"]
        == "field_validation_pending"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_basis"]["ranking_state"]
        == "leading_but_provisional"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_advisory"]["title"]
        == "Leading but still provisional"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_protocol"]["title"]
        == "Provisional leader confirmation"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_explanation"][
            "limiting_factor"
        ]
        == "field_validation"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_verdict"]["label"]
        == "Hold, do not promote yet"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_acceptance"]["label"]
        == "Almost accepted, but still provisional"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_acceptance_progress"][
            "level"
        ]
        == "advancing"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_next_test"]["title"]
        == "Close the last acceptance gap"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_status_board"][
            "headline"
        ]
        == "Close, but still provisional"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_profile_priority"][
            "title"
        ]
        == "Hunting comparison priority"
    )
    assert captured["evidence_summary_updates"]["batch_comparison_mission_brief"][
        "mission"
    ].startswith("Close, but still provisional")
    assert (
        captured["evidence_summary_updates"]["batch_comparison_portfolio"][
            "status_headline"
        ]
        == "Close, but still provisional"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_session_strategy"][
            "mode"
        ]
        == "field_validation_session"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_campaign_view"]["title"]
        == "Comparison campaign view"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_action_plan"]["summary"]
        == "Confirm hunting trust before promotion."
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_session_manifest"][
            "primary_bucket"
        ]
        == "confirm"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_next_session_brief"][
            "hold_back"
        ]
        == "pause: Safety Watch"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_today_plan"][
            "first_batch_name"
        ]
        == "Current batch"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_workboard"][
            "primary_bucket"
        ]
        == "confirm"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_workboard"][
            "status_label"
        ]
        == "Confirmation session"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_checklist"][
            "highest_priority"
        ]
        == "Cold-bore confirmation"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_scorecard"][
            "swing_factor"
        ]
        == "field_validation"
    )
    assert (
        captured["evidence_summary_updates"]["batch_comparison_confidence"]["level"]
        == "moderate"
    )
    assert captured["evidence_summary_updates"]["batch_comparison_learning_note"][
        "takeaway"
    ].startswith("For hunting")
    assert (
        captured["learning_state_updates"]["summary"]["batch_spread_reason"]
        == "Chrono is stable while groups are open."
    )
    assert captured["learning_state_updates"]["summary"]["batch_spread_note_flags"] == [
        "shooter_series"
    ]
    assert captured["learning_state_updates"]["summary"][
        "batch_spread_pattern_flags"
    ] == ["horizontal_dominant"]
    assert (
        captured["learning_state_updates"]["summary"]["batch_spread_control_plan"][
            "primary_action"
        ]
        == "Repeat one controlled group before rejecting it."
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_spread_decision"]["label"]
        == "Repeat before rejecting"
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_spread_profile_guidance"][
            "emphasis"
        ]
        == "Confirm cold-bore point of impact before field approval."
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_spread_evidence_quality"][
            "score"
        ]
        == 56.0
    )
    assert (
        captured["learning_state_updates"]["summary"][
            "batch_spread_learning_explanation"
        ]["user_takeaway"]
        == "For hunting, prove safe cold-bore field behavior before trusting the load."
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_spread_capture_checklist"][
            "items"
        ][0]["label"]
        == "Cold-bore validation"
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_spread_validation_status"][
            "label"
        ]
        == "Not field-ready yet"
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_basis"][
            "current_rank"
        ]
        == 1
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_advisory"][
            "recommended_action"
        ]
        == "Not field-ready yet"
    )
    assert captured["learning_state_updates"]["summary"]["batch_comparison_protocol"][
        "primary_action"
    ].startswith("Repeat the current leader")
    assert captured["learning_state_updates"]["summary"][
        "batch_comparison_explanation"
    ]["next_measurement"].startswith("Capture one cold-bore")
    assert captured["learning_state_updates"]["summary"]["batch_comparison_verdict"][
        "summary"
    ].startswith("This batch leads for now")
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_acceptance"][
            "next_gate"
        ]
        == "Not field-ready yet"
    )
    assert (
        captured["learning_state_updates"]["summary"][
            "batch_comparison_acceptance_progress"
        ]["score"]
        == 63.3
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_next_test"][
            "check_first"
        ]
        == "Cold-bore confirmation"
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_status_board"][
            "readiness_band"
        ]
        == "near_ready"
    )
    assert captured["learning_state_updates"]["summary"][
        "batch_comparison_profile_priority"
    ]["guardrail"].startswith("Do not promote a hunting batch")
    assert captured["learning_state_updates"]["summary"][
        "batch_comparison_mission_brief"
    ]["success_marker"].startswith("One calm, field-style")
    assert captured["learning_state_updates"]["summary"]["batch_comparison_portfolio"][
        "focus"
    ].startswith("The current leader is promising")
    assert (
        captured["learning_state_updates"]["summary"][
            "batch_comparison_session_strategy"
        ]["objective"]
        == "Confirm hunting trust before promotion."
    )
    assert captured["learning_state_updates"]["summary"][
        "batch_comparison_campaign_view"
    ]["summary"].startswith("band near_ready")
    assert captured["learning_state_updates"]["summary"][
        "batch_comparison_action_plan"
    ]["primary_action"].startswith("Repeat the current leader")
    assert (
        captured["learning_state_updates"]["summary"][
            "batch_comparison_session_manifest"
        ]["first_batch_name"]
        == "Current batch"
    )
    assert (
        captured["learning_state_updates"]["summary"][
            "batch_comparison_next_session_brief"
        ]["primary_bucket"]
        == "confirm"
    )
    assert captured["learning_state_updates"]["summary"]["batch_comparison_today_plan"][
        "summary"
    ].startswith("Run Current batch first")
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_workboard"][
            "hold_back"
        ]
        == "pause: Safety Watch"
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_workboard"][
            "status_label"
        ]
        == "Confirmation session"
    )
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_checklist"][
            "title"
        ]
        == "Comparison checklist"
    )
    assert captured["learning_state_updates"]["summary"]["batch_comparison_scorecard"][
        "summary"
    ].startswith("Current batch mainly trails")
    assert (
        captured["learning_state_updates"]["summary"]["batch_comparison_confidence"][
            "score"
        ]
        == 61.0
    )
    assert captured["learning_state_updates"]["summary"][
        "batch_comparison_learning_note"
    ]["plain_summary"].startswith("Readiness or validation depth")
