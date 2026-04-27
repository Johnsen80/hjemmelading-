from __future__ import annotations

import csv
import json
import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from src.tools.bullet_catalog_cleanup import clean_bullet_catalog, clean_bullet_rows

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".github" / "test_tmp"


@contextmanager
def _local_temp_dir(prefix: str):
    path = TEST_TMP_ROOT / f"{prefix}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_clean_bullet_rows_normalizes_text_and_related_refs():
    rows = [
        {
            "id": "1",
            "manufacturer": "RG bullets",
            "name": "Sub-X  #45031",
            "caliber": ".356 ",
            "weight_grains": "124",
            "display_name": "",
            "source_label": " Gordon memory dump ",
            "external_ref": "gordon_memory_dump|bullet|RG bullets|Sub-X  #45031|.356 |124",
            "raw_json": json.dumps(
                {"mname": "RG bullets", "pname": "Sub-X  #45031", "caliber": ".356 "}
            ),
        },
        {
            "id": "2",
            "manufacturer": "RG Bullets",
            "name": "Control",
            "caliber": ".355",
            "weight_grains": "115.0",
            "display_name": "RG Bullets Control",
            "source_label": "Gordon memory dump",
            "external_ref": "gordon_memory_dump|bullet|RG Bullets|Control|.355|115.0",
            "raw_json": json.dumps(
                {"mname": "RG Bullets", "pname": "Control", "caliber": ".355"}
            ),
        },
    ]

    cleaned_rows, stats = clean_bullet_rows(rows)

    assert cleaned_rows[0]["manufacturer"] == "RG Bullets"
    assert cleaned_rows[0]["name"] == "Sub-X #45031"
    assert cleaned_rows[0]["caliber"] == ".356"
    assert cleaned_rows[0]["display_name"] == "RG Bullets Sub-X #45031"
    assert cleaned_rows[0]["source_label"] == "Reference memory dump"
    assert (
        cleaned_rows[0]["external_ref"]
        == "reference_memory_dump|bullet|RG Bullets|Sub-X #45031|.356|124.0"
    )
    assert json.loads(cleaned_rows[0]["raw_json"]) == {
        "mname": "RG Bullets",
        "pname": "Sub-X #45031",
        "caliber": ".356",
    }
    assert cleaned_rows[1]["source_label"] == "Reference memory dump"
    assert (
        cleaned_rows[1]["external_ref"]
        == "reference_memory_dump|bullet|RG Bullets|Control|.355|115.0"
    )
    assert stats["rows_changed"] == 2
    assert stats["blank_display_name_remaining"] == 0


def test_clean_bullet_catalog_writes_clean_csv_and_report():
    with _local_temp_dir("bullet-catalog-clean") as tmpdir:
        input_path = tmpdir / "bullets_catalog_master.csv"
        output_path = tmpdir / "bullets_catalog_master_clean.csv"
        report_path = tmpdir / "bullets_catalog_master_clean.json"
        markdown_path = tmpdir / "bullets_catalog_master_clean.md"
        input_path.write_text(
            "id;name;manufacturer;caliber;weight_grains;display_name;source_label;external_ref;raw_json\n"
            '1;Sub-X  #45031;RG bullets;.356 ;124;;;gordon_memory_dump|bullet|RG bullets|Sub-X  #45031|.356 |124;{"mname":"RG bullets","pname":"Sub-X  #45031","caliber":".356 "}\n',
            encoding="utf-8",
        )

        stats = clean_bullet_catalog(
            input_path,
            output_path,
            report_json_path=report_path,
            report_md_path=markdown_path,
        )

        with output_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            rows = list(reader)

        assert rows[0]["manufacturer"] == "RG bullets"
        assert rows[0]["name"] == "Sub-X #45031"
        assert rows[0]["display_name"] == "RG bullets Sub-X #45031"
        assert stats["rows_changed"] == 1
        assert report_path.exists()
        assert markdown_path.exists()
