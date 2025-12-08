<#
Build script for Windows (PowerShell). Creates a PyInstaller onedir build
for Hjemmelading. It attempts to locate PyQt6 plugin and resource folders
and adds them to the build so the resulting onedir works on other Windows
machines.

Usage (from project root, venv activated):
  & .\.venv\Scripts\Activate.ps1
  .\scripts\build_windows.ps1

#>
Write-Host "Hjemmelading: onedir build helper (PyInstaller)"

# Try to prefer the venv python if present
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptRoot "..\.venv\Scripts\python.exe" | Resolve-Path -ErrorAction SilentlyContinue
if ($venvPython) { $python = $venvPython.Path } else { $python = "python" }

Write-Host "Using Python: $python"

# Output log
$buildLog = Join-Path $scriptRoot "..\build_output.log" | Resolve-Path -ErrorAction SilentlyContinue
if (-not $buildLog) { $buildLog = Join-Path $scriptRoot "..\build_output.log" }

Write-Host "Build log: $buildLog"

function Run-Log([string[]] $cmd) {
    Write-Host "Running: $($cmd -join ' ')"
    $proc = Start-Process -FilePath $cmd[0] -ArgumentList $cmd[1..($cmd.Length-1)] -NoNewWindow -PassThru -Wait -RedirectStandardOutput $buildLog -RedirectStandardError $buildLog
    return $proc.ExitCode
}

# Probe PyQt6 plugin path
try {
    $pluginPath = & $python -c "import PyQt6, pathlib, sys; p = pathlib.Path(PyQt6.__file__).parents[1] / 'Qt' / 'plugins'; sys.stdout.write(str(p))" 2>$null
} catch {
    $pluginPath = $null
}

if (-not $pluginPath) {
    Write-Warning "Could not auto-detect PyQt6 plugin path. Ensure PyQt6 is installed in the active venv."
} else {
    Write-Host "Detected PyQt6 plugins at: $pluginPath"
}

# Prepare add-data entries (relative to project root)
$projectRoot = (Resolve-Path "$scriptRoot\..").Path
$dataJson = Join-Path $projectRoot 'data\demo_weapons.json'
$logoDir = Join-Path $projectRoot 'Logo'

$addDataArgs = @()
if (Test-Path $dataJson) { $addDataArgs += "--add-data"; $addDataArgs += "$dataJson;data" }
if (Test-Path $logoDir) { $addDataArgs += "--add-data"; $addDataArgs += "$logoDir;Logo" }

# Collect binary/plugin args (platforms + resources)
$addBinaryArgs = @()
if ($pluginPath) {
    $platforms = Join-Path $pluginPath 'platforms'
    if (Test-Path $platforms) {
        $addBinaryArgs += "--add-binary"; $addBinaryArgs += "$platforms\qwindows.dll;PyQt6\Qt\plugins\platforms"
    }
    # WebEngine resources (if present)
    $webengine = Join-Path (Split-Path $pluginPath -Parent) 'resources'
    if (Test-Path $webengine) {
        $addBinaryArgs += "--add-binary"; $addBinaryArgs += "$webengine;PyQt6\Qt\resources"
    }
}

Write-Host "Preparing PyInstaller args..."

# Base args
$pyInstallerArgs = @('--onedir','--noconfirm','--name','Hjemmelading','--windowed','--log-level=DEBUG')

foreach ($a in $addDataArgs) { $pyInstallerArgs += $a }
foreach ($b in $addBinaryArgs) { $pyInstallerArgs += $b }

# Hidden imports that commonly help with PyInstaller collecting PyQt6 hooks
$pyInstallerArgs += '--hidden-import'; $pyInstallerArgs += 'PyQt6'; $pyInstallerArgs += '--hidden-import'; $pyInstallerArgs += 'PyQt6.sip'

# Ensure WebEngine resources are included when present
try {
    $sitePackages = & $python -c "import site, sys; print('\n'.join(site.getsitepackages()))" 2>$null
    if ($sitePackages) { Write-Host "Site packages: $sitePackages" }
} catch {}

# Entry script
$entry = Join-Path $projectRoot 'main.py'
$pyInstallerArgs += $entry

Write-Host "pyinstaller args: $($pyInstallerArgs -join ' ')"

# Run PyInstaller and capture output to build_output.log
$cmd = @($python, '-m', 'PyInstaller') + $pyInstallerArgs
$exit = Run-Log $cmd
if ($exit -ne 0) {
    Write-Error "PyInstaller failed with exit code $exit. See $buildLog for details."
    exit $exit
}

Write-Host "Build complete. Check the 'dist\\Hjemmelading' folder and $buildLog for details."
<#
Build script for Windows using PyInstaller.

Usage:
  Open PowerShell (run as user, not necessarily admin) in the repository root and run:

    .\scripts\build_windows.ps1

Notes:
- Requires Python 3.9+ and Visual C++ redistributable installed on the build machine.
- This script creates/uses a virtualenv at `.venv` under repo root.
- Output will be in `dist/VALKYRIE_BALLISTICS` (one-folder build).
- Adjust `$entryPoint` if your app entry is different than `src/main.py`.
#>

param(
    [switch]$OneFile = $false
)

$ErrorActionPreference = 'Stop'

# Move to repository root (parent of this script)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location (Join-Path $scriptDir '..')

Write-Host "Building VALKYRIE BALLISTICS (Windows) from: $(Get-Location)"

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtualenv .venv..."
    python -m venv .venv
}

Write-Host "Activating virtualenv..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip and installing build deps..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller pyinstaller-hooks-contrib

# Entry point - adjust if your main script is at a different path
# Default to repo root `main.py` if present; fall back to `src/main.py`.
if (Test-Path 'main.py') {
    $entryPoint = 'main.py'
} else {
    $entryPoint = 'src/main.py'
}

if (-not (Test-Path $entryPoint)) {
    Write-Error "Entry point not found: $entryPoint. Update scripts/build_windows.ps1 to point to your main script."
    exit 1
}

# Common PyInstaller args
$name = 'VALKYRIE_BALLISTICS'
$distPath = "dist\$name"
$workPath = 'build'
$specPath = '.'

# Data files to include (source;destination) - adjust as needed
$dataArgs = @(
    "Logo\logo.png;Logo",
    "data\reloading.db;data"
)

# Build add-data parameters in a PowerShell 5.1 compatible way
$addDataParams = ($dataArgs | ForEach-Object { "--add-data `"$_`"" }) -join ' '

# Use onefile only if explicitly requested (PyQt6 apps often work better as onedir)
if ($OneFile) {
    $oneFileArg = '--onefile'
    $oneDirArg = ''
} else {
    $oneFileArg = ''
    $oneDirArg = '--onedir'
}

Write-Host "Running PyInstaller... (this may take a while)"

 # Ensure PyInstaller adds the repository root to its analysis path so the
 # `src` package is discoverable during static analysis. Also add an explicit
 # hidden import for the UI main window to avoid optional-import warnings.
 # Also pass any additional hooks from the `hooks` directory so our
 # `hook-src.ui.py` is picked up by PyInstaller.
 $hooksDir = 'hooks'
 if (Test-Path $hooksDir) {
     $hooksArg = "--additional-hooks-dir `"$hooksDir`""
 } else {
     $hooksArg = ''
 }

 $pyinstallerCmd = "pyinstaller --noconfirm --windowed $oneFileArg $oneDirArg --name $name --distpath dist --workpath $workPath --specpath $specPath --paths `".`" --hidden-import `"src.ui.main_window`" $hooksArg $addDataParams `"$entryPoint`""

Write-Host $pyinstallerCmd
Invoke-Expression $pyinstallerCmd

Write-Host "Build finished. Output folder: $distPath"

Write-Host "IMPORTANT: For PyQt6 apps you may need to include Qt platform plugins and QtWebEngine resources."
Write-Host "If the app fails with plugin errors, see scripts/README_build_windows.md for troubleshooting steps."

Write-Host "Done."
