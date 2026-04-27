from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECHECK_ROOT = REPO_ROOT / ".github" / "tmp" / "gordon_extract_recheck"
OUTPUT_JSON = (
    REPO_ROOT
    / ".github"
    / "data"
    / "component_knowledge_base"
    / "gordon_readable_inventory_report.json"
)
OUTPUT_MD = (
    REPO_ROOT
    / ".github"
    / "data"
    / "component_knowledge_base"
    / "gordon_readable_inventory_report.md"
)


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _safe_float(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def build_report() -> dict[str, Any]:
    projectiles = _read_csv(RECHECK_ROOT / "gordon_extracted_projectiles_raw.csv")
    propellants = _read_csv(RECHECK_ROOT / "gordon_extracted_propellants_raw.csv")
    summary_path = RECHECK_ROOT / "gordon_extraction_summary.json"
    summary = (
        json.loads(summary_path.read_text(encoding="utf-8"))
        if summary_path.exists()
        else {}
    )

    projectile_keys = Counter()
    projectile_variants: dict[str, set[str]] = defaultdict(set)
    for row in projectiles:
        maker = str(row.get("mname") or "").strip()
        name = str(row.get("pname") or row.get("ProjectileName") or "").strip()
        lot = str(row.get("lotid") or "").strip()
        if not maker and not name:
            continue
        key = f"{maker} {name}".strip()
        projectile_keys[key] += 1
        if lot:
            projectile_variants[key].add(lot)

    powder_keys = Counter()
    powder_variants: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in propellants:
        maker = str(row.get("mname") or "").strip()
        name = str(row.get("pname") or "").strip()
        lot = str(row.get("lotid") or "").strip()
        key = f"{maker} {name}".strip()
        if not key:
            continue
        powder_keys[key] += 1
        powder_variants[key].append(
            {
                "lotid": lot or None,
                "Ba": _safe_float(row.get("Ba")),
                "Qex": _safe_float(row.get("Qex")),
                "k": _safe_float(row.get("k")),
                "pt": _safe_float(row.get("pt")),
                "source_file": str(row.get("source_file") or "").strip() or None,
            }
        )

    condensed_powders = {}
    for key, variants in powder_variants.items():
        seen = []
        unique_variants = []
        for variant in variants:
            signature = (
                variant.get("lotid"),
                variant.get("Ba"),
                variant.get("Qex"),
                variant.get("k"),
                variant.get("pt"),
            )
            if signature in seen:
                continue
            seen.append(signature)
            unique_variants.append(variant)
        condensed_powders[key] = unique_variants

    report = {
        "summary": summary,
        "raw_readable_counts": {
            "projectiles": len(projectiles),
            "propellants": len(propellants),
        },
        "projectiles": {
            "unique_named_entries": len(projectile_keys),
            "duplicate_snapshot_counts": dict(projectile_keys),
            "lot_breakdown": {
                key: sorted(values) for key, values in projectile_variants.items()
            },
        },
        "powders": {
            "unique_named_entries": len(powder_keys),
            "duplicate_snapshot_counts": dict(powder_keys),
            "distinct_parameter_variants": condensed_powders,
        },
        "assessment": {
            "message": (
                "Readable Gordon sources contain more raw snapshots and some distinct powder parameter variants "
                "than the deduplicated app library currently exposes."
            )
        },
    }
    return report


def write_report(report: dict[str, Any]) -> None:
    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Gordon Readable Inventory Report",
        "",
        f"- Raw projectiles: {report['raw_readable_counts']['projectiles']}",
        f"- Raw propellants: {report['raw_readable_counts']['propellants']}",
        f"- Unique named projectile entries: {report['projectiles']['unique_named_entries']}",
        f"- Unique named powder entries: {report['powders']['unique_named_entries']}",
        "",
        "## Distinct powder parameter variants",
    ]
    for key, variants in report["powders"]["distinct_parameter_variants"].items():
        lines.append(f"- {key}: {len(variants)} distinct variant(s)")
        for variant in variants[:4]:
            lines.append(
                f"  lot={variant.get('lotid')} Ba={variant.get('Ba')} k={variant.get('k')} pt={variant.get('pt')}"
            )
    lines.extend(
        [
            "",
            "## Assessment",
            f"- {report['assessment']['message']}",
            "",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    report = build_report()
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
