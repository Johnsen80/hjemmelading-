import importlib
import os
import subprocess
import sys
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
print("Repo root:", ROOT)
venv_py = os.path.join(ROOT, "ui", ".venv", "Scripts", "python.exe")
if not os.path.exists(venv_py):
    print("venv python not found at", venv_py)
    sys.exit(1)

# 1) Run smoke script
smoke = os.path.join(ROOT, "tools", "run_settings_smoke.py")
print("\nRunning smoke script:", smoke)
res = subprocess.run([venv_py, smoke], capture_output=True, text=True)
print("--- STDOUT ---")
print(res.stdout)
print("--- STDERR ---")
print(res.stderr)
print("smoke exitcode:", res.returncode)
if res.returncode != 0:
    print("Smoke script failed, aborting further checks")

# 2) Run pytest
print("\nRunning pytest...")
res2 = subprocess.run(
    [venv_py, "-m", "pytest", "-q", ROOT], capture_output=True, text=True
)
print(res2.stdout)
print(res2.stderr)
print("pytest exitcode:", res2.returncode)

# 3) Import smoke check
print("\nRunning import smoke check...")
parent = os.path.dirname(ROOT)
if parent not in sys.path:
    sys.path.insert(0, parent)

mods = [
    "HjemmeladingApp.main",
    "HjemmeladingApp.modules.user_profile",
    "HjemmeladingApp.ui.settings_dialog",
    "HjemmeladingApp.ui.customizer",
    "HjemmeladingApp.utils.safe_logger",
]
err = False
for m in mods:
    try:
        importlib.import_module(m)
        print("import OK:", m)
    except Exception as e:
        print("import FAILED:", m, "->", e)
        traceback.print_exc()
        err = True
print("IMPORT CHECK COMPLETE; failures=" + str(err))
if res.returncode != 0:
    sys.exit(res.returncode)
if res2.returncode != 0 or err:
    sys.exit(2)
print("\nALL CHECKS PASSED")
