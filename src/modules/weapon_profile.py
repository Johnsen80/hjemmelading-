from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Barrel:
    id: str
    name: str = ""
    length_mm: Optional[float] = None
    material: Optional[str] = None
    mount_type: Optional[str] = None
    measurement_points: List[Dict[str, Any]] = field(default_factory=list)
    harmonic_metadata: Dict[str, Any] = field(default_factory=dict)
    # Muzzle / muzzle-device info (suppressor, brake, compensator)
    muzzle_device_type: Optional[str] = (
        None  # e.g. 'suppressor', 'compensator', 'brake', None
    )
    muzzle_device_weight_g: Optional[float] = None
    muzzle_device_length_mm: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Barrel":
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            length_mm=data.get("length_mm"),
            material=data.get("material"),
            mount_type=data.get("mount_type"),
            measurement_points=data.get("measurement_points", []),
            harmonic_metadata=data.get("harmonic_metadata", {}),
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
    caliber: str = ""
    barrel_length_mm: Optional[float] = None
    twist: Optional[str] = None
    muzzle_velocity_mps: Optional[float] = None
    notes: str = ""
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
            caliber=data.get("caliber", ""),
            barrel_length_mm=data.get("barrel_length_mm"),
            twist=data.get("twist"),
            muzzle_velocity_mps=data.get("muzzle_velocity_mps"),
            notes=data.get("notes", ""),
            barrels=barrels,
            optics=optics,
        )


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
