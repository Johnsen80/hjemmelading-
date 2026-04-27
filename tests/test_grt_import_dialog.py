from types import SimpleNamespace

from src.modules import grt_integration as grt_module


class _FakeDb:
    def __init__(self, existing_rows):
        self._existing_rows = existing_rows
        self.update_calls = []
        self.insert_calls = []

    def execute_query(self, query, params=()):
        if "FROM grt_data WHERE ammo_profile_id = ?" in query:
            ammo_profile_id = params[0]
            return list(self._existing_rows.get(ammo_profile_id, []))
        return []

    def update(self, table, data, condition, params=()):
        self.update_calls.append((table, data, condition, params))

    def insert(self, table, data):
        self.insert_calls.append((table, data))
        return 1


def test_grt_import_updates_existing_record(monkeypatch):
    fake_db = _FakeDb(existing_rows={5: [{"id": 11}]})
    info_messages = []

    monkeypatch.setattr(
        grt_module.QMessageBox,
        "information",
        lambda *a, **k: info_messages.append((a, k)),
    )

    dialog = SimpleNamespace(
        db=fake_db,
        grt_data=[
            {
                "name": "Test profile",
                "velocity_fps": 2750,
                "max_pressure_psi": 58000,
                "case_fill_percent": 97.5,
                "accuracy_potential": 0.8,
            }
        ],
        find_matching_profile=lambda item: {"id": 5, "name": "Matched profile"},
        accept=lambda: None,
    )

    grt_module.GRTImportDialog.do_import(dialog)

    assert len(fake_db.update_calls) == 1
    table, data, condition, params = fake_db.update_calls[0]
    assert table == "grt_data"
    assert condition == "id = ?"
    assert params == (11,)
    assert data["ammo_profile_id"] == 5
    assert data["predicted_velocity"] == 2750
    assert data["max_pressure_psi"] == 58000
    assert fake_db.insert_calls == []
    assert info_messages


def test_grt_import_inserts_when_no_existing_record(monkeypatch):
    fake_db = _FakeDb(existing_rows={})
    info_messages = []

    monkeypatch.setattr(
        grt_module.QMessageBox,
        "information",
        lambda *a, **k: info_messages.append((a, k)),
    )

    dialog = SimpleNamespace(
        db=fake_db,
        grt_data=[
            {
                "name": "New profile",
                "predicted_velocity": 2680,
                "pressure": 55000,
                "fill_ratio": 94.0,
            }
        ],
        find_matching_profile=lambda item: {"id": 9, "name": "Matched profile"},
        accept=lambda: None,
    )

    grt_module.GRTImportDialog.do_import(dialog)

    assert fake_db.update_calls == []
    assert len(fake_db.insert_calls) == 1
    table, data = fake_db.insert_calls[0]
    assert table == "grt_data"
    assert data["ammo_profile_id"] == 9
    assert data["predicted_velocity"] == 2680
    assert data["max_pressure_psi"] == 55000
    assert data["case_fill_percent"] == 94.0
    assert info_messages
