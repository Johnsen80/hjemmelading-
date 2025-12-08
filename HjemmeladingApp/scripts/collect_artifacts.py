import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
ART.mkdir(exist_ok=True)


def run_cmd(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + "\n" + p.stderr


def main():
    tests_rc, tests_out = run_cmd([sys.executable, "-m", "pytest", "-q"])
    (ART / "pytest.txt").write_text(tests_out)

    ruff_rc, ruff_out = run_cmd([sys.executable, "-m", "ruff", "check", "."])
    (ART / "ruff.txt").write_text(ruff_out)

    print("Wrote artifacts to", ART)
    return 0 if tests_rc == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
