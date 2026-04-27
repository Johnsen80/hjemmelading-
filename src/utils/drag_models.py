"""Felles hjelpere for valg av dragmodell og BC-data."""

from __future__ import annotations

import json
from typing import Any

from PyQt6.QtCore import QSettings


def preferred_drag_model() -> str:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return (
        str(settings.value("ballistics/drag_model", "AUTO") or "AUTO").strip().upper()
    )


def coerce_bc(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_bc_segments(value: Any) -> list[dict[str, float | str | None]]:
    if not value:
        return []
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value)
        except Exception:
            return []
    if not isinstance(raw, list):
        return []

    segments: list[dict[str, float | str | None]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        model = str(item.get("model") or "AUTO").strip().upper()
        segments.append(
            {
                "model": model,
                "velocity_fps_min": coerce_bc(
                    item.get("velocity_fps_min") or item.get("min_fps")
                ),
                "velocity_fps_max": coerce_bc(
                    item.get("velocity_fps_max") or item.get("max_fps")
                ),
                "bc_g1": coerce_bc(item.get("bc_g1")),
                "bc_g7": coerce_bc(item.get("bc_g7")),
                "bc": coerce_bc(item.get("bc")),
            }
        )
    segments.sort(
        key=lambda seg: float(seg.get("velocity_fps_min") or 0.0), reverse=True
    )
    return segments


def _pick_segment_for_velocity(
    segments: list[dict[str, float | str | None]],
    velocity_fps: float | None,
) -> dict[str, float | str | None] | None:
    if not segments or velocity_fps is None:
        return None
    velocity = float(velocity_fps)
    for segment in segments:
        min_v = segment.get("velocity_fps_min")
        max_v = segment.get("velocity_fps_max")
        if min_v is not None and velocity < float(min_v):
            continue
        if max_v is not None and velocity > float(max_v):
            continue
        return segment
    return segments[-1] if segments else None


def resolve_drag_choice(
    bc_g1: Any,
    bc_g7: Any,
    requested: str | None = None,
    bc_segments: Any = None,
    velocity_fps: float | None = None,
) -> dict[str, str | float | None]:
    requested_model = str(requested or "AUTO").strip().upper()
    g1 = coerce_bc(bc_g1)
    g7 = coerce_bc(bc_g7)
    segments = parse_bc_segments(bc_segments)
    selected_segment = _pick_segment_for_velocity(segments, velocity_fps)

    if selected_segment is not None:
        seg_model = str(selected_segment.get("model") or "AUTO").strip().upper()
        seg_g1 = coerce_bc(selected_segment.get("bc_g1"))
        seg_g7 = coerce_bc(selected_segment.get("bc_g7"))
        seg_bc = coerce_bc(selected_segment.get("bc"))

        if requested_model == "G7" and seg_g7 is not None:
            return {
                "resolved_model": "G7",
                "bc_value": seg_g7,
                "source": "bc_segments_g7",
                "segment_match": selected_segment,
            }
        if requested_model == "G1" and seg_g1 is not None:
            return {
                "resolved_model": "G1",
                "bc_value": seg_g1,
                "source": "bc_segments_g1",
                "segment_match": selected_segment,
            }
        if seg_model == "G7" and seg_bc is not None:
            return {
                "resolved_model": "G7",
                "bc_value": seg_bc,
                "source": "bc_segments",
                "segment_match": selected_segment,
            }
        if seg_model == "G1" and seg_bc is not None:
            return {
                "resolved_model": "G1",
                "bc_value": seg_bc,
                "source": "bc_segments",
                "segment_match": selected_segment,
            }
        if requested_model != "G1" and seg_g7 is not None:
            return {
                "resolved_model": "G7",
                "bc_value": seg_g7,
                "source": "bc_segments_g7",
                "segment_match": selected_segment,
            }
        if seg_g1 is not None:
            return {
                "resolved_model": "G1",
                "bc_value": seg_g1,
                "source": "bc_segments_g1",
                "segment_match": selected_segment,
            }

    if requested_model == "G7":
        if g7 is not None:
            return {"resolved_model": "G7", "bc_value": g7, "source": "bc_g7"}
        return {"resolved_model": "G1", "bc_value": g1, "source": "bc_g1"}

    if requested_model == "G1":
        if g1 is not None:
            return {"resolved_model": "G1", "bc_value": g1, "source": "bc_g1"}
        return {"resolved_model": "G7", "bc_value": g7, "source": "bc_g7"}

    if g7 is not None:
        return {"resolved_model": "G7", "bc_value": g7, "source": "bc_g7"}
    if g1 is not None:
        return {"resolved_model": "G1", "bc_value": g1, "source": "bc_g1"}
    return {"resolved_model": "AUTO", "bc_value": None, "source": None}
