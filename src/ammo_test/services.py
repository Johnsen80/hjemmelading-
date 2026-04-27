"""Business logic for the ammo test module."""

from __future__ import annotations

import statistics
from datetime import date
from typing import Any

from .models import AmmoLot, AmmoTestSession, AmmoTestShot, LotComparisonResult


def _db_row(row: Any) -> dict[str, Any]:
    return dict(row) if not isinstance(row, dict) else row


# ---------------------------------------------------------------------------
# Lot CRUD
# ---------------------------------------------------------------------------


def save_lot(db: Any, lot: AmmoLot) -> int:
    data = {
        "brand": lot.brand,
        "model": lot.model,
        "caliber": lot.caliber,
        "bullet_weight_gr": lot.bullet_weight_gr,
        "lot_number": lot.lot_number,
        "purchase_date": lot.purchase_date,
        "purchase_price": lot.purchase_price,
        "store": lot.store,
        "count_purchased": lot.count_purchased,
        "count_remaining": lot.count_remaining,
        "expiry_date": lot.expiry_date,
        "storage_notes": lot.storage_notes,
        "notes": lot.notes,
    }
    if lot.id:
        db.update("ammo_lots", data, "id = ?", (lot.id,))
        return lot.id
    else:
        db.insert("ammo_lots", data)
        rows = db.execute_query("SELECT last_insert_rowid() AS id")
        return int(rows[0]["id"]) if rows else -1


def delete_lot(db: Any, lot_id: int) -> None:
    sessions = db.execute_query(
        "SELECT id FROM ammo_test_sessions WHERE lot_id = ?", (lot_id,)
    )
    for s in sessions:
        delete_session(db, s["id"])
    db.delete("ammo_lots", "id = ?", (lot_id,))


def get_lot(db: Any, lot_id: int) -> AmmoLot | None:
    rows = db.execute_query("SELECT * FROM ammo_lots WHERE id = ?", (lot_id,))
    return AmmoLot.from_row(_db_row(rows[0])) if rows else None


def list_lots(
    db: Any, brand: str | None = None, caliber: str | None = None
) -> list[AmmoLot]:
    q = "SELECT * FROM ammo_lots WHERE 1=1"
    params: list[Any] = []
    if brand:
        q += " AND brand = ?"
        params.append(brand)
    if caliber:
        q += " AND caliber = ?"
        params.append(caliber)
    q += " ORDER BY brand, model, purchase_date DESC"
    return [AmmoLot.from_row(_db_row(r)) for r in db.execute_query(q, tuple(params))]


def list_brands(db: Any) -> list[str]:
    rows = db.execute_query("SELECT DISTINCT brand FROM ammo_lots ORDER BY brand")
    return [r["brand"] for r in rows if r.get("brand")]


def list_calibers(db: Any) -> list[str]:
    rows = db.execute_query("SELECT DISTINCT caliber FROM ammo_lots ORDER BY caliber")
    return [r["caliber"] for r in rows if r.get("caliber")]


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


def save_session(db: Any, session: AmmoTestSession) -> int:
    data = {
        "lot_id": session.lot_id,
        "rifle_id": session.rifle_id,
        "rifle_name": session.rifle_name,
        "barrel_configuration_id": session.barrel_configuration_id,
        "barrel_name": session.barrel_name,
        "test_date": session.test_date or date.today().isoformat(),
        "distance_m": session.distance_m,
        "temp_c": session.temp_c,
        "wind_mps": session.wind_mps,
        "wind_dir_deg": session.wind_dir_deg,
        "barometric_pressure_hpa": session.barometric_pressure_hpa,
        "barrel_state": session.barrel_state,
        "shots_in_prior_string": session.shots_in_prior_string,
        "group_size_mm": session.group_size_mm,
        "poi_x_mm": session.poi_x_mm,
        "poi_y_mm": session.poi_y_mm,
        "image_path": session.image_path,
        "notes": session.notes,
    }
    if session.id:
        db.update("ammo_test_sessions", data, "id = ?", (session.id,))
        return session.id
    else:
        db.insert("ammo_test_sessions", data)
        rows = db.execute_query("SELECT last_insert_rowid() AS id")
        return int(rows[0]["id"]) if rows else -1


def delete_session(db: Any, session_id: int) -> None:
    db.delete("ammo_test_shots", "session_id = ?", (session_id,))
    db.delete("ammo_test_sessions", "id = ?", (session_id,))


def get_sessions_for_lot(db: Any, lot_id: int) -> list[AmmoTestSession]:
    rows = db.execute_query(
        "SELECT * FROM ammo_test_sessions WHERE lot_id = ? ORDER BY test_date DESC",
        (lot_id,),
    )
    sessions = [AmmoTestSession.from_row(_db_row(r)) for r in rows]
    for s in sessions:
        _enrich_session_stats(db, s)
    return sessions


def get_all_sessions(db: Any) -> list[AmmoTestSession]:
    rows = db.execute_query("SELECT * FROM ammo_test_sessions ORDER BY test_date DESC")
    sessions = [AmmoTestSession.from_row(_db_row(r)) for r in rows]
    for s in sessions:
        _enrich_session_stats(db, s)
    return sessions


def _enrich_session_stats(db: Any, session: AmmoTestSession) -> None:
    if session.id is None:
        return
    shots = get_shots_for_session(db, session.id)
    vels = [
        s.velocity_fps
        for s in shots
        if s.velocity_fps and not s.is_dud and not s.is_calibration
    ]
    session.shot_count = len(shots)
    session.dud_count = sum(1 for s in shots if s.is_dud)
    session.light_strike_count = sum(1 for s in shots if s.is_light_strike)
    session.ftf_count = sum(1 for s in shots if s.is_ftf)
    session.fte_count = sum(1 for s in shots if s.is_fte)
    if vels:
        session.avg_vel_fps = round(sum(vels) / len(vels), 1)
        session.es_fps = round(max(vels) - min(vels), 1)
        session.sd_fps = round(statistics.pstdev(vels), 1) if len(vels) > 1 else 0.0


# ---------------------------------------------------------------------------
# Shot CRUD
# ---------------------------------------------------------------------------


def save_shots(db: Any, session_id: int, shots: list[AmmoTestShot]) -> None:
    db.delete("ammo_test_shots", "session_id = ?", (session_id,))
    for shot in shots:
        db.insert(
            "ammo_test_shots",
            {
                "session_id": session_id,
                "shot_number": shot.shot_number,
                "velocity_fps": shot.velocity_fps,
                "is_cold_bore": int(shot.is_cold_bore),
                "is_calibration": int(shot.is_calibration),
                "is_dud": int(shot.is_dud),
                "is_light_strike": int(shot.is_light_strike),
                "is_ftf": int(shot.is_ftf),
                "is_fte": int(shot.is_fte),
                "notes": shot.notes,
            },
        )


def get_shots_for_session(db: Any, session_id: int) -> list[AmmoTestShot]:
    rows = db.execute_query(
        "SELECT * FROM ammo_test_shots WHERE session_id = ? ORDER BY shot_number",
        (session_id,),
    )
    return [AmmoTestShot.from_row(_db_row(r)) for r in rows]


# ---------------------------------------------------------------------------
# Lot comparison
# ---------------------------------------------------------------------------


def build_lot_comparison(db: Any, lot_ids: list[int]) -> LotComparisonResult:
    lots = [get_lot(db, lid) for lid in lot_ids]
    lots = [lot for lot in lots if lot is not None]
    sessions_by_lot: dict[int, list[AmmoTestSession]] = {}
    for lot in lots:
        sessions_by_lot[lot.id] = get_sessions_for_lot(db, lot.id)  # type: ignore[index]
    return LotComparisonResult(lots=lots, sessions_by_lot=sessions_by_lot)


def find_similar_lots(db: Any, brand: str, model: str, caliber: str) -> list[AmmoLot]:
    rows = db.execute_query(
        "SELECT * FROM ammo_lots WHERE brand = ? AND model = ? AND caliber = ? ORDER BY purchase_date DESC",
        (brand, model, caliber),
    )
    return [AmmoLot.from_row(_db_row(r)) for r in rows]


# ---------------------------------------------------------------------------
# Weapon matrix — same lot across multiple rifles
# ---------------------------------------------------------------------------


def build_weapon_matrix(db: Any, lot_id: int) -> list[dict[str, Any]]:
    """Return per-rifle summary for a given lot."""
    sessions = get_sessions_for_lot(db, lot_id)
    by_rifle: dict[str, list[AmmoTestSession]] = {}
    for s in sessions:
        key = s.rifle_name or f"Rifle {s.rifle_id}"
        by_rifle.setdefault(key, []).append(s)

    result = []
    for rifle_name, sess_list in by_rifle.items():
        vels = [s.avg_vel_fps for s in sess_list if s.avg_vel_fps]
        groups = [s.group_size_mm for s in sess_list if s.group_size_mm]
        es_vals = [s.es_fps for s in sess_list if s.es_fps]
        total_shots = sum(s.shot_count for s in sess_list)
        total_fail = sum(
            s.dud_count + s.light_strike_count + s.ftf_count + s.fte_count
            for s in sess_list
        )
        result.append(
            {
                "rifle_name": rifle_name,
                "session_count": len(sess_list),
                "avg_vel_fps": round(sum(vels) / len(vels), 1) if vels else None,
                "avg_es_fps": (
                    round(sum(es_vals) / len(es_vals), 1) if es_vals else None
                ),
                "avg_group_mm": round(sum(groups) / len(groups), 2) if groups else None,
                "reliability_pct": (
                    round(100 * (total_shots - total_fail) / total_shots, 1)
                    if total_shots
                    else None
                ),
                "sessions": sess_list,
            }
        )
    result.sort(key=lambda x: (x["avg_group_mm"] or 9999))
    return result


# ---------------------------------------------------------------------------
# Report data builder
# ---------------------------------------------------------------------------


def build_report_data(db: Any, lot_ids: list[int]) -> dict[str, Any]:
    comparison = build_lot_comparison(db, lot_ids)
    rows = []
    for lot in comparison.lots:
        sessions = comparison.sessions_by_lot.get(lot.id, [])
        rows.append(
            {
                "lot": lot,
                "sessions": sessions,
                "avg_vel": comparison.avg_vel(lot.id),  # type: ignore[arg-type]
                "avg_es": comparison.avg_es(lot.id),  # type: ignore[arg-type]
                "avg_group": comparison.avg_group(lot.id),  # type: ignore[arg-type]
                "reliability": comparison.reliability_pct(lot.id),  # type: ignore[arg-type]
            }
        )
    return {"rows": rows, "lot_count": len(lot_ids)}
