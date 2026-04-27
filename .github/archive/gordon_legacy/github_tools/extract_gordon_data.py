from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
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


def _discover_component_xml_roots(
    source_root: Path,
    extra_roots: list[Path] | None = None,
    include_default_appdata: bool = True,
) -> list[Path]:
    roots: list[Path] = []
    candidates = [source_root]
    if source_root.name.lower() == "data":
        candidates.append(source_root.parent)
    if extra_roots:
        candidates.extend(extra_roots)
    if include_default_appdata:
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
    xml_paths: list[Path] = []
    seen: set[Path] = set()
    patterns = ("*.xml", "*.projectile", "*.propellant", "*.caliber")
    for root in roots:
        for pattern in patterns:
            for path in sorted(root.rglob(pattern)):
                if path in seen:
                    continue
                seen.add(path)
                xml_paths.append(path)
    return xml_paths


def _component_db_template() -> dict[str, list[dict[str, Any]]]:
    return {
        "bullets": [],
        "powders": [],
        "primers": [],
        "brass": [],
    }


def _load_component_database(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return _component_db_template()
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    merged = _component_db_template()
    for key in merged:
        value = data.get(key, []) if isinstance(data, dict) else []
        merged[key] = value if isinstance(value, list) else []
    return merged


def _save_component_database(path: Path, data: dict[str, list[dict[str, Any]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "meta": {"schema_version": "component_database.v1"},
                "data": data,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _next_id(records: list[dict[str, Any]]) -> int:
    max_id = 0
    for record in records:
        try:
            max_id = max(max_id, int(record.get("id", 0) or 0))
        except Exception:
            continue
    return max_id + 1


def _bullet_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("manufacturer") or "").strip().lower(),
        str(row.get("name") or "").strip().lower(),
        str(row.get("caliber") or "").strip().lower(),
        f"{float(row.get('weight') or 0.0):.3f}",
    )


def _powder_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("manufacturer") or "").strip().lower(),
        str(row.get("name") or "").strip().lower(),
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _extract_measurements(root: ET.Element, source_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    title = _decode(root.findtext(".//InnerBallistikInput/title"))
    for measurement in root.findall(".//Measurement"):
        measurement_title = _decode(measurement.get("title"))
        for charge in measurement.findall("charge"):
            charge_name = _decode(charge.get("name"))
            charge_value = _safe_float(charge.get("value"))
            for shot_index, shot in enumerate(charge.findall("shot"), start=1):
                rows.append(
                    {
                        "source_file": str(source_path),
                        "load_title": title,
                        "measurement_title": measurement_title,
                        "charge_name": charge_name,
                        "charge_value_kg": charge_value,
                        "shot_index": shot_index,
                        "velocity_mps": _safe_float(shot.get("velocity")),
                        "pressure_bar": _safe_float(shot.get("pressure")),
                    }
                )
    return rows


def _app_bullet_from_projectile(data: dict[str, Any], reference: str) -> dict[str, Any]:
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
        "weight": round(
            _safe_float(data.get("gmass") or data.get("mp"))
            * (15.4323584 if data.get("mp") else 1.0),
            3,
        ),
        "bc_g1": round(_safe_float(data.get("g1bc") or data.get("gBC0")), 3),
        "bc_g7": round(_safe_float(data.get("g7bc")), 3),
        "length": round(_mm_to_in(data.get("glen")), 3),
        "diameter": round(
            (
                _safe_float(data.get("caliber"))
                if str(data.get("caliber") or "").startswith(".")
                else _mm_to_in(data.get("Dbul") or data.get("gdia"))
            ),
            3,
        ),
        "type": data.get("type", ""),
        "notes": reference,
        "source": "local_component_pack",
    }


def _app_bullet_from_projectilefile(
    data: dict[str, Any], reference: str
) -> dict[str, Any]:
    return {
        "manufacturer": data.get("mname", ""),
        "name": data.get("pname", ""),
        "caliber": data.get("caliber", ""),
        "weight": round(_safe_float(data.get("gmass")), 3),
        "bc_g1": round(_safe_float(data.get("g1bc") or data.get("gBC0")), 3),
        "bc_g7": round(_safe_float(data.get("g7bc")), 3),
        "length": round(_mm_to_in(data.get("glen")), 3),
        "diameter": round(_mm_to_in(data.get("gdia")), 3),
        "type": data.get("type", ""),
        "notes": reference,
        "source": "local_component_pack",
    }


def _app_powder_from_propellant(data: dict[str, Any], reference: str) -> dict[str, Any]:
    density = _safe_float(data.get("pcd"))
    if density > 20:
        density = round(density / 1000.0, 3)
    return {
        "manufacturer": data.get("mname", ""),
        "name": data.get("pname", ""),
        "burn_rate": str(data.get("Ba") or "").strip(),
        "density": density,
        "best_for": "",
        "temp_stable": False,
        "notes": reference,
        "source": "local_component_pack",
    }


def _app_caliber_from_caliberfile(
    data: dict[str, Any], reference: str
) -> dict[str, Any]:
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
        "reference": reference,
    }


def _projectile_reference_row(data: dict[str, Any]) -> dict[str, Any]:
    projectile_name = str(data.get("ProjectileName") or "").strip()
    manufacturer = str(data.get("mname") or "").strip()
    product_name = str(data.get("pname") or "").strip()
    caliber_in = str(data.get("caliber") or "").strip()
    if projectile_name and (not manufacturer or not product_name or not caliber_in):
        parts = [part.strip() for part in projectile_name.split(",")]
        if not manufacturer and parts:
            manufacturer = parts[0]
        if not product_name and len(parts) > 1:
            product_name = parts[1]
        if not caliber_in and len(parts) > 2:
            caliber_in = parts[2]

    return {
        "source_file": data.get("source_file", ""),
        "load_title": data.get("load_title", ""),
        "manufacturer": manufacturer,
        "product_name": product_name or projectile_name,
        "lotid": data.get("lotid", ""),
        "caliber_in": caliber_in,
        "diameter_mm": round(_safe_float(data.get("gdia") or data.get("Dbul")), 3),
        "length_mm": round(_safe_float(data.get("glen") or data.get("lP")), 3),
        "mass_gr": round(
            _safe_float(data.get("gmass") or data.get("mp"))
            * (15.4323584 if data.get("mp") else 1.0),
            3,
        ),
        "pressure_bar": round(_safe_float(data.get("gpressure")), 3),
        "friction": round(_safe_float(data.get("gfriction")), 3),
        "depth_max_mm": round(_safe_float(data.get("gdepthmax")), 3),
        "g1_bc": round(_safe_float(data.get("g1bc") or data.get("gBC0")), 3),
        "g7_bc": round(_safe_float(data.get("g7bc")), 3),
        "ubcs": data.get("gUBCS", ""),
        "tail_type": data.get("gtailtype") or data.get("gTailType", ""),
        "tail_dia_a_mm": round(
            _safe_float(data.get("gtaildiaA") or data.get("gTailDiaA")), 3
        ),
        "tail_dia_b_mm": round(
            _safe_float(data.get("gtaildiaB") or data.get("gTailDiaB")), 3
        ),
        "tail_length_mm": round(_safe_float(data.get("gtailh")), 3),
        "type": data.get("type", ""),
        "mode": data.get("mode", ""),
        "status": data.get("status", ""),
        "origin": data.get("origin", ""),
        "descr": data.get("descr", ""),
        "cdate": data.get("cdate", ""),
        "cby": data.get("cby", ""),
        "mdate": data.get("mdate", ""),
        "mby": data.get("mby", ""),
    }


def _propellant_reference_row(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": data.get("source_file", ""),
        "load_title": data.get("load_title", ""),
        "manufacturer": data.get("mname", ""),
        "product_name": data.get("pname", ""),
        "lotid": data.get("lotid", ""),
        "Br": round(_safe_float(data.get("Br")), 4),
        "Bp": round(_safe_float(data.get("Bp")), 4),
        "Brp": round(_safe_float(data.get("Brp")), 4),
        "Ba": round(_safe_float(data.get("Ba")), 4),
        "Qex_kj_kg": round(_safe_float(data.get("Qex")), 4),
        "k": round(_safe_float(data.get("k")), 4),
        "eta": round(_safe_float(data.get("eta")), 4),
        "a0": round(_safe_float(data.get("a0")), 4),
        "a1": round(_safe_float(data.get("a1")), 4),
        "z1": round(_safe_float(data.get("z1")), 4),
        "z2": round(_safe_float(data.get("z2")), 4),
        "pc_kg_m3": round(_safe_float(data.get("pc")), 4),
        "pcd_kg_m3": round(_safe_float(data.get("pcd")), 4),
        "pt_c": round(_safe_float(data.get("pt")), 4),
        "tcc": round(_safe_float(data.get("tcc")), 4),
        "tch": round(_safe_float(data.get("tch")), 4),
        "Lp": round(_safe_float(data.get("Lp")), 4),
        "Lr": round(_safe_float(data.get("Lr")), 4),
        "L01": round(_safe_float(data.get("L01")), 4),
        "L02": round(_safe_float(data.get("L02")), 4),
        "L03": round(_safe_float(data.get("L03")), 4),
        "L04": round(_safe_float(data.get("L04")), 4),
        "L05": round(_safe_float(data.get("L05")), 4),
        "L06": round(_safe_float(data.get("L06")), 4),
        "L07": round(_safe_float(data.get("L07")), 4),
        "L08": round(_safe_float(data.get("L08")), 4),
        "L09": round(_safe_float(data.get("L09")), 4),
        "Qlty": round(_safe_float(data.get("Qlty")), 4),
        "type": data.get("type", ""),
        "mode": data.get("mode", ""),
        "status": data.get("status", ""),
        "origin": data.get("origin", ""),
        "descr": data.get("descr", ""),
        "cdate": data.get("cdate", ""),
        "cby": data.get("cby", ""),
        "mdate": data.get("mdate", ""),
        "mby": data.get("mby", ""),
    }


def _caliber_reference_row(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": data.get("source_file", ""),
        "load_title": data.get("load_title", ""),
        "cipname": data.get("cipname") or data.get("CaliberName", ""),
        "altname": data.get("altname", ""),
        "standard": data.get("standard") or data.get("method", ""),
        "ciporigin": data.get("ciporigin", ""),
        "ciptype": data.get("ciptype", ""),
        "cipdate": data.get("cipdate", ""),
        "ciprevdate": data.get("ciprevdate", ""),
        "cippdf": data.get("cippdf", ""),
        "L3_case_length_mm": round(
            _safe_float(data.get("L3") or data.get("caselen")), 3
        ),
        "L6_oal_mm": round(_safe_float(data.get("L6") or data.get("oal")), 3),
        "V_case_capacity": round(_safe_float(data.get("V") or data.get("casevol")), 3),
        "Pmax_bar": round(_safe_float(data.get("Pmax") or data.get("pMaxZul")), 3),
        "G1_bullet_diameter_mm": round(
            _safe_float(data.get("G1") or data.get("Dz")), 3
        ),
        "H1_mm": round(_safe_float(data.get("H1")), 3),
        "H2_mm": round(_safe_float(data.get("H2")), 3),
        "R_mm": round(_safe_float(data.get("R")), 3),
        "R1_mm": round(_safe_float(data.get("R1")), 3),
        "R3_mm": round(_safe_float(data.get("R3")), 3),
        "E_mm": round(_safe_float(data.get("E")), 3),
        "E1_mm": round(_safe_float(data.get("E1")), 3),
        "L3G_mm": round(_safe_float(data.get("L3G")), 3),
        "PK_bar": round(_safe_float(data.get("PK")), 3),
        "PE_bar": round(_safe_float(data.get("PE")), 3),
        "EE": round(_safe_float(data.get("EE")), 3),
        "M": data.get("M", ""),
        "origin": data.get("origin", ""),
        "descr": data.get("descr", ""),
        "cdate": data.get("cdate", ""),
        "cby": data.get("cby", ""),
        "mdate": data.get("mdate", ""),
        "mby": data.get("mby", ""),
    }


def extract_gordon_data(
    source_root: Path,
    extra_component_roots: list[Path] | None = None,
    include_default_appdata: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    search_root = source_root
    grtload_files = sorted(search_root.rglob("*.grtload"))
    if not grtload_files and search_root.name.lower() == "data":
        search_root = search_root.parent
        grtload_files = sorted(search_root.rglob("*.grtload"))

    raw_projectiles: list[dict[str, Any]] = []
    raw_propellants: list[dict[str, Any]] = []
    raw_calibers: list[dict[str, Any]] = []
    measurements: list[dict[str, Any]] = []
    bullets_for_app: list[dict[str, Any]] = []
    powders_for_app: list[dict[str, Any]] = []
    calibers_for_reference: list[dict[str, Any]] = []
    projectile_reference_rows: list[dict[str, Any]] = []
    propellant_reference_rows: list[dict[str, Any]] = []
    caliber_reference_rows: list[dict[str, Any]] = []

    for component_xml in _iter_component_xml_files(
        _discover_component_xml_roots(
            search_root,
            extra_component_roots,
            include_default_appdata=include_default_appdata,
        )
    ):
        root = _read_xml(component_xml)
        if root is None:
            continue
        for node in root.findall(".//projectilefile"):
            data = _parse_var_block(node)
            data["source_file"] = str(component_xml)
            raw_projectiles.append(data)
            projectile_reference_rows.append(_projectile_reference_row(data))
            bullets_for_app.append(
                _app_bullet_from_projectilefile(
                    data,
                    f"Gordon component XML: {component_xml.name}",
                )
            )
        for node in root.findall(".//propellantfile"):
            data = _parse_var_block(node)
            data["source_file"] = str(component_xml)
            raw_propellants.append(data)
            propellant_reference_rows.append(_propellant_reference_row(data))
            powders_for_app.append(
                _app_powder_from_propellant(
                    data,
                    f"Gordon component XML: {component_xml.name}",
                )
            )
        for node in root.findall(".//caliberfile"):
            data = _parse_var_block(node)
            data["source_file"] = str(component_xml)
            raw_calibers.append(data)
            caliber_reference_rows.append(_caliber_reference_row(data))
            calibers_for_reference.append(
                _app_caliber_from_caliberfile(
                    data,
                    f"Gordon component XML: {component_xml.name}",
                )
            )

    for grtload in grtload_files:
        root = _read_xml(grtload)
        if root is None:
            continue

        title = _decode(root.findtext(".//InnerBallistikInput/title"))
        measurements.extend(_extract_measurements(root, grtload))

        for node in root.findall(".//projectile"):
            data = _parse_input_block(node)
            data["source_file"] = str(grtload)
            data["load_title"] = title
            raw_projectiles.append(data)
            projectile_reference_rows.append(_projectile_reference_row(data))
            bullets_for_app.append(
                _app_bullet_from_projectile(
                    data,
                    f"GRT load file: {grtload.name}",
                )
            )

        for node in root.findall(".//propellant"):
            data = _parse_input_block(node)
            data["source_file"] = str(grtload)
            data["load_title"] = title
            raw_propellants.append(data)
            propellant_reference_rows.append(_propellant_reference_row(data))
            powders_for_app.append(
                _app_powder_from_propellant(
                    data,
                    f"GRT load file: {grtload.name}",
                )
            )

        caliber = root.find(".//caliber")
        caliberfile = root.find(".//caliberfile")
        merged: dict[str, Any] = {}
        if caliber is not None:
            merged.update(_parse_input_block(caliber))
        if caliberfile is not None:
            merged.update(_parse_var_block(caliberfile))
        if merged:
            merged["source_file"] = str(grtload)
            merged["load_title"] = title
            raw_calibers.append(merged)
            caliber_reference_rows.append(_caliber_reference_row(merged))
            calibers_for_reference.append(
                _app_caliber_from_caliberfile(
                    merged,
                    f"GRT load file: {grtload.name}",
                )
            )

    return {
        "raw_projectiles": raw_projectiles,
        "raw_propellants": raw_propellants,
        "raw_calibers": raw_calibers,
        "measurements": measurements,
        "bullets_for_app": bullets_for_app,
        "powders_for_app": powders_for_app,
        "calibers_for_reference": calibers_for_reference,
        "projectile_reference_rows": projectile_reference_rows,
        "propellant_reference_rows": propellant_reference_rows,
        "caliber_reference_rows": caliber_reference_rows,
    }


def _dedupe_rows(rows: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    seen: set[Any] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        if kind == "bullet":
            key = _bullet_key(row)
        elif kind == "powder":
            key = _powder_key(row)
        else:
            key = tuple((k, str(v)) for k, v in sorted(row.items()))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def merge_into_component_database(
    component_db_path: Path,
    bullets: list[dict[str, Any]],
    powders: list[dict[str, Any]],
) -> dict[str, int]:
    data = _load_component_database(component_db_path)
    added = {"bullets": 0, "powders": 0}

    existing_bullet_keys = {_bullet_key(row) for row in data["bullets"]}
    next_bullet_id = _next_id(data["bullets"])
    for row in bullets:
        if not row.get("name"):
            continue
        key = _bullet_key(row)
        if key in existing_bullet_keys:
            continue
        merged = dict(row)
        merged["id"] = next_bullet_id
        next_bullet_id += 1
        data["bullets"].append(merged)
        existing_bullet_keys.add(key)
        added["bullets"] += 1

    existing_powder_keys = {_powder_key(row) for row in data["powders"]}
    next_powder_id = _next_id(data["powders"])
    for row in powders:
        if not row.get("name"):
            continue
        key = _powder_key(row)
        if key in existing_powder_keys:
            continue
        merged = dict(row)
        merged["id"] = next_powder_id
        next_powder_id += 1
        data["powders"].append(merged)
        existing_powder_keys.add(key)
        added["powders"] += 1

    _save_component_database(component_db_path, data)
    return added


def _normalize_pack_notes(
    rows: list[dict[str, Any]], note_text: str
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["notes"] = note_text
        item["source"] = "local_component_pack"
        normalized.append(item)
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--component-db", type=Path, required=True)
    args = parser.parse_args()

    extracted = extract_gordon_data(args.source_root)

    bullets = _dedupe_rows(extracted["bullets_for_app"], "bullet")
    powders = _dedupe_rows(extracted["powders_for_app"], "powder")
    calibers = _dedupe_rows(extracted["calibers_for_reference"], "caliber")
    bullets = _normalize_pack_notes(
        bullets,
        "Lokal standarddatapakke importert fra tilgjengelige komponentfiler.",
    )
    powders = _normalize_pack_notes(
        powders,
        "Lokal standarddatapakke importert fra tilgjengelige komponentfiler.",
    )

    output_root = args.output_root
    _write_csv(
        output_root / "gordon_extracted_projectiles_raw.csv",
        extracted["raw_projectiles"],
    )
    _write_csv(
        output_root / "gordon_extracted_propellants_raw.csv",
        extracted["raw_propellants"],
    )
    _write_csv(
        output_root / "gordon_extracted_calibers_raw.csv", extracted["raw_calibers"]
    )
    _write_csv(
        output_root / "gordon_projectile_reference.csv",
        extracted["projectile_reference_rows"],
    )
    _write_csv(
        output_root / "gordon_propellant_reference.csv",
        extracted["propellant_reference_rows"],
    )
    _write_csv(
        output_root / "gordon_caliber_reference_full.csv",
        extracted["caliber_reference_rows"],
    )
    _write_csv(
        output_root / "gordon_extracted_measurements.csv", extracted["measurements"]
    )
    _write_csv(output_root / "gordon_bullets_for_hjemmelading.csv", bullets)
    _write_csv(output_root / "gordon_powders_for_hjemmelading.csv", powders)
    _write_csv(output_root / "gordon_calibers_reference.csv", calibers)
    (output_root / "local_component_pack.json").write_text(
        json.dumps(
            {
                "meta": {
                    "schema_version": "component_database.v1",
                    "source": "local_component_pack",
                },
                "data": {
                    "bullets": bullets,
                    "powders": powders,
                    "calibers": calibers,
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    added = merge_into_component_database(args.component_db, bullets, powders)

    summary = {
        "source_root": str(args.source_root),
        "output_root": str(output_root),
        "raw_projectiles": len(extracted["raw_projectiles"]),
        "raw_propellants": len(extracted["raw_propellants"]),
        "raw_calibers": len(extracted["raw_calibers"]),
        "measurements": len(extracted["measurements"]),
        "unique_bullets_for_app": len(bullets),
        "unique_powders_for_app": len(powders),
        "unique_calibers_reference": len(calibers),
        "added_to_component_database": added,
        "note": "Gordon .db-filen var ikke lesbar som vanlig SQLite, så CSV-ene er bygd fra tilgjengelige XML/.grtload-kilder.",
    }
    (output_root / "gordon_extraction_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
