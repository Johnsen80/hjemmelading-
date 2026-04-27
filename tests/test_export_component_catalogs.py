from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from src.database.database import Database

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


def test_export_component_catalogs_runs_with_relative_defaults_via_args():
    with _local_temp_dir("export-component-catalogs") as tmpdir:
        db_path = tmpdir / "catalogs.db"
        export_dir = tmpdir / "exports"

        database = Database(str(db_path))
        try:
            database.conn.execute(
                "INSERT INTO cases (name, manufacturer, caliber, material, quantity, times_fired, needs_annealing, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "6.5 CM Match",
                    "Lapua",
                    "6.5 Creedmoor",
                    "Brass",
                    100,
                    2,
                    0,
                    "Seed case",
                ),
            )
            database.conn.commit()
        finally:
            database.close()

        script_path = (
            PROJECT_ROOT / ".github" / "tools" / "export_component_catalogs.py"
        )
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--db-path",
                str(db_path),
                "--export-dir",
                str(export_dir),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )

        assert result.returncode == 0, result.stderr or result.stdout
        payload = json.loads(result.stdout)
        assert payload["exports"]["primers"]["rows"] >= 1
        assert payload["exports"]["cases"]["rows"] >= 1

        manifest_path = export_dir / "components_catalog_manifest.json"
        primers_path = export_dir / "primers_catalog_master.csv"
        cases_path = export_dir / "cases_catalog_master.csv"
        assert manifest_path.exists()
        assert primers_path.exists()
        assert cases_path.exists()

        with cases_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))
        assert any(row["manufacturer"] == "Lapua" for row in rows)
        assert any(
            row["display_name"] == "Lapua 6.5 CM Match 6.5 Creedmoor" for row in rows
        )


def test_export_component_catalogs_seeds_default_cases_for_fresh_db():
    with _local_temp_dir("export-component-catalogs-seeded") as tmpdir:
        db_path = tmpdir / "fresh-catalogs.db"
        export_dir = tmpdir / "exports"

        database = Database(str(db_path))
        database.close()

        script_path = (
            PROJECT_ROOT / ".github" / "tools" / "export_component_catalogs.py"
        )
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--db-path",
                str(db_path),
                "--export-dir",
                str(export_dir),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )

        assert result.returncode == 0, result.stderr or result.stdout
        payload = json.loads(result.stdout)
        assert payload["exports"]["cases"]["rows"] >= 3

        cases_path = export_dir / "cases_catalog_master.csv"
        with cases_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))

        assert any(
            row["manufacturer"] == "Reference"
            and row["name"] == "Baseline Brass"
            and row["caliber"] == "6.5 Creedmoor"
            and row["case_capacity_gr_h2o"] == "53.8"
            and row["trim_length_mm"] == "48.77"
            for row in rows
        )
