from types import SimpleNamespace

from src.modules import workflow_hub as workflow_hub_module


def test_create_list_button_marks_legacy_workflow(monkeypatch):
    captured = {}

    class _FakeButton:
        def __init__(self, text, parent=None):
            captured["text"] = text
            self._tooltip = None

        def setCursor(self, *_args, **_kwargs):
            pass

        def setToolTip(self, value):
            captured["tooltip"] = value

        def setProperty(self, *_args, **_kwargs):
            pass

        class _Signal:
            def connect(self, *_args, **_kwargs):
                pass

        clicked = _Signal()

    monkeypatch.setattr(workflow_hub_module, "QPushButton", _FakeButton)

    fake_hub = SimpleNamespace(
        workflow_selected=SimpleNamespace(emit=lambda *_args, **_kwargs: None),
        _legacy_workflow_ids=lambda: {"primer_tools"},
        _register_mode_widget=lambda *_args, **_kwargs: None,
    )

    workflow_hub_module.WorkflowHub._create_list_button(
        fake_hub,
        "primer_tools",
        "",
        "Primer Tools",
        "Selector, seating guide, pressure diagnostics",
    )

    assert "(Legacy)" in captured["text"]
    assert "Legacy" in captured["tooltip"]
