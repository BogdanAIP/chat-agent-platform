[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ControllerPath,
    [Parameter(Mandatory)][string]$ConfigPath,
    [Parameter(Mandatory)][string]$ModelRoot,
    [Parameter(Mandatory)][string]$StateRoot,
    [ValidateRange(1, 60)][int]$IntervalSeconds = 15
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $ControllerPath -PathType Leaf)) {
    throw "Vision runtime controller is missing: $ControllerPath"
}

$testMode = ([string]$env:CHAT_VISION_RUNTIME_TEST_MODE -eq '1')

while ($true) {
    Start-Sleep -Seconds $IntervalSeconds
    try {
        if ($testMode) {
            $json = & $ControllerPath `
                -Action Sweep `
                -ConfigPath $ConfigPath `
                -ModelRoot $ModelRoot `
                -StateRoot $StateRoot `
                2>&1 | Out-String
        }
        else {
            $json = & $ControllerPath -Action Sweep 2>&1 | Out-String
        }

        try {
            $status = $json | ConvertFrom-Json
        }
        catch {
            break
        }
        if (-not [bool]$status.running) {
            break
        }
    }
    catch {
        break
    }
}
