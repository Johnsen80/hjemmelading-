Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

venvPath = scriptDir & "\\.venv\\Scripts\\pythonw.exe"
If Not fso.FileExists(venvPath) Then
    venvPath = "pythonw"
End If

linkPath = scriptDir & "\\HJEMMELADING_test.lnk"
Set lnk = WshShell.CreateShortcut(linkPath)
lnk.TargetPath = venvPath
lnk.Arguments = Chr(34) & scriptDir & "\\HjemmeladingApp\\main.py" & Chr(34)
lnk.WorkingDirectory = scriptDir
iconPath = scriptDir & "\\hjemmelading.ico"
If fso.FileExists(iconPath) Then
    lnk.IconLocation = iconPath
End If
lnk.Description = "HJEMMELADING - test shortcut"
lnk.Save

Set lnk = Nothing
Set WshShell = Nothing
Set fso = Nothing
