# NOTE: removed top-level mypy file-ignore to allow targeted checks

import importlib
import importlib.util
import os
import sys
import traceback
from pathlib import Path

# Ensure Qt DLL search path includes PyQt6's bundled Qt6/bin when running
# the app directly from source. This prevents "DLL load failed while importing
# QtCore" errors on Windows when the Qt6 DLLs are not on PATH.
try:
    spec = importlib.util.find_spec("PyQt6")
    if spec and spec.origin:
        pyqt_pkg_dir = Path(spec.origin).resolve().parent
        qt_bin = pyqt_pkg_dir / "Qt6" / "bin"
        if qt_bin.exists():
            # Python 3.8+: add directory to DLL search path
            try:
                os.add_dll_directory(str(qt_bin))
            except Exception:
                # Fallback: prepend to PATH (best-effort)
                os.environ["PATH"] = (
                    str(qt_bin) + os.pathsep + os.environ.get("PATH", "")
                )
except Exception:
    pass
from pathlib import Path

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

# Ensure project root is on sys.path so absolute imports work
try:
    proj_root = Path(__file__).resolve().parents[1]
    proj_root_str = str(proj_root)
    if proj_root_str not in sys.path:
        sys.path.insert(0, proj_root_str)
except Exception as _suppressed_exc:
    pass


def get_log_dir() -> str:
    """Return a per-user log directory path (best-effort).

    This helper is safe to call from exception handlers where other
    utilities may not be available.
    """
    try:
        local_appdata = os.environ.get("LOCALAPPDATA") or os.path.join(
            str(Path.home()), "AppData", "Local"
        )
        log_dir = os.path.join(local_appdata, "Hjemmelading", "logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            pass
        return log_dir
    except Exception:
        return os.getcwd()


# AppMainWindow will be resolved after the local MainWindow class is defined.

# Import safe logger (provide lightweight fallbacks)
try:
    from HjemmeladingApp.utils.safe_logger import append_exception, append_message
except Exception as _suppressed_exc:

    def append_exception(msg, exc=None):
        return None

    def append_message(msg):
        return None


def _global_excepthook(exc_type, exc_value, exc_tb):
    try:
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            append_exception("Uncaught exception (HjemmeladingApp): " + tb, exc_value)
        except Exception as _suppressed_exc:
            pass
        try:
            with open("hjemmeladingapp_error.log", "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception as _suppressed_exc:
            pass
    except Exception as _suppressed_exc:
        pass


try:
    sys.excepthook = _global_excepthook
except Exception as _suppressed_exc:
    pass


class _FallbackMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HjemmeladingApp - Moderne og fleksibel")
        self.setMinimumSize(1000, 700)

        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # Profil-meny
        profile_menu = QMenu("Profil", self)
        menubar.addMenu(profile_menu)
        profile_action = QAction("Rediger profil og innstillinger", self)
        profile_action.triggered.connect(self.open_profile_editor)
        profile_menu.addAction(profile_action)

        # Innstillinger-meny
        settings_menu = QMenu("Innstillinger", self)
        menubar.addMenu(settings_menu)
        # Legg til rask tilgang for å åpne innstillinger
        settings_action = QAction("Åpne innstillinger", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(settings_action)

        # Språk-meny
        language_menu = QMenu("Språk", self)
        settings_menu.addMenu(language_menu)
        for lang in ["Norsk", "Engelsk", "Tysk"]:
            lang_action = QAction(lang, self)
            # capture default arg to avoid late-binding
            lang_action.triggered.connect(
                lambda checked, lang_choice=lang: self.set_language(lang_choice)
            )
            language_menu.addAction(lang_action)

        # Simple central area with welcome message
        central = QWidget()
        layout = QVBoxLayout()
        label = QLabel(
            "Velkommen! Dette er et moderne, fleksibelt program.\n"
            "Her kan du tilpasse utseende, tema og bakgrunn."
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def open_profile_editor(self):
        try:
            from HjemmeladingApp.ui.profile_editor import ProfileEditor

            try:
                self.profile_editor = ProfileEditor(self)
                self.profile_editor.show()
            except Exception as e:
                try:
                    append_exception("ProfileEditor creation failed: " + str(e), e)
                except Exception as _suppressed_exc:
                    pass
                QMessageBox.warning(
                    self,
                    "Feil",
                    "Kunne ikke åpne profilredigerer (feil ved opprettelse).",
                )
        except Exception as _suppressed_exc:
            QMessageBox.warning(
                self, "Feil", "Kunne ikke åpne profilredigerer (mangler modul)."
            )

    def set_language(self, lang):
        QMessageBox.information(self, "Språkvalg", f"Språk satt til: {lang}")

    def open_settings_dialog(self):
        try:
            append_message("User invoked Open Settings")
        except Exception as _suppressed_exc:
            pass
        try:
            from HjemmeladingApp.ui.settings_dialog import SettingsDialog

            try:
                self._settings_dialog = SettingsDialog(self)
            except Exception as e:
                try:
                    append_exception("SettingsDialog creation failed: " + str(e), e)
                except Exception as _suppressed_exc:
                    pass
                QMessageBox.warning(
                    self, "Feil", f"Kunne ikke opprette innstillingsdialog: {e}"
                )
                return

            try:
                if hasattr(self._settings_dialog, "exec"):
                    self._settings_dialog.exec()
                elif hasattr(self._settings_dialog, "exec_"):
                    self._settings_dialog.exec_()
                else:
                    self._settings_dialog.show()
            except Exception as e:
                try:
                    import traceback as _tb

                    append_exception(
                        "SettingsDialog.exec/show failed: " + _tb.format_exc(), e
                    )
                except Exception as _suppressed_exc:
                    pass
                try:
                    self._settings_dialog.show()
                except Exception as _suppressed_exc:
                    pass
        except Exception as e:
            try:
                import datetime
                import traceback as _tb

                append_exception(
                    f"\n--- {datetime.datetime.utcnow().isoformat()}Z ---\n"
                    + _tb.format_exc(),
                    e,
                )
            except Exception as _suppressed_exc:
                pass
            try:
                QMessageBox.warning(
                    self,
                    "Feil",
                    f"Kunne ikke åpne innstillinger: {e}\nSe per-user logg for detaljer.",
                )
            except Exception as _suppressed_exc:
                pass


# Determine application main window implementation.
# Try several common import paths so the frozen layout doesn't prevent
# resolving the richer `MainWindow` implementation provided under `src.ui`.
# Prefer distributed `ui` package (commonly used by PyInstaller collections),
# then fall back to the repository `src` layout and finally a local `main_window`.
AppMainWindow = _FallbackMainWindow
try:
    # Install lightweight instrumentation to detect which modules create
    # QWidget instances without a parent at import/startup. This helps find
    # modules that instantiate UI at import-time and leave top-level widgets.
    import traceback
    from pathlib import Path

    from PyQt6.QtWidgets import QWidget

    _orig_qwidget_init = QWidget.__init__
    # During early startup we may want to force newly-created widgets
    # with no parent to attach to the main window. This global will be
    # set to the main window instance later in `main()` and cleared
    # after a short grace period.
    _FORCE_PARENT_TO = None

    def _instrumented_qwidget_init(self, *args, **kwargs):
        try:
            _orig_qwidget_init(self, *args, **kwargs)
        except Exception:
            # still attempt to continue; don't break application startup
            try:
                _orig_qwidget_init(self, *args, **kwargs)
            except Exception:
                return
        try:
            # If widget has no parent, record caller info so we can trace module-level UI
            if getattr(self, "parent", lambda: None)() is None:
                try:
                    stack = traceback.extract_stack()
                    # last meaningful frame before QWidget init
                    caller = stack[-3] if len(stack) >= 3 else stack[0]
                except Exception:
                    caller = None
                # Primary per-user log (best-effort)
                try:
                    trace_file = Path(get_log_dir()) / "widget_creation_trace.log"
                    with open(trace_file, "a", encoding="utf-8") as _wf:
                        _wf.write(
                            f"widget-created: {type(self).__name__} - {getattr(caller,'filename', '<unknown>')}:{getattr(caller,'name', '<unknown>')}:{getattr(caller,'lineno', 0)}\n"
                        )
                except Exception:
                    pass
                # Also write a verbose trace into workspace-accessible logs for easier inspection during development
                try:
                    ws_base = Path(__file__).resolve().parents[1]
                    dev_trace = (
                        ws_base / "tools" / "logs" / "widget_creation_trace_source.log"
                    )
                    try:
                        dev_trace.parent.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        pass
                    with open(dev_trace, "a", encoding="utf-8") as _wf2:
                        _wf2.write("--- WIDGET CREATED ---\n")
                        _wf2.write(f"type: {type(self).__name__}\n")
                        if caller is not None:
                            _wf2.write(
                                f"caller: {caller.filename}:{caller.name}:{caller.lineno}\n"
                            )
                        try:
                            _wf2.write("stack:\n")
                            import traceback as _tb

                            _wf2.write(_tb.format_stack())
                        except Exception:
                            pass
                        # If a force-parent anchor is set, attach this widget to it
                        try:
                            exempt = {"QMainWindow"}
                            if (
                                _FORCE_PARENT_TO is not None
                                and type(self).__name__ not in exempt
                            ):
                                try:
                                    self.setParent(_FORCE_PARENT_TO)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    try:
        QWidget.__init__ = _instrumented_qwidget_init
    except Exception:
        pass
    # Also instrument common leaf widget constructors to ensure they
    # default to the forced parent during early startup. This helps
    # catch modules that call QLabel/QPushButton/QMenu directly
    # without providing a parent.
    try:
        from PyQt6.QtWidgets import (
            QFrame,
            QGroupBox,
            QLabel,
            QMenu,
            QPushButton,
            QRadioButton,
            QScrollArea,
            QTabWidget,
        )

        _orig_qlabel_init = QLabel.__init__

        def _instrumented_qlabel_init(self, *args, **kwargs):
            try:
                # If no explicit parent provided, and a force-parent anchor
                # exists, set it as the parent to avoid transient top-levels.
                parent_provided = False
                if "parent" in kwargs:
                    parent_provided = True
                else:
                    try:
                        parent_provided = any(isinstance(a, QWidget) for a in args)
                    except Exception:
                        parent_provided = False
                if (
                    not parent_provided
                    and globals().get("_FORCE_PARENT_TO") is not None
                ):
                    kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
            except Exception:
                pass
            return _orig_qlabel_init(self, *args, **kwargs)

        try:
            QLabel.__init__ = _instrumented_qlabel_init
        except Exception:
            pass
        # Also ensure QMessageBox instances default to the forced parent
        try:
            from PyQt6.QtWidgets import QMessageBox

            _orig_qmsg_init = QMessageBox.__init__

            def _instrumented_qmsg_init(self, *args, **kwargs):
                try:
                    parent_provided = False
                    if "parent" in kwargs:
                        parent_provided = True
                    else:
                        try:
                            parent_provided = any(isinstance(a, QWidget) for a in args)
                        except Exception:
                            parent_provided = False
                    if (
                        not parent_provided
                        and globals().get("_FORCE_PARENT_TO") is not None
                    ):
                        kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
                except Exception:
                    pass
                return _orig_qmsg_init(self, *args, **kwargs)

            try:
                QMessageBox.__init__ = _instrumented_qmsg_init
            except Exception:
                pass
        except Exception:
            pass

        _orig_qpush_init = QPushButton.__init__

        def _instrumented_qpush_init(self, *args, **kwargs):
            try:
                parent_provided = False
                if "parent" in kwargs:
                    parent_provided = True
                else:
                    try:
                        parent_provided = any(isinstance(a, QWidget) for a in args)
                    except Exception:
                        parent_provided = False
                if (
                    not parent_provided
                    and globals().get("_FORCE_PARENT_TO") is not None
                ):
                    kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
            except Exception:
                pass
            return _orig_qpush_init(self, *args, **kwargs)

        try:
            QPushButton.__init__ = _instrumented_qpush_init
        except Exception:
            pass
        # Instrument QMenu
        try:
            _orig_qmenu_init = QMenu.__init__

            def _instrumented_qmenu_init(self, *args, **kwargs):
                try:
                    parent_provided = False
                    if "parent" in kwargs:
                        parent_provided = True
                    else:
                        try:
                            parent_provided = any(isinstance(a, QWidget) for a in args)
                        except Exception:
                            parent_provided = False
                    if (
                        not parent_provided
                        and globals().get("_FORCE_PARENT_TO") is not None
                    ):
                        kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
                except Exception:
                    pass
                return _orig_qmenu_init(self, *args, **kwargs)

            try:
                QMenu.__init__ = _instrumented_qmenu_init
            except Exception:
                pass
        except Exception:
            pass

        # Instrument additional common widgets
        try:
            _orig_qgroup_init = QGroupBox.__init__

            def _instrumented_qgroup_init(self, *args, **kwargs):
                try:
                    parent_provided = False
                    if "parent" in kwargs:
                        parent_provided = True
                    else:
                        try:
                            parent_provided = any(isinstance(a, QWidget) for a in args)
                        except Exception:
                            parent_provided = False
                    if (
                        not parent_provided
                        and globals().get("_FORCE_PARENT_TO") is not None
                    ):
                        kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
                except Exception:
                    pass
                return _orig_qgroup_init(self, *args, **kwargs)

            try:
                QGroupBox.__init__ = _instrumented_qgroup_init
            except Exception:
                pass
        except Exception:
            pass

        try:
            _orig_qradio_init = QRadioButton.__init__

            def _instrumented_qradio_init(self, *args, **kwargs):
                try:
                    parent_provided = False
                    if "parent" in kwargs:
                        parent_provided = True
                    else:
                        try:
                            parent_provided = any(isinstance(a, QWidget) for a in args)
                        except Exception:
                            parent_provided = False
                    if (
                        not parent_provided
                        and globals().get("_FORCE_PARENT_TO") is not None
                    ):
                        kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
                except Exception:
                    pass
                return _orig_qradio_init(self, *args, **kwargs)

            try:
                QRadioButton.__init__ = _instrumented_qradio_init
            except Exception:
                pass
        except Exception:
            pass

        try:
            _orig_qtab_init = QTabWidget.__init__

            def _instrumented_qtab_init(self, *args, **kwargs):
                try:
                    parent_provided = False
                    if "parent" in kwargs:
                        parent_provided = True
                    else:
                        try:
                            parent_provided = any(isinstance(a, QWidget) for a in args)
                        except Exception:
                            parent_provided = False
                    if (
                        not parent_provided
                        and globals().get("_FORCE_PARENT_TO") is not None
                    ):
                        kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
                except Exception:
                    pass
                return _orig_qtab_init(self, *args, **kwargs)

            try:
                QTabWidget.__init__ = _instrumented_qtab_init
            except Exception:
                pass
        except Exception:
            pass

        try:
            _orig_qframe_init = QFrame.__init__

            def _instrumented_qframe_init(self, *args, **kwargs):
                try:
                    parent_provided = False
                    if "parent" in kwargs:
                        parent_provided = True
                    else:
                        try:
                            parent_provided = any(isinstance(a, QWidget) for a in args)
                        except Exception:
                            parent_provided = False
                    if (
                        not parent_provided
                        and globals().get("_FORCE_PARENT_TO") is not None
                    ):
                        kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
                except Exception:
                    pass
                return _orig_qframe_init(self, *args, **kwargs)

            try:
                QFrame.__init__ = _instrumented_qframe_init
            except Exception:
                pass
        except Exception:
            pass

        try:
            _orig_qscroll_init = QScrollArea.__init__

            def _instrumented_qscroll_init(self, *args, **kwargs):
                try:
                    parent_provided = False
                    if "parent" in kwargs:
                        parent_provided = True
                    else:
                        try:
                            parent_provided = any(isinstance(a, QWidget) for a in args)
                        except Exception:
                            parent_provided = False
                    if (
                        not parent_provided
                        and globals().get("_FORCE_PARENT_TO") is not None
                    ):
                        kwargs.setdefault("parent", globals().get("_FORCE_PARENT_TO"))
                except Exception:
                    pass
                return _orig_qscroll_init(self, *args, **kwargs)

            try:
                QScrollArea.__init__ = _instrumented_qscroll_init
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        pass
except Exception:
    pass
# Defer importing the richer `MainWindow` implementation until runtime
# inside `main()` so instrumentation (force-parent/guarded-show) can be
# established before any module-level widget constructors run. This
# prevents modules imported by `src.ui.main_window` from creating
# top-level widgets before the app and main window exist.


def main():
    global _FORCE_PARENT_TO
    try:
        try:
            QCoreApplication.setAttribute(
                Qt.ApplicationAttribute.AA_ShareOpenGLContexts
            )
        except Exception as _suppressed_exc:
            pass
        app = QApplication(sys.argv)
        # Diagnostic trace: record number of top-level widgets before creating window
        try:
            from pathlib import Path as _P

            trace_file = _P(get_log_dir()) / "startup_trace.log"
            with open(trace_file, "a", encoding="utf-8") as _tf:
                _tf.write(
                    f"startup: pre-window topLevelWidgets={len(app.topLevelWidgets())}\n"
                )
        except Exception:
            pass
        try:
            try:
                from HjemmeladingApp.utils.fonts import register_bundled_fonts
            except Exception as _suppressed_exc:
                register_bundled_fonts = None
            if register_bundled_fonts:
                try:
                    n = register_bundled_fonts()
                    try:
                        append_message(f"Registered {n} bundled fonts at startup")
                    except Exception as _suppressed_exc:
                        pass
                except Exception as _suppressed_exc:
                    pass
        except Exception as _suppressed_exc:
            pass
        # Create a temporary hidden anchor widget to act as the forced
        # parent for any widgets created very early during imports. This
        # prevents accidental top-level windows appearing before the
        # real main window exists. The anchor will be reparented/cleared
        # after the real window is created.
        try:
            from PyQt6.QtWidgets import QWidget

            _temp_startup_anchor = QWidget()
            try:
                _temp_startup_anchor.setObjectName("_startup_anchor")
                _temp_startup_anchor.hide()
            except Exception:
                pass
            try:
                _FORCE_PARENT_TO = _temp_startup_anchor
            except Exception:
                pass
        except Exception:
            _temp_startup_anchor = None

        # Resolve the richer MainWindow implementation now that the
        # QApplication exists and instrumentation is active. Importing
        # `src.ui.main_window` (or alternative locations) earlier could
        # trigger module-level widget construction before we have a
        # parent anchor; importing it here prevents that.
        for _mod in ("ui.main_window", "src.ui.main_window", "main_window"):
            try:
                m = importlib.import_module(_mod)
                if hasattr(m, "MainWindow"):
                    AppMainWindow = getattr(m, "MainWindow")
                    break
            except Exception as e:
                try:
                    logger.debug("Failed to import %s: %s", _mod, e)
                except Exception:
                    pass

        win = AppMainWindow()

        # Reparent any widgets that were created against the temporary
        # startup anchor onto the real main window so they no longer
        # behave as detached top-level windows.
        try:
            if _temp_startup_anchor is not None:
                try:
                    for child in list(_temp_startup_anchor.findChildren(QWidget)):
                        try:
                            child.setParent(win)
                            try:
                                child.hide()
                            except Exception:
                                pass
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    _temp_startup_anchor.deleteLater()
                except Exception:
                    pass

        except Exception:
            pass

        # Set force-parent anchor so widgets created without a parent
        # during early startup get attached to the main window.
        try:
            _FORCE_PARENT_TO = win
        except Exception:
            pass
        # Install a temporary guard that prevents arbitrary top-level
        # widgets from being shown during early startup. Restore original
        # behavior after a short grace period.
        try:
            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QWidget

            _orig_show = getattr(QWidget, "show", None)

            def _guarded_show(self, *a, **kw):
                try:
                    # Allow the main window and any widgets that have a parent
                    if (
                        self is win
                        or getattr(self, "parent", lambda: None)() is not None
                    ):
                        if _orig_show:
                            return _orig_show(self, *a, **kw)
                        return None
                    # Otherwise, suppress showing top-level widgets during startup
                    try:
                        self.hide()
                    except Exception:
                        pass
                    return None
                except Exception:
                    if _orig_show:
                        return _orig_show(self, *a, **kw)
                    return None

            try:
                setattr(QWidget, "show", _guarded_show)
                # Restore after 20s so dialogs and normal windows function later
                QTimer.singleShot(20000, lambda: setattr(QWidget, "show", _orig_show))
                # Clear the forced-parent anchor after a longer grace period
                try:
                    # Keep the force-parent anchor longer to catch delayed UI initializers
                    QTimer.singleShot(
                        18000, lambda: globals().update({"_FORCE_PARENT_TO": None})
                    )
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

        win.show()
        # Aggressively close or reparent any stray top-level widgets shortly
        # after showing the main window. Some modules create transient popups
        # or menus that briefly become top-level; close them to ensure only
        # the main window remains visible at startup.
        try:
            from PyQt6.QtCore import QTimer

            def _force_close_strays():
                try:
                    for w in list(app.topLevelWidgets()):
                        try:
                            if w is win:
                                continue
                            # Best-effort: try close() first (respects widget's
                            # cleanup handlers), then hide+deleteLater, and
                            # finally reparent to the main window.
                            try:
                                w.close()
                            except Exception:
                                try:
                                    w.hide()
                                except Exception:
                                    pass
                            try:
                                w.setParent(win)
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

            # Schedule multiple force-close attempts at short intervals
            for ms in (50, 150, 300, 700, 1000, 2000, 3000, 5000):
                try:
                    QTimer.singleShot(ms, _force_close_strays)
                except Exception:
                    pass
        except Exception:
            pass
        # Temporarily hide the main menubar to avoid transient detached
        # QMenu popups or stray menus during startup. Restore after app
        # initialization has settled.
        try:
            from PyQt6.QtCore import QTimer

            try:
                mb = win.menuBar()
                if mb is not None:
                    try:
                        mb.hide()
                    except Exception:
                        pass
                    QTimer.singleShot(2500, lambda: mb.show())
                    QTimer.singleShot(8000, lambda: mb.show())
            except Exception:
                pass
        except Exception:
            pass
        # Defensive: prune stray top-level widgets that may have been created
        # by modules during startup (prevents transient second windows).
        try:
            from PyQt6.QtCore import QTimer

            def _prune_top_level():
                try:
                    for w in list(app.topLevelWidgets()):
                        try:
                            # Keep the main window visible; reparent obvious stray widgets
                            if w is win:
                                continue
                            # Aggressively reparent any top-level widget that is not
                            # the main window. This prevents modules from briefly
                            # creating detached windows during startup. Exclude
                            # dialogs that intentionally require top-level behavior.
                            try:
                                # Attach to the main window so they are not top-level.
                                w.setParent(win)
                                # Clear window flags so it behaves as a widget rather than a top-level window
                                try:
                                    w.setWindowFlag(Qt.WindowType.Window, False)
                                    w.setWindowFlag(Qt.WindowType.Dialog, False)
                                except Exception:
                                    pass
                                # Ensure they are hidden initially to avoid visual glitches.
                                try:
                                    w.hide()
                                except Exception:
                                    pass
                                # As a last resort, schedule deleteLater for purely transient UI
                                try:
                                    w.deleteLater()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        except Exception:
                            pass
                except Exception:
                    pass

                try:
                    # Run pruning multiple times to catch widgets created at different
                    # moments during early startup (immediate, short delays, and later spikes).
                    QTimer.singleShot(0, _prune_top_level)
                    QTimer.singleShot(500, _prune_top_level)
                    QTimer.singleShot(1000, _prune_top_level)
                    QTimer.singleShot(2000, _prune_top_level)
                    QTimer.singleShot(3000, _prune_top_level)
                    QTimer.singleShot(5000, _prune_top_level)
                    QTimer.singleShot(10000, _prune_top_level)
                    QTimer.singleShot(15000, _prune_top_level)
                    QTimer.singleShot(20000, _prune_top_level)
                    # Additionally, run a longer-lived repeating prune timer to
                    # aggressively catch widgets that appear shortly after startup.
                    try:
                        _rep_timer = QTimer()
                        _rep_timer.setInterval(200)
                        _rep_count = {"n": 0}

                        def _rep_prune():
                            try:
                                _prune_top_level()
                            except Exception:
                                pass
                            _rep_count["n"] += 1
                            if _rep_count["n"] > 120:
                                try:
                                    _rep_timer.stop()
                                except Exception:
                                    pass

                        try:
                            _rep_timer.timeout.connect(_rep_prune)
                            _rep_timer.start()
                        except Exception:
                            pass
                    except Exception:
                        pass
                except Exception:
                    pass

        except Exception:
            pass
        # Log top-level widgets after showing main window to help diagnose transient windows
        try:
            from pathlib import Path as _P

            from PyQt6.QtCore import QTimer

            trace_file = _P(get_log_dir()) / "startup_trace.log"
            with open(trace_file, "a", encoding="utf-8") as _tf:
                _tf.write(
                    f"startup: post-window topLevelWidgets={len(app.topLevelWidgets())}\n"
                )

            # Also write delayed snapshots to catch windows that appear shortly
            # after startup (e.g. scheduled dialogs or background initializers).
            def _dump_later():
                try:
                    widgets = list(app.topLevelWidgets())
                    with open(trace_file, "a", encoding="utf-8") as _tf2:
                        _tf2.write(
                            f"startup: later-window(1s) topLevelWidgets={len(widgets)}\n"
                        )
                        for w in widgets:
                            try:
                                title = ""
                                try:
                                    title = (
                                        w.windowTitle()
                                        if hasattr(w, "windowTitle")
                                        else ""
                                    )
                                except Exception:
                                    title = ""
                                p = None
                                try:
                                    p = w.parent()
                                except Exception:
                                    p = None
                                pinfo = "<none>"
                                try:
                                    if p is not None:
                                        pinfo = f"{type(p).__name__} ({getattr(p, 'objectName', lambda: '')()})"
                                except Exception:
                                    pinfo = "<err>"
                                _tf2.write(
                                    f"  widget: {type(w).__name__} - title={title} - parent={pinfo}\n"
                                )
                            except Exception:
                                pass
                    # Attempt to reparent/hide any remaining stray widgets seen at 1s
                    try:
                        for w in list(app.topLevelWidgets()):
                            try:
                                if w is win:
                                    continue
                                try:
                                    w.setParent(win)
                                except Exception:
                                    pass
                                try:
                                    w.hide()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception:
                    pass

            def _dump_later_3s():
                try:
                    widgets = list(app.topLevelWidgets())
                    with open(trace_file, "a", encoding="utf-8") as _tf3:
                        _tf3.write(
                            f"startup: later-window(3s) topLevelWidgets={len(widgets)}\n"
                        )
                        for w in widgets:
                            try:
                                title = ""
                                try:
                                    title = (
                                        w.windowTitle()
                                        if hasattr(w, "windowTitle")
                                        else ""
                                    )
                                except Exception:
                                    title = ""
                                p = None
                                try:
                                    p = w.parent()
                                except Exception:
                                    p = None
                                pinfo = "<none>"
                                try:
                                    if p is not None:
                                        pinfo = f"{type(p).__name__} ({getattr(p, 'objectName', lambda: '')()})"
                                except Exception:
                                    pinfo = "<err>"
                                _tf3.write(
                                    f"  widget: {type(w).__name__} - title={title} - parent={pinfo}\n"
                                )
                            except Exception:
                                pass
                    # Final attempt: reparent/hide any remaining stray widgets at 3s
                    try:
                        for w in list(app.topLevelWidgets()):
                            try:
                                if w is win:
                                    continue
                                try:
                                    w.setParent(win)
                                except Exception:
                                    pass
                                try:
                                    w.hide()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception:
                    pass

            try:
                QTimer.singleShot(1000, _dump_later)
                QTimer.singleShot(3000, _dump_later_3s)
                # Additional later snapshot to capture very-delayed initializers
                try:
                    QTimer.singleShot(8000, _dump_later_3s)
                except Exception:
                    pass

                # As an extra safeguard: aggressively reparent any widgets
                # found among all widgets that still have no parent at these
                # moments. Some code creates widgets without parents that may
                # not be reachable via topLevelWidgets() immediately.
                def _aggressive_reparent():
                    try:
                        app = None
                        try:
                            from PyQt6.QtWidgets import QApplication

                            app = QApplication.instance()
                        except Exception:
                            app = None
                        if not app:
                            return
                        for w in list(app.allWidgets()):
                            try:
                                p = None
                                try:
                                    p = w.parent()
                                except Exception:
                                    p = None
                                if (
                                    p is None
                                    and w is not win
                                    and type(w).__name__
                                    not in ("QMainWindow", "QDialog")
                                ):
                                    try:
                                        w.setParent(win)
                                    except Exception:
                                        pass
                                    try:
                                        w.hide()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                    except Exception:
                        pass

                try:
                    QTimer.singleShot(1100, _aggressive_reparent)
                    QTimer.singleShot(3100, _aggressive_reparent)
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass
        sys.exit(app.exec())
    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(tb)
        app = QApplication([])
        QMessageBox.critical(
            None,
            "Feil ved oppstart",
            f"Det oppstod en feil:\n{e}\nSe error.log for detaljer.",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
