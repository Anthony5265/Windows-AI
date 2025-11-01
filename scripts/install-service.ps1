Param(
  [string]$NodePath = "C:\Program Files\nodejs\node.exe",
  [string]$AgentDir = ".\windows-ai-agent"
)
# Creates a Task Scheduler task to start the agent at logon
$Script = "$AgentDir\src\agent.js"
if (!(Test-Path $NodePath)) { Write-Error "Node not found at $NodePath"; exit 1 }
if (!(Test-Path $Script)) { Write-Error "Agent not found at $Script"; exit 1 }

$Action = New-ScheduledTaskAction -Execute $NodePath -Argument $Script
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries)

Register-ScheduledTask -TaskName "WindowsAI-Agent" -InputObject $Task -Force
Write-Host "Installed Task Scheduler job 'WindowsAI-Agent' to start at logon."
