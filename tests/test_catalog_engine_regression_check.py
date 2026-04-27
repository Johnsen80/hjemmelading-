from __future__ import annotations

from pathlib import Path

import pytest

from src.tools.catalog_engine_regression_check import (
    build_markdown_report,
    run_engine_regression_check,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = PROJECT_ROOT / ".github" / "data" / "exports"


@pytest.mark.core
def test_catalog_engine_regression_check_preserves_engine_critical_data():
    report = run_engine_regression_check(EXPORT_ROOT)

    assert report["bullet_core_equal"] is True
    assert report["powder_core_equal"] is True
    assert report["powder_model_core_equal"] is True
    assert report["bullet_core_delta"] == 0
    assert report["powder_core_delta"] == 0
    assert report["powder_model_core_delta"] == 0
    assert report["raw_counts"] == report["clean_counts"]
    assert (
        report["raw_import_report"]["powder_models_usable_for_simulation"]
        == report["clean_import_report"]["powder_models_usable_for_simulation"]
    )


def test_catalog_engine_regression_markdown_report_contains_core_summary():
    report = {
        "bullet_core_equal": True,
        "powder_core_equal": True,
        "powder_model_core_equal": True,
        "bullet_core_delta": 0,
        "powder_core_delta": 0,
        "powder_model_core_delta": 0,
        "raw_counts": {
            "bullets": 1,
            "powders": 2,
            "lots": 3,
            "powder_models": 4,
            "powder_models_usable": 5,
        },
        "clean_counts": {
            "bullets": 1,
            "powders": 2,
            "lots": 3,
            "powder_models": 4,
            "powder_models_usable": 5,
        },
    }

    markdown = build_markdown_report(report)

    assert "Catalog Engine Regression Check" in markdown
    assert "Bullet core equal: `True`" in markdown
    assert "Raw bullets: `1` | Clean bullets: `1`" in markdown
