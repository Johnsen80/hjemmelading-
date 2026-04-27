from pathlib import Path

from src.database.database import Database
from src.tools.load_development_session_service import (
    create_load_development_session,
    get_load_development_session,
    link_legacy_loading_session,
    list_load_development_sessions,
    update_load_development_session,
)


def test_load_development_session_service_creates_and_parses_canonical_session():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_dev_session_service.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        session_id = create_load_development_session(
            database,
            rifle_id=None,
            rifle_name="Test Rifle",
            rifle_caliber="6.5 CM",
            usage_profile_key="langhold",
            usage_profile_name="Langhold/PRS",
            component_selection={"bullet_id": 10, "powder_id": 20},
            intake_snapshot={"source": "unit_test"},
            recommendation={"charge_window_gr": {"min": 41.2, "max": 42.0}},
            evidence_summary={"reference_source_count": 3},
            learning_state={"best_history": {}},
            quantity_target=25,
            recommended_charge_min_gr=41.2,
            recommended_charge_max_gr=42.0,
            next_action="build_initial_test_batches",
            notes="Canonical session seed",
        )

        row = get_load_development_session(database, session_id)
        assert row is not None
        assert row["usage_profile_key"] == "langhold"
        assert row["recommendation_json"]["charge_window_gr"]["min"] == 41.2
        assert row["component_selection_json"]["bullet_id"] == 10
        assert row["learning_state_json"]["schema_version"] == "load_learning_state.v1"
        assert row["learning_state_json"]["best_history"] == {}
        assert row["learning_state_json"]["analysis"]["barrel_context"] == {}

        listed = list_load_development_sessions(database, status="active")
        assert listed
        assert listed[0]["id"] == session_id
    finally:
        database.close()


def test_load_development_session_service_links_legacy_loading_session():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_dev_session_link.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        legacy_session_id = database.insert(
            "loading_sessions",
            {
                "date": "2026-04-06",
                "ammo_profile_id": None,
                "quantity": 20,
                "coal_min": None,
                "coal_max": None,
                "powder_weight_min": 41.0,
                "powder_weight_max": 42.0,
                "time_minutes": None,
                "total_cost": None,
                "notes": "Legacy row",
            },
        )
        session_id = create_load_development_session(
            database,
            rifle_id=None,
            rifle_name="Legacy Link Rifle",
            rifle_caliber="308 Win",
            usage_profile_key="jakt",
            usage_profile_name="Jakt",
            legacy_loading_session_id=legacy_session_id,
        )

        link_legacy_loading_session(
            database,
            legacy_loading_session_id=legacy_session_id,
            load_session_id=session_id,
        )

        legacy_row = database.get_by_id("loading_sessions", legacy_session_id)
        session_row = database.get_by_id("load_development_sessions", session_id)
        assert legacy_row["load_session_id"] == session_id
        assert session_row["legacy_loading_session_id"] == legacy_session_id
    finally:
        database.close()


def test_load_development_session_service_updates_and_merges_component_selection():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_dev_session_update.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        session_id = create_load_development_session(
            database,
            rifle_id=12,
            rifle_name="Update Rifle",
            rifle_caliber="308 Win",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
            component_selection={"bullet_id": 10, "powder_id": 20},
        )

        updated = update_load_development_session(
            database,
            session_id,
            updates={
                "barrel_id": "pipe-a",
                "barrel_name": "24in Proof",
                "ammo_profile_id": 44,
            },
            component_selection_updates={"powder_lot_id": 33, "primer_id": 55},
        )

        assert updated is not None
        assert updated["barrel_id"] == "pipe-a"
        assert updated["ammo_profile_id"] == 44
        assert updated["component_selection_json"]["bullet_id"] == 10
        assert updated["component_selection_json"]["powder_id"] == 20
        assert updated["component_selection_json"]["powder_lot_id"] == 33
        assert updated["component_selection_json"]["primer_id"] == 55
    finally:
        database.close()


def test_load_development_session_service_stores_barrel_configuration_context():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_dev_session_barrel_config.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        session_id = create_load_development_session(
            database,
            rifle_id=3,
            rifle_name="Config Rifle",
            rifle_caliber="300 BLK",
            barrel_id="blk-10",
            barrel_name="10.5in BLK",
            barrel_configuration_id="blk-10-supp",
            barrel_configuration_name="Suppressor On",
            barrel_configuration_snapshot={
                "muzzle_device_type": "suppressor",
                "muzzle_device_weight_g": 420,
            },
            component_lots={"powder_lot_id": 7, "primer_lot_id": 8},
            usage_profile_key="subsonic",
            usage_profile_name="Subsonic",
            subsonic_mode=True,
            session_verdict="promising",
        )

        updated = update_load_development_session(
            database,
            session_id,
            barrel_configuration_snapshot_updates={"mount_type": "qd"},
            component_lots_updates={"bullet_lot_id": 9},
        )

        assert updated is not None
        assert updated["barrel_id"] == "blk-10"
        assert updated["barrel_configuration_id"] == "blk-10-supp"
        assert updated["barrel_configuration_name"] == "Suppressor On"
        assert updated["subsonic_mode"] == 1
        assert updated["session_verdict"] == "promising"
        assert (
            updated["barrel_configuration_snapshot_json"]["muzzle_device_type"]
            == "suppressor"
        )
        assert updated["barrel_configuration_snapshot_json"]["mount_type"] == "qd"
        assert updated["component_lots_json"]["powder_lot_id"] == 7
        assert updated["component_lots_json"]["bullet_lot_id"] == 9
    finally:
        database.close()


def test_load_development_session_service_normalizes_legacy_learning_state_shape():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_dev_session_learning_state.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        session_id = create_load_development_session(
            database,
            rifle_id=None,
            rifle_name="Learning Rifle",
            rifle_caliber="6 Dasher",
            usage_profile_key="precision",
            usage_profile_name="Presisjon",
            learning_state={
                "best_history": {"group_size_moa": 0.39},
                "barrel_context": {"level": "ok", "title": "Known barrel"},
                "node_fit": {"level": "watch", "title": "Retest node"},
                "custom_note": "keep",
            },
        )

        updated = update_load_development_session(
            database,
            session_id,
            learning_state_updates={
                "summary": {"next_focus": "capture_measured_velocity"},
            },
        )

        assert updated is not None
        assert (
            updated["learning_state_json"]["schema_version"] == "load_learning_state.v1"
        )
        assert updated["learning_state_json"]["best_history"]["group_size_moa"] == 0.39
        assert (
            updated["learning_state_json"]["analysis"]["barrel_context"]["level"]
            == "ok"
        )
        assert (
            updated["learning_state_json"]["analysis"]["node_fit"]["title"]
            == "Retest node"
        )
        assert (
            updated["learning_state_json"]["summary"]["next_focus"]
            == "capture_measured_velocity"
        )
        assert updated["learning_state_json"]["custom_note"] == "keep"
    finally:
        database.close()
