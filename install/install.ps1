Write-Host "Installing Windows AI services..."

function Ensure-Tool {
    param(
        [string]$Command,
        [scriptblock]$Installer
    )
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-Host "$Command not found, attempting download..."
        & $Installer
    }
}

Ensure-Tool 'nssm.exe' {
    $url = 'https://nssm.cc/release/nssm-2.24.zip'
    $zip = Join-Path $env:TEMP 'nssm.zip'
    Invoke-WebRequest $url -OutFile $zip
    $dir = Join-Path $env:ProgramData 'nssm'
    Expand-Archive $zip -DestinationPath $dir -Force
    $nssmExe = Get-ChildItem $dir -Recurse -Filter nssm.exe | Select-Object -First 1
    if ($nssmExe) {
        $env:PATH = "$($nssmExe.Directory.FullName);$env:PATH"
    }
}

Ensure-Tool 'mkcert' {
    $url = 'https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert.exe'
    $exe = Join-Path $env:ProgramData 'mkcert.exe'
    Invoke-WebRequest $url -OutFile $exe
    $env:PATH = "$env:ProgramData;$env:PATH"
}

Ensure-Tool 'node' {
    $url = 'https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi'
    $msi = Join-Path $env:TEMP 'node.msi'
    Invoke-WebRequest $url -OutFile $msi
    Start-Process msiexec.exe -ArgumentList '/i',$msi,'/quiet','/norestart' -Wait
}

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
