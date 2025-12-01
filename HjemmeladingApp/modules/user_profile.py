import json
import os
from HjemmeladingApp.utils.safe_logger import append_exception

PROFILE_PATH = os.path.join(
    os.path.expanduser("~"), "HjemmeladingApp_user_profile.json"
)


class UserProfile:
    def __init__(self):
        self.data = {
            "username": "",
            "theme": "Standard",
            "background": "",
            "button_style": "Standard",
            "other_settings": {},
        }
        self.load()

    def load(self):
        if os.path.exists(PROFILE_PATH):
            try:
                with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as exc:
                try:
                    append_exception(f"Failed to load profile from {PROFILE_PATH}", exc)
                except Exception:
                    pass

    def save(self):
        try:
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as exc:
            try:
                append_exception(f"Failed to save profile to {PROFILE_PATH}", exc)
            except Exception:
                pass

    def export(self, export_path):
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as exc:
            try:
                append_exception(f"Failed to export profile to {export_path}", exc)
            except Exception:
                pass
            return False

    def import_profile(self, import_path):
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            self.save()
            return True
        except Exception as exc:
            try:
                append_exception(f"Failed to import profile from {import_path}", exc)
            except Exception:
                pass
            return False
