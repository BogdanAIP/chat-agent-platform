[CmdletBinding()]
param(
    [int]$DelayMinutes = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$logPath = Join-Path $PSScriptRoot 'probe-error.log'
if (Test-Path -LiteralPath $logPath) {
    Remove-Item -LiteralPath $logPath -Force
}

try {
    if ($DelayMinutes -lt 1 -or $DelayMinutes -gt 30) {
        throw 'DelayMinutes must be between 1 and 30.'
    }

    $promptPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'experiments/chatgpt-deeplink-autosend/scheduled-probe-prompt.txt'
    $registrarPath = Join-Path $PSScriptRoot 'register-chatgpt-deeplink-autosend-probe.ps1'
    $at = (Get-Date).AddMinutes($DelayMinutes)

    & $registrarPath -PromptBodyPath $promptPath -At $at -Force

    Write-Host ''
    Write-Host ('SUCCESS: probe scheduled for ' + $at.ToString('HH:mm:ss')) -ForegroundColor Green
    Write-Host 'Do not click anything in ChatGPT. Wait for a new chat to open automatically.'
}
catch {
    $message = $_ | Out-String
    $message | Set-Content -LiteralPath $logPath -Encoding utf8
    Write-Host ''
    Write-Host 'PROBE REGISTRATION FAILED' -ForegroundColor Red
    Write-Host $message -ForegroundColor Red
    Write-Host ('The same error was saved to: ' + $logPath) -ForegroundColor Yellow
}
finally {
    Write-Host ''
    Read-Host 'Press Enter to close this window'
}
