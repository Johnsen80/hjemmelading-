param(
    [string]$PythonExe = "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\.tool-venv\Scripts\python.exe",
    [string]$ProjectRoot = "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading",
    [string]$PluginDir = "C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe"
)

$ErrorActionPreference = "Stop"

$logPath = Join-Path $PluginDir "probe_log.jsonl"
$healthTool = Join-Path $ProjectRoot "tools\check_gordon_plugin_health.py"

if (Test-Path $logPath) {
    Remove-Item -Force $logPath
}

& $PythonExe $healthTool
