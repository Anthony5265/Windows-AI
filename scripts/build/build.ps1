# Windows AI Build Script

param(
    [string]$Version = "2.0.0"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] [$Level] $Message"
}

Write-Log "Building Windows AI v$Version"

# Create dist directory
Write-Log "Preparing distribution directory"
$distDir = ".\dist\WindowsAI"
if (Test-Path $distDir) {
    Remove-Item -Recurse -Force $distDir
}
New-Item -ItemType Directory -Path $distDir -Force | Out-Null

# Copy files
Write-Log "Copying application files"
Copy-Item -Recurse ".\windows_ai" "$distDir\" -ErrorAction SilentlyContinue
Copy-Item ".\requirements.txt" "$distDir\" -ErrorAction SilentlyContinue
Copy-Item ".\README.md" "$distDir\" -ErrorAction SilentlyContinue

# Create ZIP
Write-Log "Creating portable ZIP package"
$zipPath = ".\dist\WindowsAI-Portable-$Version.zip"
Compress-Archive -Path $distDir -DestinationPath $zipPath -Force

Write-Log "Build complete. Distribution in ./dist/"
Write-Log "Next: Test application and create GitHub release"
