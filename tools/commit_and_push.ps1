<#
Helper to interactively stage, commit and push changes.
Usage:
  .\tools\commit_and_push.ps1           # interactive: shows status, prompts to commit and push
  .\tools\commit_and_push.ps1 -Message "My commit message" -Auto  # runs without prompts
#>

param(
    [string]$Message = "Hardening: headless tests, CI, theme and logo fixes",
    [switch]$Auto
)

function Run($cmd) {
    Write-Host "> $cmd"
    & $cmd
}

# Ensure git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git not found on PATH. Install git or run these commands manually."
    exit 1
}

Write-Host "Git status (porcelain):"
git status --porcelain

if (-not $Auto) {
    $yn = Read-Host "Stage ALL changes and commit with message: '$Message'? (y/N)"
    if ($yn -ne 'y' -and $yn -ne 'Y') {
        Write-Host "Aborting — no changes staged. To run non-interactively, pass -Auto."
        exit 0
    }
}

# Stage all changes
git add -A

# Check if there is anything to commit
$changes = git status --porcelain
if (-not $changes) {
    Write-Host "No changes to commit."
} else {
    git commit -m "$Message"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Commit failed. Check git output above."
        exit $LASTEXITCODE
    }
    Write-Host "Commit created."
}

if (-not $Auto) {
    $push = Read-Host "Push commit to remote 'origin'? (y/N)"
    if ($push -ne 'y' -and $push -ne 'Y') {
        Write-Host "Done locally. You can push later with: git push origin HEAD"
        exit 0
    }
}

# Push
Write-Host "Pushing to origin HEAD..."
git push origin HEAD
if ($LASTEXITCODE -ne 0) {
    Write-Error "Push failed. You may need to set upstream or fix auth."
    exit $LASTEXITCODE
}

Write-Host "Push complete."
