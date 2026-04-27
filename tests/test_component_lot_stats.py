from pathlib import Path

from src.database.database import Database


def test_component_lot_stats_schema_and_rollup():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/component_lot_stats.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        lot_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(component_lots)")
        }
        assert "supplier" in lot_columns
        assert "unit_cost" in lot_columns
        assert "source" in lot_columns

        stats_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(component_lot_stats)")
        }
        assert "weight_avg_grains" in stats_columns
        assert "length_stddev_mm" in stats_columns
        assert "diameter_avg_mm" in stats_columns
        assert "thickness_avg_mm" in stats_columns

        lot_id = database.create_component_lot(
            component_type="bullet",
            component_id=1,
            lot_number="LOT-001",
            quantity_initial=250,
            supplier="Test Supplier",
            source="seed_import",
        )
        session_id = database.create_component_measurement_session(
            lot_id,
            measured_by="tester",
            sample_size=3,
        )
        database.add_component_measurement_value(
            session_id,
            item_index=1,
            weight_grains=167.9,
            length_mm=31.10,
            diameter_mm=7.82,
            thickness_mm=0.40,
        )
        database.add_component_measurement_value(
            session_id,
            item_index=2,
            weight_grains=168.1,
            length_mm=31.20,
            diameter_mm=7.83,
            thickness_mm=0.41,
        )
        database.add_component_measurement_value(
            session_id,
            item_index=3,
            weight_grains=168.0,
            length_mm=31.15,
            diameter_mm=7.81,
            thickness_mm=0.39,
        )

        stats = database.get_component_lot_stats(lot_id)
        assert stats is not None
        assert stats["sample_count"] == 3
        assert stats["weight_avg_grains"] == 168.0
        assert stats["weight_min_grains"] == 167.9
        assert stats["weight_max_grains"] == 168.1
        assert stats["length_avg_mm"] == 31.15
        assert stats["diameter_avg_mm"] == 7.82
        assert stats["thickness_avg_mm"] == 0.4
        assert stats["weight_stddev_grains"] is not None
        assert stats["length_stddev_mm"] is not None
    finally:
        database.close()
