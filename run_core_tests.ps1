$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".github\.tool-venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Fant ikke test-runner: $python"
}

& $python -m pytest -q -m core @Args
