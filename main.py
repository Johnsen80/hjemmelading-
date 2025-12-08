"""
Hovedprogram for Reloading Workshop Manager
"""

import os
import site
import sys
import traceback
from pathlib import Path

# Ensure the application can import the `src` package when running from a PyInstaller
# bundle (extracted to sys._MEIPASS) or when running from the repo root.
if getattr(sys, "frozen", False):
    _base = getattr(sys, "_MEIPASS", None)
    if _base and _base not in sys.path:
        sys.path.insert(0, _base)
else:
    _base = os.path.dirname(os.path.abspath(__file__))
    if _base not in sys.path:
        sys.path.insert(0, _base)

from src.logging_config import configure_logging, get_log_dir, get_logger

# Configure logging early
configure_logging()
logger = get_logger(__name__)
# Per-user persistent diagnostics helper
try:
    from HjemmeladingApp.utils.safe_logger import append_exception, append_message
except Exception:
    # If the helper is missing or broken, continue without raising.
    def append_exception(msg, exc=None):
        try:
            return None
        except Exception:
            return None

    def append_message(msg):
        try:
            return None
        except Exception:
            return None


# Attempt to import PyQt after logging is configured so import errors are captured
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
except Exception as e:
    # Write detailed import error to debug_err.log and exit
    err = f"Failed to import PyQt6: {e}\n{traceback.format_exc()}"
    logger.exception("PyQt6 import failed: %s", e)
    try:
        # Persist to per-user debug_err.log when possible
        append_exception(err, e)
    except Exception:
        pass
    print(err, file=sys.stderr)
    sys.exit(3)


def main():
    """Hovedfunksjon som starter applikasjonen"""

    # Helper: locate likely Qt plugin directories (returns list)
    def locate_qt_plugin_paths():
        candidates = []
        # If frozen, check _MEIPASS siblings
        if getattr(sys, "frozen", False):
            base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
                os.path.abspath(__file__)
            )
            candidates += [
                os.path.join(base, "Qt", "plugins"),
                os.path.join(base, "plugins"),
                os.path.join(base, "platforms"),
                os.path.join(base, "PyQt6", "Qt", "plugins"),
            ]

        # venv / site-packages locations
        try:
            for sp in site.getsitepackages():
                p = Path(sp) / "PyQt6" / "Qt" / "plugins"
                candidates.append(str(p))
                p2 = Path(sp) / "Qt" / "plugins"
                candidates.append(str(p2))
        except Exception:
            pass

        # sys.prefix (virtualenv) and common relative paths
        try:
            pref = Path(sys.prefix)
            candidates.append(
                str(pref / "Lib" / "site-packages" / "PyQt6" / "Qt" / "plugins")
            )
            candidates.append(str(pref / "Lib" / "site-packages" / "Qt" / "plugins"))
        except Exception:
            pass

        # Filter and return only existing dirs, deduped
        seen = set()
        found = []
        for c in candidates:
            if not c:
                continue
            try:
                p = os.path.normpath(c)
            except Exception:
                p = c
            if p in seen:
                continue
            seen.add(p)
            if os.path.isdir(p):
                found.append(p)
        return found

    def dump_startup_env(log_path=None):
        """Dump a brief startup environment to the per-user debug_app.log by default.

        If `log_path` is provided it will be used verbatim; otherwise the
        per-user log directory from `get_log_dir()` is used.
        """
        try:
            if log_path is None:
                log_dir = get_log_dir()
                log_path = os.path.join(log_dir, "debug_app.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("--- Startup environment ---\n")
                f.write(f"EXE: {sys.executable}\n")
                f.write(f"VERSION: {sys.version}\n")
                f.write(f"PWD: {os.getcwd()}\n")
                f.write(f'PATH: {os.environ.get("PATH")[:4000]}\n')
                f.write(
                    f'QT_QPA_PLATFORM_PLUGIN_PATH: {os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH")}\n'
                )
                f.write("-------------------------\n")
        except Exception:
            pass

    # VIKTIG: High DPI støtte - sett FØR QApplication opprettes
    # PyQt6 har automatisk high DPI scaling, men vi setter noen attributter
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass  # Eldre PyQt6 versjoner
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    # Before creating QApplication, try to locate and set Qt plugin paths
    try:
        plugin_paths = locate_qt_plugin_paths()
        if plugin_paths:
            # Prefer the first valid path
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", plugin_paths[0])
            try:
                from PyQt6.QtCore import QCoreApplication

                for p in plugin_paths:
                    QCoreApplication.addLibraryPath(p)
                    logger.info("Adding Qt lib path: %s", p)
            except Exception:
                logger.exception("Failed to add Qt lib paths via QCoreApplication")
        else:
            logger.warning("No Qt plugin paths located by heuristic")
    except Exception:
        logger.exception("Error while locating Qt plugin paths")

    dump_startup_env()

    # Opprett Qt-applikasjon
    # Install a global excepthook so uncaught exceptions (including those
    # originating from slots) are persisted to our per-user diagnostics and
    # do not silently kill the process without a trace.
    def _global_excepthook(exc_type, exc_value, exc_traceback):
        try:
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            logger.critical("Uncaught exception: %s", tb)
            try:
                append_exception("Uncaught exception", exc_value)
            except Exception:
                pass
            # If a QApplication exists, show a simple dialog to inform the user.
            try:
                from PyQt6.QtWidgets import QApplication, QMessageBox

                app_inst = QApplication.instance()
                if app_inst is not None:
                    try:
                        QMessageBox.critical(
                            None,
                            "Uventet feil",
                            "Et uventet problem oppstod. Se debug_err.log for detaljer.",
                        )
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            # Avoid any exceptions escaping the excepthook
            pass

    try:
        sys.excepthook = _global_excepthook
    except Exception:
        pass
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Reloading Workshop Manager")
        app.setOrganizationName("ReloadingTools")
    except Exception as e:
        # Log and persist failure to create QApplication (often plugin/path issues)
        err = f"Failed to create QApplication: {e}\n{traceback.format_exc()}"
        logger.exception("Failed to create QApplication: %s", e)
        try:
            append_exception(err, e)
            try:
                append_message(
                    "QT_QPA_PLATFORM=" + str(os.environ.get("QT_QPA_PLATFORM"))
                )
                append_message("PATH=" + str(os.environ.get("PATH")))
            except Exception:
                pass
        except Exception:
            pass
        print(err, file=sys.stderr)
        sys.exit(4)

    # Attempt to load bundled fonts from `HjemmeladingApp/resources/fonts/`.
    # Place any .ttf files there (e.g. DejaVu fonts) to ensure Qt/Matplotlib
    # can render glyphs even if the system has no fonts installed.
    try:
        import glob

        from PyQt6.QtGui import QFontDatabase

        # _base defined earlier as repo root or sys._MEIPASS; fall back to dirname
        try:
            fonts_dir = os.path.join(_base, "HjemmeladingApp", "resources", "fonts")
        except Exception:
            fonts_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "HjemmeladingApp",
                "resources",
                "fonts",
            )
        loaded = []
        if os.path.isdir(fonts_dir):
            for ttf in glob.glob(os.path.join(fonts_dir, "*.ttf")):
                try:
                    fid = QFontDatabase.addApplicationFont(ttf)
                    if fid != -1:
                        fams = QFontDatabase.applicationFontFamilies(fid)
                        loaded.append((os.path.basename(ttf), list(fams)))
                except Exception as e:
                    logger.exception("Failed to add font %s: %s", ttf, e)
                    try:
                        append_exception(f"Failed to add font {ttf}", e)
                    except Exception:
                        pass
        if loaded:
            logger.info("Bundled fonts loaded: %s", loaded)
            try:
                append_message(
                    "Bundled fonts loaded: " + ", ".join([n for n, _ in loaded])
                )
            except Exception:
                pass
            # Also register the ttf files with matplotlib's font manager so
            # matplotlib can find glyphs (e.g. emoji/bar-chart) even if the
            # system fontconfig doesn't see them yet.
            try:
                import matplotlib as mpl
                import matplotlib.font_manager as mfm

                try:
                    cache_dir = mpl.get_cachedir()
                    append_message(f"matplotlib cache dir: {cache_dir}")
                except Exception:
                    cache_dir = None
                # Use the modern API when available: fontManager.addfont
                for ttf_path in glob.glob(os.path.join(fonts_dir, "*.ttf")):
                    try:
                        if hasattr(mfm, "fontManager") and hasattr(
                            mfm.fontManager, "addfont"
                        ):
                            mfm.fontManager.addfont(ttf_path)
                        elif hasattr(mfm, "addfont"):
                            mfm.addfont(ttf_path)
                        else:
                            # older matplotlib: try adding via FontProperties fallback
                            try:
                                from matplotlib.font_manager import FontProperties

                                FontProperties(fname=ttf_path)
                            except Exception:
                                pass
                        logger.info("Registered font with matplotlib: %s", ttf_path)
                    except Exception as e:
                        logger.exception(
                            "Failed to register font with matplotlib: %s", e
                        )
                        try:
                            append_exception(
                                f"Failed to register font with matplotlib: {ttf_path}",
                                e,
                            )
                        except Exception:
                            pass
                # Attempt to rebuild matplotlib's font cache so newly added fonts are picked up
                try:
                    if hasattr(mfm, "fontManager") and hasattr(mfm, "_rebuild"):
                        # Some MPL versions expose a top-level _rebuild
                        try:
                            mfm._rebuild()
                        except Exception:
                            # fallback to fontManager internal rebuild
                            try:
                                mfm.fontManager._rebuild()
                            except Exception:
                                pass
                    else:
                        # Try to force a rebuild via the fontManager instance
                        try:
                            mfm.fontManager._rebuild()
                        except Exception:
                            pass
                except Exception:
                    pass
                # If DejaVu Sans is available in the QFontDatabase-loaded fonts, prefer it
                try:
                    if any("DejaVu Sans" in fam for _, fams in loaded for fam in fams):
                        try:
                            mpl.rcParams["font.family"] = "DejaVu Sans"
                            append_message("matplotlib configured to use DejaVu Sans")
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                # matplotlib not available or registration failed; continue
                try:
                    append_message(
                        "matplotlib font registration skipped (matplotlib not installed)."
                    )
                except Exception:
                    pass
    except Exception:
        # Non-fatal; record diagnostics for later inspection
        try:
            append_message("Bundled font loading skipped or failed during startup.")
        except Exception:
            pass

    # FONT CHECK: Qt may not ship fonts in some PyQt6 deployments. If the
    # QFontDatabase seems empty, persist advice to the per-user log so
    # users know how to remedy missing glyphs (matplotlib/Qt font warnings).
    try:
        from PyQt6.QtGui import QFontDatabase

        try:
            families = QFontDatabase().families()
            if not families or len(families) < 5:
                msg = (
                    "Warning: Qt font database appears empty or minimal. "
                    "Missing fonts can cause glyphs/icons to be absent. "
                    "Install DejaVu fonts or configure fontconfig. See: https://dejavu-fonts.github.io/"
                )
                logger.warning(msg)
                try:
                    append_message(msg)
                except Exception:
                    pass
        except Exception:
            # If QFontDatabase operations fail, log a diagnostic entry.
            try:
                append_message("QFontDatabase check failed during startup.")
            except Exception:
                pass
    except Exception:
        # PyQt6.QtGui might not be importable here in some environments; skip.
        pass

    # When running as a PyInstaller bundle, Qt platform plugins may be located
    # under the extracted `_MEIPASS` directory. Try to add common plugin paths
    # to Qt's library path and to `QT_QPA_PLATFORM_PLUGIN_PATH` so the
    # application can find `qwindows.dll` and other plugins.
    try:
        from PyQt6.QtCore import QCoreApplication

        if getattr(sys, "frozen", False):
            # Running as a PyInstaller bundle: prefer plugin paths inside _MEIPASS
            base = getattr(sys, "_MEIPASS", None) or _base
            logger.info(
                "Detected frozen execution; checking Qt plugin paths under %s", base
            )
            # Common layout: <_MEIPASS>/Qt/plugins or <_MEIPASS>/platforms
            possible = [
                os.path.join(base, "Qt", "plugins"),
                os.path.join(base, "plugins"),
                os.path.join(base, "platforms"),
                os.path.join(base, "PyQt6", "Qt", "plugins"),
            ]
            for p in possible:
                if os.path.isdir(p):
                    try:
                        QCoreApplication.addLibraryPath(p)
                        # Also set env var for safety
                        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = p
                        logger.info("Added Qt plugin path: %s", p)
                        break
                    except Exception:
                        logger.exception("Failed to add Qt plugin path: %s", p)
        else:
            # Running from source / venv: try to locate development-installed PyQt6 plugins
            # For non-frozen runs, ensure the environment can find Qt plugins
            # (useful for virtualenvs where PyQt installs plugins under site-packages)
            import importlib.util

            try:
                spec = importlib.util.find_spec("PyQt6")
                if spec and spec.origin:
                    candidate = os.path.join(
                        os.path.dirname(spec.origin), "..", "Qt", "plugins"
                    )
                    candidate = os.path.normpath(candidate)
                    if os.path.isdir(candidate):
                        logger.info("Running dev: adding Qt plugin path: %s", candidate)
                        try:
                            QCoreApplication.addLibraryPath(candidate)
                            os.environ.setdefault(
                                "QT_QPA_PLATFORM_PLUGIN_PATH", candidate
                            )
                            logger.info("Added Qt plugin path (dev): %s", candidate)
                        except Exception:
                            logger.exception(
                                "Failed to add Qt plugin path (dev): %s", candidate
                            )
            except Exception:
                logger.exception("Error locating PyQt6 plugin path in dev env")
    except Exception:
        # Non-fatal if QtCore isn't available yet
        pass

    # Sett stil
    app.setStyle("Fusion")
    # Show a minimal splash/launcher window immediately so the user sees something
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

    splash = QWidget()
    splash.setWindowTitle("VALKYRIE BALLISTICS - Starting")
    splash_layout = QVBoxLayout()
    splash_label = QLabel("Starting VALKYRIE BALLISTICS...\nPlease wait.")
    splash_layout.addWidget(splash_label)
    splash.setLayout(splash_layout)
    splash.resize(800, 300)
    # Always on top
    try:
        splash.setWindowFlag(splash.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    except Exception:
        pass
    # Tving midt på skjermen
    try:
        screen = app.primaryScreen()
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - splash.width()) // 2
        y = geo.y() + (geo.height() - splash.height()) // 2
        splash.move(x, y)
    except Exception as e:
        try:
            log_dir = get_log_dir()
            with open(
                os.path.join(log_dir, "debug_app.log"), "a", encoding="utf-8"
            ) as f:
                f.write(f"Splash move error: {e}\n")
        except Exception:
            logger.exception("Failed to write splash move error to per-user log: %s", e)
    splash.show()
    app.processEvents()
    # Logg posisjon og størrelse
    try:
        try:
            log_dir = get_log_dir()
            with open(
                os.path.join(log_dir, "debug_app.log"), "a", encoding="utf-8"
            ) as f:
                f.write(f"Splash pos: {splash.pos()}, size: {splash.size()}\n")
        except Exception:
            logger.exception("Failed to write splash position to per-user log")
    except Exception:
        pass

    # Add a timer to update splash if nothing happens in 10s and 30s
    def still_waiting():
        splash_label.setText(
            "Still waiting...\nIf no window appears, check debug_err.log."
        )
        splash.show()
        app.processEvents()
        # Sjekk om vinduet er synlig
        if not splash.isVisible():
            splash_label.setText(
                "FEIL: Splash-vinduet er usynlig! Sjekk skjerminnstillinger og driver."
            )
            splash.show()
            app.processEvents()

    QTimer.singleShot(10000, still_waiting)
    QTimer.singleShot(
        30000,
        lambda: splash_label.setText(
            "Startup failed or is blocked.\nNo window appeared.\nCheck debug_err.log and debug_app.log."
        ),
    )

    # Opprett og vis hovedvindu med feilhåndtering
    try:
        logger.info("Starter MainWindow...")
        from src.ui.main_window import MainWindow

        window = MainWindow()
        logger.info("MainWindow opprettet, viser vindu...")
        # Close splash and show main window
        try:
            splash.close()
        except Exception:
            pass
        window.show()
        logger.info("window.show() kjørt")
        # Ensure window is raised and activated
        try:
            window.raise_()
            window.activateWindow()
            QTimer.singleShot(200, lambda: (window.raise_(), window.activateWindow()))
        except Exception:
            pass
    except Exception as e:

        error_msg = (
            f"Det oppstod en feil under oppstart:\n{e}\n\n{traceback.format_exc()}"
        )
        logger.exception("Oppstartsfeil: %s", e)
        try:
            append_exception(error_msg, e)
        except Exception:
            pass
        # Show error message in the splash window so user sees it without modal dialogs
        try:
            splash_label.setText("Startup error:\nSee debug_err.log for details.")
            # Always-on-top and visible
            try:
                splash.setWindowFlag(
                    splash.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
                )
            except Exception:
                pass

            # Buttons: Open debug log, Retry launching main window, Quit
            btn_open = QPushButton("Open debug log")

            def _open_log():
                try:
                    import os

                    # Prefer per-user logs if available
                    log_dir = get_log_dir()
                    perr = os.path.join(log_dir, "debug_err.log")
                    papp = os.path.join(log_dir, "debug_app.log")
                    if os.path.exists(perr):
                        os.startfile(perr)
                    elif os.path.exists(papp):
                        os.startfile(papp)
                    else:
                        # fallback: show a messagebox with recent log tail
                        from PyQt6.QtWidgets import QMessageBox

                        QMessageBox.information(splash, "Logs", "No debug log found.")
                except Exception:
                    pass

            btn_open.clicked.connect(_open_log)

            btn_retry = QPushButton("Retry")

            def _retry():
                try:
                    # Attempt to re-import and create MainWindow
                    from importlib import reload

                    try:
                        import src.ui.main_window as mwmod

                        reload(mwmod)
                    except Exception:
                        pass
                    from src.ui.main_window import MainWindow

                    w = MainWindow()
                    w.show()
                    try:
                        splash.close()
                    except Exception:
                        pass
                except Exception as re:
                    # Log retry failure and keep splash visible
                    import traceback as _tb

                    msg = f"Retry failed: {re}\n{_tb.format_exc()}"
                    try:
                        append_exception(msg, re)
                    except Exception:
                        pass

            btn_retry.clicked.connect(_retry)

            btn_quit = QPushButton("Quit")
            btn_quit.clicked.connect(lambda: sys.exit(2))

            from PyQt6.QtWidgets import QHBoxLayout

            btn_row = QHBoxLayout()
            btn_row.addWidget(btn_open)
            btn_row.addWidget(btn_retry)
            btn_row.addWidget(btn_quit)
            splash_layout.addLayout(btn_row)
            splash_layout.addStretch()
            splash.show()
            # Ensure events processed so the splash appears immediately and stays on top
            app.processEvents()
        except Exception:
            pass

    # Start event loop
    try:
        sys.exit(app.exec())
    except Exception as e:
        logger.exception("Event loop feilet: %s", e)
        try:
            append_exception(f"Event loop feilet: {e}\n", e)
        except Exception:
            pass


if __name__ == "__main__":
    main()
