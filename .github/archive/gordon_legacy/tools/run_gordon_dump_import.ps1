param(
    [string]$DumpDir = "C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe\dumps",
    [string]$ExportDir = "",
    [switch]$ImportDb
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".github\.tool-venv\Scripts\python.exe"
$script = Join-Path $repoRoot "tools\import_gordon_dumps.py"

if (-not (Test-Path $python)) {
    throw "Fant ikke Python-miljo: $python"
}

if (-not (Test-Path $script)) {
    throw "Fant ikke importscript: $script"
}

if ([string]::IsNullOrWhiteSpace($ExportDir)) {
    $ExportDir = Join-Path $repoRoot "data\gordon_temp_extract"
}

$args = @(
    $script,
    "--dump-dir", $DumpDir,
    "--export-dir", $ExportDir
)

if ($ImportDb) {
    $args += "--import-db"
}

Write-Host "Python:" $python
Write-Host "DumpDir:" $DumpDir
Write-Host "ExportDir:" $ExportDir
if ($ImportDb) {
    Write-Host "DB-import: enabled"
} else {
    Write-Host "DB-import: disabled"
}

& $python @args
