# Windows AI Test Certificate Generator
# Creates a self-signed code signing certificate for testing purposes
# NOT FOR PRODUCTION USE - Test certificates will show security warnings

param(
    [string]$SubjectName = "CN=Windows AI Test Certificate",
    [string]$Password = "test1234",
    [int]$ValidYears = 2,
    [string]$OutputPath = "$PSScriptRoot\test-cert.pfx",
    [switch]$InstallToStore = $false
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Windows AI Test Certificate Generator" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "WARNING: This creates a TEST certificate only!" -ForegroundColor Yellow
Write-Host "For production, obtain a certificate from a trusted CA" -ForegroundColor Yellow
Write-Host ""

# =====================================================================
# Check Prerequisites
# =====================================================================

Write-Host "[1/4] Checking prerequisites..." -ForegroundColor Yellow

# Check if running on Windows
if ($PSVersionTable.Platform -and $PSVersionTable.Platform -ne "Win32NT") {
    Write-Host "  ERROR: This script must run on Windows" -ForegroundColor Red
    exit 1
}

# Check if PowerShell version supports New-SelfSignedCertificate
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "  ERROR: PowerShell 5.0 or later required" -ForegroundColor Red
    Write-Host "  Current version: $($PSVersionTable.PSVersion)" -ForegroundColor Red
    exit 1
}

Write-Host "  Prerequisites met" -ForegroundColor Green
Write-Host ""

# =====================================================================
# Generate Certificate
# =====================================================================

Write-Host "[2/4] Generating test certificate..." -ForegroundColor Yellow

try {
    # Create certificate parameters
    $certParams = @{
        Subject = $SubjectName
        Type = "CodeSigning"
        KeyAlgorithm = "RSA"
        KeyLength = 2048
        HashAlgorithm = "SHA256"
        NotAfter = (Get-Date).AddYears($ValidYears)
        CertStoreLocation = "Cert:\CurrentUser\My"
        KeyUsage = "DigitalSignature"
        TextExtension = @("2.5.29.37={text}1.3.6.1.5.5.7.3.3") # Code Signing EKU
    }

    Write-Host "  Creating self-signed certificate..." -ForegroundColor Gray
    Write-Host "    Subject: $SubjectName" -ForegroundColor Gray
    Write-Host "    Valid for: $ValidYears years" -ForegroundColor Gray
    Write-Host "    Algorithm: RSA 2048, SHA256" -ForegroundColor Gray

    $cert = New-SelfSignedCertificate @certParams

    Write-Host "  Certificate created successfully!" -ForegroundColor Green
    Write-Host "    Thumbprint: $($cert.Thumbprint)" -ForegroundColor Gray
    Write-Host "    Valid from: $($cert.NotBefore)" -ForegroundColor Gray
    Write-Host "    Valid until: $($cert.NotAfter)" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host "  ERROR: Failed to create certificate: $_" -ForegroundColor Red
    exit 1
}

# =====================================================================
# Export to PFX
# =====================================================================

Write-Host "[3/4] Exporting certificate to PFX..." -ForegroundColor Yellow

try {
    # Convert password to secure string
    $passwordSecure = ConvertTo-SecureString -String $Password -Force -AsPlainText

    # Export certificate
    Write-Host "  Exporting to: $OutputPath" -ForegroundColor Gray
    Export-PfxCertificate -Cert $cert -FilePath $OutputPath -Password $passwordSecure | Out-Null

    if (Test-Path $OutputPath) {
        $fileSize = [math]::Round((Get-Item $OutputPath).Length / 1KB, 2)
        Write-Host "  Certificate exported successfully!" -ForegroundColor Green
        Write-Host "    File: $OutputPath" -ForegroundColor Gray
        Write-Host "    Size: $fileSize KB" -ForegroundColor Gray
        Write-Host "    Password: $Password" -ForegroundColor Gray
    } else {
        Write-Host "  ERROR: Export failed - file not created" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

} catch {
    Write-Host "  ERROR: Failed to export certificate: $_" -ForegroundColor Red
    exit 1
}

# =====================================================================
# Install to Trusted Root (Optional)
# =====================================================================

if ($InstallToStore) {
    Write-Host "[4/4] Installing certificate to Trusted Root..." -ForegroundColor Yellow

    try {
        # Export public key
        $cerPath = [System.IO.Path]::ChangeExtension($OutputPath, ".cer")
        Export-Certificate -Cert $cert -FilePath $cerPath | Out-Null

        # Import to Trusted Root
        Write-Host "  Installing to Trusted Root Certification Authorities..." -ForegroundColor Gray
        Write-Host "  (This requires administrator privileges)" -ForegroundColor Gray

        Import-Certificate -FilePath $cerPath -CertStoreLocation "Cert:\LocalMachine\Root" | Out-Null

        Write-Host "  Certificate installed to Trusted Root" -ForegroundColor Green
        Write-Host ""

        # Clean up temporary CER file
        Remove-Item $cerPath -Force

    } catch {
        Write-Host "  WARNING: Failed to install to Trusted Root: $_" -ForegroundColor Yellow
        Write-Host "  You may need to run this script as Administrator" -ForegroundColor Yellow
        Write-Host "  Or manually install the certificate to Trusted Root" -ForegroundColor Yellow
        Write-Host ""
    }

} else {
    Write-Host "[4/4] Skipping Trusted Root installation" -ForegroundColor Gray
    Write-Host "  Use -InstallToStore to install certificate to Trusted Root" -ForegroundColor Gray
    Write-Host ""
}

# =====================================================================
# Clean up Certificate Store
# =====================================================================

# Remove certificate from personal store (we only need the PFX file)
Write-Host "Cleaning up..." -ForegroundColor Yellow
try {
    Remove-Item -Path "Cert:\CurrentUser\My\$($cert.Thumbprint)" -Force
    Write-Host "  Certificate removed from personal store" -ForegroundColor Gray
} catch {
    Write-Host "  WARNING: Could not remove certificate from store: $_" -ForegroundColor Yellow
}

Write-Host ""

# =====================================================================
# Summary
# =====================================================================

Write-Host "================================================" -ForegroundColor Green
Write-Host "  TEST CERTIFICATE CREATED!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Certificate file: $OutputPath" -ForegroundColor Cyan
Write-Host "  Password: $Password" -ForegroundColor Cyan
Write-Host "  Subject: $SubjectName" -ForegroundColor Cyan
Write-Host "  Valid until: $($cert.NotAfter.ToString('yyyy-MM-dd'))" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Usage:" -ForegroundColor Yellow
Write-Host "    .\sign-installer.ps1 -InstallerPath <path> -UseTestCert" -ForegroundColor White
Write-Host ""

if (-not $InstallToStore) {
    Write-Host "  NOTE: Test certificate not installed to Trusted Root" -ForegroundColor Yellow
    Write-Host "  Signed installers will show security warnings" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  To install to Trusted Root (removes warnings):" -ForegroundColor Yellow
    Write-Host "    .\create-test-cert.ps1 -InstallToStore" -ForegroundColor White
    Write-Host "  (Requires Administrator privileges)" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "IMPORTANT: This is a TEST certificate only!" -ForegroundColor Red
Write-Host "For production releases, obtain a certificate from a trusted CA:" -ForegroundColor Red
Write-Host "  - DigiCert: https://www.digicert.com/code-signing" -ForegroundColor Gray
Write-Host "  - Sectigo: https://sectigo.com/ssl-certificates-tls/code-signing" -ForegroundColor Gray
Write-Host "  - GlobalSign: https://www.globalsign.com/en/code-signing-certificate" -ForegroundColor Gray
Write-Host ""

Write-Host "Test certificate generation completed!" -ForegroundColor Green
Write-Host ""
