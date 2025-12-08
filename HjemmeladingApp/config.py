import json
import os
from pathlib import Path
from typing import Any, Dict

# Small alias to make configuration types explicit across the codebase
Config = Dict[str, Any]

APP_NAME = "Hjemmelading"


def get_config_dir() -> Path:
    """Return platform-appropriate config directory for the app."""
    local = (
        os.getenv("LOCALAPPDATA")
        or os.getenv("XDG_CONFIG_HOME")
        or str(Path.home() / ".config")
    )
    return Path(local) / APP_NAME


def ensure_config_dir() -> Path:
    p = get_config_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_config_path() -> Path:
    return ensure_config_dir() / "config.json"


def get_default_config() -> Config:
    return {
        "version": 1,
        "theme": "light",
        "rgb": {"r": 60, "g": 120, "b": 200},
        "button_style": "filled",
        "background": {"type": "default", "path": None, "mode": "fill"},
        "units": {"global": "metric", "modules": {}},
        "profiles": {"default": {}},
    }


def load_config() -> Config:
    p = get_config_path()
    if not p.exists():
        cfg = get_default_config()
        save_config(cfg)
        return cfg
    try:
        with p.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as _suppressed_exc:
        # If the config is corrupted, move it aside and recreate default
        bad = p.with_suffix(".broken.json")
        try:
            p.replace(bad)
        except Exception as _suppressed_exc:
            pass
        cfg = get_default_config()
        save_config(cfg)
        return cfg


def save_config(cfg: Config) -> None:
    p = get_config_path()
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    tmp.replace(p)


def migrate_config(cfg: Config) -> Config:
    # Placeholder for versioned migrations. For now, return cfg unchanged.
    return cfg


if __name__ == "__main__":
    print("Config dir:", get_config_dir())
    print("Config file:", get_config_path())
    cfg = load_config()
    print("Loaded config keys:", list(cfg.keys()))
