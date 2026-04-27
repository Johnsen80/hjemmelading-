param(
    [string]$PythonVersion = "3.11",
    [switch]$IncludePySide6
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
$toolVenv = Join-Path $repoRoot ".github\.tool-venv"
$requirementsPath = Join-Path $repoRoot "HjemmeladingApp\requirements-dev.txt"

Write-Host "Rebuilding tool environment at $toolVenv with Python $PythonVersion"

if (Test-Path $toolVenv) {
    Remove-Item -Recurse -Force $toolVenv
}

& py "-$PythonVersion" -m venv $toolVenv

$pythonExe = Join-Path $toolVenv "Scripts\python.exe"
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r $requirementsPath

$packages = @(
    "PyQt6",
    "pillow",
    "mypy",
    "types-Pillow",
    "types-requests"
)

if ($IncludePySide6) {
    $packages += "PySide6"
}

& $pythonExe -m pip install @packages

Write-Host "Tool environment rebuilt successfully."
Write-Host "Interpreter: $pythonExe"