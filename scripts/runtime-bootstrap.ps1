\
param(
  [string]$NodeVersion = "20.16.0",
  [string]$PythonVersion = "3.11.9"
)
$ErrorActionPreference = 'Stop'
$root = "$env:ProgramFiles\Windows AI"
if (!(Test-Path $root)) { $root = "$env:ProgramFiles(x86)\Windows AI" }
if (!(Test-Path $root)) { $root = "$env:ProgramFiles\Windows AI" }
$rt = Join-Path $root "runtime"
$newNode = Join-Path $rt "node"
$newPy = Join-Path $rt "python"
New-Item -Type Directory -Force $rt, $newNode, $newPy | Out-Null

# Download Node zip
$nodeZip = Join-Path $rt "node-v$NodeVersion-win-x64.zip"
$nodeUrl = "https://nodejs.org/dist/v$NodeVersion/node-v$NodeVersion-win-x64.zip"
Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeZip
Expand-Archive -Path $nodeZip -DestinationPath $rt -Force
# Move content to runtime\node
$nodeDir = Join-Path $rt "node-v$NodeVersion-win-x64"
if (Test-Path $nodeDir) { Copy-Item -Recurse -Force "$nodeDir\*" $newNode }

# Download Python embeddable
$pyZip = Join-Path $rt "python-$PythonVersion-embed-amd64.zip"
$pyUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
Invoke-WebRequest -Uri $pyUrl -OutFile $pyZip
Expand-Archive -Path $pyZip -DestinationPath $newPy -Force

Write-Host "Runtime bootstrap complete at $rt"
