@echo off
set QT_DEBUG_PLUGINS=1
set QT_QPA_PLATFORM=offscreen
set HEADLESS=1
"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\tools\dist_onedir\VALKYRIE_BALLISTICS_DIR\VALKYRIE_BALLISTICS_DIR.exe" > "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\onedir_stdout.log" 2> "C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\logs\onedir_err.log"
echo DONE
