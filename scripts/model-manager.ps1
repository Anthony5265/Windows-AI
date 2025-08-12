\
param([ValidateSet('ollama','lmstudio')][string]$Host='ollama')
$ErrorActionPreference = 'Stop'
if ($Host -eq 'ollama') {
  winget install -e --id Ollama.Ollama -h --accept-source-agreements --accept-package-agreements
} else {
  winget install -e --id LMStudio.LMStudio -h --accept-source-agreements --accept-package-agreements
}
Write-Host "Installed $Host (if supported)."
