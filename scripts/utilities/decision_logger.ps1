# Decision Log - Learn from past decisions
# CRITICAL PRIORITY #2

$decisionLog = "C:\Users\antho\logs\unified_ai_memory\memory_database\decisions\decision_log.jsonl"

function Add-Decision {
    param(
        [string]$Action,
        [string]$Reasoning,
        [string]$Context,
        [hashtable]$Alternatives = @{},
        [string]$Outcome = "pending"
    )
    
    $decision = @{
        timestamp = Get-Date -Format 'o'
        action = $Action
        reasoning = $Reasoning
        context = $Context
        alternatives_considered = $Alternatives
        outcome = $Outcome
        session_id = Get-Date -Format 'yyyyMMdd_HHmmss'
    }
    
    $decision | ConvertTo-Json -Compress | Add-Content $decisionLog
}

function Get-SimilarDecisions {
    param([string]$Context)
    
    if (-not (Test-Path $decisionLog)) { return @() }
    
    Get-Content $decisionLog | 
        ForEach-Object { $_ | ConvertFrom-Json } | 
        Where-Object { $_.context -match $Context } |
        Sort-Object timestamp -Descending |
        Select-Object -First 10
}

function Get-DecisionPatterns {
    if (-not (Test-Path $decisionLog)) { return @{} }
    
    $decisions = Get-Content $decisionLog | ForEach-Object { $_ | ConvertFrom-Json }
    
    @{
        total_decisions = $decisions.Count
        successful = ($decisions | Where-Object { $_.outcome -eq 'success' }).Count
        failed = ($decisions | Where-Object { $_.outcome -eq 'failed' }).Count
        common_actions = $decisions | Group-Object action | Sort-Object Count -Descending | Select-Object -First 10
        learned_preferences = @{
            # Extract patterns
            autonomous_approved = ($decisions | Where-Object { $_.action -match 'auto' }).Count
            manual_intervention = ($decisions | Where-Object { $_.action -match 'manual' }).Count
        }
    }
}

# Export functions
Export-ModuleMember -Function Add-Decision, Get-SimilarDecisions, Get-DecisionPatterns
