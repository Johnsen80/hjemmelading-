"""Simple validation utilities for hjemmelading profile data.

This provides a minimal schema check to avoid persisting clearly invalid
profile data. It's intentionally lightweight (no external deps) so it can
run in tests and on user machines without extra installs.
"""

from __future__ import annotations

from typing import Any, Dict

ALLOWED_THEMES = {
    "Standard",
    "Lys",
    "Mørk",
    "Fargerik",
    "light",
    "dark",
    "high-contrast",
}


def validate_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a profile dictionary.

    Returns a cleaned profile dict or raises ValueError on invalid input.
    """
    if not isinstance(data, dict):
        raise ValueError("Profile must be a dict")

    cleaned: Dict[str, Any] = {}

    # username
    username = data.get("username", "")
    if username is None:
        username = ""
    if not isinstance(username, str):
        # try to coerce
        username = str(username)
    cleaned["username"] = username

    # theme
    theme = data.get("theme", "Standard")
    if not isinstance(theme, str):
        theme = str(theme)
    if theme not in ALLOWED_THEMES:
        # allow case-insensitive mapping from 'light'/'dark' to known values
        t_lower = theme.lower()
        if t_lower == "light":
            theme = "light"
        elif t_lower == "dark":
            theme = "dark"
        else:
            raise ValueError(f"Unsupported theme: {theme}")
    cleaned["theme"] = theme

    # background (allow empty string or str)
    bg = data.get("background", "")
    if bg is None:
        bg = ""
    if not isinstance(bg, str):
        bg = str(bg)
    cleaned["background"] = bg

    # button_style
    btn = data.get("button_style", "Standard")
    if btn is None:
        btn = "Standard"
    if not isinstance(btn, str):
        btn = str(btn)
    cleaned["button_style"] = btn

    # other_settings: must be a dict if present
    other = data.get("other_settings", {})
    if other is None:
        other = {}
    if not isinstance(other, dict):
        raise ValueError("other_settings must be a mapping/dict")
    cleaned["other_settings"] = other

    # Preserve any additional keys but ensure serializable values
    for k, v in data.items():
        if k in cleaned:
            continue
        # only include simple serializable values (str, int, float, bool, dict, list)
        if isinstance(v, (str, int, float, bool, dict, list, type(None))):
            cleaned[k] = v

    return cleaned
