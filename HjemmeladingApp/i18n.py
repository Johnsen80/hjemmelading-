"""Minimal i18n helper for the packaged app.

Provides a `set_language(lang_code)` function used by UI code. This is a
conservative implementation that won't fail if Qt isn't available during
headless tests; it stores a preference in QSettings when possible.
"""

from __future__ import annotations
import logging

log = logging.getLogger(__name__)


def set_language(lang_code: str) -> None:
    """Set application language.

    lang_code: 'no' for Norwegian, 'en' for English, etc. This function is
    intentionally minimal: it records the preferred language in QSettings if
    available, but otherwise is a no-op.
    """
    try:
        # Try to persist the language preference in QSettings if Qt is present
        try:
            from PyQt6.QtCore import QSettings  # type: ignore

            qs = QSettings("ReloadingWorkshop", "ReloadingManager")
            qs.setValue("language", "Norsk" if lang_code == "no" else "English")
        except Exception:
            # If Qt isn't available in this environment, swallow the error
            pass
    except Exception:
        log.exception("Failed to set language preference")


__all__ = ["set_language"]
