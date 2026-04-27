from __future__ import annotations

import os
import sys
from types import ModuleType


def _candidate_order() -> list[str]:
    env_choice = (
        os.environ.get("HJEMMELADING_QT_API") or os.environ.get("QT_API") or ""
    ).strip()
    if env_choice in {"PyQt6", "PySide6"}:
        other = "PySide6" if env_choice == "PyQt6" else "PyQt6"
        return [env_choice, other]

    loaded: list[str] = []
    for name in ("PyQt6", "PySide6"):
        if name in sys.modules:
            loaded.append(name)
    if loaded:
        return loaded + [name for name in ("PyQt6", "PySide6") if name not in loaded]

    return ["PyQt6", "PySide6"]


def _import_binding() -> tuple[str, ModuleType, ModuleType, ModuleType]:
    last_error: Exception | None = None
    for name in _candidate_order():
        try:
            qt_core = __import__(f"{name}.QtCore", fromlist=["QtCore"])
            qt_gui = __import__(f"{name}.QtGui", fromlist=["QtGui"])
            qt_widgets = __import__(f"{name}.QtWidgets", fromlist=["QtWidgets"])
            return name, qt_core, qt_gui, qt_widgets
        except Exception as exc:
            last_error = exc
    raise RuntimeError("Neither PyQt6 nor PySide6 could be imported") from last_error


BINDING, QtCore, QtGui, QtWidgets = _import_binding()

QSettings = getattr(QtCore, "QSettings", None)
QPixmap = getattr(QtGui, "QPixmap", None)
QFontDatabase = getattr(QtGui, "QFontDatabase", None)

__all__ = [
    "BINDING",
    "QFontDatabase",
    "QPixmap",
    "QSettings",
    "QtCore",
    "QtGui",
    "QtWidgets",
]
