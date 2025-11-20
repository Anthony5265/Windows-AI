$ErrorActionPreference="Stop"
try {
    $response = Invoke-RestMethod http://127.0.0.1:15777/health
    if (-not $response.ok) {
        throw "Agent health check failed"
    }
    Write-Host "OK"
}
catch {
    Write-Error $_;
    exit 1
}