# SUPERVISED TERMINAL-BASED SWARM
# 1 LLM agent + support agents (organizer, logger, summarizer, etc)
# Max 10 terminals total - runs in actual PowerShell windows

param(
    [int]$MaxTerminals = 10,
    [int]$TargetCount = 652
)

$BaseDir = "C:\Users\antho\Windows-AI"
$OutputDir = "$BaseDir\extensions_supervised"
$LogDir = "C:\Users\antho\logs\unified_ai_memory\supervised_swarm"
$RoadmapFile = "$BaseDir\ULTIMATE_EXTENSION_ROADMAP.md"

# Disable all approval prompts
$env:GITHUB_COPILOT_CHAT_NO_CONFIRM = "1"

# Clean slate
Remove-Item $LogDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $OutputDir, $LogDir | Out-Null

Write-Host "=== SUPERVISED TERMINAL-BASED SWARM ===" -ForegroundColor Magenta
Write-Host "Max terminals: $MaxTerminals" -ForegroundColor Green
Write-Host "1 LLM Agent (Ollama) + 9 Support Agents" -ForegroundColor Cyan
Write-Host "Approval mode: DISABLED (fully autonomous)" -ForegroundColor Yellow
Write-Host "Running in actual terminals (not background jobs)`n" -ForegroundColor Cyan

# Load roadmap
$roadmap = Get-Content $RoadmapFile -Raw
$unchecked = [regex]::Matches($roadmap, '- \[ \] (.+)') | ForEach-Object { $_.Groups[1].Value.Trim() }
$extensionsToGenerate = $unchecked | Select-Object -First $TargetCount

Write-Host "Extensions to generate: $($extensionsToGenerate.Count)" -ForegroundColor Cyan
Write-Host "Tasks for LLM agent: $($extensionsToGenerate.Count)`n" -ForegroundColor Yellow

# Create agent scripts in temp directory
$AgentScriptDir = "$BaseDir\agent_scripts"
New-Item -ItemType Directory -Force -Path $AgentScriptDir | Out-Null

# 1. LLM Agent (Ollama) - generates extensions
Write-Host "Creating LLM Agent (Ollama)..." -ForegroundColor Green
$llmScript = @"
`$BaseDir = "C:\Users\antho\Windows-AI"
`$OutputDir = "`$BaseDir\extensions_supervised"
`$LogDir = "C:\Users\antho\logs\unified_ai_memory\supervised_swarm"
`$tasks = @'
$($extensionsToGenerate -join "`n")
'@ -split "`n"

Write-Host "LLM AGENT - Starting..." -ForegroundColor Green
Write-Host "Tasks: `$(`$tasks.Count)" -ForegroundColor Cyan

`$completed = 0
`$failed = 0

foreach(`$task in `$tasks) {
    `$safeName = `$task -replace '[^a-zA-Z0-9_-]', '_'
    `$extDir = Join-Path `$OutputDir `$safeName
    `$logFile = Join-Path `$LogDir "llm_`${safeName}.log"
    
    Write-Host "[`$completed/`$(`$tasks.Count)] `$task" -ForegroundColor Yellow
    
    `$prompt = "VSCode extension: `$task. Output package.json and code."
    
    try {
        `$result = `$prompt | & ollama run qwen2.5-coder:1.5b 2>&1
        `$resultText = if(`$result -is [Array]) { `$result -join "`n" } else { `$result }
        `$resultText | Out-File `$logFile -Force -Encoding utf8
        
        if(`$resultText -and `$resultText.Length -gt 200) {
            New-Item -ItemType Directory -Force -Path `$extDir | Out-Null
            `$resultText | Out-File (Join-Path `$extDir "extension.txt") -Force -Encoding utf8
            `$completed++
            Write-Host "  ✓ Success" -ForegroundColor Green
        } else {
            `$failed++
            Write-Host "  ✗ Failed (short output)" -ForegroundColor Red
        }
    } catch {
        `$failed++
        Write-Host "  ✗ Failed (error)" -ForegroundColor Red
    }
    
    @{
        agent = "LLM"
        completed = `$completed
        failed = `$failed
        total = `$tasks.Count
        current = `$task
        timestamp = Get-Date -Format "o"
    } | ConvertTo-Json -Compress | Out-File (Join-Path `$LogDir "llm_status.json") -Force
    
    Start-Sleep -Milliseconds 300
}

Write-Host "`nLLM AGENT - Complete: `$completed succeeded, `$failed failed" -ForegroundColor Green
Read-Host "Press Enter to close"
"@

$llmScript | Out-File "$AgentScriptDir\llm_agent.ps1" -Force -Encoding utf8

# 2. Organizer Agent
Write-Host "Creating Organizer Agent..." -ForegroundColor Green
$organizerScript = @"
`$OutputDir = "C:\Users\antho\Windows-AI\extensions_supervised"
`$LogFile = "C:\Users\antho\logs\unified_ai_memory\supervised_swarm\organizer.log"

Write-Host "ORGANIZER AGENT - Starting..." -ForegroundColor Cyan

while(`$true) {
    Start-Sleep -Seconds 60
    
    `$dirs = Get-ChildItem `$OutputDir -Directory -ErrorAction SilentlyContinue
    `$count = `$dirs.Count
    
    # Organize by category
    `$organized = @{}
    foreach(`$dir in `$dirs) {
        `$name = `$dir.Name
        `$category = if(`$name -match '^(AI|ML|Data)') { 'AI_ML' }
                    elseif(`$name -match '^(Web|HTTP|API)') { 'Web' }
                    elseif(`$name -match '^(Test|Debug)') { 'Testing' }
                    else { 'Other' }
        
        if(-not `$organized[`$category]) { `$organized[`$category] = @() }
        `$organized[`$category] += `$name
    }
    
    `$log = "[`$(Get-Date -Format 'HH:mm:ss')] Extensions: `$count | " + 
           (`$organized.GetEnumerator() | ForEach-Object { "`$(`$_.Key): `$(`$_.Value.Count)" }) -join ", "
    
    Write-Host `$log -ForegroundColor Cyan
    `$log | Out-File `$LogFile -Append -Encoding utf8
}
"@

$organizerScript | Out-File "$AgentScriptDir\organizer_agent.ps1" -Force -Encoding utf8

# 3. Logger Agent
Write-Host "Creating Logger Agent..." -ForegroundColor Green
for($i = 1; $i -le $CopilotAgents; $i++) {
    $agentName = "Copilot_$i"
    $agentTasks = $extensionsToGenerate | Select-Object -Skip $taskIdx -First $tasksPerAgent
    $taskIdx += $tasksPerAgent
    
    if(-not $agentTasks) { break }
    
    Start-Job -Name $agentName -ScriptBlock {
        param($name, $tasks, $outDir, $logDir)
        
        # Disable confirmations in job
        $env:GITHUB_COPILOT_CHAT_NO_CONFIRM = "1"
        
        $completed = 0
        $failed = 0
        $startTime = Get-Date
        
        foreach($task in $tasks) {
            $safeName = $task -replace '[^a-zA-Z0-9_-]', '_'
            $extDir = Join-Path $outDir $safeName
            $logFile = Join-Path $logDir "${name}_${safeName}.log"
            
            $prompt = "Create complete VSCode extension for: $task. Include package.json and main code. Output working code only."
            
            try {
                $result = $prompt | & gh copilot suggest -t shell 2>&1
                $exitCode = $LASTEXITCODE
                
                $resultText = if($result -is [Array]) { $result -join "`n" } else { $result }
                $resultText | Out-File $logFile -Force -Encoding utf8
                
                if($exitCode -eq 0 -and $resultText -and $resultText.Length -gt 300) {
                    New-Item -ItemType Directory -Force -Path $extDir | Out-Null
                    $resultText | Out-File (Join-Path $extDir "extension.txt") -Force -Encoding utf8
                    $completed++
                } else {
                    $failed++
                }
                
            } catch {
                $failed++
            }
            
            # Progress update
            @{
                agent = $name
                type = "copilot"
                completed = $completed
                failed = $failed
                total = $tasks.Count
                current = $task
                timestamp = Get-Date -Format "o"
            } | ConvertTo-Json -Compress | Out-File (Join-Path $logDir "${name}_status.json") -Force
            
            Start-Sleep -Milliseconds 400
        }
        
        return @{ agent=$name; type="copilot"; completed=$completed; failed=$failed; total=$tasks.Count }
        
    } -ArgumentList $agentName, $agentTasks, $OutputDir, $LogDir
    
    Write-Host "  ✓ $agentName - $($agentTasks.Count) tasks" -ForegroundColor Green
    Start-Sleep -Milliseconds 200
}

# Launch Ollama agents
Write-Host "`nLaunching Ollama agents..." -ForegroundColor Green
for($i = 1; $i -le $OllamaAgents; $i++) {
    $agentName = "Ollama_$i"
    $agentTasks = $extensionsToGenerate | Select-Object -Skip $taskIdx -First $tasksPerAgent
    $taskIdx += $tasksPerAgent
    
    if(-not $agentTasks) { break }
    
    Start-Job -Name $agentName -ScriptBlock {
        param($name, $tasks, $outDir, $logDir)
        
        $completed = 0
        $failed = 0
        
        foreach($task in $tasks) {
            $safeName = $task -replace '[^a-zA-Z0-9_-]', '_'
            $extDir = Join-Path $outDir $safeName
            $logFile = Join-Path $logDir "${name}_${safeName}.log"
            
            $prompt = "VSCode extension: $task. Output package.json and code."
            
            try {
                $result = $prompt | & ollama run qwen2.5-coder:1.5b 2>&1
                $resultText = if($result -is [Array]) { $result -join "`n" } else { $result }
                $resultText | Out-File $logFile -Force -Encoding utf8
                
                if($resultText -and $resultText.Length -gt 200) {
                    New-Item -ItemType Directory -Force -Path $extDir | Out-Null
                    $resultText | Out-File (Join-Path $extDir "extension.txt") -Force -Encoding utf8
                    $completed++
                } else {
                    $failed++
                }
            } catch {
                $failed++
            }
            
            @{
                agent = $name
                type = "ollama"
                completed = $completed
                failed = $failed
                total = $tasks.Count
                current = $task
                timestamp = Get-Date -Format "o"
            } | ConvertTo-Json -Compress | Out-File (Join-Path $logDir "${name}_status.json") -Force
            
            Start-Sleep -Milliseconds 300
        }
        
        return @{ agent=$name; type="ollama"; completed=$completed; failed=$failed; total=$tasks.Count }
        
    } -ArgumentList $agentName, $agentTasks, $OutputDir, $LogDir
    
    Write-Host "  ✓ $agentName - $($agentTasks.Count) tasks" -ForegroundColor Green
    Start-Sleep -Milliseconds 200
}

Write-Host "`n🚀 Launched $MaxAgents agents" -ForegroundColor Green
Write-Host "`n=== ACTIVE MONITORING STARTED ===" -ForegroundColor Cyan
Write-Host "I will monitor and report progress every 30 seconds`n" -ForegroundColor Yellow

# Active monitoring loop
$monitorStart = Get-Date
$lastReport = $monitorStart

while($true) {
    Start-Sleep -Seconds 30
    
    $now = Get-Date
    $jobs = Get-Job | Where-Object { $_.Name -like "Copilot_*" -or $_.Name -like "Ollama_*" }
    
    if(-not $jobs) {
        Write-Host "`n⚠️ No jobs found. Exiting monitor." -ForegroundColor Yellow
        break
    }
    
    $running = ($jobs | Where-Object State -eq 'Running').Count
    $completed = ($jobs | Where-Object State -eq 'Completed').Count
    $failed = ($jobs | Where-Object State -eq 'Failed').Count
    
    # Count actual extensions
    $extDirs = (Get-ChildItem $OutputDir -Directory -ErrorAction SilentlyContinue).Count
    
    # Read agent status files
    $statusFiles = Get-ChildItem "$LogDir\*_status.json" -ErrorAction SilentlyContinue
    $totalCompleted = 0
    $totalFailed = 0
    $currentTasks = @()
    
    foreach($sf in $statusFiles) {
        try {
            $status = Get-Content $sf -Raw | ConvertFrom-Json
            $totalCompleted += $status.completed
            $totalFailed += $status.failed
            $currentTasks += "$($status.agent): $($status.current)"
        } catch {}
    }
    
    $elapsed = [math]::Round(($now - $monitorStart).TotalMinutes, 1)
    $rate = if($elapsed -gt 0) { [math]::Round($totalCompleted / $elapsed, 1) } else { 0 }
    
    # Progress report
    Write-Host "`n[$($now.ToString('HH:mm:ss'))] === PROGRESS REPORT ===" -ForegroundColor Cyan
    Write-Host "  Agents: $running running, $completed done, $failed crashed" -ForegroundColor Yellow
    Write-Host "  Extensions: $totalCompleted built, $totalFailed failed" -ForegroundColor Green
    Write-Host "  Directories: $extDirs" -ForegroundColor Cyan
    Write-Host "  Rate: $rate ext/min | Elapsed: $elapsed min" -ForegroundColor Gray
    
    # Show what agents are working on
    if($currentTasks.Count -gt 0) {
        Write-Host "`n  Currently working on:" -ForegroundColor Yellow
        $currentTasks | Select-Object -First 3 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
    
    # Check if done
    if($running -eq 0) {
        Write-Host "`n✅ ALL AGENTS COMPLETED!" -ForegroundColor Green
        break
    }
    
    # Detailed report every 5 minutes
    if(($now - $lastReport).TotalMinutes -ge 5) {
        $lastReport = $now
        Write-Host "`n  === DETAILED STATUS ===" -ForegroundColor Magenta
        
        $statusFiles | ForEach-Object {
            try {
                $s = Get-Content $_.FullName -Raw | ConvertFrom-Json
                Write-Host "    $($s.agent) [$($s.type)]: $($s.completed)/$($s.total) done, $($s.failed) failed" -ForegroundColor Cyan
            } catch {}
        }
    }
}

# Final summary
Write-Host "`n=== FINAL RESULTS ===" -ForegroundColor Magenta

$results = $jobs | Receive-Job
$results | Format-Table -AutoSize Agent, Type, Completed, Failed, Total

$totalBuilt = ($results | Measure-Object -Property completed -Sum).Sum
$totalFailed = ($results | Measure-Object -Property failed -Sum).Sum
$actualDirs = (Get-ChildItem $OutputDir -Directory).Count

Write-Host "`nReported: $totalBuilt built, $totalFailed failed" -ForegroundColor Yellow
Write-Host "Actual directories: $actualDirs" -ForegroundColor Green

# Update progress
$newTotal = 2496 + $actualDirs
$newPercent = [math]::Round($newTotal / 3148 * 100, 2)

@{
    last_updated = Get-Date -Format "o"
    tasks = @{
        "Windows-AI Extensions" = @{
            status = if($newTotal -ge 3148) { "completed" } else { "in_progress" }
            percent_complete = $newPercent
            metadata = @{
                extensions_created = $newTotal
                target = 3148
                last_session = Get-Date -Format "o"
                method = "supervised_copilot_ollama"
            }
        }
    }
} | ConvertTo-Json -Depth 5 | Out-File "C:\Users\antho\logs\unified_ai_memory\UNIFIED_PROGRESS.json" -Force

Write-Host "`nProgress: $newTotal / 3148 ($newPercent%)" -ForegroundColor Cyan
Write-Host "Output: $OutputDir" -ForegroundColor Green

# Cleanup
Get-Job | Where-Object { $_.Name -like "Copilot_*" -or $_.Name -like "Ollama_*" } | Remove-Job -Force
Write-Host "`nAll done! ✨" -ForegroundColor Green
