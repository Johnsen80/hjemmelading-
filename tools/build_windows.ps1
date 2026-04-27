# tools/build_windows.ps1
# Build helper for Windows (PowerShell)
# Prefer the main build script for consistent packaging.

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..") -ErrorAction SilentlyContinue
if ($repoRoot) {
    $primary = Join-Path $repoRoot.Path "scripts\build_windows.ps1"
    if (Test-Path $primary) {
        Write-Host "Delegating to scripts\build_windows.ps1"
        & $primary
        exit $LASTEXITCODE
    }
}

if (Test-Path -Path ".\.venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

$log = "pyinstaller_build.log"
Write-Host "Building with PyInstaller; logging to $log"
& .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --noconsole --onedir --name VALKYRIE_BALLISTICS main.py *> $log

if (Test-Path $log) {
    Write-Host "--- Last 200 lines of build log ---"
    Get-Content $log -Tail 200
} else {
    Write-Host "Build finished but no log found. Check PyInstaller output above."
}
