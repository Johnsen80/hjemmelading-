"""
Optional dependency shims used to make import-time safe in headless/CI environments.
Provides safe fallbacks for matplotlib and OpenCV so modules can import without
raising ModuleNotFoundError. When a library is missing, the shim exposes a
minimal compatible API that prevents import failures; functions that actually
need plotting or CV should check the corresponding flag (HAS_MPL/HAS_CV2)
and either disable features or show an informative message to the user.
"""

_HAS_MPL = False
_HAS_CV2 = False

# Matplotlib shim
try:
    import matplotlib.pyplot as plt  # type: ignore
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvasQTAgg as FigureCanvasQTAgg,
    )
    from matplotlib.figure import Figure  # type: ignore

    HAS_MPL = True
    FigureCanvas = FigureCanvasQTAgg
except Exception:
    class _DummyPlt:
        def subplots(self, *args, **kwargs):
            fig = _DummyFigure()
            ax = fig.add_subplot()
            return fig, ax

        def figure(self, *args, **kwargs):
            return _DummyFigure()

    plt = _DummyPlt()
    HAS_MPL = False

    # Provide lightweight dummies so code that constructs figures/canvases
    # does not fail at import time. These stubs implement a minimal subset
    # of the Matplotlib API that our app expects; they do nothing at runtime
    # but prevent AttributeErrors when calling methods.

    class _DummyAxes:
        def __init__(self):
            self.spines = {
                "top": _DummySpine(),
                "right": _DummySpine(),
                "left": _DummySpine(),
                "bottom": _DummySpine(),
            }

        def clear(self):
            return

        def set_xlabel(self, *args, **kwargs):
            return

        def set_ylabel(self, *args, **kwargs):
            return

        def set_title(self, *args, **kwargs):
            return

        def grid(self, *args, **kwargs):
            return

        def plot(self, *args, **kwargs):
            return

        def scatter(self, *args, **kwargs):
            return

        def legend(self, *args, **kwargs):
            return

        def add_subplot(self, *args, **kwargs):
            return self

    class _DummySpine:
        def set_visible(self, *args, **kwargs):
            return

        def set_linewidth(self, *args, **kwargs):
            return

    class _DummyFigure:
        def __init__(self, *args, **kwargs):
            self._axes = [_DummyAxes()]

        def add_subplot(self, *args, **kwargs):
            return _DummyAxes()

        def tight_layout(self, *args, **kwargs):
            return

    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

    class _DummyCanvas(QWidget):
        def __init__(self, fig=None, parent=None):
            parent_widget = parent if parent is not None else None
            super().__init__(parent_widget)
            self._fig = fig
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Plotting unavailable in this environment"))
            self.setLayout(layout)

        def draw(self):
            return

    Figure = _DummyFigure
    FigureCanvas = _DummyCanvas
    # Provide alias compatible with modules that import backend-specific
    # `FigureCanvasQTAgg` so they receive a QWidget-like dummy.
    FigureCanvasQTAgg = _DummyCanvas

# OpenCV shim
try:
    import cv2  # type: ignore

    HAS_CV2 = True
except Exception:
    cv2 = None  # type: ignore
    HAS_CV2 = False

__all__ = ["plt", "Figure", "FigureCanvas", "HAS_MPL", "cv2", "HAS_CV2"]
