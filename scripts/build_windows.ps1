<#
Build script for Windows (PowerShell). Creates a PyInstaller onedir build
for Hjemmelading. It attempts to locate PyQt6 plugin and resource folders
and adds them to the build so the resulting onedir works on other Windows
machines.

Usage (from project root, venv activated):
  & .\.venv\Scripts\Activate.ps1
  .\scripts\build_windows.ps1

#>
# This script uses approved PowerShell verbs only.
Write-Host "Valkyrie Ballistics: onedir build helper (PyInstaller)"

# Try to prefer the venv python if present
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptRoot "..\.venv\Scripts\python.exe" | Resolve-Path -ErrorAction SilentlyContinue
$appVenvPython = Join-Path $scriptRoot "..\HjemmeladingApp\.venv\Scripts\python.exe" | Resolve-Path -ErrorAction SilentlyContinue
if ($venvPython) { $python = $venvPython.Path } else { $python = "python" }

$pyInstallerOk = $false
if ($python) {
    try {
        & $python -c "import PyInstaller" 2>$null
        if ($LASTEXITCODE -eq 0) { $pyInstallerOk = $true }
    } catch {
        $pyInstallerOk = $false
    }
}

if (-not $pyInstallerOk -and $appVenvPython) {
    Write-Warning "PyInstaller not available in repo venv. Falling back to HjemmeladingApp venv."
    $python = $appVenvPython.Path
}

Write-Host "Using Python: $python"

# Output log
$buildLog = Join-Path $scriptRoot "..\build_output.log" | Resolve-Path -ErrorAction SilentlyContinue
if (-not $buildLog) { $buildLog = Join-Path $scriptRoot "..\build_output.log" }
$buildErrLog = Join-Path $scriptRoot "..\build_output.err.log" | Resolve-Path -ErrorAction SilentlyContinue
if (-not $buildErrLog) { $buildErrLog = Join-Path $scriptRoot "..\build_output.err.log" }

Write-Host "Build log: $buildLog"

function Test-EnvFlag([string] $value) {
    if (-not $value) { return $false }
    $normalized = $value.ToLowerInvariant()
    return $normalized -in @("1", "true", "yes", "y", "on")
}

function Invoke-BuildLoggedProcess([string[]] $cmd) {
    Write-Host "Running: $($cmd -join ' ')"
    $proc = Start-Process -FilePath $cmd[0] -ArgumentList $cmd[1..($cmd.Length-1)] -NoNewWindow -PassThru -Wait -RedirectStandardOutput $buildLog -RedirectStandardError $buildErrLog
    return $proc.ExitCode
}

function Resolve-InnoSetup {
    $candidate = $env:VALKYRIE_INNO_SETUP_PATH
    if ($candidate -and (Test-Path $candidate)) { return $candidate }
    $cmd = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    $paths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Resolve-SignTool {
    $candidate = $env:VALKYRIE_SIGNTOOL_PATH
    if ($candidate -and (Test-Path $candidate)) { return $candidate }
    $cmd = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    return $null
}

function Invoke-SignTool([string] $filePath) {
    if (-not $filePath -or -not (Test-Path $filePath)) { return $false }
    if (-not $script:signToolPath) {
        Write-Warning "signtool.exe not found. Skipping signing."
        return $false
    }
    $timestampUrl = $script:timestampUrl
    if (-not $timestampUrl) { $timestampUrl = "http://timestamp.digicert.com" }
    $signArgs = @("sign", "/fd", "SHA256", "/tr", $timestampUrl, "/td", "SHA256")
    if ($script:certSha1) {
        $signArgs += "/sha1"; $signArgs += $script:certSha1
    } elseif ($script:certPath) {
        $signArgs += "/f"; $signArgs += $script:certPath
        if ($script:certPassword) { $signArgs += "/p"; $signArgs += $script:certPassword }
    } else {
        Write-Warning "Signing requested but no certificate configured."
        return $false
    }
    $signArgs += $filePath

    Write-Host "Signing $filePath"
    $proc = Start-Process -FilePath $script:signToolPath -ArgumentList $signArgs -NoNewWindow -PassThru -Wait -RedirectStandardOutput $buildLog -RedirectStandardError $buildErrLog
    if ($proc.ExitCode -ne 0) {
        Write-Warning "signtool failed with exit code $($proc.ExitCode)"
        return $false
    }
    return $true
}

# Probe PyQt6 Qt root (Qt6 preferred)
$qtRoot = $null
try {
    $qtRoot = & $python -c "import PyQt6, pathlib, sys; p = pathlib.Path(PyQt6.__file__).resolve().parent / 'Qt6'; sys.stdout.write(str(p))" 2>$null
} catch {
    $qtRoot = $null
}
if (-not $qtRoot -or -not (Test-Path $qtRoot)) {
    try {
        $qtRoot = & $python -c "import PyQt6, pathlib, sys; p = pathlib.Path(PyQt6.__file__).resolve().parent / 'Qt'; sys.stdout.write(str(p))" 2>$null
    } catch {
        $qtRoot = $null
    }
}

$pluginPath = $null
$qtDestRoot = $null
if ($qtRoot -and (Test-Path $qtRoot)) {
    $pluginPath = Join-Path $qtRoot 'plugins'
    $qtRootName = Split-Path $qtRoot -Leaf
    $qtDestRoot = "PyQt6\$qtRootName"
}

if (-not $pluginPath -or -not (Test-Path $pluginPath)) {
    Write-Warning "Could not auto-detect PyQt6 plugin path. Ensure PyQt6 is installed in the active venv."
} else {
    Write-Host "Detected PyQt6 plugins at: $pluginPath"
}

# Prepare add-data entries (relative to project root)
$projectRoot = (Resolve-Path "$scriptRoot\..").Path
$dataJson = Join-Path $projectRoot 'data\demo_weapons.json'
$logoDir = Join-Path $projectRoot 'Logo'
$fontsDir = Join-Path $projectRoot 'HjemmeladingApp\resources\fonts'

$addDataArgs = @()
if (Test-Path $dataJson) { $addDataArgs += "--add-data"; $addDataArgs += "$dataJson;data" }
if (Test-Path $logoDir) { $addDataArgs += "--add-data"; $addDataArgs += "$logoDir;Logo" }
if (Test-Path $fontsDir) { $addDataArgs += "--add-data"; $addDataArgs += "$fontsDir;HjemmeladingApp\resources\fonts" }

# Collect binary/plugin args (Qt bin + plugins + resources)
$addBinaryArgs = @()
if ($qtRoot -and $qtDestRoot) {
    $qtBin = Join-Path $qtRoot 'bin'
    if (Test-Path $qtBin) {
        $addBinaryArgs += "--add-binary"; $addBinaryArgs += "$qtBin;$qtDestRoot\bin"
    }
    if ($pluginPath -and (Test-Path $pluginPath)) {
        $addBinaryArgs += "--add-binary"; $addBinaryArgs += "$pluginPath;$qtDestRoot\plugins"
    }
    $qtResources = Join-Path $qtRoot 'resources'
    if (Test-Path $qtResources) {
        $addBinaryArgs += "--add-binary"; $addBinaryArgs += "$qtResources;$qtDestRoot\resources"
    }
}

Write-Host "Preparing PyInstaller args..."

# Base args
$distRoot = Join-Path $projectRoot 'dist'
$defaultDist = Join-Path $distRoot 'VALKYRIE_BALLISTICS'
if (Test-Path $defaultDist) {
    $distRoot = Join-Path $projectRoot 'dist_smoke'
}

$pyInstallerArgs = @('--onedir','--noconfirm','--name','VALKYRIE_BALLISTICS','--windowed','--log-level=DEBUG','--distpath', $distRoot)

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
$exit = Invoke-BuildLoggedProcess -cmd $cmd
if ($exit -ne 0) {
    Write-Error "PyInstaller failed with exit code $exit. See $buildLog for details."
    exit $exit
}

$signRequested = Test-EnvFlag $env:VALKYRIE_SIGN
$buildInstaller = Test-EnvFlag $env:VALKYRIE_BUILD_INSTALLER

if ($signRequested) {
    $script:signToolPath = Resolve-SignTool
    $script:certPath = $env:VALKYRIE_CERT_PATH
    $script:certPassword = $env:VALKYRIE_CERT_PASSWORD
    $script:certSha1 = $env:VALKYRIE_CERT_SHA1
    $script:timestampUrl = $env:VALKYRIE_TIMESTAMP_URL

    $appExe = Join-Path $distRoot "VALKYRIE_BALLISTICS\VALKYRIE_BALLISTICS.exe"
    Invoke-SignTool $appExe | Out-Null
}

if ($buildInstaller) {
    $iscc = Resolve-InnoSetup
    if (-not $iscc) {
        Write-Warning "Inno Setup not found (ISCC.exe). Skipping installer build."
    } else {
        $env:VALKYRIE_DIST_DIR = Join-Path $distRoot "VALKYRIE_BALLISTICS"
        $installerOut = Join-Path $projectRoot "dist_installer"
        $env:VALKYRIE_INSTALLER_OUT = $installerOut

        $iss = Join-Path $projectRoot "installer\VALKYRIE_BALLISTICS_installer.iss"
        $installerCmd = @($iscc, $iss)
        $installerExitCode = Invoke-BuildLoggedProcess -cmd $installerCmd
        if ($installerExitCode -ne 0) {
            Write-Error "Inno Setup failed with exit code $installerExitCode. See $buildLog for details."
            exit $installerExitCode
        }

        if ($signRequested) {
            $installerExe = Get-ChildItem -Path $installerOut -Filter "*.exe" -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
            if ($installerExe) {
                Invoke-SignTool $installerExe.FullName | Out-Null
            }
        }
    }
}

Write-Host "Build complete. Check '$distRoot\\VALKYRIE_BALLISTICS' and $buildLog for details."
