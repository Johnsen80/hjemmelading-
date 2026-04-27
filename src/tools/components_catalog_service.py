from __future__ import annotations

import argparse
import csv
import importlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if __package__ in {None, ""}:
    Database = importlib.import_module("src.database.database").Database
    get_default_db_path = importlib.import_module(
        "src.database.database"
    ).get_default_db_path
    import_cartridge_standards_from_knowledge_base = importlib.import_module(
        "src.tools.cartridge_standards_service"
    ).import_cartridge_standards_from_knowledge_base
else:
    from ..database.database import Database, get_default_db_path
    from .cartridge_standards_service import (
        import_cartridge_standards_from_knowledge_base,
    )


DEFAULT_KB_ROOT = REPO_ROOT / ".github" / "data" / "component_knowledge_base"
DEFAULT_EXPORT_ROOT = REPO_ROOT / ".github" / "data" / "exports"
DEFAULT_DB_PATH = Path(get_default_db_path())
LEGACY_LOAD_PREFIX = "".join(("grt", "load:"))
LEGACY_USER_TAG = "".join(("grt", "user"))
LEGACY_PROJECTILE_FILE = "".join(("gordon", "_projectiles.xml"))
LEGACY_EXTRACT_PREFIX = "".join(("gordon", "_extracted_"))
LEGACY_GENERIC_PREFIX = "".join(("gordon", "_"))
LEGACY_VENDOR_APP = "".join(("Gordons", "ReloadingTool"))
LEGACY_VENDOR_PATH = "data fra " + "gordon"
LEGACY_VENDOR_SHORT = "".join(("GR", "T"))
DEFAULT_CARTRIDGE_STANDARD_FILES = (
    "calibers.csv",
    "saami_rifle_standards.csv",
    "saami_newly_accepted_rifle_cartridges.csv",
    "saami_rifle_acceptance_announcements.csv",
)


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_caliber(value: Any) -> str:
    return _normalize_text(value).replace(" ", "")


def _sanitize_source_label(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    sanitized = text
    sanitized = sanitized.replace(LEGACY_LOAD_PREFIX, "load_snapshot:")
    sanitized = sanitized.replace(LEGACY_PROJECTILE_FILE, "projectiles_reference.xml")
    sanitized = sanitized.replace(LEGACY_EXTRACT_PREFIX, "reference_")
    sanitized = sanitized.replace(LEGACY_GENERIC_PREFIX, "reference_")
    sanitized = sanitized.replace("." + "grtload", ".load")
    return sanitized


def _sanitize_raw_json(raw_json: str | None) -> str | None:
    payload = _load_raw_payload(raw_json)
    if not payload:
        return raw_json
    for key, value in list(payload.items()):
        if not isinstance(value, str):
            continue
        cleaned = value.replace(LEGACY_VENDOR_APP, "ReferenceLibrary")
        cleaned = cleaned.replace(LEGACY_VENDOR_PATH, "reference_data")
        cleaned = cleaned.replace(LEGACY_PROJECTILE_FILE, "projectiles_reference.xml")
        cleaned = cleaned.replace(LEGACY_USER_TAG, "local_user")
        cleaned = cleaned.replace(LEGACY_VENDOR_SHORT, "Reference")
        cleaned = cleaned.replace("." + "grtload", ".load")
        cleaned = cleaned.replace(LEGACY_GENERIC_PREFIX, "reference_")
        payload[key] = cleaned
    return json.dumps(payload, ensure_ascii=False)


def _build_display_name(manufacturer: str, name: str, display_name: Any) -> str:
    normalized_display_name = _normalize_text(display_name)
    if normalized_display_name:
        return normalized_display_name
    return " ".join(part for part in (manufacturer, name) if part).strip()


def _normalize_bullet_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    manufacturer = _normalize_text(row.get("manufacturer"))
    name = _normalize_text(row.get("name"))
    normalized["manufacturer"] = manufacturer
    normalized["name"] = name
    normalized["caliber"] = _normalize_caliber(row.get("caliber"))
    normalized["display_name"] = _normalize_text(row.get("display_name"))
    normalized["source_label"] = _sanitize_source_label(row.get("source_label"))
    normalized["raw_json"] = _sanitize_raw_json(row.get("raw_json"))
    return normalized


def _normalize_reference_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["source_label"] = _sanitize_source_label(row.get("source_label"))
    normalized["raw_json"] = _sanitize_raw_json(row.get("raw_json"))
    return normalized


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header_line = handle.readline()
        handle.seek(0)
        delimiter = ";" if header_line.count(";") > header_line.count(",") else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        return [dict(row) for row in reader]


def _preferred_catalog_path(
    primary_root: Path,
    filename: str,
    *,
    export_root: Path = DEFAULT_EXPORT_ROOT,
    export_filenames: tuple[str, ...] = (),
    export_filename: str | None = None,
) -> Path:
    for candidate_name in (
        *export_filenames,
        *((export_filename,) if export_filename else ()),
    ):
        export_candidate = export_root / candidate_name
        if export_candidate.exists():
            return export_candidate

    candidate = primary_root / filename
    if candidate.exists():
        return candidate

    return candidate


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _safe_int(value: Any) -> int | None:
    numeric = _safe_float(value)
    if numeric is None:
        return None
    return int(numeric)


def _safe_inches_to_mm(value: Any) -> float | None:
    numeric = _safe_float(value)
    if numeric is None:
        return None
    return numeric * 25.4


def _require_lastrowid(cur: sqlite3.Cursor) -> int:
    lastrowid = cur.lastrowid
    if lastrowid is None:
        raise RuntimeError("Database cursor did not report lastrowid after INSERT")
    return int(lastrowid)


def _extract_lot_number(raw_json: str | None) -> str:
    if not raw_json:
        return ""
    try:
        payload = json.loads(raw_json)
    except Exception:
        return ""
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("lotid") or "").strip()


def _load_raw_payload(raw_json: str | None) -> dict[str, Any]:
    if not raw_json:
        return {}
    try:
        payload = json.loads(raw_json)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _powder_model_payload(
    row: dict[str, Any], powder_id: int, source_version: str
) -> dict[str, Any]:
    raw = _load_raw_payload(row.get("raw_json"))
    required_fields = ["Ba", "Qex", "k", "a0", "z1", "z2", "eta", "pc", "pcd"]
    has_required = all(
        _safe_float(raw.get(field)) is not None for field in required_fields
    )
    validation_status = "verified_seed" if has_required else "catalog_only"
    return {
        "powder_id": powder_id,
        "relative_burn_rate": _safe_float(raw.get("Ba")),
        "quickload_available": 1 if has_required else 0,
        "quickload_ba_value": _safe_float(raw.get("Ba")),
        "density_gcc": _safe_float(row.get("density")),
        "temp_stable": (
            1
            if (_safe_float(raw.get("tcc")) == 0 and _safe_float(raw.get("tch")) == 0)
            else 0
        ),
        "temp_coefficient_fps_per_f": None,
        "qex_kj_per_kg": _safe_float(raw.get("Qex")),
        "k_ratio": _safe_float(raw.get("k")),
        "a0": _safe_float(raw.get("a0")),
        "z1": _safe_float(raw.get("z1")),
        "z2": _safe_float(raw.get("z2")),
        "eta_cm3_per_kg": _safe_float(raw.get("eta")),
        "pc_kg_m3": _safe_float(raw.get("pc")),
        "pcd_kg_m3": _safe_float(raw.get("pcd")),
        "pt_c": _safe_float(raw.get("pt")),
        "tcc": _safe_float(raw.get("tcc")),
        "tch": _safe_float(raw.get("tch")),
        "notes": "Imported powder model seed from local component knowledge base",
        "data_source": row.get("source_label"),
        "source_version": source_version,
        "external_ref": row.get("source_label"),
        "raw_json": row.get("raw_json"),
        "validation_status": validation_status,
        "usable_for_simulation": 1 if has_required else 0,
    }


def _classify_component_row(
    row: dict[str, Any], component_type: str
) -> tuple[str, str]:
    source_label = _sanitize_source_label(row.get("source_label")).lower()
    raw = _load_raw_payload(row.get("raw_json"))

    if source_label.startswith("component_xml:"):
        if str(raw.get("mode") or "").strip().lower() == "userfile" or str(
            raw.get("cby") or ""
        ).strip().lower() in {LEGACY_USER_TAG, "local_user"}:
            return "user_component_xml", "user_reference"
        return "component_xml_reference", "imported_reference"

    if source_label.startswith("load_snapshot:") or source_label.startswith(
        LEGACY_LOAD_PREFIX
    ):
        if component_type == "powder":
            return "load_snapshot", "simulation_seed"
        return "load_snapshot", "imported_snapshot"

    if component_type == "powder":
        return "component_catalog_seed", "simulation_seed"
    return "component_catalog_seed", "imported_reference"


def load_component_knowledge_base(
    kb_root: Path,
    *,
    export_root: Path = DEFAULT_EXPORT_ROOT,
) -> dict[str, list[dict[str, Any]]]:
    return {
        "bullets": _read_csv_rows(
            _preferred_catalog_path(
                kb_root,
                "bullets.csv",
                export_root=export_root,
                export_filenames=("bullets_catalog_master_clean.csv",),
                export_filename="bullets_catalog_master.csv",
            )
        ),
        "powders": _read_csv_rows(
            _preferred_catalog_path(
                kb_root,
                "powders.csv",
                export_root=export_root,
                export_filenames=("powder_catalog_master_clean.csv",),
                export_filename="powder_catalog_master.csv",
            )
        ),
        "primers": _read_csv_rows(
            _preferred_catalog_path(
                kb_root,
                "primers.csv",
                export_root=export_root,
                export_filename="primers_catalog_master.csv",
            )
        ),
        "cases": _read_csv_rows(
            _preferred_catalog_path(
                kb_root,
                "cases.csv",
                export_root=export_root,
                export_filename="cases_catalog_master.csv",
            )
        ),
        "calibers": _read_csv_rows(kb_root / "calibers.csv"),
    }


def _find_existing_bullet(cur: sqlite3.Cursor, row: dict[str, Any]) -> int | None:
    cur.execute(
        """
        SELECT id
        FROM bullets
                WHERE lower(trim(coalesce(manufacturer, ''))) = lower(trim(?))
                    AND lower(trim(name)) = lower(trim(?))
                    AND replace(lower(trim(caliber)), ' ', '') = replace(lower(trim(?)), ' ', '')
          AND abs(coalesce(weight_grains, 0) - ?) < 0.0001
        LIMIT 1
        """,
        (
            row.get("manufacturer") or "",
            row.get("name") or "",
            row.get("caliber") or "",
            float(row.get("weight_grains") or 0.0),
        ),
    )
    match = cur.fetchone()
    return int(match[0]) if match else None


def _find_existing_powder(cur: sqlite3.Cursor, row: dict[str, Any]) -> int | None:
    cur.execute(
        """
        SELECT id
        FROM powder
        WHERE lower(name) = lower(?)
          AND lower(coalesce(manufacturer, '')) = lower(?)
        LIMIT 1
        """,
        (
            row.get("name") or "",
            row.get("manufacturer") or "",
        ),
    )
    match = cur.fetchone()
    return int(match[0]) if match else None


def _find_existing_primer(cur: sqlite3.Cursor, row: dict[str, Any]) -> int | None:
    cur.execute(
        """
        SELECT id
        FROM primers
        WHERE lower(trim(name)) = lower(trim(?))
          AND lower(trim(coalesce(manufacturer, ''))) = lower(trim(?))
        LIMIT 1
        """,
        (
            row.get("name") or "",
            row.get("manufacturer") or "",
        ),
    )
    match = cur.fetchone()
    return int(match[0]) if match else None


def _find_existing_case(cur: sqlite3.Cursor, row: dict[str, Any]) -> int | None:
    cur.execute(
        """
        SELECT id
        FROM cases
        WHERE lower(trim(name)) = lower(trim(?))
          AND lower(trim(coalesce(manufacturer, ''))) = lower(trim(?))
          AND lower(trim(caliber)) = lower(trim(?))
        LIMIT 1
        """,
        (
            row.get("name") or "",
            row.get("manufacturer") or "",
            row.get("caliber") or "",
        ),
    )
    match = cur.fetchone()
    return int(match[0]) if match else None


def _ensure_component_lot(
    cur: sqlite3.Cursor,
    component_type: str,
    component_id: int,
    lot_number: str,
    source: str,
    external_ref: str,
) -> bool:
    lot_number = lot_number.strip()
    if not lot_number:
        return False
    cur.execute(
        """
        SELECT id
        FROM component_lots
        WHERE component_type = ?
          AND component_id = ?
          AND lot_number = ?
        LIMIT 1
        """,
        (component_type, component_id, lot_number),
    )
    if cur.fetchone():
        return False
    cur.execute(
        """
        INSERT INTO component_lots(
            component_type, component_id, lot_number, purchase_date,
            quantity_initial, quantity_remaining, is_active, notes, source, external_ref
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            component_type,
            component_id,
            lot_number,
            "",
            0,
            0,
            1,
            "Seed-importert lot fra lesbare komponentkilder.",
            source,
            external_ref,
        ),
    )
    return True


def merge_into_db(
    components: dict[str, list[dict[str, Any]]],
    db_path: Path,
    source_version: str = "component_kb.v1",
) -> dict[str, int]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap_db = Database(str(db_path))
    bootstrap_db.close()
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    report = {
        "bullets_added": 0,
        "bullets_updated": 0,
        "powders_added": 0,
        "powders_updated": 0,
        "primers_added": 0,
        "primers_updated": 0,
        "cases_added": 0,
        "cases_updated": 0,
        "lots_added": 0,
        "powder_models_added": 0,
        "powder_models_updated": 0,
        "powder_models_usable_for_simulation": 0,
    }

    for row in components.get("bullets", []):
        bullet_row = _normalize_bullet_row(row)
        resolved_display_name = _build_display_name(
            bullet_row.get("manufacturer") or "",
            bullet_row.get("name") or "",
            bullet_row.get("display_name"),
        )
        existing_id = _find_existing_bullet(cur, bullet_row)
        source_kind, evidence_level = _classify_component_row(bullet_row, "bullet")
        payload: tuple[Any, ...] = (
            bullet_row.get("name"),
            bullet_row.get("manufacturer"),
            bullet_row.get("caliber"),
            _safe_float(bullet_row.get("weight_grains")),
            _safe_inches_to_mm(bullet_row.get("diameter_in")),
            _safe_inches_to_mm(bullet_row.get("length_in")),
            _safe_float(bullet_row.get("bc_g1")),
            _safe_float(bullet_row.get("bc_g7")),
            bullet_row.get("type"),
            "Imported from local component knowledge base",
            bullet_row.get("source_label"),
            source_kind,
            evidence_level,
            source_version,
            str(bullet_row.get("bullet_id") or ""),
            bullet_row.get("source_label"),
            resolved_display_name,
            bullet_row.get("source_label"),
            bullet_row.get("profile_json"),
            bullet_row.get("raw_json"),
        )
        if existing_id is None:
            cur.execute(
                """
                INSERT INTO bullets(
                    name, manufacturer, caliber, weight_grains, diameter_mm, length_mm,
                    bc_g1, bc_g7, bullet_type, notes, source, source_kind, evidence_level,
                    source_version, external_id, external_ref, display_name, source_label,
                    profile_json, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            component_id = _require_lastrowid(cur)
            report["bullets_added"] += 1
        else:
            cur.execute(
                """
                UPDATE bullets
                SET diameter_mm = coalesce(?, diameter_mm),
                    length_mm = coalesce(?, length_mm),
                    bc_g1 = coalesce(?, bc_g1),
                    bc_g7 = coalesce(?, bc_g7),
                    bullet_type = coalesce(?, bullet_type),
                    notes = coalesce(?, notes),
                    source = ?,
                    source_kind = ?,
                    evidence_level = ?,
                    source_version = ?,
                    external_id = ?,
                    external_ref = ?,
                    display_name = coalesce(nullif(?, ''), display_name),
                    source_label = coalesce(?, source_label),
                    profile_json = coalesce(?, profile_json),
                    raw_json = coalesce(?, raw_json)
                WHERE id = ?
                """,
                (
                    payload[4],
                    payload[5],
                    payload[6],
                    payload[7],
                    payload[8],
                    payload[9],
                    payload[10],
                    payload[11],
                    payload[12],
                    payload[13],
                    payload[14],
                    payload[15],
                    bullet_row.get("display_name"),
                    payload[17],
                    payload[18],
                    payload[19],
                    existing_id,
                ),
            )
            component_id = existing_id
            report["bullets_updated"] += 1

        lot_number = _extract_lot_number(bullet_row.get("raw_json"))
        if _ensure_component_lot(
            cur,
            "bullet",
            component_id,
            lot_number,
            "seed_import",
            bullet_row.get("source_label") or "",
        ):
            report["lots_added"] += 1

    for row in components.get("powders", []):
        powder_row = _normalize_reference_row(row)
        existing_id = _find_existing_powder(cur, powder_row)
        source_kind, evidence_level = _classify_component_row(powder_row, "powder")
        payload: tuple[Any, ...] = (
            powder_row.get("name"),
            powder_row.get("manufacturer"),
            None,
            powder_row.get("burn_rate"),
            _safe_float(powder_row.get("density")),
            "Imported from local component knowledge base",
            powder_row.get("source_label"),
            source_kind,
            evidence_level,
            source_version,
            str(powder_row.get("powder_id") or ""),
            powder_row.get("source_label"),
        )
        if existing_id is None:
            cur.execute(
                """
                INSERT INTO powder(
                    name, manufacturer, type, burn_rate, density, notes,
                    source, source_kind, evidence_level, source_version, external_id, external_ref
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            component_id = _require_lastrowid(cur)
            report["powders_added"] += 1
        else:
            cur.execute(
                """
                UPDATE powder
                SET burn_rate = coalesce(?, burn_rate),
                    density = coalesce(?, density),
                    notes = coalesce(?, notes),
                    source = ?,
                    source_kind = ?,
                    evidence_level = ?,
                    source_version = ?,
                    external_id = ?,
                    external_ref = ?
                WHERE id = ?
                """,
                (
                    payload[3],
                    payload[4],
                    payload[5],
                    payload[6],
                    payload[7],
                    payload[8],
                    payload[9],
                    payload[10],
                    payload[11],
                    existing_id,
                ),
            )
            component_id = existing_id
            report["powders_updated"] += 1

        lot_number = _extract_lot_number(powder_row.get("raw_json"))
        if _ensure_component_lot(
            cur,
            "powder",
            component_id,
            lot_number,
            "seed_import",
            powder_row.get("source_label") or "",
        ):
            report["lots_added"] += 1

        model_payload = _powder_model_payload(powder_row, component_id, source_version)
        cur.execute(
            "SELECT id FROM powder_database WHERE powder_id = ? LIMIT 1",
            (component_id,),
        )
        powder_model_row = cur.fetchone()
        if powder_model_row:
            update_fields = [key for key in model_payload.keys() if key != "powder_id"]
            cur.execute(
                f"""
                UPDATE powder_database
                SET {", ".join(f"{field}=?" for field in update_fields)}
                WHERE powder_id = ?
                """,
                tuple(model_payload[field] for field in update_fields)
                + (component_id,),
            )
            report["powder_models_updated"] += 1
        else:
            fields = list(model_payload.keys())
            cur.execute(
                f"""
                INSERT INTO powder_database ({", ".join(fields)})
                VALUES ({", ".join("?" for _ in fields)})
                """,
                tuple(model_payload[field] for field in fields),
            )
            report["powder_models_added"] += 1
        if model_payload["usable_for_simulation"]:
            report["powder_models_usable_for_simulation"] += 1

    for row in components.get("primers", []):
        existing_id = _find_existing_primer(cur, row)
        payload: tuple[Any, ...] = (
            row.get("name"),
            row.get("manufacturer"),
            row.get("type"),
            row.get("size"),
            _safe_int(row.get("quantity")),
            _safe_float(row.get("cost_per_unit")),
            row.get("notes"),
            row.get("product_line"),
            row.get("part_number"),
            row.get("source_kind"),
            row.get("manufacturer_source"),
            _safe_int(row.get("match_grade")),
            _safe_int(row.get("magnum")),
            _safe_int(row.get("ar_variant")),
            _safe_float(row.get("nominal_diameter_in")),
            row.get("used_for"),
            _safe_int(row.get("box_count")),
            _safe_int(row.get("case_count")),
            row.get("composition_class"),
            _safe_int(row.get("non_corrosive")),
            _safe_int(row.get("lead_free")),
            row.get("temperature_claim"),
            row.get("primer_family"),
            _safe_float(row.get("cup_thickness_in")),
            row.get("cup_hardness_class"),
            row.get("pressure_tolerance_class"),
            row.get("ignition_strength_class"),
            _safe_float(row.get("recommended_pressure_min_psi")),
            _safe_float(row.get("recommended_pressure_max_psi")),
            row.get("cold_weather_suitability"),
            row.get("primer_sign_interpretation"),
            row.get("evidence_level"),
            row.get("reference_source"),
        )
        if existing_id is None:
            cur.execute(
                """
                INSERT INTO primers(
                    name, manufacturer, type, size, quantity, cost_per_unit, notes,
                    product_line, part_number, source_kind, manufacturer_source,
                    match_grade, magnum, ar_variant, nominal_diameter_in, used_for,
                    box_count, case_count, composition_class, non_corrosive,
                    lead_free, temperature_claim, primer_family, cup_thickness_in,
                    cup_hardness_class, pressure_tolerance_class,
                    ignition_strength_class, recommended_pressure_min_psi,
                    recommended_pressure_max_psi, cold_weather_suitability,
                    primer_sign_interpretation, evidence_level, reference_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            component_id = _require_lastrowid(cur)
            report["primers_added"] += 1
        else:
            cur.execute(
                """
                UPDATE primers
                SET type = coalesce(?, type),
                    size = coalesce(?, size),
                    quantity = coalesce(?, quantity),
                    cost_per_unit = coalesce(?, cost_per_unit),
                    notes = coalesce(?, notes),
                    product_line = coalesce(?, product_line),
                    part_number = coalesce(?, part_number),
                    source_kind = coalesce(?, source_kind),
                    manufacturer_source = coalesce(?, manufacturer_source),
                    match_grade = coalesce(?, match_grade),
                    magnum = coalesce(?, magnum),
                    ar_variant = coalesce(?, ar_variant),
                    nominal_diameter_in = coalesce(?, nominal_diameter_in),
                    used_for = coalesce(?, used_for),
                    box_count = coalesce(?, box_count),
                    case_count = coalesce(?, case_count),
                    composition_class = coalesce(?, composition_class),
                    non_corrosive = coalesce(?, non_corrosive),
                    lead_free = coalesce(?, lead_free),
                    temperature_claim = coalesce(?, temperature_claim),
                    primer_family = coalesce(?, primer_family),
                    cup_thickness_in = coalesce(?, cup_thickness_in),
                    cup_hardness_class = coalesce(?, cup_hardness_class),
                    pressure_tolerance_class = coalesce(?, pressure_tolerance_class),
                    ignition_strength_class = coalesce(?, ignition_strength_class),
                    recommended_pressure_min_psi = coalesce(?, recommended_pressure_min_psi),
                    recommended_pressure_max_psi = coalesce(?, recommended_pressure_max_psi),
                    cold_weather_suitability = coalesce(?, cold_weather_suitability),
                    primer_sign_interpretation = coalesce(?, primer_sign_interpretation),
                    evidence_level = coalesce(?, evidence_level),
                    reference_source = coalesce(?, reference_source)
                WHERE id = ?
                """,
                payload[2:] + (existing_id,),
            )
            component_id = existing_id
            report["primers_updated"] += 1

        lot_number = str(row.get("lot_number") or "").strip() or _extract_lot_number(
            row.get("raw_json")
        )
        if _ensure_component_lot(
            cur,
            "primers",
            component_id,
            lot_number,
            "seed_import",
            row.get("reference_source") or row.get("source_label") or "",
        ):
            report["lots_added"] += 1

    for row in components.get("cases", []):
        existing_id = _find_existing_case(cur, row)
        payload = (
            row.get("name"),
            row.get("manufacturer"),
            row.get("caliber"),
            row.get("material"),
            _safe_int(row.get("quantity")),
            _safe_int(row.get("times_fired")),
            row.get("last_annealed"),
            _safe_int(row.get("needs_annealing")),
            row.get("notes"),
            row.get("lot_number"),
            row.get("purchase_date"),
            _safe_float(row.get("case_capacity_gr_h2o")),
            _safe_float(row.get("avg_weight_gr")),
            row.get("wall_thickness"),
            _safe_float(row.get("neck_thickness_mm")),
            _safe_int(row.get("retired_quantity")),
            row.get("last_trimmed_date"),
            _safe_float(row.get("trim_length_mm")),
            _safe_int(row.get("primer_pocket_uniformed")),
            _safe_int(row.get("flash_hole_deburred")),
        )
        if existing_id is None:
            cur.execute(
                """
                INSERT INTO cases(
                    name, manufacturer, caliber, material, quantity, times_fired,
                    last_annealed, needs_annealing, notes, lot_number,
                    purchase_date, case_capacity_gr_h2o, avg_weight_gr,
                    wall_thickness, neck_thickness_mm, retired_quantity,
                    last_trimmed_date, trim_length_mm, primer_pocket_uniformed,
                    flash_hole_deburred
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            report["cases_added"] += 1
        else:
            cur.execute(
                """
                UPDATE cases
                SET material = coalesce(?, material),
                    quantity = coalesce(?, quantity),
                    times_fired = coalesce(?, times_fired),
                    last_annealed = coalesce(?, last_annealed),
                    needs_annealing = coalesce(?, needs_annealing),
                    notes = coalesce(?, notes),
                    lot_number = coalesce(?, lot_number),
                    purchase_date = coalesce(?, purchase_date),
                    case_capacity_gr_h2o = coalesce(?, case_capacity_gr_h2o),
                    avg_weight_gr = coalesce(?, avg_weight_gr),
                    wall_thickness = coalesce(?, wall_thickness),
                    neck_thickness_mm = coalesce(?, neck_thickness_mm),
                    retired_quantity = coalesce(?, retired_quantity),
                    last_trimmed_date = coalesce(?, last_trimmed_date),
                    trim_length_mm = coalesce(?, trim_length_mm),
                    primer_pocket_uniformed = coalesce(?, primer_pocket_uniformed),
                    flash_hole_deburred = coalesce(?, flash_hole_deburred)
                WHERE id = ?
                """,
                payload[3:] + (existing_id,),
            )
            report["cases_updated"] += 1

    con.commit()
    con.close()
    return report


def sync_component_knowledge_base(
    kb_root: Path = DEFAULT_KB_ROOT,
    db_path: Path = DEFAULT_DB_PATH,
    export_root: Path = DEFAULT_EXPORT_ROOT,
) -> dict[str, int]:
    components = load_component_knowledge_base(kb_root, export_root=export_root)
    return merge_into_db(components, db_path=db_path)


def sync_reference_knowledge_base(
    kb_root: Path = DEFAULT_KB_ROOT,
    db_path: Path = DEFAULT_DB_PATH,
    export_root: Path = DEFAULT_EXPORT_ROOT,
) -> dict[str, Any]:
    component_report = sync_component_knowledge_base(
        kb_root=kb_root,
        db_path=db_path,
        export_root=export_root,
    )

    database = Database(str(db_path))
    try:
        cartridge_reports: dict[str, dict[str, int]] = {}
        total_added_or_updated = 0
        total_skipped = 0
        for filename in DEFAULT_CARTRIDGE_STANDARD_FILES:
            csv_path = kb_root / filename
            if not csv_path.exists():
                continue
            report = import_cartridge_standards_from_knowledge_base(database, csv_path)
            cartridge_reports[filename] = report
            total_added_or_updated += int(report.get("added_or_updated", 0))
            total_skipped += int(report.get("skipped", 0))
        database.conn.commit()
    finally:
        database.close()

    return {
        "components": component_report,
        "cartridge_standards": {
            "files": cartridge_reports,
            "added_or_updated": total_added_or_updated,
            "skipped": total_skipped,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb-root", type=Path, default=DEFAULT_KB_ROOT)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    args = parser.parse_args()

    report = sync_reference_knowledge_base(
        kb_root=args.kb_root,
        db_path=args.db_path,
        export_root=args.export_root,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
