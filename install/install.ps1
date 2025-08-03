Write-Host "Installing Windows AI services..."
if (Get-Command nssm.exe -ErrorAction SilentlyContinue) {
    nssm install WindowsAIService "node" "apps\server.js"
}
if (Get-Command mkcert -ErrorAction SilentlyContinue) {
    mkcert -install
}
if (Get-Command New-NetFirewallRule -ErrorAction SilentlyContinue) {
    try {
        New-NetFirewallRule -DisplayName "Windows AI" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080 | Out-Null
    } catch {}
}
Write-Host "Install complete."
