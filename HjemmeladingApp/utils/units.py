"""Unit conversion utilities used by the app.

Keep conversions explicit and testable.
"""

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


if __name__ == "__main__":
    # quick sanity checks
    assert abs(km_to_miles(1.0) - 0.62137119) < 1e-9
    assert abs(miles_to_km(0.62137119) - 1.0) < 1e-6
    assert abs(kg_to_lbs(1.0) - 2.2046226218) < 1e-9
    assert abs(celsius_to_fahrenheit(0) - 32) < 1e-9
    print("units OK")
