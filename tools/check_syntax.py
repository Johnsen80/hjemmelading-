import compileall
import sys
import os

paths = []
for p in ("src", "HjemmeladingApp"):
    if os.path.isdir(p):
        paths.append(p)

if not paths:
    print("No source directories found (src or HjemmeladingApp). Exiting.")
    sys.exit(0)

ok = True
for p in paths:
    print(f"Checking: {p}")
    res = compileall.compile_dir(p, force=False, quiet=1)
    if not res:
        ok = False

if ok:
    print("All files compiled successfully.")
else:
    print("Some files failed to compile. See messages above.")
    sys.exit(2)
