from pathlib import Path

from src.database.database import Database
from src.tools.cartridge_standards_service import (
    import_cartridge_standards_from_knowledge_base,
)


def test_import_cartridge_standards_from_knowledge_base_reads_cip_dimensions():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/import_cartridge_standards.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    csv_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/data/component_knowledge_base/calibers.csv"
    )

    database = Database(str(db_path))
    try:
        result = import_cartridge_standards_from_knowledge_base(database, csv_path)
        assert result["added_or_updated"] >= 1

        rows = database.list_cartridge_standards(caliber_name="6.5 Creedmoor")
        assert rows
        cip_rows = [row for row in rows if row.get("standard_body") == "CIP"]
        assert cip_rows
        row = cip_rows[0]

        assert row["caliber_name"] == "6.5 Creedmoor"
        assert float(row["max_pressure_bar"]) == 4350.0
        assert row["max_pressure_psi"] > 63000
        assert row["oal_mm"] > 69
        assert row["source_kind"] == "official_cip"
        assert row["evidence_level"] == "official_standard"
        assert "cip-bobp.org" in (row.get("drawing_pdf_url") or "")
    finally:
        database.close()


def test_import_cartridge_standards_from_knowledge_base_reads_direct_saami_seed_rows():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/import_cartridge_standards_saami.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    csv_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/data/component_knowledge_base/saami_rifle_standards.csv"
    )

    database = Database(str(db_path))
    try:
        result = import_cartridge_standards_from_knowledge_base(database, csv_path)
        assert result["added_or_updated"] >= 5

        rows = database.list_cartridge_standards(caliber_name="6.5 Creedmoor")
        assert rows
        saami_rows = [row for row in rows if row.get("standard_body") == "SAAMI"]
        assert saami_rows
        row = saami_rows[0]

        assert row["caliber_name"] == "6.5 Creedmoor"
        assert row["source_kind"] == "official_saami"
        assert row["evidence_level"] == "official_standard"
        assert round(float(row["max_pressure_psi"])) == 62000
        assert 4274 < float(row["max_pressure_bar"]) < 4277
        assert round(float(row["oal_mm"]), 2) == 71.76
        assert "saami.org" in (row.get("drawing_pdf_url") or "")
    finally:
        database.close()


def test_import_cartridge_standards_from_knowledge_base_reads_saami_prestandard_rows():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/import_cartridge_standards_saami_prestandard.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    csv_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/data/component_knowledge_base/saami_newly_accepted_rifle_cartridges.csv"
    )

    database = Database(str(db_path))
    try:
        result = import_cartridge_standards_from_knowledge_base(database, csv_path)
        assert result["added_or_updated"] >= 6

        rows = database.list_cartridge_standards(caliber_name="7mm Backcountry")
        assert rows
        row = rows[0]

        assert row["standard_body"] == "SAAMI"
        assert row["source_kind"] == "official_saami"
        assert row["evidence_level"] == "official_prestandard"
        assert round(float(row["max_pressure_psi"])) == 80000
        assert "saami.org" in (row.get("drawing_pdf_url") or "")
    finally:
        database.close()


def test_import_cartridge_standards_from_knowledge_base_reads_saami_announcement_rows():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/import_cartridge_standards_saami_announcement.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    csv_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/data/component_knowledge_base/saami_rifle_acceptance_announcements.csv"
    )

    database = Database(str(db_path))
    try:
        result = import_cartridge_standards_from_knowledge_base(database, csv_path)
        assert result["added_or_updated"] >= 15

        rows = database.list_cartridge_standards(caliber_name="277 SIG Fury")
        assert rows
        row = rows[0]

        assert row["standard_body"] == "SAAMI"
        assert row["source_kind"] == "official_saami"
        assert row["evidence_level"] == "official_announcement"
        assert round(float(row["max_pressure_psi"])) == 80000
        assert "saami.org" in (row.get("drawing_pdf_url") or "")
    finally:
        database.close()
