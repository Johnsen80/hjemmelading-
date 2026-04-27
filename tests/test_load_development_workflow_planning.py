from types import SimpleNamespace

from src.modules import load_development_workflow as workflow_module


class _FakeDb:
    def __init__(self, valid_tables=None, query_results=None):
        self.valid_tables = valid_tables or {}
        self.query_results = query_results or {}
        self.calls = []

    def get_by_id(self, table, record_id):
        return self.valid_tables.get(table, {}).get(record_id)

    def execute_query(self, query, params=()):
        normalized = " ".join(query.split())
        self.calls.append((normalized, params))
        return self.query_results.get((normalized, params), [])


def test_build_workflow_test_plan_for_ocw():
    plan = workflow_module.build_workflow_test_plan(
        {
            "protocol": "ocw",
            "usage_profile": "precision",
            "start_charge": 42.3,
            "target_es": 10,
            "target_sd": 8,
            "target_group": 0.5,
        }
    )

    assert plan["protocol_name"] == "OCW (Optimal Charge Weight)"
    assert "42.3 gr" in plan["next_action"]
    assert any("0.3 gr" in step for step in [plan["increment"]])
    assert any("0.50 MOA" in item for item in plan["exit_criteria"])


def test_build_workflow_test_plan_for_hunting_emphasizes_cold_bore_and_impact():
    plan = workflow_module.build_workflow_test_plan(
        {
            "protocol": "ocw",
            "usage_profile": "hunting_medium",
            "start_charge": 43.0,
        }
    )

    assert plan["usage_name"] == "Hunting roe deer / deer"
    assert "cold-bore" in plan["usage_focus"].lower()
    assert any(
        "cold-bore" in item.lower() or "cold-bore" in item.lower()
        for item in plan["capture"]
    )
    assert any(
        "impact" in item.lower() or "kulevindu" in item.lower()
        for item in plan["exit_criteria"]
    )
    assert "hunting use" in plan["next_action"].lower()


def test_build_workflow_impact_window_warns_without_chrono_data():
    db = _FakeDb(
        valid_tables={
            "bullets": {
                2: {
                    "id": 2,
                    "manufacturer": "Hornady",
                    "name": "ELD-X",
                    "weight_grains": 143,
                    "bc_g1": 0.625,
                    "bullet_type": "bonded hunting",
                }
            }
        }
    )

    advisory = workflow_module.build_workflow_impact_window(
        db,
        {"usage_profile": "hunting_medium", "bullet_id": 2},
        {"chronograph_sessions": []},
    )

    assert advisory["level"] == "warning"
    assert "chronograph data" in advisory["message"].lower()
    assert (
        any(
            "data foundation" in item.lower() or "confidence" in item.lower()
            for item in advisory["checks"]
        )
        is False
    )


def test_build_workflow_impact_window_reports_margin_for_hunting_profile():
    db = _FakeDb(
        valid_tables={
            "bullets": {
                2: {
                    "id": 2,
                    "manufacturer": "Hornady",
                    "name": "ELD-X",
                    "weight_grains": 143,
                    "bc_g1": 0.625,
                    "bullet_type": "bonded hunting",
                }
            }
        }
    )

    advisory = workflow_module.build_workflow_impact_window(
        db,
        {"usage_profile": "hunting_medium", "bullet_id": 2},
        {
            "chronograph_sessions": [
                {"avg_velocity_fps": 2710.0},
                {"avg_velocity_fps": 2690.0},
                {"avg_velocity_fps": 2705.0},
                {"avg_velocity_fps": 2698.0},
                {"avg_velocity_fps": 2701.0},
            ]
        },
    )

    assert advisory["level"] in {"ok", "warning"}
    assert advisory["title"] == "Impact Window"
    assert "fps" in advisory["message"]
    assert "-" in advisory["message"]
    assert (
        "jaktavstand" in advisory["checks"][1].lower()
        or "bc" in advisory["checks"][1].lower()
    )
    assert any("uncertainty" in item.lower() for item in advisory["checks"])
    assert advisory["confidence_label"] in {"High confidence", "High Confidence"}
    assert (
        advisory["impact_velocity_low_fps"]
        < advisory["impact_velocity_fps"]
        < advisory["impact_velocity_high_fps"]
    )
    assert any("data foundation" in item.lower() for item in advisory["checks"])


def test_build_workflow_impact_window_uses_measured_environment_when_available():
    db = _FakeDb(
        valid_tables={
            "bullets": {
                2: {
                    "id": 2,
                    "manufacturer": "Hornady",
                    "name": "ELD-X",
                    "weight_grains": 143,
                    "bc_g7": 0.315,
                    "bullet_type": "bonded hunting",
                }
            }
        }
    )

    advisory = workflow_module.build_workflow_impact_window(
        db,
        {"usage_profile": "hunting_medium", "bullet_id": 2},
        {
            "chronograph_sessions": [{"avg_velocity_fps": 2700.0, "es_fps": 10.0}],
            "environmental_measurements": [
                {
                    "temperature_c": 24.0,
                    "pressure_hpa": 950.0,
                    "humidity_percent": 45.0,
                    "elevation_m": 1200.0,
                }
            ],
        },
    )

    assert advisory["density_ratio"] < 1.0
    assert any("measured environment" in item.lower() for item in advisory["checks"])
    assert advisory["density_altitude_m"] > 0


def test_build_workflow_impact_window_prefers_g7_when_available(monkeypatch):
    from src.utils.ballistics import estimate_retained_velocity_fps

    monkeypatch.setattr(workflow_module, "_preferred_drag_model", lambda: "AUTO")
    db = _FakeDb(
        valid_tables={
            "bullets": {
                2: {
                    "id": 2,
                    "manufacturer": "Hornady",
                    "name": "ELD-X",
                    "weight_grains": 143,
                    "bc_g1": 0.625,
                    "bc_g7": 0.315,
                    "bullet_type": "bonded hunting",
                }
            }
        }
    )

    advisory = workflow_module.build_workflow_impact_window(
        db,
        {"usage_profile": "hunting_medium", "bullet_id": 2},
        {"chronograph_sessions": [{"avg_velocity_fps": 2700.0}]},
    )

    assert advisory["drag_model"] == "G7"
    assert advisory["bc_used"] == 0.315
    assert "BC (G7)" in advisory["checks"][1]
    density_ratio = workflow_module._build_workflow_environment({}).density_ratio()
    assert advisory["impact_velocity_fps"] == estimate_retained_velocity_fps(
        2700.0,
        180.0,
        0.315,
        "G7",
        density_ratio=density_ratio,
    )


def test_build_workflow_impact_window_uses_segmented_bc_when_available(monkeypatch):
    monkeypatch.setattr(workflow_module, "_preferred_drag_model", lambda: "AUTO")
    db = _FakeDb(
        valid_tables={
            "bullets": {
                2: {
                    "id": 2,
                    "manufacturer": "Hornady",
                    "name": "ELD-X",
                    "weight_grains": 143,
                    "bc_g1": 0.625,
                    "bc_g7": 0.315,
                    "bc_segments_json": [
                        {
                            "velocity_fps_min": 2600,
                            "velocity_fps_max": 3000,
                            "bc_g7": 0.245,
                        },
                        {
                            "velocity_fps_min": 2000,
                            "velocity_fps_max": 2599,
                            "bc_g7": 0.228,
                        },
                    ],
                    "bullet_type": "bonded hunting",
                }
            }
        }
    )

    advisory = workflow_module.build_workflow_impact_window(
        db,
        {"usage_profile": "hunting_medium", "bullet_id": 2},
        {"chronograph_sessions": [{"avg_velocity_fps": 2710.0}]},
    )

    assert advisory["drag_model"] == "G7"
    assert advisory["bc_used"] == 0.245
    assert advisory["bc_segment_label"] == "G7 0.245 @ 2600-3000 fps"
    assert any("Segmented BC" in item for item in advisory["checks"])


def test_build_workflow_evidence_quality_includes_input_quality_checks(monkeypatch):
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_readiness_summary",
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence"
        },
    )
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_component_robustness",
        lambda db, workflow: {"score": 68},
    )
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_next_test_recommendation",
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence"
        },
    )
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_component_verification_advisory",
        lambda db, workflow: {"level": "warning"},
    )
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_impact_window",
        lambda db, workflow, observations: {"confidence_label": "High confidence"},
    )

    db = _FakeDb(
        valid_tables={
            "bullets": {
                2: {
                    "id": 2,
                    "bc_g7": 0.315,
                }
            }
        }
    )
    summary = workflow_module.build_workflow_evidence_quality(
        {
            "rifle_id": 1,
            "bullet_id": 2,
            "barrel_id": "A",
            "barrel_name": "24in",
            "powder_id": 3,
            "start_charge": 43.0,
            "created_date": "2026-03-20",
        },
        {
            "chronograph_sessions": [{"id": 1, "session_date": "2026-03-25"}],
            "best_group_mm": 12.0,
        },
        db,
    )

    assert any("Input quality:" in item for item in summary["checks"])
    assert any("Chrono:" in item for item in summary["checks"])
    assert any("Internal ballistics:" in item for item in summary["checks"])


def test_build_workflow_evidence_quality_flags_thin_primer_baseline(monkeypatch):
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_readiness_summary",
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence"
        },
    )
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_component_robustness",
        lambda db, workflow: {"score": 68},
    )
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_next_test_recommendation",
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence"
        },
    )
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_component_verification_advisory",
        lambda db, workflow: {"level": "neutral"},
    )
    monkeypatch.setattr(
        workflow_module,
        "build_workflow_impact_window",
        lambda db, workflow, observations: {"confidence_label": "High confidence"},
    )

    db = _FakeDb(valid_tables={"bullets": {2: {"id": 2, "bc_g7": 0.315}}})
    summary = workflow_module.build_workflow_evidence_quality(
        {
            "name": "OCW Test",
            "rifle_id": 1,
            "bullet_id": 2,
            "barrel_id": "A",
            "barrel_name": "24in",
            "powder_id": 3,
            "start_charge": 43.0,
            "created_date": "2026-03-20",
        },
        {
            "chronograph_sessions": [{"id": 1, "session_date": "2026-03-25"}],
            "best_group_mm": 12.0,
            "pressure_sign_rows": [
                {
                    "primer_image_path": "reports/primer-step-5.jpg",
                    "primer_image_observation": "light crater around the firing pin",
                    "date": "2026-03-25",
                }
            ],
        },
        db,
    )

    assert any(
        "Primer baseline: Single primer review only" == item
        for item in summary["checks"]
    )
    assert any(
        "Compare the next primer image against a conservative control load" in item
        for item in summary["checks"]
    )


def test_build_workflow_internal_ballistics_summary_uses_barrel_h2o_and_charge():
    class _InternalBallisticsDb(_FakeDb):
        def get_barrel_learning_profile(self, rifle_id, barrel_id, barrel_name):
            return {
                "avg_case_capacity_h2o": 52.4,
                "h2o_samples": 12,
            }

    db = _InternalBallisticsDb(
        valid_tables={
            "powder": {3: {"id": 3, "name": "H4350", "density": 0.91}},
            "rifles": {1: {"id": 1, "barrel_length_inches": 24.0}},
        }
    )

    summary = workflow_module.build_workflow_internal_ballistics_summary(
        db,
        {
            "rifle_id": 1,
            "barrel_id": "A",
            "barrel_name": "24in match",
            "powder_id": 3,
            "start_charge": 43.0,
        },
    )

    assert summary["title"] in {"Internal Ballistics", "Internballistikk"}
    assert any(metric["name"] == "Fyllrate" for metric in summary["metrics"])
    assert any(metric["name"] == "Krutttetthet" for metric in summary["metrics"])
    assert any("H2O basis" in check for check in summary["checks"])


def test_build_workflow_internal_ballistics_summary_prefers_case_context_and_reports_trim_length():
    class _InternalBallisticsCaseDb(_FakeDb):
        def refresh_case_learning_profile(self, case_id):
            assert case_id == 7
            return {
                "avg_case_capacity_h2o": 53.8,
                "h2o_samples": 1,
            }

        def get_barrel_learning_profile(self, rifle_id, barrel_id, barrel_name):
            raise AssertionError(
                "barrel profile should not be used when case context is available"
            )

    db = _InternalBallisticsCaseDb(
        valid_tables={
            "powder": {3: {"id": 3, "name": "H4350", "density": 0.91}},
            "rifles": {1: {"id": 1, "barrel_length_inches": 24.0}},
            "cases": {
                7: {
                    "id": 7,
                    "name": "Baseline Brass",
                    "manufacturer": "Reference",
                    "caliber": "6.5 Creedmoor",
                    "case_capacity_gr_h2o": 53.8,
                    "trim_length_mm": 48.77,
                }
            },
        }
    )

    summary = workflow_module.build_workflow_internal_ballistics_summary(
        db,
        {
            "rifle_id": 1,
            "barrel_id": "A",
            "barrel_name": "24in match",
            "powder_id": 3,
            "case_id": 7,
            "start_charge": 43.0,
        },
    )

    assert summary["title"] in {"Internal Ballistics", "Internballistikk"}
    assert any(metric["name"] == "Fyllrate" for metric in summary["metrics"])
    assert any("selected case" in check.lower() for check in summary["checks"])
    assert any("trim length 48.77 mm" in check.lower() for check in summary["checks"])


def test_build_workflow_calibration_summary_prefers_configuration_specific_barrel_learning():
    class _ConfigCalibrationDb(_FakeDb):
        def get_barrel_learning_profile(
            self,
            rifle_id,
            barrel_id,
            barrel_name,
            barrel_configuration_id=None,
            barrel_configuration_name=None,
        ):
            if barrel_configuration_id == "pipe-a:suppressed":
                return {
                    "confidence_score": 68.0,
                    "calibration_offset_fps": -12.0,
                    "temp_sensitivity_fps_per_c": 1.4,
                    "cold_bore_shift_moa": 0.18,
                }
            return {
                "confidence_score": 96.0,
                "calibration_offset_fps": -1.0,
                "temp_sensitivity_fps_per_c": 0.2,
                "cold_bore_shift_moa": 0.02,
            }

    summary = workflow_module.build_workflow_calibration_summary(
        _ConfigCalibrationDb(),
        {
            "rifle_id": 1,
            "barrel_id": "pipe-a",
            "barrel_name": "26in Match Pipe",
            "barrel_configuration_id": "pipe-a:suppressed",
            "barrel_configuration_name": "Suppressed",
            "usage_profile": "hunting_medium",
        },
    )

    assert any(
        metric["name"] == "Barrel Offset" and metric["value"] == "-12.0 fps"
        for metric in summary["metrics"]
    )
    assert any(
        metric["name"] == "Temperature Response" and metric["value"] == "+1.4 fps/°C"
        for metric in summary["metrics"]
    )


def test_format_workflow_evidence_basis_html_includes_internal_ballistics():
    class _InternalBallisticsDb(_FakeDb):
        def get_barrel_learning_profile(self, rifle_id, barrel_id, barrel_name):
            return {
                "avg_case_capacity_h2o": 52.4,
                "h2o_samples": 8,
            }

    db = _InternalBallisticsDb(
        valid_tables={
            "powder": {3: {"id": 3, "name": "H4350", "density": 0.91}},
            "rifles": {1: {"id": 1, "barrel_length_inches": 24.0}},
        }
    )

    html = workflow_module.format_workflow_evidence_basis_html(
        {"chronograph_sessions": [{"avg_velocity_fps": 2700.0}]},
        db,
        {
            "rifle_id": 1,
            "barrel_id": "A",
            "barrel_name": "24in",
            "powder_id": 3,
            "start_charge": 43.0,
        },
    )

    assert "Fyllrate" in html


def test_format_workflow_evidence_basis_html_includes_primer_review_counts():
    html = workflow_module.format_workflow_evidence_basis_html(
        {
            "pressure_notes": ["Flat primer observed"],
            "pressure_sign_rows": [
                {
                    "primer_image_path": "reports/primer-step-5.jpg",
                    "primer_image_observation": "light crater around the firing pin",
                },
                {
                    "notes": "ejector swipe seen on the second firing",
                },
            ],
        }
    )

    assert "Pressure-sign logs: 2" in html
    assert "Primer image reviews: 1/2" in html
    assert "supporting evidence, not standalone proof" in html


def test_format_workflow_evidence_basis_html_highlights_rifle_specific_primer_baseline():
    html = workflow_module.format_workflow_evidence_basis_html(
        {
            "pressure_notes": ["Flat primer observed"],
            "pressure_sign_rows": [
                {
                    "primer_image_path": "reports/primer-step-5.jpg",
                    "primer_image_observation": "light crater around the firing pin",
                    "date": "2026-03-25",
                }
            ],
        },
        workflow_data={"name": "OCW Test"},
    )

    assert (
        "one image is not enough to define this rifle's normal primer fingerprint"
        in html
    )
    assert (
        "Compare the next primer image against a conservative control load from the same rifle"
        in html
    )


def test_format_workflow_evidence_basis_html_includes_unified_record_counts():
    html = workflow_module.format_workflow_evidence_basis_html(
        {
            "evidence_records": [
                {"date": "2026-03-25", "has_cross_source_evidence": True},
                {"date": "2026-03-24", "has_cross_source_evidence": False},
            ]
        }
    )

    assert "Unified evidence records: 2" in html
    assert "Cross-linked evidence days: 1/2" in html


def test_format_workflow_evidence_basis_html_renders_evidence_timeline_cards():
    html = workflow_module.format_workflow_evidence_basis_html(
        {
            "evidence_records": [
                {
                    "date": "2026-03-25",
                    "sources": ["target", "chronograph", "pressure"],
                    "rounds_fired": 10,
                    "best_group_mm": 10.5,
                    "best_es_fps": 9.0,
                    "pressure_events": 1,
                    "primer_image_reviews": 1,
                    "notes": ["Tight node around 42.4 gr."],
                }
            ]
        }
    )

    assert "Evidence timeline:" in html
    assert "2026-03-25" in html
    assert "Sources:</b> target, chronograph, pressure" in html
    assert "Best group: 10.5 mm" in html
    assert "Primer image reviews: 1" in html
    assert "Tight node around 42.4 gr." in html


def test_validate_workflow_data_rejects_missing_components():
    widget = SimpleNamespace(db=_FakeDb(valid_tables={"rifles": {1: {"id": 1}}}))

    error = workflow_module.LoadDevelopmentWorkflow.validate_workflow_data(
        widget,
        {
            "name": "Test",
            "rifle_id": 1,
            "bullet_id": 2,
            "powder_id": 3,
            "primer_id": 4,
            "start_charge": 42.0,
        },
    )

    assert error == "Choose a valid bullet before creating the workflow."


def test_validate_workflow_data_accepts_valid_input():
    widget = SimpleNamespace(
        db=_FakeDb(
            valid_tables={
                "rifles": {1: {"id": 1}},
                "bullets": {2: {"id": 2}},
                "powder": {3: {"id": 3}},
                "primers": {4: {"id": 4}},
            }
        )
    )

    error = workflow_module.LoadDevelopmentWorkflow.validate_workflow_data(
        widget,
        {
            "name": "Test",
            "rifle_id": 1,
            "bullet_id": 2,
            "powder_id": 3,
            "primer_id": 4,
            "usage_profile": "precision",
            "start_charge": 42.0,
        },
    )

    assert error is None


def test_validate_workflow_data_rejects_missing_primer():
    widget = SimpleNamespace(
        db=_FakeDb(
            valid_tables={
                "rifles": {1: {"id": 1}},
                "bullets": {2: {"id": 2}},
                "powder": {3: {"id": 3}},
            }
        )
    )

    error = workflow_module.LoadDevelopmentWorkflow.validate_workflow_data(
        widget,
        {
            "name": "Test",
            "rifle_id": 1,
            "bullet_id": 2,
            "powder_id": 3,
            "primer_id": 4,
            "start_charge": 42.0,
        },
    )

    assert error == "Choose a valid primer before creating the workflow."


def test_validate_workflow_data_rejects_invalid_usage_profile():
    widget = SimpleNamespace(
        db=_FakeDb(
            valid_tables={
                "rifles": {1: {"id": 1}},
                "bullets": {2: {"id": 2}},
                "powder": {3: {"id": 3}},
                "primers": {4: {"id": 4}},
            }
        )
    )

    error = workflow_module.LoadDevelopmentWorkflow.validate_workflow_data(
        widget,
        {
            "name": "Test",
            "rifle_id": 1,
            "bullet_id": 2,
            "powder_id": 3,
            "primer_id": 4,
            "usage_profile": "space_magic",
            "start_charge": 42.0,
        },
    )

    assert error == "Choose a valid usage profile before creating the workflow."


def test_create_workflow_persists_usage_profile_and_component_ids():
    captured = {}

    class _InsertDb(_FakeDb):
        def insert(self, table, data):
            captured["table"] = table
            captured["data"] = data
            return 99

    original_information = workflow_module.QMessageBox.information
    workflow_module.QMessageBox.information = staticmethod(lambda *args, **kwargs: None)
    try:
        widget = SimpleNamespace(
            db=_InsertDb(),
            load_active_workflows=lambda: None,
        )
        workflow_module.LoadDevelopmentWorkflow.create_workflow(
            widget,
            {
                "name": "Hjorteladning",
                "rifle_id": 1,
                "barrel_id": "b1",
                "barrel_name": "Jaktpipe",
                "bullet_id": 2,
                "powder_id": 3,
                "primer_id": 4,
                "usage_profile": "hunting_medium",
                "caliber": "6.5 CM",
                "protocol": "ocw",
                "target_es": 10,
                "target_group": 0.8,
                "notes": "Cold bore focus",
            },
        )
    finally:
        workflow_module.QMessageBox.information = original_information

    assert captured["table"] == "load_development_workflows"
    assert captured["data"]["bullet_id"] == 2
    assert captured["data"]["powder_id"] == 3
    assert captured["data"]["primer_id"] == 4
    assert captured["data"]["usage_profile"] == "hunting_medium"


def test_format_workflow_action_message_for_batch():
    message = workflow_module.format_workflow_action_message(
        {
            "protocol": "ocw",
            "start_charge": 41.8,
            "target_es": 10,
            "target_sd": 8,
            "target_group": 0.5,
        },
        "batch",
    )

    assert "OCW" in message
    assert "41.8 gr" in message
    assert "0.3 gr" in message


def test_format_workflow_action_message_for_analysis():
    message = workflow_module.format_workflow_action_message(
        {
            "protocol": "bayesian",
            "target_es": 9,
            "target_sd": 7,
            "target_group": 0.4,
        },
        "analysis",
    )

    assert "ES" in message
    assert "0.40 MOA" in message


def test_build_workflow_pressure_advisory_flags_spike_risk_from_notes():
    advisory = workflow_module.build_workflow_pressure_advisory(
        {
            "protocol": "ocw",
            "notes": "Observerte pressurespiker og tydelige ejector marks i siste serie.",
        }
    )

    assert advisory["level"] == "critical"
    assert advisory["title"] == "Pressure spike risk"
    assert (
        "pressuretegn" in advisory["message"].lower()
        or "spike" in advisory["message"].lower()
    )


def test_build_workflow_pressure_advisory_warns_for_ladder_protocol():
    advisory = workflow_module.build_workflow_pressure_advisory(
        {
            "protocol": "ladder",
            "notes": "",
        }
    )

    assert advisory["level"] == "warning"
    assert advisory["title"] == "Pressure watch"
    assert (
        "velocity spikes" in advisory["message"]
        or "velocity-spikes" in advisory["message"]
    )


def test_format_pressure_advisory_html_includes_title_and_checks():
    html = workflow_module.format_pressure_advisory_html(
        {
            "protocol": "seating",
            "notes": "",
        }
    )

    assert "Seating-depth pressure watch" in html
    assert "Stop the series immediately" in html


def test_build_workflow_powder_lot_advisory_reports_retest_plan():
    powder_lot_query = " ".join(
        """
            SELECT id
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC
            LIMIT 1
        """.split()
    )

    class _LotDb(_FakeDb):
        def compare_powder_lots(self, component_id, current_lot_id):
            return {
                "severity": "high",
                "title": "Tydelig lotavvik",
                "message": "Sammenlignet med forrige lot OLD-LOT: Snittfart +26.0 fps",
                "verification_plan": {
                    "shots": 5,
                    "start_delta_grains": -0.2,
                    "focus": "Start 0.2 gr under forrige bekreftede ladning og chrono de første 5 skuddene før videre testing.",
                },
            }

    db = _LotDb(
        query_results={
            (powder_lot_query, (7,)): [{"id": 91}],
        }
    )

    advisory = workflow_module.build_workflow_powder_lot_advisory(
        db,
        {"powder_id": 7},
    )

    assert advisory["level"] == "critical"
    assert advisory["title"] == "Tydelig lotavvik"
    assert any("5 control shots" in item for item in advisory["checks"])
    assert any("-0.2 gr" in item for item in advisory["checks"])


def test_build_workflow_component_verification_advisory_combines_lot_signals():
    powder_lot_query = " ".join(
        """
            SELECT id
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC
            LIMIT 1
        """.split()
    )
    bullet_lot_query = " ".join(
        """
                SELECT id
                FROM bullet_lots
                WHERE bullet_id = ?
                ORDER BY is_active DESC, purchase_date DESC, created_date DESC, id DESC
                LIMIT 1
                """.split()
    )
    primer_lot_query = " ".join(
        """
                SELECT id
                FROM component_lots
                WHERE component_type = 'primers' AND component_id = ?
                ORDER BY is_active DESC, purchase_date DESC, created_date DESC
                LIMIT 1
                """.split()
    )

    class _VerificationDb(_FakeDb):
        def compare_powder_lots(self, component_id, current_lot_id):
            return {
                "severity": "watch",
                "title": "Merkbart lotavvik",
                "message": "Sammenlignet med forrige lot: Snittfart +14.0 fps",
                "current_profile": {"confidence_label": "middels"},
                "verification_plan": {
                    "shots": 3,
                    "start_delta_grains": -0.1,
                    "focus": "Start 0.1 gr under forrige ladning og chrono 3 control shots.",
                },
            }

        def compare_bullet_lots(self, bullet_id, current_lot_id):
            return {
                "severity": "watch",
                "title": "Merkbart kulelotavvik",
                "message": "Sammenlignet med forrige lot: Typisk gruppe +0.120 MOA",
                "current_profile": {"confidence_label": "høy"},
                "verification_plan": {
                    "focus": "Skyt 3 control shots og se etter gruppedrift eller urolig seating-respons."
                },
            }

        def compare_primer_lots(self, component_id, current_lot_id):
            return {
                "severity": "high",
                "title": "Tydelig primerlotavvik",
                "message": "Sammenlignet med forrige lot: ES +9.5",
                "current_profile": {"confidence_label": "lav"},
                "verification_plan": {
                    "focus": "Chrono minst 5 control shots og følg spesielt med på ES/SD og tidlige pressuretegn."
                },
            }

    db = _VerificationDb(
        query_results={
            (powder_lot_query, (7,)): [{"id": 91}],
            (bullet_lot_query, (11,)): [{"id": 42}],
            (primer_lot_query, (4,)): [{"id": 77}],
        }
    )

    advisory = workflow_module.build_workflow_component_verification_advisory(
        db,
        {"powder_id": 7, "bullet_id": 11, "primer_id": 4},
    )

    assert advisory["level"] == "critical"
    assert advisory["title"] == "Combined Lot Verification"
    assert "Powder Lot" in advisory["message"]
    assert "Bullet Lot" in advisory["message"]
    assert "Primer Lot" in advisory["message"]
    assert "Data foundation" in advisory["message"]
    assert "Uncertainty" in advisory["message"]
    assert any("Chrono minst 5 control shots" in item for item in advisory["checks"])
    assert "middels" in advisory["message"].lower()


def test_build_workflow_next_test_recommendation_prioritizes_pressure_stop():
    recommendation = workflow_module.build_workflow_next_test_recommendation(
        {"protocol": "ocw", "notes": ""},
        {
            "pressure_notes": ["Flat primer og ejector mark"],
            "chronograph_sessions": [{"id": 1}],
            "best_es_fps": 8.0,
            "best_sd_fps": 4.0,
            "best_group_mm": 11.0,
        },
        None,
    )

    assert "pressure" in recommendation["title"].lower()
    assert "control shots" in recommendation["action"].lower()


def test_build_workflow_next_test_recommendation_prioritizes_lot_verification():
    class _Db:
        pass

    original_verification = (
        workflow_module.build_workflow_component_verification_advisory
    )
    original_readiness = workflow_module.build_workflow_readiness_summary
    workflow_module.build_workflow_component_verification_advisory = (
        lambda db, workflow: {
            "level": "critical",
            "checks": ["Powder Lot: Kjør 5 control shots med start -0.2 gr."],
        }
    )
    workflow_module.build_workflow_readiness_summary = lambda workflow, observations, db=None: {
        "level": "more_data",
        "title": "Trenger flere data",
        "message": "Kontroller videre.",
        "confidence_label": "Medium Confidence",
        "confidence_message": "Lotsignalet er tydelig, men resten av data foundationet er fortsatt under oppbygging.",
    }
    try:
        recommendation = workflow_module.build_workflow_next_test_recommendation(
            {"protocol": "ocw"},
            {
                "pressure_notes": [],
                "chronograph_sessions": [{"id": 1}],
                "best_group_mm": 12.0,
            },
            _Db(),
        )
    finally:
        workflow_module.build_workflow_component_verification_advisory = (
            original_verification
        )
        workflow_module.build_workflow_readiness_summary = original_readiness

    assert "lot verification" in recommendation["title"].lower()
    assert "control shots" in recommendation["action"].lower()
    assert recommendation["confidence_label"] == "Medium Confidence"


def test_build_workflow_next_test_recommendation_marks_verification_series_when_ready():
    class _Db:
        pass

    original_verification = (
        workflow_module.build_workflow_component_verification_advisory
    )
    original_readiness = workflow_module.build_workflow_readiness_summary
    workflow_module.build_workflow_component_verification_advisory = (
        lambda db, workflow: {"level": "ok", "checks": []}
    )
    workflow_module.build_workflow_readiness_summary = lambda workflow, observations, db=None: {
        "level": "ready",
        "title": "Klar for next step",
        "message": "Ser bra ut.",
        "confidence_label": "High Confidence",
        "confidence_message": "Chronograph, group, and robustness point in the same direction.",
    }
    try:
        recommendation = workflow_module.build_workflow_next_test_recommendation(
            {"protocol": "ocw"},
            {
                "pressure_notes": [],
                "chronograph_sessions": [{"id": 1}],
                "best_group_mm": 10.0,
            },
            _Db(),
        )
    finally:
        workflow_module.build_workflow_component_verification_advisory = (
            original_verification
        )
        workflow_module.build_workflow_readiness_summary = original_readiness

    assert "verification series" in recommendation["title"].lower()
    assert "node" in recommendation["action"].lower()
    assert recommendation["confidence_label"] == "High Confidence"


def test_build_workflow_next_test_recommendation_prefers_hunting_verification_when_ready():
    class _Db:
        pass

    original_verification = (
        workflow_module.build_workflow_component_verification_advisory
    )
    original_readiness = workflow_module.build_workflow_readiness_summary
    workflow_module.build_workflow_component_verification_advisory = (
        lambda db, workflow: {"level": "ok", "checks": []}
    )
    workflow_module.build_workflow_readiness_summary = (
        lambda workflow, observations, db=None: {
            "level": "ready",
            "title": "Klar for next step",
            "message": "Ser bra ut.",
            "confidence_label": "High Confidence",
            "confidence_message": "Both hunting data and robustness look usable.",
        }
    )
    try:
        recommendation = workflow_module.build_workflow_next_test_recommendation(
            {"protocol": "ocw", "usage_profile": "hunting_medium"},
            {
                "pressure_notes": [],
                "chronograph_sessions": [{"id": 1}],
                "best_group_mm": 10.0,
            },
            _Db(),
        )
    finally:
        workflow_module.build_workflow_component_verification_advisory = (
            original_verification
        )
        workflow_module.build_workflow_readiness_summary = original_readiness

    assert "cold-bore and hunting verification" in recommendation["title"].lower()
    assert "cold-bore" in recommendation["action"].lower()


def test_build_workflow_next_test_recommendation_prefers_training_robustness_when_ready():
    class _Db:
        pass

    original_verification = (
        workflow_module.build_workflow_component_verification_advisory
    )
    original_readiness = workflow_module.build_workflow_readiness_summary
    workflow_module.build_workflow_component_verification_advisory = (
        lambda db, workflow: {"level": "ok", "checks": []}
    )
    workflow_module.build_workflow_readiness_summary = lambda workflow, observations, db=None: {
        "level": "ready",
        "title": "Klar for next step",
        "message": "Ser bra ut.",
        "confidence_label": "Medium Confidence",
        "confidence_message": "Ladningen ser brukbar ut, men bor bekreftes med en enkel control series.",
    }
    try:
        recommendation = workflow_module.build_workflow_next_test_recommendation(
            {"protocol": "ocw", "usage_profile": "training"},
            {
                "pressure_notes": [],
                "chronograph_sessions": [{"id": 1}],
                "best_group_mm": 10.0,
            },
            _Db(),
        )
    finally:
        workflow_module.build_workflow_component_verification_advisory = (
            original_verification
        )
        workflow_module.build_workflow_readiness_summary = original_readiness

    assert "robust control series" in recommendation["title"].lower()
    assert (
        "repeat" in recommendation["action"].lower()
        or "stable" in recommendation["action"].lower()
    )
    assert recommendation["confidence_label"] == "Medium Confidence"


def test_format_workflow_next_test_html_includes_confidence():
    html = workflow_module.format_workflow_next_test_html(
        {
            "title": "Best next test: verification series",
            "action": "Skyt 3 control shots.",
            "reason": "The data foundation points toward node verification.",
            "checks": ["Chrono alle skudd."],
            "confidence_label": "High Confidence",
            "confidence_message": "The recommendation is based on both solid measured data and usable robustness.",
        }
    )

    assert "High Confidence" in html
    assert "usable robustness" in html


def test_build_workflow_component_robustness_summarizes_learning_sources():
    powder_lot_query = " ".join(
        """
            SELECT id
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC
            LIMIT 1
        """.split()
    )
    bullet_lot_query = " ".join(
        """
                SELECT id
                FROM bullet_lots
                WHERE bullet_id = ?
                ORDER BY is_active DESC, purchase_date DESC, created_date DESC, id DESC
                LIMIT 1
                """.split()
    )
    primer_lot_query = " ".join(
        """
                SELECT id
                FROM component_lots
                WHERE component_type = 'primers' AND component_id = ?
                ORDER BY is_active DESC, purchase_date DESC, created_date DESC
                LIMIT 1
                """.split()
    )

    class _LearningDb(_FakeDb):
        def get_barrel_learning_profile(self, rifle_id, barrel_id, barrel_name=None):
            return {
                "confidence_score": 78.0,
                "confidence_label": "høy trygghet",
                "status": "learning",
                "data_points": 5,
                "drift_flag": None,
            }

        def compare_powder_lots(self, component_id, current_lot_id):
            return {
                "severity": "watch",
                "title": "Merkbart lotavvik",
                "message": "Sammenlignet med forrige lot: Snittfart +14.0 fps",
                "verification_plan": {
                    "shots": 3,
                    "start_delta_grains": -0.1,
                    "focus": "Start 0.1 gr under forrige ladning og chrono 3 control shots.",
                },
                "current_profile": {
                    "confidence_score": 66.0,
                    "confidence_label": "brukbar trygghet",
                    "batch_samples": 2,
                    "chrono_samples": 4,
                },
            }

        def compare_bullet_lots(self, bullet_id, current_lot_id):
            return {
                "severity": "ok",
                "status": "stable",
                "verification_plan": {
                    "shots": 3,
                    "focus": "Skyt én kort control series og bekreft at gruppen matcher forventningene.",
                },
                "current_profile": {
                    "confidence_score": 71.0,
                    "confidence_label": "brukbar trygghet",
                    "qc_samples": 8,
                    "batch_samples": 2,
                },
            }

        def compare_primer_lots(self, component_id, current_lot_id):
            return {
                "severity": "watch",
                "status": "watch",
                "verification_plan": {
                    "shots": 3,
                    "focus": "Chrono 3 control shots og se etter økt ES/SD eller treg/ujevn ignition.",
                },
                "current_profile": {
                    "confidence_score": 62.0,
                    "confidence_label": "brukbar trygghet",
                    "batch_samples": 2,
                    "typical_es_fps": 17.0,
                    "profile_data": {"typical_sd_fps": 7.0},
                },
            }

    db = _LearningDb(
        query_results={
            (powder_lot_query, (7,)): [{"id": 91}],
            (bullet_lot_query, (11,)): [{"id": 42}],
            (primer_lot_query, (4,)): [{"id": 77}],
        }
    )

    summary = workflow_module.build_workflow_component_robustness(
        db,
        {
            "rifle_id": 3,
            "barrel_id": "B1",
            "barrel_name": '26" Match',
            "powder_id": 7,
            "bullet_id": 11,
            "primer_id": 4,
        },
    )

    assert summary["level"] == "warning"
    assert summary["score"] > 0
    assert summary["uncertainty_message"]
    assert any(
        "barrel" in component["name"].lower() for component in summary["components"]
    )
    assert any(component["name"] == "Powder Lot" for component in summary["components"])
    assert any(component["name"] == "Primer Lot" for component in summary["components"])
    assert any(
        "control shots" in item and "-0.1 gr" in item for item in summary["checks"]
    )


def test_build_workflow_calibration_summary_combines_barrel_and_lot_learning():
    powder_lot_query = " ".join(
        """
            SELECT id
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC
            LIMIT 1
        """.split()
    )
    primer_lot_query = " ".join(
        """
                SELECT id
                FROM component_lots
                WHERE component_type = 'primers' AND component_id = ?
                ORDER BY is_active DESC, purchase_date DESC, created_date DESC
                LIMIT 1
                """.split()
    )

    class _CalibrationDb(_FakeDb):
        def get_barrel_learning_profile(self, rifle_id, barrel_id, barrel_name=None):
            return {
                "confidence_score": 78.0,
                "calibration_offset_fps": -14.0,
                "temp_sensitivity_fps_per_c": 1.8,
                "cold_bore_shift_moa": 0.24,
            }

        def compare_powder_lots(self, component_id, current_lot_id):
            return {
                "current_profile": {
                    "confidence_score": 72.0,
                    "velocity_offset_fps": 9.0,
                    "temp_sensitivity_fps_per_c": 1.2,
                }
            }

        def compare_primer_lots(self, component_id, current_lot_id):
            return {
                "current_profile": {
                    "confidence_score": 61.0,
                    "typical_es_fps": 11.0,
                }
            }

        def execute_query(self, query, params=()):
            normalized = " ".join(query.split())
            if "FROM engine_calibrations" in normalized:
                return [{"sample_count": 6, "mse": 4.2, "accepted": 1}]
            return super().execute_query(query, params)

    summary = workflow_module.build_workflow_calibration_summary(
        _CalibrationDb(
            query_results={
                (powder_lot_query, (2,)): [{"id": 10}],
                (primer_lot_query, (3,)): [{"id": 11}],
            }
        ),
        {
            "rifle_id": 1,
            "barrel_id": "pipe-a",
            "barrel_name": "Pipe A",
            "powder_id": 2,
            "primer_id": 3,
            "ammo_profile_id": 4,
            "usage_profile": "hunting_medium",
        },
    )

    assert summary["level"] in {"ok", "warning"}
    assert summary["score"] > 50
    assert any(metric["name"] == "Barrel Offset" for metric in summary["metrics"])
    assert any(
        metric["name"] == "Temperature Response" for metric in summary["metrics"]
    )
    assert any(metric["name"] == "Powder Lot Offset" for metric in summary["metrics"])
    assert any(metric["name"] == "Engine Calibration" for metric in summary["metrics"])


def test_format_component_robustness_html_includes_score_and_components():
    powder_lot_query = " ".join(
        """
            SELECT id
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC
            LIMIT 1
        """.split()
    )

    class _MinimalDb(_FakeDb):
        def get_barrel_learning_profile(self, rifle_id, barrel_id, barrel_name=None):
            return {
                "confidence_score": 85.0,
                "confidence_label": "høy trygghet",
                "status": "learning",
                "data_points": 6,
                "drift_flag": None,
            }

        def compare_powder_lots(self, component_id, current_lot_id):
            return {
                "severity": "ok",
                "title": "Lotene ser like ut",
                "message": "Kort verification series er nok.",
                "verification_plan": {
                    "shots": 3,
                    "start_delta_grains": 0.0,
                    "focus": "Bekreft at hastighet og ES matcher.",
                },
                "current_profile": {
                    "confidence_score": 82.0,
                    "confidence_label": "høy trygghet",
                    "batch_samples": 3,
                    "chrono_samples": 4,
                },
            }

        def compare_bullet_lots(self, bullet_id, current_lot_id):
            return {
                "severity": "ok",
                "status": "stable",
                "verification_plan": {"shots": 3, "focus": "Bekreft gruppen."},
                "current_profile": {
                    "confidence_score": 80.0,
                    "confidence_label": "høy trygghet",
                    "qc_samples": 10,
                    "batch_samples": 2,
                },
            }

    db = _MinimalDb(
        query_results={
            (powder_lot_query, (7,)): [{"id": 91}],
        }
    )

    html = workflow_module.format_component_robustness_html(
        db,
        {
            "rifle_id": 3,
            "barrel_id": "B1",
            "powder_id": 7,
        },
    )

    assert "Robustness" in html
    assert "/100" in html
    assert "Barrel" in html
    assert "Powder Lot" in html
    assert "Uncertainty:" in html


def test_collect_workflow_observations_reads_shooting_and_chrono_data():
    explicit_batch_query = " ".join(
        """
            SELECT bps.session_date AS date,
                   bps.id AS batch_session_id,
                   bps.batch_id,
                   bps.session_name,
                   bps.session_type,
                   bps.shot_count AS rounds_fired,
                   bps.group_size_mm AS best_group_mm,
                   bps.group_size_mm AS avg_group_mm,
                   bps.notes,
                   bps.analysis_json,
                   bp.rifle_id
            FROM batch_project_sessions bps
            JOIN batch_projects bp ON bp.id = bps.batch_id
            WHERE bp.source_workflow = ?
            ORDER BY bps.session_date DESC, bps.id DESC
            LIMIT 10
        """.split()
    )
    shooting_query = " ".join(
        """
            SELECT date, rounds_fired, best_group_mm, avg_group_mm, notes
            FROM shooting_sessions
            WHERE rifle_id = ?
              AND (? = '' OR date >= ?)
            ORDER BY date DESC
            LIMIT 10
        """.split()
    )
    chrono_query = " ".join(
        """
            SELECT session_date, shot_count, avg_velocity_fps, es_fps, sd_fps, notes, session_name
            FROM chronograph_sessions
            WHERE import_meta_json LIKE ?
              AND (? = '' OR session_date >= ?)
            ORDER BY session_date DESC
            LIMIT 10
        """.split()
    )
    fallback_chrono_query = " ".join(
        """
            SELECT session_date, shot_count, avg_velocity_fps, es_fps, sd_fps, notes, session_name
            FROM chronograph_sessions
            WHERE (session_name LIKE ? OR notes LIKE ?)
              AND (? = '' OR session_date >= ?)
            ORDER BY session_date DESC
            LIMIT 10
        """.split()
    )
    environmental_query = " ".join(
        """
        SELECT datetime, location_name, elevation_m, temperature_c, pressure_hpa,
               humidity_percent, wind_speed_ms, wind_direction_deg, density_altitude_ft
        FROM environmental_data
        WHERE (? = '' OR datetime >= ?)
        ORDER BY datetime DESC
        LIMIT 5
        """.split()
    )
    db = _FakeDb(
        query_results={
            (explicit_batch_query, ("workflow:12",)): [
                {
                    "date": "2026-03-25",
                    "batch_session_id": 71,
                    "batch_id": 19,
                    "session_name": "Batch A",
                    "session_type": "chronograph",
                    "rounds_fired": 5,
                    "best_group_mm": 10.5,
                    "avg_group_mm": 10.5,
                    "notes": "Flat primer på siste skudd",
                    "analysis_json": "{}",
                    "rifle_id": 4,
                }
            ],
            (shooting_query, (4, "2026-03-20", "2026-03-20")): [
                {
                    "date": "2026-03-24",
                    "rounds_fired": 15,
                    "best_group_mm": 12.4,
                    "avg_group_mm": 18.1,
                    "notes": "Litt ejector mark på siste steg",
                }
            ],
            (chrono_query, ('%"workflow_id": 12%', "2026-03-20", "2026-03-20")): [
                {
                    "session_date": "2026-03-25",
                    "shot_count": 5,
                    "avg_velocity_fps": 2820.0,
                    "es_fps": 9.0,
                    "sd_fps": 3.0,
                    "notes": "Direkte workflow-koblet",
                    "session_name": "OCW Test workflow-linked",
                }
            ],
            (
                fallback_chrono_query,
                ("%OCW Test%", "%OCW Test%", "2026-03-20", "2026-03-20"),
            ): [
                {
                    "session_date": "2026-03-24",
                    "shot_count": 5,
                    "avg_velocity_fps": 2810.0,
                    "es_fps": 11.0,
                    "sd_fps": 4.0,
                    "notes": "Rolig serie",
                    "session_name": "OCW Test runde 1",
                }
            ],
            (environmental_query, ("2026-03-20", "2026-03-20")): [
                {
                    "datetime": "2026-03-25 10:00:00",
                    "location_name": "Rena",
                    "elevation_m": 300.0,
                    "temperature_c": 7.0,
                    "pressure_hpa": 1002.0,
                    "humidity_percent": 65,
                    "wind_speed_ms": 2.0,
                    "wind_direction_deg": 220,
                    "density_altitude_ft": 950.0,
                }
            ],
        }
    )

    observations = workflow_module.collect_workflow_observations(
        db,
        {
            "id": 12,
            "name": "OCW Test",
            "rifle_id": 4,
            "created_date": "2026-03-20",
        },
    )

    assert observations["best_group_mm"] == 10.5
    assert observations["best_es_fps"] == 9.0
    assert observations["best_sd_fps"] == 3.0
    assert len(observations["pressure_notes"]) == 4
    assert len(observations["environmental_measurements"]) == 1


def test_collect_workflow_observations_prefers_direct_load_session_match_for_shooting_sessions():
    direct_shooting_query = " ".join(
        """
            SELECT date, rounds_fired, best_group_mm, avg_group_mm, notes
            FROM shooting_sessions
            WHERE load_session_id = ?
            ORDER BY date DESC, id DESC
            LIMIT 10
        """.split()
    )
    db = _FakeDb(
        query_results={
            (direct_shooting_query, (33,)): [
                {
                    "date": "2026-03-28",
                    "rounds_fired": 8,
                    "best_group_mm": 9.8,
                    "avg_group_mm": 12.0,
                    "notes": "Direct session-linked target result",
                }
            ],
        }
    )

    observations = workflow_module.collect_workflow_observations(
        db,
        {
            "id": 12,
            "name": "OCW Test",
            "rifle_id": 4,
            "created_date": "2026-03-20",
            "load_session_id": 33,
        },
    )

    assert (
        observations["shooting_sessions"][0]["notes"]
        == "Direct session-linked target result"
    )
    assert observations["best_group_mm"] == 9.8


def test_collect_workflow_observations_skips_broad_fallbacks_for_named_setup():
    direct_shooting_query = " ".join(
        """
            SELECT date, rounds_fired, best_group_mm, avg_group_mm, notes
            FROM shooting_sessions
            WHERE load_session_id = ?
            ORDER BY date DESC, id DESC
            LIMIT 10
        """.split()
    )
    chrono_query = " ".join(
        """
            SELECT session_date, shot_count, avg_velocity_fps, es_fps, sd_fps, notes, session_name
            FROM chronograph_sessions
            WHERE import_meta_json LIKE ?
              AND (? = '' OR session_date >= ?)
            ORDER BY session_date DESC
            LIMIT 10
        """.split()
    )
    direct_pressure_query = " ".join(
        """
            SELECT notes, primer_image_path, primer_image_quality,
                                                 primer_image_observation, primer_image_confidence, date,
                                                 workflow_id, load_session_id, session_name,
                                                 batch_id, batch_session_id, rifle_id, barrel_id, barrel_name
            FROM pressure_signs
            WHERE ammo_profile_id = ?
              AND load_session_id = ?
              AND (? = '' OR date >= ?)
            ORDER BY date DESC, id DESC
            LIMIT 10
        """.split()
    )
    broad_shooting_query = " ".join(
        """
            SELECT date, rounds_fired, best_group_mm, avg_group_mm, notes
            FROM shooting_sessions
            WHERE rifle_id = ?
              AND (? = '' OR date >= ?)
            ORDER BY date DESC
            LIMIT 10
        """.split()
    )
    broad_chrono_query = " ".join(
        """
            SELECT session_date, shot_count, avg_velocity_fps, es_fps, sd_fps, notes, session_name
            FROM chronograph_sessions
            WHERE (session_name LIKE ? OR notes LIKE ?)
              AND (? = '' OR session_date >= ?)
            ORDER BY session_date DESC
            LIMIT 10
        """.split()
    )
    broad_pressure_query = " ".join(
        """
            SELECT notes, primer_image_path, primer_image_quality,
                                                 primer_image_observation, primer_image_confidence, date,
                                                 workflow_id, load_session_id, session_name,
                                                 batch_id, batch_session_id, rifle_id, barrel_id, barrel_name
            FROM pressure_signs
            WHERE ammo_profile_id = ?
                            AND (? IS NULL OR rifle_id IS NULL OR rifle_id = ?)
                            AND (? = '' OR barrel_id IS NULL OR barrel_id = ?)
              AND (? = '' OR date >= ?)
            ORDER BY date DESC, id DESC
            LIMIT 10
        """.split()
    )
    db = _FakeDb(
        query_results={
            (direct_shooting_query, (33,)): [],
            (chrono_query, ('%"workflow_id": 12%', "2026-03-20", "2026-03-20")): [],
            (direct_pressure_query, (19, 33, "2026-03-20", "2026-03-20")): [
                {
                    "notes": "Direct pressure note for this setup.",
                    "primer_image_path": "",
                    "primer_image_quality": "",
                    "primer_image_observation": "",
                    "primer_image_confidence": "",
                    "date": "2026-03-25",
                    "workflow_id": 12,
                    "load_session_id": 33,
                    "session_name": "Setup A",
                    "batch_id": None,
                    "batch_session_id": None,
                    "rifle_id": 4,
                    "barrel_id": "B1",
                    "barrel_name": "26in Match",
                }
            ],
        }
    )

    observations = workflow_module.collect_workflow_observations(
        db,
        {
            "id": 12,
            "name": "OCW Test",
            "rifle_id": 4,
            "ammo_profile_id": 19,
            "load_session_id": 33,
            "barrel_id": "B1",
            "barrel_configuration_id": "cfg-suppressed",
            "barrel_configuration_name": "Suppressed",
            "created_date": "2026-03-20",
        },
    )

    assert observations["pressure_notes"] == ["Direct pressure note for this setup."]
    assert (broad_shooting_query, (4, "2026-03-20", "2026-03-20")) not in db.calls
    assert (
        broad_chrono_query,
        ("%OCW Test%", "%OCW Test%", "2026-03-20", "2026-03-20"),
    ) not in db.calls
    assert (
        broad_pressure_query,
        (19, 4, 4, "B1", "B1", "2026-03-20", "2026-03-20"),
    ) not in db.calls


def test_collect_workflow_observations_includes_primer_image_pressure_note():
    pressure_sign_query = " ".join(
        """
            SELECT notes, primer_image_path, primer_image_quality,
                                     primer_image_observation, primer_image_confidence, date,
                                     workflow_id, load_session_id, session_name,
                                                                         batch_id, batch_session_id, rifle_id, barrel_id, barrel_name
            FROM pressure_signs
            WHERE ammo_profile_id = ?
              AND (? IS NULL OR rifle_id IS NULL OR rifle_id = ?)
                            AND (? = '' OR barrel_id IS NULL OR barrel_id = ?)
              AND (? = '' OR date >= ?)
            ORDER BY date DESC, id DESC
            LIMIT 10
        """.split()
    )
    db = _FakeDb(
        query_results={
            (pressure_sign_query, (19, 4, 4, "", "", "2026-03-20", "2026-03-20")): [
                {
                    "notes": "Flat primer on the hottest step.",
                    "primer_image_path": "reports/primer-step-5.jpg",
                    "primer_image_quality": "good",
                    "primer_image_observation": "light crater around the firing pin",
                    "primer_image_confidence": "medium",
                    "date": "2026-03-25",
                    "workflow_id": None,
                    "load_session_id": None,
                    "session_name": None,
                    "batch_id": 19,
                    "batch_session_id": 71,
                    "rifle_id": 4,
                    "barrel_id": None,
                    "barrel_name": None,
                }
            ],
        }
    )

    observations = workflow_module.collect_workflow_observations(
        db,
        {
            "id": 12,
            "name": "OCW Test",
            "rifle_id": 4,
            "ammo_profile_id": 19,
            "created_date": "2026-03-20",
        },
    )

    assert "Flat primer on the hottest step." in observations["pressure_notes"]
    assert any(
        "Primer image review - light crater around the firing pin - confidence medium - image quality good"
        == item
        for item in observations["pressure_notes"]
    )
    assert (
        observations["pressure_sign_rows"][0]["primer_image_path"]
        == "reports/primer-step-5.jpg"
    )


def test_collect_workflow_observations_builds_unified_evidence_records():
    shooting_query = " ".join(
        """
            SELECT date, rounds_fired, best_group_mm, avg_group_mm, notes
            FROM shooting_sessions
            WHERE rifle_id = ?
              AND (? = '' OR date >= ?)
            ORDER BY date DESC
            LIMIT 10
        """.split()
    )
    chrono_query = " ".join(
        """
            SELECT session_date, shot_count, avg_velocity_fps, es_fps, sd_fps, notes, session_name
            FROM chronograph_sessions
            WHERE (session_name LIKE ? OR notes LIKE ?)
              AND (? = '' OR session_date >= ?)
            ORDER BY session_date DESC
            LIMIT 10
        """.split()
    )
    pressure_sign_query = " ".join(
        """
            SELECT notes, primer_image_path, primer_image_quality,
                                     primer_image_observation, primer_image_confidence, date,
                                                                         workflow_id, load_session_id, session_name,
                                                                         batch_id, batch_session_id, rifle_id, barrel_id, barrel_name
            FROM pressure_signs
            WHERE ammo_profile_id = ?
                            AND (? IS NULL OR rifle_id IS NULL OR rifle_id = ?)
                            AND (? = '' OR barrel_id IS NULL OR barrel_id = ?)
              AND (? = '' OR date >= ?)
            ORDER BY date DESC, id DESC
            LIMIT 10
        """.split()
    )
    environmental_query = " ".join(
        """
        SELECT datetime, location_name, elevation_m, temperature_c, pressure_hpa,
               humidity_percent, wind_speed_ms, wind_direction_deg, density_altitude_ft
        FROM environmental_data
        WHERE (? = '' OR datetime >= ?)
        ORDER BY datetime DESC
        LIMIT 5
        """.split()
    )
    db = _FakeDb(
        query_results={
            (shooting_query, (4, "2026-03-20", "2026-03-20")): [
                {
                    "date": "2026-03-25",
                    "rounds_fired": 5,
                    "best_group_mm": 10.5,
                    "avg_group_mm": 12.2,
                    "notes": "Tight node around 42.4 gr.",
                }
            ],
            (chrono_query, ("%OCW Test%", "%OCW Test%", "2026-03-20", "2026-03-20")): [
                {
                    "session_date": "2026-03-25",
                    "shot_count": 5,
                    "avg_velocity_fps": 2712.0,
                    "es_fps": 9.0,
                    "sd_fps": 3.0,
                    "notes": "Stable chrono string.",
                    "session_name": "OCW Test round 1",
                }
            ],
            (pressure_sign_query, (19, 4, 4, "", "", "2026-03-20", "2026-03-20")): [
                {
                    "notes": "Flat primer on the hottest step.",
                    "primer_image_path": "reports/primer-step-5.jpg",
                    "primer_image_quality": "good",
                    "primer_image_observation": "light crater around the firing pin",
                    "primer_image_confidence": "medium",
                    "date": "2026-03-25",
                    "workflow_id": None,
                    "load_session_id": None,
                    "session_name": None,
                    "batch_id": 19,
                    "batch_session_id": 71,
                    "rifle_id": 4,
                    "barrel_id": None,
                    "barrel_name": None,
                }
            ],
            (environmental_query, ("2026-03-20", "2026-03-20")): [
                {
                    "datetime": "2026-03-25 10:00:00",
                    "location_name": "Rena",
                    "temperature_c": 7.0,
                    "pressure_hpa": 1002.0,
                    "humidity_percent": 65,
                    "wind_speed_ms": 2.0,
                    "wind_direction_deg": 220,
                    "density_altitude_ft": 950.0,
                }
            ],
        }
    )

    observations = workflow_module.collect_workflow_observations(
        db,
        {
            "id": 12,
            "name": "OCW Test",
            "rifle_id": 4,
            "ammo_profile_id": 19,
            "created_date": "2026-03-20",
        },
    )

    assert len(observations["evidence_records"]) == 2
    source_sets = [
        set(record["sources"]) for record in observations["evidence_records"]
    ]
    assert {"chronograph"} in source_sets
    assert {"target", "pressure", "environment"} in source_sets

    target_record = next(
        record
        for record in observations["evidence_records"]
        if set(record["sources"]) == {"target", "pressure", "environment"}
    )
    chrono_record = next(
        record
        for record in observations["evidence_records"]
        if set(record["sources"]) == {"chronograph"}
    )

    assert target_record["date"] == "2026-03-25"
    assert target_record["has_cross_source_evidence"] is True
    assert target_record["primer_image_reviews"] == 1
    assert target_record["environment_samples"] == 1
    assert target_record["location_name"] == "Rena"
    assert target_record["temperature_c"] == 7.0
    assert target_record["pressure_hpa"] == 1002.0
    assert target_record["density_altitude_ft"] == 950.0
    assert target_record["best_group_mm"] == 10.5
    assert "Tight node around 42.4 gr." in target_record["notes"]

    assert chrono_record["date"] == "2026-03-25"
    assert chrono_record["best_es_fps"] == 9.0
    assert chrono_record["best_sd_fps"] == 3.0
    assert chrono_record["max_avg_velocity_fps"] == 2712.0


def test_collect_workflow_observations_separates_same_day_records_with_different_session_names():
    explicit_batch_query = " ".join(
        """
            SELECT bps.session_date AS date,
                   bps.id AS batch_session_id,
                   bps.batch_id,
                   bps.session_name,
                   bps.session_type,
                   bps.shot_count AS rounds_fired,
                   bps.group_size_mm AS best_group_mm,
                   bps.group_size_mm AS avg_group_mm,
                   bps.notes,
                   bps.analysis_json,
                   bp.rifle_id
            FROM batch_project_sessions bps
            JOIN batch_projects bp ON bp.id = bps.batch_id
            WHERE bp.source_workflow = ?
            ORDER BY bps.session_date DESC, bps.id DESC
            LIMIT 10
        """.split()
    )
    chrono_query = " ".join(
        """
            SELECT session_date, shot_count, avg_velocity_fps, es_fps, sd_fps, notes, session_name
            FROM chronograph_sessions
            WHERE import_meta_json LIKE ?
              AND (? = '' OR session_date >= ?)
            ORDER BY session_date DESC
            LIMIT 10
        """.split()
    )
    pressure_sign_query = " ".join(
        """
            SELECT notes, primer_image_path, primer_image_quality,
                   primer_image_observation, primer_image_confidence, date,
                                     workflow_id, load_session_id, session_name,
                                     batch_id, batch_session_id, rifle_id, barrel_id, barrel_name
            FROM pressure_signs
            WHERE ammo_profile_id = ?
                            AND (? IS NULL OR rifle_id IS NULL OR rifle_id = ?)
                            AND (? = '' OR barrel_id IS NULL OR barrel_id = ?)
              AND (? = '' OR date >= ?)
            ORDER BY date DESC, id DESC
            LIMIT 10
        """.split()
    )
    db = _FakeDb(
        query_results={
            (explicit_batch_query, ("workflow:12",)): [
                {
                    "date": "2026-03-25",
                    "batch_session_id": 71,
                    "batch_id": 19,
                    "session_name": "Batch A",
                    "session_type": "group",
                    "rounds_fired": 5,
                    "best_group_mm": 10.5,
                    "avg_group_mm": 10.5,
                    "notes": "Target session for batch A.",
                    "analysis_json": "{}",
                    "rifle_id": 4,
                }
            ],
            (chrono_query, ('%"workflow_id": 12%', "2026-03-20", "2026-03-20")): [
                {
                    "session_date": "2026-03-25",
                    "shot_count": 5,
                    "avg_velocity_fps": 2712.0,
                    "es_fps": 9.0,
                    "sd_fps": 3.0,
                    "notes": "Chronograph session for batch B.",
                    "session_name": "Batch B",
                }
            ],
            (pressure_sign_query, (19, 4, 4, "", "", "2026-03-20", "2026-03-20")): [
                {
                    "notes": "Pressure note for batch A.",
                    "primer_image_path": "",
                    "primer_image_quality": "",
                    "primer_image_observation": "",
                    "primer_image_confidence": "",
                    "date": "2026-03-25",
                    "workflow_id": 12,
                    "load_session_id": None,
                    "session_name": "Batch A",
                    "batch_id": 19,
                    "batch_session_id": 71,
                    "rifle_id": 4,
                    "barrel_id": None,
                    "barrel_name": None,
                }
            ],
        }
    )

    observations = workflow_module.collect_workflow_observations(
        db,
        {
            "id": 12,
            "name": "OCW Test",
            "rifle_id": 4,
            "ammo_profile_id": 19,
            "created_date": "2026-03-20",
        },
    )

    assert len(observations["evidence_records"]) == 2
    source_sets = [
        set(record["sources"]) for record in observations["evidence_records"]
    ]
    assert {"target", "pressure"} in source_sets
    assert {"chronograph"} in source_sets


def test_build_primer_baseline_assessment_respects_disabled_primer_review():
    assessment = workflow_module._build_primer_baseline_assessment(
        {"name": "6.5 CM Trainer"},
        {
            "explicit_batch_sessions": [
                {
                    "primer_image_review": {
                        "enabled": False,
                        "batch_id": 19,
                        "rifle_id": 4,
                    }
                }
            ],
            "pressure_sign_rows": [
                {
                    "notes": "Velocity uptick only.",
                    "primer_image_path": "",
                    "primer_image_observation": "",
                    "date": "2026-03-25",
                }
            ],
        },
    )

    assert assessment["level"] == "neutral"
    assert assessment["title"] == "Primer image review disabled by user"
    assert "should not nag for primer photos" in assessment["message"]


def test_build_primer_image_pressure_note_returns_empty_without_image_or_observation():
    assert workflow_module._build_primer_image_pressure_note({}) == ""


def test_pressure_advisory_can_be_upgraded_by_observed_pressure_notes():
    advisory = workflow_module.build_workflow_pressure_advisory(
        {
            "protocol": "ocw",
            "notes": "Skyteøkt: ejector mark og flat primer i øvre node.",
        }
    )

    assert advisory["level"] == "critical"
    assert advisory["title"] == "Pressure spike risk"


def test_build_workflow_readiness_summary_stops_on_pressure_signs():
    summary = workflow_module.build_workflow_readiness_summary(
        {
            "target_es_sd": 10,
            "target_sd": 8,
            "target_group_size": 0.5,
        },
        {
            "pressure_notes": ["Flat primer og ejector mark på siste steg"],
            "chronograph_sessions": [{"id": 1}],
            "best_es_fps": 9.0,
            "best_sd_fps": 4.0,
            "best_group_mm": 12.0,
        },
    )

    assert summary["level"] == "stop"
    assert (
        "pressure" in summary["title"].lower()
        or "pressure" in summary["message"].lower()
    )


def test_build_workflow_readiness_summary_needs_more_data_without_group():
    summary = workflow_module.build_workflow_readiness_summary(
        {
            "target_es_sd": 10,
            "target_sd": 8,
            "target_group_size": 0.5,
        },
        {
            "pressure_notes": [],
            "chronograph_sessions": [{"id": 1}],
            "best_es_fps": 9.0,
            "best_sd_fps": 4.0,
            "best_group_mm": None,
        },
    )

    assert summary["level"] == "more_data"
    assert "missing" in summary["message"].lower()
    assert summary["confidence_label"] == "Low Confidence"


def test_build_workflow_readiness_summary_can_mark_ready():
    summary = workflow_module.build_workflow_readiness_summary(
        {
            "target_es_sd": 10,
            "target_sd": 8,
            "target_group_size": 0.5,
        },
        {
            "pressure_notes": [],
            "chronograph_sessions": [{"id": 1}],
            "best_es_fps": 8.0,
            "best_sd_fps": 4.0,
            "best_group_mm": 11.0,
        },
    )

    assert summary["level"] == "ready"
    assert "next step" in summary["title"].lower()
    assert summary["confidence_label"] in {
        "Medium confidence",
        "High confidence",
        "Medium Confidence",
        "High Confidence",
    }


def test_build_workflow_readiness_summary_holds_ready_when_robustness_is_low():
    class _RobustnessDb:
        pass

    original = workflow_module.build_workflow_component_robustness
    workflow_module.build_workflow_component_robustness = lambda db, workflow: {
        "level": "critical",
        "score": 42,
    }
    try:
        summary = workflow_module.build_workflow_readiness_summary(
            {
                "target_es_sd": 10,
                "target_sd": 8,
                "target_group_size": 0.5,
            },
            {
                "pressure_notes": [],
                "chronograph_sessions": [{"id": 1}],
                "best_es_fps": 8.0,
                "best_sd_fps": 4.0,
                "best_group_mm": 11.0,
            },
            _RobustnessDb(),
        )
    finally:
        workflow_module.build_workflow_component_robustness = original

    assert summary["level"] == "more_data"
    assert "robustness" in summary["message"].lower()


def test_build_workflow_readiness_summary_requires_control_series_on_warning_robustness():
    class _RobustnessDb:
        pass

    original = workflow_module.build_workflow_component_robustness
    workflow_module.build_workflow_component_robustness = lambda db, workflow: {
        "level": "warning",
        "score": 64,
    }
    try:
        summary = workflow_module.build_workflow_readiness_summary(
            {
                "target_es_sd": 10,
                "target_sd": 8,
                "target_group_size": 0.5,
            },
            {
                "pressure_notes": [],
                "chronograph_sessions": [{"id": 1}],
                "best_es_fps": 8.0,
                "best_sd_fps": 4.0,
                "best_group_mm": 11.0,
            },
            _RobustnessDb(),
        )
    finally:
        workflow_module.build_workflow_component_robustness = original

    assert summary["level"] == "more_data"
    assert "control series" in summary["message"].lower()


def test_format_workflow_readiness_html_includes_confidence():
    html = workflow_module.format_workflow_readiness_html(
        {
            "level": "ready",
            "title": "Klar for next step",
            "message": "Workflowet ser bra ut.",
            "confidence_label": "High Confidence",
            "confidence_message": "The status is based on both measured data and usable robustness.",
        }
    )

    assert "High Confidence" in html
    assert "usable robustness" in html


def test_build_workflow_evidence_quality_summarizes_combined_signals():
    class _EvidenceDb:
        pass

    original_readiness = workflow_module.build_workflow_readiness_summary
    original_robustness = workflow_module.build_workflow_component_robustness
    original_next_test = workflow_module.build_workflow_next_test_recommendation
    original_verification = (
        workflow_module.build_workflow_component_verification_advisory
    )
    original_impact = workflow_module.build_workflow_impact_window
    workflow_module.build_workflow_readiness_summary = (
        lambda workflow, observations, db=None: {
            "confidence_label": "High Confidence",
        }
    )
    workflow_module.build_workflow_component_robustness = lambda db, workflow: {
        "score": 78
    }
    workflow_module.build_workflow_next_test_recommendation = (
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence",
        }
    )
    workflow_module.build_workflow_component_verification_advisory = (
        lambda db, workflow: {"level": "warning"}
    )
    workflow_module.build_workflow_impact_window = lambda db, workflow, observations: {
        "confidence_label": "Medium Confidence"
    }
    try:
        summary = workflow_module.build_workflow_evidence_quality(
            {"usage_profile": "hunting_medium"},
            {"chronograph_sessions": [{"id": 1}]},
            _EvidenceDb(),
        )
    finally:
        workflow_module.build_workflow_readiness_summary = original_readiness
        workflow_module.build_workflow_component_robustness = original_robustness
        workflow_module.build_workflow_next_test_recommendation = original_next_test
        workflow_module.build_workflow_component_verification_advisory = (
            original_verification
        )
        workflow_module.build_workflow_impact_window = original_impact

    assert summary["title"] in {"Usable Evidence Quality", "High Evidence Quality"}
    assert summary["checks"]
    assert any("Readiness" in item for item in summary["checks"])


def test_format_workflow_evidence_quality_html_includes_checks():
    html = workflow_module.format_workflow_evidence_quality_html(
        {
            "level": "medium",
            "title": "Usable Evidence Quality",
            "message": "The data foundation is useful, but not fully confirmed yet.",
            "score": 3.25,
            "checks": ["Readiness: High Confidence", "Robustness: 78/100"],
        }
    )

    assert "Usable Evidence Quality" in html
    assert "3.2" in html or "3.3" in html
    assert "Readiness: High confidence" in html or "Readiness: High Confidence" in html


def test_build_workflow_evidence_quality_reports_primer_review_coverage():
    original_readiness = workflow_module.build_workflow_readiness_summary
    original_robustness = workflow_module.build_workflow_component_robustness
    original_next_test = workflow_module.build_workflow_next_test_recommendation
    original_verification = (
        workflow_module.build_workflow_component_verification_advisory
    )
    original_impact = workflow_module.build_workflow_impact_window
    original_input_quality = workflow_module.build_input_quality_summary
    original_internal_ballistics = (
        workflow_module.build_workflow_internal_ballistics_summary
    )

    workflow_module.build_workflow_readiness_summary = (
        lambda workflow, observations, db=None: {"confidence_label": "High Confidence"}
    )
    workflow_module.build_workflow_component_robustness = lambda db, workflow: {
        "score": 78
    }
    workflow_module.build_workflow_next_test_recommendation = (
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence"
        }
    )
    workflow_module.build_workflow_component_verification_advisory = (
        lambda db, workflow: {"level": "warning"}
    )
    workflow_module.build_workflow_impact_window = lambda db, workflow, observations: {
        "confidence_label": "Medium Confidence"
    }
    workflow_module.build_input_quality_summary = (
        lambda workflow, observations, bullet_data=None, environment=None: {
            "level": "high",
            "title": "High Input Quality",
            "checks": [],
        }
    )
    workflow_module.build_workflow_internal_ballistics_summary = lambda db, workflow: {
        "level": "ok",
        "title": "Internal Ballistics",
        "checks": [],
    }
    try:
        summary = workflow_module.build_workflow_evidence_quality(
            {"usage_profile": "hunting_medium"},
            {
                "chronograph_sessions": [{"id": 1}],
                "pressure_sign_rows": [
                    {
                        "primer_image_path": "reports/primer-step-5.jpg",
                        "primer_image_observation": "light crater around the firing pin",
                    },
                    {"notes": "heavy bolt lift observed"},
                ],
            },
            _FakeDb(),
        )
    finally:
        workflow_module.build_workflow_readiness_summary = original_readiness
        workflow_module.build_workflow_component_robustness = original_robustness
        workflow_module.build_workflow_next_test_recommendation = original_next_test
        workflow_module.build_workflow_component_verification_advisory = (
            original_verification
        )
        workflow_module.build_workflow_impact_window = original_impact
        workflow_module.build_input_quality_summary = original_input_quality
        workflow_module.build_workflow_internal_ballistics_summary = (
            original_internal_ballistics
        )

    assert any(
        "Pressure review coverage: 1/2 pressure observations have primer-image support"
        in item
        for item in summary["checks"]
    )


def test_build_workflow_evidence_quality_reports_linked_evidence_coverage():
    original_readiness = workflow_module.build_workflow_readiness_summary
    original_robustness = workflow_module.build_workflow_component_robustness
    original_next_test = workflow_module.build_workflow_next_test_recommendation
    original_verification = (
        workflow_module.build_workflow_component_verification_advisory
    )
    original_impact = workflow_module.build_workflow_impact_window
    original_input_quality = workflow_module.build_input_quality_summary
    original_internal_ballistics = (
        workflow_module.build_workflow_internal_ballistics_summary
    )

    workflow_module.build_workflow_readiness_summary = (
        lambda workflow, observations, db=None: {"confidence_label": "High Confidence"}
    )
    workflow_module.build_workflow_component_robustness = lambda db, workflow: {
        "score": 78
    }
    workflow_module.build_workflow_next_test_recommendation = (
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence"
        }
    )
    workflow_module.build_workflow_component_verification_advisory = (
        lambda db, workflow: {"level": "warning"}
    )
    workflow_module.build_workflow_impact_window = lambda db, workflow, observations: {
        "confidence_label": "Medium Confidence"
    }
    workflow_module.build_input_quality_summary = (
        lambda workflow, observations, bullet_data=None, environment=None: {
            "level": "high",
            "title": "High Input Quality",
            "checks": [],
        }
    )
    workflow_module.build_workflow_internal_ballistics_summary = lambda db, workflow: {
        "level": "ok",
        "title": "Internal Ballistics",
        "checks": [],
    }
    try:
        summary = workflow_module.build_workflow_evidence_quality(
            {"usage_profile": "hunting_medium"},
            {
                "chronograph_sessions": [{"id": 1}],
                "evidence_records": [
                    {
                        "sources": ["target", "chronograph", "pressure", "environment"],
                    },
                    {
                        "sources": ["target", "chronograph"],
                    },
                ],
            },
            _FakeDb(),
        )
    finally:
        workflow_module.build_workflow_readiness_summary = original_readiness
        workflow_module.build_workflow_component_robustness = original_robustness
        workflow_module.build_workflow_next_test_recommendation = original_next_test
        workflow_module.build_workflow_component_verification_advisory = (
            original_verification
        )
        workflow_module.build_workflow_impact_window = original_impact
        workflow_module.build_input_quality_summary = original_input_quality
        workflow_module.build_workflow_internal_ballistics_summary = (
            original_internal_ballistics
        )

    assert any(
        "Linked evidence coverage: 1/2 complete test days and 2/2 cross-linked days"
        in item
        for item in summary["checks"]
    )


def test_build_workflow_evidence_quality_prefers_complete_linked_evidence_days():
    original_readiness = workflow_module.build_workflow_readiness_summary
    original_robustness = workflow_module.build_workflow_component_robustness
    original_next_test = workflow_module.build_workflow_next_test_recommendation
    original_verification = (
        workflow_module.build_workflow_component_verification_advisory
    )
    original_impact = workflow_module.build_workflow_impact_window
    original_input_quality = workflow_module.build_input_quality_summary
    original_internal_ballistics = (
        workflow_module.build_workflow_internal_ballistics_summary
    )

    workflow_module.build_workflow_readiness_summary = (
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence"
        }
    )
    workflow_module.build_workflow_component_robustness = lambda db, workflow: {
        "score": 55
    }
    workflow_module.build_workflow_next_test_recommendation = (
        lambda workflow, observations, db=None: {
            "confidence_label": "Medium Confidence"
        }
    )
    workflow_module.build_workflow_component_verification_advisory = (
        lambda db, workflow: {"level": ""}
    )
    workflow_module.build_workflow_impact_window = lambda db, workflow, observations: {
        "confidence_label": "Medium Confidence",
        "level": "ok",
    }
    workflow_module.build_input_quality_summary = (
        lambda workflow, observations, bullet_data=None, environment=None: {
            "level": "medium",
            "title": "Usable Input Quality",
            "checks": [],
        }
    )
    workflow_module.build_workflow_internal_ballistics_summary = lambda db, workflow: {
        "level": "ok",
        "title": "Internal Ballistics",
        "checks": [],
    }
    try:
        fragmented = workflow_module.build_workflow_evidence_quality(
            {"usage_profile": "precision"},
            {
                "evidence_records": [
                    {"sources": ["target"]},
                    {"sources": ["chronograph"]},
                ]
            },
            _FakeDb(),
        )
        complete = workflow_module.build_workflow_evidence_quality(
            {"usage_profile": "precision"},
            {
                "evidence_records": [
                    {"sources": ["target", "chronograph", "pressure", "environment"]},
                    {"sources": ["target", "chronograph"]},
                ]
            },
            _FakeDb(),
        )
    finally:
        workflow_module.build_workflow_readiness_summary = original_readiness
        workflow_module.build_workflow_component_robustness = original_robustness
        workflow_module.build_workflow_next_test_recommendation = original_next_test
        workflow_module.build_workflow_component_verification_advisory = (
            original_verification
        )
        workflow_module.build_workflow_impact_window = original_impact
        workflow_module.build_input_quality_summary = original_input_quality
        workflow_module.build_workflow_internal_ballistics_summary = (
            original_internal_ballistics
        )

    assert complete["score"] > fragmented["score"]


def test_format_workflow_evidence_basis_html_labels_measured_modeled_and_recommended():
    html = workflow_module.format_workflow_evidence_basis_html(
        {
            "chronograph_sessions": [{"id": 1}, {"id": 2}],
            "shooting_sessions": [{"id": 9}],
            "best_es_fps": 11.0,
            "best_group_mm": 18.5,
            "pressure_notes": ["Flat primer observed"],
        }
    )

    assert "Measured:" in html
    assert "Modeled:" in html
    assert "Recommended:" in html
    assert "Chronograph sessions: 2" in html


def test_format_workflow_evidence_basis_html_renders_environment_in_timeline_cards():
    html = workflow_module.format_workflow_evidence_basis_html(
        {
            "evidence_records": [
                {
                    "date": "2026-03-25",
                    "sources": ["target", "chronograph", "pressure", "environment"],
                    "rounds_fired": 10,
                    "best_group_mm": 10.5,
                    "best_es_fps": 9.0,
                    "pressure_events": 1,
                    "primer_image_reviews": 1,
                    "environment_samples": 1,
                    "location_name": "Rena",
                    "temperature_c": 7.0,
                    "pressure_hpa": 1002.0,
                    "wind_speed_ms": 2.0,
                    "density_altitude_ft": 950.0,
                    "notes": ["Tight node around 42.4 gr."],
                }
            ]
        }
    )

    assert "Evidence timeline:" in html
    assert "Sources:</b> target, chronograph, pressure, environment" in html
    assert "Environment:</b> Rena | 7.0 C | 1002 hPa | Wind 2.0 m/s | DA 950 ft" in html
    assert "Environment samples: 1" in html


def test_format_workflow_evidence_basis_html_includes_environment_linked_counts():
    html = workflow_module.format_workflow_evidence_basis_html(
        {
            "evidence_records": [
                {
                    "date": "2026-03-25",
                    "has_cross_source_evidence": True,
                    "environment_samples": 1,
                },
                {
                    "date": "2026-03-24",
                    "has_cross_source_evidence": False,
                    "environment_samples": 0,
                },
            ]
        }
    )

    assert "Environment-linked evidence days: 1/2" in html


def test_workflow_detail_opens_batch_workspace_via_launcher(monkeypatch):
    calls = []
    launcher = SimpleNamespace(show_batch_workspace=lambda: calls.append("batch"))
    accepted = []
    widget = SimpleNamespace(
        workflow_id=1,
        db=SimpleNamespace(get_by_id=lambda table, workflow_id: {"protocol": "ocw"}),
        _find_workflow_launcher=lambda: launcher,
        accept=lambda: accepted.append(True),
    )

    workflow_module.WorkflowDetailDialog.create_test_batch(widget)

    assert calls == ["batch"]
    assert accepted == [True]


def test_workflow_detail_opens_chronograph_via_launcher():
    calls = []
    launcher = SimpleNamespace(
        launch_workflow=lambda workflow_id: calls.append(workflow_id)
    )
    accepted = []
    widget = SimpleNamespace(
        workflow_id=1,
        db=SimpleNamespace(get_by_id=lambda table, workflow_id: {"protocol": "ocw"}),
        _find_workflow_launcher=lambda: launcher,
        accept=lambda: accepted.append(True),
    )

    workflow_module.WorkflowDetailDialog.import_chronograph_data(widget)

    assert calls == ["chronograph_import"]
    assert accepted == [True]


def test_workflow_detail_opens_target_analyzer_via_launcher():
    calls = []
    launcher = SimpleNamespace(show_target_analyzer=lambda: calls.append("target"))
    accepted = []
    widget = SimpleNamespace(
        workflow_id=1,
        db=SimpleNamespace(get_by_id=lambda table, workflow_id: {"protocol": "ocw"}),
        _find_workflow_launcher=lambda: launcher,
        accept=lambda: accepted.append(True),
    )

    workflow_module.WorkflowDetailDialog.upload_target_image(widget)

    assert calls == ["target"]
    assert accepted == [True]
