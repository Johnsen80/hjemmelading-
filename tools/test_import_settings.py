import importlib
import sys
import traceback
from pathlib import Path

# Ensure the project root is on sys.path so package-style imports work
proj_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(proj_root))

try:
    importlib.import_module("HjemmeladingApp.ui.settings_dialog")
    print("SETTINGS_IMPORT_OK")
except Exception:
    traceback.print_exc()
    print("SETTINGS_IMPORT_FAIL")
