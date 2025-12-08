from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
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
    def load_logo_pixmap(width: int | None = None):
        return None


try:
    from src.assets.logo import get_window_icon_pixmap
except Exception:

    def get_window_icon_pixmap(size=64):
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

    def tr(key: str, *, lang: str | None = None, **kwargs: object) -> str:
        return key


logger = get_logger(__name__)


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
        self.setWindowTitle("VALKYRIE BALLISTICS - Hjemmelading")
        self.setMinimumSize(900, 600)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        central = QWidget()
        layout = QVBoxLayout()
        label = QLabel("Hovedvinduet er oppe og kjører!\nUtvid funksjonalitet her.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        central.setLayout(layout)
        self.setCentralWidget(central)

        # Apply user settings and initialize the full UI safely.
        try:
            self.apply_user_settings()
        except Exception as e:
            # Log and persist startup exceptions for debugging, but don't silently swallow them.
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
                # Show minimal user-visible error and re-raise so callers can handle it.
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

        # Check for saved workflows after UI is ready
        self.check_saved_workflows()

    def _open_workflow_debug(self):
        """Temporary debug dialog to list available workflows and launch them."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Debug: Launch workflow")
        dlg.setMinimumSize(400, 300)
        layout = QVBoxLayout()

        listw = QListWidget()
        # Populate from the workflow map used by launch_workflow
        wf_keys = [
            "load_development_workflow",
            "ocw_test",
            "ladder_test",
            "seating_depth",
            "smart_wizard",
            "temperature_test",
            "saami_compliance",
            "chronograph_import",
            "cold_bore",
            "batch_qc",
            "lot_tracker",
            "drop_chart",
            "wind_drift",
            "zero_shift",
        ]
        for k in wf_keys:
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

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        self.setWindowTitle("HJEMMELADING - Precision Reloading System")
        self.setGeometry(100, 100, 1400, 900)

        # Set professional skull icon (use central helper)
        from PyQt6.QtGui import QIcon

        pix_icon = load_logo_pixmap(128)
        if pix_icon:
            self.setWindowIcon(QIcon(pix_icon))

        # Apply dark tactical theme
        self.setStyleSheet(ReloadingTheme.get_stylesheet())

        # Opprett meny
        self.create_menu()

        # Opprett status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self._show_status_message("Klar")

        # Opprett sentralt widget med stacked layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.apply_global_button_style()
        # Hovedlayout
        # Ensure at least minimal state objects exist
        if not hasattr(self, "mode_manager"):
            self.mode_manager = None
        if not hasattr(self, "state_manager"):
            self.state_manager = None

    def apply_global_button_style(self):
        # Industrial, dark, square buttons
        button_style = """
            QPushButton {
                background-color: #232a2f;
                color: #e6eef3;
                border: 1px solid #2f363b;
                border-radius: 4px;
                padding: 10px 18px;
                font-weight: 700;
                font-size: 14px;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #2b3136;
                border: 1px solid #ff6b35; /* accent edge */
            }
            QPushButton:pressed {
                background-color: #1b2023;
                border: 1px solid #1f2427;
            }
        """
        self.setStyleSheet(self.styleSheet() + button_style)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        # Navigation bar
        nav_bar = QWidget()
        nav_bar.setStyleSheet(
            """
            QWidget {
                background-color: #2c3e50;
                padding: 10px;
            }
        """
        )
        nav_layout = QHBoxLayout()
        nav_bar.setLayout(nav_layout)

        # Home button with modern project logo (small)
        self.btn_home = QPushButton("Workflow Hub")
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
        self.btn_home.setStyleSheet(
            """
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #444857, stop:1 #23242b);
                color: #ffd700;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                border: 2px solid #7d5a18;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #5a5e6e, stop:1 #2c2d35);
                color: #fffbe6;
                border: 2px solid #ffd700;
            }
            QPushButton:pressed {
                background-color: #23242b;
                color: #ffd700;
                border: 2px solid #bfa14a;
            }
        """
        )
        self.btn_home.clicked.connect(self.show_workflow_hub)
        nav_layout.addWidget(self.btn_home)

        # All Tools button
        self.btn_all_tools = QPushButton("🔧 All Tools (Legacy)")
        self.btn_all_tools.setStyleSheet(
            """
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #7f8c8d, stop:1 #4b5254);
                color: #e0e0e0;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                border: 2px solid #444;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #95a5a6, stop:1 #5a6062);
                color: #fff;
                border: 2px solid #ffd700;
            }
            QPushButton:pressed {
                background-color: #4b5254;
                color: #ffd700;
                border: 2px solid #bfa14a;
                /* box-shadow removed (unsupported by Qt stylesheets) */
            }
        """
        )
        self.btn_all_tools.clicked.connect(self.show_all_tools)
        nav_layout.addWidget(self.btn_all_tools)

        nav_layout.addStretch()

        # Current workflow label
        self.label_current_workflow = QLabel("")
        self.label_current_workflow.setStyleSheet(
            "color: white; font-size: 14px; font-weight: bold;"
        )
        nav_layout.addWidget(self.label_current_workflow)

        layout.addWidget(nav_bar)

        # Vis hovedlogo øverst (bruker din logo-fil)
        pix = load_logo_pixmap(120)
        if pix:
            logo_lbl = QLabel()
            logo_lbl.setPixmap(pix)
            logo_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Stacked widget for switching between workflow hub and tools
        self.stacked_widget = QStackedWidget()
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

            # Finally, initialize the full UI
            try:
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

        # Page 1: Workflow Hub (imported lazily so startup can proceed if module fails)
        try:
            from src.modules.workflow_hub import WorkflowHub

            self.workflow_hub = WorkflowHub(self.state_manager, self.mode_manager)
            self.workflow_hub.workflow_selected.connect(self.launch_workflow)
            self.stacked_widget.addWidget(self.workflow_hub)
        except Exception as e:
            logger.exception("Failed to create WorkflowHub: %s", e)
            fallback = QWidget()
            lbl = QLabel("Workflow Hub unavailable")
            fl = QVBoxLayout()
            fl.addWidget(lbl)
            fallback.setLayout(fl)
            self.stacked_widget.addWidget(fallback)
            self.workflow_hub = None

        # Page 2: All Tools (legacy tabs)
        self.tabs_widget = QWidget()
        tabs_layout = QVBoxLayout()
        self.tabs_widget.setLayout(tabs_layout)

        self.tabs = QTabWidget()
        tabs_layout.addWidget(self.tabs)

        self.stacked_widget.addWidget(self.tabs_widget)

        # Legg til tabs
        self.create_tabs()

        # Start on workflow hub
        self.show_workflow_hub()

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

        # Dashboard tab
        dashboard_widget = self.create_dashboard_tab()
        self.tabs.addTab(dashboard_widget, _tr("tab_dashboard"))

        # Test Lab tab
        test_lab_widget = self.create_test_lab_tab()
        self.tabs.addTab(test_lab_widget, _tr("tab_test_lab"))

        # Ammunisjon tab
        ammo_widget = self.create_ammo_tab()
        self.tabs.addTab(ammo_widget, _tr("tab_ammunition"))

        # Rifles & Optikk tab
        rifles_widget = self.create_rifles_tab()
        self.tabs.addTab(rifles_widget, _tr("tab_rifles"))

        # Lager tab
        inventory_widget = self.create_inventory_tab()
        self.tabs.addTab(inventory_widget, _tr("tab_inventory"))

        # Logg tab
        log_widget = self.create_log_tab()
        self.tabs.addTab(log_widget, _tr("tab_log"))

        # Analyse tab
        analysis_widget = self.create_analysis_tab()
        self.tabs.addTab(analysis_widget, _tr("tab_analysis"))

        # Innstillinger tab
        settings_widget = self.create_settings_tab()
        self.tabs.addTab(settings_widget, _tr("tab_settings"))

    def create_dashboard_tab(self):
        """Oppretter dashboard-fanen"""
        try:
            from src.modules.dashboard import Dashboard

            return Dashboard()
        except Exception as e:
            logger.exception("Failed to import Dashboard: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Dashboard unavailable"))
            w.setLayout(layout)
            return w

    def create_test_lab_tab(self):
        """Oppretter test lab-fanen"""
        try:
            from src.modules.ladder_test_lab import LadderTestLab

            return LadderTestLab()
        except Exception as e:
            logger.exception("Failed to import LadderTestLab: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Test Lab unavailable"))
            w.setLayout(layout)
            return w

    def create_ammo_tab(self):
        """Oppretter ammunisjon-fanen"""
        try:
            from src.modules.ammo_profile_manager import AmmoProfileManager

            return AmmoProfileManager()
        except Exception as e:
            logger.exception("Failed to import AmmoProfileManager: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Ammunisjon unavailable"))
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

            tabs.addTab(RifleDatabaseManager(), "🎯 Våpen Database")
        except Exception as e:
            logger.exception("RifleDatabaseManager import failed: %s", e)

        # Tab 2: Rifle & Optic Manager (Legacy)
        try:
            from src.modules.rifle_optic_manager import RifleOpticManager

            tabs.addTab(RifleOpticManager(), "🔭 Rifle & Optikk")
        except Exception as e:
            logger.exception("RifleOpticManager import failed: %s", e)

        # Tab 3: Rifle Performance Tracker
        try:
            from src.modules.rifle_performance_tracker import RiflePerformanceTracker

            tabs.addTab(RiflePerformanceTracker(), "📈 Performance")
        except Exception as e:
            logger.exception("RiflePerformanceTracker import failed: %s", e)

        return widget

    def create_inventory_tab(self):
        """Oppretter lager-fanen"""
        try:
            from src.modules.inventory_manager import InventoryManager

            return InventoryManager()
        except Exception as e:
            logger.exception("InventoryManager import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Inventory unavailable"))
            w.setLayout(layout)
            return w

    def create_log_tab(self):
        """Oppretter logg-fanen"""
        try:
            from src.modules.session_logger import SessionLogger

            return SessionLogger()
        except Exception as e:
            logger.exception("SessionLogger import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Log unavailable"))
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

            tabs.addTab(TerrainMapViewer(), "🗺️ Terrengkart")
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
        """Show workflow hub landing page"""
        self.stacked_widget.setCurrentIndex(0)
        self.label_current_workflow.setText("")
        self.statusBar.showMessage("Workflow Hub - Velg hva du vil gjøre")

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
        active_states = self.state_manager.get_all_active()

        if active_states:
            # Show resume dialog (import lazily to avoid startup import failures)
            try:
                from src.modules.workflow_resume_dialog import WorkflowResumeDialog

                dialog = WorkflowResumeDialog(self.state_manager, self)
                dialog.workflow_selected.connect(self.resume_workflow)
                # Show dialog after a short delay so main window is visible
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(500, dialog.exec)
            except Exception as e:
                logger.exception("Failed to show WorkflowResumeDialog: %s", e)
                return

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
        dialog = QWidget()
        dialog.setWindowTitle("🥉 Brass/Hylse Manager")
        dialog.resize(1400, 900)
        layout = QVBoxLayout()
        try:
            from src.modules.brass_manager import BrassManager

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
        dialog = QWidget()
        dialog.setWindowTitle("🎯 Rifles & Optikk")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.rifle_optic_manager import RifleOpticManager

            manager = RifleOpticManager()
            layout.addWidget(manager)
        except Exception as e:
            logger.exception("RifleOpticManager import failed: %s", e)
            layout.addWidget(QLabel("Rifle & Optic Manager unavailable"))
        dialog.setLayout(layout)
        dialog.show()
        self.statusBar.showMessage("📍 Rifles & Optikk Manager")

    def show_ammo_profile_manager(self):
        """Show ammo profiles manager"""
        dialog = QWidget()
        dialog.setWindowTitle("📦 Ammunisjonsprofiler")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.ammo_profile_manager import AmmoProfileManager

            manager = AmmoProfileManager()
            layout.addWidget(manager)
        except Exception as e:
            logger.exception("AmmoProfileManager import failed: %s", e)
            layout.addWidget(QLabel("Ammo Profile Manager unavailable"))
        dialog.setLayout(layout)
        dialog.show()
        self.statusBar.showMessage("📍 Ammunisjonsprofil Manager")

    def show_rifle_performance(self):
        """Show rifle performance tracker"""
        dialog = QWidget()
        dialog.setWindowTitle("📊 Rifle Performance Tracker")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.rifle_performance_tracker import RiflePerformanceTracker

            tracker = RiflePerformanceTracker()
            layout.addWidget(tracker)
        except Exception as e:
            logger.exception("RiflePerformanceTracker import failed: %s", e)
            layout.addWidget(QLabel("Rifle Performance Tracker unavailable"))
        dialog.setLayout(layout)
        dialog.show()
        self.statusBar.showMessage("📍 Rifle Performance Tracker")

    def show_ballistics_simulator(self):
        """Show real-time ballistics simulator"""
        from src.modules.ballistics_simulator import BallisticsSimulator

        dialog = QWidget()
        dialog.setWindowTitle("🔬 Real-Time Ballistics Simulator")
        dialog.resize(1600, 1000)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        simulator = BallisticsSimulator()
        layout.addWidget(simulator)

        dialog.setLayout(layout)
        dialog.show()
        self.statusBar.showMessage(
            "🔬 Ballistics Simulator - Physics-based load prediction"
        )

    def show_precision_tracker(self):
        """Show precision tracker"""
        dialog = QWidget()
        dialog.setWindowTitle("🎯 Precision Tracker")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.precision_tracker import PrecisionTracker

            tracker = PrecisionTracker()
            layout.addWidget(tracker)
        except Exception as e:
            logger.exception("PrecisionTracker import failed: %s", e)
            layout.addWidget(QLabel("Precision Tracker unavailable"))
        dialog.setLayout(layout)
        dialog.show()
        self.statusBar.showMessage("📍 Precision Tracker")

    def show_target_analyzer(self):
        """Show target analyzer"""
        dialog = QWidget()
        dialog.setWindowTitle("📸 Target Analyzer")
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from src.modules.target_analyzer import TargetAnalyzer

            analyzer = TargetAnalyzer()
            layout.addWidget(analyzer)
        except Exception as e:
            logger.exception("TargetAnalyzer import failed: %s", e)
            layout.addWidget(QLabel("Target Analyzer unavailable"))
        dialog.setLayout(layout)
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

            dialog = QWidget()
            dialog.setWindowTitle("✅ SAAMI/CIP Compliance Checker")
            dialog.resize(900, 700)
            layout = QVBoxLayout()
            checker = SAAMIComplianceChecker()
            layout.addWidget(checker)
            dialog.setLayout(layout)
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

            dialog = QWidget()
            dialog.setWindowTitle("🔗 Gordon Reloading Tool Integration")
            dialog.resize(1200, 800)
            layout = QVBoxLayout()
            grt = GRTIntegration()
            layout.addWidget(grt)
            dialog.setLayout(layout)
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

            dialog = QWidget()
            dialog.setWindowTitle("⚠️ Safety Dashboard")
            dialog.resize(1200, 800)
            layout = QVBoxLayout()
            dashboard = SafetyDashboard()
            layout.addWidget(dashboard)
            dialog.setLayout(layout)
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

            dialog = QWidget()
            dialog.setWindowTitle("📉 Dope Card Generator")
            dialog.resize(1000, 700)
            layout = QVBoxLayout()
            generator = DropChartGenerator()
            layout.addWidget(generator)
            dialog.setLayout(layout)
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
        reply = QMessageBox.question(
            self,
            "Bekreft avslutning",
            "Er du sikker på at du vil avslutte?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Lukk database
            self.db.close()
            event.accept()
        else:
            event.ignore()
