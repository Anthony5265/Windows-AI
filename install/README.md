# Windows AI Installer

Complete zero-configuration installer for Windows AI Assistant.

## Overview

The Windows AI installer is a production-grade NSIS installer that bundles:

- ✅ Python 3.11 embedded runtime
- ✅ Node.js 20 portable runtime
- ✅ All Python dependencies
- ✅ All Node.js dependencies
- ✅ Backend FastAPI service
- ✅ Electron GUI application
- ✅ System tray application
- ✅ Windows service for auto-start
- ✅ First-run wizard
- ✅ Documentation

## Features

### Zero-Configuration Deployment

Users simply run the installer - everything is configured automatically:

1. **Single-Click Install** - No manual configuration required
2. **Auto-Start on Boot** - Windows service starts backend automatically
3. **System Tray Integration** - Quick access from system tray
4. **Bundled Runtimes** - No need to install Python or Node.js separately
5. **Pre-Configured** - Sensible defaults for immediate use

### What Gets Installed

```
C:\Program Files\Windows AI\
├── python\                     # Python 3.11 embedded
├── nodejs\                     # Node.js 20 portable
├── windows_ai\                 # Backend Python code
├── apps\gui\                   # Electron GUI app
├── windows-ai-tray\            # System tray app
├── first-run-wizard\           # First-run setup wizard
├── install\                    # Installation scripts
├── docs\                       # Documentation
└── Uninstall.exe              # Uninstaller

%APPDATA%\WindowsAI\
├── config.json                # User configuration
├── chat_history.json          # Chat history
├── models\                    # Downloaded AI models
├── plugins\                   # Custom plugins
└── logs\                      # Application logs
```

### Windows Service

The installer creates a Windows service named **"WindowsAI"** that:

- Starts automatically on boot
- Runs the FastAPI backend on port 8010
- Monitors health and auto-restarts on failure
- Runs in the background (no console window)

### Registry Keys

```
HKLM\Software\Windows AI\
├── InstallDir                 # Installation directory
└── Version                    # Installed version

HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\Windows AI\
├── DisplayName
├── DisplayVersion
├── Publisher
├── UninstallString
├── DisplayIcon
└── EstimatedSize

HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\
└── WINDOWSAI_HOME            # Installation path
```

## Building the Installer

### Prerequisites

1. **Windows 10 or later** (64-bit)
2. **NSIS 3.x** - Download from https://nsis.sourceforge.io/
3. **PowerShell 5.1 or later**
4. **Python 3.11+** (for testing)
5. **Node.js 20+** (for building GUI apps)

### Quick Build

```powershell
# Basic build (assumes runtimes already downloaded)
.\install\build-installer.ps1

# Full build with runtime download
.\install\build-installer.ps1 -DownloadRuntimes

# Skip tests for faster build
.\install\build-installer.ps1 -SkipTests

# Custom version
.\install\build-installer.ps1 -Version "1.0.0"

# Full build with all options
.\install\build-installer.ps1 -DownloadRuntimes -Version "1.0.0"
```

### Build Process

The build script performs these steps:

1. **Download Runtimes** (optional)
   - Python 3.11.9 embedded (AMD64)
   - Node.js 20.11.1 portable (x64)

2. **Run Tests**
   - Python unit tests
   - Integration tests
   - Validates all components

3. **Clean Build Directory**
   - Removes old build artifacts
   - Cleans `__pycache__`, `node_modules`, etc.

4. **Build GUI Application**
   - Installs npm dependencies
   - Builds Electron app with electron-builder
   - Creates executable

5. **Build Tray Application**
   - Installs npm dependencies
   - Builds Electron app
   - Creates tray executable

6. **Build NSIS Installer**
   - Compiles installer.nsi
   - Bundles all components
   - Creates `WindowsAI-Setup-{version}.exe`

### Build Output

```
dist\
└── WindowsAI-Setup-0.5.0.exe    # Final installer (~150-200 MB)
```

## Manual Build (Advanced)

If you need to customize the build process:

### 1. Prepare Runtimes

```powershell
# Download Python embedded
$pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
Invoke-WebRequest -Uri $pythonUrl -OutFile python.zip
Expand-Archive python.zip install\runtimes\python-3.11-embed-amd64

# Download Node.js portable
$nodeUrl = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip"
Invoke-WebRequest -Uri $nodeUrl -OutFile node.zip
Expand-Archive node.zip install\runtimes\
Rename-Item install\runtimes\node-v20.11.1-win-x64 node-v20-win-x64
```

### 2. Build Applications

```powershell
# Build GUI
cd apps\gui
npm install
npm run build

# Build Tray
cd ..\..\windows-ai-tray
npm install
npm run build
```

### 3. Compile Installer

```powershell
# Using NSIS
"C:\Program Files (x86)\NSIS\makensis.exe" install\installer.nsi
```

## Installation Options

When users run the installer, they can choose:

### Required Components

- ✅ **Core Components** - Backend, GUI, basic features (required)

### Optional Components

- ☐ **Windows Service** - Auto-start on boot (recommended)
- ☐ **System Tray Application** - Quick access (recommended)
- ☐ **Desktop Shortcuts** - Desktop and Start Menu links
- ☐ **First-Run Wizard** - Initial setup guide
- ☐ **Documentation** - User guides and API docs

## Uninstallation

The installer creates a full uninstaller that:

1. Stops the Windows service
2. Removes the Windows service registration
3. Removes all files from Program Files
4. Removes shortcuts (desktop, Start Menu, startup)
5. Removes registry keys
6. **Optionally** removes user data (asks during uninstall)

### Silent Uninstall

```batch
"C:\Program Files\Windows AI\Uninstall.exe" /S
```

## Installer Size Optimization

Current installer is ~150-200 MB due to:

- Python embedded runtime: ~15 MB
- Node.js portable: ~50 MB
- Python dependencies: ~50 MB
- Node.js dependencies: ~30 MB
- Application code: ~20 MB
- NSIS compression: LZMA (best compression)

### Further Optimization

To reduce size:

1. **Strip unused Python modules**
2. **Use PyInstaller** instead of embedded Python
3. **Remove dev dependencies** from npm packages
4. **Compress with UPX** (executables)
5. **Split into base + plugins** installers

## Troubleshooting

### Build Issues

**NSIS not found**
```
Install NSIS from https://nsis.sourceforge.io/
Ensure it's in C:\Program Files (x86)\NSIS\
```

**Runtime download fails**
```powershell
# Manual download
.\install\build-installer.ps1 -DownloadRuntimes

# Or download manually and extract to install\runtimes\
```

**Build fails with "admin required"**
```powershell
# Run PowerShell as Administrator
Start-Process powershell -Verb RunAs
```

### Installation Issues

**Service fails to install**
- Run installer as Administrator
- Check Windows Event Logs for details
- Manually install: `python install\windows_service.py install`

**GUI won't start**
- Check backend is running: `http://localhost:8010/health`
- Check logs in `%APPDATA%\WindowsAI\logs\`
- Restart Windows service: `net restart WindowsAI`

**Port 8010 already in use**
- Change port in `%APPDATA%\WindowsAI\config.json`
- Restart Windows service

## Development

### Testing Installer Without Installing

```powershell
# Extract installer contents without installing
.\WindowsAI-Setup-0.5.0.exe /S /D=C:\Temp\WindowsAI-Test

# Run backend manually
cd C:\Temp\WindowsAI-Test
.\python\python.exe -m windows_ai.main

# Run GUI manually
cd apps\gui
npm start
```

### Creating Installer Variants

Edit `install\installer.nsi` to customize:

- Installation directory
- Component selections
- Registry keys
- File associations
- Post-install actions

### Signing the Installer

For production release, sign with code signing certificate:

```batch
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com WindowsAI-Setup-0.5.0.exe
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Installer

on:
  release:
    types: [created]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install NSIS
        run: choco install nsis -y

      - name: Build Installer
        run: .\install\build-installer.ps1 -DownloadRuntimes -Version "${{ github.ref_name }}"

      - name: Upload Installer
        uses: actions/upload-artifact@v3
        with:
          name: installer
          path: dist\WindowsAI-Setup-*.exe
```

## License

See LICENSE file in root directory.

## Support

For installer issues:
- GitHub Issues: https://github.com/yourorg/Windows-AI/issues
- Documentation: https://docs.windows-ai.example.com
- Email: support@windows-ai.example.com
