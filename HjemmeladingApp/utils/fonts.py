from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def resolve_bundled_fonts_dir() -> Path | None:
    """Resolve the bundled fonts directory if it exists."""
    env_dir = os.environ.get("VALKYRIE_FONTDIR")
    if env_dir:
        try:
            env_path = Path(env_dir)
            if env_path.exists():
                return env_path
        except Exception as e:
            log.debug("Invalid VALKYRIE_FONTDIR %s: %s", env_dir, e)

    candidates: list[Path] = []
    try:
        candidates.append(
            Path(__file__).resolve().parent.parent / "resources" / "fonts"
        )
    except Exception as e:
        log.debug("Could not resolve package fonts directory: %s", e)
    try:
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(
                Path(meipass) / "HjemmeladingApp" / "resources" / "fonts"
            )
            candidates.append(Path(meipass) / "resources" / "fonts")
    except Exception as e:
        log.debug("Could not resolve PyInstaller font dir: %s", e)

    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except Exception:
            continue
    return None


def ensure_qt_fontdir() -> Path | None:
    """Ensure QT_QPA_FONTDIR points at a valid font directory if available."""
    existing = os.environ.get("QT_QPA_FONTDIR")
    if existing:
        try:
            existing_path = Path(existing)
            if existing_path.exists():
                return existing_path
        except Exception as e:
            log.debug("Invalid QT_QPA_FONTDIR %s: %s", existing, e)

    fonts_dir = resolve_bundled_fonts_dir()
    if fonts_dir is not None:
        os.environ["QT_QPA_FONTDIR"] = str(fonts_dir)
        return fonts_dir

    if os.name == "nt":
        try:
            win_dir = Path(os.environ.get("WINDIR", r"C:\\Windows")) / "Fonts"
            if win_dir.exists():
                os.environ["QT_QPA_FONTDIR"] = str(win_dir)
                return win_dir
        except Exception as e:
            log.debug("Could not resolve Windows font dir: %s", e)

    return None


def register_bundled_fonts() -> int:
    """Register any .ttf files found under `resources/fonts/`.

    Returns the number of fonts successfully registered.
    Attempts to register with both Qt (QFontDatabase) and matplotlib's
    font manager so both Qt widgets and matplotlib can find glyphs.
    """
    try:
        fonts_dir = resolve_bundled_fonts_dir()
    except Exception as e:
        log.debug("Could not resolve fonts directory: %s", e)
        return 0

    if not fonts_dir:
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
                    log.exception(
                        "QFontDatabase.addApplicationFont failed for %s: %s", f, e
                    )
            # Matplotlib registration (if available)
            if mf is not None:
                try:
                    mf.fontManager.addfont(str(f))
                except Exception as e:
                    log.exception(
                        "matplotlib.font_manager.addfont failed for %s: %s", f, e
                    )
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
