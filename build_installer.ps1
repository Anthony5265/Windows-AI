# PowerShell script to build Windows AI installer
# Run from repository root on Windows

param(
    [string]$PythonExe = "python",
    [string]$CertPath = "",
    [string]$TimestampServer = "",
    [string[]]$PythonOptions = @('--embed')
)

$ErrorActionPreference = 'Stop'

function Ensure-Package {
    param(
        [string]$package
    )
    Write-Output "Installing $package..."
    & $PythonExe -m pip install --upgrade $package
}

if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    Write-Output "Python is required to build the installer. Install Python 3.11+ and rerun." -ForegroundColor Red
    exit 1
}

# install dependencies
& $PythonExe -m pip install --upgrade pip
Ensure-Package 'pyinstaller'
if (Test-Path 'requirements.txt') {
    & $PythonExe -m pip install -r requirements.txt
}

# run PyInstaller for both architectures
$architectures = @('x86', 'x64')
$resources = @('install','plugins','assets','config','control_center','automation','windows_ai')

foreach ($arch in $architectures) {
    Write-Output "Running PyInstaller for $arch..."

    $dist = Join-Path (Get-Location) "dist_$arch"
    $build = Join-Path (Get-Location) "build_$arch"

    if (Test-Path $dist) { Remove-Item $dist -Recurse -Force }
    if (Test-Path $build) { Remove-Item $build -Recurse -Force }

    $pyArgs = @(
        '--noconfirm','--onefile','--windowed','installer/gui_installer.py',
        '--name',"WindowsAI_Installer_$arch",
        '--distpath',$dist,
        '--workpath',$build,
        '--specpath',$build,
        '--target-arch',$arch
    )

    foreach ($opt in $PythonOptions) {
        $pyArgs += '--python-option'
        $pyArgs += $opt
    }

    & $PythonExe -m PyInstaller @pyArgs

    foreach ($res in $resources) {
        if (Test-Path $res) {
            Copy-Item $res -Destination (Join-Path $dist $res) -Recurse -Force
        }
    }

    Write-Output "Installer built at $dist\WindowsAI_Installer_$arch.exe"
}

$installerExe = Join-Path $dist 'WindowsAI_Installer.exe'
if ($CertPath -and $TimestampServer) {
    if (Test-Path $CertPath) {
        Write-Output "Signing installer..."
        & "SignTool.exe" sign /fd SHA256 /f $CertPath /tr $TimestampServer /td SHA256 $installerExe
    } else {
        Write-Output "Certificate not found at $CertPath. Skipping signing."
    }
} else {
    Write-Output "CertPath or TimestampServer not provided. Skipping signing."
}

Write-Output "Installer built at dist\WindowsAI_Installer.exe"
Write-Output "Running the installer will automatically execute install\install.ps1"
Write-Output "with admin rights to register services."
