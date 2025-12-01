param(
    [string]$TargetPath = '',
    [string]$ShortcutName = 'VALKYRIE BALLISTICS.lnk',
    [string]$IconPath = ''
)

Set-Location (Join-Path $PSScriptRoot '..')

if ([string]::IsNullOrWhiteSpace($TargetPath)) {
    $exePath = Join-Path (Get-Location) 'dist\VALKYRIE_BALLISTICS\VALKYRIE_BALLISTICS.exe'
    if (Test-Path $exePath) { $TargetPath = $exePath } else { Write-Error 'Built exe not found. Build first.'; exit 1 }
}

# Prepare icon path if not provided
if ([string]::IsNullOrWhiteSpace($IconPath)) {
    $possibleIco = Join-Path (Get-Location) 'Logo\logo.ico'
    if (Test-Path $possibleIco) { $IconPath = $possibleIco }
}

$wsh = New-Object -ComObject WScript.Shell
$startMenu = [Environment]::GetFolderPath('Programs')
$appFolder = Join-Path $startMenu 'VALKYRIE BALLISTICS'
if (-not (Test-Path $appFolder)) { New-Item -Path $appFolder -ItemType Directory | Out-Null }
$shortcutPath = Join-Path $appFolder $ShortcutName
$lnk = $wsh.CreateShortcut($shortcutPath)
$lnk.TargetPath = $TargetPath
$lnk.WorkingDirectory = Split-Path $TargetPath
if (-not [string]::IsNullOrWhiteSpace($IconPath) -and (Test-Path $IconPath)) { $lnk.IconLocation = $IconPath } else { $lnk.IconLocation = $TargetPath }
$lnk.Save()
Write-Host "Start Menu shortcut created: $shortcutPath"