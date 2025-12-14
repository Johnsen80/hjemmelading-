"""Test helper: ensure a QApplication exists early during pytest runs.

This module is imported by Python's site machinery if present on sys.path.
It creates a headless Qt application (offscreen) when PyQt6 is available so
tests that import GUI modules at import-time don't fail with
"QWidget: Must construct a QApplication before a QWidget".

This file is intentionally lightweight and only affects local/test runs.
"""

from __future__ import annotations

import os

try:
    # Set offscreen platform if not explicitly set
    if "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    from PyQt6.QtWidgets import QApplication

    try:
        # Create a single application instance if none exists
        if QApplication.instance() is None:
            QApplication([])
    except Exception:
        # Be tolerant: if Qt cannot be initialized in this environment,
        # tests that require it will either skip or fail in a useful way.
        pass
except Exception:
    # PyQt6 not installed or other import errors - ignore.
    pass
