<# 
Copies mirrors from codex into the correct repo locations.
Run from repo root:  powershell -ExecutionPolicy Bypass -File .\codex\SCRIPTS\setup_repo.ps1
#>
param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"

# Create root folders if missing
$folders = @("docs", "openapi", ".github\ISSUE_TEMPLATE")
foreach ($f in $folders) {
  if (-not (Test-Path $f)) { New-Item -ItemType Directory -Force -Path $f | Out-Null }
}

# Copy OpenAPI
Copy-Item "codex\openapi\windows-ai.yaml" "openapi\windows-ai.yaml" -Force:$Force

# Copy root helper files
Copy-Item "codex\ROOT_FILES\.editorconfig" ".editorconfig" -Force:$Force
Copy-Item "codex\ROOT_FILES\.gitattributes" ".gitattributes" -Force:$Force
Copy-Item "codex\ROOT_FILES\.gitignore" ".gitignore" -Force:$Force

# Copy GitHub templates
Copy-Item "codex\TEMPLATES\PULL_REQUEST_TEMPLATE.md" ".github\PULL_REQUEST_TEMPLATE.md" -Force:$Force
Copy-Item "codex\TEMPLATES\ISSUE_FEATURE.md" ".github\ISSUE_TEMPLATE\feature.yml" -Force:$Force
Copy-Item "codex\TEMPLATES\ISSUE_BUG.md" ".github\ISSUE_TEMPLATE\bug.yml" -Force:$Force

Write-Host "Repo bootstrapped. Review files and commit."
