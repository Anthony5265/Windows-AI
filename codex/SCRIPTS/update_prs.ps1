<#
Rebases all open PR branches onto the latest main branch and pushes updates.
Requires the GitHub CLI (`gh`) to be installed and authenticated.
Run from repo root:
  powershell -ExecutionPolicy Bypass -File .\codex\SCRIPTS\update_prs.ps1
#>

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Error "GitHub CLI 'gh' is required."
  exit 1
}

$startBranch = git rev-parse --abbrev-ref HEAD

git fetch origin

$prsJson = gh pr list --state open --json number,headRefName
$prs = $prsJson | ConvertFrom-Json

if (-not $prs) {
  Write-Host "No open pull requests found."
  exit 0
}

foreach ($pr in $prs) {
  $branch = $pr.headRefName
  Write-Host "Updating PR #$($pr.number) ($branch)..."
  git fetch origin $branch
  git checkout $branch
  if (-not (git rebase origin/main)) {
    Write-Warning "Rebase failed for $branch. Aborting."
    git rebase --abort 2>$null
    git checkout $startBranch
    continue
  }
  git push --force-with-lease origin $branch
}

git checkout $startBranch
