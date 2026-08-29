[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PromptBodyPath,

    [Parameter(Mandatory = $true)]
    [datetime]$At,

    [string]$TaskName = 'ChatAgentPlatform-DeepLinkAutoSend-Probe',

    [switch]$Force,

    [switch]$NoRegister
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'Windows Task Scheduler registration is supported only on Windows.'
}
if ($At -le (Get-Date).AddSeconds(15)) {
    throw 'At must be at least 15 seconds in the future.'
}
if ([string]::IsNullOrWhiteSpace($TaskName) -or $TaskName.Length -gt 180) {
    throw 'TaskName must be non-empty and at most 180 characters.'
}

$resolvedPromptPath = (Resolve-Path -LiteralPath $PromptBodyPath).Path
$launcherPath = Join-Path $PSScriptRoot 'launch-chatgpt-deeplink-autosend.ps1'
if (-not (Test-Path -LiteralPath $launcherPath -PathType Leaf)) {
    throw "Launcher not found: $launcherPath"
}

function Quote-TaskArgument {
    param([Parameter(Mandatory = $true)][string]$Value)
    if ($Value.Contains('"')) {
        throw 'Task argument paths containing a double quote are not supported.'
    }
    return '"' + $Value + '"'
}

$pwsh = (Get-Command pwsh.exe -ErrorAction Stop).Source
$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$argument = @(
    '-NoLogo'
    '-NoProfile'
    '-File'
    (Quote-TaskArgument -Value $launcherPath)
    '-PromptBodyPath'
    (Quote-TaskArgument -Value $resolvedPromptPath)
) -join ' '

$spec = [ordered]@{
    task_name = $TaskName
    at = $At.ToString('o')
    user = $userId
    logon_type = 'Interactive'
    run_level = 'Limited'
    executable = $pwsh
    arguments = $argument
    prompt_path = $resolvedPromptPath
    launcher_path = $launcherPath
    registered = $false
}

if (-not $NoRegister) {
    Import-Module ScheduledTasks -ErrorAction Stop

    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $existing -and -not $Force) {
        throw "Scheduled task '$TaskName' already exists. Use -Force only when replacing that explicit probe task is intended."
    }
    if ($null -ne $existing -and $Force) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    $action = New-ScheduledTaskAction -Execute $pwsh -Argument $argument
    $trigger = New-ScheduledTaskTrigger -Once -At $At
    $principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 2)

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description 'Experimental one-shot ordinary-ChatGPT deep-link autosend probe. No recurrence or retry.' | Out-Null

    $spec.registered = $true
}

$spec | ConvertTo-Json -Compress
