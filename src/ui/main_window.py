from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from PyQt6.QtCore import QSettings, QSize, Qt
    from PyQt6.QtGui import QAction, QIcon, QKeySequence, QPixmap
    from PyQt6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QStackedWidget,
        QStatusBar,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
else:
    try:
        from PyQt6.QtCore import QSettings, QSize, Qt
        from PyQt6.QtGui import QAction, QIcon, QKeySequence
        from PyQt6.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QStackedWidget,
            QStatusBar,
            QTabWidget,
            QVBoxLayout,
            QWidget,
        )

        _HAS_QT = True
    except Exception:  # pragma: no cover - optional dependency fallback
        _HAS_QT = False

        class _Stub:
            """Minimal stub base class used when PyQt6 is unavailable."""

        # Annotate with Any so mypy treats these as simple runtime names
        QSettings: Any = _Stub
        QSize: Any = _Stub

        class Qt:  # type: ignore
            class WindowType:
                WindowStaysOnTopHint = 0

            class AlignmentFlag:
                AlignCenter = 0

        QAction: Any = _Stub
        QIcon: Any = _Stub
        QKeySequence: Any = _Stub

        # Lightweight widget stubs: classes are empty and will allow class
        # definitions that inherit from them to succeed in headless environments.
        QDialog: Any = _Stub
        QHBoxLayout: Any = _Stub
        QLabel: Any = _Stub
        QListWidget: Any = _Stub
        QMainWindow: Any = object

        class _MsgBox:
            @staticmethod
            def critical(*args, **kwargs):
                return None

        QMessageBox: Any = _MsgBox
        QPushButton: Any = _Stub
        QStackedWidget: Any = _Stub
        QStatusBar: Any = _Stub
        QTabWidget: Any = _Stub
        QVBoxLayout: Any = _Stub
        QWidget: Any = _Stub

import os

from src.logging_config import get_logger

# Per-user persistent diagnostics helper
try:
    from HjemmeladingApp.utils.safe_logger import append_exception, append_message
except Exception:

    def append_exception(
        msg: str = "", exc: BaseException | None = None, app_name: str = ""
    ) -> None:
        return None

    def append_message(msg: str, app_name: str = "") -> None:
        return None


# Logo helpers: try to load a project logo or fall back to generated skull icon
try:
    from src.ui.logo_helper import load_logo_pixmap
except Exception:
    # Provide a safe fallback if helper cannot be imported
    def load_logo_pixmap(width: int | None = None) -> Optional["QPixmap"]:
        return None


try:
    from src.assets.logo import get_window_icon_pixmap
except Exception:

    def get_window_icon_pixmap(size=64) -> Any:
        return None


# Theme helper (fallback if module not available)
try:
    from src.ui.reloading_theme import ReloadingTheme
except Exception:

    class ReloadingTheme:  # type: ignore[no-redef]
        @staticmethod
        def get_stylesheet():
            return """
            QWidget { background-color: #23242b; color: #e0e0e0; }
            """


# Simple translation helper (fallback to identity)
try:
    from src.utils.i18n import tr
except Exception:

    def tr(key: str, lang: str | None = None, *args: object, **kwargs: object) -> str:
        return key


logger = get_logger(__name__)


# Headless detection helper — treats offscreen/minimal QT platforms and CI/HEADLESS env as headless
def _is_headless() -> bool:
    qp = os.environ.get("QT_QPA_PLATFORM", "").lower()
    if qp in ("offscreen", "minimal"):
        return True
    if os.environ.get("CI", "").lower() in ("1", "true"):
        return True
    if os.environ.get("HEADLESS", "").lower() in ("1", "true"):
        return True
    return False


_HEADLESS = _is_headless()


def _run_modal(dialog: Any) -> None:
    """Run a dialog in a headless-safe way: show() if headless, otherwise exec().

    Annotate `dialog` as `Any` so static type checkers accept runtime duck-typing
    (some stubbed headless fallbacks declare widget types as `object`).
    """
    if _HEADLESS:
        try:
            # Local shims: ensure lightweight widgets created during settings
            # application are parented to the main window to avoid stray
            # top-level widgets appearing during startup.
            try:
                _orig_QLabel = QLabel
                _orig_QPushButton = QPushButton
                _orig_QMenu = QMenu
                _orig_QWidget = QWidget

                def _make_label(*a, **kw):
                    try:
                        if "parent" in kw:
                            return _orig_QLabel(*a, **kw)
                        if len(a) > 0 and isinstance(a[0], _orig_QWidget):
                            return _orig_QLabel(*a, **kw)
                        return _orig_QLabel(self)
                    except Exception:
                        return _orig_QLabel(*a, **kw)

                def _make_button(*a, **kw):
                    try:
                        if "parent" in kw:
                            return _orig_QPushButton(*a, **kw)
                        if len(a) > 0 and isinstance(a[0], _orig_QWidget):
                            return _orig_QPushButton(*a, **kw)
                        return _orig_QPushButton(*a, **{**kw, "parent": self})
                    except Exception:
                        return _orig_QPushButton(*a, **kw)

                def _make_menu(*a, **kw):
                    try:
                        if "parent" in kw:
                            return _orig_QMenu(*a, **kw)
                        if len(a) > 0 and isinstance(a[0], _orig_QWidget):
                            return _orig_QMenu(*a, **kw)
                        return _orig_QMenu(self)
                    except Exception:
                        return _orig_QMenu(*a, **kw)

                globals()["QLabel"] = _make_label  # type: ignore
                globals()["QPushButton"] = _make_button  # type: ignore
                globals()["QMenu"] = _make_menu  # type: ignore
            except Exception:
                pass
            # Non-blocking show() is better for CI/offscreen environments
            dialog.show()
        except Exception:
            # best-effort: ignore failures when showing in headless
            pass
    else:
        try:
            dialog.exec()
        except Exception:
            try:
                dialog.show()
            except Exception:
                pass


# Apply saved theme/settings helper
def _build_theme_css_from_cfg(cfg: dict) -> str:
    # Minimal translation of settings into a stylesheet string for the app.
    theme = cfg.get("theme", "light")
    rgb = cfg.get("rgb", {"r": 60, "g": 120, "b": 200})
    btn_style = cfg.get("button_style", "filled")
    r = int(rgb.get("r", 60))
    g = int(rgb.get("g", 120))
    b = int(rgb.get("b", 200))
    base_hex = f"#{r:02x}{g:02x}{b:02x}"
    if theme == "dark":
        win_hex = "#1c1c1e"
        text_hex = "#ededed"
    elif theme == "high-contrast":
        win_hex = "#000000"
        text_hex = "#ffff00"
    else:
        # light
        win_hex = "#f6f7f8"
        text_hex = "#111111"

    # Buttons
    if btn_style == "filled":
        btn_css = f"background-color: {base_hex}; color: {text_hex};"
    elif btn_style == "outlined":
        btn_css = f"background-color: transparent; color: {text_hex}; border: 2px solid {base_hex};"
    else:
        btn_css = f"background-color: transparent; color: {text_hex}; border: none;"

    css = f"""
QWidget {{ background-color: {win_hex}; color: {text_hex}; }}
QPushButton {{ {btn_css} padding:6px 10px; border-radius:6px; }}
QLineEdit, QTextEdit {{ background-color: {win_hex}; color: {text_hex}; border: 1px solid {base_hex}; }}
QTabWidget::pane {{ background: {win_hex}; }}
"""
    return css


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Guard to avoid double-initializing the UI (prevents duplicate menus/windows)
        self._ui_initialized = False
        self.setWindowTitle("Valkyrie Ballistics")
        self.setMinimumSize(900, 600)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        # Apply app theme early so initial landing UI matches saved appearance.
        # Read minimal saved theme values from QSettings synchronously to
        # avoid a visual flash from default -> user theme during startup.
        try:
            try:
                from PyQt6.QtCore import QSettings

                qs = QSettings("ReloadingWorkshop", "ReloadingManager")
                theme = qs.value("theme", None)
                rgb = qs.value("rgb", None)
                btn_style = qs.value("button_style", None)
                cfg = {}
                if theme is not None:
                    cfg["theme"] = theme
                if isinstance(rgb, dict):
                    cfg["rgb"] = rgb
                if btn_style is not None:
                    cfg["button_style"] = btn_style

                # Start from the baseline theme and merge user CSS
                base_css = ""
                try:
                    base_css = ReloadingTheme.get_stylesheet() or ""
                except Exception:
                    base_css = ""

                try:
                    user_css = _build_theme_css_from_cfg(cfg) if cfg else ""
                except Exception:
                    user_css = ""

                combined = base_css + "\n" + user_css if user_css else base_css
                if combined:
                    self.setStyleSheet(combined)
                else:
                    # Fallback to baseline
                    try:
                        self.setStyleSheet(ReloadingTheme.get_stylesheet())
                    except Exception:
                        pass
            except Exception:
                # If QSettings or theme merging fails, fall back gracefully
                try:
                    self.setStyleSheet(ReloadingTheme.get_stylesheet())
                except Exception:
                    pass
        except Exception:
            pass
        central = QWidget(self)
        central.setObjectName("landingCentral")
        layout = QVBoxLayout()
        # place items toward top so buttons appear higher on the page
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(36, 18, 36, 18)
        layout.setSpacing(12)

        # subtle logo shown near the top as a faint, non-interactive element
        try:
            logo_lbl = QLabel(central)
            logo_pix = load_logo_pixmap(420)
            if logo_pix:
                try:

                    logo_lbl.setPixmap(logo_pix)
                except Exception:
                    logo_lbl.setPixmap(logo_pix)
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # make logo non-interactive so clicks reach buttons
            try:
                from PyQt6.QtWidgets import QGraphicsOpacityEffect

                eff = QGraphicsOpacityEffect(logo_lbl)
                eff.setOpacity(0.10)
                logo_lbl.setGraphicsEffect(eff)
                logo_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            except Exception:
                pass
            # limit vertical space so it doesn't dominate the page
            logo_lbl.setMaximumHeight(160)
            layout.addWidget(logo_lbl)
        except Exception:
            # ignore failures to render logo and continue
            pass

        # Quick-launch shortcuts: provide direct buttons to important modules
        try:
            row = QWidget(central)
            row_layout = QHBoxLayout()
            row_layout.setSpacing(16)
            row_layout.setContentsMargins(0, 4, 0, 4)
            row.setLayout(row_layout)

            def _make_btn(text, slot):
                b = QPushButton(text, row)
                b.setMinimumHeight(64)
                b.setProperty("class", "landingBig")
                try:
                    b.clicked.connect(slot)
                except Exception:
                    pass
                return b

            btn_weapon = _make_btn("Våpenprofiler", self.show_weapon_profile_editor)
            btn_load = _make_btn(
                "Reloading",
                lambda: self.launch_workflow("load_development_workflow"),
            )
            btn_ballistics = _make_btn(
                "Ballistics / Terrengkart", self.show_ballistics_simulator
            )

            # center the buttons row visually
            row_layout.addStretch(1)
            row_layout.addWidget(btn_weapon)
            row_layout.addWidget(btn_load)
            row_layout.addWidget(btn_ballistics)
            row_layout.addStretch(1)

            layout.addWidget(row)
        except Exception:
            layout.addWidget(QLabel("Snarveier: (knapper utilgjengelige)"))

        # add a flexible spacer so content hugs the top
        try:
            from PyQt6.QtWidgets import QSizePolicy, QSpacerItem

            spacer = QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
            layout.addItem(spacer)
        except Exception:
            pass

        central.setLayout(layout)
        self.setCentralWidget(central)

        # Defer applying user settings until after the window is constructed
        # to avoid long-running or blocking work during MainWindow.__init__.
        try:
            from PyQt6.QtCore import QTimer

            # schedule apply_user_settings to run once the event loop starts
            QTimer.singleShot(0, self.apply_user_settings)
        except Exception:
            # If QTimer isn't available, fall back to direct call (best-effort)
            try:
                self.apply_user_settings()
            except Exception as e:
                try:
                    import traceback

                    err = f"Exception during apply_user_settings: {e}\n{traceback.format_exc()}"
                    try:
                        logger.exception("%s", err)
                    except Exception:
                        pass
                    try:
                        append_exception(err, e)
                    except Exception:
                        pass
                finally:
                    try:
                        QMessageBox.critical(None, "Oppstartsfeil", str(e))
                    except Exception:
                        pass
                    raise

        # Quick debug shortcut to list and launch workflows (helps when UI elements are hard to reach)
        try:
            act = QAction("DebugShortcut", self)
            act.setShortcut(QKeySequence("Ctrl+D"))
            act.triggered.connect(self._open_workflow_debug)
            # Add to the window so the shortcut is active
            self.addAction(act)
        except Exception:
            pass

        # Check for saved workflows after UI is ready — schedule to avoid blocking
        try:
            # Do not auto-check saved workflows at startup; this can trigger
            # late imports that create top-level widgets. Make resume available
            # via the File menu instead.
            pass
        except Exception:
            try:
                self.check_saved_workflows()
            except Exception:
                pass

    def _open_workflow_debug(self):
        """Temporary debug dialog to list available workflows and launch them."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Debug: Launch workflow")
        dlg.setMinimumSize(400, 300)
        layout = QVBoxLayout()
        listw = QListWidget()

        # Populate from the workflow map used by launch_workflow. Filter out
        # workflows that require optional dependencies (matplotlib/OpenCV)
        from src.utils.optional_deps import HAS_CV2, HAS_MPL

        wf_keys = [
            ("load_development_workflow", None),
            ("ocw_test", None),
            ("ladder_test", "mpl"),
            ("seating_depth", None),
            ("smart_wizard", None),
            ("temperature_test", None),
            ("saami_compliance", None),
            ("chronograph_import", None),
            ("cold_bore", None),
            ("batch_qc", "mpl"),
            ("lot_tracker", None),
            ("drop_chart", "mpl"),
            ("wind_drift", None),
            ("zero_shift", None),
            ("target_analyzer", "cv2"),
        ]

        for k, req in wf_keys:
            if req == "mpl" and not HAS_MPL:
                # Skip workflows that need matplotlib if it's absent
                continue
            if req == "cv2" and not HAS_CV2:
                # Skip CV workflows if OpenCV is absent
                continue
            listw.addItem(k)
        layout.addWidget(listw)

        btn_launch = QPushButton("Launch Selected")

        def _do_launch():
            it = listw.currentItem()
            if it:
                self.launch_workflow(it.text())
                dlg.accept()

        btn_launch.clicked.connect(_do_launch)
        layout.addWidget(btn_launch)

        dlg.setLayout(layout)
        dlg.exec()

    def open_measurement_wizard(self):
        """Open the measurement wizard dialog in a safe, lazy-imported way."""
        try:
            from src.modules.measurement_wizard import show_measurement_wizard

            show_measurement_wizard()
        except Exception as e:
            try:
                QMessageBox.critical(
                    self, "Feil", f"Kunne ikke åpne Measurement Wizard: {e}"
                )
            except Exception:
                pass

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        # Avoid running initialization twice (guards duplicate menus/windows)
        if getattr(self, "_ui_initialized", False):
            return
        self._ui_initialized = True
        self.setWindowTitle("Valkyrie Ballistics - Precision Reloading System")
        self.setGeometry(100, 100, 1400, 900)

        # Safety: locally shadow QLabel/QPushButton to ensure widgets
        # created without an explicit parent default to the main window.
        # This reduces transient top-level widgets during startup.
        try:
            _orig_QLabel = QLabel
            _orig_QPushButton = QPushButton
            _orig_QMenu = QMenu
            _orig_QGroupBox = QGroupBox
            _orig_QRadioButton = QRadioButton
            _orig_QTabWidget = QTabWidget

            def _make_label(*a, **kw):
                try:
                    if "parent" in kw:
                        return _orig_QLabel(*a, **kw)
                    if len(a) > 0 and isinstance(a[0], QWidget):
                        return _orig_QLabel(*a, **kw)
                    if len(a) == 0:
                        return _orig_QLabel(self)
                    return _orig_QLabel(a[0], self)
                except Exception:
                    return _orig_QLabel(*a, **kw)

            def _make_button(*a, **kw):
                try:
                    if "parent" in kw:
                        return _orig_QPushButton(*a, **kw)
                    if len(a) > 0 and isinstance(a[0], QWidget):
                        return _orig_QPushButton(*a, **kw)
                    if len(a) == 0:
                        return _orig_QPushButton("", self)
                    return _orig_QPushButton(a[0], self)
                except Exception:
                    return _orig_QPushButton(*a, **kw)

            def _make_menu(*a, **kw):
                try:
                    if "parent" in kw:
                        return _orig_QMenu(*a, **kw)
                    if len(a) > 0 and isinstance(a[0], QWidget):
                        return _orig_QMenu(*a, **kw)
                    return _orig_QMenu(self)
                except Exception:
                    return _orig_QMenu(*a, **kw)

            def _make_groupbox(*a, **kw):
                try:
                    if "parent" in kw:
                        return _orig_QGroupBox(*a, **kw)
                    if len(a) > 0 and isinstance(a[0], QWidget):
                        return _orig_QGroupBox(*a, **kw)
                    if len(a) == 0:
                        return _orig_QGroupBox("", self)
                    return _orig_QGroupBox(a[0], self)
                except Exception:
                    return _orig_QGroupBox(*a, **kw)

            def _make_radiobutton(*a, **kw):
                try:
                    if "parent" in kw:
                        return _orig_QRadioButton(*a, **kw)
                    if len(a) > 0 and isinstance(a[0], QWidget):
                        return _orig_QRadioButton(*a, **kw)
                    if len(a) == 0:
                        return _orig_QRadioButton("", self)
                    return _orig_QRadioButton(a[0], self)
                except Exception:
                    return _orig_QRadioButton(*a, **kw)

            def _make_tabwidget(*a, **kw):
                try:
                    if "parent" in kw:
                        return _orig_QTabWidget(*a, **kw)
                    if len(a) > 0 and isinstance(a[0], QWidget):
                        return _orig_QTabWidget(*a, **kw)
                    return _orig_QTabWidget(self)
                except Exception:
                    return _orig_QTabWidget(*a, **kw)

            globals()["QLabel"] = _make_label  # type: ignore
            globals()["QPushButton"] = _make_button  # type: ignore
            globals()["QMenu"] = _make_menu  # type: ignore
            globals()["QGroupBox"] = _make_groupbox  # type: ignore
            globals()["QRadioButton"] = _make_radiobutton  # type: ignore
            globals()["QTabWidget"] = _make_tabwidget  # type: ignore
        except Exception:
            pass

        # Set professional skull icon (use central helper)
        from PyQt6.QtGui import QIcon

        pix_icon = load_logo_pixmap(128)
        if pix_icon:
            self.setWindowIcon(QIcon(pix_icon))

        # Apply dark tactical theme
        self.setStyleSheet(ReloadingTheme.get_stylesheet())

        # Opprett meny
        self.create_menu()

        # Show onboarding modal on first run
        # NOTE: avoid auto-showing the onboarding dialog at startup to prevent
        # creating a second top-level window immediately after the main window
        # is shown. The onboarding can be launched from the Help menu instead.
        try:
            from PyQt6.QtCore import QSettings

            settings = QSettings("Valkyrie", "ValkyrieBallistics")
            seen = settings.value("onboarding_seen", False)
            if not seen:
                try:
                    # Mark onboarding as seen so it won't pop up automatically.
                    # This avoids the transient second window on startup.
                    settings.setValue("onboarding_seen", True)
                except Exception:
                    pass
        except Exception:
            pass

        # Opprett status bar
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self._show_status_message("Klar")

        # Opprett sentralt widget med stacked layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.apply_global_button_style()
        # Show banner if optional dependencies are missing (matplotlib/OpenCV)
        try:
            from src.utils.optional_deps import HAS_CV2, HAS_MPL

            missing = []
            if not HAS_MPL:
                missing.append("matplotlib")
            if not HAS_CV2:
                missing.append("opencv-python")

            if missing:
                try:
                    from src.ui.disabled_feature_card import DisabledFeatureCard

                    central_layout = self.central_widget.layout()
                    card = DisabledFeatureCard(missing, parent=self)
                    if central_layout is not None and hasattr(
                        central_layout, "insertWidget"
                    ):
                        central_layout.insertWidget(0, card)
                except Exception:
                    # non-fatal: ignore UI banner failures in headless environments
                    pass
        except Exception:
            pass
        # Hovedlayout
        # Ensure at least minimal state objects exist
        if not hasattr(self, "mode_manager"):
            self.mode_manager = None
        if not hasattr(self, "state_manager"):
            self.state_manager = None

    def apply_global_button_style(self):
        # Industrial, dark, square buttons
        # Use centralized button stylesheet
        button_style = ReloadingTheme.get_button_stylesheet()
        self.setStyleSheet(self.styleSheet() + button_style)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        # Navigation bar
        nav_bar = QWidget(self.central_widget)
        # Use centralized navbar style
        nav_bar.setStyleSheet(ReloadingTheme.get_navbar_style())
        nav_layout = QHBoxLayout()
        nav_bar.setLayout(nav_layout)

        # Home button with modern project logo (small)
        self.btn_home = QPushButton("Workflow Hub", nav_bar)
        # Prefer a small logo PNG if available, otherwise fall back to tactical icon
        try:
            pix_home = load_logo_pixmap(24)
        except Exception:
            pix_home = None
        if pix_home:
            self.btn_home.setIcon(QIcon(pix_home))
        else:
            self.btn_home.setIcon(QIcon(get_window_icon_pixmap(32)))
        self.btn_home.setIconSize(QSize(24, 24))
        # Use themed selector instead of inline stylesheet
        self.btn_home.setObjectName("homeButton")
        self.btn_home.clicked.connect(self.show_workflow_hub)
        nav_layout.addWidget(self.btn_home)

        # Measurement Wizard quick-launch
        try:
            from src.ui.icon_registry import get_icon

            self.btn_measurement_wizard = QPushButton("Measurement Wizard", nav_bar)
            # Use themed selector for measurement wizard
            self.btn_measurement_wizard.setObjectName("measurementWizardButton")
            self.btn_measurement_wizard.setMinimumHeight(36)
            icon = get_icon("measurement_wizard")
            if icon:
                self.btn_measurement_wizard.setIcon(icon)
            self.btn_measurement_wizard.clicked.connect(self.open_measurement_wizard)
            nav_layout.addWidget(self.btn_measurement_wizard)
        except Exception:
            pass

        # All Tools button
        self.btn_all_tools = QPushButton("🔧 All Tools (Legacy)", nav_bar)
        # Use themed selector for all tools button
        self.btn_all_tools.setObjectName("allToolsButton")
        self.btn_all_tools.clicked.connect(self.show_all_tools)
        nav_layout.addWidget(self.btn_all_tools)

        nav_layout.addStretch()

        # Current workflow label
        self.label_current_workflow = QLabel("", nav_bar)
        # Use themed selector for current workflow label
        self.label_current_workflow.setObjectName("currentWorkflowLabel")
        nav_layout.addWidget(self.label_current_workflow)

        layout.addWidget(nav_bar)

        # Landing area: large faint logo background with big quick-action buttons
        try:
            from PyQt6.QtGui import QFont
            from PyQt6.QtWidgets import QGraphicsOpacityEffect, QSizePolicy

            pix = load_logo_pixmap(420)
            if pix:
                logo_lbl = QLabel(self.central_widget)
                logo_lbl.setPixmap(pix)
                logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo_lbl.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                try:
                    op = QGraphicsOpacityEffect(logo_lbl)
                    op.setOpacity(0.12)
                    logo_lbl.setGraphicsEffect(op)
                except Exception:
                    pass
                layout.addWidget(logo_lbl)

            # Centered big buttons overlay (stacked into main area)
            landing = QWidget(self.central_widget)
            landing_layout = QVBoxLayout()
            landing.setLayout(landing_layout)

            landing_layout.addStretch()

            def _big_btn(text, slot):
                b = QPushButton(text, landing)
                try:
                    b.setProperty("class", "landingBig")
                except Exception:
                    pass
                b.setMinimumSize(320, 90)
                try:
                    f = QFont()
                    f.setPointSize(14)
                    f.setBold(True)
                    b.setFont(f)
                except Exception:
                    pass
                try:
                    b.clicked.connect(slot)
                except Exception:
                    pass
                return b

            b_weapon = _big_btn("Våpenprofiler", self.show_weapon_profile_editor)
            b_reloading = _big_btn(
                "Reloading (Load Builder)",
                lambda: self.launch_workflow("load_development_workflow"),
            )
            b_ballistics = _big_btn(
                "Ballistics / Terrengkart", self.show_ballistics_simulator
            )

            # Arrange buttons in a vertical column centered
            btn_container = QWidget(landing)
            btn_layout = QVBoxLayout()
            btn_container.setLayout(btn_layout)
            btn_layout.setSpacing(18)
            btn_layout.addWidget(b_weapon, alignment=Qt.AlignmentFlag.AlignHCenter)
            btn_layout.addWidget(b_reloading, alignment=Qt.AlignmentFlag.AlignHCenter)
            btn_layout.addWidget(b_ballistics, alignment=Qt.AlignmentFlag.AlignHCenter)

            landing_layout.addWidget(
                btn_container, alignment=Qt.AlignmentFlag.AlignHCenter
            )
            landing_layout.addStretch()

            # Add landing page as first stacked widget so it's shown on startup
            self.stacked_widget = QStackedWidget(self.central_widget)
            self.stacked_widget.addWidget(landing)
            layout.addWidget(self.stacked_widget)
        except Exception:
            # Fallback to original simple logo + stacked widget
            pix = load_logo_pixmap(120)
            if pix:
                logo_lbl = QLabel(self.central_widget)
                logo_lbl.setPixmap(pix)
                logo_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                layout.addWidget(logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.stacked_widget = QStackedWidget(self.central_widget)
            layout.addWidget(self.stacked_widget)

    def apply_theme_from_settings(self) -> None:
        """Read saved settings and apply a matching stylesheet to the app.

        This ensures that changes made in the settings dialog are reflected
        on next startup and when apply_user_settings() is called.
        """
        try:
            from HjemmeladingApp.settings import settings as app_settings
        except Exception:
            return

        try:
            cfg = app_settings.get()
            css = _build_theme_css_from_cfg(cfg)
            # Merge with existing stylesheet so internal theme bits remain
            try:
                existing = self.styleSheet() or ""
                self.setStyleSheet(existing + "\n" + css)
            except Exception:
                self.setStyleSheet(css)
        except Exception:
            logger.exception("Error applying theme from settings")

    def _show_status_message(self, msg: str, timeout: int = 0) -> None:
        """Safely show a message in the status bar regardless of attribute/method shape."""
        sb = None
        try:
            maybe = getattr(self, "statusBar", None)
            if callable(maybe):
                sb = maybe()
            else:
                sb = maybe
        except Exception:
            sb = None
        if sb is not None:
            try:
                # Some status bars expect (str, int) while others accept only str
                sb.showMessage(msg, timeout)
            except Exception:
                try:
                    sb.showMessage(msg)
                except Exception:
                    pass

    def apply_user_settings(self):
        """Safely apply per-user settings and initialize mode/shortcuts.

        Uses archived logic but provides safe fallbacks if modules are missing.
        """
        try:
            # No local shims here — rely on module-level widget classes.

            # Try to import an application-provided UserModeManager
            try:
                from src.modules.mode_manager import UserMode, UserModeManager
            except Exception:
                try:
                    from HjemmeladingApp.utils.mode_manager import (
                        UserMode,
                        UserModeManager,
                    )
                except Exception:
                    # Provide small stub fallbacks
                    UserMode = type("UserMode", (), {"BEGINNER": 0, "EXPERT": 1})

                    class _StubSignal:
                        def __init__(self):
                            self._callbacks = []

                        def connect(self, fn):
                            self._callbacks.append(fn)

                        def emit(self, *args, **kwargs):
                            for cb in list(self._callbacks):
                                try:
                                    cb(*args, **kwargs)
                                except Exception:
                                    pass

                    class UserModeManager:
                        def __init__(self):
                            self.mode_changed = _StubSignal()
                            self._mode = UserMode.BEGINNER

                        def is_beginner(self):
                            return (
                                getattr(self, "_mode", UserMode.BEGINNER)
                                == UserMode.BEGINNER
                            )

                        def set_mode(self, mode):
                            self._mode = mode
                            try:
                                self.mode_changed.emit(mode)
                            except Exception:
                                pass

            self.mode_manager = UserModeManager()
            try:
                self._UserMode = UserMode
            except NameError:
                self._UserMode = type("UserMode", (), {"BEGINNER": 0, "EXPERT": 1})
            # Connect mode change signal if available
            try:
                self.mode_manager.mode_changed.connect(
                    getattr(self, "on_mode_changed", lambda *a, **k: None)
                )
            except Exception:
                pass

            # Initialize keyboard shortcuts manager (will be set up after UI is created)
            self.shortcuts_manager = None

            # Load language setting via QSettings and attempt to set language
            try:
                language = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                    "language", "Norsk"
                )
                lang_code = "no" if language == "Norsk" else "en"
                try:
                    # Try common places for set_language
                    try:
                        from src.i18n import set_language
                    except Exception:
                        from HjemmeladingApp.i18n import set_language
                    set_language(lang_code)
                except Exception:
                    # ignore if i18n subsystem not available at import-time
                    pass
            except Exception:
                pass

            # Finally, initialize the full UI (only once)
            try:
                if not getattr(self, "_ui_initialized", False):
                    self.init_ui()
            except Exception:
                # re-raise to be handled by caller
                raise
            # After UI is created, apply any saved user theme/settings
            try:
                self.apply_theme_from_settings()
            except Exception:
                # Do not let theme application break startup
                logger.exception("Failed to apply saved theme settings")
        except Exception:
            # Let caller handle logging and UI notification
            raise

        # Create a workspace area where dialogs/widgets can be embedded
        # This prevents code from creating new top-level windows and allows
        # show_* helpers to add widgets into a stacked area instead of
        # calling .show() which would create transient top-levels.
        try:
            from PyQt6.QtWidgets import QStackedWidget

            central_layout = None
            try:
                central_layout = self.central_widget.layout()
            except Exception:
                central_layout = None

            try:
                if central_layout is not None and hasattr(central_layout, "addWidget"):
                    self.workspace_area = QStackedWidget(self.central_widget)
                    central_layout.addWidget(self.workspace_area)
                else:
                    # Fall back to parent the workspace area on the main window
                    self.workspace_area = QStackedWidget(self)
            except Exception:
                self.workspace_area = QStackedWidget(self)
        except Exception:
            # If Qt isn't available, provide a simple stub so attribute exists
            class _StubWS:
                def addWidget(self, *_a, **_k):
                    return None

                def setCurrentWidget(self, *_a, **_k):
                    return None

            self.workspace_area = _StubWS()

        # Page 1: Workflow Hub placeholder — create the heavy hub lazily
        try:
            placeholder = QWidget(self.stacked_widget)
            placeholder.setObjectName("workflowHubPlaceholder")
            ph_layout = QVBoxLayout()
            ph_lbl = QLabel("Workflow Hub (loading on demand)", placeholder)
            ph_layout.addWidget(ph_lbl)
            placeholder.setLayout(ph_layout)
            self.stacked_widget.addWidget(placeholder)
            # Do not instantiate the real WorkflowHub now; create on-demand.
            self.workflow_hub = None
        except Exception as e:
            logger.exception("Failed to add WorkflowHub placeholder: %s", e)
            self.workflow_hub = None

        # Page 2: All Tools (legacy tabs)
        self.tabs_widget = QWidget(self.stacked_widget)
        tabs_layout = QVBoxLayout()
        self.tabs_widget.setLayout(tabs_layout)

        self.tabs = QTabWidget()
        tabs_layout.addWidget(self.tabs)

        self.stacked_widget.addWidget(self.tabs_widget)

        # Legg til tabs
        self.create_tabs()

        # Start on landing page (do not instantiate heavy hub at startup)
        try:
            self.stacked_widget.setCurrentIndex(0)
        except Exception:
            pass

    def create_menu(self):
        """Oppretter menylinjen"""
        menubar = self.menuBar()
        _tr = globals().get("tr", lambda k, **kw: k)

        # Fil-meny
        file_menu = menubar.addMenu(_tr("menu_file"))

        new_action = QAction(tr("menu_new"), self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)

        export_action = QAction(tr("menu_export"), self)
        export_action.setShortcut("Ctrl+E")
        file_menu.addAction(export_action)

        # Resume saved workflows (user-triggered)
        resume_action = QAction("Resume Saved Workflows...", self)
        resume_action.triggered.connect(self.open_resume_dialog)
        file_menu.addAction(resume_action)

        file_menu.addSeparator()

        exit_action = QAction(tr("menu_exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Verktøy-meny
        tools_menu = menubar.addMenu(tr("menu_tools"))

        calc_action = QAction("&Zero Shift Calculator", self)
        calc_action.triggered.connect(self.show_zero_shift_calculator)
        tools_menu.addAction(calc_action)

        harmonic_action = QAction("🎯 &Harmonic Wizard", self)
        harmonic_action.triggered.connect(self.show_harmonic_wizard)
        tools_menu.addAction(harmonic_action)

        simulator_action = QAction("🔬 &Ballistics Simulator", self)
        simulator_action.setShortcut("Ctrl+B")
        simulator_action.triggered.connect(self.show_ballistics_simulator)
        tools_menu.addAction(simulator_action)

        tools_menu.addSeparator()

        seating_action = QAction("&Seating Depth Calculator", self)
        tools_menu.addAction(seating_action)

        anneal_action = QAction("&Case Annealing", self)
        tools_menu.addAction(anneal_action)

        # Weapon Profiles editor (demo)
        weapon_profiles_action = QAction("Weapon Profiles...", self)
        weapon_profiles_action.triggered.connect(self.show_weapon_profile_editor)
        tools_menu.addAction(weapon_profiles_action)

        # Hjelp-meny
        help_menu = menubar.addMenu(_tr("menu_help"))

        about_action = QAction(_tr("menu_about"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        guide_action = QAction(_tr("menu_user_guide"), self)
        help_menu.addAction(guide_action)

    def create_tabs(self):
        """Oppretter alle tabs"""
        _tr = globals().get("tr", lambda k, **kw: k)

        # Lightweight lazy loader widget: defers heavy tab construction until
        # the tab is actually shown. This keeps import-time and startup fast
        # and safe for headless/CI environments.
        class LazyLoadWidget(QWidget):
            def __init__(self, factory, parent=None):
                super().__init__(parent)
                self._factory = factory
                self._loaded = False
                self._layout = None
                try:
                    self._layout = QVBoxLayout()
                    self.setLayout(self._layout)
                    self._loading_label = QLabel("Loading…", self)
                    self._layout.addWidget(self._loading_label)
                except Exception:
                    self._layout = None

                # If no parent supplied, try to attach to main window shortly
                # after construction to avoid becoming a transient top-level.
                if parent is None:
                    try:
                        from PyQt6.QtCore import QTimer
                        from PyQt6.QtWidgets import QApplication, QMainWindow

                        def _attach():
                            try:
                                app = QApplication.instance()
                                if not app:
                                    return
                                for w in app.topLevelWidgets():
                                    if isinstance(w, QMainWindow):
                                        try:
                                            self.setParent(w)
                                        except Exception:
                                            pass
                                        break
                            except Exception:
                                pass

                        QTimer.singleShot(0, _attach)
                    except Exception:
                        pass

            def _load(self):
                if self._loaded:
                    return
                self._loaded = True
                try:
                    widget = None
                    try:
                        widget = self._factory(self)
                    except TypeError:
                        try:
                            widget = self._factory(parent=self)
                        except TypeError:
                            widget = self._factory()

                    if isinstance(widget, QWidget) and self._layout is not None:
                        try:
                            widget.setParent(self)
                        except Exception:
                            pass
                        try:
                            while self._layout.count():
                                item = self._layout.takeAt(0)
                                w = item.widget()
                                if w is not None:
                                    try:
                                        w.setParent(None)
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        try:
                            self._layout.addWidget(widget)
                        except Exception:
                            pass
                    else:
                        if self._layout is not None:
                            try:
                                self._layout.addWidget(QLabel("(Loaded content)", self))
                            except Exception:
                                pass
                except Exception:
                    try:
                        logger.exception("LazyLoadWidget factory failed")
                    except Exception:
                        pass
                    if self._layout is not None:
                        try:
                            self._layout.addWidget(QLabel("Failed to load tab"))
                        except Exception:
                            pass

            def showEvent(self, ev):
                try:
                    self._load()
                except Exception:
                    pass
                try:
                    super().showEvent(ev)
                except Exception:
                    pass

        # Dashboard tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_dashboard_tab, parent=self.tabs),
            _tr("tab_dashboard"),
        )

        # Test Lab tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_test_lab_tab, parent=self.tabs),
            _tr("tab_test_lab"),
        )

        # Ammunisjon tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_ammo_tab, parent=self.tabs),
            _tr("tab_ammunition"),
        )

        # Rifles & Optikk tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_rifles_tab, parent=self.tabs), _tr("tab_rifles")
        )

        # Lager tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_inventory_tab, parent=self.tabs),
            _tr("tab_inventory"),
        )

        # Logg tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_log_tab, parent=self.tabs), _tr("tab_log")
        )

        # Analyse tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_analysis_tab, parent=self.tabs),
            _tr("tab_analysis"),
        )

        # Innstillinger tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_settings_tab, parent=self.tabs),
            _tr("tab_settings"),
        )

    def create_dashboard_tab(self):
        """Oppretter dashboard-fanen"""
        try:
            from src.modules.dashboard import Dashboard

            # Prefer passing this loader as parent to avoid creating
            # intermediate top-level widgets during module initialization.
            try:
                return Dashboard(self)
            except TypeError:
                try:
                    return Dashboard(parent=self)
                except TypeError:
                    return Dashboard()
        except Exception as e:
            logger.exception("Failed to import Dashboard: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Dashboard unavailable", w))
            w.setLayout(layout)
            return w

    def create_test_lab_tab(self):
        """Oppretter test lab-fanen"""
        try:
            from src.modules.ladder_test_lab import LadderTestLab

            try:
                return LadderTestLab(self)
            except TypeError:
                try:
                    return LadderTestLab(parent=self)
                except TypeError:
                    return LadderTestLab()
        except Exception as e:
            logger.exception("Failed to import LadderTestLab: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Test Lab unavailable", w))
            w.setLayout(layout)
            return w

    def create_ammo_tab(self):
        """Oppretter ammunisjon-fanen"""
        try:
            from src.modules.ammo_profile_manager import AmmoProfileManager

            try:
                return AmmoProfileManager(self)
            except TypeError:
                try:
                    return AmmoProfileManager(parent=self)
                except TypeError:
                    return AmmoProfileManager()
        except Exception as e:
            logger.exception("Failed to import AmmoProfileManager: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Ammunisjon unavailable", w))
            w.setLayout(layout)
            return w

    def create_rifles_tab(self):
        """Oppretter rifles & optikk-fanen"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Tabs for rifle management
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Rifle Database Manager (NEW - COMPREHENSIVE)
        try:
            from src.modules.rifle_database_manager import RifleDatabaseManager

            try:
                tabs.addTab(RifleDatabaseManager(self), "🎯 Våpen Database")
            except TypeError:
                try:
                    tabs.addTab(RifleDatabaseManager(parent=self), "🎯 Våpen Database")
                except TypeError:
                    tabs.addTab(RifleDatabaseManager(), "🎯 Våpen Database")
        except Exception as e:
            logger.exception("RifleDatabaseManager import failed: %s", e)

        # Tab 2: Rifle & Optic Manager (Legacy)
        try:
            from src.modules.rifle_optic_manager import RifleOpticManager

            try:
                tabs.addTab(RifleOpticManager(self), "🔭 Rifle & Optikk")
            except TypeError:
                try:
                    tabs.addTab(RifleOpticManager(parent=self), "🔭 Rifle & Optikk")
                except TypeError:
                    tabs.addTab(RifleOpticManager(), "🔭 Rifle & Optikk")
        except Exception as e:
            logger.exception("RifleOpticManager import failed: %s", e)

        # Tab 3: Rifle Performance Tracker
        try:
            from src.modules.rifle_performance_tracker import RiflePerformanceTracker

            try:
                tabs.addTab(RiflePerformanceTracker(self), "📈 Performance")
            except TypeError:
                try:
                    tabs.addTab(RiflePerformanceTracker(parent=self), "📈 Performance")
                except TypeError:
                    tabs.addTab(RiflePerformanceTracker(), "📈 Performance")
        except Exception as e:
            logger.exception("RiflePerformanceTracker import failed: %s", e)

        return widget

    def create_inventory_tab(self):
        """Oppretter lager-fanen"""
        try:
            from src.modules.inventory_manager import InventoryManager

            try:
                return InventoryManager(self)
            except TypeError:
                try:
                    return InventoryManager(parent=self)
                except TypeError:
                    return InventoryManager()
        except Exception as e:
            logger.exception("InventoryManager import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Inventory unavailable", w))
            w.setLayout(layout)
            return w

    def create_log_tab(self):
        """Oppretter logg-fanen"""
        try:
            from src.modules.session_logger import SessionLogger

            try:
                return SessionLogger(self)
            except TypeError:
                try:
                    return SessionLogger(parent=self)
                except TypeError:
                    return SessionLogger()
        except Exception as e:
            logger.exception("SessionLogger import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Log unavailable", w))
            w.setLayout(layout)
            return w

    def create_analysis_tab(self):
        """Oppretter analyse-fanen"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Tabs for ulike analyser
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Target Analyzer
        try:
            from src.modules.target_analyzer import TargetAnalyzer

            try:
                tabs.addTab(TargetAnalyzer(self), "📷 Target Analyzer")
            except TypeError:
                try:
                    tabs.addTab(TargetAnalyzer(parent=self), "📷 Target Analyzer")
                except TypeError:
                    tabs.addTab(TargetAnalyzer(), "📷 Target Analyzer")
        except Exception as e:
            logger.exception("TargetAnalyzer import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Target Analyzer unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "📷 Target Analyzer")

        # Tab 2: Precision Tracker
        try:
            from src.modules.precision_tracker import PrecisionTracker

            try:
                tabs.addTab(PrecisionTracker(self), "📊 Precision Tracker")
            except TypeError:
                try:
                    tabs.addTab(PrecisionTracker(parent=self), "📊 Precision Tracker")
                except TypeError:
                    tabs.addTab(PrecisionTracker(), "📊 Precision Tracker")
        except Exception as e:
            logger.exception("PrecisionTracker import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Precision Tracker unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "📊 Precision Tracker")

        # Tab 3: Safety Dashboard
        try:
            from src.modules.safety_dashboard import SafetyDashboard

            try:
                tabs.addTab(SafetyDashboard(self), "⚠️ Sikkerhet")
            except TypeError:
                try:
                    tabs.addTab(SafetyDashboard(parent=self), "⚠️ Sikkerhet")
                except TypeError:
                    tabs.addTab(SafetyDashboard(), "⚠️ Sikkerhet")
        except Exception as e:
            logger.exception("SafetyDashboard import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Safety Dashboard unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "⚠️ Sikkerhet")

        # Tab 4: Terrain Map (imported with try/except to avoid circular import failures)
        try:
            from src.modules.terrain_map import TerrainMapViewer

            viewer = TerrainMapViewer()
            is_qwidget = False
            try:
                is_qwidget = isinstance(viewer, QWidget)
            except Exception:
                is_qwidget = False

            if is_qwidget:
                tabs.addTab(viewer, "🗺️ Terrengkart")
            else:
                # Wrap non-Qt viewer objects in a lightweight QWidget so
                # QTabWidget.addTab() does not raise a TypeError in headless
                # or baseline import-safe implementations.
                wrap = QWidget()
                wrap_layout = QVBoxLayout()
                wrap.setLayout(wrap_layout)
                try:
                    # If the viewer exposes a Qt widget (e.g. map_view), embed it.
                    mv = getattr(viewer, "map_view", None)
                    if mv is not None and isinstance(mv, QWidget):
                        wrap_layout.addWidget(mv)
                    else:
                        wrap_layout.addWidget(QLabel("TerrainMapViewer (wrapped)"))
                except Exception:
                    wrap_layout.addWidget(QLabel("TerrainMapViewer (wrapped)"))
                tabs.addTab(wrap, "🗺️ Terrengkart")
        except Exception as e:
            logger.exception("Feil ved import av TerrainMapViewer: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Terrain Map unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "🗺️ Terrengkart")

        # Tab 5: Environmental Logger
        try:
            from src.modules.environmental_logger import EnvironmentalLogger

            try:
                tabs.addTab(EnvironmentalLogger(self), "🌡️ Værdata")
            except TypeError:
                try:
                    tabs.addTab(EnvironmentalLogger(parent=self), "🌡️ Værdata")
                except TypeError:
                    tabs.addTab(EnvironmentalLogger(), "🌡️ Værdata")
        except Exception as e:
            logger.exception("EnvironmentalLogger import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Environmental Logger unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "🌡️ Værdata")

        # Tab 6: Drop Chart & Wind
        try:
            from src.modules.drop_chart_generator import DropChartGenerator

            try:
                tabs.addTab(DropChartGenerator(self), "📊 Drop/Wind")
            except TypeError:
                try:
                    tabs.addTab(DropChartGenerator(parent=self), "📊 Drop/Wind")
                except TypeError:
                    tabs.addTab(DropChartGenerator(), "📊 Drop/Wind")
        except Exception as e:
            logger.exception("DropChartGenerator import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Drop Chart Generator unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "📊 Drop/Wind")

        # Tab 7: Rifle Performance (Cold Bore & Barrel)
        try:
            from src.modules.rifle_performance_tracker import RiflePerformanceTracker

            try:
                tabs.addTab(RiflePerformanceTracker(self), "🎯 Rifle Performance")
            except TypeError:
                try:
                    tabs.addTab(
                        RiflePerformanceTracker(parent=self), "🎯 Rifle Performance"
                    )
                except TypeError:
                    tabs.addTab(RiflePerformanceTracker(), "🎯 Rifle Performance")
        except Exception as e:
            logger.exception("RiflePerformanceTracker import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Rifle Performance unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "🎯 Rifle Performance")

        # Tab 8: Chronograph Import
        try:
            from src.modules.chronograph_importer import ChronographImporter

            try:
                tabs.addTab(ChronographImporter(self), "📊 Chronograph")
            except TypeError:
                try:
                    tabs.addTab(ChronographImporter(parent=self), "📊 Chronograph")
                except TypeError:
                    tabs.addTab(ChronographImporter(), "📊 Chronograph")
        except Exception as e:
            logger.exception("ChronographImporter import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Chronograph Import unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "📊 Chronograph")

        # Tab 9: GRT Import
        try:
            from src.modules.grt_importer import GRTImporter

            try:
                tabs.addTab(GRTImporter(self), "📦 GRT Import")
            except TypeError:
                try:
                    tabs.addTab(GRTImporter(parent=self), "📦 GRT Import")
                except TypeError:
                    tabs.addTab(GRTImporter(), "📦 GRT Import")
        except Exception as e:
            logger.exception("GRTImporter import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("GRT Import unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "📦 GRT Import")

        # Tab 10: GRT Integrasjon
        try:
            from src.modules.grt_integration import GRTIntegration

            try:
                tabs.addTab(GRTIntegration(self), "🔗 GRT Integrasjon")
            except TypeError:
                try:
                    tabs.addTab(GRTIntegration(parent=self), "🔗 GRT Integrasjon")
                except TypeError:
                    tabs.addTab(GRTIntegration(), "🔗 GRT Integrasjon")
        except Exception as e:
            logger.exception("GRTIntegration import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("GRT Integration unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "🔗 GRT Integrasjon")

        # Tab 11: Temperature Ladder Test
        try:
            from src.modules.temperature_ladder_test import TemperatureLadderTest

            try:
                tabs.addTab(TemperatureLadderTest(self), "🌡️ Temp Test")
            except TypeError:
                try:
                    tabs.addTab(TemperatureLadderTest(parent=self), "🌡️ Temp Test")
                except TypeError:
                    tabs.addTab(TemperatureLadderTest(), "🌡️ Temp Test")
        except Exception as e:
            logger.exception("TemperatureLadderTest import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Temperature Ladder Test unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "🌡️ Temp Test")

        # Tab 12: Component Lot Tracker
        try:
            from src.modules.component_lot_tracker import ComponentLotTracker

            tabs.addTab(ComponentLotTracker(), "🏷️ Lot Tracker")
        except Exception as e:
            logger.exception("ComponentLotTracker import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Component Lot Tracker unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "🏷️ Lot Tracker")

        # Tab 13: Batch QC Dashboard
        try:
            from src.modules.batch_qc_dashboard import BatchQCDashboard

            tabs.addTab(BatchQCDashboard(), "🎯 Batch QC")
        except Exception as e:
            logger.exception("BatchQCDashboard import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Batch QC unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "🎯 Batch QC")

        # Tab 14: SAAMI/CIP Compliance
        try:
            from src.modules.saami_compliance_checker import SAAMIComplianceChecker

            tabs.addTab(SAAMIComplianceChecker(), "✅ SAAMI/CIP")
        except Exception as e:
            logger.exception("SAAMIComplianceChecker import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("SAAMI/CIP Checker unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "✅ SAAMI/CIP")

        # Tab 15: Real-Time Ballistics Simulator
        try:
            from src.modules.ballistics_simulator import BallisticsSimulator

            tabs.addTab(BallisticsSimulator(), "🔬 Ballistics Simulator")
        except Exception as e:
            logger.exception("BallisticsSimulator import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Ballistics Simulator unavailable"))
            w.setLayout(layout)
            tabs.addTab(w, "🔬 Ballistics Simulator")

        # Tab 4: Statistikk (placeholder)
        stats_widget = QWidget()
        stats_layout = QVBoxLayout()
        stats_widget.setLayout(stats_layout)

        stats_title = QLabel("📊 Statistikk & Trender")
        try:
            from PyQt6.QtGui import QFont

            stats_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        except Exception:
            # If QFont isn't available for some reason, skip setting the custom font
            pass
        stats_layout.addWidget(stats_title)

        stats_info = QLabel(
            """
        <h3>Kommende funksjoner:</h3>
        <ul>
            <li>Presisjons-utvikling over tid</li>
            <li>Kostnadsanalyse per patron</li>
            <li>Sammenligning av ladninger</li>
            <li>Mest brukte komponenter</li>
        </ul>
        """
        )
        stats_layout.addWidget(stats_info)
        stats_layout.addStretch()

        tabs.addTab(stats_widget, "📊 Statistikk")

        return widget

    def create_settings_tab(self):
        """Oppretter innstillinger-fanen"""
        try:
            from src.modules.settings import SettingsWidget

            return SettingsWidget()
        except Exception as e:
            logger.exception("SettingsWidget import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Settings unavailable"))
            w.setLayout(layout)
            return w

    def show_about(self):
        """Viser 'Om programmet' dialog"""
        QMessageBox.about(
            self,
            "Om Reloading Workshop Manager",
            """<h2>Reloading Workshop Manager</h2>
            <p><b>Versjon:</b> 1.0.0 Beta</p>
            <p><b>Beskrivelse:</b> Avansert verktøy for hjemmelading av ammunisjon</p>

            <h3>Funksjoner:</h3>
            <ul>
                <li>Zero Shift Calculator</li>
                <li>Ladder Test Analyse</li>
                <li>Presisjonsanalyse</li>
                <li>Settedybde-optimalisering</li>
                <li>Hylse-gløding</li>
                <li>Lagermodul</li>
                <li>Statistikk og rapporter</li>
            </ul>

            <p><b>⚠️ Viktig sikkerhetsinformasjon:</b></p>
            <p>Dette programmet er et hjelpemiddel. Bruk alltid anerkjente
            laste-manualer og følg sikkerhetsprosedyrer. Start lavt, gå sakte!</p>

            <p><i>Utviklet for reloading-entusiaster</i></p>
            """,
        )

    def show_zero_shift_calculator(self):
        """Viser Zero Shift Calculator som en ny tab"""
        # Sjekk om tab allerede eksisterer
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "🎯 Zero Shift":
                self.tabs.setCurrentIndex(i)
                return

        # Opprett ny tab
        try:
            from src.modules.zero_shift_calculator import ZeroShiftCalculator

            zero_shift_widget = ZeroShiftCalculator()
            self.tabs.addTab(zero_shift_widget, "🎯 Zero Shift")
            self.tabs.setCurrentWidget(zero_shift_widget)
        except Exception as e:
            logger.exception("ZeroShiftCalculator import failed: %s", e)
            QMessageBox.warning(
                self,
                "Unavailable",
                "Zero Shift Calculator unavailable (see debug_err.log in %LOCALAPPDATA%\\Hjemmelading\\logs)",
            )

    def show_harmonic_wizard(self):
        """Viser Harmonic Wizard som en ny tab"""
        from src.modules.harmonic_wizard import HarmonicWizard

        # Sjekk om tab allerede eksisterer
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "🎯 Harmonic Wizard":
                self.tabs.setCurrentIndex(i)
                return

        # Opprett ny tab
        harmonic_widget = HarmonicWizard()
        self.tabs.addTab(harmonic_widget, "🎯 Harmonic Wizard")
        self.tabs.setCurrentWidget(harmonic_widget)

    def show_workflow_hub(self):
        """Show workflow hub landing page (lazy init).

        Instantiate `WorkflowHub` on first request to avoid heavy UI
        construction during MainWindow.__init__ and prevent transient
        top-level windows at startup.
        """
        try:
            # Lazy-create the WorkflowHub and parent it to the main window so
            # created widgets are not top-levels. Prefer the newer signature
            # that accepts `defer_ui=True` to avoid immediate heavy init.
            if getattr(self, "workflow_hub", None) is None:
                try:
                    from src.modules.workflow_hub import WorkflowHub

                    try:
                        self.workflow_hub = WorkflowHub(
                            self.state_manager,
                            self.mode_manager,
                            parent=self,
                            defer_ui=True,
                        )
                    except TypeError:
                        # Fallback if older ctor signature doesn't accept defer_ui
                        try:
                            self.workflow_hub = WorkflowHub(
                                self.state_manager, self.mode_manager, parent=self
                            )
                        except TypeError:
                            # Last resort: no args
                            self.workflow_hub = WorkflowHub()

                    try:
                        self.workflow_hub.workflow_selected.connect(
                            self.launch_workflow
                        )
                    except Exception:
                        pass

                    try:
                        self.stacked_widget.addWidget(self.workflow_hub)
                    except Exception:
                        pass
                except Exception as e:
                    logger.exception("WorkflowHub import/creation failed: %s", e)
                    self._show_status_message("Kunne ikke laste Workflow Hub")
                    return

            # Ensure the deferred UI is created now that the user explicitly
            # requested it (no-op if already initialized).
            try:
                if getattr(self.workflow_hub, "ensure_ui", None):
                    self.workflow_hub.ensure_ui()
            except Exception:
                pass

            # Show the hub in the stacked widget
            try:
                self.stacked_widget.setCurrentWidget(self.workflow_hub)
            except Exception:
                try:
                    idx = self.stacked_widget.indexOf(self.workflow_hub)
                    if idx != -1:
                        self.stacked_widget.setCurrentIndex(idx)
                    else:
                        self.stacked_widget.setCurrentIndex(0)
                except Exception:
                    self.stacked_widget.setCurrentIndex(0)

            self.label_current_workflow.setText("Workflow Hub")
            try:
                self._show_status_message("Workflow Hub - Velg hva du vil gjøre")
            except Exception:
                pass
        except Exception as e:
            logger.exception("Failed to show WorkflowHub: %s", e)

    def show_all_tools(self):
        """Show all tools (legacy tab view)"""
        self.stacked_widget.setCurrentIndex(1)
        self.label_current_workflow.setText("📋 All Tools")
        self.statusBar.showMessage("Legacy view - Alle verktøy")

    def launch_workflow(self, workflow_id: str):
        """Launch specific workflow"""
        workflow_map = {
            "ocw_test": ("OCW Test", 3),
            "ladder_test": ("Ladder Test", 4),
            "seating_depth": ("Seating Depth", 5),
            "smart_wizard": ("Smart Loading Wizard", None),
            "temperature_test": ("Temperature Test", 11),
            "saami_compliance": ("SAAMI/CIP", 14),
            "chronograph_import": ("Chronograph Import", 7),
            "cold_bore": ("Cold Bore Logger", 6),
            "batch_qc": ("Batch QC", 13),
            "lot_tracker": ("Lot Tracker", 12),
            "drop_chart": ("Drop Chart", None),
            "wind_drift": ("Wind Drift", None),
            "zero_shift": ("Zero Shift", None),
            "rifle_setup": ("Rifle Manager", 1),
            "grt_import": ("GRT Import", 9),
            "component_database": ("Component Database", 2),
            "component_inventory": ("Component Inventory", 12),
            "primer_tools": ("Primer Tools", None),
            "load_wizard": ("Load Development Wizard", None),
            # Komponenter
            "brass_manager": ("Brass/Hylse Manager", None),
            "bullet_manager": ("Bullet Manager", None),
            "powder_manager": ("Powder Manager", None),
            "primer_manager": ("Primer Manager", None),
            # Rifles & Utstyr
            "rifle_optic_manager": ("Rifles & Optikk", None),
            "ammo_profile_manager": ("Ammunisjonsprofiler", None),
            "rifle_performance": ("Rifle Performance", None),
            # Testing & Analyse
            "precision_tracker": ("Precision Tracker", None),
            "target_analyzer": ("Target Analyzer", None),
            # Tools
            "saami_checker": ("SAAMI/CIP Checker", None),
            "grt_integration": ("GRT Integration", None),
            "safety_dashboard": ("Safety Dashboard", None),
            # Load Development Workflow
            "load_development_workflow": ("Load Development Workflow", None),
        }

        if workflow_id not in workflow_map:
            self._show_status_message(f"Workflow '{workflow_id}' not implemented yet")
            return

        workflow_name, tab_idx = workflow_map[workflow_id]

        # Handle special cases
        if workflow_id == "smart_wizard":
            self.launch_smart_wizard()
            return

        if workflow_id == "zero_shift":
            self.show_zero_shift_calculator()
            return

        if workflow_id == "primer_tools":
            self.show_primer_tools()
            return

        if workflow_id == "modern_load_builder":
            self.show_modern_load_builder()
            return

        if workflow_id == "load_wizard":
            self.show_load_wizard()
            return

        if workflow_id == "load_development_workflow":
            self.show_load_development_workflow()
            return

        # Komponenter
        if workflow_id == "brass_manager":
            self.show_brass_manager()
            return

        if workflow_id == "rifle_optic_manager":
            self.show_rifle_optic_manager()
            return

        if workflow_id == "ammo_profile_manager":
            self.show_ammo_profile_manager()
            return

        if workflow_id == "rifle_performance":
            self.show_rifle_performance()
            return

        if workflow_id == "precision_tracker":
            self.show_precision_tracker()
            return

        if workflow_id == "target_analyzer":
            self.show_target_analyzer()
            return

        if workflow_id == "saami_checker":
            self.show_saami_checker()
            return

        if workflow_id == "grt_integration":
            self.show_grt_integration()
            return

        if workflow_id == "safety_dashboard":
            self.show_safety_dashboard()
            return

        if workflow_id == "drop_chart":
            self.show_drop_chart()
            return

        # Switch to tabs view and select workflow tab
        if tab_idx is not None:
            self.stacked_widget.setCurrentIndex(1)
            self.tabs.setCurrentIndex(tab_idx)
            self.label_current_workflow.setText(f"📍 {workflow_name}")
            self._show_status_message(f"Active workflow: {workflow_name}")

            # Mark as active in hub
            self.workflow_hub.mark_workflow_active(workflow_id, workflow_name)
        else:
            self._show_status_message(f"'{workflow_name}' coming soon!")

    def launch_smart_wizard(self):
        """Launch Smart Loading Wizard"""
        from src.modules.smart_loading_wizard import SmartLoadingWizard

        wizard = SmartLoadingWizard(self)
        if wizard.exec():
            # Wizard completed
            self.statusBar.showMessage("Smart Loading Wizard completed!")
            self.workflow_hub.mark_workflow_completed("smart_wizard")
        else:
            # Wizard cancelled
            self.statusBar.showMessage("Smart Loading Wizard cancelled")

    def check_saved_workflows(self):
        """Check for saved workflows on startup"""
        # Guard against uninitialized state_manager during deferred startup
        if not hasattr(self, "state_manager") or self.state_manager is None:
            return

        active_states = self.state_manager.get_all_active()
        # If there are saved workflows, record that fact but do NOT auto-show
        # a separate modal at startup. Users can open the resume dialog from
        # the File menu (Resume Saved Workflows...) to avoid a transient
        # second top-level window.
        try:
            if active_states:
                self._saved_workflows_available = True
                self._saved_states_preview = active_states
                try:
                    self.statusBar.showMessage(
                        f"{len(active_states)} saved workflow(s) available — File → Resume Saved Workflows..."
                    )
                except Exception:
                    pass
            else:
                self._saved_workflows_available = False
                self._saved_states_preview = []
        except Exception:
            self._saved_workflows_available = False
            self._saved_states_preview = []

    def resume_workflow(self, workflow_id: str):
        """Resume a saved workflow"""
        state = self.state_manager.get_state(workflow_id)
        if not state:
            return

        # Try to launch the workflow and notify the user
        try:
            self.launch_workflow(workflow_id)
            self._show_status_message(f"Resumed workflow: {state.workflow_name}")
            QMessageBox.information(
                self,
                "Workflow Resumed",
                f"✅ {state.workflow_name} resumed!\n\nYour previous progress has been restored.",
            )
        except Exception as e:
            logger.exception("Failed to resume workflow %s: %s", workflow_id, e)
            QMessageBox.warning(
                self,
                "Resume Failed",
                "Could not resume workflow (see debug_err.log in %LOCALAPPDATA%\\Hjemmelading\\logs)",
            )

    def open_resume_dialog(self):
        """User-invoked: open the resume dialog if saved workflows exist."""
        try:
            if not getattr(self, "_saved_workflows_available", False):
                QMessageBox.information(
                    self,
                    "No Saved Workflows",
                    "There are no saved workflows to resume.",
                )
                return
            from src.modules.workflow_resume_dialog import WorkflowResumeDialog

            dialog = WorkflowResumeDialog(self.state_manager, self)
            dialog.workflow_selected.connect(self.resume_workflow)
            _run_modal(dialog)
        except Exception as e:
            logger.exception("Failed to open resume dialog: %s", e)
            try:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Kunne ikke åpne Resume dialog (se logg).",
                )
            except Exception:
                pass

    def show_weapon_profile_editor(self):
        """Open the Weapon Profile Editor dialog (loads/saves JSON)."""
        try:
            from pathlib import Path

            from src.ui.weapon_profile_editor import WeaponProfileEditor

            dlg = WeaponProfileEditor(
                data_path=Path("data/demo_weapons.json"), parent=self
            )
            dlg.exec()
        except Exception as e:
            logger.exception("WeaponProfileEditor failed to open: %s", e)
            QMessageBox.warning(
                self,
                "Unavailable",
                "Weapon Profile Editor unavailable (see debug_err.log in %LOCALAPPDATA%\\Hjemmelading\\logs)",
            )

    def on_mode_changed(self, new_mode: str):
        """Handle user mode change"""
        _um = getattr(self, "_UserMode", None)
        if _um is None:
            beginner_val = 0
        else:
            beginner_val = getattr(_um, "BEGINNER", 0)

        mode_name = "🔰 Beginner" if new_mode == beginner_val else "⚡ Expert"

        self._show_status_message(f"Mode changed to: {mode_name}")

        # Show notification
        config = self.mode_manager.get_ui_config()

        if config["confirmation_dialogs"]:
            features = []
            if config["show_tooltips"]:
                features.append("✅ Tooltips enabled")
            else:
                features.append("❌ Tooltips disabled")

            if config["enable_shortcuts"]:
                features.append("⌨️ Keyboard shortcuts enabled")
            else:
                features.append("⌨️ Keyboard shortcuts disabled")

            if config["wizard_mode"]:
                features.append("🧙 Wizard mode enabled")
            else:
                features.append("🧙 Wizard mode disabled")

            QMessageBox.information(
                self,
                "Mode Changed",
                f"User mode changed to: {mode_name}\n\n" + "\n".join(features),
            )

    def show_primer_tools(self):
        """Show primer tools dialog"""
        from src.modules.primer_tools import PrimerToolsHub

        try:
            dialog = PrimerToolsHub(self)
        except TypeError:
            try:
                dialog = PrimerToolsHub(parent=self)
            except TypeError:
                dialog = PrimerToolsHub()
        dialog.setWindowTitle("🔥 Primer Selection & Analysis Tools")
        dialog.resize(1000, 600)
        dialog.show()

    def show_load_wizard(self):
        """Show complete load development wizard with professional batch management"""
        from src.modules.load_development_wizard import LoadDevelopmentWizard

        wizard = LoadDevelopmentWizard(self)

        # Connect batch creation signal to refresh UI
        def on_batches_created(batch_ids):
            """Handle successful batch creation"""
            self.statusBar.showMessage(
                f"✅ {len(batch_ids)} batches created successfully!"
            )
            # Refresh any relevant tables/views if needed
            if hasattr(self, "loaded_ammo_view"):
                self.loaded_ammo_view.refresh()

        wizard.batch_created.connect(on_batches_created)

        if wizard.exec():
            num_batches = len(wizard.created_batches) if wizard.created_batches else 0
            if num_batches > 0:
                QMessageBox.information(
                    self,
                    "Load Development Batches Created",
                    f"✅ {num_batches} test batches created successfully!\n\n"
                    f"Batch numbers: {', '.join([f'LAB-{i:03d}' for i in range(1, num_batches+1)])}\n\n"
                    "Neste steg:\n"
                    "1. Load the batches according to the test protocol\n"
                    "2. Perform QC measurements (powder charge, CBTO, runout)\n"
                    "3. Test at the range and record accuracy data\n"
                    "4. Analyze results to find optimal load",
                )
            else:
                self.statusBar.showMessage("Wizard cancelled or no batches created")
        else:
            self.statusBar.showMessage("Load development wizard cancelled")

    def show_brass_manager(self):
        """Show brass/case lifecycle manager"""
        dialog = QWidget(self)
        dialog.setWindowTitle("🥉 Brass/Hylse Manager")
        dialog.resize(1400, 900)
        layout = QVBoxLayout()
        try:
            from src.modules.brass_manager import BrassManager

            try:
                manager = BrassManager(self)
            except TypeError:
                try:
                    manager = BrassManager(parent=self)
                except TypeError:
                    manager = BrassManager()
            layout.addWidget(manager)
        except Exception as e:
            logger.exception("BrassManager import failed: %s", e)
            layout.addWidget(QLabel("Brass manager unavailable"))
        dialog.setLayout(layout)

        # Add to workspace area
        self.workspace_area.addWidget(dialog)
        self.workspace_area.setCurrentWidget(dialog)

        # Update workflow state
        if self.workflow_hub:
            try:
                self.workflow_hub.mark_workflow_active(
                    "brass_manager", "Brass/Hylse Manager"
                )
            except Exception:
                pass
        self.statusBar.showMessage("🥉 Brass lifecycle tracking aktivert")

    def show_rifle_optic_manager(self):
        """Show rifles and optics manager"""
        dialog = QWidget(self)
        dialog.setWindowTitle("🎯 Rifles & Optikk")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.rifle_optic_manager import RifleOpticManager

            try:
                manager = RifleOpticManager(self)
            except TypeError:
                try:
                    manager = RifleOpticManager(parent=self)
                except TypeError:
                    manager = RifleOpticManager()
            layout.addWidget(manager)
        except Exception as e:
            logger.exception("RifleOpticManager import failed: %s", e)
            layout.addWidget(QLabel("Rifle & Optic Manager unavailable", dialog))
        dialog.setLayout(layout)
        # Add to workspace area instead of showing as a separate top-level window
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self.statusBar.showMessage("📍 Rifles & Optikk Manager")

    def show_ammo_profile_manager(self):
        """Show ammo profiles manager"""
        dialog = QWidget(self)
        dialog.setWindowTitle("📦 Ammunisjonsprofiler")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.ammo_profile_manager import AmmoProfileManager

            try:
                manager = AmmoProfileManager(self)
            except TypeError:
                try:
                    manager = AmmoProfileManager(parent=self)
                except TypeError:
                    manager = AmmoProfileManager()
            layout.addWidget(manager)
        except Exception as e:
            logger.exception("AmmoProfileManager import failed: %s", e)
            layout.addWidget(QLabel("Ammo Profile Manager unavailable", dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self.statusBar.showMessage("📍 Ammunisjonsprofil Manager")

    def show_rifle_performance(self):
        """Show rifle performance tracker"""
        dialog = QWidget(self)
        dialog.setWindowTitle("📊 Rifle Performance Tracker")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.rifle_performance_tracker import RiflePerformanceTracker

            try:
                tracker = RiflePerformanceTracker(self)
            except TypeError:
                try:
                    tracker = RiflePerformanceTracker(parent=self)
                except TypeError:
                    tracker = RiflePerformanceTracker()
            layout.addWidget(tracker)
        except Exception as e:
            logger.exception("RiflePerformanceTracker import failed: %s", e)
            layout.addWidget(QLabel("Rifle Performance Tracker unavailable", dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self.statusBar.showMessage("📍 Rifle Performance Tracker")

    def show_ballistics_simulator(self):
        """Show real-time ballistics simulator"""
        from src.modules.ballistics_simulator import BallisticsSimulator

        dialog = QWidget(self)
        dialog.setWindowTitle("🔬 Real-Time Ballistics Simulator")
        dialog.resize(1600, 1000)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        try:
            simulator = BallisticsSimulator(self)
        except TypeError:
            try:
                simulator = BallisticsSimulator(parent=self)
            except TypeError:
                simulator = BallisticsSimulator()
        layout.addWidget(simulator)

        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self.statusBar.showMessage(
            "🔬 Ballistics Simulator - Physics-based load prediction"
        )

    def show_precision_tracker(self):
        """Show precision tracker"""
        dialog = QWidget(self)
        dialog.setWindowTitle("🎯 Precision Tracker")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.precision_tracker import PrecisionTracker

            try:
                tracker = PrecisionTracker(self)
            except TypeError:
                try:
                    tracker = PrecisionTracker(parent=self)
                except TypeError:
                    tracker = PrecisionTracker()
            layout.addWidget(tracker)
        except Exception as e:
            logger.exception("PrecisionTracker import failed: %s", e)
            layout.addWidget(QLabel("Precision Tracker unavailable", dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self.statusBar.showMessage("📍 Precision Tracker")

    def show_target_analyzer(self):
        """Show target analyzer"""
        dialog = QWidget(self)
        dialog.setWindowTitle("📸 Target Analyzer")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.target_analyzer import TargetAnalyzer

            try:
                analyzer = TargetAnalyzer(self)
            except TypeError:
                try:
                    analyzer = TargetAnalyzer(parent=self)
                except TypeError:
                    analyzer = TargetAnalyzer()
            layout.addWidget(analyzer)
        except Exception as e:
            logger.exception("TargetAnalyzer import failed: %s", e)
            layout.addWidget(QLabel("Target Analyzer unavailable", dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self.statusBar.showMessage("📍 Target Analyzer")

    def show_load_development_workflow(self):
        """Show comprehensive load development workflow manager"""
        try:
            from PyQt6.QtWidgets import QDialog, QMessageBox

            from src.modules.load_development_workflow import LoadDevelopmentWorkflow

            self.statusBar.showMessage("🎯 Loading Workflow Manager...")

            dialog = QDialog(self)
            dialog.setWindowTitle("🎯 Load Development Workflow Manager")
            dialog.setWindowIcon(self.windowIcon())
            dialog.resize(1400, 900)
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)

            try:
                try:
                    workflow = LoadDevelopmentWorkflow(self)
                except TypeError:
                    try:
                        workflow = LoadDevelopmentWorkflow(parent=self)
                    except TypeError:
                        workflow = LoadDevelopmentWorkflow()
                layout.addWidget(workflow)
                dialog.setLayout(layout)
                self.statusBar.showMessage(
                    "🎯 Load Development Workflow - Complete lifecycle management"
                )
                result = dialog.exec()
                if result == 0:
                    QMessageBox.information(
                        self,
                        "Workflow ikke åpnet",
                        "Workflow-dialogen ble ikke åpnet eller ble lukket umiddelbart.",
                    )
                    self.statusBar.showMessage("❌ Workflow-dialogen ble ikke åpnet.")
            except Exception as inner_e:
                error_msg = (
                    f"Failed to initialize LoadDevelopmentWorkflow:\n\n{str(inner_e)}"
                )
                logger.exception(
                    "Failed to initialize LoadDevelopmentWorkflow: %s", inner_e
                )
                QMessageBox.critical(self, "Error", error_msg)
                import traceback

                logger.debug(traceback.format_exc())
                self.statusBar.showMessage(f"❌ Error: {str(inner_e)}")

        except Exception as e:
            error_msg = f"Failed to open Load Development Workflow dialog:\n\n{str(e)}"
            logger.exception("%s", error_msg)
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", error_msg)
            import traceback

            logger.debug(traceback.format_exc())
            self.statusBar.showMessage(f"❌ Error: {str(e)}")

    def show_modern_load_builder(self):
        """Show modern interactive load builder with AI"""
        logger.info("NEW LOAD (Tactical) button clicked!")
        try:
            logger.info("Importing ModernLoadBuilder...")
            from PyQt6.QtWidgets import QDialog

            from src.modules.modern_load_builder import ModernLoadBuilder

            logger.info("Import successful, creating dialog...")
            self.statusBar.showMessage("⚡ Loading Tactical Load Builder...")

            dialog = QDialog(self)
            dialog.setWindowTitle("⚡ TACTICAL LOAD BUILDER - AI Powered")
            dialog.setWindowIcon(self.windowIcon())
            dialog.resize(1600, 1000)
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)

            logger.info("Creating ModernLoadBuilder widget...")
            try:
                builder = ModernLoadBuilder(self)
            except TypeError:
                try:
                    builder = ModernLoadBuilder(parent=self)
                except TypeError:
                    builder = ModernLoadBuilder()
            layout.addWidget(builder)

            dialog.setLayout(layout)
            logger.info("Opening dialog...")
            self.statusBar.showMessage("⚡ Tactical Load Builder - AI assistant ready")
            dialog.exec()
            logger.info("Dialog closed successfully")

        except Exception as e:
            error_msg = f"Failed to open Modern Load Builder:\n\n{str(e)}"
            logger.exception("%s", error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            import traceback

            logger.debug(traceback.format_exc())
            self.statusBar.showMessage(f"❌ Error: {str(e)}")

    def show_saami_checker(self):
        """Show SAAMI/CIP compliance checker"""
        try:
            from src.modules.saami_compliance_checker import SAAMIComplianceChecker

            dialog = QWidget(self)
            dialog.setWindowTitle("✅ SAAMI/CIP Compliance Checker")
            dialog.resize(900, 700)
            layout = QVBoxLayout()
            checker = SAAMIComplianceChecker()
            layout.addWidget(checker)
            dialog.setLayout(layout)
            try:
                self.workspace_area.addWidget(dialog)
                self.workspace_area.setCurrentWidget(dialog)
            except Exception:
                dialog.show()
            self.statusBar.showMessage("📍 SAAMI/CIP Checker")
        except Exception as e:
            logger.exception("SAAMIComplianceChecker import failed: %s", e)
            QMessageBox.warning(
                self,
                "Unavailable",
                "SAAMI/CIP Checker unavailable (see debug_err.log in %LOCALAPPDATA%\\Hjemmelading\\logs)",
            )

    def show_grt_integration(self):
        """Show GRT integration"""
        try:
            from src.modules.grt_integration import GRTIntegration

            dialog = QWidget(self)
            dialog.setWindowTitle("🔗 Gordon Reloading Tool Integration")
            dialog.resize(1200, 800)
            layout = QVBoxLayout()
            try:
                grt = GRTIntegration(self)
            except TypeError:
                try:
                    grt = GRTIntegration(parent=self)
                except TypeError:
                    grt = GRTIntegration()
            layout.addWidget(grt)
            dialog.setLayout(layout)
            try:
                self.workspace_area.addWidget(dialog)
                self.workspace_area.setCurrentWidget(dialog)
            except Exception:
                dialog.show()
            self.statusBar.showMessage("📍 GRT Integration")
        except Exception as e:
            logger.exception("GRTIntegration import failed: %s", e)
            QMessageBox.warning(
                self,
                "Unavailable",
                "GRT Integration unavailable (see debug_err.log in %LOCALAPPDATA%\\Hjemmelading\\logs)",
            )

    def show_safety_dashboard(self):
        """Show safety dashboard"""
        try:
            from src.modules.safety_dashboard import SafetyDashboard

            dialog = QWidget(self)
            dialog.setWindowTitle("⚠️ Safety Dashboard")
            dialog.resize(1200, 800)
            layout = QVBoxLayout()
            try:
                dashboard = SafetyDashboard(self)
            except TypeError:
                try:
                    dashboard = SafetyDashboard(parent=self)
                except TypeError:
                    dashboard = SafetyDashboard()
            layout.addWidget(dashboard)
            dialog.setLayout(layout)
            try:
                self.workspace_area.addWidget(dialog)
                self.workspace_area.setCurrentWidget(dialog)
            except Exception:
                dialog.show()
            self.statusBar.showMessage("📍 Safety Dashboard")
        except Exception as e:
            logger.exception("SafetyDashboard import failed: %s", e)
            QMessageBox.warning(
                self,
                "Unavailable",
                "Safety Dashboard unavailable (see debug_err.log in %LOCALAPPDATA%\\Hjemmelading\\logs)",
            )

    def show_drop_chart(self):
        """Show drop chart / dope card generator"""
        try:
            from src.modules.drop_chart_generator import DropChartGenerator

            dialog = QWidget(self)
            dialog.setWindowTitle("📉 Dope Card Generator")
            dialog.resize(1000, 700)
            layout = QVBoxLayout()
            try:
                generator = DropChartGenerator(self)
            except TypeError:
                try:
                    generator = DropChartGenerator(parent=self)
                except TypeError:
                    generator = DropChartGenerator()
            layout.addWidget(generator)
            dialog.setLayout(layout)
            try:
                self.workspace_area.addWidget(dialog)
                self.workspace_area.setCurrentWidget(dialog)
            except Exception:
                dialog.show()
            self.statusBar.showMessage("📍 Dope Card Generator")
        except Exception as e:
            logger.exception("DropChartGenerator import failed: %s", e)
            QMessageBox.warning(
                self,
                "Unavailable",
                "Dope Card Generator unavailable (see debug_err.log in %LOCALAPPDATA%\\Hjemmelading\\logs)",
            )

    def closeEvent(self, event):
        """Håndterer lukking av vinduet"""
        # In headless/offscreen environments we cannot show modal
        # confirmation dialogs; accept the close immediately to avoid
        # blocking the event loop (used by probes/tests).
        try:
            headless_flag = globals().get("_HEADLESS", False)
        except Exception:
            headless_flag = False

        # Also treat explicit QT_QPA_PLATFORM or the Qt platform name as headless
        try:
            import os

            qp = os.environ.get("QT_QPA_PLATFORM", "").lower()
            if qp in ("offscreen", "minimal"):
                headless_flag = True
        except Exception:
            pass

        try:
            from PyQt6.QtGui import QGuiApplication

            try:
                pname = QGuiApplication.platformName().lower()
                if pname in ("offscreen", "minimal"):
                    headless_flag = True
            except Exception:
                pass
        except Exception:
            pass

        if headless_flag:
            try:
                self.db.close()
            except Exception:
                pass
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            "Bekreft avslutning",
            "Er du sikker på at du vil avslutte?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Lukk database
            try:
                self.db.close()
            except Exception:
                pass
            event.accept()
        else:
            event.ignore()
