$Wsh = New-Object -ComObject WScript.Shell
$desk = [System.IO.Path]::Combine($env:USERPROFILE, 'Desktop')
$lnkPath = [System.IO.Path]::Combine($desk, 'Valkyrie Ballistics.lnk')
$sc = $Wsh.CreateShortcut($lnkPath)
$sc.TargetPath = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\run_valkyrie.bat'
$sc.WorkingDirectory = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading'
$icon = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\Logo\logo.ico'
if (Test-Path $icon) { $sc.IconLocation = $icon } else { $sc.IconLocation = 'C:\Windows\System32\shell32.dll,1' }
$sc.Save()
# remove old shortcut if present
$old = [System.IO.Path]::Combine($desk, 'Hjemmelading.lnk')
if (Test-Path $old) { Remove-Item -Force $old }
Write-Output "Created shortcut: $lnkPath"
