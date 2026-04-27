from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(r"c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading")
EXPORT_DIR = REPO_ROOT / ".github" / "data" / "exports"


def preferred_export_path(name: str) -> Path:
    refreshed = EXPORT_DIR / name.replace(".csv", "_refreshed.csv")
    if refreshed.exists():
        return refreshed
    return EXPORT_DIR / name


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def has_value(value: Any) -> bool:
    return value not in (None, "", "null", "None")


def pct(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100.0, 1)


def coverage(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    total = len(rows)
    count = sum(1 for row in rows if has_value(row.get(field)))
    return {
        "field": field,
        "count": count,
        "total": total,
        "coverage_percent": pct(count, total),
    }


def audit_bullets() -> dict[str, Any]:
    rows = read_csv_rows(preferred_export_path("bullets_catalog_master.csv"))
    key_fields = [
        "manufacturer",
        "name",
        "weight_grains",
        "bc_g1",
        "bc_g7",
        "length_mm",
        "diameter_mm",
        "base_type",
        "tip_type",
        "shape_family",
        "construction_type",
        "intended_use",
        "minimum_expansion_fps",
        "preferred_impact_min_fps",
        "preferred_impact_max_fps",
        "terminal_notes",
        "recommended_twist",
    ]
    return {
        "rows": len(rows),
        "critical_fields": {field: coverage(rows, field) for field in key_fields},
    }


def audit_powder() -> dict[str, Any]:
    rows = read_csv_rows(preferred_export_path("powder_catalog_master.csv"))
    key_fields = [
        "manufacturer",
        "name",
        "burn_rate",
        "relative_burn_rate",
        "quickload_ba_value",
        "qex_kj_per_kg",
        "k_ratio",
        "a0",
        "z1",
        "z2",
        "eta_cm3_per_kg",
        "pc_kg_m3",
        "pcd_kg_m3",
        "pt_c",
        "temp_stable",
        "validation_status",
        "usable_for_simulation",
    ]
    return {
        "rows": len(rows),
        "critical_fields": {field: coverage(rows, field) for field in key_fields},
    }


def audit_primers() -> dict[str, Any]:
    rows = read_csv_rows(preferred_export_path("primers_catalog_master.csv"))
    key_fields = [
        "manufacturer",
        "name",
        "type",
        "size",
        "primer_family",
        "match_grade_label",
        "magnum_label",
        "ignition_strength_class",
        "pressure_tolerance_class",
        "cup_hardness_class",
        "recommended_pressure_min_psi",
        "recommended_pressure_max_psi",
        "cold_weather_suitability",
    ]
    return {
        "rows": len(rows),
        "critical_fields": {field: coverage(rows, field) for field in key_fields},
    }


def audit_cases() -> dict[str, Any]:
    rows = read_csv_rows(preferred_export_path("cases_catalog_master.csv"))
    profile_baselines = read_csv_rows(EXPORT_DIR / "case_baselines_from_profiles.csv")
    key_fields = [
        "manufacturer",
        "name",
        "caliber",
        "material",
        "times_fired",
        "last_annealed",
        "needs_annealing_label",
    ]
    return {
        "rows": len(rows),
        "profile_baseline_rows": len(profile_baselines),
        "critical_fields": {field: coverage(rows, field) for field in key_fields},
    }


def build_summary(audit: dict[str, Any]) -> dict[str, Any]:
    rows = int(audit.get("rows") or 0)
    critical_fields = audit.get("critical_fields") or {}
    good = sum(
        1
        for details in critical_fields.values()
        if float(details.get("coverage_percent") or 0.0) >= 80.0
    )
    medium = sum(
        1
        for details in critical_fields.values()
        if 40.0 <= float(details.get("coverage_percent") or 0.0) < 80.0
    )
    weak = sum(
        1
        for details in critical_fields.values()
        if float(details.get("coverage_percent") or 0.0) < 40.0
    )
    return {
        "rows": rows,
        "good_fields": good,
        "medium_fields": medium,
        "weak_fields": weak,
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Komponentdata-audit",
        "",
        "Dette er en nøytral dekningstest av komponentdataene vi nå eier i Hjemmelading.",
        "",
    ]
    for component_name in ("bullets", "powder", "primers", "cases"):
        section = payload.get(component_name) or {}
        summary = build_summary(section)
        lines.append(f"## {component_name}")
        lines.append("")
        lines.append(f"- Rader: `{summary['rows']}`")
        if component_name == "cases":
            lines.append(
                f"- Pipebaselines fra våpenprofiler: `{int(section.get('profile_baseline_rows') or 0)}`"
            )
        lines.append(f"- Sterke felt (>=80%): `{summary['good_fields']}`")
        lines.append(f"- Middels felt (40-79%): `{summary['medium_fields']}`")
        lines.append(f"- Svake felt (<40%): `{summary['weak_fields']}`")
        lines.append("")
        lines.append("| Felt | Dekning |")
        lines.append("| --- | ---: |")
        for field, details in (section.get("critical_fields") or {}).items():
            lines.append(f"| `{field}` | `{details['coverage_percent']:.1f}%` |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = {
        "bullets": audit_bullets(),
        "powder": audit_powder(),
        "primers": audit_primers(),
        "cases": audit_cases(),
    }

    json_path = EXPORT_DIR / "component_data_audit.json"
    md_path = EXPORT_DIR / "component_data_audit.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(build_markdown(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "json": str(json_path),
                "md": str(md_path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
