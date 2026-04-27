from src.modules.batch_analyzer import BatchAnalyzer


def test_batch_analyzer_summary_mentions_setup_label():
    analyzer = BatchAnalyzer(
        {
            "batch_name": "Node A",
            "barrel_name": "26in Match Pipe",
            "barrel_configuration_name": "Suppressed",
        },
        sessions=[{"group_size_mm": 12.5}],
        notes=[],
        attachments=[],
        chronograph_stats={"count": 5, "avg": 2798.0, "es": 18.0, "sd": 7.5},
    )

    summary = analyzer.analyze()

    assert "Setup: 26in Match Pipe / Suppressed." in summary.summary


def test_batch_analyzer_html_mentions_setup_label():
    analyzer = BatchAnalyzer(
        {
            "batch_name": "Node A",
            "barrel_name": "26in Match Pipe",
            "barrel_configuration_name": "Suppressed",
        },
        sessions=[],
        notes=[],
        attachments=[],
        chronograph_stats={},
    )

    html = analyzer.to_html()

    assert "<b>Setup:</b> 26in Match Pipe / Suppressed" in html
