import importlib
import os
import sys
import time
import traceback
from pathlib import Path

# Ensure repo root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Use offscreen platform and Windows fonts
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

print("PROBE-INST: start", time.strftime("%H:%M:%S"))

try:
    print("PROBE-INST: importing PyQt6")
    print("PROBE-INST: PyQt6 ok")
except Exception as e:
    print("PROBE-INST: PyQt6 import failed:", e)
    traceback.print_exc()

mwmod = None
try:
    print("PROBE-INST: importing src.ui.main_window")
    t0 = time.time()
    mwmod = importlib.import_module("src.ui.main_window")
    t1 = time.time()
    print(f"PROBE-INST: imported src.ui.main_window in {t1-t0:.3f}s")
except Exception as e:
    print("PROBE-INST: import failed:", e)
    traceback.print_exc()

if not mwmod:
    print("PROBE-INST: module not available, exiting")
    sys.exit(2)

try:
    from PyQt6.QtWidgets import QApplication

    print("PROBE-INST: creating QApplication")
    app = QApplication([])
    print("PROBE-INST: QApplication created")
except Exception as e:
    print("PROBE-INST: QApplication creation failed:", e)
    traceback.print_exc()
    sys.exit(3)

try:
    # Mark onboarding as seen to avoid modal dialogs blocking headless startup
    from PyQt6.QtCore import QSettings

    try:
        s = QSettings("VALKYRIE", "Hjemmelading")
        s.setValue("onboarding_seen", True)
    except Exception:
        pass
except Exception:
    pass

if hasattr(mwmod, "MainWindow"):
    try:
        print("PROBE-INST: instantiating MainWindow")
        t0 = time.time()
        mw = mwmod.MainWindow()
        t1 = time.time()
        print(f"PROBE-INST: MainWindow instantiated in {t1-t0:.3f}s")
        try:
            mw.close()
        except Exception:
            pass
    except Exception as e:
        print("PROBE-INST: MainWindow instantiation failed:", e)
        traceback.print_exc()
        sys.exit(4)
else:
    print("PROBE-INST: MainWindow not found in module")

# Give Qt a moment to settle
time.sleep(0.5)
try:
    app.quit()
except Exception:
    pass
print("PROBE-INST: done", time.strftime("%H:%M:%S"))
