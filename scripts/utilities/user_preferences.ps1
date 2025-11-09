# User Preference Profile - Personalized AI behavior
# INTELLIGENCE #7

$profileFile = "C:\Users\antho\logs\unified_ai_memory\memory_database\USER_PREFERENCES.json"

function Initialize-UserProfile {
    @{
        version = "1.0"
        last_updated = Get-Date -Format 'o'
        
        # Communication style
        communication = @{
            tone = "concise"  # concise, detailed, technical
            verbosity = "minimal"  # minimal, moderate, verbose
            output_format = "clean"  # clean, formatted, rich
            explanations = "only_on_error"  # always, only_on_error, never
        }
        
        # Risk tolerance
        autonomy = @{
            risk_tolerance = "high"  # low, medium, high
            auto_approve_low_risk = $true
            auto_approve_medium_risk = $true
            auto_approve_high_risk = $false
            require_confirmation = $false
        }
        
        # Tool preferences
        tools = @{
            preferred_package_manager = "pip"  # pip, uv, conda
            preferred_shell = "pwsh"  # pwsh, powershell, cmd
            parallel_execution = $true
            max_parallel_jobs = 10
        }
        
        # Logging preferences
        logging = @{
            save_all_outputs = $true
            create_summaries = $true
            detail_level = "high"  # low, medium, high
            organize_automatically = $true
        }
        
        # Session preferences
        session = @{
            auto_save_state = $true
            save_interval_minutes = 5
            preserve_context = $true
            restore_on_startup = $true
        }
        
        # Learned patterns
        learned = @{
            frequent_commands = @()
            common_directories = @("C:\Users\antho\Windows-AI", "C:\Users\antho\AI CLI")
            preferred_models = @("claude-sonnet", "gemini-pro")
            work_hours = @{start = 8; end = 22}
        }
        
        # Project specific
        projects = @{
            "Windows-AI" = @{
                auto_organize = $true
                extension_batch_size = 100
                run_tests = $false
            }
        }
    } | ConvertTo-Json -Depth 10 | Out-File $profileFile
}

function Get-UserPreference {
    param([string]$Category, [string]$Key)
    
    if (-not (Test-Path $profileFile)) { Initialize-UserProfile }
    
    $profile = Get-Content $profileFile | ConvertFrom-Json
    
    if ($Key) {
        return $profile.$Category.$Key
    } else {
        return $profile.$Category
    }
}

function Set-UserPreference {
    param([string]$Category, [string]$Key, $Value)
    
    if (-not (Test-Path $profileFile)) { Initialize-UserProfile }
    
    $profile = Get-Content $profileFile | ConvertFrom-Json
    $profile.$Category.$Key = $Value
    $profile.last_updated = Get-Date -Format 'o'
    
    $profile | ConvertTo-Json -Depth 10 | Out-File $profileFile
}

# Initialize if doesn't exist
if (-not (Test-Path $profileFile)) { Initialize-UserProfile }
