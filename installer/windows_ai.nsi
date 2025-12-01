; Windows AI NSIS Installer Script
; Creates professional Windows installer

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; Application Info
!define APPNAME "Windows AI"
!define COMPANYNAME "Windows AI Team"
!define DESCRIPTION "AI Integration Platform for Windows"
!define VERSIONMAJOR 2
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/Anthony5265/Windows-AI"
!define UPDATEURL "https://github.com/Anthony5265/Windows-AI/releases"
!define ABOUTURL "https://github.com/Anthony5265/Windows-AI"

; Installer Settings
Name "${APPNAME}"
OutFile "..\dist\WindowsAI-Setup-${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" "InstallDir"
RequestExecutionLevel admin

; Modern UI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\assets\icon.ico"
!define MUI_UNICON "..\assets\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\assets\installer-banner.bmp"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Windows AI Core" SecCore
    SectionIn RO ; Required section

    SetOutPath "$INSTDIR"

    ; Copy all files from build directory
    File /r "..\dist\WindowsAI\*.*"

    ; Create data directories
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\plugins"
    CreateDirectory "$INSTDIR\models"
    CreateDirectory "$INSTDIR\config"

    ; Write default config
    FileOpen $0 "$INSTDIR\config\settings.yaml" w
    FileWrite $0 "# Windows AI Configuration$\r$\n"
    FileWrite $0 "version: ${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}$\r$\n"
    FileWrite $0 "security:$\r$\n"
    FileWrite $0 "  sandbox_level: standard$\r$\n"
    FileWrite $0 "  guardrails: true$\r$\n"
    FileWrite $0 "api:$\r$\n"
    FileWrite $0 "  host: localhost$\r$\n"
    FileWrite $0 "  port: 8765$\r$\n"
    FileClose $0

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\WindowsAI.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1

    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" "$0"

    ; Store install directory
    WriteRegStr HKLM "Software\${APPNAME}" "InstallDir" "$INSTDIR"
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\WindowsAI.exe" "" "$INSTDIR\WindowsAI.exe" 0
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\WindowsAI.exe" "" "$INSTDIR\WindowsAI.exe" 0
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
SectionEnd

Section "Add to PATH" SecPath
    ; Add to system PATH
    EnVar::SetHKLM
    EnVar::AddValue "PATH" "$INSTDIR"
SectionEnd

Section "Install Dependencies" SecDeps
    ; Check for Python
    nsExec::ExecToLog 'python --version'
    Pop $0
    ${If} $0 != 0
        MessageBox MB_YESNO "Python not found. Would you like to download it?" IDNO skip_python
        ExecShell "open" "https://www.python.org/downloads/"
        skip_python:
    ${EndIf}

    ; Install Python dependencies
    SetOutPath "$INSTDIR"
    nsExec::ExecToLog 'pip install -r "$INSTDIR\requirements-full.txt" --quiet'
SectionEnd

Section "Install Ollama (Local AI)" SecOllama
    ; Download and install Ollama for local LLM support
    MessageBox MB_YESNO "Would you like to install Ollama for local AI models?" IDNO skip_ollama
    ExecShell "open" "https://ollama.ai/download"
    skip_ollama:
SectionEnd

; Section Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core Windows AI application (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Create a desktop shortcut"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create Start Menu shortcuts"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPath} "Add Windows AI to system PATH"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDeps} "Install Python dependencies"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecOllama} "Install Ollama for local AI model support"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Section
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR\*.*"
    RMDir "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\${APPNAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APPNAME}"

    ; Remove from PATH
    EnVar::SetHKLM
    EnVar::DeleteValue "PATH" "$INSTDIR"

    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey HKLM "Software\${APPNAME}"
SectionEnd

; Installer Functions
Function .onInit
    ; Check for admin rights
    UserInfo::GetAccountType
    Pop $0
    ${If} $0 != "admin"
        MessageBox MB_ICONSTOP "Administrator rights required!"
        SetErrorLevel 740
        Quit
    ${EndIf}
FunctionEnd
