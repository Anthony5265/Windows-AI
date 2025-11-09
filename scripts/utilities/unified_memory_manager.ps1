# Unified Memory & Context Manager for All AI CLIs
# Creates persistent, shared context accessible by all AI agents
# Single source of truth for logs, memories, and context

param(
    [switch]$Start,
    [switch]$Stop,
    [switch]$Initialize
)

# SINGLE UNIFIED DIRECTORY - All AI CLIs use this
$UNIFIED_BASE = "C:\Users\antho\logs\unified_ai_memory"
$ACTIVE_SESSION = "$UNIFIED_BASE\active_session"
$SHARED_CONTEXT = "$UNIFIED_BASE\shared_context"
$MEMORY_DB = "$UNIFIED_BASE\memory_database"
$CLI_OUTPUTS = "$UNIFIED_BASE\cli_outputs"

$pidFile = "$UNIFIED_BASE\memory_manager.pid"
$logFile = "$UNIFIED_BASE\memory_manager.log"

function Write-MemLog {
    param([string]$Message)
    "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')) - $Message" | Tee-Object -FilePath $logFile -Append
}

function Initialize-UnifiedStructure {
    # Create unified directory structure
    $structure = @(
        $UNIFIED_BASE,
        $ACTIVE_SESSION,
        "$ACTIVE_SESSION\current_chat",
        "$ACTIVE_SESSION\prompts",
        "$ACTIVE_SESSION\responses",
        $SHARED_CONTEXT,
        "$SHARED_CONTEXT\gemini",
        "$SHARED_CONTEXT\claude",
        "$SHARED_CONTEXT\codex", 
        "$SHARED_CONTEXT\opencode",
        "$SHARED_CONTEXT\copilot",
        $MEMORY_DB,
        "$MEMORY_DB\sessions",
        "$MEMORY_DB\conversations",
        "$MEMORY_DB\decisions",
        "$MEMORY_DB\learnings",
        $CLI_OUTPUTS,
        "$CLI_OUTPUTS\raw",
        "$CLI_OUTPUTS\summaries",
        "$CLI_OUTPUTS\indexed"
    )
    
    foreach ($dir in $structure) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    
    # Create master context index
    $masterIndex = @{
        created = Get-Date -Format 'o'
        version = "1.0"
        structure = $structure
        purpose = "Unified memory and context for all AI CLIs"
        active_session_id = Get-Date -Format 'yyyyMMdd_HHmmss'
        cli_sources = @("gemini", "claude", "codex", "opencode", "copilot")
    }
    
    $masterIndex | ConvertTo-Json -Depth 5 | Out-File "$UNIFIED_BASE\MASTER_INDEX.json"
    
    Write-MemLog "Initialized unified structure at $UNIFIED_BASE"
}

if ($Initialize) {
    Write-Host "Initializing Unified Memory Structure..." -ForegroundColor Yellow
    Initialize-UnifiedStructure
    Write-Host "✓ Unified memory structure created at:" -ForegroundColor Green
    Write-Host "  $UNIFIED_BASE" -ForegroundColor Cyan
    return
}

if ($Stop) {
    if (Test-Path $pidFile) {
        $jobs = Get-Content $pidFile | ConvertFrom-Json
        foreach ($jobId in $jobs) {
            Stop-Job -Id $jobId -ErrorAction SilentlyContinue
            Remove-Job -Id $jobId -ErrorAction SilentlyContinue
        }
        Remove-Item $pidFile
        Write-MemLog "Memory manager stopped"
    }
    return
}

if ($Start) {
    Initialize-UnifiedStructure
    
    Write-MemLog "Unified Memory Manager starting..."
    
    # Job 1: Real-time file system monitor - catches EVERYTHING
    $fsWatchJob = Start-Job -ScriptBlock {
        param($base, $active, $context, $db, $outputs, $log)
        
        function Write-Log { 
            param([string]$Msg)
            "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')) - $Msg" | Out-File $log -Append 
        }
        
        # Monitor all AI CLI directories
        $watchPaths = @(
            "$env:USERPROFILE\.gemini",
            "$env:USERPROFILE\.claude",
            "$env:USERPROFILE\.codex",
            "$env:USERPROFILE\.opencode",
            "$env:USERPROFILE\.copilot",
            "$env:USERPROFILE\AI CLI",
            "$env:USERPROFILE\Windows-AI",
            "$env:USERPROFILE\logs"
        )
        
        # Create file system watchers for each path
        $watchers = @()
        foreach ($path in $watchPaths) {
            if (Test-Path $path) {
                $watcher = New-Object System.IO.FileSystemWatcher
                $watcher.Path = $path
                $watcher.IncludeSubdirectories = $true
                $watcher.EnableRaisingEvents = $true
                
                # Watch for: Created, Modified, Deleted
                Register-ObjectEvent -InputObject $watcher -EventName Created -Action {
                    $file = $Event.SourceEventArgs.FullPath
                    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
                    
                    # Copy to unified structure based on type
                    if ($file -match '\.(log|txt)$') {
                        $dest = "$using:outputs\raw\$(Split-Path $file -Leaf)"
                        Copy-Item $file $dest -Force -ErrorAction SilentlyContinue
                    }
                    elseif ($file -match 'chat|history|conversation') {
                        $cli = if ($file -match '\.gemini') { 'gemini' }
                               elseif ($file -match '\.claude') { 'claude' }
                               elseif ($file -match '\.codex') { 'codex' }
                               elseif ($file -match '\.opencode') { 'opencode' }
                               elseif ($file -match '\.copilot') { 'copilot' }
                               else { 'unknown' }
                        
                        $dest = "$using:context\$cli\$(Split-Path $file -Leaf)"
                        Copy-Item $file $dest -Force -ErrorAction SilentlyContinue
                        
                        # Also copy to active session
                        Copy-Item $file "$using:active\current_chat\${cli}_$(Split-Path $file -Leaf)" -Force -ErrorAction SilentlyContinue
                    }
                } | Out-Null
                
                $watchers += $watcher
            }
        }
        
        # Keep job alive
        while ($true) { Start-Sleep -Seconds 60 }
        
    } -ArgumentList $UNIFIED_BASE, $ACTIVE_SESSION, $SHARED_CONTEXT, $MEMORY_DB, $CLI_OUTPUTS, $logFile
    
    # Job 2: Periodic scanner - organizes anything missed
    $scanJob = Start-Job -ScriptBlock {
        param($base, $context, $outputs, $log)
        
        function Write-Log { 
            param([string]$Msg)
            "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) - $Msg" | Out-File $log -Append 
        }
        
        $scanPaths = @(
            "$env:USERPROFILE\.gemini",
            "$env:USERPROFILE\.claude",
            "$env:USERPROFILE\.codex",
            "$env:USERPROFILE\.opencode",
            "$env:USERPROFILE\.copilot",
            "$env:USERPROFILE\AI CLI",
            "$env:USERPROFILE\Windows-AI"
        )
        
        while ($true) {
            Start-Sleep -Seconds 60  # Scan every minute
            
            Write-Log "Running periodic scan..."
            
            foreach ($scanPath in $scanPaths) {
                if (-not (Test-Path $scanPath)) { continue }
                
                # Find files modified in last 2 minutes
                $recentFiles = Get-ChildItem $scanPath -Recurse -File -ErrorAction SilentlyContinue |
                    Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-2) }
                
                foreach ($file in $recentFiles) {
                    # Organize by type
                    if ($file.Extension -match '\.(log|txt)$') {
                        $dest = "$outputs\raw\$($file.Name)"
                        if (-not (Test-Path $dest)) {
                            Copy-Item $file.FullName $dest -Force -ErrorAction SilentlyContinue
                            Write-Log "Captured log: $($file.Name)"
                        }
                    }
                    elseif ($file.Name -match 'chat|history|conversation|prompt|response') {
                        $cli = if ($file.FullName -match '\.gemini') { 'gemini' }
                               elseif ($file.FullName -match '\.claude') { 'claude' }
                               elseif ($file.FullName -match '\.codex') { 'codex' }
                               elseif ($file.FullName -match '\.opencode') { 'opencode' }
                               elseif ($file.FullName -match '\.copilot') { 'copilot' }
                               else { 'unknown' }
                        
                        $dest = "$context\$cli\$($file.Name)"
                        if (-not (Test-Path $dest)) {
                            Copy-Item $file.FullName $dest -Force -ErrorAction SilentlyContinue
                            Write-Log "Captured context: $($file.Name) -> $cli"
                        }
                    }
                }
            }
        }
    } -ArgumentList $UNIFIED_BASE, $SHARED_CONTEXT, $CLI_OUTPUTS, $logFile
    
    # Job 3: Generate cross-CLI context summaries
    $summaryJob = Start-Job -ScriptBlock {
        param($context, $outputs, $db, $log)
        
        function Write-Log { 
            param([string]$Msg)
            "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) - $Msg" | Out-File $log -Append 
        }
        
        while ($true) {
            Start-Sleep -Seconds 120  # Every 2 minutes
            
            # Generate unified summary accessible to all CLIs
            $allChats = @()
            foreach ($cli in @('gemini', 'claude', 'codex', 'opencode', 'copilot')) {
                $cliChats = Get-ChildItem "$context\$cli" -File -ErrorAction SilentlyContinue
                foreach ($chat in $cliChats) {
                    $allChats += @{
                        cli = $cli
                        file = $chat.Name
                        path = $chat.FullName
                        size = $chat.Length
                        modified = $chat.LastWriteTime
                    }
                }
            }
            
            # Create unified summary
            $summary = @{
                timestamp = Get-Date -Format 'o'
                total_conversations = $allChats.Count
                by_cli = @{
                    gemini = ($allChats | Where-Object { $_.cli -eq 'gemini' }).Count
                    claude = ($allChats | Where-Object { $_.cli -eq 'claude' }).Count
                    codex = ($allChats | Where-Object { $_.cli -eq 'codex' }).Count
                    opencode = ($allChats | Where-Object { $_.cli -eq 'opencode' }).Count
                    copilot = ($allChats | Where-Object { $_.cli -eq 'copilot' }).Count
                }
                recent_files = $allChats | Sort-Object { $_.modified } -Descending | Select-Object -First 20
            }
            
            $summary | ConvertTo-Json -Depth 5 | Out-File "$db\unified_summary.json"
            Write-Log "Generated unified summary: $($summary.total_conversations) conversations"
        }
    } -ArgumentList $SHARED_CONTEXT, $CLI_OUTPUTS, $MEMORY_DB, $logFile
    
    # Save job IDs
    @($fsWatchJob.Id, $scanJob.Id, $summaryJob.Id) | ConvertTo-Json | Out-File $pidFile
    
    Write-MemLog "Memory manager started - Jobs: $($fsWatchJob.Id), $($scanJob.Id), $summaryJob.Id"
    
    Write-Host "✓ Unified Memory Manager ACTIVE" -ForegroundColor Green
    Write-Host "  - Base: $UNIFIED_BASE" -ForegroundColor Cyan
    Write-Host "  - Real-time monitoring: ALL AI CLI directories" -ForegroundColor Cyan
    Write-Host "  - Shared context: $SHARED_CONTEXT" -ForegroundColor Cyan
    Write-Host "  - Memory DB: $MEMORY_DB" -ForegroundColor Cyan
    Write-Host "  - All CLIs can access unified memories" -ForegroundColor Green
    
    return @{
        FSWatchJob = $fsWatchJob
        ScanJob = $scanJob
        SummaryJob = $summaryJob
    }
}

Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  .\unified_memory_manager.ps1 -Initialize  # Create structure"
Write-Host "  .\unified_memory_manager.ps1 -Start       # Start monitoring"
Write-Host "  .\unified_memory_manager.ps1 -Stop        # Stop monitoring"
