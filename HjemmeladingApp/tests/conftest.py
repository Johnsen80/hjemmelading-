"""Pytest conftest for in-repo tests.

Ensure the package root (the `HjemmeladingApp` directory) is on `sys.path`
so imports like `modules.hjemmelading` resolve correctly during collection.
This is a small, safe test-only shim and can be removed once test import
layout is standardized.
"""

import os
import sys

# Insert the package root at front so tests import packages from the
# repository rather than relying on the external environment.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Provide a lightweight `modules` shim during test collection so imports
# like `from modules.hjemmelading import ...` resolve to
# `HjemmeladingApp.modules.hjemmelading` in the repository.
try:
    import importlib

    if "modules" not in sys.modules:
        _mod_pkg = importlib.import_module("HjemmeladingApp.modules")
        sys.modules.setdefault("modules", _mod_pkg)
except Exception:
    # Keep quiet - pytest will show the original ImportError if this fails.
    pass
import os
import sys

# Ensure project parent dir is on sys.path so tests can import package
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
PARENT = os.path.dirname(PROJECT_ROOT)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)
