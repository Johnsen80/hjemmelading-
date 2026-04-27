$env:QT_DEBUG_PLUGINS = '1'
$env:HEADLESS = '1'
$env:QT_QPA_PLATFORM = 'offscreen'
$exe = Join-Path $PSScriptRoot '..\dist\VALKYRIE_BALLISTICS\VALKYRIE_BALLISTICS.exe'
$out = Join-Path $PSScriptRoot 'logs\onedir_run_stdout.log'
$err = Join-Path $PSScriptRoot 'logs\onedir_run_err.log'
$p = Start-Process -FilePath $exe -PassThru -NoNewWindow -RedirectStandardOutput $out -RedirectStandardError $err
Write-Host "Started pid $($p.Id)"
$dump = Join-Path $env:TEMP 'hjemmelading_hang_trace.log'
$found = $false
$maxWait = 120
for ($i=0; $i -lt $maxWait; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $dump) { 
        $ts = Get-Date -Format yyyyMMdd_HHmmss
        $dest = Join-Path $PSScriptRoot "logs\hang_trace_$ts.log"
        Copy-Item $dump $dest -Force
        Write-Host "Found dump, copied to $dest"
        $found = $true
        break
    }
}
if (-not $found) { Write-Host "No dump found after $maxWait seconds" }
# Give process a few seconds then kill if still alive
Start-Sleep -Seconds 2
try {
    $p.Refresh()
    # Copy per-user startup trace into workspace logs if present
    try {
        if ($env:LOCALAPPDATA) {
            $userTrace = Join-Path $env:LOCALAPPDATA "Hjemmelading\logs\startup_trace.log"
            if (Test-Path $userTrace) {
                $destTrace = Join-Path $PSScriptRoot "logs\startup_trace_from_app.log"
                Copy-Item $userTrace $destTrace -Force -ErrorAction SilentlyContinue
            }
        }
    } catch { }
    if (-not $p.HasExited) { $p.Kill(); Write-Host "Killed process" }
} catch { }
Write-Host "Done"