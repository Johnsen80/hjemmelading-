"""Manual Qt runner for the SettingsDialog.

This file is a convenience entrypoint for manual testing only. It is
guarded so importing the module (e.g. by pytest) does not start the
Qt event loop. Use `python qt_test.py` to run interactively.
"""

from __future__ import annotations

import sys

from PyQt6 import QtWidgets

try:
    # Local import so tests that don't need Qt won't fail at import time
    from HjemmeladingApp.ui.settings_dialog import SettingsDialog
except Exception:
    SettingsDialog = None  # type: ignore


def main() -> int:
    if SettingsDialog is None:
        print("SettingsDialog not importable in this environment.")
        return 0
    app = QtWidgets.QApplication(sys.argv)
    dlg = SettingsDialog()
    dlg.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
