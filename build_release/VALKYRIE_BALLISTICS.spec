# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, collect_submodules


a = Analysis(
    ['..\\HjemmeladingApp\\main.py'],
    pathex=[r'C:\\Users\\bjjoh\\OneDrive\\Dokumenter\\Programering\\Hjemmelading'],
    binaries=collect_dynamic_libs('PyQt6'),
    datas=[('c:\\Users\\bjjoh\\OneDrive\\Dokumenter\\Programering\\Hjemmelading\\Logo\\logo.ico', 'Logo'), ('c:\\Users\\bjjoh\\OneDrive\\Dokumenter\\Programering\\Hjemmelading\\Logo\\logo.png', 'Logo'), ('c:\\Users\\bjjoh\\OneDrive\\Dokumenter\\Programering\\Hjemmelading\\data\\reloading.db', 'data')] + collect_data_files('PyQt6'),
    hiddenimports=(
        collect_submodules('modules')
        + collect_submodules('src.modules')
        + collect_submodules('src.ui')
        + collect_submodules('src')
        + ['src.ui.main_window']
    ),
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VALKYRIE_BALLISTICS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VALKYRIE_BALLISTICS',
)
