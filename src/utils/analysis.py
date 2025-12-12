"""Lightweight statistical utilities for QC and load analysis.

This module avoids external dependencies and implements basic
statistics and bootstrap CI useful for measurement sessions and
ladder analysis.

Functions:
- compute_stats(values) -> dict
- detect_outliers(values, method='z', thresh=3.0) -> list of indices
- bootstrap_ci(values, stat='mean', n_iter=2000, ci=95) -> (low, high)

"""
from __future__ import annotations

import math
import random
import statistics
from typing import List, Tuple, Optional


def compute_stats(values: List[float]) -> dict:
    """Compute basic descriptive statistics for a list of numbers.

    Returns a dict with: n, mean, median, sd (sample), var, min, max, iqr,
    ci95_low, ci95_high (bootstrap when n<30 uses bootstrap to be safer).
    """
    vals = [float(v) for v in values if v is not None]
    n = len(vals)
    if n == 0:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "sd": None,
            "var": None,
            "min": None,
            "max": None,
            "iqr": None,
            "ci95": (None, None),
        }

    mean = statistics.mean(vals)
    median = statistics.median(vals)
    var = statistics.pvariance(vals) if n == 1 else statistics.variance(vals)
    sd = math.sqrt(var)
    mn = min(vals)
    mx = max(vals)
    sorted_vals = sorted(vals)
    q1 = sorted_vals[max(0, int(0.25 * n) - 1)]
    q3 = sorted_vals[min(n - 1, int(0.75 * n))]
    iqr = q3 - q1

    # Confidence interval: use t-approx when n>=30, else bootstrap
    if n >= 30:
        se = sd / math.sqrt(n) if n > 0 else None
        # approximate 95% CI using 1.96 (large-sample)
        ci_low = mean - 1.96 * se if se is not None else None
        ci_high = mean + 1.96 * se if se is not None else None
    else:
        ci_low, ci_high = bootstrap_ci(vals, stat="mean", n_iter=2000, ci=95)

    return {
        "n": n,
        "mean": mean,
        "median": median,
        "sd": sd,
        "var": var,
        "min": mn,
        "max": mx,
        "iqr": iqr,
        "ci95": (ci_low, ci_high),
    }


def detect_outliers(values: List[float], method: str = "z", thresh: float = 3.0) -> List[int]:
    """Return indices of values considered outliers.

    Methods:
    - 'z': z-score using sample mean/std (sensitive to outliers)
    - 'mad': median absolute deviation (robust)
    """
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        return []

    indices = []
    if method == "z":
        mean = statistics.mean(vals)
        sd = statistics.stdev(vals) if n > 1 else 0.0
        if sd == 0:
            return []
        for i, v in enumerate(vals):
            z = (v - mean) / sd
            if abs(z) > thresh:
                indices.append(i)
    elif method == "mad":
        med = statistics.median(vals)
        abs_dev = [abs(v - med) for v in vals]
        mad = statistics.median(abs_dev)
        if mad == 0:
            return []
        # scale factor to make MAD comparable to std dev for normal dist
        scale = 1.4826
        for i, v in enumerate(vals):
            z = (v - med) / (mad * scale)
            if abs(z) > thresh:
                indices.append(i)
    else:
        raise ValueError("Unknown method for outlier detection: %s" % method)

    return indices


def bootstrap_ci(values: List[float], stat: str = "mean", n_iter: int = 2000, ci: float = 95) -> Tuple[Optional[float], Optional[float]]:
    """Compute percentile bootstrap CI for a statistic ('mean' or 'median').

    Returns (low, high) as floats. For empty values returns (None,None).
    """
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        return (None, None)

    stats = []
    for _ in range(n_iter):
        sample = [random.choice(vals) for __ in range(n)]
        if stat == "mean":
            stats.append(statistics.mean(sample))
        elif stat == "median":
            stats.append(statistics.median(sample))
        else:
            raise ValueError("Unsupported stat for bootstrap: %s" % stat)

    lower_pct = (100.0 - ci) / 2.0
    upper_pct = 100.0 - lower_pct
    stats_sorted = sorted(stats)
    lo = stats_sorted[int(math.floor((lower_pct / 100.0) * len(stats_sorted)))]
    hi = stats_sorted[int(math.ceil((upper_pct / 100.0) * len(stats_sorted))) - 1]
    return (lo, hi)


if __name__ == "__main__":
    # simple demo
    sample = [random.gauss(100.0, 2.5) for _ in range(12)]
    sample += [115.0]  # an outlier
    print('sample:', sample)
    print('stats:', compute_stats(sample))
    print('outliers (z):', detect_outliers(sample, method='z', thresh=3.0))
    print('outliers (mad):', detect_outliers(sample, method='mad', thresh=3.5))
    print('bootstrap mean CI:', bootstrap_ci(sample, stat='mean', n_iter=2000))
