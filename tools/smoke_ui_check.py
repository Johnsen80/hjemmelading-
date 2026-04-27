# pyright: reportOptionalCall=false, reportOptionalMemberAccess=false

import os
import sys
from pathlib import Path
from typing import Any, cast

# Ensure repository root is on sys.path for src imports
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.qt_compat import QApplication, QSettings  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("HEADLESS", "1")
    if os.name == "nt":
        os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")
    if QApplication is None:
        raise RuntimeError("Qt compatibility layer is unavailable")

    if QSettings is not None:
        try:
            settings = cast(Any, QSettings)("Valkyrie", "ValkyrieBallistics")
            settings.setValue("onboarding_seen", True)
        except Exception:
            pass

    qt_app = cast(Any, QApplication)
    app = qt_app([])  # pyright: ignore[reportOptionalCall]
    win = MainWindow()
    apply_error = None

    try:
        app.processEvents()
    except Exception:
        pass

    if apply_error is not None:
        print("apply_user_settings_error", apply_error, flush=True)
    print("stacked_widget", hasattr(win, "stacked_widget"), flush=True)
    if hasattr(win, "stacked_widget"):
        try:
            print("stacked_count", win.stacked_widget.count(), flush=True)
        except Exception as exc:
            print("stacked_count_error", exc, flush=True)
    print("nav_keys", list(getattr(win, "_nav_buttons", {}).keys()), flush=True)
    print("mode_combo", hasattr(win, "mode_combo"), flush=True)
    print("command_input", hasattr(win, "command_input"), flush=True)
    print("project_combo", hasattr(win, "project_combo"), flush=True)
    if hasattr(win, "project_combo"):
        try:
            print("project_enabled", win.project_combo.isEnabled(), flush=True)
        except Exception as exc:
            print("project_enabled_error", exc, flush=True)
        try:
            print("project_count", win.project_combo.count(), flush=True)
        except Exception as exc:
            print("project_count_error", exc, flush=True)
    try:
        win.close()
    except Exception:
        pass
    try:
        app.quit()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
