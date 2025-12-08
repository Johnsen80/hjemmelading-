# PyInstaller .spec template for a one-folder build of Hjemmelading.
# Edit `datas` and `hiddenimports` as needed before running `pyinstaller --onedir`.

# To build using this spec:
# & .\.venv\Scripts\python.exe -m PyInstaller packaging\hjemmelading_onedir.spec

import sys
from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]

# Include demo data and Logo folder by default
datas = [
    (str(project_root / 'data' / 'demo_weapons.json'), 'data'),
    (str(project_root / 'Logo'), 'Logo'),
]

hiddenimports = [
    'PyQt6',
]

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Hjemmelading', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)

coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='Hjemmelading')
