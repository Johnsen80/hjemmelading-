"""Compatibility shim for mode manager.

Some parts of the codebase import `src.modules.mode_manager`. If that module
is missing (for example when using the packaged `HjemmeladingApp.utils`),
this shim will try to forward the real implementation from
`HjemmeladingApp.utils.mode_manager`. If that isn't available either, a
conservative stub implementation is provided so imports don't fail and the
application can continue running.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    # Prefer the canonical implementation if present
    from HjemmeladingApp.utils.mode_manager import UserMode  # type: ignore
    from HjemmeladingApp.utils.mode_manager import UserModeManager
except Exception:
    # Provide a tiny safe fallback so imports succeed for editors/tests
    log = logging.getLogger(__name__)

    class UserMode:  # type: ignore[no-redef]
        BEGINNER = 0
        EXPERT = 1

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

        def is_beginner(self) -> bool:
            return getattr(self, "_mode", UserMode.BEGINNER) == UserMode.BEGINNER

        def set_mode(self, mode) -> None:
            self._mode = mode
            try:
                self.mode_changed.emit(mode)
            except Exception:
                log.exception("Error emitting mode_changed")


__all__ = ["UserModeManager", "UserMode"]
