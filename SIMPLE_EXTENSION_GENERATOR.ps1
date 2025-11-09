# SIMPLIFIED EXTENSION GENERATOR - Use Copilot CLI only
# This script uses ONLY gh copilot since it's reliable and you're already running it

param(
    [int]$TargetCount = 652,  # Remaining extensions
    [string]$OutputDir = "C:\Users\antho\Windows-AI\extensions_final"
)

$BaseDir = "C:\Users\antho\Windows-AI"
$LogDir = "C:\Users\antho\logs\unified_ai_memory"
$RoadmapFile = "$BaseDir\ULTIMATE_EXTENSION_ROADMAP.md"

Write-Host "=== SIMPLIFIED EXTENSION BUILDER ===" -ForegroundColor Magenta
Write-Host "Target: Generate $TargetCount extensions using GitHub Copilot" -ForegroundColor Cyan

# Create output directory
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Load uncompleted extensions
if(-not (Test-Path $RoadmapFile)) {
    Write-Error "Roadmap not found: $RoadmapFile"
    exit 1
}

$roadmap = Get-Content $RoadmapFile -Raw
$unchecked = [regex]::Matches($roadmap, '- \[ \] (.+)') | ForEach-Object { $_.Groups[1].Value.Trim() }

if($unchecked.Count -eq 0) {
    Write-Host "✓ All extensions already completed!" -ForegroundColor Green
    exit 0
}

Write-Host "Found $($unchecked.Count) uncompleted extensions`n" -ForegroundColor Yellow

# Take only what we need
$extensionsToGenerate = $unchecked | Select-Object -First $TargetCount

$completed = 0
$failed = 0
$startTime = Get-Date

Write-Host "Generating extensions..." -ForegroundColor Cyan

foreach($ext in $extensionsToGenerate) {
    $safeName = $ext -replace '[^a-zA-Z0-9_-]', '_'
    $extDir = Join-Path $OutputDir $safeName
    $codeFile = Join-Path $extDir "extension.json"
    
    Write-Host "  [$($completed + $failed + 1)/$TargetCount] $ext..." -NoNewline
    
    $prompt = @"
Create a VSCode extension for: $ext

Output ONLY a valid JSON object with this structure:
{
  "name": "extension-name",
  "displayName": "Extension Display Name",
  "description": "What the extension does",
  "version": "1.0.0",
  "publisher": "windows-ai",
  "main": "./out/extension.js",
  "activationEvents": ["onCommand:extension.command"],
  "contributes": {
    "commands": [{
      "command": "extension.command",
      "title": "Command Title"
    }]
  },
  "implementation": "// TypeScript implementation here"
}

Make it complete and functional. JSON only, no markdown.
"@

    try {
        # Use gh copilot - most reliable
        $result = echo $prompt | gh copilot suggest -t shell 2>&1
        
        if($LASTEXITCODE -eq 0 -and $result) {
            New-Item -ItemType Directory -Force -Path $extDir | Out-Null
            $result | Out-File $codeFile -Force -Encoding utf8
            
            $completed++
            Write-Host " ✓" -ForegroundColor Green
        } else {
            $failed++
            Write-Host " ✗ (exit $LASTEXITCODE)" -ForegroundColor Red
        }
    } catch {
        $failed++
        Write-Host " ✗ ($_)" -ForegroundColor Red
    }
    
    # Progress every 50
    if(($completed + $failed) % 50 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $rate = ($completed + $failed) / $elapsed.TotalMinutes
        $remaining = $TargetCount - ($completed + $failed)
        $eta = [math]::Round($remaining / $rate)
        
        Write-Host "`n  Progress: $completed completed, $failed failed | Rate: $([math]::Round($rate, 1))/min | ETA: $eta min`n" -ForegroundColor Cyan
    }
}

$totalTime = (Get-Date) - $startTime

Write-Host "`n=== COMPLETE ===" -ForegroundColor Green
Write-Host "Completed: $completed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Total time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes" -ForegroundColor Cyan
Write-Host "Output directory: $OutputDir" -ForegroundColor Cyan

# Update progress
$newTotal = 2496 + $completed
$newPercent = [math]::Round(($newTotal / 3148) * 100, 2)

@{
    last_updated = Get-Date -Format "o"
    tasks = @{
        "Windows-AI Extensions" = @{
            status = if($newTotal -ge 3148) { "completed" } else { "in_progress" }
            percent_complete = $newPercent
            metadata = @{
                extensions_created = $newTotal
                target = 3148
                last_session = Get-Date -Format "o"
            }
        }
    }
} | ConvertTo-Json -Depth 5 | Out-File "$LogDir\UNIFIED_PROGRESS.json" -Force

Write-Host "`nProgress updated: $newTotal / 3148 ($newPercent%)" -ForegroundColor Green
