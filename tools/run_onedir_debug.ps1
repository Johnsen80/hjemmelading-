$dist = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\tools\dist_onedir\VALKYRIE_BALLISTICS_DIR.exe'
New-Item -Path 'tools/logs' -ItemType Directory -Force | Out-Null
$env:QT_DEBUG_PLUGINS = '1'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:HEADLESS = '1'
$stdout = 'tools/logs/onedir_stdout.log'
$stderr = 'tools/logs/onedir_err.log'
$proc = Start-Process -FilePath $dist -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
if (-not (Wait-Process -Id $proc.Id -Timeout 120)) {
    Write-Output "Timeout, killing $($proc.Id)"
    Stop-Process -Id $proc.Id -Force
} else {
    Write-Output "Process exited normally"
}
Write-Output "--- STDOUT (tail 200) ---"
Get-Content -Path $stdout -Tail 200 -ErrorAction SilentlyContinue
Write-Output "--- STDERR (tail 200) ---"
Get-Content -Path $stderr -Tail 200 -ErrorAction SilentlyContinue
