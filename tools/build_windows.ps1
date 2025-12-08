# tools/build_windows.ps1
# Build helper for Windows (PowerShell)
# Run from repository root. Activates venv and runs PyInstaller.

if (Test-Path -Path ".\.venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

$log = "pyinstaller_build.log"
Write-Host "Building with PyInstaller; logging to $log"
& .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --noconsole --onedir --name Hjemmelading main.py *> $log

if (Test-Path $log) {
    Write-Host "--- Last 200 lines of build log ---"
    Get-Content $log -Tail 200
} else {
    Write-Host "Build finished but no log found. Check PyInstaller output above."
}
