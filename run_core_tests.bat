@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.github\.tool-venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo Fant ikke test-runner: "%PYTHON%"
  exit /b 1
)

"%PYTHON%" -m pytest -q -m core %*
