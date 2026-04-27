from types import SimpleNamespace

from src.modules import chronograph_importer as chrono_module


class _FakeCombo:
    def __init__(self, value):
        self._value = value

    def currentData(self):
        return self._value


class _FakeLineEdit:
    def __init__(self, value=""):
        self._value = value

    def text(self):
        return self._value


class _FakeNotes:
    def __init__(self, value=""):
        self._value = value

    def toPlainText(self):
        return self._value


class _MissingAmmoDb:
    def __init__(self):
        self.update_calls = []
        self.insert_calls = []

    def get_by_id(self, table, record_id):
        return None

    def update(self, table, data, condition, params=()):
        self.update_calls.append((table, data, condition, params))

    def insert(self, table, data):
        self.insert_calls.append((table, data))
        return 1


class _SavingAmmoDb:
    def __init__(self):
        self.insert_calls = []
        self.record_calls = []
        self.refresh_calls = []

    def get_by_id(self, table, record_id):
        if table == "ammo_profiles":
            return {"id": record_id, "rifle_id": 7}
        return {"id": record_id}

    def insert(self, table, data):
        self.insert_calls.append((table, data))
        if table == "chronograph_sessions":
            return 11
        return len(self.insert_calls)

    def record_barrel_chronograph_observation(self, *args, **kwargs):
        self.record_calls.append((args, kwargs))

    def refresh_powder_lot_learning_profile(self, lot_id):
        self.refresh_calls.append(lot_id)
        return {}


def _make_session():
    reading = chrono_module.ChronographReading(shot_number=1, velocity_fps=2700.0)
    return chrono_module.ChronographSession(
        device_type="Garmin Xero",
        session_name="Test session",
        date="2026-03-25",
        velocities=[2700.0],
        avg_velocity=2700.0,
        es=0.0,
        sd=0.0,
        min_velocity=2700.0,
        max_velocity=2700.0,
        shot_count=1,
        raw_data=[reading],
    )


def _make_quality_session(*, shot_count=5, es=18.0, sd=7.0):
    readings = [
        chrono_module.ChronographReading(
            shot_number=index + 1,
            velocity_fps=2700.0 + index,
        )
        for index in range(shot_count)
    ]
    return chrono_module.ChronographSession(
        device_type="Garmin Xero",
        session_name="Quality session",
        date="2026-03-25",
        velocities=[reading.velocity_fps for reading in readings],
        avg_velocity=2700.0,
        es=es,
        sd=sd,
        min_velocity=2698.0,
        max_velocity=2710.0,
        shot_count=shot_count,
        raw_data=readings,
    )


def test_update_ammo_velocity_handles_missing_profile(monkeypatch):
    warnings = []
    fake_db = _MissingAmmoDb()
    monkeypatch.setattr(
        chrono_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    widget = SimpleNamespace(
        current_session=_make_session(),
        ammo_combo=_FakeCombo(7),
        db=fake_db,
    )

    chrono_module.ChronographImporter.update_ammo_velocity(widget)

    assert warnings
    assert fake_db.update_calls == []


def test_save_session_handles_missing_profile(monkeypatch):
    warnings = []
    fake_db = _MissingAmmoDb()
    monkeypatch.setattr(
        chrono_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    widget = SimpleNamespace(
        current_session=_make_session(),
        ammo_combo=_FakeCombo(9),
        db=fake_db,
        file_path_input=_FakeLineEdit("C:/tmp/test.csv"),
        session_notes=_FakeNotes("note"),
    )

    chrono_module.ChronographImporter.save_session(widget)

    assert warnings
    assert fake_db.insert_calls == []


def test_quality_summary_marks_ready_for_stable_series():
    summary = chrono_module.build_chronograph_quality_summary(
        _make_quality_session(shot_count=7, es=16.0, sd=6.5)
    )

    assert summary["level"] == "ready"
    assert "Stable chrono series" in summary["title"]


def test_quality_summary_marks_needs_more_data_for_short_series():
    summary = chrono_module.build_chronograph_quality_summary(
        _make_quality_session(shot_count=3, es=9.0, sd=4.0)
    )

    assert summary["level"] == "needs_more_data"
    assert "more shots" in summary["message"].lower()


def test_quality_summary_marks_unstable_for_high_spread():
    summary = chrono_module.build_chronograph_quality_summary(
        _make_quality_session(shot_count=8, es=52.0, sd=17.0)
    )

    assert summary["level"] == "unstable"
    assert "Check load" in summary["message"]


def test_build_chronograph_evidence_basis_labels_measured_modeled_and_recommended():
    summary = chrono_module.build_chronograph_evidence_basis(
        _make_quality_session(shot_count=6, es=18.0, sd=6.0)
    )

    assert summary["title"] == "Evidence basis"
    assert "Measured:" in summary["message"]
    assert "Modeled:" in summary["message"]
    assert "Recommended:" in summary["message"]


def test_format_velocity_uses_metric_when_global_units_are_metric(monkeypatch):
    monkeypatch.setattr(chrono_module, "_get_global_unit_system", lambda: "metric")

    assert "m/s" in chrono_module._format_velocity(2700.0)
    assert "fps" in chrono_module._format_velocity(2700.0)


def test_get_active_workflow_context_prefers_canonical_session_runtime(monkeypatch):
    class _FakeSettings:
        def value(self, key, default=None):
            mapping = {
                "workflow_context/workflow_id": "12",
                "workflow_context/workflow_name": "OCW Test",
                "workflow_context/load_session_id": "33",
                "workflow_context/rifle_id": "stale-rifle",
                "workflow_context/barrel_id": "stale-barrel",
                "workflow_context/barrel_name": "Old Barrel",
                "workflow_context/barrel_configuration_id": "old-cfg",
                "workflow_context/barrel_configuration_name": "Old Setup",
                "workflow_context/created_date": "2026-03-20",
            }
            return mapping.get(key, default)

    monkeypatch.setattr(
        chrono_module, "QSettings", lambda *args, **kwargs: _FakeSettings()
    )
    monkeypatch.setattr(chrono_module, "get_database", lambda: object())
    monkeypatch.setattr(
        chrono_module,
        "build_active_workflow_context_from_settings",
        lambda settings, db, int_fields=(): {
            "workflow_id": 12,
            "load_session_id": 33,
            "workflow_name": "OCW Test",
            "rifle_id": 7,
            "barrel_id": "B1",
            "barrel_name": "24in Match",
            "barrel_configuration_id": "cfg-supp",
            "barrel_configuration_name": "Suppressed",
            "usage_profile_name": "Competition",
        },
    )

    context = chrono_module._get_active_workflow_context()

    assert context["workflow_id"] == 12
    assert context["load_session_id"] == 33
    assert context["rifle_id"] == 7
    assert context["barrel_id"] == "B1"
    assert context["barrel_name"] == "24in Match"
    assert context["barrel_configuration_name"] == "Suppressed"
    assert context["usage_profile_name"] == "Competition"


def test_save_session_refreshes_canonical_measurement_summary(monkeypatch):
    infos = []
    refresh_calls = []
    fake_db = _SavingAmmoDb()

    monkeypatch.setattr(
        chrono_module.QMessageBox, "information", lambda *a, **k: infos.append((a, k))
    )
    monkeypatch.setattr(
        chrono_module,
        "_get_active_workflow_context",
        lambda: {
            "load_session_id": 33,
            "rifle_id": 7,
            "barrel_id": "B1",
            "barrel_name": "24in Match",
            "barrel_configuration_id": "cfg-supp",
            "barrel_configuration_name": "Suppressed",
        },
    )
    monkeypatch.setattr(chrono_module, "_get_active_batch_context", lambda: {})
    monkeypatch.setattr(
        chrono_module,
        "refresh_load_session_measurement_summary",
        lambda db, session_id, source=None: refresh_calls.append((session_id, source)),
    )

    widget = SimpleNamespace(
        current_session=_make_quality_session(shot_count=5, es=14.0, sd=5.0),
        ammo_combo=_FakeCombo(9),
        db=fake_db,
        file_path_input=_FakeLineEdit("C:/tmp/test.csv"),
        session_notes=_FakeNotes("note"),
    )

    chrono_module.ChronographImporter.save_session(widget)

    assert any(table == "chronograph_sessions" for table, _ in fake_db.insert_calls)
    assert any(table == "chronograph_readings" for table, _ in fake_db.insert_calls)
    assert fake_db.record_calls
    assert refresh_calls == [(33, "chronograph_importer.save_session")]
    assert infos
