; Windows AI - NSIS Installer Script
; Complete zero-config installer for Windows AI Assistant
; Bundles Python, Node.js, dependencies, and auto-configures everything

!define APP_NAME "Windows AI"
!define APP_VERSION "0.5.0"
!define COMPANY_NAME "Windows AI Team"
!define APP_DESCRIPTION "AI-powered intelligent assistant for Windows"
!define APP_EXECUTABLE "windows-ai.exe"
!define INSTALL_DIR "$PROGRAMFILES64\${APP_NAME}"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

; Modern UI
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"
!include "x64.nsh"

; =====================================================================
; General Configuration
; =====================================================================

Name "${APP_NAME}"
OutFile "WindowsAI-Setup-${APP_VERSION}.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
ShowInstDetails show
ShowUnInstDetails show

; =====================================================================
; Modern UI Configuration
; =====================================================================

!define MUI_ABORTWARNING
!define MUI_ICON "install\assets\icon.ico"
!define MUI_UNICON "install\assets\icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "install\assets\header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "install\assets\wizard.bmp"
!define MUI_FINISHPAGE_RUN "$INSTDIR\windows-ai-tray\windows-ai-tray.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Windows AI Tray"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.md"

; =====================================================================
; Pages
; =====================================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; =====================================================================
; Version Information
; =====================================================================

VIProductVersion "0.5.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${COMPANY_NAME}"
VIAddVersionKey "LegalCopyright" "© ${COMPANY_NAME}"
VIAddVersionKey "FileDescription" "${APP_DESCRIPTION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"

; =====================================================================
; Installer Sections
; =====================================================================

Section "!Core Components" SecCore
  SectionIn RO  ; Required section

  DetailPrint "Installing Windows AI Core..."
  SetOutPath "$INSTDIR"

  ; Copy core files
  File /r "windows_ai"
  File /r "apps"
  File /r "install"
  File /r "scripts"
  File "README.md"
  File "LICENSE"
  File "requirements.txt"
  File "pyproject.toml"

  DetailPrint "Installing Python runtime..."
  ; Extract embedded Python
  SetOutPath "$INSTDIR\python"
  File /r "install\runtimes\python-3.11-embed-amd64\*.*"

  DetailPrint "Installing Node.js runtime..."
  ; Extract Node.js portable
  SetOutPath "$INSTDIR\nodejs"
  File /r "install\runtimes\node-v20-win-x64\*.*"

  ; Add to PATH for this installer session
  System::Call 'Kernel32::SetEnvironmentVariable(t "PATH", t "$INSTDIR\python;$INSTDIR\nodejs;$%PATH%")'

  DetailPrint "Installing Python dependencies..."
  SetOutPath "$INSTDIR"
  nsExec::ExecToLog '"$INSTDIR\python\python.exe" -m pip install --no-warn-script-location -r requirements.txt'
  Pop $0
  ${If} $0 != 0
    DetailPrint "Warning: Some Python dependencies may have failed to install"
  ${EndIf}

  DetailPrint "Installing Node.js dependencies for GUI..."
  SetOutPath "$INSTDIR\apps\gui"
  nsExec::ExecToLog '"$INSTDIR\nodejs\npm.cmd" install --production'
  Pop $0

  DetailPrint "Installing Node.js dependencies for Tray..."
  SetOutPath "$INSTDIR\windows-ai-tray"
  nsExec::ExecToLog '"$INSTDIR\nodejs\npm.cmd" install --production'
  Pop $0

  DetailPrint "Creating data directory..."
  CreateDirectory "$APPDATA\WindowsAI"
  CreateDirectory "$APPDATA\WindowsAI\models"
  CreateDirectory "$APPDATA\WindowsAI\plugins"
  CreateDirectory "$APPDATA\WindowsAI\logs"

  ; Write default config
  FileOpen $0 "$APPDATA\WindowsAI\config.json" w
  FileWrite $0 '{"model": "gpt-3.5-turbo", "temperature": 0.7, "theme": "dark", "auto_start": true}'
  FileClose $0

  DetailPrint "Core installation complete!"
SectionEnd

Section "Windows Service" SecService
  DetailPrint "Installing Windows AI Service..."

  ; Install Python service dependencies
  SetOutPath "$INSTDIR"
  nsExec::ExecToLog '"$INSTDIR\python\python.exe" -m pip install --no-warn-script-location pywin32'

  ; Install the Windows service
  DetailPrint "Registering Windows service..."
  nsExec::ExecToLog '"$INSTDIR\python\python.exe" "$INSTDIR\install\windows_service.py" --startup auto install'
  Pop $0
  ${If} $0 == 0
    DetailPrint "Starting Windows AI service..."
    nsExec::ExecToLog 'net start WindowsAI'
    Pop $0
    ${If} $0 == 0
      DetailPrint "Service started successfully!"
    ${Else}
      DetailPrint "Warning: Service installed but failed to start. You can start it manually from Services."
    ${EndIf}
  ${Else}
    MessageBox MB_OK|MB_ICONEXCLAMATION "Failed to install Windows service. The application will still work but won't auto-start on boot. You may need to run the installer as Administrator."
  ${EndIf}
SectionEnd

Section "System Tray Application" SecTray
  DetailPrint "Configuring System Tray application..."

  SetOutPath "$INSTDIR\windows-ai-tray"

  ; Create startup shortcut for tray app
  CreateDirectory "$SMSTARTUP"
  CreateShortcut "$SMSTARTUP\Windows AI Tray.lnk" "$INSTDIR\windows-ai-tray\windows-ai-tray.exe" "" "$INSTDIR\windows-ai-tray\icon.ico"

  DetailPrint "Tray application configured for auto-start"
SectionEnd

Section "Desktop Shortcuts" SecShortcuts
  DetailPrint "Creating shortcuts..."

  ; Desktop shortcuts
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\apps\gui\windows-ai-gui.exe" "" "$INSTDIR\apps\gui\icon.ico"

  ; Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\apps\gui\windows-ai-gui.exe" "" "$INSTDIR\apps\gui\icon.ico"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\System Tray.lnk" "$INSTDIR\windows-ai-tray\windows-ai-tray.exe" "" "$INSTDIR\windows-ai-tray\icon.ico"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

  DetailPrint "Shortcuts created"
SectionEnd

Section "First-Run Wizard" SecWizard
  DetailPrint "Installing First-Run Wizard..."

  SetOutPath "$INSTDIR\first-run-wizard"
  File /r "first-run-wizard\*.*"

  ; Install wizard dependencies
  nsExec::ExecToLog '"$INSTDIR\nodejs\npm.cmd" install --production'

  DetailPrint "First-Run Wizard installed"
SectionEnd

Section "Documentation" SecDocs
  DetailPrint "Installing documentation..."

  SetOutPath "$INSTDIR\docs"
  File /r "docs\*.*"

  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Documentation.lnk" "$INSTDIR\docs\README.md"

  DetailPrint "Documentation installed"
SectionEnd

; =====================================================================
; Post-Installation
; =====================================================================

Section -Post
  DetailPrint "Finalizing installation..."

  ; Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Write registry keys
  WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\${APP_NAME}" "Version" "${APP_VERSION}"

  ; Add to Programs and Features
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "${COMPANY_NAME}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\apps\gui\icon.ico"
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair" 1

  ; Calculate installed size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "EstimatedSize" "$0"

  ; Set environment variables
  WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "WINDOWSAI_HOME" "$INSTDIR"

  ; Notify system of environment change
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

  DetailPrint "Installation complete!"
  DetailPrint ""
  DetailPrint "Windows AI has been installed successfully."
  DetailPrint "The service will auto-start on boot."
  DetailPrint "Launch the tray application to get started."
SectionEnd

; =====================================================================
; Section Descriptions
; =====================================================================

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core Windows AI components (required)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecService} "Windows service for auto-start on boot (recommended)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecTray} "System tray application for quick access (recommended)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecShortcuts} "Desktop and Start Menu shortcuts"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecWizard} "First-run setup wizard"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "Documentation and user guides"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; =====================================================================
; Uninstaller
; =====================================================================

Section "Uninstall"
  DetailPrint "Stopping Windows AI Service..."
  nsExec::ExecToLog 'net stop WindowsAI'

  DetailPrint "Removing Windows AI Service..."
  nsExec::ExecToLog '"$INSTDIR\python\python.exe" "$INSTDIR\install\windows_service.py" remove'

  DetailPrint "Removing files..."

  ; Remove shortcuts
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMSTARTUP\Windows AI Tray.lnk"
  RMDir /r "$SMPROGRAMS\${APP_NAME}"

  ; Remove installation directory
  RMDir /r "$INSTDIR\windows_ai"
  RMDir /r "$INSTDIR\apps"
  RMDir /r "$INSTDIR\install"
  RMDir /r "$INSTDIR\scripts"
  RMDir /r "$INSTDIR\first-run-wizard"
  RMDir /r "$INSTDIR\windows-ai-tray"
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\nodejs"
  RMDir /r "$INSTDIR\docs"
  Delete "$INSTDIR\*.md"
  Delete "$INSTDIR\*.txt"
  Delete "$INSTDIR\*.toml"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  ; Remove registry keys
  DeleteRegKey HKLM "${UNINSTALL_KEY}"
  DeleteRegKey HKLM "Software\${APP_NAME}"
  DeleteRegValue HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "WINDOWSAI_HOME"

  ; Notify system of environment change
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

  DetailPrint "Uninstallation complete!"

  ; Ask if user wants to remove data
  MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to remove all user data and settings? This cannot be undone." IDYES RemoveData IDNO KeepData

  RemoveData:
    DetailPrint "Removing user data..."
    RMDir /r "$APPDATA\WindowsAI"
    Goto Done

  KeepData:
    DetailPrint "User data preserved in $APPDATA\WindowsAI"

  Done:
SectionEnd

; =====================================================================
; Installer Functions
; =====================================================================

Function .onInit
  ; Check Windows version
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_OK|MB_ICONSTOP "Windows AI requires Windows 10 or later."
    Abort
  ${EndIf}

  ; Check 64-bit
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "Windows AI requires 64-bit Windows."
    Abort
  ${EndIf}

  ; Check if already installed
  ReadRegStr $0 HKLM "Software\${APP_NAME}" "InstallDir"
  ${If} $0 != ""
    MessageBox MB_YESNO|MB_ICONQUESTION "${APP_NAME} is already installed. Do you want to reinstall?" IDYES Continue
    Abort
    Continue:
  ${EndIf}

  ; Check admin rights
  UserInfo::GetAccountType
  Pop $0
  ${If} $0 != "admin"
    MessageBox MB_OK|MB_ICONEXCLAMATION "Administrator rights required. Please run installer as Administrator."
    SetErrorLevel 740 ; ERROR_ELEVATION_REQUIRED
    Abort
  ${EndIf}
FunctionEnd

Function .onInstSuccess
  ; Show completion message
  MessageBox MB_OK "${APP_NAME} has been installed successfully!$\n$\nThe backend service is now running.$\nLaunch the tray application to get started."
FunctionEnd
