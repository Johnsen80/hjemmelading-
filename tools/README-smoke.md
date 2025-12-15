# Headless smoke test

This project includes a small headless smoke test that imports the UI modules and instantiates `SettingsDialog` and `MainWindow` in an offscreen Qt environment.

Quick usage (Windows PowerShell):

```powershell
# Use the helper that auto-detects the venv python
.\tools\run_smoke.ps1

# Or run directly with your venv python
& '.\.venv\Scripts\python.exe' '.\tools\headless_smoke_test.py'
```

On Unix-like systems:

```bash
./tools/run_smoke.sh
# To create a venv first (requires python3 on PATH):
./tools/run_smoke.sh create
```

If the test prints that fonts are missing, the project (Valkyrie Ballistics) bundles DejaVu fonts under `HjemmeladingApp/resources/fonts` and the smoke test registers them, but Qt may still print an informational warning about its own font search path. We filter that warning in the smoke test to keep logs clean.
