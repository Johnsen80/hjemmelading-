from __future__ import annotations

import json
from typing import Any

REQUIRED_POWDER_MODEL_FIELDS = ("Ba", "Qex", "k", "a0", "z1", "z2", "eta", "pc", "pcd")
IMAGE_KEYS = {"imageUuid", "imageDetailUuid"}


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> float | None:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _safe_json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    text = _normalize_text(value)
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _sanitize_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(payload or {})
    for key in IMAGE_KEYS:
        source.pop(key, None)
    return source


def _json_text(value: dict[str, Any] | None) -> str | None:
    payload = dict(value or {})
    if not payload:
        return None
    return json.dumps(payload, ensure_ascii=False)


def _bullet_group_key(snapshot: dict[str, Any]) -> tuple[str, str, str, float | None]:
    return (
        _normalize_text(snapshot.get("manufacturer")).lower(),
        _normalize_text(
            snapshot.get("model_name") or snapshot.get("display_name")
        ).lower(),
        _normalize_text(snapshot.get("caliber")).lower(),
        _safe_float(snapshot.get("weight_grains")),
    )


def _powder_group_key(snapshot: dict[str, Any]) -> tuple[str, str]:
    return (
        _normalize_text(snapshot.get("manufacturer")).lower(),
        _normalize_text(
            snapshot.get("model_name") or snapshot.get("display_name")
        ).lower(),
    )


def _choose_preferred_snapshot(
    snapshots: list[dict[str, Any]], component_type: str
) -> dict[str, Any]:
    if not snapshots:
        return {}
    if component_type == "powder":
        return max(
            snapshots,
            key=lambda item: (
                sum(
                    1
                    for field in REQUIRED_POWDER_MODEL_FIELDS
                    if _safe_float(_safe_json_dict(item.get("profile_json")).get(field))
                    is not None
                ),
                _normalize_text(item.get("updated_date")),
                int(item.get("id") or 0),
            ),
        )
    return max(
        snapshots,
        key=lambda item: (
            int(_safe_float(item.get("bc_g7")) is not None),
            int(_safe_float(item.get("bc_g1")) is not None),
            int(_safe_float(item.get("length_mm")) is not None),
            _normalize_text(item.get("updated_date")),
            int(item.get("id") or 0),
        ),
    )


def _bullet_external_ref(snapshot: dict[str, Any]) -> str:
    return "|".join(
        [
            "gordon_readable",
            "bullet",
            _normalize_text(snapshot.get("manufacturer")),
            _normalize_text(snapshot.get("model_name") or snapshot.get("display_name")),
            _normalize_text(snapshot.get("caliber")),
            _normalize_text(snapshot.get("weight_grains")),
        ]
    )


def _powder_external_ref(snapshot: dict[str, Any]) -> str:
    return "|".join(
        [
            "gordon_readable",
            "powder",
            _normalize_text(snapshot.get("manufacturer")),
            _normalize_text(snapshot.get("model_name") or snapshot.get("display_name")),
        ]
    )


def _find_existing_bullet(database, snapshot: dict[str, Any]) -> dict[str, Any] | None:
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
        (
            _normalize_text(snapshot.get("manufacturer")),
            _normalize_text(snapshot.get("model_name") or snapshot.get("display_name")),
            _normalize_text(snapshot.get("caliber")),
            float(_safe_float(snapshot.get("weight_grains")) or 0.0),
        ),
    )
    return dict(rows[0]) if rows else None


def _find_existing_powder(database, snapshot: dict[str, Any]) -> dict[str, Any] | None:
    rows = database.execute_query(
        """
        SELECT *
        FROM powder
        WHERE lower(coalesce(manufacturer, '')) = lower(?)
          AND lower(name) = lower(?)
        ORDER BY id
        LIMIT 1
        """,
        (
            _normalize_text(snapshot.get("manufacturer")),
            _normalize_text(snapshot.get("model_name") or snapshot.get("display_name")),
        ),
    )
    return dict(rows[0]) if rows else None


def _upsert_powder_model(
    database,
    powder_id: int,
    snapshot: dict[str, Any],
    source_version: str,
) -> str:
    profile = _sanitize_payload(_safe_json_dict(snapshot.get("profile_json")))
    raw_payload = _sanitize_payload(_safe_json_dict(snapshot.get("raw_json")))
    usable_for_simulation = int(
        all(
            _safe_float(profile.get(field)) is not None
            for field in REQUIRED_POWDER_MODEL_FIELDS
        )
    )
    payload = {
        "powder_id": int(powder_id),
        "relative_burn_rate": _safe_float(profile.get("Ba")),
        "quickload_available": usable_for_simulation,
        "quickload_ba_value": _safe_float(profile.get("Ba")),
        "density_gcc": None,
        "temp_stable": int(
            (_safe_float(profile.get("tcc")) or 0.0) == 0.0
            and (_safe_float(profile.get("tch")) or 0.0) == 0.0
        ),
        "temp_coefficient_fps_per_f": None,
        "qex_kj_per_kg": _safe_float(profile.get("Qex")),
        "k_ratio": _safe_float(profile.get("k")),
        "a0": _safe_float(profile.get("a0")),
        "z1": _safe_float(profile.get("z1")),
        "z2": _safe_float(profile.get("z2")),
        "eta_cm3_per_kg": _safe_float(profile.get("eta")),
        "pc_kg_m3": _safe_float(profile.get("pc")),
        "pcd_kg_m3": _safe_float(profile.get("pcd")),
        "pt_c": _safe_float(profile.get("pt")),
        "tcc": _safe_float(profile.get("tcc")),
        "tch": _safe_float(profile.get("tch")),
        "notes": "Imported Gordon powder reference model into local library.",
        "data_source": _normalize_text(snapshot.get("source_label"))
        or "gordon_readable",
        "validation_status": (
            "verified_seed" if usable_for_simulation else "catalog_only"
        ),
        "usable_for_simulation": usable_for_simulation,
        "source_version": source_version,
        "external_ref": _powder_external_ref(snapshot),
        "raw_json": _json_text(raw_payload),
    }
    existing = database.execute_query(
        "SELECT id FROM powder_database WHERE powder_id = ? LIMIT 1",
        (int(powder_id),),
    )
    if existing:
        database.update("powder_database", payload, "powder_id = ?", (int(powder_id),))
        return "updated"
    database.insert("powder_database", payload)
    return "added"


def import_gordon_snapshots_into_component_library(
    database,
    source_version: str = "gordon_library_import.v1",
) -> dict[str, int]:
    bullet_snapshots = [
        dict(row)
        for row in database.list_component_reference_snapshots(
            component_type="bullet", source_system="gordon_readable"
        )
    ]
    powder_snapshots = [
        dict(row)
        for row in database.list_component_reference_snapshots(
            component_type="powder", source_system="gordon_readable"
        )
    ]

    bullet_groups: dict[tuple[str, str, str, float | None], list[dict[str, Any]]] = {}
    for snapshot in bullet_snapshots:
        key = _bullet_group_key(snapshot)
        if not key[1]:
            continue
        bullet_groups.setdefault(key, []).append(snapshot)

    powder_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for snapshot in powder_snapshots:
        key = _powder_group_key(snapshot)
        if not key[1]:
            continue
        powder_groups.setdefault(key, []).append(snapshot)

    report = {
        "bullet_library_added": 0,
        "bullet_library_updated": 0,
        "bullet_library_skipped": 0,
        "powder_library_added": 0,
        "powder_library_updated": 0,
        "powder_library_skipped": 0,
        "powder_models_added": 0,
        "powder_models_updated": 0,
        "powder_models_usable_for_simulation": 0,
    }

    for snapshots in bullet_groups.values():
        preferred = _choose_preferred_snapshot(snapshots, "bullet")
        name = _normalize_text(
            preferred.get("model_name") or preferred.get("display_name")
        )
        caliber = _normalize_text(preferred.get("caliber"))
        weight_grains = _safe_float(preferred.get("weight_grains"))
        bullet_profile = _sanitize_payload(
            _safe_json_dict(preferred.get("profile_json"))
        )
        bullet_raw = _sanitize_payload(_safe_json_dict(preferred.get("raw_json")))
        if not name or not caliber or weight_grains is None:
            report["bullet_library_skipped"] += 1
            continue
        payload = {
            "name": name,
            "manufacturer": _normalize_text(preferred.get("manufacturer")) or None,
            "display_name": _normalize_text(preferred.get("display_name")) or name,
            "caliber": caliber,
            "weight_grains": weight_grains,
            "diameter_mm": _safe_float(preferred.get("diameter_mm")),
            "length_mm": _safe_float(preferred.get("length_mm")),
            "bc_g1": _safe_float(bullet_profile.get("bc_g1"))
            or _safe_float(preferred.get("bc_g1")),
            "bc_g7": _safe_float(bullet_profile.get("bc_g7"))
            or _safe_float(preferred.get("bc_g7")),
            "bullet_type": _normalize_text(
                bullet_raw.get("type")
                or bullet_raw.get("gTailType")
                or bullet_profile.get("tail_type")
            )
            or None,
            "notes": _normalize_text(bullet_raw.get("descr"))
            or "Imported Gordon bullet reference into local library.",
            "description": _normalize_text(
                bullet_raw.get("gUBCS") or bullet_profile.get("ubcs")
            )
            or None,
            "source": "gordon_import",
            "source_kind": "gordon_readable_snapshot",
            "evidence_level": _normalize_text(preferred.get("evidence_level"))
            or "imported_reference",
            "source_version": source_version,
            "source_label": _normalize_text(preferred.get("source_label")) or None,
            "profile_json": _json_text(bullet_profile),
            "raw_json": _json_text(bullet_raw),
            "external_ref": _bullet_external_ref(preferred),
        }
        existing = _find_existing_bullet(database, preferred)
        if existing:
            update_payload = dict(payload)
            update_payload["display_name"] = payload["display_name"] or existing.get(
                "display_name"
            )
            update_payload["diameter_mm"] = payload["diameter_mm"] or existing.get(
                "diameter_mm"
            )
            update_payload["length_mm"] = payload["length_mm"] or existing.get(
                "length_mm"
            )
            update_payload["bc_g1"] = payload["bc_g1"] or existing.get("bc_g1")
            update_payload["bc_g7"] = payload["bc_g7"] or existing.get("bc_g7")
            update_payload["bullet_type"] = payload["bullet_type"] or existing.get(
                "bullet_type"
            )
            update_payload["notes"] = existing.get("notes") or payload["notes"]
            update_payload["description"] = payload["description"] or existing.get(
                "description"
            )
            update_payload["source_label"] = payload["source_label"] or existing.get(
                "source_label"
            )
            update_payload["profile_json"] = payload["profile_json"] or existing.get(
                "profile_json"
            )
            update_payload["raw_json"] = payload["raw_json"] or existing.get("raw_json")
            database.update("bullets", update_payload, "id = ?", (int(existing["id"]),))
            report["bullet_library_updated"] += 1
        else:
            database.insert("bullets", payload)
            report["bullet_library_added"] += 1

    for snapshots in powder_groups.values():
        preferred = _choose_preferred_snapshot(snapshots, "powder")
        name = _normalize_text(
            preferred.get("model_name") or preferred.get("display_name")
        )
        powder_profile = _sanitize_payload(
            _safe_json_dict(preferred.get("profile_json"))
        )
        powder_raw = _sanitize_payload(_safe_json_dict(preferred.get("raw_json")))
        if not name:
            report["powder_library_skipped"] += 1
            continue
        burn_rate_label = (
            f"Ba {_safe_float(powder_profile.get('Ba')):.4f}"
            if _safe_float(powder_profile.get("Ba")) is not None
            else None
        )
        payload = {
            "name": name,
            "manufacturer": _normalize_text(preferred.get("manufacturer")) or None,
            "display_name": _normalize_text(preferred.get("display_name")) or name,
            "type": None,
            "burn_rate": burn_rate_label,
            "density": _safe_float(powder_profile.get("pc")) or None,
            "notes": _normalize_text(preferred.get("source_label"))
            or "Imported Gordon powder reference into local library.",
            "description": (
                f"Qex={_safe_float(powder_profile.get('Qex')):.0f} kJ/kg, "
                f"k={_safe_float(powder_profile.get('k')):.4f}, "
                f"eta={_safe_float(powder_profile.get('eta')):.4f}"
                if _safe_float(powder_profile.get("Qex")) is not None
                and _safe_float(powder_profile.get("k")) is not None
                and _safe_float(powder_profile.get("eta")) is not None
                else None
            ),
            "source": "gordon_import",
            "source_kind": "gordon_readable_snapshot",
            "evidence_level": _normalize_text(preferred.get("evidence_level"))
            or "simulation_seed",
            "source_version": source_version,
            "source_label": _normalize_text(preferred.get("source_label")) or None,
            "profile_json": _json_text(powder_profile),
            "raw_json": _json_text(powder_raw),
            "external_ref": _powder_external_ref(preferred),
        }
        existing = _find_existing_powder(database, preferred)
        if existing:
            update_payload = dict(payload)
            update_payload["display_name"] = payload["display_name"] or existing.get(
                "display_name"
            )
            update_payload["type"] = existing.get("type") or payload["type"]
            update_payload["burn_rate"] = payload["burn_rate"] or existing.get(
                "burn_rate"
            )
            update_payload["density"] = payload["density"] or existing.get("density")
            update_payload["notes"] = existing.get("notes") or payload["notes"]
            update_payload["description"] = payload["description"] or existing.get(
                "description"
            )
            update_payload["source_label"] = payload["source_label"] or existing.get(
                "source_label"
            )
            update_payload["profile_json"] = payload["profile_json"] or existing.get(
                "profile_json"
            )
            update_payload["raw_json"] = payload["raw_json"] or existing.get("raw_json")
            database.update("powder", update_payload, "id = ?", (int(existing["id"]),))
            powder_id = int(existing["id"])
            report["powder_library_updated"] += 1
        else:
            powder_id = database.insert("powder", payload)
            report["powder_library_added"] += 1

        model_result = _upsert_powder_model(
            database, powder_id, preferred, source_version
        )
        if model_result == "added":
            report["powder_models_added"] += 1
        else:
            report["powder_models_updated"] += 1
        model_row = database.execute_query(
            "SELECT usable_for_simulation FROM powder_database WHERE powder_id = ? LIMIT 1",
            (powder_id,),
        )
        if model_row and int(model_row[0].get("usable_for_simulation") or 0):
            report["powder_models_usable_for_simulation"] += 1

    return report
