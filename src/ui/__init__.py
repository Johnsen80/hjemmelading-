"""Init for the `src.ui` package.

Keep this file minimal and import-safe. During PyInstaller analysis or
other frozen runtimes importing heavy UI submodules (like ``main_window``)
can raise spurious ``ImportError`` due to differences in import paths.
Attempt to import the richer ``MainWindow`` if available, but never
raise during package import — callers should perform lazy imports and
apply fallbacks as needed.
"""

__all__ = []

# Prefer a best-effort, non-raising import of the rich MainWindow so
# frozen executables don't fail at package import time. If the import
# fails, we quietly continue and allow callers to try alternate paths.
try:
    from .main_window import MainWindow  # type: ignore
except Exception:
    # Don't propagate import errors from heavy UI modules during package
    # import; consumers will attempt their own lazy imports.
    pass
