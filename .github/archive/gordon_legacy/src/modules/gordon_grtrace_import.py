from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

from ..database.database import Database
from .gordon_measurement_import import find_bullet_match, find_powder_match, safe_float


def decode(value: object) -> str:
    return unquote(str(value or "")).strip()


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


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
    return len(left_words & right_words)


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


def is_documentation_sample(path: Path) -> bool:
    lowered = str(path).replace("\\", "/").lower()
    return "/doku/" in lowered or "/docs/" in lowered or "/samples/" in lowered


def _parse_caliber(case_name: str, path: Path) -> str:
    case_text = decode(case_name)
    if case_text:
        normalized = case_text.lower()
        if "hxp 77" in normalized or "30-06" in normalized:
            return ".30-06 Spring. HXP 77 (30-06 Springfield, 30-06, 7,62 x 63)"
    stem = path.stem.lower()
    if stem.startswith("30-06"):
        return ".30-06 Spring. HXP 77 (30-06 Springfield, 30-06, 7,62 x 63)"
    return case_text or path.stem


def _parse_projectile(projectile_text: str) -> tuple[str, str, float | None, str]:
    text = decode(projectile_text)
    weight = None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if match:
        weight = safe_float(match.group(1))
    manufacturer = "Sierra" if "smk" in text.lower() else ""
    bullet_name = "MatchKing" if "smk" in text.lower() else text
    numeric_caliber = (
        ".308" if "168" in text and "30-06" not in text.lower() else ".308"
    )
    return manufacturer, bullet_name, weight, numeric_caliber


def _existing_profile_for_grtrace(db: Database, source_path: Path) -> dict | None:
    source_key = str(source_path).replace("\\", "/").lower()
    for profile in db.get_all("ammo_profiles"):
        try:
            context = json.loads(profile.get("component_context_json") or "{}")
        except Exception:
            context = {}
        if (
            str(context.get("source_file") or "").replace("\\", "/").lower()
            == source_key
        ):
            return profile
    return None


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


def _build_profile_name(
    caliber: str,
    bullet_manufacturer: str,
    bullet_name: str,
    powder_name: str,
    charge_grains: float | None,
) -> str:
    charge_text = f"{charge_grains:.2f} gr" if charge_grains is not None else "? gr"
    return f"{caliber} | {bullet_manufacturer} {bullet_name} | {powder_name} | {charge_text}"


@dataclass
class GRTraceImportResult:
    unique_files: int = 0
    documentation_samples_skipped: int = 0
    imported_profiles: int = 0
    reused_profiles: int = 0
    imported_sessions: int = 0
    skipped_sessions: int = 0


def parse_grtrace_file(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    traces = payload.get("Traces") or []
    config = payload.get("Config") or {}
    projectile_text = decode(config.get("Projectile"))
    powder_text = decode(config.get("Propellant"))
    case_text = decode(config.get("Case"))
    primer_text = decode(config.get("Primer"))

    bullet_manufacturer, bullet_name, bullet_weight, numeric_caliber = (
        _parse_projectile(projectile_text)
    )
    powder_manufacturer = "IMR" if powder_text.upper().startswith("IMR") else ""
    powder_name = powder_text
    caliber = _parse_caliber(case_text, path)

    velocities_mps = [safe_float(trace.get("Velocity")) for trace in traces]
    velocities_mps = [value for value in velocities_mps if value is not None]
    velocities_fps = [round(value * 3.28084, 1) for value in velocities_mps]
    pmax_values = [safe_float(trace.get("pmax_bar")) for trace in traces]
    pmax_values = [value for value in pmax_values if value is not None]
    powder_charge_grains = safe_float((traces[0] if traces else {}).get("PowderCharge"))
    coal_mm = safe_float((traces[0] if traces else {}).get("COAL"))

    avg_trace = payload.get("AvgTrace") or {}
    avg_pmax_bar = safe_float(avg_trace.get("pmax_bar")) or average(pmax_values)

    return {
        "source_file": str(path),
        "source_hash": hashlib.sha256(path.read_bytes()).hexdigest(),
        "device": payload.get("Device"),
        "session_date": payload.get("DateTime"),
        "projectile": projectile_text,
        "propellant": powder_text,
        "case": case_text,
        "primer": primer_text,
        "caliber": caliber,
        "bullet_manufacturer": bullet_manufacturer,
        "bullet_name": bullet_name,
        "bullet_weight": bullet_weight,
        "numeric_caliber": numeric_caliber,
        "powder_manufacturer": powder_manufacturer,
        "powder_name": powder_name,
        "powder_charge": powder_charge_grains,
        "coal": coal_mm,
        "velocities_fps": velocities_fps,
        "avg_velocity_fps": (
            round(average(velocities_fps), 1) if velocities_fps else None
        ),
        "es_fps": round(calc_es(velocities_fps), 1) if velocities_fps else None,
        "sd_fps": (
            round(calc_sd(velocities_fps), 1) if len(velocities_fps) > 1 else None
        ),
        "min_velocity_fps": round(min(velocities_fps), 1) if velocities_fps else None,
        "max_velocity_fps": round(max(velocities_fps), 1) if velocities_fps else None,
        "avg_pmax_bar": round(avg_pmax_bar, 1) if avg_pmax_bar is not None else None,
        "avg_pmax_psi": (
            round(avg_pmax_bar * 14.5037738, 1) if avg_pmax_bar is not None else None
        ),
        "raw_payload": payload,
    }


def ensure_profile_for_grtrace(
    db: Database, parsed: dict[str, object]
) -> tuple[dict | None, bool]:
    existing = _existing_profile_for_grtrace(db, Path(str(parsed["source_file"])))
    if existing:
        return existing, False

    bullets = db.get_all("bullets")
    powders = db.get_all("powder")
    bullet_match = find_bullet_match(
        bullets,
        str(parsed.get("bullet_manufacturer") or ""),
        str(parsed.get("numeric_caliber") or parsed.get("caliber") or ""),
        safe_float(parsed.get("bullet_weight")),
        str(parsed.get("bullet_name") or ""),
    )
    powder_match = find_powder_match(
        powders,
        str(parsed.get("powder_manufacturer") or ""),
        str(parsed.get("powder_name") or ""),
    )

    profile = {
        "name": _build_profile_name(
            str(parsed.get("caliber") or ""),
            str(parsed.get("bullet_manufacturer") or ""),
            str(parsed.get("bullet_name") or ""),
            str(parsed.get("powder_name") or ""),
            safe_float(parsed.get("powder_charge")),
        ),
        "caliber": str(parsed.get("caliber") or "Unknown"),
        "bullet_id": bullet_match.get("id") if bullet_match else None,
        "bullet_weight": safe_float(parsed.get("bullet_weight")) or 0.0,
        "powder_id": powder_match.get("id") if powder_match else None,
        "powder_charge": safe_float(parsed.get("powder_charge")) or 0.0,
        "coal": safe_float(parsed.get("coal")),
        "velocity_fps": safe_float(parsed.get("avg_velocity_fps")),
        "bc_g1": safe_float((bullet_match or {}).get("bc_g1")),
        "bc_g7": safe_float((bullet_match or {}).get("bc_g7")),
        "notes": f"Imported from GRTrace file {Path(str(parsed['source_file'])).name}",
        "component_context_json": json.dumps(
            {
                "source": "gordon_grtrace_import",
                "source_file": parsed.get("source_file"),
                "device": parsed.get("device"),
                "projectile": parsed.get("projectile"),
                "propellant": parsed.get("propellant"),
                "case": parsed.get("case"),
                "primer": parsed.get("primer"),
                "avg_pmax_bar": parsed.get("avg_pmax_bar"),
            },
            ensure_ascii=False,
        ),
    }
    profile_id = db.insert("ammo_profiles", profile)
    created = db.execute_query(
        "SELECT * FROM ammo_profiles WHERE id = ?", (profile_id,)
    )
    return (created[0] if created else None), True


def import_grtrace_files(
    db: Database, paths: Iterable[Path], include_documentation_samples: bool = False
) -> GRTraceImportResult:
    result = GRTraceImportResult()
    seen_hashes: set[str] = set()
    for path in paths:
        if not include_documentation_samples and is_documentation_sample(path):
            result.documentation_samples_skipped += 1
            continue
        parsed = parse_grtrace_file(path)
        source_hash = str(parsed.get("source_hash") or "")
        if not source_hash or source_hash in seen_hashes:
            continue
        seen_hashes.add(source_hash)
        result.unique_files += 1

        profile, created = ensure_profile_for_grtrace(db, parsed)
        if created:
            result.imported_profiles += 1
        else:
            result.reused_profiles += 1

        if _existing_session_for_hash(db, source_hash):
            result.skipped_sessions += 1
            continue

        session_name = Path(str(parsed["source_file"])).stem
        session_payload = {
            "ammo_profile_id": (profile or {}).get("id"),
            "device_type": str(parsed.get("device") or "GRTrace"),
            "session_name": session_name,
            "session_date": str(
                parsed.get("session_date")
                or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
            "avg_velocity_fps": parsed.get("avg_velocity_fps"),
            "es_fps": parsed.get("es_fps"),
            "sd_fps": parsed.get("sd_fps"),
            "min_velocity_fps": parsed.get("min_velocity_fps"),
            "max_velocity_fps": parsed.get("max_velocity_fps"),
            "shot_count": len(parsed.get("velocities_fps") or []),
            "notes": f"Imported from GRTrace with avg pmax {parsed.get('avg_pmax_bar')} bar",
            "raw_data_json": json.dumps(parsed.get("raw_payload"), ensure_ascii=False),
            "import_source": Path(str(parsed["source_file"])).name,
            "import_meta_json": json.dumps(
                {
                    "source": "gordon_grtrace_import",
                    "source_file": parsed.get("source_file"),
                    "raw_sha256": source_hash,
                    "avg_pmax_bar": parsed.get("avg_pmax_bar"),
                    "avg_pmax_psi": parsed.get("avg_pmax_psi"),
                },
                ensure_ascii=False,
            ),
        }
        session_id = db.insert("chronograph_sessions", session_payload)
        for index, velocity in enumerate(parsed.get("velocities_fps") or [], start=1):
            db.insert(
                "chronograph_readings",
                {
                    "session_id": session_id,
                    "shot_number": index,
                    "velocity_fps": velocity,
                    "timestamp": None,
                    "temperature_f": None,
                    "notes": None,
                },
            )
        result.imported_sessions += 1
    return result
