[CmdletBinding()]
param(
    [ValidateSet('Start', 'Stop', 'Status', 'Touch', 'Sweep', 'Doctor')]
    [string]$Action = 'Status',
    [string]$ConfigPath,
    [string]$ModelRoot,
    [string]$StateRoot,
    [switch]$NoWatchdog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$DefaultConfigPath = Join-Path $RepoRoot 'config\local-vision-runtime.json'
$DefaultModelRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage25\models'
$DefaultStateRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\vision-runtime'
$WatchdogScript = Join-Path $PSScriptRoot 'local-vision-runtime-watchdog.ps1'
$TestMode = ([string]$env:CHAT_VISION_RUNTIME_TEST_MODE -eq '1')

function Resolve-OptionPath {
    param([string]$Provided, [Parameter(Mandatory)][string]$Default, [Parameter(Mandatory)][string]$Name)
    if ([string]::IsNullOrWhiteSpace($Provided)) { return [IO.Path]::GetFullPath($Default) }
    if (-not $TestMode) { throw "$Name override is available only when CHAT_VISION_RUNTIME_TEST_MODE=1." }
    return [IO.Path]::GetFullPath($Provided)
}

$EffectiveConfigPath = Resolve-OptionPath -Provided $ConfigPath -Default $DefaultConfigPath -Name 'ConfigPath'
$EffectiveModelRoot = Resolve-OptionPath -Provided $ModelRoot -Default $DefaultModelRoot -Name 'ModelRoot'
$EffectiveStateRoot = Resolve-OptionPath -Provided $StateRoot -Default $DefaultStateRoot -Name 'StateRoot'
if ($NoWatchdog -and -not $TestMode) { throw 'NoWatchdog is test-only.' }

$StateFile = Join-Path $EffectiveStateRoot 'state.json'
$StdoutLog = Join-Path $EffectiveStateRoot 'llama-server.stdout.log'
$StderrLog = Join-Path $EffectiveStateRoot 'llama-server.stderr.log'
$WatchdogStdoutLog = Join-Path $EffectiveStateRoot 'watchdog.stdout.log'
$WatchdogStderrLog = Join-Path $EffectiveStateRoot 'watchdog.stderr.log'

function Initialize-StateRoot { New-Item -ItemType Directory -Force -Path $EffectiveStateRoot | Out-Null }

function Get-Config {
    if (-not (Test-Path -LiteralPath $EffectiveConfigPath -PathType Leaf)) { throw "Vision runtime config is missing: $EffectiveConfigPath" }
    try { $config = Get-Content -LiteralPath $EffectiveConfigPath -Raw -Encoding utf8 | ConvertFrom-Json }
    catch { throw "Vision runtime config is invalid JSON: $($_.Exception.Message)" }

    if ([int]$config.schema_version -ne 1) { throw 'Vision runtime config schema_version must be 1.' }
    if ([string]::IsNullOrWhiteSpace([string]$config.profile)) { throw 'Vision runtime config profile is required.' }
    if (-not $TestMode -and [string]$config.profile -ne 'lfm25-vl-450m-f16') { throw 'Production vision runtime config must use the reviewed lfm25-vl-450m-f16 profile.' }
    if ([string]$config.runtime.host -ne '127.0.0.1') { throw 'Vision runtime must bind only to 127.0.0.1.' }

    $port = [int]$config.runtime.port
    if ($port -lt 1 -or $port -gt 65535) { throw 'Vision runtime port must be between 1 and 65535.' }
    $readyTimeout = [int]$config.runtime.ready_timeout_seconds
    if ($readyTimeout -lt 5 -or $readyTimeout -gt 300) { throw 'ready_timeout_seconds must be between 5 and 300.' }
    $ttl = [int]$config.idle_ttl_seconds
    $watchdogInterval = [int]$config.watchdog_interval_seconds
    if ($ttl -lt 2 -or $ttl -gt 3600) { throw 'idle_ttl_seconds must be between 2 and 3600.' }
    if ($watchdogInterval -lt 1 -or $watchdogInterval -gt 60 -or $watchdogInterval -gt $ttl) { throw 'watchdog_interval_seconds must be between 1 and 60 and not exceed idle TTL.' }

    foreach ($name in @('min_start_physical_gb','min_start_virtual_gb','min_run_physical_gb','min_run_virtual_gb')) {
        $value = [double]$config.memory.$name
        if ($value -lt 0.01 -or $value -gt 64.0) { throw "Invalid memory policy value: $name" }
    }
    if (-not $TestMode) {
        if ([double]$config.memory.min_start_physical_gb -lt 1.50) { throw 'Production min_start_physical_gb must remain at least 1.50 GB until target acceptance changes it.' }
        if ([double]$config.memory.min_start_virtual_gb -lt 3.00) { throw 'Production min_start_virtual_gb must remain at least 3.00 GB until target acceptance changes it.' }
    }

    $serverArgs = @($config.server_args | ForEach-Object { [string]$_ })
    $joined = $serverArgs -join ' '
    foreach ($required in @('--device none','--gpu-layers 0','--ctx-size 2048','--threads 8','--parallel 1','--offline')) {
        if (-not $TestMode -and $joined -notmatch [regex]::Escape($required)) { throw "Production server_args lost required reviewed marker: $required" }
    }
    foreach ($forbidden in @('--host','--port','-m ','--model','--mmproj')) {
        if ($joined -match [regex]::Escape($forbidden)) { throw "server_args must not override controller-owned runtime/artifact argument: $forbidden" }
    }
    return $config
}

function Get-ArtifactPaths {
    param([Parameter(Mandatory)]$Config)
    $directory = [string]$Config.artifacts.directory
    $modelFile = [string]$Config.artifacts.model.file
    $mmprojFile = [string]$Config.artifacts.mmproj.file
    foreach ($value in @($directory,$modelFile,$mmprojFile)) {
        if ([string]::IsNullOrWhiteSpace($value) -or [IO.Path]::IsPathRooted($value) -or $value -match '(^|[\\/])\.\.?(?:[\\/]|$)') { throw 'Artifact paths in reviewed config must be non-empty relative paths without dot traversal.' }
    }
    $dir = Join-Path $EffectiveModelRoot $directory
    return [pscustomobject]@{ model = Join-Path $dir $modelFile; mmproj = Join-Path $dir $mmprojFile }
}

function Test-Artifact {
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][int64]$ExpectedBytes,[Parameter(Mandatory)][string]$ExpectedSha256,[Parameter(Mandatory)][string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Label artifact is missing: $Path" }
    $item = Get-Item -LiteralPath $Path
    if ([int64]$item.Length -ne $ExpectedBytes) { throw "$Label artifact byte-size mismatch. Expected $ExpectedBytes, got $($item.Length)." }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $ExpectedSha256.ToLowerInvariant()) { throw "$Label artifact SHA256 mismatch." }
    return $actual
}

function Confirm-Artifacts {
    param([Parameter(Mandatory)]$Config)
    $paths = Get-ArtifactPaths -Config $Config
    $modelSha = Test-Artifact -Path $paths.model -ExpectedBytes ([int64]$Config.artifacts.model.bytes) -ExpectedSha256 ([string]$Config.artifacts.model.sha256) -Label 'model'
    $mmprojSha = Test-Artifact -Path $paths.mmproj -ExpectedBytes ([int64]$Config.artifacts.mmproj.bytes) -ExpectedSha256 ([string]$Config.artifacts.mmproj.sha256) -Label 'mmproj'
    return [pscustomobject]@{ model_path=[IO.Path]::GetFullPath($paths.model); mmproj_path=[IO.Path]::GetFullPath($paths.mmproj); model_sha256=$modelSha; mmproj_sha256=$mmprojSha }
}

function Resolve-RuntimeExecutable {
    param([Parameter(Mandatory)]$Config)
    $command = [string]$Config.runtime.command
    if ([string]::IsNullOrWhiteSpace($command)) { throw 'runtime.command is required.' }
    if ([IO.Path]::IsPathRooted($command)) {
        if (-not $TestMode) { throw 'Production runtime.command must resolve by reviewed command name, not an arbitrary absolute path.' }
        if (-not (Test-Path -LiteralPath $command -PathType Leaf)) { throw "Runtime executable not found: $command" }
        return [IO.Path]::GetFullPath($command)
    }
    if (-not $TestMode -and $command -ne 'llama-server') { throw 'Production runtime.command must be llama-server.' }
    return [IO.Path]::GetFullPath((Get-Command $command -ErrorAction Stop).Source)
}

function Get-CommandPrefix {
    param([Parameter(Mandatory)]$Config)
    if ($null -eq $Config.runtime.PSObject.Properties['command_prefix']) { return @() }
    $prefix = @($Config.runtime.command_prefix | ForEach-Object { [string]$_ })
    if ($prefix.Count -gt 0 -and -not $TestMode) { throw 'runtime.command_prefix is test-only.' }
    return $prefix
}

function Confirm-RuntimeVersion {
    param([Parameter(Mandatory)]$Config,[Parameter(Mandatory)][string]$Executable)
    $prefix = @(Get-CommandPrefix -Config $Config)
    $output = @(& $Executable @prefix '--version' 2>&1) | Out-String
    if ($LASTEXITCODE -ne 0) { throw "Vision runtime --version failed: $($output.Trim())" }
    foreach ($marker in @($Config.runtime.required_version_markers | ForEach-Object { [string]$_ })) {
        if ([string]::IsNullOrWhiteSpace($marker) -or $output -notmatch [regex]::Escape($marker)) { throw "Vision runtime version output is missing required marker: $marker" }
    }
    return $output.Trim()
}

function Get-MemorySnapshot {
    $os = Get-CimInstance Win32_OperatingSystem
    return [pscustomobject]@{ physical_gb=[math]::Round((($os.FreePhysicalMemory*1KB)/1GB),3); virtual_gb=[math]::Round((($os.FreeVirtualMemory*1KB)/1GB),3) }
}

function Test-MemoryFloor {
    param([Parameter(Mandatory)]$Memory,[Parameter(Mandatory)][double]$PhysicalFloor,[Parameter(Mandatory)][double]$VirtualFloor)
    return ($Memory.physical_gb -ge $PhysicalFloor -and $Memory.virtual_gb -ge $VirtualFloor)
}

function Get-PortListeners {
    param([Parameter(Mandatory)][int]$Port)
    if ($null -eq (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue)) { return @() }
    return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Get-State {
    if (-not (Test-Path -LiteralPath $StateFile -PathType Leaf)) { return $null }
    try { return Get-Content -LiteralPath $StateFile -Raw -Encoding utf8 | ConvertFrom-Json }
    catch { throw "Vision runtime state is invalid: $($_.Exception.Message)" }
}

function Save-State {
    param([Parameter(Mandatory)]$State)
    Initialize-StateRoot
    $tmp = "$StateFile.new"
    $State | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $tmp -Encoding utf8
    Move-Item -LiteralPath $tmp -Destination $StateFile -Force
}
function Remove-State { Remove-Item -LiteralPath $StateFile -Force -ErrorAction SilentlyContinue }

function Get-StringSha256 {
    param([Parameter(Mandatory)][string]$Value)
    $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [Convert]::ToHexString($sha.ComputeHash($bytes)).ToLowerInvariant() }
    finally { $sha.Dispose(); [Array]::Clear($bytes,0,$bytes.Length) }
}

function Get-ProcessIdentity {
    param([Parameter(Mandatory)][int]$ProcessId)
    $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $cim) { return $null }
    $exe = [string]$cim.ExecutablePath
    $commandLine = [string]$cim.CommandLine
    if ([string]::IsNullOrWhiteSpace($exe) -or [string]::IsNullOrWhiteSpace($commandLine)) { return $null }
    try { $exe = [IO.Path]::GetFullPath($exe) } catch { return $null }
    try { $start = (Get-Process -Id $ProcessId -ErrorAction Stop).StartTime.ToUniversalTime().ToString('o') } catch { return $null }
    return [pscustomobject]@{ executable=$exe; command_line_sha256=(Get-StringSha256 -Value $commandLine); process_start_time_utc=$start }
}

function Test-OwnedServerProcess {
    param([Parameter(Mandatory)]$State)
    $identity = Get-ProcessIdentity -ProcessId ([int]$State.pid)
    if ($null -eq $identity -or $null -eq $State.PSObject.Properties['process_command_sha256']) { return $false }
    return (
        [string]$identity.executable -ieq [IO.Path]::GetFullPath([string]$State.runtime_executable) -and
        [string]$identity.command_line_sha256 -eq [string]$State.process_command_sha256 -and
        [string]$identity.process_start_time_utc -eq [string]$State.process_start_time_utc
    )
}

function Contains-CommandMarker {
    param([string]$CommandLine,[string]$Marker)
    if ([string]::IsNullOrWhiteSpace($CommandLine) -or [string]::IsNullOrWhiteSpace($Marker)) { return $false }
    return ($CommandLine.IndexOf($Marker,[StringComparison]::OrdinalIgnoreCase) -ge 0)
}

function Test-OwnedWatchdogProcess {
    param([Parameter(Mandatory)]$State)
    if ($null -eq $State.PSObject.Properties['watchdog_pid'] -or $null -eq $State.watchdog_pid) { return $false }
    $watchdogPid = [int]$State.watchdog_pid
    if ($watchdogPid -eq $PID) { return $true }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$watchdogPid" -ErrorAction SilentlyContinue
    if ($null -eq $process -or [string]$process.Name -notmatch '^pwsh(\.exe)?$') { return $false }
    return ((Contains-CommandMarker -CommandLine ([string]$process.CommandLine) -Marker $WatchdogScript) -and (Contains-CommandMarker -CommandLine ([string]$process.CommandLine) -Marker $EffectiveStateRoot))
}

function Test-Health {
    param([Parameter(Mandatory)][int]$Port)
    try { $response=Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2 -SkipHttpErrorCheck; return ($response.StatusCode -eq 200) }
    catch { return $false }
}

function Get-StatusObject {
    param([Parameter(Mandatory)]$Config)
    $state=Get-State; $port=[int]$Config.runtime.port; $listeners=@(Get-PortListeners -Port $port)
    if ($null -eq $state) { return [pscustomobject]@{profile=[string]$Config.profile;running=$false;ready=$false;conflict=($listeners.Count -gt 0);pid=$null;watchdog_pid=$null;port=$port;idle_seconds=$null;state='stopped'} }
    $owned=Test-OwnedServerProcess -State $state
    $processExists=($null -ne (Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue))
    $conflict=($processExists -and -not $owned); $ready=($owned -and (Test-Health -Port $port)); $idle=$null
    try { $last=[DateTimeOffset]::Parse([string]$state.last_used_at); $idle=[math]::Max(0,[math]::Round(([DateTimeOffset]::UtcNow-$last).TotalSeconds,1)) } catch {}
    return [pscustomobject]@{profile=[string]$state.profile;running=$owned;ready=$ready;conflict=$conflict;pid=[int]$state.pid;watchdog_pid=$state.watchdog_pid;port=$port;idle_seconds=$idle;state=if($conflict){'ownership-conflict'}elseif($ready){'ready'}elseif($owned){'starting-or-unhealthy'}else{'stale'}}
}

function Stop-Watchdog {
    param([Parameter(Mandatory)]$State)
    if (-not (Test-OwnedWatchdogProcess -State $State)) { return }
    $watchdogPid=[int]$State.watchdog_pid
    if ($watchdogPid -ne $PID) { Stop-Process -Id $watchdogPid -Force -ErrorAction SilentlyContinue }
}

function Stop-OwnedRuntime {
    param([Parameter(Mandatory)]$Config,[string]$Reason='explicit-stop')
    $state=Get-State
    if ($null -eq $state) { return [pscustomobject]@{stopped=$true;reason='already-stopped'} }
    Stop-Watchdog -State $state
    $processExists=($null -ne (Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue))
    if ($processExists -and -not (Test-OwnedServerProcess -State $state)) { throw 'Vision runtime ownership mismatch. Refusing to terminate an unverified process.' }
    if ($processExists) {
        Stop-Process -Id ([int]$state.pid) -Force -ErrorAction Stop
        for($i=0;$i-lt50;$i++){if($null -eq (Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue)){break};Start-Sleep -Milliseconds 100}
        if($null -ne (Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue)){throw 'Owned vision runtime process did not stop.'}
    }
    Remove-State
    return [pscustomobject]@{stopped=$true;reason=$Reason}
}

function Quote-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)
    if ($Value.Contains('"')) { throw 'Vision runtime process arguments must not contain a double quote.' }
    if ($Value -notmatch '\s') { return $Value }
    return '"' + $Value + '"'
}

function Start-Watchdog {
    param([Parameter(Mandatory)]$Config)
    if ($NoWatchdog) { return $null }
    if (-not (Test-Path -LiteralPath $WatchdogScript -PathType Leaf)) { throw "Vision runtime watchdog script is missing: $WatchdogScript" }
    $pwsh=(Get-Command pwsh.exe -ErrorAction Stop).Source
    $args=@('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',$WatchdogScript,'-ControllerPath',$PSCommandPath,'-ConfigPath',$EffectiveConfigPath,'-ModelRoot',$EffectiveModelRoot,'-StateRoot',$EffectiveStateRoot,'-IntervalSeconds',[string][int]$Config.watchdog_interval_seconds)
    $line=($args | ForEach-Object { Quote-ProcessArgument -Value ([string]$_) }) -join ' '
    Remove-Item $WatchdogStdoutLog,$WatchdogStderrLog -Force -ErrorAction SilentlyContinue
    return Start-Process -FilePath $pwsh -ArgumentList $line -WindowStyle Hidden -RedirectStandardOutput $WatchdogStdoutLog -RedirectStandardError $WatchdogStderrLog -PassThru
}

function Start-Runtime {
    param([Parameter(Mandatory)]$Config)
    Initialize-StateRoot
    $existing=Get-State
    if($null -ne $existing){
        if(Test-OwnedServerProcess -State $existing){
            if(Test-Health -Port ([int]$Config.runtime.port)){$existing.last_used_at=[DateTimeOffset]::UtcNow.ToString('o');Save-State -State $existing;return Get-StatusObject -Config $Config}
            $null=Stop-OwnedRuntime -Config $Config -Reason 'unhealthy-restart'
        } else {
            $exists=($null -ne (Get-Process -Id ([int]$existing.pid) -ErrorAction SilentlyContinue))
            if($exists){throw 'Existing vision runtime state points to an unverified live process. Refusing ambiguous startup.'}
            Stop-Watchdog -State $existing;Remove-State
        }
    }
    if(@(Get-PortListeners -Port ([int]$Config.runtime.port)).Count -gt 0){throw "Vision runtime port $($Config.runtime.port) is occupied by an unowned listener."}
    $memory=Get-MemorySnapshot
    if(-not(Test-MemoryFloor -Memory $memory -PhysicalFloor ([double]$Config.memory.min_start_physical_gb) -VirtualFloor ([double]$Config.memory.min_start_virtual_gb))){throw "Vision runtime admission denied: free physical=$($memory.physical_gb) GB, virtual=$($memory.virtual_gb) GB."}
    $artifacts=Confirm-Artifacts -Config $Config; $resolvedRuntime=Resolve-RuntimeExecutable -Config $Config; $version=Confirm-RuntimeVersion -Config $Config -Executable $resolvedRuntime
    $args=[System.Collections.Generic.List[string]]::new(); foreach($v in @(Get-CommandPrefix -Config $Config)){$args.Add([string]$v)}; foreach($v in @('-m',$artifacts.model_path,'--mmproj',$artifacts.mmproj_path)){$args.Add([string]$v)}; foreach($v in @($Config.server_args|ForEach-Object{[string]$_})){$args.Add([string]$v)}; foreach($v in @('--host','127.0.0.1','--port',[string][int]$Config.runtime.port)){$args.Add([string]$v)}
    $argLine=(@($args)|ForEach-Object{Quote-ProcessArgument -Value ([string]$_)}) -join ' '
    Remove-Item $StdoutLog,$StderrLog -Force -ErrorAction SilentlyContinue
    $process=Start-Process -FilePath $resolvedRuntime -ArgumentList $argLine -WindowStyle Hidden -RedirectStandardOutput $StdoutLog -RedirectStandardError $StderrLog -PassThru
    $identity=$null
    for($i=0;$i-lt40;$i++){ $identity=Get-ProcessIdentity -ProcessId $process.Id; if($null -ne $identity){break}; Start-Sleep -Milliseconds 50 }
    if($null -eq $identity){try{Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue}catch{};throw 'Could not capture owned vision runtime process identity after start.'}
    $state=[pscustomobject][ordered]@{schema_version=2;owner='chat-agent-platform-vision-runtime';profile=[string]$Config.profile;pid=[int]$process.Id;process_start_time_utc=[string]$identity.process_start_time_utc;process_command_sha256=[string]$identity.command_line_sha256;runtime_executable=[string]$identity.executable;runtime_requested_executable=$resolvedRuntime;runtime_version=$version;model_path=$artifacts.model_path;model_sha256=$artifacts.model_sha256;mmproj_path=$artifacts.mmproj_path;mmproj_sha256=$artifacts.mmproj_sha256;host='127.0.0.1';port=[int]$Config.runtime.port;started_at=[DateTimeOffset]::UtcNow.ToString('o');last_used_at=[DateTimeOffset]::UtcNow.ToString('o');idle_ttl_seconds=[int]$Config.idle_ttl_seconds;watchdog_pid=$null}
    Save-State -State $state
    $ready=$false;$deadline=[DateTimeOffset]::UtcNow.AddSeconds([int]$Config.runtime.ready_timeout_seconds)
    while([DateTimeOffset]::UtcNow -lt $deadline){if($process.HasExited){break};if(Test-Health -Port ([int]$Config.runtime.port)){$ready=$true;break};Start-Sleep -Milliseconds 250}
    if(-not $ready){$tail=if(Test-Path $StderrLog){(Get-Content $StderrLog -Tail 60|Out-String).Trim()}else{''};$null=Stop-OwnedRuntime -Config $Config -Reason 'readiness-failed';throw "Vision runtime did not become ready. $tail"}
    $post=Get-MemorySnapshot
    if(-not(Test-MemoryFloor -Memory $post -PhysicalFloor ([double]$Config.memory.min_run_physical_gb) -VirtualFloor ([double]$Config.memory.min_run_virtual_gb))){$null=Stop-OwnedRuntime -Config $Config -Reason 'post-start-memory-floor';throw "Vision runtime started but violated run memory floor: physical=$($post.physical_gb) GB, virtual=$($post.virtual_gb) GB."}
    $watchdog=Start-Watchdog -Config $Config
    if($null -ne $watchdog){$state=Get-State;$state.watchdog_pid=[int]$watchdog.Id;Save-State -State $state}
    return Get-StatusObject -Config $Config
}

function Touch-Runtime {
    param([Parameter(Mandatory)]$Config)
    $state=Get-State
    if($null -eq $state){throw 'Vision runtime is not running.'}
    if(-not(Test-OwnedServerProcess -State $state)){throw 'Vision runtime ownership cannot be verified.'}
    if(-not(Test-Health -Port ([int]$Config.runtime.port))){throw 'Vision runtime is not healthy.'}
    $state.last_used_at=[DateTimeOffset]::UtcNow.ToString('o')
    Save-State -State $state
    return Get-StatusObject -Config $Config
}

function Sweep-Runtime {
    param([Parameter(Mandatory)]$Config)
    $state=Get-State
    if($null -eq $state){return Get-StatusObject -Config $Config}
    if(-not(Test-OwnedServerProcess -State $state)){
        $exists=($null -ne (Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue))
        if($exists){throw 'Vision runtime ownership mismatch during sweep. Refusing to terminate an unverified process.'}
        Stop-Watchdog -State $state;Remove-State;return Get-StatusObject -Config $Config
    }
    $memory=Get-MemorySnapshot
    if(-not(Test-MemoryFloor -Memory $memory -PhysicalFloor ([double]$Config.memory.min_run_physical_gb) -VirtualFloor ([double]$Config.memory.min_run_virtual_gb))){$null=Stop-OwnedRuntime -Config $Config -Reason 'resource-pressure';return Get-StatusObject -Config $Config}
    $last=[DateTimeOffset]::Parse([string]$state.last_used_at)
    if(([DateTimeOffset]::UtcNow-$last).TotalSeconds -ge [int]$Config.idle_ttl_seconds){$null=Stop-OwnedRuntime -Config $Config -Reason 'idle-ttl'}
    return Get-StatusObject -Config $Config
}

function Get-DoctorObject {
    param([Parameter(Mandatory)]$Config)
    $artifacts=Confirm-Artifacts -Config $Config;$runtime=Resolve-RuntimeExecutable -Config $Config;$version=Confirm-RuntimeVersion -Config $Config -Executable $runtime;$memory=Get-MemorySnapshot
    return [pscustomobject]@{profile=[string]$Config.profile;runtime_executable=$runtime;runtime_version=$version;model_path=$artifacts.model_path;model_sha256=$artifacts.model_sha256;mmproj_path=$artifacts.mmproj_path;mmproj_sha256=$artifacts.mmproj_sha256;physical_free_gb=$memory.physical_gb;virtual_free_gb=$memory.virtual_gb;admission_ready=(Test-MemoryFloor -Memory $memory -PhysicalFloor ([double]$Config.memory.min_start_physical_gb) -VirtualFloor ([double]$Config.memory.min_start_virtual_gb));host='127.0.0.1';port=[int]$Config.runtime.port;idle_ttl_seconds=[int]$Config.idle_ttl_seconds}
}

$mutexName=if($TestMode){$bytes=[Text.Encoding]::UTF8.GetBytes($EffectiveStateRoot);$sha=[Security.Cryptography.SHA256]::Create();try{'Local\ChatAgentPlatformVisionRuntime-'+([Convert]::ToHexString($sha.ComputeHash($bytes))).Substring(0,12)}finally{$sha.Dispose()}}else{'Local\ChatAgentPlatformVisionRuntime'}
$mutex=[Threading.Mutex]::new($false,$mutexName);$acquired=$false
try{
    try{$acquired=$mutex.WaitOne(30000)}catch[Threading.AbandonedMutexException]{$acquired=$true}
    if(-not $acquired){throw 'Timed out waiting for the vision runtime operation mutex.'}
    $config=Get-Config
    $result=switch($Action){
        'Start'{Start-Runtime -Config $config}
        'Stop'{$null=Stop-OwnedRuntime -Config $config -Reason 'explicit-stop';Get-StatusObject -Config $config}
        'Status'{Get-StatusObject -Config $config}
        'Touch'{Touch-Runtime -Config $config}
        'Sweep'{Sweep-Runtime -Config $config}
        'Doctor'{Get-DoctorObject -Config $config}
    }
    $result|ConvertTo-Json -Depth 8
} finally {
    if($acquired){try{$mutex.ReleaseMutex()}catch{}}
    $mutex.Dispose()
}
