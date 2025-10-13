\
param([ValidateSet('ollama','lmstudio')][string]$Host='ollama')
$ErrorActionPreference = 'Stop'
if ($Host -eq 'ollama') {
  winget install -e --id Ollama.Ollama -h --accept-source-agreements --accept-package-agreements
  try {
    ollama pull phi3:mini
    Write-Host 'phi3:mini model downloaded.'
  } catch {
    Write-Host 'Failed to download phi3:mini. Visit https://ollama.com/library/phi3 for manual instructions.'
  }
} else {
  winget install -e --id LMStudio.LMStudio -h --accept-source-agreements --accept-package-agreements
  try {
    lms download phi3:mini
    Write-Host 'phi3:mini model downloaded.'
  } catch {
    Write-Host 'Failed to download phi3:mini. See https://lmstudio.ai/docs for guidance.'
  }
}
Write-Host "Installed $Host (if supported)."
