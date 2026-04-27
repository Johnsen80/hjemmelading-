from types import SimpleNamespace

from src.modules import brass_manager as brass_module


class _FakeItem:
    def __init__(self, data):
        self._data = data

    def data(self, role):
        del role
        return self._data


class _FakeTable:
    def __init__(self, items):
        self._items = items

    def selectedItems(self):
        return self._items


class _MissingCaseDb:
    def __init__(self):
        self.queries = []

    def execute_query(self, query, params=()):
        self.queries.append((query, params))
        return []


def test_log_firing_handles_missing_case(monkeypatch):
    warnings = []
    fake_db = _MissingCaseDb()
    monkeypatch.setattr(
        brass_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    widget = SimpleNamespace(
        table=_FakeTable([_FakeItem(41)]),
        db=fake_db,
        load_data=lambda: warnings.append("reloaded"),
    )
    widget._ensure_case_exists = (
        lambda case_id: brass_module.BrassManager._ensure_case_exists(widget, case_id)
    )

    brass_module.BrassManager.log_firing(widget)

    assert warnings
    assert fake_db.queries == [("SELECT id FROM cases WHERE id = ?", (41,))]


def test_retire_cases_handles_missing_case(monkeypatch):
    warnings = []
    fake_db = _MissingCaseDb()
    monkeypatch.setattr(
        brass_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    widget = SimpleNamespace(
        table=_FakeTable([_FakeItem(77)]),
        db=fake_db,
        load_data=lambda: warnings.append("reloaded"),
    )
    widget._ensure_case_exists = (
        lambda case_id: brass_module.BrassManager._ensure_case_exists(widget, case_id)
    )

    brass_module.BrassManager.retire_cases(widget)

    assert warnings
    assert fake_db.queries == [("SELECT id FROM cases WHERE id = ?", (77,))]
