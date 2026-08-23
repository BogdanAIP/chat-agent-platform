Option Explicit

If WScript.Arguments.Count <> 2 Then
    WScript.Quit 2
End If

Dim shell, pwshPath, supervisorPath, command
Set shell = CreateObject("WScript.Shell")

pwshPath = WScript.Arguments.Item(0)
supervisorPath = WScript.Arguments.Item(1)

command = Quote(pwshPath) & _
    " -NoLogo -NoProfile -ExecutionPolicy Bypass -File " & _
    Quote(supervisorPath) & " -Action Run"

' Window style 0 means hidden. wscript.exe is a GUI-subsystem host, so the
' long-lived supervisor never needs a visible console host in the user session.
shell.Run command, 0, False
WScript.Quit 0

Function Quote(value)
    Quote = Chr(34) & Replace(value, Chr(34), Chr(34) & Chr(34)) & Chr(34)
End Function
