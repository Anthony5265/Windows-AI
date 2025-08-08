Write-Host "Uninstalling Windows AI services..."

$LogPath = Join-Path $PSScriptRoot 'uninstall.log'
New-Item -Path $LogPath -ItemType File -Force | Out-Null

function Write-UninstallLog {
    param([string]$Message)
    Add-Content -Path $LogPath -Value "$(Get-Date -Format s) $Message"
}

# Use the snapshot to restore system changes
if (Get-Command python -ErrorAction SilentlyContinue) {
    python -m installer.snapshot restore
}

if (Get-Command nssm.exe -ErrorAction SilentlyContinue) {
    nssm remove WindowsAIService confirm
    $service = Get-Service -Name WindowsAIService -ErrorAction SilentlyContinue
    if ($LASTEXITCODE -ne 0 -or $service) {
        Write-UninstallLog "Failed to remove service WindowsAIService. ExitCode: $LASTEXITCODE Exists: $([bool]$service)"
    }
}

if (Get-Command Remove-NetFirewallRule -ErrorAction SilentlyContinue) {
    Remove-NetFirewallRule -DisplayName "Windows AI" -ErrorAction SilentlyContinue | Out-Null
    $removeSuccess = $?
    $rule = Get-NetFirewallRule -DisplayName "Windows AI" -ErrorAction SilentlyContinue
    if (-not $removeSuccess -or $rule) {
        Write-UninstallLog "Failed to remove firewall rule 'Windows AI'. ExitCode: $LASTEXITCODE Exists: $([bool]$rule)"
    }
}

Write-Host "Uninstall complete."
