# STDIN Yes Feeder - Pipes 'y' responses to any waiting prompts
# This is the nuclear option - automatically feeds 'y' to stdin

param(
    [int]$Interval = 2000,  # Send 'y' every 2 seconds
    [switch]$Start,
    [switch]$Stop
)

$pidFile = "C:\Users\antho\logs\unified_sessions\yes_feeder.pid"
$logFile = "C:\Users\antho\logs\unified_sessions\yes_feeder_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message)
    "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) - $Message" | Tee-Object -FilePath $logFile -Append
}

if ($Stop) {
    if (Test-Path $pidFile) {
        $pid = Get-Content $pidFile
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Remove-Item $pidFile
        Write-Log "Yes-feeder stopped (PID: $pid)"
        Write-Host "Yes-feeder stopped" -ForegroundColor Yellow
    }
    return
}

if ($Start) {
    # Start background job that periodically sends 'y' to console
    $job = Start-Job -ScriptBlock {
        param($interval, $log)
        
        while ($true) {
            Start-Sleep -Milliseconds $interval
            
            # Try to send 'y' + Enter to stdin, also just Enter alone
            # This will auto-respond to any blocking prompts
            try {
                $wshell = New-Object -ComObject wscript.shell
                $wshell.SendKeys('y')
                Start-Sleep -Milliseconds 50
                $wshell.SendKeys('~')  # ~ is Enter
                Start-Sleep -Milliseconds 50
                $wshell.SendKeys('~')  # Send Enter again for prompts that just need Enter
            } catch {
                # Silent fail
            }
        }
    } -ArgumentList $Interval, $logFile
    
    $job.Id | Out-File $pidFile
    Write-Log "Yes-feeder started (Job ID: $($job.Id))"
    Write-Host "Yes-feeder running - auto-sending 'y' every $($Interval)ms" -ForegroundColor Green
    Write-Host "To stop: .\stdin_yes_feeder.ps1 -Stop" -ForegroundColor Yellow
    
    return $job
}

Write-Host "Usage: .\stdin_yes_feeder.ps1 -Start or -Stop" -ForegroundColor Cyan
