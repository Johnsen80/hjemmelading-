from __future__ import annotations

from src.tools.component_catalog_health_report import build_markdown_report


def test_component_catalog_health_markdown_includes_priorities():
    report = {
        "summary": {
            "highest_priority_catalogs": ["cases"],
            "next_cleanup_candidate": "cases",
            "catalogs_ready_for_sync": ["bullets", "powders", "primers"],
            "catalogs_blocking_sync": ["cases"],
        },
        "bullets": {
            "rows": 10,
            "noise_score": 5,
            "priority": "high",
            "effective_priority": "medium",
            "catalog_sync_ready": True,
            "operational_status": "ready_for_sync",
            "blank_display_name": 2,
            "blank_source_label": 2,
            "manufacturer_variant_groups": 1,
            "raw_json_parse_fail": 0,
            "raw_json_name_mismatch": 0,
            "duplicate_key_groups": 1,
            "recommendation": "Clean bullets.",
            "effective_recommendation": "Use clean bullets.",
            "operational_recommendation": "Bullets ready.",
            "clean_artifact_present": True,
            "manufacturer_variant_examples": {"maker": {"Maker": 1, "maker": 1}},
        },
        "powders": {
            "rows": 2,
            "noise_score": 1,
            "priority": "medium",
            "effective_priority": "medium",
            "catalog_sync_ready": True,
            "operational_status": "ready_for_sync",
            "blank_display_name": 0,
            "blank_source_label": 1,
            "manufacturer_variant_groups": 0,
            "raw_json_parse_fail": 0,
            "raw_json_name_mismatch": 0,
            "duplicate_key_groups": 0,
            "recommendation": "Clean powders.",
            "effective_recommendation": "Clean powders.",
            "operational_recommendation": "Powders ready.",
            "clean_artifact_present": True,
            "manufacturer_variant_examples": {},
        },
        "cases": {
            "rows": 0,
            "noise_score": 0,
            "priority": "high",
            "effective_priority": "high",
            "catalog_sync_ready": False,
            "operational_status": "missing_source_data",
            "blank_display_name": 0,
            "blank_source_label": 0,
            "manufacturer_variant_groups": 0,
            "raw_json_parse_fail": 0,
            "raw_json_name_mismatch": 0,
            "duplicate_key_groups": 0,
            "recommendation": "Populate cases.",
            "effective_recommendation": "Populate cases.",
            "operational_recommendation": "Populate cases for sync.",
            "clean_artifact_present": False,
            "manufacturer_variant_examples": {},
        },
        "primers": {
            "rows": 5,
            "noise_score": 0,
            "priority": "low",
            "effective_priority": "low",
            "catalog_sync_ready": True,
            "operational_status": "ready_for_sync",
            "blank_display_name": 0,
            "blank_source_label": 0,
            "manufacturer_variant_groups": 0,
            "raw_json_parse_fail": 0,
            "raw_json_name_mismatch": 0,
            "duplicate_key_groups": 0,
            "recommendation": "Keep stable.",
            "effective_recommendation": "Keep stable.",
            "operational_recommendation": "Keep stable for sync.",
            "clean_artifact_present": False,
            "manufacturer_variant_examples": {},
        },
    }

    markdown = build_markdown_report(report)

    assert "Component Catalog Health Report" in markdown
    assert "Next cleanup candidate: `cases`" in markdown
    assert "Catalogs ready for sync: `bullets, powders, primers`" in markdown
    assert "Catalogs blocking sync: `cases`" in markdown
    assert "## Primers" in markdown
    assert "Catalog sync ready: `True`" in markdown
    assert "Operational status: `missing_source_data`" in markdown
    assert "Recommendation: Populate cases." in markdown
