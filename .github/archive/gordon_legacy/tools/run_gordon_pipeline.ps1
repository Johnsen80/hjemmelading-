param(
    [string]$PythonExe = "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\.tool-venv\Scripts\python.exe",
    [string]$ProjectRoot = "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading",
    [string]$DumpDir = "C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe\dumps",
    [switch]$SkipMeasurementSeed,
    [switch]$SkipDumpImport,
    [switch]$SkipGRTraceImport,
    [switch]$SkipPressureTraceImport,
    [switch]$SkipInventory
)

$ErrorActionPreference = "Stop"

$exportDir = Join-Path $ProjectRoot "data\gordon_temp_extract"
$measurementTool = Join-Path $ProjectRoot "tools\import_gordon_measurement_profiles.py"
$dumpTool = Join-Path $ProjectRoot "tools\import_gordon_dumps.py"
$grtraceTool = Join-Path $ProjectRoot "tools\import_gordon_grtrace.py"
$pressureTraceTool = Join-Path $ProjectRoot "tools\import_gordon_pressuretrace_grtloads.py"
$healthTool = Join-Path $ProjectRoot "tools\check_gordon_plugin_health.py"
$statusTool = Join-Path $ProjectRoot "tools\gordon_status_report.py"
$inventoryTool = Join-Path $ProjectRoot "tools\gordon_source_inventory.py"
$qualityTool = Join-Path $ProjectRoot "tools\gordon_data_quality_report.py"

& $PythonExe $healthTool

if (-not $SkipMeasurementSeed) {
    & $PythonExe $measurementTool --import-db --seed-grt-data
}

if (-not $SkipDumpImport) {
    & $PythonExe $dumpTool --dump-dir $DumpDir --export-dir $exportDir --import-db
}

if (-not $SkipGRTraceImport) {
    & $PythonExe $grtraceTool
}

if (-not $SkipPressureTraceImport) {
    & $PythonExe $pressureTraceTool
}

if (-not $SkipInventory) {
    & $PythonExe $inventoryTool
    & $PythonExe $qualityTool
}

& $PythonExe $statusTool
