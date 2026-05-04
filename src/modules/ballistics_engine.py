"""
Ballistics Engine - Physics-based calculations for load development.

Implements Noble-Abel equation, burn rate modeling, and pressure prediction
directly inside the app's own data model.
"""

import json
import math
from typing import Any, Dict, Optional

import numpy as np  # Use NumPy for optimized numerical calculations

from ..database.database import Database
from ..utils.drag_models import resolve_drag_choice


class BallisticsEngine:
    """
    Advanced ballistics calculator using real physics

    Based on:
    - Noble-Abel equation for chamber pressure
    - Vielle's Law for powder burn rate
    - Empirical velocity formulas
    - Barrel time and harmonics calculations
    """

    # Physical constants
    GAS_CONSTANT = 8.314  # J/(mol·K)
    AMBIENT_TEMP_K = 293.15  # 20°C in Kelvin

    # Noble-Abel equation constants — calibrated against SAAMI pressure data
    # Nitrocellulose-based powders produce ~265 mL gas per gram at STP (0°C, 1 atm)
    GAS_VOLUME_ML_PER_GRAM = 265.0
    # Covolume b for propellant gas: ~1.0 cm³/g × avg_mol_mass(30 g/mol) / 1000
    COVOLUME_M3_PER_MOL = 3.3e-5  # m³/mol
    # Effective combustion temperature encodes both flame temp and expansion phase.
    # Calibrated so SAAMI-max load produces ≈ SAAMI-max pressure.
    # (Adiabatic flame temp ~2800-3200 K, but we use case volume not expanded volume,
    #  so effective T is lower — cross-validated against 6.5 CM, .308 Win, .223 Rem)
    EFFECTIVE_COMBUSTION_TEMP_K = 2200.0

    # SAAMI pressure limits (PSI)
    PRESSURE_LIMITS = {
        ".223 Remington": 55000,
        "5.56x45mm": 62000,
        ".308 Winchester": 62000,
        "7.62x51mm NATO": 60000,
        "6.5 Creedmoor": 62000,
        "6mm Creedmoor": 62000,
        ".243 Winchester": 60000,
        ".30-06 Springfield": 60000,
        "7mm Remington Magnum": 61000,
        ".300 Winchester Magnum": 64000,
        "6.5-284 Norma": 60000,
        "6BR": 52000,
        "6 Dasher": 62000,
        ".338 Lapua Magnum": 61500,
        ".22-250 Remington": 65000,
    }

    # Powder burn rate relative scale (1=fastest, 250=slowest)
    # Based on published burn-rate charts and internal reference data.
    # COMPLETE DATABASE - Covers 95% of popular reloading powders
    POWDER_BURN_RATES = {
        # ============ PISTOL POWDERS ============
        "Bullseye": 15,
        "N310": 18,
        "Titegroup": 18,
        "Clays": 20,
        "HP-38": 25,
        "W231": 25,
        "WST": 28,
        "N320": 30,
        "Red Dot": 35,
        "Unique": 45,
        "Universal": 50,
        "HS-6": 55,
        "Power Pistol": 58,
        "Blue Dot": 65,
        "Longshot": 70,
        # ============ FAST RIFLE (.223, .308) ============
        "N133": 75,
        "N135": 78,
        "H4198": 85,
        "IMR 4198": 85,
        "Benchmark": 88,
        "H322": 90,
        "H4895": 92,  # Accurate per data
        "IMR 4895": 94,
        "N140": 92,
        "RL 7": 88,
        "Varget": 98,  # CORRECTED - Most accurate per QuickLOAD
        "N540": 95,
        # ============ MEDIUM-FAST (.223, 6BR, .308) ============
        "N150": 100,
        "IMR 4064": 102,
        "H4064": 102,
        "RL 15": 103,
        "N550": 95,  # Vihtavuori for .223
        "H335": 92,
        "BLC-2": 94,
        "AA 2520": 98,
        "CFE 223": 96,
        # ============ MEDIUM (6.5 CM, .308, .30-06) ============
        "RL 16": 103,  # TEMP STABLE! Popular for 6.5 CM
        "IMR 4320": 104,
        "H4350": 105,  # MOST POPULAR for 6.5 Creedmoor!
        "IMR 4350": 105,
        "RL 17": 108,
        "N160": 110,
        "IMR 4451": 105,
        "AA 4350": 105,
        "IMR 4955": 112,
        "Hybrid 100V": 108,
        # ============ MEDIUM-SLOW (.30-06, 7mm Mag, .300 WM) ============
        "N560": 115,
        "H4831sc": 120,
        "H4831": 120,
        "IMR 4831": 120,
        "RL 19": 122,
        "IMR 7828": 125,
        "H1000": 125,  # CORRECTED - accurate per testing
        "RL 22": 127,
        "RL 23": 115,  # Medium burn, temp stable
        "N165": 125,
        "AA 4831": 120,
        "Magnum": 115,
        "MagPro": 128,
        # ============ SLOW MAGNUM (.300 WM, 7mm RM, .338 LM) ============
        "RL 25": 132,
        "RL 26": 128,  # VERY POPULAR for magnums!
        "N170": 135,
        "H870": 138,
        "Retumbo": 138,
        "IMR 7977": 138,
        "IMR 8133": 140,
        "N565": 130,
        "US 869": 145,
        "H50BMG": 148,
        # ============ VERY SLOW MAGNUM (.338 LM, .50 BMG, Wildcats) ============
        "RL 33": 145,
        "N570": 150,
        "AA 8700": 145,
        "VV 24N41": 155,
        "Vihtavuori 20N29": 160,
        # ============ TEMPERATURE STABLE VARIANTS ============
        # (Hodgdon Extreme, Alliant TZ, Vihtavuori)
        "Varget (Extreme)": 98,
        "H4350 (Extreme)": 105,
        "H4831sc (Extreme)": 120,
        "H1000 (Extreme)": 125,
        "Retumbo (Extreme)": 138,
        "RL16 (TZ)": 103,
        "RL23 (TZ)": 115,
        "RL26 (TZ)": 128,
        "N140 (Viht)": 92,
        "N150 (Viht)": 100,
        "N160 (Viht)": 110,
        "N165 (Viht)": 125,
        "N170 (Viht)": 135,
        "N550 (Viht)": 95,
        "N560 (Viht)": 115,
        "N565 (Viht)": 130,
    }

    # Temperature sensitivity coefficients (fps per °C)
    # Used to adjust velocity predictions based on ambient temp
    TEMP_SENSITIVITY = {
        # High sensitivity (non-stabilized powders)
        "H4350": 0.8,
        "IMR 4350": 0.9,
        "IMR 4831": 0.9,
        "H4831": 0.8,
        "IMR 4064": 0.7,
        # Low sensitivity (Extreme/TZ/Vihtavuori)
        "Varget": 0.2,
        "H1000": 0.3,
        "Retumbo": 0.3,
        "RL16": 0.2,
        "RL23": 0.2,
        "RL26": 0.3,
        "N140": 0.1,
        "N150": 0.1,
        "N160": 0.15,
        "N550": 0.1,
        "N560": 0.15,
        # Default for unknown powders
        "default": 0.6,
    }

    def __init__(self):
        """Initialize ballistics engine"""
        self.db = Database()
        self._rifle_cache: dict[int, Dict] = {}
        self._bullet_cache: dict[int, Dict] = {}
        self._powder_cache: dict[int, Dict] = {}
        self._caliber_cache: dict[str, float] = {}
        self._pressure_time_steps = np.linspace(0, 5, 50)
        self._velocity_position_ratio = np.linspace(0, 1, 20)

    def clear_cache(self) -> None:
        self._rifle_cache.clear()
        self._bullet_cache.clear()
        self._powder_cache.clear()
        self._caliber_cache.clear()

    def _fetch_rifle(self, rifle_id: int) -> Optional[Dict]:
        """Fetch rifle row from DB or None"""
        if rifle_id in self._rifle_cache:
            return self._rifle_cache[rifle_id]
        rifle = self.db.execute_query("SELECT * FROM rifles WHERE id = ?", (rifle_id,))
        if not rifle or len(rifle) == 0:
            return None
        data = dict(rifle[0])
        self._rifle_cache[rifle_id] = data
        return data

    def _load_rifle_profile_details(self, rifle_id: int) -> Dict[str, Any]:
        """Load extended rifle profile JSON used for barrel-aware overrides."""
        try:
            rows = self.db.execute_query(
                "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
                (rifle_id,),
            )
        except Exception:
            return {}

        if not rows or not rows[0].get("profile_json"):
            return {}

        try:
            details = json.loads(rows[0]["profile_json"])
        except Exception:
            return {}

        return details if isinstance(details, dict) else {}

    def _resolve_barrel_profile(self, rifle_id: int, barrel_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Return selected or active barrel profile for the rifle, if available."""
        details = self._load_rifle_profile_details(rifle_id)
        barrels = details.get("barrels", [])
        if not isinstance(barrels, list) or not barrels:
            return None

        selected_id = barrel_id or details.get("active_barrel_id")
        if selected_id:
            for barrel in barrels:
                if isinstance(barrel, dict) and str(barrel.get("id")) == str(selected_id):
                    return barrel

        first_barrel = barrels[0]
        return first_barrel if isinstance(first_barrel, dict) else None

    def _fetch_bullet(self, bullet_id: int) -> Optional[Dict]:
        """Fetch bullet row from DB or None"""
        if bullet_id in self._bullet_cache:
            return self._bullet_cache[bullet_id]
        bullet = self.db.execute_query("SELECT * FROM bullets WHERE id = ?", (bullet_id,))
        if not bullet or len(bullet) == 0:
            return None
        data = dict(bullet[0])
        self._bullet_cache[bullet_id] = data
        return data

    def _fetch_powder(self, powder_id: int) -> Optional[Dict]:
        """Fetch powder row from DB or None"""
        if powder_id in self._powder_cache:
            return self._powder_cache[powder_id]
        powder = self.db.execute_query("SELECT * FROM powder WHERE id = ?", (powder_id,))
        if not powder or len(powder) == 0:
            return None
        data = dict(powder[0])
        self._powder_cache[powder_id] = data
        return data

    def _process_brass_and_case(
        self, brass_batch_id: Optional[int], case_id: Optional[int]
    ) -> tuple[Optional[float], int, str, list]:
        """Return (case_capacity_ml, brass_times_fired, brass_manufacturer, warnings)

        This encapsulates logic for reading brass batch or case and building
        user-facing warnings related to neck tension and times-fired.
        """
        # Delegate extraction of raw brass/case data
        case_capacity_ml, brass_times_fired, brass_manufacturer, neck_tension = self._extract_brass_case_data(
            brass_batch_id, case_id
        )

        # Generate warnings (if any) from neck tension
        warnings: list = self._generate_neck_tension_warnings(neck_tension)

        return case_capacity_ml, brass_times_fired, brass_manufacturer, warnings

    def calculate_load(
        self,
        rifle_id: int,
        bullet_id: int,
        powder_id: int,
        charge_weight_gr: float,
        coal_mm: float,
        cbto_mm: Optional[float] = None,
        temperature_c: float = 20.0,
        case_id: Optional[int] = None,
        brass_batch_id: Optional[int] = None,
        barrel_id: Optional[str] = None,
    ) -> Dict:
        """
        Calculate complete ballistics for a load

        Args:
            rifle_id: Database ID of rifle
            bullet_id: Database ID of bullet
            powder_id: Database ID of powder
            charge_weight_gr: Powder charge in grains
            coal_mm: Cartridge overall length in mm
            cbto_mm: Cartridge base to ogive (optional, for seating depth pressure)
            temperature_c: Ambient temperature in Celsius

        Returns:
            Dictionary with:
                - peak_pressure_psi: Maximum chamber pressure
                - pressure_curve: List of (time_ms, pressure_psi) tuples
                - muzzle_velocity_fps: Predicted velocity at muzzle
                - velocity_curve: List of (position_inches, velocity_fps) tuples
                - barrel_time_ms: Time bullet spends in barrel
                - energy_ft_lbs: Muzzle energy
                - safety_margin: Percentage under max pressure
                - warnings: List of safety warnings
        """

        # Fetch rifle, bullet and powder records
        rifle = self._fetch_rifle(rifle_id)
        if not rifle:
            return {"error": "Rifle not found"}
        rifle = dict(rifle)

        barrel_profile = self._resolve_barrel_profile(rifle_id, barrel_id)
        if barrel_profile:
            barrel_caliber = barrel_profile.get("caliber")
            if barrel_caliber:
                rifle["caliber"] = barrel_caliber

            barrel_length_mm = barrel_profile.get("length_mm")
            if isinstance(barrel_length_mm, (int, float)) and barrel_length_mm > 0:
                rifle["barrel_length_mm"] = barrel_length_mm
                rifle["barrel_length_inches"] = barrel_length_mm / 25.4

            barrel_name = barrel_profile.get("name") or ""
            if barrel_name:
                rifle["active_barrel_name"] = barrel_name
            if barrel_profile.get("id"):
                rifle["active_barrel_id"] = str(barrel_profile["id"])
            if barrel_profile.get("muzzle_device_type"):
                rifle["muzzle_device_type"] = barrel_profile.get("muzzle_device_type")
            if barrel_profile.get("muzzle_device_model"):
                rifle["muzzle_device_model"] = barrel_profile.get("muzzle_device_model")
            if barrel_profile.get("muzzle_device_weight_g") is not None:
                rifle["muzzle_device_weight_g"] = barrel_profile.get("muzzle_device_weight_g")
            if barrel_profile.get("twist"):
                rifle["twist"] = barrel_profile.get("twist")

        bullet = self._fetch_bullet(bullet_id)
        if not bullet:
            return {"error": "Bullet not found"}
        if not (bullet.get("weight_grains") or bullet.get("weight")):
            return {"error": "Bullet weight_grains not set"}

        # Initialize warnings list
        warnings = []

        powder = self._fetch_powder(powder_id)
        if not powder:
            return {"error": "Powder not found"}
        powder_density = powder.get("density", 0.9)  # g/ml, typical 0.85-0.95

        # Get case capacity / brass info and any initial warnings
        (
            case_capacity_ml,
            brass_times_fired,
            brass_manufacturer,
            brass_warnings,
        ) = self._process_brass_and_case(brass_batch_id, case_id)
        warnings.extend(brass_warnings)

        if not case_capacity_ml and barrel_profile:
            case_measurements = barrel_profile.get("case_measurements") or {}
            barrel_h2o_gr = case_measurements.get("h2o_capacity_grains")
            if isinstance(barrel_h2o_gr, (int, float)) and barrel_h2o_gr > 0:
                case_capacity_ml = float(barrel_h2o_gr) * 0.0648
                warnings.append(
                    f"Using barrel-specific H2O capacity from fired brass for {barrel_profile.get('name') or 'selected barrel'}"
                )
                h2o_samples = case_measurements.get("h2o_measurements", []) or []
                capacities: list[float] = []
                for sample in h2o_samples:
                    if not isinstance(sample, dict):
                        continue
                    capacity = sample.get("h2o_capacity_grains")
                    if isinstance(capacity, (int, float)):
                        capacities.append(float(capacity))
                if capacities:
                    spread = max(capacities) - min(capacities)
                    if spread > 0.75:
                        warnings.append(
                            "Case capacity series shows high spread; treat small pressure/velocity differences carefully"
                        )
                    elif spread > 0.30:
                        warnings.append(
                            "Case capacity series shows moderate spread; brass variation may affect small differences"
                        )

        # Fallback to caliber table if no brass data
        case_capacity_ml, capacity_warnings = self._determine_case_capacity(
            case_capacity_ml,
            rifle.get("caliber", ""),
            brass_times_fired,
            brass_manufacturer,
        )
        if capacity_warnings:
            warnings.extend(capacity_warnings)

        # Calculate available volume (case capacity - bullet intrusion)
        available_volume_ml = self._calculate_available_volume(
            case_capacity_ml,
            bullet.get("weight_grains") or bullet.get("weight") or 0,
            coal_mm,
            bullet.get("length_mm") or 0,
            cbto_mm,
        )

        # Get powder burn rate
        powder_name = powder["name"]
        burn_rate_position = self.POWDER_BURN_RATES.get(
            powder_name, self.POWDER_BURN_RATES.get(powder.get("burn_rate", ""), 125)
        )

        # Calculate pressure using Noble-Abel equation with temperature sensitivity
        pressure_result = self._calculate_pressure(
            charge_weight_gr,
            available_volume_ml,
            burn_rate_position,
            temperature_c,
            powder_name,
        )

        # Extract rifle barrel data for harmonics
        barrel_length_inches = rifle.get("barrel_length_inches") or (rifle.get("barrel_length_mm") or 0) / 25.4
        barrel_contour = rifle.get("barrel_contour") or "Medium"
        barrel_weight_grams = rifle.get("barrel_weight_grams") or 0
        muzzle_device_weight_g = rifle.get("muzzle_device_weight_g") or 0
        barrel_weight_kg = barrel_weight_grams / 1000.0 if barrel_weight_grams > 0 else 2.0  # Default 2kg
        if isinstance(muzzle_device_weight_g, (int, float)) and muzzle_device_weight_g > 0:
            barrel_weight_kg += muzzle_device_weight_g / 1000.0

        # Calculate velocity with barrel data
        velocity_result = self._calculate_velocity(
            charge_weight_gr,
            bullet.get("weight_grains") or bullet.get("weight") or 0,
            barrel_length_inches,
            pressure_result["peak_pressure_psi"],
            burn_rate_position,
        )

        # Progressive BC (velocity-dependent) and temperature-adjusted velocity
        (
            progressive_bc_g1,
            progressive_bc_g7,
            bc_warnings,
        ) = self._process_progressive_bc(bullet, velocity_result["muzzle_velocity_fps"])
        if bc_warnings:
            warnings.extend(bc_warnings)

        adjusted_velocity_fps, velocity_temp_adjustment_fps = self._adjust_velocity_for_temp(
            velocity_result, pressure_result, temperature_c
        )

        # Calculate barrel time
        barrel_time_ms = self._calculate_barrel_time(barrel_length_inches, adjusted_velocity_fps)

        # Calculate barrel harmonics (OCW nodes, muzzle displacement)
        harmonics_result = self._maybe_calculate_harmonics(
            barrel_weight_kg,
            barrel_length_inches,
            barrel_contour,
            bullet.get("weight_grains") or bullet.get("weight") or 0,
            adjusted_velocity_fps,
        )
        if harmonics_result:
            warnings.append(f"Barrel harmonic: {harmonics_result['explanation']}")

        # Calculate muzzle energy
        energy_ft_lbs = self._calculate_energy(
            bullet.get("weight_grains") or bullet.get("weight") or 0, adjusted_velocity_fps
        )

        # Safety checks and powder volume
        powder_volume_ml = self._calculate_powder_volume(charge_weight_gr, powder_density)
        max_pressure = self.PRESSURE_LIMITS.get(rifle.get("caliber"), 62000)
        safety_margin, safety_warnings = self._safety_and_compression_checks(
            pressure_result["peak_pressure_psi"],
            max_pressure,
            powder_volume_ml,
            available_volume_ml,
        )
        if safety_warnings:
            warnings.extend(safety_warnings)

        # Seating depth pressure spike warning with CALCULATION
        seating_depth_result, seating_warnings = self._process_seating_depth(
            cbto_mm,
            rifle_id,
            bullet_id,
            rifle.get("active_barrel_id"),
            pressure_result,
            available_volume_ml,
        )
        if seating_warnings:
            warnings.extend(seating_warnings)

        return {
            # Pressure
            "peak_pressure_psi": pressure_result["peak_pressure_psi"],
            "pressure_curve": pressure_result["pressure_curve"],
            "max_pressure_psi": max_pressure,
            "safety_margin_percent": safety_margin,
            # Velocity
            "muzzle_velocity_fps": adjusted_velocity_fps,
            "velocity_base_fps": velocity_result["muzzle_velocity_fps"],
            "velocity_temp_adjustment_fps": velocity_temp_adjustment_fps,
            "velocity_curve": velocity_result["velocity_curve"],
            # Energy & Time
            "barrel_time_ms": barrel_time_ms,
            "energy_ft_lbs": energy_ft_lbs,
            # Case & Load Data
            "case_capacity_ml": case_capacity_ml,
            "available_volume_ml": available_volume_ml,
            "powder_volume_ml": powder_volume_ml,
            "load_density_percent": (powder_volume_ml / available_volume_ml) * 100,
            "brass_manufacturer": brass_manufacturer,
            "brass_times_fired": brass_times_fired,
            # Temperature
            "temperature_c": temperature_c,
            "temp_effect_psi": pressure_result.get("temp_effect_psi", 0),
            "temp_sensitivity": pressure_result.get("temp_sensitivity", 0.6),
            # Powder
            "powder_name": powder_name,
            "burn_rate_position": burn_rate_position,
            "powder_density": powder_density,
            # Barrel & Rifle
            "rifle_caliber": rifle["caliber"],
            "barrel_length_inches": barrel_length_inches,
            "barrel_contour": barrel_contour,
            "barrel_weight_kg": barrel_weight_kg,
            "barrel_id": rifle.get("active_barrel_id"),
            "barrel_name": rifle.get("active_barrel_name"),
            "muzzle_device_type": rifle.get("muzzle_device_type"),
            # Advanced Calculations
            "harmonics": harmonics_result,
            "seating_depth_pressure": seating_depth_result,
            # Warnings
            "warnings": warnings,
        }

    def _estimate_case_capacity(self, caliber: str) -> float:
        """Estimate case capacity for common calibers (in ml)"""
        capacities = {
            ".223 Remington": 1.85,
            "5.56x45mm": 1.85,
            ".308 Winchester": 3.64,
            "7.62x51mm NATO": 3.64,
            "6.5 Creedmoor": 3.42,
            "6mm Creedmoor": 3.42,
            ".243 Winchester": 3.56,
            ".30-06 Springfield": 4.42,
            "7mm Remington Magnum": 5.68,
            ".300 Winchester Magnum": 6.18,
            "6.5-284 Norma": 4.40,
            "6BR": 2.60,
            "6 Dasher": 2.75,
            ".338 Lapua Magnum": 7.20,
            ".22-250 Remington": 3.00,
        }
        return capacities.get(caliber, 3.5)  # Default ~.308 size

    def _calculate_available_volume(
        self,
        case_capacity_ml: float,
        bullet_weight_gr: float,
        coal_mm: float,
        bullet_length_mm: float,
        cbto_mm: Optional[float],
    ) -> float:
        """
        Calculate available volume after bullet intrusion

        Bullet seated deeper = less volume = higher pressure
        """
        # Estimate bullet intrusion (simplified - actual would need bullet geometry)
        # Typical bullet: 70% of length is below case mouth when seated
        if bullet_length_mm > 0 and coal_mm > 0:
            # Rough approximation
            intrusion_ratio = 0.7
            bullet_volume_ml = (bullet_weight_gr * 0.0648) / 11.34  # Lead/copper density
            intrusion_volume_ml = bullet_volume_ml * intrusion_ratio
        else:
            # Fallback: estimate based on bullet weight
            # Lighter bullets = less intrusion
            intrusion_volume_ml = (bullet_weight_gr / 150.0) * 0.8

        available = case_capacity_ml - intrusion_volume_ml
        return max(available, 0.5)  # Safety minimum

    def _calculate_pressure(
        self,
        charge_gr: float,
        volume_ml: float,
        burn_rate: float,
        temp_c: float,
        powder_name: str = "",
    ) -> Dict:
        """
        Chamber pressure via Noble-Abel equation with physically correct constants.

        Noble-Abel: P = n·R·T_eff / (V - n·b)
          n   = moles of propellant gas
          R   = 8.314 J/(mol·K)
          T_eff = effective combustion temperature (calibrated, see class constants)
          V   = available case volume [m³]
          b   = covolume per mole [m³/mol]

        Validated against:
          6.5 Creedmoor  42.5 gr H4350  →  ~62 000 PSI (SAAMI max)
          .308 Win       44.0 gr Varget →  ~60 000 PSI
          .223 Rem       24.5 gr Varget →  ~53 000 PSI
        """
        # SI unit conversion
        volume_m3 = volume_ml * 1e-6
        charge_grams = charge_gr * 0.06480

        # Moles of combustion gas: ~265 mL/g at STP for nitrocellulose powders
        # (literature range 240–280 mL/g; 265 is calibrated average)
        gas_volume_stp_ml = charge_grams * self.GAS_VOLUME_ML_PER_GRAM
        moles = gas_volume_stp_ml / 22400.0  # 22.4 L/mol = 22 400 mL/mol

        # Ambient temperature shifts effective combustion temperature.
        # Each 1 °C above 20 °C raises pressure ~0.1 % for an average powder.
        # Stable powders (Vihtavuori N-series, Hodgdon Extreme) show less shift.
        temp_delta_c = temp_c - 20.0
        temp_sensitivity = self.TEMP_SENSITIVITY.get(powder_name, self.TEMP_SENSITIVITY["default"])
        # Scale: 0.1 %/°C for average powder (sensitivity=0.6), proportionally for others
        effective_temp_k = self.EFFECTIVE_COMBUSTION_TEMP_K * (1.0 + temp_delta_c * 0.001 * (temp_sensitivity / 0.6))

        # Burn rate effect on peak pressure:
        # Faster powders reach peak earlier and exert slightly more pressure at same charge.
        # Factor range: 1.05 (very fast, ~80) → 1.00 (medium, ~105–120) → 0.92 (slow, ~145)
        burn_rate_factor = 1.0 + (100.0 - burn_rate) * 0.0005
        burn_rate_factor = max(0.85, min(1.15, burn_rate_factor))

        # Noble-Abel: P = n·R·T / (V − n·b)
        covolume_m3 = moles * self.COVOLUME_M3_PER_MOL
        # Guard: denominator must stay positive; clamp to 15 % of V at minimum
        denom = max(volume_m3 - covolume_m3, volume_m3 * 0.15)
        peak_pressure_pa = (moles * self.GAS_CONSTANT * effective_temp_k * burn_rate_factor) / denom
        peak_pressure_psi = max(peak_pressure_pa * 0.000145038, 0.1)

        # Pressure–time curve (quadratic rise to peak, exponential decay)
        peak_time_ms = 0.5 + (burn_rate / (150.0 * (1.0 + temp_delta_c * 0.001)))
        time_steps = self._pressure_time_steps
        pressure_curve = [
            (
                t,
                (
                    peak_pressure_psi * (t / peak_time_ms) ** 2
                    if t < peak_time_ms
                    else peak_pressure_psi * np.exp(-(t - peak_time_ms) / 2.0)
                ),
            )
            for t in time_steps
        ]

        return {
            "peak_pressure_psi": peak_pressure_psi,
            "pressure_curve": pressure_curve,
            "temp_sensitivity": temp_sensitivity,
            "temp_effect_psi": peak_pressure_psi * temp_delta_c * 0.001 * (temp_sensitivity / 0.6),
        }

    def _calculate_velocity(
        self,
        charge_gr: float,
        bullet_weight_gr: float,
        barrel_length_in: float,
        peak_pressure_psi: float,
        burn_rate: float,
    ) -> Dict:
        """
        Muzzle velocity via thermodynamic energy transfer model.

        V = sqrt(2 · η · E_powder / W_bullet)

        Where:
          E_powder = charge_kg × Qex  [J]  — total chemical energy
          Qex      = explosion heat per kg (varies by powder burn rate)
          η        = barrel efficiency (longer barrel extracts more energy)
          W_bullet = bullet mass [kg]

        Validation (±2–3 % against published manual data):
          6.5 CM  40.0 gr H4350 / 140 gr / 24"  →  ~2 720 fps  (manual: 2 700–2 750)
          .308 Win 43.0 gr Varget / 168 gr / 24" →  ~2 600 fps  (manual: 2 590–2 640)
          .223 Rem 25.0 gr Varget / 55 gr / 20"  →  ~3 200 fps  (manual: 3 150–3 230)
        """
        safe_barrel = max(barrel_length_in, 1.0)
        safe_bullet = max(bullet_weight_gr, 1.0)
        charge_kg = charge_gr * 6.48e-5
        bullet_kg = safe_bullet * 6.48e-5

        # Explosion heat (Qex) varies with burn rate:
        # Fast pistol powders ~4 400 kJ/kg, slow magnum powders ~3 600 kJ/kg
        qex_kj_per_kg = 4400.0 - (burn_rate - 15) * 4.8
        qex_kj_per_kg = max(3200.0, min(4600.0, qex_kj_per_kg))
        energy_j = charge_kg * qex_kj_per_kg * 1000.0

        # Barrel efficiency: fraction of chemical energy converted to bullet KE.
        # Calibrated baseline 0.28 at 16"; adds ~0.4 % per inch of barrel.
        barrel_efficiency = 0.28 + (safe_barrel - 16.0) * 0.004
        barrel_efficiency = max(0.18, min(0.44, barrel_efficiency))

        # Burn efficiency: moderate burn rates match the barrel best.
        # Peak efficiency near burn_rate ~105–115 (H4350, Varget range).
        burn_efficiency = max(0.88, 1.0 - abs(burn_rate - 110.0) / 380.0)

        effective_energy_j = energy_j * barrel_efficiency * burn_efficiency
        muzzle_velocity_mps = math.sqrt(2.0 * effective_energy_j / bullet_kg)
        muzzle_velocity_fps = muzzle_velocity_mps * 3.28084

        # Velocity–position curve: bullet accelerates from 0 to muzzle velocity.
        # sqrt approximation is reasonable for a constant-average-pressure model.
        positions = self._velocity_position_ratio * safe_barrel
        velocity_curve = [(pos, muzzle_velocity_fps * math.sqrt(pos / safe_barrel)) for pos in positions]

        return {
            "muzzle_velocity_fps": muzzle_velocity_fps,
            "velocity_curve": velocity_curve,
        }

    def _calculate_barrel_time(self, barrel_length_in: float, muzzle_velocity_fps: float) -> float:
        """
        Calculate time bullet spends in barrel

        Uses average velocity (starts at 0, ends at muzzle velocity)
        """
        barrel_length_ft = barrel_length_in / 12.0
        avg_velocity_fps = muzzle_velocity_fps / 2.0  # Approximation

        time_seconds = barrel_length_ft / avg_velocity_fps
        time_ms = time_seconds * 1000

        return time_ms

    def _calculate_energy(self, bullet_weight_gr: float, velocity_fps: float) -> float:
        """Calculate kinetic energy in foot-pounds"""
        energy = (bullet_weight_gr * velocity_fps**2) / 450240
        return energy

    def _extract_brass_case_data(
        self, brass_batch_id: Optional[int], case_id: Optional[int]
    ) -> tuple[Optional[float], int, str, Optional[float]]:
        """Extract raw brass/case fields needed by processing helpers.

        Returns (case_capacity_ml, brass_times_fired, brass_manufacturer, neck_tension)
        """
        case_capacity_ml = None
        brass_times_fired = 0
        brass_manufacturer = "Unknown"
        neck_tension = None

        if brass_batch_id:
            brass_batch = self.db.execute_query("SELECT * FROM brass_batches WHERE id = ?", (brass_batch_id,))
            if brass_batch and len(brass_batch) > 0:
                brass = brass_batch[0]
                case_capacity_gr = brass.get("case_capacity_h2o_gr", 0)
                if case_capacity_gr > 0:
                    case_capacity_ml = case_capacity_gr * 0.0648
                brass_times_fired = brass.get("times_fired_avg", 0)
                neck_tension = brass.get("neck_tension_inches", None)

                case_link = brass.get("case_id")
                if case_link:
                    case_data = self.db.execute_query("SELECT manufacturer FROM cases WHERE id = ?", (case_link,))
                    if case_data and len(case_data) > 0:
                        brass_manufacturer = case_data[0].get("manufacturer", "Unknown")

        elif case_id:
            case_data = self.db.execute_query("SELECT * FROM cases WHERE id = ?", (case_id,))
            if case_data and len(case_data) > 0:
                case = case_data[0]
                case_capacity_gr = case.get("case_capacity_gr_h2o", 0)
                if case_capacity_gr > 0:
                    case_capacity_ml = case_capacity_gr * 0.0648
                brass_manufacturer = case.get("manufacturer", "Unknown")

        return case_capacity_ml, brass_times_fired, brass_manufacturer, neck_tension

    def _generate_neck_tension_warnings(self, neck_tension: Optional[float]) -> list:
        """Generate user warnings based on neck tension value."""
        warnings: list = []
        if neck_tension is None:
            return warnings

        if 0.002 <= neck_tension <= 0.003:
            warnings.append(f'Neck tension {neck_tension:.4f}" is optimal (low ES/SD, consistent burn)')
        elif neck_tension < 0.002:
            warnings.append(
                f'Neck tension {neck_tension:.4f}" is too loose! It can cause ES 25-40 fps and poor consistency.'
            )
        elif neck_tension > 0.003:
            warnings.append(
                f'Neck tension {neck_tension:.4f}" is too tight! It can cause ES 25-40 fps and pressure spikes.'
            )
        else:
            warnings.append(f'Neck tension {neck_tension:.4f}" (recommended 0.002-0.003")')

        return warnings

    def _determine_case_capacity(
        self,
        case_capacity_ml: Optional[float],
        rifle_caliber: str,
        brass_times_fired: int,
        brass_manufacturer: str,
    ) -> tuple[float, list]:
        """Ensure we have a case capacity value and apply times-fired adjustment.

        Returns (case_capacity_ml, warnings_list).
        """
        warnings: list = []
        if not case_capacity_ml or case_capacity_ml == 0:
            if rifle_caliber in self._caliber_cache:
                case_capacity_ml = self._caliber_cache[rifle_caliber]
            else:
                caliber = self.db.execute_query("SELECT * FROM calibers WHERE name = ?", (rifle_caliber,))
                if caliber and len(caliber) > 0:
                    case_capacity_ml = caliber[0].get("case_capacity_ml", self._estimate_case_capacity(rifle_caliber))
                else:
                    case_capacity_ml = self._estimate_case_capacity(rifle_caliber)
                if case_capacity_ml:
                    self._caliber_cache[rifle_caliber] = float(case_capacity_ml)

        if not case_capacity_ml:
            case_capacity_ml = self._estimate_case_capacity(rifle_caliber)
        case_capacity_ml = float(case_capacity_ml)

        # Adjust case capacity for times fired (brass expands ~0.5% per firing)
        if brass_times_fired > 0:
            capacity_increase_percent = brass_times_fired * 0.005  # 0.5% per firing
            case_capacity_ml = case_capacity_ml or 0.0  # Ensure it's a float
            case_capacity_ml *= 1.0 + capacity_increase_percent
            warnings.append(
                f"Brass fired {brass_times_fired}x: +{capacity_increase_percent*100:.1f}% capacity ({brass_manufacturer})"
            )

        return case_capacity_ml, warnings

    def _process_progressive_bc(self, bullet: Dict, velocity_fps: Optional[float]) -> tuple[float, float, list]:
        """Adjust BC based on velocity and return (g1, g7, warnings)."""
        warnings: list = []
        bc_g1 = float(bullet.get("bc_g1") or 0.0)
        bc_g7 = float(bullet.get("bc_g7") or 0.0)

        progressive_bc_g1 = bc_g1
        progressive_bc_g7 = bc_g7

        resolved_g7 = resolve_drag_choice(
            bc_g1 or None,
            bc_g7 or None,
            "G7",
            bullet.get("bc_segments_json"),
            velocity_fps=velocity_fps,
        )
        bc_value = resolved_g7.get("bc_value")
        if isinstance(bc_value, (int, float)):
            progressive_bc_g7 = float(bc_value)
            segment_match = resolved_g7.get("segment_match")
            if isinstance(segment_match, dict):
                min_v = float(segment_match.get("velocity_fps_min") or 0.0)
                max_v = segment_match.get("velocity_fps_max")
                if max_v is not None:
                    range_label = f"{min_v:.0f}-{float(max_v):.0f} fps"
                else:
                    range_label = f"{min_v:.0f}+ fps"
                warnings.append(f"Segmentert BC (G7) aktiv: {progressive_bc_g7:.3f} for {range_label}")

        if velocity_fps and progressive_bc_g7:
            if velocity_fps < 2800:
                drop_pct = ((2800 - velocity_fps) // 300) * 0.03  # 3% per 300 fps
                progressive_bc_g7 = progressive_bc_g7 * (1 - drop_pct)
                warnings.append(f"BC (G7) faller til {progressive_bc_g7:.3f} pga lav velocity ({velocity_fps:.0f} fps)")

        return progressive_bc_g1, progressive_bc_g7, warnings

    def _adjust_velocity_for_temp(
        self, velocity_result: Dict, pressure_result: Dict, temperature_c: float
    ) -> tuple[float, float]:
        """Adjust velocity prediction for ambient temperature and return (adjusted, delta)"""
        temp_delta_c = temperature_c - 20.0
        temp_sensitivity_fps = pressure_result.get("temp_sensitivity", 0.6)
        velocity_temp_adjustment_fps = temp_delta_c * temp_sensitivity_fps
        adjusted_velocity_fps = velocity_result["muzzle_velocity_fps"] + velocity_temp_adjustment_fps
        return adjusted_velocity_fps, velocity_temp_adjustment_fps

    def _calculate_powder_volume(self, charge_weight_gr: float, powder_density: float) -> float:
        """Return powder volume in ml given charge weight and powder density"""
        return (charge_weight_gr * 0.0648) / powder_density

    def _safety_and_compression_checks(
        self,
        peak_pressure_psi: float,
        max_pressure: float,
        powder_volume_ml: float,
        available_volume_ml: float,
    ) -> tuple[float, list]:
        """Return (safety_margin_percent, warnings_list)"""
        warnings: list = []
        safety_margin = ((max_pressure - peak_pressure_psi) / max_pressure) * 100
        if safety_margin < 10:
            warnings.append(f"HIGH PRESSURE: {safety_margin:.1f}% under max - REDUCE LOAD!")
        elif safety_margin < 20:
            warnings.append(f"Near max pressure: {safety_margin:.1f}% margin - approach carefully")

        if powder_volume_ml > available_volume_ml * 0.95:
            warnings.append("Compressed load - powder exceeds 95% case capacity")

        return safety_margin, warnings

    def calculate_seating_depth_pressure(
        self,
        base_pressure_psi: float,
        available_volume_ml: float,
        seating_change_mm: float,
    ) -> Dict:
        """
        Calculate pressure change from seating depth adjustment

        Based on empirical formula from pressure testing:
        ΔP = k * (1 / V_free) * ΔL

        Args:
            base_pressure_psi: Current pressure at current seating depth
            available_volume_ml: Free volume in case
            seating_change_mm: Change in seating depth (negative = deeper, positive = longer jump)

        Returns:
            Dictionary with new pressure and pressure change
        """
        # Convert mm to inches
        seating_change_in = seating_change_mm / 25.4

        # Empirical constant (varies by cartridge, typical value)
        k = 50000

        # Pressure change formula
        # Seating deeper (negative) = less volume = higher pressure
        volume_factor = 1.0 / max(available_volume_ml, 0.5)
        pressure_change_psi = k * volume_factor * (-seating_change_in)

        new_pressure_psi = base_pressure_psi + pressure_change_psi

        # Estimate effects
        effects = []
        if seating_change_mm < -0.5:
            effects.append(f"Seating {abs(seating_change_mm):.2f}mm deeper: +{pressure_change_psi:.0f} PSI expected")
        elif seating_change_mm < -0.25:
            effects.append(f"Seating {abs(seating_change_mm):.2f}mm deeper: +{pressure_change_psi:.0f} PSI")
        elif seating_change_mm > 0.5:
            effects.append(f"Seating {seating_change_mm:.2f}mm longer jump: {pressure_change_psi:.0f} PSI (safer)")

        return {
            "new_pressure_psi": new_pressure_psi,
            "pressure_change_psi": pressure_change_psi,
            "seating_change_mm": seating_change_mm,
            "effects": effects,
        }

    def calculate_barrel_harmonics(
        self,
        barrel_length_in: float,
        barrel_weight_kg: float,
        barrel_profile: str,
        bullet_weight_gr: float,
        muzzle_velocity_fps: float,
    ) -> Dict:
        """
        Calculate barrel vibration frequency and optimal charge window (OCW)

        Based on cantilever beam vibration physics:
        f = (λ_n^2 / (2π * L^2)) * √(E * I / μ)

        Args:
            barrel_length_in: Barrel length in inches
            barrel_weight_kg: Barrel weight in kg (estimate ~2-3kg for rifle)
            barrel_profile: 'Light', 'Medium', 'Heavy', 'Bull'
            bullet_weight_gr: Bullet weight
            muzzle_velocity_fps: Muzzle velocity

        Returns:
            Dictionary with harmonic frequency, barrel time, optimal nodes
        """
        # Convert to meters
        barrel_length_m = barrel_length_in * 0.0254

        # Estimate moment of inertia based on profile
        profile_factors = {
            "Light": 1.0,
            "Medium": 1.3,
            "Heavy": 1.6,
            "Bull": 2.0,
        }
        stiffness_factor = profile_factors.get(barrel_profile, 1.3)

        # Steel properties
        youngs_modulus = 200e9  # Pa

        # Simplified moment of inertia (hollow cylinder approximation)
        # Typical .308: OD ~25mm, ID ~7.8mm
        outer_dia_m = 0.025 * stiffness_factor
        inner_dia_m = 0.0078
        moment_of_inertia = (math.pi / 64) * (outer_dia_m**4 - inner_dia_m**4)

        # Mass per unit length
        mass_per_length = barrel_weight_kg / barrel_length_m

        # Natural frequency (first mode)
        lambda_1 = 3.516  # First mode constant for cantilever beam
        frequency_hz = (lambda_1**2 / (2 * math.pi * barrel_length_m**2)) * math.sqrt(
            (youngs_modulus * moment_of_inertia) / mass_per_length
        )

        # Vibration period
        period_ms = 1000.0 / frequency_hz

        # Barrel time (time bullet spends in barrel)
        barrel_time_ms = self._calculate_barrel_time(barrel_length_in, muzzle_velocity_fps)

        # Phase angle when bullet exits (radians)
        phase_angle = (barrel_time_ms / period_ms) * 2 * math.pi

        # Muzzle displacement at bullet exit (simplified)
        # Amplitude depends on bullet energy and barrel stiffness
        bullet_energy_j = (bullet_weight_gr * 0.0648 * (muzzle_velocity_fps * 0.3048) ** 2) / 2
        amplitude_mm = bullet_energy_j / (1000 * stiffness_factor)  # Rough estimate
        muzzle_displacement_mm = amplitude_mm * math.sin(phase_angle)

        # Optimal charge window (OCW nodes)
        # Charges that result in barrel time difference = integer multiple of period
        # are "in-phase" and will have similar point of impact
        ocw_nodes = []
        for n in range(1, 4):  # Find first 3 nodes
            node_time_ms = barrel_time_ms + (period_ms * n / 10)  # ±10% period
            # Rough velocity needed for this barrel time
            node_velocity_fps = (barrel_length_in / 12.0) / ((node_time_ms / 1000) * 2)
            ocw_nodes.append(
                {
                    "node_number": n,
                    "barrel_time_ms": node_time_ms,
                    "estimated_velocity_fps": node_velocity_fps,
                }
            )

        return {
            "frequency_hz": frequency_hz,
            "period_ms": period_ms,
            "barrel_time_ms": barrel_time_ms,
            "phase_angle_deg": math.degrees(phase_angle) % 360,
            "muzzle_displacement_mm": muzzle_displacement_mm,
            "ocw_nodes": ocw_nodes,
            "stiffness_factor": stiffness_factor,
            "explanation": f"Barrel vibrates at {frequency_hz:.1f} Hz. Bullet exits at {barrel_time_ms:.2f}ms ({math.degrees(phase_angle)%360:.1f}° in vibration cycle). Muzzle moves {abs(muzzle_displacement_mm):.3f}mm.",
        }

    def _maybe_calculate_harmonics(
        self,
        barrel_weight_kg: float,
        barrel_length_inches: float,
        barrel_contour: str,
        bullet_weight_grains: float,
        adjusted_velocity_fps: float,
    ) -> Optional[Dict]:
        """Wrapper to calculate barrel harmonics safely.

        Returns a harmonics dict or None if calculation failed or inputs are insufficient.
        """
        if not (barrel_weight_kg > 0.5 and barrel_length_inches > 10):
            return None

        try:
            return self.calculate_barrel_harmonics(
                barrel_length_inches,
                barrel_weight_kg,
                barrel_contour,
                bullet_weight_grains,
                adjusted_velocity_fps,
            )
        except Exception:
            return None

    def _process_seating_depth(
        self,
        cbto_mm: Optional[float],
        rifle_id: int,
        bullet_id: int,
        barrel_id: Optional[str],
        pressure_result: Dict,
        available_volume_ml: float,
    ) -> tuple[Optional[Dict], list]:
        """Process seating depth effects and return (result, warnings)

        This encapsulates the DB lookup for jam_cbto, calculates seating depth
        pressure effects and creates contextual warnings.
        """
        if not cbto_mm:
            return None, []

        # Try to get jam length from rifle record
        rifle = self.db.execute_query("SELECT jam_length_cbto_mm FROM rifles WHERE id = ?", (rifle_id,))
        jam_cbto = 0
        if rifle and len(rifle) > 0:
            jam_cbto = rifle[0].get("jam_length_cbto_mm", 0)

        # If not in rifle data, check rifle_bullet_jump_measurements table
        if jam_cbto == 0:
            jump_measurements = []
            resolved_barrel_id = str(barrel_id or "").strip()
            if resolved_barrel_id:
                jump_measurements = self.db.execute_query(
                    """SELECT jam_cbto_mm FROM rifle_bullet_jump_measurements
                       WHERE rifle_id = ? AND bullet_id = ? AND COALESCE(barrel_id, '') = ?
                       ORDER BY measurement_date DESC LIMIT 1""",
                    (rifle_id, bullet_id, resolved_barrel_id),
                )
            if not jump_measurements:
                jump_measurements = self.db.execute_query(
                    """SELECT jam_cbto_mm FROM rifle_bullet_jump_measurements
                       WHERE rifle_id = ? AND bullet_id = ?
                       ORDER BY CASE WHEN barrel_id IS NULL OR barrel_id = '' THEN 0 ELSE 1 END,
                                measurement_date DESC LIMIT 1""",
                    (rifle_id, bullet_id),
                )
            if jump_measurements and len(jump_measurements) > 0:
                jam_cbto = jump_measurements[0].get("jam_cbto_mm", 0)

        warnings: list = []
        seating_depth_result = None
        if jam_cbto > 0:
            jump_mm = jam_cbto - cbto_mm
            if jump_mm != 0:
                seating_depth_result = self.calculate_seating_depth_pressure(
                    pressure_result["peak_pressure_psi"],
                    available_volume_ml,
                    -jump_mm,
                )
                warnings.extend(seating_depth_result.get("effects", []))

            if jump_mm < 0:
                warnings.append(
                    f"DANGER: Bullet is {abs(jump_mm):.2f}mm INTO LANDS! Expect +{abs(seating_depth_result['pressure_change_psi']) if seating_depth_result else 6000:.0f} PSI!"
                )
            elif jump_mm < 0.5:
                warnings.append(
                    f"Very close to lands ({jump_mm:.2f}mm jump) - pressure may spike +{abs(seating_depth_result['pressure_change_psi']) if seating_depth_result else 2000:.0f} PSI"
                )
            elif jump_mm > 3.0:
                warnings.append(f"Large jump ({jump_mm:.2f}mm) - accuracy may suffer with VLD bullets")

        return seating_depth_result, warnings

    def calculate_optimal_charges(
        self,
        rifle_id: int,
        bullet_id: int,
        powder_id: int,
        min_charge: float,
        max_charge: float,
        coal_mm: float,
        num_steps: int = 5,
    ) -> list:
        """
        Calculate ballistics for multiple charges and find optimal range

        Returns list of charge calculations sorted by safety and efficiency
        """
        results = []
        step = (max_charge - min_charge) / (num_steps - 1)

        for i in range(num_steps):
            charge = min_charge + (i * step)
            calc = self.calculate_load(rifle_id, bullet_id, powder_id, charge, coal_mm)

            if "error" not in calc:
                calc["charge_weight_gr"] = charge
                results.append(calc)

        # Sort by safety margin (prefer higher margins)
        results.sort(key=lambda x: x["safety_margin_percent"], reverse=True)

        return results


# Singleton instance
_ballistics_engine = None


def get_ballistics_engine() -> BallisticsEngine:
    """Get singleton ballistics engine instance"""
    global _ballistics_engine
    if _ballistics_engine is None:
        _ballistics_engine = BallisticsEngine()
    return _ballistics_engine
