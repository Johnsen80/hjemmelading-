"""
Chronograph CSV import helpers.

Parses common CSV outputs from chronographs (simple CSV with a velocity column)
and stores an import summary in `chronograph_imports` table.
"""
from __future__ import annotations

import csv
import json
import statistics
from typing import List, Dict, Optional


def _extract_velocities_from_csv(path: str) -> List[float]:
    velocities: List[float] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = list(reader)

    if not rows:
        return velocities

    # Detect header row (if any). Look for a column containing 'vel' or 'velocity' or 'fps'
    header = None
    first = rows[0]
    lower = [c.strip().lower() for c in first]
    vel_idx: Optional[int] = None
    for i, col in enumerate(lower):
        if any(k in col for k in ("vel", "velocity", "fps")):
            vel_idx = i
            header = True
            break

    data_rows = rows[1:] if header else rows

    for r in data_rows:
        if not r:
            continue
        # If vel_idx known, try that column; otherwise scan for first numeric-looking value
        val = None
        if vel_idx is not None and len(r) > vel_idx:
            val = r[vel_idx].strip()
        else:
            # find first numeric token
            for tok in r:
                t = tok.strip().replace('"', '').replace("'", "")
                try:
                    float(t)
                    val = t
                    break
                except Exception:
                    continue

        if val is None:
            continue
        try:
            # Remove common units
            v = val.lower().replace("fps", "").replace("ft/s", "").strip()
            velocities.append(float(v))
        except Exception:
            continue

    return velocities


def summarize_velocities(velocities: List[float]) -> Dict:
    if not velocities:
        return {"count": 0, "avg": None, "es": None, "sd": None}
    avg = statistics.mean(velocities)
    es = max(velocities) - min(velocities)
    sd = statistics.stdev(velocities) if len(velocities) > 1 else 0.0
    return {"count": len(velocities), "avg": avg, "es": es, "sd": sd}


def import_chronograph_csv(db, file_path: str, ammo_profile_id: Optional[int] = None, note: Optional[str] = None) -> Dict:
    """
    Parse a chronograph CSV and persist an import summary in the database.

    Creates table `chronograph_imports` if missing and inserts the summary.
    Returns a dict with import id and stats.
    """
    velocities = _extract_velocities_from_csv(file_path)
    stats = summarize_velocities(velocities)

    cur = db.cursor
    # Create table if missing
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chronograph_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
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

    cur.execute(
        "INSERT INTO chronograph_imports (file_path, ammo_profile_id, velocity_count, velocity_avg, velocity_es, velocity_sd, velocities_json, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            file_path,
            ammo_profile_id,
            stats["count"],
            stats["avg"],
            stats["es"],
            stats["sd"],
            json.dumps(velocities),
            note,
        ),
    )
    db.conn.commit()
    import_id = cur.lastrowid
    return {"ok": True, "import_id": import_id, "stats": stats}


def import_velocities(db, velocities: List[float], ammo_profile_id: Optional[int] = None, note: Optional[str] = None) -> Dict:
    """
    Persist a list of velocities into `chronograph_imports` and return stats.
    """
    stats = summarize_velocities(velocities)
    cur = db.cursor
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chronograph_imports (
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

    cur.execute(
        "INSERT INTO chronograph_imports (file_path, ammo_profile_id, velocity_count, velocity_avg, velocity_es, velocity_sd, velocities_json, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            None,
            ammo_profile_id,
            stats["count"],
            stats["avg"],
            stats["es"],
            stats["sd"],
            json.dumps(velocities),
            note,
        ),
    )
    db.conn.commit()
    import_id = cur.lastrowid
    return {"ok": True, "import_id": import_id, "stats": stats}
