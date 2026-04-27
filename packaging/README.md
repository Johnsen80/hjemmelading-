# Packaging notes

This folder contains helper scripts and notes for producing a Windows
build of Valkyrie Ballistics using PyInstaller.

Quick steps (from repo root, PowerShell):

1. Activate the project venv:

```powershell
& .\.venv\Scripts\Activate.ps1
```

2. Run the build helper which runs PyInstaller and writes logs:

```powershell
scripts\build_windows.ps1
```

What to expect and next steps:

- The first builds will often surface missing data files or Qt plugin
  issues (platform-specific). The helper script captures full logs in
  `build_output.log` and `build_output.err.log` for diagnosis.
- If the UI fails or Qt reports missing plugins at runtime, you'll need to
  add `--add-data` or `--add-binary` entries for the PyQt6 plugins and/or
  include hidden imports. Typical plugin folders are under your venv in
  `Lib\site-packages\PyQt6\Qt6\plugins` (or `PyQt6\Qt\plugins` on older layouts).
- I can iterate on a spec file to include `src`, PyQt6 plugins and any
  hidden imports once we see concrete errors from the build log.

Optional: build an installer (Inno Setup)

- Install Inno Setup 6 (or set `VALKYRIE_INNO_SETUP_PATH` to `ISCC.exe`).
- Set `VALKYRIE_BUILD_INSTALLER=1` before running the build script.
- The installer is written to `dist_installer` (override with
  `VALKYRIE_INSTALLER_OUT`).
- To pass the build output location to Inno Setup manually, set
  `VALKYRIE_DIST_DIR` (defaults to `dist\VALKYRIE_BALLISTICS`).
- To set the installer version, set `VALKYRIE_APP_VERSION`.

Optional: sign binaries/installers

- Set `VALKYRIE_SIGN=1` to sign the app EXE and installer.
- Provide signing config via:
  - `VALKYRIE_SIGNTOOL_PATH` (optional if `signtool.exe` is on PATH)
  - `VALKYRIE_CERT_PATH` (PFX)
  - `VALKYRIE_CERT_PASSWORD` (PFX password)
  - `VALKYRIE_CERT_SHA1` (thumbprint, alternative to PFX)
  - `VALKYRIE_TIMESTAMP_URL` (defaults to `http://timestamp.digicert.com`)

If you want me to continue automatically, allow me to iterate on the
spec and re-run builds until the EXE is functional. Note: long builds
may be truncated in the remote runner; running locally via `tools\build_windows.ps1`
is recommended for the fastest iteration.
