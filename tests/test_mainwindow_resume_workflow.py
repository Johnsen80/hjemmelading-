import json
from types import SimpleNamespace

import src.ui.main_window as main_window_module
from src.ui.main_window import MainWindow


class _FakeSettings:
    store: dict[str, object] = {}

    def __init__(self, *args, **kwargs):
        pass

    def setValue(self, key, value):
        self.store[key] = value

    def value(self, key, default=None):
        return self.store.get(key, default)

    def sync(self):
        return None


class _FakeMessageBox:
    @staticmethod
    def information(*args, **kwargs):
        return None

    @staticmethod
    def warning(*args, **kwargs):
        return None


def test_resume_workflow_restores_session_context_and_active_setup(monkeypatch):
    _FakeSettings.store = {}
    captured: dict[str, object] = {}

    class _StateManager:
        def get_state(self, workflow_id):
            return SimpleNamespace(
                workflow_id=workflow_id,
                workflow_name="Modern Load Builder",
                data={
                    "workflow_id": workflow_id,
                    "load_session_id": "55",
                    "rifle_id": "7",
                    "barrel_id": "B1",
                    "barrel_configuration_id": "cfg-bare",
                    "barrel_configuration_name": "Bare",
                },
            )

    class _Db:
        def get_by_id(self, table, row_id):
            assert table == "load_development_sessions"
            assert row_id == 55
            return {
                "id": 55,
                "ammo_profile_id": 9,
                "rifle_id": 7,
                "barrel_id": "B2",
                "barrel_name": "26in Match",
                "barrel_configuration_id": "cfg-supp",
                "barrel_configuration_name": "Suppressed",
                "session_name": "Workup A",
            }

        def execute_query(self, query, params):
            assert params == (7,)
            return [
                {
                    "profile_json": json.dumps(
                        {
                            "active_barrel_id": "B1",
                            "active_barrel_configuration_id": "cfg-bare",
                            "active_barrel_configuration_name": "Bare",
                            "barrels": [
                                {"id": "B1", "name": "24in", "is_active": True},
                                {"id": "B2", "name": "26in Match", "is_active": False},
                            ],
                            "barrel_configurations": [
                                {
                                    "id": "cfg-bare",
                                    "name": "Bare",
                                    "barrel_id": "B1",
                                    "is_active": True,
                                },
                                {
                                    "id": "cfg-supp",
                                    "name": "Suppressed",
                                    "barrel_id": "B2",
                                    "is_active": False,
                                },
                            ],
                        }
                    )
                }
            ]

        def update(self, table, data, condition, params):
            captured["update"] = {
                "table": table,
                "data": data,
                "condition": condition,
                "params": params,
            }

    monkeypatch.setattr(main_window_module, "QSettings", _FakeSettings)
    monkeypatch.setattr(main_window_module, "QMessageBox", _FakeMessageBox)

    widget = SimpleNamespace(
        state_manager=_StateManager(),
        db=_Db(),
        launch_workflow=lambda workflow_id: captured.setdefault(
            "workflow_id", workflow_id
        ),
        _show_status_message=lambda message: captured.setdefault("status", message),
    )

    MainWindow.resume_workflow(widget, "modern_load_builder")

    assert captured["workflow_id"] == "modern_load_builder"
    assert _FakeSettings.store["workflow_context/load_session_id"] == 55
    assert _FakeSettings.store["workflow_context/rifle_id"] == 7
    assert _FakeSettings.store["workflow_context/barrel_id"] == "B2"
    assert _FakeSettings.store["workflow_context/barrel_configuration_id"] == "cfg-supp"
    assert (
        _FakeSettings.store["workflow_context/barrel_configuration_name"]
        == "Suppressed"
    )
    updated_profile = json.loads(captured["update"]["data"]["profile_json"])
    assert updated_profile["active_barrel_id"] == "B2"
    assert updated_profile["active_barrel_configuration_id"] == "cfg-supp"
    assert updated_profile["active_barrel_configuration_name"] == "Suppressed"
    assert updated_profile["barrels"][0]["is_active"] is False
    assert updated_profile["barrels"][1]["is_active"] is True
    assert updated_profile["barrel_configurations"][0]["is_active"] is False
    assert updated_profile["barrel_configurations"][1]["is_active"] is True


def test_resume_workflow_uses_saved_state_context_when_session_missing(monkeypatch):
    _FakeSettings.store = {}

    class _StateManager:
        def get_state(self, workflow_id):
            return SimpleNamespace(
                workflow_id=workflow_id,
                workflow_name="Modern Load Builder",
                data={
                    "workflow_id": workflow_id,
                    "load_session_id": "77",
                    "rifle_id": "5",
                    "barrel_id": "B3",
                    "barrel_name": "20in Trainer",
                    "barrel_configuration_id": "cfg-trainer",
                    "barrel_configuration_name": "Trainer",
                    "session_name": "Session B",
                },
            )

    class _Db:
        def get_by_id(self, table, row_id):
            assert table == "load_development_sessions"
            assert row_id == 77
            return None

        def execute_query(self, query, params):
            return []

    monkeypatch.setattr(main_window_module, "QSettings", _FakeSettings)
    monkeypatch.setattr(main_window_module, "QMessageBox", _FakeMessageBox)

    widget = SimpleNamespace(
        state_manager=_StateManager(),
        db=_Db(),
        launch_workflow=lambda workflow_id: None,
        _show_status_message=lambda message: None,
    )

    MainWindow.resume_workflow(widget, "modern_load_builder")

    assert _FakeSettings.store["workflow_context/load_session_id"] == 77
    assert _FakeSettings.store["workflow_context/rifle_id"] == 5
    assert _FakeSettings.store["workflow_context/barrel_id"] == "B3"
    assert _FakeSettings.store["workflow_context/barrel_name"] == "20in Trainer"
    assert (
        _FakeSettings.store["workflow_context/barrel_configuration_id"] == "cfg-trainer"
    )
    assert (
        _FakeSettings.store["workflow_context/barrel_configuration_name"] == "Trainer"
    )
    assert _FakeSettings.store["workflow_context/session_name"] == "Session B"
