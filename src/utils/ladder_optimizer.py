"""
Optimize charge using historical ladder test results.

Fits a quadratic model to (charge, group_size_mm) pairs and returns a suggested
charge that minimizes the model within observed bounds.
"""

from typing import Dict, List, Optional


def _solve_3x3(mat: List[List[float]], rhs: List[float]) -> Optional[List[float]]:
    """Solve 3x3 linear system using Gaussian elimination. Returns None on failure."""
    # Make copies
    a = [row[:] for row in mat]
    b = rhs[:]
    n = 3
    # Forward elimination
    for i in range(n):
        # find pivot
        piv = i
        for j in range(i + 1, n):
            if abs(a[j][i]) > abs(a[piv][i]):
                piv = j
        if abs(a[piv][i]) < 1e-12:
            return None
        if piv != i:
            a[i], a[piv] = a[piv], a[i]
            b[i], b[piv] = b[piv], b[i]
        # normalize and eliminate
        for j in range(i + 1, n):
            factor = a[j][i] / a[i][i]
            for k in range(i, n):
                a[j][k] -= factor * a[i][k]
            b[j] -= factor * b[i]
    # Back substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = b[i]
        for j in range(i + 1, n):
            s -= a[i][j] * x[j]
        x[i] = s / a[i][i]
    return x


def fit_quadratic(charges: List[float], groups: List[float]) -> Optional[Dict]:
    """Fit y = a x^2 + b x + c. Returns dict with a,b,c and r2."""
    if len(charges) < 3:
        return None
    n = len(charges)
    s1 = sum(charges)
    s2 = sum(x * x for x in charges)
    s3 = sum(x**3 for x in charges)
    s4 = sum(x**4 for x in charges)
    sy = sum(groups)
    sxy = sum(x * y for x, y in zip(charges, groups))
    sx2y = sum((x * x) * y for x, y in zip(charges, groups))

    mat = [[s4, s3, s2], [s3, s2, s1], [s2, s1, n]]
    rhs = [sx2y, sxy, sy]
    sol = _solve_3x3(mat, rhs)
    if not sol:
        return None
    a, b, c = sol

    # compute R^2
    ymean = sy / n
    ss_tot = sum((y - ymean) ** 2 for y in groups)
    ss_res = 0.0
    for x, y in zip(charges, groups):
        ypred = a * x * x + b * x + c
        ss_res += (y - ypred) ** 2
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {"a": a, "b": b, "c": c, "r2": r2}


def suggest_charge_from_history(
    db,
    rifle_id: Optional[int] = None,
    bullet_id: Optional[int] = None,
    powder_id: Optional[int] = None,
) -> Optional[Dict]:
    """Query historical ladder test results and propose a charge.

    Returns dict with suggested_charge and model info or None if insufficient data.
    """
    cur = db.cursor
    q = "SELECT tr.charge_weight, tr.group_size_mm FROM test_results tr JOIN ladder_tests lt ON tr.ladder_test_id = lt.id WHERE tr.charge_weight IS NOT NULL AND tr.group_size_mm IS NOT NULL"
    params: List = []
    if rifle_id is not None:
        q += " AND lt.rifle_id = ?"
        params.append(rifle_id)
    if bullet_id is not None:
        q += " AND lt.bullet_id = ?"
        params.append(bullet_id)
    if powder_id is not None:
        q += " AND lt.powder_id = ?"
        params.append(powder_id)

    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    if not rows or len(rows) < 3:
        return None

    charges = [float(r[0]) for r in rows]
    groups = [float(r[1]) for r in rows]

    model = fit_quadratic(charges, groups)
    if not model:
        return None

    a = model["a"]
    b = model["b"]
    # vertex at -b/(2a)
    if abs(a) < 1e-12:
        return None
    suggested = -b / (2 * a)

    # clamp to observed range
    min_c, max_c = min(charges), max(charges)
    if suggested < min_c:
        suggested = min_c
    if suggested > max_c:
        suggested = max_c

    return {
        "suggested_charge": suggested,
        "model": model,
        "observed_range": (min_c, max_c),
        "sample_count": len(rows),
    }
