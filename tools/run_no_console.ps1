<#
.SYNOPSIS
  Launch the application without a console window using the project's venv pythonw.

USAGE
  From repository root in PowerShell:
    .\tools\run_no_console.ps1

This script prefers `.venv\Scripts\pythonw.exe` in the repo. If it doesn't
exist it falls back to `pythonw.exe` on PATH.
#>
Param()

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPythonw = Join-Path $repoRoot '.venv\Scripts\pythonw.exe'

if (Test-Path $venvPythonw) {
    $exe = $venvPythonw
} else {
    $exe = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)?.Source
}

if (-not $exe) {
    Write-Error "pythonw.exe not found in .venv or on PATH. Activate venv or install Python."
    exit 2
}

$args = '-m', 'HjemmeladingApp.main'

# Start the process detached
Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -WorkingDirectory $repoRoot
Write-Output "Started app with $exe"