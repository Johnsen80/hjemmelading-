"""
CLI bridge for Gordon dump files.

Reads JSON dumps produced by the temporary Gordon probe plugin, builds
GRT-style candidate rows, optionally matches them against ammo_profiles,
and can import matched rows into grt_data.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import Database  # noqa: E402
from src.modules.gordon_measurement_import import (  # noqa: E402
    find_bullet_match,
    find_powder_match,
    mm_to_caliber_string,
)

DEFAULT_DUMP_DIR = Path(
    r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe\dumps"
)
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "data" / "gordon_temp_extract"
PROJECT_DB_PATH = PROJECT_ROOT / "data" / "reloading.db"
GRAMS_TO_GRAINS = 15.43235835


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def normalize_path_key(value: object) -> str:
    return str(value or "").strip().replace("\\", "/").lower()


def parse_number_with_unit(value: object) -> tuple[float | None, str]:
    text = str(value or "").strip()
    if not text:
        return None, ""
    match = re.match(r"^\s*([-+]?\d+(?:[.,]\d+)?)\s*(.*)$", text)
    if not match:
        return None, ""
    raw_number = match.group(1).replace(",", ".")
    try:
        number = float(raw_number)
    except Exception:
        return None, ""
    return number, match.group(2).strip().lower()


def velocity_to_fps(value: object) -> float | None:
    number, unit = parse_number_with_unit(value)
    if number is None:
        return None
    if "m/s" in unit:
        return round(number * 3.28084, 1)
    return round(number, 1)


def pressure_to_psi(value: object) -> float | None:
    number, unit = parse_number_with_unit(value)
    if number is None:
        return None
    if "bar" in unit:
        return round(number * 14.5037738, 1)
    return round(number, 1)


def pressure_to_bar(value: object) -> float | None:
    number, unit = parse_number_with_unit(value)
    if number is None:
        return None
    if "psi" in unit:
        return round(number / 14.5037738, 1)
    return round(number, 1)


def safe_float(value: object) -> float | None:
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def values_close(
    left: float | None, right: float | None, tolerance: float = 0.15
) -> bool:
    if left is None or right is None:
        return False
    return abs(left - right) <= tolerance


def grams_to_grains(value: object) -> float | None:
    number = safe_float(value)
    if number is None:
        return None
    return round(number * GRAMS_TO_GRAINS, 2)


def build_canonical_profile_name(
    parsed: dict[str, object], fallback_title: str = ""
) -> str:
    caliber = str(parsed.get("caliber") or "").strip()
    bullet_manufacturer = str(parsed.get("bullet_manufacturer") or "").strip()
    bullet_name = str(parsed.get("bullet_name") or "").strip()
    bullet_numeric_caliber = str(parsed.get("bullet_numeric_caliber") or "").strip()
    bullet_weight = safe_float(parsed.get("bullet_weight_grains"))
    powder_manufacturer = str(parsed.get("powder_manufacturer") or "").strip()
    powder_name = str(parsed.get("powder_name") or "").strip()
    powder_charge = safe_float(parsed.get("powder_charge_grains"))

    bullet_bits = [
        part
        for part in [bullet_manufacturer, bullet_name, bullet_numeric_caliber]
        if part
    ]
    if bullet_weight is not None:
        bullet_bits.append(f"{bullet_weight:.2f} grain")
    powder_bits = [part for part in [powder_manufacturer, powder_name] if part]
    if powder_charge is not None:
        powder_bits.append(f"{powder_charge:.2f} gr")

    parts = [
        part
        for part in [
            caliber,
            " ".join(bullet_bits).strip(),
            " ".join(powder_bits).strip(),
        ]
        if part
    ]
    canonical = " | ".join(parts).strip()
    return canonical or fallback_title.strip() or "Gordon import"


def title_mismatch(parsed: dict[str, object]) -> bool:
    title = normalize_text(parsed.get("title"))
    if not title:
        return False
    bullet_manufacturer = normalize_text(parsed.get("bullet_manufacturer"))
    bullet_name = normalize_text(parsed.get("bullet_name"))
    bullet_weight = safe_float(parsed.get("bullet_weight_grains"))

    title_weight_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*grain", str(parsed.get("title") or ""), re.IGNORECASE
    )
    title_weight = (
        safe_float(title_weight_match.group(1)) if title_weight_match else None
    )

    if bullet_manufacturer and bullet_manufacturer not in title:
        return True
    if bullet_name and bullet_name not in title:
        return True
    if (
        bullet_weight is not None
        and title_weight is not None
        and not values_close(bullet_weight, title_weight, tolerance=0.6)
    ):
        return True
    return False


def dump_type_and_summary(payload: dict) -> tuple[str, str]:
    if "results" in payload:
        results = payload.get("results") or {}
        chunks = results.get("chunks") or []
        summary = (
            f"tabhandle={((payload.get('active_tab') or {}).get('active') or {}).get('tabhandle', '-')}, "
            f"chunkCount={len(chunks)}"
        )
        return "tab_results", summary
    if "tabs" in payload:
        tabs = payload.get("tabs") or []
        return "tab_list", f"tabs={len(tabs)}"
    if "active" in payload or "tab" in payload:
        active = payload.get("active") or {}
        tab = payload.get("tab") or {}
        return (
            "active_tab",
            f"caption={tab.get('caption') or active.get('caption') or '-'}",
        )
    return "unknown", f"keys={', '.join(sorted(payload.keys())[:4])}"


def read_dump_files(dump_dir: Path) -> list[dict[str, object]]:
    if not dump_dir.exists():
        return []
    dumps: list[dict[str, object]] = []
    for path in sorted(
        dump_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            dumps.append(
                {
                    "path": path,
                    "type": "invalid_json",
                    "summary": str(exc),
                    "payload": None,
                }
            )
            continue
        row_type, summary = dump_type_and_summary(payload)
        dumps.append(
            {
                "path": path,
                "type": row_type,
                "summary": summary,
                "payload": payload,
            }
        )
    return dumps


def candidate_from_tab_results_dump(
    payload: dict, source_name: str
) -> dict[str, object]:
    active_tab = payload.get("active_tab") or {}
    active_values = active_tab.get("active") or {}
    tab_values = active_tab.get("tab") or {}
    results = payload.get("results") or {}
    results_data = results.get("data") or {}

    caption = tab_values.get("caption") or active_values.get("caption") or source_name
    tab_file = tab_values.get("file") or active_values.get("file") or ""

    return {
        "name": caption,
        "profile_name": caption,
        "source_dump": source_name,
        "source_file": tab_file,
        "predicted_velocity": velocity_to_fps(
            results_data.get("EndVelocity") or results_data.get("MuzzleVelocity")
        ),
        "velocity_fps": velocity_to_fps(
            results_data.get("EndVelocity") or results_data.get("MuzzleVelocity")
        ),
        "max_pressure_psi": pressure_to_psi(results_data.get("MaxPressure")),
        "max_pressure_bar": pressure_to_bar(results_data.get("MaxPressure")),
        "case_fill_percent": safe_float(results_data.get("LoadingDensity")),
        "optimal_coal": safe_float(results_data.get("CartridgeOAL"))
        or safe_float(results_data.get("oal")),
        "raw_summary": {
            "max_pressure": results_data.get("MaxPressure"),
            "end_velocity": results_data.get("EndVelocity")
            or results_data.get("MuzzleVelocity"),
            "end_energy": results_data.get("EndEnergy")
            or results_data.get("MuzzleEnergy"),
            "end_time": results_data.get("EndTime") or results_data.get("MuzzleTime"),
            "burnout_in_barrel": results_data.get("BurnoutInBarrel"),
            "chunk_count": len(results.get("chunks") or []),
        },
    }


def parse_grtload_profile(source_file: str) -> dict[str, object] | None:
    if not source_file:
        return None
    source_path = Path(source_file)
    if not source_path.exists():
        return None
    try:
        root = ET.fromstring(source_path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None

    input_root = root.find(".//InnerBallistikInput")
    if input_root is None:
        return None

    def section_inputs(section_name: str) -> dict[str, str]:
        section = input_root.find(section_name)
        if section is None:
            return {}
        values: dict[str, str] = {}
        for item in section.findall("input"):
            name = str(item.attrib.get("name") or "")
            values[name] = unquote(str(item.attrib.get("value") or ""))
        return values

    title = unquote(str(input_root.findtext("title") or "")).strip()
    caliber = section_inputs("caliber")
    projectile = section_inputs("projectile")
    propellant = section_inputs("propellant")

    parsed = {
        "title": title,
        "caliber": caliber.get("CaliberName", "").strip(),
        "bullet_numeric_caliber": mm_to_caliber_string(projectile.get("Dbul")),
        "coal": safe_float(caliber.get("oal")),
        "bullet_manufacturer": projectile.get("mname", "").strip(),
        "bullet_name": projectile.get("pname", "").strip(),
        "bullet_weight_grains": grams_to_grains(projectile.get("mp")),
        "bullet_bc_g1": safe_float(projectile.get("g1bc")),
        "bullet_bc_g7": safe_float(projectile.get("g7bc")),
        "powder_manufacturer": propellant.get("mname", "").strip(),
        "powder_name": propellant.get("pname", "").strip(),
        "powder_charge_grains": grams_to_grains(propellant.get("mc")),
        "source_file": str(source_path),
        "canonical_profile_name": "",
        "title_projectile_mismatch": False,
    }
    parsed["canonical_profile_name"] = build_canonical_profile_name(
        parsed, fallback_title=title
    )
    parsed["title_projectile_mismatch"] = title_mismatch(parsed)
    return parsed


def find_matching_profile(db: Database, candidate: dict[str, object]) -> dict | None:
    profiles = db.get_all("ammo_profiles")
    candidate_name = normalize_text(candidate.get("profile_name"))
    candidate_coal = safe_float(candidate.get("optimal_coal"))
    candidate_source_file = str(candidate.get("source_file") or "")
    candidate_source_key = normalize_path_key(candidate_source_file)
    candidate_basename = (
        Path(candidate_source_file).name.lower() if candidate_source_file else ""
    )
    candidate_velocity = safe_float(candidate.get("predicted_velocity"))
    candidate_pressure = safe_float(candidate.get("max_pressure_bar"))
    if candidate_name:
        for profile in profiles:
            if normalize_text(profile.get("name")) == candidate_name:
                return profile
    if candidate_name:
        for profile in profiles:
            profile_name = normalize_text(profile.get("name"))
            if candidate_name in profile_name or profile_name in candidate_name:
                return profile
    if candidate_coal is not None:
        for profile in profiles:
            profile_coal = safe_float(profile.get("coal"))
            if profile_coal is not None and abs(profile_coal - candidate_coal) < 0.05:
                return profile

    source_matches = []
    if candidate_source_key or candidate_basename:
        for profile in profiles:
            try:
                context = json.loads(profile.get("component_context_json") or "{}")
            except Exception:
                context = {}
            source_file = str(context.get("source_file") or "")
            source_key = normalize_path_key(source_file)
            if candidate_source_key and source_key == candidate_source_key:
                source_matches.append(profile)
                continue
            if (
                candidate_basename
                and Path(source_file).name.lower() == candidate_basename
            ):
                source_matches.append(profile)
        if len(source_matches) == 1:
            return source_matches[0]
        if source_matches:
            scored_matches = []
            for profile in source_matches:
                score = 0.0
                existing_rows = db.execute_query(
                    "SELECT predicted_velocity, max_pressure_bar FROM grt_data WHERE ammo_profile_id = ?",
                    (profile["id"],),
                )
                if existing_rows:
                    row = existing_rows[0]
                    existing_velocity = safe_float(row.get("predicted_velocity"))
                    existing_pressure = safe_float(row.get("max_pressure_bar"))
                    if candidate_velocity is not None and existing_velocity is not None:
                        score += abs(candidate_velocity - existing_velocity)
                    else:
                        score += 1000.0
                    if candidate_pressure is not None and existing_pressure is not None:
                        score += abs(candidate_pressure - existing_pressure) * 2.0
                    else:
                        score += 1000.0
                else:
                    score += 5000.0
                scored_matches.append((score, profile))
            scored_matches.sort(key=lambda item: item[0])
            return scored_matches[0][1]
    return None


def build_grt_record(
    ammo_profile_id: int, candidate: dict[str, object]
) -> dict[str, object]:
    return {
        "ammo_profile_id": ammo_profile_id,
        "predicted_velocity": candidate.get("predicted_velocity"),
        "max_pressure_psi": candidate.get("max_pressure_psi"),
        "max_pressure_bar": candidate.get("max_pressure_bar"),
        "case_fill_percent": candidate.get("case_fill_percent"),
        "optimal_coal": candidate.get("optimal_coal"),
        "grt_data": json.dumps(candidate, ensure_ascii=False),
        "import_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "notes": f"Imported from Gordon dump {candidate.get('source_dump', '')}",
    }


def _refresh_profile_from_parsed(
    db: Database,
    profile: dict,
    parsed: dict[str, object],
    candidate: dict[str, object],
) -> dict:
    bullets = db.get_all("bullets")
    powders = db.get_all("powder")
    bullet_match = find_bullet_match(
        bullets,
        str(parsed.get("bullet_manufacturer") or ""),
        str(parsed.get("bullet_numeric_caliber") or parsed.get("caliber") or ""),
        safe_float(parsed.get("bullet_weight_grains")),
        str(parsed.get("bullet_name") or ""),
    )
    powder_match = find_powder_match(
        powders,
        str(parsed.get("powder_manufacturer") or ""),
        str(parsed.get("powder_name") or ""),
    )

    updates: dict[str, object] = {}
    canonical_name = str(
        parsed.get("canonical_profile_name") or profile.get("name") or ""
    ).strip()
    if bullet_match and not profile.get("bullet_id"):
        updates["bullet_id"] = bullet_match.get("id")
    if bullet_match and profile.get("bullet_id") != bullet_match.get("id"):
        updates["bullet_id"] = bullet_match.get("id")
    if powder_match and not profile.get("powder_id"):
        updates["powder_id"] = powder_match.get("id")
    if powder_match and profile.get("powder_id") != powder_match.get("id"):
        updates["powder_id"] = powder_match.get("id")
    if parsed.get("caliber") and not profile.get("caliber"):
        updates["caliber"] = parsed.get("caliber")
    if parsed.get("caliber") and normalize_text(
        profile.get("caliber")
    ) != normalize_text(parsed.get("caliber")):
        updates["caliber"] = parsed.get("caliber")
    if safe_float(parsed.get("bullet_weight_grains")) and not safe_float(
        profile.get("bullet_weight")
    ):
        updates["bullet_weight"] = safe_float(parsed.get("bullet_weight_grains"))
    if safe_float(parsed.get("bullet_weight_grains")) and not values_close(
        safe_float(profile.get("bullet_weight")),
        safe_float(parsed.get("bullet_weight_grains")),
        tolerance=0.6,
    ):
        updates["bullet_weight"] = safe_float(parsed.get("bullet_weight_grains"))
    if safe_float(parsed.get("powder_charge_grains")) and not safe_float(
        profile.get("powder_charge")
    ):
        updates["powder_charge"] = safe_float(parsed.get("powder_charge_grains"))
    if safe_float(parsed.get("powder_charge_grains")) and not values_close(
        safe_float(profile.get("powder_charge")),
        safe_float(parsed.get("powder_charge_grains")),
        tolerance=0.11,
    ):
        updates["powder_charge"] = safe_float(parsed.get("powder_charge_grains"))
    if safe_float(parsed.get("coal")) and not safe_float(profile.get("coal")):
        updates["coal"] = safe_float(parsed.get("coal"))
    if safe_float(parsed.get("coal")) and not values_close(
        safe_float(profile.get("coal")), safe_float(parsed.get("coal")), tolerance=0.05
    ):
        updates["coal"] = safe_float(parsed.get("coal"))
    if safe_float(parsed.get("bullet_bc_g1")) and not safe_float(profile.get("bc_g1")):
        updates["bc_g1"] = safe_float(parsed.get("bullet_bc_g1"))
    if safe_float(parsed.get("bullet_bc_g1")) and not values_close(
        safe_float(profile.get("bc_g1")),
        safe_float(parsed.get("bullet_bc_g1")),
        tolerance=0.01,
    ):
        updates["bc_g1"] = safe_float(parsed.get("bullet_bc_g1"))
    if (
        safe_float(parsed.get("bullet_bc_g7")) is not None
        and safe_float(profile.get("bc_g7")) is None
    ):
        updates["bc_g7"] = safe_float(parsed.get("bullet_bc_g7"))
    if safe_float(parsed.get("bullet_bc_g7")) is not None and not values_close(
        safe_float(profile.get("bc_g7")),
        safe_float(parsed.get("bullet_bc_g7")),
        tolerance=0.01,
    ):
        updates["bc_g7"] = safe_float(parsed.get("bullet_bc_g7"))
    if safe_float(candidate.get("predicted_velocity")) and not safe_float(
        profile.get("velocity_fps")
    ):
        updates["velocity_fps"] = safe_float(candidate.get("predicted_velocity"))
    if canonical_name and normalize_text(profile.get("name")) != normalize_text(
        canonical_name
    ):
        updates["name"] = canonical_name

    try:
        context = json.loads(profile.get("component_context_json") or "{}")
    except Exception:
        context = {}
    context.update(
        {
            "source": "gordon_dump_import",
            "source_file": str(
                parsed.get("source_file") or candidate.get("source_file") or ""
            ),
            "load_title": str(
                parsed.get("title") or candidate.get("profile_name") or ""
            ),
            "canonical_profile_name": canonical_name,
            "title_projectile_mismatch": bool(parsed.get("title_projectile_mismatch")),
            "bullet_manufacturer": parsed.get("bullet_manufacturer"),
            "bullet_name": parsed.get("bullet_name"),
            "bullet_weight_grains": safe_float(parsed.get("bullet_weight_grains")),
            "powder_manufacturer": parsed.get("powder_manufacturer"),
            "powder_name": parsed.get("powder_name"),
            "powder_charge_grains": safe_float(parsed.get("powder_charge_grains")),
        }
    )
    updates["component_context_json"] = json.dumps(context, ensure_ascii=False)

    if updates:
        db.update("ammo_profiles", updates, "id = ?", (profile["id"],))
        refreshed = db.execute_query(
            "SELECT * FROM ammo_profiles WHERE id = ?", (profile["id"],)
        )
        if refreshed:
            return refreshed[0]
    return profile


def ensure_profile_for_candidate(
    db: Database, candidate: dict[str, object]
) -> dict | None:
    source_file = str(candidate.get("source_file") or "")
    parsed = parse_grtload_profile(source_file)
    if not parsed:
        return None

    existing_profiles = db.get_all("ammo_profiles")
    source_key = normalize_path_key(source_file)
    source_basename = Path(source_file).name.lower()
    for profile in existing_profiles:
        try:
            context = json.loads(profile.get("component_context_json") or "{}")
        except Exception:
            context = {}
        context_source = str(context.get("source_file") or "")
        context_key = normalize_path_key(context_source)
        if source_key and context_key == source_key:
            return _refresh_profile_from_parsed(db, profile, parsed, candidate)
        if (
            source_basename
            and Path(context_source).name.lower() == source_basename
            and not context_key
        ):
            return _refresh_profile_from_parsed(db, profile, parsed, candidate)

    bullets = db.get_all("bullets")
    powders = db.get_all("powder")
    bullet_match = find_bullet_match(
        bullets,
        str(parsed.get("bullet_manufacturer") or ""),
        str(parsed.get("bullet_numeric_caliber") or parsed.get("caliber") or ""),
        safe_float(parsed.get("bullet_weight_grains")),
        str(parsed.get("bullet_name") or ""),
    )
    powder_match = find_powder_match(
        powders,
        str(parsed.get("powder_manufacturer") or ""),
        str(parsed.get("powder_name") or ""),
    )

    profile_name = str(
        parsed.get("canonical_profile_name")
        or parsed.get("title")
        or candidate.get("profile_name")
        or candidate.get("name")
        or "Gordon import"
    ).strip()
    profile_record = {
        "name": profile_name,
        "caliber": str(parsed.get("caliber") or "Unknown"),
        "bullet_id": bullet_match.get("id") if bullet_match else None,
        "bullet_weight": safe_float(parsed.get("bullet_weight_grains")) or 0.0,
        "powder_id": powder_match.get("id") if powder_match else None,
        "powder_charge": safe_float(parsed.get("powder_charge_grains")) or 0.0,
        "coal": safe_float(parsed.get("coal")),
        "velocity_fps": safe_float(candidate.get("predicted_velocity")),
        "bc_g1": safe_float(parsed.get("bullet_bc_g1")),
        "bc_g7": safe_float(parsed.get("bullet_bc_g7")),
        "notes": f"Auto-created from Gordon dump {candidate.get('source_dump', '')}",
        "component_context_json": json.dumps(
            {
                "source": "gordon_dump_import",
                "source_file": str(parsed.get("source_file") or source_file),
                "load_title": str(
                    parsed.get("title") or candidate.get("profile_name") or ""
                ),
                "canonical_profile_name": profile_name,
                "title_projectile_mismatch": bool(
                    parsed.get("title_projectile_mismatch")
                ),
                "bullet_manufacturer": parsed.get("bullet_manufacturer"),
                "bullet_name": parsed.get("bullet_name"),
                "bullet_weight_grains": safe_float(parsed.get("bullet_weight_grains")),
                "powder_manufacturer": parsed.get("powder_manufacturer"),
                "powder_name": parsed.get("powder_name"),
                "powder_charge_grains": safe_float(parsed.get("powder_charge_grains")),
            },
            ensure_ascii=False,
        ),
    }
    new_id = db.insert("ammo_profiles", profile_record)
    created = db.execute_query("SELECT * FROM ammo_profiles WHERE id = ?", (new_id,))
    return created[0] if created else None


def build_candidate_rows(db: Database, dump_dir: Path) -> list[dict[str, object]]:
    rows_by_key: dict[str, dict[str, object]] = {}
    for dump_row in read_dump_files(dump_dir):
        if dump_row.get("type") != "tab_results":
            continue
        payload = dump_row.get("payload")
        if not isinstance(payload, dict):
            continue
        candidate = candidate_from_tab_results_dump(
            payload, Path(dump_row["path"]).name
        )
        match = find_matching_profile(db, candidate)
        key = str(
            candidate.get("source_file")
            or candidate.get("profile_name")
            or dump_row["path"]
        )
        if key not in rows_by_key:
            rows_by_key[key] = {
                "candidate": candidate,
                "match": match,
                "path": dump_row["path"],
            }
    return list(rows_by_key.values())


def export_candidates(
    candidate_rows: list[dict[str, object]], export_dir: Path
) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    candidates = []
    for row in candidate_rows:
        candidate = dict(row["candidate"])
        match = row.get("match")
        candidate["matched_ammo_profile_id"] = (
            match.get("id") if isinstance(match, dict) else None
        )
        candidate["matched_ammo_profile_name"] = (
            match.get("name") if isinstance(match, dict) else None
        )
        candidates.append(candidate)
    path = export_dir / "gordon_grt_import_candidates.json"
    path.write_text(
        json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return path


def import_candidates(
    db: Database, candidate_rows: list[dict[str, object]]
) -> tuple[int, int]:
    imported = 0
    skipped = 0
    for row in candidate_rows:
        match = row.get("match")
        match = (
            ensure_profile_for_candidate(db, row["candidate"])
            if not isinstance(match, dict)
            else ensure_profile_for_candidate(db, row["candidate"]) or match
        )
        row["match"] = match
        if not isinstance(match, dict):
            skipped += 1
            continue
        grt_record = build_grt_record(int(match["id"]), row["candidate"])
        existing = db.execute_query(
            "SELECT id FROM grt_data WHERE ammo_profile_id = ?",
            (match["id"],),
        )
        if existing:
            db.update("grt_data", grt_record, "id = ?", (existing[0]["id"],))
        else:
            db.insert("grt_data", grt_record)
        imported += 1
    return imported, skipped


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump-dir", default=str(DEFAULT_DUMP_DIR))
    parser.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR))
    parser.add_argument("--import-db", action="store_true")
    args = parser.parse_args(argv[1:])

    dump_dir = Path(args.dump_dir)
    export_dir = Path(args.export_dir)
    db = Database(db_path=str(PROJECT_DB_PATH))

    candidate_rows = build_candidate_rows(db, dump_dir)
    export_path = export_candidates(candidate_rows, export_dir)

    matched = sum(1 for row in candidate_rows if row.get("match"))
    print(f"Dump dir: {dump_dir}")
    print(f"Candidates: {len(candidate_rows)}")
    print(f"Matched ammo profiles: {matched}")
    print(f"Exported: {export_path}")

    if args.import_db:
        imported, skipped = import_candidates(db, candidate_rows)
        print(f"Imported to grt_data: {imported}")
        print(f"Skipped without match: {skipped}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
