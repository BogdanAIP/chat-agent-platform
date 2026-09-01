[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PromptBodyPath,

    [string]$RunId,

    [switch]$NoLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pluginName = 'Chat Local Bridge Test'
$runIdPattern = '^[A-Za-z0-9._:-]{8,128}$'

function New-CapRunId {
    return ('autosend-' + [guid]::NewGuid().ToString('N'))
}

function Assert-CapRunId {
    param([Parameter(Mandatory = $true)][string]$Value)

    if ($Value -notmatch $runIdPattern) {
        throw 'RunId must be 8-128 characters and contain only letters, digits, dot, underscore, colon, or hyphen.'
    }
}

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = New-CapRunId
}
Assert-CapRunId -Value $RunId

$resolvedPromptPath = (Resolve-Path -LiteralPath $PromptBodyPath).Path
$promptBody = Get-Content -LiteralPath $resolvedPromptPath -Raw -Encoding utf8
if ([string]::IsNullOrWhiteSpace($promptBody)) {
    throw 'Prompt body must not be empty.'
}
if ($promptBody.Length -gt 12000) {
    throw 'Prompt body exceeds the 12000-character experimental bound.'
}
if ($promptBody -match 'CAP_AUTOSEND_RUN_ID=') {
    throw 'Prompt body must not contain CAP_AUTOSEND_RUN_ID; the launcher owns the run-id sentinel.'
}

$prompt = @(
    "@$pluginName DEEPLINK_AUTOSEND_WAKE"
    "CAP_AUTOSEND_RUN_ID=$RunId"
    ''
    $promptBody.Trim()
) -join "`n"

$encodedRunId = [uri]::EscapeDataString($RunId)
$encodedPlugin = [uri]::EscapeDataString($pluginName)
$encodedPrompt = [uri]::EscapeDataString($prompt)
$url = "https://chatgpt.com/?cap_autosend=1&cap_run_id=$encodedRunId&cap_plugin=$encodedPlugin&prompt=$encodedPrompt"

$result = [ordered]@{
    run_id = $RunId
    prompt_path = $resolvedPromptPath
    url = $url
    launched = $false
}

if (-not $NoLaunch) {
    if ($env:OS -ne 'Windows_NT') {
        throw 'This launcher physically opens ChatGPT only on Windows.'
    }

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $url
    $startInfo.UseShellExecute = $true
    $process = [System.Diagnostics.Process]::Start($startInfo)
    if ($null -eq $process) {
        throw 'Windows did not return a process handle for the HTTPS URI launch.'
    }
    $result.launched = $true
}

$result | ConvertTo-Json -Compress
