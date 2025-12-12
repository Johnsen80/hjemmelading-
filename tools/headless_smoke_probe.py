import faulthandler
import importlib
import os
import sys
import threading
import time as _time
import traceback
from pathlib import Path
from typing import Any, Optional

# Use offscreen by default for headless runs
os.environ["QT_QPA_PLATFORM"] = os.environ.get("QT_QPA_PLATFORM", "offscreen")
# Add repository root to sys.path dynamically so the probe can import `src`.
ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# Ensure Qt has a font directory in headless Windows environments to avoid
# expensive/missing font discovery which can block/processEvents during
# QApplication startup. Use system fonts as a sensible default on Windows.
try:
    if os.name == "nt":
        os.environ.setdefault(
            "QT_QPA_FONTDIR", os.environ.get("QT_QPA_FONTDIR", r"C:\\Windows\\Fonts")
        )
except Exception:
    pass

print("PROBE: start")

# Install faulthandler to ensure Python-level tracebacks on deadlock/crash
faulthandler.enable()


def _start_watchdog(timeout: float = 8.0):
    """Start a background watchdog that dumps all thread stacktraces
    if the probe hangs for longer than `timeout` seconds.
    """

    def _wd():
        _time.sleep(timeout)
        print(f"PROBE-WD: timeout after {timeout}s, dumping threads...", flush=True)
        try:
            import sys

            frames = sys._current_frames()
            for tid, frame in frames.items():
                print(f"\n--- Thread {tid} stack:\n", flush=True)
                traceback.print_stack(frame)
        except Exception:
            traceback.print_exc()
        try:
            # force exit so CI doesn't hang forever
            os._exit(3)
        except Exception:
            pass

    t = threading.Thread(target=_wd, daemon=True)
    t.start()


# 1: basic imports
try:
    print("PROBE: importing PyQt6")
    print("PROBE: PyQt6 imported")
except Exception as e:
    print("PROBE: PyQt6 import failed:", e)
    traceback.print_exc()

mwmod: Optional[Any] = None
try:
    print("PROBE: importing src.ui.main_window")
    mwmod = importlib.import_module("src.ui.main_window")
    print("PROBE: imported src.ui.main_window")
except Exception as e:
    print("PROBE: src.ui.main_window import failed:", e)
    traceback.print_exc()

# Monkeypatch heavy UI startup methods to safe no-ops in headless probe runs so
# instantiation won't trigger long-running dialogs, network calls, or complex
# tab/widget construction. This keeps the probe focused on import/creation.
if mwmod and hasattr(mwmod, "MainWindow"):
    try:
        print("PROBE: applying headless monkeypatches to MainWindow")

        def _noop(self, *a, **k):
            return None

        for name in (
            "init_ui",
            "apply_user_settings",
            "check_saved_workflows",
            "create_tabs",
            "close",
            "closeEvent",
        ):
            if hasattr(mwmod.MainWindow, name):
                try:
                    setattr(mwmod.MainWindow, name, _noop)
                    print(f"PROBE: patched MainWindow.{name}")
                except Exception:
                    print(f"PROBE: failed to patch MainWindow.{name}")
    except Exception:
        traceback.print_exc()

# 2: create QApplication
try:
    from PyQt6.QtWidgets import QApplication

    print("PROBE: creating QApplication")
    app = QApplication([])
    print("PROBE: QApplication created")
except Exception as e:
    print("PROBE: QApplication creation failed:", e)
    traceback.print_exc()

# 3: instantiate MainWindow
try:
    if mwmod and hasattr(mwmod, "MainWindow"):
        # Instantiate MainWindow in-process with heavy methods monkeypatched
        # to no-ops. This avoids spawning subprocesses on Windows which can
        # introduce bootstrap issues, while still preventing blocking
        # behaviour because the heavy work was patched earlier.
        print("PROBE: instantiating MainWindow (in-process)")
        try:
            try:
                mw = mwmod.MainWindow()
                print("PROBE: MainWindow instantiated")
            except Exception as e:
                print("PROBE: MainWindow instantiation raised:", e)
                traceback.print_exc()

            # Attempt to close and process events to ensure clean shutdown
            try:
                try:
                    _mw = locals().get("mw", None)
                    if _mw is not None:
                        _mw.close()
                except Exception:
                    pass
                _app = globals().get("app", None)
                if _app is not None:
                    try:
                        _app.processEvents()
                    except Exception:
                        pass
                    try:
                        _app.quit()
                    except Exception:
                        pass
                print("PROBE: MainWindow closed and QApplication quit")
            except Exception:
                traceback.print_exc()
        except Exception as e:
            print("PROBE: MainWindow instantiation failed:", e)
            traceback.print_exc()
    else:
        print("PROBE: MainWindow not found in module")
except Exception as e:
    print("PROBE: MainWindow instantiation failed:", e)
    traceback.print_exc()

# 4: optional matplotlib check
try:
    import matplotlib as mpl
    from matplotlib import font_manager as fm

    print("PROBE: matplotlib version", getattr(mpl, "__version__", "?"))
    try:
        ttflist = fm.fontManager.ttflist
        print("PROBE: matplotlib font count", len(ttflist))
    except Exception as e:
        print("PROBE: unable to query fontManager:", e)
except Exception as e:
    print("PROBE: matplotlib not available:", e)

print("PROBE: done")
