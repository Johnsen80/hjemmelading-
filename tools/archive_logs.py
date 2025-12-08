"""Archive old debug logs into `logs/` with a timestamp.

Run from project root using the project's Python:
  & .\.venv\Scripts\python.exe .\tools\archive_logs.py
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

# Ensure repo root is importable for `src` when running this helper directly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.logging_config import get_log_dir

# Archive any repo-root debug files into the per-user log directory
ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = Path(get_log_dir())
LOG_DIR.mkdir(parents=True, exist_ok=True)


def archive(fname: str):
    # Move repo-root file (if present) into per-user logs with UTC timestamp
    p = ROOT / fname
    if p.exists():
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dest = LOG_DIR / f"{p.stem}-{ts}{p.suffix}"
        try:
            shutil.move(str(p), str(dest))
            print(f"Archived {p.name} -> {dest}")
        except Exception as e:
            print(f"Failed to archive {p}: {e}")
    else:
        print(f"No {fname} in repo root to archive")


def main():
    archive("debug_err.log")
    archive("debug_app.log")


if __name__ == "__main__":
    main()
