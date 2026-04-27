"""Simple mode manager utility used by the UI.

This module provides `UserMode` and `UserModeManager` used across the
application. It is intentionally minimal and defensive so the UI can import
it reliably during tests or when packaging the app.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from .qt_compat import QSettings

log = logging.getLogger(__name__)


class UserMode:
    BEGINNER = 0
    EXPERT = 1
    RESEARCH = 2


class _SimpleSignal:
    def __init__(self) -> None:
        self._callbacks: list[Callable[..., Any]] = []

    def connect(self, fn: Callable[..., Any]) -> None:
        try:
            self._callbacks.append(fn)
        except Exception as e:
            log.exception("Failed to connect signal callback: %s", e)

    def emit(self, *args: Any, **kwargs: Any) -> None:
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
        if QSettings is not None:
            try:
                val = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                    "ui/mode", "beginner"
                )
                if str(val).lower() == "expert":
                    self._mode = UserMode.EXPERT
                elif str(val).lower() == "research":
                    self._mode = UserMode.RESEARCH
            except Exception:
                pass

    def is_beginner(self) -> bool:
        return getattr(self, "_mode", UserMode.BEGINNER) == UserMode.BEGINNER

    def is_expert(self) -> bool:
        return getattr(self, "_mode", UserMode.BEGINNER) == UserMode.EXPERT

    def is_research(self) -> bool:
        return getattr(self, "_mode", UserMode.BEGINNER) == UserMode.RESEARCH

    def get_mode(self) -> int:
        return getattr(self, "_mode", UserMode.BEGINNER)

    def set_mode(self, mode) -> None:
        self._mode = mode
        if QSettings is not None:
            try:
                if mode == UserMode.RESEARCH:
                    val = "research"
                elif mode == UserMode.EXPERT:
                    val = "expert"
                else:
                    val = "beginner"
                QSettings("ReloadingWorkshop", "ReloadingManager").setValue(
                    "ui/mode", val
                )
            except Exception:
                pass
        try:
            self.mode_changed.emit(mode)
        except Exception as e:
            log.exception("Failed to emit mode_changed: %s", e)

    def get_ui_config(self) -> dict[str, bool]:
        """Return UI behavior flags based on current mode."""
        beginner = self.is_beginner()
        research = self.is_research()
        if beginner:
            return {
                "confirmation_dialogs": True,
                "show_tooltips": True,
                "show_help_text": True,
                "show_examples": True,
                "enable_shortcuts": False,
                "compact_layout": False,
                "wizard_mode": True,
                "detailed_errors": True,
                "research_mode": False,
            }
        if research:
            return {
                "confirmation_dialogs": False,
                "show_tooltips": False,
                "show_help_text": False,
                "show_examples": False,
                "enable_shortcuts": True,
                "compact_layout": True,
                "wizard_mode": False,
                "detailed_errors": True,
                "research_mode": True,
            }
        return {
            "confirmation_dialogs": False,
            "show_tooltips": False,
            "show_help_text": False,
            "show_examples": False,
            "enable_shortcuts": True,
            "compact_layout": True,
            "wizard_mode": False,
            "detailed_errors": False,
            "research_mode": False,
        }


__all__ = ["UserMode", "UserModeManager"]
