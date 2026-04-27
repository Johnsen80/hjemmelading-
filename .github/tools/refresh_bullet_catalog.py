from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(r"c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading")
EXPORT_DIR = REPO_ROOT / ".github" / "data" / "exports"
MASTER_PATH = EXPORT_DIR / "bullets_catalog_master.csv"
TIDY_PATH = EXPORT_DIR / "bullets_catalog_tidy.csv"


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter=";", extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def safe_write_with_fallback(
    path: Path, rows: list[dict[str, Any]], fieldnames: list[str]
) -> Path:
    try:
        write_rows(path, rows, fieldnames)
        return path
    except PermissionError:
        fallback = path.with_name(f"{path.stem}_refreshed{path.suffix}")
        write_rows(fallback, rows, fieldnames)
        return fallback


def safe_float(value: Any) -> float | None:
    try:
        text = str(value or "").strip().replace(",", ".")
        return float(text) if text else None
    except Exception:
        return None


def safe_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def contains_any(text: str, *needles: str) -> bool:
    haystack = f" {str(text or '').strip().lower()} "
    return any(needle.strip().lower() in haystack for needle in needles if needle)


def infer_terminal_window(
    *,
    name_bits: str,
    construction_type: str,
    tip_type: str,
    intended_use: str,
) -> tuple[float | None, float | None, float | None, str]:
    construction = str(construction_type or "").strip().lower()
    tip = str(tip_type or "").strip().lower()
    use = str(intended_use or "").strip().lower()

    minimum_expansion_fps: float | None = None
    preferred_impact_min_fps: float | None = None
    preferred_impact_max_fps: float | None = None
    terminal_notes: list[str] = []

    if construction == "monolithic" or contains_any(
        name_bits,
        " tsx",
        " ttsx",
        " cx ",
        " copper",
        " mono",
        " monolithic",
        " ecostrike",
    ):
        minimum_expansion_fps = 1900.0
        preferred_impact_min_fps = 2000.0
        preferred_impact_max_fps = 3200.0
        terminal_notes.append("monolithic profile")
    elif construction == "bonded" or contains_any(
        name_bits, " bonded", " accubond", " interbond", " oryx", " fusion"
    ):
        minimum_expansion_fps = 1700.0
        preferred_impact_min_fps = 1800.0
        preferred_impact_max_fps = 3000.0
        terminal_notes.append("bonded hunting profile")
    elif use == "varmint" or contains_any(
        name_bits, " varmint", " vmax", " blitz", " tnt ", " ballistic tip varmint"
    ):
        minimum_expansion_fps = 2200.0
        preferred_impact_min_fps = 2400.0
        preferred_impact_max_fps = 3400.0
        terminal_notes.append("varmint profile")
    elif tip == "polymer_tip" or contains_any(
        name_bits,
        " polymer",
        " tipped",
        " ballistic tip",
        " sst",
        " eld-x",
        " intertip",
    ):
        minimum_expansion_fps = 1600.0 if use == "hunting" else 1800.0
        preferred_impact_min_fps = 1750.0 if use == "hunting" else 1900.0
        preferred_impact_max_fps = (
            3150.0 if use == "hunting" else preferred_impact_max_fps
        )
        terminal_notes.append("polymer-tip profile")
    elif tip == "soft_point" or construction == "hunting_jacketed" or use == "hunting":
        minimum_expansion_fps = 1600.0
        preferred_impact_min_fps = 1750.0
        preferred_impact_max_fps = 3000.0
        terminal_notes.append("traditional hunting profile")
    elif construction == "match" or contains_any(
        name_bits, " match", " smk", " scenar", " otm", " rdf", " eld-m"
    ):
        minimum_expansion_fps = 1800.0
        preferred_impact_min_fps = 1900.0
        terminal_notes.append("match-like terminal guess")
    elif (
        construction == "fmj"
        or tip == "fmj"
        or contains_any(name_bits, " fmj", " full metal jacket")
    ):
        minimum_expansion_fps = 2000.0
        terminal_notes.append("fmj / low-expansion profile")
    elif use == "subsonic" or contains_any(name_bits, " sub-x", " subx", " subsonic"):
        minimum_expansion_fps = 950.0
        preferred_impact_min_fps = 1000.0
        preferred_impact_max_fps = 1250.0
        terminal_notes.append("subsonic profile")

    terminal_hint = " | ".join(terminal_notes)
    return (
        minimum_expansion_fps,
        preferred_impact_min_fps,
        preferred_impact_max_fps,
        terminal_hint,
    )


def estimate_greenhill_twist_inches(
    diameter_mm: float | None,
    length_mm: float | None,
    muzzle_velocity_fps: float | None = None,
) -> float | None:
    if not diameter_mm or not length_mm:
        return None
    diameter_in = float(diameter_mm) / 25.4
    length_in = float(length_mm) / 25.4
    if diameter_in <= 0 or length_in <= 0:
        return None
    constant = 180.0 if float(muzzle_velocity_fps or 0.0) >= 2800.0 else 150.0
    twist = (constant * (diameter_in**2)) / length_in
    return round(twist, 1) if twist > 0 else None


def build_name_bits(
    row: dict[str, Any], profile: dict[str, Any], raw: dict[str, Any]
) -> str:
    parts = [
        row.get("manufacturer"),
        row.get("name"),
        row.get("display_name"),
        row.get("type"),
        row.get("raw_type"),
        row.get("profile_type"),
        raw.get("mname"),
        raw.get("pname"),
        raw.get("type"),
        raw.get("gUBCS"),
        raw.get("descr"),
    ]
    return " ".join(
        str(part or "").strip() for part in parts if str(part or "").strip()
    ).lower()


def enrich_row(row: dict[str, Any]) -> dict[str, Any]:
    profile = safe_json(row.get("profile_json"))
    raw = safe_json(row.get("raw_json"))
    name_bits = build_name_bits(row, profile, raw)

    diameter_mm = (
        safe_float(row.get("diameter_mm"))
        or safe_float(profile.get("diameter_mm"))
        or safe_float(raw.get("gdia"))
    )
    length_mm = (
        safe_float(row.get("length_mm"))
        or safe_float(profile.get("length_mm"))
        or safe_float(raw.get("glen"))
    )
    diameter_in = safe_float(row.get("diameter_in")) or (
        round(diameter_mm / 25.4, 4) if diameter_mm else None
    )

    tail_type = row.get("base_type") or profile.get("tail_type") or raw.get("gtailtype")
    base_type = str(row.get("base_type") or "").strip()
    if not base_type:
        tail_height = safe_float(profile.get("tail_height_mm")) or safe_float(
            raw.get("gtailh")
        )
        tail_dia_a = safe_float(profile.get("tail_dia_a_mm")) or safe_float(
            raw.get("gtaildiaA")
        )
        if isinstance(tail_type, (int, float)) and float(tail_type) > 0:
            base_type = "boat_tail"
        elif tail_height and tail_height > 0:
            base_type = "boat_tail"
        elif tail_dia_a and diameter_mm and tail_dia_a < diameter_mm:
            base_type = "boat_tail"
        elif contains_any(
            name_bits,
            " hpbt",
            " bt ",
            " boat tail",
            " bthp",
            "btsp",
            "lrbt",
            "vld",
            "hybrid",
        ):
            base_type = "boat_tail"
        elif contains_any(
            name_bits, " flat base", " fb ", " fbhp", " round nose", " rn "
        ):
            base_type = "flat_base"

    tip_type = str(row.get("tip_type") or "").strip()
    if not tip_type:
        if contains_any(
            name_bits,
            " polymer",
            " ballistic tip",
            " accutip",
            " tip ",
            " tipped",
            " vmax",
            "sst",
            "eld-x",
            "eld-m",
            "a-tip",
            " sub-x",
            " terminal ascent",
            " gamechanger",
            " game changer",
        ):
            tip_type = "polymer_tip"
        elif contains_any(
            name_bits,
            " hollow point",
            " hp ",
            " hpbt",
            " bthp",
            "otm",
            " matchburner",
            " h-mantle",
            " hollow nose",
        ):
            tip_type = "hollow_point"
        elif contains_any(
            name_bits,
            " soft point",
            " sp ",
            " jsp",
            " interlock",
            " power-point",
            " pro-hunter",
            " core-lokt",
        ):
            tip_type = "soft_point"
        elif contains_any(name_bits, " round nose", " rn "):
            tip_type = "round_nose"
        elif contains_any(name_bits, " fmj", " full metal jacket"):
            tip_type = "fmj"

    construction_type = str(row.get("construction_type") or "").strip()
    if not construction_type:
        if contains_any(
            name_bits,
            "mono",
            " monolithic",
            "tsx",
            "ttsx",
            " ttsx ",
            " cx ",
            " cutting edge",
            " copper",
            "solid",
            " lrx ",
            " e-tip",
            " etip",
            " naturalis",
            " gmx ",
            " hammer hunter",
            " fox classic hunter",
        ):
            construction_type = "monolithic"
        elif contains_any(
            name_bits,
            "bonded",
            " interbond",
            " accubond",
            " accubond lr",
            " oryx",
            " fusion",
            " a-frame",
            " aframe",
            " trophy bonded",
            " bear claw",
            " terminal ascent",
        ):
            construction_type = "bonded"
        elif contains_any(name_bits, " fmj", " full metal jacket"):
            construction_type = "fmj"
        elif contains_any(
            name_bits,
            " match",
            " smk",
            " scenar",
            " hybrid",
            " rdf",
            "eld-m",
            " berger",
            " otm",
            " tmk",
            " a-tip",
            " hpbt",
            " bthp",
            " target elite",
            " competition",
            " matchking",
            " custom competition",
        ):
            construction_type = "match"
        elif contains_any(
            name_bits,
            " soft point",
            " hunting",
            " interlock",
            " ecostrike",
            " deadtough",
            " gameking",
            " pro-hunter",
            " power-point",
            " partition",
            " core-lokt",
            " sst",
            " eld-x",
            " interbond",
            " terminal ascent",
            " game changer",
            " gamechanger",
            " tipped gameking",
            " tgk",
            " mega",
            " hammer hunter",
        ):
            construction_type = "hunting_jacketed"
        elif tip_type == "soft_point":
            construction_type = "hunting_jacketed"
        elif tip_type == "fmj":
            construction_type = "fmj"
        elif tip_type == "hollow_point" and contains_any(
            name_bits, " match", "otm", "tmk", "smk", "scenar", "hpbt", "bthp"
        ):
            construction_type = "match"

    shape_family = str(row.get("shape_family") or "").strip()
    if not shape_family:
        if contains_any(name_bits, "vld", "hybrid", "eld", "rdf", " a-tip"):
            shape_family = "vld"
        elif contains_any(name_bits, " round nose", " rn "):
            shape_family = "round_nose"
        elif contains_any(name_bits, " wadcutter", " wc ", " swc "):
            shape_family = "wadcutter"
        elif contains_any(name_bits, "spitzer", "hpbt", "bthp", "bt ", " sp "):
            shape_family = "spitzer"
        elif contains_any(
            name_bits, " hunting", " interlock", " gameking", " ecostrike"
        ):
            shape_family = "hunting"

    intended_use = str(row.get("intended_use") or "").strip()
    if not intended_use:
        if contains_any(
            name_bits,
            " varmint",
            " vmax",
            " blitz",
            " tnt ",
            " varmint grenade",
            " ballistic tip varmint",
        ):
            intended_use = "varmint"
        elif contains_any(
            name_bits,
            " hunting",
            " interlock",
            " accubond",
            " tsx",
            " ttsx",
            " oryx",
            " ecostrike",
            " deadtough",
            " gameking",
            " tipped gameking",
            " tgk",
            " partition",
            " terminal ascent",
            " core-lokt",
            " power-point",
            " pro-hunter",
            " sst",
            " eld-x",
            " a-frame",
            " fusion",
            " lrx",
            " e-tip",
            " hammer hunter",
        ):
            intended_use = "hunting"
        elif contains_any(
            name_bits,
            " match",
            " smk",
            " scenar",
            " hybrid",
            "eld-m",
            " rdf",
            " otm",
            " tmk",
            " hpbt",
            " bthp",
            " matchking",
            " custom competition",
            " target elite",
            " a-tip",
        ):
            intended_use = "match"
        elif contains_any(name_bits, " sub-x", " subx", " subsonic"):
            intended_use = "subsonic"
        elif contains_any(
            name_bits, " fmj", " full metal jacket", " range", " training"
        ):
            intended_use = "training"
        elif construction_type in {"monolithic", "bonded", "hunting_jacketed"}:
            intended_use = "hunting"
        elif construction_type == "match":
            intended_use = "match"
        elif construction_type == "fmj":
            intended_use = "training"
        elif tip_type == "soft_point":
            intended_use = "hunting"
        elif tip_type == "polymer_tip" and contains_any(
            name_bits, " vmax", " blitz", " varm", " tnt "
        ):
            intended_use = "varmint"
        elif tip_type == "polymer_tip":
            intended_use = "hunting"
        elif tip_type == "hollow_point" and contains_any(
            name_bits, " match", "otm", "tmk", "smk", "scenar", "hpbt", "bthp"
        ):
            intended_use = "match"

    recommended_twist = safe_float(row.get("recommended_twist"))
    if recommended_twist is None:
        recommended_twist = estimate_greenhill_twist_inches(diameter_mm, length_mm)

    minimum_expansion_fps = safe_float(row.get("minimum_expansion_fps"))
    preferred_impact_min_fps = safe_float(row.get("preferred_impact_min_fps"))
    preferred_impact_max_fps = safe_float(row.get("preferred_impact_max_fps"))
    terminal_hint = str(row.get("terminal_notes") or "").strip()
    if (
        minimum_expansion_fps is None
        and preferred_impact_min_fps is None
        and preferred_impact_max_fps is None
    ):
        (
            minimum_expansion_fps,
            preferred_impact_min_fps,
            preferred_impact_max_fps,
            terminal_hint,
        ) = infer_terminal_window(
            name_bits=name_bits,
            construction_type=construction_type,
            tip_type=tip_type,
            intended_use=intended_use,
        )

    notes: list[str] = []
    if recommended_twist is not None:
        notes.append(f"Greenhill ca. 1:{recommended_twist:.1f}")
    if base_type:
        notes.append(base_type.replace("_", " "))
    if construction_type:
        notes.append(construction_type.replace("_", " "))
    if terminal_hint:
        notes.append(terminal_hint)

    inference_score = 0
    for field in (
        base_type,
        tip_type,
        shape_family,
        construction_type,
        intended_use,
        recommended_twist,
        minimum_expansion_fps,
        preferred_impact_min_fps,
    ):
        if field not in (None, ""):
            inference_score += 1
    if inference_score >= 5:
        confidence = "high"
    elif inference_score >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        **row,
        "diameter_mm": (
            diameter_mm if diameter_mm is not None else row.get("diameter_mm")
        ),
        "diameter_in": (
            diameter_in if diameter_in is not None else row.get("diameter_in")
        ),
        "length_mm": length_mm if length_mm is not None else row.get("length_mm"),
        "base_type": base_type,
        "tip_type": tip_type,
        "shape_family": shape_family,
        "construction_type": construction_type,
        "intended_use": intended_use,
        "minimum_expansion_fps": (
            minimum_expansion_fps
            if minimum_expansion_fps is not None
            else row.get("minimum_expansion_fps")
        ),
        "preferred_impact_min_fps": (
            preferred_impact_min_fps
            if preferred_impact_min_fps is not None
            else row.get("preferred_impact_min_fps")
        ),
        "preferred_impact_max_fps": (
            preferred_impact_max_fps
            if preferred_impact_max_fps is not None
            else row.get("preferred_impact_max_fps")
        ),
        "terminal_notes": terminal_hint,
        "recommended_twist": (
            recommended_twist
            if recommended_twist is not None
            else row.get("recommended_twist")
        ),
        "inference_confidence": confidence,
        "geometry_notes": " | ".join(notes),
    }


def main() -> None:
    rows = read_rows(MASTER_PATH)
    enriched = [enrich_row(row) for row in rows]

    all_fields = list(enriched[0].keys()) if enriched else []
    if "geometry_notes" not in all_fields:
        all_fields.append("geometry_notes")

    tidy_fields = [
        field
        for field in [
            "id",
            "display_name",
            "manufacturer",
            "name",
            "caliber",
            "weight_grains",
            "diameter_mm",
            "diameter_in",
            "length_mm",
            "bc_g1",
            "bc_g7",
            "base_type",
            "tip_type",
            "shape_family",
            "construction_type",
            "intended_use",
            "minimum_expansion_fps",
            "preferred_impact_min_fps",
            "preferred_impact_max_fps",
            "terminal_notes",
            "recommended_twist",
            "inference_confidence",
            "geometry_notes",
            "source_label",
            "evidence_level",
            "notes",
        ]
        if field in all_fields
    ]

    written_master = safe_write_with_fallback(MASTER_PATH, enriched, all_fields)
    written_tidy = safe_write_with_fallback(TIDY_PATH, enriched, tidy_fields)

    print(
        json.dumps(
            {
                "rows": len(enriched),
                "master": str(written_master),
                "tidy": str(written_tidy),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
