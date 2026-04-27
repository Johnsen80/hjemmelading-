"""Init for the `src.ui` package.

Keep this file minimal and import-safe. During PyInstaller analysis or
other frozen runtimes importing heavy UI submodules (like ``main_window``)
can raise spurious ``ImportError`` due to differences in import paths.
Attempt to import the richer ``MainWindow`` if available, but never
raise during package import — callers should perform lazy imports and
apply fallbacks as needed.
"""

from typing import Any

__all__ = []

# MainWindow is resolved dynamically; keep it as an optional runtime symbol.
MainWindow: Any | None = None

# Prefer a best-effort, non-raising import of the rich MainWindow so
# frozen executables don't fail at package import time. If the import
# fails, we quietly continue and allow callers to try alternate paths.
try:
    from .main_window import MainWindow  # type: ignore

    __all__.append("MainWindow")
except Exception:
    # Attempt a fallback for frozen/archived runtimes (PyInstaller)
    # where the package source may be inside a zip archive. Try to
    # load the `main_window.py` source from package resources and
    # exec it into a new module named `src.ui.main_window` so callers
    # can still import `MainWindow` lazily.
    try:
        import pkgutil
        import types

        data = pkgutil.get_data(__package__, "main_window.py")
        if data:
            src = data.decode("utf-8")
            mod_name = __name__ + ".main_window"
            mod = types.ModuleType(mod_name)
            mod.__file__ = f"{__package__}/main_window.py"
            # Provide a minimal package context for relative imports
            mod.__package__ = __package__
            # Execute source in module namespace
            exec(compile(src, mod.__file__, "exec"), mod.__dict__)
            # Insert into sys.modules so subsequent imports work
            import sys

            sys.modules[mod_name] = mod
            # Expose MainWindow if provided
            if hasattr(mod, "MainWindow"):
                MainWindow = getattr(mod, "MainWindow")
                __all__.append("MainWindow")
    except Exception:
        # Best-effort only: do not raise during package import.
        pass
    # If that didn't work, try to read the PyInstaller base_library.zip
    # which is placed under the distribution's `_internal` directory in
    # onedir builds. This lets us extract the original source file and
    # execute it so frozen runtimes can still provide `MainWindow`.
    try:
        import sys
        import zipfile
        from pathlib import Path

        exe = Path(sys.executable)
        # In onedir, the executable sits next to the package folder
        candidate = exe.parent / "_internal" / "base_library.zip"
        if not candidate.exists():
            # Also try sys._MEIPASS if available
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                candidate = Path(meipass) / "base_library.zip"
        if candidate.exists():
            with zipfile.ZipFile(candidate, "r") as z:
                member = "src/ui/main_window.py"
                if member in z.namelist():
                    src = z.read(member).decode("utf-8")
                    mod_name = __name__ + ".main_window"
                    import sys as _sys
                    import types

                    mod = types.ModuleType(mod_name)
                    mod.__file__ = str(candidate) + "::" + member
                    mod.__package__ = __package__
                    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
                    _sys.modules[mod_name] = mod
                    if hasattr(mod, "MainWindow"):
                        MainWindow = getattr(mod, "MainWindow")
                        __all__.append("MainWindow")
    except Exception:
        pass
