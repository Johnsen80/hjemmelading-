"""
Batch management helpers: create batches and decrement inventory
"""

from typing import Dict, Optional

GRAINS_TO_GRAMS = 0.06479891


def _find_active_lot(cursor, component_type: str, component_id: int) -> Optional[int]:
    """Find an active component_lots.id for given component, or None."""
    cursor.execute(
        "SELECT id FROM component_lots WHERE component_type = ? AND component_id = ? AND is_active = 1 ORDER BY created_date ASC LIMIT 1",
        (component_type, component_id),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def create_loading_batch(
    db,
    ammo_profile_id: int,
    name: str,
    batch_size: int,
    powder_charge_grains: float,
    coal_mm: Optional[float] = None,
    cbto_mm: Optional[float] = None,
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
        "INSERT INTO loading_sessions (date, ammo_profile_id, quantity, coal_min, coal_max, powder_weight_min, powder_weight_max, notes) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)",
        (
            ammo_profile_id,
            batch_size,
            coal_mm,
            coal_mm,
            float(powder_charge_grains),
            float(powder_charge_grains),
            f"Batch {name} created",
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
