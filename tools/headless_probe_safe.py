"""Lightweight headless probe that monkeypatches heavy startup methods.

Run from repo root with venv python. This avoids subprocess/workarounds and
prints concise status messages for quick triage.
"""

import os
import sys
import traceback
from pathlib import Path

# Headless defaults
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

print("SAFE_PROBE: start")

try:
    import importlib

    print("SAFE_PROBE: importing src.ui.main_window")
    mwmod = importlib.import_module("src.ui.main_window")
    print("SAFE_PROBE: imported main_window")

    # Instrument MainWindow.__init__ to log entry/exit for debugging hangs
    try:
        if hasattr(mwmod, "MainWindow") and hasattr(mwmod.MainWindow, "__init__"):
            _orig_init = mwmod.MainWindow.__init__

            def _wrapped_init(self, *a, **k):
                print("SAFE_PROBE: MainWindow.__init__ ENTER")
                try:
                    _orig_init(self, *a, **k)
                finally:
                    print("SAFE_PROBE: MainWindow.__init__ EXIT")

            mwmod.MainWindow.__init__ = _wrapped_init  # type: ignore[assignment]
            print("SAFE_PROBE: instrumented MainWindow.__init__")
    except Exception as e:
        print("SAFE_PROBE: failed to instrument MainWindow.__init__:", e)

    # Wrap create_tabs to time tab construction so we can spot slow module
    # initializers. Do not noop init/apply_user_settings here so we exercise
    # real startup paths.
    if hasattr(mwmod.MainWindow, "create_tabs"):
        try:
            _orig_create_tabs = mwmod.MainWindow.create_tabs

            def _timed_create_tabs(self, *a, **k):
                import time

                print("SAFE_PROBE: MainWindow.create_tabs START")
                t0 = time.time()
                try:
                    return _orig_create_tabs(self, *a, **k)
                finally:
                    print(
                        f"SAFE_PROBE: MainWindow.create_tabs END {time.time()-t0:.3f}s"
                    )

            mwmod.MainWindow.create_tabs = _timed_create_tabs  # type: ignore[assignment]
            print("SAFE_PROBE: wrapped MainWindow.create_tabs for timing")
        except Exception as e:
            print("SAFE_PROBE: failed to wrap create_tabs:", e)

    # Create application and instantiate
    from PyQt6.QtWidgets import QApplication

    print("SAFE_PROBE: creating QApplication")
    app = QApplication([])
    print("SAFE_PROBE: QApplication created")

    # Prevent modal dialogs from blocking the probe: make QDialog.exec a no-op.
    try:
        from PyQt6.QtWidgets import QDialog, QMessageBox

        def _no_block_exec(self, *a, **k):
            try:
                return 0
            except Exception:
                return 0

        try:
            QDialog.exec = _no_block_exec  # type: ignore[attr-defined]
            print("SAFE_PROBE: patched QDialog.exec to no-op")
        except Exception as e:
            print("SAFE_PROBE: failed to patch QDialog.exec:", e)

        try:
            # Some code may call QMessageBox.exec; patch defensively
            if hasattr(QMessageBox, "exec"):
                QMessageBox.exec = _no_block_exec  # type: ignore[attr-defined]
                print("SAFE_PROBE: patched QMessageBox.exec to no-op")
        except Exception as e:
            print("SAFE_PROBE: failed to patch QMessageBox.exec:", e)
    except Exception:
        # If PyQt widgets are unavailable or patching fails, continue (probe may still work)
        pass

    try:
        print("SAFE_PROBE: instantiating MainWindow")
        mw = mwmod.MainWindow()
        print("SAFE_PROBE: MainWindow instantiated")
    except Exception as e:
        print("SAFE_PROBE: MainWindow instantiation failed:", e)
        traceback.print_exc()

    # Close and process events
    # Try processing events for a short period to surface deferred callbacks
    try:
        import time

        print("SAFE_PROBE: processing events for up to 20s to observe deferred work")
        start = time.time()
        last_print = start
        while time.time() - start < 20.0:
            try:
                app.processEvents()
            except Exception:
                pass
            # print a heartbeat once per second
            now = time.time()
            if now - last_print >= 1.0:
                print(f"SAFE_PROBE: heartbeat {now - start:.1f}s")
                last_print = now
            time.sleep(0.05)
        print("SAFE_PROBE: event processing window complete")
    except Exception as e:
        print("SAFE_PROBE: error during event processing loop:", e)
        traceback.print_exc()

    try:
        _mw = locals().get("mw", None)
        if _mw is not None:
            try:
                _mw.close()
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
        print("SAFE_PROBE: clean shutdown OK")
    except Exception as e:
        print("SAFE_PROBE: error during shutdown:", e)
        traceback.print_exc()
except Exception as e:
    print("SAFE_PROBE: fatal error:", e)
    traceback.print_exc()

print("SAFE_PROBE: done")
