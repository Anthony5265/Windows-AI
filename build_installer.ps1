# PowerShell script to build Windows AI installer
# Run from repository root on Windows

param(
    [string]$PythonExe = "python"
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

# run PyInstaller
Write-Output "Running PyInstaller..."
& $PythonExe -m PyInstaller --noconfirm --onefile --windowed installer/gui_installer.py --name 'WindowsAI_Installer'

# copy assets
$dist = Join-Path (Get-Location) 'dist'
$resources = @('install','plugins','assets','config','control_center','automation','windows_ai')
foreach ($res in $resources) {
    if (Test-Path $res) {
        Copy-Item $res -Destination (Join-Path $dist $res) -Recurse -Force
    }
}

Write-Output "Installer built at dist\WindowsAI_Installer.exe"
Write-Output "Running the installer will automatically execute install\install.ps1"
Write-Output "with admin rights to register services."
