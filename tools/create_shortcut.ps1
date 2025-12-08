<#
.SYNOPSIS
  Create a Desktop shortcut that launches the app with no console using the repo venv's pythonw.

USAGE
  Run from repository root (PowerShell):
    .\tools\create_shortcut.ps1

This uses COM to create a `.lnk` on the current user's Desktop.
#>
Param()

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPythonw = Join-Path $repoRoot '.venv\Scripts\pythonw.exe'

if (Test-Path $venvPythonw) {
    $target = $venvPythonw
    $arguments = '-m HjemmeladingApp.main'
} else {
    $target = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)?.Source
    if (-not $target) {
        Write-Error "pythonw.exe not found in .venv or on PATH. Activate venv or install Python."
        exit 2
    }
    $arguments = '-m HjemmeladingApp.main'
}

$desktop = [Environment]::GetFolderPath('Desktop')
$linkPath = Join-Path $desktop 'Hjemmelading.lnk'

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($linkPath)
$shortcut.TargetPath = $target
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $repoRoot
$shortcut.WindowStyle = 1
$shortcut.IconLocation = "$target,0"
$shortcut.Save()

Write-Output "Created shortcut: $linkPath"
