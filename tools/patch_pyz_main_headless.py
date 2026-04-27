import zipfile
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
pyz = repo / "dist" / "VALKYRIE_BALLISTICS" / "_internal" / "base_library.zip"
print("pyz", pyz)
with zipfile.ZipFile(pyz, "r") as zin:
    names = zin.namelist()
    if "HjemmeladingApp/main.py" not in names:
        print("main.py not in pyz")
        raise SystemExit(2)
    src = zin.read("HjemmeladingApp/main.py").decode("utf-8")

# Insert HEADLESS auto-quit right before sys.exit(app.exec())
old = "sys.exit(app.exec())"
if old not in src:
    print("pattern not found")
    raise SystemExit(3)

insertion = """
    # If running in CI/headless mode, quit the app shortly after startup
    # so smoke tests can verify startup without staying in the event loop.
    try:
        from PyQt6.QtCore import QTimer
        import os
        if os.environ.get('HEADLESS','').lower() in ('1','true'):
            try:
                QTimer.singleShot(1000, app.quit)
            except Exception:
                pass
    except Exception:
        pass
"""
new_src = src.replace(old, insertion + "\n    " + old)

# Rebuild a new zip with modified main.py
new_pyz = pyz.with_suffix(".new")
with zipfile.ZipFile(pyz, "r") as zin, zipfile.ZipFile(new_pyz, "w") as zout:
    for item in zin.infolist():
        if item.filename == "HjemmeladingApp/main.py":
            zout.writestr(item, new_src)
        else:
            zout.writestr(item, zin.read(item.filename))

# Replace original
bak = pyz.with_suffix(".bak")
if bak.exists():
    bak.unlink()
pyz.rename(bak)
new_pyz.rename(pyz)
print("patched main.py in pyz (backup at", bak, ")")
