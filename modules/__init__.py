"""Compatibility shim so code/tests that import ``modules.*`` can resolve
the real package under ``HjemmeladingApp.modules`` when running tools from
the repository root.

This file is intentionally minimal and only used for static tools (mypy,
language servers) and test collection. It delegates at runtime to the real
package when available.
"""

from __future__ import annotations

import importlib
import types
from typing import Any

try:
    # Prefer the in-repo package
    pkg = importlib.import_module("HjemmeladingApp.modules")
    # Re-export submodules for convenience
    for attr in dir(pkg):
        if not attr.startswith("__"):
            globals()[attr] = getattr(pkg, attr)
except Exception:
    # Provide a minimal placeholder so imports succeed during static analysis
    # or when running tests/tools from a different CWD.
    class _Placeholder(types.ModuleType):
        pass

    placeholder: Any = _Placeholder("modules")
    globals().update({"hjemmelading": getattr(placeholder, "hjemmelading", None)})
