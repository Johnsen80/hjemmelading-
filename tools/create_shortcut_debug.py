"""Deprecated debug helper.

This file was used to create a desktop shortcut during development.
It's been archived to `tools/archive/create_shortcut_debug.py` after
verification. Leave this placeholder here to avoid accidental execution.

If you want to re-run the archived script, run:

    python tools/archive/create_shortcut_debug.py

Or remove this placeholder if you prefer the repo cleaned.
"""

from pathlib import Path


def info():
    p = Path(__file__).resolve()
    return {
        "status": "archived",
        "archived_path": str(p.parent.joinpath("archive", "create_shortcut_debug.py")),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(info(), indent=2, ensure_ascii=False))
