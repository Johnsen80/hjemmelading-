"""
Pressure Safety Calculator
Beregner trykk, load density, og validerer mot SAAMI/CIP/NATO standarder

Basert på:
- Internal Ballistics formler
- SAAMI/CIP pressure standards
- Piobert's Law (burning rate)
- QuickLOAD-style estimering
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .cartridge_standard_support import get_max_pressure_psi_for_caliber


@dataclass
class PressureEstimate:
    """Resultat fra trykkberegning"""

    estimated_psi: float
    max_saami_psi: float
    percent_of_max: float
    safety_rating: str  # 'SAFE', 'CAUTION', 'DANGER'
    load_density_percent: float
    case_fill_percent: float
    compression_ratio: float
    warnings: list
    notes: str


class PressureCalculator:
    """
    Beregner estimert trykk og safety margins

    VIKTIG: Dette er ESTIMATER, ikke målt trykk!
    Bruk alltid offisiell ladningsmanual som primærkilde.
    """

    # SAAMI/CIP Maximum Average Pressure (MAP) limits
    SAAMI_LIMITS = {
        "6.5 Creedmoor": 62000,
        ".308 Winchester": 62000,
        "7.62x51mm NATO": 60191,  # NATO spec
        ".223 Remington": 55000,
        "5.56x45mm NATO": 58000,
        ".30-06 Springfield": 60000,
        "6mm Creedmoor": 62000,
        "6.5x55 Swedish": 51487,  # CIP (conservative)
        ".300 Winchester Magnum": 64000,
        "6.5 PRC": 65000,
    }

    # Powder bulk density (g/cm³) - brukes for load density beregning
    POWDER_DENSITY = {
        "H4350": 0.89,
        "Varget": 0.91,
        "H4895": 0.87,
        "IMR 4064": 0.95,
        "N140": 0.95,
        "N150": 0.92,
        "N160": 0.90,
        "RL16": 0.88,
        "RL26": 0.86,
        "H1000": 0.84,
        "Retumbo": 0.82,
    }

    def __init__(self, database=None):
        """Initialize calculator with optional database connection"""
        self.db = database

    def get_saami_max(self, cartridge: str) -> int:
        """Hent SAAMI/CIP maks trykk for kaliber"""
        if self.db:
            lookup = get_max_pressure_psi_for_caliber(self.db, cartridge)
            if isinstance(lookup, (int, float)) and lookup > 0:
                return int(round(float(lookup)))

            result = self.db.execute_query(
                "SELECT max_avg_pressure_psi FROM cartridge_specs WHERE cartridge_name = ?",
                (cartridge,),
            )
            if result and len(result) > 0:
                return result[0]["max_avg_pressure_psi"]

        # Fallback til hardkodet dict
        return self.SAAMI_LIMITS.get(cartridge, 62000)  # Default 62k PSI

    def calculate_load_density(
        self,
        powder_charge_grains: float,
        powder_name: str,
        case_capacity_grains_h2o: float,
    ) -> float:
        """
        Beregner load density %

        Load density = (powder volume / case volume) * 100
        Optimal: 85-105%

        Args:
            powder_charge_grains: Vekt av krutt i grains
            powder_name: Kruttnavn (for bulk density lookup)
            case_capacity_grains_h2o: Hylse-kapasitet i grains H2O

        Returns:
            Load density i prosent
        """
        # Hent powder bulk density
        bulk_density = self.POWDER_DENSITY.get(powder_name, 0.88)  # Default 0.88 g/cm³

        # Konverter grains til gram
        powder_charge_grams = powder_charge_grains * 0.06479891

        # Beregn powder volume (cm³)
        powder_volume_cm3 = powder_charge_grams / bulk_density

        # Case capacity i cm³ (1 grain H2O ≈ 0.0648 gram, density H2O = 1.0 g/cm³)
        case_volume_cm3 = (case_capacity_grains_h2o * 0.06479891) / 1.0

        # Load density
        load_density = (powder_volume_cm3 / case_volume_cm3) * 100.0

        return load_density

    def calculate_case_fill(
        self,
        powder_charge_grains: float,
        case_capacity_grains_h2o: float,
        bullet_length_inches: float,
        coal_inches: float,
        case_length_inches: float,
    ) -> float:
        """
        Beregner hvor mye av hylsen som er fylt (inkludert bullet intrusion)

        Returns:
            Case fill % (100% = helt fylt, >100% = komprimert)
        """
        # Beregn hvor langt kulen sitter inn i hylsen
        bullet_intrusion = case_length_inches - (coal_inches - bullet_length_inches)
        bullet_intrusion = max(0, bullet_intrusion)  # Kan ikke være negativ

        # Effektiv case capacity (redusert av bullet intrusion)
        # Rough estimate: 1 inch bullet intrusion ≈ 20% volume reduction
        volume_reduction_factor = 1.0 - (bullet_intrusion * 0.20)
        effective_capacity = case_capacity_grains_h2o * volume_reduction_factor

        # Case fill (powder weight / effective capacity)
        case_fill = (powder_charge_grains / effective_capacity) * 100.0

        return case_fill

    def estimate_pressure_from_velocity(
        self,
        cartridge: str,
        bullet_weight_grains: float,
        measured_velocity_fps: float,
        manual_min_velocity: float,
        manual_max_velocity: float,
        manual_min_pressure: float,
        manual_max_pressure: float,
    ) -> float:
        """
        Estimerer trykk basert på målt hastighet og ladningsmanual-data

        Bruker lineær interpolering mellom min og max datapunkter.

        Args:
            cartridge: Kalibernavn
            bullet_weight_grains: Kulevekt
            measured_velocity_fps: Målt hastighet fra chronograph
            manual_min_velocity: Minimum hastighet fra manual
            manual_max_velocity: Maximum hastighet fra manual
            manual_min_pressure: Minimum trykk fra manual (PSI)
            manual_max_pressure: Maximum trykk fra manual (PSI)

        Returns:
            Estimert trykk i PSI
        """
        # Sjekk at velocity er innenfor range
        if measured_velocity_fps < manual_min_velocity:
            # Under minimum - extrapolate ned
            velocity_ratio = (measured_velocity_fps - manual_min_velocity) / (
                manual_max_velocity - manual_min_velocity
            )
            estimated_psi = manual_min_pressure + (
                velocity_ratio * (manual_max_pressure - manual_min_pressure)
            )
            return max(estimated_psi, 0)

        elif measured_velocity_fps > manual_max_velocity:
            # Over maximum - ADVARSEL!
            velocity_ratio = (measured_velocity_fps - manual_min_velocity) / (
                manual_max_velocity - manual_min_velocity
            )
            estimated_psi = manual_min_pressure + (
                velocity_ratio * (manual_max_pressure - manual_min_pressure)
            )
            return estimated_psi

        else:
            # Innenfor range - linear interpolation
            velocity_ratio = (measured_velocity_fps - manual_min_velocity) / (
                manual_max_velocity - manual_min_velocity
            )
            estimated_psi = manual_min_pressure + (
                velocity_ratio * (manual_max_pressure - manual_min_pressure)
            )
            return estimated_psi

    def estimate_pressure_from_charge(
        self,
        cartridge: str,
        powder_charge_grains: float,
        manual_min_charge: float,
        manual_max_charge: float,
        manual_min_pressure: float,
        manual_max_pressure: float,
    ) -> float:
        """
        Estimerer trykk basert på ladningsvekt

        MERK: Trykkurven er IKKE lineær, men denne gir en rough estimate.
        Trykk øker eksponentielt nær max!
        """
        if powder_charge_grains <= manual_min_charge:
            return manual_min_pressure
        elif powder_charge_grains >= manual_max_charge:
            return manual_max_pressure

        # Ikke-lineær kurve (power function)
        # Pressure increases exponentially near max
        charge_ratio = (powder_charge_grains - manual_min_charge) / (
            manual_max_charge - manual_min_charge
        )

        # Eksponentiell faktor (trykk øker raskere ved høye ladninger)
        pressure_ratio = charge_ratio**1.5  # Power 1.5 gir realistic kurve

        estimated_psi = manual_min_pressure + (
            pressure_ratio * (manual_max_pressure - manual_min_pressure)
        )
        return estimated_psi

    def calculate_compression_ratio(
        self, case_volume_cm3: float, powder_volume_cm3: float, bullet_volume_cm3: float
    ) -> float:
        """
        Beregner compression ratio

        CR = (case volume) / (powder volume + bullet volume)
        CR < 1.0 = compressed load
        CR = 1.0 = 100% full
        CR > 1.0 = air space
        """
        total_volume = powder_volume_cm3 + bullet_volume_cm3
        if total_volume == 0:
            return 1.0

        compression_ratio = case_volume_cm3 / total_volume
        return compression_ratio

    def evaluate_safety(
        self,
        cartridge: str,
        powder_charge_grains: float,
        powder_name: str,
        bullet_weight_grains: float,
        case_capacity_grains_h2o: float,
        measured_velocity_fps: Optional[float] = None,
        manual_data: Optional[Dict] = None,
    ) -> PressureEstimate:
        """
        Evaluerer total sikkerhet for en ladning

        Args:
            cartridge: Kalibernavn (f.eks. "6.5 Creedmoor")
            powder_charge_grains: Ladningsvekt
            powder_name: Kruttnavn
            bullet_weight_grains: Kulevekt
            case_capacity_grains_h2o: Hylse-kapasitet
            measured_velocity_fps: Målt hastighet (optional)
            manual_data: Dict med manual data (optional):
                {
                    'min_charge': float,
                    'max_charge': float,
                    'min_velocity': float,
                    'max_velocity': float,
                    'min_pressure': float,
                    'max_pressure': float
                }

        Returns:
            PressureEstimate med full safety analysis
        """
        warnings = []

        # Hent SAAMI max
        max_saami_psi = self.get_saami_max(cartridge)

        # Estimer trykk
        if manual_data and measured_velocity_fps:
            # Beste metode: Velocity-basert med manual data
            estimated_psi = self.estimate_pressure_from_velocity(
                cartridge,
                bullet_weight_grains,
                measured_velocity_fps,
                manual_data["min_velocity"],
                manual_data["max_velocity"],
                manual_data["min_pressure"],
                manual_data["max_pressure"],
            )
        elif manual_data:
            # Charge-basert estimering
            estimated_psi = self.estimate_pressure_from_charge(
                cartridge,
                powder_charge_grains,
                manual_data["min_charge"],
                manual_data["max_charge"],
                manual_data["min_pressure"],
                manual_data["max_pressure"],
            )
        else:
            # Ingen manual data - rough estimate
            # Anta at 90% av max charge = 85% av max pressure
            estimated_psi = max_saami_psi * 0.85
            warnings.append(
                "ADVARSEL: Ingen manual-data tilgjengelig! Estimat er svært usikkert."
            )

        # Beregn % av SAAMI max
        percent_of_max = (estimated_psi / max_saami_psi) * 100.0

        # Safety rating
        if percent_of_max > 100:
            safety_rating = "DANGER"
            warnings.append(
                f"⛔ FARE! Estimert trykk ({estimated_psi:,.0f} PSI) overstiger SAAMI max ({max_saami_psi:,} PSI)!"
            )
        elif percent_of_max > 95:
            safety_rating = "CAUTION"
            warnings.append(
                f"FORSIKTIG! Ladning er nær SAAMI max ({percent_of_max:.1f}% av max)."
            )
        else:
            safety_rating = "SAFE"

        # Beregn load density
        load_density = self.calculate_load_density(
            powder_charge_grains, powder_name, case_capacity_grains_h2o
        )

        # Load density warnings
        if load_density < 85:
            warnings.append(
                f"Lav load density ({load_density:.1f}%). Kan gi høy ES. Vurder raskere krutt."
            )
        elif load_density > 105:
            warnings.append(
                f"⛔ HØYT komprimert ladning ({load_density:.1f}%)! FARE for hylseutvidelse!"
            )

        # Case fill (forenklet - uten bullet intrusion)
        case_fill = (powder_charge_grains / case_capacity_grains_h2o) * 100.0

        # Compression ratio (forenklet)
        compression_ratio = 1.0 / (load_density / 100.0) if load_density > 0 else 1.0

        # Notater
        notes = f"Estimert trykk: {estimated_psi:,.0f} PSI ({percent_of_max:.1f}% av SAAMI max {max_saami_psi:,} PSI)"

        if measured_velocity_fps:
            notes += f"\nMålt hastighet: {measured_velocity_fps:.0f} fps"

        notes += f"\nLoad density: {load_density:.1f}%"

        return PressureEstimate(
            estimated_psi=estimated_psi,
            max_saami_psi=max_saami_psi,
            percent_of_max=percent_of_max,
            safety_rating=safety_rating,
            load_density_percent=load_density,
            case_fill_percent=case_fill,
            compression_ratio=compression_ratio,
            warnings=warnings,
            notes=notes,
        )

    def check_load_against_manual(
        self, powder_charge: float, manual_min: float, manual_max: float
    ) -> Tuple[bool, str]:
        """
        Sjekker om ladning er innenfor manual-range

        Returns:
            (is_safe, message)
        """
        if powder_charge < manual_min:
            return (
                False,
                (
                    f"Ladning ({powder_charge:.1f}gr) er UNDER manual minimum "
                    f"({manual_min:.1f}gr). "
                    "Kan gi upålitelig tenning."
                ),
            )
        elif powder_charge > manual_max:
            return (
                False,
                f"⛔ FARE! Ladning ({powder_charge:.1f}gr) OVERSTIGER manual maximum ({manual_max:.1f}gr)!",
            )
        elif powder_charge > manual_max * 0.98:
            return (
                True,
                f"FORSIKTIG! Ladning ({powder_charge:.1f}gr) er nær manual max ({manual_max:.1f}gr).",
            )
        else:
            margin = ((manual_max - powder_charge) / manual_max) * 100
            return True, f"Ladning OK. {margin:.1f}% margin til max."


# Eksempel på bruk
if __name__ == "__main__":
    calc = PressureCalculator()

    # Test case: 6.5 Creedmoor
    result = calc.evaluate_safety(
        cartridge="6.5 Creedmoor",
        powder_charge_grains=41.0,
        powder_name="H4350",
        bullet_weight_grains=140,
        case_capacity_grains_h2o=52.5,
        measured_velocity_fps=2710,
        manual_data={
            "min_charge": 39.0,
            "max_charge": 42.5,
            "min_velocity": 2550,
            "max_velocity": 2750,
            "min_pressure": 52000,
            "max_pressure": 62000,
        },
    )

    print("PRESSURE SAFETY ANALYSIS")
    print("=" * 60)
    print(f"Safety Rating: {result.safety_rating}")
    print(f"Estimated Pressure: {result.estimated_psi:,.0f} PSI")
    print(f"SAAMI Max: {result.max_saami_psi:,} PSI")
    print(f"Percent of Max: {result.percent_of_max:.1f}%")
    print(f"Load Density: {result.load_density_percent:.1f}%")
    print(f"\n{result.notes}")

    if result.warnings:
        print("\nWARNINGS:")
        for warning in result.warnings:
            print(f"  {warning}")
