# PowerShell launcher for Hjemmelading app (double-click or run from PS)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
Push-Location $PSScriptRoot
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    try {
        & .\.venv\Scripts\Activate.ps1
    } catch {
        Write-Host "Could not source Activate.ps1, continuing to call python directly"
    }
} else {
    Write-Host ".venv\Scripts\Activate.ps1 not found"
}
python .\main.py $args
Pop-Location
Pause
