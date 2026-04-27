import sqlite3
from pathlib import Path

from src.database.database import Database


def test_database_migration_adds_bc_segments_columns_to_legacy_schema():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/legacy_bc_segments.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE bullets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            caliber TEXT,
            weight_grains REAL,
            bc_g1 REAL,
            bc_g7 REAL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE ammo_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            caliber TEXT,
            bullet_weight REAL,
            powder_charge REAL,
            bc_g1 REAL,
            bc_g7 REAL
        )
        """
    )
    conn.commit()
    conn.close()

    database = Database(str(db_path))
    try:
        bullet_columns = {
            row["name"] for row in database.execute_query("PRAGMA table_info(bullets)")
        }
        ammo_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(ammo_profiles)")
        }

        assert "bc_segments_json" in bullet_columns
        assert "bc_segments_json" in ammo_columns
        assert "component_context_json" in ammo_columns
    finally:
        database.close()


def test_database_migration_adds_powder_model_columns_to_legacy_schema():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/legacy_powder_model.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE powder (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manufacturer TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE powder_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            powder_id INTEGER NOT NULL UNIQUE,
            relative_burn_rate REAL,
            density_gcc REAL
        )
        """
    )
    conn.commit()
    conn.close()

    database = Database(str(db_path))
    try:
        powder_model_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(powder_database)")
        }

        assert "qex_kj_per_kg" in powder_model_columns
        assert "k_ratio" in powder_model_columns
        assert "a0" in powder_model_columns
        assert "z1" in powder_model_columns
        assert "z2" in powder_model_columns
        assert "eta_cm3_per_kg" in powder_model_columns
        assert "pc_kg_m3" in powder_model_columns
        assert "pcd_kg_m3" in powder_model_columns
        assert "validation_status" in powder_model_columns
        assert "usable_for_simulation" in powder_model_columns
        assert "raw_json" in powder_model_columns
    finally:
        database.close()


def test_database_migration_adds_primer_profile_columns_to_legacy_schema():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/legacy_primer_profile.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE primers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manufacturer TEXT,
            type TEXT,
            size TEXT,
            quantity INTEGER DEFAULT 0,
            cost_per_unit REAL,
            notes TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    database = Database(str(db_path))
    try:
        primer_columns = {
            row["name"] for row in database.execute_query("PRAGMA table_info(primers)")
        }

        assert "primer_family" in primer_columns
        assert "product_line" in primer_columns
        assert "part_number" in primer_columns
        assert "source_kind" in primer_columns
        assert "manufacturer_source" in primer_columns
        assert "match_grade" in primer_columns
        assert "magnum" in primer_columns
        assert "ar_variant" in primer_columns
        assert "nominal_diameter_in" in primer_columns
        assert "used_for" in primer_columns
        assert "box_count" in primer_columns
        assert "case_count" in primer_columns
        assert "composition_class" in primer_columns
        assert "non_corrosive" in primer_columns
        assert "lead_free" in primer_columns
        assert "temperature_claim" in primer_columns
        assert "cup_thickness_in" in primer_columns
        assert "cup_hardness_class" in primer_columns
        assert "pressure_tolerance_class" in primer_columns
        assert "ignition_strength_class" in primer_columns
        assert "recommended_pressure_min_psi" in primer_columns
        assert "recommended_pressure_max_psi" in primer_columns
        assert "cold_weather_suitability" in primer_columns
        assert "primer_sign_interpretation" in primer_columns
        assert "evidence_level" in primer_columns
        assert "reference_source" in primer_columns
    finally:
        database.close()


def test_database_seeds_default_primer_profiles_without_inventory_requirement():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/seeded_primer_profiles.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        rows = database.execute_query(
            "SELECT manufacturer, name, quantity, pressure_tolerance_class, product_line, part_number, source_kind FROM primers WHERE manufacturer = ? AND name = ?",
            ("CCI", "450"),
        )

        assert rows
        assert rows[0]["quantity"] == 0
        assert rows[0]["pressure_tolerance_class"] == "high"
        assert rows[0]["product_line"] == "CCI Primers"
        assert rows[0]["part_number"] == "17"
        assert rows[0]["source_kind"] == "manufacturer_published+reference_inferred"
    finally:
        database.close()


def test_database_seeds_default_case_profiles_without_inventory_requirement():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/seeded_case_profiles.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        rows = database.execute_query(
            "SELECT manufacturer, name, caliber, quantity, case_capacity_gr_h2o, trim_length_mm, notes FROM cases WHERE manufacturer = ? AND name = ? AND caliber = ?",
            ("Reference", "Baseline Brass", "6.5 Creedmoor"),
        )

        assert rows
        assert rows[0]["quantity"] == 0
        assert rows[0]["case_capacity_gr_h2o"] == 53.8
        assert rows[0]["trim_length_mm"] == 48.77
        assert "intern kaliberbaseline" in rows[0]["notes"]
    finally:
        database.close()


def test_database_migrates_legacy_cases_schema_before_seeding_defaults():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/legacy_cases_schema.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manufacturer TEXT,
            caliber TEXT NOT NULL
        )
        """
    )
    cur.execute(
        "INSERT INTO cases (name, manufacturer, caliber) VALUES (?, ?, ?)",
        ("Baseline Brass", "Reference", "6.5 Creedmoor"),
    )
    conn.commit()
    conn.close()

    database = Database(str(db_path))
    try:
        case_columns = {
            row["name"] for row in database.execute_query("PRAGMA table_info(cases)")
        }
        rows = database.execute_query(
            "SELECT manufacturer, name, caliber, case_capacity_gr_h2o, trim_length_mm, notes FROM cases WHERE manufacturer = ? AND name = ? AND caliber = ?",
            ("Reference", "Baseline Brass", "6.5 Creedmoor"),
        )

        assert "case_capacity_gr_h2o" in case_columns
        assert "trim_length_mm" in case_columns
        assert rows
        assert rows[0]["case_capacity_gr_h2o"] == 53.8
        assert rows[0]["trim_length_mm"] == 48.77
        assert "intern kaliberbaseline" in rows[0]["notes"]
    finally:
        database.close()


def test_database_creates_canonical_load_development_sessions_table_and_link_column():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/load_development_session_schema.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        session_columns = {
            row["name"]
            for row in database.execute_query(
                "PRAGMA table_info(load_development_sessions)"
            )
        }
        loading_session_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(loading_sessions)")
        }

        assert "session_uid" in session_columns
        assert "lifecycle_stage" in session_columns
        assert "component_selection_json" in session_columns
        assert "recommendation_json" in session_columns
        assert "legacy_loading_session_id" in session_columns
        assert "load_session_id" in loading_session_columns
    finally:
        database.close()


def test_database_creates_downstream_load_session_link_columns():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/downstream_load_session_schema.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        batch_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(batch_projects)")
        }
        batch_session_columns = {
            row["name"]
            for row in database.execute_query(
                "PRAGMA table_info(batch_project_sessions)"
            )
        }
        ladder_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(ladder_tests)")
        }
        result_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(test_results)")
        }
        chrono_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(chronograph_imports)")
        }
        shooting_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(shooting_sessions)")
        }
        pressure_sign_columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(pressure_signs)")
        }

        assert "load_session_id" in batch_columns
        assert "load_session_id" in batch_session_columns
        assert "load_session_id" in ladder_columns
        assert "load_session_id" in result_columns
        assert "load_session_id" in chrono_columns
        assert "load_session_id" in shooting_columns
        assert "batch_id" in pressure_sign_columns
        assert "batch_session_id" in pressure_sign_columns
        assert "rifle_id" in pressure_sign_columns
        assert "barrel_id" in pressure_sign_columns
        assert "barrel_name" in pressure_sign_columns
    finally:
        database.close()


def test_database_creates_seating_depth_profiles_table_and_supports_upsert_lookup():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/seating_depth_profiles.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        columns = {
            row["name"]
            for row in database.execute_query(
                "PRAGMA table_info(seating_depth_profiles)"
            )
        }
        assert "rifle_id" in columns
        assert "barrel_id" in columns
        assert "barrel_name" in columns
        assert "bullet_id" in columns
        assert "component_lot_id" in columns
        assert "preferred_cbto_mm" in columns
        assert "preferred_jump_mm" in columns

        legacy_row_id = database.upsert_seating_depth_profile(
            {
                "rifle_id": 10,
                "bullet_id": 20,
                "component_lot_id": 30,
                "preferred_coal_mm": 71.0,
                "preferred_cbto_mm": 55.9,
                "preferred_jump_mm": 0.30,
                "evidence_level": "legacy",
            }
        )
        assert legacy_row_id

        row_id = database.upsert_seating_depth_profile(
            {
                "rifle_id": 10,
                "barrel_id": "pipe-b",
                "barrel_name": "26in Match",
                "bullet_id": 20,
                "component_lot_id": 30,
                "preferred_coal_mm": 71.2,
                "preferred_cbto_mm": 56.1,
                "preferred_jump_mm": 0.18,
                "evidence_level": "builder_saved",
            }
        )
        assert row_id

        fetched = database.get_seating_depth_profile(10, 20, 30, barrel_id="pipe-b")
        assert fetched is not None
        assert float(fetched["preferred_cbto_mm"]) == 56.1
        assert float(fetched["preferred_jump_mm"]) == 0.18
        assert fetched["barrel_name"] == "26in Match"

        fallback = database.get_seating_depth_profile(10, 20, 30, barrel_id="pipe-c")
        assert fallback is not None
        assert float(fallback["preferred_cbto_mm"]) == 55.9
    finally:
        database.close()


def test_database_can_rank_best_seating_depth_evidence_from_batch_history():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/seating_depth_history.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        lot_id = database.insert(
            "component_lots",
            {
                "component_type": "bullet",
                "component_id": 20,
                "lot_number": "LOT-A",
                "purchase_date": "2026-03-31",
                "quantity_initial": 100,
                "quantity_remaining": 100,
                "is_active": 1,
            },
        )

        batch_id = database.insert(
            "batch_projects",
            {
                "batch_number": "BATCH-TEST-001",
                "batch_name": "65CM seating test",
                "rifle_id": 10,
                "bullet_id": 20,
                "status": "active",
                "charge_weight_grains": 41.5,
                "coal_mm": 71.05,
                "cbto_mm": 56.02,
                "component_snapshot_json": (
                    '{"bullet":{"id":20,"lot_number":"LOT-A"},'
                    '"powder":{"name":"N555"},"primer":{"name":"CCI 450"}}'
                ),
                "analysis_json": "{}",
            },
        )
        database.insert(
            "batch_project_sessions",
            {
                "batch_id": batch_id,
                "session_name": "Verification",
                "session_date": "2026-03-31T12:00:00",
                "session_type": "range",
                "shot_count": 5,
                "group_size_moa": 0.34,
                "analysis_json": '{"stats":{"avg":2812.0,"es":9.0,"sd":4.1}}',
            },
        )

        evidence = database.get_best_seating_depth_evidence(10, 20, lot_id, "LOT-A")

        assert evidence is not None
        assert evidence["matches_selected_lot"] is True
        assert float(evidence["cbto_mm"]) == 56.02
        assert float(evidence["best_group_moa"]) == 0.34
        assert float(evidence["best_es_fps"]) == 9.0
        assert evidence["confidence"] in {"medium", "high"}
    finally:
        database.close()


def test_database_best_seating_evidence_prefers_closer_temperature_and_throat_context():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/seating_depth_context_rank.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        lot_id = database.insert(
            "component_lots",
            {
                "component_type": "bullet",
                "component_id": 20,
                "lot_number": "LOT-A",
                "purchase_date": "2026-03-31",
                "quantity_initial": 100,
                "quantity_remaining": 100,
                "is_active": 1,
            },
        )

        first_batch = database.insert(
            "batch_projects",
            {
                "batch_number": "BATCH-CTX-001",
                "batch_name": "Cold context",
                "rifle_id": 10,
                "bullet_id": 20,
                "status": "active",
                "charge_weight_grains": 41.5,
                "coal_mm": 71.00,
                "cbto_mm": 56.00,
                "component_snapshot_json": '{"bullet":{"id":20,"lot_number":"LOT-A"}}',
                "analysis_json": '{"seating_context":{"temperature_c":5.0,"distance_m":100.0,"throat_erosion_mm":0.02}}',
            },
        )
        database.insert(
            "batch_project_sessions",
            {
                "batch_id": first_batch,
                "session_name": "Cold",
                "session_date": "2026-03-31T10:00:00",
                "session_type": "range",
                "distance_m": 100,
                "temperature_c": 5.0,
                "shot_count": 5,
                "group_size_moa": 0.32,
                "analysis_json": '{"stats":{"avg":2810.0,"es":7.0,"sd":3.2}}',
            },
        )

        second_batch = database.insert(
            "batch_projects",
            {
                "batch_number": "BATCH-CTX-002",
                "batch_name": "Warm context",
                "rifle_id": 10,
                "bullet_id": 20,
                "status": "active",
                "charge_weight_grains": 41.5,
                "coal_mm": 71.04,
                "cbto_mm": 56.06,
                "component_snapshot_json": '{"bullet":{"id":20,"lot_number":"LOT-A"}}',
                "analysis_json": '{"seating_context":{"temperature_c":16.0,"distance_m":100.0,"throat_erosion_mm":0.12}}',
            },
        )
        database.insert(
            "batch_project_sessions",
            {
                "batch_id": second_batch,
                "session_name": "Warm",
                "session_date": "2026-03-31T12:00:00",
                "session_type": "range",
                "distance_m": 100,
                "temperature_c": 16.0,
                "shot_count": 5,
                "group_size_moa": 0.35,
                "analysis_json": '{"stats":{"avg":2813.0,"es":8.0,"sd":3.5},"seating_context":{"throat_erosion_mm":0.12}}',
            },
        )

        evidence = database.get_best_seating_depth_evidence(
            10,
            20,
            lot_id,
            "LOT-A",
            target_temperature_c=15.0,
            target_distance_m=100.0,
            target_throat_erosion_mm=0.11,
            include_ranked=True,
        )

        assert evidence is not None
        assert float(evidence["cbto_mm"]) == 56.06
        assert abs(float(evidence["temperature_delta_c"]) - 1.0) < 1e-6
        assert abs(float(evidence["throat_delta_mm"]) - 0.01) < 1e-6
        assert len(evidence["ranked_candidates"]) >= 2
    finally:
        database.close()


def test_database_creates_cartridge_standards_table():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/cartridge_standards.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        columns = {
            row["name"]
            for row in database.execute_query("PRAGMA table_info(cartridge_standards)")
        }

        assert "caliber_name" in columns
        assert "standard_body" in columns
        assert "max_pressure_bar" in columns
        assert "max_pressure_psi" in columns
        assert "oal_mm" in columns
        assert "case_length_mm" in columns
        assert "case_capacity_ml" in columns
        assert "drawing_pdf_url" in columns
        assert "raw_json" in columns
        assert "user_defined" in columns
    finally:
        database.close()
