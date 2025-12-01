import sys
import traceback
from pathlib import Path
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

# Ensure project root is on sys.path so absolute imports work
try:
    proj_root = Path(__file__).resolve().parents[1]
    proj_root_str = str(proj_root)
    if proj_root_str not in sys.path:
        sys.path.insert(0, proj_root_str)
except Exception:
    pass

# Import safe logger (provide lightweight fallbacks)
try:
    from HjemmeladingApp.utils.safe_logger import append_exception, append_message
except Exception:

    def append_exception(msg, exc=None):
        return None

    def append_message(msg):
        return None


def _global_excepthook(exc_type, exc_value, exc_tb):
    try:
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            append_exception("Uncaught exception (HjemmeladingApp): " + tb, exc_value)
        except Exception:
            pass
        try:
            with open("hjemmeladingapp_error.log", "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
    except Exception:
        pass


try:
    sys.excepthook = _global_excepthook
except Exception:
    pass


class MainWindow(QMainWindow):
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
                except Exception:
                    pass
                QMessageBox.warning(
                    self,
                    "Feil",
                    "Kunne ikke åpne profilredigerer (feil ved opprettelse).",
                )
        except Exception:
            QMessageBox.warning(
                self, "Feil", "Kunne ikke åpne profilredigerer (mangler modul)."
            )

    def set_language(self, lang):
        QMessageBox.information(self, "Språkvalg", f"Språk satt til: {lang}")

    def open_settings_dialog(self):
        try:
            append_message("User invoked Open Settings")
        except Exception:
            pass
        try:
            from HjemmeladingApp.ui.settings_dialog import SettingsDialog

            try:
                self._settings_dialog = SettingsDialog(self)
            except Exception as e:
                try:
                    append_exception("SettingsDialog creation failed: " + str(e), e)
                except Exception:
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
                except Exception:
                    pass
                try:
                    self._settings_dialog.show()
                except Exception:
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
            except Exception:
                pass
            try:
                QMessageBox.warning(
                    self,
                    "Feil",
                    f"Kunne ikke åpne innstillinger: {e}\nSe per-user logg for detaljer.",
                )
            except Exception:
                pass


def main():
    try:
        try:
            QCoreApplication.setAttribute(
                Qt.ApplicationAttribute.AA_ShareOpenGLContexts
            )
        except Exception:
            pass
        app = QApplication(sys.argv)
        try:
            try:
                from HjemmeladingApp.utils.fonts import register_bundled_fonts
            except Exception:
                register_bundled_fonts = None
            if register_bundled_fonts:
                try:
                    n = register_bundled_fonts()
                    try:
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
        app = QApplication([])
        QMessageBox.critical(
            None,
            "Feil ved oppstart",
            f"Det oppstod en feil:\n{e}\nSe error.log for detaljer.",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
