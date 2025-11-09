# CLI Syntax Reference for Agents

## CORRECT CLI Usage

### OpenCode
```powershell
# ✓ CORRECT - Use --input with file
$prompt | Out-File temp.txt
opencode --model grok-2-1212 --input temp.txt

# ✓ CORRECT - Use stdin
echo "prompt" | opencode --model grok-2-1212

# ❌ WRONG - Don't pass raw multi-line strings
opencode --model grok-2-1212 --prompt "multi
line
text"
```

### Gemini
```powershell
# ✓ CORRECT - Model flag + stdin
echo "prompt" | gemini -m gemini-2.0-flash-exp

# ❌ WRONG - Don't use chat subcommand with conflicting flags
gemini chat --yolo --approval-mode=yolo "prompt"

# ❌ WRONG - Conflicting approval modes
gemini --yolo --approval-mode=yolo
```

### Codex
```powershell
# ✓ CORRECT - Model flag + stdin
echo "prompt" | codex -m gpt-4

# ❌ WRONG - Don't pass multi-line literal strings
codex chat "You are Agent_111...
MISSION: ..."

# ❌ WRONG - Missing proper escaping
codex "text with `n newlines"
```

### Claude
```powershell
# ✓ CORRECT - Stdin only, no model flag
echo "prompt" | claude

# ❌ WRONG - Don't use chat subcommand
claude chat

# ❌ WRONG - No model flags
claude --model claude-3-5-sonnet
```

### Copilot
```powershell
# ✓ CORRECT - Use suggest with target type
echo "prompt" | gh copilot suggest -t shell

# ✓ CORRECT - Explain mode
gh copilot explain "command"

# ❌ WRONG - Raw prompts without pipe
gh copilot suggest "build a feature"
```

### Ollama
```powershell
# ✓ CORRECT - Run with model name
echo "prompt" | ollama run qwen2.5-coder:1.5b

# ✓ CORRECT - Specify format
ollama run llama2 --format json

# ❌ WRONG - Don't use chat for scripting
ollama chat llama2 < prompt.txt
```

## Common Pitfalls

### 1. Multi-line Prompts
```powershell
# ❌ WRONG
$prompt = @"
You are an agent.
Do this task.
"@
codex "$prompt"  # Breaks on newlines

# ✓ CORRECT
$prompt = @"
You are an agent.
Do this task.
"@
$prompt | codex -m gpt-4
```

### 2. Error Handling
```powershell
# ❌ WRONG - No error capture
opencode --model grok-2 "prompt" > output.txt

# ✓ CORRECT - Capture errors
opencode --model grok-2 "prompt" 2>&1 | Tee-Object output.txt
if($LASTEXITCODE -ne 0) {
    # Handle error
}
```

### 3. Empty Outputs
```powershell
# ❌ WRONG - No validation
$result = echo "prompt" | claude
$result | Out-File output.txt

# ✓ CORRECT - Validate before saving
$result = echo "prompt" | claude 2>&1
if($result -and $result.Length -gt 0) {
    $result | Out-File output.txt
} else {
    Write-Error "CLI returned empty output"
}
```

### 4. Timeout Issues
```powershell
# ❌ WRONG - Synchronous, can hang
$result = echo "prompt" | some-slow-cli

# ✓ CORRECT - Use job with timeout
$job = Start-Job { echo "prompt" | some-slow-cli }
$result = Wait-Job $job -Timeout 60
if($result) {
    Receive-Job $job
} else {
    Stop-Job $job
}
```

## Agent Template
```powershell
function Invoke-AgentTask {
    param(
        [string]$CLI,
        [string]$Prompt,
        [string]$OutputFile
    )
    
    try {
        $result = switch($CLI) {
            'opencode' {
                $temp = New-TemporaryFile
                $Prompt | Out-File $temp -Encoding utf8
                & opencode --model grok-2-1212 --input $temp.FullName 2>&1
                Remove-Item $temp -Force -ErrorAction SilentlyContinue
            }
            'gemini' {
                $Prompt | & gemini -m gemini-2.0-flash-exp 2>&1
            }
            'codex' {
                $Prompt | & codex -m gpt-4 2>&1
            }
            'claude' {
                $Prompt | & claude 2>&1
            }
            'copilot' {
                $Prompt | & gh copilot suggest -t shell 2>&1
            }
            default {
                throw "Unknown CLI: $CLI"
            }
        }
        
        if($LASTEXITCODE -eq 0 -and $result) {
            $result | Out-File $OutputFile -Force
            return @{ success = $true; output = $result }
        } else {
            return @{ success = $false; error = "Exit code: $LASTEXITCODE" }
        }
        
    } catch {
        return @{ success = $false; error = $_.Exception.Message }
    }
}
```

## Testing CLIs
```powershell
# Test each CLI before spawning agents
$testPrompt = "Echo 'hello world'"

@('opencode', 'gemini', 'codex', 'claude', 'copilot') | ForEach-Object {
    Write-Host "Testing $_..." -ForegroundColor Cyan
    
    $result = Invoke-AgentTask -CLI $_ -Prompt $testPrompt -OutputFile "test_$_.txt"
    
    if($result.success) {
        Write-Host "  ✓ $_ works" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $_ failed: $($result.error)" -ForegroundColor Red
    }
}
```
