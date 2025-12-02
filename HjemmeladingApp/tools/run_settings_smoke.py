# ruff: noqa
import os
import sys
import tempfile

# Headless smoke script: create invalid JSON, run import flow and report LAST_ERROR.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_temp_bad_json() -> str:
    tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    tf.write("{ this is not valid json }")
    tf.flush()
    tf.close()
    return tf.name


def main() -> int:
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"PyQt6 not available: {exc}")
        return 2

    test_path = _make_temp_bad_json()

    # Non-blocking dialogs
    try:
        QFileDialog.getOpenFileName = lambda *a, **k: (test_path, "")
    except Exception:
        pass

    try:
        QMessageBox.information = lambda *a, **k: None
        QMessageBox.warning = lambda *a, **k: None
        QMessageBox.exec = lambda *a, **k: None
    except Exception:
        pass

    # Ensure imports work from tools/ runner
    repo_parent = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if repo_parent not in sys.path:
        sys.path.insert(0, repo_parent)

    proj_dir = os.path.dirname(os.path.dirname(__file__))
    if proj_dir not in sys.path:
        sys.path.insert(0, proj_dir)

    try:
        from HjemmeladingApp.modules.user_profile import UserProfile

        up = UserProfile()
        up.import_profile(test_path)
        last_err = getattr(up, "last_error", None)
        if last_err:
            print("LAST_ERROR:", str(last_err))
            return 0
    except Exception as exc:
        print("CORE_IMPORT_EXCEPTION:", exc)

    # Drive UI path as fallback
    QApplication([])
    try:
        from HjemmeladingApp.ui.profile_editor import ProfileEditor

        pe = ProfileEditor()
        pe.import_profile()
        last_err = getattr(pe.profile, "last_error", None)
        if last_err:
            print("LAST_ERROR:", str(last_err))
            return 0
        else:
            print("NO_LAST_ERROR")
            return 1
    except Exception as exc:
        print("SMOKE_EXCEPTION:", exc)
        return 3
    finally:
        try:
            os.unlink(test_path)
        except Exception:
            pass


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
import os
import sys

# Run Qt in offscreen mode for headless smoke testing
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Ensure the repository parent directory is on sys.path so `import HjemmeladingApp` works
repo_parent = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if repo_parent not in sys.path:
    sys.path.insert(0, repo_parent)

# Also ensure the project directory itself is on sys.path so both
# `HjemmeladingApp.modules...` and bare `modules...` imports work.
proj_dir = os.path.dirname(os.path.dirname(__file__))
if proj_dir not in sys.path:
    sys.path.insert(0, proj_dir)


def main():
    try:
        from PyQt6.QtWidgets import QFileDialog
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"PyQt6 not available: {exc}")
        return 2

    # Create an invalid JSON profile file to force an import error
    tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    tf.write("{ this is not valid json }")
    tf.flush()
    tf.close()
    test_path = tf.name

    # Monkeypatch file dialogs and message boxes so the UI flow is non-blocking
    try:
        QFileDialog.getOpenFileName = lambda *a, **k: (test_path, "")
    except Exception:
        import os
        import sys
        import tempfile


        # Run Qt in offscreen mode for headless smoke testing
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


        def _make_temp_bad_json() -> str:
            tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
            tf.write("{ this is not valid json }")
            tf.flush()
            tf.close()
            return tf.name


        def main() -> int:
            try:
                from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog
            except Exception as exc:  # pragma: no cover - environment dependent
                print(f"PyQt6 not available: {exc}")
                return 2

            test_path = _make_temp_bad_json()

            # Monkeypatch file dialogs and message boxes so the UI flow is non-blocking
            try:
                QFileDialog.getOpenFileName = lambda *a, **k: (test_path, "")
            except Exception:
                pass

            try:
                QMessageBox.information = lambda *a, **k: None
                QMessageBox.warning = lambda *a, **k: None
                QMessageBox.exec = lambda *a, **k: None
            except Exception:
                pass

            # Ensure package/project import resolution works when running from tools/
            repo_parent = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if repo_parent not in sys.path:
                sys.path.insert(0, repo_parent)

            proj_dir = os.path.dirname(os.path.dirname(__file__))
            if proj_dir not in sys.path:
                sys.path.insert(0, proj_dir)

            # First, try the core import path
            try:
                from HjemmeladingApp.modules.user_profile import UserProfile

                up = UserProfile()
                up.import_profile(test_path)
                last_err = getattr(up, "last_error", None)
                if last_err:
                    print("LAST_ERROR:", str(last_err))
                    return 0
            except Exception as exc:
                print("CORE_IMPORT_EXCEPTION:", exc)

            # Instantiate QApplication without keeping an unused name
            QApplication([])

            try:
                from HjemmeladingApp.ui.profile_editor import ProfileEditor

                pe = ProfileEditor()
                pe.import_profile()
                last_err = getattr(pe.profile, "last_error", None)
                if last_err:
                    print("LAST_ERROR:", str(last_err))
                    return 0
                else:
                    print("NO_LAST_ERROR")
                    return 1
            except Exception as exc:
                print("SMOKE_EXCEPTION:", exc)
                return 3
            finally:
                try:
                    os.unlink(test_path)
                except Exception:
                    pass


        if __name__ == "__main__":
            rc = main()
            sys.exit(rc)
    win = MainWindow()
    win.show()

    # Open settings after short delay
    QTimer.singleShot(300, win.open_settings_dialog)
    # Quit app shortly after to finish smoke test
    QTimer.singleShot(1500, app.quit)
    rc = app.exec()
    print("App exited with rc=", rc)


if __name__ == "__main__":
    run()
