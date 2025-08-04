Write-Host "Uninstalling Windows AI services..."

# Use the snapshot to restore system changes
if (Get-Command python -ErrorAction SilentlyContinue) {
    python -m installer.snapshot restore
}

if (Get-Command nssm.exe -ErrorAction SilentlyContinue) {
    nssm remove WindowsAIService confirm
}
if (Get-Command Remove-NetFirewallRule -ErrorAction SilentlyContinue) {
    try {
        Remove-NetFirewallRule -DisplayName "Windows AI" | Out-Null
    } catch {}
}
Write-Host "Uninstall complete."
