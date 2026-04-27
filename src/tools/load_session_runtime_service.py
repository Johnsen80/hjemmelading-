from __future__ import annotations

import json
from typing import Any

from PyQt6.QtCore import QSettings

from ..database.database import Database
from ..modules.smart_ammo_engine import build_smart_ammo_engine_from_runtime
from .load_development_session_service import (
    get_load_development_session,
    update_load_development_session,
)


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _table_exists(database: Database, table_name: str) -> bool:
    rows = database.execute_query(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return bool(rows)


def _get_row_by_id(
    database: Database, table_name: str, row_id: Any
) -> dict[str, Any] | None:
    resolved_id = _safe_int(row_id)
    if resolved_id is None or not _table_exists(database, table_name):
        return None
    return database.get_by_id(table_name, resolved_id)


def _query_single_row(
    database: Database, query: str, params: tuple[Any, ...]
) -> dict[str, Any] | None:
    rows = database.execute_query(query, params)
    return dict(rows[0]) if rows else None


def _safe_json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _extract_batch_session_primer_review(session: dict[str, Any]) -> dict[str, Any]:
    analysis = (
        session.get("analysis_json")
        if isinstance(session.get("analysis_json"), dict)
        else {}
    )
    review = analysis.get("primer_image_review") if isinstance(analysis, dict) else {}
    return dict(review) if isinstance(review, dict) else {}


def _extract_batch_session_primer_images(session: dict[str, Any]) -> list[str]:
    review = _extract_batch_session_primer_review(session)
    raw_images = review.get("images")
    images = [str(item).strip() for item in (raw_images or []) if str(item).strip()]
    if images:
        return images
    fallback = str(review.get("path") or review.get("primary_path") or "").strip()
    return [fallback] if fallback else []


def _component_selection(session: dict[str, Any]) -> dict[str, Any]:
    selection = session.get("component_selection_json") or {}
    return dict(selection) if isinstance(selection, dict) else {}


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _get_barrel_learning_profile(
    database: Database,
    rifle_id: int | None,
    barrel_id: str,
    barrel_name: str,
    barrel_configuration_id: str | None = None,
    barrel_configuration_name: str | None = None,
) -> dict[str, Any]:
    if (
        rifle_id is None
        or not barrel_id
        or not hasattr(database, "get_barrel_learning_profile")
    ):
        return {}
    getter = database.get_barrel_learning_profile
    try:
        return getter(
            rifle_id,
            barrel_id,
            barrel_name,
            barrel_configuration_id,
            barrel_configuration_name,
        )
    except TypeError:
        return getter(rifle_id, barrel_id, barrel_name)


def _derive_configuration_id_from_snapshot(snapshot: dict[str, Any]) -> str:
    """Derive a barrel_configuration_id from snapshot fields when the column is NULL.

    This handles older sessions and code paths that didn't write barrel_configuration_id.
    Uses the same slug logic as barrel_configuration.build_derived_barrel_configuration_context.
    """
    barrel_id = str(snapshot.get("barrel_id") or "").strip()
    barrel_name = str(snapshot.get("barrel_name") or "").strip()
    muzzle_device_type = (
        str(snapshot.get("muzzle_device_type") or "none").strip().lower()
    )
    muzzle_device_model = str(snapshot.get("muzzle_device_model") or "").strip()
    if not barrel_id and not barrel_name:
        return ""
    import re

    def _slug(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    barrel_prefix = _slug(barrel_id or barrel_name)
    config_suffix = _slug(
        muzzle_device_type if muzzle_device_type not in ("", "none") else "bare-muzzle"
    )
    if muzzle_device_model:
        config_suffix = f"{config_suffix}-{_slug(muzzle_device_model)}"
    return f"{barrel_prefix}-{config_suffix}" if barrel_prefix else ""


def _resolve_barrel_context(
    database: Database, session: dict[str, Any]
) -> dict[str, Any]:
    rifle_id = _safe_int(session.get("rifle_id"))
    session_barrel_id = str(session.get("barrel_id") or "").strip()
    session_barrel_name = str(session.get("barrel_name") or "").strip()
    session_barrel_configuration_id = str(
        session.get("barrel_configuration_id") or ""
    ).strip()
    session_barrel_configuration_name = str(
        session.get("barrel_configuration_name") or ""
    ).strip()

    barrel_id = session_barrel_id
    barrel_name = session_barrel_name
    source = "session"

    if (
        not barrel_id
        and rifle_id is not None
        and hasattr(database, "resolve_learning_barrel")
    ):
        resolved = database.resolve_learning_barrel(rifle_id)
        barrel_id = str(resolved.get("barrel_id") or "").strip()
        if not barrel_name:
            barrel_name = str(resolved.get("barrel_name") or "").strip()
        source = "rifle_profile" if barrel_id else "unknown"

    # Fallback 1: derive configuration_id from the stored snapshot when the
    # direct column is NULL (old sessions / code paths that didn't set it).
    if not session_barrel_configuration_id:
        raw_snapshot = session.get("barrel_configuration_snapshot_json")
        snapshot = raw_snapshot if isinstance(raw_snapshot, dict) else {}
        derived_id = _derive_configuration_id_from_snapshot(snapshot)
        if derived_id:
            session_barrel_configuration_id = derived_id

    # Fallback 2: when barrel was resolved from the rifle profile and configuration
    # is still missing, look it up from rifle_profile_details.
    if (
        not session_barrel_configuration_id
        and source == "rifle_profile"
        and rifle_id is not None
    ):
        try:
            rows = database.execute_query(
                "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
                (rifle_id,),
            )
            if rows and rows[0].get("profile_json"):
                details = json.loads(rows[0]["profile_json"])
                active_cfg_id = str(
                    details.get("active_barrel_configuration_id") or ""
                ).strip()
                if active_cfg_id:
                    session_barrel_configuration_id = active_cfg_id
                    if not session_barrel_configuration_name:
                        for cfg in details.get("barrel_configurations") or []:
                            if (
                                isinstance(cfg, dict)
                                and str(cfg.get("id") or "") == active_cfg_id
                            ):
                                session_barrel_configuration_name = str(
                                    cfg.get("name") or ""
                                ).strip()
                                break
        except Exception:
            pass

    learning_profile: dict[str, Any] = {}
    if rifle_id is not None and barrel_id:
        learning_profile = _get_barrel_learning_profile(
            database,
            rifle_id,
            barrel_id,
            barrel_name,
            session_barrel_configuration_id or None,
            session_barrel_configuration_name or None,
        )

    return {
        "barrel_id": barrel_id or None,
        "barrel_name": barrel_name or None,
        "barrel_configuration_id": session_barrel_configuration_id or None,
        "barrel_configuration_name": session_barrel_configuration_name or None,
        "source": source,
        "learning_profile": learning_profile,
    }


def _resolve_component_context(
    database: Database, selection: dict[str, Any]
) -> dict[str, Any]:
    bullet_id = _safe_int(selection.get("bullet_id"))
    powder_id = _safe_int(selection.get("powder_id"))
    primer_id = _safe_int(selection.get("primer_id"))
    case_id = _safe_int(selection.get("case_id"))

    case_learning_profile: dict[str, Any] = {}
    if case_id is not None and hasattr(database, "get_case_learning_profile"):
        case_learning_profile = database.get_case_learning_profile(case_id)

    return {
        "selection": selection,
        "bullet": _get_row_by_id(database, "bullets", bullet_id),
        "powder": _get_row_by_id(database, "powder", powder_id),
        "primer": _get_row_by_id(database, "primers", primer_id),
        "case": _get_row_by_id(database, "cases", case_id),
        "case_learning_profile": case_learning_profile,
    }


def _resolve_component_lot_by_number(
    database: Database,
    component_types: tuple[str, ...],
    component_id: int | None,
    lot_number: str,
) -> dict[str, Any] | None:
    if (
        component_id is None
        or not lot_number
        or not _table_exists(database, "component_lots")
    ):
        return None
    for component_type in component_types:
        row = _query_single_row(
            database,
            """
            SELECT *
            FROM component_lots
            WHERE component_type = ? AND component_id = ? AND lot_number = ?
            LIMIT 1
            """,
            (component_type, component_id, lot_number),
        )
        if row:
            return row
    return None


def _resolve_bullet_lot_by_number(
    database: Database,
    bullet_id: int | None,
    lot_number: str,
) -> dict[str, Any] | None:
    if (
        bullet_id is None
        or not lot_number
        or not _table_exists(database, "bullet_lots")
    ):
        return None
    return _query_single_row(
        database,
        "SELECT * FROM bullet_lots WHERE bullet_id = ? AND lot_number = ? LIMIT 1",
        (bullet_id, lot_number),
    )


def _attach_lot_learning_profile(
    database: Database,
    lot_row: dict[str, Any] | None,
    *,
    source_table: str,
) -> dict[str, Any] | None:
    if not lot_row:
        return None
    lot_id = _safe_int(lot_row.get("id"))
    if lot_id is None:
        return lot_row

    learning_profile = None
    if source_table == "component_lots" and _table_exists(
        database, "component_lot_learning_profiles"
    ):
        learning_profile = _query_single_row(
            database,
            "SELECT * FROM component_lot_learning_profiles WHERE component_lot_id = ? LIMIT 1",
            (lot_id,),
        )
    elif source_table == "bullet_lots" and _table_exists(
        database, "bullet_lot_learning_profiles"
    ):
        learning_profile = _query_single_row(
            database,
            "SELECT * FROM bullet_lot_learning_profiles WHERE bullet_lot_id = ? LIMIT 1",
            (lot_id,),
        )

    enriched = dict(lot_row)
    enriched["source_table"] = source_table
    enriched["learning_profile"] = learning_profile or {}
    return enriched


def _resolve_lot_context(
    database: Database,
    selection: dict[str, Any],
    components: dict[str, Any],
) -> dict[str, Any]:
    bullet_id = _safe_int(selection.get("bullet_id"))
    powder_id = _safe_int(selection.get("powder_id"))
    primer_id = _safe_int(selection.get("primer_id"))
    case_id = _safe_int(selection.get("case_id"))

    bullet_lot_id = _safe_int(selection.get("bullet_lot_id"))
    powder_lot_id = _safe_int(selection.get("powder_lot_id"))
    primer_lot_id = _safe_int(selection.get("primer_lot_id"))
    case_lot_id = _safe_int(selection.get("case_lot_id"))

    bullet_lot = None
    if bullet_lot_id is not None:
        bullet_lot = _get_row_by_id(database, "bullet_lots", bullet_lot_id)
        if bullet_lot:
            bullet_lot = _attach_lot_learning_profile(
                database, bullet_lot, source_table="bullet_lots"
            )
    if bullet_lot is None:
        bullet_lot_number = str(
            selection.get("bullet_lot_number") or selection.get("bullet_lot") or ""
        ).strip()
        bullet_lot = _resolve_bullet_lot_by_number(
            database, bullet_id, bullet_lot_number
        )
        if bullet_lot:
            bullet_lot = _attach_lot_learning_profile(
                database, bullet_lot, source_table="bullet_lots"
            )

    def resolve_component_lot(
        component_types: tuple[str, ...],
        component_id: int | None,
        lot_id: int | None,
        *number_keys: str,
    ) -> dict[str, Any] | None:
        row = None
        if lot_id is not None:
            row = _get_row_by_id(database, "component_lots", lot_id)
            if row and str(row.get("component_type") or "") not in component_types:
                row = None
        if row is None:
            lot_number = ""
            for key in number_keys:
                value = str(selection.get(key) or "").strip()
                if value:
                    lot_number = value
                    break
            row = _resolve_component_lot_by_number(
                database, component_types, component_id, lot_number
            )
        if row is None:
            return None
        return _attach_lot_learning_profile(
            database, row, source_table="component_lots"
        )

    return {
        "bullet": bullet_lot,
        "powder": resolve_component_lot(
            ("powder",),
            powder_id,
            powder_lot_id,
            "powder_lot_number",
            "powder_lot",
        ),
        "primer": resolve_component_lot(
            ("primer", "primers"),
            primer_id,
            primer_lot_id,
            "primer_lot_number",
            "primer_lot",
        ),
        "case": resolve_component_lot(
            ("case", "cases"),
            case_id,
            case_lot_id,
            "case_lot_number",
            "lot_number",
        ),
    }


def _resolve_evidence_context(
    database: Database,
    session_id: int,
    barrel_configuration_id: str | None = None,
) -> dict[str, Any]:
    chronograph_imports = (
        database.execute_query(
            "SELECT * FROM chronograph_imports WHERE load_session_id = ? ORDER BY import_date DESC, id DESC",
            (session_id,),
        )
        if _table_exists(database, "chronograph_imports")
        else []
    )
    test_results = (
        database.execute_query(
            "SELECT * FROM test_results WHERE load_session_id = ? ORDER BY id DESC",
            (session_id,),
        )
        if _table_exists(database, "test_results")
        else []
    )
    ladder_tests = (
        database.execute_query(
            "SELECT * FROM ladder_tests WHERE load_session_id = ? ORDER BY date DESC, id DESC",
            (session_id,),
        )
        if _table_exists(database, "ladder_tests")
        else []
    )
    batch_projects = (
        database.execute_query(
            "SELECT * FROM batch_projects WHERE load_session_id = ? ORDER BY updated_date DESC, id DESC",
            (session_id,),
        )
        if _table_exists(database, "batch_projects")
        else []
    )
    for row in batch_projects:
        row["analysis_json"] = _safe_json_dict(row.get("analysis_json"))
    batch_sessions = (
        database.execute_query(
            "SELECT * FROM batch_project_sessions WHERE load_session_id = ? ORDER BY session_date DESC, id DESC",
            (session_id,),
        )
        if _table_exists(database, "batch_project_sessions")
        else []
    )
    for row in batch_sessions:
        row["analysis_json"] = _safe_json_dict(row.get("analysis_json"))
        row["primer_image_review"] = _extract_batch_session_primer_review(row)
        row["primer_image_images"] = _extract_batch_session_primer_images(row)
    shooting_sessions = (
        database.execute_query(
            "SELECT * FROM shooting_sessions WHERE load_session_id = ? ORDER BY date DESC, id DESC",
            (session_id,),
        )
        if _table_exists(database, "shooting_sessions")
        else []
    )
    pressure_signs = (
        database.execute_query(
            "SELECT * FROM pressure_signs WHERE load_session_id = ? ORDER BY date DESC, id DESC",
            (session_id,),
        )
        if _table_exists(database, "pressure_signs")
        else []
    )

    # Collect (group_size_mm, shot_count, charge_weight) tuples to track sample-size
    # robustness and charge-window learning. A 5-shot group is more trustworthy than
    # a 3-shot group at the same mm size. The charge weight of the best group is the
    # seed for persisting a learned charge window in learning_state_json.
    best_group_candidates: list[float] = []
    group_shot_counts: list[int] = (
        []
    )  # shot count for each group, parallel to candidates
    group_charge_weights: list[float | None] = (
        []
    )  # charge_weight_gr for each group, parallel
    for row in test_results:
        value = row.get("group_size_mm")
        if isinstance(value, (int, float)):
            best_group_candidates.append(float(value))
            group_shot_counts.append(
                int(row.get("shot_count") or row.get("velocity_count") or 0)
            )
            cw = row.get("charge_weight")
            group_charge_weights.append(
                float(cw) if isinstance(cw, (int, float)) else None
            )
    for row in batch_sessions:
        value = row.get("group_size_mm")
        if isinstance(value, (int, float)):
            best_group_candidates.append(float(value))
            group_shot_counts.append(int(row.get("shot_count") or 0))
            group_charge_weights.append(
                None
            )  # batch sessions don't carry per-row charge weight
    for row in shooting_sessions:
        value = row.get("best_group_mm") or row.get("avg_group_mm")
        if isinstance(value, (int, float)):
            best_group_candidates.append(float(value))
            group_shot_counts.append(int(row.get("shot_count") or 0))
            group_charge_weights.append(None)

    # Shot count and charge weight for the best (smallest) group; avg shot count.
    best_group_shot_count: int | None = None
    best_group_charge_gr: float | None = None
    avg_group_shot_count: float | None = None
    if best_group_candidates and group_shot_counts:
        best_idx = best_group_candidates.index(min(best_group_candidates))
        best_group_shot_count = (
            group_shot_counts[best_idx] if group_shot_counts[best_idx] > 0 else None
        )
        best_group_charge_gr = (
            group_charge_weights[best_idx]
            if best_idx < len(group_charge_weights)
            else None
        )
        nonzero = [c for c in group_shot_counts if c > 0]
        avg_group_shot_count = (
            round(sum(nonzero) / len(nonzero), 1) if nonzero else None
        )

    # Charge-window: collect all (charge_weight, group_size_mm) pairs from test_results.
    # Used downstream by refresh_load_session_measurement_summary to persist learned limits.
    charge_group_pairs: list[tuple[float, float]] = []
    for row in test_results:
        cw = row.get("charge_weight")
        gm = row.get("group_size_mm")
        if isinstance(cw, (int, float)) and isinstance(gm, (int, float)):
            charge_group_pairs.append((float(cw), float(gm)))

    latest_velocity = None
    if chronograph_imports:
        latest_velocity = chronograph_imports[0].get("velocity_avg")
    if latest_velocity is None:
        for row in reversed(test_results):
            value = row.get("velocity_avg")
            if isinstance(value, (int, float)):
                latest_velocity = float(value)
                break

    primer_review_enabled_sessions = 0
    primer_review_disabled_sessions = 0
    primer_review_sessions = 0
    primer_review_image_count = 0
    primer_review_notes = 0
    primer_review_latest_date = None
    for row in batch_sessions:
        review = (
            row.get("primer_image_review")
            if isinstance(row.get("primer_image_review"), dict)
            else {}
        )
        if review.get("enabled") is False:
            primer_review_disabled_sessions += 1
        elif review.get("enabled") is True:
            primer_review_enabled_sessions += 1
        images = (
            row.get("primer_image_images")
            if isinstance(row.get("primer_image_images"), list)
            else []
        )
        observation = str(review.get("observation") or "").strip()
        if images or observation:
            primer_review_sessions += 1
            primer_review_image_count += len(images)
            if observation:
                primer_review_notes += 1
            session_date = str(row.get("session_date") or row.get("date") or "").strip()
            if session_date and (
                primer_review_latest_date is None
                or session_date > str(primer_review_latest_date)
            ):
                primer_review_latest_date = session_date

    pressure_sign_primer_reviews = 0
    pressure_sign_linked_batches = 0
    pressure_sign_linked_rifle = 0
    pressure_sign_linked_barrel = 0
    for row in pressure_signs:
        image_path = str(row.get("primer_image_path") or "").strip()
        observation = str(row.get("primer_image_observation") or "").strip()
        if image_path or observation:
            pressure_sign_primer_reviews += 1
        if row.get("batch_session_id") not in (None, ""):
            pressure_sign_linked_batches += 1
        if row.get("rifle_id") not in (None, ""):
            pressure_sign_linked_rifle += 1
        if row.get("barrel_id") not in (None, ""):
            pressure_sign_linked_barrel += 1

    primer_review_status = "none"
    if (
        primer_review_disabled_sessions
        and primer_review_enabled_sessions == 0
        and primer_review_sessions == 0
    ):
        primer_review_status = "disabled"
    elif primer_review_sessions or pressure_sign_primer_reviews:
        primer_review_status = "captured"
    elif primer_review_enabled_sessions:
        primer_review_status = "enabled"

    batch_spread_signal_hint = None
    batch_spread_confidence = None
    batch_spread_reason = None
    batch_spread_watchouts: list[str] = []
    batch_spread_note_flags: list[str] = []
    batch_spread_max_wind_mps = None
    batch_spread_pattern_flags: list[str] = []
    batch_spread_axis_ratio = None
    batch_spread_poi_shift_mm = None
    batch_spread_control_plan: dict[str, Any] | None = None
    batch_spread_decision: dict[str, Any] | None = None
    batch_spread_profile_guidance: dict[str, Any] | None = None
    batch_spread_evidence_quality: dict[str, Any] | None = None
    batch_spread_learning_explanation: dict[str, Any] | None = None
    batch_spread_capture_checklist: dict[str, Any] | None = None
    batch_spread_validation_status: dict[str, Any] | None = None
    batch_comparison_basis: dict[str, Any] | None = None
    batch_comparison_advisory: dict[str, Any] | None = None
    batch_comparison_protocol: dict[str, Any] | None = None
    batch_comparison_explanation: dict[str, Any] | None = None
    batch_comparison_verdict: dict[str, Any] | None = None
    batch_comparison_acceptance: dict[str, Any] | None = None
    batch_comparison_acceptance_progress: dict[str, Any] | None = None
    batch_comparison_next_test: dict[str, Any] | None = None
    batch_comparison_status_board: dict[str, Any] | None = None
    batch_comparison_profile_priority: dict[str, Any] | None = None
    batch_comparison_mission_brief: dict[str, Any] | None = None
    batch_comparison_portfolio: dict[str, Any] | None = None
    batch_comparison_session_strategy: dict[str, Any] | None = None
    batch_comparison_campaign_view: dict[str, Any] | None = None
    batch_comparison_action_plan: dict[str, Any] | None = None
    batch_comparison_campaign_board: dict[str, Any] | None = None
    batch_comparison_session_queue: dict[str, Any] | None = None
    batch_comparison_session_manifest: dict[str, Any] | None = None
    batch_comparison_next_session_brief: dict[str, Any] | None = None
    batch_comparison_today_plan: dict[str, Any] | None = None
    batch_comparison_workboard: dict[str, Any] | None = None
    batch_comparison_checklist: dict[str, Any] | None = None
    batch_comparison_scorecard: dict[str, Any] | None = None
    batch_comparison_confidence: dict[str, Any] | None = None
    batch_comparison_learning_note: dict[str, Any] | None = None
    for row in batch_projects:
        analysis = (
            row.get("analysis_json")
            if isinstance(row.get("analysis_json"), dict)
            else {}
        )
        metrics = (
            analysis.get("metrics") if isinstance(analysis.get("metrics"), dict) else {}
        )
        hint = str(
            metrics.get("spread_signal_hint")
            or analysis.get("spread_signal_hint")
            or ""
        ).strip()
        if not hint:
            continue
        batch_spread_signal_hint = hint
        batch_spread_confidence = (
            str(
                metrics.get("spread_confidence")
                or analysis.get("spread_confidence")
                or ""
            ).strip()
            or None
        )
        batch_spread_reason = (
            str(
                metrics.get("spread_reason") or analysis.get("spread_reason") or ""
            ).strip()
            or None
        )
        raw_watchouts = (
            metrics.get("spread_watchouts") or analysis.get("spread_watchouts") or []
        )
        batch_spread_watchouts = [
            str(item).strip() for item in raw_watchouts if str(item).strip()
        ]
        raw_note_flags = (
            metrics.get("spread_note_flags") or analysis.get("spread_note_flags") or []
        )
        batch_spread_note_flags = [
            str(item).strip() for item in raw_note_flags if str(item).strip()
        ]
        batch_spread_max_wind_mps = _safe_float(
            metrics.get("spread_max_wind_mps") or analysis.get("spread_max_wind_mps")
        )
        raw_pattern_flags = (
            metrics.get("spread_pattern_flags")
            or analysis.get("spread_pattern_flags")
            or []
        )
        batch_spread_pattern_flags = [
            str(item).strip() for item in raw_pattern_flags if str(item).strip()
        ]
        batch_spread_axis_ratio = _safe_float(
            metrics.get("spread_axis_ratio") or analysis.get("spread_axis_ratio")
        )
        batch_spread_poi_shift_mm = _safe_float(
            metrics.get("spread_poi_shift_mm") or analysis.get("spread_poi_shift_mm")
        )
        raw_control_plan = metrics.get("spread_control_plan") or analysis.get(
            "spread_control_plan"
        )
        batch_spread_control_plan = (
            raw_control_plan if isinstance(raw_control_plan, dict) else None
        )
        raw_decision = metrics.get("spread_decision") or analysis.get("spread_decision")
        batch_spread_decision = raw_decision if isinstance(raw_decision, dict) else None
        raw_profile_guidance = metrics.get("spread_profile_guidance") or analysis.get(
            "spread_profile_guidance"
        )
        batch_spread_profile_guidance = (
            raw_profile_guidance if isinstance(raw_profile_guidance, dict) else None
        )
        raw_evidence_quality = metrics.get("spread_evidence_quality") or analysis.get(
            "spread_evidence_quality"
        )
        batch_spread_evidence_quality = (
            raw_evidence_quality if isinstance(raw_evidence_quality, dict) else None
        )
        raw_learning_explanation = metrics.get(
            "spread_learning_explanation"
        ) or analysis.get("spread_learning_explanation")
        batch_spread_learning_explanation = (
            raw_learning_explanation
            if isinstance(raw_learning_explanation, dict)
            else None
        )
        raw_capture_checklist = metrics.get("spread_capture_checklist") or analysis.get(
            "spread_capture_checklist"
        )
        batch_spread_capture_checklist = (
            raw_capture_checklist if isinstance(raw_capture_checklist, dict) else None
        )
        raw_validation_status = metrics.get("spread_validation_status") or analysis.get(
            "spread_validation_status"
        )
        batch_spread_validation_status = (
            raw_validation_status if isinstance(raw_validation_status, dict) else None
        )
        raw_comparison_basis = analysis.get("batch_comparison_basis")
        batch_comparison_basis = (
            raw_comparison_basis if isinstance(raw_comparison_basis, dict) else None
        )
        raw_comparison_advisory = analysis.get("batch_comparison_advisory")
        batch_comparison_advisory = (
            raw_comparison_advisory
            if isinstance(raw_comparison_advisory, dict)
            else None
        )
        raw_comparison_protocol = analysis.get("batch_comparison_protocol")
        batch_comparison_protocol = (
            raw_comparison_protocol
            if isinstance(raw_comparison_protocol, dict)
            else None
        )
        raw_comparison_explanation = analysis.get("batch_comparison_explanation")
        batch_comparison_explanation = (
            raw_comparison_explanation
            if isinstance(raw_comparison_explanation, dict)
            else None
        )
        raw_comparison_verdict = analysis.get("batch_comparison_verdict")
        batch_comparison_verdict = (
            raw_comparison_verdict if isinstance(raw_comparison_verdict, dict) else None
        )
        raw_comparison_acceptance = analysis.get("batch_comparison_acceptance")
        batch_comparison_acceptance = (
            raw_comparison_acceptance
            if isinstance(raw_comparison_acceptance, dict)
            else None
        )
        raw_comparison_acceptance_progress = analysis.get(
            "batch_comparison_acceptance_progress"
        )
        batch_comparison_acceptance_progress = (
            raw_comparison_acceptance_progress
            if isinstance(raw_comparison_acceptance_progress, dict)
            else None
        )
        raw_comparison_next_test = analysis.get("batch_comparison_next_test")
        batch_comparison_next_test = (
            raw_comparison_next_test
            if isinstance(raw_comparison_next_test, dict)
            else None
        )
        raw_comparison_status_board = analysis.get("batch_comparison_status_board")
        batch_comparison_status_board = (
            raw_comparison_status_board
            if isinstance(raw_comparison_status_board, dict)
            else None
        )
        raw_comparison_profile_priority = analysis.get(
            "batch_comparison_profile_priority"
        )
        batch_comparison_profile_priority = (
            raw_comparison_profile_priority
            if isinstance(raw_comparison_profile_priority, dict)
            else None
        )
        raw_comparison_mission_brief = analysis.get("batch_comparison_mission_brief")
        batch_comparison_mission_brief = (
            raw_comparison_mission_brief
            if isinstance(raw_comparison_mission_brief, dict)
            else None
        )
        raw_comparison_portfolio = analysis.get("batch_comparison_portfolio")
        batch_comparison_portfolio = (
            raw_comparison_portfolio
            if isinstance(raw_comparison_portfolio, dict)
            else None
        )
        raw_comparison_session_strategy = analysis.get(
            "batch_comparison_session_strategy"
        )
        batch_comparison_session_strategy = (
            raw_comparison_session_strategy
            if isinstance(raw_comparison_session_strategy, dict)
            else None
        )
        raw_comparison_campaign_view = analysis.get("batch_comparison_campaign_view")
        batch_comparison_campaign_view = (
            raw_comparison_campaign_view
            if isinstance(raw_comparison_campaign_view, dict)
            else None
        )
        raw_comparison_action_plan = analysis.get("batch_comparison_action_plan")
        batch_comparison_action_plan = (
            raw_comparison_action_plan
            if isinstance(raw_comparison_action_plan, dict)
            else None
        )
        raw_comparison_campaign_board = analysis.get("batch_comparison_campaign_board")
        batch_comparison_campaign_board = (
            raw_comparison_campaign_board
            if isinstance(raw_comparison_campaign_board, dict)
            else None
        )
        raw_comparison_session_queue = analysis.get("batch_comparison_session_queue")
        batch_comparison_session_queue = (
            raw_comparison_session_queue
            if isinstance(raw_comparison_session_queue, dict)
            else None
        )
        raw_comparison_session_manifest = analysis.get(
            "batch_comparison_session_manifest"
        )
        batch_comparison_session_manifest = (
            raw_comparison_session_manifest
            if isinstance(raw_comparison_session_manifest, dict)
            else None
        )
        raw_comparison_next_session_brief = analysis.get(
            "batch_comparison_next_session_brief"
        )
        batch_comparison_next_session_brief = (
            raw_comparison_next_session_brief
            if isinstance(raw_comparison_next_session_brief, dict)
            else None
        )
        raw_comparison_today_plan = analysis.get("batch_comparison_today_plan")
        batch_comparison_today_plan = (
            raw_comparison_today_plan
            if isinstance(raw_comparison_today_plan, dict)
            else None
        )
        raw_comparison_workboard = analysis.get("batch_comparison_workboard")
        batch_comparison_workboard = (
            raw_comparison_workboard
            if isinstance(raw_comparison_workboard, dict)
            else None
        )
        raw_comparison_checklist = analysis.get("batch_comparison_checklist")
        batch_comparison_checklist = (
            raw_comparison_checklist
            if isinstance(raw_comparison_checklist, dict)
            else None
        )
        raw_comparison_scorecard = analysis.get("batch_comparison_scorecard")
        batch_comparison_scorecard = (
            raw_comparison_scorecard
            if isinstance(raw_comparison_scorecard, dict)
            else None
        )
        raw_comparison_confidence = analysis.get("batch_comparison_confidence")
        batch_comparison_confidence = (
            raw_comparison_confidence
            if isinstance(raw_comparison_confidence, dict)
            else None
        )
        raw_comparison_learning_note = analysis.get("batch_comparison_learning_note")
        batch_comparison_learning_note = (
            raw_comparison_learning_note
            if isinstance(raw_comparison_learning_note, dict)
            else None
        )
        break

    return {
        "chronograph_imports": chronograph_imports,
        "test_results": test_results,
        "ladder_tests": ladder_tests,
        "batch_projects": batch_projects,
        "batch_sessions": batch_sessions,
        "shooting_sessions": shooting_sessions,
        "pressure_signs": pressure_signs,
        "primer_review": {
            "status": primer_review_status,
            "enabled_session_count": primer_review_enabled_sessions,
            "disabled_session_count": primer_review_disabled_sessions,
            "reviewed_session_count": primer_review_sessions,
            "review_image_count": primer_review_image_count,
            "review_note_count": primer_review_notes,
            "latest_review_date": primer_review_latest_date,
            "pressure_sign_review_count": pressure_sign_primer_reviews,
            "linked_pressure_sign_batch_count": pressure_sign_linked_batches,
            "linked_pressure_sign_rifle_count": pressure_sign_linked_rifle,
            "linked_pressure_sign_barrel_count": pressure_sign_linked_barrel,
        },
        "summary": {
            "chronograph_import_count": len(chronograph_imports),
            "test_result_count": len(test_results),
            "ladder_test_count": len(ladder_tests),
            "batch_count": len(batch_projects),
            "range_session_count": len(batch_sessions) + len(shooting_sessions),
            "setup_matched_session_count": sum(
                1
                for s in batch_sessions
                if not barrel_configuration_id
                or not str(s.get("barrel_configuration_id") or "").strip()
                or str(s.get("barrel_configuration_id") or "").strip()
                == barrel_configuration_id
            )
            + len(shooting_sessions),
            "setup_unmatched_session_count": sum(
                1
                for s in batch_sessions
                if barrel_configuration_id
                and str(s.get("barrel_configuration_id") or "").strip()
                and str(s.get("barrel_configuration_id") or "").strip()
                != barrel_configuration_id
            ),
            "pressure_sign_count": len(pressure_signs),
            "primer_review_status": primer_review_status,
            "primer_review_enabled_session_count": primer_review_enabled_sessions,
            "primer_review_disabled_session_count": primer_review_disabled_sessions,
            "primer_review_session_count": primer_review_sessions,
            "primer_review_image_count": primer_review_image_count,
            "pressure_sign_primer_review_count": pressure_sign_primer_reviews,
            "pressure_sign_linked_barrel_count": pressure_sign_linked_barrel,
            "has_measured_velocity": latest_velocity is not None,
            "has_measured_group": bool(best_group_candidates),
            "latest_avg_velocity_fps": latest_velocity,
            "best_group_mm": (
                min(best_group_candidates) if best_group_candidates else None
            ),
            "best_group_shot_count": best_group_shot_count,
            "best_group_charge_gr": best_group_charge_gr,
            "avg_group_shot_count": avg_group_shot_count,
            "charge_group_pairs": charge_group_pairs,
            "batch_spread_signal_hint": batch_spread_signal_hint,
            "batch_spread_confidence": batch_spread_confidence,
            "batch_spread_reason": batch_spread_reason,
            "batch_spread_watchouts": batch_spread_watchouts,
            "batch_spread_note_flags": batch_spread_note_flags,
            "batch_spread_max_wind_mps": batch_spread_max_wind_mps,
            "batch_spread_pattern_flags": batch_spread_pattern_flags,
            "batch_spread_axis_ratio": batch_spread_axis_ratio,
            "batch_spread_poi_shift_mm": batch_spread_poi_shift_mm,
            "batch_spread_control_plan": batch_spread_control_plan,
            "batch_spread_decision": batch_spread_decision,
            "batch_spread_profile_guidance": batch_spread_profile_guidance,
            "batch_spread_evidence_quality": batch_spread_evidence_quality,
            "batch_spread_learning_explanation": batch_spread_learning_explanation,
            "batch_spread_capture_checklist": batch_spread_capture_checklist,
            "batch_spread_validation_status": batch_spread_validation_status,
            "batch_comparison_basis": batch_comparison_basis,
            "batch_comparison_advisory": batch_comparison_advisory,
            "batch_comparison_protocol": batch_comparison_protocol,
            "batch_comparison_explanation": batch_comparison_explanation,
            "batch_comparison_verdict": batch_comparison_verdict,
            "batch_comparison_acceptance": batch_comparison_acceptance,
            "batch_comparison_acceptance_progress": batch_comparison_acceptance_progress,
            "batch_comparison_next_test": batch_comparison_next_test,
            "batch_comparison_status_board": batch_comparison_status_board,
            "batch_comparison_profile_priority": batch_comparison_profile_priority,
            "batch_comparison_mission_brief": batch_comparison_mission_brief,
            "batch_comparison_portfolio": batch_comparison_portfolio,
            "batch_comparison_session_strategy": batch_comparison_session_strategy,
            "batch_comparison_campaign_view": batch_comparison_campaign_view,
            "batch_comparison_action_plan": batch_comparison_action_plan,
            "batch_comparison_campaign_board": batch_comparison_campaign_board,
            "batch_comparison_session_queue": batch_comparison_session_queue,
            "batch_comparison_session_manifest": batch_comparison_session_manifest,
            "batch_comparison_next_session_brief": batch_comparison_next_session_brief,
            "batch_comparison_today_plan": batch_comparison_today_plan,
            "batch_comparison_workboard": batch_comparison_workboard,
            "batch_comparison_checklist": batch_comparison_checklist,
            "batch_comparison_scorecard": batch_comparison_scorecard,
            "batch_comparison_confidence": batch_comparison_confidence,
            "batch_comparison_learning_note": batch_comparison_learning_note,
        },
    }


def _profile_snapshot(
    profile: dict[str, Any] | None,
    *,
    fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    raw = dict(profile or {})
    snapshot = {
        "status": raw.get("status") or "insufficient_data",
        "confidence_score": _safe_float(raw.get("confidence_score")) or 0.0,
        "confidence_label": str(raw.get("confidence_label") or "ingen data ennå"),
        "data_points": _safe_int(raw.get("data_points")) or 0,
        "drift_flag": raw.get("drift_flag"),
    }
    for field in fields:
        snapshot[field] = raw.get(field)
    return snapshot


def _resolve_learning_context(
    session: dict[str, Any],
    barrel: dict[str, Any],
    components: dict[str, Any],
    lots: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    evidence_summary = (
        evidence.get("summary") if isinstance(evidence.get("summary"), dict) else {}
    )
    session_learning = (
        session.get("learning_state_json")
        if isinstance(session.get("learning_state_json"), dict)
        else {}
    )

    barrel_profile = (
        barrel.get("learning_profile")
        if isinstance(barrel.get("learning_profile"), dict)
        else {}
    )
    case_profile = (
        components.get("case_learning_profile")
        if isinstance(components.get("case_learning_profile"), dict)
        else {}
    )

    lot_snapshots: dict[str, Any] = {}
    lot_scores: list[float] = []
    for lot_name in ("bullet", "powder", "primer", "case"):
        lot_row = lots.get(lot_name) if isinstance(lots, dict) else None
        profile = (
            lot_row.get("learning_profile")
            if isinstance(lot_row, dict)
            and isinstance(lot_row.get("learning_profile"), dict)
            else {}
        )
        fields: tuple[str, ...] = ()
        if lot_name == "powder":
            fields = (
                "velocity_offset_fps",
                "temp_sensitivity_fps_per_c",
                "typical_es_fps",
            )
        elif lot_name == "bullet":
            fields = ("typical_group_moa", "best_recorded_moa", "qc_pass_rate_percent")
        elif lot_name == "primer":
            fields = ("velocity_offset_fps", "typical_es_fps", "pressure_watch_count")
        elif lot_name == "case":
            fields = ("avg_velocity_fps", "velocity_offset_fps", "pressure_watch_count")
        snapshot = _profile_snapshot(profile, fields=fields)
        snapshot["lot_number"] = (
            lot_row.get("lot_number") if isinstance(lot_row, dict) else None
        )
        lot_snapshots[lot_name] = snapshot
        lot_scores.append(float(snapshot.get("confidence_score") or 0.0))

    barrel_snapshot = _profile_snapshot(
        barrel_profile,
        fields=(
            "chrono_samples",
            "target_samples",
            "temperature_samples",
            "calibration_offset_fps",
            "temp_sensitivity_fps_per_c",
            "cold_bore_shift_moa",
            "estimated_barrel_life_used_percent",
        ),
    )
    case_snapshot = _profile_snapshot(
        case_profile,
        fields=(
            "h2o_samples",
            "avg_case_capacity_h2o",
            "capacity_spread_h2o",
            "typical_times_fired",
            "estimated_remaining_cycles",
        ),
    )

    scores = [
        float(barrel_snapshot.get("confidence_score") or 0.0),
        float(case_snapshot.get("confidence_score") or 0.0),
        *lot_scores,
    ]
    non_zero_scores = [score for score in scores if score > 0.0]
    aggregate_score = (
        round(sum(non_zero_scores) / len(non_zero_scores), 1)
        if non_zero_scores
        else 0.0
    )
    session_confidence = _safe_float(session.get("confidence_score"))
    if session_confidence is not None and session_confidence > 0.0:
        aggregate_score = (
            round((aggregate_score + session_confidence) / 2.0, 1)
            if aggregate_score > 0.0
            else round(session_confidence, 1)
        )

    if aggregate_score >= 80.0:
        aggregate_label = "godt kalibrert"
    elif aggregate_score >= 55.0:
        aggregate_label = "delvis kalibrert"
    elif aggregate_score >= 25.0:
        aggregate_label = "tidlig læring"
    else:
        aggregate_label = "rå modell"

    weakest_link = None
    weakest_score = None
    candidates = {
        "pipe": float(barrel_snapshot.get("confidence_score") or 0.0),
        "hylse": float(case_snapshot.get("confidence_score") or 0.0),
        "kulelot": float(
            lot_snapshots.get("bullet", {}).get("confidence_score") or 0.0
        ),
        "kruttlot": float(
            lot_snapshots.get("powder", {}).get("confidence_score") or 0.0
        ),
        "primerlot": float(
            lot_snapshots.get("primer", {}).get("confidence_score") or 0.0
        ),
        "hylselot": float(lot_snapshots.get("case", {}).get("confidence_score") or 0.0),
    }
    for label, score in candidates.items():
        if weakest_score is None or score < weakest_score:
            weakest_link = label
            weakest_score = score

    next_focus = str(session.get("next_action") or "").strip() or None
    if not next_focus:
        if not evidence_summary.get("has_measured_velocity"):
            next_focus = "capture_measured_velocity"
        elif not evidence_summary.get("has_measured_group"):
            next_focus = "capture_group_validation"
        elif weakest_link == "pipe":
            next_focus = "strengthen_barrel_profile"
        elif weakest_link in {"kruttlot", "primerlot", "hylselot", "kulelot"}:
            next_focus = "verify_component_lot"

    # Prefer the canonical model_status persisted by refresh_load_session_measurement_summary
    # (raw / partially_calibrated / well_calibrated) over the computed confidence label.
    persisted_model_status = str(session_learning.get("model_status") or "").strip()
    model_status = (
        persisted_model_status
        if persisted_model_status in {"raw", "partially_calibrated", "well_calibrated"}
        else aggregate_label
    )

    return {
        "aggregate": {
            "confidence_score": aggregate_score,
            "confidence_label": aggregate_label,
            "model_status": model_status,
            "weakest_link": weakest_link,
            "next_focus": next_focus,
        },
        "barrel": barrel_snapshot,
        "case": case_snapshot,
        "lots": lot_snapshots,
        "session": dict(session_learning),
    }


def _resolve_recommendation_context(session: dict[str, Any]) -> dict[str, Any]:
    recommendation_payload = (
        session.get("recommendation_json")
        if isinstance(session.get("recommendation_json"), dict)
        else {}
    )
    baseline = (
        recommendation_payload.get("baseline")
        if isinstance(recommendation_payload.get("baseline"), dict)
        else {}
    )
    # If a learned charge window has been persisted in learning_state_json and the
    # existing baseline does not already carry a learned charge, promote the learned
    # center into the baseline so the engine treats it as charge_source="learned".
    learning_state = (
        session.get("learning_state_json")
        if isinstance(session.get("learning_state_json"), dict)
        else {}
    )
    charge_window = (
        learning_state.get("charge_window")
        if isinstance(learning_state.get("charge_window"), dict)
        else None
    )
    if (
        charge_window is not None
        and str(baseline.get("charge_source") or "").strip().lower() != "learned"
    ):
        center_gr = charge_window.get("center_gr")
        if isinstance(center_gr, (int, float)):
            baseline = dict(baseline)
            baseline["charge_gr"] = float(center_gr)
            baseline["charge_source"] = "learned"
            baseline["charge_window_min_gr"] = charge_window.get("min_gr")
            baseline["charge_window_max_gr"] = charge_window.get("max_gr")

    # Restore persisted seating window when the baseline doesn't already carry one.
    seating_window = (
        learning_state.get("seating_window")
        if isinstance(learning_state.get("seating_window"), dict)
        else None
    )
    if seating_window is not None and not isinstance(
        baseline.get("seating_window_mm"), (list, tuple)
    ):
        sw_min = seating_window.get("min_mm")
        sw_max = seating_window.get("max_mm")
        if isinstance(sw_min, (int, float)) and isinstance(sw_max, (int, float)):
            baseline = dict(baseline)
            baseline["seating_window_mm"] = [float(sw_min), float(sw_max)]
            baseline["seating_source"] = str(
                seating_window.get("source") or "persisted"
            )

    return {
        "active_settings": (
            recommendation_payload.get("active_settings")
            if isinstance(recommendation_payload.get("active_settings"), dict)
            else {}
        ),
        "recommendation": (
            recommendation_payload.get("recommendation")
            if isinstance(recommendation_payload.get("recommendation"), dict)
            else {}
        ),
        "baseline": baseline,
        "control_state": (
            recommendation_payload.get("control_state")
            if isinstance(recommendation_payload.get("control_state"), dict)
            else {}
        ),
        "pressure_assessment": (
            recommendation_payload.get("pressure_assessment")
            if isinstance(recommendation_payload.get("pressure_assessment"), dict)
            else {}
        ),
        "internal_ballistics": (
            recommendation_payload.get("internal_ballistics")
            if isinstance(recommendation_payload.get("internal_ballistics"), dict)
            else {}
        ),
    }


def _build_runtime_context(
    session: dict[str, Any],
    rifle: dict[str, Any] | None,
    barrel: dict[str, Any],
    selection: dict[str, Any],
    lots: dict[str, Any],
) -> dict[str, Any]:
    rifle_row = dict(rifle or {})
    barrel_row = dict(barrel or {})
    component_lots = dict(lots or {})

    def _lot_number(name: str) -> str | None:
        row = component_lots.get(name)
        if not isinstance(row, dict):
            return None
        value = str(row.get("lot_number") or "").strip()
        return value or None

    return {
        "load_session_id": _safe_int(session.get("id")),
        "session_uid": str(session.get("session_uid") or "").strip() or None,
        "workflow_id": _safe_int(session.get("workflow_id")),
        "status": str(session.get("status") or "").strip() or None,
        "lifecycle_stage": str(session.get("lifecycle_stage") or "").strip() or None,
        "rifle_id": _safe_int(session.get("rifle_id"))
        or _safe_int(rifle_row.get("id")),
        "rifle_name": str(
            session.get("rifle_name") or rifle_row.get("name") or ""
        ).strip()
        or None,
        "rifle_caliber": str(
            session.get("rifle_caliber") or rifle_row.get("caliber") or ""
        ).strip()
        or None,
        "barrel_id": barrel_row.get("barrel_id"),
        "barrel_name": barrel_row.get("barrel_name"),
        "barrel_configuration_id": barrel_row.get("barrel_configuration_id"),
        "barrel_configuration_name": barrel_row.get("barrel_configuration_name"),
        "usage_profile_key": str(session.get("usage_profile_key") or "").strip()
        or None,
        "usage_profile_name": str(session.get("usage_profile_name") or "").strip()
        or None,
        "bullet_id": _safe_int(selection.get("bullet_id")),
        "powder_id": _safe_int(selection.get("powder_id")),
        "primer_id": _safe_int(selection.get("primer_id")),
        "case_id": _safe_int(selection.get("case_id")),
        "bullet_lot_id": _safe_int(selection.get("bullet_lot_id")),
        "powder_lot_id": _safe_int(selection.get("powder_lot_id")),
        "primer_lot_id": _safe_int(selection.get("primer_lot_id")),
        "case_lot_id": _safe_int(selection.get("case_lot_id")),
        "bullet_lot_number": _lot_number("bullet"),
        "powder_lot_number": _lot_number("powder"),
        "primer_lot_number": _lot_number("primer"),
        "case_lot_number": _lot_number("case"),
        "next_action": str(session.get("next_action") or "").strip() or None,
        "safety_status": str(session.get("safety_status") or "").strip() or None,
        "confidence_label": str(session.get("confidence_label") or "").strip() or None,
        "confidence_score": _safe_float(session.get("confidence_score")),
        "created_date": session.get("created_date"),
        "updated_date": session.get("updated_date"),
    }


def _build_runtime_identity(
    session: dict[str, Any],
    rifle: dict[str, Any] | None,
    barrel: dict[str, Any],
    components: dict[str, Any],
    lots: dict[str, Any],
) -> dict[str, Any]:
    component_rows = dict(components or {})
    lot_rows = dict(lots or {})
    rifle_row = dict(rifle or {})
    barrel_row = dict(barrel or {})

    def _component_identity(name: str) -> dict[str, Any]:
        row = component_rows.get(name)
        if not isinstance(row, dict):
            return {"id": None, "label": None}
        manufacturer = str(row.get("manufacturer") or row.get("make") or "").strip()
        model_name = str(row.get("name") or row.get("type") or "").strip()
        label = (
            " ".join(bit for bit in (manufacturer, model_name) if bit).strip() or None
        )
        return {
            "id": _safe_int(row.get("id")),
            "label": label,
        }

    def _lot_identity(name: str) -> dict[str, Any]:
        row = lot_rows.get(name)
        if not isinstance(row, dict):
            return {"id": None, "lot_number": None}
        return {
            "id": _safe_int(row.get("id")),
            "lot_number": str(row.get("lot_number") or "").strip() or None,
            "source_table": str(row.get("source_table") or "").strip() or None,
        }

    return {
        "session_uid": str(session.get("session_uid") or "").strip() or None,
        "rifle": {
            "id": _safe_int(session.get("rifle_id")) or _safe_int(rifle_row.get("id")),
            "label": str(
                session.get("rifle_name") or rifle_row.get("name") or ""
            ).strip()
            or None,
            "caliber": str(
                session.get("rifle_caliber") or rifle_row.get("caliber") or ""
            ).strip()
            or None,
        },
        "barrel": {
            "id": barrel_row.get("barrel_id"),
            "label": barrel_row.get("barrel_name"),
            "configuration_id": barrel_row.get("barrel_configuration_id"),
            "configuration_label": barrel_row.get("barrel_configuration_name"),
        },
        "usage": {
            "key": str(session.get("usage_profile_key") or "").strip() or None,
            "label": str(session.get("usage_profile_name") or "").strip() or None,
        },
        "components": {
            "bullet": _component_identity("bullet"),
            "powder": _component_identity("powder"),
            "primer": _component_identity("primer"),
            "case": _component_identity("case"),
        },
        "lots": {
            "bullet": _lot_identity("bullet"),
            "powder": _lot_identity("powder"),
            "primer": _lot_identity("primer"),
            "case": _lot_identity("case"),
        },
    }


def build_load_session_runtime(
    database: Database, session_id: int
) -> dict[str, Any] | None:
    session = get_load_development_session(database, session_id)
    if not session:
        return None

    selection = _component_selection(session)
    components = _resolve_component_context(database, selection)
    lots = _resolve_lot_context(database, selection, components)
    rifle = _get_row_by_id(database, "rifles", session.get("rifle_id"))
    barrel = _resolve_barrel_context(database, session)
    session_barrel_cfg_id = (
        str(session.get("barrel_configuration_id") or "").strip() or None
    )
    evidence = _resolve_evidence_context(
        database, session_id, barrel_configuration_id=session_barrel_cfg_id
    )

    runtime = {
        "session": session,
        "rifle": rifle,
        "barrel": barrel,
        "components": components,
        "lots": lots,
        "evidence": evidence,
        "recommendation": _resolve_recommendation_context(session),
        "learning": _resolve_learning_context(
            session, barrel, components, lots, evidence
        ),
        "context": _build_runtime_context(session, rifle, barrel, selection, lots),
        "identity": _build_runtime_identity(session, rifle, barrel, components, lots),
        "status": {
            "session_status": session.get("status"),
            "lifecycle_stage": session.get("lifecycle_stage"),
            "safety_status": session.get("safety_status"),
            "confidence_label": session.get("confidence_label"),
            "confidence_score": session.get("confidence_score"),
            "next_action": session.get("next_action"),
        },
    }
    runtime["smart_engine"] = build_smart_ammo_engine_from_runtime(runtime)
    runtime["delta"] = build_load_session_runtime_delta(runtime)
    return runtime


def enrich_workflow_context_from_session(
    database: Database | None,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    resolved = dict(context) if isinstance(context, dict) else {}
    if database is None:
        return resolved

    load_session_id = _safe_int(resolved.get("load_session_id"))
    if load_session_id is None:
        return resolved

    runtime = build_load_session_runtime(database, load_session_id)
    if not isinstance(runtime, dict):
        return resolved

    runtime_context = (
        runtime.get("context") if isinstance(runtime.get("context"), dict) else {}
    )
    runtime_identity = (
        runtime.get("identity") if isinstance(runtime.get("identity"), dict) else {}
    )
    identity_rifle = (
        runtime_identity.get("rifle")
        if isinstance(runtime_identity.get("rifle"), dict)
        else {}
    )
    identity_barrel = (
        runtime_identity.get("barrel")
        if isinstance(runtime_identity.get("barrel"), dict)
        else {}
    )
    identity_usage = (
        runtime_identity.get("usage")
        if isinstance(runtime_identity.get("usage"), dict)
        else {}
    )

    resolved["load_session_id"] = load_session_id

    canonical_fields = {
        "ammo_profile_id": (
            runtime.get("session", {}).get("ammo_profile_id")
            if isinstance(runtime.get("session"), dict)
            else None
        ),
        "rifle_id": runtime_context.get("rifle_id"),
        "rifle_name": runtime_context.get("rifle_name") or identity_rifle.get("label"),
        "barrel_id": runtime_context.get("barrel_id"),
        "barrel_name": runtime_context.get("barrel_name")
        or identity_barrel.get("label"),
        "barrel_configuration_id": runtime_context.get("barrel_configuration_id")
        or identity_barrel.get("configuration_id"),
        "barrel_configuration_name": runtime_context.get("barrel_configuration_name")
        or identity_barrel.get("configuration_label"),
        "usage_profile_key": runtime_context.get("usage_profile_key")
        or identity_usage.get("key"),
        "usage_profile_name": runtime_context.get("usage_profile_name")
        or identity_usage.get("label"),
        "status": runtime_context.get("status"),
        "lifecycle_stage": runtime_context.get("lifecycle_stage"),
        "confidence_label": runtime_context.get("confidence_label"),
        "safety_status": runtime_context.get("safety_status"),
        "next_action": runtime_context.get("next_action"),
    }
    for key, value in canonical_fields.items():
        if value not in (None, ""):
            resolved[key] = value

    return resolved


def build_active_workflow_context_from_settings(
    settings: QSettings,
    database: Database | None = None,
    *,
    int_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    workflow_id = _safe_int(settings.value("workflow_context/workflow_id"))
    load_session_id = _safe_int(settings.value("workflow_context/load_session_id"))
    if workflow_id is None and load_session_id is None:
        return {}

    context: dict[str, Any] = {
        "workflow_id": workflow_id,
        "workflow_name": str(
            settings.value("workflow_context/workflow_name", "") or ""
        ).strip(),
        "load_session_id": load_session_id,
        "rifle_id": settings.value("workflow_context/rifle_id"),
        "barrel_id": settings.value("workflow_context/barrel_id"),
        "barrel_name": str(
            settings.value("workflow_context/barrel_name", "") or ""
        ).strip(),
        "barrel_configuration_id": settings.value(
            "workflow_context/barrel_configuration_id"
        ),
        "barrel_configuration_name": str(
            settings.value("workflow_context/barrel_configuration_name", "") or ""
        ).strip(),
        "created_date": str(
            settings.value("workflow_context/created_date", "") or ""
        ).strip(),
    }
    for field_name in int_fields:
        value = _safe_int(settings.value(f"workflow_context/{field_name}"))
        if value is None:
            continue
        context[field_name] = value

    return enrich_workflow_context_from_session(database, context)


def get_active_load_session_id_from_settings(settings: QSettings) -> int | None:
    return _safe_int(settings.value("workflow_context/load_session_id"))


def store_workflow_context_in_settings(
    settings: QSettings,
    context: dict[str, Any] | None,
    *,
    sync: bool = False,
) -> None:
    payload = dict(context) if isinstance(context, dict) else {}
    for key, value in payload.items():
        settings.setValue(f"workflow_context/{key}", value)
    if not sync:
        return
    try:
        settings.sync()
    except Exception:
        pass


def refresh_load_session_measurement_summary(
    database: Database | None,
    session_id: int | None,
    *,
    source: str | None = None,
) -> dict[str, Any] | None:
    resolved_session_id = _safe_int(session_id)
    if database is None or resolved_session_id is None:
        return None

    runtime = build_load_session_runtime(database, resolved_session_id)
    if not isinstance(runtime, dict):
        return None

    evidence = (
        runtime.get("evidence") if isinstance(runtime.get("evidence"), dict) else {}
    )
    summary = (
        evidence.get("summary") if isinstance(evidence.get("summary"), dict) else {}
    )
    if not summary:
        return None

    recommendation_ctx = (
        runtime.get("recommendation")
        if isinstance(runtime.get("recommendation"), dict)
        else {}
    )
    learning = (
        runtime.get("learning") if isinstance(runtime.get("learning"), dict) else {}
    )
    learning_aggregate = (
        learning.get("aggregate") if isinstance(learning.get("aggregate"), dict) else {}
    )
    learning_barrel = (
        learning.get("barrel") if isinstance(learning.get("barrel"), dict) else {}
    )
    learning_case = (
        learning.get("case") if isinstance(learning.get("case"), dict) else {}
    )
    learning_lots = (
        learning.get("lots") if isinstance(learning.get("lots"), dict) else {}
    )

    chrono_count = int(summary.get("chronograph_import_count") or 0)
    test_count = int(summary.get("test_result_count") or 0)
    batch_count = int(summary.get("batch_count") or 0)
    pressure_sign_count = int(summary.get("pressure_sign_count") or 0)
    range_session_count = int(summary.get("range_session_count") or 0)
    has_measured_velocity = bool(summary.get("has_measured_velocity"))
    has_measured_group = bool(summary.get("has_measured_group"))
    weakest_link = str(learning_aggregate.get("weakest_link") or "").strip() or None

    if chrono_count >= 3 and test_count >= 3:
        data_strength = "high"
    elif chrono_count >= 1 and test_count >= 1:
        data_strength = "medium"
    elif (
        chrono_count >= 1
        or test_count >= 1
        or batch_count >= 1
        or range_session_count >= 1
    ):
        data_strength = "low"
    else:
        data_strength = "none"

    drift_flags = []
    for snapshot in (
        learning_barrel,
        learning_case,
        (
            learning_lots.get("powder")
            if isinstance(learning_lots.get("powder"), dict)
            else {}
        ),
        (
            learning_lots.get("bullet")
            if isinstance(learning_lots.get("bullet"), dict)
            else {}
        ),
        (
            learning_lots.get("primer")
            if isinstance(learning_lots.get("primer"), dict)
            else {}
        ),
        (
            learning_lots.get("case")
            if isinstance(learning_lots.get("case"), dict)
            else {}
        ),
    ):
        flag = str((snapshot or {}).get("drift_flag") or "").strip()
        if flag:
            drift_flags.append(flag)

    if pressure_sign_count > 0 or drift_flags:
        drift_state = "watch"
    elif (
        data_strength in {"medium", "high"}
        and has_measured_velocity
        and has_measured_group
    ):
        drift_state = "stable"
    elif has_measured_velocity or has_measured_group:
        drift_state = "monitor"
    else:
        drift_state = "unknown"

    batch_spread_signal_hint = str(
        summary.get("batch_spread_signal_hint") or ""
    ).strip()
    signal_hint = "insufficient_evidence"
    if pressure_sign_count > 0:
        signal_hint = "pressure_or_ammo"
    elif batch_spread_signal_hint:
        signal_hint = batch_spread_signal_hint
    elif (
        weakest_link in {"kruttlot", "primerlot", "kulelot", "hylselot"}
        and has_measured_velocity
    ):
        signal_hint = "ammo_or_process_signal"
    elif weakest_link in {"pipe", "hylse"} and (
        has_measured_velocity or has_measured_group
    ):
        signal_hint = "possible_shooter_or_setup_signal"
    elif has_measured_group and not has_measured_velocity:
        signal_hint = "target_only"
    elif has_measured_velocity and not has_measured_group:
        signal_hint = "velocity_only"
    elif (
        has_measured_velocity
        and has_measured_group
        and data_strength in {"medium", "high"}
        and not weakest_link
    ):
        signal_hint = "mixed_but_stable"

    # Charge-window learning: persist the learned charge limits when evidence is
    # strong enough. The center is the charge that produced the best group; the
    # window covers all charges that produced groups within 1.5× the best result.
    # Requires: paired velocity+group data, medium+ data strength, no pressure signs.
    learned_charge_window: dict[str, Any] | None = None
    best_group_charge_gr = _safe_float(summary.get("best_group_charge_gr"))
    charge_group_pairs: list[tuple[float, float]] = (
        summary.get("charge_group_pairs") or []
    )
    if (
        best_group_charge_gr is not None
        and has_measured_velocity
        and has_measured_group
        and pressure_sign_count == 0
        and data_strength in {"medium", "high"}
        and charge_group_pairs
    ):
        best_group_mm = min(g for _, g in charge_group_pairs)
        ceiling_mm = best_group_mm * 1.5
        accepted_charges = [cw for cw, gm in charge_group_pairs if gm <= ceiling_mm]
        if accepted_charges:
            learned_charge_window = {
                "center_gr": round(best_group_charge_gr, 3),
                "min_gr": round(min(accepted_charges) - 0.05, 3),
                "max_gr": round(max(accepted_charges) + 0.05, 3),
                "source": "learned",
                "sample_count": len(accepted_charges),
                "confirmed_data_strength": data_strength,
            }

    evidence_updates = {
        "chronograph_import_count": summary.get("chronograph_import_count"),
        "test_result_count": summary.get("test_result_count"),
        "batch_count": summary.get("batch_count"),
        "range_session_count": summary.get("range_session_count"),
        "pressure_sign_count": summary.get("pressure_sign_count"),
        "primer_review_status": summary.get("primer_review_status"),
        "primer_review_session_count": summary.get("primer_review_session_count"),
        "primer_review_enabled_session_count": summary.get(
            "primer_review_enabled_session_count"
        ),
        "primer_review_disabled_session_count": summary.get(
            "primer_review_disabled_session_count"
        ),
        "primer_review_image_count": summary.get("primer_review_image_count"),
        "pressure_sign_primer_review_count": summary.get(
            "pressure_sign_primer_review_count"
        ),
        "has_measured_velocity": summary.get("has_measured_velocity"),
        "has_measured_group": summary.get("has_measured_group"),
        "latest_avg_velocity_fps": summary.get("latest_avg_velocity_fps"),
        "best_group_mm": summary.get("best_group_mm"),
        "data_strength": data_strength,
        "drift_state": drift_state,
        "signal_hint": signal_hint,
        "batch_spread_signal_hint": summary.get("batch_spread_signal_hint"),
        "batch_spread_confidence": summary.get("batch_spread_confidence"),
        "batch_spread_reason": summary.get("batch_spread_reason"),
        "batch_spread_watchouts": summary.get("batch_spread_watchouts"),
        "batch_spread_note_flags": summary.get("batch_spread_note_flags"),
        "batch_spread_max_wind_mps": summary.get("batch_spread_max_wind_mps"),
        "batch_spread_pattern_flags": summary.get("batch_spread_pattern_flags"),
        "batch_spread_axis_ratio": summary.get("batch_spread_axis_ratio"),
        "batch_spread_poi_shift_mm": summary.get("batch_spread_poi_shift_mm"),
        "batch_spread_control_plan": summary.get("batch_spread_control_plan"),
        "batch_spread_decision": summary.get("batch_spread_decision"),
        "batch_spread_profile_guidance": summary.get("batch_spread_profile_guidance"),
        "batch_spread_evidence_quality": summary.get("batch_spread_evidence_quality"),
        "batch_spread_learning_explanation": summary.get(
            "batch_spread_learning_explanation"
        ),
        "batch_spread_capture_checklist": summary.get("batch_spread_capture_checklist"),
        "batch_spread_validation_status": summary.get("batch_spread_validation_status"),
        "batch_comparison_basis": summary.get("batch_comparison_basis"),
        "batch_comparison_advisory": summary.get("batch_comparison_advisory"),
        "batch_comparison_protocol": summary.get("batch_comparison_protocol"),
        "batch_comparison_explanation": summary.get("batch_comparison_explanation"),
        "batch_comparison_verdict": summary.get("batch_comparison_verdict"),
        "batch_comparison_acceptance": summary.get("batch_comparison_acceptance"),
        "batch_comparison_acceptance_progress": summary.get(
            "batch_comparison_acceptance_progress"
        ),
        "batch_comparison_next_test": summary.get("batch_comparison_next_test"),
        "batch_comparison_status_board": summary.get("batch_comparison_status_board"),
        "batch_comparison_profile_priority": summary.get(
            "batch_comparison_profile_priority"
        ),
        "batch_comparison_mission_brief": summary.get("batch_comparison_mission_brief"),
        "batch_comparison_portfolio": summary.get("batch_comparison_portfolio"),
        "batch_comparison_session_strategy": summary.get(
            "batch_comparison_session_strategy"
        ),
        "batch_comparison_campaign_view": summary.get("batch_comparison_campaign_view"),
        "batch_comparison_action_plan": summary.get("batch_comparison_action_plan"),
        "batch_comparison_campaign_board": summary.get(
            "batch_comparison_campaign_board"
        ),
        "batch_comparison_session_queue": summary.get("batch_comparison_session_queue"),
        "batch_comparison_session_manifest": summary.get(
            "batch_comparison_session_manifest"
        ),
        "batch_comparison_next_session_brief": summary.get(
            "batch_comparison_next_session_brief"
        ),
        "batch_comparison_today_plan": summary.get("batch_comparison_today_plan"),
        "batch_comparison_workboard": summary.get("batch_comparison_workboard"),
        "batch_comparison_checklist": summary.get("batch_comparison_checklist"),
        "batch_comparison_scorecard": summary.get("batch_comparison_scorecard"),
        "batch_comparison_confidence": summary.get("batch_comparison_confidence"),
        "batch_comparison_learning_note": summary.get("batch_comparison_learning_note"),
        "drift_flags": drift_flags,
        "weakest_link": weakest_link,
        "measurement_sync_source": str(source or "").strip() or None,
    }

    # Seating-window persistence: read the current recommendation's seating_window_mm
    # and persist it in learning_state_json so re-opens restore the same seating window
    # without having to re-run the full ballistics model.
    recommendation_inner = (
        recommendation_ctx.get("recommendation")
        if isinstance(recommendation_ctx.get("recommendation"), dict)
        else {}
    )
    raw_seating_window = recommendation_inner.get("seating_window_mm")
    persisted_seating_window: dict[str, Any] | None = None
    if isinstance(raw_seating_window, (list, tuple)) and len(raw_seating_window) == 2:
        try:
            sw_min = float(raw_seating_window[0])
            sw_max = float(raw_seating_window[1])
            persisted_seating_window = {
                "min_mm": round(sw_min, 3),
                "max_mm": round(sw_max, 3),
                "source": "recommendation",
            }
        except (TypeError, ValueError):
            pass

    # Lot-drift snapshot: persist key drift signals per lot type so they survive
    # across sessions even if lot tables change. Only non-empty snapshots are stored.
    # The engine and delta builder can read these without re-querying lot tables.
    lot_drift_snapshot: dict[str, Any] = {}
    for lot_name in ("powder", "bullet", "primer", "case"):
        lot_snap = (
            learning_lots.get(lot_name) if isinstance(learning_lots, dict) else None
        )
        if not isinstance(lot_snap, dict):
            continue
        # Extract the meaningful drift fields, skip empty/zero-only snapshots.
        if lot_name == "powder":
            keep_fields = (
                "lot_number",
                "velocity_offset_fps",
                "temp_sensitivity_fps_per_c",
                "typical_es_fps",
                "drift_flag",
                "confidence_score",
            )
        elif lot_name == "bullet":
            keep_fields = (
                "lot_number",
                "typical_group_moa",
                "best_recorded_moa",
                "qc_pass_rate_percent",
                "drift_flag",
                "confidence_score",
            )
        elif lot_name == "primer":
            keep_fields = (
                "lot_number",
                "velocity_offset_fps",
                "typical_es_fps",
                "pressure_watch_count",
                "drift_flag",
                "confidence_score",
            )
        else:  # case
            keep_fields = (
                "lot_number",
                "avg_velocity_fps",
                "velocity_offset_fps",
                "pressure_watch_count",
                "drift_flag",
                "confidence_score",
            )
        entry = {
            k: lot_snap.get(k)
            for k in keep_fields
            if lot_snap.get(k) not in (None, 0, "", [])
        }
        if entry:
            lot_drift_snapshot[lot_name] = entry

    # model_status: canonical learning progress for the session.
    # raw = nothing measured; partially_calibrated = some data; well_calibrated = paired + strong.
    if not has_measured_velocity and not has_measured_group:
        model_status = "raw"
    elif (
        has_measured_velocity
        and has_measured_group
        and data_strength in {"medium", "high"}
        and pressure_sign_count == 0
    ):
        model_status = "well_calibrated"
    else:
        model_status = "partially_calibrated"

    learning_updates: dict[str, Any] = {
        "model_status": model_status,
        "summary": {
            "has_measured_velocity": has_measured_velocity,
            "has_measured_group": has_measured_group,
            "chronograph_import_count": chrono_count,
            "test_result_count": test_count,
            "batch_count": batch_count,
            "range_session_count": range_session_count,
            "pressure_sign_count": pressure_sign_count,
            "primer_review_status": str(
                summary.get("primer_review_status") or ""
            ).strip()
            or None,
            "data_strength": data_strength,
            "drift_state": drift_state,
            "signal_hint": signal_hint,
            "batch_spread_signal_hint": summary.get("batch_spread_signal_hint"),
            "batch_spread_confidence": summary.get("batch_spread_confidence"),
            "batch_spread_reason": summary.get("batch_spread_reason"),
            "batch_spread_watchouts": summary.get("batch_spread_watchouts"),
            "batch_spread_note_flags": summary.get("batch_spread_note_flags"),
            "batch_spread_max_wind_mps": summary.get("batch_spread_max_wind_mps"),
            "batch_spread_pattern_flags": summary.get("batch_spread_pattern_flags"),
            "batch_spread_axis_ratio": summary.get("batch_spread_axis_ratio"),
            "batch_spread_poi_shift_mm": summary.get("batch_spread_poi_shift_mm"),
            "batch_spread_control_plan": summary.get("batch_spread_control_plan"),
            "batch_spread_decision": summary.get("batch_spread_decision"),
            "batch_spread_profile_guidance": summary.get(
                "batch_spread_profile_guidance"
            ),
            "batch_spread_evidence_quality": summary.get(
                "batch_spread_evidence_quality"
            ),
            "batch_spread_learning_explanation": summary.get(
                "batch_spread_learning_explanation"
            ),
            "batch_spread_capture_checklist": summary.get(
                "batch_spread_capture_checklist"
            ),
            "batch_spread_validation_status": summary.get(
                "batch_spread_validation_status"
            ),
            "batch_comparison_basis": summary.get("batch_comparison_basis"),
            "batch_comparison_advisory": summary.get("batch_comparison_advisory"),
            "batch_comparison_protocol": summary.get("batch_comparison_protocol"),
            "batch_comparison_explanation": summary.get("batch_comparison_explanation"),
            "batch_comparison_verdict": summary.get("batch_comparison_verdict"),
            "batch_comparison_acceptance": summary.get("batch_comparison_acceptance"),
            "batch_comparison_acceptance_progress": summary.get(
                "batch_comparison_acceptance_progress"
            ),
            "batch_comparison_next_test": summary.get("batch_comparison_next_test"),
            "batch_comparison_status_board": summary.get(
                "batch_comparison_status_board"
            ),
            "batch_comparison_profile_priority": summary.get(
                "batch_comparison_profile_priority"
            ),
            "batch_comparison_mission_brief": summary.get(
                "batch_comparison_mission_brief"
            ),
            "batch_comparison_portfolio": summary.get("batch_comparison_portfolio"),
            "batch_comparison_session_strategy": summary.get(
                "batch_comparison_session_strategy"
            ),
            "batch_comparison_campaign_view": summary.get(
                "batch_comparison_campaign_view"
            ),
            "batch_comparison_action_plan": summary.get("batch_comparison_action_plan"),
            "batch_comparison_campaign_board": summary.get(
                "batch_comparison_campaign_board"
            ),
            "batch_comparison_session_queue": summary.get(
                "batch_comparison_session_queue"
            ),
            "batch_comparison_session_manifest": summary.get(
                "batch_comparison_session_manifest"
            ),
            "batch_comparison_next_session_brief": summary.get(
                "batch_comparison_next_session_brief"
            ),
            "batch_comparison_today_plan": summary.get("batch_comparison_today_plan"),
            "batch_comparison_workboard": summary.get("batch_comparison_workboard"),
            "batch_comparison_checklist": summary.get("batch_comparison_checklist"),
            "batch_comparison_scorecard": summary.get("batch_comparison_scorecard"),
            "batch_comparison_confidence": summary.get("batch_comparison_confidence"),
            "batch_comparison_learning_note": summary.get(
                "batch_comparison_learning_note"
            ),
            "drift_flags": drift_flags,
            "weakest_link": weakest_link,
            "measurement_sync_source": str(source or "").strip() or None,
        },
        # Charge-window learning: None when evidence is not yet strong enough;
        # populated when we have paired data + no pressure signs. The engine reads
        # this as charge_source="learned" when it builds the recommendation baseline.
        "charge_window": learned_charge_window,
        # Seating-window persistence: last recommended seating window from the
        # ballistics model. Survives session re-opens; read back in
        # _resolve_recommendation_context to restore the seating baseline.
        "seating_window": persisted_seating_window,
        # Lot-drift memory: point-in-time snapshot of observed lot characteristics.
        # Persisted so they survive session reopens and lot-table changes.
        # Only stored when at least one lot has recorded drift signals.
        "lot_drift": lot_drift_snapshot if lot_drift_snapshot else None,
    }

    updated = update_load_development_session(
        database,
        resolved_session_id,
        evidence_summary_updates=evidence_updates,
        learning_state_updates=learning_updates,
    )
    return updated


def build_load_session_runtime_delta(runtime: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(runtime, dict):
        return {
            "level": "unknown",
            "title": "Runtime delta unavailable",
            "summary": "No runtime context is available yet.",
            "items": [],
            "impacts": [],
            "focus_areas": [],
            "suggested_action": None,
        }

    session = runtime.get("session") if isinstance(runtime.get("session"), dict) else {}
    runtime_evidence = (
        runtime.get("evidence") if isinstance(runtime.get("evidence"), dict) else {}
    )
    runtime_evidence_summary = (
        runtime_evidence.get("summary")
        if isinstance(runtime_evidence.get("summary"), dict)
        else {}
    )
    intake = (
        session.get("intake_snapshot_json")
        if isinstance(session.get("intake_snapshot_json"), dict)
        else {}
    )
    evidence = (
        session.get("evidence_summary_json")
        if isinstance(session.get("evidence_summary_json"), dict)
        else {}
    )
    latest_result = (
        evidence.get("latest_result")
        if isinstance(evidence.get("latest_result"), dict)
        else {}
    )
    recommendation_context = (
        runtime.get("recommendation")
        if isinstance(runtime.get("recommendation"), dict)
        else {}
    )
    recommendation_baseline = (
        recommendation_context.get("baseline")
        if isinstance(recommendation_context.get("baseline"), dict)
        else {}
    )
    runtime_context = (
        runtime.get("context") if isinstance(runtime.get("context"), dict) else {}
    )
    learning_state_json = (
        session.get("learning_state_json")
        if isinstance(session.get("learning_state_json"), dict)
        else {}
    )
    persisted_lot_drift = (
        learning_state_json.get("lot_drift")
        if isinstance(learning_state_json.get("lot_drift"), dict)
        else {}
    )
    smart_engine = (
        runtime.get("smart_engine")
        if isinstance(runtime.get("smart_engine"), dict)
        else {}
    )
    smart_engine_result = (
        smart_engine.get("engine_result")
        if isinstance(smart_engine.get("engine_result"), dict)
        else {}
    )
    smart_candidate_profile = (
        smart_engine_result.get("candidate_profile")
        if isinstance(smart_engine_result.get("candidate_profile"), dict)
        else {}
    )
    smart_return_targets = (
        smart_engine_result.get("return_targets")
        if isinstance(smart_engine_result.get("return_targets"), dict)
        else {}
    )
    smart_branch_advisory = (
        smart_engine_result.get("branch_advisory")
        if isinstance(smart_engine_result.get("branch_advisory"), dict)
        else {}
    )
    smart_baseline_diagnostics = (
        smart_engine_result.get("baseline_diagnostics")
        if isinstance(smart_engine_result.get("baseline_diagnostics"), dict)
        else {}
    )
    smart_evidence_diagnostics = (
        smart_engine_result.get("evidence_diagnostics")
        if isinstance(smart_engine_result.get("evidence_diagnostics"), dict)
        else {}
    )
    smart_baseline_control = (
        smart_engine_result.get("baseline_control")
        if isinstance(smart_engine_result.get("baseline_control"), dict)
        else {}
    )
    smart_decisions = (
        smart_engine_result.get("decisions")
        if isinstance(smart_engine_result.get("decisions"), dict)
        else {}
    )
    smart_next_test = (
        smart_decisions.get("next_test")
        if isinstance(smart_decisions.get("next_test"), dict)
        else {}
    )
    smart_recommendation_stack = (
        smart_decisions.get("recommendation_stack")
        if isinstance(smart_decisions.get("recommendation_stack"), list)
        else []
    )
    smart_guidance = (
        smart_decisions.get("guidance")
        if isinstance(smart_decisions.get("guidance"), dict)
        else {}
    )
    smart_validation_gate = (
        smart_decisions.get("validation_gate")
        if isinstance(smart_decisions.get("validation_gate"), dict)
        else {}
    )
    smart_execution_plan = (
        smart_decisions.get("execution_plan")
        if isinstance(smart_decisions.get("execution_plan"), dict)
        else {}
    )
    smart_do_not_change_yet = (
        smart_decisions.get("do_not_change_yet")
        if isinstance(smart_decisions.get("do_not_change_yet"), list)
        else []
    )
    smart_blocked_by = (
        smart_decisions.get("blocked_by")
        if isinstance(smart_decisions.get("blocked_by"), list)
        else []
    )
    smart_recommendation_confidence = (
        smart_decisions.get("recommendation_confidence")
        if isinstance(smart_decisions.get("recommendation_confidence"), dict)
        else {}
    )
    smart_harmonics = (
        smart_engine_result.get("harmonics")
        if isinstance(smart_engine_result.get("harmonics"), dict)
        else {}
    )
    smart_bullet_fit = (
        smart_engine_result.get("bullet_fit")
        if isinstance(smart_engine_result.get("bullet_fit"), dict)
        else {}
    )
    smart_chamber_jump = (
        smart_engine_result.get("chamber_jump")
        if isinstance(smart_engine_result.get("chamber_jump"), dict)
        else {}
    )
    smart_candidate_robustness = str(
        smart_candidate_profile.get("robustness_level") or ""
    ).strip()
    smart_node_fit = str(smart_candidate_profile.get("node_fit") or "").strip()
    smart_next_action = str(smart_next_test.get("recommended_action") or "").strip()
    smart_next_reason = str(smart_next_test.get("why") or "").strip()
    smart_harmonic_tier = str(smart_harmonics.get("stability_tier") or "").strip()
    smart_bullet_fit_level = str(smart_bullet_fit.get("level") or "").strip()
    smart_bullet_fit_score = _safe_float(smart_bullet_fit.get("fit_score"))
    smart_bullet_fit_message = str(smart_bullet_fit.get("message") or "").strip()
    smart_jump_band = str(smart_chamber_jump.get("jump_band") or "").strip()
    smart_jump_summary = str(smart_chamber_jump.get("summary") or "").strip()
    smart_current_jump = _safe_float(smart_chamber_jump.get("current_jump_mm"))
    smart_guidance_title = str(smart_guidance.get("title") or "").strip()
    smart_guidance_setup = str(smart_guidance.get("setup_line") or "").strip()
    smart_gate_label = str(smart_validation_gate.get("label") or "").strip()
    smart_gate_next = str(smart_validation_gate.get("next_gate") or "").strip()
    smart_plan_summary = str(smart_execution_plan.get("summary") or "").strip()
    smart_plan_session_type = str(
        smart_execution_plan.get("session_type") or ""
    ).strip()
    smart_plan_success = str(smart_execution_plan.get("success_criteria") or "").strip()
    smart_plan_estimated_rounds = _safe_int(
        smart_execution_plan.get("estimated_rounds")
    )
    smart_confidence_level = str(
        smart_recommendation_confidence.get("level") or ""
    ).strip()
    smart_confidence_score = _safe_float(smart_recommendation_confidence.get("score"))
    smart_confidence_summary = str(
        smart_recommendation_confidence.get("summary") or ""
    ).strip()
    smart_confidence_uncertainty = str(
        smart_recommendation_confidence.get("uncertainty") or ""
    ).strip()
    smart_branch_label = str(smart_branch_advisory.get("label") or "").strip()
    smart_branch_compare_mode = str(
        smart_branch_advisory.get("compare_mode") or ""
    ).strip()
    smart_branch_display_line = str(
        smart_branch_advisory.get("display_line") or ""
    ).strip()
    smart_branch_action_line = str(
        smart_branch_advisory.get("action_line") or ""
    ).strip()
    smart_charge_alignment = str(
        smart_baseline_control.get("charge_alignment") or ""
    ).strip()
    smart_charge_target = str(
        smart_baseline_control.get("charge_target_label") or ""
    ).strip()
    smart_seating_alignment = str(
        smart_baseline_control.get("seating_alignment") or ""
    ).strip()
    smart_seating_target = str(
        smart_baseline_control.get("seating_target_label") or ""
    ).strip()
    smart_active_return_line = str(
        smart_baseline_control.get("active_return_line") or ""
    ).strip()
    smart_charge_return_line = str(
        (
            _safe_json_dict(smart_return_targets.get("charge")).get("return_line")
            if isinstance(smart_return_targets.get("charge"), dict)
            else ""
        )
        or smart_baseline_control.get("charge_return_line")
        or (
            f"return toward {smart_charge_target} before treating this as the same candidate."
            if smart_charge_alignment == "outside" and smart_charge_target
            else ""
        )
        or ""
    ).strip()
    smart_seating_return_line = str(
        (
            _safe_json_dict(smart_return_targets.get("seating")).get("return_line")
            if isinstance(smart_return_targets.get("seating"), dict)
            else ""
        )
        or smart_baseline_control.get("seating_return_line")
        or (
            f"return toward {smart_seating_target} before trusting the comparison."
            if smart_seating_alignment == "outside" and smart_seating_target
            else ""
        )
        or ""
    ).strip()
    smart_plan_keep_constant = (
        smart_execution_plan.get("keep_constant")
        if isinstance(smart_execution_plan.get("keep_constant"), list)
        else []
    )
    smart_plan_capture = (
        smart_execution_plan.get("capture")
        if isinstance(smart_execution_plan.get("capture"), list)
        else []
    )
    smart_baseline_items = (
        smart_baseline_diagnostics.get("items")
        if isinstance(smart_baseline_diagnostics.get("items"), list)
        else []
    )
    smart_baseline_impacts = (
        smart_baseline_diagnostics.get("impacts")
        if isinstance(smart_baseline_diagnostics.get("impacts"), list)
        else []
    )
    smart_baseline_focus = (
        smart_baseline_diagnostics.get("focus_areas")
        if isinstance(smart_baseline_diagnostics.get("focus_areas"), list)
        else []
    )
    smart_baseline_action = str(
        smart_baseline_diagnostics.get("suggested_action") or ""
    ).strip()
    smart_evidence_items = (
        smart_evidence_diagnostics.get("items")
        if isinstance(smart_evidence_diagnostics.get("items"), list)
        else []
    )
    smart_evidence_impacts = (
        smart_evidence_diagnostics.get("impacts")
        if isinstance(smart_evidence_diagnostics.get("impacts"), list)
        else []
    )
    smart_evidence_focus = (
        smart_evidence_diagnostics.get("focus_areas")
        if isinstance(smart_evidence_diagnostics.get("focus_areas"), list)
        else []
    )
    smart_evidence_action = str(
        smart_evidence_diagnostics.get("suggested_action") or ""
    ).strip()
    smart_evidence_status = str(smart_evidence_diagnostics.get("status") or "").strip()
    smart_preferred_action = (
        smart_baseline_action
        or smart_evidence_action
        or (
            next(
                (
                    str(item).strip()
                    for item in smart_baseline_items
                    if str(item).strip()
                ),
                "",
            )
            if str(smart_baseline_diagnostics.get("status") or "").strip() == "aligned"
            else ""
        )
        or smart_branch_action_line
        or smart_active_return_line
        or smart_guidance_setup
        or smart_next_reason
        or None
    )

    items: list[str] = []
    impacts: list[str] = []
    focus_areas: list[str] = []
    level = "ok"
    suggested_action = str(session.get("next_action") or "").strip() or None
    if smart_next_action in {
        "return_to_charge_baseline",
        "return_to_seating_baseline",
        "stop_and_review",
    }:
        suggested_action = smart_preferred_action or suggested_action
    if (
        smart_evidence_status in {"needs_measurement", "thin_evidence"}
        and level != "critical"
    ):
        level = "warning"
    if smart_bullet_fit_level == "critical":
        level = "critical"
    elif smart_bullet_fit_level == "warning" and level != "critical":
        level = "warning"

    def add_focus_area(label: str) -> None:
        normalized = label.strip()
        if normalized and normalized not in focus_areas:
            focus_areas.append(normalized)

    # Lot-drift warning: compare current lot numbers against the persisted calibrated
    # lot snapshot. Raise a warning item for each lot that has changed.
    _lot_label_map = {
        "powder": "Powder",
        "bullet": "Bullet",
        "primer": "Primer",
        "case": "Case",
    }
    _lot_context_keys = {
        "powder": "powder_lot_number",
        "bullet": "bullet_lot_number",
        "primer": "primer_lot_number",
        "case": "case_lot_number",
    }
    for _lot_name, _ctx_key in _lot_context_keys.items():
        _persisted_snap = persisted_lot_drift.get(_lot_name)
        if not isinstance(_persisted_snap, dict):
            continue
        _calibrated_lot = str(_persisted_snap.get("lot_number") or "").strip()
        if not _calibrated_lot:
            continue
        _current_lot = str(runtime_context.get(_ctx_key) or "").strip()
        if _current_lot and _current_lot != _calibrated_lot:
            level = "warning" if level != "critical" else level
            _label = _lot_label_map.get(_lot_name, _lot_name.capitalize())
            items.append(
                f"{_label} lot changed from calibrated lot '{_calibrated_lot}' to '{_current_lot}'. "
                f"Advice and learned windows may no longer apply — verify before loading."
            )
            add_focus_area(f"{_lot_name} lot drift")

    current_charge = _safe_float(intake.get("charge_weight_gr"))
    baseline_charge = _safe_float(recommendation_baseline.get("charge_gr"))
    baseline_coal = _safe_float(recommendation_baseline.get("coal_mm"))
    baseline_cbto = _safe_float(recommendation_baseline.get("cbto_mm"))
    current_cbto = _safe_float(intake.get("cbto_mm"))
    charge_source = (
        str(recommendation_baseline.get("charge_source") or "").strip().lower()
    )
    seating_source = (
        str(recommendation_baseline.get("seating_source") or "").strip().lower()
    )
    recommended_charge_min = _safe_float(session.get("recommended_charge_min_gr"))
    recommended_charge_max = _safe_float(session.get("recommended_charge_max_gr"))
    if (
        current_charge is not None
        and baseline_charge is not None
        and not smart_baseline_diagnostics
    ):
        charge_delta = current_charge - baseline_charge
        learned_charge_label = "learned " if charge_source == "learned" else ""
        if abs(charge_delta) > 0.05:
            level = "warning"
            items.append(
                f"Charge {current_charge:.2f} gr is {abs(charge_delta):.2f} gr away from the frozen {learned_charge_label}recommendation baseline ({baseline_charge:.2f} gr)."
            )
            if charge_source == "learned":
                impacts.append(
                    "Charge comparisons now sit outside a learned session baseline, so node and pressure conclusions should be treated as custom until a new learned charge is confirmed."
                )
            else:
                impacts.append(
                    "Charge comparisons now sit outside the session baseline, so node and pressure conclusions should be treated as custom until revalidated."
                )
            add_focus_area("velocity node")
            add_focus_area("data trust")
            suggested_action = (
                "Use the frozen learned charge baseline or confirm a new charge node before promoting this setup again."
                if charge_source == "learned"
                else "Use the frozen recommendation baseline or confirm a new charge node before promoting this setup."
            )
        else:
            items.append(
                f"Charge {current_charge:.2f} gr is aligned with the frozen {learned_charge_label}recommendation baseline."
            )
    elif (
        current_charge is not None
        and recommended_charge_min is not None
        and recommended_charge_max is not None
    ):
        if current_charge < recommended_charge_min:
            level = "warning"
            items.append(
                f"Charge {current_charge:.2f} gr is {recommended_charge_min - current_charge:.2f} gr below the suggested window."
            )
            impacts.append(
                "Velocity may land below the expected node and measured validation can become less representative."
            )
            add_focus_area("velocity node")
            add_focus_area("data trust")
            suggested_action = "Increase charge back into the suggested window before using new chrono or grouping results as reference."
        elif current_charge > recommended_charge_max:
            level = "warning"
            items.append(
                f"Charge {current_charge:.2f} gr is {current_charge - recommended_charge_max:.2f} gr above the suggested window."
            )
            impacts.append(
                "Pressure margin can shrink quickly above the suggested charge band, especially with warmer conditions or tighter brass."
            )
            add_focus_area("pressure margin")
            add_focus_area("data trust")
            suggested_action = "Reduce charge into the suggested window and re-check pressure signs before continuing the test plan."
        else:
            items.append(
                f"Charge {current_charge:.2f} gr is inside the suggested window."
            )

    current_coal = _safe_float(intake.get("coal_mm"))
    recommended_coal_min = _safe_float(session.get("recommended_coal_min"))
    recommended_coal_max = _safe_float(session.get("recommended_coal_max"))
    if (
        current_cbto is not None
        and baseline_cbto is not None
        and not smart_baseline_diagnostics
    ):
        cbto_delta = current_cbto - baseline_cbto
        if abs(cbto_delta) > 0.03:
            if level != "critical":
                level = "warning"
            learned_label = "learned " if seating_source == "learned" else ""
            items.append(
                f"CBTO {current_cbto:.2f} mm is {abs(cbto_delta):.2f} mm away from the {learned_label}recommendation baseline ({baseline_cbto:.2f} mm)."
            )
            if seating_source == "learned":
                impacts.append(
                    "Seating now sits outside a learned baseline, so jump and group comparisons should be treated as custom until a new sweet spot is reconfirmed."
                )
            else:
                impacts.append(
                    "Seating now sits outside the frozen baseline, so jump and group comparisons should be treated as custom until they are reconfirmed."
                )
            add_focus_area("jump")
            add_focus_area("grouping")
            if not suggested_action or "charge" not in suggested_action.lower():
                suggested_action = (
                    "Return to the frozen learned seating baseline or confirm a new seating sweet spot before treating the result as learned behavior."
                    if seating_source == "learned"
                    else "Return to the frozen seating baseline or confirm a new seating sweet spot before treating the result as learned behavior."
                )
        else:
            aligned_label = (
                "learned seating baseline"
                if seating_source == "learned"
                else "seating baseline"
            )
            items.append(
                f"CBTO {current_cbto:.2f} mm is aligned with the frozen {aligned_label}."
            )
    elif (
        current_coal is not None
        and baseline_coal is not None
        and not smart_baseline_diagnostics
    ):
        coal_delta = current_coal - baseline_coal
        if abs(coal_delta) > 0.03:
            if level != "critical":
                level = "warning"
            items.append(
                f"COAL {current_coal:.2f} mm is {abs(coal_delta):.2f} mm away from the frozen recommendation baseline ({baseline_coal:.2f} mm)."
            )
            impacts.append(
                "Seating now sits outside the frozen baseline, so case-volume and jump comparisons should be treated as custom until they are reconfirmed."
            )
            add_focus_area("case volume")
            add_focus_area("jump")
            if not suggested_action or "charge" not in suggested_action.lower():
                suggested_action = "Return to the frozen seating baseline or verify this custom seating before comparing against prior evidence."
        else:
            items.append(
                f"COAL {current_coal:.2f} mm is aligned with the frozen seating baseline."
            )
    elif (
        current_coal is not None
        and recommended_coal_min is not None
        and recommended_coal_max is not None
    ):
        if current_coal < recommended_coal_min:
            if level != "critical":
                level = "warning"
            items.append(
                f"COAL {current_coal:.2f} mm is {recommended_coal_min - current_coal:.2f} mm shorter than the current recommended band."
            )
            impacts.append(
                "Shorter seating can change case volume, pressure behavior, and jump enough that current comparisons become harder to trust."
            )
            add_focus_area("case volume")
            add_focus_area("jump")
            add_focus_area("data trust")
            if not suggested_action or "charge" not in suggested_action.lower():
                suggested_action = "Move seating back into the recommended COAL band before comparing groups or ES/SD against previous tests."
        elif current_coal > recommended_coal_max:
            if level != "critical":
                level = "warning"
            items.append(
                f"COAL {current_coal:.2f} mm is {current_coal - recommended_coal_max:.2f} mm longer than the current recommended band."
            )
            impacts.append(
                "Longer seating can move the bullet closer to the lands and change both pressure onset and grouping behavior."
            )
            add_focus_area("pressure onset")
            add_focus_area("jump")
            if not suggested_action or "charge" not in suggested_action.lower():
                suggested_action = "Seat back into the recommended COAL band or verify actual jump before treating this as a valid comparison point."
        else:
            items.append(
                f"COAL {current_coal:.2f} mm is inside the current recommended band."
            )

    safety_status = str(session.get("safety_status") or "").strip().lower()
    if safety_status == "high_risk":
        level = "critical"
        items.append(
            "Safety state is high risk. Pressure and seating should be reviewed before further testing."
        )
        impacts.append(
            "Further testing in this state can invalidate learning and may push the setup into unsafe pressure territory."
        )
        add_focus_area("pressure margin")
        add_focus_area("brass response")
        suggested_action = "Stop and back the load down before continuing. Confirm pressure margin, seating, and brass condition first."
    elif safety_status == "caution":
        if level != "critical":
            level = "warning"
        items.append(
            "Safety state is caution. Keep charge steps conservative and verify with chronograph data."
        )
        impacts.append(
            "Current results should be interpreted conservatively until velocity, pressure behavior, and brass response are confirmed."
        )
        add_focus_area("pressure margin")
        add_focus_area("velocity validation")
        if not suggested_action:
            suggested_action = "Keep the next test conservative and verify with chronograph plus brass inspection before expanding the test range."

    confidence_label = str(session.get("confidence_label") or "").strip().lower()
    confidence_score = _safe_float(session.get("confidence_score"))
    if (
        confidence_label == "low"
        or (confidence_score is not None and confidence_score < 2.5)
    ) and not smart_evidence_diagnostics:
        if level != "critical":
            level = "warning"
        items.append(
            "Confidence is still low, so current guidance depends on thin or partially assumed data."
        )
        impacts.append(
            "Changes can look meaningful even when the underlying data basis is still too thin for strong conclusions."
        )
        add_focus_area("data trust")
        if not suggested_action:
            suggested_action = "Add measured data with chrono or grouping before locking in a node or ranking this combination highly."
    elif confidence_label:
        items.append(f"Confidence basis is currently marked as {confidence_label}.")

    load_density = _safe_float(latest_result.get("load_density_percent"))
    if load_density is not None and load_density > 103.0:
        if level != "critical":
            level = "warning"
        items.append(
            f"Load density is {load_density:.1f}%, which points to a compressed or near-compressed load."
        )
        impacts.append(
            "Compression can make small seating or lot changes more sensitive and can raise the need for smaller verification steps."
        )
        add_focus_area("fill ratio")
        add_focus_area("seating sensitivity")
        if not suggested_action:
            suggested_action = "Use smaller charge steps and re-check seating consistency before treating the load as stable."
    elif load_density is not None and load_density < 85.0:
        if level != "critical":
            level = "warning"
        items.append(
            f"Load density is {load_density:.1f}%, which can increase sensitivity and spread."
        )
        impacts.append(
            "Low fill can increase orientation sensitivity and make ES/SD less robust across conditions."
        )
        add_focus_area("fill ratio")
        add_focus_area("velocity consistency")
        if not suggested_action:
            suggested_action = "Verify ES/SD with a larger chronograph sample before accepting this load as stable."

    has_measured_velocity_flag = runtime_evidence_summary.get("has_measured_velocity")
    has_measured_group_flag = runtime_evidence_summary.get("has_measured_group")
    signal_hint = str(runtime_evidence_summary.get("signal_hint") or "").strip()
    batch_spread_reason = str(
        runtime_evidence_summary.get("batch_spread_reason") or ""
    ).strip()
    batch_spread_control_plan = (
        runtime_evidence_summary.get("batch_spread_control_plan")
        if isinstance(runtime_evidence_summary.get("batch_spread_control_plan"), dict)
        else {}
    )
    control_action = str(
        batch_spread_control_plan.get("primary_action")
        or batch_spread_control_plan.get("shot_plan")
        or ""
    ).strip()
    batch_spread_decision = (
        runtime_evidence_summary.get("batch_spread_decision")
        if isinstance(runtime_evidence_summary.get("batch_spread_decision"), dict)
        else {}
    )
    decision_state = str(batch_spread_decision.get("state") or "").strip()
    decision_label = str(batch_spread_decision.get("label") or "").strip()
    decision_rationale = str(batch_spread_decision.get("rationale") or "").strip()
    batch_spread_profile_guidance = (
        runtime_evidence_summary.get("batch_spread_profile_guidance")
        if isinstance(
            runtime_evidence_summary.get("batch_spread_profile_guidance"), dict
        )
        else {}
    )
    profile_title = str(batch_spread_profile_guidance.get("title") or "").strip()
    profile_emphasis = str(batch_spread_profile_guidance.get("emphasis") or "").strip()
    profile_note_added = False
    if profile_title or profile_emphasis:
        message = f"Use profile focus: {profile_title or 'validation focus'}."
        if profile_emphasis:
            message += f" {profile_emphasis}"
        items.append(message)
        profile_note_added = True
    batch_spread_evidence_quality = (
        runtime_evidence_summary.get("batch_spread_evidence_quality")
        if isinstance(
            runtime_evidence_summary.get("batch_spread_evidence_quality"), dict
        )
        else {}
    )
    spread_quality_level = str(batch_spread_evidence_quality.get("level") or "").strip()
    spread_quality_score = _safe_float(batch_spread_evidence_quality.get("score"))
    quality_note_added = False
    if spread_quality_level:
        score_text = (
            f" ({spread_quality_score:.1f}/100)"
            if spread_quality_score is not None
            else ""
        )
        items.append(f"Spread evidence quality is {spread_quality_level}{score_text}.")
        quality_note_added = True
        if spread_quality_level in {"very_thin", "thin"}:
            if level != "critical":
                level = "warning"
            add_focus_area("evidence quality")
    batch_spread_learning_explanation = (
        runtime_evidence_summary.get("batch_spread_learning_explanation")
        if isinstance(
            runtime_evidence_summary.get("batch_spread_learning_explanation"), dict
        )
        else {}
    )
    learning_title = str(batch_spread_learning_explanation.get("title") or "").strip()
    learning_takeaway = str(
        batch_spread_learning_explanation.get("user_takeaway") or ""
    ).strip()
    batch_spread_capture_checklist = (
        runtime_evidence_summary.get("batch_spread_capture_checklist")
        if isinstance(
            runtime_evidence_summary.get("batch_spread_capture_checklist"), dict
        )
        else {}
    )
    batch_spread_validation_status = (
        runtime_evidence_summary.get("batch_spread_validation_status")
        if isinstance(
            runtime_evidence_summary.get("batch_spread_validation_status"), dict
        )
        else {}
    )
    batch_comparison_basis = (
        runtime_evidence_summary.get("batch_comparison_basis")
        if isinstance(runtime_evidence_summary.get("batch_comparison_basis"), dict)
        else {}
    )
    batch_comparison_advisory = (
        runtime_evidence_summary.get("batch_comparison_advisory")
        if isinstance(runtime_evidence_summary.get("batch_comparison_advisory"), dict)
        else {}
    )
    batch_comparison_protocol = (
        runtime_evidence_summary.get("batch_comparison_protocol")
        if isinstance(runtime_evidence_summary.get("batch_comparison_protocol"), dict)
        else {}
    )
    batch_comparison_explanation = (
        runtime_evidence_summary.get("batch_comparison_explanation")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_explanation"), dict
        )
        else {}
    )
    batch_comparison_verdict = (
        runtime_evidence_summary.get("batch_comparison_verdict")
        if isinstance(runtime_evidence_summary.get("batch_comparison_verdict"), dict)
        else {}
    )
    batch_comparison_acceptance = (
        runtime_evidence_summary.get("batch_comparison_acceptance")
        if isinstance(runtime_evidence_summary.get("batch_comparison_acceptance"), dict)
        else {}
    )
    batch_comparison_acceptance_progress = (
        runtime_evidence_summary.get("batch_comparison_acceptance_progress")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_acceptance_progress"), dict
        )
        else {}
    )
    batch_comparison_next_test = (
        runtime_evidence_summary.get("batch_comparison_next_test")
        if isinstance(runtime_evidence_summary.get("batch_comparison_next_test"), dict)
        else {}
    )
    batch_comparison_status_board = (
        runtime_evidence_summary.get("batch_comparison_status_board")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_status_board"), dict
        )
        else {}
    )
    batch_comparison_profile_priority = (
        runtime_evidence_summary.get("batch_comparison_profile_priority")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_profile_priority"), dict
        )
        else {}
    )
    batch_comparison_mission_brief = (
        runtime_evidence_summary.get("batch_comparison_mission_brief")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_mission_brief"), dict
        )
        else {}
    )
    batch_comparison_portfolio = (
        runtime_evidence_summary.get("batch_comparison_portfolio")
        if isinstance(runtime_evidence_summary.get("batch_comparison_portfolio"), dict)
        else {}
    )
    batch_comparison_session_strategy = (
        runtime_evidence_summary.get("batch_comparison_session_strategy")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_session_strategy"), dict
        )
        else {}
    )
    batch_comparison_campaign_view = (
        runtime_evidence_summary.get("batch_comparison_campaign_view")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_campaign_view"), dict
        )
        else {}
    )
    batch_comparison_action_plan = (
        runtime_evidence_summary.get("batch_comparison_action_plan")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_action_plan"), dict
        )
        else {}
    )
    batch_comparison_campaign_board = (
        runtime_evidence_summary.get("batch_comparison_campaign_board")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_campaign_board"), dict
        )
        else {}
    )
    batch_comparison_session_queue = (
        runtime_evidence_summary.get("batch_comparison_session_queue")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_session_queue"), dict
        )
        else {}
    )
    batch_comparison_session_manifest = (
        runtime_evidence_summary.get("batch_comparison_session_manifest")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_session_manifest"), dict
        )
        else {}
    )
    batch_comparison_next_session_brief = (
        runtime_evidence_summary.get("batch_comparison_next_session_brief")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_next_session_brief"), dict
        )
        else {}
    )
    batch_comparison_today_plan = (
        runtime_evidence_summary.get("batch_comparison_today_plan")
        if isinstance(runtime_evidence_summary.get("batch_comparison_today_plan"), dict)
        else {}
    )
    batch_comparison_workboard = (
        runtime_evidence_summary.get("batch_comparison_workboard")
        if isinstance(runtime_evidence_summary.get("batch_comparison_workboard"), dict)
        else {}
    )
    batch_comparison_checklist = (
        runtime_evidence_summary.get("batch_comparison_checklist")
        if isinstance(runtime_evidence_summary.get("batch_comparison_checklist"), dict)
        else {}
    )
    batch_comparison_scorecard = (
        runtime_evidence_summary.get("batch_comparison_scorecard")
        if isinstance(runtime_evidence_summary.get("batch_comparison_scorecard"), dict)
        else {}
    )
    batch_comparison_confidence = (
        runtime_evidence_summary.get("batch_comparison_confidence")
        if isinstance(runtime_evidence_summary.get("batch_comparison_confidence"), dict)
        else {}
    )
    batch_comparison_learning_note = (
        runtime_evidence_summary.get("batch_comparison_learning_note")
        if isinstance(
            runtime_evidence_summary.get("batch_comparison_learning_note"), dict
        )
        else {}
    )
    checklist_title = str(batch_spread_capture_checklist.get("title") or "").strip()
    checklist_items = (
        batch_spread_capture_checklist.get("items")
        if isinstance(batch_spread_capture_checklist.get("items"), list)
        else []
    )
    validation_state = str(batch_spread_validation_status.get("status") or "").strip()
    validation_label = str(batch_spread_validation_status.get("label") or "").strip()
    validation_summary = str(
        batch_spread_validation_status.get("summary") or ""
    ).strip()
    validation_next_gate = str(
        batch_spread_validation_status.get("next_gate") or ""
    ).strip()
    validation_usage_goal = str(
        batch_spread_validation_status.get("usage_goal") or ""
    ).strip()
    validation_ready_now = batch_spread_validation_status.get("ready_now") is True
    validation_score = _safe_float(
        batch_spread_validation_status.get("readiness_score")
    )
    comparison_state = str(batch_comparison_basis.get("ranking_state") or "").strip()
    comparison_summary = str(batch_comparison_basis.get("summary") or "").strip()
    comparison_rank = _safe_int(batch_comparison_basis.get("current_rank"))
    comparison_count = _safe_int(batch_comparison_basis.get("count"))
    comparison_leader = str(
        batch_comparison_basis.get("leader_batch_name") or ""
    ).strip()
    comparison_gap = _safe_float(batch_comparison_basis.get("leader_gap_score"))
    comparison_advisory_title = str(
        batch_comparison_advisory.get("title") or ""
    ).strip()
    comparison_advisory_message = str(
        batch_comparison_advisory.get("message") or ""
    ).strip()
    comparison_advisory_action = str(
        batch_comparison_advisory.get("recommended_action") or ""
    ).strip()
    comparison_promotion_ready = (
        batch_comparison_advisory.get("promotion_ready") is True
    )
    comparison_protocol_title = str(
        batch_comparison_protocol.get("title") or ""
    ).strip()
    comparison_protocol_action = str(
        batch_comparison_protocol.get("primary_action") or ""
    ).strip()
    comparison_protocol_plan = str(
        batch_comparison_protocol.get("shot_plan") or ""
    ).strip()
    comparison_bottleneck = str(
        batch_comparison_explanation.get("limiting_factor") or ""
    ).strip()
    comparison_reason = str(batch_comparison_explanation.get("reason") or "").strip()
    comparison_next_measurement = str(
        batch_comparison_explanation.get("next_measurement") or ""
    ).strip()
    comparison_verdict_label = str(batch_comparison_verdict.get("label") or "").strip()
    comparison_verdict_summary = str(
        batch_comparison_verdict.get("summary") or ""
    ).strip()
    comparison_acceptance_label = str(
        batch_comparison_acceptance.get("label") or ""
    ).strip()
    comparison_acceptance_summary = str(
        batch_comparison_acceptance.get("summary") or ""
    ).strip()
    comparison_acceptance_gate = str(
        batch_comparison_acceptance.get("next_gate") or ""
    ).strip()
    comparison_acceptance_ready = (
        batch_comparison_acceptance.get("ready_for_acceptance") is True
    )
    comparison_acceptance_gaps = (
        batch_comparison_acceptance.get("remaining_gaps")
        if isinstance(batch_comparison_acceptance.get("remaining_gaps"), list)
        else []
    )
    comparison_acceptance_first_gap = next(
        (str(item).strip() for item in comparison_acceptance_gaps if str(item).strip()),
        "",
    )
    comparison_acceptance_progress_level = str(
        batch_comparison_acceptance_progress.get("level") or ""
    ).strip()
    comparison_acceptance_progress_score = _safe_float(
        batch_comparison_acceptance_progress.get("score")
    )
    comparison_acceptance_progress_summary = str(
        batch_comparison_acceptance_progress.get("summary") or ""
    ).strip()
    comparison_acceptance_progress_target = str(
        batch_comparison_acceptance_progress.get("next_target") or ""
    ).strip()
    comparison_acceptance_progress_passed = _safe_int(
        batch_comparison_acceptance_progress.get("passed_count")
    )
    comparison_acceptance_progress_total = _safe_int(
        batch_comparison_acceptance_progress.get("total_count")
    )
    comparison_next_test_title = str(
        batch_comparison_next_test.get("title") or ""
    ).strip()
    comparison_next_test_summary = str(
        batch_comparison_next_test.get("summary") or ""
    ).strip()
    comparison_next_test_action = str(
        batch_comparison_next_test.get("primary_action") or ""
    ).strip()
    comparison_next_test_first_check = str(
        batch_comparison_next_test.get("check_first") or ""
    ).strip()
    comparison_board_headline = str(
        batch_comparison_status_board.get("headline") or ""
    ).strip()
    comparison_board_summary = str(
        batch_comparison_status_board.get("summary") or ""
    ).strip()
    comparison_board_band = str(
        batch_comparison_status_board.get("readiness_band") or ""
    ).strip()
    comparison_profile_title = str(
        batch_comparison_profile_priority.get("title") or ""
    ).strip()
    comparison_profile_emphasis = str(
        batch_comparison_profile_priority.get("emphasis") or ""
    ).strip()
    comparison_profile_guardrail = str(
        batch_comparison_profile_priority.get("guardrail") or ""
    ).strip()
    comparison_mission = str(
        batch_comparison_mission_brief.get("mission") or ""
    ).strip()
    comparison_mission_action = str(
        batch_comparison_mission_brief.get("primary_action") or ""
    ).strip()
    comparison_mission_success = str(
        batch_comparison_mission_brief.get("success_marker") or ""
    ).strip()
    comparison_portfolio_title = str(
        batch_comparison_portfolio.get("title") or ""
    ).strip()
    comparison_portfolio_focus = str(
        batch_comparison_portfolio.get("focus") or ""
    ).strip()
    comparison_session_strategy_title = str(
        batch_comparison_session_strategy.get("title") or ""
    ).strip()
    comparison_session_strategy_mode = str(
        batch_comparison_session_strategy.get("mode") or ""
    ).strip()
    comparison_session_strategy_objective = str(
        batch_comparison_session_strategy.get("objective") or ""
    ).strip()
    comparison_campaign_title = str(
        batch_comparison_campaign_view.get("title") or ""
    ).strip()
    comparison_campaign_summary = str(
        batch_comparison_campaign_view.get("summary") or ""
    ).strip()
    comparison_action_plan_title = str(
        batch_comparison_action_plan.get("title") or ""
    ).strip()
    comparison_action_plan_summary = str(
        batch_comparison_action_plan.get("summary") or ""
    ).strip()
    comparison_action_plan_next = str(
        batch_comparison_action_plan.get("primary_action") or ""
    ).strip()
    comparison_campaign_board_title = str(
        batch_comparison_campaign_board.get("title") or ""
    ).strip()
    comparison_campaign_board_summary = str(
        batch_comparison_campaign_board.get("summary") or ""
    ).strip()
    comparison_campaign_board_preview = (
        batch_comparison_campaign_board.get("preview")
        if isinstance(batch_comparison_campaign_board.get("preview"), list)
        else []
    )
    comparison_session_queue_title = str(
        batch_comparison_session_queue.get("title") or ""
    ).strip()
    comparison_session_queue_first = str(
        batch_comparison_session_queue.get("first_batch_name") or ""
    ).strip()
    comparison_session_queue_preview = (
        batch_comparison_session_queue.get("preview")
        if isinstance(batch_comparison_session_queue.get("preview"), list)
        else []
    )
    comparison_session_manifest_title = str(
        batch_comparison_session_manifest.get("title") or ""
    ).strip()
    comparison_session_manifest_summary = str(
        batch_comparison_session_manifest.get("summary") or ""
    ).strip()
    comparison_session_manifest_bucket = str(
        batch_comparison_session_manifest.get("primary_bucket") or ""
    ).strip()
    comparison_session_manifest_first = str(
        batch_comparison_session_manifest.get("first_batch_name") or ""
    ).strip()
    comparison_session_manifest_preview = (
        batch_comparison_session_manifest.get("queue_preview")
        if isinstance(batch_comparison_session_manifest.get("queue_preview"), list)
        else []
    )
    comparison_session_manifest_lanes = (
        batch_comparison_session_manifest.get("lane_summaries")
        if isinstance(batch_comparison_session_manifest.get("lane_summaries"), list)
        else []
    )
    comparison_next_session_brief_title = str(
        batch_comparison_next_session_brief.get("title") or ""
    ).strip()
    comparison_next_session_brief_summary = str(
        batch_comparison_next_session_brief.get("summary") or ""
    ).strip()
    comparison_next_session_brief_action = str(
        batch_comparison_next_session_brief.get("primary_action") or ""
    ).strip()
    comparison_next_session_brief_hold = str(
        batch_comparison_next_session_brief.get("hold_back") or ""
    ).strip()
    comparison_today_plan_title = str(
        batch_comparison_today_plan.get("title") or ""
    ).strip()
    comparison_today_plan_summary = str(
        batch_comparison_today_plan.get("summary") or ""
    ).strip()
    comparison_today_plan_action = str(
        batch_comparison_today_plan.get("primary_action") or ""
    ).strip()
    comparison_workboard_title = str(
        batch_comparison_workboard.get("title") or ""
    ).strip()
    comparison_workboard_summary = str(
        batch_comparison_workboard.get("summary") or ""
    ).strip()
    comparison_workboard_status = str(
        batch_comparison_workboard.get("status_label") or ""
    ).strip()
    comparison_workboard_action = str(
        batch_comparison_workboard.get("primary_action") or ""
    ).strip()
    comparison_workboard_hold = str(
        batch_comparison_workboard.get("hold_back") or ""
    ).strip()
    comparison_workboard_first = str(
        batch_comparison_workboard.get("first_batch_name") or ""
    ).strip()
    comparison_workboard_bucket = str(
        batch_comparison_workboard.get("primary_bucket") or ""
    ).strip()
    comparison_workboard_counts = (
        batch_comparison_workboard.get("counts")
        if isinstance(batch_comparison_workboard.get("counts"), dict)
        else {}
    )
    comparison_workboard_counts_text = " | ".join(
        f"{bucket} {int(value)}"
        for bucket, value in (
            ("shoot_now", comparison_workboard_counts.get("shoot_now") or 0),
            ("confirm", comparison_workboard_counts.get("confirm") or 0),
            ("hold", comparison_workboard_counts.get("hold") or 0),
            ("pause", comparison_workboard_counts.get("pause") or 0),
            ("reject_watch", comparison_workboard_counts.get("reject_watch") or 0),
        )
        if int(value) > 0
    )
    comparison_workboard_lanes = (
        batch_comparison_workboard.get("lane_summaries")
        if isinstance(batch_comparison_workboard.get("lane_summaries"), list)
        else []
    )
    comparison_workboard_lanes_text = " | ".join(
        str(item.get("summary") or "").strip()
        for item in comparison_workboard_lanes
        if isinstance(item, dict) and str(item.get("summary") or "").strip()
    )
    comparison_checklist_title = str(
        batch_comparison_checklist.get("title") or ""
    ).strip()
    comparison_checklist_first = str(
        batch_comparison_checklist.get("highest_priority") or ""
    ).strip()
    comparison_swing_factor = str(
        batch_comparison_scorecard.get("swing_factor") or ""
    ).strip()
    comparison_scorecard_summary = str(
        batch_comparison_scorecard.get("summary") or ""
    ).strip()
    comparison_confidence_level = str(
        batch_comparison_confidence.get("level") or ""
    ).strip()
    comparison_confidence_score = _safe_float(batch_comparison_confidence.get("score"))
    comparison_confidence_summary = str(
        batch_comparison_confidence.get("summary") or ""
    ).strip()
    comparison_learning_summary = str(
        batch_comparison_learning_note.get("plain_summary") or ""
    ).strip()
    comparison_learning_takeaway = str(
        batch_comparison_learning_note.get("takeaway") or ""
    ).strip()
    learning_note_added = False
    if learning_title or learning_takeaway:
        message = f"Learning note: {learning_title or 'spread lesson'}."
        if learning_takeaway:
            message += f" {learning_takeaway}"
        items.append(message)
        learning_note_added = True
    if checklist_title or checklist_items:
        first_labels = [
            str(item.get("label") or "").strip()
            for item in checklist_items[:2]
            if isinstance(item, dict) and str(item.get("label") or "").strip()
        ]
        message = f"Capture checklist: {checklist_title or 'next capture'}."
        if first_labels:
            message += " Start with " + ", ".join(first_labels) + "."
        items.append(message)
    if validation_label or validation_summary:
        readiness_text = (
            f" ({validation_score:.1f}/100)" if validation_score is not None else ""
        )
        message = f"Validation status: {validation_label or validation_state}{readiness_text}."
        if validation_summary:
            message += f" {validation_summary}"
        if validation_next_gate:
            message += f" Next gate: {validation_next_gate}"
        items.append(message)
        add_focus_area("validation gate")
        if validation_usage_goal == "hunting":
            add_focus_area("field validation")
        elif validation_usage_goal == "competition":
            add_focus_area("competition ranking")
        elif validation_usage_goal == "learning":
            add_focus_area("learning cycle")
        if not validation_ready_now and level != "critical":
            level = "warning"
        if not suggested_action and validation_next_gate:
            suggested_action = validation_next_gate
    if comparison_state or comparison_summary or comparison_advisory_title:
        message = "Batch comparison:"
        if comparison_state:
            message += f" {comparison_state}."
        if comparison_rank is not None and comparison_count is not None:
            message += f" Rank {comparison_rank}/{comparison_count}."
        if comparison_summary:
            message += f" {comparison_summary}"
        items.append(message)
        add_focus_area("batch comparison")
        if comparison_state in {
            "trailing_candidate",
            "leading_but_provisional",
            "blocked",
        }:
            add_focus_area("promotion gate")
        if comparison_leader and comparison_state == "trailing_candidate":
            add_focus_area("comparison leader")
        if comparison_advisory_title or comparison_advisory_message:
            advisory_message = f"Comparison advisory: {comparison_advisory_title or 'comparison gate'}."
            if comparison_advisory_message:
                advisory_message += f" {comparison_advisory_message}"
            if comparison_advisory_action:
                advisory_message += f" Next gate: {comparison_advisory_action}"
            items.append(advisory_message)
        if comparison_protocol_title or comparison_protocol_action:
            protocol_message = f"Comparison protocol: {comparison_protocol_title or 'head-to-head protocol'}."
            if comparison_protocol_action:
                protocol_message += f" {comparison_protocol_action}"
            if comparison_protocol_plan:
                protocol_message += f" Shot plan: {comparison_protocol_plan}"
            items.append(protocol_message)
            add_focus_area("head-to-head test")
        if comparison_bottleneck or comparison_reason:
            explanation_message = f"Comparison explanation: {comparison_bottleneck or 'current bottleneck'}."
            if comparison_reason:
                explanation_message += f" {comparison_reason}"
            if comparison_next_measurement:
                explanation_message += (
                    f" Next measurement: {comparison_next_measurement}"
                )
            items.append(explanation_message)
            add_focus_area("comparison bottleneck")
        if comparison_verdict_label or comparison_verdict_summary:
            verdict_message = (
                f"Comparison verdict: {comparison_verdict_label or 'hold'}."
            )
            if comparison_verdict_summary:
                verdict_message += f" {comparison_verdict_summary}"
            items.append(verdict_message)
            add_focus_area("comparison verdict")
        if comparison_acceptance_label or comparison_acceptance_summary:
            acceptance_message = f"Comparison acceptance: {comparison_acceptance_label or 'not accepted'}."
            if comparison_acceptance_summary:
                acceptance_message += f" {comparison_acceptance_summary}"
            if comparison_acceptance_gate:
                acceptance_message += f" Next gate: {comparison_acceptance_gate}"
            items.append(acceptance_message)
            add_focus_area("acceptance gate")
        if comparison_acceptance_first_gap:
            items.append(
                f"Comparison acceptance gap: {comparison_acceptance_first_gap}"
            )
        if comparison_acceptance_progress_level:
            progress_message = (
                f"Acceptance progress: {comparison_acceptance_progress_level}"
            )
            if comparison_acceptance_progress_score is not None:
                progress_message += f" ({comparison_acceptance_progress_score:.1f}/100)"
            if (
                comparison_acceptance_progress_passed is not None
                and comparison_acceptance_progress_total is not None
            ):
                progress_message += f", conditions {comparison_acceptance_progress_passed}/{comparison_acceptance_progress_total}"
            progress_message += "."
            if comparison_acceptance_progress_summary:
                progress_message += f" {comparison_acceptance_progress_summary}"
            if comparison_acceptance_progress_target:
                progress_message += (
                    f" Next target: {comparison_acceptance_progress_target}"
                )
            items.append(progress_message)
            add_focus_area("acceptance progress")
        if comparison_next_test_title or comparison_next_test_summary:
            next_test_message = (
                f"Comparison next test: {comparison_next_test_title or 'next test'}."
            )
            if comparison_next_test_summary:
                next_test_message += f" {comparison_next_test_summary}"
            if comparison_next_test_action:
                next_test_message += f" Action: {comparison_next_test_action}"
            if comparison_next_test_first_check:
                next_test_message += f" First check: {comparison_next_test_first_check}"
            items.append(next_test_message)
            add_focus_area("next comparison test")
        if comparison_board_headline or comparison_board_summary:
            board_message = (
                f"Comparison board: {comparison_board_headline or 'status'}."
            )
            if comparison_board_summary:
                board_message += f" {comparison_board_summary}"
            if comparison_board_band:
                board_message += f" Readiness band: {comparison_board_band}"
            items.append(board_message)
            add_focus_area("comparison board")
        if comparison_profile_title or comparison_profile_emphasis:
            profile_message = f"Comparison profile: {comparison_profile_title or 'comparison priority'}."
            if comparison_profile_emphasis:
                profile_message += f" {comparison_profile_emphasis}"
            if comparison_profile_guardrail:
                profile_message += f" Guardrail: {comparison_profile_guardrail}"
            items.append(profile_message)
            add_focus_area("comparison profile")
        if comparison_mission or comparison_mission_action:
            mission_message = f"Mission brief: {comparison_mission or 'Run the next comparison honestly.'}"
            if comparison_mission_action:
                mission_message += f" Action: {comparison_mission_action}"
            if comparison_mission_success:
                mission_message += f" Success marker: {comparison_mission_success}"
            items.append(mission_message)
            add_focus_area("mission brief")
        if comparison_portfolio_title or comparison_portfolio_focus:
            portfolio_message = (
                f"Comparison portfolio: {comparison_portfolio_title or 'portfolio'}."
            )
            if comparison_portfolio_focus:
                portfolio_message += f" {comparison_portfolio_focus}"
            items.append(portfolio_message)
            add_focus_area("comparison portfolio")
        if comparison_session_strategy_title or comparison_session_strategy_objective:
            strategy_message = f"Session strategy: {comparison_session_strategy_title or 'session strategy'}."
            if comparison_session_strategy_mode:
                strategy_message += f" Mode: {comparison_session_strategy_mode}."
            if comparison_session_strategy_objective:
                strategy_message += f" {comparison_session_strategy_objective}"
            items.append(strategy_message)
            add_focus_area("session strategy")
        if comparison_campaign_title or comparison_campaign_summary:
            campaign_message = (
                f"Campaign view: {comparison_campaign_title or 'campaign view'}."
            )
            if comparison_campaign_summary:
                campaign_message += f" {comparison_campaign_summary}"
            items.append(campaign_message)
            add_focus_area("campaign view")
        if comparison_action_plan_title or comparison_action_plan_summary:
            action_plan_message = (
                f"Action plan: {comparison_action_plan_title or 'action plan'}."
            )
            if comparison_action_plan_summary:
                action_plan_message += f" {comparison_action_plan_summary}"
            if comparison_action_plan_next:
                action_plan_message += f" Next: {comparison_action_plan_next}"
            items.append(action_plan_message)
            add_focus_area("action plan")
        if comparison_campaign_board_title or comparison_campaign_board_summary:
            campaign_board_message = f"Campaign board: {comparison_campaign_board_title or 'campaign board'}."
            if comparison_campaign_board_summary:
                campaign_board_message += f" {comparison_campaign_board_summary}"
            if comparison_campaign_board_preview:
                campaign_board_message += " Preview: " + " | ".join(
                    str(item).strip()
                    for item in comparison_campaign_board_preview[:3]
                    if str(item).strip()
                )
            items.append(campaign_board_message)
            add_focus_area("campaign board")
        if comparison_session_queue_title or comparison_session_queue_first:
            queue_message = (
                f"Session queue: {comparison_session_queue_title or 'session queue'}."
            )
            if comparison_session_queue_first:
                queue_message += f" First batch: {comparison_session_queue_first}"
            if comparison_session_queue_preview:
                queue_message += " Queue: " + " | ".join(
                    str(item).strip()
                    for item in comparison_session_queue_preview[:3]
                    if str(item).strip()
                )
            items.append(queue_message)
            add_focus_area("session queue")
        if comparison_session_manifest_title or comparison_session_manifest_summary:
            manifest_message = f"Session manifest: {comparison_session_manifest_title or 'session manifest'}."
            if comparison_session_manifest_summary:
                manifest_message += f" {comparison_session_manifest_summary}"
            if comparison_session_manifest_bucket:
                manifest_message += (
                    f" Primary bucket: {comparison_session_manifest_bucket}"
                )
            if comparison_session_manifest_first:
                manifest_message += f" First batch: {comparison_session_manifest_first}"
            if comparison_session_manifest_preview:
                manifest_message += " Queue: " + " | ".join(
                    str(item).strip()
                    for item in comparison_session_manifest_preview[:3]
                    if str(item).strip()
                )
            if comparison_session_manifest_lanes:
                manifest_message += " Lanes: " + " | ".join(
                    str(item.get("summary") or "").strip()
                    for item in comparison_session_manifest_lanes[:4]
                    if isinstance(item, dict) and str(item.get("summary") or "").strip()
                )
            items.append(manifest_message)
            add_focus_area("session manifest")
            if comparison_session_manifest_lanes:
                add_focus_area("session lanes")
        if comparison_next_session_brief_title or comparison_next_session_brief_summary:
            brief_message = f"Next session brief: {comparison_next_session_brief_title or 'session brief'}."
            if comparison_next_session_brief_summary:
                brief_message += f" {comparison_next_session_brief_summary}"
            if comparison_next_session_brief_action:
                brief_message += f" Action: {comparison_next_session_brief_action}"
            if comparison_next_session_brief_hold:
                brief_message += f" Hold back: {comparison_next_session_brief_hold}"
            items.append(brief_message)
            add_focus_area("next session brief")
        if comparison_today_plan_title or comparison_today_plan_summary:
            today_message = (
                f"Today plan: {comparison_today_plan_title or 'today plan'}."
            )
            if comparison_today_plan_summary:
                today_message += f" {comparison_today_plan_summary}"
            if comparison_today_plan_action:
                today_message += f" Action: {comparison_today_plan_action}"
            items.append(today_message)
            add_focus_area("today plan")
        if comparison_workboard_title or comparison_workboard_summary:
            workboard_message = (
                f"Workboard: {comparison_workboard_title or 'workboard'}."
            )
            if comparison_workboard_summary:
                workboard_message += f" {comparison_workboard_summary}"
            if comparison_workboard_status:
                workboard_message += f" Status: {comparison_workboard_status}"
            if comparison_workboard_bucket:
                workboard_message += f" Primary lane: {comparison_workboard_bucket}"
            if comparison_workboard_first:
                workboard_message += f" Run first: {comparison_workboard_first}"
            if comparison_workboard_counts_text:
                workboard_message += f" Counts: {comparison_workboard_counts_text}"
            if comparison_workboard_lanes_text:
                workboard_message += f" Lanes: {comparison_workboard_lanes_text}"
            if comparison_workboard_action:
                workboard_message += f" Action: {comparison_workboard_action}"
            if comparison_workboard_hold:
                workboard_message += f" Hold back: {comparison_workboard_hold}"
            items.append(workboard_message)
            add_focus_area("workboard")
        if comparison_checklist_title or comparison_checklist_first:
            checklist_message = (
                f"Comparison checklist: {comparison_checklist_title or 'next compare'}."
            )
            if comparison_checklist_first:
                checklist_message += f" First check: {comparison_checklist_first}"
            items.append(checklist_message)
            add_focus_area("comparison checklist")
        if comparison_swing_factor or comparison_scorecard_summary:
            scorecard_message = (
                f"Comparison scorecard: {comparison_swing_factor or 'main delta'}."
            )
            if comparison_scorecard_summary:
                scorecard_message += f" {comparison_scorecard_summary}"
            items.append(scorecard_message)
            add_focus_area("comparison scorecard")
        if comparison_confidence_level:
            confidence_message = f"Comparison confidence: {comparison_confidence_level}"
            if comparison_confidence_score is not None:
                confidence_message += f" ({comparison_confidence_score:.1f}/100)"
            confidence_message += "."
            if comparison_confidence_summary:
                confidence_message += f" {comparison_confidence_summary}"
            items.append(confidence_message)
            add_focus_area("comparison confidence")
        if comparison_learning_summary or comparison_learning_takeaway:
            learning_message = f"Comparison learning: {comparison_learning_summary or 'comparison lesson'}."
            if comparison_learning_takeaway:
                learning_message += f" {comparison_learning_takeaway}"
            items.append(learning_message)
            add_focus_area("comparison learning")
        if (
            comparison_gap is not None
            and comparison_leader
            and comparison_state == "trailing_candidate"
        ):
            impacts.append(
                f"The current batch trails {comparison_leader} by about {comparison_gap:.1f} comparison-score points after evidence and readiness are weighted in."
            )
        if (
            (
                not comparison_promotion_ready
                and comparison_state
                in {"trailing_candidate", "leading_but_provisional", "blocked"}
            )
            or (comparison_acceptance_label and not comparison_acceptance_ready)
        ) and level != "critical":
            level = "warning"
        if comparison_workboard_action:
            suggested_action = comparison_workboard_action
        elif comparison_today_plan_action:
            suggested_action = comparison_today_plan_action
        elif comparison_protocol_action:
            suggested_action = comparison_protocol_action
        elif comparison_next_test_action:
            suggested_action = comparison_next_test_action
        elif comparison_mission_action:
            suggested_action = comparison_mission_action
        elif comparison_acceptance_gate:
            suggested_action = comparison_acceptance_gate
        elif comparison_acceptance_progress_target:
            suggested_action = comparison_acceptance_progress_target
        elif comparison_advisory_action:
            suggested_action = comparison_advisory_action
    if signal_hint == "possible_shooter_or_setup_signal":
        if level != "critical":
            level = "warning"
        message = "Spread signal points to possible shooter, rest, optic, setup, or series effect rather than clear ammunition failure."
        if batch_spread_reason:
            message += f" {batch_spread_reason}"
        items.append(message)
        impacts.append(
            "A good load can be rejected too early if a single open group is treated as pure ammo behavior."
        )
        add_focus_area("controlled group")
        add_focus_area("shooter/setup separation")
        if not suggested_action:
            suggested_action = (
                control_action
                or "Repeat one controlled group with the same load and setup before rejecting the recipe."
            )
    elif signal_hint == "ammo_or_process_signal":
        if level != "critical":
            level = "warning"
        message = "Spread signal points toward ammunition, loading process, or component variation."
        if batch_spread_reason:
            message += f" {batch_spread_reason}"
        items.append(message)
        impacts.append(
            "Group and velocity evidence should be confirmed with a controlled chrono series before changing several variables."
        )
        add_focus_area("ammo process")
        add_focus_area("velocity consistency")
        if not suggested_action:
            suggested_action = (
                control_action
                or "Run a short same-setup control series and inspect loading process variables before fine-tuning seating or charge."
            )
    elif signal_hint == "setup_drift_watch":
        if level != "critical":
            level = "warning"
        message = "Spread signal points to possible setup or condition drift."
        if batch_spread_reason:
            message += f" {batch_spread_reason}"
        items.append(message)
        impacts.append(
            "Setup drift can make a load look worse even when the recipe itself has not changed."
        )
        add_focus_area("setup drift")
        add_focus_area("grouping")
        if not suggested_action:
            suggested_action = (
                control_action
                or "Check optic, action torque, barrel condition, muzzle device, and environment before blaming the load."
            )
    elif signal_hint == "environment_or_condition_signal":
        if level != "critical":
            level = "warning"
        message = "Spread signal points toward wind, mirage, light, weather, or other range-condition influence."
        if batch_spread_reason:
            message += f" {batch_spread_reason}"
        items.append(message)
        impacts.append(
            "Condition effects can make a good load look poor or make a weak load look better than it is."
        )
        add_focus_area("environment control")
        add_focus_area("repeatability")
        if not suggested_action:
            suggested_action = (
                control_action
                or "Repeat or compare the same load in calmer or well-documented conditions before changing charge or seating."
            )
    elif signal_hint == "node_or_barrel_timing_signal":
        if level != "critical":
            level = "warning"
        message = "Spread signal points toward vertical pattern, seating depth, barrel timing, or tracking consistency."
        if batch_spread_reason:
            message += f" {batch_spread_reason}"
        items.append(message)
        impacts.append(
            "Stable ES/SD with a vertical target pattern can lead to the wrong powder change if seating depth, barrel timing, or rest tracking is not checked first."
        )
        add_focus_area("vertical pattern")
        add_focus_area("seating depth")
        add_focus_area("barrel timing")
        if not suggested_action:
            suggested_action = (
                control_action
                or "Repeat the same load with controlled tracking, then try a small seating-depth bracket if the vertical pattern remains."
            )
    elif signal_hint == "insufficient_evidence":
        if level != "critical":
            level = "warning"
        items.append(
            "Spread signal is still insufficient for separating ammo, shooter, setup, and environment effects."
        )
        impacts.append(
            "The system needs matched chrono and group evidence before it can give a stronger cause hint."
        )
        add_focus_area("matched evidence")
        add_focus_area("data trust")
        if not suggested_action:
            suggested_action = (
                control_action
                or "Capture matched chrono and group data under the same setup before making a hard call."
            )
    if decision_state and decision_state != "ready_for_cautious_optimization":
        if level != "critical":
            level = "warning"
        message = f"Decision gate: {decision_label or decision_state}."
        if decision_rationale:
            message += f" {decision_rationale}"
        items.append(message)
        impacts.append(
            "The next action should confirm the decision gate before the load is accepted, rejected, or optimized."
        )
        add_focus_area("decision gate")
    elif decision_state == "ready_for_cautious_optimization":
        items.append(
            "Decision gate: ready for cautious one-variable-at-a-time optimization."
        )
    if not profile_note_added and (profile_title or profile_emphasis):
        message = f"Use profile focus: {profile_title or 'validation focus'}."
        if profile_emphasis:
            message += f" {profile_emphasis}"
        items.append(message)
    if not quality_note_added and spread_quality_level:
        score_text = (
            f" ({spread_quality_score:.1f}/100)"
            if spread_quality_score is not None
            else ""
        )
        items.append(f"Spread evidence quality is {spread_quality_level}{score_text}.")
        if spread_quality_level in {"very_thin", "thin"}:
            if level != "critical":
                level = "warning"
            add_focus_area("evidence quality")
    if not learning_note_added and (learning_title or learning_takeaway):
        message = f"Learning note: {learning_title or 'spread lesson'}."
        if learning_takeaway:
            message += f" {learning_takeaway}"
        items.append(message)
    if has_measured_velocity_flag is False and not smart_evidence_diagnostics:
        if level != "critical":
            level = "warning"
        items.append(
            "Session still lacks measured chronograph data for the active setup."
        )
        impacts.append(
            "Velocity trends and pressure interpretation remain more model-driven than measured until chrono data is logged."
        )
        add_focus_area("velocity validation")
        add_focus_area("data trust")
        if not suggested_action:
            suggested_action = "Capture a chronograph string for the current setup before treating the node as verified."
    if has_measured_group_flag is False and not smart_evidence_diagnostics:
        if level != "critical":
            level = "warning"
        items.append("Session still lacks measured grouping data for the active setup.")
        impacts.append(
            "Grouping conclusions remain provisional until the barrel and seating behavior are confirmed on target."
        )
        add_focus_area("grouping")
        add_focus_area("data trust")
        if not suggested_action:
            suggested_action = "Add one measured group at the active seating depth before ranking this combination highly."
    if (
        level in {"warning", "critical"}
        and smart_guidance_setup
        and smart_next_action == "collect_matched_group_and_chrono"
        and not smart_evidence_action
    ):
        suggested_action = smart_guidance_setup

    if not items:
        return {
            "level": "unknown",
            "title": "Runtime delta unavailable",
            "summary": "There is not enough runtime data to explain the current delta yet.",
            "items": [],
            "impacts": [],
            "focus_areas": [],
            "suggested_action": None,
        }

    title_map = {
        "critical": "Runtime delta requires attention",
        "warning": "Runtime delta shows active deviations",
        "ok": "Runtime delta is within the current recommendation",
        "unknown": "Runtime delta unavailable",
    }
    summary_map = {
        "critical": "Current settings or safety state should be reviewed before further testing.",
        "warning": "The active setup differs from the current recommendation or has limited support data.",
        "ok": "The active setup is aligned with the current session recommendation.",
        "unknown": "There is not enough runtime data to explain the current delta yet.",
    }
    summary = summary_map[level]
    if focus_areas and level in {"warning", "critical"}:
        summary += " Focus: " + ", ".join(focus_areas[:4]) + "."

    smart_summary = None
    if smart_candidate_robustness or smart_node_fit or smart_harmonic_tier:
        parts = []
        if smart_candidate_robustness:
            parts.append(f"robustness {smart_candidate_robustness}")
        if smart_node_fit:
            parts.append(f"node fit {smart_node_fit}")
        if smart_harmonic_tier:
            parts.append(f"harmonics {smart_harmonic_tier}")
        smart_summary = "Smart engine sees " + ", ".join(parts) + "."
        items.append(smart_summary)
        if level in {"warning", "critical"} and smart_candidate_robustness == "low":
            add_focus_area("engine robustness")
        if level in {"warning", "critical"} and smart_node_fit in {
            "developing",
            "unclear",
        }:
            add_focus_area("node fit")
    if smart_next_action and smart_next_reason:
        items.append(
            f"Smart engine next test: {smart_next_action} - {smart_next_reason}"
        )
    elif smart_next_action:
        items.append(f"Smart engine next test: {smart_next_action}")
    if smart_gate_label:
        gate_text = f"Smart engine gate: {smart_gate_label}"
        if smart_gate_next:
            gate_text += f" - {smart_gate_next}"
        items.append(gate_text)
    if smart_plan_summary:
        plan_text = f"Smart engine protocol: {smart_plan_summary}"
        if smart_plan_session_type:
            plan_text += f" [{smart_plan_session_type}]"
        if smart_plan_estimated_rounds is not None and smart_plan_estimated_rounds > 0:
            plan_text += f" ~{smart_plan_estimated_rounds} rounds"
        items.append(plan_text)
    first_keep_constant = next(
        (str(item).strip() for item in smart_plan_keep_constant if str(item).strip()),
        "",
    )
    if first_keep_constant:
        items.append(f"Smart engine keep constant: {first_keep_constant}")
    first_capture = next(
        (str(item).strip() for item in smart_plan_capture if str(item).strip()), ""
    )
    if first_capture:
        items.append(f"Smart engine capture: {first_capture}")
    first_hold_line = next(
        (str(item).strip() for item in smart_do_not_change_yet if str(item).strip()), ""
    )
    if first_hold_line:
        items.append(f"Smart engine hold: {first_hold_line}")
    first_block = next(
        (
            str(item.get("title") or item.get("kind") or "").strip()
            for item in smart_blocked_by
            if isinstance(item, dict)
            and str(item.get("title") or item.get("kind") or "").strip()
        ),
        "",
    )
    if first_block:
        items.append(f"Smart engine blocker: {first_block}")
    if smart_confidence_level:
        confidence_text = f"Smart engine confidence: {smart_confidence_level}"
        if smart_confidence_score is not None:
            confidence_text += f" ({smart_confidence_score:.1f}/100)"
        if smart_confidence_uncertainty:
            confidence_text += f" - uncertainty {smart_confidence_uncertainty}"
        items.append(confidence_text)
    if smart_confidence_summary:
        items.append(f"Smart engine confidence note: {smart_confidence_summary}")
    for baseline_item in smart_baseline_items:
        text = str(baseline_item).strip()
        if text:
            items.append(text)
    for baseline_impact in smart_baseline_impacts:
        text = str(baseline_impact).strip()
        if text and text not in impacts:
            impacts.append(text)
    for baseline_focus in smart_baseline_focus:
        add_focus_area(str(baseline_focus))
    for evidence_item in smart_evidence_items:
        text = str(evidence_item).strip()
        if text:
            items.append(text)
    for evidence_impact in smart_evidence_impacts:
        text = str(evidence_impact).strip()
        if text and text not in impacts:
            impacts.append(text)
    for evidence_focus in smart_evidence_focus:
        add_focus_area(str(evidence_focus))
    if smart_branch_display_line:
        items.append(f"Smart engine branch: {smart_branch_display_line}")
    if smart_bullet_fit_level:
        bullet_fit_text = f"Smart engine bullet fit: {smart_bullet_fit_level}"
        if smart_bullet_fit_score is not None:
            bullet_fit_text += f" ({smart_bullet_fit_score:.1f}/100)"
        if smart_bullet_fit_message:
            bullet_fit_text += f" - {smart_bullet_fit_message}"
        items.append(bullet_fit_text)
    if smart_jump_band or smart_jump_summary:
        jump_text = "Smart engine jump: "
        if smart_jump_band:
            jump_text += smart_jump_band
            if smart_current_jump is not None:
                jump_text += f" ({smart_current_jump:.3f} mm)"
        if smart_jump_summary:
            jump_text += f" - {smart_jump_summary}"
        items.append(jump_text)
    elif smart_branch_label:
        branch_text = f"Smart engine branch: {smart_branch_label}"
        if smart_branch_compare_mode:
            branch_text += f" ({smart_branch_compare_mode})"
        items.append(branch_text)
    if smart_active_return_line:
        items.append(f"Smart engine baseline control: {smart_active_return_line}")
    elif smart_charge_return_line:
        items.append(f"Smart engine charge baseline: {smart_charge_return_line}")
    elif smart_seating_return_line:
        items.append(f"Smart engine seating baseline: {smart_seating_return_line}")
    if (
        level in {"warning", "critical"}
        and not suggested_action
        and smart_preferred_action
    ):
        suggested_action = smart_preferred_action

    return {
        "level": level,
        "title": title_map[level],
        "summary": summary,
        "items": items[:36],
        "impacts": impacts[:3],
        "focus_areas": focus_areas[:36],
        "suggested_action": suggested_action,
        "smart_engine": {
            "candidate_robustness": smart_candidate_robustness or None,
            "node_fit": smart_node_fit or None,
            "harmonics_tier": smart_harmonic_tier or None,
            "bullet_fit_level": smart_bullet_fit_level or None,
            "bullet_fit_score": smart_bullet_fit_score,
            "bullet_fit_message": smart_bullet_fit_message or None,
            "jump_band": smart_jump_band or None,
            "jump_summary": smart_jump_summary or None,
            "current_jump_mm": smart_current_jump,
            "next_action": smart_next_action or None,
            "next_reason": smart_next_reason or None,
            "guidance_title": smart_guidance_title or None,
            "guidance_setup": smart_guidance_setup or None,
            "validation_label": smart_gate_label or None,
            "validation_next_gate": smart_gate_next or None,
            "plan_summary": smart_plan_summary or None,
            "plan_session_type": smart_plan_session_type or None,
            "plan_success_criteria": smart_plan_success or None,
            "plan_estimated_rounds": smart_plan_estimated_rounds,
            "plan_keep_constant": smart_plan_keep_constant[:4],
            "plan_capture": smart_plan_capture[:4],
            "do_not_change_yet": smart_do_not_change_yet[:4],
            "blocked_by": smart_blocked_by[:4],
            "confidence_level": smart_confidence_level or None,
            "confidence_score": smart_confidence_score,
            "confidence_summary": smart_confidence_summary or None,
            "confidence_uncertainty": smart_confidence_uncertainty or None,
            "branch_label": smart_branch_label or None,
            "branch_compare_mode": smart_branch_compare_mode or None,
            "branch_display_line": smart_branch_display_line or None,
            "branch_action_line": smart_branch_action_line or None,
            "baseline_status": str(
                smart_baseline_diagnostics.get("status") or ""
            ).strip()
            or None,
            "baseline_items": [
                str(item).strip() for item in smart_baseline_items if str(item).strip()
            ][:4],
            "baseline_impacts": [
                str(item).strip()
                for item in smart_baseline_impacts
                if str(item).strip()
            ][:4],
            "baseline_focus_areas": [
                str(item).strip() for item in smart_baseline_focus if str(item).strip()
            ][:4],
            "evidence_status": str(
                smart_evidence_diagnostics.get("status") or ""
            ).strip()
            or None,
            "evidence_items": [
                str(item).strip() for item in smart_evidence_items if str(item).strip()
            ][:4],
            "evidence_impacts": [
                str(item).strip()
                for item in smart_evidence_impacts
                if str(item).strip()
            ][:4],
            "evidence_focus_areas": [
                str(item).strip() for item in smart_evidence_focus if str(item).strip()
            ][:4],
            "charge_alignment": smart_charge_alignment or None,
            "charge_target": smart_charge_target or None,
            "charge_return_line": smart_charge_return_line or None,
            "seating_alignment": smart_seating_alignment or None,
            "seating_target": smart_seating_target or None,
            "seating_return_line": smart_seating_return_line or None,
            "active_return_line": smart_active_return_line or None,
            "preferred_action": smart_preferred_action,
            "summary": smart_summary,
            "recommendation_count": len(smart_recommendation_stack),
        },
    }


__all__ = ["build_load_session_runtime", "build_load_session_runtime_delta"]
