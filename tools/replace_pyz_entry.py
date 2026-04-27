import sys
import zipfile
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
dist_pyz = repo_root / "dist" / "VALKYRIE_BALLISTICS" / "_internal" / "base_library.zip"
source = repo_root / "src" / "ui" / "__init__.py"
print("dist_pyz", dist_pyz)
print("source", source)
if not dist_pyz.exists():
    print("ERROR: dist pyz not found", dist_pyz)
    sys.exit(2)
if not source.exists():
    print("ERROR: source not found", source)
    sys.exit(3)

new_pyz = dist_pyz.with_suffix(".new")
with zipfile.ZipFile(dist_pyz, "r") as zin, zipfile.ZipFile(new_pyz, "w") as zout:
    for item in zin.infolist():
        if item.filename == "src/ui/__init__.py":
            print("Skipping old", item.filename)
            continue
        data = zin.read(item.filename)
        zout.writestr(item, data)
    # write new entry
    src_text = source.read_text(encoding="utf-8")
    zout.writestr("src/ui/__init__.py", src_text)

# Replace original
backup = dist_pyz.with_suffix(".bak")
if backup.exists():
    backup.unlink()
dist_pyz.rename(backup)
new_pyz.rename(dist_pyz)
print("Replaced base_library.zip (backup at", backup, ")")
