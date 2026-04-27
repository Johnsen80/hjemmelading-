$exe = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\dist\VALKYRIE_BALLISTICS\VALKYRIE_BALLISTICS.exe'
$log = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\exe_smoke.log'
Add-Content -Path $log -Value "=== Smoke run at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
$env:QT_QPA_PLATFORM = 'offscreen'
$env:HEADLESS = '1'
$env:QT_DEBUG_PLUGINS = '1'
if (!(Test-Path $exe)) {
    Add-Content -Path $log -Value "EXE not found: $exe"
    exit 2
}
$p = Start-Process -FilePath $exe -PassThru -ErrorAction SilentlyContinue
if ($null -eq $p) { Add-Content -Path $log -Value 'Failed to start process'; exit 1 }
Add-Content -Path $log -Value ("Started PID:{0}" -f $p.Id)
$timeout = 60
$sw = [Diagnostics.Stopwatch]::StartNew()
while ($sw.Elapsed.TotalSeconds -lt $timeout -and -not $p.HasExited) { Start-Sleep -Milliseconds 500 }
if (-not $p.HasExited) {
    Add-Content -Path $log -Value ("Timeout after {0}s; killing process" -f $timeout)
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    Add-Content -Path $log -Value 'Process killed'
} else {
    Add-Content -Path $log -Value ("Process exited; ExitCode:{0}" -f $p.ExitCode)
}
