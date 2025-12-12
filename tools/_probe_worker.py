import sys
import traceback
from pathlib import Path

# Ensure repo root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Use offscreen if not already set
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication
    import importlib

    app = QApplication([])
    mwmod = importlib.import_module("src.ui.main_window")
    mw = mwmod.MainWindow()
    try:
        mw.close()
    except Exception:
        pass
    try:
        app.processEvents()
    except Exception:
        pass
    try:
        app.quit()
    except Exception:
        pass
    print("PROBE_WORKER: OK")
    sys.exit(0)
except Exception as e:
    print("PROBE_WORKER: FAILED:", e)
    traceback.print_exc()
    sys.exit(2)
