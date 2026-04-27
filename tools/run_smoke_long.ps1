$exe = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\dist\VALKYRIE_BALLISTICS\VALKYRIE_BALLISTICS.exe'
$out = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\exe_smoke.log'
$err = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\exe_smoke.err.log'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:HEADLESS = '1'
if (-not (Test-Path $exe)) {
    Write-Output "EXE_MISSING: $exe"
    exit 2
}
Remove-Item -Path $out,$err -Force -ErrorAction SilentlyContinue
$p = Start-Process -FilePath $exe -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
Write-Output "Started PID:$($p.Id)"
if (Wait-Process -Id $p.Id -Timeout 120) {
    Write-Output 'Process exited normally'
} else {
    Write-Output 'Timeout after 120s; killing process'
    Stop-Process -Id $p.Id -Force
    Write-Output 'Process killed'
}
Write-Output "\n=== STDOUT (last 200 lines) ==="
Get-Content $out -ErrorAction SilentlyContinue | Select-Object -Last 200
Write-Output "\n=== STDERR (last 200 lines) ==="
Get-Content $err -ErrorAction SilentlyContinue | Select-Object -Last 200
