from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "reloading.db"
EXPORT_DIR = PROJECT_ROOT / "data" / "gordon_temp_extract"
QUALITY_JSON = EXPORT_DIR / "gordon_data_quality_report.json"
QUALITY_TOOL = PROJECT_ROOT / "tools" / "gordon_data_quality_report.py"
STATUS_TOOL = PROJECT_ROOT / "tools" / "gordon_status_report.py"


def load_quality_report() -> dict[str, object]:
    if not QUALITY_JSON.exists():
        raise FileNotFoundError(f"Missing quality report: {QUALITY_JSON}")
    return json.loads(QUALITY_JSON.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete documentation/sample rows.",
    )
    args = parser.parse_args(argv)

    report = load_quality_report()
    session_ids = sorted(
        {int(row["id"]) for row in report.get("documentation_sessions") or []}
    )
    profile_ids = sorted(
        {int(row["id"]) for row in report.get("documentation_profiles") or []}
    )
    grt_ids = sorted(
        {int(row["id"]) for row in report.get("documentation_grt_rows") or []}
    )

    print(f"documentation_profiles: {len(profile_ids)} -> {profile_ids}")
    print(f"documentation_sessions: {len(session_ids)} -> {session_ids}")
    print(f"documentation_grt_rows: {len(grt_ids)} -> {grt_ids}")

    if not args.apply:
        print("Dry run only. Use --apply to delete the rows above.")
        return 0

    conn = sqlite3.connect(DB_PATH)
    try:
        if session_ids:
            placeholders = ",".join("?" for _ in session_ids)
            conn.execute(
                f"DELETE FROM chronograph_readings WHERE session_id IN ({placeholders})",
                session_ids,
            )
            conn.execute(
                f"DELETE FROM chronograph_sessions WHERE id IN ({placeholders})",
                session_ids,
            )
        if grt_ids:
            placeholders = ",".join("?" for _ in grt_ids)
            conn.execute(f"DELETE FROM grt_data WHERE id IN ({placeholders})", grt_ids)
        if profile_ids:
            placeholders = ",".join("?" for _ in profile_ids)
            conn.execute(
                f"DELETE FROM ammo_profiles WHERE id IN ({placeholders})", profile_ids
            )
        conn.commit()
    finally:
        conn.close()

    subprocess.run([sys.executable, str(QUALITY_TOOL)], check=False)
    subprocess.run([sys.executable, str(STATUS_TOOL)], check=False)
    print("Cleanup applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
