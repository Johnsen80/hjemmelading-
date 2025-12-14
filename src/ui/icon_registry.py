from pathlib import Path
from typing import TYPE_CHECKING, Optional

_ROOT = Path(__file__).resolve().parents[1]
_ICON_DIR = _ROOT / "images" / "icons"

# Guard Qt imports so this module is safe to import in headless/test envs
try:
    from PyQt6.QtGui import QIcon, QPixmap

    _HAS_QT = True
except Exception:
    QIcon = None  # type: ignore
    QPixmap = None  # type: ignore
    _HAS_QT = False


if TYPE_CHECKING:
    # Provide QIcon typing for static analysis without importing Qt at runtime
    from PyQt6.QtGui import QIcon  # pragma: no cover - typing only


def get_icon(name: str) -> Optional["QIcon"]:
    """Return a QIcon for the given logical icon name or None.

    If Qt is not available (headless/test), returns None. Tries common
    extensions and prefers creating a `QIcon` directly from path.
    """
    if not _HAS_QT:
        return None

    for ext in ("svg", "png", "ico"):
        p = _ICON_DIR / f"{name}.{ext}"
        if p.exists():
            # Try to construct a QIcon directly from path (supports SVG/PNG)
            try:
                return QIcon(str(p))
            except Exception:
                # As a fallback try loading via QPixmap
                try:
                    pix = QPixmap(str(p))
                    return QIcon(pix)
                except Exception:
                    return None
    return None
