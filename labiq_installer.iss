[Setup]
AppName=LabIQ
AppVersion=1.0
AppPublisher=Bojanna Shantheyanda
AppPublisherURL=https://labiq-production.up.railway.app
DefaultDirName={autopf}\LabIQ
DefaultGroupName=LabIQ
OutputDir=installer
OutputBaseFilename=LabIQ_Setup
SetupIconFile=labiq.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\LabIQ.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LabIQ"; Filename: "{app}\LabIQ.exe"
Name: "{group}\Uninstall LabIQ"; Filename: "{uninstallexe}"
Name: "{autodesktop}\LabIQ"; Filename: "{app}\LabIQ.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\LabIQ.exe"; Description: "Launch LabIQ"; Flags: nowait postinstall skipifsilent