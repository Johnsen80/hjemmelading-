import os
import sqlite3
import sys

# Ensure repo root is on sys.path so `src` package is importable during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import chronograph_import


class SimpleDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()


def test_import_velocities_persists_and_summarizes():
    db = SimpleDB()
    velocities = [2500.0, 2520.0, 2490.0]
    res = chronograph_import.import_velocities(
        db, velocities, ammo_profile_id=5, note="unit-test"
    )
    assert res["ok"] is True
    assert "import_id" in res
    stats = res["stats"]
    assert stats["count"] == 3
    assert abs(stats["avg"] - 2503.3333) < 0.1


def test_import_chronograph_csv_parses_file(tmp_path):
    db = SimpleDB()
    content = "velocity\n2600\n2610\n2590\n"
    p = tmp_path / "chrono.csv"
    p.write_text(content)

    res = chronograph_import.import_chronograph_csv(
        db, str(p), ammo_profile_id=None, note="csv-test"
    )
    assert res["ok"] is True
    assert res["stats"]["count"] == 3
