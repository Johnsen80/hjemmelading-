"""Small runner to launch the Weapon Profile editor for testing.

Run this from the project root with the project's Python environment active:

  & .\\.venv\\Scripts\\python.exe .\tools\run_weapon_editor.py

"""

# Ensure repo root is on sys.path for imports like `src.*` (works without
# requiring `tools` to be an importable package).
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from PyQt6.QtWidgets import QApplication

    from src.ui.weapon_profile_editor import WeaponProfileEditor
except Exception:
    traceback.print_exc()
    print("Failed to import PyQt6 or the editor module.")
    raise


def main():
    app = QApplication(sys.argv)
    editor = WeaponProfileEditor(data_path=Path("data/demo_weapons.json"))
    editor.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
