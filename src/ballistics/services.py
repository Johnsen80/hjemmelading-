from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from ..database.database import get_database
from ..modules.ballistics_engine import get_ballistics_engine
from ..utils.advanced_ballistics import AdvancedBallisticsEngine, AtmosphericConditions
from ..utils.cartridge_standard_support import get_max_pressure_psi_for_caliber
from ..utils.drag_models import preferred_drag_model, resolve_drag_choice
from ..utils.environment import BallisticEnvironment
from ..utils.internal_ballistics import build_internal_ballistics_summary

# All internal ballistics should use ballistics_layer
from ..utils.rifle_harmonics import calculate_harmonics_profile
from ..utils.scientific_quality import build_input_quality_summary
from ..utils.unit_preferences import (
    format_group_size_mm,
    format_length_mm,
    format_pressure_psi,
    format_pressure_range_psi,
    format_velocity_fps,
    format_weight_grains,
)


@dataclass
class LoadAnalysisRequest:
    rifle_id: int
    bullet_id: int
    powder_id: int
    charge_weight_gr: float
    coal_mm: float
    primer_id: int | None = None
    cbto_mm: float | None = None
    temperature_c: float = 15.0
    pressure_hpa: float = 1013.25
    humidity_percent: float = 50.0
    altitude_m: float = 0.0
    wind_speed_mps: float = 0.0
    wind_dir_deg: float = 90.0
    case_id: int | None = None
    brass_batch_id: int | None = None
    bullet_lot_id: int | None = None
    powder_lot_id: int | None = None
    primer_lot_id: int | None = None
    barrel_id: str | None = None
    ammo_profile_id: int | None = None
    usage_profile: str = "precision"
    target_distance_m: float | None = None
    zero_distance_m: float | None = None
    subsonic_mode: bool = False
    rifle_overrides: dict[str, Any] | None = None
    barrel_overrides: dict[str, Any] | None = None
    bullet_overrides: dict[str, Any] | None = None
    powder_overrides: dict[str, Any] | None = None
    primer_overrides: dict[str, Any] | None = None
    case_overrides: dict[str, Any] | None = None


def compute_clicks(delta_angle: float, click_value: float) -> int:
    """Compute the number of clicks needed for a given angle adjustment."""
    if not click_value:
        return 0
    return round(delta_angle / click_value)


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    numeric = _coerce_float(value)
    if numeric is None:
        return None
    return int(numeric)


def _safe_json_loads(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _clean_label(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _contains_any(text: str, *tokens: str) -> bool:
    haystack = f" {str(text or '').strip().lower()} "
    return any(token.lower() in haystack for token in tokens if token)


def _merge_first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _merge_user_overrides(
    base: dict[str, Any] | None, overrides: dict[str, Any] | None
) -> dict[str, Any]:
    merged = dict(base or {})
    if not isinstance(overrides, dict):
        return merged
    for key, value in overrides.items():
        if value in (None, "", [], {}):
            continue
        merged[key] = value
    return merged


def _parse_twist_inches(value: Any) -> float | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if ":" in text:
        text = text.split(":", 1)[1]
    for prefix in ("1/", "1-", "1 "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    text = text.replace("twist", "").replace("in", "").replace('"', "").strip()
    try:
        twist = float(text)
    except Exception:
        return None
    return twist if twist > 0 else None


def _infer_bullet_diameter_mm(
    bullet: dict[str, Any], caliber_text: str
) -> float | None:
    diameter = _coerce_float(bullet.get("diameter_mm"))
    if diameter and diameter > 0:
        return diameter

    text = str(caliber_text or "").strip().lower()
    if not text:
        return None

    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if not match:
        return None

    try:
        value = float(match.group(1).replace(",", "."))
    except Exception:
        return None

    if text.startswith(".") or value < 1.5:
        return value * 25.4
    return value


def _estimate_gyroscopic_stability(
    *,
    bullet: dict[str, Any],
    caliber_text: str,
    twist_inches: float | None,
    muzzle_velocity_fps: float | None,
    environment: BallisticEnvironment,
) -> dict[str, Any]:
    missing_inputs: list[str] = []
    if not twist_inches or twist_inches <= 0:
        missing_inputs.append("twist")

    weight_gr = _coerce_float(bullet.get("weight_grains", bullet.get("weight")))
    length_mm = _coerce_float(bullet.get("length_mm"))
    diameter_mm = _infer_bullet_diameter_mm(bullet, caliber_text)
    if not weight_gr:
        missing_inputs.append("kulevekt")
    if not length_mm:
        missing_inputs.append("kulelengde")
    if not diameter_mm:
        missing_inputs.append("kulediameter / kaliber")
    if missing_inputs:
        return {"missing_inputs": missing_inputs}

    diameter_in = float(diameter_mm) / 25.4
    length_in = float(length_mm) / 25.4
    if diameter_in <= 0 or length_in <= 0:
        return {"missing_inputs": ["gyldig kulelengde og diameter"]}

    length_calibers = length_in / diameter_in
    twist_calibers = float(twist_inches) / diameter_in
    if length_calibers <= 0 or twist_calibers <= 0:
        return {"missing_inputs": ["gyldig twist og kulegeometri"]}

    velocity = max(float(muzzle_velocity_fps or 2800.0), 500.0)
    temp_f = float(environment.temperature_c) * 9.0 / 5.0 + 32.0
    pressure_inhg = float(environment.pressure_hpa) * 0.0295299831

    try:
        sg = (30.0 * float(weight_gr)) / (
            (twist_calibers**2)
            * (diameter_in**3)
            * length_calibers
            * (1.0 + length_calibers**2)
        )
        sg *= (velocity / 2800.0) ** (1.0 / 3.0)
        sg *= ((temp_f + 459.67) / (59.0 + 459.67)) * (29.92 / pressure_inhg)
    except Exception:
        return {"missing_inputs": ["stabilitetsberegning kunne ikke fullfores"]}

    if sg >= 1.5:
        tier = "god stabilitet"
    elif sg >= 1.3:
        tier = "brukbar stabilitet"
    elif sg >= 1.0:
        tier = "marginal stabilitet"
    else:
        tier = "ustabil / hoy risiko"

    return {
        "sg": sg,
        "tier": tier,
        "diameter_mm": diameter_mm,
        "length_mm": length_mm,
        "velocity_fps": velocity,
    }


def _estimate_greenhill_twist_inches(
    *,
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
    try:
        twist_inches = (constant * (diameter_in**2)) / length_in
    except Exception:
        return None
    return twist_inches if twist_inches > 0 else None


def _resolve_bullet_profile(bullet: dict[str, Any]) -> dict[str, Any]:
    bullet = dict(bullet or {})
    profile = _safe_json_loads(bullet.get("profile_json"))
    raw = _safe_json_loads(bullet.get("raw_json"))

    name_bits = " ".join(
        str(part or "").strip()
        for part in (
            bullet.get("manufacturer"),
            bullet.get("name"),
            raw.get("mname"),
            raw.get("pname"),
            raw.get("gUBCS"),
            raw.get("descr"),
        )
        if str(part or "").strip()
    ).lower()

    tail_type = _merge_first_nonempty(
        bullet.get("base_type"),
        profile.get("tail_type"),
        raw.get("gtailtype"),
    )
    base_type = None
    if isinstance(tail_type, (int, float)) and float(tail_type) > 0:
        base_type = "boat_tail"
    elif _contains_any(
        name_bits, " hpbt", "bt ", " boat tail", " bthp", "btsp", "vld", "lrbt"
    ):
        base_type = "boat_tail"
    elif _contains_any(
        name_bits, " flat base", " fb ", " fbhp", "fbhp", "rn", "round nose"
    ):
        base_type = "flat_base"

    tip_type = None
    if _contains_any(
        name_bits,
        " polymer",
        " ballistic tip",
        "v-max",
        "accutip",
        "sst",
        "tipped",
        "tip",
    ):
        tip_type = "polymer_tip"
    elif _contains_any(
        name_bits, " hollow point", " hp", " hpbt", " bthp", " matchburner"
    ):
        tip_type = "hollow_point"
    elif _contains_any(name_bits, " soft point", " sp", " jsp"):
        tip_type = "soft_point"
    elif _contains_any(name_bits, " round nose", " rn"):
        tip_type = "round_nose"
    elif _contains_any(name_bits, " fmj", " full metal jacket"):
        tip_type = "fmj"

    construction_type = None
    if _contains_any(
        name_bits, "mono", " monolithic", "tsx", "ttsx", "cx", "cutting edge", "copper"
    ):
        construction_type = "monolithic"
    elif _contains_any(name_bits, "bonded", " interbond", " accubond", "oryx"):
        construction_type = "bonded"
    elif _contains_any(name_bits, " fmj", " full metal jacket"):
        construction_type = "fmj"
    elif _contains_any(
        name_bits, " match", " smk", " scenar", "berger", " hybrid", " rdf", "eld-m"
    ):
        construction_type = "match"
    elif _contains_any(name_bits, " soft point", "sp", "round nose", "rn", "hunting"):
        construction_type = "hunting_jacketed"

    shape_family = None
    if _contains_any(name_bits, "vld", "hybrid", "eld", "rdf"):
        shape_family = "vld"
    elif _contains_any(name_bits, " round nose", " rn"):
        shape_family = "round_nose"
    elif _contains_any(name_bits, " wadcutter", "wc", "swc"):
        shape_family = "wadcutter"
    elif _contains_any(name_bits, " spitzer", "bt", "hpbt", "bthp", "sp"):
        shape_family = "spitzer"

    intended_use = None
    if _contains_any(name_bits, " varmint", " vmax", " v-max", "tnt", "blitz"):
        intended_use = "varmint"
    elif _contains_any(
        name_bits,
        " hunting",
        " interlock",
        " accubond",
        " tsx",
        "ttsx",
        "oryx",
        "ecostrike",
        "deadtough",
    ):
        intended_use = "hunting"
    elif _contains_any(
        name_bits, " match", " smk", " scenar", " hybrid", "eld-m", "rdf", "otm"
    ):
        intended_use = "match"
    elif _contains_any(name_bits, " sub-x", " subx", " subsonic"):
        intended_use = "subsonic"

    diameter_mm = _merge_first_nonempty(
        _coerce_float(bullet.get("diameter_mm")),
        _coerce_float(profile.get("diameter_mm")),
        _coerce_float(raw.get("gdia")),
    )
    length_mm = _merge_first_nonempty(
        _coerce_float(bullet.get("length_mm")),
        _coerce_float(profile.get("length_mm")),
        _coerce_float(raw.get("glen")),
    )

    confidence = "high"
    if not length_mm or not diameter_mm:
        confidence = "medium"
    if not any((base_type, tip_type, construction_type, shape_family, intended_use)):
        confidence = "low" if confidence == "medium" else "medium"

    summary_bits = [
        bit
        for bit in (
            base_type.replace("_", " ") if base_type else None,
            tip_type.replace("_", " ") if tip_type else None,
            construction_type.replace("_", " ") if construction_type else None,
            intended_use.replace("_", " ") if intended_use else None,
        )
        if bit
    ]

    return {
        **bullet,
        "diameter_mm": diameter_mm,
        "length_mm": length_mm,
        "base_type": base_type,
        "tip_type": tip_type,
        "construction_type": construction_type,
        "shape_family": shape_family,
        "intended_use": intended_use,
        "geometry_confidence": confidence,
        "geometry_summary": ", ".join(summary_bits) if summary_bits else None,
        "profile_json_dict": profile,
        "raw_json_dict": raw,
    }


def _build_projectile_terminal_profile(
    bullet: dict[str, Any] | None,
    usage_profile: str,
) -> dict[str, Any]:
    bullet = dict(bullet or {})
    usage = str(usage_profile or "precision").strip().lower()
    profile = _safe_json_loads(bullet.get("profile_json"))
    raw = _safe_json_loads(bullet.get("raw_json"))

    construction = str(bullet.get("construction_type") or "").strip().lower()
    tip_type = str(bullet.get("tip_type") or "").strip().lower()
    intended_use = str(bullet.get("intended_use") or "").strip().lower()
    bullet_type = (
        str(
            _merge_first_nonempty(
                bullet.get("bullet_type"),
                bullet.get("type"),
                profile.get("bullet_type"),
                raw.get("type"),
            )
            or ""
        )
        .strip()
        .lower()
    )

    minimum_expansion_fps = _coerce_float(
        _merge_first_nonempty(
            bullet.get("minimum_expansion_fps"),
            bullet.get("min_expansion_fps"),
            profile.get("minimum_expansion_fps"),
            profile.get("min_expansion_fps"),
            raw.get("minimum_expansion_fps"),
            raw.get("min_expansion_fps"),
        )
    )
    preferred_impact_min_fps = _coerce_float(
        _merge_first_nonempty(
            bullet.get("preferred_impact_min_fps"),
            profile.get("preferred_impact_min_fps"),
            raw.get("preferred_impact_min_fps"),
        )
    )
    preferred_impact_max_fps = _coerce_float(
        _merge_first_nonempty(
            bullet.get("preferred_impact_max_fps"),
            profile.get("preferred_impact_max_fps"),
            raw.get("preferred_impact_max_fps"),
        )
    )

    min_energy_ftlbs = 0.0
    if usage == "hunting_small":
        min_energy_ftlbs = 500.0
    elif usage == "hunting_medium":
        min_energy_ftlbs = 1000.0
    elif usage == "hunting_large":
        min_energy_ftlbs = 1500.0
    elif usage == "long_range_hunting":
        min_energy_ftlbs = 1200.0

    notes: list[str] = []
    confidence = "medium"

    if minimum_expansion_fps is None:
        if construction == "monolithic" or _contains_any(
            bullet_type, "mono", "copper", "tsx", "ttsx", "cx"
        ):
            minimum_expansion_fps = 1900.0
            preferred_impact_min_fps = preferred_impact_min_fps or 2000.0
            notes.append(
                "Monolithic bullets often need higher impact velocity for reliable expansion."
            )
        elif construction == "bonded" or _contains_any(
            bullet_type, "bonded", "accubond", "interbond", "oryx"
        ):
            minimum_expansion_fps = 1700.0
            preferred_impact_min_fps = preferred_impact_min_fps or 1800.0
            notes.append(
                "Bonded hunting bullets usually keep working lower than monolithic designs,"
                " but still benefit from solid impact speed."
            )
        elif tip_type == "polymer_tip" or _contains_any(
            bullet_type, "sst", "ballistic tip", "tipped", "v-max", "vmax"
        ):
            _hunting_usage = {"hunting_small", "hunting_medium", "long_range_hunting"}
            minimum_expansion_fps = 1600.0 if usage in _hunting_usage else 1800.0
            preferred_impact_min_fps = preferred_impact_min_fps or (
                1700.0 if usage == "long_range_hunting" else 1800.0
            )
            notes.append(
                "Polymer-tipped bullets often start expansion earlier than FMJ or pure match profiles."
            )
        elif (
            tip_type == "soft_point"
            or construction == "hunting_jacketed"
            or intended_use == "hunting"
        ):
            _hunting_usage = {"hunting_small", "hunting_medium", "long_range_hunting"}
            minimum_expansion_fps = 1600.0 if usage in _hunting_usage else 1700.0
            preferred_impact_min_fps = preferred_impact_min_fps or 1750.0
            notes.append(
                "Traditional hunting bullets usually tolerate moderate impact speeds well."
            )
        elif intended_use == "varmint" or _contains_any(
            bullet_type, "varmint", "blitz", "tnt"
        ):
            minimum_expansion_fps = 2200.0
            preferred_impact_min_fps = preferred_impact_min_fps or 2400.0
            preferred_impact_max_fps = preferred_impact_max_fps or 3400.0
            notes.append(
                "Varmint bullets typically need high impact speed and can be very aggressive at close range."
            )
        elif construction == "match" or _contains_any(
            bullet_type, "match", "otm", "smk", "eld-m", "rdf", "scenar"
        ):
            minimum_expansion_fps = 1800.0
            preferred_impact_min_fps = preferred_impact_min_fps or 1900.0
            notes.append(
                "Match bullets can still create damage, but controlled hunting performance is less predictable."
            )
        elif (
            construction == "fmj"
            or tip_type == "fmj"
            or _contains_any(bullet_type, "fmj", "full metal jacket")
        ):
            minimum_expansion_fps = 2000.0
            notes.append(
                "FMJ bullets are usually poor choices when reliable expansion is the goal."
            )

    if preferred_impact_min_fps is None and minimum_expansion_fps is not None:
        preferred_impact_min_fps = minimum_expansion_fps + 100.0
    if preferred_impact_max_fps is None and intended_use == "varmint":
        preferred_impact_max_fps = 3400.0

    if minimum_expansion_fps is not None:
        confidence = (
            "high"
            if bullet.get("construction_type")
            or bullet.get("tip_type")
            or bullet.get("bullet_type")
            else "medium"
        )
    else:
        confidence = "low"

    role_bits = [
        str(part).replace("_", " ")
        for part in (
            construction or None,
            tip_type or None,
            intended_use or None,
        )
        if part
    ]
    profile_summary = ", ".join(role_bits) if role_bits else None

    return {
        "construction_type": construction or None,
        "tip_type": tip_type or None,
        "intended_use": intended_use or None,
        "bullet_type": bullet_type or None,
        "minimum_expansion_fps": minimum_expansion_fps,
        "preferred_impact_min_fps": preferred_impact_min_fps,
        "preferred_impact_max_fps": preferred_impact_max_fps,
        "minimum_energy_ftlbs": min_energy_ftlbs,
        "confidence": confidence,
        "profile_summary": profile_summary,
        "notes": notes,
    }


def _build_bullet_geometry_summary(
    bullet: dict[str, Any], twist_inches: float | None
) -> dict[str, Any]:
    bullet = bullet or {}
    missing: list[str] = []
    if not _coerce_float(bullet.get("length_mm")):
        missing.append("kulelengde")
    if not _coerce_float(bullet.get("diameter_mm")):
        missing.append("kulediameter")
    if not bullet.get("base_type"):
        missing.append("base-type")
    if not bullet.get("tip_type"):
        missing.append("tip-type")
    if not bullet.get("construction_type"):
        missing.append("konstruksjon")

    notes: list[str] = []
    if bullet.get("length_mm"):
        notes.append(f"Kulelengde {format_length_mm(float(bullet['length_mm']))}.")
    if bullet.get("diameter_mm"):
        notes.append(f"Diameter {format_length_mm(float(bullet['diameter_mm']))}.")
    if twist_inches:
        notes.append(f"Twist 1:{twist_inches:.1f}.")
    if bullet.get("base_type"):
        notes.append(f"Base: {str(bullet['base_type']).replace('_', ' ')}.")
    if bullet.get("tip_type"):
        notes.append(f"Tupp: {str(bullet['tip_type']).replace('_', ' ')}.")
    if bullet.get("construction_type"):
        notes.append(
            f"Konstruksjon: {str(bullet['construction_type']).replace('_', ' ')}."
        )
    if str(bullet.get("shape_family") or "").strip().lower() == "vld":
        notes.append("VLD-/hybridprofil tilsier ofte hoy seating-folsomhet.")
    if str(bullet.get("construction_type") or "").strip().lower() == "monolithic":
        notes.append(
            "Monolittiske kuler er ofte lengre enn vekten tilsier og krever ekstra kontroll pa seating og stabilitet."
        )

    recommended_twist = _estimate_greenhill_twist_inches(
        diameter_mm=_coerce_float(bullet.get("diameter_mm")),
        length_mm=_coerce_float(bullet.get("length_mm")),
    )
    twist_assessment = "unknown"
    if recommended_twist is not None:
        notes.append(
            f"Enkel Greenhill-twist peker mot omtrent 1:{recommended_twist:.1f}."
        )
        if twist_inches:
            if twist_inches <= recommended_twist + 0.2:
                twist_assessment = "compatible"
                notes.append(
                    "Valgt twist ser ut til a vaere i riktig omrade for denne kulelengden."
                )
            elif twist_inches <= recommended_twist + 1.0:
                twist_assessment = "borderline"
                notes.append(
                    "Valgt twist ser brukbar ut, men gir ikke stor margin for temperatur- eller fartstap."
                )
            else:
                twist_assessment = "slow_for_bullet"
                notes.append(
                    "Valgt twist virker langsom for kulelengden og bor verifiseres ekstra med stabilitetsdata."
                )

    return {
        "length_mm": _coerce_float(bullet.get("length_mm")),
        "diameter_mm": _coerce_float(bullet.get("diameter_mm")),
        "base_type": bullet.get("base_type"),
        "tip_type": bullet.get("tip_type"),
        "construction_type": bullet.get("construction_type"),
        "shape_family": bullet.get("shape_family"),
        "intended_use": bullet.get("intended_use"),
        "geometry_confidence": bullet.get("geometry_confidence"),
        "recommended_twist_in": recommended_twist,
        "twist_assessment": twist_assessment,
        "missing_fields": missing,
        "notes": notes,
    }


def _build_primer_profile_summary(
    primer: dict[str, Any] | None, temperature_c: float | None = None
) -> dict[str, Any]:
    primer = dict(primer or {})
    family = str(primer.get("primer_family") or "").strip().lower() or None
    ignition = str(primer.get("ignition_strength_class") or "").strip().lower() or None
    pressure_class = (
        str(primer.get("pressure_tolerance_class") or "").strip().lower() or None
    )
    hardness = str(primer.get("cup_hardness_class") or "").strip().lower() or None
    cold_weather = (
        str(primer.get("cold_weather_suitability") or "").strip().lower() or None
    )
    pressure_min = _coerce_float(primer.get("recommended_pressure_min_psi"))
    pressure_max = _coerce_float(primer.get("recommended_pressure_max_psi"))

    notes: list[str] = []
    if family:
        notes.append(f"Tennhettefamilie: {family.replace('_', ' ')}.")
    if ignition:
        notes.append(f"Tenningsstyrke: {ignition.replace('_', ' ')}.")
    if hardness:
        notes.append(f"Kopphardhet: {hardness.replace('_', ' ')}.")
    if pressure_min is not None and pressure_max is not None:
        notes.append(
            f"Anbefalt trykkvindu: {format_pressure_range_psi(pressure_min, pressure_max)}."
        )
    elif pressure_max is not None:
        notes.append(f"Anbefalt maks trykk: {format_pressure_psi(pressure_max)}.")
    if temperature_c is not None and cold_weather:
        if temperature_c <= 0 and cold_weather in {"poor", "limited"}:
            notes.append("Kuldeegenskapene virker begrensede for dagens temperatur.")
        elif temperature_c <= 5 and cold_weather == "good":
            notes.append("Kuldeegenskapene passer godt til dagens temperatur.")

    return {
        "family": family,
        "ignition_strength_class": ignition,
        "pressure_tolerance_class": pressure_class,
        "cup_hardness_class": hardness,
        "cold_weather_suitability": cold_weather,
        "recommended_pressure_min_psi": pressure_min,
        "recommended_pressure_max_psi": pressure_max,
        "notes": notes,
    }


def _apply_bullet_harmonic_context(
    harmonics: dict[str, Any] | None,
    bullet: dict[str, Any] | None,
    *,
    twist_inches: float | None = None,
) -> dict[str, Any]:
    summary = dict(harmonics or {})
    bullet = bullet or {}
    sensitivity = dict(summary.get("sensitivity") or {})
    notes = list(summary.get("notes") or [])

    shape_family = str(bullet.get("shape_family") or "").strip().lower()
    construction = str(bullet.get("construction_type") or "").strip().lower()
    length_mm = _coerce_float(bullet.get("length_mm"))
    diameter_mm = _coerce_float(bullet.get("diameter_mm"))

    length_calibers = None
    if length_mm and diameter_mm and diameter_mm > 0:
        try:
            length_calibers = float(length_mm) / float(diameter_mm)
        except Exception:
            length_calibers = None

    if shape_family == "vld":
        sensitivity["seating_depth"] = round(
            min(2.2, (_coerce_float(sensitivity.get("seating_depth")) or 1.0) + 0.18), 2
        )
        notes.append(
            "VLD-/hybridkule: seating-endringer kan flytte ladningen raskt inn eller ut av node."
        )

    if construction == "monolithic":
        sensitivity["seating_depth"] = round(
            min(2.2, (_coerce_float(sensitivity.get("seating_depth")) or 1.0) + 0.10), 2
        )
        sensitivity["charge"] = round(
            min(2.0, (_coerce_float(sensitivity.get("charge")) or 1.0) + 0.05), 2
        )
        notes.append(
            "Monolittisk kule: lengde og bæreflate tilsier konservative seating- og charge-steg."
        )

    if length_calibers and length_calibers >= 4.5:
        sensitivity["seating_depth"] = round(
            min(2.2, (_coerce_float(sensitivity.get("seating_depth")) or 1.0) + 0.12), 2
        )
        notes.append(
            f"Lang kule ({length_calibers:.2f} kalibre): node-fit blir mer følsom for seating og twist."
        )

    if twist_inches and length_mm and diameter_mm:
        recommended_twist = _estimate_greenhill_twist_inches(
            diameter_mm=diameter_mm,
            length_mm=length_mm,
        )
        if recommended_twist and twist_inches > recommended_twist + 1.0:
            sensitivity["seating_depth"] = round(
                min(
                    2.2, (_coerce_float(sensitivity.get("seating_depth")) or 1.0) + 0.08
                ),
                2,
            )
            notes.append(
                "Twist ser treg ut for kulelengden: node og seating bør verifiseres ekstra nøye."
            )

    summary["sensitivity"] = sensitivity
    summary["notes"] = notes
    return summary


def _build_node_fit_summary(
    harmonics: dict[str, Any] | None,
    bullet: dict[str, Any] | None,
    observations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    harmonics = harmonics or {}
    bullet = bullet or {}
    observations = observations or {}
    observation_summary = (
        observations.get("summary")
        if isinstance(observations.get("summary"), dict)
        else {}
    )
    score = _coerce_float(harmonics.get("harmonic_score")) or 0.0
    confidence = str(harmonics.get("harmonics_confidence") or "").strip() or "low"
    seating_sens = _coerce_float(
        (harmonics.get("sensitivity") or {}).get("seating_depth")
    )
    charge_sens = _coerce_float((harmonics.get("sensitivity") or {}).get("charge"))

    level = "ok" if score >= 14 else "warning" if score >= 10 else "info"
    title = (
        "Node-fit ser lovende"
        if score >= 14
        else (
            "Node-fit trenger verifisering"
            if score >= 10
            else "Node-fit er forelopig svak"
        )
    )
    message = (
        "Modellen peker mot et brukbart nodeomrade."
        if score >= 14
        else (
            "Det finnes signaler, men ladningen bor verifiseres med kort sweep."
            if score >= 10
            else "Bruk modellen som grovt startpunkt og jobb systematisk med charge/seating."
        )
    )

    checks: list[str] = []
    if seating_sens is not None:
        checks.append(f"Seating-folsomhet {seating_sens:.2f}.")
    if charge_sens is not None:
        checks.append(f"Charge-folsomhet {charge_sens:.2f}.")
    if confidence:
        checks.append(f"Harmonikk-confidence {confidence}.")
    chrono_count = int(observation_summary.get("chrono_count") or 0)
    accuracy_count = int(observation_summary.get("accuracy_count") or 0)
    pressure_events = int(observation_summary.get("pressure_event_count") or 0)
    best_group_mm = _coerce_float(observation_summary.get("best_group_mm"))
    avg_group_mm = _coerce_float(observation_summary.get("avg_group_mm"))
    if chrono_count:
        checks.append(f"{chrono_count} kronografokter koblet til denne ladningen.")
    if accuracy_count:
        checks.append(f"{accuracy_count} presisjonstester koblet til denne ladningen.")
    if best_group_mm is not None:
        checks.append(
            f"Beste registrerte gruppe {format_group_size_mm(best_group_mm)}."
        )
    if avg_group_mm is not None:
        checks.append(
            f"Gjennomsnittlig registrert gruppe {format_group_size_mm(avg_group_mm)}."
        )
    if pressure_events:
        checks.append(
            f"{pressure_events} registrerte trykktegn bor tas med i nodevurderingen."
        )
    for note in (harmonics.get("notes") or [])[:3]:
        note_text = str(note or "").strip()
        if note_text:
            checks.append(note_text)
    if bullet.get("shape_family") == "vld":
        checks.append("VLD-/hybridkule tilsier sma seating-endringer rundt node.")
    if bullet.get("construction_type") == "monolithic":
        checks.append("Monolittisk kule bor verifiseres med konservative steg.")

    if chrono_count >= 2 and accuracy_count >= 1 and pressure_events == 0:
        if level == "info":
            level = "warning"
        message += " Historiske data gir bedre grunnlag for å stole på nodevurderingen."
    if avg_group_mm is not None and avg_group_mm <= 20.0 and pressure_events == 0:
        level = "ok" if score >= 10 else level
        title = "Node-fit ser bedre ut med historiske data" if score >= 10 else title
    if pressure_events:
        if level != "critical":
            level = "warning"
        title = "Node-fit må ses opp mot trykktegn"
        message = "Det finnes trykkobservasjoner i historikken. Verifiser charge-vindu konservativt."

    return {
        "level": level,
        "title": title,
        "message": message,
        "checks": checks,
    }


def _summarize_observation_history(
    observations: dict[str, Any] | None,
) -> dict[str, Any]:
    observations = observations or {}
    chrono_rows = list(observations.get("chronograph_sessions") or [])
    accuracy_rows = list(observations.get("accuracy_tests") or [])
    pressure_rows = list(observations.get("pressure_signs") or [])

    best_group_mm_values: list[float] = []
    avg_group_mm_values: list[float] = []
    for row in accuracy_rows:
        best_group = _coerce_float(row.get("best_group_mm"))
        avg_group = _coerce_float(
            row.get("average_group_size_mm") or row.get("avg_group_mm")
        )
        if best_group is not None:
            best_group_mm_values.append(best_group)
        if avg_group is not None:
            avg_group_mm_values.append(avg_group)

    pressure_events = 0
    for row in pressure_rows:
        if any(
            row.get(key) not in (None, "", 0, "0", False)
            for key in (
                "flattened_primers",
                "sticky_bolt",
                "ejector_marks",
                "case_head_expansion",
                "notes",
                "pressure_level",
                "primer_image_path",
                "primer_image_observation",
            )
        ):
            pressure_events += 1

    return {
        "chrono_count": len(chrono_rows),
        "accuracy_count": len(accuracy_rows),
        "pressure_event_count": pressure_events,
        "best_group_mm": min(best_group_mm_values) if best_group_mm_values else None,
        "avg_group_mm": (
            (sum(avg_group_mm_values) / len(avg_group_mm_values))
            if avg_group_mm_values
            else None
        ),
    }


def _summarize_pressure_risk(
    result: dict[str, Any], max_pressure_psi: float | None
) -> dict[str, Any]:
    safety = _coerce_float(result.get("safety_margin_percent"))
    peak = _coerce_float(result.get("peak_pressure_psi"))
    maximum = max_pressure_psi or _coerce_float(result.get("max_pressure_psi"))
    display_margin = safety
    if peak is not None and maximum:
        try:
            display_margin = (float(maximum) - float(peak)) / float(maximum) * 100.0
        except Exception:
            display_margin = safety

    warnings = [str(w) for w in (result.get("warnings") or []) if w]
    spike_terms = (
        "spike",
        "into lands",
        "close to lands",
        "compressed load",
        "neck tension",
        "high pressure",
        "danger:",
    )
    spike_warnings = [
        warning
        for warning in warnings
        if any(term in warning.lower() for term in spike_terms)
    ]
    if spike_warnings:
        return {
            "level": "critical",
            "title": "Pressure spike risk",
            "message": spike_warnings[0],
        }
    if display_margin is None:
        return {
            "level": "unknown",
            "title": "Pressure risk unavailable",
            "message": "Manglende trykkdata. Verifiser komponenter og simulering før testing.",
        }
    if display_margin < 10:
        return {
            "level": "critical",
            "title": "High pressure risk",
            "message": f"Kun {display_margin:.1f}% margin til maks trykk.",
        }
    if display_margin < 15:
        return {
            "level": "warning",
            "title": "Pressure near max",
            "message": f"{display_margin:.1f}% margin gjenstar. Kjor konservativ verifisering.",
        }
    return {
        "level": "ok",
        "title": "Pressure margin healthy",
        "message": f"{display_margin:.1f}% margin til maks trykk.",
    }


def _summarize_stability_advisor(
    *,
    stability: dict[str, Any] | None,
    result: dict[str, Any] | None,
    subsonic_mode: bool,
    twist_inches: float | None,
    bullet: dict[str, Any] | None,
    barrel_details: dict[str, Any] | None,
    rifle_data: dict[str, Any] | None,
) -> dict[str, Any]:
    stability = stability or {}
    bullet = bullet or {}
    barrel_details = barrel_details or {}
    rifle_data = rifle_data or {}

    if stability.get("missing_inputs"):
        missing = ", ".join(str(item) for item in stability.get("missing_inputs") or [])
        return {
            "level": "unknown",
            "title": "Stability data incomplete",
            "message": "Legg inn twist, kulelengde og kulegeometri for et mer presist stabilitetsestimat.",
            "checks": [f"Mangler data: {missing}"],
        }

    try:
        sg = float(stability.get("sg"))
    except Exception:
        return {
            "level": "unknown",
            "title": "Stability unavailable",
            "message": "Stabilitet kunne ikke vurderes fra dagens data.",
            "checks": [],
        }

    velocity_fps = _coerce_float(
        (result or {}).get("muzzle_velocity_fps", stability.get("velocity_fps"))
    )
    muzzle_device = (
        str(
            barrel_details.get("muzzle_device_type")
            or barrel_details.get("muzzle_device")
            or rifle_data.get("muzzle_device")
            or ""
        )
        .strip()
        .lower()
    )
    has_suppressor = any(
        token in muzzle_device for token in ("suppressor", "moderator", "demper")
    )

    checks: list[str] = []
    level = "ok"
    title = "Stability looks healthy"
    message = f"Sg {sg:.2f} tyder pa god stabilitet i dagens oppsett."

    if sg < 1.0:
        level = "critical"
        title = "High tumble risk"
        message = f"Sg {sg:.2f} er under 1.0. Kula kan vaere ustabil ut av munningen."
    elif subsonic_mode and sg < 1.15:
        level = "critical"
        title = "Marginal subsonic stability"
        message = f"Sg {sg:.2f} er for lavt til komfortabel subsonisk bruk."
    elif sg < 1.3:
        level = "warning"
        title = "Marginal stability"
        message = f"Sg {sg:.2f} er marginalt. Verifiser med grupper og yaw-tegn."
    elif sg < 1.5:
        level = "warning"
        title = "Usable but not roomy stability"
        message = f"Sg {sg:.2f} er brukbar, men gir ikke stor margin mot kulde eller lav fart."

    if velocity_fps is not None:
        checks.append(f"Modellert fart {format_velocity_fps(velocity_fps)}.")
    if twist_inches:
        checks.append(f"Twist 1:{twist_inches:.1f} vurderes mot valgt kule.")

    bullet_length = _coerce_float(bullet.get("length_mm"))
    if bullet_length is not None:
        checks.append(
            f"Kulelengde {format_length_mm(bullet_length)} er med i estimatet."
        )
    if bullet.get("base_type"):
        checks.append(
            f"Base-type {str(bullet.get('base_type')).replace('_', ' ')} er registrert."
        )
    if bullet.get("construction_type"):
        checks.append(
            f"Konstruksjon {str(bullet.get('construction_type')).replace('_', ' ')} er registrert."
        )
    if bullet.get("geometry_confidence") in {"low", "medium"}:
        checks.append(
            "Kulegeometrien er delvis tolket eller mangler felt. Legg inn mer kuledata for bedre modell."
        )
    recommended_twist = _estimate_greenhill_twist_inches(
        diameter_mm=_coerce_float(bullet.get("diameter_mm")),
        length_mm=bullet_length,
        muzzle_velocity_fps=velocity_fps,
    )
    if recommended_twist is not None:
        checks.append(
            f"Enkel Greenhill-guide peker mot omtrent 1:{recommended_twist:.1f}."
        )
        if twist_inches and twist_inches > recommended_twist + 1.0:
            if level != "critical":
                level = "warning"
            title = (
                "Twist may be slow for bullet length" if level != "critical" else title
            )
            message = (
                f"Dagens twist 1:{twist_inches:.1f} virker langsom for kulelengden."
                if level != "critical"
                else message
            )

    if has_suppressor and sg < 1.3:
        checks.append(
            "Demper registrert: marginal stabilitet gir ekstra risiko for yaw og mulig baffle-kontakt."
        )
        if level != "critical":
            level = "critical" if subsonic_mode else "warning"
            if level == "critical":
                title = "Suppressor risk from low stability"
                message = f"Sg {sg:.2f} er marginal med demper i oppsettet."
    elif has_suppressor:
        checks.append(
            "Demper registrert: god stabilitetsmargin er ekstra viktig for videre testing."
        )

    if subsonic_mode:
        checks.append(
            "Subsonisk modus aktiv: stabilitet vektes strengere enn i vanlig hastighetsomrade."
        )

    return {
        "level": level,
        "title": title,
        "message": message,
        "sg": sg,
        "checks": checks,
    }


def build_bullet_fit_summary(
    *,
    bullet: dict[str, Any] | None,
    bullet_geometry: dict[str, Any] | None,
    stability: dict[str, Any] | None,
    stability_assessment: dict[str, Any] | None,
    harmonics: dict[str, Any] | None,
    twist_inches: float | None,
    result: dict[str, Any] | None,
) -> dict[str, Any]:
    bullet = bullet or {}
    bullet_geometry = bullet_geometry or {}
    stability = stability or {}
    stability_assessment = stability_assessment or {}
    harmonics = harmonics or {}
    result = result or {}

    checks: list[str] = []
    missing_fields = [
        str(item).strip()
        for item in (bullet_geometry.get("missing_fields") or [])
        if str(item).strip()
    ]

    sg = _coerce_float(stability.get("sg"))
    velocity_fps = _coerce_float(
        result.get("muzzle_velocity_fps", stability.get("velocity_fps"))
    )
    recommended_twist = _coerce_float(bullet_geometry.get("recommended_twist_in"))
    seating_sensitivity = _coerce_float(
        (
            (harmonics.get("sensitivity") or {})
            if isinstance(harmonics.get("sensitivity"), dict)
            else {}
        ).get("seating_depth")
    )

    score = 50.0

    if sg is not None:
        if sg >= 1.55:
            score += 24.0
        elif sg >= 1.35:
            score += 16.0
        elif sg >= 1.20:
            score += 8.0
        elif sg >= 1.0:
            score -= 10.0
        else:
            score -= 26.0
        checks.append(f"SG {sg:.2f} based on current twist and modeled velocity.")
    else:
        checks.append(
            "SG could not be calculated from the current bullet and rifle data."
        )

    twist_assessment = (
        str(bullet_geometry.get("twist_assessment") or "unknown").strip().lower()
    )
    if twist_assessment == "compatible":
        score += 15.0
    elif twist_assessment == "borderline":
        score += 6.0
    elif twist_assessment == "slow_for_bullet":
        score -= 16.0

    geometry_confidence = (
        str(
            bullet_geometry.get("geometry_confidence")
            or bullet.get("geometry_confidence")
            or "unknown"
        )
        .strip()
        .lower()
    )
    if geometry_confidence == "high":
        score += 8.0
    elif geometry_confidence == "medium":
        score += 4.0
    elif geometry_confidence == "low":
        score -= 2.0

    if missing_fields:
        score -= min(18.0, float(len(missing_fields)) * 4.0)
        checks.append("Missing geometry fields: " + ", ".join(missing_fields[:4]) + ".")

    if twist_inches is not None:
        if recommended_twist is not None:
            checks.append(
                f"Current twist 1:{twist_inches:.1f}; simple guidance points to about 1:{recommended_twist:.1f} or faster."
            )
        else:
            checks.append(
                f"Current twist 1:{twist_inches:.1f} is available for fit evaluation."
            )

    if velocity_fps is not None:
        checks.append(f"Modeled muzzle velocity {format_velocity_fps(velocity_fps)}.")

    bullet_length = _coerce_float(
        bullet_geometry.get("length_mm", bullet.get("length_mm"))
    )
    if bullet_length is not None:
        checks.append(
            f"Bullet length {format_length_mm(bullet_length)} is part of the fit model."
        )

    if seating_sensitivity is not None and seating_sensitivity >= 1.6:
        score -= 4.0
        checks.append(
            f"Seating sensitivity {seating_sensitivity:.2f}: this bullet likely benefits from tighter seating-depth control."
        )

    notes = [
        str(item).strip()
        for item in (bullet_geometry.get("notes") or [])
        if str(item).strip()
    ]
    if notes:
        checks.extend(notes[:2])

    score = max(0.0, min(100.0, score))

    level = "ok"
    title = "Bullet fit looks strong"
    message = "The bullet appears to match the rifle well for twist, stability margin, and geometry context."
    if sg is not None and sg < 1.0:
        level = "critical"
        title = "Bullet fit is unsafe"
        message = "Current stability is below a usable margin. Choose a shorter bullet, higher velocity, or faster twist before testing."
    elif score < 40.0:
        level = "critical"
        title = "Bullet fit is poor"
        message = "The current bullet-rifle combination shows weak stability or geometry fit and should be treated as high risk."
    elif score < 65.0:
        level = "warning"
        title = "Bullet fit is usable but narrow"
        message = "The setup may work, but the margin is limited. Confirm with groups, yaw signs, and a conservative test plan."

    recommended_bits: list[str] = []
    if recommended_twist is not None:
        recommended_bits.append(f"twist about 1:{recommended_twist:.1f} or faster")
    if sg is not None and sg < 1.35:
        recommended_bits.append("target SG around 1.35 to 1.55 for more working margin")
    if seating_sensitivity is not None and seating_sensitivity >= 1.6:
        recommended_bits.append("keep seating-depth changes small and measured")
    if not recommended_bits:
        recommended_bits.append("current setup is close to the recommended baseline")

    return {
        "fit_score": round(score, 1),
        "level": level,
        "title": title,
        "message": message,
        "checks": checks[:6],
        "recommended_baseline": "; ".join(recommended_bits),
        "geometry_confidence": geometry_confidence,
        "twist_assessment": twist_assessment or "unknown",
        "sg": sg,
    }


def _build_terminal_summary(
    *,
    usage_profile: str,
    target_distance_m: float,
    impact_velocity_fps: float | None,
    impact_energy_ftlbs: float | None,
    bullet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bullet = bullet or {}
    usage = str(usage_profile or "precision").strip().lower()
    if impact_velocity_fps is None or impact_energy_ftlbs is None:
        return {
            "level": "unknown",
            "title": "Terminal assessment unavailable",
            "message": "Missing impact data for the selected distance.",
        }

    projectile_profile = _build_projectile_terminal_profile(bullet, usage)
    min_energy = float(projectile_profile.get("minimum_energy_ftlbs") or 0.0)
    min_velocity = _coerce_float(projectile_profile.get("minimum_expansion_fps")) or 0.0
    preferred_min = _coerce_float(projectile_profile.get("preferred_impact_min_fps"))
    preferred_max = _coerce_float(projectile_profile.get("preferred_impact_max_fps"))
    profile_summary = projectile_profile.get("profile_summary")
    advisory_notes = [
        str(note).strip()
        for note in (projectile_profile.get("notes") or [])
        if str(note).strip()
    ]

    title = "Impact window"
    if usage == "hunting_small":
        title = "Small game impact window"
    elif usage == "hunting_medium":
        title = "Hunting impact window"
    elif usage == "hunting_large":
        title = "Large game impact window"
    elif usage == "long_range_hunting":
        title = "Long-range hunting impact window"

    if usage not in {
        "hunting_small",
        "hunting_medium",
        "hunting_large",
        "long_range_hunting",
    }:
        extra_bits: list[str] = []
        if profile_summary:
            extra_bits.append(f"Projectile profile: {profile_summary}.")
        if preferred_min is not None:
            if preferred_max is not None:
                extra_bits.append(
                    f"Estimated working window: {format_velocity_fps(preferred_min)} to {format_velocity_fps(preferred_max)}."
                )
            else:
                extra_bits.append(
                    f"Estimated minimum impact window: {format_velocity_fps(preferred_min)}."
                )
        extra_bits.extend(advisory_notes[:1])
        return {
            "level": "info",
            "title": "Terminal assessment",
            "message": (
                f"Impact at {target_distance_m:.0f} m: {format_velocity_fps(impact_velocity_fps)} and {impact_energy_ftlbs:.0f} ft-lbs. "
                + " ".join(extra_bits)
            ).strip(),
            "projectile_profile": projectile_profile,
        }

    construction = (
        str(projectile_profile.get("construction_type") or "").strip().lower()
    )
    tip_type = str(projectile_profile.get("tip_type") or "").strip().lower()
    bullet_type = str(projectile_profile.get("bullet_type") or "").strip().lower()

    suitability_warning = None
    level = "ok"
    if construction == "match" or _contains_any(
        bullet_type, "match", "otm", "smk", "eld-m", "rdf", "scenar"
    ):
        suitability_warning = "This projectile looks match-oriented, so controlled hunting expansion may be less predictable."
        level = "warning"
    elif (
        construction == "fmj"
        or tip_type == "fmj"
        or _contains_any(bullet_type, "fmj", "full metal jacket")
    ):
        suitability_warning = "This projectile looks FMJ-like and is usually a poor match when controlled expansion is the goal."
        level = "warning"

    failures: list[str] = []
    cautions: list[str] = []
    if min_energy and impact_energy_ftlbs < min_energy:
        failures.append(
            f"energy is below the target floor ({impact_energy_ftlbs:.0f} vs {min_energy:.0f} ft-lbs)"
        )
    if min_velocity and impact_velocity_fps < min_velocity:
        failures.append(
            f"impact velocity is below the estimated minimum working window ({format_velocity_fps(impact_velocity_fps)} vs {format_velocity_fps(min_velocity)})"
        )
    if preferred_min is not None and impact_velocity_fps < preferred_min:
        cautions.append(
            f"impact velocity sits below the preferred expansion window ({format_velocity_fps(preferred_min)}+)"
        )
    if preferred_max is not None and impact_velocity_fps > preferred_max:
        cautions.append(
            f"impact velocity sits above the preferred window ({format_velocity_fps(preferred_max)} max estimate)"
        )

    if failures:
        level = "warning" if level != "critical" else level
        message_bits = [
            f"Impact at {target_distance_m:.0f} m is {format_velocity_fps(impact_velocity_fps)} and {impact_energy_ftlbs:.0f} ft-lbs.",
            "Energy alone is not enough here: " + "; ".join(failures) + ".",
        ]
        if suitability_warning:
            message_bits.append(suitability_warning)
        elif advisory_notes:
            message_bits.append(advisory_notes[0])
        return {
            "level": level,
            "title": title,
            "message": " ".join(message_bits),
            "projectile_profile": projectile_profile,
        }

    message_bits = [
        f"Impact at {target_distance_m:.0f} m is {format_velocity_fps(impact_velocity_fps)} and {impact_energy_ftlbs:.0f} ft-lbs.",
    ]
    if cautions:
        level = "warning" if level == "ok" else level
        message_bits.append(
            "Projectile suitability looks usable, but " + "; ".join(cautions) + "."
        )
    else:
        message_bits.append(
            "Projectile energy and impact speed look usable for the selected purpose."
        )
    if suitability_warning:
        message_bits.append(suitability_warning)
    elif advisory_notes:
        message_bits.append(advisory_notes[0])
    if profile_summary:
        message_bits.append(f"Profile: {profile_summary}.")
    return {
        "level": level,
        "title": title,
        "message": " ".join(message_bits),
        "projectile_profile": projectile_profile,
    }


def build_game_suitability_summary(
    *,
    usage_profile: str,
    terminal_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    terminal_summary = terminal_summary or {}
    usage = str(usage_profile or "").strip().lower()

    game_labels = {
        "hunting_small": "Smaller game",
        "hunting_medium": "Roe deer / medium game",
        "hunting_large": "Moose / large game",
        "long_range_hunting": "Long-range hunting",
    }
    game_label = game_labels.get(usage)
    if not game_label:
        return {
            "level": "neutral",
            "title": "Game Suitability",
            "message": "Game suitability becomes active when the workflow is hunting-oriented.",
            "confidence_label": "Inactive",
            "confidence_message": "No hunting usage profile is selected.",
            "game_label": None,
        }

    projectile_profile = (
        terminal_summary.get("projectile_profile")
        if isinstance(terminal_summary.get("projectile_profile"), dict)
        else {}
    )
    profile_confidence = (
        str(projectile_profile.get("confidence") or "low").strip().lower()
    )
    profile_summary = str(projectile_profile.get("profile_summary") or "").strip()
    terminal_level = str(terminal_summary.get("level") or "unknown").strip().lower()
    terminal_message = str(terminal_summary.get("message") or "").strip()

    confidence_label = "Low confidence"
    confidence_message = "The suitability view is mostly heuristic and should be backed by known bullet behavior."
    if profile_confidence == "high":
        confidence_label = "Medium confidence"
        confidence_message = "The estimate is supported by recognizable bullet construction and impact-window logic, but is not a tissue simulation."
    elif profile_confidence == "medium":
        confidence_label = "Medium confidence"
        confidence_message = "The estimate uses some bullet-profile signals, but more bullet-specific terminal data would improve it."

    level = "ok"
    title = f"Suitable for {game_label}"
    message = f"Current impact window looks usable for {game_label.lower()}."
    if terminal_level in {"warning", "critical"}:
        level = "warning"
        title = f"Conditional fit for {game_label}"
        message = (
            terminal_message
            or f"The current impact window is usable only with caution for {game_label.lower()}."
        )
    elif terminal_level in {"unknown", "neutral"}:
        level = "unknown"
        title = f"Suitability unclear for {game_label}"
        message = (
            terminal_message
            or "The app is missing enough impact data to make a hunting suitability call."
        )

    checks: list[str] = []
    if profile_summary:
        checks.append(f"Projectile profile: {profile_summary}.")
    minimum_expansion = _coerce_float(projectile_profile.get("minimum_expansion_fps"))
    preferred_min = _coerce_float(projectile_profile.get("preferred_impact_min_fps"))
    preferred_max = _coerce_float(projectile_profile.get("preferred_impact_max_fps"))
    if minimum_expansion is not None:
        checks.append(
            f"Estimated minimum working floor {format_velocity_fps(minimum_expansion)}."
        )
    if preferred_min is not None and preferred_max is not None:
        checks.append(
            f"Preferred impact window about {format_velocity_fps(preferred_min)} to {format_velocity_fps(preferred_max)}."
        )
    elif preferred_min is not None:
        checks.append(
            f"Preferred impact starts around {format_velocity_fps(preferred_min)}."
        )

    return {
        "level": level,
        "title": title,
        "message": message,
        "confidence_label": confidence_label,
        "confidence_message": confidence_message,
        "game_label": game_label,
        "checks": checks[:3],
    }


def _build_brass_context_summary(
    *,
    barrel_details: dict[str, Any] | None,
    case_row: dict[str, Any] | None,
    internal_ballistics: dict[str, Any] | None,
) -> dict[str, Any]:
    barrel_details = barrel_details or {}
    case_row = case_row or {}
    internal_ballistics = internal_ballistics or {}
    case_measurements = barrel_details.get("case_measurements") or {}

    h2o_primary = _coerce_float(
        _merge_first_nonempty(
            case_measurements.get("h2o_capacity_grains"),
            case_row.get("case_capacity_gr_h2o"),
            case_row.get("case_capacity_h2o_gr"),
            case_row.get("avg_case_capacity_h2o"),
        )
    )
    h2o_samples = [
        _coerce_float(sample.get("h2o_capacity_grains"))
        for sample in (case_measurements.get("h2o_measurements") or [])
        if isinstance(sample, dict)
        and _coerce_float(sample.get("h2o_capacity_grains")) is not None
    ]
    h2o_spread = None
    if len(h2o_samples) >= 2:
        h2o_spread = max(h2o_samples) - min(h2o_samples)
    if h2o_spread is None:
        h2o_spread = _coerce_float(case_row.get("capacity_spread_h2o"))

    shoulder_bump_mm = _coerce_float(case_measurements.get("shoulder_bump_mm"))
    base_to_datum_mm = _coerce_float(case_measurements.get("base_to_datum_mm"))
    neck_diameter_mm = _coerce_float(case_measurements.get("neck_diameter_mm"))
    trim_length_mm = _coerce_float(case_measurements.get("trim_length_mm"))
    modeled_capacity_ml = _coerce_float(
        _merge_first_nonempty(
            internal_ballistics.get("case_capacity_ml"),
            internal_ballistics.get("case_capacity_cc"),
            case_row.get("case_capacity_ml"),
        )
    )

    checks: list[str] = []
    level = "info"
    title = "Brass-baseline er delvis kjent"
    message = (
        "Legg inn flere mål fra skutte hylser for å styrke kammer- og trykkmodellen."
    )

    if h2o_primary is not None:
        checks.append(
            f"H2O / case capacity {format_weight_grains(h2o_primary, 'powder')}."
        )
        level = "ok"
        title = "Brass-baseline er tilgjengelig"
        message = (
            "Målt case capacity kan brukes som bedre grunnlag enn rene standardverdier."
        )
    else:
        checks.append("H2O / case capacity mangler fra aktiv pipe.")

    if h2o_spread is not None:
        checks.append(f"H2O-spread {format_weight_grains(h2o_spread, 'powder')}.")
        if h2o_spread > 0.75:
            level = "warning"
            title = "Brass-variansen er høy"
            message = "Stor spredning i H2O-målingene gjør små trykk- og hastighetsforskjeller mindre pålitelige."
        elif h2o_spread > 0.30:
            checks.append(
                "Middels H2O-spread: bruk konservative tolkninger av små forskjeller."
            )
        else:
            checks.append("H2O-serien ser jevn ut for denne pipe-/hylsekombinasjonen.")

    if shoulder_bump_mm is not None:
        checks.append(f"Shoulder bump {format_length_mm(shoulder_bump_mm)}.")
    if base_to_datum_mm is not None:
        checks.append(f"Base-to-datum {format_length_mm(base_to_datum_mm)}.")
    if neck_diameter_mm is not None:
        checks.append(f"Neck-diameter {format_length_mm(neck_diameter_mm)}.")
    if trim_length_mm is not None:
        checks.append(f"Trimlengde {format_length_mm(trim_length_mm)}.")
    if modeled_capacity_ml is not None:
        checks.append(f"Modellert hylsevolum {modeled_capacity_ml:.3f} ml.")

    missing_bits: list[str] = []
    if h2o_primary is None:
        missing_bits.append("H2O / case capacity")
    if neck_diameter_mm is None:
        missing_bits.append("neck-diameter")
    if trim_length_mm is None:
        missing_bits.append("trimlengde")
    if shoulder_bump_mm is None:
        missing_bits.append("shoulder bump")
    if base_to_datum_mm is None:
        missing_bits.append("base-to-datum")

    source_count = sum(
        value is not None
        for value in (
            h2o_primary,
            shoulder_bump_mm,
            base_to_datum_mm,
            neck_diameter_mm,
            trim_length_mm,
        )
    )
    if source_count >= 4 and level != "warning":
        level = "ok"
        title = "Brass-baseline er sterk"
        message = "Mål fra skutte hylser gir et godt grunnlag for internballistikk, seating og harmonikkvurdering."
    elif source_count <= 1 and level != "warning":
        title = "Brass-baseline er svak"
        message = "Mål H2O, neck-diameter, trimlengde, shoulder bump og base-to-datum på skutte hylser for å gjøre analysen mer pipe-spesifikk."

    if missing_bits:
        checks.append("Mangler: " + ", ".join(missing_bits[:5]) + ".")
    if h2o_primary is None and not h2o_samples:
        checks.append(
            "Start gjerne med 3-5 H2O-målinger fra skutte hylser i samme pipe."
        )

    return {
        "level": level,
        "title": title,
        "message": message,
        "h2o_capacity_grains": h2o_primary,
        "h2o_spread_grains": h2o_spread,
        "shoulder_bump_mm": shoulder_bump_mm,
        "base_to_datum_mm": base_to_datum_mm,
        "neck_diameter_mm": neck_diameter_mm,
        "trim_length_mm": trim_length_mm,
        "checks": checks,
    }


def _build_barrel_context_summary(
    *,
    rifle: dict[str, Any] | None,
    barrel_details: dict[str, Any] | None,
    twist_inches: float | None,
    stability: dict[str, Any] | None,
) -> dict[str, Any]:
    rifle = rifle or {}
    barrel_details = barrel_details or {}
    stability = stability or {}

    barrel_name = _clean_label(barrel_details.get("name")) or "Aktiv pipe"
    barrel_length_mm = _coerce_float(
        _merge_first_nonempty(
            barrel_details.get("length_mm"), rifle.get("barrel_length_mm")
        )
    )
    barrel_profile = _clean_label(barrel_details.get("barrel_profile"))
    attachment = _clean_label(
        _merge_first_nonempty(
            barrel_details.get("barrel_attachment_type"),
            barrel_details.get("mount_type"),
        )
    )
    free_float_mm = _coerce_float(barrel_details.get("free_float_length_mm"))
    muzzle_type = _clean_label(
        _merge_first_nonempty(
            barrel_details.get("muzzle_device_type"), rifle.get("muzzle_device")
        )
    )
    muzzle_model = _clean_label(barrel_details.get("muzzle_device_model"))
    muzzle_weight_g = _coerce_float(barrel_details.get("muzzle_device_weight_g"))
    twist_direction = _clean_label(
        _merge_first_nonempty(
            barrel_details.get("rifling_direction"),
            barrel_details.get("twist_direction"),
            rifle.get("twist_direction"),
        )
    )

    checks: list[str] = [f"Pipe: {barrel_name}."]
    level = "info"
    title = "Pipekontekst delvis kjent"
    message = "Legg inn pipeprofil, twist og munningsutstyr for bedre harmonikkmodell."

    if barrel_length_mm is not None:
        checks.append(f"Pipe-lengde {barrel_length_mm:.1f} mm.")
    if barrel_profile:
        checks.append(f"Pipeprofil {barrel_profile}.")
    if twist_inches is not None:
        checks.append(f"Twist 1:{twist_inches:.1f}.")
        level = "ok"
        title = "Pipekontekst er tilgjengelig"
        message = "Twist og pipeparametre kan brukes aktivt i stabilitet og node-fit."
    else:
        checks.append("Twist mangler fra aktiv pipe.")
    if twist_direction:
        checks.append(f"Rifleretning {twist_direction}.")
    if attachment:
        checks.append(f"Innfestning {attachment}.")
    if free_float_mm is not None:
        checks.append(f"Fri flukt {free_float_mm:.1f} mm.")
    if muzzle_type:
        muzzle_text = f"Munningsutstyr {muzzle_type}"
        if muzzle_model:
            muzzle_text += f" ({muzzle_model})"
        if muzzle_weight_g is not None:
            muzzle_text += f", {muzzle_weight_g:.0f} g"
        checks.append(f"{muzzle_text}.")

    sg = _coerce_float(stability.get("sg"))
    if sg is not None and sg < 1.3 and muzzle_type == "suppressor":
        level = "warning"
        title = "Pipekontekst viser ekstra risiko"
        message = (
            "Marginal stabilitet sammen med demper krever konservativ verifisering."
        )

    known_count = sum(
        value is not None and value != ""
        for value in (
            barrel_length_mm,
            barrel_profile,
            twist_inches,
            attachment,
            free_float_mm,
            muzzle_type,
        )
    )
    if known_count >= 4 and level != "warning":
        level = "ok"
        title = "Pipekontekst er sterk"
        message = "Pipeprofilen har nok data til å gi bedre harmonikk- og stabilitetsvurdering."

    return {
        "level": level,
        "title": title,
        "message": message,
        "barrel_name": barrel_name,
        "barrel_length_mm": barrel_length_mm,
        "barrel_profile": barrel_profile,
        "barrel_attachment": attachment,
        "free_float_length_mm": free_float_mm,
        "muzzle_device_type": muzzle_type,
        "muzzle_device_model": muzzle_model,
        "muzzle_device_weight_g": muzzle_weight_g,
        "twist_direction": twist_direction,
        "checks": checks,
    }


def _recommendation_window(
    *,
    result: dict[str, Any],
    harmonics: dict[str, Any],
    pressure_assessment: dict[str, Any],
    stability_assessment: dict[str, Any],
    internal_ballistics: dict[str, Any] | None,
    terminal_summary: dict[str, Any] | None,
    input_quality: dict[str, Any] | None = None,
    observation_summary: dict[str, Any] | None = None,
    usage_profile: str = "precision",
    subsonic_mode: bool,
    bullet: dict[str, Any] | None = None,
    primer: dict[str, Any] | None = None,
    bullet_lot_context: dict[str, Any] | None = None,
    powder_lot_context: dict[str, Any] | None = None,
    primer_lot_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bullet = bullet or {}
    primer = primer or {}
    internal_ballistics = internal_ballistics or {}
    terminal_summary = terminal_summary or {}
    input_quality = input_quality or {}
    observation_summary = observation_summary or {}
    bullet_lot_context = bullet_lot_context or {}
    powder_lot_context = powder_lot_context or {}
    primer_lot_context = primer_lot_context or {}
    usage_profile = str(usage_profile or "precision").strip().lower()
    quality_level = str(input_quality.get("level") or "").strip().lower()
    quality_score = _coerce_float(input_quality.get("score")) or 0.0
    chrono_count = int(observation_summary.get("chrono_count") or 0)
    accuracy_count = int(observation_summary.get("accuracy_count") or 0)
    charge_weight = _coerce_float(result.get("charge_weight_gr"))
    if charge_weight is None:
        return {
            "next_step": "Verifiser inngangsdata for a fa anbefalt charge-vindu.",
        }

    charge_sensitivity = (
        _coerce_float((harmonics.get("sensitivity") or {}).get("charge")) or 1.0
    )
    seating_sensitivity = (
        _coerce_float((harmonics.get("sensitivity") or {}).get("seating_depth")) or 1.0
    )
    harmonic_score = _coerce_float(harmonics.get("harmonic_score")) or 10.0

    if str(bullet.get("shape_family") or "").strip().lower() == "vld":
        seating_sensitivity = max(seating_sensitivity, 1.15)
    if str(bullet.get("base_type") or "").strip().lower() == "boat_tail":
        charge_sensitivity = max(charge_sensitivity, 0.9)
    if str(bullet.get("construction_type") or "").strip().lower() == "monolithic":
        seating_sensitivity = max(seating_sensitivity, 1.05)

    powder_checks = " ".join(
        str(item) for item in (powder_lot_context.get("checks") or [])
    ).lower()
    if (
        "lot-avvik" in powder_checks
        or "trykkobservasjoner" in powder_checks
        or powder_lot_context.get("level") == "warning"
    ):
        charge_sensitivity = max(charge_sensitivity, 1.15)
    elif powder_lot_context.get("level") == "ok":
        charge_sensitivity = max(charge_sensitivity, 0.95)

    bullet_sample_count = int(bullet_lot_context.get("sample_count") or 0)
    if bullet_sample_count >= 10:
        seating_sensitivity = max(seating_sensitivity, 0.95)
    elif bullet_lot_context.get("level") == "info":
        seating_sensitivity = max(seating_sensitivity, 1.05)

    primer_checks = " ".join(
        str(item) for item in (primer_lot_context.get("checks") or [])
    ).lower()
    if "typisk es" in primer_checks or "typisk sd" in primer_checks:
        charge_sensitivity = max(charge_sensitivity, 0.95)

    primer_family = str(primer.get("primer_family") or "").strip().lower()
    ignition_strength = str(primer.get("ignition_strength_class") or "").strip().lower()
    pressure_class = str(primer.get("pressure_tolerance_class") or "").strip().lower()
    cold_weather = str(primer.get("cold_weather_suitability") or "").strip().lower()
    recommended_min_psi = _coerce_float(primer.get("recommended_pressure_min_psi"))
    recommended_max_psi = _coerce_float(primer.get("recommended_pressure_max_psi"))
    peak_pressure_psi = _coerce_float(result.get("max_pressure_psi"))

    if ignition_strength == "magnum":
        if subsonic_mode or pressure_assessment.get("level") in {"warning", "critical"}:
            charge_sensitivity = max(charge_sensitivity, 1.1)
        elif primer_family.endswith("rifle_magnum"):
            charge_sensitivity = max(charge_sensitivity, 1.03)
    elif ignition_strength in {"standard_plus", "benchrest"}:
        charge_sensitivity = max(charge_sensitivity, 0.97)

    if pressure_class in {"standard", "medium"} and pressure_assessment.get(
        "level"
    ) in {"warning", "critical"}:
        charge_sensitivity = max(charge_sensitivity, 1.1)
    elif pressure_class in {"high", "medium_high"}:
        charge_sensitivity = max(charge_sensitivity, 0.98)

    if peak_pressure_psi is not None:
        if recommended_max_psi is not None and peak_pressure_psi > recommended_max_psi:
            charge_sensitivity = max(charge_sensitivity, 1.15)
        elif (
            recommended_min_psi is not None and peak_pressure_psi < recommended_min_psi
        ):
            charge_sensitivity = max(charge_sensitivity, 1.05)

    if cold_weather in {"poor", "limited"} and subsonic_mode:
        charge_sensitivity = max(charge_sensitivity, 1.08)
    elif cold_weather == "good":
        charge_sensitivity = max(charge_sensitivity, 0.98)

    fill_percent = _coerce_float(internal_ballistics.get("load_density_percent"))
    compression_ratio = _coerce_float(internal_ballistics.get("compression_ratio"))
    burn_percent = _coerce_float(internal_ballistics.get("burn_completeness_percent"))
    internal_level = str(internal_ballistics.get("level") or "").strip().lower()
    temp_stable = internal_ballistics.get("temp_stable")
    validation_status = (
        str(internal_ballistics.get("validation_status") or "").strip().lower()
    )
    terminal_level = str(terminal_summary.get("level") or "").strip().lower()
    terminal_message = str(terminal_summary.get("message") or "").strip()
    terminal_profile = (
        terminal_summary.get("projectile_profile")
        if isinstance(terminal_summary.get("projectile_profile"), dict)
        else {}
    )
    terminal_confidence = str(terminal_profile.get("confidence") or "").strip().lower()
    projectile_summary = str(terminal_profile.get("profile_summary") or "").strip()
    preferred_terminal_floor = _coerce_float(
        terminal_profile.get("preferred_impact_min_fps")
    )

    if fill_percent is not None:
        if fill_percent < 85:
            charge_sensitivity = max(charge_sensitivity, 1.05)
            seating_sensitivity = max(seating_sensitivity, 1.05)
        elif fill_percent > 103:
            charge_sensitivity = max(charge_sensitivity, 1.15)
        elif fill_percent >= 90:
            charge_sensitivity = max(charge_sensitivity, 0.95)

    if compression_ratio is not None and compression_ratio < 0.96:
        charge_sensitivity = max(charge_sensitivity, 1.2)
        seating_sensitivity = max(seating_sensitivity, 1.05)

    if burn_percent is not None:
        if burn_percent < 78:
            charge_sensitivity = max(charge_sensitivity, 1.2)
        elif burn_percent < 88:
            charge_sensitivity = max(charge_sensitivity, 1.1)

    if temp_stable in (False, 0, "0"):
        charge_sensitivity = max(charge_sensitivity, 1.05)

    if validation_status in {"memory_extracted", "unverified"}:
        charge_sensitivity = max(charge_sensitivity, 1.05)
    if usage_profile.startswith("hunting") and terminal_level == "warning":
        charge_sensitivity = max(charge_sensitivity, 1.05)
    elif usage_profile.startswith("hunting") and terminal_level == "critical":
        charge_sensitivity = max(charge_sensitivity, 1.1)

    charge_step = (
        0.2 if charge_sensitivity >= 1.1 else 0.3 if charge_sensitivity >= 0.8 else 0.4
    )
    seating_step_mm = (
        0.10
        if seating_sensitivity >= 1.1
        else 0.20 if seating_sensitivity >= 0.8 else 0.30
    )

    # Recommendation windows should reflect evidence strength, not just modeled sensitivity.
    if quality_level == "low" or quality_score < 2.5:
        charge_step = max(charge_step, 0.4)
        seating_step_mm = max(seating_step_mm, 0.30)
    elif chrono_count == 0 and accuracy_count == 0:
        charge_step = max(charge_step, 0.35)
        seating_step_mm = max(seating_step_mm, 0.25)
    elif (
        chrono_count >= 3
        and accuracy_count >= 2
        and quality_level == "high"
        and str(pressure_assessment.get("level") or "") not in {"warning", "critical"}
    ):
        charge_step = min(charge_step, 0.2)
        seating_step_mm = min(seating_step_mm, 0.10)
    elif (
        chrono_count >= 2
        and accuracy_count >= 1
        and quality_level in {"medium", "high"}
    ):
        charge_step = min(charge_step, 0.25)
        seating_step_mm = min(seating_step_mm, 0.15)

    if str(pressure_assessment.get("level")) == "critical":
        next_step = (
            "Reduser kruttmengden og verifiser med kort serie før videre testing."
        )
    elif internal_level == "critical":
        next_step = (
            "Reduser charge eller velg en mer robust kombinasjon for du tester videre."
        )
    elif str(stability_assessment.get("level")) == "critical":
        next_step = "Bekreft stabilitet for valgt kule/twist-forhold for du jager videre presisjon."
    elif usage_profile.startswith("hunting") and terminal_level == "critical":
        next_step = "Kort ned realistisk jaktavstand eller velg et mer egnet prosjektil for du regner ladningen som jaktklar."
    elif usage_profile.startswith("hunting") and terminal_level == "warning":
        next_step = "Bekreft impact-vindu og kaldpipe ved realistisk jaktavstand for du laster inn denne som ferdig jaktprofil."
    elif subsonic_mode:
        next_step = "Verifiser sonic margin, funksjon og stabilitet med en kort subsonisk serie."
    elif internal_level == "warning":
        next_step = "Bekreft fyllingsgrad, forbrenning og temperaturrespons med en kort verifiseringsserie."
    elif harmonic_score >= 14:
        next_step = (
            "Bekreft noden med en kort verifiseringsserie og små seating-endringer."
        )
    else:
        next_step = "Kjor et lite charge- eller seating-sweep for a finne et mer robust arbeidsvindu."

    notes: list[str] = []
    if str(bullet.get("shape_family") or "").strip().lower() == "vld":
        notes.append("VLD-/hybridprofil: prioriter sma seating-endringer rundt noden.")
    if str(bullet.get("construction_type") or "").strip().lower() == "monolithic":
        notes.append(
            "Monolittisk kule: verifiser trykk og seating ekstra konservativt."
        )
    if bullet.get("geometry_confidence") in {"low", "medium"}:
        notes.append("Mer kuledata kan gi bedre seating- og terminalvurdering.")
    if powder_lot_context.get("level") == "warning":
        notes.append(
            "Kruttlotten viser avvik eller trykksignal i historikken. Hold charge-steg små og verifiser konservativt."
        )
    elif powder_lot_context.get("level") == "ok":
        notes.append(
            "Kruttlotten har læringsgrunnlag som kan brukes til å bekrefte charge-vinduet."
        )
    if bullet_sample_count >= 10:
        notes.append(
            "Kulelotten har god måleserie. Seating-rådet bygger på mer presis lot-geometri enn katalogverdier alene."
        )
    elif bullet_lot_context.get("level") == "info":
        notes.append(
            "Kulelot er valgt, men måleserien er fortsatt tynn. Bekreft seating med små steg."
        )
    if primer_lot_context.get("level") == "ok":
        notes.append("Tennhettelot med læring kan hjelpe når ES/SD skal vurderes.")
    if ignition_strength == "magnum":
        notes.append(
            "Magnum-tennhette: bekreft trykk og ES nøye hvis ladningen allerede er tett eller rask."
        )
    elif ignition_strength in {"standard_plus", "benchrest"}:
        notes.append(
            "Benchrest/match-tennhette passer godt når du vil bekrefte små ES/SD-forskjeller."
        )
    if pressure_class in {"standard", "medium"} and pressure_assessment.get(
        "level"
    ) in {"warning", "critical"}:
        notes.append(
            "Tennhettens trykkklasse tilsier litt ekstra konservative charge-steg i dette trykkområdet."
        )
    if (
        recommended_max_psi is not None
        and peak_pressure_psi is not None
        and peak_pressure_psi > recommended_max_psi
    ):
        notes.append("Beregnet trykk ligger over tennhettens anbefalte trykkvindu.")
    if cold_weather in {"poor", "limited"} and subsonic_mode:
        notes.append(
            "Kuldeegenskapene virker begrensede for subsonisk eller kald bruk. Bekreft tenning i feltforhold."
        )
    if fill_percent is not None and fill_percent < 85:
        notes.append(
            "Lav fyllingsgrad: verifiser orienteringsfølsomhet og ES med flere skudd."
        )
    elif fill_percent is not None and fill_percent > 103:
        notes.append(
            "Hoy fyllingsgrad: hold charge-steg små og bekreft seating/trykk nøye."
        )
    if compression_ratio is not None and compression_ratio < 0.96:
        notes.append("Kompresjon i ladningen tilsier konservative charge-endringer.")
    if burn_percent is not None and burn_percent < 78:
        notes.append(
            "Lav modellert forbrenningsandel: kort pipe eller treg kombinasjon bør bekreftes med chrono og munningssignatur."
        )
    elif burn_percent is not None and burn_percent < 88:
        notes.append(
            "Moderat forbrenningsandel: velocity og effektivitet bør bekreftes i praksis."
        )
    if temp_stable in (False, 0, "0"):
        notes.append(
            "Kruttet er ikke markert som temperaturstabilt. Test i relevant temperaturvindu."
        )
    if usage_profile.startswith("hunting") and projectile_summary:
        notes.append(f"Prosjektilprofil: {projectile_summary}.")
    if usage_profile.startswith("hunting") and preferred_terminal_floor is not None:
        notes.append(
            f"Estimert terminalt arbeidsvindu starter rundt {format_velocity_fps(preferred_terminal_floor)}."
        )
    if (
        usage_profile.startswith("hunting")
        and terminal_level in {"warning", "critical"}
        and terminal_message
    ):
        notes.append(f"Impact-vurdering: {terminal_message}")
    if usage_profile.startswith("hunting") and terminal_confidence in {"low", ""}:
        notes.append(
            "Prosjektildataen er fortsatt tynn. Bekreft terminal egnethet ekstra konservativt."
        )
    if quality_level == "low" or quality_score < 2.5:
        notes.append(
            "Svakt datagrunnlag: anbefalingsvinduet er holdt bredt til chrono og gruppedata finnes."
        )
    elif chrono_count == 0 and accuracy_count == 0:
        notes.append(
            "Ingen egne chrono- eller gruppeserier finnes ennå. Vinduet leses som grov startveiledning, ikke fin node."
        )
    elif chrono_count >= 3 and accuracy_count >= 2 and quality_level == "high":
        notes.append(
            "Sterkt maalegrunnlag: charge- og seating-vinduet kan tolkes som et strammere arbeidsvindu enn ren modellprediksjon."
        )

    can_freeze_charge = (
        quality_level in {"medium", "high"}
        and quality_score >= 2.5
        and (chrono_count >= 1 or accuracy_count >= 1)
    )
    can_freeze_seating = (
        quality_level in {"medium", "high"}
        and quality_score >= 2.5
        and accuracy_count >= 1
    )
    readiness_reason = (
        "Measured support is strong enough to freeze the modeled baseline."
    )
    if not can_freeze_charge and not can_freeze_seating:
        readiness_reason = "Recommendation window is still modeled guidance. Add measured chrono and group data before freezing a baseline."
        notes.append(
            "Anbefalingsvinduet er forelopig modellert veiledning. Samle chrono og gruppedata for du fryser baseline i builderen."
        )
    elif can_freeze_charge and not can_freeze_seating:
        readiness_reason = "Charge window has measured support, but seating still needs group data before it should be frozen."
        notes.append(
            "Charge-vinduet kan brukes som baseline, men seating bor fortsatt bekreftes med gruppedata for det fryses."
        )

    return {
        "charge_step_gr": charge_step,
        "charge_window_gr": [
            round(charge_weight - charge_step, 2),
            round(charge_weight + charge_step, 2),
        ],
        "seating_step_mm": seating_step_mm,
        "seating_window_mm": [round(-seating_step_mm, 2), round(seating_step_mm, 2)],
        "next_step": next_step,
        "notes": notes,
        "baseline_readiness": {
            "charge_can_freeze": can_freeze_charge,
            "seating_can_freeze": can_freeze_seating,
            "chrono_count": chrono_count,
            "accuracy_count": accuracy_count,
            "input_quality_level": quality_level or "unknown",
            "input_quality_score": quality_score,
            "reason": readiness_reason,
        },
        "evidence_profile": {
            "chrono_count": chrono_count,
            "accuracy_count": accuracy_count,
            "input_quality_level": quality_level or "unknown",
            "input_quality_score": quality_score,
        },
    }


def _usage_target_distance(
    usage_profile: str, target_distance_m: float | None
) -> float:
    if isinstance(target_distance_m, (int, float)) and float(target_distance_m) > 0:
        return float(target_distance_m)
    usage = str(usage_profile or "").strip().lower()
    if usage == "subsonic":
        return 100.0
    if usage.startswith("hunting"):
        return 300.0
    if usage == "long_range_hunting":
        return 500.0
    if usage == "precision":
        return 300.0
    if usage == "training":
        return 200.0
    return 300.0


class LoadAnalysisService:
    """Samlet fysikk- og anbefalingslag for laddedelen."""

    def __init__(self, db: Any | None = None):
        self.db = db or get_database()
        self.engine = get_ballistics_engine()
        self.advanced_engine = AdvancedBallisticsEngine()

    def _get_rifle_profile_details(self, rifle_id: int) -> dict[str, Any]:
        try:
            rows = self.db.execute_query(
                "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
                (rifle_id,),
            )
        except Exception:
            return {}
        if not rows or not rows[0].get("profile_json"):
            return {}
        return _safe_json_loads(rows[0]["profile_json"])

    def _resolve_barrel_details(
        self, rifle_id: int, barrel_id: str | None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        details = self._get_rifle_profile_details(rifle_id)
        barrels = details.get("barrels", [])
        selected_id = barrel_id or details.get("active_barrel_id")
        barrel = {}
        if isinstance(barrels, list):
            for candidate in barrels:
                if isinstance(candidate, dict) and str(candidate.get("id")) == str(
                    selected_id
                ):
                    barrel = dict(candidate)
                    break
            if not barrel and barrels and isinstance(barrels[0], dict):
                barrel = dict(barrels[0])
        if barrel:
            details = dict(details)
            details["selected_barrel_id"] = barrel.get("id")
            details["selected_barrel_name"] = barrel.get("name")
        return details, barrel

    def _build_environment(self, request: LoadAnalysisRequest) -> BallisticEnvironment:
        return BallisticEnvironment(
            temperature_c=request.temperature_c,
            pressure_hpa=request.pressure_hpa,
            humidity_percent=request.humidity_percent,
            altitude_m=request.altitude_m,
            wind_speed_mps=request.wind_speed_mps,
            wind_dir_deg=request.wind_dir_deg,
            temperature_source="provided",
            pressure_source="provided",
            humidity_source="provided",
            altitude_source="provided",
        )

    def _resolve_reference_rows(
        self, request: LoadAnalysisRequest
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        rifle_row = self.db.get_by_id("rifles", request.rifle_id) or {}
        bullet_row = self.db.get_by_id("bullets", request.bullet_id) or {}
        powder_row = self.db.get_by_id("powder", request.powder_id) or {}
        primer_id = request.primer_id
        if primer_id is None:
            primer_id = _coerce_int((request.primer_overrides or {}).get("id"))
        primer_row = self.db.get_by_id("primers", primer_id) or {} if primer_id else {}
        return dict(rifle_row), dict(bullet_row), dict(powder_row), dict(primer_row)

    def _apply_bullet_lot_context(
        self,
        bullet: dict[str, Any],
        bullet_lot_id: int | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        bullet = dict(bullet or {})
        summary = {
            "level": "unknown",
            "title": "Kulelot ukjent",
            "message": "Ingen aktiv kulelot valgt.",
            "checks": [],
        }
        if not bullet_lot_id:
            return bullet, summary
        lot_row = self.db.get_by_id("component_lots", bullet_lot_id) or {}
        stats = self.db.get_component_lot_stats(int(bullet_lot_id)) or {}
        if not lot_row:
            return bullet, summary

        lot_number = str(lot_row.get("lot_number") or f"Lot {bullet_lot_id}").strip()
        bullet["selected_lot_id"] = bullet_lot_id
        bullet["selected_lot_number"] = lot_number
        bullet["measured_lot_stats"] = dict(stats)
        bullet["nominal_weight_grains"] = bullet.get(
            "weight_grains", bullet.get("weight")
        )
        bullet["nominal_length_mm"] = bullet.get("length_mm")
        bullet["nominal_diameter_mm"] = bullet.get("diameter_mm")
        if stats.get("weight_avg_grains") is not None:
            bullet["weight_grains"] = float(stats["weight_avg_grains"])
            bullet["weight"] = float(stats["weight_avg_grains"])
        if stats.get("length_avg_mm") is not None:
            bullet["length_mm"] = float(stats["length_avg_mm"])
        if stats.get("diameter_avg_mm") is not None:
            bullet["diameter_mm"] = float(stats["diameter_avg_mm"])

        checks = [f"Aktiv kulelot {lot_number}."]
        sample_count = int(stats.get("sample_count") or 0)
        if sample_count:
            checks.append(f"{sample_count} kontrollmålinger.")
        if stats.get("weight_avg_grains") is not None:
            checks.append(
                f"Målt snittvekt {format_weight_grains(float(stats['weight_avg_grains']), 'bullet')}."
            )
        if stats.get("length_avg_mm") is not None:
            checks.append(
                f"Målt snittlengde {format_length_mm(float(stats['length_avg_mm']))}."
            )
        if stats.get("base_to_ogive_avg_mm") is not None:
            checks.append(
                f"Målt BTO {format_length_mm(float(stats['base_to_ogive_avg_mm']))}."
            )
        summary = {
            "level": "ok" if sample_count >= 5 else "info",
            "title": "Kulelot brukt i analysen",
            "message": (
                "Motoren bruker målte lot-data for kulegeometri og vekt."
                if sample_count
                else "Kulelot er valgt, men mangler måleserie."
            ),
            "checks": checks,
            "lot_number": lot_number,
            "sample_count": sample_count,
        }
        return bullet, summary

    def _build_powder_lot_context(
        self,
        powder_lot_id: int | None,
    ) -> dict[str, Any]:
        summary = {
            "level": "unknown",
            "title": "Kruttlot ukjent",
            "message": "Ingen aktiv kruttlot valgt.",
            "checks": [],
        }
        if not powder_lot_id:
            return summary
        lot_row = self.db.get_by_id("component_lots", powder_lot_id) or {}
        profile = self.db.refresh_powder_lot_learning_profile(int(powder_lot_id)) or {}
        if not lot_row:
            return summary
        lot_number = str(lot_row.get("lot_number") or f"Lot {powder_lot_id}").strip()
        checks = [f"Aktiv kruttlot {lot_number}."]
        if profile.get("confidence_label"):
            checks.append(f"Læring {profile['confidence_label']}.")
        if profile.get("avg_velocity_fps") is not None:
            checks.append(
                f"Typisk fart {format_velocity_fps(float(profile['avg_velocity_fps']))}."
            )
        if profile.get("velocity_offset_fps") is not None:
            checks.append(
                f"Lot-avvik {format_velocity_fps(float(profile['velocity_offset_fps']))}."
            )
        if profile.get("temp_sensitivity_fps_per_c") is not None:
            checks.append(
                f"Tempfølsomhet {format_velocity_fps(float(profile['temp_sensitivity_fps_per_c']))}/°C."
            )
        if int(profile.get("pressure_watch_count") or 0):
            checks.append(
                f"{int(profile['pressure_watch_count'])} trykkobservasjoner knyttet til lotten."
            )
        level = "ok" if float(profile.get("confidence_score") or 0) >= 50 else "info"
        if int(profile.get("pressure_watch_count") or 0):
            level = "warning"
        return {
            "level": level,
            "title": "Kruttlot brukt i analysen",
            "message": (
                "Kruttlot-læring brukes som støtte for tolkning av fart og trykk."
                if profile
                else "Kruttlot er valgt, men mangler læringsgrunnlag."
            ),
            "checks": checks,
            "lot_number": lot_number,
        }

    def _build_primer_lot_context(
        self,
        primer_lot_id: int | None,
    ) -> dict[str, Any]:
        summary = {
            "level": "unknown",
            "title": "Tennhettelot ukjent",
            "message": "Ingen aktiv tennhettelot valgt.",
            "checks": [],
        }
        if not primer_lot_id:
            return summary
        lot_row = self.db.get_by_id("component_lots", primer_lot_id) or {}
        profile = self.db.refresh_primer_lot_learning_profile(int(primer_lot_id)) or {}
        if not lot_row:
            return summary
        lot_number = str(lot_row.get("lot_number") or f"Lot {primer_lot_id}").strip()
        checks = [f"Aktiv tennhettelot {lot_number}."]
        if profile.get("typical_es_fps") is not None:
            checks.append(f"Typisk ES {float(profile['typical_es_fps']):.1f}.")
        if profile.get("typical_sd_fps") is not None:
            checks.append(f"Typisk SD {float(profile['typical_sd_fps']):.1f}.")
        return {
            "level": "ok" if profile else "info",
            "title": "Tennhettelot brukt i analysen",
            "message": (
                "Tennhettelot brukes som kontekst for spredning og tenning."
                if profile
                else "Tennhettelot er valgt, men mangler læringsgrunnlag."
            ),
            "checks": checks,
            "lot_number": lot_number,
        }

    def _collect_observations(self, request: LoadAnalysisRequest) -> dict[str, Any]:
        observations: dict[str, Any] = {
            "chronograph_sessions": [],
            "accuracy_tests": [],
            "pressure_signs": [],
        }
        if not request.ammo_profile_id:
            observations["summary"] = _summarize_observation_history(observations)
            return observations
        try:
            rows = self.db.execute_query(
                """
                SELECT *
                FROM chronograph_sessions
                WHERE ammo_profile_id = ?
                ORDER BY datetime(session_date) DESC, id DESC
                LIMIT 10
                """,
                (request.ammo_profile_id,),
            )
        except Exception:
            rows = []
        observations["chronograph_sessions"] = [dict(row) for row in rows or []]
        try:
            rows = self.db.execute_query(
                """
                SELECT *
                FROM rifle_accuracy_tests
                WHERE ammo_profile_id = ?
                ORDER BY datetime(test_date) DESC, id DESC
                LIMIT 10
                """,
                (request.ammo_profile_id,),
            )
        except Exception:
            rows = []
        observations["accuracy_tests"] = [dict(row) for row in rows or []]
        try:
            rows = self.db.execute_query(
                """
                SELECT *
                FROM pressure_signs
                WHERE ammo_profile_id = ?
                ORDER BY datetime(date) DESC, id DESC
                LIMIT 10
                """,
                (request.ammo_profile_id,),
            )
        except Exception:
            rows = []
        observations["pressure_signs"] = [dict(row) for row in rows or []]
        observations["summary"] = _summarize_observation_history(observations)
        return observations

    def analyze_load(
        self, request: LoadAnalysisRequest | dict[str, Any]
    ) -> dict[str, Any]:
        if isinstance(request, dict):
            request = LoadAnalysisRequest(**request)

        rifle, bullet, powder, primer = self._resolve_reference_rows(request)
        rifle = _merge_user_overrides(rifle, request.rifle_overrides)
        bullet = _merge_user_overrides(bullet, request.bullet_overrides)
        powder = _merge_user_overrides(powder, request.powder_overrides)
        primer = _merge_user_overrides(primer, request.primer_overrides)
        bullet = _resolve_bullet_profile(bullet)
        bullet, bullet_lot_context = self._apply_bullet_lot_context(
            bullet, request.bullet_lot_id
        )
        details, barrel = self._resolve_barrel_details(
            request.rifle_id, request.barrel_id
        )
        barrel = _merge_user_overrides(barrel, request.barrel_overrides)
        environment = self._build_environment(request)
        observations = self._collect_observations(request)
        powder_lot_context = self._build_powder_lot_context(request.powder_lot_id)
        primer_lot_context = self._build_primer_lot_context(request.primer_lot_id)
        primer_profile = _build_primer_profile_summary(primer, request.temperature_c)

        result = self.engine.calculate_load(
            request.rifle_id,
            request.bullet_id,
            request.powder_id,
            request.charge_weight_gr,
            request.coal_mm,
            request.cbto_mm,
            temperature_c=request.temperature_c,
            case_id=request.case_id,
            brass_batch_id=request.brass_batch_id,
            barrel_id=request.barrel_id,
        )
        if "error" in result:
            return {"error": result["error"]}

        result["charge_weight_gr"] = request.charge_weight_gr
        caliber_name = str(rifle.get("caliber") or barrel.get("caliber") or "").strip()
        weapon_type = (
            str(
                rifle.get("weapon_type")
                or barrel.get("weapon_type")
                or details.get("weapon_type")
                or "rifle"
            )
            .strip()
            .lower()
        )
        if weapon_type not in {"pistol", "revolver", "handgun"}:
            weapon_type = "rifle"
        else:
            weapon_type = "pistol"
        max_pressure_psi = get_max_pressure_psi_for_caliber(
            self.db,
            caliber_name,
            fallback_psi=_coerce_float(result.get("max_pressure_psi")),
        )

        twist_inches = _parse_twist_inches(
            barrel.get("twist") or rifle.get("twist") or details.get("twist")
        )
        harmonics = _apply_bullet_harmonic_context(
            calculate_harmonics_profile(rifle, details),
            bullet,
            twist_inches=twist_inches,
        )
        stability = _estimate_gyroscopic_stability(
            bullet=bullet,
            caliber_text=caliber_name,
            twist_inches=twist_inches,
            muzzle_velocity_fps=_coerce_float(result.get("muzzle_velocity_fps")),
            environment=environment,
        )
        bullet_geometry = _build_bullet_geometry_summary(bullet, twist_inches)
        node_fit = _build_node_fit_summary(harmonics, bullet, observations)
        stability_assessment = _summarize_stability_advisor(
            stability=stability,
            result=result,
            subsonic_mode=request.subsonic_mode,
            twist_inches=twist_inches,
            bullet=bullet,
            barrel_details=barrel,
            rifle_data=rifle,
        )
        bullet_fit_summary = build_bullet_fit_summary(
            bullet=bullet,
            bullet_geometry=bullet_geometry,
            stability=stability,
            stability_assessment=stability_assessment,
            harmonics=harmonics,
            twist_inches=twist_inches,
            result=result,
        )

        case_row = (
            self.db.get_by_id("cases", request.case_id) if request.case_id else {}
        )
        case_row = _merge_user_overrides(dict(case_row or {}), request.case_overrides)
        case_measurements = (
            barrel.get("case_measurements") or details.get("case_measurements") or {}
        )
        case_capacity_gr_h2o = _coerce_float(
            case_measurements.get("h2o_capacity_grains")
            or case_measurements.get("h2o_capacity_gr_h2o")
            or rifle.get("case_capacity_gr_h2o")
        )
        case_capacity_ml = _coerce_float(case_measurements.get("case_capacity_ml"))
        barrel_length_in = _coerce_float(rifle.get("barrel_length_inches"))
        if barrel_length_in is None:
            barrel_length_mm = _coerce_float(
                barrel.get("length_mm") or rifle.get("barrel_length_mm")
            )
            if barrel_length_mm is not None:
                barrel_length_in = barrel_length_mm / 25.4

        burn_rate_position = str(powder.get("burn_rate") or "").strip().lower() or None
        internal_ballistics = build_internal_ballistics_summary(
            charge_weight_gr=request.charge_weight_gr,
            powder_name=str(powder.get("name") or ""),
            case_capacity_gr_h2o=case_capacity_gr_h2o,
            case_capacity_ml=case_capacity_ml,
            barrel_length_in=barrel_length_in,
            load_density_percent=_coerce_float(result.get("load_density_percent")),
            powder_density_g_ml=_coerce_float(powder.get("density_gcc")),
            burn_rate_position=burn_rate_position,
            qex_kj_per_kg=_coerce_float(
                _merge_first_nonempty(powder.get("qex_kj_per_kg"), powder.get("Qex"))
            ),
            k_ratio=_coerce_float(
                _merge_first_nonempty(
                    powder.get("k_ratio"), powder.get("k"), powder.get("k_value")
                )
            ),
            temp_stable=powder.get("temp_stable"),
            validation_status=_clean_label(
                _merge_first_nonempty(
                    powder.get("validation_status"), powder.get("evidence_level")
                )
            ),
            usable_for_simulation=powder.get("usable_for_simulation"),
            pressure_margin_percent=_coerce_float(result.get("safety_margin_percent")),
        )
        brass_context = _build_brass_context_summary(
            barrel_details=barrel,
            case_row=dict(case_row or {}),
            internal_ballistics=internal_ballistics,
        )
        barrel_context = _build_barrel_context_summary(
            rifle=rifle,
            barrel_details=barrel,
            twist_inches=twist_inches,
            stability=stability,
        )

        input_quality = build_input_quality_summary(
            {
                "rifle_id": request.rifle_id,
                "bullet_id": request.bullet_id,
                "created_date": None,
            },
            observations,
            bullet_data=bullet,
            environment=environment,
        )

        drag_choice = resolve_drag_choice(
            bullet.get("bc_g1"),
            bullet.get("bc_g7"),
            preferred_drag_model(),
            bullet.get("bc_segments_json"),
            velocity_fps=_coerce_float(result.get("muzzle_velocity_fps")),
        )
        bc_value = _coerce_float(drag_choice.get("bc_value"))
        target_distance_m = _usage_target_distance(
            request.usage_profile, request.target_distance_m
        )
        zero_distance_m = request.zero_distance_m or 100.0

        external_ballistics: dict[str, Any] = {}
        terminal_summary: dict[str, Any] = {}
        if bc_value is not None:
            try:
                trajectory = self.advanced_engine.calculate_trajectory(
                    velocity_fps=float(result["muzzle_velocity_fps"]),
                    bc=bc_value,
                    weight_grains=float(
                        bullet.get("weight_grains") or bullet.get("weight") or 0.0
                    ),
                    zero_distance_m=zero_distance_m,
                    max_distance_m=max(target_distance_m, zero_distance_m),
                    step_size_m=10.0,
                    bc_type=str(drag_choice.get("resolved_model") or "G7"),
                    conditions=AtmosphericConditions(
                        temperature_f=environment.temperature_c * 9.0 / 5.0 + 32.0,
                        pressure_inhg=environment.pressure_hpa * 0.0295299831,
                        humidity_percent=environment.humidity_percent,
                        altitude_ft=environment.altitude_m * 3.28084,
                    ),
                    wind_speed_mph=environment.wind_speed_mps * 2.23694,
                    wind_angle_deg=environment.wind_dir_deg,
                    twist_rate=twist_inches or 10.0,
                    twist_direction=str(
                        barrel.get("rifling_direction") or "RIGHT"
                    ).upper(),
                )
                point = self.advanced_engine.get_drop_at_distance(
                    trajectory, target_distance_m
                )
                if point is not None:
                    external_ballistics = {
                        "drag_model": str(drag_choice.get("resolved_model") or "AUTO"),
                        "bc_value": bc_value,
                        "target_distance_m": target_distance_m,
                        "drop_cm": point.drop_cm,
                        "drop_moa": point.drop_moa,
                        "drop_mrad": point.drop_mrad,
                        "windage_cm": point.windage_cm,
                        "windage_moa": point.windage_moa,
                        "windage_mrad": point.windage_mrad,
                        "impact_velocity_fps": point.velocity_fps,
                        "impact_energy_ftlbs": point.energy_ftlbs,
                        "time_of_flight_s": point.time_s,
                    }
                    terminal_summary = _build_terminal_summary(
                        usage_profile=request.usage_profile,
                        target_distance_m=target_distance_m,
                        impact_velocity_fps=point.velocity_fps,
                        impact_energy_ftlbs=point.energy_ftlbs,
                        bullet=bullet,
                    )
            except Exception:
                external_ballistics = {}
                terminal_summary = {
                    "level": "unknown",
                    "title": "External ballistics unavailable",
                    "message": "Klarte ikke bygge trajectory for valgt konfigurasjon.",
                }

        pressure_assessment = _summarize_pressure_risk(result, max_pressure_psi)
        game_suitability_summary = build_game_suitability_summary(
            usage_profile=request.usage_profile,
            terminal_summary=terminal_summary,
        )
        obs_summary = (
            observations.get("summary")
            if isinstance(observations.get("summary"), dict)
            else {}
        )
        recommendation = _recommendation_window(
            result=result,
            harmonics=harmonics,
            pressure_assessment=pressure_assessment,
            stability_assessment=stability_assessment,
            internal_ballistics=internal_ballistics,
            terminal_summary=terminal_summary,
            input_quality=input_quality,
            observation_summary=obs_summary,
            usage_profile=request.usage_profile,
            subsonic_mode=request.subsonic_mode,
            bullet=bullet,
            primer=primer,
            bullet_lot_context=bullet_lot_context,
            powder_lot_context=powder_lot_context,
            primer_lot_context=primer_lot_context,
        )
        override_labels = []
        if isinstance(request.bullet_overrides, dict) and request.bullet_overrides:
            override_labels.append("kule")
        if isinstance(request.powder_overrides, dict) and request.powder_overrides:
            override_labels.append("krutt")
        if isinstance(request.primer_overrides, dict) and request.primer_overrides:
            override_labels.append("tennhette")
        if isinstance(request.case_overrides, dict) and request.case_overrides:
            override_labels.append("brass")
        if isinstance(request.barrel_overrides, dict) and request.barrel_overrides:
            override_labels.append("pipe")
        if recommendation.get("notes") is not None:
            if override_labels:
                recommendation["notes"].append(
                    "Brukerdata overstyrer masterdata for: "
                    + ", ".join(override_labels)
                    + "."
                )
            if bullet_lot_context.get("level") in {"ok", "info"}:
                recommendation["notes"].append(bullet_lot_context.get("message"))
            if powder_lot_context.get("level") in {"ok", "info", "warning"}:
                recommendation["notes"].append(powder_lot_context.get("message"))
            if primer_lot_context.get("level") in {"ok", "info"}:
                recommendation["notes"].append(primer_lot_context.get("message"))
            if primer_profile.get("notes"):
                recommendation["notes"].extend(primer_profile.get("notes"))
            if int(obs_summary.get("chrono_count") or 0) >= 2:
                recommendation["notes"].append(
                    "Historiske chrono-data finnes og kan brukes til å bekrefte charge-vinduet."
                )
            if int(obs_summary.get("accuracy_count") or 0) >= 1:
                recommendation["notes"].append(
                    "Historiske presisjonstester finnes og bør brukes når noden skal låses."
                )
            if brass_context.get("level") == "warning":
                recommendation["notes"].append(
                    "Brass-baselinen viser høy variasjon. Tolkningsmarginen på små forskjeller bør være større."
                )
            elif brass_context.get("level") == "ok":
                recommendation["notes"].append(
                    "Målt brass-baseline finnes og styrker internballistikk og seating-vurdering."
                )
            if terminal_summary.get("level") in {
                "warning",
                "critical",
            } and terminal_summary.get("message"):
                recommendation["notes"].append(
                    "Projectile fit: " + str(terminal_summary.get("message")).strip()
                )
            else:
                projectile_profile = (
                    terminal_summary.get("projectile_profile")
                    if isinstance(terminal_summary.get("projectile_profile"), dict)
                    else {}
                )
                projectile_summary = str(
                    projectile_profile.get("profile_summary") or ""
                ).strip()
                if projectile_summary:
                    recommendation["notes"].append(
                        "Projectile fit: " + projectile_summary + "."
                    )
            if internal_ballistics.get("level") == "critical":
                recommendation["notes"].append(
                    "Internballistikken peker mot hoy risiko i fyllingsgrad, kompresjon eller forbrenning. Hold teststeg små."
                )
            elif internal_ballistics.get("level") == "warning":
                recommendation["notes"].append(
                    "Internballistikken viser at fyllingsgrad, forbrenning eller temperaturrespons bør bekreftes i praksis."
                )
            if barrel_context.get("muzzle_device_type") == "suppressor":
                recommendation["notes"].append(
                    "Demper i pipeprofilen bør tas med når node og stabilitet verifiseres."
                )
            if barrel_context.get("level") == "ok":
                recommendation["notes"].append(
                    "Pipeprofilen har nok data til å gi bedre harmonikk- og stabilitetsvurdering."
                )
            if weapon_type == "pistol":
                recommendation["notes"].append(
                    "Pistol registrert: prioriter funksjon, praktisk presisjon, ES/SD og trygg hastighet. Rifleharmonikk og langholdslogikk er mindre styrende."
                )

        return {
            "request": asdict(request),
            "rifle": rifle,
            "barrel": barrel,
            "case": dict(case_row or {}),
            "bullet": bullet,
            "bullet_geometry": bullet_geometry,
            "powder": powder,
            "primer": primer,
            "primer_profile": primer_profile,
            "bullet_lot_context": bullet_lot_context,
            "powder_lot_context": powder_lot_context,
            "primer_lot_context": primer_lot_context,
            "environment": environment.summary(),
            "result": result,
            "harmonics": harmonics,
            "node_fit": node_fit,
            "stability": stability,
            "pressure_assessment": pressure_assessment,
            "stability_assessment": stability_assessment,
            "bullet_fit_summary": bullet_fit_summary,
            "barrel_context": barrel_context,
            "brass_context": brass_context,
            "internal_ballistics": internal_ballistics,
            "input_quality": input_quality,
            "external_ballistics": external_ballistics,
            "terminal_summary": terminal_summary,
            "game_suitability_summary": game_suitability_summary,
            "recommendation": recommendation,
            "observations": observations,
            "meta": {
                "weapon_type": weapon_type,
                "max_pressure_psi": max_pressure_psi,
                "drag_choice": dict(drag_choice),
                "has_brass_baseline": bool(case_measurements),
                "has_case_row": bool(case_row),
                "has_pipe_history": bool(observations.get("chronograph_sessions")),
                "bullet_geometry_confidence": bullet.get("geometry_confidence"),
                "user_override_fields": override_labels,
            },
        }


def predict_poi_shift(
    reference: dict[str, Any],
    new_load: dict[str, Any],
    target_distance_m: float,
    env: BallisticEnvironment | None,
):
    """Predict the point of impact shift when changing load."""
    env = env or BallisticEnvironment()
    reference_drop = _coerce_float((reference or {}).get("drop_cm"))
    reference_wind = _coerce_float((reference or {}).get("windage_cm"))
    new_drop = _coerce_float((new_load or {}).get("drop_cm"))
    new_wind = _coerce_float((new_load or {}).get("windage_cm"))
    if None in {reference_drop, reference_wind, new_drop, new_wind}:
        return None
    return {
        "target_distance_m": target_distance_m,
        "drop_shift_cm": round(float(new_drop) - float(reference_drop), 2),
        "wind_shift_cm": round(float(new_wind) - float(reference_wind), 2),
        "environment": env.summary(),
    }


def generate_dope_table(
    zero: float,
    ballistics: dict[str, Any],
    distances: list[float],
    env: BallisticEnvironment | None,
):
    """Generate a simple DOPE table from a base ballistic solution."""
    env = env or BallisticEnvironment()
    impact_velocity = _coerce_float(ballistics.get("impact_velocity_fps"))
    drop_moa = _coerce_float(ballistics.get("drop_moa"))
    wind_moa = _coerce_float(ballistics.get("windage_moa"))
    if impact_velocity is None or drop_moa is None or wind_moa is None:
        return []
    rows = []
    base_distance = max(
        _coerce_float(ballistics.get("target_distance_m")) or 100.0, 1.0
    )
    for distance in distances:
        scale = float(distance) / base_distance
        rows.append(
            {
                "distance_m": float(distance),
                "elevation_moa": round(drop_moa * scale, 2),
                "windage_moa": round(wind_moa * scale, 2),
                "impact_velocity_fps": round(
                    max(0.0, impact_velocity - (scale - 1.0) * 120.0), 1
                ),
                "environment": env.summary(),
            }
        )
    return rows


def analyze_load(
    request: LoadAnalysisRequest | dict[str, Any], db: Any | None = None
) -> dict[str, Any]:
    """Convenience wrapper around LoadAnalysisService."""
    return LoadAnalysisService(db=db).analyze_load(request)
