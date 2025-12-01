from __future__ import annotations
from pathlib import Path
import logging

log = logging.getLogger(__name__)


def register_bundled_fonts() -> int:
    """Register any .ttf files found under `resources/fonts/`.

    Returns the number of fonts successfully registered.
    Attempts to register with both Qt (QFontDatabase) and matplotlib's
    font manager so both Qt widgets and matplotlib can find glyphs.
    """
    try:
        fonts_dir = Path(__file__).resolve().parent.parent / "resources" / "fonts"
    except Exception:
        return 0

    if not fonts_dir.exists():
        return 0

    added = 0
    # Lazy imports so this module can be imported in non-Qt environments
    try:
        from PyQt6.QtGui import QFontDatabase
    except Exception:
        QFontDatabase = None  # type: ignore

    try:
        import matplotlib.font_manager as mf
    except Exception:
        mf = None

    for f in sorted(fonts_dir.glob("*.ttf")):
        try:
            # Qt registration (if available)
            if QFontDatabase is not None:
                try:
                    res = QFontDatabase.addApplicationFont(str(f))
                    if res == -1:
                        # addApplicationFont may return -1 for failure
                        log.debug("QFontDatabase failed to add %s", f)
                    else:
                        log.debug("QFontDatabase added %s -> id %s", f, res)
                except Exception:
                    log.exception("QFontDatabase.addApplicationFont failed for %s", f)
            # Matplotlib registration (if available)
            if mf is not None:
                try:
                    mf.fontManager.addfont(str(f))
                except Exception:
                    log.exception("matplotlib.font_manager.addfont failed for %s", f)
            added += 1
        except Exception:
            log.exception("Failed to register font %s", f)
    # Rebuild matplotlib font cache if possible
    try:
        if mf is not None:
            try:
                mf._rebuild()
            except Exception:
                # If private API not present, ignore
                pass
    except Exception:
        pass

    return added
