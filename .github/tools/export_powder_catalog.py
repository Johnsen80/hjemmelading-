from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(r"c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading")
DB_PATH = REPO_ROOT / "data" / "reloading.db"
EXPORT_DIR = REPO_ROOT / ".github" / "data" / "exports"


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def safe_json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def flatten_source(prefix: str, data: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            flattened[f"{prefix}{key}"] = json.dumps(value, ensure_ascii=False)
        else:
            flattened[f"{prefix}{key}"] = value
    return flattened


def collect_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            p.*,
            pd.id AS powder_database_id,
            pd.burn_rate_position,
            pd.relative_burn_rate,
            pd.density_gcc,
            pd.grain_size_mm,
            pd.grain_shape,
            pd.temp_stable,
            pd.temp_coefficient_fps_per_f,
            pd.peak_pressure_timing,
            pd.loading_density_optimal_percent,
            pd.velocity_potential,
            pd.suitable_for_cartridges,
            pd.optimal_bullet_weight_range,
            pd.quickload_available,
            pd.quickload_ba_value,
            pd.quickload_weighting_factor,
            pd.notes AS powder_database_notes,
            pd.data_source AS powder_database_data_source,
            pd.created_date AS powder_database_created_date,
            pd.qex_kj_per_kg,
            pd.k_ratio,
            pd.a0,
            pd.z1,
            pd.z2,
            pd.eta_cm3_per_kg,
            pd.pc_kg_m3,
            pd.pcd_kg_m3,
            pd.pt_c,
            pd.tcc,
            pd.tch,
            pd.validation_status,
            pd.usable_for_simulation,
            pd.source_version AS powder_database_source_version,
            pd.external_ref AS powder_database_external_ref,
            pd.raw_json AS powder_database_raw_json
        FROM powder p
        LEFT JOIN powder_database pd ON pd.powder_id = p.id
        ORDER BY p.manufacturer, p.name, p.id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def derive_row(row: dict[str, Any]) -> dict[str, Any]:
    profile_data = safe_json_dict(row.get("profile_json"))
    raw_data = safe_json_dict(row.get("raw_json"))
    sim_raw_data = safe_json_dict(row.get("powder_database_raw_json"))

    lot_number = str(
        profile_data.get("lot_number") or raw_data.get("lotid") or ""
    ).strip()
    manufacturer = str(row.get("manufacturer") or "").strip()
    name = str(row.get("name") or "").strip()
    display_name = (
        str(row.get("display_name") or "").strip()
        or " ".join(bit for bit in [manufacturer, name] if bit).strip()
    )
    powder_type = str(row.get("type") or raw_data.get("type") or "").strip()
    grain_shape = str(row.get("grain_shape") or "").strip()
    if not grain_shape:
        lowered_type = powder_type.lower()
        if "extrud" in lowered_type:
            grain_shape = "extruded"
        elif "ball" in lowered_type or "spherical" in lowered_type:
            grain_shape = "ball"
        elif "flake" in lowered_type:
            grain_shape = "flake"

    return {
        **row,
        "display_name": display_name,
        "lot_number": lot_number,
        "powder_type_normalized": powder_type or None,
        "grain_shape_normalized": grain_shape or None,
        "source_display": str(
            row.get("source_label") or row.get("source") or ""
        ).strip(),
        "profile_keys": ", ".join(sorted(profile_data.keys())),
        "raw_keys": ", ".join(sorted(raw_data.keys())),
        "simulation_raw_keys": ", ".join(sorted(sim_raw_data.keys())),
        **flatten_source("profile_", profile_data),
        **flatten_source("raw_", raw_data),
        **flatten_source("sim_raw_", sim_raw_data),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter=";", extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        base_rows = collect_rows(conn)
    finally:
        conn.close()

    enriched_rows = [derive_row(row) for row in base_rows]
    all_keys: set[str] = set()
    for row in enriched_rows:
        all_keys.update(row.keys())

    preferred_order = [
        "id",
        "display_name",
        "manufacturer",
        "name",
        "powder_type_normalized",
        "type",
        "grain_shape_normalized",
        "grain_shape",
        "burn_rate",
        "relative_burn_rate",
        "burn_rate_position",
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
        "tcc",
        "tch",
        "density_gcc",
        "grain_size_mm",
        "temp_stable",
        "temp_coefficient_fps_per_f",
        "loading_density_optimal_percent",
        "velocity_potential",
        "optimal_bullet_weight_range",
        "suitable_for_cartridges",
        "quickload_available",
        "quickload_weighting_factor",
        "usable_for_simulation",
        "validation_status",
        "lot_number",
        "source",
        "source_kind",
        "source_label",
        "source_display",
        "source_version",
        "powder_database_data_source",
        "powder_database_source_version",
        "external_id",
        "external_ref",
        "powder_database_external_ref",
        "evidence_level",
        "notes",
        "powder_database_notes",
        "quantity_grams",
        "cost_per_unit",
        "purchase_date",
        "created_date",
        "powder_database_created_date",
        "powder_database_id",
        "profile_keys",
        "raw_keys",
        "simulation_raw_keys",
        "profile_json",
        "raw_json",
        "powder_database_raw_json",
    ]

    remaining = sorted(key for key in all_keys if key not in preferred_order)
    master_fieldnames = [key for key in preferred_order if key in all_keys] + remaining

    tidy_fieldnames = [
        key
        for key in [
            "id",
            "display_name",
            "manufacturer",
            "name",
            "powder_type_normalized",
            "grain_shape_normalized",
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
            "density_gcc",
            "grain_size_mm",
            "temp_stable",
            "temp_coefficient_fps_per_f",
            "loading_density_optimal_percent",
            "velocity_potential",
            "optimal_bullet_weight_range",
            "suitable_for_cartridges",
            "usable_for_simulation",
            "validation_status",
            "lot_number",
            "source_display",
            "evidence_level",
            "notes",
        ]
        if key in all_keys
    ]

    write_csv(
        EXPORT_DIR / "powder_catalog_master.csv", enriched_rows, master_fieldnames
    )
    write_csv(EXPORT_DIR / "powder_catalog_tidy.csv", enriched_rows, tidy_fieldnames)

    print(
        json.dumps(
            {
                "rows": len(enriched_rows),
                "master": str(EXPORT_DIR / "powder_catalog_master.csv"),
                "tidy": str(EXPORT_DIR / "powder_catalog_tidy.csv"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
