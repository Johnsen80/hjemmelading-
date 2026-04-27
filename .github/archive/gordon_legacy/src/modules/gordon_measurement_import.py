from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from ..database.database import Database

KG_TO_GRAINS = 15432.35835294143
MPS_TO_FPS = 3.28084


@dataclass
class ImportStats:
    grouped_profiles: int = 0
    inserted_profiles: int = 0
    updated_profiles: int = 0
    matched_bullets: int = 0
    matched_powders: int = 0
    missing_bullets: int = 0
    missing_powders: int = 0


def normalize_text(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[#()]+", " ", text)
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def safe_float(value: object) -> float | None:
    try:
        return float(str(value or "").replace(",", ".").strip())
    except Exception:
        return None


def mm_to_caliber_string(value_mm: object) -> str:
    number = safe_float(value_mm)
    if number is None:
        return ""
    caliber = f"{round(number / 25.4, 3):.3f}".rstrip("0").rstrip(".")
    return caliber.lstrip("0")


def is_numeric_caliber(value: object) -> bool:
    return bool(re.match(r"^(?:0|\.)\.\d{3,4}$|^\.\d{3,4}$", str(value or "").strip()))


def normalize_caliber_token(value: object) -> str:
    text = str(value or "").strip()
    if re.match(r"^0\.\d{3,4}$", text):
        return f".{text.split('.', 1)[1]}"
    return text


def kg_to_grains(value_kg: object) -> float | None:
    number = safe_float(value_kg)
    if number is None:
        return None
    return round(number * KG_TO_GRAINS, 2)


def mps_to_fps(value_mps: object) -> float | None:
    number = safe_float(value_mps)
    if number is None:
        return None
    return round(number * MPS_TO_FPS, 1)


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def measurement_group_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("source_file", "").strip(),
        row.get("load_title", "").strip(),
        row.get("charge_value_kg", "").strip(),
    )


def source_lookup_key(row: dict[str, str]) -> tuple[str, str]:
    return (
        row.get("source_file", "").strip(),
        row.get("load_title", "").strip(),
    )


def build_caliber_map(caliber_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for row in caliber_rows:
        reference = row.get("reference", "")
        match = re.search(r"GRT load file:\s*(.+)$", reference)
        if not match:
            continue
        mapping[match.group(1).strip().lower()] = row
    return mapping


def caliber_from_sources(
    load_title: str,
    source_file: str,
    projectile_row: dict[str, str] | None,
    caliber_map: dict[str, dict[str, str]],
) -> str:
    file_name = Path(source_file).name.lower()
    caliber_row = caliber_map.get(file_name)
    if caliber_row and caliber_row.get("name"):
        return caliber_row["name"].strip()

    if projectile_row:
        projectile_caliber = (projectile_row.get("caliber") or "").strip()
        if projectile_caliber:
            return projectile_caliber
        projectile_diameter = projectile_row.get("Dbul") or projectile_row.get("gdia")
        caliber_guess = mm_to_caliber_string(projectile_diameter)
        if caliber_guess:
            return caliber_guess

        manufacturer = (projectile_row.get("mname") or "").strip()
        if manufacturer and manufacturer in load_title:
            return load_title.split(manufacturer, 1)[0].strip(" ,")

    return load_title.strip()


def caliber_from_load_title(load_title: str, bullet_manufacturer: str) -> str:
    manufacturer = (bullet_manufacturer or "").strip()
    if manufacturer and manufacturer in load_title:
        return load_title.split(manufacturer, 1)[0].strip(" ,")
    match = re.search(
        r"^(.*?)\s+[^,]+,\s*[^,]+,\s*0\.\d+,\s*[\d.]+\s+grain\s+.+$", load_title
    )
    if match:
        return match.group(1).strip(" ,")
    return ""


def score_name_match(left: str, right: str) -> int:
    lnorm = normalize_text(left)
    rnorm = normalize_text(right)
    if not lnorm or not rnorm:
        return 0
    if lnorm == rnorm:
        return 6
    if lnorm in rnorm or rnorm in lnorm:
        return 4
    left_words = set(lnorm.split())
    right_words = set(rnorm.split())
    overlap = len(left_words & right_words)
    return overlap


def find_bullet_match(
    bullets: list[dict],
    manufacturer: str,
    caliber: str,
    weight_grains: float | None,
    bullet_name: str,
) -> dict | None:
    manufacturer_norm = normalize_text(manufacturer)
    caliber_norm = normalize_text(caliber)
    best: tuple[int, dict] | None = None
    for bullet in bullets:
        if (
            manufacturer_norm
            and normalize_text(bullet.get("manufacturer")) != manufacturer_norm
        ):
            continue
        if caliber_norm and normalize_text(bullet.get("caliber")) != caliber_norm:
            continue
        bullet_weight = safe_float(bullet.get("weight_grains"))
        if (
            weight_grains is not None
            and bullet_weight is not None
            and abs(bullet_weight - weight_grains) > 1.25
        ):
            continue
        score = score_name_match(bullet_name, str(bullet.get("name") or ""))
        if (
            weight_grains is not None
            and bullet_weight is not None
            and abs(bullet_weight - weight_grains) < 0.11
        ):
            score += 3
        if best is None or score > best[0]:
            best = (score, bullet)
    return best[1] if best and best[0] > 0 else None


def find_powder_match(
    powders: list[dict], manufacturer: str, powder_name: str
) -> dict | None:
    manufacturer_norm = normalize_text(manufacturer)
    best: tuple[int, dict] | None = None
    for powder in powders:
        if (
            manufacturer_norm
            and normalize_text(powder.get("manufacturer")) != manufacturer_norm
        ):
            continue
        score = score_name_match(powder_name, str(powder.get("name") or ""))
        if best is None or score > best[0]:
            best = (score, powder)
    return best[1] if best and best[0] > 0 else None


def build_profile_name(
    caliber: str,
    bullet_manufacturer: str,
    bullet_name: str,
    powder_manufacturer: str,
    powder_name: str,
    charge_grains: float | None,
) -> str:
    charge_text = f"{charge_grains:.2f} gr" if charge_grains is not None else "? gr"
    return (
        f"{caliber} | {bullet_manufacturer} {bullet_name} | "
        f"{powder_manufacturer} {powder_name} | {charge_text}"
    )


def projectile_identity(
    projectile_row: dict[str, str] | None, load_title: str
) -> tuple[str, str, float | None, str]:
    row = projectile_row or {}
    manufacturer = (row.get("mname") or "").strip()
    bullet_name = (row.get("pname") or "").strip()
    numeric_caliber = normalize_caliber_token((row.get("caliber") or "").strip())
    if not is_numeric_caliber(numeric_caliber):
        numeric_caliber = mm_to_caliber_string(row.get("Dbul") or row.get("gdia"))
    weight_grains = safe_float(row.get("gmass"))
    if weight_grains is None:
        weight_grams = safe_float(row.get("mp"))
        if weight_grams is not None:
            weight_grains = round(weight_grams * 15.43235835, 2)

    projectile_name = (row.get("ProjectileName") or "").strip()
    if projectile_name:
        match = re.match(
            r"^\s*([^,]+),\s*([^,]+),\s*(0\.\d+),\s*([\d.]+)\s+grain",
            projectile_name,
        )
        if match:
            manufacturer = manufacturer or match.group(1).strip()
            bullet_name = bullet_name or match.group(2).strip()
            numeric_caliber = numeric_caliber or normalize_caliber_token(match.group(3))
            if weight_grains is None:
                weight_grains = safe_float(match.group(4))

    if (not manufacturer or not bullet_name) and load_title:
        match = re.search(
            r"([^,]+),\s*([^,]+),\s*(0\.\d+),\s*([\d.]+)\s+grain\s+(.+)$",
            load_title,
        )
        if match:
            manufacturer = manufacturer or match.group(1).split()[-1].strip()
            bullet_name = bullet_name or match.group(2).strip()
            numeric_caliber = numeric_caliber or normalize_caliber_token(match.group(3))
            if weight_grains is None:
                weight_grains = safe_float(match.group(4))

    return manufacturer, bullet_name, weight_grains, numeric_caliber


def build_import_rows(
    data_dir: Path,
    db: Database,
) -> tuple[list[dict[str, object]], ImportStats]:
    stats = ImportStats()
    measurement_rows = read_csv_rows(data_dir / "gordon_extracted_measurements.csv")
    projectile_rows = read_csv_rows(data_dir / "gordon_extracted_projectiles_raw.csv")
    propellant_rows = read_csv_rows(data_dir / "gordon_extracted_propellants_raw.csv")
    caliber_rows = read_csv_rows(data_dir / "gordon_calibers_reference.csv")

    projectile_map = {
        source_lookup_key(row): row for row in projectile_rows if row.get("load_title")
    }
    propellant_map = {
        source_lookup_key(row): row for row in propellant_rows if row.get("load_title")
    }
    caliber_map = build_caliber_map(caliber_rows)

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in measurement_rows:
        grouped[measurement_group_key(row)].append(row)

    bullets = db.get_all("bullets")
    powders = db.get_all("powder")
    rows: list[dict[str, object]] = []
    stats.grouped_profiles = len(grouped)

    for key, group_rows in sorted(grouped.items()):
        source_file, load_title, charge_value_kg = key
        projectile_row = projectile_map.get((source_file, load_title))
        propellant_row = propellant_map.get((source_file, load_title))

        bullet_manufacturer, bullet_name, weight_grains, numeric_caliber = (
            projectile_identity(
                projectile_row,
                load_title,
            )
        )
        powder_manufacturer = (propellant_row or {}).get("mname", "").strip()
        powder_name = (propellant_row or {}).get("pname", "").strip()

        if not bullet_manufacturer or not bullet_name:
            parsed = re.search(
                r"(.+?)\s+([^,]+),\s*([^,]+),\s*0\.\d+,\s*([\d.]+)\s+grain\s+(.+)$",
                load_title,
            )
            if parsed:
                bullet_manufacturer = bullet_manufacturer or parsed.group(2).strip()
                bullet_name = bullet_name or parsed.group(3).strip()
                powder_name = powder_name or parsed.group(5).strip()

        caliber = caliber_from_load_title(
            load_title, bullet_manufacturer
        ) or caliber_from_sources(
            load_title,
            source_file,
            projectile_row,
            caliber_map,
        )
        charge_grains = kg_to_grains(charge_value_kg)

        bullet_match = find_bullet_match(
            bullets,
            bullet_manufacturer,
            numeric_caliber,
            weight_grains,
            bullet_name,
        )
        powder_match = find_powder_match(powders, powder_manufacturer, powder_name)

        if bullet_match:
            stats.matched_bullets += 1
        else:
            stats.missing_bullets += 1
        if powder_match:
            stats.matched_powders += 1
        else:
            stats.missing_powders += 1

        velocities_mps = [safe_float(row.get("velocity_mps")) for row in group_rows]
        velocities_mps = [value for value in velocities_mps if value is not None]
        pressures_bar = [safe_float(row.get("pressure_bar")) for row in group_rows]
        pressures_bar = [value for value in pressures_bar if value is not None]

        avg_velocity_fps = mps_to_fps(average(velocities_mps))
        avg_pressure_bar = round(average(pressures_bar), 1) if pressures_bar else None
        if avg_pressure_bar is not None and avg_pressure_bar <= 0:
            avg_pressure_bar = None
        avg_pressure_psi = (
            round(avg_pressure_bar * 14.5037738, 1)
            if avg_pressure_bar is not None
            else None
        )

        bc_g1 = safe_float((projectile_row or {}).get("g1bc"))
        bc_g7 = safe_float((projectile_row or {}).get("g7bc"))
        if bullet_match:
            bc_g1 = safe_float(bullet_match.get("bc_g1")) or bc_g1
            bc_g7 = safe_float(bullet_match.get("bc_g7")) or bc_g7
            if not weight_grains:
                weight_grains = safe_float(bullet_match.get("weight_grains"))

        profile_name = build_profile_name(
            caliber,
            bullet_manufacturer,
            bullet_name,
            powder_manufacturer,
            powder_name,
            charge_grains,
        )
        context = {
            "source": "gordon_measurement_import",
            "source_file": source_file,
            "load_title": load_title,
            "charge_value_kg": safe_float(charge_value_kg),
            "charge_grains": charge_grains,
            "measurement_title": group_rows[0].get("measurement_title"),
            "shot_count": len(group_rows),
            "shot_indices": [row.get("shot_index") for row in group_rows],
            "avg_velocity_mps": (
                round(average(velocities_mps), 3) if velocities_mps else None
            ),
            "avg_pressure_bar": avg_pressure_bar,
            "projectile_row": projectile_row,
            "propellant_row": propellant_row,
            "caliber_reference": caliber_map.get(Path(source_file).name.lower()),
        }
        rows.append(
            {
                "lookup_name": profile_name,
                "data": {
                    "name": profile_name,
                    "rifle_id": None,
                    "caliber": caliber,
                    "bullet_id": bullet_match.get("id") if bullet_match else None,
                    "bullet_weight": weight_grains or 0,
                    "powder_id": powder_match.get("id") if powder_match else None,
                    "powder_charge": charge_grains or 0,
                    "primer_id": None,
                    "case_id": None,
                    "coal": None,
                    "cbto": None,
                    "velocity_fps": avg_velocity_fps,
                    "bc_g1": bc_g1,
                    "bc_g7": bc_g7,
                    "notes": f"Imported from Gordon measurement series: {Path(source_file).name}",
                    "component_context_json": json.dumps(context, ensure_ascii=False),
                },
                "grt_data": {
                    "predicted_velocity": avg_velocity_fps,
                    "max_pressure_psi": avg_pressure_psi,
                    "max_pressure_bar": avg_pressure_bar,
                    "case_fill_percent": None,
                    "predicted_accuracy_potential": None,
                    "burn_rate_position": None,
                    "optimal_coal": None,
                    "grt_data": json.dumps(context, ensure_ascii=False),
                    "notes": f"Seeded from Gordon measurement import: {Path(source_file).name}",
                },
            }
        )
    return rows, stats


def import_measurement_profiles(
    data_dir: Path,
    db: Database,
    import_grt_seed: bool = False,
) -> tuple[ImportStats, list[dict[str, object]]]:
    rows, stats = build_import_rows(data_dir, db)
    existing_profiles = db.get_all("ammo_profiles")
    for row in rows:
        candidate_context = json.loads(row["data"]["component_context_json"])
        matched_existing = None
        for profile in existing_profiles:
            try:
                existing_context = json.loads(
                    profile.get("component_context_json") or "{}"
                )
            except Exception:
                existing_context = {}
            if existing_context.get("source_file") == candidate_context.get(
                "source_file"
            ) and existing_context.get("charge_grains") == candidate_context.get(
                "charge_grains"
            ):
                matched_existing = profile
                break
        if matched_existing is None:
            existing = db.execute_query(
                "SELECT id FROM ammo_profiles WHERE name = ?", (row["lookup_name"],)
            )
            if existing:
                matched_existing = existing[0]

        if matched_existing:
            profile_id = matched_existing["id"]
            db.update("ammo_profiles", row["data"], "id = ?", (profile_id,))
            stats.updated_profiles += 1
        else:
            profile_id = db.insert("ammo_profiles", row["data"])
            stats.inserted_profiles += 1
            existing_profiles.append({"id": profile_id, **row["data"]})

        if import_grt_seed:
            existing_grt = db.execute_query(
                "SELECT id FROM grt_data WHERE ammo_profile_id = ?",
                (profile_id,),
            )
            grt_record = dict(row["grt_data"])
            grt_record["ammo_profile_id"] = profile_id
            if existing_grt:
                db.update("grt_data", grt_record, "id = ?", (existing_grt[0]["id"],))
            else:
                db.insert("grt_data", grt_record)
    return stats, rows
