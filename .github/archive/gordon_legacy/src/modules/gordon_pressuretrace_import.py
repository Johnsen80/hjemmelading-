from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from ..database.database import Database
from .gordon_measurement_import import (
    find_bullet_match,
    find_powder_match,
    kg_to_grains,
    mm_to_caliber_string,
    mps_to_fps,
    safe_float,
)


def decode(value: object) -> str:
    return unquote(str(value or "")).strip()


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def calc_es(values: list[float]) -> float | None:
    if not values:
        return None
    return max(values) - min(values)


def calc_sd(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return variance**0.5


def _section_inputs(root: ET.Element, section_name: str) -> dict[str, str]:
    section = root.find(section_name)
    if section is None:
        return {}
    return {
        item.attrib.get("name", ""): decode(item.attrib.get("value", ""))
        for item in section.findall("input")
    }


def _profile_name(
    caliber: str,
    bullet_manufacturer: str,
    bullet_name: str,
    powder_manufacturer: str,
    powder_name: str,
    charge_grains: float | None,
) -> str:
    charge_text = f"{charge_grains:.2f} gr" if charge_grains is not None else "? gr"
    return f"{caliber} | {bullet_manufacturer} {bullet_name} | {powder_manufacturer} {powder_name} | {charge_text}"


def _source_hash(path: Path, charge_index: int) -> str:
    seed = f"{path.resolve()}::{charge_index}".encode("utf-8", errors="replace")
    return hashlib.sha256(seed).hexdigest()


def _existing_session_for_hash(db: Database, raw_sha256: str) -> dict | None:
    rows = db.execute_query("SELECT * FROM chronograph_sessions")
    for row in rows:
        try:
            meta = json.loads(row.get("import_meta_json") or "{}")
        except Exception:
            meta = {}
        if meta.get("raw_sha256") == raw_sha256:
            return row
    return None


def _match_existing_profile(
    db: Database, source_file: str, charge_grains: float | None, lookup_name: str
) -> dict | None:
    source_key = str(source_file).replace("\\", "/").lower()
    for profile in db.get_all("ammo_profiles"):
        if str(profile.get("name") or "").strip() == lookup_name:
            return profile
        try:
            context = json.loads(profile.get("component_context_json") or "{}")
        except Exception:
            context = {}
        context_key = str(context.get("source_file") or "").replace("\\", "/").lower()
        context_charge = safe_float(
            context.get("charge_grains") or context.get("charge_value_grains")
        )
        if (
            context_key == source_key
            and charge_grains is not None
            and context_charge is not None
            and abs(context_charge - charge_grains) < 0.05
        ):
            return profile
    return None


def _ensure_profile(
    db: Database, payload: dict[str, object]
) -> tuple[dict | None, bool]:
    existing = _match_existing_profile(
        db,
        str(payload.get("source_file") or ""),
        safe_float(payload.get("charge_grains")),
        str(payload.get("lookup_name") or ""),
    )
    if existing:
        return existing, False

    bullets = db.get_all("bullets")
    powders = db.get_all("powder")
    bullet_match = find_bullet_match(
        bullets,
        str(payload.get("bullet_manufacturer") or ""),
        str(payload.get("numeric_caliber") or payload.get("caliber") or ""),
        safe_float(payload.get("bullet_weight_grains")),
        str(payload.get("bullet_name") or ""),
    )
    powder_match = find_powder_match(
        powders,
        str(payload.get("powder_manufacturer") or ""),
        str(payload.get("powder_name") or ""),
    )
    record = {
        "name": payload.get("lookup_name"),
        "caliber": payload.get("caliber"),
        "bullet_id": bullet_match.get("id") if bullet_match else None,
        "bullet_weight": safe_float(payload.get("bullet_weight_grains")) or 0.0,
        "powder_id": powder_match.get("id") if powder_match else None,
        "powder_charge": safe_float(payload.get("charge_grains")) or 0.0,
        "coal": safe_float(payload.get("coal_mm")),
        "velocity_fps": safe_float(payload.get("avg_velocity_fps")),
        "bc_g1": safe_float(payload.get("bc_g1")),
        "bc_g7": safe_float(payload.get("bc_g7")),
        "notes": f"Imported from Gordon PressureTrace appendix: {Path(str(payload.get('source_file'))).name}",
        "component_context_json": json.dumps(
            {
                "source": "gordon_pressuretrace_import",
                "source_file": payload.get("source_file"),
                "charge_name": payload.get("charge_name"),
                "charge_grains": payload.get("charge_grains"),
                "measurement_title": payload.get("measurement_title"),
                "avg_pressure_bar": payload.get("avg_pressure_bar"),
            },
            ensure_ascii=False,
        ),
    }
    profile_id = db.insert("ammo_profiles", record)
    created = db.execute_query(
        "SELECT * FROM ammo_profiles WHERE id = ?", (profile_id,)
    )
    return (created[0] if created else None), True


def parse_pressuretrace_grtload(path: Path) -> list[dict[str, object]]:
    root = ET.parse(path).getroot().find(".//InnerBallistikInput")
    if root is None:
        return []
    title = decode(root.findtext("title") or "")
    caliber = _section_inputs(root, "caliber")
    projectile = _section_inputs(root, "projectile")
    propellant = _section_inputs(root, "propellant")
    appendix = root.find("appendix")
    if appendix is None:
        return []

    bullet_manufacturer = projectile.get("mname", "").strip()
    bullet_name = projectile.get("pname", "").strip()
    bullet_weight_grains = (
        round((safe_float(projectile.get("mp")) or 0.0) * 15.43235835, 2)
        if safe_float(projectile.get("mp")) is not None
        else None
    )
    numeric_caliber = mm_to_caliber_string(projectile.get("Dbul"))
    powder_manufacturer = propellant.get("mname", "").strip()
    powder_name = propellant.get("pname", "").strip()
    caliber_name = caliber.get("CaliberName", "").strip() or title
    coal_mm = safe_float(caliber.get("oal"))

    rows: list[dict[str, object]] = []
    charge_index = 0
    for measurement in appendix.findall("Measurement"):
        measurement_title = decode(measurement.attrib.get("title", ""))
        for charge in measurement.findall("charge"):
            if decode(charge.attrib.get("source")) != "PressureTrace":
                continue
            charge_index += 1
            shots = charge.findall("shot")
            velocities_mps = [safe_float(shot.attrib.get("velocity")) for shot in shots]
            velocities_mps = [value for value in velocities_mps if value is not None]
            velocities_fps = [
                mps_to_fps(value) for value in velocities_mps if value is not None
            ]
            velocities_fps = [value for value in velocities_fps if value is not None]
            pressures_bar = [safe_float(shot.attrib.get("pressure")) for shot in shots]
            pressures_bar = [value for value in pressures_bar if value is not None]
            charge_grains = kg_to_grains(charge.attrib.get("value"))
            row = {
                "source_file": str(path),
                "source_hash": _source_hash(path, charge_index),
                "title": title,
                "measurement_title": measurement_title,
                "charge_name": decode(charge.attrib.get("name")),
                "charge_grains": charge_grains,
                "caliber": caliber_name,
                "bullet_manufacturer": bullet_manufacturer,
                "bullet_name": bullet_name,
                "bullet_weight_grains": bullet_weight_grains,
                "numeric_caliber": numeric_caliber,
                "powder_manufacturer": powder_manufacturer,
                "powder_name": powder_name,
                "coal_mm": coal_mm,
                "bc_g1": safe_float(projectile.get("g1bc")),
                "bc_g7": safe_float(projectile.get("g7bc")),
                "avg_velocity_fps": (
                    round(average(velocities_fps), 1) if velocities_fps else None
                ),
                "es_fps": round(calc_es(velocities_fps), 1) if velocities_fps else None,
                "sd_fps": (
                    round(calc_sd(velocities_fps), 1)
                    if len(velocities_fps) > 1
                    else None
                ),
                "min_velocity_fps": (
                    round(min(velocities_fps), 1) if velocities_fps else None
                ),
                "max_velocity_fps": (
                    round(max(velocities_fps), 1) if velocities_fps else None
                ),
                "avg_pressure_bar": (
                    round(average(pressures_bar), 1) if pressures_bar else None
                ),
                "avg_pressure_psi": (
                    round(average(pressures_bar) * 14.5037738, 1)
                    if pressures_bar
                    else None
                ),
                "velocities_fps": velocities_fps,
                "shots": [
                    {
                        "shot_number": idx,
                        "velocity_mps": safe_float(shot.attrib.get("velocity")),
                        "velocity_fps": (
                            velocities_fps[idx - 1]
                            if idx - 1 < len(velocities_fps)
                            else None
                        ),
                        "pressure_bar": safe_float(shot.attrib.get("pressure")),
                    }
                    for idx, shot in enumerate(shots, start=1)
                ],
            }
            row["lookup_name"] = _profile_name(
                caliber_name,
                bullet_manufacturer,
                bullet_name,
                powder_manufacturer,
                powder_name,
                charge_grains,
            )
            rows.append(row)
    return rows


@dataclass
class PressureTraceImportResult:
    sessions_found: int = 0
    profiles_created: int = 0
    profiles_reused: int = 0
    sessions_imported: int = 0
    sessions_skipped: int = 0


def import_pressuretrace_grtloads(
    db: Database, paths: list[Path]
) -> PressureTraceImportResult:
    result = PressureTraceImportResult()
    for path in paths:
        for row in parse_pressuretrace_grtload(path):
            result.sessions_found += 1
            profile, created = _ensure_profile(db, row)
            if created:
                result.profiles_created += 1
            else:
                result.profiles_reused += 1
            if _existing_session_for_hash(db, str(row["source_hash"])):
                result.sessions_skipped += 1
                continue
            session_id = db.insert(
                "chronograph_sessions",
                {
                    "ammo_profile_id": (profile or {}).get("id"),
                    "device_type": "PressureTrace II",
                    "session_name": f"{Path(row['source_file']).stem} | {row['charge_name']}",
                    "session_date": "",
                    "avg_velocity_fps": row.get("avg_velocity_fps"),
                    "es_fps": row.get("es_fps"),
                    "sd_fps": row.get("sd_fps"),
                    "min_velocity_fps": row.get("min_velocity_fps"),
                    "max_velocity_fps": row.get("max_velocity_fps"),
                    "shot_count": len(row.get("shots") or []),
                    "notes": f"Imported from PressureTrace appendix in {Path(row['source_file']).name}; avg pressure {row.get('avg_pressure_bar')} bar",
                    "raw_data_json": json.dumps(row, ensure_ascii=False),
                    "import_source": Path(row["source_file"]).name,
                    "import_meta_json": json.dumps(
                        {
                            "source": "gordon_pressuretrace_import",
                            "source_file": row.get("source_file"),
                            "charge_name": row.get("charge_name"),
                            "raw_sha256": row.get("source_hash"),
                            "avg_pressure_bar": row.get("avg_pressure_bar"),
                            "avg_pressure_psi": row.get("avg_pressure_psi"),
                        },
                        ensure_ascii=False,
                    ),
                },
            )
            for shot in row.get("shots") or []:
                db.insert(
                    "chronograph_readings",
                    {
                        "session_id": session_id,
                        "shot_number": shot.get("shot_number"),
                        "velocity_fps": shot.get("velocity_fps"),
                        "timestamp": None,
                        "temperature_f": None,
                        "notes": f"pressure_bar={shot.get('pressure_bar')}",
                    },
                )
            result.sessions_imported += 1
    return result
