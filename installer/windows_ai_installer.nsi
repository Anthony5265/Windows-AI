
; Windows AI Complete Installer - ALL 43 PHASE 3 ITEMS
!define PRODUCT_NAME "Windows AI"
!define PRODUCT_VERSION "2.0.0"
!define PRODUCT_PUBLISHER "Windows AI Team"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "WindowsAI-Setup.exe"
InstallDir "$PROGRAMFILES\WindowsAI"

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "dist\*.*"
  CreateShortCut "$SMPROGRAMS\Windows AI.lnk" "$INSTDIR\WindowsAI.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\*.*"
  RMDir /r "$INSTDIR"
SectionEnd
