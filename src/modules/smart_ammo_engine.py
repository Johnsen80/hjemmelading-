from __future__ import annotations

from typing import Any

from ..ballistics.services import (
    _build_bullet_geometry_summary,
    _estimate_gyroscopic_stability,
    _parse_twist_inches,
    build_bullet_fit_summary,
)
from ..tools.evidence_quality_service import cap_evidence_level, score_to_level
from ..utils.barrel_configuration import (
    load_rifle_profile_details,
    resolve_active_barrel_configuration_context,
)
from ..utils.environment import BallisticEnvironment
from ..utils.internal_ballistics import build_internal_ballistics_summary
from ..utils.rifle_harmonics import calculate_harmonics_profile


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except Exception:
        return None


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _clean_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _query_single_row(
    database: Any, query: str, params: tuple[Any, ...]
) -> dict[str, Any]:
    try:
        rows = database.execute_query(query, params)
    except Exception:
        return {}
    return dict(rows[0]) if rows else {}


def _resolve_profile_barrel_details(
    profile_details: dict[str, Any], barrel_id: Any, barrel_name: Any
) -> dict[str, Any]:
    target_id = _clean_text(barrel_id)
    target_name = _clean_text(barrel_name)
    for barrel in _list(profile_details.get("barrels")):
        if not isinstance(barrel, dict):
            continue
        barrel_dict = dict(barrel)
        candidate_id = _clean_text(barrel_dict.get("id"))
        candidate_name = _clean_text(barrel_dict.get("name"))
        if target_id and candidate_id == target_id:
            return barrel_dict
        if target_name and candidate_name == target_name:
            return barrel_dict
    return {}


def _normalize_burn_rate_position(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if text in {"fast", "medium", "slow"}:
        return text
    numeric = _safe_float(value)
    if numeric is None:
        return None
    if numeric <= 85:
        return "fast"
    if numeric >= 165:
        return "slow"
    return "medium"


def _case_capacity_h2o(
    *,
    case_row: dict[str, Any],
    case_learning: dict[str, Any],
    profile_details: dict[str, Any],
) -> float | None:
    case_measurements = _dict(profile_details.get("case_measurements"))
    for candidate in (
        case_learning.get("avg_case_capacity_h2o"),
        case_row.get("case_capacity_gr_h2o"),
        case_measurements.get("case_capacity_gr_h2o"),
        case_measurements.get("avg_case_capacity_h2o"),
    ):
        resolved = _safe_float(candidate)
        if resolved is not None:
            return resolved
    return None


def _case_capacity_ml(
    *,
    case_row: dict[str, Any],
    case_capacity_h2o: float | None,
    raw_internal_ballistics: dict[str, Any],
    profile_details: dict[str, Any],
) -> float | None:
    case_measurements = _dict(profile_details.get("case_measurements"))
    for candidate in (
        raw_internal_ballistics.get("case_capacity_ml"),
        case_measurements.get("case_capacity_ml"),
        case_row.get("case_capacity_ml"),
    ):
        resolved = _safe_float(candidate)
        if resolved is not None:
            return resolved
    if case_capacity_h2o is None:
        return None
    return round(case_capacity_h2o * 0.0648, 4)


def _barrel_length_mm(
    *,
    barrel_row: dict[str, Any],
    rifle_row: dict[str, Any],
    profile_details: dict[str, Any],
) -> float | None:
    for candidate in (
        barrel_row.get("length_mm"),
        profile_details.get("barrel_length_mm"),
        rifle_row.get("barrel_length_mm"),
        rifle_row.get("barrel_length"),
    ):
        resolved = _safe_float(candidate)
        if resolved is not None:
            return resolved
    return None


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _build_lot_learning_summary(
    lots: dict[str, Any], learning: dict[str, Any]
) -> dict[str, Any]:
    learned_lots = _dict(learning.get("lots"))
    component_entries: list[dict[str, Any]] = []
    caution_count = 0
    active_count = 0

    for name in ("bullet", "powder", "primer", "case"):
        lot_row = _dict(lots.get(name))
        if not lot_row:
            continue
        active_count += 1
        learning_profile = _dict(lot_row.get("learning_profile"))
        confidence_label = (
            _clean_text(learning_profile.get("confidence_label"))
            or _clean_text(learning_profile.get("model_status"))
            or _clean_text(learned_lots.get(f"{name}_confidence_label"))
            or "unknown"
        )
        drift_flag = bool(
            learning_profile.get("drift_flag")
            or learning_profile.get("watch_flag")
            or learning_profile.get("change_sensitive")
        )
        if drift_flag or confidence_label in {"low", "thin", "watch"}:
            caution_count += 1
        component_entries.append(
            {
                "component": name,
                "lot_number": _clean_text(lot_row.get("lot_number")),
                "confidence_label": confidence_label,
                "drift_flag": drift_flag,
            }
        )

    status = (
        "stable"
        if component_entries and caution_count == 0
        else "watch" if caution_count else "unresolved"
    )
    return {
        "status": status,
        "active_lot_count": active_count,
        "watch_count": caution_count,
        "components": component_entries,
    }


def _alignment_state(
    current: float | None, baseline: float | None, tolerance: float
) -> tuple[str, float | None]:
    if current is None or baseline is None:
        return "unknown", None
    delta = round(current - baseline, 2)
    return ("aligned" if abs(delta) <= tolerance else "outside"), delta


def _resolve_bullet_row(
    database: Any,
    components: dict[str, Any],
) -> dict[str, Any]:
    bullet_row = _dict(components.get("bullet"))
    bullet_id = _safe_int(bullet_row.get("id"))
    if bullet_id is None:
        return bullet_row
    database_row = _query_single_row(
        database,
        "SELECT * FROM bullets WHERE id = ? LIMIT 1",
        (bullet_id,),
    )
    if not database_row:
        return bullet_row
    merged = dict(database_row)
    merged.update(
        {
            key: value
            for key, value in bullet_row.items()
            if value not in (None, "", [], {})
        }
    )
    if "id" not in merged:
        merged["id"] = bullet_id
    return merged


def _resolve_seating_depth_context(
    *,
    database: Any,
    rifle_id: int | None,
    barrel_id: str | None,
    bullet_row: dict[str, Any],
    lot_row: dict[str, Any],
    current_cbto_mm: float | None,
    current_coal_mm: float | None,
    current_temperature_c: float | None,
) -> dict[str, Any]:
    if rifle_id is None:
        return {}
    bullet_id = _safe_int(bullet_row.get("id"))
    if bullet_id is None:
        return {}
    component_lot_id = _safe_int(
        lot_row.get("id")
        or bullet_row.get("selected_lot_id")
        or bullet_row.get("component_lot_id")
    )
    selected_lot_number = _clean_text(
        lot_row.get("lot_number")
        or bullet_row.get("selected_lot_number")
        or bullet_row.get("lot_number")
    )

    seating_profile = {}
    best_evidence = {}
    jump_row = {}
    try:
        seating_profile = (
            database.get_seating_depth_profile(
                rifle_id,
                bullet_id,
                component_lot_id,
                barrel_id or None,
            )
            or {}
        )
    except Exception:
        seating_profile = {}
    try:
        best_evidence = (
            database.get_best_seating_depth_evidence(
                rifle_id,
                bullet_id,
                component_lot_id,
                selected_lot_number,
                current_temperature_c,
                None,
                None,
                barrel_id or None,
                include_ranked=True,
            )
            or {}
        )
    except Exception:
        best_evidence = {}
    try:
        resolved_barrel_id = str(barrel_id or "").strip()
        rows = database.execute_query(
            """
            SELECT *
            FROM rifle_bullet_jump_measurements
            WHERE rifle_id = ? AND bullet_id = ?
              AND (? = '' OR COALESCE(barrel_id, '') = ?)
            ORDER BY CASE WHEN COALESCE(barrel_id, '') = ? THEN 0 ELSE 1 END,
                     CASE WHEN barrel_id IS NULL OR barrel_id = '' THEN 0 ELSE 1 END,
                     measurement_date DESC
            LIMIT 1
            """,
            (
                rifle_id,
                bullet_id,
                resolved_barrel_id,
                resolved_barrel_id,
                resolved_barrel_id,
            ),
        )
        jump_row = dict(rows[0]) if rows else {}
    except Exception:
        jump_row = {}

    jam_cbto_mm = _safe_float(
        _first_nonempty(
            jump_row.get("jam_cbto_mm"),
            seating_profile.get("jam_cbto_mm"),
            bullet_row.get("jam_length_cbto_mm"),
        )
    )
    preferred_jump_mm = _safe_float(
        _first_nonempty(
            seating_profile.get("preferred_jump_mm"),
            bullet_row.get("optimal_jump_mm"),
        )
    )
    preferred_cbto_mm = _safe_float(
        _first_nonempty(
            seating_profile.get("preferred_cbto_mm"),
            best_evidence.get("cbto_mm"),
        )
    )
    current_jump_mm = (
        round(float(jam_cbto_mm) - float(current_cbto_mm), 3)
        if jam_cbto_mm is not None and current_cbto_mm is not None
        else None
    )
    if current_jump_mm is None:
        jump_band = "unknown"
    elif current_jump_mm < 0:
        jump_band = "into_lands"
    elif current_jump_mm < 0.10:
        jump_band = "very_close"
    elif current_jump_mm < 0.35:
        jump_band = "tight"
    elif current_jump_mm <= 1.20:
        jump_band = "working_window"
    else:
        jump_band = "long_jump"

    return {
        "seating_profile": seating_profile,
        "best_evidence": best_evidence,
        "jump_measurement": jump_row,
        "jam_cbto_mm": jam_cbto_mm,
        "preferred_jump_mm": preferred_jump_mm,
        "preferred_cbto_mm": preferred_cbto_mm,
        "current_jump_mm": current_jump_mm,
        "current_cbto_mm": current_cbto_mm,
        "current_coal_mm": current_coal_mm,
        "jump_band": jump_band,
        "status": (
            "known"
            if current_jump_mm is not None
            or preferred_jump_mm is not None
            or preferred_cbto_mm is not None
            else "unresolved"
        ),
        "source_label": (
            "measured profile"
            if seating_profile
            else (
                "best evidence"
                if best_evidence
                else "jump measurement" if jump_row else "unresolved"
            )
        ),
    }


def _resolve_velocity_fps(
    raw_internal_ballistics: dict[str, Any],
    internal_ballistics_summary: dict[str, Any],
) -> float | None:
    for candidate in (
        raw_internal_ballistics.get("muzzle_velocity_fps"),
        raw_internal_ballistics.get("velocity_fps"),
        raw_internal_ballistics.get("predicted_velocity_fps"),
        internal_ballistics_summary.get("muzzle_velocity_fps"),
        internal_ballistics_summary.get("velocity_fps"),
    ):
        resolved = _safe_float(candidate)
        if resolved is not None:
            return resolved
    for candidate in (
        raw_internal_ballistics.get("muzzle_velocity_mps"),
        raw_internal_ballistics.get("velocity_mps"),
        internal_ballistics_summary.get("muzzle_velocity_mps"),
        internal_ballistics_summary.get("velocity_mps"),
    ):
        resolved = _safe_float(candidate)
        if resolved is not None:
            return round(resolved * 3.28084, 1)
    return None


def _build_bullet_fit_context(
    *,
    bullet_row: dict[str, Any],
    weapon: dict[str, Any],
    profile_barrel: dict[str, Any],
    runtime_rifle: dict[str, Any],
    environment_data: dict[str, Any],
    harmonics_profile: dict[str, Any],
    internal_ballistics_summary: dict[str, Any],
    raw_internal_ballistics: dict[str, Any],
) -> dict[str, Any]:
    twist_inches = _parse_twist_inches(
        _first_nonempty(
            profile_barrel.get("twist"),
            profile_barrel.get("twist_rate"),
            runtime_rifle.get("twist_rate"),
            runtime_rifle.get("twist"),
        )
    )
    bullet_geometry = _build_bullet_geometry_summary(bullet_row, twist_inches)
    environment = BallisticEnvironment(
        temperature_c=_safe_float(environment_data.get("temperature_c")) or 15.0,
        pressure_hpa=_safe_float(environment_data.get("pressure_hpa")) or 1013.25,
        humidity_percent=_safe_float(environment_data.get("humidity_percent")) or 50.0,
        altitude_m=_safe_float(environment_data.get("altitude_m")) or 0.0,
    )
    velocity_fps = _resolve_velocity_fps(
        raw_internal_ballistics, internal_ballistics_summary
    )
    stability = _estimate_gyroscopic_stability(
        bullet=bullet_row,
        caliber_text=str(weapon.get("caliber") or "").strip(),
        twist_inches=twist_inches,
        muzzle_velocity_fps=velocity_fps,
        environment=environment,
    )
    fit_summary = build_bullet_fit_summary(
        bullet=bullet_row,
        bullet_geometry=bullet_geometry,
        stability=stability,
        stability_assessment={},
        harmonics=harmonics_profile,
        twist_inches=twist_inches,
        result={"muzzle_velocity_fps": velocity_fps},
    )
    return {
        "twist_inches": twist_inches,
        "bullet_geometry": bullet_geometry,
        "stability": stability,
        "fit_summary": fit_summary,
    }


def _build_enriched_engine_input(
    database: Any,
    runtime: dict[str, Any],
    engine_input: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(engine_input)
    weapon = _dict(payload.get("weapon"))
    barrel = _dict(payload.get("barrel"))
    components = _dict(payload.get("components"))
    load = _dict(payload.get("load"))
    physics_inputs = _dict(payload.get("physics_inputs"))
    learning = _dict(payload.get("learning"))

    rifle_id = _safe_int(weapon.get("rifle_id"))
    profile_details = load_rifle_profile_details(database, rifle_id)
    runtime_rifle = _dict(runtime.get("rifle"))
    profile_barrel = _resolve_profile_barrel_details(
        profile_details, barrel.get("barrel_id"), barrel.get("barrel_name")
    )

    barrel_context = resolve_active_barrel_configuration_context(
        db=database,
        rifle_id=rifle_id,
        rifle_data=runtime_rifle,
        profile_details=profile_details,
        active_barrel_details=profile_barrel or None,
    )

    harmonics_profile: dict[str, Any] = {}
    try:
        harmonics_profile = calculate_harmonics_profile(runtime_rifle, profile_details)
    except Exception:
        harmonics_profile = {}

    powder_row = _dict(components.get("powder"))
    case_row = _dict(components.get("case"))
    bullet_row = _resolve_bullet_row(database, components)
    case_learning = _dict(learning.get("case"))
    raw_internal_ballistics = _dict(physics_inputs.get("internal_ballistics"))
    raw_pressure_assessment = _dict(physics_inputs.get("pressure_assessment"))
    case_capacity_h2o = _case_capacity_h2o(
        case_row=case_row,
        case_learning=case_learning,
        profile_details=profile_details,
    )
    case_capacity_ml = _case_capacity_ml(
        case_row=case_row,
        case_capacity_h2o=case_capacity_h2o,
        raw_internal_ballistics=raw_internal_ballistics,
        profile_details=profile_details,
    )
    barrel_length_mm = _barrel_length_mm(
        barrel_row=profile_barrel,
        rifle_row=runtime_rifle,
        profile_details=profile_details,
    )

    powder_database = {}
    powder_id = _safe_int(powder_row.get("id"))
    if powder_id is not None:
        powder_database = _query_single_row(
            database,
            "SELECT * FROM powder_database WHERE powder_id = ? LIMIT 1",
            (powder_id,),
        )

    internal_ballistics_summary: dict[str, Any] = {}
    try:
        internal_ballistics_summary = build_internal_ballistics_summary(
            charge_weight_gr=_safe_float(load.get("charge_weight_gr")),
            powder_name=_clean_text(powder_row.get("name")),
            case_capacity_gr_h2o=case_capacity_h2o,
            case_capacity_ml=case_capacity_ml,
            barrel_length_in=(
                round(float(barrel_length_mm) / 25.4, 2)
                if barrel_length_mm is not None
                else None
            ),
            load_density_percent=_safe_float(
                _first_nonempty(
                    raw_internal_ballistics.get("load_density_percent"),
                    raw_internal_ballistics.get("fill_ratio_percent"),
                )
            ),
            powder_density_g_ml=_safe_float(
                _first_nonempty(
                    powder_database.get("density_gcc"),
                    powder_row.get("density"),
                )
            ),
            burn_rate_position=_normalize_burn_rate_position(
                _first_nonempty(
                    powder_database.get("peak_pressure_timing"),
                    powder_row.get("burn_rate"),
                    powder_database.get("burn_rate_position"),
                )
            ),
            qex_kj_per_kg=_safe_float(powder_database.get("qex_kj_per_kg")),
            k_ratio=_safe_float(powder_database.get("k_ratio")),
            temp_stable=powder_database.get("temp_stable"),
            validation_status=_clean_text(powder_database.get("validation_status")),
            usable_for_simulation=powder_database.get("usable_for_simulation"),
            pressure_margin_percent=_safe_float(
                _first_nonempty(
                    raw_pressure_assessment.get("safety_margin_percent"),
                    raw_internal_ballistics.get("pressure_margin_percent"),
                )
            ),
        )
    except Exception:
        internal_ballistics_summary = {}

    seating_depth_context = _resolve_seating_depth_context(
        database=database,
        rifle_id=rifle_id,
        barrel_id=_clean_text(barrel.get("barrel_id")),
        bullet_row=bullet_row,
        lot_row=_dict(_dict(payload.get("lots")).get("bullet")),
        current_cbto_mm=_safe_float(load.get("cbto_mm")),
        current_coal_mm=_safe_float(load.get("coal_mm")),
        current_temperature_c=_safe_float(
            _dict(payload.get("environment")).get("temperature_c")
        ),
    )
    bullet_fit_context = _build_bullet_fit_context(
        bullet_row=bullet_row,
        weapon=weapon,
        profile_barrel=profile_barrel,
        runtime_rifle=runtime_rifle,
        environment_data=_dict(payload.get("environment")),
        harmonics_profile=harmonics_profile,
        internal_ballistics_summary=internal_ballistics_summary,
        raw_internal_ballistics=raw_internal_ballistics,
    )

    payload["derived"] = {
        "profile_details": profile_details,
        "profile_available": bool(profile_details),
        "barrel_configuration_context": barrel_context,
        "profile_barrel": profile_barrel,
        "harmonics_profile": harmonics_profile,
        "internal_ballistics_summary": internal_ballistics_summary,
        "bullet_row": bullet_row,
        "bullet_fit_context": bullet_fit_context,
        "seating_depth_context": seating_depth_context,
        "powder_database": powder_database,
        "lot_learning_summary": _build_lot_learning_summary(
            _dict(payload.get("lots")), learning
        ),
        "case_capacity_gr_h2o": case_capacity_h2o,
        "case_capacity_ml": case_capacity_ml,
        "barrel_length_mm": barrel_length_mm,
    }
    return payload


def _component_label(row: dict[str, Any]) -> str | None:
    manufacturer = _clean_text(row.get("manufacturer") or row.get("make"))
    model_name = _clean_text(row.get("name") or row.get("type"))
    label = " ".join(bit for bit in (manufacturer, model_name) if bit).strip()
    return label or None


def _normalize_component_context(
    components: dict[str, Any],
) -> dict[str, Any]:
    selection = _dict(components.get("selection"))
    case_learning_profile = _dict(components.get("case_learning_profile"))
    normalized: dict[str, Any] = {
        "selection": selection,
        "case_learning_profile": case_learning_profile,
    }
    active_count = 0
    available_count = 0

    for name in ("bullet", "powder", "primer", "case"):
        raw = _dict(components.get(name))
        selected_id = _safe_int(selection.get(f"{name}_id"))
        resolved_id = _safe_int(raw.get("id") or selected_id)
        resolved = dict(raw)
        if resolved_id is not None:
            resolved["id"] = resolved_id
            active_count += 1
        if raw:
            available_count += 1
        resolved["label"] = _component_label(resolved)
        resolved["selected"] = resolved_id is not None
        resolved["selected_id"] = selected_id
        resolved["status"] = (
            "selected"
            if resolved_id is not None and raw
            else "selected_unresolved" if resolved_id is not None else "unselected"
        )
        normalized[name] = resolved

    normalized["active_component_count"] = active_count
    normalized["available_component_count"] = available_count
    normalized["status"] = (
        "known"
        if active_count >= 3 and available_count >= 3
        else "partial" if active_count or available_count else "unresolved"
    )
    return normalized


def _normalize_lot_context(lots: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    active_count = 0
    watch_count = 0

    for name in ("bullet", "powder", "primer", "case"):
        raw = _dict(lots.get(name))
        learning_profile = _dict(raw.get("learning_profile"))
        lot_number = _clean_text(raw.get("lot_number"))
        lot_id = _safe_int(raw.get("id"))
        watch_flag = bool(
            learning_profile.get("drift_flag")
            or learning_profile.get("watch_flag")
            or learning_profile.get("change_sensitive")
        )
        if lot_id is not None or lot_number:
            active_count += 1
        if watch_flag:
            watch_count += 1
        resolved = dict(raw)
        resolved["id"] = lot_id
        resolved["lot_number"] = lot_number
        resolved["watch_flag"] = watch_flag
        resolved["confidence_label"] = _clean_text(
            learning_profile.get("confidence_label")
            or learning_profile.get("model_status")
        )
        resolved["status"] = (
            "selected" if lot_id is not None or lot_number else "unselected"
        )
        normalized[name] = resolved

    normalized["active_lot_count"] = active_count
    normalized["watch_count"] = watch_count
    normalized["status"] = (
        "watch" if watch_count else "known" if active_count else "unresolved"
    )
    return normalized


def _normalize_environment_context(
    active_settings: dict[str, Any],
    session: dict[str, Any],
) -> dict[str, Any]:
    def _env_val(key: str) -> Any:
        v = active_settings.get(key)
        return v if v is not None else session.get(key)

    temperature_c = _safe_float(_env_val("temperature_c"))
    pressure_hpa = _safe_float(_env_val("pressure_hpa"))
    humidity_percent = _safe_float(_env_val("humidity_percent"))
    altitude_m = _safe_float(_env_val("altitude_m"))
    source = (
        "active_settings"
        if any(
            active_settings.get(key) not in (None, "")
            for key in (
                "temperature_c",
                "pressure_hpa",
                "humidity_percent",
                "altitude_m",
            )
        )
        else (
            "session"
            if any(
                session.get(key) not in (None, "")
                for key in (
                    "temperature_c",
                    "pressure_hpa",
                    "humidity_percent",
                    "altitude_m",
                )
            )
            else "unresolved"
        )
    )

    summary: dict[str, Any] = {
        "temperature_c": temperature_c,
        "pressure_hpa": pressure_hpa,
        "humidity_percent": humidity_percent,
        "altitude_m": altitude_m,
        "source": source,
    }
    if None not in (temperature_c, pressure_hpa, humidity_percent, altitude_m):
        environment = BallisticEnvironment(
            temperature_c=float(temperature_c),
            pressure_hpa=float(pressure_hpa),
            humidity_percent=float(humidity_percent),
            altitude_m=float(altitude_m),
        )
        atmosphere = environment.summary()
        summary["density_ratio"] = _safe_float(atmosphere.get("density_ratio"))
        summary["density_altitude_m"] = _safe_float(
            atmosphere.get("density_altitude_m")
        )
        summary["density_altitude_ft"] = _safe_float(
            atmosphere.get("density_altitude_ft")
        )
        summary["pressure_altitude_m"] = environment.pressure_altitude_m()
        summary["status"] = "known"
    else:
        summary["density_ratio"] = None
        summary["density_altitude_m"] = None
        summary["density_altitude_ft"] = None
        summary["pressure_altitude_m"] = None
        summary["status"] = (
            "partial"
            if any(
                value is not None
                for value in (temperature_c, pressure_hpa, humidity_percent, altitude_m)
            )
            else "unresolved"
        )
    return summary


def _normalize_evidence_context(evidence: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(evidence.get("summary"))
    primer_review = _dict(evidence.get("primer_review"))
    measured = {
        "status": (
            "measured"
            if summary.get("has_measured_velocity") is True
            and summary.get("has_measured_group") is True
            else (
                "partial"
                if (
                    summary.get("has_measured_velocity") is True
                    or summary.get("has_measured_group") is True
                    or _safe_int(summary.get("chronograph_import_count"))
                    not in (None, 0)
                    or _safe_int(summary.get("test_result_count")) not in (None, 0)
                )
                else "unresolved"
            )
        ),
        "has_measured_velocity": summary.get("has_measured_velocity") is True,
        "has_measured_group": summary.get("has_measured_group") is True,
        "latest_avg_velocity_fps": _safe_float(summary.get("latest_avg_velocity_fps")),
        "best_group_mm": _safe_float(summary.get("best_group_mm")),
        "chronograph_import_count": _safe_int(summary.get("chronograph_import_count"))
        or 0,
        "test_result_count": _safe_int(summary.get("test_result_count")) or 0,
        "ladder_test_count": _safe_int(summary.get("ladder_test_count")) or 0,
        "batch_count": _safe_int(summary.get("batch_count")) or 0,
        "range_session_count": _safe_int(summary.get("range_session_count")) or 0,
        "pressure_sign_count": _safe_int(summary.get("pressure_sign_count")) or 0,
        "signal_hint": _clean_text(summary.get("batch_spread_signal_hint")),
        "evidence_level": _clean_text(
            _dict(summary.get("batch_spread_evidence_quality")).get("level")
        ),
        "evidence_score": _safe_float(
            _dict(summary.get("batch_spread_evidence_quality")).get("score")
        ),
        "primer_review_status": _clean_text(summary.get("primer_review_status")),
    }
    return {
        "status": measured["status"],
        "summary": summary,
        "primer_review": primer_review,
        "measured": measured,
    }


def _resolve_usage_goal(
    session: dict[str, Any],
    validation: dict[str, Any],
) -> str:
    validation_goal = _clean_text(validation.get("usage_goal"))
    if validation_goal:
        return validation_goal.lower()
    for candidate in (
        session.get("usage_profile_key"),
        session.get("usage_profile_name"),
    ):
        text = str(candidate or "").strip().lower()
        if not text:
            continue
        if text in {"hunting", "hunt", "jakt", "field"}:
            return "hunting"
        if text in {"competition", "match", "precision", "prs"}:
            return "competition"
        if text in {"learning", "training", "train", "development"}:
            return "learning"
    return "general"


# score_to_level and cap_evidence_level are imported from evidence_quality_service.
# Use the module-level names as aliases to avoid breaking existing call sites.
_evidence_level_from_score = score_to_level
_cap_evidence_level = cap_evidence_level


def _build_evidence_weighting(
    *,
    session: dict[str, Any],
    evidence_summary: dict[str, Any],
    validation: dict[str, Any],
    batch_spread_evidence: dict[str, Any],
    signal_hint: str,
) -> dict[str, Any]:
    has_measured_velocity = evidence_summary.get("has_measured_velocity") is True
    has_measured_group = evidence_summary.get("has_measured_group") is True
    chrono_count = _safe_int(evidence_summary.get("chronograph_import_count")) or 0
    test_result_count = _safe_int(evidence_summary.get("test_result_count")) or 0
    pressure_sign_count = _safe_int(evidence_summary.get("pressure_sign_count")) or 0
    # Shot-count robustness: a 5-shot group is worth more than a 3-shot group.
    # best_group_shot_count is the shot count for the best (smallest mm) group recorded.
    best_group_shot_count = _safe_int(evidence_summary.get("best_group_shot_count"))
    raw_level = str(batch_spread_evidence.get("level") or "").strip().lower()
    raw_score = _safe_float(batch_spread_evidence.get("score"))
    note_flags = [
        str(item).strip()
        for item in _list(evidence_summary.get("batch_spread_note_flags"))
        if str(item).strip()
    ]
    pattern_flags = [
        str(item).strip()
        for item in _list(evidence_summary.get("batch_spread_pattern_flags"))
        if str(item).strip()
    ]

    if has_measured_velocity and has_measured_group:
        matched_status = "paired"
    elif has_measured_velocity:
        matched_status = "velocity_only"
    elif has_measured_group:
        matched_status = "group_only"
    elif chrono_count or test_result_count:
        matched_status = "partial_unmatched"
    else:
        matched_status = "none"

    effective_score = raw_score
    if effective_score is None:
        effective_score = (
            62.0
            if matched_status == "paired"
            else (
                34.0
                if matched_status
                in {"velocity_only", "group_only", "partial_unmatched"}
                else 12.0
            )
        )

    effective_level = raw_level or _evidence_level_from_score(effective_score)
    if matched_status != "paired" or signal_hint in {
        "insufficient_evidence",
        "target_only",
        "velocity_only",
    }:
        effective_level = _cap_evidence_level(effective_level, "thin")
        effective_score = min(effective_score, 39.0)

    ambiguous_signal = signal_hint in {
        "ammo_or_process_signal",
        "possible_shooter_or_setup_signal",
        "setup_drift_watch",
        "environment_or_condition_signal",
    }
    mixed_signal = bool(
        ambiguous_signal
        or pressure_sign_count > 0
        or len(note_flags) + len(pattern_flags) >= 2
        or (
            note_flags
            and pattern_flags
            and signal_hint
            not in {"", "insufficient_evidence", "target_only", "velocity_only"}
        )
    )
    if mixed_signal:
        effective_level = _cap_evidence_level(effective_level, "moderate")
        effective_score = min(effective_score, 52.0)

    # Shot-count cap: cap "strong" evidence at "moderate" when best group has
    # fewer than 5 shots. A 3-shot group at 0.4 MOA must not outrank a 5-shot
    # group at 0.6 MOA. Evidence is only "strong" when the sample is large enough.
    small_sample_group = has_measured_group and (
        best_group_shot_count is not None and best_group_shot_count < 5
    )
    if small_sample_group:
        effective_level = _cap_evidence_level(effective_level, "moderate")
        effective_score = min(
            effective_score, 74.0
        )  # cap just below "strong" threshold

    usage_goal = _resolve_usage_goal(session, validation)
    cold_bore_status = "not_applicable"
    cold_bore_summary = (
        "Cold-bore validation is not a primary gate for this usage profile."
    )
    if usage_goal == "hunting":
        validation_state = str(validation.get("status") or "").strip().lower()
        if validation_state in {
            "field_validation_pending",
            "cold_bore_confirmation_pending",
        }:
            cold_bore_status = validation_state
            cold_bore_summary = str(validation.get("next_gate") or "").strip() or (
                "Confirm one cold-bore field shot and a short support-matched control group before treating the load as hunting-ready."
            )
        elif matched_status != "paired" or effective_level in {"very_thin", "thin"}:
            cold_bore_status = "evidence_pending"
            cold_bore_summary = "Hunting trust still needs matched chrono and group evidence before cold-bore behavior can be judged fairly."
        else:
            cold_bore_status = "needs_confirmation"
            cold_bore_summary = "The load looks usable, but hunting approval still depends on a documented cold-bore and realistic-support confirmation."

    group_pattern_status = "unknown"
    group_pattern_summary = "No clear group-pattern signal is available yet."
    if "vertical_dominant" in pattern_flags:
        group_pattern_status = "vertical_watch"
        group_pattern_summary = "Vertical dominance suggests node, seating, timing, or support tracking should be confirmed before a broad powder change."
    elif "horizontal_dominant" in pattern_flags:
        group_pattern_status = "horizontal_watch"
        group_pattern_summary = "Horizontal dominance suggests wind, cant, support, or condition effects should be separated before judging the load."
    elif "poi_shift_watch" in pattern_flags:
        group_pattern_status = "poi_shift_watch"
        group_pattern_summary = "Point-of-impact drift suggests setup or condition control should be confirmed before trusting the ranking."

    return {
        "status": effective_level or "unknown",
        "score": round(effective_score, 1) if effective_score is not None else None,
        "raw_status": raw_level or None,
        "raw_score": raw_score,
        "validation": validation,
        "signal_hint": signal_hint,
        "usage_goal": usage_goal,
        "matched_status": matched_status,
        "has_measured_velocity": has_measured_velocity,
        "has_measured_group": has_measured_group,
        "chrono_count": chrono_count,
        "test_result_count": test_result_count,
        "pressure_sign_count": pressure_sign_count,
        "note_flags": note_flags,
        "pattern_flags": pattern_flags,
        "cold_bore": {
            "status": cold_bore_status,
            "summary": cold_bore_summary,
        },
        "group_pattern": {
            "status": group_pattern_status,
            "summary": group_pattern_summary,
            "flags": pattern_flags,
        },
        "mixed_signal": {
            "status": "mixed_signal" if mixed_signal else "clearer_signal",
            "summary": (
                "Evidence currently mixes load data with setup, shooter, or condition signals."
                if mixed_signal
                else "The current evidence has a more isolated cause signal."
            ),
        },
        "small_sample_group": small_sample_group,
    }


def build_engine_input_from_runtime(runtime: dict[str, Any] | None) -> dict[str, Any]:
    runtime_data = runtime if isinstance(runtime, dict) else {}
    session = _dict(runtime_data.get("session"))
    context = _dict(runtime_data.get("context"))
    identity = _dict(runtime_data.get("identity"))
    recommendation = _dict(runtime_data.get("recommendation"))
    evidence = _dict(runtime_data.get("evidence"))
    learning = _dict(runtime_data.get("learning"))
    learning_aggregate = _dict(learning.get("aggregate"))
    barrel = _dict(runtime_data.get("barrel"))
    rifle = _dict(runtime_data.get("rifle"))
    components = _dict(runtime_data.get("components"))
    lots = _dict(runtime_data.get("lots"))

    active_settings = _dict(recommendation.get("active_settings"))
    baseline = _dict(recommendation.get("baseline"))
    control_state = _dict(recommendation.get("control_state"))
    pressure_assessment = _dict(recommendation.get("pressure_assessment"))
    internal_ballistics = _dict(recommendation.get("internal_ballistics"))
    component_context = _normalize_component_context(components)
    lot_context = _normalize_lot_context(lots)
    environment_context = _normalize_environment_context(active_settings, session)
    evidence_context = _normalize_evidence_context(evidence)

    return {
        "session": {
            "load_session_id": _safe_int(
                context.get("load_session_id") or session.get("id")
            ),
            "workflow_id": _safe_int(
                context.get("workflow_id") or session.get("workflow_id")
            ),
            "status": context.get("status") or session.get("status"),
            "lifecycle_stage": context.get("lifecycle_stage")
            or session.get("lifecycle_stage"),
            "usage_profile_key": context.get("usage_profile_key")
            or session.get("usage_profile_key"),
            "usage_profile_name": context.get("usage_profile_name")
            or session.get("usage_profile_name"),
            "next_action": context.get("next_action") or session.get("next_action"),
            "safety_status": context.get("safety_status")
            or session.get("safety_status"),
            "confidence_label": context.get("confidence_label")
            or session.get("confidence_label"),
            "confidence_score": _safe_float(
                context.get("confidence_score") or session.get("confidence_score")
            ),
        },
        "weapon": {
            "rifle_id": _safe_int(
                context.get("rifle_id")
                or session.get("rifle_id")
                or (identity.get("rifle") or {}).get("id")
            ),
            "rifle_name": context.get("rifle_name")
            or session.get("rifle_name")
            or (identity.get("rifle") or {}).get("label"),
            "caliber": context.get("rifle_caliber")
            or session.get("rifle_caliber")
            or (identity.get("rifle") or {}).get("caliber")
            or rifle.get("caliber"),
            "weapon_type": rifle.get("weapon_type"),
            "action_type": rifle.get("action_type"),
        },
        "barrel": {
            "barrel_id": context.get("barrel_id")
            or barrel.get("barrel_id")
            or (identity.get("barrel") or {}).get("id"),
            "barrel_name": context.get("barrel_name")
            or barrel.get("barrel_name")
            or (identity.get("barrel") or {}).get("label"),
            "barrel_configuration_id": context.get("barrel_configuration_id")
            or barrel.get("barrel_configuration_id")
            or (identity.get("barrel") or {}).get("configuration_id"),
            "barrel_configuration_name": context.get("barrel_configuration_name")
            or barrel.get("barrel_configuration_name")
            or (identity.get("barrel") or {}).get("configuration_label"),
            "learning_profile": _dict(barrel.get("learning_profile")),
            "source": barrel.get("source"),
        },
        "components": component_context,
        "lots": lot_context,
        "environment": environment_context,
        "load": {
            "charge_weight_gr": _safe_float(
                active_settings.get("charge_weight_gr") or baseline.get("charge_gr")
            ),
            "coal_mm": _safe_float(
                active_settings.get("coal_mm") or baseline.get("coal_mm")
            ),
            "cbto_mm": _safe_float(
                active_settings.get("cbto_mm") or baseline.get("cbto_mm")
            ),
            "baseline": baseline,
            "control_state": control_state,
        },
        "physics_inputs": {
            "pressure_assessment": pressure_assessment,
            "internal_ballistics": internal_ballistics,
        },
        "evidence": evidence_context,
        "learning": {
            "aggregate": learning_aggregate,
            "barrel": _dict(learning.get("barrel")),
            "case": _dict(learning.get("case")),
            "lots": _dict(learning.get("lots")),
            "session": _dict(learning.get("session")),
        },
    }


def build_engine_result_from_input(
    engine_input: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = engine_input if isinstance(engine_input, dict) else {}
    session = _dict(payload.get("session"))
    weapon = _dict(payload.get("weapon"))
    barrel = _dict(payload.get("barrel"))
    load = _dict(payload.get("load"))
    physics_inputs = _dict(payload.get("physics_inputs"))
    evidence = _dict(payload.get("evidence"))
    evidence_summary = _dict(evidence.get("summary"))
    learning = _dict(payload.get("learning"))
    learning_aggregate = _dict(learning.get("aggregate"))
    lots = _dict(payload.get("lots"))
    components = _dict(payload.get("components"))
    derived = _dict(payload.get("derived"))

    pressure_assessment = _dict(physics_inputs.get("pressure_assessment"))
    raw_internal_ballistics = _dict(physics_inputs.get("internal_ballistics"))
    internal_ballistics_summary = (
        _dict(derived.get("internal_ballistics_summary")) or raw_internal_ballistics
    )
    harmonics_profile = _dict(derived.get("harmonics_profile"))
    barrel_context = _dict(derived.get("barrel_configuration_context"))
    bullet_fit_context = _dict(derived.get("bullet_fit_context"))
    bullet_fit_summary = _dict(bullet_fit_context.get("fit_summary"))
    seating_depth_context = _dict(derived.get("seating_depth_context"))
    lot_learning_summary = _dict(derived.get("lot_learning_summary"))
    barrel_learning = _dict(barrel.get("learning_profile"))
    batch_spread_evidence = _dict(evidence_summary.get("batch_spread_evidence_quality"))
    batch_spread_validation = _dict(
        evidence_summary.get("batch_spread_validation_status")
    )
    signal_hint = str(evidence_summary.get("batch_spread_signal_hint") or "").strip()
    has_measured_velocity = evidence_summary.get("has_measured_velocity") is True
    has_measured_group = evidence_summary.get("has_measured_group") is True
    range_session_count = _safe_int(evidence_summary.get("range_session_count")) or 0
    # setup_matched_session_count is conservative: only sessions where barrel_configuration_id
    # matches (or is NULL/unknown) are counted. When present, prefer it over the raw total
    # so that sessions from a different setup do not inflate repeat_confirmed.
    setup_matched_count = _safe_int(evidence_summary.get("setup_matched_session_count"))
    confirmed_session_count = (
        setup_matched_count if setup_matched_count is not None else range_session_count
    )
    setup_unmatched_count = (
        _safe_int(evidence_summary.get("setup_unmatched_session_count")) or 0
    )
    session_confidence_label = (
        str(session.get("confidence_label") or "").strip().lower()
    )
    session_confidence_score = _safe_float(session.get("confidence_score"))

    safety_state = (
        str(
            pressure_assessment.get("status")
            or session.get("safety_status")
            or internal_ballistics_summary.get("level")
            or "unknown"
        ).strip()
        or "unknown"
    )
    safety_blocked = safety_state in {
        "warning",
        "critical",
        "review_required",
        "stop",
        "high_risk",
    }
    internal_ballistics_level = (
        str(internal_ballistics_summary.get("level") or "").strip().lower()
    )
    if internal_ballistics_level == "critical":
        safety_blocked = True
    current_jump_mm = _safe_float(seating_depth_context.get("current_jump_mm"))
    jump_band = str(seating_depth_context.get("jump_band") or "").strip().lower()
    if jump_band == "into_lands":
        safety_blocked = True
        if safety_state == "ok":
            safety_state = "warning"

    harmonic_score = _safe_float(
        _first_nonempty(
            harmonics_profile.get("harmonic_score"),
            barrel_learning.get("harmonic_score"),
        )
    )
    node_bands = harmonics_profile.get("node_bands")
    if not isinstance(node_bands, list):
        node_bands = (
            barrel_learning.get("node_bands")
            if isinstance(barrel_learning.get("node_bands"), list)
            else []
        )
    harmonics_status = "known" if harmonics_profile or barrel_learning else "unresolved"
    harmonic_node_summary = {
        "status": harmonics_status,
        "node_bands": node_bands,
        "harmonic_score": harmonic_score,
        "stability_tier": harmonics_profile.get("stability_tier")
        or barrel_learning.get("stability_tier"),
        "confidence_label": harmonics_profile.get("harmonics_confidence")
        or barrel_learning.get("confidence_label"),
        "calibration_state": harmonics_profile.get("calibration_state"),
        "drift_flag": barrel_learning.get("drift_flag"),
        "notes": _list(harmonics_profile.get("notes"))[:4],
        "sensitivity": _dict(harmonics_profile.get("sensitivity")),
    }

    seating_sensitivity = _safe_float(
        _dict(harmonics_profile.get("sensitivity")).get("seating_depth")
    )
    if safety_blocked:
        recommended_next_change = "stop_and_review"
    elif signal_hint == "node_or_barrel_timing_signal":
        recommended_next_change = "seating_first"
    elif seating_sensitivity is not None and seating_sensitivity >= 1.25:
        recommended_next_change = "small_seating_bracket"
    else:
        recommended_next_change = "confirm_before_change"
    seating_jump_summary = {
        "status": seating_depth_context.get("status")
        or (
            "known"
            if load.get("cbto_mm") not in (None, "")
            or load.get("coal_mm") not in (None, "")
            else "unresolved"
        ),
        "coal_mm": _safe_float(load.get("coal_mm")),
        "cbto_mm": _safe_float(load.get("cbto_mm")),
        "jam_cbto_mm": _safe_float(seating_depth_context.get("jam_cbto_mm")),
        "current_jump_mm": current_jump_mm,
        "preferred_jump_mm": _safe_float(
            seating_depth_context.get("preferred_jump_mm")
        ),
        "preferred_cbto_mm": _safe_float(
            seating_depth_context.get("preferred_cbto_mm")
        ),
        "jump_band": jump_band or None,
        "source_label": _clean_text(seating_depth_context.get("source_label")),
        "node_alignment": (
            "sensitive"
            if seating_sensitivity is not None and seating_sensitivity >= 1.25
            else (
                "forgiving"
                if seating_sensitivity is not None and seating_sensitivity <= 0.75
                else "unknown"
            )
        ),
        "recommended_next_change": recommended_next_change,
    }

    active_lot_count = sum(
        1
        for name in ("bullet", "powder", "primer", "case")
        if _dict(lots.get(name)).get("id") not in (None, "")
    )
    powder_data = _dict(components.get("powder"))
    primer_data = _dict(components.get("primer"))
    case_data = _dict(components.get("case"))
    component_interaction = {
        "status": (
            "known"
            if components.get("bullet")
            and components.get("powder")
            and components.get("case")
            else "partial"
        ),
        "has_bullet": bool(_dict(components.get("bullet"))),
        "has_powder": bool(powder_data),
        "has_primer": bool(primer_data),
        "has_case": bool(case_data),
        "active_lot_count": active_lot_count,
        "case_capacity_gr_h2o": _safe_float(derived.get("case_capacity_gr_h2o")),
        "case_capacity_ml": _safe_float(derived.get("case_capacity_ml")),
        "powder_burn_rate_position": _normalize_burn_rate_position(
            _first_nonempty(
                _dict(derived.get("powder_database")).get("peak_pressure_timing"),
                powder_data.get("burn_rate"),
                _dict(derived.get("powder_database")).get("burn_rate_position"),
            )
        ),
        "powder_temp_stable": _dict(derived.get("powder_database")).get("temp_stable"),
        "primer_family": _clean_text(
            primer_data.get("primer_family") or primer_data.get("type")
        ),
        "bullet_fit_level": _clean_text(bullet_fit_summary.get("level")),
        "bullet_fit_score": _safe_float(bullet_fit_summary.get("fit_score")),
        "twist_assessment": _clean_text(bullet_fit_summary.get("twist_assessment")),
        "geometry_confidence": _clean_text(
            bullet_fit_summary.get("geometry_confidence")
        ),
        "jump_band": jump_band or None,
        "preferred_jump_mm": _safe_float(
            seating_depth_context.get("preferred_jump_mm")
        ),
        "lot_learning": lot_learning_summary,
    }
    chamber_jump_summary = {
        "status": seating_depth_context.get("status") or "unresolved",
        "jam_cbto_mm": _safe_float(seating_depth_context.get("jam_cbto_mm")),
        "current_jump_mm": current_jump_mm,
        "preferred_jump_mm": _safe_float(
            seating_depth_context.get("preferred_jump_mm")
        ),
        "preferred_cbto_mm": _safe_float(
            seating_depth_context.get("preferred_cbto_mm")
        ),
        "jump_band": jump_band or None,
        "source_label": _clean_text(seating_depth_context.get("source_label")),
        "best_evidence_batch_id": _safe_int(
            _dict(seating_depth_context.get("best_evidence")).get("batch_id")
        ),
        "summary": (
            f"Current jump {current_jump_mm:.3f} mm sits in {jump_band.replace('_', ' ')}."
            if current_jump_mm is not None and jump_band
            else (
                f"Preferred jump is about {_safe_float(seating_depth_context.get('preferred_jump_mm')):.3f} mm."
                if _safe_float(seating_depth_context.get("preferred_jump_mm"))
                is not None
                else "Jump context is still unresolved for this rifle and bullet."
            )
        ),
    }

    evidence_confidence = _build_evidence_weighting(
        session=session,
        evidence_summary=evidence_summary,
        validation=batch_spread_validation,
        batch_spread_evidence=batch_spread_evidence,
        signal_hint=signal_hint,
    )
    baseline = _dict(load.get("baseline"))
    control_state = _dict(load.get("control_state"))
    current_charge = _safe_float(load.get("charge_weight_gr"))
    current_coal = _safe_float(load.get("coal_mm"))
    current_cbto = _safe_float(load.get("cbto_mm"))
    baseline_charge = _safe_float(baseline.get("charge_gr"))
    baseline_coal = _safe_float(baseline.get("coal_mm"))
    baseline_cbto = _safe_float(baseline.get("cbto_mm"))
    charge_alignment, charge_delta = _alignment_state(
        current_charge, baseline_charge, 0.05
    )
    charge_source = (
        str(baseline.get("charge_source") or "recommended").strip().lower()
        or "recommended"
    )
    charge_source_label = (
        "learned baseline" if charge_source == "learned" else "modeled baseline"
    )
    if baseline_cbto is not None and current_cbto is not None:
        seating_alignment, seating_delta = _alignment_state(
            current_cbto, baseline_cbto, 0.03
        )
        seating_target_value = baseline_cbto
        seating_target_label = f"{baseline_cbto:.2f} mm CBTO"
        seating_target_unit = "cbto_mm"
    else:
        seating_alignment, seating_delta = _alignment_state(
            current_coal, baseline_coal, 0.03
        )
        seating_target_value = baseline_coal
        seating_target_label = (
            f"{baseline_coal:.2f} mm COAL" if baseline_coal is not None else None
        )
        seating_target_unit = "coal_mm" if baseline_coal is not None else None
    seating_source = (
        str(baseline.get("seating_source") or "recommended").strip().lower()
        or "recommended"
    )
    seating_source_label = (
        "learned baseline" if seating_source == "learned" else "modeled baseline"
    )
    baseline_control = {
        "charge_alignment": charge_alignment,
        "charge_delta_gr": charge_delta,
        "charge_source": charge_source,
        "charge_source_label": charge_source_label,
        "charge_target_gr": baseline_charge,
        "charge_target_label": (
            f"{baseline_charge:.2f} gr" if baseline_charge is not None else None
        ),
        "seating_alignment": seating_alignment,
        "seating_delta_mm": seating_delta,
        "seating_source": seating_source,
        "seating_source_label": seating_source_label,
        "seating_target_mm": seating_target_value,
        "seating_target_label": seating_target_label,
        "seating_target_unit": seating_target_unit,
        "charge_state": str(control_state.get("charge_state") or "").strip().lower()
        or None,
        "seating_state": str(control_state.get("seating_state") or "").strip().lower()
        or None,
        "branch_state": (
            "custom_branch"
            if charge_alignment == "outside" or seating_alignment == "outside"
            else (
                "frozen_baseline"
                if charge_alignment == "aligned" or seating_alignment == "aligned"
                else "unknown"
            )
        ),
        "should_return_before_compare": bool(
            charge_alignment == "outside" or seating_alignment == "outside"
        ),
        "recovery_action": (
            "return_to_charge_baseline"
            if charge_alignment == "outside" and baseline_charge is not None
            else (
                "return_to_seating_baseline"
                if seating_alignment == "outside" and seating_target_label
                else None
            )
        ),
        "charge_return_line": (
            f"Return charge toward {baseline_charge:.2f} gr before treating this as the same candidate."
            if charge_alignment == "outside" and baseline_charge is not None
            else ""
        ),
        "seating_return_line": (
            f"Return seating toward {seating_target_label} before trusting the comparison."
            if seating_alignment == "outside" and seating_target_label
            else ""
        ),
        "summary": (
            f"Return charge toward {baseline_charge:.2f} gr before trusting the comparison."
            if charge_alignment == "outside" and baseline_charge is not None
            else (
                f"Return seating toward {seating_target_label} before trusting the comparison."
                if seating_alignment == "outside" and seating_target_label
                else (
                    "Current setup is aligned with the frozen baseline."
                    if charge_alignment == "aligned" or seating_alignment == "aligned"
                    else ""
                )
            )
        ),
    }
    baseline_control["active_return_line"] = (
        baseline_control.get("charge_return_line")
        or baseline_control.get("seating_return_line")
        or ""
    )
    baseline_control["alignment_summary"] = (
        f"Charge is aligned with the frozen {charge_source_label}."
        if charge_alignment == "aligned" and seating_alignment != "outside"
        else (
            f"Seating is aligned with the frozen {seating_source_label}."
            if seating_alignment == "aligned" and charge_alignment != "outside"
            else baseline_control.get("summary") or ""
        )
    )
    return_targets = {
        "charge": {
            "label": (
                f"{baseline_charge:.2f} gr" if baseline_charge is not None else None
            ),
            "value_gr": baseline_charge,
            "source_label": charge_source_label,
            "aligned": charge_alignment == "aligned",
            "return_line": baseline_control.get("charge_return_line") or "",
        },
        "seating": {
            "label": seating_target_label,
            "value_mm": seating_target_value,
            "unit": seating_target_unit,
            "source_label": seating_source_label,
            "aligned": seating_alignment == "aligned",
            "return_line": baseline_control.get("seating_return_line") or "",
        },
    }
    branch_advisory = {
        "state": baseline_control.get("branch_state"),
        "label": (
            "Custom branch"
            if baseline_control.get("branch_state") == "custom_branch"
            else (
                "Frozen baseline"
                if baseline_control.get("branch_state") == "frozen_baseline"
                else "Unknown branch"
            )
        ),
        "summary": baseline_control.get("summary") or "",
        "compare_mode": (
            "return_before_compare"
            if baseline_control.get("should_return_before_compare")
            else (
                "same_branch"
                if baseline_control.get("branch_state") == "frozen_baseline"
                else "unknown"
            )
        ),
    }
    branch_advisory["display_line"] = (
        f"{branch_advisory['label']} ({branch_advisory['compare_mode']})"
        if branch_advisory.get("label") and branch_advisory.get("compare_mode")
        else branch_advisory.get("label") or ""
    )
    branch_advisory["action_line"] = (
        baseline_control.get("active_return_line")
        or baseline_control.get("alignment_summary")
        or branch_advisory.get("summary")
        or ""
    )
    learning_summary = {
        "model_status": learning_aggregate.get("model_status")
        or learning_aggregate.get("confidence_label")
        or "raw model",
        "weakest_link": learning_aggregate.get("weakest_link"),
        "next_focus": learning_aggregate.get("next_focus")
        or session.get("next_action"),
        "lot_watch_count": _safe_int(lot_learning_summary.get("watch_count")) or 0,
    }

    evidence_level = str(evidence_confidence.get("status") or "").strip().lower()
    strong_evidence = evidence_level in {"moderate", "strong", "high"}
    small_sample_group = bool(evidence_confidence.get("small_sample_group"))
    usage_goal = str(evidence_confidence.get("usage_goal") or "general").strip()
    cold_bore_channel = _dict(evidence_confidence.get("cold_bore"))
    cold_bore_status = str(cold_bore_channel.get("status") or "not_applicable").strip()
    evidence_diagnostics = {
        "status": "supported",
        "items": [],
        "impacts": [],
        "focus_areas": [],
        "suggested_action": "",
    }
    if not has_measured_velocity:
        evidence_diagnostics["status"] = "needs_measurement"
        evidence_diagnostics["items"].append(
            "Session still lacks measured chronograph data for the active setup."
        )
        evidence_diagnostics["impacts"].append(
            "Velocity trends and pressure interpretation remain more model-driven than measured until chrono data is logged."
        )
        evidence_diagnostics["focus_areas"].extend(
            ["velocity validation", "data trust"]
        )
        evidence_diagnostics["suggested_action"] = (
            "Capture a chronograph string for the current setup before treating the node as verified."
        )
    if not has_measured_group:
        evidence_diagnostics["status"] = "needs_measurement"
        evidence_diagnostics["items"].append(
            "Session still lacks measured grouping data for the active setup."
        )
        evidence_diagnostics["impacts"].append(
            "Grouping conclusions remain provisional until the barrel and seating behavior are confirmed on target."
        )
        for focus_area in ("grouping", "data trust"):
            if focus_area not in evidence_diagnostics["focus_areas"]:
                evidence_diagnostics["focus_areas"].append(focus_area)
        if not evidence_diagnostics["suggested_action"]:
            evidence_diagnostics["suggested_action"] = (
                "Add one measured group at the active seating depth before ranking this combination highly."
            )
    if session_confidence_label == "low" or (
        session_confidence_score is not None and session_confidence_score < 2.5
    ):
        if evidence_diagnostics["status"] == "supported":
            evidence_diagnostics["status"] = "thin_evidence"
        evidence_diagnostics["items"].append(
            "Confidence is still low, so current guidance depends on thin or partially assumed data."
        )
        evidence_diagnostics["impacts"].append(
            "Changes can look meaningful even when the underlying data basis is still too thin for strong conclusions."
        )
        if "data trust" not in evidence_diagnostics["focus_areas"]:
            evidence_diagnostics["focus_areas"].append("data trust")
        if not evidence_diagnostics["suggested_action"]:
            evidence_diagnostics["suggested_action"] = (
                "Add measured data with chrono or grouping before locking in a node or ranking this combination highly."
            )
    if (
        evidence_level in {"very_thin", "thin"}
        and evidence_diagnostics["status"] == "supported"
    ):
        evidence_diagnostics["status"] = "thin_evidence"
        evidence_diagnostics["items"].append(
            "Matched evidence is still thin, so stronger ranking or optimization should wait."
        )
        evidence_diagnostics["impacts"].append(
            "Thin evidence can make small changes look more meaningful than they really are."
        )
        for focus_area in ("matched evidence", "data trust"):
            if focus_area not in evidence_diagnostics["focus_areas"]:
                evidence_diagnostics["focus_areas"].append(focus_area)
        if not evidence_diagnostics["suggested_action"]:
            evidence_diagnostics["suggested_action"] = (
                "Capture matched chrono and group data under the same setup before making a hard call."
            )
    if evidence_confidence.get("mixed_signal", {}).get("status") == "mixed_signal":
        if evidence_diagnostics["status"] == "supported":
            evidence_diagnostics["status"] = "mixed_signal"
        evidence_diagnostics["items"].append(
            "Evidence currently mixes load signal with setup, shooter, or condition effects."
        )
        evidence_diagnostics["impacts"].append(
            "The engine should prefer a controlled repeat over a strong ranking when several causes can explain the result."
        )
        for focus_area in ("matched evidence", "signal isolation"):
            if focus_area not in evidence_diagnostics["focus_areas"]:
                evidence_diagnostics["focus_areas"].append(focus_area)
        if not evidence_diagnostics["suggested_action"]:
            evidence_diagnostics["suggested_action"] = (
                "Repeat one same-setup control series before changing the recipe or ranking the load harder."
            )
    cold_bore_channel = _dict(evidence_confidence.get("cold_bore"))
    if cold_bore_channel.get("status") in {
        "field_validation_pending",
        "cold_bore_confirmation_pending",
        "evidence_pending",
        "needs_confirmation",
    }:
        evidence_diagnostics["items"].append(
            str(cold_bore_channel.get("summary") or "").strip()
        )
        if "cold-bore validation" not in evidence_diagnostics["focus_areas"]:
            evidence_diagnostics["focus_areas"].append("cold-bore validation")
    group_pattern_channel = _dict(evidence_confidence.get("group_pattern"))
    if group_pattern_channel.get("status") not in {"unknown", ""}:
        evidence_diagnostics["items"].append(
            str(group_pattern_channel.get("summary") or "").strip()
        )
    # Surface unmatched sessions when the session count is inflated by a different setup.
    if setup_unmatched_count > 0:
        evidence_diagnostics["items"].append(
            f"{setup_unmatched_count} session(s) were logged from a different barrel configuration "
            "and are not counted toward repeat confirmation for this setup."
        )
        if "setup identity" not in evidence_diagnostics["focus_areas"]:
            evidence_diagnostics["focus_areas"].append("setup identity")
    bullet_fit_level = str(bullet_fit_summary.get("level") or "").strip().lower()
    bullet_fit_score = _safe_float(bullet_fit_summary.get("fit_score"))
    stable_harmonics = str(
        harmonics_profile.get("stability_tier") or ""
    ).strip().lower() in {
        "stable",
        "very-stable",
    }
    # Validation gates: block ranking when evidence is ambiguous or insufficient.
    # These gates stop a "lucky" result from being promoted before the signal is
    # interpretable. Ranking resumes once more measurements narrow the cause.
    evidence_gated = evidence_level in {"insufficient_evidence"} or signal_hint in {
        "insufficient_evidence",
        "pressure_or_ammo",
    }
    if safety_blocked:
        candidate_ranking = {
            "status": "blocked",
            "reason": "safety_blocked",
        }
    elif evidence_gated:
        candidate_ranking = {
            "status": "blocked",
            "reason": (
                signal_hint
                if signal_hint in {"pressure_or_ammo"}
                else "insufficient_evidence"
            ),
        }
    elif strong_evidence and stable_harmonics:
        candidate_ranking = {
            "status": "promising",
            "reason": "stable_node_supported",
        }
    else:
        candidate_ranking = {
            "status": "provisional",
            "reason": "awaiting_more_engine_layers",
        }

    lot_watch_count = _safe_int(lot_learning_summary.get("watch_count")) or 0
    temperature_watch = internal_ballistics_summary.get("temp_stable") in (
        False,
        0,
        "0",
    )
    # "High" robustness requires multiple confirmed sessions (≥2) so a single lucky
    # series cannot reach the top tier. confirmed_session_count uses the setup-matched
    # count when available (conservative: explicit config mismatches don't count).
    repeat_confirmed = confirmed_session_count >= 2
    robustness_level = (
        "high"
        if not safety_blocked
        and not evidence_gated
        and stable_harmonics
        and strong_evidence
        and not small_sample_group
        and lot_watch_count == 0
        and bullet_fit_level not in {"warning", "critical"}
        and repeat_confirmed
        else (
            "moderate"
            if not safety_blocked
            and not evidence_gated
            and (stable_harmonics or strong_evidence)
            and bullet_fit_level != "critical"
            else "low"
        )
    )
    candidate_profile = {
        "robustness_level": robustness_level,
        "node_fit": (
            "strong"
            if stable_harmonics and strong_evidence
            else (
                "developing"
                if stable_harmonics or signal_hint == "node_or_barrel_timing_signal"
                else "unclear"
            )
        ),
        "temperature_watch": temperature_watch,
        "lot_watch": lot_watch_count > 0,
        "evidence_gate": evidence_level or "unknown",
        "bullet_fit_level": bullet_fit_level or None,
        "bullet_fit_score": bullet_fit_score,
        "jump_band": jump_band or None,
        "small_sample_group": small_sample_group,
        "repeat_session_count": confirmed_session_count,
        "repeat_confirmed": repeat_confirmed,
        "setup_unmatched_session_count": setup_unmatched_count,
    }
    baseline_diagnostics = {
        "status": (
            "return_to_baseline"
            if charge_alignment == "outside" or seating_alignment == "outside"
            else (
                "aligned"
                if charge_alignment == "aligned" or seating_alignment == "aligned"
                else "unknown"
            )
        ),
        "items": [],
        "impacts": [],
        "focus_areas": [],
        "suggested_action": "",
    }
    if charge_alignment == "outside" and baseline_charge is not None:
        learned_charge_label = "learned " if charge_source == "learned" else ""
        baseline_diagnostics["items"].append(
            f"Charge {current_charge:.2f} gr is {abs(charge_delta or 0.0):.2f} gr away from the frozen {learned_charge_label}recommendation baseline ({baseline_charge:.2f} gr)."
        )
        baseline_diagnostics["impacts"].append(
            "Charge comparisons now sit outside a learned session baseline, so node and pressure conclusions should be treated as custom until a new learned charge is confirmed."
            if charge_source == "learned"
            else "Charge comparisons now sit outside the session baseline, so node and pressure conclusions should be treated as custom until revalidated."
        )
        baseline_diagnostics["focus_areas"].extend(["velocity node", "data trust"])
        baseline_diagnostics["suggested_action"] = (
            "Use the frozen learned charge baseline or confirm a new charge node before promoting this setup again."
            if charge_source == "learned"
            else "Use the frozen recommendation baseline or confirm a new charge node before promoting this setup."
        )
    elif charge_alignment == "aligned" and baseline_charge is not None:
        learned_charge_label = "learned " if charge_source == "learned" else ""
        baseline_diagnostics["items"].append(
            f"Charge {current_charge:.2f} gr is aligned with the frozen {learned_charge_label}recommendation baseline."
        )
    if seating_alignment == "outside" and seating_target_label:
        baseline_label = (
            f"{baseline_cbto:.2f} mm"
            if baseline_cbto is not None
            else f"{baseline_coal:.2f} mm"
        )
        if baseline_cbto is not None and current_cbto is not None:
            learned_label = "learned " if seating_source == "learned" else ""
            baseline_diagnostics["items"].append(
                f"CBTO {current_cbto:.2f} mm is {abs(seating_delta or 0.0):.2f} mm away from the {learned_label}recommendation baseline ({baseline_label})."
            )
        elif baseline_coal is not None and current_coal is not None:
            baseline_diagnostics["items"].append(
                f"COAL {current_coal:.2f} mm is {abs(seating_delta or 0.0):.2f} mm away from the frozen recommendation baseline ({baseline_label})."
            )
        baseline_diagnostics["impacts"].append(
            "Seating now sits outside a learned baseline, so jump and group comparisons should be treated as custom until a new sweet spot is reconfirmed."
            if seating_source == "learned"
            else "Seating now sits outside the frozen baseline, so jump and group comparisons should be treated as custom until they are reconfirmed."
        )
        for focus_area in (
            "jump",
            "grouping" if baseline_cbto is not None else "case volume",
        ):
            if focus_area not in baseline_diagnostics["focus_areas"]:
                baseline_diagnostics["focus_areas"].append(focus_area)
        if "jump" not in baseline_diagnostics["focus_areas"]:
            baseline_diagnostics["focus_areas"].append("jump")
        if not baseline_diagnostics["suggested_action"]:
            baseline_diagnostics["suggested_action"] = (
                "Return to the frozen learned seating baseline or confirm a new seating sweet spot before treating the result as learned behavior."
                if seating_source == "learned"
                else "Return to the frozen seating baseline or confirm a new seating sweet spot before treating the result as learned behavior."
            )
    elif seating_alignment == "aligned" and seating_target_label:
        aligned_label = (
            "learned seating baseline"
            if seating_source == "learned"
            else "seating baseline"
        )
        if baseline_cbto is not None and current_cbto is not None:
            baseline_diagnostics["items"].append(
                f"CBTO {current_cbto:.2f} mm is aligned with the frozen {aligned_label}."
            )
        elif baseline_coal is not None and current_coal is not None:
            baseline_diagnostics["items"].append(
                f"COAL {current_coal:.2f} mm is aligned with the frozen {aligned_label}."
            )

    recommendation_stack: list[dict[str, Any]] = []
    if safety_blocked:
        recommendation_stack.append(
            {
                "priority": 1,
                "area": "safety",
                "action": "stop_and_review",
                "reason": pressure_assessment.get("summary")
                or internal_ballistics_summary.get("message")
                or "Safety has to win over optimization.",
            }
        )
    elif charge_alignment == "outside" and baseline_charge is not None:
        recommendation_stack.append(
            {
                "priority": 1,
                "area": "charge_baseline",
                "action": "return_to_charge_baseline",
                "reason": (
                    f"Current charge sits outside the frozen {charge_source_label}, so charge comparisons should return to "
                    f"{baseline_charge:.2f} gr or confirm a fresh node before promotion."
                ),
            }
        )
    elif seating_alignment == "outside" and seating_target_label:
        recommendation_stack.append(
            {
                "priority": 1,
                "area": "seating_baseline",
                "action": "return_to_seating_baseline",
                "reason": (
                    f"Current seating sits outside the frozen {seating_source_label}, so jump comparisons should return to "
                    f"{seating_target_label} or confirm a fresh seating sweet spot."
                ),
            }
        )
    elif signal_hint == "node_or_barrel_timing_signal":
        recommendation_stack.append(
            {
                "priority": 1,
                "area": "seating_jump",
                "action": "seating_depth_bracket",
                "reason": "Pattern and spread signal look more like timing or node confirmation than a charge change.",
            }
        )
    else:
        recommendation_stack.append(
            {
                "priority": 1,
                "area": "validation",
                "action": (
                    "confirm_node_window"
                    if stable_harmonics
                    else "collect_matched_group_and_chrono"
                ),
                "reason": "The next step should either confirm the current node window or improve matched evidence before broader tuning.",
            }
        )

    if lot_watch_count > 0:
        recommendation_stack.append(
            {
                "priority": len(recommendation_stack) + 1,
                "area": "lots",
                "action": "hold_current_lots_constant",
                "reason": "Active component lots carry watch flags, so comparisons should keep lots fixed until the node is confirmed.",
            }
        )
    if temperature_watch:
        recommendation_stack.append(
            {
                "priority": len(recommendation_stack) + 1,
                "area": "temperature",
                "action": "verify_temp_shift",
                "reason": "The powder context is not clearly temperature-stable, so velocity and POI should be confirmed across conditions.",
            }
        )
    if evidence_level in {"very_thin", "thin"}:
        recommendation_stack.append(
            {
                "priority": len(recommendation_stack) + 1,
                "area": "evidence",
                "action": "collect_matched_group_and_chrono",
                "reason": "Thin evidence should be strengthened before the engine promotes a load confidently.",
            }
        )

    if safety_blocked:
        next_action = "stop_and_review"
        why = (
            "Current jump appears to run into the lands, so seating safety must be cleared before precision tuning continues."
            if jump_band == "into_lands"
            else pressure_assessment.get("summary")
            or internal_ballistics_summary.get("message")
            or "Safety or pressure-related uncertainty blocks further optimization."
        )
    elif charge_alignment == "outside" and baseline_charge is not None:
        next_action = "return_to_charge_baseline"
        why = f"Current charge is outside the frozen {charge_source_label}; return to {baseline_charge:.2f} gr or validate a fresh charge node first."
    elif seating_alignment == "outside" and seating_target_label:
        next_action = "return_to_seating_baseline"
        why = f"Current seating is outside the frozen {seating_source_label}; return to {seating_target_label} or validate a fresh seating sweet spot first."
    elif signal_hint == "node_or_barrel_timing_signal":
        next_action = "seating_depth_bracket"
        why = (
            evidence_summary.get("batch_spread_reason")
            or "Spread pattern points more toward node or timing verification than a larger powder change."
        )
    elif evidence_level in {"very_thin", "thin"}:
        next_action = "collect_matched_group_and_chrono"
        why = "Evidence is still thin, so the next step should be a matched control string before stronger tuning."
    elif stable_harmonics:
        next_action = "confirm_node_window"
        why = "Current harmonics look reasonably stable, so the next step is to confirm the node window conservatively."
    else:
        next_action = (
            session.get("next_action")
            or learning_aggregate.get("next_focus")
            or "confirm_current_load"
        )
        why = (
            evidence_summary.get("batch_spread_reason")
            or internal_ballistics_summary.get("message")
            or learning_aggregate.get("next_focus")
        )
    # Usage-goal override: after the base action is set, upgrade to goal-specific
    # next step when the evidence state permits it and safety is clear. Safety and
    # baseline-return actions are never overridden — they take unconditional priority.
    # Active technical optimization actions (bracketing, load development steps) are
    # also not overridden — the open technical question must be answered first.
    _active_optimization_actions = {
        "seating_depth_bracket",
        "charge_bracket",
        "ocw_series",
        "seating_trim",
        "build_initial_test_batches",
        "collect_chrono_data",
        "collect_group_data",
        "resolve_pressure",
        "reduce_charge",
        "stop_and_consult",
    }
    if next_action not in {
        "stop_and_review",
        "return_to_charge_baseline",
        "return_to_seating_baseline",
    }:
        if usage_goal == "hunting" and cold_bore_status not in {"not_applicable"}:
            next_action = "cold_bore_field_validation"
            why = (
                cold_bore_channel.get("summary")
                or "Hunting approval requires a documented cold-bore field shot from realistic support before the load is field-ready."
            )
        elif (
            usage_goal == "competition"
            and not evidence_gated
            and not repeat_confirmed
            and next_action not in _active_optimization_actions
        ):
            next_action = "repeatability_string"
            why = (
                "Competition readiness requires the load to repeat cleanly across at least two independent sessions "
                "before it can be ranked confidently against alternatives."
            )
        elif (
            usage_goal == "competition"
            and not evidence_gated
            and repeat_confirmed
            and next_action == "confirm_current_load"
        ):
            next_action = "confirm_node_window"
            why = "Evidence repeats confirm the result — confirm the node window conservatively before final competition ranking."
    risk_flags: list[str] = []
    if safety_blocked:
        risk_flags.append("safety_block")
    if lot_watch_count > 0:
        risk_flags.append("lot_watch")
    if temperature_watch:
        risk_flags.append("temperature_watch")
    if evidence_level in {"very_thin", "thin"}:
        risk_flags.append("thin_evidence")
    if candidate_profile["node_fit"] in {"developing", "unclear"}:
        risk_flags.append("node_not_proven")
    if charge_alignment == "outside":
        risk_flags.append("charge_off_baseline")
    if seating_alignment == "outside":
        risk_flags.append("seating_off_baseline")
    guardrails: list[str] = []
    if safety_blocked:
        guardrails.append(
            "Do not optimize charge or seating until pressure and safety are reviewed."
        )
    if charge_alignment == "outside":
        guardrails.append(
            "Do not compare charge results against the frozen baseline until charge is returned or a new node is confirmed."
        )
    if seating_alignment == "outside":
        guardrails.append(
            "Do not compare seating results against the frozen baseline until seating is returned or a new sweet spot is confirmed."
        )
    if lot_watch_count > 0:
        guardrails.append(
            "Keep active lots fixed until the current comparison is confirmed."
        )
    if evidence_level in {"very_thin", "thin"}:
        guardrails.append("Do not promote or reject the load from thin evidence alone.")
    if temperature_watch:
        guardrails.append(
            "Verify velocity and point of impact across temperature before trusting the result widely."
        )
    if candidate_profile["node_fit"] in {"developing", "unclear"}:
        guardrails.append(
            "Treat the current node as provisional until a matched repeat confirms it."
        )
    shot_plan_map = {
        "stop_and_review": "Pause live tuning. Review pressure margin, brass response, and the current seating baseline before the next shot string.",
        "return_to_charge_baseline": "Return to the frozen charge baseline or run a fresh charge confirmation before treating the setup as the same candidate.",
        "return_to_seating_baseline": "Return to the frozen seating baseline or confirm a new seating sweet spot before comparing against prior evidence.",
        "seating_depth_bracket": "Shoot one control group at the current load, then a tight seating-depth bracket with charge held constant.",
        "collect_matched_group_and_chrono": "Shoot one matched chrono string and one measured group under the same setup and conditions.",
        "confirm_node_window": "Repeat the same charge and seating with a short confirmation string before ranking it higher.",
        "confirm_current_load": "Repeat the current recipe once more with the same lots and setup before changing variables.",
        "cold_bore_field_validation": "Fire one cold-bore shot from field-realistic support, note POI, then fire a short 3-5 shot control group. Log both as a hunting validation session.",
        "repeatability_string": "Shoot one matched chrono string and measured group in a second independent range session, keeping setup and conditions as similar as possible to the first session.",
    }
    promotion_gate = {
        "status": (
            "blocked"
            if safety_blocked
            else (
                "return_to_baseline"
                if charge_alignment == "outside" or seating_alignment == "outside"
                else (
                    "needs_evidence"
                    if evidence_level in {"very_thin", "thin"}
                    else (
                        "needs_confirmation"
                        if candidate_profile["node_fit"] in {"developing", "unclear"}
                        else "eligible"
                    )
                )
            )
        ),
        "reason": (
            "safety"
            if safety_blocked
            else (
                "baseline_control"
                if charge_alignment == "outside" or seating_alignment == "outside"
                else (
                    "thin_evidence"
                    if evidence_level in {"very_thin", "thin"}
                    else (
                        "node_confirmation"
                        if candidate_profile["node_fit"] in {"developing", "unclear"}
                        else "supported"
                    )
                )
            )
        ),
    }
    guidance_title_map = {
        "stop_and_review": "Stop and review safety before optimization",
        "return_to_charge_baseline": "Return to the frozen charge baseline first",
        "return_to_seating_baseline": "Return to the frozen seating baseline first",
        "seating_depth_bracket": "Confirm seating depth before broader tuning",
        "collect_matched_group_and_chrono": "Collect matched evidence before stronger claims",
        "confirm_node_window": "Confirm the current node window conservatively",
        "confirm_current_load": "Repeat the current load before making a bigger change",
        "cold_bore_field_validation": "Confirm cold-bore behavior from realistic field support",
        "repeatability_string": "Run a repeatability confirmation string across two sessions",
    }
    guidance_setup_map = {
        "stop_and_review": "Run a conservative control series only after pressure margin, brass response, and seating are reviewed.",
        "return_to_charge_baseline": "Return to the frozen charge baseline before trusting the comparison, or prove a new charge node as a fresh branch.",
        "return_to_seating_baseline": "Return to the frozen seating baseline before trusting the comparison, or prove a new seating sweet spot as a fresh branch.",
        "seating_depth_bracket": "Keep charge fixed and run a small seating-depth bracket before changing powder broadly.",
        "collect_matched_group_and_chrono": "Capture one matched chrono string and one measured group under the same setup and conditions.",
        "confirm_node_window": "Repeat the current charge and seating under the same setup to prove the node window is real.",
        "confirm_current_load": "Repeat the same load with the same lots and setup before promoting or rejecting it.",
        "cold_bore_field_validation": "Fire one documented cold-bore shot from realistic field support, then a short matched control group, before approving the load for hunting use.",
        "repeatability_string": "Run one matched chrono string and one measured group in a second independent session before ranking the load for competition.",
    }
    guidance = {
        "title": guidance_title_map.get(
            next_action, "Use the smart engine as the next conservative step"
        ),
        "setup_line": guidance_setup_map.get(
            next_action,
            why or "Repeat under controlled conditions before the next tuning step.",
        ),
        "reason": why,
        "priority": (
            recommendation_stack[0]["area"] if recommendation_stack else "validation"
        ),
    }
    keep_constant_map = {
        "stop_and_review": [
            "Do not change charge and seating in the same step.",
            "Keep current component lots fixed while reviewing the pressure picture.",
        ],
        "return_to_charge_baseline": [
            "Do not change seating while re-establishing the charge baseline.",
            "Keep lots and rifle setup fixed while returning to the baseline charge.",
        ],
        "return_to_seating_baseline": [
            "Do not change charge while re-establishing the seating baseline.",
            "Keep lots and rifle setup fixed while returning to the baseline seating.",
        ],
        "seating_depth_bracket": [
            "Keep charge weight fixed.",
            "Keep powder, primer, and brass lots fixed.",
            "Keep the same rifle setup and support condition.",
        ],
        "collect_matched_group_and_chrono": [
            "Keep charge and seating fixed for the control string.",
            "Use the same rifle/barrel/setup and support condition.",
            "Keep active component lots fixed.",
        ],
        "confirm_node_window": [
            "Keep charge, seating, and component lots fixed.",
            "Repeat under the same rifle setup and similar conditions.",
        ],
        "confirm_current_load": [
            "Keep the full recipe unchanged for the confirmation pass.",
            "Use the same lots, setup, and distance.",
        ],
        "cold_bore_field_validation": [
            "Keep charge, seating, and all component lots identical to the tested recipe.",
            "Use the same zero distance and optic settings.",
            "Do not fire a fouling shot before the cold-bore validation shot.",
        ],
        "repeatability_string": [
            "Keep charge, seating, and component lots identical across both sessions.",
            "Use the same rifle/barrel/setup — do not change optics, suppressor, or stock between sessions.",
            "Do not change any recipe variable until both session results are logged.",
        ],
    }
    capture_map = {
        "stop_and_review": [
            "Pressure notes and brass condition",
            "Chronograph trace if available",
            "Any seating or jump change already applied",
        ],
        "return_to_charge_baseline": [
            "One short confirmation string at the frozen charge baseline",
            "Measured chrono at the baseline charge",
            "Any POI shift after returning to baseline",
        ],
        "return_to_seating_baseline": [
            "One short confirmation string at the frozen seating baseline",
            "Measured group at the baseline seating",
            "Any POI shift after returning to baseline",
        ],
        "seating_depth_bracket": [
            "One control group at current seating",
            "One short seating-depth bracket",
            "Chronograph on the control string",
        ],
        "collect_matched_group_and_chrono": [
            "One matched chrono string",
            "One measured group from the same setup",
            "Wind / condition notes",
        ],
        "confirm_node_window": [
            "One short confirmation string",
            "Measured group and chrono under the same setup",
            "POI confirmation relative to prior node result",
        ],
        "confirm_current_load": [
            "One repeat group",
            "Chronograph confirmation if not already matched",
            "Condition notes",
        ],
        "cold_bore_field_validation": [
            "Cold-bore shot POI relative to known zero",
            "3-5 shot control group from field-realistic support",
            "Condition and temperature notes",
        ],
        "repeatability_string": [
            "One matched chrono string in session 2",
            "One measured group in session 2",
            "Date, lot, and conditions from both sessions for comparison",
        ],
    }
    success_criteria_map = {
        "stop_and_review": "The setup is only allowed forward when pressure and internal-ballistics concerns are cleared.",
        "return_to_charge_baseline": "The baseline charge repeats cleanly enough that later charge comparisons can be trusted again.",
        "return_to_seating_baseline": "The baseline seating repeats cleanly enough that later seating comparisons can be trusted again.",
        "seating_depth_bracket": "A seating step should tighten or stabilize the pattern without introducing new pressure concern.",
        "collect_matched_group_and_chrono": "The engine gets one clean matched evidence set before stronger conclusions are made.",
        "confirm_node_window": "The same charge and seating repeat with similar POI and stable chrono behavior.",
        "confirm_current_load": "The current recipe repeats cleanly enough to be trusted as a real signal.",
        "cold_bore_field_validation": "Cold-bore POI is within acceptable hunting margin and the control group confirms consistent point of impact.",
        "repeatability_string": "Session 2 matches session 1 within acceptable ES/SD and group-size bounds, confirming the result is not a one-off.",
    }
    stop_conditions_map = {
        "stop_and_review": [
            "Any new pressure sign",
            "Unexpected brass response",
            "Internal-ballistics summary remains warning/critical",
        ],
        "return_to_charge_baseline": [
            "A new pressure sign appears while returning to the baseline charge",
            "The baseline charge no longer behaves like the prior confirmed state",
        ],
        "return_to_seating_baseline": [
            "A new pressure sign appears while returning to the baseline seating",
            "The baseline seating no longer behaves like the prior confirmed state",
        ],
        "seating_depth_bracket": [
            "Any new pressure sign during the control string",
            "Velocity jump or POI shift that breaks the current baseline",
        ],
        "collect_matched_group_and_chrono": [
            "Conditions drift enough that the string is no longer matched",
            "A new safety flag appears",
        ],
        "confirm_node_window": [
            "The repeat opens up in a way that breaks the node picture",
            "Pressure or lot watch becomes active",
        ],
        "confirm_current_load": [
            "The repeat is not comparable to the original setup",
            "A new pressure sign appears",
        ],
        "cold_bore_field_validation": [
            "Cold-bore POI is outside acceptable hunting margin",
            "Conditions prevent a fair comparison to the original zero",
            "A pressure sign or unusual brass response appears",
        ],
        "repeatability_string": [
            "Session 2 conditions are too different from session 1 for a fair comparison",
            "A new pressure or safety flag appears in session 2",
        ],
    }
    estimated_rounds_map = {
        "stop_and_review": 0,
        "return_to_charge_baseline": 5,
        "return_to_seating_baseline": 5,
        "seating_depth_bracket": 9,
        "collect_matched_group_and_chrono": 8,
        "confirm_node_window": 6,
        "confirm_current_load": 5,
        "cold_bore_field_validation": 6,
        "repeatability_string": 8,
    }
    session_type_map = {
        "stop_and_review": "safety_review",
        "return_to_charge_baseline": "charge_baseline_recovery",
        "return_to_seating_baseline": "seating_baseline_recovery",
        "seating_depth_bracket": "seating_validation",
        "collect_matched_group_and_chrono": "evidence_control",
        "confirm_node_window": "node_confirmation",
        "confirm_current_load": "load_confirmation",
        "cold_bore_field_validation": "field_validation",
        "repeatability_string": "repeatability_confirmation",
    }
    validation_gate = {
        "status": (
            "blocked"
            if safety_blocked
            else (
                "return_to_baseline"
                if charge_alignment == "outside" or seating_alignment == "outside"
                else (
                    "collect_more_evidence"
                    if evidence_level in {"very_thin", "thin"}
                    else (
                        "confirm_node"
                        if candidate_profile["node_fit"] in {"developing", "unclear"}
                        else "ready_for_cautious_promotion"
                    )
                )
            )
        ),
        "label": (
            "Blocked by safety"
            if safety_blocked
            else (
                "Return to frozen baseline"
                if charge_alignment == "outside" or seating_alignment == "outside"
                else (
                    "Needs matched evidence"
                    if evidence_level in {"very_thin", "thin"}
                    else (
                        "Needs node confirmation"
                        if candidate_profile["node_fit"] in {"developing", "unclear"}
                        else "Ready for cautious promotion"
                    )
                )
            )
        ),
        "must_prove": (
            "Pressure and internal-ballistics concerns are cleared before tuning continues."
            if safety_blocked
            else (
                "The recipe is returned to the frozen charge/seating baseline or a fresh custom baseline is confirmed."
                if charge_alignment == "outside" or seating_alignment == "outside"
                else (
                    "One matched group and chrono set under the same setup."
                    if evidence_level in {"very_thin", "thin"}
                    else (
                        "The current node repeats cleanly under the same setup."
                        if candidate_profile["node_fit"] in {"developing", "unclear"}
                        else "The candidate stays stable enough to compare against other accepted loads."
                    )
                )
            )
        ),
        "next_gate": (
            "Clear the safety block first."
            if safety_blocked
            else (
                "Return to the frozen baseline or prove a fresh custom baseline."
                if charge_alignment == "outside" or seating_alignment == "outside"
                else (
                    "Collect one clean matched evidence pass."
                    if evidence_level in {"very_thin", "thin"}
                    else (
                        "Run one same-setup confirmation string."
                        if candidate_profile["node_fit"] in {"developing", "unclear"}
                        else "Compare cautiously against the current accepted baseline."
                    )
                )
            )
        ),
    }
    do_not_change_yet: list[str] = []
    if safety_blocked:
        do_not_change_yet.extend(
            [
                "Do not push charge higher while safety or pressure review is still open.",
                "Do not treat this recipe as a ranking candidate yet.",
            ]
        )
    if charge_alignment == "outside":
        do_not_change_yet.append(
            "Do not keep tuning away from the frozen charge baseline until the new charge path is explicitly confirmed."
        )
    if seating_alignment == "outside":
        do_not_change_yet.append(
            "Do not keep tuning away from the frozen seating baseline until the new seating path is explicitly confirmed."
        )
    if next_action == "seating_depth_bracket":
        do_not_change_yet.append(
            "Do not change powder charge before the seating-depth check is complete."
        )
    if evidence_level in {"very_thin", "thin"}:
        do_not_change_yet.append(
            "Do not promote or reject the load from thin evidence alone."
        )
    if lot_watch_count > 0:
        do_not_change_yet.append(
            "Do not change active component lots during the current confirmation pass."
        )
    if temperature_watch:
        do_not_change_yet.append(
            "Do not generalize the result across temperatures until a temp check is logged."
        )
    if candidate_profile["node_fit"] in {"developing", "unclear"}:
        do_not_change_yet.append(
            "Do not call the node proven until one same-setup repeat confirms it."
        )

    blocked_by: list[dict[str, str]] = []
    if safety_blocked:
        blocked_by.append(
            {
                "kind": "safety",
                "title": "Safety block",
                "reason": why,
            }
        )
    if charge_alignment == "outside" and baseline_charge is not None:
        blocked_by.append(
            {
                "kind": "charge_baseline",
                "title": "Charge baseline block",
                "reason": f"Current charge is outside the frozen {charge_source_label} and should return to {baseline_charge:.2f} gr or be treated as a fresh branch.",
            }
        )
    if seating_alignment == "outside" and seating_target_label:
        blocked_by.append(
            {
                "kind": "seating_baseline",
                "title": "Seating baseline block",
                "reason": f"Current seating is outside the frozen {seating_source_label} and should return to {seating_target_label} or be treated as a fresh branch.",
            }
        )
    if evidence_level in {"very_thin", "thin"}:
        blocked_by.append(
            {
                "kind": "evidence",
                "title": "Evidence block",
                "reason": "Matched chrono and group evidence is still too thin for a strong recommendation.",
            }
        )
    if candidate_profile["node_fit"] in {"developing", "unclear"}:
        blocked_by.append(
            {
                "kind": "node_confirmation",
                "title": "Node confirmation block",
                "reason": "The current node picture is still provisional and needs a same-setup repeat.",
            }
        )
    if lot_watch_count > 0:
        blocked_by.append(
            {
                "kind": "lot_watch",
                "title": "Lot watch block",
                "reason": "Active lot watch flags mean comparisons should stay inside the same lot set until confirmed.",
            }
        )
    if bullet_fit_level in {"warning", "critical"}:
        blocked_by.append(
            {
                "kind": "bullet_fit",
                "title": "Bullet fit block",
                "reason": str(
                    bullet_fit_summary.get("message")
                    or "Bullet fit should be cleared before stronger promotion."
                ),
            }
        )

    recommendation_confidence_score = (
        84.0
        if promotion_gate["status"] == "eligible" and robustness_level == "high"
        else (
            68.0
            if promotion_gate["status"] == "eligible"
            else (
                58.0
                if promotion_gate["status"] == "needs_confirmation"
                else 44.0 if promotion_gate["status"] == "needs_evidence" else 18.0
            )
        )
    )
    recommendation_confidence = {
        "score": recommendation_confidence_score,
        "level": (
            "high"
            if recommendation_confidence_score >= 75.0
            else "moderate" if recommendation_confidence_score >= 50.0 else "low"
        ),
        "summary": (
            "The engine sees a reasonably stable and promotable candidate."
            if recommendation_confidence_score >= 75.0
            else (
                "The engine sees a usable direction, but the candidate still needs confirmation."
                if recommendation_confidence_score >= 50.0
                else "The engine recommendation is still conservative because one or more gates remain open."
            )
        ),
        "uncertainty": (
            "safety"
            if safety_blocked
            else (
                "baseline"
                if charge_alignment == "outside" or seating_alignment == "outside"
                else (
                    "evidence"
                    if evidence_level in {"very_thin", "thin"}
                    else (
                        "node"
                        if candidate_profile["node_fit"] in {"developing", "unclear"}
                        else "lot" if lot_watch_count > 0 else "normal"
                    )
                )
            )
        ),
    }
    execution_plan = {
        "title": guidance["title"],
        "primary_action": next_action,
        "shot_plan": shot_plan_map.get(next_action, guidance["setup_line"]),
        "session_type": session_type_map.get(next_action, "validation"),
        "estimated_rounds": estimated_rounds_map.get(next_action),
        "keep_constant": keep_constant_map.get(next_action, []),
        "capture": capture_map.get(next_action, []),
        "success_criteria": success_criteria_map.get(next_action, guidance["reason"]),
        "stop_conditions": stop_conditions_map.get(next_action, []),
        "summary": (
            f"{guidance['title']}: {shot_plan_map.get(next_action, guidance['setup_line'])}"
        ),
        "guardrails": guardrails,
        "risk_flags": risk_flags,
        "promotion_gate": promotion_gate,
    }

    return {
        "identity": {
            "rifle_name": weapon.get("rifle_name"),
            "barrel_name": barrel_context.get("barrel_name")
            or barrel.get("barrel_name"),
            "barrel_configuration_name": barrel_context.get("barrel_configuration_name")
            or barrel.get("barrel_configuration_name"),
            "usage_profile_name": session.get("usage_profile_name"),
        },
        "safety": {
            "state": safety_state,
            "blocked": safety_blocked,
            "pressure_summary": pressure_assessment,
            "internal_ballistics_level": internal_ballistics_level or None,
        },
        "physics": {
            "internal_ballistics": internal_ballistics_summary,
            "raw_internal_ballistics": raw_internal_ballistics,
            "component_interaction": component_interaction,
        },
        "harmonics": harmonic_node_summary,
        "bullet_fit": bullet_fit_summary,
        "chamber_jump": chamber_jump_summary,
        "seating_jump": seating_jump_summary,
        "evidence": evidence_confidence,
        "evidence_diagnostics": evidence_diagnostics,
        "learning": learning_summary,
        "candidate_profile": candidate_profile,
        "baseline_control": baseline_control,
        "baseline_diagnostics": baseline_diagnostics,
        "return_targets": return_targets,
        "branch_advisory": branch_advisory,
        "decisions": {
            "candidate_ranking": candidate_ranking,
            "next_test": {
                "recommended_action": next_action,
                "blocked": safety_blocked,
                "why": why,
            },
            "recommendation_stack": recommendation_stack,
            "guidance": guidance,
            "validation_gate": validation_gate,
            "do_not_change_yet": do_not_change_yet,
            "blocked_by": blocked_by,
            "recommendation_confidence": recommendation_confidence,
            "execution_plan": execution_plan,
        },
        "engine_state": {
            "status": "ready" if weapon.get("rifle_name") else "incomplete_input",
            "offline_only": True,
            "explainable": True,
            "external_ai_used": False,
            "profile_available": bool(derived.get("profile_available")),
        },
    }


def build_smart_ammo_engine_from_runtime(
    runtime: dict[str, Any] | None,
) -> dict[str, Any]:
    engine_input = build_engine_input_from_runtime(runtime)
    engine_result = build_engine_result_from_input(engine_input)
    return {
        "engine_input": engine_input,
        "engine_result": engine_result,
    }


def build_smart_ammo_engine(database, session_id: int) -> dict[str, Any] | None:
    from ..tools.load_session_runtime_service import build_load_session_runtime

    runtime = build_load_session_runtime(database, session_id)
    if not isinstance(runtime, dict):
        return None
    engine_input = build_engine_input_from_runtime(runtime)
    enriched_input = _build_enriched_engine_input(database, runtime, engine_input)
    engine_result = build_engine_result_from_input(enriched_input)
    return {
        "engine_input": enriched_input,
        "engine_result": engine_result,
    }
