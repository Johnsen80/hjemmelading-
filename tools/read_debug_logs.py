"""Print last 400 lines of debug_err.log and debug_app.log for quick diagnostics.

This helper prefers the per-user log directory set by the application.
"""
from pathlib import Path
import sys, os
# Ensure repo root is importable for `src` when running this helper directly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.logging_config import get_log_dir


def print_tail(path: Path, n: int = 400):
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
        print(f"--- {path} (last {n} lines) ---")
        for line in lines[-n:]:
            print(line)
    except Exception as e:
        print(f"Could not read {path}: {e}")


if __name__ == "__main__":
    log_dir = Path(get_log_dir())
    p_err = log_dir / 'debug_err.log'
    p_app = log_dir / 'debug_app.log'
    print_tail(p_err)
    print_tail(p_app)
