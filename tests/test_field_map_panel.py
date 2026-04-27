"""Smoke tests for FieldMapPanel — import-only (no Qt needed for logic helpers)."""

from __future__ import annotations

import pytest


def test_haversine_known_distance():
    from src.ui.field_map_panel import _haversine_m

    # Oslo → ~55 km northeast
    d = _haversine_m(59.9139, 10.7522, 60.3, 11.3)
    assert 50_000 < d < 80_000


def test_haversine_zero():
    from src.ui.field_map_panel import _haversine_m

    assert _haversine_m(60.0, 10.0, 60.0, 10.0) == pytest.approx(0.0, abs=1.0)


def test_bearing_north():
    from src.ui.field_map_panel import _bearing_deg

    b = _bearing_deg(60.0, 10.0, 61.0, 10.0)
    assert b == pytest.approx(0.0, abs=1.0)


def test_bearing_east():
    from src.ui.field_map_panel import _bearing_deg

    b = _bearing_deg(60.0, 10.0, 60.0, 11.0)
    assert 85 < b < 95


def test_bearing_south():
    from src.ui.field_map_panel import _bearing_deg

    b = _bearing_deg(60.0, 10.0, 59.0, 10.0)
    assert b == pytest.approx(180.0, abs=1.0)


def test_bearing_west():
    from src.ui.field_map_panel import _bearing_deg

    b = _bearing_deg(60.0, 10.0, 60.0, 9.0)
    assert 265 < b < 275


def test_target_colors_cycle():
    from src.ui.field_map_panel import _target_color

    colors = [_target_color(i) for i in range(20)]
    assert all(c.startswith("#") for c in colors)
    assert colors[0] == colors[8]  # cycles after 8


def test_module_imports_without_qt():
    """field_map_panel must be importable even when QtWebEngine is absent."""
    from src.ui import field_map_panel as fmp

    assert hasattr(fmp, "FieldMapPanel")
    assert hasattr(fmp, "_haversine_m")
    assert hasattr(fmp, "_bearing_deg")


def test_fetch_elevation_returns_list_on_error():
    """Returns empty list if network is unavailable (CI has no internet)."""
    from src.ui.field_map_panel import _fetch_elevation_profile

    result = _fetch_elevation_profile(60.0, 10.0, 61.0, 11.0, n=3)
    assert isinstance(result, list)
