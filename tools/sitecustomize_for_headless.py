import os
import threading
import time

if os.environ.get("HEADLESS", "").lower() in ("1", "true"):

    def _watchdog():
        # Short aggressive exit for CI smoke runs: sleep briefly then force exit.
        # Keeps headless smoke tests fast while still allowing app to initialize.
        time.sleep(3)
        try:
            os._exit(0)
        except Exception:
            pass

    t = threading.Thread(target=_watchdog, daemon=True)
    t.start()
