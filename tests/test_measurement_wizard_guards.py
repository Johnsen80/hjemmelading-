from types import SimpleNamespace

from src.modules import measurement_wizard as wizard_module


class _FakeCombo:
    def __init__(self, value, count=1):
        self._value = value
        self._count = count

    def count(self):
        return self._count

    def currentData(self):
        return self._value


class _FakeTable:
    def rowCount(self):
        return 0


class _MissingLotDb:
    def __init__(self):
        self.lookups = []
        self.session_calls = []

    def get_by_id(self, table, record_id):
        self.lookups.append((table, record_id))
        return None

    def create_measurement_session(self, *args, **kwargs):
        self.session_calls.append((args, kwargs))
        return 1


def test_save_session_handles_missing_lot(monkeypatch):
    warnings = []
    fake_db = _MissingLotDb()
    monkeypatch.setattr(
        wizard_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    reloaded = []
    widget = SimpleNamespace(
        lot_combo=_FakeCombo(11),
        table=_FakeTable(),
        db=fake_db,
        load_lots=lambda: reloaded.append(True),
    )

    wizard_module.MeasurementSessionDialog.save_session(widget)

    assert warnings
    assert reloaded == [True]
    assert fake_db.session_calls == []
