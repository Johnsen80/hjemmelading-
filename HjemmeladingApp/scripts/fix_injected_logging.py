"""Fix previously injected logging to avoid NameError when `_logger`/`safe_logger` missing.

This script finds the common patterns injected earlier and replaces them with
safe lookups using `globals().get(...)` and a stderr fallback.
"""
from pathlib import Path
from typing import List
import re

TARGET_FILES: List[Path] = [
    Path("ui/settings_dialog.py"),
    Path("ui/profile_editor.py"),
    Path("ui/customizer.py"),
    Path("utils/backgrounds.py"),
    Path("utils/safe_logger.py"),
    Path("modules/user_profile.py"),
]


def fix_file(p: Path) -> int:
    if not p.exists():
        return 0
    s = p.read_text(encoding="utf-8")
    orig = s

    # Replace 'if _logger:' occurrences with safe lookup
    s = re.sub(
        r"(?m)^(?P<indent>[ \t]*)try:\n(?P=indent)[ \t]*if _logger:\n(?P<rest>.*?)^(?P=indent)except Exception:\n(?P=indent)[ \t]*pass\n",
        lambda m: (
            f"{m.group('indent')}try:\n"
            f"{m.group('indent')}    _mod_logger = globals().get('_logger', None)\n"
            f"{m.group('indent')}    if _mod_logger:\n"
            + m.group('rest')
            + f"{m.group('indent')}except Exception:\n{m.group('indent')}    pass\n"
        ),
        s,
    )

    # Replace 'safe_logger.append_exception(...)' single-line calls with safe lookup+fallback
    def repl_safe(match):
        indent = match.group('indent')
        inner = match.group('inner')
        # reuse the same message text in stderr fallback
        return (
            f"{indent}try:\n"
            f"{indent}    _safe_logger = globals().get('safe_logger', None)\n"
            f"{indent}    if _safe_logger:\n"
            f"{indent}        _safe_logger.append_exception({inner})\n"
            f"{indent}    else:\n"
            f"{indent}        try:\n"
            f"{indent}            import sys\n"
            f"{indent}            sys.stderr.write(str({inner}.split(',')[0]) + f\": {{_suppressed_exc}}\\n\")\n"
            f"{indent}        except Exception:\n"
            f"{indent}            pass\n"
        )

    s = re.sub(r"(?m)^(?P<indent>[ \t]*)try:\n(?P=indent)[ \t]*safe_logger\.append_exception\((?P<inner>.*?)\)\n(?P=indent)except Exception:\n(?P=indent)[ \t]*pass\n",
                   repl_safe,
                   s)

    if s != orig:
        p.write_text(s, encoding="utf-8")
        return 1
    return 0


def main():
    repo_root = Path(__file__).resolve().parents[1]
    changed = 0
    for rel in TARGET_FILES:
        p = repo_root / rel
        if fix_file(p):
            print(f"Fixed {p}")
            changed += 1
    print(f"Files fixed: {changed}")


if __name__ == '__main__':
    main()
