[CmdletBinding()]
param(
    [ValidateSet("Install", "Start", "Stop", "Toggle", "Status", "SetProfile")]
    [string]$Action = "Status",

    [ValidateSet("reference", "files-readonly", "browser-isolated")]
    [string]$Profile,

    [string]$FilesRoot,

    [switch]$NoNotify
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ControllerPath = Join-Path $PSScriptRoot "chat-platform-controller.ps1"
$MutexName = "Local\ChatAgentPlatformControllerOperation"
$MutexTimeoutMilliseconds = 30000
$script:LastControllerExitCode = 1

if (-not (Test-Path -LiteralPath $ControllerPath)) {
    throw "Internal controller is missing: $ControllerPath"
}

function Get-ControllerArguments {
    $arguments = [System.Collections.Generic.List[string]]::new()

    foreach ($value in @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $ControllerPath,
        "-Action", $Action
    )) {
        $arguments.Add([string]$value)
    }

    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        $arguments.Add("-Profile")
        $arguments.Add($Profile)
    }

    if (-not [string]::IsNullOrWhiteSpace($FilesRoot)) {
        $arguments.Add("-FilesRoot")
        $arguments.Add($FilesRoot)
    }

    if ($NoNotify) {
        $arguments.Add("-NoNotify")
    }

    return $arguments
}

function Invoke-InternalControllerStatus {
    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $arguments = Get-ControllerArguments

    # Status never starts a persistent child. Keep its JSON stdout transparent
    # so callers can parse it directly.
    & $pwsh @arguments
    $script:LastControllerExitCode = $LASTEXITCODE
}

function Invoke-InternalControllerMutation {
    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false

    foreach ($argument in (Get-ControllerArguments)) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    # Do not invoke the mutating controller through a PowerShell pipeline.
    # Start/Toggle may spawn long-lived 1MCP/tunnel descendants; if their
    # inherited stdout handle belongs to an outer pipeline, EOF can be held
    # open after the controller itself has completed. Wait on the exact child
    # process handle instead.
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo

    try {
        if (-not $process.Start()) {
            throw "Failed to start the internal Chat Agent Platform controller."
        }

        $process.WaitForExit()
        $script:LastControllerExitCode = $process.ExitCode
    }
    finally {
        $process.Dispose()
    }
}

if ($Action -eq "Status") {
    Invoke-InternalControllerStatus
    exit $script:LastControllerExitCode
}

$mutex = New-Object System.Threading.Mutex($false, $MutexName)
$acquired = $false
$exitCode = 1

try {
    try {
        $acquired = $mutex.WaitOne($MutexTimeoutMilliseconds)
    }
    catch [System.Threading.AbandonedMutexException] {
        # The previous owner terminated without releasing the mutex. Windows
        # grants ownership to this caller, so lifecycle recovery may continue.
        $acquired = $true
    }

    if (-not $acquired) {
        throw (
            "Another Chat Agent Platform lifecycle operation is still running. " +
            "Retry after it finishes."
        )
    }

    Invoke-InternalControllerMutation
    $exitCode = $script:LastControllerExitCode
}
finally {
    if ($acquired) {
        try {
            $mutex.ReleaseMutex()
        }
        catch {
            # Process/session teardown still closes the handle. Do not hide the
            # result of the lifecycle operation with a release-only error.
        }
    }

    $mutex.Dispose()
}

exit $exitCode
