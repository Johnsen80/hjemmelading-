from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPORT_ROOT = REPO_ROOT / ".github" / "data" / "exports"


def _read_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = handle.readline()
        handle.seek(0)
        reader = csv.DictReader(
            handle, delimiter=";" if header.count(";") > header.count(",") else ","
        )
        rows = [dict(row) for row in reader]
        return rows, list(reader.fieldnames or [])


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _profile_catalog(
    path: Path, *, clean_artifact_path: Path | None = None
) -> dict[str, Any]:
    rows, headers = _read_rows(path)
    manufacturer_variants: dict[str, Counter[str]] = defaultdict(Counter)
    duplicate_keys: Counter[tuple[str, ...]] = Counter()
    blank_display_name = 0
    blank_source_label = 0
    name_whitespace_noise = 0
    manufacturer_whitespace_noise = 0
    raw_json_rows = 0
    raw_json_parse_fail = 0
    raw_json_name_mismatch = 0
    raw_json_manufacturer_mismatch = 0

    for row in rows:
        manufacturer = _normalize_text(row.get("manufacturer"))
        name = _normalize_text(row.get("name"))
        if manufacturer:
            manufacturer_variants[manufacturer.lower()][manufacturer] += 1
        if "display_name" in row and not _normalize_text(row.get("display_name")):
            blank_display_name += 1
        if "source_label" in row and not _normalize_text(row.get("source_label")):
            blank_source_label += 1
        if name != str(row.get("name") or "").strip():
            name_whitespace_noise += 1
        if manufacturer != str(row.get("manufacturer") or "").strip():
            manufacturer_whitespace_noise += 1
        raw_json = str(row.get("raw_json") or "").strip()
        if raw_json:
            raw_json_rows += 1
            try:
                payload = json.loads(raw_json)
            except Exception:
                raw_json_parse_fail += 1
                payload = None
            if isinstance(payload, dict):
                if "pname" in payload and _normalize_text(payload.get("pname")) != name:
                    raw_json_name_mismatch += 1
                if (
                    "mname" in payload
                    and _normalize_text(payload.get("mname")) != manufacturer
                ):
                    raw_json_manufacturer_mismatch += 1

        key_parts = []
        for field in ("manufacturer", "name", "caliber", "size", "type"):
            if field in row:
                key_parts.append(_normalize_text(row.get(field)).lower())
        if key_parts:
            duplicate_keys[tuple(key_parts)] += 1

    noise_score = (
        blank_display_name
        + blank_source_label
        + name_whitespace_noise
        + manufacturer_whitespace_noise
        + raw_json_parse_fail
        + raw_json_name_mismatch
        + raw_json_manufacturer_mismatch
        + sum(1 for counter in manufacturer_variants.values() if len(counter) > 1)
    )

    clean_artifact_present = bool(clean_artifact_path and clean_artifact_path.exists())

    if len(rows) == 0:
        priority = "high"
        recommendation = "Catalog is empty and should be populated before relying on it as a reference source."
    elif noise_score == 0:
        priority = "low"
        recommendation = (
            "Catalog looks stable; keep it under regression monitoring only."
        )
    elif noise_score <= 3:
        priority = "medium"
        recommendation = "Only minor normalization issues remain; a conservative cleanup pass is sufficient."
    else:
        priority = "high"
        recommendation = "Catalog still contains visible data-quality noise and should be cleaned before broader dependence."

    effective_priority = priority
    effective_recommendation = recommendation
    if clean_artifact_present and len(rows) > 0:
        effective_priority = "medium" if priority == "high" else priority
        effective_recommendation = "Raw master still has historical noise, but a clean export already exists and should be treated as the operational source."

    catalog_sync_ready = len(rows) > 0
    if not catalog_sync_ready:
        operational_status = "missing_source_data"
        operational_recommendation = "Catalog sync cannot rely on this source until it contains at least a minimal reference dataset."
    elif effective_priority == "high":
        operational_status = "usable_with_cleanup_needed"
        operational_recommendation = "Catalog is populated and can sync, but data-quality cleanup should happen before broader operational dependence."
    else:
        operational_status = "ready_for_sync"
        operational_recommendation = "Catalog is suitable as an operational sync source under current regression monitoring."

    return {
        "path": str(path),
        "rows": len(rows),
        "headers": len(headers),
        "blank_display_name": blank_display_name,
        "blank_source_label": blank_source_label,
        "name_whitespace_noise": name_whitespace_noise,
        "manufacturer_whitespace_noise": manufacturer_whitespace_noise,
        "manufacturer_variant_groups": sum(
            1 for counter in manufacturer_variants.values() if len(counter) > 1
        ),
        "manufacturer_variant_examples": {
            key: dict(counter)
            for key, counter in list(
                (item for item in manufacturer_variants.items() if len(item[1]) > 1)
            )[:5]
        },
        "raw_json_rows": raw_json_rows,
        "raw_json_parse_fail": raw_json_parse_fail,
        "raw_json_name_mismatch": raw_json_name_mismatch,
        "raw_json_manufacturer_mismatch": raw_json_manufacturer_mismatch,
        "duplicate_key_groups": sum(
            1 for count in duplicate_keys.values() if count > 1
        ),
        "noise_score": noise_score,
        "priority": priority,
        "recommendation": recommendation,
        "clean_artifact_present": clean_artifact_present,
        "effective_priority": effective_priority,
        "effective_recommendation": effective_recommendation,
        "catalog_sync_ready": catalog_sync_ready,
        "operational_status": operational_status,
        "operational_recommendation": operational_recommendation,
    }


def build_health_report(export_root: Path = DEFAULT_EXPORT_ROOT) -> dict[str, Any]:
    catalogs = {
        "bullets": (
            export_root / "bullets_catalog_master.csv",
            export_root / "bullets_catalog_master_clean.csv",
        ),
        "powders": (
            export_root / "powder_catalog_master.csv",
            export_root / "powder_catalog_master_clean.csv",
        ),
        "cases": (export_root / "cases_catalog_master.csv", None),
        "primers": (export_root / "primers_catalog_master.csv", None),
    }
    report = {
        name: _profile_catalog(path, clean_artifact_path=clean_path)
        for name, (path, clean_path) in catalogs.items()
    }
    ordered = sorted(
        report.items(),
        key=lambda item: (
            {"high": 2, "medium": 1, "low": 0}[item[1]["effective_priority"]],
            item[1]["noise_score"],
            item[1]["rows"],
        ),
        reverse=True,
    )
    report["summary"] = {
        "highest_priority_catalogs": [
            name for name, data in ordered if data["effective_priority"] == "high"
        ],
        "next_cleanup_candidate": ordered[0][0] if ordered else None,
        "catalogs_ready_for_sync": [
            name
            for name, data in report.items()
            if name != "summary" and data["catalog_sync_ready"]
        ],
        "catalogs_blocking_sync": [
            name
            for name, data in report.items()
            if name != "summary" and not data["catalog_sync_ready"]
        ],
    }
    return report


def build_markdown_report(report: dict[str, Any]) -> str:
    lines = ["# Component Catalog Health Report", ""]
    summary = report.get("summary", {})
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Next cleanup candidate: `{summary.get('next_cleanup_candidate')}`")
    lines.append(
        f"- High-priority catalogs: `{', '.join(summary.get('highest_priority_catalogs', [])) or 'none'}`"
    )
    lines.append(
        f"- Catalogs ready for sync: `{', '.join(summary.get('catalogs_ready_for_sync', [])) or 'none'}`"
    )
    lines.append(
        f"- Catalogs blocking sync: `{', '.join(summary.get('catalogs_blocking_sync', [])) or 'none'}`"
    )
    lines.append("")

    for name in ("bullets", "powders", "cases", "primers"):
        data = report[name]
        lines.extend(
            [
                f"## {name.title()}",
                "",
                f"- Rows: `{data['rows']}`",
                f"- Noise score: `{data['noise_score']}`",
                f"- Priority: `{data['priority']}`",
                f"- Effective priority: `{data['effective_priority']}`",
                f"- Clean artifact present: `{data['clean_artifact_present']}`",
                f"- Catalog sync ready: `{data['catalog_sync_ready']}`",
                f"- Operational status: `{data['operational_status']}`",
                f"- Blank display_name: `{data['blank_display_name']}`",
                f"- Blank source_label: `{data['blank_source_label']}`",
                f"- Manufacturer variant groups: `{data['manufacturer_variant_groups']}`",
                f"- Raw JSON parse failures: `{data['raw_json_parse_fail']}`",
                f"- Raw JSON name mismatches: `{data['raw_json_name_mismatch']}`",
                f"- Duplicate key groups: `{data['duplicate_key_groups']}`",
                f"- Recommendation: {data['effective_recommendation']}",
                f"- Operational recommendation: {data['operational_recommendation']}",
                "",
            ]
        )
        examples = data.get("manufacturer_variant_examples") or {}
        if examples:
            lines.append("Manufacturer variant examples:")
            for key, variants in examples.items():
                lines.append(f"- `{key}`: `{variants}`")
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    args = parser.parse_args()

    report = build_health_report(args.export_root)
    if args.report_json is not None:
        args.report_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if args.report_md is not None:
        args.report_md.write_text(build_markdown_report(report), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
