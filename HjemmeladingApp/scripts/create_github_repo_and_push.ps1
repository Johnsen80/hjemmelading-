<#
.SYNOPSIS
  Create a GitHub repository and push the current branch.

.DESCRIPTION
  This helper tries to create a repository using the GitHub CLI (`gh`) if available.
  If `gh` is not installed, it can call the GitHub REST API using a Personal Access Token
  supplied via the environment variable `GITHUB_TOKEN`.

.PARAMETER Owner
  GitHub account or organization to create the repo under. Default: your authenticated user.

.PARAMETER RepoName
  Repository name to create. Default: HjemmeladingApp

.PARAMETER Private
  Create repository as private when present.

USAGE
  # Using gh (recommended)
  .\create_github_repo_and_push.ps1 -Owner Johnsen80 -RepoName HjemmeladingApp

  # Using PAT (set GITHUB_TOKEN env var first)
  $env:GITHUB_TOKEN = "ghp_..."
  .\create_github_repo_and_push.ps1 -Owner <your-username> -RepoName HjemmeladingApp
#>

param(
    [string]$Owner = '',
    [string]$RepoName = 'HjemmeladingApp',
    [switch]$Private
)

function Write-ErrAndExit($msg){ Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

Push-Location -Path (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent) | Out-Null
Pop-Location | Out-Null

# Ensure we're in repo root (assumes script in scripts/)
$repoRoot = Resolve-Path ".." -Relative
Set-Location -Path (Join-Path -Path (Get-Location) -ChildPath '..')

$currentBranch = (git rev-parse --abbrev-ref HEAD) 2>$null
if (-not $currentBranch) { Write-ErrAndExit 'Not a git repository or git not available.' }
Write-Host "Current branch: $currentBranch"

if ($Owner -ne '') { $fullName = "$Owner/$RepoName" } else { $fullName = $RepoName }

if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host 'Found GitHub CLI `gh` — using it to create repo.'
    $privacy = $Private.IsPresent ? '--private' : '--public'
    # `--source . --remote origin --push` will add remote and push current branch
    $args = @('repo','create',$fullName,$privacy,'--source','.', '--remote','origin','--push','--confirm')
    Write-Host "Running: gh $($args -join ' ')"
    gh @args
    if ($LASTEXITCODE -ne 0) { Write-ErrAndExit 'gh failed to create/push the repo.' }
    Write-Host 'Repository created and branch pushed using gh.'
    exit 0
}

if (-not $env:GITHUB_TOKEN) {
    Write-Host "GitHub CLI not found and no GITHUB_TOKEN set."
    Write-Host "Options:"; Write-Host "  - Install gh (https://cli.github.com/) and run again, or"; Write-Host "  - Create a Personal Access Token (repo scope) and set it in environment variable GITHUB_TOKEN, then run this script again."
    Write-ErrAndExit 'No available method to create repo.'
}

Write-Host 'Using GITHUB_TOKEN to call GitHub REST API to create repo.'
$body = @{
    name = $RepoName
    private = $Private.IsPresent
}
$json = $body | ConvertTo-Json

$headers = @{ Authorization = "token $($env:GITHUB_TOKEN)"; 'User-Agent' = 'create-script' }

if ($Owner -eq '') {
    # create under authenticated user
    $url = 'https://api.github.com/user/repos'
} else {
    # create under org
    $url = "https://api.github.com/orgs/$Owner/repos"
}

Write-Host "Creating repo via API: $url"
$resp = Invoke-RestMethod -Method Post -Uri $url -Headers $headers -Body $json -ContentType 'application/json' -ErrorAction Stop
if (-not $resp) { Write-ErrAndExit 'API did not return a response.' }

Write-Host 'Repository created. Now set origin and push branch.'
$remoteUrl = $resp.clone_url
git remote remove origin 2>$null
git remote add origin $remoteUrl
git push -u origin $currentBranch
if ($LASTEXITCODE -ne 0) { Write-ErrAndExit 'git push failed.' }

Write-Host "Pushed branch $currentBranch to $remoteUrl"
