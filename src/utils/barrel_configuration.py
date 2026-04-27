from __future__ import annotations

import json
import re
from typing import Any


def _slugify(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "default"


def _normalize_muzzle_device_type(value: object) -> str | None:
    text = str(value or "").strip().lower()
    if not text or text in {
        "none",
        "no",
        "no device",
        "bare",
        "bare muzzle",
        "ingen",
        "ingen enhet",
    }:
        return None
    if any(
        token in text for token in ("suppressor", "moderator", "demper", "silencer")
    ):
        return "suppressor"
    if "brake" in text:
        return "brake"
    if "comp" in text:
        return "compensator"
    return text


def _looks_like_suppressor(muzzle_device_type: object) -> bool:
    return _normalize_muzzle_device_type(muzzle_device_type) == "suppressor"


def load_rifle_profile_details(db, rifle_id: int | None) -> dict[str, Any]:
    if rifle_id in (None, ""):
        return {}
    try:
        rows = db.execute_query(
            "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
            (int(rifle_id),),
        )
    except Exception:
        return {}
    if not rows:
        return {}
    raw = rows[0].get("profile_json")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _resolve_active_barrel(
    profile_details: dict[str, Any] | None,
    active_barrel_details: dict[str, Any] | None = None,
) -> tuple[str | None, dict[str, Any]]:
    details = profile_details or {}
    if isinstance(active_barrel_details, dict) and active_barrel_details:
        barrel = dict(active_barrel_details)
        barrel_id = (
            str(barrel.get("id") or details.get("active_barrel_id") or "").strip()
            or None
        )
        return barrel_id, barrel

    active_barrel_id = str(details.get("active_barrel_id") or "").strip() or None
    barrels = details.get("barrels", [])
    if isinstance(barrels, list):
        for barrel in barrels:
            if (
                isinstance(barrel, dict)
                and active_barrel_id
                and str(barrel.get("id") or "").strip() == active_barrel_id
            ):
                return active_barrel_id, dict(barrel)
        for barrel in barrels:
            if isinstance(barrel, dict):
                return str(barrel.get("id") or "").strip() or active_barrel_id, dict(
                    barrel
                )
    return active_barrel_id, {}


def build_derived_barrel_configuration_context(
    *,
    barrel_id: str | None,
    barrel: dict[str, Any] | None = None,
    rifle_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    barrel_data = dict(barrel or {})
    rifle_context = rifle_data or {}
    barrel_name = str(barrel_data.get("name") or "").strip() or None
    normalized_muzzle_device = _normalize_muzzle_device_type(
        barrel_data.get("muzzle_device_type")
        or barrel_data.get("muzzle_device")
        or rifle_context.get("muzzle_device")
    )
    muzzle_device_model = (
        str(barrel_data.get("muzzle_device_model") or "").strip() or None
    )
    suppressor_used = _looks_like_suppressor(normalized_muzzle_device)

    if normalized_muzzle_device == "suppressor":
        config_label = "Suppressor On"
    elif normalized_muzzle_device == "brake":
        config_label = "Brake"
    elif normalized_muzzle_device == "compensator":
        config_label = "Compensator"
    elif normalized_muzzle_device:
        config_label = normalized_muzzle_device.replace("-", " ").title()
    else:
        config_label = "Bare Muzzle"

    barrel_configuration_name = (
        f"{config_label} ({muzzle_device_model})"
        if muzzle_device_model
        else config_label
    )

    barrel_configuration_id = None
    if barrel_id or barrel_name or normalized_muzzle_device or muzzle_device_model:
        barrel_prefix = _slugify(
            barrel_id or barrel_name or rifle_context.get("name") or "barrel"
        )
        config_suffix = _slugify(normalized_muzzle_device or "bare-muzzle")
        if muzzle_device_model:
            config_suffix = f"{config_suffix}-{_slugify(muzzle_device_model)}"
        barrel_configuration_id = f"{barrel_prefix}-{config_suffix}"

    snapshot = {
        "barrel_id": barrel_id,
        "barrel_name": barrel_name,
        "caliber": barrel_data.get("caliber") or rifle_context.get("caliber"),
        "length_mm": barrel_data.get("length_mm"),
        "twist": barrel_data.get("twist") or rifle_context.get("twist_rate"),
        "muzzle_device_type": normalized_muzzle_device or "none",
        "muzzle_device_model": muzzle_device_model,
        "muzzle_device_weight_g": barrel_data.get("muzzle_device_weight_g"),
        "poi_shift_h": barrel_data.get("poi_shift_h"),
        "poi_shift_v": barrel_data.get("poi_shift_v"),
        "suppressor_used": suppressor_used,
    }

    return {
        "barrel_id": barrel_id,
        "barrel_name": barrel_name,
        "barrel_configuration_id": barrel_configuration_id,
        "barrel_configuration_name": barrel_configuration_name,
        "barrel_configuration_snapshot": snapshot,
        "muzzle_device_type": normalized_muzzle_device or "none",
        "suppressor_used": suppressor_used,
    }


def _resolve_explicit_barrel_configuration(
    profile_details: dict[str, Any] | None,
    *,
    barrel_id: str | None,
) -> dict[str, Any]:
    details = profile_details or {}
    explicit_active_id = (
        str(details.get("active_barrel_configuration_id") or "").strip() or None
    )
    configurations = details.get("barrel_configurations", [])
    if not isinstance(configurations, list):
        return {}

    matching: list[dict[str, Any]] = []
    for configuration in configurations:
        if not isinstance(configuration, dict):
            continue
        configuration_barrel_id = (
            str(configuration.get("barrel_id") or "").strip() or None
        )
        if (
            barrel_id
            and configuration_barrel_id
            and configuration_barrel_id != barrel_id
        ):
            continue
        if barrel_id and not configuration_barrel_id:
            continue
        matching.append(dict(configuration))

    if explicit_active_id:
        for configuration in matching:
            configuration_id = str(configuration.get("id") or "").strip()
            if configuration_id and configuration_id == explicit_active_id:
                return configuration
    for configuration in matching:
        if bool(configuration.get("is_active")):
            return configuration
    return matching[0] if len(matching) == 1 else {}


def resolve_active_barrel_configuration_context(
    db=None,
    rifle_id: int | None = None,
    *,
    rifle_data: dict[str, Any] | None = None,
    profile_details: dict[str, Any] | None = None,
    active_barrel_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    details = profile_details or {}
    if not details and db is not None and rifle_id not in (None, ""):
        details = load_rifle_profile_details(db, rifle_id)

    barrel_id, barrel = _resolve_active_barrel(details, active_barrel_details)
    derived_context = build_derived_barrel_configuration_context(
        barrel_id=barrel_id,
        barrel=barrel,
        rifle_data=rifle_data,
    )
    explicit_configuration = _resolve_explicit_barrel_configuration(
        details, barrel_id=barrel_id
    )

    barrel_name = (
        str(
            explicit_configuration.get("barrel_name")
            or derived_context.get("barrel_name")
            or barrel.get("name")
            or ""
        ).strip()
        or None
    )
    snapshot = dict(derived_context.get("barrel_configuration_snapshot") or {})
    explicit_snapshot = explicit_configuration.get("snapshot")
    if isinstance(explicit_snapshot, dict):
        snapshot.update(explicit_snapshot)
    snapshot["barrel_id"] = barrel_id
    snapshot["barrel_name"] = barrel_name
    normalized_muzzle_device = _normalize_muzzle_device_type(
        explicit_configuration.get("muzzle_device_type")
        or snapshot.get("muzzle_device_type")
        or barrel.get("muzzle_device_type")
        or barrel.get("muzzle_device")
        or (rifle_data or {}).get("muzzle_device")
    )
    muzzle_device_model = (
        str(
            explicit_configuration.get("muzzle_device_model")
            or snapshot.get("muzzle_device_model")
            or barrel.get("muzzle_device_model")
            or ""
        ).strip()
        or None
    )
    suppressor_used = _looks_like_suppressor(normalized_muzzle_device)
    snapshot["muzzle_device_type"] = normalized_muzzle_device or "none"
    snapshot["muzzle_device_model"] = muzzle_device_model
    snapshot["suppressor_used"] = suppressor_used

    barrel_configuration_id = (
        str(
            explicit_configuration.get("id")
            or derived_context.get("barrel_configuration_id")
            or ""
        ).strip()
        or None
    )
    barrel_configuration_name = (
        str(
            explicit_configuration.get("name")
            or derived_context.get("barrel_configuration_name")
            or ""
        ).strip()
        or None
    )

    return {
        "barrel_id": barrel_id,
        "barrel_name": barrel_name,
        "barrel_configuration_id": barrel_configuration_id,
        "barrel_configuration_name": barrel_configuration_name,
        "barrel_configuration_snapshot": snapshot,
        "muzzle_device_type": normalized_muzzle_device or "none",
        "suppressor_used": suppressor_used,
    }
