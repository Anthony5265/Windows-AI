param(
    [Parameter(Mandatory = $true)]
    [string]$SetupPlanPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SetupPlanPath)) {
    throw "Provider setup plan not found: $SetupPlanPath"
}

$raw = Get-Content -Path $SetupPlanPath -Raw -Encoding UTF8
$plan = $raw | ConvertFrom-Json

$errors = New-Object System.Collections.Generic.List[string]

function Add-ValidationError {
    param([string]$Message)
    $script:errors.Add($Message) | Out-Null
}

if (-not $plan.providers) {
    Add-ValidationError "providers is required"
}

if (-not $plan.ollama) {
    Add-ValidationError "ollama is required"
} elseif (-not $plan.ollama.recommended_models) {
    Add-ValidationError "ollama.recommended_models is required"
}

if (-not $plan.installer_actions) {
    Add-ValidationError "installer_actions is required"
}

foreach ($provider in @($plan.providers)) {
    if (-not $provider.provider_id) { Add-ValidationError "provider.provider_id is required" }
    if ($provider.recommended_action -notin @("ready", "authenticate", "install")) {
        Add-ValidationError "provider $($provider.provider_id) has invalid recommended_action: $($provider.recommended_action)"
    }
    if ($provider.provider_id -eq "ollama" -and $provider.auth_configured -ne $true) {
        Add-ValidationError "ollama should not require cloud authentication"
    }
}

foreach ($model in @($plan.ollama.recommended_models)) {
    if (-not $model.id) { Add-ValidationError "ollama model id is required" }
    if (-not $model.target -or -not $model.target.StartsWith("ollama:")) {
        Add-ValidationError "ollama model $($model.id) must include a runnable ollama:<model> target"
    }
}

if ($plan.target_catalog) {
    foreach ($target in @($plan.target_catalog.all_targets)) {
        if (-not $target.provider_id) { Add-ValidationError "target provider_id is required" }
        if (-not $target.target) { Add-ValidationError "target value is required" }
        if ($target.recommended_action -notin @("ready", "authenticate", "install")) {
            Add-ValidationError "target $($target.target) has invalid recommended_action: $($target.recommended_action)"
        }
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    throw "Provider setup validation failed with $($errors.Count) error(s)."
}

Write-Output "Provider setup plan is valid: $SetupPlanPath"
