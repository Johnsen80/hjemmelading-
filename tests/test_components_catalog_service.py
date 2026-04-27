from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from src.database.database import Database
from src.tools import components_catalog_service as catalog_service
from src.tools.bullet_catalog_cleanup import clean_bullet_rows
from src.tools.components_catalog_service import (
    merge_into_db,
    sync_reference_knowledge_base,
)
from src.tools.powder_catalog_cleanup import clean_powder_rows

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".github" / "test_tmp"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def _local_temp_dir(prefix: str):
    path = TEST_TMP_ROOT / f"{prefix}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_merge_into_db_imports_components_and_seed_lots():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/components_catalog_service.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    database.close()

    components = {
        "bullets": [
            {
                "bullet_id": "10",
                "manufacturer": "Hornady",
                "name": "ELD-M",
                "caliber": "0.264",
                "weight_grains": "140.0",
                "diameter_in": "0.264",
                "length_in": "1.332",
                "bc_g1": "0.58",
                "bc_g7": "0.0",
                "type": "BTHP",
                "display_name": "Hornady  ELD-M",
                "profile_json": json.dumps({"diameter_mm": 6.71}),
                "source_label": "grtload:test.grtload",
                "raw_json": json.dumps({"lotid": "LOT-B-1"}),
            }
        ],
        "powders": [
            {
                "powder_id": "20",
                "manufacturer": "Vihtavuori",
                "name": "N540",
                "burn_rate": "0.5816",
                "density": "0.94",
                "source_label": "grtload:test.grtload",
                "raw_json": json.dumps(
                    {
                        "lotid": "LOT-P-1",
                        "Ba": "0.5816",
                        "Qex": "4000",
                        "k": "1.2131",
                        "a0": "1.4074",
                        "z1": "0.4882",
                        "z2": "0.8341",
                        "eta": "1",
                        "pc": "1620",
                        "pcd": "940",
                        "pt": "21",
                        "tcc": "0",
                        "tch": "0",
                    }
                ),
            }
        ],
        "primers": [
            {
                "manufacturer": "CCI",
                "name": "BR-4",
                "type": "Small Rifle Benchrest",
                "size": "small rifle",
                "quantity": "0",
                "notes": "Seed primer",
                "product_line": "CCI Primers",
                "part_number": "19",
                "source_kind": "manufacturer_published+reference_inferred",
                "manufacturer_source": "CCI catalog",
                "match_grade": "1",
                "magnum": "0",
                "ar_variant": "0",
                "nominal_diameter_in": "0.175",
                "used_for": "Benchrest",
                "box_count": "100",
                "non_corrosive": "1",
                "lead_free": "0",
                "primer_family": "small_rifle_benchrest",
                "cup_thickness_in": "0.025",
                "cup_hardness_class": "hard",
                "pressure_tolerance_class": "high",
                "ignition_strength_class": "standard_plus",
                "recommended_pressure_min_psi": "50000",
                "recommended_pressure_max_psi": "62000",
                "cold_weather_suitability": "good",
                "primer_sign_interpretation": "late_signs_possible",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon notes",
                "raw_json": json.dumps({"lotid": "LOT-PR-1"}),
            }
        ],
        "cases": [
            {
                "manufacturer": "Lapua",
                "name": "Palma Brass",
                "caliber": ".308 Winchester",
                "material": "brass",
                "quantity": "0",
                "times_fired": "0",
                "needs_annealing": "0",
                "notes": "Seed case",
                "case_capacity_gr_h2o": "56.1",
                "trim_length_mm": "51.18",
                "primer_pocket_uniformed": "1",
                "flash_hole_deburred": "1",
            }
        ],
        "calibers": [],
    }

    report = merge_into_db(components, db_path)

    assert report["bullets_added"] == 1
    assert report["powders_added"] == 1
    assert report["primers_updated"] == 1
    assert report["cases_added"] == 1
    assert report["lots_added"] == 3
    assert report["powder_models_added"] == 1
    assert report["powder_models_usable_for_simulation"] == 1

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        bullets = [dict(row) for row in con.execute("SELECT * FROM bullets")]
        powders = [dict(row) for row in con.execute("SELECT * FROM powder")]
        primers = [
            dict(row)
            for row in con.execute(
                "SELECT * FROM primers WHERE manufacturer = 'CCI' AND name = 'BR-4'"
            )
        ]
        cases = [
            dict(row)
            for row in con.execute(
                "SELECT * FROM cases WHERE manufacturer = 'Lapua' AND name = 'Palma Brass'"
            )
        ]
        lots = [
            dict(row)
            for row in con.execute(
                "SELECT * FROM component_lots ORDER BY component_type"
            )
        ]
        powder_models = [
            dict(row) for row in con.execute("SELECT * FROM powder_database")
        ]
    finally:
        con.close()

    assert bullets[0]["name"] == "ELD-M"
    assert bullets[0]["display_name"] == "Hornady ELD-M"
    assert bullets[0]["source"] == "load_snapshot:test.load"
    assert bullets[0]["source_label"] == "load_snapshot:test.load"
    assert bullets[0]["source_kind"] == "load_snapshot"
    assert bullets[0]["evidence_level"] == "imported_snapshot"
    assert bullets[0]["profile_json"] == json.dumps({"diameter_mm": 6.71})
    assert bullets[0]["raw_json"] == json.dumps({"lotid": "LOT-B-1"})
    assert powders[0]["name"] == "N540"
    assert powders[0]["source_version"] == "component_kb.v1"
    assert powders[0]["source"] == "load_snapshot:test.load"
    assert powders[0]["source_kind"] == "load_snapshot"
    assert powders[0]["evidence_level"] == "simulation_seed"
    assert primers[0]["match_grade"] == 1
    assert primers[0]["product_line"] == "CCI Primers"
    assert primers[0]["reference_source"] == "Calhoon notes"
    assert cases[0]["caliber"] == ".308 Winchester"
    assert cases[0]["case_capacity_gr_h2o"] == 56.1
    assert cases[0]["primer_pocket_uniformed"] == 1
    assert [lot["lot_number"] for lot in lots] == ["LOT-B-1", "LOT-P-1", "LOT-PR-1"]
    assert powder_models[0]["quickload_available"] == 1
    assert powder_models[0]["usable_for_simulation"] == 1
    assert powder_models[0]["quickload_ba_value"] == 0.5816
    assert powder_models[0]["qex_kj_per_kg"] == 4000.0
    assert powder_models[0]["k_ratio"] == 1.2131


def test_sync_reference_knowledge_base_imports_components_and_cartridge_standards():
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/components_reference_sync.db"
    )
    kb_root = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/data/component_knowledge_base"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    report = sync_reference_knowledge_base(kb_root=kb_root, db_path=db_path)

    assert report["components"]["bullets_added"] >= 1
    assert report["components"]["powders_added"] >= 1
    assert report["cartridge_standards"]["added_or_updated"] >= 1
    assert "saami_rifle_standards.csv" in report["cartridge_standards"]["files"]

    database = Database(str(db_path))
    try:
        standards = database.list_cartridge_standards(caliber_name="6.5 Creedmoor")
        assert standards
        assert any(row.get("standard_body") == "SAAMI" for row in standards)
    finally:
        database.close()


def test_read_csv_rows_detects_semicolon_without_mutating_csv_excel():
    with _local_temp_dir("components-catalog-csv") as tmpdir:
        csv_path = tmpdir / "powders.csv"
        csv_path.write_text(
            "name;manufacturer;density\nN540;Vihtavuori;0.94\n",
            encoding="utf-8-sig",
        )

        original_delimiter = csv.excel.delimiter
        rows = catalog_service._read_csv_rows(csv_path)

        assert rows == [
            {"name": "N540", "manufacturer": "Vihtavuori", "density": "0.94"}
        ]
        assert csv.excel.delimiter == original_delimiter


def test_load_component_knowledge_base_prefers_export_catalogs(monkeypatch):
    with _local_temp_dir("components-catalog-kb") as tmpdir:
        kb_root = tmpdir / "kb"
        export_root = tmpdir / "exports"
        kb_root.mkdir()
        export_root.mkdir()

        (kb_root / "bullets.csv").write_text(
            "name,manufacturer,caliber,weight_grains\nKB Bullet,Maker,0.264,140\n",
            encoding="utf-8",
        )
        (kb_root / "powders.csv").write_text(
            "name,manufacturer,density\nKB Powder,Maker,0.91\n",
            encoding="utf-8",
        )
        (kb_root / "calibers.csv").write_text(
            "name\n6.5 Creedmoor\n",
            encoding="utf-8",
        )
        (export_root / "primers_catalog_master.csv").write_text(
            "name,manufacturer,type\nExport Primer,Maker,Standard\n",
            encoding="utf-8",
        )
        (export_root / "cases_catalog_master.csv").write_text(
            "name,manufacturer,caliber,material\nExport Case,Maker,6.5 Creedmoor,brass\n",
            encoding="utf-8",
        )
        (export_root / "bullets_catalog_master.csv").write_text(
            "name,manufacturer,caliber,weight_grains\nExport Bullet,Maker,0.264,147\n",
            encoding="utf-8",
        )
        (export_root / "bullets_catalog_master_clean.csv").write_text(
            "name,manufacturer,caliber,weight_grains\nClean Bullet,Maker,0.264,150\n",
            encoding="utf-8",
        )
        (export_root / "powder_catalog_master.csv").write_text(
            "name,manufacturer,density\nExport Powder,Maker,0.95\n",
            encoding="utf-8",
        )
        (export_root / "powder_catalog_master_clean.csv").write_text(
            "name,manufacturer,density\nClean Powder,Maker,0.97\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(catalog_service, "DEFAULT_EXPORT_ROOT", export_root)

        components = catalog_service.load_component_knowledge_base(
            kb_root, export_root=export_root
        )

        assert components["bullets"][0]["name"] == "Clean Bullet"
        assert components["powders"][0]["name"] == "Clean Powder"
        assert components["primers"][0]["name"] == "Export Primer"
        assert components["cases"][0]["name"] == "Export Case"
        assert components["calibers"][0]["name"] == "6.5 Creedmoor"


def test_merge_into_db_normalizes_bullet_fields_and_reuses_existing_row():
    with _local_temp_dir("components-catalog-normalize") as tmpdir:
        db_path = tmpdir / "catalog.db"
        database = Database(str(db_path))
        database.close()

        initial_components = {
            "bullets": [
                {
                    "bullet_id": "10",
                    "manufacturer": "RG Bullets",
                    "name": "CMJ9mm",
                    "caliber": ".356",
                    "weight_grains": "124.0",
                    "diameter_in": "0.356",
                    "length_in": "0.557",
                    "bc_g1": "0.12",
                    "type": "FMJ",
                    "source_label": "reference_memory_dump",
                    "raw_json": json.dumps({"lotid": "LOT-1"}),
                }
            ],
            "powders": [],
            "calibers": [],
        }
        noisy_components = {
            "bullets": [
                {
                    "bullet_id": "10",
                    "manufacturer": "RG bullets",
                    "name": "CMJ9mm",
                    "caliber": ".356 ",
                    "weight_grains": "124.0",
                    "diameter_in": "0.356",
                    "length_in": "0.557",
                    "bc_g1": "0.12",
                    "type": "FMJ",
                    "display_name": "",
                    "source_label": "reference_memory_dump",
                    "raw_json": json.dumps({"lotid": "LOT-1"}),
                }
            ],
            "powders": [],
            "calibers": [],
        }

        first_report = merge_into_db(initial_components, db_path)
        second_report = merge_into_db(noisy_components, db_path)

        con = sqlite3.connect(str(db_path))
        con.row_factory = sqlite3.Row
        try:
            bullets = [dict(row) for row in con.execute("SELECT * FROM bullets")]
        finally:
            con.close()

        assert first_report["bullets_added"] == 1
        assert second_report["bullets_added"] == 0
        assert second_report["bullets_updated"] == 1
        assert len(bullets) == 1
        assert bullets[0]["manufacturer"] == "RG Bullets"
        assert bullets[0]["name"] == "CMJ9mm"
        assert bullets[0]["caliber"] == ".356"
        assert bullets[0]["display_name"] == "RG Bullets CMJ9mm"
        assert bullets[0]["source_label"] == "reference_memory_dump"


def test_components_catalog_service_runs_as_direct_script():
    with _local_temp_dir("components-catalog-script") as tmpdir:
        kb_root = tmpdir / "kb"
        db_path = tmpdir / "catalog.db"
        kb_root.mkdir()

        (kb_root / "bullets.csv").write_text(
            "name,manufacturer,caliber,weight_grains,diameter_in,length_in,bc_g1,bc_g7,type,source_label,raw_json,bullet_id\n"
            "Script Bullet,Maker,0.264,140,0.264,1.33,0.62,0.31,BTHP,component_xml:test,{},42\n",
            encoding="utf-8",
        )
        (kb_root / "powders.csv").write_text(
            "name,manufacturer,burn_rate,density,source_label,raw_json,powder_id\n"
            "Script Powder,Maker,0.51,0.95,component_xml:test,{},84\n",
            encoding="utf-8",
        )
        (kb_root / "calibers.csv").write_text("name\n6.5 Creedmoor\n", encoding="utf-8")

        script_path = PROJECT_ROOT / "src" / "tools" / "components_catalog_service.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--kb-root",
                str(kb_root),
                "--db-path",
                str(db_path),
                "--export-root",
                str(tmpdir / "exports"),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )

        assert result.returncode == 0, result.stderr or result.stdout
        payload = json.loads(result.stdout)
        assert payload["components"]["bullets_added"] == 1
        assert payload["components"]["powders_added"] == 1
        assert payload["cartridge_standards"]["added_or_updated"] >= 1
        assert db_path.exists()


def test_clean_catalogs_preserve_engine_critical_seed_data():
    export_root = PROJECT_ROOT / ".github" / "data" / "exports"

    bullet_master_rows = catalog_service._read_csv_rows(
        export_root / "bullets_catalog_master.csv"
    )
    bullet_clean_rows, _ = clean_bullet_rows(bullet_master_rows)
    powder_master_rows = catalog_service._read_csv_rows(
        export_root / "powder_catalog_master.csv"
    )
    powder_clean_rows, _ = clean_powder_rows(powder_master_rows)

    def normalized_text(value: str) -> str:
        return " ".join(str(value or "").strip().split()).lower()

    def bullet_signature(
        row: dict[str, str],
    ) -> tuple[str, str, str, str, str, str, str]:
        return (
            normalized_text(row.get("manufacturer") or ""),
            normalized_text(row.get("name") or ""),
            str(row.get("caliber") or "").replace(" ", "").strip().lower(),
            str(row.get("weight_grains") or "").strip(),
            str(row.get("bc_g1") or "").strip(),
            str(row.get("bc_g7") or "").strip(),
            normalized_text(row.get("type") or ""),
        )

    def powder_signature(row: dict[str, str]) -> tuple[str, str, str, str]:
        return (
            normalized_text(row.get("manufacturer") or ""),
            normalized_text(row.get("name") or ""),
            str(row.get("burn_rate") or "").strip(),
            str(row.get("density") or "").strip(),
        )

    assert len(bullet_master_rows) == len(bullet_clean_rows)
    assert len(powder_master_rows) == len(powder_clean_rows)
    assert {bullet_signature(row) for row in bullet_master_rows} == {
        bullet_signature(row) for row in bullet_clean_rows
    }
    assert {powder_signature(row) for row in powder_master_rows} == {
        powder_signature(row) for row in powder_clean_rows
    }
