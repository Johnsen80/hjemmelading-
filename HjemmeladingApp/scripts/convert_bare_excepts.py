"""Convert bare `except Exception:` to `except Exception as e:` and add best-effort logging.

This script updates Python files in-place. It matches only bare
`except Exception:` (no `as`) and replaces each with a block that captures
the exception as `e` and writes a best-effort log using `_logger` if present
and an `stderr` fallback. Changes are conservative to avoid altering other
exception forms.

Run from repository root.
"""
import re
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
PY_FILES = [p for p in BASE.rglob("*.py") if "__pycache__" not in p.parts]

PATTERN = re.compile(r"^(?P<indent>[ \t]*)except\s+Exception\s*:\s*$", re.MULTILINE)

REPLACEMENT = (
    "except Exception as e:\n"
    "{indent}    try:\n"
    "{indent}        if _logger:\n"
    "{indent}            _logger.exception(\"Unhandled exception in {file}: %s\", e)\n"
    "{indent}    except Exception:\n"
    "{indent}        pass\n"
    "{indent}    try:\n"
    "{indent}        import sys\n"
    "{indent}        sys.stderr.write(f\"Unhandled exception in {file}: {{e}}\\n\")\n"
    "{indent}    except Exception:\n"
    "{indent}        pass\n"
)


def process_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    changed = 0

    def repl(m: re.Match) -> str:
        nonlocal changed
        indent = m.group("indent")
        changed += 1
        return REPLACEMENT.format(indent=indent, file=path.name)

    new_text = PATTERN.sub(repl, text)
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed


def main() -> None:
    total = 0
    files_changed = 0
    for p in PY_FILES:
        c = process_file(p)
        if c:
            print(f"Updated {p} ({c} replacements)")
            total += c
            files_changed += 1
    print(f"Files changed: {files_changed}, total replacements: {total}")


if __name__ == "__main__":
    main()
