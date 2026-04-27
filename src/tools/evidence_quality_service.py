"""Canonical evidence quality constants and helpers.

This module is the single source of truth for:
- Evidence score thresholds (score → level mapping)
- Spread signal hint names
- Score-to-level conversion

All other modules (batch_analyzer, smart_ammo_engine, load_session_runtime_service,
digital_twin) must import from here instead of redefining their own thresholds.

DO NOT add heavy logic here. Computation lives in batch_analyzer.py.
This module only owns the constants and the thin conversion function.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Canonical score → level thresholds
# These define what "strong", "moderate", "thin", and "very_thin" mean.
# Changing them here changes the meaning everywhere.
# ---------------------------------------------------------------------------

EVIDENCE_SCORE_THRESHOLDS: dict[str, float] = {
    "strong": 75.0,
    "moderate": 50.0,
    "thin": 25.0,
    # Below thin → "very_thin"
}

# Ordered from weakest to strongest — use for cap/floor operations.
EVIDENCE_LEVEL_ORDER: list[str] = ["very_thin", "thin", "moderate", "strong"]

# ---------------------------------------------------------------------------
# Canonical spread signal hint names
# Must stay in sync with batch_analyzer._spread_learning_signal().
# ---------------------------------------------------------------------------

SPREAD_SIGNAL_HINTS: list[str] = [
    "pressure_or_ammo",
    "ammo_or_process_signal",
    "possible_shooter_or_setup_signal",
    "setup_drift_watch",
    "environment_or_condition_signal",
    "node_or_barrel_timing_signal",
    "poi_shift_watch",
    "target_only",
    "velocity_only",
    "mixed_but_stable",
    "insufficient_evidence",
]

# Hints that block optimization (safety > precision).
BLOCKING_SIGNAL_HINTS: frozenset[str] = frozenset(
    ["pressure_or_ammo", "insufficient_evidence"]
)

# Hints that require process/setup work before optimization.
CONTROL_REQUIRED_SIGNAL_HINTS: frozenset[str] = frozenset(
    [
        "ammo_or_process_signal",
        "setup_drift_watch",
        "environment_or_condition_signal",
    ]
)


# ---------------------------------------------------------------------------
# score_to_level — canonical score → level conversion
# ---------------------------------------------------------------------------


def score_to_level(score: float | None) -> str:
    """Convert a numeric evidence quality score to a canonical level string.

    Args:
        score: Evidence quality score in [0, 100], or None if unknown.

    Returns:
        "strong" | "moderate" | "thin" | "very_thin" | "unknown"
    """
    if score is None:
        return "unknown"
    if score >= EVIDENCE_SCORE_THRESHOLDS["strong"]:
        return "strong"
    if score >= EVIDENCE_SCORE_THRESHOLDS["moderate"]:
        return "moderate"
    if score >= EVIDENCE_SCORE_THRESHOLDS["thin"]:
        return "thin"
    return "very_thin"


def cap_evidence_level(level: str, ceiling: str) -> str:
    """Cap an evidence level at a ceiling value.

    Example: cap_evidence_level("strong", "moderate") → "moderate"

    Args:
        level:   The current evidence level string.
        ceiling: The maximum allowed level string.

    Returns:
        The capped level string. Returns the ceiling if level is unknown.
    """
    if level not in EVIDENCE_LEVEL_ORDER:
        return ceiling if ceiling in EVIDENCE_LEVEL_ORDER else "very_thin"
    if ceiling not in EVIDENCE_LEVEL_ORDER:
        return level
    return EVIDENCE_LEVEL_ORDER[
        min(
            EVIDENCE_LEVEL_ORDER.index(level),
            EVIDENCE_LEVEL_ORDER.index(ceiling),
        )
    ]


def is_blocking_hint(hint: str) -> bool:
    """Return True if the spread signal hint blocks optimization."""
    return hint in BLOCKING_SIGNAL_HINTS


def is_control_required_hint(hint: str) -> bool:
    """Return True if the hint requires process/setup control before optimization."""
    return hint in CONTROL_REQUIRED_SIGNAL_HINTS


# ---------------------------------------------------------------------------
# Confidence level thresholds for workflow and builder modules.
# These use raw accumulated delta scores — NOT the 0-100 evidence scale above.
# ---------------------------------------------------------------------------

WORKFLOW_CONFIDENCE_THRESHOLDS: dict[str, float] = {"high": 4.5, "medium": 2.5}
BUILDER_CONFIDENCE_THRESHOLDS: dict[str, float] = {"high": 6.0, "medium": 4.0}


def score_to_confidence_level(
    score: float | None,
    thresholds: dict[str, float] | None = None,
) -> str:
    """Convert a raw accumulated delta score to "high" | "medium" | "low".

    Used by build_workflow_evidence_quality() and summarize_builder_confidence_model()
    to keep the level-assignment logic in one place.

    Args:
        score:      Accumulated delta score (small float, not 0-100).
        thresholds: Dict with "high" and "medium" keys.  Defaults to
                    WORKFLOW_CONFIDENCE_THRESHOLDS.

    Returns:
        "high" | "medium" | "low"
    """
    if thresholds is None:
        thresholds = WORKFLOW_CONFIDENCE_THRESHOLDS
    s = float(score or 0.0)
    if s >= thresholds.get("high", 4.5):
        return "high"
    if s >= thresholds.get("medium", 2.5):
        return "medium"
    return "low"
