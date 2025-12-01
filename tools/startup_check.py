import importlib
import traceback

modules = [
    'src.ui.main_window',
    'src.ui.reloading_theme',
    'src.ui.logo_helper',
    'src.assets.logo_tactical',
    'src.assets.logo_viking',
    'src.modules.workflow_hub',
    'src.modules.dashboard',
    'src.database.database',
]

results = []
for m in modules:
    try:
        importlib.import_module(m)
        results.append((m, 'OK', ''))
    except Exception as e:
        results.append((m, 'ERROR', traceback.format_exc()))

with open('startup_import_check.txt', 'w', encoding='utf-8') as f:
    for mod, status, tb in results:
        f.write(f"MODULE: {mod} STATUS: {status}\n")
        if tb:
            f.write(tb + '\n')

print('Wrote startup_import_check.txt')
