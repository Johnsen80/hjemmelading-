from __future__ import annotations

from typing import Any

try:
    from src.utils.i18n import tr as _tr_real

    def tr(x, **kwargs):
        return _tr_real(x, **kwargs)  # type: ignore[misc]

except Exception:

    def tr(x, **kwargs):
        return x  # type: ignore[misc]


from src.utils.unit_preferences import (
    format_length_delta_mm,
    format_pressure_psi,
    format_velocity_delta_fps,
    format_velocity_fps,
    format_weight_grains,
)

try:
    from PyQt6.QtCore import Qt
except Exception:
    pass  # type: ignore[assignment]


def __getattr__(name: str) -> Any:
    """Lazily pull module-level helpers from modern_load_builder at runtime.

    All the advisory/summary helpers (summarize_pressure_risk,
    _advisory_style, build_runtime_analysis_context, etc.) are defined as
    module-level functions inside modern_load_builder.  By the time any of
    the mixin methods are actually *called*, modern_load_builder is fully
    loaded, so this deferred lookup is safe.
    """
    import src.modules.modern_load_builder as _mlb  # noqa: PLC0415

    if hasattr(_mlb, name):
        val = getattr(_mlb, name)
        globals()[name] = val  # cache for subsequent calls
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class _MLBStatsMixin:
    """Statistics, safety panel, and scope comparison methods."""

    def update_stats(self, result):
        """Update statistics display"""
        self.stat_pressure.setText(
            f"Pressure: {format_pressure_psi(result['peak_pressure_psi'])}"
        )
        self.stat_velocity.setText(
            f"Velocity: {format_velocity_fps(result['muzzle_velocity_fps'])}"
        )
        self.stat_energy.setText(f"Energy: {result['energy_ft_lbs']:.0f} ft-lbs")
        self.stat_barrel_time.setText(f"Time: {result['barrel_time_ms']:.2f} ms")

        safety = result["safety_margin_percent"]
        color = "#27ae60" if safety > 15 else "#e67e22" if safety > 10 else "#e74c3c"
        emoji = "🟢" if safety > 15 else "🟠" if safety > 10 else "🔴"

        self.stat_safety.setText(tr("mlb_safety_display", emoji=emoji, margin=safety))
        self.stat_safety.setStyleSheet(
            f"color: {color}; font-weight: bold; padding: 8px; font-size: 10pt;"
        )

        try:
            self._update_safety_panel(result)
        except Exception:
            pass

        # Update rich metric cards
        try:
            self._update_metric_cards(result)
        except Exception:
            pass

        # Keep charge slider gradient in sync with safe-max charge
        try:
            safe_max = result.get("safe_max_charge_gr") or result.get("max_charge_gr")
            if safe_max is not None:
                self._last_safe_max_charge_gr = float(safe_max)
                self._apply_charge_slider_gradient(float(safe_max))
        except Exception:
            pass

        # Update scope comparison with previous load
        self.update_scope_comparison(result)

    def _update_safety_panel(self, result):
        if not hasattr(self, "safety_status_label"):
            return

        service_analysis = (
            self._latest_load_analysis
            if isinstance(getattr(self, "_latest_load_analysis", None), dict)
            else {}
        )
        analysis = service_analysis
        workflow_data = {
            "rifle_id": (
                self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None
            ),
            "bullet_id": (
                self.bullet_data.get("id")
                if isinstance(self.bullet_data, dict)
                else None
            ),
        }

        safety = result.get("safety_margin_percent")
        peak = result.get("peak_pressure_psi")
        saami_max = result.get("max_pressure_psi")

        details = self._get_rifle_profile_details()
        profile_limit = details.get("pressure_limit_psi") if details else None
        try:
            profile_limit = float(profile_limit) if profile_limit is not None else None
        except Exception:
            profile_limit = None

        display_max = profile_limit or saami_max
        display_margin = safety
        if display_max is not None and peak is not None:
            try:
                display_margin = (
                    (float(display_max) - float(peak)) / float(display_max) * 100.0
                )
            except Exception:
                display_margin = safety

        if display_margin is None:
            self.safety_status_label.setText(tr("mlb_safety_unavailable"))
            self.safety_status_label.setProperty("variant", "warningText")
            self.safety_status_label.setStyleSheet("")
        elif display_margin >= 15:
            self.safety_status_label.setText(tr("mlb_safety_ok", margin=display_margin))
            self.safety_status_label.setProperty("variant", "successText")
            self.safety_status_label.setStyleSheet("")
        elif display_margin >= 10:
            self.safety_status_label.setText(
                tr("mlb_safety_caution", margin=display_margin)
            )
            self.safety_status_label.setProperty("variant", "warningText")
            self.safety_status_label.setStyleSheet("")
        else:
            self.safety_status_label.setText(
                tr("mlb_safety_high_risk", margin=display_margin)
            )
            self.safety_status_label.setProperty("variant", "warningText")
            self.safety_status_label.setStyleSheet("color: #b91c1c; font-weight: 700;")

        if display_margin is not None:
            self.safety_margin_label.setText(
                tr("mlb_safety_margin_value", margin=display_margin)
            )
        if peak is not None:
            self.safety_pressure_label.setText(
                f"{tr('mlb_peak_pressure')}: {format_pressure_psi(peak)}"
            )
        if display_max is not None:
            label = tr("mlb_max_pressure")
            if profile_limit is not None:
                label = tr("mlb_max_pressure_profile")
            self.safety_saami_label.setText(
                f"{label}: {format_pressure_psi(display_max)}"
            )

        mag_limit = None
        try:
            mag_limit = details.get("magazine_length_mm") if details else None
        except Exception:
            mag_limit = None
        if mag_limit is None:
            try:
                mag_limit = self.rifle_data.get("max_coal_magazine_mm")
            except Exception:
                mag_limit = None
        if mag_limit is not None:
            self.safety_mag_label.setText(
                tr("mlb_magazine_limit_value", value=float(mag_limit))
            )
        else:
            self.safety_mag_label.setText(tr("mlb_magazine_limit_missing"))

        if (
            profile_limit is not None
            and peak is not None
            and display_margin is not None
        ):
            color = (
                "#27ae60"
                if display_margin > 15
                else "#e67e22" if display_margin > 10 else "#e74c3c"
            )
            emoji = (
                "🟢" if display_margin > 15 else "🟠" if display_margin > 10 else "🔴"
            )
            self.stat_safety.setText(
                tr("mlb_safety_display", emoji=emoji, margin=display_margin)
            )
            self.stat_safety.setStyleSheet(
                f"color: {color}; font-weight: bold; padding: 8px; font-size: 10pt;"
            )

        runtime = self._get_cached_or_active_load_session_runtime()
        runtime_analysis_context = build_runtime_analysis_context(
            runtime, service_analysis
        )
        pressure_risk = (
            runtime_analysis_context.get("pressure_assessment")
            if isinstance(runtime_analysis_context.get("pressure_assessment"), dict)
            and runtime_analysis_context.get("pressure_assessment")
            else summarize_pressure_risk(result)
        )
        if pressure_risk["level"] == "critical":
            self.pressure_alert_label.setStyleSheet(
                "padding: 8px; border-radius: 6px; background: #fee2e2; color: #991b1b; font-weight: 700;"
            )
        elif pressure_risk["level"] == "warning":
            self.pressure_alert_label.setStyleSheet(
                "padding: 8px; border-radius: 6px; background: #fef3c7; color: #92400e; font-weight: 700;"
            )
        elif pressure_risk["level"] == "ok":
            self.pressure_alert_label.setStyleSheet(
                "padding: 8px; border-radius: 6px; background: #dcfce7; color: #166534; font-weight: 700;"
            )
        else:
            self.pressure_alert_label.setStyleSheet(
                "padding: 8px; border-radius: 6px; background: #f3f4f6; color: #374151;"
            )
        self.pressure_alert_label.setText(
            f"{pressure_risk['title']}: {pressure_risk['message']}"
        )

        if hasattr(self, "powder_lot_alert_label"):
            powder_context = self._get_selected_powder_context()
            powder_lot_risk = summarize_powder_lot_advisory(
                self.db,
                powder_context.get("id") if isinstance(powder_context, dict) else None,
            )
            powder_model_risk = summarize_powder_model_advisory(
                powder_context if isinstance(powder_context, dict) else None
            )
            display_risk = powder_model_risk
            if powder_model_risk["level"] not in {"critical", "warning"}:
                display_risk = powder_lot_risk
            if display_risk["level"] == "critical":
                self.powder_lot_alert_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fee2e2; color: #991b1b; font-weight: 700;"
                )
            elif display_risk["level"] == "warning":
                self.powder_lot_alert_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fef3c7; color: #92400e; font-weight: 700;"
                )
            elif display_risk["level"] == "ok":
                self.powder_lot_alert_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #dcfce7; color: #166534; font-weight: 700;"
                )
            else:
                self.powder_lot_alert_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #f3f4f6; color: #374151;"
                )
            self.powder_lot_alert_label.setText(
                f"{display_risk['title']}: {display_risk['message']}"
            )

        if hasattr(self, "component_verification_label"):
            bullet_id = (
                self.bullet_data.get("id")
                if isinstance(self.bullet_data, dict)
                else None
            )
            primer_id = (
                self.primer_data.get("id")
                if isinstance(self.primer_data, dict)
                else None
            )
            powder_id = (
                powder_context.get("id") if isinstance(powder_context, dict) else None
            )
            component_plan = summarize_component_verification_plan(
                self.db, powder_id, bullet_id, primer_id
            )
            if component_plan["level"] == "critical":
                self.component_verification_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fee2e2; color: #991b1b; font-weight: 700;"
                )
            elif component_plan["level"] == "warning":
                self.component_verification_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fef3c7; color: #92400e; font-weight: 700;"
                )
            elif component_plan["level"] == "ok":
                self.component_verification_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #dcfce7; color: #166534; font-weight: 700;"
                )
            else:
                self.component_verification_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #f3f4f6; color: #374151;"
                )
            self.component_verification_label.setText(
                f"{component_plan['title']}: {component_plan['message']}"
            )

        if hasattr(self, "retest_advisor_label"):
            retest_advisor = summarize_retest_advisor(
                self.db,
                (
                    self.rifle_data.get("id")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                bullet_data=(
                    self.bullet_data if isinstance(self.bullet_data, dict) else None
                ),
                powder_data=(
                    powder_context if isinstance(powder_context, dict) else None
                ),
                primer_data=(
                    self.primer_data if isinstance(self.primer_data, dict) else None
                ),
                current_charge=float(self.current_charge or 0),
                coal_mm=float(self.coal_mm or 0),
                cbto_mm=float(self.cbto_mm or 0),
                result=result if isinstance(result, dict) else None,
            )
            if retest_advisor["level"] == "critical":
                self.retest_advisor_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fee2e2; color: #991b1b; font-weight: 700;"
                )
            elif retest_advisor["level"] == "warning":
                self.retest_advisor_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fef3c7; color: #92400e; font-weight: 700;"
                )
            elif retest_advisor["level"] == "ok":
                self.retest_advisor_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #dcfce7; color: #166534; font-weight: 700;"
                )
            else:
                self.retest_advisor_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #f3f4f6; color: #374151;"
                )
            self.retest_advisor_label.setText(
                f"{retest_advisor['title']}: {retest_advisor['message']}"
            )

        barrel_details = self._get_active_barrel_details()
        twist_inches = self._parse_twist_inches(
            barrel_details.get("twist") or (self.rifle_data or {}).get("twist_rate")
        )
        caliber_text = str(
            barrel_details.get("caliber")
            or (self.rifle_data or {}).get("caliber")
            or ""
        ).lower()
        stability = self._estimate_gyroscopic_stability(
            self.bullet_data if isinstance(self.bullet_data, dict) else {},
            twist_inches,
            caliber_text,
            result.get("muzzle_velocity_fps") if isinstance(result, dict) else None,
        )
        subsonic_mode = bool(
            getattr(self, "subsonic_cb", None) and self.subsonic_cb.isChecked()
        )
        subsonic_target_fps = self._subsonic_target_fps()
        subsonic_history = summarize_subsonic_history_advisory(
            self.db,
            self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None,
            self.bullet_data.get("id") if isinstance(self.bullet_data, dict) else None,
            powder_context.get("id") if isinstance(powder_context, dict) else None,
        )
        model_match = summarize_model_vs_measured_advisory(
            self.db,
            self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None,
            self.bullet_data.get("id") if isinstance(self.bullet_data, dict) else None,
            powder_context.get("id") if isinstance(powder_context, dict) else None,
            current_charge_grains=(
                float(self.current_charge or 0)
                if self.current_charge is not None
                else None
            ),
            current_cbto_mm=(
                float(self.cbto_mm or 0) if self.cbto_mm is not None else None
            ),
            predicted_velocity_fps=(
                float(result.get("muzzle_velocity_fps"))
                if isinstance(result, dict)
                and isinstance(result.get("muzzle_velocity_fps"), (int, float))
                else None
            ),
            subsonic_mode=subsonic_mode,
            current_powder_lot_number=str(
                powder_context.get("lot_number")
                or powder_context.get("selected_lot_number")
                or ""
            ).strip(),
            target_temperature_c=(
                float(result.get("_environment", {}).get("temperature_c"))
                if isinstance(result, dict)
                and isinstance(result.get("_environment"), dict)
                and isinstance(
                    result.get("_environment", {}).get("temperature_c"), (int, float)
                )
                else None
            ),
        )

        if hasattr(self, "stability_advisor_label"):
            stability_advisor = (
                service_analysis.get("stability_assessment")
                if isinstance(service_analysis.get("stability_assessment"), dict)
                else summarize_stability_advisor(
                    stability,
                    result=result if isinstance(result, dict) else None,
                    subsonic_mode=subsonic_mode,
                    twist_inches=twist_inches,
                    bullet=(
                        self.bullet_data if isinstance(self.bullet_data, dict) else None
                    ),
                    barrel_details=barrel_details,
                    rifle_data=(
                        self.rifle_data if isinstance(self.rifle_data, dict) else None
                    ),
                )
            )
            self.stability_advisor_label.setStyleSheet(
                _advisory_style(stability_advisor["level"])
            )
            detail_suffix = ""
            checks = stability_advisor.get("checks") or []
            if checks:
                detail_suffix = f" ({checks[0]})"
            self.stability_advisor_label.setText(
                f"{stability_advisor['title']}: {stability_advisor['message']}{detail_suffix}"
            )

        if hasattr(self, "bullet_fit_label"):
            bullet_geometry = (
                service_analysis.get("bullet_geometry")
                if isinstance(service_analysis.get("bullet_geometry"), dict)
                else {}
            )
            harmonic_context = (
                service_analysis.get("harmonics")
                if isinstance(service_analysis.get("harmonics"), dict)
                else {}
            )
            bullet_fit = (
                service_analysis.get("bullet_fit_summary")
                if isinstance(service_analysis.get("bullet_fit_summary"), dict)
                else summarize_bullet_fit_advisor(
                    bullet=(
                        self.bullet_data if isinstance(self.bullet_data, dict) else None
                    ),
                    bullet_geometry=bullet_geometry,
                    stability=stability if isinstance(stability, dict) else None,
                    stability_assessment=(
                        stability_advisor
                        if isinstance(stability_advisor, dict)
                        else None
                    ),
                    harmonics=harmonic_context,
                    twist_inches=twist_inches,
                    result=result if isinstance(result, dict) else None,
                )
            )
            self.bullet_fit_label.setStyleSheet(
                _advisory_style(str(bullet_fit.get("level") or "unknown"))
            )
            fit_score = _coerce_float(bullet_fit.get("fit_score"))
            fit_checks = [
                str(item).strip()
                for item in (bullet_fit.get("checks") or [])
                if str(item).strip()
            ]
            fit_title = str(bullet_fit.get("title") or "Bullet Fit").strip()
            fit_message = str(bullet_fit.get("message") or "").strip()
            fit_meta: list[str] = []
            if fit_score is not None:
                fit_meta.append(
                    _status_pill(f"Fit {fit_score:.0f}/100", bullet_fit.get("level"))
                )
            geometry_confidence = str(
                bullet_fit.get("geometry_confidence") or ""
            ).strip()
            if geometry_confidence:
                fit_meta.append(
                    _status_pill(f"Geometry {geometry_confidence.title()}", "info")
                )
            fit_html = f"<b>{fit_title}</b>: {fit_message}"
            if fit_meta:
                fit_html += "<br>" + "".join(fit_meta)
            recommended_baseline = str(
                bullet_fit.get("recommended_baseline") or ""
            ).strip()
            if recommended_baseline:
                fit_html += (
                    "<br><span style='font-weight:400'>Recommended baseline: "
                    + recommended_baseline
                    + "</span>"
                )
            if fit_checks:
                fit_html += (
                    "<br><span style='font-weight:400'>"
                    + " | ".join(fit_checks[:2])
                    + "</span>"
                )
            self.bullet_fit_label.setText(fit_html)

        if hasattr(self, "subsonic_advisor_label"):
            subsonic_advisor = summarize_subsonic_advisor(
                result if isinstance(result, dict) else None,
                enabled=subsonic_mode,
                target_velocity_fps=subsonic_target_fps,
                stability=stability,
            )
            display_level = subsonic_advisor["level"]
            if subsonic_history["level"] == "critical":
                display_level = "critical"
            elif subsonic_history["level"] == "warning" and display_level not in {
                "critical",
                "warning",
            }:
                display_level = "warning"
            self.subsonic_advisor_label.setStyleSheet(_advisory_style(display_level))
            detail_bits = []
            checks = subsonic_advisor.get("checks") or []
            if checks:
                detail_bits.append(str(checks[0]))
            history_checks = subsonic_history.get("checks") or []
            if history_checks:
                detail_bits.append(str(history_checks[0]))
            history_title = str(subsonic_history.get("title") or "").strip()
            history_message = str(subsonic_history.get("message") or "").strip()
            history_suffix = ""
            if history_title and history_title != "No subsonic history yet":
                history_suffix = f" History: {history_title.lower()}."
            elif history_message and subsonic_history.get("level") != "unknown":
                history_suffix = f" History: {history_message}"
            detail_suffix = f" ({' | '.join(detail_bits)})" if detail_bits else ""
            self.subsonic_advisor_label.setText(
                f"{subsonic_advisor['title']}: {subsonic_advisor['message']}{history_suffix}{detail_suffix}"
            )

        if hasattr(self, "model_vs_measured_label"):
            self.model_vs_measured_label.setStyleSheet(
                _advisory_style(model_match["level"])
            )
            model_checks = model_match.get("checks") or []
            model_suffix_bits = []
            if model_checks:
                model_suffix_bits.append(str(model_checks[0]))
            bias_direction = str(model_match.get("bias_direction") or "").strip()
            bias_fps = model_match.get("bias_fps")
            if isinstance(bias_fps, (int, float)):
                if bias_direction == "model_higher":
                    model_suffix_bits.append(
                        f"bias: the model often runs about {format_velocity_delta_fps(abs(float(bias_fps))).lstrip('+')} high"
                    )
                elif bias_direction == "measured_higher":
                    model_suffix_bits.append(
                        f"bias: the model often runs about {format_velocity_delta_fps(abs(float(bias_fps))).lstrip('+')} low"
                    )
            model_suffix = (
                f" ({' | '.join(model_suffix_bits)})" if model_suffix_bits else ""
            )
            self.model_vs_measured_label.setText(
                f"{model_match['title']}: {model_match['message']}{model_suffix}"
            )

        if hasattr(self, "impact_window_label"):
            impact_window = (
                service_analysis.get("terminal_summary")
                if isinstance(service_analysis.get("terminal_summary"), dict)
                and service_analysis.get("terminal_summary")
                else summarize_builder_impact_window(
                    self.db,
                    self.bullet_data if isinstance(self.bullet_data, dict) else None,
                    result,
                )
            )
            if impact_window["level"] == "critical":
                self.impact_window_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fee2e2; color: #991b1b; font-weight: 700;"
                )
            elif impact_window["level"] == "warning":
                self.impact_window_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fef3c7; color: #92400e; font-weight: 700;"
                )
            elif impact_window["level"] == "ok":
                self.impact_window_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #dcfce7; color: #166534; font-weight: 700;"
                )
            else:
                self.impact_window_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #f3f4f6; color: #374151;"
                )
            impact_details = str(impact_window.get("details") or "").strip()
            impact_text = f"{impact_window['title']}: {impact_window['message']}"
            if impact_details:
                impact_text += f"\n{impact_details}"
            self.impact_window_label.setText(impact_text)

        if hasattr(self, "game_suitability_label"):
            terminal_summary = (
                service_analysis.get("terminal_summary")
                if isinstance(service_analysis.get("terminal_summary"), dict)
                else {}
            )
            game_suitability = (
                service_analysis.get("game_suitability_summary")
                if isinstance(service_analysis.get("game_suitability_summary"), dict)
                else summarize_game_suitability_advisor(
                    usage_profile=self._current_usage_profile(),
                    terminal_summary=terminal_summary,
                )
            )
            self.game_suitability_label.setStyleSheet(
                _advisory_style(str(game_suitability.get("level") or "unknown"))
            )
            gs_title = str(game_suitability.get("title") or "Game Suitability").strip()
            gs_message = str(game_suitability.get("message") or "").strip()
            gs_conf_label = str(game_suitability.get("confidence_label") or "").strip()
            gs_conf_message = str(
                game_suitability.get("confidence_message") or ""
            ).strip()
            gs_checks = [
                str(item).strip()
                for item in (game_suitability.get("checks") or [])
                if str(item).strip()
            ]
            gs_meta: list[str] = []
            game_label = str(game_suitability.get("game_label") or "").strip()
            if game_label:
                gs_meta.append(_status_pill(game_label, game_suitability.get("level")))
            if gs_conf_label:
                gs_meta.append(_status_pill(gs_conf_label, "info"))
            gs_html = f"<b>{gs_title}</b>: {gs_message}"
            if gs_meta:
                gs_html += "<br>" + "".join(gs_meta)
            if gs_conf_message:
                gs_html += (
                    "<br><span style='font-weight:400'>" + gs_conf_message + "</span>"
                )
            if gs_checks:
                gs_html += (
                    "<br><span style='font-weight:400'>"
                    + " | ".join(gs_checks[:2])
                    + "</span>"
                )
            self.game_suitability_label.setText(gs_html)

        if hasattr(self, "calibration_profile_label"):
            bullet_id = (
                self.bullet_data.get("id")
                if isinstance(self.bullet_data, dict)
                else None
            )
            primer_id = (
                self.primer_data.get("id")
                if isinstance(self.primer_data, dict)
                else None
            )
            powder_id = (
                powder_context.get("id") if isinstance(powder_context, dict) else None
            )
            barrel_details = self._get_active_barrel_details()
            active_barrel_context = (
                self._get_active_barrel_configuration_context() or {}
            )
            calibration_profile = summarize_builder_calibration_profile(
                self.db,
                self.rifle_data if isinstance(self.rifle_data, dict) else None,
                self._get_active_barrel_id(),
                str(barrel_details.get("name") or "").strip(),
                powder_id,
                bullet_id,
                primer_id,
                getattr(self, "current_ammo_profile_id", None),
                barrel_configuration_id=active_barrel_context.get(
                    "barrel_configuration_id"
                ),
                barrel_configuration_name=active_barrel_context.get(
                    "barrel_configuration_name"
                ),
            )
            if calibration_profile["level"] == "critical":
                self.calibration_profile_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fee2e2; color: #991b1b; font-weight: 700;"
                )
            elif calibration_profile["level"] == "warning":
                self.calibration_profile_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fef3c7; color: #92400e; font-weight: 700;"
                )
            elif calibration_profile["level"] == "ok":
                self.calibration_profile_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #dcfce7; color: #166534; font-weight: 700;"
                )
            else:
                self.calibration_profile_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #f3f4f6; color: #374151;"
                )
            self.calibration_profile_label.setText(
                f"{calibration_profile['title']}: {calibration_profile['message']}"
            )

        if hasattr(self, "internal_ballistics_label"):
            internal_ballistics = (
                runtime_analysis_context.get("internal_ballistics")
                if isinstance(runtime_analysis_context.get("internal_ballistics"), dict)
                and runtime_analysis_context.get("internal_ballistics")
                else self._build_current_internal_ballistics_summary(
                    latest_result=result,
                    powder_name=str((powder_context or {}).get("name") or ""),
                )
            )
            if internal_ballistics["level"] == "critical":
                self.internal_ballistics_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fee2e2; color: #991b1b; font-weight: 700;"
                )
            elif internal_ballistics["level"] == "warning":
                self.internal_ballistics_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #fef3c7; color: #92400e; font-weight: 700;"
                )
            elif internal_ballistics["level"] == "ok":
                self.internal_ballistics_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #dcfce7; color: #166534; font-weight: 700;"
                )
            else:
                self.internal_ballistics_label.setStyleSheet(
                    "padding: 8px; border-radius: 6px; background: #f3f4f6; color: #374151;"
                )
            self.internal_ballistics_label.setText(
                f"{internal_ballistics['title']}: {internal_ballistics['message']}"
            )

        if hasattr(self, "evidence_basis_label"):
            evidence_internal_ballistics = (
                runtime_analysis_context.get("internal_ballistics")
                if isinstance(runtime_analysis_context.get("internal_ballistics"), dict)
                and runtime_analysis_context.get("internal_ballistics")
                else self._build_current_internal_ballistics_summary(
                    latest_result=result,
                    powder_name=str((powder_context or {}).get("name") or ""),
                )
            )
            evidence_basis = summarize_builder_evidence_basis(
                result,
                workflow_data=workflow_data,
                observations=(
                    service_analysis.get("observations")
                    if isinstance(service_analysis.get("observations"), dict)
                    else {
                        "chronograph_sessions": (
                            [{"avg_velocity_fps": result.get("muzzle_velocity_fps")}]
                            if isinstance(
                                result.get("muzzle_velocity_fps"), (int, float)
                            )
                            else []
                        ),
                    }
                ),
                bullet_data=(
                    self.bullet_data if isinstance(self.bullet_data, dict) else None
                ),
                environment=(
                    result.get("_environment") if isinstance(result, dict) else None
                ),
                internal_ballistics_summary=evidence_internal_ballistics,
            )
            confidence_model = summarize_builder_confidence_model(
                result,
                workflow_data=workflow_data,
                observations=(
                    service_analysis.get("observations")
                    if isinstance(service_analysis.get("observations"), dict)
                    else {
                        "chronograph_sessions": (
                            [{"avg_velocity_fps": result.get("muzzle_velocity_fps")}]
                            if isinstance(
                                result.get("muzzle_velocity_fps"), (int, float)
                            )
                            else []
                        ),
                    }
                ),
                bullet_data=(
                    self.bullet_data if isinstance(self.bullet_data, dict) else None
                ),
                powder_data=(
                    powder_context if isinstance(powder_context, dict) else None
                ),
                environment=(
                    result.get("_environment") if isinstance(result, dict) else None
                ),
                tracked_brass=self._has_tracked_brass_batch(),
                seating_evidence=self._get_best_known_seating_evidence(),
                subsonic_history=subsonic_history,
                model_match=model_match,
            )
            detail_html = "".join(
                f"<li>{item}</li>"
                for item in (confidence_model.get("checks") or [])[:4]
            )
            self.evidence_basis_label.setText(
                f"{evidence_basis['title']}: {evidence_basis['message']}"
                + (
                    f"<br><ul style='margin:6px 0 0 18px;'>{detail_html}</ul>"
                    if detail_html
                    else ""
                )
            )
            self.evidence_basis_label.setTextFormat(Qt.TextFormat.RichText)

            recommendation = (
                service_analysis.get("recommendation")
                if isinstance(service_analysis.get("recommendation"), dict)
                else {}
            )
            observations = (
                service_analysis.get("observations")
                if isinstance(service_analysis.get("observations"), dict)
                else {}
            )
            observation_summary = (
                observations.get("summary")
                if isinstance(observations.get("summary"), dict)
                else {}
            )
            terminal_summary = (
                service_analysis.get("terminal_summary")
                if isinstance(service_analysis.get("terminal_summary"), dict)
                else {}
            )
            input_quality = (
                service_analysis.get("input_quality")
                if isinstance(service_analysis.get("input_quality"), dict)
                else {}
            )
            runtime = self._get_cached_or_active_load_session_runtime()
            runtime_analysis_context = build_runtime_analysis_context(runtime, analysis)
            evidence_summary = build_profile_evidence_summary(
                self.db,
                (
                    int(self.current_ammo_profile_id)
                    if getattr(self, "current_ammo_profile_id", None) not in (None, "")
                    else None
                ),
                analysis_context=runtime_analysis_context,
            )
            load_card_summary = build_load_card_summary(
                self.db,
                (
                    int(self.current_ammo_profile_id)
                    if getattr(self, "current_ammo_profile_id", None) not in (None, "")
                    else None
                ),
            )
            learning_guidance = build_learning_workflow_guidance(runtime)
            primer_review_runtime = (
                runtime_analysis_context.get("primer_review")
                if isinstance(runtime_analysis_context.get("primer_review"), dict)
                else {}
            )
            next_step_text = str(recommendation.get("next_step") or "").strip()
            recommendation_runtime = (
                runtime.get("recommendation")
                if isinstance(runtime.get("recommendation"), dict)
                else {}
            )
            recommendation_targets = summarize_recommendation_return_targets(
                (
                    recommendation_runtime.get("control_state")
                    if isinstance(recommendation_runtime.get("control_state"), dict)
                    else {}
                ),
                (
                    recommendation_runtime.get("baseline")
                    if isinstance(recommendation_runtime.get("baseline"), dict)
                    else {}
                ),
            )
            history_bits = []
            chrono_count = int(
                evidence_summary.get("chrono_count")
                or observation_summary.get("chrono_count")
                or 0
            )
            accuracy_count = int(
                evidence_summary.get("accuracy_count")
                or observation_summary.get("accuracy_count")
                or 0
            )
            pressure_count = int(
                evidence_summary.get("pressure_count")
                or observation_summary.get("pressure_event_count")
                or 0
            )
            best_group_mm = (
                evidence_summary.get("best_group_mm")
                if evidence_summary.get("best_group_mm") not in (None, "")
                else observation_summary.get("best_group_mm")
            )
            if chrono_count:
                history_bits.append(f"{chrono_count} chrono")
            if accuracy_count:
                history_bits.append(f"{accuracy_count} accuracy tests")
            if isinstance(best_group_mm, (int, float)):
                history_bits.append(
                    f"best group {format_group_size_mm(float(best_group_mm))}"
                )
            if pressure_count:
                history_bits.append(f"{pressure_count} pressure events")
            primer_review_summary = str(
                primer_review_runtime.get("summary") or ""
            ).strip()
            primer_review_title = str(primer_review_runtime.get("title") or "").strip()
            projectile_fit = str(
                evidence_summary.get("projectile_title")
                or evidence_summary.get("projectile_label")
                or terminal_summary.get("title")
                or ""
            ).strip()
            self.confidence_label.setText(
                f"{confidence_model['title']} ({float(confidence_model['score']):.2f}): {confidence_model['message']}"
                + (
                    f" Data quality: {input_quality.get('title')}."
                    if input_quality.get("title")
                    else ""
                )
                + (
                    f" Barrel history: {', '.join(history_bits)}."
                    if history_bits
                    else ""
                )
                + (
                    f" Primer review: {primer_review_title.lower()} ({primer_review_summary})."
                    if primer_review_title and primer_review_summary
                    else ""
                )
                + (f" Projectile fit: {projectile_fit}." if projectile_fit else "")
                + (
                    f" Learning priority: {learning_guidance.get('setup')}"
                    if learning_guidance.get("setup")
                    else ""
                )
                + (
                    " Recommendation target: "
                    + " | ".join(recommendation_targets)
                    + "."
                    if recommendation_targets
                    else ""
                )
                + (f" Next step: {next_step_text}" if next_step_text else "")
            )
            self.confidence_label.setWordWrap(True)
            self.confidence_label.setStyleSheet(
                _advisory_style(confidence_model["level"])
            )
            if hasattr(self, "analysis_health_label"):
                pressure_assessment = (
                    runtime_analysis_context.get("pressure_assessment")
                    if isinstance(
                        runtime_analysis_context.get("pressure_assessment"), dict
                    )
                    else {}
                )
                internal_ballistics = (
                    runtime_analysis_context.get("internal_ballistics")
                    if isinstance(
                        runtime_analysis_context.get("internal_ballistics"), dict
                    )
                    else {}
                )
                stability_assessment = (
                    runtime_analysis_context.get("stability_assessment")
                    if isinstance(
                        runtime_analysis_context.get("stability_assessment"), dict
                    )
                    else {}
                )
                primer_review = (
                    runtime_analysis_context.get("primer_review")
                    if isinstance(runtime_analysis_context.get("primer_review"), dict)
                    else {}
                )
                lot_level = str(evidence_summary.get("lot_level") or "unknown")
                health_bits = [
                    _status_pill("Pressure", pressure_assessment.get("level")),
                    _status_pill("Burn", internal_ballistics.get("level")),
                    _status_pill("Stability", stability_assessment.get("level")),
                    _status_pill("Primer", primer_review.get("level")),
                    _status_pill(
                        "Projectile", evidence_summary.get("projectile_level")
                    ),
                    _status_pill("Brass", evidence_summary.get("brass_level")),
                    _status_pill("History", evidence_summary.get("history_level")),
                    _status_pill("Lots", lot_level),
                ]
                health_summary = []
                pressure_title = str(pressure_assessment.get("title") or "").strip()
                if pressure_title:
                    health_summary.append(pressure_title)
                internal_title = str(internal_ballistics.get("title") or "").strip()
                if internal_title and internal_title != pressure_title:
                    health_summary.append(internal_title)
                brass_title = str(evidence_summary.get("brass_title") or "").strip()
                if brass_title and brass_title not in {pressure_title, internal_title}:
                    health_summary.append(brass_title)
                projectile_title = str(
                    evidence_summary.get("projectile_title") or ""
                ).strip()
                if projectile_title and projectile_title not in {
                    pressure_title,
                    internal_title,
                    brass_title,
                }:
                    health_summary.append(projectile_title)
                primer_title = str(primer_review.get("title") or "").strip()
                if primer_title and primer_title not in {
                    pressure_title,
                    internal_title,
                    brass_title,
                    projectile_title,
                }:
                    health_summary.append(primer_title)
                self.analysis_health_label.setText(
                    "<b>Model Health</b><br>"
                    + "".join(health_bits)
                    + (
                        "<br><span style='color:#6b7280'>"
                        + " | ".join(health_summary[:3])
                        + "</span>"
                        if health_summary
                        else ""
                    )
                )
            if hasattr(self, "analysis_trust_label"):
                trust = build_profile_trust_map(evidence_summary)
                trust_pills = [
                    _status_pill("Measured", trust.get("measured_level")),
                    _status_pill("Simulated", trust.get("simulated_level")),
                    _status_pill("Derived", trust.get("derived_level")),
                    _status_pill("Assumed", trust.get("assumed_level")),
                ]
                self.analysis_trust_label.setText(
                    "<b>Evidence Map</b><br>"
                    + "".join(trust_pills)
                    + (
                        "<br><span style='color:#6b7280'>"
                        + str(trust.get("summary") or "")
                        + "</span>"
                        if str(trust.get("summary") or "").strip()
                        else ""
                    )
                )

        try:
            self.evidence_label.setText(self._build_evidence_summary())
        except Exception:
            pass
        try:
            self._refresh_evidence_actions()
        except Exception:
            pass
        try:
            self._refresh_calibration_table()
        except Exception:
            pass
        try:
            runtime = self._get_cached_or_active_load_session_runtime()
            runtime_analysis_context = build_runtime_analysis_context(runtime, analysis)
            recommendation = (
                service_analysis.get("recommendation")
                if isinstance(service_analysis.get("recommendation"), dict)
                else {}
            )
            observations = (
                service_analysis.get("observations")
                if isinstance(service_analysis.get("observations"), dict)
                else {}
            )
            observation_summary = (
                observations.get("summary")
                if isinstance(observations.get("summary"), dict)
                else {}
            )
            evidence_summary = build_profile_evidence_summary(
                self.db,
                (
                    int(self.current_ammo_profile_id)
                    if getattr(self, "current_ammo_profile_id", None) not in (None, "")
                    else None
                ),
                analysis_context=runtime_analysis_context,
            )
            recommendation_runtime = (
                runtime.get("recommendation")
                if isinstance(runtime.get("recommendation"), dict)
                else {}
            )
            recommendation_targets = summarize_recommendation_return_targets(
                (
                    recommendation_runtime.get("control_state")
                    if isinstance(recommendation_runtime.get("control_state"), dict)
                    else {}
                ),
                (
                    recommendation_runtime.get("baseline")
                    if isinstance(recommendation_runtime.get("baseline"), dict)
                    else {}
                ),
            )
            charge_window = recommendation.get("charge_window_gr") or []
            seating_window = recommendation.get("seating_window_mm") or []
            next_lines = []
            next_step = str(recommendation.get("next_step") or "").strip()
            if next_step:
                next_lines.append(next_step)
            if learning_guidance.get("header"):
                next_lines.append(learning_guidance["header"])
            if learning_guidance.get("setup"):
                next_lines.append(learning_guidance["setup"])
            next_lines.extend(recommendation_targets)
            if len(charge_window) == 2:
                next_lines.append(
                    "Recommended charge window: "
                    f"{format_weight_grains(float(charge_window[0]), 'powder')}"
                    " til "
                    f"{format_weight_grains(float(charge_window[1]), 'powder')}"
                )
            if len(seating_window) == 2:
                next_lines.append(
                    "Recommended seating adjustment: "
                    f"{format_length_delta_mm(float(seating_window[0]))}"
                    " til "
                    f"{format_length_delta_mm(float(seating_window[1]))}"
                )
            chrono_count = int(
                evidence_summary.get("chrono_count")
                or observation_summary.get("chrono_count")
                or 0
            )
            accuracy_count = int(
                evidence_summary.get("accuracy_count")
                or observation_summary.get("accuracy_count")
                or 0
            )
            best_group_mm = (
                evidence_summary.get("best_group_mm")
                if evidence_summary.get("best_group_mm") not in (None, "")
                else observation_summary.get("best_group_mm")
            )
            history_parts = []
            if chrono_count:
                history_parts.append(f"{chrono_count} chrono")
            if accuracy_count:
                history_parts.append(f"{accuracy_count} accuracy")
            if isinstance(best_group_mm, (int, float)):
                history_parts.append(
                    f"best group {format_group_size_mm(float(best_group_mm))}"
                )
            if history_parts:
                next_lines.append("Barrel history: " + ", ".join(history_parts))
            lot_actions = [
                str(item).strip()
                for item in (evidence_summary.get("lot_actions") or [])
                if str(item).strip()
            ]
            if lot_actions:
                next_lines.append(lot_actions[0])
            brass_context = resolve_runtime_learning_context(
                runtime, analysis, "brass_context"
            )
            brass_level = str(brass_context.get("level") or "").strip().lower()
            brass_title = str(brass_context.get("title") or "").strip()
            brass_checks = [
                str(item).strip()
                for item in (brass_context.get("checks") or [])
                if str(item).strip()
            ]
            brass_actions = []
            if brass_level in {"info", "warning"} or "svak" in brass_title.lower():
                brass_actions.append(
                    "Brass baseline: measure 3-5 H2O samples and enter neck, trim, bump, and base-to-datum."
                )
            for item in brass_checks:
                lowered = item.lower()
                if (
                    "start gjerne med 3-5 h2o-målinger" in lowered
                    or "start with 3-5 h2o measurements" in lowered
                ):
                    brass_actions.append(
                        "Brass baseline: start with 3-5 H2O measurements from the same barrel."
                    )
                    break
            if brass_actions:
                next_lines.extend(brass_actions[:1])
            impact_window = (
                service_analysis.get("terminal_summary")
                if isinstance(service_analysis.get("terminal_summary"), dict)
                and service_analysis.get("terminal_summary")
                else summarize_builder_impact_window(
                    self.db,
                    workflow_data,
                    observations,
                )
            )
            impact_checks = [
                str(item).strip()
                for item in (impact_window.get("checks") or [])
                if str(item).strip()
            ]
            verification_line = ""
            for item in impact_checks:
                if item.startswith("Recommended verification:"):
                    verification_line = item.removeprefix(
                        "Recommended verification:"
                    ).strip()
                    break
            if not verification_line:
                verification_line = str(
                    impact_window.get("verification_action") or ""
                ).strip()
            if verification_line:
                next_lines.append("Projectile verification: " + verification_line)
            if hasattr(self, "load_card_summary_label"):
                details = load_card_summary.get("detail_lines") or []
                self.load_card_summary_label.setText(
                    f"<b>{load_card_summary.get('title') or 'Load Card'}</b>"
                    + (
                        f"<br><span style='color:#6b7280'>{load_card_summary.get('subtitle')}</span>"
                        if load_card_summary.get("subtitle")
                        else ""
                    )
                    + (
                        f"<br>{load_card_summary.get('component_line')}"
                        if load_card_summary.get("component_line")
                        else ""
                        + (
                            f"<br><span style='color:#6b7280'>{learning_guidance.get('card_hint')}</span>"
                            if learning_guidance.get("card_hint")
                            else ""
                        )
                    )
                    + (
                        f"<br><span style='color:#6b7280'>{' | '.join(str(item) for item in details[:3] if str(item).strip())}</span>"
                        if details
                        else ""
                    )
                    + (
                        f"<br><span style='color:#6b7280'>{learning_guidance.get('card_hint')}</span>"
                        if learning_guidance.get("card_hint")
                        else ""
                    )
                )
            if hasattr(self, "safety_next_label"):
                self.safety_next_label.setText(
                    "\n".join(next_lines)
                    if next_lines
                    else tr("mlb_next_step_placeholder")
                )
            if hasattr(self, "pipe_history_label"):
                pressure_count = int(
                    evidence_summary.get("pressure_count")
                    or observation_summary.get("pressure_event_count")
                    or 0
                )
                avg_group_mm = (
                    evidence_summary.get("avg_group_mm")
                    if evidence_summary.get("avg_group_mm") not in (None, "")
                    else observation_summary.get("avg_group_mm")
                )
                history_level = str(evidence_summary.get("history_level") or "unknown")
                history_title = str(
                    evidence_summary.get("history_title") or "History missing"
                )
                active_barrel_context = (
                    self._get_active_barrel_configuration_context() or {}
                )
                setup_label = _format_barrel_configuration_label(
                    str(
                        active_barrel_context.get("barrel_configuration_name") or ""
                    ).strip(),
                    str(active_barrel_context.get("barrel_name") or "").strip(),
                )
                history_lines = []
                if setup_label:
                    history_lines.append(f"Setup: {setup_label}")
                history_lines.append(
                    f"Chrono sessions: {chrono_count}"
                    if chrono_count
                    else "Chrono sessions: none"
                )
                history_lines.append(
                    f"Accuracy tests: {accuracy_count}"
                    if accuracy_count
                    else "Accuracy tests: none"
                )
                if isinstance(best_group_mm, (int, float)):
                    history_lines.append(
                        f"Best group: {format_group_size_mm(float(best_group_mm))}"
                    )
                if isinstance(avg_group_mm, (int, float)):
                    history_lines.append(
                        f"Average group: {format_group_size_mm(float(avg_group_mm))}"
                    )
                history_lines.append(
                    f"Pressure signs: {pressure_count}"
                    if pressure_count
                    else "Pressure signs: none recorded"
                )
                self.pipe_history_label.setStyleSheet(
                    _pipe_history_style(history_level)
                )
                self.pipe_history_label.setText(
                    f"{history_title}\n" + "\n".join(history_lines)
                )
            if hasattr(self, "barrel_context_label"):
                barrel_context = resolve_runtime_learning_context(
                    runtime, analysis, "barrel_context"
                )
                barrel_checks = [
                    str(item).strip()
                    for item in (barrel_context.get("checks") or [])
                    if str(item).strip()
                ]
                barrel_title = str(barrel_context.get("title") or "Barrel Context")
                barrel_message = str(barrel_context.get("message") or "").strip()
                active_barrel_context = (
                    self._get_active_barrel_configuration_context() or {}
                )
                setup_label = _format_barrel_configuration_label(
                    str(
                        active_barrel_context.get("barrel_configuration_name") or ""
                    ).strip(),
                    str(active_barrel_context.get("barrel_name") or "").strip(),
                )
                barrel_lines = []
                if setup_label:
                    barrel_lines.append(f"Setup {setup_label}.")
                if barrel_message:
                    barrel_lines.append(barrel_message)
                if barrel_checks:
                    barrel_lines.append(" | ".join(barrel_checks[:3]))
                self.barrel_context_label.setText(
                    f"{barrel_title}: "
                    + (" ".join(barrel_lines) if barrel_lines else "--")
                )
            if hasattr(self, "brass_context_label"):
                brass_checks = [
                    str(item).strip()
                    for item in (brass_context.get("checks") or [])
                    if str(item).strip()
                ]
                brass_title = str(brass_context.get("title") or "Brass Baseline")
                brass_message = str(brass_context.get("message") or "").strip()
                brass_lines = []
                if brass_message:
                    brass_lines.append(brass_message)
                if brass_checks:
                    brass_lines.append(" | ".join(brass_checks[:3]))
                self.brass_context_label.setText(
                    f"{brass_title}: "
                    + (" ".join(brass_lines) if brass_lines else "--")
                )
            if hasattr(self, "powder_internal_label"):
                internal_ballistics = (
                    analysis.get("internal_ballistics")
                    if isinstance(analysis.get("internal_ballistics"), dict)
                    else {}
                )
                powder_title = str(internal_ballistics.get("title") or "Powder & Burn")
                powder_message = str(internal_ballistics.get("message") or "").strip()
                powder_metrics = []
                for metric in (internal_ballistics.get("metrics") or [])[:4]:
                    if not isinstance(metric, dict):
                        continue
                    metric_name = str(metric.get("name") or "").strip()
                    metric_value = str(metric.get("value") or "").strip()
                    if metric_name and metric_value:
                        powder_metrics.append(f"{metric_name}: {metric_value}")
                powder_checks = [
                    str(item).strip()
                    for item in (internal_ballistics.get("checks") or [])[:2]
                    if str(item).strip()
                ]
                powder_lines = []
                if powder_message:
                    powder_lines.append(powder_message)
                if powder_metrics:
                    powder_lines.append(" | ".join(powder_metrics))
                if powder_checks:
                    powder_lines.append(" | ".join(powder_checks))
                self.powder_internal_label.setText(
                    f"{powder_title}: "
                    + (" ".join(powder_lines) if powder_lines else "--")
                )
            if hasattr(self, "projectile_context_label"):
                terminal_summary = (
                    analysis.get("terminal_summary")
                    if isinstance(analysis.get("terminal_summary"), dict)
                    else {}
                )
                projectile_profile = (
                    terminal_summary.get("projectile_profile")
                    if isinstance(terminal_summary.get("projectile_profile"), dict)
                    else {}
                )
                projectile_title = "Projectile Profile"
                projectile_lines = []
                projectile_notes = [
                    str(item).strip()
                    for item in (projectile_profile.get("notes") or [])[:2]
                    if str(item).strip()
                ]
                profile_summary = str(
                    projectile_profile.get("profile_summary") or ""
                ).strip()
                intended_use = str(projectile_profile.get("intended_use") or "").strip()
                minimum_expansion = projectile_profile.get("minimum_expansion_fps")
                preferred_min = projectile_profile.get("preferred_impact_min_fps")
                preferred_max = projectile_profile.get("preferred_impact_max_fps")
                if profile_summary:
                    projectile_lines.append(f"Type: {profile_summary}")
                if intended_use:
                    projectile_lines.append(f"Use: {intended_use.replace('_', ' ')}")
                if preferred_min not in (None, "") and preferred_max not in (None, ""):
                    projectile_lines.append(
                        "Window: "
                        + f"{format_velocity_fps(float(preferred_min))}-{format_velocity_fps(float(preferred_max))}"
                    )
                elif preferred_min not in (None, ""):
                    projectile_lines.append(
                        f"Floor: {format_velocity_fps(float(preferred_min))}"
                    )
                elif minimum_expansion not in (None, ""):
                    projectile_lines.append(
                        f"Minimum: {format_velocity_fps(float(minimum_expansion))}"
                    )
                confidence = str(projectile_profile.get("confidence") or "").strip()
                if confidence:
                    projectile_lines.append(f"Confidence: {confidence}")
                projectile_text = " | ".join(projectile_lines)
                if projectile_notes:
                    projectile_text = (
                        projectile_text + " " if projectile_text else ""
                    ) + " ".join(projectile_notes)
                self.projectile_context_label.setText(
                    f"{projectile_title}: " + (projectile_text or "--")
                )
            if hasattr(self, "primer_context_label"):
                primer_profile = (
                    analysis.get("primer_profile")
                    if isinstance(analysis.get("primer_profile"), dict)
                    else {}
                )
                primer_lot_context = (
                    analysis.get("primer_lot_context")
                    if isinstance(analysis.get("primer_lot_context"), dict)
                    else {}
                )
                primer_title = "Primer Profile"
                primer_lines = []
                family = str(
                    primer_profile.get("family")
                    or primer_profile.get("primer_family")
                    or ""
                ).strip()
                ignition = str(
                    primer_profile.get("ignition_strength_class") or ""
                ).strip()
                pressure_class = str(
                    primer_profile.get("pressure_tolerance_class") or ""
                ).strip()
                cold_weather = str(
                    primer_profile.get("cold_weather_suitability") or ""
                ).strip()
                if family:
                    primer_lines.append(f"Family: {family.replace('_', ' ')}")
                if ignition:
                    primer_lines.append(f"Ignition: {ignition.replace('_', ' ')}")
                if pressure_class:
                    primer_lines.append(
                        f"Pressure class: {pressure_class.replace('_', ' ')}"
                    )
                if cold_weather:
                    primer_lines.append(f"Cold weather: {cold_weather}")
                pressure_min = primer_profile.get("recommended_pressure_min_psi")
                pressure_max = primer_profile.get("recommended_pressure_max_psi")
                if pressure_min not in (None, "") and pressure_max not in (None, ""):
                    primer_lines.append(
                        f"Window: {format_pressure_range_psi(float(pressure_min), float(pressure_max))}"
                    )
                primer_notes = [
                    str(item).strip()
                    for item in (primer_profile.get("notes") or [])[:2]
                    if str(item).strip()
                ]
                if primer_lot_context.get("lot_number"):
                    primer_lines.append(f"Lot: {primer_lot_context.get('lot_number')}")
                if primer_lot_context.get("title"):
                    primer_notes.append(str(primer_lot_context.get("title")))
                primer_text = " | ".join(primer_lines)
                if primer_notes:
                    primer_text = (primer_text + " " if primer_text else "") + " ".join(
                        primer_notes[:2]
                    )
                self.primer_context_label.setText(
                    f"{primer_title}: " + (primer_text or "--")
                )
            lot_parts = []
            bullet_lot_context = (
                analysis.get("bullet_lot_context")
                if isinstance(analysis.get("bullet_lot_context"), dict)
                else {}
            )
            powder_lot_context = (
                analysis.get("powder_lot_context")
                if isinstance(analysis.get("powder_lot_context"), dict)
                else {}
            )
            primer_lot_context = (
                analysis.get("primer_lot_context")
                if isinstance(analysis.get("primer_lot_context"), dict)
                else {}
            )
            if bullet_lot_context.get("lot_number"):
                lot_parts.append(f"Bullet lot {bullet_lot_context['lot_number']}")
            if powder_lot_context.get("lot_number"):
                lot_parts.append(f"Powder lot {powder_lot_context['lot_number']}")
            if primer_lot_context.get("lot_number"):
                lot_parts.append(f"Primer lot {primer_lot_context['lot_number']}")
            if lot_parts and hasattr(self, "load_card_summary_label"):
                self.load_card_summary_label.setText(
                    str(self.load_card_summary_label.text() or "")
                    + "<br><span style='color:#6b7280'>"
                    + " | ".join(lot_parts)
                    + "</span>"
                )
            if hasattr(self, "pipe_history_trend_label"):
                self.pipe_history_trend_label.setText(
                    "Trend: "
                    + str(evidence_summary.get("trend_label") or "no trend data yet")
                )
            if hasattr(self, "learning_runtime_label"):
                self.learning_runtime_label.setText(
                    self._format_learning_runtime_label(runtime)
                )
        except Exception:
            pass

        try:
            self.harmonics_profile_btn.setEnabled(False)
            self.harmonics_profile_btn.setText("Update firearm profile for harmonics")
            self.safety_checks.clear()
            if hasattr(self, "analysis_health_label"):
                self.analysis_health_label.setText("Model Health: --")
            if hasattr(self, "analysis_trust_label"):
                self.analysis_trust_label.setText("Evidence Map: --")
            if hasattr(self, "load_card_summary_label"):
                self.load_card_summary_label.setText("Load Card: --")
            if hasattr(self, "pipe_history_label"):
                self.pipe_history_label.setText("Barrel History: --")
                self.pipe_history_label.setStyleSheet(_pipe_history_style("unknown"))
            if hasattr(self, "barrel_context_label"):
                self.barrel_context_label.setText("Barrel Context: --")
            if hasattr(self, "brass_context_label"):
                self.brass_context_label.setText("Brass Baseline: --")
            if hasattr(self, "powder_internal_label"):
                self.powder_internal_label.setText("Powder & Burn: --")
            if hasattr(self, "projectile_context_label"):
                self.projectile_context_label.setText("Projectile Profile: --")
            if hasattr(self, "primer_context_label"):
                self.primer_context_label.setText("Primer Profile: --")
            if hasattr(self, "pipe_history_trend_label"):
                self.pipe_history_trend_label.setText("Trend: --")
            if hasattr(self, "learning_runtime_label"):
                self.learning_runtime_label.setText("Learning State: --")
        except Exception:
            return

        checks = []
        if display_margin is None:
            checks.append("WARN: missing data for pressure margin")
        elif display_margin >= 15:
            checks.append("OK: pressure margin healthy")
        elif display_margin >= 10:
            checks.append("WARN: pressure margin narrow")
        else:
            checks.append("FAIL: pressure margin below target")

        if self.coal_mm and self.cbto_mm:
            checks.append("OK: COAL/CBTO set")
        else:
            checks.append("WARN: COAL/CBTO not set")

        if self.bullet_data and self.powder_data:
            checks.append("OK: components selected")
        else:
            checks.append("WARN: missing component selection")

        if self._has_tracked_brass_batch():
            checks.append("OK: brass is linked to a registered batch")
        elif self.brass_data:
            checks.append(
                "WARN: brass is not linked to a registered batch - small precision and velocity differences may include brass variation"
            )
        else:
            checks.append("WARN: brass batch not selected")

        if profile_limit is None:
            checks.append("WARN: no weapon pressure limit override")

        if details.get("scope_height_mm") is None:
            checks.append("WARN: scope height not set")

        if details.get("zero_distance_m") is None:
            checks.append("WARN: zero distance not set")

        harmonics = self._get_rifle_harmonics_profile()
        service_harmonics = (
            service_analysis.get("harmonics")
            if isinstance(service_analysis.get("harmonics"), dict)
            else {}
        )
        missing_harmonics = harmonics.get("missing_required_inputs", [])
        if missing_harmonics:
            checks.append(
                "WARN: harmonics data incomplete - missing "
                + ", ".join(missing_harmonics[:3])
            )
            try:
                self.harmonics_profile_btn.setEnabled(True)
                self.harmonics_profile_btn.setText(
                    "Update firearm profile: "
                    + self._format_harmonics_missing_fields(missing_harmonics[:2])
                )
            except Exception:
                pass
        else:
            checks.append(
                f"OK: harmonics data quality {harmonics.get('harmonics_confidence', 'low')}"
            )
            try:
                harmonic_score = service_harmonics.get(
                    "harmonic_score", harmonics.get("harmonic_score")
                )
                stability_tier = service_harmonics.get(
                    "stability_tier", harmonics.get("stability_tier")
                )
                if harmonic_score is not None:
                    suffix = f" ({float(harmonic_score):.1f}/20"
                    if stability_tier:
                        suffix += f", {stability_tier}"
                    suffix += ")"
                    self.harmonics_profile_btn.setEnabled(True)
                    self.harmonics_profile_btn.setText(
                        "Update firearm profile for harmonics" + suffix
                    )
            except Exception:
                pass

        h2o_stats = self._get_h2o_stats()
        if h2o_stats:
            if h2o_stats["spread"] > 0.75:
                checks.append(
                    "WARN: H2O / case capacity has high spread - avoid over-interpreting small pressure or velocity changes"
                )
            elif h2o_stats["spread"] > 0.30:
                checks.append(
                    "WARN: H2O / case capacity spread is moderate - small differences may include brass variation"
                )
            else:
                checks.append(
                    f"OK: H2O / case capacity looks consistent across {h2o_stats['count']} measurements"
                )

        try:
            _, fit_checks = self._build_component_fit_assessment(result)
            checks.extend(fit_checks)
        except Exception:
            pass

        if mag_limit is not None and self.coal_mm:
            try:
                if float(self.coal_mm or 0) > float(mag_limit):
                    checks.append("FAIL: COAL exceeds magazine limit")
            except Exception:
                pass

        for item in checks:
            self.safety_checks.addItem(item)

        if display_margin is None:
            self.safety_next_label.setText(
                "Select bullet and powder to evaluate safety."
            )
        elif display_margin < 10:
            self.safety_next_label.setText(
                "Reduce charge or increase seating depth before testing."
            )
        elif display_margin < 15:
            self.safety_next_label.setText(
                "Proceed carefully and confirm with chronograph data."
            )
        else:
            if self._current_weapon_type() == "pistol":
                self.safety_next_label.setText(
                    "Safety margin looks good. Ready for a controlled test series."
                )
            else:
                self.safety_next_label.setText(
                    "Safety margin looks good. Ready for ladder testing."
                )

        if self.brass_data and not self._has_tracked_brass_batch():
            self.safety_next_label.setText(
                "Feel free to use chrono and group data, but be careful not to over-interpret small differences when brass is not tied to a recorded batch."
            )

    def update_scope_comparison(self, current_result):
        """Update scope adjustment comparison with previous load for same weapon"""
        if not self.rifle_data or not self.bullet_data or not self.powder_data:
            self.scope_comparison_group.setVisible(False)
            return

        rifle_id = self.rifle_data["id"]
        current_velocity = current_result.get("muzzle_velocity_fps", 0)

        # Find PREVIOUS load for same weapon (most recent ammo_profile)
        current_profile_id = getattr(self, "current_ammo_profile_id", None)
        previous_query = """
            SELECT name, velocity_fps, bc_g1, bc_g7, bc_segments_json, bullet_weight, caliber, created_date
            FROM ammo_profiles
            WHERE rifle_id = ? AND velocity_fps IS NOT NULL AND (bc_g1 IS NOT NULL OR bc_g7 IS NOT NULL OR bc_segments_json IS NOT NULL)
        """
        previous_params = [rifle_id]
        if current_profile_id:
            previous_query += " AND id != ?"
            previous_params.append(current_profile_id)
        previous_query += """
            ORDER BY created_date DESC
            LIMIT 1
        """
        previous_load = self.db.execute_query(
            previous_query,
            tuple(previous_params),
        )

        if not previous_load:
            self.scope_comparison_label.setText(
                f"<b>NEW LOAD:</b> {self.rifle_data['name']}<br>"
                f"<i>This is the first load for this firearm. No comparison is available.</i>"
            )
            self.scope_comparison_group.setVisible(True)
            return

        (
            prev_name,
            prev_vel,
            prev_bc_g1,
            prev_bc_g7,
            prev_bc_segments_json,
            prev_weight,
            prev_cal,
            prev_created,
        ) = previous_load[0]
        drag_model, current_bc, prev_bc, current_segment, prev_segment = (
            self._resolve_scope_drag_model(
                self.bullet_data,
                prev_bc_g1,
                prev_bc_g7,
                prev_bc_segments_json,
                current_velocity,
                prev_vel,
            )
        )
        if not current_velocity or current_bc is None or prev_bc is None:
            self.scope_comparison_group.setVisible(False)
            return

        # Calculate drop at 100m, 300m, 600m (using utils ballistics calculator)

        from ..layers import ballistics_layer

        ballistics_calc = ballistics_layer.basic

        zero_dist = 100  # Standard zero
        test_distances = [100, 300, 600]

        # Create comparison table
        comparison_html = f"""
        <b>NEW LOAD:</b> {self.rifle_data['name']} - {self.bullet_data.get('name', 'Custom')} {format_weight_grains(self.bullet_data.get('weight_grains', 0), 'bullet')}<br>
        • Velocity: {format_velocity_fps(current_velocity)}, BC ({drag_model}): {current_bc:.3f}, Powder: {self.powder_data.get('name', 'Unknown')} ({format_weight_grains(self.current_charge, 'powder')}){f" | Segmented BC: {current_segment}" if current_segment else ""}<br><br>

        <b>PREVIOUS LOAD:</b> {prev_name}<br>
        • Velocity: {format_velocity_fps(prev_vel)}, BC ({drag_model}): {prev_bc:.3f}, Bullet Weight: {format_weight_grains(prev_weight, 'bullet')}{f" | Segmented BC: {prev_segment}" if prev_segment else ""}<br><br>

        <b>POINT OF IMPACT / ADJUSTMENT (Zero: {zero_dist}m | Drag: {drag_model}):</b><br>
        <table style='width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 9pt;'>
        <tr style='background-color: #f0f0f0; font-weight: bold;'>
            <td style='padding: 3px; border: 1px solid #ddd;'>Dist</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Drop New</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Drop Previous</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Δ</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Adjustment</td>
        </tr>
        """

        for dist in test_distances:
            # Drop for new load
            drop_new = ballistics_calc.calculate_drop(
                current_velocity, current_bc, dist, zero_dist, drag_model
            )
            drop_new_moa = ballistics_calc.cm_to_moa(drop_new, dist)

            # Drop for previous load
            drop_prev = ballistics_calc.calculate_drop(
                prev_vel, prev_bc, dist, zero_dist, drag_model
            )
            drop_prev_moa = ballistics_calc.cm_to_moa(drop_prev, dist)

            # Difference
            diff_cm = drop_new - drop_prev
            diff_moa = drop_new_moa - drop_prev_moa

            # Scope adjustment (0.25 MOA/click standard)
            clicks = diff_moa / 0.25
            direction = "↑" if clicks > 0 else "↓" if clicks < 0 else "="

            color = (
                "#27ae60"
                if abs(diff_cm) < 5
                else "#f39c12" if abs(diff_cm) < 15 else "#e74c3c"
            )

            comparison_html += f"""
            <tr>
                <td style='padding: 3px; border: 1px solid #ddd;'>{dist}m</td>
                <td style='padding: 3px; border: 1px solid #ddd;'>{drop_new:.0f}cm ({drop_new_moa:.1f} MOA)</td>
                <td style='padding: 3px; border: 1px solid #ddd;'>{drop_prev:.0f}cm ({drop_prev_moa:.1f} MOA)</td>
                <td style='padding: 3px; border: 1px solid #ddd; background-color: {color}; color: white; font-weight: bold;'>{diff_cm:+.0f}cm</td>
                <td style='padding: 3px; border: 1px solid #ddd; font-weight: bold;'>{direction} {abs(clicks):.0f} clicks</td>
            </tr>
            """

        comparison_html += """
        </table><br>
        <i style='font-size: 8pt;'>Green = &lt;5 cm, Yellow = 5-15 cm, Red = &gt;15 cm. Standard: 0.25 MOA/click.</i>
        """

        self.scope_comparison_label.setText(comparison_html)
        self.scope_comparison_group.setVisible(True)
