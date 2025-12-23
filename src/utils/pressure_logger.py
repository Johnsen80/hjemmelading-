"""Pressure logging helpers: persist and query predicted pressures."""

from typing import Any, Dict, List, Optional


def log_predicted_pressure(
    db: Any,
    rifle_id: Optional[int] = None,
    ammo_profile_id: Optional[int] = None,
    charge_weight: Optional[float] = None,
    coal_mm: Optional[float] = None,
    cbto_mm: Optional[float] = None,
    predicted_pressure_psi: Optional[float] = None,
    saami_max_psi: Optional[float] = None,
    note: Optional[str] = None,
) -> int:
    """Insert a predicted pressure row into `pressure_history`.

    Returns the inserted row id.
    """
    sql = (
        "INSERT INTO pressure_history (rifle_id, ammo_profile_id, charge_weight, coal_mm, cbto_mm, "
        "predicted_pressure_psi, saami_max_psi, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    params = (
        rifle_id,
        ammo_profile_id,
        charge_weight,
        coal_mm,
        cbto_mm,
        predicted_pressure_psi,
        saami_max_psi,
        note,
    )
    cur = db.cursor
    cur.execute(sql, params)
    db.conn.commit()
    return cur.lastrowid


def query_recent_pressures(db: Any, limit: int = 100) -> List[Dict[str, Any]]:
    """Return recent pressure_history rows ordered by timestamp desc."""
    cur = db.cursor
    cur.execute(
        "SELECT id, timestamp, rifle_id, ammo_profile_id, charge_weight, coal_mm, cbto_mm, "
        "predicted_pressure_psi, saami_max_psi, note FROM pressure_history ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    result: List[Dict[str, Any]] = []
    for r in rows:
        # sqlite3.Row supports mapping access
        result.append({k: r[k] for k in r.keys()})
    return result


def predict_and_log(
    db: Any,
    engine: Any,
    rifle_id: Optional[int],
    ammo_profile_id: Optional[int],
    charge_weight: float,
    coal_mm: Optional[float] = None,
    cbto_mm: Optional[float] = None,
    saami_max_psi: Optional[float] = None,
    note: Optional[str] = None,
    temp_c: Optional[float] = None,
    pressure_kpa: Optional[float] = None,
    humidity_pct: Optional[float] = None,
) -> int:
    """Ask the provided engine to predict pressure (best-effort) and log it.

    The engine is expected to have a method like `predict_peak_pressure` or `predict_pressure`.
    If prediction fails, `predicted_pressure_psi` will be None but the row will still be logged.
    """
    predicted = None
    try:
        # Prefer engine methods that accept env params if available
        if hasattr(engine, "predict_peak_pressure"):
            # if engine supports env args, pass them
            try:
                predicted = engine.predict_peak_pressure(
                    charge_weight,
                    coal_mm=coal_mm,
                    cbto_mm=cbto_mm,
                    temp_c=temp_c,
                    pressure_kpa=pressure_kpa,
                    humidity_pct=humidity_pct,
                )
            except TypeError:
                predicted = engine.predict_peak_pressure(
                    charge_weight, coal_mm=coal_mm, cbto_mm=cbto_mm
                )
        elif hasattr(engine, "predict_pressure"):
            try:
                predicted = engine.predict_pressure(
                    charge_weight,
                    coal_mm=coal_mm,
                    cbto_mm=cbto_mm,
                    temp_c=temp_c,
                    pressure_kpa=pressure_kpa,
                    humidity_pct=humidity_pct,
                )
            except TypeError:
                predicted = engine.predict_pressure(
                    charge_weight, coal_mm=coal_mm, cbto_mm=cbto_mm
                )
        else:
            # Try a generic call signature
            try:
                predicted = engine(
                    charge_weight, coal_mm, cbto_mm, temp_c, pressure_kpa, humidity_pct
                )
            except Exception:
                predicted = engine(charge_weight, coal_mm, cbto_mm)
    except Exception:
        predicted = None

    # If engine returned a velocity instead of pressure, leave it as-is; the
    # caller may choose to store velocity predictions elsewhere. If the engine
    # returned a numeric value that represents pressure, store it. If engine
    # didn't support env params and we have env data, apply a rough air-density
    # scaling to the predicted pressure to account for ambient conditions.
    from src.utils.env_corrections import air_density_ratio

    adjusted = predicted
    try:
        if (
            adjusted is not None
            and temp_c is not None
            and pressure_kpa is not None
            and humidity_pct is not None
        ):
            # apply partial scaling based on air density ratio (conservative)
            ratio = air_density_ratio(temp_c, pressure_kpa, humidity_pct)
            # scale pressure modestly (pressure roughly scales with internal ballistics; keep conservative factor)
            adjusted = float(adjusted) * (1.0 + (ratio - 1.0) * 0.5)
    except Exception:
        pass

    return log_predicted_pressure(
        db,
        rifle_id=rifle_id,
        ammo_profile_id=ammo_profile_id,
        charge_weight=charge_weight,
        coal_mm=coal_mm,
        cbto_mm=cbto_mm,
        predicted_pressure_psi=adjusted,
        saami_max_psi=saami_max_psi,
        note=note,
    )
