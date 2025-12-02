"""Inject consistent logging into 'except Exception as _suppressed_exc:' blocks.

Targets a small set of high-value files to keep changes focused and
reviewable. For each matching except-block, the script inserts a best-effort
logging block that prefers `_logger.exception(...)`, then falls back to
`safe_logger.append_exception(...)` and finally `sys.stderr`.

Run from repository root.
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


def make_logging_block(indent: str, filename: str) -> List[str]:
    # Return lines to insert after the except line
    return [
        f"{indent}    try:\n",
        f"{indent}        if _logger:\n",
        f"{indent}            _logger.exception(\"Unhandled exception in {filename}: %s\", _suppressed_exc)\n",
        f"{indent}    except Exception:\n",
        f"{indent}        pass\n",
        f"{indent}    try:\n",
        f"{indent}        safe_logger.append_exception(\"{filename} suppressed exception\", _suppressed_exc)\n",
        f"{indent}    except Exception:\n",
        f"{indent}        try:\n",
        f"{indent}            import sys\n",
        f"{indent}            sys.stderr.write(f\"{filename} suppressed exception: {{_suppressed_exc}}\\n\")\n",
        f"{indent}        except Exception:\n",
        f"{indent}            pass\n",
    ]


def process_file(path: Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    out_lines: List[str] = []
    changed = 0
    for i, line in enumerate(lines):
        out_lines.append(line)
        stripped = line.lstrip()
        # Match line like: except Exception as _suppressed_exc:
        if stripped.startswith("except Exception as _suppressed_exc:"):
            indent = line[: len(line) - len(stripped)]
            # inject logging block
            out_lines.extend(make_logging_block(indent, path.name))
            changed += 1
    if changed:
        path.write_text("".join(out_lines), encoding="utf-8")
    return changed


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    total = 0
    files_changed = 0
    for rel in TARGET_FILES:
        p = repo_root / rel
        n = process_file(p)
        if n:
            print(f"Patched {p} ({n} inserts)")
            total += n
            files_changed += 1
    print(f"Files changed: {files_changed}, total inserts: {total}")


if __name__ == "__main__":
    main()
