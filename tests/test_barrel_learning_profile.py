import json
from pathlib import Path

from src.database.database import Database


def test_get_barrel_learning_profile_initializes_default_record():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/barrel_learning_default.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles",
        {
            "name": "Test Rifle",
            "caliber": ".308 Winchester",
        },
    )

    profile = database.get_barrel_learning_profile(rifle_id, "barrel-1", "Match Pipe")

    assert profile["rifle_id"] == rifle_id
    assert profile["barrel_id"] == "barrel-1"
    assert profile["barrel_name"] == "Match Pipe"
    assert profile["status"] == "insufficient_data"
    assert profile["confidence_label"] == "ingen data ennå"
    assert profile["data_points"] == 0

    rows = database.execute_query(
        "SELECT * FROM barrel_learning_profiles WHERE rifle_id = ? AND barrel_id = ?",
        (rifle_id, "barrel-1"),
    )
    assert len(rows) == 1
    database.close()


def test_upsert_barrel_learning_profile_updates_metrics_and_extra_profile_data():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/barrel_learning_update.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles",
        {
            "name": "Test Rifle",
            "caliber": "6.5 Creedmoor",
        },
    )

    updated = database.upsert_barrel_learning_profile(
        rifle_id,
        "barrel-2",
        {
            "status": "calibrating",
            "confidence_score": 61.0,
            "data_points": 7,
            "chrono_samples": 4,
            "target_samples": 2,
            "temperature_samples": 1,
            "calibration_offset_fps": -18.5,
            "cold_bore_shift_moa": 0.32,
            "drift_flag": "watch",
            "node_robustness_score": 0.74,
        },
        barrel_name="Hunting Pipe",
    )

    assert updated["status"] == "calibrating"
    assert updated["confidence_label"] == "brukbar trygghet"
    assert updated["chrono_samples"] == 4
    assert updated["profile_data"]["node_robustness_score"] == 0.74
    assert updated["drift_flag"] == "watch"
    database.close()


def test_record_barrel_chronograph_observation_uses_active_barrel_and_updates_learning():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/barrel_learning_chrono.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles",
        {
            "name": "Chrono Rifle",
            "caliber": ".223 Remington",
        },
    )
    database.insert(
        "rifle_profile_details",
        {
            "rifle_id": rifle_id,
            "profile_json": '{"active_barrel_id":"pipe-a","barrels":[{"id":"pipe-a","name":"Pipe A"}]}',
        },
    )

    updated = database.record_barrel_chronograph_observation(
        rifle_id,
        None,
        None,
        {
            "session_name": "Series 1",
            "session_date": "2026-03-26",
            "avg_velocity_fps": 2820.0,
            "es_fps": 18.0,
            "sd_fps": 7.2,
            "temperature_f": 59.0,
        },
    )

    assert updated["barrel_id"] == "pipe-a"
    assert updated["barrel_name"] == "Pipe A"
    assert updated["chrono_samples"] == 1
    assert updated["temperature_samples"] == 1
    assert updated["typical_es_fps"] == 18.0
    assert updated["profile_data"]["last_avg_velocity_fps"] == 2820.0
    database.close()


def test_record_barrel_chronograph_observation_tracks_configuration_specific_learning():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/barrel_learning_chrono_config.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles",
        {
            "name": "Config Rifle",
            "caliber": ".308 Winchester",
        },
    )

    database.record_barrel_chronograph_observation(
        rifle_id,
        "pipe-a",
        "Pipe A",
        {
            "session_name": "Bare Series",
            "session_date": "2026-04-09",
            "avg_velocity_fps": 2815.0,
            "es_fps": 14.0,
            "sd_fps": 5.8,
            "temperature_f": 57.0,
        },
        barrel_configuration_id="pipe-a:bare",
        barrel_configuration_name="Bare muzzle",
    )
    updated = database.record_barrel_chronograph_observation(
        rifle_id,
        "pipe-a",
        "Pipe A",
        {
            "session_name": "Suppressed Series",
            "session_date": "2026-04-10",
            "avg_velocity_fps": 2798.0,
            "es_fps": 11.0,
            "sd_fps": 4.9,
            "temperature_f": 61.0,
        },
        barrel_configuration_id="pipe-a:suppressed",
        barrel_configuration_name="Suppressed",
    )

    aggregate = database.get_barrel_learning_profile(rifle_id, "pipe-a", "Pipe A")
    bare_profile = database.get_barrel_learning_profile(
        rifle_id,
        "pipe-a",
        "Pipe A",
        "pipe-a:bare",
        "Bare muzzle",
    )

    assert aggregate["chrono_samples"] == 2
    assert updated["barrel_configuration_id"] == "pipe-a:suppressed"
    assert updated["chrono_samples"] == 1
    assert updated["profile_data"]["last_avg_velocity_fps"] == 2798.0
    assert bare_profile["chrono_samples"] == 1
    assert bare_profile["profile_data"]["last_avg_velocity_fps"] == 2815.0
    database.close()


def test_record_barrel_target_observation_updates_group_learning():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/barrel_learning_target.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles",
        {
            "name": "Target Rifle",
            "caliber": "6mm Creedmoor",
        },
    )

    updated = database.record_barrel_target_observation(
        rifle_id,
        "pipe-b",
        "Pipe B",
        {
            "date": "2026-03-26",
            "distance_meters": 100,
            "best_group_mm": 12.5,
        },
    )

    assert updated["target_samples"] == 1
    assert updated["profile_data"]["typical_group_mm"] == 12.5
    assert updated["profile_data"]["last_target_distance_m"] == 100
    database.close()


def test_record_barrel_target_observation_tracks_configuration_specific_groups():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/barrel_learning_target_config.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles",
        {
            "name": "Target Config Rifle",
            "caliber": "6mm Creedmoor",
        },
    )

    updated = database.record_barrel_target_observation(
        rifle_id,
        "pipe-b",
        "Pipe B",
        {
            "date": "2026-04-09",
            "distance_meters": 100,
            "best_group_mm": 9.8,
        },
        barrel_configuration_id="pipe-b:brake",
        barrel_configuration_name="Muzzle brake",
    )
    aggregate = database.get_barrel_learning_profile(rifle_id, "pipe-b", "Pipe B")

    assert updated["barrel_configuration_id"] == "pipe-b:brake"
    assert updated["target_samples"] == 1
    assert updated["profile_data"]["typical_group_mm"] == 9.8
    assert aggregate["target_samples"] == 1
    database.close()


def test_refresh_case_learning_profile_builds_case_lot_summary():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/case_learning_profile.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    case_id = database.insert(
        "cases",
        {
            "name": "Lapua Lot A",
            "manufacturer": "Lapua",
            "caliber": "6.5 Creedmoor",
            "quantity": 80,
            "times_fired": 4,
            "case_capacity_gr_h2o": 52.4,
            "avg_weight_gr": 171.2,
            "retired_quantity": 5,
        },
    )
    database.insert(
        "case_measurements",
        {
            "case_id": case_id,
            "measurement_date": "2026-03-26",
            "case_weight_gr": 171.8,
            "measurement_type": "fired",
        },
    )
    database.insert(
        "case_firing_log",
        {
            "case_id": case_id,
            "firing_date": "2026-03-26",
            "rounds_fired": 20,
            "pressure_level": "medium",
        },
    )
    database.insert(
        "case_prep_log",
        {
            "case_id": case_id,
            "prep_date": "2026-03-25",
            "trimmed": 1,
        },
    )
    database.insert(
        "case_annealing_log",
        {
            "case_id": case_id,
            "annealing_date": "2026-03-20",
            "method": "AMP Annealer",
        },
    )

    profile = database.refresh_case_learning_profile(case_id)

    assert profile["case_id"] == case_id
    assert profile["status"] == "learning"
    assert profile["h2o_samples"] == 1
    assert profile["firing_events"] == 1
    assert profile["prep_events"] == 1
    assert profile["anneal_events"] == 1
    assert profile["avg_case_capacity_h2o"] == 52.4
    assert profile["profile_data"]["available_quantity"] == 80
    assert profile["profile_data"]["retired_quantity"] == 5
    database.close()


def test_refresh_powder_lot_learning_profile_builds_velocity_and_drift_summary():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/powder_learning_profile.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles",
        {
            "name": "Powder Rifle",
            "caliber": ".308 Winchester",
        },
    )
    powder_id = database.insert(
        "powder",
        {
            "name": "N550",
            "manufacturer": "Vihtavuori",
        },
    )
    bullet_id = database.insert(
        "bullets",
        {
            "name": "175 SMK",
            "manufacturer": "Sierra",
            "caliber": ".308",
            "weight_grains": 175.0,
        },
    )
    primer_id = database.insert(
        "primers",
        {
            "name": "BR2",
            "manufacturer": "CCI",
        },
    )
    bullet_lot_id = database.insert(
        "bullet_lots",
        {
            "bullet_id": bullet_id,
            "lot_number": "B-100",
            "purchase_date": "2026-03-01",
            "quantity_purchased": 100,
            "quantity_remaining": 80,
        },
    )
    brass_batch_id = database.insert(
        "brass_batches",
        {
            "batch_name": "Lapua Batch",
            "lot_number": "L-55",
        },
    )
    component_lot_id = database.insert(
        "component_lots",
        {
            "component_type": "powder",
            "component_id": powder_id,
            "lot_number": "P-LOT-01",
            "purchase_date": "2026-03-10",
            "quantity_initial": 1000.0,
            "quantity_remaining": 700.0,
            "is_active": 1,
            "notes": "Test lot",
        },
    )
    database.insert(
        "loaded_ammo_batches",
        {
            "batch_number": "LAB-001",
            "batch_name": "Node Test 1",
            "rifle_id": rifle_id,
            "loaded_date": "2026-03-20",
            "brass_batch_id": brass_batch_id,
            "bullet_lot_id": bullet_lot_id,
            "powder_id": powder_id,
            "powder_lot_number": "P-LOT-01",
            "primer_id": primer_id,
            "charge_weight_grains": 43.5,
            "coal_mm": 71.2,
            "quantity_loaded": 20,
            "quantity_remaining": 8,
            "predicted_velocity_fps": 2710.0,
            "actual_velocity_avg_fps": 2738.0,
            "actual_es_fps": 17.0,
            "actual_best_moa": 0.72,
            "loading_temperature_c": 8.0,
            "intended_use": "hunting",
        },
    )
    database.insert(
        "loaded_ammo_batches",
        {
            "batch_number": "LAB-002",
            "batch_name": "Node Test 2",
            "rifle_id": rifle_id,
            "loaded_date": "2026-03-24",
            "brass_batch_id": brass_batch_id,
            "bullet_lot_id": bullet_lot_id,
            "powder_id": powder_id,
            "powder_lot_number": "P-LOT-01",
            "primer_id": primer_id,
            "charge_weight_grains": 43.7,
            "coal_mm": 71.2,
            "quantity_loaded": 20,
            "quantity_remaining": 5,
            "predicted_velocity_fps": 2720.0,
            "actual_velocity_avg_fps": 2752.0,
            "actual_es_fps": 16.0,
            "actual_best_moa": 0.64,
            "loading_temperature_c": 18.0,
            "intended_use": "hunting",
            "pressure_signs_observed": 1,
        },
    )
    database.insert(
        "chronograph_sessions",
        {
            "device_type": "Garmin Xero",
            "session_name": "Lot verification",
            "session_date": "2026-03-25",
            "avg_velocity_fps": 2748.0,
            "es_fps": 14.0,
            "sd_fps": 5.5,
            "min_velocity_fps": 2740.0,
            "max_velocity_fps": 2754.0,
            "shot_count": 5,
            "temperature_f": 64.4,
            "import_meta_json": json.dumps(
                {
                    "batch_context": {
                        "batch_id": 1,
                        "powder_id": powder_id,
                        "powder_lot_number": "P-LOT-01",
                        "powder_component_lot_id": component_lot_id,
                    }
                }
            ),
        },
    )

    profile = database.refresh_powder_lot_learning_profile(component_lot_id)

    assert profile["component_lot_id"] == component_lot_id
    assert profile["status"] == "learning"
    assert profile["batch_samples"] == 2
    assert profile["chrono_samples"] == 3
    assert profile["temperature_samples"] == 2
    assert profile["avg_velocity_fps"] == 2746.0
    assert profile["velocity_offset_fps"] == 30.0
    assert profile["typical_es_fps"] == 15.7
    assert profile["best_recorded_moa"] == 0.64
    assert profile["pressure_watch_count"] == 1
    assert profile["drift_flag"] == "pressure_watch"
    assert profile["profile_data"]["chrono_import_samples"] == 1
    assert profile["profile_data"]["intended_use_counts"]["hunting"] == 2
    database.close()


def test_compare_powder_lots_marks_noticeable_shift_and_retest_guidance():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/powder_lot_compare.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert("rifles", {"name": "Compare Rifle", "caliber": ".308"})
    powder_id = database.insert("powder", {"name": "N150", "manufacturer": "VV"})
    bullet_id = database.insert(
        "bullets",
        {
            "name": "175 SMK",
            "manufacturer": "Sierra",
            "caliber": ".308",
            "weight_grains": 175.0,
        },
    )
    primer_id = database.insert("primers", {"name": "210M", "manufacturer": "Fed"})
    bullet_lot_id = database.insert(
        "bullet_lots",
        {
            "bullet_id": bullet_id,
            "lot_number": "B-200",
            "purchase_date": "2026-03-01",
            "quantity_purchased": 100,
            "quantity_remaining": 90,
        },
    )
    brass_batch_id = database.insert(
        "brass_batches",
        {"batch_name": "Lapua Compare", "lot_number": "L-200"},
    )
    database.insert(
        "component_lots",
        {
            "component_type": "powder",
            "component_id": powder_id,
            "lot_number": "OLD-LOT",
            "purchase_date": "2026-02-01",
            "quantity_initial": 1000.0,
            "quantity_remaining": 200.0,
            "is_active": 0,
            "notes": "",
        },
    )
    new_lot_id = database.insert(
        "component_lots",
        {
            "component_type": "powder",
            "component_id": powder_id,
            "lot_number": "NEW-LOT",
            "purchase_date": "2026-03-15",
            "quantity_initial": 1000.0,
            "quantity_remaining": 900.0,
            "is_active": 1,
            "notes": "",
        },
    )

    for batch_number, lot_number, actual_velocity, predicted_velocity, es in (
        ("LOT-OLD-1", "OLD-LOT", 2712.0, 2710.0, 12.0),
        ("LOT-OLD-2", "OLD-LOT", 2716.0, 2715.0, 13.0),
        ("LOT-NEW-1", "NEW-LOT", 2738.0, 2710.0, 15.0),
        ("LOT-NEW-2", "NEW-LOT", 2742.0, 2712.0, 16.0),
    ):
        database.insert(
            "loaded_ammo_batches",
            {
                "batch_number": batch_number,
                "batch_name": batch_number,
                "rifle_id": rifle_id,
                "loaded_date": "2026-03-20",
                "brass_batch_id": brass_batch_id,
                "bullet_lot_id": bullet_lot_id,
                "powder_id": powder_id,
                "powder_lot_number": lot_number,
                "primer_id": primer_id,
                "charge_weight_grains": 44.0,
                "coal_mm": 71.0,
                "quantity_loaded": 20,
                "quantity_remaining": 10,
                "predicted_velocity_fps": predicted_velocity,
                "actual_velocity_avg_fps": actual_velocity,
                "actual_es_fps": es,
            },
        )

    comparison = database.compare_powder_lots(powder_id, new_lot_id)

    assert comparison["status"] == "retest_required"
    assert comparison["severity"] == "high"
    assert comparison["previous_lot_number"] == "OLD-LOT"
    assert comparison["avg_velocity_shift_fps"] == 26.0
    assert comparison["velocity_offset_shift_fps"] == 27.5
    assert comparison["suggested_charge_adjustment_grains"] == -0.2
    assert comparison["verification_plan"]["shots"] == 5
    assert comparison["verification_plan"]["start_delta_grains"] == -0.2
    assert "Start konservativt" in comparison["recommended_action"]
    database.close()


def test_refresh_bullet_lot_learning_profile_uses_qc_and_batch_results():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/bullet_lot_learning.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles", {"name": "Bullet Rifle", "caliber": "6.5 Creedmoor"}
    )
    powder_id = database.insert("powder", {"name": "N160", "manufacturer": "VV"})
    primer_id = database.insert("primers", {"name": "BR4", "manufacturer": "CCI"})
    bullet_id = database.insert(
        "bullets",
        {
            "name": "140 Hybrid",
            "manufacturer": "Berger",
            "caliber": "6.5",
            "weight_grains": 140.0,
        },
    )
    bullet_lot_id = database.insert(
        "bullet_lots",
        {
            "bullet_id": bullet_id,
            "lot_number": "BL-140A",
            "purchase_date": "2026-03-01",
            "quantity_purchased": 500,
            "quantity_remaining": 420,
            "qc_performed": 1,
            "quality_rating": "excellent",
        },
    )
    brass_batch_id = database.insert(
        "brass_batches",
        {"batch_name": "Alpha Batch", "lot_number": "AB-1"},
    )
    for bullet_number, weight, bto, passed in (
        (1, 140.1, 0.6120, 1),
        (2, 140.0, 0.6118, 1),
        (3, 140.2, 0.6121, 1),
        (4, 139.9, 0.6117, 1),
        (5, 140.3, 0.6125, 0),
    ):
        database.insert(
            "bullet_qc_measurements",
            {
                "lot_id": bullet_lot_id,
                "measurement_date": "2026-03-02",
                "bullet_number": bullet_number,
                "weight_grains": weight,
                "length_bto_inches": bto,
                "passed_qc": passed,
            },
        )

    for batch_number, actual_moa_avg, actual_best_moa in (
        ("BLT-1", 0.72, 0.58),
        ("BLT-2", 0.68, 0.54),
    ):
        database.insert(
            "loaded_ammo_batches",
            {
                "batch_number": batch_number,
                "batch_name": batch_number,
                "rifle_id": rifle_id,
                "loaded_date": "2026-03-20",
                "brass_batch_id": brass_batch_id,
                "bullet_lot_id": bullet_lot_id,
                "powder_id": powder_id,
                "powder_lot_number": "P-1",
                "primer_id": primer_id,
                "charge_weight_grains": 41.5,
                "coal_mm": 71.0,
                "quantity_loaded": 20,
                "quantity_remaining": 10,
                "actual_moa_avg": actual_moa_avg,
                "actual_best_moa": actual_best_moa,
            },
        )

    profile = database.refresh_bullet_lot_learning_profile(bullet_lot_id)

    assert profile["bullet_lot_id"] == bullet_lot_id
    assert profile["status"] == "learning"
    assert profile["qc_samples"] == 5
    assert profile["batch_samples"] == 2
    assert profile["qc_pass_rate_percent"] == 80.0
    assert profile["avg_weight_grains"] == 140.1
    assert profile["best_recorded_moa"] == 0.54
    assert profile["typical_group_moa"] == 0.7
    assert profile["profile_data"]["quality_rating"] == "excellent"
    database.close()


def test_compare_bullet_lots_marks_new_lot_for_verification():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/bullet_lot_compare.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert(
        "rifles", {"name": "Bullet Compare Rifle", "caliber": ".308"}
    )
    powder_id = database.insert("powder", {"name": "N150", "manufacturer": "VV"})
    primer_id = database.insert("primers", {"name": "210M", "manufacturer": "Fed"})
    bullet_id = database.insert(
        "bullets",
        {
            "name": "175 SMK",
            "manufacturer": "Sierra",
            "caliber": ".308",
            "weight_grains": 175.0,
        },
    )
    old_lot_id = database.insert(
        "bullet_lots",
        {
            "bullet_id": bullet_id,
            "lot_number": "OLD-B",
            "purchase_date": "2026-02-01",
            "quantity_purchased": 200,
            "quantity_remaining": 100,
            "qc_performed": 1,
        },
    )
    new_lot_id = database.insert(
        "bullet_lots",
        {
            "bullet_id": bullet_id,
            "lot_number": "NEW-B",
            "purchase_date": "2026-03-15",
            "quantity_purchased": 200,
            "quantity_remaining": 180,
            "qc_performed": 1,
        },
    )
    brass_batch_id = database.insert(
        "brass_batches",
        {"batch_name": "Bullet Compare Batch", "lot_number": "BC-1"},
    )

    for lot_id, measurements in (
        (old_lot_id, [(175.0, 0.6118, 1), (175.1, 0.6119, 1), (175.0, 0.6117, 1)]),
        (new_lot_id, [(174.8, 0.6130, 1), (175.3, 0.6142, 1), (175.4, 0.6145, 0)]),
    ):
        for idx, (weight, bto, passed) in enumerate(measurements, start=1):
            database.insert(
                "bullet_qc_measurements",
                {
                    "lot_id": lot_id,
                    "measurement_date": "2026-03-10",
                    "bullet_number": idx,
                    "weight_grains": weight,
                    "length_bto_inches": bto,
                    "passed_qc": passed,
                },
            )

    for batch_number, bullet_lot_id, actual_moa_avg, actual_best_moa in (
        ("OLD-B-1", old_lot_id, 0.55, 0.42),
        ("NEW-B-1", new_lot_id, 0.92, 0.80),
    ):
        database.insert(
            "loaded_ammo_batches",
            {
                "batch_number": batch_number,
                "batch_name": batch_number,
                "rifle_id": rifle_id,
                "loaded_date": "2026-03-20",
                "brass_batch_id": brass_batch_id,
                "bullet_lot_id": bullet_lot_id,
                "powder_id": powder_id,
                "powder_lot_number": "P-1",
                "primer_id": primer_id,
                "charge_weight_grains": 44.0,
                "coal_mm": 71.0,
                "quantity_loaded": 20,
                "quantity_remaining": 10,
                "actual_moa_avg": actual_moa_avg,
                "actual_best_moa": actual_best_moa,
            },
        )

    comparison = database.compare_bullet_lots(bullet_id, new_lot_id)

    assert comparison["status"] == "retest_required"
    assert comparison["severity"] == "high"
    assert comparison["previous_lot_number"] == "OLD-B"
    assert comparison["group_shift_moa"] == 0.37
    assert comparison["verification_plan"]["shots"] == 5
    assert "verifiseringsserie" in comparison["recommended_action"].lower()
    database.close()


def test_compare_primer_lots_marks_ignition_shift_and_control_series():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/primer_lot_compare.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    rifle_id = database.insert("rifles", {"name": "Primer Rifle", "caliber": ".308"})
    powder_id = database.insert("powder", {"name": "N550", "manufacturer": "VV"})
    bullet_id = database.insert(
        "bullets",
        {
            "name": "175 SMK",
            "manufacturer": "Sierra",
            "caliber": ".308",
            "weight_grains": 175.0,
        },
    )
    primer_id = database.insert("primers", {"name": "210M", "manufacturer": "Fed"})
    bullet_lot_id = database.insert(
        "bullet_lots",
        {
            "bullet_id": bullet_id,
            "lot_number": "B-300",
            "purchase_date": "2026-03-01",
            "quantity_purchased": 100,
            "quantity_remaining": 90,
        },
    )
    brass_batch_id = database.insert(
        "brass_batches",
        {"batch_name": "Lapua Primer", "lot_number": "L-300"},
    )
    database.insert(
        "component_lots",
        {
            "component_type": "primers",
            "component_id": primer_id,
            "lot_number": "OLD-PRIMER",
            "purchase_date": "2026-02-01",
            "quantity_initial": 1000.0,
            "quantity_remaining": 600.0,
            "is_active": 0,
        },
    )
    current_lot_id = database.insert(
        "component_lots",
        {
            "component_type": "primers",
            "component_id": primer_id,
            "lot_number": "NEW-PRIMER",
            "purchase_date": "2026-03-15",
            "quantity_initial": 1000.0,
            "quantity_remaining": 800.0,
            "is_active": 1,
        },
    )

    for batch_number, primer_lot_number, velocity, es_fps, sd_fps, best_moa in (
        ("PR-OLD-1", "OLD-PRIMER", 2715.0, 11.0, 4.2, 0.68),
        ("PR-OLD-2", "OLD-PRIMER", 2718.0, 12.0, 4.5, 0.64),
        ("PR-NEW-1", "NEW-PRIMER", 2728.0, 20.0, 8.1, 0.82),
        ("PR-NEW-2", "NEW-PRIMER", 2730.0, 22.0, 8.8, 0.88),
    ):
        database.insert(
            "loaded_ammo_batches",
            {
                "batch_number": batch_number,
                "batch_name": batch_number,
                "rifle_id": rifle_id,
                "loaded_date": "2026-03-20",
                "brass_batch_id": brass_batch_id,
                "bullet_lot_id": bullet_lot_id,
                "powder_id": powder_id,
                "powder_lot_number": "P-LOT-01",
                "primer_id": primer_id,
                "primer_lot_number": primer_lot_number,
                "charge_weight_grains": 43.4,
                "coal_mm": 71.2,
                "quantity_loaded": 20,
                "quantity_remaining": 10,
                "actual_velocity_avg_fps": velocity,
                "actual_es_fps": es_fps,
                "actual_sd_fps": sd_fps,
                "actual_best_moa": best_moa,
            },
        )

    comparison = database.compare_primer_lots(primer_id, current_lot_id)

    assert comparison["status"] == "retest_required"
    assert comparison["severity"] == "high"
    assert comparison["typical_es_shift_fps"] == 9.5
    assert comparison["typical_sd_shift_fps"] == 4.1
    assert comparison["verification_plan"]["shots"] == 5
    assert "ES/SD" in comparison["verification_plan"]["focus"]
    database.close()
