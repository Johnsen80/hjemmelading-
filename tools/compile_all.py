"""Compile all .py files under the workspace and report syntax/runtime compile errors.
Usage: python tools/compile_all.py
"""

import os
import py_compile
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
errors = []
for dirpath, dirnames, filenames in os.walk(root):
    # skip venv and build dirs
    if any(
        x in dirpath
        for x in (
            os.path.sep + ".venv",
            os.path.sep + "build",
            os.path.sep + "dist",
            os.path.sep + "node_modules",
        )
    ):
        continue
    for fn in filenames:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(dirpath, fn)
        try:
            py_compile.compile(path, doraise=True)
        except Exception as e:
            errors.append((path, repr(e)))

if not errors:
    print("OK: no syntax errors found")
    sys.exit(0)

print("Found errors in the following files:")
for p, e in errors:
    print(p)
    print("  ", e)

sys.exit(2)
