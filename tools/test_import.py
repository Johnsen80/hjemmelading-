import sys
from pathlib import Path

repo = Path(r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading")
sys.path.insert(0, str(repo))
print("sys.path[0]=", sys.path[0])
try:
    print("Imported settings_dialog OK")
except Exception as e:
    import traceback

    print("Import failed:", e)
    traceback.print_exc()
