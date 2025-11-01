\
!include "MUI2.nsh"
!define APPNAME "Windows AI"
!define COMPANY "Windows AI"
!define VERSION "0.1.0"
OutFile "WindowsAI-Setup-${VERSION}.exe"
InstallDir "C:\Windows AI"
RequestExecutionLevel admin
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"
Section "Install"
  SetOutPath "$INSTDIR"
  File /r "..\..\apps"
  File /r "..\..\scripts"
  File /r "..\..\config"
  File /r "..\..\assets"
  CreateDirectory "$PROGRAMDATA\Windows AI\config"
  CreateDirectory "$PROGRAMDATA\Windows AI\data"
  CreateDirectory "$PROGRAMDATA\Windows AI\logs"
  CreateDirectory "$PROGRAMDATA\Windows AI\models"
  CreateDirectory "$SMPROGRAMS\Windows AI"
SectionEnd
Section "Uninstall"
  RMDir /r "$SMPROGRAMS\Windows AI"
  RMDir /r "$INSTDIR"
SectionEnd

nsExec::ExecToLog 'cmd /c schtasks /Create /TN "WindowsAI_Actions" /TR ""$INSTDIR\\apps\\actions\\start.cmd"" /SC ONSTART /RL HIGHEST /F'

nsExec::ExecToLog 'cmd /c schtasks /Create /TN "WindowsAI_AgentHub" /TR ""$INSTDIR\\apps\\agenthub\\start.cmd"" /SC ONSTART /RL HIGHEST /F'

nsExec::ExecToLog 'cmd /c schtasks /Create /TN "WindowsAI_Proxy" /TR ""$INSTDIR\\apps\\proxy\\start.cmd"" /SC ONSTART /RL HIGHEST /F'

nsExec::ExecToLog 'cmd /c schtasks /Create /TN "WindowsAI_Tray" /TR ""$INSTDIR\\apps\\gui\\dist\\win-unpacked\\WindowsAI.exe"" /SC ONLOGON /RL HIGHEST /F'
