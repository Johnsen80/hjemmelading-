from types import SimpleNamespace

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog

from src.modules import session_logger as session_logger_module


class _FakeItem:
    def __init__(self, value):
        self._value = value

    def data(self, role):
        if role == Qt.ItemDataRole.UserRole:
            return self._value
        return None


class _FakeTable:
    def __init__(self, session_id):
        self._session_id = session_id

    def currentRow(self):
        return 0

    def item(self, row, column):
        assert row == 0
        assert column == 0
        return _FakeItem(self._session_id)


class _FakeDb:
    def __init__(self):
        self.update_calls = []

    def get_by_id(self, table, session_id):
        return {"id": session_id, "table": table}

    def get_all(self, table):
        if table == "ammo_profiles":
            return [{"id": 1, "name": "Test ammo"}]
        if table == "rifles":
            return [{"id": 2, "name": "Test rifle"}]
        return []

    def update(self, table, data, condition, params=()):
        self.update_calls.append((table, data, condition, params))


def test_edit_loading_session_uses_database_update_condition(monkeypatch):
    fake_db = _FakeDb()
    refreshed = {"called": False}

    class _AcceptedDialog:
        def __init__(self, *args, **kwargs):
            self._data = {
                "date": "2026-03-25",
                "project_name": "Test Project",
                "ammo_profile_id": 1,
            }

        def exec(self):
            return QDialog.DialogCode.Accepted

        def get_data(self):
            return self._data

    monkeypatch.setattr(session_logger_module, "LoadingSessionDialog", _AcceptedDialog)
    monkeypatch.setattr(
        session_logger_module.QMessageBox, "information", lambda *a, **k: None
    )
    monkeypatch.setattr(
        session_logger_module,
        "_get_active_project_context",
        lambda: {"project_name": "Test Project", "project_path": "C:/tmp/project"},
    )

    logger_widget = SimpleNamespace(
        db=fake_db,
        loading_table=_FakeTable(42),
        load_loading_sessions=lambda: refreshed.__setitem__("called", True),
    )

    session_logger_module.SessionLogger.edit_loading_session(logger_widget)

    assert fake_db.update_calls == [
        (
            "loading_sessions",
            {
                "date": "2026-03-25",
                "project_name": "Test Project",
                "ammo_profile_id": 1,
            },
            "id = ?",
            (42,),
        )
    ]
    assert refreshed["called"] is True


def test_edit_shooting_session_uses_database_update_condition(monkeypatch):
    fake_db = _FakeDb()
    refreshed = {"called": False}

    class _AcceptedDialog:
        def __init__(self, *args, **kwargs):
            self._data = {
                "date": "2026-03-25",
                "project_name": "Test Project",
                "rifle_id": 2,
                "ammo_profile_id": 1,
            }

        def exec(self):
            return QDialog.DialogCode.Accepted

        def get_data(self):
            return self._data

    monkeypatch.setattr(session_logger_module, "ShootingSessionDialog", _AcceptedDialog)
    monkeypatch.setattr(
        session_logger_module.QMessageBox, "information", lambda *a, **k: None
    )
    monkeypatch.setattr(
        session_logger_module,
        "_get_active_project_context",
        lambda: {"project_name": "Test Project", "project_path": "C:/tmp/project"},
    )

    logger_widget = SimpleNamespace(
        db=fake_db,
        shooting_table=_FakeTable(77),
        load_shooting_sessions=lambda: refreshed.__setitem__("called", True),
    )

    session_logger_module.SessionLogger.edit_shooting_session(logger_widget)

    assert fake_db.update_calls == [
        (
            "shooting_sessions",
            {
                "date": "2026-03-25",
                "project_name": "Test Project",
                "rifle_id": 2,
                "ammo_profile_id": 1,
            },
            "id = ?",
            (77,),
        )
    ]
    assert refreshed["called"] is True
