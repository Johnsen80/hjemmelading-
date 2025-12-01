from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox
import logging
from HjemmeladingApp.utils.safe_logger import append_exception
logger = logging.getLogger(__name__)

try:
    from HjemmeladingApp.modules.user_profile import UserProfile
except Exception:
    try:
        # backwards-compatible import if running from package root
        from HjemmeladingApp.modules.user_profile import UserProfile  # type: ignore
    except Exception as _up_err:
        # Provide a lightweight stub so the UI doesn't crash when module missing
        try:
            append_exception(f"UserProfile import failed: {_up_err}", _up_err)
        except Exception:
            pass
        class UserProfile:
            def __init__(self):
                self.data = {}
            def save(self):
                return False
            def export(self, path):
                return False
            def import_profile(self, path):
                return False


class ProfileEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Build UI inside try/except so failures in optional subsystems don't kill the app
        try:
            self.setWindowTitle("Brukerprofil og innstillinger")
            self.setMinimumSize(400, 350)
            self.profile = UserProfile()
            # Ensure profile has a data dict
            if not hasattr(self.profile, 'data') or not isinstance(self.profile.data, dict):
                self.profile.data = {}

            layout = QVBoxLayout()

            self.username_edit = QLineEdit(self.profile.data.get("username", ""))
            layout.addWidget(QLabel("Brukernavn:"))
            layout.addWidget(self.username_edit)

            self.theme_combo = QComboBox()
            self.theme_combo.addItems(["Standard", "Lys", "Mørk", "Fargerik"])
            self.theme_combo.setCurrentText(self.profile.data.get("theme", "Standard"))
            layout.addWidget(QLabel("Tema:"))
            layout.addWidget(self.theme_combo)

            self.button_combo = QComboBox()
            self.button_combo.addItems(["Standard", "Rund", "Fargerik", "Flat", "Glass"])
            self.button_combo.setCurrentText(self.profile.data.get("button_style", "Standard"))
            layout.addWidget(QLabel("Knappestil:"))
            layout.addWidget(self.button_combo)

            self.bg_edit = QLineEdit(self.profile.data.get("background", ""))
            self.bg_btn = QPushButton("Velg bakgrunnsbilde")
            self.bg_btn.clicked.connect(self.choose_bg)
            layout.addWidget(QLabel("Bakgrunnsbilde:"))
            layout.addWidget(self.bg_edit)
            layout.addWidget(self.bg_btn)

            self.save_btn = QPushButton("Lagre innstillinger")
            self.save_btn.clicked.connect(self.save)
            layout.addWidget(self.save_btn)

            self.export_btn = QPushButton("Eksporter profil")
            self.export_btn.clicked.connect(self.export)
            layout.addWidget(self.export_btn)

            self.import_btn = QPushButton("Importer profil")
            self.import_btn.clicked.connect(self.import_profile)
            layout.addWidget(self.import_btn)

            self.setLayout(layout)
        except Exception as _init_err:
            # If constructing full UI fails, provide a minimal fallback so app continues
            try:
                append_exception(f"ProfileEditor init failed: {_init_err}", _init_err)
            except Exception:
                pass
            logger.exception("ProfileEditor init failed")
            fallback_layout = QVBoxLayout()
            fallback_layout.addWidget(QLabel("Profilredigering er midlertidig utilgjengelig."))
            close_btn = QPushButton("Lukk")
            close_btn.clicked.connect(self.close)
            fallback_layout.addWidget(close_btn)
            self.setLayout(fallback_layout)
            # Ensure attributes exist to avoid attribute errors elsewhere
            self.profile = UserProfile()
            if not hasattr(self.profile, 'data'):
                self.profile.data = {}

    def choose_bg(self):
        try:
            file, _ = QFileDialog.getOpenFileName(self, "Velg bilde", "", "Bilder (*.png *.jpg *.jpeg *.bmp)")
            if file:
                self.bg_edit.setText(file)
        except Exception as _bg_err:
            try:
                append_exception(f"choose_bg failed: {_bg_err}", _bg_err)
            except Exception:
                pass
            logger.exception("choose_bg failed")

    def save(self):
        try:
            self.profile.data["username"] = self.username_edit.text()
            self.profile.data["theme"] = self.theme_combo.currentText()
            self.profile.data["button_style"] = self.button_combo.currentText()
            self.profile.data["background"] = self.bg_edit.text()
            ok = False
            try:
                ok = bool(getattr(self.profile, 'save', lambda: False)())
            except Exception as _save_err:
                try:
                    append_exception(f"Profile save failed: {_save_err}", _save_err)
                except Exception:
                    pass
                logger.exception("Profile save failed")
            if ok:
                try:
                    QMessageBox.information(self, "Lagret", "Innstillinger lagret!")
                except Exception:
                    # non-blocking fallback when running headless
                    logger.info("Settings saved (no UI notification available)")
            else:
                try:
                    QMessageBox.warning(self, "Feil", "Kunne ikke lagre innstillinger.")
                except Exception:
                    logger.warning("Could not show save warning messagebox")
        except Exception as _err:
            try:
                append_exception(f"save handler exception: {_err}", _err)
            except Exception:
                pass
            logger.exception("save handler exception")

    def export(self):
        try:
            file, _ = QFileDialog.getSaveFileName(self, "Eksporter profil", "", "JSON (*.json)")
            if file:
                ok = False
                try:
                    ok = bool(getattr(self.profile, 'export', lambda p: False)(file))
                except Exception as _exp_err:
                    try:
                        append_exception(f"Profile export failed: {_exp_err}", _exp_err)
                    except Exception:
                        pass
                    logger.exception("Profile export failed")
                if ok:
                    try:
                        QMessageBox.information(self, "Eksportert", "Profil eksportert!")
                    except Exception:
                        logger.info("Profile exported (no UI notification)")
                else:
                    try:
                        QMessageBox.warning(self, "Feil", "Eksport feilet!")
                    except Exception:
                        logger.warning("Could not show export warning messagebox")
        except Exception as _err:
            try:
                append_exception(f"export handler exception: {_err}", _err)
            except Exception:
                pass
            logger.exception("export handler exception")

    def import_profile(self):
        try:
            file, _ = QFileDialog.getOpenFileName(self, "Importer profil", "", "JSON (*.json)")
            if file:
                ok = False
                try:
                    ok = bool(getattr(self.profile, 'import_profile', lambda p: False)(file))
                except Exception as _imp_err:
                    try:
                        append_exception(f"Profile import failed: {_imp_err}", _imp_err)
                    except Exception:
                        pass
                    logger.exception("Profile import failed")
                if ok:
                    try:
                        QMessageBox.information(self, "Importert", "Profil importert!")
                    except Exception:
                        logger.info("Profile imported (no UI notification)")
                    # Update UI fields safely
                    try:
                        self.username_edit.setText(self.profile.data.get("username", ""))
                        self.theme_combo.setCurrentText(self.profile.data.get("theme", "Standard"))
                        self.button_combo.setCurrentText(self.profile.data.get("button_style", "Standard"))
                        self.bg_edit.setText(self.profile.data.get("background", ""))
                    except Exception:
                        logger.exception("Failed to update profile fields after import")
                else:
                    try:
                        QMessageBox.warning(self, "Feil", "Import feilet!")
                    except Exception:
                        logger.warning("Could not show import warning messagebox")
        except Exception as _err:
            try:
                append_exception(f"import handler exception: {_err}", _err)
            except Exception:
                pass
            logger.exception("import handler exception")
