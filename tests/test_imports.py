import sys
import traceback

# Simple import smoke test to detect import-time crashes in key modules
def test_import_ui_modules():
    modules = [
        'HjemmeladingApp.ui.settings_dialog',
        'src.ui.main_window',
        'src.assets.logo',
        'src.ui.logo_helper',
        'src.ui.reloading_theme',
    ]
    failed = []
    for m in modules:
        try:
            __import__(m)
        except Exception as e:
            failed.append((m, traceback.format_exc()))
    assert not failed, 'Import failures:\n' + '\n'.join(f"{m}: {tb}" for m, tb in failed)
