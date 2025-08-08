param([string]$TaskName="WindowsAITray")
$trayDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cmd = Join-Path $trayDir "run-tray.cmd"
try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue } catch {}
# Use cmd.exe so working dir is correct
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$cmd`""
$trig   = New-ScheduledTaskTrigger -AtLogOn
$princ  = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Highest -LogonType Interactive
$task   = New-ScheduledTask -Action $action -Trigger $trig -Principal $princ
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "Tray task $TaskName installed and started."
