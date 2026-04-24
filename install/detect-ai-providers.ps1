param(
    [string]$OutputPath = "$env:TEMP\windows-ai-provider-setup.json"
)

$ErrorActionPreference = "SilentlyContinue"

function Get-ExePath {
    param(
        [string[]]$Names,
        [string[]]$CandidatePaths
    )

    foreach ($name in $Names) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source) {
            return $cmd.Source
        }
    }

    foreach ($candidate in $CandidatePaths) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Get-CommandVersion {
    param([string]$ExePath)

    if (-not $ExePath) { return $null }

    $argSets = @(
        @("--version"),
        @("version"),
        @("-v")
    )

    foreach ($args in $argSets) {
        try {
            $output = & $ExePath @args 2>&1 | Out-String
            if ($output -and $output.Trim()) {
                return ($output.Trim().Split([Environment]::NewLine)[0]).Substring(0, [Math]::Min(200, ($output.Trim().Split([Environment]::NewLine)[0]).Length))
            }
        } catch {
        }
    }

    return $null
}

function Test-AuthConfigured {
    param([string[]]$EnvVars)

    if (-not $EnvVars -or $EnvVars.Count -eq 0) {
        return $true
    }

    foreach ($envVar in $EnvVars) {
        if ([Environment]::GetEnvironmentVariable($envVar)) {
            return $true
        }
    }
    return $false
}

function Get-ProviderRecord {
    param(
        [string]$Id,
        [string]$DisplayName,
        [string[]]$ExecutableNames,
        [string[]]$CandidatePaths,
        [string[]]$AuthEnvVars,
        [string]$InstallUrl,
        [string]$AuthHint,
        [string]$Category = "cloud_cli",
        [hashtable]$Metadata = @{},
        [bool]$SupportsLocalModels = $false,
        [bool]$SupportsCode = $false,
        [bool]$SupportsVision = $false
    )

    $exePath = Get-ExePath -Names $ExecutableNames -CandidatePaths $CandidatePaths
    $version = Get-CommandVersion -ExePath $exePath
    $authConfigured = Test-AuthConfigured -EnvVars $AuthEnvVars

    $recommendedAction = if ($exePath -and $authConfigured) {
        "ready"
    } elseif ($exePath) {
        "authenticate"
    } else {
        "install"
    }

    return [ordered]@{
        provider_id = $Id
        display_name = $DisplayName
        category = $Category
        detected = [bool]$exePath
        executable_path = $exePath
        version = $version
        auth_configured = $authConfigured
        recommended_action = $recommendedAction
        install_url = $InstallUrl
        auth_hint = $AuthHint
        capabilities = [ordered]@{
            supports_local_models = $SupportsLocalModels
            supports_chat = $true
            supports_code = $SupportsCode
            supports_vision = $SupportsVision
        }
        metadata = [ordered]@{
            target_format = $Metadata.target_format
            example_targets = @($Metadata.example_targets)
            installer_strategy = $Metadata.installer_strategy
        }
    }
}

function New-ProviderTargetCatalog {
    param(
        [array]$Providers,
        [array]$RecommendedModels,
        [string]$DefaultTarget
    )

    $availableTargets = @()
    $setupRequiredTargets = @()

    foreach ($provider in $Providers) {
        $targets = @()

        if ($provider.provider_id -eq "ollama") {
            if ($RecommendedModels -and $RecommendedModels.Count -gt 0) {
                foreach ($model in $RecommendedModels) {
                    $targets += [ordered]@{
                        target = $model.target
                        model_id = $model.id
                        reason = $model.reason
                        source = "ollama"
                        type = "local_model"
                        is_default = ($model.target -eq $DefaultTarget)
                    }
                }
            } else {
                $targets += [ordered]@{
                    target = $provider.metadata.target_format
                    model_id = $null
                    reason = "Install Ollama and download a local model to enable this target."
                    source = "ollama"
                    type = "local_runtime"
                    is_default = $false
                }
            }
        } else {
            foreach ($target in @($provider.metadata.example_targets)) {
                if ($target) {
                    $targets += [ordered]@{
                        target = $target
                        model_id = $null
                        reason = $null
                        source = "provider_cli"
                        type = "cloud_cli"
                        is_default = $false
                    }
                }
            }
        }

        foreach ($targetInfo in $targets) {
            $entry = [ordered]@{
                provider_id = $provider.provider_id
                provider_name = $provider.display_name
                category = $provider.category
                detected = $provider.detected
                auth_configured = $provider.auth_configured
                recommended_action = $provider.recommended_action
                install_url = $provider.install_url
                auth_hint = $provider.auth_hint
                capabilities = $provider.capabilities
                metadata = $provider.metadata
                target = $targetInfo.target
                target_format = $provider.metadata.target_format
                source = $targetInfo.source
                type = $targetInfo.type
                model_id = $targetInfo.model_id
                reason = $targetInfo.reason
                is_default = $targetInfo.is_default
            }

            if ($provider.recommended_action -eq "ready") {
                $availableTargets += $entry
            } else {
                $setupRequiredTargets += $entry
            }
        }
    }

    $allTargets = @($availableTargets + $setupRequiredTargets)
    $catalogDefault = if ($DefaultTarget) {
        $DefaultTarget
    } elseif ($availableTargets.Count -gt 0) {
        $availableTargets[0].target
    } else {
        $null
    }

    return [ordered]@{
        default_target = $catalogDefault
        available_targets = $availableTargets
        setup_required_targets = $setupRequiredTargets
        all_targets = $allTargets
        counts = [ordered]@{
            available = $availableTargets.Count
            setup_required = $setupRequiredTargets.Count
            total = $allTargets.Count
        }
    }
}

$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
$programFiles = ${env:ProgramFiles}
$programFilesX86 = ${env:ProgramFiles(x86)}

$providers = @(
    (Get-ProviderRecord -Id "gemini" -DisplayName "Gemini CLI" -ExecutableNames @("gemini", "gemini.exe") -CandidatePaths @(
        "$localAppData\Programs\GeminiCLI\gemini.exe",
        "$programFiles\GeminiCLI\gemini.exe",
        "$programFilesX86\GeminiCLI\gemini.exe"
    ) -AuthEnvVars @("GEMINI_API_KEY", "GOOGLE_API_KEY") -InstallUrl "https://ai.google.dev/" -AuthHint "Sign in with your Google AI credentials or configure an API key." -Category "cloud_cli" -Metadata @{ target_format = "cli:gemini"; example_targets = @("cli:gemini"); installer_strategy = "detect_or_install_cli" } -SupportsVision $true),
    (Get-ProviderRecord -Id "codex" -DisplayName "Codex CLI" -ExecutableNames @("codex", "codex.exe") -CandidatePaths @(
        "$localAppData\Programs\CodexCLI\codex.exe",
        "$programFiles\CodexCLI\codex.exe",
        "$programFilesX86\CodexCLI\codex.exe"
    ) -AuthEnvVars @("OPENAI_API_KEY") -InstallUrl "https://platform.openai.com/" -AuthHint "Authenticate with your OpenAI account or API key." -Category "cloud_cli" -Metadata @{ target_format = "cli:codex"; example_targets = @("cli:codex"); installer_strategy = "detect_or_install_cli" } -SupportsCode $true),
    (Get-ProviderRecord -Id "claude" -DisplayName "Claude CLI" -ExecutableNames @("claude", "claude.exe") -CandidatePaths @(
        "$localAppData\Programs\ClaudeCLI\claude.exe",
        "$programFiles\ClaudeCLI\claude.exe",
        "$programFilesX86\ClaudeCLI\claude.exe"
    ) -AuthEnvVars @("ANTHROPIC_API_KEY") -InstallUrl "https://console.anthropic.com/" -AuthHint "Authenticate with Anthropic credentials or API key." -Category "cloud_cli" -Metadata @{ target_format = "cli:claude"; example_targets = @("cli:claude"); installer_strategy = "detect_or_install_cli" } -SupportsCode $true -SupportsVision $true),
    (Get-ProviderRecord -Id "grok" -DisplayName "Grok CLI" -ExecutableNames @("grok", "grok.exe") -CandidatePaths @(
        "$localAppData\Programs\GrokCLI\grok.exe",
        "$programFiles\GrokCLI\grok.exe",
        "$programFilesX86\GrokCLI\grok.exe"
    ) -AuthEnvVars @("XAI_API_KEY", "GROK_API_KEY") -InstallUrl "https://x.ai/" -AuthHint "Authenticate with your xAI account or API key." -Category "cloud_cli" -Metadata @{ target_format = "cli:grok"; example_targets = @("cli:grok"); installer_strategy = "detect_or_install_cli" } -SupportsCode $true),
    (Get-ProviderRecord -Id "ollama" -DisplayName "Ollama" -ExecutableNames @("ollama", "ollama.exe") -CandidatePaths @(
        "$localAppData\Programs\Ollama\ollama.exe",
        "$programFiles\Ollama\ollama.exe",
        "$programFilesX86\Ollama\ollama.exe"
    ) -AuthEnvVars @() -InstallUrl "https://ollama.com/download" -AuthHint "No cloud auth required. Download a model to begin." -Category "local_runtime" -Metadata @{ target_format = "ollama:<model>"; example_targets = @("ollama:llama3.1:8b", "ollama:phi3:mini"); installer_strategy = "detect_or_install_runtime" } -SupportsLocalModels $true -SupportsCode $true)
)

$memoryGB = $null
try {
    $computerInfo = Get-CimInstance Win32_ComputerSystem
    if ($computerInfo.TotalPhysicalMemory) {
        $memoryGB = [Math]::Round($computerInfo.TotalPhysicalMemory / 1GB, 1)
    }
} catch {
}

$gpuHint = $null
try {
    $gpuHint = (Get-CimInstance Win32_VideoController | Select-Object -First 1 -ExpandProperty Name)
} catch {
}

$cpuCount = [Environment]::ProcessorCount

$recommendedModels = @()
if (($memoryGB -as [double]) -ge 32) {
    $recommendedModels = @(
        @{ id = "qwen2.5-coder:14b"; reason = "Strong coding model for high-memory systems" },
        @{ id = "llama3.1:8b"; reason = "General purpose balanced model" },
        @{ id = "mistral:7b"; reason = "Fast local general model" }
    )
} elseif (($memoryGB -as [double]) -ge 16) {
    $recommendedModels = @(
        @{ id = "llama3.1:8b"; reason = "Balanced default for midrange systems" },
        @{ id = "qwen2.5-coder:7b"; reason = "Good code model for midrange systems" },
        @{ id = "phi3:mini"; reason = "Fast and lighter backup option" }
    )
} else {
    $recommendedModels = @(
        @{ id = "phi3:mini"; reason = "Lightweight default for lower-memory systems" },
        @{ id = "gemma2:2b"; reason = "Small local model for constrained hardware" },
        @{ id = "tinyllama"; reason = "Very lightweight fallback" }
    )
}

$recommendedModels = @($recommendedModels | ForEach-Object {
    [ordered]@{
        id = $_.id
        reason = $_.reason
        target = "ollama:$($_.id)"
    }
})

$defaultModelId = if ($recommendedModels.Count -gt 0) { $recommendedModels[0].id } else { $null }
$defaultTarget = if ($recommendedModels.Count -gt 0) { $recommendedModels[0].target } else { $null }
$targetCatalog = New-ProviderTargetCatalog -Providers $providers -RecommendedModels $recommendedModels -DefaultTarget $defaultTarget

$setupPlan = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    providers = $providers
    hardware = [ordered]@{
        platform = "Windows"
        architecture = $env:PROCESSOR_ARCHITECTURE
        cpu_count = $cpuCount
        total_memory_gb = $memoryGB
        gpu_hint = $gpuHint
    }
    ollama = [ordered]@{
        default_model_id = $defaultModelId
        default_target = $defaultTarget
        recommended_models = $recommendedModels
    }
    target_catalog = $targetCatalog
    installer_actions = @($providers | ForEach-Object {
        [ordered]@{
            provider_id = $_.provider_id
            action = $_.recommended_action
            detected = $_.detected
        }
    })
}

$parentDir = Split-Path -Parent $OutputPath
if ($parentDir -and -not (Test-Path $parentDir)) {
    New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
}

$setupPlan | ConvertTo-Json -Depth 8 | Set-Content -Path $OutputPath -Encoding UTF8
Write-Output $OutputPath
