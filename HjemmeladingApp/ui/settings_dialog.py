from __future__ import annotations
from pathlib import Path
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from ..settings import settings
from ..utils import backgrounds, safe_logger

# Prefer the project's logging config when present, otherwise None
_logger = None


DEFAULT_LOGO_PATH = Path(
    r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\Logo"
)


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        # Wrap initialization so any unexpected error doesn't crash the whole app.
        self.setWindowTitle("Innstillinger — Hjemmelading")
        self.resize(600, 420)

        layout = QtWidgets.QVBoxLayout(self)

        # Top: logo
        self.logo_label = QtWidgets.QLabel()
        self.logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedHeight(100)
        layout.addWidget(self.logo_label)
        try:
            self._load_logo()
        except Exception as _suppressed_exc:
            try:
                from HjemmeladingApp.utils import safe_logger as _safe_logger
                _safe_logger.handle_suppressed(_suppressed_exc, "ui/settings_dialog.py")
            except Exception:
                try:
                    import sys
                    sys.stderr.write("ui/settings_dialog.py suppressed exception: " + str(_suppressed_exc) + "\n")
                except Exception:
                    pass
            pass

        # Tabs
        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs, 1)

        # Appearance tab
        appearance = QtWidgets.QWidget()
        tabs.addTab(appearance, "Utseende")
        app_layout = QtWidgets.QFormLayout(appearance)

        # Theme combo
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["light", "dark", "high-contrast"])
        try:
            self.theme_combo.setCurrentText(settings.get().get("theme", "light"))
        except (AttributeError, TypeError, KeyError):
            self.theme_combo.setCurrentText("light")
        app_layout.addRow("Tema:", self.theme_combo)

        # RGB sliders
        rgb_group = QtWidgets.QWidget()
        rgb_layout = QtWidgets.QHBoxLayout(rgb_group)
        self.sliders = {}
        for comp in ("r", "g", "b"):
            v = QtWidgets.QVBoxLayout()
            lbl = QtWidgets.QLabel(comp.upper())
            s = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
            s.setRange(0, 255)
            s.setTickInterval(16)
            s.setTickPosition(QtWidgets.QSlider.TickPosition.TicksRight)
            try:
                s.setValue(settings.get().get("rgb", {}).get(comp, 128))
            except (AttributeError, TypeError, KeyError, ValueError):
                s.setValue(128)
            v.addWidget(lbl)
            v.addWidget(s)
            rgb_layout.addLayout(v)
            self.sliders[comp] = s
        app_layout.addRow("Fargejustering (RGB):", rgb_group)

        # Button style
        self.btn_style = QtWidgets.QComboBox()
        self.btn_style.addItems(["filled", "outlined", "flat"])
        try:
            self.btn_style.setCurrentText(settings.get().get("button_style", "filled"))
        except (AttributeError, TypeError, KeyError):
            self.btn_style.setCurrentText("filled")
        app_layout.addRow("Knappestil:", self.btn_style)

        # Background chooser
        bg_widget = QtWidgets.QWidget()
        bg_h = QtWidgets.QHBoxLayout(bg_widget)
        self.bg_path_edit = QtWidgets.QLineEdit()
        self.bg_path_edit.setReadOnly(True)
        self.bg_choose = QtWidgets.QPushButton("Velg bilde...")
        bg_h.addWidget(self.bg_path_edit)
        bg_h.addWidget(self.bg_choose)
        app_layout.addRow("Bakgrunn:", bg_widget)

        # Background mode (fill/fit/center/stretch)
        self.bg_mode = QtWidgets.QComboBox()
        self.bg_mode.addItems(["fill", "fit", "center", "stretch"])
        # Set from settings if present
        try:
            self.bg_mode.setCurrentText(
                settings.get().get("background", {}).get("mode", "fill")
            )
        except (AttributeError, TypeError, KeyError):
            self.bg_mode.setCurrentText("fill")
        app_layout.addRow("Bakgrunnsmodus:", self.bg_mode)

        # Units tab
        units = QtWidgets.QWidget()
        tabs.addTab(units, "Enheter")
        u_layout = QtWidgets.QFormLayout(units)
        self.unit_global = QtWidgets.QComboBox()
        self.unit_global.addItems(["metric", "imperial"])
        try:
            self.unit_global.setCurrentText(
                settings.get().get("units", {}).get("global", "metric")
            )
        except (AttributeError, TypeError, KeyError):
            self.unit_global.setCurrentText("metric")
        u_layout.addRow("Globalt system:", self.unit_global)

        # Buttons
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(btns)

        # Preview area
        preview_group = QtWidgets.QGroupBox("Forhåndsvisning")
        preview_layout = QtWidgets.QHBoxLayout(preview_group)
        self.preview_label = QtWidgets.QLabel("Dette er en forhåndsvisning")
        self.preview_btn = QtWidgets.QPushButton("Eksempel")
        preview_layout.addWidget(self.preview_label)
        preview_layout.addStretch(1)
        preview_layout.addWidget(self.preview_btn)
        layout.addWidget(preview_group)

        # Connections
        self.bg_choose.clicked.connect(self._choose_background)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        for s in self.sliders.values():
            s.valueChanged.connect(self._on_rgb_change)
        self.theme_combo.currentTextChanged.connect(self._on_theme_change)
        self.bg_mode.currentTextChanged.connect(self._apply_preview)

        # Initialize preview style
        try:
            self._apply_preview()
        except Exception as e:
            # Log the preview failure and record in safe logger. Provide a
            # minimal fallback UI so the user can continue using the app.
            try:
                if _logger:
                    _logger.exception(
                        "Failed initial preview application in SettingsDialog: %s", e
                    )
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass
            try:
                safe_logger.append_exception("SettingsDialog.__init__ failed", e)
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass
            # Build a minimal error dialog UI so dialog remains usable
            try:
                try:
                    super().__init__(parent)
                except Exception as _suppressed_exc:
                    try:
                        _mod_logger = globals().get('_logger') or globals().get('logger')
                        if _mod_logger:
                            _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                    except Exception:
                        pass
                    try:
                        _append = globals().get('append_exception')
                        if _append:
                            _append("settings_dialog.py suppressed exception", _suppressed_exc)
                        else:
                            _safe = globals().get('safe_logger')
                            if _safe:
                                try:
                                    _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                                except Exception:
                                    pass
                            else:
                                try:
                                    import sys
                                    sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                                except Exception:
                                    pass
                    except Exception:
                        try:
                            import sys
                            sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                        except Exception:
                            pass
                    pass
                self.setWindowTitle("Innstillinger — Feil")
                self.resize(400, 120)
                err_layout = QtWidgets.QVBoxLayout(self)
                lbl = QtWidgets.QLabel(
                    "En feil oppstod ved åpning av innstillinger. Se debug_err.log for detaljer."
                )
                err_layout.addWidget(lbl)
                btn = QtWidgets.QPushButton("Lukk")
                btn.clicked.connect(self.reject)
                err_layout.addWidget(btn)
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                # If even fallback UI fails, swallow to avoid crashing the app
                pass

    def _safe_log_exception(self, msg: str = "", exc: Exception | None = None) -> None:
        try:
            if _logger:
                if exc:
                    try:
                        _logger.exception(msg or "Exception in SettingsDialog")
                    except Exception as _suppressed_exc:
                        try:
                            _mod_logger = globals().get('_logger') or globals().get('logger')
                            if _mod_logger:
                                _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                        except Exception:
                            pass
                        try:
                            _append = globals().get('append_exception')
                            if _append:
                                _append("settings_dialog.py suppressed exception", _suppressed_exc)
                            else:
                                _safe = globals().get('safe_logger')
                                if _safe:
                                    try:
                                        _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                                    except Exception:
                                        pass
                                else:
                                    try:
                                        import sys
                                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                                    except Exception:
                                        pass
                        except Exception:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                        pass
                else:
                    try:
                        _logger.error(msg)
                    except Exception as _suppressed_exc:
                        try:
                            _mod_logger = globals().get('_logger') or globals().get('logger')
                            if _mod_logger:
                                _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                        except Exception:
                            pass
                        try:
                            _append = globals().get('append_exception')
                            if _append:
                                _append("settings_dialog.py suppressed exception", _suppressed_exc)
                            else:
                                _safe = globals().get('safe_logger')
                                if _safe:
                                    try:
                                        _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                                    except Exception:
                                        pass
                                else:
                                    try:
                                        import sys
                                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                                    except Exception:
                                        pass
                        except Exception:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                        pass
            # Use the centralized safe_logger to append to per-user debug file
            try:
                safe_logger.append_exception(msg or "SettingsDialog exception", exc)
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass
        except Exception as _suppressed_exc:
            try:
                _mod_logger = globals().get('_logger') or globals().get('logger')
                if _mod_logger:
                    _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
            except Exception:
                pass
            try:
                _append = globals().get('append_exception')
                if _append:
                    _append("settings_dialog.py suppressed exception", _suppressed_exc)
                else:
                    _safe = globals().get('safe_logger')
                    if _safe:
                        try:
                            _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                        except Exception:
                            pass
                    else:
                        try:
                            import sys
                            sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                        except Exception:
                            pass
            except Exception:
                try:
                    import sys
                    sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                except Exception:
                    pass
            # Intentionally swallow all errors during logging
            pass

    def _load_logo(self) -> None:
        # Try to load a logo from the provided Logo path; if it's a directory, pick a PNG/JPG inside.
        try:
            p = DEFAULT_LOGO_PATH
            pix = None
            if p.exists():
                if p.is_file():
                    pix = QtGui.QPixmap(str(p))
                else:
                    for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg"):
                        found = list(p.glob(ext))
                        if found:
                            pix = QtGui.QPixmap(str(found[0]))
                            break
            if pix and not pix.isNull():
                self.logo_label.setPixmap(
                    pix.scaledToHeight(
                        96, QtCore.Qt.TransformationMode.SmoothTransformation
                    )
                )
            else:
                self.logo_label.setText("HJEMMELADING")
        except (OSError, RuntimeError, TypeError):
            try:
                if _logger:
                    _logger.exception("Failed to load settings dialog logo")
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass
            try:
                self.logo_label.setText("HJEMMELADING")
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass

    def _choose_background(self) -> None:
        try:
            fn, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Velg bakgrunnsbilde",
                str(Path.home()),
                "Images (*.png *.jpg *.jpeg *.bmp)",
            )
            if fn:
                self.bg_path_edit.setText(fn)
        except (OSError, RuntimeError):
            try:
                if _logger:
                    _logger.exception("Failed during background selection dialog")
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass

    def _on_rgb_change(self) -> None:
        self._apply_preview()

    def _on_theme_change(self) -> None:
        self._apply_preview()

    def _apply_preview(self) -> None:
        r = self.sliders["r"].value()
        g = self.sliders["g"].value()
        b = self.sliders["b"].value()
        btn_style = self.btn_style.currentText()
        # Theme presets
        theme = self.theme_combo.currentText()
        base_color = QtGui.QColor(r, g, b)
        # Determine colors depending on theme and build a stylesheet so the
        # entire dialog and surrounding widgets look consistent. Palette-only
        # changes sometimes leave parts using the platform style, causing
        # mismatched light/dark areas.
        if theme == "light":
            window_color = base_color.lighter(180)
            text_color = QtGui.QColor(20, 20, 20)
        elif theme == "dark":
            # Make a properly dark window background and light text
            window_color = (
                QtGui.QColor(28, 28, 30) if r + g + b < 200 else base_color.darker(180)
            )
            text_color = QtGui.QColor(235, 235, 235)
        else:  # high-contrast
            window_color = QtGui.QColor(0, 0, 0)
            text_color = QtGui.QColor(255, 255, 0)

        # Build a dialog-level stylesheet for consistent contrast
        win_hex = window_color.name()
        text_hex = text_color.name()
        btn_hex = base_color.name()

        # Precompute repeated QColor names to avoid very long lines
        lineedit_bg = QtGui.QColor(window_color).darker(110).name()
        lineedit_border = QtGui.QColor(window_color).lighter(120).name()
        combobox_bg = QtGui.QColor(window_color).darker(110).name()

        dialog_parts = [
            f"QWidget{{ background-color: {win_hex}; color: {text_hex}; }}",
            f"QGroupBox{{ background-color: transparent; color: {text_hex}; border: none; }}",
            f"QLabel{{ color: {text_hex}; }}",
            (
                f"QLineEdit{{ background-color: {lineedit_bg}; color: {text_hex}; "
                f"border: 1px solid {lineedit_border}; padding:4px; }}"
            ),
            f"QComboBox{{ background-color: {combobox_bg}; color: {text_hex}; }}",
            f"QTabWidget::pane {{ background: {win_hex}; }}",
        ]

        dialog_css = "\n".join(dialog_parts) + "\n"

        # Button styles adjusted by chosen button style
        if btn_style == "filled":
            btn_css = (
                f"background-color: {btn_hex}; color: {text_hex}; "
                "padding:6px 12px; border-radius:6px;"
            )
        elif btn_style == "outlined":
            btn_css = (
                f"background-color: transparent; color: {text_hex}; "
                f"border: 2px solid {btn_hex}; padding:4px 10px; border-radius:6px;"
            )
        else:  # flat
            btn_css = (
                f"background-color: transparent; color: {text_hex}; "
                "border: none; padding:4px 10px;"
            )

        # Apply built styles
        dialog_css += f"\nQPushButton{{ {btn_css} }}\n"
        self.setStyleSheet(dialog_css)
        # Ensure preview has explicit styles as well
        self.preview_btn.setStyleSheet(btn_css)
        self.preview_label.setStyleSheet(f"color: {text_hex}; background: transparent;")

        # If a custom background path was chosen, try to show it in preview
        try:
            cur_bg = self.bg_path_edit.text()
            if cur_bg:
                self._update_bg_preview(cur_bg, self.bg_mode.currentText())
        except (OSError, RuntimeError, AttributeError):
            try:
                if _logger:
                    _logger.exception("Error updating background preview")
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass

    def _on_save(self) -> None:
        cfg = settings.get()
        cfg["theme"] = self.theme_combo.currentText()
        cfg["rgb"] = {k: v.value() for k, v in self.sliders.items()}
        cfg["button_style"] = self.btn_style.currentText()
        bg_path = self.bg_path_edit.text() or None
        if bg_path:
            try:
                saved = backgrounds.save_background(bg_path)
            except ValueError as e:
                QtWidgets.QMessageBox.warning(
                    self, "Ugyldig bakgrunn", f"Kan ikke bruke valgt bilde: {e}"
                )
                return
            except OSError as e:
                QtWidgets.QMessageBox.critical(
                    self, "Feil ved lagring", f"Kunne ikke lagre bakgrunn: {e}"
                )
                if _logger:
                    _logger.exception("Failed to save background")
                return
            mode = self.bg_mode.currentText()
            cfg["background"] = {"type": "custom", "path": saved, "mode": mode}
        else:
            cfg["background"] = {"type": "default", "path": None, "mode": "fill"}
        try:
            cfg.setdefault("units", {})["global"] = self.unit_global.currentText()
            try:
                settings.import_config(cfg)
            except (ValueError, TypeError):
                try:
                    if _logger:
                        _logger.exception(
                            "Failed to import config in SettingsDialog._on_save"
                        )
                except Exception as _suppressed_exc:
                    try:
                        _mod_logger = globals().get('_logger') or globals().get('logger')
                        if _mod_logger:
                            _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                    except Exception:
                        pass
                    try:
                        _append = globals().get('append_exception')
                        if _append:
                            _append("settings_dialog.py suppressed exception", _suppressed_exc)
                        else:
                            _safe = globals().get('safe_logger')
                            if _safe:
                                try:
                                    _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                                except Exception:
                                    pass
                            else:
                                try:
                                    import sys
                                    sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                                except Exception:
                                    pass
                    except Exception:
                        try:
                            import sys
                            sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                        except Exception:
                            pass
                    pass
            try:
                settings.save()
            except OSError:
                try:
                    if _logger:
                        _logger.exception(
                            "Failed to save settings in SettingsDialog._on_save"
                        )
                except Exception as _suppressed_exc:
                    try:
                        _mod_logger = globals().get('_logger') or globals().get('logger')
                        if _mod_logger:
                            _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                    except Exception:
                        pass
                    try:
                        _append = globals().get('append_exception')
                        if _append:
                            _append("settings_dialog.py suppressed exception", _suppressed_exc)
                        else:
                            _safe = globals().get('safe_logger')
                            if _safe:
                                try:
                                    _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                                except Exception:
                                    pass
                            else:
                                try:
                                    import sys
                                    sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                                except Exception:
                                    pass
                    except Exception:
                        try:
                            import sys
                            sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                        except Exception:
                            pass
                    pass
            self.accept()
        except Exception as e:
            # Last-resort: log and notify user but don't crash app
            try:
                self._safe_log_exception(
                    "Unhandled error during SettingsDialog save", e
                )
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass
            try:
                QtWidgets.QMessageBox.critical(
                    self, "Feil", f"Kunne ikke lagre innstillinger: {e}"
                )
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass

    def _update_bg_preview(self, path: str, mode: str) -> None:
        """Load image from path and set it on the preview label using the chosen mode."""
        try:
            pix = QtGui.QPixmap(path)
            if pix.isNull():
                # invalid image, just leave text
                return
            w = self.preview_label.width() or 200
            h = self.preview_label.height() or 120
            if mode == "fill":
                scaled = pix.scaled(
                    w,
                    h,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            elif mode == "fit":
                scaled = pix.scaled(
                    w,
                    h,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            elif mode == "stretch":
                scaled = pix.scaled(
                    w,
                    h,
                    QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            else:  # center
                scaled = pix.scaled(
                    w,
                    h,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            self.preview_label.setPixmap(scaled)
        except Exception as _suppressed_exc:
            try:
                _mod_logger = globals().get('_logger') or globals().get('logger')
                if _mod_logger:
                    _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
            except Exception:
                pass
            try:
                _append = globals().get('append_exception')
                if _append:
                    _append("settings_dialog.py suppressed exception", _suppressed_exc)
                else:
                    _safe = globals().get('safe_logger')
                    if _safe:
                        try:
                            _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                        except Exception:
                            pass
                    else:
                        try:
                            import sys
                            sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                        except Exception:
                            pass
            except Exception:
                try:
                    import sys
                    sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                except Exception:
                    pass
            # on preview failure, log and continue
            try:
                if _logger:
                    _logger.exception("Preview image update failed for %s", path)
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in settings_dialog.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("settings_dialog.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("settings_dialog.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"settings_dialog.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
                pass


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    dlg = SettingsDialog()
    dlg.show()
    sys.exit(app.exec())
