import os
import subprocess
import sys


def test_core_imports():
    # Ensure project parent is on sys.path so package imports resolve
    repo_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(repo_root)
    parent = os.path.dirname(project_root)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    modules = [
        "HjemmeladingApp.modules.user_profile",
        "HjemmeladingApp.ui.settings_dialog",
        "HjemmeladingApp.ui.customizer",
        "HjemmeladingApp.utils.safe_logger",
    ]

    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")

    for m in modules:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import importlib, os, sys; "
                    f"sys.path.insert(0, {parent!r}); "
                    "sys.modules.setdefault('modules', importlib.import_module('HjemmeladingApp.modules')); "
                    f"importlib.import_module({m!r})"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr or result.stdout
