"""Simple calibration utilities to fit predicted -> measured mappings.

This module provides a best-effort linear calibration between engine predictions
and observed chronograph measurements. It stores calibration records in
`engine_calibrations` table.
"""

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


def calibrate_engine(db: Any, engine: Any, import_ids: List[int]) -> Dict[str, Any]:
    """Calibrate the engine using provided `chronograph_imports` ids.

    For each import id, the function attempts to find an associated
    `ammo_profiles` row with a stored `powder_charge` (charge weight). It
    then calls the `engine` to predict a velocity for that charge and compares
    to the measured average velocity stored in the import.

    Returns a dict with calibration results and stores a row in
    `engine_calibrations`.
    """
    cur = db.cursor
    preds: List[float] = []
    meas: List[float] = []

    for iid in import_ids:
        cur.execute(
            "SELECT velocities_json, ammo_profile_id, velocity_avg FROM chronograph_imports WHERE id = ?",
            (iid,),
        )
        row = cur.fetchone()
        if not row:
            continue
        # measured average velocity
        try:
            measured = row[2] if row[2] is not None else None
            if measured is None:
                # try to parse velocities_json
                import json

                velocities = json.loads(row[0]) if row[0] else []
                if not velocities:
                    continue
                measured = sum(velocities) / len(velocities)
        except Exception:
            continue

        ap_id = row[1]
        if not ap_id:
            # cannot simulate without an ammo_profile that includes charge
            continue

        cur.execute("SELECT powder_charge FROM ammo_profiles WHERE id = ?", (ap_id,))
        ap = cur.fetchone()
        if not ap:
            continue
        charge = ap[0]
        if charge is None:
            continue

        # Ask engine to predict velocity for this configuration (best-effort)
        predicted_vel = None
        try:
            if hasattr(engine, "predict_velocity"):
                predicted_vel = engine.predict_velocity(charge)
            elif hasattr(engine, "calculate_load"):
                # try to use calculate_load and look for a velocity key
                res = engine.calculate_load(None, None, None, charge, None, None)
                if isinstance(res, dict):
                    predicted_vel = (
                        res.get("velocity")
                        or res.get("velocity_avg")
                        or res.get("predicted_velocity")
                    )
            else:
                # try calling engine as function
                res = engine(charge)
                if isinstance(res, dict):
                    predicted_vel = res.get("velocity")
        except Exception:
            predicted_vel = None

        if predicted_vel is None:
            continue

        try:
            pv = float(predicted_vel)
            mv = float(measured)
        except Exception:
            continue

        preds.append(pv)
        meas.append(mv)

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
                f"calibrated from imports {import_ids}",
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
    }


def get_calibration_samples(
    db: Any, engine: Any, import_ids: List[int]
) -> Dict[str, Any]:
    """Return predicted and measured sample pairs for the given chronograph import ids.

    Returns a dict: {"ok": bool, "preds": [...], "meas": [...], "used": n}
    This does not persist anything; it's a helper for plotting and diagnostics.
    """
    cur = db.cursor
    preds: List[float] = []
    meas: List[float] = []

    for iid in import_ids:
        cur.execute(
            "SELECT velocities_json, ammo_profile_id, velocity_avg FROM chronograph_imports WHERE id = ?",
            (iid,),
        )
        row = cur.fetchone()
        if not row:
            continue

        # measured average velocity
        measured = row[2] if row[2] is not None else None
        if measured is None:
            import json

            velocities = json.loads(row[0]) if row[0] else []
            if not velocities:
                continue
            measured = sum(velocities) / len(velocities)

        ap_id = row[1]
        if not ap_id:
            continue

        cur.execute("SELECT powder_charge FROM ammo_profiles WHERE id = ?", (ap_id,))
        ap = cur.fetchone()
        if not ap:
            continue
        charge = ap[0]
        if charge is None:
            continue

        # predict
        predicted_vel = None
        try:
            if hasattr(engine, "predict_velocity"):
                predicted_vel = engine.predict_velocity(charge)
            elif hasattr(engine, "calculate_load"):
                res = engine.calculate_load(None, None, None, charge, None, None)
                if isinstance(res, dict):
                    predicted_vel = (
                        res.get("velocity")
                        or res.get("velocity_avg")
                        or res.get("predicted_velocity")
                    )
            else:
                res = engine(charge)
                if isinstance(res, dict):
                    predicted_vel = res.get("velocity")
        except Exception:
            predicted_vel = None

        if predicted_vel is None:
            continue

        try:
            pv = float(predicted_vel)
            mv = float(measured)
        except Exception:
            continue

        preds.append(pv)
        meas.append(mv)

    if not preds:
        return {"ok": False, "preds": [], "meas": [], "used": 0}
    return {"ok": True, "preds": preds, "meas": meas, "used": len(preds)}
