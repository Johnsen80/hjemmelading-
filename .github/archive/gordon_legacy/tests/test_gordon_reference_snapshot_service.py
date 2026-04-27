from pathlib import Path

from src.database.database import Database
from src.tools.gordon_reference_snapshot_service import import_gordon_readable_snapshots


def test_import_gordon_readable_snapshots_copies_variants_into_internal_db():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/gordon_reference_snapshots.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        projectiles_csv = Path(
            "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tmp/gordon_extract_recheck/gordon_extracted_projectiles_raw.csv"
        )
        propellants_csv = Path(
            "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tmp/gordon_extract_recheck/gordon_extracted_propellants_raw.csv"
        )
        calibers_csv = Path(
            "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tmp/gordon_extract_recheck/gordon_extracted_calibers_raw.csv"
        )

        result = import_gordon_readable_snapshots(
            database, projectiles_csv, propellants_csv, calibers_csv
        )

        assert result["bullets_added_or_updated"] >= 9
        assert result["powders_added_or_updated"] >= 2
        assert result["calibers_added_or_updated"] >= 1

        bullets = database.list_component_reference_snapshots(
            component_type="bullet", source_system="gordon_readable"
        )
        powders = database.list_component_reference_snapshots(
            component_type="powder", source_system="gordon_readable"
        )
        calibers = database.list_component_reference_snapshots(
            component_type="caliber", source_system="gordon_readable"
        )

        assert bullets
        assert powders
        assert calibers
        assert any(
            row["manufacturer"] == "Hornady" and "ELD-M" in (row["model_name"] or "")
            for row in bullets
        )
        assert any(
            row["manufacturer"] == "Vihtavuori" and row["model_name"] == "N540"
            for row in powders
        )
        assert any(row["lot_number"] == "2021-09-30" for row in powders)
        assert any(
            "C.I.P." in (row["manufacturer"] or "")
            or ".308" in (row["model_name"] or "")
            for row in calibers
        )
    finally:
        database.close()


def test_database_creates_component_reference_snapshots_table():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/component_reference_snapshots.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        columns = {
            row["name"]
            for row in database.execute_query(
                "PRAGMA table_info(component_reference_snapshots)"
            )
        }

        assert "source_system" in columns
        assert "component_type" in columns
        assert "manufacturer" in columns
        assert "model_name" in columns
        assert "caliber" in columns
        assert "lot_number" in columns
        assert "profile_json" in columns
        assert "raw_json" in columns
    finally:
        database.close()


def test_import_gordon_readable_snapshots_supports_full_xml_exports():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/gordon_reference_snapshots_xml.db"
    )
    xml_dir = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/gordon_reference_xml_case_a"
    )
    xml_dir.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    projectiles_xml = xml_dir / "full_projectiles.xml"
    propellants_xml = xml_dir / "full_propellants.xml"
    calibers_xml = xml_dir / "full_calibers.xml"
    projectiles_xml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<GordonsReloadingTool>
  <projectilefile>
    <var name="mname" value="Hornady" />
    <var name="pname" value="ELD-M" />
    <var name="ProjectileName" value="Hornady ELD-M" />
    <var name="caliber" value=".264" />
    <var name="gmass" value="140.0" />
    <var name="gdia" value="6.71" />
    <var name="glen" value="34.8" />
    <var name="g1bc" value="0.646" />
    <var name="g7bc" value="0.326" />
    <var name="gUBCS" value="H0S2F2S4N3" />
  </projectilefile>
</GordonsReloadingTool>
""",
        encoding="utf-8",
    )
    propellants_xml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<GordonsReloadingTool>
  <propellantfile>
    <var name="mname" value="Vihtavuori" />
    <var name="pname" value="N540" />
    <var name="lotid" value="2021-09-30" />
    <var name="Ba" value="2.9203" />
    <var name="Qex" value="4100" />
    <var name="k" value="1.2245" />
    <var name="a0" value="0.9701" />
    <var name="z1" value="0.2863" />
    <var name="z2" value="0.8148" />
    <var name="eta" value="713" />
    <var name="pc" value="1390" />
    <var name="pcd" value="620" />
    <var name="pt" value="21" />
    <var name="imageUuid" value="skip-me" />
  </propellantfile>
</GordonsReloadingTool>
""",
        encoding="utf-8",
    )
    calibers_xml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<GordonsReloadingTool>
  <caliberfile>
    <var name="CaliberName" value=".308 Winchester" />
    <var name="standard" value="C.I.P." />
    <var name="Pmax" value="4150" />
    <var name="Dz" value="7.82" />
    <var name="caselen" value="51.18" />
  </caliberfile>
</GordonsReloadingTool>
""",
        encoding="utf-8",
    )

    database = Database(str(db_path))
    try:
        result = import_gordon_readable_snapshots(
            database, projectiles_xml, propellants_xml, calibers_xml
        )

        assert result["bullets_added_or_updated"] == 1
        assert result["powders_added_or_updated"] == 1
        assert result["calibers_added_or_updated"] == 1

        bullets = database.list_component_reference_snapshots(
            component_type="bullet", source_system="gordon_readable"
        )
        powders = database.list_component_reference_snapshots(
            component_type="powder", source_system="gordon_readable"
        )
        calibers = database.list_component_reference_snapshots(
            component_type="caliber", source_system="gordon_readable"
        )

        assert len(bullets) == 1
        assert bullets[0]["manufacturer"] == "Hornady"
        assert bullets[0]["source_file"] == "full_projectiles.xml"
        assert len(powders) == 1
        assert powders[0]["manufacturer"] == "Vihtavuori"
        assert powders[0]["source_file"] == "full_propellants.xml"
        assert len(calibers) == 1
        assert calibers[0]["model_name"] == ".308 Winchester"
        assert calibers[0]["source_file"] == "full_calibers.xml"
    finally:
        database.close()
