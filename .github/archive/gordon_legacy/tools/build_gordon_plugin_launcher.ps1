param(
    [string]$ProjectRoot = "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading",
    [string]$PythonExe = "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\.tool-venv\Scripts\python.exe",
    [string]$PyInstallerExe = "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\.tool-venv\Scripts\pyinstaller.exe",
    [string]$PluginDir = "C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe"
)

$ErrorActionPreference = "Stop"

$tmpRoot = Join-Path $ProjectRoot ".github\tmp"
$launcherPy = Join-Path $tmpRoot "gordon_plugin_launcher.py"
$distDir = Join-Path $tmpRoot "dist_gordon_plugin_dir"
$buildDir = Join-Path $tmpRoot "build_gordon_plugin_dir"
$specDir = $tmpRoot
$builtLauncherDir = Join-Path $distDir "gordon_plugin_launcher"
$targetLauncherDir = Join-Path $PluginDir "launcher"

if (Test-Path $distDir) {
    Remove-Item -Recurse -Force $distDir
}
if (Test-Path $buildDir) {
    Remove-Item -Recurse -Force $buildDir
}
if (Test-Path $targetLauncherDir) {
    Remove-Item -Recurse -Force $targetLauncherDir
}

& $PyInstallerExe `
  -y `
  --onedir `
  --distpath $distDir `
  --workpath $buildDir `
  --specpath $specDir `
  $launcherPy

Copy-Item -Recurse -Force $builtLauncherDir $targetLauncherDir

Write-Host "Launcher built and copied to: $targetLauncherDir"
