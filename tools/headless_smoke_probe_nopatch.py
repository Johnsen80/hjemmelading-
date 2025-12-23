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
# Prefer a safe, well-supported style plugin to avoid platform plugin warnings
os.environ.setdefault(
    "QT_STYLE_OVERRIDE", os.environ.get("QT_STYLE_OVERRIDE", "fusion")
)
# Enable plugin debug output to help diagnose platform/icon engine issues
os.environ.setdefault("QT_DEBUG_PLUGINS", os.environ.get("QT_DEBUG_PLUGINS", "1"))
# Ensure Qt can find system fonts on Windows to avoid font discovery warnings
if os.name == "nt":
    os.environ.setdefault(
        "QT_QPA_FONTDIR", os.environ.get("QT_QPA_FONTDIR", r"C:\\Windows\\Fonts")
    )
# Add repository root to sys.path dynamically so the probe can import `src`.
ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

print("PROBE-NP: start (no monkeypatch)")

faulthandler.enable()


def _start_watchdog(timeout: float = 8.0):
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
            os._exit(3)
        except Exception:
            pass

    t = threading.Thread(target=_wd, daemon=True)
    t.start()


mwmod: Optional[Any] = None
try:
    print("PROBE-NP: importing src.ui.main_window")
    mwmod = importlib.import_module("src.ui.main_window")
    print("PROBE-NP: imported src.ui.main_window")
except Exception as e:
    print("PROBE-NP: src.ui.main_window import failed:", e)
    traceback.print_exc()

# Note: This variant intentionally DOES NOT monkeypatch MainWindow.

# 2: create QApplication
try:
    from PyQt6.QtWidgets import QApplication

    print("PROBE-NP: creating QApplication")
    app = QApplication([])
    print("PROBE-NP: QApplication created")
except Exception as e:
    print("PROBE-NP: QApplication creation failed:", e)
    traceback.print_exc()

# 3: instantiate MainWindow
try:
    if mwmod and hasattr(mwmod, "MainWindow"):
        print("PROBE-NP: instantiating MainWindow (in-process, no patch)")
        # Start watchdog to dump stacks if instantiation blocks
        _start_watchdog(8.0)
        try:
            try:
                mw = mwmod.MainWindow()
                print("PROBE-NP: MainWindow instantiated")
                try:
                    # Print top-level widget snapshots at 0s, 1s and 3s to
                    # detect delayed transient windows created after show.
                    from PyQt6.QtWidgets import QApplication

                    def _dump_snapshot(tag):
                        try:
                            app = QApplication.instance()
                            if not app:
                                return
                            tls = app.topLevelWidgets()
                            print(
                                f"PROBE-NP: snapshot {tag}: topLevelWidgets={len(tls)}"
                            )
                            for w in tls:
                                try:
                                    print(
                                        "  -",
                                        type(w).__name__,
                                        getattr(w, "objectName", lambda: "")(),
                                    )
                                except Exception:
                                    try:
                                        print("  -", type(w).__name__)
                                    except Exception:
                                        pass
                        except Exception:
                            pass

                    _dump_snapshot("0s")
                    import time as _time

                    _time.sleep(1)
                    _dump_snapshot("1s")
                    _time.sleep(2)
                    _dump_snapshot("3s")
                except Exception:
                    pass
            except Exception as e:
                print("PROBE-NP: MainWindow instantiation raised:", e)
                traceback.print_exc()

            try:
                _mw = locals().get("mw", None)
                if _mw is not None:
                    try:
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
                print("PROBE-NP: MainWindow closed and QApplication quit")
            except Exception:
                traceback.print_exc()
        except Exception as e:
            print("PROBE-NP: MainWindow instantiation failed:", e)
            traceback.print_exc()
    else:
        print("PROBE-NP: MainWindow not found in module")
except Exception as e:
    print("PROBE-NP: MainWindow instantiation failed:", e)
    traceback.print_exc()

print("PROBE-NP: done")
