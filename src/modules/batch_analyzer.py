"""Analysis helpers for batch projects.

The goal is to keep the advice simple, repeatable, and tied to the actual
batch history the user can come back to later.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List, Optional

from ..tools.evidence_quality_service import score_to_level


@dataclass
class BatchAnalysis:
    score: float = 0.0
    confidence: float = 0.0
    summary: str = ""
    trend_summary: str = ""
    next_focus: str = ""
    improvement_potential: str = ""
    strengths: List[str] = field(default_factory=list)
    watchouts: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class BatchAnalyzer:
    """Turn batch sessions, chrono data, and notes into actionable feedback."""

    def __init__(
        self,
        batch: Dict[str, Any],
        *,
        sessions: Optional[List[Dict[str, Any]]] = None,
        notes: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        chronograph_stats: Optional[Dict[str, Any]] = None,
        engine_result: Optional[Dict[str, Any]] = None,
    ):
        self.batch = batch or {}
        self.sessions = sessions or []
        self.notes = notes or []
        self.attachments = attachments or []
        self.chronograph_stats = chronograph_stats or {}
        self.engine_result = engine_result or {}

    def _setup_label(self) -> str:
        barrel_name = str(self.batch.get("barrel_name") or "").strip()
        configuration_name = str(
            self.batch.get("barrel_configuration_name") or ""
        ).strip()
        if (
            configuration_name
            and barrel_name
            and configuration_name.casefold() != barrel_name.casefold()
        ):
            return f"{barrel_name} / {configuration_name}"
        return configuration_name or barrel_name

    def _usage_goal(self) -> str:
        text = " ".join(
            str(self.batch.get(key) or "")
            for key in (
                "usage_profile_key",
                "usage_profile_name",
                "use_case",
                "purpose",
                "goal",
                "batch_goal",
            )
        ).casefold()
        if any(word in text for word in ("hunt", "jakt", "jeger", "field", "felt")):
            return "hunting"
        if any(
            word in text
            for word in (
                "competition",
                "match",
                "prs",
                "nrl",
                "dfs",
                "konkurranse",
                "presisjon",
            )
        ):
            return "competition"
        if any(
            word in text
            for word in (
                "hobby",
                "learning",
                "læring",
                "laring",
                "beginner",
                "nybegynner",
                "amatør",
                "amator",
            )
        ):
            return "learning"
        return "general"

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except Exception:
            return None

    def _group_values(self) -> List[float]:
        values: List[float] = []
        for session in self.sessions:
            group = self._safe_float(session.get("group_size_mm"))
            if group is not None:
                values.append(group)
        return values

    def _chrono_values(self) -> Dict[str, Optional[float]]:
        stats = self.chronograph_stats or {}
        return {
            "count": self._safe_float(stats.get("count")),
            "avg": self._safe_float(stats.get("avg")),
            "es": self._safe_float(stats.get("es")),
            "sd": self._safe_float(stats.get("sd")),
        }

    @staticmethod
    def _parse_session_date(value: Any) -> datetime:
        text = str(value or "").strip()
        if not text:
            return datetime.min
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    def _sorted_sessions(self) -> List[Dict[str, Any]]:
        return sorted(
            self.sessions,
            key=lambda session: (
                self._parse_session_date(session.get("session_date")),
                session.get("id") or 0,
            ),
        )

    def _session_analysis_stats(
        self, session: Dict[str, Any]
    ) -> Dict[str, Optional[float]]:
        raw = self._session_analysis_payload(session)
        if isinstance(raw, dict):
            stats = raw.get("stats") if isinstance(raw.get("stats"), dict) else raw
        else:
            stats = {}
        return {
            "count": self._safe_float(stats.get("count")),
            "avg": self._safe_float(stats.get("avg")),
            "es": self._safe_float(stats.get("es")),
            "sd": self._safe_float(stats.get("sd")),
        }

    def _session_analysis_payload(self, session: Dict[str, Any]) -> Dict[str, Any]:
        raw = session.get("analysis_json") or {}
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = {}
        return raw if isinstance(raw, dict) else {}

    def _session_pattern_metrics(self) -> Dict[str, Any]:
        vertical_values: List[float] = []
        horizontal_values: List[float] = []
        poi_x_values: List[float] = []
        poi_y_values: List[float] = []

        def first_number(*values: Any) -> Optional[float]:
            for value in values:
                parsed = self._safe_float(value)
                if parsed is not None:
                    return parsed
            return None

        for session in self.sessions:
            payload = self._session_analysis_payload(session)
            stats = (
                payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
            )
            target = (
                payload.get("target") if isinstance(payload.get("target"), dict) else {}
            )
            vertical = first_number(
                session.get("vertical_spread"),
                session.get("vertical_spread_mm"),
                payload.get("vertical_spread"),
                payload.get("vertical_spread_mm"),
                stats.get("vertical_spread"),
                stats.get("vertical_spread_mm"),
                target.get("vertical_spread"),
                target.get("vertical_spread_mm"),
            )
            horizontal = first_number(
                session.get("horizontal_spread"),
                session.get("horizontal_spread_mm"),
                payload.get("horizontal_spread"),
                payload.get("horizontal_spread_mm"),
                stats.get("horizontal_spread"),
                stats.get("horizontal_spread_mm"),
                target.get("horizontal_spread"),
                target.get("horizontal_spread_mm"),
            )
            if vertical is not None:
                vertical_values.append(vertical)
            if horizontal is not None:
                horizontal_values.append(horizontal)

            poi_x = first_number(
                session.get("poi_x_mm"),
                session.get("poi_horizontal_mm"),
                payload.get("poi_x_mm"),
                payload.get("poi_horizontal_mm"),
                stats.get("poi_x_mm"),
                target.get("poi_x_mm"),
            )
            poi_y = first_number(
                session.get("poi_y_mm"),
                session.get("poi_vertical_mm"),
                payload.get("poi_y_mm"),
                payload.get("poi_vertical_mm"),
                stats.get("poi_y_mm"),
                target.get("poi_y_mm"),
            )
            poi_x_cm = first_number(
                session.get("poi_horizontal_cm"),
                payload.get("poi_horizontal_cm"),
                stats.get("poi_horizontal_cm"),
                target.get("poi_horizontal_cm"),
            )
            poi_y_cm = first_number(
                session.get("poi_vertical_cm"),
                payload.get("poi_vertical_cm"),
                stats.get("poi_vertical_cm"),
                target.get("poi_vertical_cm"),
            )
            if poi_x is None and poi_x_cm is not None:
                poi_x = poi_x_cm * 10.0
            if poi_y is None and poi_y_cm is not None:
                poi_y = poi_y_cm * 10.0
            if poi_x is not None:
                poi_x_values.append(poi_x)
            if poi_y is not None:
                poi_y_values.append(poi_y)

        vertical_avg = mean(vertical_values) if vertical_values else None
        horizontal_avg = mean(horizontal_values) if horizontal_values else None
        axis_ratio = None
        flags: List[str] = []
        if vertical_avg is not None and horizontal_avg is not None:
            smaller = max(1e-9, min(vertical_avg, horizontal_avg))
            axis_ratio = max(vertical_avg, horizontal_avg) / smaller
            if vertical_avg >= horizontal_avg * 1.5 and vertical_avg >= 15.0:
                flags.append("vertical_dominant")
            elif horizontal_avg >= vertical_avg * 1.5 and horizontal_avg >= 15.0:
                flags.append("horizontal_dominant")
            elif axis_ratio <= 1.25:
                flags.append("round_group_pattern")

        poi_shift_x = (
            (max(poi_x_values) - min(poi_x_values)) if len(poi_x_values) >= 2 else None
        )
        poi_shift_y = (
            (max(poi_y_values) - min(poi_y_values)) if len(poi_y_values) >= 2 else None
        )
        poi_shift = (
            max(value for value in (poi_shift_x, poi_shift_y) if value is not None)
            if (poi_shift_x is not None or poi_shift_y is not None)
            else None
        )
        if poi_shift is not None and poi_shift >= 20.0:
            flags.append("poi_shift_watch")

        return {
            "flags": sorted(set(flags)),
            "vertical_avg_mm": vertical_avg,
            "horizontal_avg_mm": horizontal_avg,
            "axis_ratio": axis_ratio,
            "poi_shift_mm": poi_shift,
        }

    def _session_wind_values(self) -> List[float]:
        values: List[float] = []
        for session in self.sessions:
            for key in ("wind_speed_mps", "wind_mps", "wind_speed"):
                value = self._safe_float(session.get(key))
                if value is not None:
                    values.append(value)
                    break
        return values

    @staticmethod
    def _note_signal_flags(notes_text: str) -> List[str]:
        text = notes_text.casefold()
        groups = {
            "pressure": (
                "pressure",
                "sticky bolt",
                "flattened primer",
                "heavy bolt",
                "crater",
                "trykk",
                "tung hevarm",
                "treg hevarm",
                "hevarm",
                "treg bolt",
                "flat tennhette",
                "flate tennhetter",
                "krater",
                "hylsemerke",
                "ejector mark",
            ),
            "shooter_series": (
                "pulled",
                "flyer",
                "called flyer",
                "bad shot",
                "bad trigger",
                "jerk",
                "flinch",
                "avtrekk",
                "napp",
                "rykk",
                "dårlig skudd",
                "darlig skudd",
                "utligger",
                "brutt serie",
                "avbrutt",
                "puls",
                "stress",
                "dårlig rytme",
                "darlig rytme",
            ),
            "setup_equipment": (
                "rest",
                "support",
                "bipod",
                "position",
                "optic",
                "scope",
                "torque",
                "suppressor",
                "muzzle device",
                "støtte",
                "stotte",
                "tofoten",
                "tofot",
                "stilling",
                "kikkert",
                "montasje",
                "moment",
                "demper",
                "munningsbrems",
                "løst",
                "lost",
            ),
            "environment": (
                "wind",
                "gust",
                "mirage",
                "rain",
                "light",
                "weather",
                "vær",
                "ver",
                "vind",
                "vindkast",
                "regn",
                "lys",
                "sol",
                "skiftende",
            ),
        }
        return sorted(
            key for key, words in groups.items() if any(word in text for word in words)
        )

    def _series_change(
        self, values: List[float], *, lower_is_better: bool = True
    ) -> Dict[str, Optional[float]]:
        values = [value for value in values if value is not None]
        if len(values) < 2:
            return {"delta": None, "pct": None, "direction": None}
        if len(values) <= 3:
            first_avg = values[0]
            last_avg = values[-1]
        else:
            window = min(3, max(1, len(values) // 2))
            first_avg = mean(values[:window])
            last_avg = mean(values[-window:])
        delta = last_avg - first_avg
        base = abs(first_avg) if abs(first_avg) > 1e-9 else 1.0
        pct = (delta / base) * 100.0
        if abs(delta) < 1e-6:
            direction = "flat"
        else:
            better = delta < 0 if lower_is_better else delta > 0
            direction = "improving" if better else "worsening"
        return {"delta": delta, "pct": pct, "direction": direction}

    # Priority order used when aggregating per-session engine hints.
    # Higher index = lower priority (least blocking).
    _HINT_PRIORITY: Dict[str, int] = {
        "pressure_or_ammo": 0,
        "ammo_or_process_signal": 1,
        "possible_shooter_or_setup_signal": 2,
        "setup_drift_watch": 3,
        "environment_or_condition_signal": 4,
        "node_or_barrel_timing_signal": 5,
        "poi_shift_watch": 6,
        "target_only": 7,
        "velocity_only": 8,
        "mixed_but_stable": 9,
        "insufficient_evidence": 10,
    }

    @classmethod
    def _aggregate_session_hints(cls, sessions: List[Dict[str, Any]]) -> Optional[str]:
        """Return the highest-priority signal_hint across sessions that have one.

        Sessions enriched with ``_signal_hint`` (by recompute_batch_analysis_from_db)
        have a per-session engine-computed hint.  We pick the most blocking one so the
        batch signal reflects the worst open concern rather than the average.
        Returns None if no session carries a hint.
        """
        hints = [
            str(s.get("_signal_hint") or "").strip()
            for s in sessions
            if s.get("_signal_hint")
        ]
        if not hints:
            return None
        return min(hints, key=lambda h: cls._HINT_PRIORITY.get(h, 99))

    def _spread_learning_signal(
        self,
        *,
        groups: List[float],
        chrono: Dict[str, Optional[float]],
        group_trend: Dict[str, Optional[float]],
        note_flags: List[str],
        max_wind_mps: Optional[float],
        pattern: Dict[str, Any],
    ) -> Dict[str, Any]:
        has_pressure_note = "pressure" in note_flags
        has_shooter_note = "shooter_series" in note_flags
        has_setup_note = "setup_equipment" in note_flags
        has_environment_note = "environment" in note_flags
        pattern_flags = set(pattern.get("flags") or [])
        chrono_count = int(chrono.get("count") or 0)
        es = chrono.get("es")
        sd = chrono.get("sd")
        avg_group = mean(groups) if groups else None
        best_group = min(groups) if groups else None
        large_group = bool(
            (avg_group is not None and avg_group > 25.0)
            or (best_group is not None and best_group > 20.0)
        )
        low_velocity_spread = bool(
            chrono_count >= 5
            and es is not None
            and sd is not None
            and es <= 25.0
            and sd <= 10.0
        )
        high_velocity_spread = bool(
            chrono_count >= 5
            and ((es is not None and es > 40.0) or (sd is not None and sd > 18.0))
        )
        group_worsening = group_trend.get("direction") == "worsening"
        windy_group_context = bool(
            groups and max_wind_mps is not None and max_wind_mps >= 5.0
        )
        vertical_dominant = "vertical_dominant" in pattern_flags
        horizontal_dominant = "horizontal_dominant" in pattern_flags
        poi_shift_watch = "poi_shift_watch" in pattern_flags

        if has_pressure_note:
            return {
                "hint": "pressure_or_ammo",
                "confidence": "medium",
                "reason": "Batch notes mention pressure signs, so safety and ammunition behavior must be confirmed before precision tuning.",
                "watchouts": [
                    "Pressure-related notes make this a conservative ammo/safety watch before any optimization."
                ],
            }
        if has_setup_note and groups:
            return {
                "hint": "setup_drift_watch",
                "confidence": "medium",
                "reason": "Notes mention support, optic, torque, suppressor, position, or other setup/equipment context, so the group result needs setup confirmation before load judgment.",
                "watchouts": [
                    "Setup or equipment notes can make a load look worse; confirm support, optic, torque, muzzle device, and barrel state before changing the recipe."
                ],
            }
        if high_velocity_spread and large_group:
            return {
                "hint": "ammo_or_process_signal",
                "confidence": "medium",
                "reason": "Large groups appear together with high ES/SD, which points toward ammunition, loading process, or component variation.",
                "watchouts": [
                    "High velocity spread and open groups should be treated as a load/process signal until a control series disproves it."
                ],
            }
        if high_velocity_spread and vertical_dominant:
            return {
                "hint": "ammo_or_process_signal",
                "confidence": "medium",
                "reason": "Vertical-dominant target spread appears together with high ES/SD, which strengthens the ammunition, loading process, or velocity-variation signal.",
                "watchouts": [
                    "Vertical spread and high ES/SD should be confirmed with a same-setup chrono control series before seating or aiming changes."
                ],
            }
        if has_environment_note and groups:
            return {
                "hint": "environment_or_condition_signal",
                "confidence": "medium",
                "reason": "Notes mention wind, mirage, light, weather, or changing conditions, so the group result needs environmental confirmation before load judgment.",
                "watchouts": [
                    "Condition notes can hide the real load behavior; repeat or compare in known wind and mirage before rejecting or trusting the recipe."
                ],
            }
        if windy_group_context:
            return {
                "hint": "environment_or_condition_signal",
                "confidence": "low",
                "reason": f"Recorded wind reached about {max_wind_mps:.1f} m/s during group evidence, so condition effects should be separated from load behavior.",
                "watchouts": [
                    "High or changing wind can open groups; repeat in calmer or well-documented conditions before changing the load."
                ],
            }
        if horizontal_dominant:
            return {
                "hint": "environment_or_condition_signal",
                "confidence": "low",
                "reason": "The group pattern is horizontal-dominant, which often needs wind, mirage, support, cant, or position control before load judgment.",
                "watchouts": [
                    "Horizontal-dominant spread should be repeated with known wind, stable support, and consistent rifle cant before changing the load."
                ],
            }
        if has_shooter_note and groups:
            return {
                "hint": "possible_shooter_or_setup_signal",
                "confidence": "medium",
                "reason": "Batch or session notes mention shooter, rhythm, trigger, flyer, or interrupted-series conditions, so group spread should not be treated as pure ammunition behavior yet.",
                "watchouts": [
                    "Session notes point to possible shooter or series influence; repeat under controlled conditions before rejecting the load."
                ],
            }
        if poi_shift_watch:
            return {
                "hint": "setup_drift_watch",
                "confidence": "low",
                "reason": "Point of impact shifts between sessions, so setup, zero, barrel condition, or condition drift should be confirmed before ranking the load.",
                "watchouts": [
                    "POI movement can hide the real group/load signal; confirm zero, optic, torque, barrel condition, and conditions before changing the recipe."
                ],
            }
        if not groups and chrono_count < 5:
            return {
                "hint": "insufficient_evidence",
                "confidence": "low",
                "reason": "The batch has too little measured group and chrono evidence to separate ammunition behavior from shooter or setup effects.",
                "watchouts": [
                    "Collect matched chrono and group evidence before ranking this load."
                ],
            }
        if low_velocity_spread and large_group:
            return {
                "hint": "possible_shooter_or_setup_signal",
                "confidence": "medium",
                "reason": "Chronograph spread is controlled while groups are still open, so the batch may be showing shooter, setup, rest, optic, or condition effects rather than pure ammo spread.",
                "watchouts": [
                    "Do not reject the load from group size alone; repeat with controlled support, rhythm, and point-of-aim conditions."
                ],
            }
        if low_velocity_spread and vertical_dominant:
            return {
                "hint": "node_or_barrel_timing_signal",
                "confidence": "low",
                "reason": "Chronograph spread is controlled but the target pattern is vertical-dominant, so seating depth, barrel timing, rest tracking, or point-of-aim consistency should be checked before blaming charge spread.",
                "watchouts": [
                    "Low ES/SD with vertical-dominant spread calls for a controlled repeat and small seating or barrel-timing checks, not a broad powder change."
                ],
            }
        if group_worsening:
            return {
                "hint": "setup_drift_watch",
                "confidence": "low",
                "reason": "Groups are opening between sessions, so setup drift, barrel condition, environmental change, or shooter-series variation should be confirmed.",
                "watchouts": [
                    "Worsening groups need a control series before assuming the load itself has degraded."
                ],
            }
        if groups and chrono_count < 5:
            return {
                "hint": "target_only",
                "confidence": "low",
                "reason": "The batch has group evidence but not enough chrono evidence to separate vertical ammunition spread from shooter or setup effects.",
                "watchouts": [
                    "Add a chrono control string before drawing strong conclusions from the group."
                ],
            }
        if chrono_count >= 5 and not groups:
            return {
                "hint": "velocity_only",
                "confidence": "low",
                "reason": "The batch has chrono evidence but no group validation for the active setup.",
                "watchouts": [
                    "Add a measured group before ranking precision or seating changes."
                ],
            }
        return {
            "hint": "mixed_but_stable",
            "confidence": "low",
            "reason": "Current chrono and group evidence does not show a clear single cause; keep using controlled confirmation series.",
            "watchouts": [],
        }

    @staticmethod
    def _spread_control_plan(hint: str) -> Dict[str, Any]:
        plans = {
            "pressure_or_ammo": {
                "priority": "safety",
                "title": "Pressure and ammo safety check",
                "primary_action": "Stop precision tuning; inspect pressure evidence and only repeat from a conservative lower control point if the load is safe.",
                "shot_plan": "Use a reduced control load or known-safe reference, chrono the first 3 to 5 shots, and inspect every case and primer.",
                "avoid": "Do not chase group size, seating depth, or velocity while pressure behavior is unresolved.",
                "success_criteria": "No repeated pressure signs and predictable velocity before any precision optimization resumes.",
            },
            "ammo_or_process_signal": {
                "priority": "high",
                "title": "Ammo/process control series",
                "primary_action": "Run a same-setup control series and inspect charge, seating, neck tension, case lot, and component lot consistency before tuning several variables.",
                "shot_plan": "Load 5 to 10 identical rounds, chrono every shot, and fire one documented group under the same rifle and support setup.",
                "avoid": "Do not change charge and seating at the same time until the process signal is confirmed or disproven.",
                "success_criteria": "ES/SD and group behavior move together or the process variable is isolated.",
            },
            "possible_shooter_or_setup_signal": {
                "priority": "medium",
                "title": "Controlled repeatability group",
                "primary_action": "Repeat one controlled group with the same load before rejecting it; hold support, position, rhythm, cant, and point of aim constant.",
                "shot_plan": "Fire one 5-shot group, call any flyer immediately, and keep chrono optional unless velocity evidence is also weak.",
                "avoid": "Do not discard a promising load based on one open or interrupted series.",
                "success_criteria": "The repeat group confirms whether the spread follows the load or the series conditions.",
            },
            "setup_drift_watch": {
                "priority": "medium",
                "title": "Setup and zero control",
                "primary_action": "Confirm optic, action torque, muzzle device, barrel condition, zero, and POI before treating group drift as load failure.",
                "shot_plan": "Check setup mechanically, then fire a short control group with the same load and documented zero/reference point.",
                "avoid": "Do not change the recipe before setup drift and POI movement are checked.",
                "success_criteria": "POI and grouping repeat after setup confirmation, or the drifting element is found.",
            },
            "environment_or_condition_signal": {
                "priority": "medium",
                "title": "Known-condition repeat",
                "primary_action": "Repeat or compare the same load in calmer or well-documented wind, mirage, light, and temperature before changing charge or seating.",
                "shot_plan": "Fire one group with wind/mirage notes and, if possible, compare against a known reference load in the same conditions.",
                "avoid": "Do not tune around a condition-driven horizontal or unstable group pattern.",
                "success_criteria": "The load repeats in controlled conditions or the condition effect is clearly separated.",
            },
            "node_or_barrel_timing_signal": {
                "priority": "medium",
                "title": "Vertical pattern and barrel timing check",
                "primary_action": "Repeat the same load with careful tracking and point of aim; if vertical spread remains with stable ES/SD, test a small seating-depth bracket.",
                "shot_plan": "Fire one control group, then test 2 to 3 small seating-depth steps while keeping charge, lot, support, and conditions stable.",
                "avoid": "Do not make a broad powder change before confirming whether the vertical pattern follows seating, timing, support tracking, or aim.",
                "success_criteria": "Vertical spread shrinks or repeats clearly enough to guide seating/timing work.",
            },
            "target_only": {
                "priority": "low",
                "title": "Add chrono evidence",
                "primary_action": "Add a chrono string for the same load and setup before ranking the target result strongly.",
                "shot_plan": "Chrono 5 shots and pair the string with one measured group under the same setup.",
                "avoid": "Do not infer velocity spread or pressure stability from group size alone.",
                "success_criteria": "Target and velocity evidence describe the same setup and lot.",
            },
            "velocity_only": {
                "priority": "low",
                "title": "Add group validation",
                "primary_action": "Add a measured group for the same chrono-proven load before ranking precision or seating behavior.",
                "shot_plan": "Fire one documented group with the same lot, charge, seating, and setup used for the chrono string.",
                "avoid": "Do not accept a low ES/SD load as precise until it is validated on target.",
                "success_criteria": "Velocity and group behavior support the same decision.",
            },
            "insufficient_evidence": {
                "priority": "low",
                "title": "Collect matched evidence",
                "primary_action": "Capture matched chrono and group evidence before making a hard call on ammo, shooter, setup, or conditions.",
                "shot_plan": "Log at least one 5-shot chrono string and one measured group under the same rifle setup and conditions.",
                "avoid": "Do not optimize or reject the load from thin or unmatched data.",
                "success_criteria": "The batch has enough paired evidence to separate likely causes.",
            },
        }
        return dict(
            plans.get(
                hint,
                {
                    "priority": "low",
                    "title": "Stable confirmation series",
                    "primary_action": "Keep the current load stable and confirm it with another controlled series before making small optimizations.",
                    "shot_plan": "Repeat one matched chrono and group series with the same setup.",
                    "avoid": "Do not change multiple variables at once.",
                    "success_criteria": "The result repeats closely enough to justify the next tuning step.",
                },
            )
        )

    @staticmethod
    def _spread_decision_state(
        hint: str,
        *,
        groups: List[float],
        chrono: Dict[str, Optional[float]],
        confidence: str,
    ) -> Dict[str, Any]:
        chrono_count = int(chrono.get("count") or 0)
        paired_evidence = bool(groups and chrono_count >= 5)
        stable_evidence = bool(
            paired_evidence
            and (chrono.get("es") is None or (chrono.get("es") or 0.0) <= 30.0)
            and (chrono.get("sd") is None or (chrono.get("sd") or 0.0) <= 12.0)
        )
        states = {
            "pressure_or_ammo": {
                "state": "safety_stop",
                "label": "Safety first",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "Pressure or ammunition safety evidence must be resolved before precision decisions.",
            },
            "ammo_or_process_signal": {
                "state": "process_control_required",
                "label": "Control ammo/process before tuning",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "High velocity spread or process-like behavior should be confirmed before changing several variables or rejecting the recipe.",
            },
            "possible_shooter_or_setup_signal": {
                "state": "repeat_before_rejecting",
                "label": "Repeat before rejecting",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "The load may be better than the group suggests; repeat under controlled series conditions first.",
            },
            "setup_drift_watch": {
                "state": "setup_control_required",
                "label": "Confirm setup before judging load",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "Setup, zero, POI, or barrel-condition drift can masquerade as a load problem.",
            },
            "environment_or_condition_signal": {
                "state": "condition_control_required",
                "label": "Confirm conditions before judging load",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "Wind, mirage, light, or changing conditions can hide true load behavior.",
            },
            "node_or_barrel_timing_signal": {
                "state": "focused_tuning_after_repeat",
                "label": "Repeat, then tune seating/timing",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "Stable ES/SD with vertical pattern should be repeated before seating or barrel-timing work.",
            },
            "target_only": {
                "state": "collect_velocity_before_decision",
                "label": "Add chrono before deciding",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "Target evidence needs paired chrono data before strong load ranking.",
            },
            "velocity_only": {
                "state": "collect_group_before_decision",
                "label": "Add group before deciding",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "Chrono evidence needs target validation before precision ranking.",
            },
            "insufficient_evidence": {
                "state": "collect_matched_evidence",
                "label": "Collect matched evidence",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "There is not enough paired evidence to separate load, shooter, setup, and conditions.",
            },
        }
        if hint in states:
            result = dict(states[hint])
        elif stable_evidence and (confidence in {"medium", "high"} or len(groups) >= 2):
            result = {
                "state": "ready_for_cautious_optimization",
                "label": "Ready for cautious optimization",
                "can_optimize": True,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "Paired chrono and group evidence looks stable enough for one-variable-at-a-time tuning.",
            }
        elif paired_evidence:
            result = {
                "state": "confirm_before_optimization",
                "label": "Confirm once before optimizing",
                "can_optimize": False,
                "can_reject_load": False,
                "can_accept_load": False,
                "rationale": "The evidence is paired, but the cause signal is still weak enough to deserve one confirmation series.",
            }
        else:
            result = dict(states["insufficient_evidence"])
        result["paired_evidence"] = paired_evidence
        result["chrono_count"] = chrono_count
        result["group_count"] = len(groups)
        return result

    @staticmethod
    def _spread_profile_guidance(hint: str, usage_goal: str) -> Dict[str, Any]:
        if usage_goal == "hunting":
            if hint == "pressure_or_ammo":
                emphasis = "Safety margin and humane field reliability come before group tuning."
            elif hint in {
                "possible_shooter_or_setup_signal",
                "environment_or_condition_signal",
            }:
                emphasis = "Confirm cold-bore point of impact from realistic field support before trusting or rejecting the load."
            elif hint == "setup_drift_watch":
                emphasis = "Confirm zero, optic, muzzle device, and cold-bore POI before hunting use."
            else:
                emphasis = "Prioritize a conservative, repeatable cold-bore validation over maximum tuning."
            return {
                "usage_goal": "hunting",
                "title": "Hunting validation focus",
                "emphasis": emphasis,
                "recommended_check": "Use one cold-bore shot plus a short chrono/control group from realistic support before field approval.",
                "explanation_style": "plain_safety_first",
            }
        if usage_goal == "competition":
            if hint == "ammo_or_process_signal":
                emphasis = "Separate loading-process variation from rifle/setup variation before chasing a node."
            elif hint == "node_or_barrel_timing_signal":
                emphasis = "Use repeatable ES/SD, vertical pattern, and seating-depth brackets to isolate the tuning direction."
            elif hint in {"possible_shooter_or_setup_signal", "setup_drift_watch"}:
                emphasis = "Lock setup, support, zero, and shooter process before ranking the load."
            else:
                emphasis = "Demand repeatability across matched chrono and group evidence before competition ranking."
            return {
                "usage_goal": "competition",
                "title": "Competition repeatability focus",
                "emphasis": emphasis,
                "recommended_check": "Use same-setup control strings, documented groups, and lot/setup separation before final ranking.",
                "explanation_style": "technical_repeatability",
            }
        if usage_goal == "learning":
            if hint == "insufficient_evidence":
                emphasis = "Build understanding with one simple matched chrono-and-group test before changing the recipe."
            else:
                emphasis = "Change only one thing at a time and learn what the signal is trying to separate."
            return {
                "usage_goal": "learning",
                "title": "Learning and hobby focus",
                "emphasis": emphasis,
                "recommended_check": "Keep the next test small, write down conditions, and compare one clear variable at a time.",
                "explanation_style": "teaching",
            }
        return {
            "usage_goal": "general",
            "title": "General validation focus",
            "emphasis": "Keep the next test conservative and matched to the evidence gap.",
            "recommended_check": "Use one controlled repeat with the same rifle setup, lot, charge, seating, and conditions.",
            "explanation_style": "balanced",
        }

    @staticmethod
    def _spread_evidence_quality(
        *,
        groups: List[float],
        chrono: Dict[str, Optional[float]],
        note_flags: List[str],
        pattern: Dict[str, Any],
        max_wind_mps: Optional[float],
        attachment_count: int,
    ) -> Dict[str, Any]:
        chrono_count = int(chrono.get("count") or 0)
        group_count = len(groups)
        score = 0.0
        strengths: List[str] = []
        limitations: List[str] = []
        missing: List[str] = []

        if chrono_count >= 10:
            score += 25.0
            strengths.append("chrono_sample_10_plus")
        elif chrono_count >= 5:
            score += 18.0
            strengths.append("chrono_sample_5_plus")
        elif chrono_count > 0:
            score += 8.0
            limitations.append("thin_chrono_sample")
        else:
            missing.append("chrono_string")

        if group_count >= 3:
            score += 25.0
            strengths.append("repeat_group_3_plus")
        elif group_count >= 2:
            score += 18.0
            strengths.append("repeat_group_2_plus")
        elif group_count == 1:
            score += 10.0
            limitations.append("single_group_only")
        else:
            missing.append("measured_group")

        if chrono_count >= 5 and group_count >= 1:
            score += 20.0
            strengths.append("paired_chrono_group")
        else:
            limitations.append("unpaired_or_incomplete_evidence")

        if pattern.get("flags"):
            score += 10.0
            strengths.append("target_pattern_context")
        else:
            missing.append("vertical_horizontal_or_poi_context")

        if note_flags:
            score += 8.0
            strengths.append("session_notes_context")
        else:
            missing.append("condition_or_series_notes")

        if max_wind_mps is not None:
            score += 7.0
            strengths.append("wind_context")
        else:
            missing.append("wind_context")

        if attachment_count > 0:
            score += min(5.0, attachment_count * 2.5)
            strengths.append("image_attachment_context")

        score = max(0.0, min(100.0, score))
        level = score_to_level(score)

        recommended_logging: List[str] = []
        if "chrono_string" in missing or "thin_chrono_sample" in limitations:
            recommended_logging.append(
                "Log a 5-shot or larger chrono string for the same setup."
            )
        if "measured_group" in missing or "single_group_only" in limitations:
            recommended_logging.append(
                "Log at least one repeat measured group before ranking the load strongly."
            )
        if "vertical_horizontal_or_poi_context" in missing:
            recommended_logging.append(
                "Capture vertical/horizontal pattern or POI shift when the target data supports it."
            )
        if "condition_or_series_notes" in missing:
            recommended_logging.append(
                "Add short notes for wind, mirage, support, rhythm, and called flyers."
            )
        if "wind_context" in missing:
            recommended_logging.append(
                "Record wind speed or a short wind/mirage note for the group."
            )

        return {
            "score": round(score, 1),
            "level": level,
            "paired_evidence": chrono_count >= 5 and group_count >= 1,
            "chrono_count": chrono_count,
            "group_count": group_count,
            "strengths": strengths,
            "limitations": limitations,
            "missing": sorted(set(missing)),
            "recommended_logging": recommended_logging,
        }

    @staticmethod
    def _spread_learning_explanation(
        hint: str,
        *,
        usage_goal: str,
        evidence_quality: Dict[str, Any],
        pattern: Dict[str, Any],
    ) -> Dict[str, Any]:
        complexity = {
            "hunting": "simple",
            "learning": "teaching",
            "competition": "technical",
        }.get(usage_goal, "balanced")
        base = {
            "pressure_or_ammo": {
                "title": "Pressure signs override precision",
                "plain_summary": "Pressure or ammunition safety signs must be resolved before the group size matters.",
                "causal_chain": [
                    "Pressure signs can indicate unsafe margin.",
                    "Unsafe margin can change velocity, case behavior, and rifle stress.",
                    "Precision tuning is not reliable until safety is stable.",
                ],
                "watch_next": [
                    "primer/case condition",
                    "bolt lift",
                    "velocity jump",
                    "known-safe reference load",
                ],
            },
            "ammo_or_process_signal": {
                "title": "Velocity spread and group spread can point to process variation",
                "plain_summary": "When high ES/SD and open groups appear together, the load or loading process needs a control check.",
                "causal_chain": [
                    "Charge, neck tension, case capacity, seating, or lot variation can change muzzle velocity.",
                    "Velocity variation often shows up as vertical or inconsistent group behavior.",
                    "A same-setup control series separates process variation from shooter/setup noise.",
                ],
                "watch_next": [
                    "charge consistency",
                    "neck tension",
                    "case lot",
                    "seating consistency",
                    "ES/SD",
                ],
            },
            "possible_shooter_or_setup_signal": {
                "title": "A bad group is not always a bad load",
                "plain_summary": "Stable chrono with open groups can mean the series, support, position, or setup affected the target.",
                "causal_chain": [
                    "A stable load can still group poorly if the shot process changes.",
                    "Support, rhythm, trigger break, cant, and point of aim can open a group.",
                    "Repeating one controlled group protects good loads from being rejected too early.",
                ],
                "watch_next": [
                    "support",
                    "position",
                    "rhythm",
                    "called flyers",
                    "rifle cant",
                ],
            },
            "setup_drift_watch": {
                "title": "Setup drift can hide load behavior",
                "plain_summary": "POI shift or setup notes mean the rifle system should be checked before the recipe is judged.",
                "causal_chain": [
                    "Optic, torque, muzzle device, zero, or barrel condition can shift point of impact.",
                    "That shift can make the load look unstable even if the ammunition is repeatable.",
                    "Setup confirmation turns the next group into useful evidence.",
                ],
                "watch_next": [
                    "zero",
                    "optic/mount",
                    "action torque",
                    "muzzle device",
                    "barrel condition",
                ],
            },
            "environment_or_condition_signal": {
                "title": "Conditions can create false load signals",
                "plain_summary": "Wind, mirage, light, or changing conditions can open groups without the load being the main cause.",
                "causal_chain": [
                    "Wind and mirage change apparent point of aim and bullet path.",
                    "Horizontal or unstable patterns often need condition control.",
                    "Repeating in known conditions separates environment from ammunition behavior.",
                ],
                "watch_next": [
                    "wind",
                    "mirage",
                    "light",
                    "temperature",
                    "known-condition repeat",
                ],
            },
            "node_or_barrel_timing_signal": {
                "title": "Stable velocity with vertical spread can be timing or tracking",
                "plain_summary": "If ES/SD is controlled but the target is vertical, check tracking and seating/barrel timing before changing powder broadly.",
                "causal_chain": [
                    "Low ES/SD means velocity spread is not the obvious first suspect.",
                    "Vertical pattern can come from seating depth, barrel timing, support tracking, or point of aim.",
                    "A small seating bracket after a repeat test is safer than changing many variables.",
                ],
                "watch_next": [
                    "vertical spread",
                    "seating depth",
                    "barrel timing",
                    "rest tracking",
                    "point of aim",
                ],
            },
            "insufficient_evidence": {
                "title": "The system needs paired evidence",
                "plain_summary": "The data is too thin to separate ammunition, shooter, setup, and conditions confidently.",
                "causal_chain": [
                    "Chrono alone cannot prove precision.",
                    "Group alone cannot prove velocity consistency.",
                    "Matched chrono and group data lets the system compare cause and effect.",
                ],
                "watch_next": [
                    "5-shot chrono",
                    "measured group",
                    "same setup",
                    "short notes",
                ],
            },
        }
        payload = dict(
            base.get(
                hint,
                {
                    "title": "Stable data supports careful next steps",
                    "plain_summary": "The current evidence does not point to one clear fault, so one-variable-at-a-time confirmation is the right direction.",
                    "causal_chain": [
                        "Mixed but stable evidence can still be useful.",
                        "Changing one variable at a time keeps the lesson readable.",
                        "Repeated matched evidence makes future recommendations stronger.",
                    ],
                    "watch_next": [
                        "repeatability",
                        "same setup",
                        "one variable",
                        "matched chrono and group",
                    ],
                },
            )
        )
        payload["complexity"] = complexity
        payload["usage_goal"] = usage_goal
        payload["evidence_quality_level"] = evidence_quality.get("level")
        payload["evidence_missing"] = evidence_quality.get("missing") or []
        payload["pattern_flags"] = pattern.get("flags") or []
        if usage_goal == "hunting":
            payload["user_takeaway"] = (
                "For hunting, prove safe cold-bore field behavior before trusting the load."
            )
        elif usage_goal == "competition":
            payload["user_takeaway"] = (
                "For competition, prove repeatability before ranking or tuning aggressively."
            )
        elif usage_goal == "learning":
            payload["user_takeaway"] = (
                "For learning, keep the next test small so the cause becomes easier to see."
            )
        else:
            payload["user_takeaway"] = (
                "Confirm the signal with matched evidence before making a hard decision."
            )
        return payload

    @staticmethod
    def _spread_capture_checklist(
        hint: str,
        *,
        usage_goal: str,
        evidence_quality: Dict[str, Any],
        note_flags: List[str],
        pattern: Dict[str, Any],
    ) -> Dict[str, Any]:
        missing = set(evidence_quality.get("missing") or [])
        items: List[Dict[str, Any]] = []

        def add_item(key: str, label: str, why: str, priority: str) -> None:
            if key not in {item["key"] for item in items}:
                items.append(
                    {"key": key, "label": label, "why": why, "priority": priority}
                )

        if (
            hint in {"insufficient_evidence", "target_only"}
            or "chrono_string" in missing
        ):
            add_item(
                "chrono_string",
                "5+ shot chrono string",
                "Needed to connect group behavior to velocity consistency.",
                "high",
            )
        if (
            hint in {"insufficient_evidence", "velocity_only"}
            or "measured_group" in missing
        ):
            add_item(
                "repeat_group",
                "Repeat measured group",
                "Needed to validate precision on target for the same setup.",
                "high",
            )
        if "vertical_horizontal_or_poi_context" in missing:
            add_item(
                "target_pattern",
                "Vertical/horizontal or POI context",
                "Pattern data helps separate load, setup, and environment effects.",
                "medium",
            )
        if "condition_or_series_notes" in missing or hint in {
            "possible_shooter_or_setup_signal",
            "environment_or_condition_signal",
        }:
            add_item(
                "session_notes",
                "Short shot-process notes",
                "Notes about wind, support, rhythm, and flyers explain group behavior.",
                "medium",
            )
        if "wind_context" in missing or hint == "environment_or_condition_signal":
            add_item(
                "wind_context",
                "Wind or mirage note",
                "Condition logging helps rule in or out environmental spread.",
                "medium",
            )
        if hint == "setup_drift_watch":
            add_item(
                "setup_check",
                "Optic/torque/zero check",
                "Setup drift can mimic a bad load.",
                "high",
            )
        if hint == "node_or_barrel_timing_signal":
            add_item(
                "seating_bracket",
                "Small seating-depth bracket",
                "A narrow seating test is safer than a broad powder change.",
                "medium",
            )
        if hint == "ammo_or_process_signal":
            add_item(
                "process_check",
                "Charge and case-process check",
                "Process variation is a likely source of the spread.",
                "high",
            )
        if usage_goal == "hunting":
            add_item(
                "cold_bore",
                "Cold-bore validation",
                "Field confidence depends on first-shot behavior, not only warm groups.",
                "high",
            )
            add_item(
                "field_support",
                "Realistic field support note",
                "Hunting decisions need support and position context.",
                "medium",
            )
        elif usage_goal == "competition":
            add_item(
                "same_setup_repeat",
                "Same-setup repeat string",
                "Competition ranking needs repeatability before scoring a load highly.",
                "high",
            )
        elif usage_goal == "learning":
            add_item(
                "one_variable",
                "One variable changed",
                "Learning is clearer when only one factor changes at a time.",
                "medium",
            )

        if not items:
            add_item(
                "matched_repeat",
                "Matched repeat series",
                "A controlled repeat keeps the learning loop honest.",
                "medium",
            )

        return {
            "usage_goal": usage_goal,
            "title": "Next capture checklist",
            "items": items,
            "highest_priority": next(
                (item["label"] for item in items if item["priority"] == "high"),
                items[0]["label"],
            ),
        }

    @staticmethod
    def _spread_validation_status(
        hint: str,
        *,
        usage_goal: str,
        decision: Dict[str, Any],
        evidence_quality: Dict[str, Any],
        pattern: Dict[str, Any],
        note_flags: List[str],
    ) -> Dict[str, Any]:
        quality_level = str(evidence_quality.get("level") or "very_thin").strip()
        evidence_score = float(evidence_quality.get("score") or 0.0)
        paired_evidence = bool(decision.get("paired_evidence"))
        blocking_factors: List[str] = []
        if not paired_evidence:
            blocking_factors.append("paired_evidence_missing")
        if quality_level in {"very_thin", "thin"}:
            blocking_factors.append("evidence_quality_too_thin")
        if "poi_shift_watch" in (pattern.get("flags") or []):
            blocking_factors.append("poi_shift_unconfirmed")
        if hint == "pressure_or_ammo" or "pressure" in note_flags:
            blocking_factors.append("safety_unresolved")

        if usage_goal == "hunting":
            blocking_factors.append("cold_bore_field_confirmation_pending")
            if hint == "pressure_or_ammo":
                return {
                    "usage_goal": "hunting",
                    "status": "safety_block",
                    "label": "Not field-safe yet",
                    "summary": "Pressure or ammo safety signs block field use until the load is backed down and re-validated.",
                    "next_gate": "Resolve pressure signs, then confirm a conservative cold-bore field check before hunting use.",
                    "readiness_score": 0.0,
                    "ready_now": False,
                    "blocking_factors": blocking_factors,
                }
            if hint in {
                "ammo_or_process_signal",
                "possible_shooter_or_setup_signal",
                "setup_drift_watch",
                "environment_or_condition_signal",
                "insufficient_evidence",
                "target_only",
                "velocity_only",
            }:
                return {
                    "usage_goal": "hunting",
                    "status": "field_validation_pending",
                    "label": "Not field-ready yet",
                    "summary": "The load still needs a controlled repeat and a conservative field-style confirmation before it should be trusted for hunting.",
                    "next_gate": "Resolve the current spread signal, then confirm one cold-bore shot plus a short realistic-support control series.",
                    "readiness_score": round(min(evidence_score, 55.0), 1),
                    "ready_now": False,
                    "blocking_factors": blocking_factors,
                }
            return {
                "usage_goal": "hunting",
                "status": "cold_bore_confirmation_pending",
                "label": "Candidate for cold-bore confirmation",
                "summary": "The load looks promising, but hunting trust still depends on first-shot and realistic-support validation.",
                "next_gate": "Confirm one cold-bore field shot and a short support-matched control group before treating it as hunting-ready.",
                "readiness_score": round(min(max(evidence_score, 60.0), 78.0), 1),
                "ready_now": False,
                "blocking_factors": blocking_factors,
            }

        if usage_goal == "competition":
            if hint == "pressure_or_ammo":
                return {
                    "usage_goal": "competition",
                    "status": "safety_block",
                    "label": "Not competition-ready",
                    "summary": "Pressure or ammo safety concerns block ranking and optimization until the load is stabilized safely.",
                    "next_gate": "Resolve safety first, then rebuild matched chrono and group evidence before ranking this setup.",
                    "readiness_score": 0.0,
                    "ready_now": False,
                    "blocking_factors": blocking_factors,
                }
            if hint in {
                "ammo_or_process_signal",
                "possible_shooter_or_setup_signal",
                "setup_drift_watch",
                "environment_or_condition_signal",
                "insufficient_evidence",
                "target_only",
                "velocity_only",
            }:
                return {
                    "usage_goal": "competition",
                    "status": "ranking_validation_pending",
                    "label": "Not ranking-ready yet",
                    "summary": "Competition ranking should wait until the spread signal is separated with same-setup repeat evidence.",
                    "next_gate": "Run a same-setup repeat/control string and keep process, wind, and setup variables documented before ranking the load.",
                    "readiness_score": round(min(evidence_score, 58.0), 1),
                    "ready_now": False,
                    "blocking_factors": blocking_factors,
                }
            if hint == "node_or_barrel_timing_signal":
                blocking_factors.append("vertical_pattern_confirmation_pending")
                return {
                    "usage_goal": "competition",
                    "status": "tuning_validation_pending",
                    "label": "Repeat before ranking or tuning harder",
                    "summary": "Stable ES/SD is promising, but the vertical pattern still needs repeat confirmation before seating-depth ranking.",
                    "next_gate": "Repeat one same-setup control group, then use a narrow seating-depth bracket if the vertical pattern remains.",
                    "readiness_score": round(min(max(evidence_score, 58.0), 72.0), 1),
                    "ready_now": False,
                    "blocking_factors": blocking_factors,
                }
            ready_now = (
                paired_evidence
                and quality_level in {"moderate", "strong"}
                and decision.get("can_optimize") is True
            )
            return {
                "usage_goal": "competition",
                "status": "cautious_ranking_candidate",
                "label": "Candidate for cautious ranking",
                "summary": "The evidence is stable enough to compare this load cautiously, but ranking should still stay tied to matched conditions and setup control.",
                "next_gate": "Confirm one more same-setup repeat string before treating the ranking as durable across sessions or matches.",
                "readiness_score": round(
                    (
                        max(evidence_score, 70.0)
                        if ready_now
                        else min(max(evidence_score, 60.0), 72.0)
                    ),
                    1,
                ),
                "ready_now": ready_now,
                "blocking_factors": blocking_factors,
            }

        if usage_goal == "learning":
            if hint == "pressure_or_ammo":
                return {
                    "usage_goal": "learning",
                    "status": "safety_block",
                    "label": "Pause and fix safety first",
                    "summary": "This is not a good learning example until the load is brought back to a safe, conservative baseline.",
                    "next_gate": "Back off the load, confirm safety, then capture one simple matched example before resuming tuning.",
                    "readiness_score": 0.0,
                    "ready_now": False,
                    "blocking_factors": blocking_factors,
                }
            if hint in {
                "insufficient_evidence",
                "target_only",
                "velocity_only",
            } or quality_level in {"very_thin", "thin"}:
                return {
                    "usage_goal": "learning",
                    "status": "collect_more_data",
                    "label": "Needs one clearer example",
                    "summary": "The module can teach more effectively after one small, well-matched example with target and chrono data.",
                    "next_gate": "Capture one simple matched test with a measured group, a short chrono string, and a short note about conditions.",
                    "readiness_score": round(min(evidence_score, 52.0), 1),
                    "ready_now": False,
                    "blocking_factors": blocking_factors,
                }
            return {
                "usage_goal": "learning",
                "status": "learning_cycle_ready",
                "label": "Ready for the next learning cycle",
                "summary": "The evidence is good enough to teach something useful as long as the next change stays small and readable.",
                "next_gate": "Change one variable at a time and log the same measurements again so the lesson stays clear.",
                "readiness_score": round(max(evidence_score, 58.0), 1),
                "ready_now": True,
                "blocking_factors": blocking_factors,
            }

        if hint == "pressure_or_ammo":
            return {
                "usage_goal": "general",
                "status": "safety_block",
                "label": "Not ready for use decisions",
                "summary": "Safety concerns must be resolved before this load is trusted or tuned further.",
                "next_gate": "Resolve safety first, then rebuild matched validation data.",
                "readiness_score": 0.0,
                "ready_now": False,
                "blocking_factors": blocking_factors,
            }
        if (
            paired_evidence
            and quality_level in {"moderate", "strong"}
            and hint
            not in {
                "ammo_or_process_signal",
                "possible_shooter_or_setup_signal",
                "setup_drift_watch",
                "environment_or_condition_signal",
                "insufficient_evidence",
                "target_only",
                "velocity_only",
            }
        ):
            return {
                "usage_goal": "general",
                "status": "cautious_validation_candidate",
                "label": "Candidate for cautious validation",
                "summary": "The evidence is stable enough for conservative one-variable-at-a-time follow-up.",
                "next_gate": "Confirm one more matched series before calling the result durable.",
                "readiness_score": round(max(evidence_score, 65.0), 1),
                "ready_now": True,
                "blocking_factors": blocking_factors,
            }
        return {
            "usage_goal": "general",
            "status": "provisional_validation",
            "label": "Provisional validation only",
            "summary": "The current result is still provisional until the signal is repeated with stronger matched evidence.",
            "next_gate": "Repeat the load with the same setup and fill the biggest evidence gaps before making a hard call.",
            "readiness_score": round(min(evidence_score, 58.0), 1),
            "ready_now": False,
            "blocking_factors": blocking_factors,
        }

    def analyze(self) -> BatchAnalysis:
        sessions = self._sorted_sessions()
        groups = self._group_values()
        chrono = self._chrono_values()
        batch_note_text = " ".join((n.get("note_text", "") or "") for n in self.notes)
        session_note_text = " ".join(
            (session.get("notes", "") or "") for session in sessions
        )
        notes_text = f"{batch_note_text} {session_note_text}".lower()
        note_flags = self._note_signal_flags(notes_text)
        wind_values = self._session_wind_values()
        max_wind_mps = max(wind_values) if wind_values else None
        pattern_metrics = self._session_pattern_metrics()
        usage_goal = self._usage_goal()
        batch_name = self.batch.get("batch_name") or self.batch.get("name") or "Batch"
        setup_label = self._setup_label()

        strengths: List[str] = []
        watchouts: List[str] = []
        next_steps: List[str] = []
        score = 0.0
        confidence = 12.0
        trend_summary = ""
        next_focus = ""
        improvement_potential = "Low"

        session_group_values: List[float] = []
        session_chrono_avg_values: List[float] = []
        for session in sessions:
            group_value = self._safe_float(session.get("group_size_mm"))
            if group_value is not None:
                session_group_values.append(group_value)
            chrono_stats = self._session_analysis_stats(session)
            chrono_avg = chrono_stats.get("avg")
            if chrono_avg is not None:
                session_chrono_avg_values.append(chrono_avg)

        if groups:
            best_group = min(groups)
            avg_group = mean(groups)
            score += max(0.0, 100.0 - avg_group * 2.0)
            confidence += min(30.0, len(groups) * 4.0)
            if best_group <= 10:
                strengths.append("You have a clearly strong node in the group data.")
            elif best_group <= 20:
                strengths.append("There is at least one promising load to build on.")
            else:
                watchouts.append(
                    "The groups are still fairly open, so the load needs more tuning."
                )

            group_trend = self._series_change(groups, lower_is_better=True)
            if group_trend["direction"] == "improving":
                trend_summary = "The groups are trending in the right direction."
                strengths.append(
                    "Development looks stable or improving between test sessions."
                )
            elif group_trend["direction"] == "worsening":
                trend_summary = "The groups are opening up in the latest sessions."
                watchouts.append("The groups vary noticeably between sessions.")
            else:
                trend_summary = "The groups look consistent between sessions."
        else:
            watchouts.append("There is no recorded group data for this batch yet.")

        if chrono.get("count"):
            count = int(chrono["count"] or 0)
            es = chrono.get("es") or 0.0
            sd = chrono.get("sd") or 0.0
            confidence += min(25.0, count * 1.5)

            if count >= 5 and sd <= 12:
                strengths.append("Chronograph data looks consistent.")
            elif count >= 5 and sd > 20:
                watchouts.append(
                    "Velocity spread is high and should be tightened before further optimization."
                )

            if es <= 20 and count >= 5:
                strengths.append(
                    "Extreme spread is low enough that the load appears predictable."
                )
            elif es > 40:
                watchouts.append(
                    "Extreme spread is high enough to indicate that multiple variables are in play."
                )

        chrono_trend = self._series_change(
            session_chrono_avg_values, lower_is_better=False
        )
        if len(session_chrono_avg_values) >= 2:
            if chrono_trend["direction"] == "improving":
                trend_summary = (
                    f"{trend_summary} Velocity is also stable between sessions."
                    if trend_summary
                    else "Velocity is stable between sessions."
                )
            elif chrono_trend["direction"] == "worsening":
                watchouts.append(
                    "The chronograph average is shifting more than desired between sessions."
                )

        spread_signal = self._spread_learning_signal(
            groups=groups,
            chrono=chrono,
            group_trend=(
                self._series_change(groups, lower_is_better=True) if groups else {}
            ),
            note_flags=note_flags,
            max_wind_mps=max_wind_mps,
            pattern=pattern_metrics,
        )
        spread_hint = str(spread_signal.get("hint") or "insufficient_evidence")
        # If per-session engine hints are available, let the most blocking one
        # override the batch-level raw-data computation. The engine's per-session
        # signal is always more specific (it has the full session runtime context);
        # the batch-level fallback is kept for sessions without a linked load record.
        aggregated_hint = self._aggregate_session_hints(sessions)
        if aggregated_hint and self._HINT_PRIORITY.get(
            aggregated_hint, 99
        ) < self._HINT_PRIORITY.get(spread_hint, 99):
            spread_hint = aggregated_hint
        spread_reason = str(spread_signal.get("reason") or "").strip()
        spread_watchouts = [
            str(item).strip()
            for item in (spread_signal.get("watchouts") or [])
            if str(item).strip()
        ]
        spread_control_plan = self._spread_control_plan(spread_hint)
        spread_decision = self._spread_decision_state(
            spread_hint,
            groups=groups,
            chrono=chrono,
            confidence=str(spread_signal.get("confidence") or "low"),
        )
        spread_profile_guidance = self._spread_profile_guidance(spread_hint, usage_goal)
        spread_evidence_quality = self._spread_evidence_quality(
            groups=groups,
            chrono=chrono,
            note_flags=note_flags,
            pattern=pattern_metrics,
            max_wind_mps=max_wind_mps,
            attachment_count=len(self.attachments),
        )
        spread_learning_explanation = self._spread_learning_explanation(
            spread_hint,
            usage_goal=usage_goal,
            evidence_quality=spread_evidence_quality,
            pattern=pattern_metrics,
        )
        spread_capture_checklist = self._spread_capture_checklist(
            spread_hint,
            usage_goal=usage_goal,
            evidence_quality=spread_evidence_quality,
            note_flags=note_flags,
            pattern=pattern_metrics,
        )
        spread_validation_status = self._spread_validation_status(
            spread_hint,
            usage_goal=usage_goal,
            decision=spread_decision,
            evidence_quality=spread_evidence_quality,
            pattern=pattern_metrics,
            note_flags=note_flags,
        )
        watchouts.extend(item for item in spread_watchouts if item not in watchouts)

        if "pressure" in note_flags:
            watchouts.append(
                "The notes mention pressure signs, so further work should stay conservative."
            )
            next_steps.append(
                "Consider testing more cautiously with focus on safety margin and case prep."
            )
            next_focus = "Safety margin and lower powder spread"

        if spread_hint == "possible_shooter_or_setup_signal":
            next_steps.append(
                "Repeat one controlled group before rejecting the load; keep support, position, rhythm, and aiming process consistent."
            )
            next_focus = next_focus or "Controlled repeatability check"
        elif spread_hint == "ammo_or_process_signal":
            next_steps.append(
                "Run a control series with the same setup and inspect loading process variables before changing several things at once."
            )
            next_focus = next_focus or "Ammo/process control series"
        elif spread_hint == "setup_drift_watch":
            next_steps.append(
                "Confirm torque, optic, barrel condition, and environmental changes before treating the group drift as a load failure."
            )
            next_focus = next_focus or "Setup and drift confirmation"
        elif spread_hint == "environment_or_condition_signal":
            next_steps.append(
                "Repeat or compare the load in calmer, known conditions before changing charge or seating based on the group."
            )
            next_focus = next_focus or "Environment-controlled repeat"
        elif spread_hint == "node_or_barrel_timing_signal":
            next_steps.append(
                "Repeat the same load with careful tracking and point of aim, then test a small seating-depth bracket if vertical pattern remains."
            )
            next_focus = next_focus or "Seating depth and barrel timing check"
        elif spread_hint == "insufficient_evidence":
            next_steps.append(
                "Capture matched chrono and group data before making a hard call on the load."
            )
            next_focus = next_focus or "Collect matched evidence"

        if groups:
            avg_group = mean(groups)
            if avg_group > 15:
                next_steps.append(
                    "Try small seating-depth adjustments to find a clearer node."
                )
                next_focus = next_focus or "Seating depth and node refinement"
            else:
                next_steps.append(
                    "Keep the load near the current level and confirm it with a new test series."
                )
                next_focus = next_focus or "Confirm the current load"

        if chrono.get("sd") is not None:
            sd = chrono["sd"] or 0.0
            if sd > 18:
                next_steps.append(
                    "Look more closely at neck tension and more uniform powder charges."
                )
                next_focus = next_focus or "Neck tension and powder uniformity"
            elif sd <= 10 and groups:
                next_steps.append(
                    "The chrono is stable enough that seating depth and node tuning may offer the biggest gain."
                )
                next_focus = next_focus or "Seating depth and node tuning"

        if len(self.attachments) > 0:
            strengths.append(
                f"{len(self.attachments)} image attachments are stored with the batch."
            )
            confidence += min(10.0, len(self.attachments) * 2.0)

        if not next_steps:
            next_steps.append(
                "Keep logging data in the same batch and compare it with the previous session."
            )
        control_action = str(spread_control_plan.get("primary_action") or "").strip()
        if control_action and control_action not in next_steps:
            next_steps.append(control_action)
        decision_label = str(spread_decision.get("label") or "").strip()
        decision_rationale = str(spread_decision.get("rationale") or "").strip()
        if decision_label and decision_rationale:
            decision_step = f"Decision gate: {decision_label}. {decision_rationale}"
            if decision_step not in next_steps:
                next_steps.append(decision_step)
        profile_action = str(
            spread_profile_guidance.get("recommended_check") or ""
        ).strip()
        if profile_action and profile_action not in next_steps:
            next_steps.append(profile_action)
        for logging_action in spread_evidence_quality.get("recommended_logging") or []:
            if logging_action not in next_steps:
                next_steps.append(logging_action)
        learning_takeaway = str(
            spread_learning_explanation.get("user_takeaway") or ""
        ).strip()
        if learning_takeaway and learning_takeaway not in next_steps:
            next_steps.append(learning_takeaway)
        validation_label = str(spread_validation_status.get("label") or "").strip()
        validation_summary = str(spread_validation_status.get("summary") or "").strip()
        validation_next_gate = str(
            spread_validation_status.get("next_gate") or ""
        ).strip()
        validation_status = str(spread_validation_status.get("status") or "").strip()
        validation_ready_now = spread_validation_status.get("ready_now") is True
        if validation_label and validation_summary:
            validation_step = (
                f"Validation status: {validation_label}. {validation_summary}"
            )
            if validation_step not in next_steps:
                next_steps.append(validation_step)
        if validation_next_gate and validation_next_gate not in next_steps:
            next_steps.append(validation_next_gate)
        if validation_label and not validation_ready_now:
            validation_watchout = (
                f"Validation is still provisional: {validation_label.lower()}."
            )
            if validation_watchout not in watchouts:
                watchouts.append(validation_watchout)
        for checklist_item in spread_capture_checklist.get("items") or []:
            label = str(checklist_item.get("label") or "").strip()
            why = str(checklist_item.get("why") or "").strip()
            if label:
                checklist_step = f"Capture: {label}."
                if why:
                    checklist_step += f" {why}"
                if checklist_step not in next_steps:
                    next_steps.append(checklist_step)
        # Inject canonical engine recommendations when available — the engine has full
        # load-session context (charge, seating, lot, pressure) that batch-level spread
        # analysis cannot see. Engine items go first so the UI surfaces the most specific
        # action before generic spread guidance.
        engine_node_fit = ""
        if self.engine_result:
            decisions = (
                self.engine_result.get("decisions")
                if isinstance(self.engine_result.get("decisions"), dict)
                else {}
            )
            engine_stack = (
                decisions.get("recommendation_stack")
                if isinstance(decisions.get("recommendation_stack"), list)
                else []
            )
            engine_next = (
                decisions.get("next_test")
                if isinstance(decisions.get("next_test"), dict)
                else {}
            )
            safety = (
                self.engine_result.get("safety")
                if isinstance(self.engine_result.get("safety"), dict)
                else {}
            )
            candidate = (
                self.engine_result.get("candidate_profile")
                if isinstance(self.engine_result.get("candidate_profile"), dict)
                else {}
            )
            engine_action = str(engine_next.get("recommended_action") or "").strip()
            engine_blocked = bool(safety.get("blocked"))
            engine_node_fit = str(candidate.get("node_fit") or "").strip()
            # Prepend engine recommendation_stack items first — they have load-session
            # context (charge, seating, lot) that spread-only analysis cannot see.
            if engine_stack:
                engine_steps = []
                for item in engine_stack[:3]:
                    reason = str(item.get("reason") or "").strip()
                    area = str(item.get("area") or "").strip()
                    if reason:
                        label = (
                            f"Engine ({area}): {reason}"
                            if area
                            else f"Engine: {reason}"
                        )
                        if label not in next_steps:
                            engine_steps.append(label)
                next_steps = engine_steps + next_steps
            # Safety override always goes first, after stack injection.
            if engine_blocked:
                pressure_summary = safety.get("pressure_summary") or {}
                safety_msg = str(
                    (
                        pressure_summary.get("summary")
                        if isinstance(pressure_summary, dict)
                        else None
                    )
                    or "Safety signals are active — stay conservative."
                ).strip()
                safety_step = f"Safety: {safety_msg}"
                if safety_step not in next_steps:
                    next_steps.insert(0, safety_step)
            # Engine next_test action is more specific than spread-only next_focus.
            if engine_action:
                next_focus = engine_action

        if not next_focus:
            next_focus = "Continue logging and confirm the trend"

        if groups:
            avg_group = mean(groups)
            target_group = self._safe_float(self.batch.get("target_group_mm"))
            if target_group and target_group > 0:
                gap = avg_group - target_group
                if gap <= 0:
                    improvement_potential = "Low"
                elif gap <= target_group * 0.25:
                    improvement_potential = "Moderate"
                else:
                    improvement_potential = "High"
            else:
                if avg_group <= 10:
                    improvement_potential = "Low"
                elif avg_group <= 20:
                    improvement_potential = "Moderate"
                else:
                    improvement_potential = "High"
        elif chrono.get("count"):
            sd = chrono.get("sd") or 0.0
            improvement_potential = "Moderate" if sd > 12 else "Low"

        confidence = max(0.0, min(100.0, confidence))

        metrics = {
            "group_samples": len(groups),
            "group_best_mm": min(groups) if groups else None,
            "group_avg_mm": mean(groups) if groups else None,
            "group_trend": (
                self._series_change(groups, lower_is_better=True) if groups else {}
            ),
            "chrono_session_samples": len(session_chrono_avg_values),
            "chrono_trend": chrono_trend if session_chrono_avg_values else {},
            "chrono_count": int(chrono.get("count") or 0),
            "chrono_avg": chrono.get("avg"),
            "chrono_es": chrono.get("es"),
            "chrono_sd": chrono.get("sd"),
            "confidence": confidence,
            "improvement_potential": improvement_potential,
            "next_focus": next_focus,
            "spread_signal_hint": spread_hint,
            "spread_confidence": spread_signal.get("confidence") or "low",
            "spread_reason": spread_reason,
            "spread_watchouts": spread_watchouts,
            "spread_control_plan": spread_control_plan,
            "spread_control_priority": spread_control_plan.get("priority"),
            "spread_control_title": spread_control_plan.get("title"),
            "spread_decision": spread_decision,
            "spread_decision_state": spread_decision.get("state"),
            "spread_can_optimize": spread_decision.get("can_optimize"),
            "spread_can_reject_load": spread_decision.get("can_reject_load"),
            "spread_can_accept_load": spread_decision.get("can_accept_load"),
            "spread_usage_goal": usage_goal,
            "spread_profile_guidance": spread_profile_guidance,
            "spread_evidence_quality": spread_evidence_quality,
            "spread_evidence_quality_level": spread_evidence_quality.get("level"),
            "spread_evidence_quality_score": spread_evidence_quality.get("score"),
            "spread_learning_explanation": spread_learning_explanation,
            "spread_capture_checklist": spread_capture_checklist,
            "spread_validation_status": spread_validation_status,
            "spread_validation_state": validation_status,
            "spread_validation_label": spread_validation_status.get("label"),
            "spread_validation_ready_now": spread_validation_status.get("ready_now"),
            "spread_validation_readiness_score": spread_validation_status.get(
                "readiness_score"
            ),
            "spread_note_flags": note_flags,
            "spread_max_wind_mps": max_wind_mps,
            "spread_pattern_flags": pattern_metrics.get("flags") or [],
            "spread_vertical_avg_mm": pattern_metrics.get("vertical_avg_mm"),
            "spread_horizontal_avg_mm": pattern_metrics.get("horizontal_avg_mm"),
            "spread_axis_ratio": pattern_metrics.get("axis_ratio"),
            "spread_poi_shift_mm": pattern_metrics.get("poi_shift_mm"),
            "engine_node_fit": engine_node_fit or None,
        }

        summary = (
            f"{batch_name}: {metrics['group_samples']} group sessions, {metrics['chrono_count']} chronograph shots."
            if metrics["group_samples"] or metrics["chrono_count"]
            else f"{batch_name}: no test data yet."
        )
        if setup_label:
            summary += f" Setup: {setup_label}."

        return BatchAnalysis(
            score=round(score, 1),
            confidence=round(confidence, 1),
            summary=summary,
            trend_summary=trend_summary,
            next_focus=next_focus,
            improvement_potential=improvement_potential,
            strengths=strengths,
            watchouts=watchouts,
            next_steps=next_steps,
            metrics=metrics,
        )

    def recommend_next(self) -> Dict[str, Any]:
        """Return a compact recommendation dictionary for the UI."""
        analysis = self.analyze()
        return {
            "score": analysis.score,
            "confidence": analysis.confidence,
            "summary": analysis.summary,
            "trend_summary": analysis.trend_summary,
            "next_focus": analysis.next_focus,
            "improvement_potential": analysis.improvement_potential,
            "strengths": analysis.strengths,
            "watchouts": analysis.watchouts,
            "next_steps": analysis.next_steps,
            "metrics": analysis.metrics,
        }

    def to_html(self) -> str:
        analysis = self.analyze()
        setup_label = self._setup_label()
        strengths = (
            "".join(f"<li>{html.escape(item)}</li>" for item in analysis.strengths)
            or "<li>-</li>"
        )
        watchouts = (
            "".join(f"<li>{html.escape(item)}</li>" for item in analysis.watchouts)
            or "<li>-</li>"
        )
        steps = (
            "".join(f"<li>{html.escape(item)}</li>" for item in analysis.next_steps)
            or "<li>-</li>"
        )
        metrics = json.dumps(analysis.metrics, ensure_ascii=False, indent=2)
        trend = html.escape(analysis.trend_summary or "No clear trend yet.")
        next_focus = html.escape(analysis.next_focus or "Continue logging data.")
        improvement = html.escape(analysis.improvement_potential or "-")
        setup_html = (
            f"<p><b>Setup:</b> {html.escape(setup_label)}</p>" if setup_label else ""
        )
        spread_hint = html.escape(
            str(analysis.metrics.get("spread_signal_hint") or "insufficient_evidence")
        )
        spread_confidence = html.escape(
            str(analysis.metrics.get("spread_confidence") or "low")
        )
        spread_reason = html.escape(
            str(analysis.metrics.get("spread_reason") or "No spread signal yet.")
        )
        spread_validation = analysis.metrics.get("spread_validation_status")
        validation_html = ""
        if isinstance(spread_validation, dict):
            validation_label = html.escape(
                str(spread_validation.get("label") or "Provisional")
            )
            validation_summary = html.escape(
                str(spread_validation.get("summary") or "")
            )
            validation_next_gate = html.escape(
                str(spread_validation.get("next_gate") or "")
            )
            validation_html = f"<p><b>Validation:</b> {validation_label}"
            if validation_summary:
                validation_html += f" - {validation_summary}"
            if validation_next_gate:
                validation_html += f" Next gate: {validation_next_gate}"
            validation_html += "</p>"
        return f"""
        <h3>Batch Analysis</h3>
        {setup_html}
        <p><b>Score:</b> {analysis.score:.1f} | <b>Confidence:</b> {analysis.confidence:.1f}% | <b>Potential:</b> {improvement}</p>
        <p><b>Status:</b> {html.escape(analysis.summary)}</p>
        <p><b>Trend:</b> {trend}</p>
        <p><b>Spread Signal:</b> {spread_hint} ({spread_confidence}) - {spread_reason}</p>
        {validation_html}
        <p><b>Next Focus:</b> {next_focus}</p>
        <h4>Strengths</h4>
        <ul>{strengths}</ul>
        <h4>Watchouts</h4>
        <ul>{watchouts}</ul>
        <h4>Next Steps</h4>
        <ul>{steps}</ul>
        <pre>{metrics}</pre>
        """
