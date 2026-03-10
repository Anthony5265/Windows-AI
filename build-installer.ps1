# Windows AI Installer Build Script (PowerShell)
# Builds WindowsAI-Setup.exe using NSIS

param(
    [string]$Version = "2.0.0",
    [switch]$Release = $false,
    [switch]$SkipValidation = $false
)

# Colors for output
$Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
}

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp]" -ForegroundColor Gray -NoNewline
    Write-Host " $Message" -ForegroundColor $Colors[$Type]
}

function Test-Prerequisites {
    Write-Status "Checking prerequisites..." "Info"
    
    # Check NSIS is installed
    $nsis = Get-ChildItem -Path "C:\Program Files*\NSIS\makensis.exe" -ErrorAction SilentlyContinue
    if (-not $nsis) {
        Write-Status "NSIS not found! Install from: https://nsis.sourceforge.io" "Error"
        Write-Status "Continuing with build report only (no .exe generation)..." "Warning"
        return $false
    }
    
    Write-Status "✓ NSIS found" "Success"
    return $true
}

function Build-Python {
    Write-Status "Building Python distribution..." "Info"
    
    # Create dist/WindowsAI directory with Python app
    $distDir = ".\dist\WindowsAI"
    if (Test-Path $distDir) {
        Remove-Item -Recurse -Force $distDir
    }
    
    New-Item -ItemType Directory -Path $distDir -Force | Out-Null
    
    # Copy Python package
    Copy-Item -Recurse ".\windows_ai" "$distDir\" -ErrorAction SilentlyContinue
    Copy-Item ".\requirements.txt" "$distDir\" -ErrorAction SilentlyContinue
    Copy-Item ".\README.md" "$distDir\" -ErrorAction SilentlyContinue
    
    Write-Status "✓ Python distribution prepared" "Success"
}

function Build-Installer {
    param([boolean]$HasNSIS)
    
    if (-not $HasNSIS) {
        Write-Status "Skipping .exe generation (NSIS not installed)" "Warning"
        return $true
    }
    
    Write-Status "Building Windows installer with NSIS..." "Info"
    
    # Find NSIS
    $nsis = Get-ChildItem -Path "C:\Program Files*\NSIS\makensis.exe" | Select-Object -First 1
    
    if (-not $nsis) {
        Write-Status "NSIS path not found" "Error"
        return $false
    }
    
    # Build installer
    $nsisScript = ".\installer\windows_ai.nsi"
    if (-not (Test-Path $nsisScript)) {
        Write-Status "NSIS script not found: $nsisScript" "Error"
        return $false
    }
    
    Write-Status "Running: $($nsis.FullName) $nsisScript" "Info"
    & $nsis.FullName $nsisScript
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✓ Installer created successfully" "Success"
        return $true
    } else {
        Write-Status "NSIS build failed (exit code: $LASTEXITCODE)" "Error"
        return $false
    }
}

function Create-PortableZip {
    Write-Status "Creating portable ZIP package..." "Info"
    
    $zipPath = ".\dist\WindowsAI-Portable-$Version.zip"
    $sourceDir = ".\dist\WindowsAI"
    
    if (Test-Path $sourceDir) {
        # Compress directory
        Compress-Archive -Path $sourceDir -DestinationPath $zipPath -Force
        
        if (Test-Path $zipPath) {
            $size = (Get-Item $zipPath).Length / 1MB
            Write-Status "✓ Portable ZIP created: WindowsAI-Portable-$Version.zip ($([Math]::Round($size, 1)) MB)" "Success"
            return $true
        }
    }
    
    return $false
}

function Generate-Checksums {
    Write-Status "Generating checksums..." "Info"
    
    $checksumFile = ".\dist\CHECKSUMS.txt"
    $files = @(
        ".\dist\WindowsAI-Setup-$Version.exe",
        ".\dist\WindowsAI-Portable-$Version.zip"
    )
    
    $checksums = @()
    foreach ($file in $files) {
        if (Test-Path $file) {
            $hash = (Get-FileHash -Path $file -Algorithm SHA256).Hash
            $filename = Split-Path $file -Leaf
            $checksums += "$hash  $filename"
        }
    }
    
    if ($checksums.Count -gt 0) {
        Set-Content -Path $checksumFile -Value $checksums
        Write-Status "✓ Checksums written to CHECKSUMS.txt" "Success"
    }
}

function Generate-ReleaseNotes {
    Write-Status "Generating release notes..." "Info"
    
    $releaseNotes = @(
        "# Windows AI v$Version Release",
        "",
        "## What's New",
        "- PyQt5 Desktop GUI with tabbed interface",
        "- 22 Production-ready audio plugins",
        "- Automated installer build system",
        "- NSIS-based Windows installer",
        "",
        "## Installation",
        "1. Download WindowsAI-Setup-$Version.exe",
        "2. Run the installer",
        "3. Follow the installation wizard",
        "4. Launch from Start Menu: Windows AI",
        "",
        "## Audio Plugins Included",
        "- Transcription: Whisper, Azure Speech, Deepgram, AWS Transcribe",
        "- Text-to-Speech: ElevenLabs, Bark, Coqui TTS",
        "- Advanced: FastWhisper, WhisperX, Seamless-M4T, and more",
        "",
        "## System Requirements",
        "- Windows 10/11 (64-bit)",
        "- 4GB RAM minimum",
        "- 2GB disk space",
        "- Internet connection (for cloud plugins)",
        "",
        "## Build Date",
        "$(Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC")",
        "",
        "## SHA256 Checksums",
        "See CHECKSUMS.txt",
        "",
        "## Support",
        "GitHub: https://github.com/Anthony5265/Windows-AI"
    ) -join "`r`n"
    
    $notesPath = ".\dist\RELEASE_NOTES.md"
    Set-Content -Path $notesPath -Value $releaseNotes
    Write-Status "✓ Release notes written to RELEASE_NOTES.md" "Success"
}

# Main Build Process
function Main {
    Write-Host ""
    Write-Status "========================================" "Info"
    Write-Status "WINDOWS AI INSTALLER BUILD SCRIPT" "Info"
    Write-Status "Version: $Version" "Info"
    Write-Status "========================================" "Info"
    
    # Validate build environment
    if (-not $SkipValidation) {
        $hasNSIS = Test-Prerequisites
    } else {
        $hasNSIS = $false
    }
    
    # Run build steps
    Build-Python
    $installerOK = Build-Installer -HasNSIS $hasNSIS
    $zipOK = Create-PortableZip
    Generate-Checksums
    Generate-ReleaseNotes
    
    # Summary
    Write-Host ""
    Write-Status "========================================" "Info"
    Write-Status "BUILD COMPLETE" "Success"
    Write-Status "========================================" "Info"
    
    Write-Status "Artifacts created in ./dist/:" "Info"
    Get-ChildItem -Path ".\dist\*" -File | ForEach-Object {
        $size = $_.Length / 1MB
        Write-Host "  ✓ $($_.Name) ($([Math]::Round($size, 1)) MB)"
    }
    
    Write-Host ""
    Write-Status "Next Steps:" "Info"
    Write-Status "1. Review RELEASE_NOTES.md and CHECKSUMS.txt" "Info"
    if ($hasNSIS) {
        Write-Status "2. Test WindowsAI-Setup-$Version.exe on Windows 10/11" "Info"
    }
    Write-Status "3. Create GitHub release" "Info"
    Write-Status "4. Upload artifacts to GitHub releases" "Info"
    
    Write-Host ""
}

# Run main function
Main
