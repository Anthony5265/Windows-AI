$ErrorActionPreference="Stop"
$response = Invoke-RestMethod http://127.0.0.1:15777/health -ErrorAction Stop
if (-not $response.ok) { Write-Error "Agent health check failed" }
