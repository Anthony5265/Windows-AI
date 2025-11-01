param(
  [string]$Url = "http://127.0.0.1:15777/health",
  [string]$AgentTask = "WindowsAIAgent",
  [int]$TimeoutMs = 1500
)
try {
  $c = New-Object Net.Http.HttpClient
  $c.Timeout = [TimeSpan]::FromMilliseconds($TimeoutMs)
  $r = $c.GetAsync($Url).GetAwaiter().GetResult()
  if (-not $r.IsSuccessStatusCode) { throw "HTTP $($r.StatusCode)" }
  Write-Output "ok"
} catch {
  schtasks /Run /TN "$AgentTask" | Out-Null
  Start-Sleep -Milliseconds 500
  Write-Output "restarted"
}
