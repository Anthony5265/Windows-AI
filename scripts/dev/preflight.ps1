# Preflight Check Script
# Verifies Windows prerequisites before Windows-AI installation
# Created: 2025-11-15

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Windows-AI Preflight Check" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

$issues = @()
$warnings = @()

# Check Windows version
Write-Host "[1/10] Checking Windows version..." -ForegroundColor Yellow
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 10) {
    $issues += "Windows 10 or later required (found: $osVersion)"
} else {
    Write-Host "  ✓ Windows $($osVersion.Major).$($osVersion.Minor) detected" -ForegroundColor Green
}

# Check PowerShell version
Write-Host "[2/10] Checking PowerShell version..." -ForegroundColor Yellow
if ($PSVersionTable.PSVersion.Major -lt 5) {
    $issues += "PowerShell 5.0 or later required (found: $($PSVersionTable.PSVersion))"
} else {
    Write-Host "  ✓ PowerShell $($PSVersionTable.PSVersion) detected" -ForegroundColor Green
}

# Check Python
Write-Host "[3/10] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            $issues += "Python 3.8+ required (found: $pythonVersion)"
        } else {
            Write-Host "  ✓ $pythonVersion detected" -ForegroundColor Green
        }
    }
} catch {
    $issues += "Python not found in PATH"
}

# Check Node.js
Write-Host "[4/10] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match "v(\d+)\.") {
        $major = [int]$matches[1]
        if ($major -lt 14) {
            $issues += "Node.js 14+ required (found: $nodeVersion)"
        } else {
            Write-Host "  ✓ Node.js $nodeVersion detected" -ForegroundColor Green
        }
    }
} catch {
    $issues += "Node.js not found in PATH"
}

# Check Git
Write-Host "[5/10] Checking Git..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    Write-Host "  ✓ $gitVersion detected" -ForegroundColor Green
} catch {
    $warnings += "Git not found (optional but recommended)"
}

# Check available disk space
Write-Host "[6/10] Checking disk space..." -ForegroundColor Yellow
$drive = Get-PSDrive -Name C
$freeGB = [math]::Round($drive.Free / 1GB, 2)
if ($freeGB -lt 5) {
    $issues += "At least 5GB free space required (found: ${freeGB}GB)"
} else {
    Write-Host "  ✓ ${freeGB}GB free space available" -ForegroundColor Green
}

# Check memory
Write-Host "[7/10] Checking system memory..." -ForegroundColor Yellow
$ram = Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum
$ramGB = [math]::Round($ram.Sum / 1GB, 2)
if ($ramGB -lt 4) {
    $warnings += "4GB+ RAM recommended (found: ${ramGB}GB)"
} else {
    Write-Host "  ✓ ${ramGB}GB RAM detected" -ForegroundColor Green
}

# Check execution policy
Write-Host "[8/10] Checking execution policy..." -ForegroundColor Yellow
$policy = Get-ExecutionPolicy
if ($policy -eq "Restricted") {
    $issues += "Execution policy is Restricted. Run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser"
} else {
    Write-Host "  ✓ Execution policy: $policy" -ForegroundColor Green
}

# Check internet connectivity
Write-Host "[9/10] Checking internet connectivity..." -ForegroundColor Yellow
try {
    $null = Test-Connection -ComputerName google.com -Count 1 -Quiet
    Write-Host "  ✓ Internet connection available" -ForegroundColor Green
} catch {
    $warnings += "No internet connection (required for downloading dependencies)"
}

# Check administrator privileges
Write-Host "[10/10] Checking administrator privileges..." -ForegroundColor Yellow
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Host "  ✓ Running with administrator privileges" -ForegroundColor Green
} else {
    $warnings += "Not running as administrator (may be required for some features)"
}

# Summary
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Preflight Check Summary" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✓ All checks passed! System is ready for Windows-AI installation.`n" -ForegroundColor Green
    exit 0
} else {
    if ($issues.Count -gt 0) {
        Write-Host "CRITICAL ISSUES ($($issues.Count)):" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "  ✗ $issue" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "WARNINGS ($($warnings.Count)):" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  ! $warning" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    if ($issues.Count -gt 0) {
        Write-Host "Please resolve critical issues before installing Windows-AI.`n" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "Warnings detected but system can proceed with installation.`n" -ForegroundColor Yellow
        exit 0
    }
}
