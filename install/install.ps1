function Get-ToolVersion {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    try {
        $output = & $Command @Arguments 2>&1
    } catch {
        return $null
    }

    $match = $output | Select-String -Pattern '\d+(\.\d+)+'
    if ($match) {
        return [Version]$match.Matches[0].Value
    }
    return $null
}

function Require-MinVersion {
    param(
        [string]$Name,
        [string]$Command,
        [Version]$Minimum,
        [string[]]$Arguments
    )

    $version = Get-ToolVersion -Command $Command -Arguments $Arguments
    if (-not $version) {
        throw "Unable to determine $Name version."
    }
    Write-Host "$Name version $version"
    if ($version -lt $Minimum) {
        throw "$Name $Minimum or later is required."
    }
    return $version
}

function Invoke-WindowsAIInstall {
    Write-Host "Installing Windows AI services..."

    $minPSVersion = [Version]'5.1'
    $minNssmVersion = [Version]'2.24'
    $minMkcertVersion = [Version]'1.4.0'

    Write-Host "PowerShell version $($PSVersionTable.PSVersion)"
    if ($PSVersionTable.PSVersion -lt $minPSVersion) {
        throw "PowerShell $minPSVersion or later is required."
    }

    # Start a new snapshot so we can rollback these actions later
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -m installer.snapshot create
    }

    if (Get-Command nssm.exe -ErrorAction SilentlyContinue) {
        Require-MinVersion -Name 'nssm' -Command 'nssm.exe' -Minimum $minNssmVersion -Arguments 'version'
        nssm install WindowsAIService "node" "apps\server.js"
        if (Get-Command python -ErrorAction SilentlyContinue) {
            python -m installer.snapshot record service WindowsAIService
        }
    }

    if (Get-Command mkcert -ErrorAction SilentlyContinue) {
        Require-MinVersion -Name 'mkcert' -Command 'mkcert' -Minimum $minMkcertVersion -Arguments '--version'
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
}

if ($MyInvocation.InvocationName -ne '.') {
    Invoke-WindowsAIInstall
}

