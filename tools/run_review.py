#!/usr/bin/env python3
"""Small runner to open the Weapon Profile Editor for quick review.

Usage: python tools/run_review.py
This script prepends the repository root to sys.path so imports like
`src.ui.weapon_profile_editor` work when invoked from the repo root.
"""
import sys
from pathlib import Path

if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))

    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.weapon_profile_editor import WeaponProfileEditor
    except Exception as e:
        print("Failed to import GUI components:", e)
        raise

    app = QApplication([])
    dlg = WeaponProfileEditor()
    dlg.show()
    sys.exit(app.exec())
