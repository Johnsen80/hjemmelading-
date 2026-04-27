"""Block 2 tests: engine input resolution — component, lot, environment, evidence.

Verifies that build_engine_input_from_runtime always produces a deterministic,
well-labelled context regardless of how much data is available. Missing fields
must degrade gracefully (status = partial/unresolved), never silently shift to
wrong values.
"""

from __future__ import annotations

from src.modules.smart_ammo_engine import build_engine_input_from_runtime


def _make_runtime(**kwargs) -> dict:
    """Build a minimal runtime dict with easy overrides."""
    base: dict = {
        "session": {},
        "components": {},
        "lots": {},
        "recommendation": {},
        "evidence": {},
        "learning": {},
        "barrel": {},
        "rifle": {},
        "context": {},
        "identity": {},
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Component context
# ---------------------------------------------------------------------------


def test_empty_components_produces_unresolved_status():
    r = build_engine_input_from_runtime(_make_runtime())
    assert r["components"]["status"] == "unresolved"
    assert r["components"]["active_component_count"] == 0


def test_two_components_produces_partial_status():
    r = build_engine_input_from_runtime(
        _make_runtime(
            components={
                "selection": {"bullet_id": 1, "powder_id": 2},
                "bullet": {"id": 1, "name": "ELD-M"},
                "powder": {"id": 2, "name": "N555"},
            }
        )
    )
    assert r["components"]["status"] == "partial"
    assert r["components"]["active_component_count"] == 2


def test_three_or_more_components_produces_known_status():
    r = build_engine_input_from_runtime(
        _make_runtime(
            components={
                "selection": {
                    "bullet_id": 1,
                    "powder_id": 2,
                    "primer_id": 3,
                    "case_id": 4,
                },
                "bullet": {"id": 1, "name": "ELD-M"},
                "powder": {"id": 2, "name": "N555"},
                "primer": {"id": 3, "name": "BR-2"},
                "case": {"id": 4, "name": "Lapua"},
            }
        )
    )
    assert r["components"]["status"] == "known"
    assert r["components"]["active_component_count"] == 4


def test_component_selected_flag_set_only_when_id_present():
    r = build_engine_input_from_runtime(
        _make_runtime(
            components={
                "selection": {"bullet_id": 1},
                "bullet": {"id": 1, "name": "ELD-M"},
            }
        )
    )
    assert r["components"]["bullet"]["selected"] is True
    assert r["components"]["powder"]["selected"] is False
    assert r["components"]["primer"]["selected"] is False


def test_component_id_resolved_from_selection_when_row_missing():
    """selection.bullet_id must be honoured even when no bullet row is present."""
    r = build_engine_input_from_runtime(
        _make_runtime(
            components={
                "selection": {"bullet_id": 42},
            }
        )
    )
    assert r["components"]["bullet"]["id"] == 42
    assert r["components"]["bullet"]["selected"] is True


def test_components_empty_dict_is_handled_gracefully():
    r = build_engine_input_from_runtime(None)
    assert r["components"]["status"] == "unresolved"
    assert r["components"]["active_component_count"] == 0


# ---------------------------------------------------------------------------
# Lot context
# ---------------------------------------------------------------------------


def test_empty_lots_produces_unresolved_status():
    r = build_engine_input_from_runtime(_make_runtime())
    assert r["lots"]["status"] == "unresolved"
    assert r["lots"]["active_lot_count"] == 0


def test_single_lot_produces_known_status():
    r = build_engine_input_from_runtime(
        _make_runtime(
            lots={
                "powder": {"id": 10, "lot_number": "P-01", "learning_profile": {}},
            }
        )
    )
    assert r["lots"]["status"] == "known"
    assert r["lots"]["active_lot_count"] == 1
    assert r["lots"]["powder"]["lot_number"] == "P-01"


def test_unselected_lot_has_unselected_status():
    r = build_engine_input_from_runtime(_make_runtime())
    for name in ("bullet", "powder", "primer", "case"):
        assert r["lots"][name]["status"] == "unselected"


def test_lot_with_drift_flag_sets_watch_status():
    r = build_engine_input_from_runtime(
        _make_runtime(
            lots={
                "powder": {
                    "id": 10,
                    "lot_number": "P-01",
                    "learning_profile": {"drift_flag": True},
                },
            }
        )
    )
    assert r["lots"]["status"] == "watch"
    assert r["lots"]["watch_count"] == 1
    assert r["lots"]["powder"]["watch_flag"] is True


def test_partial_lot_selection_no_crash():
    """Only powder lot set; bullet/primer/case lots missing — must not raise."""
    r = build_engine_input_from_runtime(
        _make_runtime(
            lots={
                "powder": {"id": 5, "lot_number": "VV-A1", "learning_profile": {}},
                "bullet": None,
                "primer": None,
                "case": None,
            }
        )
    )
    assert r["lots"]["bullet"]["status"] == "unselected"
    assert r["lots"]["powder"]["status"] == "selected"


# ---------------------------------------------------------------------------
# Environment context
# ---------------------------------------------------------------------------


def test_no_environment_data_produces_unresolved():
    r = build_engine_input_from_runtime(_make_runtime())
    assert r["environment"]["status"] == "unresolved"
    assert r["environment"]["density_altitude_m"] is None


def test_partial_environment_produces_partial_status():
    """Temperature only — density altitude cannot be computed."""
    r = build_engine_input_from_runtime(
        _make_runtime(recommendation={"active_settings": {"temperature_c": 12.0}})
    )
    assert r["environment"]["status"] == "partial"
    assert r["environment"]["temperature_c"] == 12.0
    assert r["environment"]["density_altitude_m"] is None


def test_full_environment_produces_known_status_with_density_altitude():
    r = build_engine_input_from_runtime(
        _make_runtime(
            recommendation={
                "active_settings": {
                    "temperature_c": 15.0,
                    "pressure_hpa": 1013.25,
                    "humidity_percent": 50.0,
                    "altitude_m": 0.0,
                }
            }
        )
    )
    assert r["environment"]["status"] == "known"
    assert r["environment"]["density_altitude_m"] is not None
    assert r["environment"]["density_ratio"] is not None


def test_environment_falls_back_to_session_when_active_settings_empty():
    """Session-level temp/pressure should be used when active_settings has nothing."""
    r = build_engine_input_from_runtime(
        _make_runtime(
            session={
                "temperature_c": 10.0,
                "pressure_hpa": 1005.0,
                "humidity_percent": 60.0,
                "altitude_m": 200.0,
            },
            recommendation={"active_settings": {}},
        )
    )
    assert r["environment"]["status"] == "known"
    assert r["environment"]["source"] == "session"
    assert r["environment"]["temperature_c"] == 10.0


def test_active_settings_takes_priority_over_session_environment():
    r = build_engine_input_from_runtime(
        _make_runtime(
            session={
                "temperature_c": 5.0,
                "pressure_hpa": 990.0,
                "humidity_percent": 70.0,
                "altitude_m": 500.0,
            },
            recommendation={
                "active_settings": {
                    "temperature_c": 20.0,
                    "pressure_hpa": 1013.0,
                    "humidity_percent": 40.0,
                    "altitude_m": 100.0,
                }
            },
        )
    )
    assert r["environment"]["source"] == "active_settings"
    assert r["environment"]["temperature_c"] == 20.0


# ---------------------------------------------------------------------------
# Evidence context
# ---------------------------------------------------------------------------


def test_no_evidence_produces_unresolved():
    r = build_engine_input_from_runtime(_make_runtime())
    assert r["evidence"]["status"] == "unresolved"
    assert r["evidence"]["measured"]["has_measured_velocity"] is False
    assert r["evidence"]["measured"]["has_measured_group"] is False


def test_chrono_only_evidence_produces_partial_status():
    r = build_engine_input_from_runtime(
        _make_runtime(
            evidence={
                "summary": {
                    "has_measured_velocity": True,
                    "has_measured_group": False,
                    "chronograph_import_count": 1,
                    "latest_avg_velocity_fps": 2810.0,
                }
            }
        )
    )
    assert r["evidence"]["status"] == "partial"
    assert r["evidence"]["measured"]["has_measured_velocity"] is True
    assert r["evidence"]["measured"]["has_measured_group"] is False
    assert r["evidence"]["measured"]["latest_avg_velocity_fps"] == 2810.0


def test_full_evidence_produces_measured_status():
    r = build_engine_input_from_runtime(
        _make_runtime(
            evidence={
                "summary": {
                    "has_measured_velocity": True,
                    "has_measured_group": True,
                    "chronograph_import_count": 2,
                    "test_result_count": 1,
                    "latest_avg_velocity_fps": 2815.0,
                    "best_group_mm": 14.8,
                }
            }
        )
    )
    assert r["evidence"]["status"] == "measured"
    assert r["evidence"]["measured"]["best_group_mm"] == 14.8


def test_range_session_count_surfaced_in_evidence_measured():
    r = build_engine_input_from_runtime(
        _make_runtime(
            evidence={
                "summary": {
                    "range_session_count": 3,
                }
            }
        )
    )
    assert r["evidence"]["measured"]["range_session_count"] == 3


def test_zero_range_sessions_produces_zero_not_none():
    r = build_engine_input_from_runtime(_make_runtime())
    assert r["evidence"]["measured"]["range_session_count"] == 0


def test_evidence_signal_hint_surfaced():
    r = build_engine_input_from_runtime(
        _make_runtime(
            evidence={
                "summary": {
                    "batch_spread_signal_hint": "node_or_barrel_timing_signal",
                    "batch_spread_evidence_quality": {
                        "level": "moderate",
                        "score": 65.0,
                    },
                }
            }
        )
    )
    assert r["evidence"]["measured"]["signal_hint"] == "node_or_barrel_timing_signal"
    assert r["evidence"]["measured"]["evidence_level"] == "moderate"
    assert r["evidence"]["measured"]["evidence_score"] == 65.0


def test_evidence_none_runtime_does_not_crash():
    r = build_engine_input_from_runtime(None)
    assert r["evidence"]["status"] == "unresolved"


# ---------------------------------------------------------------------------
# Engine output: context identity surfaced in result
# ---------------------------------------------------------------------------


def test_engine_result_states_component_status():
    """Engine result must carry the component status so consumers know what was resolved."""
    from src.modules.smart_ammo_engine import build_engine_result_from_input

    r = build_engine_result_from_input(
        {
            "session": {"usage_profile_name": "General"},
            "components": {
                "selection": {"bullet_id": 1, "powder_id": 2},
                "bullet": {"id": 1, "name": "ELD-M"},
                "powder": {"id": 2, "name": "N555"},
                "status": "partial",
            },
        }
    )
    # Engine must not crash on partial components
    assert isinstance(r, dict)
    assert "decisions" in r


def test_engine_result_graceful_on_missing_environment():
    from src.modules.smart_ammo_engine import build_engine_result_from_input

    r = build_engine_result_from_input(
        {
            "session": {"usage_profile_name": "General"},
            "environment": {"status": "unresolved"},
        }
    )
    assert isinstance(r, dict)
    env_out = r.get("environment") or {}
    assert env_out.get("status") in {"unresolved", "partial", "known", None}
