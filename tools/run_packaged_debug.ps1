$exe = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\dist\VALKYRIE_BALLISTICS\VALKYRIE_BALLISTICS.exe'
New-Item -Path 'tools/logs' -ItemType Directory -Force | Out-Null
$env:QT_DEBUG_PLUGINS = '1'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:HEADLESS = '1'
$out = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\exe_afterdb_stdout.log'
$err = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\exe_afterdb_err.log'
Write-Output "Starting $exe (logs -> $out, $err)"
$p = Start-Process -FilePath $exe -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
if (-not (Wait-Process -Id $p.Id -Timeout 120)) {
    Write-Output "Timeout, killing $($p.Id)"
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
} else {
    Write-Output 'Process exited normally'
}
Write-Output '--- STDOUT (tail 200) ---'
Get-Content -Path $out -Tail 200 -ErrorAction SilentlyContinue
Write-Output '--- STDERR (tail 200) ---'
Get-Content -Path $err -Tail 200 -ErrorAction SilentlyContinue
