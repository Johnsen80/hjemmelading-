from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChronoData:
    velocities: List[float] = field(default_factory=list)

    def stats(self) -> Dict[str, Optional[float]]:
        if not self.velocities:
            return {"mean": None, "es": None, "sd": None, "n": 0}
        import math

        vals = self.velocities
        n = len(vals)
        mean = sum(vals) / n
        es = max(vals) - min(vals)
        sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
        return {"mean": mean, "es": es, "sd": sd, "n": n}


@dataclass
class LoadShot:
    id: str
    bullet_ref: Optional[str] = None
    powder_ref: Optional[str] = None
    case_ref: Optional[str] = None
    seating_depth_col_mm: Optional[float] = None
    neck_tension: Optional[str] = None
    chrono: ChronoData = field(default_factory=ChronoData)
    group_image_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["chrono"] = {"velocities": self.chrono.velocities}
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoadShot":
        chrono = ChronoData(data.get("chrono", {}).get("velocities", []))
        return cls(
            id=str(data.get("id", "")),
            bullet_ref=data.get("bullet_ref"),
            powder_ref=data.get("powder_ref"),
            case_ref=data.get("case_ref"),
            seating_depth_col_mm=data.get("seating_depth_col_mm"),
            neck_tension=data.get("neck_tension"),
            chrono=chrono,
            group_image_path=data.get("group_image_path"),
        )


@dataclass
class CalibrationTest:
    id: str
    barrel_id: Optional[str] = None
    date: Optional[str] = None
    loads: List[LoadShot] = field(default_factory=list)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "barrel_id": self.barrel_id, "date": self.date, "loads": [load_item.to_dict() for load_item in self.loads], "notes": self.notes}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibrationTest":
        loads = [LoadShot.from_dict(load_item) for load_item in data.get("loads", [])]
        return cls(
            id=str(data.get("id", "")),
            barrel_id=data.get("barrel_id"),
            date=data.get("date"),
            loads=loads,
            notes=data.get("notes"),
        )


def parse_chronograph_csv(path: str) -> ChronoData:
    """Simple CSV parser for chronograph outputs: expects one column of velocities or a CSV with numeric tokens."""
    vals: List[float] = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                # split on common delimiters
                for token in line.replace(";", ",").split(","):
                    token = token.strip()
                    try:
                        v = float(token)
                        vals.append(v)
                    except Exception:
                        # ignore non-numeric tokens
                        pass
    except Exception:
        pass
    return ChronoData(vals)
