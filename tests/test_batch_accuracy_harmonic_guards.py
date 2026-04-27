from types import SimpleNamespace

from src.modules import batch_workspace as batch_module
from src.modules import harmonic_wizard as harmonic_module
from src.modules import rifle_accuracy_test_system as accuracy_module


class _FakeItem:
    def __init__(self, text="", data=None):
        self._text = text
        self._data = data

    def text(self):
        return self._text

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


def test_harmonic_analyze_test_handles_missing_test(monkeypatch):
    warnings = []
    queries = []
    monkeypatch.setattr(
        harmonic_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    class _Db:
        def execute_query(self, query, params=()):
            queries.append((query, params))
            return []

    reloaded = []
    widget = SimpleNamespace(
        tests_table=_FakeTable(item=_FakeItem(data=44)),
        db=_Db(),
        load_tests=lambda: reloaded.append(True),
    )

    harmonic_module.HarmonicWizard.analyze_test(widget)

    assert warnings
    assert reloaded == [True]
    assert len(queries) == 1


def test_accuracy_view_details_handles_missing_test(monkeypatch):
    warnings = []
    monkeypatch.setattr(
        accuracy_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    class _Db:
        def get_by_id(self, table, record_id):
            return None

    reloaded = []
    widget = SimpleNamespace(
        table=_FakeTable(item=_FakeItem(text="12")),
        db=_Db(),
        load_tests=lambda: reloaded.append(True),
    )

    accuracy_module.RifleAccuracyTestManager.view_test_details(widget)

    assert warnings
    assert reloaded == [True]


def test_accuracy_print_sheet_handles_missing_test(monkeypatch):
    warnings = []
    monkeypatch.setattr(
        accuracy_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )

    class _Db:
        def get_by_id(self, table, record_id):
            return None

    reloaded = []
    widget = SimpleNamespace(
        table=_FakeTable(item=_FakeItem(text="18")),
        db=_Db(),
        load_tests=lambda: reloaded.append(True),
    )

    accuracy_module.RifleAccuracyTestManager.print_test_sheet(widget)

    assert warnings
    assert reloaded == [True]


def test_batch_workspace_load_batch_handles_missing_batch(monkeypatch):
    warnings = []
    monkeypatch.setattr(
        batch_module.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append((a, k)),
    )
    monkeypatch.setattr(batch_module, "get_batch_project", lambda db, batch_id: None)

    refreshed = []
    widget = SimpleNamespace(
        db=object(),
        current_batch_id=99,
        _current_batch={"id": 99},
        refresh_batches=lambda: refreshed.append(True),
    )

    batch_module.BatchWorkspace.load_batch(widget, 99)

    assert warnings
    assert refreshed == [True]
    assert widget.current_batch_id is None
    assert widget._current_batch is None


def test_get_active_workflow_verification_advisory_reads_workflow_summary(monkeypatch):
    monkeypatch.setattr(
        batch_module,
        "_get_active_workflow_context",
        lambda: {"workflow_id": 12},
    )

    class _Db:
        def get_by_id(self, table, record_id):
            assert table == "load_development_workflows"
            assert record_id == 12
            return {"id": 12, "powder_id": 7, "bullet_id": 8, "primer_id": 9}

    class _WorkflowModule:
        @staticmethod
        def build_workflow_component_verification_advisory(db, workflow):
            assert workflow["id"] == 12
            return {
                "title": "Samlet lotverifisering",
                "message": "Fokuser på Kruttlot og Primerlot.",
                "level": "warning",
            }

    monkeypatch.setattr(
        batch_module.importlib, "import_module", lambda name: _WorkflowModule
    )

    advisory = batch_module._get_active_workflow_verification_advisory(_Db())

    assert advisory["title"] == "Samlet lotverifisering"
    assert advisory["level"] == "warning"
    assert "Kruttlot" in advisory["message"]


def test_get_active_workflow_verification_advisory_reads_checks(monkeypatch):
    monkeypatch.setattr(
        batch_module,
        "_get_active_workflow_context",
        lambda: {"workflow_id": 13},
    )

    class _Db:
        def get_by_id(self, table, record_id):
            return {"id": 13}

    class _WorkflowModule:
        @staticmethod
        def build_workflow_component_verification_advisory(db, workflow):
            return {
                "title": "Samlet lotverifisering",
                "message": "Fokuser på Kruttlot og Primerlot.",
                "level": "critical",
                "checks": [
                    "Kruttlot: Kjør 5 kontrollskudd med start -0.2 gr.",
                    "Primerlot: Chrono minst 5 kontrollskudd.",
                ],
            }

    monkeypatch.setattr(
        batch_module.importlib, "import_module", lambda name: _WorkflowModule
    )

    advisory = batch_module._get_active_workflow_verification_advisory(_Db())

    assert len(advisory["checks"]) == 2
    assert "Kruttlot" in advisory["checks"][0]


def test_format_workflow_verification_guidance_includes_checks():
    guidance = batch_module._format_workflow_verification_guidance(
        {
            "title": "Samlet lotverifisering",
            "message": "Flere komponentledd peker på konservativ bekreftelse.",
            "checks": [
                "Kruttlot: Kjør 5 kontrollskudd med start -0.2 gr.",
                "Primerlot: Chrono minst 5 kontrollskudd.",
            ],
        }
    )

    assert "Samlet lotverifisering" in guidance
    assert "Recommended verification setup:" in guidance
    assert "- Kruttlot: Kjør 5 kontrollskudd med start -0.2 gr." in guidance


def test_parse_analysis_payload_handles_json_and_invalid_text():
    parsed = batch_module._parse_analysis_payload('{"score": 82.0}')
    invalid = batch_module._parse_analysis_payload("not-json")

    assert parsed["score"] == 82.0
    assert invalid == {}


def test_refresh_analysis_preserves_verification_advisory(monkeypatch):
    updates = []
    sync_calls = []
    monkeypatch.setattr(
        batch_module,
        "update_batch_project",
        lambda db, batch_id, payload: updates.append((batch_id, payload)),
    )
    monkeypatch.setattr(
        batch_module,
        "refresh_load_session_measurement_summary",
        lambda db, session_id, source=None: sync_calls.append((session_id, source)),
    )

    class _Analyzer:
        def __init__(self, *args, **kwargs):
            pass

        def recommend_next(self):
            return {
                "score": 83.0,
                "confidence": 71.0,
                "improvement_potential": "moderat",
                "trend_summary": "Stigende hastighet",
                "next_focus": "Bekreft node",
            }

        def to_html(self):
            return "<b>ok</b>"

    monkeypatch.setattr(batch_module, "BatchAnalyzer", _Analyzer)

    class _Label:
        def __init__(self):
            self.value = None

        def setText(self, value):
            self.value = value

    class _Text:
        def __init__(self):
            self.value = None

        def setHtml(self, value):
            self.value = value

    widget = SimpleNamespace(
        db=object(),
        current_batch_id=44,
        _current_batch={
            "load_session_id": 33,
            "analysis_json": {
                "verification_advisory": {
                    "title": "Samlet lotverifisering",
                    "message": "Fokuser på Kruttlot og Primerlot.",
                }
            },
        },
        _current_sessions=[],
        _current_notes=[],
        _current_attachments=[],
        _combined_chronograph_stats=lambda: {},
        analysis_score_label=_Label(),
        analysis_confidence_label=_Label(),
        analysis_potential_label=_Label(),
        analysis_trend_label=_Label(),
        analysis_focus_label=_Label(),
        analysis_text=_Text(),
    )

    batch_module.BatchWorkspace.refresh_analysis(widget)

    assert updates
    payload = updates[0][1]["analysis_json"]
    assert payload["verification_advisory"]["title"] == "Samlet lotverifisering"
    assert widget.analysis_focus_label.value == "Bekreft node"
    assert sync_calls == [(33, "batch_workspace.refresh_analysis")]


def test_build_batch_evidence_basis_labels_measured_modeled_and_recommended():
    summary = batch_module._build_batch_evidence_basis(
        {
            "charge_weight_grains": 42.5,
            "coal_mm": 71.2,
        },
        {
            "score": 82.0,
            "confidence": 74.0,
            "next_focus": "Bekreft node",
            "verification_advisory": {"title": "Samlet lotverifisering"},
        },
        [
            {"group_size_mm": 19.5, "notes": "Trygg og rolig serie"},
        ],
        {"avg_velocity_fps": 2710.0},
    )

    assert summary["title"] == "Evidence basis"
    assert "Measured:" in summary["message"]
    assert "Modeled:" in summary["message"]
    assert "Recommended:" in summary["message"]


def test_format_distance_m_uses_imperial_when_global_units_are_imperial(monkeypatch):
    monkeypatch.setattr(batch_module, "_get_global_unit_system", lambda: "imperial")

    formatted = batch_module._format_distance_m(100.0)

    assert "yd" in formatted
    assert "m" in formatted


def test_format_group_mm_uses_imperial_when_global_units_are_imperial(monkeypatch):
    monkeypatch.setattr(batch_module, "_get_global_unit_system", lambda: "imperial")

    formatted = batch_module._format_group_mm(25.4)

    assert "in" in formatted
    assert "mm" in formatted
