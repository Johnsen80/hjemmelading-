@echo off
cd /d "%~dp0"
set "PY=%~dp0.venv\Scripts\pythonw.exe"
if exist "%PY%" (
	start "" "%PY%" "%~dp0main.py"
) else (
	start "" pythonw "%~dp0main.py"
)
