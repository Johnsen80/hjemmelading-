"""
Felles miljø- og atmosfærehjelpere for ballistikk.

Dette laget skal være den felles sannheten for temperatur, trykk, luftfuktighet,
høyde, lufttetthet og density altitude på tvers av moduler.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BallisticEnvironment:
    """Felles miljømodell i SI-enheter."""

    temperature_c: float = 15.0
    pressure_hpa: float = 1013.25
    humidity_percent: float = 50.0
    altitude_m: float = 0.0
    wind_speed_mps: float = 0.0
    wind_dir_deg: float = 0.0
    pressure_source: str = "assumed"
    humidity_source: str = "assumed"
    temperature_source: str = "assumed"
    altitude_source: str = "assumed"

    # ISA constants
    _SEA_LEVEL_TEMP_K = 288.15
    _SEA_LEVEL_PRESSURE_PA = 101325.0
    _SEA_LEVEL_DENSITY = 1.225
    _TEMP_LAPSE_K_PER_M = 0.0065
    _GAS_CONSTANT_DRY_AIR = 287.05
    _GAS_CONSTANT_WATER_VAPOR = 461.495
    _GRAVITY = 9.80665

    @property
    def temperature_k(self) -> float:
        return self.temperature_c + 273.15

    @property
    def pressure_pa(self) -> float:
        return self.pressure_hpa * 100.0

    @property
    def relative_humidity(self) -> float:
        humidity = float(self.humidity_percent) / 100.0
        return min(max(humidity, 0.0), 1.0)

    def saturation_vapor_pressure_pa(self) -> float:
        """
        Tetens-ligningen gir et praktisk damptrykkestimat for vanlige skyteforhold.
        """
        return 610.94 * math.exp(
            (17.625 * self.temperature_c) / (self.temperature_c + 243.04)
        )

    def air_density_kg_m3(self) -> float:
        """
        Fuktig lufttetthet som sum av tørrluft og vanndamp.
        """
        vapor_pressure = self.saturation_vapor_pressure_pa() * self.relative_humidity
        dry_air_pressure = max(self.pressure_pa - vapor_pressure, 0.0)
        temperature_k = max(self.temperature_k, 1.0)
        return dry_air_pressure / (
            self._GAS_CONSTANT_DRY_AIR * temperature_k
        ) + vapor_pressure / (self._GAS_CONSTANT_WATER_VAPOR * temperature_k)

    def density_ratio(self) -> float:
        return self.air_density_kg_m3() / self._SEA_LEVEL_DENSITY

    def pressure_altitude_m(self) -> float:
        """
        Enkel trykkhøyde fra lokaltrykk relativt til ISA.
        """
        pressure_ratio = max(self.pressure_pa / self._SEA_LEVEL_PRESSURE_PA, 1e-9)
        exponent = 1.0 / 5.25588
        return 44330.77 * (1.0 - pressure_ratio**exponent)

    def density_altitude_m(self) -> float:
        """
        Inverterer ISA-tetthet til høyde i troposfæren.
        """
        density_ratio = max(self.density_ratio(), 1e-9)
        exponent = 1.0 / 4.255876
        return (self._SEA_LEVEL_TEMP_K / self._TEMP_LAPSE_K_PER_M) * (
            1.0 - density_ratio**exponent
        )

    def density_altitude_ft(self) -> float:
        return self.density_altitude_m() * 3.28084

    def summary(self) -> dict[str, float | str]:
        return {
            "temperature_c": self.temperature_c,
            "pressure_hpa": self.pressure_hpa,
            "humidity_percent": self.humidity_percent,
            "altitude_m": self.altitude_m,
            "density_ratio": self.density_ratio(),
            "density_altitude_m": self.density_altitude_m(),
            "density_altitude_ft": self.density_altitude_ft(),
            "temperature_source": self.temperature_source,
            "pressure_source": self.pressure_source,
            "humidity_source": self.humidity_source,
            "altitude_source": self.altitude_source,
        }
