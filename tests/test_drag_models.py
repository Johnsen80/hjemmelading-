from src.utils.drag_models import resolve_drag_choice


def test_resolve_drag_choice_prefers_g7_in_auto():
    resolved = resolve_drag_choice(0.462, 0.235, "AUTO")

    assert resolved["resolved_model"] == "G7"
    assert resolved["bc_value"] == 0.235


def test_resolve_drag_choice_falls_back_to_g1_when_g7_missing():
    resolved = resolve_drag_choice(0.462, None, "G7")

    assert resolved["resolved_model"] == "G1"
    assert resolved["bc_value"] == 0.462


def test_resolve_drag_choice_uses_segmented_bc_for_matching_velocity():
    resolved = resolve_drag_choice(
        0.462,
        0.235,
        "AUTO",
        bc_segments=[
            {"velocity_fps_min": 2600, "velocity_fps_max": 3000, "bc_g7": 0.245},
            {"velocity_fps_min": 2000, "velocity_fps_max": 2599, "bc_g7": 0.228},
        ],
        velocity_fps=2710.0,
    )

    assert resolved["resolved_model"] == "G7"
    assert resolved["bc_value"] == 0.245
    assert resolved["source"] == "bc_segments_g7"


def test_resolve_drag_choice_falls_back_to_regular_bc_when_segments_missing():
    resolved = resolve_drag_choice(
        0.462,
        0.235,
        "AUTO",
        bc_segments="not json",
        velocity_fps=2710.0,
    )

    assert resolved["resolved_model"] == "G7"
    assert resolved["bc_value"] == 0.235
