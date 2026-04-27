from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

from src.modules import component_database as component_module

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".github" / "test_tmp"


@contextmanager
def _local_temp_dir():
    path = TEST_TMP_ROOT / f"component-db-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_import_component_csv_rows_for_bullets_accepts_common_headers():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "bullets.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "Bullet Name,Maker,Caliber,Weight (gr),BC G1,BC G7,Length (mm),Diameter (mm),Type,Notes",
                    "Scenar-L,Lapua,6.5mm,136.0,0.578,0.295,34.2,7.82,BTHP,Match bullet",
                ]
            ),
            encoding="utf-8",
        )

        rows, report = component_module.import_component_csv_rows(csv_path, "bullets")

    assert report == {"imported": 1, "skipped": 0}
    assert rows[0]["name"] == "Scenar-L"
    assert rows[0]["manufacturer"] == "Lapua"
    assert rows[0]["weight"] == 136.0
    assert rows[0]["diameter"] == 7.82


def test_import_component_csv_rows_for_powders_tracks_skipped_rows():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "powders.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "Powder Name,Brand,Burn Rate,Density (g/cc),Best For,Temp Stable,Notes",
                    ",Vihtavuori,Fast,0.92,6.5 Creedmoor,Yes,Missing name",
                    "N150,Vihtavuori,Medium,0.94,308 Win,Yes,Stable powder",
                ]
            ),
            encoding="utf-8",
        )

        rows, report = component_module.import_component_csv_rows(csv_path, "powders")

    assert report == {"imported": 1, "skipped": 1}
    assert rows[0]["name"] == "N150"
    assert rows[0]["temp_stable"] is True


def test_merge_component_records_counts_duplicates_and_assigns_ids():
    existing = [
        {
            "id": 4,
            "manufacturer": "Lapua",
            "name": "Scenar-L",
            "caliber": "6.5mm",
            "weight": 136.0,
        }
    ]
    incoming = [
        {
            "manufacturer": "Lapua",
            "name": "Scenar-L",
            "caliber": "6.5mm",
            "weight": 136.0,
        },
        {
            "manufacturer": "Hornady",
            "name": "ELD-M",
            "caliber": "6.5mm",
            "weight": 140.0,
        },
    ]

    report = component_module.merge_component_records(existing, incoming, "bullets")

    assert report == {"added": 1, "duplicates": 1}
    assert len(existing) == 2
    assert existing[-1]["id"] == 5
    assert existing[-1]["name"] == "ELD-M"


def test_component_database_json_roundtrip_preserves_rows():
    with _local_temp_dir() as tmp_path:
        db_path = tmp_path / "components.json"
        data = {
            "bullets": [
                {
                    "id": 1,
                    "manufacturer": "Lapua",
                    "name": "Scenar-L",
                    "caliber": "6.5mm",
                    "weight": 136.0,
                    "bc_g1": 0.578,
                }
            ],
            "powders": [],
            "primers": [],
            "brass": [],
        }

        component_module.export_component_database(data, db_path)
        raw = db_path.read_text(encoding="utf-8")
        loaded = component_module.load_component_database_json(db_path)

    assert '"schema_version": "component_database.v1"' in raw
    assert loaded["bullets"][0]["name"] == "Scenar-L"
    assert loaded["bullets"][0]["manufacturer"] == "Lapua"
    assert loaded["bullets"][0]["weight"] == 136.0


def test_component_database_bullet_csv_roundtrip_reads_exported_row():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "bullets_export.csv"
        data = {
            "bullets": [
                {
                    "id": 7,
                    "manufacturer": "Hornady",
                    "name": "ELD-M",
                    "caliber": "6.5mm",
                    "weight": 140.0,
                    "bc_g1": 0.610,
                    "bc_g7": 0.305,
                    "length": 34.8,
                    "diameter": 7.82,
                    "type": "ELD",
                    "notes": "Roundtrip",
                }
            ],
            "powders": [],
            "primers": [],
            "brass": [],
        }

        component_module.export_component_database(
            data, csv_path, component_type="bullets"
        )
        exported_text = csv_path.read_text(encoding="utf-8")
        rows, report = component_module.import_component_csv_rows(csv_path, "bullets")

    assert report == {"imported": 1, "skipped": 0}
    assert "export_schema_version" in exported_text.splitlines()[0]
    assert rows[0]["name"] == "ELD-M"
    assert rows[0]["manufacturer"] == "Hornady"
    assert rows[0]["weight"] == 140.0
    assert rows[0]["diameter"] == 7.82
