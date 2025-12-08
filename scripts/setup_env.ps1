# Setup script for Windows development environment
# Usage: Right-click -> Run with PowerShell (or run in an elevated prompt if needed)
# This script creates a virtual environment and installs requirements from requirements.txt

param(
    [string]$venvName = ".venv"
)

Write-Host "Creating virtual environment in '$venvName'..."
python -m venv $venvName
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create virtual environment. Ensure Python is installed and on PATH."
    exit 1
}

Write-Host "Activating virtual environment..."
# Use the PowerShell activation script path
$activate = Join-Path -Path $venvName -ChildPath "Scripts\Activate.ps1"
if (-Not (Test-Path $activate)) {
    Write-Error "Activation script not found at $activate"
    exit 1
}

Write-Host "Installing/Upgrading pip, setuptools and wheel..."
& $activate; python -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upgrade pip. See errors above."
    exit 1
}

Write-Host "Installing requirements from requirements.txt (may take a while)..."
& $activate; pip install -r "requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Some packages failed to install. Common fixes: install Microsoft Visual C++ Redistributable and try again, or use Miniconda for heavy numeric packages."
    Write-Host "Microsoft visual c++ redistributable: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist"
    exit 0
}

Write-Host "Setup complete. Activate the venv with:`n    .\$venvName\Scripts\Activate.ps1`"}]}{