# Unified Progress Tracker - No duplicate work across CLIs
# HIGH PRIORITY #18

$progressFile = "C:\Users\antho\logs\unified_ai_memory\UNIFIED_PROGRESS.json"

function Update-Progress {
    param(
        [string]$TaskName,
        [string]$CLI,
        [string]$Status,
        [int]$PercentComplete = 0,
        [hashtable]$Metadata = @{}
    )
    
    $lock = "C:\Users\antho\logs\unified_ai_memory\progress.lock"
    
    # Simple file-based locking
    while (Test-Path $lock) { Start-Sleep -Milliseconds 100 }
    New-Item $lock -ItemType File -Force | Out-Null
    
    try {
        $progress = if (Test-Path $progressFile) {
            Get-Content $progressFile | ConvertFrom-Json
        } else {
            @{
                last_updated = Get-Date -Format 'o'
                tasks = @{}
            }
        }
        
        if (-not $progress.tasks.$TaskName) {
            $progress.tasks | Add-Member -NotePropertyName $TaskName -NotePropertyValue @{
                created = Get-Date -Format 'o'
                status = $Status
                assigned_cli = $CLI
                percent_complete = $PercentComplete
                last_updated = Get-Date -Format 'o'
                metadata = $Metadata
                history = @()
            } -Force
        } else {
            $progress.tasks.$TaskName.status = $Status
            $progress.tasks.$TaskName.percent_complete = $PercentComplete
            $progress.tasks.$TaskName.last_updated = Get-Date -Format 'o'
            $progress.tasks.$TaskName.metadata = $Metadata
            $progress.tasks.$TaskName.history += @{
                timestamp = Get-Date -Format 'o'
                cli = $CLI
                status = $Status
                percent = $PercentComplete
            }
        }
        
        $progress.last_updated = Get-Date -Format 'o'
        $progress | ConvertTo-Json -Depth 10 | Out-File $progressFile
        
    } finally {
        Remove-Item $lock -Force
    }
}

function Get-TaskProgress {
    param([string]$TaskName)
    
    if (-not (Test-Path $progressFile)) { return $null }
    
    $progress = Get-Content $progressFile | ConvertFrom-Json
    $progress.tasks.$TaskName
}

function Get-AllProgress {
    if (-not (Test-Path $progressFile)) { return @{} }
    
    Get-Content $progressFile | ConvertFrom-Json
}

function Complete-Task {
    param([string]$TaskName, [string]$CLI)
    
    Update-Progress -TaskName $TaskName -CLI $CLI -Status "completed" -PercentComplete 100
}

# Export functions for use by all CLIs
Export-ModuleMember -Function Update-Progress, Get-TaskProgress, Get-AllProgress, Complete-Task
