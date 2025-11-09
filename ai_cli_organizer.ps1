# AI CLI Log Organizer & Summarizer Agent
# Organizes all AI CLI directories, past logs, and creates detailed summaries
# Focuses ONLY on AI CLI related content

param(
    [switch]$Start,
    [switch]$Stop,
    [switch]$OrganizeNow
)

$pidFile = "C:\Users\antho\logs\unified_sessions\organizer_agent.pid"
$logFile = "C:\Users\antho\logs\unified_sessions\organizer_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

$aiCliDirs = @(
    "C:\Users\antho\.gemini",
    "C:\Users\antho\.claude",
    "C:\Users\antho\.codex",
    "C:\Users\antho\.opencode",
    "C:\Users\antho\.copilot",
    "C:\Users\antho\AI CLI",
    "C:\Users\antho\Windows-AI"
)

$archiveBase = "C:\Users\antho\logs\organized_archives"

function Write-OrgLog {
    param([string]$Message)
    "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) - $Message" | Tee-Object -FilePath $logFile -Append
}

function Organize-AICliDirectory {
    param([string]$DirPath)
    
    if (-not (Test-Path $DirPath)) { return }
    
    Write-OrgLog "Organizing: $DirPath"
    $dirName = Split-Path $DirPath -Leaf
    $archiveDir = "$archiveBase\$dirName\$(Get-Date -Format 'yyyyMMdd')"
    
    # Create organized structure
    $structure = @{
        'logs' = "$archiveDir\logs"
        'chat_history' = "$archiveDir\chat_history"
        'cache' = "$archiveDir\cache"
        'config' = "$archiveDir\config"
        'temp' = "$archiveDir\temp"
        'summaries' = "$archiveDir\summaries"
    }
    
    foreach ($folder in $structure.Values) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
    }
    
    # Move and organize logs
    Get-ChildItem $DirPath -Recurse -File -ErrorAction SilentlyContinue | 
        Where-Object { $_.Extension -match '\.(log|txt)$' } |
        ForEach-Object {
            $dest = "$($structure['logs'])\$($_.Name)"
            Copy-Item $_.FullName $dest -Force -ErrorAction SilentlyContinue
            Write-OrgLog "Archived log: $($_.Name)"
        }
    
    # Organize chat history files
    Get-ChildItem $DirPath -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match 'chat|history|conversation' } |
        ForEach-Object {
            Copy-Item $_.FullName "$($structure['chat_history'])\$($_.Name)" -Force -ErrorAction SilentlyContinue
            Write-OrgLog "Archived chat: $($_.Name)"
        }
    
    # Organize config files
    Get-ChildItem $DirPath -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -match '\.(json|yaml|yml|toml|conf|config)$' } |
        ForEach-Object {
            Copy-Item $_.FullName "$($structure['config'])\$($_.Name)" -Force -ErrorAction SilentlyContinue
        }
    
    # Generate comprehensive summary
    Generate-DirectorySummary -DirPath $DirPath -OutputPath "$($structure['summaries'])\directory_summary.md"
}

function Generate-DirectorySummary {
    param(
        [string]$DirPath,
        [string]$OutputPath
    )
    
    $files = Get-ChildItem $DirPath -Recurse -File -ErrorAction SilentlyContinue
    $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
    
    $logFiles = $files | Where-Object { $_.Extension -match '\.(log|txt)$' }
    $chatFiles = $files | Where-Object { $_.Name -match 'chat|history|conversation' }
    $configFiles = $files | Where-Object { $_.Extension -match '\.(json|yaml|yml|toml|conf)$' }
    
    $summary = @"
# AI CLI Directory Summary: $(Split-Path $DirPath -Leaf)
**Generated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**Path:** $DirPath

## Overview
- **Total Files:** $($files.Count)
- **Total Size:** $([math]::Round($totalSize/1MB, 2)) MB
- **Log Files:** $($logFiles.Count)
- **Chat History Files:** $($chatFiles.Count)
- **Config Files:** $($configFiles.Count)

## Directory Structure
``````
$(Get-ChildItem $DirPath -Recurse -Directory -ErrorAction SilentlyContinue | Select-Object -First 50 FullName | ForEach-Object { $_.FullName -replace [regex]::Escape($DirPath), '.' } | Out-String)
``````

## Recent Log Files
| File | Size | Last Modified |
|------|------|---------------|
$(($logFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 20 | ForEach-Object { "| $($_.Name) | $([math]::Round($_.Length/1KB, 2)) KB | $($_.LastWriteTime) |" }) -join "`n")

## Chat History Files
$(($chatFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 10 | ForEach-Object {
    $lines = (Get-Content $_.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
    "- **$($_.Name)** - $lines lines, $([math]::Round($_.Length/1KB, 2)) KB"
}) -join "`n")

## Configuration Files
$(($configFiles | ForEach-Object { "- $($_.Name)" }) -join "`n")

## Storage Breakdown
``````
$((Get-ChildItem $DirPath -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    "$($_.Name): $([math]::Round($size/1MB, 2)) MB"
}) | Out-String)
``````

## Key Observations
- Oldest file: $(($files | Sort-Object CreationTime | Select-Object -First 1).Name) ($(($files | Sort-Object CreationTime | Select-Object -First 1).CreationTime))
- Newest file: $(($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).Name) ($(($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime))
- Largest file: $(($files | Sort-Object Length -Descending | Select-Object -First 1).Name) ($([math]::Round(($files | Sort-Object Length -Descending | Select-Object -First 1).Length/1MB, 2)) MB)

---
*Generated by AI CLI Organizer Agent*
"@
    
    $summary | Out-File $OutputPath -Encoding UTF8
    Write-OrgLog "Generated summary: $OutputPath"
}

if ($Stop) {
    if (Test-Path $pidFile) {
        $jobId = Get-Content $pidFile
        Stop-Job -Id $jobId -ErrorAction SilentlyContinue
        Remove-Job -Id $jobId -ErrorAction SilentlyContinue
        Remove-Item $pidFile
        Write-OrgLog "Organizer agent stopped"
    }
    return
}

if ($OrganizeNow) {
    Write-Host "Starting immediate organization..." -ForegroundColor Yellow
    foreach ($dir in $aiCliDirs) {
        if (Test-Path $dir) {
            Write-Host "  Processing: $dir" -ForegroundColor Cyan
            Organize-AICliDirectory -DirPath $dir
        }
    }
    Write-Host "✓ Organization complete!" -ForegroundColor Green
    Write-Host "Archives: $archiveBase" -ForegroundColor Gray
    return
}

if ($Start) {
    Write-OrgLog "AI CLI Organizer Agent starting..."
    
    # Background job for continuous organization
    $job = Start-Job -ScriptBlock {
        param($dirs, $archive, $log)
        
        function Write-Log {
            param([string]$Msg)
            "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) - $Msg" | Out-File $log -Append
        }
        
        while ($true) {
            Start-Sleep -Seconds 300  # Run every 5 minutes
            
            Write-Log "Running periodic organization..."
            
            foreach ($dir in $dirs) {
                if (Test-Path $dir) {
                    # Look for new logs in last 10 minutes
                    $newLogs = Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue |
                        Where-Object { $_.Extension -match '\.(log|txt)$' -and $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) }
                    
                    if ($newLogs.Count -gt 0) {
                        Write-Log "Found $($newLogs.Count) new logs in $dir"
                        # Organize this directory
                        # (simplified version for background job)
                        $dirName = Split-Path $dir -Leaf
                        $dest = "$archive\$dirName\$(Get-Date -Format 'yyyyMMdd')\logs"
                        New-Item -ItemType Directory -Path $dest -Force | Out-Null
                        
                        foreach ($log in $newLogs) {
                            Copy-Item $log.FullName "$dest\$($log.Name)" -Force -ErrorAction SilentlyContinue
                        }
                    }
                }
            }
        }
    } -ArgumentList $aiCliDirs, $archiveBase, $logFile
    
    $job.Id | Out-File $pidFile
    Write-OrgLog "Organizer agent started (Job ID: $($job.Id))"
    
    Write-Host "✓ AI CLI Organizer Agent ACTIVE" -ForegroundColor Green
    Write-Host "  - Monitoring: $(($aiCliDirs | ForEach-Object { Split-Path $_ -Leaf }) -join ', ')" -ForegroundColor Cyan
    Write-Host "  - Archives: $archiveBase" -ForegroundColor Gray
    Write-Host "  - Runs every: 5 minutes" -ForegroundColor Yellow
    Write-Host "  - To stop: .\ai_cli_organizer.ps1 -Stop" -ForegroundColor Gray
    
    return $job
}

Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  .\ai_cli_organizer.ps1 -Start         # Start background agent"
Write-Host "  .\ai_cli_organizer.ps1 -OrganizeNow   # Run organization once"
Write-Host "  .\ai_cli_organizer.ps1 -Stop          # Stop background agent"
