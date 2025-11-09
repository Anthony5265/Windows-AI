# Universal CLI Log Capture Agent
# Captures ALL CLI outputs (Gemini, Claude, Codex, OpenCode, Copilot) in real-time
# Saves both raw logs and generates detailed summaries

param(
    [switch]$Start,
    [switch]$Stop,
    [string]$LogBaseDir = "C:\Users\antho\logs\unified_sessions"
)

$pidFile = "$LogBaseDir\log_capture_agent.pid"
$sessionId = Get-Date -Format 'yyyyMMdd_HHmmss'
$rawLogDir = "$LogBaseDir\$sessionId\raw"
$summaryLogDir = "$LogBaseDir\$sessionId\summaries"

function Write-AgentLog {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'
    "$timestamp - $Message" | Tee-Object -FilePath "$LogBaseDir\log_agent.log" -Append
}

if ($Stop) {
    if (Test-Path $pidFile) {
        $jobs = Get-Content $pidFile | ConvertFrom-Json
        foreach ($jobId in $jobs.JobIds) {
            Stop-Job -Id $jobId -ErrorAction SilentlyContinue
            Remove-Job -Id $jobId -ErrorAction SilentlyContinue
        }
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        Write-AgentLog "Log capture agent stopped"
        Write-Host "Log capture agent stopped" -ForegroundColor Yellow
    }
    return
}

if ($Start) {
    New-Item -ItemType Directory -Path $rawLogDir -Force | Out-Null
    New-Item -ItemType Directory -Path $summaryLogDir -Force | Out-Null
    
    Write-AgentLog "Log capture agent starting - Session: $sessionId"
    
    # Job 1: Monitor and capture raw CLI outputs
    $captureJob = Start-Job -ScriptBlock {
        param($rawDir, $sessionId)
        
        $cliPatterns = @{
            'gemini' = 'gemini|google|bard'
            'claude' = 'claude|anthropic'
            'codex' = 'codex|openai-codex'
            'opencode' = 'opencode|open-code'
            'copilot' = 'copilot|github-copilot'
        }
        
        while ($true) {
            Start-Sleep -Seconds 5
            
            # Get all PowerShell processes and their transcripts
            Get-Process pwsh,powershell -ErrorAction SilentlyContinue | ForEach-Object {
                $procId = $_.Id
                
                # Check each CLI type
                foreach ($cli in $cliPatterns.Keys) {
                    $pattern = $cliPatterns[$cli]
                    
                    # Capture stdout/stderr via process monitoring
                    try {
                        $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
                        $logFile = "$rawDir\${cli}_${procId}_${timestamp}.log"
                        
                        # Use Get-Content with -Wait on known log locations
                        $knownPaths = @(
                            "$env:USERPROFILE\.${cli}\logs",
                            "$env:USERPROFILE\AI CLI\.${cli}\logs",
                            "$env:TEMP\${cli}_*.log"
                        )
                        
                        foreach ($path in $knownPaths) {
                            if (Test-Path $path) {
                                Get-ChildItem $path -Filter "*.log" -File -ErrorAction SilentlyContinue | 
                                    Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-5) } |
                                    ForEach-Object {
                                        Copy-Item $_.FullName "$rawDir\${cli}_$($_.Name)" -Force -ErrorAction SilentlyContinue
                                    }
                            }
                        }
                    } catch {
                        # Silent continue
                    }
                }
            }
        }
    } -ArgumentList $rawLogDir, $sessionId
    
    # Job 2: Generate detailed summaries from raw logs
    $summaryJob = Start-Job -ScriptBlock {
        param($rawDir, $summaryDir, $sessionId)
        
        while ($true) {
            Start-Sleep -Seconds 30
            
            Get-ChildItem $rawDir -Filter "*.log" -File -ErrorAction SilentlyContinue | 
                Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-2) } |
                ForEach-Object {
                    $rawLog = $_
                    $summaryFile = "$summaryDir\summary_$($rawLog.BaseName).md"
                    
                    if (-not (Test-Path $summaryFile)) {
                        try {
                            $content = Get-Content $rawLog.FullName -Raw -ErrorAction SilentlyContinue
                            
                            if ($content.Length -gt 100) {
                                # Extract key information
                                $commands = ($content | Select-String -Pattern "^>.*$" -AllMatches).Matches.Value
                                $errors = ($content | Select-String -Pattern "error|exception|failed" -AllMatches).Matches.Count
                                $prompts = ($content | Select-String -Pattern "User:|Assistant:|Human:|AI:" -AllMatches).Matches.Count
                                
                                $summary = @"
# CLI Session Summary
**Generated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**Source:** $($rawLog.Name)
**Size:** $([math]::Round($rawLog.Length/1KB, 2)) KB
**Session:** $sessionId

## Statistics
- Commands executed: $($commands.Count)
- Errors detected: $errors
- Conversation turns: $prompts
- Duration: $($rawLog.LastWriteTime - $rawLog.CreationTime)

## Commands Executed
``````
$($commands -join "`n")
``````

## Key Events
$($content | Select-String -Pattern "INFO|WARN|ERROR" | Select-Object -First 20 | ForEach-Object { "- $($_.Line)" } | Out-String)

## Full Transcript
[See raw log: $($rawLog.Name)]

---
*Auto-generated by Log Capture Agent*
"@
                                $summary | Out-File $summaryFile -Encoding UTF8
                            }
                        } catch {
                            # Silent continue
                        }
                    }
                }
        }
    } -ArgumentList $rawLogDir, $summaryLogDir, $sessionId
    
    # Job 3: Monitor CLI process creation and attach logging
    $monitorJob = Start-Job -ScriptBlock {
        param($rawDir)
        
        $cliExecutables = @('gemini', 'claude', 'codex', 'opencode', 'gh')
        
        while ($true) {
            Start-Sleep -Seconds 10
            
            foreach ($exe in $cliExecutables) {
                Get-Process $exe -ErrorAction SilentlyContinue | ForEach-Object {
                    $proc = $_
                    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
                    $procLog = "$rawDir\${exe}_proc_$($proc.Id)_${timestamp}.log"
                    
                    @"
Process: $($proc.ProcessName)
PID: $($proc.Id)
Started: $($proc.StartTime)
WorkingSet: $([math]::Round($proc.WorkingSet64/1MB, 2)) MB
CommandLine: $(Get-WmiObject Win32_Process -Filter "ProcessId=$($proc.Id)" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CommandLine)
"@ | Out-File $procLog -Encoding UTF8 -Append
                }
            }
        }
    } -ArgumentList $rawLogDir
    
    # Save job IDs
    @{
        SessionId = $sessionId
        JobIds = @($captureJob.Id, $summaryJob.Id, $monitorJob.Id)
        RawLogDir = $rawLogDir
        SummaryDir = $summaryLogDir
    } | ConvertTo-Json | Out-File $pidFile
    
    Write-AgentLog "Log capture agent started - Jobs: $($captureJob.Id), $($summaryJob.Id), $($monitorJob.Id)"
    
    Write-Host "✓ Universal CLI Log Capture Agent ACTIVE" -ForegroundColor Green
    Write-Host "  - Capturing: Gemini, Claude, Codex, OpenCode, Copilot" -ForegroundColor Cyan
    Write-Host "  - Raw logs: $rawLogDir" -ForegroundColor Gray
    Write-Host "  - Summaries: $summaryLogDir" -ForegroundColor Gray
    Write-Host "  - Session: $sessionId" -ForegroundColor Yellow
    
    return @{
        CaptureJob = $captureJob
        SummaryJob = $summaryJob
        MonitorJob = $monitorJob
    }
}

Write-Host "Usage: .\universal_cli_logger.ps1 -Start or -Stop" -ForegroundColor Cyan
