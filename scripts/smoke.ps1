$ErrorActionPreference="Stop"
try {
  $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:15777/health -TimeoutSec 5
  if ($r.Content -notmatch '"'"'ok'"'"'\s*:\s*true') { throw "Health not ok" }
  Write-Host "OK"
} catch { Write-Error $_; exit 1 }
