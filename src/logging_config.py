import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler


def _default_log_dir(app_name: str = "Hjemmelading") -> Path:
    """Return a Path to the per-user log directory (AppData on Windows).

    Falls back to the current working directory if the per-user path is unavailable.
    """
    # Prefer LOCALAPPDATA on Windows, otherwise use XDG or home
    local = os.getenv('LOCALAPPDATA') or os.getenv('XDG_STATE_HOME')
    if local:
        p = Path(local) / app_name / "logs"
    else:
        p = Path.home() / f".{app_name}" / "logs"
    try:
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        # Fallback to current working directory
        try:
            cwd = Path.cwd() / "logs"
            cwd.mkdir(parents=True, exist_ok=True)
            return cwd
        except Exception:
            return Path('.')


def configure_logging(level=logging.INFO, logfile: str | None = None, app_name: str = "Hjemmelading"):
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
        fh = RotatingFileHandler(str(log_path), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.info("Logging configured. File: %s", str(log_path))
    except Exception:
        # If file handler can't be created, continue with console only
        logger.exception("Failed to create file logging handler; continuing with console only")


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
        return '.'
