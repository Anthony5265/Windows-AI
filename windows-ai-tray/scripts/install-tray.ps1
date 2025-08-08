param([string]$TaskName="WindowsAITray")
$trayScripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$trayRoot    = Split-Path -Parent $trayScripts
$cmd = Join-Path $trayRoot "run-tray.cmd"
try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue } catch {}
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$cmd`""
$trig   = New-ScheduledTaskTrigger -AtLogOn
$princ  = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Highest -LogonType Interactive
$task   = New-ScheduledTask -Action $action -Trigger $trig -Principal $princ
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "Tray task $TaskName installed and started."
