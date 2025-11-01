param(
    [string]$BackupPattern = "*.bak.*"
)
Write-Host "Rolling back files matching pattern: $BackupPattern"
Get-ChildItem -Recurse -Filter $BackupPattern | ForEach-Object {
    $original = $_.FullName -replace "\.bak\..*$",""
    Write-Host "Restoring $($_.FullName) to $original"
    Copy-Item -Force $_.FullName $original
}
Write-Host "Rollback complete."
