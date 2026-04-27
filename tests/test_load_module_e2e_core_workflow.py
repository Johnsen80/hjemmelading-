"""End-to-end CI test: core commercial load module workflow.

Verifies that the following sequence works deterministically without UI:

  1. Create rifle + components
  2. Create load development session
  3. Save chrono import (simulates chronograph_importer.save_session)
  4. Save target group result (simulates target_analyzer.save_results)
  5. Create batch project + batch session
  6. Recompute batch analysis (Block 4: headless analysis)
  7. Refresh measurement summary / learning state (Block 4: deterministic loop)
  8. Re-open: rebuild runtime from DB (simulates app restart or tab switch)
  9. Verify context is intact — no rifle/barrel/component drift
 10. Verify evidence counts are correct
 11. Verify signal_hint is a canonical value
 12. Verify learning aggregate is populated
 13. Run smart ammo engine — verify recommendation is present
 14. Verify runtime delta level is not "unknown"

This test must pass in CI without any Qt display and without any external service.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from src.database.database import Database
from src.layers import component_layer
from src.modules.batch_workspace import recompute_batch_analysis_from_db
from src.modules.smart_ammo_engine import build_smart_ammo_engine
from src.tools.evidence_quality_service import SPREAD_SIGNAL_HINTS
from src.tools.load_development_session_service import create_load_development_session
from src.tools.load_session_runtime_service import (
    build_load_session_runtime,
    build_load_session_runtime_delta,
    refresh_load_session_measurement_summary,
)

add_batch_session = component_layer.batch.add_batch_session
create_batch_project = component_layer.batch.create_batch_project


_TMP = Path(
    "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp"
)


def _fresh_db() -> Database:
    _TMP.mkdir(parents=True, exist_ok=True)
    path = _TMP / f"e2e_core_workflow_{uuid4().hex}.db"
    return Database(str(path))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_components(db: Database) -> dict:
    """Insert minimal rifle + components and return their IDs."""
    rifle_id = db.insert(
        "rifles",
        {
            "name": "E2E Match Rifle",
            "caliber": "6.5 CM",
            "twist_rate": "1:8",
        },
    )
    bullet_id = db.insert(
        "bullets",
        {
            "name": "147gr ELD-M",
            "manufacturer": "Hornady",
            "caliber": "6.5 CM",
            "weight_grains": 147.0,
        },
    )
    powder_id = db.insert(
        "powder",
        {
            "name": "N555",
            "manufacturer": "Vihtavuori",
        },
    )
    primer_id = db.insert(
        "primers",
        {
            "name": "CCI BR-2",
            "manufacturer": "CCI",
        },
    )
    case_id = db.insert(
        "cases",
        {
            "name": "Lapua 6.5 CM",
            "manufacturer": "Lapua",
            "caliber": "6.5 CM",
        },
    )
    return {
        "rifle_id": rifle_id,
        "bullet_id": bullet_id,
        "powder_id": powder_id,
        "primer_id": primer_id,
        "case_id": case_id,
    }


# ---------------------------------------------------------------------------
# Main end-to-end test
# ---------------------------------------------------------------------------


def test_core_commercial_workflow_e2e():
    """Full workflow: create → measure → re-open → verify context + recommendation."""
    db = _fresh_db()
    try:
        # ------------------------------------------------------------------
        # Step 1: Seed rifle and components
        # ------------------------------------------------------------------
        ids = _seed_components(db)
        rifle_id = ids["rifle_id"]
        bullet_id = ids["bullet_id"]
        powder_id = ids["powder_id"]
        primer_id = ids["primer_id"]
        case_id = ids["case_id"]

        # ------------------------------------------------------------------
        # Step 2: Create load development session
        # ------------------------------------------------------------------
        session_id = create_load_development_session(
            db,
            rifle_id=rifle_id,
            rifle_name="E2E Match Rifle",
            rifle_caliber="6.5 CM",
            barrel_id="pipe-e2e",
            barrel_name="26in Match",
            barrel_configuration_id="pipe-e2e:bare",
            barrel_configuration_name="Bare muzzle",
            usage_profile_key="precision",
            usage_profile_name="Presisjon / match",
            component_selection={
                "bullet_id": bullet_id,
                "powder_id": powder_id,
                "primer_id": primer_id,
                "case_id": case_id,
            },
            recommendation={
                "charge_window_gr": {"min": 41.5, "max": 42.5},
                "baseline": {
                    "available": True,
                    "charge_gr": 42.0,
                    "coal_mm": 71.5,
                    "cbto_mm": 68.9,
                    "charge_source": "recommended",
                    "trust_label": "medium",
                },
            },
            recommended_charge_min_gr=41.5,
            recommended_charge_max_gr=42.5,
            confidence_label="medium",
            confidence_score=55.0,
            next_action="build_initial_test_batches",
        )
        assert session_id is not None and session_id > 0, "Session must be created"

        # ------------------------------------------------------------------
        # Step 3: Save chrono import (simulates chronograph_importer.save_session)
        # ------------------------------------------------------------------
        velocities = [2810.0, 2818.0, 2805.0, 2822.0, 2814.0]
        chrono_id = db.insert(
            "chronograph_imports",
            {
                "load_session_id": session_id,
                "file_path": "e2e_chrono.csv",
                "velocity_count": len(velocities),
                "velocity_avg": sum(velocities) / len(velocities),
                "velocity_es": max(velocities) - min(velocities),
                "velocity_sd": 6.2,
                "velocities_json": json.dumps(velocities),
                "import_date": "2026-04-14",
            },
        )
        assert chrono_id is not None

        # ------------------------------------------------------------------
        # Step 4: Save target group result (simulates target_analyzer.save_results)
        # test_results schema: charge_weight NOT NULL, group_size_mm, velocity_avg
        # ------------------------------------------------------------------
        target_id = db.insert(
            "test_results",
            {
                "load_session_id": session_id,
                "charge_weight": 42.0,
                "group_size_mm": 15.2,
                "group_size_moa": 0.52,
                "velocity_avg": 2814.0,
            },
        )
        assert target_id is not None

        # ------------------------------------------------------------------
        # Step 5: Create batch project + batch session
        # ------------------------------------------------------------------
        batch_result = create_batch_project(
            db,
            "E2E Batch 001",
            rifle_id,
            barrel_id="pipe-e2e",
            barrel_name="26in Match",
            barrel_configuration_id="pipe-e2e:bare",
            barrel_configuration_name="Bare muzzle",
            load_session_id=session_id,
            bullet_id=bullet_id,
            powder_id=powder_id,
            primer_id=primer_id,
            case_id=case_id,
        )
        assert batch_result.get("ok") and batch_result.get("batch_id")
        batch_id = int(batch_result["batch_id"])

        add_batch_session(
            db,
            batch_id,
            load_session_id=session_id,
            rifle_id=rifle_id,
            barrel_id="pipe-e2e",
            barrel_name="26in Match",
            barrel_configuration_id="pipe-e2e:bare",
            barrel_configuration_name="Bare muzzle",
            session_name="Validation 1",
            session_date="2026-04-14",
            distance_m=100,
            shot_count=5,
            group_size_mm=15.2,
            group_size_moa=0.52,
            chronograph_import_id=chrono_id,
        )

        # ------------------------------------------------------------------
        # Step 6: Recompute batch analysis headlessly (Block 4)
        # ------------------------------------------------------------------
        analysis = recompute_batch_analysis_from_db(db, batch_id)
        assert isinstance(
            analysis, dict
        ), "recompute_batch_analysis_from_db must return a dict"
        assert (
            "metrics" in analysis or "score" in analysis
        ), "Analysis must contain metrics or score key"

        # ------------------------------------------------------------------
        # Step 7: Refresh learning state (Block 4 — deterministic loop)
        # ------------------------------------------------------------------
        updated = refresh_load_session_measurement_summary(
            db, session_id, source="e2e_test"
        )
        assert isinstance(
            updated, dict
        ), "refresh_load_session_measurement_summary must return updated session"

        # ------------------------------------------------------------------
        # Step 8: Re-open — rebuild full runtime from DB
        # (simulates app restart, tab switch, or resume after close)
        # ------------------------------------------------------------------
        runtime = build_load_session_runtime(db, session_id)
        assert isinstance(runtime, dict), "Runtime must be a dict after re-open"

        # ------------------------------------------------------------------
        # Step 9: Context integrity — nothing must be lost
        # ------------------------------------------------------------------
        context = runtime.get("context") or {}
        assert (
            context.get("rifle_id") == rifle_id
        ), f"rifle_id drifted: expected {rifle_id}, got {context.get('rifle_id')}"
        assert (
            context.get("barrel_id") == "pipe-e2e"
        ), f"barrel_id drifted: got {context.get('barrel_id')}"
        assert (
            context.get("barrel_configuration_id") == "pipe-e2e:bare"
        ), f"barrel_configuration_id drifted: got {context.get('barrel_configuration_id')}"

        session_row = runtime.get("session") or {}
        component_selection = session_row.get("component_selection_json") or {}
        assert (
            component_selection.get("bullet_id") == bullet_id
        ), f"bullet_id drifted: expected {bullet_id}, got {component_selection.get('bullet_id')}"
        assert (
            component_selection.get("powder_id") == powder_id
        ), f"powder_id drifted: expected {powder_id}, got {component_selection.get('powder_id')}"

        # ------------------------------------------------------------------
        # Step 10: Evidence counts must reflect saved measurements
        # ------------------------------------------------------------------
        evidence = runtime.get("evidence") or {}
        summary = evidence.get("summary") or {}

        assert (
            summary.get("chronograph_import_count", 0) >= 1
        ), f"chronograph_import_count expected >= 1, got {summary.get('chronograph_import_count')}"
        assert (
            summary.get("has_measured_velocity") is True
        ), "has_measured_velocity must be True after chrono import"
        assert (
            summary.get("has_measured_group") is True
        ), "has_measured_group must be True after target result"
        assert (
            summary.get("batch_count", 0) >= 1
        ), f"batch_count expected >= 1, got {summary.get('batch_count')}"

        # ------------------------------------------------------------------
        # Step 11: signal_hint must be a canonical value.
        # signal_hint is computed by refresh_load_session_measurement_summary and
        # persisted to evidence_summary_json — read it from the session row.
        # ------------------------------------------------------------------
        persisted_evidence = session_row.get("evidence_summary_json") or {}
        signal_hint = str(persisted_evidence.get("signal_hint") or "").strip()
        assert signal_hint in SPREAD_SIGNAL_HINTS, (
            f"signal_hint '{signal_hint}' is not in SPREAD_SIGNAL_HINTS. "
            f"Was refresh_load_session_measurement_summary called? "
            f"persisted_evidence keys: {list(persisted_evidence.keys())}"
        )

        # ------------------------------------------------------------------
        # Step 12: Learning aggregate must be populated
        # ------------------------------------------------------------------
        learning = runtime.get("learning") or {}
        aggregate = learning.get("aggregate") or {}
        assert isinstance(
            aggregate.get("confidence_score"), (int, float)
        ), f"learning.aggregate.confidence_score must be numeric, got {aggregate.get('confidence_score')}"
        assert (
            aggregate.get("confidence_label") is not None
        ), "learning.aggregate.confidence_label must be set"

        # Step 12b: model_status must be persisted in learning_state_json
        session_row = runtime.get("session") or {}
        learning_state = session_row.get("learning_state_json") or {}
        model_status = learning_state.get("model_status")
        assert model_status in {
            "raw",
            "partially_calibrated",
            "well_calibrated",
        }, f"learning_state_json.model_status must be canonical, got '{model_status}'"
        # After paired chrono + target data, model_status must not be 'raw'
        assert (
            model_status != "raw"
        ), f"After chrono + target data, model_status must not be 'raw', got '{model_status}'"

        # Step 12c: learning_state_json must have canonical structure
        assert (
            "candidates" in learning_state
        ), "learning_state_json must have 'candidates' key"
        assert isinstance(
            learning_state["candidates"].get("confirmed"), list
        ), "candidates.confirmed must be a list"
        assert isinstance(
            learning_state["candidates"].get("rejected"), list
        ), "candidates.rejected must be a list"

        # ------------------------------------------------------------------
        # Step 13: Smart engine must produce a recommendation
        # ------------------------------------------------------------------
        engine_result = build_smart_ammo_engine(db, session_id)
        assert isinstance(
            engine_result, dict
        ), "build_smart_ammo_engine must return a dict"

        engine_output = engine_result.get("engine_result") or {}
        assert isinstance(
            engine_output, dict
        ), "engine_result.engine_result must be a dict"
        # Engine must at minimum have run without crashing and produced structured output.
        # Check for known engine-output keys (baseline_control, decisions, evidence).
        engine_keys = set(engine_output.keys())
        assert engine_keys & {
            "baseline_control",
            "decisions",
            "evidence",
            "safety",
        }, f"engine_result missing expected structural keys: {list(engine_keys)}"

        # ------------------------------------------------------------------
        # Step 14: Runtime delta must not be "unknown"
        # ------------------------------------------------------------------
        delta = build_load_session_runtime_delta(runtime)
        assert isinstance(delta, dict), "Runtime delta must be a dict"
        assert delta.get("level") != "unknown", (
            f"Runtime delta level is 'unknown' — runtime context is incomplete. "
            f"Delta: {delta}"
        )

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Context-drift regression: re-open after partial data must not lose context
# ---------------------------------------------------------------------------


def test_context_survives_reopen_with_no_measurements():
    """Session with zero measurements must still return correct context after re-open."""
    db = _fresh_db()
    try:
        ids = _seed_components(db)
        rifle_id = ids["rifle_id"]

        session_id = create_load_development_session(
            db,
            rifle_id=rifle_id,
            rifle_name="Sparse Rifle",
            rifle_caliber=".308 Win",
            barrel_id="pipe-sparse",
            barrel_name="20in Hunting",
            barrel_configuration_id="pipe-sparse:bare",
            barrel_configuration_name="Bare",
            usage_profile_key="hunting",
            usage_profile_name="Jakt",
            component_selection={
                "bullet_id": ids["bullet_id"],
                "powder_id": ids["powder_id"],
            },
        )

        # No measurements — just re-open
        runtime = build_load_session_runtime(db, session_id)
        assert isinstance(runtime, dict)

        context = runtime.get("context") or {}
        assert (
            context.get("rifle_id") == rifle_id
        ), "rifle_id must survive re-open with zero measurements"
        assert (
            context.get("barrel_id") == "pipe-sparse"
        ), "barrel_id must survive re-open with zero measurements"

        evidence = runtime.get("evidence") or {}
        summary = evidence.get("summary") or {}
        assert summary.get("chronograph_import_count", 0) == 0
        assert summary.get("has_measured_velocity") is not True
        assert summary.get("has_measured_group") is not True

        # signal_hint is only populated after refresh — with no measurements, the
        # persisted evidence_summary_json is empty, which is correct behaviour.
        # The live summary must NOT have a non-canonical value.
        live_hint = summary.get("signal_hint") or ""
        assert (
            live_hint == "" or live_hint in SPREAD_SIGNAL_HINTS
        ), f"live signal_hint '{live_hint}' must be empty or canonical with no data"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Learning loop: signal_hint updates after measurement save
# ---------------------------------------------------------------------------


def test_signal_hint_updates_after_chrono_save():
    """After saving chrono data and refreshing, signal_hint must move from
    'insufficient_evidence' to a velocity-informed canonical value."""
    db = _fresh_db()
    try:
        ids = _seed_components(db)
        session_id = create_load_development_session(
            db,
            rifle_id=ids["rifle_id"],
            rifle_name="Signal Test Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
            component_selection={"bullet_id": ids["bullet_id"]},
        )

        # Before chrono + before refresh: persisted evidence_summary_json is empty.
        # The live-computed evidence knows nothing about signal_hint yet.
        runtime_before = build_load_session_runtime(db, session_id)
        session_before = runtime_before.get("session") or {}
        hint_before = str(
            (session_before.get("evidence_summary_json") or {}).get("signal_hint") or ""
        ).strip()
        # No refresh has run yet — persisted signal_hint must be empty
        assert (
            hint_before == ""
        ), f"Before any refresh: persisted signal_hint must be empty, got '{hint_before}'"

        # Save chrono import
        db.insert(
            "chronograph_imports",
            {
                "load_session_id": session_id,
                "file_path": "signal_test.csv",
                "velocity_count": 5,
                "velocity_avg": 2800.0,
                "velocity_es": 12.0,
                "velocity_sd": 4.5,
                "velocities_json": json.dumps([2795.0, 2800.0, 2805.0, 2802.0, 2798.0]),
                "import_date": "2026-04-14",
            },
        )

        # Refresh learning state (as chronograph_importer does)
        refresh_load_session_measurement_summary(
            db, session_id, source="test_signal_hint"
        )

        # After refresh: signal_hint must be in the persisted evidence_summary_json
        runtime_after = build_load_session_runtime(db, session_id)
        session_after = runtime_after.get("session") or {}
        hint_after = str(
            (session_after.get("evidence_summary_json") or {}).get("signal_hint") or ""
        ).strip()
        assert hint_after in SPREAD_SIGNAL_HINTS, (
            f"After refresh: hint '{hint_after}' not canonical. "
            f"SPREAD_SIGNAL_HINTS: {SPREAD_SIGNAL_HINTS}"
        )
        assert hint_after != "insufficient_evidence", (
            f"After chrono save + refresh: signal_hint must move from "
            f"'insufficient_evidence', got '{hint_after}'"
        )
        # Live evidence must also reflect the chrono
        has_velocity = (
            (runtime_after.get("evidence") or {})
            .get("summary", {})
            .get("has_measured_velocity")
        )
        assert (
            has_velocity is True
        ), "has_measured_velocity must be True after chrono import + refresh"
    finally:
        db.close()
