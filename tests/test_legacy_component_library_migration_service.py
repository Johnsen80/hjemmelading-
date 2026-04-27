from pathlib import Path

from src.database.database import Database
from src.tools.legacy_component_library_migration_service import (
    migrate_legacy_component_tables_into_library,
)


def test_migrate_legacy_component_tables_into_library_promotes_legacy_rows():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/legacy_component_library_migration.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        database.insert(
            "bullet_data",
            {
                "name": "Hybrid Target",
                "manufacturer": "Berger",
                "diameter": 0.264,
                "weight": 140.0,
                "bc": 0.618,
                "type": "Hybrid",
                "length": 1.43,
                "notes": "Legacy bullet row",
            },
        )
        database.insert(
            "powder_data",
            {
                "name": "N140",
                "manufacturer": "Vihtavuori",
                "type": "Single-base",
                "burn_rate": "Medium",
                "energy_density": 0.93,
                "notes": "Legacy powder row",
            },
        )

        report_first = migrate_legacy_component_tables_into_library(database)
        report_second = migrate_legacy_component_tables_into_library(database)

        bullets = database.execute_query("SELECT * FROM bullets ORDER BY id")
        powders = database.execute_query("SELECT * FROM powder ORDER BY id")
        powder_models = database.execute_query(
            "SELECT * FROM powder_database ORDER BY id"
        )
    finally:
        database.close()

    assert report_first["bullet_library_added"] == 1
    assert report_first["powder_library_added"] == 1
    assert report_first["powder_models_added"] == 1
    assert report_second["bullet_library_added"] == 0
    assert report_second["powder_library_added"] == 0
    assert report_second["bullet_library_updated"] >= 1
    assert report_second["powder_library_updated"] >= 1
    assert report_second["powder_models_updated"] >= 1
    assert len(bullets) == 1
    assert bullets[0]["manufacturer"] == "Berger"
    assert bullets[0]["name"] == "Hybrid Target"
    assert bullets[0]["caliber"] == ".264"
    assert len(powders) == 1
    assert powders[0]["manufacturer"] == "Vihtavuori"
    assert powders[0]["name"] == "N140"
    assert len(powder_models) == 1
    assert int(powder_models[0]["usable_for_simulation"] or 0) == 0
