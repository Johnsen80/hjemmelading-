import faulthandler
import os
import sys
import threading
import time
import traceback

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

_WATCHDOG_SECONDS = int(os.environ.get("HEADLESS_SMOKE_TIMEOUT", "15"))


def _start_watchdog(timeout_seconds: int) -> None:
    if os.environ.get("HEADLESS_SMOKE_DISABLE_WATCHDOG", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return

    def _watchdog() -> None:
        time.sleep(timeout_seconds)
        print(
            f"HEADLESS_SMOKE: timeout after {timeout_seconds}s, dumping threads",
            flush=True,
        )
        try:
            faulthandler.dump_traceback(file=sys.stderr)
        except Exception:
            pass
        os._exit(3)

    threading.Thread(target=_watchdog, daemon=True).start()


def _should_skip_mainwindow() -> bool:
    if os.environ.get("HEADLESS_SMOKE_RUN_MAINWINDOW", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    qp = os.environ.get("QT_QPA_PLATFORM", "").lower()
    if qp in ("offscreen", "minimal"):
        return True
    if os.environ.get("HEADLESS", "").lower() in ("1", "true", "yes"):
        return True
    return False


# Ensure repo root on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
print("HEADLESS_SMOKE: start")
faulthandler.enable()
_start_watchdog(_WATCHDOG_SECONDS)
try:
    # Install a Qt message handler to filter noisy font-directory warnings
    try:
        # qInstallMessageHandler is available in PyQt6.QtCore
        from PyQt6.QtCore import qInstallMessageHandler

        def _qt_message_handler(msg_type, context, message):
            try:
                text = str(message)
            except Exception:
                text = message
            # Filter the specific QFontDatabase warning about missing Qt fonts
            if "Cannot find font directory" in text or "Qt no longer ships fonts" in text:
                return
            # Otherwise forward to stderr
            try:
                stderr = sys.__stderr__ if sys.__stderr__ is not None else sys.stderr
                if stderr is not None:
                    stderr.write(str(message) + "\n")
            except Exception:
                pass

        qInstallMessageHandler(_qt_message_handler)
    except Exception:
        # If Qt isn't importable or qInstallMessageHandler unavailable, ignore
        pass
    # Try to import QtWebEngine early (it must be imported before a Q(Core)Application
    # is created in some environments). If not available, ensure we set the
    # AA_ShareOpenGLContexts attribute on QApplication before instantiation.
    try:
        import PyQt6.QtWebEngineWidgets  # noqa: F401

        print("HEADLESS_SMOKE: QtWebEngineWidgets imported (PyQt6.QtWebEngineWidgets)")
    except Exception as e:
        try:
            from PyQt6 import QtWebEngineWidgets  # noqa: F401

            print("HEADLESS_SMOKE: QtWebEngineWidgets imported (PyQt6 import)")
        except Exception as e2:
            print("HEADLESS_SMOKE: QtWebEngineWidgets import failed:", e2 or e)

    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        print("HEADLESS_SMOKE: Set AA_ShareOpenGLContexts")
    except Exception:
        pass

    app = QApplication([])
    print("HEADLESS_SMOKE: QApplication created")
    # Try to register any bundled fonts so Qt and matplotlib can find glyphs
    try:
        # Import local helper if present
        try:
            from HjemmeladingApp.utils.fonts import register_bundled_fonts
        except Exception:
            register_bundled_fonts = None
        if register_bundled_fonts:
            n = register_bundled_fonts()
            print("HEADLESS_SMOKE: registered bundled fonts count:", n)
    except Exception as e:
        print("HEADLESS_SMOKE: font registration failed:", e)
    # Settings dialog (use the packaged UI path)
    try:
        from HjemmeladingApp.ui.settings_dialog import SettingsDialog

        sd = SettingsDialog()
        print("HEADLESS_SMOKE: SettingsDialog instantiated")
        try:
            sd.close()
        except Exception:
            pass
    except Exception:
        print("HEADLESS_SMOKE: SettingsDialog failed:")
        traceback.print_exc()
    # Main window (skip by default in headless to avoid hangs)
    if _should_skip_mainwindow():
        print("HEADLESS_SMOKE: skipping MainWindow in headless mode " "(set HEADLESS_SMOKE_RUN_MAINWINDOW=1 to enable)")
    else:
        try:
            from src.ui.main_window import MainWindow

            mw = MainWindow()
            print("HEADLESS_SMOKE: MainWindow instantiated")
            try:
                mw.close()
            except Exception:
                pass
        except Exception:
            print("HEADLESS_SMOKE: MainWindow failed:")
            traceback.print_exc()
    # Process events briefly
    try:
        app.processEvents()
        print("HEADLESS_SMOKE: processEvents done")
    except Exception:
        traceback.print_exc()
    # Add a small matplotlib font diagnostic so we can see what matplotlib
    # sees at runtime (whether DejaVu Sans is available and roughly how many
    # font families matplotlib knows about).
    try:
        import matplotlib as mpl
        from matplotlib import font_manager as fm

        print("HEADLESS_SMOKE: matplotlib version", getattr(mpl, "__version__", "?"))
        try:
            ttflist = fm.fontManager.ttflist
            families = sorted({fe.name for fe in ttflist if getattr(fe, "name", None)})
            print("HEADLESS_SMOKE: matplotlib font families count:", len(families))
            print("HEADLESS_SMOKE: sample families:", families[:20])
            print(
                "HEADLESS_SMOKE: DejaVu Sans present:",
                any("DejaVu Sans" in f for f in families),
            )
        except Exception as e:
            print("HEADLESS_SMOKE: unable to query fontManager.ttflist:", e)
    except ModuleNotFoundError as e:
        print("HEADLESS_SMOKE: matplotlib not available:", e)
    except Exception as e:
        print("HEADLESS_SMOKE: matplotlib failed:", e)
        traceback.print_exc()
    try:
        app.quit()
    except Exception:
        pass
except Exception:
    traceback.print_exc()
print("HEADLESS_SMOKE: done")
