# PRODUCTION PARALLEL ORCHESTRATOR - WORKING CLIs ONLY
# Uses: Copilot, Claude, Codex, OpenCode (Gemini excluded - broken)

param(
    [int]$MaxAgents = 20,
    [int]$TargetCount = 652,
    [string]$LogDir = "C:\Users\antho\logs\unified_ai_memory"
)

$BaseDir = "C:\Users\antho\Windows-AI"
$OutputDir = "$BaseDir\extensions_parallel"
$AgentLogDir = "$LogDir\agents_parallel"
$RoadmapFile = "$BaseDir\ULTIMATE_EXTENSION_ROADMAP.md"

# Clean slate
Remove-Item $AgentLogDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $OutputDir, $AgentLogDir | Out-Null

Write-Host "=== PRODUCTION PARALLEL EXTENSION BUILDER ===" -ForegroundColor Magenta
Write-Host "Target: $TargetCount extensions across $MaxAgents agents" -ForegroundColor Cyan
Write-Host "Using: Copilot, Claude, Codex, OpenCode (Gemini excluded)" -ForegroundColor Yellow

# Load roadmap
if(-not (Test-Path $RoadmapFile)) {
    Write-Error "Roadmap not found: $RoadmapFile"
    exit 1
}

$roadmap = Get-Content $RoadmapFile -Raw
$unchecked = [regex]::Matches($roadmap, '- \[ \] (.+)') | ForEach-Object { $_.Groups[1].Value.Trim() }

if($unchecked.Count -eq 0) {
    Write-Host "✓ All extensions completed!" -ForegroundColor Green
    exit 0
}

$extensionsToGenerate = $unchecked | Select-Object -First $TargetCount
Write-Host "Found $($extensionsToGenerate.Count) extensions to generate`n" -ForegroundColor Yellow

# Agent distribution (NO GEMINI)
$agentsPerCLI = @{
    'copilot' = [math]::Ceiling($MaxAgents * 0.30)  # 6 agents
    'claude'  = [math]::Ceiling($MaxAgents * 0.30)  # 6 agents
    'codex'   = [math]::Ceiling($MaxAgents * 0.25)  # 5 agents
    'opencode' = [math]::Ceiling($MaxAgents * 0.15) # 3 agents
}

$taskIdx = 0
$agentId = 1
$tasksPerAgent = [math]::Ceiling($extensionsToGenerate.Count / $MaxAgents)

Write-Host "Launching agents..`n" -ForegroundColor Cyan

foreach($cli in $agentsPerCLI.Keys) {
    $count = $agentsPerCLI[$cli]
    
    for($i = 1; $i -le $count; $i++) {
        $agentName = "Agent_${agentId}_${cli}"
        
        # Assign tasks
        $agentTasks = $extensionsToGenerate | Select-Object -Skip $taskIdx -First $tasksPerAgent
        $taskIdx += $tasksPerAgent
        
        if(-not $agentTasks -or $agentTasks.Count -eq 0) {
            break
        }
        
        # Launch job with working CLI
        Start-Job -Name $agentName -ScriptBlock {
            param($name, $cli, $tasks, $outDir, $logDir)
            
            $completed = 0
            $failed = 0
            $startTime = Get-Date
            
            foreach($task in $tasks) {
                $safeName = $task -replace '[^a-zA-Z0-9_-]', '_'
                $extDir = Join-Path $outDir $safeName
                $logFile = Join-Path $logDir "${name}_${safeName}.log"
                
                $prompt = @"
Create a VSCode extension for: $task

Output a complete, working extension with:
1. package.json with all metadata
2. Main extension.ts/js with activate() and deactivate()
3. All required dependencies
4. README.md

Be thorough. Output code only, no explanations.
"@

                try {
                    $result = $null
                    $exitCode = 1
                    
                    # Execute with tested, working syntax
                    switch($cli) {
                        'copilot' {
                            $result = $prompt | & gh copilot suggest -t shell 2>&1
                            $exitCode = $LASTEXITCODE
                        }
                        'claude' {
                            $result = $prompt | & claude 2>&1
                            $exitCode = $LASTEXITCODE
                        }
                        'codex' {
                            $result = $prompt | & codex 2>&1
                            $exitCode = $LASTEXITCODE
                        }
                        'opencode' {
                            $result = & opencode run -m grok-2-1212 -p $prompt 2>&1
                            $exitCode = $LASTEXITCODE
                        }
                    }
                    
                    # Save log
                    $result | Out-File $logFile -Force -Encoding utf8
                    
                    # Validate output (handle arrays from CLI output)
                    $resultText = if($result -is [Array]) { $result -join "`n" } else { $result }
                    $contentLength = if($resultText) { $resultText.Length } else { 0 }
                    
                    if($exitCode -eq 0 -and $contentLength -gt 200) {
                        New-Item -ItemType Directory -Force -Path $extDir | Out-Null
                        $resultText | Out-File (Join-Path $extDir "generated_code.txt") -Force -Encoding utf8
                        
                        # Try to extract package.json if present
                        $pkgMatch = [regex]::Match($resultText, '(?s)\{[^{]*"name"\s*:\s*"[^"]+".+?\}')
                        if($pkgMatch.Success) {
                            $pkgMatch.Value | Out-File (Join-Path $extDir "package.json") -Force -Encoding utf8
                        }
                        
                        $completed++
                    } else {
                        $failed++
                        "ERROR: Exit=$exitCode, Length=$contentLength" | Out-File $logFile -Append
                    }
                    
                } catch {
                    $failed++
                    "EXCEPTION: $($_.Exception.Message)" | Out-File $logFile -Force
                }
                
                # Progress update
                $elapsed = ((Get-Date) - $startTime).TotalSeconds
                $rate = if($elapsed -gt 0) { ($completed + $failed) / $elapsed * 60 } else { 0 }
                
                @{
                    agent = $name
                    cli = $cli
                    completed = $completed
                    failed = $failed
                    total = $tasks.Count
                    current_task = $task
                    rate_per_min = [math]::Round($rate, 2)
                    timestamp = Get-Date -Format "o"
                } | ConvertTo-Json -Compress | Out-File (Join-Path $logDir "${name}_progress.json") -Force
                
                Start-Sleep -Milliseconds 500  # Rate limit
            }
            
            return @{
                agent = $name
                cli = $cli
                total = $tasks.Count
                completed = $completed
                failed = $failed
                rate = [math]::Round((($completed + $failed) / ((Get-Date) - $startTime).TotalMinutes), 2)
            }
            
        } -ArgumentList $agentName, $cli, $agentTasks, $OutputDir, $AgentLogDir
        
        $agentId++
        Write-Host "  ✓ [$cli] $agentName - $($agentTasks.Count) tasks" -ForegroundColor Green
        Start-Sleep -Milliseconds 200
    }
}

$totalLaunched = $agentId - 1
Write-Host "`n🚀 Launched $totalLaunched agents" -ForegroundColor Green
Write-Host "`nMonitoring (press Ctrl+C to exit monitor, agents continue)...`n" -ForegroundColor Yellow

# Monitoring loop
$startTime = Get-Date
$lastUpdate = $startTime

while($true) {
    Start-Sleep -Seconds 15
    
    $now = Get-Date
    $jobs = Get-Job | Where-Object { $_.Name -like "Agent_*" }
    
    if(-not $jobs) {
        Write-Host "No jobs found. Exiting monitor." -ForegroundColor Red
        break
    }
    
    $running = ($jobs | Where-Object State -eq 'Running').Count
    $completed = ($jobs | Where-Object State -eq 'Completed').Count
    $failed = ($jobs | Where-Object State -eq 'Failed').Count
    
    # Aggregate progress
    $progressFiles = Get-ChildItem "$AgentLogDir\*_progress.json" -ErrorAction SilentlyContinue
    $totalCompleted = 0
    $totalFailed = 0
    $avgRate = 0
    
    if($progressFiles) {
        foreach($pf in $progressFiles) {
            try {
                $p = Get-Content $pf -Raw | ConvertFrom-Json
                $totalCompleted += $p.completed
                $totalFailed += $p.failed
                $avgRate += $p.rate_per_min
            } catch {}
        }
        $avgRate = if($progressFiles.Count -gt 0) { [math]::Round($avgRate / $progressFiles.Count, 1) } else { 0 }
    }
    
    $elapsed = ($now - $startTime).TotalMinutes
    $timestamp = $now.ToString("HH:mm:ss")
    
    Write-Host "[$timestamp] Jobs: $running running, $completed done, $failed crashed | Extensions: $totalCompleted built, $totalFailed failed | Avg: $avgRate/min | Elapsed: $([math]::Round($elapsed, 1))min" -ForegroundColor Cyan
    
    # Check if done
    if($running -eq 0) {
        Write-Host "`n✓ All agents finished!" -ForegroundColor Green
        break
    }
    
    # Every 5 minutes, show top performers
    if(($now - $lastUpdate).TotalMinutes -ge 5) {
        $lastUpdate = $now
        Write-Host "`n--- Top Performers ---" -ForegroundColor Yellow
        $progressFiles | ForEach-Object {
            $p = Get-Content $_.FullName -Raw | ConvertFrom-Json
            [PSCustomObject]@{
                Agent = $p.agent
                CLI = $p.cli
                Done = $p.completed
                Failed = $p.failed
                Rate = "$($p.rate_per_min)/min"
            }
        } | Sort-Object Done -Descending | Select-Object -First 5 | Format-Table -AutoSize
    }
}

# Final summary
Write-Host "`n=== FINAL RESULTS ===" -ForegroundColor Magenta

$results = $jobs | Receive-Job
$results | Format-Table -AutoSize Agent, CLI, Completed, Failed, Rate

$grandTotal = ($results | Measure-Object -Property completed -Sum).Sum
$grandFailed = ($results | Measure-Object -Property failed -Sum).Sum

Write-Host "`nTotal Built: $grandTotal" -ForegroundColor Green
Write-Host "Total Failed: $grandFailed" -ForegroundColor Red
Write-Host "Success Rate: $([math]::Round($grandTotal / ($grandTotal + $grandFailed) * 100, 1))%" -ForegroundColor Cyan
Write-Host "Output: $OutputDir" -ForegroundColor Cyan

# Update progress tracker
$newTotal = 2496 + $grandTotal
$newPercent = [math]::Round(($newTotal / 3148) * 100, 2)

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
                method = "parallel_orchestrator_v2"
            }
        }
    }
} | ConvertTo-Json -Depth 5 | Out-File "$LogDir\UNIFIED_PROGRESS.json" -Force

Write-Host "`nProgress: $newTotal / 3148 ($newPercent%)" -ForegroundColor Green

# Cleanup jobs
Get-Job | Where-Object { $_.Name -like "Agent_*" } | Remove-Job -Force
Write-Host "`nJobs cleaned up. Done!" -ForegroundColor Green
