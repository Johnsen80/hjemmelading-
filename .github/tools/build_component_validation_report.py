from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_ROOT = REPO_ROOT / ".github" / "data" / "component_knowledge_base"
OUTPUT_JSON = KB_ROOT / "validation_report.json"
OUTPUT_MD = KB_ROOT / "validation_report.md"


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_json(value: Any) -> dict[str, Any]:
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _float(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _classify_caliber_source(row: dict[str, Any]) -> tuple[str, str]:
    raw = _parse_json(row.get("raw_json"))
    standard = str(
        raw.get("standard") or raw.get("method") or row.get("standard") or ""
    ).upper()
    origin = str(raw.get("origin") or "").lower()
    has_cip_pdf = bool(str(raw.get("cippdf") or "").strip())
    if "CIP" in standard and (has_cip_pdf or "cip-bobp.org" in origin):
        return "official_cip", "official_standard"
    if "SAAMI" in standard:
        return "official_saami", "official_standard"
    if "USER" in standard:
        return "user_measurement", "user_reference"
    return "grt_reference", "imported_reference"


def build_report() -> dict[str, Any]:
    bullets = _read_csv(KB_ROOT / "bullets.csv")
    powders = _read_csv(KB_ROOT / "powders.csv")
    calibers = _read_csv(KB_ROOT / "calibers.csv")

    bullet_sources = Counter()
    bullet_missing_bc = 0
    bullet_zero_bc = 0
    for row in bullets:
        label = str(row.get("source_label") or "")
        if label.startswith("component_xml:"):
            bullet_sources["component_xml"] += 1
        elif label.startswith("grtload:"):
            bullet_sources["grtload"] += 1
        else:
            bullet_sources["other"] += 1
        g1 = _float(row.get("bc_g1"))
        g7 = _float(row.get("bc_g7"))
        if g1 is None and g7 is None:
            bullet_missing_bc += 1
        elif (g1 or 0.0) == 0.0 and (g7 or 0.0) == 0.0:
            bullet_zero_bc += 1

    powder_sources = Counter()
    powder_complete_models = 0
    required_powder_fields = ("Ba", "Qex", "k", "a0", "z1", "z2", "eta", "pc", "pcd")
    for row in powders:
        label = str(row.get("source_label") or "")
        if label.startswith("grtload:"):
            powder_sources["grtload"] += 1
        elif label.startswith("component_xml:"):
            powder_sources["component_xml"] += 1
        else:
            powder_sources["other"] += 1
        raw = _parse_json(row.get("raw_json"))
        if all(_float(raw.get(field)) is not None for field in required_powder_fields):
            powder_complete_models += 1

    caliber_source_kinds = Counter()
    caliber_evidence = Counter()
    caliber_with_pdf = 0
    for row in calibers:
        source_kind, evidence_level = _classify_caliber_source(row)
        caliber_source_kinds[source_kind] += 1
        caliber_evidence[evidence_level] += 1
        raw = _parse_json(row.get("raw_json"))
        if str(raw.get("cippdf") or "").strip():
            caliber_with_pdf += 1

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "bullets": len(bullets),
            "powders": len(powders),
            "calibers": len(calibers),
        },
        "bullets": {
            "source_breakdown": dict(bullet_sources),
            "rows_with_missing_bc": bullet_missing_bc,
            "rows_with_zero_bc": bullet_zero_bc,
            "assessment": "Not manufacturer-verified by default; mixed user and GRT snapshot data.",
        },
        "powders": {
            "source_breakdown": dict(powder_sources),
            "rows_with_complete_simulation_fields": powder_complete_models,
            "assessment": "Simulation-capable rows are GRT-derived seeds, not independently manufacturer-verified.",
        },
        "calibers": {
            "source_kind_breakdown": dict(caliber_source_kinds),
            "evidence_breakdown": dict(caliber_evidence),
            "rows_with_drawing_pdf": caliber_with_pdf,
            "assessment": "Primarily CIP/GRT-derived; not a complete SAAMI library.",
        },
    }
    return report


def write_report(report: dict[str, Any]) -> None:
    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md = "\n".join(
        [
            "# Component Validation Report",
            "",
            f"- Bullets: {report['summary']['bullets']}",
            f"- Powders: {report['summary']['powders']}",
            f"- Calibers: {report['summary']['calibers']}",
            "",
            "## Bullets",
            f"- Source breakdown: {report['bullets']['source_breakdown']}",
            f"- Rows with missing BC: {report['bullets']['rows_with_missing_bc']}",
            f"- Rows with zero BC: {report['bullets']['rows_with_zero_bc']}",
            f"- Assessment: {report['bullets']['assessment']}",
            "",
            "## Powders",
            f"- Source breakdown: {report['powders']['source_breakdown']}",
            f"- Rows with complete simulation fields: {report['powders']['rows_with_complete_simulation_fields']}",
            f"- Assessment: {report['powders']['assessment']}",
            "",
            "## Calibers",
            f"- Source kind breakdown: {report['calibers']['source_kind_breakdown']}",
            f"- Evidence breakdown: {report['calibers']['evidence_breakdown']}",
            f"- Rows with drawing PDF: {report['calibers']['rows_with_drawing_pdf']}",
            f"- Assessment: {report['calibers']['assessment']}",
            "",
        ]
    )
    OUTPUT_MD.write_text(md + "\n", encoding="utf-8")


def main() -> None:
    report = build_report()
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
