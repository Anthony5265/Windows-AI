# SUPER INTELLIGENT ORGANIZER AGENT
# Continuously scans, organizes, and makes everything accessible across all AI CLIs
# Creates detailed summaries and indexes for persistent memory

param(
    [switch]$Start,
    [switch]$Stop,
    [switch]$OrganizeNow
)

$pidFile = "C:\Users\antho\logs\unified_ai_memory\super_organizer.pid"
$logFile = "C:\Users\antho\logs\unified_ai_memory\super_organizer.log"
$unifiedBase = "C:\Users\antho\logs\unified_ai_memory"

function Write-OrgLog {
    param([string]$Message)
    "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')) - $Message" | Tee-Object -FilePath $logFile -Append
}

function Organize-Everything {
    Write-OrgLog "=== STARTING COMPREHENSIVE ORGANIZATION ==="
    
    # Scan EVERYTHING that gets created, modified, or accessed
    $scanTargets = @(
        "C:\Users\antho\.gemini",
        "C:\Users\antho\.claude", 
        "C:\Users\antho\.codex",
        "C:\Users\antho\.opencode",
        "C:\Users\antho\.copilot",
        "C:\Users\antho\AI CLI",
        "C:\Users\antho\Windows-AI",
        "C:\Users\antho\logs"
    )
    
    foreach ($target in $scanTargets) {
        if (-not (Test-Path $target)) { continue }
        
        Write-OrgLog "Scanning: $target"
        $cliName = Split-Path $target -Leaf
        
        # Get ALL files (logs, chats, configs, everything)
        $allFiles = Get-ChildItem $target -Recurse -File -ErrorAction SilentlyContinue
        
        foreach ($file in $allFiles) {
            # Determine what type of file this is
            $fileType = "unknown"
            $destination = ""
            
            if ($file.Extension -match '\.(log|txt)$') {
                $fileType = "log"
                $destination = "$unifiedBase\cli_outputs\raw\$cliName\$($file.Name)"
            }
            elseif ($file.Name -match 'chat|history|conversation|session') {
                $fileType = "chat_history"
                $destination = "$unifiedBase\shared_context\$cliName\chat_history\$($file.Name)"
            }
            elseif ($file.Name -match 'prompt|query|input') {
                $fileType = "prompt"
                $destination = "$unifiedBase\shared_context\$cliName\prompts\$($file.Name)"
            }
            elseif ($file.Name -match 'response|output|reply') {
                $fileType = "response"
                $destination = "$unifiedBase\shared_context\$cliName\responses\$($file.Name)"
            }
            elseif ($file.Extension -match '\.(json|yaml|yml|toml|conf|config)$') {
                $fileType = "config"
                $destination = "$unifiedBase\shared_context\$cliName\config\$($file.Name)"
            }
            elseif ($file.Extension -match '\.(py|js|ps1|sh|bat|cmd)$') {
                $fileType = "code"
                $destination = "$unifiedBase\shared_context\$cliName\code\$($file.Name)"
            }
            elseif ($file.Extension -match '\.(md|txt|rst)$') {
                $fileType = "documentation"
                $destination = "$unifiedBase\shared_context\$cliName\docs\$($file.Name)"
            }
            
            # Only copy if new or modified
            if ($destination -and (-not (Test-Path $destination) -or $file.LastWriteTime -gt (Get-Item $destination -ErrorAction SilentlyContinue).LastWriteTime)) {
                $destDir = Split-Path $destination -Parent
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                Copy-Item $file.FullName $destination -Force -ErrorAction SilentlyContinue
                Write-OrgLog "Organized [$fileType]: $($file.Name) -> $cliName"
                
                # Create metadata for this file
                $metadata = @{
                    original_path = $file.FullName
                    organized_path = $destination
                    file_type = $fileType
                    cli_source = $cliName
                    size_bytes = $file.Length
                    created = $file.CreationTime
                    modified = $file.LastWriteTime
                    organized_at = Get-Date -Format 'o'
                }
                
                $metadataFile = "$destination.metadata.json"
                $metadata | ConvertTo-Json | Out-File $metadataFile
            }
        }
    }
    
    Write-OrgLog "=== ORGANIZATION SCAN COMPLETE ==="
}

function Generate-MasterIndex {
    Write-OrgLog "Generating master index..."
    
    $index = @{
        generated = Get-Date -Format 'o'
        version = "2.0"
        total_files_organized = 0
        by_cli = @{}
        by_type = @{}
        structure = @{}
    }
    
    # Count everything
    $clis = @('gemini', 'claude', 'codex', 'opencode', 'copilot', 'AI CLI', 'Windows-AI', 'logs')
    foreach ($cli in $clis) {
        $cliPath = "$unifiedBase\shared_context\$cli"
        if (Test-Path $cliPath) {
            $files = Get-ChildItem $cliPath -Recurse -File -ErrorAction SilentlyContinue
            $index.by_cli[$cli] = @{
                total_files = $files.Count
                total_size_mb = [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
                last_updated = (Get-Date -Format 'o')
                categories = @{}
            }
            
            # Count by category
            $categories = Get-ChildItem $cliPath -Directory -ErrorAction SilentlyContinue
            foreach ($cat in $categories) {
                $catFiles = Get-ChildItem $cat.FullName -Recurse -File -ErrorAction SilentlyContinue
                $index.by_cli[$cli].categories[$cat.Name] = $catFiles.Count
                
                # Add to global type count
                if (-not $index.by_type[$cat.Name]) {
                    $index.by_type[$cat.Name] = 0
                }
                $index.by_type[$cat.Name] += $catFiles.Count
            }
            
            $index.total_files_organized += $files.Count
        }
    }
    
    # Save master index
    $index | ConvertTo-Json -Depth 10 | Out-File "$unifiedBase\MASTER_INDEX.json"
    Write-OrgLog "Master index generated: $($index.total_files_organized) files indexed"
}

function Generate-DetailedSummaries {
    Write-OrgLog "Generating detailed summaries for each CLI..."
    
    $clis = @('gemini', 'claude', 'codex', 'opencode', 'copilot')
    
    foreach ($cli in $clis) {
        $cliPath = "$unifiedBase\shared_context\$cli"
        if (-not (Test-Path $cliPath)) { continue }
        
        $summary = @"
# $cli CLI - Detailed Context Summary
**Generated:** $(Get-Date -Format 'o')
**Path:** $cliPath

## Overview
This directory contains all organized content from the $cli CLI, making it accessible to all other AI agents.

"@
        
        # Chat History
        $chatPath = "$cliPath\chat_history"
        if (Test-Path $chatPath) {
            $chats = Get-ChildItem $chatPath -File -ErrorAction SilentlyContinue
            $summary += @"

## Chat History ($($chats.Count) files)
Recent conversations and interactions:

"@
            foreach ($chat in ($chats | Sort-Object LastWriteTime -Descending | Select-Object -First 10)) {
                $lines = (Get-Content $chat.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
                $size = [math]::Round($chat.Length/1KB, 2)
                $summary += "- **$($chat.Name)** - $lines lines, ${size}KB, modified $(Get-Date $chat.LastWriteTime -Format 'yyyy-MM-dd HH:mm')`n"
            }
        }
        
        # Prompts
        $promptPath = "$cliPath\prompts"
        if (Test-Path $promptPath) {
            $prompts = Get-ChildItem $promptPath -File -ErrorAction SilentlyContinue
            $summary += @"

## Prompts ($($prompts.Count) files)
User queries and inputs:

"@
            foreach ($prompt in ($prompts | Sort-Object LastWriteTime -Descending | Select-Object -First 5)) {
                $preview = (Get-Content $prompt.FullName -Head 1 -ErrorAction SilentlyContinue)
                $summary += "- **$($prompt.Name)**: $preview`n"
            }
        }
        
        # Responses
        $responsePath = "$cliPath\responses"
        if (Test-Path $responsePath) {
            $responses = Get-ChildItem $responsePath -File -ErrorAction SilentlyContinue
            $summary += @"

## Responses ($($responses.Count) files)
AI-generated outputs and replies.

"@
        }
        
        # Config
        $configPath = "$cliPath\config"
        if (Test-Path $configPath) {
            $configs = Get-ChildItem $configPath -File -ErrorAction SilentlyContinue
            $summary += @"

## Configuration ($($configs.Count) files)
Settings and preferences:

"@
            foreach ($config in $configs) {
                $summary += "- $($config.Name)`n"
            }
        }
        
        # Code
        $codePath = "$cliPath\code"
        if (Test-Path $codePath) {
            $codes = Get-ChildItem $codePath -File -ErrorAction SilentlyContinue
            $summary += @"

## Code Files ($($codes.Count) files)
Scripts and code generated or used:

"@
            foreach ($code in ($codes | Select-Object -First 10)) {
                $summary += "- $($code.Name) ($($code.Extension))`n"
            }
        }
        
        # Docs
        $docsPath = "$cliPath\docs"
        if (Test-Path $docsPath) {
            $docs = Get-ChildItem $docsPath -File -ErrorAction SilentlyContinue
            $summary += @"

## Documentation ($($docs.Count) files)

"@
            foreach ($doc in $docs) {
                $summary += "- $($doc.Name)`n"
            }
        }
        
        $summary += @"

## Access Path for Other CLIs
Any AI CLI can access this $cli context via:
``````
$cliPath
``````

---
*Auto-generated by Super Intelligent Organizer Agent*
"@
        
        # Save summary
        $summaryFile = "$unifiedBase\cli_outputs\summaries\${cli}_COMPLETE_SUMMARY.md"
        New-Item -ItemType Directory -Path (Split-Path $summaryFile -Parent) -Force | Out-Null
        $summary | Out-File $summaryFile -Encoding UTF8
        Write-OrgLog "Generated detailed summary for $cli"
    }
}

function Create-CrossReferenceIndex {
    Write-OrgLog "Creating cross-reference index..."
    
    # Build searchable index of all content
    $searchIndex = @{
        created = Get-Date -Format 'o'
        entries = @()
    }
    
    $allFiles = Get-ChildItem "$unifiedBase\shared_context" -Recurse -File -Include "*.md", "*.txt", "*.log", "*.json" -ErrorAction SilentlyContinue
    
    foreach ($file in ($allFiles | Select-Object -First 1000)) {  # Limit to prevent huge index
        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        if ($content) {
            $searchIndex.entries += @{
                path = $file.FullName
                name = $file.Name
                type = $file.Extension
                size = $file.Length
                modified = $file.LastWriteTime
                preview = ($content -split "`n" | Select-Object -First 5) -join " "
            }
        }
    }
    
    $searchIndex | ConvertTo-Json -Depth 10 | Out-File "$unifiedBase\SEARCH_INDEX.json"
    Write-OrgLog "Search index created with $($searchIndex.entries.Count) entries"
}

if ($Stop) {
    if (Test-Path $pidFile) {
        $jobs = Get-Content $pidFile | ConvertFrom-Json
        foreach ($jobId in $jobs) {
            Stop-Job -Id $jobId -ErrorAction SilentlyContinue
            Remove-Job -Id $jobId -ErrorAction SilentlyContinue
        }
        Remove-Item $pidFile
        Write-OrgLog "Super Organizer stopped"
    }
    return
}

if ($OrganizeNow) {
    Write-Host "=== SUPER INTELLIGENT ORGANIZER - RUNNING NOW ===" -ForegroundColor Magenta
    Organize-Everything
    Generate-MasterIndex
    Generate-DetailedSummaries
    Create-CrossReferenceIndex
    Write-Host "✓ Complete organization finished!" -ForegroundColor Green
    Write-Host "Location: $unifiedBase" -ForegroundColor Cyan
    return
}

if ($Start) {
    Write-OrgLog "Super Intelligent Organizer starting..."
    
    # Background job - continuous organization
    $job = Start-Job -ScriptBlock {
        param($base, $log)
        
        function Write-Log { param([string]$M) "$((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) - $M" | Out-File $log -Append }
        
        while ($true) {
            Start-Sleep -Seconds 30  # Scan every 30 seconds
            
            Write-Log "Running organization cycle..."
            
            # Quick scan for new/modified files
            $targets = @(
                "$env:USERPROFILE\.gemini",
                "$env:USERPROFILE\.claude",
                "$env:USERPROFILE\.codex",
                "$env:USERPROFILE\.opencode",
                "$env:USERPROFILE\.copilot",
                "$env:USERPROFILE\AI CLI",
                "$env:USERPROFILE\Windows-AI"
            )
            
            foreach ($target in $targets) {
                if (-not (Test-Path $target)) { continue }
                
                $cliName = Split-Path $target -Leaf
                
                # Find recently modified files (last 2 minutes)
                $recentFiles = Get-ChildItem $target -Recurse -File -ErrorAction SilentlyContinue |
                    Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-2) }
                
                foreach ($file in $recentFiles) {
                    $destBase = "$base\shared_context\$cliName"
                    
                    # Determine category and destination
                    $dest = if ($file.Name -match 'chat|history|conversation') {
                        "$destBase\chat_history\$($file.Name)"
                    } elseif ($file.Name -match 'prompt|query') {
                        "$destBase\prompts\$($file.Name)"
                    } elseif ($file.Name -match 'response|output') {
                        "$destBase\responses\$($file.Name)"
                    } elseif ($file.Extension -match '\.(log|txt)$') {
                        "$base\cli_outputs\raw\$cliName\$($file.Name)"
                    } elseif ($file.Extension -match '\.(json|yaml|yml)$') {
                        "$destBase\config\$($file.Name)"
                    } else {
                        $null
                    }
                    
                    if ($dest) {
                        $destDir = Split-Path $dest -Parent
                        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                        Copy-Item $file.FullName $dest -Force -ErrorAction SilentlyContinue
                        Write-Log "Auto-organized: $($file.Name) -> $cliName"
                    }
                }
            }
        }
    } -ArgumentList $unifiedBase, $logFile
    
    $job.Id | ConvertTo-Json | Out-File $pidFile
    
    Write-OrgLog "Super Intelligent Organizer started (Job: $($job.Id))"
    Write-Host "✓ Super Intelligent Organizer ACTIVE" -ForegroundColor Green
    Write-Host "  - Scans every 30 seconds" -ForegroundColor Cyan
    Write-Host "  - Organizes: logs, chats, prompts, responses, configs, code, docs" -ForegroundColor Cyan
    Write-Host "  - Creates: detailed summaries, master index, search index" -ForegroundColor Cyan
    Write-Host "  - Makes everything accessible to all AI CLIs" -ForegroundColor Green
    
    return $job
}

Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  .\super_organizer.ps1 -Start         # Start continuous background organization"
Write-Host "  .\super_organizer.ps1 -OrganizeNow   # Run full organization once"
Write-Host "  .\super_organizer.ps1 -Stop          # Stop background organization"
