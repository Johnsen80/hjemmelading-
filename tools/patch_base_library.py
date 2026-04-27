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

src_text = source.read_text(encoding="utf-8")
# Write into the zip under path 'src/ui/__init__.py'
with zipfile.ZipFile(dist_pyz, "a") as z:
    z.writestr("src/ui/__init__.py", src_text)
print("patched base_library.zip")
