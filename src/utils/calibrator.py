"""Simple calibration utilities to fit predicted -> measured mappings.

This module provides a best-effort linear calibration between engine predictions
and observed chronograph measurements. It stores calibration records in
`engine_calibrations` table.
"""

import json
import math
from typing import Any, Dict, List, Optional, Tuple


def _linear_fit(
    xs: List[float], ys: List[float]
) -> Optional[Tuple[float, float, float]]:
    """Fit y = a*x + b via least squares. Returns (a, b, mse) or None."""
    if not xs or not ys or len(xs) != len(ys) or len(xs) < 2:
        return None
    n = len(xs)
    sx = sum(xs)
    sy = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-12:
        return None
    a = (n * sxy - sx * sy) / denom
    b = (sy - a * sx) / n
    mse = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys)) / n
    return a, b, mse


def _table_exists(cur: Any, table_name: str) -> bool:
    try:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (table_name,),
        )
        return cur.fetchone() is not None
    except Exception:
        return False


def _row_get(row: Any, key: str, index: int | None = None) -> Any:
    try:
        return row[key]
    except Exception:
        if index is None:
            return None
        try:
            return row[index]
        except Exception:
            return None


def _parse_velocities(payload: Any) -> List[float]:
    if payload in (None, ""):
        return []
    data = payload
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except Exception:
            return []
    velocities: List[float] = []
    if isinstance(data, list):
        for item in data:
            value = None
            if isinstance(item, dict):
                value = item.get("velocity_fps")
                if value is None:
                    value = item.get("velocity")
            else:
                value = item
            try:
                velocities.append(float(value))
            except Exception:
                continue
    return velocities


def _extract_measured(row: Any, source_table: str) -> tuple[Optional[float], int]:
    velocities: List[float] = []
    if source_table == "chronograph_sessions":
        measured = _row_get(row, "avg_velocity_fps", 2)
        if measured is None:
            velocities = _parse_velocities(_row_get(row, "raw_data_json", 0))
            measured = sum(velocities) / len(velocities) if velocities else None
        count = _row_get(row, "shot_count")
        if isinstance(count, (int, float)):
            return measured, int(count)
        return measured, len(velocities)

    measured = _row_get(row, "velocity_avg", 2)
    if measured is None:
        velocities = _parse_velocities(_row_get(row, "velocities_json", 0))
        measured = sum(velocities) / len(velocities) if velocities else None
    count = _row_get(row, "velocity_count")
    if isinstance(count, (int, float)):
        return measured, int(count)
    return measured, len(velocities)


def _extract_temperature_c(row: Any, source_table: str) -> Optional[float]:
    if source_table != "chronograph_sessions":
        return None
    temp_f = _row_get(row, "temperature_f")
    try:
        return (float(temp_f) - 32.0) * 5.0 / 9.0 if temp_f is not None else None
    except Exception:
        return None


def _fetch_ammo_profile(cur: Any, ap_id: int) -> Optional[Dict[str, Any]]:
    try:
        cur.execute(
            "SELECT rifle_id, bullet_id, powder_id, powder_charge, coal, cbto FROM ammo_profiles WHERE id = ?",
            (ap_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "rifle_id": _row_get(row, "rifle_id", 0),
            "bullet_id": _row_get(row, "bullet_id", 1),
            "powder_id": _row_get(row, "powder_id", 2),
            "powder_charge": _row_get(row, "powder_charge", 3),
            "coal_mm": _row_get(row, "coal", 4),
            "cbto_mm": _row_get(row, "cbto", 5),
        }
    except Exception:
        try:
            cur.execute(
                "SELECT powder_charge FROM ammo_profiles WHERE id = ?",
                (ap_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {"powder_charge": _row_get(row, "powder_charge", 0)}
        except Exception:
            return None


def _predict_velocity(
    engine: Any, profile: Dict[str, Any], temperature_c: Optional[float]
) -> Optional[float]:
    charge = profile.get("powder_charge")
    if charge is None:
        return None

    predicted = None
    try:
        if hasattr(engine, "predict_velocity"):
            predicted = engine.predict_velocity(charge)
    except Exception:
        predicted = None

    if predicted is None and hasattr(engine, "calculate_load"):
        rifle_id = profile.get("rifle_id")
        bullet_id = profile.get("bullet_id")
        powder_id = profile.get("powder_id")
        if rifle_id and bullet_id and powder_id:
            coal_mm = profile.get("coal_mm")
            coal_value = float(coal_mm) if coal_mm else 0.0
            cbto_mm = profile.get("cbto_mm")
            temp_c = float(temperature_c) if temperature_c is not None else 20.0
            try:
                res = engine.calculate_load(
                    rifle_id,
                    bullet_id,
                    powder_id,
                    float(charge),
                    coal_value,
                    cbto_mm,
                    temp_c,
                )
                if isinstance(res, dict) and not res.get("error"):
                    predicted = (
                        res.get("muzzle_velocity_fps")
                        or res.get("velocity")
                        or res.get("velocity_avg")
                        or res.get("predicted_velocity")
                    )
            except Exception:
                predicted = None

    if predicted is None:
        try:
            res = engine(charge)
            if isinstance(res, dict):
                predicted = res.get("velocity")
        except Exception:
            predicted = None

    try:
        return float(predicted) if predicted is not None else None
    except Exception:
        return None


def _resolve_source_table(cur: Any, source_table: Optional[str]) -> Optional[str]:
    if source_table:
        return source_table
    if _table_exists(cur, "chronograph_sessions"):
        return "chronograph_sessions"
    if _table_exists(cur, "chronograph_imports"):
        return "chronograph_imports"
    return None


def _fetch_source_row(cur: Any, source_table: str, row_id: int) -> Any:
    if source_table == "chronograph_sessions":
        cur.execute(
            "SELECT raw_data_json, ammo_profile_id, avg_velocity_fps, temperature_f, shot_count "
            "FROM chronograph_sessions WHERE id = ?",
            (row_id,),
        )
    else:
        cur.execute(
            "SELECT velocities_json, ammo_profile_id, velocity_avg, velocity_count "
            "FROM chronograph_imports WHERE id = ?",
            (row_id,),
        )
    return cur.fetchone()


def _collect_samples(
    db: Any, engine: Any, record_ids: List[int], source_table: Optional[str]
) -> Dict[str, Any]:
    cur = db.cursor
    source = _resolve_source_table(cur, source_table)
    if not source:
        return {"ok": False, "reason": "no_chronograph_table", "preds": [], "meas": []}

    preds: List[float] = []
    meas: List[float] = []

    for rid in record_ids:
        row = _fetch_source_row(cur, source, rid)
        if not row:
            continue

        measured, _count = _extract_measured(row, source)
        if measured is None:
            continue

        ap_id = _row_get(row, "ammo_profile_id", 1)
        if not ap_id:
            continue

        profile = _fetch_ammo_profile(cur, ap_id)
        if not profile:
            continue

        temp_c = _extract_temperature_c(row, source)
        predicted = _predict_velocity(engine, profile, temp_c)
        if predicted is None:
            continue

        try:
            preds.append(float(predicted))
            meas.append(float(measured))
        except Exception:
            continue

    return {
        "ok": bool(preds),
        "preds": preds,
        "meas": meas,
        "used": len(preds),
        "source_table": source,
    }


def calibrate_engine(
    db: Any,
    engine: Any,
    import_ids: List[int],
    source_table: Optional[str] = None,
) -> Dict[str, Any]:
    """Calibrate the engine using provided chronograph ids.

    For each import id, the function attempts to find an associated
    `ammo_profiles` row with a stored `powder_charge` (charge weight). It
    then calls the `engine` to predict a velocity for that charge and compares
    to the measured average velocity stored in the import.

    Returns a dict with calibration results and stores a row in
    `engine_calibrations`.
    """
    cur = db.cursor
    samples = _collect_samples(db, engine, import_ids, source_table)
    if not samples.get("ok"):
        return {
            "ok": False,
            "reason": samples.get("reason", "insufficient_simulated_data"),
            "used": samples.get("used", 0),
        }

    preds = samples.get("preds", [])
    meas = samples.get("meas", [])

    if len(preds) < 2:
        return {
            "ok": False,
            "reason": "insufficient_simulated_data",
            "used": len(preds),
        }

    fit = _linear_fit(preds, meas)
    if not fit:
        return {"ok": False, "reason": "fit_failed", "used": len(preds)}

    slope, intercept, mse = fit

    # persist calibration
    try:
        engine_name = None
        try:
            engine_name = getattr(engine, "name", None) or engine.__class__.__name__
        except Exception:
            engine_name = None

        cur.execute(
            "INSERT INTO engine_calibrations (engine_name, slope, intercept, sample_count, mse, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (
                engine_name,
                slope,
                intercept,
                len(preds),
                mse,
                f"calibrated from {samples.get('source_table')} {import_ids}",
            ),
        )
        db.conn.commit()
    except Exception:
        # ignore persistence errors but return the fit
        pass

    return {
        "ok": True,
        "slope": slope,
        "intercept": intercept,
        "mse": mse,
        "used": len(preds),
        "source_table": samples.get("source_table"),
    }


def get_calibration_samples(
    db: Any,
    engine: Any,
    import_ids: List[int],
    source_table: Optional[str] = None,
) -> Dict[str, Any]:
    """Return predicted and measured sample pairs for the given chronograph ids.

    Returns a dict: {"ok": bool, "preds": [...], "meas": [...], "used": n}
    This does not persist anything; it's a helper for plotting and diagnostics.
    """
    samples = _collect_samples(db, engine, import_ids, source_table)
    if not samples.get("ok"):
        return {
            "ok": False,
            "preds": [],
            "meas": [],
            "used": samples.get("used", 0),
            "reason": samples.get("reason"),
        }
    return {
        "ok": True,
        "preds": samples.get("preds", []),
        "meas": samples.get("meas", []),
        "used": samples.get("used", 0),
        "source_table": samples.get("source_table"),
    }


def benchmark_engine(
    db: Any,
    engine: Any,
    import_ids: List[int],
    source_table: Optional[str] = None,
    apply_calibration: bool = False,
) -> Dict[str, Any]:
    """Benchmark predicted vs measured velocity errors for selected chronograph ids."""
    samples = _collect_samples(db, engine, import_ids, source_table)
    if not samples.get("ok"):
        return {
            "ok": False,
            "reason": samples.get("reason", "insufficient_simulated_data"),
            "used": samples.get("used", 0),
        }

    preds = samples.get("preds", [])
    meas = samples.get("meas", [])
    if not preds:
        return {
            "ok": False,
            "reason": "insufficient_simulated_data",
            "used": 0,
        }

    if apply_calibration:
        try:
            cur = db.cursor
            cur.execute(
                "SELECT slope, intercept FROM engine_calibrations ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            if row and row[0] is not None:
                slope = float(row[0])
                intercept = float(row[1] or 0.0)
                preds = [slope * p + intercept for p in preds]
        except Exception:
            pass

    errors = [p - m for p, m in zip(preds, meas)]
    mae = sum(abs(e) for e in errors) / len(errors)
    rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
    bias = sum(errors) / len(errors)

    r2 = None
    if len(meas) > 1:
        mean_meas = sum(meas) / len(meas)
        ss_tot = sum((m - mean_meas) ** 2 for m in meas)
        ss_res = sum((m - p) ** 2 for m, p in zip(meas, preds))
        if ss_tot > 0:
            r2 = 1.0 - (ss_res / ss_tot)

    try:
        engine_name = None
        try:
            engine_name = getattr(engine, "name", None) or engine.__class__.__name__
        except Exception:
            engine_name = None
        cur = db.cursor
        cur.execute(
            "INSERT INTO engine_benchmarks (engine_name, sample_count, mae, rmse, bias, r2, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                engine_name,
                len(preds),
                mae,
                rmse,
                bias,
                r2,
                f"benchmarked from {samples.get('source_table')} {import_ids}",
            ),
        )
        db.conn.commit()
    except Exception:
        pass

    return {
        "ok": True,
        "mae": mae,
        "rmse": rmse,
        "bias": bias,
        "r2": r2,
        "used": len(preds),
        "source_table": samples.get("source_table"),
    }
