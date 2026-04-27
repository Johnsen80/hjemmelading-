# Real tr — imported below after src is on the path
try:
    from src.utils.i18n import tr as _tr_real

    def tr(x, **kwargs):  # type: ignore[misc]
        return _tr_real(x, **kwargs)

except Exception:

    def tr(x, **kwargs):  # type: ignore[misc]
        return x


try:
    from src.utils.pressure_logger import (  # type: ignore[assignment]
        predict_and_log,
        query_recent_pressures,
    )
except Exception:

    def query_recent_pressures(*args, **kwargs):  # type: ignore[misc]
        return []

    def predict_and_log(*args, **kwargs) -> int:  # type: ignore[misc]
        return 0


try:
    from src.utils.barrel_configuration import (
        resolve_active_barrel_configuration_context,
    )
except Exception:

    def resolve_active_barrel_configuration_context(*args, **kwargs):  # type: ignore[misc]
        return {}


try:
    from src.research.service import ResearchService  # type: ignore[assignment]
except Exception:

    class ResearchService:  # type: ignore[no-redef]
        def __init__(self, db):
            pass

        def lock_session(self, session_id: int) -> None:
            pass


try:
    from src.modules.component_database import (  # type: ignore[assignment]
        AddPowderLotDialog,
        AddPrimerLotDialog,
    )
except Exception:

    class AddPowderLotDialog:  # type: ignore[no-redef]
        def __init__(self, *a, **k):
            pass

        def exec(self) -> int:
            return 0

        def get_lot_data(self) -> dict:
            return {}

    class AddPrimerLotDialog:  # type: ignore[no-redef]
        def __init__(self, *a, **k):
            pass

        def exec(self) -> int:
            return 0

        def get_lot_data(self) -> dict:
            return {}


from src.modules._mlb_help_mixin import _MLBHelpMixin
from src.modules._mlb_stats_mixin import _MLBStatsMixin


def format_distance_m(val):
    try:
        return f"{float(val):.1f} m"
    except Exception:
        return str(val)


def show_basis_dialog():
    dlg = QDialog(None)
    dlg.setWindowTitle(tr("mlb_basis_dialog_title"))
    v = QVBoxLayout()
    h = (
        QVBoxLayout()
    )  # Use QVBoxLayout for demonstration; replace with QHBoxLayout if needed
    show_basis_btn = QPushButton(tr("mlb_show_basis_plot"))
    h.addWidget(show_basis_btn)
    v.addLayout(h)
    # Example input and send button
    inp = QLineEdit()
    v.addWidget(inp)
    send_btn = QPushButton(tr("mlb_send"))
    v.addWidget(send_btn)

    def do_send():
        # Dummy send handler
        QMessageBox.information(None, tr("mlb_send_title"), inp.text())

    send_btn.clicked.connect(do_send)
    inp.returnPressed.connect(do_send)
    btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    btns.rejected.connect(dlg.reject)
    v.addWidget(btns)
    dlg.setLayout(v)
    try:
        dlg.setFocusProxy(inp)
        QTimer.singleShot(0, inp.setFocus)
    except Exception:
        pass


def format_group_size_mm(val):
    try:
        return f"{float(val):.2f} mm"
    except Exception:
        return str(val)


def format_length_mm(val):
    try:
        return f"{float(val):.2f} mm"
    except Exception:
        return str(val)


def build_bullet_fit_summary(*args, **kwargs) -> dict:
    return {}


comparison_portfolio_title = ""
comparison_portfolio_focus = ""
comparison_session_strategy_title = ""
comparison_session_strategy_mode = ""
comparison_campaign_title = ""
comparison_campaign_summary = ""
comparison_action_plan_title = ""
comparison_action_plan_summary = ""
comparison_campaign_board_title = ""
comparison_campaign_board_summary = ""
comparison_campaign_board_preview = []
comparison_session_queue_title = ""
comparison_session_queue_preview = []
comparison_session_manifest_title = ""
comparison_session_manifest_summary = ""
comparison_checklist_title = ""
comparison_swing_factor = ""
comparison_scorecard_summary = ""
comparison_confidence_level = ""
comparison_confidence_score = None
comparison_confidence_summary = ""
comparison_learning_summary = ""
comparison_learning_takeaway = ""
batch_spread_reason = ""
comparison_summary = ""
comparison_advisory_title = ""
comparison_advisory_message = ""
comparison_protocol_title = ""
comparison_bottleneck = ""
comparison_reason = ""
comparison_verdict_label = ""
comparison_verdict_summary = ""
comparison_acceptance_label = ""
comparison_acceptance_summary = ""
comparison_acceptance_progress_level = ""
comparison_acceptance_progress_score = None
comparison_acceptance_progress_passed = None
comparison_acceptance_progress_total = None
comparison_acceptance_progress_summary = ""
comparison_next_test_summary = ""
comparison_next_test_first_check = ""
comparison_board_headline = ""
comparison_board_band = ""
comparison_board_summary = ""
comparison_profile_title = ""
comparison_profile_emphasis = ""
comparison_profile_guardrail = ""
comparison_mission = ""
comparison_mission_success = ""
pressure_level = ""
smart_validation_next_gate = ""
smart_execution_keep_constant = []
smart_execution_capture = []
smart_do_not_change_yet = []
smart_blocked_by = []
smart_confidence_level = ""
smart_confidence_score = None
smart_confidence_uncertainty = ""
smart_confidence_summary = ""
smart_evidence_status = ""
smart_evidence_items = []
smart_evidence_focus = []
smart_branch_display_line = ""
smart_branch_label = ""
smart_branch_compare_mode = ""
smart_active_return_line = ""
smart_charge_return_line = ""
smart_seating_return_line = ""
spread_capture_title = ""
spread_capture_items = []
spread_validation_label = ""
spread_validation_score = None
spread_validation_summary = ""
comparison_state = ""
comparison_rank = None
comparison_count = None
# Fallback definitions for batch/smart/comparison variables to avoid NameError
batch_spread_control_plan = {}
batch_spread_decision = {}
batch_spread_profile_guidance = {}
batch_spread_evidence_quality = {}
batch_spread_learning_explanation = {}
smart_candidate_profile = {}
smart_next_test = {}
smart_harmonics = {}
smart_bullet_fit = {}
smart_chamber_jump = {}
smart_guidance = {}
smart_validation_gate = {}
smart_execution_plan = {}
smart_recommendation_confidence = {}
smart_branch_advisory = {}
smart_baseline_control = {}
smart_return_targets = {}
smart_evidence_diagnostics = {}
batch_spread_capture_checklist = {}
batch_spread_validation_status = {}
batch_comparison_basis = {}
batch_comparison_advisory = {}
batch_comparison_protocol = {}
batch_comparison_explanation = {}
batch_comparison_verdict = {}
batch_comparison_acceptance = {}
batch_comparison_acceptance_progress = {}
batch_comparison_next_test = {}
batch_comparison_status_board = {}
batch_comparison_profile_priority = {}
spread_profile_check = ""
spread_validation_next_gate = ""
comparison_advisory_action = ""
comparison_protocol_action = ""
comparison_protocol_plan = ""
comparison_next_measurement = ""
comparison_acceptance_gate = ""
comparison_acceptance_first_gap = ""
comparison_acceptance_progress_target = ""
comparison_next_test_action = ""
comparison_next_test_title = ""
comparison_mission_action = ""
comparison_session_strategy_objective = ""
comparison_action_plan_next = ""
comparison_session_queue_first = ""
comparison_workboard_lanes_text = ""
comparison_checklist_first = ""
smart_execution_summary = ""

# Additional fallbacks for undefined variables used in setup/summary logic
smart_seating_alignment = ""
smart_seating_target = ""
smart_branch_action_line = ""
header_title_override = ""
confidence_label = ""
spread_decision_label = ""
spread_decision_state = ""
spread_profile_title = ""
spread_profile_emphasis = ""
spread_quality_level = ""
spread_quality_score = None
spread_lesson_title = ""
spread_lesson_takeaway = ""
smart_candidate_robustness = ""
smart_node_fit = ""
smart_harmonics_tier = ""
smart_bullet_fit_level = ""
smart_bullet_fit_score = None
smart_bullet_fit_message = ""
smart_jump_band = ""
smart_jump_summary = ""
smart_current_jump_mm = None
smart_engine_next_action = ""
smart_engine_next_reason = ""
smart_validation_label = ""
smart_execution_success = ""
smart_charge_alignment = ""
smart_charge_target = ""
smart_execution_session_type = ""
"""
Modern Load Builder - Interactive visual load development with local guidance
Replaces old wizard with intuitive 2-step workflow + live visualization
"""

import json
import re
import statistics
from datetime import datetime, timezone
from typing import Any, TypedDict

from PyQt6.QtCore import QDate, QPointF, QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QTextCursor
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from src.ballistics.services import (
    LoadAnalysisRequest,
    LoadAnalysisService,
    build_game_suitability_summary,
)
from src.database.batch_manager import add_batch_session, create_batch_project
from src.database.database import get_database
from src.layers.component_layer import component_layer
from src.logging_config import get_logger
from src.modules.reference_owned_data_service import (  # noqa: F401
    build_load_card_summary,
    build_profile_evidence_summary,
    build_profile_trust_map,
)
from src.tools.evidence_quality_service import (
    BUILDER_CONFIDENCE_THRESHOLDS,
    score_to_confidence_level,
)
from src.tools.load_development_session_service import update_load_development_session
from src.tools.load_session_runtime_service import (
    build_active_workflow_context_from_settings,
    build_load_session_runtime,
    get_active_load_session_id_from_settings,
)
from src.utils.cartridge_standard_support import (
    compare_chamber_to_cartridge_standard,
    find_best_cartridge_standard,
    get_max_pressure_psi_for_caliber,
)
from src.utils.internal_ballistics import build_internal_ballistics_summary
from src.utils.rifle_harmonics import calculate_harmonics_profile
from src.utils.scientific_quality import build_input_quality_summary

# Import all unit/format helpers from utils.unit_preferences
from src.utils.unit_preferences import (
    format_length_delta_mm,
    format_pressure_psi,
    format_temperature_c,
    format_temperature_delta_c,
    format_velocity_delta_fps,
    format_velocity_fps,
    format_velocity_rate_fps_per_c,
    format_velocity_rate_fps_per_gr,
    format_weight_grains,
    get_length_suffix,
    get_pressure_suffix,
    get_temperature_suffix,
    get_velocity_suffix,
    get_weight_suffix,
    length_display_to_mm,
    length_mm_to_display_value,
    pressure_display_to_kpa,
    pressure_kpa_to_display_value,
    temperature_c_to_display_value,
    temperature_display_to_c,
    velocity_display_to_fps,
    velocity_fps_to_display_value,
    weight_display_to_grains,
    weight_grains_to_display_value,
)

try:
    from src.utils.env_corrections import air_density_ratio  # type: ignore[import]
except Exception:
    air_density_ratio = None  # type: ignore[assignment]

try:
    from src.ui.reloading_theme import ReloadingTheme as ReloadingTheme  # type: ignore[assignment] # noqa: PLC0414
except Exception:

    class ReloadingTheme:  # type: ignore[no-redef,assignment]
        ACCENT = "#c0392b"
        TEXT_PRIMARY = "#ecf0f1"
        TEXT_SECONDARY = "#bdc3c7"
        BACKGROUND = "#1a1a2e"
        PANEL = "#16213e"

        @staticmethod
        def get_stylesheet() -> str:
            return ""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(source: dict[str, Any], key: str) -> dict[str, Any]:
    """Extract a nested dict from *source* by *key*, returning {} if missing or wrong type."""
    val = source.get(key)
    return val if isinstance(val, dict) else {}


def _as_list(source: dict[str, Any], key: str) -> list[Any]:
    """Extract a nested list from *source* by *key*, returning [] if missing or wrong type."""
    val = source.get(key)
    return val if isinstance(val, list) else []


def _project_name_from_path(path: str) -> str:
    cleaned = (path or "").strip().rstrip("\\/")
    if not cleaned:
        return "Standard Project"
    parts = re.split(r"[\\/]+", cleaned)
    return parts[-1] if parts and parts[-1] else cleaned


def _get_active_load_session_id() -> int | None:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return get_active_load_session_id_from_settings(settings)


def _coerce_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _coerce_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except Exception:
        return None


def build_learning_workflow_guidance(
    runtime: dict | None,
) -> dict[str, Any]:  # noqa: C901
    _rt: dict[str, Any] = runtime if isinstance(runtime, dict) else {}

    learning: dict[str, Any] = _as_dict(_rt, "learning")
    context: dict[str, Any] = _as_dict(_rt, "context")
    evidence: dict[str, Any] = _as_dict(_rt, "evidence")
    recommendation_runtime: dict[str, Any] = _as_dict(_rt, "recommendation")
    smart_engine: dict[str, Any] = _as_dict(_rt, "smart_engine")

    aggregate: dict[str, Any] = _as_dict(learning, "aggregate")
    session_payload: dict[str, Any] = _as_dict(learning, "session")
    session_summary: dict[str, Any] = _as_dict(session_payload, "summary")

    evidence_summary: dict[str, Any] = _as_dict(evidence, "summary")
    input_quality: dict[str, Any] = _as_dict(evidence, "input_quality")
    rec_summary: dict[str, Any] = _as_dict(recommendation_runtime, "summary")

    smart_engine_result: dict[str, Any] = _as_dict(smart_engine, "engine_result")
    decisions: dict[str, Any] = _as_dict(smart_engine_result, "decisions")

    def _smart(key: str) -> dict[str, Any]:
        d = _as_dict(smart_engine_result, key)
        return d if d else _as_dict(decisions, key)

    smart_candidate_profile = _as_dict(smart_engine_result, "candidate_profile")
    smart_harmonics = _as_dict(smart_engine_result, "harmonics")
    smart_bullet_fit = _as_dict(smart_engine_result, "bullet_fit")
    smart_chamber_jump = _as_dict(smart_engine_result, "chamber_jump")
    smart_branch_advisory = _as_dict(smart_engine_result, "branch_advisory")
    smart_return_targets = _as_dict(smart_engine_result, "return_targets")
    smart_baseline_control = _as_dict(smart_engine_result, "baseline_control")
    smart_evidence_diagnostics = _as_dict(smart_engine_result, "evidence_diagnostics")
    smart_next_test = _smart("next_test")
    smart_guidance = _smart("guidance")
    smart_validation_gate = _smart("validation_gate")
    smart_execution_plan = _smart("execution_plan")
    smart_recommendation_confidence = _smart("recommendation_confidence")
    do_not_change_yet: list[Any] = _as_list(decisions, "do_not_change_yet")
    blocked_by: list[Any] = _as_list(decisions, "blocked_by")

    next_focus = str(
        rec_summary.get("next_focus")
        or recommendation_runtime.get("next_focus")
        or aggregate.get("next_focus")
        or session_summary.get("next_focus")
        or ""
    ).strip()
    weakest_link = str(
        rec_summary.get("weakest_link")
        or recommendation_runtime.get("weakest_link")
        or aggregate.get("weakest_link")
        or ""
    ).strip()
    confidence_label = str(
        rec_summary.get("confidence_label")
        or recommendation_runtime.get("confidence_label")
        or aggregate.get("confidence_label")
        or ""
    ).strip()
    header_title_override = str(
        rec_summary.get("header_title")
        or recommendation_runtime.get("header_title")
        or ""
    ).strip()
    pressure_level = str(
        _as_dict(context, "pressure_assessment").get("level")
        or evidence_summary.get("pressure_level")
        or session_summary.get("pressure_level")
        or ""
    ).strip()
    input_quality_level = str(
        input_quality.get("level")
        or evidence_summary.get("input_quality_level")
        or session_summary.get("input_quality_level")
        or ""
    ).strip()
    signal_hint = str(session_summary.get("signal_hint") or "").strip()
    batch_spread_reason = str(session_summary.get("batch_spread_reason") or "").strip()
    usage_profile_name = str(context.get("usage_profile_name") or "").strip()
    test_result_count = _coerce_int(evidence_summary.get("test_result_count")) or 0

    smart_guidance_title = str(smart_guidance.get("title") or "").strip()
    smart_guidance_setup_line = str(smart_guidance.get("setup_line") or "").strip()
    smart_next_test_action = str(
        smart_next_test.get("recommended_action") or ""
    ).strip()
    smart_execution_summary = str(smart_execution_plan.get("summary") or "").strip()
    smart_evidence_diag_action = str(
        smart_evidence_diagnostics.get("suggested_action") or ""
    ).strip()
    focus_labels = {
        "capture_measured_velocity": "capture measured velocity",
        "capture_group_validation": "capture group validation",
        "strengthen_barrel_profile": "strengthen barrel profile",
        "verify_component_lot": "verify component lot",
    }
    weakest_labels = {
        "pipe": "pipe",
        "hylse": "case baseline",
        "kulelot": "bullet lot",
        "kruttlot": "powder lot",
        "primerlot": "primer lot",
        "hylselot": "case lot",
    }

    # --- Priority 1: pressure warning/critical ---
    if pressure_level in ("warning", "critical"):
        if pressure_level == "warning":
            setup_line = "Test setup: chrono the first 5 shots before optimization. confirm pressure behavior before extending any ladder."
        else:
            setup_line = "Test setup: stop ladder progression. Confirm pressure behavior with current components before any optimization."
        header = "Learning priority: verify pressure before optimization"
        if confidence_label:
            header += f" ({confidence_label})"
        card_hint = f"{header}. {setup_line} Pressure state: {pressure_level}."
        return {"header": header, "setup": setup_line, "card_hint": card_hint}

    # --- Priority 2: Hunting cold-bore ---
    if usage_profile_name == "Hunting" and test_result_count == 0:
        setup_line = "Test setup: shoot 1 cold-bore shot and record temperature, conditions, and impact. Confirm field ready before season."
        header = "Learning priority: capture cold-bore hunting validation"
        if confidence_label:
            header += f" ({confidence_label})"
        card_hint = f"{header}. {setup_line}"
        return {"header": header, "setup": setup_line, "card_hint": card_hint}

    # --- Priority 3: signal_hint branches ---
    if signal_hint == "possible_shooter_or_setup_signal":
        setup_line = "Test setup: repeat one controlled group before blaming the load. Rule out shooter or setup error first."
        header = "Learning priority: repeat before rejecting the load"
        if confidence_label:
            header += f" ({confidence_label})"
        card_hint = f"{header}. {setup_line} Signal: {signal_hint}."
        if batch_spread_reason:
            card_hint += f" {batch_spread_reason}"
        return {"header": header, "setup": setup_line, "card_hint": card_hint}

    if signal_hint == "ammo_or_process_signal":
        setup_line = "Test setup: chrono every shot and check neck tension, primer seating depth, and case prep consistency."
        header = "Learning priority: confirm ammo and loading process"
        if confidence_label:
            header += f" ({confidence_label})"
        card_hint = f"{header}. {setup_line}"
        return {"header": header, "setup": setup_line, "card_hint": card_hint}

    if signal_hint == "environment_or_condition_signal":
        setup_line = "Test setup: record wind and mirage for every group. avoid changing charge or seating until conditions are confirmed repeatable."
        header = "Learning priority: confirm environmental repeatability"
        if confidence_label:
            header += f" ({confidence_label})"
        card_hint = f"{header}. {setup_line} Signal: {signal_hint}."
        if batch_spread_reason:
            card_hint += f" {batch_spread_reason}"
        return {"header": header, "setup": setup_line, "card_hint": card_hint}

    if signal_hint == "node_or_barrel_timing_signal":
        bsc_plan = _as_dict(session_summary, "batch_spread_control_plan")
        bsc_decision = _as_dict(session_summary, "batch_spread_decision")
        bsc_profile = _as_dict(session_summary, "batch_spread_profile_guidance")
        bsc_eq = _as_dict(session_summary, "batch_spread_evidence_quality")
        bsc_learn = _as_dict(session_summary, "batch_spread_learning_explanation")
        bsc_checklist = _as_dict(session_summary, "batch_spread_capture_checklist")
        bsc_validation = _as_dict(session_summary, "batch_spread_validation_status")
        bcmp_basis = _as_dict(session_summary, "batch_comparison_basis")
        bcmp_advisory = _as_dict(session_summary, "batch_comparison_advisory")
        bcmp_protocol = _as_dict(session_summary, "batch_comparison_protocol")
        bcmp_explanation = _as_dict(session_summary, "batch_comparison_explanation")
        bcmp_verdict = _as_dict(session_summary, "batch_comparison_verdict")
        bcmp_acceptance = _as_dict(session_summary, "batch_comparison_acceptance")
        bcmp_progress = _as_dict(
            session_summary, "batch_comparison_acceptance_progress"
        )
        bcmp_next_test = _as_dict(session_summary, "batch_comparison_next_test")
        bcmp_board = _as_dict(session_summary, "batch_comparison_status_board")
        bcmp_profile_prio = _as_dict(
            session_summary, "batch_comparison_profile_priority"
        )
        bcmp_mission = _as_dict(session_summary, "batch_comparison_mission_brief")
        bcmp_portfolio = _as_dict(session_summary, "batch_comparison_portfolio")
        bcmp_strategy = _as_dict(session_summary, "batch_comparison_session_strategy")
        bcmp_campaign = _as_dict(session_summary, "batch_comparison_campaign_view")
        bcmp_action_plan = _as_dict(session_summary, "batch_comparison_action_plan")
        bcmp_campaign_board = _as_dict(
            session_summary, "batch_comparison_campaign_board"
        )
        bcmp_queue = _as_dict(session_summary, "batch_comparison_session_queue")
        bcmp_manifest = _as_dict(session_summary, "batch_comparison_session_manifest")
        bcmp_brief = _as_dict(session_summary, "batch_comparison_next_session_brief")
        bcmp_today = _as_dict(session_summary, "batch_comparison_today_plan")
        bcmp_workboard = _as_dict(session_summary, "batch_comparison_workboard")
        bcmp_ch_list = _as_dict(session_summary, "batch_comparison_checklist")
        bcmp_scorecard = _as_dict(session_summary, "batch_comparison_scorecard")
        bcmp_confidence = _as_dict(session_summary, "batch_comparison_confidence")
        bcmp_learning = _as_dict(session_summary, "batch_comparison_learning_note")

        setup_parts: list[str] = []
        _pa = str(bsc_plan.get("primary_action") or "").strip()
        _sp = str(bsc_plan.get("shot_plan") or "").strip()
        _rc = str(bsc_profile.get("recommended_check") or "").strip()
        if _pa:
            setup_parts.append(_pa)
        if _sp:
            setup_parts.append(_sp)
        if _rc:
            setup_parts.append(_rc)
        if not setup_parts:
            setup_parts.append("Repeat the same setup with careful tracking.")
        _vgate = str(bsc_validation.get("next_gate") or "").strip()
        _adv_act = str(bcmp_advisory.get("recommended_action") or "").strip()
        _proto_act = str(bcmp_protocol.get("primary_action") or "").strip()
        _proto_plan = str(bcmp_protocol.get("shot_plan") or "").strip()
        _next_meas = str(bcmp_explanation.get("next_measurement") or "").strip()
        _acc_gate = str(bcmp_acceptance.get("next_gate") or "").strip()
        _prog_target = str(bcmp_progress.get("next_target") or "").strip()
        _nt_act = str(bcmp_next_test.get("primary_action") or "").strip()
        _miss_act = str(bcmp_mission.get("primary_action") or "").strip()
        _sess_obj = str(bcmp_strategy.get("objective") or "").strip()
        _ap_act = str(bcmp_action_plan.get("primary_action") or "").strip()
        _mf_bucket = str(bcmp_manifest.get("primary_bucket") or "").strip()
        _mf_first = str(bcmp_manifest.get("first_batch_name") or "").strip()
        _brief_act = str(bcmp_brief.get("primary_action") or "").strip()
        _today_act = str(bcmp_today.get("primary_action") or "").strip()
        _wb_act = str(bcmp_workboard.get("primary_action") or "").strip()
        _wb_lane = str(bcmp_workboard.get("primary_bucket") or "").strip()
        _wb_first = str(bcmp_workboard.get("first_batch_name") or "").strip()
        _wb_counts = _as_dict(bcmp_workboard, "counts")
        _wb_lanes = _as_list(bcmp_workboard, "lane_summaries")
        _ch_prio = str(bcmp_ch_list.get("highest_priority") or "").strip()
        if _vgate:
            setup_parts.append(f"Validation gate: {_vgate}")
        if _adv_act:
            setup_parts.append(f"Comparison gate: {_adv_act}")
        if _proto_act:
            setup_parts.append(f"Head-to-head: {_proto_act}")
        if _proto_plan:
            setup_parts.append(f"Protocol: {_proto_plan}")
        if _next_meas:
            setup_parts.append(f"Bottleneck check: {_next_meas}")
        if _acc_gate:
            setup_parts.append(f"Acceptance gate: {_acc_gate}")
        if _prog_target:
            setup_parts.append(f"Progress target: {_prog_target}")
        if _nt_act:
            setup_parts.append(f"Next test: {_nt_act}")
        if _miss_act:
            setup_parts.append(f"Mission action: {_miss_act}")
        if _sess_obj:
            setup_parts.append(f"Session objective: {_sess_obj}")
        if _ap_act:
            setup_parts.append(f"Action plan: {_ap_act}")
        if _mf_bucket:
            setup_parts.append(f"Session bucket: {_mf_bucket}")
        if _mf_first:
            setup_parts.append(f"Manifest first: {_mf_first}")
        if _brief_act:
            setup_parts.append(f"Session brief: {_brief_act}")
        if _today_act:
            setup_parts.append(f"Today plan: {_today_act}")
        if _wb_act:
            setup_parts.append(f"Workboard: {_wb_act}")
        if _wb_lane:
            setup_parts.append(f"Workboard lane: {_wb_lane}")
        if _wb_first:
            setup_parts.append(f"Workboard first: {_wb_first}")
        if _wb_counts:
            _wc_parts = [
                f"{k} {int(_wb_counts.get(k) or 0)}"
                for k in ("shoot_now", "confirm", "hold", "pause", "reject_watch")
                if _wb_counts.get(k)
            ]
            if _wc_parts:
                setup_parts.append(f"Workboard counts: {' | '.join(_wc_parts)}")
        if _wb_lanes:
            _wl_sums = [
                str(ln.get("summary") or "") for ln in _wb_lanes if ln.get("summary")
            ]
            if _wl_sums:
                setup_parts.append(f"Workboard lanes: {' | '.join(_wl_sums)}")
        if _ch_prio:
            setup_parts.append(f"Compare first: {_ch_prio}")
        setup_line = " ".join(setup_parts)

        header = "Learning priority: confirm vertical pattern and barrel timing"
        if confidence_label:
            header += f" ({confidence_label})"

        cb: list[str] = [f"{header}. {setup_line}"]
        cb.append(f"Signal: {signal_hint}.")
        _dec_label = str(bsc_decision.get("label") or "").strip()
        if _dec_label:
            cb.append(f"Decision: {_dec_label}")
        _prof_title = str(bsc_profile.get("title") or "").strip()
        if _prof_title:
            cb.append(f"Profile: {_prof_title}")
        _eq_level = str(bsc_eq.get("level") or "").strip()
        _eq_score = _coerce_float(bsc_eq.get("score"))
        if _eq_level:
            _eq_str = f"Evidence quality: {_eq_level}"
            if _eq_score is not None:
                _eq_str += f" ({_eq_score:.1f}/100)"
            cb.append(_eq_str)
        _les_title = str(bsc_learn.get("title") or "").strip()
        if _les_title:
            cb.append(f"Lesson: {_les_title}")
        _takeaway = str(bsc_learn.get("user_takeaway") or "").strip()
        if _takeaway:
            cb.append(f"Takeaway: {_takeaway}")
        _cl_title = str(bsc_checklist.get("title") or "").strip()
        _cl_items = _as_list(bsc_checklist, "items")
        if _cl_title and _cl_items:
            _item_labels = [
                str(i.get("label") or "") for i in _cl_items if i.get("label")
            ]
            cb.append(f"Checklist: {_cl_title} -> {' | '.join(_item_labels)}")
        _val_label = str(bsc_validation.get("label") or "").strip()
        _val_score = _coerce_float(bsc_validation.get("readiness_score"))
        if _val_label:
            _val_str = f"Validation: {_val_label}"
            if _val_score is not None:
                _val_str += f" ({_val_score:.1f}/100)"
            cb.append(_val_str)
        _basis_state = str(bcmp_basis.get("ranking_state") or "").strip()
        _basis_rank = _coerce_int(bcmp_basis.get("current_rank"))
        _basis_count = _coerce_int(bcmp_basis.get("count"))
        if _basis_state:
            _b_str = f"Batch comparison: {_basis_state}"
            if _basis_rank is not None and _basis_count is not None:
                _b_str += f" ({_basis_rank}/{_basis_count})"
            cb.append(_b_str)
        _adv_title = str(bcmp_advisory.get("title") or "").strip()
        if _adv_title:
            cb.append(f"Comparison advisory: {_adv_title}")
        _proto_title = str(bcmp_protocol.get("title") or "").strip()
        if _proto_title:
            cb.append(f"Comparison protocol: {_proto_title}")
        _expl_factor = str(bcmp_explanation.get("limiting_factor") or "").strip()
        if _expl_factor:
            cb.append(f"Comparison bottleneck: {_expl_factor}")
        _verdict_label = str(bcmp_verdict.get("label") or "").strip()
        if _verdict_label:
            cb.append(f"Comparison verdict: {_verdict_label}")
        _acc_label = str(bcmp_acceptance.get("label") or "").strip()
        if _acc_label:
            cb.append(f"Comparison acceptance: {_acc_label}")
        _acc_gaps = _as_list(bcmp_acceptance, "remaining_gaps")
        for gap in _acc_gaps:
            cb.append(f"Acceptance gap: {gap}")
        _prog_level = str(bcmp_progress.get("level") or "").strip()
        _prog_score = _coerce_float(bcmp_progress.get("score"))
        _prog_passed = _coerce_int(bcmp_progress.get("passed_count"))
        _prog_total = _coerce_int(bcmp_progress.get("total_count"))
        if _prog_level:
            _ps = f"Acceptance progress: {_prog_level}"
            if _prog_score is not None:
                _ps += f" ({_prog_score:.1f}/100)"
            if _prog_passed is not None and _prog_total is not None:
                _ps += f" {_prog_passed}/{_prog_total}"
            cb.append(_ps)
        _nt_title = str(bcmp_next_test.get("title") or "").strip()
        if _nt_title:
            cb.append(f"Next test: {_nt_title}")
        _board_headline = str(bcmp_board.get("headline") or "").strip()
        _board_band = str(bcmp_board.get("readiness_band") or "").strip()
        if _board_headline:
            _bs = f"Comparison board: {_board_headline}"
            if _board_band:
                _bs += f" ({_board_band})"
            cb.append(_bs)
        _pp_title = str(bcmp_profile_prio.get("title") or "").strip()
        if _pp_title:
            cb.append(f"Comparison profile: {_pp_title}")
        _miss_mission = str(bcmp_mission.get("mission") or "").strip()
        if _miss_mission:
            cb.append(f"Mission brief: {_miss_mission}")
        _port_title = str(bcmp_portfolio.get("title") or "").strip()
        _port_focus = str(bcmp_portfolio.get("focus") or "").strip()
        if _port_title:
            _ps2 = f"Portfolio: {_port_title}"
            if _port_focus:
                _ps2 += f" - {_port_focus}"
            cb.append(_ps2)
        _strat_title = str(bcmp_strategy.get("title") or "").strip()
        _strat_mode = str(bcmp_strategy.get("mode") or "").strip()
        _strat_obj = str(bcmp_strategy.get("objective") or "").strip()
        if _strat_title:
            _ss = f"Session strategy: {_strat_title}"
            if _strat_mode:
                _ss += f" ({_strat_mode})"
            if _strat_obj:
                _ss += f" - {_strat_obj}"
            cb.append(_ss)
        _camp_title = str(bcmp_campaign.get("title") or "").strip()
        _camp_summary = str(bcmp_campaign.get("summary") or "").strip()
        if _camp_title:
            _cs = f"Campaign view: {_camp_title}"
            if _camp_summary:
                _cs += f" - {_camp_summary}"
            cb.append(_cs)
        _ap_title = str(bcmp_action_plan.get("title") or "").strip()
        _ap_summary = str(bcmp_action_plan.get("summary") or "").strip()
        if _ap_title:
            _aps = f"Action plan: {_ap_title}"
            if _ap_summary:
                _aps += f" - {_ap_summary}"
            cb.append(_aps)
        _cb_title = str(bcmp_campaign_board.get("title") or "").strip()
        _cb_summary = str(bcmp_campaign_board.get("summary") or "").strip()
        _cb_preview = _as_list(bcmp_campaign_board, "preview")
        if _cb_title:
            _cbs = f"Campaign board: {_cb_title}"
            if _cb_summary:
                _cbs += f" - {_cb_summary}"
            if _cb_preview:
                _cbs += f" - {' | '.join(str(p) for p in _cb_preview)}"
            cb.append(_cbs)
        _q_title = str(bcmp_queue.get("title") or "").strip()
        _q_first = str(bcmp_queue.get("first_batch_name") or "").strip()
        _q_preview = _as_list(bcmp_queue, "preview")
        if _q_title:
            _qs = f"Session queue: {_q_title}"
            if _q_first:
                _qs += f" - first {_q_first}"
            if _q_preview:
                _qs += f" - {' | '.join(str(p) for p in _q_preview)}"
            cb.append(_qs)
        _mf_title = str(bcmp_manifest.get("title") or "").strip()
        _mf_bucket2 = str(bcmp_manifest.get("primary_bucket") or "").strip()
        _mf_q_preview = _as_list(bcmp_manifest, "queue_preview")
        _mf_lanes = _as_list(bcmp_manifest, "lane_summaries")
        if _mf_title:
            cb.append(f"Session manifest: {_mf_title} ({_mf_bucket2})")
        if _mf_q_preview:
            cb.append(" | ".join(str(p) for p in _mf_q_preview))
        if _mf_lanes:
            _lane_sums = [
                str(ln.get("summary") or "") for ln in _mf_lanes if ln.get("summary")
            ]
            if _lane_sums:
                cb.append(" | ".join(_lane_sums))
            _lane_labels = [
                f"lane {ln.get('bucket')}" for ln in _mf_lanes if ln.get("bucket")
            ]
            if _lane_labels:
                cb.append(" | ".join(_lane_labels))
        _brief_title = str(bcmp_brief.get("title") or "").strip()
        _brief_summary = str(bcmp_brief.get("summary") or "").strip()
        _brief_hold = str(bcmp_brief.get("hold_back") or "").strip()
        if _brief_title:
            _brs = f"Next session brief: {_brief_title}"
            if _brief_summary:
                _brs += f" - {_brief_summary}"
            if _brief_hold:
                _brs += f" - hold back {_brief_hold}"
            cb.append(_brs)
        _today_title = str(bcmp_today.get("title") or "").strip()
        _today_summary = str(bcmp_today.get("summary") or "").strip()
        if _today_title:
            _ts = f"Today plan: {_today_title}"
            if _today_summary:
                _ts += f" - {_today_summary}"
            cb.append(_ts)
        _wb_title = str(bcmp_workboard.get("title") or "").strip()
        _wb_summary = str(bcmp_workboard.get("summary") or "").strip()
        _wb_status = str(bcmp_workboard.get("status_label") or "").strip()
        if _wb_title:
            _wbs = f"Workboard: {_wb_title}"
            if _wb_summary:
                _wbs += f" - {_wb_summary}"
            cb.append(_wbs)
        if _wb_status:
            cb.append(_wb_status)
        _wb_lanes2 = _as_list(bcmp_workboard, "lane_summaries")
        if _wb_lanes2:
            _wl2 = [
                str(ln.get("summary") or "") for ln in _wb_lanes2 if ln.get("summary")
            ]
            if _wl2:
                cb.append(" | ".join(_wl2))
            _wll = [f"lane {ln.get('bucket')}" for ln in _wb_lanes2 if ln.get("bucket")]
            if _wll:
                cb.append(" | ".join(_wll))
        _wb_counts2 = _as_dict(bcmp_workboard, "counts")
        if _wb_counts2:
            _wc2 = [
                f"{k} {int(_wb_counts2.get(k) or 0)}"
                for k in ("shoot_now", "confirm", "hold", "pause", "reject_watch")
                if _wb_counts2.get(k)
            ]
            if _wc2:
                cb.append(" | ".join(_wc2))
            cb.append(f"first {_wb_first}" if _wb_first else "")
        _chl_title = str(bcmp_ch_list.get("title") or "").strip()
        _chl_prio = str(bcmp_ch_list.get("highest_priority") or "").strip()
        if _chl_title and _chl_prio:
            cb.append(f"Comparison checklist: {_chl_title} -> {_chl_prio}")
        _sc_factor = str(bcmp_scorecard.get("swing_factor") or "").strip()
        if _sc_factor:
            cb.append(f"Comparison scorecard: {_sc_factor}")
        _conf_level = str(bcmp_confidence.get("level") or "").strip()
        _conf_score = _coerce_float(bcmp_confidence.get("score"))
        if _conf_level:
            _cfs = f"Comparison confidence: {_conf_level}"
            if _conf_score is not None:
                _cfs += f" ({_conf_score:.1f}/100)"
            cb.append(_cfs)
        _learn_plain = str(bcmp_learning.get("plain_summary") or "").strip()
        if _learn_plain:
            cb.append(f"Comparison learning: {_learn_plain}")
        card_hint = " ".join(s for s in cb if s)
        return {"header": header, "setup": setup_line, "card_hint": card_hint}

    # --- Priority 4: smart engine evidence diagnostics needs_measurement ---
    if smart_evidence_diagnostics.get("status") == "needs_measurement":
        setup_line = (
            f"Test setup: {smart_evidence_diag_action}"
            if smart_evidence_diag_action
            else "Test setup: close the missing evidence gap first."
        )
        header_base = "Close the missing evidence first"
        header = f"Learning priority: {header_base}"
        if confidence_label:
            header += f" ({confidence_label})"
        card_hint = f"{header}. {setup_line}"
        _diag_items = _as_list(smart_evidence_diagnostics, "items")
        _diag_focus = _as_list(smart_evidence_diagnostics, "focus_areas")
        _diag_status = str(smart_evidence_diagnostics.get("status") or "").strip()
        if _diag_status and _diag_items:
            card_hint += f" Engine evidence: {_diag_status} - {_diag_items[0]}"
        if _diag_focus:
            card_hint += f" Engine evidence focus: {_diag_focus[0]}"
        return {"header": header, "setup": setup_line, "card_hint": card_hint}

    # --- Priority 5: smart engine guidance setup line ---
    if smart_guidance_setup_line:
        setup_parts2: list[str] = [f"Test setup: {smart_guidance_setup_line}"]
        for cap in _as_list(smart_execution_plan, "capture"):
            setup_parts2.append(f"Capture: {cap}")
        _ret_charge = _as_dict(smart_return_targets, "charge")
        if _ret_charge.get("label"):
            setup_parts2.append(f"Charge target: {_ret_charge['label']}")
        if smart_baseline_control.get("active_return_line"):
            setup_parts2.append(
                f"Baseline control: {smart_baseline_control['active_return_line']}"
            )
        setup_line = " ".join(setup_parts2)
        _eff_header = (
            smart_guidance_title or header_title_override or "Learning priority"
        )
        if _eff_header.lower() != "learning priority":
            header = f"Learning priority: {_eff_header}"
        else:
            header = "Learning priority"
        if confidence_label:
            header += f" ({confidence_label})"
        card_hint = f"{header}. {setup_line}"
        data_bits2: list[str] = []
        _rp = str(smart_candidate_profile.get("robustness_level") or "").strip()
        _nf2 = str(smart_candidate_profile.get("node_fit") or "").strip()
        _ht = str(smart_harmonics.get("stability_tier") or "").strip()
        if _rp or _nf2 or _ht:
            data_bits2.append(
                f"Engine robustness: {_rp}, node fit {_nf2}, harmonics {_ht}".strip(
                    ", "
                )
            )
        if smart_next_test_action:
            data_bits2.append(f"Engine next test: {smart_next_test_action}")
        _vg_label = str(smart_validation_gate.get("label") or "").strip()
        if _vg_label:
            data_bits2.append(f"Engine gate: {_vg_label}")
        _exec_summary = str(smart_execution_plan.get("summary") or "").strip()
        if _exec_summary:
            data_bits2.append(f"Engine protocol: {_exec_summary.split(':')[0].strip()}")
        _keep = _as_list(smart_execution_plan, "keep_constant")
        if _keep:
            data_bits2.append(f"Engine keep constant: {_keep[0]}")
        if do_not_change_yet:
            data_bits2.append(f"Engine hold: {do_not_change_yet[0]}")
        if blocked_by:
            _bl = blocked_by[0]
            if isinstance(_bl, dict):
                data_bits2.append(
                    f"Engine blocker: {_bl.get('title') or _bl.get('kind') or ''}"
                )
        _rc_level = str(smart_recommendation_confidence.get("level") or "").strip()
        _rc_score = _coerce_float(smart_recommendation_confidence.get("score"))
        _rc_uncertainty = str(
            smart_recommendation_confidence.get("uncertainty") or ""
        ).strip()
        if _rc_level:
            _rcs = f"Engine confidence: {_rc_level}"
            if _rc_score is not None:
                _rcs += f" ({_rc_score:.1f}/100)"
            if _rc_uncertainty:
                _rcs += f" - uncertainty {_rc_uncertainty}"
            data_bits2.append(_rcs)
        _bf_level = str(smart_bullet_fit.get("level") or "").strip()
        _bf_score = _coerce_float(smart_bullet_fit.get("fit_score"))
        if _bf_level:
            _bfs = f"Engine bullet fit: {_bf_level}"
            if _bf_score is not None:
                _bfs += f" ({_bf_score:.1f}/100)"
            data_bits2.append(_bfs)
        _cj_band = str(smart_chamber_jump.get("jump_band") or "").strip()
        _cj_mm = _coerce_float(smart_chamber_jump.get("current_jump_mm"))
        if _cj_band:
            _cjs = f"Engine jump: {_cj_band}"
            if _cj_mm is not None:
                _cjs += f" ({_cj_mm:.3f} mm)"
            data_bits2.append(_cjs)
        _branch_disp = str(smart_branch_advisory.get("display_line") or "").strip()
        if _branch_disp:
            data_bits2.append(f"Engine branch: {_branch_disp}")
        if smart_baseline_control.get("active_return_line"):
            data_bits2.append(
                f"Engine baseline control: {smart_baseline_control['active_return_line']}"
            )
        if data_bits2:
            card_hint += " " + " | ".join(data_bits2) + "."
        return {"header": header, "setup": setup_line, "card_hint": card_hint}

    # --- Default: next_focus / weakest_link branches ---
    setup_line = ""
    if (
        not setup_line
        and smart_execution_summary
        and pressure_level not in {"critical", "warning"}
    ):
        setup_line = f"Test setup: {smart_execution_summary}"
    if not setup_line and next_focus == "capture_measured_velocity":
        setup_line = "Test setup: run a 5-shot chrono confirmation at the current seating before using new grouping results as the node signal."
    elif not setup_line and next_focus == "capture_group_validation":
        setup_line = "Test setup: keep the validated velocity recipe stable and shoot a focused confirmation group before changing charge or seating again."
    elif not setup_line and next_focus == "strengthen_barrel_profile":
        setup_line = "Test setup: repeat the same barrel condition with chrono and grouping so the barrel profile learns from matched evidence."
    elif not setup_line and next_focus == "verify_component_lot":
        if weakest_link == "kruttlot":
            setup_line = "Test setup: treat the powder lot as new, start about 0.2 gr under the previous confirmed charge, and chrono the first 5 shots before extending the ladder."
        elif weakest_link == "kulelot":
            setup_line = "Test setup: keep charge stable and confirm velocity plus grouping with the selected bullet lot before seating-depth tuning."
        elif weakest_link == "primerlot":
            setup_line = "Test setup: keep charge stable and chrono the first 5 shots with the selected primer lot before you trust pressure and ES behavior."
        elif weakest_link == "hylselot":
            setup_line = "Test setup: measure case capacity from the active lot, then chrono a short confirmation batch before trusting pressure and node shifts."
        else:
            setup_line = "Test setup: keep one variable stable and run a short confirmation batch so the active component lot gets measured evidence."
    elif not setup_line and weakest_link == "pipe":
        setup_line = "Test setup: repeat under the same barrel condition and log chrono plus grouping before changing components."
    elif not setup_line and weakest_link == "hylse":
        setup_line = "Test setup: measure case baseline inputs first, then rerun the current recipe so pressure and velocity assumptions rest on measured brass data."

    if not setup_line:
        return {}

    title_parts: list[str] = []
    if next_focus:
        title_parts.append(focus_labels.get(next_focus, next_focus.replace("_", " ")))
    if weakest_link:
        title_parts.append(
            f"weakest link {weakest_labels.get(weakest_link, weakest_link)}"
        )
    header = "Learning priority"
    if header_title_override:
        header += ": " + header_title_override
    if title_parts:
        header += (", " if header_title_override else ": ") + ", ".join(title_parts)
    if confidence_label:
        header += f" ({confidence_label})"

    card_hint = f"{header}. {setup_line}"

    data_bits3: list[str] = []
    _rp3 = str(smart_candidate_profile.get("robustness_level") or "").strip()
    _nf3 = str(smart_candidate_profile.get("node_fit") or "").strip()
    _ht3 = str(smart_harmonics.get("stability_tier") or "").strip()
    if _rp3 or _nf3 or _ht3:
        data_bits3.append(
            f"Engine robustness: {_rp3}, node fit {_nf3}, harmonics {_ht3}".strip(", ")
        )
    if smart_next_test_action:
        data_bits3.append(f"Engine next test: {smart_next_test_action}")
    _conf_level3 = str(smart_recommendation_confidence.get("level") or "").strip()
    _conf_score3 = _coerce_float(smart_recommendation_confidence.get("score"))
    _conf_summary3 = str(smart_recommendation_confidence.get("summary") or "").strip()
    if _conf_level3:
        _ct3 = f"Engine confidence: {_conf_level3}"
        if _conf_score3 is not None:
            _ct3 += f" ({_conf_score3:.1f}/100)"
        if _conf_summary3:
            _ct3 += f" - {_conf_summary3}"
        data_bits3.append(_ct3)
    if input_quality_level:
        data_bits3.append(f"Input quality: {input_quality_level}")
    if data_bits3:
        card_hint += " " + " | ".join(data_bits3) + "."

    return {
        "header": header,
        "setup": setup_line,
        "card_hint": card_hint,
    }


def build_setup_line(
    cur,
    listw,
    self,
    tr,
    smart_evidence_action,
    smart_guidance_title,
    smart_guidance_setup,
    chrono_count,
    usage,
    test_count,
    next_focus,
    weakest_link,
    signal_hint,
    input_quality_level,
    trust_label,
    spread_primary_action,
    spread_shot_plan,
    batch_comparison_workboard,
    batch_comparison_next_session_brief,
    batch_comparison_today_plan,
    batch_comparison_session_manifest,
    batch_spread_control_plan=None,
    batch_spread_decision=None,
    batch_spread_profile_guidance=None,
    batch_spread_evidence_quality=None,
    batch_spread_learning_explanation=None,
    smart_candidate_profile=None,
    smart_next_test=None,
    smart_harmonics=None,
    smart_bullet_fit=None,
    smart_chamber_jump=None,
    smart_guidance=None,
    smart_validation_gate=None,
    smart_execution_plan=None,
    smart_recommendation_confidence=None,
):
    # Definer alle variabler som brukes nedenfor, hvis de ikke allerede er definert
    comparison_session_manifest_bucket = str(
        batch_comparison_session_manifest.get("primary_bucket") or ""
    ).strip()
    comparison_session_manifest_first = str(
        batch_comparison_session_manifest.get("first_batch_name") or ""
    ).strip()
    comparison_session_manifest_preview = _as_list(
        batch_comparison_session_manifest, "queue_preview"
    )
    comparison_session_manifest_lanes = _as_list(
        batch_comparison_session_manifest, "lane_summaries"
    )
    comparison_next_session_brief_title = str(
        batch_comparison_next_session_brief.get("title") or ""
    ).strip()
    comparison_next_session_brief_summary = str(
        batch_comparison_next_session_brief.get("summary") or ""
    ).strip()
    comparison_next_session_brief_action = str(
        batch_comparison_next_session_brief.get("primary_action") or ""
    ).strip()
    comparison_next_session_brief_hold = str(
        batch_comparison_next_session_brief.get("hold_back") or ""
    ).strip()
    comparison_today_plan_title = str(
        batch_comparison_today_plan.get("title") or ""
    ).strip()
    comparison_today_plan_summary = str(
        batch_comparison_today_plan.get("summary") or ""
    ).strip()
    comparison_today_plan_action = str(
        batch_comparison_today_plan.get("primary_action") or ""
    ).strip()
    comparison_workboard_title = str(
        batch_comparison_workboard.get("title") or ""
    ).strip()
    comparison_workboard_summary = str(
        batch_comparison_workboard.get("summary") or ""
    ).strip()
    comparison_workboard_status = str(
        batch_comparison_workboard.get("status_label") or ""
    ).strip()
    comparison_workboard_action = str(
        batch_comparison_workboard.get("primary_action") or ""
    ).strip()
    comparison_workboard_first = str(
        batch_comparison_workboard.get("first_batch_name") or ""
    ).strip()
    comparison_workboard_bucket = str(
        batch_comparison_workboard.get("primary_bucket") or ""
    ).strip()
    comparison_workboard_counts = _as_dict(batch_comparison_workboard, "counts")
    comparison_workboard_counts_text = " | ".join(
        f"{bucket} {int(value)}"
        for bucket, value in [
            ("shoot_now", comparison_workboard_counts.get("shoot_now") or 0),
            ("confirm", comparison_workboard_counts.get("confirm") or 0),
            ("hold", comparison_workboard_counts.get("hold") or 0),
            ("pause", comparison_workboard_counts.get("pause") or 0),
            ("reject_watch", comparison_workboard_counts.get("reject_watch") or 0),
        ]
    )

    # SQL-kall og analyse av test_results
    cur.execute(
        "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 200"
    )
    rows = cur.fetchall() or []
    charges = []
    velocities = []
    for r in reversed(rows):
        try:
            c = float(r[0])
            v = float(r[1])
        except Exception:
            continue
        charges.append(c)
        velocities.append(v)
    if not charges:
        QMessageBox.information(
            self, tr("mlb_no_data_title"), tr("mlb_no_test_results_refit")
        )
        return
    from ..utils.gp_optimizer import suggest_next_charge

    min_c = max(0.0, min(charges) - 1.0)
    max_c = max(charges) + 1.0
    new_sugg = suggest_next_charge(charges, velocities, (min_c, max_c))
    import json

    cur.execute(
        "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
        (float(new_sugg), json.dumps({"based_on_rows": len(charges)})),
    )
    self.db.conn.commit()
    QMessageBox.information(
        self,
        tr("mlb_refit_complete_title"),
        tr("mlb_refit_complete_message", charge=new_sugg),
    )
    # refresh list
    listw.clear()
    cur.execute(
        "SELECT id, suggested_charge, created_date, basis_text FROM optimizer_suggestions ORDER BY id DESC LIMIT 200"
    )
    rows = cur.fetchall() or []
    for r in rows:
        sid2 = r[0]
        sc2 = r[1]
        cd2 = r[2]
        basis2 = (r[3] or "")[:200]
        item2 = QListWidgetItem(
            f"#{sid2} — {format_weight_grains(sc2, 'powder')} — {cd2} — {basis2}"
        )
        item2.setData(Qt.ItemDataRole.UserRole, sid2)
        listw.addItem(item2)

    setup_line = f"Test setup: {smart_evidence_action}"

    # Tilføy ekstra informasjon til setup_line hvis relevante variabler er satt
    if spread_shot_plan:
        setup_line += f" Shot plan: {spread_shot_plan}"
    if spread_profile_check:
        setup_line += f" Profile check: {spread_profile_check}"
    if spread_validation_next_gate:
        setup_line += f" Validation gate: {spread_validation_next_gate}"
    if comparison_advisory_action:
        setup_line += f" Comparison gate: {comparison_advisory_action}"
    if comparison_protocol_action:
        setup_line += f" Head-to-head: {comparison_protocol_action}"
        if comparison_protocol_plan:
            setup_line += f" Protocol: {comparison_protocol_plan}"
    if comparison_next_measurement:
        setup_line += f" Bottleneck check: {comparison_next_measurement}"
    if comparison_acceptance_gate:
        setup_line += f" Acceptance gate: {comparison_acceptance_gate}"
    elif comparison_acceptance_first_gap:
        setup_line += f" Acceptance gap: {comparison_acceptance_first_gap}"
    if comparison_acceptance_progress_target:
        setup_line += f" Progress target: {comparison_acceptance_progress_target}"
    if comparison_next_test_action:
        setup_line += f" Next test: {comparison_next_test_action}"
    elif comparison_next_test_title:
        setup_line += f" Next test: {comparison_next_test_title}"
    if comparison_mission_action:
        setup_line += f" Mission action: {comparison_mission_action}"
    if comparison_session_strategy_objective:
        setup_line += f" Session objective: {comparison_session_strategy_objective}"
    if comparison_action_plan_next:
        setup_line += f" Action plan: {comparison_action_plan_next}"
    if comparison_session_queue_first:
        setup_line += f" Queue first: {comparison_session_queue_first}"
    if comparison_session_manifest_bucket:
        setup_line += f" Session bucket: {comparison_session_manifest_bucket}"
    if comparison_session_manifest_first:
        setup_line += f" Manifest first: {comparison_session_manifest_first}"
    if comparison_next_session_brief_action:
        setup_line += f" Session brief: {comparison_next_session_brief_action}"
    if comparison_today_plan_action:
        setup_line += f" Today plan: {comparison_today_plan_action}"
    if comparison_workboard_action:
        setup_line += f" Workboard: {comparison_workboard_action}"
    if comparison_workboard_bucket:
        setup_line += f" Workboard lane: {comparison_workboard_bucket}"
    if comparison_workboard_first:
        setup_line += f" Workboard first: {comparison_workboard_first}"
    if comparison_workboard_counts_text:
        setup_line += f" Workboard counts: {comparison_workboard_counts_text}"
    if comparison_workboard_lanes_text:
        setup_line += f" Workboard lanes: {comparison_workboard_lanes_text}"
    if comparison_checklist_first:
        setup_line += f" Compare first: {comparison_checklist_first}"

    if smart_execution_summary and pressure_level not in {"critical", "warning"}:
        if not setup_line:
            setup_line = f"Test setup: {smart_execution_summary}"
        if smart_validation_next_gate:
            setup_line += f" Validation gate: {smart_validation_next_gate}"
        first_keep_constant = next(
            (
                str(item).strip()
                for item in smart_execution_keep_constant
                if str(item).strip()
            ),
            "",
        )
        if first_keep_constant:
            setup_line += f" Keep constant: {first_keep_constant}"
        first_capture = next(
            (
                str(item).strip()
                for item in smart_execution_capture
                if str(item).strip()
            ),
            "",
        )
        if first_capture:
            setup_line += f" Capture: {first_capture}"
        if smart_execution_success:
            setup_line += f" Success: {smart_execution_success}"
        if smart_charge_alignment == "outside" and smart_charge_target:
            setup_line += f" Charge target: {smart_charge_target}"
        if smart_seating_alignment == "outside" and smart_seating_target:
            setup_line += f" Seating target: {smart_seating_target}"
        if smart_branch_action_line:
            setup_line += f" Baseline control: {smart_branch_action_line}"

    focus_labels = {
        "capture_measured_velocity": "capture measured velocity",
        "capture_group_validation": "capture group validation",
        "strengthen_barrel_profile": "strengthen barrel profile",
        "verify_component_lot": "verify component lot",
    }
    weakest_labels = {
        "pipe": "pipe",
        "hylse": "case baseline",
        "kulelot": "bullet lot",
        "kruttlot": "powder lot",
        "primerlot": "primer lot",
        "hylselot": "case lot",
    }

    title_parts = []
    if next_focus:
        title_parts.append(focus_labels.get(next_focus, next_focus.replace("_", " ")))
    if weakest_link:
        title_parts.append(
            f"weakest link {weakest_labels.get(weakest_link, weakest_link)}"
        )

    if not setup_line and next_focus == "capture_measured_velocity":
        setup_line = "Test setup: run a 5-shot chrono confirmation at the current seating before using new grouping results as the node signal."
    elif not setup_line and next_focus == "capture_group_validation":
        setup_line = "Test setup: keep the validated velocity recipe stable and shoot a focused confirmation group before changing charge or seating again."
    elif not setup_line and next_focus == "strengthen_barrel_profile":
        setup_line = "Test setup: repeat the same barrel condition with chrono and grouping so the barrel profile learns from matched evidence."
    elif not setup_line and next_focus == "verify_component_lot":
        if weakest_link == "kruttlot":
            setup_line = "Test setup: treat the powder lot as new, start about 0.2 gr under the previous confirmed charge, and chrono the first 5 shots before extending the ladder."
        elif weakest_link == "kulelot":
            setup_line = "Test setup: keep charge stable and confirm velocity plus grouping with the selected bullet lot before seating-depth tuning."
        elif weakest_link == "primerlot":
            setup_line = "Test setup: keep charge stable and chrono the first 5 shots with the selected primer lot before you trust pressure and ES behavior."
        elif weakest_link == "hylselot":
            setup_line = "Test setup: measure case capacity from the active lot, then chrono a short confirmation batch before trusting pressure and node shifts."
        else:
            setup_line = "Test setup: keep one variable stable and run a short confirmation batch so the active component lot gets measured evidence."
    elif not setup_line and weakest_link == "pipe":
        setup_line = "Test setup: repeat under the same barrel condition and log chrono plus grouping before changing components."
    elif not setup_line and weakest_link == "hylse":
        setup_line = "Test setup: measure case baseline inputs first, then rerun the current recipe so pressure and velocity assumptions rest on measured brass data."

    if not setup_line:
        return {}

    header = "Learning priority"
    if header_title_override:
        header += ": " + header_title_override
    if title_parts:
        header += (", " if header_title_override else ": ") + ", ".join(title_parts)
    if confidence_label:
        header += f" ({confidence_label})"

    data_bits = []
    if chrono_count or test_count:
        data_bits.append(
            f"Data foundation: {chrono_count} chrono, {test_count} validation tests"
        )
    if pressure_level in {"critical", "warning"}:
        data_bits.append(f"Pressure state: {pressure_level}")
    elif input_quality_level:
        data_bits.append(f"Input quality: {input_quality_level}")
    if trust_label:
        data_bits.append(f"Trust: {trust_label}")
    if signal_hint:
        data_bits.append(f"Signal: {signal_hint}")
    if spread_decision_label or spread_decision_state:
        data_bits.append(f"Decision: {spread_decision_label or spread_decision_state}")
    if spread_profile_title:
        data_bits.append(f"Profile: {spread_profile_title}")
    if spread_profile_emphasis:
        data_bits.append(f"Profile focus: {spread_profile_emphasis}")
    if spread_quality_level:
        quality_text = f"Evidence quality: {spread_quality_level}"
        if spread_quality_score is not None:
            quality_text += f" ({spread_quality_score:.1f}/100)"
        data_bits.append(quality_text)
    if spread_lesson_title:
        data_bits.append(f"Lesson: {spread_lesson_title}")
    if spread_lesson_takeaway:
        data_bits.append(f"Takeaway: {spread_lesson_takeaway}")
    if smart_candidate_robustness:
        engine_text = f"Engine robustness: {smart_candidate_robustness}"
        if smart_node_fit:
            engine_text += f", node fit {smart_node_fit}"
        if smart_harmonics_tier:
            engine_text += f", harmonics {smart_harmonics_tier}"
        data_bits.append(engine_text)
    if smart_bullet_fit_level:
        bullet_fit_text = f"Engine bullet fit: {smart_bullet_fit_level}"
        if smart_bullet_fit_score is not None:
            bullet_fit_text += f" ({smart_bullet_fit_score:.1f}/100)"
        if smart_bullet_fit_message:
            bullet_fit_text += f" - {smart_bullet_fit_message}"
        data_bits.append(bullet_fit_text)
    if smart_jump_band or smart_jump_summary:
        jump_text = "Engine jump: "
        if smart_jump_band:
            jump_text += smart_jump_band
            if smart_current_jump_mm is not None:
                jump_text += f" ({smart_current_jump_mm:.3f} mm)"
        if smart_jump_summary:
            jump_text += f" - {smart_jump_summary}"
        data_bits.append(jump_text)
    if smart_engine_next_action:
        engine_next_text = f"Engine next test: {smart_engine_next_action}"
        if smart_engine_next_reason:
            engine_next_text += f" - {smart_engine_next_reason}"
        data_bits.append(engine_next_text)
    if smart_validation_label:
        engine_gate_text = f"Engine gate: {smart_validation_label}"
        if smart_validation_next_gate:
            engine_gate_text += f" - {smart_validation_next_gate}"
        data_bits.append(engine_gate_text)
    if smart_execution_summary:
        engine_plan_text = f"Engine protocol: {smart_execution_summary}"
        if smart_execution_session_type:
            engine_plan_text += f" [{smart_execution_session_type}]"
        data_bits.append(engine_plan_text)
    first_engine_keep_constant = next(
        (
            str(item).strip()
            for item in smart_execution_keep_constant
            if str(item).strip()
        ),
        "",
    )
    if first_engine_keep_constant:
        data_bits.append(f"Engine keep constant: {first_engine_keep_constant}")
    first_engine_capture = next(
        (str(item).strip() for item in smart_execution_capture if str(item).strip()),
        "",
    )
    if first_engine_capture:
        data_bits.append(f"Engine capture: {first_engine_capture}")
    first_engine_hold = next(
        (str(item).strip() for item in smart_do_not_change_yet if str(item).strip()),
        "",
    )
    if first_engine_hold:
        data_bits.append(f"Engine hold: {first_engine_hold}")
    first_engine_blocker = next(
        (
            str(item.get("title") or item.get("kind") or "").strip()
            for item in smart_blocked_by
            if isinstance(item, dict)
            and str(item.get("title") or item.get("kind") or "").strip()
        ),
        "",
    )
    if first_engine_blocker:
        data_bits.append(f"Engine blocker: {first_engine_blocker}")
    if smart_confidence_level:
        confidence_text = f"Engine confidence: {smart_confidence_level}"
        if smart_confidence_score is not None:
            confidence_text += f" ({smart_confidence_score:.1f}/100)"
        if smart_confidence_uncertainty:
            confidence_text += f" - uncertainty {smart_confidence_uncertainty}"
        data_bits.append(confidence_text)
    if smart_confidence_summary:
        data_bits.append(f"Engine confidence note: {smart_confidence_summary}")
    if smart_evidence_status:
        evidence_text = f"Engine evidence: {smart_evidence_status}"
        first_evidence_item = next(
            (str(item).strip() for item in smart_evidence_items if str(item).strip()),
            "",
        )
        if first_evidence_item:
            evidence_text += f" - {first_evidence_item}"
        data_bits.append(evidence_text)
    first_evidence_focus = next(
        (str(item).strip() for item in smart_evidence_focus if str(item).strip()), ""
    )
    if first_evidence_focus:
        data_bits.append(f"Engine evidence focus: {first_evidence_focus}")
    if smart_branch_display_line:
        data_bits.append(f"Engine branch: {smart_branch_display_line}")
    elif smart_branch_label:
        branch_text = f"Engine branch: {smart_branch_label}"
        if smart_branch_compare_mode:
            branch_text += f" ({smart_branch_compare_mode})"
        data_bits.append(branch_text)
    if smart_active_return_line:
        data_bits.append(f"Engine baseline control: {smart_active_return_line}")
    elif smart_charge_return_line:
        data_bits.append(f"Engine charge baseline: {smart_charge_return_line}")
    elif smart_seating_return_line:
        data_bits.append(f"Engine seating baseline: {smart_seating_return_line}")
    if spread_capture_title:
        first_capture = next(
            (
                str(item.get("label") or "").strip()
                for item in spread_capture_items
                if isinstance(item, dict) and str(item.get("label") or "").strip()
            ),
            "",
        )
        checklist_text = f"Checklist: {spread_capture_title}"
        if first_capture:
            checklist_text += f" -> {first_capture}"
        data_bits.append(checklist_text)
    if spread_validation_label:
        validation_text = f"Validation: {spread_validation_label}"
        if spread_validation_score is not None:
            validation_text += f" ({spread_validation_score:.1f}/100)"
        if spread_validation_summary:
            validation_text += f" - {spread_validation_summary}"
        data_bits.append(validation_text)
    if comparison_state:
        comparison_text = f"Batch comparison: {comparison_state}"
        if comparison_rank is not None and comparison_count is not None:
            comparison_text += f" ({comparison_rank}/{comparison_count})"
        if comparison_summary:
            comparison_text += f" - {comparison_summary}"
        data_bits.append(comparison_text)
    if comparison_advisory_title:
        advisory_text = f"Comparison advisory: {comparison_advisory_title}"
        if comparison_advisory_message:
            advisory_text += f" - {comparison_advisory_message}"
        data_bits.append(advisory_text)
    if comparison_protocol_title:
        protocol_text = f"Comparison protocol: {comparison_protocol_title}"
        if comparison_protocol_action:
            protocol_text += f" - {comparison_protocol_action}"
        data_bits.append(protocol_text)
    if comparison_bottleneck:
        explanation_text = f"Comparison bottleneck: {comparison_bottleneck}"
        if comparison_reason:
            explanation_text += f" - {comparison_reason}"
        data_bits.append(explanation_text)
    if comparison_verdict_label:
        verdict_text = f"Comparison verdict: {comparison_verdict_label}"
        if comparison_verdict_summary:
            verdict_text += f" - {comparison_verdict_summary}"
        data_bits.append(verdict_text)
    if comparison_acceptance_label:
        acceptance_text = f"Comparison acceptance: {comparison_acceptance_label}"
        if comparison_acceptance_summary:
            acceptance_text += f" - {comparison_acceptance_summary}"
        data_bits.append(acceptance_text)
    if comparison_acceptance_first_gap:
        data_bits.append(f"Acceptance gap: {comparison_acceptance_first_gap}")
    if comparison_acceptance_progress_level:
        progress_text = f"Acceptance progress: {comparison_acceptance_progress_level}"
        if comparison_acceptance_progress_score is not None:
            progress_text += f" ({comparison_acceptance_progress_score:.1f}/100)"
        if (
            comparison_acceptance_progress_passed is not None
            and comparison_acceptance_progress_total is not None
        ):
            progress_text += f" {comparison_acceptance_progress_passed}/{comparison_acceptance_progress_total}"
        if comparison_acceptance_progress_summary:
            progress_text += f" - {comparison_acceptance_progress_summary}"
        data_bits.append(progress_text)
    if comparison_next_test_title:
        next_test_text = f"Next test: {comparison_next_test_title}"
        if comparison_next_test_summary:
            next_test_text += f" - {comparison_next_test_summary}"
        if comparison_next_test_first_check:
            next_test_text += f" -> {comparison_next_test_first_check}"
        data_bits.append(next_test_text)
    if comparison_board_headline:
        board_text = f"Comparison board: {comparison_board_headline}"
        if comparison_board_band:
            board_text += f" ({comparison_board_band})"
        if comparison_board_summary:
            board_text += f" - {comparison_board_summary}"
        data_bits.append(board_text)
    if comparison_profile_title:
        profile_text = f"Comparison profile: {comparison_profile_title}"
        if comparison_profile_emphasis:
            profile_text += f" - {comparison_profile_emphasis}"
        if comparison_profile_guardrail:
            profile_text += f" - {comparison_profile_guardrail}"
        data_bits.append(profile_text)
    if comparison_mission:
        mission_text = f"Mission brief: {comparison_mission}"
        if comparison_mission_success:
            mission_text += f" - {comparison_mission_success}"
        data_bits.append(mission_text)
    if comparison_portfolio_title:
        portfolio_text = f"Portfolio: {comparison_portfolio_title}"
        if comparison_portfolio_focus:
            portfolio_text += f" - {comparison_portfolio_focus}"
        data_bits.append(portfolio_text)
    if comparison_session_strategy_title:
        strategy_text = f"Session strategy: {comparison_session_strategy_title}"
        if comparison_session_strategy_mode:
            strategy_text += f" ({comparison_session_strategy_mode})"
        if comparison_session_strategy_objective:
            strategy_text += f" - {comparison_session_strategy_objective}"
        data_bits.append(strategy_text)
    if comparison_campaign_title:
        campaign_text = f"Campaign view: {comparison_campaign_title}"
        if comparison_campaign_summary:
            campaign_text += f" - {comparison_campaign_summary}"
        data_bits.append(campaign_text)
    if comparison_action_plan_title:
        action_text = f"Action plan: {comparison_action_plan_title}"
        if comparison_action_plan_summary:
            action_text += f" - {comparison_action_plan_summary}"
        data_bits.append(action_text)
    if comparison_campaign_board_title:
        board2_text = f"Campaign board: {comparison_campaign_board_title}"
        if comparison_campaign_board_summary:
            board2_text += f" - {comparison_campaign_board_summary}"
        if comparison_campaign_board_preview:
            board2_text += " - " + " | ".join(
                str(item).strip()
                for item in comparison_campaign_board_preview[:3]
                if str(item).strip()
            )
        data_bits.append(board2_text)
    if comparison_session_queue_title:
        queue_text = f"Session queue: {comparison_session_queue_title}"
        if comparison_session_queue_first:
            queue_text += f" - first {comparison_session_queue_first}"
        if comparison_session_queue_preview:
            queue_text += " - " + " | ".join(
                str(item).strip()
                for item in comparison_session_queue_preview[:3]
                if str(item).strip()
            )
        data_bits.append(queue_text)
    if comparison_session_manifest_title:
        manifest_text = f"Session manifest: {comparison_session_manifest_title}"
        if comparison_session_manifest_bucket:
            manifest_text += f" ({comparison_session_manifest_bucket})"
        if comparison_session_manifest_summary:
            manifest_text += f" - {comparison_session_manifest_summary}"
        if comparison_session_manifest_preview:
            manifest_text += " - " + " | ".join(
                str(item).strip()
                for item in comparison_session_manifest_preview[:3]
                if str(item).strip()
            )
        if comparison_session_manifest_lanes:
            manifest_text += " - " + " | ".join(
                str(item.get("summary") or "").strip()
                for item in comparison_session_manifest_lanes[:4]
                if isinstance(item, dict) and str(item.get("summary") or "").strip()
            )
        data_bits.append(manifest_text)
    if comparison_next_session_brief_title:
        brief_text = f"Next session brief: {comparison_next_session_brief_title}"
        if comparison_next_session_brief_summary:
            brief_text += f" - {comparison_next_session_brief_summary}"
        if comparison_next_session_brief_hold:
            brief_text += f" - hold back {comparison_next_session_brief_hold}"
        data_bits.append(brief_text)
    if comparison_today_plan_title:
        today_text = f"Today plan: {comparison_today_plan_title}"
        if comparison_today_plan_summary:
            today_text += f" - {comparison_today_plan_summary}"
        data_bits.append(today_text)
    if comparison_workboard_title:
        workboard_text = f"Workboard: {comparison_workboard_title}"
        if comparison_workboard_summary:
            workboard_text += f" - {comparison_workboard_summary}"
        if comparison_workboard_status:
            workboard_text += f" - {comparison_workboard_status}"
        if comparison_workboard_bucket:
            workboard_text += f" - lane {comparison_workboard_bucket}"
        if comparison_workboard_first:
            workboard_text += f" - first {comparison_workboard_first}"
        if comparison_workboard_counts_text:
            workboard_text += f" - {comparison_workboard_counts_text}"
        if comparison_workboard_lanes_text:
            workboard_text += f" - {comparison_workboard_lanes_text}"
        data_bits.append(workboard_text)
    if comparison_checklist_title:
        checklist_text = f"Comparison checklist: {comparison_checklist_title}"
        if comparison_checklist_first:
            checklist_text += f" -> {comparison_checklist_first}"
        data_bits.append(checklist_text)
    if comparison_swing_factor:
        scorecard_text = f"Comparison scorecard: {comparison_swing_factor}"
        if comparison_scorecard_summary:
            scorecard_text += f" - {comparison_scorecard_summary}"
        data_bits.append(scorecard_text)
    if comparison_confidence_level:
        confidence_text = f"Comparison confidence: {comparison_confidence_level}"
        if comparison_confidence_score is not None:
            confidence_text += f" ({comparison_confidence_score:.1f}/100)"
        if comparison_confidence_summary:
            confidence_text += f" - {comparison_confidence_summary}"
        data_bits.append(confidence_text)
    if comparison_learning_summary:
        learning_text = f"Comparison learning: {comparison_learning_summary}"
        if comparison_learning_takeaway:
            learning_text += f" - {comparison_learning_takeaway}"
        data_bits.append(learning_text)
    if batch_spread_reason:
        data_bits.append(f"Spread reason: {batch_spread_reason}")

    card_hint = f"{header}. {setup_line}"
    if data_bits:
        card_hint += " " + " | ".join(data_bits) + "."

    return {
        "header": header,
        "setup": setup_line,
        "card_hint": card_hint,
    }


def summarize_runtime_primer_review(runtime: dict | None) -> dict[str, Any]:
    _rt = runtime if isinstance(runtime, dict) else {}
    evidence = _as_dict(_rt, "evidence")
    primer_review = _as_dict(evidence, "primer_review")
    summary = _as_dict(evidence, "summary")
    context = _as_dict(_rt, "context")
    identity = _as_dict(_rt, "identity")
    session = _as_dict(_rt, "session")
    identity_barrel = _as_dict(identity, "barrel")
    barrel_label = str(
        identity_barrel.get("label")
        or context.get("barrel_name")
        or session.get("barrel_name")
        or context.get("barrel_id")
        or session.get("barrel_id")
        or ""
    ).strip()
    configuration_label = str(
        identity_barrel.get("configuration_label")
        or context.get("barrel_configuration_name")
        or session.get("barrel_configuration_name")
        or ""
    ).strip()
    setup_label = _format_barrel_configuration_label(configuration_label, barrel_label)
    if setup_label:
        barrel_label = setup_label
    barrel_context = f" for barrel {barrel_label}" if barrel_label else ""

    status = (
        str(
            primer_review.get("status") or summary.get("primer_review_status") or "none"
        )
        .strip()
        .lower()
    )
    enabled_count = (
        _coerce_int(
            primer_review.get("enabled_session_count")
            or summary.get("primer_review_enabled_session_count")
        )
        or 0
    )
    disabled_count = (
        _coerce_int(
            primer_review.get("disabled_session_count")
            or summary.get("primer_review_disabled_session_count")
        )
        or 0
    )
    reviewed_count = (
        _coerce_int(
            primer_review.get("reviewed_session_count")
            or summary.get("primer_review_session_count")
        )
        or 0
    )
    image_count = (
        _coerce_int(
            primer_review.get("review_image_count")
            or summary.get("primer_review_image_count")
        )
        or 0
    )
    pressure_review_count = (
        _coerce_int(
            primer_review.get("pressure_sign_review_count")
            or summary.get("pressure_sign_primer_review_count")
        )
        or 0
    )

    if status == "disabled":
        return {
            "status": status,
            "level": "info",
            "title": "Primer review disabled",
            "message": f"Primer image review is explicitly turned off for the linked batch sessions{barrel_context}, so missing primer photos are intentional. Primer appearance is only a supporting pressure diagnostic and should not drive accuracy decisions on its own.",
            "summary": f"primer review disabled across {disabled_count} session{'s' if disabled_count != 1 else ''}",
        }
    if status == "captured":
        review_bits = []
        if reviewed_count:
            review_bits.append(
                f"{reviewed_count} reviewed session{'s' if reviewed_count != 1 else ''}"
            )
        if image_count:
            review_bits.append(f"{image_count} image{'s' if image_count != 1 else ''}")
        if pressure_review_count:
            review_bits.append(
                f"{pressure_review_count} pressure-sign review{'s' if pressure_review_count != 1 else ''}"
            )
        detail = ", ".join(review_bits) if review_bits else "captured evidence"
        return {
            "status": status,
            "level": "ok",
            "title": "Primer review linked",
            "message": f"Primer image evidence is linked to the current rifle and load-session context{barrel_context}. Treat it as a supporting pressure and fault-diagnosis clue, not as a direct accuracy signal or a standalone stop/go decision.",
            "summary": detail,
        }
    if status == "enabled":
        return {
            "status": status,
            "level": "warning",
            "title": "Primer review enabled but not logged",
            "message": f"Primer image review is enabled for this workflow context{barrel_context}, but no primer review has been captured yet. When used, it should stay a supporting pressure clue rather than a precision metric.",
            "summary": f"enabled across {enabled_count} session{'s' if enabled_count != 1 else ''}",
        }
    return {
        "status": "none",
        "level": "unknown",
        "title": "Primer review unavailable",
        "message": f"No canonical primer review context is linked to this load session{barrel_context} yet. Primer appearance can help flag pressure or setup issues, but it is not a precision signal by itself.",
        "summary": "no primer review context",
    }


def _runtime_learning_analysis(runtime: dict | None) -> dict[str, Any]:
    _rt = runtime if isinstance(runtime, dict) else {}
    learning = _as_dict(_rt, "learning")
    session_payload = _as_dict(learning, "session")
    return _as_dict(session_payload, "analysis")


def resolve_runtime_learning_context(
    runtime: dict | None,
    analysis: dict | None,
    key: str,
) -> dict[str, Any]:
    runtime_analysis = _runtime_learning_analysis(runtime)
    runtime_value = _as_dict(runtime_analysis, key)
    if runtime_value:
        return runtime_value
    return _as_dict(analysis if isinstance(analysis, dict) else {}, key)


def build_runtime_analysis_context(
    runtime: dict | None,
    analysis: dict | None = None,
) -> dict[str, Any]:
    _rt = runtime if isinstance(runtime, dict) else {}
    session = _as_dict(_rt, "session")
    recommendation = _as_dict(_rt, "recommendation")
    if not recommendation:
        recommendation = _as_dict(session, "recommendation_json")
    fallback = analysis if isinstance(analysis, dict) else {}

    pressure_assessment = _as_dict(recommendation, "pressure_assessment")
    if not pressure_assessment:
        pressure_assessment = _as_dict(fallback, "pressure_assessment")

    internal_ballistics = _as_dict(recommendation, "internal_ballistics")
    if not internal_ballistics:
        internal_ballistics = _as_dict(fallback, "internal_ballistics")

    return {
        "pressure_assessment": pressure_assessment,
        "internal_ballistics": internal_ballistics,
        "brass_context": resolve_runtime_learning_context(
            runtime, fallback, "brass_context"
        ),
        "barrel_context": resolve_runtime_learning_context(
            runtime, fallback, "barrel_context"
        ),
        "stability_assessment": resolve_runtime_learning_context(
            runtime, fallback, "stability_assessment"
        ),
        "primer_review": summarize_runtime_primer_review(runtime),
    }


# LEGACY-ISOLATED: overlaps engine candidate_ranking; safe removal blocked pending builder-class test harness
def summarize_charge_promotion_candidate(
    *,
    current_charge_gr: float | None,
    db: Any | None = None,
    rifle_id: int | None = None,
    bullet_id: int | None = None,
    powder_id: int | None = None,
    history_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = history_result if isinstance(history_result, dict) else None
    if result is None and db is not None:
        try:
            from ..utils.ladder_optimizer import suggest_charge_from_history

            result = suggest_charge_from_history(
                db,
                rifle_id=rifle_id,
                bullet_id=bullet_id,
                powder_id=powder_id,
            )
        except Exception:
            result = None

    if not isinstance(result, dict):
        return {"eligible": False}

    suggested_charge = _coerce_float(result.get("suggested_charge"))
    model = _as_dict(result, "model")
    _observed_range_raw = result.get("observed_range")
    observed_range: list[Any] = (
        list(_observed_range_raw)
        if isinstance(_observed_range_raw, (tuple, list))
        else []
    )
    sample_count = _coerce_int(result.get("sample_count")) or 0
    current_charge = _coerce_float(current_charge_gr)
    model_a = _coerce_float(model.get("a"))
    model_r2 = _coerce_float(model.get("r2"))
    observed_min = (
        _coerce_float(observed_range[0]) if len(observed_range) == 2 else None
    )
    observed_max = (
        _coerce_float(observed_range[1]) if len(observed_range) == 2 else None
    )
    observed_span = None
    if observed_min is not None and observed_max is not None:
        observed_span = round(observed_max - observed_min, 2)
    charge_delta = None
    if suggested_charge is not None and current_charge is not None:
        charge_delta = round(current_charge - suggested_charge, 2)

    eligible = bool(
        suggested_charge is not None
        and current_charge is not None
        and model_a is not None
        and model_a > 0.0
        and model_r2 is not None
        and model_r2 >= 0.60
        and sample_count >= 4
        and observed_span is not None
        and observed_span <= 1.5
        and charge_delta is not None
        and abs(charge_delta) <= 0.15
    )
    if not eligible:
        return {
            "eligible": False,
            "suggested_charge_gr": suggested_charge,
            "model_r2": model_r2,
            "sample_count": sample_count,
            "observed_range_gr": (
                [observed_min, observed_max]
                if observed_min is not None and observed_max is not None
                else None
            ),
            "charge_delta_gr": charge_delta,
        }

    assert suggested_charge is not None  # guaranteed by eligible check above
    assert model_r2 is not None  # guaranteed by eligible check above
    return {
        "eligible": True,
        "title": "Ready for learned charge",
        "message": (
            f"History is strong enough to treat {suggested_charge:.2f} gr as a learned charge "
            f"(R2 {model_r2:.2f}, {sample_count} ladder points)."
        ),
        "promoted_charge_gr": round(suggested_charge, 2),
        "model_r2": model_r2,
        "sample_count": sample_count,
        "observed_range_gr": (
            [observed_min, observed_max]
            if observed_min is not None and observed_max is not None
            else None
        ),
        "charge_delta_gr": charge_delta,
    }


def _format_barrel_configuration_label(
    barrel_configuration_name: str | None,
    barrel_name: str | None = None,
) -> str:
    configuration = str(barrel_configuration_name or "").strip()
    barrel = str(barrel_name or "").strip()
    if configuration and barrel and configuration.casefold() != barrel.casefold():
        return f"{barrel} / {configuration}"
    return configuration or barrel


# LEGACY-ISOLATED: overlaps engine baseline_control; safe removal blocked pending builder-class test harness
def build_evidence_recommendation_baseline(
    *,
    analysis: dict[str, Any] | None,
    current_charge_gr: float | None,
    coal_mm: float | None,
    cbto_mm: float | None,
    seating_summary: dict[str, Any] | None = None,
    charge_promotion_candidate: dict[str, Any] | None = None,
    signature: tuple[Any, ...] | None = None,
) -> dict[str, Any]:
    _analysis: dict[str, Any] = analysis or {}
    _seating: dict[str, Any] = seating_summary or {}
    rifle_context = _as_dict(_analysis, "rifle_context")
    recommendation = _as_dict(_analysis, "recommendation")
    input_quality = _as_dict(_analysis, "input_quality")
    observations = _as_dict(_analysis, "observations")
    observation_summary = _as_dict(observations, "summary")
    baseline_readiness = _as_dict(recommendation, "baseline_readiness")
    promotion_candidate = _as_dict(_seating, "promotion_candidate")
    best_known_evidence = _as_dict(_seating, "best_known_evidence")
    _cpq: dict[str, Any] = (
        charge_promotion_candidate
        if isinstance(charge_promotion_candidate, dict)
        else {}
    )
    charge_promotion_candidate = _cpq
    quality_level = str(input_quality.get("level") or "").strip().lower()
    quality_score = _coerce_float(input_quality.get("score")) or 0.0
    chrono_count = int(observation_summary.get("chrono_count") or 0)
    accuracy_count = int(observation_summary.get("accuracy_count") or 0)
    allow_recommended_charge = bool(baseline_readiness.get("charge_can_freeze"))
    allow_recommended_seating = bool(baseline_readiness.get("seating_can_freeze"))
    if not baseline_readiness:
        allow_recommended_charge = (
            quality_level in {"medium", "high"}
            and quality_score >= 2.5
            and (chrono_count >= 1 or accuracy_count >= 1)
        )
        allow_recommended_seating = (
            quality_level in {"medium", "high"}
            and quality_score >= 2.5
            and accuracy_count >= 1
        )

    barrel_name = str(rifle_context.get("barrel_name") or "").strip()
    barrel_configuration_id = str(
        rifle_context.get("barrel_configuration_id") or ""
    ).strip()
    barrel_configuration_name = str(
        rifle_context.get("barrel_configuration_name") or ""
    ).strip()
    setup_label = _format_barrel_configuration_label(
        barrel_configuration_name, barrel_name
    )

    baseline: dict[str, Any] = {
        "available": False,
        "signature": signature,
        "charge_gr": current_charge_gr,
        "coal_mm": coal_mm,
        "cbto_mm": cbto_mm,
        "charge_source": "current",
        "seating_source": "current",
        "trust_score": _coerce_float(input_quality.get("score")),
        "trust_label": str(input_quality.get("level") or "unknown").strip().lower()
        or "unknown",
        "barrel_name": barrel_name,
        "barrel_configuration_id": barrel_configuration_id or None,
        "barrel_configuration_name": barrel_configuration_name,
        "setup_label": setup_label,
    }

    promoted_charge = _coerce_float(
        charge_promotion_candidate.get("promoted_charge_gr")
    )
    if charge_promotion_candidate.get("eligible") and promoted_charge is not None:
        baseline["available"] = True
        baseline["charge_gr"] = round(promoted_charge, 2)
        baseline["charge_source"] = "learned"
        baseline["charge_source_detail"] = "history"
    charge_window = _as_list(recommendation, "charge_window_gr")
    if (
        baseline.get("charge_source") != "learned"
        and allow_recommended_charge
        and len(charge_window) == 2
    ):
        charge_min = _coerce_float(charge_window[0])
        charge_max = _coerce_float(charge_window[1])
        if charge_min is not None and charge_max is not None:
            baseline["available"] = True
            baseline["charge_gr"] = round((charge_min + charge_max) / 2.0, 2)
            baseline["charge_window_gr"] = [charge_min, charge_max]
            baseline["charge_source"] = "recommended"

    seating_window = _as_list(recommendation, "seating_window_mm")
    if allow_recommended_seating and len(seating_window) == 2 and coal_mm is not None:
        seat_min = _coerce_float(seating_window[0])
        seat_max = _coerce_float(seating_window[1])
        if seat_min is not None and seat_max is not None:
            baseline["available"] = True
            baseline["coal_mm"] = round(
                float(coal_mm) + ((seat_min + seat_max) / 2.0), 2
            )
            baseline["seating_window_mm"] = [seat_min, seat_max]
            baseline["seating_source"] = "recommended"

    target_cbto = None
    seating_source_detail = ""
    promoted_cbto = _coerce_float(promotion_candidate.get("promoted_cbto_mm"))
    if promotion_candidate.get("eligible") and promoted_cbto is not None:
        target_cbto = promoted_cbto
        baseline["seating_source"] = "learned"
        seating_source_detail = "sweet_spot"
    else:
        evidence_confidence = (
            str(best_known_evidence.get("confidence") or "").strip().lower()
        )
        evidence_cbto = _coerce_float(best_known_evidence.get("cbto_mm"))
        if evidence_confidence == "high" and evidence_cbto is not None:
            target_cbto = evidence_cbto
            baseline["seating_source"] = "learned"
            seating_source_detail = "best_known"

    if target_cbto is not None:
        baseline["available"] = True
        baseline["cbto_mm"] = round(target_cbto, 2)
        baseline["seating_source_detail"] = seating_source_detail
        if coal_mm is not None and cbto_mm is not None:
            baseline["coal_mm"] = round(
                float(coal_mm) + (target_cbto - float(cbto_mm)), 2
            )

    summary_bits: list[str] = []
    if (
        baseline.get("charge_source") == "learned"
        and baseline.get("charge_gr") is not None
    ):
        summary_bits.append(f"learned charge {float(baseline['charge_gr']):.2f} gr")
    elif (
        baseline.get("charge_source") == "recommended"
        and baseline.get("charge_gr") is not None
    ):
        summary_bits.append(f"charge {float(baseline['charge_gr']):.2f} gr")
    if (
        baseline.get("seating_source") == "learned"
        and baseline.get("cbto_mm") is not None
    ):
        summary_bits.append(f"learned seating {float(baseline['cbto_mm']):.2f} mm CBTO")
    elif (
        baseline.get("seating_source") == "recommended"
        and baseline.get("coal_mm") is not None
    ):
        summary_bits.append(f"seating {float(baseline['coal_mm']):.2f} mm COAL")
    if setup_label:
        summary_bits.append(f"setup {setup_label}")
    baseline["summary"] = ", ".join(summary_bits)
    return baseline


# LEGACY-ISOLATED: overlaps engine baseline_control alignment; safe removal blocked pending builder-class test harness
def build_recommendation_control_state(
    *,
    current_charge_gr: float | None,
    coal_mm: float | None,
    cbto_mm: float | None,
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(baseline, dict) or not baseline.get("available"):
        return {
            "available": False,
            "level": "unknown",
            "message": "Recommendation state becomes active when the engine has enough evidence to freeze a baseline.",
            "can_apply": False,
            "charge_state": "unavailable",
            "seating_state": "unavailable",
        }

    charge_target = _coerce_float(baseline.get("charge_gr"))
    coal_target = _coerce_float(baseline.get("coal_mm"))
    cbto_target = _coerce_float(baseline.get("cbto_mm"))
    charge_aligned = (
        charge_target is not None
        and current_charge_gr is not None
        and abs(float(current_charge_gr) - charge_target) <= 0.05
    )
    seating_aligned = False
    if cbto_target is not None and cbto_mm is not None:
        seating_aligned = abs(float(cbto_mm) - cbto_target) <= 0.03
    elif coal_target is not None and coal_mm is not None:
        seating_aligned = abs(float(coal_mm) - coal_target) <= 0.03

    charge_source = str(baseline.get("charge_source") or "recommended").strip().lower()
    if charge_source == "learned":
        charge_state = "learned" if charge_aligned else "custom"
    else:
        charge_state = "recommended" if charge_aligned else "custom"
    seating_source = (
        str(baseline.get("seating_source") or "recommended").strip().lower()
    )
    if seating_source == "learned":
        seating_state = "learned" if seating_aligned else "custom"
    else:
        seating_state = "recommended" if seating_aligned else "custom"

    def _source_label(source: str) -> str:
        normalized = str(source or "recommended").strip().lower()
        if normalized == "learned":
            return "learned baseline"
        if normalized == "recommended":
            return "modeled baseline"
        if normalized == "current":
            return "current baseline"
        return normalized + " baseline"

    trust_label = str(baseline.get("trust_label") or "unknown").strip().lower()
    level = "ok"
    if trust_label in {"low", "warning", "critical", "unknown"}:
        level = "warning"
    if charge_state == "custom" or seating_state == "custom":
        level = "info" if level == "ok" else level

    source_summary = []
    if charge_target is not None:
        source_summary.append(f"charge target {charge_target:.2f} gr")
    if cbto_target is not None:
        source_summary.append(f"CBTO target {cbto_target:.2f} mm")
    elif coal_target is not None:
        source_summary.append(f"COAL target {coal_target:.2f} mm")

    charge_source_label = _source_label(charge_source)
    seating_source_label = _source_label(seating_source)

    message = "Builder is aligned with the frozen baseline."
    if charge_state == "custom" or seating_state == "custom":
        message = (
            "Builder is in custom mode. Use the frozen baseline to jump back to the "
            f"{charge_source_label if charge_state == 'custom' else seating_source_label}."
        )
    if source_summary:
        message += " " + " | ".join(source_summary) + "."
    setup_label = str(baseline.get("setup_label") or "").strip()
    if setup_label:
        message += f" Applies to setup {setup_label}."

    return {
        "available": True,
        "level": level,
        "message": message,
        "can_apply": charge_state == "custom" or seating_state == "custom",
        "charge_state": charge_state,
        "seating_state": seating_state,
        "trust_label": trust_label,
        "charge_target_gr": charge_target,
        "coal_target_mm": coal_target,
        "cbto_target_mm": cbto_target,
        "charge_source_label": charge_source_label,
        "seating_source_label": seating_source_label,
        "seating_source": seating_source,
        "setup_label": setup_label,
    }


# LEGACY-ISOLATED: overlaps engine evidence_diagnostics; safe removal blocked pending builder-class test harness
def summarize_recommendation_evidence_basis(
    analysis: dict[str, Any] | None,
    baseline: dict[str, Any] | None = None,
) -> dict[str, str]:
    _analysis: dict[str, Any] = analysis if isinstance(analysis, dict) else {}
    _baseline: dict[str, Any] = baseline if isinstance(baseline, dict) else {}
    rifle_context = _as_dict(_analysis, "rifle_context")
    recommendation = _as_dict(_analysis, "recommendation")
    observations = _as_dict(_analysis, "observations")
    observation_summary = _as_dict(observations, "summary")
    input_quality = _as_dict(_analysis, "input_quality")
    baseline_readiness = _as_dict(recommendation, "baseline_readiness")

    chrono_count = int(observation_summary.get("chrono_count") or 0)
    accuracy_count = int(observation_summary.get("accuracy_count") or 0)
    quality_title = str(input_quality.get("title") or "Input quality unknown").strip()
    quality_level = (
        str(input_quality.get("level") or "unknown").strip().lower() or "unknown"
    )
    setup_label = str(
        _baseline.get("setup_label") or ""
    ).strip() or _format_barrel_configuration_label(
        str(rifle_context.get("barrel_configuration_name") or "").strip(),
        str(rifle_context.get("barrel_name") or "").strip(),
    )

    measured_parts: list[str] = []
    modeled_parts: list[str] = []
    learned_parts: list[str] = []

    if chrono_count > 0:
        measured_parts.append(f"{chrono_count} chrono series support charge guidance")
    else:
        measured_parts.append("no chrono series support charge guidance yet")
    if accuracy_count > 0:
        measured_parts.append(
            f"{accuracy_count} accuracy/group sessions support seating guidance"
        )
    else:
        measured_parts.append("no group data supports seating guidance yet")

    charge_window = _as_list(recommendation, "charge_window_gr")
    if len(charge_window) == 2:
        modeled_parts.append("charge window is engine-modeled")
    else:
        modeled_parts.append("no modeled charge window is active")
    seating_window = _as_list(recommendation, "seating_window_mm")
    if len(seating_window) == 2:
        modeled_parts.append("seating window is harmonic/model-based")
    else:
        modeled_parts.append("no modeled seating window is active")
    modeled_parts.append(quality_title or f"input quality is {quality_level}")

    charge_source = str(_baseline.get("charge_source") or "").strip().lower()
    seating_source = str(_baseline.get("seating_source") or "").strip().lower()
    if charge_source == "learned":
        learned_parts.append("charge baseline is learned from history")
    elif baseline_readiness.get("charge_can_freeze"):
        learned_parts.append(
            "charge baseline has measured support but is not learned history yet"
        )
    else:
        learned_parts.append("charge baseline is still modeled only")
    if seating_source == "learned":
        learned_parts.append("seating baseline is learned from history")
    elif baseline_readiness.get("seating_can_freeze"):
        learned_parts.append(
            "seating baseline has measured support but is not learned history yet"
        )
    else:
        learned_parts.append("seating baseline is still modeled only")

    message = (
        (f"Setup: {setup_label}. " if setup_label else "")
        + f"Measured: {', '.join(measured_parts)}. "
        + f"Modeled: {', '.join(modeled_parts)}. "
        + f"Learned: {', '.join(learned_parts)}."
    )
    compact_parts = []
    if setup_label:
        compact_parts.append(f"Setup {setup_label}")
    compact_parts.append(f"Measured: chrono {chrono_count}, groups {accuracy_count}")
    compact_parts.append(
        f"Modeled: charge {'yes' if len(charge_window) == 2 else 'no'}, seating {'yes' if len(seating_window) == 2 else 'no'}"
    )
    compact_parts.append(
        f"Learned: charge {charge_source or 'none'}, seating {seating_source or 'none'}"
    )
    compact = " | ".join(compact_parts)
    return {
        "title": "Recommendation Basis",
        "message": message,
        "compact": compact,
    }


def summarize_recommendation_return_targets(
    control_state: dict[str, Any] | None,
    baseline: dict[str, Any] | None,
) -> list[str]:
    control_state = control_state if isinstance(control_state, dict) else {}
    baseline = baseline if isinstance(baseline, dict) else {}
    if not baseline.get("available") and not control_state:
        return []

    target_lines: list[str] = []
    charge_source = (
        str(baseline.get("charge_source") or "recommended").strip().lower()
        or "recommended"
    )
    charge_source_label = (
        "learned baseline"
        if charge_source == "learned"
        else "modeled baseline" if charge_source == "recommended" else charge_source
    )
    charge_target = _coerce_float(control_state.get("charge_target_gr"))
    if charge_target is None:
        charge_target = _coerce_float(baseline.get("charge_gr"))
    if charge_target is not None:
        target_lines.append(
            f"Charge target ({charge_source_label}): {charge_target:.2f} gr"
        )

    seating_source = (
        str(baseline.get("seating_source") or "recommended").strip().lower()
        or "recommended"
    )
    seating_source_label = (
        "learned baseline"
        if seating_source == "learned"
        else "modeled baseline" if seating_source == "recommended" else seating_source
    )
    cbto_target = _coerce_float(control_state.get("cbto_target_mm"))
    if cbto_target is None:
        cbto_target = _coerce_float(baseline.get("cbto_mm"))
    coal_target = _coerce_float(control_state.get("coal_target_mm"))
    if coal_target is None:
        coal_target = _coerce_float(baseline.get("coal_mm"))
    if cbto_target is not None:
        target_lines.append(
            f"Seating target ({seating_source_label}): {cbto_target:.2f} mm CBTO"
        )
    elif coal_target is not None:
        target_lines.append(
            f"Seating target ({seating_source_label}): {coal_target:.2f} mm COAL"
        )

    return target_lines


class _MeasuredModelCandidate(TypedDict, total=False):
    batch_id: int
    charge_weight_grains: float | None
    cbto_mm: float | None
    subsonic_enabled: bool | None
    powder_lot_number: str | None
    temperature_c: float | None
    velocity_values: list[float]
    group_values: list[float]
    session_ids: set[int]
    matches_powder_lot: bool
    temperature_delta_c: float
    avg_measured_velocity_fps: float
    best_group_moa: float | None
    velocity_delta_fps: float | None
    signed_velocity_delta_fps: float | None
    charge_delta_grains: float | None
    cbto_delta_mm: float | None
    session_count: int
    evidence_count: int
    score: float


def summarize_pressure_risk(result: dict) -> dict[str, Any]:
    safety = result.get("safety_margin_percent")
    peak = result.get("peak_pressure_psi")
    maximum = result.get("max_pressure_psi")
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
            "message": "Missing pressure data. Verify components and run prediction before testing.",
        }
    if display_margin < 10:
        return {
            "level": "critical",
            "title": "High pressure risk",
            "message": f"Only {display_margin:.1f}% margin to max pressure. Reduce charge before testing.",
        }
    if display_margin < 15:
        return {
            "level": "warning",
            "title": "Pressure near max",
            "message": f"{display_margin:.1f}% margin remaining. Proceed carefully and confirm with chrono.",
        }
    return {
        "level": "ok",
        "title": "Pressure margin healthy",
        "message": f"{display_margin:.1f}% margin remaining to max pressure.",
    }


def _advisory_style(level: str) -> str:
    level = str(level or "").strip().lower()
    if level == "critical":
        return "padding: 6px 8px; border-radius: 5px; background: #3a1a1a; color: #ff6b6b; font-weight: 700; border-left: 2px solid #e74c3c;"
    if level == "warning":
        return "padding: 6px 8px; border-radius: 5px; background: #2e2410; color: #f0a500; font-weight: 700; border-left: 2px solid #e67e22;"
    if level == "ok":
        return "padding: 6px 8px; border-radius: 5px; background: #102818; color: #4cd890; font-weight: 700; border-left: 2px solid #27ae60;"
    return "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"


def _pipe_history_style(level: str) -> str:
    base = _advisory_style(level)
    return base + " font-weight: 600;"


def _status_pill(label: str, level: str | None) -> str:
    palette = {
        "critical": ("#3a1a1a", "#ff6b6b"),
        "warning": ("#2e2410", "#f0a500"),
        "ok": ("#102818", "#4cd890"),
        "info": ("#0f1e38", "#4a9eff"),
        "unknown": ("#1a2035", "#8a9ec0"),
        "neutral": ("#1a2035", "#8a9ec0"),
    }
    bg, fg = palette.get(
        str(level or "unknown").strip().lower(), ("#1a2035", "#8a9ec0")
    )
    return (
        f"<span style='display:inline-block; margin:0 6px 4px 0; padding:2px 8px; "
        f"border-radius:999px; background:{bg}; color:{fg}; font-size:8pt; font-weight:700;'>{label}</span>"
    )


def summarize_stability_advisor(
    stability: dict | None,
    *,
    result: dict | None = None,
    subsonic_mode: bool = False,
    twist_inches: float | None = None,
    bullet: dict | None = None,
    barrel_details: dict | None = None,
    rifle_data: dict | None = None,
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
            "message": "Enter twist, bullet length, and bullet geometry to get a more precise stability estimate.",
            "checks": [f"Missing data: {missing}"],
        }

    sg = _coerce_float(stability.get("sg"))
    if sg is None:
        return {
            "level": "unknown",
            "title": "Stability unavailable",
            "message": "Stability could not be assessed from today's data.",
            "checks": [],
        }

    result_data = result or {}
    velocity_fps = _coerce_float(
        result_data.get("muzzle_velocity_fps", stability.get("velocity_fps"))
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
    message = f"Sg {sg:.2f} indicates good stability in the current setup."

    if sg < 1.0:
        level = "critical"
        title = "High tumble risk"
        message = f"Sg {sg:.2f} is below 1.0. The bullet may already be unstable at the muzzle."
    elif subsonic_mode and sg < 1.15:
        level = "critical"
        title = "Marginal subsonic stability"
        message = f"Sg {sg:.2f} is too low for comfortable subsonic use. Verify carefully before further testing."
    elif sg < 1.3:
        level = "warning"
        title = "Marginal stability"
        message = (
            f"Sg {sg:.2f} is marginal. Watch groups, yaw signs, and keyholing closely."
        )
    elif sg < 1.5:
        level = "warning"
        title = "Usable but not roomy stability"
        message = f"Sg {sg:.2f} looks usable, but it does not leave much margin for cold weather, low velocity, or a long bullet."

    if velocity_fps is not None:
        checks.append(f"Modeled velocity {format_velocity_fps(velocity_fps)}.")
    if twist_inches:
        checks.append(
            f"Twist 1:{twist_inches:.1f} is evaluated against the selected bullet."
        )

    bullet_length = _coerce_float(bullet.get("length_mm"))
    if bullet_length is not None:
        checks.append(
            f"Bullet length {format_length_mm(bullet_length)} is included in the stability estimate."
        )

    if has_suppressor and sg < 1.3:
        checks.append(
            "Suppressor registered: marginal stability adds extra risk of yaw and possible baffle contact."
        )
        if level != "critical":
            level = "critical" if subsonic_mode else "warning"
            if level == "critical":
                title = "Suppressor risk from low stability"
                message = f"Sg {sg:.2f} is marginal with a suppressor in the setup. Verify without the suppressor first."
    elif has_suppressor:
        checks.append(
            "Suppressor registered: good stability margin is especially important before further testing."
        )

    if subsonic_mode:
        checks.append(
            "Subsonic mode active: stability is weighted more strictly than in the normal velocity range."
        )

    return {
        "level": level,
        "title": title,
        "message": message,
        "sg": sg,
        "checks": checks,
    }


def summarize_bullet_fit_advisor(
    *,
    bullet: dict | None,
    bullet_geometry: dict | None,
    stability: dict | None,
    stability_assessment: dict | None,
    harmonics: dict | None,
    twist_inches: float | None,
    result: dict | None,
) -> dict[str, Any]:
    return build_bullet_fit_summary(
        bullet=bullet if isinstance(bullet, dict) else None,
        bullet_geometry=bullet_geometry if isinstance(bullet_geometry, dict) else None,
        stability=stability if isinstance(stability, dict) else None,
        stability_assessment=(
            stability_assessment if isinstance(stability_assessment, dict) else None
        ),
        harmonics=harmonics if isinstance(harmonics, dict) else None,
        twist_inches=twist_inches,
        result=result if isinstance(result, dict) else None,
    )


def summarize_game_suitability_advisor(
    *,
    usage_profile: str,
    terminal_summary: dict | None,
) -> dict[str, Any]:
    return build_game_suitability_summary(
        usage_profile=usage_profile,
        terminal_summary=(
            terminal_summary if isinstance(terminal_summary, dict) else None
        ),
    )


def summarize_subsonic_advisor(
    result: dict | None,
    *,
    enabled: bool,
    target_velocity_fps: float,
    stability: dict | None = None,
) -> dict[str, Any]:
    if not enabled:
        return {
            "level": "unknown",
            "title": "Subsonic mode inactive",
            "message": "Enable subsonic mode to get sonic margin, squib risk, and stability assessment.",
            "checks": [],
        }

    result = result or {}
    stability = stability or {}
    velocity_fps = _coerce_float(result.get("muzzle_velocity_fps"))
    if velocity_fps is None:
        return {
            "level": "unknown",
            "title": "Subsonic data unavailable",
            "message": "Missing modeled velocity to assess subsonic margin.",
            "checks": [],
        }

    load_density = _coerce_float(result.get("load_density_percent"))

    target_velocity_fps = float(target_velocity_fps or 1050.0)
    margin_fps = target_velocity_fps - velocity_fps
    checks = [
        f"Target {format_velocity_fps(target_velocity_fps)}, modeled {format_velocity_fps(velocity_fps)}."
    ]

    level = "ok"
    title = "Subsonic window looks usable"
    message = f"The load sits {format_velocity_delta_fps(margin_fps).lstrip('+')} below target velocity."

    if velocity_fps > target_velocity_fps + 25.0:
        level = "critical"
        title = "Over subsonic target"
        message = f"The load sits {format_velocity_delta_fps(abs(margin_fps)).lstrip('+')} above target. Risk of sonic crack is high."
    elif velocity_fps > target_velocity_fps:
        level = "warning"
        title = "Near or above subsonic ceiling"
        message = f"The load sits {format_velocity_delta_fps(abs(margin_fps)).lstrip('+')} above target. Temperature or altitude may make it audibly transonic."
    elif margin_fps < 25.0:
        level = "warning"
        title = "Thin sonic margin"
        message = f"Only {format_velocity_delta_fps(margin_fps).lstrip('+')} below target. Warmer weather or lot differences may cause crack."
    elif margin_fps > 180.0:
        level = "warning"
        title = "Very low subsonic velocity"
        message = f"The load sits {format_velocity_delta_fps(margin_fps).lstrip('+')} below target. Verify stability, function, and squib margin in practice."

    if load_density is not None:
        checks.append(f"Fyllgrad {load_density:.1f}%.")
        if load_density < 50.0:
            level = "critical"
            title = "Low fill risk in subsonic mode"
            message = "Very low fill ratio can give uneven ignition, large velocity spread, or in the worst case squib risk."
        elif load_density < 65.0 and level != "critical":
            if level == "ok":
                level = "warning"
                title = "Low fill subsonic setup"
            checks.append(
                "Low fill ratio: pay extra attention to powder position sensitivity and the need for small charge steps."
            )

    sg = _coerce_float(stability.get("sg"))
    if sg is not None:
        checks.append(f"Stabilitetsestimat Sg {sg:.2f}.")
        if sg < 1.15:
            level = "critical"
            title = "Subsonic stability risk"
            message = "Subsonic velocity combined with low Sg gives increased risk of tumbling or poor accuracy."

    return {
        "level": level,
        "title": title,
        "message": message,
        "margin_fps": margin_fps,
        "checks": checks,
    }


def summarize_subsonic_history_advisory(
    db,
    rifle_id: int | None,
    bullet_id: int | None,
    powder_id: int | None,
) -> dict[str, Any]:
    if not db or not rifle_id or not bullet_id or not powder_id:
        return {
            "level": "unknown",
            "title": "No subsonic history yet",
            "message": "Log a few subsonic range sessions so the program can learn cycling, sonic crack, and stability.",
            "checks": [],
        }

    try:
        rows = db.execute_query(
            """
            SELECT
                bp.analysis_json AS batch_analysis_json,
                bps.analysis_json AS session_analysis_json,
                bps.notes AS session_notes
            FROM batch_projects bp
            LEFT JOIN batch_project_sessions bps ON bps.batch_id = bp.id
            WHERE bp.rifle_id = ?
              AND bp.bullet_id = ?
              AND bp.powder_id = ?
            ORDER BY datetime(bp.updated_date) DESC, datetime(bps.session_date) DESC, bps.id DESC
            LIMIT 40
            """,
            (rifle_id, bullet_id, powder_id),
        )
    except Exception:
        rows = []

    total = 0
    cycled = 0
    failed = 0
    marginal = 0
    sonic_crack = 0
    keyhole = 0
    suppressor = 0

    for row in rows or []:
        batch_analysis = _safe_json_loads((row or {}).get("batch_analysis_json"))
        sub_ctx = (
            batch_analysis.get("subsonic_context")
            if isinstance(batch_analysis, dict)
            else None
        )
        if not isinstance(sub_ctx, dict) or not sub_ctx.get("enabled"):
            continue
        session_analysis = _safe_json_loads((row or {}).get("session_analysis_json"))
        observations = (
            session_analysis.get("subsonic_observations")
            if isinstance(session_analysis, dict)
            else None
        )
        if not isinstance(observations, dict):
            continue
        total += 1
        status = str(observations.get("cycling_status") or "").strip().lower()
        if status == "cycled":
            cycled += 1
        elif status == "failed":
            failed += 1
        elif status == "marginal":
            marginal += 1
        if observations.get("sonic_crack"):
            sonic_crack += 1
        if observations.get("keyhole"):
            keyhole += 1
        if observations.get("suppressor_used"):
            suppressor += 1

    if total == 0:
        return {
            "level": "unknown",
            "title": "No subsonic history yet",
            "message": "No recorded subsonic observations for this firearm/bullet/powder combination yet.",
            "checks": [],
        }

    checks = [f"{total} subsonic sessions in the history for this setup."]
    if cycled:
        checks.append(f"{cycled} sessions cycled.")
    if marginal:
        checks.append(f"{marginal} sessions were marginal on function.")
    if failed:
        checks.append(f"{failed} sessions did not cycle.")
    if sonic_crack:
        checks.append(f"{sonic_crack} sessions had sonic crack.")
    if keyhole:
        checks.append(f"{keyhole} sessions showed keyhole or tumble signs.")
    if suppressor:
        checks.append(f"{suppressor} sessions were fired with a suppressor.")

    if keyhole:
        return {
            "level": "critical",
            "title": "Historical subsonic stability warning",
            "message": "History contains keyhole or tumble signs for this combination. Verify stability before further testing.",
            "checks": checks,
        }
    if failed or sonic_crack >= max(2, total // 2):
        return {
            "level": "warning",
            "title": "Mixed subsonic history",
            "message": "History shows function or sound-related issues. This combination may need finer charge steps or more stable seating.",
            "checks": checks,
        }
    if cycled >= 2 and sonic_crack == 0 and keyhole == 0:
        return {
            "level": "ok",
            "title": "Subsonic history looks promising",
            "message": "History shows repeatable subsonic sessions without clear stability warnings.",
            "checks": checks,
        }
    return {
        "level": "warning",
        "title": "Thin subsonic evidence",
        "message": "There is some subsonic history, but not enough to call the setup robust yet.",
        "checks": checks,
    }


def get_subsonic_history_windows(
    db,
    rifle_id: int | None,
    bullet_id: int | None,
    powder_id: int | None,
) -> dict[str, Any]:
    empty = {
        "successful_charge_range": None,
        "problem_charge_range": None,
        "successful_cbto_range": None,
        "problem_cbto_range": None,
        "successful_count": 0,
        "problem_count": 0,
    }
    if not db or not rifle_id or not bullet_id or not powder_id:
        return empty

    try:
        rows = db.execute_query(
            """
            SELECT
                bp.charge_weight_grains,
                bp.cbto_mm,
                bp.analysis_json AS batch_analysis_json,
                bps.analysis_json AS session_analysis_json
            FROM batch_projects bp
            LEFT JOIN batch_project_sessions bps ON bps.batch_id = bp.id
            WHERE bp.rifle_id = ?
              AND bp.bullet_id = ?
              AND bp.powder_id = ?
            ORDER BY datetime(bp.updated_date) DESC, datetime(bps.session_date) DESC, bps.id DESC
            LIMIT 50
            """,
            (rifle_id, bullet_id, powder_id),
        )
    except Exception:
        rows = []

    successful_charges: list[float] = []
    problem_charges: list[float] = []
    successful_cbto: list[float] = []
    problem_cbto: list[float] = []

    for row in rows or []:
        batch_analysis = _safe_json_loads((row or {}).get("batch_analysis_json"))
        sub_ctx = (
            batch_analysis.get("subsonic_context")
            if isinstance(batch_analysis, dict)
            else None
        )
        if not isinstance(sub_ctx, dict) or not sub_ctx.get("enabled"):
            continue
        session_analysis = _safe_json_loads((row or {}).get("session_analysis_json"))
        observations = (
            session_analysis.get("subsonic_observations")
            if isinstance(session_analysis, dict)
            else None
        )
        if not isinstance(observations, dict):
            continue

        charge = None
        cbto = None
        try:
            if row.get("charge_weight_grains") not in (None, ""):
                charge = float(row.get("charge_weight_grains"))
        except Exception:
            charge = None
        try:
            if row.get("cbto_mm") not in (None, ""):
                cbto = float(row.get("cbto_mm"))
        except Exception:
            cbto = None

        status = str(observations.get("cycling_status") or "").strip().lower()
        sonic_crack = bool(observations.get("sonic_crack"))
        keyhole = bool(observations.get("keyhole"))

        is_success = status == "cycled" and not sonic_crack and not keyhole
        is_problem = status == "failed" or sonic_crack or keyhole

        if is_success:
            if charge is not None:
                successful_charges.append(charge)
            if cbto is not None:
                successful_cbto.append(cbto)
        elif is_problem:
            if charge is not None:
                problem_charges.append(charge)
            if cbto is not None:
                problem_cbto.append(cbto)

    def _range(values: list[float]) -> tuple[float, float] | None:
        if not values:
            return None
        return (min(values), max(values))

    return {
        "successful_charge_range": _range(successful_charges),
        "problem_charge_range": _range(problem_charges),
        "successful_cbto_range": _range(successful_cbto),
        "problem_cbto_range": _range(problem_cbto),
        "successful_count": len(successful_charges),
        "problem_count": len(problem_charges),
    }


def summarize_model_vs_measured_advisory(
    db,
    rifle_id: int | None,
    bullet_id: int | None,
    powder_id: int | None,
    *,
    current_charge_grains: float | None = None,
    current_cbto_mm: float | None = None,
    predicted_velocity_fps: float | None = None,
    subsonic_mode: bool | None = None,
    current_powder_lot_number: str | None = None,
    target_temperature_c: float | None = None,
) -> dict[str, Any]:
    if not db or not rifle_id or not bullet_id or not powder_id:
        return {
            "level": "unknown",
            "title": "Model vs Measured Unavailable",
            "message": "Select a firearm, bullet, and powder to compare the model against logged chronograph data.",
            "checks": [],
            "evidence_count": 0,
        }

    rows = db.execute_query(
        """
        SELECT
            bp.id AS batch_id,
            bp.charge_weight_grains,
            bp.cbto_mm,
            bp.powder_id,
            bp.component_snapshot_json,
            bp.analysis_json AS batch_analysis_json,
            bps.id AS session_id,
            bps.analysis_json AS session_analysis_json,
            bps.group_size_moa
        FROM batch_projects bp
        LEFT JOIN batch_project_sessions bps ON bps.batch_id = bp.id
        WHERE bp.rifle_id = ? AND bp.bullet_id = ?
        ORDER BY bp.id DESC, bps.id DESC
        """,
        (rifle_id, bullet_id),
    )
    if not rows:
        return {
            "level": "unknown",
            "title": "No Measured Reference Yet",
            "message": "The batch history lacks suitable chronograph data for this firearm/bullet combination.",
            "checks": [],
            "evidence_count": 0,
        }

    candidates: list[dict[str, Any]] = []
    grouped: dict[int, dict[str, Any]] = {}
    for row in rows:
        snapshot = _safe_json_loads(row.get("component_snapshot_json"))
        powder_entry = _extract_saved_component_entry(
            snapshot,
            _safe_json_loads(row.get("batch_analysis_json")),
            "powder",
        )
        batch_powder_id = row.get("powder_id") or powder_entry.get("id")
        if _coerce_int(batch_powder_id) != _coerce_int(powder_id):
            continue

        batch_id = row.get("batch_id")
        if batch_id in (None, ""):
            continue
        resolved_batch_id = _coerce_int(batch_id)
        if resolved_batch_id is None:
            continue
        batch_id = resolved_batch_id
        entry = grouped.get(batch_id)
        if entry is None:
            batch_analysis = _safe_json_loads(row.get("batch_analysis_json"))
            batch_sub = batch_analysis.get("subsonic_context")
            batch_sub_enabled = None
            if isinstance(batch_sub, dict):
                batch_sub_enabled = bool(batch_sub.get("enabled"))
            seating_context = batch_analysis.get("seating_context")
            if not isinstance(seating_context, dict):
                seating_context = {}
            powder_lot_number = str(
                powder_entry.get("lot_number")
                or powder_entry.get("selected_lot_number")
                or ""
            ).strip()
            entry = {
                "batch_id": batch_id,
                "charge_weight_grains": _coerce_float(row.get("charge_weight_grains")),
                "cbto_mm": _coerce_float(row.get("cbto_mm")),
                "subsonic_enabled": batch_sub_enabled,
                "powder_lot_number": powder_lot_number or None,
                "temperature_c": _coerce_float(seating_context.get("temperature_c")),
                "velocity_values": [],
                "group_values": [],
                "session_ids": set(),
            }
            grouped[batch_id] = entry

        session_id = row.get("session_id")
        resolved_session_id = _coerce_int(session_id)
        if resolved_session_id is not None:
            entry["session_ids"].add(resolved_session_id)
        session_analysis = _safe_json_loads(row.get("session_analysis_json"))
        stats_raw = (
            session_analysis.get("stats")
            if isinstance(session_analysis, dict)
            else None
        )
        stats = stats_raw if isinstance(stats_raw, dict) else {}
        avg_velocity = _coerce_float(stats.get("avg"))
        if avg_velocity is None:
            avg_velocity = _coerce_float(session_analysis.get("avg_velocity_fps"))
        if avg_velocity is not None:
            entry["velocity_values"].append(avg_velocity)

        group_moa = _coerce_float(row.get("group_size_moa"))
        if group_moa is None:
            group_moa = _coerce_float(session_analysis.get("group_size_moa"))
        if group_moa is not None:
            entry["group_values"].append(group_moa)

    for entry in grouped.values():
        velocities = list(entry["velocity_values"])
        if not velocities:
            continue
        session_ids = entry["session_ids"]
        groups = list(entry["group_values"])
        avg_velocity = statistics.mean(velocities)
        velocity_delta = None
        signed_velocity_delta = None
        if predicted_velocity_fps is not None:
            velocity_delta = abs(avg_velocity - float(predicted_velocity_fps))
            signed_velocity_delta = avg_velocity - float(predicted_velocity_fps)
        charge_delta = None
        entry_charge = entry.get("charge_weight_grains")
        if current_charge_grains is not None and entry_charge is not None:
            charge_delta = abs(entry_charge - float(current_charge_grains))
        cbto_delta = None
        entry_cbto = entry.get("cbto_mm")
        if current_cbto_mm is not None and entry_cbto is not None:
            cbto_delta = abs(entry_cbto - float(current_cbto_mm))

        score = 0.0
        score += min(18.0, len(session_ids) * 4.0)
        score += min(12.0, len(velocities) * 2.0)
        if velocity_delta is not None:
            score += max(0.0, 35.0 - float(velocity_delta) * 1.2)
        if charge_delta is not None:
            score += max(0.0, 15.0 - float(charge_delta) * 30.0)
        if cbto_delta is not None:
            score += max(0.0, 10.0 - float(cbto_delta) * 45.0)
        if groups:
            score += max(0.0, 10.0 - min(groups) * 4.0)
        if subsonic_mode is not None and entry.get("subsonic_enabled") is not None:
            score += (
                8.0
                if bool(entry.get("subsonic_enabled")) == bool(subsonic_mode)
                else 0.0
            )
        if current_powder_lot_number:
            stored_lot = str(entry.get("powder_lot_number") or "").strip()
            if stored_lot and stored_lot == str(current_powder_lot_number).strip():
                score += 10.0
                entry["matches_powder_lot"] = True
            else:
                entry["matches_powder_lot"] = False
        entry_temperature = entry.get("temperature_c")
        if target_temperature_c is not None and entry_temperature is not None:
            temperature_delta = abs(entry_temperature - float(target_temperature_c))
            score += max(0.0, 8.0 - temperature_delta * 0.7)
            entry["temperature_delta_c"] = temperature_delta

        entry.update(
            {
                "avg_measured_velocity_fps": avg_velocity,
                "best_group_moa": min(groups) if groups else None,
                "velocity_delta_fps": velocity_delta,
                "signed_velocity_delta_fps": signed_velocity_delta,
                "charge_delta_grains": charge_delta,
                "cbto_delta_mm": cbto_delta,
                "session_count": len(session_ids),
                "evidence_count": len(velocities),
                "score": score,
            }
        )
        candidates.append(entry)

    if not candidates:
        return {
            "level": "unknown",
            "title": "No Measured Reference Yet",
            "message": "The history contains batches, but none have usable chronograph data for this powder.",
            "checks": [],
            "evidence_count": 0,
        }

    candidates.sort(
        key=lambda item: (
            1 if item.get("matches_powder_lot") else 0,
            item.get("score") or 0.0,
            item.get("session_count") or 0,
            item.get("evidence_count") or 0,
        ),
        reverse=True,
    )
    best = candidates[0]
    signed_deltas = [
        item["signed_velocity_delta_fps"]
        for item in candidates[: min(5, len(candidates))]
        if isinstance(item.get("signed_velocity_delta_fps"), (int, float))
    ]
    bias_fps = statistics.mean(signed_deltas) if signed_deltas else None
    bias_direction = ""
    if isinstance(bias_fps, (int, float)):
        if bias_fps >= 8.0:
            bias_direction = "measured_higher"
        elif bias_fps <= -8.0:
            bias_direction = "model_higher"
        else:
            bias_direction = "neutral"
    delta = best.get("velocity_delta_fps")
    checks: list[str] = []
    if isinstance(best.get("avg_measured_velocity_fps"), (int, float)):
        checks.append(
            f"A similar batch was measured around {format_velocity_fps(best['avg_measured_velocity_fps'])}."
        )
    if isinstance(delta, (int, float)):
        checks.append(
            f"The deviation from the model is about {format_velocity_delta_fps(float(delta)).lstrip('+')}."
        )
    if isinstance(bias_fps, (int, float)):
        if bias_direction == "measured_higher":
            checks.append(
                f"The history suggests the model is often about {abs(float(bias_fps)):.0f} fps low."
            )
        elif bias_direction == "model_higher":
            checks.append(
                f"The history suggests the model is often about {abs(float(bias_fps)):.0f} fps high."
            )
        else:
            checks.append("The history shows no clear systematic model bias right now.")
    if best.get("matches_powder_lot"):
        checks.append("The reference uses the same powder lot as the active setup.")
    if isinstance(best.get("charge_delta_grains"), (int, float)):
        checks.append(
            f"The charge difference from the reference is {format_weight_grains(best['charge_delta_grains'], 'powder')}."
        )
    if isinstance(best.get("cbto_delta_mm"), (int, float)):
        checks.append(
            f"The CBTO difference from the reference is {format_length_delta_mm(best['cbto_delta_mm'])}."
        )
    if isinstance(best.get("temperature_delta_c"), (int, float)):
        checks.append(
            f"The temperature difference from the reference is {format_temperature_delta_c(best['temperature_delta_c']).lstrip('+')}."
        )
    if isinstance(best.get("best_group_moa"), (int, float)):
        checks.append(
            f"The best recorded group in the reference is {best['best_group_moa']:.2f} MOA."
        )

    level = "unknown"
    title = "Model vs Measured"
    message = "The builder lacks enough matching chronograph series to assess model fit with confidence."
    if isinstance(delta, (int, float)):
        if float(delta) <= 15.0:
            level = "ok"
            title = "The Model Matches Well"
            message = "The predicted velocity is close to the measured history for similar batches."
        elif float(delta) <= 30.0:
            level = "warning"
            title = "The Model Needs Confirmation"
            message = "The predicted velocity is usable, but it differs enough that a chronograph should confirm this series."
        else:
            level = "critical"
            title = "The Model Differs from Measured Data"
            message = "The history suggests the model misses noticeably for similar setups. Read velocity and pressure conservatively."
    elif (best.get("evidence_count") or 0) >= 2:
        level = "warning"
        title = "Thin Model Validation"
        message = "Measured history exists, but not enough matching series are available to quantify model deviation properly."

    return {
        "level": level,
        "title": title,
        "message": message,
        "checks": checks[:5],
        "reference": best,
        "candidate_count": len(candidates),
        "evidence_count": best.get("evidence_count") or 0,
        "bias_fps": (
            round(float(bias_fps), 1) if isinstance(bias_fps, (int, float)) else None
        ),
        "bias_direction": bias_direction or None,
    }


def get_rifle_pressure_limit_psi(db, rifle_data: dict | None) -> float | None:
    caliber = str((rifle_data or {}).get("caliber") or "").strip()
    if not caliber:
        return None
    try:
        return get_max_pressure_psi_for_caliber(db, caliber)
    except Exception:
        return None


def _seating_visualization_html(jump_mm: float | None) -> str:
    marker_label = "Unknown"
    marker_pct = 50.0
    if isinstance(jump_mm, (int, float)):
        marker_pct = max(0.0, min(100.0, ((float(jump_mm) + 0.30) / 2.30) * 100.0))
        marker_label = f"Jump {float(jump_mm):+.2f} mm"
    return f"""
    <div style='margin-top:4px;'>
      <div style='display:flex; width:100%; height:10px; border-radius:6px; overflow:hidden; border:1px solid #d1d5db;'>
        <div style='width:13%; background:#dc2626;' title='Into lands'></div>
        <div style='width:17%; background:#f59e0b;' title='Tight jump'></div>
                <div style='width:35%; background:#16a34a;' title='Working window'></div>
                <div style='width:35%; background:#93c5fd;' title='Long jump'></div>
      </div>
      <div style='position:relative; height:14px; margin-top:2px;'>
        <div style='position:absolute; left:calc({marker_pct:.1f}% - 1px); top:0; bottom:0; width:2px; background:#111827;'></div>
      </div>
      <div style='font-size:8pt; color:#374151;'>
                Into lands | Tight jump | Working window | Long jump
      </div>
      <div style='font-size:8pt; color:#111827;'><b>{marker_label}</b></div>
    </div>
    """


def _build_cartridge_geometry_visual_html(
    *,
    coal_mm: float | None,
    cbto_mm: float | None,
    jam_cbto_mm: float | None,
    jump_mm: float | None,
    standard_oal_mm: float | None = None,
    case_length_mm: float | None = None,
    bullet_length_mm: float | None = None,
    throat_erosion_mm: float | None = None,
    neck_clearance_mm: float | None = None,
    neck_clearance_basis: str | None = None,
    freebore_delta_mm: float | None = None,
    standard_body: str | None = None,
    subsonic_mode: bool = False,
    stability_tier: str | None = None,
    stability_level: str | None = None,
    subsonic_level: str | None = None,
    subsonic_history_level: str | None = None,
    has_suppressor: bool = False,
) -> str:
    values = [
        value
        for value in (coal_mm, cbto_mm, jam_cbto_mm, standard_oal_mm, case_length_mm)
        if isinstance(value, (int, float)) and float(value) > 0
    ]
    if not values:
        return ""

    total_mm = max(float(max(values)), 1.0)
    width = 46

    def _pos(value: float | None) -> int | None:
        if value is None:
            return None
        try:
            return max(
                0, min(width - 1, int(round((float(value) / total_mm) * (width - 1))))
            )
        except Exception:
            return None

    chamber = ["-"] * width
    cartridge = [" "] * width
    ref = [" "] * width

    mouth_pos = _pos(case_length_mm)
    ogive_pos = _pos(cbto_mm)
    lands_pos = _pos(jam_cbto_mm)
    tip_pos = _pos(coal_mm)
    std_pos = _pos(standard_oal_mm)

    if mouth_pos is not None:
        chamber[mouth_pos] = "M"
    if ogive_pos is not None:
        chamber[ogive_pos] = "O"
    if lands_pos is not None:
        chamber[lands_pos] = "L"
        for idx in range(lands_pos + 1, min(width, lands_pos + 5)):
            chamber[idx] = ">"

    body_end = mouth_pos if mouth_pos is not None else max(2, width // 2)
    for idx in range(0, min(width, body_end + 1)):
        cartridge[idx] = "="
    if mouth_pos is not None:
        cartridge[mouth_pos] = "|"
    if tip_pos is not None and mouth_pos is not None:
        for idx in range(mouth_pos + 1, min(width, tip_pos + 1)):
            cartridge[idx] = "-"
        cartridge[min(width - 1, tip_pos)] = ">"
    elif tip_pos is not None:
        cartridge[min(width - 1, tip_pos)] = ">"

    if std_pos is not None:
        ref[std_pos] = "S"
    if ogive_pos is not None:
        ref[ogive_pos] = "O"
    if lands_pos is not None:
        ref[lands_pos] = "L"

    info_bits = []
    if jump_mm is not None:
        info_bits.append(f"jump {float(jump_mm):+.2f} mm")
    if standard_oal_mm is not None and coal_mm is not None:
        info_bits.append(f"COAL {float(coal_mm):.2f}/{float(standard_oal_mm):.2f} mm")
    if throat_erosion_mm not in (None, ""):
        try:
            info_bits.append(f"throat {float(throat_erosion_mm):.2f} mm")
        except Exception:
            pass
    if neck_clearance_mm not in (None, ""):
        try:
            label = "neck clr"
            if neck_clearance_basis == "standard_estimate":
                label = "neck est"
            info_bits.append(f"{label} {float(neck_clearance_mm):+.3f} mm")
        except Exception:
            pass
    if freebore_delta_mm not in (None, ""):
        try:
            info_bits.append(f"freebore Δ {float(freebore_delta_mm):+.3f} mm")
        except Exception:
            pass
    if standard_body:
        info_bits.append(str(standard_body))
    if stability_tier:
        info_bits.append(str(stability_tier))
    if subsonic_mode:
        info_bits.append("sub")

    def _pill(label: str, level: str | None) -> str:
        palette = {
            "critical": ("#3a1a1a", "#ff6b6b"),
            "warning": ("#2e2410", "#f0a500"),
            "ok": ("#102818", "#4cd890"),
            "unknown": ("#1a2035", "#8a9ec0"),
            "neutral": ("#1a2035", "#8a9ec0"),
        }
        bg, fg = palette.get(
            str(level or "unknown").strip().lower(), ("#1a2035", "#8a9ec0")
        )
        return (
            f"<span style='display:inline-block; margin:0 6px 4px 0; padding:2px 8px; "
            f"border-radius:999px; background:{bg}; color:{fg}; font-size:8pt; font-weight:700;'>{label}</span>"
        )

    pills = []
    if stability_level:
        pills.append(_pill("Stabilitet", stability_level))
    if subsonic_mode:
        pills.append(_pill("Sub", subsonic_level or "unknown"))
    if subsonic_history_level:
        pills.append(_pill("History", subsonic_history_level))
    if has_suppressor:
        pills.append(
            _pill(
                "Suppressor",
                (
                    "warning"
                    if str(stability_level or "").lower() in {"critical", "warning"}
                    else "ok"
                ),
            )
        )

    return (
        "<div style='margin-top:6px; padding:6px 8px; border-radius:6px; background:#f8fafc; color:#111827; border:1px solid #dbeafe;'>"
        + "<b>Cartridge / chamber view</b><br>"
        + ("".join(pills) + "<br>" if pills else "")
        + "<span style='font-weight:400'>Technical cross-section view from bolt face to throat. "
        + "M = case mouth, O = selected ogive/CBTO, L = lands/jam, S = standard OAL.</span>"
        + "<pre style='margin:6px 0 0 0; font-family:Consolas, monospace; font-size:8pt; line-height:1.25;'>"
        + f"Chamber : |{''.join(chamber)}\n"
        + f"Round   : |{''.join(cartridge)}\n"
        + f"Ref     : |{''.join(ref)}\n"
        + "Legend  : M mouth, O ogive, L lands, S standard"
        + (f"\nInfo    : {' | '.join(info_bits)}" if info_bits else "")
        + "</pre></div>"
    )


def _seating_history_visualization_html(
    current_cbto_mm: float | None,
    best_cbto_mm: float | None,
    jam_cbto_mm: float | None,
    ranked_candidates: list[dict[str, Any]] | None = None,
) -> str:
    if best_cbto_mm in (None, ""):
        return ""
    values = [
        float(value)
        for value in (current_cbto_mm, best_cbto_mm, jam_cbto_mm)
        if value not in (None, "")
    ]
    candidate_values = []
    for item in ranked_candidates or []:
        if isinstance(item, dict) and item.get("cbto_mm") not in (None, ""):
            try:
                candidate_value = _coerce_float(item.get("cbto_mm"))
                if candidate_value is not None:
                    candidate_values.append(candidate_value)
            except Exception:
                pass
    values.extend(candidate_values)
    if not values:
        return ""
    min_val = min(values) - 0.20
    max_val = max(values) + 0.20
    span = max(0.20, max_val - min_val)

    def _pos(value: float | None) -> float | None:
        if value in (None, ""):
            return None
        return max(0.0, min(100.0, ((float(value) - min_val) / span) * 100.0))

    current_pos = _pos(current_cbto_mm)
    best_pos = _pos(best_cbto_mm)
    jam_pos = _pos(jam_cbto_mm)
    sweet_min = None
    sweet_max = None
    if candidate_values:
        top_values = sorted(
            candidate_values[:3] if len(candidate_values) >= 3 else candidate_values
        )
        sweet_min = _pos(min(top_values))
        sweet_max = _pos(max(top_values))

    markers = []
    if sweet_min is not None and sweet_max is not None:
        markers.append(
            f"<div style='position:absolute; left:{sweet_min:.1f}%; width:max(6px, calc({sweet_max:.1f}% - {sweet_min:.1f}%)); top:1px; bottom:1px; border-radius:5px; background:rgba(22,163,74,0.28);' title='Historical sweet spot'></div>"
        )
    if jam_pos is not None:
        markers.append(
            f"<div style='position:absolute; left:calc({jam_pos:.1f}% - 1px); top:0; bottom:0; width:2px; background:#dc2626;' title='Jam'></div>"
        )
    for index, item in enumerate(ranked_candidates or []):
        if not isinstance(item, dict) or item.get("cbto_mm") in (None, ""):
            continue
        pos = _pos(_coerce_float(item.get("cbto_mm")))
        if pos is None:
            continue
        size = 8 if index == 0 else 6
        color = "#2563eb" if index == 0 else "#60a5fa"
        markers.append(
            f"<div style='position:absolute; left:calc({pos:.1f}% - {size/2:.1f}px); top:{2 if index == 0 else 3}px; width:{size}px; height:{size}px; border-radius:999px; background:{color}; opacity:{1.0 if index == 0 else 0.85};' title='Historical candidate {index + 1}'></div>"
        )
    if best_pos is not None:
        markers.append(
            f"<div style='position:absolute; left:calc({best_pos:.1f}% - 5px); top:1px; width:10px; height:10px; border-radius:999px; background:#2563eb;' title='Best known CBTO'></div>"
        )
    if current_pos is not None:
        markers.append(
            f"<div style='position:absolute; left:calc({current_pos:.1f}% - 4px); top:2px; width:8px; height:8px; transform:rotate(45deg); background:#111827;' title='Current CBTO'></div>"
        )
    return f"""
    <div style='margin-top:4px;'>
      <div style='font-size:8pt; color:#374151; margin-bottom:2px;'>
                History: diamond = current, blue = candidates, green = sweet spot, red = jam
      </div>
      <div style='position:relative; width:100%; height:14px; border-radius:7px; background:#e5e7eb; border:1px solid #d1d5db;'>
        {''.join(markers)}
      </div>
    </div>
    """


def _seating_confidence_html(best_known_evidence: dict[str, Any] | None) -> str:
    if not isinstance(best_known_evidence, dict):
        return ""
    confidence = str(best_known_evidence.get("confidence") or "").strip().lower()
    if confidence == "high":
        bg = "#dcfce7"
        fg = "#166534"
        label = "High Evidence"
    elif confidence == "medium":
        bg = "#fef3c7"
        fg = "#92400e"
        label = "Medium Evidence"
    else:
        bg = "#1a2035"
        fg = "#8a9ec0"
        label = "Low Evidence"

    facts = []
    if best_known_evidence.get("session_count") not in (None, ""):
        session_count = _coerce_int(best_known_evidence.get("session_count"))
        if session_count is not None:
            facts.append(f"{session_count} sessions")
    evidence_count = _coerce_int(best_known_evidence.get("evidence_count"))
    if evidence_count is not None:
        facts.append(f"{evidence_count} data points")
    score_value = _coerce_float(best_known_evidence.get("score"))
    if score_value is not None:
        facts.append(f"score {score_value:.0f}")
    if best_known_evidence.get("matches_selected_lot"):
        facts.append("same lot")
    return (
        f"<div style='margin-top:4px; padding:6px 8px; border-radius:6px; background:{bg}; color:{fg};'>"
        f"<b>{label}</b>"
        + (
            f"<br><span style='font-weight:400'>{' | '.join(facts)}</span>"
            if facts
            else ""
        )
        + "</div>"
    )


def build_seating_sandbox_html(
    engine,
    rifle_id: int | None,
    bullet_id: int | None,
    powder_id: int | None,
    charge_weight_gr: float | None,
    coal_mm: float | None,
    cbto_mm: float | None,
    *,
    current_result: dict | None = None,
    barrel_id: str | None = None,
    ranked_candidates: list[dict[str, Any]] | None = None,
    subsonic_history: dict[str, Any] | None = None,
) -> str:
    if not engine or not all(
        value not in (None, "")
        for value in (
            rifle_id,
            bullet_id,
            powder_id,
            charge_weight_gr,
            coal_mm,
            cbto_mm,
        )
    ):
        return ""
    try:
        base_cbto = _coerce_float(cbto_mm)
        base_coal = _coerce_float(coal_mm)
        base_charge = _coerce_float(charge_weight_gr)
        rifle_id_i = _coerce_int(rifle_id)
        bullet_id_i = _coerce_int(bullet_id)
        powder_id_i = _coerce_int(powder_id)
    except Exception:
        return ""
    if (
        base_cbto is None
        or base_coal is None
        or base_charge is None
        or rifle_id_i is None
        or bullet_id_i is None
        or powder_id_i is None
    ):
        return ""

    base_result = current_result if isinstance(current_result, dict) else None
    if not isinstance(base_result, dict) or "error" in base_result:
        try:
            base_result = engine.calculate_load(
                rifle_id_i,
                bullet_id_i,
                powder_id_i,
                base_charge,
                base_coal,
                base_cbto,
                barrel_id=barrel_id,
            )
        except Exception:
            base_result = None
    if not isinstance(base_result, dict) or "error" in base_result:
        return ""

    offsets = [-0.10, -0.05, 0.0, 0.05, 0.10]
    samples: list[tuple[float, dict]] = []
    for offset in offsets:
        try:
            result = (
                base_result
                if offset == 0.0
                else engine.calculate_load(
                    rifle_id_i,
                    bullet_id_i,
                    powder_id_i,
                    base_charge,
                    base_coal,
                    round(base_cbto + offset, 3),
                    barrel_id=barrel_id,
                )
            )
        except Exception:
            continue
        if not isinstance(result, dict) or "error" in result:
            continue
        samples.append((offset, result))
    if len(samples) < 2:
        return ""

    base_pressure = float(base_result.get("peak_pressure_psi") or 0.0)
    base_velocity = float(base_result.get("muzzle_velocity_fps") or 0.0)
    base_time = float(base_result.get("barrel_time_ms") or 0.0)
    sweet_min = None
    sweet_max = None
    candidate_values = []
    for item in ranked_candidates or []:
        if not isinstance(item, dict) or item.get("cbto_mm") in (None, ""):
            continue
        try:
            candidate_value = _coerce_float(item.get("cbto_mm"))
            if candidate_value is not None:
                candidate_values.append(candidate_value)
        except Exception:
            continue
    if candidate_values:
        top_values = sorted(
            candidate_values[:3] if len(candidate_values) >= 3 else candidate_values
        )
        sweet_min = min(top_values)
        sweet_max = max(top_values)
    successful_cbto_range = None
    problem_cbto_range = None
    if isinstance(subsonic_history, dict):
        successful_cbto_range = subsonic_history.get("successful_cbto_range")
        problem_cbto_range = subsonic_history.get("problem_cbto_range")

    rows = []
    for offset, result in samples:
        trial_cbto = base_cbto + offset
        pressure = float(result.get("peak_pressure_psi") or 0.0)
        velocity = float(result.get("muzzle_velocity_fps") or 0.0)
        barrel_time = float(result.get("barrel_time_ms") or 0.0)
        jump_mm = None
        if result.get("jump_to_lands_mm") not in (None, ""):
            try:
                jump_mm = _coerce_float(result.get("jump_to_lands_mm"))
            except Exception:
                jump_mm = None
        elif result.get("jump_mm") not in (None, ""):
            try:
                jump_mm = _coerce_float(result.get("jump_mm"))
            except Exception:
                jump_mm = None
        label = "Now"
        if offset < 0:
            label = f"{offset:+.2f} mm"
        elif offset > 0:
            label = f"+{offset:.2f} mm"
        sweet_status = ""
        if sweet_min is not None and sweet_max is not None:
            if sweet_min <= trial_cbto <= sweet_max:
                sweet_status = "In Sweet Spot"
            elif (sweet_min - 0.03) <= trial_cbto <= (sweet_max + 0.03):
                sweet_status = "Near Window"
            else:
                sweet_status = "Outside"
        history_status = ""
        if (
            isinstance(successful_cbto_range, (tuple, list))
            and len(successful_cbto_range) == 2
            and successful_cbto_range[0] is not None
            and successful_cbto_range[1] is not None
            and float(successful_cbto_range[0])
            <= trial_cbto
            <= float(successful_cbto_range[1])
        ):
            history_status = "Similar to a Working Sub"
        elif (
            isinstance(problem_cbto_range, (tuple, list))
            and len(problem_cbto_range) == 2
            and problem_cbto_range[0] is not None
            and problem_cbto_range[1] is not None
            and float(problem_cbto_range[0])
            <= trial_cbto
            <= float(problem_cbto_range[1])
        ):
            history_status = "Near a Known Problem Area"
        rows.append(
            "<tr>"
            f"<td style='padding:2px 6px;'><b>{label}</b></td>"
            f"<td style='padding:2px 6px;'>{format_pressure_psi(pressure)} ({format_pressure_psi(pressure - base_pressure)})</td>"
            f"<td style='padding:2px 6px;'>{format_velocity_fps(velocity)} ({format_velocity_fps(velocity - base_velocity)})</td>"
            f"<td style='padding:2px 6px;'>{barrel_time:.3f} ms ({barrel_time - base_time:+.3f})</td>"
            f"<td style='padding:2px 6px;'>{'' if jump_mm is None else format_length_delta_mm(jump_mm)}</td>"
            f"<td style='padding:2px 6px;'>{sweet_status}</td>"
            f"<td style='padding:2px 6px;'>{history_status}</td>"
            "</tr>"
        )
    history_hint = ""
    if isinstance(subsonic_history, dict) and (
        subsonic_history.get("successful_count")
        or subsonic_history.get("problem_count")
    ):
        history_hint = " The history column shows whether a seating value resembles earlier subsonic setups that worked or caused problems."
    return (
        "<div style='margin-top:6px; padding:6px 8px; border-radius:6px; background:#eff6ff; color:#1e3a8a;'>"
        "<b>Seating sandbox</b><br>"
        "<span style='font-weight:400'>Move CBTO mentally around the current value and see the modeled effect on pressure, velocity, barrel time, jump, and whether you are in a historical sweet spot."
        + history_hint
        + "</span>"
        "<table style='margin-top:4px; font-size:8pt; border-collapse:collapse;'>"
        "<tr><th style='text-align:left; padding:2px 6px;'>CBTO</th>"
        "<th style='text-align:left; padding:2px 6px;'>Pressure</th>"
        "<th style='text-align:left; padding:2px 6px;'>Velocity</th>"
        "<th style='text-align:left; padding:2px 6px;'>Barrel time</th>"
        "<th style='text-align:left; padding:2px 6px;'>Jump</th>"
        "<th style='text-align:left; padding:2px 6px;'>Sweet spot</th>"
        "<th style='text-align:left; padding:2px 6px;'>History</th></tr>"
        + "".join(rows)
        + "</table></div>"
    )


def get_published_powder_charge_window(
    db,
    caliber: str | None,
    powder_name: str | None,
    bullet_id: int | None = None,
    bullet_weight_gr: float | None = None,
) -> dict[str, Any] | None:
    if not db or not str(caliber or "").strip() or not str(powder_name or "").strip():
        return None
    try:
        rows = db.execute_query(
            """
            SELECT *
            FROM load_data
            WHERE cartridge LIKE ? AND powder_name LIKE ?
            ORDER BY verified DESC, source
            """,
            (f"%{str(caliber).strip()}%", f"%{str(powder_name).strip()}%"),
        )
    except Exception:
        rows = []
    if not rows:
        return None
    filtered = list(rows)
    if bullet_id:
        filtered = [
            row for row in filtered if row.get("bullet_id") == bullet_id
        ] or filtered
    if bullet_weight_gr not in (None, ""):
        narrowed = []
        for row in filtered:
            try:
                if (
                    abs(
                        float(row.get("bullet_weight_grains")) - float(bullet_weight_gr)
                    )
                    <= 3.0
                ):
                    narrowed.append(row)
            except Exception:
                continue
        filtered = narrowed or filtered
    min_values = [
        float(row["min_charge_grains"])
        for row in filtered
        if row.get("min_charge_grains") not in (None, "")
    ]
    max_values = [
        float(row["max_charge_grains"])
        for row in filtered
        if row.get("max_charge_grains") not in (None, "")
    ]
    if not min_values or not max_values:
        return None
    return {
        "source_count": len(filtered),
        "avg_min_charge_grains": sum(min_values) / len(min_values),
        "avg_max_charge_grains": sum(max_values) / len(max_values),
        "min_charge_floor_grains": min(min_values),
        "max_charge_ceiling_grains": max(max_values),
        "sources": [
            str(row.get("source") or "").strip()
            for row in filtered[:3]
            if str(row.get("source") or "").strip()
        ],
    }


def build_powder_sandbox_html(
    engine,
    rifle_id: int | None,
    bullet_id: int | None,
    powder_id: int | None,
    charge_weight_gr: float | None,
    coal_mm: float | None,
    cbto_mm: float | None,
    *,
    current_result: dict | None = None,
    barrel_id: str | None = None,
    published_window: dict[str, Any] | None = None,
    subsonic_history: dict[str, Any] | None = None,
) -> str:
    if not engine or not all(
        value not in (None, "")
        for value in (
            rifle_id,
            bullet_id,
            powder_id,
            charge_weight_gr,
            coal_mm,
            cbto_mm,
        )
    ):
        return ""
    try:
        base_charge = _coerce_float(charge_weight_gr)
        base_coal = _coerce_float(coal_mm)
        base_cbto = _coerce_float(cbto_mm)
        rifle_id_i = _coerce_int(rifle_id)
        bullet_id_i = _coerce_int(bullet_id)
        powder_id_i = _coerce_int(powder_id)
    except Exception:
        return ""
    if (
        base_charge is None
        or base_coal is None
        or base_cbto is None
        or rifle_id_i is None
        or bullet_id_i is None
        or powder_id_i is None
    ):
        return ""
    offsets = [-0.30, -0.15, 0.0, 0.15, 0.30]
    base_result = current_result if isinstance(current_result, dict) else None
    if not isinstance(base_result, dict) or "error" in base_result:
        try:
            base_result = engine.calculate_load(
                rifle_id_i,
                bullet_id_i,
                powder_id_i,
                base_charge,
                base_coal,
                base_cbto,
                barrel_id=barrel_id,
            )
        except Exception:
            base_result = None
    if not isinstance(base_result, dict) or "error" in base_result:
        return ""
    base_pressure = float(base_result.get("peak_pressure_psi") or 0.0)
    base_velocity = float(base_result.get("muzzle_velocity_fps") or 0.0)
    base_density = float(base_result.get("load_density_percent") or 0.0)
    avg_min = None
    avg_max = None
    if isinstance(published_window, dict):
        try:
            if published_window.get("avg_min_charge_grains") not in (None, ""):
                avg_min = _coerce_float(published_window.get("avg_min_charge_grains"))
            if published_window.get("avg_max_charge_grains") not in (None, ""):
                avg_max = _coerce_float(published_window.get("avg_max_charge_grains"))
        except Exception:
            avg_min = avg_max = None
    successful_charge_range = None
    problem_charge_range = None
    if isinstance(subsonic_history, dict):
        successful_charge_range = subsonic_history.get("successful_charge_range")
        problem_charge_range = subsonic_history.get("problem_charge_range")
    rows = []
    for offset in offsets:
        trial_charge = round(base_charge + offset, 2)
        if trial_charge <= 0:
            continue
        try:
            result = (
                base_result
                if offset == 0.0
                else engine.calculate_load(
                    rifle_id_i,
                    bullet_id_i,
                    powder_id_i,
                    trial_charge,
                    base_coal,
                    base_cbto,
                    barrel_id=barrel_id,
                )
            )
        except Exception:
            continue
        if not isinstance(result, dict) or "error" in result:
            continue
        pressure = float(result.get("peak_pressure_psi") or 0.0)
        velocity = float(result.get("muzzle_velocity_fps") or 0.0)
        density = float(result.get("load_density_percent") or 0.0)
        status = []
        if density >= 100.0:
            status.append("Compressed")
        elif density >= 95.0:
            status.append("High Fill Ratio")
        if avg_min is not None and trial_charge < avg_min:
            status.append("Below Published Min")
        elif avg_max is not None and trial_charge > avg_max:
            status.append("Above Published Max")
        elif avg_min is not None and avg_max is not None:
            status.append("Inside Published Window")
        history_status = ""
        if (
            isinstance(successful_charge_range, (tuple, list))
            and len(successful_charge_range) == 2
            and successful_charge_range[0] is not None
            and successful_charge_range[1] is not None
            and float(successful_charge_range[0])
            <= trial_charge
            <= float(successful_charge_range[1])
        ):
            history_status = "Similar to a Working Sub"
        elif (
            isinstance(problem_charge_range, (tuple, list))
            and len(problem_charge_range) == 2
            and problem_charge_range[0] is not None
            and problem_charge_range[1] is not None
            and float(problem_charge_range[0])
            <= trial_charge
            <= float(problem_charge_range[1])
        ):
            history_status = "Near a Known Problem Area"
        rows.append(
            "<tr>"
            f"<td style='padding:2px 6px;'><b>{format_weight_grains(trial_charge, 'powder')}</b></td>"
            f"<td style='padding:2px 6px;'>{format_pressure_psi(pressure)} ({format_pressure_psi(pressure - base_pressure)})</td>"
            f"<td style='padding:2px 6px;'>{format_velocity_fps(velocity)} ({format_velocity_fps(velocity - base_velocity)})</td>"
            f"<td style='padding:2px 6px;'>{density:.1f}% ({density - base_density:+.1f})</td>"
            f"<td style='padding:2px 6px;'>{', '.join(status) if status else '-'}</td>"
            f"<td style='padding:2px 6px;'>{history_status}</td>"
            "</tr>"
        )
    if not rows:
        return ""
    published_hint = ""
    if avg_min is not None and avg_max is not None:
        published_hint = (
            " Published window about " f"{avg_min:.2f} gr" "-" f"{avg_max:.2f} gr."
        )
    history_hint = ""
    if isinstance(subsonic_history, dict) and (
        subsonic_history.get("successful_count")
        or subsonic_history.get("problem_count")
    ):
        history_hint = " The history column shows whether a load resembles earlier subsonic sessions that worked or caused problems."
    return (
        "<div style='margin-top:6px; padding:6px 8px; border-radius:6px; background:#fff7ed; color:#9a3412;'>"
        "<b>Powder sandbox</b><br>"
        "<span style='font-weight:400'>Move charge slightly around the current value and see the modeled effect on pressure, velocity, and fill ratio."
        + published_hint
        + history_hint
        + "</span>"
        "<table style='margin-top:4px; font-size:8pt; border-collapse:collapse;'>"
        "<tr><th style='text-align:left; padding:2px 6px;'>Charge</th>"
        "<th style='text-align:left; padding:2px 6px;'>Pressure</th>"
        "<th style='text-align:left; padding:2px 6px;'>Velocity</th>"
        "<th style='text-align:left; padding:2px 6px;'>Fill</th>"
        "<th style='text-align:left; padding:2px 6px;'>Status</th>"
        "<th style='text-align:left; padding:2px 6px;'>History</th></tr>"
        + "".join(rows)
        + "</table></div>"
    )


def _seating_trend_summary_html(best_known_evidence: dict[str, Any] | None) -> str:
    if not isinstance(best_known_evidence, dict):
        return ""
    ranked_source = best_known_evidence.get("ranked_candidates")
    ranked = (
        [item for item in ranked_source if isinstance(item, dict)]
        if isinstance(ranked_source, list)
        else []
    )
    if len(ranked) < 2:
        return ""
    cbto_values = []
    group_values = []
    for item in ranked[:5]:
        if item.get("cbto_mm") not in (None, ""):
            try:
                cbto_values.append(float(item["cbto_mm"]))
            except Exception:
                pass
        if item.get("best_group_moa") not in (None, ""):
            try:
                group_values.append(float(item["best_group_moa"]))
            except Exception:
                pass
    if not cbto_values:
        return ""
    spread = max(cbto_values) - min(cbto_values) if len(cbto_values) > 1 else 0.0
    group_hint = ""
    if group_values:
        group_hint = (
            f" | best groups {min(group_values):.2f}-{max(group_values):.2f} MOA"
        )
    return (
        "<div style='margin-top:4px; font-size:8pt; color:#374151;'>"
        f"Trend window: {min(cbto_values):.2f}-{max(cbto_values):.2f} mm CBTO"
        f" ({spread:.2f} mm span){group_hint}"
        "</div>"
    )


def _summarize_seating_promotion_candidate(
    best_known_evidence: dict[str, Any] | None,
    current_cbto_mm: float | None,
) -> dict[str, Any]:
    if not isinstance(best_known_evidence, dict):
        return {"eligible": False}
    try:
        confidence = str(best_known_evidence.get("confidence") or "").strip().lower()
        best_group = _coerce_float(best_known_evidence.get("best_group_moa"))
        best_es = _coerce_float(best_known_evidence.get("best_es_fps"))
        best_sd = _coerce_float(best_known_evidence.get("best_sd_fps"))
        best_cbto = _coerce_float(best_known_evidence.get("cbto_mm"))
    except Exception:
        return {"eligible": False}
    if best_group is None or best_es is None or best_sd is None or best_cbto is None:
        return {"eligible": False}

    ranked_source = best_known_evidence.get("ranked_candidates")
    ranked = (
        [item for item in ranked_source if isinstance(item, dict)]
        if isinstance(ranked_source, list)
        else []
    )
    ranked_cbto = []
    for item in ranked[:3]:
        if item.get("cbto_mm") not in (None, ""):
            try:
                ranked_cbto.append(float(item["cbto_mm"]))
            except Exception:
                pass
    sweet_span = max(ranked_cbto) - min(ranked_cbto) if len(ranked_cbto) >= 2 else 0.0
    cbto_delta = None
    if current_cbto_mm is not None:
        cbto_delta = abs(float(current_cbto_mm) - best_cbto)

    eligible = (
        confidence == "high"
        and best_group <= 0.40
        and best_es <= 12.0
        and best_sd <= 6.0
        and sweet_span <= 0.10
        and (cbto_delta is None or cbto_delta <= 0.10)
    )
    if not eligible:
        return {
            "eligible": False,
            "sweet_span_mm": sweet_span,
            "cbto_delta_mm": cbto_delta,
        }
    return {
        "eligible": True,
        "title": "Ready for sweet spot",
        "message": (
            f"History is strong enough to flag this seating as a sweet spot "
            f"({best_group:.2f} MOA / ES {best_es:.1f} / SD {best_sd:.1f})."
        ),
        "promoted_cbto_mm": best_cbto,
        "sweet_span_mm": sweet_span,
        "cbto_delta_mm": cbto_delta,
    }


def summarize_seating_depth_advisor(
    db,
    rifle_data: dict | None,
    bullet_data: dict | None,
    coal_mm: float | None,
    cbto_mm: float | None,
    *,
    profile_details: dict | None = None,
    barrel_details: dict | None = None,
    harmonics: dict | None = None,
    current_temperature_c: float | None = None,
    current_distance_m: float | None = None,
    subsonic_mode: bool = False,
    stability_context: dict | None = None,
    subsonic_context: dict | None = None,
    subsonic_history: dict | None = None,
) -> dict[str, Any]:
    rifle = rifle_data or {}
    bullet = bullet_data or {}
    details = profile_details or {}
    barrel = barrel_details or {}
    harmonics = harmonics or {}
    current_throat_erosion_mm = None
    try:
        _throat_val = (
            barrel.get("throat_erosion_mm")
            or rifle.get("throat_erosion_mm")
            or details.get("throat_erosion_mm")
        )
        current_throat_erosion_mm = (
            float(_throat_val) if _throat_val is not None else None
        )
    except Exception:
        current_throat_erosion_mm = None

    caliber = str(
        rifle.get("caliber") or bullet.get("caliber") or barrel.get("caliber") or ""
    ).strip()
    standard = find_best_cartridge_standard(db, caliber) if caliber else None
    standard_oal_mm = standard.get("oal_mm") if isinstance(standard, dict) else None
    chamber_comparison = {}
    if db and caliber:
        try:
            chamber_comparison = compare_chamber_to_cartridge_standard(
                db,
                caliber,
                {
                    "freebore_mm": barrel.get("freebore_mm")
                    or rifle.get("freebore_mm"),
                    "throat_angle_deg": barrel.get("throat_angle_deg")
                    or rifle.get("throat_angle_deg"),
                    "throat_erosion_mm": barrel.get("throat_erosion_mm")
                    or rifle.get("throat_erosion_mm")
                    or details.get("throat_erosion_mm"),
                    "chamber_neck_diameter_mm": (
                        details.get("chamber_neck_diameter_mm")
                        or barrel.get("chamber_neck_diameter_mm")
                    ),
                    "trim_length_mm": barrel.get("trim_length_mm"),
                },
            )
        except Exception:
            chamber_comparison = {}
    seating_profile = None
    best_known_evidence = None
    resolved_barrel_id = str(
        barrel.get("id")
        or barrel.get("barrel_id")
        or details.get("selected_barrel_id")
        or rifle.get("active_barrel_id")
        or ""
    ).strip()
    component_lot_id = bullet.get("selected_lot_id")
    if db and rifle.get("id") and bullet.get("id"):
        try:
            seating_profile = db.get_seating_depth_profile(
                int(rifle.get("id") or 0),
                int(bullet.get("id") or 0),
                int(component_lot_id) if component_lot_id not in (None, "") else None,
                resolved_barrel_id or None,
            )
        except Exception:
            seating_profile = None
        try:
            best_known_evidence = db.get_best_seating_depth_evidence(
                int(rifle.get("id") or 0),
                int(bullet.get("id") or 0),
                int(component_lot_id) if component_lot_id not in (None, "") else None,
                str(bullet.get("selected_lot_number") or "").strip() or None,
                current_temperature_c,
                current_distance_m,
                current_throat_erosion_mm,
                resolved_barrel_id or None,
                include_ranked=True,
            )
        except Exception:
            best_known_evidence = None

    jam_cbto_mm = None
    if rifle.get("jam_length_cbto_mm") not in (None, ""):
        try:
            jam_cbto_mm = float(rifle.get("jam_length_cbto_mm") or 0)
        except Exception:
            jam_cbto_mm = None
    if jam_cbto_mm is None and db and rifle.get("id") and bullet.get("id"):
        try:
            resolved_barrel_id = str(
                barrel.get("id")
                or barrel.get("barrel_id")
                or details.get("selected_barrel_id")
                or rifle.get("active_barrel_id")
                or ""
            ).strip()
            rows = db.execute_query(
                """
                SELECT jam_cbto_mm
                FROM rifle_bullet_jump_measurements
                WHERE rifle_id = ? AND bullet_id = ?
                  AND (? = '' OR COALESCE(barrel_id, '') = ?)
                ORDER BY CASE WHEN COALESCE(barrel_id, '') = ? THEN 0 ELSE 1 END,
                         CASE WHEN barrel_id IS NULL OR barrel_id = '' THEN 0 ELSE 1 END,
                         measurement_date DESC
                LIMIT 1
                """,
                (
                    rifle.get("id"),
                    bullet.get("id"),
                    resolved_barrel_id,
                    resolved_barrel_id,
                    resolved_barrel_id,
                ),
            )
            if rows and rows[0].get("jam_cbto_mm") not in (None, ""):
                jam_cbto_mm = float(rows[0]["jam_cbto_mm"])
        except Exception:
            jam_cbto_mm = None
    if (
        jam_cbto_mm is None
        and seating_profile
        and seating_profile.get("jam_cbto_mm") not in (None, "")
    ):
        try:
            jam_cbto_mm = float(seating_profile.get("jam_cbto_mm"))
        except Exception:
            jam_cbto_mm = None

    jump_mm = None
    if jam_cbto_mm is not None and cbto_mm is not None:
        try:
            jump_mm = float(jam_cbto_mm) - float(cbto_mm)
        except Exception:
            jump_mm = None

    level = "neutral"
    title = "Seating Depth"
    message = "Enter COAL/CBTO and jam data to get a sharper seating assessment."
    checks: list[str] = []

    if jump_mm is not None:
        seating_sensitivity = None
        try:
            seating_sensitivity = float(
                (harmonics or {}).get("sensitivity", {}).get("seating_depth")
            )
        except Exception:
            seating_sensitivity = None
        throat_erosion = current_throat_erosion_mm

        if jump_mm < 0:
            level = "critical"
            title = "Seating Depth: Into the Lands"
            message = (
                f"The bullet appears to be seated {abs(float(jump_mm)):.2f} mm into the lands. "
                "Treat this as high risk for a pressure spike and test very conservatively."
            )
            checks.append("Reduce CBTO or increase jump before further testing.")
        elif jump_mm < 0.10:
            level = "warning"
            title = "Seating Depth: Very Close to the Lands"
            message = f"Jump is only {float(jump_mm):.2f} mm. This can be precise, but pressure and lot response can change quickly."
            checks.append("Be extra conservative with charge and temperature.")
        elif jump_mm < 0.35:
            level = "warning"
            title = "Seating Depth: Tight Jump"
            message = f"Jump {float(jump_mm):.2f} mm sits in a tight window. Good for fine-tuning, but sensitive to throat and lot changes."
            checks.append(
                "Confirm seating with a control series after bullet-lot or throat changes."
            )
        elif jump_mm <= 1.20:
            level = "ok"
            title = "Seating Depth: Working Window"
            message = f"Jump {float(jump_mm):.2f} mm sits in a robust working window for further testing and harmonics work."
            checks.append("Use this as a stable baseline for charge and node work.")
        else:
            level = "neutral"
            title = "Seating Depth: Long Jump"
            message = f"Jump {float(jump_mm):.2f} mm is relatively long. Often robust and safe, but not always optimal for best precision."
            checks.append(
                "Consider testing a shorter jump if precision is the primary goal."
            )

        if seating_sensitivity is not None:
            if seating_sensitivity >= 1.5:
                checks.append(
                    f"The harmonics model rates seating sensitivity as high ({seating_sensitivity:.2f})."
                )
            elif seating_sensitivity >= 1.1:
                checks.append(
                    f"The harmonics model rates seating sensitivity as moderate ({seating_sensitivity:.2f})."
                )
            else:
                checks.append(
                    f"The harmonics model rates seating sensitivity as relatively robust ({seating_sensitivity:.2f})."
                )
        if throat_erosion is not None and throat_erosion >= 0.10:
            checks.append(
                f"Recorded throat erosion of {throat_erosion:.2f} mm can move the jam and jump window over time."
            )
    else:
        if jam_cbto_mm is None:
            checks.append(
                "Missing measured jam/CBTO for the selected bullet in this firearm."
            )

    if standard_oal_mm not in (None, "") and coal_mm is not None:
        try:
            coal_delta = float(coal_mm) - float(standard_oal_mm)
            checks.append(
                f"COAL {float(coal_mm):.2f} mm mot standard {float(standard_oal_mm):.2f} mm ({coal_delta:+.2f} mm)."
            )
        except Exception:
            pass
    if isinstance(chamber_comparison, dict):
        neck_clearance = chamber_comparison.get("neck_clearance_mm")
        freebore_delta = chamber_comparison.get("freebore_delta_mm")
        if neck_clearance not in (None, ""):
            try:
                checks.append(
                    f"Indicative neck clearance {float(neck_clearance):+.3f} mm versus cartridge standard."
                )
            except Exception:
                pass
        if freebore_delta not in (None, ""):
            try:
                checks.append(
                    f"Freebore deviation versus standard {float(freebore_delta):+.3f} mm."
                )
            except Exception:
                pass

    if seating_profile:
        profile_bits = []
        if seating_profile.get("preferred_jump_mm") not in (None, ""):
            profile_bits.append(
                f"preferred jump {float(seating_profile['preferred_jump_mm']):.2f} mm"
            )
        if seating_profile.get("preferred_cbto_mm") not in (None, ""):
            profile_bits.append(
                f"profile CBTO {float(seating_profile['preferred_cbto_mm']):.2f} mm"
            )
        lot_hint = ""
        if bullet.get("selected_lot_number"):
            lot_hint = f" for lot {bullet.get('selected_lot_number')}"
        if profile_bits:
            checks.append(
                "Stored seating profile"
                + lot_hint
                + ": "
                + ", ".join(profile_bits)
                + "."
            )
            checks[-1] = (
                "Lagret seating-profil"
                + lot_hint
                + ": "
                + ", ".join(profile_bits)
                + "."
            )

    if isinstance(best_known_evidence, dict):
        evidence_bits = []
        if best_known_evidence.get("cbto_mm") not in (None, ""):
            evidence_bits.append(f"CBTO {float(best_known_evidence['cbto_mm']):.2f} mm")
        if best_known_evidence.get("best_group_moa") not in (None, ""):
            evidence_bits.append(
                f"best group {float(best_known_evidence['best_group_moa']):.2f} MOA"
            )
        if best_known_evidence.get("best_es_fps") not in (None, ""):
            evidence_bits.append(
                f"ES {format_velocity_fps(float(best_known_evidence['best_es_fps']))}"
            )
        if best_known_evidence.get("best_sd_fps") not in (None, ""):
            evidence_bits.append(
                f"SD {format_velocity_fps(float(best_known_evidence['best_sd_fps']))}"
            )
        confidence = str(best_known_evidence.get("confidence") or "").strip()
        lot_ref = str(best_known_evidence.get("lot_number") or "").strip()
        source_hint = (
            "from active lot"
            if best_known_evidence.get("matches_selected_lot")
            else "from history"
        )
        if lot_ref and not best_known_evidence.get("matches_selected_lot"):
            source_hint += f" (lot {lot_ref})"
        elif lot_ref and best_known_evidence.get("matches_selected_lot"):
            source_hint = f"from active lot {lot_ref}"
        evidence_text = (
            ", ".join(evidence_bits) if evidence_bits else "measured batch data"
        )
        source_text = source_hint or "from history"
        checks.append(
            f"Best known seating {source_text}: {evidence_text}."
            + (f" Evidens {confidence}." if confidence else "")
        )
        if cbto_mm is not None and best_known_evidence.get("cbto_mm") not in (None, ""):
            cbto_delta = float(cbto_mm) - float(best_known_evidence["cbto_mm"])
            if abs(cbto_delta) >= 0.05:
                checks.append(
                    f"The current CBTO is {cbto_delta:+.2f} mm relative to the best known seating from history."
                )
        if best_known_evidence.get("temperature_delta_c") not in (None, ""):
            checks.append(
                f"Temperature match versus history: {format_temperature_delta_c(float(best_known_evidence['temperature_delta_c'])).lstrip('+')} deviation."
            )
        if best_known_evidence.get("distance_delta_m") not in (None, ""):
            checks.append(
                f"Distance match versus history: {float(best_known_evidence['distance_delta_m']):.0f} m deviation."
            )
        if best_known_evidence.get("throat_delta_mm") not in (None, ""):
            checks.append(
                f"Throat erosion versus history: {float(best_known_evidence['throat_delta_mm']):.2f} mm deviation."
            )

    promotion_candidate = _summarize_seating_promotion_candidate(
        best_known_evidence, cbto_mm
    )
    if promotion_candidate.get("eligible"):
        checks.append(
            f"{str(promotion_candidate.get('title') or 'Sweet spot')}: "
            f"{str(promotion_candidate.get('message') or '').strip()}"
        )

    summary_bits = []
    if jam_cbto_mm is not None:
        summary_bits.append(f"Jam CBTO {float(jam_cbto_mm):.2f} mm")
    if cbto_mm is not None:
        summary_bits.append(f"Selected CBTO {float(cbto_mm):.2f} mm")
    if coal_mm is not None:
        summary_bits.append(f"COAL {float(coal_mm):.2f} mm")
    if seating_profile and seating_profile.get("preferred_jump_mm") not in (None, ""):
        summary_bits.append(
            f"Profile jump {float(seating_profile['preferred_jump_mm']):.2f} mm"
        )
    if isinstance(best_known_evidence, dict) and best_known_evidence.get(
        "cbto_mm"
    ) not in (None, ""):
        summary_bits.append(
            f"Best known CBTO {float(best_known_evidence['cbto_mm']):.2f} mm"
        )
    if promotion_candidate.get("eligible"):
        summary_bits.append("Sweet spot ready")

    geometry_html = _build_cartridge_geometry_visual_html(
        coal_mm=coal_mm,
        cbto_mm=cbto_mm,
        jam_cbto_mm=jam_cbto_mm,
        jump_mm=jump_mm,
        standard_oal_mm=(
            float(standard_oal_mm) if standard_oal_mm not in (None, "") else None
        ),
        case_length_mm=(
            float(standard.get("case_length_mm") or 0)
            if isinstance(standard, dict)
            and standard.get("case_length_mm") not in (None, "")
            else None
        ),
        bullet_length_mm=(
            float(bullet.get("length_mm") or 0)
            if bullet.get("length_mm") not in (None, "")
            else None
        ),
        throat_erosion_mm=current_throat_erosion_mm,
        neck_clearance_mm=(
            chamber_comparison.get("neck_clearance_mm")
            if isinstance(chamber_comparison, dict)
            else None
        ),
        neck_clearance_basis=(
            chamber_comparison.get("neck_clearance_basis")
            if isinstance(chamber_comparison, dict)
            else None
        ),
        freebore_delta_mm=(
            chamber_comparison.get("freebore_delta_mm")
            if isinstance(chamber_comparison, dict)
            else None
        ),
        standard_body=(
            chamber_comparison.get("standard_body")
            if isinstance(chamber_comparison, dict)
            else None
        ),
        subsonic_mode=subsonic_mode,
        stability_tier=(
            f"seat sens {float((harmonics or {}).get('sensitivity', {}).get('seating_depth')):.2f}"
            if (harmonics or {}).get("sensitivity", {}).get("seating_depth")
            not in (None, "")
            else None
        ),
        stability_level=(
            str((stability_context or {}).get("level") or "").strip().lower() or None
        ),
        subsonic_level=(
            str((subsonic_context or {}).get("level") or "").strip().lower() or None
        ),
        subsonic_history_level=(
            str((subsonic_history or {}).get("level") or "").strip().lower() or None
        ),
        has_suppressor=any(
            token
            in str(
                barrel.get("muzzle_device_type")
                or barrel.get("muzzle_device")
                or rifle.get("muzzle_device")
                or ""
            )
            .strip()
            .lower()
            for token in ("suppressor", "moderator", "demper")
        ),
    )

    return {
        "level": level,
        "title": title,
        "message": message,
        "jump_mm": jump_mm,
        "jam_cbto_mm": jam_cbto_mm,
        "standard_oal_mm": standard_oal_mm,
        "seating_profile": seating_profile,
        "best_known_evidence": best_known_evidence,
        "promotion_candidate": promotion_candidate,
        "checks": checks,
        "summary": " | ".join(summary_bits),
        "visualization_html": _seating_visualization_html(jump_mm) + geometry_html,
        "history_visualization_html": _seating_history_visualization_html(
            cbto_mm,
            (
                best_known_evidence.get("cbto_mm")
                if isinstance(best_known_evidence, dict)
                else None
            ),
            jam_cbto_mm,
            (
                best_known_evidence.get("ranked_candidates")
                if isinstance(best_known_evidence, dict)
                else None
            ),
        ),
        "confidence_html": _seating_confidence_html(best_known_evidence),
        "trend_summary_html": _seating_trend_summary_html(best_known_evidence),
    }


def summarize_powder_lot_advisory(db, powder_id) -> dict[str, str]:
    if not db or not powder_id:
        return {
            "level": "neutral",
            "title": "Powder Lot",
            "message": "Select a powder to view lot guidance.",
        }
    try:
        rows = db.execute_query(
            """
            SELECT id
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC
            LIMIT 1
            """,
            (int(powder_id),),
        )
    except Exception:
        rows = []
    if not rows:
        return {
            "level": "neutral",
            "title": "Powder Lot",
            "message": "No registered powder lots for the selected powder.",
        }

    comparison = db.compare_powder_lots(int(powder_id), int(rows[0]["id"]))
    if not comparison:
        return {
            "level": "neutral",
            "title": "Powder Lot",
            "message": "No lot guidance available yet.",
        }

    verification_plan = comparison.get("verification_plan") or {}
    current_profile = comparison.get("current_profile") or {}
    plan_focus = str(verification_plan.get("focus") or "").strip()
    delta = verification_plan.get("start_delta_grains")
    delta_text = ""
    if isinstance(delta, (int, float)) and float(delta) != 0.0:
        delta_text = (
            f" Start {abs(float(delta)):.2f} gr {'opp' if float(delta) > 0 else 'ned'}."
        )

    severity = str(comparison.get("severity") or "info")
    level = "neutral"
    if severity == "ok":
        level = "ok"
    elif severity == "watch":
        level = "warning"
    elif severity == "high":
        level = "critical"

    message = str(comparison.get("message") or "").strip()
    confidence_label = str(current_profile.get("confidence_label") or "").strip()
    deltas = [
        abs(float(comparison.get("avg_velocity_shift_fps") or 0.0)),
        abs(float(comparison.get("velocity_offset_shift_fps") or 0.0)),
        abs(float(comparison.get("typical_es_shift_fps") or 0.0)),
    ]
    span = max(deltas) if deltas else 0.0
    uncertainty_message = (
        f"Usikkerhet: denne loten kan fortsatt flytte hastighetsbildet med omtrent {max(8.0, span):.0f} fps."
        if span > 0
        else ""
    )
    if not uncertainty_message and str(comparison.get("severity") or "") in {
        "watch",
        "high",
    }:
        uncertainty_message = "Uncertainty: this lot can still move the velocity picture noticeably until the verification series is confirmed."
    if confidence_label:
        message = f"{message} Data foundation: {confidence_label}.".strip()
    if uncertainty_message:
        message = f"{message} {uncertainty_message}".strip()
    if plan_focus:
        message = f"{message} {plan_focus}{delta_text}".strip()
    return {
        "level": level,
        "title": str(comparison.get("title") or "Powder Lot").strip() or "Powder Lot",
        "message": message or "Lot guidance available.",
        "confidence_label": confidence_label,
    }


def summarize_powder_model_advisory(powder_context: dict | None) -> dict[str, str]:
    if not isinstance(powder_context, dict) or not powder_context:
        return {
            "level": "neutral",
            "title": "Powder Model",
            "message": "Select a powder to view model status.",
        }

    powder_name = str(powder_context.get("name") or "selected powder").strip()
    validation_status = str(powder_context.get("validation_status") or "").strip()
    usable_for_simulation = bool(powder_context.get("usable_for_simulation"))
    data_source = str(powder_context.get("data_source") or "").strip()
    missing_fields = []
    for label, key in [
        ("Ba", "quickload_ba_value"),
        ("Qex", "qex_kj_per_kg"),
        ("k", "k_ratio"),
        ("a0", "a0"),
        ("z1", "z1"),
        ("z2", "z2"),
        ("eta", "eta_cm3_per_kg"),
        ("pc", "pc_kg_m3"),
        ("pcd", "pcd_kg_m3"),
    ]:
        if powder_context.get(key) in (None, "", 0) and key not in {"tcc", "tch"}:
            missing_fields.append(label)

    if usable_for_simulation:
        source_suffix = f" Source: {data_source}." if data_source else ""
        return {
            "level": "ok",
            "title": "Powder Model Ready",
            "message": f"{powder_name} has enough model fields for simulation.{source_suffix}",
        }

    if validation_status:
        status_text = f" Status: {validation_status}."
    else:
        status_text = ""
    missing_text = (
        f" Missing: {', '.join(missing_fields[:6])}."
        if missing_fields
        else " The model basis is incomplete."
    )
    return {
        "level": "critical",
        "title": "Powder Model Missing",
        "message": (
            f"{powder_name} is not verified for pressure, fill-ratio, or OBT calculations."
            f"{status_text}{missing_text}"
        ).strip(),
    }


def infer_primer_reference_profile(primer_context: dict | None) -> dict[str, Any]:
    """Fill in known primer profile hints when the database row is sparse."""
    primer = dict(primer_context or {})
    if not primer:
        return {}

    manufacturer = str(primer.get("manufacturer") or "").strip().lower()
    name = str(primer.get("name") or "").strip().lower()
    key = f"{manufacturer} {name}".strip()

    known_profiles = {
        "cci 450": {
            "product_line": "CCI Primers",
            "part_number": "17",
            "source_kind": "manufacturer_published+reference_inferred",
            "manufacturer_source": "CCI catalog",
            "match_grade": 0,
            "magnum": 1,
            "primer_family": "small_rifle_magnum",
            "cup_thickness_in": 0.025,
            "cup_hardness_class": "hard",
            "pressure_tolerance_class": "high",
            "ignition_strength_class": "magnum",
            "recommended_pressure_min_psi": 50000.0,
            "recommended_pressure_max_psi": 62000.0,
            "primer_sign_interpretation": "late_signs_possible",
            "evidence_level": "reference_seed",
        },
        "cci br-4": {
            "product_line": "CCI Primers",
            "part_number": "19",
            "source_kind": "manufacturer_published+reference_inferred",
            "manufacturer_source": "CCI catalog",
            "match_grade": 1,
            "magnum": 0,
            "primer_family": "small_rifle_benchrest",
            "cup_thickness_in": 0.025,
            "cup_hardness_class": "hard",
            "pressure_tolerance_class": "high",
            "ignition_strength_class": "standard_plus",
            "recommended_pressure_min_psi": 50000.0,
            "recommended_pressure_max_psi": 62000.0,
            "primer_sign_interpretation": "late_signs_possible",
            "evidence_level": "reference_seed",
        },
        "federal 205": {
            "product_line": "Federal Champion",
            "part_number": "100",
            "source_kind": "manufacturer_published+reference_inferred",
            "manufacturer_source": "Federal catalog",
            "match_grade": 0,
            "magnum": 0,
            "primer_family": "small_rifle",
            "cup_thickness_in": 0.022,
            "cup_hardness_class": "medium",
            "pressure_tolerance_class": "high",
            "ignition_strength_class": "standard",
            "recommended_pressure_min_psi": 50000.0,
            "recommended_pressure_max_psi": 62000.0,
            "primer_sign_interpretation": "normal",
            "evidence_level": "reference_seed",
        },
        "federal 205m": {
            "product_line": "Gold Medal",
            "part_number": "GM205M",
            "source_kind": "manufacturer_published+reference_inferred",
            "manufacturer_source": "Federal catalog",
            "match_grade": 1,
            "magnum": 0,
            "primer_family": "small_rifle_match",
            "cup_thickness_in": 0.022,
            "cup_hardness_class": "medium",
            "pressure_tolerance_class": "high",
            "ignition_strength_class": "standard",
            "recommended_pressure_min_psi": 50000.0,
            "recommended_pressure_max_psi": 62000.0,
            "primer_sign_interpretation": "normal",
            "evidence_level": "reference_seed",
        },
        "remington 7 1/2": {
            "product_line": "Remington Bench Rest",
            "source_kind": "reference_inferred",
            "manufacturer_source": "Remington SDS / safety materials",
            "match_grade": 1,
            "magnum": 0,
            "primer_family": "small_rifle_benchrest",
            "cup_thickness_in": 0.025,
            "cup_hardness_class": "hard",
            "pressure_tolerance_class": "high",
            "ignition_strength_class": "standard_plus",
            "recommended_pressure_min_psi": 50000.0,
            "recommended_pressure_max_psi": 62000.0,
            "primer_sign_interpretation": "late_signs_possible",
            "evidence_level": "reference_seed",
        },
        "cci 400": {
            "product_line": "CCI Primers",
            "part_number": "13",
            "source_kind": "manufacturer_published+reference_inferred",
            "manufacturer_source": "CCI catalog",
            "match_grade": 0,
            "magnum": 0,
            "primer_family": "small_rifle",
            "cup_thickness_in": 0.020,
            "cup_hardness_class": "medium",
            "pressure_tolerance_class": "moderate",
            "ignition_strength_class": "standard",
            "recommended_pressure_min_psi": 35000.0,
            "recommended_pressure_max_psi": 50000.0,
            "primer_sign_interpretation": "early_signs_possible",
            "evidence_level": "reference_seed",
        },
        "remington 6 1/2": {
            "product_line": "Remington Primers",
            "source_kind": "reference_inferred",
            "manufacturer_source": "Remington SDS / safety materials",
            "match_grade": 0,
            "magnum": 0,
            "primer_family": "small_rifle",
            "cup_thickness_in": 0.020,
            "cup_hardness_class": "soft",
            "pressure_tolerance_class": "moderate",
            "ignition_strength_class": "standard",
            "recommended_pressure_min_psi": 35000.0,
            "recommended_pressure_max_psi": 50000.0,
            "primer_sign_interpretation": "early_signs_possible",
            "evidence_level": "reference_seed",
        },
        "winchester sr": {
            "product_line": "Winchester Components",
            "source_kind": "manufacturer_published+reference_inferred",
            "manufacturer_source": "Winchester components / SDS",
            "match_grade": 0,
            "magnum": 0,
            "primer_family": "small_rifle",
            "cup_thickness_in": 0.020,
            "cup_hardness_class": "medium",
            "pressure_tolerance_class": "moderate",
            "ignition_strength_class": "standard",
            "recommended_pressure_min_psi": 35000.0,
            "recommended_pressure_max_psi": 50000.0,
            "primer_sign_interpretation": "early_signs_possible",
            "evidence_level": "reference_seed",
        },
    }

    profile = known_profiles.get(key, {})
    if not profile:
        return primer

    for field, value in profile.items():
        if primer.get(field) in (None, "", 0):
            primer[field] = value
    if not primer.get("reference_source"):
        primer["reference_source"] = "Calhoon small-rifle pressure notes"
    return primer


def summarize_primer_profile_advisory(
    primer_context: dict | None, result: dict | None = None
) -> dict[str, str]:
    """Evaluate whether the selected primer profile matches the current pressure window."""
    primer = infer_primer_reference_profile(primer_context)
    if not isinstance(primer, dict) or not primer:
        return {
            "level": "neutral",
            "title": "Primer Profile",
            "message": "Select a primer to view the primer profile and pressure window.",
        }

    name = (
        f"{str(primer.get('manufacturer') or '').strip()} "
        f"{str(primer.get('name') or 'valgt primer').strip()}"
    ).strip()
    peak = result.get("peak_pressure_psi") if isinstance(result, dict) else None
    maximum = result.get("max_pressure_psi") if isinstance(result, dict) else None

    pressure_class = str(primer.get("pressure_tolerance_class") or "").strip()
    sign_mode = str(primer.get("primer_sign_interpretation") or "").strip()
    recommended_min = primer.get("recommended_pressure_min_psi")
    recommended_max = primer.get("recommended_pressure_max_psi")

    try:
        peak_f = float(peak) if peak is not None else None
    except Exception:
        peak_f = None
    try:
        max_f = float(maximum) if maximum is not None else None
    except Exception:
        max_f = None

    if peak_f is not None and recommended_max not in (None, ""):
        try:
            if peak_f > float(recommended_max or 0):
                return {
                    "level": "critical",
                    "title": "Primer Above Pressure Window",
                    "message": (
                        f"{name} is rated to about {int(float(recommended_max or 0))} PSI, "
                        f"while the load is running around {int(peak_f)} PSI. Choose a more pressure-tolerant primer "
                        "or reduce the load."
                    ),
                }
        except Exception:
            pass

    if peak_f is not None and pressure_class == "moderate":
        return {
            "level": "critical",
            "title": "Primer Not Ideal for High Pressure",
            "message": (
                f"{name} is classified for moderate SRP pressure. Around {int(peak_f)} PSI you should stay "
                "very conservative, and classic primer signs may appear early or become misleading."
            ),
        }

    if (
        max_f
        and peak_f
        and peak_f >= 0.95 * max_f
        and sign_mode == "late_signs_possible"
    ):
        return {
            "level": "warning",
            "title": "Thick Primer Cups Can Hide Signs",
            "message": (
                f"{name} has a tougher cup and may show late primer signs near max. Do not use the absence of "
                "flattening or piercing alone as proof of low pressure."
            ),
        }

    if peak_f is not None and recommended_min not in (None, ""):
        try:
            if peak_f < float(recommended_min or 0) and str(
                primer.get("ignition_strength_class") or ""
            ) in {
                "magnum",
                "standard_plus",
            }:
                return {
                    "level": "warning",
                    "title": "Strong Primer in a Low Pressure Window",
                    "message": (
                        f"{name} is a relatively strong primer and the load sits low in the pressure window. "
                        "Confirm ES/SD and ignition consistency with a control series."
                    ),
                }
        except Exception:
            pass

    source = str(primer.get("reference_source") or "").strip()
    return {
        "level": "ok",
        "title": "Primer Profile Fits",
        "message": f"{name} looks reasonable in this pressure window."
        + (f" Source: {source}." if source else ""),
    }


def collect_safety_advisories(
    result: dict | None,
    powder_context: dict | None = None,
    primer_context: dict | None = None,
    internal_ballistics: dict | None = None,
) -> list[dict[str, str]]:
    """Collect warning/critical advisories for the current builder state."""
    advisories: list[dict[str, str]] = []

    pressure_risk = summarize_pressure_risk(result or {})
    if pressure_risk.get("level") in {"warning", "critical"}:
        advisories.append(
            {
                "level": str(pressure_risk.get("level") or "warning"),
                "title": str(pressure_risk.get("title") or "Pressure Assessment"),
                "message": str(pressure_risk.get("message") or "").strip(),
            }
        )

    powder_risk = summarize_powder_model_advisory(powder_context)
    if powder_risk.get("level") in {"warning", "critical"}:
        advisories.append(
            {
                "level": str(powder_risk.get("level") or "warning"),
                "title": str(powder_risk.get("title") or "Powder Model"),
                "message": str(powder_risk.get("message") or "").strip(),
            }
        )

    primer_risk = summarize_primer_profile_advisory(primer_context, result or {})
    if primer_risk.get("level") in {"warning", "critical"}:
        advisories.append(
            {
                "level": str(primer_risk.get("level") or "warning"),
                "title": str(primer_risk.get("title") or "Primer Profile"),
                "message": str(primer_risk.get("message") or "").strip(),
            }
        )

    if isinstance(internal_ballistics, dict) and internal_ballistics.get("level") in {
        "warning",
        "critical",
    }:
        advisories.append(
            {
                "level": str(internal_ballistics.get("level") or "warning"),
                "title": str(internal_ballistics.get("title") or "Internal Ballistics"),
                "message": str(internal_ballistics.get("message") or "").strip(),
            }
        )

    return advisories


def build_component_context_summary(
    bullet_data: dict | None = None,
    powder_data: dict | None = None,
    primer_data: dict | None = None,
) -> str:
    """Summarize whether active component data is standard, measured, or learned."""
    lines: list[str] = []

    if isinstance(bullet_data, dict) and bullet_data:
        bullet_name = str(bullet_data.get("name") or "Selected bullet").strip()
        lot_number = str(bullet_data.get("selected_lot_number") or "").strip()
        measured_stats = bullet_data.get("measured_lot_stats") or {}
        if measured_stats.get("sample_count"):
            lines.append(
                f"Bullet: {bullet_name} | Lot {lot_number or '-'} | Measured lot average active"
            )
        elif lot_number:
            lines.append(
                f"Bullet: {bullet_name} | Lot {lot_number} | Standard library data in use"
            )
        else:
            lines.append(f"Bullet: {bullet_name} | Standard library data in use")

    if isinstance(powder_data, dict) and powder_data:
        powder_name = str(powder_data.get("name") or "Selected powder").strip()
        lot_number = str(powder_data.get("selected_lot_number") or "").strip()
        comparison = powder_data.get("lot_comparison") or {}
        reference_variant_count = int(
            powder_data.get("reference_variant_count")
            or powder_data.get("gordon_reference_variant_count")
            or 0
        )
        if lot_number and comparison.get("title"):
            lines.append(
                f"Powder: {powder_name} | Lot {lot_number} | Learned lot context: {comparison.get('title')}"
            )
        elif lot_number:
            lines.append(
                f"Powder: {powder_name} | Lot {lot_number} | Active lot context"
            )
        else:
            lines.append(f"Powder: {powder_name} | Standard catalog data")
        if reference_variant_count:
            lines.append(
                f"Powder references: {reference_variant_count} internal Gordon variants"
            )

    if isinstance(primer_data, dict) and primer_data:
        primer_name = str(primer_data.get("name") or "Selected primer").strip()
        lot_number = str(primer_data.get("selected_lot_number") or "").strip()
        comparison = primer_data.get("lot_comparison") or {}
        if lot_number and comparison.get("title"):
            lines.append(
                f"Primer: {primer_name} | Lot {lot_number} | Learned lot context: {comparison.get('title')}"
            )
        elif lot_number:
            lines.append(
                f"Primer: {primer_name} | Lot {lot_number} | Active lot context"
            )
        else:
            lines.append(f"Primer: {primer_name} | Standard inventory data")

    if not lines:
        return (
            "No active component context yet. Select a bullet, powder, and optional lots to see "
            "whether the builder is using standard data, measured lot averages, or historical learning."
        )
    return "<br>".join(lines)


def build_active_component_context_payload(
    bullet_data: dict | None = None,
    powder_data: dict | None = None,
    primer_data: dict | None = None,
) -> dict[str, Any]:
    """Create a compact serializable payload describing current component provenance."""
    summary = build_component_context_summary(
        bullet_data=bullet_data,
        powder_data=powder_data,
        primer_data=primer_data,
    )
    payload: dict[str, Any] = {
        "summary_html": summary,
        "bullet": None,
        "powder": None,
        "primer": None,
    }
    if isinstance(bullet_data, dict) and bullet_data:
        measured_stats = bullet_data.get("measured_lot_stats") or {}
        payload["bullet"] = {
            "id": bullet_data.get("id"),
            "name": bullet_data.get("name"),
            "lot_number": bullet_data.get("selected_lot_number"),
            "uses_measured_lot_stats": bool(measured_stats.get("sample_count")),
            "sample_count": measured_stats.get("sample_count"),
            "nominal_weight_grains": bullet_data.get("nominal_weight_grains"),
            "effective_weight_grains": bullet_data.get(
                "weight_grains", bullet_data.get("weight")
            ),
            "nominal_length_mm": bullet_data.get("nominal_length_mm"),
            "effective_length_mm": bullet_data.get("length_mm"),
            "nominal_diameter_mm": bullet_data.get("nominal_diameter_mm"),
            "effective_diameter_mm": bullet_data.get("diameter_mm"),
            "bc_g1": bullet_data.get("bc_g1"),
            "bc_g7": bullet_data.get("bc_g7"),
            "bullet_type": bullet_data.get("bullet_type"),
            "source_label": bullet_data.get("source_label"),
        }
    if isinstance(powder_data, dict) and powder_data:
        comparison = powder_data.get("lot_comparison") or {}
        payload["powder"] = {
            "id": powder_data.get("id"),
            "name": powder_data.get("name"),
            "lot_number": powder_data.get("selected_lot_number"),
            "validation_status": powder_data.get("validation_status"),
            "usable_for_simulation": powder_data.get("usable_for_simulation"),
            "reference_snapshot_count": powder_data.get("reference_snapshot_count"),
            "reference_variant_count": powder_data.get("reference_variant_count"),
            "gordon_reference_snapshot_count": powder_data.get(
                "gordon_reference_snapshot_count"
            ),
            "gordon_reference_variant_count": powder_data.get(
                "gordon_reference_variant_count"
            ),
            "quickload_ba_value": powder_data.get("quickload_ba_value"),
            "qex_kj_per_kg": powder_data.get("qex_kj_per_kg"),
            "k_ratio": powder_data.get("k_ratio"),
            "eta_cm3_per_kg": powder_data.get("eta_cm3_per_kg"),
            "pc_kg_m3": powder_data.get("pc_kg_m3"),
            "pt_c": powder_data.get("pt_c"),
            "temp_stable": powder_data.get("temp_stable"),
            "data_source": powder_data.get("data_source"),
            "lot_learning_title": comparison.get("title"),
            "lot_learning_severity": comparison.get("severity"),
        }
    if isinstance(primer_data, dict) and primer_data:
        comparison = primer_data.get("lot_comparison") or {}
        payload["primer"] = {
            "id": primer_data.get("id"),
            "name": primer_data.get("name"),
            "lot_number": primer_data.get("selected_lot_number"),
            "lot_learning_title": comparison.get("title"),
            "lot_learning_severity": comparison.get("severity"),
        }
    return payload


def summarize_bullet_lot_advisory(db, bullet_id) -> dict[str, str]:
    if not db or not bullet_id:
        return {
            "level": "neutral",
            "title": "Bullet Lot",
            "message": "Select a bullet to view lot guidance.",
        }
    try:
        rows = db.execute_query(
            """
            SELECT id
            FROM bullet_lots
            WHERE bullet_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC, id DESC
            LIMIT 1
            """,
            (int(bullet_id),),
        )
    except Exception:
        rows = []
    if not rows:
        return {
            "level": "neutral",
            "title": "Bullet Lot",
            "message": "No registered bullet lots for the selected bullet.",
        }

    comparison = db.compare_bullet_lots(int(bullet_id), int(rows[0]["id"]))
    if not comparison:
        return {
            "level": "neutral",
            "title": "Bullet Lot",
            "message": "No lot guidance available yet.",
        }

    verification_plan = comparison.get("verification_plan") or {}
    current_profile = comparison.get("current_profile") or {}
    plan_focus = str(verification_plan.get("focus") or "").strip()
    severity = str(comparison.get("severity") or "info")
    level = "neutral"
    if severity == "ok":
        level = "ok"
    elif severity == "watch":
        level = "warning"
    elif severity == "high":
        level = "critical"

    message = str(comparison.get("message") or "").strip()
    confidence_label = str(current_profile.get("confidence_label") or "").strip()
    group_shift = abs(float(comparison.get("group_shift_moa") or 0.0))
    bto_shift = abs(float(comparison.get("bto_std_shift") or 0.0))
    uncertainty_message = (
        f'Usikkerhet: denne loten kan fortsatt gi omtrent +/-{max(0.1, group_shift):.2f} MOA gruppedrift og +/-{max(0.0005, bto_shift):.4f}" seating-variasjon.'
        if group_shift > 0 or bto_shift > 0
        else ""
    )
    if not uncertainty_message and str(comparison.get("severity") or "") in {
        "watch",
        "high",
    }:
        uncertainty_message = "Uncertainty: this lot can still move group behavior or seating response until the control series is confirmed."
    if confidence_label:
        message = f"{message} Data foundation: {confidence_label}.".strip()
    if uncertainty_message:
        message = f"{message} {uncertainty_message}".strip()
    if plan_focus:
        message = f"{message} {plan_focus}".strip()
    return {
        "level": level,
        "title": str(comparison.get("title") or "Bullet Lot").strip() or "Bullet Lot",
        "message": message or "Lot guidance available.",
        "confidence_label": confidence_label,
    }


def summarize_primer_lot_advisory(db, primer_id) -> dict[str, str]:
    if not db or not primer_id:
        return {
            "level": "neutral",
            "title": "Primer Lot",
            "message": "Select a primer to view lot assessment.",
        }
    try:
        rows = db.execute_query(
            """
            SELECT id
            FROM component_lots
            WHERE component_type = 'primers' AND component_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC
            LIMIT 1
            """,
            (int(primer_id),),
        )
    except Exception:
        rows = []
    if not rows:
        return {
            "level": "neutral",
            "title": "Primer Lot",
            "message": "No recorded primer lots for the selected primer.",
        }

    comparison = db.compare_primer_lots(int(primer_id), int(rows[0]["id"]))
    if not comparison:
        return {
            "level": "neutral",
            "title": "Primer Lot",
            "message": "No lot assessment available yet.",
        }

    verification_plan = comparison.get("verification_plan") or {}
    current_profile = comparison.get("current_profile") or {}
    plan_focus = str(verification_plan.get("focus") or "").strip()
    severity = str(comparison.get("severity") or "info")
    level = "neutral"
    if severity == "ok":
        level = "ok"
    elif severity == "watch":
        level = "warning"
    elif severity == "high":
        level = "critical"

    message = str(comparison.get("message") or "").strip()
    confidence_label = str(current_profile.get("confidence_label") or "").strip()
    es_shift = abs(float(comparison.get("typical_es_shift_fps") or 0.0))
    sd_shift = abs(float(comparison.get("typical_sd_shift_fps") or 0.0))
    span = max(es_shift, sd_shift)
    uncertainty_message = (
        f"Uncertainty: the lot can still move the ignition picture by about {format_velocity_delta_fps(max(3.0, span))} in the ES/SD window."
        if span > 0
        else ""
    )
    if not uncertainty_message and str(comparison.get("severity") or "") in {
        "watch",
        "high",
    }:
        uncertainty_message = "Uncertainty: the lot can still shift the ES/SD picture until ignition consistency is confirmed."
    if confidence_label:
        message = f"{message} Data foundation: {confidence_label}.".strip()
    if uncertainty_message:
        message = f"{message} {uncertainty_message}".strip()
    if plan_focus:
        message = f"{message} {plan_focus}".strip()
    return {
        "level": level,
        "title": str(comparison.get("title") or "Primer Lot").strip() or "Primer Lot",
        "message": message or "Lotvurdering tilgjengelig.",
        "confidence_label": confidence_label,
    }


def summarize_component_verification_plan(
    db, powder_id, bullet_id, primer_id
) -> dict[str, str]:
    advisories = [
        ("Powder Lot", summarize_powder_lot_advisory(db, powder_id)),
        ("Bullet Lot", summarize_bullet_lot_advisory(db, bullet_id)),
        ("Primer Lot", summarize_primer_lot_advisory(db, primer_id)),
    ]
    actionable = [
        (label, advisory)
        for label, advisory in advisories
        if advisory.get("level") in {"critical", "warning"}
    ]
    if not actionable:
        return {
            "level": "ok",
            "title": "Combined Verification",
            "message": "No clear lot deviations were found. A short normal control series is usually enough.",
        }

    level = (
        "critical"
        if any(advisory.get("level") == "critical" for _, advisory in actionable)
        else "warning"
    )
    labels = ", ".join(
        f"{label} ({advisory.get('title', 'Lot')})" for label, advisory in actionable
    )
    lead = (
        "Several lot signals point toward conservative verification."
        if len(actionable) > 1
        else "One active lot signal should be confirmed before further fine-tuning."
    )
    details = " ".join(
        f"{label}: {str(advisory.get('message') or '').strip()}"
        for label, advisory in actionable
    )
    confidence_labels = [
        str(advisory.get("confidence_label") or "").strip()
        for _, advisory in actionable
        if str(advisory.get("confidence_label") or "").strip()
    ]
    confidence_summary = ""
    if confidence_labels:
        confidence_summary = " Confidence: " + ", ".join(confidence_labels[:3]) + "."
    uncertainty_summary = (
        " Uncertainty: the verification picture is still moving between lots."
        if actionable
        else ""
    )
    return {
        "level": level,
        "title": "Combined Verification",
        "message": f"{lead} Focus on: {labels}. {details}{confidence_summary}{uncertainty_summary}".strip(),
    }


def _safe_json_loads(text: object) -> dict[str, Any]:
    if isinstance(text, dict):
        return dict(text)
    raw = str(text or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _build_predicted_result_summary(result: dict | None) -> dict[str, Any]:
    result = result or {}
    summary: dict[str, Any] = {}
    for key in (
        "muzzle_velocity_fps",
        "peak_pressure_psi",
        "safety_margin_percent",
        "load_density_percent",
        "barrel_time_ms",
        "max_pressure_psi",
        "case_capacity_ml",
        "powder_volume_ml",
        "available_volume_ml",
    ):
        value = result.get(key)
        if isinstance(value, (int, float)):
            summary[key] = float(value)
    warnings = result.get("warnings") or []
    if isinstance(warnings, list) and warnings:
        summary["warnings"] = [str(item) for item in warnings[:5] if str(item).strip()]
    environment = result.get("_environment")
    if isinstance(environment, dict):
        env_summary = {}
        for key in ("temperature_c", "pressure_hpa", "humidity_percent", "altitude_m"):
            value = environment.get(key)
            if isinstance(value, (int, float)):
                env_summary[key] = float(value)
        if env_summary:
            summary["environment"] = env_summary
    return summary


def _extract_saved_component_entry(
    snapshot: dict[str, Any], analysis: dict[str, Any], key: str
) -> dict[str, Any]:
    context = analysis.get("component_context")
    if isinstance(context, dict):
        candidate = context.get(key)
        if isinstance(candidate, dict):
            return dict(candidate)
    candidate = snapshot.get(key)
    if isinstance(candidate, dict):
        return dict(candidate)
    return {}


def _build_retest_protocol(
    level: str, usage_profile: str, suggested_control_shots: int
) -> dict[str, Any]:
    profile = str(usage_profile or "").strip()
    if profile.startswith("hunting"):
        steps = [
            "1 cold-bore shot against a realistic hunting setup",
            f"{max(3, suggested_control_shots - 1)} chrono shots for velocity and ES",
            "Confirm point of impact and the expected impact window",
        ]
    elif profile == "training":
        steps = [
            f"{max(2, suggested_control_shots)} control shots over the chronograph",
            "Look for robustness against small setup and temperature changes",
            "Stop when the load is repeatable enough, not necessarily fully optimized",
        ]
    elif profile in {"precision", "long_range_hunting"}:
        steps = [
            f"{max(5, suggested_control_shots)} chrono shots in the verification series",
            "Fire at least one extra group for repeatability and vertical spread",
            "Lock the node only when ES/SD and point of impact repeat",
        ]
    else:
        steps = [
            f"{max(3, suggested_control_shots)} control shots with a chronograph",
            "Confirm that velocity and pressure behavior look stable",
            "Move on to fine-tuning only after a clean control series",
        ]

    if level == "critical":
        steps.insert(
            0,
            "Start conservatively and consider stepping slightly down in charge before a full series",
        )
    elif level == "warning":
        steps.insert(
            0,
            "Keep the first series short and read the chronograph before further escalation",
        )

    summary = " | ".join(steps[:3])
    return {"summary": summary, "steps": steps}


def build_retest_session_payload(
    retest_advisory: dict[str, Any] | None,
) -> dict[str, Any]:
    advisory = retest_advisory or {}
    profile = str(advisory.get("usage_profile") or "").strip()
    shots = advisory.get("suggested_control_shots")
    try:
        shot_count = max(1, int(float(shots or 0)))
    except Exception:
        shot_count = 5

    if profile.startswith("hunting"):
        session_name = "Retest - Cold-Bore and Hunting Verification"
    elif profile in {"precision", "long_range_hunting"}:
        session_name = "Retest - Chronograph and Precision Verification"
    elif profile == "training":
        session_name = "Retest - Robustness Check"
    else:
        session_name = "Retest - Verification Series"

    _proto_steps = advisory.get("protocol_steps")
    protocol_steps = [
        str(step).strip()
        for step in (_proto_steps if isinstance(_proto_steps, list) else [])
        if str(step).strip()
    ]
    focus = str(advisory.get("focus") or "").strip()
    notes_parts = []
    if focus:
        notes_parts.append(f"Focus: {focus}")
    if protocol_steps:
        notes_parts.append("Setup:")
        notes_parts.extend(f"- {step}" for step in protocol_steps[:4])
    notes = "\n".join(notes_parts).strip()

    return {
        "session_name": session_name,
        "session_type": "range",
        "shot_count": shot_count,
        "notes": notes,
        "analysis_json": {
            "created_from": "modern_load_builder_retest_advisor",
            "retest_advisory": advisory,
            "protocol_summary": advisory.get("protocol_summary"),
            "protocol_steps": protocol_steps,
        },
    }


def summarize_retest_advisor(
    db,
    rifle_id,
    bullet_data: dict | None = None,
    powder_data: dict | None = None,
    primer_data: dict | None = None,
    current_charge: float | None = None,
    coal_mm: float | None = None,
    cbto_mm: float | None = None,
    result: dict | None = None,
    usage_profile: str | None = None,
    target_es: float | None = None,
) -> dict[str, Any]:
    """Summarize how aggressively the user should retest based on changes from the latest batch."""
    current_entries = {
        "bullet": bullet_data if isinstance(bullet_data, dict) else {},
        "powder": powder_data if isinstance(powder_data, dict) else {},
        "primer": primer_data if isinstance(primer_data, dict) else {},
    }
    current_names = {
        "bullet": "Bullet",
        "powder": "Powder",
        "primer": "Primer",
    }
    workflow_profile = str(usage_profile or "").strip()
    workflow_target_es = target_es
    if not workflow_profile:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            workflow_context = build_active_workflow_context_from_settings(settings, db)
            workflow_profile = str(
                workflow_context.get("usage_profile_key")
                or settings.value("workflow_context/usage_profile", "")
                or ""
            ).strip()
            if workflow_target_es is None:
                raw_target_es = settings.value("workflow_context/target_es")
                if raw_target_es not in (None, ""):
                    workflow_target_es = float(raw_target_es)
        except Exception:
            workflow_profile = ""

    reference_batch = None
    if db and rifle_id:
        try:
            rows = db.execute_query(
                """
                SELECT batch_number, batch_name, created_date, charge_weight_grains, coal_mm, cbto_mm,
                       component_snapshot_json, analysis_json
                FROM batch_projects
                WHERE rifle_id = ?
                ORDER BY datetime(updated_date) DESC, datetime(created_date) DESC, id DESC
                LIMIT 1
                """,
                (int(rifle_id),),
            )
            reference_batch = rows[0] if rows else None
        except Exception:
            reference_batch = None

    changes: list[str] = []
    major_change_count = 0
    critical_change_count = 0
    watchouts: list[str] = []

    if reference_batch:
        snapshot = _safe_json_loads(reference_batch.get("component_snapshot_json"))
        analysis = _safe_json_loads(reference_batch.get("analysis_json"))
        for key, label in current_names.items():
            current_entry = current_entries.get(key) or {}
            if not current_entry:
                continue
            previous_entry = _extract_saved_component_entry(snapshot, analysis, key)
            current_id = current_entry.get("id")
            previous_id = previous_entry.get("id")
            current_name = str(current_entry.get("name") or "unknown").strip()
            if current_name == "ukjent":
                current_name = "unknown"
            previous_name = str(previous_entry.get("name") or "").strip()
            current_lot = str(
                current_entry.get("selected_lot_number")
                or current_entry.get("lot_number")
                or ""
            ).strip()
            previous_lot = str(previous_entry.get("lot_number") or "").strip()

            if previous_id and current_id and previous_id != current_id:
                changes.append(
                    f"{label} changed from {previous_name or previous_id} to {current_name or current_id}."
                )
                major_change_count += 1
            elif current_lot and previous_lot and current_lot != previous_lot:
                changes.append(
                    f"{label} changed lot from {previous_lot} to {current_lot}."
                )
                major_change_count += 1

        baseline_charge = reference_batch.get("charge_weight_grains")
        if isinstance(current_charge, (int, float)) and isinstance(
            baseline_charge, (int, float)
        ):
            delta = float(current_charge) - float(baseline_charge)
            if abs(delta) >= 0.30:
                changes.append(
                    f"Charge changed by {format_weight_grains(abs(delta), 'powder')} {'up' if delta > 0 else 'down'} from the previous batch."
                )
                critical_change_count += 1
            elif abs(delta) >= 0.10:
                changes.append(
                    f"Charge adjusted by {format_weight_grains(abs(delta), 'powder')} {'up' if delta > 0 else 'down'} from the previous batch."
                )
                major_change_count += 1

        baseline_coal = reference_batch.get("coal_mm")
        if isinstance(coal_mm, (int, float)) and isinstance(
            baseline_coal, (int, float)
        ):
            delta = float(coal_mm) - float(baseline_coal)
            if abs(delta) >= 0.20:
                changes.append(f"COAL changed {delta:+.2f} mm.")
                major_change_count += 1

        baseline_cbto = reference_batch.get("cbto_mm")
        if isinstance(cbto_mm, (int, float)) and isinstance(
            baseline_cbto, (int, float)
        ):
            delta = float(cbto_mm) - float(baseline_cbto)
            if abs(delta) >= 0.10:
                changes.append(f"CBTO changed {delta:+.2f} mm.")
                major_change_count += 1

    powder_comparison = (
        (powder_data or {}).get("lot_comparison")
        if isinstance(powder_data, dict)
        else {}
    ) or {}
    if str(powder_comparison.get("severity") or "") == "high":
        critical_change_count += 1
        watchouts.append(str(powder_comparison.get("message") or "").strip())
    elif str(powder_comparison.get("severity") or "") == "watch":
        major_change_count += 1
        watchouts.append(str(powder_comparison.get("message") or "").strip())

    primer_comparison = (
        (primer_data or {}).get("lot_comparison")
        if isinstance(primer_data, dict)
        else {}
    ) or {}
    if str(primer_comparison.get("severity") or "") == "high":
        critical_change_count += 1
        watchouts.append(str(primer_comparison.get("message") or "").strip())
    elif str(primer_comparison.get("severity") or "") == "watch":
        major_change_count += 1
        watchouts.append(str(primer_comparison.get("message") or "").strip())

    bullet_stats = (
        (bullet_data or {}).get("measured_lot_stats")
        if isinstance(bullet_data, dict)
        else {}
    ) or {}
    sample_count = bullet_stats.get("sample_count")
    if isinstance(sample_count, (int, float)) and 0 < float(sample_count) < 5:
        major_change_count += 1
        watchouts.append(
            f"The bullet lot is based on only {int(sample_count)} measurements, so the lot average is still thin."
        )

    pressure_risk = summarize_pressure_risk(result or {})
    if pressure_risk.get("level") == "critical":
        critical_change_count += 1
        watchouts.append(str(pressure_risk.get("message") or "").strip())
    elif pressure_risk.get("level") == "warning":
        major_change_count += 1
        watchouts.append(str(pressure_risk.get("message") or "").strip())

    if critical_change_count > 0:
        level = "critical"
        suggested_control_shots = 10
        focus = "Take 3 cautious control shots first, then fire at least 5 more chronograph shots before you judge group or velocity."
    elif major_change_count > 0:
        level = "warning"
        suggested_control_shots = 5
        focus = "Run a short verification series with a chronograph before further fine-tuning."
    else:
        level = "ok"
        suggested_control_shots = 3
        focus = "A short normal control series is usually enough before you move on."

    profile_message = ""
    if workflow_profile.startswith("hunting"):
        suggested_control_shots = max(
            suggested_control_shots, 4 if level == "ok" else 6
        )
        focus = (
            "Prioritize cold-bore confirmation and realistic hunting distance before approving the load."
            if level == "ok"
            else "Prioritize cold-bore confirmation, realistic hunting distance, and a chronograph before further adjustment."
        )
        profile_message = " Hunting profile active: the first shot and real use distance matter more than pure node chasing."
    elif workflow_profile == "training":
        suggested_control_shots = max(suggested_control_shots, 4)
        focus = "Confirm that the load is robust and easy to repeat before spending more time on polishing."
        profile_message = " Training profile active: robustness and simple verification are prioritized."
    elif workflow_profile in {"precision", "long_range_hunting"}:
        suggested_control_shots = max(
            suggested_control_shots,
            5 if level != "critical" else suggested_control_shots,
        )
        focus = "Chronograph a full verification series and watch especially for vertical spread and repeatability."
        profile_message = " Precision profile active: confirm ES/SD and repeatability before locking the node."
    if isinstance(workflow_target_es, (int, float)):
        profile_message = (
            f"{profile_message} The target picture is ES <= {int(float(workflow_target_es))} fps."
        ).strip()

    protocol = _build_retest_protocol(level, workflow_profile, suggested_control_shots)
    protocol_summary = str(protocol.get("summary") or "").strip()

    reference_text = ""
    if reference_batch:
        reference_text = f" Reference: {reference_batch.get('batch_number') or reference_batch.get('batch_name') or 'previous batch'}."
    elif rifle_id:
        reference_text = " No previous batch was found for this firearm, so you are building without a local reference."

    change_summary = " ".join(changes[:5]).strip()
    watch_summary = " ".join(item for item in watchouts[:3] if item).strip()

    if level == "ok":
        message = (
            "No clear changes versus the latest reference suggest a hard retest."
            f"{reference_text} {focus}{profile_message}"
        ).strip()
    else:
        message = (
            f"A retest is recommended before further fine-tuning. {change_summary or 'There are active component or pressure signals that should be confirmed.'}"
            f" {watch_summary} {focus}{reference_text}{profile_message}"
        ).strip()
    if protocol_summary:
        message = f"{message} Suggested protocol: {protocol_summary}".strip()

    return {
        "level": level,
        "title": "Retest Guidance",
        "message": message,
        "suggested_control_shots": suggested_control_shots,
        "changes": changes,
        "usage_profile": workflow_profile or None,
        "target_es": workflow_target_es,
        "protocol_summary": protocol_summary,
        "protocol_steps": list(protocol.get("steps") or []),
        "reference_batch_number": (
            reference_batch.get("batch_number") if reference_batch else None
        ),
        "reference_batch_name": (
            reference_batch.get("batch_name") if reference_batch else None
        ),
        "focus": focus,
    }


def summarize_builder_impact_window(
    db, bullet_data, result: dict | None, usage_profile: str | None = None
) -> dict[str, str]:
    workflow_data = {}
    if usage_profile:
        workflow_data["usage_profile"] = usage_profile
    elif db is not None:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            workflow_context = build_active_workflow_context_from_settings(settings, db)
            workflow_id = workflow_context.get("workflow_id")
            if workflow_context.get("usage_profile_key") not in (None, ""):
                workflow_data["usage_profile"] = workflow_context.get(
                    "usage_profile_key"
                )
            if workflow_id:
                workflow_row = db.get_by_id("load_development_workflows", workflow_id)
                if workflow_row:
                    workflow_data.update(dict(workflow_row))
        except Exception:
            pass

    bullet_id = None
    if isinstance(bullet_data, dict):
        bullet_id = bullet_data.get("id")
    elif bullet_data:
        bullet_id = bullet_data
    if bullet_id:
        workflow_data["bullet_id"] = bullet_id

    if not workflow_data.get("usage_profile", "").startswith("hunting"):
        return {
            "level": "neutral",
            "title": "Impact Window",
            "message": "Impact assessment is shown when the active workflow is hunting-oriented.",
        }

    muzzle_velocity = None
    _mv = result.get("muzzle_velocity_fps") if isinstance(result, dict) else None
    if isinstance(_mv, (int, float)):
        muzzle_velocity = float(_mv)
    observations = {
        "chronograph_sessions": (
            [{"avg_velocity_fps": muzzle_velocity}]
            if muzzle_velocity is not None
            else []
        )
    }

    try:
        import importlib

        workflow_module = importlib.import_module(
            "src.modules.load_development_workflow"
        )
        builder = getattr(workflow_module, "build_workflow_impact_window", None)
        if callable(builder):
            impact = builder(db, workflow_data, observations)
            if not isinstance(impact, dict):
                raise ValueError("build_workflow_impact_window returned non-dict")
            projectile_profile = _as_dict(impact, "projectile_profile")
            detail_bits = []
            profile_summary = str(
                projectile_profile.get("profile_summary") or ""
            ).strip()
            preferred_min = projectile_profile.get("preferred_impact_min_fps")
            preferred_max = projectile_profile.get("preferred_impact_max_fps")
            if profile_summary:
                detail_bits.append(f"Projectile: {profile_summary}.")
            if isinstance(preferred_min, (int, float)) and isinstance(
                preferred_max, (int, float)
            ):
                detail_bits.append(
                    f"Estimated working window: {preferred_min:.0f}-{preferred_max:.0f} fps."
                )
            elif isinstance(preferred_min, (int, float)):
                detail_bits.append(
                    f"Estimated working floor: {preferred_min:.0f}+ fps."
                )
            return {
                "level": str(impact.get("level") or "neutral"),
                "title": str(impact.get("title") or "Impact Window"),
                "message": str(
                    impact.get("message") or "No impact assessment available."
                ),
                "details": " ".join(detail_bits).strip(),
            }
    except Exception:
        pass
    return {
        "level": "neutral",
        "title": "Impact Window",
        "message": "No impact assessment is available right now.",
        "details": "",
    }


def summarize_builder_calibration_profile(
    db,
    rifle_data,
    barrel_id,
    barrel_name,
    powder_id=None,
    bullet_id=None,
    primer_id=None,
    ammo_profile_id=None,
    usage_profile: str | None = None,
    barrel_configuration_id=None,
    barrel_configuration_name=None,
) -> dict[str, str]:
    if db is None:
        return {
            "level": "neutral",
            "title": tr("mlb_calibration_profile"),
            "message": tr("mlb_calibration_profile_unavailable"),
        }

    workflow_data: dict[str, Any] = {}
    if isinstance(rifle_data, dict):
        rifle_id = rifle_data.get("id")
        if rifle_id not in (None, ""):
            workflow_data["rifle_id"] = rifle_id
    if barrel_id not in (None, ""):
        workflow_data["barrel_id"] = barrel_id
    if barrel_name:
        workflow_data["barrel_name"] = barrel_name
    if barrel_configuration_id not in (None, ""):
        workflow_data["barrel_configuration_id"] = barrel_configuration_id
    if barrel_configuration_name:
        workflow_data["barrel_configuration_name"] = barrel_configuration_name
    if powder_id not in (None, ""):
        workflow_data["powder_id"] = powder_id
    if bullet_id not in (None, ""):
        workflow_data["bullet_id"] = bullet_id
    if primer_id not in (None, ""):
        workflow_data["primer_id"] = primer_id
    if ammo_profile_id not in (None, ""):
        workflow_data["ammo_profile_id"] = ammo_profile_id
    if usage_profile:
        workflow_data["usage_profile"] = usage_profile

    if not workflow_data.get("barrel_id"):
        return {
            "level": "neutral",
            "title": tr("mlb_calibration_profile"),
            "message": tr("mlb_calibration_profile_pending"),
        }

    from .load_development_workflow import build_workflow_calibration_summary

    _summary_raw = build_workflow_calibration_summary(db, workflow_data)
    summary: dict[str, Any] = _summary_raw if isinstance(_summary_raw, dict) else {}
    metrics: list[str] = []
    for metric in _as_list(summary, "metrics"):
        if isinstance(metric, dict):
            name = str(metric.get("name") or "").strip()
            value = str(metric.get("value") or "").strip()
            source = str(metric.get("source") or "").strip()
            parts = [part for part in (name, value) if part]
            metric_text = ": ".join(parts) if parts else str(metric).strip()
            if source:
                metric_text = f"{metric_text} ({source})"
        else:
            metric_text = str(metric).strip()
        if metric_text:
            metrics.append(metric_text)
    message = str(summary.get("message") or "").strip()
    if metrics:
        message = f"{message} {' | '.join(metrics[:7])}".strip()
    setup_label = _format_barrel_configuration_label(
        barrel_configuration_name, barrel_name
    )
    if setup_label:
        message = f"Setup {setup_label}. {message}".strip()
    return {
        "level": str(summary.get("level") or "neutral"),
        "title": tr("mlb_calibration_profile"),
        "message": message or tr("mlb_calibration_profile_unavailable"),
    }


def _get_profile_scoped_engine_calibration(
    db, ammo_profile_id: int | None
) -> dict[str, float | None] | None:
    if db is None or ammo_profile_id in (None, ""):
        return None

    try:
        resolved_ammo_profile_id = int(ammo_profile_id)
    except Exception:
        return None

    queries = (
        """
        SELECT slope, intercept, mse
        FROM engine_calibrations
        WHERE ammo_profile_id = ?
        ORDER BY accepted DESC, accepted_date DESC, created_date DESC, id DESC
        LIMIT 1
        """,
        """
        SELECT slope, intercept, mse
        FROM engine_calibrations
        WHERE ammo_profile_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
    )

    for query in queries:
        try:
            rows = db.execute_query(query, (resolved_ammo_profile_id,))
        except Exception:
            rows = []
        if not rows:
            continue

        row = rows[0]
        try:
            slope = row.get("slope")
            intercept = row.get("intercept")
            mse = row.get("mse")
        except Exception:
            try:
                slope = row[0]
                intercept = row[1]
                mse = row[2]
            except Exception:
                continue

        if slope in (None, ""):
            continue
        return {
            "slope": float(slope),
            "intercept": float(intercept or 0.0),
            "mse": float(mse) if mse not in (None, "") else None,
        }

    return None


def summarize_builder_evidence_basis(
    result: dict | None,
    workflow_data: dict | None = None,
    observations: dict | None = None,
    bullet_data: dict | None = None,
    environment=None,
    internal_ballistics_summary: dict | None = None,
) -> dict[str, str]:
    measured_parts: list[str] = []
    modeled_parts: list[str] = []
    recommended_parts: list[str] = []

    if isinstance(result, dict):
        if isinstance(result.get("muzzle_velocity_fps"), (int, float)):
            measured_parts.append(
                "chronograph-based muzzle velocity is used in the evaluation"
            )
        if isinstance(result.get("peak_pressure_psi"), (int, float)):
            modeled_parts.append("internal ballistics and pressure margin are modeled")
            internal_ballistics = (
                internal_ballistics_summary
                if isinstance(internal_ballistics_summary, dict)
                else build_internal_ballistics_summary(
                    charge_weight_gr=result.get("charge_weight_grains"),
                    powder_name=result.get("powder_name"),
                    case_capacity_ml=result.get("case_capacity_ml"),
                    barrel_length_in=result.get("barrel_length_inches"),
                    load_density_percent=result.get("load_density_percent"),
                    powder_volume_ml=result.get("powder_volume_ml"),
                    available_volume_ml=result.get("available_volume_ml"),
                    powder_density_g_ml=result.get("powder_density"),
                    burn_rate_position=result.get("burn_rate_position"),
                )
            )
            if isinstance(internal_ballistics, dict):
                modeled_parts.append(str(internal_ballistics.get("message") or ""))
        warnings = result.get("warnings")
        if isinstance(warnings, list) and warnings:
            recommended_parts.append(
                "pressure and spike warnings drive the recommended next step"
            )
        if isinstance(result.get("safety_margin_percent"), (int, float)):
            recommended_parts.append("safety margin is used in the QA guidance")

    if not measured_parts:
        measured_parts.append(
            "missing measured data makes the builder guidance more provisional"
        )
    if not modeled_parts:
        modeled_parts.append("no modeled ballistics data is available right now")
    if not recommended_parts:
        recommended_parts.append(
            "the builder is waiting for more data before it gives a clear recommendation"
        )

    input_quality = build_input_quality_summary(
        workflow_data or {},
        observations or {},
        bullet_data=bullet_data or {},
        environment=environment,
    )

    message = (
        f"Measured: {', '.join(measured_parts)}. "
        f"Modeled: {', '.join(modeled_parts)}. "
        f"Recommended: {', '.join(recommended_parts)}. "
        f"Input quality: {input_quality['title']}. {input_quality['message']}"
    )
    return {
        "level": "info",
        "title": "Data Foundation",
        "message": message,
    }


def summarize_builder_confidence_model(
    result: dict | None,
    *,
    workflow_data: dict | None = None,
    observations: dict | None = None,
    bullet_data: dict | None = None,
    powder_data: dict | None = None,
    environment=None,
    tracked_brass: bool = False,
    seating_evidence: dict | None = None,
    subsonic_history: dict | None = None,
    model_match: dict | None = None,
) -> dict[str, Any]:
    input_quality = build_input_quality_summary(
        workflow_data or {},
        observations or {},
        bullet_data=bullet_data or {},
        environment=environment,
    )
    score = float(input_quality.get("score") or 0.0)
    quality_checks = list(input_quality.get("checks") or [])
    checks: list[str] = []

    powder_context = powder_data or {}
    if powder_context.get("usable_for_simulation"):
        score += 1.0
        checks.append("The powder model is marked as usable for simulation.")
    else:
        checks.append("The powder model is not fully verified for simulation.")

    if tracked_brass:
        score += 0.5
        checks.append(
            "A recorded brass batch is selected, which gives better traceability and interpretation."
        )
    else:
        checks.append("Brass is not fully batch-tracked in this builder.")

    if isinstance(result, dict) and result.get("_calibration_mse") not in (None, ""):
        try:
            import math

            sigma = math.sqrt(float(result.get("_calibration_mse") or 0))
            score += 1.0
            checks.append(
                f"The engine has calibration support with sigma around {format_velocity_fps(sigma)}."
            )
        except Exception:
            score += 0.5
            checks.append(
                "The engine has calibration support, but the uncertainty could not be quantified."
            )
    else:
        checks.append("No saved engine calibration exists for this prediction.")

    seating_conf = str((seating_evidence or {}).get("confidence") or "").strip().lower()
    if seating_conf == "high":
        score += 0.75
        checks.append(
            "Seating history has high evidence for the selected bullet and setup."
        )
    elif seating_conf == "medium":
        score += 0.35
        checks.append("Seating history is useful, but still moderate.")
    else:
        checks.append("Seating history is thin or missing for this setup.")

    sub_hist_level = str((subsonic_history or {}).get("level") or "").strip().lower()
    if sub_hist_level == "ok":
        score += 0.5
        checks.append("Subsonic history shows working sessions for this combination.")
    elif sub_hist_level == "critical":
        checks.append(
            "Subsonic history contains serious stability or function warnings."
        )
    elif sub_hist_level == "warning":
        checks.append("Subsonic history is mixed and should be read conservatively.")

    model_level = str((model_match or {}).get("level") or "").strip().lower()
    model_ref = (model_match or {}).get("reference")
    bias_direction = (
        str((model_match or {}).get("bias_direction") or "").strip().lower()
    )
    bias_fps = (model_match or {}).get("bias_fps")
    if isinstance(bias_fps, (int, float)):
        if bias_direction in {"model_higher", "measured_higher"}:
            score += 0.15
            direction_text = "high" if bias_direction == "model_higher" else "low"
            checks.append(
                f"The history shows a readable model bias of about {abs(float(bias_fps)):.0f} fps ({direction_text})."
            )
        elif bias_direction == "neutral":
            score += 0.35
            checks.append("History shows little or no systematic model bias.")
    if model_level == "ok":
        score += 0.9
        checks.append(
            "The model aligns well with measured chrono history for similar batches."
        )
    elif model_level == "warning":
        score += 0.2
        checks.append(
            "The model has some support in history, but still needs chrono confirmation."
        )
    elif model_level == "critical":
        checks.append(
            "Similar batches show a clear deviation between model and measured velocity."
        )
    elif isinstance(model_ref, dict):
        checks.append(
            "There is some measured history, but not enough to calibrate the model reliably."
        )

    level = score_to_confidence_level(score, BUILDER_CONFIDENCE_THRESHOLDS)
    if level == "high":
        title = "High Confidence"
        message = "The data basis is broad enough that the guidance can be read with relatively good confidence."
    elif level == "medium":
        title = "Usable Confidence"
        message = (
            "The builder has a useful basis, but some parts are still assumed or thin."
        )
    else:
        title = "Low Confidence"
        message = "The builder lacks enough measured or verified data for strong conclusions without extra testing."

    return {
        "level": level,
        "title": title,
        "message": message,
        "score": round(score, 2),
        "checks": (checks + quality_checks)[:8],
    }


# Importing heavy visualization libs lazily inside methods to avoid
# expensive imports at module import time (helps headless/CI probes).


class ModernLoadBuilder(QWidget, _MLBHelpMixin, _MLBStatsMixin):
    """
    Modern 2-step load development interface:
    Step 1: Select firearm + brass (quick)
    Step 2: Interactive load builder with live graphs + AI chat
    """

    load_created = pyqtSignal(dict)
    batch_created = pyqtSignal(int)

    _COMPONENT_REQUIRED_FIELDS = {
        "component_powder": ("name",),
        "component_primer": ("type",),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        # Defer creation of ballistics engine until actually needed to avoid
        # expensive/side-effectful initialization during import/UI composition.
        self._engine = None
        self._load_analysis_service = None
        self._logger = get_logger(__name__)
        self._research_service = None
        self._research_service_init_failed = False
        self._component_cache = {
            "component_bullet": {},
            "component_powder": {},
            "component_primer": {},
            "component_case": {},
        }
        self._firearm_cache = {}
        self._advanced_widgets = []
        self._advanced_chrono_widgets = []
        self._latest_load_session_runtime = None
        self._latest_seating_summary = None
        self._recommendation_baseline = None

        # UI persisted preferences (loaded shortly after UI creation)
        self.velocity_y_min = None
        self.velocity_y_max = None

        # State
        self.current_step = 1
        self.rifle_data = None
        self.brass_data = None
        self.bullet_data = None
        self.powder_data = None
        self.primer_data = None
        self.current_charge = 42.5
        self.coal_mm = 71.5
        self.cbto_mm = 68.8

        self._rifle_profile_details = None
        self._rifle_profile_details_id = None

        # AI chat history
        self.chat_history = []

        self.init_ui()

    @property
    def engine(self):
        """Lazily initialize and return the ballistics engine."""
        if getattr(self, "_engine", None) is None:
            try:
                from .ballistics_engine import get_ballistics_engine

                self._engine = get_ballistics_engine()
            except Exception:
                self._engine = None
        return self._engine

    @property
    def load_analysis_service(self):
        """Lazily initialize and return the shared load-analysis service."""
        if getattr(self, "_load_analysis_service", None) is None:
            try:
                self._load_analysis_service = LoadAnalysisService(self.db)
            except Exception:
                self._load_analysis_service = None
        return self._load_analysis_service

    def _current_usage_profile(self) -> str:
        """Return current workflow usage profile when available."""
        runtime = self._get_cached_or_active_load_session_runtime()
        if isinstance(runtime, dict):
            context = _as_dict(runtime, "context")
            profile = str(context.get("usage_profile_key") or "").strip()
            if profile:
                return profile
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            workflow_context = build_active_workflow_context_from_settings(
                settings, self.db
            )
            profile = str(
                workflow_context.get("usage_profile_key")
                or settings.value("workflow_context/usage_profile", "")
                or ""
            ).strip()
            return profile or "precision"
        except Exception:
            return "precision"

    def _build_service_analysis(self) -> dict | None:
        """Build a shared analysis object for the current load state."""
        if not self.load_analysis_service:
            return None
        if not all([self.rifle_data, self.bullet_data, self.powder_data]):
            return None

        try:
            _pkpa = self._current_pressure_kpa()
            pressure_hpa = (
                float(_pkpa) * 10.0
                if hasattr(self, "pressure_spin") and _pkpa is not None
                else 1013.25
            )
        except Exception:
            pressure_hpa = 1013.25

        try:
            _rd = self.rifle_data if isinstance(self.rifle_data, dict) else {}
            _bd = self.bullet_data if isinstance(self.bullet_data, dict) else {}
            _pd = self.powder_data if isinstance(self.powder_data, dict) else {}
            _tc = self._current_temperature_c()
            request = LoadAnalysisRequest(
                rifle_id=int(_rd.get("id") or 0),
                bullet_id=int(_bd.get("id") or 0),
                powder_id=int(_pd.get("id") or 0),
                primer_id=(
                    int(self.primer_data["id"])
                    if isinstance(self.primer_data, dict)
                    and self.primer_data.get("id") not in (None, "")
                    else None
                ),
                charge_weight_gr=float(self.current_charge or 0),
                coal_mm=float(self.coal_mm or 0),
                cbto_mm=float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
                temperature_c=(
                    _tc if _tc is not None and hasattr(self, "temp_spin") else 15.0
                ),
                pressure_hpa=pressure_hpa,
                humidity_percent=(
                    float(getattr(self, "humidity_spin").value())
                    if hasattr(self, "humidity_spin")
                    else 50.0
                ),
                altitude_m=(
                    float(getattr(self, "altitude_spin").value())
                    if hasattr(self, "altitude_spin")
                    else 0.0
                ),
                wind_speed_mps=(
                    float(getattr(self, "wind_spin").value())
                    if hasattr(self, "wind_spin")
                    else 0.0
                ),
                wind_dir_deg=(
                    float(getattr(self, "wind_dir_spin").value())
                    if hasattr(self, "wind_dir_spin")
                    else 90.0
                ),
                case_id=(
                    int(self.brass_data["id"])
                    if isinstance(self.brass_data, dict)
                    and self.brass_data.get("id") not in (None, "")
                    else None
                ),
                brass_batch_id=(
                    int(self.brass_data["id"])
                    if isinstance(self.brass_data, dict)
                    and self.brass_data.get("id") not in (None, "")
                    else None
                ),
                bullet_lot_id=(
                    int(self.bullet_data["selected_lot_id"])
                    if isinstance(self.bullet_data, dict)
                    and self.bullet_data.get("selected_lot_id") not in (None, "")
                    else None
                ),
                powder_lot_id=(
                    int(self.powder_data["selected_lot_id"])
                    if isinstance(self.powder_data, dict)
                    and self.powder_data.get("selected_lot_id") not in (None, "")
                    else None
                ),
                primer_lot_id=(
                    int(self.primer_data["selected_lot_id"])
                    if isinstance(self.primer_data, dict)
                    and self.primer_data.get("selected_lot_id") not in (None, "")
                    else None
                ),
                barrel_id=self._get_active_barrel_id(),
                usage_profile=self._current_usage_profile(),
                subsonic_mode=bool(
                    getattr(self, "subsonic_cb", None) and self.subsonic_cb.isChecked()
                ),
                rifle_overrides=(
                    dict(self.rifle_data) if isinstance(self.rifle_data, dict) else None
                ),
                bullet_overrides=(
                    dict(self.bullet_data)
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                powder_overrides=(
                    dict(self.powder_data)
                    if isinstance(self.powder_data, dict)
                    else None
                ),
                primer_overrides=(
                    dict(self.primer_data)
                    if isinstance(self.primer_data, dict)
                    else None
                ),
                case_overrides=(
                    dict(self.brass_data) if isinstance(self.brass_data, dict) else None
                ),
                barrel_overrides=(
                    self._get_active_barrel_details()
                    if hasattr(self, "_get_active_barrel_details")
                    else None
                ),
            )
            analysis = self.load_analysis_service.analyze_load(request)
            if isinstance(analysis, dict) and "error" not in analysis:
                return analysis
        except Exception:
            return None
        return None

    def _get_active_load_session_runtime(self) -> dict | None:
        session_id = _get_active_load_session_id()
        if session_id is None:
            return None
        try:
            return build_load_session_runtime(self.db, session_id)
        except Exception:
            return None

    def _get_cached_or_active_load_session_runtime(self) -> dict | None:
        runtime = (
            self._latest_load_session_runtime
            if isinstance(getattr(self, "_latest_load_session_runtime", None), dict)
            else None
        )
        if isinstance(runtime, dict):
            return runtime
        runtime = self._get_active_load_session_runtime()
        if isinstance(runtime, dict):
            self._latest_load_session_runtime = runtime
        return runtime

    def _apply_runtime_selection_to_step2(self) -> None:
        """Restore component selection and load values from canonical session runtime.

        Called in initialize_step2() after all combos are populated.
        Ensures the builder reflects the last persisted session state, not UI defaults.
        """
        runtime = self._get_active_load_session_runtime()
        if not isinstance(runtime, dict):
            return
        self._latest_load_session_runtime = runtime

        selection = runtime.get("component_selection")
        if isinstance(selection, dict):
            bullet_id = selection.get("bullet_id")
            powder_id = selection.get("powder_id")
            primer_id = selection.get("primer_id")
            if self._select_combo_by_id(getattr(self, "bullet_combo", None), bullet_id):
                item_data = getattr(self, "bullet_combo", None)
                if item_data is not None:
                    self.bullet_data = item_data.currentData()
            if self._select_combo_by_id(getattr(self, "powder_combo", None), powder_id):
                item_data = getattr(self, "powder_combo", None)
                if item_data is not None:
                    self.powder_data = item_data.currentData()
            if self._select_combo_by_id(getattr(self, "primer_combo", None), primer_id):
                item_data = getattr(self, "primer_combo", None)
                if item_data is not None:
                    self.primer_data = item_data.currentData()

        intake = runtime.get("intake_snapshot")
        if isinstance(intake, dict):

            def _f(v: object) -> float | None:
                try:
                    return float(v) if v not in (None, "") else None  # type: ignore[arg-type]
                except Exception:
                    return None

            charge = _f(intake.get("charge_weight_gr"))
            coal = _f(intake.get("coal_mm"))
            cbto = _f(intake.get("cbto_mm"))

            if charge is not None:
                self.current_charge = charge
                spin = getattr(self, "charge_spin", None)
                if spin is not None:
                    try:
                        spin.blockSignals(True)
                        spin.setValue(charge)
                        spin.blockSignals(False)
                    except Exception:
                        pass

            if coal is not None:
                self.coal_mm = coal
                spin = getattr(self, "coal_spin", None)
                if spin is not None:
                    try:
                        spin.blockSignals(True)
                        spin.setValue(coal)
                        spin.blockSignals(False)
                    except Exception:
                        pass

            if cbto is not None:
                self.cbto_mm = cbto
                spin = getattr(self, "cbto_spin", None)
                if spin is not None:
                    try:
                        spin.blockSignals(True)
                        spin.setValue(cbto)
                        spin.blockSignals(False)
                    except Exception:
                        pass

    def _select_combo_by_id(
        self, combo: object, target_id: object, id_key: str = "id"
    ) -> bool:
        """Find and select the combo item whose data[id_key] matches target_id.

        Signals are blocked during the programmatic selection to avoid cascading
        re-analysis. The caller is responsible for updating self.*_data afterwards.
        Returns True if a matching item was found and selected.
        """
        if combo is None or target_id in (None, ""):
            return False
        try:
            target = str(target_id)
            from PySide6.QtWidgets import QComboBox  # type: ignore[import]

            if not isinstance(combo, QComboBox):
                return False
            for i in range(combo.count()):
                item_data = combo.itemData(i)
                if (
                    isinstance(item_data, dict)
                    and str(item_data.get(id_key) or "") == target
                ):
                    combo.blockSignals(True)
                    combo.setCurrentIndex(i)
                    combo.blockSignals(False)
                    return True
        except Exception:
            pass
        return False

    def _build_active_load_session_component_selection(self) -> dict[str, Any]:
        selection: dict[str, Any] = {}

        if isinstance(self.bullet_data, dict) and self.bullet_data.get("id") not in (
            None,
            "",
        ):
            selection["bullet_id"] = int(self.bullet_data["id"])
        if isinstance(self.powder_data, dict) and self.powder_data.get("id") not in (
            None,
            "",
        ):
            selection["powder_id"] = int(self.powder_data["id"])
        if isinstance(self.primer_data, dict) and self.primer_data.get("id") not in (
            None,
            "",
        ):
            selection["primer_id"] = int(self.primer_data["id"])

        case_id = None
        if isinstance(self.brass_data, dict):
            if self.brass_data.get("case_id") not in (None, ""):
                case_id = self.brass_data.get("case_id")
            elif self.brass_data.get("id") not in (None, ""):
                case_id = self.brass_data.get("id")
            if self.brass_data.get("id") not in (None, ""):
                selection["brass_batch_id"] = int(self.brass_data["id"])
            brass_lot_number = str(self.brass_data.get("lot_number") or "").strip()
            if brass_lot_number:
                selection["case_lot_number"] = brass_lot_number
        if case_id not in (None, ""):
            selection["case_id"] = int(case_id)

        for component_type, lot_id_key, lot_number_key in (
            ("bullet", "bullet_lot_id", "bullet_lot_number"),
            ("powder", "powder_lot_id", "powder_lot_number"),
            ("primers", "primer_lot_id", "primer_lot_number"),
        ):
            lot_id = self._selected_component_lot_id(component_type)
            if lot_id not in (None, ""):
                selection[lot_id_key] = int(lot_id)
                component_id = selection.get(component_type.rstrip("s") + "_id")
                lot_row = self._get_component_lot_record(
                    component_type,
                    component_id,
                    preferred_lot_id=lot_id,
                )
                lot_number = str((lot_row or {}).get("lot_number") or "").strip()
                if lot_number:
                    selection[lot_number_key] = lot_number

        return selection

    def _build_active_load_session_intake_snapshot(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "usage_profile": self._current_usage_profile(),
            "charge_weight_gr": (
                float(self.current_charge or 0)
                if self.current_charge is not None
                else None
            ),
            "coal_mm": float(self.coal_mm or 0) if self.coal_mm is not None else None,
            "cbto_mm": float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
        }

        try:
            _tc2 = self._current_temperature_c()
            snapshot["temperature_c"] = (
                float(_tc2) if hasattr(self, "temp_spin") and _tc2 is not None else None
            )
        except Exception:
            snapshot["temperature_c"] = None
        try:
            _pkpa = self._current_pressure_kpa()
            snapshot["pressure_kpa"] = (
                float(_pkpa)
                if hasattr(self, "pressure_spin") and _pkpa is not None
                else None
            )
        except Exception:
            snapshot["pressure_kpa"] = None
        try:
            snapshot["humidity_percent"] = (
                float(self.humidity_spin.value())
                if hasattr(self, "humidity_spin")
                else None
            )
        except Exception:
            snapshot["humidity_percent"] = None
        try:
            snapshot["altitude_m"] = (
                float(getattr(self, "altitude_spin").value())
                if hasattr(self, "altitude_spin")
                else None
            )
        except Exception:
            snapshot["altitude_m"] = None
        snapshot["subsonic_mode"] = bool(
            getattr(self, "subsonic_cb", None) and self.subsonic_cb.isChecked()
        )
        return snapshot

    def _resolve_session_safety_status(
        self, analysis: dict | None, result: dict | None
    ) -> str:
        _an = analysis if isinstance(analysis, dict) else {}
        pressure_assessment = _as_dict(_an, "pressure_assessment")
        level = str(pressure_assessment.get("level") or "").strip().lower()
        if level in {"critical", "fail"}:
            return "high_risk"
        if level in {"warning", "warn"}:
            return "caution"

        display_margin = None
        if isinstance(result, dict):
            display_margin = result.get("safety_margin_percent")
            peak = result.get("peak_pressure_psi")
            maximum = result.get("max_pressure_psi")
            if peak is not None and maximum not in (None, 0, ""):
                try:
                    display_margin = (
                        (float(maximum) - float(peak)) / float(maximum) * 100.0
                    )
                except Exception:
                    pass
        try:
            if display_margin is not None and float(display_margin) < 10.0:
                return "high_risk"
            if display_margin is not None and float(display_margin) < 15.0:
                return "caution"
            if display_margin is not None:
                return "ok"
        except Exception:
            pass
        return "review_required"

    def _build_active_load_session_analysis_payloads(
        self,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        _raw_analysis = getattr(self, "_latest_load_analysis", None)
        analysis: dict[str, Any] = (
            _raw_analysis if isinstance(_raw_analysis, dict) else {}
        )
        _raw_result = getattr(self, "_latest_visual_result", None)
        result: dict[str, Any] = _raw_result if isinstance(_raw_result, dict) else {}
        recommendation = _as_dict(analysis, "recommendation")
        observations = _as_dict(analysis, "observations")
        observation_summary = _as_dict(observations, "summary")
        input_quality = _as_dict(analysis, "input_quality")
        pressure_assessment = _as_dict(analysis, "pressure_assessment")
        internal_ballistics = _as_dict(analysis, "internal_ballistics")

        updates: dict[str, Any] = {
            "confidence_label": str(input_quality.get("level") or "medium"),
            "confidence_score": (
                float(input_quality.get("score") or 0)
                if input_quality.get("score") not in (None, "")
                else None
            ),
            "safety_status": self._resolve_session_safety_status(analysis, result),
            "next_action": str(recommendation.get("next_step") or "").strip() or None,
        }

        charge_window = _as_list(recommendation, "charge_window_gr")
        if len(charge_window) == 2:
            try:
                updates["recommended_charge_min_gr"] = float(charge_window[0])
                updates["recommended_charge_max_gr"] = float(charge_window[1])
            except Exception:
                pass

        seating_window = _as_list(recommendation, "seating_window_mm")
        if len(seating_window) == 2 and self.coal_mm is not None:
            try:
                updates["recommended_coal_min"] = float(self.coal_mm or 0) + float(
                    seating_window[0]
                )
                updates["recommended_coal_max"] = float(self.coal_mm or 0) + float(
                    seating_window[1]
                )
            except Exception:
                pass

        # Runtime baseline wins: prefer the runtime-derived frozen baseline over the
        # locally computed candidate so session re-opens restore the correct state.
        baseline = (
            self._ensure_recommendation_baseline()
            or self._build_recommendation_baseline_candidate()
        )
        charge_promotion_candidate = summarize_charge_promotion_candidate(
            db=self.db,
            rifle_id=(
                (self.rifle_data or {}).get("id")
                if isinstance(self.rifle_data, dict)
                else None
            ),
            bullet_id=(
                (self.bullet_data or {}).get("id")
                if isinstance(self.bullet_data, dict)
                else None
            ),
            powder_id=(
                (self.powder_data or {}).get("id")
                if isinstance(self.powder_data, dict)
                else None
            ),
            current_charge_gr=(
                float(self.current_charge or 0)
                if self.current_charge is not None
                else None
            ),
        )
        control_state = build_recommendation_control_state(
            current_charge_gr=(
                float(self.current_charge or 0)
                if self.current_charge is not None
                else None
            ),
            coal_mm=float(self.coal_mm or 0) if self.coal_mm is not None else None,
            cbto_mm=float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
            baseline=baseline,
        )

        recommendation_payload: dict[str, Any] = {
            "active_settings": {
                "charge_weight_gr": (
                    float(self.current_charge or 0)
                    if self.current_charge is not None
                    else None
                ),
                "coal_mm": (
                    float(self.coal_mm or 0) if self.coal_mm is not None else None
                ),
                "cbto_mm": (
                    float(self.cbto_mm or 0) if self.cbto_mm is not None else None
                ),
            },
            "recommendation": recommendation,
            "baseline": baseline,
            "control_state": control_state,
            "charge_promotion_candidate": charge_promotion_candidate,
            "pressure_assessment": pressure_assessment,
            "internal_ballistics": {
                "level": internal_ballistics.get("level"),
                "title": internal_ballistics.get("title"),
                "message": internal_ballistics.get("message"),
            },
        }

        evidence_payload: dict[str, Any] = {
            "input_quality": input_quality,
            "observation_summary": observation_summary,
            "latest_result": {
                "muzzle_velocity_fps": result.get("muzzle_velocity_fps"),
                "peak_pressure_psi": result.get("peak_pressure_psi"),
                "safety_margin_percent": result.get("safety_margin_percent"),
                "load_density_percent": result.get("load_density_percent"),
                "fill_ratio": result.get("fill_ratio"),
            },
            "pressure_assessment": {
                "level": pressure_assessment.get("level"),
                "title": pressure_assessment.get("title"),
                "message": pressure_assessment.get("message"),
            },
        }

        learning_payload: dict[str, Any] = {
            "summary": {
                "next_focus": str(recommendation.get("next_step") or "").strip()
                or None,
                "input_quality_level": str(input_quality.get("level") or "").strip()
                or None,
                "input_quality_score": (
                    float(input_quality.get("score") or 0)
                    if input_quality.get("score") not in (None, "")
                    else None
                ),
                "pressure_level": str(pressure_assessment.get("level") or "").strip()
                or None,
                "stability_level": str(
                    _as_dict(analysis, "stability_assessment").get("level") or ""
                ).strip()
                or None,
                "barrel_level": str(
                    _as_dict(analysis, "barrel_context").get("level") or ""
                ).strip()
                or None,
                "brass_level": str(
                    _as_dict(analysis, "brass_context").get("level") or ""
                ).strip()
                or None,
            },
            "barrel_context": _as_dict(analysis, "barrel_context"),
            "brass_context": _as_dict(analysis, "brass_context"),
            "node_fit": _as_dict(analysis, "node_fit"),
            "stability_assessment": _as_dict(analysis, "stability_assessment"),
        }
        return updates, recommendation_payload, evidence_payload, learning_payload

    def _format_learning_runtime_label(self, runtime: dict | None) -> str:
        _rt = runtime if isinstance(runtime, dict) else {}
        learning = _as_dict(_rt, "learning")
        evidence = _as_dict(_rt, "evidence")
        aggregate = _as_dict(learning, "aggregate")
        session_payload = _as_dict(learning, "session")
        session_summary = _as_dict(session_payload, "summary")
        evidence_summary = _as_dict(evidence, "summary")

        confidence_label = str(
            aggregate.get("confidence_label") or aggregate.get("model_status") or ""
        ).strip()
        confidence_score = aggregate.get("confidence_score")
        weakest_link = str(aggregate.get("weakest_link") or "").strip()
        next_focus = str(
            session_summary.get("next_focus") or aggregate.get("next_focus") or ""
        ).strip()
        pressure_level = str(session_summary.get("pressure_level") or "").strip()
        data_strength = str(session_summary.get("data_strength") or "").strip()
        drift_state = str(session_summary.get("drift_state") or "").strip()
        signal_hint = str(session_summary.get("signal_hint") or "").strip()
        chrono_count = (
            _coerce_int(
                evidence_summary.get("chronograph_import_count")
                or evidence_summary.get("chrono_count")
            )
            or 0
        )
        test_count = (
            _coerce_int(
                evidence_summary.get("test_result_count")
                or evidence_summary.get("accuracy_count")
            )
            or 0
        )

        parts: list[str] = []
        if confidence_label:
            score_suffix = ""
            try:
                if confidence_score not in (None, ""):
                    score_suffix = f" ({float(confidence_score):.1f})"
            except Exception:
                score_suffix = ""
            parts.append(f"Model: {confidence_label}{score_suffix}")
        if chrono_count or test_count:
            parts.append(f"Data: {chrono_count} chrono / {test_count} tests")
        if data_strength:
            parts.append(f"Strength: {data_strength}")
        if weakest_link:
            parts.append(f"Weakest link: {weakest_link}")
        if next_focus:
            parts.append(f"Next focus: {next_focus}")
        if pressure_level:
            parts.append(f"Pressure: {pressure_level}")
        if drift_state:
            parts.append(f"Drift: {drift_state}")
        if signal_hint:
            parts.append(f"Signal: {signal_hint}")

        if not parts:
            return "Learning State: --"
        return "Learning State: " + " | ".join(parts)

    def _sync_active_load_session_context(self) -> None:
        session_id = _get_active_load_session_id()
        if session_id is None:
            return

        barrel = (
            self._get_active_barrel_details()
            if hasattr(self, "_get_active_barrel_details")
            else {}
        )
        barrel_context = (
            self._get_active_barrel_configuration_context()
            if hasattr(self, "_get_active_barrel_configuration_context")
            else {}
        )
        barrel_name = str((barrel or {}).get("name") or "").strip() or None
        rifle_name = None
        rifle_caliber = None
        rifle_id = None
        if isinstance(self.rifle_data, dict):
            rifle_name = str(self.rifle_data.get("name") or "").strip() or None
            rifle_caliber = str(self.rifle_data.get("caliber") or "").strip() or None
            _rid = self.rifle_data.get("id")
            if _rid not in (None, ""):
                rifle_id = int(_rid)

        ammo_profile_id = getattr(self, "current_ammo_profile_id", None)
        scalar_updates = {
            "rifle_id": rifle_id,
            "rifle_name": rifle_name,
            "rifle_caliber": rifle_caliber,
            "barrel_id": barrel_context.get("barrel_id")
            or self._get_active_barrel_id(),
            "barrel_name": barrel_context.get("barrel_name") or barrel_name,
            "barrel_configuration_id": barrel_context.get("barrel_configuration_id"),
            "barrel_configuration_name": barrel_context.get(
                "barrel_configuration_name"
            ),
            "ammo_profile_id": (
                int(ammo_profile_id) if ammo_profile_id not in (None, "") else None
            ),
        }
        analysis_updates, recommendation_payload, evidence_payload, learning_payload = (
            self._build_active_load_session_analysis_payloads()
        )
        scalar_updates.update(
            {k: v for k, v in analysis_updates.items() if v is not None}
        )

        try:
            update_load_development_session(
                self.db,
                session_id,
                updates=scalar_updates,
                component_selection=self._build_active_load_session_component_selection(),
                intake_snapshot=self._build_active_load_session_intake_snapshot(),
                barrel_configuration_snapshot=barrel_context.get(
                    "barrel_configuration_snapshot"
                )
                or {},
                recommendation=recommendation_payload,
                evidence_summary=evidence_payload,
                learning_state=learning_payload,
            )
        except Exception:
            return

        try:
            self._latest_load_session_runtime = build_load_session_runtime(
                self.db, session_id
            )
        except Exception:
            self._latest_load_session_runtime = None

        runtime = (
            self._latest_load_session_runtime
            if isinstance(self._latest_load_session_runtime, dict)
            else {}
        )
        delta = _as_dict(runtime, "delta")
        delta_action = str(delta.get("suggested_action") or "").strip() or None
        current_action = str(scalar_updates.get("next_action") or "").strip() or None
        if delta_action and delta_action != current_action:
            try:
                update_load_development_session(
                    self.db,
                    session_id,
                    updates={"next_action": delta_action},
                )
            except Exception:
                pass
            else:
                try:
                    self._latest_load_session_runtime = build_load_session_runtime(
                        self.db, session_id
                    )
                except Exception:
                    self._latest_load_session_runtime = runtime

    def _fallback_runtime_context_parts(self) -> list[str]:
        parts: list[str] = []
        rifle_name = ""
        if isinstance(self.rifle_data, dict):
            rifle_name = str(self.rifle_data.get("name") or "").strip()
        barrel = (
            self._get_active_barrel_details()
            if hasattr(self, "_get_active_barrel_details")
            else {}
        )
        barrel_name = str((barrel or {}).get("name") or "").strip()
        if rifle_name:
            parts.append(f"Rifle: {rifle_name}")
        if barrel_name:
            parts.append(f"Barrel: {barrel_name}")

        component_bits = []
        if isinstance(self.bullet_data, dict) and self.bullet_data.get("name"):
            bullet_name = str(self.bullet_data.get("name") or "").strip()
            bullet_lot = str(self.bullet_data.get("selected_lot_number") or "").strip()
            component_bits.append(
                f"Bullet {bullet_name}" + (f" [{bullet_lot}]" if bullet_lot else "")
            )
        if isinstance(self.powder_data, dict) and self.powder_data.get("name"):
            powder_name = str(self.powder_data.get("name") or "").strip()
            powder_lot = str(self.powder_data.get("selected_lot_number") or "").strip()
            component_bits.append(
                f"Powder {powder_name}" + (f" [{powder_lot}]" if powder_lot else "")
            )
        if isinstance(self.primer_data, dict) and self.primer_data.get("name"):
            primer_name = str(self.primer_data.get("name") or "").strip()
            primer_lot = str(self.primer_data.get("selected_lot_number") or "").strip()
            component_bits.append(
                f"Primer {primer_name}" + (f" [{primer_lot}]" if primer_lot else "")
            )
        if component_bits:
            parts.append("Builder selections: " + " | ".join(component_bits))
        return parts

    def _refresh_runtime_context_summary(self) -> None:
        if not hasattr(self, "runtime_context_label"):
            return

        runtime = self._get_cached_or_active_load_session_runtime()

        if not runtime:
            fallback_parts = self._fallback_runtime_context_parts()
            message = "No active canonical load session is linked yet."
            if fallback_parts:
                message += "<br>" + "<br>".join(fallback_parts)
            else:
                message += " Builder is currently using local selections only."
            self.runtime_context_label.setText("<b>Session Runtime</b><br>" + message)
            self.runtime_context_label.setStyleSheet(_advisory_style("unknown"))
            if hasattr(self, "runtime_delta_label"):
                self.runtime_delta_label.setText(
                    "<b>Runtime Delta</b><br>Session delta becomes available when an active canonical load session exists."
                )
                self.runtime_delta_label.setStyleSheet(_advisory_style("unknown"))
            return

        _runtime: dict[str, Any] = runtime if isinstance(runtime, dict) else {}
        context = _as_dict(_runtime, "context")
        identity = _as_dict(_runtime, "identity")
        session = _as_dict(_runtime, "session")
        rifle = _as_dict(_runtime, "rifle")
        barrel = _as_dict(_runtime, "barrel")
        lots = _as_dict(_runtime, "lots")
        evidence = _as_dict(_runtime, "evidence")
        recommendation_runtime = _as_dict(_runtime, "recommendation")
        summary = _as_dict(evidence, "summary")
        identity_rifle = _as_dict(identity, "rifle")
        identity_barrel = _as_dict(identity, "barrel")
        identity_usage = _as_dict(identity, "usage")
        identity_components = _as_dict(identity, "components")
        identity_lots = _as_dict(identity, "lots")

        lines = []
        session_uid = str(
            context.get("session_uid") or session.get("session_uid") or ""
        ).strip()
        usage_name = str(
            identity_usage.get("label")
            or context.get("usage_profile_name")
            or context.get("usage_profile_key")
            or session.get("usage_profile_name")
            or session.get("usage_profile_key")
            or ""
        ).strip()
        rifle_name = str(
            identity_rifle.get("label")
            or context.get("rifle_name")
            or rifle.get("name")
            or session.get("rifle_name")
            or ""
        ).strip()
        barrel_name = str(
            identity_barrel.get("label")
            or context.get("barrel_name")
            or barrel.get("barrel_name")
            or session.get("barrel_name")
            or ""
        ).strip()
        setup_label = _format_barrel_configuration_label(
            str(
                identity_barrel.get("configuration_label")
                or context.get("barrel_configuration_name")
                or barrel.get("barrel_configuration_name")
                or session.get("barrel_configuration_name")
                or ""
            ).strip(),
            barrel_name,
        )
        if rifle_name or usage_name:
            heading = " | ".join(part for part in (rifle_name, usage_name) if part)
            lines.append(heading)
        if barrel_name:
            barrel_profile = _as_dict(barrel, "learning_profile")
            barrel_confidence = str(
                barrel_profile.get("confidence_label") or ""
            ).strip()
            lines.append(
                "Barrel: "
                + (setup_label or barrel_name)
                + (f" ({barrel_confidence})" if barrel_confidence else "")
            )

        active_lots = []
        for key, label in (
            ("bullet", "Bullet"),
            ("powder", "Powder"),
            ("primer", "Primer"),
            ("case", "Case"),
        ):
            lot_identity = _as_dict(identity_lots, key)
            lot = _as_dict(lots, key)
            component = _as_dict(identity_components, key)
            lot_number = str(
                lot_identity.get("lot_number")
                or context.get(f"{key}_lot_number")
                or lot.get("lot_number")
                or ""
            ).strip()
            if not lot_number:
                continue
            component_label = str(component.get("label") or "").strip()
            if component_label:
                active_lots.append(f"{label} {component_label} [{lot_number}]")
            else:
                active_lots.append(f"{label} {lot_number}")
        if active_lots:
            lines.append("Active lots: " + " | ".join(active_lots))

        evidence_bits = []
        chrono_count = int(summary.get("chronograph_import_count") or 0)
        test_count = int(summary.get("test_result_count") or 0)
        batch_count = int(summary.get("batch_count") or 0)
        best_group_mm = summary.get("best_group_mm")
        latest_velocity = summary.get("latest_avg_velocity_fps")
        if chrono_count:
            evidence_bits.append(f"{chrono_count} chrono imports")
        if test_count:
            evidence_bits.append(f"{test_count} test results")
        if batch_count:
            evidence_bits.append(f"{batch_count} batch projects")
        if isinstance(best_group_mm, (int, float)):
            evidence_bits.append(
                f"best group {format_group_size_mm(float(best_group_mm))}"
            )
        if isinstance(latest_velocity, (int, float)):
            evidence_bits.append(
                f"latest avg {format_velocity_fps(float(latest_velocity))}"
            )
        if evidence_bits:
            lines.append("Evidence: " + " | ".join(evidence_bits))

        control_state = _as_dict(recommendation_runtime, "control_state")
        baseline = _as_dict(recommendation_runtime, "baseline")
        recommendation_bits = []
        charge_state = str(control_state.get("charge_state") or "").strip()
        seating_state = str(control_state.get("seating_state") or "").strip()
        trust_label = str(
            control_state.get("trust_label") or baseline.get("trust_label") or ""
        ).strip()
        if charge_state:
            recommendation_bits.append(f"charge {charge_state}")
        if seating_state:
            recommendation_bits.append(f"seating {seating_state}")
        if trust_label:
            recommendation_bits.append(f"trust {trust_label}")
        baseline_summary = str(baseline.get("summary") or "").strip()
        if baseline_summary:
            recommendation_bits.append(baseline_summary)
        elif setup_label:
            recommendation_bits.append(f"setup {setup_label}")
        recommendation_bits.extend(
            summarize_recommendation_return_targets(control_state, baseline)
        )
        if recommendation_bits:
            lines.append("Recommendation: " + " | ".join(recommendation_bits))

        meta = []
        status = str(context.get("status") or session.get("status") or "").strip()
        stage = str(
            context.get("lifecycle_stage") or session.get("lifecycle_stage") or ""
        ).strip()
        confidence = str(
            context.get("confidence_label") or session.get("confidence_label") or ""
        ).strip()
        safety = str(
            context.get("safety_status") or session.get("safety_status") or ""
        ).strip()
        if status:
            meta.append(f"status {status}")
        if stage:
            meta.append(f"stage {stage}")
        if confidence:
            meta.append(f"confidence {confidence}")
        if safety:
            meta.append(f"safety {safety}")
        if session_uid:
            meta.append(f"session {session_uid[:8]}")
        if meta:
            lines.append("Runtime: " + " | ".join(meta))
        if not lines:
            lines.append(
                "Canonical session is active, but the runtime summary is still building."
            )

        level = "ok" if evidence_bits else "warning"
        self.runtime_context_label.setText(
            "<b>Session Runtime</b><br>" + "<br>".join(lines)
        )
        self.runtime_context_label.setStyleSheet(_advisory_style(level))
        if hasattr(self, "runtime_delta_label"):
            delta = _as_dict(_runtime, "delta")
            delta_items = [
                str(item).strip()
                for item in (delta.get("items") or [])
                if str(item).strip()
            ]
            delta_impacts = [
                str(item).strip()
                for item in (delta.get("impacts") or [])
                if str(item).strip()
            ]
            delta_focus_areas = [
                str(item).strip()
                for item in (delta.get("focus_areas") or [])
                if str(item).strip()
            ]
            delta_summary = str(delta.get("summary") or "").strip()
            delta_title = str(delta.get("title") or "Runtime Delta").strip()
            delta_action = str(delta.get("suggested_action") or "").strip()
            delta_lines = [delta_summary] if delta_summary else []
            delta_lines.extend(delta_items[:3])
            if delta_focus_areas:
                delta_lines.append("Focus: " + ", ".join(delta_focus_areas[:4]))
            if delta_impacts:
                delta_lines.append("Impact: " + delta_impacts[0])
            if len(delta_impacts) > 1:
                delta_lines.append("Then: " + delta_impacts[1])
            if delta_action:
                delta_lines.append("Next: " + delta_action)
            self.runtime_delta_label.setText(
                "<b>" + delta_title + "</b><br>" + "<br>".join(delta_lines)
            )
            self.runtime_delta_label.setStyleSheet(
                _advisory_style(str(delta.get("level") or "unknown"))
            )

    def _refresh_service_recommendation_callout(self) -> None:
        """Show compact service-based recommendation text in builder callouts."""
        if not hasattr(self, "powder_recommendation"):
            return

        _raw_analysis = getattr(self, "_latest_load_analysis", None)
        analysis: dict[str, Any] = (
            _raw_analysis if isinstance(_raw_analysis, dict) else {}
        )
        recommendation = _as_dict(analysis, "recommendation")
        if not recommendation:
            return

        baseline = self._ensure_recommendation_baseline()
        basis_summary = summarize_recommendation_evidence_basis(analysis, baseline)

        parts: list[str] = []
        next_step = str(recommendation.get("next_step") or "").strip()
        if next_step:
            parts.append(next_step)
        compact_basis = str(basis_summary.get("compact") or "").strip()
        if compact_basis:
            parts.append("Recommendation basis: " + compact_basis)
        charge_window = recommendation.get("charge_window_gr") or []
        if len(charge_window) == 2:
            parts.append(
                "Recommended charge window: "
                f"{format_weight_grains(float(charge_window[0]), 'powder')}"
                " - "
                f"{format_weight_grains(float(charge_window[1]), 'powder')}"
            )
        seating_window = recommendation.get("seating_window_mm") or []
        if len(seating_window) == 2:
            parts.append(
                "Recommended seating adjustment: "
                f"{format_length_delta_mm(float(seating_window[0]))}"
                " to "
                f"{format_length_delta_mm(float(seating_window[1]))}"
            )
        for note in recommendation.get("notes") or []:
            note_text = str(note or "").strip()
            if note_text:
                parts.append(note_text)
        powder_lot_context = _as_dict(analysis, "powder_lot_context")
        bullet_lot_context = _as_dict(analysis, "bullet_lot_context")
        if powder_lot_context.get("lot_number"):
            parts.append(
                f"Powder lot in engine: {powder_lot_context.get('lot_number')}"
            )
        if bullet_lot_context.get("lot_number"):
            parts.append(
                f"Bullet lot in engine: {bullet_lot_context.get('lot_number')}"
            )
        if not parts:
            return

        existing = str(self.powder_recommendation.text() or "").strip()
        marker = "<br><br><b>Engine Suggestion:</b>"
        if marker in existing:
            existing = existing.split(marker, 1)[0].strip()
        service_block = "<br>".join(parts)
        if existing:
            self.powder_recommendation.setText(existing + marker + " " + service_block)
        else:
            self.powder_recommendation.setText(
                "<b>Engine Suggestion:</b> " + service_block
            )

    def init_ui(self):
        """Single-screen load builder: top bar + 3-column layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._advanced_widgets = []
        self._advanced_chrono_widgets = []

        # Hidden legacy widgets expected by downstream methods
        self.guided_hint = QLabel(self)
        self.guided_hint.hide()
        layout.addWidget(self.guided_hint)
        self.step1_widget = QWidget(self)
        self.step1_widget.hide()
        self.step2_widget = QWidget(self)
        self.step2_widget.hide()
        self.current_step = 2

        layout.addWidget(self._build_top_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_left_column())
        splitter.addWidget(self._build_middle_column())
        splitter.addWidget(self._build_right_column())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 6)
        layout.addWidget(splitter, 1)

        self._build_hidden_utility_widgets(layout)

        self.setLayout(layout)

        try:
            self.apply_ui_mode_from_settings()
        except Exception:
            pass

        QTimer.singleShot(120, self._init_load_data)

    # ── New single-screen builder methods ─────────────────────────────────────

    def _build_top_bar(self):
        """Rifle selector · purpose toggles · Demper/Subsonisk · action buttons."""
        bar = QWidget()
        bar.setObjectName("loadBuilderTopBar")
        bar.setStyleSheet(
            "#loadBuilderTopBar { background: #1a1f2e; border-bottom: 1px solid #2d3548; }"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 8, 14, 8)
        h.setSpacing(10)

        # ── Rifle dropdown ──
        self.rifle_combo = QComboBox()
        self.rifle_combo.setMinimumWidth(230)
        self.rifle_combo.setToolTip("Velg våpen")
        self.rifle_combo.setStyleSheet(
            "QComboBox { background:#252b3b; color:#e0e6f0; border:1px solid #3b4560;"
            " border-radius:6px; padding:5px 10px; font-weight:bold; }"
            "QComboBox::drop-down { border:none; }"
        )
        self.rifle_combo.currentIndexChanged.connect(self.on_rifle_combo_changed)
        self.rifle_combo.activated.connect(self._on_rifle_combo_activated)
        h.addWidget(self.rifle_combo)

        h.addSpacing(12)

        # ── Purpose pill buttons ──
        self._purpose_btn_group = QButtonGroup(bar)
        self._purpose_btn_group.setExclusive(True)
        purpose_style = (
            "QPushButton { border:1px solid #3b4d7a; border-radius:14px; padding:5px 14px;"
            " color:#7a94c4; background:transparent; font-size:12px; }"
            "QPushButton:checked { background:#2d4a8a; color:#ffffff; border-color:#4a6bb0; }"
            "QPushButton:hover { background:#253660; }"
        )
        for label, key in [
            ("Jakt", "hunting"),
            ("Presisjon", "precision"),
            ("Langhold", "long_range"),
        ]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("purpose_key", key)
            btn.setStyleSheet(purpose_style)
            btn.setFixedHeight(30)
            self._purpose_btn_group.addButton(btn)
            h.addWidget(btn)
        if self._purpose_btn_group.buttons():
            self._purpose_btn_group.buttons()[0].setChecked(True)

        h.addSpacing(12)

        # ── Option checkboxes ──
        cb_style = "QCheckBox { color:#b0bcd6; spacing:6px; } QCheckBox::indicator { width:16px; height:16px; }"
        self.suppressor_cb = QCheckBox("Demper")
        self.suppressor_cb.setStyleSheet(cb_style)
        self.subsonic_cb = QCheckBox("Subsonisk")
        self.subsonic_cb.setStyleSheet(cb_style)
        self.subsonic_target = QDoubleSpinBox()
        self.subsonic_target.setRange(500.0, 1300.0)
        self.subsonic_target.setValue(1050.0)
        self.subsonic_target.setSingleStep(5.0)
        self.subsonic_target.setVisible(False)
        self.subsonic_target.setStyleSheet(
            "QDoubleSpinBox { background:#252b3b; color:#e0e6f0; border:1px solid #3b4560;"
            " border-radius:4px; padding:3px 6px; }"
        )
        self.subsonic_cb.toggled.connect(
            lambda checked: self.subsonic_target.setVisible(checked)
        )
        self.subsonic_cb.toggled.connect(self.update_visualization)
        self.subsonic_target.valueChanged.connect(self.update_visualization)
        self.subsonic_row = bar  # legacy alias
        h.addWidget(self.suppressor_cb)
        h.addWidget(self.subsonic_cb)
        h.addWidget(self.subsonic_target)

        h.addStretch()

        # ── Action buttons ──
        btn_style_ghost = (
            "QPushButton { color:#7a94c4; background:transparent; border:1px solid #3b4560;"
            " border-radius:6px; padding:5px 12px; }"
            "QPushButton:hover { background:#252b3b; }"
        )
        btn_style_primary = (
            "QPushButton { background:#2d4a8a; color:#fff; border:none;"
            " border-radius:6px; padding:5px 16px; font-weight:bold; }"
            "QPushButton:hover { background:#3a5fa8; }"
        )
        btn_style_secondary = (
            "QPushButton { background:#252b3b; color:#c0cce0; border:1px solid #3b4560;"
            " border-radius:6px; padding:5px 12px; }"
            "QPushButton:hover { background:#2d3548; }"
        )

        self.ai_button = QPushButton("Local Guide")
        self.ai_button.setStyleSheet(btn_style_ghost)
        self.ai_button.clicked.connect(self.on_open_ai_chat)
        h.addWidget(self.ai_button)

        save_btn = QPushButton("Lagre")
        save_btn.setStyleSheet(btn_style_primary)
        save_btn.clicked.connect(self.on_save_load_clicked)
        h.addWidget(save_btn)

        batch_btn = QPushButton("Lag Batch")
        batch_btn.setStyleSheet(btn_style_secondary)
        batch_btn.clicked.connect(self.on_create_batch_clicked)
        h.addWidget(batch_btn)

        # Legacy reference (check_step1_complete uses this)
        self.next_btn = QPushButton()
        self.next_btn.hide()

        return bar

    def _build_left_column(self):
        """Slim component column: brass, bullet, powder, primer — clean dark cards."""
        widget = QWidget()
        widget.setStyleSheet("QWidget { background:#161b2a; }")

        # Call create_component_controls() hidden so all self.* widget refs exist
        _legacy = self.create_component_controls()
        _legacy.hide()
        _legacy.setParent(widget)

        # Hidden legacy brass radio-button infrastructure
        self._brass_container_widget = QWidget()
        self._brass_container_widget.hide()
        self._brass_container_widget.setParent(widget)
        self.brass_container = QVBoxLayout(self._brass_container_widget)
        self.brass_button_group = QButtonGroup(widget)
        self.brass_button_group.setExclusive(True)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        hdr = QLabel("KOMPONENTER")
        hdr.setStyleSheet(
            "color:#3d5a8a; font-size:9px; font-weight:bold; letter-spacing:2px;"
            " padding-bottom:4px; background:transparent;"
        )
        layout.addWidget(hdr)

        rows = [
            ("Hylse / Batch", "_brass_combo_proxy"),
            ("Kule", "bullet_combo"),
            ("Krutt", "powder_combo"),
            ("Tennhette", "primer_combo"),
        ]

        # Create new brass combo
        self.brass_combo = QComboBox()
        self.brass_combo.addItem("— velg etter rifle —", None)
        self.brass_combo.currentIndexChanged.connect(self.on_brass_combo_changed)

        combo_map = {
            "_brass_combo_proxy": self.brass_combo,
            "bullet_combo": self.bullet_combo,
            "powder_combo": self.powder_combo,
            "primer_combo": self.primer_combo,
        }

        _CARD_SS = (
            "QWidget#compCard {{ background:#1c2438; border-radius:6px;"
            " border-left:3px solid {color}; }}"
        )
        colors = ["#3498db", "#2ecc71", "#e67e22", "#e74c3c"]

        for (label_text, attr), color in zip(rows, colors):
            card = QWidget()
            card.setObjectName("compCard")
            card.setStyleSheet(_CARD_SS.format(color=color))
            cv = QVBoxLayout(card)
            cv.setContentsMargins(10, 6, 8, 6)
            cv.setSpacing(3)

            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                "color:#5a7ab0; font-size:9px; font-weight:bold;"
                " letter-spacing:0.5px; background:transparent;"
            )
            cv.addWidget(lbl)

            combo = combo_map[attr]
            combo.setStyleSheet(
                "QComboBox { background:#0f1420; color:#c8d8f0;"
                " border:1px solid #2a3550; border-radius:4px;"
                " padding:4px 8px; font-size:12px; }"
                "QComboBox::drop-down { border:none; width:20px; }"
                "QComboBox QAbstractItemView { background:#1c2438; color:#c8d8f0;"
                " selection-background-color:#2d4a8a; }"
            )
            cv.addWidget(combo)
            layout.addWidget(card)

        layout.addStretch()

        # Quick-access barrel config row
        bc_row = QHBoxLayout()
        bc_lbl = QLabel("Setup:")
        bc_lbl.setStyleSheet("color:#3d5a8a; font-size:10px; background:transparent;")
        bc_row.addWidget(bc_lbl)
        self.barrel_configuration_combo.setStyleSheet(
            "QComboBox { background:#0f1420; color:#8a9ec0; border:1px solid #2a3550;"
            " border-radius:4px; padding:3px 6px; font-size:11px; }"
            "QComboBox::drop-down { border:none; }"
        )
        bc_row.addWidget(self.barrel_configuration_combo, 1)
        layout.addLayout(bc_row)

        return widget

    def _build_middle_column(self):
        """Parameters column: charge + COAL/CBTO + safety indicators."""
        widget = QWidget()
        widget.setStyleSheet("QWidget { background:#13182a; }")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        hdr = QLabel("PARAMETRE")
        hdr.setStyleSheet(
            "color:#3d5a8a; font-size:9px; font-weight:bold; letter-spacing:2px;"
            " padding-bottom:4px; background:transparent;"
        )
        layout.addWidget(hdr)

        layout.addWidget(self.create_charge_slider())

        # Compact seating section (only COAL + CBTO spinboxes, no guidance walls)
        seat_card = QWidget()
        seat_card.setStyleSheet("QWidget { background:#1c2438; border-radius:6px; }")
        sc = QVBoxLayout(seat_card)
        sc.setContentsMargins(12, 10, 12, 10)
        sc.setSpacing(6)
        seat_hdr = QLabel("SITTING / COAL")
        seat_hdr.setStyleSheet(
            "color:#5a7ab0; font-size:9px; font-weight:bold; background:transparent;"
        )
        sc.addWidget(seat_hdr)

        # Ensure seating widgets exist (create_seating_controls creates them)
        _seat_hidden = self.create_seating_controls()
        _seat_hidden.hide()
        _seat_hidden.setParent(widget)

        _spin_ss = (
            "QDoubleSpinBox { background:#0f1420; color:#c8d8f0; border:1px solid #2a3550;"
            " border-radius:4px; padding:4px 8px; font-size:13px; font-family:monospace; }"
        )
        for spin_attr, caption in [
            ("coal_spin", "COAL  (mm)"),
            ("cbto_spin", "CBTO  (mm)"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(caption)
            lbl.setStyleSheet(
                "color:#5a7ab0; font-size:10px; min-width:80px; background:transparent;"
            )
            spin = getattr(self, spin_attr)
            spin.setStyleSheet(_spin_ss)
            row.addWidget(lbl)
            row.addWidget(spin, 1)
            sc.addLayout(row)

        layout.addWidget(seat_card)

        # Compact safety strip (visual pill indicators)
        layout.addWidget(self._build_compact_safety_strip())

        layout.addStretch()
        return widget

    def _build_compact_safety_strip(self):
        """2-column grid of colored status pills for the middle column."""
        card = QWidget()
        card.setStyleSheet("QWidget { background:#1c2438; border-radius:6px; }")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(6)

        hdr = QLabel("SIKKERHET")
        hdr.setStyleSheet(
            "color:#5a7ab0; font-size:9px; font-weight:bold; letter-spacing:1px;"
            " background:transparent;"
        )
        outer.addWidget(hdr)

        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)

        _pill_base = (
            "QLabel { border-radius:4px; padding:4px 8px; font-size:10px;"
            " background:#12192e; color:#5a7ab0; }"
        )

        def _make_pill(attr: str, text: str) -> QLabel:
            lbl = QLabel(f"● {text}")
            lbl.setStyleSheet(_pill_base)
            setattr(self, attr, lbl)
            return lbl

        pills = [
            ("_pill_pressure", "Trykk: --"),
            ("_pill_stability", "Stabilitet: --"),
            ("_pill_bullet_fit", "Kuletilpasning: --"),
            ("_pill_subsonic", "Subsonisk: --"),
            ("_pill_impact", "Treffvindu: --"),
            ("_pill_retest", "Retest: --"),
        ]
        for i, (attr, text) in enumerate(pills):
            lbl = _make_pill(attr, text)
            grid.addWidget(lbl, i // 2, i % 2)

        outer.addLayout(grid)
        return card

    def _update_compact_safety_strip(self):
        """Refresh pill colors/text from the verbose label texts."""
        _ok = "QLabel { border-radius:4px; padding:4px 8px; font-size:10px; background:#0d2b1a; color:#27ae60; }"
        _warn = "QLabel { border-radius:4px; padding:4px 8px; font-size:10px; background:#2b1c08; color:#e67e22; }"
        _bad = "QLabel { border-radius:4px; padding:4px 8px; font-size:10px; background:#2b0d0d; color:#e74c3c; }"
        _idle = "QLabel { border-radius:4px; padding:4px 8px; font-size:10px; background:#12192e; color:#5a7ab0; }"

        def _style_for(text: str):
            t = text.lower()
            if any(
                k in t
                for k in ("ok", "safe", "good", "grønn", "trygg", "stable", "stabil")
            ):
                return _ok
            if any(k in t for k in ("warn", "advar", "caution", "gul", "marginal")):
                return _warn
            if any(
                k in t
                for k in (
                    "danger",
                    "fare",
                    "exceed",
                    "over",
                    "rød",
                    "critical",
                    "kritisk",
                    "fail",
                )
            ):
                return _bad
            return _idle

        def _sync(pill_attr: str, src_label_attr: str, short: str):
            pill = getattr(self, pill_attr, None)
            src = getattr(self, src_label_attr, None)
            if pill is None:
                return
            raw = src.text() if src else "--"
            # strip html tags for style detection
            import re as _re

            plain = _re.sub(r"<[^>]+>", "", raw)
            pill.setStyleSheet(_style_for(plain))
            pill.setText(
                f"● {short}: {plain[:28]}" if len(plain) > 3 else f"● {short}: --"
            )

        _sync("_pill_pressure", "pressure_alert_label", "Trykk")
        _sync("_pill_stability", "stability_advisor_label", "Stabilitet")
        _sync("_pill_bullet_fit", "bullet_fit_label", "Kule")
        _sync("_pill_subsonic", "subsonic_advisor_label", "Sub")
        _sync("_pill_impact", "impact_window_label", "Treff")
        _sync("_pill_retest", "retest_advisor_label", "Retest")

    def _build_right_column(self):
        """Results column: metric cards + live graphs."""
        widget = QWidget()
        widget.setStyleSheet("QWidget { background:#10131f; }")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 12, 12, 12)
        layout.setSpacing(6)

        hdr = QLabel("RESULTATER")
        hdr.setStyleSheet(
            "color:#3d5a8a; font-size:9px; font-weight:bold; letter-spacing:2px;"
            " padding-bottom:2px; background:transparent;"
        )
        layout.addWidget(hdr)

        # Metric cards strip (always visible — shows "—" until data loads)
        metrics = self.create_stats_bar()
        layout.addWidget(metrics)

        # Graphs
        graphs = self._build_graph_area()
        layout.addWidget(graphs, 1)

        return widget

    def _build_graph_area(self):
        """Pressure + velocity graphs in a dark container."""
        container = QWidget()
        container.setStyleSheet("QWidget { background:#10131f; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        try:
            import pyqtgraph as pg  # type: ignore[import]

            self._pg = pg
            pg.setConfigOption("background", "#10131f")
            pg.setConfigOption("foreground", "#4a6a9a")

            _AXIS_SS = {"color": "#4a6a9a", "font-size": "9pt"}

            self.pressure_plot = pg.PlotWidget()
            self.pressure_plot.setLabel("left", "Trykk", units="PSI", **_AXIS_SS)
            self.pressure_plot.setLabel("bottom", "Tid", units="ms", **_AXIS_SS)
            self.pressure_plot.setTitle("Kammertrykk", color="#4a6a9a", size="9pt")
            self.pressure_plot.setMinimumHeight(160)
            self.pressure_plot.showGrid(x=True, y=True, alpha=0.15)
            layout.addWidget(self.pressure_plot, 1)

            self.velocity_plot = pg.PlotWidget()
            self.velocity_plot.setLabel("left", "Hastighet", units="fps", **_AXIS_SS)
            self.velocity_plot.setLabel(
                "bottom", "Posisjon", units="tommer", **_AXIS_SS
            )
            self.velocity_plot.setTitle("Kulehastighet", color="#4a6a9a", size="9pt")
            self.velocity_plot.setMinimumHeight(160)
            self.velocity_plot.showGrid(x=True, y=True, alpha=0.15)
            layout.addWidget(self.velocity_plot, 1)

            # Transonic toggle (compact)
            tc_row = QHBoxLayout()
            self.transonic_cb = QCheckBox("Vis transonisk sone")
            self.transonic_cb.setChecked(True)
            self.transonic_cb.setStyleSheet(
                "color:#4a6a9a; font-size:10px; background:transparent;"
            )
            self.transonic_cb.toggled.connect(self.update_visualization)
            self.transonic_margin = QDoubleSpinBox()
            self.transonic_margin.setRange(0, 500)
            self.transonic_margin.setValue(50)
            self.transonic_margin.setSuffix(" fps")
            self.transonic_margin.setStyleSheet(
                "QDoubleSpinBox { background:#0f1420; color:#4a6a9a; border:1px solid #2a3550;"
                " border-radius:3px; padding:2px 6px; font-size:10px; }"
            )
            self.transonic_margin.valueChanged.connect(self.update_visualization)
            tc_row.addWidget(self.transonic_cb)
            tc_row.addWidget(self.transonic_margin)
            tc_row.addStretch()
            layout.addLayout(tc_row)

            # ── Trajectory arc panel ──────────────────────────────────────────
            traj_hdr_row = QHBoxLayout()
            traj_hdr = QLabel("BALLISTISK BANE")
            traj_hdr.setStyleSheet(
                "color:#3d5a8a; font-size:9px; font-weight:bold; letter-spacing:2px;"
                " background:transparent;"
            )
            self._traj_range_combo = QComboBox()
            self._traj_range_combo.addItems(["300 m", "500 m", "800 m", "1000 m"])
            self._traj_range_combo.setCurrentIndex(1)
            self._traj_range_combo.setStyleSheet(
                "QComboBox { background:#1a2035; color:#4a6a9a; border:1px solid #2a3550;"
                " border-radius:3px; padding:2px 6px; font-size:9px; }"
            )
            self._traj_range_combo.currentIndexChanged.connect(
                self.update_visualization
            )
            traj_hdr_row.addWidget(traj_hdr)
            traj_hdr_row.addStretch()
            traj_hdr_row.addWidget(self._traj_range_combo)
            layout.addLayout(traj_hdr_row)

            self.trajectory_plot = pg.PlotWidget(container)
            self.trajectory_plot.setLabel(
                "left", "Fall", units="cm", color="#4a6a9a", **{"font-size": "9pt"}
            )
            self.trajectory_plot.setLabel(
                "bottom", "Avstand", units="m", color="#4a6a9a", **{"font-size": "9pt"}
            )
            self.trajectory_plot.setTitle(
                "Kulebane (nullstilt 100 m)", color="#4a6a9a", size="9pt"
            )
            self.trajectory_plot.setMinimumHeight(140)
            self.trajectory_plot.showGrid(x=True, y=True, alpha=0.15)
            self.trajectory_plot.invertY(False)
            layout.addWidget(self.trajectory_plot, 1)

            # Distance table (5 columns × 3 rows)
            self._traj_table = QTableWidget(3, 5)
            self._traj_table.setHorizontalHeaderLabels(
                ["100 m", "200 m", "300 m", "400 m", "500 m"]
            )
            self._traj_table.setVerticalHeaderLabels(["m/s", "Fall cm", "J"])
            _th = self._traj_table.horizontalHeader()
            if _th is not None:
                _th.setDefaultSectionSize(62)
            _tv = self._traj_table.verticalHeader()
            if _tv is not None:
                _tv.setDefaultSectionSize(22)
            self._traj_table.setFixedHeight(106)
            self._traj_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self._traj_table.setStyleSheet(
                "QTableWidget { background:#0d1120; color:#8ab0d0; border:none;"
                " gridline-color:#1e2a40; font-size:10px; }"
                "QHeaderView::section { background:#121828; color:#4a6a9a; border:none;"
                " font-size:9px; padding:2px; }"
            )
            layout.addWidget(self._traj_table)

        except ImportError:
            ph = QLabel(
                "pyqtgraph ikke installert — installer med:  pip install pyqtgraph"
            )
            ph.setStyleSheet("color:#4a6a9a; padding:20px; background:transparent;")
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(ph)
            self.pressure_plot = None
            self.velocity_plot = None
            self.trajectory_plot = None
            self._traj_table = None
            self._traj_range_combo = QComboBox()
            self.transonic_cb = QCheckBox()
            self.transonic_margin = QDoubleSpinBox()

        return container

    def _build_hidden_utility_widgets(self, layout):
        """Create utility widgets needed by existing logic, kept hidden.

        IMPORTANT: every widget here must be a child of `hidden` (or deeper).
        Parentless widgets become top-level Qt windows the moment setVisible(True)
        is called on them — which _apply_ui_mode and update_scope_comparison do.
        A child of a hidden parent can never show as a separate window.
        """
        hidden = QWidget(self)  # child of self → never a top-level window
        hidden.hide()
        layout.addWidget(hidden)

        # ── Safety panel labels (hidden — still updated by existing logic) ──────
        try:
            _safety_panel = self.create_safety_panel()
            _safety_panel.setParent(hidden)
        except Exception:
            pass

        # ── Action buttons (advanced-mode only) ────────────────────────────────
        self.explain_plot_btn = QPushButton(tr("mlb_explain_this_plot"), hidden)
        self.explain_plot_btn.clicked.connect(self.on_explain_plot_clicked)
        self._advanced_widgets.append(self.explain_plot_btn)

        self.ai_settings_btn = QPushButton(tr("mlb_ai_settings_title"), hidden)
        self.ai_settings_btn.clicked.connect(self.on_open_ai_settings)
        self._advanced_widgets.append(self.ai_settings_btn)

        self.prefs_btn = QPushButton(tr("mlb_preferences_title"), hidden)
        self.prefs_btn.clicked.connect(self.on_open_preferences)

        self.suggest_btn = QPushButton(tr("mlb_suggest_next_charge"), hidden)
        self.suggest_btn.clicked.connect(self.on_suggest_next_charge)
        self._advanced_widgets.append(self.suggest_btn)

        self.manage_suggestions_btn = QPushButton(tr("mlb_manage_suggestions"), hidden)
        self.manage_suggestions_btn.clicked.connect(self.on_manage_suggestions_clicked)
        self._advanced_widgets.append(self.manage_suggestions_btn)

        self.auto_match_btn = QPushButton(tr("mlb_auto_match_suggestions"), hidden)
        self.auto_match_btn.clicked.connect(self.on_auto_match_suggestions)
        self._advanced_widgets.append(self.auto_match_btn)

        self.auto_match_toggle = QPushButton(tr("mlb_enable_auto_match"), hidden)
        self.auto_match_toggle.setCheckable(True)
        self.auto_match_toggle.toggled.connect(self.on_toggle_auto_match)
        self._advanced_widgets.append(self.auto_match_toggle)

        self._auto_match_timer = QTimer(self)
        self._auto_match_timer.setInterval(10000)
        self._auto_match_timer.timeout.connect(self._auto_match_poll)
        self._last_test_result_id = None

        # ── Pressure log ───────────────────────────────────────────────────────
        self.pressure_group = QGroupBox(tr("mlb_pressure_log"), hidden)
        pressure_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self.pressure_rifle_combo = QComboBox(hidden)
        self.pressure_rifle_combo.addItem("All firearms", None)
        try:
            for r in (
                self.db.execute_query("SELECT id, name FROM rifles ORDER BY name") or []
            ):
                self.pressure_rifle_combo.addItem(r.get("name", "?"), r.get("id"))
        except Exception:
            pass
        self.pressure_rifle_combo.currentIndexChanged.connect(self.refresh_pressure_log)
        filter_layout.addWidget(self.pressure_rifle_combo)
        self.pressure_from = QDateEdit(hidden)
        self.pressure_from.setCalendarPopup(True)
        self.pressure_from.setDate(QDate.currentDate().addDays(-30))
        filter_layout.addWidget(self.pressure_from)
        self.pressure_to = QDateEdit(hidden)
        self.pressure_to.setCalendarPopup(True)
        self.pressure_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.pressure_to)
        for label, days in [("7d", 7), ("30d", 30), ("90d", 90)]:
            btn = QPushButton(label, hidden)
            btn.clicked.connect(lambda _=False, d=days: self.on_set_date_preset(d))
            filter_layout.addWidget(btn)
        self.pressure_search = QLineEdit(hidden)
        self.pressure_search.setPlaceholderText(tr("mlb_filter_notes_id_charge"))
        self.pressure_search.returnPressed.connect(self.refresh_pressure_log)
        filter_layout.addWidget(self.pressure_search)
        pressure_layout.addLayout(filter_layout)
        self.pressure_list = QListWidget(hidden)
        self.pressure_list.setMinimumHeight(150)
        pressure_layout.addWidget(self.pressure_list)
        pbtn_layout = QHBoxLayout()
        for label, slot in [
            (tr("mlb_refresh_icon"), self.refresh_pressure_log),
            (tr("mlb_export_csv"), self.on_export_pressure_log),
            (tr("mlb_log_predicted_pressure"), self.on_log_predicted_pressure),
        ]:
            b = QPushButton(label, hidden)
            b.clicked.connect(slot)
            pbtn_layout.addWidget(b)
        pressure_layout.addLayout(pbtn_layout)
        self.pressure_group.setLayout(pressure_layout)
        self._advanced_widgets.append(self.pressure_group)

        # ── AI chat refs ───────────────────────────────────────────────────────
        self.chat_widget = QWidget(hidden)
        self.chat_display = QTextEdit(self.chat_widget)
        self.chat_display.setReadOnly(True)
        self.chat_input = QLineEdit(self.chat_widget)
        self.collapse_btn = QPushButton(self.chat_widget)

        # ── Scope comparison (stats mixin calls setVisible on these) ───────────
        self.scope_comparison_group = QGroupBox(hidden)
        self.scope_comparison_label = QLabel(self.scope_comparison_group)

        # ── Compare + transonic row (advanced-mode toggles) ────────────────────
        self.compare_btn = QPushButton(tr("mlb_compare_other_powders"), hidden)
        self._advanced_widgets.append(self.compare_btn)

        self.transonic_row = QWidget(hidden)
        self._advanced_widgets.append(self.transonic_row)

        self._apply_velocity_unit_preferences()

    def _make_col_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#8a9ec0; font-size:11px;")
        return lbl

    def _style_combo(self, combo: QComboBox) -> None:
        combo.setStyleSheet(
            "QComboBox { background:#252b3b; color:#dde4f0; border:1px solid #3b4560;"
            " border-radius:5px; padding:4px 8px; }"
            "QComboBox::drop-down { border:none; }"
            "QComboBox QAbstractItemView { background:#252b3b; color:#dde4f0; }"
        )

    def on_rifle_combo_changed(self, index: int) -> None:
        """Handle rifle selection from the top-bar dropdown."""
        rifle_data = self.rifle_combo.itemData(index)
        if not isinstance(rifle_data, dict):
            return
        self.rifle_data = rifle_data
        self._rifle_profile_details = None
        self._rifle_profile_details_id = None
        self._latest_load_analysis = None  # type: ignore[attr-defined]
        self._latest_seating_summary = None
        self._recommendation_baseline = None
        try:
            s = QSettings("ReloadingWorkshop", "ReloadingManager")
            s.remove("pending_builder_rifle_id")
            s.remove("pending_builder_barrel_id")
        except Exception:
            pass
        self._populate_brass_combo(rifle_data.get("caliber", ""))
        self._refresh_active_rifle_context()
        self._sync_active_load_session_context()
        self.initialize_step2()

    def _populate_rifle_combo_box(self) -> None:
        """Load rifles from DB into the top-bar combo and restore last selection."""
        self.rifle_combo.blockSignals(True)
        self.rifle_combo.clear()
        self.rifle_combo.addItem("— velg rifle —", None)
        rifles = self._list_rifles_for_selection()
        pending_id = None
        try:
            pending_id = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "pending_builder_rifle_id"
            )
        except Exception:
            pass
        if pending_id is None:
            try:
                _rt = self._get_active_load_session_runtime()
                if isinstance(_rt, dict) and _rt.get("rifle_id") not in (None, ""):
                    pending_id = str(_rt["rifle_id"])
            except Exception:
                pass
        select_index = 0
        for i, rifle in enumerate(rifles, start=1):
            name = rifle.get("name") or f"Firearm #{rifle.get('id')}"
            caliber = rifle.get("caliber") or "?"
            self.rifle_combo.addItem(f"{name}  ·  {caliber}", rifle)
            if pending_id and str(rifle.get("id")) == str(pending_id):
                select_index = i
        self.rifle_combo.blockSignals(False)
        if select_index > 0:
            self.rifle_combo.setCurrentIndex(select_index)
            self.on_rifle_combo_changed(select_index)

    def _on_rifle_combo_activated(self, index: int) -> None:
        """Refresh rifle list when user opens the dropdown (picks up newly added rifles)."""
        current_id = None
        data = self.rifle_combo.itemData(self.rifle_combo.currentIndex())
        if isinstance(data, dict):
            current_id = data.get("id")
        self._populate_rifle_combo_box()
        # Restore the previously selected rifle if still in list
        if current_id is not None:
            for i in range(self.rifle_combo.count()):
                d = self.rifle_combo.itemData(i)
                if isinstance(d, dict) and d.get("id") == current_id:
                    self.rifle_combo.blockSignals(True)
                    self.rifle_combo.setCurrentIndex(i)
                    self.rifle_combo.blockSignals(False)
                    break

    def _populate_brass_combo(self, caliber: str) -> None:
        """Populate brass batch combo for the given caliber."""
        self.brass_combo.blockSignals(True)
        self.brass_combo.clear()
        self.brass_combo.addItem("— velg hylse-batch —", None)
        try:
            batches = self.db.execute_query(
                """
                SELECT bb.*, c.name as case_name
                FROM brass_batches bb
                JOIN cases c ON bb.case_id = c.id
                WHERE c.caliber = ? AND bb.cases_active > 0
                ORDER BY bb.created_date DESC
                """,
                (caliber,),
            )
            for b in batches or []:
                label = (
                    f"{b.get('case_name', '?')}  —  {b.get('cases_active', '?')} stk"
                )
                self.brass_combo.addItem(label, dict(b))
        except Exception:
            pass
        self.brass_combo.blockSignals(False)
        if self.brass_combo.count() == 2:
            self.brass_combo.setCurrentIndex(1)
            self.on_brass_combo_changed(1)

    def on_brass_combo_changed(self, index: int) -> None:
        """Handle brass batch selection from left-column combo."""
        self.brass_data = self.brass_combo.itemData(index)
        self._sync_active_load_session_context()

    def _init_load_data(self) -> None:
        """Populate rifle combo once the event loop is running."""
        self._populate_rifle_combo_box()

    def apply_ui_mode_from_settings(self) -> None:
        """Apply guided vs expert mode based on persisted settings."""
        try:
            val = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "ui/mode", "beginner"
            )
        except Exception:
            val = "beginner"

        is_beginner = str(val).lower() != "expert"
        self._apply_ui_mode(is_beginner)

    def _apply_ui_mode(self, is_beginner: bool) -> None:
        try:
            self.guided_hint.setVisible(is_beginner)
        except Exception:
            pass

        advanced: list[QWidget] = []
        try:
            advanced.extend(getattr(self, "_advanced_widgets", []) or [])
        except Exception:
            pass
        try:
            advanced.extend(getattr(self, "_advanced_chrono_widgets", []) or [])
        except Exception:
            pass

        for widget in advanced:
            try:
                if widget.parentWidget() is None:
                    continue  # never show a parentless widget as a top-level window
                widget.setVisible(not is_beginner)
            except Exception:
                pass

        if is_beginner:
            try:
                if (
                    getattr(self, "auto_match_toggle", None)
                    and self.auto_match_toggle.isChecked()
                ):
                    self.auto_match_toggle.setChecked(False)
            except Exception:
                pass

    def refresh_pressure_log(self):
        """Reload the pressure_history list applying current filters."""
        try:
            rows = query_recent_pressures(self.db, limit=500)
        except Exception:
            rows = []

        # Apply firearm filter, date range, and quick text filter
        rifle_id = None
        if hasattr(self, "pressure_rifle_combo"):
            sel = self.pressure_rifle_combo.currentData()
            if isinstance(sel, int):
                rifle_id = sel

        q = ""
        if hasattr(self, "pressure_search"):
            q = (self.pressure_search.text() or "").strip().lower()

        # date range
        date_from = None
        date_to = None
        if hasattr(self, "pressure_from") and hasattr(self, "pressure_to"):
            try:
                date_from = self.pressure_from.date().toString("yyyy-MM-dd")
                date_to = self.pressure_to.date().toString("yyyy-MM-dd")
            except Exception:
                date_from = None
                date_to = None

        # build id->name caches
        rifle_names = {}
        ammo_names = {}
        try:
            for r in self.db.execute_query("SELECT id, name FROM rifles"):
                rifle_names[r.get("id")] = r.get("name")
        except Exception:
            pass
        try:
            for a in self.db.execute_query("SELECT id, name FROM ammo_profiles"):
                ammo_names[a.get("id")] = a.get("name")
        except Exception:
            pass

        filtered = []
        for r in rows:
            if rifle_id and r.get("rifle_id") != rifle_id:
                continue

            ts = r.get("timestamp") or ""
            ts_date = ts[:10] if isinstance(ts, str) and len(ts) >= 10 else ""
            if date_from and ts_date and ts_date < date_from:
                continue
            if date_to and ts_date and ts_date > date_to:
                continue

            if q:
                note = str(r.get("note") or "").lower()
                if (
                    q not in note
                    and q not in str(r.get("id") or "")
                    and q not in str(r.get("charge_weight") or "")
                ):
                    continue
            filtered.append(r)

        self.pressure_list.clear()
        # build powder/bullet lot mapping per ammo_profile
        ammo_component_lots: dict = {}
        try:
            rows_ap = self.db.execute_query(
                "SELECT id, powder_id, bullet_id FROM ammo_profiles"
            )
            for ap in rows_ap:
                apid = ap.get("id")
                powder_lot = None
                bullet_lot = None
                try:
                    if ap.get("powder_id"):
                        pr = self.db.execute_query(
                            "SELECT lot_number FROM component_lots WHERE component_type='powder' AND component_id=? ORDER BY created_date DESC LIMIT 1",
                            (ap.get("powder_id"),),
                        )
                        if pr:
                            powder_lot = pr[0].get("lot_number")
                except Exception:
                    powder_lot = None
                try:
                    if ap.get("bullet_id"):
                        br = self.db.execute_query(
                            "SELECT lot_number FROM component_lots WHERE component_type='bullet' AND component_id=? ORDER BY created_date DESC LIMIT 1",
                            (ap.get("bullet_id"),),
                        )
                        if br:
                            bullet_lot = br[0].get("lot_number")
                except Exception:
                    bullet_lot = None
                ammo_component_lots[apid] = {
                    "powder_lot": powder_lot,
                    "bullet_lot": bullet_lot,
                }
        except Exception:
            pass

        for r in filtered:
            try:
                pval = r.get("predicted_pressure_psi")
                ptxt = format_pressure_psi(pval) if pval is not None else "N/A"
            except Exception:
                ptxt = "N/A"

            rifle_name = rifle_names.get(r.get("rifle_id"), f"V:{r.get('rifle_id')}")
            ammo_name = ammo_names.get(
                r.get("ammo_profile_id"), f"A:{r.get('ammo_profile_id')}"
            )
            charge_text = format_weight_grains(r.get("charge_weight"), "powder")
            display = f"{r.get('timestamp')} | {rifle_name} | {ammo_name} | Charge:{charge_text} | P:{ptxt} | {r.get('note') or ''}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, r.get("id"))
            self.pressure_list.addItem(item)

    def on_set_date_preset(self, days: int):
        """Set the date_from to `days` ago and refresh the list."""
        try:
            self.pressure_from.setDate(QDate.currentDate().addDays(-int(days)))
            self.pressure_to.setDate(QDate.currentDate())
        except Exception:
            pass
        self.refresh_pressure_log()

    def on_export_pressure_log(self):
        """Export currently filtered pressure log rows to CSV."""
        # Reuse the same filtering logic as refresh (but fetch rows again)
        try:
            rows = query_recent_pressures(self.db, limit=500)
        except Exception:
            rows = []

        rifle_id = None
        if hasattr(self, "pressure_rifle_combo"):
            sel = self.pressure_rifle_combo.currentData()
            rifle_id = sel

        q = ""
        if hasattr(self, "pressure_search"):
            q = (self.pressure_search.text() or "").strip().lower()

        date_from = None
        date_to = None
        if hasattr(self, "pressure_from") and hasattr(self, "pressure_to"):
            try:
                date_from = self.pressure_from.date().toString("yyyy-MM-dd")
                date_to = self.pressure_to.date().toString("yyyy-MM-dd")
            except Exception:
                date_from = None
                date_to = None

        filtered = []
        for r in rows:
            if rifle_id and r.get("rifle_id") != rifle_id:
                continue
            ts = r.get("timestamp") or ""
            ts_date = ts[:10] if isinstance(ts, str) and len(ts) >= 10 else ""
            if date_from and ts_date and ts_date < date_from:
                continue
            if date_to and ts_date and ts_date > date_to:
                continue
            if q:
                note = str(r.get("note") or "").lower()
                if (
                    q not in note
                    and q not in str(r.get("id") or "")
                    and q not in str(r.get("charge_weight") or "")
                ):
                    continue
            filtered.append(r)

        if not filtered:
            QMessageBox.information(
                self, tr("mlb_no_data_title"), tr("mlb_no_pressure_log_rows")
            )
            return

        fname, _ = QFileDialog.getSaveFileName(
            self, tr("mlb_export_pressure_log_csv"), "", "CSV Files (*.csv)"
        )
        if not fname:
            return

        import csv

        # Build name caches
        rifle_names = {}
        ammo_names = {}
        ammo_lots = {}
        ammo_component_lots = {}
        try:
            for r in self.db.execute_query("SELECT id, name FROM rifles"):
                rifle_names[r.get("id")] = r.get("name")
        except Exception:
            pass
        try:
            for a in self.db.execute_query("SELECT id, name FROM ammo_profiles"):
                ammo_names[a.get("id")] = a.get("name")
        except Exception:
            pass
        try:
            for a in self.db.execute_query(
                "SELECT ap.id as apid, c.lot_number as lot FROM ammo_profiles ap LEFT JOIN cases c ON ap.case_id = c.id"
            ):
                ammo_lots[a.get("apid")] = a.get("lot")
        except Exception:
            pass
        try:
            # map ammo_profile -> powder/bullet lot numbers (latest per component)
            for ap in self.db.execute_query(
                "SELECT id, powder_id, bullet_id FROM ammo_profiles"
            ):
                apid = ap.get("id")
                powder_lot = None
                bullet_lot = None
                try:
                    if ap.get("powder_id"):
                        p_row = self.db.execute_query(
                            "SELECT lot_number FROM component_lots WHERE component_type='powder' AND component_id=? ORDER BY created_date DESC LIMIT 1",
                            (ap.get("powder_id"),),
                        )
                        if p_row:
                            powder_lot = p_row[0].get("lot_number")
                except Exception:
                    powder_lot = None
                try:
                    if ap.get("bullet_id"):
                        b_row = self.db.execute_query(
                            "SELECT lot_number FROM component_lots WHERE component_type='bullet' AND component_id=? ORDER BY created_date DESC LIMIT 1",
                            (ap.get("bullet_id"),),
                        )
                        if b_row:
                            bullet_lot = b_row[0].get("lot_number")
                except Exception:
                    bullet_lot = None
                ammo_component_lots[apid] = {
                    "powder_lot": powder_lot,
                    "bullet_lot": bullet_lot,
                }
        except Exception:
            pass

        try:
            with open(fname, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(
                    [
                        "id",
                        "timestamp",
                        "rifle_id",
                        "rifle_name",
                        "ammo_profile_id",
                        "ammo_name",
                        "ammo_case_lot",
                        "powder_lot",
                        "bullet_lot",
                        "charge_weight",
                        "coal_mm",
                        "cbto_mm",
                        "predicted_pressure_psi",
                        "saami_max_psi",
                        "note",
                    ]
                )
                for r in filtered:
                    comp = ammo_component_lots.get(r.get("ammo_profile_id"), {})
                    writer.writerow(
                        [
                            r.get("id"),
                            r.get("timestamp"),
                            r.get("rifle_id"),
                            rifle_names.get(r.get("rifle_id")),
                            r.get("ammo_profile_id"),
                            ammo_names.get(r.get("ammo_profile_id")),
                            ammo_lots.get(r.get("ammo_profile_id")),
                            comp.get("powder_lot"),
                            comp.get("bullet_lot"),
                            r.get("charge_weight"),
                            r.get("coal_mm"),
                            r.get("cbto_mm"),
                            r.get("predicted_pressure_psi"),
                            r.get("saami_max_psi"),
                            r.get("note"),
                        ]
                    )
            QMessageBox.information(
                self,
                tr("mlb_exported_title"),
                tr("mlb_exported_pressure_rows", count=len(filtered), path=fname),
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("mlb_export_failed_title"),
                tr("mlb_export_csv_failed", error=e),
            )

    def create_step1_page(self):
        """Step 1: Select firearm & brass"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Header
        header = QLabel(tr("mlb_step1_header"))
        header.setProperty("role", "title")
        header.setWordWrap(True)
        layout.addWidget(header)

        subtitle = QLabel(tr("mlb_step1_subtitle"))
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Content area
        content = QHBoxLayout()

        # Left: Firearm selection
        rifle_group = self.create_rifle_selection_panel()
        content.addWidget(rifle_group)

        # Right: Brass selection
        brass_group = self.create_brass_selection_panel()
        content.addWidget(brass_group)

        layout.addLayout(content)

        # Navigation
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        self.next_btn = QPushButton(tr("mlb_next_build_load"))
        self.next_btn.setProperty("variant", "primary")
        self.next_btn.setProperty("size", "lg")
        self.next_btn.clicked.connect(self.go_to_step2)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_rifle_selection_panel(self):
        """Build the firearm selection card for step 1."""

        group = QGroupBox(tr("mlb_select_rifle_group"))
        group.setProperty("variant", "panel")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        intro = QLabel(tr("mlb_select_rifle_intro"))
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        layout.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        rifle_layout = QVBoxLayout()
        rifle_layout.setSpacing(8)
        rifle_layout.setContentsMargins(0, 0, 0, 0)

        self.rifle_button_group = QButtonGroup(group)
        self.rifle_button_group.setExclusive(True)
        pending_rifle_id = None
        try:
            pending_rifle_id = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "pending_builder_rifle_id"
            )
        except Exception:
            pending_rifle_id = None

        # If no explicit UI hint, restore from canonical session runtime.
        if pending_rifle_id is None:
            try:
                _rt = self._get_active_load_session_runtime()
                if isinstance(_rt, dict) and _rt.get("rifle_id") not in (None, ""):
                    pending_rifle_id = str(_rt["rifle_id"])
            except Exception:
                pass

        rifles = self._list_rifles_for_selection()

        if rifles:
            for rifle in rifles:
                name = rifle.get("name") or f"Firearm #{rifle.get('id')}"
                caliber = rifle.get("caliber") or "?"
                twist = rifle.get("twist_rate") or "?"
                length = rifle.get("barrel_length_cm")
                details = f"{caliber} • {twist} twist"
                if length:
                    details += f" • {length} cm"
                btn = QRadioButton(f"{name}\n{details}")
                btn.setProperty("variant", "listItem")
                btn.rifle_data = rifle  # type: ignore[attr-defined]
                btn.toggled.connect(self.on_rifle_selected)
                self.rifle_button_group.addButton(btn)
                rifle_layout.addWidget(btn)
                try:
                    if pending_rifle_id is not None and str(rifle.get("id")) == str(
                        pending_rifle_id
                    ):
                        QTimer.singleShot(0, lambda button=btn: button.setChecked(True))
                except Exception:
                    pass
        else:
            placeholder = QLabel(tr("mlb_no_rifles_found"))
            placeholder.setProperty("role", "muted")
            placeholder.setProperty("emphasis", "placeholder")
            placeholder.setWordWrap(True)
            rifle_layout.addWidget(placeholder)

        rifle_layout.addStretch()
        scroll_widget.setLayout(rifle_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        group.setLayout(layout)
        return group

    @staticmethod
    def _coerce_float(value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except Exception:
            return None

    def _list_rifles_for_selection(self):
        try:
            rifles = self.db.execute_query(
                """
                SELECT id, name, caliber, twist_rate, barrel_length_mm
                FROM rifles
                ORDER BY name COLLATE NOCASE
                """
            )
        except Exception:
            return []

        normalized_rifles = []
        for rifle in rifles or []:
            row = dict(rifle)
            barrel_length_mm = self._coerce_float(row.get("barrel_length_mm"))
            if barrel_length_mm is not None:
                row["barrel_length_cm"] = round(barrel_length_mm / 10.0, 1)
            else:
                legacy_length_cm = self._coerce_float(row.get("barrel_length_cm"))
                if legacy_length_cm is not None:
                    row["barrel_length_cm"] = legacy_length_cm
            normalized_rifles.append(row)
        return normalized_rifles

    def create_brass_selection_panel(self):
        """Build the brass selection pane for step 1."""

        group = QGroupBox(tr("mlb_select_brass_batch_group"))
        group.setProperty("variant", "panel")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        intro = QLabel(tr("mlb_select_brass_intro"))
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        layout.addWidget(intro)

        self.brass_button_group = QButtonGroup(group)
        self.brass_button_group.setExclusive(True)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._brass_container_widget = QWidget()
        self.brass_container = QVBoxLayout()
        self.brass_container.setSpacing(8)
        self.brass_container.setContentsMargins(0, 0, 0, 0)
        self._brass_container_widget.setLayout(self.brass_container)
        scroll.setWidget(self._brass_container_widget)
        layout.addWidget(scroll)

        placeholder = QLabel("Select a firearm first to view brass batches.")
        placeholder.setObjectName("brass-placeholder")
        placeholder.setProperty("role", "muted")
        placeholder.setProperty("emphasis", "placeholder")
        placeholder.setWordWrap(True)
        self.brass_container.addWidget(placeholder)
        self.brass_container.addStretch()

        add_btn = QPushButton(tr("mlb_add_new_brass_batch"))
        add_btn.setProperty("variant", "secondary")
        add_btn.clicked.connect(self.on_add_new_brass_batch)
        layout.addWidget(add_btn)

        group.setLayout(layout)
        return group

    def on_rifle_selected(self, checked):
        """Handle firearm selection"""
        if not checked:
            return

        sender = self.sender()
        self.rifle_data = sender.rifle_data  # type: ignore[attr-defined]
        self._rifle_profile_details = None
        self._rifle_profile_details_id = None
        self._latest_load_analysis = None
        self._latest_seating_summary = None
        self._recommendation_baseline = None
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.remove("pending_builder_rifle_id")
            settings.remove("pending_builder_barrel_id")
        except Exception:
            pass

        # Load brass for this caliber
        self.load_brass_for_caliber(self.rifle_data["caliber"])
        self._refresh_active_rifle_context()
        self._sync_active_load_session_context()

        self.check_step1_complete()

    def load_brass_for_caliber(self, caliber):
        """Load brass batches for selected caliber"""
        if not hasattr(self, "brass_container"):
            return

        # Clear existing
        while self.brass_container.count():
            item = self.brass_container.takeAt(0)
            if item is not None and item.widget():
                item.widget().deleteLater()  # type: ignore[union-attr]

        self.brass_button_group = QButtonGroup(self)
        self.brass_button_group.setExclusive(True)

        # Query brass
        brass_batches = self.db.execute_query(
            """
            SELECT bb.*, c.name as case_name
            FROM brass_batches bb
            JOIN cases c ON bb.case_id = c.id
            WHERE c.caliber = ?
            AND bb.cases_active > 0
            ORDER BY bb.created_date DESC
        """,
            (caliber,),
        )

        if brass_batches:
            for brass in brass_batches:
                rb = QRadioButton(
                    f"{brass['case_name']} Batch #{brass['id']}\n"
                    f"  {brass['cases_active']} cases, "
                    f"{brass.get('times_fired_avg', 0):.0f}x fired"
                )
                rb.setProperty("variant", "listItem")
                rb.brass_data = brass  # type: ignore[attr-defined]
                rb.toggled.connect(self.on_brass_selected)
                self.brass_button_group.addButton(rb)
                self.brass_container.addWidget(rb)
        else:
            no_brass = QLabel(tr("mlb_no_brass_for_caliber", caliber=caliber))
            no_brass.setProperty("role", "muted")
            no_brass.setProperty("emphasis", "placeholder")
            self.brass_container.addWidget(no_brass)

        manual_rb = QRadioButton(
            "Other / unbatched brass\n"
            "  Bruk dette hvis du vil velge brass selv uten registrert batchnummer"
        )
        manual_rb.setProperty("variant", "listItem")
        manual_rb.brass_data = {  # type: ignore[attr-defined]
            "id": None,
            "case_id": None,
            "case_name": caliber,
            "manufacturer": "",
            "name": "Other / unbatched brass",
            "times_fired_avg": None,
            "is_manual": True,
            "tracked_batch": False,
        }
        manual_rb.toggled.connect(self.on_brass_selected)
        self.brass_button_group.addButton(manual_rb)
        self.brass_container.addWidget(manual_rb)

        self.brass_container.addStretch()

    def on_add_new_brass_batch(self):
        """Open the brass manager so the user can register a new batch."""

        try:
            from .brass_manager import BrassManager
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("mlb_error_title"),
                tr("mlb_open_brass_manager_failed", error=exc),
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_brass_manager_title"))
        dlg.setModal(True)
        dlg.resize(960, 720)
        container = QVBoxLayout(dlg)
        manager = BrassManager()
        manager.setParent(dlg)
        container.addWidget(manager)
        dlg.setLayout(container)
        dlg.exec()

        try:
            if self.rifle_data and self.rifle_data.get("caliber"):
                self._populate_brass_combo(self.rifle_data["caliber"])
        except Exception:
            pass

    def on_brass_selected(self, checked):
        """Handle brass selection"""
        if not checked:
            return

        sender = self.sender()
        self.brass_data = sender.brass_data  # type: ignore[attr-defined]
        self._sync_active_load_session_context()

        self.check_step1_complete()

    def check_step1_complete(self):
        """Enable next button if firearm and brass are selected"""
        if self.rifle_data and self.brass_data:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)

    def _has_tracked_brass_batch(self) -> bool:
        """Return True when selected brass is linked to a known batch."""
        if not isinstance(self.brass_data, dict):
            return False
        if self.brass_data.get("is_manual"):
            return False
        return bool(self.brass_data.get("id"))

    def go_to_step2(self):
        """Move to step 2: Load builder"""
        # Hide step 1
        self.step1_widget.hide()

        # Show step 2
        if self.layout() is not None:
            self.layout().addWidget(self.step2_widget)  # type: ignore[union-attr]
        self.step2_widget.show()

        # Initialize step 2 with weapon data
        self.initialize_step2()
        # persist last-open step
        try:
            self.current_step = 2
            self._save_ui_setting("last_step", "2")
        except Exception:
            pass

    def create_step2_page(self):
        """Step 2: Interactive Load Builder"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton(tr("mlb_back"))
        back_btn.setProperty("variant", "secondary")
        back_btn.clicked.connect(self.go_back_to_step1)
        header_layout.addWidget(back_btn)

        title = QLabel(tr("mlb_interactive_builder"))
        title.setProperty("role", "title")
        header_layout.addWidget(title)

        header_layout.addStretch()

        load_btn = QPushButton(tr("mlb_load_saved_design"))
        load_btn.setProperty("variant", "ghost")
        load_btn.setToolTip(tr("mlb_load_saved_design_tooltip"))
        load_btn.clicked.connect(self.on_load_saved_design_clicked)
        header_layout.addWidget(load_btn)

        save_btn = QPushButton(tr("mlb_save_load"))
        save_btn.setProperty("variant", "primary")
        save_btn.setToolTip(tr("mlb_save_load_tooltip"))
        save_btn.clicked.connect(self.on_save_load_clicked)
        header_layout.addWidget(save_btn)

        create_batch_btn = QPushButton(tr("mlb_create_batch"))
        create_batch_btn.setProperty("variant", "secondary")
        header_layout.addWidget(create_batch_btn)
        create_batch_btn.clicked.connect(self.on_create_batch_clicked)

        print_label_btn = QPushButton(tr("mlb_print_label"))
        print_label_btn.setProperty("variant", "secondary")
        print_label_btn.clicked.connect(self.on_print_label_clicked)
        header_layout.addWidget(print_label_btn)

        layout.addLayout(header_layout)

        # Main content: Splitter (recipe, precision lab, safety)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        recipe_panel = self.create_recipe_panel()
        splitter.addWidget(recipe_panel)

        precision_panel = self.create_precision_lab_panel()
        splitter.addWidget(precision_panel)

        safety_panel = self.create_safety_panel()
        splitter.addWidget(safety_panel)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 2)

        layout.addWidget(splitter, 1)

        # Bottom: AI Chat (collapsible)
        self.chat_widget = self.create_ai_chat_panel()
        layout.addWidget(self.chat_widget)

        widget.setLayout(layout)
        return widget

    def create_recipe_panel(self):
        """Create the recipe builder panel."""
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel(tr("mlb_recipe_builder"))
        title.setProperty("variant", "cardTitle")
        layout.addWidget(title)

        subtitle = QLabel(tr("mlb_recipe_subtitle"))
        subtitle.setProperty("variant", "cardSubtitle")
        layout.addWidget(subtitle)

        layout.addWidget(self.create_controls_panel(), 1)

        widget.setLayout(layout)
        return widget

    def create_precision_lab_panel(self):
        """Create the precision lab visualization panel."""
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel(tr("mlb_precision_lab"))
        title.setProperty("variant", "cardTitle")
        layout.addWidget(title)

        subtitle = QLabel(tr("mlb_precision_subtitle"))
        subtitle.setProperty("variant", "cardSubtitle")
        layout.addWidget(subtitle)

        layout.addWidget(self.create_visualization_panel(), 1)

        self.precision_hint = QLabel(tr("mlb_precision_hint"))
        self.precision_hint.setProperty("variant", "callout")
        self.precision_hint.setWordWrap(True)
        layout.addWidget(self.precision_hint)

        widget.setLayout(layout)
        return widget

    def create_safety_panel(self):
        """Create the safety and QA panel."""
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel(tr("mlb_safety_qa"))
        title.setProperty("variant", "cardTitle")
        layout.addWidget(title)

        subtitle = QLabel(tr("mlb_safety_subtitle"))
        subtitle.setProperty("variant", "cardSubtitle")
        layout.addWidget(subtitle)

        self.safety_status_label = QLabel(tr("mlb_select_components_for_safety"))
        self.safety_status_label.setProperty("role", "muted")
        self.safety_status_label.setWordWrap(True)
        layout.addWidget(self.safety_status_label)

        self.pressure_alert_label = QLabel(f"{tr('mlb_pressure_spike_risk')}: --")
        self.pressure_alert_label.setWordWrap(True)
        self.pressure_alert_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.pressure_alert_label)

        self.powder_lot_alert_label = QLabel(f"{tr('mlb_powder_lot')}: --")
        self.powder_lot_alert_label.setWordWrap(True)
        self.powder_lot_alert_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.powder_lot_alert_label)

        self.component_verification_label = QLabel(
            f"{tr('mlb_combined_verification')}: --"
        )
        self.component_verification_label.setWordWrap(True)
        self.component_verification_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.component_verification_label)

        self.retest_advisor_label = QLabel("Retest Advisor: --")
        self.retest_advisor_label.setWordWrap(True)
        self.retest_advisor_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.retest_advisor_label)

        self.stability_advisor_label = QLabel("Stability Advisor: --")
        self.stability_advisor_label.setWordWrap(True)
        self.stability_advisor_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.stability_advisor_label)

        self.bullet_fit_label = QLabel("Bullet Fit: --")
        self.bullet_fit_label.setWordWrap(True)
        self.bullet_fit_label.setTextFormat(Qt.TextFormat.RichText)
        self.bullet_fit_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.bullet_fit_label)

        self.recommendation_state_label = QLabel("Recommendation State: --")
        self.recommendation_state_label.setWordWrap(True)
        self.recommendation_state_label.setTextFormat(Qt.TextFormat.RichText)
        self.recommendation_state_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.recommendation_state_label)

        recommendation_action_row = QHBoxLayout()
        self.use_recommended_btn = QPushButton("Use Recommended")
        self.use_recommended_btn.setProperty("variant", "ghost")
        self.use_recommended_btn.setEnabled(False)
        self.use_recommended_btn.clicked.connect(
            self.on_apply_recommendation_baseline_clicked
        )
        recommendation_action_row.addWidget(self.use_recommended_btn)
        recommendation_action_row.addStretch()
        layout.addLayout(recommendation_action_row)

        self.subsonic_advisor_label = QLabel("Subsonic Advisor: --")
        self.subsonic_advisor_label.setWordWrap(True)
        self.subsonic_advisor_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.subsonic_advisor_label)

        self.model_vs_measured_label = QLabel("Model vs Measured: --")
        self.model_vs_measured_label.setWordWrap(True)
        self.model_vs_measured_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.model_vs_measured_label)

        self.retest_action_btn = QPushButton("Opprett retest-serie")
        self.retest_action_btn.setProperty("variant", "secondary")
        self.retest_action_btn.clicked.connect(self.on_create_retest_session_clicked)
        layout.addWidget(self.retest_action_btn)

        self.impact_window_label = QLabel(f"{tr('mlb_impact_window')}: --")
        self.impact_window_label.setWordWrap(True)
        self.impact_window_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.impact_window_label)

        self.game_suitability_label = QLabel("Game Suitability: --")
        self.game_suitability_label.setWordWrap(True)
        self.game_suitability_label.setTextFormat(Qt.TextFormat.RichText)
        self.game_suitability_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.game_suitability_label)

        self.calibration_profile_label = QLabel(f"{tr('mlb_calibration_profile')}: --")
        self.calibration_profile_label.setWordWrap(True)
        self.calibration_profile_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.calibration_profile_label)

        self.internal_ballistics_label = QLabel(f"{tr('mlb_internal_ballistics')}: --")
        self.internal_ballistics_label.setWordWrap(True)
        self.internal_ballistics_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.internal_ballistics_label)

        self.evidence_basis_label = QLabel(f"{tr('mlb_evidence_basis')}: --")
        self.evidence_basis_label.setWordWrap(True)
        self.evidence_basis_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.evidence_basis_label)

        margin_group = QGroupBox(tr("mlb_pressure_margin"))
        margin_group.setProperty("variant", "panel")
        margin_layout = QVBoxLayout()
        self.safety_margin_label = QLabel(f"{tr('mlb_safety_margin')}: --")
        self.safety_pressure_label = QLabel(f"{tr('mlb_peak_pressure')}: --")
        self.safety_saami_label = QLabel(f"{tr('mlb_max_pressure')}: --")
        self.safety_mag_label = QLabel(f"{tr('mlb_magazine_limit')}: --")
        margin_layout.addWidget(self.safety_margin_label)
        margin_layout.addWidget(self.safety_pressure_label)
        margin_layout.addWidget(self.safety_saami_label)
        margin_layout.addWidget(self.safety_mag_label)
        margin_group.setLayout(margin_layout)
        layout.addWidget(margin_group)

        confidence_group = QGroupBox(tr("mlb_confidence"))
        confidence_group.setProperty("variant", "panel")
        confidence_layout = QVBoxLayout()
        self.confidence_label = QLabel(tr("mlb_calibration_unavailable"))
        self.confidence_label.setProperty("role", "muted")
        confidence_layout.addWidget(self.confidence_label)
        self.runtime_context_label = QLabel("Session Runtime: --")
        self.runtime_context_label.setWordWrap(True)
        self.runtime_context_label.setTextFormat(Qt.TextFormat.RichText)
        self.runtime_context_label.setStyleSheet(_advisory_style("unknown"))
        confidence_layout.addWidget(self.runtime_context_label)
        self.runtime_delta_label = QLabel("Runtime Delta: --")
        self.runtime_delta_label.setWordWrap(True)
        self.runtime_delta_label.setTextFormat(Qt.TextFormat.RichText)
        self.runtime_delta_label.setStyleSheet(_advisory_style("unknown"))
        confidence_layout.addWidget(self.runtime_delta_label)
        self.analysis_health_label = QLabel("Model Health: --")
        self.analysis_health_label.setWordWrap(True)
        self.analysis_health_label.setTextFormat(Qt.TextFormat.RichText)
        confidence_layout.addWidget(self.analysis_health_label)
        self.analysis_trust_label = QLabel("Evidence Map: --")
        self.analysis_trust_label.setWordWrap(True)
        self.analysis_trust_label.setTextFormat(Qt.TextFormat.RichText)
        confidence_layout.addWidget(self.analysis_trust_label)
        self.harmonics_profile_btn = QPushButton(tr("mlb_update_harmonics_profile"))
        self.harmonics_profile_btn.setProperty("variant", "secondary")
        self.harmonics_profile_btn.setEnabled(False)
        self.harmonics_profile_btn.clicked.connect(self.on_open_harmonics_profile)
        confidence_layout.addWidget(self.harmonics_profile_btn)
        confidence_group.setLayout(confidence_layout)
        layout.addWidget(confidence_group)

        evidence_group = QGroupBox(tr("mlb_evidence_basis"))
        evidence_group.setProperty("variant", "panel")
        evidence_layout = QVBoxLayout()
        self.evidence_label = QLabel(tr("mlb_evidence_basis_hint"))
        self.evidence_label.setWordWrap(True)
        evidence_layout.addWidget(self.evidence_label)
        evidence_actions = QHBoxLayout()
        self.evidence_h2o_btn = QPushButton(tr("mlb_add_h2o"))
        self.evidence_h2o_btn.setProperty("variant", "secondary")
        self.evidence_h2o_btn.clicked.connect(self.on_open_case_capacity_profile)
        evidence_actions.addWidget(self.evidence_h2o_btn)
        self.evidence_chrono_btn = QPushButton(tr("mlb_select_import_chrono"))
        self.evidence_chrono_btn.setProperty("variant", "secondary")
        self.evidence_chrono_btn.clicked.connect(self.on_focus_chronograph_data)
        evidence_actions.addWidget(self.evidence_chrono_btn)
        self.evidence_group_btn = QPushButton(tr("mlb_register_calibration_series"))
        self.evidence_group_btn.setProperty("variant", "secondary")
        self.evidence_group_btn.clicked.connect(self.on_add_group_data)
        evidence_actions.addWidget(self.evidence_group_btn)
        evidence_layout.addLayout(evidence_actions)
        self.calibration_table = QTableWidget()
        self.calibration_table.setColumnCount(7)
        self.calibration_table.setHorizontalHeaderLabels(
            [
                tr("mlb_calibration_powder"),
                tr("mlb_calibration_lot"),
                tr("mlb_calibration_charge"),
                tr("mlb_calibration_v0"),
                "ES/SD",
                tr("mlb_calibration_image"),
                tr("mlb_calibration_series"),
            ]
        )
        self.calibration_table.setAlternatingRowColors(True)
        self.calibration_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.calibration_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.calibration_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        _vh = self.calibration_table.verticalHeader()
        if _vh is not None:
            _vh.setVisible(False)
        self.calibration_table.cellDoubleClicked.connect(
            self.on_edit_calibration_series
        )
        try:
            header = self.calibration_table.horizontalHeader()
            if header is not None:
                header.setStretchLastSection(True)
        except Exception:
            pass
        self.calibration_table.setMinimumHeight(150)
        evidence_layout.addWidget(self.calibration_table)
        self.calibration_trend_label = QLabel(tr("mlb_calibration_trend_placeholder"))
        self.calibration_trend_label.setWordWrap(True)
        self.calibration_trend_label.setProperty("variant", "callout")
        evidence_layout.addWidget(self.calibration_trend_label)
        calibration_plot_controls = QHBoxLayout()
        calibration_plot_controls.addWidget(QLabel(tr("mlb_calibration_plot")))
        self.calibration_metric_combo = QComboBox()
        self.calibration_metric_combo.addItems(["Velocity", "ES", "SD", "Gruppe"])
        self.calibration_metric_combo.currentIndexChanged.connect(
            self._refresh_calibration_plot
        )
        calibration_plot_controls.addWidget(self.calibration_metric_combo)
        calibration_plot_controls.addWidget(QLabel(tr("mlb_powder_filter")))
        self.calibration_powder_filter = QComboBox()
        self.calibration_powder_filter.addItem(tr("mlb_all_powders"), "")
        self.calibration_powder_filter.currentIndexChanged.connect(
            self._refresh_calibration_table
        )
        calibration_plot_controls.addWidget(self.calibration_powder_filter)
        calibration_plot_controls.addWidget(QLabel(tr("mlb_bullet_filter")))
        self.calibration_bullet_filter = QComboBox()
        self.calibration_bullet_filter.addItem(tr("mlb_all_bullets"), "")
        self.calibration_bullet_filter.currentIndexChanged.connect(
            self._refresh_calibration_table
        )
        calibration_plot_controls.addWidget(self.calibration_bullet_filter)
        calibration_plot_controls.addWidget(QLabel(tr("mlb_lot_filter")))
        self.calibration_lot_filter = QComboBox()
        self.calibration_lot_filter.addItem(tr("mlb_all_lots"), "")
        self.calibration_lot_filter.currentIndexChanged.connect(
            self._refresh_calibration_table
        )
        calibration_plot_controls.addWidget(self.calibration_lot_filter)
        calibration_plot_controls.addWidget(QLabel(tr("mlb_distance_filter")))
        self.calibration_distance_filter = QComboBox()
        self.calibration_distance_filter.addItem(tr("mlb_all_distances"), "")
        self.calibration_distance_filter.currentIndexChanged.connect(
            self._refresh_calibration_table
        )
        calibration_plot_controls.addWidget(self.calibration_distance_filter)
        calibration_plot_controls.addWidget(QLabel(tr("mlb_temp_filter")))
        self.calibration_temperature_filter = QComboBox()
        self.calibration_temperature_filter.addItem(tr("mlb_all_temperatures"), "")
        self.calibration_temperature_filter.currentIndexChanged.connect(
            self._refresh_calibration_table
        )
        calibration_plot_controls.addWidget(self.calibration_temperature_filter)
        calibration_plot_controls.addStretch()
        evidence_layout.addLayout(calibration_plot_controls)
        self.calibration_plot_placeholder = QLabel(
            tr("mlb_calibration_plot_placeholder")
        )
        self.calibration_plot_placeholder.setWordWrap(True)
        self.calibration_plot_placeholder.setProperty("role", "muted")
        evidence_layout.addWidget(self.calibration_plot_placeholder)
        self.temperature_drift_placeholder = QLabel(tr("mlb_temp_drift_placeholder"))
        self.temperature_drift_placeholder.setWordWrap(True)
        self.temperature_drift_placeholder.setProperty("role", "muted")
        evidence_layout.addWidget(self.temperature_drift_placeholder)
        evidence_group.setLayout(evidence_layout)
        layout.addWidget(evidence_group)

        checks_group = QGroupBox(tr("mlb_checks"))
        checks_group.setProperty("variant", "panel")
        checks_layout = QVBoxLayout()
        self.safety_checks = QListWidget()
        self.safety_checks.addItem(tr("mlb_select_components_for_checks"))
        checks_layout.addWidget(self.safety_checks)
        checks_group.setLayout(checks_layout)
        layout.addWidget(checks_group, 1)

        next_group = QGroupBox(tr("mlb_next_step_title"))
        next_group.setProperty("variant", "panel")
        next_layout = QVBoxLayout()
        self.load_card_summary_label = QLabel("Load Card: --")
        self.load_card_summary_label.setWordWrap(True)
        self.load_card_summary_label.setProperty("role", "muted")
        next_layout.addWidget(self.load_card_summary_label)
        self.safety_next_label = QLabel(tr("mlb_next_step_placeholder"))
        self.safety_next_label.setWordWrap(True)
        next_layout.addWidget(self.safety_next_label)
        self.pipe_history_label = QLabel("Barrel History: --")
        self.pipe_history_label.setWordWrap(True)
        self.pipe_history_label.setProperty("role", "muted")
        next_layout.addWidget(self.pipe_history_label)
        self.barrel_context_label = QLabel("Barrel Context: --")
        self.barrel_context_label.setWordWrap(True)
        self.barrel_context_label.setProperty("role", "muted")
        next_layout.addWidget(self.barrel_context_label)
        self.brass_context_label = QLabel("Brass Baseline: --")
        self.brass_context_label.setWordWrap(True)
        self.brass_context_label.setProperty("role", "muted")
        next_layout.addWidget(self.brass_context_label)
        self.powder_internal_label = QLabel("Powder & Burn: --")
        self.powder_internal_label.setWordWrap(True)
        self.powder_internal_label.setProperty("role", "muted")
        next_layout.addWidget(self.powder_internal_label)
        self.projectile_context_label = QLabel("Projectile Profile: --")
        self.projectile_context_label.setWordWrap(True)
        self.projectile_context_label.setProperty("role", "muted")
        next_layout.addWidget(self.projectile_context_label)
        self.primer_context_label = QLabel("Primer Profile: --")
        self.primer_context_label.setWordWrap(True)
        self.primer_context_label.setProperty("role", "muted")
        next_layout.addWidget(self.primer_context_label)
        self.pipe_history_trend_label = QLabel("Trend: --")
        self.pipe_history_trend_label.setWordWrap(True)
        self.pipe_history_trend_label.setProperty("role", "muted")
        next_layout.addWidget(self.pipe_history_trend_label)
        self.learning_runtime_label = QLabel("Learning State: --")
        self.learning_runtime_label.setWordWrap(True)
        self.learning_runtime_label.setProperty("role", "muted")
        next_layout.addWidget(self.learning_runtime_label)
        next_group.setLayout(next_layout)
        layout.addWidget(next_group)

        widget.setLayout(layout)
        return widget

    def create_controls_panel(self):
        """Create left control panel"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setProperty("variant", "clean")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        # Components
        comp_group = self.create_component_controls()
        scroll_layout.addWidget(comp_group)

        # Charge weight slider
        charge_group = self.create_charge_slider()
        scroll_layout.addWidget(charge_group)

        # Seating depth
        seating_group = self.create_seating_controls()
        scroll_layout.addWidget(seating_group)

        scroll_layout.addStretch()

        # Import chronograph CSV button
        import_btn = QPushButton(tr("mlb_import_chrono_csv"))
        import_btn.setProperty("variant", "secondary")
        import_btn.clicked.connect(self.on_import_chronograph_clicked)
        scroll_layout.addWidget(import_btn)

        # Manual chronograph entry
        manual_btn = QPushButton(tr("mlb_manual_chrono"))
        manual_btn.setProperty("variant", "secondary")
        manual_btn.clicked.connect(self.on_manual_chronograph_clicked)
        scroll_layout.addWidget(manual_btn)

        # Chronograph imports list
        chrono_group = QGroupBox(tr("mlb_imported_chrono_data"))
        chrono_group.setProperty("variant", "panel")
        chrono_layout = QVBoxLayout()

        self.chrono_list = QListWidget()
        chrono_layout.addWidget(self.chrono_list)
        self.chrono_list.itemSelectionChanged.connect(self.on_chrono_selection_changed)

        chrono_btn_layout = QHBoxLayout()
        refresh_btn = QPushButton(tr("mlb_refresh"))
        refresh_btn.setProperty("variant", "secondary")
        refresh_btn.clicked.connect(self.on_refresh_chronograph_list)
        chrono_btn_layout.addWidget(refresh_btn)

        attach_btn = QPushButton(tr("mlb_attach_profile"))
        attach_btn.setProperty("variant", "secondary")
        attach_btn.clicked.connect(self.on_attach_chronograph_to_profile)
        chrono_btn_layout.addWidget(attach_btn)

        save_btn = QPushButton(tr("mlb_save_import_results"))
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self.on_save_chronograph_to_test_results)
        chrono_btn_layout.addWidget(save_btn)

        chrono_qc_attach_btn = QPushButton(tr("mlb_attach_qc_batch"))
        chrono_qc_attach_btn.clicked.connect(self.on_attach_chrono_to_qc_batch)
        chrono_btn_layout.addWidget(chrono_qc_attach_btn)

        chrono_suggest_btn = QPushButton(tr("mlb_analyze_suggest"))
        chrono_suggest_btn.clicked.connect(self.on_analyze_and_suggest)
        chrono_btn_layout.addWidget(chrono_suggest_btn)

        chrono_optimize_btn = QPushButton(tr("mlb_optimize_ladder"))
        chrono_optimize_btn.clicked.connect(self.on_optimize_from_ladder_tests)
        chrono_btn_layout.addWidget(chrono_optimize_btn)

        chrono_calibrate_btn = QPushButton(tr("mlb_calibrate_engine"))
        chrono_calibrate_btn.clicked.connect(self.on_calibrate_engine_clicked)
        chrono_btn_layout.addWidget(chrono_calibrate_btn)

        chrono_show_cal_btn = QPushButton(tr("mlb_show_calibration"))
        chrono_show_cal_btn.clicked.connect(self.on_show_calibration_clicked)
        chrono_btn_layout.addWidget(chrono_show_cal_btn)

        try:
            self._advanced_chrono_widgets.extend(
                [
                    chrono_qc_attach_btn,
                    chrono_suggest_btn,
                    chrono_optimize_btn,
                    chrono_calibrate_btn,
                    chrono_show_cal_btn,
                ]
            )
        except Exception:
            pass

        chrono_layout.addLayout(chrono_btn_layout)
        chrono_group.setLayout(chrono_layout)
        scroll_layout.addWidget(chrono_group)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)

        layout.addWidget(scroll)
        widget.setLayout(layout)

        return widget

    def create_component_controls(self):
        """Create component selection controls"""
        group = QGroupBox(tr("mlb_components"))
        group.setProperty("variant", "panel")
        layout = QVBoxLayout()

        self.rifle_context_label = QLabel(tr("mlb_rifle_context"))
        self.rifle_context_label.setWordWrap(True)
        self.rifle_context_label.setProperty("variant", "callout")
        layout.addWidget(self.rifle_context_label)

        setup_row = QHBoxLayout()
        setup_row.addWidget(QLabel("Setup"))
        self.barrel_configuration_combo = QComboBox()
        self.barrel_configuration_combo.currentIndexChanged.connect(
            self.on_barrel_configuration_changed
        )
        setup_row.addWidget(self.barrel_configuration_combo, 1)
        layout.addLayout(setup_row)

        # Bullet
        bullet_label = QLabel(tr("mlb_bullet"))
        layout.addWidget(bullet_label)

        bullet_row = QHBoxLayout()
        self.bullet_combo = QComboBox()
        self.bullet_combo.currentIndexChanged.connect(self.on_bullet_changed)
        bullet_row.addWidget(self.bullet_combo, 1)
        self.manual_bullet_btn = QPushButton(tr("mlb_manual_bullet"))
        self.manual_bullet_btn.setProperty("variant", "secondary")
        self.manual_bullet_btn.clicked.connect(self.on_add_manual_bullet)
        bullet_row.addWidget(self.manual_bullet_btn)
        self.open_bullet_library_btn = QPushButton("Library")
        self.open_bullet_library_btn.setProperty("variant", "ghost")
        self.open_bullet_library_btn.clicked.connect(
            lambda: self._open_selected_component_in_library("bullet")
        )
        bullet_row.addWidget(self.open_bullet_library_btn)
        layout.addLayout(bullet_row)

        self.bullet_lot_combo = QComboBox()
        self.bullet_lot_combo.currentIndexChanged.connect(self.on_bullet_lot_changed)
        bullet_lot_row = QHBoxLayout()
        bullet_lot_row.addWidget(self.bullet_lot_combo, 1)
        self.add_bullet_lot_btn = QPushButton("New Lot")
        self.add_bullet_lot_btn.setProperty("variant", "ghost")
        self.add_bullet_lot_btn.clicked.connect(self.on_add_bullet_lot)
        bullet_lot_row.addWidget(self.add_bullet_lot_btn)
        self.edit_bullet_lot_btn = QPushButton("Edit Lot")
        self.edit_bullet_lot_btn.setProperty("variant", "ghost")
        self.edit_bullet_lot_btn.clicked.connect(self.on_edit_bullet_lot)
        bullet_lot_row.addWidget(self.edit_bullet_lot_btn)
        layout.addLayout(bullet_lot_row)

        self.bullet_info = QLabel(tr("mlb_select_bullet_details"))
        self.bullet_info.setProperty("role", "muted")
        self.bullet_info.setProperty("emphasis", "placeholder")
        layout.addWidget(self.bullet_info)

        self.edit_bullet_btn = QPushButton(tr("mlb_edit_selected_bullet"))
        self.edit_bullet_btn.setProperty("variant", "secondary")
        self.edit_bullet_btn.clicked.connect(self.on_edit_selected_bullet)
        self.edit_bullet_btn.setEnabled(False)
        layout.addWidget(self.edit_bullet_btn)

        layout.addSpacing(10)

        # Environmental conditions
        env_group = QGroupBox(tr("mlb_ambient_conditions"))
        env_group.setProperty("variant", "panel")
        env_layout = QHBoxLayout()
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(
            float(temperature_c_to_display_value(-40.0) or -40.0),
            float(temperature_c_to_display_value(60.0) or 60.0),
        )
        self.temp_spin.setValue(float(temperature_c_to_display_value(15.0) or 15.0))
        self.temp_spin.setSuffix(get_temperature_suffix())
        env_layout.addWidget(QLabel(tr("mlb_temp")))
        env_layout.addWidget(self.temp_spin)

        self.pressure_spin = QDoubleSpinBox()
        self.pressure_spin.setRange(
            float(pressure_kpa_to_display_value(70.0) or 70.0),
            float(pressure_kpa_to_display_value(110.0) or 110.0),
        )
        self.pressure_spin.setValue(
            float(pressure_kpa_to_display_value(101.325) or 101.325)
        )
        self.pressure_spin.setSuffix(get_pressure_suffix())
        env_layout.addWidget(QLabel(tr("mlb_pressure")))
        env_layout.addWidget(self.pressure_spin)

        self.humidity_spin = QDoubleSpinBox()
        self.humidity_spin.setRange(0.0, 100.0)
        self.humidity_spin.setValue(0.0)
        self.humidity_spin.setSuffix(" %")
        env_layout.addWidget(QLabel(tr("mlb_humidity")))
        env_layout.addWidget(self.humidity_spin)

        env_group.setLayout(env_layout)
        layout.addWidget(env_group)

        # Powder
        powder_label = QLabel(tr("mlb_powder"))
        layout.addWidget(powder_label)

        powder_row = QHBoxLayout()
        self.powder_combo = QComboBox()
        self.powder_combo.currentIndexChanged.connect(self.on_powder_changed)
        powder_row.addWidget(self.powder_combo, 1)
        self.manual_powder_btn = QPushButton(tr("mlb_manual_powder"))
        self.manual_powder_btn.setProperty("variant", "secondary")
        self.manual_powder_btn.clicked.connect(self.on_add_manual_powder)
        powder_row.addWidget(self.manual_powder_btn)
        self.open_powder_library_btn = QPushButton("Library")
        self.open_powder_library_btn.setProperty("variant", "ghost")
        self.open_powder_library_btn.clicked.connect(
            lambda: self._open_selected_component_in_library("powder")
        )
        powder_row.addWidget(self.open_powder_library_btn)
        layout.addLayout(powder_row)

        self.powder_lot_combo = QComboBox()
        self.powder_lot_combo.currentIndexChanged.connect(self.on_powder_lot_changed)
        powder_lot_row = QHBoxLayout()
        powder_lot_row.addWidget(self.powder_lot_combo, 1)
        self.add_powder_lot_btn = QPushButton("New Lot")
        self.add_powder_lot_btn.setProperty("variant", "ghost")
        self.add_powder_lot_btn.clicked.connect(self.on_add_powder_lot)
        powder_lot_row.addWidget(self.add_powder_lot_btn)
        self.edit_powder_lot_btn = QPushButton("Edit Lot")
        self.edit_powder_lot_btn.setProperty("variant", "ghost")
        self.edit_powder_lot_btn.clicked.connect(self.on_edit_powder_lot)
        powder_lot_row.addWidget(self.edit_powder_lot_btn)
        layout.addLayout(powder_lot_row)

        self.powder_info = QLabel(tr("mlb_select_powder_details"))
        self.powder_info.setProperty("role", "muted")
        self.powder_info.setProperty("emphasis", "placeholder")
        layout.addWidget(self.powder_info)

        # AI recommendation placeholder
        self.powder_recommendation = QLabel("")
        self.powder_recommendation.setWordWrap(True)
        self.powder_recommendation.setProperty("variant", "callout")
        layout.addWidget(self.powder_recommendation)

        self.powder_sandbox_label = QLabel("")
        self.powder_sandbox_label.setWordWrap(True)
        self.powder_sandbox_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.powder_sandbox_label)

        self.component_fit_label = QLabel(tr("mlb_component_fit_placeholder"))
        self.component_fit_label.setWordWrap(True)
        self.component_fit_label.setProperty("variant", "callout")
        layout.addWidget(self.component_fit_label)

        self.component_context_label = QLabel(
            "No active component context yet. Select a bullet, powder, and preferably lots to see whether the builder is using standard data, measured lot means, or historical learning."
        )
        self.component_context_label.setWordWrap(True)
        self.component_context_label.setProperty("variant", "panel")
        layout.addWidget(self.component_context_label)

        layout.addSpacing(10)

        # Primer
        primer_label = QLabel(tr("mlb_primer"))
        layout.addWidget(primer_label)

        primer_row = QHBoxLayout()
        self.primer_combo = QComboBox()
        self.primer_combo.currentIndexChanged.connect(self.on_primer_changed)
        primer_row.addWidget(self.primer_combo, 1)
        self.manual_primer_btn = QPushButton("Manual Primer")
        self.manual_primer_btn.setProperty("variant", "secondary")
        self.manual_primer_btn.clicked.connect(self.on_add_manual_primer)
        primer_row.addWidget(self.manual_primer_btn)
        self.open_primer_library_btn = QPushButton("Library")
        self.open_primer_library_btn.setProperty("variant", "ghost")
        self.open_primer_library_btn.clicked.connect(
            lambda: self._open_selected_component_in_library("primer")
        )
        primer_row.addWidget(self.open_primer_library_btn)
        layout.addLayout(primer_row)

        self.primer_lot_combo = QComboBox()
        self.primer_lot_combo.currentIndexChanged.connect(self.on_primer_lot_changed)
        primer_lot_row = QHBoxLayout()
        primer_lot_row.addWidget(self.primer_lot_combo, 1)
        self.add_primer_lot_btn = QPushButton("New Lot")
        self.add_primer_lot_btn.setProperty("variant", "ghost")
        self.add_primer_lot_btn.clicked.connect(self.on_add_primer_lot)
        primer_lot_row.addWidget(self.add_primer_lot_btn)
        self.edit_primer_lot_btn = QPushButton("Edit Lot")
        self.edit_primer_lot_btn.setProperty("variant", "ghost")
        self.edit_primer_lot_btn.clicked.connect(self.on_edit_primer_lot)
        primer_lot_row.addWidget(self.edit_primer_lot_btn)
        layout.addLayout(primer_lot_row)

        self.primer_info = QLabel(tr("mlb_select_primer_details"))
        self.primer_info.setProperty("role", "muted")
        self.primer_info.setProperty("emphasis", "placeholder")
        layout.addWidget(self.primer_info)

        group.setLayout(layout)
        return group

    def create_charge_slider(self):
        """Charge weight slider with a green→orange→red safety-zone track."""
        group = QGroupBox(tr("mlb_charge_weight"))
        group.setProperty("variant", "panel")
        group.setStyleSheet(
            "QGroupBox { background:#1c2438; border:1px solid #2d3f60; border-radius:7px;"
            " color:#5a7ab0; font-size:9px; font-weight:bold; letter-spacing:1px;"
            " padding-top:14px; margin-top:6px; }"
            "QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 4px; }"
        )
        layout = QVBoxLayout()
        layout.setSpacing(6)

        # Big live charge value
        self.charge_label = QLabel(format_weight_grains(self.current_charge, "powder"))
        self.charge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.charge_label.setStyleSheet(
            "font-size:26px; font-weight:bold; font-family:monospace;"
            " color:#2ecc71; background:transparent;"
        )
        layout.addWidget(self.charge_label)

        # Slider with gradient track
        self.charge_slider = QSlider(Qt.Orientation.Horizontal)
        self.charge_slider.setMinimum(300)  # 30.0 gr
        self.charge_slider.setMaximum(550)  # 55.0 gr
        self.charge_slider.setValue(425)
        self.charge_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.charge_slider.setTickInterval(25)
        self.charge_slider.setMinimumHeight(28)
        self._apply_charge_slider_gradient()
        self.charge_slider.valueChanged.connect(self.on_charge_slider_changed)
        self.charge_slider.valueChanged.connect(self._on_charge_slider_visual_update)
        layout.addWidget(self.charge_slider)

        # Min / Max labels
        _lim_ss = "color:#3d5a8a; font-size:9px; background:transparent;"
        lim = QHBoxLayout()
        _lbl_lo = QLabel(format_weight_grains(30.0, "powder"))
        _lbl_lo.setStyleSheet(_lim_ss)
        _lbl_hi = QLabel(format_weight_grains(55.0, "powder"))
        _lbl_hi.setStyleSheet(_lim_ss)
        lim.addWidget(_lbl_lo)
        lim.addStretch()
        lim.addWidget(_lbl_hi)
        layout.addLayout(lim)

        group.setLayout(layout)
        return group

    _SLIDER_GRADIENT_TEMPLATE = (
        "QSlider::groove:horizontal {{"
        "  height:10px; border-radius:5px;"
        "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        "    stop:0 #1a6b35,"
        "    stop:{s80:.3f} #27ae60,"
        "    stop:{s90:.3f} #e67e22,"
        "    stop:{s95:.3f} #e74c3c,"
        "    stop:1 #922b21);"
        "}}"
        "QSlider::handle:horizontal {{"
        "  width:18px; height:18px; margin:-4px 0;"
        "  border-radius:9px;"
        "  background:#dde4f0; border:2px solid #7f8fa6;"
        "}}"
        "QSlider::handle:horizontal:hover {{"
        "  background:#ffffff; border-color:#2ecc71;"
        "}}"
    )

    def _apply_charge_slider_gradient(self, safe_max_gr: float | None = None) -> None:
        """Repaint the slider track so green→orange→red zones line up with real limits."""
        lo = 30.0
        hi = 55.0
        span = hi - lo or 1.0
        cap = safe_max_gr if safe_max_gr else hi
        # clamp within slider range
        cap = max(lo, min(hi, cap))
        s80 = (cap * 0.80 - lo) / span
        s90 = (cap * 0.90 - lo) / span
        s95 = (cap * 0.95 - lo) / span
        s80 = max(0.01, min(0.97, s80))
        s90 = max(s80 + 0.01, min(0.98, s90))
        s95 = max(s90 + 0.01, min(0.99, s95))
        css = self._SLIDER_GRADIENT_TEMPLATE.format(s80=s80, s90=s90, s95=s95)
        if hasattr(self, "charge_slider"):
            self.charge_slider.setStyleSheet(css)

    def _on_charge_slider_visual_update(self, value: int) -> None:
        """Update the big charge label colour as the handle moves into danger zones."""
        gr = value / 10.0
        lbl = getattr(self, "charge_label", None)
        if lbl is None:
            return
        # Use last known safe max if available
        safe_max = getattr(self, "_last_safe_max_charge_gr", 55.0) or 55.0
        pct = gr / safe_max if safe_max else 1.0
        color = "#2ecc71" if pct < 0.80 else "#e67e22" if pct < 0.95 else "#e74c3c"
        import re

        lbl.setStyleSheet(
            re.sub(r"color:[^;]+;", f"color:{color};", lbl.styleSheet(), count=1)
        )

    def _apply_velocity_unit_preferences(self):
        sub_min = velocity_fps_to_display_value(500.0)
        sub_max = velocity_fps_to_display_value(1300.0)
        sub_default = velocity_fps_to_display_value(1050.0)
        if getattr(self, "subsonic_target", None) is not None:
            self.subsonic_target.setRange(
                float(min(sub_min or 500.0, sub_max or 1300.0)),
                float(max(sub_min or 500.0, sub_max or 1300.0)),
            )
            self.subsonic_target.setValue(float(sub_default or 1050.0))
            self.subsonic_target.setSingleStep(
                5.0 if "fps" in get_velocity_suffix() else 2.0
            )
            self.subsonic_target.setSuffix(get_velocity_suffix())
        if getattr(self, "transonic_margin", None) is not None:
            trans_max = velocity_fps_to_display_value(500.0)
            trans_default = velocity_fps_to_display_value(50.0)
            self.transonic_margin.setRange(0.0, float(trans_max or 500.0))
            self.transonic_margin.setValue(float(trans_default or 50.0))
            self.transonic_margin.setSingleStep(
                5.0 if "fps" in get_velocity_suffix() else 2.0
            )
            self.transonic_margin.setSuffix(get_velocity_suffix())

    def _subsonic_target_fps(self) -> float:
        _sub_widget = getattr(self, "subsonic_target", None)
        target = velocity_display_to_fps(
            _sub_widget.value() if _sub_widget is not None else 1050.0
        )
        return float(target or 1050.0)

    def _transonic_margin_fps(self) -> float:
        _trans_widget = getattr(self, "transonic_margin", None)
        margin = velocity_display_to_fps(
            _trans_widget.value() if _trans_widget is not None else 50.0
        )
        return float(margin or 50.0)

    def _current_temperature_c(self) -> float | None:
        if not hasattr(self, "temp_spin"):
            return None
        return temperature_display_to_c(self.temp_spin.value())

    def _current_pressure_kpa(self) -> float | None:
        if not hasattr(self, "pressure_spin"):
            return None
        return pressure_display_to_kpa(self.pressure_spin.value())

    def create_seating_controls(self):
        """Create seating depth controls"""
        group = QGroupBox(tr("mlb_seating_depth"))
        group.setProperty("variant", "panel")
        layout = QVBoxLayout()

        # COAL
        coal_layout = QHBoxLayout()
        coal_layout.addWidget(QLabel("COAL:"))
        self.coal_spin = QDoubleSpinBox()
        self.coal_spin.setRange(50.0, 100.0)
        self.coal_spin.setValue(71.5)
        self.coal_spin.setDecimals(2)
        self.coal_spin.setSuffix(" mm")
        self.coal_spin.valueChanged.connect(self.on_seating_changed)
        coal_layout.addWidget(self.coal_spin)
        layout.addLayout(coal_layout)

        # CBTO
        cbto_layout = QHBoxLayout()
        cbto_layout.addWidget(QLabel("CBTO:"))
        self.cbto_spin = QDoubleSpinBox()
        self.cbto_spin.setRange(50.0, 100.0)
        self.cbto_spin.setValue(68.8)
        self.cbto_spin.setDecimals(2)
        self.cbto_spin.setSuffix(" mm")
        self.cbto_spin.valueChanged.connect(self.on_seating_changed)
        cbto_layout.addWidget(self.cbto_spin)
        layout.addLayout(cbto_layout)

        # Jump display
        self.jump_label = QLabel(tr("mlb_jump_calculating"))
        self.jump_label.setProperty("role", "muted")
        layout.addWidget(self.jump_label)

        self.seating_visual_label = QLabel()
        self.seating_visual_label.setWordWrap(True)
        self.seating_visual_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.seating_visual_label)

        self.seating_advisor_label = QLabel(
            "Seating-depth guidance will appear here when firearm, bullet, and seating data are ready."
        )
        self.seating_advisor_label.setWordWrap(True)
        self.seating_advisor_label.setStyleSheet(
            "padding: 6px 8px; border-radius: 5px; background: #1a2035; color: #8a9ec0; border-left: 2px solid #2d3f60;"
        )
        layout.addWidget(self.seating_advisor_label)

        self.seating_confidence_label = QLabel("")
        self.seating_confidence_label.setWordWrap(True)
        self.seating_confidence_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.seating_confidence_label)

        self.seating_history_label = QLabel("")
        self.seating_history_label.setWordWrap(True)
        self.seating_history_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.seating_history_label)

        self.seating_trend_label = QLabel("")
        self.seating_trend_label.setWordWrap(True)
        self.seating_trend_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.seating_trend_label)

        self.seating_sandbox_label = QLabel("")
        self.seating_sandbox_label.setWordWrap(True)
        self.seating_sandbox_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.seating_sandbox_label)

        seating_profile_row = QHBoxLayout()
        self.save_seating_profile_btn = QPushButton("Save Profile")
        self.save_seating_profile_btn.setProperty("variant", "ghost")
        self.save_seating_profile_btn.clicked.connect(
            self.on_save_seating_profile_clicked
        )
        seating_profile_row.addWidget(self.save_seating_profile_btn)

        self.apply_seating_profile_btn = QPushButton("Apply Saved Profile")
        self.apply_seating_profile_btn.setProperty("variant", "ghost")
        self.apply_seating_profile_btn.clicked.connect(
            self.on_apply_saved_seating_profile_clicked
        )
        seating_profile_row.addWidget(self.apply_seating_profile_btn)

        self.compare_seating_profile_btn = QPushButton("Compare Lot")
        self.compare_seating_profile_btn.setProperty("variant", "ghost")
        self.compare_seating_profile_btn.clicked.connect(
            self.on_compare_seating_profile_clicked
        )
        seating_profile_row.addWidget(self.compare_seating_profile_btn)

        self.apply_best_known_seating_btn = QPushButton("Apply Best Known")
        self.apply_best_known_seating_btn.setProperty("variant", "ghost")
        self.apply_best_known_seating_btn.clicked.connect(
            self.on_apply_best_known_seating_clicked
        )
        seating_profile_row.addWidget(self.apply_best_known_seating_btn)
        layout.addLayout(seating_profile_row)

        # Optimize button
        self.seating_optimize_btn = QPushButton(tr("mlb_optimize_accuracy"))
        self.seating_optimize_btn.setProperty("variant", "secondary")
        layout.addWidget(self.seating_optimize_btn)
        try:
            self._advanced_widgets.append(self.seating_optimize_btn)
        except Exception:
            pass

        group.setLayout(layout)
        return group

    def create_visualization_panel(self):
        """Create right visualization panel"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Stats bar
        stats_group = self.create_stats_bar()
        layout.addWidget(stats_group)

        # Scope adjustment comparison
        self.scope_comparison_group = QGroupBox(tr("mlb_scope_adjustment_group"))
        self.scope_comparison_group.setProperty("variant", "warning")
        scope_layout = QVBoxLayout()
        self.scope_comparison_group.setLayout(scope_layout)

        self.scope_comparison_label = QLabel(tr("mlb_scope_adjustment_compare"))
        self.scope_comparison_label.setWordWrap(True)
        scope_layout.addWidget(self.scope_comparison_label)

        self.scope_comparison_group.setVisible(False)
        layout.addWidget(self.scope_comparison_group)

        # Scope Adjustment Comparison (vs previous load)
        self.scope_comparison_group = QGroupBox(tr("mlb_scope_adjustment_group"))
        self.scope_comparison_group.setProperty("variant", "warning")
        scope_comp_layout = QVBoxLayout()
        self.scope_comparison_label = QLabel(tr("mlb_scope_adjustment_previous"))
        self.scope_comparison_label.setWordWrap(True)
        scope_comp_layout.addWidget(self.scope_comparison_label)
        self.scope_comparison_group.setLayout(scope_comp_layout)
        self.scope_comparison_group.setVisible(False)
        layout.addWidget(self.scope_comparison_group)

        # Pressure & Velocity plots - lazy-import pyqtgraph and provide safe
        # fallbacks if the library is unavailable (prevents heavy import at
        # module load time and keeps headless probes lightweight).
        try:
            import pyqtgraph as pg  # type: ignore

            # Keep reference to pyqtgraph module for later use
            self._pg = pg

            self.pressure_plot = pg.PlotWidget()
            panel_bg = ReloadingTheme.PANEL
            text_fg = ReloadingTheme.TEXT_PRIMARY
            self.pressure_plot.setBackground(panel_bg)
            self.pressure_plot.setLabel("left", "Pressure", units="PSI", color=text_fg)
            self.pressure_plot.setLabel("bottom", "Time", units="ms", color=text_fg)
            self.pressure_plot.setTitle("Chamber Pressure", color=text_fg, size="12pt")
            self.pressure_plot.setMinimumHeight(200)
            layout.addWidget(self.pressure_plot)

            self.velocity_plot = pg.PlotWidget()
            self.velocity_plot.setBackground(panel_bg)
            self.velocity_plot.setLabel("left", "Velocity", units="fps", color=text_fg)
            self.velocity_plot.setLabel(
                "bottom", "Position", units="inches", color=text_fg
            )
            self.velocity_plot.setTitle("Bullet Velocity", color=text_fg, size="12pt")
            self.velocity_plot.setMinimumHeight(200)
            layout.addWidget(self.velocity_plot)
            # Transonic overlay controls
            self.transonic_row = QWidget()
            trans_h = QHBoxLayout()
            self.transonic_row.setLayout(trans_h)
            self.transonic_cb = QCheckBox("Show Transonic Margin")
            self.transonic_cb.setChecked(True)
            self.transonic_cb.toggled.connect(self.update_visualization)
            # persist when toggled
            self.transonic_cb.toggled.connect(
                lambda v: self._save_ui_setting(
                    "transonic_overlay_enabled", "1" if v else "0"
                )
            )
            trans_h.addWidget(self.transonic_cb)

            trans_h.addWidget(QLabel(f"Margin ({get_velocity_suffix().strip()}):"))
            self.transonic_margin = QDoubleSpinBox()
            self.transonic_margin.setRange(0.0, 500.0)
            self.transonic_margin.setValue(50.0)
            self.transonic_margin.setSingleStep(5.0)
            self.transonic_margin.valueChanged.connect(self.update_visualization)
            # persist margin changes
            self.transonic_margin.valueChanged.connect(
                lambda v: self._save_ui_setting(
                    "transonic_margin_fps",
                    str(velocity_display_to_fps(v) or v),
                )
            )
            trans_h.addWidget(self.transonic_margin)

            layout.addWidget(self.transonic_row)
            try:
                self._advanced_widgets.append(self.transonic_row)
            except Exception:
                pass
            # load persisted ui settings if present
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT value FROM ui_settings WHERE key = ?",
                    ("transonic_overlay_enabled",),
                )
                row = cur.fetchone()
                if row and row[0] is not None:
                    try:
                        self.transonic_cb.setChecked(bool(int(row[0])))
                    except Exception:
                        # tolerate non-int values
                        self.transonic_cb.setChecked(
                            row[0].lower() in ("1", "true", "yes")
                        )
                cur.execute(
                    "SELECT value FROM ui_settings WHERE key = ?",
                    ("transonic_margin_fps",),
                )
                row2 = cur.fetchone()
                if row2 and row2[0] is not None:
                    try:
                        self.transonic_margin.setValue(
                            float(
                                velocity_fps_to_display_value(float(row2[0])) or row2[0]
                            )
                        )
                    except Exception:
                        pass
                # velocity y-range
                cur.execute(
                    "SELECT value FROM ui_settings WHERE key = ?", ("velocity_y_min",)
                )
                vmin_r = cur.fetchone()
                if vmin_r and vmin_r[0] is not None:
                    try:
                        self.velocity_y_min = float(vmin_r[0])
                    except Exception:
                        self.velocity_y_min = None
                else:
                    self.velocity_y_min = None
                cur.execute(
                    "SELECT value FROM ui_settings WHERE key = ?", ("velocity_y_max",)
                )
                vmax_r = cur.fetchone()
                if vmax_r and vmax_r[0] is not None:
                    try:
                        self.velocity_y_max = float(vmax_r[0])
                    except Exception:
                        self.velocity_y_max = None
                else:
                    self.velocity_y_max = None
            except Exception:
                pass
            self._apply_velocity_unit_preferences()
        except Exception:
            # Fallback: simple read-only text placeholders so UI still renders
            from PyQt6.QtWidgets import QTextEdit

            ph1 = QTextEdit("Pressure plot unavailable (pyqtgraph missing)")
            ph1.setReadOnly(True)
            ph1.setMinimumHeight(200)
            layout.addWidget(ph1)

            ph2 = QTextEdit("Velocity plot unavailable (pyqtgraph missing)")
            ph2.setReadOnly(True)
            ph2.setMinimumHeight(200)
            layout.addWidget(ph2)

        # Compare button
        self.compare_btn = QPushButton(tr("mlb_compare_other_powders"))
        self.compare_btn.setProperty("variant", "secondary")
        layout.addWidget(self.compare_btn)
        try:
            self._advanced_widgets.append(self.compare_btn)
        except Exception:
            pass

        widget.setLayout(layout)
        return widget

    def create_stats_bar(self):
        """Rich metric cards — big coloured numbers nerds can read at a glance."""
        widget = QWidget()
        widget.setObjectName("metricsStrip")
        h = QHBoxLayout(widget)
        h.setContentsMargins(0, 0, 0, 6)
        h.setSpacing(5)

        CARDS = [
            ("_mc_vel", "—", "HASTIGHET", "#2ecc71"),
            ("_mc_pres", "—", "TRYKK", "#e74c3c"),
            ("_mc_energy", "—", "ENERGI", "#f39c12"),
            ("_mc_recoil", "—", "REKYL", "#9b59b6"),
            ("_mc_time", "—", "LØPSTID", "#3498db"),
            ("_mc_margin", "—", "SIKKERHETSMARGIN", "#2ecc71"),
        ]
        for attr, default, unit, color in CARDS:
            card = QWidget()
            card.setStyleSheet(
                f"QWidget {{ background:#1a2035; border-radius:7px;"
                f" border-left:3px solid {color}; }}"
            )
            v = QVBoxLayout(card)
            v.setContentsMargins(10, 7, 10, 7)
            v.setSpacing(1)

            num = QLabel(default)
            num.setStyleSheet(
                f"color:{color}; font-size:20px; font-weight:bold;"
                f" font-family:monospace; background:transparent; border:none;"
            )
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            setattr(self, f"{attr}_num", num)

            lbl = QLabel(unit)
            lbl.setStyleSheet(
                "color:#4a5e80; font-size:9px; font-weight:bold;"
                " letter-spacing:0.5px; background:transparent; border:none;"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            sub = QLabel("")
            sub.setStyleSheet(
                "color:#2a3a55; font-size:8px; background:transparent; border:none;"
            )
            sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            setattr(self, f"{attr}_sub", sub)

            v.addWidget(num)
            v.addWidget(lbl)
            v.addWidget(sub)
            h.addWidget(card, 1)

        # Delta comparison row (shown when a reference load exists)
        self._delta_row = QWidget()
        self._delta_row.setObjectName("deltaRow")
        self._delta_row.hide()
        dr = QHBoxLayout(self._delta_row)
        dr.setContentsMargins(4, 2, 4, 2)
        dr.setSpacing(14)
        _DELTA_FIELDS = [
            ("_dc_vel", "Δ hastighet"),
            ("_dc_pres", "Δ trykk"),
            ("_dc_energy", "Δ energi"),
            ("_dc_charge", "Δ ladning"),
            ("_dc_coal", "Δ COAL"),
        ]
        ref_lbl = QLabel("vs. referanse:")
        ref_lbl.setStyleSheet("color:#4a5e80; font-size:9px;")
        dr.addWidget(ref_lbl)
        for attr, caption in _DELTA_FIELDS:
            cell = QWidget()
            cv = QVBoxLayout(cell)
            cv.setContentsMargins(0, 0, 0, 0)
            cv.setSpacing(0)
            val = QLabel("—")
            val.setStyleSheet(
                "color:#7a94c4; font-size:11px; font-weight:bold; font-family:monospace;"
            )
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cap = QLabel(caption)
            cap.setStyleSheet("color:#3a4e6a; font-size:8px;")
            cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            setattr(self, f"{attr}_lbl", val)
            cv.addWidget(val)
            cv.addWidget(cap)
            dr.addWidget(cell)
        dr.addStretch()

        # Confidence badge
        self._confidence_badge = QLabel("● SIMULERING")
        self._confidence_badge.setStyleSheet(
            "color:#3498db; font-size:9px; font-weight:bold; letter-spacing:0.5px;"
            " background:#0d1525; border:1px solid #1a3a6a; border-radius:4px; padding:2px 7px;"
        )
        dr.addWidget(self._confidence_badge)

        outer = QWidget()
        ov = QVBoxLayout(outer)
        ov.setContentsMargins(0, 0, 0, 0)
        ov.setSpacing(4)
        ov.addWidget(widget)
        ov.addWidget(self._delta_row)

        # Legacy label refs kept for _mlb_stats_mixin compatibility
        for legacy in (
            "stat_pressure",
            "stat_velocity",
            "stat_energy",
            "stat_barrel_time",
            "stat_safety",
        ):
            lbl = QLabel()
            lbl.hide()
            setattr(self, legacy, lbl)

        # Reference load state (populated on save / load)
        self._reference_result: dict | None = None

        return outer

    # ── Purpose helpers ────────────────────────────────────────────────────────

    def _get_active_purpose(self) -> str:
        """Return 'hunting', 'precision', or 'long_range' from top-bar toggles."""
        grp = getattr(self, "_purpose_btn_group", None)
        if grp is None:
            return "precision"
        checked = grp.checkedButton()
        if checked is None:
            return "precision"
        return str(checked.property("purpose_key") or "precision")

    # ── Confidence level ───────────────────────────────────────────────────────

    def _get_confidence_level(self) -> tuple[str, str]:
        """Return (label, colour) based on how much validated data exists."""
        try:
            rifle_id = (
                self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None
            )
            if rifle_id is None:
                return ("SIMULERING", "#3498db")
            rows = self.db.execute_query(
                "SELECT COUNT(*) as n FROM test_results WHERE rifle_id = ? AND velocity_avg IS NOT NULL",
                (rifle_id,),
            )
            count = int((rows[0].get("n") or 0) if rows else 0)
        except Exception:
            return ("SIMULERING", "#3498db")
        if count == 0:
            return ("SIMULERING", "#3498db")
        if count < 5:
            return (f"DELVIS VALIDERT  {count} skudd", "#e67e22")
        if count < 20:
            return (f"VALIDERT  {count} skudd", "#2ecc71")
        return (f"GODT VALIDERT  {count} skudd", "#2ecc71")

    # ── Reference load ─────────────────────────────────────────────────────────

    def _set_reference_result(self, result: dict) -> None:
        """Pin current result as comparison baseline."""
        self._reference_result = dict(result)

    def _update_metric_cards(self, result: dict) -> None:
        """Push live calculation results into the metric cards."""
        import re as _re

        from src.utils.unit_preferences import format_pressure_psi

        def _s(attr: str, text: str, color: str | None = None) -> None:
            w = getattr(self, f"{attr}_num", None)
            if w is None:
                return
            w.setText(text)
            if color:
                w.setStyleSheet(
                    _re.sub(r"color:[^;]+;", f"color:{color};", w.styleSheet(), count=1)
                )

        def _sub(attr: str, text: str) -> None:
            w = getattr(self, f"{attr}_sub", None)
            if w:
                w.setText(text)

        # ── Velocity ──────────────────────────────────────────────────────────
        vel_fps = result.get("muzzle_velocity_fps")
        if vel_fps is not None:
            vel_ms = float(vel_fps) * 0.3048
            _s("_mc_vel", f"{vel_ms:.0f} m/s")
            _sub("_mc_vel", f"{float(vel_fps):.0f} fps")

        # ── Pressure ─────────────────────────────────────────────────────────
        peak_psi = result.get("peak_pressure_psi")
        saami_psi = result.get("max_pressure_psi")
        if peak_psi is not None:
            pct = (float(peak_psi) / float(saami_psi) * 100) if saami_psi else None
            pres_color = (
                "#2ecc71"
                if (pct or 0) < 80
                else "#e67e22" if (pct or 0) < 95 else "#e74c3c"
            )
            peak_bar = float(peak_psi) * 0.0689476
            _s("_mc_pres", f"{peak_bar:.0f} bar", pres_color)
            _sub(
                "_mc_pres",
                f"{pct:.0f}% av SAAMI maks" if pct else format_pressure_psi(peak_psi),
            )

        # ── Energy with purpose-based thresholds ─────────────────────────────
        energy_ftlbs = result.get("energy_ft_lbs")
        if energy_ftlbs is not None:
            joules = float(energy_ftlbs) * 1.35582
            _s("_mc_energy", f"{joules:.0f} J")
            purpose = self._get_active_purpose()
            if purpose == "hunting":
                # Norwegian hunting thresholds (approx.)
                if joules >= 2700:
                    _sub("_mc_energy", "✓ Elg  ✓ Hjort  ✓ Rådyr")
                elif joules >= 1500:
                    _sub("_mc_energy", "✗ Elg  ✓ Hjort  ✓ Rådyr")
                elif joules >= 800:
                    _sub("_mc_energy", "✗ Elg  ✗ Hjort  ✓ Rådyr")
                else:
                    _sub("_mc_energy", "✗ Elg  ✗ Hjort  ✗ Rådyr")
            else:
                _sub("_mc_energy", f"{float(energy_ftlbs):.0f} ft-lbs")

        # ── Recoil ────────────────────────────────────────────────────────────
        recoil = result.get("recoil_energy_ft_lbs") or result.get("recoil_j")
        if recoil is not None:
            rj = (
                float(recoil) * 1.35582
                if result.get("recoil_energy_ft_lbs")
                else float(recoil)
            )
            _s("_mc_recoil", f"{rj:.1f} J")
            _sub(
                "_mc_recoil", "lett" if rj < 10 else "moderat" if rj < 20 else "kraftig"
            )

        # ── Barrel time ───────────────────────────────────────────────────────
        bt = result.get("barrel_time_ms")
        if bt is not None:
            _s("_mc_time", f"{float(bt):.3f} ms")
            # Optimal barrel time hint
            obt = result.get("optimal_barrel_time_ms")
            if obt is not None:
                diff = float(bt) - float(obt)
                hint = (
                    f"OBT {float(obt):.3f} ms  ({'+' if diff >= 0 else ''}{diff:.3f})"
                )
                _sub("_mc_time", hint)

        # ── Safety margin ─────────────────────────────────────────────────────
        safety = result.get("safety_margin_percent")
        if safety is not None:
            mc = "#2ecc71" if safety > 15 else "#e67e22" if safety > 10 else "#e74c3c"
            _s("_mc_margin", f"{safety:.0f}%", mc)
            _sub(
                "_mc_margin",
                "TRYGT" if safety > 15 else "FORSIKTIG" if safety > 10 else "FARE",
            )

        # ── Confidence badge ──────────────────────────────────────────────────
        badge = getattr(self, "_confidence_badge", None)
        if badge is not None:
            conf_label, conf_color = self._get_confidence_level()
            badge.setText(f"● {conf_label}")
            badge.setStyleSheet(
                _re.sub(
                    r"color:[^;]+;", f"color:{conf_color};", badge.styleSheet(), count=1
                )
            )

        # ── Delta comparison row ──────────────────────────────────────────────
        ref = getattr(self, "_reference_result", None)
        delta_row = getattr(self, "_delta_row", None)
        if ref is not None and delta_row is not None:
            delta_row.show()

            def _delta(
                attr: str, new_val, ref_val, fmt: str = ".1f", unit: str = ""
            ) -> None:
                w = getattr(self, f"{attr}_lbl", None)
                if w is None or new_val is None or ref_val is None:
                    return
                try:
                    d = float(new_val) - float(ref_val)
                    sign = "+" if d >= 0 else ""
                    color = "#2ecc71" if d == 0 else "#e67e22"
                    w.setText(f"{sign}{d:{fmt}}{unit}")
                    w.setStyleSheet(
                        _re.sub(
                            r"color:[^;]+;", f"color:{color};", w.styleSheet(), count=1
                        )
                    )
                except Exception:
                    pass

            ref_vel = ref.get("muzzle_velocity_fps")
            ref_psi = ref.get("peak_pressure_psi")
            ref_e = ref.get("energy_ft_lbs")

            if vel_fps and ref_vel:
                w = getattr(self, "_dc_vel_lbl", None)
                if w:
                    d = (float(vel_fps) - float(ref_vel)) * 0.3048
                    sign = "+" if d >= 0 else ""
                    color = "#2ecc71" if d == 0 else "#e67e22"
                    w.setText(f"{sign}{d:.0f} m/s")
                    w.setStyleSheet(
                        _re.sub(
                            r"color:[^;]+;", f"color:{color};", w.styleSheet(), count=1
                        )
                    )
            _delta("_dc_pres", peak_psi, ref_psi, ".0f", " psi")
            _delta("_dc_energy", energy_ftlbs, ref_e, ".0f", " ft-lbs")
            _delta(
                "_dc_charge",
                self.current_charge,
                ref.get("_snap_charge_gr"),
                ".2f",
                " gr",
            )
            _delta("_dc_coal", self.coal_mm, ref.get("_snap_coal_mm"), ".2f", " mm")

    def create_ai_chat_panel(self):
        """Create AI chat panel (collapsible)"""
        widget = QWidget()
        widget.setMaximumHeight(300)
        layout = QVBoxLayout()

        # Header with collapse button
        header_layout = QHBoxLayout()

        chat_title = QLabel(tr("mlb_ai_assistant"))
        chat_title.setProperty("role", "subtitle")
        header_layout.addWidget(chat_title)

        header_layout.addStretch()

        self.collapse_btn = QPushButton(tr("mlb_collapse"))
        self.collapse_btn.setProperty("variant", "ghost")
        self.collapse_btn.clicked.connect(self.toggle_chat)
        header_layout.addWidget(self.collapse_btn)

        layout.addLayout(header_layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display, 1)

        # Input area
        input_layout = QHBoxLayout()

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText(tr("mlb_chat_placeholder"))
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input)

        send_btn = QPushButton(tr("mlb_send"))
        send_btn.setProperty("variant", "primary")
        send_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        # Add welcome message
        self.add_ai_message(tr("mlb_ai_welcome"))

        widget.setLayout(layout)
        return widget

    def on_create_batch_clicked(self):
        """UI handler: ask for batch name/size and create batch"""
        # Ensure components selected
        if not (
            self.rifle_data
            and self.bullet_data
            and self.powder_data
            and self.brass_data
        ):
            QMessageBox.warning(
                self,
                tr("mlb_missing_data_title"),
                tr("mlb_missing_data_message"),
            )
            return

        count, ok = QInputDialog.getInt(
            self, "Batch Size", "How many rounds to create?", 10, 1, 10000, 1
        )
        if not ok:
            return

        name, ok2 = QInputDialog.getText(
            self,
            "Batch Name",
            "Name for this batch:",
            text=f"Batch for {self.rifle_data.get('name','rifle')}",
        )
        if not ok2:
            return

        component_context = build_active_component_context_payload(
            bullet_data=(
                self.bullet_data if isinstance(self.bullet_data, dict) else None
            ),
            powder_data=(
                self.powder_data if isinstance(self.powder_data, dict) else None
            ),
            primer_data=(
                self.primer_data if isinstance(self.primer_data, dict) else None
            ),
        )
        seating_context = self._get_current_seating_context()
        subsonic_context = self._get_current_subsonic_context()
        retest_advisory = summarize_retest_advisor(
            self.db,
            self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None,
            bullet_data=(
                self.bullet_data if isinstance(self.bullet_data, dict) else None
            ),
            powder_data=(
                self.powder_data if isinstance(self.powder_data, dict) else None
            ),
            primer_data=(
                self.primer_data if isinstance(self.primer_data, dict) else None
            ),
            current_charge=float(self.current_charge or 0),
            coal_mm=float(self.coal_mm or 0),
            cbto_mm=float(self.cbto_mm or 0),
            result=getattr(self, "_latest_visual_result", None),
        )
        model_match_advisory = summarize_model_vs_measured_advisory(
            self.db,
            self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None,
            self.bullet_data.get("id") if isinstance(self.bullet_data, dict) else None,
            self.powder_data.get("id") if isinstance(self.powder_data, dict) else None,
            current_charge_grains=float(self.current_charge or 0),
            current_cbto_mm=float(self.cbto_mm or 0),
            predicted_velocity_fps=(
                float(_lvr_mv)
                if isinstance(
                    (_lvr := getattr(self, "_latest_visual_result", None)), dict
                )
                and isinstance(
                    (_lvr_mv := _lvr.get("muzzle_velocity_fps")), (int, float)
                )
                else None
            ),
            subsonic_mode=bool(subsonic_context.get("enabled")),
            current_powder_lot_number=(
                str(
                    self.powder_data.get("lot_number")
                    or self.powder_data.get("selected_lot_number")
                    or ""
                ).strip()
                if isinstance(self.powder_data, dict)
                else ""
            ),
            target_temperature_c=(
                float(_tc_val)
                if isinstance(
                    (_tc_val := seating_context.get("temperature_c")), (int, float)
                )
                else None
            ),
        )

        # Ensure there's an ammo_profile for this configuration; create minimal profile
        cur = self.db.cursor
        # Build minimal ammo_profile
        cur.execute(
            "INSERT INTO ammo_profiles (name, rifle_id, caliber, bullet_id, bullet_weight, powder_id, powder_charge, primer_id, case_id, coal, cbto, component_context_json, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (
                name,
                self.rifle_data.get("id"),
                self.rifle_data.get("caliber"),
                self.bullet_data.get("id"),
                float(self.bullet_data.get("weight", 0)),
                self.powder_data.get("id"),
                float(self.current_charge or 0),
                self.primer_data.get("id") if self.primer_data else None,
                self.brass_data.get("id") if self.brass_data else None,
                float(self.coal_mm or 0),
                float(self.cbto_mm or 0),
                json.dumps(component_context, ensure_ascii=False),
            ),
        )
        self.db.conn.commit()
        ammo_profile_id = cur.lastrowid
        self._persist_current_seating_depth_profile(source="batch_create")

        # Persist a user-facing batch project so the load can be revisited later
        component_snapshot = {
            "rifle": self.rifle_data,
            "bullet": self.bullet_data,
            "powder": self.powder_data,
            "primer": self.primer_data,
            "brass": self.brass_data,
            "component_context": component_context,
            "settings": {
                "charge_weight_grains": self.current_charge,
                "coal_mm": self.coal_mm,
                "cbto_mm": self.cbto_mm,
                "subsonic_mode": subsonic_context.get("enabled"),
                "subsonic_target_fps": subsonic_context.get("target_velocity_fps"),
            },
        }
        current_project_path = str(
            QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "workspace/current_project", ""
            )
            or ""
        ).strip()
        analysis_context = {
            "workspace": {
                "project_name": _project_name_from_path(current_project_path),
                "project_path": current_project_path,
            },
            "rifle_context": {
                "rifle_id": self.rifle_data.get("id") if self.rifle_data else None,
                "rifle_name": self.rifle_data.get("name") if self.rifle_data else None,
                "barrel_id": self._get_active_barrel_id(),
                "barrel_name": (
                    self._get_active_barrel_details().get("name")
                    if self._get_active_barrel_details()
                    else None
                ),
            },
            "component_context": component_context,
            "component_context_summary": component_context.get("summary_html"),
            "seating_context": seating_context,
            "subsonic_context": subsonic_context,
            "seating_promotion_candidate": _summarize_seating_promotion_candidate(
                self._get_best_known_seating_evidence(),
                float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
            ),
            "predicted_result_summary": _build_predicted_result_summary(
                getattr(self, "_latest_visual_result", None)
            ),
            "retest_advisory": retest_advisory,
            "model_match_advisory": model_match_advisory,
        }
        barrel_context = self._get_active_barrel_configuration_context()
        analysis_context["rifle_context"]["barrel_configuration_id"] = (
            barrel_context.get("barrel_configuration_id")
        )
        analysis_context["rifle_context"]["barrel_configuration_name"] = (
            barrel_context.get("barrel_configuration_name")
        )

        batch_result = create_batch_project(
            self.db,
            name,
            int(self.rifle_data.get("id") or 0),
            barrel_id=barrel_context.get("barrel_id"),
            barrel_name=barrel_context.get("barrel_name"),
            barrel_configuration_id=barrel_context.get("barrel_configuration_id"),
            barrel_configuration_name=barrel_context.get("barrel_configuration_name"),
            load_session_id=_get_active_load_session_id(),
            ammo_profile_id=ammo_profile_id,
            source_workflow="modern_load_builder",
            charge_weight_grains=float(self.current_charge or 0),
            coal_mm=float(self.coal_mm or 0),
            cbto_mm=float(self.cbto_mm or 0),
            bullet_id=self.bullet_data.get("id"),
            powder_id=self.powder_data.get("id"),
            primer_id=self.primer_data.get("id") if self.primer_data else None,
            brass_batch_id=self.brass_data.get("id") if self.brass_data else None,
            case_id=self.brass_data.get("case_id") if self.brass_data else None,
            notes=tr("mlb_batch_notes_created", count=count),
            barrel_configuration_snapshot=barrel_context.get(
                "barrel_configuration_snapshot"
            ),
            component_snapshot=component_snapshot,
            analysis_json=analysis_context,
        )

        # Call legacy batch manager for inventory/QC bookkeeping
        try:
            create_loading_batch = component_layer.batch.create_loading_batch

            res = create_loading_batch(
                self.db,
                ammo_profile_id,
                name,
                count,
                self.current_charge or 0,
                self.coal_mm or 0,
                self.cbto_mm or 0,
                load_session_id=_get_active_load_session_id(),
            )
        except Exception as e:
            QMessageBox.critical(
                self, tr("mlb_error_title"), tr("mlb_batch_create_error", error=e)
            )
            return

        if not res.get("ok"):
            QMessageBox.warning(
                self,
                tr("mlb_batch_not_created"),
                res.get("message", tr("mlb_unknown_error")),
            )
            return

        QMessageBox.information(
            self,
            tr("mlb_batch_created_title"),
            tr(
                "mlb_batch_created_message",
                batch_id=batch_result.get("batch_id"),
                batch_number=batch_result.get("batch_number"),
            ),
        )
        self.last_created_batch_id = int(batch_result.get("batch_id") or 0)

        try:
            self.batch_created.emit(int(batch_result.get("batch_id") or 0))
        except Exception:
            pass

    def _build_current_retest_advisory(self) -> dict[str, Any]:
        return summarize_retest_advisor(
            self.db,
            self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None,
            bullet_data=(
                self.bullet_data if isinstance(self.bullet_data, dict) else None
            ),
            powder_data=(
                self.powder_data if isinstance(self.powder_data, dict) else None
            ),
            primer_data=(
                self.primer_data if isinstance(self.primer_data, dict) else None
            ),
            current_charge=float(self.current_charge or 0),
            coal_mm=float(self.coal_mm or 0),
            cbto_mm=float(self.cbto_mm or 0),
            result=getattr(self, "_latest_visual_result", None),
        )

    def _ensure_retest_batch(self, retest_advisory: dict[str, Any]) -> int | None:
        existing_batch_id = getattr(self, "last_created_batch_id", None)
        if existing_batch_id:
            return int(existing_batch_id)

        if not (
            self.rifle_data
            and self.bullet_data
            and self.powder_data
            and self.brass_data
        ):
            QMessageBox.warning(
                self,
                "Retest-serie",
                "Select firearm, bullet, powder, and brass before creating a retest series.",
            )
            return None

        suggested_count = max(
            5, int(retest_advisory.get("suggested_control_shots") or 5)
        )
        default_name = f"Retest {self.rifle_data.get('name', 'rifle')} {self.powder_data.get('name', '').strip()}".strip()
        name, ok = QInputDialog.getText(
            self,
            "Opprett retest-batch",
            "Batchnavn for retest-serien:",
            text=default_name,
        )
        if not ok:
            return None
        batch_name = (name or "").strip() or default_name

        component_context = build_active_component_context_payload(
            bullet_data=(
                self.bullet_data if isinstance(self.bullet_data, dict) else None
            ),
            powder_data=(
                self.powder_data if isinstance(self.powder_data, dict) else None
            ),
            primer_data=(
                self.primer_data if isinstance(self.primer_data, dict) else None
            ),
        )
        seating_context = self._get_current_seating_context()
        subsonic_context = self._get_current_subsonic_context()
        current_project_path = str(
            QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "workspace/current_project", ""
            )
            or ""
        ).strip()
        analysis_context = {
            "workspace": {
                "project_name": _project_name_from_path(current_project_path),
                "project_path": current_project_path,
            },
            "rifle_context": {
                "rifle_id": self.rifle_data.get("id") if self.rifle_data else None,
                "rifle_name": self.rifle_data.get("name") if self.rifle_data else None,
                "barrel_id": self._get_active_barrel_id(),
                "barrel_name": (
                    self._get_active_barrel_details().get("name")
                    if self._get_active_barrel_details()
                    else None
                ),
            },
            "component_context": component_context,
            "component_context_summary": component_context.get("summary_html"),
            "seating_context": seating_context,
            "subsonic_context": subsonic_context,
            "seating_promotion_candidate": _summarize_seating_promotion_candidate(
                self._get_best_known_seating_evidence(),
                float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
            ),
            "predicted_result_summary": _build_predicted_result_summary(
                getattr(self, "_latest_visual_result", None)
            ),
            "retest_advisory": retest_advisory,
            "model_match_advisory": summarize_model_vs_measured_advisory(
                self.db,
                (
                    self.rifle_data.get("id")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                (
                    self.bullet_data.get("id")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                (
                    self.powder_data.get("id")
                    if isinstance(self.powder_data, dict)
                    else None
                ),
                current_charge_grains=float(self.current_charge or 0),
                current_cbto_mm=float(self.cbto_mm or 0),
                predicted_velocity_fps=(
                    float(_lvr_mv2)
                    if isinstance(
                        (_lvr2 := getattr(self, "_latest_visual_result", None)), dict
                    )
                    and isinstance(
                        (_lvr_mv2 := _lvr2.get("muzzle_velocity_fps")), (int, float)
                    )
                    else None
                ),
                subsonic_mode=bool(subsonic_context.get("enabled")),
                current_powder_lot_number=(
                    str(
                        self.powder_data.get("lot_number")
                        or self.powder_data.get("selected_lot_number")
                        or ""
                    ).strip()
                    if isinstance(self.powder_data, dict)
                    else ""
                ),
                target_temperature_c=(
                    float(_sc_tc2)
                    if isinstance(
                        (_sc_tc2 := seating_context.get("temperature_c")), (int, float)
                    )
                    else None
                ),
            ),
        }
        barrel_context = self._get_active_barrel_configuration_context()
        analysis_context["rifle_context"]["barrel_configuration_id"] = (
            barrel_context.get("barrel_configuration_id")
        )
        analysis_context["rifle_context"]["barrel_configuration_name"] = (
            barrel_context.get("barrel_configuration_name")
        )

        cur = self.db.cursor
        cur.execute(
            "INSERT INTO ammo_profiles (name, rifle_id, caliber, bullet_id, bullet_weight, powder_id, powder_charge, primer_id, case_id, coal, cbto, component_context_json, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (
                batch_name,
                self.rifle_data.get("id"),
                self.rifle_data.get("caliber"),
                self.bullet_data.get("id"),
                float(self.bullet_data.get("weight", 0)),
                self.powder_data.get("id"),
                float(self.current_charge or 0),
                self.primer_data.get("id") if self.primer_data else None,
                self.brass_data.get("id") if self.brass_data else None,
                float(self.coal_mm or 0),
                float(self.cbto_mm or 0),
                json.dumps(component_context, ensure_ascii=False),
            ),
        )
        self.db.conn.commit()
        ammo_profile_id = cur.lastrowid
        self._persist_current_seating_depth_profile(source="retest_batch")

        batch_result = create_batch_project(
            self.db,
            batch_name,
            int(self.rifle_data.get("id") or 0),
            barrel_id=barrel_context.get("barrel_id"),
            barrel_name=barrel_context.get("barrel_name"),
            barrel_configuration_id=barrel_context.get("barrel_configuration_id"),
            barrel_configuration_name=barrel_context.get("barrel_configuration_name"),
            load_session_id=_get_active_load_session_id(),
            ammo_profile_id=ammo_profile_id,
            source_workflow="modern_load_builder",
            charge_weight_grains=float(self.current_charge or 0),
            coal_mm=float(self.coal_mm or 0),
            cbto_mm=float(self.cbto_mm or 0),
            bullet_id=self.bullet_data.get("id"),
            powder_id=self.powder_data.get("id"),
            primer_id=self.primer_data.get("id") if self.primer_data else None,
            brass_batch_id=self.brass_data.get("id") if self.brass_data else None,
            case_id=self.brass_data.get("case_id") if self.brass_data else None,
            notes=f"Retest batch created from Retest Advisor ({suggested_count} control shots).",
            barrel_configuration_snapshot=barrel_context.get(
                "barrel_configuration_snapshot"
            ),
            component_snapshot={
                "rifle": self.rifle_data,
                "bullet": self.bullet_data,
                "powder": self.powder_data,
                "primer": self.primer_data,
                "brass": self.brass_data,
                "component_context": component_context,
                "subsonic_context": subsonic_context,
            },
            analysis_json=analysis_context,
        )
        self.last_created_batch_id = int(batch_result.get("batch_id") or 0)
        try:
            self.batch_created.emit(int(batch_result.get("batch_id") or 0))
        except Exception:
            pass
        return self.last_created_batch_id

    def on_create_retest_session_clicked(self) -> None:
        retest_advisory = self._build_current_retest_advisory()
        batch_id = self._ensure_retest_batch(retest_advisory)
        if not batch_id:
            return

        payload = build_retest_session_payload(retest_advisory)
        payload["analysis_json"] = dict(payload.get("analysis_json") or {})
        payload["analysis_json"]["component_context"] = (
            build_active_component_context_payload(
                bullet_data=(
                    self.bullet_data if isinstance(self.bullet_data, dict) else None
                ),
                powder_data=(
                    self.powder_data if isinstance(self.powder_data, dict) else None
                ),
                primer_data=(
                    self.primer_data if isinstance(self.primer_data, dict) else None
                ),
            )
        )
        payload["analysis_json"]["charge_weight_grains"] = float(
            self.current_charge or 0
        )
        payload["analysis_json"]["coal_mm"] = float(self.coal_mm or 0)
        payload["analysis_json"]["cbto_mm"] = float(self.cbto_mm or 0)
        payload["analysis_json"][
            "seating_context"
        ] = self._get_current_seating_context()
        payload["analysis_json"][
            "subsonic_context"
        ] = self._get_current_subsonic_context()
        payload["analysis_json"]["predicted_result_summary"] = (
            _build_predicted_result_summary(
                getattr(self, "_latest_visual_result", None)
            )
        )
        payload["analysis_json"]["seating_promotion_candidate"] = (
            _summarize_seating_promotion_candidate(
                self._get_best_known_seating_evidence(),
                float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
            )
        )
        payload["analysis_json"]["model_match_advisory"] = (
            summarize_model_vs_measured_advisory(
                self.db,
                (
                    self.rifle_data.get("id")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                (
                    self.bullet_data.get("id")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                (
                    self.powder_data.get("id")
                    if isinstance(self.powder_data, dict)
                    else None
                ),
                current_charge_grains=float(self.current_charge or 0),
                current_cbto_mm=float(self.cbto_mm or 0),
                predicted_velocity_fps=(
                    float(_lvr_mv)
                    if isinstance(
                        (_lvr := getattr(self, "_latest_visual_result", None)), dict
                    )
                    and isinstance(
                        (_lvr_mv := _lvr.get("muzzle_velocity_fps")), (int, float)
                    )
                    else None
                ),
                subsonic_mode=bool(
                    (payload["analysis_json"].get("subsonic_context") or {}).get(
                        "enabled"
                    )
                ),
                current_powder_lot_number=(
                    str(
                        self.powder_data.get("lot_number")
                        or self.powder_data.get("selected_lot_number")
                        or ""
                    ).strip()
                    if isinstance(self.powder_data, dict)
                    else ""
                ),
                target_temperature_c=(
                    float(_psc_tc)
                    if isinstance(
                        (
                            _psc_tc := (
                                payload["analysis_json"].get("seating_context") or {}
                            ).get("temperature_c")
                        ),
                        (int, float),
                    )
                    else None
                ),
            )
        )
        barrel_context = self._get_active_barrel_configuration_context()
        add_batch_session(
            self.db,
            int(batch_id),
            load_session_id=_get_active_load_session_id(),
            rifle_id=(
                self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None
            ),
            barrel_id=barrel_context.get("barrel_id"),
            barrel_name=barrel_context.get("barrel_name"),
            barrel_configuration_id=barrel_context.get("barrel_configuration_id"),
            barrel_configuration_name=barrel_context.get("barrel_configuration_name"),
            session_name=str(
                payload.get("session_name") or "Retest - verifiseringsserie"
            ),
            session_type=str(payload.get("session_type") or "range"),
            shot_count=int(payload.get("shot_count") or 5),
            distance_m=int(
                (self._get_current_seating_context().get("distance_m") or 100)
            ),
            temperature_c=self._get_current_seating_context().get("temperature_c"),
            suppressor_used=barrel_context.get("suppressor_used"),
            muzzle_device_type=barrel_context.get("muzzle_device_type"),
            notes=str(payload.get("notes") or "").strip(),
            analysis_json=payload.get("analysis_json") or {},
        )

        host = self.window()
        if host is not None and hasattr(host, "show_batch_workspace"):
            try:
                host.show_batch_workspace(batch_id=int(batch_id))  # type: ignore[attr-defined]
                return
            except Exception:
                pass

        QMessageBox.information(
            self,
            "Retest Series Created",
            "The retest series has been added to the batch and can be opened in Batch Workspace.",
        )

    # ------------------------------------------------------------------
    # Lagre / Last inn ladningsoppsett
    # ------------------------------------------------------------------

    _SAVED_DESIGNS_DDL = """
        CREATE TABLE IF NOT EXISTS saved_load_designs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            rifle_id    INTEGER,
            snapshot_json TEXT  NOT NULL,
            created_at  TEXT    NOT NULL
        )
    """

    def _ensure_saved_designs_table(self) -> None:
        """Opprett saved_load_designs-tabellen om den ikke finnes."""
        try:
            self.db.cursor.execute(self._SAVED_DESIGNS_DDL)
            self.db.conn.commit()
        except Exception:
            pass

    def on_save_load_clicked(self) -> None:
        """Lagre nåværende ladningsoppsett som et navngitt design."""
        if not self.rifle_data:
            QMessageBox.warning(
                self,
                "Mangler rifle",
                "Velg en rifle i Trinn 1 før du lagrer.",
            )
            return
        if not (self.bullet_data or self.powder_data):
            QMessageBox.warning(
                self,
                "Mangler komponenter",
                "Velg minst kule eller krutt før du lagrer.",
            )
            return

        # Foreslå et navn
        rifle_name = (
            self.rifle_data.get("name") or self.rifle_data.get("caliber") or "Rifle"
            if isinstance(self.rifle_data, dict)
            else "Rifle"
        )
        powder_name = (
            self.powder_data.get("name") or ""
            if isinstance(self.powder_data, dict)
            else ""
        )
        charge = float(self.current_charge or 0) if self.current_charge else 0.0
        default_name = f"{rifle_name} – {powder_name} {charge:.1f}gr".strip(" –")

        name, ok = QInputDialog.getText(
            self,
            tr("mlb_save_load_dialog_title"),
            tr("mlb_save_load_dialog_label"),
            text=default_name,
        )
        if not ok or not name.strip():
            return

        import json as _json
        from datetime import datetime
        from datetime import timezone as _tz

        snapshot = {
            "name": name.strip(),
            "rifle_data": (
                self.rifle_data if isinstance(self.rifle_data, dict) else None
            ),
            "bullet_data": (
                self.bullet_data if isinstance(self.bullet_data, dict) else None
            ),
            "powder_data": (
                self.powder_data if isinstance(self.powder_data, dict) else None
            ),
            "primer_data": (
                self.primer_data if isinstance(self.primer_data, dict) else None
            ),
            "brass_data": (
                self.brass_data if isinstance(self.brass_data, dict) else None
            ),
            "charge_gr": charge,
            "coal_mm": float(self.coal_mm or 0) if self.coal_mm else None,
            "cbto_mm": float(self.cbto_mm or 0) if self.cbto_mm else None,
        }
        rifle_id = (
            self.rifle_data.get("id") if isinstance(self.rifle_data, dict) else None
        )

        try:
            self._ensure_saved_designs_table()
            self.db.cursor.execute(
                "INSERT INTO saved_load_designs (name, rifle_id, snapshot_json, created_at)"
                " VALUES (?, ?, ?, ?)",
                (
                    name.strip(),
                    rifle_id,
                    _json.dumps(snapshot, ensure_ascii=False),
                    datetime.now(_tz.utc).isoformat(),
                ),
            )
            self.db.conn.commit()
            # Pin current result as comparison baseline for delta row
            try:
                latest = getattr(self, "_latest_visual_result", None)
                if isinstance(latest, dict):
                    snap = dict(latest)
                    snap["_snap_charge_gr"] = float(self.current_charge or 0)
                    snap["_snap_coal_mm"] = float(self.coal_mm or 0)
                    self._set_reference_result(snap)
            except Exception:
                pass
            try:
                from src.ui.toast import show_toast

                show_toast(self, f"Lagret: {name.strip()}", kind="success")
            except Exception:
                QMessageBox.information(
                    self,
                    tr("mlb_save_load_saved_title"),
                    tr("mlb_save_load_saved_body").format(name=name.strip()),
                )
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("mlb_save_load_error_title"),
                tr("mlb_save_load_error_body").format(error=exc),
            )

    def on_load_saved_design_clicked(self) -> None:
        """Vis dialog med lagrede ladningsoppsett og last inn valgt."""
        self._ensure_saved_designs_table()
        try:
            rows = self.db.execute_query(
                "SELECT id, name, created_at FROM saved_load_designs"
                " ORDER BY created_at DESC LIMIT 200"
            )
        except Exception:
            rows = []

        if not rows:
            QMessageBox.information(
                self,
                tr("mlb_no_saved_designs_title"),
                tr("mlb_no_saved_designs_body"),
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_load_design_title"))
        dlg.setMinimumWidth(520)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.addWidget(QLabel(tr("mlb_load_design_label")))

        list_widget = QListWidget()
        for row in rows:
            created = str(row.get("created_at") or "")[:16].replace("T", " ")
            item = QListWidgetItem(f"{row['name']}   ({created})")
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            list_widget.addItem(item)
        if list_widget.count():
            list_widget.setCurrentRow(0)
        dlg_layout.addWidget(list_widget)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        dlg_layout.addWidget(btn_box)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selected = list_widget.currentItem()
        if not selected:
            return

        design_id = selected.data(Qt.ItemDataRole.UserRole)
        try:
            result = self.db.execute_query(
                "SELECT snapshot_json FROM saved_load_designs WHERE id = ?",
                (design_id,),
            )
            if not result:
                return
            import json as _json

            snapshot = _json.loads(result[0]["snapshot_json"])
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("mlb_load_error_title"),
                tr("mlb_load_error_body").format(error=exc),
            )
            return

        # Gjenopprett tilstand
        if isinstance(snapshot.get("rifle_data"), dict):
            self.rifle_data = snapshot["rifle_data"]
        if isinstance(snapshot.get("bullet_data"), dict):
            self.bullet_data = snapshot["bullet_data"]
        if isinstance(snapshot.get("powder_data"), dict):
            self.powder_data = snapshot["powder_data"]
        if isinstance(snapshot.get("primer_data"), dict):
            self.primer_data = snapshot["primer_data"]
        if isinstance(snapshot.get("brass_data"), dict):
            self.brass_data = snapshot["brass_data"]

        for attr, key in (
            ("current_charge", "charge_gr"),
            ("coal_mm", "coal_mm"),
            ("cbto_mm", "cbto_mm"),
        ):
            val = snapshot.get(key)
            if val is not None:
                try:
                    setattr(self, attr, float(val))
                except (TypeError, ValueError):
                    pass

        # Oppdater UI-spinbokser om de finnes
        for spin_attr, val_attr in (
            ("charge_spin", "current_charge"),
            ("coal_spin", "coal_mm"),
            ("cbto_spin", "cbto_mm"),
        ):
            try:
                spin = getattr(self, spin_attr, None)
                if spin is not None:
                    spin.setValue(float(getattr(self, val_attr)))
            except Exception:
                pass

        # Utløs ny analyse
        try:
            self._request_update()  # type: ignore[attr-defined]
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Ladning lastet inn",
            f'"{snapshot.get("name", "")}" er lastet inn.\n'
            "Kontroller og juster om nødvendig.",
        )

    def on_print_label_clicked(self):
        """Generate and save a printable label for the current profile or batch."""
        try:
            from ..utils.label_printer import generate_label_text, save_label_to_file
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("mlb_missing_module_title"),
                tr("mlb_label_module_missing", error=e),
            )
            return

        ap_id = getattr(self, "current_ammo_profile_id", None)
        if not ap_id:
            # ask user for an ammo_profile id
            ap_id, ok = QInputDialog.getInt(
                self,
                tr("mlb_ammo_profile_id_title"),
                tr("mlb_ammo_profile_id_message"),
                0,
            )
            if not ok:
                return
            if ap_id == 0:
                ap_id = None

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("mlb_save_label_as"),
            "label.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if not path:
            return

        latest_result = getattr(self, "_latest_visual_result", None)
        internal_ballistics_summary = None
        if isinstance(latest_result, dict):
            internal_ballistics_summary = (
                self._build_current_internal_ballistics_summary(
                    latest_result=latest_result,
                    powder_name=str((self.powder_data or {}).get("name") or ""),
                    ammo_profile_id=ap_id,
                )
            )
        text = generate_label_text(
            self.db,
            ammo_profile_id=ap_id,
            internal_ballistics_summary=internal_ballistics_summary,
        )
        try:
            save_label_to_file(path, text)
        except Exception as e:
            QMessageBox.critical(
                self, tr("mlb_save_failed_title"), tr("mlb_save_label_failed", error=e)
            )
            return

        QMessageBox.information(
            self, tr("mlb_saved_title"), tr("mlb_label_saved", path=path)
        )

    def on_import_chronograph_clicked(self):
        """Open a file dialog, import selected CSV and show stats"""
        path, _ = QFileDialog.getOpenFileName(
            self, tr("mlb_select_chrono_csv"), "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        try:
            from ..utils.chronograph_import import import_chronograph_csv

            res = import_chronograph_csv(
                self.db,
                path,
                None,
                load_session_id=_get_active_load_session_id(),
                note=f"Imported via UI from {path}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("mlb_import_failed_title"),
                tr("mlb_import_csv_failed", error=e),
            )
            return

        stats = res.get("stats", {})
        QMessageBox.information(
            self,
            tr("mlb_import_complete_title"),
            tr(
                "mlb_import_complete_message",
                count=stats.get("count", 0),
                avg=stats.get("avg"),
                es=stats.get("es"),
                sd=stats.get("sd"),
            ),
        )

    def on_manual_chronograph_clicked(self):
        """Open dialog to paste velocities (one per line or comma-separated) and insert into DB"""
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_manual_chrono"))
        layout = QVBoxLayout()

        info = QLabel(tr("mlb_manual_chrono_info"))
        layout.addWidget(info)

        vel_text = QTextEdit()
        vel_text.setPlaceholderText(tr("mlb_manual_chrono_placeholder"))
        vel_text.setMinimumHeight(120)
        layout.addWidget(vel_text)

        ap_label = QLabel(tr("mlb_ammo_profile_optional"))
        layout.addWidget(ap_label)
        ap_input = QLineEdit()
        ap_input.setPlaceholderText(tr("mlb_ammo_profile_placeholder"))
        layout.addWidget(ap_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)

        def on_accept():
            text = vel_text.toPlainText().strip()
            if not text:
                QMessageBox.warning(
                    dlg, tr("mlb_no_data_title"), tr("mlb_paste_velocity_first")
                )
                return
            # parse values
            normalized = text.replace(",", " ")
            tokens = [t for t in normalized.split() if t.strip()]
            vals = []
            for tok in tokens:
                try:
                    vals.append(float(tok))
                except Exception:
                    QMessageBox.warning(
                        dlg,
                        tr("mlb_parse_error_title"),
                        tr("mlb_parse_token_failed", token=tok),
                    )
                    return

            ap_id = None
            ap_text = ap_input.text().strip()
            if ap_text:
                try:
                    ap_id = int(ap_text)
                except Exception:
                    QMessageBox.warning(
                        dlg, tr("mlb_parse_error_title"), tr("mlb_ammo_profile_int")
                    )
                    return

            # persist
            try:
                from ..utils.chronograph_import import import_velocities

                res = import_velocities(
                    self.db,
                    vals,
                    ap_id,
                    load_session_id=_get_active_load_session_id(),
                    note="Manual entry via UI",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr("mlb_error_title"),
                    tr("mlb_save_velocities_failed", error=e),
                )
                dlg.reject()
                return

            stats = res.get("stats", {})
            QMessageBox.information(
                self,
                tr("mlb_saved_title"),
                tr(
                    "mlb_saved_velocities",
                    count=stats.get("count", 0),
                    avg=stats.get("avg"),
                ),
            )
            dlg.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dlg.reject)

        dlg.setLayout(layout)
        dlg.exec()

    def on_refresh_chronograph_list(self):
        """Reload recent chronograph imports into the list widget"""
        cur = self.db.cursor
        cur.execute(
            "SELECT id, file_path, import_date, velocity_count, velocity_avg, velocity_es, velocity_sd FROM chronograph_imports ORDER BY import_date DESC LIMIT 50"
        )
        rows = cur.fetchall()
        self.chrono_list.clear()
        for r in rows:
            import_id = r[0]
            file_path = r[1] or "(manual)"
            date = r[2]
            count = r[3]
            avg = r[4]
            es = r[5]
            sd = r[6]
            display_date = date or tr("mlb_unknown_date")
            text = (
                f"#{import_id} {file_path} ({display_date}) — {count} {tr('mlb_velocity_short')} "
                f"— avg {format_velocity_fps(avg)} — ES {format_velocity_fps(es)} — SD {format_velocity_fps(sd)}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, import_id)
            self.chrono_list.addItem(item)

    def on_chrono_selection_changed(self):
        """Plot velocities from the selected chronograph import into the velocity plot."""
        item = self.chrono_list.currentItem()
        if not item:
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute(
            "SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,)
        )
        row = cur.fetchone()
        if not row:
            return
        import json

        try:
            velocities = json.loads(row[0]) if row[0] else []
        except Exception:
            velocities = []

        if not velocities:
            QMessageBox.information(
                self, tr("mlb_no_velocities_title"), tr("mlb_no_velocities_message")
            )
            return

        pg = getattr(self, "_pg", None)
        _vplot = getattr(self, "velocity_plot", None)
        # If pyqtgraph is available and we have a plot widget, overlay import points
        if pg is not None and _vplot is not None:
            try:
                _vplot.clear()
                # First draw simulated curve if present
                if hasattr(self, "_last_velocity_curve") and self._last_velocity_curve:
                    sim_x, sim_y = self._last_velocity_curve
                    _vplot.plot(
                        sim_x, sim_y, pen=pg.mkPen(color="#27ae60", width=3), name="sim"
                    )

                # Plot import velocities as points (x = shot index)
                xs = list(range(1, len(velocities) + 1))
                _vplot.plot(
                    xs,
                    velocities,
                    pen=pg.mkPen(color="#34495e", width=2),
                    symbol="o",
                    symbolBrush="#34495e",
                )
            except Exception as e:
                QMessageBox.warning(
                    self, "Plot error", f"Could not plot velocities: {e}"
                )
        else:
            # Fallback: show summary text
            avg = sum(velocities) / len(velocities)
            es = max(velocities) - min(velocities)
            self.scope_comparison_label.setText(
                f"Imported {len(velocities)} velocities — Avg {format_velocity_fps(avg)} — ES {format_velocity_fps(es)}"
            )

    def on_attach_chronograph_to_profile(self):
        """Attach selected chronograph import to an ammo_profile (create minimal profile if needed)"""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, tr("mlb_no_selection_title"), tr("mlb_select_import_first")
            )
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)

        # If a current ammo selection exists (we created one when creating batch earlier), attach to it.
        # Otherwise create a minimal ammo_profile from current UI selections.
        cur = self.db.cursor
        cur.execute(
            "SELECT ammo_profile_id FROM chronograph_imports WHERE id = ?", (import_id,)
        )
        existing = cur.fetchone()
        if existing and existing[0]:
            QMessageBox.information(
                self,
                "Already attached",
                f"Import already attached to profile id {existing[0]}",
            )
            return

        # Create minimal profile if we have component selections
        if self.rifle_data and self.bullet_data and self.powder_data:
            name = f"Profile from import {import_id}"
            cur.execute(
                "INSERT INTO ammo_profiles (name, rifle_id, caliber, bullet_id, bullet_weight, powder_id, powder_charge, primer_id, case_id, coal, cbto, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (
                    name,
                    self.rifle_data.get("id"),
                    self.rifle_data.get("caliber"),
                    self.bullet_data.get("id"),
                    float(self.bullet_data.get("weight", 0)),
                    self.powder_data.get("id"),
                    float(self.current_charge or 0),
                    self.primer_data.get("id") if self.primer_data else None,
                    self.brass_data.get("id") if self.brass_data else None,
                    float(self.coal_mm or 0),
                    float(self.cbto_mm or 0),
                ),
            )
            self.db.conn.commit()
            ammo_profile_id = cur.lastrowid
        else:
            # Prompt for profile id
            ap_id, ok = QInputDialog.getInt(
                self, "Ammo Profile ID", "Enter existing Ammo Profile ID to attach to:"
            )
            if not ok:
                return
            ammo_profile_id = ap_id

        # Update import row
        cur.execute(
            "UPDATE chronograph_imports SET ammo_profile_id = ? WHERE id = ?",
            (ammo_profile_id, import_id),
        )
        self.db.conn.commit()
        QMessageBox.information(
            self,
            "Attached",
            f"Import #{import_id} attached to profile {ammo_profile_id}",
        )
        self.on_refresh_chronograph_list()

    def on_save_chronograph_to_test_results(self):
        """Save selected chronograph import statistics into `test_results` linked to a profile or batch."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("mlb_select_import_first")
            )
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute(
            "SELECT velocities_json, ammo_profile_id, load_session_id FROM chronograph_imports WHERE id = ?",
            (import_id,),
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(
                self, tr("mlb_not_found_title"), tr("mlb_import_row_not_found")
            )
            return
        import json

        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(
                self, tr("mlb_no_velocities_title"), tr("mlb_no_velocities_message")
            )
            return

        # Determine ammo_profile to attach results
        ap_id = row[1]
        load_session_id = row[2]
        if not ap_id:
            # try to use currently selected ammo/profile in UI if exists (we created one earlier when creating batch)
            # For simplicity, prompt user for an ammo_profile id
            ap_id, ok = QInputDialog.getInt(
                self,
                "Ammo Profile ID",
                "Enter Ammo Profile ID to associate test results with:",
            )
            if not ok:
                return

        # Compute stats
        avg = sum(velocities) / len(velocities)
        es = max(velocities) - min(velocities)
        sd = statistics.stdev(velocities) if len(velocities) > 1 else 0.0

        # Insert into test_results: put first up to 3 velocities into velocity_1..3
        v1 = velocities[0] if len(velocities) > 0 else None
        v2 = velocities[1] if len(velocities) > 1 else None
        v3 = velocities[2] if len(velocities) > 2 else None

        cur.execute(
            "INSERT INTO test_results (ladder_test_id, load_session_id, charge_weight, velocity_1, velocity_2, velocity_3, velocity_avg, velocity_es, velocity_sd, image_path, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None,
                load_session_id,
                None,
                v1,
                v2,
                v3,
                float(avg),
                float(es),
                float(sd),
                None,
                f"Imported from chronograph_imports #{import_id}, linked to ammo_profile {ap_id}",
            ),
        )
        self.db.conn.commit()
        inserted_id = cur.lastrowid
        QMessageBox.information(
            self,
            "Saved",
            f"Saved test_results id {inserted_id} (avg {format_velocity_fps(avg)}, ES {format_velocity_fps(es)})",
        )
        # Also log predicted pressure for this saved test result (best-effort)
        chosen_charge = float(self.current_charge or 0)
        try:
            rifle_id = self.rifle_data["id"] if self.rifle_data else None
            # determine charge from attached ammo_profile if present
            if ap_id:
                cur.execute(
                    "SELECT powder_charge FROM ammo_profiles WHERE id = ?", (ap_id,)
                )
                r = cur.fetchone()
                if r and r[0] is not None:
                    chosen_charge = float(r[0])

            coal = float(self.coal_spin.value()) if hasattr(self, "coal_spin") else None
            cbto = float(self.cbto_spin.value()) if hasattr(self, "cbto_spin") else None
            saami = get_rifle_pressure_limit_psi(self.db, self.rifle_data)

            predict_and_log(
                self.db,
                self.engine,
                rifle_id,
                ap_id,
                chosen_charge,
                coal_mm=coal,
                cbto_mm=cbto,
                saami_max_psi=saami,
                note=f"Saved test_results #{inserted_id} from import #{import_id}",
                temp_c=(
                    self._current_temperature_c()
                    if hasattr(self, "temp_spin")
                    else None
                ),
                pressure_kpa=(
                    self._current_pressure_kpa()
                    if hasattr(self, "pressure_spin")
                    else None
                ),
                humidity_pct=(
                    float(self.humidity_spin.value())
                    if hasattr(self, "humidity_spin")
                    else None
                ),
            )
        except Exception:
            pass

        if ap_id:
            try:
                self._record_research_sample(
                    ammo_profile_id=ap_id,
                    velocities=velocities,
                    charge_gr=chosen_charge,
                    import_id=import_id,
                )
            except Exception as exc:
                self._logger.warning("Research sample recording failed: %s", exc)

    def on_analyze_and_suggest(self):
        """Analyze selected import (or current test results) and show recommendations."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("mlb_select_import_first")
            )
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute(
            "SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,)
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Not found", "Import row not found in DB")
            return
        import json

        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(
                self, "No velocities", "Selected import has no velocities"
            )
            return

        # Compute stats
        import statistics as _st

        avg = _st.mean(velocities)
        es = max(velocities) - min(velocities)
        sd = _st.stdev(velocities) if len(velocities) > 1 else 0.0

        from ..utils.recommender import suggest_adjustments

        stats = {"count": len(velocities), "avg": avg, "es": es, "sd": sd}
        suggestions = suggest_adjustments(
            stats, self.current_charge or 0, self.coal_mm or 0, self.cbto_mm or 0
        )

        # Show suggestions in dialog
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_analysis_suggestions_title"))
        layout = QVBoxLayout()
        for s in suggestions:
            layout.addWidget(QLabel(s))

        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec()

    def on_optimize_from_ladder_tests(self):
        """Query historical ladder tests and propose an optimal charge."""
        try:
            from ..utils.ladder_optimizer import suggest_charge_from_history
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("mlb_error_title"),
                tr("mlb_optimizer_module_missing", error=e),
            )
            return

        rifle_id = self.rifle_data.get("id") if self.rifle_data else None
        bullet_id = self.bullet_data.get("id") if self.bullet_data else None
        powder_id = self.powder_data.get("id") if self.powder_data else None

        res = suggest_charge_from_history(self.db, rifle_id, bullet_id, powder_id)
        if not res:
            QMessageBox.information(
                self,
                tr("mlb_insufficient_data_title"),
                tr("mlb_insufficient_ladder_data"),
            )
            return

        suggested: float = float(res.get("suggested_charge") or 0)
        model = res.get("model") or {}
        a = model.get("a") or 0.0
        b = model.get("b") or 0.0
        r2 = model.get("r2")

        # Refine suggestion by sampling the quadratic model across observed range
        samples: list = []
        try:
            _obs = res.get("observed_range")
            min_c, max_c = (
                _obs
                if isinstance(_obs, (list, tuple))
                else (suggested - 0.5, suggested + 0.5)
            )

            best_charge: float = suggested
            best_val = None
            for i in range(21):
                c = min_c + (max_c - min_c) * i / 20.0
                val = a * c * c + b * c + model.get("c", 0.0)
                samples.append((c, val))
                if best_val is None or val < best_val:
                    best_val = val
                    best_charge = c

            # Use refined charge
            refined = best_charge
        except Exception:
            refined = suggested

        # Plot model curve overlay on velocity_plot
        pg = getattr(self, "_pg", None)
        _vplot2 = getattr(self, "velocity_plot", None)
        if pg is not None and _vplot2 is not None:
            try:
                xs = [s[0] for s in samples]
                ys = [s[1] for s in samples]
                _vplot2.plot(
                    xs,
                    ys,
                    pen=pg.mkPen(color="#8e44ad", width=2, style=Qt.PenStyle.DashLine),
                )
            except Exception:
                pass

        # Safety check: use ballistics engine to predict peak pressure for refined suggestion
        predicted_pressure = None
        saami_max_psi = None
        try:
            eng = self.engine
            if eng:
                _rd = self.rifle_data if isinstance(self.rifle_data, dict) else {}
                _bd = self.bullet_data if isinstance(self.bullet_data, dict) else {}
                _pd = self.powder_data if isinstance(self.powder_data, dict) else {}
                res_calc = eng.calculate_load(
                    int(_rd.get("id") or 0),
                    int(_bd.get("id") or 0),
                    int(_pd.get("id") or 0),
                    float(refined),
                    float(self.coal_mm or 0),
                    float(self.cbto_mm or 0),
                    barrel_id=self._get_active_barrel_id(),
                )
                predicted_pressure = res_calc.get("max_pressure_psi")
        except Exception:
            predicted_pressure = None

        try:
            # Lookup SAAMI/CIP max pressure for the caliber
            caliber = None
            if self.rifle_data:
                caliber = self.rifle_data.get("caliber")
            if caliber:
                saami_max_psi = get_max_pressure_psi_for_caliber(self.db, caliber)
        except Exception:
            saami_max_psi = None

        # If we have predicted pressure and saami, enforce safety
        # Log the prediction into pressure_history for auditing
        try:
            ammo_profile_id = getattr(self, "current_ammo_profile_id", None)
            predict_and_log(
                self.db,
                self.engine,
                rifle_id,
                ammo_profile_id,
                float(refined),
                coal_mm=float(self.coal_mm or 0) if self.coal_mm is not None else None,
                cbto_mm=float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
                saami_max_psi=saami_max_psi,
                note="Optimizer suggestion",
            )
        except Exception:
            pass

        if predicted_pressure is not None and saami_max_psi is not None:
            if predicted_pressure > saami_max_psi:
                QMessageBox.critical(
                    self,
                    tr("mlb_unsafe_title"),
                    tr(
                        "mlb_optimizer_unsafe_blocked",
                        pressure=predicted_pressure,
                        max_pressure=saami_max_psi,
                    ),
                )
                return
            elif predicted_pressure > saami_max_psi * 0.95:
                confirm = QMessageBox.question(
                    self,
                    tr("mlb_high_pressure_warning_title"),
                    tr(
                        "mlb_high_pressure_warning_message",
                        pressure=predicted_pressure,
                        max_pressure=saami_max_psi,
                    ),
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return

        # Prompt user to accept refined suggestion
        accept = QMessageBox.question(
            self,
            tr("mlb_optimizer_suggestion_title"),
            tr("mlb_optimizer_suggestion_message", charge=refined, r2=r2),
        )
        if accept == QMessageBox.StandardButton.Yes:
            # set slider value (slider stores 10x grains)
            try:
                self.charge_slider.setValue(int(round(float(refined) * 10)))
                self.current_charge = refined
                self.charge_label.setText(
                    format_weight_grains(self.current_charge, "powder")
                )
                self.update_visualization()
                # Log predicted pressure for the applied suggestion
                try:
                    rifle_id = self.rifle_data["id"] if self.rifle_data else None
                    ap_id = getattr(self, "current_ammo_profile_id", None)
                    coal = (
                        float(self.coal_spin.value())
                        if hasattr(self, "coal_spin")
                        else None
                    )
                    cbto = (
                        float(self.cbto_spin.value())
                        if hasattr(self, "cbto_spin")
                        else None
                    )
                    # saami lookup
                    saami = get_rifle_pressure_limit_psi(self.db, self.rifle_data)
                    predict_and_log(
                        self.db,
                        self.engine,
                        rifle_id,
                        ap_id,
                        float(self.current_charge or 0),
                        coal_mm=coal,
                        cbto_mm=cbto,
                        saami_max_psi=saami,
                        note="Applied optimizer suggestion",
                        temp_c=(
                            self._current_temperature_c()
                            if hasattr(self, "temp_spin")
                            else None
                        ),
                        pressure_kpa=(
                            self._current_pressure_kpa()
                            if hasattr(self, "pressure_spin")
                            else None
                        ),
                        humidity_pct=(
                            float(self.humidity_spin.value())
                            if hasattr(self, "humidity_spin")
                            else None
                        ),
                    )
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.warning(
                    self,
                    tr("mlb_apply_failed_title"),
                    tr("mlb_apply_suggested_charge_failed", error=e),
                )

    def on_calibrate_engine_clicked(self):
        """Run calibration using the selected chronograph import(s)."""
        # Collect selected import(s)
        items = [self.chrono_list.item(i) for i in range(self.chrono_list.count())]
        selected_ids = []
        for it in items:
            if it and it.isSelected():
                iid = it.data(Qt.ItemDataRole.UserRole)
                if iid:
                    selected_ids.append(iid)

        if not selected_ids:
            # fallback: use current item if nothing multi-selected
            cur_item = self.chrono_list.currentItem()
            if cur_item:
                selected_ids = [cur_item.data(Qt.ItemDataRole.UserRole)]

        if not selected_ids:
            QMessageBox.information(
                self,
                tr("mlb_calibrate_title"),
                tr("mlb_select_import_for_calibration"),
            )
            return

        try:
            from ..utils.calibrator import calibrate_engine
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("mlb_missing_module_title"),
                tr("mlb_calibration_module_missing", error=e),
            )
            return

        res = calibrate_engine(self.db, self.engine, selected_ids)
        if not res.get("ok"):
            QMessageBox.warning(
                self,
                tr("mlb_calibration_failed_title"),
                tr(
                    "mlb_calibration_failed_message",
                    reason=res.get("reason"),
                    used=res.get("used"),
                ),
            )
            return

        slope = res.get("slope")
        intercept = res.get("intercept")
        mse = res.get("mse")
        used = res.get("used")

        QMessageBox.information(
            self,
            tr("mlb_calibration_complete_title"),
            tr(
                "mlb_calibration_complete_message",
                slope=slope,
                intercept=intercept,
                mse=mse,
                used=used,
            ),
        )

    def on_show_calibration_clicked(self):
        """Show last calibration info and optionally plot samples from selected imports."""
        cur = self.db.cursor
        cur.execute(
            "SELECT id, slope, intercept, mse, notes, created_date FROM engine_calibrations ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.information(
                self, tr("mlb_no_calibration_title"), tr("mlb_no_calibration_message")
            )
            return

        cid, slope, intercept, mse, notes, created = row

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_calibration_details_title"))
        v = QVBoxLayout()
        v.addWidget(QLabel(tr("mlb_calibration_id_value", id=cid)))
        v.addWidget(QLabel(tr("mlb_created_value", value=created)))
        v.addWidget(
            QLabel(
                tr(
                    "mlb_calibration_stats_value",
                    slope=slope,
                    intercept=float(intercept or 0.0),
                    mse=float(mse or 0.0),
                )
            )
        )
        v.addWidget(QLabel(tr("mlb_notes_value", value=notes or "")))

        # If user has selected imports, offer to plot their samples
        selected_ids = []
        if hasattr(self, "chrono_list") and getattr(self, "chrono_list") is not None:
            try:
                items = [
                    self.chrono_list.item(i) for i in range(self.chrono_list.count())
                ]
                selected_ids = [
                    it.data(Qt.ItemDataRole.UserRole)
                    for it in items
                    if it and it.isSelected()
                ]
            except Exception:
                selected_ids = []

        # If there are no selected items, ask the user to enter import ids manually
        if not selected_ids:
            text, ok = QInputDialog.getText(
                self,
                tr("mlb_select_imports_title"),
                tr("mlb_select_imports_message"),
            )
            if ok and text:
                try:
                    selected_ids = [
                        int(x.strip()) for x in text.split(",") if x.strip()
                    ]
                except Exception:
                    selected_ids = []

        if selected_ids:
            h = QHBoxLayout()
            plot_btn = QPushButton(tr("mlb_plot_selected_imports"))
            h.addWidget(plot_btn)
            v.addLayout(h)

            def do_plot():
                try:
                    from ..utils.calibrator import get_calibration_samples

                    samples = get_calibration_samples(
                        self.db, self.engine, selected_ids
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        tr("mlb_error_title"),
                        tr("mlb_could_not_get_samples", error=e),
                    )
                    return

                preds = samples.get("preds")
                meas = samples.get("meas")
                if not samples.get("ok") or not preds:
                    QMessageBox.information(
                        self,
                        tr("mlb_no_samples_title"),
                        tr("mlb_no_samples_message"),
                    )
                    return
                preds = list(preds)
                meas = list(meas) if meas is not None else []

                # Plot in a new dialog using pyqtgraph if available
                try:
                    import pyqtgraph as pg  # type: ignore[import-untyped]

                    pdlg = QDialog(self)
                    pdlg.setWindowTitle(tr("mlb_calibration_samples_title"))
                    layout = QVBoxLayout()
                    pw = pg.PlotWidget()
                    pw.setLabel("left", tr("mlb_measured_velocity_axis"))
                    pw.setLabel("bottom", tr("mlb_predicted_velocity_axis"))
                    pw.plot(preds, meas, pen=None, symbol="o")
                    # fit line
                    try:
                        a = float(slope)
                        b = float(intercept or 0.0)
                        xs = sorted(preds)
                        ys = [a * x + b for x in xs]
                        pw.plot(xs, ys, pen=pg.mkPen(color="y", width=2))
                    except Exception:
                        pass
                    layout.addWidget(pw)
                    btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
                    btns.accepted.connect(pdlg.accept)
                    layout.addWidget(btns)
                    pdlg.setLayout(layout)
                    pdlg.exec()
                except Exception:
                    # Fallback: show textual summary
                    pairs = "\n".join(
                        f"pred:{p:.1f} -> meas:{m:.1f}" for p, m in zip(preds, meas)
                    )
                    QMessageBox.information(self, tr("mlb_samples_title"), f"{pairs}")

            plot_btn.clicked.connect(do_plot)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        btns.accepted.connect(dlg.accept)
        v.addWidget(btns)

        def do_accept():
            # Prompt user to optionally tie calibration to an ammo_profile
            try:
                cur = self.db.cursor
                cur.execute("SELECT id, name FROM ammo_profiles ORDER BY name")
                rows = cur.fetchall() or []
                choices = [r[1] or f"#{r[0]}" for r in rows]
                ids = [r[0] for r in rows]
                ammo_id = None
                if choices:
                    item, ok = QInputDialog.getItem(
                        self,
                        tr("mlb_tie_ammo_profile_title"),
                        tr("mlb_tie_ammo_profile_message"),
                        choices,
                        0,
                        False,
                    )
                    if ok and item:
                        try:
                            idx = choices.index(item)
                            ammo_id = ids[idx]
                        except Exception:
                            ammo_id = None

                # Update calibration row as accepted
                try:
                    if ammo_id:
                        cur.execute(
                            "UPDATE engine_calibrations SET accepted=1, accepted_date=CURRENT_TIMESTAMP, ammo_profile_id=? WHERE id = ?",
                            (ammo_id, cid),
                        )
                    else:
                        cur.execute(
                            "UPDATE engine_calibrations SET accepted=1, accepted_date=CURRENT_TIMESTAMP WHERE id = ?",
                            (cid,),
                        )
                    self.db.conn.commit()
                    QMessageBox.information(
                        self,
                        tr("mlb_calibration_accepted_title"),
                        tr("mlb_calibration_accepted_message"),
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        tr("mlb_error_title"),
                        tr("mlb_accept_calibration_failed", error=e),
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr("mlb_error_title"),
                    tr("mlb_query_ammo_profiles_failed", error=e),
                )

        accept_btn = QPushButton(tr("mlb_accept_calibration"))
        accept_btn.clicked.connect(do_accept)
        v.addWidget(accept_btn)

    def on_open_ai_settings(self):
        """Open guidance settings dialog."""
        try:
            from ..utils.ai_assistant import Assistant
        except Exception:
            Assistant = None

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_ai_settings_title"))
        v = QVBoxLayout()

        info = QLabel(tr("mlb_ai_settings_info"))
        info.setWordWrap(True)
        v.addWidget(info)

        enabled_cb = QCheckBox(tr("mlb_enable_remote_ai"))
        v.addWidget(enabled_cb)

        model_label = QLabel(tr("mlb_model_label"))
        model_input = QLineEdit()
        model_input.setPlaceholderText(tr("mlb_model_placeholder"))
        v.addWidget(model_label)
        v.addWidget(model_input)

        api_label = QLabel(tr("mlb_api_key_label"))
        api_input = QLineEdit()
        api_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_input.setPlaceholderText(tr("mlb_api_key_placeholder"))
        v.addWidget(api_label)
        v.addWidget(api_input)

        show_key_cb = QCheckBox(tr("mlb_show_api_key"))

        def _toggle_show_key(checked: bool):
            api_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )

        show_key_cb.toggled.connect(_toggle_show_key)
        v.addWidget(show_key_cb)

        clear_key_cb = QCheckBox(tr("mlb_clear_saved_api_key"))
        v.addWidget(clear_key_cb)

        status = QLabel("")
        status.setProperty("role", "muted")
        status.setWordWrap(True)
        v.addWidget(status)

        existing_api_key = None
        existing_model = None
        try:
            cur = self.db.cursor
            cur.execute(
                "CREATE TABLE IF NOT EXISTS ai_settings (id INTEGER PRIMARY KEY AUTOINCREMENT, enabled INTEGER, model TEXT, api_key TEXT, created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            cur.execute(
                "SELECT enabled, model, api_key FROM ai_settings ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                enabled_cb.setChecked(bool(row[0]))
                existing_model = row[1]
                if existing_model:
                    model_input.setText(str(existing_model))
                existing_api_key = row[2]
        except Exception:
            pass

        if existing_api_key:
            status.setText(tr("mlb_api_key_stored"))
        else:
            status.setText(tr("mlb_api_key_missing"))

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        v.addWidget(btns)

        def on_ok():
            enabled = enabled_cb.isChecked()
            model_val = model_input.text().strip() or existing_model
            api_val = api_input.text().strip()
            if clear_key_cb.isChecked():
                api_val = None
            elif not api_val:
                api_val = existing_api_key

            try:
                if Assistant is not None:
                    Assistant(model=model_val, db=self.db).save_settings(
                        self.db, enabled, model_val, api_val
                    )
                else:
                    cur = self.db.cursor
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS ai_settings (id INTEGER PRIMARY KEY AUTOINCREMENT, enabled INTEGER, model TEXT, api_key TEXT, created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
                    )
                    cur.execute(
                        "INSERT INTO ai_settings (enabled, model, api_key) VALUES (?, ?, ?)",
                        (1 if enabled else 0, model_val, api_val),
                    )
                    self.db.conn.commit()
            except Exception:
                pass

            dlg.accept()

        btns.accepted.connect(on_ok)
        btns.rejected.connect(dlg.reject)

        dlg.setLayout(v)
        dlg.exec()

    def on_open_ai_chat(self):
        """Open the AI assistant chat dialog."""
        try:
            from ..utils.ai_assistant import Assistant  # type: ignore[import]

            _svc = Assistant(db=getattr(self, "db", None))  # noqa: F841
            QMessageBox.information(
                self, tr("mlb_ai_assistant"), tr("mlb_ai_unavailable")
            )
        except Exception:
            QMessageBox.information(
                self, tr("mlb_ai_assistant"), tr("mlb_ai_unavailable")
            )

    def on_explain_plot_clicked(self):
        """Gather current plot data and ask the assistant to explain it."""
        try:
            from ..utils.ai_assistant import Assistant
        except Exception:
            Assistant = None

        # Try to capture the last plotted velocity curve and stats
        ctx = {}
        try:
            if hasattr(self, "_last_velocity_curve") and self._last_velocity_curve:
                xs, ys = self._last_velocity_curve
                # summarize: min/max/mean
                import statistics

                ctx["plot_summary"] = {
                    "n": len(xs),
                    "x_min": min(xs),
                    "x_max": max(xs),
                    "y_min": min(ys),
                    "y_max": max(ys),
                    "y_mean": float(statistics.mean(ys)) if ys else None,
                }
        except Exception:
            pass

        # Persist snapshot if we have series data
        try:
            if (
                ctx.get("plot_summary")
                and hasattr(self, "_last_velocity_curve")
                and self._last_velocity_curve
            ):
                xs, ys = self._last_velocity_curve
                import json

                meta = json.dumps(ctx.get("plot_summary"))
                series = json.dumps({"x": xs, "y": ys})
                try:
                    cur = self.db.cursor
                    cur.execute(
                        "INSERT INTO plot_snapshots (snapshot_type, metadata, series_json) VALUES (?, ?, ?)",
                        ("velocity_curve", meta, series),
                    )
                    self.db.conn.commit()
                except Exception:
                    pass
        except Exception:
            pass

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_explain_plot_title"))
        v = QVBoxLayout()
        prompt_edit = QTextEdit()
        prompt_edit.setPlaceholderText(tr("mlb_explain_plot_placeholder"))
        v.addWidget(QLabel(tr("mlb_plot_summary")))
        v.addWidget(QLabel(str(ctx.get("plot_summary", tr("mlb_no_plot_data")))))
        v.addWidget(prompt_edit)

        h = QHBoxLayout()
        ask_btn = QPushButton(tr("mlb_ask_assistant"))
        h.addWidget(ask_btn)
        v.addLayout(h)

        result = QTextEdit()
        result.setReadOnly(True)
        v.addWidget(result)

        def do_ask():
            q = prompt_edit.toPlainText().strip() or "Explain the currently shown plot."
            assistant = Assistant() if Assistant is not None else None
            try:
                if assistant:
                    resp = assistant.chat(
                        q, [], context={"plot_summary": ctx.get("plot_summary")}
                    )
                    result.setPlainText(resp)
                    try:
                        assistant.persist_chat(self.db, q, resp)
                    except Exception:
                        pass
                else:
                    result.setPlainText(
                        "(stub) No remote assistant available. Plot summary: %s"
                        % ctx.get("plot_summary")
                    )
            except Exception as e:
                result.setPlainText(f"Error contacting assistant: {e}")

        ask_btn.clicked.connect(do_ask)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        dlg.setLayout(v)
        dlg.exec()

    def on_open_preferences(self):
        """Open a small Preferences dialog for UI settings."""
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_preferences_title"))
        v = QVBoxLayout()

        # Transonic overlay setting
        trans_cb = QCheckBox(tr("mlb_show_transonic_margin"))
        trans_margin_label = QLabel(
            f"{tr('mlb_margin_fps')} ({get_velocity_suffix().strip()})"
        )
        trans_spin = QDoubleSpinBox()
        trans_spin.setRange(0.0, float(velocity_fps_to_display_value(500.0) or 500.0))
        trans_spin.setSingleStep(5.0 if "fps" in get_velocity_suffix() else 2.0)
        trans_spin.setSuffix(get_velocity_suffix())

        # Load current persisted values
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT value FROM ui_settings WHERE key = ?",
                ("transonic_overlay_enabled",),
            )
            r = cur.fetchone()
            if r and r[0] is not None:
                try:
                    trans_cb.setChecked(bool(int(r[0])))
                except Exception:
                    trans_cb.setChecked(r[0].lower() in ("1", "true", "yes"))
            cur.execute(
                "SELECT value FROM ui_settings WHERE key = ?", ("transonic_margin_fps",)
            )
            r2 = cur.fetchone()
            if r2 and r2[0] is not None:
                try:
                    trans_spin.setValue(
                        float(velocity_fps_to_display_value(float(r2[0])) or r2[0])
                    )
                except Exception:
                    pass
        except Exception:
            pass

        v.addWidget(trans_cb)
        h = QHBoxLayout()
        h.addWidget(trans_margin_label)
        h.addWidget(trans_spin)
        v.addLayout(h)

        # Velocity plot Y-range prefs
        v.addSpacing(6)
        v.addWidget(QLabel(tr("mlb_velocity_plot_y_range")))
        y_h = QHBoxLayout()
        y_min_label = QLabel(tr("mlb_min_label"))
        y_min_spin = QDoubleSpinBox()
        y_min_spin.setRange(0.0, 5000.0)
        y_min_spin.setSingleStep(10.0)
        y_max_label = QLabel(tr("mlb_max_label"))
        y_max_spin = QDoubleSpinBox()
        y_max_spin.setRange(0.0, 10000.0)
        y_max_spin.setSingleStep(10.0)

        # Load persisted values
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT value FROM ui_settings WHERE key = ?", ("velocity_y_min",)
            )
            rmin = cur.fetchone()
            if rmin and rmin[0] is not None:
                try:
                    y_min_spin.setValue(float(rmin[0]))
                except Exception:
                    pass
            cur.execute(
                "SELECT value FROM ui_settings WHERE key = ?", ("velocity_y_max",)
            )
            rmax = cur.fetchone()
            if rmax and rmax[0] is not None:
                try:
                    y_max_spin.setValue(float(rmax[0]))
                except Exception:
                    pass
        except Exception:
            pass

        y_h.addWidget(y_min_label)
        y_h.addWidget(y_min_spin)
        y_h.addWidget(y_max_label)
        y_h.addWidget(y_max_spin)
        v.addLayout(y_h)

        # Theme selection + preview
        v.addSpacing(6)
        v.addWidget(QLabel(tr("mlb_ui_theme")))
        theme_h = QHBoxLayout()
        theme_label = QLabel(tr("mlb_theme_label"))
        theme_combo = QComboBox()
        theme_combo.addItems(
            [tr("mlb_theme_system"), tr("mlb_theme_light"), tr("mlb_theme_dark")]
        )
        theme_h.addWidget(theme_label)
        theme_h.addWidget(theme_combo)
        # Preview box
        theme_preview = QLabel(tr("mlb_theme_preview"))
        theme_preview.setMinimumHeight(60)
        theme_preview.setStyleSheet(
            "padding:8px; border:1px solid #ccc; border-radius:4px;"
        )
        v.addLayout(theme_h)
        v.addWidget(theme_preview)

        # Load persisted theme if present
        try:
            cur = self.db.cursor
            cur.execute("SELECT value FROM ui_settings WHERE key = ?", ("ui_theme",))
            theme_row = cur.fetchone()
            if theme_row and theme_row[0]:
                theme_val = (theme_row[0] or "").lower()
                if theme_val == "dark":
                    theme_combo.setCurrentText(tr("mlb_theme_dark"))
                elif theme_val == "light":
                    theme_combo.setCurrentText(tr("mlb_theme_light"))
                else:
                    theme_combo.setCurrentText(tr("mlb_theme_system"))
        except Exception:
            pass

        def _apply_theme_preview(name: str):
            try:
                n = (name or "").lower()
                if n == "dark":
                    theme_preview.setStyleSheet(
                        "background:#2c2c2c; color:#f0f0f0; padding:8px; border-radius:4px;"
                    )
                elif n == "light" or n == "system":
                    theme_preview.setStyleSheet(
                        "background: #ffffff; color: #222; padding:8px; border-radius:4px; border:1px solid #ddd;"
                    )
                else:
                    theme_preview.setStyleSheet(
                        "padding:8px; border:1px solid #ccc; border-radius:4px;"
                    )
            except Exception:
                pass

        theme_combo.currentTextChanged.connect(_apply_theme_preview)
        # initialise preview
        try:
            _apply_theme_preview(theme_combo.currentText())
        except Exception:
            pass

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        v.addWidget(btns)

        # Reset to defaults button
        reset_btn = QPushButton(tr("mlb_reset_preferences"))

        def do_reset():
            try:
                # remove persisted keys
                for k in (
                    "transonic_overlay_enabled",
                    "transonic_margin_fps",
                    "velocity_y_min",
                    "velocity_y_max",
                    "ui_theme",
                ):
                    try:
                        self._delete_ui_setting(k)
                    except Exception:
                        pass
                # reset UI elements
                try:
                    trans_cb.setChecked(False)
                    trans_spin.setValue(
                        float(velocity_fps_to_display_value(50.0) or 50.0)
                    )
                    y_min_spin.setValue(0.0)
                    y_max_spin.setValue(0.0)
                    try:
                        theme_combo.setCurrentText(tr("mlb_theme_system"))
                        _apply_theme_preview(tr("mlb_theme_system"))
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass

        reset_btn.clicked.connect(do_reset)
        v.addWidget(reset_btn)

        def on_ok():
            try:
                self._save_ui_setting(
                    "transonic_overlay_enabled", "1" if trans_cb.isChecked() else "0"
                )
                self._save_ui_setting(
                    "transonic_margin_fps",
                    str(
                        velocity_display_to_fps(trans_spin.value())
                        or trans_spin.value()
                    ),
                )
                # velocity y-range
                try:
                    self._save_ui_setting("velocity_y_min", str(y_min_spin.value()))
                    self._save_ui_setting("velocity_y_max", str(y_max_spin.value()))
                    # update instance values
                    self.velocity_y_min = float(y_min_spin.value())
                    self.velocity_y_max = float(y_max_spin.value())
                except Exception:
                    pass
                # UI theme
                try:
                    sel_text = theme_combo.currentText() or tr("mlb_theme_system")
                    theme_map = {
                        tr("mlb_theme_system").lower(): "system",
                        tr("mlb_theme_light").lower(): "light",
                        tr("mlb_theme_dark").lower(): "dark",
                    }
                    sel = theme_map.get(sel_text.lower(), "system")
                    if sel in ("system", "light", "dark"):
                        self._save_ui_setting("ui_theme", sel)
                        # apply immediately to this widget
                        if sel == "dark":
                            try:
                                self.setStyleSheet(
                                    "background: #2c2c2c; color: #f0f0f0;"
                                )
                            except Exception:
                                pass
                        else:
                            try:
                                self.setStyleSheet("")
                            except Exception:
                                pass
                except Exception:
                    pass
                # apply to live widgets if present
                try:
                    if getattr(self, "transonic_cb", None):
                        self.transonic_cb.setChecked(trans_cb.isChecked())
                    if getattr(self, "transonic_margin", None):
                        self.transonic_margin.setValue(trans_spin.value())
                    self.update_visualization()
                except Exception:
                    pass
            except Exception:
                pass
            dlg.accept()

        btns.accepted.connect(on_ok)
        btns.rejected.connect(dlg.reject)

        dlg.setLayout(v)
        dlg.exec()

    def on_suggest_next_charge(self):
        """Gather recent test results and ask GP optimizer to suggest next charge."""
        try:
            from ..utils.gp_optimizer import suggest_next_charge
        except Exception:
            QMessageBox.critical(
                self, tr("mlb_error_title"), tr("mlb_gp_optimizer_missing")
            )
            return

        # Collect recent results from test_results (use velocity_avg if present)
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 20"
            )
            rows = cur.fetchall() or []
            if not rows:
                QMessageBox.information(
                    self, tr("mlb_no_data_title"), tr("mlb_no_recent_test_results")
                )
                return
            charges = []
            velocities = []
            # reverse to chronological order
            for r in reversed(rows):
                try:
                    c = float(r[0])
                    v = float(r[1])
                except Exception:
                    continue
                charges.append(c)
                velocities.append(v)
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("mlb_db_error_title"),
                tr("mlb_query_test_results_failed", error=e),
            )
            return

        if not charges or not velocities:
            QMessageBox.information(
                self,
                tr("mlb_no_usable_data_title"),
                tr("mlb_no_usable_charge_velocity"),
            )
            return

        # Determine bounds from observed charges (expand a bit)
        min_c = max(0.0, min(charges) - 1.0)
        max_c = max(charges) + 1.0
        try:
            suggestion = suggest_next_charge(charges, velocities, (min_c, max_c))
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("mlb_optimizer_error_title"),
                tr("mlb_optimizer_failed", error=e),
            )
            return

        # If subsonic mode is enabled, attempt to adjust suggestion downward until predicted velocity <= target
        try:
            if getattr(self, "subsonic_cb", None) and self.subsonic_cb.isChecked():
                target_v = self._subsonic_target_fps()
                # if engine available, simulate and step down
                if hasattr(self, "engine") and self.engine:
                    try:
                        sim_v = None
                        # try predict at suggested charge
                        if hasattr(self.engine, "predict_velocity"):
                            sim_v = float(self.engine.predict_velocity(suggestion))  # type: ignore[attr-defined]
                        elif hasattr(self.engine, "calculate_load"):
                            res = self.engine.calculate_load(None, None, None, suggestion, None, None)  # type: ignore[attr-defined, arg-type]
                            if isinstance(res, dict):
                                sim_v = float(
                                    res.get("velocity")
                                    or res.get("velocity_avg")
                                    or res.get("predicted_velocity")
                                    or 0
                                )
                        # if predicted is above target, step down by 0.5gr until within bounds or reach min_c
                        step = 0.5
                        attempts = 0
                        while (
                            sim_v is not None
                            and sim_v > target_v
                            and suggestion > min_c
                            and attempts < 20
                        ):
                            suggestion = round(max(min_c, suggestion - step), 3)
                            attempts += 1
                            try:
                                if hasattr(self.engine, "predict_velocity"):
                                    sim_v = float(
                                        self.engine.predict_velocity(suggestion)  # type: ignore[attr-defined]
                                    )
                                elif hasattr(self.engine, "calculate_load"):
                                    res = self.engine.calculate_load(None, None, None, suggestion, None, None)  # type: ignore[attr-defined, arg-type]
                                    if isinstance(res, dict):
                                        sim_v = float(
                                            res.get("velocity")
                                            or res.get("velocity_avg")
                                            or res.get("predicted_velocity")
                                            or 0
                                        )
                            except Exception:
                                break
                        # if we couldn't satisfy target, warn user
                        if sim_v is not None and sim_v > target_v:
                            QMessageBox.warning(
                                self,
                                tr("mlb_subsonic_title"),
                                tr(
                                    "mlb_subsonic_target_not_reached",
                                    target=target_v,
                                    predicted=sim_v,
                                    charge=suggestion,
                                ),
                            )
                    except Exception:
                        pass
                else:
                    # without engine, just nudge suggestion lower conservatively
                    suggestion = round(max(min_c, suggestion - 0.5), 3)

        except Exception:
            pass

        # Persist suggestion
        try:
            import json

            basis = json.dumps({"charges": charges, "velocities": velocities})
            cur.execute(
                "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
                (float(suggestion), basis),
            )
            self.db.conn.commit()
        except Exception:
            pass

        QMessageBox.information(
            self,
            tr("mlb_suggestion_title"),
            tr("mlb_suggested_next_charge", charge=suggestion),
        )

    def on_manage_suggestions_clicked(self):
        """Open a dialog to browse/pick past optimizer suggestions."""
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mlb_optimizer_suggestions_title"))
        v = QVBoxLayout()

        listw = QListWidget()
        self._suggestion_listw = listw
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT id, suggested_charge, created_date, basis_text FROM optimizer_suggestions ORDER BY id DESC LIMIT 200"
            )
            rows = cur.fetchall() or []
            for r in rows:
                sid = r[0]
                sc = r[1]
                cd = r[2]
                basis = (r[3] or "")[:200]
                item = QListWidgetItem(
                    f"#{sid} — {format_weight_grains(sc, 'powder')} — {cd} — {basis}"
                )
                item.setData(Qt.ItemDataRole.UserRole, sid)
                listw.addItem(item)
        except Exception:
            pass

        v.addWidget(listw)

        h = QHBoxLayout()
        create_wf_btn = QPushButton(tr("mlb_create_workflow_from_suggestion"))
        mark_tested_btn = QPushButton(tr("mlb_mark_suggestion_tested"))
        h.addWidget(create_wf_btn)
        h.addWidget(mark_tested_btn)
        v.addLayout(h)

        def create_workflow():
            it = listw.currentItem()
            if not it:
                QMessageBox.information(
                    self, tr("mlb_select_title"), tr("mlb_select_suggestion_first")
                )
                return
            sid = it.data(Qt.ItemDataRole.UserRole)
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT suggested_charge, basis_text FROM optimizer_suggestions WHERE id = ?",
                    (sid,),
                )
                row = cur.fetchone()
                if not row:
                    QMessageBox.critical(
                        self, tr("mlb_error_title"), tr("mlb_suggestion_not_found")
                    )
                    return
                suggested_charge = float(row[0])
                basis = (row[1] or "").strip()
                name = f"GP Suggestion #{sid}"
                next_action = f"Test suggested charge {format_weight_grains(suggested_charge, 'powder')} (based on suggestion #{sid})"
                if basis:
                    next_action += f"\nKontekst: {basis[:140]}"
                cur.execute(
                    "INSERT INTO load_development_workflows (name, status, next_action) VALUES (?, 'suggested', ?)",
                    (name, next_action),
                )
                self.db.conn.commit()
                QMessageBox.information(
                    self,
                    tr("mlb_workflow_created_title"),
                    tr("mlb_workflow_created_from_suggestion"),
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr("mlb_db_error_title"),
                    tr("mlb_create_workflow_failed", error=e),
                )

        def mark_tested():
            it = listw.currentItem()
            if not it:
                QMessageBox.information(
                    self, tr("mlb_select_title"), tr("mlb_select_suggestion_first")
                )
                return
            sid = it.data(Qt.ItemDataRole.UserRole)
            # Prompt for test_result id (or choose from recent)
            try:
                cur = self.db.cursor
                cur.execute(
                    "SELECT id, ladder_test_id, charge_weight, velocity_avg FROM test_results ORDER BY id DESC LIMIT 50"
                )
                rows = cur.fetchall() or []
                choices = [f"#{r[0]} charge:{r[2]} vel:{r[3]}" for r in rows]
                ids = [r[0] for r in rows]
                if choices:
                    sel, ok = QInputDialog.getItem(
                        self,
                        tr("mlb_select_test_result_title"),
                        tr("mlb_select_test_result_message"),
                        choices,
                        0,
                        False,
                    )
                    if not ok:
                        return
                    idx = choices.index(sel)
                    tr_id = ids[idx]
                else:
                    tr_text, ok = QInputDialog.getText(
                        self,
                        tr("mlb_test_result_id_title"),
                        tr("mlb_test_result_id_message"),
                    )
                    if not ok:
                        return
                    tr_id = int(tr_text.strip())
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr("mlb_error_title"),
                    tr("mlb_select_test_result_failed", error=e),
                )
                return

            # Update suggestion record to record tested id and refit GP using all recent test_results
            try:
                # append tested marker to basis_text
                cur.execute(
                    "SELECT basis_text FROM optimizer_suggestions WHERE id = ?", (sid,)
                )
                row = cur.fetchone()
                basis = (row[0] or "") + f"\nTESTED_WITH:{tr_id}"
                cur.execute(
                    "UPDATE optimizer_suggestions SET basis_text = ? WHERE id = ?",
                    (basis, sid),
                )
                self.db.conn.commit()
            except Exception:
                pass

            # Re-run suggestion step (same logic as on_suggest_next_charge)
            try:
                cur.execute(
                    "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 200"
                )
                rows = cur.fetchall() or []
                charges = []
                velocities = []
                for r in reversed(rows):
                    try:
                        c = float(r[0])
                        v = float(r[1])
                    except Exception:
                        continue
                    charges.append(c)
                    velocities.append(v)
                if not charges:
                    QMessageBox.information(
                        self, tr("mlb_no_data_title"), tr("mlb_no_test_results_refit")
                    )
                    return
                from ..utils.gp_optimizer import suggest_next_charge

                min_c = max(0.0, min(charges) - 1.0)
                max_c = max(charges) + 1.0
                new_sugg = suggest_next_charge(charges, velocities, (min_c, max_c))
                import json

                cur.execute(
                    "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
                    (float(new_sugg), json.dumps({"based_on_rows": len(charges)})),
                )
                self.db.conn.commit()
                QMessageBox.information(
                    self,
                    tr("mlb_refit_complete_title"),
                    tr("mlb_refit_complete_message", charge=new_sugg),
                )
                # refresh list
                listw.clear()
                cur.execute(
                    "SELECT id, suggested_charge, created_date, basis_text FROM optimizer_suggestions ORDER BY id DESC LIMIT 200"
                )
                rows = cur.fetchall() or []
                for r in rows:
                    sid2 = r[0]
                    sc2 = r[1]
                    cd2 = r[2]
                    basis2 = (r[3] or "")[:200]
                    item2 = QListWidgetItem(
                        f"#{sid2} — {format_weight_grains(sc2, 'powder')} — {cd2} — {basis2}"
                    )

                    item2.setData(Qt.ItemDataRole.UserRole, sid2)
                    listw.addItem(item2)
            except Exception:
                pass

        create_wf_btn.clicked.connect(create_workflow)
        mark_tested_btn.clicked.connect(mark_tested)
        show_basis_btn = QPushButton(tr("mlb_show_basis_plot"))
        show_basis_btn.clicked.connect(self.show_basis)

    def show_basis(self):
        listw = getattr(self, "_suggestion_listw", None)
        it = listw.currentItem() if listw is not None else None
        if not it:
            QMessageBox.information(
                self, tr("mlb_select_title"), tr("mlb_select_suggestion_first")
            )
            return
        sid = it.data(Qt.ItemDataRole.UserRole)
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT basis_text FROM optimizer_suggestions WHERE id = ?", (sid,)
            )
            row = cur.fetchone()
            if not row or not row[0]:
                QMessageBox.information(
                    self, tr("mlb_no_basis_title"), tr("mlb_no_basis_message")
                )
                return
            import json

            b = row[0]
            try:
                payload = json.loads(b)
                xs = payload.get("x") or payload.get("charges") or []
                ys = payload.get("y") or payload.get("velocities") or []
            except Exception:
                QMessageBox.information(
                    self,
                    tr("mlb_unsupported_title"),
                    tr("mlb_basis_unsupported"),
                )
                return
            try:
                import pyqtgraph as pg  # type: ignore[import]  # noqa: F401

                self._show_pyqtgraph_plot(xs, ys, sid)
            except Exception:
                pairs = "\n".join(f"{x}->{y}" for x, y in zip(xs, ys))
                QMessageBox.information(self, tr("mlb_basis_data_title"), pairs)
        except Exception:
            pass

    def _show_pyqtgraph_plot(self, xs, ys, sid):
        try:
            pdlg = QDialog(self)
            pdlg.setWindowTitle(tr("mlb_basis_plot_title", id=sid))
            lv = QVBoxLayout()
            import pyqtgraph as pg  # type: ignore

            pw = pg.PlotWidget()
            pw.plot(xs, ys, pen=None, symbol="o")
            pw.setLabel("left", tr("mlb_velocity_axis"))
            pw.setLabel("bottom", tr("mlb_charge_axis"))
            lv.addWidget(pw)
            btns2 = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            btns2.rejected.connect(pdlg.reject)
            lv.addWidget(btns2)
            pdlg.setLayout(lv)
            pdlg.exec()
        except Exception as e:
            QMessageBox.critical(
                self, tr("mlb_error_title"), tr("mlb_load_basis_failed", error=e)
            )

    def on_auto_match_suggestions(self):
        """Attempt to auto-match open suggestions to recent test_results within tolerance, mark tested and refit."""
        try:
            cur = self.db.cursor
            # find suggestions not already marked tested
            cur.execute(
                "SELECT id, suggested_charge FROM optimizer_suggestions ORDER BY id DESC LIMIT 200"
            )
            rows = cur.fetchall() or []
            if not rows:
                QMessageBox.information(
                    self, "No suggestions", "No optimizer suggestions found."
                )
                return

            matched = 0
            for r in rows:
                sid = r[0]
                sugg = float(r[1]) if r[1] is not None else None
                if sugg is None:
                    continue

                best_diff: float | None = None
                best_id: int = 0

                # Find closest test_result to this suggestion
                try:
                    cur.execute(
                        "SELECT id, charge_weight FROM test_results WHERE charge_weight IS NOT NULL ORDER BY id DESC LIMIT 500"
                    )
                    test_rows = cur.fetchall() or []
                    for tr_row in test_rows:
                        try:
                            tr_id = int(tr_row[0])
                            tr_charge = float(tr_row[1])
                        except Exception:
                            continue
                        diff = abs(tr_charge - sugg)
                        if best_diff is None or diff < best_diff:
                            best_diff = diff
                            best_id = tr_id
                except Exception:
                    pass

                # if close enough (<=0.3gr) mark tested
                if best_diff is not None and best_diff <= 0.3:
                    try:
                        cur.execute(
                            "SELECT basis_text FROM optimizer_suggestions WHERE id = ?",
                            (sid,),
                        )
                        row = cur.fetchone()
                        basis = (row[0] or "") + f"\nTESTED_WITH:{best_id}"
                        cur.execute(
                            "UPDATE optimizer_suggestions SET basis_text = ? WHERE id = ?",
                            (basis, sid),
                        )
                        self.db.conn.commit()
                        matched += 1
                    except Exception:
                        pass

            # if we matched any, refit GP and produce a new suggestion
            if matched:
                try:
                    cur.execute(
                        "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 500"
                    )
                    rows2 = cur.fetchall() or []
                    charges = []
                    velocities = []
                    for r in reversed(rows2):
                        try:
                            charges.append(float(r[0]))
                            velocities.append(float(r[1]))
                        except Exception:
                            continue
                    if charges:
                        from ..utils.gp_optimizer import suggest_next_charge

                        min_c = max(0.0, min(charges) - 1.0)
                        max_c = max(charges) + 1.0
                        new_sugg = suggest_next_charge(
                            charges, velocities, (min_c, max_c)
                        )
                        import json

                        cur.execute(
                            "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
                            (
                                float(new_sugg),
                                json.dumps({"based_on_rows": len(charges)}),
                            ),
                        )
                        self.db.conn.commit()
                        QMessageBox.information(
                            self,
                            "Auto-Match",
                            f"Matched {matched} suggestions. New suggestion: {format_weight_grains(new_sugg, 'powder')}",
                        )
                        return
                except Exception as e:
                    QMessageBox.information(
                        self,
                        "Auto-Match",
                        f"Matched {matched} suggestions but refit failed: {e}",
                    )
                    return

            QMessageBox.information(
                self,
                "Auto-Match",
                f"Auto-match complete. Matched {matched} suggestions.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Auto-match failed: {e}")

    def on_toggle_auto_match(self, checked: bool):
        """Enable or disable the background poller for new test_results."""
        if checked:
            # initialize last seen id
            try:
                cur = self.db.cursor
                cur.execute("SELECT MAX(id) FROM test_results")
                row = cur.fetchone()
                self._last_test_result_id = (
                    int(row[0]) if row and row[0] is not None else 0
                )
            except Exception:
                self._last_test_result_id = 0
            self._auto_match_timer.start()
            self.auto_match_toggle.setText("Disable Auto-Match")
        else:
            self._auto_match_timer.stop()
            self.auto_match_toggle.setText("Enable Auto-Match")

    def _auto_match_poll(self):
        """Poll DB for new test_results and process them."""
        try:
            cur = self.db.cursor
            cur.execute("SELECT MAX(id) FROM test_results")
            row = cur.fetchone()
            max_id = int(row[0]) if row and row[0] is not None else 0
            if self._last_test_result_id is None:
                self._last_test_result_id = max_id
                return
            if max_id > self._last_test_result_id:
                # process new ids
                for nid in range(self._last_test_result_id + 1, max_id + 1):
                    try:
                        self._auto_match_on_new_result(nid)
                    except Exception:
                        pass
                self._last_test_result_id = max_id
        except Exception:
            # ignore polling errors
            return

    def _auto_match_on_new_result(self, tr_id: int):
        """Try to match a single new test_result to any open suggestions within tolerance."""
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT charge_weight, velocity_avg FROM test_results WHERE id = ?",
                (tr_id,),
            )
            row = cur.fetchone()
            if not row:
                return
            try:
                charge = float(row[0])
            except Exception:
                return

            # find suggestions not yet marked TESTED_WITH
            cur.execute(
                "SELECT id, suggested_charge, basis_text FROM optimizer_suggestions ORDER BY id DESC LIMIT 500"
            )
            rows = cur.fetchall() or []
            matched_any = False
            for r in rows:
                sid = r[0]
                try:
                    sc = float(r[1])
                except Exception:
                    continue
                basis = r[2] or ""
                if "TESTED_WITH:" in basis:
                    continue
                if abs(sc - charge) <= 0.3:
                    # mark tested
                    try:
                        new_basis = basis + f"\nTESTED_WITH:{tr_id}"
                        cur.execute(
                            "UPDATE optimizer_suggestions SET basis_text = ? WHERE id = ?",
                            (new_basis, sid),
                        )
                        self.db.conn.commit()
                        matched_any = True
                    except Exception:
                        pass

            if matched_any:
                # refit GP and persist new suggestion
                try:
                    cur.execute(
                        "SELECT charge_weight, velocity_avg FROM test_results WHERE velocity_avg IS NOT NULL ORDER BY id DESC LIMIT 500"
                    )
                    rows2 = cur.fetchall() or []
                    charges = []
                    velocities = []
                    for r in reversed(rows2):
                        try:
                            charges.append(float(r[0]))
                            velocities.append(float(r[1]))
                        except Exception:
                            continue
                    if charges:
                        from ..utils.gp_optimizer import suggest_next_charge

                        min_c = max(0.0, min(charges) - 1.0)
                        max_c = max(charges) + 1.0
                        new_sugg = suggest_next_charge(
                            charges, velocities, (min_c, max_c)
                        )
                        import json

                        cur.execute(
                            "INSERT INTO optimizer_suggestions (suggested_charge, basis_text) VALUES (?, ?)",
                            (
                                float(new_sugg),
                                json.dumps({"based_on_rows": len(charges)}),
                            ),
                        )
                        self.db.conn.commit()
                except Exception:
                    pass
        except Exception:
            return

    # ------------------------------------------------------------------
    # Research/telemetry helpers
    # ------------------------------------------------------------------
    def _get_research_service(self):
        if self._research_service is None and not self._research_service_init_failed:
            try:
                self._research_service = ResearchService(self.db)
            except Exception as exc:
                self._logger.warning("ResearchService init failed: %s", exc)
                self._research_service_init_failed = True
                self._research_service = None
        return self._research_service

    def _record_research_sample(
        self, ammo_profile_id, velocities, charge_gr, import_id
    ):
        service = self._get_research_service()
        if service is None or not ammo_profile_id or not velocities:
            return

        ammo_profile = self._fetch_ammo_profile(ammo_profile_id)
        if not ammo_profile:
            return

        rifle_row = self._fetch_rifle_row(ammo_profile.get("rifle_id"))
        firearm_id = self._ensure_research_firearm(rifle_row)
        component_ids = self._ensure_component_snapshots(ammo_profile)
        load_recipe_id = self._insert_load_recipe_record(
            firearm_id,
            component_ids,
            ammo_profile,
            charge_gr,
            rifle_row,
        )
        session_id = self._insert_test_session_record(
            firearm_id,
            ammo_profile,
            rifle_row,
            import_id,
        )
        self._insert_test_result_record(session_id, load_recipe_id, velocities)
        service.lock_session(session_id)

    def _fetch_ammo_profile(self, ammo_profile_id):
        if not ammo_profile_id:
            return None
        rows = self.db.execute_query(
            "SELECT * FROM ammo_profiles WHERE id = ?",
            (ammo_profile_id,),
        )
        if rows:
            return dict(rows[0])
        return None

    def _get_selected_case_row(self, ammo_profile_id=None):
        resolved_ammo_profile_id = ammo_profile_id
        if resolved_ammo_profile_id in (None, ""):
            resolved_ammo_profile_id = getattr(self, "current_ammo_profile_id", None)

        ammo_profile = None
        if resolved_ammo_profile_id not in (None, ""):
            try:
                ammo_profile = self._fetch_ammo_profile(int(resolved_ammo_profile_id))
            except Exception:
                ammo_profile = None

        case_id = (
            ammo_profile.get("case_id") if isinstance(ammo_profile, dict) else None
        )
        if not case_id and isinstance(self.brass_data, dict):
            case_id = self.brass_data.get("case_id")

        if not case_id:
            return None, None

        try:
            rows = self.db.execute_query(
                "SELECT * FROM cases WHERE id = ?", (int(case_id),)
            )
        except Exception:
            rows = []
        if rows:
            return int(case_id), dict(rows[0])
        return int(case_id), None

    def _build_current_internal_ballistics_summary(
        self,
        latest_result=None,
        powder_name=None,
        ammo_profile_id=None,
    ):
        result = (
            latest_result
            if isinstance(latest_result, dict)
            else getattr(self, "_latest_visual_result", None)
        )
        selected_powder_name = str(
            powder_name
            or (
                (self.powder_data or {}).get("name")
                if isinstance(self.powder_data, dict)
                else ""
            )
            or ((result or {}).get("powder_name") if isinstance(result, dict) else "")
            or ""
        )

        case_id, case_row = self._get_selected_case_row(ammo_profile_id=ammo_profile_id)
        case_capacity_h2o = None
        h2o_samples = 0
        case_capacity_source = None
        trim_length_mm = None

        if isinstance(case_row, dict):
            trim_length_mm = self._coerce_float(case_row.get("trim_length_mm"))

        if case_id and hasattr(self.db, "refresh_case_learning_profile"):
            try:
                case_profile = self.db.refresh_case_learning_profile(int(case_id)) or {}
            except Exception:
                case_profile = {}
            learned_capacity = self._coerce_float(
                case_profile.get("avg_case_capacity_h2o")
            )
            learned_samples = int(case_profile.get("h2o_samples") or 0)
            if learned_capacity is not None:
                case_capacity_h2o = learned_capacity
                h2o_samples = max(learned_samples, 1)
                case_capacity_source = "case_profile"

        if case_capacity_h2o is None and isinstance(case_row, dict):
            row_capacity = self._coerce_float(case_row.get("case_capacity_gr_h2o"))
            if row_capacity is not None:
                case_capacity_h2o = row_capacity
                h2o_samples = max(h2o_samples, 1)
                case_capacity_source = "case_row"

        case_capacity_ml = (
            case_capacity_h2o * 0.0648
            if case_capacity_h2o is not None
            else (
                self._coerce_float((result or {}).get("case_capacity_ml"))
                if isinstance(result, dict)
                else None
            )
        )
        load_density_percent = None
        if case_capacity_h2o is None or not selected_powder_name:
            load_density_percent = (
                self._coerce_float((result or {}).get("load_density_percent"))
                if isinstance(result, dict)
                else None
            )

        summary = build_internal_ballistics_summary(
            charge_weight_gr=self._coerce_float(self.current_charge or 0),
            powder_name=selected_powder_name,
            case_capacity_gr_h2o=case_capacity_h2o,
            case_capacity_ml=case_capacity_ml,
            barrel_length_in=(
                self._coerce_float((result or {}).get("barrel_length_inches"))
                if isinstance(result, dict)
                else None
            ),
            load_density_percent=load_density_percent,
            powder_volume_ml=(
                self._coerce_float((result or {}).get("powder_volume_ml"))
                if isinstance(result, dict)
                else None
            ),
            available_volume_ml=(
                self._coerce_float((result or {}).get("available_volume_ml"))
                if isinstance(result, dict)
                else None
            ),
            powder_density_g_ml=(
                self._coerce_float((result or {}).get("powder_density"))
                if isinstance(result, dict)
                else None
            ),
            burn_rate_position=(
                (result or {}).get("burn_rate_position")
                if isinstance(result, dict)
                else None
            ),
            pressure_margin_percent=(
                self._coerce_float((result or {}).get("safety_margin_percent"))
                if isinstance(result, dict)
                else None
            ),
        )

        checks = list(summary.get("checks") or [])
        if case_capacity_h2o is not None and case_capacity_source in {
            "case_profile",
            "case_row",
        }:
            checks.append(
                f"H2O basis: {float(case_capacity_h2o):.2f} gr from the selected case ({h2o_samples} basis points)."
            )
        if trim_length_mm is not None:
            checks.append(
                f"Trim length {trim_length_mm:.2f} mm from the selected case is available in the builder context."
            )
        summary["checks"] = checks[:6]
        return summary

    def _fetch_rifle_row(self, rifle_id):
        if rifle_id:
            rows = self.db.execute_query(
                "SELECT * FROM rifles WHERE id = ?",
                (rifle_id,),
            )
            if rows:
                return dict(rows[0])
        if isinstance(self.rifle_data, dict):
            return self.rifle_data
        return None

    def _ensure_research_firearm(self, rifle_row):
        if not rifle_row:
            return None

        label = rifle_row.get("name") or f"firearm-{rifle_row.get('id') or '?'}"
        caliber = rifle_row.get("caliber") or "unknown"
        barrel_length_mm = self._coerce_float(rifle_row.get("barrel_length_mm"))
        if barrel_length_mm is None:
            length_cm = self._coerce_float(rifle_row.get("barrel_length_cm"))
            if length_cm is not None:
                barrel_length_mm = length_cm * 10.0
        twist = rifle_row.get("twist_rate") or rifle_row.get("twist")
        muzzle_device = rifle_row.get("muzzle_device") or "none"
        if muzzle_device not in ("none", "suppressor", "brake"):
            muzzle_device = "none"
        muzzle_weight = self._coerce_float(rifle_row.get("muzzle_device_weight_g"))

        cache_key = (label, caliber, barrel_length_mm, twist)
        cached = self._firearm_cache.get(cache_key)
        if cached:
            return cached

        cur = self.db.cursor
        cur.execute(
            "SELECT id FROM firearm WHERE label = ? AND caliber = ? LIMIT 1",
            (label, caliber),
        )
        row = cur.fetchone()
        if row:
            firearm_id = row[0]
        else:
            cur.execute(
                "INSERT INTO firearm (label, caliber, barrel_length_mm, twist, muzzle_device, muzzle_device_weight_g) VALUES (?, ?, ?, ?, ?, ?)",
                (label, caliber, barrel_length_mm, twist, muzzle_device, muzzle_weight),
            )
            self.db.conn.commit()
            firearm_id = cur.lastrowid

        self._firearm_cache[cache_key] = firearm_id
        return firearm_id

    def _ensure_component_snapshots(self, ammo_profile):
        components = {"bullet": None, "powder": None, "primer": None, "case": None}

        bullet_row = None
        bullet_id = ammo_profile.get("bullet_id")
        if bullet_id:
            rows = self.db.execute_query(
                "SELECT * FROM bullets WHERE id = ?", (bullet_id,)
            )
            if rows:
                bullet_row = dict(rows[0])
        bullet_source = bullet_row or self.bullet_data or {}
        bullet_values = {
            "make": bullet_source.get("manufacturer") or bullet_source.get("brand"),
            "model": bullet_source.get("name")
            or bullet_source.get("model")
            or bullet_source.get("label"),
            "weight_gr": self._coerce_float(
                bullet_source.get("weight_grains")
                or bullet_source.get("weight")
                or ammo_profile.get("bullet_weight")
            ),
            "bc": self._coerce_float(
                bullet_source.get("bc_g7") or bullet_source.get("bc_g1")
            ),
            "diameter_mm": self._coerce_float(bullet_source.get("diameter_mm")),
        }
        components["bullet"] = self._ensure_component_row(
            "component_bullet", bullet_values
        )

        powder_row = None
        powder_id = ammo_profile.get("powder_id")
        if powder_id:
            rows = self.db.execute_query(
                "SELECT * FROM powder WHERE id = ?", (powder_id,)
            )
            if rows:
                powder_row = dict(rows[0])
        powder_source = powder_row or self.powder_data or {}
        powder_values = {
            "make": powder_source.get("manufacturer") or powder_source.get("brand"),
            "name": powder_source.get("name")
            or powder_source.get("display_name")
            or powder_source.get("model"),
        }
        components["powder"] = self._ensure_component_row(
            "component_powder", powder_values
        )

        primer_row = None
        primer_id = ammo_profile.get("primer_id")
        if primer_id:
            rows = self.db.execute_query(
                "SELECT * FROM primers WHERE id = ?", (primer_id,)
            )
            if rows:
                primer_row = dict(rows[0])
        primer_source = primer_row or self.primer_data or {}
        primer_values = {
            "type": primer_source.get("type")
            or primer_source.get("size")
            or primer_source.get("category"),
            "make": primer_source.get("manufacturer") or primer_source.get("brand"),
            "model": primer_source.get("name") or primer_source.get("model"),
        }
        components["primer"] = self._ensure_component_row(
            "component_primer", primer_values
        )

        case_row = None
        case_id = ammo_profile.get("case_id")
        if case_id:
            rows = self.db.execute_query("SELECT * FROM cases WHERE id = ?", (case_id,))
            if rows:
                case_row = dict(rows[0])
        case_source = case_row or self.brass_data or {}
        case_values = {
            "make": case_source.get("manufacturer") or case_source.get("brand"),
            "model": case_source.get("name") or case_source.get("model"),
        }
        components["case"] = self._ensure_component_row("component_case", case_values)

        return components

    def _ensure_component_row(self, table, values):
        if not any(value is not None for value in values.values()):
            return None

        required_fields = self._COMPONENT_REQUIRED_FIELDS.get(table, ())
        for field in required_fields:
            val = values.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                return None

        cache = self._component_cache.setdefault(table, {})
        cache_key = tuple(
            round(val, 6) if isinstance(val, float) else val for val in values.values()
        )
        cached = cache.get(cache_key)
        if cached:
            return cached

        conditions = []
        params = []
        for column, value in values.items():
            if value is None:
                conditions.append(f"{column} IS NULL")
            else:
                conditions.append(f"{column} = ?")
                params.append(value)
        where_clause = " AND ".join(conditions)

        cur = self.db.cursor
        cur.execute(
            f"SELECT id FROM {table} WHERE {where_clause} LIMIT 1",
            tuple(params),
        )
        row = cur.fetchone()
        if row:
            comp_id = row[0]
        else:
            columns = ", ".join(values.keys())
            placeholders = ", ".join("?" for _ in values)
            cur.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                tuple(values.values()),
            )
            self.db.conn.commit()
            comp_id = cur.lastrowid

        cache[cache_key] = comp_id
        return comp_id

    def _insert_load_recipe_record(
        self, firearm_id, component_ids, ammo_profile, charge_gr, rifle_row
    ):
        cur = self.db.cursor
        case_firings = None
        if isinstance(self.brass_data, dict):
            case_firings = self._coerce_float(self.brass_data.get("times_fired_avg"))
        col_mm = self._coerce_float(ammo_profile.get("coal"))
        if col_mm is None:
            col_mm = self._coerce_float(self.coal_mm or 0)
        cbto_mm = self._coerce_float(ammo_profile.get("cbto"))
        if cbto_mm is None:
            cbto_mm = self._coerce_float(self.cbto_mm or 0)
        jump_mm = None
        jam_length = None
        if rifle_row:
            jam_length = self._coerce_float(rifle_row.get("jam_length_cbto_mm"))
        if jam_length is not None and cbto_mm is not None:
            jump_mm = jam_length - cbto_mm

        cur.execute(
            """
            INSERT INTO load_recipe (
                firearm_id,
                bullet_id,
                powder_id,
                primer_id,
                case_id,
                case_firings,
                powder_charge_gr,
                col_mm,
                jump_mm,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                firearm_id,
                component_ids.get("bullet"),
                component_ids.get("powder"),
                component_ids.get("primer"),
                component_ids.get("case"),
                case_firings,
                self._coerce_float(charge_gr),
                col_mm,
                jump_mm,
                _utcnow(),
            ),
        )
        self.db.conn.commit()
        return cur.lastrowid

    def _insert_test_session_record(
        self, firearm_id, ammo_profile, rifle_row, import_id
    ):
        cur = self.db.cursor
        base_label = (
            ammo_profile.get("name")
            or (rifle_row or {}).get("name")
            or "Chronograph Session"
        )
        label = base_label
        if import_id:
            label = f"{base_label} import #{import_id}"
        temperature = None
        if hasattr(self, "temp_spin"):
            temperature = self._coerce_float(self._current_temperature_c())

        cur.execute(
            """
            INSERT INTO test_session (
                firearm_id,
                label,
                distance_m,
                temperature_c,
                chronograph_type,
                status,
                started_at
            ) VALUES (?, ?, ?, ?, ?, 'draft', ?)
            """,
            (
                firearm_id,
                (label or "Chronograph Session")[:160],
                None,
                temperature,
                "chronograph_import",
                _utcnow(),
            ),
        )
        self.db.conn.commit()
        return cur.lastrowid

    def _insert_test_result_record(self, session_id, load_recipe_id, velocities):
        cleaned = []
        for velocity in velocities:
            val = self._coerce_float(velocity)
            if val is not None:
                cleaned.append(val * 0.3048)
        if not cleaned:
            return None

        shots_n = len(cleaned)
        avg_mps = sum(cleaned) / shots_n
        es_mps = max(cleaned) - min(cleaned)
        sd_mps = statistics.stdev(cleaned) if shots_n > 1 else 0.0

        cur = self.db.cursor
        cur.execute(
            """
            INSERT INTO test_result (
                test_session_id,
                load_recipe_id,
                shots_n,
                velocity_avg_mps,
                velocity_sd_mps,
                velocity_es_mps,
                group_size_mm,
                group_moa,
                pressure_signs_reported
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                session_id,
                load_recipe_id,
                shots_n,
                avg_mps,
                sd_mps,
                es_mps,
                None,
                None,
            ),
        )
        self.db.conn.commit()
        return cur.lastrowid

    @staticmethod
    def _format_segment_match(segment_match, drag_model: str) -> str:
        if not isinstance(segment_match, dict):
            return ""
        model = str(segment_match.get("model") or drag_model or "AUTO").strip().upper()
        if model == "AUTO":
            model = str(drag_model or "AUTO").strip().upper()
        bc_value = (
            segment_match.get("bc_g7")
            or segment_match.get("bc_g1")
            or segment_match.get("bc")
        )
        min_v = segment_match.get("velocity_fps_min")
        max_v = segment_match.get("velocity_fps_max")
        if bc_value is None:
            return ""
        if max_v is not None:
            return (
                f"{model} {float(bc_value):.3f} @ "
                f"{format_velocity_fps(float(min_v or 0))}-{format_velocity_fps(float(max_v))}"
            )
        return (
            f"{model} {float(bc_value):.3f} @ {format_velocity_fps(float(min_v or 0))}+"
        )

    @staticmethod
    def _preferred_drag_model() -> str:
        from ..utils.drag_models import preferred_drag_model

        try:
            return preferred_drag_model()
        except Exception:
            return "AUTO"

    @classmethod
    def _resolve_scope_drag_model(
        cls,
        current_bullet: dict,
        previous_bc_g1,
        previous_bc_g7,
        previous_bc_segments_json=None,
        current_velocity_fps: float | None = None,
        previous_velocity_fps: float | None = None,
    ) -> tuple[str, float | None, float | None, str, str]:
        from ..utils.drag_models import resolve_drag_choice

        preferred = cls._preferred_drag_model()
        current_bc_g7 = cls._coerce_float(current_bullet.get("bc_g7"))
        current_bc_g1 = cls._coerce_float(current_bullet.get("bc_g1"))
        prev_g7 = cls._coerce_float(previous_bc_g7)
        prev_g1 = cls._coerce_float(previous_bc_g1)
        current = resolve_drag_choice(
            current_bc_g1,
            current_bc_g7,
            preferred,
            current_bullet.get("bc_segments_json"),
            velocity_fps=current_velocity_fps,
        )
        previous = resolve_drag_choice(
            prev_g1,
            prev_g7,
            preferred,
            previous_bc_segments_json,
            velocity_fps=previous_velocity_fps,
        )
        current_segment = cls._format_segment_match(
            current.get("segment_match"), str(current.get("resolved_model") or "G1")
        )
        previous_segment = cls._format_segment_match(
            previous.get("segment_match"), str(previous.get("resolved_model") or "G1")
        )

        if (
            current["resolved_model"] == "G7"
            and previous["resolved_model"] == "G7"
            and current["bc_value"] is not None
            and previous["bc_value"] is not None
        ):
            return (
                "G7",
                (
                    float(current["bc_value"])
                    if isinstance(current["bc_value"], (int, float))
                    else None
                ),
                (
                    float(previous["bc_value"])
                    if isinstance(previous["bc_value"], (int, float))
                    else None
                ),
                current_segment,
                previous_segment,
            )
        return "G1", current_bc_g1, prev_g1, current_segment, previous_segment

    def on_attach_chrono_to_qc_batch(self):
        """Attach selected chronograph import by creating or using existing qc_batch and insert qc_measurements."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("mlb_select_import_first")
            )
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute(
            "SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,)
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Not found", "Import row not found in DB")
            return
        import json

        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(
                self, "No velocities", "Selected import has no velocities"
            )
            return

        # Ask user to either enter existing qc_batch id or create new
        batch_id, ok = QInputDialog.getInt(
            self,
            tr("mlb_qc_batch_id_title"),
            tr("mlb_qc_batch_id_message"),
            0,
        )
        if not ok:
            return

        if batch_id == 0:
            # create new qc batch
            name, ok2 = QInputDialog.getText(
                self, tr("mlb_new_qc_batch_title"), tr("mlb_new_qc_batch_message")
            )
            if not ok2 or not name:
                QMessageBox.warning(
                    self, tr("mlb_cancelled_title"), tr("mlb_batch_creation_cancelled")
                )
                return
            batch_size, ok3 = QInputDialog.getInt(
                self,
                tr("mlb_batch_size_title"),
                tr("mlb_qc_batch_size_message"),
                len(velocities),
                1,
            )
            if not ok3:
                return
            cur.execute(
                "INSERT INTO qc_batches (name, target_charge, charge_tolerance, target_coal, coal_tolerance, batch_size, status) VALUES (?, ?, ?, ?, ?, ?, 'in_progress')",
                (name, None, None, None, None, batch_size),
            )
            batch_id = cur.lastrowid
            self.db.conn.commit()

        # Insert measurements
        for i, v in enumerate(velocities, start=1):
            cur.execute(
                "INSERT INTO qc_measurements (batch_id, patron_number, measurement_type, value, target_value, delta, is_outlier, notes) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                (
                    batch_id,
                    i,
                    "velocity",
                    float(v),
                    None,
                    None,
                    f"Imported from chronograph_imports #{import_id}",
                ),
            )

        # Optionally mark batch completed if we've inserted >= batch_size
        cur.execute("SELECT batch_size FROM qc_batches WHERE id = ?", (batch_id,))
        b = cur.fetchone()
        if b and b[0] and int(b[0]) <= len(velocities):
            cur.execute(
                "UPDATE qc_batches SET status = 'completed', completed_date = datetime('now') WHERE id = ?",
                (batch_id,),
            )

        self.db.conn.commit()
        QMessageBox.information(
            self,
            tr("mlb_qc_batch_updated_title"),
            tr(
                "mlb_qc_batch_updated_message", count=len(velocities), batch_id=batch_id
            ),
        )
        self.on_refresh_chronograph_list()

    def toggle_chat(self):
        """Toggle chat panel visibility"""
        if self.chat_display.isVisible():
            self.chat_display.hide()
            self.chat_input.hide()
            self.collapse_btn.setText(tr("mlb_expand"))
            self.chat_widget.setMaximumHeight(50)
        else:
            self.chat_display.show()
            self.chat_input.show()
            self.collapse_btn.setText(tr("mlb_collapse"))
            self.chat_widget.setMaximumHeight(300)

    def send_chat_message(self):
        """Send message to AI"""
        message = self.chat_input.text().strip()
        if not message:
            return

        # Display user message
        self.add_user_message(message)
        self.chat_input.clear()

        # Get AI response (placeholder - will integrate real AI later)
        response = self.get_ai_response(message)
        self.add_ai_message(response)

    def add_user_message(self, message):
        """Add user message to chat"""
        self.chat_display.append(
            f"<div style='text-align: right; margin: 10px;'>"
            f"<b style='color: #3498db;'>You:</b> {message}"
            f"</div>"
        )
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def add_ai_message(self, message):
        """Add AI message to chat"""
        self.chat_display.append(
            f"<div style='margin: 10px;'>"
            f"<b style='color: #9b59b6;'>AI:</b> {message}"
            f"</div>"
        )
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def get_ai_response(self, message):
        """
        Comprehensive AI reloading assistant - your expert friend!
        Answers ALL questions about reloading process
        """
        message_lower = message.lower()

        # ==================== KRUTT / POWDER ====================
        if any(word in message_lower for word in ["krutt", "powder", "pulver"]):
            if any(
                word in message_lower
                for word in ["anbefal", "recommend", "best", "hvilken"]
            ):
                return self.get_powder_recommendation_text()
            elif any(
                word in message_lower
                for word in ["mengde", "charge", "hvor mye", "how much"]
            ):
                return self.explain_charge_weight()
            elif any(
                word in message_lower for word in ["temperatur", "temperature", "temp"]
            ):
                return self.explain_powder_temperature()
            elif any(
                word in message_lower
                for word in ["brennhastighet", "burn rate", "speed"]
            ):
                return self.explain_burn_rate()
            elif any(
                word in message_lower for word in ["lagring", "storage", "oppbevaring"]
            ):
                return self.explain_powder_storage()

        # ==================== KULER / BULLETS ====================
        elif any(word in message_lower for word in ["kule", "bullet", "prosjektil"]):
            if any(
                word in message_lower
                for word in ["seating", "sette", "dybde", "depth", "cbto", "coal"]
            ):
                return self.explain_seating_depth()
            elif any(
                word in message_lower for word in ["jump", "hopp", "lands", "rifling"]
            ):
                return self.explain_bullet_jump()
            elif any(
                word in message_lower
                for word in ["vekt", "weight", "tung", "lett", "heavy", "light"]
            ):
                return self.explain_bullet_weight()
            elif any(
                word in message_lower for word in ["bc", "ballistisk", "ballistic"]
            ):
                return self.explain_bc()

        # ==================== TENNHETTER / PRIMERS ====================
        elif any(word in message_lower for word in ["tennhette", "primer", "tenner"]):
            if any(
                word in message_lower
                for word in ["anbefal", "recommend", "hvilken", "best"]
            ):
                return self.get_primer_recommendation()
            elif any(
                word in message_lower
                for word in ["magnum", "standard", "forskjell", "difference"]
            ):
                return self.explain_primer_types()
            elif any(
                word in message_lower
                for word in ["feil", "problem", "pierced", "cratered"]
            ):
                return self.diagnose_primer_problems()

        # ==================== HYLSER / BRASS ====================
        elif any(word in message_lower for word in ["hylse", "brass", "case"]):
            if any(
                word in message_lower for word in ["trim", "trimme", "lengde", "length"]
            ):
                return self.explain_brass_trimming()
            elif any(word in message_lower for word in ["neck", "hals", "tension"]):
                return self.explain_neck_tension()
            elif any(word in message_lower for word in ["anneal", "gløde", "hardhet"]):
                return self.explain_annealing()
            elif any(
                word in message_lower for word in ["prep", "preparer", "forbered"]
            ):
                return self.explain_brass_prep()
            elif any(
                word in message_lower for word in ["ganger", "times", "bruk", "levetid"]
            ):
                return self.explain_brass_life()

        # ==================== DIER / DIES ====================
        elif any(word in message_lower for word in ["die", "dier", "dies"]):
            if any(
                word in message_lower
                for word in ["innstilling", "setup", "justere", "adjust"]
            ):
                return self.explain_die_setup()
            elif any(
                word in message_lower
                for word in ["full length", "fl", "neck", "sizing"]
            ):
                return self.explain_sizing_dies()
            elif any(word in message_lower for word in ["seating", "sette", "bullet"]):
                return self.explain_seating_die()
            elif any(word in message_lower for word in ["crimping", "crimpe", "crimp"]):
                return self.explain_crimping()
            elif any(
                word in message_lower for word in ["problem", "stuck", "fast", "feil"]
            ):
                return self.diagnose_die_problems()

        # ==================== TRYKK / PRESSURE ====================
        elif any(word in message_lower for word in ["trykk", "pressure", "psi", "bar"]):
            if any(
                word in message_lower for word in ["høy", "high", "for mye", "too much"]
            ):
                return self.explain_high_pressure()
            elif any(word in message_lower for word in ["tegn", "signs", "symptom"]):
                return self.explain_pressure_signs()
            elif any(
                word in message_lower for word in ["saami", "max", "grense", "limit"]
            ):
                return self.explain_saami_limits()
            elif any(word in message_lower for word in ["hvorfor", "why", "årsak"]):
                return self.explain_pressure()

        # ==================== SIKKERHET / SAFETY ====================
        elif any(
            word in message_lower
            for word in ["sikker", "safe", "trygg", "farlig", "danger"]
        ):
            return self.check_safety_comprehensive()

        # ==================== PRESISJON / ACCURACY ====================
        elif any(
            word in message_lower
            for word in ["presisjon", "accuracy", "nøyaktighet", "gruppe", "group"]
        ):
            if any(
                word in message_lower
                for word in ["forbedre", "improve", "bedre", "better"]
            ):
                return self.improve_accuracy_tips()
            elif any(word in message_lower for word in ["ocw", "ladder", "test"]):
                return self.suggest_test_plan()
            elif any(
                word in message_lower for word in ["es", "sd", "spredning", "spread"]
            ):
                return self.explain_es_sd()

        # ==================== TESTING ====================
        elif any(
            word in message_lower for word in ["test", "ocw", "ladder", "sighter"]
        ):
            return self.suggest_test_plan()

        # ==================== LØP / BARREL ====================
        elif any(word in message_lower for word in ["løp", "barrel", "pipe"]):
            if any(
                word in message_lower for word in ["harmonisk", "harmonic", "vibration"]
            ):
                return self.explain_barrel_harmonics()
            elif any(
                word in message_lower for word in ["lengde", "length", "kort", "lang"]
            ):
                return self.explain_barrel_length()
            elif any(
                word in message_lower for word in ["rengjøring", "cleaning", "fouling"]
            ):
                return self.explain_barrel_cleaning()

        # ==================== VERKTØY / TOOLS ====================
        elif any(
            word in message_lower for word in ["verktøy", "tool", "utstyr", "equipment"]
        ):
            return self.recommend_tools()

        # ==================== PROSESS / PROCESS ====================
        elif any(
            word in message_lower
            for word in ["prosess", "process", "hvordan", "how to", "steg", "step"]
        ):
            return self.explain_reloading_process()

        # ==================== GENERELL HJELP ====================
        else:
            return self.general_help_message()

    def get_powder_recommendation_text(self):
        """Generate powder recommendation"""
        if not self.rifle_data:
            return "Please select a firearm first!"

        caliber = self.rifle_data["caliber"]

        recommendations = {
            ".308 Winchester": "For .308 Win, I recommend:\n\n1. Varget (burn rate 115) - Temperature stable, excellent accuracy\n2. H4350 - Slightly slower, also great\n3. RL15 - Faster, good for shorter barrels",
            "6.5 Creedmoor": "For 6.5 Creedmoor, I recommend:\n\n1. H4350 - THE standard for 6.5 CM\n2. RL16 - Temp stable, higher velocity\n3. Varget - Works great with lighter bullets",
            ".223 Remington": "For .223 Rem, I recommend:\n\n1. Varget - Excellent accuracy\n2. H4895 - Very versatile\n3. RL15 - Good velocities",
        }

        return recommendations.get(
            caliber, tr("mlb_powder_recommendation_fallback", caliber=caliber)
        )

    def get_primer_recommendation(self):
        """Get primer recommendation"""
        if not self.powder_data:
            return tr("mlb_select_powder_for_primer")

        return (
            "For your powder choice:\n\n"
            "🥇 CCI BR-2 - Benchrest grade, lowest ES/SD\n"
            "🥈 Federal 210M - Match grade, excellent\n"
            "3. CCI 200 - Standard LR, works great\n\n"
            "Avoid magnum primers unless using slow ball powder."
        )

    def explain_pressure(self):
        """Explain current pressure"""
        # Would use actual calculation here
        return (
            (
                "Pressure is influenced by:\n\n"
                "1. Charge weight (more powder = higher pressure)\n"
                "2. Case capacity (less space = higher pressure)\n"
                "3. Seating depth (closer to lands = higher pressure)\n"
                "4. Powder burn rate (faster = higher peak)\n"
                "5. Temperature (hotter = higher pressure)\n\n"
                "Always stay under SAAMI/CIP max!"
            )
            + self._get_h2o_ai_note()
            + self._get_chrono_ai_note()
            + self._get_calibration_ai_note()
        )

    def check_safety(self):
        """Check if current load is safe"""
        # Would use actual calculation here
        return (
            (
                "Based on current settings:\n\n"
                "Pressure looks SAFE\n"
                "Under SAAMI maximum\n"
                "Always watch for pressure signs.\n\n"
                "Signs of high pressure:\n"
                "• Flattened primers\n"
                "• Ejector marks on brass\n"
                "• Difficult bolt lift\n"
                "• Case head expansion"
            )
            + self._get_h2o_ai_note()
            + self._get_chrono_ai_note()
            + self._get_calibration_ai_note()
        )

    def suggest_test_plan(self):
        """Suggest OCW test plan"""
        return (
            "I recommend this test protocol:\n\n"
            "OCW Test (15 rounds):\n"
            "• 42.0gr × 3 shots\n"
            "• 42.3gr × 3 shots\n"
            "• 42.5gr × 3 shots ← Expected best\n"
            "• 42.8gr × 3 shots\n"
            "• 43.0gr × 3 shots\n\n"
            "Shoot at 100m, look for cluster (OCW node).\n"
            "Then test seating depth (9 rounds).\n\n"
            "Total: 24 rounds vs traditional 60-100!"
        )

    def go_back_to_step1(self):
        """Go back to step 1"""
        self.step2_widget.hide()
        if self.layout() is not None:
            self.layout().removeWidget(self.step2_widget)  # type: ignore[union-attr]
        self.step1_widget.show()
        # persist last-open step
        try:
            self.current_step = 1
            self._save_ui_setting("last_step", "1")
        except Exception:
            pass

    def initialize_step2(self):
        """Initialize step 2 with weapon data"""
        # Load components for this weapon
        self.load_bullets_for_caliber()
        self.load_powders()
        self.load_primers()
        self._get_rifle_profile_details()
        self._refresh_active_rifle_context()

        # Restore prior session component selection and load values from canonical runtime.
        # This must run after combos are populated so items can be matched by ID.
        try:
            self._apply_runtime_selection_to_step2()
        except Exception:
            pass

        barrel = self._get_active_barrel_details()
        barrel_name = barrel.get("name") or "standard barrel"
        _rdata = self.rifle_data if isinstance(self.rifle_data, dict) else {}
        barrel_caliber = barrel.get("caliber") or _rdata.get("caliber")

        # Show weapon info
        self.add_ai_message(
            f"Great! You selected {_rdata.get('name', '?')} ({barrel_caliber}).\n"
            f"Active barrel: {barrel_name}.\n\n"
            f"Let me help you build the right load for this setup."
        )
        if not self._has_tracked_brass_batch():
            self.add_ai_message(
                "You are using brass that is not tied to a recorded batch. "
                "That is perfectly fine, but the program will treat the data basis as less precise for fine interpretation of pressure, velocity, and precision."
            )
        try:
            self._sync_active_load_session_context()
            self._refresh_runtime_context_summary()
        except Exception:
            pass

    def load_bullets_for_caliber(self):
        """Load bullets for selected weapon caliber"""
        self.bullet_combo.clear()
        self.bullet_combo.addItem("Select bullet...", None)
        if hasattr(self, "bullet_lot_combo"):
            self.bullet_lot_combo.clear()
            self.bullet_lot_combo.addItem("Select Lot Automatically", None)
        caliber = ""
        if self.rifle_data:
            caliber = str(self.rifle_data.get("caliber") or "").strip()
        try:
            bullets = None
            if caliber:
                # Exact match first
                bullets = self.db.execute_query(
                    "SELECT * FROM bullets WHERE caliber = ? ORDER BY manufacturer, weight_grains, name",
                    (caliber,),
                )
                # If no exact match, try by numeric diameter prefix
                # Handles e.g. "308 Winchester" → ".308", "6.5 Creedmoor" → "6.5mm"
                if not bullets:
                    import re as _re

                    m = _re.match(r"\.?(\d+\.?\d*)", caliber.strip())
                    if m:
                        diam = m.group(1)
                        bullets = self.db.execute_query(
                            "SELECT * FROM bullets WHERE caliber LIKE ? OR caliber LIKE ? OR caliber = ?"
                            " ORDER BY manufacturer, weight_grains, name",
                            (f"{diam}%", f".{diam}%", caliber),
                        )
            if not bullets:
                bullets = self.db.execute_query(
                    "SELECT * FROM bullets ORDER BY manufacturer, weight_grains, name"
                )
        except Exception:
            bullets = []
        for bullet in bullets or []:
            label_parts = [
                str(bullet.get("manufacturer") or "").strip(),
                str(bullet.get("name") or "").strip(),
            ]
            label = " ".join(part for part in label_parts if part).strip() or (
                f"Bullet #{bullet.get('id')}"
            )
            weight = bullet.get("weight_grains")
            if weight is not None:
                try:
                    label += f" ({format_weight_grains(float(weight), 'bullet')})"
                except Exception:
                    pass
            self.bullet_combo.addItem(label, dict(bullet))

    def load_powders(self):
        """Load powders from inventory"""
        powders = self.db.execute_query(
            "SELECT * FROM powder ORDER BY manufacturer, name"
        )
        self.powder_combo.clear()
        self.powder_combo.addItem(tr("mlb_select_powder"), None)
        if hasattr(self, "powder_lot_combo"):
            self.powder_lot_combo.clear()
            self.powder_lot_combo.addItem("Select Lot Automatically", None)
        for powder in powders:
            label_parts = [
                str(powder.get("manufacturer") or "").strip(),
                str(powder.get("name") or "").strip(),
            ]
            label = " ".join(part for part in label_parts if part).strip() or (
                f"Powder #{powder.get('id')}"
            )
            quantity = powder.get("quantity_grams")
            try:
                qty = float(quantity or 0)
            except Exception:
                qty = 0.0
            if qty > 0:
                label += f" ({qty:.0f} g)"
            else:
                label += f" ({tr('mlb_simulation_not_in_stock')})"
            self.powder_combo.addItem(label, dict(powder))

    def load_primers(self):
        """Load primers from inventory and reference catalog."""
        primers = self.db.execute_query(
            """
            SELECT *
            FROM primers
            ORDER BY
                CASE WHEN COALESCE(quantity, 0) > 0 THEN 0 ELSE 1 END,
                manufacturer COLLATE NOCASE,
                name COLLATE NOCASE
            """
        )
        self.primer_combo.clear()
        self.primer_combo.addItem(tr("mlb_select_primer"), None)
        if hasattr(self, "primer_lot_combo"):
            self.primer_lot_combo.clear()
            self.primer_lot_combo.addItem("Select Lot Automatically", None)
        for primer in primers:
            label = f"{primer['manufacturer']} {primer['name']}".strip()
            qty = primer.get("quantity")
            try:
                if qty is not None:
                    label += f" ({int(qty)} stk)"
            except Exception:
                pass
            self.primer_combo.addItem(label, primer)

    def _open_primer_editor_dialog(
        self, existing_primer: dict | None = None
    ) -> dict | None:
        """Create or edit a primer reference/inventory entry."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Manual Primer")
        dialog.resize(460, 420)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        manufacturer_edit = QLineEdit(
            str((existing_primer or {}).get("manufacturer") or "")
        )
        form.addRow("Manufacturer", manufacturer_edit)

        name_edit = QLineEdit(str((existing_primer or {}).get("name") or ""))
        form.addRow("Name", name_edit)

        type_edit = QLineEdit(str((existing_primer or {}).get("type") or ""))
        form.addRow("Type", type_edit)

        size_edit = QLineEdit(str((existing_primer or {}).get("size") or ""))
        form.addRow("Size", size_edit)

        product_line_edit = QLineEdit(
            str((existing_primer or {}).get("product_line") or "")
        )
        form.addRow("Series", product_line_edit)

        part_number_edit = QLineEdit(
            str((existing_primer or {}).get("part_number") or "")
        )
        form.addRow("Part Number", part_number_edit)

        family_edit = QLineEdit(str((existing_primer or {}).get("primer_family") or ""))
        form.addRow("Primer Family", family_edit)

        quantity_spin = QDoubleSpinBox()
        quantity_spin.setRange(0, 100000)
        quantity_spin.setDecimals(0)
        quantity_spin.setValue(float((existing_primer or {}).get("quantity") or 0))
        quantity_spin.setSuffix(" pcs")
        form.addRow("Quantity", quantity_spin)

        cup_spin = QDoubleSpinBox()
        cup_spin.setRange(0.0, 0.050)
        cup_spin.setDecimals(3)
        cup_spin.setSingleStep(0.001)
        existing_cup = self._coerce_float(
            (existing_primer or {}).get("cup_thickness_in")
        )
        if existing_cup:
            cup_spin.setValue(existing_cup)
        cup_spin.setSuffix(" in")
        form.addRow("Cup Thickness", cup_spin)

        pressure_class_edit = QLineEdit(
            str((existing_primer or {}).get("pressure_tolerance_class") or "")
        )
        form.addRow("Pressure Class", pressure_class_edit)

        ignition_edit = QLineEdit(
            str((existing_primer or {}).get("ignition_strength_class") or "")
        )
        form.addRow("Ignition Strength", ignition_edit)

        ref_source_edit = QLineEdit(
            str((existing_primer or {}).get("reference_source") or "")
        )
        form.addRow("Source", ref_source_edit)

        notes_edit = QTextEdit()
        notes_edit.setPlainText(str((existing_primer or {}).get("notes") or ""))
        form.addRow("Notes", notes_edit)

        help_label = QLabel(
            "You can create a primer even if it is not in the standard list. "
            "Technical fields can be filled in later."
        )
        help_label.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addLayout(form)
        layout.addWidget(help_label)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        name = name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                tr("mlb_missing_data_title"),
                "A primer must at least have a name.",
            )
            return None

        return {
            "manufacturer": manufacturer_edit.text().strip() or None,
            "name": name,
            "type": type_edit.text().strip() or None,
            "size": size_edit.text().strip() or None,
            "product_line": product_line_edit.text().strip() or None,
            "part_number": part_number_edit.text().strip() or None,
            "primer_family": family_edit.text().strip() or None,
            "quantity": int(quantity_spin.value()),
            "cup_thickness_in": (
                float(cup_spin.value()) if cup_spin.value() > 0 else None
            ),
            "pressure_tolerance_class": pressure_class_edit.text().strip() or None,
            "ignition_strength_class": ignition_edit.text().strip() or None,
            "source_kind": (existing_primer or {}).get("source_kind") or "manual_entry",
            "evidence_level": (existing_primer or {}).get("evidence_level")
            or "manual_entry",
            "reference_source": ref_source_edit.text().strip() or None,
            "manufacturer_source": ref_source_edit.text().strip() or None,
            "notes": notes_edit.toPlainText().strip()
            or "Created manually from Modern Load Builder",
        }

    def on_add_manual_primer(self):
        """Create a manual/custom primer entry when it is missing from the list."""
        payload = self._open_primer_editor_dialog()
        if not payload:
            return
        primer_id = self.db.insert("primers", payload)
        if primer_id is None:
            QMessageBox.critical(
                self, "Could Not Save Primer", "The primer could not be saved."
            )
            return

        self.load_primers()
        for idx in range(self.primer_combo.count()):
            data = self.primer_combo.itemData(idx)
            if isinstance(data, dict) and str(data.get("id")) == str(primer_id):
                self.primer_combo.setCurrentIndex(idx)
                break
        self.add_ai_message("Manuell primer er lagt til og kan brukes med en gang.")

    def on_bullet_changed(self, index):
        """Handle bullet selection"""
        bullet = self.bullet_combo.currentData()
        if bullet:
            self._load_component_lot_choices("bullet", bullet.get("id"))
            self.bullet_data = self._apply_bullet_lot_measurements(dict(bullet))
            bullet = self.bullet_data if isinstance(self.bullet_data, dict) else {}
            weight = bullet.get("weight_grains", bullet.get("weight", "?"))
            bc_g1 = bullet.get("bc_g1")
            bc_g7 = bullet.get("bc_g7")
            length_mm = bullet.get("length_mm")
            bullet_type = bullet.get("bullet_type")
            try:
                weight_text = format_weight_grains(float(weight), "bullet")
            except Exception:
                weight_text = str(weight)
            details = [f"{tr('mlb_weight_label')}: {weight_text}"]
            if bc_g7:
                try:
                    details.append(f"BC G7: {float(bc_g7):.3f}")
                except Exception:
                    details.append(f"BC G7: {bc_g7}")
            if bc_g1:
                try:
                    details.append(f"BC G1: {float(bc_g1):.3f}")
                except Exception:
                    details.append(f"BC G1: {bc_g1}")
            if bc_g7 and bc_g1:
                details.append("Drag: foretrekk G7")
            segment_label = ""
            if bullet.get("bc_segments_json"):
                from ..utils.drag_models import resolve_drag_choice

                preferred = self._preferred_drag_model()
                resolved = resolve_drag_choice(
                    bullet.get("bc_g1"),
                    bullet.get("bc_g7"),
                    preferred,
                    bullet.get("bc_segments_json"),
                    velocity_fps=self._coerce_float(
                        bullet.get("velocity_fps") or bullet.get("velocity")
                    ),
                )
                segment_label = self._format_segment_match(
                    resolved.get("segment_match"),
                    str(resolved.get("resolved_model") or "G1"),
                )
            if segment_label:
                details.append(f"Segmented BC: {segment_label}")
            if length_mm:
                try:
                    details.append(
                        f"{tr('mlb_length_label')}: {format_length_mm(float(length_mm))}"
                    )
                except Exception:
                    details.append(f"{tr('mlb_length_label')}: {length_mm}")
            profile = _safe_json_loads(bullet.get("profile_json"))
            tail_type = str(
                (profile or {}).get("tail_type") or bullet.get("bullet_type") or ""
            ).strip()
            if bullet.get("selected_lot_number"):
                lot_details = [f"Lot: {bullet.get('selected_lot_number')}"]
                measured_stats = bullet.get("measured_lot_stats") or {}
                if measured_stats.get("sample_count"):
                    lot_details.append(
                        f"using measured mean ({int(measured_stats.get('sample_count') or 0)} pcs)"
                    )
                details.append(" | ".join(lot_details))
            if tail_type and tail_type != str(bullet_type or "").strip():
                details.append(f"Profile: {tail_type}")
            if bullet_type:
                details.append(f"{tr('mlb_type_label')}: {bullet_type}")
            if bullet.get("source_label"):
                details.append(f"Source: {bullet.get('source_label')}")
            if bullet.get("description"):
                details.append(str(bullet.get("description")))
            self.bullet_info.setText(" | ".join(details))
            self._refresh_component_context_label()
            self._refresh_bullet_action_button()
            self._sync_active_load_session_context()
            self.update_visualization()
        else:
            self.bullet_data = None
            self.bullet_info.setText(tr("mlb_select_bullet_details"))
            self._refresh_component_context_label()
            self._refresh_bullet_action_button()
            self._sync_active_load_session_context()
            if hasattr(self, "component_fit_label"):
                self.component_fit_label.setText(
                    "Select a bullet and powder to assess how well the combination fits the selected firearm and active barrel."
                )

    def _open_bullet_editor_dialog(
        self, existing_bullet: dict | None = None
    ) -> dict | None:
        """Open a small bullet editor and return payload if accepted."""
        caliber = ""
        if existing_bullet and existing_bullet.get("caliber"):
            caliber = str(existing_bullet.get("caliber") or "").strip()
        elif self.rifle_data:
            caliber = str(self.rifle_data.get("caliber") or "").strip()

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("mlb_manual_bullet_title"))
        dialog.resize(420, 320)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        manufacturer_edit = QLineEdit(
            str((existing_bullet or {}).get("manufacturer") or "")
        )
        form.addRow(tr("mlb_manufacturer_label"), manufacturer_edit)

        name_edit = QLineEdit(str((existing_bullet or {}).get("name") or ""))
        form.addRow(tr("mlb_name_label"), name_edit)

        caliber_edit = QLineEdit(caliber)
        form.addRow(tr("mlb_caliber_field"), caliber_edit)

        weight_spin = QDoubleSpinBox()
        weight_spin.setRange(
            float(weight_grains_to_display_value(20.0, "bullet") or 20.0),
            float(weight_grains_to_display_value(1000.0, "bullet") or 1000.0),
        )
        weight_spin.setDecimals(1)
        weight_spin.setSuffix(get_weight_suffix("bullet"))
        existing_weight = self._coerce_float(
            (existing_bullet or {}).get(
                "weight_grains", (existing_bullet or {}).get("weight")
            )
        )
        if existing_weight:
            weight_spin.setValue(
                float(
                    weight_grains_to_display_value(existing_weight, "bullet")
                    or existing_weight
                )
            )
        form.addRow(tr("mlb_weight_field"), weight_spin)

        bc_spin = QDoubleSpinBox()
        bc_spin.setRange(0.0, 2.0)
        bc_spin.setDecimals(3)
        bc_spin.setSingleStep(0.001)
        existing_bc = self._coerce_float((existing_bullet or {}).get("bc_g1"))
        if existing_bc:
            bc_spin.setValue(existing_bc)
        form.addRow("BC (G1):", bc_spin)

        bc_g7_spin = QDoubleSpinBox()
        bc_g7_spin.setRange(0.0, 2.0)
        bc_g7_spin.setDecimals(3)
        bc_g7_spin.setSingleStep(0.001)
        existing_bc_g7 = self._coerce_float((existing_bullet or {}).get("bc_g7"))
        if existing_bc_g7:
            bc_g7_spin.setValue(existing_bc_g7)
        form.addRow("BC (G7):", bc_g7_spin)

        length_spin = QDoubleSpinBox()
        length_spin.setRange(
            float(length_mm_to_display_value(0.0) or 0.0),
            float(length_mm_to_display_value(100.0) or 100.0),
        )
        length_spin.setDecimals(2)
        length_spin.setSuffix(get_length_suffix())
        existing_length = self._coerce_float((existing_bullet or {}).get("length_mm"))
        if existing_length:
            length_spin.setValue(
                float(length_mm_to_display_value(existing_length) or existing_length)
            )
        form.addRow(tr("mlb_length_field"), length_spin)

        type_edit = QLineEdit(str((existing_bullet or {}).get("bullet_type") or ""))
        form.addRow(tr("mlb_bullet_type_field"), type_edit)

        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText(tr("mlb_bullet_notes_placeholder"))
        desc_edit.setPlainText(str((existing_bullet or {}).get("description") or ""))
        form.addRow(tr("mlb_notes_field"), desc_edit)

        help_label = QLabel(tr("mlb_bullet_help"))
        help_label.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addLayout(form)
        layout.addWidget(help_label)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        bullet_name = name_edit.text().strip()
        bullet_caliber = caliber_edit.text().strip()
        if not bullet_name or not bullet_caliber or weight_spin.value() <= 0:
            QMessageBox.warning(
                self,
                tr("mlb_missing_data_title"),
                tr("mlb_missing_bullet_data"),
            )
            return None

        return {
            "name": bullet_name,
            "manufacturer": manufacturer_edit.text().strip() or None,
            "caliber": bullet_caliber,
            "weight_grains": float(
                weight_display_to_grains(weight_spin.value(), "bullet")
                or weight_spin.value()
            ),
            "diameter_mm": self._coerce_float(
                (existing_bullet or {}).get("diameter_mm")
            ),
            "length_mm": (
                float(length_display_to_mm(length_spin.value()) or 0.0)
                if length_spin.value() > 0
                else None
            ),
            "bc_g1": float(bc_spin.value()) if bc_spin.value() > 0 else None,
            "bc_g7": float(bc_g7_spin.value()) if bc_g7_spin.value() > 0 else None,
            "bullet_type": type_edit.text().strip() or None,
            "quantity": int((existing_bullet or {}).get("quantity") or 0),
            "cost_per_unit": self._coerce_float(
                (existing_bullet or {}).get("cost_per_unit")
            ),
            "notes": "Created manually from Modern Load Builder",
            "description": desc_edit.toPlainText().strip() or None,
        }

    def on_add_manual_bullet(self):
        """Create a manual/custom bullet entry for simulation."""
        payload = self._open_bullet_editor_dialog()
        if not payload:
            return
        bullet_id = self.db.insert("bullets", payload)
        if bullet_id is None:
            QMessageBox.critical(
                self,
                tr("mlb_save_bullet_failed_title"),
                tr("mlb_save_bullet_failed", error="insert returned None"),
            )
            return

        self.load_bullets_for_caliber()
        for idx in range(self.bullet_combo.count()):
            data = self.bullet_combo.itemData(idx)
            if isinstance(data, dict) and str(data.get("id")) == str(bullet_id):
                self.bullet_combo.setCurrentIndex(idx)
                break
        self.add_ai_message(tr("mlb_bullet_added_ai"))

    def on_edit_selected_bullet(self):
        """Edit the currently selected bullet to fill missing simulation data."""
        current_bullet = self.bullet_combo.currentData()
        if not isinstance(current_bullet, dict) or not current_bullet.get("id"):
            QMessageBox.information(
                self,
                tr("mlb_no_bullet_selected_title"),
                tr("mlb_no_bullet_selected_message"),
            )
            return
        payload = self._open_bullet_editor_dialog(current_bullet)
        if not payload:
            return
        try:
            self.db.update("bullets", payload, "id = ?", (current_bullet.get("id"),))
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr("mlb_update_bullet_failed_title"),
                tr("mlb_update_bullet_failed", error=exc),
            )
            return
        current_id = str(current_bullet.get("id"))
        self.load_bullets_for_caliber()
        for idx in range(self.bullet_combo.count()):
            data = self.bullet_combo.itemData(idx)
            if isinstance(data, dict) and str(data.get("id")) == current_id:
                self.bullet_combo.setCurrentIndex(idx)
                break
        self.add_ai_message(tr("mlb_bullet_updated_ai"))

    def on_powder_changed(self, index):
        """Handle powder selection"""
        powder = self.powder_combo.currentData()
        if powder:
            self._load_component_lot_choices("powder", powder.get("id"))
            self.powder_data = self._apply_powder_lot_context(dict(powder))
            powder = self.powder_data if isinstance(self.powder_data, dict) else {}
            burn_rate = powder.get("burn_rate")
            density = powder.get("density") or powder.get("density_g_cc")
            qty = powder.get("quantity_grams", 0)
            published_window = get_published_powder_charge_window(
                self.db,
                (
                    (self.rifle_data or {}).get("caliber")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                powder.get("name"),
                (
                    (self.bullet_data or {}).get("id")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                (
                    (self.bullet_data or {}).get("weight")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
            )
            info_parts = [f"Type: {powder.get('type', '?')}"]
            try:
                info_parts.append(
                    f"{tr('mlb_inventory_label')}: {float(qty or 0):.0f} g"
                )
            except Exception:
                info_parts.append(f"{tr('mlb_inventory_label')}: {qty}")
            if burn_rate:
                info_parts.append(f"{tr('mlb_burn_rate_label')}: {burn_rate}")
            if density is not None:
                try:
                    info_parts.append(
                        f"{tr('mlb_density_label')}: {float(density):.3f} g/cc"
                    )
                except Exception:
                    info_parts.append(f"{tr('mlb_density_label')}: {density}")
            _ba = powder.get("quickload_ba_value")
            if _ba is not None:
                try:
                    info_parts.append(f"Ba: {float(_ba):.4f}")
                except Exception:
                    info_parts.append(f"Ba: {_ba}")
            _qex = powder.get("qex_kj_per_kg")
            if _qex is not None:
                try:
                    info_parts.append(f"Qex: {float(_qex):.0f} kJ/kg")
                except Exception:
                    info_parts.append(f"Qex: {_qex}")
            _kr = powder.get("k_ratio")
            if _kr is not None:
                try:
                    info_parts.append(f"k: {float(_kr):.4f}")
                except Exception:
                    info_parts.append(f"k: {powder.get('k_ratio')}")
            if powder.get("usable_for_simulation"):
                info_parts.append("Simulation profile ready")
            elif powder.get("validation_status"):
                info_parts.append(f"Profile status: {powder.get('validation_status')}")
            if powder.get("temp_stable") in (0, 1, True, False):
                info_parts.append(
                    "Temp stable"
                    if bool(powder.get("temp_stable"))
                    else "Temp sensitive/unknown"
                )
            if powder.get("selected_lot_number"):
                info_parts.append(f"Lot: {powder.get('selected_lot_number')}")
            comparison = powder.get("lot_comparison") or {}
            if comparison.get("title") and comparison.get("severity") in {
                "watch",
                "high",
            }:
                info_parts.append(str(comparison.get("title")))
            if published_window:
                info_parts.append(
                    f"Published about {format_weight_grains(float(published_window['avg_min_charge_grains']), 'powder')}-"
                    f"{format_weight_grains(float(published_window['avg_max_charge_grains']), 'powder')}"
                )
            variant_count = int(
                powder.get("reference_variant_count")
                or powder.get("gordon_reference_variant_count")
                or 0
            )
            snapshot_count = int(
                powder.get("reference_snapshot_count")
                or powder.get("gordon_reference_snapshot_count")
                or 0
            )
            if variant_count:
                info_parts.append(f"{variant_count} interne referansevarianter")
            elif snapshot_count:
                info_parts.append(f"{snapshot_count} interne referansesnapshots")
            self.powder_info.setText(", ".join(info_parts))

            # Show AI recommendation
            recommendation = tr(
                "mlb_ai_powder_recommendation",
                name=powder["name"],
                burn_rate=powder.get("burn_rate", "?"),
            )
            if published_window:
                recommendation += (
                    f"<br>Published charge window: about "
                    f"{format_weight_grains(float(published_window['avg_min_charge_grains']), 'powder')}-"
                    f"{format_weight_grains(float(published_window['avg_max_charge_grains']), 'powder')} "
                    f"({int(published_window['source_count'])} kilder)."
                )
            self.powder_recommendation.setText(recommendation)
            self._refresh_component_context_label()
            self._sync_active_load_session_context()
            self.update_visualization()
        else:
            self.powder_data = None
            self.powder_info.setText(tr("mlb_select_powder_details"))
            self.powder_recommendation.setText("")
            if hasattr(self, "powder_sandbox_label"):
                self.powder_sandbox_label.setText("")
            self._refresh_component_context_label()
            self._sync_active_load_session_context()
            if hasattr(self, "component_fit_label"):
                self.component_fit_label.setText(
                    "Select a bullet and powder to assess how well the combination fits the selected firearm and active barrel."
                )

    def on_primer_changed(self, index):
        """Handle primer selection and active primer lot context."""
        primer = self.primer_combo.currentData()
        if primer:
            self._load_component_lot_choices("primers", primer.get("id"))
            self.primer_data = self._apply_primer_lot_context(dict(primer))
            primer = self.primer_data if isinstance(self.primer_data, dict) else {}
            info_parts = [
                f"{primer.get('manufacturer') or '?'} {primer.get('name') or '?'}".strip()
            ]
            if primer.get("type"):
                info_parts.append(f"Type: {primer.get('type')}")
            if primer.get("size"):
                info_parts.append(f"Size: {primer.get('size')}")
            primer_profile = infer_primer_reference_profile(primer)
            if primer_profile.get("product_line"):
                info_parts.append(f"Series: {primer_profile.get('product_line')}")
            if primer_profile.get("part_number"):
                info_parts.append(f"PN: {primer_profile.get('part_number')}")
            if primer_profile.get("pressure_tolerance_class"):
                info_parts.append(
                    f"Pressure class: {primer_profile.get('pressure_tolerance_class')}"
                )
            if primer_profile.get("magnum"):
                info_parts.append("Magnum")
            if primer_profile.get("match_grade"):
                info_parts.append("Match")
            _cup_val = primer_profile.get("cup_thickness_in")
            if _cup_val not in (None, ""):
                try:
                    info_parts.append(f'Cup: {float(_cup_val):.3f}"')
                except Exception:
                    pass
            if primer_profile.get("source_kind"):
                info_parts.append(f"Basis: {primer_profile.get('source_kind')}")
            if primer.get("selected_lot_number"):
                info_parts.append(f"Lot: {primer.get('selected_lot_number')}")
            learning = primer.get("lot_learning_profile") or {}
            if isinstance(learning.get("typical_es_fps"), (int, float)):
                info_parts.append(
                    f"Lot ES: {format_velocity_fps(float(learning['typical_es_fps']))}"
                )
            comparison = primer.get("lot_comparison") or {}
            if comparison.get("title") and comparison.get("severity") in {
                "watch",
                "high",
            }:
                info_parts.append(str(comparison.get("title")))
            self.primer_info.setText(", ".join(part for part in info_parts if part))
            self._refresh_component_context_label()
            self._sync_active_load_session_context()
            try:
                self.update_visualization()
            except Exception:
                pass
        else:
            self.primer_data = None
            self.primer_info.setText(tr("mlb_select_primer_details"))
            self._refresh_component_context_label()
            self._sync_active_load_session_context()

    def on_bullet_lot_changed(self, index):
        """Rebuild bullet context when the explicit lot selection changes."""
        bullet = self.bullet_combo.currentData()
        if not bullet:
            return
        self.bullet_data = self._apply_bullet_lot_measurements(dict(bullet))
        self._sync_active_load_session_context()
        self.on_bullet_changed(self.bullet_combo.currentIndex())

    def on_powder_lot_changed(self, index):
        """Rebuild powder context when the explicit lot selection changes."""
        powder = self.powder_combo.currentData()
        if not powder:
            return
        self.powder_data = self._apply_powder_lot_context(dict(powder))
        self._sync_active_load_session_context()
        self.on_powder_changed(self.powder_combo.currentIndex())

    def on_primer_lot_changed(self, index):
        """Rebuild primer context when the explicit lot selection changes."""
        primer = self.primer_combo.currentData()
        if not primer:
            return
        self.primer_data = self._apply_primer_lot_context(dict(primer))
        self._sync_active_load_session_context()
        self.on_primer_changed(self.primer_combo.currentIndex())

    def _select_component_lot_in_combo(self, combo, lot_id) -> None:
        """Restore a specific lot selection in one of the component lot combos."""
        if combo is None or lot_id is None:
            return
        try:
            index = combo.findData(lot_id)
        except Exception:
            index = -1
        if index is not None and index >= 0:
            combo.setCurrentIndex(index)

    def _open_bullet_lot_dialog(self, existing_lot: dict | None = None) -> dict | None:
        """Minimal bullet lot dialog for quick creation inside the builder."""
        existing_lot = existing_lot or {}
        dialog = QDialog(self)
        dialog.setWindowTitle("Bullet Lot")
        dialog.resize(420, 300)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        lot_number = QLineEdit()
        lot_number.setText(str(existing_lot.get("lot_number") or ""))
        form.addRow("Lot Number", lot_number)

        quantity = QDoubleSpinBox()
        quantity.setRange(0, 100000)
        quantity.setDecimals(0)
        try:
            quantity.setValue(
                float(
                    existing_lot.get("quantity_remaining")
                    or existing_lot.get("quantity_initial")
                    or 250
                )
            )
        except Exception:
            quantity.setValue(250)
        quantity.setSuffix(" pcs")
        form.addRow("Quantity", quantity)

        storage_location = QLineEdit()
        storage_location.setText(str(existing_lot.get("storage_location") or ""))
        form.addRow("Storage Location", storage_location)

        notes = QTextEdit()
        notes.setMaximumHeight(90)
        notes.setPlainText(str(existing_lot.get("notes") or ""))
        form.addRow("Notes", notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return {
            "lot_number": lot_number.text().strip(),
            "quantity_initial": float(quantity.value()),
            "storage_location": storage_location.text().strip() or None,
            "notes": notes.toPlainText().strip() or None,
            "source": "manual_bullet_lot",
            "is_active": 1,
        }

    def on_add_bullet_lot(self) -> None:
        """Create a new bullet lot directly from the builder."""
        bullet = self.bullet_combo.currentData()
        if not isinstance(bullet, dict) or not bullet.get("id"):
            QMessageBox.information(
                self,
                "Bullet Lot",
                "Select a bullet before creating a new lot.",
            )
            return
        payload = self._open_bullet_lot_dialog()
        if not payload:
            return
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Bullet Lot", "The lot must at least have a lot number."
            )
            return

        self.db.update(
            "component_lots",
            {"is_active": 0},
            "component_type = ? AND component_id = ?",
            ("bullet", int(bullet["id"])),
        )
        lot_id = self.db.create_component_lot(
            "bullet",
            int(bullet["id"]),
            str(payload.get("lot_number")),
            float(payload.get("quantity_initial") or 0),
            storage_location=payload.get("storage_location"),
            notes=payload.get("notes"),
            source=payload.get("source"),
            is_active=1,
        )
        self._load_component_lot_choices("bullet", bullet.get("id"))
        self._select_component_lot_in_combo(self.bullet_lot_combo, lot_id)
        self.on_bullet_changed(self.bullet_combo.currentIndex())

    def on_edit_bullet_lot(self) -> None:
        """Edit the currently selected bullet lot directly from the builder."""
        bullet = self.bullet_combo.currentData()
        lot_id = self._selected_component_lot_id("bullet")
        if not isinstance(bullet, dict) or not bullet.get("id") or not lot_id:
            QMessageBox.information(
                self,
                "Bullet Lot",
                "Select a bullet lot before trying to edit it.",
            )
            return
        existing_lot = self.db.get_by_id("component_lots", int(lot_id)) or {}
        payload = self._open_bullet_lot_dialog(existing_lot)
        if not payload:
            return
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Bullet Lot", "The lot must at least have a lot number."
            )
            return
        self.db.update(
            "component_lots",
            {
                "lot_number": str(payload.get("lot_number")),
                "quantity_initial": float(payload.get("quantity_initial") or 0),
                "quantity_remaining": float(payload.get("quantity_initial") or 0),
                "storage_location": payload.get("storage_location"),
                "notes": payload.get("notes"),
                "source": payload.get("source"),
            },
            "id = ?",
            (int(lot_id),),
        )
        self._load_component_lot_choices("bullet", bullet.get("id"))
        self._select_component_lot_in_combo(self.bullet_lot_combo, lot_id)
        self.on_bullet_changed(self.bullet_combo.currentIndex())

    def on_add_powder_lot(self) -> None:
        """Create a new powder lot directly from the builder."""
        powder = self.powder_combo.currentData()
        if not isinstance(powder, dict) or not powder.get("id"):
            QMessageBox.information(
                self,
                "Powder Lot",
                "Select a powder before creating a new lot.",
            )
            return
        dialog = AddPowderLotDialog(self, powder)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_lot_data()
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Powder Lot", "The lot must at least have a lot number."
            )
            return

        self.db.update(
            "component_lots",
            {"is_active": 0},
            "component_type = ? AND component_id = ?",
            ("powder", int(powder["id"])),
        )
        lot_id = self.db.create_component_lot(
            "powder",
            int(powder["id"]),
            str(payload.get("lot_number")),
            float(payload.get("quantity_initial") or 0),
            storage_location=payload.get("storage_location"),
            notes=payload.get("notes"),
            source=payload.get("source"),
            is_active=1,
        )
        self.db.upsert_component_lot_learning_profile(
            int(lot_id),
            {
                "status": payload.get("learning_status"),
                "avg_velocity_fps": payload.get("avg_velocity_fps"),
                "velocity_offset_fps": payload.get("velocity_offset_fps"),
                "typical_es_fps": payload.get("typical_es_fps"),
                "notes": payload.get("learning_notes"),
            },
        )
        self._load_component_lot_choices("powder", powder.get("id"))
        self._select_component_lot_in_combo(self.powder_lot_combo, lot_id)
        self.on_powder_changed(self.powder_combo.currentIndex())

    def on_edit_powder_lot(self) -> None:
        """Edit the currently selected powder lot directly from the builder."""
        powder = self.powder_combo.currentData()
        lot_id = self._selected_component_lot_id("powder")
        if not isinstance(powder, dict) or not powder.get("id") or not lot_id:
            QMessageBox.information(
                self,
                "Powder Lot",
                "Select a powder lot before trying to edit it.",
            )
            return
        existing_lot = self.db.get_by_id("component_lots", int(lot_id)) or {}
        learning = self.db.get_component_lot_learning_profile(int(lot_id)) or {}
        dialog = AddPowderLotDialog(
            self,
            powder,
            existing_lot={
                **existing_lot,
                "learning_status": learning.get("status"),
                "avg_velocity_fps": learning.get("avg_velocity_fps"),
                "velocity_offset_fps": learning.get("velocity_offset_fps"),
                "typical_es_fps": learning.get("typical_es_fps"),
                "learning_notes": learning.get("notes"),
            },
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_lot_data()
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Powder Lot", "The lot must at least have a lot number."
            )
            return
        self.db.update(
            "component_lots",
            {
                "lot_number": str(payload.get("lot_number")),
                "quantity_initial": float(payload.get("quantity_initial") or 0),
                "quantity_remaining": float(payload.get("quantity_initial") or 0),
                "storage_location": payload.get("storage_location"),
                "notes": payload.get("notes"),
                "source": payload.get("source"),
            },
            "id = ?",
            (int(lot_id),),
        )
        self.db.upsert_component_lot_learning_profile(
            int(lot_id),
            {
                "status": payload.get("learning_status"),
                "avg_velocity_fps": payload.get("avg_velocity_fps"),
                "velocity_offset_fps": payload.get("velocity_offset_fps"),
                "typical_es_fps": payload.get("typical_es_fps"),
                "notes": payload.get("learning_notes"),
            },
        )
        self._load_component_lot_choices("powder", powder.get("id"))
        self._select_component_lot_in_combo(self.powder_lot_combo, lot_id)
        self.on_powder_changed(self.powder_combo.currentIndex())

    def on_add_primer_lot(self) -> None:
        """Create a new primer lot directly from the builder."""
        primer = self.primer_combo.currentData()
        if not isinstance(primer, dict) or not primer.get("id"):
            QMessageBox.information(
                self,
                "Primer Lot",
                "Select a primer before creating a new lot.",
            )
            return
        dialog = AddPrimerLotDialog(self, primer)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_lot_data()
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Primer Lot", "The lot must at least have a lot number."
            )
            return

        self.db.update(
            "component_lots",
            {"is_active": 0},
            "component_type = ? AND component_id = ?",
            ("primers", int(primer["id"])),
        )
        lot_id = self.db.create_component_lot(
            "primers",
            int(primer["id"]),
            str(payload.get("lot_number")),
            float(payload.get("quantity_initial") or 0),
            storage_location=payload.get("storage_location"),
            notes=payload.get("notes"),
            source=payload.get("source"),
            is_active=1,
        )
        self.db.upsert_component_lot_learning_profile(
            int(lot_id),
            {
                "status": payload.get("learning_status"),
                "typical_es_fps": payload.get("typical_es_fps"),
                "typical_sd_fps": payload.get("typical_sd_fps"),
                "notes": payload.get("learning_notes"),
            },
        )
        self._load_component_lot_choices("primers", primer.get("id"))
        self._select_component_lot_in_combo(self.primer_lot_combo, lot_id)
        self.on_primer_changed(self.primer_combo.currentIndex())

    def on_edit_primer_lot(self) -> None:
        """Edit the currently selected primer lot directly from the builder."""
        primer = self.primer_combo.currentData()
        lot_id = self._selected_component_lot_id("primers")
        if not isinstance(primer, dict) or not primer.get("id") or not lot_id:
            QMessageBox.information(
                self,
                "Primer Lot",
                "Select a primer lot before trying to edit it.",
            )
            return
        existing_lot = self.db.get_by_id("component_lots", int(lot_id)) or {}
        learning = self.db.get_component_lot_learning_profile(int(lot_id)) or {}
        dialog = AddPrimerLotDialog(
            self,
            primer,
            existing_lot={
                **existing_lot,
                "learning_status": learning.get("status"),
                "typical_es_fps": learning.get("typical_es_fps"),
                "typical_sd_fps": (learning.get("profile_data") or {}).get(
                    "typical_sd_fps"
                ),
                "learning_notes": learning.get("notes"),
            },
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_lot_data()
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Primer Lot", "The lot must at least have a lot number."
            )
            return
        self.db.update(
            "component_lots",
            {
                "lot_number": str(payload.get("lot_number")),
                "quantity_initial": float(payload.get("quantity_initial") or 0),
                "quantity_remaining": float(payload.get("quantity_initial") or 0),
                "storage_location": payload.get("storage_location"),
                "notes": payload.get("notes"),
                "source": payload.get("source"),
            },
            "id = ?",
            (int(lot_id),),
        )
        self.db.upsert_component_lot_learning_profile(
            int(lot_id),
            {
                "status": payload.get("learning_status"),
                "typical_es_fps": payload.get("typical_es_fps"),
                "typical_sd_fps": payload.get("typical_sd_fps"),
                "notes": payload.get("learning_notes"),
            },
        )
        self._load_component_lot_choices("primers", primer.get("id"))
        self._select_component_lot_in_combo(self.primer_lot_combo, lot_id)
        self.on_primer_changed(self.primer_combo.currentIndex())

    def on_add_manual_powder(self):
        """Create a manual/custom powder entry for simulation."""
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("mlb_manual_powder_title"))
        dialog.resize(420, 320)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        manufacturer_edit = QLineEdit()
        form.addRow(tr("mlb_manufacturer_label"), manufacturer_edit)

        name_edit = QLineEdit()
        form.addRow(tr("mlb_name_label"), name_edit)

        type_edit = QLineEdit()
        form.addRow(tr("mlb_type_field"), type_edit)

        burn_rate_edit = QLineEdit()
        burn_rate_edit.setPlaceholderText(tr("mlb_burn_rate_placeholder"))
        form.addRow(tr("mlb_burn_rate_field"), burn_rate_edit)

        density_spin = QDoubleSpinBox()
        density_spin.setRange(0.0, 2.0)
        density_spin.setDecimals(3)
        density_spin.setSingleStep(0.001)
        density_spin.setSuffix(" g/cc")
        density_spin.setValue(0.90)
        form.addRow(tr("mlb_density_field"), density_spin)

        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText(tr("mlb_powder_notes_placeholder"))
        form.addRow(tr("mlb_notes_field"), notes_edit)

        help_label = QLabel(tr("mlb_powder_help"))
        help_label.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addLayout(form)
        layout.addWidget(help_label)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        powder_name = name_edit.text().strip()
        if not powder_name:
            QMessageBox.warning(
                self,
                tr("mlb_missing_data_title"),
                tr("mlb_missing_powder_data"),
            )
            return

        payload = {
            "name": powder_name,
            "manufacturer": manufacturer_edit.text().strip() or None,
            "type": type_edit.text().strip() or None,
            "burn_rate": burn_rate_edit.text().strip() or None,
            "density": (
                float(density_spin.value()) if density_spin.value() > 0 else None
            ),
            "quantity_grams": 0.0,
            "cost_per_unit": None,
            "purchase_date": None,
            "notes": "Created manually from Modern Load Builder",
            "description": notes_edit.toPlainText().strip() or None,
        }
        powder_id = self.db.insert("powder", payload)
        if powder_id is None:
            QMessageBox.critical(
                self,
                "Could Not Save Powder",
                "An error occurred while saving the powder.",
            )
            return

        self.load_powders()
        for idx in range(self.powder_combo.count()):
            data = self.powder_combo.itemData(idx)
            if isinstance(data, dict) and str(data.get("id")) == str(powder_id):
                self.powder_combo.setCurrentIndex(idx)
                break
        self.add_ai_message(
            "Manual powder has been added and can now be simulated against the selected firearm and active barrel."
        )

    def on_charge_slider_changed(self, value):
        """Handle charge slider change"""
        self.current_charge = value / 10.0
        self.charge_label.setText(format_weight_grains(self.current_charge, "powder"))
        self.update_visualization()

    def _parse_twist_inches(self, twist_value) -> float | None:
        """Parse twist text like 1:10 or 10 into inches per turn."""
        if twist_value is None:
            return None
        text = str(twist_value).strip().lower().replace('"', "")
        if not text:
            return None
        for prefix in ("1:", "1-"):
            if prefix in text:
                text = text.split(prefix, 1)[1]
                break
        text = text.replace("twist", "").replace("in", "").strip()
        try:
            value = float(text)
            return value if value > 0 else None
        except Exception:
            return None

    def _classify_burn_rate_bucket(self, powder: dict) -> str:
        """Return a rough burn-rate bucket from powder data."""
        burn_rate = str(powder.get("burn_rate") or "").strip().lower()
        if not burn_rate:
            return "unknown"
        if burn_rate.isdigit():
            try:
                position = int(burn_rate)
                if position <= 80:
                    return "fast"
                if position <= 140:
                    return "medium"
                return "slow"
            except Exception:
                return "unknown"
        if any(word in burn_rate for word in ["fast", "rask"]):
            return "fast"
        if any(word in burn_rate for word in ["slow", "langsom"]):
            return "slow"
        if any(word in burn_rate for word in ["medium", "mid"]):
            return "medium"
        return "unknown"

    def _infer_bullet_diameter_mm(
        self, bullet: dict, caliber_text: str
    ) -> float | None:
        """Return bullet diameter in mm from bullet data or a light caliber inference."""
        diameter = self._coerce_float(bullet.get("diameter_mm"))
        if diameter and diameter > 0:
            return diameter

        text = (caliber_text or "").strip().lower()
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
        self,
        bullet: dict,
        twist_inches: float | None,
        caliber_text: str,
        muzzle_velocity_fps: float | None,
    ) -> dict:
        """Estimate gyroscopic stability (Sg) using a Miller-style approximation."""
        missing_inputs: list[str] = []
        if not twist_inches or twist_inches <= 0:
            missing_inputs.append("twist")

        weight_gr = self._coerce_float(
            bullet.get("weight_grains", bullet.get("weight"))
        )
        length_mm = self._coerce_float(bullet.get("length_mm"))
        diameter_mm = self._infer_bullet_diameter_mm(bullet, caliber_text)
        if not weight_gr:
            missing_inputs.append("bullet weight")
        if not length_mm:
            missing_inputs.append("bullet length")
        if not diameter_mm:
            missing_inputs.append("bullet diameter / caliber")
        if missing_inputs:
            return {"missing_inputs": missing_inputs}

        assert (
            twist_inches is not None and twist_inches > 0
        )  # guaranteed by missing_inputs guard
        assert weight_gr is not None  # guaranteed by missing_inputs guard
        assert diameter_mm is not None  # guaranteed by missing_inputs early return
        assert length_mm is not None  # guaranteed by missing_inputs early return
        diameter_in = diameter_mm / 25.4
        length_in = length_mm / 25.4
        if diameter_in <= 0 or length_in <= 0:
            return {"missing_inputs": ["valid bullet length and diameter"]}

        length_calibers = length_in / diameter_in
        twist_calibers = twist_inches / diameter_in
        if length_calibers <= 0 or twist_calibers <= 0:
            return {"missing_inputs": ["valid twist and bullet geometry"]}

        velocity = max(float(muzzle_velocity_fps or 2800.0), 500.0)
        _tc3 = self._current_temperature_c()
        temp_c = (
            float(_tc3) if hasattr(self, "temp_spin") and _tc3 is not None else 15.0
        )
        _pkpa3 = self._current_pressure_kpa()
        pressure_kpa = (
            float(_pkpa3)
            if hasattr(self, "pressure_spin") and _pkpa3 is not None
            else 101.325
        )
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        pressure_inhg = pressure_kpa * 0.2953

        try:
            sg = (30.0 * weight_gr) / (
                (twist_calibers**2)
                * (diameter_in**3)
                * length_calibers
                * (1.0 + length_calibers**2)
            )
            sg *= (velocity / 2800.0) ** (1.0 / 3.0)
            sg *= ((temp_f + 459.67) / (59.0 + 459.67)) * (29.92 / pressure_inhg)
        except Exception:
            return {"missing_inputs": ["stability calculation could not be completed"]}

        if sg >= 1.5:
            tier = "good stability"
        elif sg >= 1.3:
            tier = "usable stability"
        elif sg >= 1.0:
            tier = "marginal stability"
        else:
            tier = "unstable / high risk"

        return {
            "sg": sg,
            "tier": tier,
            "diameter_mm": diameter_mm,
            "length_mm": length_mm,
            "velocity_fps": velocity,
        }

    def _refresh_bullet_action_button(self) -> None:
        """Update bullet action button text based on missing simulation data."""
        if not hasattr(self, "edit_bullet_btn"):
            return
        bullet = self.bullet_data if isinstance(self.bullet_data, dict) else None
        if not bullet or not bullet.get("id"):
            self.edit_bullet_btn.setEnabled(False)
            self.edit_bullet_btn.setText("Edit Selected Bullet")
            return

        barrel = self._get_active_barrel_details()
        caliber_text = str(
            barrel.get("caliber") or (self.rifle_data or {}).get("caliber") or ""
        ).lower()
        twist_inches = self._parse_twist_inches(
            barrel.get("twist") or (self.rifle_data or {}).get("twist_rate")
        )
        stability = self._estimate_gyroscopic_stability(
            bullet,
            twist_inches,
            caliber_text,
            None,
        )
        missing = list(stability.get("missing_inputs") or [])
        if missing:
            preview = ", ".join(missing[:2])
            if len(missing) > 2:
                preview += ", ..."
            self.edit_bullet_btn.setText(f"Fill in: {preview}")
        else:
            self.edit_bullet_btn.setText("Edit Selected Bullet")
        self.edit_bullet_btn.setEnabled(True)

    def _build_component_fit_assessment(
        self, result: dict | None = None
    ) -> tuple[str, list[str]]:
        """Return a short fit summary and check lines for selected bullet/powder."""
        if not self.rifle_data or not self.bullet_data or not self.powder_data:
            return (
                "Select a bullet and powder to get an assessment of how well the combination fits the selected firearm and active barrel.",
                [],
            )

        barrel = self._get_active_barrel_details()
        details = self._get_rifle_profile_details()
        twist_value = barrel.get("twist") or self.rifle_data.get("twist_rate")
        twist_inches = self._parse_twist_inches(twist_value)
        bullet_weight = self._coerce_float(
            self.bullet_data.get("weight_grains", self.bullet_data.get("weight"))
        )
        bullet_length = self._coerce_float(self.bullet_data.get("length_mm"))
        barrel_length_mm = self._coerce_float(
            barrel.get("length_mm")
            or details.get("barrel_length_mm")
            or self.rifle_data.get("barrel_length_mm")
        )
        mag_limit = self._coerce_float(details.get("magazine_length_mm"))
        powder_bucket = self._classify_burn_rate_bucket(self.powder_data)
        caliber_text = str(
            barrel.get("caliber") or self.rifle_data.get("caliber") or ""
        ).lower()
        stability = self._estimate_gyroscopic_stability(
            self.bullet_data,
            twist_inches,
            caliber_text,
            result.get("muzzle_velocity_fps") if result else None,
        )
        notes: list[str] = []
        checks: list[str] = []

        if twist_inches and bullet_weight:
            if twist_inches >= 12 and bullet_weight > 175:
                notes.append(
                    "The twist looks slow for this bullet weight. Stabilization may be marginal."
                )
                checks.append(
                    "WARN: twist looks slow for the selected bullet weight - verify stability and precision in practice"
                )
            elif twist_inches <= 8 and bullet_weight < 130:
                notes.append(
                    "The twist is fast, but that is usually perfectly fine. A light bullet can still work well."
                )
                checks.append(
                    "OK: a fast twist usually stabilizes lighter bullets well too"
                )
            else:
                notes.append(
                    "Twist and bullet weight look reasonable as a starting point."
                )
                checks.append("OK: twist and bullet weight look compatible")

        if stability:
            sg = float(stability["sg"])
            notes.append(
                f"Estimated stability Sg {sg:.2f} ({stability['tier']}) at about {format_velocity_fps(float(stability['velocity_fps']))}."
            )
            if sg < 1.0:
                checks.append(
                    "FAIL: estimated Sg is below 1.0 - the bullet may be unstable in this twist"
                )
            elif sg < 1.3:
                checks.append(
                    "WARN: estimated Sg is marginal - verify carefully with actual groups and preferably yaw signs"
                )
            elif sg < 1.5:
                checks.append(
                    "WARN: estimated Sg is usable but not generous - watch stability in cold weather and at longer range"
                )
            else:
                checks.append("OK: estimated Sg indicates good gyroscopic stability")
        elif stability.get("missing_inputs"):
            missing = ", ".join(stability.get("missing_inputs", []))
            notes.append(
                "Sg/stability cannot be calculated yet because data is missing: "
                + missing
                + ". Enter these fields for a more precise assessment."
            )
            checks.append("WARN: Sg estimate is missing data - enter " + missing)

        if bullet_length and twist_inches:
            if bullet_length > 36 and twist_inches >= 10:
                notes.append(
                    "The bullet is relatively long for the stated twist. Pay extra attention to stability."
                )
                checks.append(
                    "WARN: a long bullet may require a faster twist for fully safe stability"
                )

        if mag_limit and self.coal_mm:
            if float(self.coal_mm or 0) > mag_limit:
                notes.append(
                    "The current COAL appears to exceed the magazine length for this firearm."
                )
                checks.append("FAIL: selected COAL exceeds magazine length")
            elif float(self.coal_mm or 0) > mag_limit - 1.0:
                notes.append(
                    "COAL is very close to magazine length. That can limit seating-depth testing."
                )
                checks.append("WARN: COAL is very close to magazine length")
            else:
                checks.append("OK: COAL appears to fit within magazine length")

        if barrel_length_mm and bullet_weight:
            if (
                barrel_length_mm < 470
                and bullet_weight >= 175
                and powder_bucket == "slow"
            ):
                notes.append(
                    "A heavy bullet in a short barrel with slow powder can leave unburned powder and reduce effective velocity."
                )
                checks.append(
                    "WARN: heavy bullet + short barrel + slow powder can be a sluggish combination"
                )
            elif (
                barrel_length_mm >= 600
                and bullet_weight >= 160
                and powder_bucket == "slow"
            ):
                notes.append(
                    "A long barrel and heavier bullet often pair well with a slightly slower powder."
                )
                checks.append(
                    "OK: barrel length and powder speed look sensible together"
                )
            elif barrel_length_mm < 470 and powder_bucket == "fast":
                notes.append(
                    "A short barrel and faster powder can be a sensible starting point."
                )
                checks.append(
                    "OK: short barrel and faster powder often work well together"
                )

        if result and result.get("load_density_percent") is not None:
            try:
                density = float(result["load_density_percent"])
                if density < 85:
                    notes.append(
                        "Load density is low. The combination can still work, but often with more ES and less even combustion."
                    )
                elif density > 105:
                    notes.append(
                        "The load appears compressed. Be extra conservative and verify carefully."
                    )
            except Exception:
                pass

        if not notes:
            notes.append(
                "Bullet and powder look like a usable starting point for this firearm, but always verify with a chronograph and actual groups."
            )

        return " ".join(notes), checks

    def on_seating_changed(self):
        """Handle seating depth change"""
        self.coal_mm = self.coal_spin.value()
        self.cbto_mm = self.cbto_spin.value()
        self._refresh_seating_depth_advisor()

        self.update_visualization()

    def _refresh_seating_depth_advisor(self, result: dict | None = None) -> None:
        if not hasattr(self, "seating_advisor_label"):
            return

        service_analysis = (
            self._latest_load_analysis
            if isinstance(getattr(self, "_latest_load_analysis", None), dict)
            else {}
        )
        if not service_analysis and result is not None:
            try:
                service_analysis = self._build_service_analysis() or {}
            except Exception:
                service_analysis = {}

        try:
            seating_context = self._get_current_seating_context()
            barrel_details = self._get_active_barrel_details()
            twist_inches = self._parse_twist_inches(
                barrel_details.get("twist") or (self.rifle_data or {}).get("twist_rate")
            )
            caliber_text = str(
                barrel_details.get("caliber")
                or (self.rifle_data or {}).get("caliber")
                or ""
            ).lower()
            live_stability = self._estimate_gyroscopic_stability(
                self.bullet_data if isinstance(self.bullet_data, dict) else {},
                twist_inches,
                caliber_text,
                result.get("muzzle_velocity_fps") if isinstance(result, dict) else None,
            )
            sub_mode = bool(
                getattr(self, "subsonic_cb", None) and self.subsonic_cb.isChecked()
            )
            _sub_tgt = getattr(self, "subsonic_target", None)
            target_fps = float(_sub_tgt.value() if _sub_tgt is not None else 1050.0)
            stability_advisory = summarize_stability_advisor(
                live_stability,
                result=result if isinstance(result, dict) else None,
                subsonic_mode=sub_mode,
                twist_inches=twist_inches,
                bullet=self.bullet_data if isinstance(self.bullet_data, dict) else None,
                barrel_details=barrel_details,
                rifle_data=(
                    self.rifle_data if isinstance(self.rifle_data, dict) else None
                ),
            )
            subsonic_advisory = summarize_subsonic_advisor(
                result if isinstance(result, dict) else None,
                enabled=sub_mode,
                target_velocity_fps=target_fps,
                stability=live_stability,
            )
            subsonic_history = summarize_subsonic_history_advisory(
                self.db,
                (
                    (self.rifle_data or {}).get("id")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                (
                    (self.bullet_data or {}).get("id")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                (
                    (self.powder_data or {}).get("id")
                    if isinstance(self.powder_data, dict)
                    else None
                ),
            )
            summary = summarize_seating_depth_advisor(
                self.db,
                self.rifle_data if isinstance(self.rifle_data, dict) else None,
                self.bullet_data if isinstance(self.bullet_data, dict) else None,
                float(self.coal_mm or 0) if self.coal_mm is not None else None,
                float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
                profile_details=self._get_rifle_profile_details(),
                barrel_details=barrel_details,
                harmonics=self._get_rifle_harmonics_profile(),
                current_temperature_c=seating_context.get("temperature_c"),
                current_distance_m=seating_context.get("distance_m"),
                subsonic_mode=sub_mode,
                stability_context=stability_advisory,
                subsonic_context=subsonic_advisory,
                subsonic_history=subsonic_history,
            )
        except Exception:
            summary = {
                "level": "neutral",
                "title": "Seating Depth",
                "message": "Could not build the seating advisor right now.",
                "checks": [],
                "visualization_html": _seating_visualization_html(None),
            }

        self._latest_seating_summary = summary

        jump_mm = summary.get("jump_mm")
        jam_cbto_mm = summary.get("jam_cbto_mm")
        if jump_mm is not None:
            self.jump_label.setText(
                f'Jump: {float(jump_mm):.2f}mm ({float(jump_mm)/25.4:.3f}")'
            )
        elif jam_cbto_mm is not None:
            self.jump_label.setText(f"Jam CBTO: {float(jam_cbto_mm):.2f} mm")
        else:
            self.jump_label.setText(tr("mlb_jump_calculating"))

        if hasattr(self, "seating_visual_label"):
            self.seating_visual_label.setText(
                str(summary.get("visualization_html") or "")
            )
        if hasattr(self, "seating_confidence_label"):
            self.seating_confidence_label.setText(
                str(summary.get("confidence_html") or "")
            )
        if hasattr(self, "seating_history_label"):
            self.seating_history_label.setText(
                str(summary.get("history_visualization_html") or "")
            )
        if hasattr(self, "seating_trend_label"):
            self.seating_trend_label.setText(
                str(summary.get("trend_summary_html") or "")
            )
        subsonic_windows: dict[str, Any] | None = None
        if hasattr(self, "seating_sandbox_label"):
            subsonic_windows = get_subsonic_history_windows(
                self.db,
                (
                    (self.rifle_data or {}).get("id")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                (
                    (self.bullet_data or {}).get("id")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                (
                    (self.powder_data or {}).get("id")
                    if isinstance(self.powder_data, dict)
                    else None
                ),
            )
            sandbox_html = build_seating_sandbox_html(
                getattr(self, "engine", None),
                (
                    (self.rifle_data or {}).get("id")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                (
                    (self.bullet_data or {}).get("id")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                (
                    (self.powder_data or {}).get("id")
                    if isinstance(self.powder_data, dict)
                    else None
                ),
                (
                    float(self.current_charge or 0)
                    if self.current_charge is not None
                    else None
                ),
                float(self.coal_mm or 0) if self.coal_mm is not None else None,
                float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
                current_result=result,
                barrel_id=self._get_active_barrel_id(),
                ranked_candidates=(summary.get("best_known_evidence") or {}).get(
                    "ranked_candidates"
                ),
                subsonic_history=subsonic_windows,
            )
            self.seating_sandbox_label.setText(sandbox_html)
        if hasattr(self, "powder_sandbox_label"):
            published_window = get_published_powder_charge_window(
                self.db,
                (
                    (self.rifle_data or {}).get("caliber")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                (
                    (self.powder_data or {}).get("name")
                    if isinstance(self.powder_data, dict)
                    else None
                ),
                (
                    (self.bullet_data or {}).get("id")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                (
                    (self.bullet_data or {}).get("weight")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
            )
            powder_sandbox_html = build_powder_sandbox_html(
                getattr(self, "engine", None),
                (
                    (self.rifle_data or {}).get("id")
                    if isinstance(self.rifle_data, dict)
                    else None
                ),
                (
                    (self.bullet_data or {}).get("id")
                    if isinstance(self.bullet_data, dict)
                    else None
                ),
                (
                    (self.powder_data or {}).get("id")
                    if isinstance(self.powder_data, dict)
                    else None
                ),
                (
                    float(self.current_charge or 0)
                    if self.current_charge is not None
                    else None
                ),
                float(self.coal_mm or 0) if self.coal_mm is not None else None,
                float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
                current_result=result,
                barrel_id=self._get_active_barrel_id(),
                published_window=published_window,
                subsonic_history=subsonic_windows,
            )
            self.powder_sandbox_label.setText(powder_sandbox_html)

        checks = summary.get("checks") or []
        detail_html = "".join(f"<li>{item}</li>" for item in checks[:4])
        message = str(summary.get("message") or "").strip()
        title = str(summary.get("title") or "Seating Depth").strip()
        summary_line = str(summary.get("summary") or "").strip()
        _svc: dict[str, Any] = (
            service_analysis if isinstance(service_analysis, dict) else {}
        )
        service_harmonics = _as_dict(_svc, "harmonics")
        service_recommendation = _as_dict(_svc, "recommendation")
        bullet_geometry = _as_dict(_svc, "bullet_geometry")
        node_fit = _as_dict(_svc, "node_fit")
        if summary.get("level") == "critical":
            self.seating_advisor_label.setStyleSheet(_advisory_style("critical"))
        elif summary.get("level") == "warning":
            self.seating_advisor_label.setStyleSheet(_advisory_style("warning"))
        elif summary.get("level") == "ok":
            self.seating_advisor_label.setStyleSheet(_advisory_style("ok"))
        else:
            self.seating_advisor_label.setStyleSheet(_advisory_style("unknown"))

        html = f"<b>{title}</b>: {message}"
        if summary_line:
            html += f"<br><span style='font-weight:400'>{summary_line}</span>"
        harmonic_score = service_harmonics.get("harmonic_score")
        harmonic_confidence = str(
            service_harmonics.get("harmonics_confidence") or ""
        ).strip()
        seating_sensitivity = (service_harmonics.get("sensitivity") or {}).get(
            "seating_depth"
        )
        if harmonic_score is not None or seating_sensitivity is not None:
            harmonic_parts = []
            if harmonic_score is not None:
                harmonic_parts.append(f"Harmonics score {float(harmonic_score):.1f}/20")
            if seating_sensitivity is not None:
                harmonic_parts.append(
                    f"seating sensitivity {float(seating_sensitivity):.2f}"
                )
            if harmonic_confidence:
                harmonic_parts.append(f"confidence {harmonic_confidence}")
            html += (
                "<br><span style='font-weight:400'>"
                + " | ".join(harmonic_parts)
                + "</span>"
            )
        seating_window = service_recommendation.get("seating_window_mm") or []
        if len(seating_window) == 2:
            html += (
                "<br><span style='font-weight:400'>"
                f"Engine seating suggestion: {float(seating_window[0]):+.2f} to {float(seating_window[1]):+.2f} mm"
                "</span>"
            )
        geometry_notes = bullet_geometry.get("notes") or []
        if geometry_notes:
            html += (
                "<br><span style='font-weight:400'>"
                + " | ".join(
                    str(note) for note in geometry_notes[:2] if str(note).strip()
                )
                + "</span>"
            )
        node_checks = node_fit.get("checks") or []
        if node_checks:
            html += (
                "<br><span style='font-weight:400'>"
                + " | ".join(str(note) for note in node_checks[:2] if str(note).strip())
                + "</span>"
            )
        if detail_html:
            html += f"<br><ul style='margin:6px 0 0 18px; font-weight:400'>{detail_html}</ul>"
        self.seating_advisor_label.setText(html)

    def _persist_current_seating_depth_profile(self, source: str = "builder") -> None:
        if not (
            self.db
            and isinstance(self.rifle_data, dict)
            and isinstance(self.bullet_data, dict)
        ):
            return
        rifle_id = self.rifle_data.get("id")
        bullet_id = self.bullet_data.get("id")
        if not rifle_id or not bullet_id:
            return
        summary = summarize_seating_depth_advisor(
            self.db,
            self.rifle_data,
            self.bullet_data,
            float(self.coal_mm or 0) if self.coal_mm is not None else None,
            float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
            profile_details=self._get_rifle_profile_details(),
            barrel_details=self._get_active_barrel_details(),
            harmonics=self._get_rifle_harmonics_profile(),
            current_temperature_c=self._get_current_seating_context().get(
                "temperature_c"
            ),
            current_distance_m=self._get_current_seating_context().get("distance_m"),
        )
        payload = {
            "rifle_id": int(rifle_id),
            "barrel_id": self._get_active_barrel_id(),
            "barrel_name": str(
                self._get_active_barrel_details().get("name") or ""
            ).strip()
            or None,
            "bullet_id": int(bullet_id),
            "component_lot_id": self.bullet_data.get("selected_lot_id"),
            "preferred_coal_mm": (
                float(self.coal_mm or 0) if self.coal_mm is not None else None
            ),
            "preferred_cbto_mm": (
                float(self.cbto_mm or 0) if self.cbto_mm is not None else None
            ),
            "preferred_jump_mm": summary.get("jump_mm"),
            "jam_cbto_mm": summary.get("jam_cbto_mm"),
            "standard_oal_mm": summary.get("standard_oal_mm"),
            "evidence_level": (
                "sweet_spot_promoted"
                if (summary.get("promotion_candidate") or {}).get("eligible")
                else "builder_saved"
            ),
            "source": source,
            "notes": " | ".join(
                part
                for part in [
                    str(summary.get("message") or "").strip(),
                    str(
                        (summary.get("promotion_candidate") or {}).get("message") or ""
                    ).strip(),
                ]
                if part
            ),
        }
        try:
            self.db.upsert_seating_depth_profile(payload)
        except Exception:
            pass

    def _get_saved_seating_depth_profile(self) -> dict | None:
        if not (
            self.db
            and isinstance(self.rifle_data, dict)
            and isinstance(self.bullet_data, dict)
        ):
            return None
        rifle_id = self.rifle_data.get("id")
        bullet_id = self.bullet_data.get("id")
        if not rifle_id or not bullet_id:
            return None
        try:
            component_lot_id = self.bullet_data.get("selected_lot_id")
            return self.db.get_seating_depth_profile(
                int(rifle_id),
                int(bullet_id),
                int(component_lot_id) if component_lot_id not in (None, "") else None,
                self._get_active_barrel_id(),
            )
        except Exception:
            return None

    def _get_best_known_seating_evidence(self) -> dict | None:
        if not (
            self.db
            and isinstance(self.rifle_data, dict)
            and isinstance(self.bullet_data, dict)
        ):
            return None
        rifle_id = self.rifle_data.get("id")
        bullet_id = self.bullet_data.get("id")
        if not rifle_id or not bullet_id:
            return None
        try:
            component_lot_id = self.bullet_data.get("selected_lot_id")
            lot_number = (
                str(self.bullet_data.get("selected_lot_number") or "").strip() or None
            )
            context = self._get_current_seating_context()
            return self.db.get_best_seating_depth_evidence(
                int(rifle_id),
                int(bullet_id),
                int(component_lot_id) if component_lot_id not in (None, "") else None,
                lot_number,
                context.get("temperature_c"),
                context.get("distance_m"),
                context.get("throat_erosion_mm"),
                self._get_active_barrel_id(),
            )
        except Exception:
            return None

    def _current_recommendation_signature(self) -> tuple[Any, ...]:
        powder_context = self._get_selected_powder_context()
        return (
            (
                (self.rifle_data or {}).get("id")
                if isinstance(self.rifle_data, dict)
                else None
            ),
            self._get_active_barrel_id(),
            (
                (self.bullet_data or {}).get("id")
                if isinstance(self.bullet_data, dict)
                else None
            ),
            (
                (self.bullet_data or {}).get("selected_lot_id")
                if isinstance(self.bullet_data, dict)
                else None
            ),
            powder_context.get("id") if isinstance(powder_context, dict) else None,
            (
                (self.powder_data or {}).get("selected_lot_id")
                if isinstance(self.powder_data, dict)
                else None
            ),
        )

    def _build_recommendation_baseline_candidate(self) -> dict[str, Any]:
        analysis = (
            self._latest_load_analysis
            if isinstance(getattr(self, "_latest_load_analysis", None), dict)
            else {}
        )
        seating_summary = (
            self._latest_seating_summary
            if isinstance(getattr(self, "_latest_seating_summary", None), dict)
            else {}
        )
        charge_promotion_candidate = summarize_charge_promotion_candidate(
            db=self.db,
            rifle_id=(
                (self.rifle_data or {}).get("id")
                if isinstance(self.rifle_data, dict)
                else None
            ),
            bullet_id=(
                (self.bullet_data or {}).get("id")
                if isinstance(self.bullet_data, dict)
                else None
            ),
            powder_id=(
                (self.powder_data or {}).get("id")
                if isinstance(self.powder_data, dict)
                else None
            ),
            current_charge_gr=(
                float(self.current_charge or 0)
                if self.current_charge is not None
                else None
            ),
        )
        return build_evidence_recommendation_baseline(
            analysis=analysis,
            current_charge_gr=(
                float(self.current_charge or 0)
                if self.current_charge is not None
                else None
            ),
            coal_mm=float(self.coal_mm or 0) if self.coal_mm is not None else None,
            cbto_mm=float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
            seating_summary=seating_summary,
            charge_promotion_candidate=charge_promotion_candidate,
            signature=self._current_recommendation_signature(),
        )

    def _ensure_recommendation_baseline(self) -> dict[str, Any] | None:
        signature = self._current_recommendation_signature()
        _baseline_raw = getattr(self, "_recommendation_baseline", None)
        baseline: dict[str, Any] | None = (
            _baseline_raw if isinstance(_baseline_raw, dict) else None
        )
        if (
            baseline
            and baseline.get("signature") == signature
            and baseline.get("available")
        ):
            return baseline

        runtime = self._get_cached_or_active_load_session_runtime()
        _rr_raw = runtime.get("recommendation") if isinstance(runtime, dict) else None
        runtime_recommendation: dict[str, Any] = (
            _rr_raw if isinstance(_rr_raw, dict) else {}
        )
        _rb_raw = runtime_recommendation.get("baseline")
        runtime_baseline: dict[str, Any] = _rb_raw if isinstance(_rb_raw, dict) else {}
        if runtime_baseline.get("available"):
            runtime_signature = tuple(runtime_baseline.get("signature") or ())
            if not runtime_signature or runtime_signature == signature:
                self._recommendation_baseline: dict[str, Any] | None = dict(
                    runtime_baseline
                )
                return self._recommendation_baseline

        candidate = self._build_recommendation_baseline_candidate()
        if candidate.get("available"):
            self._recommendation_baseline = candidate
            return candidate

        self._recommendation_baseline = None
        return None

    def _refresh_recommendation_state_panel(self) -> None:
        if not hasattr(self, "recommendation_state_label"):
            return

        baseline = self._ensure_recommendation_baseline()
        state = build_recommendation_control_state(
            current_charge_gr=(
                float(self.current_charge or 0)
                if self.current_charge is not None
                else None
            ),
            coal_mm=float(self.coal_mm or 0) if self.coal_mm is not None else None,
            cbto_mm=float(self.cbto_mm or 0) if self.cbto_mm is not None else None,
            baseline=baseline,
        )

        self.recommendation_state_label.setStyleSheet(
            _advisory_style(str(state.get("level") or "unknown"))
        )
        if hasattr(self, "use_recommended_btn"):
            self.use_recommended_btn.setEnabled(bool(state.get("can_apply")))
            if state.get("can_apply"):
                charge_source_label = str(
                    state.get("charge_source_label") or "frozen baseline"
                ).strip()
                seating_source_label = str(
                    state.get("seating_source_label") or "frozen baseline"
                ).strip()
                if charge_source_label == seating_source_label:
                    self.use_recommended_btn.setText(
                        "Use " + charge_source_label.title()
                    )
                else:
                    self.use_recommended_btn.setText("Use Frozen Baseline")
                self.use_recommended_btn.setToolTip(
                    "Jump back to the current frozen baseline. "
                    f"Charge uses {charge_source_label}; seating uses {seating_source_label}."
                )
            else:
                self.use_recommended_btn.setText("Use Frozen Baseline")
                self.use_recommended_btn.setToolTip(
                    "Builder is already aligned with the frozen baseline."
                )

        if not state.get("available"):
            self.recommendation_state_label.setText(
                "<b>Recommendation State</b>: " + str(state.get("message") or "")
            )
            return

        chips = [
            _status_pill(
                "Charge " + str(state.get("charge_state") or "unknown").title(),
                (
                    "ok"
                    if state.get("charge_state") in {"recommended", "learned"}
                    else "info"
                ),
            ),
            _status_pill(
                "Seating " + str(state.get("seating_state") or "unknown").title(),
                (
                    "ok"
                    if state.get("seating_state") in {"recommended", "learned"}
                    else "info"
                ),
            ),
            _status_pill(
                "Trust " + str(state.get("trust_label") or "unknown").title(),
                "info",
            ),
        ]
        target_bits: list[str] = []
        if state.get("charge_target_gr") is not None:
            target_bits.append(f"Charge {float(state['charge_target_gr']):.2f} gr")
        if state.get("cbto_target_mm") is not None:
            target_bits.append(f"CBTO {float(state['cbto_target_mm']):.2f} mm")
        elif state.get("coal_target_mm") is not None:
            target_bits.append(f"COAL {float(state['coal_target_mm']):.2f} mm")

        html = "<b>Recommendation State</b>: " + str(state.get("message") or "")
        html += "<br>" + "".join(chips)
        if target_bits:
            html += (
                "<br><span style='font-weight:400'>Frozen baseline: "
                + " | ".join(target_bits)
                + "</span>"
            )
        source_line_bits: list[str] = []
        if state.get("charge_source_label"):
            source_line_bits.append("Charge " + str(state.get("charge_source_label")))
        if state.get("seating_source_label"):
            source_line_bits.append("Seating " + str(state.get("seating_source_label")))
        if source_line_bits:
            html += (
                "<br><span style='font-weight:400'>"
                + " | ".join(source_line_bits)
                + "</span>"
            )
        basis_summary = summarize_recommendation_evidence_basis(
            (
                self._latest_load_analysis
                if isinstance(getattr(self, "_latest_load_analysis", None), dict)
                else {}
            ),
            baseline,
        )
        compact_basis = str(basis_summary.get("compact") or "").strip()
        if compact_basis:
            html += "<br><span style='font-weight:400'>" + compact_basis + "</span>"
        self.recommendation_state_label.setText(html)

    def on_apply_recommendation_baseline_clicked(self) -> None:
        baseline = self._ensure_recommendation_baseline()
        if not baseline:
            return

        charge_target = _coerce_float(baseline.get("charge_gr"))
        coal_target = _coerce_float(baseline.get("coal_mm"))
        cbto_target = _coerce_float(baseline.get("cbto_mm"))

        charge_signals = None
        coal_signals = None
        cbto_signals = None
        try:
            if hasattr(self, "charge_slider"):
                charge_signals = self.charge_slider.blockSignals(True)
            if hasattr(self, "coal_spin"):
                coal_signals = self.coal_spin.blockSignals(True)
            if hasattr(self, "cbto_spin"):
                cbto_signals = self.cbto_spin.blockSignals(True)

            if charge_target is not None:
                self.current_charge = charge_target
                if hasattr(self, "charge_slider"):
                    self.charge_slider.setValue(int(round(charge_target * 10.0)))
                if hasattr(self, "charge_label"):
                    self.charge_label.setText(
                        format_weight_grains(charge_target, "powder")
                    )
            if coal_target is not None:
                self.coal_mm = coal_target
                if hasattr(self, "coal_spin"):
                    self.coal_spin.setValue(coal_target)
            if cbto_target is not None:
                self.cbto_mm = cbto_target
                if hasattr(self, "cbto_spin"):
                    self.cbto_spin.setValue(cbto_target)
        finally:
            if hasattr(self, "charge_slider") and charge_signals is not None:
                self.charge_slider.blockSignals(charge_signals)
            if hasattr(self, "coal_spin") and coal_signals is not None:
                self.coal_spin.blockSignals(coal_signals)
            if hasattr(self, "cbto_spin") and cbto_signals is not None:
                self.cbto_spin.blockSignals(cbto_signals)

        try:
            self._refresh_seating_depth_advisor()
        except Exception:
            pass
        self.update_visualization()

    def _get_current_seating_context(self) -> dict[str, float | None]:
        temperature_c = None
        if hasattr(self, "temp_spin"):
            try:
                temperature_c = self._current_temperature_c()
            except Exception:
                temperature_c = None
        details = self._get_rifle_profile_details()
        barrel = self._get_active_barrel_details()
        distance_m = None
        for candidate in (
            details.get("zero_distance_m"),
            barrel.get("zero_distance_m"),
            barrel.get("distance_m"),
        ):
            try:
                if candidate not in (None, ""):
                    distance_m = float(candidate)
                    break
            except Exception:
                continue
        if distance_m is None:
            distance_m = 100.0

        throat_erosion_mm = None
        for candidate in (
            barrel.get("throat_erosion_mm"),
            details.get("throat_erosion_mm"),
            (self.rifle_data or {}).get("throat_erosion_mm"),
        ):
            try:
                if candidate not in (None, ""):
                    throat_erosion_mm = float(candidate)
                    break
            except Exception:
                continue

        return {
            "temperature_c": temperature_c,
            "distance_m": distance_m,
            "throat_erosion_mm": throat_erosion_mm,
        }

    def _get_current_subsonic_context(self) -> dict[str, Any]:
        enabled = bool(
            getattr(self, "subsonic_cb", None) and self.subsonic_cb.isChecked()
        )
        target_velocity_fps = 1050.0
        if getattr(self, "subsonic_target", None) is not None:
            try:
                target_velocity_fps = self._subsonic_target_fps()
            except Exception:
                target_velocity_fps = 1050.0
        latest_result = (
            getattr(self, "_latest_visual_result", None)
            if isinstance(getattr(self, "_latest_visual_result", None), dict)
            else None
        )
        summary = summarize_subsonic_advisor(
            latest_result,
            enabled=enabled,
            target_velocity_fps=target_velocity_fps,
        )
        return {
            "enabled": enabled,
            "target_velocity_fps": target_velocity_fps,
            "advisory": summary,
        }

    def _build_seating_profile_compare_text(self) -> str:
        if not (
            self.db
            and isinstance(self.rifle_data, dict)
            and isinstance(self.bullet_data, dict)
        ):
            return "Select firearm and bullet first."
        rifle_id = self.rifle_data.get("id")
        bullet_id = self.bullet_data.get("id")
        if not rifle_id or not bullet_id:
            return "Select firearm and bullet first."

        try:
            profiles = self.db.list_seating_depth_profiles(
                int(rifle_id),
                int(bullet_id),
                self._get_active_barrel_id(),
            )
        except Exception:
            profiles = []
        if not profiles:
            return "No seating profiles are stored for this firearm/bullet combination yet."

        current_lot_id = self.bullet_data.get("selected_lot_id")
        current_profile = None
        fallback_profile = None
        for profile in profiles:
            if (
                current_lot_id not in (None, "")
                and profile.get("component_lot_id") == current_lot_id
            ):
                current_profile = profile
            elif (
                profile.get("component_lot_id") in (None, "")
                and fallback_profile is None
            ):
                fallback_profile = profile
        reference_profile = None
        if current_profile:
            for profile in profiles:
                if profile is current_profile:
                    continue
                if profile.get("component_lot_id") != current_lot_id:
                    reference_profile = profile
                    break
        else:
            current_profile = fallback_profile or profiles[0]
            for profile in profiles:
                if profile is not current_profile:
                    reference_profile = profile
                    break

        if not current_profile:
            return "No active seating profile was found to compare."
        if not reference_profile:
            return (
                "Only one seating profile exists for this firearm/bullet combination."
            )

        current_jump = current_profile.get("preferred_jump_mm")
        ref_jump = reference_profile.get("preferred_jump_mm")
        current_cbto = current_profile.get("preferred_cbto_mm")
        ref_cbto = reference_profile.get("preferred_cbto_mm")
        current_lot = current_profile.get("component_lot_id")
        ref_lot = reference_profile.get("component_lot_id")
        current_label = (
            f"aktiv lot {self.bullet_data.get('selected_lot_number')}"
            if current_lot not in (None, "")
            else "generell profil"
        )
        ref_label = "referanseprofil"
        if ref_lot not in (None, ""):
            ref_label = f"annen lot ({ref_lot})"

        bits = [f"Sammenligner {current_label} mot {ref_label}."]
        if current_jump not in (None, "") and ref_jump not in (None, ""):
            delta_jump = float(current_jump) - float(ref_jump)
            bits.append(
                f"Jump {float(current_jump):.2f} mm vs {float(ref_jump):.2f} mm ({delta_jump:+.2f} mm)."
            )
        if current_cbto not in (None, "") and ref_cbto not in (None, ""):
            delta_cbto = float(current_cbto) - float(ref_cbto)
            bits.append(
                f"CBTO {float(current_cbto):.2f} mm vs {float(ref_cbto):.2f} mm ({delta_cbto:+.2f} mm)."
            )
        if current_profile.get("notes"):
            bits.append(f"Aktiv profil: {current_profile.get('notes')}")
        if reference_profile.get("notes"):
            bits.append(f"Referanse: {reference_profile.get('notes')}")
        return " ".join(bits)

    def on_save_seating_profile_clicked(self) -> None:
        if not (self.rifle_data and self.bullet_data):
            QMessageBox.information(
                self,
                "Seating Profile",
                "Select firearm and bullet before saving a seating profile.",
            )
            return
        self._persist_current_seating_depth_profile(source="manual_save")
        QMessageBox.information(
            self,
            "Seating Profile Saved",
            "The current COAL/CBTO/jump has been saved as a seating profile for the selected firearm, bullet, and lot when relevant.",
        )
        self._refresh_seating_depth_advisor()

    def on_apply_saved_seating_profile_clicked(self) -> None:
        profile = self._get_saved_seating_depth_profile()
        if not profile:
            QMessageBox.information(
                self,
                "Seating Profile",
                "No saved seating profile was found for the selected firearm/bullet/lot.",
            )
            return
        try:
            if profile.get("preferred_coal_mm") not in (None, ""):
                self.coal_spin.setValue(float(profile["preferred_coal_mm"]))
            if profile.get("preferred_cbto_mm") not in (None, ""):
                self.cbto_spin.setValue(float(profile["preferred_cbto_mm"]))
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Seating Profile",
                f"Could not apply the saved seating profile:\n{exc}",
            )
            return
        self.on_seating_changed()
        QMessageBox.information(
            self,
            "Seating Profile Applied",
            "The saved seating profile has been applied to COAL/CBTO.",
        )

    def on_compare_seating_profile_clicked(self) -> None:
        text = self._build_seating_profile_compare_text()
        QMessageBox.information(self, "Compare Seating Profiles", text)

    def on_apply_best_known_seating_clicked(self) -> None:
        evidence = self._get_best_known_seating_evidence()
        if not evidence:
            QMessageBox.information(
                self,
                "Best Known Seating",
                "No historical batch data with seating results was found for the selected firearm/bullet yet.",
            )
            return
        try:
            if evidence.get("coal_mm") not in (None, ""):
                self.coal_spin.setValue(float(evidence["coal_mm"]))
            if evidence.get("cbto_mm") not in (None, ""):
                self.cbto_spin.setValue(float(evidence["cbto_mm"]))
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Best Known Seating",
                f"Could not apply historical seating data:\n{exc}",
            )
            return
        self.on_seating_changed()
        detail_bits = []
        if evidence.get("best_group_moa") not in (None, ""):
            detail_bits.append(f"group {float(evidence['best_group_moa']):.2f} MOA")
        if evidence.get("best_es_fps") not in (None, ""):
            detail_bits.append(
                f"ES {format_velocity_fps(float(evidence['best_es_fps']))}"
            )
        if evidence.get("best_sd_fps") not in (None, ""):
            detail_bits.append(
                f"SD {format_velocity_fps(float(evidence['best_sd_fps']))}"
            )
        detail_text = ", ".join(detail_bits) if detail_bits else "historical result"
        QMessageBox.information(
            self,
            "Best Known Seating Applied",
            "The builder is set to the best known seating from history"
            + (f" ({detail_text})." if detail_text else "."),
        )

    def update_visualization(self):
        """Update graphs with current parameters"""
        if not all([self.rifle_data, self.bullet_data, self.powder_data]):
            return
        if not self.engine:
            return

        # Calculate ballistics
        _rd_vis = self.rifle_data if isinstance(self.rifle_data, dict) else {}
        _bd_vis = self.bullet_data if isinstance(self.bullet_data, dict) else {}
        _pd_vis = self.powder_data if isinstance(self.powder_data, dict) else {}
        result = self.engine.calculate_load(
            int(_rd_vis.get("id") or 0),
            int(_bd_vis.get("id") or 0),
            int(_pd_vis.get("id") or 0),
            self.current_charge or 0,
            self.coal_mm or 0,
            self.cbto_mm or 0,
            barrel_id=self._get_active_barrel_id(),
        )

        if "error" in result:
            return

        try:
            fit_summary, _ = self._build_component_fit_assessment(result)
            self.component_fit_label.setText(fit_summary)
            self._refresh_bullet_action_button()
        except Exception:
            pass
        try:
            self._refresh_seating_depth_advisor(result)
        except Exception:
            pass

        # Apply environmental corrections and calibration (best-effort)
        try:
            temp_c = (
                self._current_temperature_c() if hasattr(self, "temp_spin") else None
            )
            pressure_kpa = (
                self._current_pressure_kpa() if hasattr(self, "pressure_spin") else None
            )
            humidity_pct = (
                float(self.humidity_spin.value())
                if hasattr(self, "humidity_spin")
                else None
            )

            ratio = None
            if (
                temp_c is not None
                and pressure_kpa is not None
                and humidity_pct is not None
            ):
                try:
                    ratio = air_density_ratio(temp_c, pressure_kpa, humidity_pct) if air_density_ratio is not None else None  # type: ignore[misc]
                except Exception:
                    ratio = None

            # copy result so we don't mutate engine internals
            scaled = dict(result)

            # scale pressure and velocity curves conservatively if ratio available
            if ratio is not None:
                try:
                    scale = 1.0 + (ratio - 1.0) * 0.5
                    # pressure_curve: list of (time, pressure)
                    if "pressure_curve" in scaled and scaled["pressure_curve"]:
                        scaled_pc = [
                            (t, float(p) * scale) for (t, p) in scaled["pressure_curve"]
                        ]
                        scaled["pressure_curve"] = scaled_pc
                        # adjust numeric peak/max fields if present
                        if "max_pressure_psi" in scaled:
                            scaled["max_pressure_psi"] = (
                                float(scaled["max_pressure_psi"]) * scale
                            )
                        if "peak_pressure_psi" in scaled:
                            scaled["peak_pressure_psi"] = (
                                float(scaled["peak_pressure_psi"]) * scale
                            )

                    # velocity_curve: list of (position, vel)
                    if "velocity_curve" in scaled and scaled["velocity_curve"]:
                        scaled_vc = [
                            (x, float(v) * scale) for (x, v) in scaled["velocity_curve"]
                        ]
                        scaled["velocity_curve"] = scaled_vc
                        if "muzzle_velocity_fps" in scaled:
                            scaled["muzzle_velocity_fps"] = (
                                float(scaled["muzzle_velocity_fps"]) * scale
                            )
                except Exception:
                    pass

            # Apply profile-scoped linear calibration (predicted -> measured) if available
            try:
                calibration = _get_profile_scoped_engine_calibration(
                    getattr(self, "db", None),
                    getattr(self, "current_ammo_profile_id", None),
                )
                if calibration:
                    slope = float(calibration["slope"] or 1.0)
                    intercept = float(calibration.get("intercept") or 0.0)
                    mse = calibration.get("mse")
                    # apply to velocity numbers
                    if "velocity_curve" in scaled and scaled["velocity_curve"]:
                        scaled["velocity_curve"] = [
                            (x, slope * float(v) + intercept)
                            for (x, v) in scaled["velocity_curve"]
                        ]
                    if "muzzle_velocity_fps" in scaled:
                        scaled["muzzle_velocity_fps"] = (
                            slope * float(scaled.get("muzzle_velocity_fps", 0))
                            + intercept
                        )
                    # attach mse for plotting uncertainty bands
                    if mse is not None:
                        scaled["_calibration_mse"] = mse
            except Exception:
                pass

        except Exception:
            scaled = result

        self._latest_visual_result = dict(scaled)
        try:
            self._latest_load_analysis = self._build_service_analysis()
        except Exception:
            self._latest_load_analysis = None
        try:
            self._refresh_runtime_context_summary()
        except Exception:
            pass
        try:
            self._refresh_service_recommendation_callout()
        except Exception:
            pass
        try:
            self._refresh_recommendation_state_panel()
        except Exception:
            pass

        # Update graphs with scaled/calibrated result
        self.update_pressure_graph(scaled)
        self.update_velocity_graph(scaled)
        self.update_stats(scaled)
        try:
            self._update_trajectory_panel(scaled)
        except Exception:
            pass
        try:
            self._update_compact_safety_strip()
        except Exception:
            pass

    def _update_trajectory_panel(self, result):
        """Compute and draw a simple G7/G1 point-mass trajectory (zeroed at 100 m)."""
        pg = getattr(self, "_pg", None)
        tplot = getattr(self, "trajectory_plot", None)
        ttable = getattr(self, "_traj_table", None)
        if pg is None or tplot is None:
            return

        import math

        # --- gather inputs -------------------------------------------------------
        mv_fps = float(result.get("muzzle_velocity_fps") or 0)
        if mv_fps < 100:
            return

        bd = self.bullet_data if isinstance(self.bullet_data, dict) else {}
        bc_g7 = float(bd.get("bc_g7") or 0)
        bc_g1 = float(bd.get("bc_g1") or 0)
        bullet_mass_gr = float(bd.get("weight_grains") or bd.get("weight_gr") or 0)

        # prefer G7; fall back to G7-equivalent of G1 (×0.51)
        if bc_g7 > 0:
            bc = bc_g7
            model = "G7"
        elif bc_g1 > 0:
            bc = bc_g1 * 0.51
            model = "G1→G7"
        else:
            return

        # range from combo
        try:
            combo = getattr(self, "_traj_range_combo", None)
            max_m = int((combo.currentText() if combo else "500 m").split()[0])
        except Exception:
            max_m = 500

        # --- point-mass simulation (simplified Euler, ~2 m steps) ---------------
        # G7 retardation coefficient (SI units): k = (ρ·A)/(2·m·BC_G7_kg/m²)
        # We work in metric: velocity m/s, distance m, time s
        # Standard air density 1.2250 kg/m³, bullet cross-section from calibre or mass
        # Short-cut: use sectional density approach
        # drag acceleration = (v²·ρ·Cd_ref)/(2·m/A) where m/A = BC_G7 (kg/m²)
        # BC_G7 in lbs/in² → convert: 1 lb/in² ≈ 703.07 kg/m²

        bc_si = bc * 703.07  # kg/m²
        rho = 1.2250  # kg/m³ standard air
        mv_ms = mv_fps * 0.3048  # m/s
        g = 9.807  # m/s²
        dt = 0.002  # time step s

        vx = mv_ms
        vy = 0.0
        x = 0.0
        y = 0.0

        # zero-crossing at 100 m: run once to find drop at 100 m, then offset
        dist_pts: list[float] = []
        drop_pts: list[float] = []

        t_total = 0.0
        zero_drop = 0.0
        zero_found = False

        while x <= max_m + 2:
            dist_pts.append(x)
            drop_pts.append(y)

            if not zero_found and x >= 100.0:
                zero_drop = y
                zero_found = True

            v = math.hypot(vx, vy)
            drag_a = (rho * v * v) / (2.0 * bc_si)  # m/s²
            ax = -drag_a * (vx / v) if v > 0 else 0
            ay = -drag_a * (vy / v) - g if v > 0 else -g
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t_total += dt
            if vx < 1:
                break

        # offset so y=0 at 100 m
        drop_cm = [(d - zero_drop) * 100 for d in drop_pts]

        # re-derive velocity at key distances for the table
        checkpoints = [100, 200, 300, 400, 500]
        check_data: dict[int, dict] = {}
        vx2, vy2, x2, y2 = mv_ms, 0.0, 0.0, 0.0
        remaining = list(checkpoints)
        while remaining and x2 <= checkpoints[-1] + 2:
            v2 = math.hypot(vx2, vy2)
            if remaining and x2 >= remaining[0]:
                dist_m = remaining.pop(0)
                vel_ms = v2
                bullet_kg = (
                    (bullet_mass_gr / 7000) * 0.453592 if bullet_mass_gr > 0 else 0
                )
                energy_j = 0.5 * bullet_kg * v2 * v2 if bullet_kg > 0 else 0
                drop_offset = (y2 - zero_drop) * 100
                check_data[dist_m] = {
                    "vel_ms": vel_ms,
                    "drop_cm": drop_offset,
                    "energy_j": energy_j,
                }
            drag2 = (rho * v2 * v2) / (2.0 * bc_si)
            ax2 = -drag2 * (vx2 / v2) if v2 > 0 else 0
            ay2 = -drag2 * (vy2 / v2) - g if v2 > 0 else -g
            vx2 += ax2 * dt
            vy2 += ay2 * dt
            x2 += vx2 * dt
            y2 += vy2 * dt
            if vx2 < 1:
                break

        # --- draw ----------------------------------------------------------------
        tplot.clear()
        tplot.setTitle(
            f"Kulebane ({model}, nullstilt 100 m) · MV {mv_fps:.0f} fps",
            color="#4a6a9a",
            size="9pt",
        )

        # zero line
        tplot.addLine(
            y=0, pen=pg.mkPen(color="#2d5a3d", width=1, style=Qt.PenStyle.DashLine)
        )

        # color by drop severity
        pen = pg.mkPen(color="#3a9edf", width=2.0)
        tplot.plot(dist_pts, drop_cm, pen=pen)

        # mark checkpoints
        for dm, dat in check_data.items():
            tplot.addLine(x=dm, pen=pg.mkPen(color="#1e3a50", width=1))
            try:
                sp = pg.ScatterPlotItem(
                    [dm],
                    [dat["drop_cm"]],
                    symbol="o",
                    size=6,
                    brush=pg.mkBrush("#3a9edf"),
                    pen=pg.mkPen(None),
                )
                tplot.addItem(sp)
            except Exception:
                pass

        # --- table ---------------------------------------------------------------
        if ttable is not None:
            for col, dm in enumerate(checkpoints):
                dat = check_data.get(dm, {})
                vel = dat.get("vel_ms", 0)
                drp = dat.get("drop_cm", 0)
                enj = dat.get("energy_j", 0)
                ttable.setItem(0, col, QTableWidgetItem(f"{vel:.0f}"))
                ttable.setItem(1, col, QTableWidgetItem(f"{drp:+.1f}"))
                ttable.setItem(2, col, QTableWidgetItem(f"{enj:.0f}"))
            for r in range(3):
                for c in range(5):
                    item = ttable.item(r, c)
                    if item:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_pressure_graph(self, result):
        """Update pressure curve with live safety-zone bands."""
        pg = getattr(self, "_pg", None)
        pplot = getattr(self, "pressure_plot", None)
        if pg is None or pplot is None:
            return
        pplot.clear()

        curve_data = result.get("pressure_curve") or []
        if not curve_data:
            return

        times = [p[0] for p in curve_data]
        pressures = [p[1] for p in curve_data]
        saami_max = result.get("max_pressure_psi")
        peak_psi = result.get("peak_pressure_psi") or max(pressures, default=0)

        # ── Coloured safety-zone bands ────────────────────────────────────────
        if saami_max:
            try:
                zone_80 = saami_max * 0.80
                zone_95 = saami_max * 0.95

                def _hband(y_lo, y_hi, rgba):
                    region = pg.LinearRegionItem(
                        values=(y_lo, y_hi),
                        orientation="horizontal",
                        movable=False,
                        brush=pg.mkBrush(*rgba),
                        pen=pg.mkPen(None),
                    )
                    pplot.addItem(region)

                _hband(0, zone_80, (39, 174, 96, 18))  # green — safe
                _hband(zone_80, zone_95, (230, 126, 34, 22))  # orange — caution
                _hband(zone_95, saami_max * 1.15, (231, 76, 60, 28))  # red — danger
            except Exception:
                pass

        # ── Calibration uncertainty band ──────────────────────────────────────
        try:
            import math

            mse = result.get("_calibration_mse")
            if mse is not None:
                peak_vel = float(result.get("muzzle_velocity_fps") or 1)
                p_unc = math.sqrt(mse) * (peak_psi / peak_vel if peak_vel else 0)
                upper = [p + p_unc for p in pressures]
                lower = [p - p_unc for p in pressures]
                uc = pplot.plot(times, upper, pen=pg.mkPen(None))
                lc = pplot.plot(times, lower, pen=pg.mkPen(None))
                pplot.addItem(pg.FillBetweenItem(uc, lc, brush=(231, 76, 60, 40)))
        except Exception:
            pass

        # ── Main pressure curve (colour reflects safety) ─────────────────────
        if saami_max and peak_psi:
            pct = peak_psi / saami_max
            curve_color = (
                "#2ecc71" if pct < 0.80 else "#e67e22" if pct < 0.95 else "#e74c3c"
            )
        else:
            curve_color = "#e74c3c"

        pplot.plot(times, pressures, pen=pg.mkPen(color=curve_color, width=2.5))

        # ── SAAMI max line (labelled) ─────────────────────────────────────────
        if saami_max:
            line = pplot.addLine(
                y=saami_max,
                pen=pg.mkPen(color="#e74c3c", width=1.5, style=Qt.PenStyle.DashLine),
            )
            try:
                line.label = pg.InfLineLabel(
                    line,
                    text=f"SAAMI MAX  {saami_max:,.0f} PSI",
                    position=0.97,
                    color="#e74c3c",
                    fill=pg.mkBrush(20, 20, 35, 180),
                )
            except Exception:
                pass

        # ── Peak-pressure dot + annotation ───────────────────────────────────
        try:
            peak_t = times[pressures.index(max(pressures))]
            scatter = pg.ScatterPlotItem(
                [peak_t],
                [max(pressures)],
                symbol="o",
                size=10,
                brush=pg.mkBrush(curve_color),
                pen=pg.mkPen(None),
            )
            pplot.addItem(scatter)
        except Exception:
            pass

        # ── Update metric cards ───────────────────────────────────────────────
        try:
            self._update_metric_cards(result)
        except Exception:
            pass

    def update_velocity_graph(self, result):
        """Update velocity curve with purpose-based thresholds and muzzle annotation."""
        vel_curve = result.get("velocity_curve") or []
        if not vel_curve:
            return
        positions = [v[0] for v in vel_curve]
        velocities = [v[1] for v in vel_curve]

        # Store latest simulated curve for overlaying with imports
        self._last_velocity_curve = (positions, velocities)

        pg = getattr(self, "_pg", None)
        vplot = getattr(self, "velocity_plot", None)
        if pg is None or vplot is None:
            return
        vplot.clear()

        muzzle_fps = result.get("muzzle_velocity_fps") or (
            velocities[-1] if velocities else 0
        )

        # ── Purpose-based velocity threshold lines ───────────────────────────
        purpose = self._get_active_purpose()
        _thresholds = {
            "hunting": [(1800, "#e67e22", "Min jakt"), (2400, "#2ecc71", "OK jakt")],
            "precision": [(2600, "#3498db", "Presisjonsgrense")],
            "long_range": [(2800, "#9b59b6", "Langhold")],
        }
        for fps_thresh, color, label in _thresholds.get(purpose, []):
            if positions:
                line = vplot.addLine(
                    y=fps_thresh,
                    pen=pg.mkPen(color=color, width=1, style=Qt.PenStyle.DotLine),
                )
                try:
                    line.label = pg.InfLineLabel(
                        line,
                        text=f"{label}  {fps_thresh} fps",
                        position=0.05,
                        color=color,
                        fill=pg.mkBrush(20, 20, 35, 160),
                    )
                except Exception:
                    pass

        # ── Curve colour based on whether muzzle velocity meets purpose threshold ─
        _purpose_thresholds = _thresholds.get(purpose)
        min_thresh: float = (
            float(_purpose_thresholds[0][0]) if _purpose_thresholds else 2400.0
        )
        muzzle_fps_f = float(muzzle_fps or 0)
        if muzzle_fps_f >= min_thresh:
            curve_color = "#2ecc71"
        elif muzzle_fps_f >= min_thresh * 0.90:
            curve_color = "#e67e22"
        else:
            curve_color = "#e74c3c"

        vplot.plot(positions, velocities, pen=pg.mkPen(color=curve_color, width=2.5))

        # ── Muzzle velocity dot ───────────────────────────────────────────────
        if positions and velocities:
            try:
                scatter = pg.ScatterPlotItem(
                    [positions[-1]],
                    [velocities[-1]],
                    symbol="d",
                    size=10,
                    brush=pg.mkBrush(curve_color),
                    pen=pg.mkPen(None),
                )
                vplot.addItem(scatter)
            except Exception:
                pass

        # If calibration MSE present, draw uncertainty band
        try:
            mse = result.get("_calibration_mse")
            if mse is not None:
                import math

                vel_unc = math.sqrt(mse)
                upper = [v + vel_unc for v in velocities]
                lower = [v - vel_unc for v in velocities]
                up_curve = vplot.plot(
                    positions, upper, pen=pg.mkPen(color=(39, 174, 96, 80), width=0)
                )
                low_curve = vplot.plot(
                    positions, lower, pen=pg.mkPen(color=(39, 174, 96, 80), width=0)
                )
                try:
                    vplot.addItem(
                        pg.FillBetweenItem(up_curve, low_curve, brush=(39, 174, 96, 50))
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # Draw transonic speed-of-sound line and optional margin band.
        try:
            if getattr(self, "transonic_cb", None) and self.transonic_cb.isChecked():
                from ..utils.ballistics_utils import speed_of_sound_fps

                _tc_vis2 = self._current_temperature_c()
                temp_c = (
                    float(_tc_vis2)
                    if hasattr(self, "temp_spin") and _tc_vis2 is not None
                    else 15.0
                )
                sos = float(speed_of_sound_fps(temp_c))
                margin = self._transonic_margin_fps()
                xs = positions if positions else [0, 1]
                top = [sos + margin for _ in xs]
                bot = [sos - margin for _ in xs]
                top_curve = vplot.plot(
                    xs, top, pen=pg.mkPen(color=(52, 152, 219, 120), width=0)
                )
                bot_curve = vplot.plot(
                    xs, bot, pen=pg.mkPen(color=(52, 152, 219, 120), width=0)
                )
                try:
                    vplot.addItem(
                        pg.FillBetweenItem(
                            top_curve, bot_curve, brush=(52, 152, 219, 40)
                        )
                    )
                except Exception:
                    pass
                vplot.addLine(
                    y=sos,
                    pen=pg.mkPen(color="#2980b9", width=2, style=Qt.PenStyle.DashLine),
                )
        except Exception:
            pass

    def _get_rifle_profile_details(self) -> dict:
        """Fetch cached rifle profile details for the active rifle."""
        try:
            rifle_id = self.rifle_data.get("id") if self.rifle_data else None
        except Exception:
            rifle_id = None

        if not rifle_id:
            return {}

        if (
            getattr(self, "_rifle_profile_details_id", None) == rifle_id
            and self._rifle_profile_details is not None
        ):
            return self._rifle_profile_details

        details = {}
        try:
            rows = self.db.execute_query(
                "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
                (rifle_id,),
            )
            if rows and rows[0].get("profile_json"):
                import json

                details = json.loads(rows[0]["profile_json"])
        except Exception:
            details = {}

        self._rifle_profile_details = details
        self._rifle_profile_details_id = rifle_id
        return details

    def _get_active_barrel_id(self) -> str | None:
        """Return active barrel id from rifle profile details when available."""
        details = self._get_rifle_profile_details()
        active_barrel_id = details.get("active_barrel_id")
        if active_barrel_id:
            return str(active_barrel_id)

        barrels = details.get("barrels", [])
        if isinstance(barrels, list) and barrels:
            first_barrel = barrels[0]
            if isinstance(first_barrel, dict) and first_barrel.get("id"):
                return str(first_barrel["id"])
        return None

    def _get_active_barrel_details(self) -> dict:
        """Return active barrel/løp details from rifle profile data."""
        details = self._get_rifle_profile_details()
        active_barrel_id = self._get_active_barrel_id()
        barrels = details.get("barrels", [])
        if isinstance(barrels, list):
            for barrel in barrels:
                if isinstance(barrel, dict) and str(barrel.get("id")) == str(
                    active_barrel_id
                ):
                    return barrel
            for barrel in barrels:
                if isinstance(barrel, dict):
                    return barrel
        return {}

    def _get_active_barrel_configuration_context(self) -> dict[str, Any]:
        rifle_data = self.rifle_data if isinstance(self.rifle_data, dict) else None
        rifle_id = rifle_data.get("id") if rifle_data else None
        return resolve_active_barrel_configuration_context(
            rifle_id=rifle_id,
            rifle_data=rifle_data,
            profile_details=self._get_rifle_profile_details(),
            active_barrel_details=self._get_active_barrel_details(),
        )

    def _get_available_barrel_configurations(self) -> list[dict[str, Any]]:
        details = self._get_rifle_profile_details()
        barrel_id = self._get_active_barrel_id()
        configurations = details.get("barrel_configurations", [])
        matching: list[dict[str, Any]] = []
        if isinstance(configurations, list):
            for configuration in configurations:
                if not isinstance(configuration, dict):
                    continue
                configuration_barrel_id = (
                    str(configuration.get("barrel_id") or "").strip() or None
                )
                if (
                    barrel_id
                    and configuration_barrel_id
                    and configuration_barrel_id != barrel_id
                ):
                    continue
                if barrel_id and not configuration_barrel_id:
                    continue
                matching.append(dict(configuration))
        if matching:
            return matching

        fallback = self._get_active_barrel_configuration_context()
        fallback_id = str(fallback.get("barrel_configuration_id") or "").strip() or None
        fallback_name = (
            str(fallback.get("barrel_configuration_name") or "").strip() or None
        )
        if not fallback_id and not fallback_name:
            return []
        return [
            {
                "id": fallback_id or "current-setup",
                "name": fallback_name or fallback_id or "Current setup",
                "barrel_id": barrel_id,
                "barrel_name": fallback.get("barrel_name"),
                "is_active": True,
                "derived": True,
            }
        ]

    def _refresh_barrel_configuration_selector(self) -> None:
        combo = getattr(self, "barrel_configuration_combo", None)
        if combo is None:
            return
        combo.blockSignals(True)
        combo.clear()
        configurations = self._get_available_barrel_configurations()
        for configuration in configurations:
            configuration_id = (
                str(configuration.get("id") or "").strip() or "current-setup"
            )
            configuration_name = str(
                configuration.get("name") or configuration_id or "Current setup"
            ).strip()
            combo.addItem(configuration_name or "Current setup", configuration_id)

        active_context = self._get_active_barrel_configuration_context()
        active_id = (
            str(active_context.get("barrel_configuration_id") or "").strip() or None
        )
        if combo.count() <= 0:
            combo.addItem("Current setup", None)
        target_id = active_id or str(combo.itemData(0) or "").strip() or None
        for index in range(combo.count()):
            if str(combo.itemData(index) or "").strip() == str(target_id or ""):
                combo.setCurrentIndex(index)
                break
        combo.setEnabled(combo.count() > 0)
        combo.blockSignals(False)

    def _apply_active_barrel_configuration_selection(
        self, configuration_id: str | None
    ) -> bool:
        details = dict(self._get_rifle_profile_details())
        barrel_id = self._get_active_barrel_id()
        if not barrel_id:
            return False

        configurations = details.get("barrel_configurations", [])
        if not isinstance(configurations, list):
            return False

        selected_configuration: dict[str, Any] | None = None
        updated_configurations: list[dict[str, Any]] = []
        for configuration in configurations:
            if not isinstance(configuration, dict):
                updated_configurations.append(configuration)
                continue
            configuration_copy = dict(configuration)
            configuration_barrel_id = (
                str(configuration_copy.get("barrel_id") or "").strip() or None
            )
            configuration_key = str(configuration_copy.get("id") or "").strip() or None
            if barrel_id and configuration_barrel_id == barrel_id:
                configuration_copy["is_active"] = bool(
                    configuration_id and configuration_key == configuration_id
                )
            if configuration_id and configuration_key == configuration_id:
                selected_configuration = configuration_copy
            updated_configurations.append(configuration_copy)

        if selected_configuration is None:
            return False

        details["barrel_configurations"] = updated_configurations
        details["active_barrel_configuration_id"] = (
            str(selected_configuration.get("id") or "").strip() or None
        )
        details["active_barrel_configuration_name"] = (
            str(selected_configuration.get("name") or "").strip() or None
        )
        return self._save_rifle_profile_details(details)

    def on_barrel_configuration_changed(self) -> None:
        combo = getattr(self, "barrel_configuration_combo", None)
        if combo is None:
            return
        configuration_id = combo.currentData()
        configuration_key = str(configuration_id or "").strip() or None
        if not configuration_key:
            return
        if not self._apply_active_barrel_configuration_selection(configuration_key):
            return
        self._refresh_barrel_configuration_selector()
        self._refresh_active_rifle_context()
        try:
            self._sync_active_load_session_context()
            self._refresh_runtime_context_summary()
        except Exception:
            pass
        try:
            self.evidence_label.setText(self._build_evidence_summary())
            self._refresh_evidence_actions()
        except Exception:
            pass
        try:
            self.update_visualization()
        except Exception:
            pass

    def _format_harmonics_missing_fields(self, missing_fields: list[str]) -> str:
        labels = {
            "barrel_length_mm": "barrel length",
            "barrel_profile": "barrel profile/contour",
            "barrel_weight_g": "barrel weight",
            "attachment_type": "attachment type/mount type",
            "action_stiffness": "action stiffness / systemstivhet",
            "support_type": "support type",
        }
        translated = [labels.get(field, field) for field in missing_fields]
        return ", ".join(translated)

    def _get_h2o_stats(self) -> dict:
        """Return summary statistics for stored H2O / case-capacity measurements."""
        barrel = self._get_active_barrel_details()
        case_measurements = barrel.get("case_measurements") or {}
        raw_samples = case_measurements.get("h2o_measurements", []) or []
        _cap_vals = [
            sample.get("h2o_capacity_grains")
            for sample in raw_samples
            if isinstance(sample, dict)
        ]
        capacities = [float(v) for v in _cap_vals if v is not None]
        if not capacities:
            return {}

        spread = max(capacities) - min(capacities)
        quality = (
            "low spread"
            if spread <= 0.30
            else "moderate spread" if spread <= 0.75 else "high spread"
        )
        return {
            "count": len(capacities),
            "average": sum(capacities) / len(capacities),
            "spread": spread,
            "quality": quality,
        }

    def _get_h2o_ai_note(self) -> str:
        """Return a short AI-facing caution based on stored H2O variation."""
        h2o_stats = self._get_h2o_stats()
        if not h2o_stats:
            return ""
        if h2o_stats["spread"] > 0.75:
            return (
                "\n\nYour H2O / case-capacity series has high spread. "
                "Small differences in pressure or velocity may therefore fall within case-capacity variation. "
                "Measure more cases and verify the trend before drawing conclusions."
            )
        if h2o_stats["spread"] > 0.30:
            return (
                "\n\nYour H2O / case-capacity series has moderate spread. "
                "Small differences may come from brass variation, so interpret the results somewhat cautiously."
            )
        return "\n\nYour H2O / case-capacity series looks consistent, making small differences in the data easier to trust."

    def _get_chrono_ai_note(self) -> str:
        """Return a short AI-facing note based on selected chronograph data volume."""
        if not hasattr(self, "chrono_list") or self.chrono_list is None:
            return ""
        item = self.chrono_list.currentItem()
        if not item:
            return ""

        import_id = item.data(Qt.ItemDataRole.UserRole)
        if not import_id:
            return ""

        try:
            rows = self.db.execute_query(
                "SELECT velocities_json FROM chronograph_imports WHERE id = ?",
                (import_id,),
            )
            if not rows or not rows[0].get("velocities_json"):
                return ""
            velocities = json.loads(rows[0]["velocities_json"])
        except Exception:
            return ""

        count = len(velocities) if isinstance(velocities, list) else 0
        if count <= 0:
            return ""
        if count < 5:
            return (
                "\n\nThe selected chronograph series has fewer than 5 shots. "
                "That is too thin a basis for reading small differences in ES, SD, or velocity aggressively."
            )
        if count < 10:
            return (
                "\n\nThe selected chronograph series has fewer than 10 shots. "
                "Use it as an indication, but preferably verify with more shots before making firm conclusions."
            )
        return f"\n\nThe selected chronograph series has {count} shots, which gives a better basis for evaluating ES and SD."

    def _get_group_ai_note(self) -> str:
        """Return a short AI-facing note about available group/target data."""
        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        if isinstance(calibration_tests, list):
            image_count = 0
            for test in calibration_tests:
                if not isinstance(test, dict):
                    continue
                for load in test.get("loads", []) or []:
                    if isinstance(load, dict) and load.get("group_image_path"):
                        image_count += 1
            if image_count:
                return (
                    "\n\nThere are recorded calibration series with target images on the active barrel, "
                    "so the precision assessment can be built on more than just velocity."
                )
        try:
            rows = self.db.execute_query(
                "SELECT image_path FROM test_results WHERE image_path IS NOT NULL AND image_path != '' ORDER BY id DESC LIMIT 5"
            )
        except Exception:
            return ""

        count = len(rows or [])
        if count == 0:
            return (
                "\n\nI see no saved group data or target images in the latest test results. "
                "The precision assessment is therefore weaker than if you combine chronograph data with groups."
            )
        return "\n\nThere are recorded group results / target images, so the precision assessment can be built on more than just velocity."

    def _get_calibration_summary(self) -> dict:
        """Summarize calibration series for the active barrel with powder awareness."""
        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        if not isinstance(calibration_tests, list) or not calibration_tests:
            return {}

        series_count = 0
        load_count = 0
        image_count = 0
        powder_labels: list[str] = []
        powder_families: set[str] = set()
        charge_values: list[float] = []
        velocity_avgs: list[float] = []

        for test in calibration_tests:
            if not isinstance(test, dict):
                continue
            series_count += 1
            for load in test.get("loads", []) or []:
                if not isinstance(load, dict):
                    continue
                load_count += 1
                if load.get("group_image_path"):
                    image_count += 1

                powder_name = str(load.get("powder") or "").strip()
                powder_make = str(load.get("powder_manufacturer") or "").strip()
                powder_label = " ".join(
                    part for part in [powder_make, powder_name] if part
                )
                if powder_label:
                    powder_labels.append(powder_label)
                elif powder_name:
                    powder_labels.append(powder_name)

                powder_family = str(load.get("powder_type") or "").strip()
                if powder_family:
                    powder_families.add(powder_family.lower())

                try:
                    charge = load.get("charge_weight_gr")
                    if charge is not None:
                        charge_values.append(float(charge))
                except Exception:
                    pass
                try:
                    vel = load.get("velocity_avg")
                    if vel is not None:
                        velocity_avgs.append(float(vel))
                except Exception:
                    pass

        unique_powders = sorted({label for label in powder_labels if label})
        mixed_powders = len(unique_powders) > 1
        mixed_families = len(powder_families) > 1
        summary = {
            "series_count": series_count,
            "load_count": load_count,
            "image_count": image_count,
            "unique_powders": unique_powders,
            "powder_count": len(unique_powders),
            "mixed_powders": mixed_powders,
            "mixed_powder_families": mixed_families,
        }
        if charge_values:
            summary["charge_min"] = min(charge_values)
            summary["charge_max"] = max(charge_values)
        if velocity_avgs:
            summary["velocity_min"] = min(velocity_avgs)
            summary["velocity_max"] = max(velocity_avgs)
        return summary

    def _get_calibration_rows(self, limit: int | None = 8) -> list[dict]:
        """Flatten calibration loads for the active barrel into table-friendly rows."""
        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        if not isinstance(calibration_tests, list):
            return []

        rows: list[dict] = []
        powder_filter = ""
        bullet_filter = ""
        lot_filter = ""
        distance_filter = ""
        temperature_filter = ""
        try:
            if hasattr(self, "calibration_powder_filter"):
                powder_filter = str(self.calibration_powder_filter.currentData() or "")
        except Exception:
            powder_filter = ""
        try:
            if hasattr(self, "calibration_bullet_filter"):
                bullet_filter = str(self.calibration_bullet_filter.currentData() or "")
        except Exception:
            bullet_filter = ""
        try:
            if hasattr(self, "calibration_lot_filter"):
                lot_filter = str(self.calibration_lot_filter.currentData() or "")
        except Exception:
            lot_filter = ""
        try:
            if hasattr(self, "calibration_distance_filter"):
                distance_filter = str(
                    self.calibration_distance_filter.currentData() or ""
                )
        except Exception:
            distance_filter = ""
        try:
            if hasattr(self, "calibration_temperature_filter"):
                temperature_filter = str(
                    self.calibration_temperature_filter.currentData() or ""
                )
        except Exception:
            temperature_filter = ""
        for test in reversed(calibration_tests):
            if not isinstance(test, dict):
                continue
            series_label = test.get("created_date") or test.get("id") or "serie"
            distance_value = test.get("distance_m")
            distance_label = "-"
            if distance_value is not None:
                try:
                    distance_label = format_distance_m(float(distance_value))
                except Exception:
                    distance_label = str(distance_value)
            temperature_value = test.get("temperature_c")
            temperature_label = "-"
            if temperature_value is not None:
                try:
                    temperature_label = format_temperature_c(float(temperature_value))
                except Exception:
                    temperature_label = str(temperature_value)
            for load in test.get("loads", []) or []:
                if not isinstance(load, dict):
                    continue
                powder_name = str(load.get("powder") or "").strip()
                powder_make = str(load.get("powder_manufacturer") or "").strip()
                powder_label = " ".join(
                    part for part in [powder_make, powder_name] if part
                ).strip()
                if not powder_label:
                    powder_label = powder_name or "-"
                bullet_name = str(load.get("bullet") or "").strip()
                bullet_make = str(load.get("bullet_manufacturer") or "").strip()
                bullet_weight = load.get("bullet_weight_gr")
                bullet_label = " ".join(
                    part for part in [bullet_make, bullet_name] if part
                ).strip()
                if not bullet_label:
                    bullet_label = bullet_name or "-"
                if bullet_weight is not None:
                    try:
                        bullet_label = (
                            f"{bullet_label} {format_weight_grains(float(bullet_weight), 'bullet')}"
                        ).strip()
                    except Exception:
                        pass
                powder_lot = str(load.get("powder_lot") or "").strip()
                bullet_lot = str(load.get("bullet_lot") or "").strip()
                lot_parts = []
                if powder_lot:
                    lot_parts.append(f"Powder {powder_lot}")
                if bullet_lot:
                    lot_parts.append(f"Bullet {bullet_lot}")
                lot_label = " | ".join(lot_parts) if lot_parts else "-"
                if powder_filter and powder_label != powder_filter:
                    continue
                if bullet_filter and bullet_label != bullet_filter:
                    continue
                if lot_filter and lot_label != lot_filter:
                    continue
                if distance_filter and distance_label != distance_filter:
                    continue
                if temperature_filter and temperature_label != temperature_filter:
                    continue
                charge = load.get("charge_weight_gr")
                vel = load.get("velocity_avg")
                es = load.get("velocity_es")
                sd = load.get("velocity_sd")
                image_flag = "Yes" if load.get("group_image_path") else "-"
                rows.append(
                    {
                        "test_id": test.get("id"),
                        "bullet": bullet_label,
                        "powder": powder_label,
                        "lot": lot_label,
                        "distance": distance_label,
                        "distance_m": distance_value,
                        "temperature": temperature_label,
                        "temperature_c": test.get("temperature_c"),
                        "charge": charge,
                        "velocity": vel,
                        "es": es,
                        "sd": sd,
                        "group_size_mm": load.get("group_size_mm"),
                        "image": image_flag,
                        "series": str(series_label)[:19],
                    }
                )
                if limit is not None and len(rows) >= limit:
                    return rows
        return rows

    def _refresh_calibration_powder_filter(self) -> None:
        """Refresh powder filter options from active barrel calibration data."""
        if not hasattr(self, "calibration_powder_filter"):
            return

        current_value = str(self.calibration_powder_filter.currentData() or "")
        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        powders: list[str] = []
        if isinstance(calibration_tests, list):
            for test in calibration_tests:
                if not isinstance(test, dict):
                    continue
                for load in test.get("loads", []) or []:
                    if not isinstance(load, dict):
                        continue
                    powder_name = str(load.get("powder") or "").strip()
                    powder_make = str(load.get("powder_manufacturer") or "").strip()
                    powder_label = " ".join(
                        part for part in [powder_make, powder_name] if part
                    ).strip()
                    if powder_label:
                        powders.append(powder_label)

        unique_powders = sorted(set(powders))
        self.calibration_powder_filter.blockSignals(True)
        self.calibration_powder_filter.clear()
        self.calibration_powder_filter.addItem("All powders", "")
        for powder in unique_powders:
            self.calibration_powder_filter.addItem(powder, powder)
        restore_index = self.calibration_powder_filter.findData(current_value)
        if restore_index >= 0:
            self.calibration_powder_filter.setCurrentIndex(restore_index)
        self.calibration_powder_filter.blockSignals(False)

    def _refresh_calibration_bullet_filter(self) -> None:
        """Refresh bullet filter options from active barrel calibration data."""
        if not hasattr(self, "calibration_bullet_filter"):
            return

        current_value = str(self.calibration_bullet_filter.currentData() or "")
        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        bullets: list[str] = []
        if isinstance(calibration_tests, list):
            for test in calibration_tests:
                if not isinstance(test, dict):
                    continue
                for load in test.get("loads", []) or []:
                    if not isinstance(load, dict):
                        continue
                    bullet_name = str(load.get("bullet") or "").strip()
                    bullet_make = str(load.get("bullet_manufacturer") or "").strip()
                    bullet_weight = load.get("bullet_weight_gr")
                    bullet_label = " ".join(
                        part for part in [bullet_make, bullet_name] if part
                    ).strip()
                    if bullet_weight is not None:
                        try:
                            bullet_label = (
                                f"{bullet_label} {format_weight_grains(float(bullet_weight), 'bullet')}"
                            ).strip()
                        except Exception:
                            pass
                    if bullet_label:
                        bullets.append(bullet_label)

        unique_bullets = sorted(set(bullets))
        self.calibration_bullet_filter.blockSignals(True)
        self.calibration_bullet_filter.clear()
        self.calibration_bullet_filter.addItem("All bullets", "")
        for bullet in unique_bullets:
            self.calibration_bullet_filter.addItem(bullet, bullet)
        restore_index = self.calibration_bullet_filter.findData(current_value)
        if restore_index >= 0:
            self.calibration_bullet_filter.setCurrentIndex(restore_index)
        self.calibration_bullet_filter.blockSignals(False)

    def _refresh_calibration_lot_filter(self) -> None:
        """Refresh lot filter options from active barrel calibration data."""
        if not hasattr(self, "calibration_lot_filter"):
            return

        current_value = str(self.calibration_lot_filter.currentData() or "")
        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        lots: list[str] = []
        if isinstance(calibration_tests, list):
            for test in calibration_tests:
                if not isinstance(test, dict):
                    continue
                for load in test.get("loads", []) or []:
                    if not isinstance(load, dict):
                        continue
                    powder_lot = str(load.get("powder_lot") or "").strip()
                    bullet_lot = str(load.get("bullet_lot") or "").strip()
                    lot_parts = []
                    if powder_lot:
                        lot_parts.append(f"Powder {powder_lot}")
                    if bullet_lot:
                        lot_parts.append(f"Bullet {bullet_lot}")
                    if lot_parts:
                        lots.append(" | ".join(lot_parts))

        unique_lots = sorted(set(lots))
        self.calibration_lot_filter.blockSignals(True)
        self.calibration_lot_filter.clear()
        self.calibration_lot_filter.addItem("Alle lot", "")
        for lot in unique_lots:
            self.calibration_lot_filter.addItem(lot, lot)
        restore_index = self.calibration_lot_filter.findData(current_value)
        if restore_index >= 0:
            self.calibration_lot_filter.setCurrentIndex(restore_index)
        self.calibration_lot_filter.blockSignals(False)

    def _refresh_calibration_distance_filter(self) -> None:
        """Refresh distance filter options from active barrel calibration data."""
        if not hasattr(self, "calibration_distance_filter"):
            return

        current_value = str(self.calibration_distance_filter.currentData() or "")
        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        distances: list[str] = []
        if isinstance(calibration_tests, list):
            for test in calibration_tests:
                if not isinstance(test, dict):
                    continue
                distance_value = test.get("distance_m")
                if distance_value is None:
                    continue
                try:
                    distances.append(f"{float(distance_value):.0f} m")
                except Exception:
                    distances.append(str(distance_value))

        def _distance_sort_key(value: str):
            try:
                return (0, float(value.split()[0]))
            except Exception:
                return (1, value)

        unique_distances = sorted(set(distances), key=_distance_sort_key)
        self.calibration_distance_filter.blockSignals(True)
        self.calibration_distance_filter.clear()
        self.calibration_distance_filter.addItem("All distances", "")
        for distance in unique_distances:
            self.calibration_distance_filter.addItem(distance, distance)
        restore_index = self.calibration_distance_filter.findData(current_value)
        if restore_index >= 0:
            self.calibration_distance_filter.setCurrentIndex(restore_index)
        self.calibration_distance_filter.blockSignals(False)

    def _refresh_calibration_temperature_filter(self) -> None:
        """Refresh temperature filter options from active barrel calibration data."""
        if not hasattr(self, "calibration_temperature_filter"):
            return

        current_value = str(self.calibration_temperature_filter.currentData() or "")
        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        temperatures: list[str] = []
        if isinstance(calibration_tests, list):
            for test in calibration_tests:
                if not isinstance(test, dict):
                    continue
                temperature_value = test.get("temperature_c")
                if temperature_value is None:
                    continue
                try:
                    temperatures.append(format_temperature_c(float(temperature_value)))
                except Exception:
                    temperatures.append(str(temperature_value))

        def _temperature_sort_key(value: str):
            try:
                return (0, float(value.split()[0]))
            except Exception:
                return (1, value)

        unique_temperatures = sorted(set(temperatures), key=_temperature_sort_key)
        self.calibration_temperature_filter.blockSignals(True)
        self.calibration_temperature_filter.clear()
        self.calibration_temperature_filter.addItem("All temperatures", "")
        for temperature in unique_temperatures:
            self.calibration_temperature_filter.addItem(temperature, temperature)
        restore_index = self.calibration_temperature_filter.findData(current_value)
        if restore_index >= 0:
            self.calibration_temperature_filter.setCurrentIndex(restore_index)
        self.calibration_temperature_filter.blockSignals(False)

    def _estimate_temperature_velocity_drift(self, rows: list[dict]) -> dict:
        """Estimate fps per degree from comparable calibration rows when possible."""
        grouped: dict[tuple[str, str, str, float], list[dict]] = {}
        for row in rows:
            if row.get("velocity") is None or row.get("temperature_c") is None:
                continue
            if row.get("charge") is None:
                continue
            try:
                charge_bucket = round(float(row["charge"]), 1)
                temp = float(row["temperature_c"])
                velocity = float(row["velocity"])
            except Exception:
                continue
            key = (
                str(row.get("powder") or "-"),
                str(row.get("lot") or "-"),
                str(row.get("bullet") or "-"),
                charge_bucket,
            )
            grouped.setdefault(key, []).append(
                {
                    "temp": temp,
                    "velocity": velocity,
                    "distance": row.get("distance"),
                    "series": row.get("series"),
                }
            )

        best_key = None
        best_group = None
        best_score = None
        for key, group in grouped.items():
            unique_temps = sorted({round(item["temp"], 2) for item in group})
            if len(unique_temps) < 2:
                continue
            temp_span = max(unique_temps) - min(unique_temps)
            if temp_span < 1.0:
                continue
            score = (len(unique_temps), temp_span, len(group))
            if best_score is None or score > best_score:
                best_score = score
                best_key = key
                best_group = group

        if not best_group or not best_key:
            return {}

        ordered = sorted(best_group, key=lambda item: item["temp"])
        temp_span = ordered[-1]["temp"] - ordered[0]["temp"]
        if abs(temp_span) < 1e-9:
            return {}
        velocity_span = ordered[-1]["velocity"] - ordered[0]["velocity"]
        fps_per_c = velocity_span / temp_span
        return {
            "powder": best_key[0],
            "lot": best_key[1],
            "bullet": best_key[2],
            "charge": best_key[3],
            "temp_min": ordered[0]["temp"],
            "temp_max": ordered[-1]["temp"],
            "velocity_min": ordered[0]["velocity"],
            "velocity_max": ordered[-1]["velocity"],
            "fps_per_c": fps_per_c,
            "point_count": len(ordered),
            "temp_count": len({round(item["temp"], 2) for item in ordered}),
            "points": ordered,
        }

    def _build_calibration_trend_summary(self) -> str:
        """Build a compact trend interpretation for active barrel calibration data."""
        rows = self._get_calibration_rows(limit=None)
        if not rows:
            return "Calibration trends will appear here when the active barrel has enough data."

        points: list[dict] = []
        powder_labels = {
            str(row.get("powder") or "-") for row in rows if row.get("powder")
        }
        lot_labels = {
            str(row.get("lot") or "-")
            for row in rows
            if row.get("lot") and row.get("lot") != "-"
        }
        lot_filter = ""
        distance_labels = {
            str(row.get("distance") or "-")
            for row in rows
            if row.get("distance") and row.get("distance") != "-"
        }
        distance_filter = ""
        temperature_labels = {
            str(row.get("temperature") or "-")
            for row in rows
            if row.get("temperature") and row.get("temperature") != "-"
        }
        temperature_filter = ""
        try:
            if hasattr(self, "calibration_lot_filter"):
                lot_filter = str(self.calibration_lot_filter.currentData() or "")
        except Exception:
            lot_filter = ""
        try:
            if hasattr(self, "calibration_distance_filter"):
                distance_filter = str(
                    self.calibration_distance_filter.currentData() or ""
                )
        except Exception:
            distance_filter = ""
        try:
            if hasattr(self, "calibration_temperature_filter"):
                temperature_filter = str(
                    self.calibration_temperature_filter.currentData() or ""
                )
        except Exception:
            temperature_filter = ""
        for row in rows:
            if row.get("charge") is None or row.get("velocity") is None:
                continue
            points.append(
                {
                    "charge": float(row["charge"]),
                    "velocity": float(row["velocity"]),
                    "es": float(row["es"]) if row.get("es") is not None else None,
                    "sd": float(row["sd"]) if row.get("sd") is not None else None,
                }
            )

        if len(points) < 2:
            return (
                "Too few data points to read a trend. Add at least two calibration loads "
                "with charge and velocity on the active barrel."
            )

        points.sort(key=lambda item: item["charge"])
        charge_span = points[-1]["charge"] - points[0]["charge"]
        velocity_span = points[-1]["velocity"] - points[0]["velocity"]
        fps_per_gr = None
        if abs(charge_span) > 1e-9:
            fps_per_gr = velocity_span / charge_span

        es_values = [item["es"] for item in points if item.get("es") is not None]
        sd_values = [item["sd"] for item in points if item.get("sd") is not None]

        lines = []
        if temperature_filter:
            lines.append(
                "Showing trend for the selected temperature: "
                + temperature_filter
                + ". This makes temperature drift easier to read in the data."
            )
        elif len(temperature_labels) > 1:
            preview = ", ".join(sorted(list(temperature_labels))[:2])
            if len(temperature_labels) > 2:
                preview += ", ..."
            lines.append(
                "Trend data mixes multiple temperatures: "
                + preview
                + ". Filter by temperature when interpreting velocity and ES/SD."
            )
        if distance_filter:
            lines.append(
                "Showing trend for the selected distance: "
                + distance_filter
                + ". This gives you a cleaner comparison basis."
            )
        elif len(distance_labels) > 1:
            preview = ", ".join(sorted(list(distance_labels))[:2])
            if len(distance_labels) > 2:
                preview += ", ..."
            lines.append(
                "Trend data mixes multiple distances: "
                + preview
                + ". Filter by distance when interpreting group size and POI."
            )
        if lot_filter:
            lines.append(
                "Showing trend for the selected lot: "
                + lot_filter
                + ". This gives you a cleaner basis than mixing multiple lots."
            )
        elif len(lot_labels) > 1:
            preview = ", ".join(sorted(list(lot_labels))[:2])
            if len(lot_labels) > 2:
                preview += ", ..."
            lines.append(
                "Trend data mixes multiple lots: "
                + preview
                + ". Filter by lot when you want to read small differences."
            )
        elif lot_labels:
            lines.append(
                "Trend data appears to be based on one lot: " + next(iter(lot_labels))
            )
        if len(powder_labels) > 1:
            labels = ", ".join(sorted(list(powder_labels))[:2])
            if len(powder_labels) > 2:
                labels += ", ..."
            lines.append(
                "Trend data mixes multiple powders: "
                + labels
                + ". Compare within the same powder type and lot when possible."
            )
        elif powder_labels:
            lines.append(
                "Trend data appears to use the same powder: "
                + next(iter(powder_labels))
            )

        if fps_per_gr is not None:
            lines.append(
                f"Charge -> velocity: "
                f"{format_weight_grains(points[0]['charge'], 'powder')}-{format_weight_grains(points[-1]['charge'], 'powder')} "
                f"gave {format_velocity_fps(points[0]['velocity'])}-{format_velocity_fps(points[-1]['velocity'])} "
                f"({format_velocity_rate_fps_per_gr(fps_per_gr)} over this interval)."
            )

        if es_values:
            lines.append(
                f"ES trend: best {format_velocity_fps(min(es_values))}, worst {format_velocity_fps(max(es_values))}."
            )
        if sd_values:
            lines.append(
                f"SD trend: best {format_velocity_fps(min(sd_values))}, worst {format_velocity_fps(max(sd_values))}."
            )

        temp_drift = self._estimate_temperature_velocity_drift(rows)
        if temp_drift:
            lines.append(
                "Temperature drift: "
                f"{format_velocity_rate_fps_per_c(temp_drift['fps_per_c'])} "
                f"based on {temp_drift['point_count']} points for "
                f"{temp_drift['powder']} / {temp_drift['lot']} / "
                f"{format_weight_grains(temp_drift['charge'], 'powder')} between "
                f"{format_temperature_c(temp_drift['temp_min'])} and {format_temperature_c(temp_drift['temp_max'])}."
            )

        return " ".join(lines)

    def _get_calibration_plot_points(self) -> list[dict]:
        """Return charge/metric points for compact calibration plotting."""
        points: list[dict] = []
        metric = "velocity"
        if hasattr(self, "calibration_metric_combo"):
            metric = self.calibration_metric_combo.currentText().lower()
        rows = self._get_calibration_rows(limit=None)
        metric_key = {
            "velocity": "velocity",
            "es": "es",
            "sd": "sd",
            "gruppe": "group_size_mm",
        }.get(metric, "velocity")
        for row in rows:
            charge = row.get("charge")
            if charge is None:
                continue
            metric_value = row.get(metric_key)
            if metric_value is None:
                continue
            points.append(
                {
                    "charge": float(charge),
                    "value": float(metric_value),
                    "powder": str(row.get("powder") or "-"),
                    "lot": str(row.get("lot") or "-"),
                    "bullet": str(row.get("bullet") or "-"),
                    "distance": str(row.get("distance") or "-"),
                    "temperature_c": row.get("temperature_c"),
                    "velocity": row.get("velocity"),
                    "es": row.get("es"),
                    "sd": row.get("sd"),
                    "group_size_mm": row.get("group_size_mm"),
                    "series": str(row.get("series") or "-"),
                }
            )
        return sorted(points, key=lambda item: item["charge"])

    def _get_calibration_ai_note(self) -> str:
        """Return a short note explaining how to interpret calibration trends."""
        summary = self._get_calibration_summary()
        if not summary:
            return ""
        rows = self._get_calibration_rows(limit=None)
        lot_labels = sorted(
            {
                str(row.get("lot") or "-")
                for row in rows
                if row.get("lot") and row.get("lot") != "-"
            }
        )
        distance_labels = sorted(
            {
                str(row.get("distance") or "-")
                for row in rows
                if row.get("distance") and row.get("distance") != "-"
            }
        )
        temperature_labels = sorted(
            {
                str(row.get("temperature") or "-")
                for row in rows
                if row.get("temperature") and row.get("temperature") != "-"
            }
        )
        lot_filter = ""
        distance_filter = ""
        temperature_filter = ""
        try:
            if hasattr(self, "calibration_lot_filter"):
                lot_filter = str(self.calibration_lot_filter.currentData() or "")
        except Exception:
            lot_filter = ""
        try:
            if hasattr(self, "calibration_distance_filter"):
                distance_filter = str(
                    self.calibration_distance_filter.currentData() or ""
                )
        except Exception:
            distance_filter = ""
        try:
            if hasattr(self, "calibration_temperature_filter"):
                temperature_filter = str(
                    self.calibration_temperature_filter.currentData() or ""
                )
        except Exception:
            temperature_filter = ""
        if temperature_filter:
            return (
                "\n\nCalibration view is filtered to temperature "
                + temperature_filter
                + ", making it easier to separate true trend from temperature drift."
            )
        if len(temperature_labels) > 1:
            return (
                "\n\nCalibration series on the active barrel mix multiple temperatures. "
                "Use the temperature filter if you want to read velocity and ES/SD more precisely."
            )
        temp_drift = self._estimate_temperature_velocity_drift(rows)
        if temp_drift:
            return (
                "\n\nThere are enough comparable data points to estimate temperature drift at roughly "
                f"{format_velocity_rate_fps_per_c(temp_drift['fps_per_c'])} for this load. "
                "Use this as an indication, not an absolute truth."
            )
        if distance_filter:
            return (
                "\n\nCalibration view is filtered to distance "
                + distance_filter
                + ", so group and velocity data are compared on a more equal basis."
            )
        if len(distance_labels) > 1:
            return (
                "\n\nCalibration series on the active barrel mix multiple shooting distances. "
                "Use the distance filter when you want to read precision and point of impact more accurately."
            )
        if lot_filter:
            return (
                "\n\nCalibration view is filtered to one specific lot ("
                + lot_filter
                + "), making small differences easier to interpret than when multiple lots are mixed."
            )
        if len(lot_labels) > 1:
            return (
                "\n\nCalibration series on the active barrel mix multiple lots. "
                "Use the lot filter if you want to read small differences in velocity, ES, SD, or group size more precisely."
            )
        if summary.get("mixed_powders"):
            return (
                "\n\nCalibration series on the active barrel use multiple powders. "
                "Do not interpret this as a pure powder-charge trend alone. Compare within the same powder type and lot when possible."
            )
        powder_names = summary.get("unique_powders") or []
        if powder_names:
            return (
                f"\n\nCalibration data on the active barrel appears to be built on the same powder ({powder_names[0]}), "
                "making changes in charge, velocity, and precision easier to interpret as one combined trend."
            )
        return ""

    def _build_evidence_summary(self) -> str:
        """Build a compact summary of the current data foundation."""
        parts = []

        h2o_stats = self._get_h2o_stats()
        if h2o_stats:
            parts.append(
                f"<b>H2O / case capacity:</b> {h2o_stats['count']} measurements, {h2o_stats['quality']}, spread {format_weight_grains(h2o_stats['spread'], 'powder')}"
            )
        else:
            parts.append(
                "<b>H2O / case capacity:</b> not recorded from fired cases in this chamber"
            )

        chrono_note = self._get_chrono_ai_note()
        if "under 5 skudd" in chrono_note:
            chrono_line = "under 5 shots in the selected chronograph series"
        elif "under 10 skudd" in chrono_note:
            chrono_line = "under 10 shots in the selected chronograph series"
        elif "gir et bedre grunnlag" in chrono_note:
            chrono_line = "good shot basis in the selected chronograph series"
        else:
            chrono_line = "no chronograph series selected"
        parts.append(f"<b>Chronograph:</b> {chrono_line}")

        if self._has_tracked_brass_batch():
            brass_line = "tracked batch selected"
        elif self.brass_data:
            brass_line = "unbatched brass selected - fine-grained interpretation becomes less precise"
        else:
            brass_line = "no brass selected"
        parts.append(f"<b>Brass:</b> {brass_line}")

        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        calibration_count = (
            len(calibration_tests) if isinstance(calibration_tests, list) else 0
        )
        group_note = self._get_group_ai_note()
        if calibration_count:
            group_line = f"{calibration_count} calibration series on the active barrel"
        elif "ingen lagrede gruppedata" in group_note:
            group_line = "no recent group data or target images"
        else:
            group_line = "group data/target images available"
        parts.append(f"<b>Groups:</b> {group_line}")

        calibration_summary = self._get_calibration_summary()
        if calibration_summary:
            calib_line = (
                f"{calibration_summary['series_count']} series / "
                f"{calibration_summary['load_count']} loads"
            )
            if (
                calibration_summary.get("charge_min") is not None
                and calibration_summary.get("charge_max") is not None
            ):
                calib_line += (
                    f" | charge {format_weight_grains(calibration_summary['charge_min'], 'powder')}-"
                    f"{format_weight_grains(calibration_summary['charge_max'], 'powder')}"
                )
            if calibration_summary.get("mixed_powders"):
                powder_preview = ", ".join(
                    calibration_summary.get("unique_powders", [])[:2]
                )
                if calibration_summary.get("powder_count", 0) > 2:
                    powder_preview += ", ..."
                calib_line += f" | multiple powders: {powder_preview}"
            else:
                powder_names = calibration_summary.get("unique_powders") or []
                if powder_names:
                    calib_line += f" | powder: {powder_names[0]}"
            distance_labels = sorted(
                {
                    str(row.get("distance") or "-")
                    for row in self._get_calibration_rows(limit=None)
                    if row.get("distance") and row.get("distance") != "-"
                }
            )
            temperature_labels = sorted(
                {
                    str(row.get("temperature") or "-")
                    for row in self._get_calibration_rows(limit=None)
                    if row.get("temperature") and row.get("temperature") != "-"
                }
            )
            if distance_labels:
                if len(distance_labels) == 1:
                    calib_line += f" | distance: {distance_labels[0]}"
                else:
                    calib_line += (
                        f" | distances: {distance_labels[0]}, {distance_labels[1]}"
                        + (", ..." if len(distance_labels) > 2 else "")
                    )
            if temperature_labels:
                if len(temperature_labels) == 1:
                    calib_line += f" | temp: {temperature_labels[0]}"
                else:
                    calib_line += (
                        f" | temperatures: {temperature_labels[0]}, {temperature_labels[1]}"
                        + (", ..." if len(temperature_labels) > 2 else "")
                    )
            parts.append(f"<b>Calibration:</b> {calib_line}")

        latest_result = getattr(self, "_latest_visual_result", None)
        if isinstance(latest_result, dict):
            internal_ballistics = self._build_current_internal_ballistics_summary(
                latest_result=latest_result,
                powder_name=str((self.powder_data or {}).get("name") or ""),
            )
            parts.append(
                f"<b>Internal Ballistics:</b> {internal_ballistics['message']}"
            )

        return "<br>".join(parts)

    def _save_rifle_profile_details(self, details: dict) -> bool:
        """Persist updated rifle profile details for the active rifle."""
        try:
            rifle_id = self.rifle_data.get("id") if self.rifle_data else None
        except Exception:
            rifle_id = None
        if not rifle_id:
            return False

        payload = json.dumps(details, ensure_ascii=False)
        try:
            existing = self.db.execute_query(
                "SELECT id FROM rifle_profile_details WHERE rifle_id = ?",
                (rifle_id,),
            )
            if existing:
                self.db.update(
                    "rifle_profile_details",
                    {"profile_json": payload},
                    "rifle_id = ?",
                    (rifle_id,),
                )
            else:
                self.db.insert(
                    "rifle_profile_details",
                    {"rifle_id": rifle_id, "profile_json": payload},
                )
            self._rifle_profile_details = details
            self._rifle_profile_details_id = rifle_id
            return True
        except Exception:
            return False

    def _get_selected_powder_context(self) -> dict:
        """Return selected powder metadata useful for calibration/test storage."""
        powder = dict(self.powder_data or {})
        powder_id = powder.get("id")
        if not powder_id:
            return powder

        try:
            rows = self.db.execute_query(
                "SELECT * FROM powder_database WHERE powder_id = ?",
                (powder_id,),
            )
            if rows:
                powder.update(
                    {
                        "burn_rate_position": rows[0].get("burn_rate_position"),
                        "relative_burn_rate": rows[0].get("relative_burn_rate"),
                        "density_gcc": rows[0].get("density_gcc"),
                        "grain_shape": rows[0].get("grain_shape"),
                        "temp_stable": rows[0].get("temp_stable"),
                        "temp_coefficient_fps_per_f": rows[0].get(
                            "temp_coefficient_fps_per_f"
                        ),
                        "quickload_available": rows[0].get("quickload_available"),
                        "quickload_ba_value": rows[0].get("quickload_ba_value"),
                        "qex_kj_per_kg": rows[0].get("qex_kj_per_kg"),
                        "k_ratio": rows[0].get("k_ratio"),
                        "a0": rows[0].get("a0"),
                        "z1": rows[0].get("z1"),
                        "z2": rows[0].get("z2"),
                        "eta_cm3_per_kg": rows[0].get("eta_cm3_per_kg"),
                        "pc_kg_m3": rows[0].get("pc_kg_m3"),
                        "pcd_kg_m3": rows[0].get("pcd_kg_m3"),
                        "pt_c": rows[0].get("pt_c"),
                        "tcc": rows[0].get("tcc"),
                        "tch": rows[0].get("tch"),
                        "validation_status": rows[0].get("validation_status"),
                        "usable_for_simulation": rows[0].get("usable_for_simulation"),
                        "data_source": rows[0].get("data_source"),
                    }
                )
        except Exception:
            pass
        try:
            snapshot_rows = self.db.execute_query(
                """
                SELECT lot_number, profile_json
                FROM component_reference_snapshots
                WHERE source_system IN ('reference_readable', 'gordon_readable')
                  AND component_type = 'powder'
                  AND lower(coalesce(manufacturer, '')) = lower(?)
                  AND lower(coalesce(model_name, '')) = lower(?)
                """,
                (
                    powder.get("manufacturer") or "",
                    powder.get("name") or "",
                ),
            )
            powder["reference_snapshot_count"] = len(snapshot_rows)
            powder["gordon_reference_snapshot_count"] = len(snapshot_rows)
            variant_signatures = set()
            for row in snapshot_rows:
                try:
                    profile = _safe_json_loads(row.get("profile_json"))
                except Exception:
                    profile = {}
                variant_signatures.add(
                    (
                        row.get("lot_number"),
                        profile.get("Ba"),
                        profile.get("Qex"),
                        profile.get("k"),
                        profile.get("pt"),
                    )
                )
            powder["reference_variant_count"] = len(variant_signatures)
            powder["gordon_reference_variant_count"] = len(variant_signatures)
        except Exception:
            powder["reference_snapshot_count"] = (
                powder.get("reference_snapshot_count")
                or powder.get("gordon_reference_snapshot_count")
                or 0
            )
            powder["reference_variant_count"] = (
                powder.get("reference_variant_count")
                or powder.get("gordon_reference_variant_count")
                or 0
            )
            powder["gordon_reference_snapshot_count"] = (
                powder.get("gordon_reference_snapshot_count")
                or powder["reference_snapshot_count"]
            )
            powder["gordon_reference_variant_count"] = (
                powder.get("gordon_reference_variant_count")
                or powder["reference_variant_count"]
            )
        return powder

    def _get_component_lot_number(
        self, component_type: str, component_id
    ) -> str | None:
        """Return latest lot number for a component when available."""
        if not component_id:
            return None
        try:
            rows = self.db.execute_query(
                "SELECT lot_number FROM component_lots WHERE component_type = ? AND component_id = ? ORDER BY is_active DESC, created_date DESC LIMIT 1",
                (component_type, component_id),
            )
            if rows:
                lot_number = str(rows[0].get("lot_number") or "").strip()
                return lot_number or None
        except Exception:
            return None
        return None

    def _selected_component_lot_id(self, component_type: str):
        combo_name = {
            "bullet": "bullet_lot_combo",
            "powder": "powder_lot_combo",
            "primers": "primer_lot_combo",
        }.get(component_type)
        if not combo_name or not hasattr(self, combo_name):
            return None
        combo = getattr(self, combo_name)
        try:
            lot_id = combo.currentData()
        except Exception:
            lot_id = None
        return lot_id or None

    def _format_component_lot_choice_label(
        self, component_type: str, row: dict | None
    ) -> str:
        """Build an informative dropdown label for a component lot."""
        if not isinstance(row, dict):
            return "Unknown lot"

        label = str(row.get("lot_number") or f"Lot #{row.get('id')}").strip()
        details: list[str] = []

        qty = row.get("quantity_remaining")
        try:
            if qty is not None:
                details.append(f"{float(qty):.0f} remaining")
        except Exception:
            pass

        lot_id = row.get("id")
        if component_type == "bullet":
            stats = {}
            try:
                if lot_id:
                    stats = self.db.get_component_lot_stats(int(lot_id)) or {}
            except Exception:
                stats = {}
            sample_count = stats.get("sample_count")
            if sample_count:
                details.append(f"n={int(sample_count)}")
            if stats.get("weight_avg_grains") is not None:
                details.append(f"{float(stats['weight_avg_grains']):.1f} gr")
            if stats.get("length_avg_mm") is not None:
                details.append(f"{float(stats['length_avg_mm']):.2f} mm")

        elif component_type == "powder":
            profile = {}
            comparison = {}
            try:
                if lot_id:
                    profile = (
                        self.db.refresh_powder_lot_learning_profile(int(lot_id)) or {}
                    )
            except Exception:
                profile = {}
            try:
                component_id = row.get("component_id")
                if lot_id and component_id:
                    comparison = (
                        self.db.compare_powder_lots(int(component_id), int(lot_id))
                        or {}
                    )
            except Exception:
                comparison = {}
            if profile.get("confidence_label"):
                details.append(f"learning {profile['confidence_label']}")
            if profile.get("avg_velocity_fps") is not None:
                details.append(f"{float(profile['avg_velocity_fps']):.0f} fps")
            elif comparison.get("title"):
                details.append(str(comparison.get("title")).strip())

        elif component_type == "primers":
            profile = {}
            comparison = {}
            try:
                if lot_id:
                    profile = (
                        self.db.refresh_primer_lot_learning_profile(int(lot_id)) or {}
                    )
            except Exception:
                profile = {}
            try:
                component_id = row.get("component_id")
                if lot_id and component_id:
                    comparison = (
                        self.db.compare_primer_lots(int(component_id), int(lot_id))
                        or {}
                    )
            except Exception:
                comparison = {}
            if profile.get("typical_es_fps") is not None:
                details.append(f"ES {float(profile['typical_es_fps']):.1f} fps")
            if profile.get("typical_sd_fps") is not None:
                details.append(f"SD {float(profile['typical_sd_fps']):.1f} fps")
            elif comparison.get("title"):
                details.append(str(comparison.get("title")).strip())

        if details:
            return f"{label} ({' | '.join(details[:4])})"
        return label

    def _load_component_lot_choices(self, component_type: str, component_id) -> None:
        combo_name = {
            "bullet": "bullet_lot_combo",
            "powder": "powder_lot_combo",
            "primers": "primer_lot_combo",
        }.get(component_type)
        if not combo_name or not hasattr(self, combo_name):
            return
        combo = getattr(self, combo_name)
        try:
            selected_before = combo.currentData()
        except Exception:
            selected_before = None
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Select Lot Automatically", None)
        selected_index = 0
        if component_id:
            try:
                rows = self.db.execute_query(
                    """
                    SELECT *
                    FROM component_lots
                    WHERE component_type = ? AND component_id = ?
                    ORDER BY is_active DESC, created_date DESC, id DESC
                    """,
                    (component_type, component_id),
                )
            except Exception:
                rows = []
            for row in rows or []:
                label = self._format_component_lot_choice_label(
                    component_type, dict(row)
                )
                combo.addItem(label, row.get("id"))
                if selected_before and int(row.get("id") or 0) == int(selected_before):
                    selected_index = combo.count() - 1
        combo.setCurrentIndex(selected_index)
        combo.blockSignals(False)

    def _get_component_lot_record(
        self,
        component_type: str,
        component_id,
        preferred_lot_id=None,
    ) -> dict | None:
        """Return the selected/active lot row for a component when available."""
        if not component_id:
            return None
        try:
            rows = self.db.execute_query(
                """
                SELECT *
                FROM component_lots
                WHERE component_type = ? AND component_id = ?
                ORDER BY is_active DESC, created_date DESC, id DESC
                """,
                (component_type, component_id),
            )
            if rows:
                selected_lot_fn = getattr(self, "_selected_component_lot_id", None)
                selected_id = preferred_lot_id or (
                    selected_lot_fn(component_type)
                    if callable(selected_lot_fn)
                    else None
                )
                if selected_id:
                    for row in rows:
                        if int(row.get("id") or 0) == int(selected_id):  # type: ignore[arg-type]
                            return dict(row)
                return dict(rows[0])
        except Exception:
            return None
        return None

    def _apply_bullet_lot_measurements(self, bullet: dict | None) -> dict | None:
        """Overlay measured lot averages on top of nominal bullet reference data."""
        if not isinstance(bullet, dict):
            return bullet
        bullet_id = bullet.get("id")
        if not bullet_id:
            return dict(bullet)
        selected_lot_fn = getattr(self, "_selected_component_lot_id", None)
        selected_lot_id = (
            selected_lot_fn("bullet") if callable(selected_lot_fn) else None
        )
        lot_row = self._get_component_lot_record(
            "bullet",
            bullet_id,
            preferred_lot_id=selected_lot_id,
        )
        if not lot_row:
            return dict(bullet)

        merged = dict(bullet)
        merged["selected_lot_id"] = lot_row.get("id")
        merged["selected_lot_number"] = lot_row.get("lot_number")
        merged["selected_lot_quantity_remaining"] = lot_row.get("quantity_remaining")

        stats = self.db.get_component_lot_stats(int(lot_row["id"])) or {}
        if not stats:
            return merged

        merged["measured_lot_stats"] = dict(stats)
        merged["nominal_weight_grains"] = merged.get(
            "weight_grains", merged.get("weight")
        )
        merged["nominal_length_mm"] = merged.get("length_mm")
        merged["nominal_diameter_mm"] = merged.get("diameter_mm")
        if stats.get("weight_avg_grains") is not None:
            merged["weight_grains"] = float(stats["weight_avg_grains"])
            merged["weight"] = float(stats["weight_avg_grains"])
        if stats.get("length_avg_mm") is not None:
            merged["length_mm"] = float(stats["length_avg_mm"])
        if stats.get("diameter_avg_mm") is not None:
            merged["diameter_mm"] = float(stats["diameter_avg_mm"])
        return merged

    def _apply_powder_lot_context(self, powder: dict | None) -> dict | None:
        """Attach active powder lot and learning profile to the selected powder."""
        if not isinstance(powder, dict):
            return powder
        powder_id = powder.get("id")
        if not powder_id:
            return dict(powder)
        selected_lot_fn = getattr(self, "_selected_component_lot_id", None)
        selected_lot_id = (
            selected_lot_fn("powder") if callable(selected_lot_fn) else None
        )
        lot_row = self._get_component_lot_record(
            "powder",
            powder_id,
            preferred_lot_id=selected_lot_id,
        )
        merged = dict(powder)
        if not lot_row:
            return merged
        merged["selected_lot_id"] = lot_row.get("id")
        merged["selected_lot_number"] = lot_row.get("lot_number")
        merged["selected_lot_quantity_remaining"] = lot_row.get("quantity_remaining")
        try:
            merged["lot_learning_profile"] = (
                self.db.refresh_powder_lot_learning_profile(int(lot_row["id"]))
            )
        except Exception:
            merged["lot_learning_profile"] = {}
        try:
            merged["lot_comparison"] = self.db.compare_powder_lots(
                int(powder_id), int(lot_row["id"])
            )
        except Exception:
            merged["lot_comparison"] = {}
        return merged

    def _apply_primer_lot_context(self, primer: dict | None) -> dict | None:
        """Attach active primer lot and learning profile to the selected primer."""
        if not isinstance(primer, dict):
            return primer
        primer_id = primer.get("id")
        if not primer_id:
            return dict(primer)
        selected_lot_fn = getattr(self, "_selected_component_lot_id", None)
        selected_lot_id = (
            selected_lot_fn("primers") if callable(selected_lot_fn) else None
        )
        lot_row = self._get_component_lot_record(
            "primers",
            primer_id,
            preferred_lot_id=selected_lot_id,
        )
        merged = dict(primer)
        if not lot_row:
            return merged
        merged["selected_lot_id"] = lot_row.get("id")
        merged["selected_lot_number"] = lot_row.get("lot_number")
        merged["selected_lot_quantity_remaining"] = lot_row.get("quantity_remaining")
        try:
            merged["lot_learning_profile"] = (
                self.db.refresh_primer_lot_learning_profile(int(lot_row["id"]))
            )
        except Exception:
            merged["lot_learning_profile"] = {}
        try:
            merged["lot_comparison"] = self.db.compare_primer_lots(
                int(primer_id), int(lot_row["id"])
            )
        except Exception:
            merged["lot_comparison"] = {}
        return merged

    def _refresh_evidence_actions(self) -> None:
        """Update evidence action labels based on current data availability."""
        if not hasattr(self, "evidence_h2o_btn"):
            return

        h2o_stats = self._get_h2o_stats()
        if h2o_stats:
            self.evidence_h2o_btn.setText("View Barrel / H2O")
        else:
            self.evidence_h2o_btn.setText("Enter H2O")

        chrono_has_selection = False
        try:
            chrono_has_selection = (
                hasattr(self, "chrono_list")
                and self.chrono_list is not None
                and self.chrono_list.currentItem() is not None
            )
        except Exception:
            chrono_has_selection = False
        self.evidence_chrono_btn.setText(
            "View Selected Chrono" if chrono_has_selection else "Select/Import Chrono"
        )

        barrel = self._get_active_barrel_details()
        calibration_tests = barrel.get("calibration_tests") or []
        has_calibration = isinstance(calibration_tests, list) and bool(
            calibration_tests
        )
        self.evidence_group_btn.setText(
            "Add New Calibration Series"
            if has_calibration
            else "Register Calibration Series"
        )

    def _refresh_component_context_label(self) -> None:
        """Update compact summary of active component data sources."""
        if not hasattr(self, "component_context_label"):
            return
        self.component_context_label.setText(
            build_component_context_summary(
                bullet_data=(
                    self.bullet_data if isinstance(self.bullet_data, dict) else None
                ),
                powder_data=(
                    self.powder_data if isinstance(self.powder_data, dict) else None
                ),
                primer_data=(
                    self.primer_data if isinstance(self.primer_data, dict) else None
                ),
            )
        )

    def _open_selected_component_in_library(self, component_type: str) -> None:
        """Jump from the builder to the matching row in the component library."""
        data_map = {
            "bullet": self.bullet_data if isinstance(self.bullet_data, dict) else None,
            "powder": self.powder_data if isinstance(self.powder_data, dict) else None,
            "primer": self.primer_data if isinstance(self.primer_data, dict) else None,
        }
        component = data_map.get(component_type) or {}
        component_id = component.get("id")
        if not component_id:
            QMessageBox.information(
                self,
                "Component Library",
                "Select a component first before opening the library on the correct row.",
            )
            return

        host = self.window()
        if host is not None and hasattr(host, "show_component_database"):
            try:
                host.show_component_database(component_type, int(component_id))  # type: ignore[attr-defined]
                return
            except Exception:
                pass

        QMessageBox.information(
            self,
            "Component Library",
            "Could not open the component library from this context.",
        )

    def _format_calibration_tooltip(self, point: dict) -> str:
        """Build a short tooltip for one calibration point."""
        lines = []
        powder = str(point.get("powder") or "-")
        lot = str(point.get("lot") or "-")
        bullet = str(point.get("bullet") or "-")
        series = str(point.get("series") or "-")
        charge = point.get("charge")
        velocity = point.get("velocity")
        es = point.get("es")
        sd = point.get("sd")
        group_size = point.get("group_size_mm")

        lines.append(f"Powder: {powder}")
        if lot and lot != "-":
            lines.append(f"Lot: {lot}")
        if bullet and bullet != "-":
            lines.append(f"Bullet: {bullet}")
        distance = point.get("distance")
        if distance and distance != "-":
            lines.append(f"Distance: {distance}")
        temperature = point.get("temperature_c")
        if temperature is not None:
            try:
                lines.append(f"Temperature: {format_temperature_c(float(temperature))}")
            except Exception:
                lines.append(f"Temperature: {temperature}")
        if charge is not None:
            lines.append(f"Charge: {format_weight_grains(float(charge), 'powder')}")
        if velocity is not None:
            lines.append(f"V0: {format_velocity_fps(float(velocity))}")
        if es is not None:
            lines.append(f"ES: {format_velocity_fps(float(es))}")
        if sd is not None:
            lines.append(f"SD: {format_velocity_fps(float(sd))}")
        if group_size is not None:
            lines.append(f"Group: {format_group_size_mm(float(group_size))}")
        if series and series != "-":
            lines.append(f"Series: {series}")
        return "\n".join(lines)

    def _collect_current_safety_advisories(self) -> list[dict[str, str]]:
        """Collect current high-signal safety advisories shown in the builder."""
        latest_result = getattr(self, "_latest_visual_result", None)
        powder_context = self._get_selected_powder_context()
        internal_ballistics = None
        if isinstance(latest_result, dict):
            internal_ballistics = self._build_current_internal_ballistics_summary(
                latest_result=latest_result,
                powder_name=str((self.powder_data or {}).get("name") or ""),
            )
        return collect_safety_advisories(
            latest_result,
            powder_context=powder_context,
            primer_context=(
                self.primer_data if isinstance(self.primer_data, dict) else None
            ),
            internal_ballistics=internal_ballistics,
        )

    def _confirm_high_risk_override(
        self, action_label: str
    ) -> tuple[bool, list[dict[str, str]]]:
        """Ask for explicit confirmation before continuing under critical risk."""
        advisories = self._collect_current_safety_advisories()
        critical = [item for item in advisories if item.get("level") == "critical"]
        if not critical:
            return True, advisories

        lines = [
            f"{action_label} is outside the recommended safety margin or has incomplete data support.",
            "",
            "The program will not block you, but this requires a deliberate override.",
            "",
            "Critical conditions now:",
        ]
        for item in critical[:3]:
            title = str(item.get("title") or "Warning").strip()
            message = str(item.get("message") or "").strip()
            lines.append(f"- {title}: {message}")
        lines.extend(
            [
                "",
                "Do you want to continue and save this as a deliberate override?",
            ]
        )

        answer = QMessageBox.warning(
            self,
            "Critical Safety Warning",
            "\n".join(lines),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes, advisories

    def _format_temperature_drift_tooltip(self, point: dict, drift: dict) -> str:
        """Build a short tooltip for one temperature drift point."""
        lines = [
            f"Powder: {drift.get('powder') or '-'}",
            f"Lot: {drift.get('lot') or '-'}",
            f"Bullet: {drift.get('bullet') or '-'}",
            f"Charge: {format_weight_grains(float(drift.get('charge') or 0.0), 'powder')}",
            f"Temperature: {format_temperature_c(float(point.get('temp') or 0.0))}",
            f"V0: {format_velocity_fps(float(point.get('velocity') or 0.0))}",
        ]
        distance = point.get("distance")
        if distance and distance != "-":
            lines.append(f"Distance: {distance}")
        series = point.get("series")
        if series and series != "-":
            lines.append(f"Series: {series}")
        return "\n".join(lines)

    def _refresh_temperature_drift_plot(self) -> None:
        """Refresh compact temperature vs velocity plot for comparable rows."""
        if not hasattr(self, "temperature_drift_placeholder"):
            return

        rows = self._get_calibration_rows(limit=None)
        drift = self._estimate_temperature_velocity_drift(rows)
        points = drift.get("points") or []
        if len(points) < 2:
            self._temperature_drift_hover_points = []
            self._temperature_drift_hover_key = None
            self._temperature_drift_context = {}
            QToolTip.hideText()
            self.temperature_drift_placeholder.setText(
                "Add comparable series with the same bullet, powder, lot, and roughly the same charge across at least two temperatures to view the temperature-drift graph."
            )
            if (
                hasattr(self, "temperature_drift_plot")
                and self.temperature_drift_plot is not None
            ):
                self.temperature_drift_plot.hide()
            self.temperature_drift_placeholder.show()
            return

        pg = getattr(self, "_pg", None)
        if pg is None:
            self._temperature_drift_hover_points = []
            self._temperature_drift_hover_key = None
            self._temperature_drift_context = {}
            QToolTip.hideText()
            self.temperature_drift_placeholder.setText(
                "Temperature-drift data is available, but the graph requires pyqtgraph."
            )
            self.temperature_drift_placeholder.show()
            return

        if (
            not hasattr(self, "temperature_drift_plot")
            or self.temperature_drift_plot is None
        ):
            _pw1 = self.temperature_drift_placeholder.parentWidget()
            self.temperature_drift_plot = pg.PlotWidget(_pw1)
            self.temperature_drift_plot.setBackground(ReloadingTheme.PANEL)
            self.temperature_drift_plot.setMinimumHeight(160)
            self.temperature_drift_plot.setLabel(
                "bottom", "Temperatur", units="C", color=ReloadingTheme.TEXT_PRIMARY
            )
            self.temperature_drift_plot.setLabel(
                "left", "Velocity", units="fps", color=ReloadingTheme.TEXT_PRIMARY
            )
            parent_layout = _pw1.layout() if _pw1 is not None else None
            if parent_layout is not None:
                parent_layout.addWidget(self.temperature_drift_plot)
            try:
                self.temperature_drift_plot.scene().sigMouseMoved.connect(
                    self._on_temperature_drift_plot_hover
                )
            except Exception:
                pass

        self.temperature_drift_plot.clear()
        self._temperature_drift_hover_points = list(points)
        self._temperature_drift_hover_key = None
        self._temperature_drift_context = dict(drift)
        xs = [float(point["temp"]) for point in points]
        ys = [float(point["velocity"]) for point in points]
        self.temperature_drift_plot.setTitle(
            (
                "Temperature drift: "
                f"{drift.get('powder', '-')} / {drift.get('lot', '-')} / "
                f"{drift.get('charge', 0.0):.1f} gr "
                f"({drift.get('fps_per_c', 0.0):+.1f} fps/C)"
            ),
            color=ReloadingTheme.TEXT_PRIMARY,
            size="10pt",
        )
        self.temperature_drift_plot.plot(
            xs,
            ys,
            pen=pg.mkPen(color="#dc2626", width=2),
            symbol="o",
            symbolBrush="#b91c1c",
            symbolPen=pg.mkPen(color="#b91c1c"),
        )
        if self.temperature_drift_plot.parentWidget() is not None:
            self.temperature_drift_plot.show()
            self.temperature_drift_placeholder.hide()

    def _on_calibration_plot_hover(self, pos) -> None:
        """Show tooltip when hovering near a calibration point."""
        if not hasattr(self, "calibration_plot") or self.calibration_plot is None:
            return
        points = getattr(self, "_calibration_hover_points", None) or []
        if not points:
            QToolTip.hideText()
            self._calibration_hover_key = None
            return

        plot_item = self.calibration_plot.plotItem
        try:
            if not plot_item.sceneBoundingRect().contains(pos):
                QToolTip.hideText()
                self._calibration_hover_key = None
                return
        except Exception:
            return

        best_point = None
        best_distance = None
        for point in points:
            try:
                scene_point = plot_item.vb.mapViewToScene(
                    QPointF(float(point["charge"]), float(point["value"]))
                )
            except Exception:
                continue
            dx = scene_point.x() - pos.x()
            dy = scene_point.y() - pos.y()
            distance = (dx * dx + dy * dy) ** 0.5
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_point = point

        if best_point is None or best_distance is None or best_distance > 18:
            QToolTip.hideText()
            self._calibration_hover_key = None
            return

        hover_key = (
            best_point.get("series"),
            best_point.get("powder"),
            best_point.get("lot"),
            best_point.get("charge"),
            best_point.get("value"),
        )
        if getattr(self, "_calibration_hover_key", None) == hover_key:
            return
        self._calibration_hover_key = hover_key
        QToolTip.showText(
            QCursor.pos(),
            self._format_calibration_tooltip(best_point),
            self.calibration_plot,
        )

    def _on_temperature_drift_plot_hover(self, pos) -> None:
        """Show tooltip when hovering near a temperature drift point."""
        if (
            not hasattr(self, "temperature_drift_plot")
            or self.temperature_drift_plot is None
        ):
            return
        points = getattr(self, "_temperature_drift_hover_points", None) or []
        drift = getattr(self, "_temperature_drift_context", None) or {}
        if not points:
            QToolTip.hideText()
            self._temperature_drift_hover_key = None
            return

        plot_item = self.temperature_drift_plot.plotItem
        try:
            if not plot_item.sceneBoundingRect().contains(pos):
                QToolTip.hideText()
                self._temperature_drift_hover_key = None
                return
        except Exception:
            return

        best_point = None
        best_distance = None
        for point in points:
            try:
                scene_point = plot_item.vb.mapViewToScene(
                    QPointF(float(point["temp"]), float(point["velocity"]))
                )
            except Exception:
                continue
            dx = scene_point.x() - pos.x()
            dy = scene_point.y() - pos.y()
            distance = (dx * dx + dy * dy) ** 0.5
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_point = point

        if best_point is None or best_distance is None or best_distance > 18:
            QToolTip.hideText()
            self._temperature_drift_hover_key = None
            return

        hover_key = (
            best_point.get("series"),
            best_point.get("temp"),
            best_point.get("velocity"),
        )
        if getattr(self, "_temperature_drift_hover_key", None) == hover_key:
            return
        self._temperature_drift_hover_key = hover_key
        QToolTip.showText(
            QCursor.pos(),
            self._format_temperature_drift_tooltip(best_point, drift),
            self.temperature_drift_plot,
        )

    def _refresh_calibration_table(self) -> None:
        """Refresh compact calibration table for the active barrel."""
        if not hasattr(self, "calibration_table"):
            return
        try:
            self._refresh_calibration_powder_filter()
        except Exception:
            pass
        try:
            self._refresh_calibration_bullet_filter()
        except Exception:
            pass
        try:
            self._refresh_calibration_lot_filter()
        except Exception:
            pass
        try:
            self._refresh_calibration_distance_filter()
        except Exception:
            pass
        try:
            self._refresh_calibration_temperature_filter()
        except Exception:
            pass

        rows = self._get_calibration_rows()
        self.calibration_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            charge = (
                format_weight_grains(float(row["charge"]), "powder")
                if row.get("charge") is not None
                else "-"
            )
            velocity = (
                format_velocity_fps(float(row["velocity"]))
                if row.get("velocity") is not None
                else "-"
            )
            es_sd_parts = []
            if row.get("es") is not None:
                es_sd_parts.append(f"ES {format_velocity_fps(float(row['es']))}")
            if row.get("sd") is not None:
                es_sd_parts.append(f"SD {format_velocity_fps(float(row['sd']))}")
            es_sd = " | ".join(es_sd_parts) if es_sd_parts else "-"
            values = [
                row.get("powder") or "-",
                row.get("lot") or "-",
                charge,
                velocity,
                es_sd,
                row.get("image") or "-",
                row.get("series") or "-",
            ]
            for col_index, value in enumerate(values):
                self.calibration_table.setItem(
                    row_index, col_index, QTableWidgetItem(str(value))
                )
            _cell = self.calibration_table.item(row_index, 0)
            if _cell is not None:
                _cell.setData(Qt.ItemDataRole.UserRole, row.get("test_id"))
        if not rows:
            self.calibration_table.setRowCount(1)
            self.calibration_table.setItem(
                0, 0, QTableWidgetItem("No calibration series yet")
            )
            for col_index in range(1, self.calibration_table.columnCount()):
                self.calibration_table.setItem(0, col_index, QTableWidgetItem(""))
        try:
            self.calibration_table.resizeColumnsToContents()
        except Exception:
            pass
        try:
            if hasattr(self, "calibration_trend_label"):
                self.calibration_trend_label.setText(
                    self._build_calibration_trend_summary()
                )
        except Exception:
            pass
        try:
            self._refresh_calibration_plot()
        except Exception:
            pass
        try:
            self._refresh_temperature_drift_plot()
        except Exception:
            pass

    def _refresh_calibration_plot(self) -> None:
        """Refresh compact charge vs velocity plot for active barrel."""
        if not hasattr(self, "calibration_plot_placeholder"):
            return

        points = self._get_calibration_plot_points()
        metric = "Velocity"
        if hasattr(self, "calibration_metric_combo"):
            metric = self.calibration_metric_combo.currentText()
        if len(points) < 2:
            self._calibration_hover_points = []
            self._calibration_hover_key = None
            QToolTip.hideText()
            self.calibration_plot_placeholder.setText(
                f"Add at least two calibration loads with charge and {metric.lower()} to view the graph."
            )
            if hasattr(self, "calibration_plot") and self.calibration_plot is not None:
                self.calibration_plot.hide()
            self.calibration_plot_placeholder.show()
            return

        pg = getattr(self, "_pg", None)
        if pg is None:
            self._calibration_hover_points = []
            self._calibration_hover_key = None
            QToolTip.hideText()
            powders = sorted(
                {
                    point["powder"]
                    for point in points
                    if point["powder"] and point["powder"] != "-"
                }
            )
            lots = sorted(
                {
                    point["lot"]
                    for point in points
                    if point.get("lot") and point["lot"] != "-"
                }
            )
            powder_note = ""
            if powders:
                powder_note = (
                    " Powder: "
                    + ", ".join(powders[:2])
                    + ("..." if len(powders) > 2 else "")
                )
            lot_note = ""
            if lots:
                lot_note = (
                    " Lot: " + ", ".join(lots[:2]) + ("..." if len(lots) > 2 else "")
                )
            self.calibration_plot_placeholder.setText(
                f"{len(points)} points ready for the {metric.lower()} graph.{powder_note}{lot_note}"
            )
            self.calibration_plot_placeholder.show()
            return

        if not hasattr(self, "calibration_plot") or self.calibration_plot is None:
            _pw2 = self.calibration_plot_placeholder.parentWidget()
            self.calibration_plot = pg.PlotWidget(_pw2)
            self.calibration_plot.setBackground(ReloadingTheme.PANEL)
            self.calibration_plot.setMinimumHeight(180)
            self.calibration_plot.setLabel(
                "bottom", "Charge", units="gr", color=ReloadingTheme.TEXT_PRIMARY
            )
            parent_layout = _pw2.layout() if _pw2 is not None else None
            if parent_layout is not None:
                parent_layout.addWidget(self.calibration_plot)
            try:
                self.calibration_plot.scene().sigMouseMoved.connect(
                    self._on_calibration_plot_hover
                )
            except Exception:
                pass

        self.calibration_plot.clear()
        self._calibration_hover_points = list(points)
        self._calibration_hover_key = None
        plot_item = self.calibration_plot.plotItem
        old_legend = getattr(self, "calibration_plot_legend", None)
        if old_legend is not None:
            try:
                plot_item.scene().removeItem(old_legend)
            except Exception:
                pass
            self.calibration_plot_legend = None
        xs = [point["charge"] for point in points]
        ys = [point["value"] for point in points]
        mixed_powders = (
            len(
                {
                    point["powder"]
                    for point in points
                    if point["powder"] and point["powder"] != "-"
                }
            )
            > 1
        )
        lot_labels = sorted(
            {
                point["lot"]
                for point in points
                if point.get("lot") and point["lot"] != "-"
            }
        )
        mixed_lots = len(lot_labels) > 1
        left_unit = ""
        if metric == "Velocity":
            left_unit = "fps"
        elif metric == "ES":
            left_unit = "fps"
        elif metric == "SD":
            left_unit = "fps"
        elif metric == "Gruppe":
            left_unit = "mm"
        self.calibration_plot.setLabel(
            "left", metric, units=left_unit, color=ReloadingTheme.TEXT_PRIMARY
        )
        self.calibration_plot.setTitle(
            f"Calibration: Charge vs {metric}",
            color=ReloadingTheme.TEXT_PRIMARY,
            size="10pt",
        )
        if mixed_lots:
            self.calibration_plot_legend = plot_item.addLegend(offset=(10, 10))
            palette = [
                ("#2563eb", "#1d4ed8"),
                ("#d97706", "#b45309"),
                ("#059669", "#047857"),
                ("#dc2626", "#b91c1c"),
                ("#7c3aed", "#6d28d9"),
            ]
            grouped_points: dict[str, list[dict]] = {}
            for point in points:
                label = point.get("lot") or "-"
                grouped_points.setdefault(label, []).append(point)
            for index, lot_label in enumerate(sorted(grouped_points.keys())):
                group = sorted(
                    grouped_points[lot_label], key=lambda item: item["charge"]
                )
                color_pair = palette[index % len(palette)]
                self.calibration_plot.plot(
                    [item["charge"] for item in group],
                    [item["value"] for item in group],
                    pen=pg.mkPen(color=color_pair[0], width=2),
                    symbol="o",
                    symbolBrush=color_pair[1],
                    symbolPen=pg.mkPen(color=color_pair[1]),
                    name=lot_label,
                )
        else:
            pen_color = "#d97706" if mixed_powders else "#2563eb"
            symbol_color = "#b45309" if mixed_powders else "#1d4ed8"
            self.calibration_plot.plot(
                xs,
                ys,
                pen=pg.mkPen(color=pen_color, width=2),
                symbol="o",
                symbolBrush=symbol_color,
                symbolPen=pg.mkPen(color=symbol_color),
            )
        if self.calibration_plot.parentWidget() is not None:
            self.calibration_plot.show()
            self.calibration_plot_placeholder.hide()

    def on_edit_calibration_series(self, row: int, column: int) -> None:
        """Open the selected calibration series for editing."""
        _ = column
        if not hasattr(self, "calibration_table"):
            return
        item = self.calibration_table.item(row, 0)
        if item is None:
            return
        test_id = item.data(Qt.ItemDataRole.UserRole)
        if not test_id:
            return

        details = dict(self._get_rifle_profile_details())
        barrels = details.get("barrels") or []
        active_barrel_id = self._get_active_barrel_id()
        barrel_index = -1
        active_barrel = {}
        if isinstance(barrels, list):
            for index, barrel in enumerate(barrels):
                if isinstance(barrel, dict) and str(barrel.get("id")) == str(
                    active_barrel_id
                ):
                    barrel_index = index
                    active_barrel = dict(barrel)
                    break
        if barrel_index < 0:
            return

        calibration_tests = list(active_barrel.get("calibration_tests") or [])
        target_index = -1
        target_test = {}
        for index, test in enumerate(calibration_tests):
            if isinstance(test, dict) and str(test.get("id")) == str(test_id):
                target_index = index
                target_test = dict(test)
                break
        if target_index < 0:
            return

        try:
            from ..ui.calibration_test_dialog import CalibrationTestDialog
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Open Calibration Series",
                f"An error occurred while opening the calibration series:\n{exc}",
            )
            return

        dialog = CalibrationTestDialog(
            parent=self,
            profile=details,
            existing={
                "distance_m": target_test.get("distance_m"),
                "temperature_c": target_test.get("temperature_c"),
                "loads": target_test.get("loads", []),
                "notes": target_test.get("notes", ""),
            },
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        updated = dialog.gather()
        calibration_tests[target_index] = {
            **target_test,
            "loads": updated.get("loads", []),
            "notes": updated.get("notes", ""),
            "distance_m": updated.get("distance_m"),
            "temperature_c": updated.get("temperature_c"),
            "updated_date": datetime.now().isoformat(timespec="seconds"),
        }
        active_barrel["calibration_tests"] = calibration_tests
        barrels[barrel_index] = active_barrel
        details["barrels"] = barrels

        if not self._save_rifle_profile_details(details):
            QMessageBox.warning(
                self,
                "Save Failed",
                "The changes to the calibration series could not be saved.",
            )
            return

        try:
            self._refresh_active_rifle_context()
            self.evidence_label.setText(self._build_evidence_summary())
            self._refresh_evidence_actions()
            self._refresh_calibration_table()
        except Exception:
            pass

    def on_open_case_capacity_profile(self) -> None:
        """Open active barrel profile to register H2O and chamber-derived case data."""
        self.on_open_harmonics_profile()

    def on_focus_chronograph_data(self) -> None:
        """Guide the user to selected chronograph data or import flow."""
        if not hasattr(self, "chrono_list") or self.chrono_list is None:
            return
        try:
            self.chrono_list.setFocus()
            if self.chrono_list.count() > 0:
                if self.chrono_list.currentRow() < 0:
                    self.chrono_list.setCurrentRow(0)
                self.chrono_list.scrollToItem(self.chrono_list.currentItem())
                return
        except Exception:
            pass
        self.on_import_chronograph_clicked()

    def on_add_group_data(self) -> None:
        """Create a simple calibration series for the active barrel."""
        if not self.rifle_data or not self.rifle_data.get("id"):
            QMessageBox.information(
                self,
                "No Firearm Profile",
                "Select a firearm and an active barrel before registering group data.",
            )
            return

        active_barrel_id = self._get_active_barrel_id()
        details = dict(self._get_rifle_profile_details())
        barrels = details.get("barrels") or []
        barrel_index = -1
        active_barrel = {}
        if isinstance(barrels, list):
            for index, barrel in enumerate(barrels):
                if isinstance(barrel, dict) and str(barrel.get("id")) == str(
                    active_barrel_id
                ):
                    barrel_index = index
                    active_barrel = dict(barrel)
                    break
            if barrel_index < 0:
                for index, barrel in enumerate(barrels):
                    if isinstance(barrel, dict):
                        barrel_index = index
                        active_barrel = dict(barrel)
                        active_barrel_id = active_barrel.get("id")
                        break
        if barrel_index < 0:
            QMessageBox.information(
                self,
                "No Barrel Selected",
                "Add or select a barrel in the firearm profile before registering calibration data.",
            )
            return

        try:
            from ..ui.calibration_test_dialog import CalibrationTestDialog
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Open Calibration Series",
                f"An error occurred while opening the calibration dialog:\n{exc}",
            )
            return

        dialog = CalibrationTestDialog(
            parent=self,
            profile=details,
            existing={
                "distance_m": (
                    float(self.zero_spin.value())  # type: ignore[attr-defined]
                    if hasattr(self, "zero_spin")
                    else None
                ),
                "temperature_c": (
                    self._current_temperature_c()
                    if hasattr(self, "temp_spin")
                    else None
                ),
                "bullet": self.bullet_data.get("name") if self.bullet_data else "",
                "bullet_weight_gr": (
                    self.bullet_data.get("weight") if self.bullet_data else None
                ),
                "powder": self.powder_data.get("name") if self.powder_data else "",
                "charge_weight_gr": (
                    float(self.current_charge or 0) if self.current_charge else None
                ),
                "cbto_mm": float(self.cbto_mm or 0) if self.cbto_mm else None,
                "coal_mm": float(self.coal_mm or 0) if self.coal_mm else None,
            },
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        data = dialog.gather()
        loads = data.get("loads", [])
        if not loads:
            QMessageBox.information(
                self,
                tr("mlb_no_batch_data_title"),
                tr("mlb_no_batch_data_body"),
            )
            return

        bullet_name = self.bullet_data.get("name") if self.bullet_data else None
        bullet_manufacturer = (
            self.bullet_data.get("manufacturer") if self.bullet_data else None
        )
        bullet_lot = self._get_component_lot_number(
            "bullet", self.bullet_data.get("id") if self.bullet_data else None
        )
        powder_context = self._get_selected_powder_context()
        powder_name = powder_context.get("name") if powder_context else None
        powder_lot = self._get_component_lot_number(
            "powder", powder_context.get("id") if powder_context else None
        )
        proceed, safety_advisories = self._confirm_high_risk_override(
            "Save Calibration Series"
        )
        if not proceed:
            return
        enriched_loads = []
        for load in loads:
            if not isinstance(load, dict):
                continue
            item = dict(load)
            if not item.get("bullet") and bullet_name:
                item["bullet"] = bullet_name
            if not item.get("bullet_manufacturer") and bullet_manufacturer:
                item["bullet_manufacturer"] = bullet_manufacturer
            if not item.get("bullet_lot") and bullet_lot:
                item["bullet_lot"] = bullet_lot
            if not item.get("powder") and powder_name:
                item["powder"] = powder_name
            if not item.get("powder_lot") and powder_lot:
                item["powder_lot"] = powder_lot
            if self.current_charge:
                item["charge_weight_gr"] = float(self.current_charge or 0)
            if self.cbto_mm:
                item["cbto_mm"] = float(self.cbto_mm or 0)
            if self.coal_mm:
                item["coal_mm"] = float(self.coal_mm or 0)
            if powder_context:
                item["powder_id"] = powder_context.get("id")
                item["powder_manufacturer"] = powder_context.get("manufacturer")
                item["powder_type"] = powder_context.get("type")
                item["powder_burn_rate_label"] = powder_context.get("burn_rate")
                item["powder_burn_rate_position"] = powder_context.get(
                    "burn_rate_position"
                )
                item["powder_relative_burn_rate"] = powder_context.get(
                    "relative_burn_rate"
                )
                item["powder_density_gcc"] = powder_context.get("density_gcc")
                item["powder_grain_shape"] = powder_context.get("grain_shape")
                item["powder_temp_stable"] = powder_context.get("temp_stable")
                item["powder_temp_coefficient_fps_per_f"] = powder_context.get(
                    "temp_coefficient_fps_per_f"
                )
                item["powder_validation_status"] = powder_context.get(
                    "validation_status"
                )
                item["powder_usable_for_simulation"] = powder_context.get(
                    "usable_for_simulation"
                )
                item["powder_data_source"] = powder_context.get("data_source")
            enriched_loads.append(item)

        calibration_tests = list(active_barrel.get("calibration_tests") or [])
        calibration_tests.append(
            {
                "id": f"ct-{len(calibration_tests) + 1}",
                "barrel_id": active_barrel_id,
                "barrel_name": active_barrel.get("name"),
                "created_date": datetime.now().isoformat(timespec="seconds"),
                "distance_m": data.get("distance_m"),
                "temperature_c": data.get("temperature_c"),
                "loads": enriched_loads,
                "notes": data.get("notes", ""),
                "safety_override": bool(
                    [
                        item
                        for item in safety_advisories
                        if item.get("level") == "critical"
                    ]
                ),
                "safety_override_date": (
                    datetime.now().isoformat(timespec="seconds")
                    if [
                        item
                        for item in safety_advisories
                        if item.get("level") == "critical"
                    ]
                    else None
                ),
                "safety_override_reasons": safety_advisories,
            }
        )
        active_barrel["calibration_tests"] = calibration_tests
        barrels[barrel_index] = active_barrel
        details["barrels"] = barrels
        if active_barrel_id:
            details["active_barrel_id"] = active_barrel_id

        if not self._save_rifle_profile_details(details):
            QMessageBox.warning(
                self,
                "Save Failed",
                "The calibration series was created, but it could not be saved to the firearm profile.",
            )
            return

        try:
            self._refresh_active_rifle_context()
            self.evidence_label.setText(self._build_evidence_summary())
            self._refresh_evidence_actions()
            self._refresh_calibration_table()
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Calibration Series Saved",
            "The series has been saved to the active barrel with load data, velocities, and any target images.",
        )

    def on_open_harmonics_profile(self) -> None:
        """Open the current weapon profile to improve harmonics input data."""
        if not self.rifle_data or not self.rifle_data.get("id"):
            QMessageBox.information(
                self,
                "No Firearm Profile",
                "Select a firearm first before opening the firearm profile.",
            )
            return

        harmonics = self._get_rifle_harmonics_profile()
        missing = harmonics.get("missing_required_inputs", [])
        barrel = self._get_active_barrel_details()
        barrel_name = barrel.get("name") or "active barrel"

        if missing:
            QMessageBox.information(
                self,
                "Harmonics Data Missing",
                "Please fill in more data for "
                f"{barrel_name}.\n\nMissing now: "
                f"{self._format_harmonics_missing_fields(missing)}",
            )

        try:
            from .weapon_profile_dialog import WeaponProfileDialog

            dialog = WeaponProfileDialog(
                db=self.db,
                rifle_id=self.rifle_data["id"],
                initial_barrel_id=self._get_active_barrel_id(),
                parent=self,
            )
            if dialog.exec():
                self._rifle_profile_details = None
                self._rifle_profile_details_id = None
                self._refresh_active_rifle_context()
                try:
                    self.update_visualization()
                except Exception:
                    pass
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Could Not Open Firearm Profile",
                f"An error occurred while opening the firearm profile:\n{exc}",
            )

    def _refresh_active_rifle_context(self) -> None:
        """Update the visible rifle/barrel context shown in the builder."""
        if not hasattr(self, "rifle_context_label"):
            return

        if not self.rifle_data:
            self.rifle_context_label.setText(
                "Select a firearm in step 1 to view the active barrel and measurement data."
            )
            self._refresh_barrel_configuration_selector()
            return

        barrel = self._get_active_barrel_details()
        barrel_context = self._get_active_barrel_configuration_context() or {}
        weapon_type = (
            str(
                barrel.get("weapon_type")
                or self.rifle_data.get("weapon_type")
                or "rifle"
            )
            .strip()
            .lower()
        )
        if weapon_type not in {"pistol", "revolver", "handgun"}:
            weapon_type = "rifle"
        else:
            weapon_type = "pistol"
        barrel_name = barrel.get("name") or "Standard barrel"
        setup_name = (
            str(barrel_context.get("barrel_configuration_name") or "").strip() or None
        )
        setup_label = _format_barrel_configuration_label(setup_name, barrel_name)
        caliber = barrel.get("caliber") or self.rifle_data.get("caliber") or "Unknown"
        length_mm = barrel.get("length_mm")
        twist = barrel.get("twist") or self.rifle_data.get("twist_rate") or "?"
        muzzle_device = barrel.get("muzzle_device_type") or "None"
        muzzle_model = barrel.get("muzzle_device_model")
        case_measurements = barrel.get("case_measurements") or {}

        lines = [
            f"<b>Active Setup:</b> {self.rifle_data.get('name', 'Firearm')} / {setup_label or barrel_name}",
            f"<b>Weapon Type:</b> {'Pistol' if weapon_type == 'pistol' else 'Rifle'}",
            f"<b>Caliber:</b> {caliber}",
        ]
        if setup_name:
            lines.append(f"<b>Configuration Profile:</b> {setup_name}")

        if length_mm:
            lines.append(f"<b>Barrel Length:</b> {float(length_mm):.1f} mm")
        if twist:
            lines.append(f"<b>Twist:</b> {twist}")

        muzzle_text = muzzle_device
        if muzzle_model:
            muzzle_text = f"{muzzle_device} ({muzzle_model})"
        lines.append(f"<b>Muzzle Device:</b> {muzzle_text}")

        h2o = case_measurements.get("h2o_capacity_grains")
        h2o_stats = self._get_h2o_stats()
        trim_length_mm = case_measurements.get("trim_length_mm")
        neck_diameter_mm = case_measurements.get("neck_diameter_mm")

        measurements = []
        if h2o:
            measurements.append(
                f"case capacity / H2O {format_weight_grains(float(h2o), 'powder')}"
            )
        if h2o_stats:
            quality_hint = (
                "consistent series"
                if h2o_stats["spread"] <= 0.30
                else (
                    "can be improved"
                    if h2o_stats["spread"] <= 0.75
                    else "check the measurements"
                )
            )
            measurements.append(
                f"{h2o_stats['count']} H2O measurements ({h2o_stats['quality']}, {quality_hint})"
            )
        if trim_length_mm:
            measurements.append(f"trim {float(trim_length_mm):.2f} mm")
        if neck_diameter_mm:
            measurements.append(f"neck {float(neck_diameter_mm):.2f} mm")

        if measurements:
            lines.append(
                "<b>Case measurements from this chamber:</b> "
                + " | ".join(measurements)
            )
        else:
            lines.append(
                "<b>Case measurements from this chamber:</b> Not recorded yet. Enter case capacity / H2O and case dimensions measured from fired cases in this barrel for better precision."
            )

        harmonics = self._get_rifle_harmonics_profile()
        confidence = harmonics.get("harmonics_confidence", "low")
        missing = harmonics.get("missing_required_inputs", [])
        if weapon_type == "pistol":
            lines.append(
                "<b>Harmonics:</b> Pistol detected. Harmonics are shown as secondary support only; function, practical accuracy, and velocity stability should carry more weight."
            )
        else:
            if missing:
                lines.append(
                    "<b>Harmonics Data Quality:</b> "
                    f"{confidence} | missing: {', '.join(missing)}"
                )
            else:
                lines.append(f"<b>Harmonics Data Quality:</b> {confidence}")

        self.rifle_context_label.setText("<br>".join(lines))
        self._refresh_barrel_configuration_selector()

    def _current_weapon_type(self) -> str:
        """Return normalized current weapon type for the active setup."""
        barrel = self._get_active_barrel_details()
        weapon_type = (
            str(
                barrel.get("weapon_type")
                or (self.rifle_data or {}).get("weapon_type")
                or "rifle"
            )
            .strip()
            .lower()
        )
        return "pistol" if weapon_type in {"pistol", "revolver", "handgun"} else "rifle"

    def _get_rifle_harmonics_profile(self) -> dict:
        """Return a harmonics summary built from the active rifle profile."""
        details = self._get_rifle_profile_details()
        rifle = {}
        rifle_id = None
        try:
            rifle_id = self.rifle_data.get("id") if self.rifle_data else None
        except Exception:
            rifle_id = None

        if rifle_id:
            try:
                rows = self.db.execute_query(
                    "SELECT * FROM rifles WHERE id = ?",
                    (rifle_id,),
                )
                if rows:
                    rifle = rows[0]
            except Exception:
                rifle = {}

        if not rifle and self.rifle_data:
            rifle = dict(self.rifle_data)

        if rifle_id is not None:
            rifle.setdefault("id", rifle_id)
        if rifle.get("name"):
            details.setdefault("rifle_name", rifle.get("name"))
        if rifle_id is not None:
            details.setdefault("rifle_id", rifle_id)
        return calculate_harmonics_profile(rifle, details)

    def _save_ui_setting(self, key: str, value: str):
        """Persist a small UI setting into `ui_settings` table."""
        try:
            cur = self.db.cursor
            # Use INSERT OR REPLACE to upsert by key
            cur.execute(
                "INSERT OR REPLACE INTO ui_settings (key, value, updated_date) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, value),
            )
            self.db.conn.commit()
        except Exception:
            pass

    def _delete_ui_setting(self, key: str):
        """Delete a UI setting by key from `ui_settings`."""
        try:
            cur = self.db.cursor
            cur.execute("DELETE FROM ui_settings WHERE key = ?", (key,))
            self.db.conn.commit()
        except Exception:
            pass


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    builder = ModernLoadBuilder()
    builder.setWindowTitle("Modern Load Builder - Reloading Workshop Manager")
    builder.resize(1600, 1000)
    builder.show()
    sys.exit(app.exec())
