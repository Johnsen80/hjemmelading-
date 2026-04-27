from types import SimpleNamespace

from src.modules import load_development_workflow as workflow_module


class _FakeItem:
    def __init__(self, data):
        self._data = data

    def data(self, role):
        del role
        return self._data


class _FakeTable:
    def __init__(self, row=0, item=None):
        self._row = row
        self._item = item

    def currentRow(self):
        return self._row

    def item(self, row, column):
        del row, column
        return self._item


class _MissingWorkflowDb:
    def __init__(self):
        self.lookups = []

    def get_by_id(self, table, record_id):
        self.lookups.append((table, record_id))
        return None


def test_open_workflow_handles_missing_workflow(monkeypatch):
    warnings = []
    fake_db = _MissingWorkflowDb()
    monkeypatch.setattr(
        workflow_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    reloaded = []
    widget = SimpleNamespace(
        active_table=_FakeTable(item=_FakeItem(14)),
        db=fake_db,
        load_active_workflows=lambda: reloaded.append(True),
    )

    workflow_module.LoadDevelopmentWorkflow.open_workflow(widget)

    assert warnings
    assert reloaded == [True]


def test_analyze_results_handles_missing_workflow(monkeypatch):
    warnings = []
    fake_db = _MissingWorkflowDb()
    monkeypatch.setattr(
        workflow_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    reloaded = []
    widget = SimpleNamespace(
        active_table=_FakeTable(item=_FakeItem(22)),
        db=fake_db,
        load_active_workflows=lambda: reloaded.append(True),
    )

    workflow_module.LoadDevelopmentWorkflow.analyze_results(widget)

    assert warnings
    assert reloaded == [True]


def test_build_workflow_context_includes_barrel_configuration_fields():
    context = workflow_module.build_workflow_context(
        {
            "id": 14,
            "name": "WF-14",
            "load_session_id": 33,
            "ammo_profile_id": 9,
            "rifle_id": 7,
            "barrel_id": "B1",
            "barrel_name": "26in Match",
            "barrel_configuration_id": "cfg-supp",
            "barrel_configuration_name": "Suppressed",
            "created_date": "2026-04-10",
        }
    )

    assert context["barrel_configuration_id"] == "cfg-supp"
    assert context["barrel_configuration_name"] == "Suppressed"
