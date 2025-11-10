#Requires -Version 5.1
<#
.SYNOPSIS
    Build Windows AI Portable Distribution
.DESCRIPTION
    Creates a portable ZIP package of Windows AI that can run without installation.
    Includes Python runtime, Node.js runtime, backend, GUI, and all dependencies.
.PARAMETER OutputDir
    Directory to output the portable build (default: dist/portable)
.PARAMETER Version
    Version number for the build (default: 0.5.0)
.PARAMETER Arch
    Architecture to build for: x64 or x86 (default: x64)
.PARAMETER IncludeModels
    Include pre-downloaded AI models in the portable package
.EXAMPLE
    .\build-portable.ps1 -Version "0.5.0" -Arch x64
#>

param(
    [string]$OutputDir = "dist/portable",
    [string]$Version = "0.5.0",
    [ValidateSet('x64', 'x86')]
    [string]$Arch = "x64",
    [switch]$IncludeModels = $false
)

$ErrorActionPreference = "Stop"

# =====================================================================
# Configuration
# =====================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BuildDir = Join-Path $OutputDir "WindowsAI-Portable-$Version-$Arch"
$PackageName = "WindowsAI-Portable-$Version-$Arch.zip"

# Runtime versions
$PythonVersion = "3.11.7"
$NodeVersion = "20.11.0"

# Download URLs
if ($Arch -eq "x64") {
    $PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
    $NodeUrl = "https://nodejs.org/dist/v$NodeVersion/node-v$NodeVersion-win-x64.zip"
} else {
    $PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-win32.zip"
    $NodeUrl = "https://nodejs.org/dist/v$NodeVersion/node-v$NodeVersion-win-x86.zip"
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Windows AI Portable Build" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Version: $Version"
Write-Host "Architecture: $Arch"
Write-Host "Output: $BuildDir"
Write-Host ""

# =====================================================================
# Helper Functions
# =====================================================================

function Download-File {
    param([string]$Url, [string]$Output)

    Write-Host "Downloading: $(Split-Path -Leaf $Output)" -ForegroundColor Yellow

    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Url -OutFile $Output -UseBasicParsing
        $ProgressPreference = 'Continue'
        Write-Host "  [OK] Downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Download failed: $_" -ForegroundColor Red
        throw
    }
}

function Extract-Archive {
    param([string]$Path, [string]$Destination)

    Write-Host "Extracting: $(Split-Path -Leaf $Path)" -ForegroundColor Yellow

    try {
        Expand-Archive -Path $Path -DestinationPath $Destination -Force
        Write-Host "  [OK] Extracted successfully" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Extraction failed: $_" -ForegroundColor Red
        throw
    }
}

function Copy-WithProgress {
    param([string]$Source, [string]$Destination, [string]$Description)

    Write-Host "Copying: $Description" -ForegroundColor Yellow

    try {
        if (Test-Path $Source -PathType Container) {
            Copy-Item -Path $Source -Destination $Destination -Recurse -Force
        } else {
            Copy-Item -Path $Source -Destination $Destination -Force
        }
        Write-Host "  [OK] Copied successfully" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Copy failed: $_" -ForegroundColor Red
        throw
    }
}

# =====================================================================
# Step 1: Clean and Create Build Directory
# =====================================================================

Write-Host "`n[1/8] Preparing build directory..." -ForegroundColor Cyan

if (Test-Path $BuildDir) {
    Write-Host "  Cleaning existing build directory..."
    Remove-Item -Path $BuildDir -Recurse -Force
}

New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
$TempDir = Join-Path $OutputDir "temp"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Write-Host "  [OK] Build directory ready" -ForegroundColor Green

# =====================================================================
# Step 2: Download and Extract Python
# =====================================================================

Write-Host "`n[2/8] Setting up Python runtime..." -ForegroundColor Cyan

$PythonZip = Join-Path $TempDir "python.zip"
$PythonDir = Join-Path $BuildDir "python"

Download-File -Url $PythonUrl -Output $PythonZip
Extract-Archive -Path $PythonZip -Destination $PythonDir

# Configure embedded Python
$PthFile = Get-ChildItem -Path $PythonDir -Filter "*._pth" | Select-Object -First 1
if ($PthFile) {
    # Enable site-packages
    $content = Get-Content $PthFile.FullName
    $content = $content -replace '#import site', 'import site'
    $content | Set-Content $PthFile.FullName
}

Write-Host "  [OK] Python runtime ready" -ForegroundColor Green

# =====================================================================
# Step 3: Download and Extract Node.js
# =====================================================================

Write-Host "`n[3/8] Setting up Node.js runtime..." -ForegroundColor Cyan

$NodeZip = Join-Path $TempDir "node.zip"
$NodeExtracted = Join-Path $TempDir "node"

Download-File -Url $NodeUrl -Output $NodeZip
Extract-Archive -Path $NodeZip -Destination $NodeExtracted

# Move Node.js to build directory
$NodeFolder = Get-ChildItem -Path $NodeExtracted -Directory | Select-Object -First 1
$NodeDir = Join-Path $BuildDir "node"
Move-Item -Path $NodeFolder.FullName -Destination $NodeDir -Force

Write-Host "  [OK] Node.js runtime ready" -ForegroundColor Green

# =====================================================================
# Step 4: Install Python Dependencies
# =====================================================================

Write-Host "`n[4/8] Installing Python dependencies..." -ForegroundColor Cyan

$PythonExe = Join-Path $PythonDir "python.exe"

# Install pip
Write-Host "  Installing pip..."
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$GetPipPath = Join-Path $TempDir "get-pip.py"
Download-File -Url $GetPipUrl -Output $GetPipPath

& $PythonExe $GetPipPath --no-warn-script-location

# Install requirements
Write-Host "  Installing requirements..."
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
& $PythonExe -m pip install -r $RequirementsFile --no-warn-script-location

Write-Host "  [OK] Python dependencies installed" -ForegroundColor Green

# =====================================================================
# Step 5: Copy Backend Application
# =====================================================================

Write-Host "`n[5/8] Copying backend application..." -ForegroundColor Cyan

$BackendDir = Join-Path $BuildDir "backend"
New-Item -ItemType Directory -Path $BackendDir -Force | Out-Null

Copy-WithProgress -Source (Join-Path $ProjectRoot "windows_ai") -Destination (Join-Path $BackendDir "windows_ai") -Description "Backend source"
Copy-WithProgress -Source (Join-Path $ProjectRoot "requirements.txt") -Destination (Join-Path $BackendDir "requirements.txt") -Description "Requirements"
Copy-WithProgress -Source (Join-Path $ProjectRoot "config") -Destination (Join-Path $BackendDir "config") -Description "Configuration"

Write-Host "  [OK] Backend copied" -ForegroundColor Green

# =====================================================================
# Step 6: Build and Copy GUI Application
# =====================================================================

Write-Host "`n[6/8] Building GUI application..." -ForegroundColor Cyan

$GuiDir = Join-Path $ProjectRoot "apps\gui"
$NodeExe = Join-Path $NodeDir "node.exe"
$NpmCmd = Join-Path $NodeDir "npm.cmd"

# Install GUI dependencies
Write-Host "  Installing GUI dependencies..."
Push-Location $GuiDir
& $NpmCmd install --legacy-peer-deps
if ($LASTEXITCODE -ne 0) {
    throw "npm install failed"
}

# Build GUI
Write-Host "  Building Electron app..."
& $NpmCmd run build
if ($LASTEXITCODE -ne 0) {
    throw "Electron build failed"
}
Pop-Location

# Copy built GUI
$GuiBuildDir = Join-Path $GuiDir "dist"
if (Test-Path $GuiBuildDir) {
    Copy-WithProgress -Source $GuiBuildDir -Destination (Join-Path $BuildDir "gui") -Description "GUI application"
} else {
    Write-Host "  [WARNING] GUI build not found, copying source instead" -ForegroundColor Yellow
    Copy-WithProgress -Source $GuiDir -Destination (Join-Path $BuildDir "gui") -Description "GUI source"
}

Write-Host "  [OK] GUI application ready" -ForegroundColor Green

# =====================================================================
# Step 7: Create Launcher Scripts
# =====================================================================

Write-Host "`n[7/8] Creating launcher scripts..." -ForegroundColor Cyan

# Windows batch launcher
$LauncherBat = @"
@echo off
title Windows AI - Portable Edition

echo ========================================
echo   Windows AI - Portable Edition
echo   Version: $Version
echo ========================================
echo.

set PORTABLE_MODE=1
set PYTHON_HOME=%~dp0python
set NODE_HOME=%~dp0node
set PATH=%PYTHON_HOME%;%NODE_HOME%;%PATH%

echo Starting backend...
start "" /B "%PYTHON_HOME%\python.exe" -m windows_ai.main

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting GUI...
start "" "%NODE_HOME%\node.exe" "%~dp0gui\main.js"

echo.
echo Windows AI is now running.
echo Press any key to stop...
pause >nul

echo Stopping Windows AI...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Windows AI*" >nul 2>&1
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Windows AI*" >nul 2>&1

echo Stopped.
"@

$LauncherBat | Out-File -FilePath (Join-Path $BuildDir "WindowsAI.bat") -Encoding ASCII

# PowerShell launcher
$LauncherPs1 = @"
# Windows AI Portable Launcher
`$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Windows AI - Portable Edition" -ForegroundColor Cyan
Write-Host "  Version: $Version" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

`$env:PORTABLE_MODE = "1"
`$ScriptDir = Split-Path -Parent `$MyInvocation.MyCommand.Path
`$PythonExe = Join-Path `$ScriptDir "python\python.exe"
`$NodeExe = Join-Path `$ScriptDir "node\node.exe"

Write-Host "Starting backend..." -ForegroundColor Yellow
`$BackendProcess = Start-Process -FilePath `$PythonExe -ArgumentList "-m", "windows_ai.main" -WindowStyle Hidden -PassThru

Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Starting GUI..." -ForegroundColor Yellow
`$GuiProcess = Start-Process -FilePath `$NodeExe -ArgumentList (Join-Path `$ScriptDir "gui\main.js") -PassThru

Write-Host "Windows AI is now running!" -ForegroundColor Green
Write-Host "Press Enter to stop..." -ForegroundColor Yellow
Read-Host

Write-Host "Stopping Windows AI..." -ForegroundColor Yellow
Stop-Process -Id `$BackendProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id `$GuiProcess.Id -Force -ErrorAction SilentlyContinue

Write-Host "Stopped." -ForegroundColor Green
"@

$LauncherPs1 | Out-File -FilePath (Join-Path $BuildDir "WindowsAI.ps1") -Encoding UTF8

# README
$ReadmeContent = @"
# Windows AI - Portable Edition v$Version

This is a portable distribution of Windows AI that can run without installation.

## Quick Start

1. Extract this archive to any folder
2. Run **WindowsAI.bat** (or WindowsAI.ps1 for PowerShell)
3. Wait for the GUI to appear
4. Start chatting!

## Requirements

- Windows 10/11 (64-bit)
- No installation required
- All dependencies included

## What's Included

- Python $PythonVersion runtime (embedded)
- Node.js $NodeVersion runtime
- Windows AI backend and GUI
- All required dependencies

## Usage

### Windows Command Prompt / Batch
Double-click **WindowsAI.bat** or run from command line.

### PowerShell
Right-click **WindowsAI.ps1** and select "Run with PowerShell"
Or run: ``````powershell -ExecutionPolicy Bypass -File WindowsAI.ps1``````

## Data Storage

In portable mode, all data is stored in:
``````
<portable-dir>/data/
``````

This includes:
- Chat history
- Configuration files
- Downloaded AI models
- Logs

## Portable Mode Features

- No registry modifications
- No system-wide changes
- All data in portable directory
- Can run from USB drive
- Multiple instances supported

## Troubleshooting

**Backend won't start:**
- Check if port 8010 is available
- Run WindowsAI.ps1 in PowerShell to see detailed errors

**GUI won't start:**
- Ensure backend started successfully (wait 3-5 seconds)
- Check logs in data/logs/

**Permission errors:**
- Extract to a folder where you have write permissions
- Avoid Program Files or Windows directories

## More Information

- Documentation: https://github.com/yourorg/Windows-AI/tree/main/docs
- Issues: https://github.com/yourorg/Windows-AI/issues

---

**Version:** $Version | **Build Date:** $(Get-Date -Format "yyyy-MM-dd")
"@

$ReadmeContent | Out-File -FilePath (Join-Path $BuildDir "README.txt") -Encoding UTF8

Write-Host "  [OK] Launcher scripts created" -ForegroundColor Green

# =====================================================================
# Step 8: Create ZIP Package
# =====================================================================

Write-Host "`n[8/8] Creating portable ZIP package..." -ForegroundColor Cyan

$ZipPath = Join-Path $OutputDir $PackageName

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

# Create ZIP
Compress-Archive -Path "$BuildDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

$ZipSize = (Get-Item $ZipPath).Length / 1MB

Write-Host "  [OK] Portable package created" -ForegroundColor Green
Write-Host "  Size: $([math]::Round($ZipSize, 2)) MB" -ForegroundColor Cyan

# =====================================================================
# Cleanup
# =====================================================================

Write-Host "`nCleaning up temporary files..." -ForegroundColor Yellow
Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue

# =====================================================================
# Summary
# =====================================================================

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Package: $PackageName" -ForegroundColor White
Write-Host "Size: $([math]::Round($ZipSize, 2)) MB" -ForegroundColor White
Write-Host "Location: $ZipPath" -ForegroundColor White
Write-Host ""
Write-Host "To test the portable build:" -ForegroundColor Yellow
Write-Host "  1. Extract the ZIP to a test folder" -ForegroundColor White
Write-Host "  2. Run WindowsAI.bat" -ForegroundColor White
Write-Host ""
