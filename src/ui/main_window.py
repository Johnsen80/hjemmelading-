#!/usr/bin/env python3
# pyright: reportOptionalCall=false, reportOptionalMemberAccess=false, reportArgumentType=false, reportInvalidTypeForm=false, reportGeneralTypeIssues=false, reportAssignmentType=false, reportAttributeAccessIssue=false

import csv
import importlib
import inspect
import io
import json
import tempfile
import zipfile
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from ..qt_compat import (
    QAction,
    QApplication,
    QDesktopServices,
    QDialog,
    QFont,
    QFrame,
    QGroupBox,
    QGuiApplication,
    QHBoxLayout,
    QIcon,
    QKeySequence,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPixmap,
    QPushButton,
    QRadioButton,
    QSettings,
    QStackedWidget,
    QStatusBar,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimer,
    QtWidgets,
    QUrl,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    QComboBox = QtWidgets.QComboBox
    QFileDialog = QtWidgets.QFileDialog
else:
    try:
        QComboBox = QtWidgets.QComboBox
        QFileDialog = QtWidgets.QFileDialog
        _HAS_QT = True
    except ImportError:
        _HAS_QT = False

        class _Stub:
            """Minimal stub base class used when Qt is unavailable."""

        QSettings: Any = _Stub
        QSize: Any = _Stub
        QUrl: Any = _Stub

        class Qt:  # type: ignore
            class WindowType:
                WindowStaysOnTopHint = 0

            class AlignmentFlag:
                AlignCenter = 0

        QAction: Any = _Stub
        QDesktopServices: Any = _Stub
        QIcon: Any = _Stub
        QKeySequence: Any = _Stub

        QComboBox: Any = _Stub
        QDialog: Any = _Stub
        QFileDialog: Any = _Stub
        QFrame: Any = _Stub
        QHBoxLayout: Any = _Stub
        QLabel: Any = _Stub
        QLineEdit: Any = _Stub
        QListWidget: Any = _Stub

        class _QMainWindowStub(object):
            def show(self):
                pass

            def setWindowTitle(self, *args, **kwargs):
                pass

            def close(self):
                pass

            def setGeometry(self, *args, **kwargs):
                pass

            def resize(self, *args, **kwargs):
                pass

            def move(self, *args, **kwargs):
                pass

            def centralWidget(self):
                return None

            def layout(self):
                return None

        QMainWindow: Any = _QMainWindowStub

        class _MsgBox:
            @staticmethod
            def critical(*args, **kwargs):
                return None

            @staticmethod
            def information(*args, **kwargs):
                return None

        QMessageBox: Any = _MsgBox
        QGroupBox: Any = _Stub
        QPushButton: Any = _Stub
        QRadioButton: Any = _Stub
        QStackedWidget: Any = _Stub
        QStatusBar: Any = _Stub
        QTableWidget: Any = _Stub
        QTableWidgetItem: Any = _Stub
        QTabWidget: Any = _Stub
        QVBoxLayout: Any = _Stub
        QWidget: Any = _Stub

import os

from ..logging_config import get_logger
from ..tools.load_session_runtime_service import store_workflow_context_in_settings

# Diagnostic widget tracing is expensive; keep it opt-in for dev only.
_DIAG_WIDGETS = os.environ.get("VALKYRIE_WIDGET_TRACE", "").lower() in ("1", "true")


# Fallback for get_log_dir if needed
def get_log_dir() -> str:
    base = os.path.join(os.getcwd(), "tools", "logs")
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        pass
    return base


# GUI wrapper setup function: call this after QApplication is created
def setup_gui_wrappers():
    try:
        _QMenu_orig = QtWidgets.QMenu
        _QWidget_orig = QtWidgets.QWidget

        class _QMenu_wrapper(_QMenu_orig):
            def __init__(self, *args, **kwargs):
                parent_kw = None
                if "parent" in kwargs:
                    parent_kw = kwargs.pop("parent")
                parent_in_args = False
                try:
                    parent_in_args = any(isinstance(a, _QWidget_orig) for a in args)
                except Exception:
                    parent_in_args = False
                if parent_kw is not None and not parent_in_args:
                    try:
                        if len(args) >= 1 and isinstance(args[0], str):
                            super().__init__(args[0], parent_kw)
                            return
                        super().__init__(parent_kw)
                        return
                    except Exception:
                        pass
                if not parent_in_args and parent_kw is None:
                    try:
                        aw = QApplication.activeWindow()
                        if isinstance(aw, _QWidget_orig):
                            if len(args) >= 1 and isinstance(args[0], str):
                                super().__init__(args[0], aw)
                                return
                            super().__init__(aw)
                            return
                    except Exception:
                        pass
                super().__init__(*args, **kwargs)

        globals()["QMenu"] = _QMenu_wrapper  # type: ignore[assignment]
    except Exception:
        pass

    # Instrument QWidget.show to log stack when a top-level widget is shown.
    try:
        if not _DIAG_WIDGETS:
            raise RuntimeError("diagnostics disabled")
        import os as _os2
        import traceback as _tb2

        _orig_show = getattr(QWidget, "show", None)

        def _logged_show(self, *a, **kw):
            try:
                if getattr(self, "parent", lambda: None)() is None:
                    try:
                        ld = _os2.path.join(_os2.getcwd(), "tools", "logs")
                        _os2.makedirs(ld, exist_ok=True)
                        fn = _os2.path.join(ld, "late_widget_shows.log")
                        with open(fn, "a", encoding="utf-8") as _f:
                            _f.write(
                                f"showing top-level: {type(self).__name__} repr={repr(self)[:200]}\n"
                            )
                            _tb2.print_stack(file=_f)
                            _f.write("---\n")
                    except Exception:
                        pass
            except Exception:
                pass
            if _orig_show:
                try:
                    return _orig_show(self, *a, **kw)
                except Exception:
                    try:
                        return _orig_show(self)
                    except Exception:
                        return None

        try:
            setattr(QWidget, "show", _logged_show)  # type: ignore[method-assign]
        except Exception:
            pass
    except Exception:
        pass

    # Lightweight late-creation tracing for widgets that appear after
    # initialization. This logs full Python stack traces for QPushButton,
    # QLabel and QMenu creations to help find delayed creators.
    try:
        if not _DIAG_WIDGETS:
            raise RuntimeError("diagnostics disabled")
        import os as _os
        import traceback as _tb

        def _log_creation(w):
            try:
                ld = _os.path.join(_os.getcwd(), "tools", "logs")
                _os.makedirs(ld, exist_ok=True)
                fn = _os.path.join(ld, "late_widget_creation.log")
                with open(fn, "a", encoding="utf-8") as _f:
                    _f.write(
                        f"late-created: {type(w).__name__} repr={repr(w)[:200]} parent={getattr(w, 'parent', lambda: None)()}\n"
                    )
                    _tb.print_stack(file=_f)
                    _f.write("---\n")
            except Exception:
                pass

        def _wrap_init(orig):
            def _shim(self, *a, **kw):
                orig(self, *a, **kw)
                try:
                    _log_creation(self)
                except Exception:
                    pass

            return _shim

        try:
            QPushButton.__init__ = _wrap_init(QPushButton.__init__)  # type: ignore[method-assign]
        except Exception:
            pass
        try:
            QLabel.__init__ = _wrap_init(QLabel.__init__)  # type: ignore[method-assign]
        except Exception:
            pass
        try:
            QMenu.__init__ = _wrap_init(QMenu.__init__)  # type: ignore[method-assign]
        except Exception:
            pass
    except Exception:
        pass

    # Monkeypatch QMenuBar.addMenu to ensure menus created via the menubar
    # are parented to the menubar (and therefore not top-level).
    try:
        _orig_addMenu = getattr(QtWidgets.QMenuBar, "addMenu", None)

        def _patched_addMenu(self, *a, **kw):
            res = _orig_addMenu(self, *a, **kw) if _orig_addMenu else None
            try:
                if res is not None:
                    # Ensure the created menu has a parent
                    try:
                        if getattr(res, "parent", None) is None:
                            res.setParent(self)
                    except Exception:
                        pass
            except Exception:
                pass
            return res

        try:
            setattr(QtWidgets.QMenuBar, "addMenu", _patched_addMenu)
        except Exception:
            pass
    except Exception:
        pass

    # Optional diagnostic: monkeypatch QWidget.__init__ to log stack traces when
    # top-level widgets are created without a parent. This helps find which
    # modules create stray windows/menus during startup. Guarded by try/except
    # so it doesn't break packaged runtime.
    try:
        if not _DIAG_WIDGETS:
            raise RuntimeError("diagnostics disabled")
        _orig_qwidget_init = getattr(QWidget, "__init__", None)

        def _patched_qwidget_init(self, *a, **kw):
            parent_arg = kw.get("parent", None)
            if parent_arg is None and len(a) > 0:
                parent_arg = a[0]
            try:
                if _orig_qwidget_init:
                    _orig_qwidget_init(self, *a, **kw)
                else:
                    object.__init__(self)
            except Exception:
                try:
                    object.__init__(self)
                except Exception:
                    pass

            try:
                # Aggressive logging: record every widget created without explicit parent.
                if parent_arg is None:
                    import os
                    import traceback
                    from datetime import datetime as _dt
                    from datetime import timezone as _tz

                    log_dir = os.path.join(os.getcwd(), "tools", "logs")
                    os.makedirs(log_dir, exist_ok=True)
                    try:
                        with open(
                            os.path.join(log_dir, "top_level_creation.log"),
                            "a",
                            encoding="utf-8",
                        ) as _f:
                            _f.write(
                                f"created time={_dt.now(_tz.utc).isoformat()} type={type(self)} repr={repr(self)[:200]}\n"
                            )
                            traceback.print_stack(file=_f)
                            _f.write("---\n")
                    except Exception:
                        try:
                            # Best-effort fallback: write minimal line if full logging fails
                            with open(
                                os.path.join(log_dir, "top_level_creation_min.log"),
                                "a",
                                encoding="utf-8",
                            ) as _f:
                                _f.write(
                                    f"created time={_dt.now(_tz.utc).isoformat()} type={type(self)}\n"
                                )
                        except Exception:
                            pass
            except Exception:
                pass

        try:
            setattr(QWidget, "__init__", _patched_qwidget_init)
        except Exception:
            pass
    except Exception:
        pass


# Per-user persistent diagnostics helper
try:
    _safe_logger_module = importlib.import_module("HjemmeladingApp.utils.safe_logger")
    append_exception = _safe_logger_module.append_exception
    append_message = _safe_logger_module.append_message
except Exception:

    def append_exception(
        msg: str = "", exc: BaseException | None = None, app_name: str = ""
    ) -> None:
        return None

    def append_message(msg: str, app_name: str = "") -> None:
        return None


# Logo helpers: try to load a project logo or fall back to generated skull icon
try:
    from .logo_helper import load_logo_pixmap
except Exception:
    # Provide a safe fallback if helper cannot be imported
    def load_logo_pixmap(width: int | None = None) -> Optional["QPixmap"]:
        return None


try:
    from ..assets.logo import get_window_icon_pixmap
except Exception:

    def get_window_icon_pixmap(size=64) -> Any:
        return None


# Theme helper (fallback if module not available)
try:
    from .reloading_theme import ReloadingTheme as _ReloadingTheme
except Exception:

    class _ReloadingTheme:
        @staticmethod
        def get_stylesheet():
            return """
            QWidget { background-color: #23242b; color: #e0e0e0; }
            """

        @staticmethod
        def get_safe_stylesheet():
            return """
            QWidget { background-color: #23242b; color: #e0e0e0; }
            """

        @staticmethod
        def get_button_stylesheet():
            return """
            QPushButton { background-color: #444; color: #fff; }
            """


ReloadingTheme: Any = _ReloadingTheme


# Simple translation helper (fallback to identity)
try:
    from ..utils.i18n import tr
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
_STRAY_WIDGET_CLEANUP = os.environ.get("VALKYRIE_STRAY_WIDGET_CLEANUP", "").lower() in (
    "1",
    "true",
)


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
                        parent_hint = (
                            dialog if isinstance(dialog, _orig_QWidget) else None
                        )
                        if (
                            "parent" not in kw
                            and not (len(a) > 0 and isinstance(a[0], _orig_QWidget))
                            and parent_hint is not None
                        ):
                            kw = {**kw, "parent": parent_hint}
                        return _orig_QLabel(*a, **kw)
                    except Exception:
                        return _orig_QLabel(*a, **kw)

                def _make_button(*a, **kw):
                    try:
                        parent_hint = (
                            dialog if isinstance(dialog, _orig_QWidget) else None
                        )
                        if (
                            "parent" not in kw
                            and not (len(a) > 0 and isinstance(a[0], _orig_QWidget))
                            and parent_hint is not None
                        ):
                            kw = {**kw, "parent": parent_hint}
                        return _orig_QPushButton(*a, **kw)
                    except Exception:
                        return _orig_QPushButton(*a, **kw)

                def _make_menu(*a, **kw):
                    try:
                        parent_hint = (
                            dialog if isinstance(dialog, _orig_QWidget) else None
                        )
                        if (
                            "parent" not in kw
                            and not (len(a) > 0 and isinstance(a[0], _orig_QWidget))
                            and parent_hint is not None
                        ):
                            kw = {**kw, "parent": parent_hint}
                        return _orig_QMenu(*a, **kw)
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
    density = cfg.get("ui_density", "comfortable")
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

    if density == "compact":
        font_size = "12px"
        btn_pad = "4px 8px"
        input_pad = "4px"
    else:
        font_size = "13px"
        btn_pad = "6px 10px"
        input_pad = "6px"

    css = f"""
QWidget {{ background-color: {win_hex}; color: {text_hex}; font-size: {font_size}; }}
QPushButton {{ {btn_css} padding:{btn_pad}; border-radius:6px; }}
QLineEdit, QTextEdit {{ background-color: {win_hex}; color: {text_hex}; border: 1px solid {base_hex}; padding: {input_pad}; }}
QTabWidget::pane {{ background: {win_hex}; }}
"""
    return css


class MainWindow(QMainWindow):
    def show(self):
        super().show()

    def show_import_export_report_dialog(self):
        """Show a dialog for import/export/report actions."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle(tr("mw_import_export_report_title"))
            layout = QVBoxLayout(dialog)
            label = QLabel(tr("mw_import_export_report_body"))
            layout.addWidget(label)
            btn_close = QPushButton(tr("calib_analysis_close"))
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            dialog.setLayout(layout)
            _run_modal(dialog)
        except Exception as e:
            self._show_status_message(
                tr("mw_import_export_report_open_failed", error=e)
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("MainWindow init: start")
        self._startup_in_progress = True
        try:
            ai_helper_module = importlib.import_module("modules.ai_helper")
            ai_helper_factory = getattr(ai_helper_module, "AIHelper", None)
            self.ai_helper = (
                ai_helper_factory() if callable(ai_helper_factory) else None
            )
        except Exception:
            self.ai_helper = None
        # Guard to avoid double-initializing the UI (prevents duplicate menus/windows)
        self._ui_initialized = False
        self.setWindowTitle(tr("mw_title_short"))
        self.setMinimumSize(900, 600)
        if os.environ.get("VALKYRIE_ALWAYS_ON_TOP", "").lower() in ("1", "true"):
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        _safe_ui = os.environ.get("VALKYRIE_SAFE_UI", "").lower() in ("1", "true")
        # Apply app theme early so initial landing UI matches saved appearance.
        # Read minimal saved theme values from QSettings synchronously to
        # avoid a visual flash from default -> user theme during startup.
        try:
            from .theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            try:
                self.setStyleSheet(ReloadingTheme.get_safe_stylesheet())
            except Exception:
                pass
            else:
                try:
                    qs = QSettings("ReloadingWorkshop", "ReloadingManager")
                    theme = qs.value("theme", None)
                    rgb = qs.value("rgb", None)
                    btn_style = qs.value("button_style", None)
                    ui_density = qs.value("ui/density", None)
                    cfg = {}
                    if theme is not None:
                        cfg["theme"] = theme
                    if isinstance(rgb, dict):
                        cfg["rgb"] = rgb
                    if btn_style is not None:
                        cfg["button_style"] = btn_style
                    if ui_density is not None:
                        cfg["ui_density"] = ui_density

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
        logger.info("MainWindow init: theme applied")
        # Build the full UI immediately to avoid swapping the central widget
        # after the window is shown (prevents flicker and disappearing menus).
        try:
            logger.info("MainWindow init: calling apply_user_settings")
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
                    QMessageBox.critical(None, tr("mw_startup_error_title"), str(e))
                except Exception:
                    pass
                raise
        try:
            self._setup_ai_panel()
        except Exception:
            pass
        logger.info("MainWindow init: apply_user_settings done")

        # Quick debug shortcut to list and launch workflows (helps when UI elements are hard to reach)
        try:
            act = QAction("DebugShortcut", self)
            act.setShortcut(QKeySequence("Ctrl+D"))
            act.triggered.connect(self._open_workflow_debug)
            # Add to the window so the shortcut is active
            self.addAction(act)
        except Exception:
            pass
        self._startup_in_progress = False
        logger.info("MainWindow init: end")

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

    def _setup_ai_panel(self):
        # Create a simple AI guidance panel in the UI
        try:
            ai_group = QGroupBox(tr("mw_ai_guidance"))
            ai_layout = QVBoxLayout(ai_group)
            self.ai_label = QLabel(tr("mw_ai_guidance_prompt"))
            ai_layout.addWidget(self.ai_label)
            ai_btn = QPushButton(tr("mw_ai_get_suggestions"))
            ai_btn.clicked.connect(self._show_ai_guidance)
            ai_layout.addWidget(ai_btn)
            # Add to main layout (example, adjust as needed)
            cw = self.centralWidget()
            _cw_layout = cw.layout() if cw is not None else None
            if _cw_layout is not None:
                _cw_layout.addWidget(ai_group)
        except Exception:
            pass

    def _show_ai_guidance(self):
        # Example data for AI suggestion
        test_data = [
            {"charge": 42.0, "velocity": 820, "group_size": 18},
            {"charge": 42.2, "velocity": 825, "group_size": 15},
            {"charge": 42.4, "velocity": 830, "group_size": 22},
        ]
        if self.ai_helper is None:
            self.ai_label.setText(tr("mw_ai_unavailable"))
            return
        guidance = self.ai_helper.suggest_next_test(test_data)
        self.ai_label.setText(f"{guidance['suggestion']}\n{guidance['rationale']}")

    # ...existing code...
    # Widget creation code removed. Place widget setup in appropriate dialog or method.

    def _import_chronograph_csv(self):
        try:
            import_mod = importlib.import_module("src.utils.chronograph_import")
            import_fn = getattr(import_mod, "import_chronograph_csv", None)
            if callable(import_fn):
                self._show_status_message(tr("mw_chrono_import_helper_available"))
            else:
                self._show_status_message(tr("mw_chrono_import_helper_unavailable"))
        except Exception as e:
            self._show_status_message(tr("mw_import_failed_status", error=e))

    def _import_grt_xml(self):
        self._show_status_message(
            "Legacy reference import has been removed from the product."
        )

    def _export_chronograph_data(self):
        try:
            from ..database.chronograph_importer import export_chronograph_data

            export_chronograph_data()
            self._show_status_message(tr("mw_chrono_exported"))
        except Exception as e:
            self._show_status_message(tr("mw_export_failed_status", error=e))

    def _generate_pdf_report(self):
        try:
            report_mod = importlib.import_module("scripts.generate_pdf_report")
            generate_pdf_report = getattr(report_mod, "generate_pdf_report", None)
            if not callable(generate_pdf_report):
                raise RuntimeError(tr("mw_generate_pdf_unavailable"))
            data = self._build_workflow_pdf_report_data()
            pdf_path = "session_report.pdf"
            generate_pdf_report(data, pdf_path)
            self._show_status_message(tr("mw_pdf_report_generated"))
        except Exception as e:
            self._show_status_message(tr("mw_report_failed_status", error=e))

    def _open_workflow_debug(self):
        """Temporary debug dialog to list available workflows and launch them."""
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("mw_debug_launch_title"))
        dlg.setMinimumSize(400, 300)
        layout = QVBoxLayout()
        listw = QListWidget()

        # Populate from the workflow map used by launch_workflow. Filter out
        # workflows that require optional dependencies (matplotlib/OpenCV)
        from ..utils.optional_deps import HAS_CV2, HAS_MPL

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
            ("batch_workspace", "mpl"),
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

        btn_launch = QPushButton(tr("mw_launch_selected"))

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
            from ..modules.measurement_wizard import show_measurement_wizard

            show_measurement_wizard()
        except Exception as e:
            try:
                QMessageBox.critical(
                    self,
                    tr("msg_error"),
                    tr("mw_measurement_wizard_open_failed", error=e),
                )
            except Exception:
                pass

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        # Avoid running initialization twice (guards duplicate menus/windows)
        if getattr(self, "_ui_initialized", False):
            return
        self._ui_initialized = True
        self.setWindowTitle(tr("mw_title_full"))
        self.setGeometry(100, 100, 1400, 900)

        # Safety: locally shadow widgets only when explicit cleanup is enabled.
        # Avoid altering widget constructors in normal GUI sessions.
        if _STRAY_WIDGET_CLEANUP:
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
                        if len(a) > 1 and isinstance(a[1], QWidget):
                            return _orig_QMenu(*a, **kw)
                        if len(a) == 0:
                            return _orig_QMenu(self)
                        if len(a) == 1 and isinstance(a[0], str):
                            return _orig_QMenu(a[0], self)
                        return _orig_QMenu(*a, **kw)
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
        self.setStatusBar(QStatusBar(self))
        self._show_status_message(tr("mw_ready_ctrl_k"))

        # Opprett sentralt widget med stacked layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.apply_global_button_style()
        try:
            self._sync_mode_combo_from_settings()
        except Exception:
            pass
        try:
            self._apply_ui_mode_to_nav()
        except Exception:
            pass
        # Show banner if optional dependencies are missing (matplotlib/OpenCV)
        try:
            from ..utils.optional_deps import HAS_CV2, HAS_MPL

            missing = []
            if not HAS_MPL:
                missing.append("matplotlib")
            if not HAS_CV2:
                missing.append("opencv-python")

            if missing:
                try:
                    from .disabled_feature_card import DisabledFeatureCard

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
        # Use centralized button stylesheet
        button_style = ReloadingTheme.get_button_stylesheet()
        self.setStyleSheet(self.styleSheet() + button_style)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.central_widget.setLayout(root_layout)

        self._build_top_bar(root_layout)
        self._build_shell_body(root_layout)

        # Command palette shortcut
        try:
            act = QAction("CommandPalette", self)
            act.setShortcut(QKeySequence("Ctrl+K"))
            act.triggered.connect(self._focus_command_palette)
            self.addAction(act)
        except Exception:
            pass

        try:
            self._build_command_map()
        except Exception:
            pass

    def _build_top_bar(self, root_layout: "QVBoxLayout") -> None:
        bar = QWidget(self.central_widget)
        bar.setObjectName("topBar")
        bar_layout = QHBoxLayout()
        bar_layout.setContentsMargins(16, 8, 16, 8)
        bar_layout.setSpacing(10)
        bar.setLayout(bar_layout)

        brand = QLabel(tr("mw_brand"), bar)
        brand.setObjectName("appTitle")
        try:
            brand.setCursor(Qt.CursorShape.PointingHandCursor)
            brand.mousePressEvent = lambda _ev: self._show_page("home")
        except Exception:
            pass
        bar_layout.addWidget(brand)

        self.label_current_workflow = QLabel("", bar)
        self.label_current_workflow.setObjectName("currentWorkflowLabel")
        bar_layout.addWidget(self.label_current_workflow)

        self.project_combo = QComboBox(bar)
        self.project_combo.setObjectName("projectPicker")
        try:
            self.project_combo.setToolTip(tr("mw_switch_active_project"))
        except Exception:
            pass
        try:
            self.project_combo.currentIndexChanged.connect(self._on_project_selected)
        except Exception:
            pass
        try:
            self._project_combo_updating = False
            self._refresh_project_picker()
        except Exception:
            pass
        try:
            self.project_combo.setMinimumWidth(200)
        except Exception:
            pass
        bar_layout.addWidget(self.project_combo)

        self.command_input = QLineEdit(bar)
        self.command_input.setObjectName("commandInput")
        self.command_input.setPlaceholderText(tr("mw_search_or_command"))
        self.command_input.returnPressed.connect(self._run_command_palette)
        self.command_input.setMinimumWidth(300)
        bar_layout.addWidget(self.command_input, 1)

        # mode_combo kept as hidden widget so existing sync logic still works
        self.mode_combo = QComboBox(bar)
        self.mode_combo.setObjectName("modeSwitch")
        self.mode_combo.addItem(tr("mw_beginner"), "beginner")
        self.mode_combo.addItem(tr("mw_advanced"), "expert")
        self.mode_combo.addItem(tr("mw_research"), "research")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_combo_changed)
        self.mode_combo.setVisible(False)

        # sync_status kept as hidden attribute for compatibility
        self.sync_status = QLabel(tr("mw_offline"), bar)
        self.sync_status.setObjectName("syncStatus")
        self.sync_status.setVisible(False)

        root_layout.addWidget(bar)

    def _build_shell_body(self, root_layout: "QVBoxLayout") -> None:
        body = QWidget(self.central_widget)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body.setLayout(body_layout)

        self._build_nav_panel(body_layout)
        self._build_canvas_panel(body_layout)
        # Inspector panel removed — was cluttering the layout

        root_layout.addWidget(body, 1)

    def _build_nav_panel(self, body_layout: "QHBoxLayout") -> None:
        self.nav_panel = QWidget(self.central_widget)
        self.nav_panel.setObjectName("navPanel")
        self.nav_panel.setFixedWidth(240)
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(6)
        self.nav_panel.setLayout(nav_layout)

        self._nav_buttons: dict[str, QPushButton] = {}

        def _nav_button(label: str, key: str, handler=None) -> None:
            btn = QPushButton(label, self.nav_panel)
            btn.setProperty("class", "navButton")
            if handler is None:
                btn.clicked.connect(lambda _=False, k=key: self._show_page(k))
            else:
                btn.clicked.connect(handler)
            nav_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        _nav_button("Weapon Profile", "weapons")
        _nav_button("Load Development", "develop")
        _nav_button("Components", "components")
        _nav_button("Ballistics", "ballistics")
        _nav_button("Batches", "batches")
        _nav_button("Ammo test", "ammo_test")

        nav_layout.addStretch()

        status_lbl = QLabel(tr("mw_valkyrie_labs"), self.nav_panel)
        status_lbl.setObjectName("appTitle")
        nav_layout.addWidget(status_lbl)

        body_layout.addWidget(self.nav_panel)

    def _build_canvas_panel(self, body_layout: "QHBoxLayout") -> None:
        self.canvas_panel = QWidget(self.central_widget)
        self.canvas_panel.setObjectName("canvasPanel")
        canvas_layout = QVBoxLayout()
        canvas_layout.setContentsMargins(16, 12, 16, 12)
        canvas_layout.setSpacing(12)
        self.canvas_panel.setLayout(canvas_layout)

        self.stacked_widget = QStackedWidget(self.canvas_panel)
        canvas_layout.addWidget(self.stacked_widget)

        self._register_shell_pages()

        body_layout.addWidget(self.canvas_panel, 1)

    def _build_inspector_panel(self, body_layout: "QHBoxLayout") -> None:
        self.inspector_panel = QWidget(self.central_widget)
        self.inspector_panel.setObjectName("inspectorPanel")
        self.inspector_panel.setFixedWidth(280)
        insp_layout = QVBoxLayout()
        insp_layout.setContentsMargins(12, 12, 12, 12)
        insp_layout.setSpacing(10)
        self.inspector_panel.setLayout(insp_layout)

        hdr = QLabel(tr("mw_inspector"), self.inspector_panel)
        hdr.setObjectName("appTitle")
        insp_layout.addWidget(hdr)

        context_card = QFrame(self.inspector_panel)
        context_card.setObjectName("inspectorCard")
        context_layout = QVBoxLayout()
        context_card.setLayout(context_layout)
        self.inspector_context_title = QLabel(
            tr("mw_inspector_current_area"), context_card
        )
        self.inspector_context_title.setObjectName("cardTitle")
        context_layout.addWidget(self.inspector_context_title)
        self.inspector_context_body = QLabel("", context_card)
        self.inspector_context_body.setWordWrap(True)
        self.inspector_context_body.setObjectName("cardSubtitle")
        context_layout.addWidget(self.inspector_context_body)
        insp_layout.addWidget(context_card)

        help_card = QFrame(self.inspector_panel)
        help_card.setObjectName("inspectorCard")
        help_layout = QVBoxLayout()
        help_card.setLayout(help_layout)
        self.inspector_help_title = QLabel(tr("mw_inspector_next_step"), help_card)
        self.inspector_help_title.setObjectName("cardTitle")
        help_layout.addWidget(self.inspector_help_title)
        self.inspector_help_body = QLabel("", help_card)
        self.inspector_help_body.setWordWrap(True)
        self.inspector_help_body.setObjectName("cardSubtitle")
        help_layout.addWidget(self.inspector_help_body)
        insp_layout.addWidget(help_card)

        insp_layout.addStretch()
        body_layout.addWidget(self.inspector_panel)

    def _register_shell_pages(self) -> None:
        self._page_widgets: dict[str, QWidget] = {}

        self._register_page("home", self._create_workspace_landing())
        self._register_page(
            "develop",
            self._create_section_page(
                tr("mw_nav_load_development"),
                tr("mw_develop_intro"),
                [
                    (
                        tr("mw_start_new_load_dev"),
                        self._handle_load_development_workflow,
                    ),
                    (
                        tr("mw_batch_workspace_label"),
                        lambda: self.launch_workflow("load_development_workflow"),
                    ),
                    (tr("mw_load_assistant_label"), self.launch_smart_wizard),
                ],
            ),
        )
        self._register_page(
            "weapons",
            self._create_section_page(
                tr("mw_nav_weapons"),
                tr("mw_nav_weapons_intro"),
                [
                    (tr("mw_open_weapon_profiles"), self.show_weapon_profile_editor),
                    (tr("mw_rifle_optics_label"), self.show_rifle_optic_manager),
                    (tr("mw_ammo_profiles_label"), self.show_ammo_profile_manager),
                ],
            ),
        )
        self._register_page(
            "ballistics",
            self._create_section_page(
                "Ballistics",
                tr("mw_simulate_intro"),
                [
                    (
                        tr("mw_ballistics_simulator_label"),
                        self.show_ballistics_simulator,
                    ),
                    (tr("mw_drop_chart_label"), self.show_drop_chart),
                ],
            ),
        )
        self._register_page(
            "components",
            self._create_section_page(
                "Components",
                "Overview of reloading components: powder, bullets, cases and primers.",
                [
                    (
                        "Component inventory",
                        lambda: self._activate_tab_by_text(
                            tr("mw_inventory_batches_tab")
                        ),
                    ),
                    (
                        "Import components",
                        lambda: self.launch_workflow("batch_workspace"),
                    ),
                ],
            ),
        )
        self._register_page(
            "batches",
            self._create_section_page(
                "Batches",
                "Previously loaded batches — history, statistics and export.",
                [
                    (
                        "View batches",
                        lambda: self._activate_tab_by_text(
                            tr("mw_inventory_batches_tab")
                        ),
                    ),
                    (
                        "Batch workspace",
                        lambda: self.launch_workflow("batch_workspace"),
                    ),
                    ("Export report", self.export_report_pack),
                ],
            ),
        )
        self._register_page(
            "ammo_test",
            self._create_section_page(
                "Ammo test",
                "Test and analysis of loaded ammunition — chronograph, grouping and shooting log.",
                [
                    ("Open ammo test lab", self.show_ammo_test_lab),
                    (
                        "Import chronograph",
                        lambda: self.launch_workflow("chronograph_import"),
                    ),
                    ("Analyze targets", self.show_target_analyzer),
                ],
            ),
        )

        try:
            self.stacked_widget.setCurrentWidget(self._page_widgets["home"])
            self._set_nav_active("weapons")
        except Exception:
            pass

    def _register_page(self, key: str, widget: "QWidget") -> None:
        self._page_widgets[key] = widget
        try:
            self.stacked_widget.addWidget(widget)
        except Exception:
            pass

    def _create_workspace_landing(self) -> "QWidget":
        """Rent tile-grid hjem — 6 modulfliser i 2 rader × 3 kolonner."""
        landing = QWidget(self.stacked_widget)
        outer = QVBoxLayout()
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(24)
        landing.setLayout(outer)

        title = QLabel(tr("mw_brand"), landing)
        title.setObjectName("landingHeader")
        outer.addWidget(title)

        subtitle = QLabel("Select Module", landing)
        subtitle.setObjectName("cardSubtitle")
        outer.addWidget(subtitle)

        outer.addStretch(1)

        # --- Tile grid: 2 rows × 3 cols ---
        TILES = [
            ("Weapon Profile", "Rifle, barrel and optics", "weapons"),
            ("Load Development", "Load development", "develop"),
            ("Components", "Powder, bullets, cases and primers", "components"),
            ("Ballistics", "Trajectory simulation and wind effects", "ballistics"),
            ("Batches", "Loaded batches and history", "batches"),
            ("Ammo test", "Chronograph, target analysis and shooting log", "ammo_test"),
        ]

        def _tile(title_text: str, desc_text: str, page_key: str) -> "QFrame":
            card = QFrame(landing)
            card.setObjectName("moduleCard")
            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(20, 20, 20, 20)
            card_layout.setSpacing(8)
            card.setLayout(card_layout)

            title_lbl = QLabel(title_text, card)
            title_lbl.setObjectName("cardTitle")
            card_layout.addWidget(title_lbl)

            desc_lbl = QLabel(desc_text, card)
            desc_lbl.setObjectName("cardSubtitle")
            desc_lbl.setWordWrap(True)
            card_layout.addWidget(desc_lbl)

            card_layout.addStretch()

            open_btn = QPushButton("Open", card)
            open_btn.setProperty("class", "tileOpenBtn")
            open_btn.clicked.connect(lambda _=False, k=page_key: self._show_page(k))
            card_layout.addWidget(open_btn)

            return card

        for row_tiles in [TILES[:3], TILES[3:]]:
            row_widget = QWidget(landing)
            row_layout = QHBoxLayout()
            row_layout.setSpacing(16)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_widget.setLayout(row_layout)
            for t_title, t_desc, t_key in row_tiles:
                row_layout.addWidget(_tile(t_title, t_desc, t_key))
            outer.addWidget(row_widget)

        outer.addStretch(2)
        return landing

    def _create_section_page(
        self,
        title: str,
        subtitle: str,
        actions: list[
            tuple[str, Callable[[], Any], str | None] | tuple[str, Callable[[], Any]]
        ],
    ) -> "QWidget":
        page = QWidget(self.stacked_widget)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        page.setLayout(layout)

        hdr = QLabel(title, page)
        hdr.setObjectName("landingHeader")
        layout.addWidget(hdr)

        sub = QLabel(subtitle, page)
        sub.setObjectName("cardSubtitle")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        action_row = QWidget(page)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        action_row.setLayout(action_layout)

        for item in actions:
            if len(item) == 3:
                label, handler, status = item
            else:
                label, handler = item
                status = None
            btn = QPushButton(label, action_row)
            try:
                btn.setProperty("variant", "secondary")
            except Exception:
                pass
            if status == "coming_soon":
                btn.setEnabled(False)
                btn.setToolTip(tr("mw_coming_soon"))
                btn.setText(tr("mw_with_coming_soon_suffix", label=label))
            elif status == "legacy":
                btn.setToolTip(tr("mw_legacy_workflow"))
                btn.setText(tr("mw_with_legacy_suffix", label=label))
            if handler is not None and status != "coming_soon":
                try:
                    btn.clicked.connect(handler)
                except Exception:
                    pass
            action_layout.addWidget(btn)

        action_layout.addStretch()
        layout.addWidget(action_row)

        layout.addStretch()
        return page

    def _with_legacy_suffix(self, label: str) -> str:
        return tr("mw_with_legacy_suffix", label=label)

    def _legacy_workflow_ids(self) -> set[str]:
        return {
            "primer_tools",
            "precision_tracker",
            "temperature_test",
        }

    def _show_page(self, key: str) -> None:
        widget = self._page_widgets.get(key)
        if widget is None:
            return
        try:
            self.stacked_widget.setCurrentWidget(widget)
        except Exception:
            pass
        try:
            label_map = {
                "home": tr("mw_home"),
                "develop": "Load Development",
                "weapons": "Weapon Profile",
                "components": "Components",
                "ballistics": "Ballistics",
                "batches": "Batches",
                "ammo_test": "Ammo test",
                "lab": tr("mw_nav_lab_measurement"),
                "inventory": tr("mw_nav_inventory_batches"),
                "reports": tr("mw_nav_reports_history"),
            }
            label = label_map.get(key, key.title())
            self.label_current_workflow.setText(label)
        except Exception:
            pass
        try:
            self._update_inspector_content(key)
        except Exception:
            pass
        try:
            self._set_nav_active(key)
        except Exception:
            pass

    def _update_inspector_content(self, key: str) -> None:
        context_map = {
            "home": (
                tr("mw_home"),
                tr("mw_inspector_home_body"),
                tr("mw_inspector_home_help"),
            ),
            "develop": (
                tr("mw_nav_load_development"),
                tr("mw_develop_intro"),
                tr("mw_inspector_develop_help"),
            ),
            "weapons": (
                tr("mw_nav_weapons"),
                tr("mw_nav_weapons_intro"),
                tr("mw_inspector_weapons_help"),
            ),
            "lab": (
                tr("mw_nav_lab_measurement"),
                tr("mw_nav_lab_measurement_intro"),
                tr("mw_inspector_lab_help"),
            ),
            "ballistics": (
                tr("mw_nav_ballistics"),
                tr("mw_simulate_intro"),
                tr("mw_inspector_ballistics_help"),
            ),
            "inventory": (
                tr("mw_nav_inventory_batches"),
                tr("mw_inventory_batches_intro_1"),
                tr("mw_inspector_inventory_help"),
            ),
            "reports": (
                tr("mw_nav_reports_history"),
                tr("mw_reports_intro"),
                tr("mw_inspector_reports_help"),
            ),
        }
        title, body, help_text = context_map.get(
            key,
            (
                tr("mw_home"),
                tr("mw_inspector_home_body"),
                tr("mw_inspector_home_help"),
            ),
        )
        self.inspector_context_title.setText(title)
        self.inspector_context_body.setText(body)
        self.inspector_help_body.setText(help_text)

    def _continue_current_project(self) -> None:
        try:
            self._activate_tab_by_text(tr("mw_projects_tab"))
        except Exception:
            pass
        try:
            project_name = self._project_name_from_path(
                self._get_current_project_path()
            )
            self._show_status_message(
                tr("mw_continuing_project", project_name=project_name)
            )
        except Exception:
            pass

    def _continue_latest_project_batch(self) -> None:
        latest_batch = self._get_latest_batch_for_project()
        if not latest_batch:
            self._show_status_message(tr("mw_no_project_batch_yet"))
            return
        batch_id = latest_batch.get("id")
        if not batch_id:
            self._show_status_message(tr("mw_could_not_open_latest_project_batch"))
            return
        try:
            self.show_batch_workspace(batch_id=int(batch_id))
            batch_name = str(
                latest_batch.get("batch_name", tr("mw_latest_project_batch_default"))
            )
            self._show_status_message(tr("mw_opened_batch", batch_name=batch_name))
        except Exception:
            self._show_status_message(tr("mw_could_not_open_latest_project_batch"))

    def _open_project_batch_by_id(
        self, batch_id: int, status_message: str | None = None
    ) -> None:
        if batch_id <= 0:
            self._show_status_message(tr("mw_could_not_open_latest_project_batch"))
            return
        try:
            self.show_batch_workspace(batch_id=batch_id)
            self._show_status_message(
                status_message or tr("mw_opened_latest_project_batch")
            )
        except Exception:
            self._show_status_message(tr("mw_could_not_open_latest_project_batch"))

    def _open_target_analyzer_for_pressure_review(self) -> None:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.setValue("workflow_context/analysis_focus", "pressure_review")
            settings.setValue(
                "workflow_context/analysis_focus_reason",
                tr("mw_pressure_review_focus_reason"),
            )
        except Exception:
            pass
        self.show_target_analyzer()

    def _open_chronograph_for_workflow_data_capture(self) -> None:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.setValue("workflow_context/import_focus", "workflow_data_capture")
            settings.setValue(
                "workflow_context/import_focus_reason",
                "Workflow status needs more measured data. Import chrono data to update ES, SD, and the next step.",
            )
        except Exception:
            pass
        self.launch_workflow("chronograph_import")

    def _open_batch_for_workflow_next_step(
        self,
        batch_id: int,
        status_message: str = "Opened latest project batch for the next step",
    ) -> None:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.setValue("workflow_context/batch_focus", "workflow_next_step")
            settings.setValue(
                "workflow_context/batch_focus_reason",
                "This batch is marked as ready for the next step. Review the batch data and continue the test plan.",
            )
        except Exception:
            pass
        self._open_project_batch_by_id(batch_id, status_message)

    def _fetch_count(self, table_name: str) -> int:
        db = getattr(self, "db", None)
        if db is None:
            return 0
        try:
            rows = db.execute_query(f"SELECT COUNT(1) AS count FROM {table_name}")
        except Exception:
            return 0
        if not rows:
            return 0
        try:
            return int(rows[0].get("count", 0))
        except Exception:
            try:
                return int(rows[0]["count"])
            except Exception:
                return 0

    def _count_inventory_below_threshold(
        self, component_type: str, threshold: int
    ) -> int:
        if threshold <= 0:
            return 0
        db = getattr(self, "db", None)
        if db is None:
            return 0
        try:
            rows = db.execute_query(
                """
                SELECT COUNT(1) AS count
                FROM inventory_items
                WHERE LOWER(COALESCE(component_type, '')) = LOWER(?)
                  AND COALESCE(quantity, 0) <= ?
                """,
                (component_type, threshold),
            )
        except Exception:
            return 0
        if not rows:
            return 0
        try:
            return int(rows[0].get("count", 0))
        except Exception:
            try:
                return int(rows[0]["count"])
            except Exception:
                return 0

    def _get_workspace_attention(self) -> dict[str, int]:
        settings = QSettings("ReloadingWorkshop", "ReloadingManager")
        low_powder = int(settings.value("inventory/low_powder", 500, type=int))
        low_bullet = int(settings.value("inventory/low_bullet", 100, type=int))
        low_primer = int(settings.value("inventory/low_primer", 100, type=int))
        return {
            "low_powder_count": self._count_inventory_below_threshold(
                "powder", low_powder
            ),
            "low_bullet_count": self._count_inventory_below_threshold(
                "bullet", low_bullet
            ),
            "low_primer_count": self._count_inventory_below_threshold(
                "primer", low_primer
            ),
        }

    def _count_batches_for_project(self, project_path: str) -> int:
        normalized_project_path = self._normalize_project_path(project_path)
        if not normalized_project_path:
            return 0
        db = getattr(self, "db", None)
        if db is None:
            return 0
        try:
            rows = db.execute_query(
                "SELECT analysis_json FROM batch_projects WHERE analysis_json IS NOT NULL"
            )
        except Exception:
            return 0
        count = 0
        for row in rows or []:
            try:
                analysis_json = row.get("analysis_json")
            except Exception:
                analysis_json = None
            if not analysis_json:
                continue
            try:
                analysis = json.loads(analysis_json)
            except Exception:
                continue
            if not isinstance(analysis, dict):
                continue
            workspace = analysis.get("workspace", {})
            if not isinstance(workspace, dict):
                continue
            batch_project_path = str(workspace.get("project_path", "") or "").strip()
            if not batch_project_path:
                continue
            if (
                self._normalize_project_path(batch_project_path)
                == normalized_project_path
            ):
                count += 1
        return count

    def _get_latest_batch_for_project(
        self, project_path: str | None = None
    ) -> dict[str, object] | None:
        target_project_path = self._normalize_project_path(
            project_path or self._get_current_project_path()
        )
        if not target_project_path:
            return None
        db = getattr(self, "db", None)
        if db is None:
            return None
        try:
            rows = db.execute_query(
                """
                SELECT id, batch_name, batch_number, created_date, updated_date, analysis_json
                FROM batch_projects
                ORDER BY COALESCE(updated_date, created_date) DESC, id DESC
                """
            )
        except Exception:
            return None
        for row in rows or []:
            try:
                analysis_json = row.get("analysis_json")
            except Exception:
                analysis_json = None
            if not analysis_json:
                continue
            try:
                analysis = json.loads(analysis_json)
            except Exception:
                continue
            if not isinstance(analysis, dict):
                continue
            workspace = analysis.get("workspace", {})
            if not isinstance(workspace, dict):
                continue
            batch_project_path = str(workspace.get("project_path", "") or "").strip()
            if not batch_project_path:
                continue
            if self._normalize_project_path(batch_project_path) == target_project_path:
                return {
                    "id": row.get("id"),
                    "batch_name": row.get("batch_name"),
                    "batch_number": row.get("batch_number"),
                    "created_date": row.get("created_date"),
                    "updated_date": row.get("updated_date"),
                }
        return None

    def _get_workspace_snapshot(self) -> dict[str, object]:
        current_project_path = self._get_current_project_path()
        latest_project_batch = self._get_latest_batch_for_project(current_project_path)
        workflow_status = self._get_active_workflow_status()
        return {
            "current_project_name": self._project_name_from_path(current_project_path),
            "current_project_path": current_project_path,
            "recent_projects_count": len(self._load_recent_projects()),
            "rifle_count": self._fetch_count("rifles"),
            "ammo_profile_count": self._fetch_count("ammo_profiles"),
            "batch_count": self._fetch_count("batch_projects"),
            "current_project_batch_count": self._count_batches_for_project(
                current_project_path
            ),
            "latest_project_batch_name": (
                str(latest_project_batch.get("batch_name", ""))
                if latest_project_batch
                else ""
            ),
            "latest_project_batch_id": (
                int(latest_project_batch.get("id", 0))
                if latest_project_batch and latest_project_batch.get("id")
                else 0
            ),
            "inventory_item_count": self._fetch_count("inventory_items"),
            "loading_session_count": self._fetch_count("loading_sessions"),
            "shooting_session_count": self._fetch_count("shooting_sessions"),
            "active_workflow_name": str(workflow_status.get("workflow_name", "") or ""),
            "active_workflow_setup_label": str(
                workflow_status.get("setup_label", "") or ""
            ),
            "active_workflow_title": str(workflow_status.get("title", "") or ""),
            "active_workflow_message": str(workflow_status.get("message", "") or ""),
            "active_workflow_level": str(workflow_status.get("level", "") or ""),
            "active_workflow_confidence_label": str(
                workflow_status.get("confidence_label", "") or ""
            ),
            "active_workflow_confidence_message": str(
                workflow_status.get("confidence_message", "") or ""
            ),
            "active_workflow_robustness_title": str(
                workflow_status.get("robustness_title", "") or ""
            ),
            "active_workflow_robustness_message": str(
                workflow_status.get("robustness_message", "") or ""
            ),
            "active_workflow_robustness_level": str(
                workflow_status.get("robustness_level", "") or ""
            ),
            "active_workflow_robustness_score": str(
                workflow_status.get("robustness_score", "") or ""
            ),
            "active_workflow_robustness_uncertainty_message": str(
                workflow_status.get("robustness_uncertainty_message", "") or ""
            ),
            "active_workflow_next_test_title": str(
                workflow_status.get("next_test_title", "") or ""
            ),
            "active_workflow_next_test_action": str(
                workflow_status.get("next_test_action", "") or ""
            ),
            "active_workflow_next_test_confidence_label": str(
                workflow_status.get("next_test_confidence_label", "") or ""
            ),
            "active_workflow_next_test_confidence_message": str(
                workflow_status.get("next_test_confidence_message", "") or ""
            ),
            "active_workflow_impact_title": str(
                workflow_status.get("impact_title", "") or ""
            ),
            "active_workflow_impact_message": str(
                workflow_status.get("impact_message", "") or ""
            ),
            "active_workflow_impact_level": str(
                workflow_status.get("impact_level", "") or ""
            ),
            "active_workflow_evidence_quality_title": str(
                workflow_status.get("evidence_quality_title", "") or ""
            ),
            "active_workflow_evidence_quality_message": str(
                workflow_status.get("evidence_quality_message", "") or ""
            ),
            "active_workflow_evidence_quality_level": str(
                workflow_status.get("evidence_quality_level", "") or ""
            ),
            "active_workflow_evidence_quality_checks": list(
                workflow_status.get("evidence_quality_checks", []) or []
            ),
        }

    def _get_active_workflow_status(self) -> dict[str, object]:
        try:
            from ..tools.load_session_runtime_service import (
                build_active_workflow_context_from_settings,
            )

            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            workflow_context = build_active_workflow_context_from_settings(
                settings,
                getattr(self, "db", None),
            )
            workflow_id = workflow_context.get("workflow_id")
            if workflow_id in (None, ""):
                return {}

            if self.db is None:
                return {}

            workflow = self.db.get_by_id("load_development_workflows", workflow_id)
            if not workflow:
                return {}

            module = importlib.import_module("src.modules.load_development_workflow")
            collect = getattr(module, "collect_workflow_observations", None)
            summarize = getattr(module, "build_workflow_readiness_summary", None)
            build_robustness = getattr(
                module, "build_workflow_component_robustness", None
            )
            build_next_test = getattr(
                module, "build_workflow_next_test_recommendation", None
            )
            build_impact_window = getattr(module, "build_workflow_impact_window", None)
            build_evidence_quality = getattr(
                module, "build_workflow_evidence_quality", None
            )
            build_calibration = getattr(
                module, "build_workflow_calibration_summary", None
            )
            build_internal_ballistics = getattr(
                module, "build_workflow_internal_ballistics_summary", None
            )
            build_environment = getattr(module, "_build_workflow_environment", None)
            if collect is None or summarize is None:
                return {}

            observations = collect(self.db, workflow)
            readiness = summarize(workflow, observations)
            robustness = (
                build_robustness(self.db, workflow)
                if callable(build_robustness)
                else {}
            )
            next_test = (
                build_next_test(workflow, observations, self.db)
                if callable(build_next_test)
                else {}
            )
            impact_window = (
                build_impact_window(self.db, workflow, observations)
                if callable(build_impact_window)
                else {}
            )
            evidence_quality = (
                build_evidence_quality(workflow, observations, self.db)
                if callable(build_evidence_quality)
                else {}
            )
            calibration = (
                build_calibration(self.db, workflow)
                if callable(build_calibration)
                else {}
            )
            internal_ballistics = (
                build_internal_ballistics(self.db, workflow)
                if callable(build_internal_ballistics)
                else {}
            )
            internal_ballistics_checks = list(internal_ballistics.get("checks") or [])
            internal_ballistics_case_context = [
                str(item)
                for item in internal_ballistics_checks
                if any(
                    marker in str(item or "").strip().lower()
                    for marker in ("valgt hylse", "trimlengde")
                )
            ]
            environment_summary = {}
            if callable(build_environment):
                try:
                    environment = build_environment(observations)
                    environment_summary = environment.summary()
                except Exception:
                    environment_summary = {}
            report_plot_x: list[str] = []
            report_plot_y: list[float] = []
            report_plot_xlabel = "Serie"
            report_plot_ylabel = "Hastighet (fps)"
            for index, row in enumerate(
                observations.get("chronograph_sessions") or [], start=1
            ):
                velocity = row.get("avg_velocity_fps")
                if not isinstance(velocity, (int, float)):
                    continue
                report_plot_x.append(
                    str(
                        row.get("session_date")
                        or row.get("session_name")
                        or f"Serie {index}"
                    )
                )
                report_plot_y.append(float(velocity))
            if not report_plot_y:
                report_plot_ylabel = "Gruppe (mm)"
                for index, row in enumerate(
                    observations.get("shooting_sessions") or [], start=1
                ):
                    group_size = row.get("best_group_mm") or row.get("avg_group_mm")
                    if not isinstance(group_size, (int, float)):
                        continue
                    report_plot_x.append(str(row.get("date") or f"Serie {index}"))
                    report_plot_y.append(float(group_size))
            chronograph_summary: list[str] = []
            for row in (observations.get("chronograph_sessions") or [])[:5]:
                chronograph_summary.append(
                    (
                        f"{row.get('session_date') or row.get('session_name') or '-'}: "
                        f"{float(row.get('avg_velocity_fps')):.0f} fps, "
                        f"ES {float(row.get('es_fps')):.0f}, SD {float(row.get('sd_fps')):.1f}"
                    )
                    if isinstance(row.get("avg_velocity_fps"), (int, float))
                    and isinstance(row.get("es_fps"), (int, float))
                    and isinstance(row.get("sd_fps"), (int, float))
                    else str(row.get("session_date") or row.get("session_name") or "-")
                )
            shooting_summary: list[str] = []
            for row in (observations.get("shooting_sessions") or [])[:5]:
                group_value = row.get("best_group_mm")
                if not isinstance(group_value, (int, float)):
                    group_value = row.get("avg_group_mm")
                shooting_summary.append(
                    (
                        f"{row.get('date') or '-'}: gruppe {float(group_value):.1f} mm, "
                        f"{int(row.get('rounds_fired') or 0)} skudd"
                    )
                    if isinstance(group_value, (int, float))
                    else str(row.get("date") or "-")
                )
            accuracy_test_summary: list[str] = []
            for row in (observations.get("accuracy_test_sessions") or [])[:5]:
                avg_group = row.get("average_group_size_mm")
                best_group = row.get("best_group_mm")
                avg_velocity = row.get("average_velocity_fps")
                parts = [str(row.get("test_date") or "-")]
                if isinstance(avg_group, (int, float)):
                    parts.append(f"avg {float(avg_group):.1f} mm")
                if isinstance(best_group, (int, float)):
                    parts.append(f"best {float(best_group):.1f} mm")
                if isinstance(avg_velocity, (int, float)):
                    parts.append(f"{float(avg_velocity):.0f} fps")
                accuracy_test_summary.append(", ".join(parts))
            pressure_notes = [
                str(note).strip()
                for note in (observations.get("pressure_notes") or [])[:5]
                if str(note or "").strip()
            ]
            uncertainty_summary: list[str] = []
            confidence_message = str(
                readiness.get("confidence_message", "") or ""
            ).strip()
            if confidence_message:
                uncertainty_summary.append(f"Readiness: {confidence_message}")
            robustness_uncertainty = str(
                robustness.get("uncertainty_message", "") or ""
            ).strip()
            if robustness_uncertainty:
                uncertainty_summary.append(f"Robustness: {robustness_uncertainty}")
            impact_confidence_message = str(
                impact_window.get("confidence_message", "") or ""
            ).strip()
            if impact_confidence_message:
                uncertainty_summary.append(f"Impact: {impact_confidence_message}")
            setup_label = MainWindow._get_active_workflow_setup_label(self)
            return {
                "workflow_name": str(workflow.get("name", "") or ""),
                "setup_label": setup_label,
                "usage_profile": str(workflow.get("usage_profile", "") or ""),
                "title": str(readiness.get("title", "") or ""),
                "message": MainWindow._apply_setup_context_to_message(
                    self,
                    readiness.get("message", ""),
                    setup_label,
                ),
                "level": str(readiness.get("level", "") or ""),
                "confidence_label": str(readiness.get("confidence_label", "") or ""),
                "confidence_message": str(
                    readiness.get("confidence_message", "") or ""
                ),
                "robustness_title": str(robustness.get("title", "") or ""),
                "robustness_message": str(robustness.get("message", "") or ""),
                "robustness_level": str(robustness.get("level", "") or ""),
                "robustness_score": str(robustness.get("score", "") or ""),
                "robustness_uncertainty_message": str(
                    robustness.get("uncertainty_message", "") or ""
                ),
                "next_test_title": str(next_test.get("title", "") or ""),
                "next_test_action": MainWindow._apply_setup_context_to_message(
                    self,
                    next_test.get("action", ""),
                    setup_label,
                ),
                "next_test_confidence_label": str(
                    next_test.get("confidence_label", "") or ""
                ),
                "next_test_confidence_message": str(
                    next_test.get("confidence_message", "") or ""
                ),
                "impact_title": str(impact_window.get("title", "") or ""),
                "impact_message": MainWindow._apply_setup_context_to_message(
                    self,
                    impact_window.get("message", ""),
                    setup_label,
                ),
                "impact_level": str(impact_window.get("level", "") or ""),
                "impact_checks": list(impact_window.get("checks") or []),
                "impact_drag_model": str(impact_window.get("drag_model", "") or ""),
                "impact_bc_used": str(impact_window.get("bc_used", "") or ""),
                "impact_bc_segment": str(
                    impact_window.get("bc_segment_label", "") or ""
                ),
                "impact_density_altitude_m": str(
                    impact_window.get("density_altitude_m", "") or ""
                ),
                "impact_confidence_label": str(
                    impact_window.get("confidence_label", "") or ""
                ),
                "impact_confidence_message": str(
                    impact_window.get("confidence_message", "") or ""
                ),
                "pressure_notes": pressure_notes,
                "uncertainty_summary": uncertainty_summary,
                "evidence_quality_title": str(evidence_quality.get("title", "") or ""),
                "evidence_quality_message": str(
                    evidence_quality.get("message", "") or ""
                ),
                "evidence_quality_level": str(evidence_quality.get("level", "") or ""),
                "evidence_quality_checks": list(evidence_quality.get("checks") or []),
                "calibration_title": str(calibration.get("title", "") or ""),
                "calibration_message": str(calibration.get("message", "") or ""),
                "calibration_level": str(calibration.get("level", "") or ""),
                "calibration_checks": list(calibration.get("checks") or []),
                "calibration_score": str(calibration.get("score", "") or ""),
                "internal_ballistics_title": str(
                    internal_ballistics.get("title", "") or ""
                ),
                "internal_ballistics_message": str(
                    internal_ballistics.get("message", "") or ""
                ),
                "internal_ballistics_level": str(
                    internal_ballistics.get("level", "") or ""
                ),
                "internal_ballistics_checks": internal_ballistics_checks,
                "internal_ballistics_metrics": list(
                    internal_ballistics.get("metrics") or []
                ),
                "internal_ballistics_case_context": internal_ballistics_case_context,
                "environment_title": "Environment" if environment_summary else "",
                "environment_message": (
                    (
                        f"Temp {float(environment_summary.get('temperature_c', 15.0)):.1f} C, "
                        f"pressure {float(environment_summary.get('pressure_hpa', 1013.25)):.1f} hPa, "
                        f"RH {float(environment_summary.get('humidity_percent', 50.0)):.0f}%, "
                        f"DA approx. {float(environment_summary.get('density_altitude_m', 0.0)):.0f} m."
                    )
                    if environment_summary
                    else ""
                ),
                "environment_checks": (
                    [
                        (
                            "Environment basis: measured"
                            if str(
                                environment_summary.get("temperature_source", "assumed")
                            )
                            == "measured"
                            else "Environment basis: assumed standard atmosphere"
                        ),
                        f"Density ratio: {float(environment_summary.get('density_ratio', 1.0)):.3f}",
                    ]
                    if environment_summary
                    else []
                ),
                "report_plot_x": report_plot_x,
                "report_plot_y": report_plot_y,
                "report_plot_xlabel": report_plot_xlabel,
                "report_plot_ylabel": report_plot_ylabel,
                "chronograph_summary": chronograph_summary,
                "shooting_summary": shooting_summary,
                "accuracy_test_summary": accuracy_test_summary,
            }
        except Exception:
            return {}

    def _get_workflow_action_recommendation(
        self,
    ) -> tuple[str, Callable[[], None]] | None:
        status = self._get_active_workflow_status()
        level = str(status.get("level", "") or "")
        if not level:
            return None
        robustness_level = str(status.get("robustness_level", "") or "")
        try:
            robustness_score = int(float(status.get("robustness_score", "") or 0))
        except Exception:
            robustness_score = 0
        workspace_snapshot = self._get_workspace_snapshot()
        latest_project_batch_id = int(
            workspace_snapshot.get("latest_project_batch_id", 0) or 0
        )
        if level == "stop":
            return (
                tr("mw_recommend_pressure_review"),
                self._open_target_analyzer_for_pressure_review,
            )
        if level == "ready":
            if robustness_level == "critical" or (
                robustness_score > 0 and robustness_score < 50
            ):
                if latest_project_batch_id > 0:
                    return (
                        tr("mw_recommend_verify_batch_with_chrono"),
                        lambda: self._open_project_batch_by_id(
                            latest_project_batch_id,
                            tr("mw_opened_batch_for_conservative_verification"),
                        ),
                    )
                return (
                    tr("mw_recommend_import_chrono_before_next_batch"),
                    self._open_chronograph_for_workflow_data_capture,
                )
            if robustness_level == "warning" or (
                robustness_score > 0 and robustness_score < 70
            ):
                if latest_project_batch_id > 0:
                    return (
                        tr("mw_recommend_open_batch_for_control_series"),
                        lambda: self._open_batch_for_workflow_next_step(
                            latest_project_batch_id,
                            tr("mw_opened_batch_for_control_series"),
                        ),
                    )
                return (
                    tr("mw_recommend_run_short_control_series"),
                    self._open_chronograph_for_workflow_data_capture,
                )
            usage_profile = str(status.get("usage_profile", "") or "")
            if usage_profile.startswith("hunting"):
                if latest_project_batch_id > 0:
                    return (
                        tr("mw_recommend_open_batch_for_hunting_verification"),
                        lambda: self._open_batch_for_workflow_next_step(
                            latest_project_batch_id,
                            tr("mw_opened_batch_for_hunting_verification"),
                        ),
                    )
                return (
                    tr("mw_recommend_run_hunting_verification"),
                    self._continue_latest_project_batch,
                )
            if usage_profile == "training":
                if latest_project_batch_id > 0:
                    return (
                        tr("mw_recommend_open_batch_for_robust_control"),
                        lambda: self._open_batch_for_workflow_next_step(
                            latest_project_batch_id,
                            tr("mw_opened_batch_for_robust_control"),
                        ),
                    )
                return (
                    tr("mw_recommend_run_robust_control"),
                    self._continue_latest_project_batch,
                )
            if latest_project_batch_id > 0:
                return (
                    tr("mw_recommend_open_latest_batch"),
                    lambda: self._open_batch_for_workflow_next_step(
                        latest_project_batch_id,
                        tr("mw_opened_batch_for_next_step"),
                    ),
                )
            return (
                tr("mw_continue_project_batch_label"),
                self._continue_latest_project_batch,
            )
        if latest_project_batch_id > 0:
            return (
                tr("mw_recommend_open_batch_before_chrono_import"),
                lambda: self._open_project_batch_by_id(
                    latest_project_batch_id,
                    tr("mw_opened_batch_for_more_measurement_data"),
                ),
            )
        return (
            tr("mw_import_chronograph_data_label"),
            self._open_chronograph_for_workflow_data_capture,
        )

    def _set_nav_active(self, key: str) -> None:
        for k, btn in (self._nav_buttons or {}).items():
            try:
                btn.setProperty("active", "true" if k == key else "false")
                style = btn.style()
                if style is not None:
                    style.unpolish(btn)
                    style.polish(btn)
            except Exception:
                pass

    def _build_command_map(self) -> None:
        self._command_map = {
            "home": lambda: self._show_page("home"),
            "workspace": lambda: self._show_page("home"),
            "load development": lambda: self._show_page("develop"),
            "develop": lambda: self._show_page("develop"),
            "weapons": lambda: self._show_page("weapons"),
            "lab": lambda: self._show_page("lab"),
            "measurement": lambda: self._show_page("lab"),
            "ballistics": lambda: self._show_page("ballistics"),
            "inventory": lambda: self._show_page("inventory"),
            "batches": lambda: self._show_page("inventory"),
            "reports": lambda: self._show_page("reports"),
            "history": lambda: self._show_page("reports"),
            "all tools": self.show_all_tools,
            "settings": self._open_settings_view,
            "chronograph": lambda: self.launch_workflow("chronograph_import"),
            "load": lambda: self.launch_workflow("load_development_workflow"),
            "weapon profiles": self.show_weapon_profile_editor,
            "weapon profile": self.show_weapon_profile_editor,
            "new project": self.show_new_project_dialog,
            "project folder": self.open_active_project_folder,
            "open project": self.open_active_project_folder,
            "setup": self.show_first_run_setup,
            "setup wizard": self.show_first_run_setup,
            "first run setup": self.show_first_run_setup,
            "quick tour": self.show_quick_tour,
            "user guide": self.open_docs_folder,
            "docs": self.open_docs_folder,
            "keyboard shortcuts": self.show_keyboard_shortcuts,
            "shortcuts": self.show_keyboard_shortcuts,
            "logs": self.open_logs_folder,
            "config": self.open_config_folder,
        }

    def _run_command_palette(self) -> None:
        try:
            text = self.command_input.text().strip().lower()
        except Exception:
            text = ""
        if not text:
            return
        for key, handler in self._command_map.items():
            if text == key or text in key:
                try:
                    handler()
                    self.command_input.clear()
                    return
                except Exception:
                    break
            self._show_status_message(tr("mw_command_not_found", command=text))

    def _focus_command_palette(self) -> None:
        try:
            self.command_input.setFocus()
            self.command_input.selectAll()
        except Exception:
            pass

    def _sync_mode_combo_from_settings(self) -> None:
        try:
            val = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "ui/mode", "beginner"
            )
        except Exception:
            val = "beginner"
        try:
            idx = self.mode_combo.findData(str(val))
            if idx >= 0:
                self.mode_combo.setCurrentIndex(idx)
        except Exception:
            pass

    def _on_mode_combo_changed(self) -> None:
        try:
            mode = self.mode_combo.currentData()
        except Exception:
            mode = "beginner"

        try:
            um = getattr(self, "_UserMode", None)
            manager = getattr(self, "mode_manager", None)
            if manager is not None and um is not None:
                if str(mode).lower() == "research" and hasattr(um, "RESEARCH"):
                    manager.set_mode(um.RESEARCH)
                elif str(mode).lower() == "expert" and hasattr(um, "EXPERT"):
                    manager.set_mode(um.EXPERT)
                else:
                    manager.set_mode(getattr(um, "BEGINNER", 0))
            else:
                QSettings("ReloadingWorkshop", "ReloadingManager").setValue(
                    "ui/mode", mode
                )
                try:
                    self._apply_ui_mode_to_actions()
                    self._apply_ui_mode_to_nav()
                except Exception:
                    pass
        except Exception:
            pass

    def _set_mode_from_menu(self, mode: str) -> None:
        """Sett bruker-modus fra Innstillinger-menyen."""
        try:
            idx = self.mode_combo.findData(mode)
            if idx >= 0:
                self.mode_combo.setCurrentIndex(idx)
            else:
                self._on_mode_combo_changed()
        except Exception:
            pass

    def _open_settings_view(self) -> None:
        try:
            self.show_all_tools()
            self._activate_tab_by_text(tr("mw_settings"))
        except Exception:
            pass

    def _activate_tab_by_text(self, label: str) -> bool:
        if not hasattr(self, "tabs"):
            return False
        alias_map = {
            "terrengkart": "Ballistics",
            "logg": "Projects",
            "analyse": "Lab and testing",
            "ammunisjon": "Load Development",
            "dashboard": "Load Development",
        }
        label = alias_map.get(label.strip().lower(), label)
        try:
            for i in range(self.tabs.count()):
                try:
                    if label.lower() in self.tabs.tabText(i).lower():
                        self.tabs.setCurrentIndex(i)
                        return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def apply_theme_from_settings(self) -> None:
        """Read saved settings and apply a matching stylesheet to the app.

        This ensures that changes made in the settings dialog are reflected
        on next startup and when apply_user_settings() is called.
        """
        app_settings: Any | None = None
        try:
            if os.environ.get("VALKYRIE_SAFE_UI", "").lower() in ("1", "true"):
                return
            app_settings = getattr(
                importlib.import_module("HjemmeladingApp.settings"), "settings", None
            )
        except Exception:
            app_settings = None

        try:
            cfg = app_settings.get() if app_settings else {}
            try:
                qs = QSettings("ReloadingWorkshop", "ReloadingManager")
                theme = qs.value("theme", None)
                btn_style = qs.value("button_style", None)
                ui_density = qs.value("ui/density", None)
                if theme is not None:
                    cfg["theme"] = theme
                if btn_style is not None:
                    cfg["button_style"] = btn_style
                if ui_density is not None:
                    cfg["ui_density"] = ui_density
            except Exception:
                pass
            css = _build_theme_css_from_cfg(cfg)
            marker_start = "/* user_theme_start */"
            marker_end = "/* user_theme_end */"
            # Merge with existing stylesheet while replacing prior user theme overrides.
            try:
                existing = self.styleSheet() or ""
                start = existing.find(marker_start)
                if start != -1:
                    end = existing.find(marker_end, start)
                    if end != -1:
                        existing = existing[:start] + existing[end + len(marker_end) :]
                    else:
                        existing = existing[:start]
                combined = existing.rstrip()
                combined += "\n" + marker_start + "\n" + css + "\n" + marker_end
                self.setStyleSheet(combined)
            except Exception:
                self.setStyleSheet(css)
        except Exception:
            logger.exception("Error applying theme from settings")

    def _show_status_message(self, msg: str, timeout: int = 0) -> None:
        """Safely show a message in the status bar regardless of attribute/method shape."""
        sb: Any = None
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

    def _write_startup_trace(self, message: str) -> None:
        try:
            from datetime import datetime as _dt
            from pathlib import Path as _P

            trace_file = _P(get_log_dir()) / "startup_trace.log"
            with open(trace_file, "a", encoding="utf-8") as _tf:
                _tf.write(f"startup: {message} time={_dt.utcnow().isoformat()}\n")
        except Exception:
            pass

    def _init_mode_manager(self) -> None:
        # No local shims here — rely on module-level widget classes.
        try:
            mode_manager_module = importlib.import_module("src.modules.mode_manager")
            UserMode = getattr(mode_manager_module, "UserMode")
            UserModeManager = getattr(mode_manager_module, "UserModeManager")
        except Exception:
            try:
                mode_manager_module = importlib.import_module(
                    "HjemmeladingApp.utils.mode_manager"
                )
                UserMode = getattr(mode_manager_module, "UserMode")
                UserModeManager = getattr(mode_manager_module, "UserModeManager")
            except Exception:
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

        try:
            self.mode_manager = UserModeManager()
        except Exception:
            self.mode_manager = None
        try:
            self._UserMode = UserMode
        except Exception:
            self._UserMode = type("UserMode", (), {"BEGINNER": 0, "EXPERT": 1})

    def _init_database_handle(self) -> None:
        try:
            from ..database import get_database

            self.db = get_database()
        except Exception:
            self.db = None

    def _connect_mode_manager(self) -> None:
        try:
            if self.mode_manager is None:
                return
            self.mode_manager.mode_changed.connect(
                getattr(self, "on_mode_changed", lambda *a, **k: None)
            )
        except Exception:
            pass

        try:
            self.apply_ui_mode_from_settings()
        except Exception:
            pass

    def _apply_language_setting(self) -> None:
        try:
            from src.utils.i18n import normalize_language_code

            language = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "language", "en"
            )
            lang_code = normalize_language_code(language)
            try:
                try:
                    set_language = getattr(
                        importlib.import_module("src.i18n"), "set_language"
                    )
                except Exception:
                    set_language = getattr(
                        importlib.import_module("HjemmeladingApp.i18n"), "set_language"
                    )
                set_language(lang_code)
            except Exception:
                pass
        except Exception:
            pass

    def _ensure_ui_initialized(self) -> None:
        if getattr(self, "_ui_initialized", False):
            return
        self.init_ui()

    def _apply_theme_after_ui(self) -> None:
        try:
            self.apply_theme_from_settings()
        except Exception:
            logger.exception("Failed to apply saved theme settings")

    def _init_workspace_area(self) -> None:
        try:
            if getattr(self, "stacked_widget", None) is not None:
                self.workspace_area = self.stacked_widget
            else:
                self.workspace_area = QStackedWidget(self)
        except Exception:

            class _StubWS:
                def addWidget(self, *_a, **_k):
                    return None

                def setCurrentWidget(self, *_a, **_k):
                    return None

            self.workspace_area = _StubWS()

    def _init_workflow_hub_placeholder(self) -> None:
        try:
            placeholder = QWidget(self.stacked_widget)
            placeholder.setObjectName("workflowHubPlaceholder")
            ph_layout = QVBoxLayout()
            ph_lbl = QLabel(tr("mw_workflow_hub_loading"), placeholder)
            ph_layout.addWidget(ph_lbl)
            placeholder.setLayout(ph_layout)
            self.stacked_widget.addWidget(placeholder)
            self.workflow_hub = None
            self.workflow_hub_placeholder = placeholder
        except Exception as e:
            logger.exception("Failed to add WorkflowHub placeholder: %s", e)
            self.workflow_hub = None

    def _init_legacy_tabs(self) -> None:
        try:
            self.tabs_widget = QWidget(self.stacked_widget)
            tabs_layout = QVBoxLayout()
            self.tabs_widget.setLayout(tabs_layout)

            legacy_banner = QLabel(tr("mw_legacy_tools_banner"), self.tabs_widget)
            legacy_banner.setObjectName("legacyBanner")
            legacy_banner.setWordWrap(True)
            legacy_banner.setStyleSheet(
                "background-color: #f6e9c5; color: #6b4a00; padding: 6px 10px; border-radius: 6px;"
            )
            tabs_layout.addWidget(legacy_banner)

            legacy_intro = QLabel(tr("mw_legacy_tools_intro"), self.tabs_widget)
            legacy_intro.setObjectName("cardSubtitle")
            legacy_intro.setWordWrap(True)
            tabs_layout.addWidget(legacy_intro)

            self.tabs = QTabWidget()
            tabs_layout.addWidget(self.tabs)

            self.stacked_widget.addWidget(self.tabs_widget)
            try:
                self._tabs_page_index = self.stacked_widget.indexOf(self.tabs_widget)
            except Exception:
                self._tabs_page_index = None

            self.create_tabs()
        except Exception:
            pass

    def _start_on_landing(self) -> None:
        try:
            self.stacked_widget.setCurrentIndex(0)
        except Exception:
            pass

    def _schedule_stray_widget_cleanup(self) -> None:
        try:

            def _force_reparent():
                try:
                    if not (_HEADLESS or _STRAY_WIDGET_CLEANUP):
                        return
                    app = QApplication.instance()
                    if not app:
                        return
                    for w in list(app.topLevelWidgets()):
                        try:
                            if w is self:
                                continue
                            try:
                                flags = w.windowFlags()
                                if flags & Qt.WindowType.Popup:
                                    continue
                                if flags & Qt.WindowType.ToolTip:
                                    continue
                                if flags & Qt.WindowType.Tool:
                                    continue
                                if flags & Qt.WindowType.Dialog:
                                    continue
                            except Exception:
                                pass
                            try:
                                if w.parent() is not None:
                                    continue
                            except Exception:
                                pass
                            try:
                                w.setParent(self)
                            except Exception:
                                pass
                            try:
                                w.hide()
                            except Exception:
                                pass
                            try:
                                w.deleteLater()
                            except Exception:
                                pass
                        except Exception:
                            pass
                except Exception:
                    pass

            for ms in (100, 500, 1000, 3000, 8000):
                try:
                    QTimer.singleShot(ms, _force_reparent)
                except Exception:
                    pass
        except Exception:
            pass

    def apply_user_settings(self):
        """Safely apply per-user settings and initialize mode/shortcuts.

        Uses archived logic but provides safe fallbacks if modules are missing.
        """
        self._write_startup_trace("enter_apply_user_settings")
        logger.info("apply_user_settings: start")
        try:
            self._write_startup_trace("apply_user_settings step=mode_manager")
            logger.info("apply_user_settings: mode_manager")
            self._init_mode_manager()
            self._init_database_handle()

            self._write_startup_trace("apply_user_settings step=ui_mode")
            logger.info("apply_user_settings: ui_mode")
            self._connect_mode_manager()

            self._write_startup_trace("apply_user_settings step=init_ui")
            logger.info("apply_user_settings: init_ui")
            # Initialize keyboard shortcuts manager (will be set up after UI is created)
            self.shortcuts_manager = None
            self._apply_language_setting()

            # Finally, initialize the full UI (only once)
            self._ensure_ui_initialized()

            self._write_startup_trace("apply_user_settings step=theme")
            logger.info("apply_user_settings: theme")
            # After UI is created, apply any saved user theme/settings
            self._apply_theme_after_ui()

            self._write_startup_trace("apply_user_settings step=workspace_area")
            logger.info("apply_user_settings: workspace_area")
        except Exception:
            # Let caller handle logging and UI notification
            raise

        # Create a workspace area where dialogs/widgets can be embedded
        # This prevents code from creating new top-level windows and allows
        # show_* helpers to add widgets into a stacked area instead of
        # calling .show() which would create transient top-levels.
        self._init_workspace_area()

        # Page 1: Workflow Hub placeholder — create the heavy hub lazily
        self._init_workflow_hub_placeholder()

        self._write_startup_trace("apply_user_settings step=create_tabs")
        logger.info("apply_user_settings: create_tabs")

        # Page 2: All Tools (legacy tabs)
        self._init_legacy_tabs()

        self._write_startup_trace("apply_user_settings step=tabs_done")
        logger.info("apply_user_settings: tabs_done")

        # Start on landing page (do not instantiate heavy hub at startup)
        self._start_on_landing()

        self._write_startup_trace("exit_apply_user_settings")
        logger.info("apply_user_settings: end")

        try:
            self._maybe_show_first_run_setup()
        except Exception:
            pass

        # Defensive reparenting: schedule pruning of any stray top-level widgets
        self._schedule_stray_widget_cleanup()

    def create_menu(self):
        """Oppretter menylinjen"""
        menubar = self.menuBar()
        _tr = globals().get("tr", lambda k, **kw: k)

        # Fil-meny
        # Create menus with an explicit parent to avoid transient top-level
        # QMenu objects during startup (some Qt bindings construct the
        # QMenu before attaching it to the menubar). Creating with `self`
        # as parent ensures they are child widgets of the main window.
        file_menu = QMenu(_tr("menu_file"), self)
        menubar.addMenu(file_menu)

        new_action = QAction(tr("mw_new_project"), self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.show_new_project_dialog)
        file_menu.addAction(new_action)

        open_project_action = QAction(tr("mw_open_project_folder"), self)
        open_project_action.triggered.connect(self.open_active_project_folder)
        file_menu.addAction(open_project_action)

        # Resume saved workflows (user-triggered)
        resume_action = QAction(tr("mw_resume_saved_workflows"), self)
        resume_action.triggered.connect(self.open_resume_dialog)
        file_menu.addAction(resume_action)

        file_menu.addSeparator()

        export_action = QAction(tr("menu_export"), self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_report_pack)
        file_menu.addAction(export_action)

        exit_action = QAction(tr("menu_exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Verktøy-meny
        tools_menu = QMenu(tr("menu_tools"), self)
        menubar.addMenu(tools_menu)

        command_action = QAction(tr("mw_command_palette"), self)
        command_action.setShortcut("Ctrl+K")
        command_action.triggered.connect(self._focus_command_palette)
        tools_menu.addAction(command_action)

        tools_menu.addSeparator()

        simulator_action = QAction(tr("mw_menu_ballistics_simulator"), self)
        simulator_action.setShortcut("Ctrl+B")
        simulator_action.triggered.connect(self.show_ballistics_simulator)
        tools_menu.addAction(simulator_action)

        calc_action = QAction(tr("mw_menu_zero_shift_calculator"), self)
        calc_action.triggered.connect(self.show_zero_shift_calculator)
        tools_menu.addAction(calc_action)

        seating_action = QAction(tr("mw_menu_seating_depth_calculator"), self)
        tools_menu.addAction(seating_action)

        anneal_action = QAction(tr("mw_menu_case_annealing"), self)
        tools_menu.addAction(anneal_action)

        weapon_profiles_action = QAction(tr("mw_menu_weapon_profiles"), self)
        weapon_profiles_action.triggered.connect(self.show_weapon_profile_editor)
        tools_menu.addAction(weapon_profiles_action)

        field_planning_action = QAction(
            "🗺 Field Planning (DOPE / Range / Hunting)", self
        )
        field_planning_action.setShortcut("Ctrl+F")
        field_planning_action.triggered.connect(self.show_field_planning)
        tools_menu.addAction(field_planning_action)

        chrono_action = QAction("📡 Kronograf — hastighetsregistrering", self)
        chrono_action.setShortcut("Ctrl+H")
        chrono_action.triggered.connect(self.show_chronograph)
        tools_menu.addAction(chrono_action)

        cdm_action = QAction("🎯 CDM BC-kalibrering — tilbakeberegn fra drop", self)
        cdm_action.triggered.connect(self.show_cdm_calibration)
        tools_menu.addAction(cdm_action)

        # Track actions so we can hide/show based on user mode.
        try:
            self._advanced_actions = [
                export_action,
                simulator_action,
                calc_action,
                seating_action,
                anneal_action,
                weapon_profiles_action,
                field_planning_action,
            ]
        except Exception:
            self._advanced_actions = []

        # Innstillinger-meny
        settings_menu = QMenu(tr("menu_settings"), self)
        menubar.addMenu(settings_menu)

        settings_action = QAction(tr("menu_settings_action"), self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings_view)
        settings_menu.addAction(settings_action)

        settings_menu.addSeparator()

        mode_beginner = QAction(tr("menu_mode_beginner"), self)
        mode_beginner.triggered.connect(lambda: self._set_mode_from_menu("beginner"))
        settings_menu.addAction(mode_beginner)

        mode_expert = QAction(tr("menu_mode_expert"), self)
        mode_expert.triggered.connect(lambda: self._set_mode_from_menu("expert"))
        settings_menu.addAction(mode_expert)

        mode_research = QAction(tr("menu_mode_research"), self)
        mode_research.triggered.connect(lambda: self._set_mode_from_menu("research"))
        settings_menu.addAction(mode_research)

        # Hjelp-meny
        help_menu = menubar.addMenu(_tr("menu_help"))

        setup_action = QAction(tr("mw_first_run_setup"), self)
        setup_action.triggered.connect(self.show_first_run_setup)
        help_menu.addAction(setup_action)

        guide_action = QAction(_tr("menu_user_guide"), self)
        guide_action.triggered.connect(self.open_docs_folder)
        help_menu.addAction(guide_action)

        shortcuts_action = QAction(tr("mw_keyboard_shortcuts_title"), self)
        shortcuts_action.triggered.connect(self.show_keyboard_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        quick_tour_action = QAction(tr("mw_quick_tour"), self)
        quick_tour_action.triggered.connect(self.show_quick_tour)
        help_menu.addAction(quick_tour_action)

        open_logs_action = QAction(tr("mw_open_logs_folder"), self)
        open_logs_action.triggered.connect(self.open_logs_folder)
        help_menu.addAction(open_logs_action)

        open_config_action = QAction(tr("mw_open_config_folder"), self)
        open_config_action.triggered.connect(self.open_config_folder)
        help_menu.addAction(open_config_action)

        try:
            self._advanced_actions.extend([open_logs_action, open_config_action])
        except Exception:
            pass

        about_action = QAction(_tr("menu_about"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        try:
            self._apply_ui_mode_to_actions()
        except Exception:
            pass

        try:
            self._apply_ui_mode_to_nav()
        except Exception:
            pass

        try:
            self._sync_mode_combo_from_settings()
        except Exception:
            pass

    def create_tabs(self):
        """Oppretter alle tabs"""
        _tr = globals().get("tr", lambda k, **kw: k)

        # Lightweight lazy loader widget: defers heavy tab construction until
        # the tab is actually shown. This keeps import-time and startup fast
        # and safe for headless/CI environments.
        main_window = self

        class LazyLoadWidget(QWidget):
            def __init__(self, factory, parent=None, *factory_args, **factory_kwargs):
                super().__init__(parent)
                self._factory = factory
                self._factory_args = factory_args
                self._factory_kwargs = factory_kwargs
                self._loaded = False
                self._layout = None
                try:
                    self._layout = QVBoxLayout()
                    self.setLayout(self._layout)
                    self._loading_label = QLabel(tr("mw_loading"), self)
                    self._layout.addWidget(self._loading_label)
                except Exception:
                    self._layout = None

                # If no parent supplied, try to attach to main window shortly
                # after construction to avoid becoming a transient top-level.
                if parent is None:
                    try:

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
                    widget = main_window._instantiate_factory(
                        self._factory,
                        self,
                        *self._factory_args,
                        **self._factory_kwargs,
                    )

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
                                self._layout.addWidget(
                                    QLabel(tr("mw_loaded_content"), self)
                                )
                            except Exception:
                                pass
                except Exception:
                    try:
                        logger.exception("LazyLoadWidget factory failed")
                    except Exception:
                        pass
                    if self._layout is not None:
                        try:
                            self._layout.addWidget(QLabel(tr("mw_failed_to_load_tab")))
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

        # Ladeutvikling tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_load_development_tab, parent=self.tabs),
            _tr("tab_dashboard"),
        )

        # Prosjekter tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_projects_tab, parent=self.tabs),
            _tr("tab_test_lab"),
        )

        # Ballistikk tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_ballistics_tab, parent=self.tabs),
            _tr("tab_ammunition"),
        )

        # Lager og batcher tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_inventory_batches_tab, parent=self.tabs),
            _tr("tab_inventory"),
        )

        # Våpenprofiler tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_weapon_profiles_tab, parent=self.tabs),
            _tr("tab_rifles"),
        )

        # Lab og testing tab (lazy-loaded)
        self.tabs.addTab(
            LazyLoadWidget(self.create_lab_testing_tab, parent=self.tabs),
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
            from ..modules.dashboard import Dashboard

            return self._construct_widget(Dashboard, self)
        except Exception as e:
            logger.exception("Failed to import Dashboard: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(tr("mw_dashboard_unavailable"), w))
            w.setLayout(layout)
            return w

    def _build_module_tab_group(
        self,
        tab_specs: list[dict[str, object]],
        *,
        include_stats: bool = False,
    ) -> "QWidget":
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        for spec in tab_specs:
            self._add_tab_from_module(
                tabs,
                str(spec["title"]),
                str(spec["module"]),
                str(spec["class_name"]),
                str(spec["unavailable"]),
                str(spec["log_message"]),
                allow_non_widget=bool(spec.get("allow_non_widget", False)),
                wrap_label=(
                    str(spec["wrap_label"])
                    if spec.get("wrap_label") is not None
                    else None
                ),
            )

        if include_stats:
            tabs.addTab(self._build_stats_tab(), "Statistikk")

        return widget

    def _build_load_development_home(self) -> "QWidget":
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        workspace_snapshot = self._get_workspace_snapshot()

        hero = QGroupBox(tr("mw_load_development"))
        hero_layout = QVBoxLayout()
        hero.setLayout(hero_layout)
        hero_layout.addWidget(QLabel(tr("mw_load_development_intro")))
        hero_layout.addWidget(QLabel(tr("mw_load_development_intro2")))
        layout.addWidget(hero)

        actions = QGroupBox(tr("mw_quick_start"))
        actions_layout = QHBoxLayout()
        actions.setLayout(actions_layout)
        quick_actions = [
            (tr("mw_start_new_load"), self._handle_load_development_workflow),
            (tr("mw_continue_project_batch"), self._continue_latest_project_batch),
            (tr("mw_load_assistant_label"), self.launch_smart_wizard),
            (
                tr("mw_chronograph_import_label"),
                lambda: self.launch_workflow("chronograph_import"),
            ),
            (
                tr("mw_target_analyzer_label"),
                lambda: self.launch_workflow("target_analyzer"),
            ),
            (
                tr("mw_weapon_profiles_tab"),
                lambda: self._activate_tab_by_text(tr("mw_weapon_profiles_tab")),
            ),
        ]
        for label, handler in quick_actions:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)
        actions_layout.addStretch()
        layout.addWidget(actions)

        context = QGroupBox(tr("mw_active_work_context"))
        context_layout = QVBoxLayout()
        context.setLayout(context_layout)
        context_layout.addWidget(
            QLabel(
                f"{tr('mw_active_project')}: {workspace_snapshot.get('current_project_name', 'Default Project')}"
            )
        )
        context_layout.addWidget(
            QLabel(
                f"{tr('mw_project_batches_linked')}: "
                f"{workspace_snapshot.get('current_project_batch_count', 0)}"
            )
        )
        context_layout.addWidget(
            QLabel(
                f"{tr('mw_profiles_available')}: "
                f"{workspace_snapshot.get('rifle_count', 0)} / {workspace_snapshot.get('ammo_profile_count', 0)}"
            )
        )
        latest_project_batch_name = str(
            workspace_snapshot.get("latest_project_batch_name", "") or ""
        )
        context_layout.addWidget(
            QLabel(
                f"{tr('mw_latest_project_batch')}: "
                f"{latest_project_batch_name if latest_project_batch_name else tr('mw_none_yet')}"
            )
        )
        workflow_title = str(workspace_snapshot.get("active_workflow_title", "") or "")
        workflow_message = str(
            workspace_snapshot.get("active_workflow_message", "") or ""
        )
        workflow_name = str(workspace_snapshot.get("active_workflow_name", "") or "")
        workflow_setup_label = str(
            workspace_snapshot.get("active_workflow_setup_label", "") or ""
        )
        workflow_confidence_label = str(
            workspace_snapshot.get("active_workflow_confidence_label", "") or ""
        )
        workflow_confidence_message = str(
            workspace_snapshot.get("active_workflow_confidence_message", "") or ""
        )
        workflow_robustness_title = str(
            workspace_snapshot.get("active_workflow_robustness_title", "") or ""
        )
        workflow_robustness_message = str(
            workspace_snapshot.get("active_workflow_robustness_message", "") or ""
        )
        workflow_robustness_score = str(
            workspace_snapshot.get("active_workflow_robustness_score", "") or ""
        )
        workflow_robustness_uncertainty_message = str(
            workspace_snapshot.get("active_workflow_robustness_uncertainty_message", "")
            or ""
        )
        workflow_impact_title = str(
            workspace_snapshot.get("active_workflow_impact_title", "") or ""
        )
        workflow_impact_message = str(
            workspace_snapshot.get("active_workflow_impact_message", "") or ""
        )
        workflow_evidence_quality_title = str(
            workspace_snapshot.get("active_workflow_evidence_quality_title", "") or ""
        )
        workflow_evidence_quality_message = str(
            workspace_snapshot.get("active_workflow_evidence_quality_message", "") or ""
        )
        workflow_evidence_quality_checks = list(
            workspace_snapshot.get("active_workflow_evidence_quality_checks", []) or []
        )
        workflow_next_test_title = str(
            workspace_snapshot.get("active_workflow_next_test_title", "") or ""
        )
        workflow_next_test_action = str(
            workspace_snapshot.get("active_workflow_next_test_action", "") or ""
        )
        workflow_next_test_confidence_label = str(
            workspace_snapshot.get("active_workflow_next_test_confidence_label", "")
            or ""
        )
        workflow_next_test_confidence_message = str(
            workspace_snapshot.get("active_workflow_next_test_confidence_message", "")
            or ""
        )
        if workflow_title:
            context_layout.addWidget(
                QLabel(
                    f"{tr('mw_active_workflow')}: {workflow_name if workflow_name else tr('tab_dashboard')}"
                )
            )
            if workflow_setup_label:
                context_layout.addWidget(QLabel(f"Setup: {workflow_setup_label}"))
            context_layout.addWidget(
                QLabel(
                    f"{tr('mw_workflow_status')}: {workflow_title} - {workflow_message}"
                )
            )
            if workflow_confidence_label:
                context_layout.addWidget(
                    QLabel(
                        f"{tr('mw_readiness_confidence')}: {workflow_confidence_label}"
                    )
                )
            if workflow_confidence_message:
                confidence_label = QLabel(workflow_confidence_message)
                confidence_label.setWordWrap(True)
                context_layout.addWidget(confidence_label)
            if workflow_next_test_title:
                next_test_label = QLabel(
                    f"{tr('mw_best_next_test')}: {workflow_next_test_title} - {workflow_next_test_action}"
                )
                next_test_label.setWordWrap(True)
                context_layout.addWidget(next_test_label)
            if workflow_next_test_confidence_label:
                context_layout.addWidget(
                    QLabel(
                        f"{tr('mw_next_test_confidence')}: {workflow_next_test_confidence_label}"
                    )
                )
            if workflow_next_test_confidence_message:
                next_test_confidence = QLabel(workflow_next_test_confidence_message)
                next_test_confidence.setWordWrap(True)
                context_layout.addWidget(next_test_confidence)
            if workflow_robustness_title:
                context_layout.addWidget(
                    QLabel(
                        f"{tr('mw_robustness')}: {workflow_robustness_title}"
                        + (
                            f" ({workflow_robustness_score}/100)"
                            if workflow_robustness_score
                            else ""
                        )
                    )
                )
            if workflow_robustness_message:
                robustness_label = QLabel(workflow_robustness_message)
                robustness_label.setWordWrap(True)
                context_layout.addWidget(robustness_label)
            if workflow_robustness_uncertainty_message:
                robustness_uncertainty = QLabel(
                    f"{tr('mw_robustness_uncertainty')}: {workflow_robustness_uncertainty_message}"
                )
                robustness_uncertainty.setWordWrap(True)
                context_layout.addWidget(robustness_uncertainty)
            if workflow_impact_title and workflow_impact_message:
                impact_label = QLabel(
                    f"{workflow_impact_title}: {workflow_impact_message}"
                )
                impact_label.setWordWrap(True)
                context_layout.addWidget(impact_label)
            if workflow_evidence_quality_title:
                evidence_label = QLabel(
                    f"{tr('mw_evidence_quality')}: {workflow_evidence_quality_title}"
                )
                evidence_label.setWordWrap(True)
                context_layout.addWidget(evidence_label)
            if workflow_evidence_quality_message:
                evidence_message = QLabel(workflow_evidence_quality_message)
                evidence_message.setWordWrap(True)
                context_layout.addWidget(evidence_message)
            for item in workflow_evidence_quality_checks[:3]:
                evidence_check = QLabel(f"- {item}")
                evidence_check.setWordWrap(True)
                context_layout.addWidget(evidence_check)
        recommendation = self._get_workflow_action_recommendation()
        if recommendation is not None:
            workflow_action_label, workflow_action_handler = recommendation
            action_btn = QPushButton(workflow_action_label)
            action_btn.clicked.connect(workflow_action_handler)
            context_layout.addWidget(action_btn)
        layout.addWidget(context)

        next_steps = QGroupBox(tr("mw_recommended_flow"))
        next_steps_layout = QVBoxLayout()
        next_steps.setLayout(next_steps_layout)
        for text in (
            tr("mw_next_step_1"),
            tr("mw_next_step_2"),
            tr("mw_next_step_3"),
            tr("mw_next_step_4"),
        ):
            next_steps_layout.addWidget(QLabel(text))
        layout.addWidget(next_steps)

        layout.addStretch()
        return widget

    def _build_projects_home(self) -> "QWidget":
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        workspace_snapshot = self._get_workspace_snapshot()

        hero = QGroupBox(tr("mw_projects_history"))
        hero_layout = QVBoxLayout()
        hero.setLayout(hero_layout)
        hero_layout.addWidget(QLabel(tr("mw_projects_intro")))
        hero_layout.addWidget(QLabel(tr("mw_projects_intro2")))
        layout.addWidget(hero)

        actions = QGroupBox(tr("mw_quick_choices"))
        actions_layout = QHBoxLayout()
        actions.setLayout(actions_layout)
        quick_actions = [
            (
                tr("mw_new_loading_session"),
                lambda: self._activate_tab_by_text(tr("mw_projects_tab")),
            ),
            (
                tr("mw_new_shooting_session"),
                lambda: self._activate_tab_by_text(tr("mw_projects_tab")),
            ),
            (
                tr("mw_historical_analysis"),
                lambda: self._activate_tab_by_text(tr("mw_projects_tab")),
            ),
            (tr("mw_ammo_test_lab"), self.show_ammo_test_lab),
            (tr("mw_start_new_load_dev"), self._handle_load_development_workflow),
            (tr("mw_continue_project_batch"), self._continue_latest_project_batch),
            (
                tr("mw_batch_workspace_label"),
                lambda: self.launch_workflow("batch_workspace"),
            ),
            (
                tr("mw_weapon_profiles_tab"),
                lambda: self._activate_tab_by_text(tr("mw_weapon_profiles_tab")),
            ),
            (
                tr("mw_lab_testing_tab"),
                lambda: self._activate_tab_by_text(tr("mw_lab_testing_tab")),
            ),
        ]
        for label, handler in quick_actions:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)
        actions_layout.addStretch()
        layout.addWidget(actions)

        status = QGroupBox(tr("mw_active_project_status"))
        status_layout = QVBoxLayout()
        status.setLayout(status_layout)
        status_layout.addWidget(
            QLabel(
                f"Aktivt prosjekt: {workspace_snapshot.get('current_project_name', 'Default Project')}"
            )
        )
        status_layout.addWidget(
            QLabel(
                f"{tr('mw_recent_projects_in_list')}: {workspace_snapshot.get('recent_projects_count', 0)}"
            )
        )
        status_layout.addWidget(
            QLabel(
                f"{tr('mw_batches_linked_to_active_project')}: "
                f"{workspace_snapshot.get('current_project_batch_count', 0)}"
            )
        )
        latest_project_batch_name = str(
            workspace_snapshot.get("latest_project_batch_name", "") or ""
        )
        status_layout.addWidget(
            QLabel(
                f"{tr('mw_latest_project_batch')}: "
                f"{latest_project_batch_name if latest_project_batch_name else tr('mw_none_yet')}"
            )
        )
        status_layout.addWidget(
            QLabel(
                f"{tr('mw_available_weapon_profiles')}: {workspace_snapshot.get('rifle_count', 0)}"
            )
        )
        workflow_title = str(workspace_snapshot.get("active_workflow_title", "") or "")
        workflow_message = str(
            workspace_snapshot.get("active_workflow_message", "") or ""
        )
        workflow_name = str(workspace_snapshot.get("active_workflow_name", "") or "")
        workflow_setup_label = str(
            workspace_snapshot.get("active_workflow_setup_label", "") or ""
        )
        workflow_confidence_label = str(
            workspace_snapshot.get("active_workflow_confidence_label", "") or ""
        )
        workflow_confidence_message = str(
            workspace_snapshot.get("active_workflow_confidence_message", "") or ""
        )
        workflow_robustness_title = str(
            workspace_snapshot.get("active_workflow_robustness_title", "") or ""
        )
        workflow_robustness_message = str(
            workspace_snapshot.get("active_workflow_robustness_message", "") or ""
        )
        workflow_robustness_score = str(
            workspace_snapshot.get("active_workflow_robustness_score", "") or ""
        )
        workflow_robustness_uncertainty_message = str(
            workspace_snapshot.get("active_workflow_robustness_uncertainty_message", "")
            or ""
        )
        workflow_impact_title = str(
            workspace_snapshot.get("active_workflow_impact_title", "") or ""
        )
        workflow_impact_message = str(
            workspace_snapshot.get("active_workflow_impact_message", "") or ""
        )
        workflow_evidence_quality_title = str(
            workspace_snapshot.get("active_workflow_evidence_quality_title", "") or ""
        )
        workflow_evidence_quality_message = str(
            workspace_snapshot.get("active_workflow_evidence_quality_message", "") or ""
        )
        workflow_evidence_quality_checks = list(
            workspace_snapshot.get("active_workflow_evidence_quality_checks", []) or []
        )
        workflow_next_test_title = str(
            workspace_snapshot.get("active_workflow_next_test_title", "") or ""
        )
        workflow_next_test_action = str(
            workspace_snapshot.get("active_workflow_next_test_action", "") or ""
        )
        workflow_next_test_confidence_label = str(
            workspace_snapshot.get("active_workflow_next_test_confidence_label", "")
            or ""
        )
        workflow_next_test_confidence_message = str(
            workspace_snapshot.get("active_workflow_next_test_confidence_message", "")
            or ""
        )
        if workflow_title:
            status_layout.addWidget(
                QLabel(
                    f"{tr('mw_active_workflow')}: {workflow_name if workflow_name else tr('tab_dashboard')}"
                )
            )
            if workflow_setup_label:
                status_layout.addWidget(QLabel(f"Setup: {workflow_setup_label}"))
            status_layout.addWidget(
                QLabel(
                    f"{tr('mw_workflow_status')}: {workflow_title} - {workflow_message}"
                )
            )
            if workflow_confidence_label:
                status_layout.addWidget(
                    QLabel(
                        f"{tr('mw_readiness_confidence')}: {workflow_confidence_label}"
                    )
                )
            if workflow_confidence_message:
                confidence_label = QLabel(workflow_confidence_message)
                confidence_label.setWordWrap(True)
                status_layout.addWidget(confidence_label)
            if workflow_next_test_title:
                next_test_label = QLabel(
                    f"{tr('mw_best_next_test')}: {workflow_next_test_title} - {workflow_next_test_action}"
                )
                next_test_label.setWordWrap(True)
                status_layout.addWidget(next_test_label)
            if workflow_next_test_confidence_label:
                status_layout.addWidget(
                    QLabel(
                        f"{tr('mw_next_test_confidence')}: {workflow_next_test_confidence_label}"
                    )
                )
            if workflow_next_test_confidence_message:
                next_test_confidence = QLabel(workflow_next_test_confidence_message)
                next_test_confidence.setWordWrap(True)
                status_layout.addWidget(next_test_confidence)
            if workflow_robustness_title:
                status_layout.addWidget(
                    QLabel(
                        f"Robustness: {workflow_robustness_title}"
                        + (
                            f" ({workflow_robustness_score}/100)"
                            if workflow_robustness_score
                            else ""
                        )
                    )
                )
            if workflow_robustness_message:
                robustness_label = QLabel(workflow_robustness_message)
                robustness_label.setWordWrap(True)
                status_layout.addWidget(robustness_label)
            if workflow_robustness_uncertainty_message:
                robustness_uncertainty = QLabel(
                    f"{tr('mw_robustness_uncertainty')}: {workflow_robustness_uncertainty_message}"
                )
                robustness_uncertainty.setWordWrap(True)
                status_layout.addWidget(robustness_uncertainty)
            if workflow_impact_title and workflow_impact_message:
                impact_label = QLabel(
                    f"{workflow_impact_title}: {workflow_impact_message}"
                )
                impact_label.setWordWrap(True)
                status_layout.addWidget(impact_label)
            if workflow_evidence_quality_title:
                evidence_label = QLabel(
                    f"{tr('mw_evidence_quality')}: {workflow_evidence_quality_title}"
                )
                evidence_label.setWordWrap(True)
                status_layout.addWidget(evidence_label)
            if workflow_evidence_quality_message:
                evidence_message = QLabel(workflow_evidence_quality_message)
                evidence_message.setWordWrap(True)
                status_layout.addWidget(evidence_message)
            for item in workflow_evidence_quality_checks[:3]:
                evidence_check = QLabel(f"- {item}")
                evidence_check.setWordWrap(True)
                status_layout.addWidget(evidence_check)
        recommendation = self._get_workflow_action_recommendation()
        if recommendation is not None:
            workflow_action_label, workflow_action_handler = recommendation
            action_btn = QPushButton(workflow_action_label)
            action_btn.clicked.connect(workflow_action_handler)
            status_layout.addWidget(action_btn)
        layout.addWidget(status)

        overview = QGroupBox(tr("mw_what_you_can_do_here"))
        overview_layout = QVBoxLayout()
        overview.setLayout(overview_layout)
        for text in (
            tr("mw_projects_overview_1"),
            tr("mw_projects_overview_2"),
            tr("mw_projects_overview_3"),
        ):
            overview_layout.addWidget(QLabel(text))
        layout.addWidget(overview)

        layout.addStretch()
        return widget

    def _build_weapon_profiles_home(self) -> "QWidget":
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        workspace_snapshot = self._get_workspace_snapshot()

        hero = QGroupBox(tr("mw_weapon_profiles_tab"))
        hero_layout = QVBoxLayout()
        hero.setLayout(hero_layout)
        hero_layout.addWidget(QLabel(tr("mw_weapon_profiles_intro_1")))
        hero_layout.addWidget(QLabel(tr("mw_weapon_profiles_intro_2")))
        layout.addWidget(hero)

        actions = QGroupBox(tr("mw_quick_choices"))
        actions_layout = QHBoxLayout()
        actions.setLayout(actions_layout)
        quick_actions = [
            (
                tr("mw_open_weapon_profile"),
                lambda: self._activate_tab_by_text(tr("mw_weapon_profiles_tab")),
            ),
            (tr("mw_start_new_load_dev"), self._handle_load_development_workflow),
            (
                tr("mw_projects_tab"),
                lambda: self._activate_tab_by_text(tr("mw_projects_tab")),
            ),
            (
                tr("mw_lab_testing_tab"),
                lambda: self._activate_tab_by_text(tr("mw_lab_testing_tab")),
            ),
        ]
        for label, handler in quick_actions:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)
        actions_layout.addStretch()
        layout.addWidget(actions)

        status = QGroupBox(tr("mw_current_data_foundation"))
        status_layout = QVBoxLayout()
        status.setLayout(status_layout)
        status_layout.addWidget(
            QLabel(
                f"{tr('mw_registered_weapon_profiles')}: {workspace_snapshot.get('rifle_count', 0)}"
            )
        )
        status_layout.addWidget(
            QLabel(
                f"{tr('mw_linked_load_profiles')}: {workspace_snapshot.get('ammo_profile_count', 0)}"
            )
        )
        layout.addWidget(status)

        overview = QGroupBox(tr("mw_weapon_profile_controls"))
        overview_layout = QVBoxLayout()
        overview.setLayout(overview_layout)
        for text in (
            tr("mw_weapon_profiles_overview_1"),
            tr("mw_weapon_profiles_overview_2"),
            tr("mw_weapon_profiles_overview_3"),
        ):
            overview_layout.addWidget(QLabel(text))
        layout.addWidget(overview)

        layout.addStretch()
        return widget

    def _build_ballistics_home(self) -> "QWidget":
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        hero = QGroupBox(tr("mw_ballistics_planning"))
        hero_layout = QVBoxLayout()
        hero.setLayout(hero_layout)
        hero_layout.addWidget(QLabel(tr("mw_ballistics_intro_1")))
        hero_layout.addWidget(QLabel(tr("mw_ballistics_intro_2")))
        layout.addWidget(hero)

        actions = QGroupBox(tr("mw_quick_choices"))
        actions_layout = QHBoxLayout()
        actions.setLayout(actions_layout)
        quick_actions = [
            (
                tr("mw_ballistics_tab"),
                lambda: self._activate_tab_by_text(tr("mw_ballistics_tab")),
            ),
            (tr("mw_drop_chart_label"), self.show_drop_chart),
            (tr("mw_zero_shift_tab"), self.show_zero_shift_calculator),
            (
                tr("mw_weapon_profiles_tab"),
                lambda: self._activate_tab_by_text(tr("mw_weapon_profiles_tab")),
            ),
            (
                tr("mw_lab_testing_tab"),
                lambda: self._activate_tab_by_text(tr("mw_lab_testing_tab")),
            ),
        ]
        for label, handler in quick_actions:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)
        actions_layout.addStretch()
        layout.addWidget(actions)

        overview = QGroupBox(tr("mw_this_belongs_here"))
        overview_layout = QVBoxLayout()
        overview.setLayout(overview_layout)
        for text in (
            tr("mw_ballistics_overview_1"),
            tr("mw_ballistics_overview_2"),
            tr("mw_ballistics_overview_3"),
        ):
            overview_layout.addWidget(QLabel(text))
        layout.addWidget(overview)

        layout.addStretch()
        return widget

    def _build_lab_testing_home(self) -> "QWidget":
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        hero = QGroupBox(tr("mw_lab_testing_tab"))
        hero_layout = QVBoxLayout()
        hero.setLayout(hero_layout)
        hero_layout.addWidget(QLabel(tr("mw_lab_testing_intro_1")))
        hero_layout.addWidget(QLabel(tr("mw_lab_testing_intro_2")))
        layout.addWidget(hero)

        actions = QGroupBox(tr("mw_quick_choices"))
        actions_layout = QHBoxLayout()
        actions.setLayout(actions_layout)
        quick_actions = [
            (
                tr("mw_chronograph_tab"),
                lambda: self.launch_workflow("chronograph_import"),
            ),
            (
                tr("mw_target_analyzer_label"),
                lambda: self.launch_workflow("target_analyzer"),
            ),
            (
                tr("mw_temperature_test_tab"),
                lambda: self.launch_workflow("temperature_test"),
            ),
            (tr("mw_safety_tab"), self.show_safety_dashboard),
            (
                tr("mw_ballistics_tab"),
                lambda: self._activate_tab_by_text(tr("mw_ballistics_tab")),
            ),
        ]
        for label, handler in quick_actions:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)
        actions_layout.addStretch()
        layout.addWidget(actions)

        overview = QGroupBox(tr("mw_this_belongs_here"))
        overview_layout = QVBoxLayout()
        overview.setLayout(overview_layout)
        for text in (
            tr("mw_lab_testing_overview_1"),
            tr("mw_lab_testing_overview_2"),
            tr("mw_lab_testing_overview_3"),
        ):
            overview_layout.addWidget(QLabel(text))
        layout.addWidget(overview)

        layout.addStretch()
        return widget

    def _build_inventory_batches_home(self) -> "QWidget":
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        workspace_snapshot = self._get_workspace_snapshot()
        workspace_attention = self._get_workspace_attention()

        hero = QGroupBox(tr("mw_inventory_batches_tab"))
        hero_layout = QVBoxLayout()
        hero.setLayout(hero_layout)
        hero_layout.addWidget(QLabel(tr("mw_inventory_batches_intro_1")))
        hero_layout.addWidget(QLabel(tr("mw_inventory_batches_intro_2")))
        layout.addWidget(hero)

        actions = QGroupBox(tr("mw_quick_choices"))
        actions_layout = QHBoxLayout()
        actions.setLayout(actions_layout)
        quick_actions = [
            (
                tr("mw_open_inventory"),
                lambda: self._activate_tab_by_text(tr("mw_inventory_batches_tab")),
            ),
            (
                tr("mw_batch_workspace_label"),
                lambda: self.launch_workflow("batch_workspace"),
            ),
            (
                tr("mw_lot_tracker_tab"),
                lambda: self._activate_tab_by_text(tr("mw_inventory_batches_tab")),
            ),
            (tr("mw_start_new_load_dev"), self._handle_load_development_workflow),
            (
                tr("mw_weapon_profiles_tab"),
                lambda: self._activate_tab_by_text(tr("mw_weapon_profiles_tab")),
            ),
        ]
        for label, handler in quick_actions:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)
        actions_layout.addStretch()
        layout.addWidget(actions)

        status = QGroupBox(tr("mw_current_inventory_status"))
        status_layout = QVBoxLayout()
        status.setLayout(status_layout)
        status_layout.addWidget(
            QLabel(
                f"{tr('mw_registered_batch_projects')}: {workspace_snapshot.get('batch_count', 0)}"
            )
        )
        status_layout.addWidget(
            QLabel(
                f"{tr('mw_registered_inventory_items')}: {workspace_snapshot.get('inventory_item_count', 0)}"
            )
        )
        status_layout.addWidget(
            QLabel(
                tr(
                    "mw_low_inventory_registered",
                    powder=workspace_attention.get("low_powder_count", 0),
                    bullets=workspace_attention.get("low_bullet_count", 0),
                    primers=workspace_attention.get("low_primer_count", 0),
                )
            )
        )
        layout.addWidget(status)

        overview = QGroupBox(tr("mw_this_belongs_here"))
        overview_layout = QVBoxLayout()
        overview.setLayout(overview_layout)
        for text in (
            tr("mw_inventory_batches_overview_1"),
            tr("mw_inventory_batches_overview_2"),
            tr("mw_inventory_batches_overview_3"),
        ):
            overview_layout.addWidget(QLabel(text))
        layout.addWidget(overview)

        layout.addStretch()
        return widget

    def create_load_development_tab(self):
        """Oppretter toppnivået for ladeutvikling."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self._build_load_development_home(), tr("mw_start_tab"))
        tabs.addTab(self.create_dashboard_tab(), tr("mw_dashboard_tab"))
        tabs.addTab(self.create_ammo_tab(), tr("mw_ammunition_tab"))

        self._add_tab_from_module(
            tabs,
            tr("mw_workflows_tab"),
            "src.modules.workflow_hub",
            "WorkflowHub",
            tr("mw_workflow_hub_unavailable"),
            "WorkflowHub import failed",
        )

        return widget

    def create_projects_tab(self):
        """Oppretter prosjekt- og historikkområdet."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self._build_projects_home(), tr("mw_start_folder_tab"))

        self._add_tab_from_module(
            tabs,
            tr("mw_session_log_tab"),
            "src.modules.session_logger",
            "SessionLogger",
            tr("mw_session_logger_unavailable"),
            "SessionLogger import failed",
        )
        self._add_tab_from_module(
            tabs,
            tr("mw_history_tab"),
            "src.modules.historical_analysis",
            "HistoricalAnalysisViewer",
            tr("mw_historical_analysis_unavailable"),
            "HistoricalAnalysisViewer import failed",
        )
        tabs.addTab(self._build_stats_tab(), tr("mw_statistics_tab"))

        return widget

    def create_ballistics_tab(self):
        """Oppretter ballistikk og planlegging."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self._build_ballistics_home(), tr("mw_start_folder_tab"))

        for spec in [
            {
                "title": tr("mw_ballistics_tab"),
                "module": "src.modules.ballistics_simulator",
                "class_name": "BallisticsSimulator",
                "unavailable": tr("mw_ballistics_simulator_unavailable"),
                "log_message": "BallisticsSimulator import failed",
            },
            {
                "title": tr("mw_drop_wind_tab"),
                "module": "src.modules.drop_chart_generator",
                "class_name": "DropChartGenerator",
                "unavailable": tr("mw_drop_chart_generator_unavailable"),
                "log_message": "DropChartGenerator import failed",
            },
            {
                "title": tr("mw_terrain_map_tab"),
                "module": "src.modules.terrain_map",
                "class_name": "TerrainMapViewer",
                "unavailable": tr("mw_terrain_map_unavailable"),
                "log_message": "Feil ved import av TerrainMapViewer",
                "allow_non_widget": True,
                "wrap_label": tr("mw_terrain_map_wrapped"),
            },
            {
                "title": tr("mw_weather_data_tab"),
                "module": "src.modules.environmental_logger",
                "class_name": "EnvironmentalLogger",
                "unavailable": tr("mw_environmental_logger_unavailable"),
                "log_message": "EnvironmentalLogger import failed",
            },
        ]:
            self._add_tab_from_module(
                tabs,
                str(spec["title"]),
                str(spec["module"]),
                str(spec["class_name"]),
                str(spec["unavailable"]),
                str(spec["log_message"]),
                allow_non_widget=bool(spec.get("allow_non_widget", False)),
                wrap_label=(
                    str(spec["wrap_label"])
                    if spec.get("wrap_label") is not None
                    else None
                ),
            )

        return widget

    def create_inventory_batches_tab(self):
        """Oppretter lager- og batchområdet."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self._build_inventory_batches_home(), tr("mw_start_folder_tab"))

        for spec in [
            {
                "title": tr("mw_inventory_tab"),
                "module": "src.modules.inventory_manager",
                "class_name": "InventoryManager",
                "unavailable": tr("mw_inventory_unavailable"),
                "log_message": "InventoryManager import failed",
            },
            {
                "title": tr("mw_batch_workspace_module_tab"),
                "module": "src.modules.batch_workspace",
                "class_name": "BatchWorkspace",
                "unavailable": tr("mw_batch_workspace_unavailable"),
                "log_message": "BatchWorkspace import failed",
            },
            {
                "title": tr("mw_lot_tracker_tab"),
                "module": "src.modules.component_lot_tracker",
                "class_name": "ComponentLotTracker",
                "unavailable": tr("mw_component_lot_tracker_unavailable"),
                "log_message": "ComponentLotTracker import failed",
            },
        ]:
            self._add_tab_from_module(
                tabs,
                str(spec["title"]),
                str(spec["module"]),
                str(spec["class_name"]),
                str(spec["unavailable"]),
                str(spec["log_message"]),
            )

        return widget

    def create_weapon_profiles_tab(self):
        """Oppretter våpenprofilområdet."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self._build_weapon_profiles_home(), tr("mw_start_folder_tab"))
        tabs.addTab(self.create_rifles_tab(), tr("mw_profiles_equipment_tab"))

        return widget

    def create_lab_testing_tab(self):
        """Oppretter lab- og testområdet."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self._build_lab_testing_home(), tr("mw_start_folder_tab"))

        for spec in [
            {
                "title": tr("mw_ladder_test_tab"),
                "module": "src.modules.ladder_test_lab",
                "class_name": "LadderTestLab",
                "unavailable": tr("mw_test_lab_unavailable"),
                "log_message": "LadderTestLab import failed",
            },
            {
                "title": tr("mw_target_analyzer_title"),
                "module": "src.modules.target_analyzer",
                "class_name": "TargetAnalyzer",
                "unavailable": tr("mw_target_analyzer_unavailable"),
                "log_message": "TargetAnalyzer import failed",
            },
            {
                "title": tr("mw_chronograph_tab"),
                "module": "src.modules.chronograph_importer",
                "class_name": "ChronographImporter",
                "unavailable": tr("mw_chronograph_import_unavailable"),
                "log_message": "ChronographImporter import failed",
            },
            {
                "title": tr("mw_temperature_test_tab"),
                "module": "src.modules.temperature_ladder_test",
                "class_name": "TemperatureLadderTest",
                "unavailable": tr("mw_temperature_ladder_test_unavailable"),
                "log_message": "TemperatureLadderTest import failed",
                "legacy": True,
            },
            {
                "title": tr("mw_precision_tracker_title"),
                "module": "src.modules.precision_tracker",
                "class_name": "PrecisionTracker",
                "unavailable": tr("mw_precision_tracker_unavailable"),
                "log_message": "PrecisionTracker import failed",
                "legacy": True,
            },
            {
                "title": tr("mw_saami_checker_tab"),
                "module": "src.modules.saami_compliance_checker",
                "class_name": "SAAMIComplianceChecker",
                "unavailable": tr("mw_saami_checker_unavailable_short"),
                "log_message": "SAAMIComplianceChecker import failed",
            },
            {
                "title": tr("mw_safety_tab"),
                "module": "src.modules.safety_dashboard",
                "class_name": "SafetyDashboard",
                "unavailable": tr("mw_safety_dashboard_unavailable"),
                "log_message": "SafetyDashboard import failed",
            },
        ]:
            self._add_tab_from_module(
                tabs,
                str(spec["title"]),
                str(spec["module"]),
                str(spec["class_name"]),
                str(spec["unavailable"]),
                str(spec["log_message"]),
                legacy=bool(spec.get("legacy")),
            )

        return widget

    def create_test_lab_tab(self):
        """Oppretter test lab-fanen"""
        try:
            from ..modules.ladder_test_lab import LadderTestLab

            return self._construct_widget(LadderTestLab, self)
        except Exception as e:
            logger.exception("Failed to import LadderTestLab: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(tr("mw_test_lab_unavailable"), w))
            w.setLayout(layout)
            return w

    def create_ammo_tab(self):
        """Oppretter ammunisjon-fanen"""
        try:
            from ..modules.ammo_profile_manager import AmmoProfileManager

            return self._construct_widget(AmmoProfileManager, self)
        except Exception as e:
            logger.exception("Failed to import AmmoProfileManager: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(tr("mw_ammo_unavailable"), w))
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
            from ..modules.rifle_database_manager import RifleDatabaseManager

            tabs.addTab(
                self._construct_widget(RifleDatabaseManager, self),
                tr("mw_rifle_database_tab"),
            )
        except Exception as e:
            logger.exception("RifleDatabaseManager import failed: %s", e)

        # Tab 2: Rifle & Optic Manager
        try:
            from ..modules.rifle_optic_manager import RifleOpticManager

            tabs.addTab(
                self._construct_widget(RifleOpticManager, self),
                tr("mw_rifle_optic_tab"),
            )
        except Exception as e:
            logger.exception("RifleOpticManager import failed: %s", e)

        # Tab 3: Rifle Performance Tracker
        try:
            from ..modules.rifle_performance_tracker import RiflePerformanceTracker

            tabs.addTab(
                self._construct_widget(RiflePerformanceTracker, self),
                tr("mw_rifle_performance_tab"),
            )
        except Exception as e:
            logger.exception("RiflePerformanceTracker import failed: %s", e)

        return widget

    def create_inventory_tab(self):
        """Oppretter lager-fanen"""
        try:
            from ..modules.inventory_manager import InventoryManager

            return self._construct_widget(InventoryManager, self)
        except Exception as e:
            logger.exception("InventoryManager import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(tr("mw_inventory_unavailable"), w))
            w.setLayout(layout)
            return w

    def create_log_tab(self):
        """Oppretter logg-fanen"""
        try:
            from ..modules.session_logger import SessionLogger

            return self._construct_widget(SessionLogger, self)
        except Exception as e:
            logger.exception("SessionLogger import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(tr("mw_log_unavailable"), w))
            w.setLayout(layout)
            return w

    def _build_unavailable_tab(self, label: str) -> "QWidget":
        w = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label, w))
        layout.addStretch()
        w.setLayout(layout)
        return w

    @staticmethod
    def _instantiate_factory(factory, parent: "QWidget", *args, **kwargs):
        attempts = [
            (args, {**kwargs, "parent": parent}),
            ((parent, *args), dict(kwargs)),
            (args, dict(kwargs)),
            ((), {}),
        ]
        for call_args, call_kwargs in attempts:
            try:
                inspect.signature(factory).bind_partial(*call_args, **call_kwargs)
            except (TypeError, ValueError):
                continue
            return factory(*call_args, **call_kwargs)
        return factory()

    def _construct_widget(
        self, factory, parent: "QWidget", *args, **kwargs
    ) -> "QWidget":
        return self._instantiate_factory(factory, parent, *args, **kwargs)

    def _wrap_non_widget(self, obj: object, label: str) -> "QWidget":
        wrap = QWidget()
        wrap_layout = QVBoxLayout()
        wrap.setLayout(wrap_layout)
        try:
            mv = getattr(obj, "map_view", None)
            if mv is not None and isinstance(mv, QWidget):
                wrap_layout.addWidget(mv)
            else:
                wrap_layout.addWidget(QLabel(label, wrap))
        except Exception:
            wrap_layout.addWidget(QLabel(label, wrap))
        wrap_layout.addStretch()
        return wrap

    def _add_tab_from_module(
        self,
        tabs: "QTabWidget",
        title: str,
        module_path: str,
        class_name: str,
        unavailable_label: str,
        log_message: str,
        allow_non_widget: bool = False,
        wrap_label: str | None = None,
        legacy: bool = False,
    ) -> None:
        tab_title = self._with_legacy_suffix(title) if legacy else title
        try:
            from importlib import import_module

            module = import_module(module_path)
            factory = getattr(module, class_name)
            widget = self._construct_widget(factory, self)
            ensure_ui = getattr(widget, "ensure_ui", None)
            if callable(ensure_ui):
                try:
                    ensure_ui()
                except Exception:
                    logger.exception("Deferred UI init failed for %s", class_name)
            if isinstance(widget, QWidget):
                idx = tabs.addTab(widget, tab_title)
                if legacy:
                    tabs.setTabToolTip(idx, tr("mw_legacy_workflow"))
                return
            if allow_non_widget:
                label = wrap_label or f"{class_name} (wrapped)"
                idx = tabs.addTab(self._wrap_non_widget(widget, label), tab_title)
                if legacy:
                    tabs.setTabToolTip(idx, tr("mw_legacy_workflow"))
                return
            raise TypeError(f"{class_name} did not return QWidget")
        except Exception as e:
            logger.exception("%s: %s", log_message, e)
            idx = tabs.addTab(self._build_unavailable_tab(unavailable_label), tab_title)
            if legacy:
                tabs.setTabToolTip(idx, tr("mw_legacy_workflow"))

    def create_analysis_tab(self):
        """Oppretter analyse-fanen"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Tabs for ulike analyser
        tabs = QTabWidget()
        layout.addWidget(tabs)
        tab_specs = [
            {
                "title": tr("mw_target_analyzer_title"),
                "module": "src.modules.target_analyzer",
                "class_name": "TargetAnalyzer",
                "unavailable": tr("mw_target_analyzer_unavailable_short"),
                "log_message": "TargetAnalyzer import failed",
            },
            {
                "title": tr("mw_precision_tracker_title"),
                "module": "src.modules.precision_tracker",
                "class_name": "PrecisionTracker",
                "unavailable": tr("mw_precision_tracker_unavailable"),
                "log_message": "PrecisionTracker import failed",
                "legacy": True,
            },
            {
                "title": tr("mw_safety_dashboard_title"),
                "module": "src.modules.safety_dashboard",
                "class_name": "SafetyDashboard",
                "unavailable": tr("mw_safety_dashboard_unavailable_short"),
                "log_message": "SafetyDashboard import failed",
            },
            {
                "title": "Terrengkart",
                "module": "src.modules.terrain_map",
                "class_name": "TerrainMapViewer",
                "unavailable": tr("mw_terrain_map_unavailable"),
                "log_message": "Feil ved import av TerrainMapViewer",
                "allow_non_widget": True,
                "wrap_label": "TerrainMapViewer (wrapped)",
            },
            {
                "title": "Weather Data",
                "module": "src.modules.environmental_logger",
                "class_name": "EnvironmentalLogger",
                "unavailable": tr("mw_weather_data_unavailable"),
                "log_message": "EnvironmentalLogger import failed",
                "legacy": True,
            },
            {
                "title": "Drop/Wind",
                "module": "src.modules.drop_chart_generator",
                "class_name": "DropChartGenerator",
                "unavailable": tr("mw_drop_wind_unavailable"),
                "log_message": "DropChartGenerator import failed",
            },
            {
                "title": tr("mw_rifle_performance_title"),
                "module": "src.modules.rifle_performance_tracker",
                "class_name": "RiflePerformanceTracker",
                "unavailable": tr("mw_rifle_performance_unavailable"),
                "log_message": "RiflePerformanceTracker import failed",
            },
            {
                "title": tr("mw_chronograph_tab"),
                "module": "src.modules.chronograph_importer",
                "class_name": "ChronographImporter",
                "unavailable": tr("mw_chronograph_import_unavailable"),
                "log_message": "ChronographImporter import failed",
            },
            {},
            {
                "title": tr("mw_temperature_test_tab"),
                "module": "src.modules.temperature_ladder_test",
                "class_name": "TemperatureLadderTest",
                "unavailable": tr("mw_temperature_test_unavailable"),
                "log_message": "TemperatureLadderTest import failed",
                "legacy": True,
            },
            {
                "title": tr("mw_lot_tracker_tab"),
                "module": "src.modules.component_lot_tracker",
                "class_name": "ComponentLotTracker",
                "unavailable": tr("mw_component_lot_tracker_unavailable"),
                "log_message": "ComponentLotTracker import failed",
            },
            {
                "title": tr("mw_batch_workspace_title"),
                "module": "src.modules.batch_workspace",
                "class_name": "BatchWorkspace",
                "unavailable": tr("mw_batch_workspace_unavailable"),
                "log_message": "BatchWorkspace import failed",
            },
            {
                "title": tr("mw_saami_checker_tab"),
                "module": "src.modules.saami_compliance_checker",
                "class_name": "SAAMIComplianceChecker",
                "unavailable": tr("mw_saami_checker_unavailable_short"),
                "log_message": "SAAMIComplianceChecker import failed",
            },
            {
                "title": tr("mw_ballistics_simulator_title"),
                "module": "src.modules.ballistics_simulator",
                "class_name": "BallisticsSimulator",
                "unavailable": tr("mw_ballistics_simulator_unavailable"),
                "log_message": "BallisticsSimulator import failed",
            },
        ]

        for spec in tab_specs:
            self._add_tab_from_module(
                tabs,
                spec["title"],
                spec["module"],
                spec["class_name"],
                spec["unavailable"],
                spec["log_message"],
                allow_non_widget=spec.get("allow_non_widget", False),
                wrap_label=spec.get("wrap_label"),
                legacy=bool(spec.get("legacy", False)),
            )

        # Tab 4: Statistikk (live summary)
        stats_widget = self._build_stats_tab()
        tabs.addTab(stats_widget, tr("mw_statistics_tab"))

        return widget

    def _build_stats_tab(self) -> "QWidget":
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel(tr("mw_statistics_overview"))
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([tr("mw_metric"), tr("mw_value")])
        try:
            header = table.horizontalHeader()
            if header is not None:
                header.setStretchLastSection(True)
        except Exception:
            pass
        layout.addWidget(table)

        self._stats_table = table
        self._refresh_stats_table()

        refresh_btn = QPushButton(tr("mw_refresh"))
        refresh_btn.clicked.connect(self._refresh_stats_table)
        layout.addWidget(refresh_btn)

        layout.addStretch()
        return widget

    def _refresh_stats_table(self) -> None:
        table = getattr(self, "_stats_table", None)
        if table is None:
            return

        metrics: list[tuple[str, str]] = []
        try:
            db = getattr(self, "db", None)
            if db is None:
                from ..database import get_database

                db = get_database()
            cur = getattr(db, "cursor", None)
            if cur is None:
                raise RuntimeError("No database cursor")
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in (cur.fetchall() or [])]
            metrics.append((tr("mw_tables"), str(len(tables))))

            candidates = [
                "firearm",
                "component_bullet",
                "component_powder",
                "component_primer",
                "component_case",
                "pressure_history",
                "pressure_signs",
                "chronograph_sessions",
                "chronograph_imports",
                "load_data",
            ]
            for name in candidates:
                if name not in tables:
                    continue
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {name}")
                    row = cur.fetchone()
                    if row is not None:
                        metrics.append(
                            (tr("mw_rows_for_table", table=name), str(row[0]))
                        )
                except Exception:
                    continue
        except Exception:
            metrics = [(tr("mw_stats"), tr("mw_unavailable"))]

        try:
            table.setRowCount(len(metrics))
            for idx, (label, value) in enumerate(metrics):
                table.setItem(idx, 0, QTableWidgetItem(label))
                table.setItem(idx, 1, QTableWidgetItem(value))
        except Exception:
            pass

    def create_settings_tab(self):
        """Oppretter innstillinger-fanen"""
        try:
            from ..modules.settings import SettingsWidget

            return SettingsWidget()
        except Exception as e:
            logger.exception("SettingsWidget import failed: %s", e)
            w = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(tr("mw_settings_unavailable")))
            w.setLayout(layout)
            return w

        def _build_stats_tab(self) -> "QWidget":
            widget = QWidget()
            layout = QVBoxLayout()
            widget.setLayout(layout)

            title = QLabel(tr("mw_stats_trends_title"))
            try:
                title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            except Exception:
                pass
            layout.addWidget(title)

            summary = QLabel(tr("mw_loading_statistics"))
            summary.setWordWrap(True)
            layout.addWidget(summary)

            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels([tr("mw_table"), tr("mw_rows")])
            try:
                table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
            except Exception:
                pass
            layout.addWidget(table)

            refresh = QPushButton(tr("mw_refresh"))
            refresh.clicked.connect(lambda: self._refresh_stats_tab(table, summary))
            layout.addWidget(refresh)

            self._refresh_stats_tab(table, summary)
            layout.addStretch()
            return widget

        def _refresh_stats_tab(self, table: "QTableWidget", summary: "QLabel") -> None:
            try:
                from ..database import get_database

                db = get_database()
                cur = db.conn.cursor() if db and getattr(db, "conn", None) else None
            except Exception:
                cur = None

            if cur is None:
                summary.setText(tr("mw_no_database_available"))
                table.setRowCount(0)
                return

            try:
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
                tables = [row[0] for row in cur.fetchall()]
            except Exception:
                tables = []

            rows_total = 0
            table.setRowCount(0)

            for name in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {name}")
                    count = int(cur.fetchone()[0])
                except Exception:
                    count = 0
                row = table.rowCount()
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(name))
                table.setItem(row, 1, QTableWidgetItem(str(count)))
                rows_total += count

            summary.setText(f"Tabeller: {len(tables)} · Totale rader: {rows_total}")

    def _open_path(self, path: str, label: str) -> None:
        if not path:
            self._show_status_message(tr("mw_path_unavailable", label=label))
            return
        try:
            if not os.path.exists(path):
                self._show_status_message(tr("mw_path_not_found", label=label))
                return
        except Exception:
            pass

        opened = False
        try:
            url = QUrl.fromLocalFile(path)
            opened = bool(QDesktopServices.openUrl(url))
        except Exception:
            opened = False

        if not opened:
            try:
                if os.name == "nt":
                    os.startfile(path)  # type: ignore[attr-defined]
                    opened = True
            except Exception:
                opened = False

        if opened:
            self._show_status_message(tr("mw_opened_label", label=label))
        else:
            self._show_status_message(tr("mw_could_not_open_label", label=label))

    def open_logs_folder(self) -> None:
        self._open_path(get_log_dir(), "logs folder")

    def open_config_folder(self) -> None:
        path = ""
        try:
            app_config = importlib.import_module("HjemmeladingApp.config")
            path = str(app_config.get_config_dir())
        except Exception:
            path = ""
        self._open_path(path, "config folder")

    def open_docs_folder(self) -> None:
        path = ""
        try:
            from pathlib import Path

            root = Path(__file__).resolve().parents[2]
            path = str(root / "docs")
        except Exception:
            path = ""
        self._open_path(path, "docs folder")

    def _build_workflow_report_export_payload(self) -> dict[str, object]:
        workflow_status = self._get_active_workflow_status()
        workflow_name = str(workflow_status.get("workflow_name", "") or "").strip()
        if not workflow_name and not workflow_status:
            return {}

        internal_ballistics_case_context = [
            str(item)
            for item in (
                workflow_status.get("internal_ballistics_case_context", []) or []
            )
            if str(item or "").strip()
        ]
        internal_ballistics_message = str(
            workflow_status.get("internal_ballistics_message", "") or ""
        ).strip()
        if internal_ballistics_case_context:
            internal_ballistics_message = " | ".join(
                bit
                for bit in [
                    internal_ballistics_message,
                    *internal_ballistics_case_context[:2],
                ]
                if bit
            )

        summary_rows = [
            {
                "section": "Workflow",
                "title": workflow_name or "-",
                "message": str(workflow_status.get("message", "") or ""),
                "level": str(workflow_status.get("level", "") or ""),
            },
            {
                "section": "Impact Window",
                "title": str(workflow_status.get("impact_title", "") or ""),
                "message": str(workflow_status.get("impact_message", "") or ""),
                "level": str(workflow_status.get("impact_level", "") or ""),
            },
            {
                "section": "Evidenskvalitet",
                "title": str(workflow_status.get("evidence_quality_title", "") or ""),
                "message": str(
                    workflow_status.get("evidence_quality_message", "") or ""
                ),
                "level": str(workflow_status.get("evidence_quality_level", "") or ""),
            },
            {
                "section": "Calibration",
                "title": str(workflow_status.get("calibration_title", "") or ""),
                "message": str(workflow_status.get("calibration_message", "") or ""),
                "level": str(workflow_status.get("calibration_level", "") or ""),
            },
            {
                "section": "Internal Ballistics",
                "title": str(
                    workflow_status.get("internal_ballistics_title", "") or ""
                ),
                "message": internal_ballistics_message,
                "level": str(
                    workflow_status.get("internal_ballistics_level", "") or ""
                ),
            },
            {
                "section": "Environment",
                "title": str(workflow_status.get("environment_title", "") or ""),
                "message": str(workflow_status.get("environment_message", "") or ""),
                "level": "",
            },
            {
                "section": "Uncertainty",
                "title": "Uncertainty Summary",
                "message": " | ".join(
                    str(item)
                    for item in (workflow_status.get("uncertainty_summary", []) or [])
                ),
                "level": "",
            },
            {
                "section": "Observerte trykksignaler",
                "title": "Trykknotater",
                "message": " | ".join(
                    str(item)
                    for item in (workflow_status.get("pressure_notes", []) or [])
                ),
                "level": "",
            },
        ]
        summary_rows = [
            row
            for row in summary_rows
            if any(
                str(row.get(key) or "").strip() for key in ("title", "message", "level")
            )
        ]

        return {
            "workflow_name": workflow_name,
            "usage_profile": str(workflow_status.get("usage_profile", "") or ""),
            "readiness": {
                "title": str(workflow_status.get("title", "") or ""),
                "message": str(workflow_status.get("message", "") or ""),
                "level": str(workflow_status.get("level", "") or ""),
                "confidence_label": str(
                    workflow_status.get("confidence_label", "") or ""
                ),
                "confidence_message": str(
                    workflow_status.get("confidence_message", "") or ""
                ),
            },
            "uncertainty": {
                "checks": list(workflow_status.get("uncertainty_summary", []) or []),
            },
            "impact_window": {
                "title": str(workflow_status.get("impact_title", "") or ""),
                "message": str(workflow_status.get("impact_message", "") or ""),
                "level": str(workflow_status.get("impact_level", "") or ""),
                "checks": list(workflow_status.get("impact_checks", []) or []),
                "drag_model": str(workflow_status.get("impact_drag_model", "") or ""),
                "bc_used": str(workflow_status.get("impact_bc_used", "") or ""),
                "bc_segment": str(workflow_status.get("impact_bc_segment", "") or ""),
                "density_altitude_m": str(
                    workflow_status.get("impact_density_altitude_m", "") or ""
                ),
                "confidence_label": str(
                    workflow_status.get("impact_confidence_label", "") or ""
                ),
                "confidence_message": str(
                    workflow_status.get("impact_confidence_message", "") or ""
                ),
            },
            "evidence_quality": {
                "title": str(workflow_status.get("evidence_quality_title", "") or ""),
                "message": str(
                    workflow_status.get("evidence_quality_message", "") or ""
                ),
                "level": str(workflow_status.get("evidence_quality_level", "") or ""),
                "checks": list(
                    workflow_status.get("evidence_quality_checks", []) or []
                ),
            },
            "calibration": {
                "title": str(workflow_status.get("calibration_title", "") or ""),
                "message": str(workflow_status.get("calibration_message", "") or ""),
                "level": str(workflow_status.get("calibration_level", "") or ""),
                "score": str(workflow_status.get("calibration_score", "") or ""),
                "checks": list(workflow_status.get("calibration_checks", []) or []),
            },
            "internal_ballistics": {
                "title": str(
                    workflow_status.get("internal_ballistics_title", "") or ""
                ),
                "message": str(
                    workflow_status.get("internal_ballistics_message", "") or ""
                ),
                "level": str(
                    workflow_status.get("internal_ballistics_level", "") or ""
                ),
                "metrics": list(
                    workflow_status.get("internal_ballistics_metrics", []) or []
                ),
                "checks": list(
                    workflow_status.get("internal_ballistics_checks", []) or []
                ),
                "case_context": internal_ballistics_case_context,
            },
            "environment": {
                "title": str(workflow_status.get("environment_title", "") or ""),
                "message": str(workflow_status.get("environment_message", "") or ""),
                "checks": list(workflow_status.get("environment_checks", []) or []),
            },
            "pressure_notes": list(workflow_status.get("pressure_notes", []) or []),
            "measured_series": {
                "chronograph": list(
                    workflow_status.get("chronograph_summary", []) or []
                ),
                "shooting": list(workflow_status.get("shooting_summary", []) or []),
                "accuracy_tests": list(
                    workflow_status.get("accuracy_test_summary", []) or []
                ),
            },
            "report_plot": {
                "x": list(workflow_status.get("report_plot_x", []) or []),
                "y": list(workflow_status.get("report_plot_y", []) or []),
                "x_label": str(workflow_status.get("report_plot_xlabel", "") or ""),
                "y_label": str(workflow_status.get("report_plot_ylabel", "") or ""),
            },
            "summary_rows": summary_rows,
        }

    def _build_workflow_pdf_report_data(self) -> dict[str, object]:
        workflow_status = self._get_active_workflow_status()
        workflow_name = str(workflow_status.get("workflow_name", "") or "").strip()
        setup_label = str(workflow_status.get("setup_label", "") or "").strip()
        title = (
            f"Workflow Report - {workflow_name}" if workflow_name else "Session Report"
        )
        sections: dict[str, list[str]] = {}
        if setup_label:
            sections["Setup"] = [setup_label]
        evidence_checks = list(workflow_status.get("evidence_quality_checks", []) or [])
        if evidence_checks:
            sections["Evidence Quality"] = [str(item) for item in evidence_checks[:5]]
        uncertainty_summary = list(workflow_status.get("uncertainty_summary", []) or [])
        if uncertainty_summary:
            sections["Uncertainty"] = [str(item) for item in uncertainty_summary[:5]]
        calibration_checks = list(workflow_status.get("calibration_checks", []) or [])
        calibration_title = str(
            workflow_status.get("calibration_title", "") or ""
        ).strip()
        calibration_message = str(
            workflow_status.get("calibration_message", "") or ""
        ).strip()
        if calibration_message:
            sections[calibration_title or "Calibration Profile"] = [
                calibration_message,
                *[str(item) for item in calibration_checks[:4]],
            ]
        impact_message = str(workflow_status.get("impact_message", "") or "").strip()
        impact_checks = list(workflow_status.get("impact_checks", []) or [])
        impact_drag_model = str(
            workflow_status.get("impact_drag_model", "") or ""
        ).strip()
        impact_bc_used = str(workflow_status.get("impact_bc_used", "") or "").strip()
        impact_bc_segment = str(
            workflow_status.get("impact_bc_segment", "") or ""
        ).strip()
        impact_confidence_label = str(
            workflow_status.get("impact_confidence_label", "") or ""
        ).strip()
        impact_confidence_message = str(
            workflow_status.get("impact_confidence_message", "") or ""
        ).strip()
        impact_density_altitude_m = str(
            workflow_status.get("impact_density_altitude_m", "") or ""
        ).strip()
        impact_lines: list[str] = []
        if impact_message:
            impact_lines.append(impact_message)
        if impact_drag_model or impact_bc_used:
            impact_lines.append(
                f"Drag basis: {impact_drag_model or '-'} / BC {impact_bc_used or '-'}"
            )
        if impact_bc_segment:
            impact_lines.append(f"Segmented BC: {impact_bc_segment}")
        if impact_density_altitude_m:
            impact_lines.append(
                f"Density altitude in the assessment: approx. {impact_density_altitude_m} m"
            )
        if impact_confidence_label or impact_confidence_message:
            impact_lines.append(
                f"{impact_confidence_label}: {impact_confidence_message}".strip(": ")
            )
        impact_lines.extend(str(item) for item in impact_checks[:4])
        if impact_lines:
            sections[
                str(workflow_status.get("impact_title", "") or "Impact Window")
            ] = impact_lines
        internal_ballistics_summary = None
        internal_ballistics_title = str(
            workflow_status.get("internal_ballistics_title", "") or ""
        ).strip()
        internal_ballistics_message = str(
            workflow_status.get("internal_ballistics_message", "") or ""
        ).strip()
        internal_ballistics_checks = list(
            workflow_status.get("internal_ballistics_checks", []) or []
        )
        internal_ballistics_metrics = list(
            workflow_status.get("internal_ballistics_metrics", []) or []
        )
        internal_ballistics_case_context = [
            str(item)
            for item in (
                workflow_status.get("internal_ballistics_case_context", []) or []
            )
            if str(item or "").strip()
        ]
        if (
            internal_ballistics_title
            or internal_ballistics_message
            or internal_ballistics_metrics
            or internal_ballistics_checks
        ):
            internal_ballistics_summary = {
                "title": internal_ballistics_title or "Internal Ballistics",
                "message": internal_ballistics_message,
                "metrics": internal_ballistics_metrics,
                "context_lines": internal_ballistics_case_context,
            }
            if internal_ballistics_checks:
                sections["Internal Ballistics Checks"] = [
                    str(item) for item in internal_ballistics_checks[:5]
                ]
        environment_message = str(
            workflow_status.get("environment_message", "") or ""
        ).strip()
        environment_checks = list(workflow_status.get("environment_checks", []) or [])
        if environment_message or environment_checks:
            sections[
                str(workflow_status.get("environment_title", "") or "Environment")
            ] = [
                *([environment_message] if environment_message else []),
                *[str(item) for item in environment_checks[:4]],
            ]
        chronograph_summary = list(workflow_status.get("chronograph_summary", []) or [])
        if chronograph_summary:
            sections["Chronograph Series"] = [
                str(item) for item in chronograph_summary[:5]
            ]
        shooting_summary = list(workflow_status.get("shooting_summary", []) or [])
        if shooting_summary:
            sections["Group Series"] = [str(item) for item in shooting_summary[:5]]
        accuracy_test_summary = list(
            workflow_status.get("accuracy_test_summary", []) or []
        )
        if accuracy_test_summary:
            sections["Accuracy Tests"] = [
                str(item) for item in accuracy_test_summary[:5]
            ]
        pressure_notes = list(workflow_status.get("pressure_notes", []) or [])
        if pressure_notes:
            sections["Observerte trykksignaler"] = [
                str(item) for item in pressure_notes[:5]
            ]
        data = {
            "title": title,
            "stats": {
                "workflow": workflow_name or "-",
                "readiness": str(workflow_status.get("title", "") or "-"),
                "impact_window": str(workflow_status.get("impact_title", "") or "-"),
                "evidence_quality": str(
                    workflow_status.get("evidence_quality_title", "") or "-"
                ),
                "calibration": str(workflow_status.get("calibration_title", "") or "-"),
            },
            "internal_ballistics_summary": internal_ballistics_summary,
            "sections": sections,
            "x": list(workflow_status.get("report_plot_x", []) or []),
            "y": list(workflow_status.get("report_plot_y", []) or []),
            "x_label": str(workflow_status.get("report_plot_xlabel", "") or "Serie"),
            "y_label": str(
                workflow_status.get("report_plot_ylabel", "") or "Hastighet (fps)"
            ),
        }
        if not data["x"] or not data["y"] or len(data["x"]) != len(data["y"]):
            data["x"] = ["Serie 1", "Serie 2", "Serie 3"]
            data["y"] = [820.0, 825.0, 830.0]
        return data

    def _build_workflow_pdf_report_bytes(self) -> bytes:
        report_mod = importlib.import_module("scripts.generate_pdf_report")
        generate_pdf_report = getattr(report_mod, "generate_pdf_report", None)
        if not callable(generate_pdf_report):
            raise RuntimeError(tr("mw_generate_pdf_unavailable"))
        data = self._build_workflow_pdf_report_data()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            generate_pdf_report(data, tmp_path)
            with open(tmp_path, "rb") as fh:
                return fh.read()
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def export_report_pack(self) -> None:
        try:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            default_name = f"valkyrie_export_pack_{ts}.zip"
        except Exception:
            default_name = "valkyrie_export_pack.zip"

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                tr("mw_export_pack"),
                default_name,
                tr("mw_zip_files_filter"),
            )
        except Exception:
            file_path = ""

        if not file_path:
            return

        if not file_path.lower().endswith(".zip"):
            file_path += ".zip"

        entries: list[tuple[str, str]] = []
        export_payloads: dict[str, object] = {}
        dataset_counts: dict[str, int] = {}
        errors: list[str] = []

        db = getattr(self, "db", None)
        if db is None:
            try:
                from ..database import get_database

                db = get_database()
            except Exception:
                db = None

        def _safe_json(value: Any) -> Any:
            if value is None or value == "":
                return None
            if isinstance(value, (dict, list)):
                return value
            try:
                return json.loads(value)
            except Exception:
                return None

        def _query_rows(
            sql: str, params: tuple = (), label: str | None = None
        ) -> list[dict[str, Any]]:
            try:
                if db is None or getattr(db, "conn", None) is None:
                    return []
                cur = db.conn.execute(sql, params)
                rows = cur.fetchall() or []
                return [dict(row) for row in rows]
            except Exception as exc:
                if label:
                    errors.append(f"{label}: {exc}")
                return []

        def _table_exists(name: str) -> bool:
            rows = _query_rows(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                (name,),
            )
            return bool(rows)

        def _rows_to_csv(rows: list[dict[str, Any]]) -> str:
            if not rows:
                return ""
            fieldnames: list[str] = []
            for row in rows:
                for key in row.keys():
                    if key not in fieldnames:
                        fieldnames.append(key)
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k) for k in fieldnames})
            return buf.getvalue()

        def _add_dataset(
            name: str,
            rows: list[dict[str, Any]],
            base_name: str | None = None,
            include_csv: bool = True,
            include_json: bool = True,
        ) -> None:
            dataset_counts[name] = len(rows)
            base = base_name or name
            if include_json:
                export_payloads[f"exports/{base}.json"] = json.dumps(
                    rows,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
            if include_csv and rows:
                export_payloads[f"exports/{base}.csv"] = _rows_to_csv(rows)

        workflow_export = self._build_workflow_report_export_payload()
        if workflow_export:
            export_payloads["exports/workflow_report.json"] = json.dumps(
                workflow_export,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
            export_rows = workflow_export.get("summary_rows") or []
            if isinstance(export_rows, list) and export_rows:
                export_payloads["exports/workflow_report.csv"] = _rows_to_csv(
                    [row for row in export_rows if isinstance(row, dict)]
                )
                dataset_counts["workflow_report"] = len(export_rows)
            try:
                pdf_bytes = self._build_workflow_pdf_report_bytes()
                if pdf_bytes:
                    export_payloads["exports/workflow_report.pdf"] = pdf_bytes
                    dataset_counts["workflow_report_pdf"] = 1
            except Exception as exc:
                errors.append(f"workflow_report_pdf: {exc}")

        try:
            get_config_path = getattr(
                importlib.import_module("HjemmeladingApp.config"), "get_config_path"
            )
            cfg_path = get_config_path()
            if cfg_path.exists():
                entries.append((str(cfg_path), "config/config.json"))
        except Exception:
            pass

        try:
            log_dir = get_log_dir()
            if os.path.isdir(log_dir):
                for root, _dirs, files in os.walk(log_dir):
                    for name in files:
                        src = os.path.join(root, name)
                        rel = os.path.relpath(src, log_dir)
                        entries.append((src, os.path.join("logs", rel)))
        except Exception:
            pass

        db_path = ""
        try:
            if db is not None:
                db_path = getattr(db, "db_path", "") or ""
        except Exception:
            db_path = ""
        if not db_path:
            try:
                project_path = self._get_current_project_path()
                db_path = os.path.join(project_path, "data", "reloading.db")
            except Exception:
                db_path = ""
        if db_path and os.path.exists(db_path):
            entries.append((db_path, "data/reloading.db"))

        if db is not None:
            if _table_exists("chronograph_sessions"):
                chrono_rows = _query_rows(
                    """
                    SELECT
                        cs.id AS session_id,
                        cs.session_date,
                        cs.session_name,
                        cs.device_type,
                        cs.avg_velocity_fps,
                        cs.sd_fps,
                        cs.es_fps,
                        cs.min_velocity_fps,
                        cs.max_velocity_fps,
                        cs.shot_count,
                        cs.temperature_f,
                        cs.notes,
                        cs.import_source,
                        cs.import_meta_json,
                        cs.created_date,
                        ap.id AS ammo_profile_id,
                        ap.name AS ammo_name,
                        ap.caliber,
                        ap.powder_charge,
                        ap.bullet_weight,
                        p.name AS powder_name,
                        b.name AS bullet_name
                    FROM chronograph_sessions cs
                    LEFT JOIN ammo_profiles ap ON cs.ammo_profile_id = ap.id
                    LEFT JOIN powder p ON ap.powder_id = p.id
                    LEFT JOIN bullets b ON ap.bullet_id = b.id
                    ORDER BY cs.session_date DESC, cs.id DESC
                    """,
                    label="chronograph_sessions",
                )
                for row in chrono_rows:
                    meta = _safe_json(row.get("import_meta_json"))
                    if isinstance(meta, dict):
                        row["imported_at"] = meta.get("imported_at")
                        row["source_file"] = meta.get("source_file")
                        row["source_path"] = meta.get("source_path")
                        row["raw_sha256"] = meta.get("raw_sha256")
                        row["import_meta"] = meta
                _add_dataset("chronograph_sessions", chrono_rows)

            if _table_exists("chronograph_readings"):
                _add_dataset(
                    "chronograph_readings",
                    _query_rows(
                        "SELECT * FROM chronograph_readings ORDER BY session_id, shot_number",
                        label="chronograph_readings",
                    ),
                )

            if _table_exists("chronograph_imports"):
                _add_dataset(
                    "chronograph_imports",
                    _query_rows(
                        "SELECT * FROM chronograph_imports ORDER BY created_date DESC",
                        label="chronograph_imports",
                    ),
                )

            if _table_exists("loading_sessions"):
                _add_dataset(
                    "loading_sessions",
                    _query_rows(
                        """
                        SELECT
                            ls.*, ap.name AS ammo_name, ap.caliber AS ammo_caliber
                        FROM loading_sessions ls
                        LEFT JOIN ammo_profiles ap ON ls.ammo_profile_id = ap.id
                        ORDER BY ls.date DESC
                        """,
                        label="loading_sessions",
                    ),
                )

            if _table_exists("shooting_sessions"):
                _add_dataset(
                    "shooting_sessions",
                    _query_rows(
                        """
                        SELECT
                            ss.*, ap.name AS ammo_name, ap.caliber AS ammo_caliber, r.name AS rifle_name
                        FROM shooting_sessions ss
                        LEFT JOIN ammo_profiles ap ON ss.ammo_profile_id = ap.id
                        LEFT JOIN rifles r ON ss.rifle_id = r.id
                        ORDER BY ss.date DESC
                        """,
                        label="shooting_sessions",
                    ),
                )

            if _table_exists("comprehensive_logs"):
                comp_rows = _query_rows(
                    "SELECT * FROM comprehensive_logs ORDER BY created_at DESC",
                    label="comprehensive_logs",
                )
                comp_full: list[dict[str, Any]] = []
                comp_summary: list[dict[str, Any]] = []
                for row in comp_rows:
                    payload = _safe_json(row.get("data_json"))
                    summary_fields = {
                        "load_id": row.get("load_id"),
                        "load_name": row.get("load_name"),
                        "created_at": row.get("created_at"),
                        "updated_at": row.get("updated_at"),
                        "session_date": row.get("session_date"),
                        "session_time": row.get("session_time"),
                        "session_type": row.get("session_type"),
                        "session_location": row.get("session_location"),
                        "session_distance_m": row.get("session_distance_m"),
                        "ammo_caliber": row.get("ammo_caliber"),
                        "rifle_name": row.get("rifle_name"),
                    }
                    comp_summary.append(summary_fields)
                    full_row = dict(row)
                    full_row.pop("data_json", None)
                    full_row["data"] = payload if payload is not None else {}
                    comp_full.append(full_row)
                _add_dataset(
                    "comprehensive_logs_summary",
                    comp_summary,
                    base_name="comprehensive_logs_summary",
                )
                _add_dataset(
                    "comprehensive_logs_full",
                    comp_full,
                    base_name="comprehensive_logs_full",
                    include_csv=False,
                )

            if _table_exists("engine_benchmarks"):
                _add_dataset(
                    "engine_benchmarks",
                    _query_rows(
                        "SELECT * FROM engine_benchmarks ORDER BY created_date DESC",
                        label="engine_benchmarks",
                    ),
                )

            if _table_exists("engine_calibrations"):
                _add_dataset(
                    "engine_calibrations",
                    _query_rows(
                        "SELECT * FROM engine_calibrations ORDER BY created_date DESC",
                        label="engine_calibrations",
                    ),
                )

        if not entries and not export_payloads:
            try:
                QMessageBox.information(
                    self,
                    tr("mw_export_pack"),
                    tr("mw_export_pack_no_files"),
                )
            except Exception:
                pass
            return

        try:
            created_at = datetime.utcnow().isoformat() + "Z"
            manifest = {
                "created_at": created_at,
                "files": [arc for _src, arc in entries],
                "datasets": dataset_counts,
                "errors": errors,
            }
            manifest_lines = [
                f"created={created_at}",
                f"files={len(entries)}",
                f"exports={len(export_payloads)}",
            ]
            if errors:
                manifest_lines.append(f"errors={len(errors)}")

            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    "manifest.json",
                    json.dumps(manifest, indent=2, ensure_ascii=False),
                )
                zf.writestr("manifest.txt", "\n".join(manifest_lines) + "\n")
                for arc_path, content in export_payloads.items():
                    if isinstance(content, bytes):
                        zf.writestr(arc_path, content)
                    else:
                        zf.writestr(arc_path, content)
                for src, arc in entries:
                    try:
                        if os.path.isfile(src):
                            zf.write(src, arc)
                    except Exception:
                        continue
        except Exception:
            try:
                QMessageBox.warning(
                    self,
                    tr("mw_export_pack"),
                    tr("mw_export_pack_create_failed"),
                )
            except Exception:
                pass
            return

        try:
            QMessageBox.information(
                self,
                tr("mw_export_pack"),
                tr("mw_export_pack_created", file_path=file_path),
            )
        except Exception:
            pass

    def _project_name_from_path(self, path: str) -> str:
        try:
            name = os.path.basename(path.rstrip("\\/"))
        except Exception:
            name = ""
        return name or path

    def _normalize_project_path(self, path: str) -> str:
        try:
            return os.path.abspath(path)
        except Exception:
            return path

    def _get_default_project_entry(self) -> dict[str, str]:
        try:
            from pathlib import Path

            root = Path(__file__).resolve().parents[2]
            return {"name": "Default Project", "path": str(root)}
        except Exception:
            return {"name": "Default Project", "path": os.getcwd()}

    def _load_recent_projects(self) -> list[dict[str, str]]:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            raw = settings.value("workspace/recent_projects", "")
        except Exception:
            return []

        data = []
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return []
            try:
                data = json.loads(raw)
            except Exception:
                return []
        elif isinstance(raw, list):
            data = raw
        else:
            return []

        projects: list[dict[str, str]] = []
        for item in data:
            if isinstance(item, dict):
                path = str(item.get("path", "")).strip()
                name = str(item.get("name", "")).strip()
            elif isinstance(item, str):
                path = item.strip()
                name = ""
            else:
                continue
            if not path:
                continue
            projects.append(
                {"name": name or self._project_name_from_path(path), "path": path}
            )

        seen: set[str] = set()
        deduped: list[dict[str, str]] = []
        for proj in projects:
            key = self._normalize_project_path(proj.get("path", ""))
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(proj)
        return deduped

    def _save_recent_projects(self, projects: list[dict[str, str]]) -> None:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.setValue("workspace/recent_projects", json.dumps(projects))
        except Exception:
            pass

    def _load_pinned_projects(self) -> list[str]:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            raw = settings.value("workspace/pinned_projects", "")
        except Exception:
            return []

        items: list[str] = []
        if isinstance(raw, str):
            raw = raw.strip()
            if raw:
                try:
                    items = json.loads(raw)
                except Exception:
                    items = []
        elif isinstance(raw, list):
            items = raw

        pinned: list[str] = []
        seen: set[str] = set()
        for item in items:
            if isinstance(item, dict):
                path = str(item.get("path", "")).strip()
            else:
                path = str(item).strip()
            if not path:
                continue
            norm = self._normalize_project_path(path)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            pinned.append(norm)
        return pinned

    def _save_pinned_projects(self, pinned: list[str]) -> None:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.setValue("workspace/pinned_projects", json.dumps(pinned))
        except Exception:
            pass

    def _add_recent_project(self, path: str, name: str | None = None) -> None:
        if not path:
            return
        path = self._normalize_project_path(path)
        if not name:
            name = self._project_name_from_path(path)

        projects = self._load_recent_projects()
        cleaned: list[dict[str, str]] = []
        for proj in projects:
            if self._normalize_project_path(proj.get("path", "")) == path:
                continue
            cleaned.append(proj)

        cleaned.insert(
            0,
            {
                "name": name,
                "path": path,
                "last_opened": datetime.utcnow().isoformat(),
            },
        )
        cleaned = cleaned[:8]
        self._save_recent_projects(cleaned)

    def _remove_recent_project(self, path: str) -> None:
        if not path:
            return
        norm = self._normalize_project_path(path)
        projects = [
            p
            for p in self._load_recent_projects()
            if self._normalize_project_path(p.get("path", "")) != norm
        ]
        self._save_recent_projects(projects)
        self._unpin_project(norm)
        self._refresh_project_picker()
        self._refresh_recent_projects_ui()

    def _is_pinned_project(self, path: str) -> bool:
        norm = self._normalize_project_path(path)
        return norm in self._load_pinned_projects()

    def _pin_project(self, path: str) -> None:
        if not path:
            return
        norm = self._normalize_project_path(path)
        pinned = [p for p in self._load_pinned_projects() if p != norm]
        pinned.insert(0, norm)
        self._save_pinned_projects(pinned[:8])

    def _unpin_project(self, path: str) -> None:
        if not path:
            return
        norm = self._normalize_project_path(path)
        pinned = [p for p in self._load_pinned_projects() if p != norm]
        self._save_pinned_projects(pinned)

    def _toggle_pin_project(self, path: str) -> None:
        if not path:
            return
        if self._is_pinned_project(path):
            self._unpin_project(path)
        else:
            self._pin_project(path)
        self._refresh_project_picker()
        self._refresh_recent_projects_ui()

    def _get_current_project_path(self) -> str:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            current = settings.value("workspace/current_project", "")
            if current:
                return str(current)
        except Exception:
            pass
        default_path = self._get_default_project_entry().get("path", os.getcwd())
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.setValue("workspace/current_project", default_path)
        except Exception:
            pass
        try:
            from ..database import get_default_db_path

            os.environ["HJEMMELADING_PROJECT_PATH"] = default_path
            os.environ["HJEMMELADING_DB_PATH"] = str(get_default_db_path())
        except Exception:
            pass
        return default_path

    def _set_current_project(self, path: str) -> None:
        if not path:
            return
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.setValue("workspace/current_project", path)
        except Exception:
            pass
        try:
            from ..database import get_default_db_path

            os.environ["HJEMMELADING_PROJECT_PATH"] = path
            os.environ["HJEMMELADING_DB_PATH"] = str(get_default_db_path())
        except Exception:
            pass
        self._show_status_message(
            f"Active project: {self._project_name_from_path(path)}"
        )

    def _refresh_project_picker(self) -> None:
        combo = getattr(self, "project_combo", None)
        if combo is None:
            return
        try:
            self._project_combo_updating = True
            combo.blockSignals(True)
        except Exception:
            pass

        try:
            combo.clear()
            default_proj = self._get_default_project_entry()
            combo.addItem(default_proj["name"], default_proj["path"])

            pinned = self._load_pinned_projects()
            recent = self._load_recent_projects()
            recent_map = {self._normalize_project_path(p["path"]): p for p in recent}
            default_norm = self._normalize_project_path(default_proj["path"])

            for path in pinned:
                if self._normalize_project_path(path) == default_norm:
                    continue
                entry = recent_map.get(self._normalize_project_path(path))
                name = entry["name"] if entry else self._project_name_from_path(path)
                combo.addItem(tr("mw_pinned_project", name=name), path)

            if pinned:
                try:
                    combo.insertSeparator(combo.count())
                except Exception:
                    pass

            for proj in recent:
                norm = self._normalize_project_path(proj["path"])
                if norm == default_norm or norm in pinned:
                    continue
                combo.addItem(proj["name"], proj["path"])

            try:
                combo.insertSeparator(combo.count())
            except Exception:
                pass

            combo.addItem(tr("mw_new_project"), "__new__")
            combo.addItem(tr("mw_add_project_folder"), "__browse__")

            current = self._get_current_project_path()
            idx = combo.findData(current)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
        except Exception:
            pass
        finally:
            try:
                combo.blockSignals(False)
            except Exception:
                pass
            self._project_combo_updating = False

    def _on_project_selected(self, index: int) -> None:
        if getattr(self, "_project_combo_updating", False):
            return
        try:
            data = self.project_combo.itemData(index)
        except Exception:
            return

        if data == "__browse__":
            self._prompt_add_project()
            return

        if data == "__new__":
            self._prompt_new_project()
            return

        if isinstance(data, str) and data:
            self._set_current_project(data)
            self._add_recent_project(data)
            self._refresh_project_picker()
            self._refresh_recent_projects_ui()

    def _prompt_add_project(self) -> None:
        try:
            path = QFileDialog.getExistingDirectory(
                self, tr("mw_select_project_folder")
            )
        except Exception:
            path = ""

        if not path:
            self._refresh_project_picker()
            return

        self._add_recent_project(path)
        self._set_current_project(path)
        self._refresh_project_picker()
        self._refresh_recent_projects_ui()

    def _prompt_new_project(self) -> None:
        try:
            from .project_wizard import NewProjectDialog

            dialog = NewProjectDialog(self)
            if dialog.exec():
                if getattr(dialog, "project_path", ""):
                    self._activate_project(dialog.project_path)
                    if getattr(dialog, "pin_project", False):
                        self._pin_project(dialog.project_path)
            self._refresh_project_picker()
            self._refresh_recent_projects_ui()
        except Exception:
            self._show_status_message(tr("mw_new_project_wizard_unavailable"))

    def show_new_project_dialog(self) -> None:
        self._prompt_new_project()

    def open_active_project_folder(self) -> None:
        self._open_path(self._get_current_project_path(), "project folder")

    def _activate_project(self, path: str) -> None:
        if not path:
            return
        self._add_recent_project(path)
        self._set_current_project(path)
        self._refresh_project_picker()
        self._refresh_recent_projects_ui()

    def _refresh_recent_projects_ui(self) -> None:
        layout = getattr(self, "_recent_projects_layout", None)
        if layout is None:
            return
        try:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
        except Exception:
            pass

        projects = self._load_recent_projects()
        pinned = self._load_pinned_projects()
        project_map = {self._normalize_project_path(p["path"]): p for p in projects}

        ordered: list[tuple[dict[str, str], bool]] = []
        for path in pinned:
            entry = project_map.get(self._normalize_project_path(path))
            if entry is None:
                entry = {
                    "name": self._project_name_from_path(path),
                    "path": path,
                }
            ordered.append((entry, True))

        for proj in projects:
            norm = self._normalize_project_path(proj["path"])
            if norm in pinned:
                continue
            ordered.append((proj, False))

        if not ordered:
            empty = QLabel(tr("mw_no_recent_projects"))
            empty.setObjectName("cardSubtitle")
            empty.setWordWrap(True)
            layout.addWidget(empty)
        else:
            for proj, is_pinned in ordered[:6]:
                row = QWidget()
                row_layout = QHBoxLayout()
                try:
                    row_layout.setContentsMargins(0, 0, 0, 0)
                except Exception:
                    pass
                row.setLayout(row_layout)

                btn = QPushButton(proj["name"])
                try:
                    btn.setProperty("variant", "secondary")
                except Exception:
                    pass
                try:
                    btn.setToolTip(proj["path"])
                except Exception:
                    pass
                btn.clicked.connect(
                    lambda _=False, path=proj["path"]: self._activate_project(path)
                )
                row_layout.addWidget(btn, 1)

                pin_label = tr("mw_unpin") if is_pinned else tr("mw_pin")
                pin_btn = QPushButton(pin_label)
                pin_btn.clicked.connect(
                    lambda _=False, path=proj["path"]: self._toggle_pin_project(path)
                )
                row_layout.addWidget(pin_btn)

                if not is_pinned:
                    remove_btn = QPushButton(tr("mw_remove"))
                    remove_btn.clicked.connect(
                        lambda _=False, path=proj["path"]: self._remove_recent_project(
                            path
                        )
                    )
                    row_layout.addWidget(remove_btn)

                layout.addWidget(row)

        action_row = QWidget()
        action_layout = QHBoxLayout()
        try:
            action_layout.setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass
        action_row.setLayout(action_layout)

        new_btn = QPushButton(tr("mw_new_project"))
        new_btn.clicked.connect(self.show_new_project_dialog)
        action_layout.addWidget(new_btn)

        add_btn = QPushButton(tr("mw_add_project_folder"))
        add_btn.clicked.connect(self._prompt_add_project)
        action_layout.addWidget(add_btn)

        open_btn = QPushButton(tr("mw_open_active_folder"))
        open_btn.clicked.connect(self.open_active_project_folder)
        action_layout.addWidget(open_btn)

        action_layout.addStretch()
        layout.addWidget(action_row)

    def _maybe_show_first_run_setup(self) -> None:
        if os.environ.get("VALKYRIE_SAFE_UI", "").lower() in ("1", "true"):
            return
        try:
            if _is_headless():
                return
        except Exception:
            return
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            seen = settings.value("setup/first_run_completed", False, type=bool)
            if seen:
                return

            def _show():
                try:
                    self.show_first_run_setup()
                except Exception:
                    pass

            QTimer.singleShot(600, _show)
        except Exception:
            pass

    def show_first_run_setup(self) -> None:
        try:
            from .onboarding import FirstRunSetupDialog

            dlg = FirstRunSetupDialog(self)
            dlg.exec()
        except Exception:
            self._show_status_message(tr("mw_setup_wizard_unavailable"))

    def show_quick_tour(self) -> None:
        try:
            from .onboarding import OnboardingDialog

            dlg = OnboardingDialog(self)
            dlg.exec()
        except Exception:
            self._show_status_message(tr("mw_quick_tour_unavailable"))

    def show_ai_chat(self) -> None:
        """Show the local guidance chat window."""
        try:
            from ..modules.ai_chat_assistant import AIChatAssistant

            win = AIChatAssistant()
            win.setWindowTitle(tr("mw_ai_chat_title"))
            win.resize(900, 700)
            win.show()
            self._ai_chat_window = win
        except Exception:
            self._show_status_message(tr("mw_ai_chat_unavailable"))

    def show_keyboard_shortcuts(self) -> None:
        QMessageBox.information(
            self,
            tr("mw_keyboard_shortcuts_title"),
            tr("mw_keyboard_shortcuts_html"),
        )

    def show_about(self):
        """Viser 'Om programmet' dialog"""
        QMessageBox.about(
            self,
            tr("mw_about_title"),
            tr("mw_about_html"),
        )

    def show_zero_shift_calculator(self):
        """Viser Zero Shift Calculator som en ny tab"""
        # Sjekk om tab allerede eksisterer
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tr("mw_zero_shift_tab"):
                self.tabs.setCurrentIndex(i)
                return

        # Opprett ny tab
        try:
            from ..modules.zero_shift_calculator import ZeroShiftCalculator

            zero_shift_widget = ZeroShiftCalculator()
            self.tabs.addTab(zero_shift_widget, tr("mw_zero_shift_tab"))
            self.tabs.setCurrentWidget(zero_shift_widget)
        except Exception as e:
            logger.exception("ZeroShiftCalculator import failed: %s", e)
            QMessageBox.warning(
                self,
                tr("mw_unavailable"),
                tr("mw_zero_shift_unavailable"),
            )

    def show_harmonic_wizard(self):
        """Legacy alias for the harmonics-focused load workspace."""
        self.show_harmonics_lab()

    def show_workflow_hub(self):
        """Show workflow hub landing page (lazy init).

        Instantiate `WorkflowHub` on first request to avoid heavy UI
        construction during MainWindow.__init__ and prevent transient
        top-level windows at startup.
        """
        try:
            # Diagnostic: entering show_workflow_hub
            try:
                from datetime import datetime as _dt
                from pathlib import Path as _P

                trace_file = _P(get_log_dir()) / "startup_trace.log"
                with open(trace_file, "a", encoding="utf-8") as _tf:
                    _tf.write(
                        f"startup: enter_show_workflow_hub time={_dt.utcnow().isoformat()}\n"
                    )
            except Exception:
                pass

            # Lazy-create the WorkflowHub and parent it to the main window so
            # created widgets are not top-levels. Prefer the newer signature
            # that accepts `defer_ui=True` to avoid immediate heavy init.
            if not isinstance(getattr(self, "workflow_hub", None), QWidget):
                try:
                    from ..modules.workflow_hub import WorkflowHub

                    self.workflow_hub = self._instantiate_factory(
                        WorkflowHub,
                        self,
                        self.state_manager,
                        self.mode_manager,
                        defer_ui=True,
                    )

                    try:
                        workflow_hub = getattr(self, "workflow_hub", None)
                        if workflow_hub is not None:
                            workflow_hub.workflow_selected.connect(self.launch_workflow)
                    except Exception:
                        pass

                    try:
                        workflow_hub = getattr(self, "workflow_hub", None)
                        if workflow_hub is not None:
                            self.stacked_widget.addWidget(workflow_hub)
                    except Exception:
                        pass
                except Exception as e:
                    logger.exception("WorkflowHub import/creation failed: %s", e)
                    self._show_status_message(tr("mw_workflow_hub_load_failed"))
                    return

            # Ensure the deferred UI is created now that the user explicitly
            # requested it (no-op if already initialized).
            try:
                if getattr(self.workflow_hub, "ensure_ui", None):
                    workflow_hub = getattr(self, "workflow_hub", None)
                    if workflow_hub is not None:
                        workflow_hub.ensure_ui()
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

            self.label_current_workflow.setText(tr("mw_workflow_hub"))
            try:
                self._show_status_message(tr("mw_workflow_hub_status"))
            except Exception:
                pass
            try:
                self._set_nav_active("workspace")
            except Exception:
                pass

            # Exit trace
            try:
                from datetime import datetime as _dt
                from pathlib import Path as _P

                trace_file = _P(get_log_dir()) / "startup_trace.log"
                with open(trace_file, "a", encoding="utf-8") as _tf:
                    _tf.write(
                        f"startup: exit_show_workflow_hub time={_dt.utcnow().isoformat()}\n"
                    )
            except Exception:
                pass
        except Exception as e:
            logger.exception("Failed to show WorkflowHub: %s", e)

    def show_all_tools(self):
        """Show all tools (legacy tab view)"""
        try:
            self._show_tabs_widget()
        except Exception:
            try:
                self.stacked_widget.setCurrentIndex(1)
            except Exception:
                pass
        try:
            self.label_current_workflow.setText(tr("mw_all_tools"))
        except Exception:
            pass
        try:
            self._show_status_message(tr("mw_all_tools_status"))
        except Exception:
            pass

    def _show_tabs_widget(self) -> None:
        try:
            if getattr(self, "tabs_widget", None) is not None:
                self.stacked_widget.setCurrentWidget(self.tabs_widget)
                return
        except Exception:
            pass

        try:
            idx = getattr(self, "_tabs_page_index", None)
            if isinstance(idx, int) and idx >= 0:
                self.stacked_widget.setCurrentIndex(idx)
            else:
                self.stacked_widget.setCurrentIndex(1)
        except Exception:
            pass

    def _get_workflow_map(self) -> dict[str, tuple[str, int | None]]:
        workflow_map = {
            "ocw_test": ("OCW Test", 5),
            "ladder_test": ("Ladder Test", 5),
            "seating_depth": (tr("mw_seating_depth_label"), 5),
            "smart_wizard": (tr("mw_load_assistant_label"), None),
            "temperature_test": ("Temperature Test", 5),
            "saami_compliance": ("SAAMI/CIP", 5),
            "chronograph_import": ("Chronograph", 5),
            "cold_bore": ("Cold Bore", 1),
            "batch_workspace": ("Batch-workspace", None),
            "batch_qc": ("Batch-workspace", None),
            "lot_tracker": ("Lot Tracking", 3),
            "drop_chart": ("Drop Chart", 2),
            "wind_drift": ("Wind Drift", 2),
            "zero_shift": ("Zero Shift", 2),
            "rifle_setup": ("Firearm Setup", 4),
            "component_database": ("Component Database", 3),
            "component_inventory": ("Component Inventory", 3),
            "primer_tools": ("Primer Tools", None),
            "load_wizard": (tr("mw_harmonics_lab_label"), None),
            # Komponenter
            "brass_manager": ("Brass Manager", None),
            "bullet_manager": ("Bullet Manager", None),
            "powder_manager": ("Powder Manager", None),
            "primer_manager": ("Primer Manager", None),
            # Rifles & Utstyr
            "rifle_optic_manager": ("Firearms & Optics", None),
            "ammo_profile_manager": ("Ammunition Profiles", 0),
            "rifle_performance": ("Firearm Performance", None),
            "harmonics_lab": (tr("mw_harmonics_lab_label"), None),
            # Testing & Analyse
            "precision_tracker": ("Precision Tracking", None),
            "target_analyzer": ("Target Analysis", None),
            # Tools
            "saami_checker": ("SAAMI/CIP Check", None),
            "safety_dashboard": ("Safety Dashboard", None),
            # Load Development Workflow
            "load_development_workflow": ("Batch-workspace", None),
            "load_workflow_manager": (tr("mw_harmonics_lab_label"), None),
        }
        for workflow_id in self._legacy_workflow_ids():
            if workflow_id in workflow_map:
                label, tab_idx = workflow_map[workflow_id]
                workflow_map[workflow_id] = (self._with_legacy_suffix(label), tab_idx)
        return workflow_map

    def _handle_load_development_workflow(self) -> None:
        try:
            manager = getattr(self, "mode_manager", None)
            if manager is not None and manager.is_beginner():
                self.show_batch_workspace()
            else:
                self.show_modern_load_builder()
        except Exception:
            self.show_batch_workspace()

    def _get_workflow_handlers(self) -> dict[str, Callable[[], None]]:
        return {
            "smart_wizard": self.launch_smart_wizard,
            "zero_shift": self.show_zero_shift_calculator,
            "primer_tools": self.show_primer_tools,
            "modern_load_builder": self.show_modern_load_builder,
            "batch_workspace": self.show_batch_workspace,
            "batch_qc": self.show_batch_workspace,
            "load_wizard": self.show_harmonics_lab,
            "load_development_workflow": self._handle_load_development_workflow,
            "load_workflow_manager": self.show_harmonics_lab,
            "brass_manager": self.show_brass_manager,
            "rifle_optic_manager": self.show_rifle_optic_manager,
            "ammo_profile_manager": self.show_ammo_profile_manager,
            "rifle_performance": self.show_rifle_performance,
            "harmonics_lab": self.show_harmonics_lab,
            "precision_tracker": self.show_precision_tracker,
            "target_analyzer": self.show_target_analyzer,
            "saami_checker": self.show_saami_checker,
            "safety_dashboard": self.show_safety_dashboard,
            "drop_chart": self.show_drop_chart,
        }

    def _format_active_setup_label(
        self,
        barrel_name: object | None,
        barrel_configuration_name: object | None,
    ) -> str:
        resolved_barrel_name = str(barrel_name or "").strip()
        resolved_configuration_name = str(barrel_configuration_name or "").strip()
        if (
            resolved_barrel_name
            and resolved_configuration_name
            and resolved_barrel_name.casefold()
            != resolved_configuration_name.casefold()
        ):
            return f"{resolved_barrel_name} / {resolved_configuration_name}"
        return resolved_configuration_name or resolved_barrel_name

    def _get_active_workflow_setup_label(self) -> str:
        try:
            from ..tools.load_session_runtime_service import (
                build_active_workflow_context_from_settings,
            )

            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            workflow_context = build_active_workflow_context_from_settings(
                settings,
                getattr(self, "db", None),
            )
            barrel_name = str(workflow_context.get("barrel_name") or "").strip()
            barrel_configuration_name = str(
                workflow_context.get("barrel_configuration_name") or ""
            ).strip()
            load_session_id = workflow_context.get("load_session_id")
        except Exception:
            return ""

        if (
            not barrel_name or not barrel_configuration_name
        ) and load_session_id not in (None, ""):
            db = getattr(self, "db", None)
            if db is not None:
                try:
                    session = db.get_by_id(
                        "load_development_sessions", int(load_session_id)
                    )
                except Exception:
                    session = None
                if session:
                    if not barrel_name:
                        barrel_name = str(session.get("barrel_name") or "").strip()
                    if not barrel_configuration_name:
                        barrel_configuration_name = str(
                            session.get("barrel_configuration_name") or ""
                        ).strip()

        return MainWindow._format_active_setup_label(
            self,
            barrel_name,
            barrel_configuration_name,
        )

    def _format_workflow_display_name(
        self,
        workflow_name: str,
        workflow_id: str | None = None,
    ) -> str:
        resolved_workflow_name = str(workflow_name or "").strip()
        if not resolved_workflow_name:
            return ""
        setup_scoped_workflows = {
            "load_development",
            "load_development_workflow",
            "modern_load_builder",
            "smart_wizard",
            "batch_workspace",
            "batch_qc",
            "target_analyzer",
            "chronograph_import",
            "ocw_test",
            "ladder_test",
            "seating_depth",
            "temperature_test",
            "harmonics_lab",
            "load_wizard",
        }
        if workflow_id and workflow_id not in setup_scoped_workflows:
            return resolved_workflow_name
        setup_label = self._get_active_workflow_setup_label()
        if not setup_label:
            return resolved_workflow_name
        return f"{resolved_workflow_name} ({setup_label})"

    def _apply_setup_context_to_message(
        self,
        message: object | None,
        setup_label: str | None,
    ) -> str:
        resolved_message = str(message or "").strip()
        resolved_setup_label = str(setup_label or "").strip()
        if not resolved_setup_label:
            return resolved_message
        if not resolved_message:
            return f"Setup {resolved_setup_label}."
        if resolved_message.lower().startswith("setup "):
            return resolved_message
        return f"Setup {resolved_setup_label}. {resolved_message}"

    def _activate_workflow_tab(
        self, workflow_id: str, workflow_name: str, tab_idx: int
    ) -> None:
        display_name = MainWindow._format_workflow_display_name(
            self, workflow_name, workflow_id
        )
        try:
            self._show_tabs_widget()
            self.tabs.setCurrentIndex(tab_idx)
            self.label_current_workflow.setText(
                tr(
                    "mw_active_workflow_label",
                    workflow_name=display_name or workflow_name,
                )
            )
            self._show_status_message(
                tr(
                    "mw_active_workflow_status",
                    workflow_name=display_name or workflow_name,
                )
            )
        except Exception:
            pass

        try:
            workflow_hub = getattr(self, "workflow_hub", None)
            if workflow_hub is not None and hasattr(
                workflow_hub, "mark_workflow_active"
            ):
                workflow_hub.mark_workflow_active(
                    workflow_id, display_name or workflow_name
                )
        except Exception:
            pass

    def launch_workflow(self, workflow_id: str):
        """Launch specific workflow"""
        workflow_map = self._get_workflow_map()
        if workflow_id not in workflow_map:
            self._show_status_message(
                tr("mw_workflow_not_implemented_yet", workflow_id=workflow_id)
            )
            return

        workflow_name, tab_idx = workflow_map[workflow_id]
        handler = self._get_workflow_handlers().get(workflow_id)
        if handler:
            handler()
            return

        if tab_idx is not None:
            self._activate_workflow_tab(workflow_id, workflow_name, tab_idx)
        else:
            self._show_status_message(
                tr("mw_workflow_coming_soon", workflow_name=workflow_name)
            )

    def launch_smart_wizard(self):
        """Launch the streamlined load assistant."""
        from ..modules.smart_loading_wizard import SmartLoadingWizard

        wizard = SmartLoadingWizard(self)
        if wizard.exec():
            self._show_status_message(tr("mw_load_assistant_completed"))
            workflow_hub = getattr(self, "workflow_hub", None)
            if workflow_hub is not None:
                workflow_hub.mark_workflow_completed("smart_wizard")
        else:
            self._show_status_message(tr("mw_load_assistant_cancelled"))

    def check_saved_workflows(self):
        """Check for saved workflows on startup"""
        # Guard against uninitialized state_manager during deferred startup
        if not hasattr(self, "state_manager") or self.state_manager is None:
            return

        state_manager = getattr(self, "state_manager", None)
        if state_manager is None:
            return

        active_states = state_manager.get_all_active()
        # If there are saved workflows, record that fact but do NOT auto-show
        # a separate modal at startup. Users can open the resume dialog from
        # the File menu (Resume Saved Workflows...) to avoid a transient
        # second top-level window.
        try:
            if active_states:
                self._saved_workflows_available = True
                self._saved_states_preview = active_states
                try:
                    self._show_status_message(
                        tr("mw_saved_workflows_available", count=len(active_states))
                    )
                except Exception:
                    pass
            else:
                self._saved_workflows_available = False
                self._saved_states_preview = []
        except Exception:
            self._saved_workflows_available = False
            self._saved_states_preview = []

    def _restore_resumed_rifle_profile_context(
        self, workflow_context: dict[str, object]
    ) -> None:
        db = getattr(self, "db", None)
        if db is None:
            return

        rifle_id = workflow_context.get("rifle_id")
        if rifle_id in (None, ""):
            return
        try:
            resolved_rifle_id = int(rifle_id)
        except Exception:
            return

        try:
            rows = db.execute_query(
                "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
                (resolved_rifle_id,),
            )
        except Exception:
            return
        if not rows or not rows[0].get("profile_json"):
            return

        try:
            details = json.loads(rows[0]["profile_json"])
        except Exception:
            return
        if not isinstance(details, dict):
            return

        changed = False
        barrel_id = str(workflow_context.get("barrel_id") or "").strip() or None
        configuration_id = (
            str(workflow_context.get("barrel_configuration_id") or "").strip() or None
        )
        configuration_name = (
            str(workflow_context.get("barrel_configuration_name") or "").strip() or None
        )

        if (
            barrel_id
            and str(details.get("active_barrel_id") or "").strip() != barrel_id
        ):
            details["active_barrel_id"] = barrel_id
            changed = True

        barrels = details.get("barrels")
        if barrel_id and isinstance(barrels, list):
            updated_barrels = []
            barrels_changed = False
            for barrel in barrels:
                if not isinstance(barrel, dict):
                    updated_barrels.append(barrel)
                    continue
                updated_barrel = dict(barrel)
                is_active = str(updated_barrel.get("id") or "").strip() == barrel_id
                if bool(updated_barrel.get("is_active")) != is_active:
                    updated_barrel["is_active"] = is_active
                    barrels_changed = True
                updated_barrels.append(updated_barrel)
            if barrels_changed:
                details["barrels"] = updated_barrels
                changed = True

        if configuration_id and (
            str(details.get("active_barrel_configuration_id") or "").strip()
            != configuration_id
        ):
            details["active_barrel_configuration_id"] = configuration_id
            changed = True
        if configuration_name and (
            str(details.get("active_barrel_configuration_name") or "").strip()
            != configuration_name
        ):
            details["active_barrel_configuration_name"] = configuration_name
            changed = True

        configurations = details.get("barrel_configurations")
        if configuration_id and isinstance(configurations, list):
            updated_configurations = []
            configurations_changed = False
            matched_configuration = False
            for configuration in configurations:
                if not isinstance(configuration, dict):
                    updated_configurations.append(configuration)
                    continue
                updated_configuration = dict(configuration)
                current_id = str(updated_configuration.get("id") or "").strip() or None
                is_selected = current_id == configuration_id
                if bool(updated_configuration.get("is_active")) != is_selected:
                    updated_configuration["is_active"] = is_selected
                    configurations_changed = True
                if is_selected:
                    matched_configuration = True
                    if (
                        barrel_id
                        and (
                            str(updated_configuration.get("barrel_id") or "").strip()
                            or None
                        )
                        != barrel_id
                    ):
                        updated_configuration["barrel_id"] = barrel_id
                        configurations_changed = True
                    if configuration_name and (
                        str(updated_configuration.get("name") or "").strip()
                        != configuration_name
                    ):
                        updated_configuration["name"] = configuration_name
                        configurations_changed = True
                updated_configurations.append(updated_configuration)
            if matched_configuration and configurations_changed:
                details["barrel_configurations"] = updated_configurations
                changed = True

        if not changed:
            return

        try:
            db.update(
                "rifle_profile_details",
                {"profile_json": json.dumps(details)},
                "rifle_id = ?",
                (resolved_rifle_id,),
            )
        except Exception:
            return

    def _restore_resumed_workflow_context(self, state) -> None:
        state_data = dict(getattr(state, "data", {}) or {})

        def _coerce_optional_int(value: object) -> int | object | None:
            if value in (None, ""):
                return None
            try:
                return int(value)
            except Exception:
                return value

        session = None
        load_session_id = _coerce_optional_int(state_data.get("load_session_id"))
        db = getattr(self, "db", None)
        if load_session_id not in (None, "") and db is not None:
            try:
                session = db.get_by_id(
                    "load_development_sessions", int(load_session_id)
                )
            except Exception:
                session = None

        context = {
            "workflow_id": state_data.get("workflow_id")
            or getattr(state, "workflow_id", None),
            "workflow_name": str(
                state_data.get("workflow_name")
                or getattr(state, "workflow_name", "")
                or ""
            ).strip(),
            "load_session_id": _coerce_optional_int(
                (session or {}).get("id")
                if isinstance(session, dict)
                else load_session_id
            ),
            "ammo_profile_id": _coerce_optional_int(
                (session or {}).get("ammo_profile_id")
                if isinstance(session, dict)
                and (session or {}).get("ammo_profile_id") not in (None, "")
                else state_data.get("ammo_profile_id")
            ),
            "rifle_id": _coerce_optional_int(
                (session or {}).get("rifle_id")
                if isinstance(session, dict)
                and (session or {}).get("rifle_id") not in (None, "")
                else state_data.get("rifle_id")
            ),
            "barrel_id": str(
                (session or {}).get("barrel_id")
                if isinstance(session, dict)
                and (session or {}).get("barrel_id") not in (None, "")
                else state_data.get("barrel_id") or ""
            ).strip(),
            "barrel_name": str(
                (session or {}).get("barrel_name")
                if isinstance(session, dict)
                and (session or {}).get("barrel_name") not in (None, "")
                else state_data.get("barrel_name") or ""
            ).strip(),
            "barrel_configuration_id": str(
                (session or {}).get("barrel_configuration_id")
                if isinstance(session, dict)
                and (session or {}).get("barrel_configuration_id") not in (None, "")
                else state_data.get("barrel_configuration_id") or ""
            ).strip()
            or None,
            "barrel_configuration_name": str(
                (session or {}).get("barrel_configuration_name")
                if isinstance(session, dict)
                and (session or {}).get("barrel_configuration_name") not in (None, "")
                else state_data.get("barrel_configuration_name") or ""
            ).strip(),
            "session_name": str(
                (session or {}).get("session_name")
                if isinstance(session, dict)
                and (session or {}).get("session_name") not in (None, "")
                else state_data.get("session_name") or ""
            ).strip(),
            "created_date": str(
                state_data.get("created_date")
                or (
                    (session or {}).get("created_date")
                    if isinstance(session, dict)
                    else ""
                )
                or ((session or {}).get("date") if isinstance(session, dict) else "")
                or ""
            ).strip(),
        }

        settings = QSettings("ReloadingWorkshop", "ReloadingManager")
        store_workflow_context_in_settings(settings, context, sync=True)

        MainWindow._restore_resumed_rifle_profile_context(self, context)

    def resume_workflow(self, workflow_id: str):
        """Resume a saved workflow"""
        state_manager = getattr(self, "state_manager", None)
        if state_manager is None:
            return
        state = state_manager.get_state(workflow_id)
        if not state:
            return

        try:
            MainWindow._restore_resumed_workflow_context(self, state)
        except Exception as e:
            logger.exception(
                "Failed to restore workflow context for %s: %s", workflow_id, e
            )

        # Try to launch the workflow and notify the user
        try:
            self.launch_workflow(workflow_id)
            self._show_status_message(
                tr("mw_resumed_workflow_status", workflow_name=state.workflow_name)
            )
            QMessageBox.information(
                self,
                tr("mw_workflow_resumed_title"),
                tr("mw_workflow_resumed_message", workflow_name=state.workflow_name),
            )
        except Exception as e:
            logger.exception("Failed to resume workflow %s: %s", workflow_id, e)
            QMessageBox.warning(
                self,
                tr("mw_resume_failed_title"),
                tr("mw_resume_failed_message"),
            )

    def open_resume_dialog(self):
        """User-invoked: open the resume dialog if saved workflows exist."""
        try:
            if not getattr(self, "_saved_workflows_available", False):
                QMessageBox.information(
                    self,
                    tr("mw_no_saved_workflows_title"),
                    tr("mw_no_saved_workflows_message"),
                )
                return
            from ..modules.workflow_resume_dialog import WorkflowResumeDialog

            state_manager = getattr(self, "state_manager", None)
            if state_manager is None:
                return
            dialog = WorkflowResumeDialog(state_manager, self)
            dialog.workflow_selected.connect(self.resume_workflow)
            _run_modal(dialog)
        except Exception as e:
            logger.exception("Failed to open resume dialog: %s", e)
            try:
                QMessageBox.warning(
                    self,
                    tr("msg_error"),
                    tr("mw_resume_dialog_open_failed"),
                )
            except Exception:
                pass

    def show_weapon_profile_editor(self):
        """Open the Weapon Profile Editor dialog (loads/saves JSON)."""
        try:
            from pathlib import Path

            from .weapon_profile_editor import WeaponProfileEditor

            dlg = self._instantiate_factory(
                WeaponProfileEditor,
                self,
                data_path=Path("data/demo_weapons.json"),
            )
            dlg.exec()
        except Exception as e:
            logger.exception("WeaponProfileEditor failed to open: %s", e)
            QMessageBox.warning(
                self,
                tr("mw_unavailable"),
                tr("mw_weapon_profile_editor_unavailable"),
            )

    def show_field_planning(self):
        """Open the Field Planning window (DOPE card, shooting range, hunting safety)."""
        try:
            from .field_planning_window import FieldPlanningWindow

            win = self._instantiate_factory(
                FieldPlanningWindow,
                self,
                db=getattr(self, "db", None),
            )

            # Pre-populate rifle list from DB if possible
            try:
                from ..utils.ballistics_profile_bridge import (
                    build_weapon_ballistic_profile,
                )

                db = getattr(self, "db", None)
                if db is not None:
                    rifles = (
                        db.execute_query("SELECT id FROM rifles ORDER BY name") or []
                    )
                    profiles = []
                    for r in rifles:
                        try:
                            rid = r["id"] if isinstance(r, dict) else r[0]
                            p = build_weapon_ballistic_profile(db, rid)
                            profiles.append(p)
                        except Exception:
                            pass
                    if profiles:
                        win.populate_rifles(profiles)
            except Exception:
                pass

            win.show()
            win.raise_()
        except Exception as e:
            logger.exception("FieldPlanningWindow failed to open: %s", e)
            QMessageBox.warning(
                self,
                tr("mw_unavailable"),
                "Field planning is not available: " + str(e),
            )

    def show_cdm_calibration(self):
        """Open the CDM BC calibration panel."""
        try:
            from .cdm_calibration_panel import CDMCalibrationPanel

            dlg = CDMCalibrationPanel(db=getattr(self, "db", None), parent=self)
            try:
                from ..utils.ballistics_profile_bridge import (
                    build_weapon_ballistic_profile,
                )

                rifles = (
                    self.db.execute_query("SELECT id FROM rifles ORDER BY name LIMIT 1")
                    or []
                )
                if rifles:
                    rid = (
                        rifles[0][0]
                        if not isinstance(rifles[0], dict)
                        else rifles[0]["id"]
                    )
                    p = build_weapon_ballistic_profile(self.db, rid)
                    dlg.set_profile(p)
            except Exception:
                pass
            dlg.show()
            dlg.raise_()
        except Exception as e:
            logger.exception("CDMCalibrationPanel failed: %s", e)
            QMessageBox.warning(self, tr("mw_unavailable"), str(e))

    def show_chronograph(self):
        """Open the Chronograph session registration dialog."""
        try:
            from .chronograph_widget import ChronographWidget

            dlg = ChronographWidget(db=getattr(self, "db", None), parent=self)
            # Try to find the currently selected rifle
            try:
                rifles = (getattr(self, "db", None) or None) and self.db.execute_query(
                    "SELECT id FROM rifles ORDER BY name LIMIT 1"
                )
                if rifles:
                    rid = (
                        rifles[0][0]
                        if not isinstance(rifles[0], dict)
                        else rifles[0]["id"]
                    )
                    dlg.set_rifle(rid)
            except Exception:
                pass
            dlg.show()
            dlg.raise_()
        except Exception as e:
            logger.exception("ChronographWidget failed: %s", e)
            QMessageBox.warning(self, tr("mw_unavailable"), str(e))

    def _get_mode_key(self) -> str:
        try:
            manager = getattr(self, "mode_manager", None)
            if manager is not None:
                if getattr(manager, "is_research", lambda: False)():
                    return "research"
                if manager.is_beginner():
                    return "beginner"
                return "expert"
        except Exception:
            pass
        try:
            val = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "ui/mode", "beginner"
            )
            return str(val).lower()
        except Exception:
            return "beginner"

    def _apply_ui_mode_to_nav(self) -> None:
        mode_key = self._get_mode_key()
        is_beginner = mode_key == "beginner"

        try:
            if hasattr(self, "btn_all_tools"):
                self.btn_all_tools.setVisible(not is_beginner)
        except Exception:
            pass

        try:
            if hasattr(self, "nav_panel"):
                self.nav_panel.setFixedWidth(240 if not is_beginner else 220)
        except Exception:
            pass

    def apply_ui_mode_from_settings(self) -> None:
        """Apply user mode from persisted settings to the mode manager."""
        if not getattr(self, "mode_manager", None):
            return
        try:
            val = QSettings("ReloadingWorkshop", "ReloadingManager").value(
                "ui/mode", "beginner"
            )
        except Exception:
            val = "beginner"

        try:
            um = getattr(self, "_UserMode", None)
            expert_val = getattr(um, "EXPERT", 1) if um else 1
            beginner_val = getattr(um, "BEGINNER", 0) if um else 0
            research_val = getattr(um, "RESEARCH", 2) if um else 2
            if str(val).lower() == "research":
                manager = getattr(self, "mode_manager", None)
                if manager is not None:
                    manager.set_mode(research_val)
            elif str(val).lower() == "expert":
                manager = getattr(self, "mode_manager", None)
                if manager is not None:
                    manager.set_mode(expert_val)
            else:
                manager = getattr(self, "mode_manager", None)
                if manager is not None:
                    manager.set_mode(beginner_val)
        except Exception:
            pass

        try:
            self._sync_mode_combo_from_settings()
        except Exception:
            pass

        try:
            self._apply_ui_mode_to_actions()
        except Exception:
            pass

        try:
            self._apply_ui_mode_to_nav()
        except Exception:
            pass

        try:
            workflow_hub = getattr(self, "workflow_hub", None)
            if workflow_hub is not None and hasattr(workflow_hub, "refresh_for_mode"):
                workflow_hub.refresh_for_mode()
        except Exception:
            pass

    def _apply_ui_mode_to_actions(self) -> None:
        is_beginner = True
        try:
            manager = getattr(self, "mode_manager", None)
            if manager is not None:
                is_beginner = manager.is_beginner()
        except Exception:
            is_beginner = True

        for act in getattr(self, "_advanced_actions", []) or []:
            try:
                act.setVisible(not is_beginner)
                act.setEnabled(not is_beginner)
                if is_beginner:
                    act.setToolTip(tr("mw_available_in_expert_mode"))
                else:
                    act.setToolTip("")
            except Exception:
                pass

        try:
            if hasattr(self, "inspector_panel"):
                self.inspector_panel.setVisible(not is_beginner)
        except Exception:
            pass

    def on_mode_changed(self, new_mode: str):
        """Handle user mode change"""
        _um = getattr(self, "_UserMode", None)
        if _um is None:
            beginner_val = 0
        else:
            beginner_val = getattr(_um, "BEGINNER", 0)
        research_val = getattr(_um, "RESEARCH", 2) if _um else 2

        if new_mode == beginner_val:
            mode_name = tr("mw_beginner")
        elif new_mode == research_val:
            mode_name = tr("mw_research")
        else:
            mode_name = tr("mw_advanced")

        self._show_status_message(tr("mw_mode_changed_to", mode_name=mode_name))

        try:
            self._apply_ui_mode_to_actions()
        except Exception:
            pass

        if getattr(self, "_startup_in_progress", False):
            try:
                self._apply_ui_mode_to_nav()
            except Exception:
                pass
            return

        # Show notification
        config = {}
        try:
            manager = getattr(self, "mode_manager", None)
            config = manager.get_ui_config() if manager is not None else {}
        except Exception:
            config = {"confirmation_dialogs": False}

        if config.get("confirmation_dialogs"):
            features = []
            if config.get("show_tooltips"):
                features.append(tr("mw_tooltips_enabled"))
            else:
                features.append(tr("mw_tooltips_disabled"))

            if config.get("enable_shortcuts"):
                features.append(tr("mw_keyboard_shortcuts_enabled"))
            else:
                features.append(tr("mw_keyboard_shortcuts_disabled"))

            if config.get("wizard_mode"):
                features.append(tr("mw_wizard_mode_enabled"))
            else:
                features.append(tr("mw_wizard_mode_disabled"))

            QMessageBox.information(
                self,
                tr("mw_mode_changed_title"),
                tr("mw_user_mode_changed_to", mode_name=mode_name)
                + "\n\n"
                + "\n".join(features),
            )

        try:
            workflow_hub = getattr(self, "workflow_hub", None)
            if workflow_hub is not None and hasattr(workflow_hub, "refresh_for_mode"):
                workflow_hub.refresh_for_mode()
        except Exception:
            pass

    def show_primer_tools(self):
        """Show primer tools dialog"""
        from ..modules.primer_tools import PrimerToolsHub

        dialog = self._construct_widget(PrimerToolsHub, self)
        dialog.setWindowTitle(tr("mw_primer_tools_title"))
        dialog.resize(1000, 600)
        dialog.show()

    def show_component_database(
        self, component_type: str | None = None, component_id: int | None = None
    ):
        """Show component database and optionally focus a specific component."""
        dialog = QWidget(self)
        dialog.setWindowTitle(tr("component_db_title"))
        dialog.resize(1300, 860)
        layout = QVBoxLayout()
        try:
            from ..layers import component_layer

            manager = self._construct_widget(
                component_layer.db.ComponentDatabaseManager, self, self.db
            )
            layout.addWidget(manager)
            if component_type and component_id:
                try:
                    manager.focus_component(component_type, int(component_id))
                except Exception:
                    pass
        except Exception as e:
            logger.exception("ComponentDatabaseManager import failed: %s", e)
            layout.addWidget(QLabel(tr("component_db_unavailable"), dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self._show_status_message(tr("component_db_status_active"))

    def show_load_wizard(self):
        """Backward-compatible alias for the new harmonics/load workflow."""
        return self.show_harmonics_lab()

    def show_brass_manager(self):
        """Show brass/case lifecycle manager"""
        dialog = QWidget(self)
        dialog.setWindowTitle(tr("mw_brass_manager_title"))
        dialog.resize(1400, 900)
        layout = QVBoxLayout()
        try:
            from ..layers import component_layer

            manager = self._construct_widget(component_layer.brass.BrassManager, self)
            layout.addWidget(manager)
        except Exception as e:
            logger.exception("BrassManager import failed: %s", e)
            layout.addWidget(QLabel(tr("mw_brass_manager_unavailable")))
        dialog.setLayout(layout)

        # Add to workspace area
        self.workspace_area.addWidget(dialog)
        self.workspace_area.setCurrentWidget(dialog)

        # Update workflow state
        workflow_hub = getattr(self, "workflow_hub", None)
        if workflow_hub is not None:
            try:
                workflow_hub.mark_workflow_active(
                    "brass_manager", tr("mw_brass_manager_title")
                )
            except Exception:
                pass
        self._show_status_message(tr("mw_brass_lifecycle_activated"))

    def show_rifle_optic_manager(self):
        """Show rifles and optics manager"""
        dialog = QWidget(self)
        dialog.setWindowTitle(tr("mw_rifle_optics_manager_title"))
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from ..modules.rifle_optic_manager import RifleOpticManager

            manager = self._construct_widget(RifleOpticManager, self)
            layout.addWidget(manager)
        except Exception as e:
            logger.exception("RifleOpticManager import failed: %s", e)
            layout.addWidget(QLabel(tr("mw_rifle_optic_manager_unavailable"), dialog))
        dialog.setLayout(layout)
        # Add to workspace area instead of showing as a separate top-level window
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self._show_status_message(tr("mw_rifle_optics_manager_status"))

    def show_ammo_profile_manager(self):
        """Show ammo profiles manager"""
        dialog = QWidget(self)
        dialog.setWindowTitle(tr("mw_ammo_profiles_title"))
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from ..modules.ammo_profile_manager import AmmoProfileManager

            manager = self._construct_widget(AmmoProfileManager, self)
            layout.addWidget(manager)
        except Exception as e:
            logger.exception("AmmoProfileManager import failed: %s", e)
            layout.addWidget(QLabel(tr("mw_ammo_profile_manager_unavailable"), dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self._show_status_message(tr("mw_ammo_profile_manager_status"))

    def show_rifle_performance(self):
        """Show rifle performance tracker"""
        dialog = QWidget(self)
        dialog.setWindowTitle(tr("mw_rifle_performance_title"))
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from ..modules.rifle_performance_tracker import RiflePerformanceTracker

            tracker = self._construct_widget(RiflePerformanceTracker, self)
            layout.addWidget(tracker)
        except Exception as e:
            logger.exception("RiflePerformanceTracker import failed: %s", e)
            layout.addWidget(QLabel(tr("mw_rifle_performance_unavailable"), dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self._show_status_message(tr("mw_rifle_performance_status"))

    def show_ballistics_simulator(self):
        """Show real-time ballistics simulator"""
        from ..modules.ballistics_simulator import BallisticsSimulator

        dialog = QWidget(self)
        dialog.setWindowTitle(tr("mw_ballistics_simulator_title"))
        dialog.resize(1600, 1000)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        simulator = self._construct_widget(BallisticsSimulator, self)
        layout.addWidget(simulator)

        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self._show_status_message(tr("mw_ballistics_simulator_status"))

    def show_precision_tracker(self):
        """Show precision tracker"""
        dialog = QWidget(self)
        dialog.setWindowTitle(tr("mw_precision_tracker_title"))
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from ..modules.precision_tracker import PrecisionTracker

            tracker = self._construct_widget(PrecisionTracker, self)
            layout.addWidget(tracker)
        except Exception as e:
            logger.exception("PrecisionTracker import failed: %s", e)
            layout.addWidget(QLabel(tr("mw_precision_tracker_unavailable"), dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self._show_status_message(tr("mw_precision_tracker_status"))

    def show_target_analyzer(self):
        """Show target analyzer"""
        dialog = QWidget(self)
        dialog.setWindowTitle(tr("mw_target_analyzer_title"))
        dialog.resize(1200, 800)
        layout = QVBoxLayout()
        try:
            from ..modules.target_analyzer import TargetAnalyzer

            analyzer = self._construct_widget(TargetAnalyzer, self)
            layout.addWidget(analyzer)
        except Exception as e:
            logger.exception("TargetAnalyzer import failed: %s", e)
            layout.addWidget(QLabel(tr("mw_target_analyzer_unavailable"), dialog))
        dialog.setLayout(layout)
        try:
            self.workspace_area.addWidget(dialog)
            self.workspace_area.setCurrentWidget(dialog)
        except Exception:
            dialog.show()
        self._show_status_message(tr("mw_target_analyzer_status"))

    def show_ammo_test_lab(self):
        """Show the ammo test module (lot registration, sessions, LOT comparison, weapon matrix)."""
        try:
            from .ammo_test_window import AmmoTestWindow

            rifles = []
            try:
                rifles = self.db.get_all("rifles") or []
            except Exception:
                pass
            widget = AmmoTestWindow(db=self.db, rifles=rifles, parent=self)
            try:
                self.workspace_area.addWidget(widget)
                self.workspace_area.setCurrentWidget(widget)
            except Exception:
                widget.setWindowTitle("Ammo Test")
                widget.resize(1100, 820)
                widget.show()
        except Exception as e:
            logger.exception("AmmoTestWindow import failed: %s", e)
        self._show_status_message(tr("mw_ammo_test_lab_status"))

    def show_load_development_workflow(self):
        """Backward-compatible alias for the Batch Workspace."""
        return self.show_batch_workspace()

    def show_modern_load_builder(self):
        """Show modern interactive load builder with AI"""
        logger.info("NEW LOAD (Tactical) button clicked!")
        try:
            logger.info("Importing ModernLoadBuilder...")

            from ..modules.modern_load_builder import ModernLoadBuilder

            logger.info("Import successful, creating dialog...")
            self._show_status_message(tr("mw_loading_tactical_load_builder"))

            dialog = QDialog(self)
            dialog.setWindowTitle(tr("mw_tactical_load_builder_title"))
            dialog.setWindowIcon(self.windowIcon())
            dialog.resize(1600, 1000)
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)

            logger.info("Creating ModernLoadBuilder widget...")
            builder = self._construct_widget(ModernLoadBuilder, self)
            try:
                builder.batch_created.connect(
                    lambda batch_id: setattr(
                        self, "_pending_batch_workspace_id", batch_id
                    )
                )
            except Exception:
                pass
            layout.addWidget(builder)

            dialog.setLayout(layout)
            logger.info("Opening dialog...")
            self._show_status_message(tr("mw_tactical_load_builder_ready"))
            self._pending_batch_workspace_id = None
            dialog.exec()
            pending_batch_id = getattr(self, "_pending_batch_workspace_id", None)
            if pending_batch_id:
                try:
                    self._pending_batch_workspace_id = None
                except Exception:
                    pass
                self.show_batch_workspace(batch_id=int(pending_batch_id))
            logger.info("Dialog closed successfully")

        except Exception as e:
            error_msg = tr("mw_failed_to_open_modern_load_builder", error=e)
            logger.exception("%s", error_msg)
            QMessageBox.critical(self, tr("msg_error"), error_msg)
            import traceback

            logger.debug(traceback.format_exc())
            self._show_status_message(tr("mw_error_status", error=e))

    def show_batch_workspace(self, batch_id: int | None = None):
        """Show the new batch-centric workspace."""
        try:
            from ..modules.batch_workspace import BatchWorkspace

            self._show_status_message(tr("mw_loading_batch_workspace"))

            dialog = QDialog(self)
            dialog.setWindowTitle(tr("mw_batch_workspace_title"))
            dialog.setWindowIcon(self.windowIcon())
            dialog.resize(1600, 980)
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)

            workspace = self._construct_widget(BatchWorkspace, self, batch_id=batch_id)
            layout.addWidget(workspace)
            dialog.setLayout(layout)
            dialog.exec()
            self._show_status_message(tr("mw_batch_workspace_closed"))
        except Exception as e:
            error_msg = tr("mw_failed_to_open_batch_workspace", error=e)
            logger.exception("%s", error_msg)
            QMessageBox.critical(self, tr("msg_error"), error_msg)
            import traceback

            logger.debug(traceback.format_exc())
            self._show_status_message(tr("mw_error_status", error=e))

    def show_harmonics_lab(self):
        """Show the harmonics-focused load development workspace."""
        self._show_status_message(tr("mw_opening_harmonics_lab"))
        self.show_modern_load_builder()

    def show_saami_checker(self):
        """Show SAAMI/CIP compliance checker"""
        try:
            from ..modules.saami_compliance_checker import SAAMIComplianceChecker

            dialog = QWidget(self)
            dialog.setWindowTitle(tr("mw_saami_checker_title"))
            dialog.resize(900, 700)
            layout = QVBoxLayout()
            checker = self._construct_widget(SAAMIComplianceChecker, self)
            layout.addWidget(checker)
            dialog.setLayout(layout)
            try:
                self.workspace_area.addWidget(dialog)
                self.workspace_area.setCurrentWidget(dialog)
            except Exception:
                dialog.show()
            self._show_status_message(tr("mw_saami_checker_status"))
        except Exception as e:
            logger.exception("SAAMIComplianceChecker import failed: %s", e)
            QMessageBox.warning(
                self,
                tr("mw_unavailable"),
                tr("mw_saami_checker_unavailable"),
            )

    def show_reference_integration(self):
        """Show reference and measurement integration."""
        self._show_status_message(
            "Tidligere referanseintegrasjon er arkivert utenfor produktet."
        )
        QMessageBox.information(
            self,
            tr("mw_unavailable"),
            "Tidligere referanseintegrasjon er arkivert og er ikke lenger en del av programmet.",
        )

    def show_grt_integration(self):
        """Bakoverkompatibel alias for eldre kallesteder."""
        self.show_reference_integration()

    def show_safety_dashboard(self):
        """Show safety dashboard"""
        try:
            from ..modules.safety_dashboard import SafetyDashboard

            dialog = QWidget(self)
            dialog.setWindowTitle(tr("mw_safety_dashboard_title"))
            dialog.resize(1200, 800)
            layout = QVBoxLayout()
            dashboard = self._construct_widget(SafetyDashboard, self)
            layout.addWidget(dashboard)
            dialog.setLayout(layout)
            try:
                self.workspace_area.addWidget(dialog)
                self.workspace_area.setCurrentWidget(dialog)
            except Exception:
                dialog.show()
            self._show_status_message(tr("mw_safety_dashboard_status"))
        except Exception as e:
            logger.exception("SafetyDashboard import failed: %s", e)
            QMessageBox.warning(
                self,
                tr("mw_unavailable"),
                tr("mw_safety_dashboard_unavailable_with_log"),
            )

    def show_drop_chart(self):
        """Show drop chart / dope card generator"""
        try:
            from ..modules.drop_chart_generator import DropChartGenerator

            dialog = QWidget(self)
            dialog.setWindowTitle(tr("mw_dope_card_generator_title"))
            dialog.resize(1000, 700)
            layout = QVBoxLayout()
            generator = self._construct_widget(DropChartGenerator, self)
            layout.addWidget(generator)
            dialog.setLayout(layout)
            try:
                self.workspace_area.addWidget(dialog)
                self.workspace_area.setCurrentWidget(dialog)
            except Exception:
                dialog.show()
            self._show_status_message(tr("mw_dope_card_generator_status"))
        except Exception as e:
            logger.exception("DropChartGenerator import failed: %s", e)
            QMessageBox.warning(
                self,
                tr("mw_unavailable"),
                tr("mw_dope_card_generator_unavailable"),
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
            qp = os.environ.get("QT_QPA_PLATFORM", "").lower()
            if qp in ("offscreen", "minimal"):
                headless_flag = True
        except Exception:
            pass

        # Explicit HEADLESS env flag should force non-modal behavior
        try:
            if os.environ.get("HEADLESS", "").lower() in ("1", "true"):
                headless_flag = True
        except Exception:
            pass

        try:
            try:
                pname = QGuiApplication.platformName().lower()
                if pname in ("offscreen", "minimal"):
                    headless_flag = True
            except Exception:
                pass
        except Exception:
            pass

        if headless_flag:
            db = getattr(self, "db", None)
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass
            event.accept()
            return

        confirm_exit = True
        try:
            manager = getattr(self, "mode_manager", None)
            if manager and hasattr(manager, "get_ui_config"):
                config = manager.get_ui_config() or {}
                if not config.get("confirmation_dialogs", True):
                    confirm_exit = False
        except Exception:
            confirm_exit = True

        if not confirm_exit:
            db = getattr(self, "db", None)
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            tr("msg_confirm_exit"),
            tr("msg_exit_question"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Lukk database
            db = getattr(self, "db", None)
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass
            event.accept()
        else:
            event.ignore()
