# Session State Manager - Resume exactly where left off
# CRITICAL PRIORITY #1

param(
    [switch]$Save,
    [switch]$Load,
    [switch]$Update
)

$stateFile = "C:\Users\antho\logs\unified_ai_memory\CURRENT_STATE.json"

function Get-CurrentState {
    @{
        timestamp = Get-Date -Format 'o'
        session_id = Get-Date -Format 'yyyyMMdd_HHmmss'
        
        # Current execution context
        current_directory = (Get-Location).Path
        last_command_executed = (Get-History -Count 1 | Select-Object -ExpandProperty CommandLine)
        last_command_time = (Get-History -Count 1 | Select-Object -ExpandProperty StartExecutionTime)
        
        # Active tasks
        active_tasks = @{
            windows_ai_build = @{
                status = "in_progress"
                extensions_created = 2496
                target = 3148
                current_batch = "continuing_to_completion"
            }
        }
        
        # Pending actions
        pending_actions = @()
        
        # Error states
        errors = @()
        
        # Agent states
        agents = @{
            smart_prompt_detector = @{
                status = "running"
                key_press = "1"
                log = "C:\Users\antho\logs\unified_sessions\smart_detector_*.log"
            }
            unified_memory_manager = @{
                status = "running"
                base = "C:\Users\antho\logs\unified_ai_memory"
                jobs = 3
            }
        }
        
        # Environment
        environment = @{
            auto_approval = $true
            terminal_restarted = $false
            context_preserved = $true
        }
        
        # Last known good state
        checkpoint = @{
            directory = (Get-Location).Path
            timestamp = Get-Date -Format 'o'
        }
    }
}

if ($Load) {
    if (Test-Path $stateFile) {
        $state = Get-Content $stateFile | ConvertFrom-Json
        Write-Host "=== SESSION STATE LOADED ===" -ForegroundColor Green
        Write-Host "Session ID: $($state.session_id)"
        Write-Host "Last Command: $($state.last_command_executed)"
        Write-Host "Current Directory: $($state.current_directory)"
        Write-Host "Active Tasks: $($state.active_tasks.Keys -join ', ')"
        
        # Restore directory
        if (Test-Path $state.current_directory) {
            Set-Location $state.current_directory
        }
        
        return $state
    } else {
        Write-Host "No saved state found" -ForegroundColor Yellow
    }
}

if ($Save -or $Update) {
    $state = Get-CurrentState
    $state | ConvertTo-Json -Depth 10 | Out-File $stateFile -Force
    Write-Host "✓ Session state saved: $stateFile" -ForegroundColor Green
    return $state
}

# Default: return current state
Get-CurrentState
