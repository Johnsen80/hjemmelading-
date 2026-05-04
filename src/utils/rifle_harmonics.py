from __future__ import annotations

import json
import math
from typing import Any, Dict, Iterable, List, Optional

from ..database.database import get_database
from .cartridge_standard_support import compare_chamber_to_cartridge_standard

_STIFFNESS_ORDER = {
    "very-light": 0.45,
    "light": 0.65,
    "medium": 1.0,
    "heavy": 1.3,
    "very-heavy": 1.55,
    "bull": 1.8,
}

_ACTION_STIFFNESS = {
    "soft": 0.9,
    "normal": 1.0,
    "rigid": 1.1,
}

_SUPPORT_STABILITY = {
    "freehand": 0.88,
    "bipod": 1.0,
    "rest": 1.08,
}

_ATTACHMENT_FACTOR = {
    "unknown": 0.98,
    "threaded": 1.02,
    "barrel_nut": 1.0,
    "quick_change": 0.96,
    "press_fit": 0.99,
    "integrated_pistol": 0.97,
}


def _first_float(values: Iterable[Any], default: float = 0.0) -> float:
    for value in values:
        try:
            if value is None or value == "":
                continue
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _parse_jsonish(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    try:
        return json.loads(text)
    except Exception:
        return value


def normalize_node_bands(raw: Any) -> List[Dict[str, Any]]:
    parsed = _parse_jsonish(raw)
    if not parsed:
        return []
    if isinstance(parsed, list):
        bands: List[Dict[str, Any]] = []
        for item in parsed:
            if isinstance(item, dict):
                bands.append(
                    {
                        "start_mm": _first_float([item.get("start_mm"), item.get("start"), item.get("from")]),
                        "end_mm": _first_float([item.get("end_mm"), item.get("end"), item.get("to")]),
                        "robustness": max(
                            0.0,
                            min(
                                1.0,
                                _first_float([item.get("robustness"), item.get("score")], 0.5),
                            ),
                        ),
                        "label": item.get("label") or item.get("name") or "node",
                    }
                )
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                bands.append(
                    {
                        "start_mm": _first_float([item[0]]),
                        "end_mm": _first_float([item[1]]),
                        "robustness": 0.5,
                        "label": "node",
                    }
                )
        return bands
    if isinstance(parsed, dict):
        return [parsed]
    return []


def _resolve_active_barrel_details(
    profile_details: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Return a flattened view of the active/selected barrel for harmonics calculations."""
    details = dict(profile_details or {})
    barrels = details.get("barrels", [])
    if not isinstance(barrels, list) or not barrels:
        return details

    selected_id = details.get("selected_barrel_id") or details.get("active_barrel_id")
    selected_barrel = None

    if selected_id:
        for barrel in barrels:
            if isinstance(barrel, dict) and str(barrel.get("id")) == str(selected_id):
                selected_barrel = barrel
                break

    if selected_barrel is None:
        first_barrel = barrels[0]
        if isinstance(first_barrel, dict):
            selected_barrel = first_barrel

    if not isinstance(selected_barrel, dict):
        return details

    details.setdefault("selected_barrel_id", selected_barrel.get("id"))
    details.setdefault("selected_barrel_name", selected_barrel.get("name"))
    details.setdefault("barrel_length_mm", selected_barrel.get("length_mm"))
    details.setdefault("barrel_profile", selected_barrel.get("barrel_profile"))
    details.setdefault("barrel_attachment_type", selected_barrel.get("barrel_attachment_type"))
    details.setdefault("free_float_length_mm", selected_barrel.get("free_float_length_mm"))
    details.setdefault("action_stiffness", selected_barrel.get("action_stiffness"))
    details.setdefault("support_type", selected_barrel.get("support_type"))
    details.setdefault("barrel_torque_nm", selected_barrel.get("barrel_torque_nm"))
    details.setdefault("barrel_return_to_zero", selected_barrel.get("barrel_return_to_zero"))
    details.setdefault("muzzle_device_weight_g", selected_barrel.get("muzzle_device_weight_g"))
    details.setdefault("muzzle_device_length_mm", selected_barrel.get("muzzle_device_length_mm"))
    details.setdefault("has_muzzle_device", bool(selected_barrel.get("muzzle_device_type")))

    for key in ("tuner_mass_g", "tuner_position_mm", "node_bands", "harmonic_score"):
        if key in selected_barrel and key not in details:
            details[key] = selected_barrel.get(key)

    barrel_harmonics = selected_barrel.get("harmonic_metadata")
    if isinstance(barrel_harmonics, dict):
        harmonics = details.get("harmonics")
        if not isinstance(harmonics, dict):
            harmonics = {}
        merged_harmonics = dict(barrel_harmonics)
        merged_harmonics.update(harmonics)
        details["harmonics"] = merged_harmonics

    return details


def calculate_harmonics_profile(
    rifle: Optional[Dict[str, Any]] = None,
    profile_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    rifle = rifle or {}
    profile_details = _resolve_active_barrel_details(profile_details)
    harmonics = profile_details.get("harmonics", {})
    if not isinstance(harmonics, dict):
        harmonics = {}

    rifle_id = rifle.get("id") or profile_details.get("rifle_id")
    rifle_name = rifle.get("name") or profile_details.get("rifle_name") or "unknown"
    barrel_name = profile_details.get("selected_barrel_name") or profile_details.get("barrel_name") or "standard"
    caliber_name = rifle.get("caliber") or profile_details.get("caliber") or profile_details.get("cartridge_name") or ""
    profile_scope = "rifle-bound" if rifle_id is not None else "unbound"

    barrel_length_mm = _first_float(
        [
            profile_details.get("barrel_length_mm"),
            harmonics.get("barrel_length_mm"),
            rifle.get("barrel_length_mm"),
            rifle.get("barrel_length"),
        ],
        600.0,
    )
    barrel_profile = (
        profile_details.get("barrel_profile") or rifle.get("barrel_contour") or rifle.get("barrel_profile") or "medium"
    )
    barrel_profile_text = str(barrel_profile).lower()
    profile_factor = _STIFFNESS_ORDER.get(barrel_profile_text, 1.0)

    muzzle_dia = _first_float(
        [
            rifle.get("muzzle_diameter_mm"),
            profile_details.get("muzzle_diameter"),
            profile_details.get("muzzle_diameter_mm"),
        ],
        18.0,
    )
    breech_dia = _first_float(
        [
            rifle.get("breech_diameter_mm"),
            profile_details.get("breech_diameter"),
            profile_details.get("breech_diameter_mm"),
        ],
        28.0,
    )
    barrel_weight_g = _first_float([rifle.get("barrel_weight_grams"), profile_details.get("barrel_weight")], 2200.0)
    free_float_mm = _first_float(
        [
            harmonics.get("free_float_length_mm"),
            profile_details.get("free_float_length_mm"),
        ],
        0.0,
    )
    tuner_mass_g = _first_float([harmonics.get("tuner_mass_g")], 0.0)
    tuner_position_mm = _first_float([harmonics.get("tuner_position_mm")], 0.0)
    action_stiffness = str(
        harmonics.get("action_stiffness") or profile_details.get("action_stiffness") or "normal"
    ).lower()
    support_type = str(harmonics.get("support_type") or profile_details.get("support_type") or "bipod").lower()
    attachment_type = str(
        profile_details.get("barrel_attachment_type") or profile_details.get("mount_type") or "unknown"
    ).lower()
    attachment_factor = _ATTACHMENT_FACTOR.get(attachment_type, 1.0)
    barrel_torque_nm = _first_float([profile_details.get("barrel_torque_nm")], 0.0)
    return_to_zero = profile_details.get("barrel_return_to_zero") or ""
    muzzle_device_mass_g = _first_float(
        [
            profile_details.get("device_weight"),
            profile_details.get("muzzle_device_weight_g"),
            harmonics.get("muzzle_device_mass_g"),
        ],
        0.0,
    )
    muzzle_device_length_mm = _first_float(
        [
            profile_details.get("device_length"),
            profile_details.get("muzzle_device_length_mm"),
            harmonics.get("muzzle_device_length_mm"),
        ],
        0.0,
    )
    has_muzzle_device = bool(
        profile_details.get("has_muzzle_device") or muzzle_device_mass_g > 0 or muzzle_device_length_mm > 0
    )

    case_measurements = profile_details.get("case_measurements", {}) or {}
    chamber_inputs = {
        "freebore_mm": profile_details.get("freebore_mm") or rifle.get("freebore_mm"),
        "throat_angle_deg": profile_details.get("throat_angle_deg") or rifle.get("throat_angle_deg"),
        "throat_erosion_mm": profile_details.get("throat_erosion_mm") or rifle.get("throat_erosion_mm"),
        "case_neck_diameter_mm": case_measurements.get("neck_diameter_mm"),
        "trim_length_mm": case_measurements.get("trim_length_mm"),
    }
    chamber_comparison: Dict[str, Any] = {}
    if caliber_name:
        try:
            chamber_comparison = compare_chamber_to_cartridge_standard(
                get_database(), str(caliber_name), chamber_inputs
            )
        except Exception:
            chamber_comparison = {}

    required_inputs = {
        "barrel_length_mm": barrel_length_mm > 0,
        "barrel_profile": bool(barrel_profile and barrel_profile != "medium"),
        "barrel_weight_g": barrel_weight_g > 0,
        "attachment_type": bool(attachment_type and attachment_type != "unknown"),
        "action_stiffness": bool(action_stiffness and action_stiffness != "normal"),
        "support_type": bool(support_type and support_type != "bipod"),
    }
    optional_inputs = {
        "muzzle_device": has_muzzle_device,
        "muzzle_device_weight_g": muzzle_device_mass_g > 0,
        "tuner_mass_g": tuner_mass_g > 0,
        "free_float_length_mm": free_float_mm > 0,
        "barrel_torque_nm": barrel_torque_nm > 0,
        "return_to_zero": bool(return_to_zero),
    }
    missing_required = [key for key, ok in required_inputs.items() if not ok]
    estimated_inputs = []
    if not required_inputs["barrel_profile"]:
        estimated_inputs.append("barrel_profile defaulted to medium")
    if not required_inputs["attachment_type"]:
        estimated_inputs.append("attachment type unknown")
    if not required_inputs["action_stiffness"]:
        estimated_inputs.append("action stiffness defaulted to normal")
    if not required_inputs["support_type"]:
        estimated_inputs.append("support type defaulted to bipod")

    effective_length_mm = max(1.0, barrel_length_mm - min(free_float_mm, barrel_length_mm * 0.35))
    muzzle_ratio = max(0.5, muzzle_dia / max(breech_dia, 1.0))
    mass_factor = max(0.55, min(1.65, barrel_weight_g / max(barrel_length_mm, 1.0) / 3.0))
    stiffness_factor = profile_factor * (1.0 + (muzzle_ratio - 0.65) * 0.45) * mass_factor
    action_factor = _ACTION_STIFFNESS.get(action_stiffness, 1.0)
    support_factor = _SUPPORT_STABILITY.get(support_type, 1.0)
    muzzle_device_factor = 1.0 + (muzzle_device_mass_g / 1000.0) * 0.08 + (muzzle_device_length_mm / 100.0) * 0.04
    tuner_factor = 1.0 + (tuner_mass_g / 500.0) * 0.06

    estimated_frequency_hz = max(
        30.0,
        min(
            220.0,
            72.0
            * math.sqrt(max(stiffness_factor, 0.3))
            * action_factor
            * support_factor
            * attachment_factor
            / math.sqrt(max(effective_length_mm / 600.0, 0.4))
            / math.sqrt(muzzle_device_factor * tuner_factor),
        ),
    )
    period_ms = 1000.0 / estimated_frequency_hz

    base_score = 10.0
    base_score += (stiffness_factor - 1.0) * 6.0
    base_score += (action_factor - 1.0) * 4.0
    base_score += (support_factor - 1.0) * 3.0
    base_score += (attachment_factor - 1.0) * 10.0
    base_score += min(2.0, free_float_mm / 250.0)
    base_score += min(2.0, tuner_mass_g / 250.0)
    base_score -= min(2.5, muzzle_device_mass_g / 400.0)
    harmonic_score = max(0.0, min(20.0, base_score))

    sensitivity = {
        "charge": round(max(0.4, 1.7 - harmonic_score / 18.0), 2),
        "seating_depth": round(max(0.3, 1.4 - free_float_mm / 700.0), 2),
        "neck_tension": round(max(0.25, 1.15 - tuner_mass_g / 500.0), 2),
        "temperature": round(max(0.35, 1.2 - muzzle_device_mass_g / 2500.0), 2),
    }

    throat_erosion = chamber_comparison.get("throat_erosion_mm")
    if isinstance(throat_erosion, (int, float)) and throat_erosion > 0:
        sensitivity["seating_depth"] = round(
            min(
                2.2,
                sensitivity["seating_depth"] + min(0.35, float(throat_erosion) * 1.2),
            ),
            2,
        )
    freebore_delta = chamber_comparison.get("freebore_delta_mm")
    if isinstance(freebore_delta, (int, float)) and abs(float(freebore_delta)) >= 0.15:
        sensitivity["seating_depth"] = round(min(2.2, sensitivity["seating_depth"] + 0.12), 2)
    neck_clearance = chamber_comparison.get("neck_clearance_mm")
    if isinstance(neck_clearance, (int, float)):
        if float(neck_clearance) < 0.02:
            sensitivity["neck_tension"] = round(min(2.0, sensitivity["neck_tension"] + 0.25), 2)
        elif float(neck_clearance) < 0.05:
            sensitivity["neck_tension"] = round(min(2.0, sensitivity["neck_tension"] + 0.12), 2)

    bands = normalize_node_bands(harmonics.get("node_bands"))
    if not bands:
        center_a = round(max(15.0, effective_length_mm * 0.28), 1)
        center_b = round(max(center_a + 10.0, effective_length_mm * 0.72), 1)
        spread = max(7.5, 26.0 - harmonic_score)
        bands = [
            {
                "start_mm": round(max(0.0, center_a - spread / 2.0), 1),
                "end_mm": round(center_a + spread / 2.0, 1),
                "robustness": round(min(1.0, 0.45 + harmonic_score / 30.0), 2),
                "label": "node-a",
            },
            {
                "start_mm": round(max(0.0, center_b - spread / 2.0), 1),
                "end_mm": round(center_b + spread / 2.0, 1),
                "robustness": round(min(1.0, 0.4 + harmonic_score / 35.0), 2),
                "label": "node-b",
            },
        ]

    calibration_state = harmonics.get("calibration_state") or (
        "calibrated" if harmonics.get("node_bands") else "heuristic"
    )
    notes = []
    notes.append(f"Estimert grunnfrekvens {estimated_frequency_hz:.1f} Hz")
    notes.append(f"Estimat bygger på {barrel_profile} kontur og {support_type} støtte")
    notes.append(f"Innfesting tolkes som {attachment_type}")
    if has_muzzle_device:
        notes.append("Muzzle device er tatt med i modellen")
    if tuner_mass_g > 0:
        notes.append(f"Tuner på {tuner_position_mm:.0f} mm med {tuner_mass_g:.0f} g masse er medregnet")
    if barrel_torque_nm > 0:
        notes.append(f"Registrert pipemoment: {barrel_torque_nm:.1f} Nm")
    if return_to_zero:
        notes.append(f"Return-to-zero: {return_to_zero}")
    if attachment_type == "quick_change":
        notes.append("Quick-change system kan være mer følsomt for pipebytte og krever ofte ekstra verifisering")
    if chamber_comparison:
        notes.extend(chamber_comparison.get("notes") or [])
    if missing_required:
        notes.append("Datagrunnlaget er delvis generelt: mangler " + ", ".join(missing_required))

    required_score = sum(1 for ok in required_inputs.values() if ok)
    optional_score = sum(1 for ok in optional_inputs.values() if ok)
    completeness_ratio = (required_score + optional_score * 0.35) / (len(required_inputs) + len(optional_inputs) * 0.35)
    harmonics_confidence = (
        "high"
        if required_score >= 5 and completeness_ratio >= 0.8
        else "medium" if required_score >= 3 and completeness_ratio >= 0.55 else "low"
    )

    return {
        "version": "2.0",
        "rifle_id": rifle_id,
        "rifle_name": rifle_name,
        "barrel_name": barrel_name,
        "caliber_name": caliber_name,
        "selected_barrel_id": profile_details.get("selected_barrel_id"),
        "profile_scope": profile_scope,
        "barrel_attachment_type": attachment_type,
        "barrel_return_to_zero": return_to_zero,
        "barrel_torque_nm": round(barrel_torque_nm, 1) if barrel_torque_nm else 0.0,
        "harmonics_confidence": harmonics_confidence,
        "missing_required_inputs": missing_required,
        "estimated_inputs": estimated_inputs,
        "barrel_profile": barrel_profile,
        "barrel_length_mm": round(barrel_length_mm, 1),
        "effective_length_mm": round(effective_length_mm, 1),
        "estimated_frequency_hz": round(estimated_frequency_hz, 1),
        "period_ms": round(period_ms, 2),
        "harmonic_score": round(harmonic_score, 1),
        "stability_tier": (
            "very-stable"
            if harmonic_score >= 16
            else ("stable" if harmonic_score >= 12 else "moderate" if harmonic_score >= 8 else "sensitive")
        ),
        "support_type": support_type,
        "action_stiffness": action_stiffness,
        "free_float_length_mm": round(free_float_mm, 1),
        "tuner_mass_g": round(tuner_mass_g, 1),
        "tuner_position_mm": round(tuner_position_mm, 1),
        "muzzle_device_mass_g": round(muzzle_device_mass_g, 1),
        "muzzle_device_length_mm": round(muzzle_device_length_mm, 1),
        "has_muzzle_device": has_muzzle_device,
        "node_bands": bands,
        "sensitivity": sensitivity,
        "chamber_comparison": chamber_comparison,
        "calibration_state": calibration_state,
        "notes": notes,
        "input": {
            "muzzle_diameter_mm": round(muzzle_dia, 2),
            "breech_diameter_mm": round(breech_dia, 2),
            "barrel_weight_g": round(barrel_weight_g, 1),
        },
    }


def build_harmonics_html(rifle: Dict[str, Any], profile_details: Dict[str, Any]) -> str:
    summary = calculate_harmonics_profile(rifle, profile_details)
    bands_html = "".join(
        f"<li>{band['label']}: {band['start_mm']:.1f} - {band['end_mm']:.1f} mm "
        f"(robusthet {band['robustness']:.2f})</li>"
        for band in summary["node_bands"]
    )
    note_html = "".join(f"<li>{note}</li>" for note in summary["notes"])
    sensitivity = summary["sensitivity"]
    comparison = summary.get("chamber_comparison") or {}
    comparison_notes = "".join(f"<li>{note}</li>" for note in (comparison.get("notes") or []))
    return f"""
    <h3>Harmonisk analyse</h3>
    <ul>
        <li><b>Rifle:</b> {summary['rifle_name']} (ID {summary['rifle_id'] if summary['rifle_id'] is not None else '-'})</li>
        <li><b>Pipe/Løp:</b> {summary.get('barrel_name', 'standard')}</li>
        <li><b>Innfesting:</b> {summary.get('barrel_attachment_type', 'unknown')}</li>
        <li><b>Datakvalitet:</b> {summary.get('harmonics_confidence', 'low')}</li>
        <li><b>Scope:</b> {summary['profile_scope']}</li>
        <li><b>Kontur:</b> {summary['barrel_profile']}</li>
        <li><b>Effektiv lengde:</b> {summary['effective_length_mm']:.1f} mm</li>
        <li><b>Estimert frekvens:</b> {summary['estimated_frequency_hz']:.1f} Hz</li>
        <li><b>Periode:</b> {summary['period_ms']:.2f} ms</li>
        <li><b>Harmonikk-score:</b> {summary['harmonic_score']:.1f} / 20</li>
        <li><b>Stabilitet:</b> {summary['stability_tier']}</li>
        <li><b>Kalibrering:</b> {summary['calibration_state']}</li>
    </ul>
    <h4>Node-bånd</h4>
    <ul>{bands_html or '<li>Ingen node-bånd tilgjengelig ennå.</li>'}</ul>
    <h4>Følsomhet</h4>
    <ul>
        <li>Kruttmengde: {sensitivity['charge']:.2f}</li>
        <li>Settedybde: {sensitivity['seating_depth']:.2f}</li>
        <li>Neck tension: {sensitivity['neck_tension']:.2f}</li>
        <li>Temperatur: {sensitivity['temperature']:.2f}</li>
    </ul>
    <h4>Patron/Kammer-sammenligning</h4>
    <ul>{comparison_notes or '<li>Ingen standard-/kammer-sammenligning tilgjengelig ennå.</li>'}</ul>
    <h4>Hva modellen tar hensyn til</h4>
    <ul>{note_html}</ul>
    """
