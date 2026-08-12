Option Explicit

Const CREATE_NO_WINDOW = 134217728

Dim shell, fso, scriptDir, trayScript, pwshPath, commandLine
Dim locator, service, startupClass, startup, processClass, processId, result

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
trayScript = fso.BuildPath(scriptDir, "chat-platform-tray.ps1")
pwshPath = shell.ExpandEnvironmentStrings("%ProgramFiles%") & "\PowerShell\7\pwsh.exe"

If Not fso.FileExists(pwshPath) Then
    pwshPath = "pwsh.exe"
End If

commandLine = Quote(pwshPath) & _
    " -NoLogo -NoProfile -ExecutionPolicy Bypass -File " & Quote(trayScript) & _
    " -NoConsoleHost"

Set locator = CreateObject("WbemScripting.SWbemLocator")
Set service = locator.ConnectServer(".", "root\cimv2")
Set startupClass = service.Get("Win32_ProcessStartup")
Set startup = startupClass.SpawnInstance_()
startup.ShowWindow = 0
startup.CreateFlags = CREATE_NO_WINDOW

Set processClass = service.Get("Win32_Process")
result = processClass.Create(commandLine, Null, startup, processId)

If result <> 0 Then
    WScript.Quit result
End If

WScript.Quit 0

Function Quote(value)
    Quote = Chr(34) & value & Chr(34)
End Function
