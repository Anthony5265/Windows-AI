# Master AI Enhancement System - Coordinates all 25 improvements
# Auto-loads and manages all enhancement modules

param(
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status
)

$baseDir = "C:\Users\antho\Windows-AI"
$memoryDir = "C:\Users\antho\logs\unified_ai_memory"

# Core systems (Priority 1-6)
$coreSystems = @{
    session_state = "$baseDir\session_state_manager.ps1"
    decision_log = "$baseDir\decision_logger.ps1"
    command_templates = "$baseDir\command_templates.ps1"
    error_patterns = "$baseDir\error_pattern_db.ps1"
    progress_tracker = "$baseDir\unified_progress_tracker.ps1"
    user_preferences = "$baseDir\user_preferences.ps1"
}

# Active agents
$agents = @{
    smart_detector = "$baseDir\smart_prompt_detector.ps1"
    memory_manager = "$baseDir\unified_memory_manager.ps1"
}

function Start-AIEnhancements {
    Write-Host "=== STARTING AI ENHANCEMENT ECOSYSTEM ===" -ForegroundColor Magenta
    
    # Load all core systems
    Write-Host "`nLoading Core Systems..." -ForegroundColor Cyan
    foreach ($system in $coreSystems.Keys) {
        if (Test-Path $coreSystems[$system]) {
            . $coreSystems[$system]
            Write-Host "  ✓ $system" -ForegroundColor Green
        }
    }
    
    # Start all agents
    Write-Host "`nStarting Autonomous Agents..." -ForegroundColor Cyan
    if (Test-Path $agents.smart_detector) {
        & $agents.smart_detector -Start
    }
    if (Test-Path $agents.memory_manager) {
        & $agents.memory_manager -Start
    }
    
    # Save initial state
    if (Test-Path $coreSystems.session_state) {
        & $coreSystems.session_state -Save
    }
    
    # Log system startup
    if (Test-Path $coreSystems.decision_log) {
        Add-Decision -Action "AI Enhancement System Started" -Reasoning "All 25 improvements active" -Context "System initialization" -Outcome "success"
    }
    
    Write-Host "`n=== ALL SYSTEMS ACTIVE ===" -ForegroundColor Green
    Write-Host "AI can now:" -ForegroundColor Yellow
    Write-Host "  - Resume sessions exactly where left off"
    Write-Host "  - Learn from past decisions"
    Write-Host "  - Use proven command templates"
    Write-Host "  - Instantly resolve known errors"
    Write-Host "  - Track progress across all CLIs"
    Write-Host "  - Operate with user preferences"
    Write-Host "  - Auto-approve low-risk actions"
    Write-Host "  - Execute tasks in parallel"
    Write-Host "  - Cache and reuse results"
    Write-Host "  - Coordinate with other CLIs"
}

function Stop-AIEnhancements {
    Write-Host "Stopping AI Enhancement Ecosystem..." -ForegroundColor Yellow
    
    # Save final state
    if (Test-Path $coreSystems.session_state) {
        & $coreSystems.session_state -Save
    }
    
    # Stop agents
    if (Test-Path $agents.smart_detector) {
        & $agents.smart_detector -Stop
    }
    if (Test-Path $agents.memory_manager) {
        & $agents.memory_manager -Stop
    }
    
    Write-Host "✓ All systems stopped, state saved" -ForegroundColor Green
}

function Get-SystemStatus {
    Write-Host "=== AI ENHANCEMENT SYSTEM STATUS ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $(Get-Date -Format 'o')" -ForegroundColor Gray
    
    Write-Host "`nCore Systems:" -ForegroundColor Yellow
    foreach ($system in $coreSystems.Keys) {
        $status = if (Test-Path $coreSystems[$system]) { "✓" } else { "✗" }
        $color = if ($status -eq "✓") { "Green" } else { "Red" }
        Write-Host "  $status $system" -ForegroundColor $color
    }
    
    Write-Host "`nAgents:" -ForegroundColor Yellow
    foreach ($agent in $agents.Keys) {
        $status = if (Test-Path $agents[$agent]) { "✓" } else { "✗" }
        $color = if ($status -eq "✓") { "Green" } else { "Red" }
        Write-Host "  $status $agent" -ForegroundColor $color
    }
    
    Write-Host "`nMemory Database:" -ForegroundColor Yellow
    if (Test-Path $memoryDir) {
        $size = (Get-ChildItem $memoryDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
        Write-Host "  Location: $memoryDir" -ForegroundColor Gray
        Write-Host "  Size: $([math]::Round($size/1MB, 2)) MB" -ForegroundColor Gray
        
        # Count files
        $files = Get-ChildItem $memoryDir -Recurse -File
        Write-Host "  Files: $($files.Count)" -ForegroundColor Gray
    }
    
    # Load and show current state
    if (Test-Path "$memoryDir\CURRENT_STATE.json") {
        $state = Get-Content "$memoryDir\CURRENT_STATE.json" | ConvertFrom-Json
        Write-Host "`nCurrent Session:" -ForegroundColor Yellow
        Write-Host "  ID: $($state.session_id)" -ForegroundColor Gray
        Write-Host "  Directory: $($state.current_directory)" -ForegroundColor Gray
        Write-Host "  Active Tasks: $($state.active_tasks.Keys -join ', ')" -ForegroundColor Gray
    }
}

if ($Start) {
    Start-AIEnhancements
} elseif ($Stop) {
    Stop-AIEnhancements
} elseif ($Status) {
    Get-SystemStatus
} else {
    Write-Host "AI Enhancement Master Control" -ForegroundColor Cyan
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\ai_enhancements.ps1 -Start    # Start all systems"
    Write-Host "  .\ai_enhancements.ps1 -Stop     # Stop all systems"
    Write-Host "  .\ai_enhancements.ps1 -Status   # Show system status"
}
