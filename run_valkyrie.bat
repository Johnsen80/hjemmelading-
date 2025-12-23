@echo off
REM Run Valkyrie Ballistics app using repo venv (double-clickable)
pushd "%~dp0"
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo Virtualenv activate script not found at .venv\Scripts\activate.bat
)
python HjemmeladingApp\main.py %*
popd
pause
