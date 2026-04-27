from types import SimpleNamespace

from src.modules import component_database as component_module


class _FakeItem:
    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text


class _FakeTable:
    def __init__(self, cells):
        self._cells = cells

    def currentRow(self):
        return 0

    def item(self, row, column):
        del row
        return self._cells.get(column)


def test_on_bullet_double_click_handles_missing_numeric_cells():
    emitted = []
    widget = SimpleNamespace(
        bullets_table=_FakeTable(
            {
                0: _FakeItem("Hornady"),
                1: _FakeItem("ELD-M"),
                2: _FakeItem("6.5mm"),
                3: None,
                4: _FakeItem("bad-number"),
                5: _FakeItem(""),
            }
        ),
        component_selected=SimpleNamespace(
            emit=lambda payload: emitted.append(payload)
        ),
    )

    component_module.ComponentDatabaseManager.on_bullet_double_click(widget)

    assert emitted == [
        {
            "manufacturer": "Hornady",
            "name": "ELD-M",
            "caliber": "6.5mm",
            "weight": 0.0,
            "bc_g1": 0.0,
            "bc_g7": 0.0,
        }
    ]


def test_normalize_bc_segments_json_returns_none_for_invalid_payload():
    assert component_module._normalize_bc_segments_json("not-json") is None


def test_format_bc_segments_summary_describes_segments():
    summary = component_module._format_bc_segments_summary(
        '[{"velocity_fps_min":2000,"velocity_fps_max":2599,"bc_g7":0.228}]'
    )

    assert "2000-2599 fps" in summary
    assert "0.228" in summary
