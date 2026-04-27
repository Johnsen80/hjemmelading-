from pathlib import Path

from src.database.database import Database
from src.tools.gordon_library_import_service import (
    import_gordon_snapshots_into_component_library,
)
from src.tools.gordon_reference_snapshot_service import import_gordon_readable_snapshots


def test_import_gordon_snapshots_into_component_library_copies_into_local_tables():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/gordon_library_import.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        import_gordon_readable_snapshots(
            database,
            Path(
                "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tmp/gordon_extract_recheck/gordon_extracted_projectiles_raw.csv"
            ),
            Path(
                "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tmp/gordon_extract_recheck/gordon_extracted_propellants_raw.csv"
            ),
            Path(
                "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tmp/gordon_extract_recheck/gordon_extracted_calibers_raw.csv"
            ),
        )

        report = import_gordon_snapshots_into_component_library(database)

        bullets = database.execute_query(
            "SELECT * FROM bullets WHERE source = 'gordon_import' ORDER BY id"
        )
        powders = database.execute_query(
            "SELECT * FROM powder WHERE source = 'gordon_import' ORDER BY id"
        )
        powder_models = database.execute_query(
            "SELECT * FROM powder_database ORDER BY powder_id"
        )
    finally:
        database.close()

    assert report["bullet_library_added"] >= 1
    assert report["powder_library_added"] >= 1
    assert report["powder_models_added"] >= 1
    assert report["powder_models_usable_for_simulation"] >= 1
    assert any(
        row["manufacturer"] == "Hornady" and row["name"] == "FMJ" for row in bullets
    )
    assert any(
        row["manufacturer"] == "Vihtavuori" and row["name"] == "N540" for row in powders
    )
    assert any(row["source_kind"] == "gordon_readable_snapshot" for row in bullets)
    assert any(
        row["external_ref"].startswith("gordon_readable|powder|") for row in powders
    )
    assert any(int(row["usable_for_simulation"] or 0) == 1 for row in powder_models)
    hornady_bullet = next(row for row in bullets if row["manufacturer"] == "Hornady")
    vihtavuori_powder = next(
        row for row in powders if row["manufacturer"] == "Vihtavuori"
    )
    assert hornady_bullet["profile_json"]
    assert hornady_bullet["raw_json"]
    assert vihtavuori_powder["profile_json"]
    assert vihtavuori_powder["raw_json"]
    assert "imageUuid" not in (vihtavuori_powder["profile_json"] or "")
    assert "imageUuid" not in (vihtavuori_powder["raw_json"] or "")
    powder_model = next(
        row for row in powder_models if int(row["usable_for_simulation"] or 0) == 1
    )
    assert "imageUuid" not in (powder_model["raw_json"] or "")


def test_import_gordon_snapshots_into_component_library_is_idempotent():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/gordon_library_import_idempotent.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        import_gordon_readable_snapshots(
            database,
            Path(
                "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tmp/gordon_extract_recheck/gordon_extracted_projectiles_raw.csv"
            ),
            Path(
                "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tmp/gordon_extract_recheck/gordon_extracted_propellants_raw.csv"
            ),
        )

        first = import_gordon_snapshots_into_component_library(database)
        second = import_gordon_snapshots_into_component_library(database)

        bullet_count = database.execute_query("SELECT COUNT(*) AS count FROM bullets")[
            0
        ]["count"]
        powder_count = database.execute_query("SELECT COUNT(*) AS count FROM powder")[
            0
        ]["count"]
        powder_model_count = database.execute_query(
            "SELECT COUNT(*) AS count FROM powder_database"
        )[0]["count"]
    finally:
        database.close()

    assert first["bullet_library_added"] >= 1
    assert first["powder_library_added"] >= 1
    assert second["bullet_library_added"] == 0
    assert second["powder_library_added"] == 0
    assert second["bullet_library_updated"] >= 1
    assert second["powder_library_updated"] >= 1
    assert second["powder_models_updated"] >= 1
    assert bullet_count >= first["bullet_library_added"]
    assert powder_count >= first["powder_library_added"]
    assert powder_model_count >= first["powder_models_added"]
