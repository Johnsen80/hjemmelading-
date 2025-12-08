"""Bootstrap helper used by small scripts to ensure repo root is importable.

Usage: at top of scripts that `import src` call `import tools.bootstrap as _b; _b.ensure_repo_root()`
"""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_repo_root():
    """Ensure the repository root (the folder containing this tools/ directory)
    is on sys.path so `import src` works when running scripts from project.
    """
    try:
        this = Path(__file__).resolve()
        repo_root = this.parent.parent
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)
    except Exception:
        # best-effort only
        pass


if __name__ == "__main__":
    ensure_repo_root()
    print("Repo root ensured in sys.path")
