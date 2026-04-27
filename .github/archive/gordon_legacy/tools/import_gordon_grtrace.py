from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import Database  # noqa: E402
from src.modules.gordon_grtrace_import import import_grtrace_files  # noqa: E402

DEFAULT_GRTRACE_ROOT = PROJECT_ROOT / "data fra gordon"
PROJECT_DB_PATH = PROJECT_ROOT / "data" / "reloading.db"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_GRTRACE_ROOT))
    parser.add_argument("--include-doc-samples", action="store_true")
    args = parser.parse_args(argv[1:])

    root = Path(args.root)
    files = sorted(root.rglob("*.grtrace"))
    db = Database(db_path=str(PROJECT_DB_PATH))
    result = import_grtrace_files(
        db, files, include_documentation_samples=args.include_doc_samples
    )

    print(f"Root: {root}")
    print(f"Discovered .grtrace files: {len(files)}")
    print(f"Unique .grtrace files: {result.unique_files}")
    print(f"Documentation samples skipped: {result.documentation_samples_skipped}")
    print(f"Imported ammo profiles: {result.imported_profiles}")
    print(f"Reused ammo profiles: {result.reused_profiles}")
    print(f"Imported chronograph sessions: {result.imported_sessions}")
    print(f"Skipped existing sessions: {result.skipped_sessions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
