<#
Helper to run the headless smoke test.
Usage:
  .\tools\run_smoke.ps1          # finds venv/python and runs the smoke test
  .\tools\run_smoke.ps1 -CreateVenv  # will attempt to create .venv if missing (requires 'python' on PATH)
#>

param(
    [switch]$CreateVenv
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Project root: $root"

$candidates = @(
    "$root\\.venv\\Scripts\\python.exe",
    "$root\\venv\\Scripts\\python.exe",
    "$root\\.venv\\Scripts\\python3.exe",
    "$root\\venv\\Scripts\\python3.exe"
)

$python = $null
foreach ($c in $candidates) {
    if (Test-Path $c) {
        $python = $c
        break
    }
}

if (-not $python) {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { $python = $pyCmd.Source }
}

if (-not $python) {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) { $python = $pyCmd.Source }
}

if (-not $python -and $CreateVenv) {
    Write-Host "Creating virtualenv at $root\.venv (requires 'python' on PATH)"
    try {
        & python -m venv "$root\.venv"
        $candidate = "$root\\.venv\\Scripts\\python.exe"
        if (Test-Path $candidate) { $python = $candidate }
    } catch {
        Write-Warning "Failed to create venv: $_"
    }
}

if (-not $python) {
    Write-Error "No Python interpreter found. Provide a venv or install Python and retry."
    exit 1
}

Write-Host "Using Python: $python"

# Run the headless smoke test and forward any args
& $python "$root\tools\headless_smoke_test.py" @Args

exit $LASTEXITCODE
