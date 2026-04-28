@echo off
setlocal
cd /d "%~dp0"
set "PYW=%~dp0HjemmeladingApp\.venv\Scripts\pythonw.exe"
set "APP=%~dp0main.py"
if not exist "%PYW%" (
    echo Fant ikke pythonw.exe i HjemmeladingApp\.venv
    pause
    exit /b 1
)
if not exist "%APP%" (
    echo Fant ikke main.py
    pause
    exit /b 1
)
start "" "%PYW%" "%APP%"
exit /b 0
