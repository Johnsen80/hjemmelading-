import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
    QMenuBar,
    QMenu,
    QMessageBox,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QCoreApplication
import os
import sys
import traceback
import os
from pathlib import Path
# Ensure the project root is on sys.path so absolute imports like
# `from HjemmeladingApp...` work even when the application is launched
# from a shortcut with a different current working directory.
try:
    proj_root = Path(__file__).resolve().parents[1]
    proj_root_str = str(proj_root)
    if proj_root_str not in sys.path:
        sys.path.insert(0, proj_root_str)
except Exception:
    pass

try:
    from HjemmeladingApp.utils.safe_logger import append_exception, append_message
except Exception:
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

# Install a small global excepthook so unhandled exceptions are persisted
def _global_excepthook(exc_type, exc_value, exc_tb):
    try:
        tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            append_exception('Uncaught exception (HjemmeladingApp): ' + tb, exc_value)
        except Exception:
            pass
        try:
            # attempt to write a small error file next to the exe/script
            with open('hjemmeladingapp_error.log', 'w', encoding='utf-8') as f:
                f.write(tb)
        except Exception:
            pass
    except Exception:
        pass

try:
    sys.excepthook = _global_excepthook
except Exception:
    pass
# Per-user persistent diagnostics helper
try:
    from HjemmeladingApp.utils.safe_logger import append_exception, append_message
except Exception:
    def append_exception(msg, exc=None):
        return None
    def append_message(msg):
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HjemmeladingApp - Moderne og fleksibel")
        self.setMinimumSize(1000, 700)
        # Menylinje
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

        # Språk-meny (nå som undermeny under Innstillinger)
        language_menu = QMenu("Språk", self)
        settings_menu.addMenu(language_menu)
        for lang in ["Norsk", "Engelsk", "Tysk"]:
            lang_action = QAction(lang, self)
            # capture default arg to avoid late-binding lambda issue
            lang_action.triggered.connect(lambda checked, l=lang: self.set_language(l))
            language_menu.addAction(lang_action)

        # Åpne innstillinger (launcher for SettingsDialog)
        settings_action = QAction("Åpne innstillinger...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(settings_action)

        # Hovedinnhold
        central = QWidget()
        layout = QVBoxLayout()
        label = QLabel(
            "Velkommen! Dette er et moderne, fleksibelt program.\nHer kan du tilpasse utseende, tema og bakgrunn."
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
                    from HjemmeladingApp.utils.safe_logger import append_exception
                    append_exception('ProfileEditor creation failed: ' + str(e), e)
                except Exception:
                    pass
                QMessageBox.warning(self, "Feil", "Kunne ikke åpne profilredigerer (feil ved opprettelse).")
        except Exception:
            QMessageBox.warning(self, "Feil", "Kunne ikke åpne profilredigerer (mangler modul).")

    def set_language(self, lang):
        QMessageBox.information(self, "Språkvalg", f"Språk satt til: {lang}")

    def open_settings_dialog(self):
        # Add a small trace message to the per-user log to track attempts to open settings
        try:
            append_message('User invoked Open Settings')
        except Exception:
            pass
        try:
            from HjemmeladingApp.ui.settings_dialog import SettingsDialog
            # keep a reference so the dialog doesn't get garbage-collected
            try:
                self._settings_dialog = SettingsDialog(self)
            except Exception as e:
                try:
                    append_exception('SettingsDialog creation failed: ' + str(e), e)
                except Exception:
                    pass
                QMessageBox.warning(self, "Feil", f"Kunne ikke opprette innstillingsdialog: {e}")
                return

            # Prefer modal exec() for dialogs that support it; gracefully
            # fallback to show() when exec/exec_ isn't available.
            try:
                if hasattr(self._settings_dialog, "exec"):
                    self._settings_dialog.exec()
                elif hasattr(self._settings_dialog, "exec_"):
                    # PyQt5 compatibility name
                    self._settings_dialog.exec_()
                else:
                    self._settings_dialog.show()
            except Exception as e:
                # If exec fails at runtime, fallback to show() and log full traceback
                try:
                    import traceback
                    append_exception('SettingsDialog.exec/show failed: ' + traceback.format_exc(), e)
                except Exception:
                    pass
                try:
                    self._settings_dialog.show()
                except Exception:
                    pass
        except Exception as e:
            # Log full traceback to per-user debug_err.log to aid diagnosis
            try:
                import datetime
                import traceback as _tb
                append_exception(f"\n--- {datetime.datetime.utcnow().isoformat()}Z ---\n" + _tb.format_exc(), e)
            except Exception:
                pass
            # Attempt to show a user message without calling get_log_dir (may not be available here)
            try:
                QMessageBox.warning(self, "Feil", f"Kunne ikke åpne innstillinger: {e}\nSe per-user logg for detaljer.")
            except Exception:
                pass


def main():
    try:
        # Ensure QtWebEngine contexts attribute is set before creating QApplication
        try:
            QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        except Exception:
            # If setting the attribute fails, continue — it's non-fatal
            pass
        app = QApplication(sys.argv)
        # Register any bundled fonts so Qt and matplotlib pick them up early
        try:
            try:
                from HjemmeladingApp.utils.fonts import register_bundled_fonts
            except Exception:
                register_bundled_fonts = None
            if register_bundled_fonts:
                try:
                    n = register_bundled_fonts()
                    try:
                        from HjemmeladingApp.utils.safe_logger import append_message
                        append_message(f"Registered {n} bundled fonts at startup")
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass
        win = MainWindow()
        win.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(tb)
        # If Qt failed to initialize, show a simple message box using a temporary QApplication
        app = QApplication([])
        QMessageBox.critical(None, "Feil ved oppstart", f"Det oppstod en feil:\n{e}\nSe error.log for detaljer.")
        sys.exit(1)


if __name__ == "__main__":
    main()
