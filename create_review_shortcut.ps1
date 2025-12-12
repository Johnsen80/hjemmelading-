# Create a Desktop shortcut that launches the repo's `run_review.ps1`
# Fixed: do not assign to the automatic variable $args

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Desktop = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $Desktop 'Hjemmelading - Review.lnk'

$Shell = New-Object -ComObject WScript.Shell
$PsFile = Join-Path $RepoDir 'run_review.ps1'

if (-not (Test-Path $PsFile)) {
    Write-Warning "Runner script not found at $PsFile. The shortcut will still point to it; ensure the file exists."
}

$Target = "powershell.exe"
$LauncherArguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PsFile`""

$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.Arguments = $LauncherArguments
$Shortcut.WorkingDirectory = $RepoDir

$PythonExe = Join-Path $RepoDir '.venv\Scripts\python.exe'
if (Test-Path $PythonExe) {
    $Shortcut.IconLocation = $PythonExe
} else {
    $Shortcut.IconLocation = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
}

$Shortcut.Save()
Write-Output "Shortcut created at $ShortcutPath"
# Create a Desktop shortcut that launches the review script `run_review.ps1`.
# Run this once from PowerShell (may require ExecutionPolicy to allow script creation).

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'Hjemmelading — Review.lnk'

$target = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$psArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$RepoRoot\run_review.ps1`""

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.Arguments = $psArgs
$shortcut.WorkingDirectory = $RepoRoot
$shortcut.WindowStyle = 1
# optionally set an icon if you have one: $shortcut.IconLocation = "$RepoRoot\Logo\logo.ico"
$shortcut.Save()
Write-Host "Shortcut created at: $shortcutPath"
