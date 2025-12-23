import sys
from pathlib import Path
import os

# Ensure repository root is on sys.path so `HjemmeladingApp` imports work
try:
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
except Exception:
    pass

# Use pythonw to avoid console. Import and run main.
try:
    from HjemmeladingApp.main import main
except Exception as e:
    # Best-effort logging to a local file if imports fail
    try:
        log_path = os.path.join(os.path.expanduser("~"), "hjemmelading_run_local_error.log")
        with open(log_path, "w", encoding="utf-8") as f:
            import traceback

            f.write(traceback.format_exc())
    except Exception:
        pass
    raise

if __name__ == "__main__":
    main()
