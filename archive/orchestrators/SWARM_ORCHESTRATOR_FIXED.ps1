# FIXED SWARM ORCHESTRATOR - PROPER CLI SYNTAX
param(
    [int]$MaxAgents = 20,
    [switch]$TestMode,
    [string]$LogDir = "C:\Users\antho\logs\unified_ai_memory"
)

$BaseDir = "C:\Users\antho\Windows-AI"
$OutputDir = "$BaseDir\extensions_output"
$AgentLogDir = "$LogDir\agents"
New-Item -ItemType Directory -Force -Path $OutputDir, $AgentLogDir | Out-Null

Write-Host "=== WINDOWS-AI EXTENSION BUILDER ===" -ForegroundColor Magenta
Write-Host "Resuming at 79% (2496/3148 complete, 652 remaining)" -ForegroundColor Cyan

# Load roadmap
$roadmapPath = "$BaseDir\ULTIMATE_EXTENSION_ROADMAP.md"
if(-not (Test-Path $roadmapPath)) {
    Write-Error "Roadmap not found at $roadmapPath"
    exit 1
}

$roadmap = Get-Content $roadmapPath -Raw
$unchecked = [regex]::Matches($roadmap, '- \[ \] (.+)') | ForEach-Object { $_.Groups[1].Value.Trim() }
$totalTasks = $unchecked.Count

Write-Host "Found $totalTasks uncompleted extensions" -ForegroundColor Yellow

# CLI Command Templates (FIXED)
$CLICommands = @{
    'opencode' = @{
        model = 'grok-2-1212'
        command = { param($prompt, $output)
            # OpenCode with proper syntax
            $tempFile = New-TemporaryFile
            $prompt | Out-File $tempFile -Encoding utf8
            & opencode --model grok-2-1212 --input $tempFile.FullName 2>&1 | Tee-Object $output
            Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        }
    }
    'gemini' = @{
        model = 'gemini-2.0-flash-exp'
        command = { param($prompt, $output)
            # Gemini - use stdin, not chat subcommand
            $prompt | & gemini -m gemini-2.0-flash-exp 2>&1 | Tee-Object $output
        }
    }
    'codex' = @{
        model = 'gpt-4'
        command = { param($prompt, $output)
            # Codex - properly formatted prompt via stdin
            $prompt | & codex -m gpt-4 2>&1 | Tee-Object $output
        }
    }
    'claude' = @{
        model = 'claude-3-5-sonnet-20241022'
        command = { param($prompt, $output)
            # Claude - stdin only, no flags
            $prompt | & claude 2>&1 | Tee-Object $output
        }
    }
    'copilot' = @{
        model = ''
        command = { param($prompt, $output)
            # Copilot - use suggest with shell target
            $prompt | & gh copilot suggest -t shell 2>&1 | Tee-Object $output
        }
    }
}

# Extension generation function
function Build-Extension {
    param(
        [string]$ExtensionName,
        [string]$CLI,
        [string]$OutputPath,
        [string]$LogPath
    )
    
    $prompt = @"
Create a VSCode extension for: $ExtensionName

Requirements:
- Complete package.json with proper metadata
- Main extension.ts/js file with activate() and deactivate()
- All required dependencies
- README.md with usage instructions
- Output as a complete directory structure

Follow VSCode extension best practices. Output code only, no explanations.
"@

    try {
        $cliConfig = $CLICommands[$CLI]
        if(-not $cliConfig) {
            throw "Unknown CLI: $CLI"
        }
        
        $result = & $cliConfig.command $prompt $LogPath
        
        if($LASTEXITCODE -eq 0 -and (Test-Path $LogPath)) {
            $content = Get-Content $LogPath -Raw
            if($content.Length -gt 100) {
                return @{
                    success = $true
                    output = $content
                    cli = $CLI
                }
            }
        }
        
        return @{
            success = $false
            error = "CLI returned empty or error: $LASTEXITCODE"
        }
        
    } catch {
        return @{
            success = $false
            error = $_.Exception.Message
        }
    }
}

# Agent distribution
$agentsPerCLI = @{
    'opencode' = [math]::Ceiling($MaxAgents * 0.25)
    'gemini' = [math]::Ceiling($MaxAgents * 0.25)
    'codex' = [math]::Ceiling($MaxAgents * 0.20)
    'claude' = [math]::Ceiling($MaxAgents * 0.20)
    'copilot' = [math]::Ceiling($MaxAgents * 0.10)
}

$taskIdx = 0
$agentId = 1

Write-Host "`nLaunching $MaxAgents agents..." -ForegroundColor Cyan

foreach($cli in $agentsPerCLI.Keys) {
    $count = $agentsPerCLI[$cli]
    
    for($i = 1; $i -le $count; $i++) {
        $agentName = "Agent_${agentId}_${cli}_builder"
        
        # Calculate tasks for this agent
        $tasksPerAgent = [math]::Ceiling($totalTasks / $MaxAgents)
        $agentTasks = $unchecked | Select-Object -Skip $taskIdx -First $tasksPerAgent
        $taskIdx += $tasksPerAgent
        
        if(-not $agentTasks -or $agentTasks.Count -eq 0) {
            break
        }
        
        # Launch async job (inline CLI code, not function)
        Start-Job -Name $agentName -ScriptBlock {
            param($name, $cli, $tasks, $outDir, $logDir)
            
            $completed = 0
            $failed = 0
            
            foreach($task in $tasks) {
                $safeName = $task -replace '[^a-zA-Z0-9_-]', '_'
                $extDir = Join-Path $outDir "${safeName}_extension"
                $logFile = Join-Path $logDir "${name}_${safeName}.log"
                
                $prompt = @"
Create a VSCode extension for: $task

Requirements:
- Complete package.json with proper metadata
- Main extension.ts/js file with activate() and deactivate()
- All required dependencies
- README.md with usage instructions
- Output as a complete directory structure

Follow VSCode extension best practices. Output code only, no explanations.
"@

                try {
                    # Execute CLI based on type
                    $result = $null
                    $exitCode = 0
                    
                    switch($cli) {
                        'opencode' {
                            # OpenCode uses 'run' subcommand with -p flag
                            $result = & opencode run -m grok-2-1212 -p $prompt 2>&1
                            $exitCode = $LASTEXITCODE
                        }
                        'gemini' {
                            # Gemini - use positional prompt, don't use -m or approval flags (defaults are fine)
                            $result = & gemini $prompt 2>&1
                            $exitCode = $LASTEXITCODE
                        }
                        'codex' {
                            # Codex needs stdin to be a terminal, use temp file workaround
                            $tempFile = New-TemporaryFile
                            $prompt | Out-File $tempFile -Encoding utf8
                            $result = Get-Content $tempFile | & codex 2>&1
                            Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
                            $exitCode = $LASTEXITCODE
                        }
                        'claude' {
                            # Claude stdin only
                            $result = $prompt | & claude 2>&1
                            $exitCode = $LASTEXITCODE
                        }
                        'copilot' {
                            # Copilot suggest with shell target
                            $result = $prompt | & gh copilot suggest -t shell 2>&1
                            $exitCode = $LASTEXITCODE
                        }
                    }
                    
                    $result | Out-File $logFile -Force
                    
                    if($exitCode -eq 0 -and $result -and $result.Length -gt 100) {
                        $completed++
                        New-Item -ItemType Directory -Force -Path $extDir | Out-Null
                        $result | Out-File (Join-Path $extDir "generated_code.txt") -Force
                    } else {
                        $failed++
                        "ERROR: Exit code $exitCode, output length: $($result.Length)" | Out-File $logFile -Append
                    }
                    
                } catch {
                    $failed++
                    "ERROR: $($_.Exception.Message)" | Out-File $logFile -Append
                }
                
                # Progress update
                @{
                    agent = $name
                    completed = $completed
                    failed = $failed
                    current_task = $task
                    timestamp = Get-Date -Format "o"
                } | ConvertTo-Json -Compress | Out-File (Join-Path $logDir "${name}_progress.json") -Force
                
                Start-Sleep -Milliseconds 250
            }
            
            return @{
                agent = $name
                cli = $cli
                total = $tasks.Count
                completed = $completed
                failed = $failed
            }
            
        } -ArgumentList $agentName, $cli, $agentTasks, $OutputDir, $AgentLogDir
        
        $agentId++
        Write-Host "  ✓ Launched $agentName with $($agentTasks.Count) tasks" -ForegroundColor Green
        Start-Sleep -Milliseconds 100
    }
}

$totalLaunched = $agentId - 1
Write-Host "`n🚀 Launched $totalLaunched agents" -ForegroundColor Green
Write-Host "Monitor: Get-Job | Format-Table Name, State" -ForegroundColor Cyan
Write-Host "Progress: Get-ChildItem '$AgentLogDir\*_progress.json' | Get-Content | ConvertFrom-Json" -ForegroundColor Cyan

# Monitor loop
if(-not $TestMode) {
    Write-Host "`nMonitoring agents (Ctrl+C to exit monitor, agents continue)..." -ForegroundColor Yellow
    
    while($true) {
        Start-Sleep -Seconds 10
        
        $jobs = Get-Job | Where-Object { $_.Name -like "Agent_*" }
        $running = ($jobs | Where-Object State -eq 'Running').Count
        $completed = ($jobs | Where-Object State -eq 'Completed').Count
        $failed = ($jobs | Where-Object State -eq 'Failed').Count
        
        $progressFiles = Get-ChildItem "$AgentLogDir\*_progress.json" -ErrorAction SilentlyContinue
        $totalCompleted = 0
        $totalFailed = 0
        
        foreach($pf in $progressFiles) {
            $progress = Get-Content $pf | ConvertFrom-Json
            $totalCompleted += $progress.completed
            $totalFailed += $progress.failed
        }
        
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[$timestamp] Agents: $running running, $completed finished, $failed errored | Extensions: $totalCompleted built, $totalFailed failed" -ForegroundColor Cyan
        
        if($running -eq 0) {
            Write-Host "`n✓ All agents completed!" -ForegroundColor Green
            break
        }
    }
    
    # Final summary
    Write-Host "`n=== FINAL SUMMARY ===" -ForegroundColor Magenta
    $jobs | Receive-Job | Format-Table -AutoSize
    
    Write-Host "`nExtensions saved to: $OutputDir" -ForegroundColor Green
    Write-Host "Logs saved to: $AgentLogDir" -ForegroundColor Green
    
    # Update progress tracker
    $newTotal = 2496 + $totalCompleted
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
                }
            }
        }
    } | ConvertTo-Json -Depth 5 | Out-File "$LogDir\UNIFIED_PROGRESS.json" -Force
    
    Write-Host "`nProgress updated: $newTotal / 3148 ($newPercent%)" -ForegroundColor Cyan
}
