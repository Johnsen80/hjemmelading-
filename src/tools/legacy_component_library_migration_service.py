from __future__ import annotations

import json
from typing import Any


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> float | None:
    text = _normalize_text(value).replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _table_columns(database, table: str) -> set[str]:
    return {
        str(row.get("name") or "")
        for row in database.execute_query(f"PRAGMA table_info({table})")
    }


def _filter_payload(
    payload: dict[str, Any], allowed_columns: set[str]
) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key in allowed_columns}


def _bullet_caliber_from_diameter(diameter_in: float | None) -> str | None:
    if diameter_in is None:
        return None
    return f".{int(round(diameter_in * 1000)):03d}"


def _find_existing_bullet(
    database, manufacturer: str, name: str, caliber: str, weight_grains: float
) -> dict[str, Any] | None:
    rows = database.execute_query(
        """
        SELECT *
        FROM bullets
        WHERE lower(coalesce(manufacturer, '')) = lower(?)
          AND lower(name) = lower(?)
          AND lower(coalesce(caliber, '')) = lower(?)
          AND abs(coalesce(weight_grains, 0) - ?) < 0.0001
        ORDER BY id
        LIMIT 1
        """,
        (manufacturer, name, caliber, float(weight_grains)),
    )
    return dict(rows[0]) if rows else None


def _find_existing_powder(
    database, manufacturer: str, name: str
) -> dict[str, Any] | None:
    rows = database.execute_query(
        """
        SELECT *
        FROM powder
        WHERE lower(coalesce(manufacturer, '')) = lower(?)
          AND lower(name) = lower(?)
        ORDER BY id
        LIMIT 1
        """,
        (manufacturer, name),
    )
    return dict(rows[0]) if rows else None


def migrate_legacy_component_tables_into_library(
    database,
    source_version: str = "legacy_component_tables.v1",
) -> dict[str, int]:
    bullet_columns = _table_columns(database, "bullets")
    powder_columns = _table_columns(database, "powder")
    powder_model_columns = _table_columns(database, "powder_database")

    report = {
        "bullet_library_added": 0,
        "bullet_library_updated": 0,
        "bullet_library_skipped": 0,
        "powder_library_added": 0,
        "powder_library_updated": 0,
        "powder_library_skipped": 0,
        "powder_models_added": 0,
        "powder_models_updated": 0,
    }

    legacy_bullets = database.execute_query("SELECT * FROM bullet_data ORDER BY id")
    for legacy_row in legacy_bullets:
        row = dict(legacy_row)
        manufacturer = _normalize_text(row.get("manufacturer"))
        name = _normalize_text(row.get("name"))
        weight_grains = _safe_float(row.get("weight"))
        caliber = _bullet_caliber_from_diameter(_safe_float(row.get("diameter")))
        if not name or weight_grains is None or not caliber:
            report["bullet_library_skipped"] += 1
            continue

        raw_json = json.dumps(row, ensure_ascii=False)
        payload = _filter_payload(
            {
                "name": name,
                "manufacturer": manufacturer or None,
                "caliber": caliber,
                "weight_grains": weight_grains,
                "bc_g1": _safe_float(row.get("bc")),
                "bc_g7": None,
                "type": _normalize_text(row.get("type")) or None,
                "bullet_type": _normalize_text(row.get("type")) or None,
                "notes": _normalize_text(row.get("notes"))
                or "Migrated from legacy bullet_data table.",
                "source": "legacy_bullet_data",
                "source_kind": "legacy_catalog",
                "evidence_level": "catalog_seed",
                "source_version": source_version,
                "external_ref": f"legacy_bullet_data|{row.get('id')}",
                "external_id": str(row.get("id") or ""),
                "diameter_mm": (
                    (_safe_float(row.get("diameter")) or 0.0) * 25.4
                    if _safe_float(row.get("diameter")) is not None
                    else None
                ),
                "length_mm": (
                    (_safe_float(row.get("length")) or 0.0) * 25.4
                    if _safe_float(row.get("length")) is not None
                    else None
                ),
                "raw_json": raw_json,
            },
            bullet_columns,
        )
        existing = _find_existing_bullet(
            database, manufacturer, name, caliber, weight_grains
        )
        if existing:
            update_payload = dict(payload)
            for key in (
                "notes",
                "bc_g1",
                "bc_g7",
                "diameter_mm",
                "length_mm",
                "type",
                "bullet_type",
                "raw_json",
            ):
                if key in update_payload and existing.get(key) not in (
                    None,
                    "",
                    0,
                    0.0,
                ):
                    update_payload[key] = existing.get(key)
            database.update("bullets", update_payload, "id = ?", (int(existing["id"]),))
            report["bullet_library_updated"] += 1
        else:
            database.insert("bullets", payload)
            report["bullet_library_added"] += 1

    legacy_powders = database.execute_query("SELECT * FROM powder_data ORDER BY id")
    for legacy_row in legacy_powders:
        row = dict(legacy_row)
        manufacturer = _normalize_text(row.get("manufacturer"))
        name = _normalize_text(row.get("name"))
        if not name:
            report["powder_library_skipped"] += 1
            continue

        raw_json = json.dumps(row, ensure_ascii=False)
        payload = _filter_payload(
            {
                "name": name,
                "manufacturer": manufacturer or None,
                "type": _normalize_text(row.get("type")) or None,
                "burn_rate": _normalize_text(row.get("burn_rate")) or None,
                "notes": _normalize_text(row.get("notes"))
                or "Migrated from legacy powder_data table.",
                "source": "legacy_powder_data",
                "source_kind": "legacy_catalog",
                "evidence_level": "catalog_seed",
                "source_version": source_version,
                "external_ref": f"legacy_powder_data|{row.get('id')}",
                "external_id": str(row.get("id") or ""),
                "raw_json": raw_json,
            },
            powder_columns,
        )
        existing = _find_existing_powder(database, manufacturer, name)
        if existing:
            update_payload = dict(payload)
            for key in ("notes", "type", "burn_rate", "raw_json"):
                if key in update_payload and existing.get(key) not in (
                    None,
                    "",
                    0,
                    0.0,
                ):
                    update_payload[key] = existing.get(key)
            database.update("powder", update_payload, "id = ?", (int(existing["id"]),))
            powder_id = int(existing["id"])
            report["powder_library_updated"] += 1
        else:
            powder_id = int(database.insert("powder", payload))
            report["powder_library_added"] += 1

        if not powder_model_columns:
            continue
        model_payload = _filter_payload(
            {
                "powder_id": powder_id,
                "notes": "Migrated from legacy powder_data table. No Gordon pressure model available yet.",
                "data_source": "legacy_powder_data",
                "source_version": source_version,
                "external_ref": f"legacy_powder_data|{row.get('id')}",
                "raw_json": raw_json,
                "validation_status": "catalog_only",
                "usable_for_simulation": 0,
                "quickload_available": 0,
            },
            powder_model_columns,
        )
        existing_model = database.execute_query(
            "SELECT id FROM powder_database WHERE powder_id = ? LIMIT 1",
            (powder_id,),
        )
        if existing_model:
            database.update(
                "powder_database", model_payload, "powder_id = ?", (powder_id,)
            )
            report["powder_models_updated"] += 1
        else:
            database.insert("powder_database", model_payload)
            report["powder_models_added"] += 1

    return report
