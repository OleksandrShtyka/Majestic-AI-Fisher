Unicode true
Name "Majestic AI Fisher"
OutFile "..\installer-output\MajesticAIFisher-Setup.exe"
InstallDir "$LOCALAPPDATA\MajesticAIFisher"
RequestExecutionLevel user
ShowInstDetails show
ShowUninstDetails show

!include "MUI2.nsh"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Russian"

Section "Установить"
  SetOutPath "$INSTDIR"
  File "..\native-build\MajesticAIFisher.exe"
  File "..\native-build\fishing_native.dll"
  File "..\native-build\libgcc_s_seh-1.dll"
  File "..\native-build\libwinpthread-1.dll"

  CreateDirectory "$SMPROGRAMS\Majestic AI Fisher"
  CreateShortcut "$SMPROGRAMS\Majestic AI Fisher\Majestic AI Fisher.lnk" "$INSTDIR\MajesticAIFisher.exe"
  CreateShortcut "$DESKTOP\Majestic AI Fisher.lnk" "$INSTDIR\MajesticAIFisher.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MajesticAIFisher" "DisplayName" "Majestic AI Fisher"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MajesticAIFisher" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MajesticAIFisher" "DisplayIcon" "$INSTDIR\MajesticAIFisher.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MajesticAIFisher" "Publisher" "Majestic AI Fisher"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Majestic AI Fisher.lnk"
  Delete "$SMPROGRAMS\Majestic AI Fisher\Majestic AI Fisher.lnk"
  RMDir "$SMPROGRAMS\Majestic AI Fisher"
  Delete "$INSTDIR\MajesticAIFisher.exe"
  Delete "$INSTDIR\fishing_native.dll"
  Delete "$INSTDIR\libgcc_s_seh-1.dll"
  Delete "$INSTDIR\libwinpthread-1.dll"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir /r "$INSTDIR\avatars"
  Delete "$INSTDIR\accounts.dat"
  Delete "$INSTDIR\dqn_model.bin"
  Delete "$INSTDIR\imgui.ini"
  Delete "$INSTDIR\session.dat"
  Delete "$INSTDIR\tickets.dat"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MajesticAIFisher"
SectionEnd
