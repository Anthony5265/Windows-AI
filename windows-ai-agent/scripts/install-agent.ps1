param(
  [string]$NodeExe = "C:\Program Files\nodejs\node.exe"
)

$RepoRoot = (Get-Item -LiteralPath "$PSScriptRoot\..").FullName
$Agent    = Join-Path $RepoRoot "src\agent.js"

if (!(Test-Path $NodeExe)) {
  Write-Error "Node not found at $NodeExe. Install Node 20 LTS."
  exit 1
}

$Action   = New-ScheduledTaskAction -Execute $NodeExe -Argument "`"$Agent`" --verbose"
$Trigger  = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$Task     = New-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings

Register-ScheduledTask -TaskName "WindowsAIAgent" -InputObject $Task -Force | Out-Null
Write-Host "Scheduled task 'WindowsAIAgent' installed. It will run at logon."
