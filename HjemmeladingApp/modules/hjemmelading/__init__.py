"""Simple helper functions for the `hjemmelading` module.

This module intentionally provides a small, well-tested surface for unit
conversions and a trivial powder-mass estimator to bootstrap further
development and tests.
"""

from __future__ import annotations

from typing import Optional


def grams_to_grains(g: float) -> float:
    """Convert grams to grains.

    1 gram = 15.4323584 grains
    """
    return float(g) * 15.4323584


def grains_to_grams(gr: float) -> float:
    """Convert grains to grams."""
    return float(gr) / 15.4323584


def powder_mass_from_volume(volume_cm3: float, density_g_per_cm3: float) -> float:
    """Estimate powder mass given a volume (cm^3) and powder density (g/cm^3).

    This is a simple multiplication: mass = volume * density. It is provided
    as a utility to convert measured case volume (ml/cm3) into a mass estimate.
    """
    return float(volume_cm3) * float(density_g_per_cm3)


def powder_mass_from_volume_ml(volume_ml: float, density_g_per_cm3: float) -> float:
    """Helper accepting volume in milliliters (1 ml == 1 cm^3)."""
    return powder_mass_from_volume(float(volume_ml), float(density_g_per_cm3))


def safe_parse_float(value: Optional[object], default: float = 0.0) -> float:
    """Try to parse a value to float; return `default` on failure."""
    try:
        return float(value)
    except Exception as _e:
        return float(default)
