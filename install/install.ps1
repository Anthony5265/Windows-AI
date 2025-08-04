Write-Host "Installing Windows AI services..."

# Start a new snapshot so we can rollback these actions later
if (Get-Command python -ErrorAction SilentlyContinue) {
    python -m installer.snapshot create
}

if (Get-Command nssm.exe -ErrorAction SilentlyContinue) {
    nssm install WindowsAIService "node" "apps\server.js"
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -m installer.snapshot record service WindowsAIService
    }
}
if (Get-Command mkcert -ErrorAction SilentlyContinue) {
    mkcert -install
}
if (Get-Command New-NetFirewallRule -ErrorAction SilentlyContinue) {
    try {
        New-NetFirewallRule -DisplayName "Windows AI" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080 | Out-Null
        if (Get-Command python -ErrorAction SilentlyContinue) {
            python -m installer.snapshot record firewall 'Windows AI'
        }
    } catch {}
}
Write-Host "Install complete."
