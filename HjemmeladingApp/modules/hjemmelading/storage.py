from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def save_profile(data: Dict[str, Any], path: str | Path) -> None:
    """Save a profile dict as JSON to `path`.

    Raises OSError on I/O errors.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise OSError(f"Failed to save profile to {p}: {e}") from e


def load_profile(path: str | Path) -> Dict[str, Any]:
    """Load a profile JSON from `path` and return it as a dict.

    Raises FileNotFoundError if missing, ValueError for invalid JSON, and
    OSError for other I/O errors.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in profile {p}: {e}") from e
    except Exception as e:
        raise OSError(f"Failed to load profile {p}: {e}") from e
