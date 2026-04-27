VALKYRIE BALLISTICS — Windows build notes

This document describes how to produce a Windows test build using the provided `build_windows.ps1` script.

Prerequisites
- Windows machine
- Python 3.9+ installed and on `PATH`
- Visual C++ Redistributable for Visual Studio 2015-2019 (x86/x64) installed for runtime compatibility (https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
- Enough disk space (PyInstaller will create a temporary build folder)

Quick build steps (PowerShell, repo root):

```powershell
# Run the build script (one-folder default, standardized on main.py)
.\scripts\build_windows.ps1
```

Notes & Troubleshooting
- Entry point: The build and launch scripts are standardized on the repo-root `main.py`.
- Output folder: the default PyInstaller output is `dist\VALKYRIE_BALLISTICS\`.
- Executable name: the packaged app executable is `VALKYRIE_BALLISTICS.exe`.
- Data files: The script currently bundles `Logo\logo.png` and `data\reloading.db`. Add or remove `--add-data` entries in the script as needed.
- Qt plugins: PyQt6 applications commonly need the `platforms` plugin and (if using web views) QtWebEngine resources. If the built app reports errors like "This application failed to start because it could not find or load the Qt platform plugin "windows"", you will need to copy `platforms` (and other plugin directories) into the output folder. See PyInstaller docs and search for "Qt platform plugin".
- If you encounter missing module errors at runtime, run the built exe from a console to capture stderr, and add `--hidden-import` flags to the PyInstaller command in the script.

Recommended follow-ups
- Add an application icon via `--icon` in the PyInstaller command.
- Create an installer (NSIS/Inno Setup) if you want proper installation and Start Menu shortcuts.
- Test the built app on a clean Windows VM to verify Visual C++ dependencies.
