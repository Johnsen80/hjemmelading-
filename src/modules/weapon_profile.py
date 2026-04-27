from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CaseMeasurements:
    standard: Optional[str] = None
    trim_length_mm: Optional[float] = None
    trim_length_in: Optional[float] = None
    shoulder_bump_mm: Optional[float] = None
    shoulder_bump_in: Optional[float] = None
    base_to_datum_mm: Optional[float] = None
    base_to_datum_in: Optional[float] = None
    neck_diameter_mm: Optional[float] = None
    neck_diameter_in: Optional[float] = None
    h2o_capacity_grains: Optional[float] = None
    h2o_measurements: List[Dict[str, float]] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "CaseMeasurements":
        raw = data or {}
        return cls(
            standard=raw.get("standard"),
            trim_length_mm=raw.get("trim_length_mm"),
            trim_length_in=raw.get("trim_length_in"),
            shoulder_bump_mm=raw.get("shoulder_bump_mm"),
            shoulder_bump_in=raw.get("shoulder_bump_in"),
            base_to_datum_mm=raw.get("base_to_datum_mm"),
            base_to_datum_in=raw.get("base_to_datum_in"),
            neck_diameter_mm=raw.get("neck_diameter_mm"),
            neck_diameter_in=raw.get("neck_diameter_in"),
            h2o_capacity_grains=raw.get("h2o_capacity_grains"),
            h2o_measurements=raw.get("h2o_measurements", []) or [],
            notes=raw.get("notes", ""),
        )


@dataclass
class Barrel:
    id: str
    name: str = ""
    caliber: str = ""
    usage_type: str = "general"
    status: str = "active"
    length_mm: Optional[float] = None
    material: Optional[str] = None
    mount_type: Optional[str] = None
    barrel_attachment_type: Optional[str] = None
    barrel_profile: Optional[str] = None
    twist: Optional[str] = None
    measurement_points: List[Dict[str, Any]] = field(default_factory=list)
    harmonic_metadata: Dict[str, Any] = field(default_factory=dict)
    case_measurements: CaseMeasurements = field(default_factory=CaseMeasurements)
    # Harmonics Quick + Scorecard fields
    barrel_profile_id: Optional[str] = None
    free_float_length_mm: Optional[float] = None
    tuner_mass_g: Optional[float] = None
    tuner_position_mm: Optional[float] = None
    action_stiffness: Optional[str] = None  # 'soft', 'normal', 'rigid'
    support_type: Optional[str] = None  # 'bipod', 'rest', 'freehand'
    barrel_torque_nm: Optional[float] = None
    barrel_return_to_zero: Optional[str] = None
    harmonic_score: Optional[float] = None
    node_bands: Optional[list] = field(default_factory=list)
    # Muzzle / muzzle-device info (suppressor, brake, compensator)
    muzzle_device_type: Optional[str] = (
        None  # e.g. 'suppressor', 'compensator', 'brake', None
    )
    muzzle_device_model: Optional[str] = None
    muzzle_device_weight_g: Optional[float] = None
    muzzle_device_length_mm: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["case_measurements"] = self.case_measurements.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Barrel":
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            caliber=data.get("caliber", ""),
            usage_type=data.get("usage_type", "general"),
            status=data.get("status", "active"),
            length_mm=data.get("length_mm"),
            material=data.get("material"),
            mount_type=data.get("mount_type"),
            barrel_attachment_type=data.get("barrel_attachment_type"),
            barrel_profile=data.get("barrel_profile"),
            twist=data.get("twist"),
            measurement_points=data.get("measurement_points", []),
            harmonic_metadata=data.get("harmonic_metadata", {}),
            case_measurements=CaseMeasurements.from_dict(data.get("case_measurements")),
            barrel_profile_id=data.get("barrel_profile_id"),
            free_float_length_mm=data.get("free_float_length_mm"),
            tuner_mass_g=data.get("tuner_mass_g"),
            tuner_position_mm=data.get("tuner_position_mm"),
            action_stiffness=data.get("action_stiffness"),
            support_type=data.get("support_type"),
            barrel_torque_nm=data.get("barrel_torque_nm"),
            barrel_return_to_zero=data.get("barrel_return_to_zero"),
            harmonic_score=data.get("harmonic_score"),
            node_bands=data.get("node_bands", []),
            muzzle_device_type=data.get("muzzle_device_type"),
            muzzle_device_model=data.get("muzzle_device_model"),
            muzzle_device_weight_g=data.get("muzzle_device_weight_g"),
            muzzle_device_length_mm=data.get("muzzle_device_length_mm"),
        )


@dataclass
class Optic:
    id: str
    name: str = ""
    manufacturer: Optional[str] = None
    type: str = "telescopic"  # e.g. 'telescopic','thermal','prism','red_dot'
    zero_distance_m: Optional[float] = None
    turret_units: str = "mil"  # 'mil' or 'moa'
    click_value: Optional[float] = None  # in turret_units (e.g. 0.1 mrad or 0.25 MOA)
    clicks_per_rev: Optional[int] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Optic":
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            manufacturer=data.get("manufacturer"),
            type=data.get("type", "telescopic"),
            zero_distance_m=data.get("zero_distance_m"),
            turret_units=data.get("turret_units", "mil"),
            click_value=data.get("click_value"),
            clicks_per_rev=data.get("clicks_per_rev"),
            notes=data.get("notes", ""),
        )


@dataclass
class WeaponProfile:
    id: str
    name: str = ""
    weapon_type: str = "rifle"
    preferred_units: str = "metric"
    caliber: str = ""
    barrel_length_mm: Optional[float] = None
    twist: Optional[str] = None
    muzzle_velocity_mps: Optional[float] = None
    notes: str = ""
    active_barrel_id: Optional[str] = None
    barrels: List[Barrel] = field(default_factory=list)
    optics: List[Optic] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # ensure barrels are serializable dicts
        d["barrels"] = [b.to_dict() for b in self.barrels]
        # ensure optics are serializable dicts
        d["optics"] = [o.to_dict() for o in self.optics]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeaponProfile":
        barrels = [Barrel.from_dict(b) for b in data.get("barrels", [])]
        optics = [Optic.from_dict(o) for o in data.get("optics", [])]
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            weapon_type=data.get("weapon_type", "rifle"),
            preferred_units=data.get("preferred_units", "metric"),
            caliber=data.get("caliber", ""),
            barrel_length_mm=data.get("barrel_length_mm"),
            twist=data.get("twist"),
            muzzle_velocity_mps=data.get("muzzle_velocity_mps"),
            notes=data.get("notes", ""),
            active_barrel_id=data.get("active_barrel_id"),
            barrels=barrels,
            optics=optics,
        )

    def get_active_barrel(self) -> Optional[Barrel]:
        if self.active_barrel_id:
            for barrel in self.barrels:
                if barrel.id == self.active_barrel_id:
                    return barrel
        return self.barrels[0] if self.barrels else None


def load_profiles(path: Optional[Path]) -> List[WeaponProfile]:
    p = Path(path) if path else Path("data") / "demo_weapons.json"
    if not p.exists():
        return []
    try:
        with open(p, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return [WeaponProfile.from_dict(r) for r in raw]
    except Exception:
        return []


def save_profiles(path: Optional[Path], profiles: List[WeaponProfile]) -> None:
    p = Path(path) if path else Path("data") / "demo_weapons.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump([pfi.to_dict() for pfi in profiles], fh, indent=2, ensure_ascii=False)
