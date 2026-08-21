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

However, several minutes later both `supervisor.json` and `supervisor-recovery.json` were still absent while supervisor PID `16500` was still present. This reveals the same inherited redirected-pipe hazard inside `chat-platform-supervisor.ps1`: the supervisor can launch the replacement runtime and then remain blocked waiting for inherited stdout/stderr pipes, while the qualification harness incorrectly treats the still-existing PID plus recovered manager runtime as success.

Therefore attempt 4 is **not accepted as the final physical kill/recovery gate**. The next fix must:

1. prevent supervisor Start/Stop controller mutations from capturing inheritable stdout/stderr pipes;
2. retain captured output for bounded `Status` calls only;
3. require post-recovery supervisor responsiveness plus machine-readable `supervisor.json` and `supervisor-recovery.json` evidence before qualification may emit `PASSED`;
4. preserve the existing exact-PID/new-tunnel/runtime-ready checks;
5. separately remove the visible blank console window observed when the Scheduled Task started the supposedly hidden supervisor.

The `REMOTE_METADATA_UNAVAILABLE` status observed immediately after recovery is not by itself evidence that the local recovery failed: `runtime_ready=true` and a fresh control-plane poll were present, while the independent read-only remote metadata probe was unavailable. The architecture intentionally keeps local runtime, remote metadata/control-plane, and ordinary-Chat route evidence distinct.

## Remaining physical gates

After the corrected kill/recovery gate is accepted, the remaining target-Windows gates are:

- network disconnect -> no restart storm -> reconnect -> automatic recovery;
- sleep/resume -> automatic recovery;
- reboot/logon -> supervisor automatically starts and restores desired running state;
- ordinary ChatGPT semantic call -> fresh ChatGPT E2E receipt;
- idle resource-use measurement and recovery-latency evidence.
