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
from typing import List, Tuple, Optional

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
    src_clean = src.lstrip('\ufeff')
    tree = ast.parse(src_clean)
    ranges: List[Tuple[int, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            name_attr: Optional[object] = getattr(node, 'name', None)
            is_target = False
            if isinstance(name_attr, str):
                is_target = (name_attr == '_suppressed_exc')
            elif hasattr(name_attr, 'id'):
                # defensive: older AST variants might expose a Name node
                is_target = (getattr(name_attr, 'id', None) == '_suppressed_exc')

            if is_target:
                start = getattr(node, 'lineno', None)
                end = getattr(node, 'end_lineno', None)
                if start is None:
                    continue
                if end is None:
                    end = start + 10
                ranges.append((start, end))

    # Deduplicate and sort
    ranges = sorted(set(ranges))
    return ranges


def make_replacement_block(relpath: str, indent: str) -> str:
    tpl = [
        "except Exception as _suppressed_exc:",
        f"{indent}try:",
        f"{indent}    try:",
        f"{indent}        from HjemmeladingApp.utils import safe_logger as _safe_logger",
        f"{indent}        _safe_logger.handle_suppressed(_suppressed_exc, \"{relpath}\")",
        f"{indent}    except Exception:",
        f"{indent}        import sys",
        f"{indent}        sys.stderr.write(\"{relpath} suppressed exception: \" + str(_suppressed_exc) + \"\\n\")",
        f"{indent}    except Exception:",
        f"{indent}        pass",
        f"{indent}pass",
    ]
    return "\n".join(tpl) + "\n"


def process_file(path: Path) -> int:
    p = Path(__file__).resolve().parents[1] / path
    if not p.exists():
        return 0
    raw = p.read_text(encoding='utf-8')
    s = raw.replace('\r\n', '\n')
    try:
        ranges = find_suppressed_except_ranges(s)
    except SyntaxError as e:
        print(f"Skipping {p}: parse error: {e}")
        return 0
    if not ranges:
        return 0

    lines = s.split('\n')
    changed = 0
    for start, end in sorted(ranges, reverse=True):
        start_idx = max(0, start - 1)
        end_idx = min(len(lines), end)

        orig_line = lines[start_idx] if start_idx < len(lines) else ''
        leading = ''.join(ch for ch in orig_line if ch.isspace())
        indent = leading or '    '

        repl = make_replacement_block(str(path), indent)
        repl_lines = repl.rstrip('\n').split('\n')

        lines[start_idx:end_idx] = repl_lines
        changed += 1

    new_s = '\n'.join(lines)
    if '\r\n' in raw:
        new_s = new_s.replace('\n', '\r\n')

    p.write_text(new_s, encoding='utf-8')
    print(f"Replaced {changed} blocks in {p}")
    return changed


def main() -> None:
    total = 0
    for f in TARGET:
        total += process_file(f)
    print(f"Files changed: {total}")


if __name__ == '__main__':
    main()
"""AST-based transformer to replace verbose injected suppressed-exception handlers.

Finds `except Exception as _suppressed_exc:` handlers and replaces their body
with a concise call to `safe_logger.handle_suppressed(_suppressed_exc, '<file>')`
with a fallback to `sys.stderr`. Uses AST line ranges to do safe in-place edits.

Run from project root: `python scripts/ast_replace_suppressed.py`
"""
from __future__ import annotations
from pathlib import Path

TARGET = [
    Path("ui/settings_dialog.py"),
    Path("ui/profile_editor.py"),
    Path("ui/customizer.py"),
    Path("utils/backgrounds.py"),
    Path("modules/user_profile.py"),
]


def find_suppressed_except_ranges(src: str) -> List[Tuple[int, int]]:
    """Return list of (start_lineno, end_lineno) for ExceptHandler nodes where name == '_suppressed_exc'."""
    # strip BOM if present
    src_clean = src.lstrip('\ufeff')
    tree = ast.parse(src_clean)
    ranges: List[Tuple[int, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            # Py >= 3.8 provides end_lineno
            if getattr(node, 'name', None) == '_suppressed_exc' or (isinstance(node.name, str) and node.name == '_suppressed_exc'):
                start = node.lineno
                end = getattr(node, 'end_lineno', None)
                if end is None:
                    # fall back: try to approximate by using next node lineno or +5
                    end = start + 10
                ranges.append((start, end))
    # Deduplicate and sort
    ranges = sorted(set(ranges))
    return ranges


def make_replacement_block(relpath: str, indent: str) -> str:
    # Build a block matching the file's indentation style
    lines = [
        "except Exception as _suppressed_exc:",
        f"{indent}try:",
        f"{indent}    try:",
        f"{indent}        from HjemmeladingApp.utils import safe_logger as _safe_logger",
        f"{indent}        _safe_logger.handle_suppressed(_suppressed_exc, \"{relpath}\")",
        f"{indent}    except Exception:",
        f"{indent}        import sys",
        f"{indent}        sys.stderr.write(\"{relpath} suppressed exception: \" + str(_suppressed_exc) + \"\\n\")",
        f"{indent}except Exception:",
        f"{indent}    pass",
        f"{indent}pass",
    ]
    return "\n".join(lines) + "\n"


def process_file(path: Path) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    raw = p.read_text(encoding='utf-8')
    # Normalize to \n for processing
    s = raw.replace('\r\n', '\n')
    try:
        ranges = find_suppressed_except_ranges(s)
    except SyntaxError as e:
        print(f"Skipping {p}: parse error: {e}")
        return 0
    if not ranges:
        return 0

    # Build new content by replacing ranges from bottom->top to preserve offsets
    lines = s.split('\n')
    changed = 0
    for start, end in sorted(ranges, reverse=True):
        # AST lineno is 1-based, list is 0-based
        start_idx = max(0, start - 1)
        end_idx = min(len(lines), end)

        # Determine indentation from the original start line
        orig_line = lines[start_idx]
        leading = ''.join(ch for ch in orig_line if ch.isspace())
        if leading == '':
            indent = '    '
        else:
            indent = leading

        repl = make_replacement_block(str(path), indent.rstrip('\n'))
        repl_lines = repl.rstrip('\n').split('\n')

        # Replace slice
        lines[start_idx:end_idx] = repl_lines
        changed += 1

    new_s = '\n'.join(lines)
    # restore CRLF style if original had CRLF
    if '\r\n' in raw:
        new_s = new_s.replace('\n', '\r\n')

    p.write_text(new_s, encoding='utf-8')
    print(f"Replaced {changed} blocks in {p}")
    return changed


def main():
    total = 0
    for f in TARGET:
        total += process_file(f)
    print(f"Files changed: {total}")


if __name__ == '__main__':
    main()
