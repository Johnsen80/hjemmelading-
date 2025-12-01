import importlib
import os
import sys


def test_core_imports():
    # Ensure project parent is on sys.path so package imports resolve
    repo_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(repo_root)
    parent = os.path.dirname(project_root)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    modules = [
        'HjemmeladingApp.main',
        'HjemmeladingApp.modules.user_profile',
        'HjemmeladingApp.ui.settings_dialog',
        'HjemmeladingApp.ui.customizer',
        'HjemmeladingApp.utils.safe_logger',
    ]

    for m in modules:
        importlib.import_module(m)
