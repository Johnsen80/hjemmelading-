$env:QT_DEBUG_PLUGINS='1'
Remove-Item env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
Remove-Item env:HEADLESS -ErrorAction SilentlyContinue
$exe = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\dist\VALKYRIE_BALLISTICS\VALKYRIE_BALLISTICS.exe'
if (-not (Test-Path $exe)) { Write-Host "EXE not found: $exe"; exit 2 }
$p = Start-Process -FilePath $exe -PassThru
Write-Host "Started pid $($p.Id)"
if (-not (Wait-Process -Id $p.Id -Timeout 20)) { Write-Host 'Timeout, leaving process running' } else { Write-Host 'Process exited' } 
