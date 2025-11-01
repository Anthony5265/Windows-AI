\
$ErrorActionPreference = 'Stop'
$root = "$env:PROGRAMDATA\Windows AI"
$dirs = @("config","data","logs","models")
foreach($d in $dirs){ $p = Join-Path $root $d; if (!(Test-Path $p)) { New-Item -Type Directory -Force $p | Out-Null } }
if (!(Test-Path "$root\config\defaults.json") -and (Test-Path ".\config\defaults.json")) {
  Copy-Item ".\config\defaults.json" "$root\config\defaults.json"
}
Write-Host "First-Run setup complete at $root"
