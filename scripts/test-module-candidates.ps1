param(
    [int]$FilesystemPort = 3061,
    [int]$PlaywrightPort = 3062
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pkg = '@1mcp/agent@0.34.4'

function Stop-CandidateRuntime {
    param([Parameter(Mandatory)] [string]$ConfigPath)
    & npx.cmd -y $pkg serve --config $ConfigPath --stop *> $null
    if ($LASTEXITCODE -notin @(0, 3, 7)) {
        Write-Warning "1MCP cleanup returned exit code $LASTEXITCODE for $ConfigPath"
    }
}

function Start-CandidateRuntime {
    param(
        [Parameter(Mandatory)] [string]$ConfigPath,
        [Parameter(Mandatory)] [int]$Port,
        [Parameter(Mandatory)] [string]$ServerName
    )

    Stop-CandidateRuntime -ConfigPath $ConfigPath

    & npx.cmd -y $pkg serve `
        --config $ConfigPath `
        --host 127.0.0.1 `
        --port $Port `
        --health-info-level minimal `
        --enable-async-loading `
        --background
    if ($LASTEXITCODE -ne 0) {
        throw "1MCP failed to start candidate '$ServerName'."
    }

    $healthUri = "http://127.0.0.1:$Port/health/mcp/$ServerName"
    for ($attempt = 1; $attempt -le 90; $attempt++) {
        try {
            $health = Invoke-RestMethod -Method Get -Uri $healthUri -TimeoutSec 5
            if ([string]$health.state -eq 'ready') {
                return
            }
        }
        catch {}
        Start-Sleep -Seconds 1
    }

    throw "Candidate '$ServerName' did not become ready: $healthUri"
}

function Invoke-1McpText {
    param(
        [Parameter(Mandatory)] [string[]]$Arguments
    )
    $output = & npx.cmd -y $pkg @Arguments 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "1MCP command failed ($LASTEXITCODE): $($Arguments -join ' ')`n$output"
    }
    return $output
}

Push-Location $repoRoot
try {
    Write-Host '=== Filesystem candidate: read-only scoped root ===' -ForegroundColor Cyan
    $filesystemConfig = (Resolve-Path 'runtime/candidates/filesystem-readonly.json').Path
    $filesRoot = Join-Path ([System.IO.Path]::GetTempPath()) "chat-local-files-$PID"
    New-Item -ItemType Directory -Force -Path $filesRoot | Out-Null
    $marker = Join-Path $filesRoot 'candidate-marker.txt'
    Set-Content -Path $marker -Value 'FILESYSTEM_CANDIDATE_OK' -Encoding utf8
    $env:CHAT_LOCAL_FILES_ROOT = $filesRoot

    try {
        Start-CandidateRuntime -ConfigPath $filesystemConfig -Port $FilesystemPort -ServerName 'filesystem'
        $baseUrl = "http://127.0.0.1:$FilesystemPort"

        $inventory = Invoke-1McpText -Arguments @('inspect', 'filesystem', '--url', $baseUrl, '--format', 'json', '--all')
        foreach ($forbidden in @('write_file', 'edit_file', 'move_file', 'create_directory')) {
            if ($inventory -match [regex]::Escape($forbidden)) {
                throw "Read-only filesystem candidate exposed forbidden tool '$forbidden'."
            }
        }
        foreach ($required in @('read_text_file', 'list_allowed_directories')) {
            if ($inventory -notmatch [regex]::Escape($required)) {
                throw "Filesystem candidate is missing required tool '$required'."
            }
        }

        $readArgs = (@{ path = $marker } | ConvertTo-Json -Compress)
        $readResult = Invoke-1McpText -Arguments @('run', 'filesystem/read_text_file', '--url', $baseUrl, '--args', $readArgs, '--format', 'text')
        if ($readResult -notmatch 'FILESYSTEM_CANDIDATE_OK') {
            throw 'Filesystem candidate did not return the expected marker content.'
        }

        Write-Host 'FILESYSTEM_CANDIDATE=passed' -ForegroundColor Green
    }
    finally {
        Stop-CandidateRuntime -ConfigPath $filesystemConfig
        Remove-Item Env:CHAT_LOCAL_FILES_ROOT -ErrorAction SilentlyContinue
        Remove-Item $filesRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host '=== Playwright candidate: isolated headless browser ===' -ForegroundColor Cyan
    $playwrightConfig = (Resolve-Path 'runtime/candidates/playwright-headless.json').Path
    try {
        Start-CandidateRuntime -ConfigPath $playwrightConfig -Port $PlaywrightPort -ServerName 'playwright'
        $baseUrl = "http://127.0.0.1:$PlaywrightPort"

        $inventory = Invoke-1McpText -Arguments @('inspect', 'playwright', '--url', $baseUrl, '--format', 'json', '--all')
        if ($inventory -notmatch 'browser_navigate') {
            throw 'Playwright candidate did not expose browser_navigate.'
        }

        $page = 'data:text/html,<html><body><h1>PLAYWRIGHT_CANDIDATE_OK</h1></body></html>'
        $navigateArgs = (@{ url = $page } | ConvertTo-Json -Compress)
        $navigateResult = Invoke-1McpText -Arguments @('run', 'playwright/browser_navigate', '--url', $baseUrl, '--args', $navigateArgs, '--format', 'text')
        if ($navigateResult -notmatch 'PLAYWRIGHT_CANDIDATE_OK') {
            throw 'Playwright candidate navigation did not return the expected accessibility snapshot.'
        }

        Invoke-1McpText -Arguments @('run', 'playwright/browser_close', '--url', $baseUrl, '--format', 'text') | Out-Null
        Write-Host 'PLAYWRIGHT_CANDIDATE=passed' -ForegroundColor Green
    }
    finally {
        Stop-CandidateRuntime -ConfigPath $playwrightConfig
    }
}
finally {
    Pop-Location
}
