import json

from src.utils.barrel_configuration import resolve_active_barrel_configuration_context


class _FakeDb:
    def __init__(self, profile_json):
        self._profile_json = profile_json

    def execute_query(self, query, params=()):
        if "FROM rifle_profile_details" in query:
            return [{"profile_json": json.dumps(self._profile_json)}]
        return []


def test_resolve_active_barrel_configuration_context_uses_active_barrel_muzzle_state():
    context = resolve_active_barrel_configuration_context(
        _FakeDb(
            {
                "active_barrel_id": "pipe-1",
                "barrels": [
                    {
                        "id": "pipe-1",
                        "name": "26in Match Pipe",
                        "length_mm": 660,
                        "twist": "1:8",
                        "muzzle_device_type": "suppressor",
                        "muzzle_device_model": "A-TEC H2",
                        "muzzle_device_weight_g": 420,
                        "poi_shift_h": 0.2,
                        "poi_shift_v": -0.4,
                    }
                ],
            }
        ),
        1,
        rifle_data={"name": "Runtime Rifle", "caliber": "6.5 CM", "twist_rate": "1:8"},
    )

    assert context["barrel_id"] == "pipe-1"
    assert context["barrel_name"] == "26in Match Pipe"
    assert context["barrel_configuration_id"] == "pipe-1-suppressor-a-tec-h2"
    assert context["barrel_configuration_name"] == "Suppressor On (A-TEC H2)"
    assert context["muzzle_device_type"] == "suppressor"
    assert context["suppressor_used"] is True
    assert context["barrel_configuration_snapshot"]["muzzle_device_weight_g"] == 420


def test_resolve_active_barrel_configuration_context_defaults_to_bare_muzzle_when_no_device_is_set():
    context = resolve_active_barrel_configuration_context(
        _FakeDb(
            {
                "active_barrel_id": "pipe-2",
                "barrels": [{"id": "pipe-2", "name": "18in Trainer"}],
            }
        ),
        2,
        rifle_data={"name": "Trainer", "caliber": ".223 Rem"},
    )

    assert context["barrel_configuration_id"] == "pipe-2-bare-muzzle"
    assert context["barrel_configuration_name"] == "Bare Muzzle"
    assert context["muzzle_device_type"] == "none"
    assert context["suppressor_used"] is False


def test_resolve_active_barrel_configuration_context_prefers_explicit_named_configuration():
    context = resolve_active_barrel_configuration_context(
        _FakeDb(
            {
                "active_barrel_id": "pipe-1",
                "active_barrel_configuration_id": "cfg-match-suppressed",
                "barrels": [
                    {
                        "id": "pipe-1",
                        "name": "26in Match Pipe",
                        "muzzle_device_type": "suppressor",
                        "muzzle_device_model": "A-TEC H2",
                    }
                ],
                "barrel_configurations": [
                    {
                        "id": "cfg-match-suppressed",
                        "name": "Match Night Suppressed",
                        "barrel_id": "pipe-1",
                        "barrel_name": "26in Match Pipe",
                        "is_active": True,
                        "muzzle_device_type": "suppressor",
                        "muzzle_device_model": "A-TEC H2",
                        "snapshot": {
                            "muzzle_device_type": "suppressor",
                            "muzzle_device_model": "A-TEC H2",
                            "muzzle_device_weight_g": 420,
                        },
                    }
                ],
            }
        ),
        1,
        rifle_data={"name": "Runtime Rifle", "caliber": "6.5 CM", "twist_rate": "1:8"},
    )

    assert context["barrel_configuration_id"] == "cfg-match-suppressed"
    assert context["barrel_configuration_name"] == "Match Night Suppressed"
    assert context["muzzle_device_type"] == "suppressor"
    assert context["barrel_configuration_snapshot"]["muzzle_device_weight_g"] == 420
