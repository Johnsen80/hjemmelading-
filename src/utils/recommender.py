"""
Simple rule-based recommender for load adjustments.

Given basic statistics (avg, es, sd) and current load settings, return human
readable suggestions for next actions. This is intentionally conservative and
meant as an MVP that can later be replaced by ML/optimization.
"""

from typing import Dict, List, Optional


def suggest_adjustments(
    stats: Dict,
    current_charge: float,
    coal_mm: Optional[float] = None,
    cbto_mm: Optional[float] = None,
) -> List[str]:
    """Return a list of suggestion strings.

    stats: dict with keys 'count','avg','es','sd' (may be None)
    current_charge: grains
    """
    suggestions: List[str] = []

    count = stats.get("count") or 0
    avg = stats.get("avg")
    es = stats.get("es")
    sd = stats.get("sd")

    if count < 3:
        suggestions.append(
            "Insufficient shots to form a reliable recommendation (need ≥3)."
        )
        return suggestions

    # Safety / conservative checks
    if sd is None:
        sd = 0.0
    if es is None:
        es = 0.0

    # Rule 1: High ES/SD indicates consistency problem — try small charge adjustments
    if es > 50 or sd > 15:
        suggestions.append(
            "High ES/SD detected — try small charge adjustments (±0.1–0.3 gr) and retest 3 shots each."
        )
        suggestions.append(
            "Also check primers, seating consistency, neck tension and case prep."
        )
    elif es > 30 or sd > 10:
        suggestions.append(
            "Moderate ES/SD — consider tuning charge by ±0.1 gr and test; prefer 3-shot groups."
        )
    else:
        suggestions.append(
            "Low ES/SD — load looks consistent; focus on seating depth tuning for precision."
        )

    # Rule 2: If avg velocity is unusually high/low relative to a typical range, suggest conservative change
    # (We don't have reference data here, so only provide guidance.)
    if avg is not None:
        suggestions.append(f"Observed average velocity: {avg:.1f} fps.")

    # Rule 3: Seating depth suggestions
    if coal_mm is not None and cbto_mm is not None:
        suggestions.append(
            "If groups are vertical/vertical spread increases, try small seating changes (±0.05–0.2 mm) and retest."
        )

    suggestions.append(
        "Always remain under published max pressure and log each change. If in doubt, be conservative."
    )

    # Provide a concrete charge suggestion example
    suggestions.append(
        f"Example: try {current_charge - 0.2:.2f} gr, {current_charge:.2f} gr, and {current_charge + 0.2:.2f} gr with 3-shot groups."
    )

    return suggestions
