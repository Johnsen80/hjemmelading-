from src.modules import session_logger as logger_module


def test_format_distance_meters_uses_imperial_with_metric_context(monkeypatch):
    monkeypatch.setattr(logger_module, "_get_global_unit_system", lambda: "imperial")

    formatted = logger_module._format_distance_meters(100.0)

    assert "yd" in formatted
    assert "m" in formatted


def test_format_temperature_c_uses_imperial_with_metric_context(monkeypatch):
    monkeypatch.setattr(logger_module, "_get_global_unit_system", lambda: "imperial")

    formatted = logger_module._format_temperature_c(10.0)

    assert "°F" in formatted
    assert "°C" in formatted


def test_from_display_distance_round_trips_imperial(monkeypatch):
    monkeypatch.setattr(logger_module, "_get_global_unit_system", lambda: "imperial")

    meters = logger_module._from_display_distance(100)

    assert round(meters, 2) == round(91.44, 2)
