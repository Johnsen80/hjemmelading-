from pathlib import Path

from src.database.batch_manager import (
    add_batch_session,
    create_batch_project,
    get_batch_project,
    get_batch_sessions,
)
from src.database.database import Database


def test_batch_manager_stores_barrel_configuration_context():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/batch_manager_barrel_config.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        rifle_id = database.insert(
            "rifles",
            {
                "name": "Batch Rifle",
                "caliber": "308 Win",
            },
        )

        batch_result = create_batch_project(
            database,
            "Config Batch",
            rifle_id,
            barrel_id="308-main",
            barrel_name="24in Main",
            barrel_configuration_id="308-main-brake",
            barrel_configuration_name="Brake",
            usage_profile_key="precision",
            subsonic_mode=False,
            barrel_configuration_snapshot={
                "muzzle_device_type": "brake",
                "muzzle_device_weight_g": 110,
            },
            analysis_json={"confidence": "medium"},
        )

        batch_id = batch_result["batch_id"]
        batch = get_batch_project(database, batch_id)
        assert batch is not None
        assert batch["barrel_id"] == "308-main"
        assert batch["barrel_configuration_id"] == "308-main-brake"
        assert batch["usage_profile_key"] == "precision"

        add_batch_session(
            database,
            batch_id,
            rifle_id=rifle_id,
            barrel_id="308-main",
            barrel_name="24in Main",
            barrel_configuration_id="308-main-brake",
            barrel_configuration_name="Brake",
            suppressor_used=False,
            muzzle_device_type="brake",
            function_status="normal",
            tester_verdict="promising",
            primer_observation_json={"flattening": "none"},
            chronograph_summary_json={"avg_fps": 2712.4, "count": 10},
        )

        sessions = get_batch_sessions(database, batch_id)
        assert len(sessions) == 1
        assert sessions[0]["barrel_id"] == "308-main"
        assert sessions[0]["barrel_configuration_id"] == "308-main-brake"
        assert sessions[0]["muzzle_device_type"] == "brake"
        assert sessions[0]["function_status"] == "normal"
        assert sessions[0]["tester_verdict"] == "promising"
    finally:
        database.close()
