import os

root = "src"
for dirpath, _, files in os.walk(root):
    for f in files:
        if not f.endswith(".py"):
            continue
        fp = os.path.join(dirpath, f)
        try:
            s = open(fp, encoding="utf-8").read()
        except Exception:
            continue
        if ".show(" in s:
            has_main = "if __name__" in s
            print(fp + " | has_main=" + str(has_main))
            lines = s.splitlines()
            for i, line in enumerate(lines, 1):
                if ".show(" in line:
                    start = max(1, i - 3)
                    end = min(i + 3, len(lines))
                    print(f"  L{i}: " + "\n".join(lines[start - 1 : end]))
