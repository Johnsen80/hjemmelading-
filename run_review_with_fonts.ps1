# Start the review runner with QT fonts sourced from Windows Fonts
# Usage: double-click or run from PowerShell
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoDir

# Prefer system fonts (DejaVu or Windows fonts). Qt looks here when QT_QPA_FONTDIR is set.
$QtFontDir = Join-Path $env:WINDIR 'Fonts'
if (Test-Path $QtFontDir) {
    $env:QT_QPA_FONTDIR = $QtFontDir
    Write-Output "Set QT_QPA_FONTDIR=$QtFontDir"
} else {
    Write-Warning "System font folder not found: $QtFontDir. If you still see font warnings, consider installing DejaVu fonts into a project folder and set QT_QPA_FONTDIR accordingly."
}

# Activate .venv if present
$VenvActivate = Join-Path $RepoDir ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
}

# Run the Python runner directly
$RunnerPy = Join-Path $RepoDir "tools\run_review.py"
if (Test-Path $RunnerPy) {
    & python $RunnerPy
} else {
    Write-Error "Runner not found: $RunnerPy"
}
