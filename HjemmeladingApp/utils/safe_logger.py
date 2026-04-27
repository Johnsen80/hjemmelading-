"""Small helper for safely appending diagnostics to the per-user debug log.

This module intentionally avoids raising exceptions so it is safe to call
from exception handlers during interpreter shutdown or when logging is
partially unavailable.
"""

from __future__ import annotations

import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional


def _get_log_dir(app_name: str = "Hjemmelading") -> Path:
    """Return a directory to store per-user logs.

    Attempts several fallbacks and never raises.
    """
    try:
        # Prefer the project's logging_config if available
        from src.logging_config import get_logger

        handler = get_logger(app_name).handlers[0]
        base_dir = getattr(handler, "baseDirectory", None)
        if not base_dir:
            base_filename = getattr(handler, "baseFilename", None)
            if base_filename:
                base_dir = str(Path(base_filename).parent)
        if base_dir:
            p = Path(base_dir)
            p.mkdir(parents=True, exist_ok=True)
            return p
    except Exception:
        pass

    # Try common OS locations
    try:
        local = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME")
        if local:
            p = Path(local) / app_name / "logs"
            p.mkdir(parents=True, exist_ok=True)
            return p
    except Exception:
        pass

    # Final fallback: a logs/ directory in cwd
    try:
        cwd = Path.cwd() / "logs"
        cwd.mkdir(parents=True, exist_ok=True)
        return cwd
    except Exception:
        return Path(".")


def get_debug_log_path(app_name: str = "Hjemmelading") -> Path:
    return _get_log_dir(app_name) / "debug_err.log"


def append_exception(
    msg: str = "", exc: Optional[BaseException] = None, app_name: str = "Hjemmelading"
) -> None:
    """Append an exception + message to the per-user debug log. Never raises."""
    try:
        p = get_debug_log_path(app_name)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(f"\n--- {msg} @ {datetime.now().isoformat()}Z ---\n")
            if exc is not None:
                fh.write(
                    "".join(
                        traceback.format_exception(type(exc), exc, exc.__traceback__)
                    )
                )
            else:
                fh.write(msg + "\n")
    except Exception:
        # Best-effort fallback to stderr; do not raise
        try:
            import sys

            sys.stderr.write(f"{msg}\n")
        except Exception:
            pass


def append_message(msg: str, app_name: str = "Hjemmelading") -> None:
    """Append a plain message to the per-user debug log. Never raises."""
    try:
        p = get_debug_log_path(app_name)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(f"\n--- {datetime.now().isoformat()}Z ---\n")
            fh.write(msg + "\n")
    except Exception:
        try:
            import sys

            sys.stderr.write(f"{msg}\n")
        except Exception:
            pass


def handle_suppressed(
    exc: Exception, source: str = "<unknown>", app_name: str = "Hjemmelading"
) -> None:
    """Central helper for modules to report suppressed exceptions safely.

    Tries `append_exception` and falls back to stderr; never raises.
    """
    try:
        append_exception(f"{source} suppressed exception", exc, app_name=app_name)
    except Exception:
        try:
            import sys

            try:
                sys.stderr.write(f"{source} suppressed exception: {exc}\n")
            except Exception:
                pass
        except Exception:
            pass


# Public API names
__all__ = [
    "get_debug_log_path",
    "append_exception",
    "append_message",
    "handle_suppressed",
]
