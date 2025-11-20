# Windows AI Context Menu Installation Script
# Run as Administrator

$ErrorActionPreference = "Stop"

Write-Host "Installing Windows AI Context Menu Integration..." -ForegroundColor Cyan

# Get the installation directory
$InstallDir = Split-Path -Parent $PSCommandPath
$HandlerPath = Join-Path $InstallDir "handler.exe"

# Check if handler exists
if (-not (Test-Path $HandlerPath)) {
    Write-Host "ERROR: handler.exe not found at $HandlerPath" -ForegroundColor Red
    Write-Host "Please build the handler first using PyInstaller" -ForegroundColor Yellow
    exit 1
}

# Registry paths
$FileContextMenu = "Registry::HKEY_CLASSES_ROOT\*\shell"
$FolderContextMenu = "Registry::HKEY_CLASSES_ROOT\Directory\shell"

Write-Host "Adding file context menu items..." -ForegroundColor Green

# Analyze File
$AnalyzeKey = "$FileContextMenu\WindowsAI.Analyze"
New-Item -Path $AnalyzeKey -Force | Out-Null
Set-ItemProperty -Path $AnalyzeKey -Name "(Default)" -Value "Analyze with Windows AI"
Set-ItemProperty -Path $AnalyzeKey -Name "Icon" -Value "$HandlerPath,0"

$AnalyzeCommand = "$AnalyzeKey\command"
New-Item -Path $AnalyzeCommand -Force | Out-Null
Set-ItemProperty -Path $AnalyzeCommand -Name "(Default)" -Value "`"$HandlerPath`" analyze `"%1`""

# Summarize File
$SummarizeKey = "$FileContextMenu\WindowsAI.Summarize"
New-Item -Path $SummarizeKey -Force | Out-Null
Set-ItemProperty -Path $SummarizeKey -Name "(Default)" -Value "Summarize with Windows AI"
Set-ItemProperty -Path $SummarizeKey -Name "Icon" -Value "$HandlerPath,0"

$SummarizeCommand = "$SummarizeKey\command"
New-Item -Path $SummarizeCommand -Force | Out-Null
Set-ItemProperty -Path $SummarizeCommand -Name "(Default)" -Value "`"$HandlerPath`" summarize `"%1`""

Write-Host "Adding folder context menu items..." -ForegroundColor Green

# Ask About Folder
$AskFolderKey = "$FolderContextMenu\WindowsAI.Ask"
New-Item -Path $AskFolderKey -Force | Out-Null
Set-ItemProperty -Path $AskFolderKey -Name "(Default)" -Value "Ask Windows AI About This Folder"
Set-ItemProperty -Path $AskFolderKey -Name "Icon" -Value "$HandlerPath,0"

$AskFolderCommand = "$AskFolderKey\command"
New-Item -Path $AskFolderCommand -Force | Out-Null
Set-ItemProperty -Path $AskFolderCommand -Name "(Default)" -Value "`"$HandlerPath`" ask `"%1`""

# Ask About File (also for files)
$AskFileKey = "$FileContextMenu\WindowsAI.Ask"
New-Item -Path $AskFileKey -Force | Out-Null
Set-ItemProperty -Path $AskFileKey -Name "(Default)" -Value "Ask Windows AI"
Set-ItemProperty -Path $AskFileKey -Name "Icon" -Value "$HandlerPath,0"

$AskFileCommand = "$AskFileKey\command"
New-Item -Path $AskFileCommand -Force | Out-Null
Set-ItemProperty -Path $AskFileCommand -Name "(Default)" -Value "`"$HandlerPath`" ask `"%1`""

Write-Host ""
Write-Host "✓ Windows AI Context Menu Integration installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now right-click on files and folders to:" -ForegroundColor Cyan
Write-Host "  - Analyze with Windows AI" -ForegroundColor White
Write-Host "  - Summarize with Windows AI" -ForegroundColor White
Write-Host "  - Ask Windows AI" -ForegroundColor White
Write-Host ""

# Refresh Explorer
$code = @'
[DllImport("shell32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern void SHChangeNotify(uint wEventId, uint uFlags, IntPtr dwItem1, IntPtr dwItem2);
'@

try {
    Add-Type -MemberDefinition $code -Namespace Win32 -Name Shell32
    [Win32.Shell32]::SHChangeNotify(0x8000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
    Write-Host "Explorer refreshed" -ForegroundColor Gray
} catch {
    Write-Host "Please restart Explorer manually to see the changes" -ForegroundColor Yellow
}
