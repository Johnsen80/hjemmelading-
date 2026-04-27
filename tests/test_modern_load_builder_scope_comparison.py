from types import SimpleNamespace

from src.modules import modern_load_builder as mlb_module


class _FakeLabel:
    def __init__(self):
        self.value = None

    def setText(self, text):
        self.value = text


class _FakeGroup:
    def __init__(self):
        self.visible = None

    def setVisible(self, visible):
        self.visible = visible


class _RecordingDb:
    def __init__(self):
        self.calls = []

    def execute_query(self, query, params=()):
        self.calls.append((query, params))
        return []


def test_scope_comparison_excludes_current_profile():
    fake_db = _RecordingDb()
    widget = SimpleNamespace(
        rifle_data={"id": 7, "name": "Test Rifle"},
        bullet_data={"name": "ELD-M", "weight_grains": 140, "bc_g1": 0.62},
        powder_data={"name": "N555"},
        current_charge=42.5,
        current_ammo_profile_id=88,
        db=fake_db,
        scope_comparison_group=_FakeGroup(),
        scope_comparison_label=_FakeLabel(),
    )

    mlb_module.ModernLoadBuilder.update_scope_comparison(
        widget, {"muzzle_velocity_fps": 2780}
    )

    assert fake_db.calls
    query, params = fake_db.calls[0]
    assert "AND id != ?" in query
    assert params == (7, 88)
    assert widget.scope_comparison_group.visible is True
    assert "first load" in widget.scope_comparison_label.value.lower()


def test_resolve_scope_drag_model_prefers_g7_when_auto(monkeypatch):
    monkeypatch.setattr(
        mlb_module.ModernLoadBuilder,
        "_preferred_drag_model",
        staticmethod(lambda: "AUTO"),
    )

    drag_model, current_bc, prev_bc, current_segment, prev_segment = (
        mlb_module.ModernLoadBuilder._resolve_scope_drag_model(
            {"bc_g1": 0.620, "bc_g7": 0.315},
            0.600,
            0.300,
        )
    )

    assert drag_model == "G7"
    assert current_bc == 0.315
    assert prev_bc == 0.300
    assert current_segment == ""
    assert prev_segment == ""


def test_resolve_scope_drag_model_falls_back_to_g1_when_g7_missing(monkeypatch):
    monkeypatch.setattr(
        mlb_module.ModernLoadBuilder,
        "_preferred_drag_model",
        staticmethod(lambda: "G7"),
    )

    drag_model, current_bc, prev_bc, current_segment, prev_segment = (
        mlb_module.ModernLoadBuilder._resolve_scope_drag_model(
            {"bc_g1": 0.620, "bc_g7": None},
            0.600,
            None,
        )
    )

    assert drag_model == "G1"
    assert current_bc == 0.620
    assert prev_bc == 0.600
    assert current_segment == ""
    assert prev_segment == ""


def test_resolve_scope_drag_model_uses_segmented_bc_when_available(monkeypatch):
    monkeypatch.setattr(
        mlb_module.ModernLoadBuilder,
        "_preferred_drag_model",
        staticmethod(lambda: "AUTO"),
    )

    drag_model, current_bc, prev_bc, current_segment, prev_segment = (
        mlb_module.ModernLoadBuilder._resolve_scope_drag_model(
            {
                "bc_g1": 0.620,
                "bc_g7": 0.315,
                "bc_segments_json": [
                    {"velocity_fps_min": 2600, "velocity_fps_max": 3000, "bc_g7": 0.245}
                ],
            },
            0.600,
            0.300,
            '[{"velocity_fps_min":2500,"velocity_fps_max":2900,"bc_g7":0.240}]',
            2710.0,
            2680.0,
        )
    )

    assert drag_model == "G7"
    assert current_bc == 0.245
    assert prev_bc == 0.240
    assert current_segment.startswith("G7 0.245 @ 792.5 m/s")
    assert "3000" in current_segment
    assert prev_segment.startswith("G7 0.240 @ 762.0 m/s")
    assert "2900" in prev_segment
