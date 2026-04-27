"""Batch workspace for load development history, notes, photos, and chrono data."""

from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QDate, QSettings, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from HjemmeladingApp.utils import units

from ..layers import component_layer

add_batch_attachment = component_layer.batch.add_batch_attachment
add_batch_note = component_layer.batch.add_batch_note
add_batch_session = component_layer.batch.add_batch_session
create_batch_project = component_layer.batch.create_batch_project
get_batch_attachments = component_layer.batch.get_batch_attachments
get_batch_notes = component_layer.batch.get_batch_notes
get_batch_project = component_layer.batch.get_batch_project
get_batch_sessions = component_layer.batch.get_batch_sessions
list_batch_projects = component_layer.batch.list_batch_projects
store_manual_chronograph_for_batch = (
    component_layer.batch.store_manual_chronograph_for_batch
)
update_batch_project = component_layer.batch.update_batch_project
from ..database.database import get_database
from ..tools.load_session_runtime_service import (
    build_active_workflow_context_from_settings,
    build_load_session_runtime,
    refresh_load_session_measurement_summary,
)
from ..utils.barrel_configuration import resolve_active_barrel_configuration_context
from ..utils.chronograph_import import import_chronograph_csv
from ..utils.i18n import tr
from .batch_analyzer import BatchAnalyzer


def _compute_chrono_stats_from_db(
    db: Any, sessions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compute combined chrono velocity stats from DB for a list of batch sessions.

    This is the headless equivalent of BatchWorkspace._combined_chronograph_stats().
    It can be called outside the UI context (e.g., from chrono importer or target analyzer).
    """
    import_ids = [
        session.get("chronograph_import_id")
        for session in sessions
        if session.get("chronograph_import_id")
    ]
    if not import_ids:
        return {}
    velocities: List[float] = []
    for import_id in import_ids:
        rows = db.execute_query(
            "SELECT * FROM chronograph_imports WHERE id = ?",
            (import_id,),
        )
        if not rows:
            continue
        raw = rows[0].get("velocities_json") or "[]"
        try:
            velocities.extend(float(v) for v in json.loads(raw))
        except Exception:
            continue
    if not velocities:
        return {}
    avg = statistics.mean(velocities)
    return {
        "count": len(velocities),
        "avg": avg,
        "es": max(velocities) - min(velocities),
        "sd": statistics.stdev(velocities) if len(velocities) > 1 else 0.0,
        "min": min(velocities),
        "max": max(velocities),
    }


def recompute_batch_analysis_from_db(db: Any, batch_id: Any) -> Dict[str, Any] | None:
    """Recompute batch analysis from DB rows and persist to batch_projects.analysis_json.

    Call this after any measurement save (chrono import, target result, batch session)
    to keep the batch's spread_signal_hint and analysis up to date without requiring
    the BatchWorkspace UI to be open.

    Returns the saved analysis dict, or None on failure.
    """
    try:
        resolved_id = int(batch_id)
    except (TypeError, ValueError):
        return None
    try:
        batch = get_batch_project(db, resolved_id)
    except Exception:
        return None
    if not isinstance(batch, dict):
        return None
    sessions: List[Dict[str, Any]] = []
    notes: List[Dict[str, Any]] = []
    attachments: List[Dict[str, Any]] = []
    try:
        sessions = list(get_batch_sessions(db, resolved_id) or [])
    except Exception:
        pass
    try:
        notes = list(get_batch_notes(db, resolved_id) or [])
    except Exception:
        pass
    try:
        attachments = list(get_batch_attachments(db, resolved_id) or [])
    except Exception:
        pass
    chrono_stats = _compute_chrono_stats_from_db(db, sessions)
    # Enrich each batch session with the per-session signal_hint computed by the
    # engine (stored in load_development_sessions.evidence_summary_json). The
    # BatchAnalyzer reads these to avoid re-computing an independent signal from
    # raw batch data when the engine has already resolved the per-session hint.
    for session in sessions:
        load_session_id = session.get("load_session_id")
        if not load_session_id:
            continue
        try:
            rows = db.execute_query(
                "SELECT evidence_summary_json FROM load_development_sessions WHERE id = ?",
                (load_session_id,),
            )
            if rows:
                raw = rows[0].get("evidence_summary_json") or "{}"
                hint = json.loads(raw).get("signal_hint") or ""
                session["_signal_hint"] = hint
        except Exception:
            pass
    engine_result = _get_batch_engine_result(db, batch)
    analyzer = BatchAnalyzer(
        batch,
        sessions=sessions,
        notes=notes,
        attachments=attachments,
        chronograph_stats=chrono_stats,
        engine_result=engine_result,
    )
    try:
        recommendation = analyzer.recommend_next()
    except Exception:
        return None
    try:
        update_batch_project(db, resolved_id, {"analysis_json": recommendation})
    except Exception:
        return None
    return recommendation


def _safe_filename(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return name.strip("._") or "attachment"


def _project_name_from_path(path: str) -> str:
    cleaned = (path or "").strip().rstrip("\\/")
    if not cleaned:
        return "Standard Project"
    return Path(cleaned).name or cleaned


def _get_workspace_project_context() -> dict[str, str]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    project_path = str(settings.value("workspace/current_project", "") or "").strip()
    return {
        "project_path": project_path,
        "project_name": _project_name_from_path(project_path),
    }


def _get_global_unit_system() -> str:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return str(settings.value("units/global", "metric") or "metric").strip().lower()


def _format_distance_m(distance_m: object) -> str:
    try:
        value = float(distance_m)
    except Exception:
        return str(distance_m) if distance_m not in (None, "") else "-"
    if _get_global_unit_system() == "imperial":
        return f"{units.meters_to_yards(value):.0f} yd ({value:.0f} m)"
    return f"{value:.0f} m"


def _format_group_mm(group_mm: object) -> str:
    try:
        value = float(group_mm)
    except Exception:
        return str(group_mm) if group_mm not in (None, "") else "-"
    if _get_global_unit_system() == "imperial":
        return f"{units.mm_to_inches(value):.2f} in ({value:.1f} mm)"
    return f"{value:.1f} mm"


def _format_batch_setup_label(batch: dict[str, Any] | None) -> str:
    batch_data = batch or {}
    barrel_name = str(batch_data.get("barrel_name") or "").strip()
    configuration_name = str(batch_data.get("barrel_configuration_name") or "").strip()
    if (
        configuration_name
        and barrel_name
        and configuration_name.casefold() != barrel_name.casefold()
    ):
        return f"{barrel_name} / {configuration_name}"
    return configuration_name or barrel_name


def _get_active_workflow_context() -> dict[str, object]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    try:
        database = get_database()
    except Exception:
        database = None
    return build_active_workflow_context_from_settings(settings, database)


def _get_active_batch_focus() -> dict[str, str]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    focus = str(settings.value("workflow_context/batch_focus", "") or "").strip()
    reason = str(
        settings.value("workflow_context/batch_focus_reason", "") or ""
    ).strip()
    if not focus and not reason:
        return {}
    return {"focus": focus, "reason": reason}


def _get_active_workflow_verification_advisory(db) -> dict[str, str]:
    workflow_context = _get_active_workflow_context()
    workflow_id = workflow_context.get("workflow_id")
    if not db or workflow_id in (None, ""):
        return {}
    try:
        workflow = db.get_by_id("load_development_workflows", int(workflow_id))
    except Exception:
        return {}
    if not workflow:
        return {}
    try:
        module = importlib.import_module("src.modules.load_development_workflow")
        builder = getattr(
            module, "build_workflow_component_verification_advisory", None
        )
        if not callable(builder):
            return {}
        advisory = builder(db, workflow)
        return {
            "title": str(advisory.get("title", "") or "").strip(),
            "message": str(advisory.get("message", "") or "").strip(),
            "level": str(advisory.get("level", "") or "").strip(),
            "checks": [
                str(item).strip()
                for item in (advisory.get("checks") or [])
                if str(item).strip()
            ],
        }
    except Exception:
        return {}


def _format_workflow_verification_guidance(advisory: dict[str, object]) -> str:
    title = str(advisory.get("title", "") or "").strip()
    message = str(advisory.get("message", "") or "").strip()
    checks = [
        str(item).strip()
        for item in (advisory.get("checks") or [])
        if str(item).strip()
    ]
    if not title and not message and not checks:
        return ""

    parts = []
    if title:
        parts.append(title)
    if message:
        parts.append(message)
    if checks:
        parts.append(tr("bw_recommended_check_setup"))
        parts.extend(f"- {item}" for item in checks)
    return "\n".join(parts).strip()


def _parse_analysis_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _derive_suppressor_used(value: object) -> bool | None:
    text = str(value or "").strip().lower()
    if not text or text == "none":
        return None
    return any(
        token in text for token in ("suppressor", "moderator", "demper", "silencer")
    )


def _format_component_context_summary(
    snapshot: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> str:
    snapshot_data = snapshot or {}
    analysis_data = analysis or {}
    context = {}
    if isinstance(snapshot_data.get("component_context"), dict):
        context = dict(snapshot_data.get("component_context") or {})
    elif isinstance(analysis_data.get("component_context"), dict):
        context = dict(analysis_data.get("component_context") or {})

    summary_html = str(context.get("summary_html") or "").strip()
    if summary_html:
        return re.sub(r"<br\s*/?>", " | ", summary_html).strip()

    lines: list[str] = []
    for key in ("bullet", "powder", "primer"):
        entry = context.get(key) or {}
        if not isinstance(entry, dict) or not entry:
            continue
        name = str(entry.get("name") or key).strip()
        lot = str(entry.get("lot_number") or "").strip()
        line = f"{key}: {name}"
        if lot:
            line += f" | lot {lot}"
        if key == "bullet" and entry.get("uses_measured_lot_stats"):
            line += " | measured lot average"
        learning = str(entry.get("lot_learning_title") or "").strip()
        if learning:
            line += f" | {learning}"
        lines.append(line)
    return " | ".join(lines).strip()


def _build_retest_session_prefill(
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    analysis_data = analysis or {}
    retest = analysis_data.get("retest_advisory") or {}
    if not isinstance(retest, dict) or not retest:
        return {}

    profile = str(retest.get("usage_profile") or "").strip()
    if profile.startswith("hunting"):
        session_name = "Retest - cold bore and hunting verification"
    elif profile in {"precision", "long_range_hunting"}:
        session_name = "Retest - chrono and precision verification"
    elif profile == "training":
        session_name = "Retest - robustness check"
    else:
        session_name = "Retest - verification series"

    try:
        shot_count = max(1, int(float(retest.get("suggested_control_shots") or 5)))
    except Exception:
        shot_count = 5

    protocol_steps = [
        str(step).strip()
        for step in (retest.get("protocol_steps") or [])
        if str(step).strip()
    ]
    focus = str(retest.get("focus") or "").strip()
    notes_parts: list[str] = []
    if focus:
        notes_parts.append(f"Fokus: {focus}")
    if protocol_steps:
        notes_parts.append("Setup:")
        notes_parts.extend(f"- {step}" for step in protocol_steps[:4])

    return {
        "session_name": session_name,
        "distance_m": 100,
        "shot_count": shot_count,
        "notes": "\n".join(notes_parts).strip(),
    }


def _build_subsonic_batch_hint(analysis: dict[str, Any] | None) -> str:
    analysis_data = analysis or {}
    subsonic = analysis_data.get("subsonic_context") or {}
    if not isinstance(subsonic, dict) or not subsonic.get("enabled"):
        return ""
    advisory = subsonic.get("advisory") or {}
    target = subsonic.get("target_velocity_fps")
    bits: list[str] = []
    if target not in (None, ""):
        try:
            bits.append(f"Subsonic mode active ({float(target):.0f} fps target).")
        except Exception:
            bits.append("Subsonic mode active.")
    else:
        bits.append("Subsonic mode active.")
    title = str(advisory.get("title") or "").strip()
    if title:
        bits.append(title)
    message = str(advisory.get("message") or "").strip()
    if message:
        bits.append(message)
    return " ".join(bits).strip()


def _format_subsonic_session_observations(analysis: dict[str, Any] | None) -> str:
    analysis_data = analysis or {}
    observations = analysis_data.get("subsonic_observations") or {}
    if not isinstance(observations, dict) or not observations:
        return ""

    parts: list[str] = []
    if observations.get("cycling_status"):
        parts.append(f"cycle={observations['cycling_status']}")
    if observations.get("sonic_crack"):
        parts.append("sonic crack")
    if observations.get("keyhole"):
        parts.append("keyhole")
    if observations.get("suppressor_used"):
        parts.append("suppressor")
    return ", ".join(parts).strip()


def _extract_batch_session_primer_review(
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    analysis_data = analysis or {}
    review = analysis_data.get("primer_image_review") or {}
    return dict(review) if isinstance(review, dict) else {}


def _extract_batch_session_primer_images(
    analysis: dict[str, Any] | None,
) -> list[str]:
    review = _extract_batch_session_primer_review(analysis)
    raw_images = review.get("images")
    images = [str(item).strip() for item in (raw_images or []) if str(item).strip()]
    if images:
        return images
    fallback = str(review.get("path") or review.get("primary_path") or "").strip()
    return [fallback] if fallback else []


def _format_batch_session_primer_summary(analysis: dict[str, Any] | None) -> str:
    review = _extract_batch_session_primer_review(analysis)
    if review.get("enabled") is False:
        return "primer review disabled for this session"
    images = _extract_batch_session_primer_images(analysis)
    observation = str(review.get("observation") or "").strip()
    image_count = len(images)
    if image_count == 0 and not observation:
        return ""
    count_text = f" ({image_count} images)" if image_count > 1 else ""
    if observation:
        return f"primer review{count_text}: {observation}"
    return f"primer review logged{count_text}"


def _build_batch_session_primer_payload(
    batch: dict[str, Any] | None,
    workflow_context: dict[str, Any] | None,
    *,
    batch_session_id: int | None,
    session_name: str | None,
    session_date: str,
    primer_review_enabled: bool,
    primer_image_paths: list[str] | None,
    primer_image_quality: str | None,
    primer_image_observation: str | None,
    primer_image_confidence: str | None,
) -> dict[str, Any]:
    batch_data = batch or {}
    workflow = workflow_context or {}
    image_paths = [
        str(item).strip() for item in (primer_image_paths or []) if str(item).strip()
    ]
    image_path = image_paths[0] if image_paths else ""
    observation = str(primer_image_observation or "").strip()
    if not primer_review_enabled:
        return {}
    if not image_path and not observation:
        return {}

    ammo_profile_id = batch_data.get("ammo_profile_id")
    if ammo_profile_id in (None, ""):
        return {}

    session_label = (
        session_name
        or str(
            batch_data.get("batch_name")
            or batch_data.get("batch_number")
            or session_date
        ).strip()
    )
    image_count = len(image_paths)
    if observation:
        note = observation
        if image_count > 1:
            note = f"{observation} ({image_count} primer images in this reference set)"
    else:
        note = f"Primer baseline reference from batch session {session_label}."
        if image_count > 1:
            note = f"Primer baseline reference set ({image_count} images) from batch session {session_label}."
    load_session_id = batch_data.get("load_session_id")
    if load_session_id in (None, ""):
        load_session_id = workflow.get("load_session_id")

    return {
        "ammo_profile_id": int(ammo_profile_id),
        "charge_weight": batch_data.get("charge_weight_grains"),
        "notes": note,
        "date": session_date,
        "primer_image_path": image_path or None,
        "primer_image_quality": str(primer_image_quality or "").strip() or None,
        "primer_image_observation": observation or None,
        "primer_image_confidence": str(primer_image_confidence or "").strip() or None,
        "workflow_id": workflow.get("workflow_id"),
        "load_session_id": load_session_id,
        "session_name": session_label,
        "batch_id": batch_data.get("id"),
        "batch_session_id": batch_session_id,
        "rifle_id": batch_data.get("rifle_id"),
    }


def _save_batch_session_primer_payload(db, payload: dict[str, Any]) -> None:
    if not payload:
        return
    cur = db.cursor
    cur.execute(
        """
        INSERT INTO pressure_signs (
            ammo_profile_id, charge_weight, flat_primer, primer_crater,
            ejector_mark, extractor_mark, heavy_bolt_lift, case_head_expansion,
            velocity_spike, pressure_score, severity_level, notes, date,
            primer_image_path, primer_image_quality, primer_image_observation,
            primer_image_confidence, workflow_id, load_session_id, session_name,
            batch_id, batch_session_id, rifle_id
        ) VALUES (?, ?, 0, 0, 0, 0, 0, NULL, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.get("ammo_profile_id"),
            payload.get("charge_weight"),
            "LAV",
            payload.get("notes"),
            payload.get("date"),
            payload.get("primer_image_path"),
            payload.get("primer_image_quality"),
            payload.get("primer_image_observation"),
            payload.get("primer_image_confidence"),
            payload.get("workflow_id"),
            payload.get("load_session_id"),
            payload.get("session_name"),
            payload.get("batch_id"),
            payload.get("batch_session_id"),
            payload.get("rifle_id"),
        ),
    )
    db.conn.commit()


def _copy_batch_session_primer_image(
    media_dir: Path | None,
    source_path: str,
    *,
    session_name: str | None,
    session_date: str,
) -> str:
    src = Path(source_path)
    if not src.exists() or media_dir is None:
        raise FileNotFoundError(source_path)

    primer_dir = media_dir / "primer_reviews"
    primer_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_filename(session_name or src.stem or f"primer-{session_date}")
    dest_name = f"{stem}_{datetime.now().strftime('%Y%m%d-%H%M%S')}{src.suffix}"
    dest_path = primer_dir / dest_name
    shutil.copy2(src, dest_path)
    return str(dest_path)


def _parse_batch_session_primer_sources(value: str | None) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip() for item in text.split(" | ") if item.strip()]


def _format_model_match_summary(analysis: dict[str, Any] | None) -> str:
    analysis_data = analysis or {}
    advisory = analysis_data.get("model_match_advisory") or {}
    if not isinstance(advisory, dict) or not advisory:
        return ""

    title = str(advisory.get("title") or "").strip()
    message = str(advisory.get("message") or "").strip()
    checks = advisory.get("checks") or []
    lead = f"{title}: {message}".strip(": ").strip()
    if not lead:
        lead = message
    bias_direction = str(advisory.get("bias_direction") or "").strip().lower()
    bias_fps = advisory.get("bias_fps")
    bias_text = ""
    if isinstance(bias_fps, (int, float)):
        if bias_direction == "model_higher":
            bias_text = f"bias approx. {abs(float(bias_fps)):.0f} fps high"
        elif bias_direction == "measured_higher":
            bias_text = f"bias approx. {abs(float(bias_fps)):.0f} fps low"
        elif bias_direction == "neutral":
            bias_text = "no clear bias"
    if checks:
        details = [str(checks[0]).strip()]
        if bias_text:
            details.append(bias_text)
        return f"{lead} ({' | '.join(details)})".strip()
    if bias_text:
        return f"{lead} ({bias_text})".strip()
    return lead


def _format_batch_comparison_workboard_summary(workboard: dict[str, Any] | None) -> str:
    board = workboard or {}
    if not board:
        return ""

    status = str(board.get("status_label") or "").strip()
    first_batch = str(board.get("first_batch_name") or "").strip()
    bucket = str(board.get("primary_bucket") or "").strip()
    hold_back = str(board.get("hold_back") or "").strip()
    parts: list[str] = []
    if status:
        parts.append(status)
    if first_batch:
        parts.append(f"run {first_batch} first")
    if bucket:
        parts.append(f"bucket {bucket}")
    if hold_back:
        parts.append(f"hold back {hold_back}")
    return " | ".join(parts).strip()


def _build_batch_comparison_workboard_lane_map(
    workboard: dict[str, Any] | None,
) -> dict[str, str]:
    board = workboard or {}
    lanes = (
        board.get("lane_summaries")
        if isinstance(board.get("lane_summaries"), list)
        else []
    )
    lane_map = {
        "shoot_now": "-",
        "confirm": "-",
        "hold": "-",
        "pause": "-",
        "reject_watch": "-",
    }
    for item in lanes:
        if not isinstance(item, dict):
            continue
        bucket = str(item.get("bucket") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if bucket in lane_map and summary:
            lane_map[bucket] = summary
    return lane_map


def _build_batch_comparison_workboard_display(
    workboard: dict[str, Any] | None,
) -> dict[str, str]:
    board = workboard or {}
    lane_map = _build_batch_comparison_workboard_lane_map(board)
    status = str(board.get("status_label") or "").strip() or "-"
    summary = str(board.get("summary") or "").strip() or "-"
    first_batch = str(board.get("first_batch_name") or "").strip() or "-"
    action = str(board.get("primary_action") or "").strip() or "-"
    hold_back = str(board.get("hold_back") or "").strip() or "-"
    queue_preview = (
        board.get("queue_preview")
        if isinstance(board.get("queue_preview"), list)
        else []
    )
    counts = board.get("counts") if isinstance(board.get("counts"), dict) else {}
    today_summary = f"{status} | {summary}".strip(" |")
    queue_text = (
        " | ".join(str(item).strip() for item in queue_preview[:3] if str(item).strip())
        or "-"
    )
    counts_text = (
        " | ".join(
            f"{name} {int(value)}"
            for name, value in (
                ("shoot_now", counts.get("shoot_now") or 0),
                ("confirm", counts.get("confirm") or 0),
                ("hold", counts.get("hold") or 0),
                ("pause", counts.get("pause") or 0),
                ("reject_watch", counts.get("reject_watch") or 0),
            )
            if int(value) > 0
        )
        or "-"
    )
    lanes_summary = (
        " | ".join(
            value
            for value in (
                lane_map.get("shoot_now", "-"),
                lane_map.get("confirm", "-"),
                lane_map.get("hold", "-"),
                lane_map.get("pause", "-"),
                lane_map.get("reject_watch", "-"),
            )
            if value and value != "-"
        )
        or "-"
    )
    bucket = str(board.get("primary_bucket") or "").strip().lower()
    primary_lane_text = lane_map.get(bucket, "-") if bucket in lane_map else "-"
    if primary_lane_text == "-" and bucket and first_batch != "-":
        primary_lane_text = f"{bucket}: {first_batch}"
    board_hint = action
    if primary_lane_text != "-" and action != "-":
        board_hint = f"{primary_lane_text} | {action}"
    elif primary_lane_text != "-":
        board_hint = primary_lane_text
    elif action == "-":
        board_hint = "-"
    if "watch" in status.lower() or bucket == "reject_watch":
        tone = "watch"
    elif bucket == "confirm":
        tone = "confirm"
    elif bucket == "shoot_now":
        tone = "ready"
    else:
        tone = "neutral"
    return {
        "status": status,
        "summary": summary,
        "today_summary": today_summary,
        "counts_text": counts_text,
        "lanes_summary": lanes_summary,
        "primary_lane_text": primary_lane_text,
        "board_hint": board_hint,
        "first_batch": first_batch,
        "action": action,
        "hold_back": hold_back,
        "queue_text": queue_text,
        "tone": tone,
        "shoot_now": lane_map.get("shoot_now", "-"),
        "confirm": lane_map.get("confirm", "-"),
        "hold": lane_map.get("hold", "-"),
        "pause": lane_map.get("pause", "-"),
        "reject_watch": lane_map.get("reject_watch", "-"),
    }


def _build_batch_comparison_workboard_copy_text(
    display: dict[str, str] | None,
    *,
    mode: str = "today",
) -> str:
    view = display or {}
    if mode == "queue":
        parts = [
            str(view.get("counts_text") or "").strip(),
            str(view.get("queue_text") or "").strip(),
            str(view.get("lanes_summary") or "").strip(),
        ]
    elif mode == "full":
        parts = [
            str(view.get("status") or "").strip(),
            str(view.get("summary") or "").strip(),
            str(view.get("today_summary") or "").strip(),
            str(view.get("counts_text") or "").strip(),
            str(view.get("primary_lane_text") or "").strip(),
            str(view.get("board_hint") or "").strip(),
            str(view.get("action") or "").strip(),
            str(view.get("queue_text") or "").strip(),
            str(view.get("lanes_summary") or "").strip(),
            str(view.get("hold_back") or "").strip(),
        ]
    else:
        parts = [
            str(view.get("status") or "").strip(),
            str(view.get("today_summary") or "").strip(),
            str(view.get("primary_lane_text") or "").strip(),
            str(view.get("action") or "").strip(),
            str(view.get("hold_back") or "").strip(),
        ]
    return "\n".join(part for part in parts if part and part != "-") or "-"


def _get_batch_engine_result(
    database: Any,
    batch: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return the raw engine_result dict for a batch's linked load session, or {}."""
    batch_data = batch or {}
    load_session_id = batch_data.get("load_session_id")
    try:
        resolved_session_id = int(load_session_id)
    except Exception:
        return {}
    try:
        runtime = build_load_session_runtime(database, resolved_session_id)
    except Exception:
        return {}
    if not isinstance(runtime, dict):
        return {}
    smart_engine = (
        runtime.get("smart_engine")
        if isinstance(runtime.get("smart_engine"), dict)
        else {}
    )
    return (
        smart_engine.get("engine_result")
        if isinstance(smart_engine.get("engine_result"), dict)
        else {}
    )


def _get_batch_smart_engine_summary(
    database: Any,
    batch: dict[str, Any] | None,
) -> dict[str, str]:
    batch_data = batch or {}
    load_session_id = batch_data.get("load_session_id")
    try:
        resolved_session_id = int(load_session_id)
    except Exception:
        return {}
    try:
        runtime = build_load_session_runtime(database, resolved_session_id)
    except Exception:
        return {}
    if not isinstance(runtime, dict):
        return {}
    smart_engine = (
        runtime.get("smart_engine")
        if isinstance(runtime.get("smart_engine"), dict)
        else {}
    )
    engine_result = (
        smart_engine.get("engine_result")
        if isinstance(smart_engine.get("engine_result"), dict)
        else {}
    )
    candidate_profile = (
        engine_result.get("candidate_profile")
        if isinstance(engine_result.get("candidate_profile"), dict)
        else {}
    )
    baseline_control = (
        engine_result.get("baseline_control")
        if isinstance(engine_result.get("baseline_control"), dict)
        else {}
    )
    branch_advisory = (
        engine_result.get("branch_advisory")
        if isinstance(engine_result.get("branch_advisory"), dict)
        else {}
    )
    baseline_diagnostics = (
        engine_result.get("baseline_diagnostics")
        if isinstance(engine_result.get("baseline_diagnostics"), dict)
        else {}
    )
    evidence_diagnostics = (
        engine_result.get("evidence_diagnostics")
        if isinstance(engine_result.get("evidence_diagnostics"), dict)
        else {}
    )
    decisions = (
        engine_result.get("decisions")
        if isinstance(engine_result.get("decisions"), dict)
        else {}
    )
    bullet_fit = (
        engine_result.get("bullet_fit")
        if isinstance(engine_result.get("bullet_fit"), dict)
        else {}
    )
    chamber_jump = (
        engine_result.get("chamber_jump")
        if isinstance(engine_result.get("chamber_jump"), dict)
        else {}
    )
    next_test = (
        decisions.get("next_test")
        if isinstance(decisions.get("next_test"), dict)
        else {}
    )
    validation_gate = (
        decisions.get("validation_gate")
        if isinstance(decisions.get("validation_gate"), dict)
        else {}
    )
    execution_plan = (
        decisions.get("execution_plan")
        if isinstance(decisions.get("execution_plan"), dict)
        else {}
    )
    do_not_change_yet = (
        decisions.get("do_not_change_yet")
        if isinstance(decisions.get("do_not_change_yet"), list)
        else []
    )
    blocked_by = (
        decisions.get("blocked_by")
        if isinstance(decisions.get("blocked_by"), list)
        else []
    )
    recommendation_confidence = (
        decisions.get("recommendation_confidence")
        if isinstance(decisions.get("recommendation_confidence"), dict)
        else {}
    )
    harmonics = (
        engine_result.get("harmonics")
        if isinstance(engine_result.get("harmonics"), dict)
        else {}
    )
    safety = (
        engine_result.get("safety")
        if isinstance(engine_result.get("safety"), dict)
        else {}
    )

    robustness = str(candidate_profile.get("robustness_level") or "").strip()
    node_fit = str(candidate_profile.get("node_fit") or "").strip()
    harmonics_tier = str(harmonics.get("stability_tier") or "").strip()
    next_action = str(next_test.get("recommended_action") or "").strip()
    next_reason = str(next_test.get("why") or "").strip()
    safety_state = str(safety.get("state") or "").strip()
    blocked = bool(safety.get("blocked"))
    gate_label = str(validation_gate.get("label") or "").strip()
    gate_next = str(validation_gate.get("next_gate") or "").strip()
    plan_summary = str(execution_plan.get("summary") or "").strip()
    plan_keep_constant = (
        execution_plan.get("keep_constant")
        if isinstance(execution_plan.get("keep_constant"), list)
        else []
    )
    first_keep_constant = next(
        (str(item).strip() for item in plan_keep_constant if str(item).strip()), ""
    )
    first_hold = next(
        (str(item).strip() for item in do_not_change_yet if str(item).strip()), ""
    )
    first_block = next(
        (
            str(item.get("title") or item.get("kind") or "").strip()
            for item in blocked_by
            if isinstance(item, dict)
            and str(item.get("title") or item.get("kind") or "").strip()
        ),
        "",
    )
    confidence_level = str(recommendation_confidence.get("level") or "").strip()
    confidence_score = recommendation_confidence.get("score")
    confidence_summary = str(recommendation_confidence.get("summary") or "").strip()
    charge_alignment = str(baseline_control.get("charge_alignment") or "").strip()
    charge_target = str(baseline_control.get("charge_target_label") or "").strip()
    seating_alignment = str(baseline_control.get("seating_alignment") or "").strip()
    seating_target = str(baseline_control.get("seating_target_label") or "").strip()
    active_return_line = str(baseline_control.get("active_return_line") or "").strip()
    charge_return_line = str(baseline_control.get("charge_return_line") or "").strip()
    seating_return_line = str(baseline_control.get("seating_return_line") or "").strip()
    branch_label = str(branch_advisory.get("label") or "").strip()
    branch_compare_mode = str(branch_advisory.get("compare_mode") or "").strip()
    branch_display_line = str(branch_advisory.get("display_line") or "").strip()
    baseline_status = str(baseline_diagnostics.get("status") or "").strip()
    baseline_items = (
        baseline_diagnostics.get("items")
        if isinstance(baseline_diagnostics.get("items"), list)
        else []
    )
    first_baseline_item = next(
        (str(item).strip() for item in baseline_items if str(item).strip()), ""
    )
    evidence_status = str(evidence_diagnostics.get("status") or "").strip()
    evidence_items = (
        evidence_diagnostics.get("items")
        if isinstance(evidence_diagnostics.get("items"), list)
        else []
    )
    first_evidence_item = next(
        (str(item).strip() for item in evidence_items if str(item).strip()), ""
    )
    bullet_fit_level = str(bullet_fit.get("level") or "").strip()
    bullet_fit_message = str(bullet_fit.get("message") or "").strip()
    jump_summary = str(chamber_jump.get("summary") or "").strip()
    if not branch_label:
        if charge_alignment == "outside" or seating_alignment == "outside":
            branch_label = "Custom branch"
            branch_compare_mode = branch_compare_mode or "return_before_compare"
        elif charge_alignment == "aligned" or seating_alignment == "aligned":
            branch_label = "Frozen baseline"
            branch_compare_mode = branch_compare_mode or "same_branch"

    parts: list[str] = []
    if robustness:
        parts.append(f"robustness {robustness}")
    if node_fit:
        parts.append(f"node fit {node_fit}")
    if harmonics_tier:
        parts.append(f"harmonics {harmonics_tier}")
    summary = ""
    if parts:
        summary = "Smart engine: " + ", ".join(parts)
        if blocked and safety_state:
            summary += f" | safety {safety_state}"
    next_line = ""
    if next_action:
        next_line = f"Smart engine next: {next_action}"
        if next_reason:
            next_line += f" - {next_reason}"
    gate_line = ""
    if gate_label:
        gate_line = f"Smart engine gate: {gate_label}"
        if gate_next:
            gate_line += f" - {gate_next}"
    protocol_line = ""
    if plan_summary:
        protocol_line = f"Smart engine protocol: {plan_summary}"
        if first_keep_constant:
            protocol_line += f" Keep constant: {first_keep_constant}"
    hold_line = f"Smart engine hold: {first_hold}" if first_hold else ""
    blocker_line = f"Smart engine blocker: {first_block}" if first_block else ""
    confidence_line = ""
    if confidence_level:
        confidence_line = f"Smart engine confidence: {confidence_level}"
        if isinstance(confidence_score, (int, float)):
            confidence_line += f" ({float(confidence_score):.1f}/100)"
        if confidence_summary:
            confidence_line += f" - {confidence_summary}"
    evidence_line = ""
    if evidence_status:
        evidence_line = f"Smart engine evidence: {evidence_status}"
        if first_evidence_item:
            evidence_line += f" - {first_evidence_item}"
    bullet_fit_line = ""
    if bullet_fit_level:
        bullet_fit_line = f"Smart engine bullet fit: {bullet_fit_level}"
        if bullet_fit_message:
            bullet_fit_line += f" - {bullet_fit_message}"
    jump_line = f"Smart engine jump: {jump_summary}" if jump_summary else ""
    baseline_line = ""
    if active_return_line:
        baseline_line = f"Smart engine baseline: {active_return_line}"
    elif first_baseline_item:
        baseline_line = f"Smart engine baseline: {first_baseline_item}"
    else:
        baseline_parts: list[str] = []
        if charge_return_line:
            baseline_parts.append(charge_return_line)
        elif charge_alignment == "outside" and charge_target:
            baseline_parts.append(f"charge -> {charge_target}")
        if seating_return_line:
            baseline_parts.append(seating_return_line)
        elif seating_alignment == "outside" and seating_target:
            baseline_parts.append(f"seating -> {seating_target}")
        if baseline_parts:
            baseline_line = "Smart engine baseline: " + " | ".join(baseline_parts)
    branch_line = ""
    if branch_display_line:
        branch_line = f"Smart engine branch: {branch_display_line}"
    elif branch_label:
        branch_line = f"Smart engine branch: {branch_label}"
        if branch_compare_mode:
            branch_line += f" ({branch_compare_mode})"
    return {
        "summary": summary,
        "next": next_line,
        "gate": gate_line,
        "protocol": protocol_line,
        "hold": hold_line,
        "blocker": blocker_line,
        "confidence": confidence_line,
        "evidence": evidence_line,
        "bullet_fit": bullet_fit_line,
        "jump": jump_line,
        "baseline": baseline_line,
        "branch": branch_line,
        "robustness": robustness,
        "node_fit": node_fit,
        "harmonics_tier": harmonics_tier,
        "next_action": next_action,
        "next_reason": next_reason,
        "safety_state": safety_state,
        "baseline_status": baseline_status,
        "evidence_status": evidence_status,
    }


def _build_batch_comparison_lane_title(
    lane_name: str,
    count: int,
    *,
    completed: bool = False,
    selected: bool = False,
) -> str:
    title = f"{lane_name} ({count})" if count > 0 else lane_name
    badges: list[str] = []
    if selected:
        badges.append("focused")
    if completed:
        badges.append("done")
    if badges:
        title += " [" + ", ".join(badges) + "]"
    return title


def _load_workboard_lane_ui_state(batch_id: int | None) -> tuple[set[str], str]:
    if batch_id in (None, ""):
        return set(), ""
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    completed_raw = str(
        settings.value(f"batch_workspace/workboard/{int(batch_id)}/completed", "") or ""
    ).strip()
    selected_lane = str(
        settings.value(f"batch_workspace/workboard/{int(batch_id)}/selected", "") or ""
    ).strip()
    completed = {
        token.strip()
        for token in completed_raw.split(",")
        if token.strip() in {"shoot_now", "confirm", "hold", "pause", "reject_watch"}
    }
    if selected_lane not in {"shoot_now", "confirm", "hold", "pause", "reject_watch"}:
        selected_lane = ""
    return completed, selected_lane


def _store_workboard_lane_ui_state(
    batch_id: int | None,
    completed: set[str] | None,
    selected_lane: str | None,
) -> None:
    if batch_id in (None, ""):
        return
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    valid_lanes = {"shoot_now", "confirm", "hold", "pause", "reject_watch"}
    completed_text = ",".join(
        sorted(lane for lane in (completed or set()) if lane in valid_lanes)
    )
    selected_value = selected_lane if selected_lane in valid_lanes else ""
    settings.setValue(
        f"batch_workspace/workboard/{int(batch_id)}/completed", completed_text
    )
    settings.setValue(
        f"batch_workspace/workboard/{int(batch_id)}/selected", selected_value
    )
    settings.sync()


def _build_direct_model_match_summary(
    analysis: dict[str, Any] | None,
    chrono_stats: dict[str, Any] | None,
) -> dict[str, str]:
    analysis_data = analysis or {}
    predicted = analysis_data.get("predicted_result_summary") or {}
    chrono = chrono_stats or {}
    try:
        predicted_velocity = float(predicted.get("muzzle_velocity_fps"))
        measured_velocity = float(
            chrono.get("avg_velocity_fps")
            if chrono.get("avg_velocity_fps") is not None
            else chrono.get("avg")
        )
    except Exception:
        return {"title": "", "message": ""}

    delta = abs(measured_velocity - predicted_velocity)
    if delta <= 15.0:
        title = "Direct model match is good"
        message = (
            f"The batch's measured chrono average ({measured_velocity:.0f} fps) is close to "
            f"the saved prediction ({predicted_velocity:.0f} fps), delta about {delta:.0f} fps."
        )
    elif delta <= 30.0:
        title = "Direct model match is acceptable"
        message = (
            f"The batch's measured chrono average ({measured_velocity:.0f} fps) deviates noticeably from "
            f"the saved prediction ({predicted_velocity:.0f} fps), delta about {delta:.0f} fps."
        )
    else:
        title = "Direct model match is weak"
        message = (
            f"The batch's measured chrono average ({measured_velocity:.0f} fps) is far from "
            f"the saved prediction ({predicted_velocity:.0f} fps), delta about {delta:.0f} fps."
        )
    return {"title": title, "message": message}


def _build_direct_model_match_advisory(
    analysis: dict[str, Any] | None,
    chrono_stats: dict[str, Any] | None,
) -> dict[str, Any]:
    analysis_data = analysis or {}
    predicted = analysis_data.get("predicted_result_summary") or {}
    chrono = chrono_stats or {}
    try:
        predicted_velocity = float(predicted.get("muzzle_velocity_fps"))
        measured_velocity = float(
            chrono.get("avg_velocity_fps")
            if chrono.get("avg_velocity_fps") is not None
            else chrono.get("avg")
        )
    except Exception:
        return {}

    delta = abs(measured_velocity - predicted_velocity)
    if delta <= 15.0:
        level = "ok"
        title = "Direct model match is good"
        message = (
            f"The batch's measured chrono average ({measured_velocity:.0f} fps) is close to "
            f"the saved prediction ({predicted_velocity:.0f} fps), delta about {delta:.0f} fps."
        )
    elif delta <= 30.0:
        level = "warning"
        title = "Direct model match is acceptable"
        message = (
            f"The batch's measured chrono average ({measured_velocity:.0f} fps) deviates noticeably from "
            f"the saved prediction ({predicted_velocity:.0f} fps), delta about {delta:.0f} fps."
        )
    else:
        level = "critical"
        title = "Direct model match is weak"
        message = (
            f"The batch's measured chrono average ({measured_velocity:.0f} fps) is far from "
            f"the saved prediction ({predicted_velocity:.0f} fps), delta about {delta:.0f} fps."
        )
    return {
        "level": level,
        "title": title,
        "message": message,
        "delta_fps": round(delta, 1),
        "predicted_velocity_fps": round(predicted_velocity, 1),
        "measured_velocity_fps": round(measured_velocity, 1),
    }


def _safe_float(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _batch_comparison_snapshot(batch: dict[str, Any] | None) -> dict[str, Any]:
    row = batch or {}
    analysis_data = _parse_analysis_payload(row.get("analysis_json") or {})
    metrics = (
        analysis_data.get("metrics")
        if isinstance(analysis_data.get("metrics"), dict)
        else {}
    )
    batch_id = row.get("id")
    batch_name = str(
        row.get("batch_name") or row.get("batch_number") or f"Batch {batch_id or '-'}"
    ).strip()
    group_avg = _safe_float(
        metrics.get("group_avg_mm") or analysis_data.get("group_avg_mm")
    )
    group_best = _safe_float(
        metrics.get("group_best_mm") or analysis_data.get("group_best_mm")
    )
    evidence_quality = (
        metrics.get("spread_evidence_quality")
        if isinstance(metrics.get("spread_evidence_quality"), dict)
        else analysis_data.get("spread_evidence_quality")
    )
    validation_status = (
        metrics.get("spread_validation_status")
        if isinstance(metrics.get("spread_validation_status"), dict)
        else analysis_data.get("spread_validation_status")
    )
    decision = (
        metrics.get("spread_decision")
        if isinstance(metrics.get("spread_decision"), dict)
        else analysis_data.get("spread_decision")
    )
    signal_hint = str(
        metrics.get("spread_signal_hint")
        or analysis_data.get("spread_signal_hint")
        or ""
    ).strip()
    quality_score = _safe_float((evidence_quality or {}).get("score"))
    quality_level = str((evidence_quality or {}).get("level") or "").strip()
    validation_score = _safe_float((validation_status or {}).get("readiness_score"))
    validation_label = str((validation_status or {}).get("label") or "").strip()
    validation_state = str((validation_status or {}).get("status") or "").strip()
    ready_now = bool((validation_status or {}).get("ready_now"))
    can_optimize = bool((decision or {}).get("can_optimize"))

    precision_component = 0.0
    if group_avg is not None:
        precision_component = max(0.0, 100.0 - min(group_avg, 100.0))
    elif group_best is not None:
        precision_component = max(0.0, 95.0 - min(group_best, 95.0))

    quality_component = quality_score or 0.0
    readiness_component = validation_score or 0.0
    comparison_score = (
        precision_component * 0.5 + quality_component * 0.3 + readiness_component * 0.2
    )
    if signal_hint == "pressure_or_ammo":
        comparison_score -= 35.0
    elif signal_hint in {
        "ammo_or_process_signal",
        "possible_shooter_or_setup_signal",
        "setup_drift_watch",
        "environment_or_condition_signal",
        "insufficient_evidence",
        "target_only",
        "velocity_only",
    }:
        comparison_score -= 18.0
    elif signal_hint == "node_or_barrel_timing_signal":
        comparison_score -= 10.0
    if validation_state in {
        "field_validation_pending",
        "ranking_validation_pending",
        "tuning_validation_pending",
        "collect_more_data",
        "provisional_validation",
    }:
        comparison_score -= 12.0
    if validation_state == "safety_block":
        comparison_score -= 25.0
    if ready_now or can_optimize:
        comparison_score += 5.0

    return {
        "batch_id": batch_id,
        "batch_name": batch_name,
        "load_session_id": row.get("load_session_id"),
        "rifle_id": row.get("rifle_id"),
        "setup_label": _format_batch_setup_label(row),
        "usage_goal": str(
            metrics.get("spread_usage_goal")
            or analysis_data.get("spread_usage_goal")
            or ""
        ).strip(),
        "group_avg_mm": group_avg,
        "group_best_mm": group_best,
        "quality_score": quality_score,
        "quality_level": quality_level,
        "validation_score": validation_score,
        "validation_label": validation_label,
        "validation_state": validation_state,
        "ready_now": ready_now,
        "can_optimize": can_optimize,
        "signal_hint": signal_hint,
        "comparison_score": round(max(0.0, min(100.0, comparison_score)), 1),
    }


def _build_batch_comparison_basis(
    current_batch: dict[str, Any] | None,
    comparable_batches: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    current = _batch_comparison_snapshot(current_batch)
    current_id = current.get("batch_id")
    if current_id in (None, ""):
        return {"available": False}

    siblings: list[dict[str, Any]] = []
    for row in comparable_batches or []:
        snapshot = _batch_comparison_snapshot(row)
        if snapshot.get("batch_id") in (None, "", current_id):
            continue
        same_load_session = current.get("load_session_id") not in (
            None,
            "",
        ) and snapshot.get("load_session_id") == current.get("load_session_id")
        same_rifle = current.get("rifle_id") not in (None, "") and snapshot.get(
            "rifle_id"
        ) == current.get("rifle_id")
        same_setup = bool(current.get("setup_label")) and snapshot.get(
            "setup_label"
        ) == current.get("setup_label")
        if same_load_session or (same_rifle and same_setup):
            siblings.append(snapshot)

    rankable = [current, *siblings]
    rankable = [
        item
        for item in rankable
        if item.get("group_avg_mm") is not None
        or item.get("quality_score") is not None
        or item.get("validation_score") is not None
    ]
    if len(rankable) < 2:
        return {
            "available": False,
            "summary": "There are not enough comparable sibling batches with measured evidence yet.",
            "scope": "sibling_batches",
            "count": len(rankable),
        }

    ranked = sorted(
        rankable,
        key=lambda item: (
            -(item.get("comparison_score") or 0.0),
            item.get("group_avg_mm") if item.get("group_avg_mm") is not None else 999.0,
            -(item.get("quality_score") or 0.0),
        ),
    )
    current_rank = next(
        (
            index + 1
            for index, item in enumerate(ranked)
            if item.get("batch_id") == current_id
        ),
        len(ranked),
    )
    leader = ranked[0]
    leader_gap = round(
        (leader.get("comparison_score") or 0.0)
        - (current.get("comparison_score") or 0.0),
        1,
    )

    if current.get("validation_state") == "safety_block":
        ranking_state = "blocked"
        summary = f"{current.get('batch_name')} is blocked from ranking because safety or ammo-watch signals still need to be resolved."
    elif current_rank == 1 and current.get("ready_now"):
        ranking_state = "leading_candidate"
        summary = f"{current.get('batch_name')} leads {len(ranked)} comparable batches on combined precision, evidence quality, and readiness."
    elif current_rank == 1:
        ranking_state = "leading_but_provisional"
        summary = f"{current.get('batch_name')} currently leads {len(ranked)} comparable batches, but the result is still provisional because validation is not complete."
    else:
        ranking_state = "trailing_candidate"
        summary = f"{current.get('batch_name')} currently ranks {current_rank} of {len(ranked)} comparable batches and trails {leader.get('batch_name')} by about {leader_gap:.1f} score points."

    watchouts: list[str] = []
    if not current.get("ready_now"):
        watchouts.append(
            "Do not let a provisional batch outrank better-validated evidence."
        )
    if current.get("signal_hint") in {
        "possible_shooter_or_setup_signal",
        "environment_or_condition_signal",
        "setup_drift_watch",
    }:
        watchouts.append(
            "The current spread signal still points to non-ammo effects that can distort ranking."
        )
    if leader.get("batch_id") != current_id and leader.get("quality_score", 0.0) > (
        current.get("quality_score") or 0.0
    ):
        watchouts.append(
            "A competing batch currently has stronger evidence quality behind its score."
        )

    top_candidates = [
        {
            "batch_id": item.get("batch_id"),
            "batch_name": item.get("batch_name"),
            "comparison_score": item.get("comparison_score"),
            "group_avg_mm": item.get("group_avg_mm"),
            "quality_score": item.get("quality_score"),
            "validation_label": item.get("validation_label"),
        }
        for item in ranked[:3]
    ]
    ranked_batches = [
        {
            "batch_id": item.get("batch_id"),
            "batch_name": item.get("batch_name"),
            "comparison_score": item.get("comparison_score"),
            "group_avg_mm": item.get("group_avg_mm"),
            "quality_score": item.get("quality_score"),
            "validation_label": item.get("validation_label"),
            "validation_state": item.get("validation_state"),
            "ready_now": item.get("ready_now"),
            "signal_hint": item.get("signal_hint"),
            "usage_goal": item.get("usage_goal"),
            "rank": index + 1,
            "setup_label": item.get("setup_label"),
        }
        for index, item in enumerate(ranked)
    ]

    next_gate = ""
    if current.get("validation_label"):
        next_gate = str(current.get("validation_label"))
    if current.get("validation_state") in {
        "leading_but_provisional",
        "ranking_validation_pending",
        "tuning_validation_pending",
    } or not current.get("ready_now"):
        next_gate = str(
            current.get("validation_label")
            or "Repeat and validate before trusting the rank"
        )

    return {
        "available": True,
        "scope": "sibling_batches",
        "count": len(ranked),
        "ranking_state": ranking_state,
        "current_rank": current_rank,
        "leader_batch_name": leader.get("batch_name"),
        "leader_gap_score": leader_gap if leader.get("batch_id") != current_id else 0.0,
        "summary": summary,
        "watchouts": watchouts,
        "top_candidates": top_candidates,
        "ranked_batches": ranked_batches,
        "current_batch": current,
        "next_gate": next_gate,
    }


def _build_batch_comparison_advisory(
    comparison_basis: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    if not comparison.get("available"):
        return {}

    ranking_state = str(comparison.get("ranking_state") or "").strip()
    summary = str(comparison.get("summary") or "").strip()
    leader_name = str(comparison.get("leader_batch_name") or "").strip()
    next_gate = str(comparison.get("next_gate") or "").strip()
    watchouts = [
        str(item).strip()
        for item in (comparison.get("watchouts") or [])
        if str(item).strip()
    ]

    if ranking_state == "blocked":
        return {
            "level": "critical",
            "title": "Batch comparison blocked",
            "message": summary
            or "Safety or ammo-watch signals still block meaningful comparison.",
            "recommended_action": next_gate
            or "Resolve the blocking safety signal before trusting any batch ranking.",
            "promotion_ready": False,
            "watchouts": watchouts,
        }
    if ranking_state == "leading_candidate":
        return {
            "level": "ok",
            "title": "Leading comparison candidate",
            "message": summary
            or "This batch currently leads the comparable set on combined precision and evidence.",
            "recommended_action": next_gate
            or "Keep the setup stable and confirm one more repeat before promoting this batch as the preferred candidate.",
            "promotion_ready": True,
            "watchouts": watchouts,
        }
    if ranking_state == "leading_but_provisional":
        return {
            "level": "warning",
            "title": "Leading but still provisional",
            "message": summary
            or "This batch is ahead, but the comparison is not durable yet.",
            "recommended_action": next_gate
            or "Repeat the current batch under matched conditions before promoting it over the others.",
            "promotion_ready": False,
            "watchouts": watchouts,
        }
    return {
        "level": "warning",
        "title": "Trailing stronger evidence",
        "message": summary or "Another batch currently has a stronger combined score.",
        "recommended_action": next_gate
        or (
            f"Match or exceed {leader_name} with stronger validation before promoting this batch."
            if leader_name
            else "Strengthen validation before promoting this batch."
        ),
        "promotion_ready": False,
        "watchouts": watchouts,
    }


def _build_batch_comparison_protocol(
    comparison_basis: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    if not comparison.get("available"):
        return {}

    ranking_state = str(comparison.get("ranking_state") or "").strip()
    leader_name = str(
        comparison.get("leader_batch_name") or "the leading batch"
    ).strip()
    current_batch = (
        comparison.get("current_batch")
        if isinstance(comparison.get("current_batch"), dict)
        else {}
    )
    usage_goal = str(current_batch.get("usage_goal") or "").strip()

    if ranking_state == "blocked":
        return {
            "title": "Safety reset before comparison",
            "primary_action": "Do not run a head-to-head comparison yet; resolve the safety or ammo-watch issue first.",
            "shot_plan": "Back down to a conservative reference load and confirm pressure behavior before any ranking test.",
            "avoid": "Do not promote, rank, or optimize a batch while safety is unresolved.",
            "success_criteria": "The batch returns to a non-blocked validation state with matched chrono and target evidence.",
        }
    if ranking_state == "leading_candidate":
        action = "Run one confirmation head-to-head against the current runner-up."
        if usage_goal == "hunting":
            action = "Run one cold-bore and one short realistic-support confirmation against the next best batch."
        return {
            "title": "Confirmation before promotion",
            "primary_action": action,
            "shot_plan": "Shoot both batches in the same session, same setup, alternating order if possible, with matched chrono and measured groups.",
            "avoid": "Do not change support, optic state, seating, or lot variables between the compared batches.",
            "success_criteria": "The leading batch still holds the edge when conditions and setup are matched directly.",
        }
    if ranking_state == "leading_but_provisional":
        return {
            "title": "Provisional leader confirmation",
            "primary_action": "Repeat the current leader under the same setup before promoting it over the rest of the batch set.",
            "shot_plan": "Shoot one matched repeat string with chrono plus measured group, then compare it with the nearest competing batch if the result stays stable.",
            "avoid": "Do not lock in the current rank from one provisional series.",
            "success_criteria": "The batch remains on top after a repeat under matched conditions with stronger evidence quality.",
        }
    return {
        "title": "Head-to-head catch-up test",
        "primary_action": f"Run a same-day head-to-head against {leader_name} before promoting this batch.",
        "shot_plan": "Shoot the current batch and the leader with the same rifle setup, same distance, same support, and matched chrono plus measured groups.",
        "avoid": "Do not compare across mixed wind, changed support, changed optic state, or unmatched chrono/group evidence.",
        "success_criteria": "The current batch matches or beats the leader after evidence quality and validation are improved in the same conditions.",
    }


def _build_batch_comparison_explanation(
    comparison_basis: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    if not comparison.get("available"):
        return {}

    current = (
        comparison.get("current_batch")
        if isinstance(comparison.get("current_batch"), dict)
        else {}
    )
    ranking_state = str(comparison.get("ranking_state") or "").strip()
    leader_name = str(comparison.get("leader_batch_name") or "").strip()
    quality_level = str(current.get("quality_level") or "").strip()
    validation_state = str(current.get("validation_state") or "").strip()
    signal_hint = str(current.get("signal_hint") or "").strip()
    ready_now = current.get("ready_now") is True
    comparison_gap = _safe_float(comparison.get("leader_gap_score"))

    limiting_factor = "overall_repeatability"
    reason = "The batch still needs one more matched confirmation before the rank should be trusted."
    next_measurement = "Capture one more matched chrono and group repeat."
    if validation_state == "safety_block" or signal_hint == "pressure_or_ammo":
        limiting_factor = "safety"
        reason = "Safety evidence still blocks meaningful promotion or ranking."
        next_measurement = "Return to a conservative reference load and confirm pressure behavior first."
    elif validation_state in {
        "field_validation_pending",
        "cold_bore_confirmation_pending",
    }:
        limiting_factor = "field_validation"
        reason = (
            "Field-style confirmation is the main thing still holding the batch back."
        )
        next_measurement = (
            "Capture one cold-bore and one realistic-support confirmation string."
        )
    elif validation_state in {
        "ranking_validation_pending",
        "tuning_validation_pending",
        "leading_but_provisional",
    }:
        limiting_factor = "validation_depth"
        reason = "The batch needs stronger repeat validation before the ranking can be promoted."
        next_measurement = (
            "Repeat the same setup with matched chrono and measured groups."
        )
    elif quality_level in {"very_thin", "thin"}:
        limiting_factor = "evidence_quality"
        reason = "Thin evidence is the main thing keeping this batch from outranking stronger candidates."
        next_measurement = (
            "Add another measured group and a 5-shot or larger chrono string."
        )
    elif signal_hint in {
        "possible_shooter_or_setup_signal",
        "environment_or_condition_signal",
        "setup_drift_watch",
        "ammo_or_process_signal",
        "node_or_barrel_timing_signal",
    }:
        limiting_factor = "cause_separation"
        reason = "The current spread signal still needs to be separated from ammo, shooter, setup, or condition effects."
        next_measurement = (
            "Run a controlled repeat that isolates the current spread signal."
        )

    if ranking_state == "leading_candidate":
        reason = "The batch currently leads because precision, evidence quality, and readiness all line up better than the nearby candidates."
        next_measurement = "One more matched confirmation keeps the lead durable."
    elif ranking_state == "leading_but_provisional":
        reason = "The batch currently leads on score, but the lead is still fragile because validation is not finished."
    elif ranking_state == "trailing_candidate" and comparison_gap is not None:
        reason = f"The batch trails {leader_name or 'the leader'} by about {comparison_gap:.1f} weighted comparison-score points."
    elif ranking_state == "blocked":
        reason = "The batch is currently blocked from meaningful comparison."

    strengths: list[str] = []
    if current.get("group_avg_mm") is not None:
        strengths.append(f"group avg {current['group_avg_mm']:.1f} mm")
    if current.get("quality_score") is not None:
        strengths.append(f"evidence {float(current['quality_score']):.1f}/100")
    if current.get("validation_score") is not None:
        strengths.append(f"readiness {float(current['validation_score']):.1f}/100")
    if ready_now:
        strengths.append("ready now")

    return {
        "title": "Comparison explanation",
        "ranking_state": ranking_state,
        "limiting_factor": limiting_factor,
        "reason": reason,
        "next_measurement": next_measurement,
        "strengths": strengths,
        "leader_batch_name": leader_name,
    }


def _build_batch_comparison_verdict(
    comparison_basis: dict[str, Any] | None,
    comparison_advisory: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    advisory = comparison_advisory or {}
    if not comparison.get("available"):
        return {}

    ranking_state = str(comparison.get("ranking_state") or "").strip()
    promotion_ready = advisory.get("promotion_ready") is True
    leader_name = str(comparison.get("leader_batch_name") or "").strip()

    if ranking_state == "blocked":
        return {
            "title": "Promotion blocked",
            "state": "blocked",
            "label": "Do not promote",
            "summary": "Safety or unresolved ammo-watch evidence blocks promotion.",
            "promote_now": False,
        }
    if ranking_state == "leading_candidate" and promotion_ready:
        return {
            "title": "Promotion candidate",
            "state": "conditional_promote",
            "label": "Promote after one last confirmation",
            "summary": "This batch leads, but one last matched confirmation keeps the promotion honest.",
            "promote_now": True,
        }
    if ranking_state == "leading_but_provisional":
        return {
            "title": "Provisional leader",
            "state": "hold_leader",
            "label": "Hold, do not promote yet",
            "summary": "This batch leads for now, but the lead is still too provisional to lock in.",
            "promote_now": False,
        }
    return {
        "title": "Trailing candidate",
        "state": "do_not_promote_yet",
        "label": "Do not promote yet",
        "summary": f"This batch should stay behind {leader_name or 'the current leader'} until the comparison gap is tested under matched conditions.",
        "promote_now": False,
    }


def _build_batch_comparison_acceptance(
    comparison_basis: dict[str, Any] | None,
    comparison_advisory: dict[str, Any] | None,
    comparison_explanation: dict[str, Any] | None,
    comparison_verdict: dict[str, Any] | None,
    comparison_confidence: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    advisory = comparison_advisory or {}
    explanation = comparison_explanation or {}
    verdict = comparison_verdict or {}
    confidence = comparison_confidence or {}
    if not comparison.get("available"):
        return {}

    current = (
        comparison.get("current_batch")
        if isinstance(comparison.get("current_batch"), dict)
        else {}
    )
    usage_goal = str(current.get("usage_goal") or "general").strip().lower()
    ranking_state = str(comparison.get("ranking_state") or "").strip()
    limiting_factor = str(explanation.get("limiting_factor") or "").strip()
    verdict_state = str(verdict.get("state") or "").strip()
    confidence_level = str(confidence.get("level") or "").strip()
    confidence_score = _safe_float(confidence.get("score"))
    leader_name = str(comparison.get("leader_batch_name") or "").strip()
    next_gate = str(advisory.get("recommended_action") or "").strip()

    must_be_true = [
        "Same setup, distance, and support must be matched across the compared batches.",
        "Matched chrono plus measured groups must exist for both batches.",
        "No active safety or pressure watch can be unresolved.",
    ]
    if usage_goal == "hunting":
        candidate_name = "field candidate"
        must_be_true.extend(
            [
                "Cold-bore behavior must stay predictable enough for hunting use.",
                "Point of impact must hold from realistic field support before promotion.",
            ]
        )
    elif usage_goal == "competition":
        candidate_name = "match candidate"
        must_be_true.extend(
            [
                "Repeatability must survive a matched same-day control string.",
                "The batch must still hold together when ES/SD and group data are compared side by side.",
            ]
        )
    elif usage_goal == "learning":
        candidate_name = "learning candidate"
        must_be_true.extend(
            [
                "The comparison must teach one clear difference rather than several moving variables at once.",
                "The current result must repeat under the same setup before the lesson is accepted.",
            ]
        )
    else:
        candidate_name = "leading candidate"
        must_be_true.append(
            "The batch must repeat under matched conditions before the comparison is treated as final."
        )

    remaining_gaps: list[str] = []
    if ranking_state == "blocked":
        remaining_gaps.append(
            "Safety or ammo-watch evidence still blocks meaningful promotion."
        )
    if ranking_state == "leading_but_provisional":
        remaining_gaps.append(
            "The batch leads for now, but the lead is still provisional."
        )
    if ranking_state == "trailing_candidate":
        remaining_gaps.append(
            f"The batch still trails {leader_name or 'the current leader'} under the weighted comparison."
        )
    if limiting_factor == "field_validation":
        remaining_gaps.append(
            "Cold-bore or realistic field validation is still missing."
        )
    elif limiting_factor == "validation_depth":
        remaining_gaps.append(
            "The current result still needs one more matched repeat to be accepted."
        )
    elif limiting_factor == "evidence_quality":
        remaining_gaps.append(
            "The comparison still rests on evidence that is too thin for a hard promotion call."
        )
    elif limiting_factor == "cause_separation":
        remaining_gaps.append(
            "Ammo, shooter, setup, or environment effects still need cleaner separation."
        )
    elif limiting_factor == "overall_repeatability":
        remaining_gaps.append(
            "The batch still needs to prove repeatability before replacing the leader."
        )
    elif limiting_factor == "safety":
        remaining_gaps.append(
            "Safety must be cleared before any acceptance decision can be honest."
        )
    if confidence_level in {"thin", "very_thin"}:
        remaining_gaps.append(
            "Comparison confidence is still too thin for a hard replacement decision."
        )

    acceptance_ready = (
        verdict.get("promote_now") is True
        and ranking_state == "leading_candidate"
        and confidence_level in {"moderate", "strong"}
        and not remaining_gaps
    )
    if (
        not acceptance_ready
        and not remaining_gaps
        and verdict_state == "conditional_promote"
    ):
        remaining_gaps.append(
            "One last matched confirmation should be completed before the promotion is locked in."
        )

    if ranking_state == "blocked":
        state = "acceptance_blocked"
        label = "Acceptance blocked"
        summary = "This batch cannot replace the current candidate until the blocked condition is cleared."
    elif acceptance_ready:
        state = "ready_for_cautious_acceptance"
        label = "Ready for cautious acceptance"
        summary = f"This batch now meets the comparison bar to replace the current {candidate_name}, as long as the matched confirmation stays honest."
    elif ranking_state == "leading_but_provisional":
        state = "provisional_acceptance"
        label = "Almost accepted, but still provisional"
        summary = f"This batch is close to replacing the current {candidate_name}, but the final acceptance bar is not met yet."
    else:
        state = "acceptance_pending"
        label = "Not accepted yet"
        summary = f"This batch should not replace the current {candidate_name} until the remaining comparison gaps are closed."

    if not next_gate:
        next_gate = str(explanation.get("next_measurement") or "").strip()

    return {
        "title": "Comparison acceptance gate",
        "state": state,
        "label": label,
        "summary": summary,
        "usage_goal": usage_goal or "general",
        "candidate_type": candidate_name,
        "must_be_true": must_be_true,
        "remaining_gaps": remaining_gaps,
        "next_gate": next_gate,
        "ready_for_acceptance": acceptance_ready,
        "confidence_level": confidence_level,
        "confidence_score": confidence_score,
    }


def _build_batch_comparison_acceptance_progress(
    comparison_acceptance: dict[str, Any] | None,
    comparison_checklist: dict[str, Any] | None,
    comparison_confidence: dict[str, Any] | None,
) -> dict[str, Any]:
    acceptance = comparison_acceptance or {}
    checklist = comparison_checklist or {}
    confidence = comparison_confidence or {}
    if not acceptance:
        return {}

    must_be_true = (
        acceptance.get("must_be_true")
        if isinstance(acceptance.get("must_be_true"), list)
        else []
    )
    remaining_gaps = (
        acceptance.get("remaining_gaps")
        if isinstance(acceptance.get("remaining_gaps"), list)
        else []
    )
    total_conditions = max(1, len([item for item in must_be_true if str(item).strip()]))
    remaining_count = min(
        total_conditions, len([item for item in remaining_gaps if str(item).strip()])
    )
    passed_count = max(0, total_conditions - remaining_count)
    confidence_score = _safe_float(confidence.get("score")) or 0.0
    base_score = (passed_count / total_conditions) * 70.0
    score = max(0.0, min(100.0, round(base_score + (confidence_score * 0.3), 1)))

    if score >= 80.0:
        level = "strong"
    elif score >= 60.0:
        level = "advancing"
    elif score >= 40.0:
        level = "partial"
    else:
        level = "early"

    state = str(acceptance.get("state") or "").strip()
    if state == "ready_for_cautious_acceptance":
        summary = "Most acceptance conditions are now in place, with only a cautious confirmation mindset still required."
    elif state == "provisional_acceptance":
        summary = "The batch is moving in the right direction, but acceptance still depends on closing the last provisional gap."
    elif state == "acceptance_blocked":
        summary = "Acceptance progress is blocked until the hard blocker is cleared."
    else:
        summary = "Acceptance progress is still partial, so the batch should keep earning evidence before replacement."

    next_target = str(acceptance.get("next_gate") or "").strip()
    if not next_target:
        next_target = str(checklist.get("highest_priority") or "").strip()

    return {
        "title": "Comparison acceptance progress",
        "score": score,
        "level": level,
        "passed_count": passed_count,
        "total_count": total_conditions,
        "remaining_count": remaining_count,
        "summary": summary,
        "next_target": next_target,
        "ready_for_acceptance": acceptance.get("ready_for_acceptance") is True,
    }


def _build_batch_comparison_next_test(
    comparison_basis: dict[str, Any] | None,
    comparison_protocol: dict[str, Any] | None,
    comparison_acceptance: dict[str, Any] | None,
    comparison_acceptance_progress: dict[str, Any] | None,
    comparison_checklist: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    protocol = comparison_protocol or {}
    acceptance = comparison_acceptance or {}
    progress = comparison_acceptance_progress or {}
    checklist = comparison_checklist or {}
    if not comparison.get("available"):
        return {}

    leader_name = str(comparison.get("leader_batch_name") or "the leader").strip()
    ranking_state = str(comparison.get("ranking_state") or "").strip()
    acceptance_state = str(acceptance.get("state") or "").strip()
    checklist_first = str(checklist.get("highest_priority") or "").strip()
    protocol_title = str(protocol.get("title") or "").strip()
    protocol_action = str(protocol.get("primary_action") or "").strip()
    protocol_plan = str(protocol.get("shot_plan") or "").strip()
    next_gate = str(
        acceptance.get("next_gate") or progress.get("next_target") or ""
    ).strip()

    if ranking_state == "blocked":
        title = "Clear the block first"
        test_type = "safety_reset"
        summary = "Do not run a promotion test until the blocked state is cleared."
    elif ranking_state == "trailing_candidate":
        title = f"Catch-up test vs {leader_name}"
        test_type = "head_to_head"
        summary = f"Run the current batch directly against {leader_name} under matched conditions before it is allowed to move up."
    elif acceptance_state == "provisional_acceptance":
        title = "Close the last acceptance gap"
        test_type = "acceptance_confirmation"
        summary = "The batch is close, but one last matched confirmation should close the final gap before promotion."
    elif acceptance.get("ready_for_acceptance") is True:
        title = "Final confirmation before cautious promotion"
        test_type = "promotion_confirmation"
        summary = "Run one honest matched confirmation before the batch is treated as the new lead candidate."
    else:
        title = "Matched confirmation test"
        test_type = "confirmation"
        summary = "Run one more matched comparison test before changing the ranking."

    return {
        "title": title,
        "test_type": test_type,
        "summary": summary,
        "primary_action": protocol_action or next_gate,
        "shot_plan": protocol_plan,
        "protocol_title": protocol_title,
        "check_first": checklist_first,
        "next_gate": next_gate,
        "leader_batch_name": leader_name,
    }


def _build_batch_comparison_status_board(
    comparison_basis: dict[str, Any] | None,
    comparison_verdict: dict[str, Any] | None,
    comparison_acceptance: dict[str, Any] | None,
    comparison_acceptance_progress: dict[str, Any] | None,
    comparison_next_test: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    verdict = comparison_verdict or {}
    acceptance = comparison_acceptance or {}
    progress = comparison_acceptance_progress or {}
    next_test = comparison_next_test or {}
    if not comparison.get("available"):
        return {}

    current_rank = _safe_float(comparison.get("current_rank"))
    total_count = _safe_float(comparison.get("count"))
    leader_name = str(comparison.get("leader_batch_name") or "").strip()
    ranking_state = str(comparison.get("ranking_state") or "").strip()
    acceptance_state = str(acceptance.get("state") or "").strip()
    progress_level = str(progress.get("level") or "").strip()
    progress_score = _safe_float(progress.get("score"))
    verdict_label = str(verdict.get("label") or "").strip()

    if ranking_state == "blocked":
        board_state = "blocked"
        readiness_band = "blocked"
        headline = "Comparison blocked"
    elif acceptance_state == "ready_for_cautious_acceptance":
        board_state = "promotion_ready"
        readiness_band = "ready"
        headline = "Ready for cautious promotion"
    elif acceptance_state == "provisional_acceptance":
        board_state = "near_promotion"
        readiness_band = "near_ready"
        headline = "Close, but still provisional"
    elif ranking_state == "trailing_candidate":
        board_state = "catch_up"
        readiness_band = "behind"
        headline = "Still chasing the leader"
    else:
        board_state = "hold"
        readiness_band = "hold"
        headline = "Hold current ranking"

    rank_text = ""
    if current_rank is not None and total_count is not None:
        rank_text = f"Rank {int(current_rank)}/{int(total_count)}"

    summary_bits = [headline]
    if rank_text:
        summary_bits.append(rank_text)
    if leader_name and ranking_state == "trailing_candidate":
        summary_bits.append(f"Leader: {leader_name}")
    if progress_level:
        progress_text = progress_level
        if progress_score is not None:
            progress_text += f" ({progress_score:.1f}/100)"
        summary_bits.append(f"Progress: {progress_text}")
    if verdict_label:
        summary_bits.append(f"Verdict: {verdict_label}")

    return {
        "title": "Comparison status board",
        "state": board_state,
        "headline": headline,
        "readiness_band": readiness_band,
        "summary": " | ".join(summary_bits),
        "leader_batch_name": leader_name,
        "current_rank": int(current_rank) if current_rank is not None else None,
        "count": int(total_count) if total_count is not None else None,
        "next_test_title": str(next_test.get("title") or "").strip(),
        "next_test_action": str(next_test.get("primary_action") or "").strip(),
        "promotion_ready": acceptance.get("ready_for_acceptance") is True,
    }


def _build_batch_comparison_profile_priority(
    comparison_basis: dict[str, Any] | None,
    comparison_acceptance: dict[str, Any] | None,
    comparison_next_test: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    acceptance = comparison_acceptance or {}
    next_test = comparison_next_test or {}
    if not comparison.get("available"):
        return {}

    current = (
        comparison.get("current_batch")
        if isinstance(comparison.get("current_batch"), dict)
        else {}
    )
    usage_goal = str(current.get("usage_goal") or "general").strip().lower()
    acceptance_state = str(acceptance.get("state") or "").strip()
    next_gate = str(
        acceptance.get("next_gate") or next_test.get("primary_action") or ""
    ).strip()

    if usage_goal == "hunting":
        title = "Hunting comparison priority"
        emphasis = "Protect cold-bore trust, field realism, and humane predictability before chasing the leaderboard."
        guardrail = "Do not promote a hunting batch until cold-bore or first-shot behavior and realistic support are verified."
        success_marker = "One calm, field-style confirmation that keeps impact and behavior predictable."
    elif usage_goal == "competition":
        title = "Competition comparison priority"
        emphasis = "Favor repeatability, matched evidence, and setup control over one attractive result."
        guardrail = "Do not rank a batch higher until the same-day repeat and matched chrono/group evidence agree."
        success_marker = "A matched repeat string that still holds precision and consistency against the current leader."
    elif usage_goal == "learning":
        title = "Learning comparison priority"
        emphasis = (
            "Use the comparison to isolate one clear lesson before declaring a winner."
        )
        guardrail = (
            "Do not let several moving variables turn the comparison into noise."
        )
        success_marker = "A repeatable result that teaches one clear reason this batch should move up or stay back."
    else:
        title = "Comparison priority"
        emphasis = "Keep the comparison honest by matching setup, evidence, and confirmation depth."
        guardrail = "Do not promote the batch until the comparison is repeatable."
        success_marker = (
            "A matched confirmation that leaves little doubt about the current order."
        )

    if acceptance_state == "acceptance_blocked":
        emphasis = "Clear the hard blocker before spending shots on ranking."

    return {
        "title": title,
        "usage_goal": usage_goal or "general",
        "emphasis": emphasis,
        "guardrail": guardrail,
        "success_marker": success_marker,
        "next_gate": next_gate,
    }


def _build_batch_comparison_mission_brief(
    comparison_basis: dict[str, Any] | None,
    comparison_status_board: dict[str, Any] | None,
    comparison_profile_priority: dict[str, Any] | None,
    comparison_next_test: dict[str, Any] | None,
    comparison_acceptance: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    status_board = comparison_status_board or {}
    profile = comparison_profile_priority or {}
    next_test = comparison_next_test or {}
    acceptance = comparison_acceptance or {}
    if not comparison.get("available"):
        return {}

    headline = str(status_board.get("headline") or "Comparison mission").strip()
    readiness_band = str(status_board.get("readiness_band") or "").strip()
    next_action = str(
        next_test.get("primary_action") or acceptance.get("next_gate") or ""
    ).strip()
    next_summary = str(next_test.get("summary") or "").strip()
    check_first = str(next_test.get("check_first") or "").strip()
    guardrail = str(profile.get("guardrail") or "").strip()
    success_marker = str(profile.get("success_marker") or "").strip()
    usage_goal = str(profile.get("usage_goal") or "general").strip()

    title = "Comparison mission brief"
    mission = (
        f"{headline}: {next_summary or 'Run the next matched comparison honestly.'}"
    )
    if usage_goal == "hunting":
        mission = f"{headline}: Treat the next outing as a field-trust check before promotion."
    elif usage_goal == "competition":
        mission = f"{headline}: Treat the next outing as a matched ranking test, not a free-form tuning session."
    elif usage_goal == "learning":
        mission = f"{headline}: Treat the next outing as a single-lesson comparison, not a broad experiment."

    return {
        "title": title,
        "mission": mission,
        "readiness_band": readiness_band,
        "primary_action": next_action,
        "check_first": check_first,
        "guardrail": guardrail,
        "success_marker": success_marker,
    }


def _build_batch_comparison_portfolio(
    comparison_basis: dict[str, Any] | None,
    comparison_status_board: dict[str, Any] | None,
    comparison_acceptance: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    status_board = comparison_status_board or {}
    acceptance = comparison_acceptance or {}
    if not comparison.get("available"):
        return {}

    top_candidates = (
        comparison.get("top_candidates")
        if isinstance(comparison.get("top_candidates"), list)
        else []
    )
    ranking_state = str(comparison.get("ranking_state") or "").strip()
    leader_name = str(comparison.get("leader_batch_name") or "").strip()
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(top_candidates[:3], start=1):
        if not isinstance(candidate, dict):
            continue
        rows.append(
            {
                "rank": index,
                "batch_name": str(
                    candidate.get("batch_name") or f"Batch {index}"
                ).strip(),
                "comparison_score": _safe_float(candidate.get("comparison_score")),
                "group_avg_mm": _safe_float(candidate.get("group_avg_mm")),
                "quality_score": _safe_float(candidate.get("quality_score")),
                "validation_label": str(
                    candidate.get("validation_label") or ""
                ).strip(),
            }
        )

    focus = "Protect the current leader until a challenger earns matched confirmation."
    if ranking_state == "trailing_candidate":
        focus = f"Use the next session to test whether the current batch can close the gap to {leader_name or 'the leader'}."
    elif acceptance.get("ready_for_acceptance") is True:
        focus = "Treat the current leader as promotable, but confirm it honestly one last time."
    elif str(acceptance.get("state") or "").strip() == "provisional_acceptance":
        focus = "The current leader is promising, but the portfolio still needs one last acceptance check."

    return {
        "title": "Comparison portfolio",
        "leader_batch_name": leader_name,
        "ranking_state": ranking_state,
        "focus": focus,
        "status_headline": str(status_board.get("headline") or "").strip(),
        "rows": rows,
    }


def _build_batch_comparison_session_strategy(
    comparison_basis: dict[str, Any] | None,
    comparison_profile_priority: dict[str, Any] | None,
    comparison_mission_brief: dict[str, Any] | None,
    comparison_next_test: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    profile = comparison_profile_priority or {}
    mission = comparison_mission_brief or {}
    next_test = comparison_next_test or {}
    if not comparison.get("available"):
        return {}

    current = (
        comparison.get("current_batch")
        if isinstance(comparison.get("current_batch"), dict)
        else {}
    )
    usage_goal = str(current.get("usage_goal") or "general").strip().lower()
    ranking_state = str(comparison.get("ranking_state") or "").strip()
    test_type = str(next_test.get("test_type") or "").strip()
    mission_action = str(
        mission.get("primary_action") or next_test.get("primary_action") or ""
    ).strip()
    check_first = str(
        mission.get("check_first") or next_test.get("check_first") or ""
    ).strip()

    if usage_goal == "hunting":
        mode = "field_validation_session"
        objective = "Confirm hunting trust before promotion."
    elif usage_goal == "competition":
        mode = "ranking_session"
        objective = "Run a clean ranking session before any more tuning."
    elif usage_goal == "learning":
        mode = "learning_session"
        objective = "Use the next session to isolate one clear lesson."
    else:
        mode = "comparison_session"
        objective = "Run one honest comparison session before changing the order."

    if ranking_state == "trailing_candidate" and test_type == "head_to_head":
        objective = "Challenge the current leader under matched conditions."
    elif test_type == "promotion_confirmation":
        objective = "Confirm the likely winner without adding new noise."

    return {
        "title": "Comparison session strategy",
        "mode": mode,
        "objective": objective,
        "primary_action": mission_action,
        "check_first": check_first,
        "guardrail": str(profile.get("guardrail") or "").strip(),
    }


def _build_batch_comparison_campaign_view(
    comparison_portfolio: dict[str, Any] | None,
    comparison_session_strategy: dict[str, Any] | None,
    comparison_status_board: dict[str, Any] | None,
    comparison_next_test: dict[str, Any] | None,
) -> dict[str, Any]:
    portfolio = comparison_portfolio or {}
    strategy = comparison_session_strategy or {}
    status_board = comparison_status_board or {}
    next_test = comparison_next_test or {}
    if not portfolio and not strategy and not status_board:
        return {}

    title = "Comparison campaign view"
    leader_name = str(
        portfolio.get("leader_batch_name")
        or status_board.get("leader_batch_name")
        or ""
    ).strip()
    readiness_band = str(status_board.get("readiness_band") or "").strip()
    mode = str(strategy.get("mode") or "").strip()
    objective = str(strategy.get("objective") or "").strip()
    next_test_title = str(next_test.get("title") or "").strip()
    next_test_action = str(next_test.get("primary_action") or "").strip()

    summary_bits: list[str] = []
    if leader_name:
        summary_bits.append(f"Leader {leader_name}")
    if readiness_band:
        summary_bits.append(f"band {readiness_band}")
    if mode:
        summary_bits.append(f"mode {mode}")
    if objective:
        summary_bits.append(objective)
    summary = " | ".join(summary_bits)

    return {
        "title": title,
        "summary": summary,
        "leader_batch_name": leader_name,
        "readiness_band": readiness_band,
        "mode": mode,
        "objective": objective,
        "next_test_title": next_test_title,
        "next_test_action": next_test_action,
    }


def _build_batch_comparison_action_plan(
    comparison_campaign_view: dict[str, Any] | None,
    comparison_mission_brief: dict[str, Any] | None,
    comparison_checklist: dict[str, Any] | None,
) -> dict[str, Any]:
    campaign = comparison_campaign_view or {}
    mission = comparison_mission_brief or {}
    checklist = comparison_checklist or {}
    if not campaign and not mission:
        return {}

    checklist_items = (
        checklist.get("items") if isinstance(checklist.get("items"), list) else []
    )
    first_steps = [
        str(item.get("label") or "").strip()
        for item in checklist_items[:3]
        if isinstance(item, dict) and str(item.get("label") or "").strip()
    ]

    return {
        "title": "Comparison action plan",
        "summary": str(
            campaign.get("objective") or mission.get("mission") or ""
        ).strip(),
        "primary_action": str(
            mission.get("primary_action") or campaign.get("next_test_action") or ""
        ).strip(),
        "first_steps": first_steps,
        "success_marker": str(mission.get("success_marker") or "").strip(),
    }


def _campaign_priority_for_batch(
    candidate: dict[str, Any] | None,
) -> tuple[str, str, int]:
    row = candidate or {}
    validation_state = str(row.get("validation_state") or "").strip()
    signal_hint = str(row.get("signal_hint") or "").strip()
    ready_now = row.get("ready_now") is True
    rank = int(_safe_float(row.get("rank")) or 99)

    if validation_state == "safety_block" or signal_hint == "pressure_or_ammo":
        return ("reject_watch", "Pressure or safety evidence blocks normal ranking.", 5)
    if ready_now and rank == 1:
        return (
            "shoot_now",
            "This is the strongest current candidate and should be the first live confirmation.",
            1,
        )
    if validation_state in {
        "field_validation_pending",
        "ranking_validation_pending",
        "tuning_validation_pending",
    }:
        return (
            "confirm",
            "This batch is promising but still needs confirmation before promotion.",
            2,
        )
    if signal_hint in {
        "possible_shooter_or_setup_signal",
        "environment_or_condition_signal",
        "setup_drift_watch",
    }:
        return (
            "pause",
            "Non-ammo effects still distort the picture, so pause ranking pressure and clean up the test conditions.",
            4,
        )
    if rank <= 3:
        return (
            "hold",
            "Keep this batch in the candidate set, but it is not the first priority right now.",
            3,
        )
    return (
        "hold",
        "Keep this batch on the board until the main candidates are clarified.",
        4,
    )


def _build_batch_comparison_campaign_board(
    comparison_basis: dict[str, Any] | None,
    comparison_campaign_view: dict[str, Any] | None,
    comparison_action_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    campaign = comparison_campaign_view or {}
    action_plan = comparison_action_plan or {}
    if not comparison.get("available"):
        return {}

    ranked_batches = (
        comparison.get("ranked_batches")
        if isinstance(comparison.get("ranked_batches"), list)
        else []
    )
    rows: list[dict[str, Any]] = []
    for candidate in ranked_batches:
        if not isinstance(candidate, dict):
            continue
        priority, rationale, priority_order = _campaign_priority_for_batch(candidate)
        rows.append(
            {
                "batch_id": candidate.get("batch_id"),
                "batch_name": candidate.get("batch_name"),
                "rank": candidate.get("rank"),
                "priority": priority,
                "rationale": rationale,
                "comparison_score": candidate.get("comparison_score"),
                "validation_label": candidate.get("validation_label"),
                "signal_hint": candidate.get("signal_hint"),
                "_priority_order": priority_order,
            }
        )

    rows.sort(
        key=lambda item: (
            item.get("_priority_order", 99),
            int(_safe_float(item.get("rank")) or 99),
            -(item.get("comparison_score") or 0.0),
        )
    )
    for item in rows:
        item.pop("_priority_order", None)

    summary = str(campaign.get("summary") or action_plan.get("summary") or "").strip()
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("priority") or "").strip()
        counts[key] = counts.get(key, 0) + 1
    headline = str(campaign.get("summary") or action_plan.get("summary") or "").strip()
    preview = [
        f"{str(row.get('priority') or '').strip()}: {str(row.get('batch_name') or '').strip()}".strip(
            ": "
        )
        for row in rows[:3]
        if isinstance(row, dict) and (row.get("priority") or row.get("batch_name"))
    ]

    return {
        "title": "Comparison campaign board",
        "summary": summary,
        "headline": headline,
        "counts": counts,
        "rows": rows,
        "preview": preview,
        "first_batch_name": (
            str((rows[0] or {}).get("batch_name") or "").strip() if rows else ""
        ),
    }


def _build_batch_comparison_session_queue(
    comparison_campaign_board: dict[str, Any] | None,
    comparison_session_strategy: dict[str, Any] | None,
) -> dict[str, Any]:
    board = comparison_campaign_board or {}
    strategy = comparison_session_strategy or {}
    if not board:
        return {}

    rows = board.get("rows") if isinstance(board.get("rows"), list) else []
    queue_rows = rows[:5]
    queue = []
    for index, row in enumerate(queue_rows, start=1):
        if not isinstance(row, dict):
            continue
        queue.append(
            {
                "slot": index,
                "batch_name": str(row.get("batch_name") or f"Batch {index}").strip(),
                "priority": str(row.get("priority") or "").strip(),
                "rationale": str(row.get("rationale") or "").strip(),
            }
        )

    return {
        "title": "Comparison session queue",
        "mode": str(strategy.get("mode") or "").strip(),
        "objective": str(strategy.get("objective") or "").strip(),
        "queue": queue,
        "first_batch_name": (
            str((queue[0] or {}).get("batch_name") or "").strip() if queue else ""
        ),
        "preview": [
            f"{str(item.get('slot') or '').strip()}. {str(item.get('batch_name') or '').strip()} ({str(item.get('priority') or '').strip()})"
            for item in queue[:3]
            if isinstance(item, dict) and str(item.get("batch_name") or "").strip()
        ],
    }


def _build_batch_comparison_session_manifest(
    comparison_campaign_board: dict[str, Any] | None,
    comparison_session_queue: dict[str, Any] | None,
    comparison_action_plan: dict[str, Any] | None,
    comparison_session_strategy: dict[str, Any] | None,
) -> dict[str, Any]:
    board = comparison_campaign_board or {}
    queue_data = comparison_session_queue or {}
    action_plan = comparison_action_plan or {}
    strategy = comparison_session_strategy or {}
    rows = board.get("rows") if isinstance(board.get("rows"), list) else []
    queue = queue_data.get("queue") if isinstance(queue_data.get("queue"), list) else []
    if not rows and not queue:
        return {}

    buckets: dict[str, list[dict[str, Any]]] = {
        "shoot_now": [],
        "confirm": [],
        "hold": [],
        "pause": [],
        "reject_watch": [],
    }
    for row in rows:
        if not isinstance(row, dict):
            continue
        priority = str(row.get("priority") or "hold").strip() or "hold"
        if priority not in buckets:
            priority = "hold"
        buckets[priority].append(
            {
                "batch_name": str(row.get("batch_name") or "").strip(),
                "rank": int(_safe_float(row.get("rank")) or 99),
                "rationale": str(row.get("rationale") or "").strip(),
            }
        )

    primary_bucket = next(
        (
            name
            for name in ("shoot_now", "confirm", "hold", "pause", "reject_watch")
            if buckets[name]
        ),
        "",
    )
    first_queue = queue[0] if queue and isinstance(queue[0], dict) else {}
    first_batch_name = str(
        first_queue.get("batch_name") or queue_data.get("first_batch_name") or ""
    ).strip()
    primary_action = str(
        action_plan.get("primary_action") or strategy.get("objective") or ""
    ).strip()
    summary = str(
        board.get("summary")
        or action_plan.get("summary")
        or strategy.get("objective")
        or ""
    ).strip()
    ready_now_count = len(buckets["shoot_now"])
    confirm_count = len(buckets["confirm"])
    watch_count = len(buckets["pause"]) + len(buckets["reject_watch"])
    summary_bits = []
    if summary:
        summary_bits.append(summary)
    summary_bits.append(f"Ready now: {ready_now_count}")
    summary_bits.append(f"Confirm next: {confirm_count}")
    if watch_count:
        summary_bits.append(f"Watch/pause: {watch_count}")
    lane_summaries = []
    for bucket_name in ("shoot_now", "confirm", "hold", "pause", "reject_watch"):
        bucket_items = buckets[bucket_name]
        if not bucket_items:
            continue
        top_names = ", ".join(
            str(item.get("batch_name") or "").strip()
            for item in bucket_items[:2]
            if isinstance(item, dict) and str(item.get("batch_name") or "").strip()
        )
        lane_summaries.append(
            {
                "bucket": bucket_name,
                "count": len(bucket_items),
                "summary": f"{bucket_name}: {top_names}".strip(": "),
            }
        )

    return {
        "title": "Comparison session manifest",
        "mode": str(queue_data.get("mode") or strategy.get("mode") or "").strip(),
        "objective": str(
            queue_data.get("objective") or strategy.get("objective") or ""
        ).strip(),
        "summary": " | ".join(bit for bit in summary_bits if bit),
        "primary_bucket": primary_bucket,
        "first_batch_name": first_batch_name,
        "primary_action": primary_action,
        "buckets": buckets,
        "lane_summaries": lane_summaries,
        "queue_preview": [
            f"{str(item.get('slot') or '').strip()}. {str(item.get('batch_name') or '').strip()} ({str(item.get('priority') or '').strip()})"
            for item in queue[:3]
            if isinstance(item, dict) and str(item.get("batch_name") or "").strip()
        ],
    }


def _build_batch_comparison_next_session_brief(
    comparison_session_manifest: dict[str, Any] | None,
    comparison_session_queue: dict[str, Any] | None,
    comparison_checklist: dict[str, Any] | None,
    comparison_action_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    manifest = comparison_session_manifest or {}
    queue_data = comparison_session_queue or {}
    checklist = comparison_checklist or {}
    action_plan = comparison_action_plan or {}
    if not manifest and not queue_data:
        return {}

    first_batch_name = str(
        manifest.get("first_batch_name") or queue_data.get("first_batch_name") or ""
    ).strip()
    primary_bucket = str(manifest.get("primary_bucket") or "").strip()
    primary_action = str(
        action_plan.get("primary_action") or manifest.get("primary_action") or ""
    ).strip()
    compare_first = str(checklist.get("highest_priority") or "").strip()
    queue_preview = (
        manifest.get("queue_preview")
        if isinstance(manifest.get("queue_preview"), list)
        else []
    )
    lane_summaries = (
        manifest.get("lane_summaries")
        if isinstance(manifest.get("lane_summaries"), list)
        else []
    )

    summary_bits = []
    if first_batch_name:
        summary_bits.append(f"Start with {first_batch_name}")
    if primary_bucket:
        summary_bits.append(f"bucket {primary_bucket}")
    if compare_first:
        summary_bits.append(f"check {compare_first}")

    hold_back = ""
    for lane in lane_summaries:
        if not isinstance(lane, dict):
            continue
        bucket = str(lane.get("bucket") or "").strip()
        if bucket in {"pause", "reject_watch", "hold"}:
            hold_back = str(lane.get("summary") or "").strip()
            if hold_back:
                break

    return {
        "title": "Comparison next session brief",
        "summary": " | ".join(bit for bit in summary_bits if bit),
        "first_batch_name": first_batch_name,
        "primary_bucket": primary_bucket,
        "primary_action": primary_action,
        "compare_first": compare_first,
        "queue_preview": queue_preview,
        "hold_back": hold_back,
    }


def _build_batch_comparison_today_plan(
    comparison_next_session_brief: dict[str, Any] | None,
    comparison_session_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    brief = comparison_next_session_brief or {}
    manifest = comparison_session_manifest or {}
    if not brief and not manifest:
        return {}

    first_batch_name = str(
        brief.get("first_batch_name") or manifest.get("first_batch_name") or ""
    ).strip()
    primary_bucket = str(
        brief.get("primary_bucket") or manifest.get("primary_bucket") or ""
    ).strip()
    primary_action = str(
        brief.get("primary_action") or manifest.get("primary_action") or ""
    ).strip()
    compare_first = str(brief.get("compare_first") or "").strip()
    hold_back = str(brief.get("hold_back") or "").strip()

    summary_bits = []
    if first_batch_name:
        summary_bits.append(f"Run {first_batch_name} first")
    if compare_first:
        summary_bits.append(f"verify {compare_first}")
    if hold_back:
        summary_bits.append(f"hold back {hold_back}")

    return {
        "title": "Comparison today plan",
        "summary": " | ".join(summary_bits),
        "first_batch_name": first_batch_name,
        "primary_bucket": primary_bucket,
        "primary_action": primary_action,
        "compare_first": compare_first,
        "hold_back": hold_back,
    }


def _build_batch_comparison_workboard(
    comparison_campaign_board: dict[str, Any] | None,
    comparison_session_manifest: dict[str, Any] | None,
    comparison_next_session_brief: dict[str, Any] | None,
    comparison_today_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    board = comparison_campaign_board or {}
    manifest = comparison_session_manifest or {}
    brief = comparison_next_session_brief or {}
    today = comparison_today_plan or {}
    if not board and not manifest and not brief and not today:
        return {}

    first_batch_name = str(
        today.get("first_batch_name")
        or brief.get("first_batch_name")
        or manifest.get("first_batch_name")
        or board.get("first_batch_name")
        or ""
    ).strip()
    primary_bucket = str(
        today.get("primary_bucket")
        or brief.get("primary_bucket")
        or manifest.get("primary_bucket")
        or ""
    ).strip()
    primary_action = str(
        today.get("primary_action")
        or brief.get("primary_action")
        or manifest.get("primary_action")
        or ""
    ).strip()
    hold_back = str(today.get("hold_back") or brief.get("hold_back") or "").strip()
    lane_summaries = (
        manifest.get("lane_summaries")
        if isinstance(manifest.get("lane_summaries"), list)
        else []
    )
    queue_preview = (
        manifest.get("queue_preview")
        if isinstance(manifest.get("queue_preview"), list)
        else []
    )
    summary = str(
        today.get("summary")
        or brief.get("summary")
        or manifest.get("summary")
        or board.get("summary")
        or ""
    ).strip()
    counts = board.get("counts") if isinstance(board.get("counts"), dict) else {}
    if counts.get("reject_watch"):
        status_label = "Watch items active"
    elif primary_bucket == "confirm":
        status_label = "Confirmation session"
    elif primary_bucket == "shoot_now":
        status_label = "Ready to run"
    else:
        status_label = "Managed workboard"

    return {
        "title": "Comparison workboard",
        "summary": summary,
        "status_label": status_label,
        "first_batch_name": first_batch_name,
        "primary_bucket": primary_bucket,
        "primary_action": primary_action,
        "hold_back": hold_back,
        "counts": counts,
        "lane_summaries": lane_summaries,
        "queue_preview": queue_preview,
    }


def _build_batch_comparison_checklist(
    comparison_basis: dict[str, Any] | None,
    comparison_protocol: dict[str, Any] | None,
    comparison_explanation: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    protocol = comparison_protocol or {}
    explanation = comparison_explanation or {}
    if not comparison.get("available"):
        return {}

    ranking_state = str(comparison.get("ranking_state") or "").strip()
    limiting_factor = str(explanation.get("limiting_factor") or "").strip()
    items: list[dict[str, str]] = []

    def add_item(key: str, label: str, why: str, priority: str) -> None:
        if key not in {item["key"] for item in items}:
            items.append({"key": key, "label": label, "why": why, "priority": priority})

    add_item(
        "same_setup",
        "Same setup on both batches",
        "Comparison only means something if rifle setup and support are matched.",
        "high",
    )
    add_item(
        "matched_chrono_group",
        "Matched chrono and measured groups",
        "Both batches need the same measurement basis.",
        "high",
    )
    if ranking_state in {
        "trailing_candidate",
        "leading_candidate",
        "leading_but_provisional",
    }:
        add_item(
            "same_day_compare",
            "Same-day comparison string",
            "Different days and drifting conditions can fake winners.",
            "high",
        )
    if limiting_factor == "field_validation":
        add_item(
            "cold_bore",
            "Cold-bore confirmation",
            "Field or hunting promotion depends on first-shot behavior.",
            "high",
        )
    if limiting_factor == "evidence_quality":
        add_item(
            "extra_group",
            "One more repeat group",
            "Thin evidence is the main reason the comparison is weak.",
            "high",
        )
        add_item(
            "chrono_5plus",
            "5+ shot chrono string",
            "A larger chrono sample makes the comparison more trustworthy.",
            "medium",
        )
    if limiting_factor == "validation_depth":
        add_item(
            "repeat_string",
            "Repeat the current batch once more",
            "Validation depth is the bottleneck right now.",
            "high",
        )
    if limiting_factor == "cause_separation":
        add_item(
            "signal_control",
            "Control the active spread signal",
            "Shooter/setup/environment effects must be separated before promotion.",
            "high",
        )
    if ranking_state == "blocked":
        add_item(
            "safety_reset",
            "Safety reset first",
            "No comparison matters until the blocked state is cleared.",
            "high",
        )
    if protocol.get("shot_plan"):
        add_item(
            "shot_plan",
            "Follow the comparison shot plan",
            str(protocol.get("shot_plan") or ""),
            "medium",
        )

    return {
        "title": "Comparison checklist",
        "items": items,
        "highest_priority": next(
            (item["label"] for item in items if item["priority"] == "high"),
            items[0]["label"],
        ),
    }


def _build_batch_comparison_scorecard(
    comparison_basis: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    if not comparison.get("available"):
        return {}

    current = (
        comparison.get("current_batch")
        if isinstance(comparison.get("current_batch"), dict)
        else {}
    )
    top_candidates = (
        comparison.get("top_candidates")
        if isinstance(comparison.get("top_candidates"), list)
        else []
    )
    if not current or not top_candidates:
        return {}

    leader = top_candidates[0] if isinstance(top_candidates[0], dict) else {}
    current_name = str(current.get("batch_name") or "Current batch").strip()
    leader_name = str(leader.get("batch_name") or "Leader").strip()

    precision_score = None
    if current.get("group_avg_mm") not in (None, ""):
        try:
            precision_score = max(
                0.0, 100.0 - min(float(current["group_avg_mm"]), 100.0)
            )
        except Exception:
            precision_score = None
    leader_precision_score = None
    if leader.get("group_avg_mm") not in (None, ""):
        try:
            leader_precision_score = max(
                0.0, 100.0 - min(float(leader["group_avg_mm"]), 100.0)
            )
        except Exception:
            leader_precision_score = None

    current_quality = _safe_float(current.get("quality_score"))
    leader_quality = _safe_float(leader.get("quality_score"))
    current_readiness = _safe_float(current.get("validation_score"))
    leader_readiness = _safe_float(leader.get("validation_score"))

    deltas = {
        "precision": round(
            (precision_score or 0.0) - (leader_precision_score or 0.0), 1
        ),
        "evidence_quality": round(
            (current_quality or 0.0) - (leader_quality or 0.0), 1
        ),
        "readiness": round((current_readiness or 0.0) - (leader_readiness or 0.0), 1),
    }
    swing_factor = min(deltas.items(), key=lambda item: item[1])[0]
    summary_map = {
        "precision": f"{current_name} mainly trails {leader_name} on measured precision.",
        "evidence_quality": f"{current_name} mainly trails {leader_name} on evidence quality.",
        "readiness": f"{current_name} mainly trails {leader_name} on validation/readiness.",
    }

    rows: list[dict[str, Any]] = []
    for candidate in top_candidates[:3]:
        if not isinstance(candidate, dict):
            continue
        rows.append(
            {
                "batch_name": str(candidate.get("batch_name") or "").strip(),
                "comparison_score": _safe_float(candidate.get("comparison_score")),
                "group_avg_mm": _safe_float(candidate.get("group_avg_mm")),
                "quality_score": _safe_float(candidate.get("quality_score")),
                "validation_label": str(
                    candidate.get("validation_label") or ""
                ).strip(),
            }
        )

    return {
        "title": "Comparison scorecard",
        "leader_batch_name": leader_name,
        "current_batch_name": current_name,
        "current_rank": comparison.get("current_rank"),
        "summary": summary_map.get(swing_factor, ""),
        "swing_factor": swing_factor,
        "delta_precision": deltas["precision"],
        "delta_evidence_quality": deltas["evidence_quality"],
        "delta_readiness": deltas["readiness"],
        "rows": rows,
    }


def _build_batch_comparison_confidence(
    comparison_basis: dict[str, Any] | None,
    comparison_explanation: dict[str, Any] | None,
    comparison_verdict: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    explanation = comparison_explanation or {}
    verdict = comparison_verdict or {}
    if not comparison.get("available"):
        return {}

    current = (
        comparison.get("current_batch")
        if isinstance(comparison.get("current_batch"), dict)
        else {}
    )
    ranking_state = str(comparison.get("ranking_state") or "").strip()
    limiting_factor = str(explanation.get("limiting_factor") or "").strip()
    quality_score = _safe_float(current.get("quality_score")) or 0.0
    readiness_score = _safe_float(current.get("validation_score")) or 0.0
    comparison_gap = _safe_float(comparison.get("leader_gap_score")) or 0.0
    promote_now = verdict.get("promote_now") is True

    score = 25.0
    score += min(35.0, quality_score * 0.35)
    score += min(25.0, readiness_score * 0.25)
    if ranking_state == "leading_candidate":
        score += 10.0
    elif ranking_state == "leading_but_provisional":
        score += 4.0
    elif ranking_state == "blocked":
        score -= 30.0
    if limiting_factor in {"safety", "field_validation", "validation_depth"}:
        score -= 12.0
    elif limiting_factor in {"evidence_quality", "cause_separation"}:
        score -= 8.0
    if comparison_gap >= 10.0:
        score -= 6.0
    elif comparison_gap <= 2.0 and comparison.get("current_rank") == 1:
        score += 4.0
    if promote_now:
        score += 4.0

    score = max(0.0, min(100.0, score))
    if score >= 75.0:
        level = "strong"
    elif score >= 55.0:
        level = "moderate"
    elif score >= 35.0:
        level = "thin"
    else:
        level = "very_thin"

    summary = {
        "strong": "The current batch comparison is strong enough to guide cautious real-world decisions.",
        "moderate": "The current batch comparison is useful, but it still benefits from one more matched confirmation.",
        "thin": "The current batch comparison is directionally useful, but still too thin for hard promotion decisions.",
        "very_thin": "The current batch comparison is too fragile for strong winner/loser decisions.",
    }[level]

    return {
        "title": "Comparison confidence",
        "score": round(score, 1),
        "level": level,
        "summary": summary,
        "promote_now": promote_now,
    }


def _build_batch_comparison_learning_note(
    comparison_basis: dict[str, Any] | None,
    comparison_scorecard: dict[str, Any] | None,
    comparison_explanation: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = comparison_basis or {}
    scorecard = comparison_scorecard or {}
    explanation = comparison_explanation or {}
    if not comparison.get("available"):
        return {}

    swing_factor = str(scorecard.get("swing_factor") or "").strip()
    limiting_factor = str(explanation.get("limiting_factor") or "").strip()
    current = (
        comparison.get("current_batch")
        if isinstance(comparison.get("current_batch"), dict)
        else {}
    )
    usage_goal = str(current.get("usage_goal") or "").strip()

    title = "Comparison learning note"
    plain_summary = "A leading batch is not automatically the best real-world batch unless the comparison is matched and repeatable."
    takeaway = "Use the comparison to learn what is missing, not just to pick a winner too early."
    if swing_factor == "precision":
        plain_summary = "Measured precision is currently the biggest separator between the compared batches."
        takeaway = "When precision is the swing factor, keep the setup identical and validate on target before changing the recipe."
    elif swing_factor == "evidence_quality":
        plain_summary = "Evidence quality is currently the biggest separator between the compared batches."
        takeaway = "When evidence quality is the swing factor, add cleaner matched data before trusting the leaderboard."
    elif swing_factor == "readiness":
        plain_summary = "Readiness or validation depth is currently the biggest separator between the compared batches."
        takeaway = "When readiness is the swing factor, the best next step is confirmation, not aggressive retuning."

    if limiting_factor == "field_validation" or usage_goal == "hunting":
        takeaway = "For hunting, a batch must prove realistic first-shot and field behavior before promotion is honest."
    elif usage_goal == "competition":
        takeaway = "For competition, matched repeatability matters more than one attractive single result."
    elif usage_goal == "learning":
        takeaway = "For learning, the comparison is most useful when it shows one clear reason why one batch is ahead."

    return {
        "title": title,
        "plain_summary": plain_summary,
        "takeaway": takeaway,
        "swing_factor": swing_factor,
        "limiting_factor": limiting_factor,
    }


def _build_batch_evidence_basis(
    batch: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
    sessions: list[dict[str, Any]] | None,
    chrono_stats: dict[str, Any] | None,
    smart_engine_summary: dict[str, str] | None = None,
) -> dict[str, str]:
    measured_parts: list[str] = []
    modeled_parts: list[str] = []
    recommended_parts: list[str] = []
    spread_parts: list[str] = []

    session_rows = sessions or []
    analysis_data = analysis or {}
    chrono = chrono_stats or {}
    batch_data = batch or {}
    smart_engine = smart_engine_summary or {}
    setup_label = _format_batch_setup_label(batch_data)

    if isinstance(chrono.get("avg_velocity_fps"), (int, float)) or isinstance(
        chrono.get("avg"), (int, float)
    ):
        measured_parts.append("chrono data is logged for the batch")
    if any(session.get("group_size_mm") not in (None, "") for session in session_rows):
        measured_parts.append("group data from range sessions is recorded")
    if any((session.get("notes") or "").strip() for session in session_rows):
        measured_parts.append("range notes are included in the assessment")
    primer_review_count = 0
    primer_review_images = 0
    for session in session_rows:
        analysis_payload = _parse_analysis_payload(session.get("analysis_json") or {})
        images = _extract_batch_session_primer_images(analysis_payload)
        if images:
            primer_review_count += 1
            primer_review_images += len(images)
    if primer_review_count:
        measured_parts.append(
            f"{primer_review_images} primer reference image{'s are' if primer_review_images != 1 else ' is'} linked across {primer_review_count} batch session{'s' if primer_review_count != 1 else ''}"
        )

    if (
        analysis_data.get("score") is not None
        or analysis_data.get("confidence") is not None
    ):
        modeled_parts.append("batch analysis scores trend and potential from history")
    if (
        batch_data.get("charge_weight_grains") is not None
        or batch_data.get("coal_mm") is not None
    ):
        modeled_parts.append("load setup and batch targets are used as reference")
    predicted = analysis_data.get("predicted_result_summary") or {}
    if isinstance(predicted, dict) and predicted.get("muzzle_velocity_fps") is not None:
        modeled_parts.append(
            "saved predicted velocity follows the batch for later verification"
        )
    model_match = analysis_data.get("model_match_advisory") or {}
    if isinstance(model_match, dict) and (
        model_match.get("title") or model_match.get("message")
    ):
        modeled_parts.append("the model-vs-measured check is stored for this batch")

    verification = analysis_data.get("verification_advisory") or {}
    if verification.get("title") or verification.get("message"):
        recommended_parts.append("workflow lot verification defines the control plan")
    if analysis_data.get("next_focus"):
        recommended_parts.append("the analysis engine suggests the next focus")
    elif analysis_data.get("trend_summary"):
        recommended_parts.append(
            "the trend picture is used for further recommendations"
        )
    if isinstance(model_match, dict) and model_match.get("level") in {
        "warning",
        "critical",
    }:
        recommended_parts.append(
            "the model deviation should be followed up with chrono before further tuning"
        )
    smart_summary_text = str(smart_engine.get("summary") or "").strip()
    smart_next_text = str(smart_engine.get("next") or "").strip()
    smart_gate_text = str(smart_engine.get("gate") or "").strip()
    smart_protocol_text = str(smart_engine.get("protocol") or "").strip()
    smart_hold_text = str(smart_engine.get("hold") or "").strip()
    smart_blocker_text = str(smart_engine.get("blocker") or "").strip()
    smart_confidence_text = str(smart_engine.get("confidence") or "").strip()
    smart_baseline_text = str(smart_engine.get("baseline") or "").strip()
    smart_branch_text = str(smart_engine.get("branch") or "").strip()
    if smart_summary_text:
        modeled_parts.append(
            "the local smart ammo engine scores current robustness, node fit, and harmonics"
        )
        spread_parts.append(smart_summary_text)
    if smart_next_text:
        recommended_parts.append(
            "the local smart ammo engine contributes the next test priority"
        )
        spread_parts.append(smart_next_text)
    if smart_gate_text:
        recommended_parts.append(
            "the local smart ammo engine sets a validation gate before promotion"
        )
        spread_parts.append(smart_gate_text)
    if smart_protocol_text:
        recommended_parts.append(
            "the local smart ammo engine defines a conservative test protocol"
        )
        spread_parts.append(smart_protocol_text)
    if smart_hold_text:
        recommended_parts.append(
            "the local smart ammo engine marks what should not be changed yet"
        )
        spread_parts.append(smart_hold_text)
    if smart_blocker_text:
        recommended_parts.append(
            "the local smart ammo engine exposes current blockers directly"
        )
        spread_parts.append(smart_blocker_text)
    if smart_confidence_text:
        modeled_parts.append(
            "the local smart ammo engine scores recommendation confidence and uncertainty"
        )
        spread_parts.append(smart_confidence_text)
    if smart_baseline_text:
        recommended_parts.append(
            "the local smart ammo engine shows when the setup must return to the frozen baseline"
        )
        spread_parts.append(smart_baseline_text)
    if smart_branch_text:
        modeled_parts.append(
            "the local smart ammo engine marks whether the current setup is on the frozen baseline or a custom branch"
        )
        spread_parts.append(smart_branch_text)
    metrics = (
        analysis_data.get("metrics")
        if isinstance(analysis_data.get("metrics"), dict)
        else {}
    )
    spread_hint = str(
        metrics.get("spread_signal_hint")
        or analysis_data.get("spread_signal_hint")
        or ""
    ).strip()
    spread_confidence = str(
        metrics.get("spread_confidence") or analysis_data.get("spread_confidence") or ""
    ).strip()
    spread_reason = str(
        metrics.get("spread_reason") or analysis_data.get("spread_reason") or ""
    ).strip()
    spread_note_flags = (
        metrics.get("spread_note_flags") or analysis_data.get("spread_note_flags") or []
    )
    spread_max_wind = metrics.get("spread_max_wind_mps") or analysis_data.get(
        "spread_max_wind_mps"
    )
    spread_pattern_flags = (
        metrics.get("spread_pattern_flags")
        or analysis_data.get("spread_pattern_flags")
        or []
    )
    spread_axis_ratio = metrics.get("spread_axis_ratio") or analysis_data.get(
        "spread_axis_ratio"
    )
    spread_poi_shift = metrics.get("spread_poi_shift_mm") or analysis_data.get(
        "spread_poi_shift_mm"
    )
    spread_control_plan = metrics.get("spread_control_plan") or analysis_data.get(
        "spread_control_plan"
    )
    spread_decision = metrics.get("spread_decision") or analysis_data.get(
        "spread_decision"
    )
    spread_profile_guidance = metrics.get(
        "spread_profile_guidance"
    ) or analysis_data.get("spread_profile_guidance")
    spread_evidence_quality = metrics.get(
        "spread_evidence_quality"
    ) or analysis_data.get("spread_evidence_quality")
    spread_learning_explanation = metrics.get(
        "spread_learning_explanation"
    ) or analysis_data.get("spread_learning_explanation")
    spread_capture_checklist = metrics.get(
        "spread_capture_checklist"
    ) or analysis_data.get("spread_capture_checklist")
    spread_validation_status = metrics.get(
        "spread_validation_status"
    ) or analysis_data.get("spread_validation_status")
    comparison_basis = (
        analysis_data.get("batch_comparison_basis")
        if isinstance(analysis_data.get("batch_comparison_basis"), dict)
        else {}
    )
    comparison_advisory = (
        analysis_data.get("batch_comparison_advisory")
        if isinstance(analysis_data.get("batch_comparison_advisory"), dict)
        else {}
    )
    comparison_protocol = (
        analysis_data.get("batch_comparison_protocol")
        if isinstance(analysis_data.get("batch_comparison_protocol"), dict)
        else {}
    )
    comparison_explanation = (
        analysis_data.get("batch_comparison_explanation")
        if isinstance(analysis_data.get("batch_comparison_explanation"), dict)
        else {}
    )
    comparison_verdict = (
        analysis_data.get("batch_comparison_verdict")
        if isinstance(analysis_data.get("batch_comparison_verdict"), dict)
        else {}
    )
    comparison_acceptance = (
        analysis_data.get("batch_comparison_acceptance")
        if isinstance(analysis_data.get("batch_comparison_acceptance"), dict)
        else {}
    )
    comparison_acceptance_progress = (
        analysis_data.get("batch_comparison_acceptance_progress")
        if isinstance(analysis_data.get("batch_comparison_acceptance_progress"), dict)
        else {}
    )
    comparison_next_test = (
        analysis_data.get("batch_comparison_next_test")
        if isinstance(analysis_data.get("batch_comparison_next_test"), dict)
        else {}
    )
    comparison_status_board = (
        analysis_data.get("batch_comparison_status_board")
        if isinstance(analysis_data.get("batch_comparison_status_board"), dict)
        else {}
    )
    comparison_profile_priority = (
        analysis_data.get("batch_comparison_profile_priority")
        if isinstance(analysis_data.get("batch_comparison_profile_priority"), dict)
        else {}
    )
    comparison_mission_brief = (
        analysis_data.get("batch_comparison_mission_brief")
        if isinstance(analysis_data.get("batch_comparison_mission_brief"), dict)
        else {}
    )
    comparison_portfolio = (
        analysis_data.get("batch_comparison_portfolio")
        if isinstance(analysis_data.get("batch_comparison_portfolio"), dict)
        else {}
    )
    comparison_session_strategy = (
        analysis_data.get("batch_comparison_session_strategy")
        if isinstance(analysis_data.get("batch_comparison_session_strategy"), dict)
        else {}
    )
    comparison_campaign_view = (
        analysis_data.get("batch_comparison_campaign_view")
        if isinstance(analysis_data.get("batch_comparison_campaign_view"), dict)
        else {}
    )
    comparison_action_plan = (
        analysis_data.get("batch_comparison_action_plan")
        if isinstance(analysis_data.get("batch_comparison_action_plan"), dict)
        else {}
    )
    comparison_campaign_board = (
        analysis_data.get("batch_comparison_campaign_board")
        if isinstance(analysis_data.get("batch_comparison_campaign_board"), dict)
        else {}
    )
    comparison_session_queue = (
        analysis_data.get("batch_comparison_session_queue")
        if isinstance(analysis_data.get("batch_comparison_session_queue"), dict)
        else {}
    )
    comparison_session_manifest = (
        analysis_data.get("batch_comparison_session_manifest")
        if isinstance(analysis_data.get("batch_comparison_session_manifest"), dict)
        else {}
    )
    comparison_next_session_brief = (
        analysis_data.get("batch_comparison_next_session_brief")
        if isinstance(analysis_data.get("batch_comparison_next_session_brief"), dict)
        else {}
    )
    comparison_today_plan = (
        analysis_data.get("batch_comparison_today_plan")
        if isinstance(analysis_data.get("batch_comparison_today_plan"), dict)
        else {}
    )
    comparison_workboard = (
        analysis_data.get("batch_comparison_workboard")
        if isinstance(analysis_data.get("batch_comparison_workboard"), dict)
        else {}
    )
    comparison_checklist = (
        analysis_data.get("batch_comparison_checklist")
        if isinstance(analysis_data.get("batch_comparison_checklist"), dict)
        else {}
    )
    comparison_scorecard = (
        analysis_data.get("batch_comparison_scorecard")
        if isinstance(analysis_data.get("batch_comparison_scorecard"), dict)
        else {}
    )
    comparison_confidence = (
        analysis_data.get("batch_comparison_confidence")
        if isinstance(analysis_data.get("batch_comparison_confidence"), dict)
        else {}
    )
    comparison_learning_note = (
        analysis_data.get("batch_comparison_learning_note")
        if isinstance(analysis_data.get("batch_comparison_learning_note"), dict)
        else {}
    )
    if spread_hint:
        hint_text = spread_hint
        if spread_confidence:
            hint_text += f" ({spread_confidence})"
        spread_parts.append(hint_text)
    if spread_reason:
        spread_parts.append(spread_reason)
    if spread_note_flags:
        spread_parts.append(
            f"context flags: {', '.join(str(flag) for flag in spread_note_flags)}"
        )
    if spread_max_wind not in (None, ""):
        spread_parts.append(f"max wind: {spread_max_wind} m/s")
    if spread_pattern_flags:
        spread_parts.append(
            f"pattern flags: {', '.join(str(flag) for flag in spread_pattern_flags)}"
        )
    if spread_axis_ratio not in (None, ""):
        spread_parts.append(f"axis ratio: {spread_axis_ratio}")
    if spread_poi_shift not in (None, ""):
        spread_parts.append(f"POI shift: {spread_poi_shift} mm")
    if isinstance(spread_control_plan, dict):
        control_title = str(spread_control_plan.get("title") or "").strip()
        control_action = str(spread_control_plan.get("primary_action") or "").strip()
        if control_title:
            spread_parts.append(f"control: {control_title}")
        if control_action:
            spread_parts.append(f"next control: {control_action}")
    if isinstance(spread_decision, dict):
        decision_label = str(
            spread_decision.get("label") or spread_decision.get("state") or ""
        ).strip()
        if decision_label:
            spread_parts.append(f"decision: {decision_label}")
    if isinstance(spread_profile_guidance, dict):
        profile_title = str(spread_profile_guidance.get("title") or "").strip()
        profile_emphasis = str(spread_profile_guidance.get("emphasis") or "").strip()
        if profile_title:
            spread_parts.append(f"profile: {profile_title}")
        if profile_emphasis:
            spread_parts.append(f"profile focus: {profile_emphasis}")
    if isinstance(spread_evidence_quality, dict):
        quality_level = str(spread_evidence_quality.get("level") or "").strip()
        quality_score = spread_evidence_quality.get("score")
        if quality_level:
            spread_parts.append(
                f"evidence quality: {quality_level} ({quality_score}/100)"
            )
    if isinstance(spread_learning_explanation, dict):
        lesson_title = str(spread_learning_explanation.get("title") or "").strip()
        lesson_takeaway = str(
            spread_learning_explanation.get("user_takeaway") or ""
        ).strip()
        if lesson_title:
            spread_parts.append(f"lesson: {lesson_title}")
        if lesson_takeaway:
            spread_parts.append(f"takeaway: {lesson_takeaway}")
    if isinstance(spread_capture_checklist, dict):
        checklist_title = str(spread_capture_checklist.get("title") or "").strip()
        checklist_items = (
            spread_capture_checklist.get("items")
            if isinstance(spread_capture_checklist.get("items"), list)
            else []
        )
        if checklist_title:
            spread_parts.append(f"checklist: {checklist_title}")
        first_capture = next(
            (
                str(item.get("label") or "").strip()
                for item in checklist_items
                if isinstance(item, dict) and str(item.get("label") or "").strip()
            ),
            "",
        )
        if first_capture:
            spread_parts.append(f"first capture: {first_capture}")
    if isinstance(spread_validation_status, dict):
        validation_label = str(spread_validation_status.get("label") or "").strip()
        validation_summary = str(spread_validation_status.get("summary") or "").strip()
        validation_score = spread_validation_status.get("readiness_score")
        if validation_label:
            if validation_score not in (None, ""):
                spread_parts.append(
                    f"validation: {validation_label} ({validation_score}/100)"
                )
            else:
                spread_parts.append(f"validation: {validation_label}")
        if validation_summary:
            spread_parts.append(f"validation summary: {validation_summary}")
    if comparison_basis.get("available"):
        comparison_summary = str(comparison_basis.get("summary") or "").strip()
        comparison_state = str(comparison_basis.get("ranking_state") or "").strip()
        comparison_rank = comparison_basis.get("current_rank")
        comparison_count = comparison_basis.get("count")
        top_candidates = (
            comparison_basis.get("top_candidates")
            if isinstance(comparison_basis.get("top_candidates"), list)
            else []
        )
        if comparison_state:
            spread_parts.append(f"comparison state: {comparison_state}")
        if comparison_rank not in (None, "") and comparison_count not in (None, ""):
            spread_parts.append(f"batch rank: {comparison_rank}/{comparison_count}")
        if comparison_summary:
            spread_parts.append(f"comparison: {comparison_summary}")
        leader_name = str(comparison_basis.get("leader_batch_name") or "").strip()
        leader_gap = comparison_basis.get("leader_gap_score")
        if leader_name and leader_gap not in (None, "") and comparison_rank != 1:
            spread_parts.append(
                f"comparison leader: {leader_name} ({leader_gap} score ahead)"
            )
        if top_candidates:
            first_name = str((top_candidates[0] or {}).get("batch_name") or "").strip()
            if first_name:
                spread_parts.append(f"top candidate: {first_name}")
    if comparison_advisory:
        advisory_title = str(comparison_advisory.get("title") or "").strip()
        advisory_message = str(comparison_advisory.get("message") or "").strip()
        advisory_action = str(
            comparison_advisory.get("recommended_action") or ""
        ).strip()
        if advisory_title:
            spread_parts.append(f"comparison advisory: {advisory_title}")
        if advisory_message:
            spread_parts.append(f"comparison advisory detail: {advisory_message}")
        if advisory_action:
            spread_parts.append(f"comparison next gate: {advisory_action}")
    if comparison_protocol:
        protocol_title = str(comparison_protocol.get("title") or "").strip()
        protocol_action = str(comparison_protocol.get("primary_action") or "").strip()
        protocol_plan = str(comparison_protocol.get("shot_plan") or "").strip()
        if protocol_title:
            spread_parts.append(f"comparison protocol: {protocol_title}")
        if protocol_action:
            spread_parts.append(f"comparison action: {protocol_action}")
        if protocol_plan:
            spread_parts.append(f"comparison plan: {protocol_plan}")
    if comparison_explanation:
        explanation_factor = str(
            comparison_explanation.get("limiting_factor") or ""
        ).strip()
        explanation_reason = str(comparison_explanation.get("reason") or "").strip()
        explanation_measurement = str(
            comparison_explanation.get("next_measurement") or ""
        ).strip()
        if explanation_factor:
            spread_parts.append(f"comparison bottleneck: {explanation_factor}")
        if explanation_reason:
            spread_parts.append(f"comparison why: {explanation_reason}")
        if explanation_measurement:
            spread_parts.append(
                f"comparison next measurement: {explanation_measurement}"
            )
    if comparison_verdict:
        verdict_label = str(comparison_verdict.get("label") or "").strip()
        verdict_summary = str(comparison_verdict.get("summary") or "").strip()
        if verdict_label:
            spread_parts.append(f"comparison verdict: {verdict_label}")
        if verdict_summary:
            spread_parts.append(f"comparison verdict why: {verdict_summary}")
    if comparison_acceptance:
        acceptance_label = str(comparison_acceptance.get("label") or "").strip()
        acceptance_summary = str(comparison_acceptance.get("summary") or "").strip()
        acceptance_gate = str(comparison_acceptance.get("next_gate") or "").strip()
        acceptance_gaps = (
            comparison_acceptance.get("remaining_gaps")
            if isinstance(comparison_acceptance.get("remaining_gaps"), list)
            else []
        )
        if acceptance_label:
            spread_parts.append(f"comparison acceptance: {acceptance_label}")
        if acceptance_summary:
            spread_parts.append(f"comparison acceptance why: {acceptance_summary}")
        if acceptance_gate:
            spread_parts.append(f"comparison acceptance gate: {acceptance_gate}")
        first_gap = next(
            (str(item).strip() for item in acceptance_gaps if str(item).strip()), ""
        )
        if first_gap:
            spread_parts.append(f"comparison acceptance gap: {first_gap}")
    if comparison_acceptance_progress:
        acceptance_progress_level = str(
            comparison_acceptance_progress.get("level") or ""
        ).strip()
        acceptance_progress_score = comparison_acceptance_progress.get("score")
        acceptance_progress_summary = str(
            comparison_acceptance_progress.get("summary") or ""
        ).strip()
        acceptance_progress_target = str(
            comparison_acceptance_progress.get("next_target") or ""
        ).strip()
        if acceptance_progress_level:
            if acceptance_progress_score not in (None, ""):
                spread_parts.append(
                    f"acceptance progress: {acceptance_progress_level} ({acceptance_progress_score}/100)"
                )
            else:
                spread_parts.append(f"acceptance progress: {acceptance_progress_level}")
        if acceptance_progress_summary:
            spread_parts.append(
                f"acceptance progress why: {acceptance_progress_summary}"
            )
        if acceptance_progress_target:
            spread_parts.append(f"acceptance next target: {acceptance_progress_target}")
    if comparison_next_test:
        next_test_title = str(comparison_next_test.get("title") or "").strip()
        next_test_action = str(comparison_next_test.get("primary_action") or "").strip()
        next_test_summary = str(comparison_next_test.get("summary") or "").strip()
        next_test_check = str(comparison_next_test.get("check_first") or "").strip()
        if next_test_title:
            spread_parts.append(f"comparison next test: {next_test_title}")
        if next_test_action:
            spread_parts.append(f"comparison next test action: {next_test_action}")
        if next_test_summary:
            spread_parts.append(f"comparison next test why: {next_test_summary}")
        if next_test_check:
            spread_parts.append(f"comparison next test first check: {next_test_check}")
    if comparison_status_board:
        status_headline = str(comparison_status_board.get("headline") or "").strip()
        status_summary = str(comparison_status_board.get("summary") or "").strip()
        status_band = str(comparison_status_board.get("readiness_band") or "").strip()
        if status_headline:
            spread_parts.append(f"comparison board: {status_headline}")
        if status_band:
            spread_parts.append(f"comparison readiness band: {status_band}")
        if status_summary:
            spread_parts.append(f"comparison board summary: {status_summary}")
    if comparison_profile_priority:
        profile_title = str(comparison_profile_priority.get("title") or "").strip()
        profile_emphasis = str(
            comparison_profile_priority.get("emphasis") or ""
        ).strip()
        profile_guardrail = str(
            comparison_profile_priority.get("guardrail") or ""
        ).strip()
        if profile_title:
            spread_parts.append(f"comparison profile: {profile_title}")
        if profile_emphasis:
            spread_parts.append(f"comparison profile focus: {profile_emphasis}")
        if profile_guardrail:
            spread_parts.append(f"comparison guardrail: {profile_guardrail}")
    if comparison_mission_brief:
        mission_title = str(comparison_mission_brief.get("title") or "").strip()
        mission_text = str(comparison_mission_brief.get("mission") or "").strip()
        mission_action = str(
            comparison_mission_brief.get("primary_action") or ""
        ).strip()
        mission_success = str(
            comparison_mission_brief.get("success_marker") or ""
        ).strip()
        if mission_title:
            spread_parts.append(f"comparison mission: {mission_title}")
        if mission_text:
            spread_parts.append(f"comparison mission brief: {mission_text}")
        if mission_action:
            spread_parts.append(f"comparison mission action: {mission_action}")
        if mission_success:
            spread_parts.append(f"comparison success marker: {mission_success}")
    if comparison_portfolio:
        portfolio_title = str(comparison_portfolio.get("title") or "").strip()
        portfolio_focus = str(comparison_portfolio.get("focus") or "").strip()
        portfolio_headline = str(
            comparison_portfolio.get("status_headline") or ""
        ).strip()
        if portfolio_title:
            spread_parts.append(f"comparison portfolio: {portfolio_title}")
        if portfolio_headline:
            spread_parts.append(f"comparison portfolio state: {portfolio_headline}")
        if portfolio_focus:
            spread_parts.append(f"comparison portfolio focus: {portfolio_focus}")
    if comparison_session_strategy:
        strategy_title = str(comparison_session_strategy.get("title") or "").strip()
        strategy_mode = str(comparison_session_strategy.get("mode") or "").strip()
        strategy_objective = str(
            comparison_session_strategy.get("objective") or ""
        ).strip()
        if strategy_title:
            spread_parts.append(f"comparison session strategy: {strategy_title}")
        if strategy_mode:
            spread_parts.append(f"comparison session mode: {strategy_mode}")
        if strategy_objective:
            spread_parts.append(f"comparison session objective: {strategy_objective}")
    if comparison_campaign_view:
        campaign_title = str(comparison_campaign_view.get("title") or "").strip()
        campaign_summary = str(comparison_campaign_view.get("summary") or "").strip()
        if campaign_title:
            spread_parts.append(f"comparison campaign: {campaign_title}")
        if campaign_summary:
            spread_parts.append(f"comparison campaign summary: {campaign_summary}")
    if comparison_action_plan:
        plan_title = str(comparison_action_plan.get("title") or "").strip()
        plan_summary = str(comparison_action_plan.get("summary") or "").strip()
        plan_action = str(comparison_action_plan.get("primary_action") or "").strip()
        if plan_title:
            spread_parts.append(f"comparison action plan: {plan_title}")
        if plan_summary:
            spread_parts.append(f"comparison action summary: {plan_summary}")
        if plan_action:
            spread_parts.append(f"comparison action next: {plan_action}")
    if comparison_campaign_board:
        board_title = str(comparison_campaign_board.get("title") or "").strip()
        board_summary = str(comparison_campaign_board.get("summary") or "").strip()
        board_preview = (
            comparison_campaign_board.get("preview")
            if isinstance(comparison_campaign_board.get("preview"), list)
            else []
        )
        if board_title:
            spread_parts.append(f"comparison campaign board: {board_title}")
        if board_summary:
            spread_parts.append(f"comparison campaign board summary: {board_summary}")
        if board_preview:
            spread_parts.append(
                f"comparison board preview: {' | '.join(str(item).strip() for item in board_preview[:3] if str(item).strip())}"
            )
    if comparison_session_queue:
        queue_title = str(comparison_session_queue.get("title") or "").strip()
        queue_mode = str(comparison_session_queue.get("mode") or "").strip()
        queue_first = str(
            comparison_session_queue.get("first_batch_name") or ""
        ).strip()
        queue_preview = (
            comparison_session_queue.get("preview")
            if isinstance(comparison_session_queue.get("preview"), list)
            else []
        )
        if queue_title:
            spread_parts.append(f"comparison session queue: {queue_title}")
        if queue_mode:
            spread_parts.append(f"comparison queue mode: {queue_mode}")
        if queue_first:
            spread_parts.append(f"comparison queue first batch: {queue_first}")
        if queue_preview:
            spread_parts.append(
                f"comparison queue preview: {' | '.join(str(item).strip() for item in queue_preview[:3] if str(item).strip())}"
            )
    if comparison_session_manifest:
        manifest_title = str(comparison_session_manifest.get("title") or "").strip()
        manifest_summary = str(comparison_session_manifest.get("summary") or "").strip()
        manifest_bucket = str(
            comparison_session_manifest.get("primary_bucket") or ""
        ).strip()
        manifest_first = str(
            comparison_session_manifest.get("first_batch_name") or ""
        ).strip()
        manifest_preview = (
            comparison_session_manifest.get("queue_preview")
            if isinstance(comparison_session_manifest.get("queue_preview"), list)
            else []
        )
        lane_summaries = (
            comparison_session_manifest.get("lane_summaries")
            if isinstance(comparison_session_manifest.get("lane_summaries"), list)
            else []
        )
        if manifest_title:
            spread_parts.append(f"comparison session manifest: {manifest_title}")
        if manifest_summary:
            spread_parts.append(f"comparison manifest summary: {manifest_summary}")
        if manifest_bucket:
            spread_parts.append(f"comparison manifest bucket: {manifest_bucket}")
        if manifest_first:
            spread_parts.append(f"comparison manifest first batch: {manifest_first}")
        if manifest_preview:
            spread_parts.append(
                f"comparison manifest preview: {' | '.join(str(item).strip() for item in manifest_preview[:3] if str(item).strip())}"
            )
        if lane_summaries:
            spread_parts.append(
                "comparison manifest lanes: "
                + " | ".join(
                    str(item.get("summary") or "").strip()
                    for item in lane_summaries[:4]
                    if isinstance(item, dict) and str(item.get("summary") or "").strip()
                )
            )
    if comparison_next_session_brief:
        brief_title = str(comparison_next_session_brief.get("title") or "").strip()
        brief_summary = str(comparison_next_session_brief.get("summary") or "").strip()
        brief_first = str(
            comparison_next_session_brief.get("first_batch_name") or ""
        ).strip()
        brief_bucket = str(
            comparison_next_session_brief.get("primary_bucket") or ""
        ).strip()
        brief_hold = str(comparison_next_session_brief.get("hold_back") or "").strip()
        if brief_title:
            spread_parts.append(f"comparison next session brief: {brief_title}")
        if brief_summary:
            spread_parts.append(f"comparison next session summary: {brief_summary}")
        if brief_first:
            spread_parts.append(f"comparison next session first batch: {brief_first}")
        if brief_bucket:
            spread_parts.append(f"comparison next session bucket: {brief_bucket}")
        if brief_hold:
            spread_parts.append(f"comparison next session hold-back: {brief_hold}")
    if comparison_today_plan:
        today_title = str(comparison_today_plan.get("title") or "").strip()
        today_summary = str(comparison_today_plan.get("summary") or "").strip()
        today_first = str(comparison_today_plan.get("first_batch_name") or "").strip()
        today_bucket = str(comparison_today_plan.get("primary_bucket") or "").strip()
        if today_title:
            spread_parts.append(f"comparison today plan: {today_title}")
        if today_summary:
            spread_parts.append(f"comparison today summary: {today_summary}")
        if today_first:
            spread_parts.append(f"comparison today first batch: {today_first}")
        if today_bucket:
            spread_parts.append(f"comparison today bucket: {today_bucket}")
    if comparison_workboard:
        workboard_title = str(comparison_workboard.get("title") or "").strip()
        workboard_summary = str(comparison_workboard.get("summary") or "").strip()
        workboard_status = str(comparison_workboard.get("status_label") or "").strip()
        workboard_first = str(
            comparison_workboard.get("first_batch_name") or ""
        ).strip()
        workboard_bucket = str(comparison_workboard.get("primary_bucket") or "").strip()
        workboard_hold = str(comparison_workboard.get("hold_back") or "").strip()
        if workboard_title:
            spread_parts.append(f"comparison workboard: {workboard_title}")
        if workboard_summary:
            spread_parts.append(f"comparison workboard summary: {workboard_summary}")
        if workboard_status:
            spread_parts.append(f"comparison workboard status: {workboard_status}")
        if workboard_first:
            spread_parts.append(f"comparison workboard first batch: {workboard_first}")
        if workboard_bucket:
            spread_parts.append(f"comparison workboard bucket: {workboard_bucket}")
        if workboard_hold:
            spread_parts.append(f"comparison workboard hold-back: {workboard_hold}")
    if comparison_checklist:
        checklist_title = str(comparison_checklist.get("title") or "").strip()
        highest_priority = str(
            comparison_checklist.get("highest_priority") or ""
        ).strip()
        if checklist_title:
            spread_parts.append(f"comparison checklist: {checklist_title}")
        if highest_priority:
            spread_parts.append(f"comparison first check: {highest_priority}")
    if comparison_scorecard:
        scorecard_factor = str(comparison_scorecard.get("swing_factor") or "").strip()
        scorecard_summary = str(comparison_scorecard.get("summary") or "").strip()
        delta_precision = comparison_scorecard.get("delta_precision")
        delta_quality = comparison_scorecard.get("delta_evidence_quality")
        delta_readiness = comparison_scorecard.get("delta_readiness")
        if scorecard_factor:
            spread_parts.append(f"comparison swing factor: {scorecard_factor}")
        if scorecard_summary:
            spread_parts.append(f"comparison scorecard: {scorecard_summary}")
        if delta_precision not in (None, ""):
            spread_parts.append(f"precision delta: {delta_precision}")
        if delta_quality not in (None, ""):
            spread_parts.append(f"evidence delta: {delta_quality}")
        if delta_readiness not in (None, ""):
            spread_parts.append(f"readiness delta: {delta_readiness}")
    if comparison_confidence:
        confidence_level = str(comparison_confidence.get("level") or "").strip()
        confidence_score = comparison_confidence.get("score")
        confidence_summary = str(comparison_confidence.get("summary") or "").strip()
        if confidence_level:
            spread_parts.append(
                f"comparison confidence: {confidence_level} ({confidence_score}/100)"
            )
        if confidence_summary:
            spread_parts.append(f"comparison confidence why: {confidence_summary}")
    if comparison_learning_note:
        learning_summary = str(
            comparison_learning_note.get("plain_summary") or ""
        ).strip()
        learning_takeaway = str(comparison_learning_note.get("takeaway") or "").strip()
        if learning_summary:
            spread_parts.append(f"comparison lesson: {learning_summary}")
        if learning_takeaway:
            spread_parts.append(f"comparison takeaway: {learning_takeaway}")

    if not measured_parts:
        measured_parts.append("the measurement basis is still thin for this batch")
    if not modeled_parts:
        modeled_parts.append("no clear batch model or trend analysis is available yet")
    if not recommended_parts:
        recommended_parts.append(
            "further guidance remains provisional until more data is logged"
        )

    message = (
        (f"Setup: {setup_label}. " if setup_label else "")
        + f"Measured: {', '.join(measured_parts)}. "
        + f"Modeled: {', '.join(modeled_parts)}. "
        + (f"Spread: {' '.join(spread_parts)}. " if spread_parts else "")
        + f"Recommended: {', '.join(recommended_parts)}."
    )
    return {"title": tr("bw_evidence_basis"), "message": message}


def _store_active_batch_context(db, batch: Dict[str, Any]) -> None:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    snapshot_text = batch.get("component_snapshot_json") or "{}"
    try:
        snapshot = json.loads(snapshot_text)
    except Exception:
        snapshot = {}

    powder_entry = snapshot.get("powder") if isinstance(snapshot, dict) else {}
    powder_id = batch.get("powder_id")
    powder_name = ""
    powder_lot_number = ""
    component_lot_id = None
    if isinstance(powder_entry, dict):
        powder_id = powder_entry.get("id") or powder_id
        powder_name = str(powder_entry.get("name") or "").strip()
        powder_lot_number = str(powder_entry.get("lot_number") or "").strip()
    if powder_id not in (None, "") and not powder_lot_number:
        rows = db.execute_query(
            """
            SELECT id, lot_number
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY is_active DESC, created_date DESC
            LIMIT 1
            """,
            (int(powder_id),),
        )
        if rows:
            component_lot_id = rows[0].get("id")
            powder_lot_number = str(rows[0].get("lot_number") or "").strip()
    for key, value in {
        "batch_id": batch.get("id"),
        "batch_number": batch.get("batch_number"),
        "batch_name": batch.get("batch_name"),
        "powder_id": powder_id,
        "powder_name": powder_name,
        "powder_lot_number": powder_lot_number,
        "powder_component_lot_id": component_lot_id,
    }.items():
        settings.setValue(f"batch_context/{key}", value)
    settings.sync()


class ManualChronographDialog(QDialog):
    """Simple paste-in dialog for manual chronograph values."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("bw_manual_chrono_entry"))
        self.resize(520, 360)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(tr("bw_manual_chrono_help")))
        self.session_name = QLineEdit()
        self.session_name.setPlaceholderText(tr("bw_session_name"))
        layout.addWidget(self.session_name)
        self.velocities = QTextEdit()
        self.velocities.setPlaceholderText("820.1\n818.5\n823.0")
        layout.addWidget(self.velocities, 1)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(tr("bw_optional_notes"))
        self.notes.setMaximumHeight(90)
        layout.addWidget(self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def parsed_velocities(self) -> List[float]:
        text = (self.velocities.toPlainText() or "").strip().replace(",", " ")
        values: List[float] = []
        for token in text.split():
            try:
                values.append(float(token))
            except Exception:
                continue
        return values


class BatchWorkspace(QWidget):
    """Central workspace for one batch lifecycle."""

    def __init__(self, parent=None, batch_id: Optional[int] = None):
        super().__init__(parent)
        self.db = get_database()
        self.current_batch_id: Optional[int] = None
        self._current_batch: Dict[str, Any] = {}
        self._current_notes: List[Dict[str, Any]] = []
        self._current_sessions: List[Dict[str, Any]] = []
        self._current_attachments: List[Dict[str, Any]] = []
        self._batch_media_dir: Optional[Path] = None
        self._latest_workboard_display: Dict[str, str] = {}
        self._workboard_completed_lanes_by_batch: Dict[int, set[str]] = {}
        self._workboard_selected_lane_by_batch: Dict[int, str] = {}
        self.init_ui()
        self.refresh_batches(select_batch_id=batch_id)

    def init_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        root.addWidget(splitter, 1)

        splitter.addWidget(self._build_list_panel())
        splitter.addWidget(self._build_detail_panel())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)

    def _build_list_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel(tr("bw_title"))
        title.setProperty("variant", "cardTitle")
        layout.addWidget(title)

        subtitle = QLabel(tr("bw_subtitle"))
        subtitle.setWordWrap(True)
        subtitle.setProperty("variant", "cardSubtitle")
        layout.addWidget(subtitle)

        batch_focus = _get_active_batch_focus()
        if batch_focus.get("focus") == "workflow_next_step":
            focus_text = batch_focus.get("reason") or (tr("bw_ready_reason"))
            self.focus_label = QLabel(f"{tr('bw_next_step')}: {focus_text}")
            self.focus_label.setWordWrap(True)
            self.focus_label.setProperty("variant", "cardSubtitle")
            self.focus_label.setStyleSheet(
                "background-color: #eaf7ea; color: #256029; border: 1px solid #b7e1b9; "
                "border-radius: 6px; padding: 8px;"
            )
            layout.addWidget(self.focus_label)

        verification = _get_active_workflow_verification_advisory(self.db)
        if verification.get("message"):
            self.verification_label = QLabel(
                f"{verification.get('title') or tr('bw_combined_lot_verification')}: {verification.get('message')}"
            )
            self.verification_label.setWordWrap(True)
            self.verification_label.setProperty("variant", "cardSubtitle")
            level = verification.get("level")
            if level == "critical":
                self.verification_label.setStyleSheet(
                    "background-color: #fee2e2; color: #991b1b; border: 1px solid #f0b4b4; "
                    "border-radius: 6px; padding: 8px;"
                )
            elif level == "warning":
                self.verification_label.setStyleSheet(
                    "background-color: #fef3c7; color: #92400e; border: 1px solid #f6d98b; "
                    "border-radius: 6px; padding: 8px;"
                )
            else:
                self.verification_label.setStyleSheet(
                    "background-color: #eaf7ea; color: #256029; border: 1px solid #b7e1b9; "
                    "border-radius: 6px; padding: 8px;"
                )
            layout.addWidget(self.verification_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("bw_search_batches"))
        self.search_input.textChanged.connect(lambda: self.refresh_batches())
        layout.addWidget(self.search_input)

        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(5)
        self.batch_table.setHorizontalHeaderLabels(
            [
                tr("bw_batch_col"),
                tr("bw_rifle_col"),
                tr("bw_status_col"),
                tr("bw_created_col"),
                tr("bw_activity_col"),
            ]
        )
        self.batch_table.horizontalHeader().setSectionResizeMode(  # type: ignore[union-attr]
            QHeaderView.ResizeMode.Stretch
        )
        self.batch_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.batch_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.batch_table.itemSelectionChanged.connect(self._on_batch_selection_changed)
        layout.addWidget(self.batch_table, 1)

        button_row = QHBoxLayout()
        new_btn = QPushButton(tr("bw_new_batch"))
        new_btn.clicked.connect(self.create_batch_dialog)
        button_row.addWidget(new_btn)

        refresh_btn = QPushButton(tr("bw_refresh"))
        refresh_btn.clicked.connect(self.refresh_batches)
        button_row.addWidget(refresh_btn)

        open_btn = QPushButton(tr("bw_open"))
        open_btn.clicked.connect(self._open_selected_batch)
        button_row.addWidget(open_btn)
        layout.addLayout(button_row)

        return panel

    def _build_detail_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.header_label = QLabel(tr("bw_select_batch"))
        self.header_label.setProperty("variant", "cardTitle")
        layout.addWidget(self.header_label)

        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(True)
        self.meta_label.setProperty("variant", "cardSubtitle")
        layout.addWidget(self.meta_label)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.tabs.addTab(self._build_overview_tab(), tr("bw_overview"))
        self.tabs.addTab(self._build_notes_tab(), tr("bw_notes"))
        self.tabs.addTab(self._build_sessions_tab(), tr("bw_sessions"))
        self.tabs.addTab(self._build_photos_tab(), tr("bw_photos"))
        self.tabs.addTab(self._build_analysis_tab(), tr("bw_analysis"))

        return panel

    def _build_overview_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        grid = QFormLayout()
        self.label_batch_number = QLabel("-")
        self.label_batch_name = QLabel("-")
        self.label_batch_rifle = QLabel("-")
        self.label_batch_context = QLabel("-")
        self.label_batch_status = QLabel("-")
        self.label_batch_created = QLabel("-")
        self.label_batch_updated = QLabel("-")
        self.label_batch_components = QLabel("-")
        self.label_batch_counts = QLabel("-")
        self.label_batch_target = QLabel("-")
        self.label_batch_analysis = QLabel("-")

        for label in [
            self.label_batch_number,
            self.label_batch_name,
            self.label_batch_rifle,
            self.label_batch_context,
            self.label_batch_status,
            self.label_batch_created,
            self.label_batch_updated,
            self.label_batch_components,
            self.label_batch_counts,
            self.label_batch_target,
            self.label_batch_analysis,
        ]:
            label.setWordWrap(True)

        grid.addRow(tr("bw_batch_number"), self.label_batch_number)
        grid.addRow(tr("bw_name"), self.label_batch_name)
        grid.addRow(tr("bw_rifle"), self.label_batch_rifle)
        grid.addRow(tr("bw_project_profile"), self.label_batch_context)
        grid.addRow(tr("bw_status_col"), self.label_batch_status)
        grid.addRow(tr("bw_created"), self.label_batch_created)
        grid.addRow(tr("bw_updated"), self.label_batch_updated)
        grid.addRow(tr("bw_components"), self.label_batch_components)
        grid.addRow(tr("bw_history"), self.label_batch_counts)
        grid.addRow(tr("bw_target_setup"), self.label_batch_target)
        grid.addRow(tr("bw_latest_analysis"), self.label_batch_analysis)
        layout.addLayout(grid)

        self.snapshot_text = QTextEdit()
        self.snapshot_text.setReadOnly(True)
        self.snapshot_text.setPlaceholderText(tr("bw_snapshot_placeholder"))
        layout.addWidget(self.snapshot_text, 1)

        controls = QHBoxLayout()
        self.status_combo = QComboBox()
        self.status_combo.addItems(
            ["active", "tested", "optimized", "finalized", "archived"]
        )
        controls.addWidget(QLabel(tr("bw_status_col")))
        controls.addWidget(self.status_combo)

        save_btn = QPushButton(tr("bw_save_status"))
        save_btn.clicked.connect(self._save_batch_status)
        controls.addWidget(save_btn)

        finalize_btn = QPushButton(tr("bw_mark_finished"))
        finalize_btn.clicked.connect(self._finalize_batch)
        controls.addWidget(finalize_btn)

        controls.addStretch()
        layout.addLayout(controls)

        return widget

    def _build_notes_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        self.notes_list = QListWidget()
        layout.addWidget(self.notes_list, 2)

        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText(tr("bw_note_title_placeholder"))
        layout.addWidget(self.note_title)

        self.note_text = QTextEdit()
        self.note_text.setPlaceholderText(tr("bw_note_text_placeholder"))
        self.note_text.setMaximumHeight(120)
        layout.addWidget(self.note_text)

        buttons = QHBoxLayout()
        add_note_btn = QPushButton(tr("bw_save_note"))
        add_note_btn.clicked.connect(self._add_note)
        buttons.addWidget(add_note_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

        return widget

    def _build_sessions_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        self.session_prefill_hint = QLabel("")
        self.session_prefill_hint.setWordWrap(True)
        self.session_prefill_hint.setStyleSheet(
            "background-color: #eaf4ff; color: #1d4ed8; border: 1px solid #bfdbfe; "
            "border-radius: 6px; padding: 8px;"
        )
        self.session_prefill_hint.hide()
        layout.addWidget(self.session_prefill_hint)

        form_group = QGroupBox(tr("bw_new_range_session"))
        form = QFormLayout(form_group)

        self.session_name = QLineEdit()
        self.session_name.setPlaceholderText(tr("bw_session_name"))
        form.addRow(tr("bw_name_field"), self.session_name)

        self.session_date = QDateEdit()
        self.session_date.setCalendarPopup(True)
        self.session_date.setDate(QDate.currentDate())
        self.session_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow(tr("bw_date"), self.session_date)

        self.session_distance = QSpinBox()
        self.session_distance.setRange(25, 2000)
        self.session_distance.setValue(100)
        self.session_distance.setSuffix(" m")
        form.addRow(tr("bw_distance"), self.session_distance)

        self.session_temp = QDoubleSpinBox()
        self.session_temp.setRange(-40.0, 60.0)
        self.session_temp.setDecimals(1)
        self.session_temp.setSuffix(" C")
        form.addRow(tr("bw_temperature"), self.session_temp)

        self.session_wind = QDoubleSpinBox()
        self.session_wind.setRange(0.0, 50.0)
        self.session_wind.setDecimals(1)
        self.session_wind.setSuffix(" m/s")
        form.addRow(tr("bw_wind"), self.session_wind)

        self.session_humidity = QSpinBox()
        self.session_humidity.setRange(0, 100)
        self.session_humidity.setSuffix(" %")
        form.addRow(tr("bw_humidity"), self.session_humidity)

        self.session_group_mm = QDoubleSpinBox()
        self.session_group_mm.setRange(0.0, 500.0)
        self.session_group_mm.setDecimals(1)
        self.session_group_mm.setSuffix(" mm")
        form.addRow(tr("bw_group_size_mm"), self.session_group_mm)

        self.session_group_moa = QDoubleSpinBox()
        self.session_group_moa.setRange(0.0, 20.0)
        self.session_group_moa.setDecimals(3)
        self.session_group_moa.setSuffix(" MOA")
        form.addRow(tr("bw_group_size_moa"), self.session_group_moa)

        self.session_shots = QSpinBox()
        self.session_shots.setRange(1, 100)
        self.session_shots.setValue(5)
        form.addRow(tr("bw_shot_count"), self.session_shots)

        self.session_notes = QTextEdit()
        self.session_notes.setPlaceholderText(tr("bw_range_notes_placeholder"))
        self.session_notes.setMaximumHeight(90)
        form.addRow(tr("bw_notes_field"), self.session_notes)

        primer_group = QGroupBox(tr("bw_primer_image_title"))
        primer_form = QFormLayout(primer_group)

        self.session_enable_primer_review = QCheckBox(tr("bw_primer_image_enable"))
        self.session_enable_primer_review.setChecked(False)
        self.session_enable_primer_review.toggled.connect(
            self._set_session_primer_review_enabled
        )
        primer_form.addRow(self.session_enable_primer_review)

        primer_path_layout = QHBoxLayout()
        self.session_primer_image_path = QLineEdit()
        self.session_primer_image_path.setPlaceholderText(
            tr("bw_primer_image_path_placeholder")
        )
        self.session_primer_image_path.setReadOnly(True)
        primer_path_layout.addWidget(self.session_primer_image_path)
        self.session_primer_image_browse_btn = QPushButton(tr("bw_primer_image_browse"))
        self.session_primer_image_browse_btn.clicked.connect(
            self._browse_session_primer_image
        )
        primer_path_layout.addWidget(self.session_primer_image_browse_btn)
        primer_form.addRow(tr("bw_primer_image_path"), primer_path_layout)

        self.session_primer_image_quality = QComboBox()
        self.session_primer_image_quality.addItem(
            tr("safety_dashboard_primer_image_quality_unknown"), ""
        )
        self.session_primer_image_quality.addItem(
            tr("safety_dashboard_primer_image_quality_poor"), "poor"
        )
        self.session_primer_image_quality.addItem(
            tr("safety_dashboard_primer_image_quality_ok"), "ok"
        )
        self.session_primer_image_quality.addItem(
            tr("safety_dashboard_primer_image_quality_good"), "good"
        )
        primer_form.addRow(
            tr("bw_primer_image_quality"), self.session_primer_image_quality
        )

        self.session_primer_image_confidence = QComboBox()
        self.session_primer_image_confidence.addItem(
            tr("safety_dashboard_primer_image_confidence_low"), "low"
        )
        self.session_primer_image_confidence.addItem(
            tr("safety_dashboard_primer_image_confidence_medium"), "medium"
        )
        self.session_primer_image_confidence.addItem(
            tr("safety_dashboard_primer_image_confidence_high"), "high"
        )
        self.session_primer_image_confidence.setCurrentIndex(1)
        primer_form.addRow(
            tr("bw_primer_image_confidence"), self.session_primer_image_confidence
        )

        self.session_primer_image_observation = QTextEdit()
        self.session_primer_image_observation.setMaximumHeight(70)
        self.session_primer_image_observation.setPlaceholderText(
            tr("bw_primer_image_observation_placeholder")
        )
        primer_form.addRow(
            tr("bw_primer_image_observation"), self.session_primer_image_observation
        )

        self._session_primer_review_widgets = [
            self.session_primer_image_path,
            self.session_primer_image_browse_btn,
            self.session_primer_image_quality,
            self.session_primer_image_confidence,
            self.session_primer_image_observation,
        ]
        self._set_session_primer_review_enabled(False)

        form.addRow(primer_group)

        self.session_subsonic_group = QGroupBox("Subsonic Observations")
        self.session_subsonic_group.setCheckable(False)
        self.session_subsonic_group.setVisible(False)
        sub_form = QFormLayout(self.session_subsonic_group)

        self.session_cycling_status = QComboBox()
        self.session_cycling_status.addItem("Not Assessed", "")
        self.session_cycling_status.addItem("Cycled", "cycled")
        self.session_cycling_status.addItem("Marginal", "marginal")
        self.session_cycling_status.addItem("Did Not Cycle", "failed")
        sub_form.addRow("Cycling", self.session_cycling_status)

        self.session_sonic_crack = QCheckBox("Audible sonic crack")
        sub_form.addRow("Sound", self.session_sonic_crack)

        self.session_keyhole = QCheckBox("Keyhole / signs of tumbling")
        sub_form.addRow("Stability", self.session_keyhole)

        self.session_suppressor_used = QCheckBox("Tested with suppressor")
        sub_form.addRow("Setup", self.session_suppressor_used)

        layout.addWidget(self.session_subsonic_group)

        layout.addWidget(form_group)

        controls = QHBoxLayout()
        add_session_btn = QPushButton(tr("bw_save_session"))
        add_session_btn.clicked.connect(self._add_session)
        controls.addWidget(add_session_btn)

        import_btn = QPushButton(tr("bw_import_chrono_csv"))
        import_btn.clicked.connect(self._import_chrono_csv)
        controls.addWidget(import_btn)

        manual_btn = QPushButton(tr("bw_add_chrono_manually"))
        manual_btn.clicked.connect(self._manual_chrono_entry)
        controls.addWidget(manual_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(7)
        self.sessions_table.setHorizontalHeaderLabels(
            [
                tr("bw_session_date_col"),
                tr("bw_session_type_col"),
                tr("bw_distance_col"),
                tr("bw_group_col"),
                tr("bw_shots_col"),
                tr("bw_chrono_col"),
                tr("bw_note_col"),
            ]
        )
        self.sessions_table.horizontalHeader().setSectionResizeMode(  # type: ignore[union-attr]
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.sessions_table, 1)

        return widget

    def _build_photos_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QHBoxLayout(widget)

        left = QVBoxLayout()
        self.attachments_list = QListWidget()
        self.attachments_list.currentItemChanged.connect(self._show_attachment_preview)
        left.addWidget(self.attachments_list, 1)

        photo_buttons = QHBoxLayout()
        add_photo_btn = QPushButton(tr("bw_add_photos"))
        add_photo_btn.clicked.connect(self._add_photos)
        photo_buttons.addWidget(add_photo_btn)

        refresh_preview_btn = QPushButton(tr("bw_refresh"))
        refresh_preview_btn.clicked.connect(self._refresh_attachment_preview)
        photo_buttons.addWidget(refresh_preview_btn)
        left.addLayout(photo_buttons)

        layout.addLayout(left, 2)

        right = QVBoxLayout()
        self.photo_preview = QLabel(tr("bw_select_image_preview"))
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setMinimumSize(360, 320)
        self.photo_preview.setStyleSheet(
            "QLabel { background: #111; color: #ddd; border: 1px solid #444; }"
        )
        right.addWidget(self.photo_preview, 1)
        self.photo_caption = QLabel("")
        self.photo_caption.setWordWrap(True)
        right.addWidget(self.photo_caption)
        layout.addLayout(right, 3)

        return widget

    def _build_analysis_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        summary_box = QGroupBox(tr("bw_key_findings"))
        summary_form = QFormLayout(summary_box)
        self.analysis_score_label = QLabel("-")
        self.analysis_confidence_label = QLabel("-")
        self.analysis_potential_label = QLabel("-")
        self.analysis_trend_label = QLabel("-")
        self.analysis_focus_label = QLabel("-")
        self.analysis_basis_label = QLabel("-")
        for label in (
            self.analysis_score_label,
            self.analysis_confidence_label,
            self.analysis_potential_label,
            self.analysis_trend_label,
            self.analysis_focus_label,
            self.analysis_basis_label,
        ):
            label.setWordWrap(True)
        summary_form.addRow(tr("bw_score"), self.analysis_score_label)
        summary_form.addRow(tr("bw_confidence"), self.analysis_confidence_label)
        summary_form.addRow(tr("bw_potential"), self.analysis_potential_label)
        summary_form.addRow(tr("bw_trend"), self.analysis_trend_label)
        summary_form.addRow(tr("bw_next_focus"), self.analysis_focus_label)
        summary_form.addRow(f"{tr('bw_evidence_basis')}:", self.analysis_basis_label)
        layout.addWidget(summary_box)

        workboard_box = QGroupBox("Comparison Workboard")
        workboard_layout = QVBoxLayout(workboard_box)
        self.analysis_workboard_banner_label = QLabel("-")
        self.analysis_workboard_banner_label.setWordWrap(True)
        self.analysis_workboard_banner_label.setStyleSheet(
            "background-color: #f8fafc; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; font-weight: 600;"
        )
        workboard_layout.addWidget(self.analysis_workboard_banner_label)
        workboard_summary_box = QGroupBox("Session Snapshot")
        workboard_form = QFormLayout(workboard_summary_box)
        self.analysis_workboard_status_label = QLabel("-")
        self.analysis_workboard_summary_label = QLabel("-")
        self.analysis_workboard_today_label = QLabel("-")
        self.analysis_workboard_counts_label = QLabel("-")
        self.analysis_workboard_lanes_label = QLabel("-")
        self.analysis_workboard_primary_lane_label = QLabel("-")
        self.analysis_workboard_board_hint_label = QLabel("-")
        self.analysis_workboard_lane_brief_label = QLabel("-")
        self.analysis_workboard_first_label = QLabel("-")
        self.analysis_workboard_action_label = QLabel("-")
        self.analysis_workboard_hold_label = QLabel("-")
        self.analysis_workboard_queue_label = QLabel("-")
        self.analysis_workboard_shoot_now_label = QLabel("-")
        self.analysis_workboard_confirm_label = QLabel("-")
        self.analysis_workboard_hold_lane_label = QLabel("-")
        self.analysis_workboard_pause_label = QLabel("-")
        self.analysis_workboard_reject_watch_label = QLabel("-")
        for label in (
            self.analysis_workboard_status_label,
            self.analysis_workboard_summary_label,
            self.analysis_workboard_today_label,
            self.analysis_workboard_counts_label,
            self.analysis_workboard_lanes_label,
            self.analysis_workboard_primary_lane_label,
            self.analysis_workboard_board_hint_label,
            self.analysis_workboard_lane_brief_label,
            self.analysis_workboard_first_label,
            self.analysis_workboard_action_label,
            self.analysis_workboard_hold_label,
            self.analysis_workboard_queue_label,
            self.analysis_workboard_shoot_now_label,
            self.analysis_workboard_confirm_label,
            self.analysis_workboard_hold_lane_label,
            self.analysis_workboard_pause_label,
            self.analysis_workboard_reject_watch_label,
        ):
            label.setWordWrap(True)
        workboard_form.addRow("Status", self.analysis_workboard_status_label)
        workboard_form.addRow("Summary", self.analysis_workboard_summary_label)
        workboard_form.addRow("Today", self.analysis_workboard_today_label)
        workboard_form.addRow("Counts", self.analysis_workboard_counts_label)
        workboard_form.addRow("Lanes", self.analysis_workboard_lanes_label)
        workboard_form.addRow(
            "Primary Lane", self.analysis_workboard_primary_lane_label
        )
        workboard_form.addRow("Board Focus", self.analysis_workboard_board_hint_label)
        workboard_form.addRow("Lane Brief", self.analysis_workboard_lane_brief_label)
        workboard_form.addRow("Run First", self.analysis_workboard_first_label)
        workboard_form.addRow("Action", self.analysis_workboard_action_label)
        workboard_form.addRow("Hold Back", self.analysis_workboard_hold_label)
        workboard_form.addRow("Queue", self.analysis_workboard_queue_label)
        workboard_button_row = QHBoxLayout()
        self.analysis_workboard_copy_today_btn = QPushButton("Copy Today Plan")
        self.analysis_workboard_copy_today_btn.clicked.connect(
            self._copy_workboard_today_plan
        )
        self.analysis_workboard_copy_queue_btn = QPushButton("Copy Queue")
        self.analysis_workboard_copy_queue_btn.clicked.connect(
            self._copy_workboard_queue
        )
        self.analysis_workboard_copy_full_btn = QPushButton("Copy Full Board")
        self.analysis_workboard_copy_full_btn.clicked.connect(self._copy_workboard_full)
        self.analysis_workboard_reset_btn = QPushButton("Reset Board State")
        self.analysis_workboard_reset_btn.clicked.connect(self._reset_workboard_state)
        workboard_button_row.addWidget(self.analysis_workboard_copy_today_btn)
        workboard_button_row.addWidget(self.analysis_workboard_copy_queue_btn)
        workboard_button_row.addWidget(self.analysis_workboard_copy_full_btn)
        workboard_button_row.addWidget(self.analysis_workboard_reset_btn)
        workboard_button_row.addStretch(1)
        workboard_layout.addWidget(workboard_summary_box)
        workboard_layout.addLayout(workboard_button_row)

        lane_board_box = QGroupBox("Lane Board")
        lane_board_layout = QGridLayout(lane_board_box)
        self.analysis_workboard_lane_cards = {}
        self.analysis_workboard_lane_labels = {}
        self.analysis_workboard_lane_focus_buttons = {}
        self.analysis_workboard_lane_copy_buttons = {}
        self.analysis_workboard_lane_done_buttons = {}
        lane_specs = (
            ("shoot_now", self.analysis_workboard_shoot_now_label, 0, 0),
            ("confirm", self.analysis_workboard_confirm_label, 0, 1),
            ("hold", self.analysis_workboard_hold_lane_label, 0, 2),
            ("pause", self.analysis_workboard_pause_label, 1, 0),
            ("reject_watch", self.analysis_workboard_reject_watch_label, 1, 1),
        )
        for lane_name, lane_label, row, column in lane_specs:
            lane_card = QGroupBox(lane_name)
            lane_card_layout = QVBoxLayout(lane_card)
            lane_card_layout.setContentsMargins(10, 10, 10, 10)
            lane_card_layout.addWidget(lane_label)
            lane_button_row = QHBoxLayout()
            focus_btn = QPushButton("Focus")
            focus_btn.clicked.connect(
                lambda _checked=False, lane=lane_name: self._focus_workboard_lane(lane)
            )
            copy_btn = QPushButton("Copy")
            copy_btn.clicked.connect(
                lambda _checked=False, lane=lane_name: self._copy_workboard_lane(lane)
            )
            done_btn = QPushButton("Mark Done")
            done_btn.setCheckable(True)
            done_btn.clicked.connect(
                lambda checked=False, lane=lane_name: self._toggle_workboard_lane_done(
                    lane, checked
                )
            )
            lane_button_row.addWidget(focus_btn)
            lane_button_row.addWidget(copy_btn)
            lane_button_row.addWidget(done_btn)
            lane_card_layout.addLayout(lane_button_row)
            lane_board_layout.addWidget(lane_card, row, column)
            self.analysis_workboard_lane_cards[lane_name] = lane_card
            self.analysis_workboard_lane_labels[lane_name] = lane_label
            self.analysis_workboard_lane_focus_buttons[lane_name] = focus_btn
            self.analysis_workboard_lane_copy_buttons[lane_name] = copy_btn
            self.analysis_workboard_lane_done_buttons[lane_name] = done_btn
        workboard_layout.addWidget(lane_board_box)
        layout.addWidget(workboard_box)

        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        layout.addWidget(self.analysis_text, 1)

        buttons = QHBoxLayout()
        refresh_btn = QPushButton(tr("bw_analyze_batch"))
        refresh_btn.clicked.connect(self.refresh_analysis)
        buttons.addWidget(refresh_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

        return widget

    def refresh_batches(self, select_batch_id: Optional[int] = None) -> None:
        search = (self.search_input.text() or "").strip()
        rows = list_batch_projects(self.db, search=search or None)
        self.batch_table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            batch_item = QTableWidgetItem(row["batch_name"])
            batch_item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.batch_table.setItem(row_idx, 0, batch_item)
            self.batch_table.setItem(
                row_idx, 1, QTableWidgetItem(row.get("rifle_name") or "-")
            )
            self.batch_table.setItem(
                row_idx, 2, QTableWidgetItem(row.get("status") or "-")
            )
            self.batch_table.setItem(
                row_idx, 3, QTableWidgetItem(row.get("created_date") or "-")
            )
            activity = (
                f"{row.get('session_count', 0)} sessions / "
                f"{row.get('note_count', 0)} notes / "
                f"{row.get('attachment_count', 0)} images"
            )
            self.batch_table.setItem(row_idx, 4, QTableWidgetItem(activity))

        if select_batch_id is not None:
            self._select_batch_row(select_batch_id)
        elif self.current_batch_id is None and rows:
            self.batch_table.selectRow(0)
        elif self.current_batch_id is not None:
            self._select_batch_row(self.current_batch_id)

    def _select_batch_row(self, batch_id: int) -> None:
        for row in range(self.batch_table.rowCount()):
            item = self.batch_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == batch_id:
                self.batch_table.selectRow(row)
                return

    def _on_batch_selection_changed(self) -> None:
        row = self.batch_table.currentRow()
        if row < 0:
            return
        item = self.batch_table.item(row, 0)
        if not item:
            return
        batch_id = item.data(Qt.ItemDataRole.UserRole)
        if batch_id:
            self.load_batch(batch_id)

    def _open_selected_batch(self) -> None:
        row = self.batch_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, tr("bw_no_batch_title"), tr("bw_select_batch_first")
            )
            return
        item = self.batch_table.item(row, 0)
        if item:
            self.load_batch(item.data(Qt.ItemDataRole.UserRole))

    def load_batch(self, batch_id: int) -> None:
        batch = get_batch_project(self.db, batch_id)
        if not batch:
            QMessageBox.warning(
                self,
                tr("bw_batch_missing_title"),
                tr("bw_batch_missing_message"),
            )
            if self.current_batch_id == batch_id:
                self.current_batch_id = None
                self._current_batch = None
            self.refresh_batches()
            return
        self.current_batch_id = batch_id
        completed_lanes, selected_lane = _load_workboard_lane_ui_state(batch_id)
        self._workboard_completed_lanes_by_batch[batch_id] = completed_lanes
        if selected_lane:
            self._workboard_selected_lane_by_batch[batch_id] = selected_lane
        else:
            self._workboard_selected_lane_by_batch.pop(batch_id, None)
        self._current_batch = batch
        _store_active_batch_context(self.db, batch)
        self._current_notes = get_batch_notes(self.db, batch_id)
        self._current_sessions = get_batch_sessions(self.db, batch_id)
        self._current_attachments = get_batch_attachments(self.db, batch_id)
        self._batch_media_dir = (
            Path(self.db.db_path).resolve().parent
            / "batch_media"
            / batch["batch_number"]
        )
        self._refresh_overview()
        self._refresh_notes()
        self._refresh_sessions()
        self._refresh_attachments()
        self.refresh_analysis()
        try:
            analysis = _parse_analysis_payload(batch.get("analysis_json") or "{}")
            self._apply_retest_session_prefill(analysis)
            self._apply_subsonic_session_prefill(analysis)
        except Exception:
            pass

    def _apply_retest_session_prefill(self, analysis: dict[str, Any] | None) -> None:
        prefill = _build_retest_session_prefill(analysis)
        if not prefill:
            if hasattr(self, "session_prefill_hint"):
                self.session_prefill_hint.hide()
                self.session_prefill_hint.setText("")
            return
        if (
            hasattr(self, "session_name")
            and not (self.session_name.text() or "").strip()
        ):
            self.session_name.setText(str(prefill.get("session_name") or ""))
        if hasattr(self, "session_distance"):
            try:
                self.session_distance.setValue(int(prefill.get("distance_m") or 100))
            except Exception:
                pass
        if hasattr(self, "session_shots"):
            try:
                self.session_shots.setValue(int(prefill.get("shot_count") or 5))
            except Exception:
                pass
        if (
            hasattr(self, "session_notes")
            and not self.session_notes.toPlainText().strip()
        ):
            self.session_notes.setPlainText(str(prefill.get("notes") or ""))
        if hasattr(self, "session_prefill_hint"):
            shots = prefill.get("shot_count")
            shot_text = (
                f"{int(shots)} shots" if isinstance(shots, int) else "pre-filled shots"
            )
            self.session_prefill_hint.setText(
                f"The session fields are pre-filled from Retest Advisor for this batch. "
                f"Recommended setup: {shot_text} and notes ready to use."
            )
            self.session_prefill_hint.show()

    def _apply_subsonic_session_prefill(self, analysis: dict[str, Any] | None) -> None:
        hint = _build_subsonic_batch_hint(analysis)
        enabled = bool(hint)
        if hasattr(self, "session_subsonic_group"):
            self.session_subsonic_group.setVisible(enabled)
        if hasattr(self, "session_prefill_hint") and enabled:
            existing = (self.session_prefill_hint.text() or "").strip()
            combined = f"{existing}\n\n{hint}".strip() if existing else hint
            self.session_prefill_hint.setText(combined)
            self.session_prefill_hint.show()

    def _refresh_overview(self) -> None:
        batch = self._current_batch
        if not batch:
            return

        self.header_label.setText(
            f"{batch.get('batch_name', 'Batch')}  {batch.get('batch_number', '')}"
        )
        rifle_text = (
            f"{batch.get('rifle_name') or '-'} ({batch.get('rifle_caliber') or '-'})"
        )
        analysis_json = batch.get("analysis_json") or "{}"
        analysis = _parse_analysis_payload(analysis_json)
        workspace = analysis.get("workspace", {}) if isinstance(analysis, dict) else {}
        project_name = workspace.get("project_name") or tr("bw_default_project")
        ammo_profile_name = batch.get("ammo_profile_name") or "-"
        setup_label = _format_batch_setup_label(batch)
        self.meta_label.setText(
            f"{rifle_text}  |  {project_name}  |  {batch.get('status', '-')}"
        )

        self.label_batch_number.setText(batch.get("batch_number") or "-")
        self.label_batch_name.setText(batch.get("batch_name") or "-")
        self.label_batch_rifle.setText(rifle_text)
        context_bits = [project_name, f"{tr('bw_profile_prefix')}: {ammo_profile_name}"]
        if setup_label:
            context_bits.append(f"Setup: {setup_label}")
        self.label_batch_context.setText(" | ".join(context_bits))
        self.label_batch_status.setText(batch.get("status") or "-")
        self.label_batch_created.setText(batch.get("created_date") or "-")
        self.label_batch_updated.setText(batch.get("updated_date") or "-")

        component_snapshot = batch.get("component_snapshot_json") or "{}"
        try:
            snapshot = json.loads(component_snapshot)
        except Exception:
            snapshot = {}

        component_bits = []
        for key in ("bullet", "powder", "primer", "brass", "case"):
            entry = snapshot.get(key)
            if entry:
                component_bits.append(f"{key}: {entry}")
        context_summary = _format_component_context_summary(snapshot, analysis)
        if context_summary:
            component_bits.append(f"kontekst: {context_summary}")
        self.label_batch_components.setText(
            " | ".join(component_bits) if component_bits else "-"
        )
        self.label_batch_counts.setText(
            tr(
                "bw_sessions_notes_photos",
                sessions=len(self._current_sessions),
                notes=len(self._current_notes),
                photos=len(self._current_attachments),
            )
        )

        target_bits = []
        if batch.get("charge_weight_grains") is not None:
            target_bits.append(f"{batch['charge_weight_grains']} gr")
        if batch.get("coal_mm") is not None:
            target_bits.append(f"COAL {batch['coal_mm']} mm")
        if batch.get("cbto_mm") is not None:
            target_bits.append(f"CBTO {batch['cbto_mm']} mm")
        if batch.get("target_group_mm") is not None:
            target_bits.append(
                f"{tr('bw_target_group_prefix')} {_format_group_mm(batch['target_group_mm'])}"
            )
        self.label_batch_target.setText(" | ".join(target_bits) if target_bits else "-")

        self.status_combo.setCurrentText(batch.get("status") or "active")
        self.snapshot_text.setPlainText(
            json.dumps(snapshot, ensure_ascii=False, indent=2)
            if snapshot
            else tr("bw_snapshot_missing")
        )

        analysis_text = batch.get("analysis_json")
        analysis_summary = "-"
        if analysis_text:
            try:
                analysis_data = _parse_analysis_payload(analysis_text)
                if isinstance(analysis_data, dict):
                    smart_engine_summary = _get_batch_smart_engine_summary(
                        self.db, batch
                    )
                    parts = []
                    verification = analysis_data.get("verification_advisory") or {}
                    verification_title = str(verification.get("title") or "").strip()
                    retest = analysis_data.get("retest_advisory") or {}
                    retest_title = str(retest.get("title") or "").strip()
                    retest_shots = retest.get("suggested_control_shots")
                    retest_protocol = str(retest.get("protocol_summary") or "").strip()
                    if analysis_data.get("score") is not None:
                        parts.append(f"score {float(analysis_data['score']):.1f}")
                    if analysis_data.get("next_focus"):
                        parts.append(str(analysis_data["next_focus"]))
                    elif analysis_data.get("trend_summary"):
                        parts.append(str(analysis_data["trend_summary"]))
                    if verification_title:
                        parts.append(f"verification: {verification_title}")
                    if retest_title:
                        if isinstance(retest_shots, (int, float)):
                            parts.append(
                                f"retest: {retest_title} ({int(retest_shots)} verification shots)"
                            )
                        else:
                            parts.append(f"retest: {retest_title}")
                    if retest_protocol:
                        parts.append(f"setup: {retest_protocol}")
                    setup_label = _format_batch_setup_label(batch)
                    if setup_label:
                        parts.append(f"context: {setup_label}")
                    subsonic_hint = _build_subsonic_batch_hint(analysis_data)
                    if subsonic_hint:
                        parts.append(subsonic_hint)
                    direct_model_match = (
                        analysis_data.get("direct_model_match_advisory") or {}
                    )
                    if not isinstance(
                        direct_model_match, dict
                    ) or not direct_model_match.get("title"):
                        direct_model_match = _build_direct_model_match_advisory(
                            analysis_data,
                            self._combined_chronograph_stats(),
                        )
                    if direct_model_match.get("title"):
                        parts.append(f"direkte: {direct_model_match['title']}")
                    model_match_hint = _format_model_match_summary(analysis_data)
                    if model_match_hint:
                        parts.append(f"modell: {model_match_hint}")
                    evidence_basis = _build_batch_evidence_basis(
                        batch,
                        analysis_data,
                        self._current_sessions,
                        self._combined_chronograph_stats(),
                        smart_engine_summary,
                    )
                    if evidence_basis.get("title"):
                        parts.append(evidence_basis["title"].lower())
                    if smart_engine_summary.get("summary"):
                        parts.append(str(smart_engine_summary.get("summary")).strip())
                    if smart_engine_summary.get("next"):
                        parts.append(str(smart_engine_summary.get("next")).strip())
                    if smart_engine_summary.get("gate"):
                        parts.append(str(smart_engine_summary.get("gate")).strip())
                    if smart_engine_summary.get("protocol"):
                        parts.append(str(smart_engine_summary.get("protocol")).strip())
                    if smart_engine_summary.get("hold"):
                        parts.append(str(smart_engine_summary.get("hold")).strip())
                    if smart_engine_summary.get("blocker"):
                        parts.append(str(smart_engine_summary.get("blocker")).strip())
                    if smart_engine_summary.get("confidence"):
                        parts.append(
                            str(smart_engine_summary.get("confidence")).strip()
                        )
                    if smart_engine_summary.get("bullet_fit"):
                        parts.append(
                            str(smart_engine_summary.get("bullet_fit")).strip()
                        )
                    if smart_engine_summary.get("jump"):
                        parts.append(str(smart_engine_summary.get("jump")).strip())
                    if smart_engine_summary.get("baseline"):
                        parts.append(str(smart_engine_summary.get("baseline")).strip())
                    if smart_engine_summary.get("branch"):
                        parts.append(str(smart_engine_summary.get("branch")).strip())
                    workboard_hint = _format_batch_comparison_workboard_summary(
                        analysis_data.get("batch_comparison_workboard")
                        if isinstance(
                            analysis_data.get("batch_comparison_workboard"), dict
                        )
                        else {}
                    )
                    if workboard_hint:
                        parts.append(f"workboard: {workboard_hint}")
                    if parts:
                        analysis_summary = " | ".join(parts)
            except Exception:
                analysis_summary = "-"
        self.label_batch_analysis.setText(analysis_summary)

    def _refresh_notes(self) -> None:
        self.notes_list.clear()
        for note in self._current_notes:
            title = (
                note.get("title")
                or note.get("note_type")
                or tr("bw_note_default_title")
            )
            text = (note.get("note_text") or "").strip()
            item = QListWidgetItem(f"{title}: {text[:120]}")
            item.setData(Qt.ItemDataRole.UserRole, note)
            self.notes_list.addItem(item)

    def _refresh_sessions(self) -> None:
        self.sessions_table.setRowCount(len(self._current_sessions))
        for row_idx, session in enumerate(self._current_sessions):
            session_analysis = _parse_analysis_payload(
                session.get("analysis_json") or "{}"
            )
            self.sessions_table.setItem(
                row_idx, 0, QTableWidgetItem(session.get("session_date") or "-")
            )
            self.sessions_table.setItem(
                row_idx, 1, QTableWidgetItem(session.get("session_type") or "-")
            )
            self.sessions_table.setItem(
                row_idx,
                2,
                QTableWidgetItem(_format_distance_m(session.get("distance_m"))),
            )
            group = session.get("group_size_mm")
            self.sessions_table.setItem(
                row_idx,
                3,
                QTableWidgetItem(_format_group_mm(group)),
            )
            self.sessions_table.setItem(
                row_idx, 4, QTableWidgetItem(str(session.get("shot_count") or "-"))
            )
            chrono = session.get("chronograph_import_id")
            self.sessions_table.setItem(
                row_idx, 5, QTableWidgetItem(str(chrono) if chrono else "-")
            )
            notes = session.get("notes") or ""
            obs = _format_subsonic_session_observations(session_analysis)
            primer_summary = _format_batch_session_primer_summary(session_analysis)
            note_preview = notes[:80]
            if obs:
                note_preview = f"{obs} | {note_preview}".strip(" |")
            if primer_summary:
                note_preview = f"{primer_summary} | {note_preview}".strip(" |")
            self.sessions_table.setItem(row_idx, 6, QTableWidgetItem(note_preview))

    def _refresh_attachments(self) -> None:
        self.attachments_list.clear()
        for attachment in self._current_attachments:
            caption = attachment.get("caption") or ""
            name = os.path.basename(attachment.get("file_path") or "")
            item = QListWidgetItem(f"{name} {('- ' + caption) if caption else ''}")
            item.setData(Qt.ItemDataRole.UserRole, attachment)
            self.attachments_list.addItem(item)
        self._refresh_attachment_preview()

    def _refresh_attachment_preview(self) -> None:
        item = self.attachments_list.currentItem()
        if item is None:
            self.photo_preview.setText(tr("bw_select_image_preview"))
            self.photo_preview.setPixmap(QPixmap())
            self.photo_caption.setText("")
            return
        attachment = item.data(Qt.ItemDataRole.UserRole) or {}
        path = attachment.get("file_path") or ""
        caption = attachment.get("caption") or ""
        self.photo_caption.setText(f"{path}\n{caption}".strip())
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.photo_preview.setPixmap(
                    pixmap.scaled(
                        520,
                        360,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return
        self.photo_preview.setText(tr("bw_image_load_failed"))
        self.photo_preview.setPixmap(QPixmap())

    def _show_attachment_preview(self, *_args) -> None:
        self._refresh_attachment_preview()

    def create_batch_dialog(self) -> None:
        rifles = self.db.get_all("rifles", "name")
        if not rifles:
            QMessageBox.warning(
                self, tr("bw_missing_rifle_title"), tr("bw_missing_rifle_message")
            )
            return
        project_context = _get_workspace_project_context()
        verification = _get_active_workflow_verification_advisory(self.db)
        verification_guidance = _format_workflow_verification_guidance(verification)

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("bw_new_batch_title"))
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        name = QLineEdit()
        name.setPlaceholderText(
            tr(
                "bw_example_batch_name",
                project=project_context.get("project_name", "Project"),
            )
        )
        form.addRow(tr("bw_batch_name"), name)
        form.addRow(
            tr("bw_active_project"),
            QLabel(project_context.get("project_name", tr("bw_default_project"))),
        )

        rifle_combo = QComboBox()
        for rifle in rifles:
            rifle_combo.addItem(f"{rifle['name']} ({rifle['caliber']})", rifle["id"])
        form.addRow(tr("bw_rifle"), rifle_combo)

        notes = QTextEdit()
        notes.setMaximumHeight(90)
        notes.setPlaceholderText(tr("bw_batch_notes_placeholder"))
        if verification_guidance:
            notes.setPlainText(verification_guidance)
        form.addRow(tr("bw_notes_field"), notes)
        layout.addLayout(form)

        if verification_guidance:
            guidance_label = QLabel(verification_guidance)
            guidance_label.setWordWrap(True)
            level = verification.get("level")
            if level == "critical":
                guidance_label.setStyleSheet(
                    "background-color: #fee2e2; color: #991b1b; border: 1px solid #f0b4b4; "
                    "border-radius: 6px; padding: 8px;"
                )
            elif level == "warning":
                guidance_label.setStyleSheet(
                    "background-color: #fef3c7; color: #92400e; border: 1px solid #f6d98b; "
                    "border-radius: 6px; padding: 8px;"
                )
            else:
                guidance_label.setStyleSheet(
                    "background-color: #eaf7ea; color: #256029; border: 1px solid #b7e1b9; "
                    "border-radius: 6px; padding: 8px;"
                )
            layout.addWidget(guidance_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        if not name.text().strip():
            QMessageBox.warning(
                self, tr("bw_missing_name_title"), tr("bw_missing_name_message")
            )
            return
        workflow_context = _get_active_workflow_context()
        rifle_id = int(rifle_combo.currentData())
        barrel_context = resolve_active_barrel_configuration_context(self.db, rifle_id)
        result = create_batch_project(
            self.db,
            name.text().strip(),
            rifle_id,
            barrel_id=barrel_context.get("barrel_id"),
            barrel_name=barrel_context.get("barrel_name"),
            barrel_configuration_id=barrel_context.get("barrel_configuration_id"),
            barrel_configuration_name=barrel_context.get("barrel_configuration_name"),
            load_session_id=(
                int(workflow_context["load_session_id"])
                if workflow_context.get("load_session_id") not in (None, "")
                else None
            ),
            source_workflow=(
                f"workflow:{workflow_context['workflow_id']}"
                if workflow_context.get("workflow_id")
                else None
            ),
            analysis_json={
                "workspace": project_context,
                "created_from": "batch_workspace",
                "workflow_context": workflow_context,
                "verification_advisory": verification,
            },
            barrel_configuration_snapshot=barrel_context.get(
                "barrel_configuration_snapshot"
            ),
            notes=notes.toPlainText().strip(),
        )
        self.refresh_batches(select_batch_id=result["batch_id"])
        QMessageBox.information(
            self,
            tr("bw_batch_created_title"),
            tr("bw_batch_created_message", batch_number=result["batch_number"]),
        )

    def _add_note(self) -> None:
        if not self.current_batch_id:
            return
        text = (self.note_text.toPlainText() or "").strip()
        if not text:
            QMessageBox.warning(
                self, tr("bw_missing_note_title"), tr("bw_missing_note_message")
            )
            return
        add_batch_note(
            self.db,
            self.current_batch_id,
            text,
            title=(self.note_title.text() or "").strip() or None,
        )
        self.note_title.clear()
        self.note_text.clear()
        self.load_batch(self.current_batch_id)

    def _save_batch_status(self) -> None:
        if not self.current_batch_id:
            return
        update_batch_project(
            self.db,
            self.current_batch_id,
            {"status": self.status_combo.currentText()},
        )
        self.load_batch(self.current_batch_id)

    def _finalize_batch(self) -> None:
        if not self.current_batch_id:
            return
        update_batch_project(
            self.db,
            self.current_batch_id,
            {
                "status": "finalized",
                "finalized_date": datetime.now().isoformat(timespec="seconds"),
            },
        )
        self.load_batch(self.current_batch_id)

    def _add_session(self) -> None:
        if not self.current_batch_id:
            return
        session_name = (self.session_name.text() or "").strip() or None
        session_date = self.session_date.date().toString("yyyy-MM-dd")
        group_mm = self.session_group_mm.value()
        group_moa = self.session_group_moa.value()
        notes = self.session_notes.toPlainText().strip()
        primer_review_enabled = bool(
            self.session_enable_primer_review.isChecked()
            if hasattr(self, "session_enable_primer_review")
            else False
        )
        primer_image_source = (
            self.session_primer_image_path.text().strip()
            if primer_review_enabled and hasattr(self, "session_primer_image_path")
            else ""
        )
        primer_image_sources = _parse_batch_session_primer_sources(primer_image_source)
        primer_image_quality = (
            self.session_primer_image_quality.currentData()
            if primer_review_enabled and hasattr(self, "session_primer_image_quality")
            else ""
        )
        primer_image_confidence = (
            self.session_primer_image_confidence.currentData()
            if primer_review_enabled
            and hasattr(self, "session_primer_image_confidence")
            else ""
        )
        primer_image_observation = (
            self.session_primer_image_observation.toPlainText().strip()
            if primer_review_enabled
            and hasattr(self, "session_primer_image_observation")
            else ""
        )
        subsonic_observations = {
            "cycling_status": (
                self.session_cycling_status.currentData()
                if hasattr(self, "session_cycling_status")
                else ""
            ),
            "sonic_crack": bool(
                self.session_sonic_crack.isChecked()
                if hasattr(self, "session_sonic_crack")
                else False
            ),
            "keyhole": bool(
                self.session_keyhole.isChecked()
                if hasattr(self, "session_keyhole")
                else False
            ),
            "suppressor_used": bool(
                self.session_suppressor_used.isChecked()
                if hasattr(self, "session_suppressor_used")
                else False
            ),
        }
        primer_image_paths: list[str] = []
        if primer_image_sources:
            try:
                primer_image_paths = [
                    _copy_batch_session_primer_image(
                        self._batch_media_dir,
                        source_path,
                        session_name=session_name,
                        session_date=session_date,
                    )
                    for source_path in primer_image_sources
                ]
            except FileNotFoundError:
                QMessageBox.warning(
                    self,
                    tr("bw_primer_image_missing_title"),
                    tr("bw_primer_image_missing_message"),
                )
                return

        workflow_context = _get_active_workflow_context()
        current_batch = self._current_batch or {}
        barrel_snapshot = _parse_analysis_payload(
            current_batch.get("barrel_configuration_snapshot_json") or "{}"
        )
        derived_suppressor_used = _derive_suppressor_used(
            barrel_snapshot.get("muzzle_device_type")
        )
        analysis_payload = {
            "workflow_context": workflow_context,
            "subsonic_observations": subsonic_observations,
            "primer_image_review": {
                "enabled": primer_review_enabled,
                "batch_id": self.current_batch_id,
                "rifle_id": (
                    self._current_batch.get("rifle_id") if self._current_batch else None
                ),
                "session_name": session_name,
                "session_date": session_date,
            },
        }
        if primer_review_enabled:
            analysis_payload["primer_image_review"].update(
                {
                    "path": primer_image_paths[0] if primer_image_paths else None,
                    "primary_path": (
                        primer_image_paths[0] if primer_image_paths else None
                    ),
                    "images": primer_image_paths,
                    "image_count": len(primer_image_paths),
                    "quality": str(primer_image_quality or "").strip() or None,
                    "observation": primer_image_observation or None,
                    "confidence": str(primer_image_confidence or "").strip() or None,
                }
            )

        session_result = add_batch_session(
            self.db,
            self.current_batch_id,
            load_session_id=(
                int(current_batch.get("load_session_id"))
                if current_batch.get("load_session_id") not in (None, "")
                else None
            ),
            rifle_id=current_batch.get("rifle_id"),
            barrel_id=current_batch.get("barrel_id"),
            barrel_name=current_batch.get("barrel_name"),
            barrel_configuration_id=current_batch.get("barrel_configuration_id"),
            barrel_configuration_name=current_batch.get("barrel_configuration_name"),
            session_name=session_name,
            session_date=session_date,
            distance_m=self.session_distance.value(),
            temperature_c=self.session_temp.value(),
            wind_speed_mps=self.session_wind.value(),
            humidity_percent=self.session_humidity.value(),
            suppressor_used=(
                True
                if subsonic_observations.get("suppressor_used")
                else derived_suppressor_used
            ),
            muzzle_device_type=barrel_snapshot.get("muzzle_device_type"),
            shot_count=self.session_shots.value(),
            group_size_mm=group_mm if group_mm > 0 else None,
            group_size_moa=group_moa if group_moa > 0 else None,
            notes=notes,
            analysis_json=analysis_payload,
        )
        batch_session_id = (
            int(session_result.get("session_id"))
            if session_result.get("session_id") not in (None, "")
            else None
        )
        for index, primer_image_path in enumerate(primer_image_paths, start=1):
            caption = (
                f"Primer review - {session_name} #{index}"
                if session_name
                else f"Primer review - {session_date} #{index}"
            )
            add_batch_attachment(
                self.db,
                self.current_batch_id,
                primer_image_path,
                attachment_type="primer",
                caption=caption,
            )
        primer_payload = _build_batch_session_primer_payload(
            self._current_batch,
            workflow_context,
            batch_session_id=batch_session_id,
            session_name=session_name,
            session_date=session_date,
            primer_review_enabled=primer_review_enabled,
            primer_image_paths=primer_image_paths,
            primer_image_quality=str(primer_image_quality or "").strip(),
            primer_image_observation=primer_image_observation,
            primer_image_confidence=str(primer_image_confidence or "").strip(),
        )
        _save_batch_session_primer_payload(self.db, primer_payload)
        refresh_load_session_measurement_summary(
            self.db,
            current_batch.get("load_session_id"),
            source="batch_workspace.add_batch_session",
        )
        self.session_name.clear()
        self.session_notes.clear()
        if hasattr(self, "session_enable_primer_review"):
            self.session_enable_primer_review.setChecked(False)
        if hasattr(self, "session_primer_image_path"):
            self.session_primer_image_path.clear()
        if hasattr(self, "session_primer_image_quality"):
            self.session_primer_image_quality.setCurrentIndex(0)
        if hasattr(self, "session_primer_image_confidence"):
            self.session_primer_image_confidence.setCurrentIndex(1)
        if hasattr(self, "session_primer_image_observation"):
            self.session_primer_image_observation.clear()
        if hasattr(self, "session_cycling_status"):
            self.session_cycling_status.setCurrentIndex(0)
        if hasattr(self, "session_sonic_crack"):
            self.session_sonic_crack.setChecked(False)
        if hasattr(self, "session_keyhole"):
            self.session_keyhole.setChecked(False)
        if hasattr(self, "session_suppressor_used"):
            self.session_suppressor_used.setChecked(False)
        self.load_batch(self.current_batch_id)

    def _import_chrono_csv(self) -> None:
        if not self.current_batch_id:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("bw_select_chrono_csv"),
            "",
            "CSV Files (*.csv);;All Files (*.*)",
        )
        if not file_path:
            return
        result = import_chronograph_csv(
            self.db,
            file_path,
            load_session_id=(
                int((self._current_batch or {}).get("load_session_id"))
                if (self._current_batch or {}).get("load_session_id") not in (None, "")
                else None
            ),
            note=f"Batch import for {self._current_batch.get('batch_number')}",
        )
        add_batch_session(
            self.db,
            self.current_batch_id,
            load_session_id=(
                int((self._current_batch or {}).get("load_session_id"))
                if (self._current_batch or {}).get("load_session_id") not in (None, "")
                else None
            ),
            rifle_id=(self._current_batch or {}).get("rifle_id"),
            barrel_id=(self._current_batch or {}).get("barrel_id"),
            barrel_name=(self._current_batch or {}).get("barrel_name"),
            barrel_configuration_id=(self._current_batch or {}).get(
                "barrel_configuration_id"
            ),
            barrel_configuration_name=(self._current_batch or {}).get(
                "barrel_configuration_name"
            ),
            session_name=Path(file_path).stem,
            session_type="chronograph",
            chronograph_import_id=result.get("import_id"),
            suppressor_used=_derive_suppressor_used(
                _parse_analysis_payload(
                    (self._current_batch or {}).get(
                        "barrel_configuration_snapshot_json"
                    )
                    or "{}"
                ).get("muzzle_device_type")
            ),
            muzzle_device_type=_parse_analysis_payload(
                (self._current_batch or {}).get("barrel_configuration_snapshot_json")
                or "{}"
            ).get("muzzle_device_type"),
            shot_count=result.get("stats", {}).get("count"),
            notes=f"Imported from {os.path.basename(file_path)}",
            analysis_json={
                "stats": result.get("stats", {}),
                "workflow_context": _get_active_workflow_context(),
            },
        )
        refresh_load_session_measurement_summary(
            self.db,
            (self._current_batch or {}).get("load_session_id"),
            source="batch_workspace.import_chrono_csv",
        )
        self.load_batch(self.current_batch_id)
        QMessageBox.information(self, tr("bw_imported"), tr("bw_chrono_saved_to_batch"))

    def _set_session_primer_review_enabled(self, enabled: bool) -> None:
        for widget in getattr(self, "_session_primer_review_widgets", []):
            widget.setEnabled(enabled)

    def _browse_session_primer_image(self) -> None:
        if (
            hasattr(self, "session_enable_primer_review")
            and not self.session_enable_primer_review.isChecked()
        ):
            return
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("bw_primer_image_select"),
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*.*)",
        )
        if file_paths and hasattr(self, "session_primer_image_path"):
            self.session_primer_image_path.setText(" | ".join(file_paths))

    def _manual_chrono_entry(self) -> None:
        if not self.current_batch_id:
            return
        dlg = ManualChronographDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        velocities = dlg.parsed_velocities()
        if not velocities:
            QMessageBox.warning(
                self, tr("bw_missing_data_title"), tr("bw_no_velocities_read")
            )
            return
        result = store_manual_chronograph_for_batch(
            self.db,
            self.current_batch_id,
            velocities,
            ammo_profile_id=self._current_batch.get("ammo_profile_id"),
            note=dlg.notes.toPlainText().strip(),
            session_name=dlg.session_name.text().strip() or None,
        )
        self.load_batch(self.current_batch_id)
        QMessageBox.information(
            self,
            tr("bw_saved"),
            tr("bw_manual_chrono_saved", count=result["stats"]["count"]),
        )

    def _add_photos(self) -> None:
        if not self.current_batch_id:
            return
        if not self._batch_media_dir:
            batch = self._current_batch or {}
            batch_number = batch.get("batch_number") or f"batch-{self.current_batch_id}"
            self._batch_media_dir = (
                Path(self.db.db_path).resolve().parent / "batch_media" / batch_number
            )
        photo_dir = self._batch_media_dir / "photos"
        photo_dir.mkdir(parents=True, exist_ok=True)

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("bw_select_images"),
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*.*)",
        )
        if not file_paths:
            return

        for src_path in file_paths:
            if not os.path.exists(src_path):
                continue
            safe_name = _safe_filename(Path(src_path).stem)
            dest_name = (
                f"{safe_name}_{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                f"{Path(src_path).suffix}"
            )
            dest_path = photo_dir / dest_name
            try:
                shutil.copy2(src_path, dest_path)
                add_batch_attachment(
                    self.db,
                    self.current_batch_id,
                    str(dest_path),
                    attachment_type="photo",
                    caption=Path(src_path).name,
                )
            except Exception as exc:
                QMessageBox.warning(
                    self, tr("bw_photo_not_saved"), f"{src_path}\n{exc}"
                )
        self.load_batch(self.current_batch_id)

    def refresh_analysis(self) -> None:
        if not self.current_batch_id:
            self.analysis_text.setPlainText(tr("bw_analysis_select_batch"))
            self.analysis_score_label.setText("-")
            self.analysis_confidence_label.setText("-")
            self.analysis_potential_label.setText("-")
            self.analysis_trend_label.setText("-")
            self.analysis_focus_label.setText("-")
            if hasattr(self, "analysis_basis_label"):
                self.analysis_basis_label.setText("-")
            for attr_name in (
                "analysis_workboard_banner_label",
                "analysis_workboard_status_label",
                "analysis_workboard_summary_label",
                "analysis_workboard_today_label",
                "analysis_workboard_counts_label",
                "analysis_workboard_lanes_label",
                "analysis_workboard_primary_lane_label",
                "analysis_workboard_board_hint_label",
                "analysis_workboard_lane_brief_label",
                "analysis_workboard_first_label",
                "analysis_workboard_action_label",
                "analysis_workboard_hold_label",
                "analysis_workboard_queue_label",
                "analysis_workboard_shoot_now_label",
                "analysis_workboard_confirm_label",
                "analysis_workboard_hold_lane_label",
                "analysis_workboard_pause_label",
                "analysis_workboard_reject_watch_label",
            ):
                if hasattr(self, attr_name):
                    getattr(self, attr_name).setText("-")
            if hasattr(self, "analysis_workboard_lane_cards"):
                for lane_card in getattr(
                    self, "analysis_workboard_lane_cards", {}
                ).values():
                    lane_card.setStyleSheet("")
                    lane_card.setTitle("-")
            if hasattr(self, "analysis_workboard_lane_done_buttons"):
                for button in getattr(
                    self, "analysis_workboard_lane_done_buttons", {}
                ).values():
                    button.setChecked(False)
                    button.setText("Mark Done")
            self._latest_workboard_display = {}
            return

        chrono_stats = self._combined_chronograph_stats()
        engine_result = _get_batch_engine_result(self.db, self._current_batch)
        analyzer = BatchAnalyzer(
            self._current_batch,
            sessions=self._current_sessions,
            notes=self._current_notes,
            attachments=self._current_attachments,
            chronograph_stats=chrono_stats,
            engine_result=engine_result,
        )
        recommendation = analyzer.recommend_next()
        existing_analysis = _parse_analysis_payload(
            self._current_batch.get("analysis_json")
        )
        for preserved_key in (
            "workspace",
            "rifle_context",
            "component_context",
            "component_context_summary",
            "seating_context",
            "subsonic_context",
            "seating_promotion_candidate",
            "predicted_result_summary",
            "retest_advisory",
            "verification_advisory",
            "model_match_advisory",
            "direct_model_match_advisory",
        ):
            preserved_value = existing_analysis.get(preserved_key)
            if preserved_value not in (None, "", [], {}):
                recommendation[preserved_key] = preserved_value
        direct_model_match = _build_direct_model_match_advisory(
            recommendation,
            chrono_stats,
        )
        if direct_model_match:
            recommendation["direct_model_match_advisory"] = direct_model_match
        try:
            sibling_rows = list_batch_projects(self.db, search=None)
        except Exception:
            sibling_rows = []
        current_snapshot = dict(self._current_batch or {})
        current_snapshot["analysis_json"] = recommendation
        comparison_basis = _build_batch_comparison_basis(current_snapshot, sibling_rows)
        if comparison_basis:
            recommendation["batch_comparison_basis"] = comparison_basis
            comparison_advisory = _build_batch_comparison_advisory(comparison_basis)
            if comparison_advisory:
                recommendation["batch_comparison_advisory"] = comparison_advisory
            comparison_protocol = _build_batch_comparison_protocol(comparison_basis)
            if comparison_protocol:
                recommendation["batch_comparison_protocol"] = comparison_protocol
            comparison_explanation = _build_batch_comparison_explanation(
                comparison_basis
            )
            if comparison_explanation:
                recommendation["batch_comparison_explanation"] = comparison_explanation
            comparison_verdict = _build_batch_comparison_verdict(
                comparison_basis, comparison_advisory
            )
            if comparison_verdict:
                recommendation["batch_comparison_verdict"] = comparison_verdict
            comparison_checklist = _build_batch_comparison_checklist(
                comparison_basis,
                comparison_protocol,
                comparison_explanation,
            )
            if comparison_checklist:
                recommendation["batch_comparison_checklist"] = comparison_checklist
            comparison_scorecard = _build_batch_comparison_scorecard(comparison_basis)
            if comparison_scorecard:
                recommendation["batch_comparison_scorecard"] = comparison_scorecard
            comparison_confidence = _build_batch_comparison_confidence(
                comparison_basis,
                comparison_explanation,
                comparison_verdict,
            )
            if comparison_confidence:
                recommendation["batch_comparison_confidence"] = comparison_confidence
            comparison_acceptance = _build_batch_comparison_acceptance(
                comparison_basis,
                comparison_advisory,
                comparison_explanation,
                comparison_verdict,
                comparison_confidence,
            )
            if comparison_acceptance:
                recommendation["batch_comparison_acceptance"] = comparison_acceptance
            comparison_acceptance_progress = (
                _build_batch_comparison_acceptance_progress(
                    comparison_acceptance,
                    comparison_checklist,
                    comparison_confidence,
                )
            )
            if comparison_acceptance_progress:
                recommendation["batch_comparison_acceptance_progress"] = (
                    comparison_acceptance_progress
                )
            comparison_next_test = _build_batch_comparison_next_test(
                comparison_basis,
                comparison_protocol,
                comparison_acceptance,
                comparison_acceptance_progress,
                comparison_checklist,
            )
            if comparison_next_test:
                recommendation["batch_comparison_next_test"] = comparison_next_test
            comparison_status_board = _build_batch_comparison_status_board(
                comparison_basis,
                comparison_verdict,
                comparison_acceptance,
                comparison_acceptance_progress,
                comparison_next_test,
            )
            if comparison_status_board:
                recommendation["batch_comparison_status_board"] = (
                    comparison_status_board
                )
            comparison_profile_priority = _build_batch_comparison_profile_priority(
                comparison_basis,
                comparison_acceptance,
                comparison_next_test,
            )
            if comparison_profile_priority:
                recommendation["batch_comparison_profile_priority"] = (
                    comparison_profile_priority
                )
            comparison_mission_brief = _build_batch_comparison_mission_brief(
                comparison_basis,
                comparison_status_board,
                comparison_profile_priority,
                comparison_next_test,
                comparison_acceptance,
            )
            if comparison_mission_brief:
                recommendation["batch_comparison_mission_brief"] = (
                    comparison_mission_brief
                )
            comparison_portfolio = _build_batch_comparison_portfolio(
                comparison_basis,
                comparison_status_board,
                comparison_acceptance,
            )
            if comparison_portfolio:
                recommendation["batch_comparison_portfolio"] = comparison_portfolio
            comparison_session_strategy = _build_batch_comparison_session_strategy(
                comparison_basis,
                comparison_profile_priority,
                comparison_mission_brief,
                comparison_next_test,
            )
            if comparison_session_strategy:
                recommendation["batch_comparison_session_strategy"] = (
                    comparison_session_strategy
                )
            comparison_campaign_view = _build_batch_comparison_campaign_view(
                comparison_portfolio,
                comparison_session_strategy,
                comparison_status_board,
                comparison_next_test,
            )
            if comparison_campaign_view:
                recommendation["batch_comparison_campaign_view"] = (
                    comparison_campaign_view
                )
            comparison_action_plan = _build_batch_comparison_action_plan(
                comparison_campaign_view,
                comparison_mission_brief,
                comparison_checklist,
            )
            if comparison_action_plan:
                recommendation["batch_comparison_action_plan"] = comparison_action_plan
            comparison_campaign_board = _build_batch_comparison_campaign_board(
                comparison_basis,
                comparison_campaign_view,
                comparison_action_plan,
            )
            if comparison_campaign_board:
                recommendation["batch_comparison_campaign_board"] = (
                    comparison_campaign_board
                )
            comparison_session_queue = _build_batch_comparison_session_queue(
                comparison_campaign_board,
                comparison_session_strategy,
            )
            if comparison_session_queue:
                recommendation["batch_comparison_session_queue"] = (
                    comparison_session_queue
                )
            comparison_session_manifest = _build_batch_comparison_session_manifest(
                comparison_campaign_board,
                comparison_session_queue,
                comparison_action_plan,
                comparison_session_strategy,
            )
            if comparison_session_manifest:
                recommendation["batch_comparison_session_manifest"] = (
                    comparison_session_manifest
                )
            comparison_next_session_brief = _build_batch_comparison_next_session_brief(
                comparison_session_manifest,
                comparison_session_queue,
                comparison_checklist,
                comparison_action_plan,
            )
            if comparison_next_session_brief:
                recommendation["batch_comparison_next_session_brief"] = (
                    comparison_next_session_brief
                )
            comparison_today_plan = _build_batch_comparison_today_plan(
                comparison_next_session_brief,
                comparison_session_manifest,
            )
            if comparison_today_plan:
                recommendation["batch_comparison_today_plan"] = comparison_today_plan
            comparison_workboard = _build_batch_comparison_workboard(
                comparison_campaign_board,
                comparison_session_manifest,
                comparison_next_session_brief,
                comparison_today_plan,
            )
            if comparison_workboard:
                recommendation["batch_comparison_workboard"] = comparison_workboard
            comparison_learning_note = _build_batch_comparison_learning_note(
                comparison_basis,
                comparison_scorecard,
                comparison_explanation,
            )
            if comparison_learning_note:
                recommendation["batch_comparison_learning_note"] = (
                    comparison_learning_note
                )
        update_batch_project(
            self.db,
            self.current_batch_id,
            {"analysis_json": recommendation},
        )
        refresh_load_session_measurement_summary(
            self.db,
            (self._current_batch or {}).get("load_session_id"),
            source="batch_workspace.refresh_analysis",
        )
        self.analysis_score_label.setText(f"{recommendation.get('score', 0.0):.1f}")
        self.analysis_confidence_label.setText(
            f"{recommendation.get('confidence', 0.0):.1f}%"
        )
        self.analysis_potential_label.setText(
            str(recommendation.get("improvement_potential") or "-")
        )
        self.analysis_trend_label.setText(
            str(recommendation.get("trend_summary") or tr("bw_no_clear_trend"))
        )
        self.analysis_focus_label.setText(
            str(recommendation.get("next_focus") or tr("bw_continue_logging"))
        )
        evidence_basis = _build_batch_evidence_basis(
            self._current_batch,
            recommendation,
            self._current_sessions,
            chrono_stats,
            _get_batch_smart_engine_summary(self.db, self._current_batch),
        )
        if hasattr(self, "analysis_basis_label"):
            self.analysis_basis_label.setText(str(evidence_basis.get("message") or "-"))
        workboard = recommendation.get("batch_comparison_workboard") or {}
        display = _build_batch_comparison_workboard_display(
            workboard if isinstance(workboard, dict) else {}
        )
        self._latest_workboard_display = display
        tone_styles = {
            "ready": "background-color: #ecfdf5; color: #166534; border: 1px solid #86efac; border-radius: 6px; padding: 6px;",
            "confirm": "background-color: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; border-radius: 6px; padding: 6px;",
            "watch": "background-color: #fff7ed; color: #c2410c; border: 1px solid #fdba74; border-radius: 6px; padding: 6px;",
            "neutral": "background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px;",
        }
        lane_styles = {
            "shoot_now": tone_styles["ready"],
            "confirm": tone_styles["confirm"],
            "hold": tone_styles["neutral"],
            "pause": tone_styles["watch"],
            "reject_watch": tone_styles["watch"],
        }
        completed_by_batch = getattr(self, "_workboard_completed_lanes_by_batch", {})
        selected_by_batch = getattr(self, "_workboard_selected_lane_by_batch", {})
        completed_lanes = completed_by_batch.get(self.current_batch_id or -1, set())
        selected_lane = selected_by_batch.get(self.current_batch_id or -1, "")
        style = tone_styles.get(
            display.get("tone") or "neutral", tone_styles["neutral"]
        )
        active_lane_text = display.get(selected_lane, "-") if selected_lane else "-"
        if active_lane_text and active_lane_text != "-":
            display["board_hint"] = active_lane_text
        lane_brief = (
            active_lane_text
            if active_lane_text and active_lane_text != "-"
            else display.get("primary_lane_text", "-")
        )
        banner_text = (
            " | ".join(
                part
                for part in (
                    display.get("status", "-"),
                    display.get("board_hint", "-"),
                    display.get("action", "-"),
                )
                if part and part != "-"
            )
            or "-"
        )
        if hasattr(self, "analysis_workboard_banner_label"):
            self.analysis_workboard_banner_label.setText(banner_text)
            self.analysis_workboard_banner_label.setStyleSheet(
                style + " font-weight: 600;"
            )
        if hasattr(self, "analysis_workboard_status_label"):
            self.analysis_workboard_status_label.setText(display.get("status", "-"))
            self.analysis_workboard_status_label.setStyleSheet(style)
        if hasattr(self, "analysis_workboard_summary_label"):
            self.analysis_workboard_summary_label.setText(display.get("summary", "-"))
        if hasattr(self, "analysis_workboard_today_label"):
            self.analysis_workboard_today_label.setText(
                display.get("today_summary", "-")
            )
        if hasattr(self, "analysis_workboard_counts_label"):
            self.analysis_workboard_counts_label.setText(
                display.get("counts_text", "-")
            )
        if hasattr(self, "analysis_workboard_lanes_label"):
            self.analysis_workboard_lanes_label.setText(
                display.get("lanes_summary", "-")
            )
        if hasattr(self, "analysis_workboard_primary_lane_label"):
            self.analysis_workboard_primary_lane_label.setText(
                display.get("primary_lane_text", "-")
            )
        if hasattr(self, "analysis_workboard_board_hint_label"):
            self.analysis_workboard_board_hint_label.setText(
                display.get("board_hint", "-")
            )
        if hasattr(self, "analysis_workboard_lane_brief_label"):
            self.analysis_workboard_lane_brief_label.setText(lane_brief or "-")
        if hasattr(self, "analysis_workboard_first_label"):
            self.analysis_workboard_first_label.setText(display.get("first_batch", "-"))
        if hasattr(self, "analysis_workboard_action_label"):
            self.analysis_workboard_action_label.setText(display.get("action", "-"))
        if hasattr(self, "analysis_workboard_hold_label"):
            self.analysis_workboard_hold_label.setText(display.get("hold_back", "-"))
        if hasattr(self, "analysis_workboard_queue_label"):
            self.analysis_workboard_queue_label.setText(display.get("queue_text", "-"))
        if hasattr(self, "analysis_workboard_shoot_now_label"):
            self.analysis_workboard_shoot_now_label.setText(
                display.get("shoot_now", "-")
            )
            self.analysis_workboard_shoot_now_label.setStyleSheet(
                lane_styles["shoot_now"]
            )
            if hasattr(self, "analysis_workboard_lane_cards"):
                lane_card = self.analysis_workboard_lane_cards.get("shoot_now")
                if lane_card is not None:
                    count = (
                        int((workboard.get("counts") or {}).get("shoot_now") or 0)
                        if isinstance(workboard, dict)
                        else 0
                    )
                    lane_card.setTitle(
                        _build_batch_comparison_lane_title(
                            "shoot_now",
                            count,
                            completed="shoot_now" in completed_lanes,
                            selected=selected_lane == "shoot_now",
                        )
                    )
                    lane_card.setStyleSheet(
                        lane_styles["shoot_now"]
                        + (
                            " border-width: 2px; border-color: #0f172a;"
                            if selected_lane == "shoot_now"
                            else ""
                        )
                        + (
                            " background-color: #dcfce7;"
                            if "shoot_now" in completed_lanes
                            else ""
                        )
                    )
                    lane_card.setToolTip(display.get("shoot_now", "-"))
        if hasattr(self, "analysis_workboard_confirm_label"):
            self.analysis_workboard_confirm_label.setText(display.get("confirm", "-"))
            self.analysis_workboard_confirm_label.setStyleSheet(lane_styles["confirm"])
            if hasattr(self, "analysis_workboard_lane_cards"):
                lane_card = self.analysis_workboard_lane_cards.get("confirm")
                if lane_card is not None:
                    count = (
                        int((workboard.get("counts") or {}).get("confirm") or 0)
                        if isinstance(workboard, dict)
                        else 0
                    )
                    lane_card.setTitle(
                        _build_batch_comparison_lane_title(
                            "confirm",
                            count,
                            completed="confirm" in completed_lanes,
                            selected=selected_lane == "confirm",
                        )
                    )
                    lane_card.setStyleSheet(
                        lane_styles["confirm"]
                        + (
                            " border-width: 2px; border-color: #0f172a;"
                            if selected_lane == "confirm"
                            else ""
                        )
                        + (
                            " background-color: #dcfce7;"
                            if "confirm" in completed_lanes
                            else ""
                        )
                    )
                    lane_card.setToolTip(display.get("confirm", "-"))
        if hasattr(self, "analysis_workboard_hold_lane_label"):
            self.analysis_workboard_hold_lane_label.setText(display.get("hold", "-"))
            self.analysis_workboard_hold_lane_label.setStyleSheet(lane_styles["hold"])
            if hasattr(self, "analysis_workboard_lane_cards"):
                lane_card = self.analysis_workboard_lane_cards.get("hold")
                if lane_card is not None:
                    count = (
                        int((workboard.get("counts") or {}).get("hold") or 0)
                        if isinstance(workboard, dict)
                        else 0
                    )
                    lane_card.setTitle(
                        _build_batch_comparison_lane_title(
                            "hold",
                            count,
                            completed="hold" in completed_lanes,
                            selected=selected_lane == "hold",
                        )
                    )
                    lane_card.setStyleSheet(
                        lane_styles["hold"]
                        + (
                            " border-width: 2px; border-color: #0f172a;"
                            if selected_lane == "hold"
                            else ""
                        )
                        + (
                            " background-color: #dcfce7;"
                            if "hold" in completed_lanes
                            else ""
                        )
                    )
                    lane_card.setToolTip(display.get("hold", "-"))
        if hasattr(self, "analysis_workboard_pause_label"):
            self.analysis_workboard_pause_label.setText(display.get("pause", "-"))
            self.analysis_workboard_pause_label.setStyleSheet(lane_styles["pause"])
            if hasattr(self, "analysis_workboard_lane_cards"):
                lane_card = self.analysis_workboard_lane_cards.get("pause")
                if lane_card is not None:
                    count = (
                        int((workboard.get("counts") or {}).get("pause") or 0)
                        if isinstance(workboard, dict)
                        else 0
                    )
                    lane_card.setTitle(
                        _build_batch_comparison_lane_title(
                            "pause",
                            count,
                            completed="pause" in completed_lanes,
                            selected=selected_lane == "pause",
                        )
                    )
                    lane_card.setStyleSheet(
                        lane_styles["pause"]
                        + (
                            " border-width: 2px; border-color: #0f172a;"
                            if selected_lane == "pause"
                            else ""
                        )
                        + (
                            " background-color: #dcfce7;"
                            if "pause" in completed_lanes
                            else ""
                        )
                    )
                    lane_card.setToolTip(display.get("pause", "-"))
        if hasattr(self, "analysis_workboard_reject_watch_label"):
            self.analysis_workboard_reject_watch_label.setText(
                display.get("reject_watch", "-")
            )
            self.analysis_workboard_reject_watch_label.setStyleSheet(
                lane_styles["reject_watch"]
            )
            if hasattr(self, "analysis_workboard_lane_cards"):
                lane_card = self.analysis_workboard_lane_cards.get("reject_watch")
                if lane_card is not None:
                    count = (
                        int((workboard.get("counts") or {}).get("reject_watch") or 0)
                        if isinstance(workboard, dict)
                        else 0
                    )
                    lane_card.setTitle(
                        _build_batch_comparison_lane_title(
                            "reject_watch",
                            count,
                            completed="reject_watch" in completed_lanes,
                            selected=selected_lane == "reject_watch",
                        )
                    )
                    lane_card.setStyleSheet(
                        lane_styles["reject_watch"]
                        + (
                            " border-width: 2px; border-color: #0f172a;"
                            if selected_lane == "reject_watch"
                            else ""
                        )
                        + (
                            " background-color: #dcfce7;"
                            if "reject_watch" in completed_lanes
                            else ""
                        )
                    )
                    lane_card.setToolTip(display.get("reject_watch", "-"))
        if hasattr(self, "analysis_workboard_lane_done_buttons"):
            for lane_name, button in self.analysis_workboard_lane_done_buttons.items():
                button.blockSignals(True)
                done = lane_name in completed_lanes
                button.setChecked(done)
                button.setText("Done" if done else "Mark Done")
                button.blockSignals(False)
        comparison_prefix = ""
        if comparison_basis.get("available"):
            comparison_prefix = (
                "<p><b>Batch Comparison:</b> "
                f"{comparison_basis.get('summary') or ''}</p>"
            )
        comparison_advisory = recommendation.get("batch_comparison_advisory") or {}
        if isinstance(comparison_advisory, dict) and (
            comparison_advisory.get("title") or comparison_advisory.get("message")
        ):
            comparison_prefix += (
                "<p><b>Comparison Advisory:</b> "
                f"{comparison_advisory.get('title') or ''}: {comparison_advisory.get('message') or ''}"
            )
            if comparison_advisory.get("recommended_action"):
                comparison_prefix += (
                    f" Next gate: {comparison_advisory.get('recommended_action')}"
                )
            comparison_prefix += "</p>"
        comparison_protocol = recommendation.get("batch_comparison_protocol") or {}
        if isinstance(comparison_protocol, dict) and (
            comparison_protocol.get("title")
            or comparison_protocol.get("primary_action")
        ):
            comparison_prefix += (
                "<p><b>Comparison Protocol:</b> "
                f"{comparison_protocol.get('title') or ''}: {comparison_protocol.get('primary_action') or ''}"
            )
            if comparison_protocol.get("shot_plan"):
                comparison_prefix += (
                    f" Shot plan: {comparison_protocol.get('shot_plan')}"
                )
            comparison_prefix += "</p>"
        comparison_explanation = (
            recommendation.get("batch_comparison_explanation") or {}
        )
        if isinstance(comparison_explanation, dict) and (
            comparison_explanation.get("limiting_factor")
            or comparison_explanation.get("reason")
        ):
            comparison_prefix += (
                "<p><b>Comparison Explanation:</b> "
                f"{comparison_explanation.get('limiting_factor') or ''}: {comparison_explanation.get('reason') or ''}"
            )
            if comparison_explanation.get("next_measurement"):
                comparison_prefix += f" Next measurement: {comparison_explanation.get('next_measurement')}"
            comparison_prefix += "</p>"
        comparison_verdict = recommendation.get("batch_comparison_verdict") or {}
        if isinstance(comparison_verdict, dict) and (
            comparison_verdict.get("label") or comparison_verdict.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Comparison Verdict:</b> "
                f"{comparison_verdict.get('label') or ''}: {comparison_verdict.get('summary') or ''}</p>"
            )
        comparison_acceptance = recommendation.get("batch_comparison_acceptance") or {}
        if isinstance(comparison_acceptance, dict) and (
            comparison_acceptance.get("label") or comparison_acceptance.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Comparison Acceptance:</b> "
                f"{comparison_acceptance.get('label') or ''}: {comparison_acceptance.get('summary') or ''}"
            )
            if comparison_acceptance.get("next_gate"):
                comparison_prefix += (
                    f" Next gate: {comparison_acceptance.get('next_gate')}"
                )
            comparison_prefix += "</p>"
        comparison_acceptance_progress = (
            recommendation.get("batch_comparison_acceptance_progress") or {}
        )
        if isinstance(comparison_acceptance_progress, dict) and (
            comparison_acceptance_progress.get("level")
            or comparison_acceptance_progress.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Acceptance Progress:</b> "
                f"{comparison_acceptance_progress.get('level') or ''} ({comparison_acceptance_progress.get('score') or 0}/100)"
            )
            if comparison_acceptance_progress.get("passed_count") not in (
                None,
                "",
            ) and comparison_acceptance_progress.get("total_count") not in (None, ""):
                comparison_prefix += f" Conditions: {comparison_acceptance_progress.get('passed_count')}/{comparison_acceptance_progress.get('total_count')}"
            if comparison_acceptance_progress.get("summary"):
                comparison_prefix += f" {comparison_acceptance_progress.get('summary')}"
            if comparison_acceptance_progress.get("next_target"):
                comparison_prefix += (
                    f" Next target: {comparison_acceptance_progress.get('next_target')}"
                )
            comparison_prefix += "</p>"
        comparison_next_test = recommendation.get("batch_comparison_next_test") or {}
        if isinstance(comparison_next_test, dict) and (
            comparison_next_test.get("title") or comparison_next_test.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Comparison Next Test:</b> "
                f"{comparison_next_test.get('title') or ''}: {comparison_next_test.get('summary') or ''}"
            )
            if comparison_next_test.get("primary_action"):
                comparison_prefix += (
                    f" Action: {comparison_next_test.get('primary_action')}"
                )
            if comparison_next_test.get("check_first"):
                comparison_prefix += (
                    f" First check: {comparison_next_test.get('check_first')}"
                )
            comparison_prefix += "</p>"
        comparison_status_board = (
            recommendation.get("batch_comparison_status_board") or {}
        )
        if isinstance(comparison_status_board, dict) and (
            comparison_status_board.get("headline")
            or comparison_status_board.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Comparison Board:</b> "
                f"{comparison_status_board.get('headline') or ''}"
            )
            if comparison_status_board.get("summary"):
                comparison_prefix += f" {comparison_status_board.get('summary')}"
            comparison_prefix += "</p>"
        comparison_profile_priority = (
            recommendation.get("batch_comparison_profile_priority") or {}
        )
        if isinstance(comparison_profile_priority, dict) and (
            comparison_profile_priority.get("title")
            or comparison_profile_priority.get("emphasis")
        ):
            comparison_prefix += (
                "<p><b>Comparison Profile:</b> "
                f"{comparison_profile_priority.get('title') or ''}: {comparison_profile_priority.get('emphasis') or ''}"
            )
            if comparison_profile_priority.get("guardrail"):
                comparison_prefix += (
                    f" Guardrail: {comparison_profile_priority.get('guardrail')}"
                )
            comparison_prefix += "</p>"
        comparison_mission_brief = (
            recommendation.get("batch_comparison_mission_brief") or {}
        )
        if isinstance(comparison_mission_brief, dict) and (
            comparison_mission_brief.get("mission")
            or comparison_mission_brief.get("primary_action")
        ):
            comparison_prefix += (
                "<p><b>Mission Brief:</b> "
                f"{comparison_mission_brief.get('mission') or ''}"
            )
            if comparison_mission_brief.get("primary_action"):
                comparison_prefix += (
                    f" Action: {comparison_mission_brief.get('primary_action')}"
                )
            if comparison_mission_brief.get("success_marker"):
                comparison_prefix += (
                    f" Success: {comparison_mission_brief.get('success_marker')}"
                )
            comparison_prefix += "</p>"
        comparison_portfolio = recommendation.get("batch_comparison_portfolio") or {}
        if isinstance(comparison_portfolio, dict) and (
            comparison_portfolio.get("title") or comparison_portfolio.get("focus")
        ):
            comparison_prefix += (
                "<p><b>Comparison Portfolio:</b> "
                f"{comparison_portfolio.get('title') or ''}: {comparison_portfolio.get('focus') or ''}</p>"
            )
        comparison_session_strategy = (
            recommendation.get("batch_comparison_session_strategy") or {}
        )
        if isinstance(comparison_session_strategy, dict) and (
            comparison_session_strategy.get("title")
            or comparison_session_strategy.get("objective")
        ):
            comparison_prefix += (
                "<p><b>Session Strategy:</b> "
                f"{comparison_session_strategy.get('title') or ''}: {comparison_session_strategy.get('objective') or ''}"
            )
            if comparison_session_strategy.get("primary_action"):
                comparison_prefix += (
                    f" Action: {comparison_session_strategy.get('primary_action')}"
                )
            comparison_prefix += "</p>"
        comparison_campaign_view = (
            recommendation.get("batch_comparison_campaign_view") or {}
        )
        if isinstance(comparison_campaign_view, dict) and (
            comparison_campaign_view.get("title")
            or comparison_campaign_view.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Campaign View:</b> "
                f"{comparison_campaign_view.get('title') or ''}: {comparison_campaign_view.get('summary') or ''}</p>"
            )
        comparison_action_plan = (
            recommendation.get("batch_comparison_action_plan") or {}
        )
        if isinstance(comparison_action_plan, dict) and (
            comparison_action_plan.get("title") or comparison_action_plan.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Action Plan:</b> "
                f"{comparison_action_plan.get('title') or ''}: {comparison_action_plan.get('summary') or ''}"
            )
            if comparison_action_plan.get("primary_action"):
                comparison_prefix += (
                    f" Action: {comparison_action_plan.get('primary_action')}"
                )
            comparison_prefix += "</p>"
        comparison_campaign_board = (
            recommendation.get("batch_comparison_campaign_board") or {}
        )
        if isinstance(comparison_campaign_board, dict) and (
            comparison_campaign_board.get("title")
            or comparison_campaign_board.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Campaign Board:</b> "
                f"{comparison_campaign_board.get('title') or ''}: {comparison_campaign_board.get('summary') or ''}</p>"
            )
            preview_rows = (
                comparison_campaign_board.get("preview")
                if isinstance(comparison_campaign_board.get("preview"), list)
                else []
            )
            if preview_rows:
                comparison_prefix += (
                    "<p><b>Board Preview:</b> "
                    + " | ".join(
                        str(item).strip()
                        for item in preview_rows[:3]
                        if str(item).strip()
                    )
                    + "</p>"
                )
        comparison_session_queue = (
            recommendation.get("batch_comparison_session_queue") or {}
        )
        if isinstance(comparison_session_queue, dict) and (
            comparison_session_queue.get("title")
            or comparison_session_queue.get("first_batch_name")
        ):
            comparison_prefix += (
                "<p><b>Session Queue:</b> "
                f"{comparison_session_queue.get('title') or ''}"
            )
            if comparison_session_queue.get("first_batch_name"):
                comparison_prefix += (
                    f" First batch: {comparison_session_queue.get('first_batch_name')}"
                )
            comparison_prefix += "</p>"
            queue_preview = (
                comparison_session_queue.get("preview")
                if isinstance(comparison_session_queue.get("preview"), list)
                else []
            )
            if queue_preview:
                comparison_prefix += (
                    "<p><b>Queue Preview:</b> "
                    + " | ".join(
                        str(item).strip()
                        for item in queue_preview[:3]
                        if str(item).strip()
                    )
                    + "</p>"
                )
        comparison_session_manifest = (
            recommendation.get("batch_comparison_session_manifest") or {}
        )
        if isinstance(comparison_session_manifest, dict) and (
            comparison_session_manifest.get("title")
            or comparison_session_manifest.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Session Manifest:</b> "
                f"{comparison_session_manifest.get('title') or ''}"
            )
            if comparison_session_manifest.get("summary"):
                comparison_prefix += f": {comparison_session_manifest.get('summary')}"
            if comparison_session_manifest.get("primary_bucket"):
                comparison_prefix += f" Primary bucket: {comparison_session_manifest.get('primary_bucket')}"
            if comparison_session_manifest.get("first_batch_name"):
                comparison_prefix += f" First batch: {comparison_session_manifest.get('first_batch_name')}"
            comparison_prefix += "</p>"
            manifest_preview = (
                comparison_session_manifest.get("queue_preview")
                if isinstance(comparison_session_manifest.get("queue_preview"), list)
                else []
            )
            if manifest_preview:
                comparison_prefix += (
                    "<p><b>Manifest Preview:</b> "
                    + " | ".join(
                        str(item).strip()
                        for item in manifest_preview[:3]
                        if str(item).strip()
                    )
                    + "</p>"
                )
            lane_summaries = (
                comparison_session_manifest.get("lane_summaries")
                if isinstance(comparison_session_manifest.get("lane_summaries"), list)
                else []
            )
            if lane_summaries:
                comparison_prefix += (
                    "<p><b>Manifest Lanes:</b> "
                    + " | ".join(
                        str(item.get("summary") or "").strip()
                        for item in lane_summaries[:4]
                        if isinstance(item, dict)
                        and str(item.get("summary") or "").strip()
                    )
                    + "</p>"
                )
        comparison_next_session_brief = (
            recommendation.get("batch_comparison_next_session_brief") or {}
        )
        if isinstance(comparison_next_session_brief, dict) and (
            comparison_next_session_brief.get("title")
            or comparison_next_session_brief.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Next Session Brief:</b> "
                f"{comparison_next_session_brief.get('title') or ''}"
            )
            if comparison_next_session_brief.get("summary"):
                comparison_prefix += f": {comparison_next_session_brief.get('summary')}"
            if comparison_next_session_brief.get("primary_action"):
                comparison_prefix += (
                    f" Action: {comparison_next_session_brief.get('primary_action')}"
                )
            if comparison_next_session_brief.get("hold_back"):
                comparison_prefix += (
                    f" Hold back: {comparison_next_session_brief.get('hold_back')}"
                )
            comparison_prefix += "</p>"
        comparison_today_plan = recommendation.get("batch_comparison_today_plan") or {}
        if isinstance(comparison_today_plan, dict) and (
            comparison_today_plan.get("title") or comparison_today_plan.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Today Plan:</b> " f"{comparison_today_plan.get('title') or ''}"
            )
            if comparison_today_plan.get("summary"):
                comparison_prefix += f": {comparison_today_plan.get('summary')}"
            if comparison_today_plan.get("primary_action"):
                comparison_prefix += (
                    f" Action: {comparison_today_plan.get('primary_action')}"
                )
            comparison_prefix += "</p>"
        comparison_workboard = recommendation.get("batch_comparison_workboard") or {}
        if isinstance(comparison_workboard, dict) and (
            comparison_workboard.get("title") or comparison_workboard.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Workboard:</b> " f"{comparison_workboard.get('title') or ''}"
            )
            if comparison_workboard.get("summary"):
                comparison_prefix += f": {comparison_workboard.get('summary')}"
            if comparison_workboard.get("status_label"):
                comparison_prefix += (
                    f" Status: {comparison_workboard.get('status_label')}"
                )
            counts = (
                comparison_workboard.get("counts")
                if isinstance(comparison_workboard.get("counts"), dict)
                else {}
            )
            counts_text = " | ".join(
                f"{bucket} {int(value)}"
                for bucket, value in (
                    ("shoot_now", counts.get("shoot_now") or 0),
                    ("confirm", counts.get("confirm") or 0),
                    ("hold", counts.get("hold") or 0),
                    ("pause", counts.get("pause") or 0),
                    ("reject_watch", counts.get("reject_watch") or 0),
                )
                if int(value) > 0
            )
            if counts_text:
                comparison_prefix += f" Counts: {counts_text}"
            first_batch_name = str(
                comparison_workboard.get("first_batch_name") or ""
            ).strip()
            if first_batch_name:
                comparison_prefix += f" Run first: {first_batch_name}"
            lane_summaries = (
                comparison_workboard.get("lane_summaries")
                if isinstance(comparison_workboard.get("lane_summaries"), list)
                else []
            )
            lane_text = " | ".join(
                str(item.get("summary") or "").strip()
                for item in lane_summaries[:4]
                if isinstance(item, dict) and str(item.get("summary") or "").strip()
            )
            if lane_text:
                comparison_prefix += f" Lanes: {lane_text}"
            if comparison_workboard.get("primary_action"):
                comparison_prefix += (
                    f" Action: {comparison_workboard.get('primary_action')}"
                )
            if comparison_workboard.get("hold_back"):
                comparison_prefix += (
                    f" Hold back: {comparison_workboard.get('hold_back')}"
                )
            comparison_prefix += "</p>"
        comparison_checklist = recommendation.get("batch_comparison_checklist") or {}
        if isinstance(comparison_checklist, dict) and (
            comparison_checklist.get("title")
            or comparison_checklist.get("highest_priority")
        ):
            comparison_prefix += (
                "<p><b>Comparison Checklist:</b> "
                f"{comparison_checklist.get('title') or ''}"
            )
            if comparison_checklist.get("highest_priority"):
                comparison_prefix += (
                    f" First check: {comparison_checklist.get('highest_priority')}"
                )
            comparison_prefix += "</p>"
        comparison_scorecard = recommendation.get("batch_comparison_scorecard") or {}
        if isinstance(comparison_scorecard, dict) and (
            comparison_scorecard.get("swing_factor")
            or comparison_scorecard.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Comparison Scorecard:</b> "
                f"{comparison_scorecard.get('swing_factor') or ''}: {comparison_scorecard.get('summary') or ''}"
            )
            if comparison_scorecard.get("delta_precision") not in (None, ""):
                comparison_prefix += (
                    f" Precision delta: {comparison_scorecard.get('delta_precision')}"
                )
            if comparison_scorecard.get("delta_evidence_quality") not in (None, ""):
                comparison_prefix += f" Evidence delta: {comparison_scorecard.get('delta_evidence_quality')}"
            if comparison_scorecard.get("delta_readiness") not in (None, ""):
                comparison_prefix += (
                    f" Readiness delta: {comparison_scorecard.get('delta_readiness')}"
                )
            comparison_prefix += "</p>"
        comparison_confidence = recommendation.get("batch_comparison_confidence") or {}
        if isinstance(comparison_confidence, dict) and (
            comparison_confidence.get("level") or comparison_confidence.get("summary")
        ):
            comparison_prefix += (
                "<p><b>Comparison Confidence:</b> "
                f"{comparison_confidence.get('level') or ''} ({comparison_confidence.get('score') or 0}/100): {comparison_confidence.get('summary') or ''}</p>"
            )
        comparison_learning_note = (
            recommendation.get("batch_comparison_learning_note") or {}
        )
        if isinstance(comparison_learning_note, dict) and (
            comparison_learning_note.get("plain_summary")
            or comparison_learning_note.get("takeaway")
        ):
            comparison_prefix += (
                "<p><b>Comparison Learning:</b> "
                f"{comparison_learning_note.get('plain_summary') or ''}"
            )
            if comparison_learning_note.get("takeaway"):
                comparison_prefix += (
                    f" Takeaway: {comparison_learning_note.get('takeaway')}"
                )
            comparison_prefix += "</p>"
        direct_model_match = recommendation.get("direct_model_match_advisory") or {}
        direct_prefix = ""
        if isinstance(direct_model_match, dict) and direct_model_match.get("title"):
            direct_prefix = (
                "<p><b>Direct Batch Check:</b> "
                f"{direct_model_match['title']}: {direct_model_match['message']}</p>"
            )
        model_match_summary = _format_model_match_summary(recommendation)
        if model_match_summary:
            prefix = (
                f"{comparison_prefix}{direct_prefix}<p><b>Model vs Measured:</b> "
                f"{model_match_summary}</p>"
            )
            self.analysis_text.setHtml(prefix + analyzer.to_html())
        elif direct_prefix or comparison_prefix:
            self.analysis_text.setHtml(
                f"{comparison_prefix}{direct_prefix}" + analyzer.to_html()
            )
        else:
            self.analysis_text.setHtml(analyzer.to_html())

    def _copy_workboard_today_plan(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        text = _build_batch_comparison_workboard_copy_text(
            getattr(self, "_latest_workboard_display", {}),
            mode="today",
        )
        clipboard.setText(text)

    def _copy_workboard_queue(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        text = _build_batch_comparison_workboard_copy_text(
            getattr(self, "_latest_workboard_display", {}),
            mode="queue",
        )
        clipboard.setText(text)

    def _copy_workboard_full(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        text = _build_batch_comparison_workboard_copy_text(
            getattr(self, "_latest_workboard_display", {}),
            mode="full",
        )
        clipboard.setText(text)

    def _focus_workboard_lane(self, lane_name: str) -> None:
        if not self.current_batch_id:
            return
        self._workboard_selected_lane_by_batch[self.current_batch_id] = lane_name
        _store_workboard_lane_ui_state(
            self.current_batch_id,
            self._workboard_completed_lanes_by_batch.get(self.current_batch_id, set()),
            lane_name,
        )
        self.refresh_analysis()

    def _copy_workboard_lane(self, lane_name: str) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        text = (
            str(
                getattr(self, "_latest_workboard_display", {}).get(lane_name) or ""
            ).strip()
            or "-"
        )
        clipboard.setText(text)

    def _toggle_workboard_lane_done(self, lane_name: str, checked: bool) -> None:
        if not self.current_batch_id:
            return
        completed = self._workboard_completed_lanes_by_batch.setdefault(
            self.current_batch_id, set()
        )
        if checked:
            completed.add(lane_name)
        else:
            completed.discard(lane_name)
        _store_workboard_lane_ui_state(
            self.current_batch_id,
            completed,
            self._workboard_selected_lane_by_batch.get(self.current_batch_id, ""),
        )
        self.refresh_analysis()

    def _reset_workboard_state(self) -> None:
        if not self.current_batch_id:
            return
        self._workboard_completed_lanes_by_batch[self.current_batch_id] = set()
        self._workboard_selected_lane_by_batch.pop(self.current_batch_id, None)
        _store_workboard_lane_ui_state(self.current_batch_id, set(), "")
        self.refresh_analysis()

    def _combined_chronograph_stats(self) -> Dict[str, Any]:
        import_ids = [
            session.get("chronograph_import_id")
            for session in self._current_sessions
            if session.get("chronograph_import_id")
        ]
        if not import_ids:
            return {}
        velocities: List[float] = []
        for import_id in import_ids:
            rows = self.db.execute_query(
                "SELECT * FROM chronograph_imports WHERE id = ?",
                (import_id,),
            )
            if not rows:
                continue
            row = rows[0]
            raw = row.get("velocities_json") or "[]"
            try:
                velocities.extend(float(v) for v in json.loads(raw))
            except Exception:
                continue
        if not velocities:
            return {}
        avg = statistics.mean(velocities)
        es = max(velocities) - min(velocities)
        sd = statistics.stdev(velocities) if len(velocities) > 1 else 0.0
        return {
            "count": len(velocities),
            "avg": avg,
            "es": es,
            "sd": sd,
            "min": min(velocities),
            "max": max(velocities),
        }
