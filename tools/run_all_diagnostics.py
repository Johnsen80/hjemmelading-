"""Run all diagnostics that help investigate 'no window' startup issues.

This script will:
- Write Python/venv info to `tools/venv_check.txt`
- Attempt to import PyQt6 and write version info to `tools/pyqt_check.txt`
- Run `tools/gui_test.py` and `tools/run_weapon_editor.py`, capturing their stdout/stderr to logs
- Run `tools/startup_check.py` which checks key imports

Run from project root with venv active:
  & .\.venv\Scripts\Activate.ps1
  & .\.venv\Scripts\python.exe .\tools\run_all_diagnostics.py

Then attach the contents of the generated files under `tools/`.
"""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent

def run(cmd, outpath):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    out, _ = p.communicate()
    outpath.write_bytes(out)
    return p.returncode

def main():
    # venv / python info
    venv_log = root / 'venv_check.txt'
    run([sys.executable, '-c', "import sys; print('PYTHON_EXE:', sys.executable); print('PYTHON_VER:', sys.version)"], venv_log)

    # pip list
    run([sys.executable, '-m', 'pip', '--version'], root / 'pip_version.txt')
    run([sys.executable, '-m', 'pip', 'list'], root / 'pip_list.txt')

    # PyQt check
    pyqt_log = root / 'pyqt_check.txt'
    run([sys.executable, '-c', "import PyQt6, sys; from PyQt6 import QtCore; print('PyQt6', getattr(PyQt6,'__version__','?')); print('QT', getattr(QtCore,'QT_VERSION_STR','?'))"], pyqt_log)

    # Startup import check
    run([sys.executable, str(root / 'startup_check.py')], root / 'startup_import_check.txt')

    # GUI test
    run([sys.executable, str(root / 'gui_test.py')], root / 'gui_test_log.txt')

    # Weapon editor runner
    run([sys.executable, str(root / 'run_weapon_editor.py')], root / 'run_weapon_editor.log')

    print('Diagnostics complete. Check the tools/ folder for logs: venv_check.txt, pyqt_check.txt, gui_test_log.txt, run_weapon_editor.log, startup_import_check.txt')

if __name__ == '__main__':
    main()
