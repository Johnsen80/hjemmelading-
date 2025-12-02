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
    except Exception as e:
        log.debug("Could not resolve fonts directory: %s", e)
        return 0

    if not fonts_dir.exists():
        return 0

    added = 0
    # Lazy imports so this module can be imported in non-Qt environments
    try:
        from PyQt6.QtGui import QFontDatabase
    except Exception as e:
        log.debug("PyQt6.QtGui.QFontDatabase import failed: %s", e)
        QFontDatabase = None  # type: ignore

    try:
        import matplotlib.font_manager as mf
    except Exception as e:
        log.debug("matplotlib.font_manager import failed: %s", e)
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
                except Exception as e:
                    log.exception("QFontDatabase.addApplicationFont failed for %s: %s", f, e)
            # Matplotlib registration (if available)
            if mf is not None:
                try:
                    mf.fontManager.addfont(str(f))
                except Exception as e:
                    log.exception("matplotlib.font_manager.addfont failed for %s: %s", f, e)
            added += 1
        except Exception as e:
            log.exception("Failed to register font %s: %s", f, e)
    # Rebuild matplotlib font cache if possible
    try:
        if mf is not None:
            try:
                mf._rebuild()
            except Exception as e:
                # If private API not present, ignore
                log.debug("matplotlib _rebuild skipped: %s", e)
    except Exception as e:
        log.debug("Error while attempting matplotlib rebuild: %s", e)

    return added
