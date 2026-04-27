import os
import sqlite3
import sys

import pytest

# make src importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import calibrator


class FakeEngine:
    def __init__(self, scale=1.02, bias=-5.0):
        self.scale = scale
        self.bias = bias

    def predict_velocity(self, charge):
        # produce a simple monotonic prediction: base 2000 + 10*charge
        return 2000.0 + 10.0 * float(charge) * self.scale + self.bias


class SimpleDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self):
        cur = self.cursor
        cur.execute(
            """
            CREATE TABLE chronograph_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                ammo_profile_id INTEGER,
                import_date TEXT,
                velocity_count INTEGER,
                velocity_avg REAL,
                velocity_es REAL,
                velocity_sd REAL,
                velocities_json TEXT,
                notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE ammo_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                powder_charge REAL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE engine_calibrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                slope REAL,
                intercept REAL,
                sample_count INTEGER,
                mse REAL,
                notes TEXT
            )
            """
        )
        self.conn.commit()


@pytest.mark.core
def test_calibrator_finds_linear_mapping():
    db = SimpleDB()
    cur = db.cursor

    # Create two ammo profiles with different charges
    cur.execute(
        "INSERT INTO ammo_profiles (name, powder_charge) VALUES (?, ?)", ("p1", 40.0)
    )
    ap1 = cur.lastrowid
    cur.execute(
        "INSERT INTO ammo_profiles (name, powder_charge) VALUES (?, ?)", ("p2", 44.0)
    )
    ap2 = cur.lastrowid

    # Fake engine with known scale and bias
    eng = FakeEngine(scale=1.05, bias=-4.0)

    # Create chronograph imports with measured velocities generated from engine but with some noise
    v1 = eng.predict_velocity(40.0) + 1.0
    v2 = eng.predict_velocity(44.0) - 0.5

    cur.execute(
        "INSERT INTO chronograph_imports (ammo_profile_id, velocity_avg, velocities_json) VALUES (?, ?, ?)",
        (ap1, v1, "[%.2f]" % v1),
    )
    id1 = cur.lastrowid
    cur.execute(
        "INSERT INTO chronograph_imports (ammo_profile_id, velocity_avg, velocities_json) VALUES (?, ?, ?)",
        (ap2, v2, "[%.2f]" % v2),
    )
    id2 = cur.lastrowid
    db.conn.commit()

    res = calibrator.calibrate_engine(db, eng, [id1, id2])
    assert res.get("ok") is True
    assert res.get("used") >= 2
    # slope should be near 1.0 (measured ~ predicted), intercept near 0 within some error
    assert abs(res.get("slope") - 1.0) < 0.2


@pytest.mark.core
def test_benchmark_engine_reports_metrics():
    db = SimpleDB()
    cur = db.cursor

    cur.execute(
        "INSERT INTO ammo_profiles (name, powder_charge) VALUES (?, ?)", ("p1", 40.0)
    )
    ap1 = cur.lastrowid
    cur.execute(
        "INSERT INTO ammo_profiles (name, powder_charge) VALUES (?, ?)", ("p2", 44.0)
    )
    ap2 = cur.lastrowid

    eng = FakeEngine(scale=1.01, bias=-2.0)

    v1 = eng.predict_velocity(40.0) + 2.0
    v2 = eng.predict_velocity(44.0) - 1.0

    cur.execute(
        "INSERT INTO chronograph_imports (ammo_profile_id, velocity_avg, velocities_json) VALUES (?, ?, ?)",
        (ap1, v1, "[%.2f]" % v1),
    )
    id1 = cur.lastrowid
    cur.execute(
        "INSERT INTO chronograph_imports (ammo_profile_id, velocity_avg, velocities_json) VALUES (?, ?, ?)",
        (ap2, v2, "[%.2f]" % v2),
    )
    id2 = cur.lastrowid
    db.conn.commit()

    res = calibrator.benchmark_engine(db, eng, [id1, id2])
    assert res.get("ok") is True
    assert res.get("used") == 2
    assert res.get("mae") is not None
    assert res.get("rmse") is not None
