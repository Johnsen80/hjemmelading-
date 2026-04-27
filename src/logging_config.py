import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        return False

    probe = path / ".write_probe"
    try:
        with open(probe, "a", encoding="utf-8"):
            pass
        try:
            probe.unlink()
        except Exception:
            pass
        return True
    except Exception:
        try:
            # Best-effort cleanup if partial file got created.
            if probe.exists():
                probe.unlink()
        except Exception:
            pass
        return False


def _default_log_dir(app_name: str = "Hjemmelading") -> Path:
    """Return a Path to the per-user log directory (AppData on Windows).

    Falls back to the current working directory if the per-user path is unavailable.
    """
    # Prefer LOCALAPPDATA on Windows, otherwise use XDG or home
    local = os.getenv("LOCALAPPDATA") or os.getenv("XDG_STATE_HOME")
    if local:
        p = Path(local) / app_name / "logs"
    else:
        p = Path.home() / f".{app_name}" / "logs"
    try:
        if _is_writable_dir(p):
            return p
    except Exception:
        # Fallback to current working directory
        try:
            cwd = Path.cwd() / "logs"
            if _is_writable_dir(cwd):
                return cwd
        except Exception:
            return Path(".")

    # If the preferred location exists but is not writable (e.g. Windows policy),
    # use the current working directory logs folder instead.
    try:
        cwd = Path.cwd() / "logs"
        if _is_writable_dir(cwd):
            return cwd
    except Exception:
        pass

    return Path(".")


def configure_logging(
    level=logging.INFO, logfile: str | None = None, app_name: str = "Hjemmelading"
):
    """Configure logging for the application.

    Adds both console and rotating file handlers. By default writes into the
    per-user AppData/XDG state directory under `<app_name>/logs` and keeps
    a small number of backups.
    """
    logger = logging.getLogger()
    if logger.handlers:
        # already configured
        return

    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Determine logfile path
    if logfile:
        log_path = Path(logfile)
    else:
        d = _default_log_dir(app_name)
        log_path = d / "debug_app.log"

    try:
        # Rotating file handler: 5 MB per file, keep 5 backups
        fh = RotatingFileHandler(
            str(log_path), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.info("Logging configured. File: %s", str(log_path))
    except Exception as exc:
        # If file handler can't be created (often because the file is locked),
        # fall back to a unique filename so the app still gets file logs.
        if isinstance(exc, PermissionError):
            try:
                d = _default_log_dir(app_name)
                ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                pid = os.getpid()
                alt_path = d / f"debug_app.{pid}.{ts}.log"
                fh = RotatingFileHandler(
                    str(alt_path),
                    maxBytes=5 * 1024 * 1024,
                    backupCount=5,
                    encoding="utf-8",
                )
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(fmt)
                logger.addHandler(fh)
                logger.warning(
                    "File logging fallback enabled (original locked). File: %s",
                    str(alt_path),
                )
                return
            except Exception:
                # If fallback also fails, continue with console only.
                logger.error(
                    "Failed to create file logging handler (permission denied); continuing with console only: %s",
                    str(log_path),
                )
                return

        # Other failures: keep the traceback for diagnostics.
        logger.exception(
            "Failed to create file logging handler; continuing with console only"
        )


def get_logger(name: str):
    return logging.getLogger(name)


def get_log_dir(app_name: str = "Hjemmelading") -> str:
    """Return the per-user log directory path as a string.

    This is a thin wrapper around the internal helper so other modules
    can call it without importing pathlib directly.
    """
    p = _default_log_dir(app_name)
    try:
        return str(p)
    except Exception:
        return "."
