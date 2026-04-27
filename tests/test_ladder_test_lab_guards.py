from types import SimpleNamespace

from src.modules import ladder_test_lab as ladder_module


class _MissingTestDb:
    def get_by_id(self, table, record_id):
        return None

    def execute_query(self, query, params=()):
        return []


def test_open_results_dialog_handles_missing_test(monkeypatch):
    warnings = []
    reloaded = {"called": False}

    monkeypatch.setattr(
        ladder_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    widget = SimpleNamespace(
        db=_MissingTestDb(),
        load_tests=lambda: reloaded.__setitem__("called", True),
    )

    ladder_module.LadderTestLab.open_results_dialog(widget, 12)

    assert warnings
    assert reloaded["called"] is True


def test_open_analysis_window_handles_missing_test(monkeypatch):
    warnings = []
    reloaded = {"called": False}

    monkeypatch.setattr(
        ladder_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    widget = SimpleNamespace(
        db=_MissingTestDb(),
        load_tests=lambda: reloaded.__setitem__("called", True),
    )

    ladder_module.LadderTestLab.open_analysis_window(widget, 34)

    assert warnings
    assert reloaded["called"] is True


def test_open_results_dialog_propagates_load_session_id(monkeypatch):
    inserts = []

    class _DialogCode:
        Accepted = 1

    class _Dialog:
        def __init__(self, parent, test):
            self.test = test

        def exec(self):
            return _DialogCode.Accepted

        def get_results(self):
            return [{"charge_weight": 41.2, "velocity_avg": 2801.0}]

    class _Db:
        def get_by_id(self, table, record_id):
            return {"id": record_id, "name": "LT", "load_session_id": 55}

        def insert(self, table, data):
            inserts.append((table, dict(data)))
            return 1

    infos = []

    monkeypatch.setattr(ladder_module, "TestResultsDialog", _Dialog)
    monkeypatch.setattr(ladder_module.QDialog, "DialogCode", _DialogCode)
    monkeypatch.setattr(
        ladder_module.QMessageBox,
        "information",
        lambda *a, **k: infos.append((a, k)),
    )

    widget = SimpleNamespace(db=_Db(), load_tests=lambda: None)
    ladder_module.LadderTestLab.open_results_dialog(widget, 12)

    assert inserts
    assert inserts[0][0] == "test_results"
    assert inserts[0][1]["ladder_test_id"] == 12
    assert inserts[0][1]["load_session_id"] == 55
    assert infos


def test_get_active_load_session_id_ignores_invalid_values(monkeypatch):
    class _Settings:
        def __init__(self, *args, **kwargs):
            pass

        def value(self, key, default=None):
            return "invalid" if key == "workflow_context/load_session_id" else default

    monkeypatch.setattr(ladder_module, "QSettings", _Settings)

    assert ladder_module._get_active_load_session_id() is None
