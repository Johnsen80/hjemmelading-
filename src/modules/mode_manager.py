"""Compatibility shim for mode manager.

Some parts of the codebase import `src.modules.mode_manager`. If that module
is missing (for example when using the packaged `HjemmeladingApp.utils`),
this shim will try to forward the real implementation from
`HjemmeladingApp.utils.mode_manager`. If that isn't available either, a
conservative stub implementation is provided so imports don't fail and the
application can continue running.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

try:
    # Prefer the canonical implementation if present
    _mode_manager_module = importlib.import_module("HjemmeladingApp.utils.mode_manager")
    UserMode = getattr(_mode_manager_module, "UserMode")  # type: ignore
    UserModeManager = getattr(_mode_manager_module, "UserModeManager")
except Exception:
    # Provide a tiny safe fallback so imports succeed for editors/tests
    log = logging.getLogger(__name__)

    class UserMode:  # type: ignore[no-redef]
        BEGINNER = 0
        EXPERT = 1
        RESEARCH = 2

    class _StubSignal:
        def __init__(self) -> None:
            self._callbacks: list[Any] = []

        def connect(self, fn: Any) -> None:
            self._callbacks.append(fn)

        def emit(self, *args: Any, **kwargs: Any) -> None:
            for cb in list(self._callbacks):
                try:
                    cb(*args, **kwargs)
                except Exception:
                    log.exception("Error in mode change callback")

    class UserModeManager:  # type: ignore[no-redef]
        """Minimal replacement for the real mode manager.

        Only implements the small surface area required by the UI tests:
        - `mode_changed` signal-like object with `connect`/`emit`
        - `is_beginner()` and `set_mode(mode)` methods
        """

        def __init__(self) -> None:
            self.mode_changed = _StubSignal()
            self._mode = UserMode.BEGINNER
            try:
                from PyQt6.QtCore import QSettings

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

        def get_mode(self):
            return getattr(self, "_mode", UserMode.BEGINNER)

        def set_mode(self, mode) -> None:
            self._mode = mode
            try:
                from PyQt6.QtCore import QSettings

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
            except Exception:
                log.exception("Error emitting mode_changed")

        def get_ui_config(self) -> dict[str, bool]:
            beginner = self.is_beginner()
            research = self.is_research()
            return {
                "confirmation_dialogs": beginner,
                "show_tooltips": beginner,
                "enable_shortcuts": not beginner,
                "wizard_mode": beginner,
                "research_mode": research,
                "show_help_text": beginner,
                "show_examples": beginner,
                "compact_layout": not beginner,
            }


__all__ = ["UserModeManager", "UserMode"]
