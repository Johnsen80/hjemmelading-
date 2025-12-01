#!/usr/bin/env python3
"""Archived debug script: create desktop shortcut via PowerShell and log result.

Moved to `tools/archive` after verification. Keep for reference; safe to delete later.
"""
import json
import subprocess
from pathlib import Path
import sys


def main():
    project = Path(__file__).resolve().parents[2]
    desktop = subprocess.check_output(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"]).decode(errors='ignore').strip()
    venv_pythonw = project / ".venv" / "Scripts" / "pythonw.exe"
    if venv_pythonw.exists():
        target = str(venv_pythonw)
    else:
        # fallback to system pythonw or python
        try:
            target = subprocess.check_output(["powershell","-NoProfile","-Command","(Get-Command pythonw -ErrorAction SilentlyContinue).Source"]).decode().strip()
        except Exception:
            target = ""
        if not target:
            try:
                target = subprocess.check_output(["powershell","-NoProfile","-Command","(Get-Command python -ErrorAction SilentlyContinue).Source"]).decode().strip()
            except Exception:
                target = ""

    main_py = project / "HjemmeladingApp" / "main.py"
    lnk_path = Path(desktop) / "HJEMMELADING.lnk"

    ps = f"$s=New-Object -ComObject WScript.Shell; $lnk=$s.CreateShortcut('{lnk_path}'); $lnk.TargetPath='{target}'; $lnk.Arguments='\"{main_py}\"'; $lnk.WorkingDirectory='{project}'; $lnk.Description='HJEMMELADING - Tactical Reloading System'; $lnk.Save(); Write-Output 'OK'"

    log = {
        "project": str(project),
        "desktop": desktop,
        "target_used": target,
        "main_py": str(main_py),
        "lnk_path": str(lnk_path),
    }

    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=10)
        log["returncode"] = res.returncode
        log["stdout"] = res.stdout.strip()
        log["stderr"] = res.stderr.strip()
    except Exception as e:
        log["exception"] = str(e)

    outfile = project / "tools" / "shortcut_creation_debug.json"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(json.dumps(log, indent=2, ensure_ascii=False))

    print(json.dumps(log, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
