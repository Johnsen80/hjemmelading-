from types import SimpleNamespace

from src.modules import workflow_resume_dialog as dialog_module


class _FakeItem:
    def __init__(self, workflow_id=1, workflow_name="Test Workflow"):
        self.state = SimpleNamespace(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
        )


class _FakeList:
    def __init__(self, item):
        self._item = item
        self.removed_rows = []

    def currentItem(self):
        return self._item

    def currentRow(self):
        return 0

    def takeItem(self, row):
        self.removed_rows.append(row)

    def count(self):
        return 0


def test_clear_workflow_uses_selected_item_message(monkeypatch):
    questions = []
    infos = []
    monkeypatch.setattr(
        dialog_module.QMessageBox,
        "question",
        lambda *a, **k: questions.append((a, k))
        or dialog_module.QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        dialog_module.QMessageBox,
        "information",
        lambda *a, **k: infos.append((a, k)),
    )

    cleared = []
    rejected = []
    widget = SimpleNamespace(
        workflow_list=_FakeList(_FakeItem(workflow_id=9, workflow_name="Alpha")),
        state_manager=SimpleNamespace(
            clear_state=lambda workflow_id: cleared.append(workflow_id)
        ),
        reject=lambda: rejected.append(True),
    )

    dialog_module.WorkflowResumeDialog.clear_workflow(widget)

    assert questions
    assert "Alpha" in questions[0][0][2]
    assert cleared == [9]
    assert rejected == [True]
