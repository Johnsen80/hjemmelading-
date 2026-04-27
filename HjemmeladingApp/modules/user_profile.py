import os
from typing import Any, Dict, Optional

try:
    from .hjemmelading.storage import load_profile, save_profile
    from .hjemmelading.validation import validate_profile
except ImportError:
    # Fallback for legacy launch paths where package prefix differs
    from HjemmeladingApp.modules.hjemmelading.storage import load_profile, save_profile  # type: ignore[no-redef]
    from HjemmeladingApp.modules.hjemmelading.validation import validate_profile  # type: ignore[no-redef]

from ..utils import safe_logger

PROFILE_PATH = os.path.join(
    os.path.expanduser("~"), "HjemmeladingApp_user_profile.json"
)


class UserProfile:
    def __init__(self):
        self.data: Dict[str, Any] = {
            "username": "",
            "theme": "Standard",
            "background": "",
            "button_style": "Standard",
            "other_settings": {},
        }
        self.last_error: "Optional[str]" = None
        self.load()

    def _attempt_append(self, msg: str, exc: Exception) -> None:
        """Attempt to append an exception to the safe logger, with fallbacks.

        This consolidates the repeated nested try/except blocks used throughout
        this module for robust logging when the logging helpers themselves fail.
        """
        try:
            safe_logger.append_exception(msg, exc)
        except Exception as _s_exc:
            try:
                safe_logger.handle_suppressed(_s_exc, "modules/user_profile.py")
            except Exception:
                try:
                    import sys

                    sys.stderr.write(
                        f"user_profile.py suppressed exception: {_s_exc}\n"
                    )
                except Exception:
                    pass

    def load(self) -> None:
        try:
            # Delegate JSON loading to storage helper
            loaded = load_profile(PROFILE_PATH)
            if isinstance(loaded, dict):
                self.data = loaded
        except FileNotFoundError:
            # No profile yet; ignore
            pass
        except (ValueError, OSError) as exc:
            # Invalid JSON or I/O problems — record and log
            self._attempt_append(f"Failed to load profile from {PROFILE_PATH}", exc)

    def save(self) -> None:
        try:
            save_profile(self.data, PROFILE_PATH)
        except OSError as exc:
            self._attempt_append(f"Failed to save profile to {PROFILE_PATH}", exc)

    def export(self, export_path: str) -> bool:
        try:
            save_profile(self.data, export_path)
            return True
        except OSError as exc:
            self._attempt_append(f"Failed to export profile to {export_path}", exc)
            return False

    def import_profile(self, import_path: str) -> bool:
        try:
            loaded = load_profile(import_path)
            if isinstance(loaded, dict):
                try:
                    cleaned = validate_profile(loaded)
                except ValueError as _val_err:
                    self._attempt_append(
                        f"Imported profile validation failed: {_val_err}", _val_err
                    )
                    # expose validation message for UI
                    try:
                        self.last_error = str(_val_err)
                    except Exception as _suppressed_exc:
                        self._attempt_append(
                            "Failed to set last_error in import_profile",
                            _suppressed_exc,
                        )
                    return False
                self.data = cleaned
                self.save()
                # clear any previous error
                try:
                    self.last_error = None
                except Exception as _suppressed_exc:
                    self._attempt_append(
                        "Failed to clear last_error in import_profile",
                        _suppressed_exc,
                    )
                return True
            return False
        except (ValueError, OSError) as exc:
            self._attempt_append(f"Failed to import profile from {import_path}", exc)
            try:
                self.last_error = str(exc)
            except Exception as _suppressed_exc:
                self._attempt_append(
                    "user_profile.py suppressed exception while setting last_error",
                    _suppressed_exc,
                )
            return False
