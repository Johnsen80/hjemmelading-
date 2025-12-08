import importlib
import traceback

try:
    m = importlib.import_module("modules.hjemmelading")
    print("IMPORT OK:", m)
except Exception:
    traceback.print_exc()
    raise
