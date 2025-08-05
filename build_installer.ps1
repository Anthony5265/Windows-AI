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

# run PyInstaller for both architectures and bundle Python
Write-Output "Running PyInstaller..."
$resources = @('install','plugins','assets','config','control_center','automation','windows_ai')
$arches = @('x64','x86')
foreach ($arch in $arches) {
    $name = "WindowsAI_Installer_$arch"
    $dist = Join-Path (Get-Location) "dist\$arch"
    & $PythonExe -m PyInstaller --noconfirm --onefile --windowed installer/gui_installer.py `
        --name $name --distpath $dist --python-option embed --target-arch $arch
    foreach ($res in $resources) {
        if (Test-Path $res) {
            Copy-Item $res -Destination (Join-Path $dist $res) -Recurse -Force
        }
    }
    Write-Output "Installer built at $dist\$name.exe"
}

Write-Output "Running the installer will automatically execute install\install.ps1"
Write-Output "with admin rights to register services."
