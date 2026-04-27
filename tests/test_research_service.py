import json
import shutil
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from src.database.database import Database
from src.research.service import ResearchService

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".github" / "test_tmp"


@contextmanager
def _local_temp_dir():
    path = TEST_TMP_ROOT / f"research-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_session(db: Database) -> int:
    cur = db.cursor
    cur.execute(
        "INSERT INTO firearm (label, caliber, barrel_length_mm, twist, muzzle_device, muzzle_device_weight_g) VALUES (?, ?, ?, ?, ?, ?)",
        ("Test Rifle", "6.5 CM", 610, "1:8", "none", 0),
    )
    firearm_id = cur.lastrowid

    cur.execute(
        "INSERT INTO component_bullet (make, model, weight_gr, bc, diameter_mm) VALUES (?, ?, ?, ?, ?)",
        ("Hornady", "ELD-M", 140.0, 0.61, 6.71),
    )
    bullet_id = cur.lastrowid

    cur.execute(
        "INSERT INTO component_powder (make, name) VALUES (?, ?)",
        ("Hodgdon", "H4350"),
    )
    powder_id = cur.lastrowid

    cur.execute(
        "INSERT INTO component_primer (type, make, model) VALUES (?, ?, ?)",
        ("LR", "CCI", "BR-2"),
    )
    primer_id = cur.lastrowid

    cur.execute(
        "INSERT INTO component_case (make, model) VALUES (?, ?)",
        ("Lapua", "6.5 CM"),
    )
    case_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO load_recipe (
            firearm_id,
            bullet_id,
            powder_id,
            primer_id,
            case_id,
            case_firings,
            powder_charge_gr,
            col_mm,
            jump_mm,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            firearm_id,
            bullet_id,
            powder_id,
            primer_id,
            case_id,
            3,
            41.5,
            71.5,
            0.05,
            _utcnow(),
        ),
    )
    load_recipe_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO test_session (
            firearm_id,
            label,
            distance_m,
            temperature_c,
            chronograph_type,
            status,
            started_at,
            locked_at
        ) VALUES (?, ?, ?, ?, ?, 'draft', ?, NULL)
        """,
        (
            firearm_id,
            "Chrono import",
            100,
            15.0,
            "chronograph_import",
            _utcnow(),
        ),
    )
    session_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO test_result (
            test_session_id,
            load_recipe_id,
            shots_n,
            velocity_avg_mps,
            velocity_sd_mps,
            velocity_es_mps,
            group_size_mm,
            group_moa,
            pressure_signs_reported
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            session_id,
            load_recipe_id,
            3,
            820.0,
            4.2,
            12.0,
            None,
            None,
        ),
    )

    db.conn.commit()
    return session_id


@pytest.mark.core
def test_lock_session_enqueues_payload_when_opted_in():
    with _local_temp_dir() as tmpdir:
        db_path = tmpdir / "telemetry.db"
        database = Database(str(db_path))
        service = ResearchService(database)
        service.set_opt_in(True)

        session_id = _seed_session(database)
        service.lock_session(session_id)

        cur = database.conn.execute(
            "SELECT status, locked_at FROM test_session WHERE id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        assert row["status"] == "locked"
        assert row["locked_at"]

        outbox_rows = database.conn.execute(
            "SELECT payload_json, status FROM research_outbox"
        ).fetchall()
        assert len(outbox_rows) == 1
        payload = json.loads(outbox_rows[0]["payload_json"])
        assert payload["result"]["shots_n"] == 3
        assert payload["components"]["bullet"]["model"] == "ELD-M"
        assert outbox_rows[0]["status"] == "pending"

        database.close()


@pytest.mark.core
def test_lock_session_skips_outbox_when_opted_out():
    with _local_temp_dir() as tmpdir:
        db_path = tmpdir / "telemetry.db"
        database = Database(str(db_path))
        service = ResearchService(database)
        service.set_opt_in(False)

        session_id = _seed_session(database)
        service.lock_session(session_id)

        outbox_rows = database.conn.execute(
            "SELECT COUNT(1) FROM research_outbox"
        ).fetchone()
        assert outbox_rows[0] == 0

        cur = database.conn.execute(
            "SELECT status, locked_at FROM test_session WHERE id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        assert row["status"] == "locked"
        assert row["locked_at"]

        database.close()
