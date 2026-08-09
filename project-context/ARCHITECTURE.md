# Architecture

## Target architecture

Chat является primary intelligence. Один локальный Rust binary `agent-platform.exe` превращает намерение Chat в проверяемое выполнение через explicit Project Binding, versioned contracts и fail-closed policy. Зрелые программы остаются заменяемыми edge-инструментами; они не становятся core dependency без необходимости.

```text
Chat / Codex
    |
    +-- GitHub: source/project context
    |
    `-- optional remote tool call
            |
            v
      Yandex API Gateway
            |
            v
      Yandex Cloud Function
            |
            v
      Object Storage JSON rendezvous
            |
            | outbound long poll
            v
agent-platform.exe
    |-- Project Binding / bootstrap
    |-- capability requirements + tool lock
    |-- Policy Enforcement Point
    |-- guarded ConfirmationStore
    |-- ArtifactStore
    |-- JobStore
    |-- SecretStore -> Windows Credential Manager
    |
    +-- rust.local.ffmpeg -> FFmpeg/FFprobe CLI
    +-- rust.local.reaper -> limited Lua/ReaScript -> REAPER
    `-- edge.python.matchering -> fixed adapter -> Matchering 2.0.6
```

## Core invariants

### One local core, not a service zoo

Project policy, artifact identity, job state, secret ACL and confirmation authority live in the Rust core. Redis, database, message broker, separate workflow engine, VPS and permanent supervisor are not baseline dependencies.

A new process/service is allowed only when an independent lifecycle requirement proves that in-process/file-backed state is insufficient.

### Configuration must be executable, not decorative

`config/tools.yaml`, `tool-lock.yaml` and `capability-requirements.yaml` are parsed fail-closed. Unknown fields are rejected. Locked selection technically enforces enabled state, quality, reliability, determinism, execution path, fallback agreement and request cost.

QC/skill/acceptance declarations are explicitly evidence metadata; they are proved through tests/health instead of pretending to be generic runtime rules.

`runtime/capability-profile.json` is generated from the same locked selections and cannot maintain a separate hand-written capability list.

### Process exact bytes

Filesystem inputs are captured into an immutable Artifact Store snapshot. Policy/idempotency identity is checked against the SHA-256 of that snapshot before processing. Workflow code must process the registered snapshot, not reopen an untrusted original path later.

### One job, one physical executor

Idempotent `begin` returns one persisted job. A per-job OS file lock is then held for the duration of actual workflow execution, preventing two Chat tabs/processes from running the same DSP operation concurrently. Job state/checkpoints survive process failure and can resume after the OS releases the lock.

### External side effects require one-use authority

A guarded PEP decision creates a stable `confirmation_binding` over the action. `ConfirmationStore` prepares a short-lived record; before execution the action is re-evaluated through policy and the exact binding is atomically consumed into a non-clone `ConfirmationPermit`.

Changing artifact hash/destination/parameters invalidates the confirmation. Replay, expiry and concurrent double-consume fail closed. External adapters must consume the permit by value; simply possessing a prepared record is not authority.

### Edge tools remain typed

- FFmpeg: fixed typed operations; no arbitrary argument array from Chat.
- REAPER: generated limited Lua/ReaScript; no `os.execute`, `io.popen` or generic action dispatcher.
- Matchering: pinned Python package and fixed `probe/process` adapter only.
- Browser/video/distribution: conditional future adapters under the same contracts.

### Cloud transport is intentionally thin

Stage 4 uses a permanent **Yandex API Gateway** endpoint as the public Chat/GPT Actions ingress. The Gateway invokes a Yandex Cloud Function, which keeps only relay/auth/rendezvous logic and uses Object Storage for task/result/heartbeat JSON. The Windows binary makes outbound HTTPS long polls; no inbound Windows port/NAT change is required.

The API Gateway is not optional decoration. Direct Yandex Function invocation consumes `Authorization` for the cloud platform itself, so it cannot reliably carry the arbitrary GPT Actions `Authorization: Bearer <remote-token>` header. The Gateway preserves that external Bearer contract while invoking the Function internally.

Cloud state contains only task/result/heartbeat JSON. Task/result rendezvous is immutable by request ID; deadline and result existence define state without relying on Python instance serialization. The cloud has no media files, FFmpeg, REAPER, Matchering or business workflow logic.

Two independent credentials remain mandatory:

- remote GPT/MCP Bearer -> checked by the Function after passing through API Gateway;
- local `AGENT_TOKEN` -> stored in Windows Credential Manager and sent by the explicit Windows relay.

Normal redeployments may reuse the current pair; explicit `-RotateTokens` rotates both. Neither token belongs in Git, OpenAPI, acceptance evidence or chat text.

The relay is off by default and currently exports only `local_ping` and `runtime_self_test`.

Evidence status:

- hosted Stage 4 CI is green;
- real Yandex API Gateway -> Function -> Object Storage -> Windows transport acceptance passed 2026-08-09;
- one real **ChatGPT-originated** call through the private GPT Action remains the final Stage 4 exit gate before exposing higher-value local capabilities remotely.

## Transitional code

The Python package is retained only as a behavioral oracle for Rust parity. It is not the target runtime and should be removed only after a deliberate migration gate proves that the remaining oracle adds less value than its maintenance cost.