# COPILOT-ONLY AGENT SWARM WITH OLLAMA HELPER
# Uses ONLY gh copilot CLI + 1 small Ollama model

param(
    [int]$CopilotAgents = 15,
    [int]$OllamaAgents = 5,
    [int]$TargetCount = 652,
    [string]$OllamaModel = "qwen2.5-coder:1.5b"
)

$BaseDir = "C:\Users\antho\Windows-AI"
$OutputDir = "$BaseDir\extensions_copilot_swarm"
$LogDir = "C:\Users\antho\logs\unified_ai_memory\copilot_swarm"
$RoadmapFile = "$BaseDir\ULTIMATE_EXTENSION_ROADMAP.md"

# Clean slate
Remove-Item $LogDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $OutputDir, $LogDir | Out-Null

Write-Host "=== COPILOT + OLLAMA SWARM ===" -ForegroundColor Magenta
Write-Host "Copilot agents: $CopilotAgents" -ForegroundColor Green
Write-Host "Ollama agents: $OllamaAgents (using $OllamaModel)" -ForegroundColor Green
Write-Host "Target: $TargetCount extensions`n" -ForegroundColor Cyan

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

# Calculate distribution
$totalAgents = $CopilotAgents + $OllamaAgents
$tasksPerAgent = [math]::Ceiling($extensionsToGenerate.Count / $totalAgents)

Write-Host "Each agent will handle ~$tasksPerAgent extensions`n" -ForegroundColor Cyan
Write-Host "Launching Copilot agents..." -ForegroundColor Yellow

$taskIdx = 0
$agentId = 1

# Launch Copilot agents
for($i = 1; $i -le $CopilotAgents; $i++) {
    $agentName = "Copilot_Agent_$i"
    $agentTasks = $extensionsToGenerate | Select-Object -Skip $taskIdx -First $tasksPerAgent
    $taskIdx += $tasksPerAgent
    
    if(-not $agentTasks -or $agentTasks.Count -eq 0) { break }
    
    Start-Job -Name $agentName -ScriptBlock {
        param($name, $tasks, $outDir, $logDir)
        
        $completed = 0
        $failed = 0
        $startTime = Get-Date
        
        foreach($task in $tasks) {
            $safeName = $task -replace '[^a-zA-Z0-9_-]', '_'
            $extDir = Join-Path $outDir $safeName
            $logFile = Join-Path $logDir "${name}_${safeName}.log"
            
            $prompt = @"
Create a complete VSCode extension for: $task

Requirements:
1. Full package.json with metadata, commands, activation events
2. TypeScript/JavaScript implementation with activate() and deactivate()
3. All necessary dependencies
4. README with usage instructions

Output the complete extension code. Be thorough and functional.
"@

            try {
                # Use gh copilot - most reliable CLI
                $result = $prompt | & gh copilot suggest -t shell 2>&1
                $exitCode = $LASTEXITCODE
                
                # Handle array output
                $resultText = if($result -is [Array]) { $result -join "`n" } else { $result }
                
                # Save log
                $resultText | Out-File $logFile -Force -Encoding utf8
                
                # Validate and save
                if($exitCode -eq 0 -and $resultText -and $resultText.Length -gt 300) {
                    New-Item -ItemType Directory -Force -Path $extDir | Out-Null
                    $resultText | Out-File (Join-Path $extDir "extension_code.txt") -Force -Encoding utf8
                    
                    # Extract package.json if present
                    if($resultText -match '(?s)\{[^{]*"name"\s*:') {
                        $pkgMatch = [regex]::Match($resultText, '(?s)\{[^{]*"name"[^}]+\}')
                        if($pkgMatch.Success) {
                            $pkgMatch.Value | Out-File (Join-Path $extDir "package.json") -Force -Encoding utf8
                        }
                    }
                    
                    $completed++
                } else {
                    $failed++
                    "FAILED: Exit=$exitCode, Length=$($resultText.Length)" | Out-File $logFile -Append
                }
                
            } catch {
                $failed++
                "EXCEPTION: $($_.Exception.Message)" | Out-File $logFile -Force
            }
            
            # Progress tracking
            $elapsed = ((Get-Date) - $startTime).TotalMinutes
            $rate = if($elapsed -gt 0) { $completed / $elapsed } else { 0 }
            
            @{
                agent = $name
                type = "copilot"
                completed = $completed
                failed = $failed
                total = $tasks.Count
                rate = [math]::Round($rate, 2)
                current = $task
                timestamp = Get-Date -Format "o"
            } | ConvertTo-Json -Compress | Out-File (Join-Path $logDir "${name}_progress.json") -Force
            
            Start-Sleep -Milliseconds 300
        }
        
        return @{
            agent = $name
            type = "copilot"
            total = $tasks.Count
            completed = $completed
            failed = $failed
            rate = [math]::Round(($completed / ((Get-Date) - $startTime).TotalMinutes), 2)
        }
        
    } -ArgumentList $agentName, $agentTasks, $OutputDir, $LogDir
    
    Write-Host "  ✓ $agentName - $($agentTasks.Count) tasks" -ForegroundColor Green
    Start-Sleep -Milliseconds 150
}

# Launch Ollama agents
Write-Host "`nLaunching Ollama agents..." -ForegroundColor Yellow

for($i = 1; $i -le $OllamaAgents; $i++) {
    $agentName = "Ollama_Agent_$i"
    $agentTasks = $extensionsToGenerate | Select-Object -Skip $taskIdx -First $tasksPerAgent
    $taskIdx += $tasksPerAgent
    
    if(-not $agentTasks -or $agentTasks.Count -eq 0) { break }
    
    Start-Job -Name $agentName -ScriptBlock {
        param($name, $tasks, $model, $outDir, $logDir)
        
        $completed = 0
        $failed = 0
        $startTime = Get-Date
        
        foreach($task in $tasks) {
            $safeName = $task -replace '[^a-zA-Z0-9_-]', '_'
            $extDir = Join-Path $outDir $safeName
            $logFile = Join-Path $logDir "${name}_${safeName}.log"
            
            $prompt = @"
Create VSCode extension: $task
Output package.json and main code. Be concise but complete.
"@

            try {
                # Use Ollama
                $result = $prompt | & ollama run $model 2>&1
                $exitCode = $LASTEXITCODE
                
                $resultText = if($result -is [Array]) { $result -join "`n" } else { $result }
                
                $resultText | Out-File $logFile -Force -Encoding utf8
                
                if($exitCode -eq 0 -and $resultText -and $resultText.Length -gt 200) {
                    New-Item -ItemType Directory -Force -Path $extDir | Out-Null
                    $resultText | Out-File (Join-Path $extDir "extension_code.txt") -Force -Encoding utf8
                    $completed++
                } else {
                    $failed++
                    "FAILED: Exit=$exitCode, Length=$($resultText.Length)" | Out-File $logFile -Append
                }
                
            } catch {
                $failed++
                "EXCEPTION: $($_.Exception.Message)" | Out-File $logFile -Force
            }
            
            # Progress
            @{
                agent = $name
                type = "ollama"
                completed = $completed
                failed = $failed
                total = $tasks.Count
                current = $task
                timestamp = Get-Date -Format "o"
            } | ConvertTo-Json -Compress | Out-File (Join-Path $logDir "${name}_progress.json") -Force
            
            Start-Sleep -Milliseconds 200
        }
        
        return @{
            agent = $name
            type = "ollama"
            total = $tasks.Count
            completed = $completed
            failed = $failed
        }
        
    } -ArgumentList $agentName, $agentTasks, $OllamaModel, $OutputDir, $LogDir
    
    Write-Host "  ✓ $agentName - $($agentTasks.Count) tasks" -ForegroundColor Green
    Start-Sleep -Milliseconds 150
}

$totalLaunched = $CopilotAgents + $OllamaAgents
Write-Host "`n🚀 Launched $totalLaunched agents" -ForegroundColor Green
Write-Host "`nMonitoring... (Ctrl+C to exit, agents continue)`n" -ForegroundColor Yellow

# Monitor loop
$startTime = Get-Date

while($true) {
    Start-Sleep -Seconds 10
    
    $jobs = Get-Job | Where-Object { $_.Name -like "*_Agent_*" }
    
    if(-not $jobs) { break }
    
    $running = ($jobs | Where-Object State -eq 'Running').Count
    $completed = ($jobs | Where-Object State -eq 'Completed').Count
    $failed = ($jobs | Where-Object State -eq 'Failed').Count
    
    # Count actual extensions created
    $extDirs = (Get-ChildItem $OutputDir -Directory -ErrorAction SilentlyContinue).Count
    
    # Aggregate progress from JSON files
    $progressFiles = Get-ChildItem "$LogDir\*_progress.json" -ErrorAction SilentlyContinue
    $totalCompleted = 0
    $totalFailed = 0
    
    if($progressFiles) {
        foreach($pf in $progressFiles) {
            try {
                $p = Get-Content $pf -Raw | ConvertFrom-Json
                $totalCompleted += $p.completed
                $totalFailed += $p.failed
            } catch {}
        }
    }
    
    $elapsed = ((Get-Date) - $startTime).TotalMinutes
    $timestamp = (Get-Date).ToString("HH:mm:ss")
    
    Write-Host "[$timestamp] Agents: $running running, $completed done | Built: $totalCompleted | Failed: $totalFailed | Dirs: $extDirs | Time: $([math]::Round($elapsed, 1))min" -ForegroundColor Cyan
    
    if($running -eq 0) {
        Write-Host "`n✓ All agents finished!" -ForegroundColor Green
        break
    }
}

# Final summary
Write-Host "`n=== RESULTS ===" -ForegroundColor Magenta

$results = $jobs | Receive-Job
$results | Format-Table -AutoSize Agent, Type, Completed, Failed, Rate

$grandTotal = ($results | Measure-Object -Property completed -Sum).Sum
$grandFailed = ($results | Measure-Object -Property failed -Sum).Sum
$actualExtensions = (Get-ChildItem $OutputDir -Directory).Count

Write-Host "`nReported built: $grandTotal" -ForegroundColor Green
Write-Host "Reported failed: $grandFailed" -ForegroundColor Red
Write-Host "Actual extension dirs: $actualExtensions" -ForegroundColor Cyan
Write-Host "Success rate: $([math]::Round($grandTotal / ($grandTotal + $grandFailed) * 100, 1))%" -ForegroundColor Yellow

# Update progress
$newTotal = 2496 + $actualExtensions
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
                method = "copilot_ollama_swarm"
            }
        }
    }
} | ConvertTo-Json -Depth 5 | Out-File "C:\Users\antho\logs\unified_ai_memory\UNIFIED_PROGRESS.json" -Force

Write-Host "`nProgress: $newTotal / 3148 ($newPercent%)" -ForegroundColor Green
Write-Host "Output: $OutputDir" -ForegroundColor Cyan

# Cleanup
Get-Job | Where-Object { $_.Name -like "*_Agent_*" } | Remove-Job -Force
Write-Host "`nDone!" -ForegroundColor Green
