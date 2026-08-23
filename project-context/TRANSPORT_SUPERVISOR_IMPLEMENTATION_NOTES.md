# Transport Supervisor implementation notes

Status: **hard local tunnel kill/recovery accepted; external network disconnect/reconnect accepted; Windows sleep/resume accepted; Windows reboot/logon accepted; remaining physical qualification is still in progress**.

## Current implementation slice

PR #94 implements the first self-healing transport-supervisor slice around the accepted direct-stdio semantic transport. Accepted physical evidence is indexed in `project-context/EVIDENCE_INDEX.md`. The reboot/logon run and qualification-only defects are recorded in `project-context/TRANSPORT_SUPERVISOR_REBOOT_EVIDENCE.md`.

The full historical Attempt 1–11 narrative that previously lived in this file is preserved verbatim in `project-context/TRANSPORT_SUPERVISOR_ATTEMPT_HISTORY.md`. This file is now the concise current contract/status layer; the history file remains the detailed diagnostic record.

The durable transport contract remains:

- exact owned direct controller only;
- stable persistent tunnel id;
- no automatic remote tunnel CRUD;
- fail-closed auth/permission/resource-loss handling;
- transient metadata wait/re-probe;
- failure-class-aware bounded recovery;
- explicit manager lifecycle serialization so user Stop wins;
- durable recovery receipts and later heartbeat before a physical recovery is accepted.

## Accepted physical gates

### Hard local tunnel kill/recovery

Accepted exact head: `b03442b66b05bf0f51000ff43f2f386e1495a1ec`.

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-qualification\run-20260823-115911`

Exact owned tunnel PID `6812` was killed; replacement PID `4828`; same supervisor PID; recovery receipt `0 -> 1`; final `READY`; later heartbeat verified.

### External network disconnect/reconnect

Accepted exact head: `5c9e5b7bcd93fa054d99ef449d43d6d12df8c127`.

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-network-qualification\run-20260823-145633`

Offline observation produced no restart churn. After connectivity returned, one bounded runtime recovery was accepted: tunnel PID `19664 -> 15156`, supervisor PID remained `19872`, recovery `0 -> 1`, final `READY`, OpenAI readiness true, clean receipt and heartbeat.

### Windows sleep/resume

Accepted exact head: `809abf1abd8b8e79fb387feb78f347432229099c`.

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-sleep-resume-qualification\run-20260823-165435`

Physical Modern Standby `506 -> 507` lasted `20.329 s`; desired state survived; supervisor PID `3904` and tunnel PID `3540` stayed stable; recovery `0 -> 0`; runtime/OpenAI readiness and later heartbeat were verified after the required external VPN/network path was restored.

Attempt 10 on the same code head remains a preserved FAILED negative control because the external route was not restored before confirmation and the platform correctly remained fail-closed `REMOTE_TUNNEL_FORBIDDEN / blocked` without a restart storm.

### Windows reboot/logon

Accepted exact head: `27de6f6cec35df9bf0153da034d3c71da2747d44`.

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-reboot-qualification\run-20260823-180950`

Physical reboot/logon qualification proved:

- new Windows boot: `2026-08-22T03:21:03Z -> 2026-08-23T15:31:36.5Z`;
- current-user Scheduled Task principal SID verified;
- current-user logon trigger verified;
- post-logon supervisor PID `8176`;
- post-logon tunnel PID `14480`;
- bounded recovery delta `+1`;
- `runtime_ready=true`;
- `openai_ready=true`;
- later supervisor heartbeat verified.

The exact physical core emitted `TRANSPORT_SUPERVISOR_REBOOT_LOGON_QUALIFICATION_RESULT=PASSED` on the same exact prepared source/hash. The first Verify invocation exposed culture-sensitive `DateTime.Parse` on the target Windows locale; repeating the same observational Verify under `en-US` culture passed without platform mutation. The supported reboot gate now runs its core under deterministic invariant culture so regional settings cannot alter qualification semantics.

The physical Prepare also exposed a launcher-only redirected-pipe hang after the core had already written a complete `phase=prepared` receipt. The supported gate no longer redirects core stdout/stderr and therefore no longer waits on handles inherited by long-lived supervisor/tunnel descendants.

Detailed reboot evidence and defect attribution are maintained in `project-context/TRANSPORT_SUPERVISOR_REBOOT_EVIDENCE.md`.

## Recovery transaction contract

Runtime recovery alone is insufficient. Accepted recovery requires the sequence:

```text
recovery attempt started
 -> owned runtime replacement invoked
 -> post-recovery runtime health verified
 -> recovery receipt committed
 -> supervisor snapshot committed
 -> later heartbeat proves supervisor continued reconciling
```

Publication failure after runtime recovery must not authorize another destructive restart merely to recreate a missing receipt.

## Failure-class-specific backoff

Retry/backoff state belongs to the failure/recovery class that created it. A stale `wait_and_probe` deadline from remote metadata unavailability must not delay a later hard local `restart_runtime` action, while backoff created by a failed runtime restart remains authoritative for later runtime-restart attempts.

## Network reconnect contract

During a confirmed offline window the local runtime stays intact: stable supervisor PID, stable tunnel PID, no recovery increase. After connectivity returns either seamless same-process recovery or exactly one bounded runtime recovery is accepted, provided final state is healthy `READY`, recovery receipts settle cleanly, and the supervisor heartbeat advances.

## Sleep/resume contract

A physical sleep gate must prove actual Windows power-state evidence. The external VPN/proxy route is not owned by the supervisor; the operator must restore any required external path before beginning the bounded post-resume readiness window. Auth/permission/resource-loss states remain fail-closed and must not trigger destructive local restart loops.

## Reboot/logon contract

The reboot gate is two-phase and never initiates reboot itself:

```text
Prepare
 -> exact source/hash + boot time
 -> desired running owner
 -> current-user task principal/logon trigger SID
 -> supervisor/tunnel/recovery baseline
 -> durable phase=prepared receipt

manual Windows reboot + user logon

Verify (observational)
 -> genuinely newer boot time
 -> same owner receipt survived
 -> Scheduled Task ran after boot
 -> supervisor already existed before Verify
 -> runtime/OpenAI returned automatically
 -> recovery delta 0 or 1
 -> clean READY receipts
 -> later supervisor heartbeat
```

Verify must not install, start, stop, or restart Chat Agent Platform.

## Desired-state vs ownership boundary

The qualification slice still derives desired running/stopped state from the manager owner record. Before Stage 27 product integration, persist `desired_state` separately from `runtime_owner`. A missing/corrupt runtime owner must not silently rewrite user intent, and stale desired state must not authorize arbitrary controller ownership.

## Remaining gates

Transport Supervisor v1 still needs:

- fresh ordinary-ChatGPT semantic E2E receipt;
- idle resource-use and recovery-latency evidence;
- visible blank console cleanup before product integration;
- persistent `desired_state` / `runtime_owner` split before Stage 27 product integration.

Exact historical evidence remains in `EVIDENCE_INDEX.md`, `TRANSPORT_SUPERVISOR_ATTEMPT_HISTORY.md`, and the stage-specific evidence files. Acceptance is always scoped to the exact physically tested SHA, never automatically transferred to later moving heads.
