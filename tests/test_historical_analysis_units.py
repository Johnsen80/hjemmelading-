from src.modules import historical_analysis as history_module


def test_format_velocity_fps_uses_metric_when_global_units_are_metric(monkeypatch):
    monkeypatch.setattr(history_module, "_get_global_unit_system", lambda: "metric")

    formatted = history_module._format_velocity_fps(2700.0)

    assert "m/s" in formatted
    assert "fps" in formatted


def test_format_distance_m_uses_imperial_when_global_units_are_imperial(monkeypatch):
    monkeypatch.setattr(history_module, "_get_global_unit_system", lambda: "imperial")

    formatted = history_module._format_distance_m(100.0)

    assert "yd" in formatted
    assert "m" in formatted
