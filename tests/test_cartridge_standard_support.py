from pathlib import Path

from src.database.database import Database
from src.utils.cartridge_standard_support import (
    build_cartridge_standard_audit,
    compare_chamber_to_cartridge_standard,
    find_best_cartridge_standard,
    get_max_pressure_psi_for_caliber,
)
from src.utils.pressure_calculator import PressureCalculator


def test_cartridge_standard_support_prefers_named_standard_and_alt_name_match():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/cartridge_standard_support_match.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        database.upsert_cartridge_standard(
            {
                "caliber_name": "6.5 Creedmoor",
                "alt_name": "6,5 Creedmoor",
                "standard_body": "CIP",
                "max_pressure_psi": 63100.0,
                "case_capacity_ml": 3.40,
            }
        )
        database.upsert_cartridge_standard(
            {
                "caliber_name": "6.5 Creedmoor",
                "standard_body": "SAAMI",
                "max_pressure_psi": 62000.0,
                "case_capacity_ml": 3.35,
            }
        )

        preferred = find_best_cartridge_standard(database, "6.5 Creedmoor")
        alias_match = find_best_cartridge_standard(database, "6,5 Creedmoor")

        assert preferred is not None
        assert preferred["standard_body"] == "SAAMI"
        assert float(preferred["max_pressure_psi"]) == 62000.0
        assert alias_match is not None
        assert alias_match["standard_body"] == "CIP"
    finally:
        database.close()


def test_pressure_calculator_uses_cartridge_standards_before_fallback_limits():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/cartridge_standard_support_pressure.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        database.upsert_cartridge_standard(
            {
                "caliber_name": "Custom Alpha",
                "standard_body": "CIP",
                "max_pressure_bar": 4100.0,
            }
        )

        pressure = PressureCalculator(database).get_saami_max("Custom Alpha")

        assert pressure == int(round(4100.0 * 14.5037738))
        assert (
            get_max_pressure_psi_for_caliber(database, "Custom Alpha")
            == 4100.0 * 14.5037738
        )
    finally:
        database.close()


def test_cartridge_standard_audit_highlights_missing_case_capacity_and_drawings():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/cartridge_standard_support_audit.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        database.upsert_cartridge_standard(
            {
                "caliber_name": ".308 Winchester",
                "standard_body": "SAAMI",
                "max_pressure_psi": 62000.0,
                "oal_mm": 71.12,
                "case_length_mm": 51.18,
                "bullet_diameter_mm": 7.82,
            }
        )

        audit = build_cartridge_standard_audit(database)

        assert audit["counts"]["total"] >= 1
        assert audit["counts"]["with_pressure"] >= 1
        assert audit["counts"]["with_case_capacity"] == 0
        assert audit["counts"]["with_drawings"] == 0
        assert any("case capacity" in item.lower() for item in audit["lift_areas"])
        assert any("tegning" in item.lower() for item in audit["lift_areas"])
    finally:
        database.close()


def test_compare_chamber_to_cartridge_standard_reports_watch_conditions():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/cartridge_standard_support_compare.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        database.upsert_cartridge_standard(
            {
                "caliber_name": ".308 Winchester",
                "standard_body": "SAAMI",
                "freebore_mm": 1.20,
                "throat_angle_deg": 1.50,
                "neck_diameter_mm": 8.72,
                "case_length_mm": 51.18,
            }
        )

        comparison = compare_chamber_to_cartridge_standard(
            database,
            ".308 Winchester",
            {
                "freebore_mm": 1.45,
                "throat_angle_deg": 1.70,
                "throat_erosion_mm": 0.12,
                "chamber_neck_diameter_mm": 8.72,
                "case_neck_diameter_mm": 8.71,
                "trim_length_mm": 51.00,
            },
        )

        assert comparison["status"] == "watch"
        assert comparison["freebore_delta_mm"] == 0.25
        assert comparison["neck_clearance_mm"] == 0.01
        assert any("tight neck" in note.lower() for note in comparison["notes"])
    finally:
        database.close()


def test_compare_chamber_to_cartridge_standard_uses_reference_delta_when_no_chamber_neck():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/cartridge_standard_support_compare_reference.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        database.upsert_cartridge_standard(
            {
                "caliber_name": ".308 Winchester",
                "standard_body": "SAAMI",
                "neck_diameter_mm": 8.72,
            }
        )

        comparison = compare_chamber_to_cartridge_standard(
            database,
            ".308 Winchester",
            {
                "case_neck_diameter_mm": 8.71,
            },
        )

        assert comparison["neck_clearance_mm"] is None
        assert comparison["neck_reference_delta_mm"] == -0.01
        assert any("referansedelta" in note.lower() for note in comparison["notes"])
    finally:
        database.close()


def test_compare_chamber_to_cartridge_standard_uses_standard_estimate_when_only_chamber_neck_exists():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/cartridge_standard_support_compare_standard_neck.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        database.upsert_cartridge_standard(
            {
                "caliber_name": ".308 Winchester",
                "standard_body": "SAAMI",
                "neck_diameter_mm": 8.72,
            }
        )

        comparison = compare_chamber_to_cartridge_standard(
            database,
            ".308 Winchester",
            {
                "chamber_neck_diameter_mm": 8.69,
            },
        )

        assert comparison["neck_clearance_mm"] == -0.03
        assert comparison["neck_clearance_basis"] == "standard_estimate"
        assert comparison["standard_neck_clearance_mm"] == -0.03
    finally:
        database.close()
