from pathlib import Path

from src.database.database import Database
from src.modules import component_database as component_module


def test_build_bullet_library_rows_and_snapshot_include_owned_lot_stats():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/component_bullet_library.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        bullet_id = database.insert(
            "bullets",
            {
                "name": "ELD-M",
                "manufacturer": "Hornady",
                "caliber": "6.5mm",
                "weight_grains": 140.0,
                "length_mm": 34.8,
                "diameter_mm": 6.71,
                "bc_g7": 0.315,
                "bullet_type": "Match",
                "quantity": 400,
                "source": "verified_seed",
            },
        )
        lot_id = database.create_component_lot(
            "bullet",
            bullet_id,
            "LOT-140A",
            250,
            storage_location="Hylle A",
        )
        session_id = database.create_component_measurement_session(
            lot_id,
            sample_size=3,
            notes="Kontrollmåling",
        )
        database.add_component_measurement_value(
            session_id, 1, weight_grains=140.1, length_mm=34.81
        )
        database.add_component_measurement_value(
            session_id, 2, weight_grains=139.9, length_mm=34.79
        )
        database.add_component_measurement_value(
            session_id, 3, weight_grains=140.0, length_mm=34.80
        )

        rows = component_module.build_bullet_library_rows(database)
        snapshot = component_module.build_bullet_detail_snapshot(database, bullet_id)
        summary = component_module.format_bullet_detail_summary(snapshot)
    finally:
        database.close()

    assert len(rows) == 1
    assert rows[0]["lot_count"] == 1
    assert rows[0]["lot_quantity_remaining"] == 250

    assert snapshot["bullet"]["name"] == "ELD-M"
    assert len(snapshot["lots"]) == 1
    assert snapshot["lots"][0]["lot_number"] == "LOT-140A"
    assert snapshot["lots"][0]["stats"]["sample_count"] == 3
    assert snapshot["lots"][0]["stats"]["weight_avg_grains"] == 140.0
    assert "Your Lots: 1" in summary
    assert "Measured Lots: 1" in summary


def test_build_primer_library_rows_and_snapshot_include_profile_and_lot_learning():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/component_primer_library.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        primer_id = database.insert(
            "primers",
            {
                "name": "205M",
                "manufacturer": "Federal",
                "type": "Small Rifle Match",
                "size": "small rifle",
                "product_line": "Gold Medal",
                "part_number": "GM205M",
                "pressure_tolerance_class": "high",
                "match_grade": 1,
                "source_kind": "manufacturer_published+reference_inferred",
                "quantity": 0,
            },
        )
        lot_id = database.create_component_lot(
            "primers",
            primer_id,
            "FED-205M-A",
            900,
            storage_location="Hylle P",
        )
        database.upsert_component_lot_learning_profile(
            lot_id,
            {
                "status": "learning",
                "typical_es_fps": 11.0,
                "notes": "Stabil tenning",
                "typical_sd_fps": 4.2,
            },
        )

        rows = component_module.build_primer_library_rows(database)
        snapshot = component_module.build_primer_detail_snapshot(database, primer_id)
        summary = component_module.format_primer_detail_summary(snapshot)
    finally:
        database.close()

    assert len(rows) >= 1
    primer_row = next(row for row in rows if row["id"] == primer_id)
    assert primer_row["lot_count"] == 1
    assert primer_row["lot_quantity_remaining"] == 900

    assert snapshot["primer"]["name"] == "205M"
    assert snapshot["primer"]["product_line"] == "Gold Medal"
    assert len(snapshot["lots"]) == 1
    assert snapshot["lots"][0]["lot_number"] == "FED-205M-A"
    assert snapshot["lots"][0]["learning"]["typical_es_fps"] == 11.0
    assert snapshot["lots"][0]["learning"]["typical_sd_fps"] == 4.2
    assert "Gold Medal" in summary
    assert "Data Source: manufacturer_published+reference_inferred" in summary
    assert "Learned Lots: 1" in summary


def test_build_powder_library_rows_and_snapshot_include_lot_learning():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/component_powder_library.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        powder_id = database.insert(
            "powder",
            {
                "name": "N540",
                "manufacturer": "Vihtavuori",
                "type": "Rifle",
                "burn_rate": "Medium",
                "density": 0.95,
                "notes": "Seed powder",
            },
        )
        lot_id = database.create_component_lot(
            "powder",
            powder_id,
            "N540-24A",
            750,
            storage_location="Hylle K",
        )
        database.upsert_component_lot_learning_profile(
            lot_id,
            {
                "status": "learning",
                "avg_velocity_fps": 2812.0,
                "velocity_offset_fps": 14.0,
                "typical_es_fps": 9.5,
                "notes": "Stabil fart",
            },
        )

        rows = component_module.build_powder_library_rows(database)
        snapshot = component_module.build_powder_detail_snapshot(database, powder_id)
        summary = component_module.format_powder_detail_summary(snapshot)
    finally:
        database.close()

    assert len(rows) >= 1
    powder_row = next(row for row in rows if row["id"] == powder_id)
    assert powder_row["lot_count"] == 1
    assert powder_row["lot_quantity_remaining"] == 750

    assert snapshot["powder"]["name"] == "N540"
    assert len(snapshot["lots"]) == 1
    assert snapshot["lots"][0]["lot_number"] == "N540-24A"
    assert snapshot["lots"][0]["learning"]["avg_velocity_fps"] == 2812.0
    assert snapshot["lots"][0]["learning"]["typical_es_fps"] == 9.5
    assert "Vihtavuori" in summary
    assert "Your Lots: 1" in summary
    assert "Learned Lots: 1" in summary
