# PyInstaller .spec template for a one-folder build of Hjemmelading.
# Edit `datas` and `hiddenimports` as needed before running `pyinstaller --onedir`.

# To build using this spec:
# & .\.venv\Scripts\python.exe -m PyInstaller packaging\hjemmelading_onedir.spec

from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT


from pathlib import Path
project_root = Path().resolve()


# Collect PyQt6 resources/binaries so the onedir build runs on clean machines.
binaries, datas, hiddenimports = collect_all("PyQt6")

# Include demo data and Logo folder by default
_demo = project_root / 'data' / 'demo_weapons.json'
if _demo.exists():
    datas.append((str(_demo), 'data'))
_logo_dir = project_root / 'Logo'
if _logo_dir.exists():
    datas.append((str(_logo_dir), 'Logo'))
_fonts_dir = project_root / 'HjemmeladingApp' / 'resources' / 'fonts'
if _fonts_dir.exists():
    datas.append((str(_fonts_dir), 'HjemmeladingApp/resources/fonts'))

block_cipher = None

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root)],
    binaries=binaries,
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
