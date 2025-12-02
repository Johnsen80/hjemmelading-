from __future__ import annotations
import os
from pathlib import Path
import shutil
import uuid
import logging

# Optional GUI/image libraries for runtime previews
try:
    from PyQt6.QtGui import QPixmap

    _HAS_QT = True
except ImportError:
    QPixmap = None
    _HAS_QT = False

try:
    from PIL import Image

    _HAS_PIL = True
except ImportError:
    Image = None
    _HAS_PIL = False

logger = logging.getLogger(__name__)

MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = {"png", "jpeg", "gif", "bmp"}


def _get_appdata_dir() -> Path:
    ld = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if ld:
        return Path(ld) / "Hjemmelading"
    # fallback
    return Path.home() / ".local" / "share" / "Hjemmelading"


def ensure_backgrounds_dir() -> Path:
    d = _get_appdata_dir() / "backgrounds"
    try:
        d.mkdir(parents=True, exist_ok=True)
        return d
    except OSError:
        # Fall back to a local 'backgrounds' directory if AppData is unavailable
        try:
            fallback = Path.cwd() / "backgrounds"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        except OSError:
            # As a last resort, return the intended path object even if we couldn't create it.
            return d


def validate_image(path: str) -> tuple[bool, str]:
    p = Path(path)
    try:
        if not p.exists() or not p.is_file():
            return False, "File does not exist"
    except OSError:
        return False, "Unable to access file"
    size = p.stat().st_size
    if size > MAX_SIZE_BYTES:
        return False, f"File too large ({size} bytes > {MAX_SIZE_BYTES} bytes)"
    # Prefer Pillow for robust format detection when available.
    kind = None
    if _HAS_PIL:
        try:
            with Image.open(str(p)) as im:
                fmt = im.format
            if fmt:
                kind = fmt.lower()
        except (OSError, ValueError):
            kind = None

    # fall back to simple extension check if Pillow not present or detection failed
    if not kind:
        ext = p.suffix.lower().lstrip(".")
        if ext in ALLOWED_TYPES:
            kind = ext
        else:
            return False, "Unknown or unsupported image format"

    if kind.lower() not in ALLOWED_TYPES:
        return False, f"Image type '{kind}' is not supported"

    return True, kind


def save_background(src_path: str) -> str:
    """Validate and copy the user-selected image into the appdata backgrounds folder.

    Returns absolute path to the copied file.
    Raises ValueError on invalid input, or OSError on I/O errors.
    """
    ok, info = validate_image(src_path)
    if not ok:
        raise ValueError(info)
    kind = info
    ext = {
        "jpeg": ".jpg",
        "png": ".png",
        "gif": ".gif",
        "bmp": ".bmp",
    }.get(kind.lower(), Path(src_path).suffix or ".img")

    dest_dir = ensure_backgrounds_dir()
    unique = uuid.uuid4().hex
    dest_name = f"bg_{unique}{ext}"
    dest_path = dest_dir / dest_name
    try:
        shutil.copy2(src_path, dest_path)
        return str(dest_path)
    except PermissionError as e:
        raise OSError(f"Permission denied while copying background: {e}") from e
    except FileNotFoundError as e:
        raise OSError(f"Destination path not found: {e}") from e
    except OSError as e:
        # Bubble up OSError for the callers to handle uniformly
        raise OSError(f"Failed to save background: {e}") from e


def load_background_pixmap(path: str):
    """Attempt to load and return a QPixmap for `path` or None.

    This is a best-effort, non-raising helper used by UI code to show previews.
    If Qt is unavailable, returns None. Any exceptions are logged and swallowed.
    """
    try:
        if not path:
            return None
        if not os.path.exists(path):
            return None
    except OSError:
        return None

    if _HAS_QT:
        try:
            pix = QPixmap(path)
            if pix and not pix.isNull():
                return pix
        except (RuntimeError, TypeError) as _qt_err:
            try:
                logger.debug("QPixmap load failed: %s", _qt_err)
            except Exception as _suppressed_exc:
                pass

    # If Qt pixmap not available or failed, attempt a lightweight PIL verify
    if _HAS_PIL:
        try:
            with Image.open(path) as im:
                im.verify()
            return None
        except (OSError, ValueError) as _pil_err:
            try:
                logger.debug("PIL verify failed for %s: %s", path, _pil_err)
            except Exception as _suppressed_exc:
                pass
            return None

    return None


def get_background_preview(path: str):
    """Return a QPixmap preview when possible, otherwise None.

    This helper intentionally never raises; callers should handle None.
    """
    try:
        return load_background_pixmap(path)
    except Exception as _err:
        try:
            logger.exception("get_background_preview failed: %s", _err)
        except Exception as _suppressed_exc:
            pass
        return None
