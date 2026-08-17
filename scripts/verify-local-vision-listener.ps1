[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateRange(1, 2147483647)]
    [int]$ExpectedPid,

    [ValidateRange(1, 65535)]
    [int]$Port = 3068
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$testMode = ([string]$env:CHAT_VISION_RUNTIME_TEST_MODE -eq '1')
if (-not $testMode -and $Port -ne 3068) {
    throw 'Production vision listener verification is fixed to reviewed port 3068.'
}

if ($null -eq (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue)) {
    throw 'Get-NetTCPConnection is required to verify vision runtime listener ownership.'
}

$listeners = @(
    Get-NetTCPConnection `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction Stop
)

if ($listeners.Count -eq 0) {
    throw "Vision runtime listener is missing on reviewed port $Port."
}

$foreign = @(
    $listeners | Where-Object { [int]$_.OwningProcess -ne $ExpectedPid }
)
$nonLoopback = @(
    $listeners | Where-Object { [string]$_.LocalAddress -ne '127.0.0.1' }
)
$ownedLoopback = @(
    $listeners | Where-Object {
        [int]$_.OwningProcess -eq $ExpectedPid -and
        [string]$_.LocalAddress -eq '127.0.0.1'
    }
)

if (
    $foreign.Count -gt 0 -or
    $nonLoopback.Count -gt 0 -or
    $ownedLoopback.Count -eq 0
) {
    $summary = @(
        $listeners | ForEach-Object {
            "$([string]$_.LocalAddress):$Port pid=$([int]$_.OwningProcess)"
        }
    ) -join ', '
    throw "Vision runtime listener ownership mismatch. Expected pid=$ExpectedPid on 127.0.0.1:$Port; observed: $summary"
}

[pscustomobject]@{
    schema_version = 1
    owned = $true
    pid = $ExpectedPid
    host = '127.0.0.1'
    port = $Port
    listener_count = $listeners.Count
} | ConvertTo-Json -Depth 4
