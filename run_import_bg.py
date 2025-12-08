import importlib
import traceback

try:
    m = importlib.import_module("HjemmeladingApp.utils.backgrounds")
    print("IMPORT OK:", m)
except Exception:
    traceback.print_exc()
    raise
