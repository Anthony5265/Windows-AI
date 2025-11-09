# Error Pattern Database - Instant problem resolution
# HIGH PRIORITY #6

$errorDb = "C:\Users\antho\logs\unified_ai_memory\memory_database\error_patterns.json"

function Initialize-ErrorDb {
    $errors = @{
        version = "1.0"
        patterns = @{
            
            # Known errors with solutions
            "pkg_resources not found" = @{
                error_pattern = "ModuleNotFoundError: No module named 'pkg_resources'"
                solution = "pip install setuptools"
                context = "Python virtual environment"
                success_rate = 1.0
                occurrences = 5
            }
            
            "uv command not found" = @{
                error_pattern = "uv: command not found"
                solution = "pip install uv"
                context = "Python package management"
                success_rate = 1.0
                occurrences = 2
            }
            
            "access denied" = @{
                error_pattern = "Access is denied. \(os error 5\)"
                solution = "Run with elevated permissions or check file permissions"
                context = "File system operations"
                success_rate = 0.8
                occurrences = 10
                workaround = "Copy instead of move, create junction"
            }
            
            "path not found" = @{
                error_pattern = "Could not find a part of the path"
                solution = "Create parent directory first with New-Item -ItemType Directory -Force"
                context = "PowerShell file operations"
                success_rate = 1.0
                occurrences = 15
            }
            
            "ollama timeout" = @{
                error_pattern = "Timeout error from Ollama"
                solution = "Reduce model size, increase timeout, or chain smaller models"
                context = "Ollama model inference"
                success_rate = 0.7
                occurrences = 8
            }
            
            "network denied" = @{
                error_pattern = "installer DENIED network"
                solution = "Check firewall settings or use local resources"
                context = "Windows-AI installer"
                success_rate = 0.5
                occurrences = 3
            }
            
        }
    }
    
    $errors | ConvertTo-Json -Depth 10 | Out-File $errorDb
}

function Find-ErrorSolution {
    param([string]$ErrorMessage)
    
    if (-not (Test-Path $errorDb)) { Initialize-ErrorDb }
    
    $db = Get-Content $errorDb | ConvertFrom-Json
    
    foreach ($pattern in $db.patterns.PSObject.Properties) {
        if ($ErrorMessage -match [regex]::Escape($pattern.Value.error_pattern)) {
            Write-Host "✓ Known error detected: $($pattern.Name)" -ForegroundColor Yellow
            Write-Host "Solution: $($pattern.Value.solution)" -ForegroundColor Green
            if ($pattern.Value.workaround) {
                Write-Host "Workaround: $($pattern.Value.workaround)" -ForegroundColor Cyan
            }
            return $pattern.Value
        }
    }
    
    Write-Host "No matching error pattern found" -ForegroundColor Gray
    return $null
}

function Add-ErrorPattern {
    param(
        [string]$Name,
        [string]$Pattern,
        [string]$Solution,
        [string]$Context,
        [string]$Workaround = ""
    )
    
    if (-not (Test-Path $errorDb)) { Initialize-ErrorDb }
    
    $db = Get-Content $errorDb | ConvertFrom-Json
    $db.patterns | Add-Member -NotePropertyName $Name -NotePropertyValue @{
        error_pattern = $Pattern
        solution = $Solution
        context = $Context
        success_rate = 1.0
        occurrences = 1
        workaround = $Workaround
    } -Force
    
    $db | ConvertTo-Json -Depth 10 | Out-File $errorDb
}

# Initialize if doesn't exist
if (-not (Test-Path $errorDb)) { Initialize-ErrorDb }
