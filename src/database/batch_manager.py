"""
Batch management helpers for the load development workspace.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

GRAINS_TO_GRAMS = 0.06479891


def _find_active_lot(cursor, component_type: str, component_id: int) -> Optional[int]:
    """Find an active component_lots.id for given component, or None."""
    cursor.execute(
        "SELECT id FROM component_lots WHERE component_type = ? AND component_id = ? AND is_active = 1 ORDER BY created_date ASC LIMIT 1",
        (component_type, component_id),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _utcnow() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _json_dump(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, default=str)


def _resolve_load_session_id(
    db,
    *,
    explicit_load_session_id: Optional[int] = None,
    batch_id: Optional[int] = None,
) -> Optional[int]:
    if explicit_load_session_id not in (None, ""):
        try:
            return int(explicit_load_session_id)
        except Exception:
            return None
    if batch_id in (None, ""):
        return None
    try:
        rows = db.execute_query(
            "SELECT load_session_id FROM batch_projects WHERE id = ? LIMIT 1",
            (int(batch_id),),
        )
    except Exception:
        return None
    if not rows:
        return None
    value = rows[0].get("load_session_id")
    try:
        return int(value) if value not in (None, "") else None
    except Exception:
        return None


def _normalize_update_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure dict/list payloads are stored as JSON strings in TEXT columns."""
    normalized: Dict[str, Any] = {}
    for key, value in (data or {}).items():
        if isinstance(value, (dict, list)):
            normalized[key] = json.dumps(value, ensure_ascii=False, default=str)
        else:
            normalized[key] = value
    return normalized


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _batch_media_root(db, batch_number: str) -> Path:
    db_path = Path(getattr(db, "db_path", os.getcwd()))
    if db_path.suffix:
        root = db_path.parent
    else:
        root = db_path
    return _ensure_dir(root / "batch_media" / batch_number)


def _generate_batch_number(db) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"BATCH-{stamp}"
    candidate = base
    suffix = 1
    while True:
        row = db.execute_query(
            "SELECT id FROM batch_projects WHERE batch_number = ? LIMIT 1",
            (candidate,),
        )
        if not row:
            return candidate
        candidate = f"{base}-{suffix:02d}"
        suffix += 1


def list_batch_projects(
    db,
    status: Optional[str] = None,
    rifle_id: Optional[int] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = """
        SELECT
            bp.*,
            r.name AS rifle_name,
            r.caliber AS rifle_caliber,
            (SELECT COUNT(*) FROM batch_project_notes n WHERE n.batch_id = bp.id) AS note_count,
            (SELECT COUNT(*) FROM batch_project_sessions s WHERE s.batch_id = bp.id) AS session_count,
            (SELECT COUNT(*) FROM batch_project_attachments a WHERE a.batch_id = bp.id) AS attachment_count
        FROM batch_projects bp
        LEFT JOIN rifles r ON r.id = bp.rifle_id
        WHERE 1=1
    """
    params: list[Any] = []

    if status:
        query += " AND bp.status = ?"
        params.append(status)
    if rifle_id:
        query += " AND bp.rifle_id = ?"
        params.append(rifle_id)
    if search:
        query += " AND (bp.batch_name LIKE ? OR bp.batch_number LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY bp.updated_date DESC, bp.created_date DESC"
    return db.execute_query(query, tuple(params))


def get_batch_project(db, batch_id: int) -> Optional[Dict[str, Any]]:
    rows = db.execute_query(
        """
        SELECT
            bp.*,
            r.name AS rifle_name,
            r.caliber AS rifle_caliber,
            ap.name AS ammo_profile_name
        FROM batch_projects bp
        LEFT JOIN rifles r ON r.id = bp.rifle_id
        LEFT JOIN ammo_profiles ap ON ap.id = bp.ammo_profile_id
        WHERE bp.id = ?
        """,
        (batch_id,),
    )
    return rows[0] if rows else None


def get_batch_notes(db, batch_id: int) -> List[Dict[str, Any]]:
    return db.execute_query(
        "SELECT * FROM batch_project_notes WHERE batch_id = ? ORDER BY datetime(created_date) DESC, id DESC",
        (batch_id,),
    )


def get_batch_attachments(db, batch_id: int) -> List[Dict[str, Any]]:
    return db.execute_query(
        "SELECT * FROM batch_project_attachments WHERE batch_id = ? ORDER BY datetime(created_date) DESC, id DESC",
        (batch_id,),
    )


def get_batch_sessions(db, batch_id: int) -> List[Dict[str, Any]]:
    return db.execute_query(
        "SELECT * FROM batch_project_sessions WHERE batch_id = ? ORDER BY datetime(session_date) DESC, id DESC",
        (batch_id,),
    )


def create_batch_project(
    db,
    batch_name: str,
    rifle_id: int,
    *,
    barrel_id: Optional[str] = None,
    barrel_name: Optional[str] = None,
    barrel_configuration_id: Optional[str] = None,
    barrel_configuration_name: Optional[str] = None,
    load_session_id: Optional[int] = None,
    ammo_profile_id: Optional[int] = None,
    load_recipe_id: Optional[int] = None,
    brass_batch_id: Optional[int] = None,
    bullet_id: Optional[int] = None,
    powder_id: Optional[int] = None,
    primer_id: Optional[int] = None,
    case_id: Optional[int] = None,
    source_workflow: Optional[str] = None,
    usage_profile_key: Optional[str] = None,
    subsonic_mode: bool = False,
    target_distance_m: Optional[int] = None,
    target_group_mm: Optional[float] = None,
    target_es_fps: Optional[float] = None,
    charge_weight_grains: Optional[float] = None,
    coal_mm: Optional[float] = None,
    cbto_mm: Optional[float] = None,
    neck_tension_inches: Optional[float] = None,
    barrel_configuration_snapshot: Optional[Dict[str, Any]] = None,
    component_snapshot: Optional[Dict[str, Any]] = None,
    analysis_json: Optional[Dict[str, Any]] = None,
    notes: str = "",
) -> Dict[str, Any]:
    batch_number = _generate_batch_number(db)
    snapshot = component_snapshot or {}
    cur = db.cursor
    cur.execute(
        """
        INSERT INTO batch_projects (
            batch_number, batch_name, rifle_id, barrel_id, barrel_name,
            barrel_configuration_id, barrel_configuration_name,
            load_session_id, ammo_profile_id, load_recipe_id,
            brass_batch_id, bullet_id, powder_id, primer_id, case_id,
            source_workflow, status, usage_profile_key, subsonic_mode,
            target_distance_m, target_group_mm, target_es_fps,
            charge_weight_grains, coal_mm, cbto_mm, neck_tension_inches,
            barrel_configuration_snapshot_json, component_snapshot_json,
            analysis_json, notes, created_date, updated_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            batch_number,
            batch_name,
            rifle_id,
            barrel_id,
            barrel_name,
            barrel_configuration_id,
            barrel_configuration_name,
            load_session_id,
            ammo_profile_id,
            load_recipe_id,
            brass_batch_id,
            bullet_id,
            powder_id,
            primer_id,
            case_id,
            source_workflow,
            usage_profile_key,
            1 if subsonic_mode else 0,
            target_distance_m,
            target_group_mm,
            target_es_fps,
            charge_weight_grains,
            coal_mm,
            cbto_mm,
            neck_tension_inches,
            _json_dump(barrel_configuration_snapshot or {}),
            _json_dump(snapshot),
            _json_dump(analysis_json or {}),
            notes,
            _utcnow(),
            _utcnow(),
        ),
    )
    db.conn.commit()
    batch_id = cur.lastrowid
    return {
        "ok": True,
        "batch_id": batch_id,
        "batch_number": batch_number,
        "batch_name": batch_name,
    }


def update_batch_project(db, batch_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    data = _normalize_update_payload(dict(data or {}))
    data["updated_date"] = _utcnow()
    db.update("batch_projects", data, "id = ?", (batch_id,))
    return {"ok": True, "updated": len(data)}


def add_batch_note(
    db,
    batch_id: int,
    note_text: str,
    *,
    title: Optional[str] = None,
    note_type: str = "note",
) -> Dict[str, Any]:
    cur = db.cursor
    cur.execute(
        """
        INSERT INTO batch_project_notes (batch_id, note_type, title, note_text, created_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (batch_id, note_type, title, note_text, _utcnow()),
    )
    db.conn.commit()
    update_batch_project(db, batch_id, {})
    return {"ok": True, "note_id": cur.lastrowid}


def add_batch_attachment(
    db,
    batch_id: int,
    file_path: str,
    *,
    attachment_type: str = "photo",
    caption: str = "",
) -> Dict[str, Any]:
    cur = db.cursor
    cur.execute(
        """
        INSERT INTO batch_project_attachments (batch_id, attachment_type, file_path, caption, created_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (batch_id, attachment_type, file_path, caption, _utcnow()),
    )
    db.conn.commit()
    update_batch_project(db, batch_id, {})
    return {"ok": True, "attachment_id": cur.lastrowid}


def add_batch_session(
    db,
    batch_id: int,
    *,
    load_session_id: Optional[int] = None,
    rifle_id: Optional[int] = None,
    barrel_id: Optional[str] = None,
    barrel_name: Optional[str] = None,
    barrel_configuration_id: Optional[str] = None,
    barrel_configuration_name: Optional[str] = None,
    session_name: Optional[str] = None,
    session_date: Optional[str] = None,
    session_type: str = "range",
    distance_m: Optional[int] = None,
    temperature_c: Optional[float] = None,
    wind_speed_mps: Optional[float] = None,
    humidity_percent: Optional[float] = None,
    suppressor_used: Optional[bool] = None,
    muzzle_device_type: Optional[str] = None,
    shot_count: Optional[int] = None,
    group_size_mm: Optional[float] = None,
    group_size_moa: Optional[float] = None,
    function_status: Optional[str] = None,
    tester_verdict: Optional[str] = None,
    chronograph_import_id: Optional[int] = None,
    target_photo_path: Optional[str] = None,
    setup_photo_path: Optional[str] = None,
    additional_photos: Optional[list[str]] = None,
    notes: str = "",
    primer_observation_json: Optional[Dict[str, Any]] = None,
    chronograph_summary_json: Optional[Dict[str, Any]] = None,
    analysis_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    resolved_load_session_id = _resolve_load_session_id(
        db,
        explicit_load_session_id=load_session_id,
        batch_id=batch_id,
    )
    cur = db.cursor
    cur.execute(
        """
        INSERT INTO batch_project_sessions (
            batch_id, load_session_id, rifle_id, barrel_id, barrel_name,
            barrel_configuration_id, barrel_configuration_name,
            session_name, session_date, session_type, distance_m,
            temperature_c, wind_speed_mps, humidity_percent, suppressor_used,
            muzzle_device_type, shot_count, group_size_mm, group_size_moa,
            function_status, tester_verdict, chronograph_import_id,
            target_photo_path, setup_photo_path, additional_photos_json,
            notes, primer_observation_json, chronograph_summary_json,
            analysis_json, created_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            batch_id,
            resolved_load_session_id,
            rifle_id,
            barrel_id,
            barrel_name,
            barrel_configuration_id,
            barrel_configuration_name,
            session_name,
            session_date or _utcnow(),
            session_type,
            distance_m,
            temperature_c,
            wind_speed_mps,
            humidity_percent,
            None if suppressor_used is None else (1 if suppressor_used else 0),
            muzzle_device_type,
            shot_count,
            group_size_mm,
            group_size_moa,
            function_status,
            tester_verdict,
            chronograph_import_id,
            target_photo_path,
            setup_photo_path,
            _json_dump(additional_photos or []),
            notes,
            _json_dump(primer_observation_json or {}),
            _json_dump(chronograph_summary_json or {}),
            _json_dump(analysis_json or {}),
            _utcnow(),
        ),
    )
    db.conn.commit()
    update_batch_project(db, batch_id, {})
    return {"ok": True, "session_id": cur.lastrowid}


def store_manual_chronograph_for_batch(
    db,
    batch_id: int,
    velocities: List[float],
    *,
    load_session_id: Optional[int] = None,
    ammo_profile_id: Optional[int] = None,
    note: Optional[str] = None,
    session_name: Optional[str] = None,
) -> Dict[str, Any]:
    from src.utils.chronograph_import import import_velocities

    resolved_load_session_id = _resolve_load_session_id(
        db,
        explicit_load_session_id=load_session_id,
        batch_id=batch_id,
    )

    import_result = import_velocities(
        db,
        velocities,
        ammo_profile_id=ammo_profile_id,
        load_session_id=resolved_load_session_id,
        note=note or f"Manual entry for batch {batch_id}",
    )
    stats = import_result.get("stats", {})
    add_batch_session(
        db,
        batch_id,
        session_name=session_name or f"Chronograph {import_result.get('import_id')}",
        session_type="chronograph",
        shot_count=stats.get("count"),
        notes=note or "",
        chronograph_import_id=import_result.get("import_id"),
        load_session_id=resolved_load_session_id,
        analysis_json={"velocities": velocities, "stats": stats},
    )
    return import_result


def create_loading_batch(
    db,
    ammo_profile_id: int,
    name: str,
    batch_size: int,
    powder_charge_grains: float,
    coal_mm: Optional[float] = None,
    cbto_mm: Optional[float] = None,
    load_session_id: Optional[int] = None,
) -> Dict:
    """
    Create a loading batch for given `ammo_profile_id` and decrement inventory accordingly.

    Returns dict: {"ok": bool, "message": str, "batch_id": Optional[int]}
    """
    cur = db.cursor

    # Load ammo profile
    cur.execute("SELECT * FROM ammo_profiles WHERE id = ?", (ammo_profile_id,))
    profile = cur.fetchone()
    if not profile:
        return {"ok": False, "message": "Ammo profile not found", "batch_id": None}

    powder_id = profile["powder_id"]
    bullet_id = profile["bullet_id"]
    case_id = profile["case_id"]
    primer_id = profile["primer_id"]

    # Compute powder usage (grams)
    powder_needed_grams = powder_charge_grains * batch_size * GRAINS_TO_GRAMS

    # Check availability
    if powder_id:
        cur.execute("SELECT quantity_grams FROM powder WHERE id = ?", (powder_id,))
        r = cur.fetchone()
        if not r:
            return {"ok": False, "message": "Powder not found", "batch_id": None}
        if (r[0] or 0) < powder_needed_grams:
            return {
                "ok": False,
                "message": "Insufficient powder quantity",
                "batch_id": None,
            }

    if bullet_id:
        cur.execute("SELECT quantity FROM bullets WHERE id = ?", (bullet_id,))
        r = cur.fetchone()
        if not r:
            return {"ok": False, "message": "Bullet not found", "batch_id": None}
        if (r[0] or 0) < batch_size:
            return {"ok": False, "message": "Insufficient bullets", "batch_id": None}

    if case_id:
        cur.execute("SELECT quantity FROM cases WHERE id = ?", (case_id,))
        r = cur.fetchone()
        if not r:
            return {"ok": False, "message": "Case (brass) not found", "batch_id": None}
        if (r[0] or 0) < batch_size:
            return {
                "ok": False,
                "message": "Insufficient cases (brass)",
                "batch_id": None,
            }

    if primer_id:
        cur.execute("SELECT quantity FROM primers WHERE id = ?", (primer_id,))
        r = cur.fetchone()
        if not r:
            return {"ok": False, "message": "Primer not found", "batch_id": None}
        if (r[0] or 0) < batch_size:
            return {"ok": False, "message": "Insufficient primers", "batch_id": None}

    # Everything OK: create qc_batch and loading_session
    cur.execute(
        "INSERT INTO qc_batches (name, target_charge, charge_tolerance, target_coal, coal_tolerance, batch_size, status) VALUES (?, ?, ?, ?, ?, ?, 'completed')",
        (name, float(powder_charge_grains), 0.1, coal_mm or None, 0.1, batch_size),
    )
    batch_id = cur.lastrowid

    cur.execute(
        "INSERT INTO loading_sessions (date, ammo_profile_id, quantity, coal_min, coal_max, powder_weight_min, powder_weight_max, notes, load_session_id) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            ammo_profile_id,
            batch_size,
            coal_mm,
            coal_mm,
            float(powder_charge_grains),
            float(powder_charge_grains),
            f"Batch {name} created",
            load_session_id,
        ),
    )
    session_id = cur.lastrowid

    # Decrement inventories and component_lots quantities
    if powder_id:
        # update powder table
        cur.execute(
            "UPDATE powder SET quantity_grams = quantity_grams - ? WHERE id = ?",
            (powder_needed_grams, powder_id),
        )
        # decrement component lot
        lot_id = _find_active_lot(cur, "powder", powder_id)
        if lot_id:
            cur.execute(
                "UPDATE component_lots SET quantity_remaining = quantity_remaining - ? WHERE id = ?",
                (powder_needed_grams, lot_id),
            )

    if bullet_id:
        cur.execute(
            "UPDATE bullets SET quantity = quantity - ? WHERE id = ?",
            (batch_size, bullet_id),
        )
        lot_id = _find_active_lot(cur, "bullet", bullet_id)
        if lot_id:
            cur.execute(
                "UPDATE component_lots SET quantity_remaining = quantity_remaining - ? WHERE id = ?",
                (batch_size, lot_id),
            )

    if case_id:
        cur.execute(
            "UPDATE cases SET quantity = quantity - ? WHERE id = ?",
            (batch_size, case_id),
        )
        lot_id = _find_active_lot(cur, "case", case_id)
        if lot_id:
            cur.execute(
                "UPDATE component_lots SET quantity_remaining = quantity_remaining - ? WHERE id = ?",
                (batch_size, lot_id),
            )

    if primer_id:
        cur.execute(
            "UPDATE primers SET quantity = quantity - ? WHERE id = ?",
            (batch_size, primer_id),
        )
        lot_id = _find_active_lot(cur, "primer", primer_id)
        if lot_id:
            cur.execute(
                "UPDATE component_lots SET quantity_remaining = quantity_remaining - ? WHERE id = ?",
                (batch_size, lot_id),
            )

    db.conn.commit()

    return {
        "ok": True,
        "message": "Batch created",
        "batch_id": batch_id,
        "session_id": session_id,
    }
