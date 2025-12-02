import os
import sys
import importlib
import traceback

# Ensure parent of project root is on sys.path so package `HjemmeladingApp` resolves
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
PARENT = os.path.dirname(PROJECT_ROOT)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

# Use fully-qualified package names (module files expect package `HjemmeladingApp`)
modules = [
    "HjemmeladingApp.modules.user_profile",
    "HjemmeladingApp.ui.settings_dialog",
    "HjemmeladingApp.ui.profile_editor",
    "HjemmeladingApp.ui.customizer",
    "HjemmeladingApp.utils.safe_logger",
    "HjemmeladingApp.utils.backgrounds",
    "HjemmeladingApp.main",
]

results = {}
for m in modules:
    try:
        importlib.import_module(m)
        results[m] = ("OK", "")
    except Exception as _suppressed_exc:
        results[m] = ("ERROR", traceback.format_exc())

print("Import check results:")
for m, (status, tb) in results.items():
    print(f"- {m}: {status}")
    if status == "ERROR":
        print(tb)

# Exit with non-zero if any failures
if any(status == "ERROR" for status, _ in results.values()):
    sys.exit(1)
else:
    sys.exit(0)
