"""
Workflow Hub - Task-Based Navigation System
Erstatter tab-chaos med guided workflows
"""

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

from src.ui.logo_helper import load_logo_pixmap


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

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Base style
        self.base_style = f"""
            WorkflowCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self._darken_color(color)});
                border-radius: 12px;
                border: 2px solid {self._darken_color(color)};
                padding: 12px;
            }}
            WorkflowCard:hover {{
                border: 3px solid #2c3e50;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self._lighten_color(color)}, stop:1 {color});
            }}
        """
        self.setStyleSheet(self.base_style)

        layout = QVBoxLayout()

        # Icon + Status
        header_layout = QHBoxLayout()

        icon_label = QLabel(icon, self)
        icon_label.setStyleSheet(
            "font-size: 36px; background: transparent; border: none;"
        )
        header_layout.addWidget(icon_label)

        header_layout.addStretch()

        # Status badge
        if status == "in_progress":
            status_label = QLabel("🔄 Aktiv", self)
            status_label.setStyleSheet(
                """
                background-color: #f39c12;
                color: white;
                padding: 5px 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 11px;
            """
            )
            header_layout.addWidget(status_label)
        elif status == "completed":
            status_label = QLabel("✅ Done", self)
            status_label.setStyleSheet(
                """
                background-color: #27ae60;
                color: white;
                padding: 5px 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 11px;
            """
            )
            header_layout.addWidget(status_label)

        layout.addLayout(header_layout)

        # Title
        title_label = QLabel(title, self)
        title_label.setStyleSheet(
            """
            font-size: 16px;
            font-weight: bold;
            color: white;
            background: transparent;
            border: none;
        """
        )
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description, self)
        desc_label.setStyleSheet(
            """
            font-size: 11px;
            color: rgba(255, 255, 255, 200);
            background: transparent;
            border: none;
        """
        )
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

    def mousePressEvent(self, event):
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
                        for w in app.topLevelWidgets():
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

    def ensure_ui(self):
        """Force initialization of the UI if it was deferred."""
        # Flip the deferred flag before calling init_ui so init_ui can
        # reliably check the flag and avoid accidental construction when
        # the object was instantiated during import/early startup.
        if getattr(self, "_ui_deferred", False):
            self._ui_deferred = False
            try:
                self.init_ui()
            except Exception:
                # Keep behavior best-effort: if init fails, ensure flag
                # is left cleared so future calls will still attempt init.
                raise

    def init_ui(self):
        # Prevent accidental UI construction if this object is still
        # marked as deferred. Some callers may instantiate the hub during
        # startup; this guard ensures UI only builds when `ensure_ui()`
        # explicitly allows it.
        if getattr(self, "_ui_deferred", False):
            return

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QWidget(scroll)
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
                # default parent -> content
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

        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # HERO HEADER
        # Hero header: vis faktisk logo og tydelig tittel
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
        title = QLabel("VALKYRIE BALLISTICS", hero)
        title.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #e0e0e0; margin-bottom: 0px; letter-spacing: 2px;"
        )
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        hero_text.addWidget(title)
        subtitle = QLabel(
            "Premium reloading, ballistics & analysis. Velg modul for å komme i gang.",
            hero,
        )
        subtitle.setStyleSheet(
            "font-size: 17px; color: #ffd700; margin-bottom: 10px; font-weight: 600;"
        )
        subtitle.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        hero_text.addWidget(subtitle)
        hero_layout.addLayout(hero_text, stretch=2)
        layout.addWidget(hero)

        # Mode selector
        mode_group = QGroupBox("⚙ Brukermodus", content)
        mode_layout = QHBoxLayout()
        self.radio_beginner = QRadioButton("▶ Nybegynner (Guidet)", mode_group)
        self.radio_expert = QRadioButton("▶▶ Ekspert (Hurtig tilgang)", mode_group)
        if self.mode_manager:
            if self.mode_manager.is_beginner():
                self.radio_beginner.setChecked(True)
            else:
                self.radio_expert.setChecked(True)
        else:
            self.radio_beginner.setChecked(True)
        self.radio_beginner.toggled.connect(self.on_mode_toggled)
        mode_layout.addWidget(self.radio_beginner)
        mode_layout.addWidget(self.radio_expert)
        self.mode_description = QLabel(mode_group)
        self.mode_description.setStyleSheet(
            "color: #7f8c8d; font-size: 11px; font-style: italic;"
        )
        mode_layout.addWidget(self.mode_description)
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # PREMIUM GRID MED HOVEDMODULER
        import os

        grid = QGridLayout()
        grid.setSpacing(24)
        premium_mods = [
            (
                "dashboard",
                "Dashboard",
                "Oversikt, AI-tips, widgets og statistikk",
                "#ffd700",
                "dashboard_icon.png",
            ),
            (
                "batch_qc",
                "Batch QC",
                "Batch-logging, analyse og rapportering",
                "#27ae60",
                "batch_icon.png",
            ),
            (
                "target_analyzer",
                "Bildeanalyse",
                "Automatisk skivegjenkjenning og treffanalyse",
                "#00bfff",
                "target_icon.png",
            ),
            (
                "rifle_optic_manager",
                "Våpen & Optikk",
                "Profil, ballistikk og utstyr",
                "#bfa14a",
                "rifle_icon.png",
            ),
        ]
        for i, (wf_id, title, desc, color, icon_file) in enumerate(premium_mods):
            card = QWidget(content)
            card_layout = QVBoxLayout()
            card.setLayout(card_layout)
            card.setStyleSheet(
                f"background-color: #23242b; border-radius: 18px; border: 2px solid {color}; padding: 24px;"
            )
            # Ikon
            # Prefer module-specific icon; fall back to central Logo at different sizes, then empty text
            icon_label = QLabel(card)
            pixmap = None
            try:
                if wf_id == "dashboard":
                    pixmap = load_logo_pixmap(64)
                else:
                    icon_path = os.path.join(
                        os.path.dirname(__file__), "..", "assets", icon_file
                    )
                    tmp = QPixmap(icon_path)
                    if tmp and not tmp.isNull():
                        pixmap = tmp
            except Exception:
                pixmap = None

            if not pixmap:
                # try smaller project logo as a fallback
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
            # Tittel
            title_label = QLabel(title, card)
            title_label.setStyleSheet(
                f"font-size: 22px; font-weight: bold; color: {color}; margin-top: 8px;"
            )
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(title_label)
            # Beskrivelse
            desc_label = QLabel(desc, card)
            desc_label.setStyleSheet(
                "font-size: 13px; color: #e0e0e0; margin-bottom: 8px;"
            )
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(desc_label)
            # Start-knapp
            btn = QPushButton("Start", card)
            style = (
                f"background-color: {color}; color: #23242b; font-weight: bold; "
                f"border-radius: 8px; padding: 10px 24px; font-size: 15px;"
            )
            btn.setStyleSheet(style)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda _, wf_id=wf_id: self.workflow_selected.emit(wf_id)
            )
            card_layout.addWidget(btn)
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)

        # Resten av workflow-knappene
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        self._add_category_compact(main_layout, "▶ LOAD DEVELOPMENT")
        workflows = [
            (
                "load_development_workflow",
                "🎯",
                "Load Development Workflow",
                "KOMPLETT: Load → Batch → Test → Analyze → Optimize → Finalize",
            ),
        ]
        for wf_id, icon, title, desc in workflows:
            btn = self._create_list_button(wf_id, icon, title, desc, parent=content)
            main_layout.addWidget(btn)

        self._add_category_compact(main_layout, "▶ TESTING & OPTIMIZATION")
        testing = [
            (
                "ocw_test",
                "▲",
                "OCW Test",
                "Optimal Charge Weight - find pressure nodes",
            ),
            ("ladder_test", "▲▲", "Ladder Test", "Velocity ladder analysis"),
            (
                "seating_depth",
                "◆",
                "Seating Depth Test",
                "Berger method - find best CBTO/jump",
            ),
        ]
        for wf_id, icon, title, desc in testing:
            btn = self._create_list_button(wf_id, icon, title, desc, parent=content)
            main_layout.addWidget(btn)

        self._add_category_compact(main_layout, "▶ COMPONENTS & DATABASE")
        components = [
            (
                "component_database",
                "■",
                "Component Database",
                "Bullets, powder, primers, brass inventory",
            ),
            (
                "component_inventory",
                "▣",
                "Component Inventory",
                "Stock levels, costs, lot tracking",
            ),
            (
                "primer_tools",
                "◆",
                "Primer Tools",
                "Selector, seating guide, pressure diagnostics",
            ),
        ]
        for wf_id, icon, title, desc in components:
            btn = self._create_list_button(wf_id, icon, title, desc, parent=content)
            main_layout.addWidget(btn)

        self._add_category_compact(main_layout, "🥉 Komponenter")
        components = [
            (
                "brass_manager",
                "🥉",
                "Brass/Hylse Manager",
                "Lifecycle tracking: Kjøp → Firing → Annealing → Retirement",
            ),
            (
                "bullet_manager",
                "🎯",
                "Bullet Manager",
                "Spor bullet lots, BC testing, sorting",
            ),
            (
                "powder_manager",
                "💨",
                "Powder Manager",
                "Lot tracking, temp sensitivity, burn rate",
            ),
            ("primer_manager", "💥", "Primer Manager", "Lot variasjon, pocket sizing"),
        ]
        for wf_id, icon, title, desc in components:
            btn = self._create_list_button(wf_id, icon, title, desc, parent=content)
            main_layout.addWidget(btn)

        self._add_category_compact(main_layout, "🔫 Rifles & Utstyr")
        equipment = [
            (
                "rifle_optic_manager",
                "🎯",
                "Rifles & Optikk",
                "Administrer våpen og kikkertsikter",
            ),
            (
                "ammo_profile_manager",
                "📦",
                "Ammunisjonsprofiler",
                "Lagrede ladninger med ballistic data",
            ),
            (
                "rifle_performance",
                "📊",
                "Rifle Performance",
                "Cold bore, barrel tracking, analyse",
            ),
        ]
        for wf_id, icon, title, desc in equipment:
            btn = self._create_list_button(wf_id, icon, title, desc, parent=content)
            main_layout.addWidget(btn)
        # VIS KUN LOGOEN SENTRERT (flyttet til topp i layout)
        # Ensure the main_layout is attached to the content layout so
        # widgets created with the content as parent are properly parented.
        layout.addLayout(main_layout)
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label = QLabel(content)
        pixmap = load_logo_pixmap(256)
        if pixmap:
            logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        layout.addLayout(logo_layout)

        # Finalize scroll/content parenting and attach scroll into this widget
        try:
            scroll.setWidget(content)
        except Exception:
            pass

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.setLayout(outer)

    def _add_category_compact(self, layout, title: str):
        """Add a compact category header used to separate groups of workflows."""
        header = QLabel(title, self)
        header.setStyleSheet(
            "font-size:14px; font-weight:700; color: #ffd700; margin-top:12px; margin-bottom:6px;"
        )
        layout.addWidget(header)

    def _create_list_button(
        self,
        workflow_id: str,
        icon: str,
        title: str,
        description: str,
        parent: QWidget | None = None,
    ):
        """Create compact list-style button"""
        if parent is None:
            btn = QPushButton(f"{icon}  {title}", self)
        else:
            btn = QPushButton(f"{icon}  {title}", parent)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(description)

        btn.setStyleSheet(
            """
            QPushButton {
                background-color: white;
                border: 1px solid #dce4ec;
                border-radius: 6px;
                text-align: left;
                padding: 12px 15px;
                min-height: 45px;
                font-size: 13px;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
                border: 2px solid #3498db;
            }
            QPushButton:pressed {
                background-color: #d5dbdb;
            }
        """
        )

        btn.clicked.connect(
            lambda _, wf_id=workflow_id: self.workflow_selected.emit(wf_id)
        )

        return btn

    def _add_category(self, layout: QVBoxLayout, title: str, description: str):
        """Add category header"""
        category_frame = QFrame(self)
        category_frame.setStyleSheet(
            """
            QFrame {
                background-color: #ecf0f1;
                border-left: 4px solid #3498db;
                border-radius: 5px;
                padding: 10px;
                margin-top: 15px;
            }
        """
        )

        category_layout = QVBoxLayout()

        title_label = QLabel(title, category_frame)
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #2c3e50; background: transparent; border: none;"
        )
        category_layout.addWidget(title_label)

        desc_label = QLabel(description, category_frame)
        desc_label.setStyleSheet(
            "font-size: 12px; color: #7f8c8d; background: transparent; border: none;"
        )
        category_layout.addWidget(desc_label)

        category_frame.setLayout(category_layout)
        layout.addWidget(category_frame)

    def on_mode_toggled(self, checked: bool):
        """Mode toggle"""
        if not self.mode_manager:
            return

        from src.modules.user_mode import UserMode

        if checked:  # Beginner selected
            self.mode_manager.set_mode(UserMode.BEGINNER)
        else:  # Expert selected
            self.mode_manager.set_mode(UserMode.EXPERT)

        self.update_mode_description()

    def update_mode_description(self):
        """Update mode description label"""
        if not self.mode_manager:
            return

        if self.mode_manager.is_beginner():
            self.mode_description.setText(
                "Full tooltips, wizards, confirmation dialogs"
            )
        else:
            self.mode_description.setText(
                "Minimal UI, keyboard shortcuts, direct access"
            )

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
                "Click to continue...",
                "🔄",
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
