param(
  [string]$TaskName = "WindowsAIAgent",
  [string]$Listen   = "127.0.0.1:15777"
)
$here     = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentDir = Split-Path -Parent $here
$node     = (Get-Command node).Source
$script   = Join-Path $agentDir "bin\wai-server.js"

Write-Host "Register task $TaskName at $agentDir" -ForegroundColor Cyan
try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue } catch {}
$action = New-ScheduledTaskAction -Execute $node -Argument "`"$script`" --listen=$Listen" -WorkingDirectory $agentDir
$trig   = New-ScheduledTaskTrigger -AtLogOn
$princ  = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Highest -LogonType Interactive
$task   = New-ScheduledTask -Action $action -Trigger $trig -Principal $princ
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "Task $TaskName started." -ForegroundColor Green

