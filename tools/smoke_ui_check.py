import os
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

# Ensure repository root is on sys.path for src imports
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "windows")
    try:
        from PyQt6.QtCore import qInstallMessageHandler

        def _qt_message_handler(msg_type, context, message):
            try:
                text = str(message)
            except Exception:
                text = message
            if "Cannot find font directory" in text or "Qt no longer ships fonts" in text:
                return
            try:
                sys.__stderr__.write(str(message) + "\n")
            except Exception:
                pass

        qInstallMessageHandler(_qt_message_handler)
    except Exception:
        pass
    try:
        from HjemmeladingApp.utils.fonts import ensure_qt_fontdir

        ensure_qt_fontdir()
    except Exception:
        pass
    app = QApplication([])
    win = MainWindow()
    apply_error = None

    try:
        win.apply_user_settings()
    except Exception as exc:
        apply_error = exc

    def report() -> None:
        if apply_error is not None:
            print("apply_user_settings_error", apply_error)
        print("stacked_widget", hasattr(win, "stacked_widget"))
        if hasattr(win, "stacked_widget"):
            try:
                print("stacked_count", win.stacked_widget.count())
            except Exception as exc:
                print("stacked_count_error", exc)
        print("nav_keys", list(getattr(win, "_nav_buttons", {}).keys()))
        print("mode_combo", hasattr(win, "mode_combo"))
        print("command_input", hasattr(win, "command_input"))
        print("project_combo", hasattr(win, "project_combo"))
        if hasattr(win, "project_combo"):
            try:
                print("project_enabled", win.project_combo.isEnabled())
            except Exception as exc:
                print("project_enabled_error", exc)
            try:
                print("project_count", win.project_combo.count())
            except Exception as exc:
                print("project_count_error", exc)
        win.close()
        app.quit()

    QTimer.singleShot(500, report)
    win.show()
    app.exec()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
