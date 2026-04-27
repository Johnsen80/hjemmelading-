"""
Export Gordon user XML files from AppData into normalized JSON.

This script targets the documented user backup files stored in
AppData\\Roaming\\GordonsReloadingTool, such as projectile.xml,
powder.xml and caliber.xml.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

APPDATA_DIR = Path(r"C:\Users\bjjoh\AppData\Roaming\GordonsReloadingTool")
DEFAULT_EXPORT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "gordon_temp_extract"
    / "gordon_user_components.json"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import Database  # noqa: E402

PROJECT_DB_PATH = PROJECT_ROOT / "data" / "reloading.db"


def _decode(value: str | None) -> str:
    return urllib.parse.unquote(str(value or "")).strip()


def _safe_float(value: str | None) -> float | None:
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def _parse_var_records(path: Path, record_tag: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    root = ET.parse(path).getroot()
    records: list[dict[str, str]] = []
    for node in root.findall(f".//{record_tag}"):
        row: dict[str, str] = {}
        for var in node.findall("./var"):
            row[var.get("name", "")] = _decode(var.get("value"))
        records.append(row)
    return records


def _map_projectile(row: dict[str, str]) -> dict[str, object]:
    return {
        "manufacturer": row.get("mname", ""),
        "name": row.get("pname", ""),
        "lotid": row.get("lotid", ""),
        "caliber": row.get("caliber", ""),
        "diameter_mm": _safe_float(row.get("gdia")),
        "length_mm": _safe_float(row.get("glen")),
        "weight_grains": _safe_float(row.get("gmass")),
        "bc_g1": _safe_float(row.get("g1bc")),
        "bc_g7": _safe_float(row.get("g7bc")),
        "ubcs": row.get("gUBCS", ""),
        "created_date": row.get("cdate", ""),
        "modified_date": row.get("mdate", ""),
        "mode": row.get("mode", ""),
        "description": row.get("descr", ""),
    }


def _map_powder(row: dict[str, str]) -> dict[str, object]:
    return {
        "manufacturer": row.get("mname", ""),
        "name": row.get("pname", ""),
        "lotid": row.get("lotid", ""),
        "burn_rate": _safe_float(row.get("Ba")),
        "energy_density": _safe_float(row.get("Qex")),
        "density": _safe_float(row.get("pcd")),
        "created_date": row.get("cdate", ""),
        "modified_date": row.get("mdate", ""),
        "mode": row.get("mode", ""),
        "description": row.get("descr", ""),
    }


def _map_caliber(row: dict[str, str]) -> dict[str, object]:
    return {
        "name": row.get("cipname", ""),
        "alt_name": row.get("altname", ""),
        "standard": row.get("standard", ""),
        "origin": row.get("ciporigin", ""),
        "case_length_mm": _safe_float(row.get("L3")),
        "max_pressure_bar": _safe_float(row.get("Pmax")),
        "case_capacity_gr_h2o": _safe_float(row.get("V")),
        "created_date": row.get("cdate", ""),
        "modified_date": row.get("mdate", ""),
        "mode": row.get("mode", ""),
        "description": row.get("descr", ""),
    }


def _mm_to_inch(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value / 25.4, 3)


def _find_existing_bullet(db: Database, row: dict[str, object]) -> dict | None:
    manufacturer = str(row.get("manufacturer") or "")
    name = str(row.get("name") or "")
    caliber = str(row.get("caliber") or "")
    weight = row.get("weight_grains")
    matches = db.execute_query(
        """
        SELECT id FROM bullets
        WHERE lower(coalesce(manufacturer, '')) = lower(?)
          AND lower(coalesce(name, '')) = lower(?)
          AND lower(coalesce(caliber, '')) = lower(?)
          AND abs(coalesce(weight_grains, 0) - ?) < 0.01
        """,
        (manufacturer, name, caliber, float(weight or 0)),
    )
    return matches[0] if matches else None


def _bullet_columns(db: Database) -> set[str]:
    rows = db.execute_query("PRAGMA table_info(bullets)")
    names = {str(row.get("name")) for row in rows if row.get("name")}
    return names


def import_projectiles_to_db(
    db: Database, projectiles: list[dict[str, object]]
) -> tuple[int, int]:
    imported = 0
    skipped = 0
    available_columns = _bullet_columns(db)
    for row in projectiles:
        existing = _find_existing_bullet(db, row)
        if existing:
            skipped += 1
            continue
        payload = {
            "manufacturer": row.get("manufacturer"),
            "name": row.get("name"),
            "caliber": row.get("caliber"),
            "weight_grains": row.get("weight_grains"),
            "bc_g1": row.get("bc_g1"),
            "bc_g7": row.get("bc_g7"),
            "notes": f"Gordon AppData lot={row.get('lotid', '')} ubcs={row.get('ubcs', '')}",
            "profile_json": json.dumps(
                {
                    "diameter_mm": row.get("diameter_mm"),
                    "length_mm": row.get("length_mm"),
                    "lotid": row.get("lotid"),
                    "ubcs": row.get("ubcs"),
                },
                ensure_ascii=False,
            ),
            "raw_json": json.dumps(row, ensure_ascii=False),
        }
        if "type" in available_columns:
            payload["type"] = "Gordon userfile"
        if "bullet_type" in available_columns:
            payload["bullet_type"] = "Gordon userfile"
        if "diameter_mm" in available_columns:
            payload["diameter_mm"] = row.get("diameter_mm")
        if "length_mm" in available_columns:
            payload["length_mm"] = row.get("length_mm")
        if "display_name" in available_columns:
            payload["display_name"] = (
                f"{row.get('manufacturer', '')} {row.get('name', '')}".strip()
            )
        if "source" in available_columns:
            payload["source"] = "Gordon AppData"
        if "source_kind" in available_columns:
            payload["source_kind"] = "user_xml"
        if "evidence_level" in available_columns:
            payload["evidence_level"] = "user-entered"
        if "source_label" in available_columns:
            payload["source_label"] = "Gordon user projectile.xml"
        payload = {
            key: value for key, value in payload.items() if key in available_columns
        }
        db.insert("bullets", payload)
        imported += 1
    return imported, skipped


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("export_path", nargs="?", default=str(DEFAULT_EXPORT))
    parser.add_argument("--import-db", action="store_true")
    args = parser.parse_args(argv[1:])

    export_path = Path(args.export_path)
    export_path.parent.mkdir(parents=True, exist_ok=True)

    projectiles = [
        _map_projectile(row)
        for row in _parse_var_records(APPDATA_DIR / "projectile.xml", "projectilefile")
    ]
    powders = [
        _map_powder(row)
        for row in _parse_var_records(APPDATA_DIR / "powder.xml", "propellantfile")
    ]
    calibers = [
        _map_caliber(row)
        for row in _parse_var_records(APPDATA_DIR / "caliber.xml", "caliberfile")
    ]

    payload = {
        "source_dir": str(APPDATA_DIR),
        "projectiles": projectiles,
        "powders": powders,
        "calibers": calibers,
    }
    export_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Source dir: {APPDATA_DIR}")
    print(f"Projectiles: {len(projectiles)}")
    print(f"Powders: {len(powders)}")
    print(f"Calibers: {len(calibers)}")
    print(f"Exported: {export_path}")

    if args.import_db:
        db = Database(db_path=str(PROJECT_DB_PATH))
        imported, skipped = import_projectiles_to_db(db, projectiles)
        print(f"Imported bullets to DB: {imported}")
        print(f"Skipped existing bullets: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
