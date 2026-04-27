from src.modules import precision_tracker as tracker_module


def test_format_group_mm_uses_metric_by_default(monkeypatch):
    monkeypatch.setattr(tracker_module, "_get_global_unit_system", lambda: "metric")

    formatted = tracker_module._format_group_mm(18.5)

    assert formatted == "18.5 mm"


def test_format_group_mm_uses_imperial_with_mm_context(monkeypatch):
    monkeypatch.setattr(tracker_module, "_get_global_unit_system", lambda: "imperial")

    formatted = tracker_module._format_group_mm(25.4)

    assert "in" in formatted
    assert "mm" in formatted


def test_format_wind_mps_uses_imperial_with_metric_context(monkeypatch):
    monkeypatch.setattr(tracker_module, "_get_global_unit_system", lambda: "imperial")

    formatted = tracker_module._format_wind_mps(5.0)

    assert "mph" in formatted
    assert "m/s" in formatted
