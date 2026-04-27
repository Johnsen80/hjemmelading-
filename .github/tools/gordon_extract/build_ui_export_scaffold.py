from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / ".github" / "tmp" / "gordon_extract"


POWERSHELL_SCAFFOLD = r"""param(
    [string]$GordonExe = "C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool.exe"
)

$ErrorActionPreference = "Stop"

Write-Host "Gordon UI export scaffold"
Write-Host "Dette scriptet er foreløpig en hybrid/manual scaffold."
Write-Host "Mål: systematisere eksport av projectile/propellant/caliber hvis plugin-sporet ikke starter."

if (-not (Test-Path $GordonExe)) {
    throw "Fant ikke Gordon exe: $GordonExe"
}

Write-Host "1. Starter Gordon..."
Start-Process $GordonExe

Write-Host "2. Når Gordon er oppe:"
Write-Host "   - åpne Projectile Database"
Write-Host "   - test om hele listen kan eksporteres eller om vi må eksportere i batches"
Write-Host "   - gjør det samme for Propellant Database"
Write-Host "   - gjør det samme for Caliber Database"

Write-Host "3. Legg eksportene i en mappe og kjør så:"
Write-Host '   .github\tools\ingest_gordon_export_folder.py --source-root "<eksportmappe>"'

Write-Host ""
Write-Host "TODO for full automatisering:"
Write-Host " - identifisere faktiske menyaksesser / hurtigtaster i Gordon"
Write-Host " - styre vinduet med SendKeys eller annet Windows UI-lag"
Write-Host " - lagre eksportene i en dedikert output-mappe"
"""


README = """# Gordon UI Export Scaffold

Dette er fallback-sporet hvis plugin/API ikke starter eller ikke gir tilgang til databaseinnholdet.

Output:
- `gordon_ui_export_scaffold.ps1`

Tanken er å gjøre dette til et PowerShell-basert hybrid- eller helautomatisk eksportløp for:
- projectile
- propellant
- caliber

Foreløpig er dette en scaffold, ikke en ferdig automatisk eksport.
"""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "gordon_ui_export_scaffold.ps1").write_text(
        POWERSHELL_SCAFFOLD, encoding="utf-8"
    )
    (OUT_DIR / "gordon_ui_export_scaffold_README.md").write_text(
        README, encoding="utf-8"
    )
    print(OUT_DIR / "gordon_ui_export_scaffold.ps1")
    print(OUT_DIR / "gordon_ui_export_scaffold_README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
