"""Replace verbose injected suppressed-exception handlers with concise safe_logger calls.

This script is conservative: it normalizes newlines, finds except blocks that start
with ``except Exception as _suppressed_exc:`` and extend until the next ``pass`` on
the same indentation, and replaces them with a compact safe logging block that
prefers the project's `safe_logger` and falls back to `sys.stderr`.

Run this from the project root (it will operate on paths relative to this file).
"""

from pathlib import Path
import re

TARGET = [
    Path("ui/settings_dialog.py"),
    Path("ui/profile_editor.py"),
    Path("ui/customizer.py"),
    Path("utils/backgrounds.py"),
    Path("modules/user_profile.py"),
]


ROOT = Path(__file__).resolve().parents[0]


def make_replacement(rel_path: str) -> str:
    # Build a compact replacement; use .format to insert rel_path without f-strings
    tpl = (
        "except Exception as _suppressed_exc:\n"
        "    try:\n"
        "        try:\n"
        "            from HjemmeladingApp.utils import safe_logger as _safe_logger\n"
        "            _safe_logger.handle_suppressed(_suppressed_exc, \"{rel_path}\")\n"
        "        except Exception:\n"
        "            import sys\n"
        "            sys.stderr.write(\"{rel_path} suppressed exception: \" + str(_suppressed_exc) + \"\\n\")\n"
        "    except Exception:\n"
        "        pass\n"
        "    pass\n"
    )
    return tpl.format(rel_path=rel_path)


def process_file(path: Path) -> int:
    p = ROOT / path
    if not p.exists():
        return 0
    original = p.read_bytes()
    # detect newline style
    newline = '\r\n' if b'\r\n' in original else '\n'
    s = original.decode('utf-8').replace('\r\n', '\n')

    pattern = re.compile(r"except Exception as _suppressed_exc:\n(?:[ \t].*\n)*?[ \t]*pass\n", re.DOTALL)
    repl = make_replacement(str(path))
    new_s, n = pattern.subn(repl, s)
    if n > 0:
        # restore original newline style
        new_s = new_s.replace('\n', newline)
        p.write_text(new_s, encoding='utf-8', newline='')
        print(f"Replaced {n} blocks in {p}")
    return n


def main() -> None:
    total = 0
    for f in TARGET:
        total += process_file(f)
    print(f"Files changed: {total}")


if __name__ == '__main__':
    main()
