#define AppName "Majestic AI Fisher"
#define AppVersion "0.1.0"
#define AppPublisher "Majestic AI Fisher"
#define AppExeName "MajesticAIFisher.exe"

[Setup]
AppId={{A8E659D5-18BE-4F4B-90D8-7938F5708985}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\MajesticAIFisher
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\installer-output
OutputBaseFilename=MajesticAIFisher-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Ярлыки:"; Flags: unchecked

[Files]
Source: "..\native-build\MajesticAIFisher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\native-build\fishing_native.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\native-build\libgcc_s_seh-1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\native-build\libwinpthread-1.dll"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Запустить {#AppName}"; Flags: nowait postinstall skipifsilent
