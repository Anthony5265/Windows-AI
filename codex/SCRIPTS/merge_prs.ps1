<#
Merges the latest main branch into all open PR branches and pushes updates.
Requires the GitHub CLI (`gh`) to be installed and authenticated.
Run from repo root:
  powershell -ExecutionPolicy Bypass -File .\codex\SCRIPTS\merge_prs.ps1
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
  Write-Output "No open pull requests found."
  exit 0
}

foreach ($pr in $prs) {
  $branch = $pr.headRefName
  Write-Output "Updating PR #$($pr.number) ($branch)..."
  git fetch origin $branch
  git checkout $branch
  git merge --no-edit origin/main
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Merge failed for $branch. Aborting."
    git merge --abort 2>$null
    git checkout $startBranch
    continue
  }
  git push origin $branch
}

git checkout $startBranch
