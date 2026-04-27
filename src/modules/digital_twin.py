"""Digital twin for load development and harmonics."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..ballistics.services import analyze_load
from ..modules.smart_ammo_engine import build_engine_result_from_input
from ..utils.rifle_harmonics import calculate_harmonics_profile


class DigitalTwin:
    def __init__(
        self,
        rifle: Optional[Dict[str, Any]] = None,
        ammo: Optional[Dict[str, Any]] = None,
        environment: Optional[Dict[str, Any]] = None,
        **legacy_kwargs: Any,
    ):
        if rifle is None and legacy_kwargs:
            rifle = {
                "barrel_length_mm": legacy_kwargs.get("barrel_length"),
                "muzzle_velocity_mps": legacy_kwargs.get("powder_charge"),
                "bullet_weight_gr": legacy_kwargs.get("bullet_weight"),
                "coal_mm": legacy_kwargs.get("coal"),
                "pressure_psi": legacy_kwargs.get("pressure"),
            }
            ammo = {
                "powder_charge": legacy_kwargs.get("powder_charge"),
                "bullet_weight": legacy_kwargs.get("bullet_weight"),
            }
            environment = {"temperature_c": legacy_kwargs.get("temperature")}

        self.rifle = rifle or {}
        self.ammo = ammo or {}
        self.environment = environment or {}
        self.state: Dict[str, Any] = {}
        self.update_model()

    def update_model(self):
        analysis = self._build_service_analysis()
        smart_engine = self._build_smart_engine_state(analysis)
        harmonics = self.simulate_harmonics(analysis)
        self.state["analysis_mode"] = "service" if analysis else "fallback"
        self.state["analysis"] = analysis or {}
        self.state["smart_engine"] = smart_engine
        self.state["predicted_velocity"] = self.simulate_velocity(analysis)
        self.state["predicted_pressure"] = self.simulate_pressure(analysis)
        self.state["harmonics"] = harmonics
        self.state["bullet_fit"] = self._extract_summary(analysis, "bullet_fit_summary")
        self.state["game_suitability"] = self._extract_summary(
            analysis, "game_suitability_summary"
        )
        self.state["recommendation"] = self._extract_summary(analysis, "recommendation")
        self.state["recommendation_context"] = self._resolve_recommendation_context(
            analysis
        )
        self.state["guidance"] = self.build_guidance_summary(analysis)
        self.state["robustness"] = self.simulate_robustness(analysis, harmonics)
        self.state["warnings"] = self.generate_warnings()

    def _analysis_mode(self, analysis: Dict[str, Any] | None = None) -> str:
        if isinstance(analysis, dict) and analysis:
            return "service"
        state_mode = str(self.state.get("analysis_mode") or "").strip().lower()
        return state_mode or "fallback"

    def _coerce_float(self, value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except Exception:
            return None

    def _coerce_int(self, value: Any) -> int | None:
        try:
            if value in (None, ""):
                return None
            return int(value)
        except Exception:
            return None

    @staticmethod
    def _as_dict(v: Any) -> Dict[str, Any]:
        return v if isinstance(v, dict) else {}

    @staticmethod
    def _as_list(v: Any) -> list:
        return v if isinstance(v, list) else []

    def _extract_summary(
        self, analysis: Dict[str, Any] | None, key: str
    ) -> Dict[str, Any]:
        if isinstance(analysis, dict) and isinstance(analysis.get(key), dict):
            return dict(analysis.get(key) or {})
        return {}

    def _resolve_recommendation_context(
        self, analysis: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        analysis = analysis or {}
        context = self._as_dict(analysis.get("recommendation_context"))
        baseline = self._as_dict(context.get("baseline"))
        control_state = self._as_dict(context.get("control_state"))

        if not baseline:
            if isinstance(self.ammo.get("recommendation_baseline"), dict):
                baseline = dict(self.ammo.get("recommendation_baseline") or {})
            elif isinstance(self.rifle.get("recommendation_baseline"), dict):
                baseline = dict(self.rifle.get("recommendation_baseline") or {})
        if not control_state:
            if isinstance(self.ammo.get("recommendation_control_state"), dict):
                control_state = dict(
                    self.ammo.get("recommendation_control_state") or {}
                )
            elif isinstance(self.rifle.get("recommendation_control_state"), dict):
                control_state = dict(
                    self.rifle.get("recommendation_control_state") or {}
                )

        return {
            "baseline": dict(baseline or {}),
            "control_state": dict(control_state or {}),
        }

    def _format_measurement_target(self, value: float | None, unit: str) -> str | None:
        if value is None:
            return None
        return f"{value:.2f} {unit}"

    def _build_service_request(self) -> Dict[str, Any] | None:
        rifle_id = self._coerce_int(self.rifle.get("id"))
        bullet_id = self._coerce_int(
            self.ammo.get("bullet_id")
            or self.ammo.get("bullet")
            or self.rifle.get("bullet_id")
        )
        powder_id = self._coerce_int(
            self.ammo.get("powder_id") or self.ammo.get("powder")
        )
        charge_weight_gr = self._coerce_float(
            self.ammo.get("powder_charge") or self.ammo.get("charge")
        )
        coal_mm = self._coerce_float(self.ammo.get("coal_mm") or self.ammo.get("coal"))

        if (
            rifle_id is None
            or bullet_id is None
            or powder_id is None
            or charge_weight_gr is None
            or coal_mm is None
        ):
            return None

        request: Dict[str, Any] = {
            "rifle_id": int(rifle_id),
            "bullet_id": int(bullet_id),
            "powder_id": int(powder_id),
            "charge_weight_gr": float(charge_weight_gr),
            "coal_mm": float(coal_mm),
            "temperature_c": float(
                self._coerce_float(self.environment.get("temperature_c")) or 15.0
            ),
            "pressure_hpa": float(
                self._coerce_float(self.environment.get("pressure_hpa")) or 1013.25
            ),
            "humidity_percent": float(
                self._coerce_float(self.environment.get("humidity_percent")) or 50.0
            ),
            "altitude_m": float(
                self._coerce_float(self.environment.get("altitude_m")) or 0.0
            ),
            "wind_speed_mps": float(
                self._coerce_float(self.environment.get("wind_speed_mps")) or 0.0
            ),
            "wind_dir_deg": float(
                self._coerce_float(self.environment.get("wind_dir_deg")) or 90.0
            ),
            "usage_profile": str(
                self.ammo.get("usage_profile")
                or self.rifle.get("usage_profile")
                or "precision"
            ),
            "subsonic_mode": bool(
                self.ammo.get("subsonic_mode")
                or self.rifle.get("subsonic_mode")
                or False
            ),
        }

        optional_fields = {
            "primer_id": self._coerce_int(
                self.ammo.get("primer_id") or self.ammo.get("primer")
            ),
            "cbto_mm": self._coerce_float(
                self.ammo.get("cbto_mm") or self.ammo.get("cbto")
            ),
            "case_id": self._coerce_int(
                self.ammo.get("case_id") or self.rifle.get("case_id")
            ),
            "brass_batch_id": self._coerce_int(self.ammo.get("brass_batch_id")),
            "bullet_lot_id": self._coerce_int(self.ammo.get("bullet_lot_id")),
            "powder_lot_id": self._coerce_int(self.ammo.get("powder_lot_id")),
            "primer_lot_id": self._coerce_int(self.ammo.get("primer_lot_id")),
            "barrel_id": self.rifle.get("barrel_id"),
            "ammo_profile_id": self._coerce_int(self.ammo.get("ammo_profile_id")),
            "target_distance_m": self._coerce_float(
                self.environment.get("target_distance_m")
                or self.ammo.get("target_distance_m")
            ),
            "zero_distance_m": self._coerce_float(
                self.environment.get("zero_distance_m")
                or self.ammo.get("zero_distance_m")
            ),
        }
        for key, value in optional_fields.items():
            if value not in (None, ""):
                request[key] = value
        return request

    def _build_service_analysis(self) -> Dict[str, Any] | None:
        request = self._build_service_request()
        if not request:
            return None
        try:
            analysis = analyze_load(request)
        except Exception:
            return None
        return (
            analysis if isinstance(analysis, dict) and "error" not in analysis else None
        )

    def _build_smart_engine_state(
        self, analysis: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        analysis = analysis or {}
        harmonics = self._as_dict(analysis.get("harmonics"))
        recommendation = self._extract_summary(analysis, "recommendation")
        recommendation_context = self._resolve_recommendation_context(analysis)
        pressure = self._extract_summary(analysis, "pressure_assessment")
        input_quality = self._extract_summary(analysis, "input_quality")
        bullet_fit = self._extract_summary(analysis, "bullet_fit_summary")

        engine_input: Dict[str, Any] = {
            "session": {
                "usage_profile_name": str(
                    self.ammo.get("usage_profile")
                    or self.rifle.get("usage_profile")
                    or "precision"
                ).strip(),
                "next_action": str(recommendation.get("next_step") or "").strip()
                or None,
                "safety_status": (
                    "critical"
                    if str(pressure.get("level") or "").strip().lower() == "critical"
                    else "ok"
                ),
            },
            "weapon": {
                "rifle_name": self.rifle.get("name") or self.rifle.get("rifle_name"),
            },
            "barrel": {
                "barrel_id": self.rifle.get("barrel_id"),
                "barrel_name": self.rifle.get("barrel_name"),
                "learning_profile": {
                    "harmonic_score": harmonics.get("harmonic_score")
                    or harmonics.get("score"),
                    "node_bands": harmonics.get("node_bands") or [],
                },
            },
            "components": {
                "bullet": (
                    {"id": self.ammo.get("bullet_id")}
                    if self.ammo.get("bullet_id") not in (None, "")
                    else {}
                ),
                "powder": (
                    {"id": self.ammo.get("powder_id")}
                    if self.ammo.get("powder_id") not in (None, "")
                    else {}
                ),
                "primer": (
                    {"id": self.ammo.get("primer_id")}
                    if self.ammo.get("primer_id") not in (None, "")
                    else {}
                ),
                "case": (
                    {"id": self.ammo.get("case_id") or self.rifle.get("case_id")}
                    if (self.ammo.get("case_id") or self.rifle.get("case_id"))
                    not in (None, "")
                    else {}
                ),
            },
            "lots": {
                "bullet": (
                    {"id": self.ammo.get("bullet_lot_id")}
                    if self.ammo.get("bullet_lot_id") not in (None, "")
                    else {}
                ),
                "powder": (
                    {"id": self.ammo.get("powder_lot_id")}
                    if self.ammo.get("powder_lot_id") not in (None, "")
                    else {}
                ),
                "primer": (
                    {"id": self.ammo.get("primer_lot_id")}
                    if self.ammo.get("primer_lot_id") not in (None, "")
                    else {}
                ),
            },
            "load": {
                "charge_weight_gr": self._coerce_float(
                    self.ammo.get("powder_charge") or self.ammo.get("charge")
                ),
                "coal_mm": self._coerce_float(
                    self.ammo.get("coal_mm") or self.ammo.get("coal")
                ),
                "cbto_mm": self._coerce_float(
                    self.ammo.get("cbto_mm") or self.ammo.get("cbto")
                ),
                "baseline": self._as_dict(recommendation_context.get("baseline")),
                "control_state": self._as_dict(
                    recommendation_context.get("control_state")
                ),
            },
            "physics_inputs": {
                "pressure_assessment": pressure,
            },
            "evidence": {
                "summary": {
                    "batch_spread_evidence_quality": {
                        "level": (
                            "moderate"
                            if self._coerce_float(input_quality.get("score"))
                            not in (None,)
                            and (self._coerce_float(input_quality.get("score")) or 0.0)
                            >= 75.0
                            else "thin"
                        ),
                        "score": self._coerce_float(input_quality.get("score")),
                    },
                }
            },
            "learning": {
                "aggregate": {
                    "model_status": str(input_quality.get("title") or "").strip()
                    or "raw model",
                    "next_focus": str(recommendation.get("next_step") or "").strip()
                    or None,
                }
            },
            "derived": {
                "harmonics_profile": {
                    "node_bands": harmonics.get("node_bands") or [],
                    "harmonic_score": harmonics.get("harmonic_score")
                    or harmonics.get("score"),
                    "estimated_frequency_hz": harmonics.get("estimated_frequency_hz")
                    or harmonics.get("frequency_hz"),
                    "period_ms": harmonics.get("period_ms"),
                    "stability_tier": harmonics.get("stability_tier"),
                    "sensitivity": harmonics.get("sensitivity") or {},
                },
                "bullet_fit_context": {
                    "fit_summary": bullet_fit,
                },
            },
            "recommendation_context": recommendation_context,
        }
        if analysis:
            engine_input["derived"]["internal_ballistics_summary"] = (
                analysis.get("internal_ballistics_summary")
                if isinstance(analysis.get("internal_ballistics_summary"), dict)
                else {}
            )
        return {
            "engine_input": engine_input,
            "engine_result": build_engine_result_from_input(engine_input),
        }

    def _active_barrel_label(self) -> str | None:
        barrel_name = str(self.rifle.get("barrel_name") or "").strip()
        if barrel_name:
            return barrel_name
        barrel_id = str(self.rifle.get("barrel_id") or "").strip()
        return barrel_id or None

    def _estimate_fallback_velocity_mps(self) -> float:
        explicit_velocity = self._coerce_float(
            self.rifle.get("muzzle_velocity_mps")
            or self.ammo.get("muzzle_velocity_mps")
        )
        if explicit_velocity is not None:
            return explicit_velocity

        charge = (
            self._coerce_float(
                self.ammo.get("powder_charge") or self.ammo.get("charge")
            )
            or 42.0
        )
        bullet_weight = (
            self._coerce_float(
                self.ammo.get("bullet_weight") or self.rifle.get("bullet_weight_gr")
            )
            or 140.0
        )
        barrel_length_mm = (
            self._coerce_float(self.rifle.get("barrel_length_mm")) or 610.0
        )
        temperature_c = (
            self._coerce_float(self.environment.get("temperature_c")) or 15.0
        )

        velocity = 780.0
        velocity += max(-80.0, min(80.0, (charge - 42.0) * 9.0))
        velocity += max(-50.0, min(35.0, (barrel_length_mm - 610.0) * 0.18))
        velocity += max(-35.0, min(25.0, (140.0 - bullet_weight) * 0.9))
        velocity += max(-12.0, min(12.0, (temperature_c - 15.0) * 0.35))
        return round(max(450.0, velocity), 1)

    def _estimate_fallback_pressure_psi(self) -> float:
        explicit_pressure = self._coerce_float(
            self.rifle.get("pressure_psi") or self.ammo.get("pressure_psi")
        )
        if explicit_pressure is not None:
            return explicit_pressure

        charge = (
            self._coerce_float(
                self.ammo.get("powder_charge") or self.ammo.get("charge")
            )
            or 42.0
        )
        coal_mm = (
            self._coerce_float(self.ammo.get("coal_mm") or self.ammo.get("coal"))
            or 71.0
        )
        temperature_c = (
            self._coerce_float(self.environment.get("temperature_c")) or 15.0
        )

        pressure = 39500.0
        pressure += max(-5000.0, min(7000.0, (charge - 42.0) * 950.0))
        pressure += max(-2500.0, min(2500.0, (71.0 - coal_mm) * 140.0))
        pressure += max(-1200.0, min(1200.0, (temperature_c - 15.0) * 40.0))
        return round(max(18000.0, pressure), 0)

    def simulate_velocity(self, analysis: Dict[str, Any] | None = None):
        if isinstance(analysis, dict):
            result = self._as_dict(analysis.get("result"))
            velocity_fps = self._coerce_float(result.get("muzzle_velocity_fps"))
            if velocity_fps is not None:
                return round(velocity_fps * 0.3048, 1)
        return self._estimate_fallback_velocity_mps()

    def simulate_pressure(self, analysis: Dict[str, Any] | None = None):
        if isinstance(analysis, dict):
            result = self._as_dict(analysis.get("result"))
            peak_pressure = self._coerce_float(
                result.get("peak_pressure_psi") or result.get("pressure_psi")
            )
            if peak_pressure is not None:
                return round(peak_pressure, 0)
        return self._estimate_fallback_pressure_psi()

    def simulate_harmonics(self, analysis: Dict[str, Any] | None = None):
        if isinstance(analysis, dict) and isinstance(analysis.get("harmonics"), dict):
            harmonics = analysis.get("harmonics") or {}
            return {
                "node_bands": harmonics.get("node_bands") or [],
                "score": harmonics.get("harmonic_score") or harmonics.get("score"),
                "frequency_hz": harmonics.get("estimated_frequency_hz")
                or harmonics.get("frequency_hz"),
                "period_ms": harmonics.get("period_ms"),
                "stability_tier": harmonics.get("stability_tier"),
                "sensitivity": harmonics.get("sensitivity") or {},
            }

        rifle = self.rifle if isinstance(self.rifle, dict) else {}
        profile_details = dict(rifle)
        profile_details.setdefault("harmonics", {})
        try:
            harmonics = self._as_dict(
                calculate_harmonics_profile(rifle, profile_details)
            )
        except Exception:
            harmonics = {}
        return {
            "node_bands": harmonics.get("node_bands") or [],
            "score": harmonics.get("harmonic_score") or harmonics.get("score"),
            "frequency_hz": harmonics.get("estimated_frequency_hz")
            or harmonics.get("frequency_hz"),
            "period_ms": harmonics.get("period_ms"),
            "stability_tier": harmonics.get("stability_tier"),
            "sensitivity": harmonics.get("sensitivity") or {},
        }

    def simulate_robustness(
        self,
        analysis: Dict[str, Any] | None = None,
        harmonics: Dict[str, Any] | None = None,
    ):
        score = 0.7

        if isinstance(analysis, dict):
            pressure = self._extract_summary(analysis, "pressure_assessment")
            stability = self._extract_summary(analysis, "stability_assessment")
            bullet_fit = self._extract_summary(analysis, "bullet_fit_summary")
            game = self._extract_summary(analysis, "game_suitability_summary")

            level_adjustments = {
                "ok": 0.08,
                "info": 0.03,
                "warning": -0.12,
                "critical": -0.25,
                "unknown": -0.05,
                "neutral": 0.0,
            }
            for item in (pressure, stability, bullet_fit, game):
                level = str(item.get("level") or "neutral").strip().lower()
                score += level_adjustments.get(level, 0.0)

            fit_score = self._coerce_float(bullet_fit.get("fit_score"))
            if fit_score is not None:
                score += max(-0.12, min(0.12, (fit_score - 70.0) / 250.0))

        harmonic_score = self._coerce_float((harmonics or {}).get("score"))
        if harmonic_score is not None:
            score += max(-0.08, min(0.08, (harmonic_score - 10.0) / 80.0))

        if self._analysis_mode(analysis) != "service":
            score = min(score - 0.12, 0.55)

        return round(max(0.0, min(1.0, score)), 2)

    def build_guidance_summary(
        self, analysis: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        analysis = analysis or {}
        analysis_mode = self._analysis_mode(analysis)
        smart_engine = self._as_dict(self.state.get("smart_engine"))
        smart_engine_result = self._as_dict(smart_engine.get("engine_result"))
        smart_decisions = self._as_dict(smart_engine_result.get("decisions"))
        smart_guidance = self._as_dict(smart_decisions.get("guidance"))
        smart_validation_gate = self._as_dict(smart_decisions.get("validation_gate"))
        smart_execution_plan = self._as_dict(smart_decisions.get("execution_plan"))
        smart_baseline_control = self._as_dict(
            smart_engine_result.get("baseline_control")
        )
        smart_return_targets = self._as_dict(smart_engine_result.get("return_targets"))
        smart_branch_advisory = self._as_dict(
            smart_engine_result.get("branch_advisory")
        )
        smart_baseline_diagnostics = self._as_dict(
            smart_engine_result.get("baseline_diagnostics")
        )
        smart_bullet_fit = self._as_dict(smart_engine_result.get("bullet_fit"))
        smart_chamber_jump = self._as_dict(smart_engine_result.get("chamber_jump"))
        charge_target_payload = self._as_dict(smart_return_targets.get("charge"))
        seating_target_payload = self._as_dict(smart_return_targets.get("seating"))
        smart_hold = self._as_list(smart_decisions.get("do_not_change_yet"))
        smart_confidence = self._as_dict(
            smart_decisions.get("recommendation_confidence")
        )
        recommendation = self._extract_summary(analysis, "recommendation")
        recommendation_context = self._resolve_recommendation_context(analysis)
        recommendation_baseline = self._as_dict(recommendation_context.get("baseline"))
        recommendation_control_state = self._as_dict(
            recommendation_context.get("control_state")
        )
        bullet_fit = self._extract_summary(analysis, "bullet_fit_summary")
        game = self._extract_summary(analysis, "game_suitability_summary")
        pressure = self._extract_summary(analysis, "pressure_assessment")
        stability = self._extract_summary(analysis, "stability_assessment")
        input_quality = self._extract_summary(analysis, "input_quality")

        charge = self._coerce_float(
            self.ammo.get("powder_charge") or self.ammo.get("charge")
        )
        coal_mm = self._coerce_float(self.ammo.get("coal_mm") or self.ammo.get("coal"))
        cbto_mm = self._coerce_float(self.ammo.get("cbto_mm") or self.ammo.get("cbto"))
        charge_window = self._as_list(recommendation.get("charge_window_gr"))
        seating_window = self._as_list(recommendation.get("seating_window_mm"))

        fit_score = self._coerce_float(bullet_fit.get("fit_score"))
        quality_score = self._coerce_float(input_quality.get("score"))

        trust_score = 55.0
        if fit_score is not None:
            trust_score += max(-12.0, min(18.0, (fit_score - 70.0) / 2.5))
        if quality_score is not None:
            trust_score += max(-10.0, min(20.0, (quality_score - 60.0) / 2.5))

        level_adjustments = {
            "ok": 8.0,
            "info": 3.0,
            "warning": -12.0,
            "critical": -24.0,
            "unknown": -6.0,
            "neutral": 0.0,
        }
        for item in (pressure, stability, game):
            level = str(item.get("level") or "neutral").strip().lower()
            trust_score += level_adjustments.get(level, 0.0)

        if analysis_mode != "service":
            trust_score = min(trust_score, 42.0)
        trust_score = max(0.0, min(100.0, trust_score))

        trust_label = "Low trust"
        if analysis_mode == "service" and trust_score >= 75.0:
            trust_label = "High trust"
        elif analysis_mode == "service" and trust_score >= 55.0:
            trust_label = "Medium trust"

        charge_alignment = "unknown"
        charge_delta = None
        charge_baseline_kind = "recommended"
        baseline_charge = self._coerce_float(recommendation_baseline.get("charge_gr"))
        charge_return_target = self._format_measurement_target(baseline_charge, "gr")
        if baseline_charge is not None and charge is not None:
            charge_delta = round(charge - baseline_charge, 2)
            charge_alignment = "aligned" if abs(charge_delta) <= 0.05 else "outside"
            if (
                str(recommendation_baseline.get("charge_source") or "").strip().lower()
                == "learned"
            ):
                charge_baseline_kind = "learned"
        elif len(charge_window) == 2 and charge is not None:
            charge_min = self._coerce_float(charge_window[0])
            charge_max = self._coerce_float(charge_window[1])
            if charge_min is not None and charge_max is not None:
                charge_mid = (charge_min + charge_max) / 2.0
                charge_delta = round(charge - charge_mid, 2)
                charge_alignment = (
                    "aligned" if charge_min <= charge <= charge_max else "outside"
                )

        seating_alignment = "unknown"
        seating_delta = None
        seating_baseline_kind = "recommended"
        baseline_cbto = self._coerce_float(recommendation_baseline.get("cbto_mm"))
        baseline_coal = self._coerce_float(recommendation_baseline.get("coal_mm"))
        seating_return_target = self._format_measurement_target(
            baseline_cbto, "mm CBTO"
        )
        seating_return_target_unit = "cbto_mm" if baseline_cbto is not None else None
        if seating_return_target is None:
            seating_return_target = self._format_measurement_target(
                baseline_coal, "mm COAL"
            )
            if seating_return_target is not None:
                seating_return_target_unit = "coal_mm"
        if baseline_cbto is not None and cbto_mm is not None:
            seating_delta = round(cbto_mm - baseline_cbto, 2)
            seating_alignment = "aligned" if abs(seating_delta) <= 0.03 else "outside"
            if (
                str(recommendation_baseline.get("seating_source") or "").strip().lower()
                == "learned"
            ):
                seating_baseline_kind = "learned"
        elif baseline_coal is not None and coal_mm is not None:
            seating_delta = round(coal_mm - baseline_coal, 2)
            seating_alignment = "aligned" if abs(seating_delta) <= 0.03 else "outside"
            if (
                str(recommendation_baseline.get("seating_source") or "").strip().lower()
                == "learned"
            ):
                seating_baseline_kind = "learned"
        elif len(seating_window) == 2 and coal_mm is not None:
            seat_min = self._coerce_float(seating_window[0])
            seat_max = self._coerce_float(seating_window[1])
            if seat_min is not None and seat_max is not None:
                seating_delta = round((seat_min + seat_max) / 2.0, 2)
                seating_alignment = (
                    "aligned" if seat_min <= 0.0 <= seat_max else "outside"
                )

        recommended_baseline_bits: list[str] = []
        bullet_baseline = str(bullet_fit.get("recommended_baseline") or "").strip()
        if bullet_baseline:
            recommended_baseline_bits.append(bullet_baseline)
        if baseline_charge is not None:
            prefix = (
                "learned charge"
                if charge_baseline_kind == "learned"
                else "modeled charge baseline"
            )
            recommended_baseline_bits.append(f"{prefix} {baseline_charge:.2f} gr")
        if len(charge_window) == 2:
            recommended_baseline_bits.append(
                f"charge window {charge_window[0]} to {charge_window[1]} gr"
            )
        if baseline_cbto is not None:
            prefix = (
                "learned seating"
                if seating_baseline_kind == "learned"
                else "modeled seating baseline"
            )
            recommended_baseline_bits.append(f"{prefix} {baseline_cbto:.2f} mm CBTO")
        elif baseline_coal is not None:
            prefix = (
                "learned seating"
                if seating_baseline_kind == "learned"
                else "modeled seating baseline"
            )
            recommended_baseline_bits.append(f"{prefix} {baseline_coal:.2f} mm COAL")
        if len(seating_window) == 2:
            recommended_baseline_bits.append(
                f"seating offset {seating_window[0]} to {seating_window[1]} mm"
            )

        next_step = str(recommendation.get("next_step") or "").strip()
        if not next_step:
            next_step = (
                str(smart_guidance.get("setup_line") or "").strip()
                or "Collect more data before tightening the recommendation."
            )
        if charge_alignment == "outside" and charge_baseline_kind == "learned":
            next_step = "Return to the learned charge baseline"
            if charge_return_target:
                next_step += f" at {charge_return_target}"
            next_step += " or confirm a new charge node before treating this setup as learned again."
        elif charge_alignment == "outside" and charge_return_target:
            next_step = f"Return to the modeled charge baseline at {charge_return_target} or validate a new charge before updating the recommendation."
        elif seating_alignment == "outside" and seating_baseline_kind == "learned":
            next_step = "Return to the learned seating baseline"
            if seating_return_target:
                next_step += f" at {seating_return_target}"
            next_step += " or confirm a new sweet spot before treating this setup as learned again."
        elif seating_alignment == "outside" and seating_return_target:
            next_step = f"Return to the modeled seating baseline at {seating_return_target} or validate a new sweet spot before updating the recommendation."

        basis_note = ""
        if analysis_mode != "service":
            basis_note = "Preview only: the twin is running on fallback estimates and heuristic barrel modeling, not a full load-analysis result."
            next_step = "Preview only. Add full component IDs and measured chrono/group data before treating this as load guidance."

        guidance_level = "ok"
        if any(
            str(item.get("level") or "") == "critical"
            for item in (pressure, stability, bullet_fit)
            if isinstance(item, dict)
        ):
            guidance_level = "critical"
        elif any(
            str(item.get("level") or "") == "warning"
            for item in (pressure, stability, bullet_fit, game)
            if isinstance(item, dict)
        ):
            guidance_level = "warning"
        if analysis_mode != "service" and guidance_level == "ok":
            guidance_level = "warning"

        barrel_label = self._active_barrel_label()
        if barrel_label:
            pressure_diagnostic_note = f"On barrel {barrel_label}, primer appearance is only a supporting pressure and fault-diagnosis clue. It does not determine accuracy on its own, and similar signs can come from charge weight, chamber soot, seating depth, fouling, or other setup issues."
        else:
            pressure_diagnostic_note = "Primer appearance is only a supporting pressure and fault-diagnosis clue. It does not determine accuracy on its own, and similar signs can come from charge weight, chamber soot, seating depth, fouling, or other setup issues."

        return {
            "level": guidance_level,
            "analysis_mode": analysis_mode,
            "trust_score": round(trust_score, 1),
            "trust_label": trust_label,
            "recommended_baseline": "; ".join(recommended_baseline_bits),
            "next_step": next_step,
            "basis_note": basis_note,
            "charge_alignment": charge_alignment,
            "charge_baseline_label": (
                "learned baseline"
                if charge_baseline_kind == "learned"
                else "modeled baseline"
            ),
            "charge_delta_gr": charge_delta,
            "charge_baseline_kind": charge_baseline_kind,
            "charge_return_target": charge_return_target,
            "charge_return_target_gr": baseline_charge,
            "seating_alignment": seating_alignment,
            "seating_baseline_label": (
                "learned baseline"
                if seating_baseline_kind == "learned"
                else "modeled baseline"
            ),
            "seating_delta_mm": seating_delta,
            "seating_baseline_kind": seating_baseline_kind,
            "seating_return_target": seating_return_target,
            "seating_return_target_mm": (
                baseline_cbto if baseline_cbto is not None else baseline_coal
            ),
            "seating_return_target_unit": seating_return_target_unit,
            "charge_state": str(recommendation_control_state.get("charge_state") or "")
            .strip()
            .lower()
            or None,
            "seating_state": str(
                recommendation_control_state.get("seating_state") or ""
            )
            .strip()
            .lower()
            or None,
            "input_quality_title": str(input_quality.get("title") or "").strip(),
            "input_quality_message": str(input_quality.get("message") or "").strip(),
            "pressure_diagnostic_note": pressure_diagnostic_note,
            "engine_next_step": str(smart_guidance.get("title") or "").strip(),
            "engine_gate": str(smart_validation_gate.get("label") or "").strip(),
            "engine_gate_next": str(
                smart_validation_gate.get("next_gate") or ""
            ).strip(),
            "engine_protocol": str(smart_execution_plan.get("summary") or "").strip(),
            "engine_hold": next(
                (str(item).strip() for item in smart_hold if str(item).strip()), ""
            ),
            "engine_confidence_label": str(smart_confidence.get("level") or "").strip(),
            "engine_confidence_score": self._coerce_float(
                smart_confidence.get("score")
            ),
            "engine_confidence_note": str(
                smart_confidence.get("summary") or ""
            ).strip(),
            "engine_branch_state": str(
                smart_baseline_control.get("branch_state") or ""
            ).strip(),
            "engine_baseline_summary": str(
                smart_baseline_control.get("summary") or ""
            ).strip(),
            "engine_branch_label": str(
                smart_branch_advisory.get("label") or ""
            ).strip(),
            "engine_branch_compare_mode": str(
                smart_branch_advisory.get("compare_mode") or ""
            ).strip(),
            "engine_branch_display": str(
                smart_branch_advisory.get("display_line") or ""
            ).strip(),
            "engine_branch_action": str(
                smart_branch_advisory.get("action_line") or ""
            ).strip(),
            "engine_active_return": str(
                smart_baseline_control.get("active_return_line") or ""
            ).strip(),
            "engine_baseline_status": str(
                smart_baseline_diagnostics.get("status") or ""
            ).strip(),
            "engine_baseline_item": next(
                (
                    str(item).strip()
                    for item in (smart_baseline_diagnostics.get("items") or [])
                    if str(item).strip()
                ),
                "",
            ),
            "engine_charge_target": str(
                charge_target_payload.get("label") or ""
            ).strip(),
            "engine_seating_target": str(
                seating_target_payload.get("label") or ""
            ).strip(),
            "engine_bullet_fit_level": str(smart_bullet_fit.get("level") or "").strip(),
            "engine_bullet_fit_message": str(
                smart_bullet_fit.get("message") or ""
            ).strip(),
            "engine_jump_band": str(smart_chamber_jump.get("jump_band") or "").strip(),
            "engine_jump_summary": str(smart_chamber_jump.get("summary") or "").strip(),
        }

    def generate_warnings(self):
        warnings = []
        analysis_mode = self._analysis_mode(self.state.get("analysis"))
        if analysis_mode != "service":
            warnings.append(
                "Preview only: fallback estimates are not enough to lock a load. Add full component context and measured data first."
            )
        elif self.state["predicted_pressure"] > 45000:
            warnings.append("Pressure is near the limit.")
        if self.state["robustness"] < 0.7:
            if analysis_mode == "service":
                warnings.append("The load is sensitive to small changes.")
            else:
                warnings.append(
                    "Fallback preview suggests the setup may be sensitive to small changes."
                )
        bullet_fit = self._as_dict(self.state.get("bullet_fit"))
        game = self._as_dict(self.state.get("game_suitability"))
        analysis_state = self._as_dict(self.state.get("analysis"))
        stability = self._as_dict(analysis_state.get("stability_assessment"))
        if str(bullet_fit.get("level") or "") in {"warning", "critical"}:
            warnings.append(
                str(bullet_fit.get("message") or "Bullet fit needs confirmation.")
            )
        if str(game.get("level") or "") == "warning":
            warnings.append(
                str(game.get("message") or "Game suitability is conditional.")
            )
        if str(stability.get("level") or "") == "critical":
            warnings.append(str(stability.get("message") or "Stability is critical."))
        guidance = self._as_dict(self.state.get("guidance"))
        barrel_label = self._active_barrel_label()
        _pressure_level = str(
            self._as_dict(
                self._as_dict(self.state.get("analysis")).get("pressure_assessment")
            ).get("level")
            or ""
        )
        if isinstance(guidance, dict):
            if analysis_mode == "service" and _pressure_level in {
                "warning",
                "critical",
            }:
                if barrel_label:
                    warnings.append(
                        f"Primer signs on barrel {barrel_label} are advisory only. Treat them as one pressure clue among charge, fouling, chamber condition, and seating-depth effects."
                    )
                else:
                    warnings.append(
                        "Primer signs are advisory only. Treat them as one pressure clue among charge, fouling, chamber condition, and seating-depth effects."
                    )
            if str(guidance.get("charge_alignment") or "") == "outside":
                if str(guidance.get("charge_baseline_kind") or "") == "learned":
                    warnings.append("Current charge sits outside the learned baseline.")
                else:
                    warnings.append(
                        "Current charge sits outside the recommended window."
                    )
            if (
                str(guidance.get("seating_alignment") or "") == "outside"
                and str(guidance.get("seating_baseline_kind") or "") == "learned"
            ):
                warnings.append("Current seating sits outside the learned baseline.")
            if str(guidance.get("trust_label") or "") == "Low trust":
                warnings.append(
                    "Recommendation trust is still low; collect more evidence before locking the load."
                )
            if str(guidance.get("engine_hold") or "").strip():
                warnings.append(str(guidance.get("engine_hold")).strip())
            if str(guidance.get("engine_gate") or "").strip():
                gate_warning = str(guidance.get("engine_gate")).strip()
                next_gate = str(guidance.get("engine_gate_next") or "").strip()
                if next_gate:
                    gate_warning += f": {next_gate}"
                warnings.append(gate_warning)
        return warnings

    def apply_change(self, field: str, value: Any):
        # Endre rifle/ammo/environment og oppdater modell
        if field in self.rifle:
            self.rifle[field] = value
        elif field in self.ammo:
            self.ammo[field] = value
        elif field in self.environment:
            self.environment[field] = value
        self.update_model()

    def get_state(self):
        return self.state

    def simulate_with_plot(self):
        """Compatibility helper for the older UI code."""
        harmonics = self.state.get("harmonics", {})
        bullet_fit = self._as_dict(self.state.get("bullet_fit"))
        game = self._as_dict(self.state.get("game_suitability"))
        guidance = self._as_dict(self.state.get("guidance"))
        result = [
            f"Predicted velocity: {self.state.get('predicted_velocity')} m/s",
            f"Predicted pressure: {self.state.get('predicted_pressure')} psi",
            f"Harmonic score: {harmonics.get('score', 'N/A')}",
            f"Stability: {harmonics.get('stability_tier', 'N/A')}",
            f"Bullet fit: {bullet_fit.get('title', 'N/A')}",
            f"Game suitability: {game.get('title', 'N/A')}",
            f"Guidance trust: {guidance.get('trust_label', 'N/A')} ({guidance.get('trust_score', 'N/A')})",
            f"Next step: {guidance.get('next_step', 'N/A')}",
            f"Engine next: {guidance.get('engine_next_step', 'N/A')}",
            f"Charge target: {guidance.get('charge_return_target', 'N/A')}",
            f"Seating target: {guidance.get('seating_return_target', 'N/A')}",
            f"Robustness: {self.state.get('robustness', 'N/A')}",
        ]
        plot = (
            "predicted_velocity="
            + str(self.state.get("predicted_velocity"))
            + ", predicted_pressure="
            + str(self.state.get("predicted_pressure"))
            + ", harmonic_score="
            + str(harmonics.get("score", "N/A"))
            + ", bullet_fit="
            + str(bullet_fit.get("fit_score", "N/A"))
            + ", trust="
            + str(guidance.get("trust_score", "N/A"))
            + ", robustness="
            + str(self.state.get("robustness", "N/A"))
        )
        return "\n".join(result), f"[{plot}]"


# Eksempel på bruk:
if __name__ == "__main__":
    rifle = {"barrel_length": 610, "profile": "medium", "tuner": None}
    ammo = {"bullet": "Lapua 139gr", "powder": "N150", "charge": 44.0}
    environment = {"temp": 15, "pressure": 1013}
    twin = DigitalTwin(rifle, ammo, environment)
    print("Digital Twin State:", twin.get_state())
    twin.apply_change("charge", 45.0)
    print("Updated State:", twin.get_state())
