# Transport Supervisor implementation notes

Status: **implementation in progress / physical qualification not yet complete**.

## Current implementation slice

PR #94 implements the first self-healing transport-supervisor slice around the accepted direct-stdio semantic transport:

- `scripts/tunnel-reliability-health.ps1` classifies layered local/control-plane/remote health;
- `scripts/chat-platform-supervisor.ps1` owns desired-state reconciliation and bounded repair;
- `scripts/install-chat-platform-supervisor.ps1` installs the qualification supervisor as a current-user Scheduled Task;
- `scripts/transport-supervisor-qualification.ps1` performs the first target-Windows kill/recovery gate;
- automatic recovery is restricted to the exact installed direct controller;
- the persistent tunnel id remains stable and normal recovery never performs remote tunnel CRUD;
- authentication/permission/resource-loss states block destructive restart loops;
- transient remote metadata errors wait/re-probe;
- restart failures use 0/2/10/30s burst retry followed by indefinite low-rate retry with jitter.

## Durable recovery-transaction contract

A recovered runtime is not yet a completed recovery transaction. The supervisor must distinguish at least these facts:

```text
recovery attempt started
 -> owned runtime replacement invoked
 -> post-recovery runtime health verified
 -> recovery receipt committed
 -> supervisor snapshot committed
 -> later heartbeat proves supervisor continued reconciling
```

The physical gate must never infer success only from a new tunnel PID or a healthy manager status. A runtime may recover while the supervisor is blocked or unable to publish its own transaction state.

Publication failure after a verified runtime recovery is also different from runtime failure. It must **not** authorize another destructive restart of an already-ready runtime merely to recreate a missing receipt. The implementation should retry/reconcile the publication phase independently and remain idempotent.

A future persistent recovery-state schema should therefore be able to represent an in-progress/pending-publication recovery phase separately from the ordinary restart backoff count. If that representation is introduced, a later reconcile may finalize a verified pending transaction but must not fabricate attribution from ambiguous evidence.

## Desired-state vs ownership boundary

The qualification slice currently derives desired running/stopped state from the existing authoritative manager owner record. That is acceptable as a temporary compatibility seam, but it is not the final product model.

Before Stage 27 product integration, persist these as separate concepts:

```text
desired_state
  = explicit user/platform intent: running | stopped

runtime_owner
  = exact controller/runtime identity currently holding lifecycle ownership
```

A missing/corrupt owner record must not silently rewrite user intent, and stale desired state must not authorize ownership of an arbitrary controller. The supervisor must continue to re-read exact ownership under the shared lifecycle mutex before mutation so explicit Stop wins.

## Physical qualification evidence

### Attempt 1 — lifecycle race

Exact tested head `90cce25d7c6dbe5b34d28a8647f105d6defc6c8d` failed before fault injection because the qualification installer started the supervisor before the harness prepared the baseline. The supervisor and the public manager then correctly serialized on `Local\ChatAgentPlatformControllerOperation`, exposing a qualification-only race. The harness was changed to install with `-NoStart`, prepare the baseline first, and start the supervisor only afterward.

### Attempt 2 — PowerShell `$LASTEXITCODE` misuse

Exact tested head `b28fd85b4ea7678a1a50cb557c2754e41d7439c2` failed immediately after a successful PowerShell installer invocation because the qualification harness read `$LASTEXITCODE` under StrictMode even though `.ps1` invocation does not guarantee that native-process status variable is set. Evidence recorded `supervisor_started=false`, proving that fault injection had not begun. The harness now relies on terminating PowerShell errors instead of `$LASTEXITCODE` for installer calls.

### Attempt 3 — inherited redirected-pipe hang in qualification manager mutation

Exact tested head `4878476d86216b633ab4cb22a716ee61e4ed2974` established a new direct runtime but the qualification process remained blocked before supervisor start. The manager child process had exited and the replacement tunnel was alive, but the harness was still waiting on `ReadToEndAsync().GetResult()` for redirected stdout/stderr inherited by a long-lived descendant. The qualification harness now captures stdout/stderr only for `Status`; `Start`/`Stop` mutations do not create redirected pipes.

### Attempt 4 — recovery occurred, but supervisor liveness/state contract was not actually proven

Exact tested head `4cefc75c7bc61df55d16893b2ef5e956e7843e76` reached the real fault injection:

- healthy baseline was recorded with `runtime_ready=true`, `openai_ready=true`, and `health_code=READY`;
- owned tunnel PID `10076` was killed;
- the same supervisor PID `16500` remained alive;
- a new tunnel PID `10772` appeared;
- manager status recovered to `runtime_ready=true`;
- qualification wrote `summary.json` with `result=PASSED` and `tunnel_pid_changed=true` / `supervisor_pid_stable=true`.

However, several minutes later both `supervisor.json` and `supervisor-recovery.json` were still absent while supervisor PID `16500` was still present. This exposed the inherited redirected-pipe hazard inside `chat-platform-supervisor.ps1`: the supervisor could launch the replacement runtime and then remain blocked while the qualification harness incorrectly treated process existence plus recovered manager runtime as success.

Therefore attempt 4 is **not accepted**.

### Attempt 5 — strict receipt gate correctly rejected an incomplete transaction

Exact tested head `28c6ab835bbe5800f53de94c945a3407cfbde217` passed the hosted checks and local transport-supervisor tests, then reached real fault injection. The exact owned tunnel process was killed and manager status later returned fully healthy state, proving that a replacement runtime came up.

The stricter qualification correctly returned `FAILED` because it did not observe a verified post-fault recovery receipt within the bounded window:

```text
Supervisor did not publish a verified post-recovery receipt.
```

This result is important: manager/runtime recovery alone is insufficient evidence for supervisor transaction completion.

Subsequent head `dfa6c930a6a179bc3426a46275215337e77627cf` hardens the receipt path by:

- canonicalizing persisted recovery timestamps as UTC;
- making qualification timestamp comparisons type-safe;
- retrying only the atomic state-file replacement during short Windows reader-sharing races;
- separating runtime-recovery failure from post-recovery receipt publication failure;
- preserving captured output for bounded `Status` calls while keeping controller `Start`/`Stop` mutations free of redirected inheritable pipes;
- capturing live failure receipts/log tail before qualification uninstall.

This head still requires a new exact-head physical kill/recovery run. No acceptance is inferred from code review alone.

The `REMOTE_METADATA_UNAVAILABLE` state observed in earlier recovery diagnostics is not by itself evidence that local recovery failed. Local runtime, remote metadata/control-plane and ordinary-Chat route evidence remain independent dimensions.

## Required next gate

The immediate next physical gate is the same exact fault class on the current exact head:

```text
healthy baseline
 -> start supervisor
 -> kill only exact owned tunnel-client
 -> new tunnel PID
 -> same supervisor PID
 -> runtime_ready restored
 -> post-fault recovery receipt with increasing recovery count
 -> last_success_at after fault injection
 -> supervisor snapshot committed
 -> later heartbeat from same supervisor PID
```

Any missing receipt/heartbeat is failure even if the tunnel itself recovered.

## Remaining physical gates

After the corrected kill/recovery gate is accepted, the remaining target-Windows gates are:

- network disconnect -> no restart storm -> reconnect -> automatic recovery;
- sleep/resume -> automatic recovery;
- reboot/logon -> supervisor automatically starts and restores desired running state;
- ordinary ChatGPT semantic call -> fresh ChatGPT E2E receipt;
- idle resource-use measurement and recovery-latency evidence;
- remove the visible blank console window observed during Scheduled Task startup before product integration.
