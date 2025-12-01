# Windows AI Installer Code Signing Script
# Signs the installer executable with Authenticode certificate
# Supports both production certificates and test certificates

param(
    [Parameter(Mandatory=$true)]
    [string]$InstallerPath,

    [string]$CertificatePath = "",
    [string]$CertificatePassword = "",
    [string]$TimestampServer = "http://timestamp.digicert.com",
    [string]$ConfigFile = "$PSScriptRoot\sign-config.json",
    [switch]$UseTestCert = $false,
    [switch]$Verify = $true
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Windows AI Installer Code Signing" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# =====================================================================
# Load Configuration
# =====================================================================

$config = $null
if (Test-Path $ConfigFile) {
    Write-Host "[Config] Loading configuration from $ConfigFile..." -ForegroundColor Yellow
    $config = Get-Content $ConfigFile | ConvertFrom-Json
    Write-Host "[Config] Configuration loaded" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[Config] No configuration file found at $ConfigFile" -ForegroundColor Yellow
    Write-Host ""
}

# =====================================================================
# Validate Installer
# =====================================================================

Write-Host "[1/5] Validating installer..." -ForegroundColor Yellow

if (-not (Test-Path $InstallerPath)) {
    Write-Host "  ERROR: Installer not found at $InstallerPath" -ForegroundColor Red
    exit 1
}

$installerSize = [math]::Round((Get-Item $InstallerPath).Length / 1MB, 2)
Write-Host "  Installer: $InstallerPath" -ForegroundColor Gray
Write-Host "  Size: $installerSize MB" -ForegroundColor Gray
Write-Host "  Installer validated" -ForegroundColor Green
Write-Host ""

# =====================================================================
# Locate Certificate
# =====================================================================

Write-Host "[2/5] Locating certificate..." -ForegroundColor Yellow

$certToUse = $null
$certPasswordSecure = $null

if ($UseTestCert) {
    # Use test certificate
    Write-Host "  Using test certificate..." -ForegroundColor Gray
    $testCertPath = Join-Path $PSScriptRoot "test-cert.pfx"

    if (-not (Test-Path $testCertPath)) {
        Write-Host "  ERROR: Test certificate not found at $testCertPath" -ForegroundColor Red
        Write-Host "  Run create-test-cert.ps1 first to generate a test certificate" -ForegroundColor Yellow
        exit 1
    }

    $certToUse = $testCertPath
    $certPasswordSecure = ConvertTo-SecureString "test1234" -AsPlainText -Force
    Write-Host "  Test certificate found: $testCertPath" -ForegroundColor Green

} elseif ($CertificatePath -ne "") {
    # Use specified certificate
    Write-Host "  Using specified certificate..." -ForegroundColor Gray

    if (-not (Test-Path $CertificatePath)) {
        Write-Host "  ERROR: Certificate not found at $CertificatePath" -ForegroundColor Red
        exit 1
    }

    $certToUse = $CertificatePath

    if ($CertificatePassword -ne "") {
        $certPasswordSecure = ConvertTo-SecureString $CertificatePassword -AsPlainText -Force
    } else {
        Write-Host "  Enter certificate password:" -ForegroundColor Cyan
        $certPasswordSecure = Read-Host -AsSecureString
    }

    Write-Host "  Certificate found: $CertificatePath" -ForegroundColor Green

} elseif ($config -and $config.certificatePath) {
    # Use certificate from config
    Write-Host "  Using certificate from config..." -ForegroundColor Gray

    $configCertPath = $config.certificatePath
    if (-not [System.IO.Path]::IsPathRooted($configCertPath)) {
        $configCertPath = Join-Path $PSScriptRoot $configCertPath
    }

    if (-not (Test-Path $configCertPath)) {
        Write-Host "  ERROR: Certificate not found at $configCertPath" -ForegroundColor Red
        exit 1
    }

    $certToUse = $configCertPath

    if ($config.certificatePassword) {
        $certPasswordSecure = ConvertTo-SecureString $config.certificatePassword -AsPlainText -Force
    } else {
        Write-Host "  Enter certificate password:" -ForegroundColor Cyan
        $certPasswordSecure = Read-Host -AsSecureString
    }

    Write-Host "  Certificate found: $configCertPath" -ForegroundColor Green

} else {
    # Try to find certificate in Windows Certificate Store
    Write-Host "  Searching Windows Certificate Store..." -ForegroundColor Gray

    $cert = Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1

    if ($null -eq $cert) {
        $cert = Get-ChildItem -Path Cert:\LocalMachine\My -CodeSigningCert | Select-Object -First 1
    }

    if ($null -eq $cert) {
        Write-Host "  ERROR: No code signing certificate found" -ForegroundColor Red
        Write-Host "" -ForegroundColor Red
        Write-Host "  Options:" -ForegroundColor Yellow
        Write-Host "    1. Use test certificate: -UseTestCert" -ForegroundColor Yellow
        Write-Host "    2. Specify certificate: -CertificatePath <path> -CertificatePassword <password>" -ForegroundColor Yellow
        Write-Host "    3. Configure in sign-config.json" -ForegroundColor Yellow
        Write-Host "    4. Install certificate in Windows Certificate Store" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }

    Write-Host "  Certificate found in store: $($cert.Subject)" -ForegroundColor Green
    Write-Host "  Thumbprint: $($cert.Thumbprint)" -ForegroundColor Gray
    Write-Host "  Valid until: $($cert.NotAfter)" -ForegroundColor Gray
}

Write-Host ""

# =====================================================================
# Check SignTool
# =====================================================================

Write-Host "[3/5] Locating SignTool..." -ForegroundColor Yellow

$signTool = $null

# Common SignTool locations
$signToolPaths = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\8.1\bin\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\8.0\bin\x64\signtool.exe",
    "C:\Program Files (x86)\Microsoft SDKs\Windows\*\bin\*\signtool.exe"
)

foreach ($pattern in $signToolPaths) {
    $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $signTool = $found.FullName
        break
    }
}

if ($null -eq $signTool) {
    Write-Host "  ERROR: SignTool not found" -ForegroundColor Red
    Write-Host "  Install Windows SDK from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/" -ForegroundColor Yellow
    exit 1
}

Write-Host "  SignTool found: $signTool" -ForegroundColor Green
Write-Host ""

# =====================================================================
# Sign Installer
# =====================================================================

Write-Host "[4/5] Signing installer..." -ForegroundColor Yellow

try {
    if ($certToUse) {
        # Sign with PFX file
        Write-Host "  Signing with certificate file..." -ForegroundColor Gray

        $certPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($certPasswordSecure)
        )

        $signArgs = @(
            "sign",
            "/f", "`"$certToUse`"",
            "/p", "`"$certPasswordPlain`"",
            "/t", "`"$TimestampServer`"",
            "/fd", "SHA256",
            "/v",
            "`"$InstallerPath`""
        )

        $process = Start-Process -FilePath $signTool -ArgumentList $signArgs -NoNewWindow -Wait -PassThru

        if ($process.ExitCode -ne 0) {
            Write-Host "  ERROR: Signing failed with exit code $($process.ExitCode)" -ForegroundColor Red
            exit 1
        }

    } else {
        # Sign with certificate from store
        Write-Host "  Signing with certificate from store..." -ForegroundColor Gray

        $signArgs = @(
            "sign",
            "/sha1", $cert.Thumbprint,
            "/t", "`"$TimestampServer`"",
            "/fd", "SHA256",
            "/v",
            "`"$InstallerPath`""
        )

        $process = Start-Process -FilePath $signTool -ArgumentList $signArgs -NoNewWindow -Wait -PassThru

        if ($process.ExitCode -ne 0) {
            Write-Host "  ERROR: Signing failed with exit code $($process.ExitCode)" -ForegroundColor Red
            exit 1
        }
    }

    Write-Host "  Installer signed successfully!" -ForegroundColor Green
    Write-Host ""

} catch {
    Write-Host "  ERROR: Signing failed: $_" -ForegroundColor Red
    exit 1
}

# =====================================================================
# Verify Signature
# =====================================================================

if ($Verify) {
    Write-Host "[5/5] Verifying signature..." -ForegroundColor Yellow

    try {
        $verifyArgs = @(
            "verify",
            "/pa",
            "/v",
            "`"$InstallerPath`""
        )

        $process = Start-Process -FilePath $signTool -ArgumentList $verifyArgs -NoNewWindow -Wait -PassThru

        if ($process.ExitCode -eq 0) {
            Write-Host "  Signature verified successfully!" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: Signature verification failed" -ForegroundColor Yellow
            Write-Host "  This may be expected for test certificates" -ForegroundColor Gray
        }

    } catch {
        Write-Host "  WARNING: Verification failed: $_" -ForegroundColor Yellow
    }

    Write-Host ""
}

# =====================================================================
# Summary
# =====================================================================

Write-Host "================================================" -ForegroundColor Green
Write-Host "  SIGNING COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Signed installer: $InstallerPath" -ForegroundColor Cyan
Write-Host "  Size: $installerSize MB" -ForegroundColor Cyan
Write-Host "  Timestamp server: $TimestampServer" -ForegroundColor Cyan
Write-Host ""

if ($UseTestCert) {
    Write-Host "  NOTE: Signed with TEST certificate" -ForegroundColor Yellow
    Write-Host "  This is suitable for development/testing only" -ForegroundColor Yellow
    Write-Host "  For production, use a valid code signing certificate" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Code signing completed successfully!" -ForegroundColor Green
Write-Host ""
