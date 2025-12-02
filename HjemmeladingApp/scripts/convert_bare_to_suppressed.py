"""Safely convert bare `except Exception:` to `except Exception as _suppressed_exc:`.

This is a low-risk first pass: it captures the exception into a named
variable prefixed with an underscore to avoid F841 warnings while not
adding logging or changing control flow. Run this first, then add
targeted logging in a second pass.
"""
import re
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
PY_FILES = [p for p in BASE.rglob("*.py") if "__pycache__" not in p.parts]

PAT = re.compile(r"^(?P<indent>[ \t]*)except\s+Exception\s*:\s*$", re.MULTILINE)


def process(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    new_text, n = PAT.subn(lambda m: f"{m.group('indent')}except Exception as _suppressed_exc:", text)
    if n:
        path.write_text(new_text, encoding="utf-8")
    return n


def main():
    total = 0
    files_changed = 0
    for p in PY_FILES:
        n = process(p)
        if n:
            print(f"Patched {p} ({n} replacements)")
            total += n
            files_changed += 1
    print(f"Files changed: {files_changed}, total replacements: {total}")


if __name__ == '__main__':
    main()
