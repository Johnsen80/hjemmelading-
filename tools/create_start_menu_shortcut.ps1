# Create a Start Menu shortcut for Valkyrie Ballistics
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptRoot '..')).Path
$target = Join-Path $repoRoot 'run_valkyrie.bat'
$icon = Join-Path $repoRoot 'Logo\logo.ico'
$programs = [Environment]::GetFolderPath('Programs')
$scPath = Join-Path $programs 'Valkyrie Ballistics.lnk'

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($scPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $repoRoot
if (Test-Path $icon) { $sc.IconLocation = $icon } else { $sc.IconLocation = "$target,0" }
$sc.Save()
Write-Output "Created Start-menu shortcut: $scPath"
