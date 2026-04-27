from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..database.database import Database

_JSON_FIELDS = (
    "intake_snapshot_json",
    "component_selection_json",
    "component_lots_json",
    "recommendation_json",
    "barrel_configuration_snapshot_json",
    "evidence_summary_json",
    "learning_state_json",
)

_LEARNING_STATE_SCHEMA_VERSION = "load_learning_state.v1"

_UNSET = object()


def _to_json(payload: Any) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _as_dict(payload: Any) -> dict[str, Any]:
    return dict(payload) if isinstance(payload, dict) else {}


_VALID_MODEL_STATUSES: frozenset[str] = frozenset(
    ["raw", "partially_calibrated", "well_calibrated"]
)


def _normalize_candidates(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    confirmed = raw.get("confirmed")
    rejected = raw.get("rejected")
    return {
        "confirmed": list(confirmed) if isinstance(confirmed, list) else [],
        "rejected": list(rejected) if isinstance(rejected, list) else [],
    }


def _normalize_learning_state(payload: Any) -> dict[str, Any]:
    raw = _as_dict(payload)
    analysis = _as_dict(raw.get("analysis"))

    for legacy_key in (
        "barrel_context",
        "brass_context",
        "node_fit",
        "stability_assessment",
    ):
        legacy_value = raw.get(legacy_key)
        if legacy_key not in analysis and isinstance(legacy_value, dict):
            analysis[legacy_key] = dict(legacy_value)

    # model_status: canonical learning progress label.
    # "raw" = no measured data; "partially_calibrated" = some data; "well_calibrated" = strong evidence.
    raw_model_status = str(raw.get("model_status") or "").strip()
    model_status = (
        raw_model_status if raw_model_status in _VALID_MODEL_STATUSES else "raw"
    )

    # charge_window / seating_window / lot_drift: explicitly preserved (not re-derived).
    charge_window_raw = raw.get("charge_window")
    charge_window = (
        _as_dict(charge_window_raw) if isinstance(charge_window_raw, dict) else None
    )

    seating_window_raw = raw.get("seating_window")
    seating_window = (
        _as_dict(seating_window_raw) if isinstance(seating_window_raw, dict) else None
    )

    lot_drift_raw = raw.get("lot_drift")
    lot_drift = _as_dict(lot_drift_raw) if isinstance(lot_drift_raw, dict) else None

    # candidates: confirmed and rejected load recipes for this session.
    candidates = _normalize_candidates(raw.get("candidates"))

    normalized: dict[str, Any] = {
        "schema_version": str(
            raw.get("schema_version") or _LEARNING_STATE_SCHEMA_VERSION
        ),
        "model_status": model_status,
        "best_history": _as_dict(raw.get("best_history")),
        "analysis": {
            "barrel_context": _as_dict(analysis.get("barrel_context")),
            "brass_context": _as_dict(analysis.get("brass_context")),
            "node_fit": _as_dict(analysis.get("node_fit")),
            "stability_assessment": _as_dict(analysis.get("stability_assessment")),
        },
        "candidates": candidates,
        "summary": _as_dict(raw.get("summary")),
    }
    if charge_window is not None:
        normalized["charge_window"] = charge_window
    if seating_window is not None:
        normalized["seating_window"] = seating_window
    if lot_drift is not None:
        normalized["lot_drift"] = lot_drift

    reserved = {
        "schema_version",
        "model_status",
        "best_history",
        "analysis",
        "candidates",
        "summary",
        "charge_window",
        "seating_window",
        "lot_drift",
        "barrel_context",
        "brass_context",
        "node_fit",
        "stability_assessment",
    }
    for key, value in raw.items():
        if key not in reserved:
            normalized[key] = value

    return normalized


def _parse_session_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    parsed = dict(row)
    for field in _JSON_FIELDS:
        raw = parsed.get(field)
        if not raw:
            parsed[field] = {}
            continue
        try:
            parsed[field] = json.loads(raw)
        except Exception:
            parsed[field] = {}
    parsed["learning_state_json"] = _normalize_learning_state(
        parsed.get("learning_state_json")
    )
    return parsed


def create_load_development_session(
    database: Database,
    *,
    rifle_id: int | None,
    rifle_name: str,
    rifle_caliber: str,
    usage_profile_key: str,
    usage_profile_name: str,
    barrel_id: str | None = None,
    barrel_name: str | None = None,
    barrel_configuration_id: str | None = None,
    barrel_configuration_name: str | None = None,
    barrel_configuration_snapshot: dict[str, Any] | None = None,
    component_selection: dict[str, Any] | None = None,
    component_lots: dict[str, Any] | None = None,
    intake_snapshot: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
    evidence_summary: dict[str, Any] | None = None,
    learning_state: dict[str, Any] | None = None,
    subsonic_mode: bool = False,
    session_verdict: str | None = None,
    quantity_target: int | None = None,
    recommended_charge_min_gr: float | None = None,
    recommended_charge_max_gr: float | None = None,
    recommended_coal_min: float | None = None,
    recommended_coal_max: float | None = None,
    confidence_label: str = "medium",
    confidence_score: float | None = None,
    safety_status: str = "review_required",
    status: str = "active",
    lifecycle_stage: str = "recommendation_ready",
    next_action: str | None = None,
    legacy_loading_session_id: int | None = None,
    notes: str | None = None,
) -> int:
    timestamp = datetime.now().isoformat(timespec="seconds")
    payload = {
        "session_uid": uuid4().hex,
        "status": status,
        "lifecycle_stage": lifecycle_stage,
        "rifle_id": rifle_id,
        "rifle_name": rifle_name or None,
        "rifle_caliber": rifle_caliber or None,
        "barrel_id": barrel_id or None,
        "barrel_name": barrel_name or None,
        "barrel_configuration_id": barrel_configuration_id or None,
        "barrel_configuration_name": barrel_configuration_name or None,
        "usage_profile_key": usage_profile_key,
        "usage_profile_name": usage_profile_name,
        "subsonic_mode": 1 if subsonic_mode else 0,
        "quantity_target": quantity_target,
        "recommended_charge_min_gr": recommended_charge_min_gr,
        "recommended_charge_max_gr": recommended_charge_max_gr,
        "recommended_coal_min": recommended_coal_min,
        "recommended_coal_max": recommended_coal_max,
        "confidence_label": confidence_label,
        "confidence_score": confidence_score,
        "safety_status": safety_status,
        "next_action": next_action,
        "session_verdict": session_verdict,
        "legacy_loading_session_id": legacy_loading_session_id,
        "intake_snapshot_json": _to_json(intake_snapshot or {}),
        "component_selection_json": _to_json(component_selection or {}),
        "component_lots_json": _to_json(component_lots or {}),
        "recommendation_json": _to_json(recommendation or {}),
        "barrel_configuration_snapshot_json": _to_json(
            barrel_configuration_snapshot or {}
        ),
        "evidence_summary_json": _to_json(evidence_summary or {}),
        "learning_state_json": _to_json(_normalize_learning_state(learning_state)),
        "notes": notes,
        "created_date": timestamp,
        "updated_date": timestamp,
    }
    return database.insert("load_development_sessions", payload)


def link_legacy_loading_session(
    database: Database,
    *,
    legacy_loading_session_id: int,
    load_session_id: int,
) -> None:
    database.update(
        "loading_sessions",
        {"load_session_id": load_session_id},
        "id = ?",
        (legacy_loading_session_id,),
    )
    database.update(
        "load_development_sessions",
        {
            "legacy_loading_session_id": legacy_loading_session_id,
            "updated_date": datetime.now().isoformat(timespec="seconds"),
        },
        "id = ?",
        (load_session_id,),
    )


def get_load_development_session(
    database: Database, session_id: int
) -> dict[str, Any] | None:
    row = database.get_by_id("load_development_sessions", session_id)
    return _parse_session_row(row)


def list_load_development_sessions(
    database: Database,
    *,
    status: str | None = None,
    rifle_id: int | None = None,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM load_development_sessions WHERE 1=1"
    params: list[Any] = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if rifle_id is not None:
        query += " AND rifle_id = ?"
        params.append(rifle_id)
    query += " ORDER BY updated_date DESC, id DESC"
    rows = database.execute_query(query, tuple(params))
    return [_parse_session_row(row) or {} for row in rows]


def _merge_json_field(
    current_row: dict[str, Any],
    field_name: str,
    full_value: Any,
    updates: dict[str, Any] | None,
) -> str | None | object:
    if full_value is not _UNSET:
        if field_name == "learning_state_json":
            return _to_json(_normalize_learning_state(full_value))
        return _to_json(full_value or {})
    if updates is None:
        return _UNSET

    current_value = current_row.get(field_name)
    merged = dict(current_value) if isinstance(current_value, dict) else {}
    merged.update(updates)
    if field_name == "learning_state_json":
        merged = _normalize_learning_state(merged)
    return _to_json(merged)


def update_load_development_session(
    database: Database,
    session_id: int,
    *,
    updates: dict[str, Any] | None = None,
    component_selection: dict[str, Any] | object = _UNSET,
    component_selection_updates: dict[str, Any] | None = None,
    intake_snapshot: dict[str, Any] | object = _UNSET,
    intake_snapshot_updates: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | object = _UNSET,
    recommendation_updates: dict[str, Any] | None = None,
    component_lots: dict[str, Any] | object = _UNSET,
    component_lots_updates: dict[str, Any] | None = None,
    barrel_configuration_snapshot: dict[str, Any] | object = _UNSET,
    barrel_configuration_snapshot_updates: dict[str, Any] | None = None,
    evidence_summary: dict[str, Any] | object = _UNSET,
    evidence_summary_updates: dict[str, Any] | None = None,
    learning_state: dict[str, Any] | object = _UNSET,
    learning_state_updates: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    current_row = get_load_development_session(database, session_id)
    if not current_row:
        return None

    payload = dict(updates or {})
    json_updates = {
        "component_selection_json": _merge_json_field(
            current_row,
            "component_selection_json",
            component_selection,
            component_selection_updates,
        ),
        "intake_snapshot_json": _merge_json_field(
            current_row,
            "intake_snapshot_json",
            intake_snapshot,
            intake_snapshot_updates,
        ),
        "recommendation_json": _merge_json_field(
            current_row,
            "recommendation_json",
            recommendation,
            recommendation_updates,
        ),
        "component_lots_json": _merge_json_field(
            current_row,
            "component_lots_json",
            component_lots,
            component_lots_updates,
        ),
        "barrel_configuration_snapshot_json": _merge_json_field(
            current_row,
            "barrel_configuration_snapshot_json",
            barrel_configuration_snapshot,
            barrel_configuration_snapshot_updates,
        ),
        "evidence_summary_json": _merge_json_field(
            current_row,
            "evidence_summary_json",
            evidence_summary,
            evidence_summary_updates,
        ),
        "learning_state_json": _merge_json_field(
            current_row,
            "learning_state_json",
            learning_state,
            learning_state_updates,
        ),
    }
    for field_name, value in json_updates.items():
        if value is not _UNSET:
            payload[field_name] = value

    if not payload:
        return current_row

    payload["updated_date"] = datetime.now().isoformat(timespec="seconds")
    database.update("load_development_sessions", payload, "id = ?", (session_id,))
    return get_load_development_session(database, session_id)


_MAX_CANDIDATES_PER_LIST = 20


def _build_candidate_entry(
    *,
    charge_gr: float | None = None,
    coal_mm: float | None = None,
    cbto_mm: float | None = None,
    group_size_mm: float | None = None,
    group_size_moa: float | None = None,
    velocity_avg_fps: float | None = None,
    reason: str | None = None,
    evidence_quality: str | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "date": date or datetime.now().date().isoformat(),
    }
    if charge_gr is not None:
        entry["charge_gr"] = round(float(charge_gr), 3)
    if coal_mm is not None:
        entry["coal_mm"] = round(float(coal_mm), 3)
    if cbto_mm is not None:
        entry["cbto_mm"] = round(float(cbto_mm), 3)
    if group_size_mm is not None:
        entry["group_size_mm"] = round(float(group_size_mm), 2)
    if group_size_moa is not None:
        entry["group_size_moa"] = round(float(group_size_moa), 3)
    if velocity_avg_fps is not None:
        entry["velocity_avg_fps"] = round(float(velocity_avg_fps), 1)
    if reason:
        entry["reason"] = str(reason).strip()
    if evidence_quality:
        entry["evidence_quality"] = str(evidence_quality).strip()
    return entry


def confirm_load_candidate(
    database: Database,
    session_id: int,
    *,
    charge_gr: float | None = None,
    coal_mm: float | None = None,
    cbto_mm: float | None = None,
    group_size_mm: float | None = None,
    group_size_moa: float | None = None,
    velocity_avg_fps: float | None = None,
    reason: str | None = None,
    evidence_quality: str | None = None,
    date: str | None = None,
) -> dict[str, Any] | None:
    """Record a confirmed (keeper) load recipe in learning_state_json.candidates.confirmed.

    Appends a candidate entry and caps the list at _MAX_CANDIDATES_PER_LIST.
    Returns the updated session row, or None if session not found.
    """
    current = get_load_development_session(database, session_id)
    if not current:
        return None
    learning = _as_dict(current.get("learning_state_json"))
    candidates = _normalize_candidates(learning.get("candidates"))
    confirmed = list(candidates["confirmed"])
    confirmed.append(
        _build_candidate_entry(
            charge_gr=charge_gr,
            coal_mm=coal_mm,
            cbto_mm=cbto_mm,
            group_size_mm=group_size_mm,
            group_size_moa=group_size_moa,
            velocity_avg_fps=velocity_avg_fps,
            reason=reason,
            evidence_quality=evidence_quality,
            date=date,
        )
    )
    # Keep only the most recent N entries.
    if len(confirmed) > _MAX_CANDIDATES_PER_LIST:
        confirmed = confirmed[-_MAX_CANDIDATES_PER_LIST:]
    return update_load_development_session(
        database,
        session_id,
        learning_state_updates={
            "candidates": {"confirmed": confirmed, "rejected": candidates["rejected"]}
        },
    )


def reject_load_candidate(
    database: Database,
    session_id: int,
    *,
    charge_gr: float | None = None,
    coal_mm: float | None = None,
    cbto_mm: float | None = None,
    group_size_mm: float | None = None,
    group_size_moa: float | None = None,
    velocity_avg_fps: float | None = None,
    reason: str | None = None,
    evidence_quality: str | None = None,
    date: str | None = None,
) -> dict[str, Any] | None:
    """Record a rejected load recipe in learning_state_json.candidates.rejected.

    Appends a candidate entry and caps the list at _MAX_CANDIDATES_PER_LIST.
    Returns the updated session row, or None if session not found.
    """
    current = get_load_development_session(database, session_id)
    if not current:
        return None
    learning = _as_dict(current.get("learning_state_json"))
    candidates = _normalize_candidates(learning.get("candidates"))
    rejected = list(candidates["rejected"])
    rejected.append(
        _build_candidate_entry(
            charge_gr=charge_gr,
            coal_mm=coal_mm,
            cbto_mm=cbto_mm,
            group_size_mm=group_size_mm,
            group_size_moa=group_size_moa,
            velocity_avg_fps=velocity_avg_fps,
            reason=reason,
            evidence_quality=evidence_quality,
            date=date,
        )
    )
    if len(rejected) > _MAX_CANDIDATES_PER_LIST:
        rejected = rejected[-_MAX_CANDIDATES_PER_LIST:]
    return update_load_development_session(
        database,
        session_id,
        learning_state_updates={
            "candidates": {"confirmed": candidates["confirmed"], "rejected": rejected}
        },
    )
