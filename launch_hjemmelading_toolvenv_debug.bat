@echo off
setlocal
cd /d "%~dp0"
set "PY=%~dp0HjemmeladingApp\.venv\Scripts\python.exe"
set "APP=%~dp0main.py"
if not exist "%PY%" (
    echo Fant ikke python.exe i HjemmeladingApp\.venv
    pause
    exit /b 1
)
if not exist "%APP%" (
    echo Fant ikke main.py
    pause
    exit /b 1
)
"%PY%" "%APP%"
set "RC=%ERRORLEVEL%"
echo.
echo Programmet avsluttet med kode %RC%.
pause
exit /b %RC%
