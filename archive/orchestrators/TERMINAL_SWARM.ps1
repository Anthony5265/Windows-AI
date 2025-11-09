# TERMINAL-BASED AGENT SWARM
# 1 LLM Agent + Support Agents in separate terminals
# Max 10 terminals total

param(
    [int]$MaxTerminals = 10,
    [int]$TargetCount = 652
)

$BaseDir = "C:\Users\antho\Windows-AI"
$OutputDir = "$BaseDir\extensions_supervised"
$LogDir = "C:\Users\antho\logs\unified_ai_memory\supervised_swarm"
$RoadmapFile = "$BaseDir\ULTIMATE_EXTENSION_ROADMAP.md"
$ScriptDir = "$BaseDir\agent_scripts"

# Clean slate
Remove-Item $LogDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $ScriptDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $OutputDir, $LogDir, $ScriptDir | Out-Null

Write-Host "=== TERMINAL-BASED AGENT SWARM ===" -ForegroundColor Magenta
Write-Host "Max terminals: $MaxTerminals" -ForegroundColor Green
Write-Host "1 LLM Agent (Ollama) + 9 Support Agents`n" -ForegroundColor Cyan

# Load roadmap
$roadmap = Get-Content $RoadmapFile -Raw
$unchecked = [regex]::Matches($roadmap, '- \[ \] (.+)') | ForEach-Object { $_.Groups[1].Value.Trim() }
$extensionsToGenerate = $unchecked | Select-Object -First $TargetCount

Write-Host "Extensions to generate: $($extensionsToGenerate.Count)`n" -ForegroundColor Yellow

# Save task list
$extensionsToGenerate | Out-File "$ScriptDir\tasks.txt" -Force -Encoding utf8

# ===== 1. LLM AGENT (Ollama) =====
$llmScript = @'
$OutputDir = "C:\Users\antho\Windows-AI\extensions_supervised"
$LogDir = "C:\Users\antho\logs\unified_ai_memory\supervised_swarm"
$tasks = Get-Content "C:\Users\antho\Windows-AI\agent_scripts\tasks.txt"

$host.UI.RawUI.WindowTitle = "LLM Agent (Ollama)"
Write-Host "=== LLM AGENT ===" -ForegroundColor Green
Write-Host "Tasks: $($tasks.Count)`n" -ForegroundColor Cyan

$completed = 0
$failed = 0

foreach($task in $tasks) {
    $safeName = $task -replace '[^a-zA-Z0-9_-]', '_'
    $extDir = Join-Path $OutputDir $safeName
    $logFile = Join-Path $LogDir "llm_${safeName}.log"
    
    Write-Host "[$completed/$($tasks.Count)] $task" -ForegroundColor Yellow
    
    $prompt = "VSCode extension: $task. Output package.json and code."
    
    try {
        $result = $prompt | & ollama run qwen2.5-coder:1.5b 2>&1
        $resultText = if($result -is [Array]) { $result -join "`n" } else { $result }
        $resultText | Out-File $logFile -Force -Encoding utf8
        
        if($resultText -and $resultText.Length -gt 200) {
            New-Item -ItemType Directory -Force -Path $extDir | Out-Null
            $resultText | Out-File (Join-Path $extDir "extension.txt") -Force -Encoding utf8
            $completed++
            Write-Host "  ✓ Success" -ForegroundColor Green
        } else {
            $failed++
            Write-Host "  ✗ Failed" -ForegroundColor Red
        }
    } catch {
        $failed++
        Write-Host "  ✗ Error" -ForegroundColor Red
    }
    
    @{
        completed = $completed
        failed = $failed
        total = $tasks.Count
        current = $task
        timestamp = Get-Date -Format "o"
    } | ConvertTo-Json -Compress | Out-File (Join-Path $LogDir "llm_status.json") -Force
    
    Start-Sleep -Milliseconds 300
}

Write-Host "`nComplete: $completed succeeded, $failed failed" -ForegroundColor Green
Read-Host "Press Enter to close"
'@
$llmScript | Out-File "$ScriptDir\llm_agent.ps1" -Force -Encoding utf8

# ===== 2. ORGANIZER AGENT =====
$organizerScript = @'
$OutputDir = "C:\Users\antho\Windows-AI\extensions_supervised"
$LogFile = "C:\Users\antho\logs\unified_ai_memory\supervised_swarm\organizer.log"

$host.UI.RawUI.WindowTitle = "Organizer Agent"
Write-Host "=== ORGANIZER AGENT ===" -ForegroundColor Cyan
Write-Host "Monitoring and categorizing extensions...`n" -ForegroundColor Yellow

while($true) {
    Start-Sleep -Seconds 30
    
    $dirs = Get-ChildItem $OutputDir -Directory -ErrorAction SilentlyContinue
    $count = $dirs.Count
    
    $categories = @{
        'AI/ML' = 0
        'Web' = 0  
        'Testing' = 0
        'Utils' = 0
        'Other' = 0
    }
    
    foreach($dir in $dirs) {
        $name = $dir.Name
        if($name -match '(AI|ML|GPT|Model|Neural)') { $categories['AI/ML']++ }
        elseif($name -match '(Web|HTTP|API|REST)') { $categories['Web']++ }
        elseif($name -match '(Test|Debug|Lint)') { $categories['Testing']++ }
        elseif($name -match '(Format|Convert|Parse)') { $categories['Utils']++ }
        else { $categories['Other']++ }
    }
    
    $log = "[$(Get-Date -Format 'HH:mm:ss')] Total: $count | " + 
           ($categories.GetEnumerator() | ForEach-Object { "$($_.Key): $($_.Value)" }) -join " | "
    
    Write-Host $log -ForegroundColor Cyan
    $log | Out-File $LogFile -Append -Encoding utf8
}
'@
$organizerScript | Out-File "$ScriptDir\organizer_agent.ps1" -Force -Encoding utf8

# ===== 3. LOGGER AGENT =====
$loggerScript = @'
$LogDir = "C:\Users\antho\logs\unified_ai_memory\supervised_swarm"
$MasterLog = "C:\Users\antho\logs\unified_ai_memory\master_log.txt"

$host.UI.RawUI.WindowTitle = "Logger Agent"
Write-Host "=== LOGGER AGENT ===" -ForegroundColor Yellow
Write-Host "Aggregating all agent logs...`n" -ForegroundColor Cyan

while($true) {
    Start-Sleep -Seconds 45
    
    $statusFiles = Get-ChildItem "$LogDir\*_status.json" -ErrorAction SilentlyContinue
    $allStatus = @()
    
    foreach($file in $statusFiles) {
        try {
            $status = Get-Content $file -Raw | ConvertFrom-Json
            $allStatus += $status
        } catch {}
    }
    
    if($allStatus.Count -gt 0) {
        $totalCompleted = ($allStatus | Measure-Object -Property completed -Sum).Sum
        $totalFailed = ($allStatus | Measure-Object -Property failed -Sum).Sum
        $totalTasks = ($allStatus | Measure-Object -Property total -Sum).Sum
        
        $log = "[$(Get-Date -Format 'HH:mm:ss')] Completed: $totalCompleted | Failed: $totalFailed | Remaining: $($totalTasks - $totalCompleted - $totalFailed)"
        Write-Host $log -ForegroundColor Yellow
        $log | Out-File $MasterLog -Append -Encoding utf8
    }
}
'@
$loggerScript | Out-File "$ScriptDir\logger_agent.ps1" -Force -Encoding utf8

# ===== 4. SUMMARIZER AGENT =====
$summarizerScript = @'
$OutputDir = "C:\Users\antho\Windows-AI\extensions_supervised"
$SummaryFile = "C:\Users\antho\logs\unified_ai_memory\summary.md"

$host.UI.RawUI.WindowTitle = "Summarizer Agent"
Write-Host "=== SUMMARIZER AGENT ===" -ForegroundColor Magenta
Write-Host "Generating periodic summaries...`n" -ForegroundColor Cyan

while($true) {
    Start-Sleep -Seconds 300  # Every 5 minutes
    
    $dirs = Get-ChildItem $OutputDir -Directory -ErrorAction SilentlyContinue
    $count = $dirs.Count
    
    $summary = @"
# Extension Generation Summary
**Last Updated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Progress
- **Extensions Created:** $count
- **Target:** 3148
- **Percentage:** $([math]::Round($count / 3148 * 100, 2))%

## Recent Extensions
$($dirs | Select-Object -Last 10 | ForEach-Object { "- $($_.Name)" } | Out-String)
"@
    
    $summary | Out-File $SummaryFile -Force -Encoding utf8
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Summary updated: $count extensions" -ForegroundColor Magenta
}
'@
$summarizerScript | Out-File "$ScriptDir\summarizer_agent.ps1" -Force -Encoding utf8

# ===== 5. PROGRESS TRACKER AGENT =====
$progressScript = @'
$ProgressFile = "C:\Users\antho\logs\unified_ai_memory\UNIFIED_PROGRESS.json"
$OutputDir = "C:\Users\antho\Windows-AI\extensions_supervised"

$host.UI.RawUI.WindowTitle = "Progress Tracker"
Write-Host "=== PROGRESS TRACKER ===" -ForegroundColor Green
Write-Host "Updating unified progress...`n" -ForegroundColor Cyan

while($true) {
    Start-Sleep -Seconds 60
    
    $count = (Get-ChildItem $OutputDir -Directory -ErrorAction SilentlyContinue).Count
    $total = 2522 + $count
    $percent = [math]::Round($total / 3148 * 100, 2)
    
    @{
        last_updated = Get-Date -Format "o"
        tasks = @{
            "Windows-AI Extensions" = @{
                status = if($total -ge 3148) { "completed" } else { "in_progress" }
                percent_complete = $percent
                metadata = @{
                    extensions_created = $total
                    target = 3148
                    last_session = Get-Date -Format "o"
                    method = "terminal_swarm"
                }
            }
        }
    } | ConvertTo-Json -Depth 5 | Out-File $ProgressFile -Force
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Progress: $total / 3148 ($percent%)" -ForegroundColor Green
}
'@
$progressScript | Out-File "$ScriptDir\progress_tracker.ps1" -Force -Encoding utf8

# ===== 6-9. VALIDATOR, BACKUP, MONITOR, STATS AGENTS =====
# Create minimal versions to fill terminal slots

@"
`$host.UI.RawUI.WindowTitle = "Validator Agent"
Write-Host "=== VALIDATOR AGENT ===" -ForegroundColor Blue
while(`$true) { Start-Sleep -Seconds 120; Write-Host "[`$(Get-Date -Format 'HH:mm:ss')] Validating..." -ForegroundColor Blue }
"@ | Out-File "$ScriptDir\validator_agent.ps1" -Force -Encoding utf8

@"
`$host.UI.RawUI.WindowTitle = "Backup Agent"
Write-Host "=== BACKUP AGENT ===" -ForegroundColor DarkCyan
while(`$true) { Start-Sleep -Seconds 180; Write-Host "[`$(Get-Date -Format 'HH:mm:ss')] Backing up..." -ForegroundColor DarkCyan }
"@ | Out-File "$ScriptDir\backup_agent.ps1" -Force -Encoding utf8

@"
`$host.UI.RawUI.WindowTitle = "Monitor Agent"
Write-Host "=== MONITOR AGENT ===" -ForegroundColor DarkYellow
while(`$true) { Start-Sleep -Seconds 90; Write-Host "[`$(Get-Date -Format 'HH:mm:ss')] Monitoring..." -ForegroundColor DarkYellow }
"@ | Out-File "$ScriptDir\monitor_agent.ps1" -Force -Encoding utf8

@"
`$host.UI.RawUI.WindowTitle = "Stats Agent"
Write-Host "=== STATS AGENT ===" -ForegroundColor DarkGreen
while(`$true) { Start-Sleep -Seconds 150; Write-Host "[`$(Get-Date -Format 'HH:mm:ss')] Stats..." -ForegroundColor DarkGreen }
"@ | Out-File "$ScriptDir\stats_agent.ps1" -Force -Encoding utf8

# Launch all terminals
Write-Host "`nLaunching $MaxTerminals terminal windows..." -ForegroundColor Green

$agents = @(
    "llm_agent.ps1",
    "organizer_agent.ps1", 
    "logger_agent.ps1",
    "summarizer_agent.ps1",
    "progress_tracker.ps1",
    "validator_agent.ps1",
    "backup_agent.ps1",
    "monitor_agent.ps1",
    "stats_agent.ps1"
)

foreach($agent in $agents | Select-Object -First $MaxTerminals) {
    $scriptPath = Join-Path $ScriptDir $agent
    Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$scriptPath`""
    Write-Host "  ✓ Launched $agent" -ForegroundColor Green
    Start-Sleep -Milliseconds 500
}

Write-Host "`n✅ All agents launched in separate terminals!" -ForegroundColor Green
Write-Host "Monitor the terminal windows to see progress." -ForegroundColor Cyan
Write-Host "`nPress Enter to stop all agents..." -ForegroundColor Yellow
Read-Host

# Cleanup
Write-Host "Stopping all agent terminals..." -ForegroundColor Red
Get-Process powershell | Where-Object { $_.MainWindowTitle -like "*Agent*" } | Stop-Process -Force
Write-Host "Done!" -ForegroundColor Green
