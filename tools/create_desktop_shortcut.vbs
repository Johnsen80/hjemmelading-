Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

' Determine project folder (assumes this script lives under <project>\tools)
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectDir = fso.GetParentFolderName(scriptDir)

' Resolve desktop path (OneDrive or classic Desktop)
desktop1 = WshShell.SpecialFolders("Desktop")
desktopPath = desktop1

' Prefer venv pythonw if present
venvPythonw = projectDir & "\\.venv\\Scripts\\pythonw.exe"
targetPython = "pythonw"
If fso.FileExists(venvPythonw) Then
    targetPython = venvPythonw
End If

linkPath = desktopPath & "\\HJEMMELADING.lnk"
Set lnk = WshShell.CreateShortcut(linkPath)
lnk.TargetPath = targetPython
lnk.Arguments = Chr(34) & projectDir & "\\HjemmeladingApp\\main.py" & Chr(34)
lnk.WorkingDirectory = projectDir
iconPath = projectDir & "\\hjemmelading.ico"
If fso.FileExists(iconPath) Then
    lnk.IconLocation = iconPath
End If
lnk.Description = "HJEMMELADING - Launch application (uses venv pythonw if available)"
lnk.Save

WScript.Echo "Created shortcut: " & linkPath

Set lnk = Nothing
Set WshShell = Nothing
Set fso = Nothing
