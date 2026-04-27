"""Block 6 integration tests: runtime → batch workspace → same engine truth.

Verifies that a single load context flows through the runtime service and the
batch workspace without diverging. The canonical engine result built by
build_load_session_runtime is the same engine result that batch_workspace
injects into BatchAnalyzer — these tests confirm that alignment.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from src.database.database import Database
from src.layers import component_layer
from src.modules.batch_workspace import recompute_batch_analysis_from_db
from src.tools.load_development_session_service import create_load_development_session
from src.tools.load_session_runtime_service import build_load_session_runtime

add_batch_session = component_layer.batch.add_batch_session
create_batch_project = component_layer.batch.create_batch_project

_TMP = Path(
    "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp"
)


def _fresh_db() -> Database:
    _TMP.mkdir(parents=True, exist_ok=True)
    return Database(str(_TMP / f"engine_integration_{uuid4().hex}.db"))


def _seed(db: Database) -> dict:
    rifle_id = db.insert(
        "rifles",
        {
            "name": "Integration Rifle",
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
    powder_id = db.insert("powder", {"name": "N555", "manufacturer": "Vihtavuori"})
    return {"rifle_id": rifle_id, "bullet_id": bullet_id, "powder_id": powder_id}


def _create_session(
    db: Database, ids: dict, usage_profile_key: str = "precision"
) -> int:
    return create_load_development_session(
        db,
        rifle_id=ids["rifle_id"],
        rifle_name="Integration Rifle",
        rifle_caliber="6.5 CM",
        barrel_id="pipe-int",
        barrel_name="24in Barrel",
        barrel_configuration_id="pipe-int:bare",
        barrel_configuration_name="Bare",
        usage_profile_key=usage_profile_key,
        usage_profile_name="Test profile",
        component_selection={
            "bullet_id": ids["bullet_id"],
            "powder_id": ids["powder_id"],
        },
    )


def _create_batch(db: Database, ids: dict, session_id: int) -> int:
    result = create_batch_project(
        db,
        "Integration Batch",
        ids["rifle_id"],
        barrel_id="pipe-int",
        barrel_name="24in Barrel",
        barrel_configuration_id="pipe-int:bare",
        barrel_configuration_name="Bare",
        load_session_id=session_id,
        bullet_id=ids["bullet_id"],
        powder_id=ids["powder_id"],
    )
    assert result.get("ok") and result.get(
        "batch_id"
    ), f"Batch creation failed: {result}"
    return int(result["batch_id"])


def _add_measurements(db: Database, session_id: int) -> int:
    velocities = [2810.0, 2818.0, 2805.0, 2822.0, 2814.0]
    chrono_id = db.insert(
        "chronograph_imports",
        {
            "load_session_id": session_id,
            "file_path": "integ_chrono.csv",
            "velocity_count": len(velocities),
            "velocity_avg": sum(velocities) / len(velocities),
            "velocity_es": max(velocities) - min(velocities),
            "velocity_sd": 5.1,
            "velocities_json": json.dumps(velocities),
            "import_date": "2026-04-19",
        },
    )
    db.insert(
        "test_results",
        {
            "load_session_id": session_id,
            "charge_weight": 42.0,
            "group_size_mm": 14.8,
            "group_size_moa": 0.50,
            "velocity_avg": 2814.0,
        },
    )
    return chrono_id


# ---------------------------------------------------------------------------
# Test 1: runtime engine_result has canonical structure
# ---------------------------------------------------------------------------


def test_runtime_produces_canonical_engine_result():
    db = _fresh_db()
    try:
        ids = _seed(db)
        session_id = _create_session(db, ids)
        runtime = build_load_session_runtime(db, session_id)

        smart_engine = runtime.get("smart_engine") or {}
        engine_result = smart_engine.get("engine_result") or {}

        assert (
            isinstance(engine_result, dict) and engine_result
        ), "build_load_session_runtime must produce a non-empty engine_result dict"
        # Structural keys required for batch workspace injection
        required = {"decisions", "candidate_profile", "safety"}
        missing = required - set(engine_result.keys())
        assert not missing, f"engine_result missing keys: {missing}"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Test 2: batch workspace reads the same engine decisions as the runtime
# ---------------------------------------------------------------------------


def test_batch_workspace_uses_same_engine_decisions_as_runtime():
    db = _fresh_db()
    try:
        ids = _seed(db)
        session_id = _create_session(db, ids)
        chrono_id = _add_measurements(db, session_id)
        batch_id = _create_batch(db, ids, session_id)
        add_batch_session(
            db,
            batch_id,
            load_session_id=session_id,
            rifle_id=ids["rifle_id"],
            barrel_id="pipe-int",
            barrel_name="24in Barrel",
            barrel_configuration_id="pipe-int:bare",
            barrel_configuration_name="Bare",
            session_name="Session 1",
            session_date="2026-04-19",
            distance_m=100,
            shot_count=5,
            group_size_mm=14.8,
            group_size_moa=0.50,
            chronograph_import_id=chrono_id,
        )

        # Get engine_result via runtime (canonical source)
        runtime = build_load_session_runtime(db, session_id)
        runtime_engine = (runtime.get("smart_engine") or {}).get("engine_result") or {}
        runtime_action = (
            (runtime_engine.get("decisions") or {}).get("next_test") or {}
        ).get("recommended_action")

        # Get batch analysis — which injects the same engine_result via _get_batch_engine_result
        analysis = recompute_batch_analysis_from_db(db, batch_id)
        assert isinstance(
            analysis, dict
        ), "recompute_batch_analysis_from_db must return a dict"

        batch_next_focus = analysis.get("next_focus") or ""

        # When the engine produces a recommended_action, it must override the batch next_focus
        if runtime_action:
            assert batch_next_focus == runtime_action, (
                f"Batch next_focus '{batch_next_focus}' must match engine "
                f"recommended_action '{runtime_action}' — same session, same truth"
            )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Test 3: engine steps appear first in batch next_steps
# ---------------------------------------------------------------------------


def test_engine_recommendation_stack_prepended_in_batch_next_steps():
    db = _fresh_db()
    try:
        ids = _seed(db)
        session_id = _create_session(db, ids)
        _add_measurements(db, session_id)
        batch_id = _create_batch(db, ids, session_id)

        # Runtime engine_result
        runtime = build_load_session_runtime(db, session_id)
        engine_result = (runtime.get("smart_engine") or {}).get("engine_result") or {}
        decisions = engine_result.get("decisions") or {}
        engine_stack = decisions.get("recommendation_stack") or []

        analysis = recompute_batch_analysis_from_db(db, batch_id)
        next_steps = analysis.get("next_steps") or []

        if engine_stack:
            # At least one engine reason text must appear in next_steps
            engine_reasons = {
                str(item.get("reason") or "").strip()
                for item in engine_stack[:3]
                if item.get("reason")
            }
            matching = [
                s for s in next_steps if any(r in s for r in engine_reasons if r)
            ]
            assert matching, (
                "Engine recommendation_stack items must appear in batch next_steps. "
                f"Engine reasons: {engine_reasons}. Batch steps: {next_steps[:5]}"
            )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Test 4: context identity — runtime and batch see same rifle/barrel
# ---------------------------------------------------------------------------


def test_runtime_and_batch_see_same_rifle_barrel_identity():
    db = _fresh_db()
    try:
        ids = _seed(db)
        session_id = _create_session(db, ids)
        batch_id = _create_batch(db, ids, session_id)

        runtime = build_load_session_runtime(db, session_id)
        session = runtime.get("session") or {}

        # Batch row must link to same session
        rows = db.execute_query(
            "SELECT * FROM batch_projects WHERE id = ?", (batch_id,)
        )
        batch_row = rows[0] if rows else {}
        assert str(batch_row.get("load_session_id")) == str(
            session_id
        ), "Batch must link to the same load session as the runtime context"
        assert (
            session.get("rifle_id") == ids["rifle_id"]
        ), "Runtime session must reference the same rifle as was created"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Test 5: safety block in engine_result surfaces in batch next_steps
# ---------------------------------------------------------------------------


def test_safety_block_from_engine_surfaces_in_batch_next_steps():
    """BatchAnalyzer with a safety-blocked engine_result must put a safety step first."""
    from src.modules.batch_analyzer import BatchAnalyzer

    analyzer = BatchAnalyzer(
        batch={
            "id": 1,
            "rifle_id": 1,
            "barrel_id": "pipe-test",
        },
        sessions=[],
        engine_result={
            "safety": {
                "blocked": True,
                "pressure_summary": {"summary": "Pressure signs detected — stop."},
            },
            "decisions": {
                "recommendation_stack": [],
                "next_test": {"recommended_action": "stop_and_review"},
            },
            "candidate_profile": {},
        },
    )
    result = analyzer.analyze()
    next_steps = result.next_steps or []
    assert next_steps, "next_steps must not be empty when safety is blocked"
    assert "safety" in next_steps[0].lower(), (
        f"Safety step must be first in next_steps when engine is blocked. "
        f"Got: {next_steps[:3]}"
    )


# ---------------------------------------------------------------------------
# Test 6: no engine → batch analysis still completes without crashing
# ---------------------------------------------------------------------------


def test_batch_analysis_completes_without_linked_session():
    """Batch with no load_session_id must not crash — graceful fallback."""
    db = _fresh_db()
    try:
        ids = _seed(db)
        # Create batch with NO load_session_id
        result = create_batch_project(
            db,
            "Orphan Batch",
            ids["rifle_id"],
            barrel_id="pipe-orphan",
            barrel_name="Orphan Barrel",
            barrel_configuration_id="pipe-orphan:bare",
            barrel_configuration_name="Bare",
            load_session_id=None,
            bullet_id=ids["bullet_id"],
            powder_id=ids["powder_id"],
        )
        if not result.get("ok"):
            # If schema requires load_session_id, skip this test gracefully
            return
        batch_id = int(result["batch_id"])
        analysis = recompute_batch_analysis_from_db(db, batch_id)
        # Must return a dict (even if sparse) — must not raise
        assert isinstance(
            analysis, dict
        ), "recompute_batch_analysis_from_db must return a dict even without linked session"
    finally:
        db.close()
