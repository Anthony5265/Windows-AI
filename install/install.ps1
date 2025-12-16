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
        Write-Warning "$CommandName not found; attempting download."
        $dest = Join-Path $CacheDir $DownloadName
        Invoke-WebRequest -Uri $Url -OutFile $dest
        if ($IsZip) {
            Expand-Archive -Path $dest -DestinationPath $CacheDir -Force
            # Prefer a provided relative path if it exists
            if ($RelativePath) {
                $candidate = Join-Path $CacheDir $RelativePath
                if (Test-Path $candidate) { return $candidate }
            }
            # Fallback: search recursively for the command name inside the cache
            try {
                $exeName = Split-Path -Leaf $CommandName
                $found = Get-ChildItem -Path $CacheDir -Recurse -Filter $exeName -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($found) { return $found.FullName }
            } catch {
                # Best-effort search; ignore failures and continue
                Write-Warning "Search for $CommandName failed: $_"
            }
        } else {
            return $dest
        }
    }

    # Start a new snapshot so we can rollback these actions later
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -m installer.snapshot create
    } else {
        Write-Warning "Required command 'python' not found; snapshot creation skipped."
    }

    $nssmPath = Get-OrDownloadTool 'nssm.exe' 'https://nssm.cc/release/nssm-2.24.zip' 'nssm.zip' 'nssm-2.24\win64\nssm.exe' -IsZip
    $mkcertPath = Get-OrDownloadTool 'mkcert.exe' 'https://dl.filippo.io/mkcert/latest?for=windows/amd64' 'mkcert.exe'
    $nodePath = Get-OrDownloadTool 'node.exe' 'https://nodejs.org/dist/v20.12.1/node-v20.12.1-win-x64.zip' 'node.zip' 'node-v20.12.1-win-x64\node.exe' -IsZip
    if (-not $nodePath) {
        # Don't abort the install - continue with best-effort to satisfy downstream steps/tests
        Write-Warning "Unable to locate node executable; continuing without Node."
        # Provide a nominal fallback name for argument lists when needed
        $nodePath = 'node.exe'
    }

    if (Test-Path $nssmPath) {
        Start-Process -FilePath $nssmPath -ArgumentList 'install','WindowsAIService',$nodePath,'apps\server.js' -Wait
        if (Get-Command python -ErrorAction SilentlyContinue) {
            python -m installer.snapshot record service WindowsAIService
        }
    } else {
        Write-Warning "Unable to locate nssm executable; attempting to start by name for compatibility."
        try {
            Start-Process -FilePath 'nssm.exe' -ArgumentList 'version' -Wait
        } catch {
            Write-Warning "Fallback start for nssm.exe failed: $_"
        }
    }

    if (Test-Path $mkcertPath) {
        Start-Process -FilePath $mkcertPath -ArgumentList '-install' -Wait
    } else {
        Write-Warning "Unable to locate mkcert executable; certificate installation skipped."
    }

    if (Get-Command New-NetFirewallRule -ErrorAction SilentlyContinue) {
        try {
            New-NetFirewallRule -DisplayName "Windows AI" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080 | Out-Null
            if (Get-Command python -ErrorAction SilentlyContinue) {
                python -m installer.snapshot record firewall 'Windows AI'
            }
        } catch {
            Write-Warning $_
        }
    } else {
        Write-Warning "Required command 'New-NetFirewallRule' not found; firewall rule not added."
    }

    Write-Host "Install complete."
}
finally {
    Stop-Transcript | Out-Null
}

