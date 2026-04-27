from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _decode(value: Any) -> str:
    return urllib.parse.unquote(str(value or "")).strip()


def _safe_float(value: Any) -> float:
    text = _decode(value).replace(",", ".")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _mm_to_in(mm_value: Any) -> float:
    mm_float = _safe_float(mm_value)
    if mm_float <= 0:
        return 0.0
    return round(mm_float / 25.4, 3)


def _parse_input_block(node: ET.Element) -> dict[str, str]:
    return {
        str(item.get("name") or "").strip(): _decode(item.get("value"))
        for item in node.findall("input")
        if item.get("name")
    }


def _parse_var_block(node: ET.Element) -> dict[str, str]:
    return {
        str(item.get("name") or "").strip(): _decode(item.get("value"))
        for item in node.findall("var")
        if item.get("name")
    }


def _read_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except Exception:
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _discover_component_xml_roots(source_root: Path) -> list[Path]:
    roots: list[Path] = []
    candidates = [source_root, source_root.parent]
    appdata = os.getenv("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "GordonsReloadingTool")
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        if resolved.exists() and resolved not in roots:
            roots.append(resolved)
    return roots


def _iter_component_xml_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        for path in sorted(root.rglob("*.xml")):
            if path in seen:
                continue
            seen.add(path)
            files.append(path)
    return files


def _bullet_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("manufacturer") or "").strip().lower(),
        str(row.get("name") or "").strip().lower(),
        str(row.get("caliber") or "").strip().lower(),
        f"{float(row.get('weight_grains') or 0.0):.3f}",
    )


def _powder_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("manufacturer") or "").strip().lower(),
        str(row.get("name") or "").strip().lower(),
    )


def _caliber_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("name") or "").strip().lower(),
        f"{float(row.get('oal_mm') or 0.0):.3f}",
        f"{float(row.get('case_length_mm') or 0.0):.3f}",
    )


def _normalize_bullet_from_projectile(
    data: dict[str, Any], source_label: str
) -> dict[str, Any]:
    projectile_name = str(data.get("ProjectileName") or "").strip()
    manufacturer = str(data.get("mname") or "").strip()
    product_name = str(data.get("pname") or "").strip()
    caliber = str(data.get("caliber") or "").strip()
    if projectile_name and (not manufacturer or not product_name or not caliber):
        parts = [part.strip() for part in projectile_name.split(",")]
        if not manufacturer and parts:
            manufacturer = parts[0]
        if not product_name and len(parts) > 1:
            product_name = parts[1]
        if not caliber and len(parts) > 2:
            caliber = parts[2]
    return {
        "manufacturer": manufacturer,
        "name": product_name or projectile_name,
        "caliber": caliber,
        "weight_grains": round(
            _safe_float(data.get("gmass") or data.get("mp"))
            * (15.4323584 if data.get("mp") else 1.0),
            3,
        ),
        "bc_g1": round(_safe_float(data.get("g1bc") or data.get("gBC0")), 3),
        "bc_g7": round(_safe_float(data.get("g7bc")), 3),
        "length_in": round(_mm_to_in(data.get("glen")), 3),
        "diameter_in": round(
            (
                _safe_float(data.get("caliber"))
                if str(data.get("caliber") or "").startswith(".")
                else _mm_to_in(data.get("Dbul") or data.get("gdia"))
            ),
            3,
        ),
        "type": data.get("type", ""),
        "source_label": source_label,
        "raw_json": json.dumps(data, ensure_ascii=False, sort_keys=True),
    }


def _normalize_bullet_from_projectilefile(
    data: dict[str, Any], source_label: str
) -> dict[str, Any]:
    return {
        "manufacturer": data.get("mname", ""),
        "name": data.get("pname", ""),
        "caliber": data.get("caliber", ""),
        "weight_grains": round(_safe_float(data.get("gmass")), 3),
        "bc_g1": round(_safe_float(data.get("g1bc") or data.get("gBC0")), 3),
        "bc_g7": round(_safe_float(data.get("g7bc")), 3),
        "length_in": round(_mm_to_in(data.get("glen")), 3),
        "diameter_in": round(_mm_to_in(data.get("gdia")), 3),
        "type": data.get("type", ""),
        "source_label": source_label,
        "raw_json": json.dumps(data, ensure_ascii=False, sort_keys=True),
    }


def _normalize_powder(data: dict[str, Any], source_label: str) -> dict[str, Any]:
    density = _safe_float(data.get("pcd"))
    if density > 20:
        density = round(density / 1000.0, 3)
    return {
        "manufacturer": data.get("mname", ""),
        "name": data.get("pname", ""),
        "burn_rate": str(data.get("Ba") or "").strip(),
        "density": density,
        "temperature_c": round(_safe_float(data.get("pt")), 3),
        "source_label": source_label,
        "raw_json": json.dumps(data, ensure_ascii=False, sort_keys=True),
    }


def _normalize_caliber(data: dict[str, Any], source_label: str) -> dict[str, Any]:
    return {
        "name": data.get("CaliberName")
        or data.get("cipname")
        or data.get("altname", ""),
        "oal_mm": round(_safe_float(data.get("oal") or data.get("L6")), 3),
        "case_length_mm": round(_safe_float(data.get("caselen") or data.get("L3")), 3),
        "case_capacity_ml": round(_safe_float(data.get("casevol") or data.get("V")), 3),
        "max_pressure_bar": round(
            _safe_float(data.get("pMaxZul") or data.get("Pmax")), 3
        ),
        "bullet_diameter_mm": round(_safe_float(data.get("Dz") or data.get("G1")), 3),
        "standard": data.get("standard") or data.get("method", ""),
        "source_label": source_label,
        "raw_json": json.dumps(data, ensure_ascii=False, sort_keys=True),
    }


@dataclass
class SourceRow:
    source_id: int
    path: str
    file_name: str
    file_type: str
    sha256: str
    size_bytes: int


class KnowledgeBaseBuilder:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(database_path)
        self.conn.row_factory = sqlite3.Row
        self._source_by_key: dict[tuple[str, str], int] = {}
        self._bullet_ids: dict[tuple[str, str, str, str], int] = {}
        self._powder_ids: dict[tuple[str, str], int] = {}
        self._caliber_ids: dict[tuple[str, str, str], int] = {}

    def close(self) -> None:
        self.conn.close()

    def initialize(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            DROP TABLE IF EXISTS meta;
            DROP TABLE IF EXISTS sources;
            DROP TABLE IF EXISTS loads;
            DROP TABLE IF EXISTS measurements;
            DROP TABLE IF EXISTS raw_records;
            DROP TABLE IF EXISTS bullets;
            DROP TABLE IF EXISTS powders;
            DROP TABLE IF EXISTS calibers;

            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE sources (
                source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL
            );

            CREATE TABLE raw_records (
                raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                record_type TEXT NOT NULL,
                record_index INTEGER NOT NULL,
                load_title TEXT,
                record_json TEXT NOT NULL,
                FOREIGN KEY(source_id) REFERENCES sources(source_id)
            );

            CREATE TABLE bullets (
                bullet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                manufacturer TEXT,
                name TEXT,
                caliber TEXT,
                weight_grains REAL,
                bc_g1 REAL,
                bc_g7 REAL,
                length_in REAL,
                diameter_in REAL,
                type TEXT,
                source_label TEXT,
                raw_json TEXT NOT NULL
            );

            CREATE TABLE powders (
                powder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                manufacturer TEXT,
                name TEXT,
                burn_rate TEXT,
                density REAL,
                temperature_c REAL,
                source_label TEXT,
                raw_json TEXT NOT NULL
            );

            CREATE TABLE calibers (
                caliber_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                oal_mm REAL,
                case_length_mm REAL,
                case_capacity_ml REAL,
                max_pressure_bar REAL,
                bullet_diameter_mm REAL,
                standard TEXT,
                source_label TEXT,
                raw_json TEXT NOT NULL
            );

            CREATE TABLE loads (
                load_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                title TEXT,
                caliber_name TEXT,
                projectile_name TEXT,
                propellant_name TEXT,
                source_path TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                FOREIGN KEY(source_id) REFERENCES sources(source_id)
            );

            CREATE TABLE measurements (
                measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                load_id INTEGER NOT NULL,
                source_id INTEGER NOT NULL,
                measurement_title TEXT,
                charge_name TEXT,
                charge_value_kg REAL,
                shot_index INTEGER,
                velocity_mps REAL,
                pressure_bar REAL,
                raw_json TEXT NOT NULL,
                FOREIGN KEY(load_id) REFERENCES loads(load_id),
                FOREIGN KEY(source_id) REFERENCES sources(source_id)
            );
            """
        )
        self.conn.commit()

    def add_meta(self, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            (
                key,
                (
                    json.dumps(value, ensure_ascii=False)
                    if not isinstance(value, str)
                    else value
                ),
            ),
        )

    def add_source(self, path: Path, file_type: str) -> int:
        key = (str(path), file_type)
        if key in self._source_by_key:
            return self._source_by_key[key]
        cursor = self.conn.execute(
            """
            INSERT INTO sources(path, file_name, file_type, sha256, size_bytes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(path), path.name, file_type, _sha256(path), path.stat().st_size),
        )
        source_id = int(cursor.lastrowid)
        self._source_by_key[key] = source_id
        return source_id

    def add_raw_record(
        self,
        source_id: int,
        record_type: str,
        record_index: int,
        load_title: str | None,
        data: dict[str, Any],
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO raw_records(source_id, record_type, record_index, load_title, record_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                source_id,
                record_type,
                record_index,
                load_title,
                json.dumps(data, ensure_ascii=False, sort_keys=True),
            ),
        )

    def _upsert_bullet(self, row: dict[str, Any]) -> None:
        key = _bullet_key(row)
        if key in self._bullet_ids:
            return
        cursor = self.conn.execute(
            """
            INSERT INTO bullets(
                manufacturer, name, caliber, weight_grains, bc_g1, bc_g7,
                length_in, diameter_in, type, source_label, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("manufacturer"),
                row.get("name"),
                row.get("caliber"),
                row.get("weight_grains"),
                row.get("bc_g1"),
                row.get("bc_g7"),
                row.get("length_in"),
                row.get("diameter_in"),
                row.get("type"),
                row.get("source_label"),
                row.get("raw_json"),
            ),
        )
        self._bullet_ids[key] = int(cursor.lastrowid)

    def _upsert_powder(self, row: dict[str, Any]) -> None:
        key = _powder_key(row)
        if key in self._powder_ids:
            return
        cursor = self.conn.execute(
            """
            INSERT INTO powders(
                manufacturer, name, burn_rate, density, temperature_c, source_label, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("manufacturer"),
                row.get("name"),
                row.get("burn_rate"),
                row.get("density"),
                row.get("temperature_c"),
                row.get("source_label"),
                row.get("raw_json"),
            ),
        )
        self._powder_ids[key] = int(cursor.lastrowid)

    def _upsert_caliber(self, row: dict[str, Any]) -> None:
        key = _caliber_key(row)
        if key in self._caliber_ids:
            return
        cursor = self.conn.execute(
            """
            INSERT INTO calibers(
                name, oal_mm, case_length_mm, case_capacity_ml, max_pressure_bar,
                bullet_diameter_mm, standard, source_label, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("name"),
                row.get("oal_mm"),
                row.get("case_length_mm"),
                row.get("case_capacity_ml"),
                row.get("max_pressure_bar"),
                row.get("bullet_diameter_mm"),
                row.get("standard"),
                row.get("source_label"),
                row.get("raw_json"),
            ),
        )
        self._caliber_ids[key] = int(cursor.lastrowid)

    def add_component_xml_file(self, path: Path) -> dict[str, int]:
        root = _read_xml(path)
        if root is None:
            return {"projectilefile": 0, "propellantfile": 0, "caliberfile": 0}
        source_id = self.add_source(path, "component_xml")
        counts = {"projectilefile": 0, "propellantfile": 0, "caliberfile": 0}
        for record_index, node in enumerate(root.findall(".//projectilefile"), start=1):
            data = _parse_var_block(node)
            self.add_raw_record(source_id, "projectilefile", record_index, None, data)
            self._upsert_bullet(
                _normalize_bullet_from_projectilefile(
                    data, f"component_xml:{path.name}"
                )
            )
            counts["projectilefile"] += 1
        for record_index, node in enumerate(root.findall(".//propellantfile"), start=1):
            data = _parse_var_block(node)
            self.add_raw_record(source_id, "propellantfile", record_index, None, data)
            self._upsert_powder(_normalize_powder(data, f"component_xml:{path.name}"))
            counts["propellantfile"] += 1
        for record_index, node in enumerate(root.findall(".//caliberfile"), start=1):
            data = _parse_var_block(node)
            self.add_raw_record(source_id, "caliberfile", record_index, None, data)
            self._upsert_caliber(_normalize_caliber(data, f"component_xml:{path.name}"))
            counts["caliberfile"] += 1
        return counts

    def add_grtload_file(self, path: Path) -> dict[str, int]:
        root = _read_xml(path)
        if root is None:
            return {
                "projectile": 0,
                "propellant": 0,
                "caliber": 0,
                "caliberfile": 0,
                "measurement": 0,
                "shots": 0,
            }
        source_id = self.add_source(path, "grtload")
        title = _decode(root.findtext(".//InnerBallistikInput/title"))
        projectile_rows = [
            _parse_input_block(node) for node in root.findall(".//projectile")
        ]
        propellant_rows = [
            _parse_input_block(node) for node in root.findall(".//propellant")
        ]
        caliber_rows = [_parse_input_block(node) for node in root.findall(".//caliber")]
        caliberfile_rows = [
            _parse_var_block(node) for node in root.findall(".//caliberfile")
        ]
        summary_payload = {
            "title": title,
            "projectiles": projectile_rows,
            "propellants": propellant_rows,
            "calibers": caliber_rows,
            "caliberfiles": caliberfile_rows,
        }
        cursor = self.conn.execute(
            """
            INSERT INTO loads(source_id, title, caliber_name, projectile_name, propellant_name, source_path, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                title,
                (caliber_rows[0].get("CaliberName") if caliber_rows else "")
                or (caliberfile_rows[0].get("cipname") if caliberfile_rows else ""),
                projectile_rows[0].get("ProjectileName") if projectile_rows else "",
                propellant_rows[0].get("pname") if propellant_rows else "",
                str(path),
                json.dumps(summary_payload, ensure_ascii=False, sort_keys=True),
            ),
        )
        load_id = int(cursor.lastrowid)
        counts = {
            "projectile": 0,
            "propellant": 0,
            "caliber": 0,
            "caliberfile": 0,
            "measurement": 0,
            "shots": 0,
        }
        for record_index, data in enumerate(projectile_rows, start=1):
            self.add_raw_record(source_id, "projectile", record_index, title, data)
            self._upsert_bullet(
                _normalize_bullet_from_projectile(data, f"grtload:{path.name}")
            )
            counts["projectile"] += 1
        for record_index, data in enumerate(propellant_rows, start=1):
            self.add_raw_record(source_id, "propellant", record_index, title, data)
            self._upsert_powder(_normalize_powder(data, f"grtload:{path.name}"))
            counts["propellant"] += 1
        for record_index, data in enumerate(caliber_rows, start=1):
            self.add_raw_record(source_id, "caliber", record_index, title, data)
            self._upsert_caliber(_normalize_caliber(data, f"grtload:{path.name}"))
            counts["caliber"] += 1
        for record_index, data in enumerate(caliberfile_rows, start=1):
            self.add_raw_record(source_id, "caliberfile", record_index, title, data)
            self._upsert_caliber(_normalize_caliber(data, f"grtload:{path.name}"))
            counts["caliberfile"] += 1

        measurement_index = 0
        for measurement in root.findall(".//Measurement"):
            measurement_index += 1
            measurement_title = _decode(measurement.get("title"))
            measurement_payload = {"title": measurement_title, "charges": []}
            for charge in measurement.findall("charge"):
                charge_name = _decode(charge.get("name"))
                charge_value = _safe_float(charge.get("value"))
                charge_payload = {
                    "name": charge_name,
                    "value": charge_value,
                    "shots": [],
                }
                for shot_index, shot in enumerate(charge.findall("shot"), start=1):
                    shot_payload = {
                        "velocity": _safe_float(shot.get("velocity")),
                        "pressure": _safe_float(shot.get("pressure")),
                    }
                    charge_payload["shots"].append(shot_payload)
                    self.conn.execute(
                        """
                        INSERT INTO measurements(
                            load_id, source_id, measurement_title, charge_name, charge_value_kg,
                            shot_index, velocity_mps, pressure_bar, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            load_id,
                            source_id,
                            measurement_title,
                            charge_name,
                            charge_value,
                            shot_index,
                            shot_payload["velocity"],
                            shot_payload["pressure"],
                            json.dumps(
                                shot_payload, ensure_ascii=False, sort_keys=True
                            ),
                        ),
                    )
                    counts["shots"] += 1
                measurement_payload["charges"].append(charge_payload)
            self.add_raw_record(
                source_id, "measurement", measurement_index, title, measurement_payload
            )
            counts["measurement"] += 1
        return counts

    def export_table_to_csv(self, table_name: str, output_path: Path) -> None:
        rows = [dict(row) for row in self.conn.execute(f"SELECT * FROM {table_name}")]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            output_path.write_text("", encoding="utf-8")
            return
        fieldnames = list(rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    source_root = args.source_root
    output_root = args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    builder = KnowledgeBaseBuilder(output_root / "component_knowledge_base.db")
    builder.initialize()

    grtload_root = (
        source_root if source_root.name.lower() != "data" else source_root.parent
    )
    grtload_files = sorted(grtload_root.rglob("*.grtload"))
    component_xml_files = _iter_component_xml_files(
        _discover_component_xml_roots(source_root)
    )

    component_xml_counts: dict[str, int] = {
        "projectilefile": 0,
        "propellantfile": 0,
        "caliberfile": 0,
    }
    for path in component_xml_files:
        counts = builder.add_component_xml_file(path)
        for key, value in counts.items():
            component_xml_counts[key] += value

    grtload_counts: dict[str, int] = {
        "projectile": 0,
        "propellant": 0,
        "caliber": 0,
        "caliberfile": 0,
        "measurement": 0,
        "shots": 0,
    }
    for path in grtload_files:
        counts = builder.add_grtload_file(path)
        for key, value in counts.items():
            grtload_counts[key] += value

    builder.add_meta("source_root", str(source_root))
    builder.add_meta(
        "component_xml_roots",
        [str(path) for path in _discover_component_xml_roots(source_root)],
    )
    builder.add_meta("grtload_files", [str(path) for path in grtload_files])
    builder.add_meta("component_xml_files", [str(path) for path in component_xml_files])

    for table_name in [
        "sources",
        "raw_records",
        "bullets",
        "powders",
        "calibers",
        "loads",
        "measurements",
    ]:
        builder.export_table_to_csv(table_name, output_root / f"{table_name}.csv")

    summary = {
        "source_root": str(source_root),
        "output_root": str(output_root),
        "grtload_file_count": len(grtload_files),
        "component_xml_file_count": len(component_xml_files),
        "component_xml_counts": component_xml_counts,
        "grtload_counts": grtload_counts,
        "database_counts": {
            table_name: int(
                builder.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            )
            for table_name in [
                "sources",
                "raw_records",
                "bullets",
                "powders",
                "calibers",
                "loads",
                "measurements",
            ]
        },
        "note": "Databasen er frikoblet fra Gordon-formatet og inneholder kun data som var lesbare fra XML/grtload-kildene.",
        "unreadable_source_files": [
            str(source_root.parent / "GordonsReloadingTool.db")
        ],
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    builder.close()
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
