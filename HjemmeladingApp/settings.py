from typing import Any, Callable, Dict, List, Optional
from . import config


class SettingsManager:
    """Backend manager for application settings.

    This is intentionally GUI-agnostic: GUI code should import this and
    register callbacks for live preview or update the application when
    settings change.
    """

    def __init__(self):
        self._cfg = config.load_config()
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []

    def get(self) -> Dict[str, Any]:
        return self._cfg

    def save(self) -> None:
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
            except Exception:
                # listeners should handle their own errors
                pass

    # Convenience setters/getters
    def set_theme(self, theme: str, rgb: Optional[Dict[str, int]] = None) -> None:
        self._cfg["theme"] = theme
        if rgb:
            self._cfg["rgb"] = rgb
        self._notify()

    def set_button_style(self, style: str) -> None:
        self._cfg["button_style"] = style
        self._notify()

    def set_background(self, bkg: Dict[str, Any]) -> None:
        # bkg: {type: 'custom'|'default', path: str|None, mode: 'fill'|'contain'|'center'}
        self._cfg["background"] = bkg
        self._notify()

    def set_unit(self, scope: str, unit: str) -> None:
        # scope == 'global' or module name
        if scope == "global":
            self._cfg.setdefault("units", {})["global"] = unit
        else:
            self._cfg.setdefault("units", {}).setdefault("modules", {})[scope] = unit
        self._notify()

    def export_config(self) -> Dict[str, Any]:
        return dict(self._cfg)

    def import_config(self, cfg: Dict[str, Any]) -> None:
        self._cfg = config.migrate_config(cfg)
        self.save()
        self._notify()


settings = SettingsManager()

if __name__ == "__main__":
    print("Loaded settings:")
    print(settings.get())
