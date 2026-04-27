from src.modules.load_wizard_pages import _format_bullet_drag_summary


def test_format_bullet_drag_summary_prefers_segmented_bc():
    summary = _format_bullet_drag_summary(
        {
            "bc_g1": 0.462,
            "bc_g7": 0.235,
            "bc_segments_json": '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
        }
    )

    assert "2600-3000 fps" in summary
    assert "0.245" in summary


def test_format_bullet_drag_summary_falls_back_to_g7_g1():
    summary = _format_bullet_drag_summary({"bc_g1": 0.462, "bc_g7": 0.235})

    assert "G7 0.235" in summary
    assert "G1 0.462" in summary
