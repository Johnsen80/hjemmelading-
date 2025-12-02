import os
from typing import Dict, Any

from HjemmeladingApp.utils.safe_logger import append_exception

from modules.hjemmelading.storage import load_profile, save_profile
from modules.hjemmelading.validation import validate_profile


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
        self.load()

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
            try:
                append_exception(f"Failed to load profile from {PROFILE_PATH}", exc)
            except Exception:
                pass

    def save(self) -> None:
        try:
            save_profile(self.data, PROFILE_PATH)
        except OSError as exc:
            try:
                append_exception(f"Failed to save profile to {PROFILE_PATH}", exc)
            except Exception:
                pass

    def export(self, export_path: str) -> bool:
        try:
            save_profile(self.data, export_path)
            return True
        except OSError as exc:
            try:
                append_exception(f"Failed to export profile to {export_path}", exc)
            except Exception:
                pass
            return False

    def import_profile(self, import_path: str) -> bool:
        try:
            loaded = load_profile(import_path)
            if isinstance(loaded, dict):
                try:
                    cleaned = validate_profile(loaded)
                except ValueError as _val_err:
                    try:
                        append_exception(
                            f"Imported profile validation failed: {_val_err}", _val_err
                        )
                    except Exception:
                        pass
                    # expose validation message for UI
                    try:
                        self.last_error = str(_val_err)
                    except Exception:
                        pass
                    return False
                self.data = cleaned
                self.save()
                # clear any previous error
                try:
                    self.last_error = None
                except Exception:
                    pass
                return True
            return False
        except (ValueError, OSError) as exc:
            try:
                append_exception(f"Failed to import profile from {import_path}", exc)
            except Exception:
                pass
            try:
                self.last_error = str(exc)
            except Exception:
                pass
            return False
