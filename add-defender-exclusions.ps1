# Add Windows Defender Exclusions for Windows AI Build
# Run this script as Administrator

Write-Host "Adding Windows Defender exclusions for Windows AI build..." -ForegroundColor Green

# Add folder exclusions
$folders = @(
    "C:\Users\antho\Windows-AI-main\node_modules",
    "C:\Users\antho\Windows-AI-main\dist",
    "C:\Users\antho\Windows-AI-main\apps\gui\dist",
    "C:\Users\antho\Windows-AI-main\dist-simple"
)

foreach ($folder in $folders) {
    try {
        Add-MpPreference -ExclusionPath $folder
        Write-Host "✓ Added exclusion: $folder" -ForegroundColor Cyan
    } catch {
        Write-Host "✗ Failed to add exclusion: $folder" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

# Add process exclusions for build tools
$processes = @(
    "app-builder.exe",
    "electron-builder.exe",
    "pyinstaller.exe",
    "node.exe"
)

foreach ($process in $processes) {
    try {
        Add-MpPreference -ExclusionProcess $process
        Write-Host "✓ Added process exclusion: $process" -ForegroundColor Cyan
    } catch {
        Write-Host "✗ Failed to add process exclusion: $process" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

Write-Host "`nExclusions added successfully!" -ForegroundColor Green
Write-Host "You can now run the build without Windows Defender interference." -ForegroundColor Yellow
Write-Host "`nTo verify exclusions, run:" -ForegroundColor Gray
Write-Host "  Get-MpPreference | Select-Object -ExpandProperty ExclusionPath" -ForegroundColor Gray
