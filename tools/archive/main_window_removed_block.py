# Archived stray block removed from src/ui/main_window.py on fix
# The block was incorrectly indented inside the class and caused an IndentationError.
# Kept here for audit / potential restoration.

# BEGIN REMOVED BLOCK
try:
    self.mode_manager = UserModeManager()
    # Expose UserMode for other methods
    try:
        self._UserMode = UserMode
    except NameError:
        self._UserMode = type("UserMode", (), {"BEGINNER": 0, "EXPERT": 1})
    self.mode_manager.mode_changed.connect(self.on_mode_changed)

    # Initialize keyboard shortcuts manager (will be set up after UI is created)
    self.shortcuts_manager = None

    # Load language setting
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    language = settings.value("language", "Norsk")
    lang_code = "no" if language == "Norsk" else "en"
    set_language(lang_code)

    self.init_ui()
except Exception as e:
    # Log and persist the exception to help debugging when GUI fails silently
    import traceback

    err = f"Exception in MainWindow.__init__: {e}\n{traceback.format_exc()}"
    logger.exception("%s", err)
    try:
        from HjemmeladingApp.utils.safe_logger import append_exception
    except Exception:

        def append_exception(msg, exc=None):
            return None

    try:
        append_exception(err, e)
    except Exception:
        pass
    from PyQt6.QtWidgets import QMessageBox

    QMessageBox.critical(None, "Oppstartsfeil", err)
    # Re-raise so caller can also handle it
    raise

# END REMOVED BLOCK
