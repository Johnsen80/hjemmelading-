import importlib.util
import os
import runpy
import sys
from pathlib import Path


def _add_qt_bin_to_path():
    """Try several heuristics to find a Qt6 'bin' folder and add it to DLL search path or PATH.
    Returns True if added, False otherwise."""
    # 1) If PyQt6 is importable, try to locate package directory
    try:
        spec = importlib.util.find_spec("PyQt6")
        if spec and getattr(spec, "origin", None):
            pyqt_pkg_dir = Path(spec.origin).resolve().parent
            qt_bin = pyqt_pkg_dir / "Qt6" / "bin"
            if qt_bin.exists():
                try:
                    os.add_dll_directory(str(qt_bin))
                except Exception:
                    os.environ["PATH"] = (
                        str(qt_bin) + os.pathsep + os.environ.get("PATH", "")
                    )
                return True
    except Exception:
        pass

    # 2) Common venv locations inside workspace
    workspace = Path(__file__).resolve().parent
    candidates = [
        workspace / ".venv",
        workspace / ".github" / ".tool-venv",
        workspace / "HjemmeladingApp" / "ui" / ".venv",
    ]
    for cand in candidates:
        qt_bin = cand / "Lib" / "site-packages" / "PyQt6" / "Qt6" / "bin"
        if qt_bin.exists():
            try:
                os.add_dll_directory(str(qt_bin))
            except Exception:
                os.environ["PATH"] = (
                    str(qt_bin) + os.pathsep + os.environ.get("PATH", "")
                )
            return True

    # 3) Search workspace for PyQt6/Qt6/bin (best-effort, stop at first match)
    try:
        for p in workspace.rglob("PyQt6"):
            qt_bin = p / "Qt6" / "bin"
            if qt_bin.exists():
                try:
                    os.add_dll_directory(str(qt_bin))
                except Exception:
                    os.environ["PATH"] = (
                        str(qt_bin) + os.pathsep + os.environ.get("PATH", "")
                    )
                return True
    except Exception:
        pass

    return False


if __name__ == "__main__":
    _add_qt_bin_to_path()
    # Ensure project root is on sys.path
    proj_root = Path(__file__).resolve().parent
    if str(proj_root) not in sys.path:
        sys.path.insert(0, str(proj_root))
    # Execute the standardized top-level entrypoint so launch behavior
    # matches the release scripts and PyInstaller specs.
    runpy.run_path(str(proj_root / "main.py"), run_name="__main__")
