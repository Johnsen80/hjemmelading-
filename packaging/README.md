# Packaging notes

This folder contains helper scripts and notes for producing a Windows
build of Hjemmelading using PyInstaller.

Quick steps (from repo root, PowerShell):

1. Activate the project venv:

```powershell
& .\.venv\Scripts\Activate.ps1
```

2. Run the build helper which runs PyInstaller and writes a log:

```powershell
tools\build_windows.ps1
```

What to expect and next steps:

- The first builds will often surface missing data files or Qt plugin
  issues (platform-specific). The helper script captures full logs in
  `pyinstaller_build.log` for diagnosis.
- If the UI fails or Qt reports missing plugins at runtime, you'll need to
  add `--add-data` or `--add-binary` entries for the PyQt6 plugins and/or
  include hidden imports. Typical plugin folders are under your venv in
  `Lib\site-packages\PyQt6\Qt\plugins`.
- I can iterate on a spec file to include `src`, PyQt6 plugins and any
  hidden imports once we see concrete errors from the build log.

If you want me to continue automatically, allow me to iterate on the
spec and re-run builds until the EXE is functional. Note: long builds
may be truncated in the remote runner; running locally via `tools\build_windows.ps1`
is recommended for the fastest iteration.
