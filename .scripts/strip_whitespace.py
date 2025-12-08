"""
Strip trailing whitespace and remove whitespace-only blank lines for .py files under src
Run: python .scripts/strip_whitespace.py
"""

import os

root = os.path.join(os.path.dirname(__file__), "..", "src")
root = os.path.normpath(root)

for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(dirpath, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            changed = False
            new_lines = []
            for line in lines:
                if line.strip() == "":
                    if line == "\n":
                        new_lines.append(line)
                    else:
                        # replace whitespace-only blank line with a single newline
                        new_lines.append("\n")
                        changed = True
                else:
                    new = line.rstrip("\t \r\n") + "\n"
                    if new != line:
                        changed = True
                    new_lines.append(new)
            if changed:
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
        except Exception as e:
            print(f"Failed to process {path}: {e}")
