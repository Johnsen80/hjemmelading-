"""Check importability of all Python modules under src/ by importing
each module in a separate subprocess to isolate failures.

Usage: run from repo root with project Python:
  ./.github/.tool-venv/Scripts/python.exe tools/check_src_imports.py
"""

import glob
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(ROOT, "src")

py_files = [p for p in glob.glob(os.path.join(SRC_ROOT, "**", "*.py"), recursive=True)]
modules = []
for p in py_files:
    rel = os.path.relpath(p, ROOT)
    # derive module name: src/package/module.py -> src.package.module (strip .py)
    mod = rel[:-3].replace(os.path.sep, ".")
    modules.append((p, mod))

errors = []
print(f"Checking {len(modules)} modules under src/...")
for path, mod in modules:
    # skip __main__ style or test scripts that are not importable if desired
    # run import in separate process to avoid side effects
    # Ensure the subprocess can import the local `src` package by inserting
    # the repository root onto sys.path before importing.
    cmd = [
        sys.executable,
        "-c",
        (
            f"import os, sys; os.environ.setdefault('QT_QPA_PLATFORM','offscreen');"
            f"sys.path.insert(0, {repr(ROOT)}); import {mod}"
        ),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except Exception as e:
        errors.append((mod, str(e), ""))
        print(f"ERROR importing {mod}: {e}")
        continue
    if proc.returncode != 0:
        errors.append((mod, proc.returncode, proc.stderr.strip()[:2000]))
        print(f"FAILED import {mod} -> returncode={proc.returncode}")
    else:
        print(f"OK {mod}")

print("\nSummary:")
if not errors:
    print("All modules imported successfully")
else:
    print(f"{len(errors)} modules failed to import:")
    for mod, code, err in errors:
        print("---", mod)
        print(err)
