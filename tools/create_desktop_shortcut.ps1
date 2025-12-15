$WshShell = New-Object -ComObject WScript.Shell
$desktop = [System.IO.Path]::Combine($env:USERPROFILE, 'Desktop')
$scPath = [System.IO.Path]::Combine($desktop, 'Valkyrie Ballistics.lnk')
$sc = $WshShell.CreateShortcut($scPath)
$sc.TargetPath = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\run_valkyrie.bat'
$sc.WorkingDirectory = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading'
# Prefer project-provided ICO if present
$icon = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\Logo\logo.ico'
if (Test-Path $icon) { $sc.IconLocation = $icon } else { $sc.IconLocation = 'C:\Windows\System32\shell32.dll,1' }
$sc.Save()
Write-Output "Created shortcut: $scPath"
