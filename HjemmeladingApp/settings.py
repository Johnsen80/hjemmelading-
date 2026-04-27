import json
from typing import Any, Callable, Dict, List, Optional

from . import config
from .utils.qt_compat import QSettings

# Re-export a clearer alias for config dictionaries used across the app
Config = config.Config


class SettingsManager:
    """Backend manager for application settings.

    This is intentionally GUI-agnostic: GUI code should import this and
    register callbacks for live preview or update the application when
    settings change.
    """

    def __init__(self):
        self._cfg: Config = config.load_config()
        self._listeners: List[Callable[[Config], None]] = []
        self._qs = None
        self._refresh_from_qsettings()
        self._write_qsettings()

    def _get_qsettings(self):
        if QSettings is None:
            return None
        if self._qs is None:
            self._qs = QSettings("ReloadingWorkshop", "ReloadingManager")
        return self._qs

    def _coerce_dict(self, value: Any) -> Dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return None
        return None

    def _refresh_from_qsettings(self) -> None:
        qs = self._get_qsettings()
        if not qs:
            return
        try:
            theme = qs.value("theme", None)
            if theme:
                self._cfg["theme"] = theme
            btn_style = qs.value("button_style", None)
            if btn_style:
                self._cfg["button_style"] = btn_style
            ui_mode = qs.value("ui/mode", qs.value("ui_mode", None))
            if ui_mode:
                self._cfg["ui_mode"] = ui_mode
            ui_density = qs.value("ui/density", qs.value("ui_density", None))
            if ui_density:
                self._cfg["ui_density"] = ui_density
            rgb = self._coerce_dict(qs.value("rgb", None))
            if rgb:
                self._cfg["rgb"] = rgb
            bg = self._coerce_dict(qs.value("background", None))
            if bg:
                self._cfg["background"] = bg
            units_global = qs.value("units/global", None)
            if units_global:
                self._cfg.setdefault("units", {})["global"] = units_global
        except Exception:
            # best-effort: ignore QSettings issues
            pass

    def _write_qsettings(self) -> None:
        qs = self._get_qsettings()
        if not qs:
            return
        try:
            qs.setValue("theme", self._cfg.get("theme"))
            qs.setValue("button_style", self._cfg.get("button_style"))
            qs.setValue("ui/mode", self._cfg.get("ui_mode"))
            qs.setValue("ui/density", self._cfg.get("ui_density"))
            rgb = self._cfg.get("rgb")
            if isinstance(rgb, dict):
                qs.setValue("rgb", rgb)
            bg = self._cfg.get("background")
            if isinstance(bg, dict):
                qs.setValue("background", bg)
            units = self._cfg.get("units", {})
            if isinstance(units, dict):
                qs.setValue("units/global", units.get("global"))
        except Exception:
            pass

    def get(self) -> Config:
        self._refresh_from_qsettings()
        return self._cfg

    def save(self) -> None:
        self._write_qsettings()
        config.save_config(self._cfg)

    def register_listener(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        if fn not in self._listeners:
            self._listeners.append(fn)

    def unregister_listener(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        if fn in self._listeners:
            self._listeners.remove(fn)

    def _notify(self) -> None:
        for fn in list(self._listeners):
            try:
                fn(self._cfg)
            except Exception as _suppressed_exc:
                # listeners should handle their own errors
                pass

    # Convenience setters/getters
    def set_theme(self, theme: str, rgb: Optional[Dict[str, int]] = None) -> None:
        self._cfg["theme"] = theme
        if rgb:
            self._cfg["rgb"] = rgb
        self._write_qsettings()
        self._notify()

    def set_button_style(self, style: str) -> None:
        self._cfg["button_style"] = style
        self._write_qsettings()
        self._notify()

    def set_ui_mode(self, mode: str) -> None:
        self._cfg["ui_mode"] = mode
        self._write_qsettings()
        self._notify()

    def set_ui_density(self, density: str) -> None:
        self._cfg["ui_density"] = density
        self._write_qsettings()
        self._notify()

    def set_background(self, bkg: Dict[str, Any]) -> None:
        # bkg: {type: 'custom'|'default', path: str|None, mode: 'fill'|'contain'|'center'}
        self._cfg["background"] = bkg
        self._write_qsettings()
        self._notify()

    def set_unit(self, scope: str, unit: str) -> None:
        # scope == 'global' or module name
        if scope == "global":
            self._cfg.setdefault("units", {})["global"] = unit
        else:
            self._cfg.setdefault("units", {}).setdefault("modules", {})[scope] = unit
        self._write_qsettings()
        self._notify()

    def export_config(self) -> Config:
        return dict(self._cfg)

    def import_config(self, cfg: Config) -> None:
        self._cfg = config.migrate_config(cfg)
        self.save()
        self._notify()


settings = SettingsManager()

if __name__ == "__main__":
    print("Loaded settings:")
    print(settings.get())
