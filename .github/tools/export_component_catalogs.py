from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.database.database import Database

DB_PATH = REPO_ROOT / "data" / "reloading.db"
EXPORT_DIR = REPO_ROOT / ".github" / "data" / "exports"


def normalize_bool(value: Any) -> str:
    if value in (1, True, "1", "true", "True", "yes", "Yes"):
        return "ja"
    if value in (0, False, "0", "false", "False", "no", "No"):
        return "nei"
    return ""


def _contains_any(text: str, *needles: str) -> bool:
    haystack = f" {str(text or '').strip().lower()} "
    return any(needle.strip().lower() in haystack for needle in needles if needle)


def _normalize_text_token(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def infer_primer_fields(row: dict[str, Any]) -> dict[str, Any]:
    manufacturer = str(row.get("manufacturer") or "").strip()
    name = str(row.get("name") or "").strip()
    primer_type = str(row.get("type") or "").strip()
    size = str(row.get("size") or "").strip()
    notes = str(row.get("notes") or "").strip()
    combined = " ".join(bit for bit in [manufacturer, name, primer_type, size, notes] if bit)
    lowered = _normalize_text_token(combined)

    size_lower = _normalize_text_token(size)

    family = row.get("primer_family")
    if not family:
        if "small rifle" in size_lower:
            family = "small_rifle"
        elif "large rifle" in size_lower:
            family = "large_rifle"
        elif "small pistol" in size_lower:
            family = "small_pistol"
        elif "large pistol" in size_lower:
            family = "large_pistol"
        elif "209" in lowered or "shotshell" in lowered:
            family = "shotshell_209"

        if family:
            if _contains_any(lowered, " benchrest", " br-", "br "):
                family = f"{family}_benchrest"
            elif _contains_any(lowered, " match", "gold medal", " gm "):
                family = f"{family}_match"
            elif _contains_any(lowered, " magnum", "450", "250", "215", "205m ar", "41"):
                family = f"{family}_magnum"
            elif _contains_any(lowered, " ar ", "military", "#41", "41 "):
                family = f"{family}_military"

    ignition = row.get("ignition_strength_class")
    if not ignition:
        if _contains_any(lowered, " magnum", "450", "250", "215", "41"):
            ignition = "magnum"
        elif _contains_any(lowered, " benchrest", " br-", "gold medal", "match"):
            ignition = "standard_plus"
        elif family and "pistol" in family:
            ignition = "standard"
        elif family:
            ignition = "standard"

    pressure = row.get("pressure_tolerance_class")
    if not pressure:
        if _contains_any(lowered, " ar ", "military", "41", "450", " magnum"):
            pressure = "high"
        elif _contains_any(lowered, " benchrest", " match", "gold medal"):
            pressure = "medium_high"
        elif family:
            pressure = "standard"

    hardness = row.get("cup_hardness_class")
    if not hardness:
        if _contains_any(lowered, " ar ", "military", "41", "450", " magnum"):
            hardness = "hard"
        elif _contains_any(lowered, " benchrest", " br-", " match", "gold medal"):
            hardness = "medium_hard"
        elif family:
            hardness = "medium"

    pressure_min = row.get("recommended_pressure_min_psi")
    pressure_max = row.get("recommended_pressure_max_psi")
    if not pressure_min and family:
        if "large_rifle" in family:
            pressure_min = 42000.0
        elif "small_rifle" in family:
            pressure_min = 38000.0
    if not pressure_max and family:
        if _contains_any(lowered, " ar ", "military", "41", "450", " magnum"):
            pressure_max = 65000.0
        elif "large_rifle" in family:
            pressure_max = 62000.0
        elif "small_rifle" in family:
            pressure_max = 62000.0

    cold_weather = row.get("cold_weather_suitability")
    if not cold_weather:
        if _contains_any(lowered, " magnum", "215", "250", "450"):
            cold_weather = "good"
        elif _contains_any(lowered, " benchrest", " match", "gold medal"):
            cold_weather = "moderate"
        elif family:
            cold_weather = "standard"

    return {
        "primer_family": family,
        "ignition_strength_class": ignition,
        "pressure_tolerance_class": pressure,
        "cup_hardness_class": hardness,
        "recommended_pressure_min_psi": pressure_min,
        "recommended_pressure_max_psi": pressure_max,
        "cold_weather_suitability": cold_weather,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def export_primers(conn: sqlite3.Connection, export_dir: Path) -> dict[str, Any]:
    try:
        rows = [dict(row) for row in conn.execute("SELECT * FROM primers ORDER BY manufacturer, name, id").fetchall()]
    except sqlite3.OperationalError:
        rows = []
    enriched: list[dict[str, Any]] = []
    for row in rows:
        inferred = infer_primer_fields(row)
        primer_flags = []
        if normalize_bool(row.get("match_grade")) == "ja":
            primer_flags.append("match")
        if normalize_bool(row.get("magnum")) == "ja":
            primer_flags.append("magnum")
        if normalize_bool(row.get("ar_variant")) == "ja":
            primer_flags.append("AR")
        if normalize_bool(row.get("lead_free")) == "ja":
            primer_flags.append("blyfri")
        enriched.append(
            {
                **row,
                **inferred,
                "display_name": " ".join(
                    bit
                    for bit in [
                        str(row.get("manufacturer") or "").strip(),
                        str(row.get("name") or "").strip(),
                    ]
                    if bit
                ).strip(),
                "match_grade_label": normalize_bool(row.get("match_grade")),
                "magnum_label": normalize_bool(row.get("magnum")),
                "ar_variant_label": normalize_bool(row.get("ar_variant")),
                "non_corrosive_label": normalize_bool(row.get("non_corrosive")),
                "lead_free_label": normalize_bool(row.get("lead_free")),
                "primer_flags": ", ".join(primer_flags),
            }
        )

    tidy_fields = [
        "id",
        "display_name",
        "manufacturer",
        "name",
        "type",
        "size",
        "primer_family",
        "product_line",
        "part_number",
        "match_grade_label",
        "magnum_label",
        "ar_variant_label",
        "non_corrosive_label",
        "lead_free_label",
        "ignition_strength_class",
        "pressure_tolerance_class",
        "cup_hardness_class",
        "cup_thickness_in",
        "recommended_pressure_min_psi",
        "recommended_pressure_max_psi",
        "cold_weather_suitability",
        "temperature_claim",
        "nominal_diameter_in",
        "composition_class",
        "used_for",
        "primer_flags",
        "evidence_level",
        "reference_source",
        "notes",
        "quantity",
        "box_count",
        "case_count",
    ]
    master_fields = (
        list(enriched[0].keys()) if enriched else ["id", "display_name", "manufacturer", "name", "type", "size"]
    )

    tidy_path = export_dir / "primers_catalog_tidy.csv"
    master_path = export_dir / "primers_catalog_master.csv"
    write_csv(tidy_path, enriched, tidy_fields)
    write_csv(master_path, enriched, master_fields)
    return {"rows": len(enriched), "tidy": str(tidy_path), "master": str(master_path)}


def export_cases(conn: sqlite3.Connection, export_dir: Path) -> dict[str, Any]:
    try:
        rows = [
            dict(row) for row in conn.execute("SELECT * FROM cases ORDER BY manufacturer, caliber, name, id").fetchall()
        ]
    except sqlite3.OperationalError:
        rows = []
    enriched: list[dict[str, Any]] = []
    for row in rows:
        enriched.append(
            {
                **row,
                "display_name": " ".join(
                    bit
                    for bit in [
                        str(row.get("manufacturer") or "").strip(),
                        str(row.get("name") or "").strip(),
                        str(row.get("caliber") or "").strip(),
                    ]
                    if bit
                ).strip(),
                "needs_annealing_label": normalize_bool(row.get("needs_annealing")),
            }
        )

    tidy_fields = [
        "id",
        "display_name",
        "manufacturer",
        "name",
        "caliber",
        "material",
        "quantity",
        "times_fired",
        "last_annealed",
        "needs_annealing_label",
        "notes",
    ]
    master_fields = (
        list(enriched[0].keys()) if enriched else ["id", "display_name", "manufacturer", "name", "caliber", "material"]
    )

    tidy_path = export_dir / "cases_catalog_tidy.csv"
    master_path = export_dir / "cases_catalog_master.csv"
    write_csv(tidy_path, enriched, tidy_fields)
    write_csv(master_path, enriched, master_fields)
    return {"rows": len(enriched), "tidy": str(tidy_path), "master": str(master_path)}


def export_manifest(results: dict[str, dict[str, Any]], db_path: Path, export_dir: Path) -> str:
    manifest_path = export_dir / "components_catalog_manifest.json"
    payload = {
        "generated_from": str(db_path),
        "exports": results,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(manifest_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--export-dir", type=Path, default=EXPORT_DIR)
    args = parser.parse_args()

    args.export_dir.mkdir(parents=True, exist_ok=True)
    try:
        bootstrap_db = Database(str(args.db_path))
        bootstrap_db.close()
    except Exception as _exc:
        print(f"[export] DB bootstrap warning (continuing): {_exc}", file=sys.stderr)
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        results = {
            "primers": export_primers(conn, args.export_dir),
            "cases": export_cases(conn, args.export_dir),
        }
    finally:
        conn.close()

    manifest = export_manifest(results, args.db_path, args.export_dir)
    print(json.dumps({"exports": results, "manifest": manifest}, ensure_ascii=False))


if __name__ == "__main__":
    main()
