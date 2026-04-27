from __future__ import annotations

import json

from ..utils.drag_models import parse_bc_segments


def _normalize_segments(raw_value: str | None) -> str | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    parsed = parse_bc_segments(text)
    if not parsed:
        return None
    return json.dumps(parsed, ensure_ascii=True)


def _map_projectile_to_bullet(projectile: dict) -> dict:
    return {
        "manufacturer": projectile.get("manufacturer"),
        "name": projectile.get("name"),
        "caliber": projectile.get("caliber"),
        "weight_grains": projectile.get("weight_grains"),
        "bc_g1": projectile.get("bc_g1"),
        "bc_g7": projectile.get("bc_g7"),
        "bc_segments_json": _normalize_segments(projectile.get("bc_segments_json")),
    }


def _map_gordon_projectile(projectile: dict) -> dict:
    return {
        "manufacturer": projectile.get("manufacturer"),
        "name": projectile.get("name"),
        "caliber": projectile.get("caliber"),
        "weight_grains": projectile.get("weight"),
        "bc_g1": projectile.get("bc"),
        "bc_g7": projectile.get("bc7"),
        "bc_segments_json": _normalize_segments(projectile.get("drag_segments")),
    }


__all__ = ["_map_projectile_to_bullet", "_map_gordon_projectile"]
