# Kill any running VALKYRIE_BALLISTICS processes
Get-Process -Name VALKYRIE_BALLISTICS* -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Output "Killing PID:$($_.Id) $($_.ProcessName)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

$py = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\.tool-venv\Scripts\python.exe'
New-Item -Path 'tools/logs' -ItemType Directory -Force | Out-Null
$env:QT_DEBUG_PLUGINS = '1'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:HEADLESS = '1'
$stdout = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\pyentry_stdout.log'
$stderr = 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\pyentry_err.log'

Write-Output "Starting $py main.py (logs -> $stdout, $stderr)"
$p = Start-Process -FilePath $py -ArgumentList 'main.py' -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WorkingDirectory 'C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading' -PassThru

if (-not (Wait-Process -Id $p.Id -Timeout 120)) {
    Write-Output "Timeout, killing $($p.Id)"
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
} else {
    Write-Output 'Process exited normally'
}

Write-Output '--- STDOUT (tail 200) ---'
Get-Content -Path $stdout -Tail 200 -ErrorAction SilentlyContinue
Write-Output '--- STDERR (tail 200) ---'
Get-Content -Path $stderr -Tail 200 -ErrorAction SilentlyContinue
