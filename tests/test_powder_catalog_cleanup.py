from __future__ import annotations

import csv
import json
import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from src.tools.powder_catalog_cleanup import clean_powder_catalog, clean_powder_rows

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".github" / "test_tmp"


@contextmanager
def _local_temp_dir(prefix: str):
    path = TEST_TMP_ROOT / f"{prefix}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_clean_powder_rows_normalizes_text_and_related_refs():
    rows = [
        {
            "id": "1",
            "manufacturer": "VECTAN",
            "name": "SP 11",
            "display_name": "VECTAN SP 11",
            "source_label": " Gordon memory dump ",
            "external_ref": "gordon_memory_dump|powder|VECTAN|SP 11",
            "raw_json": json.dumps({"mname": "VECTAN", "pname": "SP 11"}),
        },
        {
            "id": "2",
            "manufacturer": "Vectan",
            "name": "A0",
            "display_name": "Vectan A0",
            "source_label": "Gordon memory dump",
            "external_ref": "gordon_memory_dump|powder|Vectan|A0",
            "raw_json": json.dumps({"mname": "Vectan", "pname": "A0"}),
        },
        {
            "id": "3",
            "manufacturer": "Hodgdon",
            "name": "LeverEvolution",
            "display_name": "Hodgdon Leverevolution",
            "source_label": "Gordon memory dump",
            "external_ref": "gordon_memory_dump|powder|Hodgdon|Leverevolution",
            "raw_json": json.dumps({"mname": "Hodgdon", "pname": "Leverevolution"}),
        },
    ]

    cleaned_rows, stats = clean_powder_rows(rows)

    assert cleaned_rows[0]["manufacturer"] == "Vectan"
    assert cleaned_rows[0]["display_name"] == "Vectan SP 11"
    assert cleaned_rows[0]["source_label"] == "Reference memory dump"
    assert (
        cleaned_rows[0]["external_ref"] == "reference_memory_dump|powder|Vectan|SP 11"
    )
    assert json.loads(cleaned_rows[0]["raw_json"]) == {
        "mname": "Vectan",
        "pname": "SP 11",
    }

    assert cleaned_rows[2]["name"] == "LeverEvolution"
    assert cleaned_rows[2]["display_name"] == "Hodgdon LeverEvolution"
    assert cleaned_rows[2]["source_label"] == "Reference memory dump"
    assert (
        cleaned_rows[2]["external_ref"]
        == "reference_memory_dump|powder|Hodgdon|LeverEvolution"
    )
    assert json.loads(cleaned_rows[2]["raw_json"]) == {
        "mname": "Hodgdon",
        "pname": "LeverEvolution",
    }

    assert stats["rows_changed"] == 3
    assert stats["manufacturer_normalized"] == 1
    assert stats["display_name_normalized"] == 2
    assert stats["blank_display_name_remaining"] == 0


def test_clean_powder_catalog_writes_clean_csv_and_report():
    with _local_temp_dir("powder-catalog-clean") as tmpdir:
        input_path = tmpdir / "powder_catalog_master.csv"
        output_path = tmpdir / "powder_catalog_master_clean.csv"
        report_path = tmpdir / "powder_catalog_master_clean.json"
        markdown_path = tmpdir / "powder_catalog_master_clean.md"
        input_path.write_text(
            "id;display_name;manufacturer;name;source_label;external_ref;raw_json\n"
            '1;VECTAN SP 11;VECTAN;SP 11; Gordon memory dump ;gordon_memory_dump|powder|VECTAN|SP 11;{"mname":"VECTAN","pname":"SP 11"}\n'
            '2;Vectan A0;Vectan;A0;Gordon memory dump;gordon_memory_dump|powder|Vectan|A0;{"mname":"Vectan","pname":"A0"}\n',
            encoding="utf-8",
        )

        stats = clean_powder_catalog(
            input_path,
            output_path,
            report_json_path=report_path,
            report_md_path=markdown_path,
        )

        with output_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            rows = list(reader)

        assert rows[0]["manufacturer"] == "Vectan"
        assert rows[0]["display_name"] == "Vectan SP 11"
        assert rows[0]["source_label"] == "Reference memory dump"
        assert stats["rows_changed"] == 2
        assert report_path.exists()
        assert markdown_path.exists()
