"""Test/runtime bootstrap for local runs.

This file is intentionally minimal and only affects local interpreter
startup (including pytest). It ensures the repository package root is
on `sys.path` and provides a lightweight top-level `modules` shim that
points at `HjemmeladingApp.modules` so legacy imports like
`import modules.hjemmelading` continue to work during tests.

Keep changes here conservative — it's a test/runtime shim, not part of
the application API.
"""

import importlib
import os
import sys

# Ensure the package root (the directory containing this file) is on sys.path
_REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Provide a minimal top-level `modules` package proxy to
# `HjemmeladingApp.modules` for older import paths used in tests.
try:
    if "modules" not in sys.modules:
        _pkg = importlib.import_module("HjemmeladingApp.modules")
        sys.modules.setdefault("modules", _pkg)
except Exception:
    # Keep this quiet — if importing the internal package fails,
    # tests will surface the original ImportError. We don't want the
    # shim to raise during interpreter startup.
    pass
