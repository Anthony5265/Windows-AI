# Windows AI Context Menu Uninstallation Script
# Run as Administrator

$ErrorActionPreference = "Stop"

Write-Host "Uninstalling Windows AI Context Menu Integration..." -ForegroundColor Cyan

# Registry paths
$FileContextMenu = "Registry::HKEY_CLASSES_ROOT\*\shell"
$FolderContextMenu = "Registry::HKEY_CLASSES_ROOT\Directory\shell"

# Remove all Windows AI context menu entries
$keys = @(
    "$FileContextMenu\WindowsAI.Analyze",
    "$FileContextMenu\WindowsAI.Summarize",
    "$FileContextMenu\WindowsAI.Ask",
    "$FolderContextMenu\WindowsAI.Ask"
)

foreach ($key in $keys) {
    if (Test-Path $key) {
        Remove-Item -Path $key -Recurse -Force
        Write-Host "Removed: $key" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "✓ Windows AI Context Menu Integration uninstalled successfully!" -ForegroundColor Green
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
