"""Inject safe logging after `except Exception as _suppressed_exc:` lines.

This version uses safe lookups so it doesn't assume `_logger` or
`safe_logger`/`append_exception` exist in the module namespace.

Only operates on a small set of key files.
"""
from pathlib import Path
from typing import List

TARGET_FILES: List[Path] = [
    Path("ui/settings_dialog.py"),
    Path("ui/profile_editor.py"),
    Path("ui/customizer.py"),
    Path("utils/backgrounds.py"),
    Path("utils/safe_logger.py"),
    Path("modules/user_profile.py"),
]


def logging_block(indent: str, filename: str) -> List[str]:
    # Indented block that uses globals().get to avoid NameError
    return [
        f"{indent}    try:\n",
        f"{indent}        _mod_logger = globals().get('_logger') or globals().get('logger')\n",
        f"{indent}        if _mod_logger:\n",
        f"{indent}            _mod_logger.exception(\"Unhandled exception in {filename}: %s\", _suppressed_exc)\n",
        f"{indent}    except Exception:\n",
        f"{indent}        pass\n",
        f"{indent}    try:\n",
        f"{indent}        _append = globals().get('append_exception')\n",
        f"{indent}        if _append:\n",
        f"{indent}            _append(\"{filename} suppressed exception\", _suppressed_exc)\n",
        f"{indent}        else:\n",
        f"{indent}            _safe = globals().get('safe_logger')\n",
        f"{indent}            if _safe:\n",
        f"{indent}                try:\n",
        f"{indent}                    _safe.append_exception(\"{filename} suppressed exception\", _suppressed_exc)\n",
        f"{indent}                except Exception:\n",
        f"{indent}                    pass\n",
        f"{indent}            else:\n",
        f"{indent}                try:\n",
        f"{indent}                    import sys\n",
        f"{indent}                    sys.stderr.write(f\"{filename} suppressed exception: {{_suppressed_exc}}\\n\")\n",
        f"{indent}                except Exception:\n",
        f"{indent}                    pass\n",
        f"{indent}    except Exception:\n",
        f"{indent}        try:\n",
        f"{indent}            import sys\n",
        f"{indent}            sys.stderr.write(f\"{filename} suppressed exception: {{_suppressed_exc}}\\n\")\n",
        f"{indent}        except Exception:\n",
        f"{indent}            pass\n",
    ]


def process(path: Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    out: List[str] = []
    changed = 0
    for line in lines:
        out.append(line)
        stripped = line.lstrip()
        if stripped.startswith("except Exception as _suppressed_exc:"):
            indent = line[: len(line) - len(stripped)]
            out.extend(logging_block(indent, path.name))
            changed += 1
    if changed:
        path.write_text("".join(out), encoding="utf-8")
    return changed


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    total = 0
    files_changed = 0
    for rel in TARGET_FILES:
        p = repo_root / rel
        n = process(p)
        if n:
            print(f"Patched {p} ({n} inserts)")
            total += n
            files_changed += 1
    print(f"Files changed: {files_changed}, total inserts: {total}")


if __name__ == '__main__':
    main()
