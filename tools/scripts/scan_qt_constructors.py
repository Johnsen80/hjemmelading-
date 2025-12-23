import os
import re

root = os.path.abspath(".")
paths = [os.path.join(root, "src"), os.path.join(root, "HjemmeladingApp")]
patterns = [
    "QLabel\\s*\\(",
    "QPushButton\\s*\\(",
    "QMenu\\s*\\(",
    "QDialog\\s*\\(",
    "QMessageBox\\s*\\(",
    "QTabWidget\\s*\\(",
    "QScrollArea\\s*\\(",
    "QGroupBox\\s*\\(",
    "QRadioButton\\s*\\(",
]
out = []
for base in paths:
    if not os.path.isdir(base):
        continue
    for dirpath, dirs, files in os.walk(base):
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(dirpath, f)
            try:
                s = open(p, encoding="utf-8").read()
            except Exception:
                continue
            for pat in patterns:
                for m in re.finditer(pat, s):
                    line = s.count("\n", 0, m.start()) + 1
                    snippet = s.splitlines()[line - 1].strip()
                    out.append(f"{p}:{line}: {pat[:-4]} -> {snippet}")
outfile = os.path.join("tools", "logs", "qt_constructors_scan.txt")
os.makedirs(os.path.dirname(outfile), exist_ok=True)
with open(outfile, "w", encoding="utf-8") as wf:
    wf.write("\n".join(out))
print("WROTE", outfile)
