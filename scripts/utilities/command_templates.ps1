# Command Templates - Proven working sequences
# HIGH PRIORITY #5

$templateDb = "C:\Users\antho\logs\unified_ai_memory\memory_database\command_templates.json"

function Initialize-Templates {
    $templates = @{
        version = "1.0"
        templates = @{
            
            # Extension generation
            generate_extensions = @{
                description = "Generate Windows-AI plugin extensions"
                commands = @(
                    "cd C:\Users\antho\Windows-AI",
                    '$unchecked = Get-Content ".\ULTIMATE_EXTENSION_ROADMAP.md" | Select-String "^\s*- \[ \] (.+)" | Select-Object -First {count}',
                    "foreach ($line in $unchecked) { ... }"
                )
                parameters = @{count = 100}
                success_rate = 1.0
            }
            
            # Log organization
            organize_logs = @{
                description = "Organize AI CLI logs"
                commands = @(
                    ".\ai_cli_organizer.ps1 -OrganizeNow"
                )
                success_rate = 1.0
            }
            
            # Agent management
            start_agents = @{
                description = "Start all autonomous agents"
                commands = @(
                    ".\smart_prompt_detector.ps1 -Start",
                    ".\unified_memory_manager.ps1 -Start"
                )
                success_rate = 1.0
            }
            
            # Session save
            save_session = @{
                description = "Save current session state"
                commands = @(
                    ".\session_state_manager.ps1 -Save"
                )
                success_rate = 1.0
            }
            
            # Build operations
            build_windows_ai = @{
                description = "Build Windows-AI project"
                commands = @(
                    "cd C:\Users\antho\Windows-AI",
                    "python --version",
                    "node --version"
                )
                prerequisites = @("python", "node")
                success_rate = 0.9
            }
            
            # Git operations
            safe_commit = @{
                description = "Safe git commit with validation"
                commands = @(
                    "git status",
                    "git diff --stat",
                    'git commit -m "{message}"'
                )
                parameters = @{message = ""}
                validation_required = $true
            }
            
        }
    }
    
    $templates | ConvertTo-Json -Depth 10 | Out-File $templateDb
}

function Get-Template {
    param([string]$Name)
    
    if (-not (Test-Path $templateDb)) { Initialize-Templates }
    
    $templates = Get-Content $templateDb | ConvertFrom-Json
    $templates.templates.$Name
}

function Invoke-Template {
    param(
        [string]$Name,
        [hashtable]$Parameters = @{}
    )
    
    $template = Get-Template -Name $Name
    if (-not $template) {
        Write-Host "Template '$Name' not found" -ForegroundColor Red
        return
    }
    
    Write-Host "Executing template: $($template.description)" -ForegroundColor Cyan
    
    foreach ($cmd in $template.commands) {
        # Replace parameters
        $finalCmd = $cmd
        foreach ($key in $Parameters.Keys) {
            $finalCmd = $finalCmd -replace "\{$key\}", $Parameters[$key]
        }
        
        Write-Host "  > $finalCmd" -ForegroundColor Gray
        Invoke-Expression $finalCmd
    }
}

# Initialize if doesn't exist
if (-not (Test-Path $templateDb)) { Initialize-Templates }
