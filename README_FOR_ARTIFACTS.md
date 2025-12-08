# Hjemmelading — Branch artifacts and restore instructions

This repository snapshot and patch-set were exported from your local branch `refactor/long-lines`.

Artifacts created (relative to the machine that created them):

- Git bundle: `../refactor-long-lines.bundle`
- Patch set directory: `../refactor_patches/` (many `0001-*.patch` ..)

Quick restore steps (PowerShell):

```powershell
# In a fresh or existing clone
# Add remote if missing
# git remote add origin <git-remote-url>
# Fetch branch from bundle and check it out
git fetch C:\Users\bjjoh\OneDrive\Dokumenter\Programering\refactor-long-lines.bundle refactor/long-lines
git checkout -b refactor/long-lines FETCH_HEAD
# Push to your origin (requires credentials/access)
git push origin refactor/long-lines
```

Or apply the patch set inside an existing repo clone:

```powershell
# From the repo root (base branch e.g. master/main)
git checkout -b refactor/long-lines
git am C:\Users\bjjoh\OneDrive\Dokumenter\Programering\refactor_patches\*.patch
# Resolve any conflicts, then push
git push origin refactor/long-lines
```

Running tests (headless baseline):

The branch has many GUI modules that import `PyQt6` at module scope. For a headless CI baseline, run pytest while ignoring files that import `PyQt6`.

Example (PowerShell):

```powershell
& ".github/.tool-venv/Scripts/Activate.ps1"
$paths = Select-String -Path "*.py","src/**/.py","HjemmeladingApp/**/.py","tests/**/.py","tools/**/.py" -Pattern 'from PyQt6' -List | Select-Object -Expand Path -Unique
$ignores = $paths | ForEach-Object { "--ignore=\"$_\"" }
$args = if ($ignores) { $ignores -join ' ' } else { '' }
python -m pytest -q --disable-warnings --maxfail=1 --ignore=bundle_publish $args
```

If you want to run GUI tests, install PyQt6 in the environment (see `requirements-gui.txt`) and run pytest normally. Note: PyQt6 is large; CI images will need to include it.

Contact me if you want me to: (A) add CI workflows to run GUI matrix with PyQt6, (B) convert GUI tests to be headless-friendly, or (C) push the branch via a remote you provide.
