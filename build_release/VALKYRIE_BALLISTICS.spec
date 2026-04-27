# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, collect_submodules
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]

# Attempt to include the entire PyQt6 Qt6/bin directory to ensure all
# Qt6 DLL dependencies are bundled. This helps avoid missing DLL errors
# on machines where Qt runtime is not installed.
_extra_qt_binaries = []
try:
    import importlib.util

    spec = importlib.util.find_spec("PyQt6")
    if spec and spec.origin:
        pyqt_pkg_dir = Path(spec.origin).resolve().parent
        qt_bin = pyqt_pkg_dir / "Qt6" / "bin"
        if qt_bin.exists():
            for p in qt_bin.glob("**/*"):
                if p.is_file():
                    # install into top-level so Qt can find them
                    _extra_qt_binaries.append((str(p), "."))
except Exception:
    _extra_qt_binaries = []


_datas = []
_logo_ico = project_root / 'Logo' / 'logo.ico'
if _logo_ico.exists():
    _datas.append((str(_logo_ico), 'Logo'))
_logo_png = project_root / 'Logo' / 'logo.png'
if _logo_png.exists():
    _datas.append((str(_logo_png), 'Logo'))
_db_path = project_root / 'data' / 'reloading.db'
if _db_path.exists():
    _datas.append((str(_db_path), 'data'))

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root)],
    binaries=collect_dynamic_libs('PyQt6') + _extra_qt_binaries,
    datas=_datas + collect_data_files('PyQt6'),
    hiddenimports=(
        collect_submodules('modules')
        + collect_submodules('src.modules')
        + collect_submodules('src.ui')
        + collect_submodules('src')
        + ['src.ui.main_window']
    ),
    hookspath=[str(project_root / 'hooks')],
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
