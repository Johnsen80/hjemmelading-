import json

import pytest

# Use a stub class that mimics the Database interface for type compatibility
from src.database.database import Database
from src.modules.ballistics_engine import BallisticsEngine


class _FakeDb(Database):
    def __init__(self, profile_json):
        self.profile_json = profile_json

    def execute_query(self, query, params=()):
        if "FROM rifle_profile_details" in query:
            return [{"profile_json": self.profile_json}]
        return []


@pytest.mark.core
def test_resolve_barrel_profile_prefers_requested_barrel():
    engine = BallisticsEngine()
    details = {
        "active_barrel_id": "barrel-1",
        "barrels": [
            {"id": "barrel-1", "name": "Trening", "caliber": ".223 Remington"},
            {"id": "barrel-2", "name": "Konkurranse", "caliber": ".308 Winchester"},
        ],
    }
    engine.db = _FakeDb(json.dumps(details))

    barrel = engine._resolve_barrel_profile(1, "barrel-2")

    assert barrel is not None
    assert barrel["name"] == "Konkurranse"
    assert barrel["caliber"] == ".308 Winchester"


@pytest.mark.core
def test_calculate_load_applies_barrel_overrides(monkeypatch):
    engine = BallisticsEngine()
    engine.db = _FakeDb("{}")

    monkeypatch.setattr(
        engine,
        "_fetch_rifle",
        lambda rifle_id: {
            "id": rifle_id,
            "caliber": ".223 Remington",
            "barrel_length_inches": 24.0,
            "barrel_contour": "Medium",
            "barrel_weight_grams": 1000.0,
        },
    )
    monkeypatch.setattr(
        engine,
        "_resolve_barrel_profile",
        lambda rifle_id, barrel_id: {
            "id": "barrel-99",
            "name": "Testløp",
            "caliber": ".308 Winchester",
            "length_mm": 660.4,
            "muzzle_device_type": "suppressor",
            "muzzle_device_weight_g": 300.0,
            "case_measurements": {"h2o_capacity_grains": 56.0},
        },
    )
    monkeypatch.setattr(
        engine,
        "_fetch_bullet",
        lambda bullet_id: {"id": bullet_id, "weight_grains": 175, "length_mm": 34.0},
    )
    monkeypatch.setattr(
        engine,
        "_fetch_powder",
        lambda powder_id: {"id": powder_id, "name": "Varget", "density": 0.91},
    )
    monkeypatch.setattr(
        engine,
        "_process_brass_and_case",
        lambda brass_batch_id, case_id: (None, 0, "", []),
    )
    monkeypatch.setattr(
        engine,
        "_determine_case_capacity",
        lambda case_capacity_ml, caliber, *_: (case_capacity_ml, []),
    )
    monkeypatch.setattr(
        engine,
        "_calculate_available_volume",
        lambda case_capacity_ml, *_: case_capacity_ml - 0.5,
    )
    monkeypatch.setattr(
        engine,
        "_calculate_pressure",
        lambda *args, **kwargs: {
            "peak_pressure_psi": 50000.0,
            "pressure_curve": [(0.0, 0.0), (1.0, 50000.0)],
        },
    )
    monkeypatch.setattr(
        engine,
        "_calculate_velocity",
        lambda *args, **kwargs: {
            "muzzle_velocity_fps": 2650.0,
            "velocity_curve": [(0.0, 0.0), (26.0, 2650.0)],
        },
    )
    monkeypatch.setattr(
        engine, "_process_progressive_bc", lambda *args, **kwargs: (0.5, 0.25, [])
    )
    monkeypatch.setattr(
        engine, "_adjust_velocity_for_temp", lambda *args, **kwargs: (2650.0, 0.0)
    )
    monkeypatch.setattr(engine, "_calculate_barrel_time", lambda *args, **kwargs: 1.2)
    monkeypatch.setattr(engine, "_calculate_energy", lambda *args, **kwargs: 2725.0)
    monkeypatch.setattr(engine, "_calculate_powder_volume", lambda *args, **kwargs: 2.1)
    monkeypatch.setattr(
        engine, "_safety_and_compression_checks", lambda *args, **kwargs: (19.0, [])
    )
    monkeypatch.setattr(
        engine, "_process_seating_depth", lambda *args, **kwargs: ({}, [])
    )

    harmonics_args = {}

    def _capture_harmonics(
        barrel_weight_kg,
        barrel_length_inches,
        barrel_contour,
        bullet_weight_gr,
        velocity_fps,
    ):
        harmonics_args["barrel_weight_kg"] = barrel_weight_kg
        harmonics_args["barrel_length_inches"] = barrel_length_inches
        return None

    monkeypatch.setattr(engine, "_maybe_calculate_harmonics", _capture_harmonics)

    result = engine.calculate_load(
        1,
        2,
        3,
        42.0,
        71.0,
        barrel_id="barrel-99",
    )

    assert result["rifle_caliber"] == ".308 Winchester"
    assert result["barrel_id"] == "barrel-99"
    assert result["barrel_name"] == "Testløp"
    assert result["muzzle_device_type"] == "suppressor"
    assert result["barrel_length_inches"] == 26.0
    assert round(result["case_capacity_ml"], 4) == round(56.0 * 0.0648, 4)
    assert harmonics_args["barrel_weight_kg"] == 1.3
    assert "Using barrel-specific H2O capacity" in " ".join(result["warnings"])


@pytest.mark.core
def test_process_progressive_bc_prefers_segmented_bc_when_available():
    engine = BallisticsEngine()

    g1, g7, warnings = engine._process_progressive_bc(
        {
            "bc_g1": 0.462,
            "bc_g7": 0.235,
            "bc_segments_json": '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
        },
        2710.0,
    )

    assert g1 == 0.462
    assert g7 == pytest.approx(0.245)
    assert any("Segmentert BC (G7) aktiv" in warning for warning in warnings)


@pytest.mark.core
def test_process_seating_depth_prefers_matching_barrel_jump_measurement(monkeypatch):
    engine = BallisticsEngine()
    engine.db = _FakeDb("{}")

    def _execute_query(query, params=()):
        normalized = " ".join(query.split())
        if "SELECT jam_length_cbto_mm FROM rifles" in normalized:
            return [{"jam_length_cbto_mm": 0}]
        if "COALESCE(barrel_id, '') = ?" in normalized:
            assert params == (1, 2, "barrel-b")
            return [{"jam_cbto_mm": 56.4}]
        if "FROM rifle_bullet_jump_measurements" in normalized:
            return [{"jam_cbto_mm": 55.9}]
        return []

    engine.db.execute_query = _execute_query
    monkeypatch.setattr(
        engine,
        "calculate_seating_depth_pressure",
        lambda *args, **kwargs: {
            "jump_mm": 0.2,
            "pressure_change_psi": 1800.0,
            "effects": [],
        },
    )

    result = engine._process_seating_depth(
        56.2,
        1,
        2,
        "barrel-b",
        {"peak_pressure_psi": 50000.0},
        3.0,
    )
    # Defensive: _process_seating_depth may return None or (None, warnings)
    if result is None:
        seating, warnings = None, []
    elif isinstance(result, tuple):
        seating, warnings = result
    else:
        seating, warnings = result, []

    assert seating is not None, "seating should not be None"
    assert seating["jump_mm"] == 0.2
    assert seating["pressure_change_psi"] == 1800.0
    assert any("Very close to lands" in warning for warning in warnings)
