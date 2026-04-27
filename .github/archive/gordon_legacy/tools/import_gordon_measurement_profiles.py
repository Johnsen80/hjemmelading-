from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import Database  # noqa: E402
from src.modules.gordon_measurement_import import (  # noqa: E402
    build_import_rows,
    import_measurement_profiles,
)

DEFAULT_DATA_DIR = PROJECT_ROOT / "data fra gordon" / "Data"
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "data" / "gordon_temp_extract"
PROJECT_DB_PATH = PROJECT_ROOT / "data" / "reloading.db"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--db-path", default=str(PROJECT_DB_PATH))
    parser.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR))
    parser.add_argument("--import-db", action="store_true")
    parser.add_argument("--seed-grt-data", action="store_true")
    args = parser.parse_args(argv[1:])

    data_dir = Path(args.data_dir)
    export_dir = Path(args.export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    db = Database(db_path=args.db_path)

    preview_rows, preview_stats = build_import_rows(data_dir, db)
    export_payload = []
    for row in preview_rows:
        record = dict(row["data"])
        context = row["data"].get("component_context_json")
        record["component_context_json"] = (
            json.loads(context) if isinstance(context, str) else context
        )
        export_payload.append(record)

    export_path = export_dir / "gordon_ammo_profile_candidates.json"
    export_path.write_text(
        json.dumps(export_payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Data dir: {data_dir}")
    print(f"Grouped profiles: {preview_stats.grouped_profiles}")
    print(f"Bullet matches: {preview_stats.matched_bullets}")
    print(f"Powder matches: {preview_stats.matched_powders}")
    print(f"Candidate export: {export_path}")

    if args.import_db:
        stats, _ = import_measurement_profiles(
            data_dir, db, import_grt_seed=args.seed_grt_data
        )
        print(f"Inserted ammo profiles: {stats.inserted_profiles}")
        print(f"Updated ammo profiles: {stats.updated_profiles}")
        print(f"Missing bullet matches: {stats.missing_bullets}")
        print(f"Missing powder matches: {stats.missing_powders}")
        if args.seed_grt_data:
            print("Seeded grt_data from measurement averages: yes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
