"""Small helper for safely appending diagnostics to the per-user debug log.

This module intentionally avoids raising exceptions so it is safe to call
from exception handlers during interpreter shutdown or when logging is
partially unavailable.
"""

from __future__ import annotations
import os
import traceback
from pathlib import Path
from typing import Optional


def _get_log_dir(app_name: str = "Hjemmelading") -> Path:
    try:
        # Prefer the project's logging_config if available
        from src.logging_config import get_log_dir as _gld

        p = Path(_gld(app_name))
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception as _suppressed_exc:
        # Fall back to LOCALAPPDATA or cwd
        try:
            local = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME")
            if local:
                p = Path(local) / app_name / "logs"
                p.mkdir(parents=True, exist_ok=True)
                return p
        except Exception as _suppressed_exc:
            pass
    try:
        cwd = Path.cwd() / "logs"
        cwd.mkdir(parents=True, exist_ok=True)
        return cwd
    except Exception as _suppressed_exc:
        return Path(".")


def get_debug_log_path(app_name: str = "Hjemmelading") -> Path:
    return _get_log_dir(app_name) / "debug_err.log"


def append_exception(
    msg: str = "", exc: Optional[BaseException] = None, app_name: str = "Hjemmelading"
) -> None:
    try:
        p = get_debug_log_path(app_name)
        with p.open("a", encoding="utf-8") as fh:
            from datetime import datetime

            fh.write(f"\n--- {msg} @ {datetime.utcnow().isoformat()}Z ---\n")
            if exc is not None:
                fh.write(
                    "".join(
                        traceback.format_exception(type(exc), exc, exc.__traceback__)
                    )
                )
            else:
                fh.write(msg + "\n")
    except Exception as _suppressed_exc:
        # Intentionally swallow all exceptions; logging must not raise
        try:
            # As a very last resort, write to stderr if available
            import sys

            sys.stderr.write(f"{msg}\n")
        except Exception as _suppressed_exc:
            pass


def append_message(msg: str, app_name: str = "Hjemmelading") -> None:
    try:
        p = get_debug_log_path(app_name)
        with p.open("a", encoding="utf-8") as fh:
            from datetime import datetime

            fh.write(f"\n--- {datetime.utcnow().isoformat()}Z ---\n")
            fh.write(msg + "\n")
    except Exception as _suppressed_exc:
        pass
