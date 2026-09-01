# One-shot Windows Task Scheduler probe

Prerequisite: the unpacked `CAP ChatGPT Deep-Link AutoSend` extension is already loaded in the browser profile used by `https://chatgpt.com`, ChatGPT is signed in, and `Chat Local Bridge Test` is available.

This probe intentionally creates **one** scheduled task and **one** future launch. It does not recur, retry, resume WorkingState, or rotate workers.

## Register a probe two minutes from now

From the repository root in PowerShell 7:

```powershell
$at = (Get-Date).AddMinutes(2)
./scripts/register-chatgpt-deeplink-autosend-probe.ps1 `
  -PromptBodyPath ./experiments/chatgpt-deeplink-autosend/scheduled-probe-prompt.txt `
  -At $at `
  -Force
```

Expected registration JSON includes:

```text
"logon_type":"Interactive"
"run_level":"Limited"
"registered":true
```

Do not click ChatGPT when the task fires. The expected physical path is:

```text
Windows Task Scheduler
 -> PowerShell launcher
 -> fresh run id
 -> https://chatgpt.com/?cap_autosend=1...
 -> ordinary Chat
 -> extension one-shot Send
 -> Chat Local Bridge Test
 -> workspace_read exactly once
```

The fresh chat should report:

```text
DEEPLINK_SCHEDULED_BRIDGE=PASS
CAP_AUTOSEND_RUN_ID=<fresh generated id>
```

A downstream bridge/tunnel error still proves the ordinary Chat/plugin bootstrap occurred, but it is not a successful end-to-end Bridge read.

## Inspect the scheduled task after the run

```powershell
Get-ScheduledTask -TaskName 'ChatAgentPlatform-DeepLinkAutoSend-Probe' |
  Get-ScheduledTaskInfo |
  Format-List LastRunTime,LastTaskResult,NextRunTime,NumberOfMissedRuns
```

For the launcher process itself, `LastTaskResult = 0` is the expected successful process-exit result. This does **not** prove the Chat task succeeded; the fresh Chat result is separate evidence.

## Remove the probe task

```powershell
Unregister-ScheduledTask `
  -TaskName 'ChatAgentPlatform-DeepLinkAutoSend-Probe' `
  -Confirm:$false
```

## Dry-run URL construction without opening a browser

```powershell
./scripts/launch-chatgpt-deeplink-autosend.ps1 `
  -PromptBodyPath ./experiments/chatgpt-deeplink-autosend/scheduled-probe-prompt.txt `
  -RunId autosend-manual-dryrun-001 `
  -NoLaunch
```

The launcher owns `CAP_AUTOSEND_RUN_ID=...`; prompt-body files containing their own sentinel are rejected.
