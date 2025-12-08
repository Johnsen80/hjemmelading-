"""Create desktop shortcut for HJEMMELADING (Windows).

This script is intentionally minimal: it prefers a virtualenv pythonw.exe
when available; otherwise it falls back to system pythonw/python.
"""

import os
import shutil
from pathlib import Path

try:
    import winshell
except Exception:
    winshell = None


def create_desktop_shortcut() -> None:
    project_dir = Path(__file__).parent.resolve()
    main_py = project_dir / "HjemmeladingApp" / "main.py"
    icon_file = project_dir / "hjemmelading.ico"

    # Prefer venv pythonw.exe if present, otherwise fall back to a system pythonw/python
    venv_pythonw = project_dir / ".venv" / "Scripts" / "pythonw.exe"
    if venv_pythonw.exists():
        pythonw_exe = str(venv_pythonw)
    else:
        pythonw_exe = shutil.which("pythonw") or shutil.which("python")

    if winshell is None:
        print("winshell not available. Install with: pip install winshell")
        return

    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, "HJEMMELADING.lnk")

    with winshell.shortcut(shortcut_path) as shortcut:
        shortcut.path = pythonw_exe
        shortcut.arguments = f'"{main_py}"'
        shortcut.working_directory = str(project_dir)
        shortcut.description = "HJEMMELADING - Tactical Reloading System"
        if icon_file.exists():
            shortcut.icon_location = (str(icon_file), 0)

    print("✅ Desktop shortcut created:", shortcut_path)


if __name__ == "__main__":
    try:
        create_desktop_shortcut()
    except Exception as e:
        print("Failed to create shortcut:", e)
