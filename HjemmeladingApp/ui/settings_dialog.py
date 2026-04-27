from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..i18n import get_language, set_language, translate
from ..settings import settings
from ..utils import backgrounds, safe_logger
from ..utils.qt_compat import QSettings, QtCore, QtGui, QtWidgets

_HAS_QT = all(part is not None for part in (QtCore, QtGui, QtWidgets))


DEFAULT_LOGO_PATH = Path(
    r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\Logo"
)


if TYPE_CHECKING:

    class SettingsDialog(QtWidgets.QDialog):
        pass

elif _HAS_QT:

    class SettingsDialog(QtWidgets.QDialog):
        def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
            super().__init__(parent)
            self._bg_changed = False
            self._default_preview_text = ""
            self._build_ui()
            self._load_logo()
            self._load_config_into_widgets()
            self._wire_signals()
            self._refresh_language_status()
            self._apply_preview()

        def _build_ui(self) -> None:

            self.setWindowTitle(f"{translate('Settings')} - Hjemmelading")
            self.resize(680, 520)
            try:
                from src.ui.theme import apply_modern_theme

                apply_modern_theme(self)
            except Exception:
                pass

            layout = QtWidgets.QVBoxLayout(self)

            self.logo_label = QtWidgets.QLabel()
            self.logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.logo_label.setMinimumHeight(72)
            layout.addWidget(self.logo_label)

            self.tabs = QtWidgets.QTabWidget()
            layout.addWidget(self.tabs, 1)

            appearance = QtWidgets.QWidget()
            self.tabs.addTab(appearance, translate("Theme"))
            appearance_layout = QtWidgets.QFormLayout(appearance)

            self.theme_combo = QtWidgets.QComboBox()
            self._populate_combo(
                self.theme_combo,
                [
                    ("light", "Theme Light"),
                    ("dark", "Theme Dark"),
                    ("high-contrast", "Theme High Contrast"),
                ],
            )
            appearance_layout.addRow(f"{translate('Theme')}:", self.theme_combo)

            self.btn_style = QtWidgets.QComboBox()
            self._populate_combo(
                self.btn_style,
                [
                    ("filled", "Button Style Filled"),
                    ("outlined", "Button Style Outlined"),
                    ("flat", "Button Style Flat"),
                ],
            )
            appearance_layout.addRow(f"{translate('Button Style')}:", self.btn_style)

            self.bg_mode = QtWidgets.QComboBox()
            self._populate_combo(
                self.bg_mode,
                [
                    ("fill", "Background Mode Fill"),
                    ("fit", "Background Mode Fit"),
                    ("center", "Background Mode Center"),
                    ("stretch", "Background Mode Stretch"),
                ],
            )
            appearance_layout.addRow(f"{translate('Background')} mode:", self.bg_mode)

            bg_widget = QtWidgets.QWidget()
            bg_layout = QtWidgets.QHBoxLayout(bg_widget)
            bg_layout.setContentsMargins(0, 0, 0, 0)
            self.bg_path_edit = QtWidgets.QLineEdit()
            self.bg_path_edit.setReadOnly(True)
            self.bg_choose = QtWidgets.QPushButton(translate("Choose Image"))
            self.bg_clear = QtWidgets.QPushButton(translate("Clear"))
            bg_layout.addWidget(self.bg_path_edit, 1)
            bg_layout.addWidget(self.bg_choose)
            bg_layout.addWidget(self.bg_clear)
            appearance_layout.addRow(f"{translate('Background')}:", bg_widget)

            rgb_widget = QtWidgets.QWidget()
            rgb_layout = QtWidgets.QHBoxLayout(rgb_widget)
            rgb_layout.setContentsMargins(0, 0, 0, 0)
            self.sliders: dict[str, QtWidgets.QSlider] = {}
            for comp in ("r", "g", "b"):
                column = QtWidgets.QVBoxLayout()
                label = QtWidgets.QLabel(comp.upper())
                slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
                slider.setRange(0, 255)
                slider.setValue(128)
                column.addWidget(label)
                column.addWidget(slider)
                rgb_layout.addLayout(column)
                self.sliders[comp] = slider
            appearance_layout.addRow(
                f"{translate('Color Adjustment')} (RGB):", rgb_widget
            )

            units = QtWidgets.QWidget()
            self.tabs.addTab(units, translate("Units"))
            units_layout = QtWidgets.QFormLayout(units)
            self.unit_global = QtWidgets.QComboBox()
            self._populate_combo(
                self.unit_global,
                [
                    ("metric", "Metric"),
                    ("imperial", "Imperial"),
                ],
            )
            units_layout.addRow(f"{translate('Global System')}:", self.unit_global)

            general = QtWidgets.QWidget()
            self.tabs.addTab(general, translate("Language"))
            general_layout = QtWidgets.QFormLayout(general)
            self.lang_combo = QtWidgets.QComboBox()
            self._populate_combo(
                self.lang_combo,
                [
                    ("no", "Norwegian"),
                    ("en", "English"),
                ],
            )
            general_layout.addRow(f"{translate('Language')}:", self.lang_combo)

            self.lang_status = QtWidgets.QLabel("")
            self.lang_status.setWordWrap(True)
            general_layout.addRow(f"{translate('I18n Status')}:", self.lang_status)

            preview_group = QtWidgets.QGroupBox(translate("Preview"))
            preview_layout = QtWidgets.QVBoxLayout(preview_group)
            self.preview_label = QtWidgets.QLabel()
            self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setMinimumHeight(140)
            self.preview_btn = QtWidgets.QPushButton(translate("Example"))
            preview_layout.addWidget(self.preview_label)
            preview_layout.addWidget(self.preview_btn, 0)
            self._default_preview_text = translate("Preview")
            layout.addWidget(preview_group)

            self.buttons = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.StandardButton.Save
                | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            )
            layout.addWidget(self.buttons)

        def _populate_combo(
            self,
            combo: QtWidgets.QComboBox,
            items: list[tuple[str, str]],
        ) -> None:
            combo.clear()
            for value, label_key in items:
                combo.addItem(translate(label_key), value)

        def _set_combo_by_data(
            self, combo: QtWidgets.QComboBox, value: str, fallback: str
        ) -> None:
            index = combo.findData(value)
            if index < 0:
                index = combo.findData(fallback)
            combo.setCurrentIndex(max(index, 0))

        def _wire_signals(self) -> None:
            self.bg_choose.clicked.connect(self._choose_background)
            self.bg_clear.clicked.connect(self._clear_background_selection)
            self.theme_combo.currentTextChanged.connect(self._on_theme_change)
            self.bg_mode.currentTextChanged.connect(self._apply_preview)
            self.btn_style.currentTextChanged.connect(self._apply_preview)
            self.lang_combo.currentTextChanged.connect(self._on_language_change)
            self.unit_global.currentTextChanged.connect(self._on_unit_change)
            self.buttons.accepted.connect(self._on_save)
            self.buttons.rejected.connect(self.reject)
            for slider in self.sliders.values():
                slider.valueChanged.connect(self._on_rgb_change)

        def _safe_log_exception(
            self, msg: str = "", exc: Exception | None = None
        ) -> None:
            try:
                safe_logger.append_exception(msg or "SettingsDialog error", exc)
            except Exception:
                pass

        def _load_logo(self) -> None:
            try:
                if not DEFAULT_LOGO_PATH.exists():
                    self.logo_label.setText("Hjemmelading")
                    return
                for candidate in (
                    DEFAULT_LOGO_PATH / "logo.png",
                    DEFAULT_LOGO_PATH / "hjemmelading_logo.png",
                    DEFAULT_LOGO_PATH / "logo.svg",
                ):
                    if not candidate.exists():
                        continue
                    pixmap = QtGui.QPixmap(str(candidate))
                    if pixmap and not pixmap.isNull():
                        self.logo_label.setPixmap(
                            pixmap.scaledToHeight(
                                72, QtCore.Qt.TransformationMode.SmoothTransformation
                            )
                        )
                        return
                self.logo_label.setText("Hjemmelading")
            except Exception as exc:
                self._safe_log_exception("Failed to load settings logo", exc)
                self.logo_label.setText("Hjemmelading")

        def _choose_background(self) -> None:
            try:
                path, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self,
                    translate("Background"),
                    "",
                    translate("Images Filter Extended"),
                )
            except Exception as exc:
                self._safe_log_exception("Background picker failed", exc)
                return

            if path:
                self._set_background_path(path, mark_changed=True)

        def _load_config_into_widgets(self) -> None:
            cfg = settings.get()
            theme = str(cfg.get("theme", "light"))
            button_style = str(cfg.get("button_style", "filled"))
            rgb = cfg.get("rgb", {}) if isinstance(cfg.get("rgb"), dict) else {}
            background = (
                cfg.get("background", {})
                if isinstance(cfg.get("background"), dict)
                else {}
            )
            units = cfg.get("units", {}) if isinstance(cfg.get("units"), dict) else {}

            self._set_combo_by_data(self.theme_combo, theme, "light")
            self._set_combo_by_data(self.btn_style, button_style, "filled")
            self._set_combo_by_data(
                self.bg_mode, str(background.get("mode", "fill")), "fill"
            )
            self._set_combo_by_data(
                self.unit_global, str(units.get("global", "metric")), "metric"
            )

            for comp, slider in self.sliders.items():
                try:
                    slider.setValue(int(rgb.get(comp, 128)))
                except Exception:
                    slider.setValue(128)

            self._set_background_path(background.get("path"), mark_changed=False)

            lang_code = "no"
            if QSettings is not None:
                try:
                    qs = QSettings("ReloadingWorkshop", "ReloadingManager")
                    lang_code = str(qs.value("language", "no"))
                except Exception:
                    lang_code = "no"
            self._set_combo_by_data(
                self.lang_combo,
                lang_code if lang_code in ("no", "en") else "no",
                "no",
            )

        def _set_background_path(
            self, path: Optional[str], *, mark_changed: bool
        ) -> None:
            normalized = str(path) if path else ""
            self.bg_path_edit.setText(normalized)
            self.bg_clear.setEnabled(bool(normalized))
            if mark_changed:
                self._bg_changed = True
            self._apply_preview()

        def _clear_background_selection(self) -> None:
            self._set_background_path(None, mark_changed=True)

        def _reset_preview_label(self) -> None:
            self.preview_label.clear()
            self.preview_label.setText(self._default_preview_text)

        def _on_rgb_change(self) -> None:
            self._apply_preview()

        def _on_theme_change(self) -> None:
            self._apply_preview()

        def _apply_preview(self) -> None:
            rgb = {name: slider.value() for name, slider in self.sliders.items()}
            accent = f"rgb({rgb['r']}, {rgb['g']}, {rgb['b']})"
            is_dark = self.theme_combo.currentData() == "dark"
            bg_color = "#101317" if is_dark else "#f6f4f0"
            text_color = "#f2f4f8" if is_dark else "#0b1320"
            border = "#364152" if is_dark else "#d6d2cb"

            self.preview_btn.setStyleSheet(
                f"QPushButton {{ background-color: {accent}; color: {text_color}; "
                f"border: 1px solid {border}; border-radius: 6px; padding: 8px 12px; }}"
            )
            self.preview_label.setStyleSheet(
                f"QLabel {{ background-color: {bg_color}; color: {text_color}; "
                f"border: 1px solid {border}; border-radius: 8px; padding: 12px; }}"
            )

            path = self.bg_path_edit.text().strip()
            if path:
                self._update_bg_preview(path, str(self.bg_mode.currentData() or "fill"))
            else:
                self._reset_preview_label()

        def _on_language_change(self, _text: str) -> None:
            lang_code = str(self.lang_combo.currentData() or "no")
            try:
                set_language(lang_code)
                self._retranslate_dynamic_options()
                self._refresh_language_status()
            except Exception as exc:
                self._safe_log_exception("Failed to change language", exc)

        def _on_unit_change(self, _text: str) -> None:
            self._apply_preview()

        def _on_save(self) -> None:
            try:
                rgb = {name: slider.value() for name, slider in self.sliders.items()}
                settings.set_theme(str(self.theme_combo.currentData() or "light"), rgb)
                settings.set_button_style(str(self.btn_style.currentData() or "filled"))
                settings.set_unit(
                    "global", str(self.unit_global.currentData() or "metric")
                )

                background_path = self.bg_path_edit.text().strip()
                background_type = "custom" if background_path else "default"
                stored_path = None
                if background_path:
                    if self._bg_changed:
                        stored_path = backgrounds.save_background(background_path)
                    else:
                        stored_path = background_path
                settings.set_background(
                    {
                        "type": background_type,
                        "path": stored_path,
                        "mode": str(self.bg_mode.currentData() or "fill"),
                    }
                )

                lang_code = str(self.lang_combo.currentData() or "no")
                if QSettings is not None:
                    try:
                        qs = QSettings("ReloadingWorkshop", "ReloadingManager")
                        qs.setValue("language", lang_code)
                    except Exception:
                        pass
                set_language(lang_code)
                self._refresh_language_status()
                settings.save()
                self.accept()
            except Exception as exc:
                self._safe_log_exception("Failed to save settings", exc)
                QtWidgets.QMessageBox.warning(
                    self,
                    translate("Settings"),
                    translate("Settings Save Error"),
                )

        def _refresh_language_status(self) -> None:
            try:
                from src.utils.i18n import get_missing_translation_report

                current_lang = get_language()
                missing = get_missing_translation_report(current_lang)
                if missing:
                    preview = ", ".join(missing[:3])
                    extra = ""
                    if len(missing) > 3:
                        extra = f" (+{len(missing) - 3} {translate('And More')})"
                    self.lang_status.setText(
                        f"{translate('Missing Keys For')} '{current_lang}': {preview}{extra}"
                    )
                    self.lang_status.setStyleSheet("color: #92400e;")
                else:
                    self.lang_status.setText(
                        f"{translate('No Registered Missing Keys For')} '{current_lang}'."
                    )
                    self.lang_status.setStyleSheet("color: #166534;")
            except Exception as exc:
                self._safe_log_exception("Failed to refresh language status", exc)
                self.lang_status.setText(translate("Could Not Read I18n Status"))
                self.lang_status.setStyleSheet("color: #991b1b;")

        def _update_bg_preview(self, path: str, _mode: str) -> None:
            pixmap = backgrounds.get_background_preview(path)
            if pixmap is None:
                self.preview_label.setText(path)
                return
            self.preview_label.setPixmap(
                pixmap.scaled(
                    self.preview_label.size() or QtCore.QSize(320, 140),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            )

        def _retranslate_dynamic_options(self) -> None:
            theme = str(self.theme_combo.currentData() or "light")
            style = str(self.btn_style.currentData() or "filled")
            bg_mode = str(self.bg_mode.currentData() or "fill")
            units = str(self.unit_global.currentData() or "metric")
            lang = str(self.lang_combo.currentData() or "no")

            self._populate_combo(
                self.theme_combo,
                [
                    ("light", "Theme Light"),
                    ("dark", "Theme Dark"),
                    ("high-contrast", "Theme High Contrast"),
                ],
            )
            self._populate_combo(
                self.btn_style,
                [
                    ("filled", "Button Style Filled"),
                    ("outlined", "Button Style Outlined"),
                    ("flat", "Button Style Flat"),
                ],
            )
            self._populate_combo(
                self.bg_mode,
                [
                    ("fill", "Background Mode Fill"),
                    ("fit", "Background Mode Fit"),
                    ("center", "Background Mode Center"),
                    ("stretch", "Background Mode Stretch"),
                ],
            )
            self._populate_combo(
                self.unit_global,
                [
                    ("metric", "Metric"),
                    ("imperial", "Imperial"),
                ],
            )
            self._populate_combo(
                self.lang_combo,
                [
                    ("no", "Norwegian"),
                    ("en", "English"),
                ],
            )

            self._set_combo_by_data(self.theme_combo, theme, "light")
            self._set_combo_by_data(self.btn_style, style, "filled")
            self._set_combo_by_data(self.bg_mode, bg_mode, "fill")
            self._set_combo_by_data(self.unit_global, units, "metric")
            self._set_combo_by_data(self.lang_combo, lang, "no")

else:

    class SettingsDialog:  # pragma: no cover - used only when Qt is unavailable
        def __init__(self, *args, **kwargs):
            raise RuntimeError("A Qt binding is required to use SettingsDialog")

        def exec(self) -> int:
            raise RuntimeError("A Qt binding is required to use SettingsDialog")

        def exec_(self) -> int:
            raise RuntimeError("A Qt binding is required to use SettingsDialog")

        def show(self) -> None:
            raise RuntimeError("A Qt binding is required to use SettingsDialog")

        def close(self) -> None:
            raise RuntimeError("A Qt binding is required to use SettingsDialog")


if __name__ == "__main__" and _HAS_QT:
    import sys

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    dlg = SettingsDialog()
    dlg.show()
    raise SystemExit(app.exec())
