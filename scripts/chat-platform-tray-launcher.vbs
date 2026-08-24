Option Explicit

If WScript.Arguments.Count <> 2 Then
    WScript.Quit 2
End If

Dim shell, pwshPath, trayPath, command
Set shell = CreateObject("WScript.Shell")

pwshPath = WScript.Arguments.Item(0)
trayPath = WScript.Arguments.Item(1)

command = Quote(pwshPath) & _
    " -NoLogo -NoProfile -ExecutionPolicy Bypass -File " & _
    Quote(trayPath) & " -NoConsoleHost"

' Window style 0 means hidden. The tray owns only the notification-area UI;
' no console host should remain visible or long-lived in the user session.
shell.Run command, 0, False
WScript.Quit 0

Function Quote(value)
    Quote = Chr(34) & Replace(value, Chr(34), Chr(34) & Chr(34)) & Chr(34)
End Function
