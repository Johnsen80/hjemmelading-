from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_gordon_xml_rows(path: Path, node_name: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    tree = ET.parse(path)
    rows: list[dict[str, Any]] = []
    source_file = path.name
    for entry in tree.findall(f".//{node_name}"):
        row: dict[str, Any] = {"source_file": source_file}
        for var_node in entry.findall("var"):
            key = str(var_node.attrib.get("name") or "").strip()
            if not key:
                continue
            row[key] = str(var_node.attrib.get("value") or "").strip()
        rows.append(row)
    return rows


def _read_projectile_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        return _read_csv_rows(path)
    return _read_gordon_xml_rows(path, "projectilefile")


def _read_propellant_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        return _read_csv_rows(path)
    return _read_gordon_xml_rows(path, "propellantfile")


def _read_caliber_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        return _read_csv_rows(path)
    return _read_gordon_xml_rows(path, "caliberfile")


def _safe_float(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _normalize_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _projectile_snapshot_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    manufacturer = _normalize_text(row.get("mname"))
    model_name = _normalize_text(row.get("pname"))
    display_name = (
        _normalize_text(row.get("ProjectileName"))
        or " ".join(
            part for part in (manufacturer or "", model_name or "") if part
        ).strip()
    )
    caliber = _normalize_text(row.get("caliber"))
    if not display_name:
        return None

    profile = {
        "bc_g1": _safe_float(row.get("g1bc")),
        "bc_g7": _safe_float(row.get("g7bc")),
        "tail_type": _normalize_text(row.get("gTailType") or row.get("gtailtype")),
        "tail_dia_a_mm": _safe_float(row.get("gTailDiaA") or row.get("gtaildiaA")),
        "tail_dia_b_mm": _safe_float(row.get("gTailDiaB") or row.get("gtaildiaB")),
        "tail_height_mm": _safe_float(row.get("gtailh")),
        "ubcs": _normalize_text(row.get("gUBCS")),
        "source_mode": _normalize_text(row.get("mode")),
        "source_title": _normalize_text(row.get("load_title")),
    }
    raw_json = json.dumps(row, ensure_ascii=False)
    return {
        "source_system": "gordon_readable",
        "component_type": "bullet",
        "manufacturer": manufacturer,
        "model_name": model_name or display_name,
        "display_name": display_name,
        "caliber": caliber,
        "weight_grains": _safe_float(row.get("gmass")),
        "diameter_mm": _safe_float(row.get("Dbul") or row.get("gdia")),
        "length_mm": _safe_float(row.get("glen")),
        "lot_number": _normalize_text(row.get("lotid")),
        "source_file": _normalize_text(row.get("source_file")),
        "source_label": _normalize_text(row.get("load_title")),
        "evidence_level": "imported_snapshot",
        "profile_json": json.dumps(profile, ensure_ascii=False),
        "raw_json": raw_json,
    }


def _powder_snapshot_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    manufacturer = _normalize_text(row.get("mname"))
    model_name = _normalize_text(row.get("pname"))
    if not model_name:
        return None
    profile = {
        "Ba": _safe_float(row.get("Ba")),
        "Qex": _safe_float(row.get("Qex")),
        "k": _safe_float(row.get("k")),
        "a0": _safe_float(row.get("a0")),
        "z1": _safe_float(row.get("z1")),
        "z2": _safe_float(row.get("z2")),
        "eta": _safe_float(row.get("eta")),
        "pc": _safe_float(row.get("pc")),
        "pcd": _safe_float(row.get("pcd")),
        "pt": _safe_float(row.get("pt")),
        "tcc": _safe_float(row.get("tcc")),
        "tch": _safe_float(row.get("tch")),
        "mc": _safe_float(row.get("mc")),
        "laddercnt": _safe_float(row.get("laddercnt")),
        "imageUuid": _normalize_text(row.get("imageUuid")),
        "source_title": _normalize_text(row.get("load_title")),
    }
    return {
        "source_system": "gordon_readable",
        "component_type": "powder",
        "manufacturer": manufacturer,
        "model_name": model_name,
        "display_name": " ".join(
            part for part in (manufacturer or "", model_name) if part
        ).strip(),
        "caliber": _normalize_text(row.get("caliber")),
        "weight_grains": None,
        "diameter_mm": None,
        "length_mm": None,
        "lot_number": _normalize_text(row.get("lotid")),
        "source_file": _normalize_text(row.get("source_file")),
        "source_label": _normalize_text(row.get("load_title")),
        "evidence_level": "simulation_seed",
        "profile_json": json.dumps(profile, ensure_ascii=False),
        "raw_json": json.dumps(row, ensure_ascii=False),
    }


def _caliber_snapshot_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    display_name = _normalize_text(
        row.get("CaliberName") or row.get("cipname") or row.get("altname")
    )
    if not display_name:
        return None
    profile = {
        "standard": _normalize_text(row.get("standard") or row.get("method")),
        "cip_origin": _normalize_text(row.get("ciporigin")),
        "cip_type": _normalize_text(row.get("ciptype")),
        "cip_date": _normalize_text(row.get("cipdate")),
        "cip_rev_date": _normalize_text(row.get("ciprevdate")),
        "datasheet_url": _normalize_text(row.get("cippdf")),
        "L3_case_length_mm": _safe_float(row.get("caselen") or row.get("L3")),
        "L6_oal_mm": _safe_float(row.get("oal") or row.get("L6")),
        "V_case_capacity_ml": _safe_float(row.get("casevol") or row.get("V")),
        "Pmax_bar": _safe_float(row.get("pMaxZul") or row.get("Pmax")),
        "G1_bullet_diameter_mm": _safe_float(row.get("Dz") or row.get("G1")),
        "H1": _safe_float(row.get("H1")),
        "H2": _safe_float(row.get("H2")),
        "R": _safe_float(row.get("R")),
        "R1": _safe_float(row.get("R1")),
        "R3": _safe_float(row.get("R3")),
        "type": _normalize_text(row.get("type")),
        "origin": _normalize_text(row.get("origin")),
        "source_title": _normalize_text(row.get("load_title")),
    }
    return {
        "source_system": "gordon_readable",
        "component_type": "caliber",
        "manufacturer": _normalize_text(row.get("standard") or row.get("ciporigin")),
        "model_name": display_name,
        "display_name": display_name,
        "caliber": display_name,
        "weight_grains": None,
        "diameter_mm": _safe_float(row.get("Dz") or row.get("G1")),
        "length_mm": _safe_float(row.get("caselen") or row.get("L3")),
        "lot_number": None,
        "source_file": _normalize_text(row.get("source_file")),
        "source_label": _normalize_text(row.get("load_title")),
        "evidence_level": "reference_standard",
        "profile_json": json.dumps(profile, ensure_ascii=False),
        "raw_json": json.dumps(row, ensure_ascii=False),
    }


def import_gordon_readable_snapshots(
    db,
    projectiles_csv: str | Path,
    propellants_csv: str | Path,
    calibers_csv: str | Path | None = None,
) -> dict[str, int]:
    projectile_rows = _read_projectile_rows(Path(projectiles_csv))
    propellant_rows = _read_propellant_rows(Path(propellants_csv))
    caliber_rows = _read_caliber_rows(Path(calibers_csv)) if calibers_csv else []
    counts = {
        "bullets_added_or_updated": 0,
        "powders_added_or_updated": 0,
        "calibers_added_or_updated": 0,
    }

    for row in projectile_rows:
        payload = _projectile_snapshot_payload(row)
        if not payload:
            continue
        db.upsert_component_reference_snapshot(payload)
        counts["bullets_added_or_updated"] += 1

    for row in propellant_rows:
        payload = _powder_snapshot_payload(row)
        if not payload:
            continue
        db.upsert_component_reference_snapshot(payload)
        counts["powders_added_or_updated"] += 1

    for row in caliber_rows:
        payload = _caliber_snapshot_payload(row)
        if not payload:
            continue
        db.upsert_component_reference_snapshot(payload)
        counts["calibers_added_or_updated"] += 1

    return counts
