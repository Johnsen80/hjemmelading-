import shutil
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
src = repo / "src" / "ui" / "main_window.py"
dst = (
    repo
    / "dist"
    / "VALKYRIE_BALLISTICS"
    / "_internal"
    / "src"
    / "ui"
    / "main_window.py"
)
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, dst)
print("copied", src, "->", dst)
