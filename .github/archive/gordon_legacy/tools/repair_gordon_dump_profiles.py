from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import Database  # noqa: E402
from tools.import_gordon_dumps import (  # noqa: E402
    _refresh_profile_from_parsed,
    parse_grtload_profile,
)

PROJECT_DB_PATH = PROJECT_ROOT / "data" / "reloading.db"


def main(argv: list[str]) -> int:
    db = Database(db_path=str(PROJECT_DB_PATH))
    repaired = 0
    scanned = 0
    for profile in db.get_all("ammo_profiles"):
        try:
            context = json.loads(profile.get("component_context_json") or "{}")
        except Exception:
            context = {}
        if str(context.get("source") or "") != "gordon_dump_import":
            continue
        source_file = str(context.get("source_file") or "")
        parsed = parse_grtload_profile(source_file)
        if not parsed:
            continue
        scanned += 1
        before_name = str(profile.get("name") or "")
        before_bullet_id = profile.get("bullet_id")
        before_powder_id = profile.get("powder_id")
        before_weight = profile.get("bullet_weight")
        refreshed = _refresh_profile_from_parsed(
            db, profile, parsed, {"source_file": source_file}
        )
        if (
            before_name != str(refreshed.get("name") or "")
            or before_bullet_id != refreshed.get("bullet_id")
            or before_powder_id != refreshed.get("powder_id")
            or before_weight != refreshed.get("bullet_weight")
        ):
            repaired += 1
            print(
                f"Repaired profile #{profile['id']}: {before_name} -> {refreshed.get('name')}"
            )
    print(f"Scanned dump profiles: {scanned}")
    print(f"Repaired dump profiles: {repaired}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
