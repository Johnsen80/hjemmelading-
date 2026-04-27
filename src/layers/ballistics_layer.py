"""
Unified Ballistics Engine Layer

This module provides a single entry point for all ballistics calculations (external, internal, advanced) and exposes a clean API for use by the UI, plugins, and other modules.

- External ballistics: drop, drift, velocity, energy, zero shift
- Internal ballistics: pressure, burn completeness, load density
- Advanced: G1/G7 drag, Coriolis, spin drift, trajectory modeling

Implements a facade pattern over the existing ballistics modules.
"""

from ..modules import ballistics_engine
from ..utils import advanced_ballistics, ballistics, internal_ballistics


class BallisticsLayer:
    """
    Facade for all ballistics calculations. Use this class to access all ballistics features.
    """

    def __init__(self):
        self.basic = ballistics.BallisticsCalculator()
        self.advanced = advanced_ballistics.AdvancedBallisticsEngine()
        self.internal = internal_ballistics
        self.engine = ballistics_engine.BallisticsEngine()

    # External Ballistics
    def calculate_drop(self, *args, **kwargs):
        return self.basic.calculate_drop(*args, **kwargs)

    def calculate_velocity_at_distance(self, *args, **kwargs):
        return self.basic.calculate_velocity_at_distance(*args, **kwargs)

    def calculate_zero_shift(self, *args, **kwargs):
        return self.basic.calculate_zero_shift(*args, **kwargs)

    def calculate_energy(self, *args, **kwargs):
        return self.basic.calculate_energy(*args, **kwargs)

    def calculate_momentum(self, *args, **kwargs):
        return self.basic.calculate_momentum(*args, **kwargs)

    # Advanced Ballistics
    def calculate_trajectory(self, *args, **kwargs):
        return self.advanced.calculate_trajectory(*args, **kwargs)

    # Internal Ballistics
    def build_internal_ballistics_summary(self, *args, **kwargs):
        return self.internal.build_internal_ballistics_summary(*args, **kwargs)

    def estimate_burn_completeness(self, *args, **kwargs):
        return self.internal.estimate_burn_completeness(*args, **kwargs)

    # Engine/Database
    def calculate_load(self, *args, **kwargs):
        return self.engine.calculate_load(*args, **kwargs)


# Singleton instance for easy import
ballistics_layer = BallisticsLayer()
