Option Explicit

If WScript.Arguments.Count <> 2 Then
    WScript.Quit 2
End If

Const AutomaticHealthIntervalMilliseconds = 1800000

Dim shell, fileSystem, pwshPath, supervisorPath, localRoot, modePath, command, exitCode
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

pwshPath = WScript.Arguments.Item(0)
supervisorPath = WScript.Arguments.Item(1)
localRoot = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\ChatAgentPlatform"
modePath = localRoot & "\state\operation-mode.json"

' The scheduled task is always registered, but manual mode deliberately has no
' long-lived supervisor. This makes manual+OFF a zero-periodic-work state while
' preserving automatic mode as an opt-in reliability monitor.
If IsManualMode(modePath) Then
    WScript.Quit 0
End If

Do
    If IsManualMode(modePath) Then
        WScript.Quit 0
    End If

    command = Quote(pwshPath) & _
        " -NoLogo -NoProfile -ExecutionPolicy Bypass -File " & _
        Quote(supervisorPath) & " -Action Reconcile"

    ' A deep health/recovery pass is intentionally one-shot. The launcher waits
    ' for it, then remains dormant for 30 minutes. No 10-second PowerShell loop
    ' exists on the normal installed automatic path.
    exitCode = shell.Run(command, 0, True)

    If IsManualMode(modePath) Then
        WScript.Quit 0
    End If

    WScript.Sleep AutomaticHealthIntervalMilliseconds
Loop

Function IsManualMode(path)
    Dim stream, text
    IsManualMode = False

    If Not fileSystem.FileExists(path) Then
        Exit Function
    End If

    On Error Resume Next
    Set stream = fileSystem.OpenTextFile(path, 1, False)
    If Err.Number <> 0 Then
        Err.Clear
        On Error GoTo 0
        Exit Function
    End If

    text = LCase(stream.ReadAll)
    stream.Close
    On Error GoTo 0

    If InStr(text, Chr(34) & "mode" & Chr(34)) > 0 And _
       InStr(text, Chr(34) & "manual" & Chr(34)) > 0 Then
        IsManualMode = True
    End If
End Function

Function Quote(value)
    Quote = Chr(34) & Replace(value, Chr(34), Chr(34) & Chr(34)) & Chr(34)
End Function
