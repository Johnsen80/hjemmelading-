"""AST-based transformer to replace verbose injected suppressed-exception handlers.

Finds ``except Exception as _suppressed_exc:`` handlers and replaces their
body with a concise call to ``safe_logger.handle_suppressed(_suppressed_exc, '<file>')``
with a fallback to ``sys.stderr``. Uses AST line ranges to perform safer
in-place edits.

Run from project root: ``python -m scripts.ast_replace_suppressed``
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Optional, Tuple

TARGET = [
    Path("ui/settings_dialog.py"),
    Path("ui/profile_editor.py"),
    Path("ui/customizer.py"),
    Path("utils/backgrounds.py"),
    Path("modules/user_profile.py"),
]


def find_suppressed_except_ranges(src: str) -> List[Tuple[int, int]]:
    """Return list of (start_lineno, end_lineno) for ExceptHandler nodes that
    capture the exception into the name ``_suppressed_exc``.
    """
    src_clean = src.lstrip("\ufeff")
    tree = ast.parse(src_clean)
    ranges: List[Tuple[int, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            # node.name may be a str (py3.8+) or a Name node in older ASTs
            name_attr: Optional[object] = getattr(node, "name", None)
            is_target = False
            if isinstance(name_attr, str):
                is_target = name_attr == "_suppressed_exc"
            elif hasattr(name_attr, "id"):
                is_target = getattr(name_attr, "id", None) == "_suppressed_exc"

            if is_target:
                start = getattr(node, "lineno", None)
                end = getattr(node, "end_lineno", None)
                if start is None:
                    continue
                if end is None:
                    end = start + 10
                ranges.append((start, end))

    # Deduplicate and sort
    ranges = sorted(set(ranges))
    return ranges


def make_replacement_block(relpath: str, indent: str) -> str:
    lines = [
        "except Exception as _suppressed_exc:",
        f"{indent}try:",
        f"{indent}    try:",
        f"{indent}        from HjemmeladingApp.utils import safe_logger as _safe_logger",
        f'{indent}        _safe_logger.handle_suppressed(_suppressed_exc, "{relpath}")',
        f"{indent}    except Exception:",
        f"{indent}        import sys",
        f"{indent}        try:",
        f"{indent}            sys.stderr.write(\"{relpath} suppressed exception: \" + str(_suppressed_exc) + '\\n')",
        f"{indent}        except Exception:",
        f"{indent}            pass",
        f"{indent}    except Exception:",
        f"{indent}        pass",
        f"{indent}pass",
    ]
    return "\n".join(lines) + "\n"


def process_file(path: Path) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    raw = p.read_text(encoding="utf-8")
    s = raw.replace("\r\n", "\n")
    try:
        ranges = find_suppressed_except_ranges(s)
    except SyntaxError as e:
        print(f"Skipping {p}: parse error: {e}")
        return 0
    if not ranges:
        return 0

    lines = s.split("\n")
    changed = 0
    for start, end in sorted(ranges, reverse=True):
        start_idx = max(0, start - 1)
        end_idx = min(len(lines), end)

        orig_line = lines[start_idx] if start_idx < len(lines) else ""
        leading = "".join(ch for ch in orig_line if ch.isspace())
        indent = leading or "    "

        repl = make_replacement_block(str(path), indent)
        repl_lines = repl.rstrip("\n").split("\n")

        lines[start_idx:end_idx] = repl_lines
        changed += 1

    new_s = "\n".join(lines)
    if "\r\n" in raw:
        new_s = new_s.replace("\n", "\r\n")

    p.write_text(new_s, encoding="utf-8")
    print(f"Replaced {changed} blocks in {p}")
    return changed


def main() -> None:
    total = 0
    for f in TARGET:
        total += process_file(f)
    print(f"Files changed: {total}")


if __name__ == "__main__":
    main()
