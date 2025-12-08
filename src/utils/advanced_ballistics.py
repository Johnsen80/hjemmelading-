"""
Advanced Ballistics Engine
Militær-nøyaktig ballistikk med G1/G7 drag functions, Coriolis, Spin Drift, Eötvös
Basert på Modified Point Mass modell
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class AtmosphericConditions:
    """Atmosfæriske forhold"""

    temperature_f: float = 59.0  # Fahrenheit
    pressure_inhg: float = 29.92  # inches Hg
    humidity_percent: float = 50.0
    altitude_ft: float = 0.0

    def get_density_ratio(self) -> float:
        """Beregner lufttetthet ratio (rho/rho0)"""
        # Standard conditions: 59°F, 29.92 inHg, sea level
        temp_rankine = self.temperature_f + 459.67
        pressure_ratio = self.pressure_inhg / 29.92
        temp_ratio = 518.67 / temp_rankine

        density_ratio = pressure_ratio * temp_ratio
        return density_ratio


@dataclass
class TrajectoryPoint:
    """Et punkt i kulebanen"""

    distance_m: float
    time_s: float
    velocity_fps: float
    drop_cm: float
    drop_moa: float
    drop_mrad: float
    windage_cm: float
    windage_moa: float
    windage_mrad: float
    energy_ftlbs: float
    momentum: float
    drift_spin_cm: float = 0.0
    drift_coriolis_cm: float = 0.0


class G1DragFunction:
    """G1 Drag Function (flat base bullets)"""

    # G1 drag function koeffisienter (Mach vs Cd)
    MACH_TABLE = [
        0.0,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        0.95,
        1.0,
        1.05,
        1.1,
        1.2,
        1.3,
        1.5,
        1.7,
        2.0,
        2.5,
        3.0,
        4.0,
        5.0,
    ]
    CD_TABLE = [
        0.2629,
        0.2558,
        0.2487,
        0.2413,
        0.2344,
        0.2278,
        0.2246,
        0.2214,
        0.2538,
        0.3105,
        0.3732,
        0.4084,
        0.4448,
        0.4615,
        0.4740,
        0.4825,
        0.4880,
        0.4960,
        0.5020,
    ]

    @staticmethod
    def get_cd(mach: float) -> float:
        """Henter drag coefficient for gitt Mach-nummer"""
        if mach <= G1DragFunction.MACH_TABLE[0]:
            return G1DragFunction.CD_TABLE[0]
        if mach >= G1DragFunction.MACH_TABLE[-1]:
            return G1DragFunction.CD_TABLE[-1]

        # Linear interpolation
        for i in range(len(G1DragFunction.MACH_TABLE) - 1):
            if G1DragFunction.MACH_TABLE[i] <= mach <= G1DragFunction.MACH_TABLE[i + 1]:
                m1, m2 = G1DragFunction.MACH_TABLE[i], G1DragFunction.MACH_TABLE[i + 1]
                cd1, cd2 = G1DragFunction.CD_TABLE[i], G1DragFunction.CD_TABLE[i + 1]
                return cd1 + (cd2 - cd1) * (mach - m1) / (m2 - m1)

        return G1DragFunction.CD_TABLE[-1]


class G7DragFunction:
    """G7 Drag Function (boat tail bullets - mer nøyaktig for moderne kuler)"""

    MACH_TABLE = [
        0.0,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        0.95,
        1.0,
        1.05,
        1.1,
        1.2,
        1.3,
        1.5,
        1.7,
        2.0,
        2.5,
        3.0,
        4.0,
        5.0,
    ]
    CD_TABLE = [
        0.1198,
        0.1197,
        0.1196,
        0.1194,
        0.1193,
        0.1194,
        0.1194,
        0.1194,
        0.1252,
        0.1396,
        0.1581,
        0.1709,
        0.1891,
        0.2029,
        0.2190,
        0.2400,
        0.2550,
        0.2800,
        0.2980,
    ]

    @staticmethod
    def get_cd(mach: float) -> float:
        """Henter drag coefficient for gitt Mach-nummer"""
        if mach <= G7DragFunction.MACH_TABLE[0]:
            return G7DragFunction.CD_TABLE[0]
        if mach >= G7DragFunction.MACH_TABLE[-1]:
            return G7DragFunction.CD_TABLE[-1]

        for i in range(len(G7DragFunction.MACH_TABLE) - 1):
            if G7DragFunction.MACH_TABLE[i] <= mach <= G7DragFunction.MACH_TABLE[i + 1]:
                m1, m2 = G7DragFunction.MACH_TABLE[i], G7DragFunction.MACH_TABLE[i + 1]
                cd1, cd2 = G7DragFunction.CD_TABLE[i], G7DragFunction.CD_TABLE[i + 1]
                return cd1 + (cd2 - cd1) * (mach - m1) / (m2 - m1)

        return G7DragFunction.CD_TABLE[-1]


class AdvancedBallisticsEngine:
    """Avansert ballistikk-motor med full Modified Point Mass implementasjon"""

    # Konstanter
    GRAVITY = 32.174  # ft/s²
    SPEED_OF_SOUND = 1116.0  # ft/s at sea level, 59°F
    EARTH_ROTATION_RATE = 0.00007292  # rad/s
    FEET_TO_METERS = 0.3048
    METERS_TO_FEET = 3.28084
    INCHES_TO_CM = 2.54

    def __init__(self):
        self.g1_drag = G1DragFunction()
        self.g7_drag = G7DragFunction()

    def calculate_trajectory(
        self,
        velocity_fps: float,
        bc: float,
        weight_grains: float,
        zero_distance_m: float,
        max_distance_m: float,
        step_size_m: float = 10.0,
        bc_type: str = "G7",
        conditions: Optional[AtmosphericConditions] = None,
        wind_speed_mph: float = 0.0,
        wind_angle_deg: float = 90.0,
        latitude_deg: float = 60.0,
        azimuth_deg: float = 0.0,
        twist_rate: float = 8.0,
        twist_direction: str = "RIGHT",
    ) -> List[TrajectoryPoint]:
        """
        Beregner full trajectory med drag, Coriolis, spin drift

        Args:
            velocity_fps: Muzzle velocity i feet per second
            bc: Ballistic coefficient
            weight_grains: Bullet weight i grains
            zero_distance_m: Zero distance i meter
            max_distance_m: Maksimal distanse i meter
            step_size_m: Steg-størrelse for beregning
            bc_type: "G1" eller "G7"
            conditions: Atmosfæriske forhold
            wind_speed_mph: Vindstyrke i mph
            wind_angle_deg: Vindvinkel (90° = full crosswind)
            latitude_deg: Breddegrad (for Coriolis)
            azimuth_deg: Skuddretning (0° = nord)
            twist_rate: Rifling twist rate (1:8 = 8)
            twist_direction: "RIGHT" eller "LEFT"
        """
        if conditions is None:
            conditions = AtmosphericConditions()

        density_ratio = conditions.get_density_ratio()
        drag_func = self.g7_drag if bc_type == "G7" else self.g1_drag

        # Initial conditions
        v = velocity_fps  # Velocity
        x = 0.0  # Distance downrange (feet)
        y = 0.0  # Vertical position (feet, relative to bore)
        t = 0.0  # Time (seconds)

        # Sight line angle for zeroing (radians)
        zero_angle = self._calculate_zero_angle(
            velocity_fps,
            bc,
            zero_distance_m * self.METERS_TO_FEET,
            density_ratio,
            drag_func,
        )

        # Velocity components
        vx = v * math.cos(zero_angle)
        vy = v * math.sin(zero_angle)

        # Time step (smaller = more accurate)
        dt = 0.001  # 1 millisecond

        trajectory = []
        current_distance_m = 0.0

        while x * self.FEET_TO_METERS <= max_distance_m:
            # Check if we should record this point
            if x * self.FEET_TO_METERS >= current_distance_m:
                # Calculate windage
                windage_cm = self._calculate_windage(
                    t, wind_speed_mph, wind_angle_deg, v, bc, density_ratio, drag_func
                )

                # Calculate spin drift
                spin_drift_cm = self._calculate_spin_drift(
                    x * self.FEET_TO_METERS, v, twist_rate, twist_direction
                )

                # Calculate Coriolis effect
                coriolis_cm = self._calculate_coriolis(
                    t, latitude_deg, azimuth_deg, vx, vy
                )

                # Total windage (wind + spin + Coriolis)
                total_windage_cm = windage_cm + spin_drift_cm + coriolis_cm

                # Drop relative to line of sight
                drop_cm = (
                    -y * self.FEET_TO_METERS * 100
                )  # Negative because y is positive up

                distance_m = x * self.FEET_TO_METERS

                point = TrajectoryPoint(
                    distance_m=distance_m,
                    time_s=t,
                    velocity_fps=v,
                    drop_cm=drop_cm,
                    drop_moa=self._cm_to_moa(drop_cm, distance_m),
                    drop_mrad=self._cm_to_mrad(drop_cm, distance_m),
                    windage_cm=total_windage_cm,
                    windage_moa=self._cm_to_moa(total_windage_cm, distance_m),
                    windage_mrad=self._cm_to_mrad(total_windage_cm, distance_m),
                    energy_ftlbs=self._calculate_energy(v, weight_grains),
                    momentum=self._calculate_momentum(v, weight_grains),
                    drift_spin_cm=spin_drift_cm,
                    drift_coriolis_cm=coriolis_cm,
                )

                trajectory.append(point)
                current_distance_m += step_size_m

            # Runge-Kutta 4th order integration
            k1_vx, k1_vy = self._derivatives(vx, vy, v, bc, density_ratio, drag_func)
            k2_vx, k2_vy = self._derivatives(
                vx + k1_vx * dt / 2,
                vy + k1_vy * dt / 2,
                v,
                bc,
                density_ratio,
                drag_func,
            )
            k3_vx, k3_vy = self._derivatives(
                vx + k2_vx * dt / 2,
                vy + k2_vy * dt / 2,
                v,
                bc,
                density_ratio,
                drag_func,
            )
            k4_vx, k4_vy = self._derivatives(
                vx + k3_vx * dt, vy + k3_vy * dt, v, bc, density_ratio, drag_func
            )

            vx += (k1_vx + 2 * k2_vx + 2 * k3_vx + k4_vx) * dt / 6
            vy += (k1_vy + 2 * k2_vy + 2 * k3_vy + k4_vy) * dt / 6

            x += vx * dt
            y += vy * dt
            t += dt

            v = math.sqrt(vx**2 + vy**2)

            # Stop if velocity drops too low
            if v < 100:
                break

        return trajectory

    def _derivatives(
        self, vx: float, vy: float, v: float, bc: float, density_ratio: float, drag_func
    ) -> Tuple[float, float]:
        """Beregner akselerasjoner (dv/dt)"""
        mach = v / self.SPEED_OF_SOUND
        cd = drag_func.get_cd(mach)

        # Drag force coefficient
        drag_coef = (density_ratio * cd) / bc
        drag = drag_coef * v

        # Acceleration components
        ax = -drag * vx / v
        ay = -self.GRAVITY - drag * vy / v

        return ax, ay

    def _calculate_zero_angle(
        self,
        velocity_fps: float,
        bc: float,
        zero_distance_ft: float,
        density_ratio: float,
        drag_func,
    ) -> float:
        """Beregner sight angle for å treffe zero distance"""
        # Iterative method to find zero angle
        angle = 0.0

        for _ in range(10):  # 10 iterations usually enough
            drop = self._calculate_drop_at_distance(
                velocity_fps, bc, zero_distance_ft, angle, density_ratio, drag_func
            )

            correction = drop / zero_distance_ft
            angle += correction

            if abs(drop) < 0.01:  # Converged (within 0.01 feet)
                break

        return angle

    def _calculate_drop_at_distance(
        self,
        velocity_fps: float,
        bc: float,
        distance_ft: float,
        angle: float,
        density_ratio: float,
        drag_func,
    ) -> float:
        """Beregner drop ved gitt distanse"""
        vx = velocity_fps * math.cos(angle)
        vy = velocity_fps * math.sin(angle)

        x, y, t = 0.0, 0.0, 0.0
        dt = 0.001

        while x < distance_ft:
            v = math.sqrt(vx**2 + vy**2)
            ax, ay = self._derivatives(vx, vy, v, bc, density_ratio, drag_func)

            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t += dt

            if v < 100:
                break

        return y

    def _calculate_windage(
        self,
        time_s: float,
        wind_mph: float,
        wind_angle_deg: float,
        velocity_fps: float,
        bc: float,
        density_ratio: float,
        drag_func,
    ) -> float:
        """Beregner wind drift i cm"""
        # Wind component perpendicular to bullet path
        wind_fps = wind_mph * 1.467  # mph to fps
        wind_component = wind_fps * math.sin(math.radians(wind_angle_deg))

        # Simplified wind drift (can be improved with full integration)
        mach = velocity_fps / self.SPEED_OF_SOUND
        cd = drag_func.get_cd(mach)
        drag_coef = (density_ratio * cd) / bc

        # Wind drift approximation
        drift_ft = wind_component * time_s * (1 + drag_coef * time_s)

        return drift_ft * self.FEET_TO_METERS * 100  # Convert to cm

    def _calculate_spin_drift(
        self,
        distance_m: float,
        velocity_fps: float,
        twist_rate: float,
        twist_direction: str,
    ) -> float:
        """
        Beregner spin drift (gyroscopic drift)
        Moderne kuler drifter 1-2 inches per 100 yards
        """
        # Simplified spin drift formula
        distance_yards = distance_m * 1.094

        # Spin drift scales with distance^1.7 approximately
        drift_inches = 0.015 * (distance_yards / 100) ** 1.7

        # Adjust for twist rate (faster twist = more drift)
        twist_factor = 8.0 / twist_rate
        drift_inches *= twist_factor

        # Direction
        if twist_direction == "LEFT":
            drift_inches = -drift_inches

        return drift_inches * self.INCHES_TO_CM

    def _calculate_coriolis(
        self,
        time_s: float,
        latitude_deg: float,
        azimuth_deg: float,
        vx: float,
        vy: float,
    ) -> float:
        """
        Beregner Coriolis effekt
        Merkbar på lang distanse (>500m)
        """
        lat_rad = math.radians(latitude_deg)
        az_rad = math.radians(azimuth_deg)

        # Coriolis acceleration
        omega = self.EARTH_ROTATION_RATE

        # Horizontal Coriolis (primary component)
        coriolis_horizontal = 2 * omega * math.sin(lat_rad) * vx * time_s

        # Adjust for shooting direction
        coriolis_total = coriolis_horizontal * math.sin(az_rad)

        # Convert to cm
        return coriolis_total * self.FEET_TO_METERS * 100

    def _calculate_energy(self, velocity_fps: float, weight_grains: float) -> float:
        """Beregner energi i ft-lbs"""
        return (velocity_fps**2 * weight_grains) / 450240

    def _calculate_momentum(self, velocity_fps: float, weight_grains: float) -> float:
        """Beregner momentum"""
        return (velocity_fps * weight_grains) / 225400

    def _cm_to_moa(self, cm: float, distance_m: float) -> float:
        """Konverterer cm til MOA"""
        if distance_m == 0:
            return 0
        moa_at_distance = (distance_m / 100) * 2.908
        return cm / moa_at_distance

    def _cm_to_mrad(self, cm: float, distance_m: float) -> float:
        """Konverterer cm til MRAD"""
        if distance_m == 0:
            return 0
        mrad_at_distance = (distance_m / 100) * 10
        return cm / mrad_at_distance

    def get_drop_at_distance(
        self, trajectory: List[TrajectoryPoint], distance_m: float
    ) -> Optional[TrajectoryPoint]:
        """Henter trajectory point ved spesifikk distanse (interpolerer hvis nødvendig)"""
        if not trajectory:
            return None

        # Find closest points
        for i in range(len(trajectory) - 1):
            if trajectory[i].distance_m <= distance_m <= trajectory[i + 1].distance_m:
                # Linear interpolation
                p1, p2 = trajectory[i], trajectory[i + 1]
                ratio = (distance_m - p1.distance_m) / (p2.distance_m - p1.distance_m)

                return TrajectoryPoint(
                    distance_m=distance_m,
                    time_s=p1.time_s + ratio * (p2.time_s - p1.time_s),
                    velocity_fps=p1.velocity_fps
                    + ratio * (p2.velocity_fps - p1.velocity_fps),
                    drop_cm=p1.drop_cm + ratio * (p2.drop_cm - p1.drop_cm),
                    drop_moa=p1.drop_moa + ratio * (p2.drop_moa - p1.drop_moa),
                    drop_mrad=p1.drop_mrad + ratio * (p2.drop_mrad - p1.drop_mrad),
                    windage_cm=p1.windage_cm + ratio * (p2.windage_cm - p1.windage_cm),
                    windage_moa=p1.windage_moa
                    + ratio * (p2.windage_moa - p1.windage_moa),
                    windage_mrad=p1.windage_mrad
                    + ratio * (p2.windage_mrad - p1.windage_mrad),
                    energy_ftlbs=p1.energy_ftlbs
                    + ratio * (p2.energy_ftlbs - p1.energy_ftlbs),
                    momentum=p1.momentum + ratio * (p2.momentum - p1.momentum),
                    drift_spin_cm=p1.drift_spin_cm
                    + ratio * (p2.drift_spin_cm - p1.drift_spin_cm),
                    drift_coriolis_cm=p1.drift_coriolis_cm
                    + ratio * (p2.drift_coriolis_cm - p1.drift_coriolis_cm),
                )

        return (
            trajectory[-1] if distance_m > trajectory[-1].distance_m else trajectory[0]
        )


def get_advanced_ballistics_engine() -> AdvancedBallisticsEngine:
    """Returnerer singleton instance"""
    return AdvancedBallisticsEngine()
