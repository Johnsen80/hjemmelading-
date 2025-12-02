import subprocess
import sys
import os


def test_profile_editor_import_smoke():
    # Run the headless smoke script and ensure it reports LAST_ERROR (exit code 0)
    script = os.path.join(os.path.dirname(__file__), "..", "tools", "run_settings_smoke.py")
    script = os.path.abspath(script)
    res = subprocess.run([sys.executable, script], capture_output=True, text=True)
    # Print outputs to help debugging in CI
    print(res.stdout)
    print(res.stderr)
    assert res.returncode == 0
    assert "LAST_ERROR:" in res.stdout
