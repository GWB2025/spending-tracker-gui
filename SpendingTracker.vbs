' Spending Tracker VBScript Launcher
' Launches the application silently without console windows

On Error Resume Next

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to the application directory
objShell.CurrentDirectory = strScriptPath

' Build paths
strPythonPath = strScriptPath & "\venv\Scripts\pythonw.exe"
strMainScript = strScriptPath & "\src\main.py"

' Check if files exist
If Not objFSO.FileExists(strPythonPath) Then
    MsgBox "Virtual environment not found. Please ensure the application is properly installed.", 16, "Spending Tracker - Error"
    WScript.Quit 1
End If

If Not objFSO.FileExists(strMainScript) Then
    MsgBox "Application files not found. Please ensure the application is properly installed.", 16, "Spending Tracker - Error"
    WScript.Quit 1
End If

' Build command with proper quoting
strCommand = Chr(34) & strPythonPath & Chr(34) & " " & Chr(34) & strMainScript & Chr(34)

' Run the command hidden (0 = hidden window, False = don't wait)
intResult = objShell.Run(strCommand, 0, False)

' Check for errors after a brief delay
WScript.Sleep 500
If Err.Number <> 0 Then
    MsgBox "Error starting Spending Tracker: " & Err.Description, 16, "Spending Tracker - Error"
End If
