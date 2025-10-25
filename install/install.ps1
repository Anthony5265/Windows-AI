param(
    [string]$CacheDir = (Join-Path $PSScriptRoot 'cache')
)

if (-not (Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir | Out-Null
}

$logPath = Join-Path $CacheDir 'install.log'
Write-Host "Starting installation transcript at $logPath"
Start-Transcript -Path $logPath -Force -IncludeInvocationHeader | Out-Null
try {
    Write-Host "Installing Windows AI services..."

    # Start a new snapshot so we can rollback these actions later
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -m installer.snapshot create
    } else {
        Write-Error "Required command 'python' not found; snapshot creation skipped."
    }

    $nssmCmd = Get-Command nssm.exe -ErrorAction SilentlyContinue
    if (-not $nssmCmd) {
        Write-Error "Required command 'nssm.exe' not found; attempting download to cache."
        $nssmZip = Join-Path $CacheDir 'nssm.zip'
        $nssmUrl = 'https://nssm.cc/release/nssm-2.24.zip'
        try {
            Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing
            Expand-Archive -Path $nssmZip -DestinationPath $CacheDir -Force
        } catch {
            Write-Error "Failed to download nssm: $_"
        }
        $nssmPath = Join-Path $CacheDir 'nssm-2.24\win64\nssm.exe'
    } else {
        $nssmPath = $nssmCmd.Path
    }

    if (Test-Path $nssmPath) {
        Start-Process -FilePath $nssmPath -ArgumentList 'install','WindowsAIService','node','apps\server.js' -Wait
        if (Get-Command python -ErrorAction SilentlyContinue) {
            python -m installer.snapshot record service WindowsAIService
        }
    } else {
        Write-Error "Unable to locate nssm executable; service installation skipped."
    }

    $mkcertCmd = Get-Command mkcert -ErrorAction SilentlyContinue
    if (-not $mkcertCmd) {
        Write-Error "Required command 'mkcert' not found; attempting download to cache."
        $mkcertPath = Join-Path $CacheDir 'mkcert.exe'
        $mkcertUrl = 'https://dl.filippo.io/mkcert/latest?for=windows/amd64'
        try {
            Invoke-WebRequest -Uri $mkcertUrl -OutFile $mkcertPath -UseBasicParsing
        } catch {
            Write-Error "Failed to download mkcert: $_"
        }
    } else {
        $mkcertPath = $mkcertCmd.Path
    }

    if (Test-Path $mkcertPath) {
        Start-Process -FilePath $mkcertPath -ArgumentList '-install' -Wait
    } else {
        Write-Error "Unable to locate mkcert executable; certificate installation skipped."
    }

    if (Get-Command New-NetFirewallRule -ErrorAction SilentlyContinue) {
        try {
            New-NetFirewallRule -DisplayName "Windows AI" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080 | Out-Null
            if (Get-Command python -ErrorAction SilentlyContinue) {
                python -m installer.snapshot record firewall 'Windows AI'
            }
        } catch {
            Write-Error $_
        }
    } else {
        Write-Error "Required command 'New-NetFirewallRule' not found; firewall rule not added."
    }

    Write-Host "Install complete."
}
finally {
    Stop-Transcript | Out-Null
}

