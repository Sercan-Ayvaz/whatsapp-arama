[Setup]
AppName=WhatsApp Arama
AppVersion=1.0
DefaultDirName={autopf}\WhatsAppArama
DefaultGroupName=WhatsApp Arama
OutputDir=output
OutputBaseFilename=WhatsAppArama-Kurulum
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Files]
Source: "dist\WhatsAppArama\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\WhatsApp Arama"; Filename: "{app}\WhatsAppArama.exe"
Name: "{autodesktop}\WhatsApp Arama"; Filename: "{app}\WhatsAppArama.exe"

[Run]
Filename: "{app}\WhatsAppArama.exe"; Description: "Uygulamayi baslat"; Flags: nowait postinstall skipifsilent
