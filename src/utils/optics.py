"""Optics helper utilities.

Provides conversions between linear offsets, angular units (mrad/moa) and turret clicks.
"""
from math import atan
from typing import Literal, Tuple

Unit = Literal["mil", "moa"]


def linear_offset_to_angle_rad(offset_m: float, range_m: float) -> float:
    """Return angle in radians for a linear offset at given range.

    Uses atan for accuracy; small-angle approximation is acceptable but we use atan.
    """
    if range_m == 0:
        raise ValueError("range_m must be non-zero")
    return atan(offset_m / range_m)


def rad_to_mil(angle_rad: float) -> float:
    """Convert radians to milliradians (mrad).

    1 rad = 1000 mrad
    """
    return angle_rad * 1000.0


def rad_to_moa(angle_rad: float) -> float:
    """Convert radians to minutes of angle (MOA).

    1 MOA = (1/60) degree = pi/(180*60) rad ≈ 0.0002908882086657216 rad
    We convert via mrad for readability.
    """
    mrad = rad_to_mil(angle_rad)
    # 1 MOA ≈ 0.290888 mrad
    return mrad / 0.2908882086657216


def angle_rad_to_unit(angle_rad: float, unit: Unit) -> float:
    if unit == "mil":
        return rad_to_mil(angle_rad)
    return rad_to_moa(angle_rad)


def angle_unit_to_rad(angle: float, unit: Unit) -> float:
    """Convert angle in unit back to radians."""
    if unit == "mil":
        return angle / 1000.0
    # moa -> mrad -> rad
    mrad = angle * 0.2908882086657216
    return mrad / 1000.0


def angle_to_clicks(angle_in_unit: float, click_value: float) -> int:
    """Return nearest integer number of clicks for given angle (in same unit as click_value)."""
    if click_value == 0 or click_value is None:
        raise ValueError("click_value must be non-zero")
    return int(round(angle_in_unit / click_value))


def clicks_to_revs_and_remainder(clicks: int, clicks_per_rev: int) -> Tuple[int, int]:
    if not clicks_per_rev or clicks_per_rev <= 0:
        return (0, abs(clicks))
    rev = clicks // clicks_per_rev
    rem = abs(clicks) % clicks_per_rev
    return (rev, rem)


def compute_clicks_for_offset(
    offset_m: float,
    range_m: float,
    unit: Unit = "mil",
    click_value: float = 0.1,
    clicks_per_rev: int | None = None,
) -> dict:
    """Compute number of turret clicks required to correct an offset.

    Returns a dict with keys:
    - clicks (signed int): positive means raise/right depending on convention
    - angle_unit (float): angle in requested unit
    - revs (int), remainder (int)
    """
    angle_rad = linear_offset_to_angle_rad(offset_m, range_m)
    angle_unit = angle_rad_to_unit(angle_rad, unit)
    clicks = angle_to_clicks(angle_unit, click_value)
    revs, rem = clicks_to_revs_and_remainder(clicks, clicks_per_rev or 0)
    return {
        "clicks": clicks,
        "angle_unit": angle_unit,
        "unit": unit,
        "revolutions": revs,
        "remainder_clicks": rem,
    }
