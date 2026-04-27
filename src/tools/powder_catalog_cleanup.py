from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


LEGACY_MEMORY_DUMP_LABEL = "Gordon memory dump"
NEUTRAL_MEMORY_DUMP_LABEL = "Reference memory dump"
LEGACY_MEMORY_DUMP_REF = "gordon_memory_dump"
NEUTRAL_MEMORY_DUMP_REF = "reference_memory_dump"


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_source_label(value: Any) -> str:
    normalized = _normalize_text(value)
    if normalized.casefold() == LEGACY_MEMORY_DUMP_LABEL.casefold():
        return NEUTRAL_MEMORY_DUMP_LABEL
    return normalized


def _display_name(
    manufacturer: str,
    name: str,
    display_name: Any,
    *,
    original_manufacturer: Any = None,
    original_name: Any = None,
) -> str:
    normalized_display_name = _normalize_text(display_name)
    original_composed_name = " ".join(
        part
        for part in (
            _normalize_text(original_manufacturer),
            _normalize_text(original_name),
        )
        if part
    ).strip()
    canonical_composed_name = " ".join(
        part for part in (manufacturer, name) if part
    ).strip()
    if not normalized_display_name:
        return canonical_composed_name
    if (
        original_composed_name
        and normalized_display_name.casefold() == original_composed_name.casefold()
    ):
        return canonical_composed_name
    return normalized_display_name


def _variant_rank(value: str, count: int) -> tuple[int, int, int, str]:
    parts = [part for part in re.split(r"[\s/]+", value) if part]
    looks_titled = int(
        any(part.isupper() for part in parts)
        or all(part[:1].isupper() for part in parts if any(ch.isalpha() for ch in part))
    )
    uppercase_letters = sum(1 for ch in value if ch.isupper())
    return (count, looks_titled, -uppercase_letters, value)


def build_manufacturer_canonical_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    variants: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        normalized = _normalize_text(row.get("manufacturer"))
        if normalized:
            variants[normalized.lower()][normalized] += 1

    canonical: dict[str, str] = {}
    for key, counter in variants.items():
        canonical[key] = max(
            counter.items(), key=lambda item: _variant_rank(item[0], item[1])
        )[0]
    return canonical


def _normalize_external_ref(external_ref: Any, manufacturer: str, name: str) -> str:
    normalized_ref = _normalize_text(external_ref)
    if not normalized_ref:
        return ""
    parts = normalized_ref.split("|")
    if len(parts) >= 4 and parts[1].lower() == "powder":
        if parts[0].strip().lower() == LEGACY_MEMORY_DUMP_REF:
            parts[0] = NEUTRAL_MEMORY_DUMP_REF
        parts[2] = manufacturer
        parts[3] = name
        return "|".join(parts)
    return normalized_ref


def _normalize_raw_json(raw_json: Any, manufacturer: str, name: str) -> str:
    text = str(raw_json or "").strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except Exception:
        return text
    if not isinstance(payload, dict):
        return text
    if "mname" in payload:
        payload["mname"] = manufacturer
    if "pname" in payload:
        payload["pname"] = name
    return json.dumps(payload, ensure_ascii=False)


def clean_powder_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    canonical_manufacturers = build_manufacturer_canonical_map(rows)
    cleaned_rows: list[dict[str, Any]] = []
    stats = Counter()

    for row in rows:
        cleaned = dict(row)
        original = dict(row)

        manufacturer = _normalize_text(row.get("manufacturer"))
        manufacturer = canonical_manufacturers.get(manufacturer.lower(), manufacturer)
        name = _normalize_text(row.get("name"))
        display_name = _display_name(
            manufacturer,
            name,
            row.get("display_name"),
            original_manufacturer=row.get("manufacturer"),
            original_name=row.get("name"),
        )
        source_label = _normalize_source_label(row.get("source_label"))

        cleaned["manufacturer"] = manufacturer
        cleaned["name"] = name
        cleaned["display_name"] = display_name
        cleaned["source_label"] = source_label
        cleaned["external_ref"] = _normalize_external_ref(
            row.get("external_ref"), manufacturer, name
        )
        cleaned["raw_json"] = _normalize_raw_json(
            row.get("raw_json"), manufacturer, name
        )

        if _normalize_text(original.get("manufacturer")) != manufacturer:
            stats["manufacturer_normalized"] += 1
        if _normalize_text(original.get("name")) != name:
            stats["name_normalized"] += 1
        if not _normalize_text(original.get("display_name")) and display_name:
            stats["display_name_filled"] += 1
        elif _normalize_text(original.get("display_name")) != display_name:
            stats["display_name_normalized"] += 1
        if _normalize_text(original.get("source_label")) != source_label:
            stats["source_label_normalized"] += 1
        if _normalize_text(original.get("external_ref")) != cleaned["external_ref"]:
            stats["external_ref_rewritten"] += 1
        if str(original.get("raw_json") or "").strip() != cleaned["raw_json"]:
            stats["raw_json_rewritten"] += 1

        cleaned_rows.append(cleaned)

    stats["rows_total"] = len(rows)
    stats["rows_changed"] = sum(
        1 for row, cleaned in zip(rows, cleaned_rows) if row != cleaned
    )
    stats["blank_display_name_remaining"] = sum(
        1 for row in cleaned_rows if not _normalize_text(row.get("display_name"))
    )
    stats["blank_source_label_remaining"] = sum(
        1 for row in cleaned_rows if not _normalize_text(row.get("source_label"))
    )
    stats["manufacturer_variant_groups_remaining"] = sum(
        1
        for variants in defaultdict(
            set,
            {
                key: {
                    r.get("manufacturer")
                    for r in cleaned_rows
                    if _normalize_text(r.get("manufacturer")).lower() == key
                }
                for key in {
                    _normalize_text(r.get("manufacturer")).lower()
                    for r in cleaned_rows
                    if _normalize_text(r.get("manufacturer"))
                }
            },
        ).values()
        if len(variants) > 1
    )
    return cleaned_rows, dict(stats)


def read_csv_rows(path: Path) -> tuple[list[dict[str, Any]], list[str], str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header_line = handle.readline()
        handle.seek(0)
        delimiter = ";" if header_line.count(";") > header_line.count(",") else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = [dict(row) for row in reader]
        fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames, delimiter


def write_csv_rows(
    path: Path, rows: list[dict[str, Any]], fieldnames: list[str], delimiter: str
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(
    input_path: Path, output_path: Path, stats: dict[str, int]
) -> str:
    return "\n".join(
        [
            "# Powder Catalog Cleanup Report",
            "",
            f"- Input: `{input_path}`",
            f"- Output: `{output_path}`",
            f"- Rows: `{stats.get('rows_total', 0)}`",
            f"- Rows changed: `{stats.get('rows_changed', 0)}`",
            f"- Manufacturer normalized: `{stats.get('manufacturer_normalized', 0)}`",
            f"- Name normalized: `{stats.get('name_normalized', 0)}`",
            f"- Display names filled: `{stats.get('display_name_filled', 0)}`",
            f"- Display names normalized: `{stats.get('display_name_normalized', 0)}`",
            f"- Source labels normalized: `{stats.get('source_label_normalized', 0)}`",
            f"- External refs rewritten: `{stats.get('external_ref_rewritten', 0)}`",
            f"- Raw JSON rewritten: `{stats.get('raw_json_rewritten', 0)}`",
            f"- Blank display names remaining: `{stats.get('blank_display_name_remaining', 0)}`",
            f"- Blank source labels remaining: `{stats.get('blank_source_label_remaining', 0)}`",
            f"- Manufacturer variant groups remaining: `{stats.get('manufacturer_variant_groups_remaining', 0)}`",
            "",
        ]
    )


def clean_powder_catalog(
    input_path: Path,
    output_path: Path,
    *,
    report_json_path: Path | None = None,
    report_md_path: Path | None = None,
) -> dict[str, int]:
    rows, fieldnames, delimiter = read_csv_rows(input_path)
    cleaned_rows, stats = clean_powder_rows(rows)
    write_csv_rows(output_path, cleaned_rows, fieldnames, delimiter)
    if report_json_path is not None:
        report_json_path.write_text(
            json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if report_md_path is not None:
        report_md_path.write_text(
            build_markdown_report(input_path, output_path, stats), encoding="utf-8"
        )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    args = parser.parse_args()

    stats = clean_powder_catalog(
        args.input,
        args.output,
        report_json_path=args.report_json,
        report_md_path=args.report_md,
    )
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
