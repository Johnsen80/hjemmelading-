from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(r"c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading")
EXPORT_DIR = REPO_ROOT / ".github" / "data" / "exports"
WEAPON_PROFILE_PATH = REPO_ROOT / "data" / "demo_weapons.json"


def safe_float(value: Any) -> float | None:
    try:
        text = str(value or "").strip().replace(",", ".")
        return float(text) if text else None
    except Exception:
        return None


def read_profiles(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter=";", extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def build_rows(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        weapon_id = str(profile.get("id") or "").strip()
        weapon_name = str(profile.get("name") or "").strip()
        caliber = str(profile.get("caliber") or "").strip()
        active_barrel_id = str(profile.get("active_barrel_id") or "").strip()
        for barrel in profile.get("barrels", []) or []:
            barrel_id = str(barrel.get("id") or "").strip()
            case_data = barrel.get("case_measurements") or {}
            samples = case_data.get("h2o_measurements") or []
            h2o_values = [
                safe_float(sample.get("h2o_capacity_grains"))
                for sample in samples
                if isinstance(sample, dict)
            ]
            h2o_values = [value for value in h2o_values if value is not None]
            h2o_capacity = safe_float(case_data.get("h2o_capacity_grains"))
            if h2o_capacity is None and h2o_values:
                h2o_capacity = round(sum(h2o_values) / len(h2o_values), 2)
            h2o_spread = (
                round(max(h2o_values) - min(h2o_values), 2)
                if len(h2o_values) >= 2
                else None
            )

            row = {
                "weapon_id": weapon_id,
                "weapon_name": weapon_name,
                "caliber": caliber,
                "barrel_id": barrel_id,
                "barrel_name": str(barrel.get("name") or "").strip(),
                "active_barrel_label": (
                    "ja" if barrel_id and barrel_id == active_barrel_id else ""
                ),
                "barrel_length_mm": safe_float(barrel.get("length_mm"))
                or safe_float(profile.get("barrel_length_mm")),
                "twist": str(barrel.get("twist") or profile.get("twist") or "").strip(),
                "barrel_profile": str(barrel.get("barrel_profile") or "").strip(),
                "mount_type": str(barrel.get("mount_type") or "").strip(),
                "barrel_attachment_type": str(
                    barrel.get("barrel_attachment_type") or ""
                ).strip(),
                "muzzle_device_type": str(
                    barrel.get("muzzle_device_type") or ""
                ).strip(),
                "muzzle_device_weight_g": safe_float(
                    barrel.get("muzzle_device_weight_g")
                ),
                "case_standard": str(case_data.get("standard") or "").strip(),
                "h2o_capacity_grains": h2o_capacity,
                "h2o_sample_count": len(h2o_values),
                "h2o_spread_grains": h2o_spread,
                "trim_length_mm": safe_float(case_data.get("trim_length_mm")),
                "shoulder_bump_mm": safe_float(case_data.get("shoulder_bump_mm")),
                "base_to_datum_mm": safe_float(case_data.get("base_to_datum_mm")),
                "neck_diameter_mm": safe_float(case_data.get("neck_diameter_mm")),
                "case_notes": str(case_data.get("notes") or "").strip(),
                "baseline_quality": (
                    "strong"
                    if h2o_capacity is not None
                    and len(h2o_values) >= 3
                    and safe_float(case_data.get("neck_diameter_mm")) is not None
                    else (
                        "partial"
                        if any(
                            value is not None
                            for value in (
                                h2o_capacity,
                                safe_float(case_data.get("trim_length_mm")),
                                safe_float(case_data.get("shoulder_bump_mm")),
                                safe_float(case_data.get("base_to_datum_mm")),
                                safe_float(case_data.get("neck_diameter_mm")),
                            )
                        )
                        else "missing"
                    )
                ),
                "source_path": str(WEAPON_PROFILE_PATH),
            }
            rows.append(row)
    return rows


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    strong = sum(1 for row in rows if row.get("baseline_quality") == "strong")
    partial = sum(1 for row in rows if row.get("baseline_quality") == "partial")
    missing = sum(1 for row in rows if row.get("baseline_quality") == "missing")

    lines = [
        "# Hylsebaseline Fra Våpenprofiler",
        "",
        "Dette er et nøytralt utdrag av pipe- og hylsebaseline vi eier gjennom våpenprofilene.",
        "",
        f"- Rader: `{total}`",
        f"- Sterk baseline: `{strong}`",
        f"- Delvis baseline: `{partial}`",
        f"- Mangler baseline: `{missing}`",
        "",
        "| Våpen | Pipe | Kaliber | H2O | H2O-prøver | Trim | Neck | Bump | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('weapon_name') or '-'} | {row.get('barrel_name') or '-'} | {row.get('caliber') or '-'} | "
            f"{row.get('h2o_capacity_grains') or '-'} | {row.get('h2o_sample_count') or 0} | "
            f"{row.get('trim_length_mm') or '-'} | {row.get('neck_diameter_mm') or '-'} | "
            f"{row.get('shoulder_bump_mm') or '-'} | {row.get('baseline_quality') or '-'} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    profiles = read_profiles(WEAPON_PROFILE_PATH)
    rows = build_rows(profiles)
    csv_path = EXPORT_DIR / "case_baselines_from_profiles.csv"
    md_path = EXPORT_DIR / "case_baselines_from_profiles.md"

    fieldnames = [
        "weapon_id",
        "weapon_name",
        "caliber",
        "barrel_id",
        "barrel_name",
        "active_barrel_label",
        "barrel_length_mm",
        "twist",
        "barrel_profile",
        "mount_type",
        "barrel_attachment_type",
        "muzzle_device_type",
        "muzzle_device_weight_g",
        "case_standard",
        "h2o_capacity_grains",
        "h2o_sample_count",
        "h2o_spread_grains",
        "trim_length_mm",
        "shoulder_bump_mm",
        "base_to_datum_mm",
        "neck_diameter_mm",
        "case_notes",
        "baseline_quality",
        "source_path",
    ]
    write_csv(csv_path, rows, fieldnames)
    write_markdown(md_path, rows)

    print(
        json.dumps(
            {"rows": len(rows), "csv": str(csv_path), "md": str(md_path)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
