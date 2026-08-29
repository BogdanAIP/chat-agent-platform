[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PromptBodyPath,

    [string]$RunId,

    [string]$BrowserPath,

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

function Resolve-ChromePath {
    param([string]$ExplicitPath)

    if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
        $resolved = (Resolve-Path -LiteralPath $ExplicitPath -ErrorAction Stop).Path
        if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
            throw "Chrome executable not found: $ExplicitPath"
        }
        return $resolved
    }

    $command = Get-Command chrome.exe -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
        (if (${env:ProgramFiles(x86)}) { Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe' }),
        (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    throw 'Google Chrome was not found. Install Chrome or pass -BrowserPath explicitly. The launcher will not fall back to the Windows default browser.'
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
    browser_path = $null
    launched = $false
}

if (-not $NoLaunch) {
    if ($env:OS -ne 'Windows_NT') {
        throw 'This launcher physically opens ChatGPT only on Windows.'
    }

    $resolvedBrowserPath = Resolve-ChromePath -ExplicitPath $BrowserPath
    $result.browser_path = $resolvedBrowserPath

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $resolvedBrowserPath
    $startInfo.ArgumentList.Add($url)
    $startInfo.UseShellExecute = $false
    $process = [System.Diagnostics.Process]::Start($startInfo)
    if ($null -eq $process) {
        throw 'Chrome launch did not return a process handle.'
    }
    $result.launched = $true
}

$result | ConvertTo-Json -Compress
