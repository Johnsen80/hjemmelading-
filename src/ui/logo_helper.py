import logging
from pathlib import Path
from typing import Optional

# Guard Qt imports so this module can be imported in headless/test environments
try:
    from ..qt_compat import QPixmap, Qt

    _HAS_QT = True
except Exception:
    QPixmap = None  # type: ignore
    _HAS_QT = False


def load_logo_pixmap(width: int | None = None) -> Optional[QPixmap]:
    """Load the project logo as a QPixmap.

    Looks for a `Logo/logo.png` file at the repository root. If found,
    returns a QPixmap (optionally scaled to `width` preserving aspect).
    Returns None if the file cannot be found or loaded or if Qt is
    unavailable in this environment.
    """
    try:
        tried = []
        # 1) repo-relative (source)
        base = Path(__file__).resolve().parents[2]
        logo_path = base / "Logo" / "logo.png"
        tried.append(logo_path)
        # 2) PyInstaller _MEIPASS (onefile)
        import sys

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            tried.append(Path(meipass) / "Logo" / "logo.png")
        # 3) executable-relative (one-dir/installed)
        try:
            exe_based = Path(sys.argv[0]).resolve().parent / "Logo" / "logo.png"
            tried.append(exe_based)
        except Exception:
            pass

        # Try all candidates
        found = None
        for p in tried:
            if p and p.exists():
                found = p
                break
        if not found:
            return None
        logo_path = found
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
