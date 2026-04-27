from types import SimpleNamespace

from src.modules import modern_load_builder as mlb_module


class _FakeCombo:
    def __init__(self, data=None):
        self._data = data

    def currentData(self):
        return self._data


class _FakeLabel:
    def __init__(self):
        self.value = None
        self.style = None

    def setText(self, text):
        self.value = text

    def setStyleSheet(self, style):
        self.style = style


def test_sync_active_load_session_context_persists_barrel_configuration(monkeypatch):
    captured: list[dict[str, object]] = []

    def _record_update(db, session_id, **kwargs):
        captured.append({"db": db, "session_id": session_id, **kwargs})
        return {"id": session_id}

    monkeypatch.setattr(mlb_module, "_get_active_load_session_id", lambda: 42)
    monkeypatch.setattr(mlb_module, "update_load_development_session", _record_update)
    monkeypatch.setattr(
        mlb_module,
        "build_load_session_runtime",
        lambda db, session_id: {"session": {"id": session_id}, "delta": {}},
    )

    widget = SimpleNamespace(
        db=object(),
        rifle_data={"id": 7, "name": "Config Rifle", "caliber": "308 Win"},
        current_ammo_profile_id=55,
        _latest_load_session_runtime=None,
        _get_active_barrel_id=lambda: "pipe-1",
        _get_active_barrel_details=lambda: {"id": "pipe-1", "name": "24in Match"},
        _get_active_barrel_configuration_context=lambda: {
            "barrel_id": "pipe-1",
            "barrel_name": "24in Match",
            "barrel_configuration_id": "pipe-1-suppressor-a-tec-h2",
            "barrel_configuration_name": "Suppressor On (A-TEC H2)",
            "barrel_configuration_snapshot": {
                "barrel_id": "pipe-1",
                "muzzle_device_type": "suppressor",
                "muzzle_device_model": "A-TEC H2",
                "muzzle_device_weight_g": 420,
                "suppressor_used": True,
            },
        },
        _build_active_load_session_analysis_payloads=lambda: (
            {"next_action": "verify"},
            {"recommendation": "ok"},
            {"evidence": "ok"},
            {"learning": "ok"},
        ),
        _build_active_load_session_component_selection=lambda: {"bullet_id": 1},
        _build_active_load_session_intake_snapshot=lambda: {"charge_weight_gr": 42.0},
    )

    mlb_module.ModernLoadBuilder._sync_active_load_session_context(widget)

    assert len(captured) == 1
    update_call = captured[0]
    assert update_call["session_id"] == 42
    assert update_call["updates"]["rifle_id"] == 7
    assert update_call["updates"]["barrel_id"] == "pipe-1"
    assert update_call["updates"]["barrel_name"] == "24in Match"
    assert (
        update_call["updates"]["barrel_configuration_id"]
        == "pipe-1-suppressor-a-tec-h2"
    )
    assert (
        update_call["updates"]["barrel_configuration_name"]
        == "Suppressor On (A-TEC H2)"
    )
    assert (
        update_call["barrel_configuration_snapshot"]["muzzle_device_type"]
        == "suppressor"
    )
    assert update_call["barrel_configuration_snapshot"]["muzzle_device_weight_g"] == 420
    assert widget._latest_load_session_runtime == {"session": {"id": 42}, "delta": {}}


def test_get_available_barrel_configurations_prefers_explicit_named_profiles():
    widget = SimpleNamespace(
        _get_rifle_profile_details=lambda: {
            "active_barrel_id": "pipe-1",
            "barrel_configurations": [
                {
                    "id": "cfg-suppressed",
                    "name": "Match Suppressed",
                    "barrel_id": "pipe-1",
                    "is_active": True,
                },
                {
                    "id": "cfg-brake",
                    "name": "Brake Training",
                    "barrel_id": "pipe-1",
                    "is_active": False,
                },
                {
                    "id": "cfg-other-barrel",
                    "name": "Other Barrel Setup",
                    "barrel_id": "pipe-2",
                    "is_active": True,
                },
            ],
        },
        _get_active_barrel_id=lambda: "pipe-1",
        _get_active_barrel_configuration_context=lambda: {},
    )

    configurations = mlb_module.ModernLoadBuilder._get_available_barrel_configurations(
        widget
    )

    assert [item["id"] for item in configurations] == ["cfg-suppressed", "cfg-brake"]
    assert configurations[0]["name"] == "Match Suppressed"


def test_apply_active_barrel_configuration_selection_persists_profile_details():
    saved: list[dict[str, object]] = []
    widget = SimpleNamespace(
        _get_rifle_profile_details=lambda: {
            "active_barrel_id": "pipe-1",
            "active_barrel_configuration_id": "cfg-suppressed",
            "barrel_configurations": [
                {
                    "id": "cfg-suppressed",
                    "name": "Match Suppressed",
                    "barrel_id": "pipe-1",
                    "is_active": True,
                },
                {
                    "id": "cfg-brake",
                    "name": "Brake Training",
                    "barrel_id": "pipe-1",
                    "is_active": False,
                },
            ],
        },
        _get_active_barrel_id=lambda: "pipe-1",
        _save_rifle_profile_details=lambda details: saved.append(details) or True,
    )

    changed = mlb_module.ModernLoadBuilder._apply_active_barrel_configuration_selection(
        widget,
        "cfg-brake",
    )

    assert changed is True
    assert saved
    saved_details = saved[0]
    assert saved_details["active_barrel_configuration_id"] == "cfg-brake"
    assert saved_details["active_barrel_configuration_name"] == "Brake Training"
    assert saved_details["barrel_configurations"][0]["is_active"] is False
    assert saved_details["barrel_configurations"][1]["is_active"] is True


def test_on_barrel_configuration_changed_refreshes_and_syncs(monkeypatch):
    calls: list[str] = []
    widget = SimpleNamespace(
        barrel_configuration_combo=_FakeCombo("cfg-brake"),
        _apply_active_barrel_configuration_selection=lambda configuration_id: configuration_id
        == "cfg-brake",
        _refresh_barrel_configuration_selector=lambda: calls.append("refresh-selector"),
        _refresh_active_rifle_context=lambda: calls.append("refresh-context"),
        _sync_active_load_session_context=lambda: calls.append("sync-session"),
        _refresh_runtime_context_summary=lambda: calls.append("runtime-summary"),
        evidence_label=SimpleNamespace(
            setText=lambda text: calls.append(f"evidence:{text}")
        ),
        _build_evidence_summary=lambda: "Evidence summary",
        _refresh_evidence_actions=lambda: calls.append("refresh-evidence"),
        update_visualization=lambda: calls.append("visualize"),
    )

    mlb_module.ModernLoadBuilder.on_barrel_configuration_changed(widget)

    assert calls[:4] == [
        "refresh-selector",
        "refresh-context",
        "sync-session",
        "runtime-summary",
    ]
    assert "evidence:Evidence summary" in calls
    assert "refresh-evidence" in calls
    assert "visualize" in calls


def test_refresh_runtime_context_summary_prefers_normalized_runtime_shape():
    runtime_label = _FakeLabel()
    delta_label = _FakeLabel()
    runtime_payload = {
        "context": {
            "session_uid": "session-abcdef12",
            "status": "active",
            "lifecycle_stage": "validation",
            "confidence_label": "high",
            "safety_status": "ok",
            "usage_profile_name": "Competition",
            "powder_lot_number": "VV-N555-A1",
        },
        "identity": {
            "rifle": {"label": "TRG 6.5"},
            "barrel": {
                "label": '26" Match',
                "configuration_label": "Suppressed",
            },
            "components": {
                "powder": {"label": "Vihtavuori N555"},
            },
            "lots": {
                "powder": {"lot_number": "VV-N555-A1"},
            },
            "usage": {"label": "Competition"},
        },
        "evidence": {
            "summary": {
                "chronograph_import_count": 2,
                "test_result_count": 3,
                "batch_count": 1,
                "best_group_mm": 12.4,
                "latest_avg_velocity_fps": 2815.0,
            }
        },
        "recommendation": {
            "control_state": {
                "charge_state": "hold",
                "seating_state": "verify",
                "trust_label": "high",
            },
            "baseline": {
                "summary": '26" Match / Suppressed',
            },
        },
        "delta": {
            "summary": "No critical drift detected.",
        },
    }
    widget = SimpleNamespace(
        runtime_context_label=runtime_label,
        runtime_delta_label=delta_label,
        _latest_load_session_runtime=None,
        _get_active_load_session_runtime=lambda: runtime_payload,
        _get_cached_or_active_load_session_runtime=lambda: runtime_payload,
    )

    mlb_module.ModernLoadBuilder._refresh_runtime_context_summary(widget)

    assert "TRG 6.5 | Competition" in runtime_label.value
    assert 'Barrel: 26" Match / Suppressed' in runtime_label.value
    assert "Active lots: Powder Vihtavuori N555 [VV-N555-A1]" in runtime_label.value
    assert (
        "Runtime: status active | stage validation | confidence high | safety ok | session session-"
        in runtime_label.value
    )
    assert runtime_label.style == mlb_module._advisory_style("ok")
    assert "No critical drift detected." in delta_label.value


def test_get_cached_or_active_load_session_runtime_caches_fetched_runtime():
    calls = []
    runtime = {"context": {"session_uid": "session-1"}}
    widget = SimpleNamespace(
        _latest_load_session_runtime=None,
        _get_active_load_session_runtime=lambda: calls.append("fetch") or runtime,
    )

    first = mlb_module.ModernLoadBuilder._get_cached_or_active_load_session_runtime(
        widget
    )
    second = mlb_module.ModernLoadBuilder._get_cached_or_active_load_session_runtime(
        widget
    )

    assert first == runtime
    assert second == runtime
    assert widget._latest_load_session_runtime == runtime
    assert calls == ["fetch"]
