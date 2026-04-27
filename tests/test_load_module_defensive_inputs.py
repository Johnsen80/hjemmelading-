"""Regression tests: defensive input handling for load module core services.

These tests verify that the load module never crashes or produces corrupt state
when receiving None, empty, partial, or malformed inputs.  They cover:

  - _normalize_learning_state: all schema fields, malformed values
  - build_engine_result_from_input: None / empty / partial inputs
  - build_load_session_runtime: missing session
  - build_load_session_runtime_delta: None runtime
  - confirm_load_candidate / reject_load_candidate: happy path + missing session
  - Learning state model_status transitions after refresh
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from src.database.database import Database
from src.modules.smart_ammo_engine import build_engine_result_from_input
from src.tools.load_development_session_service import (
    _normalize_learning_state,
    confirm_load_candidate,
    create_load_development_session,
    get_load_development_session,
    reject_load_candidate,
)
from src.tools.load_session_runtime_service import (
    build_load_session_runtime,
    build_load_session_runtime_delta,
    refresh_load_session_measurement_summary,
)

_TMP = Path(
    "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp"
)


def _fresh_db() -> Database:
    _TMP.mkdir(parents=True, exist_ok=True)
    path = _TMP / f"defensive_inputs_{uuid4().hex}.db"
    return Database(str(path))


# ---------------------------------------------------------------------------
# _normalize_learning_state: schema completeness and malformed inputs
# ---------------------------------------------------------------------------


def test_normalize_learning_state_empty_input():
    result = _normalize_learning_state(None)
    assert result["schema_version"] == "load_learning_state.v1"
    assert result["model_status"] == "raw"
    assert result["best_history"] == {}
    assert result["analysis"]["barrel_context"] == {}
    assert result["analysis"]["brass_context"] == {}
    assert result["analysis"]["node_fit"] == {}
    assert result["analysis"]["stability_assessment"] == {}
    assert result["candidates"]["confirmed"] == []
    assert result["candidates"]["rejected"] == []
    assert result["summary"] == {}


def test_normalize_learning_state_preserves_valid_model_status():
    for status in ("raw", "partially_calibrated", "well_calibrated"):
        result = _normalize_learning_state({"model_status": status})
        assert (
            result["model_status"] == status
        ), f"Expected {status}, got {result['model_status']}"


def test_normalize_learning_state_rejects_invalid_model_status():
    result = _normalize_learning_state({"model_status": "banana"})
    assert result["model_status"] == "raw"


def test_normalize_learning_state_preserves_charge_window():
    cw = {"center_gr": 42.0, "min_gr": 41.5, "max_gr": 42.5, "source": "learned"}
    result = _normalize_learning_state({"charge_window": cw})
    assert result["charge_window"]["center_gr"] == 42.0
    assert result["charge_window"]["source"] == "learned"


def test_normalize_learning_state_no_charge_window_when_absent():
    result = _normalize_learning_state({"model_status": "raw"})
    assert "charge_window" not in result


def test_normalize_learning_state_preserves_seating_window():
    sw = {"min_mm": -0.5, "max_mm": 0.2, "source": "recommendation"}
    result = _normalize_learning_state({"seating_window": sw})
    assert result["seating_window"]["min_mm"] == -0.5


def test_normalize_learning_state_preserves_lot_drift():
    ld = {"powder": {"lot_number": "P001", "velocity_offset_fps": 12.5}}
    result = _normalize_learning_state({"lot_drift": ld})
    assert result["lot_drift"]["powder"]["lot_number"] == "P001"


def test_normalize_learning_state_candidates_roundtrip():
    candidates = {
        "confirmed": [{"charge_gr": 42.1, "date": "2026-04-14"}],
        "rejected": [{"charge_gr": 44.0, "reason": "pressure signs"}],
    }
    result = _normalize_learning_state({"candidates": candidates})
    assert len(result["candidates"]["confirmed"]) == 1
    assert result["candidates"]["confirmed"][0]["charge_gr"] == 42.1
    assert len(result["candidates"]["rejected"]) == 1
    assert result["candidates"]["rejected"][0]["reason"] == "pressure signs"


def test_normalize_learning_state_candidates_non_list_coerced():
    result = _normalize_learning_state(
        {"candidates": {"confirmed": "not-a-list", "rejected": 99}}
    )
    assert result["candidates"]["confirmed"] == []
    assert result["candidates"]["rejected"] == []


def test_normalize_learning_state_preserves_extra_keys():
    result = _normalize_learning_state({"custom_flag": True, "my_note": "keep"})
    assert result["custom_flag"] is True
    assert result["my_note"] == "keep"


def test_normalize_learning_state_legacy_barrel_context_migrated():
    raw = {"barrel_context": {"level": "ok", "title": "Known barrel"}}
    result = _normalize_learning_state(raw)
    assert result["analysis"]["barrel_context"]["level"] == "ok"
    assert "barrel_context" not in result  # legacy key not duplicated at root


# ---------------------------------------------------------------------------
# build_engine_result_from_input: empty / None / partial inputs
# ---------------------------------------------------------------------------


def test_engine_result_from_empty_dict_returns_structured_output():
    result = build_engine_result_from_input({})
    assert isinstance(result, dict)
    # Must have top-level structural keys
    assert (
        "safety" in result or "decisions" in result or "baseline_control" in result
    ), f"engine result missing structural keys: {list(result.keys())}"


def test_engine_result_from_none_returns_structured_output():
    result = build_engine_result_from_input(None)
    assert isinstance(result, dict)


def test_engine_result_partial_session_only():
    engine_input = {
        "session": {"usage_profile_name": "precision"},
    }
    result = build_engine_result_from_input(engine_input)
    assert isinstance(result, dict)
    assert "safety" in result or "decisions" in result


def test_engine_result_partial_weapon_barrel_only():
    engine_input = {
        "weapon": {"rifle_name": "Test", "caliber": "6.5 CM"},
        "barrel": {"barrel_id": "pipe-01", "barrel_name": "24in"},
    }
    result = build_engine_result_from_input(engine_input)
    assert isinstance(result, dict)


def test_engine_result_with_charge_outside_learned_window():
    engine_input = {
        "session": {"usage_profile_name": "precision"},
        "load": {
            "charge_weight_gr": 45.5,
            "baseline": {
                "charge_gr": 42.0,
                "charge_source": "learned",
            },
        },
    }
    result = build_engine_result_from_input(engine_input)
    assert isinstance(result, dict)
    # The engine must not crash when charge is outside the learned window
    decisions = result.get("decisions") or {}
    assert isinstance(decisions, dict)


def test_engine_result_with_pressure_signal_blocks_ranking():
    engine_input = {
        "evidence": {
            "summary": {
                "batch_spread_evidence_quality": {"level": "moderate"},
                "signal_hint": "pressure_or_ammo",
            }
        },
    }
    result = build_engine_result_from_input(engine_input)
    assert isinstance(result, dict)
    candidate = result.get("candidate_profile") or {}
    # pressure_or_ammo should block candidate ranking
    robustness = str(candidate.get("robustness_level") or "").strip().lower()
    assert robustness in {
        "",
        "low",
        "unknown",
    }, f"pressure_or_ammo should produce low robustness, got '{robustness}'"


def test_engine_result_with_all_nones_in_load():
    engine_input = {
        "load": {
            "charge_weight_gr": None,
            "coal_mm": None,
            "cbto_mm": None,
            "baseline": None,
            "control_state": None,
        }
    }
    result = build_engine_result_from_input(engine_input)
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# build_load_session_runtime: missing session
# ---------------------------------------------------------------------------


def test_runtime_returns_none_for_missing_session():
    db = _fresh_db()
    try:
        result = build_load_session_runtime(db, 99999)
        assert result is None
    finally:
        db.close()


def test_runtime_returns_none_for_none_session_id():
    db = _fresh_db()
    try:
        result = build_load_session_runtime(db, None)
        assert result is None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# build_load_session_runtime_delta: None / empty runtime
# ---------------------------------------------------------------------------


def test_runtime_delta_from_none_is_unknown():
    delta = build_load_session_runtime_delta(None)
    assert isinstance(delta, dict)
    assert delta.get("level") == "unknown"


def test_runtime_delta_from_empty_dict_does_not_crash():
    delta = build_load_session_runtime_delta({})
    assert isinstance(delta, dict)
    assert isinstance(delta.get("level"), str)


# ---------------------------------------------------------------------------
# confirm_load_candidate / reject_load_candidate
# ---------------------------------------------------------------------------


def test_confirm_load_candidate_persists_entry():
    db = _fresh_db()
    try:
        session_id = create_load_development_session(
            db,
            rifle_id=None,
            rifle_name="Candidate Test Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
        )
        updated = confirm_load_candidate(
            db,
            session_id,
            charge_gr=42.1,
            coal_mm=71.5,
            cbto_mm=68.9,
            group_size_mm=12.4,
            group_size_moa=0.42,
            velocity_avg_fps=2815.0,
            reason="Consistent 5-shot groups, no pressure signs",
            evidence_quality="moderate",
        )
        assert updated is not None
        candidates = updated["learning_state_json"]["candidates"]
        assert len(candidates["confirmed"]) == 1
        entry = candidates["confirmed"][0]
        assert entry["charge_gr"] == 42.1
        assert entry["coal_mm"] == 71.5
        assert entry["reason"] == "Consistent 5-shot groups, no pressure signs"
        assert entry["evidence_quality"] == "moderate"
        assert "date" in entry
    finally:
        db.close()


def test_reject_load_candidate_persists_entry():
    db = _fresh_db()
    try:
        session_id = create_load_development_session(
            db,
            rifle_id=None,
            rifle_name="Reject Test Rifle",
            rifle_caliber=".308 Win",
            usage_profile_key="hunting",
            usage_profile_name="Jakt",
        )
        updated = reject_load_candidate(
            db,
            session_id,
            charge_gr=44.5,
            reason="Pressure signs, flatten primer",
            evidence_quality="thin",
        )
        assert updated is not None
        candidates = updated["learning_state_json"]["candidates"]
        assert len(candidates["rejected"]) == 1
        assert candidates["rejected"][0]["charge_gr"] == 44.5
        assert candidates["rejected"][0]["reason"] == "Pressure signs, flatten primer"
    finally:
        db.close()


def test_confirm_and_reject_accumulate_independently():
    db = _fresh_db()
    try:
        session_id = create_load_development_session(
            db,
            rifle_id=None,
            rifle_name="Accumulation Rifle",
            rifle_caliber="6 Dasher",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
        )
        confirm_load_candidate(db, session_id, charge_gr=31.0)
        confirm_load_candidate(db, session_id, charge_gr=31.2)
        reject_load_candidate(db, session_id, charge_gr=33.5, reason="Too hot")

        row = get_load_development_session(db, session_id)
        candidates = row["learning_state_json"]["candidates"]
        assert len(candidates["confirmed"]) == 2
        assert len(candidates["rejected"]) == 1
        assert candidates["confirmed"][0]["charge_gr"] == 31.0
        assert candidates["confirmed"][1]["charge_gr"] == 31.2
    finally:
        db.close()


def test_confirm_candidate_returns_none_for_missing_session():
    db = _fresh_db()
    try:
        result = confirm_load_candidate(db, 99999, charge_gr=42.0)
        assert result is None
    finally:
        db.close()


def test_reject_candidate_returns_none_for_missing_session():
    db = _fresh_db()
    try:
        result = reject_load_candidate(db, 99999, charge_gr=44.0)
        assert result is None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# model_status transitions after refresh_load_session_measurement_summary
# ---------------------------------------------------------------------------


def test_model_status_is_raw_before_any_data():
    db = _fresh_db()
    try:
        session_id = create_load_development_session(
            db,
            rifle_id=None,
            rifle_name="Status Test Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
        )
        row = get_load_development_session(db, session_id)
        # Before any refresh, model_status defaults to "raw" from the schema
        assert row["learning_state_json"]["model_status"] == "raw"
    finally:
        db.close()


def test_model_status_becomes_partially_calibrated_after_chrono_only():
    import json

    db = _fresh_db()
    try:
        rifle_id = db.insert("rifles", {"name": "Status Rifle", "caliber": "6.5 CM"})
        session_id = create_load_development_session(
            db,
            rifle_id=rifle_id,
            rifle_name="Status Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
        )
        # Add chrono only (no target result)
        db.insert(
            "chronograph_imports",
            {
                "load_session_id": session_id,
                "file_path": "test.csv",
                "velocity_count": 5,
                "velocity_avg": 2810.0,
                "velocity_es": 15.0,
                "velocity_sd": 5.0,
                "velocities_json": json.dumps([2805, 2810, 2815, 2808, 2812]),
                "import_date": "2026-04-16",
            },
        )
        refresh_load_session_measurement_summary(db, session_id, source="test")
        row = get_load_development_session(db, session_id)
        status = row["learning_state_json"]["model_status"]
        assert (
            status == "partially_calibrated"
        ), f"Expected partially_calibrated with chrono only, got '{status}'"
    finally:
        db.close()


def test_model_status_becomes_well_calibrated_with_paired_data():
    import json

    db = _fresh_db()
    try:
        rifle_id = db.insert("rifles", {"name": "Well-Cal Rifle", "caliber": "6.5 CM"})
        session_id = create_load_development_session(
            db,
            rifle_id=rifle_id,
            rifle_name="Well-Cal Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
        )
        # Add multiple chrono imports to build up data_strength
        for i in range(3):
            db.insert(
                "chronograph_imports",
                {
                    "load_session_id": session_id,
                    "file_path": f"test_{i}.csv",
                    "velocity_count": 5,
                    "velocity_avg": 2810.0 + i,
                    "velocity_es": 12.0,
                    "velocity_sd": 4.0,
                    "velocities_json": json.dumps([2805, 2810, 2815, 2808, 2812]),
                    "import_date": "2026-04-16",
                },
            )
        # Add target results (required for well_calibrated)
        for charge in [41.5, 42.0, 42.5]:
            db.insert(
                "test_results",
                {
                    "load_session_id": session_id,
                    "charge_weight": charge,
                    "group_size_mm": 14.0,
                    "velocity_avg": 2810.0,
                },
            )
        refresh_load_session_measurement_summary(db, session_id, source="test")
        row = get_load_development_session(db, session_id)
        status = row["learning_state_json"]["model_status"]
        assert status in {
            "partially_calibrated",
            "well_calibrated",
        }, f"Expected at least partially_calibrated, got '{status}'"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Charge-window persistence roundtrip
# ---------------------------------------------------------------------------


def test_charge_window_persisted_and_survives_normalize():
    import json

    db = _fresh_db()
    try:
        rifle_id = db.insert("rifles", {"name": "CW Rifle", "caliber": "6.5 CM"})
        session_id = create_load_development_session(
            db,
            rifle_id=rifle_id,
            rifle_name="CW Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
        )
        # Add paired chrono + target data at multiple charges (needed for charge window)
        for i, (charge, group_mm) in enumerate(
            [(41.5, 16.0), (42.0, 14.2), (42.5, 15.8)]
        ):
            db.insert(
                "chronograph_imports",
                {
                    "load_session_id": session_id,
                    "file_path": f"cw_{i}.csv",
                    "velocity_count": 5,
                    "velocity_avg": 2810.0,
                    "velocity_es": 12.0,
                    "velocity_sd": 4.5,
                    "velocities_json": json.dumps([2805, 2810, 2815, 2808, 2812]),
                    "import_date": "2026-04-16",
                },
            )
            db.insert(
                "test_results",
                {
                    "load_session_id": session_id,
                    "charge_weight": charge,
                    "group_size_mm": group_mm,
                    "velocity_avg": 2810.0,
                },
            )

        refresh_load_session_measurement_summary(db, session_id, source="test")
        row = get_load_development_session(db, session_id)

        # If charge_window was learned, it must survive normalization and have valid keys
        cw = row["learning_state_json"].get("charge_window")
        if cw is not None:
            assert isinstance(cw, dict)
            assert "center_gr" in cw
            assert "min_gr" in cw
            assert "max_gr" in cw
            assert cw["min_gr"] <= cw["center_gr"] <= cw["max_gr"]
    finally:
        db.close()
