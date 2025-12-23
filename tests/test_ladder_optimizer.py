import os
import sqlite3
import sys

# Ensure repo root is on sys.path so `src` package is importable during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import ladder_optimizer


class SimpleDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()


def test_fit_quadratic_and_suggest():
    db = SimpleDB()
    # Create ladder_tests and test_results tables
    db.cursor.execute(
        """
        CREATE TABLE ladder_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rifle_id INTEGER,
            bullet_id INTEGER,
            powder_id INTEGER
        )
        """
    )
    db.cursor.execute(
        "INSERT INTO ladder_tests (rifle_id, bullet_id, powder_id) VALUES (1, 2, 3)"
    )
    lt_id = db.cursor.lastrowid

    # Insert three test_results with charges and group sizes (mm)
    samples = [
        (lt_id, 40.0, 1.5),
        (lt_id, 42.0, 1.2),
        (lt_id, 44.0, 1.6),
    ]
    db.cursor.execute(
        """
        CREATE TABLE test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ladder_test_id INTEGER,
            charge_weight REAL,
            group_size_mm REAL
        )
        """
    )
    for lt, charge, group in samples:
        db.cursor.execute(
            "INSERT INTO test_results (ladder_test_id, charge_weight, group_size_mm) VALUES (?, ?, ?)",
            (lt, charge, group),
        )

    db.conn.commit()

    res = ladder_optimizer.suggest_charge_from_history(db, rifle_id=1)
    assert res is not None
    assert "suggested_charge" in res
    assert (
        res["observed_range"][0] <= res["suggested_charge"] <= res["observed_range"][1]
    )
