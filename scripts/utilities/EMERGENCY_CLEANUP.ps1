# EMERGENCY: Kill all background jobs and clean up
Write-Host "=== EMERGENCY CLEANUP ===" -ForegroundColor Red

# Force kill all jobs
Get-Job | Stop-Job -Force -ErrorAction SilentlyContinue
Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue

Write-Host "✓ All jobs stopped" -ForegroundColor Green

# Check what was created
$extCount = (Get-ChildItem "C:\Users\antho\Windows-AI\extensions_copilot_swarm" -Directory -ErrorAction SilentlyContinue).Count
Write-Host "`nExtensions created: $extCount" -ForegroundColor Cyan

$newTotal = 2496 + $extCount
Write-Host "Progress: $newTotal / 3148 ($([math]::Round($newTotal / 3148 * 100, 2))%)" -ForegroundColor Yellow

Write-Host "`nSystem cleaned up. Ready to restart." -ForegroundColor Green
Write-Host "`nNext: Run SUPERVISED_SWARM.ps1 (max 10 agents)" -ForegroundColor Cyan
