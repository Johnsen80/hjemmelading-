# Create a Desktop shortcut to run `run_review_with_fonts.ps1`
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Desktop = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $Desktop 'Hjemmelading - Review (fonts).lnk'

$Shell = New-Object -ComObject WScript.Shell
$PsFile = Join-Path $RepoDir 'run_review_with_fonts.ps1'

if (-not (Test-Path $PsFile)) {
    Write-Warning "Runner script not found at $PsFile. The shortcut will still point to it; ensure the file exists."
}

$Target = "powershell.exe"
$Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PsFile`""

$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.Arguments = $Arguments
$Shortcut.WorkingDirectory = $RepoDir

$PythonExe = Join-Path $RepoDir '.venv\Scripts\python.exe'
if (Test-Path $PythonExe) {
    $Shortcut.IconLocation = $PythonExe
} else {
    $Shortcut.IconLocation = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
}

$Shortcut.Save()
Write-Output "Shortcut created at $ShortcutPath"