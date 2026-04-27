from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _parse_float(value: Any) -> float | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def _parse_int(value: Any) -> int | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return int(float(text))
    except Exception:
        return None


def _safe_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _coalesce_text(*values: Any) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None


def _standard_body(raw: dict[str, Any], row: dict[str, Any]) -> str:
    for candidate in (
        raw.get("standard"),
        raw.get("method"),
        row.get("standard"),
    ):
        text = str(candidate or "").strip()
        if not text:
            continue
        upper = text.upper()
        if "CIP" in upper:
            return "CIP"
        if "SAAMI" in upper:
            return "SAAMI"
        if "NATO" in upper:
            return "NATO"
        if "USER" in upper:
            return "USER"
    return str(row.get("standard") or "").strip() or "REFERENCE"


def _classify_standard_source(
    raw: dict[str, Any], standard_body: str
) -> tuple[str, str]:
    origin = str(raw.get("origin") or "").strip().lower()
    has_cip_pdf = bool(str(raw.get("cippdf") or "").strip())

    if standard_body == "CIP" and (has_cip_pdf or "cip-bobp.org" in origin):
        return "official_cip", "official_standard"
    if standard_body == "SAAMI":
        return "official_saami", "official_standard"
    if standard_body == "NATO":
        return "official_nato", "official_standard"
    if standard_body == "USER":
        return "user_measurement", "user_reference"
    return "reference_snapshot", "imported_reference"


def _build_payload(row: dict[str, Any]) -> dict[str, Any]:
    raw = _safe_json(row.get("raw_json"))
    caliber_name = _coalesce_text(
        raw.get("cipname"),
        row.get("caliber_name"),
        row.get("name"),
    )
    standard_body = _coalesce_text(row.get("standard_body")) or _standard_body(raw, row)
    source_kind, evidence_level = _classify_standard_source(raw, standard_body)
    source_kind = _coalesce_text(row.get("source_kind"), source_kind) or source_kind
    evidence_level = (
        _coalesce_text(row.get("evidence_level"), evidence_level) or evidence_level
    )
    pressure_bar = _parse_float(
        raw.get("Pmax") or raw.get("pMaxZul") or row.get("max_pressure_bar")
    )
    pressure_psi = _parse_float(row.get("max_pressure_psi"))
    if pressure_bar is None and pressure_psi is not None:
        pressure_bar = pressure_psi / 14.5037738
    if pressure_psi is None and pressure_bar is not None:
        pressure_psi = pressure_bar * 14.5037738
    return {
        "caliber_name": caliber_name or "",
        "alt_name": _coalesce_text(raw.get("altname"), row.get("alt_name")),
        "standard_body": standard_body,
        "standard_label": _coalesce_text(
            row.get("standard_label"),
            row.get("standard"),
            raw.get("standard"),
            raw.get("method"),
        ),
        "pressure_method": _coalesce_text(
            row.get("pressure_method"),
            raw.get("method"),
        ),
        "max_pressure_bar": pressure_bar,
        "max_pressure_psi": pressure_psi,
        "oal_mm": _parse_float(raw.get("L6") or raw.get("oal") or row.get("oal_mm")),
        "case_length_mm": _parse_float(
            raw.get("L3") or raw.get("caselen") or row.get("case_length_mm")
        ),
        "case_capacity_ml": _parse_float(
            raw.get("casevol") or row.get("case_capacity_ml")
        ),
        "bullet_diameter_mm": _parse_float(
            raw.get("G1") or raw.get("Dz") or row.get("bullet_diameter_mm")
        ),
        "neck_diameter_mm": _parse_float(raw.get("E1") or row.get("neck_diameter_mm")),
        "shoulder_diameter_mm": _parse_float(
            raw.get("H1") or row.get("shoulder_diameter_mm")
        ),
        "base_diameter_mm": _parse_float(raw.get("P1") or row.get("base_diameter_mm")),
        "rim_diameter_mm": _parse_float(raw.get("R1") or row.get("rim_diameter_mm")),
        "freebore_mm": _parse_float(
            raw.get("c_Fe") or raw.get("Fe") or row.get("freebore_mm")
        ),
        "throat_angle_deg": _parse_float(
            raw.get("alpha") or raw.get("c_alpha") or row.get("throat_angle_deg")
        ),
        "drawing_pdf_url": _coalesce_text(
            raw.get("cippdf"), row.get("drawing_pdf_url")
        ),
        "drawing_image_url": _coalesce_text(row.get("drawing_image_url")),
        "source": _coalesce_text(row.get("source"), row.get("source_label")),
        "source_kind": source_kind,
        "evidence_level": evidence_level,
        "user_defined": (
            _parse_int(row.get("user_defined"))
            if row.get("user_defined") not in (None, "")
            else (1 if standard_body == "USER" else 0)
        ),
        "raw_json": json.dumps(raw, ensure_ascii=False) if raw else "",
        "notes": _coalesce_text(row.get("notes"))
        or "Importert fra internt referanseuttrekk.",
    }


def import_cartridge_standards_from_knowledge_base(
    db,
    csv_path: str | Path,
) -> dict[str, int]:
    path = Path(csv_path)
    counts = {"added_or_updated": 0, "skipped": 0}
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            payload = _build_payload(row)
            if not payload.get("caliber_name"):
                counts["skipped"] += 1
                continue
            db.upsert_cartridge_standard(payload)
            counts["added_or_updated"] += 1
    return counts
