; Inno Setup script for VALKYRIE BALLISTICS
[Setup]
AppName=VALKYRIE BALLISTICS
AppVersion=1.0
DefaultDirName={pf}\VALKYRIE BALLISTICS
DefaultGroupName=VALKYRIE BALLISTICS
Compression=lzma2
disableDirPage=yes

[Files]
; Copy the entire onedir distribution into Program Files\VALKYRIE BALLISTICS
Source: "dist\VALKYRIE_BALLISTICS\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
; Also include the icon in the root
Source: "Logo\logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\VALKYRIE BALLISTICS"; Filename: "{app}\VALKYRIE_BALLISTICS.exe"; WorkingDir: "{app}"; IconFilename: "{app}\logo.ico"
Name: "{userdesktop}\VALKYRIE BALLISTICS"; Filename: "{app}\VALKYRIE_BALLISTICS.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"

[Tasks]
Name: desktopicon; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\VALKYRIE_BALLISTICS.exe"; Description: "Launch VALKYRIE BALLISTICS"; Flags: nowait postinstall skipifsilent
