# Windows AI All-In-One Installer Architecture

## Design Goals

1. **Single .exe download** - User downloads one file
2. **Zero prerequisites** - Bundles Python, Node.js (if needed), all dependencies
3. **One-click install** - Minimal user interaction
4. **Auto-starts services** - Backend, tray, GUI launch automatically
5. **Deep Windows integration** - Service mode, shortcuts, context menus
6. **Includes starter models** - Downloads small LLM on first run
7. **Self-contained** - Everything needed in one package

## Installer Architecture

### Technology Stack

- **NSIS (Primary)** - Advanced Windows installer with custom pages
- **PyInstaller** - Bundle Python + backend into standalone .exe
- **electron-builder** - GUI packaging (already working)
- **NSSM** - Windows service wrapper
- **WinPython** - Alternative: embedded Python distribution

### Package Contents

```
WindowsAI-Setup-0.2.0.exe  (Installer)
  │
  ├── embedded-python/              # Embedded Python 3.11
  │   ├── python.exe
  │   ├── pythonw.exe
  │   ├── Lib/
  │   ├── DLLs/
  │   └── Scripts/
  │
  ├── backend/                       # Bundled backend service
  │   ├── windows_ai.exe             # PyInstaller bundle
  │   ├── windows_ai/                # Python modules
  │   │   ├── main.py
  │   │   ├── plugins/
  │   │   ├── iot/
  │   │   ├── mesh/
  │   │   └── ...
  │   ├── requirements.txt
  │   └── config/
  │
  ├── gui/                           # Electron GUI
  │   ├── WindowsAI.exe
  │   ├── resources/
  │   └── locales/
  │
  ├── tray/                          # System tray app
  │   ├── WindowsAI-Tray.exe
  │   └── resources/
  │
  ├── services/                      # Windows services
  │   ├── nssm.exe                   # Service manager
  │   └── windows-ai-service.xml     # Service config
  │
  ├── models/                        # Starter models (optional download)
  │   └── download_starter.bat
  │
  ├── scripts/                       # Utility scripts
  │   ├── start-all.bat
  │   ├── start-backend.bat
  │   ├── start-gui.bat
  │   ├── start-tray.bat
  │   └── configure-api-keys.bat
  │
  └── installer/                     # Installer components
      ├── vcredist_x64.exe           # Visual C++ Runtime
      └── setup-wizard.exe
```

## Installation Process

### Step 1: Pre-Installation Checks

1. Check Windows version (Windows 10+)
2. Check architecture (x64/x86)
3. Check available disk space (2GB minimum)
4. Detect Visual C++ Runtime
5. Detect existing installation

### Step 2: Installation Wizard

**Page 1: Welcome**
- Introduction to Windows AI
- License agreement

**Page 2: Installation Type**
- [ ] Quick Install (Recommended) - Auto-detects everything
- [ ] Custom Install - Choose components
- [ ] Portable Install - No system integration

**Page 3: Component Selection** (Custom only)
- [x] Backend Service (Required)
- [x] Desktop GUI (Recommended)
- [x] System Tray (Recommended)
- [ ] Windows Service Mode (Run in background)
- [ ] Download Starter Model (Phi-3-mini, 2.3GB)
- [ ] Desktop Shortcuts
- [ ] Start Menu Integration
- [ ] Run on Windows Startup

**Page 4: Configuration**
- API Keys (Optional):
  - OpenAI API Key: [____________]
  - Google/Gemini API Key: [____________]
  - Anthropic API Key: [____________]
  - [ ] Use local models only (Ollama)
- Backend Port: [8010]
- [ ] Open firewall ports automatically

**Page 5: Installation**
- Progress bar with detailed steps
- Extracting files...
- Installing Python runtime...
- Installing dependencies...
- Configuring services...
- Creating shortcuts...
- Setting up firewall rules...

**Page 6: First Run Setup**
- [ ] Launch Windows AI now
- [ ] Download starter model (Phi-3-mini)
- [ ] Show quick start guide
- [ ] Configure autostart

### Step 3: Post-Installation

1. Create desktop shortcuts
2. Create Start Menu folder
3. Register Windows service (if selected)
4. Create firewall rules
5. Set registry keys for context menu integration
6. Launch first-run configuration

## PyInstaller Backend Bundle

### Build Script: `build_backend_bundle.py`

```python
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Collect all Python modules
backend_modules = [
    'windows_ai.main',
    'windows_ai.plugins',
    'windows_ai.iot',
    'windows_ai.mesh',
    'windows_ai.folder_watcher',
    'windows_ai.scheduler',
    # ... all modules
]

# Collect all data files
data_files = [
    ('windows_ai/plugins/builtin', 'windows_ai/plugins/builtin'),
    ('config', 'config'),
]

a = Analysis(
    ['windows_ai/main.py'],
    pathex=[],
    binaries=[],
    datas=data_files,
    hiddenimports=backend_modules + [
        'uvicorn',
        'fastapi',
        'litellm',
        'pydantic',
        'httpx',
        # ... all dependencies
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='windows-ai-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for backend
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='apps/gui/build/icon.ico',
)
```

## NSIS Installer Script

### Main Script: `installer/windows_ai_installer.nsi`

```nsis
; Windows AI All-In-One Installer
; Copyright (c) 2025 Windows AI Contributors

!define PRODUCT_NAME "Windows AI"
!define PRODUCT_VERSION "0.2.0"
!define PRODUCT_PUBLISHER "Windows AI Contributors"
!define PRODUCT_WEB_SITE "https://github.com/Anthony5265/Windows-AI"

!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"

; Installer settings
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "WindowsAI-Setup-${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES64\Windows AI"
InstallDirRegKey HKLM "Software\WindowsAI" "InstallDir"
RequestExecutionLevel admin

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "apps\gui\build\icon.ico"
!define MUI_UNICON "apps\gui\build\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer\assets\wizard.bmp"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
Page custom ComponentsPage ComponentsLeave
!insertmacro MUI_PAGE_DIRECTORY
Page custom ConfigPage ConfigLeave
!insertmacro MUI_PAGE_INSTFILES
Page custom FinishPage FinishLeave

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Variables
Var InstallService
Var DownloadModel
Var OpenAIKey
Var GoogleKey
Var AnthropicKey
Var BackendPort
Var AutoStart
Var CreateShortcuts

; Main installation section
Section "Core" SEC01
  SetOutPath "$INSTDIR"

  ; Copy all files
  File /r "dist\backend\*.*"
  File /r "dist\gui\*.*"
  File /r "dist\tray\*.*"
  File /r "dist\scripts\*.*"
  File /r "config\*.*"

  ; Create data directory
  CreateDirectory "$APPDATA\Windows-AI"

  ; Write registry keys
  WriteRegStr HKLM "Software\WindowsAI" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\WindowsAI" "Version" "${PRODUCT_VERSION}"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Add to Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsAI" \
    "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsAI" \
    "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsAI" \
    "DisplayIcon" "$INSTDIR\gui\WindowsAI.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsAI" \
    "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsAI" \
    "DisplayVersion" "${PRODUCT_VERSION}"

SectionEnd

Section "Shortcuts" SEC02
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\Windows AI"
  CreateShortCut "$SMPROGRAMS\Windows AI\Windows AI.lnk" "$INSTDIR\gui\WindowsAI.exe"
  CreateShortCut "$SMPROGRAMS\Windows AI\Start Backend.lnk" "$INSTDIR\scripts\start-backend.bat"
  CreateShortCut "$SMPROGRAMS\Windows AI\Configure.lnk" "$INSTDIR\scripts\configure.bat"
  CreateShortCut "$SMPROGRAMS\Windows AI\Uninstall.lnk" "$INSTDIR\uninstall.exe"

  ; Create desktop shortcut
  CreateShortCut "$DESKTOP\Windows AI.lnk" "$INSTDIR\gui\WindowsAI.exe"
SectionEnd

Section "Windows Service" SEC03
  ; Install as Windows service using NSSM
  ExecWait '"$INSTDIR\services\nssm.exe" install "Windows AI Backend" "$INSTDIR\backend\windows-ai-backend.exe"'
  ExecWait '"$INSTDIR\services\nssm.exe" set "Windows AI Backend" AppDirectory "$INSTDIR\backend"'
  ExecWait '"$INSTDIR\services\nssm.exe" set "Windows AI Backend" DisplayName "Windows AI Backend Service"'
  ExecWait '"$INSTDIR\services\nssm.exe" set "Windows AI Backend" Description "Windows AI FastAPI Backend Service"'
  ExecWait '"$INSTDIR\services\nssm.exe" set "Windows AI Backend" Start SERVICE_AUTO_START"'

  ; Start the service
  ExecWait '"$INSTDIR\services\nssm.exe" start "Windows AI Backend"'
SectionEnd

Section "Firewall Rules" SEC04
  ; Add firewall rule for backend
  ExecWait 'netsh advfirewall firewall add rule name="Windows AI Backend" dir=in action=allow protocol=TCP localport=$BackendPort'
SectionEnd

Section "API Keys Configuration" SEC05
  ; Write API keys to environment (user level)
  ${If} $OpenAIKey != ""
    WriteRegStr HKCU "Environment" "OPENAI_API_KEY" "$OpenAIKey"
  ${EndIf}
  ${If} $GoogleKey != ""
    WriteRegStr HKCU "Environment" "GOOGLE_API_KEY" "$GoogleKey"
  ${EndIf}
  ${If} $AnthropicKey != ""
    WriteRegStr HKCU "Environment" "ANTHROPIC_API_KEY" "$AnthropicKey"
  ${EndIf}

  ; Broadcast environment change
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000
SectionEnd

Section "Autostart" SEC06
  ; Add to Windows startup
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" \
    "WindowsAI" "$INSTDIR\scripts\start-all.bat"
SectionEnd

; Uninstaller
Section "Uninstall"
  ; Stop and remove service if installed
  ExecWait '"$INSTDIR\services\nssm.exe" stop "Windows AI Backend"'
  ExecWait '"$INSTDIR\services\nssm.exe" remove "Windows AI Backend" confirm'

  ; Remove firewall rule
  ExecWait 'netsh advfirewall firewall delete rule name="Windows AI Backend"'

  ; Remove from autostart
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "WindowsAI"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\Windows AI\*.*"
  RMDir "$SMPROGRAMS\Windows AI"
  Delete "$DESKTOP\Windows AI.lnk"

  ; Remove files
  RMDir /r "$INSTDIR"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\WindowsAI"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsAI"

  ; Ask about user data
  MessageBox MB_YESNO "Remove user data and configuration?" IDYES RemoveData IDNO KeepData
  RemoveData:
    RMDir /r "$APPDATA\Windows-AI"
  KeepData:

SectionEnd
```

## Build Process

### 1. Prepare Components

```bash
# Build backend bundle
pyinstaller installer/backend_bundle.spec

# Build GUI (already working)
cd apps/gui
npm run build

# Build tray
cd apps/tray
npm run build

# Download NSSM
curl -O https://nssm.cc/release/nssm-2.24.zip
unzip nssm-2.24.zip
```

### 2. Organize Distribution

```bash
mkdir -p dist/installer
cp build/backend/windows-ai-backend.exe dist/installer/backend/
cp -r apps/gui/dist/win-unpacked/* dist/installer/gui/
cp -r apps/tray/dist/win-unpacked/* dist/installer/tray/
cp -r scripts dist/installer/
cp -r config dist/installer/
cp nssm.exe dist/installer/services/
```

### 3. Compile NSIS Installer

```bash
makensis installer/windows_ai_installer.nsi
```

## Auto-Download Starter Model

### Script: `scripts/download_starter_model.bat`

```batch
@echo off
echo Downloading Phi-3-mini starter model...
echo This will download approximately 2.3GB

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing Ollama...
    powershell -Command "Invoke-WebRequest -Uri https://ollama.ai/download/OllamaSetup.exe -OutFile ollama-setup.exe"
    start /wait ollama-setup.exe /S
    del ollama-setup.exe
)

echo Downloading Phi-3-mini model...
ollama pull phi3:mini

echo ✓ Starter model downloaded!
echo You can now use local AI without API keys.
pause
```

## First Run Experience

### Script: `scripts/first_run_setup.bat`

```batch
@echo off
cls
echo ==========================================
echo   Welcome to Windows AI!
echo ==========================================
echo.
echo Setting up for first use...
echo.

REM Check for API keys
if "%OPENAI_API_KEY%"=="" if "%GOOGLE_API_KEY%"=="" if "%ANTHROPIC_API_KEY%"=="" (
    echo No API keys detected.
    echo.
    choice /C YN /M "Would you like to configure API keys now?"
    if errorlevel 2 goto SkipKeys
    if errorlevel 1 call configure-api-keys.bat
)
:SkipKeys

REM Ask about local model
choice /C YN /M "Download starter model for offline AI? (2.3GB)"
if errorlevel 1 call download_starter_model.bat

REM Start services
echo.
echo Starting Windows AI services...
call start-all.bat

echo.
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo Windows AI is now running!
echo - Chat GUI: Desktop shortcut or Start Menu
echo - Quick Commands: Press Ctrl+Shift+Space
echo - System Tray: Look for the icon near the clock
echo.
pause
```

## Testing Checklist

- [ ] Install on clean Windows 10 VM
- [ ] Install on Windows 11
- [ ] Test without internet connection
- [ ] Test with only OpenAI key
- [ ] Test with only local models
- [ ] Test Windows Service mode
- [ ] Test autostart
- [ ] Test uninstall (keep data)
- [ ] Test uninstall (remove data)
- [ ] Test upgrade from previous version
- [ ] Test firewall rules
- [ ] Test context menu integration
- [ ] Test shortcuts
- [ ] Test portable mode

## Next Steps

1. Implement PyInstaller backend bundling
2. Create NSIS custom pages for wizard
3. Test installer on clean Windows VM
4. Add digital signature
5. Create auto-updater mechanism
6. Implement rollback functionality
7. Add telemetry opt-in during install
8. Create installer localization
