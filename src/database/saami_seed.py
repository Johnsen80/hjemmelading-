"""
SAAMI / CIP kartusj-standarder — seed-data for cartridge_standards-tabellen.

Alle mål i millimeter. Kilde: SAAMI og CIP publiserte standarder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .database import Database

# Felter: caliber_name, alt_name, standard_body, case_length_mm,
#         neck_diameter_mm, shoulder_diameter_mm, base_diameter_mm,
#         bullet_diameter_mm, max_pressure_bar, headspace_go_mm, notes
_SAAMI_DATA = [
    {
        "caliber_name": ".308 Winchester",
        "alt_name": "7.62×51 NATO",
        "standard_body": "SAAMI",
        "case_length_mm": 51.18,
        "neck_diameter_mm": 11.20,
        "shoulder_diameter_mm": 14.71,
        "base_diameter_mm": 12.01,
        "bullet_diameter_mm": 7.82,
        "max_pressure_bar": 4137,
        "headspace_go_mm": 41.50,  # SAAMI GO-gauge breech–datum
        "notes": "Mest brukte riflekaliber. SAAMI maks hylselengde 51.18 mm.",
    },
    {
        "caliber_name": ".223 Remington",
        "alt_name": "5.56×45 NATO",
        "standard_body": "SAAMI",
        "case_length_mm": 44.70,
        "neck_diameter_mm": 6.44,
        "shoulder_diameter_mm": 8.71,
        "base_diameter_mm": 9.58,
        "bullet_diameter_mm": 5.69,
        "max_pressure_bar": 5171,
        "headspace_go_mm": 37.18,
        "notes": "Brukt i AR-plattformer. Merk: 5.56 NATO-kammer er noe rommere.",
    },
    {
        "caliber_name": "6.5 Creedmoor",
        "alt_name": "6.5 CM",
        "standard_body": "SAAMI",
        "case_length_mm": 48.77,
        "neck_diameter_mm": 7.62,
        "shoulder_diameter_mm": 12.38,
        "base_diameter_mm": 12.01,
        "bullet_diameter_mm": 6.72,
        "max_pressure_bar": 4481,
        "headspace_go_mm": 39.14,
        "notes": "Populær presisjonskaliber. SAAMI 2008.",
    },
    {
        "caliber_name": ".30-06 Springfield",
        "alt_name": "7.62×63",
        "standard_body": "SAAMI",
        "case_length_mm": 63.35,
        "neck_diameter_mm": 11.20,
        "shoulder_diameter_mm": 14.72,
        "base_diameter_mm": 12.01,
        "bullet_diameter_mm": 7.82,
        "max_pressure_bar": 3965,
        "headspace_go_mm": 52.04,
        "notes": "Klassisk amerikanskrsk riflekaliber fra 1906.",
    },
    {
        "caliber_name": "6.5×55 Swedish",
        "alt_name": "6.5×55 SE",
        "standard_body": "CIP",
        "case_length_mm": 54.90,
        "neck_diameter_mm": 7.68,
        "shoulder_diameter_mm": 11.16,
        "base_diameter_mm": 12.20,
        "bullet_diameter_mm": 6.72,
        "max_pressure_bar": 3600,
        "headspace_go_mm": 45.72,
        "notes": "Skandinavisk klassiker. CIP-standard. Eldre gevær tåler lavere trykk.",
    },
    {
        "caliber_name": ".243 Winchester",
        "alt_name": "6mm Winchester",
        "standard_body": "SAAMI",
        "case_length_mm": 51.18,
        "neck_diameter_mm": 7.16,
        "shoulder_diameter_mm": 12.04,
        "base_diameter_mm": 12.01,
        "bullet_diameter_mm": 6.17,
        "max_pressure_bar": 4137,
        "headspace_go_mm": 41.50,
        "notes": "Nekkhalsing av .308 Winchester-hylse.",
    },
    {
        "caliber_name": ".300 Winchester Magnum",
        "alt_name": ".300 Win Mag",
        "standard_body": "SAAMI",
        "case_length_mm": 66.93,
        "neck_diameter_mm": 11.63,
        "shoulder_diameter_mm": 16.56,
        "base_diameter_mm": 13.97,
        "bullet_diameter_mm": 7.82,
        "max_pressure_bar": 4309,
        "headspace_go_mm": 54.86,
        "notes": "Beltekaliber. Beltet begrenser fremskuvet kammer.",
    },
    {
        "caliber_name": "7mm Remington Magnum",
        "alt_name": "7mm Rem Mag",
        "standard_body": "SAAMI",
        "case_length_mm": 63.35,
        "neck_diameter_mm": 8.13,
        "shoulder_diameter_mm": 14.39,
        "base_diameter_mm": 13.51,
        "bullet_diameter_mm": 7.24,
        "max_pressure_bar": 4309,
        "headspace_go_mm": 52.07,
        "notes": "Beltekaliber. Introdusert 1962.",
    },
    {
        "caliber_name": ".338 Lapua Magnum",
        "alt_name": "8.6×70 mm",
        "standard_body": "CIP",
        "case_length_mm": 69.20,
        "neck_diameter_mm": 9.60,
        "shoulder_diameter_mm": 19.56,
        "base_diameter_mm": 14.91,
        "bullet_diameter_mm": 8.59,
        "max_pressure_bar": 4200,
        "headspace_go_mm": 57.79,
        "notes": "Langtrekkende presisjons- og militærkaliber.",
    },
    {
        "caliber_name": ".270 Winchester",
        "alt_name": "",
        "standard_body": "SAAMI",
        "case_length_mm": 64.77,
        "neck_diameter_mm": 8.13,
        "shoulder_diameter_mm": 13.11,
        "base_diameter_mm": 12.01,
        "bullet_diameter_mm": 7.01,
        "max_pressure_bar": 4137,
        "headspace_go_mm": 52.96,
        "notes": "Nekkhalsing av .30-06.",
    },
    {
        "caliber_name": "7.62×39",
        "alt_name": "7.62 Soviet",
        "standard_body": "CIP",
        "case_length_mm": 38.64,
        "neck_diameter_mm": 8.69,
        "shoulder_diameter_mm": 10.36,
        "base_diameter_mm": 11.35,
        "bullet_diameter_mm": 7.92,
        "max_pressure_bar": 3550,
        "headspace_go_mm": 33.27,
        "notes": "AK-47/SKS-kaliber. CIP-standard.",
    },
    {
        "caliber_name": "9mm Luger",
        "alt_name": "9×19 Parabellum",
        "standard_body": "SAAMI",
        "case_length_mm": 19.15,
        "neck_diameter_mm": 9.65,
        "shoulder_diameter_mm": None,
        "base_diameter_mm": 9.93,
        "bullet_diameter_mm": 9.02,
        "max_pressure_bar": 2350,
        "headspace_go_mm": 19.05,
        "notes": "Rett hylse — headspace på hylsemunn.",
    },
    {
        "caliber_name": ".45 ACP",
        "alt_name": "11.43×23 mm",
        "standard_body": "SAAMI",
        "case_length_mm": 22.61,
        "neck_diameter_mm": 12.09,
        "shoulder_diameter_mm": None,
        "base_diameter_mm": 12.09,
        "bullet_diameter_mm": 11.43,
        "max_pressure_bar": 1310,
        "headspace_go_mm": 22.48,
        "notes": "1911-kaliber. Rett hylse.",
    },
    {
        "caliber_name": ".44 Magnum",
        "alt_name": "10.9×33R",
        "standard_body": "SAAMI",
        "case_length_mm": 32.77,
        "neck_diameter_mm": 11.43,
        "shoulder_diameter_mm": None,
        "base_diameter_mm": 13.49,
        "bullet_diameter_mm": 10.91,
        "max_pressure_bar": 2413,
        "headspace_go_mm": 32.64,
        "notes": "Revolver/karabin-kaliber.",
    },
    {
        "caliber_name": ".22 LR",
        "alt_name": "5.6×15R",
        "standard_body": "SAAMI",
        "case_length_mm": 15.11,
        "neck_diameter_mm": 5.74,
        "shoulder_diameter_mm": None,
        "base_diameter_mm": 5.74,
        "bullet_diameter_mm": 5.59,
        "max_pressure_bar": 1034,
        "headspace_go_mm": 15.06,
        "notes": "Randtenning. Lavt trykk.",
    },
]

# Name aliases for fuzzy matching (lowercase → canonical name)
_ALIASES: dict[str, str] = {
    "308": ".308 Winchester",
    "308 win": ".308 Winchester",
    "7.62x51": ".308 Winchester",
    "7.62×51": ".308 Winchester",
    "223": ".223 Remington",
    "223 rem": ".223 Remington",
    "5.56": ".223 Remington",
    "5.56x45": ".223 Remington",
    "5.56×45": ".223 Remington",
    "6.5cm": "6.5 Creedmoor",
    "6.5 cm": "6.5 Creedmoor",
    "creedmoor": "6.5 Creedmoor",
    "30-06": ".30-06 Springfield",
    ".30-06": ".30-06 Springfield",
    "7.62x63": ".30-06 Springfield",
    "6.5x55": "6.5×55 Swedish",
    "6.5×55": "6.5×55 Swedish",
    "6.5 swede": "6.5×55 Swedish",
    "243": ".243 Winchester",
    "243 win": ".243 Winchester",
    "300wm": ".300 Winchester Magnum",
    "300 wm": ".300 Winchester Magnum",
    ".300 win mag": ".300 Winchester Magnum",
    "7mm rem": "7mm Remington Magnum",
    "7mm mag": "7mm Remington Magnum",
    "338 lapua": ".338 Lapua Magnum",
    ".338": ".338 Lapua Magnum",
    "270": ".270 Winchester",
    "270 win": ".270 Winchester",
    "7.62x39": "7.62×39",
    "7.62×39": "7.62×39",
    "ak47": "7.62×39",
    "9mm": "9mm Luger",
    "9x19": "9mm Luger",
    "9×19": "9mm Luger",
    "45 acp": ".45 ACP",
    ".45": ".45 ACP",
    "44 mag": ".44 Magnum",
    "22lr": ".22 LR",
    "22 lr": ".22 LR",
}


def _entry_to_db_payload(entry: dict) -> dict:
    """Convert a seed entry to a payload compatible with cartridge_standards schema.

    Fields not in the schema (like headspace_go_mm) are stored in raw_json.
    """
    import json as _json

    extra = {}
    schema_fields = {
        "caliber_name",
        "alt_name",
        "standard_body",
        "standard_label",
        "max_pressure_bar",
        "max_pressure_psi",
        "oal_mm",
        "case_length_mm",
        "case_capacity_ml",
        "bullet_diameter_mm",
        "neck_diameter_mm",
        "shoulder_diameter_mm",
        "base_diameter_mm",
        "rim_diameter_mm",
        "freebore_mm",
        "throat_angle_deg",
        "source",
        "source_kind",
        "evidence_level",
        "user_defined",
        "notes",
    }
    payload: dict = {}
    for k, v in entry.items():
        if k in schema_fields:
            payload[k] = v
        else:
            extra[k] = v
    if extra:
        payload["raw_json"] = _json.dumps(extra, ensure_ascii=False)
    return payload


def seed_if_empty(db: "Database") -> int:
    """Seed SAAMI/CIP data into cartridge_standards if the table is empty.

    Returns the number of rows inserted.
    """
    try:
        rows = db.list_cartridge_standards()
        if rows:
            return 0  # Already seeded
    except Exception:
        return 0

    count = 0
    for entry in _SAAMI_DATA:
        try:
            payload = _entry_to_db_payload(entry)
            db.upsert_cartridge_standard(payload)
            count += 1
        except Exception:
            pass
    return count


def _enrich(row: dict) -> dict:
    """Unpack extra fields (like headspace_go_mm) from raw_json into the row dict."""
    import json as _json

    raw = row.get("raw_json")
    if raw:
        try:
            extra = _json.loads(raw)
            if isinstance(extra, dict):
                return {**row, **extra}
        except Exception:
            pass
    return row


def lookup(caliber_name: str, db: "Database") -> dict | None:
    """Return the best matching cartridge standard row for a caliber name.

    Tries exact match first, then alias lookup, then fuzzy substring.
    Returns None if no match found.
    """
    if not caliber_name or not caliber_name.strip():
        return None

    needle = caliber_name.strip()

    # 1. Exact match (case-insensitive)
    try:
        rows = db.list_cartridge_standards(caliber_name=needle)
        for r in rows:
            if r.get("caliber_name", "").casefold() == needle.casefold():
                return _enrich(r)
    except Exception:
        pass

    # 2. Alias lookup
    canonical = _ALIASES.get(needle.lower())
    if canonical:
        try:
            rows = db.list_cartridge_standards(caliber_name=canonical)
            for r in rows:
                if r.get("caliber_name", "").casefold() == canonical.casefold():
                    return _enrich(r)
        except Exception:
            pass

    # 3. Fuzzy substring — return first hit
    try:
        rows = db.list_cartridge_standards(caliber_name=needle)
        if rows:
            return _enrich(rows[0])
    except Exception:
        pass

    return None
