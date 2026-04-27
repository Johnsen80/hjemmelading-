"""
Workflow Hub - Task-Based Navigation System
Erstatter tab-chaos med guided workflows
"""

import os
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..ui.reloading_theme import ReloadingTheme
from ..utils.i18n import tr

try:
    from ..ui.logo_helper import load_logo_pixmap
except Exception:
    # Packaged environments may not expose src.* imports the same way.
    # Provide a safe fallback that returns None when logo can't be loaded.
    def load_logo_pixmap(width: int | None = None) -> QPixmap | None:
        return None


class WorkflowCard(QFrame):
    """
    Interactive workflow card med hover effects
    """

    clicked = pyqtSignal(str)  # workflow_id

    def __init__(
        self,
        workflow_id: str,
        title: str,
        description: str,
        icon: str,
        color: str,
        status: str = "ready",
        parent=None,
    ):
        super().__init__(parent)
        self.workflow_id = workflow_id
        self.color = color
        self.status = status

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("variant", "statCard")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        accent = QFrame(self)
        accent.setFixedHeight(4)
        accent.setStyleSheet(
            f"background-color: {color}; border: none; border-radius: 2px;"
        )
        layout.addWidget(accent)

        # Icon + Status
        header_layout = QHBoxLayout()

        icon_label = QLabel(icon, self)
        icon_label.setProperty("role", "muted")
        header_layout.addWidget(icon_label)

        header_layout.addStretch()

        # Status badge
        if status == "in_progress":
            status_label = QLabel(tr("workflow_hub_status_active"), self)
            status_label.setProperty("variant", "warningText")
            header_layout.addWidget(status_label)
        elif status == "completed":
            status_label = QLabel(tr("workflow_hub_status_completed"), self)
            status_label.setProperty("variant", "successText")
            header_layout.addWidget(status_label)

        layout.addLayout(header_layout)

        # Title
        title_label = QLabel(title, self)
        title_label.setProperty("variant", "cardTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description, self)
        desc_label.setProperty("variant", "cardSubtitle")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        self.setLayout(layout)
        self.setMinimumHeight(200)

    def _darken_color(self, color: str) -> str:
        """Darken hex color"""
        color = color.lstrip("#")
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _lighten_color(self, color: str) -> str:
        """Lighten hex color"""
        color = color.lstrip("#")
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r, g, b = min(255, r + 30), min(255, g + 30), min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def mousePressEvent(self, event: Any):  # type: ignore
        """Click handler"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.workflow_id)
        super().mousePressEvent(event)


class WorkflowHub(QWidget):
    """
    Main Workflow Hub - Task-based navigation
    """

    workflow_selected = pyqtSignal(str)  # workflow_id

    def __init__(
        self, state_manager=None, mode_manager=None, parent=None, defer_ui: bool = True
    ):
        # Diagnostic: record who instantiated WorkflowHub (stacktrace)
        try:
            import traceback
            from datetime import datetime as _dt

            log_dir = os.path.join(os.getcwd(), "tools", "logs")
            os.makedirs(log_dir, exist_ok=True)
            stack_file = os.path.join(log_dir, "workflowhub_init_stack.log")
            detailed_file = os.path.join(log_dir, "workflowhub_init_detailed.log")
            with open(stack_file, "a", encoding="utf-8") as _f:
                _f.write(
                    f"workflowhub: init time={_dt.utcnow().isoformat()} pid={os.getpid()}\n"
                )
                traceback.print_stack(file=_f)
                _f.write("\n")
            # Also write a separate detailed trace including caller frames
            try:
                stack = traceback.extract_stack()
                caller = stack[-2] if len(stack) >= 2 else None
                with open(detailed_file, "a", encoding="utf-8") as _df:
                    _df.write("--- WORKFLOWHUB INSTANTIATED ---\n")
                    _df.write(f"time={_dt.utcnow().isoformat()} pid={os.getpid()}\n")
                    if caller is not None:
                        _df.write(
                            f"called_from: {caller.filename}:{caller.name}:{caller.lineno}\n"
                        )
                    try:
                        import traceback as _tb

                        _df.write("stack:\n")
                        _df.write("".join(_tb.format_stack()))
                    except Exception:
                        pass
                    _df.write("\n")
            except Exception:
                pass
        except Exception:
            pass
        # Force deferred UI creation to avoid accidental top-level widget
        # construction during import/instantiation. Ignore caller's
        # `defer_ui` argument and require an explicit `ensure_ui()` call
        # from well-behaved callers when they actually want the UI built.
        defer_ui = True

        # If instantiated without an explicit parent, prefer attaching
        # to the main application window (if available) to avoid creating
        # transient top-level widgets. This is a best-effort guard when
        # callers forget to pass `parent=`.
        try:
            if parent is None:
                try:
                    from PyQt6.QtWidgets import QApplication, QMainWindow

                    app = QApplication.instance()
                    if app:
                        widgets = list(getattr(app, "topLevelWidgets", lambda: [])())
                        for w in widgets:
                            if isinstance(w, QMainWindow):
                                parent = w
                                break
                except Exception:
                    pass
        except Exception:
            pass

        super().__init__(parent)
        self.state_manager = state_manager
        self.mode_manager = mode_manager
        # Track active workflows for compact display
        self.active_workflows: dict[str, str] = {}
        # Optional UI regions populated during init_ui
        self.active_section: Any | None = None
        self.active_layout: Any | None = None
        # For safety, always defer heavy UI construction by default to avoid
        # accidental top-level widget creation during imports/instantiation.
        # Callers should explicitly call `ensure_ui()` to initialize the UI.
        self._ui_deferred = True
        # Remember caller preference; if caller requested immediate init
        # (defer_ui=False), schedule a single-shot initialization so the
        # event loop (and any parenting/guards) is in place.
        self._defer_requested = bool(defer_ui)
        if defer_ui is False:
            try:
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(0, self.ensure_ui)
            except Exception:
                # Best-effort: leave UI deferred if scheduling fails
                pass

    def _legacy_workflow_ids(self) -> set[str]:
        return {"primer_tools"}

    def ensure_ui(self):
        """Force initialization of the UI if it was deferred."""
        # Flip the deferred flag before calling init_ui so init_ui can
        # reliably check the flag and avoid accidental construction when
        # the object was instantiated during import/early startup.
        if getattr(self, "_ui_deferred", False):
            self._write_startup_trace("enter_WorkflowHub.ensure_ui")
            self._ui_deferred = False
            try:
                self.init_ui()
            except Exception:
                # Keep behavior best-effort: if init fails, ensure flag
                # is left cleared so future calls will still attempt init.
                raise
            self._write_startup_trace("exit_WorkflowHub.ensure_ui")

    def _write_startup_trace(self, message: str) -> None:
        try:
            from datetime import datetime as _dt
            from pathlib import Path as _P

            trace_file = _P.cwd() / "tools" / "logs" / "startup_trace.log"
            with open(trace_file, "a", encoding="utf-8") as _tf:
                _tf.write(f"startup: {message} time={_dt.utcnow().isoformat()}\n")
        except Exception:
            pass

    def _apply_local_widget_shims(self, content: QWidget) -> None:
        # Local shims: ensure common lightweight widgets created without an
        # explicit parent are attached to the content widget. This prevents
        # accidental transient top-level windows during deferred initialization.
        _orig_QLabel = QLabel
        _orig_QPushButton = QPushButton
        _orig_QWidget = QWidget
        _orig_QGroupBox = QGroupBox
        _orig_QRadioButton = QRadioButton
        _orig_QScrollArea = QScrollArea
        _orig_QFrame = QFrame

        def _needs_parent_arg(a, kw):
            if "parent" in kw:
                return False
            if len(a) > 0 and isinstance(a[0], _orig_QWidget):
                return False
            return True

        def _local_label(*a, **kw):
            try:
                if not _needs_parent_arg(a, kw):
                    return _orig_QLabel(*a, **kw)
                if len(a) == 0:
                    return _orig_QLabel(content)
                return _orig_QLabel(a[0], content)
            except Exception:
                return _orig_QLabel(*a, **kw)

        def _local_button(*a, **kw):
            try:
                if not _needs_parent_arg(a, kw):
                    return _orig_QPushButton(*a, **kw)
                if len(a) == 0:
                    return _orig_QPushButton("", content)
                return _orig_QPushButton(a[0], content)
            except Exception:
                return _orig_QPushButton(*a, **kw)

        def _local_widget(*a, **kw):
            try:
                if not _needs_parent_arg(a, kw):
                    return _orig_QWidget(*a, **kw)
                return _orig_QWidget(content)
            except Exception:
                return _orig_QWidget(*a, **kw)

        def _local_groupbox(*a, **kw):
            try:
                if not _needs_parent_arg(a, kw):
                    return _orig_QGroupBox(*a, **kw)
                if len(a) == 0:
                    return _orig_QGroupBox("", content)
                return _orig_QGroupBox(a[0], content)
            except Exception:
                return _orig_QGroupBox(*a, **kw)

        def _local_radiobutton(*a, **kw):
            try:
                if not _needs_parent_arg(a, kw):
                    return _orig_QRadioButton(*a, **kw)
                if len(a) == 0:
                    return _orig_QRadioButton("", content)
                return _orig_QRadioButton(a[0], content)
            except Exception:
                return _orig_QRadioButton(*a, **kw)

        def _local_frame(*a, **kw):
            try:
                if not _needs_parent_arg(a, kw):
                    return _orig_QFrame(*a, **kw)
                return _orig_QFrame(content)
            except Exception:
                return _orig_QFrame(*a, **kw)

        # Shadow local names so subsequent constructions in this function
        # without explicit parents attach to `content`.
        globals()["QLabel"] = _local_label  # type: ignore
        globals()["QPushButton"] = _local_button  # type: ignore
        globals()["QWidget"] = _local_widget  # type: ignore
        globals()["QGroupBox"] = _local_groupbox  # type: ignore
        globals()["QRadioButton"] = _local_radiobutton  # type: ignore
        globals()["QFrame"] = _local_frame  # type: ignore

    def _init_scroll_container(self) -> tuple[QScrollArea, QWidget, QVBoxLayout]:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setProperty("variant", "clean")
        content = QWidget(scroll)
        self._apply_local_widget_shims(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        self._mode_widgets = []
        return scroll, content, layout

    def _build_hero_header(self, layout: QVBoxLayout, content: QWidget) -> None:
        from PyQt6.QtWidgets import QSizePolicy

        hero = QWidget(content)
        hero_layout = QHBoxLayout()
        hero.setLayout(hero_layout)
        logo_label = QLabel(hero)
        pix = load_logo_pixmap(160)
        if pix:
            logo_label.setPixmap(pix)
        logo_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        hero_layout.addWidget(logo_label, stretch=1)

        hero_text = QVBoxLayout()
        title = QLabel(tr("workflow_hub_title"), hero)
        title.setProperty("variant", "heroTitle")
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        hero_text.addWidget(title)

        subtitle = QLabel(
            tr("workflow_hub_subtitle"),
            hero,
        )
        subtitle.setProperty("variant", "heroSubtitle")
        subtitle.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        hero_text.addWidget(subtitle)
        hero_layout.addLayout(hero_text, stretch=2)
        layout.addWidget(hero)

    def _build_mode_status_group(self, layout: QVBoxLayout, content: QWidget) -> None:
        mode_group = QGroupBox(tr("workflow_hub_user_mode"), content)
        mode_group.setProperty("variant", "panel")
        mode_layout = QHBoxLayout()
        self.mode_status_label = QLabel(mode_group)
        self.mode_status_label.setProperty("role", "muted")
        self._update_mode_status_label()
        hint = QLabel(tr("workflow_hub_change_mode_hint"), mode_group)
        hint.setProperty("role", "muted")
        mode_layout.addWidget(self.mode_status_label)
        mode_layout.addStretch()
        mode_layout.addWidget(hint)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

    def _build_quick_start_group(self, layout: QVBoxLayout, content: QWidget) -> None:
        quick_group = QGroupBox(tr("workflow_hub_quick_start"), content)
        quick_group.setProperty("variant", "panel")
        quick_layout = QHBoxLayout()
        quick_group.setLayout(quick_layout)

        quick_load = QPushButton(tr("workflow_hub_open_load_flow"), quick_group)
        quick_load.setProperty("variant", "primary")
        quick_load.clicked.connect(
            lambda: self.workflow_selected.emit("load_development_workflow")
        )
        quick_layout.addWidget(quick_load)

        quick_chrono = QPushButton(tr("workflow_hub_import_chrono"), quick_group)
        quick_chrono.setProperty("variant", "secondary")
        quick_chrono.clicked.connect(
            lambda: self.workflow_selected.emit("chronograph_import")
        )
        quick_layout.addWidget(quick_chrono)

        quick_layout.addStretch()
        layout.addWidget(quick_group)
        self._register_mode_widget(quick_group, "beginner")

    def _build_premium_grid(self, layout: QVBoxLayout, content: QWidget) -> None:
        grid = QGridLayout()
        grid.setSpacing(24)
        premium_mods = [
            (
                "batch_workspace",
                tr("workflow_hub_batch_workspace"),
                tr("workflow_hub_batch_workspace_desc"),
                ReloadingTheme.SUCCESS,
                "batch_icon.png",
                "expert",
            ),
            (
                "target_analyzer",
                tr("workflow_hub_target_analyzer"),
                tr("workflow_hub_target_analyzer_desc"),
                ReloadingTheme.INFO,
                "target_icon.png",
                "expert",
            ),
            (
                "rifle_optic_manager",
                tr("workflow_hub_rifle_optics"),
                tr("workflow_hub_rifle_optics_desc"),
                ReloadingTheme.ACCENT_BRASS,
                "rifle_icon.png",
                "all",
            ),
            (
                "harmonics_lab",
                tr("workflow_hub_harmonics_lab"),
                tr("workflow_hub_harmonics_lab_desc"),
                ReloadingTheme.SUCCESS,
                "target_icon.png",
                "expert",
            ),
        ]
        for i, (wf_id, title, desc, color, icon_file, mode) in enumerate(premium_mods):
            card = QWidget(content)
            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(10)
            card.setLayout(card_layout)
            card.setProperty("variant", "statCard")

            accent = QFrame(card)
            accent.setFixedHeight(4)
            accent.setStyleSheet(
                f"background-color: {color}; border: none; border-radius: 2px;"
            )
            card_layout.addWidget(accent)

            icon_label = QLabel(card)
            pixmap = None
            try:
                icon_path = os.path.join(
                    os.path.dirname(__file__), "..", "assets", icon_file
                )
                tmp = QPixmap(icon_path)
                if tmp and not tmp.isNull():
                    pixmap = tmp
            except Exception:
                pixmap = None

            if not pixmap:
                try:
                    pixmap = load_logo_pixmap(32)
                except Exception:
                    pixmap = None

            if pixmap and not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(
                        64,
                        64,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            else:
                icon_label.setText("")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(icon_label)

            title_label = QLabel(title, card)
            title_label.setProperty("variant", "cardTitle")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(title_label)

            desc_label = QLabel(desc, card)
            desc_label.setProperty("variant", "cardSubtitle")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(desc_label)

            btn = QPushButton(tr("workflow_hub_start"), card)
            btn.setProperty("variant", "primary")
            btn.setProperty("size", "lg")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda _, wf_id=wf_id: self.workflow_selected.emit(wf_id)
            )
            card_layout.addWidget(btn)
            grid.addWidget(card, i // 2, i % 2)
            self._register_mode_widget(card, mode)
        layout.addLayout(grid)

    def _build_workflow_lists(self, layout: QVBoxLayout, content: QWidget) -> None:
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        sections = [
            (
                tr("workflow_hub_batch_workspace"),
                [
                    (
                        "load_development_workflow",
                        "",
                        tr("workflow_hub_batch_workspace"),
                        tr("workflow_hub_batch_workspace_full_desc"),
                        "all",
                    ),
                ],
            ),
            (
                tr("workflow_hub_testing_optimization"),
                [
                    (
                        "ocw_test",
                        "",
                        tr("workflow_hub_ocw_test"),
                        tr("workflow_hub_ocw_test_desc"),
                        "expert",
                    ),
                    (
                        "ladder_test",
                        "",
                        tr("workflow_hub_ladder_test"),
                        tr("workflow_hub_ladder_test_desc"),
                        "expert",
                    ),
                    (
                        "seating_depth",
                        "",
                        tr("workflow_hub_seating_depth"),
                        tr("workflow_hub_seating_depth_desc"),
                        "expert",
                    ),
                ],
            ),
            (
                tr("workflow_hub_components_database"),
                [
                    (
                        "component_database",
                        "",
                        tr("workflow_hub_component_database"),
                        tr("workflow_hub_component_database_desc"),
                        "all",
                    ),
                    (
                        "component_inventory",
                        "",
                        tr("workflow_hub_component_inventory"),
                        tr("workflow_hub_component_inventory_desc"),
                        "all",
                    ),
                    (
                        "primer_tools",
                        "",
                        tr("workflow_hub_primer_tools"),
                        tr("workflow_hub_primer_tools_desc"),
                        "expert",
                    ),
                ],
            ),
            (
                tr("workflow_hub_components"),
                [
                    (
                        "brass_manager",
                        "",
                        tr("workflow_hub_brass_manager"),
                        tr("workflow_hub_brass_manager_desc"),
                        "expert",
                    ),
                    (
                        "bullet_manager",
                        "",
                        tr("workflow_hub_bullet_manager"),
                        tr("workflow_hub_bullet_manager_desc"),
                        "expert",
                    ),
                    (
                        "powder_manager",
                        "",
                        tr("workflow_hub_powder_manager"),
                        tr("workflow_hub_powder_manager_desc"),
                        "expert",
                    ),
                    (
                        "primer_manager",
                        "",
                        tr("workflow_hub_primer_manager"),
                        tr("workflow_hub_primer_manager_desc"),
                        "expert",
                    ),
                ],
            ),
            (
                tr("workflow_hub_rifles_equipment"),
                [
                    (
                        "rifle_optic_manager",
                        "",
                        tr("workflow_hub_rifles_and_optics"),
                        tr("workflow_hub_rifles_and_optics_desc"),
                        "all",
                    ),
                    (
                        "ammo_profile_manager",
                        "",
                        tr("workflow_hub_ammo_profiles"),
                        tr("workflow_hub_ammo_profiles_desc"),
                        "all",
                    ),
                    (
                        "rifle_performance",
                        "",
                        tr("workflow_hub_rifle_performance"),
                        tr("workflow_hub_rifle_performance_desc"),
                        "expert",
                    ),
                ],
            ),
        ]

        for title, workflows in sections:
            self._add_category_compact(main_layout, title)
            for wf_id, icon, w_title, desc, mode in workflows:
                btn = self._create_list_button(
                    wf_id, icon, w_title, desc, parent=content, mode=mode
                )
                main_layout.addWidget(btn)

        layout.addLayout(main_layout)

    def _build_logo_footer(self, layout: QVBoxLayout, content: QWidget) -> None:
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label = QLabel(content)
        pixmap = load_logo_pixmap(256)
        if pixmap:
            logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        layout.addLayout(logo_layout)

    def _finalize_layout(self, scroll: QScrollArea, content: QWidget) -> None:
        try:
            scroll.setWidget(content)
        except Exception:
            pass

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.setLayout(outer)

    def init_ui(self):
        self._write_startup_trace("enter_WorkflowHub.init_ui")
        # Prevent accidental UI construction if this object is still
        # marked as deferred. Some callers may instantiate the hub during
        # startup; this guard ensures UI only builds when `ensure_ui()`
        # explicitly allows it.
        if getattr(self, "_ui_deferred", False):
            return

        scroll, content, layout = self._init_scroll_container()
        self._build_hero_header(layout, content)
        self._build_mode_status_group(layout, content)
        self._build_quick_start_group(layout, content)
        self._build_premium_grid(layout, content)
        self._build_workflow_lists(layout, content)
        self._build_logo_footer(layout, content)

        try:
            self._apply_mode_visibility()
        except Exception:
            pass

        self._finalize_layout(scroll, content)
        self._write_startup_trace("exit_WorkflowHub.init_ui")

    def _add_category_compact(self, layout, title: str):
        """Add a compact category header used to separate groups of workflows."""
        header = QLabel(title, self)
        header.setProperty("variant", "cardTitle")
        layout.addWidget(header)

    def _create_list_button(
        self,
        workflow_id: str,
        icon: str,
        title: str,
        description: str,
        parent: QWidget | None = None,
        mode: str = "all",
    ):
        """Create compact list-style button"""
        is_legacy = workflow_id in self._legacy_workflow_ids()
        display_title = tr("mw_with_legacy_suffix", label=title) if is_legacy else title
        label_text = f"{icon} {display_title}".strip()
        if parent is None:
            btn = QPushButton(label_text, self)
        else:
            btn = QPushButton(label_text, parent)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tooltip = (
            f"{description}\n\n{tr('mw_legacy_workflow')}" if is_legacy else description
        )
        btn.setToolTip(tooltip)
        btn.setProperty("variant", "list")

        btn.clicked.connect(
            lambda _, wf_id=workflow_id: self.workflow_selected.emit(wf_id)
        )

        self._register_mode_widget(btn, mode)

        return btn

    def _add_category(self, layout: QVBoxLayout, title: str, description: str):
        """Add category header"""
        category_frame = QFrame(self)
        category_frame.setProperty("variant", "statCard")

        category_layout = QVBoxLayout()
        category_layout.setContentsMargins(12, 10, 12, 10)
        category_layout.setSpacing(4)

        title_label = QLabel(title, category_frame)
        title_label.setProperty("variant", "cardTitle")
        category_layout.addWidget(title_label)

        desc_label = QLabel(description, category_frame)
        desc_label.setProperty("variant", "cardSubtitle")
        category_layout.addWidget(desc_label)

        category_frame.setLayout(category_layout)
        layout.addWidget(category_frame)

    def on_mode_toggled(self, checked: bool):
        """Mode toggle"""
        if not self.mode_manager:
            return
        mode_cls = None
        try:
            from .mode_manager import UserMode as _UserMode

            mode_cls = _UserMode
        except Exception:
            mode_cls = None

        if mode_cls is None:
            return

        if checked:  # Beginner selected
            self.mode_manager.set_mode(mode_cls.BEGINNER)
        else:  # Expert selected
            self.mode_manager.set_mode(mode_cls.EXPERT)

        self.update_mode_description()
        try:
            self._apply_mode_visibility()
        except Exception:
            pass

    def _update_mode_status_label(self) -> None:
        if not getattr(self, "mode_status_label", None) or not self.mode_manager:
            return
        try:
            if getattr(self.mode_manager, "is_research", lambda: False)():
                self.mode_status_label.setText(tr("workflow_hub_mode_research"))
                return
        except Exception:
            pass
        if self.mode_manager.is_beginner():
            self.mode_status_label.setText(tr("workflow_hub_mode_beginner"))
        else:
            self.mode_status_label.setText(tr("workflow_hub_mode_expert"))

    def update_mode_description(self):
        """Update mode description label"""
        try:
            self._update_mode_status_label()
        except Exception:
            pass

        try:
            self._apply_mode_visibility()
        except Exception:
            pass

    def _register_mode_widget(self, widget: QWidget, mode: str) -> None:
        try:
            self._mode_widgets.append((widget, mode))
        except Exception:
            pass

    def _apply_mode_visibility(self) -> None:
        current_mode = "beginner"
        try:
            if self.mode_manager:
                if getattr(self.mode_manager, "is_research", lambda: False)():
                    current_mode = "research"
                elif self.mode_manager.is_beginner():
                    current_mode = "beginner"
                else:
                    current_mode = "expert"
        except Exception:
            current_mode = "beginner"

        for widget, required_mode in list(getattr(self, "_mode_widgets", []) or []):
            try:
                if required_mode == "beginner":
                    widget.setVisible(current_mode == "beginner")
                elif required_mode == "expert":
                    widget.setVisible(current_mode in ("expert", "research"))
                elif required_mode == "research":
                    widget.setVisible(current_mode == "research")
                else:
                    widget.setVisible(True)
            except Exception:
                pass

    def refresh_for_mode(self) -> None:
        """Public hook for callers to re-apply mode visibility."""
        try:
            self._update_mode_status_label()
        except Exception:
            pass
        try:
            self._apply_mode_visibility()
        except Exception:
            pass

    def mark_workflow_active(self, workflow_id: str, title: str):
        """Mark workflow as active (simplified for compact view)"""
        self.active_workflows[workflow_id] = title

    def mark_workflow_completed(self, workflow_id: str):
        """Mark workflow as completed"""
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]

    def _update_active_section(self):
        """Update active workflows display (disabled in compact view)"""
        # Compact view doesn't have active_layout anymore
        pass

        self.active_section.show()

        col = 0
        for workflow_id, title in self.active_workflows.items():
            # Ensure the card is parented to this hub so it is not created
            # as a transient top-level widget before being added to layouts.
            card = WorkflowCard(
                workflow_id,
                title,
                tr("workflow_hub_click_to_continue"),
                "",
                "#f39c12",
                status="in_progress",
                parent=self,
            )
            card.clicked.connect(self.workflow_selected.emit)
            self.active_layout.addWidget(card, 0, col)
            col += 1


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    # When run as a script, force UI initialization.
    window = WorkflowHub(defer_ui=False)
    window.setMinimumSize(1200, 800)
    window.show()
    sys.exit(app.exec())
