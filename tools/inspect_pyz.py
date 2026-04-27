import zipfile
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
pyz = repo_root / "dist" / "VALKYRIE_BALLISTICS" / "_internal" / "base_library.zip"
print("pyz", pyz)
with zipfile.ZipFile(pyz, "r") as z:
    data = z.read("src/ui/__init__.py").decode("utf-8")
    print(data[:2000])
