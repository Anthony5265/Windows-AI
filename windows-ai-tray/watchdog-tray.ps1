param(
  [string]$TrayTask="WindowsAITray",
  [string]$AgentTask="WindowsAIAgent",
  [string]$AgentHealth="http://127.0.0.1:15777/health",
  [int]$TimeoutMs=1500
)
$log = Join-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) "watchdog.log"
function Write-Log($m){$ts=[DateTime]::UtcNow.ToString("o"); Add-Content $log "[$ts] $m"}

# Detect tray electron tied to this repo
$trayDir = Split-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) -Parent
$procs = Get-CimInstance Win32_Process -Filter "Name='electron.exe'" |
  Where-Object { $_.CommandLine -match [regex]::Escape($trayDir) }

# Check agent health
$agentOk = $false
try{
  $c = New-Object Net.Http.HttpClient
  $c.Timeout = [TimeSpan]::FromMilliseconds($TimeoutMs)
  $r = $c.GetAsync($AgentHealth).GetAwaiter().GetResult()
  if ($r -and $r.IsSuccessStatusCode){ $agentOk = $true }
}catch{}

if (-not $agentOk){
  Write-Log "agent:down -> restart $AgentTask"
  schtasks /Run /TN "$AgentTask" | Out-Null
}else{
  Write-Log "agent:ok"
}

if (-not $procs){
  Write-Log "tray:down -> restart $TrayTask"
  schtasks /Run /TN "$TrayTask" | Out-Null
}else{
  Write-Log "tray:ok pid(s): $(@($procs.ProcessId) -join ',')"
}
