from types import SimpleNamespace

from src.modules import load_wizard_pages as pages_module


class _FakeLineEdit:
    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text


class _FakeSpinBox:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class _FakeCombo:
    def __init__(self, data):
        self._data = data

    def currentData(self):
        return self._data


class _FakeRadio:
    def __init__(self, checked):
        self._checked = checked

    def isChecked(self):
        return self._checked


class _FakeDb:
    def __init__(self, batch=None, case=None):
        self._batch = batch
        self._case = case
        self.insert_calls = []

    def insert(self, table, data):
        self.insert_calls.append((table, data))
        return 101

    def get_by_id(self, table, record_id):
        if table == "brass_batches":
            return self._batch
        if table == "cases":
            return self._case
        return None


def test_brass_selection_validate_page_handles_missing_case(monkeypatch):
    warnings = []
    fake_db = _FakeDb(batch={"id": 101}, case=None)
    wizard = SimpleNamespace(brass_data=None)

    monkeypatch.setattr(pages_module, "get_database", lambda: fake_db)
    monkeypatch.setattr(
        pages_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    page = SimpleNamespace(
        wizard=wizard,
        existing_radio=_FakeRadio(False),
        batch_name_input=_FakeLineEdit("Lapua batch"),
        case_combo=_FakeCombo(7),
        quantity_spin=_FakeSpinBox(100),
        lot_number_input=_FakeLineEdit("LOT-1"),
    )

    result = pages_module.BrassSelectionPage.validatePage(page)

    assert result is False
    assert wizard.brass_data is None
    assert fake_db.insert_calls
    assert warnings
