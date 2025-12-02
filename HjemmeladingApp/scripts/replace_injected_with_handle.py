"""Replace verbose injected suppressed-exception handlers with concise safe_logger calls.

This script is conservative: it normalizes newlines, finds except blocks that start with
`except Exception as _suppressed_exc:` and extend until the next `pass` on the same
indentation, and replaces them with a compact safe logging block that prefers the
project's `safe_logger` and falls back to `sys.stderr`.

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
    # Use a concise and safe block. No nested f-strings.
    return (
        "except Exception as _suppressed_exc:\n"
        "    try:\n"
        f"        try:\n"
        f"            from HjemmeladingApp.utils import safe_logger as _safe_logger\n"
        f"            _safe_logger.handle_suppressed(_suppressed_exc, \"{rel_path}\")\n"
        f"        except Exception:\n"
        f"            import sys\n"
        f"            sys.stderr.write(\"{rel_path} suppressed exception: \" + str(_suppressed_exc) + \"\\n\")\n"
        "    except Exception:\n"
        "        pass\n"
        "    pass\n"
    )


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


def main():
    total = 0
    for f in TARGET:
        total += process_file(f)
    print(f"Files changed: {total}")


if __name__ == '__main__':
    main()
from pathlib import Path
import re

TARGET = [
    Path("ui/settings_dialog.py"),
    Path("ui/profile_editor.py"),
    Path("ui/customizer.py"),
    Path("utils/backgrounds.py"),
    Path("modules/user_profile.py"),
]

ROOT = Path(__file__).resolve().parents[1]


def make_new(filename: str) -> str:
    # Keep same indentation as the replaced blocks (12 spaces)
    return (
        "except Exception as _suppressed_exc:\n"
        "            try:\n"
        f"                safe_logger.handle_suppressed(_suppressed_exc, \"{filename}\")\n"
        "            except Exception:\n"
        "                try:\n"
        f"                    import sys\n"
        f"                    sys.stderr.write(\"{filename} suppressed exception: \" + str(_suppressed_exc) + \"\\n\")\n"
        "                except Exception:\n"
        "                    pass\n"
        "            pass\n"
    )


def process_file(rel: Path) -> int:
    p = ROOT / rel
    if not p.exists():
        return 0
    s = p.read_text(encoding="utf-8")
    # Normalize windows newlines to \n for regex matching
    s_norm = s.replace('\r\n', '\n')

    # Replace verbose injected blocks starting with 'except Exception as _suppressed_exc:'
    pattern = re.compile(r"except Exception as _suppressed_exc:\n(?:[ \t].*?\n)*?[ \t]*pass\n", re.DOTALL)

    new_block = make_new(rel.name)
    new_s, n = pattern.subn(new_block, s_norm)
    # convert back to CRLF when writing to keep Windows style
    if n > 0:
        new_s = new_s.replace('\n', '\r\n')
    if n > 0:
        p.write_text(new_s, encoding="utf-8")
        print(f"Replaced {n} blocks in {p}")
        return n
    return 0


def main():
    total = 0
    for f in TARGET:
        total += process_file(f)
    print(f"Files changed: {total}")


if __name__ == '__main__':
    main()
