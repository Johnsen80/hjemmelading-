import json
import os
import shutil
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

# Ensure repo root is on sys.path so `src` package is importable during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.database import Database
from src.tools.load_development_session_service import create_load_development_session
from src.utils import chronograph_import

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".github" / "test_tmp"


@contextmanager
def _local_temp_dir():
    path = TEST_TMP_ROOT / f"chronograph-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


class SimpleDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()


@pytest.mark.core
def test_import_velocities_persists_and_summarizes():
    db = SimpleDB()
    velocities = [2500.0, 2520.0, 2490.0]
    res = chronograph_import.import_velocities(
        db,
        velocities,
        ammo_profile_id=5,
        load_session_id=7,
        note="unit-test",
    )
    assert res["ok"] is True
    assert "import_id" in res
    stats = res["stats"]
    assert stats["count"] == 3
    assert abs(stats["avg"] - 2503.3333) < 0.1
    row = db.conn.execute(
        "SELECT load_session_id FROM chronograph_imports WHERE id = ?",
        (res["import_id"],),
    ).fetchone()
    assert row[0] == 7


@pytest.mark.core
def test_import_chronograph_csv_parses_file():
    db = SimpleDB()
    content = "velocity\n2600\n2610\n2590\n"
    with _local_temp_dir() as tmpdir:
        p = tmpdir / "chrono.csv"
        p.write_text(content, encoding="utf-8")

        res = chronograph_import.import_chronograph_csv(
            db,
            str(p),
            ammo_profile_id=None,
            load_session_id=9,
            note="csv-test",
        )
    assert res["ok"] is True
    assert res["stats"]["count"] == 3
    row = db.conn.execute(
        "SELECT load_session_id FROM chronograph_imports WHERE id = ?",
        (res["import_id"],),
    ).fetchone()
    assert row[0] == 9


@pytest.mark.core
def test_import_velocities_migrates_existing_chronograph_imports_table():
    db_path = TEST_TMP_ROOT / "chronograph-migration.db"
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE chronograph_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            ammo_profile_id INTEGER,
            import_date TEXT DEFAULT CURRENT_TIMESTAMP,
            velocity_count INTEGER,
            velocity_avg REAL,
            velocity_es REAL,
            velocity_sd REAL,
            velocities_json TEXT,
            notes TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    db = Database(str(db_path))
    try:
        session_id = create_load_development_session(
            db,
            rifle_id=None,
            rifle_name="Chrono Test",
            rifle_caliber="308 Win",
            usage_profile_key="validation",
            usage_profile_name="Validation",
        )
        res = chronograph_import.import_velocities(
            db,
            [2600.0, 2610.0],
            load_session_id=session_id,
        )
        row = db.execute_query(
            "SELECT load_session_id FROM chronograph_imports WHERE id = ?",
            (res["import_id"],),
        )[0]
        assert row["load_session_id"] == session_id
    finally:
        db.close()
        if db_path.exists():
            db_path.unlink()


@pytest.mark.core
def test_golden_chronograph_samples():
    base = Path(__file__).resolve().parent / "data" / "golden" / "chronograph"
    expected_path = base / "expected_stats.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    for filename, stats in expected.items():
        if not filename.endswith(".csv"):
            continue
        velocities = chronograph_import._extract_velocities_from_csv(
            str(base / filename)
        )
        result = chronograph_import.summarize_velocities(velocities)
        assert result["count"] == stats["count"]
        assert abs(result["avg"] - stats["avg"]) < 0.01
        assert abs(result["es"] - stats["es"]) < 0.01
        assert abs(result["sd"] - stats["sd_sample"]) < 0.05
