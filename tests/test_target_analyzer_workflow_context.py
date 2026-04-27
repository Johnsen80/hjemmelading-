from src.modules import target_analyzer


def test_build_target_analysis_summary_includes_workflow_marker():
    summary = target_analyzer.build_target_analysis_summary(
        {
            "max_spread_mm": 18.4,
            "moa": 0.63,
            "shot_count": 5,
        },
        {
            "workflow_id": 12,
            "workflow_name": "OCW Test",
        },
    )

    assert "Target Analyzer" in summary
    assert "[workflow:12]" in summary
    assert "OCW Test" in summary


def test_get_active_workflow_context_includes_load_session_id(monkeypatch):
    class _FakeSettings:
        def value(self, key, default=None):
            mapping = {
                "workflow_context/workflow_id": "12",
                "workflow_context/workflow_name": "OCW Test",
                "workflow_context/load_session_id": "33",
                "workflow_context/rifle_id": "4",
                "workflow_context/barrel_id": "B1",
                "workflow_context/barrel_name": 'Proof 24"',
                "workflow_context/created_date": "2026-03-20",
            }
            return mapping.get(key, default)

    monkeypatch.setattr(
        target_analyzer, "QSettings", lambda *args, **kwargs: _FakeSettings()
    )

    context = target_analyzer._get_active_workflow_context()

    assert context["workflow_id"] == 12
    assert context["load_session_id"] == 33


def test_build_target_analysis_summary_without_workflow_context():
    summary = target_analyzer.build_target_analysis_summary(
        {
            "max_spread_mm": 12.0,
            "moa": 0.41,
            "shot_count": 3,
        }
    )

    assert "12.0 mm" in summary
    assert "[workflow:" not in summary


def test_build_target_quality_summary_marks_ready_for_strong_group():
    summary = target_analyzer.build_target_quality_summary(
        {
            "shot_count": 5,
            "max_spread_mm": 18.0,
            "moa": 0.62,
        }
    )

    assert summary["level"] == "ready"
    assert "Strong group" in summary["title"]


def test_build_target_quality_summary_marks_watch_for_large_group():
    summary = target_analyzer.build_target_quality_summary(
        {
            "shot_count": 5,
            "max_spread_mm": 52.0,
            "moa": 1.8,
        }
    )

    assert summary["level"] == "watch"
    assert "relatively large" in summary["message"]


def test_build_target_quality_summary_marks_needs_more_data_for_short_group():
    summary = target_analyzer.build_target_quality_summary(
        {
            "shot_count": 2,
            "max_spread_mm": 10.0,
            "moa": 0.34,
        }
    )

    assert summary["level"] == "needs_more_data"
    assert "Three or more shots" in summary["message"]


def test_build_target_evidence_basis_labels_measured_modeled_and_recommended():
    summary = target_analyzer.build_target_evidence_basis(
        {
            "shot_count": 5,
            "max_spread_mm": 18.0,
            "moa": 0.62,
            "distance_m": 100,
        }
    )

    assert summary["title"] == "Evidence basis"
    assert "Measured:" in summary["message"]
    assert "Modeled:" in summary["message"]
    assert "Recommended:" in summary["message"]


def test_format_group_size_mm_uses_imperial_when_global_units_are_imperial(monkeypatch):
    monkeypatch.setattr(target_analyzer, "_get_global_unit_system", lambda: "imperial")

    formatted = target_analyzer._format_group_size_mm(25.4)

    assert "in" in formatted
    assert "mm" in formatted


def test_format_offset_mm_uses_imperial_when_global_units_are_imperial(monkeypatch):
    monkeypatch.setattr(target_analyzer, "_get_global_unit_system", lambda: "imperial")

    formatted = target_analyzer._format_offset_mm(25.4)

    assert "in" in formatted
    assert "mm" in formatted
