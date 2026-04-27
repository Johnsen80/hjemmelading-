; Inno Setup script for VALKYRIE BALLISTICS
#define AppVersion GetEnv('VALKYRIE_APP_VERSION')
#if AppVersion == ""
	#define AppVersion "1.0"
#endif
#define DistDir GetEnv('VALKYRIE_DIST_DIR')
#if DistDir == ""
	#define DistDir "..\dist\VALKYRIE_BALLISTICS"
#endif
#define OutputDir GetEnv('VALKYRIE_INSTALLER_OUT')
#if OutputDir == ""
	#define OutputDir "..\dist\installer"
#endif
[Setup]
AppName=VALKYRIE BALLISTICS
AppVersion={#AppVersion}
DefaultDirName={pf}\VALKYRIE BALLISTICS
DefaultGroupName=VALKYRIE BALLISTICS
Compression=lzma2
disableDirPage=yes
OutputDir={#OutputDir}

[Files]
; Copy the entire onedir distribution into Program Files\VALKYRIE BALLISTICS
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\VALKYRIE BALLISTICS"; Filename: "{app}\VALKYRIE_BALLISTICS.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\VALKYRIE BALLISTICS"; Filename: "{app}\VALKYRIE_BALLISTICS.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\VALKYRIE_BALLISTICS.exe"; Description: "Launch VALKYRIE BALLISTICS"; Flags: nowait postinstall skipifsilent
