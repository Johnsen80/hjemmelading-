from pathlib import Path
import logging

# Guard Qt imports so this module can be imported in headless/test environments
try:
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtCore import Qt
    _HAS_QT = True
except Exception:
    QPixmap = None  # type: ignore
    _HAS_QT = False


def load_logo_pixmap(width: int | None = None):
    """Load the project logo as a QPixmap.

    Looks for a `Logo/logo.png` file at the repository root. If found,
    returns a QPixmap (optionally scaled to `width` preserving aspect).
    Returns None if the file cannot be found or loaded or if Qt is
    unavailable in this environment.
    """
    try:
        base = Path(__file__).resolve().parents[2]
        logo_path = base / "Logo" / "logo.png"
        if not logo_path.exists():
            return None
        if not _HAS_QT:
            # Qt not available (tests/headless). Don't raise — caller should
            # gracefully handle a missing pixmap.
            return None
        pix = QPixmap(str(logo_path))
        if pix.isNull():
            return None
        if width is not None and width > 0:
            # Use the Qt enum for transformation mode (PyQt6 expects the enum)
            pix = pix.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
        return pix
    except Exception:
        logging.exception("Failed to load logo pixmap")
        return None
