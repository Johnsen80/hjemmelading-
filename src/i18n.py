"""Compatibility shim for i18n.

The application imports `src.i18n.set_language`; prefer the packaged
`HjemmeladingApp.i18n` module if available, otherwise provide a safe stub.
"""
from __future__ import annotations
import logging

log = logging.getLogger(__name__)

try:
    # Prefer the application-provided implementation
    from HjemmeladingApp.i18n import set_language  # type: ignore
except Exception:
    def set_language(lang_code: str) -> None:
        """Fallback no-op implementation used during tests or when Qt is absent."""
        try:
            log.debug("set_language called with %s (stub)", lang_code)
        except Exception:
            pass


__all__ = ["set_language"]
