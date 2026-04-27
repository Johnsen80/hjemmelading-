from types import SimpleNamespace

from src.modules import rifle_profile_editor as editor_module


class _FakeDb:
    def __init__(self):
        self.profile_json = {
            "active_barrel_id": "pipe-b",
            "barrels": [{"id": "pipe-b", "name": "26in Match"}],
            "bullet_profiles_by_barrel": {
                "pipe-a": [{"bullet_name": "Legacy A", "jam_length_cbto_mm": "55.10"}]
            },
            "legacy_flag": True,
        }
        self.updated_payload = None
        self.insert_calls = []
        self.delete_calls = []

    def execute_query(self, query, params=()):
        normalized = " ".join(query.split())
        if (
            "FROM rifle_profile_details" in normalized
            and "SELECT profile_json" in normalized
        ):
            return [{"profile_json": editor_module.json.dumps(self.profile_json)}]
        if "FROM rifle_profile_details" in normalized and "SELECT id" in normalized:
            return [{"id": 1}]
        if "FROM bullets" in normalized:
            assert params == ("ELD-M",)
            return [{"id": 7, "weight_grains": 140.0}]
        return []

    def update(self, table, payload, condition, params):
        assert table == "rifle_profile_details"
        self.updated_payload = payload

    def insert(self, table, payload):
        self.insert_calls.append((table, payload))
        return len(self.insert_calls)

    def delete(self, table, condition, params=()):
        self.delete_calls.append((table, condition, params))


def test_save_profile_details_preserves_existing_barrel_context():
    widget = SimpleNamespace(db=_FakeDb())
    widget._load_existing_profile_details = lambda rifle_id: editor_module.RifleProfileEditor._load_existing_profile_details(
        widget, rifle_id
    )
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )
    widget._sync_explicit_barrel_configurations = lambda details: editor_module.RifleProfileEditor._sync_explicit_barrel_configurations(
        widget, details
    )

    merged = editor_module.RifleProfileEditor._save_profile_details(
        widget,
        4,
        {"bullet_profiles": [], "user_mode": "expert"},
    )

    assert merged["active_barrel_id"] == "pipe-b"
    assert merged["barrels"][0]["name"] == "26in Match"
    assert merged["bullet_profiles_by_barrel"]["pipe-a"][0]["bullet_name"] == "Legacy A"
    assert merged["legacy_flag"] is True
    assert widget.db.updated_payload is not None


def test_store_active_barrel_bullet_profiles_scopes_to_active_barrel():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )

    details = {
        "active_barrel_id": "pipe-b",
        "barrels": [{"id": "pipe-b", "name": "26in Match"}],
        "bullet_profiles_by_barrel": {
            "pipe-a": [{"bullet_name": "Older Barrel", "jam_length_cbto_mm": "55.40"}]
        },
    }
    profiles = [{"bullet_name": "ELD-M", "jam_length_cbto_mm": "56.18"}]

    updated = editor_module.RifleProfileEditor._store_active_barrel_bullet_profiles(
        widget,
        details,
        profiles,
    )

    assert (
        updated["bullet_profiles_by_barrel"]["pipe-a"][0]["bullet_name"]
        == "Older Barrel"
    )
    assert updated["bullet_profiles_by_barrel"]["pipe-b"][0]["bullet_name"] == "ELD-M"
    assert updated["bullet_profiles"][0]["bullet_name"] == "ELD-M"


def test_get_active_barrel_bullet_profiles_prefers_scoped_profiles():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )

    profiles = editor_module.RifleProfileEditor._get_active_barrel_bullet_profiles(
        widget,
        {
            "active_barrel_id": "pipe-b",
            "barrels": [{"id": "pipe-b", "name": "26in Match"}],
            "bullet_profiles": [{"bullet_name": "Legacy"}],
            "bullet_profiles_by_barrel": {
                "pipe-b": [{"bullet_name": "Scoped"}],
            },
        },
    )

    assert profiles[0]["bullet_name"] == "Scoped"


def test_store_active_barrel_chamber_details_scopes_to_active_barrel():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )

    details = {
        "active_barrel_id": "pipe-b",
        "barrels": [{"id": "pipe-b", "name": "26in Match"}],
        "chamber_details_by_barrel": {
            "pipe-a": {"chamber_spec": ".308 Win", "headspace": 44.6}
        },
    }

    updated = editor_module.RifleProfileEditor._store_active_barrel_chamber_details(
        widget,
        details,
        {"chamber_spec": ".308 Palma", "headspace": 44.9, "shoulder_bump": 0.03},
    )

    assert updated["chamber_details_by_barrel"]["pipe-a"]["chamber_spec"] == ".308 Win"
    assert (
        updated["chamber_details_by_barrel"]["pipe-b"]["chamber_spec"] == ".308 Palma"
    )
    assert updated["headspace"] == 44.9


def test_get_active_barrel_chamber_details_prefers_scoped_values():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )

    chamber = editor_module.RifleProfileEditor._get_active_barrel_chamber_details(
        widget,
        {
            "active_barrel_id": "pipe-b",
            "barrels": [{"id": "pipe-b", "name": "26in Match"}],
            "chamber_spec": "Legacy chamber",
            "headspace": 44.5,
            "chamber_details_by_barrel": {
                "pipe-b": {"chamber_spec": ".308 Palma", "headspace": 44.9},
            },
        },
    )

    assert chamber["chamber_spec"] == ".308 Palma"
    assert chamber["headspace"] == 44.9


def test_store_active_barrel_muzzle_details_updates_barrel_entry():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )
    widget._sync_explicit_barrel_configurations = lambda details: editor_module.RifleProfileEditor._sync_explicit_barrel_configurations(
        widget, details
    )

    details = {
        "active_barrel_id": "pipe-b",
        "barrels": [
            {"id": "pipe-a", "name": "Training", "muzzle_device_type": "Muzzle Brake"},
            {"id": "pipe-b", "name": "26in Match"},
        ],
    }

    updated = editor_module.RifleProfileEditor._store_active_barrel_muzzle_details(
        widget,
        details,
        {
            "has_muzzle_device": True,
            "device_type": "Suppressor",
            "device_manufacturer": "A-TEC H2",
            "device_length": 182,
            "device_weight": 340,
            "device_diameter": 44.5,
            "thread_pitch": "M18x1",
            "poi_tested": True,
            "poi_shift_h": -0.4,
            "poi_shift_v": 1.1,
        },
    )

    assert updated["barrels"][0]["muzzle_device_type"] == "Muzzle Brake"
    assert updated["barrels"][1]["muzzle_device_type"] == "Suppressor"
    assert updated["barrels"][1]["muzzle_device_weight_g"] == 340
    assert updated["device_manufacturer"] == "A-TEC H2"
    assert updated["active_barrel_configuration_id"] == "pipe-b-suppressor-a-tec-h2"
    assert updated["barrel_configurations"][0]["id"] == "pipe-b-suppressor-a-tec-h2"
    assert updated["barrel_configurations"][0]["name"] == "Suppressor On (A-TEC H2)"


def test_store_active_barrel_muzzle_details_preserves_explicit_configuration_name():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )
    widget._sync_explicit_barrel_configurations = lambda details: editor_module.RifleProfileEditor._sync_explicit_barrel_configurations(
        widget, details
    )

    details = {
        "active_barrel_id": "pipe-b",
        "active_barrel_configuration_id": "cfg-night-suppressed",
        "barrels": [
            {"id": "pipe-b", "name": "26in Match"},
        ],
        "barrel_configurations": [
            {
                "id": "cfg-night-suppressed",
                "name": "Night Match Suppressed",
                "barrel_id": "pipe-b",
                "barrel_name": "26in Match",
                "is_active": True,
                "snapshot": {
                    "muzzle_device_type": "suppressor",
                    "muzzle_device_model": "Old Can",
                },
            }
        ],
    }

    updated = editor_module.RifleProfileEditor._store_active_barrel_muzzle_details(
        widget,
        details,
        {
            "has_muzzle_device": True,
            "device_type": "Suppressor",
            "device_manufacturer": "A-TEC H2",
            "device_length": 182,
            "device_weight": 340,
            "device_diameter": 44.5,
            "thread_pitch": "M18x1",
            "poi_tested": True,
            "poi_shift_h": -0.4,
            "poi_shift_v": 1.1,
        },
    )

    assert updated["active_barrel_configuration_id"] == "cfg-night-suppressed"
    assert updated["barrel_configurations"][0]["name"] == "Night Match Suppressed"
    assert (
        updated["barrel_configurations"][0]["snapshot"]["muzzle_device_model"]
        == "A-TEC H2"
    )


def test_store_active_barrel_muzzle_details_uses_custom_active_configuration_name():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )
    widget._sync_explicit_barrel_configurations = lambda details: editor_module.RifleProfileEditor._sync_explicit_barrel_configurations(
        widget, details
    )

    updated = editor_module.RifleProfileEditor._store_active_barrel_muzzle_details(
        widget,
        {
            "active_barrel_id": "pipe-b",
            "barrels": [{"id": "pipe-b", "name": "26in Match"}],
        },
        {
            "has_muzzle_device": True,
            "device_type": "Suppressor",
            "device_manufacturer": "A-TEC H2",
            "device_length": 182,
            "device_weight": 340,
            "device_diameter": 44.5,
            "thread_pitch": "M18x1",
            "poi_tested": True,
            "poi_shift_h": -0.4,
            "poi_shift_v": 1.1,
            "active_barrel_configuration_name": "Match Suppressed",
        },
    )

    assert updated["active_barrel_configuration_name"] == "Match Suppressed"
    assert updated["barrel_configurations"][0]["name"] == "Match Suppressed"


def test_get_active_barrel_muzzle_details_prefers_barrel_entry():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )
    widget._get_active_muzzle_configuration_entry = lambda details, barrel_id=None, configuration_id=None: editor_module.RifleProfileEditor._get_active_muzzle_configuration_entry(
        widget,
        details,
        barrel_id=barrel_id,
        configuration_id=configuration_id,
    )

    muzzle = editor_module.RifleProfileEditor._get_active_barrel_muzzle_details(
        widget,
        {
            "active_barrel_id": "pipe-b",
            "barrels": [
                {
                    "id": "pipe-b",
                    "name": "26in Match",
                    "muzzle_device_type": "Suppressor",
                    "muzzle_device_model": "A-TEC H2",
                    "muzzle_device_weight_g": 340,
                    "thread_pitch": "M18x1",
                    "poi_tested": True,
                }
            ],
            "device_type": "Legacy Brake",
            "device_weight": 120,
        },
    )

    assert muzzle["device_type"] == "Suppressor"
    assert muzzle["device_manufacturer"] == "A-TEC H2"
    assert muzzle["device_weight"] == 340
    assert muzzle["thread_pitch"] == "M18x1"


def test_get_active_barrel_muzzle_details_prefers_active_configuration_snapshot():
    widget = SimpleNamespace()
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )
    widget._get_active_muzzle_configuration_entry = lambda details, barrel_id=None, configuration_id=None: editor_module.RifleProfileEditor._get_active_muzzle_configuration_entry(
        widget,
        details,
        barrel_id=barrel_id,
        configuration_id=configuration_id,
    )

    muzzle = editor_module.RifleProfileEditor._get_active_barrel_muzzle_details(
        widget,
        {
            "active_barrel_id": "pipe-b",
            "active_barrel_configuration_id": "cfg-training-brake",
            "barrels": [
                {
                    "id": "pipe-b",
                    "name": "26in Match",
                    "muzzle_device_type": "Suppressor",
                    "muzzle_device_model": "A-TEC H2",
                    "muzzle_device_weight_g": 340,
                    "thread_pitch": "M18x1",
                    "poi_tested": True,
                }
            ],
            "barrel_configurations": [
                {
                    "id": "cfg-training-brake",
                    "name": "Brake Training",
                    "barrel_id": "pipe-b",
                    "barrel_name": "26in Match",
                    "is_active": True,
                    "snapshot": {
                        "muzzle_device_type": "Muzzle Brake",
                        "muzzle_device_model": "Area 419",
                        "muzzle_device_weight_g": 120,
                        "thread_pitch": "5/8-24 UNF",
                        "poi_shift_h": 0.3,
                    },
                }
            ],
        },
    )

    assert muzzle["device_type"] == "Muzzle Brake"
    assert muzzle["device_manufacturer"] == "Area 419"
    assert muzzle["device_weight"] == 120
    assert muzzle["thread_pitch"] == "5/8-24 UNF"
    assert muzzle["active_barrel_configuration_name"] == "Brake Training"


def test_sync_bullet_profiles_to_jump_measurements_writes_barrel_scoped_rows():
    widget = SimpleNamespace(db=_FakeDb())
    widget._resolve_active_barrel_context = (
        lambda details: editor_module.RifleProfileEditor._resolve_active_barrel_context(
            widget, details
        )
    )
    widget._get_active_barrel_bullet_profiles = lambda details: editor_module.RifleProfileEditor._get_active_barrel_bullet_profiles(
        widget, details
    )
    widget._find_bullet_id_for_profile = (
        lambda profile: editor_module.RifleProfileEditor._find_bullet_id_for_profile(
            widget, profile
        )
    )
    widget._parse_optional_float = staticmethod(
        editor_module.RifleProfileEditor._parse_optional_float
    )

    details = {
        "active_barrel_id": "pipe-b",
        "barrels": [{"id": "pipe-b", "name": "26in Match"}],
        "bullet_profiles": [
            {
                "bullet_name": "ELD-M",
                "bullet_weight_gr": "140",
                "jam_length_coal_mm": "71.200",
                "jam_length_cbto_mm": "56.180",
                "optimal_jump_mm": "0.200",
                "measurement_method": "hornady_oal_gauge",
            },
            {
                "bullet_name": "No COAL",
                "bullet_weight_gr": "140",
                "jam_length_cbto_mm": "55.900",
                "measurement_method": "manual",
            },
        ],
    }

    editor_module.RifleProfileEditor._sync_bullet_profiles_to_jump_measurements(
        widget,
        4,
        details,
    )

    assert widget.db.delete_calls == [
        (
            "rifle_bullet_jump_measurements",
            "rifle_id = ? AND measurement_tool = ? AND COALESCE(barrel_id, '') = ?",
            (4, "rifle_profile_editor", "pipe-b"),
        )
    ]
    jump_inserts = [
        payload
        for table, payload in widget.db.insert_calls
        if table == "rifle_bullet_jump_measurements"
    ]
    assert len(jump_inserts) == 1
    assert jump_inserts[0]["barrel_id"] == "pipe-b"
    assert jump_inserts[0]["barrel_name"] == "26in Match"
    assert jump_inserts[0]["bullet_id"] == 7
    assert jump_inserts[0]["jam_coal_mm"] == 71.2
    assert jump_inserts[0]["jam_cbto_mm"] == 56.18
    assert jump_inserts[0]["measurement_tool"] == "rifle_profile_editor"
