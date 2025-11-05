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

    function Get-OrDownloadTool {
        param(
            [string]$CommandName,
            [string]$Url,
            [string]$DownloadName,
            [string]$RelativePath = '',
            [switch]$IsZip
        )
        $cmd = Get-Command $CommandName -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Path }
        Write-Error "$CommandName not found; attempting download."
        $dest = Join-Path $CacheDir $DownloadName
        Invoke-WebRequest -Uri $Url -OutFile $dest -UseBasicParsing
        if ($IsZip) {
            Expand-Archive -Path $dest -DestinationPath $CacheDir -Force
            if ($RelativePath) { return Join-Path $CacheDir $RelativePath }
        } else {
            return $dest
        }
    }

    # Start a new snapshot so we can rollback these actions later
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -m installer.snapshot create
    } else {
        Write-Error "Required command 'python' not found; snapshot creation skipped."
    }

    $nssmPath = Get-OrDownloadTool 'nssm.exe' 'https://nssm.cc/release/nssm-2.24.zip' 'nssm.zip' 'nssm-2.24\win64\nssm.exe' -IsZip
    $mkcertPath = Get-OrDownloadTool 'mkcert.exe' 'https://dl.filippo.io/mkcert/latest?for=windows/amd64' 'mkcert.exe'
    $nodePath = Get-OrDownloadTool 'node.exe' 'https://nodejs.org/dist/v20.12.1/node-v20.12.1-win-x64.zip' 'node.zip' 'node-v20.12.1-win-x64\node.exe' -IsZip

    if (-not $nodePath) {
        Write-Error "Unable to locate node executable; install aborted."
        return
    }

    if (Test-Path $nssmPath) {
        Start-Process -FilePath $nssmPath -ArgumentList 'install','WindowsAIService',$nodePath,'apps\server.js' -Wait
        if (Get-Command python -ErrorAction SilentlyContinue) {
            python -m installer.snapshot record service WindowsAIService
        }
    } else {
        Write-Error "Unable to locate nssm executable; service installation skipped."
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

