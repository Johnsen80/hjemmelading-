"""Gaussian Process based optimizer POC with graceful fallback.

Provides `suggest_next_charge(charges, velocities, bounds)` which returns a
recommended next charge to test. If `scikit-learn` is available a GP model is
used to estimate expected improvement; otherwise a simple heuristic is used.
"""

from typing import List, Tuple


def _heuristic_suggest(
    charges: List[float], velocities: List[float], bounds: Tuple[float, float]
) -> float:
    """Simple fallback: pick charge near the best observed velocity +/- 0.5gr.

    Ensures suggestion stays within bounds.
    """
    if not charges:
        # start near middle
        return (bounds[0] + bounds[1]) / 2.0
    # find index of max velocity (best performance)
    try:
        best_idx = max(range(len(velocities)), key=lambda i: velocities[i])
        base = float(charges[best_idx])
    except Exception:
        base = float(charges[-1])

    # If velocities show an increasing trend, prefer stepping up (+0.5).
    try:
        increasing = False
        if len(velocities) >= 2:
            # simple trend: last velocity greater than first
            increasing = velocities[-1] > velocities[0]
    except Exception:
        increasing = False

    if increasing:
        candidates = [base + 0.5, base - 0.5]
    else:
        # default: prefer smaller charge to stay conservative
        candidates = [base - 0.5, base + 0.5]
    for c in candidates:
        if bounds[0] <= c <= bounds[1]:
            return round(c, 3)
    # clamp
    return round(max(bounds[0], min(bounds[1], base)), 3)


def suggest_next_charge(
    charges: List[float], velocities: List[float], bounds: Tuple[float, float]
) -> float:
    """Suggest next charge to test.

    Args:
        charges: observed charge weights (grains)
        velocities: observed velocities (fps)
        bounds: (min_charge, max_charge)

    Returns:
        suggested charge (float)
    """
    # Try to use scikit-learn GaussianProcess if installed
    try:
        import numpy as np
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import ConstantKernel as C
        from sklearn.gaussian_process.kernels import Matern, WhiteKernel

        if len(charges) >= 2:
            X = np.array(charges).reshape(-1, 1)
            y = np.array(velocities)
            kernel = C(1.0, (1e-3, 1e3)) * Matern(
                length_scale=1.0, nu=2.5
            ) + WhiteKernel(noise_level=1)
            gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True)
            gp.fit(X, y)

            # Evaluate EI on a grid
            grid = np.linspace(bounds[0], bounds[1], 50).reshape(-1, 1)
            mu, sigma = gp.predict(grid, return_std=True)
            mu = mu.ravel()
            sigma = sigma.ravel()
            best_y = max(y)
            # Expected Improvement
            from scipy.stats import norm

            with np.errstate(divide="warn"):
                Z = (mu - best_y) / (sigma + 1e-12)
                ei = (mu - best_y) * norm.cdf(Z) + sigma * norm.pdf(Z)
            idx = int(np.nanargmax(ei))
            return float(round(float(grid[idx][0]), 3))
    except Exception:
        # fallback
        return _heuristic_suggest(charges, velocities, bounds)

    # If GP path didn't return, fallback
    return _heuristic_suggest(charges, velocities, bounds)
