# Run the quick review UI for Valkyrie Ballistics (Weapon Profile Editor)
# Usage: Right-click -> Run with PowerShell, or create a shortcut to this script.

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
# Activate venv if present
$VenvActivate = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    try {
        & $VenvActivate
    } catch {
        Write-Host "Failed to activate venv: $_"
    }
}
# Ensure repo is on PYTHONPATH for module imports
$env:PYTHONPATH = $RepoRoot
# Run the runner
python (Join-Path $RepoRoot "tools\run_review.py")
