"""Unit conversion utilities used by the app.

Keep conversions explicit and testable.
"""

MM_PER_INCH = 25.4
GRAMS_PER_GRAIN = 0.06479891
MPS_PER_FPS = 0.3048
METERS_PER_YARD = 0.9144
BAR_PER_PSI = 0.0689475729


def km_to_miles(km: float) -> float:
    return km * 0.62137119


def miles_to_km(mi: float) -> float:
    return mi / 0.62137119


def kg_to_lbs(kg: float) -> float:
    return kg * 2.2046226218


def lbs_to_kg(lbs: float) -> float:
    return lbs / 2.2046226218


def celsius_to_fahrenheit(c: float) -> float:
    return (c * 9.0 / 5.0) + 32.0


def fahrenheit_to_celsius(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def kwh_to_btu(kwh: float) -> float:
    return kwh * 3412.141633


def btu_to_kwh(btu: float) -> float:
    return btu / 3412.141633


def mm_to_inches(mm: float) -> float:
    return mm / MM_PER_INCH


def inches_to_mm(inches: float) -> float:
    return inches * MM_PER_INCH


def grains_to_grams(grains: float) -> float:
    return grains * GRAMS_PER_GRAIN


def grams_to_grains(grams: float) -> float:
    return grams / GRAMS_PER_GRAIN


def fps_to_mps(fps: float) -> float:
    return fps * MPS_PER_FPS


def mps_to_fps(mps: float) -> float:
    return mps / MPS_PER_FPS


def yards_to_meters(yards: float) -> float:
    return yards * METERS_PER_YARD


def meters_to_yards(meters: float) -> float:
    return meters / METERS_PER_YARD


def psi_to_bar(psi: float) -> float:
    return psi * BAR_PER_PSI


def bar_to_psi(bar: float) -> float:
    return bar / BAR_PER_PSI


if __name__ == "__main__":
    # quick sanity checks
    assert abs(km_to_miles(1.0) - 0.62137119) < 1e-9
    assert abs(miles_to_km(0.62137119) - 1.0) < 1e-6
    assert abs(kg_to_lbs(1.0) - 2.2046226218) < 1e-9
    assert abs(celsius_to_fahrenheit(0) - 32) < 1e-9
    assert abs(inches_to_mm(1.0) - 25.4) < 1e-9
    assert abs(fps_to_mps(1000.0) - 304.8) < 1e-9
    print("units OK")
