Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonPath = fso.BuildPath(scriptDir, ".venv\\Scripts\\pythonw.exe")
appPath = fso.BuildPath(scriptDir, "HjemmeladingApp\\main.py")

Set WshShell = CreateObject("WScript.Shell")
' Ensure the script runs with project directory as current directory
WshShell.CurrentDirectory = scriptDir

' Prepare a simple log file for vbs-run failures
logPath = fso.BuildPath(scriptDir, "vbs_error.log")

On Error Resume Next
If fso.FileExists(pythonPath) Then
	WshShell.Run chr(34) & pythonPath & chr(34) & " " & chr(34) & appPath & chr(34), 0, False
Else
	WshShell.Run "pythonw " & chr(34) & appPath & chr(34), 0, False
End If
If Err.Number <> 0 Then
	errText = "VBScript Error: " & Err.Number & " - " & Err.Description & vbCrLf
	errText = errText & "Tried: " & pythonPath & " " & appPath & vbCrLf
	On Error Resume Next
	Set fh = fso.OpenTextFile(logPath, 8, True)
	fh.WriteLine Now() & " - " & errText
	fh.Close
	Set fh = Nothing
End If
On Error Goto 0

Set WshShell = Nothing
