# Temporarily disable Windows Defender Real-Time Protection
# This will re-enable automatically on next reboot

Write-Host "Disabling Windows Defender Real-Time Protection..." -ForegroundColor Yellow
Write-Host "This is temporary and will re-enable on reboot." -ForegroundColor Gray

try {
    Set-MpPreference -DisableRealtimeMonitoring $true
    Write-Host "✓ Windows Defender Real-Time Protection disabled" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run your build. After the build completes, run:" -ForegroundColor Cyan
    Write-Host "  Set-MpPreference -DisableRealtimeMonitoring `$false" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "✗ Failed to disable Real-Time Protection" -ForegroundColor Red
    Write-Host "Make sure you're running PowerShell as Administrator" -ForegroundColor Yellow
}
