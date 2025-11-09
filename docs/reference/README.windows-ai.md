# Windows AI — Phase 1

## Prereqs (Windows PowerShell 7)
- Install Node.js 20 LTS
- Set environment variables:
  ```powershell
  setx OPENAI_API_KEY "sk-..."
  # optional for GitHub workflow dispatch:
  setx GITHUB_TOKEN "ghp_..."
  ```
- Open a new PowerShell window after `setx`.

## Run the agent
```powershell
cd windows-ai-agent
npm install
$env:OPENAI_API_KEY = $env:OPENAI_API_KEY  # ensure visible in this session
npm run test
npm run start -- --verbose
```

## Use the CLI without global install
```powershell
node .\windows-ai-agent\bin\wai.js ask "Hello from Windows AI"
node .\windows-ai-agent\bin\wai.js sh "Get-Process | Select-Object -First 3 Name,CPU"
```

## Optional: install auto-start (Task Scheduler)
```powershell
cd windows-ai-agent\scripts
.\install-agent.ps1
```

## CI
A workflow `.github/workflows/windows-ai-agent-ci.yml` builds and uploads a zip artifact on push and on manual dispatch.
