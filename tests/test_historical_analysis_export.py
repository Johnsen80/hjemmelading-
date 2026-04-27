from src.modules import historical_analysis as history_module


def test_build_export_metadata_includes_schema_filters_and_selection_mode():
    meta = history_module._build_export_metadata(
        {
            "caliber": "6.5 Creedmoor",
            "powder": "N160",
            "bullet": "ELD-X",
            "project": "Jakt 2026",
            "date_from": "2026-03-01",
            "date_to": "2026-03-26",
        },
        "filtered",
        "2026-03-26T10:00:00",
    )

    assert meta["schema_version"] == history_module.EXPORT_SCHEMA_VERSION
    assert meta["selection_mode"] == "filtered"
    assert meta["filters"]["project"] == "Jakt 2026"


def test_build_export_payload_wraps_sessions_with_meta_and_audit_fields():
    payload = history_module._build_export_payload(
        [
            {
                "load_id": "CHRONO-12",
                "import_meta": {
                    "source_path": "C:/tmp/chrono.csv",
                    "raw_sha256": "abc123",
                },
            }
        ],
        {
            "caliber": "All",
            "powder": "All",
            "bullet": "All",
            "project": "All",
            "date_from": "2026-03-01",
            "date_to": "2026-03-26",
        },
        "selected",
        "2026-03-26T10:00:00",
    )

    assert payload["meta"]["schema_version"] == history_module.EXPORT_SCHEMA_VERSION
    assert (
        payload["sessions"][0]["export_schema_version"]
        == history_module.EXPORT_SCHEMA_VERSION
    )
    assert payload["sessions"][0]["audit_source_path"] == "C:/tmp/chrono.csv"
    assert payload["sessions"][0]["audit_raw_sha256"] == "abc123"
    assert payload["sessions"][0]["export_selection_mode"] == "selected"
