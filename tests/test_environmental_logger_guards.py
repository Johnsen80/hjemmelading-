from types import SimpleNamespace

from src.modules import environmental_logger as env_module


class _FakeCombo:
    def __init__(self, value):
        self._value = value

    def currentData(self):
        return self._value


class _MissingMeasurementDb:
    def __init__(self):
        self.queries = []

    def execute_query(self, query, params=()):
        self.queries.append((query, params))
        return []


def test_run_comparison_handles_missing_measurement(monkeypatch):
    warnings = []
    fake_db = _MissingMeasurementDb()
    monkeypatch.setattr(
        env_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    reloaded = []
    widget = SimpleNamespace(
        comparison_measurement=_FakeCombo(13),
        db=fake_db,
        load_measurements_for_comparison=lambda: reloaded.append(True),
    )

    env_module.EnvironmentalLogger.run_comparison(widget)

    assert warnings
    assert reloaded == [True]
