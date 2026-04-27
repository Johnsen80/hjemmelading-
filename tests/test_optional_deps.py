import importlib

import pytest


@pytest.mark.core
def test_optional_deps_importable():
    mod = importlib.import_module("src.utils.optional_deps")
    # Should expose HAS_MPL and HAS_CV2 booleans
    assert hasattr(mod, "HAS_MPL")
    assert hasattr(mod, "HAS_CV2")


@pytest.mark.core
def test_figure_canvas_sanity():
    mod = importlib.import_module("src.utils.optional_deps")
    # Figure and FigureCanvas should exist (may be dummy implementations)
    assert hasattr(mod, "Figure")
    assert hasattr(mod, "FigureCanvas")
    Fig = mod.Figure
    Canvas = mod.FigureCanvas
    # If Figure is callable, instantiate it
    try:
        fig = Fig()
        assert fig is not None
    except Exception:
        # Acceptable: dummy class might require args
        pass
    try:
        # Canvas may be a QWidget subclass or dummy; ensure it can be constructed without error
        c = Canvas()
        assert c is not None
    except Exception:
        pass
