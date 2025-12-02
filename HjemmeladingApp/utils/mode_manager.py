"""Simple mode manager utility used by the UI.

This module provides `UserMode` and `UserModeManager` used across the
application. It is intentionally minimal and defensive so the UI can import
it reliably during tests or when packaging the app.
"""

from __future__ import annotations
import logging

log = logging.getLogger(__name__)


class UserMode:
    BEGINNER = 0
    EXPERT = 1


class _SimpleSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, fn):
        try:
            self._callbacks.append(fn)
        except Exception as e:
            log.exception("Failed to connect signal callback: %s", e)

    def emit(self, *args, **kwargs):
        for cb in list(self._callbacks):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                log.exception("Error in signal callback: %s", e)


class UserModeManager:
    """Minimal mode manager implementation.

    Methods:
    - `is_beginner()` -> bool
    - `set_mode(mode)` -> None (emits `mode_changed`)
    """

    def __init__(self) -> None:
        self.mode_changed = _SimpleSignal()
        self._mode = UserMode.BEGINNER

    def is_beginner(self) -> bool:
        return getattr(self, "_mode", UserMode.BEGINNER) == UserMode.BEGINNER

    def set_mode(self, mode) -> None:
        self._mode = mode
        try:
            self.mode_changed.emit(mode)
        except Exception as e:
            log.exception("Failed to emit mode_changed: %s", e)


__all__ = ["UserMode", "UserModeManager"]
