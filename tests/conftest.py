from __future__ import annotations

import os
from typing import Generator

import pytest

try:
    from PyQt6.QtWidgets import QApplication
except Exception:  # pragma: no cover - tests may run without PyQt available
    QApplication = None  # type: ignore


@pytest.fixture(scope="session", autouse=True)
def ensure_qapplication() -> Generator[None, None, None]:
    """Ensure a QApplication exists for tests that instantiate widgets.

    This fixture is autouse so GUI-related unit tests don't fail with
    "QWidget: Must construct a QApplication before a QWidget".
    It uses an offscreen platform if the environment variable is set.
    """
    if QApplication is None:
        yield
        return

    # If an app already exists, nothing to do
    app = QApplication.instance()
    if app is None:
        # Respect QT_QPA_PLATFORM if set by the test runner
        if "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
        # Point Qt at system fonts on Windows to avoid slow discovery/warnings.
        if os.name == "nt" and "QT_QPA_FONTDIR" not in os.environ:
            os.environ["QT_QPA_FONTDIR"] = r"C:\Windows\Fonts"
        _app = QApplication([])
        try:
            yield
        finally:
            # Do not call _app.quit() here; let process exit cleanly
            pass
    else:
        yield
