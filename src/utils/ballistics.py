"""
Ballistikk-modul for Reloading Workshop Manager
Beregninger for ballistikk, zero shift, og ammunisjonsbytte
"""

import math
from typing import Tuple, Dict, List
from dataclasses import dataclass


@dataclass
class BallisticData:
    """Dataklasse for ballistiske data"""
    velocity: float  # fps
    bc: float  # Ballistisk koeffisient
    weight: float  # grains
    zero_distance: float  # meter
    bc_type: str = "G1"  # G1 eller G7


class BallisticsCalculator:
    """Beregner ballistikk og ammunisjonsbytte"""
    
    # Konstanter
    GRAVITY = 9.80665  # m/s²
    FEET_TO_METERS = 0.3048
    METERS_TO_FEET = 3.28084
    INCHES_TO_CM = 2.54
    
    def __init__(self):
        """Initialiserer kalkulator"""
        pass
    
    def calculate_drop(self, velocity_fps: float, bc: float, distance_m: float,
                       zero_distance_m: float = 100, bc_type: str = "G1") -> float:
        """
        Beregner drop (fall) i cm ved gitt avstand
        Forenklet ballistisk modell - kan forbedres med mer avansert ballistikk
        """
        # Konverter til SI-enheter
        velocity_ms = velocity_fps * self.FEET_TO_METERS
        
        # Beregn time of flight (forenklet)
        time = distance_m / velocity_ms
        
        # Beregn drop fra tyngdekraft
        drop_m = 0.5 * self.GRAVITY * time * time
        
        # Juster for BC (forenklet drag-modell)
        drag_factor = 1.0 / (bc * 0.5) if bc > 0 else 1.0
        drop_m *= drag_factor
        
        # Beregn drop ved zero-avstand
        zero_time = zero_distance_m / velocity_ms
        zero_drop_m = 0.5 * self.GRAVITY * zero_time * zero_time * drag_factor
        
        # Juster for zero
        adjusted_drop_m = drop_m - zero_drop_m
        
        # Konverter til cm
        return adjusted_drop_m * 100
    
    def calculate_velocity_at_distance(self, initial_velocity_fps: float, bc: float,
                                       distance_m: float, bc_type: str = "G1") -> float:
        """Beregner hastighet ved gitt avstand"""
        # Forenklet beregning - kan forbedres
        velocity_ms = initial_velocity_fps * self.FEET_TO_METERS
        
        # Hastighetstap basert på drag
        drag_factor = 1.0 / (bc * 2.0) if bc > 0 else 0.1
        velocity_loss = drag_factor * distance_m
        
        final_velocity_ms = max(velocity_ms - velocity_loss, velocity_ms * 0.5)
        return final_velocity_ms / self.FEET_TO_METERS
    
    def calculate_zero_shift(self, ammo1: BallisticData, ammo2: BallisticData,
                            distance_m: float) -> Dict[str, float]:
        """
        Beregner forskjell i treffpunkt mellom to ammunisjoner
        Returnerer forskjell i cm og MOA/MRAD
        """
        # Beregn drop for begge ammunisjoner
        drop1_cm = self.calculate_drop(
            ammo1.velocity, ammo1.bc, distance_m, 
            ammo1.zero_distance, ammo1.bc_type
        )
        
        drop2_cm = self.calculate_drop(
            ammo2.velocity, ammo2.bc, distance_m,
            ammo2.zero_distance, ammo2.bc_type
        )
        
        # Forskjell i cm
        difference_cm = drop2_cm - drop1_cm
        
        # Konverter til MOA og MRAD
        moa = self.cm_to_moa(difference_cm, distance_m)
        mrad = self.cm_to_mrad(difference_cm, distance_m)
        
        return {
            'difference_cm': difference_cm,
            'difference_moa': moa,
            'difference_mrad': mrad,
            'drop_ammo1_cm': drop1_cm,
            'drop_ammo2_cm': drop2_cm
        }
    
    def cm_to_moa(self, cm: float, distance_m: float) -> float:
        """Konverterer cm til MOA ved gitt avstand"""
        # 1 MOA = 1 tomme ved 100 yards ≈ 2.908 cm ved 100m
        moa_at_distance = (distance_m / 100) * 2.908
        return cm / moa_at_distance
    
    def cm_to_mrad(self, cm: float, distance_m: float) -> float:
        """Konverterer cm til MRAD ved gitt avstand"""
        # 1 MRAD = 10 cm ved 100m
        mrad_at_distance = (distance_m / 100) * 10
        return cm / mrad_at_distance
    
    def calculate_clicks(self, difference: float, click_value: float, 
                        unit: str = "MOA") -> int:
        """
        Beregner antall klikk nødvendig for justering
        difference: forskjell i MOA eller MRAD
        click_value: verdi per klikk (f.eks. 0.25 for 1/4 MOA)
        """
        clicks = round(difference / click_value)
        return clicks
    
    def generate_adjustment_table(self, ammo1: BallisticData, ammo2: BallisticData,
                                 distances: List[float], click_value: float,
                                 click_unit: str = "MOA") -> List[Dict]:
        """
        Genererer tabell med justeringer for flere avstander
        """
        table = []
        
        for distance in distances:
            shift = self.calculate_zero_shift(ammo1, ammo2, distance)
            
            if click_unit.upper() == "MOA":
                adjustment = shift['difference_moa']
            elif click_unit.upper() == "MRAD":
                adjustment = shift['difference_mrad']
            else:
                adjustment = 0
            
            clicks = self.calculate_clicks(adjustment, click_value, click_unit)
            
            table.append({
                'distance_m': distance,
                'difference_cm': shift['difference_cm'],
                'adjustment_value': adjustment,
                'clicks': clicks,
                'direction': 'UP' if clicks > 0 else 'DOWN' if clicks < 0 else 'ZERO'
            })
        
        return table
    
    def calculate_energy(self, velocity_fps: float, weight_grains: float) -> float:
        """Beregner energi i ft-lbs"""
        return (velocity_fps ** 2 * weight_grains) / 450240
    
    def calculate_momentum(self, velocity_fps: float, weight_grains: float) -> float:
        """Beregner momentum"""
        return (velocity_fps * weight_grains) / 225400


class SeatingDepthCalculator:
    """Beregner optimal settedybde (COAL/CBTO)"""
    
    def __init__(self):
        pass
    
    def calculate_jam_length(self, ogive_to_base: float, case_length: float) -> float:
        """
        Beregner "jam" lengde (kule helt inn i rifling)
        ogive_to_base: Målt lengde fra ogive til kulebase
        case_length: Hylselengde
        """
        # Dette må måles manuelt av bruker
        return ogive_to_base + case_length
    
    def calculate_jump(self, cbto: float, jam_length: float) -> float:
        """Beregner 'jump' (avstand til lands)"""
        return jam_length - cbto
    
    def suggest_test_depths(self, jam_length: float, start_jump: float = 0.020,
                           end_jump: float = 0.060, steps: int = 5) -> List[Dict]:
        """
        Foreslår test-settedybder basert på jam-length
        Avstander i inches
        """
        suggestions = []
        step_size = (end_jump - start_jump) / (steps - 1)
        
        for i in range(steps):
            jump = start_jump + (i * step_size)
            cbto = jam_length - jump
            
            suggestions.append({
                'test_number': i + 1,
                'jump_inches': jump,
                'cbto_inches': cbto,
                'description': self._jump_description(jump)
            })
        
        return suggestions
    
    def _jump_description(self, jump: float) -> str:
        """Gir beskrivelse av jump-avstand"""
        if jump < 0.010:
            return "Meget nær lands (høy presisjon, høyere trykk)"
        elif jump < 0.030:
            return "Nær lands (balansert)"
        elif jump < 0.050:
            return "Moderat jump (trygt, god presisjon)"
        else:
            return "Langt jump (lavere trykk, kan redusere presisjon)"


class AnnealingCalculator:
    """Beregner glødetid for hylser"""
    
    # Temperatur og tid avhenger av materiale og tykkelse
    ANNEALING_TEMPS = {
        'brass': {'temp_celsius': 700, 'time_seconds': 3.5},
        'nickel_brass': {'temp_celsius': 720, 'time_seconds': 4.0}
    }
    
    def __init__(self):
        pass
    
    def calculate_annealing_time(self, material: str = 'brass',
                                case_thickness: float = 0.015,
                                times_fired: int = 0) -> Dict:
        """
        Beregner anbefalt glødetid
        case_thickness: tykkelse i inches
        """
        base_data = self.ANNEALING_TEMPS.get(material.lower(), 
                                             self.ANNEALING_TEMPS['brass'])
        
        # Juster for tykkelse
        thickness_factor = case_thickness / 0.015  # 0.015" er standard
        adjusted_time = base_data['time_seconds'] * thickness_factor
        
        return {
            'material': material,
            'temperature_celsius': base_data['temp_celsius'],
            'time_seconds': round(adjusted_time, 1),
            'times_fired': times_fired,
            'recommendation': self._annealing_recommendation(times_fired)
        }
    
    def _annealing_recommendation(self, times_fired: int) -> str:
        """Anbefaling for når hylser bør glødes"""
        if times_fired < 3:
            return "Ikke nødvendig ennå"
        elif times_fired < 5:
            return "Vurder gløding snart"
        elif times_fired < 8:
            return "Anbefalt å gløde nå"
        else:
            return "Bør glødes for å unngå sprekkdannelse"
    
    def should_anneal(self, times_fired: int, last_annealed_count: int = 0) -> bool:
        """Sjekker om hylser bør glødes"""
        firings_since_anneal = times_fired - last_annealed_count
        return firings_since_anneal >= 5
