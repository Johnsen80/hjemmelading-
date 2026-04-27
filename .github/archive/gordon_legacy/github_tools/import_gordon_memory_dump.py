from __future__ import annotations

import csv
import json
import sqlite3
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading")
DB_PATH = PROJECT_ROOT / "data" / "reloading.db"
TMP_DIR = PROJECT_ROOT / ".github" / "tmp"
DEFAULT_DUMP = TMP_DIR / "gordon_8664_copy.dmp"
OUT_PROJECTILES = TMP_DIR / "gordon_memory_projectiles.csv"
OUT_PROPELLANTS = TMP_DIR / "gordon_memory_propellants.csv"
OUT_SUMMARY = TMP_DIR / "gordon_memory_import_summary.json"

PROJECTILE_COLUMNS = [
    "id",
    "mname",
    "pname",
    "lotid",
    "caliber",
    "gdia",
    "glen",
    "gmass",
    "gpressure",
    "gfriction",
    "gtaildiaA",
    "gtaildiaB",
    "gtailh",
    "gtailtype",
    "gdepthmax",
    "g1bc",
    "g7bc",
    "gUBCS",
    "cdate",
    "cby",
    "mdate",
    "mby",
    "type",
    "mode",
    "status",
    "origin",
    "descr",
    "imageUuid",
    "geloescht",
]

PROPELLANT_COLUMNS = [
    "id",
    "mname",
    "pname",
    "lotid",
    "Br",
    "Bp",
    "Brp",
    "Ba",
    "Qex",
    "k",
    "eta",
    "a0",
    "a1",
    "z1",
    "z2",
    "pc",
    "pcd",
    "pt",
    "tcc",
    "tch",
    "Lp",
    "Lr",
    "L01",
    "L02",
    "L03",
    "L04",
    "L05",
    "L06",
    "L07",
    "L08",
    "L09",
    "Qlty",
    "cdate",
    "cby",
    "mdate",
    "mby",
    "type",
    "mode",
    "status",
    "origin",
    "descr",
    "imageUuid",
    "imageDetailUuid",
    "geloescht",
]


def _read_varint(buf: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for index in range(9):
        current = buf[offset + index]
        if index == 8:
            return (value << 8) | current, 9
        value = (value << 7) | (current & 0x7F)
        if not (current & 0x80):
            return value, index + 1
    raise ValueError("invalid varint")


def _decode_serial(buf: bytes, offset: int, serial_type: int) -> tuple[Any, int]:
    if serial_type == 0:
        return None, offset
    if serial_type == 1:
        return int.from_bytes(buf[offset : offset + 1], "big", signed=True), offset + 1
    if serial_type == 2:
        return int.from_bytes(buf[offset : offset + 2], "big", signed=True), offset + 2
    if serial_type == 3:
        return int.from_bytes(buf[offset : offset + 3], "big", signed=True), offset + 3
    if serial_type == 4:
        return int.from_bytes(buf[offset : offset + 4], "big", signed=True), offset + 4
    if serial_type == 5:
        return int.from_bytes(buf[offset : offset + 6], "big", signed=True), offset + 6
    if serial_type == 6:
        return int.from_bytes(buf[offset : offset + 8], "big", signed=True), offset + 8
    if serial_type == 7:
        return struct.unpack(">d", buf[offset : offset + 8])[0], offset + 8
    if serial_type == 8:
        return 0, offset
    if serial_type == 9:
        return 1, offset
    if serial_type >= 12:
        size = (serial_type - 12) // 2
        raw = buf[offset : offset + size]
        if serial_type % 2 == 0:
            return raw, offset + size
        return raw.decode("utf-8", "ignore"), offset + size
    raise ValueError(f"unsupported serial type: {serial_type}")


def _is_projectile_row(values: list[Any]) -> bool:
    return (
        len(values) == len(PROJECTILE_COLUMNS)
        and isinstance(values[1], str)
        and isinstance(values[2], str)
        and isinstance(values[3], str)
        and isinstance(values[4], str)
        and isinstance(values[5], float)
    )


def _is_propellant_row(values: list[Any]) -> bool:
    return (
        len(values) == len(PROPELLANT_COLUMNS)
        and isinstance(values[1], str)
        and isinstance(values[2], str)
        and isinstance(values[3], str)
        and isinstance(values[4], float)
    )


@dataclass
class ParsedPage:
    kind: str
    rows: list[dict[str, Any]]


def _parse_candidate_page(data: bytes, start: int) -> ParsedPage | None:
    if start + 1024 > len(data) or data[start] != 0x0D:
        return None
    cell_count = int.from_bytes(data[start + 3 : start + 5], "big")
    cell_content_start = int.from_bytes(data[start + 5 : start + 7], "big")
    fragmented = data[start + 7]
    if not (0 < cell_count < 80 and 0 < cell_content_start <= 1024 and fragmented < 20):
        return None

    pointers: list[int] = []
    for index in range(cell_count):
        pointer = int.from_bytes(
            data[start + 8 + index * 2 : start + 10 + index * 2], "big"
        )
        if not (0 < pointer < 1024):
            return None
        pointers.append(pointer)

    projectile_rows: list[dict[str, Any]] = []
    propellant_rows: list[dict[str, Any]] = []
    for pointer in pointers:
        try:
            cell_offset = start + pointer
            _, payload_varint_size = _read_varint(data, cell_offset)
            rowid, rowid_varint_size = _read_varint(
                data, cell_offset + payload_varint_size
            )
            payload_start = cell_offset + payload_varint_size + rowid_varint_size
            header_size, header_size_varint = _read_varint(data, payload_start)
            if not (
                0 < header_size < 400 and payload_start + header_size <= start + 1024
            ):
                return None

            serial_types: list[int] = []
            header_offset = payload_start + header_size_varint
            while header_offset < payload_start + header_size:
                serial_type, consumed = _read_varint(data, header_offset)
                serial_types.append(serial_type)
                header_offset += consumed

            body_offset = payload_start + header_size
            values: list[Any] = []
            for serial_type in serial_types:
                value, body_offset = _decode_serial(data, body_offset, serial_type)
                values.append(value)

            if _is_projectile_row(values):
                row = dict(zip(PROJECTILE_COLUMNS, values))
                row["rowid"] = rowid
                projectile_rows.append(row)
            elif _is_propellant_row(values):
                row = dict(zip(PROPELLANT_COLUMNS, values))
                row["rowid"] = rowid
                propellant_rows.append(row)
            else:
                return None
        except Exception:
            return None

    if projectile_rows and not propellant_rows:
        return ParsedPage(kind="projectile", rows=projectile_rows)
    if propellant_rows and not projectile_rows:
        return ParsedPage(kind="propellant", rows=propellant_rows)
    return None


def extract_rows_from_dump(
    dump_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data = dump_path.read_bytes()
    projectile_rows: dict[int, dict[str, Any]] = {}
    propellant_rows: dict[int, dict[str, Any]] = {}
    start = 0
    while True:
        cursor = data.find(b"\r", start)
        if cursor < 0:
            break
        parsed = _parse_candidate_page(data, cursor)
        if parsed is None:
            start = cursor + 1
            continue
        if parsed.kind == "projectile":
            for row in parsed.rows:
                projectile_rows[row["rowid"]] = row
        else:
            for row in parsed.rows:
                propellant_rows[row["rowid"]] = row
        start = cursor + 1024
    return list(projectile_rows.values()), list(propellant_rows.values())


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> float | None:
    text = _safe_text(value)
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _upsert_snapshot(cur: sqlite3.Cursor, payload: dict[str, Any]) -> None:
    existing = cur.execute(
        """
        SELECT id
        FROM component_reference_snapshots
        WHERE source_system = ?
          AND component_type = ?
          AND coalesce(manufacturer, '') = coalesce(?, '')
          AND coalesce(model_name, '') = coalesce(?, '')
          AND coalesce(caliber, '') = coalesce(?, '')
          AND coalesce(lot_number, '') = coalesce(?, '')
          AND coalesce(source_file, '') = coalesce(?, '')
        LIMIT 1
        """,
        (
            payload["source_system"],
            payload["component_type"],
            payload.get("manufacturer"),
            payload.get("model_name"),
            payload.get("caliber"),
            payload.get("lot_number"),
            payload.get("source_file"),
        ),
    ).fetchone()
    if existing:
        cur.execute(
            """
            UPDATE component_reference_snapshots
            SET display_name = ?,
                weight_grains = ?,
                diameter_mm = ?,
                length_mm = ?,
                source_label = ?,
                evidence_level = ?,
                profile_json = ?,
                raw_json = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload.get("display_name"),
                payload.get("weight_grains"),
                payload.get("diameter_mm"),
                payload.get("length_mm"),
                payload.get("source_label"),
                payload.get("evidence_level"),
                payload.get("profile_json"),
                payload.get("raw_json"),
                existing[0],
            ),
        )
        return

    cur.execute(
        """
        INSERT INTO component_reference_snapshots (
            source_system,
            component_type,
            manufacturer,
            model_name,
            display_name,
            caliber,
            weight_grains,
            diameter_mm,
            length_mm,
            lot_number,
            source_file,
            source_label,
            evidence_level,
            profile_json,
            raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["source_system"],
            payload["component_type"],
            payload.get("manufacturer"),
            payload.get("model_name"),
            payload.get("display_name"),
            payload.get("caliber"),
            payload.get("weight_grains"),
            payload.get("diameter_mm"),
            payload.get("length_mm"),
            payload.get("lot_number"),
            payload.get("source_file"),
            payload.get("source_label"),
            payload.get("evidence_level"),
            payload.get("profile_json"),
            payload.get("raw_json"),
        ),
    )


def _bullet_snapshot_payload(row: dict[str, Any]) -> dict[str, Any]:
    manufacturer = _safe_text(row.get("mname")) or None
    model_name = _safe_text(row.get("pname")) or None
    profile = {
        "bc_g1": _safe_float(row.get("g1bc")),
        "bc_g7": _safe_float(row.get("g7bc")),
        "tail_type": _safe_text(row.get("gtailtype")) or None,
        "tail_dia_a_mm": _safe_float(row.get("gtaildiaA")),
        "tail_dia_b_mm": _safe_float(row.get("gtaildiaB")),
        "tail_height_mm": _safe_float(row.get("gtailh")),
        "ubcs": _safe_text(row.get("gUBCS")) or None,
        "source_mode": _safe_text(row.get("mode")) or None,
    }
    return {
        "source_system": "gordon_memory_dump",
        "component_type": "bullet",
        "manufacturer": manufacturer,
        "model_name": model_name,
        "display_name": f"{manufacturer or ''} {model_name or ''}".strip()
        or model_name,
        "caliber": _safe_text(row.get("caliber")) or None,
        "weight_grains": _safe_float(row.get("gmass")),
        "diameter_mm": _safe_float(row.get("gdia")),
        "length_mm": _safe_float(row.get("glen")),
        "lot_number": _safe_text(row.get("lotid")) or None,
        "source_file": str(DEFAULT_DUMP.name),
        "source_label": "Gordon memory dump",
        "evidence_level": "memory_extracted",
        "profile_json": json.dumps(profile, ensure_ascii=False),
        "raw_json": json.dumps(row, ensure_ascii=False),
    }


def _powder_snapshot_payload(row: dict[str, Any]) -> dict[str, Any]:
    manufacturer = _safe_text(row.get("mname")) or None
    model_name = _safe_text(row.get("pname")) or None
    profile = {
        "Br": _safe_float(row.get("Br")),
        "Bp": _safe_float(row.get("Bp")),
        "Brp": _safe_float(row.get("Brp")),
        "Ba": _safe_float(row.get("Ba")),
        "Qex": _safe_float(row.get("Qex")),
        "k": _safe_float(row.get("k")),
        "eta": _safe_float(row.get("eta")),
        "a0": _safe_float(row.get("a0")),
        "a1": _safe_float(row.get("a1")),
        "z1": _safe_float(row.get("z1")),
        "z2": _safe_float(row.get("z2")),
        "pc": _safe_float(row.get("pc")),
        "pcd": _safe_float(row.get("pcd")),
        "pt": _safe_float(row.get("pt")),
        "tcc": _safe_float(row.get("tcc")),
        "tch": _safe_float(row.get("tch")),
        "Lp": _safe_float(row.get("Lp")),
        "Lr": _safe_float(row.get("Lr")),
        "L01": _safe_float(row.get("L01")),
        "L02": _safe_float(row.get("L02")),
        "L03": _safe_float(row.get("L03")),
        "L04": _safe_float(row.get("L04")),
        "L05": _safe_float(row.get("L05")),
        "L06": _safe_float(row.get("L06")),
        "L07": _safe_float(row.get("L07")),
        "L08": _safe_float(row.get("L08")),
        "L09": _safe_float(row.get("L09")),
        "Qlty": _safe_float(row.get("Qlty")),
    }
    return {
        "source_system": "gordon_memory_dump",
        "component_type": "powder",
        "manufacturer": manufacturer,
        "model_name": model_name,
        "display_name": f"{manufacturer or ''} {model_name or ''}".strip()
        or model_name,
        "caliber": None,
        "weight_grains": None,
        "diameter_mm": None,
        "length_mm": None,
        "lot_number": _safe_text(row.get("lotid")) or None,
        "source_file": str(DEFAULT_DUMP.name),
        "source_label": "Gordon memory dump",
        "evidence_level": "memory_extracted",
        "profile_json": json.dumps(profile, ensure_ascii=False),
        "raw_json": json.dumps(row, ensure_ascii=False),
    }


def _upsert_bullet(cur: sqlite3.Cursor, row: dict[str, Any]) -> str:
    name = _safe_text(row.get("pname"))
    manufacturer = _safe_text(row.get("mname")) or None
    caliber = _safe_text(row.get("caliber"))
    weight = _safe_float(row.get("gmass"))
    if not name or not caliber or weight is None:
        return "skipped"
    existing = cur.execute(
        """
        SELECT id
        FROM bullets
        WHERE lower(coalesce(manufacturer, '')) = lower(coalesce(?, ''))
          AND lower(name) = lower(?)
          AND lower(caliber) = lower(?)
          AND abs(weight_grains - ?) < 0.0001
        LIMIT 1
        """,
        (manufacturer, name, caliber, weight),
    ).fetchone()
    if existing:
        cur.execute(
            """
            UPDATE bullets
            SET bc_g1 = coalesce(?, bc_g1),
                bc_g7 = coalesce(?, bc_g7),
                type = coalesce(?, type),
                source = ?,
                source_version = ?,
                external_ref = ?,
                source_kind = ?,
                evidence_level = ?,
                display_name = coalesce(?, display_name),
                source_label = coalesce(?, source_label),
                profile_json = coalesce(?, profile_json),
                raw_json = coalesce(?, raw_json)
            WHERE id = ?
            """,
            (
                _safe_float(row.get("g1bc")),
                _safe_float(row.get("g7bc")),
                _safe_text(row.get("type")) or None,
                "gordon_memory_import",
                "gordon_memory_import.v1",
                f"gordon_memory_dump|bullet|{manufacturer or ''}|{name}|{caliber}|{weight}",
                "gordon_memory_dump",
                "memory_extracted",
                f"{manufacturer or ''} {name}".strip() or name,
                "Gordon memory dump",
                json.dumps(
                    {
                        "diameter_mm": _safe_float(row.get("gdia")),
                        "length_mm": _safe_float(row.get("glen")),
                        "tail_dia_a_mm": _safe_float(row.get("gtaildiaA")),
                        "tail_dia_b_mm": _safe_float(row.get("gtaildiaB")),
                        "tail_height_mm": _safe_float(row.get("gtailh")),
                        "tail_type": _safe_text(row.get("gtailtype")) or None,
                        "ubcs": _safe_text(row.get("gUBCS")) or None,
                    },
                    ensure_ascii=False,
                ),
                json.dumps(row, ensure_ascii=False),
                existing[0],
            ),
        )
        return "updated"

    cur.execute(
        """
        INSERT INTO bullets (
            name, manufacturer, caliber, weight_grains, bc_g1, bc_g7, type,
            notes, source, source_version, external_ref, source_kind,
            evidence_level, display_name, source_label, profile_json, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            manufacturer,
            caliber,
            weight,
            _safe_float(row.get("g1bc")),
            _safe_float(row.get("g7bc")),
            _safe_text(row.get("type")) or None,
            _safe_text(row.get("descr")) or "Imported from Gordon memory dump.",
            "gordon_memory_import",
            "gordon_memory_import.v1",
            f"gordon_memory_dump|bullet|{manufacturer or ''}|{name}|{caliber}|{weight}",
            "gordon_memory_dump",
            "memory_extracted",
            f"{manufacturer or ''} {name}".strip() or name,
            "Gordon memory dump",
            json.dumps(
                {
                    "diameter_mm": _safe_float(row.get("gdia")),
                    "length_mm": _safe_float(row.get("glen")),
                    "tail_dia_a_mm": _safe_float(row.get("gtaildiaA")),
                    "tail_dia_b_mm": _safe_float(row.get("gtaildiaB")),
                    "tail_height_mm": _safe_float(row.get("gtailh")),
                    "tail_type": _safe_text(row.get("gtailtype")) or None,
                    "ubcs": _safe_text(row.get("gUBCS")) or None,
                },
                ensure_ascii=False,
            ),
            json.dumps(row, ensure_ascii=False),
        ),
    )
    return "added"


def _upsert_powder(cur: sqlite3.Cursor, row: dict[str, Any]) -> tuple[str, str]:
    name = _safe_text(row.get("pname"))
    manufacturer = _safe_text(row.get("mname")) or None
    if not name:
        return "skipped", "skipped"
    existing = cur.execute(
        """
        SELECT id
        FROM powder
        WHERE lower(coalesce(manufacturer, '')) = lower(coalesce(?, ''))
          AND lower(name) = lower(?)
        LIMIT 1
        """,
        (manufacturer, name),
    ).fetchone()
    if existing:
        powder_id = existing[0]
        cur.execute(
            """
            UPDATE powder
            SET type = coalesce(?, type),
                burn_rate = coalesce(?, burn_rate),
                source = ?,
                source_version = ?,
                external_ref = ?,
                source_kind = ?,
                evidence_level = ?,
                display_name = coalesce(?, display_name),
                source_label = coalesce(?, source_label),
                profile_json = coalesce(?, profile_json),
                raw_json = coalesce(?, raw_json)
            WHERE id = ?
            """,
            (
                _safe_text(row.get("type")) or None,
                _safe_text(row.get("Ba")) or None,
                "gordon_memory_import",
                "gordon_memory_import.v1",
                f"gordon_memory_dump|powder|{manufacturer or ''}|{name}",
                "gordon_memory_dump",
                "memory_extracted",
                f"{manufacturer or ''} {name}".strip() or name,
                "Gordon memory dump",
                json.dumps(_powder_snapshot_payload(row), ensure_ascii=False),
                json.dumps(row, ensure_ascii=False),
                powder_id,
            ),
        )
        powder_status = "updated"
    else:
        cur.execute(
            """
            INSERT INTO powder (
                name, manufacturer, type, burn_rate, notes, source, source_version,
                external_ref, source_kind, evidence_level, display_name, source_label,
                profile_json, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                manufacturer,
                _safe_text(row.get("type")) or None,
                _safe_text(row.get("Ba")) or None,
                _safe_text(row.get("descr")) or "Imported from Gordon memory dump.",
                "gordon_memory_import",
                "gordon_memory_import.v1",
                f"gordon_memory_dump|powder|{manufacturer or ''}|{name}",
                "gordon_memory_dump",
                "memory_extracted",
                f"{manufacturer or ''} {name}".strip() or name,
                "Gordon memory dump",
                json.dumps(_powder_snapshot_payload(row), ensure_ascii=False),
                json.dumps(row, ensure_ascii=False),
            ),
        )
        powder_id = cur.lastrowid
        powder_status = "added"

    model_existing = cur.execute(
        "SELECT id FROM powder_database WHERE powder_id = ? LIMIT 1", (powder_id,)
    ).fetchone()
    model_values = (
        _safe_float(row.get("Ba")),
        1,
        _safe_float(row.get("Ba")),
        int(
            (_safe_float(row.get("tcc")) or 0.0) == 0.0
            and (_safe_float(row.get("tch")) or 0.0) == 0.0
        ),
        _safe_float(row.get("Qex")),
        _safe_float(row.get("k")),
        _safe_float(row.get("a0")),
        _safe_float(row.get("z1")),
        _safe_float(row.get("z2")),
        _safe_float(row.get("eta")),
        _safe_float(row.get("pc")),
        _safe_float(row.get("pcd")),
        _safe_float(row.get("pt")),
        _safe_float(row.get("tcc")),
        _safe_float(row.get("tch")),
        "Imported Gordon powder model from memory dump.",
        "gordon_memory_dump",
        "memory_extracted",
        1,
        "gordon_memory_import.v1",
        f"gordon_memory_dump|powder_model|{manufacturer or ''}|{name}",
        json.dumps(row, ensure_ascii=False),
    )
    if model_existing:
        cur.execute(
            """
            UPDATE powder_database
            SET relative_burn_rate = coalesce(?, relative_burn_rate),
                quickload_available = ?,
                quickload_ba_value = coalesce(?, quickload_ba_value),
                temp_stable = ?,
                qex_kj_per_kg = coalesce(?, qex_kj_per_kg),
                k_ratio = coalesce(?, k_ratio),
                a0 = coalesce(?, a0),
                z1 = coalesce(?, z1),
                z2 = coalesce(?, z2),
                eta_cm3_per_kg = coalesce(?, eta_cm3_per_kg),
                pc_kg_m3 = coalesce(?, pc_kg_m3),
                pcd_kg_m3 = coalesce(?, pcd_kg_m3),
                pt_c = coalesce(?, pt_c),
                tcc = coalesce(?, tcc),
                tch = coalesce(?, tch),
                notes = ?,
                data_source = ?,
                validation_status = ?,
                usable_for_simulation = ?,
                source_version = ?,
                external_ref = ?,
                raw_json = ?
            WHERE powder_id = ?
            """,
            model_values + (powder_id,),
        )
        model_status = "updated"
    else:
        cur.execute(
            """
            INSERT INTO powder_database (
                powder_id, relative_burn_rate, quickload_available, quickload_ba_value,
                temp_stable, qex_kj_per_kg, k_ratio, a0, z1, z2, eta_cm3_per_kg,
                pc_kg_m3, pcd_kg_m3, pt_c, tcc, tch, notes, data_source,
                validation_status, usable_for_simulation, source_version, external_ref, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (powder_id,) + model_values,
        )
        model_status = "added"
    return powder_status, model_status


def import_into_library(
    projectiles: list[dict[str, Any]], propellants: list[dict[str, Any]], db_path: Path
) -> dict[str, int]:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    report = {
        "snapshot_bullets": 0,
        "snapshot_powders": 0,
        "library_bullets_added": 0,
        "library_bullets_updated": 0,
        "library_bullets_skipped": 0,
        "library_powders_added": 0,
        "library_powders_updated": 0,
        "library_powders_skipped": 0,
        "powder_models_added": 0,
        "powder_models_updated": 0,
    }
    for row in projectiles:
        _upsert_snapshot(cur, _bullet_snapshot_payload(row))
        report["snapshot_bullets"] += 1
        status = _upsert_bullet(cur, row)
        if status == "added":
            report["library_bullets_added"] += 1
        elif status == "updated":
            report["library_bullets_updated"] += 1
        else:
            report["library_bullets_skipped"] += 1

    for row in propellants:
        _upsert_snapshot(cur, _powder_snapshot_payload(row))
        report["snapshot_powders"] += 1
        powder_status, model_status = _upsert_powder(cur, row)
        if powder_status == "added":
            report["library_powders_added"] += 1
        elif powder_status == "updated":
            report["library_powders_updated"] += 1
        else:
            report["library_powders_skipped"] += 1
        if model_status == "added":
            report["powder_models_added"] += 1
        elif model_status == "updated":
            report["powder_models_updated"] += 1

    con.commit()
    con.close()
    return report


def main() -> None:
    if not DEFAULT_DUMP.exists():
        raise SystemExit(f"Missing dump file: {DEFAULT_DUMP}")
    projectiles, propellants = extract_rows_from_dump(DEFAULT_DUMP)
    projectiles.sort(key=lambda row: int(row.get("rowid") or 0))
    propellants.sort(key=lambda row: int(row.get("rowid") or 0))
    _write_csv(OUT_PROJECTILES, projectiles, PROJECTILE_COLUMNS + ["rowid"])
    _write_csv(OUT_PROPELLANTS, propellants, PROPELLANT_COLUMNS + ["rowid"])
    report = import_into_library(projectiles, propellants, DB_PATH)
    report.update(
        {
            "dump_file": str(DEFAULT_DUMP),
            "projectiles_extracted": len(projectiles),
            "propellants_extracted": len(propellants),
            "projectiles_csv": str(OUT_PROJECTILES),
            "propellants_csv": str(OUT_PROPELLANTS),
            "db_path": str(DB_PATH),
        }
    )
    OUT_SUMMARY.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
