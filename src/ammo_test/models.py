"""Data models for the ammo test module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AmmoLot:
    """A box/lot of factory or hand-loaded ammunition."""

    id: int | None
    brand: str
    model: str
    caliber: str
    bullet_weight_gr: float | None
    lot_number: str
    purchase_date: str | None  # ISO date
    purchase_price: float | None  # local currency
    store: str | None
    count_purchased: int | None
    count_remaining: int | None
    expiry_date: str | None
    storage_notes: str | None
    notes: str | None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "AmmoLot":
        return cls(
            id=row.get("id"),
            brand=row.get("brand") or "",
            model=row.get("model") or "",
            caliber=row.get("caliber") or "",
            bullet_weight_gr=row.get("bullet_weight_gr"),
            lot_number=row.get("lot_number") or "",
            purchase_date=row.get("purchase_date"),
            purchase_price=row.get("purchase_price"),
            store=row.get("store"),
            count_purchased=row.get("count_purchased"),
            count_remaining=row.get("count_remaining"),
            expiry_date=row.get("expiry_date"),
            storage_notes=row.get("storage_notes"),
            notes=row.get("notes"),
        )


@dataclass
class AmmoTestSession:
    """One shooting session testing a specific lot in one rifle."""

    id: int | None
    lot_id: int
    rifle_id: int | None
    rifle_name: str
    barrel_configuration_id: str | None
    barrel_name: str
    test_date: str  # ISO date
    distance_m: float | None
    temp_c: float | None
    wind_mps: float | None
    wind_dir_deg: float | None
    barometric_pressure_hpa: float | None
    barrel_state: str | None  # cold / warm / unknown
    shots_in_prior_string: int | None
    group_size_mm: float | None
    poi_x_mm: float | None  # horizontal offset from aim point
    poi_y_mm: float | None  # vertical offset from aim point
    image_path: str | None
    notes: str | None

    # Computed from shots — not stored directly
    avg_vel_fps: float | None = None
    es_fps: float | None = None
    sd_fps: float | None = None
    shot_count: int = 0
    dud_count: int = 0
    light_strike_count: int = 0
    ftf_count: int = 0  # failure to feed
    fte_count: int = 0  # failure to eject

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "AmmoTestSession":
        return cls(
            id=row.get("id"),
            lot_id=row["lot_id"],
            rifle_id=row.get("rifle_id"),
            rifle_name=row.get("rifle_name") or "",
            barrel_configuration_id=row.get("barrel_configuration_id"),
            barrel_name=row.get("barrel_name") or "",
            test_date=row.get("test_date") or "",
            distance_m=row.get("distance_m"),
            temp_c=row.get("temp_c"),
            wind_mps=row.get("wind_mps"),
            wind_dir_deg=row.get("wind_dir_deg"),
            barometric_pressure_hpa=row.get("barometric_pressure_hpa"),
            barrel_state=row.get("barrel_state"),
            shots_in_prior_string=row.get("shots_in_prior_string"),
            group_size_mm=row.get("group_size_mm"),
            poi_x_mm=row.get("poi_x_mm"),
            poi_y_mm=row.get("poi_y_mm"),
            image_path=row.get("image_path"),
            notes=row.get("notes"),
        )


@dataclass
class AmmoTestShot:
    """One individual shot within a test session."""

    id: int | None
    session_id: int
    shot_number: int
    velocity_fps: float | None
    is_cold_bore: bool = False
    is_calibration: bool = False
    is_dud: bool = False
    is_light_strike: bool = False
    is_ftf: bool = False
    is_fte: bool = False
    notes: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "AmmoTestShot":
        return cls(
            id=row.get("id"),
            session_id=row["session_id"],
            shot_number=row.get("shot_number") or 0,
            velocity_fps=row.get("velocity_fps"),
            is_cold_bore=bool(row.get("is_cold_bore")),
            is_calibration=bool(row.get("is_calibration")),
            is_dud=bool(row.get("is_dud")),
            is_light_strike=bool(row.get("is_light_strike")),
            is_ftf=bool(row.get("is_ftf")),
            is_fte=bool(row.get("is_fte")),
            notes=row.get("notes"),
        )


@dataclass
class LotComparisonResult:
    """Result of comparing two or more lots head-to-head."""

    lots: list[AmmoLot]
    sessions_by_lot: dict[int, list[AmmoTestSession]]  # lot_id → sessions

    def avg_vel(self, lot_id: int) -> float | None:
        sessions = [s for s in self.sessions_by_lot.get(lot_id, []) if s.avg_vel_fps]
        if not sessions:
            return None
        return sum(s.avg_vel_fps for s in sessions) / len(sessions)  # type: ignore[arg-type]

    def avg_es(self, lot_id: int) -> float | None:
        sessions = [s for s in self.sessions_by_lot.get(lot_id, []) if s.es_fps]
        if not sessions:
            return None
        return sum(s.es_fps for s in sessions) / len(sessions)  # type: ignore[arg-type]

    def avg_group(self, lot_id: int) -> float | None:
        sessions = [s for s in self.sessions_by_lot.get(lot_id, []) if s.group_size_mm]
        if not sessions:
            return None
        return sum(s.group_size_mm for s in sessions) / len(sessions)  # type: ignore[arg-type]

    def reliability_pct(self, lot_id: int) -> float | None:
        sessions = self.sessions_by_lot.get(lot_id, [])
        total = sum(s.shot_count for s in sessions)
        if not total:
            return None
        failures = sum(
            s.dud_count + s.light_strike_count + s.ftf_count + s.fte_count
            for s in sessions
        )
        return round(100.0 * (total - failures) / total, 1)
