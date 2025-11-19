$ErrorActionPreference="Stop"
$files = @(
    "docs/WindowsAI_Consolidated_Roadmap.md",
    "docs/live-status.md",
    "Phase_Tracking_Sheet.md",
    "Repo_Organization_Plan.md"
)
$context = foreach ($f in $files) {
    if (Test-Path $f) {
        "`n=== $f ===`n" + (Get-Content $f -Raw)
    } else {
        "`n=== $f missing ===`n"
    }
}
$outPath = "docs/context-snapshot.txt"
$context | Out-File $outPath -Encoding utf8
Write-Host "Updated $outPath"
