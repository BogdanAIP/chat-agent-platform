# Transport Supervisor reboot/logon physical evidence

Status: **accepted**.

## Accepted physical run

Exact tested head:

`27de6f6cec35df9bf0153da034d3c71da2747d44`

Machine-local evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-reboot-qualification\run-20260823-180950`

The two-phase qualification prepared a durable pre-reboot receipt, then Windows was physically rebooted and the post-logon Verify phase ran from the same exact detached worktree/source.

Accepted observations:

- a genuinely newer Windows boot was proven: `2026-08-22T03:21:03Z -> 2026-08-23T15:31:36.5Z`;
- Scheduled Task principal SID matched the current Windows identity SID;
- the current-user logon trigger was verified;
- post-logon supervisor PID was `8176`;
- post-logon tunnel PID was `14480`;
- recovery count delta was exactly `+1`, within the bounded reboot recovery contract;
- `runtime_ready=true` after logon;
- `openai_ready=true` after logon;
- a later supervisor heartbeat was observed;
- Verify was observational and did not start/restart Chat Agent Platform.

The physical harness emitted:

```text
TRANSPORT_SUPERVISOR_REBOOT_LOGON_QUALIFICATION_RESULT=PASSED
EXACT_TESTED_HEAD=27de6f6cec35df9bf0153da034d3c71da2747d44
REBOOT_VERIFIED=True
TASK_PRINCIPAL_SID_VERIFIED=True
TASK_LOGON_TRIGGER_VERIFIED=True
RECOVERY_COUNT_DELTA=1
RUNTIME_READY_AFTER_LOGON=True
OPENAI_READY_AFTER_LOGON=True
SUPERVISOR_HEARTBEAT_VERIFIED=True
```

## Qualification-only defects discovered

The accepted physical run also exposed qualification-harness defects that are not transport-runtime failures:

1. Windows Scheduled Task identities can use different textual forms for the same account. The reboot contract now compares canonical Windows SIDs rather than raw identity strings.
2. Reboot Prepare originally attempted to inspect transport-only health fields before installing the qualification controller that exposes them. A supported reboot-gate entrypoint now bootstraps the qualification health surface first.
3. The first gate entrypoint redirected child stdout/stderr. Long-lived descendants inherited those pipes, so the launcher remained blocked after the core Prepare had already written a complete `phase=prepared` receipt. The supported gate now inherits the console instead of redirecting these pipes.
4. The exact physical Verify core parsed a persisted Windows timestamp using culture-sensitive `DateTime.Parse`; on the target Windows locale this rejected `08/22/2026 06:21:03`. The same observational Verify passed under `en-US` culture without any platform mutation. The supported gate now runs its internal core under deterministic invariant culture so regional Windows settings do not change qualification semantics.

These defects do not invalidate the accepted physical evidence because the durable Prepare receipts were complete before reboot and the successful Verify used the same exact qualification source/hash and the same physical reboot evidence. The culture compatibility rerun changed only the calling thread culture; it did not modify Chat Agent Platform state.

## Scope

This accepts the Windows reboot/logon auto-start and bounded restoration gate only. It does not by itself accept the remaining ordinary-Chat E2E, idle resource/latency, visible-console cleanup, desired-state/runtime-owner split, or Stage 27 distribution work.
