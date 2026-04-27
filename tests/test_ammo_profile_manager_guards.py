from types import SimpleNamespace

from PyQt6.QtCore import Qt

from src.modules import ammo_profile_manager as ammo_module


class _FakeItem:
    def __init__(self, value):
        self._value = value

    def data(self, role):
        if role == Qt.ItemDataRole.UserRole:
            return self._value
        return None


class _FakeTable:
    def __init__(self, profile_id):
        self._profile_id = profile_id

    def currentRow(self):
        return 0

    def item(self, row, column):
        assert row == 0
        assert column == 0
        return _FakeItem(self._profile_id)


class _MissingProfileDb:
    def get_by_id(self, table, record_id):
        return None

    def get_all(self, table):
        return []


def test_edit_profile_handles_missing_profile(monkeypatch):
    warnings = []
    reloaded = {"called": False}

    monkeypatch.setattr(
        ammo_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingProfileDb(),
        table=_FakeTable(12),
        load_data=lambda: reloaded.__setitem__("called", True),
    )

    ammo_module.AmmoProfileManager.edit_profile(manager)

    assert warnings
    assert reloaded["called"] is True


def test_copy_profile_handles_missing_profile(monkeypatch):
    warnings = []
    reloaded = {"called": False}

    monkeypatch.setattr(
        ammo_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingProfileDb(),
        table=_FakeTable(15),
        load_data=lambda: reloaded.__setitem__("called", True),
    )

    ammo_module.AmmoProfileManager.copy_profile(manager)

    assert warnings
    assert reloaded["called"] is True


def test_format_bc_summary_prefers_g7_when_both_values_exist():
    summary = ammo_module._format_bc_summary(0.462, 0.235)

    assert "0.235" in summary
    assert "0.462" in summary


def test_format_bc_summary_handles_missing_values():
    summary = ammo_module._format_bc_summary(None, None)

    assert "BC" in summary or "ballistics" in summary.lower()


def test_format_bc_summary_prefers_segmented_bc_when_available():
    summary = ammo_module._format_bc_summary(
        0.462,
        0.235,
        '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
    )

    assert "2600-3000 fps" in summary
    assert "0.245" in summary


def test_normalize_bc_segments_json_returns_compact_json_for_valid_segments():
    normalized = ammo_module._normalize_bc_segments_json(
        '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]'
    )

    assert normalized is not None
    assert "2600.0" in normalized
    assert "0.245" in normalized


def test_format_bc_segments_summary_mentions_velocity_window():
    summary = ammo_module._format_bc_segments_summary(
        '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]'
    )

    assert "2600-3000 fps" in summary
    assert "0.245" in summary
