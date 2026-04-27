import importlib
import traceback

try:
    m = importlib.import_module("src.ui")
    print("HAS_MAINWINDOW", hasattr(m, "MainWindow"))
    if hasattr(m, "MainWindow"):
        print("MainWindow module:", m.MainWindow.__module__)
except Exception as e:
    print("IMPORT ERROR:", e)
    traceback.print_exc()
