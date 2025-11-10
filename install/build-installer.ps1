# Windows AI Installer Build Script
# Prepares all components and builds the NSIS installer

param(
    [switch]$DownloadRuntimes = $false,
    [switch]$SkipTests = $false,
    [string]$Version = "0.5.0"
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Windows AI Installer Build Script" -ForegroundColor Cyan
Write-Host "  Version: $Version" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Paths
$RootDir = Split-Path $PSScriptRoot -Parent
$InstallDir = Join-Path $RootDir "install"
$RuntimesDir = Join-Path $InstallDir "runtimes"
$OutputDir = Join-Path $RootDir "dist"

# Create directories
New-Item -ItemType Directory -Force -Path $RuntimesDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# =====================================================================
# Step 1: Download Runtimes
# =====================================================================

if ($DownloadRuntimes) {
    Write-Host "[1/6] Downloading runtimes..." -ForegroundColor Yellow

    # Python Embedded
    $PythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    $PythonZip = Join-Path $RuntimesDir "python-embed.zip"
    $PythonDir = Join-Path $RuntimesDir "python-3.11-embed-amd64"

    if (-not (Test-Path $PythonDir)) {
        Write-Host "  Downloading Python 3.11 embedded..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonZip
        Expand-Archive -Path $PythonZip -DestinationPath $PythonDir -Force
        Remove-Item $PythonZip
        Write-Host "  Python embedded downloaded" -ForegroundColor Green
    } else {
        Write-Host "  Python already exists, skipping" -ForegroundColor Gray
    }

    # Node.js Portable
    $NodeUrl = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip"
    $NodeZip = Join-Path $RuntimesDir "node.zip"
    $NodeDir = Join-Path $RuntimesDir "node-v20-win-x64"

    if (-not (Test-Path $NodeDir)) {
        Write-Host "  Downloading Node.js 20 portable..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeZip
        Expand-Archive -Path $NodeZip -DestinationPath $RuntimesDir -Force
        Rename-Item (Join-Path $RuntimesDir "node-v20.11.1-win-x64") $NodeDir
        Remove-Item $NodeZip
        Write-Host "  Node.js downloaded" -ForegroundColor Green
    } else {
        Write-Host "  Node.js already exists, skipping" -ForegroundColor Gray
    }

    Write-Host "[1/6] Runtimes ready!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/6] Skipping runtime download (use -DownloadRuntimes to download)" -ForegroundColor Gray
    Write-Host ""
}

# =====================================================================
# Step 2: Run Tests
# =====================================================================

if (-not $SkipTests) {
    Write-Host "[2/6] Running tests..." -ForegroundColor Yellow

    Push-Location $RootDir
    try {
        # Check if pytest is available
        $pytestAvailable = $null -ne (Get-Command pytest -ErrorAction SilentlyContinue)

        if ($pytestAvailable) {
            Write-Host "  Running Python tests..." -ForegroundColor Gray
            pytest tests/ --tb=short
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  Tests failed!" -ForegroundColor Red
                exit 1
            }
            Write-Host "  All tests passed!" -ForegroundColor Green
        } else {
            Write-Host "  pytest not found, skipping tests" -ForegroundColor Yellow
        }
    } finally {
        Pop-Location
    }
    Write-Host ""
} else {
    Write-Host "[2/6] Skipping tests" -ForegroundColor Gray
    Write-Host ""
}

# =====================================================================
# Step 3: Clean Build Directory
# =====================================================================

Write-Host "[3/6] Cleaning build directory..." -ForegroundColor Yellow

$CleanDirs = @(
    "build",
    "dist",
    "*.egg-info",
    "__pycache__",
    "node_modules"
)

foreach ($dir in $CleanDirs) {
    Get-ChildItem -Path $RootDir -Filter $dir -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "  Build directory cleaned" -ForegroundColor Green
Write-Host ""

# =====================================================================
# Step 4: Build GUI Application
# =====================================================================

Write-Host "[4/6] Building GUI application..." -ForegroundColor Yellow

Push-Location (Join-Path $RootDir "apps\gui")
try {
    Write-Host "  Installing dependencies..." -ForegroundColor Gray
    npm install

    Write-Host "  Building Electron app..." -ForegroundColor Gray
    npm run build

    Write-Host "  GUI application built" -ForegroundColor Green
} finally {
    Pop-Location
}
Write-Host ""

# =====================================================================
# Step 5: Build Tray Application
# =====================================================================

Write-Host "[5/6] Building tray application..." -ForegroundColor Yellow

Push-Location (Join-Path $RootDir "windows-ai-tray")
try {
    Write-Host "  Installing dependencies..." -ForegroundColor Gray
    npm install

    Write-Host "  Building Electron app..." -ForegroundColor Gray
    npm run build

    Write-Host "  Tray application built" -ForegroundColor Green
} finally {
    Pop-Location
}
Write-Host ""

# =====================================================================
# Step 6: Build NSIS Installer
# =====================================================================

Write-Host "[6/6] Building NSIS installer..." -ForegroundColor Yellow

# Check if NSIS is installed
$nsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
if (-not (Test-Path $nsisPath)) {
    Write-Host "  ERROR: NSIS not found at $nsisPath" -ForegroundColor Red
    Write-Host "  Please install NSIS from https://nsis.sourceforge.io/" -ForegroundColor Yellow
    exit 1
}

# Build installer
$installerScript = Join-Path $InstallDir "installer.nsi"
Write-Host "  Compiling installer..." -ForegroundColor Gray

Push-Location $RootDir
try {
    & $nsisPath /V4 $installerScript

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Installer built successfully!" -ForegroundColor Green

        # Move installer to output directory
        $installerFile = "WindowsAI-Setup-$Version.exe"
        if (Test-Path $installerFile) {
            Move-Item $installerFile $OutputDir -Force
            Write-Host ""
            Write-Host "================================================" -ForegroundColor Green
            Write-Host "  BUILD COMPLETE!" -ForegroundColor Green
            Write-Host "================================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "  Installer: $OutputDir\$installerFile" -ForegroundColor Cyan
            Write-Host "  Size: $([math]::Round((Get-Item "$OutputDir\$installerFile").Length / 1MB, 2)) MB" -ForegroundColor Cyan
            Write-Host ""
        }
    } else {
        Write-Host "  Installer build failed!" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Build process completed successfully!" -ForegroundColor Green
Write-Host ""
