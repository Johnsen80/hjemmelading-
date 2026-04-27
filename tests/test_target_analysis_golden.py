import json
from pathlib import Path

import pytest

from src.modules import image_analysis


@pytest.mark.core
def test_golden_target_sample():
    try:
        import cv2  # noqa: F401
    except Exception:
        pytest.skip("OpenCV not installed")

    base = Path(__file__).resolve().parent / "data" / "golden" / "targets"
    expected = json.loads((base / "expected_metrics.json").read_text(encoding="utf-8"))

    for filename, metrics in expected.items():
        result = image_analysis.analyze_group_image(str(base / filename))
        if result.get("error") == "opencv-not-installed":
            pytest.skip("OpenCV not installed")
        assert result.get("error") in (None, "")

        expected_n = metrics.get("n_shots")
        if expected_n is not None:
            assert result["n_shots"] == expected_n

        expected_d = metrics.get("pixel_diameter")
        if expected_d is not None:
            assert result["pixel_diameter"] is not None
            tol = metrics.get("tolerance", 0.6)
            assert abs(result["pixel_diameter"] - expected_d) < tol
