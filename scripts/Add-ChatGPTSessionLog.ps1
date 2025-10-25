Param(
  [Parameter(Mandatory=$true)][string]$Title,
  [string]$Message,
  [string]$MessagePath,
  [string]$Owner = "Anthony5265",
  [string]$Repo  = "Windows-AI",
  [string]$Branch
)

function Get-AutoContext {
  param([string]$RepoRoot)
  $mk=@()
  $branch = (git rev-parse --abbrev-ref HEAD 2>$null)
  $status = (git status -s 2>$null)

  $agent = Join-Path $RepoRoot 'windows-ai-agent\logs\agent-latest.log'
  $tray  = Join-Path $RepoRoot 'windows-ai-tray\tray-task.log'
  $watch = Join-Path $RepoRoot 'windows-ai-tray\watchdog.log'

  $sch1 = (schtasks /Query /TN WindowsAIAgent    /FO LIST 2>$null | Out-String)
  $sch2 = (schtasks /Query /TN WindowsAITray     /FO LIST 2>$null | Out-String)
  $sch3 = (schtasks /Query /TN WindowsAIWatchdog /FO LIST 2>$null | Out-String)

  $mk += "# Context",""
  $mk += "- Repo: $Owner/$Repo"
  $mk += "- Branch: $branch"
  $mk += "- Date: $(Get-Date -Format s)",""
  $mk += "## Git status","```"
  if ($status) { $mk += $status }
  $mk += "```"

  if (Test-Path $agent) { $mk += "## agent-latest.log (tail 60)","```"; $mk += (Get-Content $agent -Tail 60); $mk += "```" }
  if (Test-Path $tray)  { $mk += "## tray-task.log (tail 60)","```";  $mk += (Get-Content $tray  -Tail 60); $mk += "```" }
  if (Test-Path $watch) { $mk += "## watchdog.log (tail 60)","```";   $mk += (Get-Content $watch -Tail 60); $mk += "```" }

  $mk += "## Scheduled Tasks","```"
  if ($sch1){$mk += $sch1.TrimEnd()}
  if ($sch2){$mk += $sch2.TrimEnd()}
  if ($sch3){$mk += $sch3.TrimEnd()}
  $mk += "```"
  return ($mk -join "`r`n")
}

# choose branch: current if not provided
if (-not $Branch -or $Branch.Trim() -eq '') { $Branch = (git rev-parse --abbrev-ref HEAD).Trim() }

# message
if (-not $Message -and $MessagePath) { $Message = Get-Content -Raw -LiteralPath $MessagePath }
if (-not $Message) { $Message = "Session log (auto-generated)" }

$repoRoot = (Resolve-Path .).Path
$ctx = Get-AutoContext -RepoRoot $repoRoot
$payload = $Message + "`r`n---`r`n" + $ctx
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($payload))

$gh = (Get-Command gh -EA SilentlyContinue)?.Source
if (-not $gh) { throw "GitHub CLI 'gh' not found in PATH." }

$path = "repos/$Owner/$Repo/actions/workflows/chatgpt-session-log.yml/dispatches"
gh api -X POST $path -F "ref=$Branch" -F "inputs[title]=$Title" -F "inputs[content_b64]=$b64" | Out-Null
Write-Host "✅ Dispatched '$Title' to chatgpt-session-log on branch $Branch."
