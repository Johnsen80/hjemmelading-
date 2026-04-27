from types import SimpleNamespace

import src.ui.main_window as main_window_module
from src.ui.main_window import MainWindow


def test_active_workflow_status_includes_next_test_confidence():
    class _Settings:
        def __init__(self, *args, **kwargs):
            pass

        def value(self, key, default=None):
            mapping = {
                "workflow_context/workflow_id": 7,
                "workflow_context/barrel_name": "26in Match",
                "workflow_context/barrel_configuration_name": "Suppressed",
            }
            return mapping.get(key, default)

    widget = SimpleNamespace(
        db=SimpleNamespace(
            get_by_id=lambda table, workflow_id: {
                "id": workflow_id,
                "name": "WF-1",
                "usage_profile": "precision",
            }
        ),
    )

    import src.modules.load_development_workflow as workflow_module

    original_qsettings = main_window_module.QSettings
    original_collect = workflow_module.collect_workflow_observations
    original_readiness = workflow_module.build_workflow_readiness_summary
    original_robustness = workflow_module.build_workflow_component_robustness
    original_next_test = workflow_module.build_workflow_next_test_recommendation
    original_impact = workflow_module.build_workflow_impact_window
    original_evidence = workflow_module.build_workflow_evidence_quality
    original_calibration = workflow_module.build_workflow_calibration_summary
    original_internal_ballistics = (
        workflow_module.build_workflow_internal_ballistics_summary
    )
    original_environment = workflow_module._build_workflow_environment
    main_window_module.QSettings = _Settings
    workflow_module.collect_workflow_observations = lambda db, workflow: {}
    workflow_module.build_workflow_readiness_summary = (
        lambda workflow, observations, db=None: {
            "title": "Klar for neste steg",
            "message": "Ser bra ut.",
            "level": "ready",
            "confidence_label": "High confidence",
            "confidence_message": "Readiness bygger på godt datagrunnlag.",
        }
    )
    workflow_module.build_workflow_component_robustness = lambda db, workflow: {
        "title": "Usable robustness",
        "message": "",
        "level": "ok",
        "score": 82,
        "uncertainty_message": "Robustness can still move a bit after the next control series.",
    }
    workflow_module.build_workflow_next_test_recommendation = (
        lambda workflow, observations, db=None: {
            "title": "Best Next Test: Verification Series",
            "action": "Fire 3 control shots.",
            "confidence_label": "Medium confidence",
            "confidence_message": "Neste steg er godt, men bør fortsatt bekreftes.",
        }
    )
    workflow_module.build_workflow_impact_window = lambda db, workflow, observations: {
        "title": "Impact Window",
        "message": "God margin ved 180 m.",
        "level": "ok",
        "checks": ["Vurderingen bruker BC (G7) 0.245 og jaktavstand 180 m."],
        "drag_model": "G7",
        "bc_used": 0.245,
        "bc_segment_label": "G7 0.245 @ 2600-3000 fps",
        "density_altitude_m": 245.0,
        "confidence_label": "High confidence",
        "confidence_message": "Impact-vurderingen bygger på brukbart chrono-grunnlag.",
    }
    workflow_module.build_workflow_evidence_quality = lambda workflow, observations, db=None: {
        "title": "Usable evidence quality",
        "message": "Measured data and robustness point in a reasonably similar direction.",
        "level": "medium",
        "checks": ["Readiness: High confidence", "Robustness: 82/100"],
    }
    workflow_module.build_workflow_calibration_summary = lambda db, workflow: {
        "title": "Kalibreringsprofilen ser brukbar ut",
        "message": "Pipe/løp-læring og komponentdata peker i samme retning.",
        "level": "ok",
        "score": 78,
        "checks": ["Cold-bore drift er låst mot 4 serier."],
    }
    workflow_module.build_workflow_internal_ballistics_summary = lambda db, workflow: {
        "title": "Internal Ballistics",
        "message": "Fyllrate 97.0%, kompresjon 1.02x.",
        "level": "ok",
        "checks": ["Fill ratio sits in a healthy working window."],
    }
    workflow_module._build_workflow_environment = lambda observations: SimpleNamespace(
        summary=lambda: {
            "temperature_c": 12.0,
            "pressure_hpa": 1002.0,
            "humidity_percent": 71.0,
            "density_altitude_m": 245.0,
            "density_ratio": 0.984,
            "temperature_source": "measured",
        }
    )
    workflow_module.collect_workflow_observations = lambda db, workflow: {
        "chronograph_sessions": [
            {"session_date": "2026-03-01", "avg_velocity_fps": 812.0},
            {"session_date": "2026-03-05", "avg_velocity_fps": 818.5},
        ],
        "shooting_sessions": [],
        "pressure_notes": ["Lett flattening i primer på siste serie."],
        "accuracy_test_sessions": [
            {
                "test_date": "2026-03-07",
                "average_group_size_mm": 16.4,
                "best_group_mm": 12.8,
                "average_velocity_fps": 817.0,
            }
        ],
    }
    try:
        status = MainWindow._get_active_workflow_status(widget)
    finally:
        main_window_module.QSettings = original_qsettings
        workflow_module.collect_workflow_observations = original_collect
        workflow_module.build_workflow_readiness_summary = original_readiness
        workflow_module.build_workflow_component_robustness = original_robustness
        workflow_module.build_workflow_next_test_recommendation = original_next_test
        workflow_module.build_workflow_impact_window = original_impact
        workflow_module.build_workflow_evidence_quality = original_evidence
        workflow_module.build_workflow_calibration_summary = original_calibration
        workflow_module.build_workflow_internal_ballistics_summary = (
            original_internal_ballistics
        )
        workflow_module._build_workflow_environment = original_environment

    assert status["next_test_title"] == "Best Next Test: Verification Series"
    assert status["next_test_confidence_label"] == "Medium confidence"
    assert "bekreftes" in status["next_test_confidence_message"].lower()
    assert "control series" in status["robustness_uncertainty_message"].lower()
    assert status["evidence_quality_title"] == "Usable evidence quality"
    assert status["evidence_quality_checks"] == [
        "Readiness: High confidence",
        "Robustness: 82/100",
    ]
    assert status["impact_title"] == "Impact Window"
    assert status["impact_drag_model"] == "G7"
    assert status["impact_bc_used"] == "0.245"
    assert status["impact_bc_segment"] == "G7 0.245 @ 2600-3000 fps"
    assert status["impact_density_altitude_m"] == "245.0"
    assert status["impact_confidence_label"] == "High confidence"
    assert status["setup_label"] == "26in Match / Suppressed"
    assert status["message"].startswith("Setup 26in Match / Suppressed. ")
    assert status["next_test_action"].startswith("Setup 26in Match / Suppressed. ")
    assert status["impact_message"].startswith("Setup 26in Match / Suppressed. ")
    assert status["internal_ballistics_title"] == "Internal Ballistics"
    assert "97.0%" in status["internal_ballistics_message"]
    assert status["internal_ballistics_checks"] == [
        "Fill ratio sits in a healthy working window."
    ]
    assert status["calibration_title"] == "Kalibreringsprofilen ser brukbar ut"
    assert "komponentdata" in status["calibration_message"].lower()
    assert status["environment_title"] == "Environment"
    assert "1002.0 hPa" in status["environment_message"]
    assert status["environment_checks"] == [
        "Environment basis: measured",
        "Density ratio: 0.984",
    ]
    assert status["report_plot_x"] == ["2026-03-01", "2026-03-05"]
    assert status["report_plot_y"] == [812.0, 818.5]
    assert status["report_plot_ylabel"] == "Hastighet (fps)"
    assert status["accuracy_test_summary"] == [
        "2026-03-07, avg 16.4 mm, best 12.8 mm, 817 fps"
    ]
    assert status["pressure_notes"] == ["Lett flattening i primer på siste serie."]
    assert status["uncertainty_summary"] == [
        "Readiness: Readiness bygger på godt datagrunnlag.",
        "Robustness: Robustness can still move a bit after the next control series.",
        "Impact: Impact-vurderingen bygger på brukbart chrono-grunnlag.",
    ]


def test_format_workflow_display_name_appends_setup_for_load_flows():
    widget = SimpleNamespace(
        _get_active_workflow_setup_label=lambda: "26in Match / Suppressed"
    )

    display_name = MainWindow._format_workflow_display_name(
        widget,
        "Load Development",
        "load_development",
    )
    unrelated_name = MainWindow._format_workflow_display_name(
        widget,
        "Component Database",
        "component_database",
    )

    assert display_name == "Load Development (26in Match / Suppressed)"
    assert unrelated_name == "Component Database"


def test_generate_pdf_report_includes_internal_ballistics_section():
    captured: dict[str, object] = {}

    class _ReportModule:
        @staticmethod
        def generate_pdf_report(data, pdf_path):
            captured["data"] = data
            captured["pdf_path"] = pdf_path

    status_payload = {
        "workflow_name": "WF-1",
        "title": "Klar for neste steg",
        "impact_title": "Trygg impact",
        "impact_message": "God margin ved 180 m.",
        "impact_checks": ["Vurderingen bruker BC (G7) 0.245 og jaktavstand 180 m."],
        "impact_drag_model": "G7",
        "impact_bc_used": "0.245",
        "impact_bc_segment": "G7 0.245 @ 2600-3000 fps",
        "impact_density_altitude_m": "245.0",
        "impact_confidence_label": "High confidence",
        "impact_confidence_message": "Impact-vurderingen bygger på brukbart chrono-grunnlag.",
        "evidence_quality_title": "Usable evidence quality",
        "evidence_quality_checks": ["Readiness: High confidence"],
        "calibration_title": "Kalibreringsprofilen ser brukbar ut",
        "calibration_message": "Pipe/løp-læring og komponentdata peker i samme retning.",
        "calibration_checks": ["Cold-bore drift er låst mot 4 serier."],
        "internal_ballistics_title": "Internal Ballistics",
        "internal_ballistics_message": "Fyllrate 97.0%, kompresjon 1.02x.",
        "internal_ballistics_checks": ["Fill ratio sits in a healthy working window."],
        "environment_title": "Environment",
        "environment_message": "Temp 12.0 C, pressure 1002.0 hPa, RH 71%, DA approx. 245 m.",
        "environment_checks": [
            "Environment basis: measured",
            "Density ratio: 0.984",
        ],
        "report_plot_x": ["2026-03-01", "2026-03-05"],
        "report_plot_y": [812.0, 818.5],
        "report_plot_xlabel": "Serie",
        "report_plot_ylabel": "Hastighet (fps)",
        "chronograph_summary": [
            "2026-03-01: 812 fps, ES 24, SD 8.1",
            "2026-03-05: 818 fps, ES 18, SD 6.4",
        ],
        "shooting_summary": ["2026-03-06: gruppe 14.2 mm, 5 skudd"],
        "accuracy_test_summary": ["2026-03-07, avg 16.4 mm, best 12.8 mm, 817 fps"],
        "pressure_notes": ["Lett flattening i primer på siste serie."],
        "uncertainty_summary": [
            "Readiness: Readiness bygger på godt datagrunnlag.",
            "Robustness: Robustness can still move a bit after the next control series.",
            "Impact: Impact-vurderingen bygger på brukbart chrono-grunnlag.",
        ],
        "_show_status_message": lambda message: None,
    }
    widget = SimpleNamespace()
    widget._get_active_workflow_status = lambda: status_payload
    widget._build_workflow_pdf_report_data = (
        lambda: MainWindow._build_workflow_pdf_report_data(widget)
    )
    widget._show_status_message = lambda message: captured.setdefault("status", message)

    original_import_module = main_window_module.importlib.import_module
    main_window_module.importlib.import_module = lambda name: _ReportModule
    try:
        MainWindow._generate_pdf_report(widget)
    finally:
        main_window_module.importlib.import_module = original_import_module

    data = dict(captured["data"])
    assert captured["pdf_path"] == "session_report.pdf"
    assert data["title"] == "Workflow Report - WF-1"
    assert data["internal_ballistics_summary"]["title"] == "Internal Ballistics"
    assert "97.0%" in data["internal_ballistics_summary"]["message"]
    assert "Internal Ballistics Checks" in data["sections"]
    assert "Trygg impact" in data["sections"]
    assert any(
        "Drag basis: G7 / BC 0.245" in line for line in data["sections"]["Trygg impact"]
    )
    assert any(
        "Segmented BC: G7 0.245 @ 2600-3000 fps" in line
        for line in data["sections"]["Trygg impact"]
    )
    assert "Kalibreringsprofilen ser brukbar ut" in data["sections"]
    assert "Environment" in data["sections"]
    assert "Chronograph Series" in data["sections"]
    assert "Group Series" in data["sections"]
    assert "Accuracy Tests" in data["sections"]
    assert "Uncertainty" in data["sections"]
    assert "Observerte trykksignaler" in data["sections"]
    assert data["x"] == ["2026-03-01", "2026-03-05"]
    assert data["y"] == [812.0, 818.5]
    assert data["y_label"] == "Hastighet (fps)"


def test_build_workflow_pdf_report_data_includes_scientific_sections():
    widget = SimpleNamespace(
        _get_active_workflow_status=lambda: {
            "workflow_name": "WF-1",
            "title": "Klar for neste steg",
            "impact_title": "Trygg impact",
            "impact_message": "God margin ved 180 m.",
            "impact_checks": ["Vurderingen bruker BC (G7) 0.245 og jaktavstand 180 m."],
            "impact_drag_model": "G7",
            "impact_bc_used": "0.245",
            "impact_bc_segment": "G7 0.245 @ 2600-3000 fps",
            "impact_density_altitude_m": "245.0",
            "impact_confidence_label": "High confidence",
            "impact_confidence_message": "Impact-vurderingen bygger på brukbart chrono-grunnlag.",
            "evidence_quality_title": "Usable evidence quality",
            "evidence_quality_checks": ["Readiness: High confidence"],
            "calibration_title": "Kalibreringsprofilen ser brukbar ut",
            "calibration_message": "Pipe/løp-læring og komponentdata peker i samme retning.",
            "calibration_checks": ["Cold-bore drift er låst mot 4 serier."],
            "internal_ballistics_title": "Internal Ballistics",
            "internal_ballistics_message": "Fyllrate 97.0%, kompresjon 1.02x.",
            "internal_ballistics_metrics": [
                {"name": "Fyllrate", "value": "97.0%"},
                {"name": "Kompresjon", "value": "1.02x"},
            ],
            "internal_ballistics_case_context": [
                "H2O basis: 53.80 gr from the selected case (4 source points).",
                "Trim length 48.77 mm from the selected case is available in the workflow context.",
            ],
            "internal_ballistics_checks": [
                "Fill ratio sits in a healthy working window."
            ],
            "environment_title": "Environment",
            "environment_message": "Temp 12.0 C, pressure 1002.0 hPa, RH 71%, DA approx. 245 m.",
            "environment_checks": [
                "Environment basis: measured",
                "Density ratio: 0.984",
            ],
            "report_plot_x": ["2026-03-01", "2026-03-05"],
            "report_plot_y": [812.0, 818.5],
            "report_plot_xlabel": "Serie",
            "report_plot_ylabel": "Hastighet (fps)",
            "chronograph_summary": [
                "2026-03-01: 812 fps, ES 24, SD 8.1",
                "2026-03-05: 818 fps, ES 18, SD 6.4",
            ],
            "shooting_summary": ["2026-03-06: gruppe 14.2 mm, 5 skudd"],
            "pressure_notes": ["Lett flattening i primer på siste serie."],
            "uncertainty_summary": [
                "Readiness: Readiness bygger på godt datagrunnlag.",
                "Impact: Impact-vurderingen bygger på brukbart chrono-grunnlag.",
            ],
        }
    )

    data = MainWindow._build_workflow_pdf_report_data(widget)

    assert data["title"] == "Workflow Report - WF-1"
    assert data["internal_ballistics_summary"]["title"] == "Internal Ballistics"
    assert data["internal_ballistics_summary"]["metrics"] == [
        {"name": "Fyllrate", "value": "97.0%"},
        {"name": "Kompresjon", "value": "1.02x"},
    ]
    assert data["internal_ballistics_summary"]["context_lines"] == [
        "H2O basis: 53.80 gr from the selected case (4 source points).",
        "Trim length 48.77 mm from the selected case is available in the workflow context.",
    ]
    assert "Trygg impact" in data["sections"]
    assert data["x"] == ["2026-03-01", "2026-03-05"]
    assert data["y"] == [812.0, 818.5]


def test_build_workflow_report_export_payload_includes_scientific_core_data():
    widget = SimpleNamespace(
        _get_active_workflow_status=lambda: {
            "workflow_name": "WF-1",
            "usage_profile": "precision",
            "title": "Klar for neste steg",
            "message": "Ser bra ut.",
            "level": "ready",
            "confidence_label": "High confidence",
            "confidence_message": "Readiness bygger på godt datagrunnlag.",
            "impact_title": "Impact Window",
            "impact_message": "God margin ved 180 m.",
            "impact_level": "ok",
            "impact_checks": ["Vurderingen bruker BC (G7) 0.245 og jaktavstand 180 m."],
            "impact_drag_model": "G7",
            "impact_bc_used": "0.245",
            "impact_bc_segment": "G7 0.245 @ 2600-3000 fps",
            "impact_density_altitude_m": "245.0",
            "impact_confidence_label": "High confidence",
            "impact_confidence_message": "Impact-vurderingen bygger på brukbart chrono-grunnlag.",
            "evidence_quality_title": "Usable evidence quality",
            "evidence_quality_message": "Measured data and robustness point in a reasonably similar direction.",
            "evidence_quality_level": "medium",
            "evidence_quality_checks": ["Readiness: High confidence"],
            "calibration_title": "Kalibreringsprofilen ser brukbar ut",
            "calibration_message": "Pipe/løp-læring og komponentdata peker i samme retning.",
            "calibration_level": "ok",
            "calibration_score": "78",
            "calibration_checks": ["Cold-bore drift er låst mot 4 serier."],
            "internal_ballistics_title": "Internal Ballistics",
            "internal_ballistics_message": "Fyllrate 97.0%, kompresjon 1.02x.",
            "internal_ballistics_level": "ok",
            "internal_ballistics_metrics": [
                {"name": "Fyllrate", "value": "97.0%"},
                {"name": "Kompresjon", "value": "1.02x"},
            ],
            "internal_ballistics_case_context": [
                "H2O basis: 53.80 gr from the selected case (4 source points).",
                "Trim length 48.77 mm from the selected case is available in the workflow context.",
            ],
            "internal_ballistics_checks": [
                "Fill ratio sits in a healthy working window."
            ],
            "environment_title": "Environment",
            "environment_message": "Temp 12.0 C, pressure 1002.0 hPa, RH 71%, DA approx. 245 m.",
            "environment_checks": [
                "Environment basis: measured",
                "Density ratio: 0.984",
            ],
            "pressure_notes": ["Lett flattening i primer på siste serie."],
            "uncertainty_summary": [
                "Readiness: Readiness bygger på godt datagrunnlag.",
                "Robustness: Robustness can still move a bit after the next control series.",
                "Impact: Impact-vurderingen bygger på brukbart chrono-grunnlag.",
            ],
            "report_plot_x": ["2026-03-01", "2026-03-05"],
            "report_plot_y": [812.0, 818.5],
            "report_plot_xlabel": "Serie",
            "report_plot_ylabel": "Hastighet (fps)",
            "chronograph_summary": [
                "2026-03-01: 812 fps, ES 24, SD 8.1",
                "2026-03-05: 818 fps, ES 18, SD 6.4",
            ],
            "shooting_summary": ["2026-03-06: gruppe 14.2 mm, 5 skudd"],
            "accuracy_test_summary": ["2026-03-07, avg 16.4 mm, best 12.8 mm, 817 fps"],
        }
    )

    payload = MainWindow._build_workflow_report_export_payload(widget)

    assert payload["workflow_name"] == "WF-1"
    assert payload["impact_window"]["drag_model"] == "G7"
    assert payload["impact_window"]["bc_segment"] == "G7 0.245 @ 2600-3000 fps"
    assert payload["internal_ballistics"]["message"].startswith("Fyllrate 97.0%")
    assert payload["internal_ballistics"]["metrics"] == [
        {"name": "Fyllrate", "value": "97.0%"},
        {"name": "Kompresjon", "value": "1.02x"},
    ]
    assert payload["internal_ballistics"]["case_context"] == [
        "H2O basis: 53.80 gr from the selected case (4 source points).",
        "Trim length 48.77 mm from the selected case is available in the workflow context.",
    ]
    assert payload["environment"]["checks"] == [
        "Environment basis: measured",
        "Density ratio: 0.984",
    ]
    assert payload["uncertainty"]["checks"] == [
        "Readiness: Readiness bygger på godt datagrunnlag.",
        "Robustness: Robustness can still move a bit after the next control series.",
        "Impact: Impact-vurderingen bygger på brukbart chrono-grunnlag.",
    ]
    assert payload["pressure_notes"] == ["Lett flattening i primer på siste serie."]
    assert payload["measured_series"]["chronograph"] == [
        "2026-03-01: 812 fps, ES 24, SD 8.1",
        "2026-03-05: 818 fps, ES 18, SD 6.4",
    ]
    assert payload["measured_series"]["shooting"] == [
        "2026-03-06: gruppe 14.2 mm, 5 skudd"
    ]
    assert payload["measured_series"]["accuracy_tests"] == [
        "2026-03-07, avg 16.4 mm, best 12.8 mm, 817 fps"
    ]
    assert payload["report_plot"]["y"] == [812.0, 818.5]
    assert any(
        row["section"] == "Internal Ballistics" for row in payload["summary_rows"]
    )


def test_build_workflow_pdf_report_bytes_uses_generator_output():
    captured: dict[str, object] = {}

    class _ReportModule:
        @staticmethod
        def generate_pdf_report(data, pdf_path):
            captured["data"] = data
            with open(pdf_path, "wb") as fh:
                fh.write(b"%PDF-FAKE")

    widget = SimpleNamespace(
        _build_workflow_pdf_report_data=lambda: {
            "title": "Workflow Report - WF-1",
            "stats": {"workflow": "WF-1"},
            "sections": {},
            "x": ["Serie 1"],
            "y": [820.0],
            "x_label": "Serie",
            "y_label": "Hastighet (fps)",
        }
    )

    original_import_module = main_window_module.importlib.import_module
    main_window_module.importlib.import_module = lambda name: _ReportModule
    try:
        pdf_bytes = MainWindow._build_workflow_pdf_report_bytes(widget)
    finally:
        main_window_module.importlib.import_module = original_import_module

    assert pdf_bytes == b"%PDF-FAKE"
    assert captured["data"]["title"] == "Workflow Report - WF-1"


def test_ready_workflow_with_low_robustness_prefers_conservative_verification():
    calls: list[tuple[int, str]] = []
    widget = SimpleNamespace(
        _get_active_workflow_status=lambda: {
            "level": "ready",
            "robustness_level": "critical",
            "robustness_score": "42",
        },
        _get_workspace_snapshot=lambda: {"latest_project_batch_id": 17},
        _open_target_analyzer_for_pressure_review=lambda: None,
        _open_project_batch_by_id=lambda batch_id, message: calls.append(
            (batch_id, message)
        ),
        _open_batch_for_workflow_next_step=lambda batch_id, message: None,
        _continue_latest_project_batch=lambda: None,
        _open_chronograph_for_workflow_data_capture=lambda: None,
    )

    label, handler = MainWindow._get_workflow_action_recommendation(widget)

    assert label == "Verify the latest batch with chronograph first"
    handler()
    assert calls == [
        (
            17,
            "Opened the latest project batch for conservative lot/robustness verification",
        )
    ]


def test_ready_workflow_with_warning_robustness_prefers_control_series():
    calls: list[tuple[int, str]] = []
    widget = SimpleNamespace(
        _get_active_workflow_status=lambda: {
            "level": "ready",
            "robustness_level": "warning",
            "robustness_score": "64",
        },
        _get_workspace_snapshot=lambda: {"latest_project_batch_id": 9},
        _open_target_analyzer_for_pressure_review=lambda: None,
        _open_project_batch_by_id=lambda batch_id, message: None,
        _open_batch_for_workflow_next_step=lambda batch_id, message: calls.append(
            (batch_id, message)
        ),
        _continue_latest_project_batch=lambda: None,
        _open_chronograph_for_workflow_data_capture=lambda: None,
    )

    label, handler = MainWindow._get_workflow_action_recommendation(widget)

    assert label == "Open the latest project batch for a control series"
    handler()
    assert calls == [
        (
            9,
            "Opened the latest project batch for a control series before the next step",
        )
    ]


def test_ready_hunting_workflow_prefers_cold_bore_verification():
    calls: list[tuple[int, str]] = []
    widget = SimpleNamespace(
        _get_active_workflow_status=lambda: {
            "level": "ready",
            "usage_profile": "hunting_medium",
            "robustness_level": "ok",
            "robustness_score": "82",
        },
        _get_workspace_snapshot=lambda: {"latest_project_batch_id": 12},
        _open_target_analyzer_for_pressure_review=lambda: None,
        _open_project_batch_by_id=lambda batch_id, message: None,
        _open_batch_for_workflow_next_step=lambda batch_id, message: calls.append(
            (batch_id, message)
        ),
        _continue_latest_project_batch=lambda: None,
        _open_chronograph_for_workflow_data_capture=lambda: None,
    )

    label, handler = MainWindow._get_workflow_action_recommendation(widget)

    assert label == "Open the latest project batch for cold-bore/hunting verification"
    handler()
    assert calls == [
        (
            12,
            "Opened the latest project batch for cold-bore and hunting verification",
        )
    ]


def test_ready_training_workflow_prefers_robust_control_series():
    calls: list[tuple[int, str]] = []
    widget = SimpleNamespace(
        _get_active_workflow_status=lambda: {
            "level": "ready",
            "usage_profile": "training",
            "robustness_level": "ok",
            "robustness_score": "79",
        },
        _get_workspace_snapshot=lambda: {"latest_project_batch_id": 21},
        _open_target_analyzer_for_pressure_review=lambda: None,
        _open_project_batch_by_id=lambda batch_id, message: None,
        _open_batch_for_workflow_next_step=lambda batch_id, message: calls.append(
            (batch_id, message)
        ),
        _continue_latest_project_batch=lambda: None,
        _open_chronograph_for_workflow_data_capture=lambda: None,
    )

    label, handler = MainWindow._get_workflow_action_recommendation(widget)

    assert label == "Open the latest project batch for a robust control series"
    handler()
    assert calls == [
        (
            21,
            "Opened the latest project batch for a robust control series",
        )
    ]
