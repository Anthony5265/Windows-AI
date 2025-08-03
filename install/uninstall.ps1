Write-Host "Uninstalling Windows AI services..."
if (Get-Command nssm.exe -ErrorAction SilentlyContinue) {
    nssm remove WindowsAIService confirm
}
if (Get-Command Remove-NetFirewallRule -ErrorAction SilentlyContinue) {
    try {
        Remove-NetFirewallRule -DisplayName "Windows AI" | Out-Null
    } catch {}
}
Write-Host "Uninstall complete."
