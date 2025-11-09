# Universal Session Logger for Multi-CLI Operations
param(
    [string]$CliName,
    [string]$Command,
    [string]$LogDir = "C:\Users\antho\logs\unified_sessions"
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$sessionId = if (Test-Path "$LogDir\current_session_id.txt") { 
    Get-Content "$LogDir\current_session_id.txt" 
} else { 
    $timestamp 
}

New-Item -ItemType Directory -Path "$LogDir\$sessionId" -Force | Out-Null
$sessionId | Out-File "$LogDir\current_session_id.txt" -Force

$logFile = "$LogDir\$sessionId\$CliName`_$timestamp.log"
$entry = @{
    timestamp = Get-Date -Format "o"
    cli = $CliName
    command = $Command
    cwd = Get-Location
} | ConvertTo-Json -Compress

Add-Content -Path $logFile -Value $entry
Add-Content -Path "$LogDir\$sessionId\unified.jsonl" -Value $entry

return $logFile
