from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = (
    REPO_ROOT
    / ".github"
    / "tmp"
    / "gordon_extract_recheck"
    / "gordon_extracted_projectiles_raw.csv"
)
OUTPUT_CSV = REPO_ROOT / ".github" / "data" / "component_knowledge_base" / "bullets.csv"


def _read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _safe_float(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _extract_from_projectile_name(projectile_name: str) -> dict[str, str]:
    text = str(projectile_name or "").strip()
    if not text:
        return {}
    result: dict[str, str] = {}
    parts = [part.strip() for part in text.split(",")]
    if len(parts) >= 1 and parts[0]:
        result["manufacturer"] = parts[0]
    if len(parts) >= 2 and parts[1]:
        result["name"] = parts[1]
    if len(parts) >= 3 and parts[2]:
        result["caliber"] = parts[2]
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*grain", text, flags=re.IGNORECASE)
    if match:
        result["weight_grains"] = match.group(1)
    return result


def _source_label(source_file: str) -> str:
    path = Path(str(source_file or "").strip())
    name = path.name
    lower_name = name.lower()
    if lower_name.endswith(".xml"):
        return f"component_xml:{name}"
    if lower_name.endswith(".grtload"):
        return f"grtload:{name}"
    return name


def _to_inches(mm_value: Any) -> float | None:
    mm_number = _safe_float(mm_value)
    if mm_number is None:
        return None
    return round(mm_number / 25.4, 3)


def build_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    next_id = 1
    for raw in raw_rows:
        derived = _extract_from_projectile_name(raw.get("ProjectileName") or "")
        manufacturer = str(
            raw.get("mname") or derived.get("manufacturer") or ""
        ).strip()
        name = str(raw.get("pname") or derived.get("name") or "").strip()
        caliber = str(raw.get("caliber") or derived.get("caliber") or "").strip()
        weight_grains = _safe_float(raw.get("gmass"))
        if weight_grains is None:
            weight_grains = _safe_float(derived.get("weight_grains"))
        bc_g1 = _safe_float(raw.get("g1bc"))
        bc_g7 = _safe_float(raw.get("g7bc"))
        length_in = _to_inches(raw.get("glen"))
        diameter_in = _to_inches(raw.get("Dbul") or raw.get("gdia"))
        row = {
            "bullet_id": next_id,
            "manufacturer": manufacturer,
            "name": name or str(raw.get("ProjectileName") or "").strip(),
            "caliber": caliber,
            "weight_grains": weight_grains if weight_grains is not None else "",
            "bc_g1": bc_g1 if bc_g1 is not None else "",
            "bc_g7": bc_g7 if bc_g7 is not None else "",
            "length_in": length_in if length_in is not None else "",
            "diameter_in": diameter_in if diameter_in is not None else "",
            "type": str(raw.get("type") or "").strip(),
            "source_label": _source_label(str(raw.get("source_file") or "")),
            "raw_json": json.dumps(raw, ensure_ascii=False),
        }
        rows.append(row)
        next_id += 1
    return rows


def write_rows(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "bullet_id",
        "manufacturer",
        "name",
        "caliber",
        "weight_grains",
        "bc_g1",
        "bc_g7",
        "length_in",
        "diameter_in",
        "type",
        "source_label",
        "raw_json",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows(_read_rows(RAW_CSV))
    write_rows(rows, OUTPUT_CSV)
    print(
        json.dumps(
            {"rows_written": len(rows), "output": str(OUTPUT_CSV)}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
