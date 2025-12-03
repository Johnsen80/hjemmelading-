import os
from typing import Dict, Any, Optional

from ..utils import safe_logger

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
        self.last_error: "Optional[str]" = None
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
                safe_logger.append_exception(f"Failed to load profile from {PROFILE_PATH}", exc)
            except Exception as _suppressed_exc:
                try:
                    safe_logger.handle_suppressed(_suppressed_exc, "modules/user_profile.py")
                except Exception:
                    try:
                        import sys

                        sys.stderr.write("user_profile.py suppressed exception: " + str(_suppressed_exc) + "\n")
                    except Exception:
                        pass

    def save(self) -> None:
        try:
            save_profile(self.data, PROFILE_PATH)
        except OSError as exc:
            try:
                safe_logger.append_exception(f"Failed to save profile to {PROFILE_PATH}", exc)
            except Exception as _suppressed_exc:
                try:
                    safe_logger.handle_suppressed(_suppressed_exc, "modules/user_profile.py")
                except Exception:
                    try:
                        import sys

                        sys.stderr.write("user_profile.py suppressed exception: " + str(_suppressed_exc) + "\n")
                    except Exception:
                        pass

    def export(self, export_path: str) -> bool:
        try:
            save_profile(self.data, export_path)
            return True
        except OSError as exc:
            try:
                safe_logger.append_exception(f"Failed to export profile to {export_path}", exc)
            except Exception as _suppressed_exc:
                try:
                    safe_logger.handle_suppressed(_suppressed_exc, "modules/user_profile.py")
                except Exception:
                    try:
                        import sys

                        sys.stderr.write("user_profile.py suppressed exception: " + str(_suppressed_exc) + "\n")
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
                        safe_logger.append_exception(f"Imported profile validation failed: {_val_err}", _val_err)
                    except Exception as _suppressed_exc:
                        try:
                            safe_logger.handle_suppressed(_suppressed_exc, "modules/user_profile.py")
                        except Exception:
                            try:
                                import sys

                                sys.stderr.write("user_profile.py suppressed exception: " + str(_suppressed_exc) + "\n")
                            except Exception:
                                pass
                    # expose validation message for UI
                    try:
                        self.last_error = str(_val_err)
                    except Exception as _suppressed_exc:
                        try:
                            safe_logger.handle_suppressed(_suppressed_exc, "modules/user_profile.py")
                        except Exception:
                            try:
                                import sys
                                sys.stderr.write("user_profile.py suppressed exception: " + str(_suppressed_exc) + "\n")
                            except Exception:
                                pass
                    return False
                self.data = cleaned
                self.save()
                # clear any previous error
                try:
                    self.last_error = None
                except Exception as _suppressed_exc:
                    try:
                        _mod_logger = globals().get('_logger') or globals().get('logger')
                        if _mod_logger:
                            _mod_logger.exception("Unhandled exception in user_profile.py: %s", _suppressed_exc)
                    except Exception:
                        pass
                    try:
                        _append = globals().get('append_exception')
                        if _append:
                            _append("user_profile.py suppressed exception", _suppressed_exc)
                        else:
                            _safe = globals().get('safe_logger')
                            if _safe:
                                try:
                                    _safe.append_exception("user_profile.py suppressed exception", _suppressed_exc)
                                except Exception:
                                    pass
                            else:
                                try:
                                    import sys
                                    sys.stderr.write(f"user_profile.py suppressed exception: {_suppressed_exc}\n")
                                except Exception:
                                    pass
                    except Exception:
                        try:
                            import sys
                            sys.stderr.write(f"user_profile.py suppressed exception: {_suppressed_exc}\n")
                        except Exception:
                            pass
                return True
            return False
        except (ValueError, OSError) as exc:
            try:
                safe_logger.append_exception(f"Failed to import profile from {import_path}", exc)
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in user_profile.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("user_profile.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("user_profile.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"user_profile.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"user_profile.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
            try:
                self.last_error = str(exc)
            except Exception as _suppressed_exc:
                try:
                    _mod_logger = globals().get('_logger') or globals().get('logger')
                    if _mod_logger:
                        _mod_logger.exception("Unhandled exception in user_profile.py: %s", _suppressed_exc)
                except Exception:
                    pass
                try:
                    _append = globals().get('append_exception')
                    if _append:
                        _append("user_profile.py suppressed exception", _suppressed_exc)
                    else:
                        _safe = globals().get('safe_logger')
                        if _safe:
                            try:
                                _safe.append_exception("user_profile.py suppressed exception", _suppressed_exc)
                            except Exception:
                                pass
                        else:
                            try:
                                import sys
                                sys.stderr.write(f"user_profile.py suppressed exception: {_suppressed_exc}\n")
                            except Exception:
                                pass
                except Exception:
                    try:
                        import sys
                        sys.stderr.write(f"user_profile.py suppressed exception: {_suppressed_exc}\n")
                    except Exception:
                        pass
            return False
