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

function Invoke-InternalController {
    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $arguments = @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $ControllerPath,
        "-Action", $Action
    )

    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        $arguments += @("-Profile", $Profile)
    }

    if (-not [string]::IsNullOrWhiteSpace($FilesRoot)) {
        $arguments += @("-FilesRoot", $FilesRoot)
    }

    if ($NoNotify) {
        $arguments += "-NoNotify"
    }

    # Keep controller stdout/stderr transparent to the caller. Store the exit
    # code out-of-band so Status JSON is never captured into an object array.
    & $pwsh @arguments
    $script:LastControllerExitCode = $LASTEXITCODE
}

if ($Action -eq "Status") {
    Invoke-InternalController
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

    Invoke-InternalController
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
