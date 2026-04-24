param(
    [string]$OutputPath = "$env:TEMP\windows-ai-provider-setup.json",
    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$detectScript = Join-Path $scriptDir "detect-ai-providers.ps1"
$validateScript = Join-Path $scriptDir "validate-provider-setup.ps1"

if (-not (Test-Path $detectScript)) {
    throw "Provider detection script not found: $detectScript"
}

if (-not $SkipValidation -and -not (Test-Path $validateScript)) {
    throw "Provider setup validator not found: $validateScript"
}

& $detectScript -OutputPath $OutputPath | Out-Null

if (-not (Test-Path $OutputPath)) {
    throw "Provider setup plan was not created: $OutputPath"
}

if (-not $SkipValidation) {
    & $validateScript -SetupPlanPath $OutputPath | Out-Null
}

Write-Output $OutputPath
