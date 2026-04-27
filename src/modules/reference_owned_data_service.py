from __future__ import annotations

import json
from typing import Any

from ..ballistics.services import (
    _build_projectile_terminal_profile,
    _resolve_bullet_profile,
)
from ..utils.unit_preferences import (
    format_group_size_mm,
    format_length_mm,
    format_velocity_fps,
    format_weight_grains,
)


def _safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def _safe_int(value: object) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(str(value).strip())
    except Exception:
        return None


def _safe_json_loads(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_profile_health_summary(
    evidence_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    evidence_summary = evidence_summary if isinstance(evidence_summary, dict) else {}
    history_level = (
        str(evidence_summary.get("history_level") or "unknown").strip().lower()
    )
    lot_level = str(evidence_summary.get("lot_level") or "unknown").strip().lower()
    brass_level = str(evidence_summary.get("brass_level") or "unknown").strip().lower()
    projectile_level = (
        str(evidence_summary.get("projectile_level") or "unknown").strip().lower()
    )
    pressure_count = int(evidence_summary.get("pressure_count") or 0)
    has_reference_data = bool(evidence_summary.get("has_reference_data"))

    def _rank(level: str) -> int:
        return {
            "critical": 4,
            "warning": 3,
            "info": 2,
            "ok": 1,
            "unknown": 0,
            "neutral": 0,
        }.get(level, 0)

    overall_level = "unknown"
    overall_rank = -1
    for level in (
        history_level,
        lot_level,
        brass_level,
        projectile_level,
        "warning" if pressure_count else ("ok" if has_reference_data else "unknown"),
    ):
        rank = _rank(level)
        if rank > overall_rank:
            overall_level = level
            overall_rank = rank

    parts = []
    history_title = str(evidence_summary.get("history_title") or "").strip()
    lot_title = str(evidence_summary.get("lot_title") or "").strip()
    brass_title = str(evidence_summary.get("brass_title") or "").strip()
    projectile_title = str(evidence_summary.get("projectile_title") or "").strip()
    if history_title:
        parts.append(history_title)
    if lot_title and lot_title != history_title:
        parts.append(lot_title)
    if brass_title and brass_title not in {history_title, lot_title}:
        parts.append(brass_title)
    if projectile_title and projectile_title not in {
        history_title,
        lot_title,
        brass_title,
    }:
        parts.append(projectile_title)
    if not parts and has_reference_data:
        parts.append("Reference data is available")
    if not parts:
        parts.append("No health info yet")

    return {
        "level": overall_level,
        "title": parts[0],
        "summary": " | ".join(parts[:2]),
        "history_level": history_level,
        "lot_level": lot_level,
        "brass_level": brass_level,
        "projectile_level": projectile_level,
        "reference_level": "ok" if has_reference_data else "unknown",
        "pressure_level": "warning" if pressure_count else "ok",
    }


def build_profile_trust_map(evidence_summary: dict[str, Any] | None) -> dict[str, Any]:
    evidence_summary = evidence_summary if isinstance(evidence_summary, dict) else {}
    measured_score = 0
    simulated_score = 0
    derived_score = 0
    assumed_score = 0
    notes: list[str] = []

    chrono_count = int(evidence_summary.get("chrono_count") or 0)
    accuracy_count = int(evidence_summary.get("accuracy_count") or 0)
    pressure_count = int(evidence_summary.get("pressure_count") or 0)
    has_reference_data = bool(evidence_summary.get("has_reference_data"))
    lot_level = str(evidence_summary.get("lot_level") or "unknown").strip().lower()
    brass_level = str(evidence_summary.get("brass_level") or "unknown").strip().lower()
    projectile_level = (
        str(evidence_summary.get("projectile_level") or "unknown").strip().lower()
    )
    analysis_level = (
        str(evidence_summary.get("analysis_level") or "unknown").strip().lower()
    )

    if chrono_count:
        measured_score += min(3, chrono_count)
    if accuracy_count:
        measured_score += min(2, accuracy_count)
    if pressure_count:
        measured_score += 1
    if has_reference_data:
        simulated_score += 2
    if analysis_level in {"ok", "info", "warning"}:
        derived_score += 2
    if lot_level in {"ok", "info"}:
        derived_score += 1
    if brass_level in {"ok", "info"}:
        derived_score += 1
    if projectile_level in {"ok", "info"}:
        derived_score += 1
    if not chrono_count:
        assumed_score += 2
    if not accuracy_count:
        assumed_score += 1
    if not has_reference_data:
        assumed_score += 1
    if brass_level in {"warning", "unknown"}:
        assumed_score += 1
    if lot_level in {"warning", "unknown"}:
        assumed_score += 1
    if projectile_level in {"warning", "unknown"}:
        assumed_score += 1

    if measured_score:
        notes.append(
            f"Measured basis: {chrono_count} chrono, {accuracy_count} precision."
        )
    if simulated_score:
        notes.append("Simulated basis is available for velocity/pressure.")
    if derived_score:
        notes.append("Derived basis uses lots, brass, and active analysis.")
    if projectile_level in {"ok", "info"}:
        notes.append(
            "Projectile fit is derived from construction, terminal window, and intended use."
        )
    if assumed_score:
        notes.append("Assumed basis is still visible in parts of the model.")

    def _level(score: int) -> str:
        if score >= 4:
            return "ok"
        if score >= 2:
            return "info"
        if score >= 1:
            return "warning"
        return "unknown"

    return {
        "measured_score": measured_score,
        "simulated_score": simulated_score,
        "derived_score": derived_score,
        "assumed_score": assumed_score,
        "measured_level": _level(measured_score),
        "simulated_level": _level(simulated_score),
        "derived_level": _level(derived_score),
        "assumed_level": (
            "warning"
            if assumed_score >= 3
            else ("info" if assumed_score >= 1 else "ok")
        ),
        "summary": " | ".join(notes[:3]) if notes else "No trust data yet",
    }


def _resolve_component_lot_id(
    db,
    *,
    component_type: str,
    component_id: int | None,
    context: dict[str, Any],
) -> int | None:
    selected_lot_id = _safe_int(
        context.get("selected_lot_id") or context.get("component_lot_id")
    )
    if selected_lot_id:
        return selected_lot_id

    lot_number = str(
        context.get("selected_lot_number") or context.get("lot_number") or ""
    ).strip()
    if not lot_number or not component_id:
        return None

    try:
        rows = (
            db.execute_query(
                """
            SELECT id
            FROM component_lots
            WHERE component_type = ? AND component_id = ? AND lot_number = ?
            ORDER BY id DESC
            LIMIT 1
            """,
                (component_type, component_id, lot_number),
            )
            or []
        )
    except Exception:
        rows = []
    if not rows:
        return None
    return _safe_int(rows[0].get("id"))


def _build_lot_quality_summary(
    db,
    *,
    component_type: str,
    component_id: int | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "component_type": component_type,
        "lot_id": None,
        "lot_number": str(
            context.get("selected_lot_number") or context.get("lot_number") or ""
        ).strip(),
        "level": "unknown",
        "title": "",
        "note": "",
    }
    lot_id = _resolve_component_lot_id(
        db,
        component_type=component_type,
        component_id=component_id,
        context=context,
    )
    summary["lot_id"] = lot_id
    if not lot_id:
        return summary

    if component_type == "bullet":
        try:
            stats = db.get_component_lot_stats(lot_id) or {}
        except Exception:
            stats = {}
        sample_count = _safe_int(stats.get("sample_count")) or 0
        weight_stddev = _safe_float(stats.get("weight_stddev_grains"))
        if sample_count >= 10:
            summary["level"] = "ok"
            summary["title"] = "Bullet lot is well measured"
        elif sample_count >= 3:
            summary["level"] = "info"
            summary["title"] = "Bullet lot is partially measured"
        else:
            summary["level"] = "unknown"
            summary["title"] = "Bullet lot is missing a measurement series"
        note = (
            f"bullet lot {summary['lot_number'] or lot_id}: {sample_count} measurements"
        )
        if weight_stddev is not None:
            note += f", SD {weight_stddev:.3f} gr"
        summary["note"] = note
        return summary

    try:
        learning = db.get_component_lot_learning_profile(lot_id) or {}
    except Exception:
        learning = {}

    confidence_score = _safe_float(learning.get("confidence_score")) or 0.0
    data_points = _safe_int(learning.get("data_points")) or 0
    pressure_watch_count = _safe_int(learning.get("pressure_watch_count")) or 0
    confidence_label = str(learning.get("confidence_label") or "").strip().lower()

    if component_type == "powder":
        if pressure_watch_count > 0:
            summary["level"] = "warning"
            summary["title"] = "Powder lot requires follow-up"
        elif confidence_score >= 0.7 or data_points >= 4:
            summary["level"] = "ok"
            summary["title"] = "Powder lot is well understood"
        elif confidence_score > 0.0 or data_points > 0:
            summary["level"] = "info"
            summary["title"] = "Powder lot is still being learned"
        else:
            summary["level"] = "unknown"
            summary["title"] = "Powder lot has no learning yet"
        summary["note"] = (
            f"powder lot {summary['lot_number'] or lot_id}: "
            f"{confidence_label or f'{confidence_score:.2f}'}"
        )
        if pressure_watch_count > 0:
            summary["note"] += f", {pressure_watch_count} pressure findings"
        return summary

    if component_type == "primer":
        if confidence_score >= 0.65 or data_points >= 3:
            summary["level"] = "ok"
            summary["title"] = "Primer lot is well understood"
        elif confidence_score > 0.0 or data_points > 0:
            summary["level"] = "info"
            summary["title"] = "Primer lot is still being learned"
        else:
            summary["level"] = "unknown"
            summary["title"] = "Primer lot has no learning yet"
        summary["note"] = (
            f"primer lot {summary['lot_number'] or lot_id}: "
            f"{confidence_label or f'{confidence_score:.2f}'}"
        )
    return summary


def build_profile_evidence_summary(
    db,
    ammo_profile_id: int | None,
    analysis_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "chrono_count": 0,
        "accuracy_count": 0,
        "pressure_count": 0,
        "best_group_mm": None,
        "avg_group_mm": None,
        "has_reference_data": False,
        "latest_velocity_fps": None,
        "latest_sd_fps": None,
        "latest_es_fps": None,
        "latest_group_mm": None,
        "predicted_velocity_fps": None,
        "evidence_label": "No evidence yet",
        "trend_label": "No trend data yet",
        "history_level": "unknown",
        "history_title": "History is missing",
        "lot_label": "",
        "lot_level": "unknown",
        "lot_title": "Lots are not verified",
        "lot_notes": "",
        "lot_actions": [],
        "brass_level": "unknown",
        "brass_title": "",
        "projectile_level": "unknown",
        "projectile_title": "",
        "projectile_label": "",
        "analysis_level": "unknown",
        "analysis_title": "",
    }
    analysis_context = analysis_context if isinstance(analysis_context, dict) else {}
    internal_ballistics = (
        analysis_context.get("internal_ballistics")
        if isinstance(analysis_context.get("internal_ballistics"), dict)
        else {}
    )
    pressure_assessment = (
        analysis_context.get("pressure_assessment")
        if isinstance(analysis_context.get("pressure_assessment"), dict)
        else {}
    )
    brass_context = (
        analysis_context.get("brass_context")
        if isinstance(analysis_context.get("brass_context"), dict)
        else {}
    )
    summary["brass_level"] = (
        str(brass_context.get("level") or "unknown").strip().lower() or "unknown"
    )
    summary["brass_title"] = str(brass_context.get("title") or "").strip()
    pressure_level = str(pressure_assessment.get("level") or "").strip().lower()
    internal_level = str(internal_ballistics.get("level") or "").strip().lower()
    if pressure_level == "critical":
        summary["analysis_level"] = "warning"
        summary["analysis_title"] = "Active analysis indicates high pressure risk"
    elif internal_level == "critical":
        summary["analysis_level"] = "warning"
        summary["analysis_title"] = (
            "Active analysis indicates high internal-ballistics risk"
        )
    elif pressure_level == "warning":
        summary["analysis_level"] = "info"
        summary["analysis_title"] = "Active analysis indicates a narrow pressure margin"
    elif internal_level == "warning":
        summary["analysis_level"] = "info"
        summary["analysis_title"] = (
            "Active analysis indicates challenging fill ratio or burn behavior"
        )

    if not ammo_profile_id:
        if summary["analysis_title"]:
            summary["evidence_label"] = summary["analysis_title"]
            summary["history_level"] = summary["analysis_level"]
            summary["history_title"] = summary["analysis_title"]
        return summary

    try:
        profile_row = db.get_by_id("ammo_profiles", ammo_profile_id) or {}
    except Exception:
        profile_row = {}

    try:
        chrono_rows = (
            db.execute_query(
                """
            SELECT *
            FROM chronograph_sessions
            WHERE ammo_profile_id = ?
            ORDER BY datetime(session_date) DESC, id DESC
            LIMIT 5
            """,
                (ammo_profile_id,),
            )
            or []
        )
    except Exception:
        chrono_rows = []

    try:
        accuracy_rows = (
            db.execute_query(
                """
            SELECT *
            FROM rifle_accuracy_tests
            WHERE ammo_profile_id = ?
            ORDER BY datetime(test_date) DESC, id DESC
            LIMIT 5
            """,
                (ammo_profile_id,),
            )
            or []
        )
    except Exception:
        accuracy_rows = []

    try:
        pressure_rows = (
            db.execute_query(
                """
            SELECT *
            FROM pressure_signs
            WHERE ammo_profile_id = ?
            ORDER BY datetime(date) DESC, id DESC
            LIMIT 5
            """,
                (ammo_profile_id,),
            )
            or []
        )
    except Exception:
        pressure_rows = []

    try:
        reference_rows = (
            db.execute_query(
                "SELECT * FROM grt_data WHERE ammo_profile_id = ? LIMIT 1",
                (ammo_profile_id,),
            )
            or []
        )
        reference_row = dict(reference_rows[0]) if reference_rows else None
    except Exception:
        reference_row = None

    best_group_values: list[float] = []
    avg_group_values: list[float] = []
    for row in accuracy_rows:
        best_group = _safe_float(row.get("best_group_mm"))
        avg_group = _safe_float(
            row.get("average_group_size_mm") or row.get("avg_group_mm")
        )
        if best_group is not None:
            best_group_values.append(best_group)
        if avg_group is not None:
            avg_group_values.append(avg_group)

    summary["chrono_count"] = len(chrono_rows)
    summary["accuracy_count"] = len(accuracy_rows)
    summary["pressure_count"] = len(pressure_rows)
    summary["best_group_mm"] = min(best_group_values) if best_group_values else None
    summary["avg_group_mm"] = (
        sum(avg_group_values) / len(avg_group_values) if avg_group_values else None
    )
    summary["has_reference_data"] = bool(reference_row)

    if chrono_rows:
        latest = chrono_rows[0]
        summary["latest_velocity_fps"] = _safe_float(latest.get("avg_velocity_fps"))
        summary["latest_sd_fps"] = _safe_float(latest.get("sd_fps"))
        summary["latest_es_fps"] = _safe_float(latest.get("es_fps"))
    if accuracy_rows:
        latest = accuracy_rows[0]
        summary["latest_group_mm"] = _safe_float(
            latest.get("best_group_mm") or latest.get("average_group_size_mm")
        )
    if reference_row:
        summary["predicted_velocity_fps"] = _safe_float(
            reference_row.get("predicted_velocity")
        )

    lot_bits = []
    component_context = _safe_json_loads(profile_row.get("component_context_json"))
    lot_summaries: list[dict[str, Any]] = []
    if isinstance(component_context, dict):
        bullet_context = (
            component_context.get("bullet")
            if isinstance(component_context.get("bullet"), dict)
            else {}
        )
        powder_context = (
            component_context.get("powder")
            if isinstance(component_context.get("powder"), dict)
            else {}
        )
        primer_context = (
            component_context.get("primer")
            if isinstance(component_context.get("primer"), dict)
            else {}
        )
        brass_context = (
            component_context.get("brass")
            if isinstance(component_context.get("brass"), dict)
            else {}
        )
        if bullet_context.get("selected_lot_number") or bullet_context.get(
            "lot_number"
        ):
            lot_bits.append(
                f"bullet lot {bullet_context.get('selected_lot_number') or bullet_context.get('lot_number')}"
            )
        if powder_context.get("selected_lot_number") or powder_context.get(
            "lot_number"
        ):
            lot_bits.append(
                f"powder lot {powder_context.get('selected_lot_number') or powder_context.get('lot_number')}"
            )
        if primer_context.get("selected_lot_number") or primer_context.get(
            "lot_number"
        ):
            lot_bits.append(
                f"primer lot {primer_context.get('selected_lot_number') or primer_context.get('lot_number')}"
            )
        if brass_context.get("lot_number"):
            lot_bits.append(f"case lot {brass_context.get('lot_number')}")
        bullet_lot_summary = _build_lot_quality_summary(
            db,
            component_type="bullet",
            component_id=_safe_int(profile_row.get("bullet_id")),
            context=bullet_context,
        )
        powder_lot_summary = _build_lot_quality_summary(
            db,
            component_type="powder",
            component_id=_safe_int(profile_row.get("powder_id")),
            context=powder_context,
        )
        primer_lot_summary = _build_lot_quality_summary(
            db,
            component_type="primer",
            component_id=_safe_int(profile_row.get("primer_id")),
            context=primer_context,
        )
        lot_summaries = [
            item
            for item in [bullet_lot_summary, powder_lot_summary, primer_lot_summary]
            if item.get("lot_id") or item.get("lot_number")
        ]
    summary["lot_label"] = " | ".join(str(bit) for bit in lot_bits if str(bit).strip())

    bullet_row = {}
    try:
        bullet_row = db.get_by_id("bullets", profile_row.get("bullet_id")) or {}
    except Exception:
        bullet_row = {}
    bullet_row = (
        _resolve_bullet_profile(bullet_row) if isinstance(bullet_row, dict) else {}
    )
    usage_profile = (
        str(
            component_context.get("usage_profile")
            or profile_row.get("usage_profile")
            or profile_row.get("purpose")
            or "precision"
        )
        .strip()
        .lower()
    )
    projectile_profile = (
        _build_projectile_terminal_profile(bullet_row, usage_profile)
        if isinstance(bullet_row, dict) and bullet_row
        else {}
    )
    projectile_summary = str(projectile_profile.get("profile_summary") or "").strip()
    preferred_min = _safe_float(projectile_profile.get("preferred_impact_min_fps"))
    preferred_max = _safe_float(projectile_profile.get("preferred_impact_max_fps"))
    minimum_expansion = _safe_float(projectile_profile.get("minimum_expansion_fps"))
    projectile_confidence = (
        str(projectile_profile.get("confidence") or "").strip().lower()
    )
    projectile_notes = [
        str(note).strip()
        for note in (projectile_profile.get("notes") or [])
        if str(note).strip()
    ]
    projectile_bits: list[str] = []
    if projectile_summary:
        projectile_bits.append(projectile_summary)
    if preferred_min is not None and preferred_max is not None:
        projectile_bits.append(
            f"window {format_velocity_fps(preferred_min)}-{format_velocity_fps(preferred_max)}"
        )
    elif preferred_min is not None:
        projectile_bits.append(f"floor {format_velocity_fps(preferred_min)}")
    elif minimum_expansion is not None:
        projectile_bits.append(f"minimum {format_velocity_fps(minimum_expansion)}")
    summary["projectile_label"] = " | ".join(projectile_bits)

    is_hunting = usage_profile.startswith("hunting")
    construction = (
        str(projectile_profile.get("construction_type") or "").strip().lower()
    )
    bullet_type = str(projectile_profile.get("bullet_type") or "").strip().lower()
    if projectile_summary:
        if is_hunting and (
            construction in {"fmj", "match", "otm_match", "target"}
            or bullet_type in {"fmj", "match", "target"}
        ):
            summary["projectile_level"] = "warning"
            summary["projectile_title"] = "Projectile fit looks weak for hunting use"
        elif is_hunting and preferred_min is not None:
            summary["projectile_level"] = (
                "ok" if projectile_confidence == "high" else "info"
            )
            summary["projectile_title"] = (
                "Projectile fit is documented for terminal use"
            )
        elif projectile_confidence in {"high", "medium"}:
            summary["projectile_level"] = "info"
            summary["projectile_title"] = "Projectile fit is partially documented"
        else:
            summary["projectile_level"] = "unknown"
            summary["projectile_title"] = "Projectile fit needs more data"
    elif is_hunting:
        summary["projectile_level"] = "warning"
        summary["projectile_title"] = "Projectile fit needs more terminal data"

    if projectile_notes and not summary["projectile_label"]:
        summary["projectile_label"] = projectile_notes[0]

    lot_notes = [
        str(item.get("note") or "").strip()
        for item in lot_summaries
        if str(item.get("note") or "").strip()
    ]
    summary["lot_notes"] = " | ".join(lot_notes)
    lot_actions: list[str] = []
    for item in lot_summaries:
        component_type = str(item.get("component_type") or "").strip().lower()
        level = str(item.get("level") or "unknown").strip().lower()
        title = str(item.get("title") or "").strip().lower()
        note = str(item.get("note") or "").strip()
        if component_type == "bullet":
            if "missing a measurement series" in title:
                lot_actions.append(
                    "Bullet lot: measure 10-20 bullets for average, SD, and length."
                )
            elif level == "info":
                lot_actions.append(
                    "Bullet lot: extend the measurement series before reading too much into small seating and node differences."
                )
        elif component_type == "powder":
            if level == "warning":
                lot_actions.append(
                    "Powder lot: run a short verification series for velocity and pressure before further fine-tuning."
                )
            elif level == "info":
                lot_actions.append(
                    "Powder lot: build more learning with a chronograph before trusting small charge differences."
                )
        elif component_type == "primer":
            if level in {"unknown", "info"}:
                lot_actions.append(
                    "Primer lot: confirm ES/SD and pressure response with a short control series."
                )
        if note and "0 measurements" in note and component_type == "bullet":
            lot_actions.append("Bullet lot: no measurement series is registered yet.")
    deduped_lot_actions: list[str] = []
    seen_actions: set[str] = set()
    for action in lot_actions:
        if action and action not in seen_actions:
            deduped_lot_actions.append(action)
            seen_actions.add(action)
    summary["lot_actions"] = deduped_lot_actions
    lot_levels = [str(item.get("level") or "unknown") for item in lot_summaries]
    if any(level == "warning" for level in lot_levels):
        summary["lot_level"] = "warning"
        summary["lot_title"] = "Lots require follow-up"
    elif sum(1 for level in lot_levels if level == "ok") >= 2:
        summary["lot_level"] = "ok"
        summary["lot_title"] = "Strong lot knowledge"
    elif any(level in {"ok", "info"} for level in lot_levels):
        summary["lot_level"] = "info"
        summary["lot_title"] = "Some lot knowledge"

    evidence_bits = []
    if summary["chrono_count"]:
        evidence_bits.append(f"{summary['chrono_count']} chrono sessions")
    if summary["accuracy_count"]:
        evidence_bits.append(f"{summary['accuracy_count']} precision tests")
    if summary["pressure_count"]:
        evidence_bits.append(f"{summary['pressure_count']} pressure events")
    else:
        evidence_bits.append("no pressure events recorded")
    if summary["has_reference_data"]:
        evidence_bits.append("predicted reference data is available")
    if summary["best_group_mm"] is not None:
        evidence_bits.append(
            f"best group {format_group_size_mm(summary['best_group_mm'])}"
        )
    if summary["avg_group_mm"] is not None:
        evidence_bits.append(
            f"average group {format_group_size_mm(summary['avg_group_mm'])}"
        )
    if summary["lot_label"]:
        evidence_bits.append(summary["lot_label"])
    if summary["lot_title"] and summary["lot_level"] != "unknown":
        evidence_bits.append(summary["lot_title"].lower())
    if summary["projectile_title"] and summary["projectile_level"] != "unknown":
        evidence_bits.append(summary["projectile_title"].lower())

    trend_bits = []
    if summary["latest_velocity_fps"] is not None:
        trend_bits.append(
            f"latest chrono {format_velocity_fps(summary['latest_velocity_fps'])}"
        )
    if summary["latest_sd_fps"] is not None:
        trend_bits.append(f"SD {summary['latest_sd_fps']:.1f}")
    elif summary["latest_es_fps"] is not None:
        trend_bits.append(f"ES {summary['latest_es_fps']:.1f}")
    if summary["latest_group_mm"] is not None:
        trend_bits.append(
            f"latest group {format_group_size_mm(summary['latest_group_mm'])}"
        )
    if summary["predicted_velocity_fps"] is not None:
        trend_bits.append(
            f"predicted {format_velocity_fps(summary['predicted_velocity_fps'])}"
        )
    if summary["lot_notes"]:
        trend_bits.append(summary["lot_notes"])
    if summary["projectile_label"]:
        trend_bits.append(summary["projectile_label"])

    summary["evidence_label"] = (
        ", ".join(evidence_bits) if evidence_bits else "no data yet"
    )
    summary["trend_label"] = (
        " | ".join(trend_bits) if trend_bits else "no trend data yet"
    )

    if summary["analysis_title"]:
        summary["evidence_label"] = (
            f"{summary['evidence_label']}, {summary['analysis_title'].lower()}"
            if summary["evidence_label"]
            else str(summary["analysis_title"])
        )

    if summary["pressure_count"]:
        summary["history_level"] = "warning"
        summary["history_title"] = "History shows risk"
    elif summary["analysis_level"] == "warning":
        summary["history_level"] = "warning"
        summary["history_title"] = str(
            summary["analysis_title"] or "Active analysis shows risk"
        )
    elif summary["lot_level"] == "warning":
        summary["history_level"] = "warning"
        summary["history_title"] = "History shows lot risk"
    elif (
        summary["chrono_count"] >= 2
        and summary["accuracy_count"] >= 1
        and summary["lot_level"] == "ok"
    ):
        summary["history_level"] = "ok"
        summary["history_title"] = "Strong barrel and lot history"
    elif summary["analysis_level"] == "info" and (
        summary["chrono_count"] or summary["accuracy_count"]
    ):
        summary["history_level"] = "info"
        summary["history_title"] = str(
            summary["analysis_title"] or "Active analysis needs follow-up"
        )
    elif summary["chrono_count"] >= 2 and summary["accuracy_count"] >= 1:
        summary["history_level"] = "ok"
        summary["history_title"] = "Strong barrel history"
    elif (summary["chrono_count"] or summary["accuracy_count"]) and summary[
        "lot_level"
    ] in {"ok", "info"}:
        summary["history_level"] = "info"
        summary["history_title"] = "Some barrel and lot history"
    elif summary["chrono_count"] or summary["accuracy_count"]:
        summary["history_level"] = "info"
        summary["history_title"] = "Some barrel history"
    elif summary["lot_level"] == "ok":
        summary["history_level"] = "info"
        summary["history_title"] = "Lots are well documented"
    elif summary["lot_level"] == "info":
        summary["history_level"] = "info"
        summary["history_title"] = "Lots are still being learned"
    elif summary["projectile_level"] == "warning":
        summary["history_level"] = "warning"
        summary["history_title"] = str(
            summary["projectile_title"] or "Projectile fit needs attention"
        )
    elif summary["projectile_level"] == "info":
        summary["history_level"] = "info"
        summary["history_title"] = str(
            summary["projectile_title"] or "Projectile fit is partially documented"
        )
    return summary


def build_load_card_summary(db, ammo_profile_id: int | None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "title": "Load Card",
        "subtitle": "Select a load to see the summary.",
        "component_line": "",
        "measurement_line": "",
        "status_line": "",
        "projectile_line": "",
        "detail_lines": [],
    }
    if not ammo_profile_id:
        return summary

    profile = db.get_by_id("ammo_profiles", ammo_profile_id) or {}
    if not profile:
        summary["subtitle"] = "Could not read the load profile."
        return summary

    rifle = (
        db.get_by_id("rifles", profile.get("rifle_id"))
        if profile.get("rifle_id")
        else None
    )
    bullet = (
        db.get_by_id("bullets", profile.get("bullet_id"))
        if profile.get("bullet_id")
        else None
    )
    bullet = _resolve_bullet_profile(bullet) if isinstance(bullet, dict) else bullet
    powder = (
        db.get_by_id("powder", profile.get("powder_id"))
        if profile.get("powder_id")
        else None
    )
    primer = (
        db.get_by_id("primers", profile.get("primer_id"))
        if profile.get("primer_id")
        else None
    )
    case = (
        db.get_by_id("cases", profile.get("case_id"))
        if profile.get("case_id")
        else None
    )

    evidence = build_profile_evidence_summary(db, ammo_profile_id)
    component_context = _safe_json_loads(profile.get("component_context_json"))

    component_bits = []
    if bullet:
        bullet_name = " ".join(
            part
            for part in [bullet.get("manufacturer"), bullet.get("name")]
            if str(part or "").strip()
        ).strip()
        weight = _safe_float(
            profile.get("bullet_weight") or bullet.get("weight_grains")
        )
        if weight is not None:
            bullet_name = (
                f"{bullet_name} {format_weight_grains(weight, 'bullet')}".strip()
            )
        if bullet_name:
            component_bits.append(bullet_name)
    if powder:
        powder_name = str(powder.get("name") or "").strip()
        charge = _safe_float(profile.get("powder_charge"))
        if charge is not None:
            powder_name = (
                f"{powder_name} {format_weight_grains(charge, 'powder')}".strip()
            )
        if powder_name:
            component_bits.append(powder_name)
    if primer and primer.get("name"):
        component_bits.append(f"Primer {primer.get('name')}")
    if case and case.get("name"):
        component_bits.append(f"Case {case.get('name')}")
    if isinstance(component_context, dict):
        bullet_context = (
            component_context.get("bullet")
            if isinstance(component_context.get("bullet"), dict)
            else {}
        )
        powder_context = (
            component_context.get("powder")
            if isinstance(component_context.get("powder"), dict)
            else {}
        )
        primer_context = (
            component_context.get("primer")
            if isinstance(component_context.get("primer"), dict)
            else {}
        )
        if bullet_context.get("selected_lot_number") or bullet_context.get(
            "lot_number"
        ):
            component_bits.append(
                f"Bullet Lot {bullet_context.get('selected_lot_number') or bullet_context.get('lot_number')}"
            )
        if powder_context.get("selected_lot_number") or powder_context.get(
            "lot_number"
        ):
            component_bits.append(
                f"Powder Lot {powder_context.get('selected_lot_number') or powder_context.get('lot_number')}"
            )
        if primer_context.get("selected_lot_number") or primer_context.get(
            "lot_number"
        ):
            component_bits.append(
                f"Primer Lot {primer_context.get('selected_lot_number') or primer_context.get('lot_number')}"
            )

    reference_rows = (
        db.execute_query(
            "SELECT * FROM grt_data WHERE ammo_profile_id = ? LIMIT 1",
            (ammo_profile_id,),
        )
        or []
    )
    reference_row = dict(reference_rows[0]) if reference_rows else {}

    predicted_velocity = _safe_float(reference_row.get("predicted_velocity"))
    measured_velocity = _safe_float(profile.get("velocity_fps"))
    if measured_velocity is None:
        measured_velocity = evidence.get("latest_velocity_fps")

    measurement_bits = []
    if predicted_velocity is not None:
        measurement_bits.append(f"predicted {format_velocity_fps(predicted_velocity)}")
    if measured_velocity is not None:
        measurement_bits.append(f"measured {format_velocity_fps(measured_velocity)}")
    if evidence.get("best_group_mm") is not None:
        measurement_bits.append(
            f"best group {format_group_size_mm(evidence['best_group_mm'])}"
        )

    status_bits = []
    if rifle and rifle.get("name"):
        status_bits.append(str(rifle.get("name")))
    caliber = str(profile.get("caliber") or (rifle or {}).get("caliber") or "").strip()
    if caliber:
        status_bits.append(caliber)
    history_title = str(evidence.get("history_title") or "").strip()
    if history_title:
        status_bits.append(history_title)

    detail_lines = []
    coal = _safe_float(profile.get("coal"))
    cbto = _safe_float(profile.get("cbto"))
    if coal is not None:
        detail_lines.append(f"COAL {format_length_mm(coal)}")
    if cbto is not None:
        detail_lines.append(f"CBTO {format_length_mm(cbto)}")
    if evidence.get("chrono_count"):
        detail_lines.append(f"{int(evidence['chrono_count'])} chrono sessions")
    if evidence.get("accuracy_count"):
        detail_lines.append(f"{int(evidence['accuracy_count'])} precision tests")
    if evidence.get("pressure_count"):
        detail_lines.append(f"{int(evidence['pressure_count'])} pressure events")
    if (
        str(evidence.get("lot_title") or "").strip()
        and str(evidence.get("lot_level") or "unknown") != "unknown"
    ):
        detail_lines.append(str(evidence["lot_title"]))

    barrel_name = None
    h2o_capacity = None
    try:
        if profile.get("rifle_id"):
            rows = (
                db.execute_query(
                    "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ? LIMIT 1",
                    (profile["rifle_id"],),
                )
                or []
            )
            if rows and rows[0].get("profile_json"):
                details = _safe_json_loads(rows[0]["profile_json"])
                barrels = details.get("barrels") or []
                active_id = details.get("active_barrel_id")
                active_barrel = {}
                if isinstance(barrels, list):
                    for barrel in barrels:
                        if isinstance(barrel, dict) and str(barrel.get("id")) == str(
                            active_id
                        ):
                            active_barrel = dict(barrel)
                            break
                    if not active_barrel:
                        for barrel in barrels:
                            if isinstance(barrel, dict):
                                active_barrel = dict(barrel)
                                break
                if active_barrel:
                    barrel_name = str(active_barrel.get("name") or "").strip() or None
                    case_measurements = active_barrel.get("case_measurements") or {}
                    h2o_capacity = _safe_float(
                        case_measurements.get("h2o_capacity_grains")
                    )
    except Exception:
        barrel_name = barrel_name or None

    if barrel_name:
        detail_lines.append(f"Aktiv pipe {barrel_name}")
    if h2o_capacity is not None:
        detail_lines.append(f"H2O {format_weight_grains(h2o_capacity, 'powder')}")

    projectile_line = ""
    if isinstance(bullet, dict):
        projectile_profile = _build_projectile_terminal_profile(
            bullet,
            str(
                component_context.get("usage_profile")
                or profile.get("usage_profile")
                or "precision"
            ),
        )
        projectile_summary = str(
            projectile_profile.get("profile_summary") or ""
        ).strip()
        preferred_min = _safe_float(projectile_profile.get("preferred_impact_min_fps"))
        preferred_max = _safe_float(projectile_profile.get("preferred_impact_max_fps"))
        projectile_bits = []
        if projectile_summary:
            projectile_bits.append(f"Projectile {projectile_summary}")
            detail_lines.append(f"Projectile {projectile_summary}")
        if preferred_min is not None and preferred_max is not None:
            projectile_bits.append(
                f"Terminal window {format_velocity_fps(preferred_min)}-{format_velocity_fps(preferred_max)}"
            )
            detail_lines.append(
                f"Terminal window {format_velocity_fps(preferred_min)}-{format_velocity_fps(preferred_max)}"
            )
        elif preferred_min is not None:
            projectile_bits.append(
                f"Terminal floor {format_velocity_fps(preferred_min)}"
            )
            detail_lines.append(f"Terminal floor {format_velocity_fps(preferred_min)}")
        projectile_line = " | ".join(projectile_bits)

    summary.update(
        {
            "title": str(profile.get("name") or "Load Card"),
            "subtitle": " | ".join(bit for bit in status_bits if bit),
            "component_line": " | ".join(component_bits),
            "measurement_line": " | ".join(measurement_bits),
            "status_line": str(evidence.get("evidence_label") or ""),
            "projectile_line": projectile_line,
            "detail_lines": detail_lines,
        }
    )
    return summary


def _normalize_source_label(source: str, context: dict[str, Any]) -> str:
    mismatch = bool(context.get("title_projectile_mismatch"))
    if source == "gordon_dump_import":
        return "Reference Import" if not mismatch else "Reference Import with Mismatch"
    if source == "gordon_grtrace_import":
        return "Pressure Trace"
    if source == "gordon_pressuretrace_import":
        return "Archive Reference"
    if source == "gordon_measurement_import":
        return "Measurement Series Archive"
    return "Hjemmelading"


def _build_status(
    predicted_velocity: float | None,
    measured_velocity: float | None,
    mismatch: bool,
    chrono_count: int,
) -> str:
    if mismatch:
        return "Source File Mismatch"
    if predicted_velocity is not None and measured_velocity is not None:
        return "Verified In-App"
    if predicted_velocity is not None and chrono_count:
        return "Has Reference + Chrono"
    if predicted_velocity is not None:
        return "Has Reference Data"
    if chrono_count:
        return "Has Chrono Data"
    return "Profile"


def _build_status_from_evidence(
    *,
    predicted_velocity: float | None,
    measured_velocity: float | None,
    mismatch: bool,
    evidence_summary: dict[str, Any],
) -> str:
    if mismatch:
        return "Source File Mismatch"
    pressure_count = int(evidence_summary.get("pressure_count") or 0)
    chrono_count = int(evidence_summary.get("chrono_count") or 0)
    accuracy_count = int(evidence_summary.get("accuracy_count") or 0)
    lot_level = str(evidence_summary.get("lot_level") or "unknown")
    if pressure_count:
        return "History Shows Risk"
    if lot_level == "warning":
        return "Lots Require Follow-Up"
    if (
        predicted_velocity is not None
        and measured_velocity is not None
        and accuracy_count
    ):
        return "Verified In-App"
    if lot_level == "ok" and (chrono_count or accuracy_count):
        return "Verified with Lot Knowledge"
    if predicted_velocity is not None and chrono_count:
        return "Has Reference + Chrono"
    if lot_level in {"ok", "info"} and not (chrono_count or accuracy_count):
        return str(evidence_summary.get("lot_title") or "Has Lot Knowledge")
    if chrono_count or accuracy_count:
        return "Has Measured Data"
    if predicted_velocity is not None:
        return "Has Reference Data"
    return "Profile"


def build_owned_reference_rows(db) -> list[dict[str, Any]]:
    profiles = db.execute_query(
        """
        SELECT
            ap.*,
            grt.predicted_velocity,
            grt.max_pressure_psi,
            grt.max_pressure_bar,
            grt.case_fill_percent,
            grt.predicted_accuracy_potential,
            grt.import_date,
            grt.notes AS grt_notes
        FROM ammo_profiles ap
        LEFT JOIN grt_data grt ON ap.id = grt.ammo_profile_id
        ORDER BY ap.name
        """
    )

    latest_chrono_rows = db.execute_query(
        """
        SELECT cs.*
        FROM chronograph_sessions cs
        JOIN (
            SELECT ammo_profile_id, MAX(id) AS max_id
            FROM chronograph_sessions
            WHERE ammo_profile_id IS NOT NULL
            GROUP BY ammo_profile_id
        ) latest
          ON latest.ammo_profile_id = cs.ammo_profile_id
         AND latest.max_id = cs.id
        """
    )
    chrono_by_profile = {
        row["ammo_profile_id"]: row
        for row in latest_chrono_rows
        if row.get("ammo_profile_id")
    }

    chrono_counts = {
        row["ammo_profile_id"]: row["count"]
        for row in db.execute_query(
            """
            SELECT ammo_profile_id, COUNT(*) AS count
            FROM chronograph_sessions
            WHERE ammo_profile_id IS NOT NULL
            GROUP BY ammo_profile_id
            """
        )
    }

    rows: list[dict[str, Any]] = []
    for profile in profiles or []:
        try:
            context = json.loads(profile.get("component_context_json") or "{}")
        except Exception:
            context = {}

        source = str(context.get("source") or "")
        has_reference_data = (
            profile.get("predicted_velocity") is not None
            or source.startswith("gordon_")
            or source.startswith("reference_")
        )
        if not has_reference_data:
            continue

        ammo_profile_id = profile["id"]
        latest_chrono = chrono_by_profile.get(ammo_profile_id) or {}
        measured_velocity = _safe_float(latest_chrono.get("avg_velocity_fps"))
        if measured_velocity is None:
            measured_velocity = _safe_float(profile.get("velocity_fps"))
        predicted_velocity = _safe_float(profile.get("predicted_velocity"))
        delta_velocity = None
        if predicted_velocity is not None and measured_velocity is not None:
            delta_velocity = round(measured_velocity - predicted_velocity, 1)

        mismatch = bool(context.get("title_projectile_mismatch"))
        chrono_count = int(chrono_counts.get(ammo_profile_id) or 0)
        evidence_summary = build_profile_evidence_summary(db, ammo_profile_id)
        rows.append(
            {
                "id": ammo_profile_id,
                "name": profile.get("name") or "",
                "source_label": _normalize_source_label(source, context),
                "source_kind": source or "internal",
                "predicted_velocity": predicted_velocity,
                "velocity_fps": measured_velocity,
                "latest_chrono_velocity_fps": _safe_float(
                    latest_chrono.get("avg_velocity_fps")
                ),
                "velocity_delta_fps": delta_velocity,
                "max_pressure_psi": _safe_float(profile.get("max_pressure_psi")),
                "max_pressure_bar": _safe_float(profile.get("max_pressure_bar")),
                "case_fill_percent": _safe_float(profile.get("case_fill_percent")),
                "predicted_accuracy_potential": profile.get(
                    "predicted_accuracy_potential"
                ),
                "import_date": profile.get("import_date"),
                "reference_notes": profile.get("grt_notes") or "",
                "grt_notes": profile.get("grt_notes") or "",
                "chrono_count": chrono_count,
                "latest_chrono_name": latest_chrono.get("session_name") or "",
                "status_label": _build_status_from_evidence(
                    predicted_velocity=predicted_velocity,
                    measured_velocity=measured_velocity,
                    mismatch=mismatch,
                    evidence_summary=evidence_summary,
                ),
                "has_source_mismatch": mismatch,
                "evidence_summary": evidence_summary,
            }
        )

    rows.sort(key=lambda row: (row["source_label"], row["name"]))
    return rows


def build_owned_gordon_rows(db) -> list[dict[str, Any]]:
    return build_owned_reference_rows(db)
