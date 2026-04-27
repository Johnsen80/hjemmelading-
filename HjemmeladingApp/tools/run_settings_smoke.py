#!/usr/bin/env python3
"""Headless smoke runner for the Settings dialog."""
import os
import sys
from pathlib import Path


def _ensure_repo_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def _read_last_error() -> str:
    try:
        from HjemmeladingApp.utils.safe_logger import get_debug_log_path

        log_path = get_debug_log_path()
    except Exception:
        return "None"

    try:
        if not log_path.exists():
            return "None"
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in reversed(lines):
            if line.strip():
                return line.strip()
    except Exception:
        return "None"
    return "None"


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if os.name == "nt":
        os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

    _ensure_repo_on_path()

    try:
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        from HjemmeladingApp.ui.settings_dialog import SettingsDialog
    except Exception as exc:
        print("SETTINGS_SMOKE: import failed:", exc)
        return 2

    app = QApplication.instance() or QApplication([])

    try:
        dialog = SettingsDialog()
        dialog.show()
    except Exception as exc:
        print("SETTINGS_SMOKE: dialog init failed:", exc)
        return 3

    def _quit() -> None:
        try:
            dialog.close()
        except Exception:
            pass
        try:
            app.quit()
        except Exception:
            pass

    try:
        delay_ms = int(os.environ.get("SETTINGS_SMOKE_QUIT_MS", "1000"))
    except Exception:
        delay_ms = 1000

    QTimer.singleShot(delay_ms, _quit)
    rc = app.exec()
    print("SETTINGS_SMOKE: done", rc)
    print(f"LAST_ERROR: {_read_last_error()}")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
