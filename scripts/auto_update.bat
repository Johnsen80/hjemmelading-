@echo off
REM Simple auto-update script for Hjemmelading
REM Checks for new release on GitHub and downloads installer if newer

setlocal
set REPO=https://github.com/bjjoh/Hjemmelading/releases/latest
set INSTALLER=VALKYRIE_BALLISTICS_installer.exe
set LOCAL_VERSION=1.0.0

REM Fetch latest version info
curl -s %REPO% > latest_release.html
for /f "tokens=2 delims=\"" %%a in ('findstr /C:"tag/" latest_release.html') do set REMOTE_VERSION=%%a

REM Compare versions (simple string match)
if "%REMOTE_VERSION%"=="%LOCAL_VERSION%" (
    echo Already up to date: %LOCAL_VERSION%
    goto end
) else (
    echo New version found: %REMOTE_VERSION%
    REM Download installer
    curl -L %REPO%/download/%INSTALLER% -o %INSTALLER%
    echo Installer downloaded: %INSTALLER%
    REM Optionally run installer
    REM start %INSTALLER%
)

:end
endlocal
