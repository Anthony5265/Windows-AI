; ============================================================================
; Windows AI - Professional NSIS Installer Script
; Creates a production-ready Windows installer
; ============================================================================

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

; ============================================================================
; Application Information
; ============================================================================

!define APPNAME "Windows AI"
!define COMPANYNAME "Windows AI Team"
!define DESCRIPTION "AI Integration Platform for Windows"
!define VERSIONMAJOR 2
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define VERSION "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"

; URLs
!define HELPURL "https://github.com/Anthony5265/Windows-AI"
!define UPDATEURL "https://github.com/Anthony5265/Windows-AI/releases"
!define ABOUTURL "https://github.com/Anthony5265/Windows-AI"

; Installer Configuration
!define INSTALLERNAME "WindowsAI-Setup-${VERSION}.exe"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
!define REG_ROOT HKLM
!define REG_APP_PATH "Software\${APPNAME}"

; ============================================================================
; Installer Settings
; ============================================================================

Name "${APPNAME}"
OutFile "..\dist\${INSTALLERNAME}"
InstallDir "$PROGRAMFILES64\${APPNAME}"
InstallDirRegKey ${REG_ROOT} "${REG_APP_PATH}" "InstallDir"
RequestExecutionLevel admin

; Compression
SetCompressor /SOLID lzma
SetCompressorDictSize 32

; ============================================================================
; Version Information
; ============================================================================

VIProductVersion "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.0"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "CompanyName" "${COMPANYNAME}"
VIAddVersionKey "LegalCopyright" "Copyright (C) 2024-2026 ${COMPANYNAME}"
VIAddVersionKey "FileDescription" "${DESCRIPTION}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"

; ============================================================================
; Modern UI Configuration
; ============================================================================

!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APPNAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of ${APPNAME}.$\r$\n$\r$\n${DESCRIPTION}$\r$\n$\r$\nClick Next to continue."

; Icons
!define MUI_ICON "..\assets\icon.ico"
!define MUI_UNICON "..\assets\icon.ico"

; Header image
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "..\assets\installer-header.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "..\assets\installer-header.bmp"

; Welcome/Finish page
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\assets\installer-banner.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "..\assets\installer-banner.bmp"

; Finish page options
!define MUI_FINISHPAGE_RUN "$INSTDIR\WindowsAI.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APPNAME}"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.md"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "View README"
!define MUI_FINISHPAGE_LINK "Visit ${APPNAME} Website"
!define MUI_FINISHPAGE_LINK_LOCATION "${ABOUTURL}"

; ============================================================================
; Installer Pages
; ============================================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ============================================================================
; Uninstaller Pages
; ============================================================================

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; ============================================================================
; Languages
; ============================================================================

!insertmacro MUI_LANGUAGE "English"

; ============================================================================
; Installer Functions
; ============================================================================

Function .onInit
    ; Check for 64-bit system
    ${If} ${RunningX64}
        SetRegView 64
    ${Else}
        MessageBox MB_ICONSTOP "Windows AI requires a 64-bit version of Windows."
        Abort
    ${EndIf}

    ; Check for admin rights
    UserInfo::GetAccountType
    Pop $0
    ${If} $0 != "admin"
        MessageBox MB_ICONSTOP "Administrator rights required!"
        SetErrorLevel 740
        Quit
    ${EndIf}

    ; Check if already installed
    ReadRegStr $0 ${REG_ROOT} "${UNINST_KEY}" "UninstallString"
    ${If} $0 != ""
        MessageBox MB_OKCANCEL|MB_ICONQUESTION \
            "${APPNAME} is already installed.$\r$\n\
            Do you want to uninstall the previous version?" \
            IDOK uninst
        Abort
uninst:
        ; Run uninstaller
        ExecWait '$0 _?=$INSTDIR'
    ${EndIf}
FunctionEnd

; ============================================================================
; Installer Sections
; ============================================================================

; Core Application (Required)
Section "!${APPNAME} Core" SecCore
    SectionIn RO ; Required section

    SetOutPath "$INSTDIR"

    ; Copy main executable
    File "..\dist\WindowsAI.exe"

    ; Copy documentation
    File "..\README.md"
    File "..\LICENSE"

    ; Copy checksums
    File /nonfatal "..\dist\WindowsAI.sha256"

    ; Create directories
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\plugins"
    CreateDirectory "$INSTDIR\models"
    CreateDirectory "$INSTDIR\config"
    CreateDirectory "$INSTDIR\temp"

    ; Create default configuration
    FileOpen $0 "$INSTDIR\config\settings.yaml" w
    FileWrite $0 "# Windows AI Configuration$\r$\n"
    FileWrite $0 "version: ${VERSION}$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "# Security Settings$\r$\n"
    FileWrite $0 "security:$\r$\n"
    FileWrite $0 "  sandbox_level: standard$\r$\n"
    FileWrite $0 "  guardrails: true$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "# API Settings$\r$\n"
    FileWrite $0 "api:$\r$\n"
    FileWrite $0 "  host: localhost$\r$\n"
    FileWrite $0 "  port: 8010$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "# First Run$\r$\n"
    FileWrite $0 "setup:$\r$\n"
    FileWrite $0 "  first_run: true$\r$\n"
    FileClose $0

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Write registry entries
    WriteRegStr ${REG_ROOT} "${REG_APP_PATH}" "InstallDir" "$INSTDIR"
    WriteRegStr ${REG_ROOT} "${REG_APP_PATH}" "Version" "${VERSION}"

    ; Add/Remove Programs entries
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "DisplayName" "${APPNAME}"
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "DisplayVersion" "${VERSION}"
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "Publisher" "${COMPANYNAME}"
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "DisplayIcon" "$INSTDIR\WindowsAI.exe"
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "HelpLink" "${HELPURL}"
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr ${REG_ROOT} "${UNINST_KEY}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegDWORD ${REG_ROOT} "${UNINST_KEY}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD ${REG_ROOT} "${UNINST_KEY}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD ${REG_ROOT} "${UNINST_KEY}" "NoModify" 1
    WriteRegDWORD ${REG_ROOT} "${UNINST_KEY}" "NoRepair" 1

    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD ${REG_ROOT} "${UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

; Desktop Shortcut
Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" \
        "$INSTDIR\WindowsAI.exe" \
        "" \
        "$INSTDIR\WindowsAI.exe" \
        0 \
        SW_SHOWNORMAL \
        "" \
        "${DESCRIPTION}"
SectionEnd

; Start Menu Shortcuts
Section "Start Menu Shortcuts" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${APPNAME}"

    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" \
        "$INSTDIR\WindowsAI.exe" \
        "" \
        "$INSTDIR\WindowsAI.exe" \
        0 \
        SW_SHOWNORMAL \
        "" \
        "${DESCRIPTION}"

    CreateShortCut "$SMPROGRAMS\${APPNAME}\README.lnk" \
        "$INSTDIR\README.md"

    CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" \
        "$INSTDIR\Uninstall.exe" \
        "" \
        "$INSTDIR\Uninstall.exe" \
        0
SectionEnd

; Add to PATH
Section "Add to System PATH" SecPath
    ; Add to system PATH
    EnVar::SetHKLM
    EnVar::AddValue "PATH" "$INSTDIR"
    Pop $0
    DetailPrint "Added to PATH: $0"
SectionEnd

; File Associations
Section "File Associations" SecFileAssoc
    ; Associate .wai files with Windows AI
    WriteRegStr HKCR ".wai" "" "WindowsAI.Document"
    WriteRegStr HKCR "WindowsAI.Document" "" "Windows AI Workflow"
    WriteRegStr HKCR "WindowsAI.Document\DefaultIcon" "" "$INSTDIR\WindowsAI.exe,0"
    WriteRegStr HKCR "WindowsAI.Document\shell\open\command" "" '"$INSTDIR\WindowsAI.exe" "%1"'

    ; Refresh shell icons
    System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'
SectionEnd

; Auto-start with Windows
Section /o "Start with Windows" SecAutoStart
    CreateShortCut "$SMSTARTUP\${APPNAME}.lnk" \
        "$INSTDIR\WindowsAI.exe" \
        "--tray" \
        "$INSTDIR\WindowsAI.exe" \
        0 \
        SW_SHOWMINIMIZED
SectionEnd

; ============================================================================
; Section Descriptions
; ============================================================================

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} \
        "Core ${APPNAME} application (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} \
        "Create a desktop shortcut for quick access"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} \
        "Create Start Menu shortcuts"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPath} \
        "Add ${APPNAME} to system PATH for command-line access"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecFileAssoc} \
        "Associate .wai files with ${APPNAME}"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecAutoStart} \
        "Automatically start ${APPNAME} when Windows starts"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ============================================================================
; Uninstaller Section
; ============================================================================

Section "Uninstall"
    ; Stop any running instances
    nsExec::Exec 'taskkill /F /IM WindowsAI.exe'
    Sleep 1000

    ; Remove files
    Delete "$INSTDIR\WindowsAI.exe"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\WindowsAI.sha256"
    Delete "$INSTDIR\Uninstall.exe"

    ; Remove configuration (optional - ask user)
    MessageBox MB_YESNO "Do you want to remove all settings and data?" IDYES RemoveData IDNO SkipData
RemoveData:
    RMDir /r "$INSTDIR\data"
    RMDir /r "$INSTDIR\logs"
    RMDir /r "$INSTDIR\config"
    RMDir /r "$INSTDIR\plugins"
    RMDir /r "$INSTDIR\models"
SkipData:

    ; Remove temp directory
    RMDir /r "$INSTDIR\temp"

    ; Remove shortcuts
    Delete "$DESKTOP\${APPNAME}.lnk"
    Delete "$SMSTARTUP\${APPNAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APPNAME}"

    ; Remove from PATH
    EnVar::SetHKLM
    EnVar::DeleteValue "PATH" "$INSTDIR"

    ; Remove file associations
    DeleteRegKey HKCR ".wai"
    DeleteRegKey HKCR "WindowsAI.Document"

    ; Refresh shell icons
    System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'

    ; Remove registry entries
    DeleteRegKey ${REG_ROOT} "${UNINST_KEY}"
    DeleteRegKey ${REG_ROOT} "${REG_APP_PATH}"

    ; Remove installation directory
    RMDir "$INSTDIR"

    ; Remove user data (optional)
    MessageBox MB_YESNO "Remove user configuration in $PROFILE\.windows_ai?" IDYES RemoveUserData IDNO SkipUserData
RemoveUserData:
    RMDir /r "$PROFILE\.windows_ai"
SkipUserData:

SectionEnd

; ============================================================================
; Uninstaller Functions
; ============================================================================

Function un.onInit
    MessageBox MB_YESNO "Are you sure you want to uninstall ${APPNAME}?" IDYES +2
    Abort
FunctionEnd

Function un.onUninstSuccess
    MessageBox MB_OK "${APPNAME} has been successfully removed from your computer."
FunctionEnd
