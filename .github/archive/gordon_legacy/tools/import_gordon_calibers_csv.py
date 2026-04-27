"""
Import local Gordon caliber reference CSV into cartridge_standards.
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


DEFAULT_CSV = (
    PROJECT_ROOT / "data fra gordon" / "Data" / "gordon_calibers_reference.csv"
)
PROJECT_DB_PATH = PROJECT_ROOT / "data" / "reloading.db"


def safe_float(value: object) -> float | None:
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def main(argv: list[str]) -> int:
    csv_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_CSV
    if not csv_path.exists():
        print(f"Missing CSV: {csv_path}")
        return 2

    conn = sqlite3.connect(PROJECT_DB_PATH)
    cur = conn.cursor()
    imported = 0
    skipped = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            caliber_name = str(row.get("name") or "").strip()
            if not caliber_name:
                continue
            cur.execute(
                "SELECT id FROM cartridge_standards WHERE caliber_name = ?",
                (caliber_name,),
            )
            existing = cur.fetchone()
            if existing:
                skipped += 1
                continue
            payload = {
                "caliber_name": caliber_name,
                "standard_body": row.get("standard") or "GRT",
                "standard_label": row.get("standard") or "GRT",
                "max_pressure_bar": safe_float(row.get("max_pressure_bar")),
                "oal_mm": safe_float(row.get("oal_mm")),
                "case_length_mm": safe_float(row.get("case_length_mm")),
                "case_capacity_ml": safe_float(row.get("case_capacity_ml")),
                "bullet_diameter_mm": safe_float(row.get("bullet_diameter_mm")),
                "source": "Gordon local CSV",
                "source_kind": "readable_snapshot",
                "evidence_level": "reference",
                "notes": row.get("reference") or "",
            }
            columns = ", ".join(payload.keys())
            placeholders = ", ".join(["?"] * len(payload))
            cur.execute(
                f"INSERT INTO cartridge_standards ({columns}) VALUES ({placeholders})",
                tuple(payload.values()),
            )
            imported += 1

    conn.commit()
    conn.close()

    print(f"CSV: {csv_path}")
    print(f"DB: {PROJECT_DB_PATH}")
    print(f"Imported cartridge standards: {imported}")
    print(f"Skipped existing: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
