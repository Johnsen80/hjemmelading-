from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import Database  # noqa: E402
from src.modules.gordon_pressuretrace_import import (  # noqa: E402
    import_pressuretrace_grtloads,
)

DEFAULT_ROOT = PROJECT_ROOT / "data fra gordon" / "doku" / "en" / "faq" / "files"
PROJECT_DB_PATH = PROJECT_ROOT / "data" / "reloading.db"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    args = parser.parse_args(argv[1:])

    root = Path(args.root)
    files = sorted(root.glob("*.grtload"))
    db = Database(db_path=str(PROJECT_DB_PATH))
    result = import_pressuretrace_grtloads(db, files)
    print(f"Root: {root}")
    print(f"Discovered .grtload files: {len(files)}")
    print(f"PressureTrace sessions found: {result.sessions_found}")
    print(f"Profiles created: {result.profiles_created}")
    print(f"Profiles reused: {result.profiles_reused}")
    print(f"Sessions imported: {result.sessions_imported}")
    print(f"Sessions skipped: {result.sessions_skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
