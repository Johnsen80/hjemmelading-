from __future__ import annotations

from typing import Any

PSI_PER_BAR = 14.5037738
DEFAULT_STANDARD_PRIORITY = ("SAAMI", "CIP", "NATO", "USER", "UNKNOWN")


def _normalize_caliber(value: Any) -> str:
    text = str(value or "").strip()
    return " ".join(text.casefold().split())


def _standard_rank(value: Any, preferred_bodies: tuple[str, ...]) -> int:
    body = str(value or "").strip().upper()
    try:
        return preferred_bodies.index(body)
    except ValueError:
        return len(preferred_bodies) + 1


def find_best_cartridge_standard(
    db: Any,
    caliber_name: str,
    preferred_bodies: tuple[str, ...] = DEFAULT_STANDARD_PRIORITY,
) -> dict[str, Any] | None:
    if not db or not str(caliber_name or "").strip():
        return None

    try:
        rows = db.list_cartridge_standards()
    except Exception:
        return None

    needle = _normalize_caliber(caliber_name)
    matches: list[dict[str, Any]] = []
    for row in rows or []:
        row_name = _normalize_caliber(row.get("caliber_name"))
        alt_name = _normalize_caliber(row.get("alt_name"))
        if needle and needle in {row_name, alt_name}:
            matches.append(dict(row))

    if not matches:
        return None

    matches.sort(
        key=lambda row: (
            _standard_rank(row.get("standard_body"), preferred_bodies),
            0 if row.get("max_pressure_psi") not in (None, "") else 1,
            0 if row.get("max_pressure_bar") not in (None, "") else 1,
            0 if row.get("case_capacity_ml") not in (None, "") else 1,
            0 if row.get("drawing_pdf_url") else 1,
        )
    )
    return matches[0]


def get_max_pressure_psi_for_caliber(
    db: Any,
    caliber_name: str,
    preferred_bodies: tuple[str, ...] = DEFAULT_STANDARD_PRIORITY,
    fallback_psi: float | None = None,
) -> float | None:
    standard = find_best_cartridge_standard(db, caliber_name, preferred_bodies)
    if standard:
        max_psi = standard.get("max_pressure_psi")
        if isinstance(max_psi, (int, float)):
            return float(max_psi)
        max_bar = standard.get("max_pressure_bar")
        if isinstance(max_bar, (int, float)):
            return float(max_bar) * PSI_PER_BAR
    return fallback_psi


def build_cartridge_standard_audit(db: Any) -> dict[str, Any]:
    try:
        rows = list(db.list_cartridge_standards()) if db else []
    except Exception:
        rows = []

    total = len(rows)
    counts = {
        "total": total,
        "with_pressure": 0,
        "with_oal": 0,
        "with_case_length": 0,
        "with_case_capacity": 0,
        "with_bullet_diameter": 0,
        "with_neck_diameter": 0,
        "with_drawings": 0,
    }
    for row in rows:
        if row.get("max_pressure_psi") not in (None, "") or row.get(
            "max_pressure_bar"
        ) not in (
            None,
            "",
        ):
            counts["with_pressure"] += 1
        if row.get("oal_mm") not in (None, ""):
            counts["with_oal"] += 1
        if row.get("case_length_mm") not in (None, ""):
            counts["with_case_length"] += 1
        if row.get("case_capacity_ml") not in (None, ""):
            counts["with_case_capacity"] += 1
        if row.get("bullet_diameter_mm") not in (None, ""):
            counts["with_bullet_diameter"] += 1
        if row.get("neck_diameter_mm") not in (None, ""):
            counts["with_neck_diameter"] += 1
        if row.get("drawing_pdf_url"):
            counts["with_drawings"] += 1

    lift_areas: list[str] = []
    if total == 0:
        lift_areas.append(
            "Mangler patronstandarder helt; importer CIP/SAAMI-data først."
        )
    else:
        if counts["with_pressure"] < total:
            lift_areas.append(
                "Fyll ut maks trykk for flere patroner for tryggere pressure-gating og sammenligning."
            )
        if counts["with_case_capacity"] < total:
            lift_areas.append(
                "Mer case capacity-data vil gjøre fyllrate og internballistikk mer presis."
            )
        if (
            counts["with_neck_diameter"] < total
            or counts["with_bullet_diameter"] < total
        ):
            lift_areas.append(
                "Manglende diameterdata begrenser hylse-vs-kammer-sammenligning og neck clearance-analyse."
            )
        if counts["with_drawings"] < total:
            lift_areas.append(
                "Tegning/PDF-lenker mangler på noen patroner; disse vil løfte visuell kontroll og standardvisning."
            )
        if counts["with_oal"] < total or counts["with_case_length"] < total:
            lift_areas.append(
                "Mer komplette lengdedata vil gi bedre bibliotek-prefill og raskere kammer-/magasinchecks."
            )

    return {
        "counts": counts,
        "lift_areas": lift_areas,
    }


def compare_chamber_to_cartridge_standard(
    db: Any,
    caliber_name: str,
    measured: dict[str, Any] | None = None,
) -> dict[str, Any]:
    standard = find_best_cartridge_standard(db, caliber_name)
    measured = dict(measured or {})
    if not standard:
        return {
            "status": "missing_standard",
            "notes": ["Ingen patronstandard funnet for valgt kaliber ennå."],
        }

    def _float(value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    standard_body = str(standard.get("standard_body") or "UNKNOWN").strip() or "UNKNOWN"
    freebore = _float(measured.get("freebore_mm"))
    throat_angle = _float(measured.get("throat_angle_deg"))
    throat_erosion = _float(measured.get("throat_erosion_mm"))
    case_neck = _float(
        measured.get("case_neck_diameter_mm") or measured.get("neck_diameter_mm")
    )
    chamber_neck = _float(measured.get("chamber_neck_diameter_mm"))
    trim_length = _float(measured.get("trim_length_mm"))

    standard_freebore = _float(standard.get("freebore_mm"))
    standard_throat_angle = _float(standard.get("throat_angle_deg"))
    standard_neck = _float(standard.get("neck_diameter_mm"))
    standard_case_length = _float(standard.get("case_length_mm"))

    notes: list[str] = [f"Referanse: {caliber_name} {standard_body}."]
    freebore_delta = None
    throat_angle_delta = None
    neck_clearance = None
    standard_neck_clearance = None
    neck_reference_delta = None
    neck_clearance_basis = None
    trim_delta = None

    if freebore is not None and standard_freebore is not None:
        freebore_delta = round(freebore - standard_freebore, 3)
        notes.append(
            f"Freebore {freebore:.3f} mm mot standard {standard_freebore:.3f} mm ({freebore_delta:+.3f} mm)."
        )
    if throat_angle is not None and standard_throat_angle is not None:
        throat_angle_delta = round(throat_angle - standard_throat_angle, 3)
        notes.append(
            f"Throat-vinkel {throat_angle:.3f}° mot standard {standard_throat_angle:.3f}° ({throat_angle_delta:+.3f}°)."
        )
    if chamber_neck is not None and case_neck is not None:
        neck_clearance = round(chamber_neck - case_neck, 3)
        neck_clearance_basis = "measured_case"
        notes.append(
            f"Kammerneck {chamber_neck:.3f} mm mot registrert hylseneck {case_neck:.3f} mm (klarering {neck_clearance:+.3f} mm)."
        )
    if chamber_neck is not None and standard_neck is not None:
        standard_neck_clearance = round(chamber_neck - standard_neck, 3)
        if neck_clearance is None:
            neck_clearance = standard_neck_clearance
            neck_clearance_basis = "standard_estimate"
        notes.append(
            f"Kammerneck {chamber_neck:.3f} mm mot standard neck {standard_neck:.3f} mm (standardklarering {standard_neck_clearance:+.3f} mm)."
        )
    elif case_neck is not None and standard_neck is not None:
        neck_reference_delta = round(case_neck - standard_neck, 3)
        notes.append(
            f"Registrert neck {case_neck:.3f} mm mot standard neck {standard_neck:.3f} mm (referansedelta {neck_reference_delta:+.3f} mm)."
        )
    if trim_length is not None and standard_case_length is not None:
        trim_delta = round(trim_length - standard_case_length, 3)
        notes.append(
            f"Hylselengde {trim_length:.3f} mm mot standard {standard_case_length:.3f} mm ({trim_delta:+.3f} mm)."
        )
    if throat_erosion is not None:
        notes.append(f"Registrert throat-erosjon {throat_erosion:.3f} mm.")

    status = "ok"
    if neck_clearance is not None and neck_clearance < 0.02:
        status = "watch"
        notes.append(
            "Tight neck-forhold kan gi mer følsom neck tension og seating-respons."
        )
    elif standard_neck_clearance is not None and standard_neck_clearance < 0.02:
        status = "watch"
        notes.append(
            "Standard neck-klarering ser stram ut. Verifiser kammer- og hylsemål før du tolker neck-respons hardt."
        )
    if throat_erosion is not None and throat_erosion >= 0.10:
        status = "watch"
        notes.append(
            "Throat-erosjon vil ofte flytte seating-vindu og nodefølsomhet over tid."
        )
    if freebore_delta is not None and abs(freebore_delta) >= 0.15:
        status = "watch"
        notes.append(
            "Freebore avviker merkbart fra standard og bør tas med i jump-/seating-vurdering."
        )

    return {
        "status": status,
        "standard_body": standard_body,
        "standard": standard,
        "freebore_delta_mm": freebore_delta,
        "throat_angle_delta_deg": throat_angle_delta,
        "neck_clearance_mm": neck_clearance,
        "neck_clearance_basis": neck_clearance_basis,
        "standard_neck_clearance_mm": standard_neck_clearance,
        "neck_reference_delta_mm": neck_reference_delta,
        "trim_delta_mm": trim_delta,
        "throat_erosion_mm": throat_erosion,
        "notes": notes,
    }
