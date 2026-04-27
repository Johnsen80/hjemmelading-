from src.modules.digital_twin import DigitalTwin


def test_digital_twin_fallback_mode_still_produces_preview_state() -> None:
    twin = DigitalTwin(
        rifle={"barrel_length_mm": 610, "twist": "1:8"},
        ammo={"powder_charge": 44.0, "bullet_weight": 140.0, "coal_mm": 71.0},
        environment={"temperature_c": 15.0, "pressure_hpa": 1013.25},
    )

    state = twin.get_state()

    assert state["analysis_mode"] == "fallback"
    assert isinstance(state["predicted_velocity"], float)
    assert isinstance(state["predicted_pressure"], float)
    assert isinstance(state["harmonics"], dict)
    assert "bullet_fit" in state
    assert "game_suitability" in state
    assert isinstance(state["guidance"], dict)
    assert "next_step" in state["guidance"]
    assert state["guidance"]["analysis_mode"] == "fallback"
    assert state["guidance"]["trust_label"] == "Low trust"
    assert state["guidance"]["trust_score"] <= 42.0
    assert "Preview only" in state["guidance"]["basis_note"]
    assert "Preview only" in state["guidance"]["next_step"]
    assert isinstance(state["smart_engine"], dict)
    assert (
        state["smart_engine"]["engine_result"]["engine_state"]["offline_only"] is True
    )
    assert "engine_gate" in state["guidance"]
    assert any("Preview only" in item for item in state["warnings"])
    assert not any(item == "Pressure is near the limit." for item in state["warnings"])


def test_digital_twin_uses_service_analysis_when_ids_are_available(monkeypatch) -> None:
    def fake_analyze_load(request):
        return {
            "result": {"muzzle_velocity_fps": 2750.0, "peak_pressure_psi": 55200.0},
            "harmonics": {
                "node_bands": [],
                "harmonic_score": 14.2,
                "estimated_frequency_hz": 78.0,
                "period_ms": 12.8,
                "stability_tier": "stable",
                "sensitivity": {"seating_depth": 1.2},
            },
            "bullet_fit_summary": {
                "level": "ok",
                "title": "Bullet fit looks strong",
                "message": "Good match.",
                "fit_score": 88.0,
            },
            "game_suitability_summary": {
                "level": "ok",
                "title": "Suitable for Roe deer / medium game",
                "message": "Looks usable.",
            },
            "pressure_assessment": {"level": "warning"},
            "stability_assessment": {"level": "ok", "message": "Stable enough."},
            "input_quality": {
                "title": "Good input quality",
                "message": "Measured data exists.",
                "score": 82.0,
            },
            "recommendation": {
                "level": "ok",
                "summary": "Keep current baseline.",
                "charge_window_gr": [44.3, 44.7],
                "seating_window_mm": [-0.1, 0.1],
                "next_step": "Confirm with a short validation string.",
            },
        }

    monkeypatch.setattr("src.modules.digital_twin.analyze_load", fake_analyze_load)

    twin = DigitalTwin(
        rifle={
            "id": 1,
            "barrel_id": "A",
            "barrel_name": "24in Match",
            "usage_profile": "hunting_medium",
        },
        ammo={"bullet_id": 2, "powder_id": 3, "powder_charge": 44.5, "coal_mm": 71.2},
        environment={"temperature_c": 12.0, "pressure_hpa": 1008.0},
    )

    state = twin.get_state()

    assert state["analysis_mode"] == "service"
    assert state["predicted_velocity"] == 838.2
    assert state["predicted_pressure"] == 55200.0
    assert state["bullet_fit"]["fit_score"] == 88.0
    assert state["game_suitability"]["title"].startswith("Suitable")
    assert state["guidance"]["trust_label"] in {"Medium trust", "High trust"}
    assert state["guidance"]["analysis_mode"] == "service"
    assert state["guidance"]["basis_note"] == ""
    assert state["guidance"]["charge_alignment"] == "aligned"
    assert state["guidance"]["next_step"] == "Confirm with a short validation string."
    assert state["guidance"]["engine_gate"] == "Needs matched evidence"
    assert state["guidance"]["engine_protocol"].startswith(
        "Collect matched evidence before stronger claims"
    )
    assert state["guidance"]["engine_confidence_label"] == "low"
    assert (
        "thin evidence" in state["guidance"]["engine_hold"].lower()
        or "promote" in state["guidance"]["engine_hold"].lower()
    )
    assert state["guidance"]["engine_branch_state"] == "unknown"
    assert state["guidance"]["engine_branch_label"] == "Unknown branch"
    assert state["guidance"]["engine_bullet_fit_level"] in {"ok", "warning"}
    assert state["guidance"]["engine_jump_band"] in {"unknown", ""}
    assert (
        "does not determine accuracy" in state["guidance"]["pressure_diagnostic_note"]
    )
    assert "24in Match" in state["guidance"]["pressure_diagnostic_note"]
    assert any("Needs matched evidence" in item for item in state["warnings"])
    assert any("24in Match" in item for item in state["warnings"])


def test_digital_twin_guidance_uses_learned_baseline_context_when_available(
    monkeypatch,
) -> None:
    def fake_analyze_load(request):
        return {
            "result": {"muzzle_velocity_fps": 2750.0, "peak_pressure_psi": 55200.0},
            "harmonics": {
                "node_bands": [],
                "harmonic_score": 14.2,
                "estimated_frequency_hz": 78.0,
                "period_ms": 12.8,
                "stability_tier": "stable",
                "sensitivity": {"seating_depth": 1.2},
            },
            "bullet_fit_summary": {
                "level": "ok",
                "title": "Bullet fit looks strong",
                "message": "Good match.",
                "fit_score": 88.0,
            },
            "game_suitability_summary": {
                "level": "ok",
                "title": "Suitable for Roe deer / medium game",
                "message": "Looks usable.",
            },
            "pressure_assessment": {"level": "warning"},
            "stability_assessment": {"level": "ok", "message": "Stable enough."},
            "input_quality": {
                "title": "Good input quality",
                "message": "Measured data exists.",
                "score": 82.0,
            },
            "recommendation": {
                "level": "ok",
                "summary": "Keep current baseline.",
                "charge_window_gr": [44.3, 44.7],
                "seating_window_mm": [-0.1, 0.1],
                "next_step": "Confirm with a short validation string.",
            },
        }

    monkeypatch.setattr("src.modules.digital_twin.analyze_load", fake_analyze_load)

    twin = DigitalTwin(
        rifle={"id": 1, "barrel_id": "A", "usage_profile": "hunting_medium"},
        ammo={
            "bullet_id": 2,
            "powder_id": 3,
            "powder_charge": 44.9,
            "coal_mm": 71.35,
            "cbto_mm": 68.78,
            "recommendation_baseline": {
                "charge_gr": 44.5,
                "charge_source": "learned",
                "cbto_mm": 68.92,
                "seating_source": "learned",
            },
            "recommendation_control_state": {
                "charge_state": "custom",
                "seating_state": "custom",
            },
        },
        environment={"temperature_c": 12.0, "pressure_hpa": 1008.0},
    )

    state = twin.get_state()

    assert state["recommendation_context"]["baseline"]["charge_source"] == "learned"
    assert state["guidance"]["charge_baseline_kind"] == "learned"
    assert state["guidance"]["charge_baseline_label"] == "learned baseline"
    assert state["guidance"]["seating_baseline_kind"] == "learned"
    assert state["guidance"]["seating_baseline_label"] == "learned baseline"
    assert state["guidance"]["charge_alignment"] == "outside"
    assert state["guidance"]["seating_alignment"] == "outside"
    assert state["guidance"]["charge_return_target"] == "44.50 gr"
    assert state["guidance"]["charge_return_target_gr"] == 44.5
    assert state["guidance"]["seating_return_target"] == "68.92 mm CBTO"
    assert state["guidance"]["seating_return_target_mm"] == 68.92
    assert state["guidance"]["seating_return_target_unit"] == "cbto_mm"
    assert "learned charge" in state["guidance"]["recommended_baseline"]
    assert state["guidance"]["engine_branch_state"] == "custom_branch"
    assert state["guidance"]["engine_branch_label"] == "Custom branch"
    assert state["guidance"]["engine_branch_compare_mode"] == "return_before_compare"
    assert (
        state["guidance"]["engine_branch_display"]
        == "Custom branch (return_before_compare)"
    )
    assert (
        state["guidance"]["engine_branch_action"]
        == "Return charge toward 44.50 gr before treating this as the same candidate."
    )
    assert (
        state["guidance"]["engine_active_return"]
        == "Return charge toward 44.50 gr before treating this as the same candidate."
    )
    assert state["guidance"]["engine_baseline_status"] == "return_to_baseline"
    assert state["guidance"]["engine_baseline_item"].startswith(
        "Charge 44.90 gr is 0.40 gr away"
    )
    assert state["guidance"]["engine_charge_target"] == "44.50 gr"
    assert state["guidance"]["engine_seating_target"] == "68.92 mm CBTO"
    assert (
        "Return charge toward 44.50 gr" in state["guidance"]["engine_baseline_summary"]
    )
    assert "44.50 gr" in state["guidance"]["next_step"]
    assert "Current charge sits outside the learned baseline." in state["warnings"]
    assert "Current seating sits outside the learned baseline." in state["warnings"]


def test_digital_twin_guidance_exposes_recommended_return_targets(monkeypatch) -> None:
    def fake_analyze_load(request):
        return {
            "result": {"muzzle_velocity_fps": 2750.0, "peak_pressure_psi": 54000.0},
            "harmonics": {
                "node_bands": [],
                "harmonic_score": 14.2,
                "estimated_frequency_hz": 78.0,
                "period_ms": 12.8,
                "stability_tier": "stable",
                "sensitivity": {"seating_depth": 1.2},
            },
            "bullet_fit_summary": {
                "level": "ok",
                "title": "Bullet fit looks strong",
                "message": "Good match.",
                "fit_score": 88.0,
            },
            "game_suitability_summary": {
                "level": "ok",
                "title": "Suitable for Roe deer / medium game",
                "message": "Looks usable.",
            },
            "pressure_assessment": {"level": "ok"},
            "stability_assessment": {"level": "ok", "message": "Stable enough."},
            "input_quality": {
                "title": "Good input quality",
                "message": "Measured data exists.",
                "score": 82.0,
            },
            "recommendation": {
                "level": "ok",
                "summary": "Keep current baseline.",
                "charge_window_gr": [44.3, 44.7],
                "seating_window_mm": [-0.1, 0.1],
                "next_step": "Confirm with a short validation string.",
            },
        }

    monkeypatch.setattr("src.modules.digital_twin.analyze_load", fake_analyze_load)

    twin = DigitalTwin(
        rifle={"id": 1, "barrel_id": "A", "usage_profile": "hunting_medium"},
        ammo={
            "bullet_id": 2,
            "powder_id": 3,
            "powder_charge": 44.9,
            "coal_mm": 71.35,
            "recommendation_baseline": {
                "charge_gr": 44.5,
                "charge_source": "recommended",
                "coal_mm": 71.0,
                "seating_source": "recommended",
            },
            "recommendation_control_state": {
                "charge_state": "custom",
                "seating_state": "custom",
            },
        },
        environment={"temperature_c": 12.0, "pressure_hpa": 1008.0},
    )

    state = twin.get_state()

    assert state["guidance"]["charge_baseline_kind"] == "recommended"
    assert state["guidance"]["charge_baseline_label"] == "modeled baseline"
    assert state["guidance"]["charge_return_target"] == "44.50 gr"
    assert state["guidance"]["seating_return_target"] == "71.00 mm COAL"
    assert state["guidance"]["seating_return_target_unit"] == "coal_mm"
    assert state["guidance"]["next_step"] == (
        "Return to the modeled charge baseline at 44.50 gr or validate a new charge before updating the recommendation."
    )
    assert (
        "modeled charge baseline 44.50 gr" in state["guidance"]["recommended_baseline"]
    )
