# Architecture

## Target architecture

Chat является primary intelligence. Один локальный Rust binary `agent-platform.exe` превращает намерение Chat в проверяемое выполнение через explicit Project Binding, versioned contracts и fail-closed policy. Зрелые программы и сетевые компоненты остаются заменяемыми edge-инструментами; они не становятся core dependency без необходимости.

Канонического cloud provider нет. Каноничны только protocol/security boundaries.

```text
ChatGPT / Codex / another MCP-capable caller
        |
        | preferred: MCP Streamable HTTP
        | compatibility: GPT Action / polling relay ingress
        v
replaceable public ingress
        |
        | direct HTTPS / reverse tunnel / reverse proxy
        | or polling-relay compatibility backend
        v
local MCP boundary or outbound polling adapter
        |
        v
agent-platform.exe
        |
        v
Project Binding -> policy -> typed capability -> local executor
```

Examples of replaceable ingress/deployment choices include an own VPS, a managed container host, frp/zrok-style reverse tunnels, provider-native secure tunnels when available, the Rust `relay-server`, and the existing Yandex backend. None of them defines the platform contract.

GitHub остаётся source/project-context каналом для Chat/Codex и не заменяет runtime transport.

Detailed connector boundaries and selection rules: `project-context/CONNECTOR_ARCHITECTURE.md`.

## Core invariants

### One local core, not a service zoo

Project policy, artifact identity, job state, secret ACL and confirmation authority live in the Rust core. Redis, database, message broker, separate workflow engine, VPS and permanent supervisor are not baseline dependencies.

A new process/service is allowed only when an independent lifecycle requirement proves that in-process/file-backed state is insufficient. Network publication should reuse mature reverse-proxy/tunnel software rather than be reimplemented in the platform.

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
- MCP: protocol implementation should use the official Rust MCP SDK rather than expanding a hand-written standards implementation.
- NAT/publication: use mature tunnel/reverse-proxy products; do not build another tunnel stack.

## Provider-neutral connector boundary

### Preferred external protocol: MCP Streamable HTTP

For MCP-capable callers the target public interface is standard MCP Streamable HTTP. MCP protocol details are an external standard, not project business logic. The target Rust implementation should therefore use the official `rmcp` SDK and keep project-specific authorization/tool dispatch behind that adapter.

The public MCP endpoint may be exposed through any infrastructure that transparently preserves the required HTTP semantics. Hosting choice must not leak into capability names, Project Binding, policy, jobs or artifacts.

### Transparent reverse tunnel path

When the user machine can establish an outbound tunnel, the simplest architecture is:

```text
remote MCP caller
  -> HTTPS public endpoint
  -> mature reverse tunnel/proxy
  -> loopback local MCP server
  -> agent-platform policy + typed execution
```

This path does not need a custom task database or rendezvous relay. frp is the preferred self-hosted reference when the operator has any ordinary VPS; zrok is an optional managed/self-hosted zero-trust alternative. Other equivalent mature tunnels may be selected by deployment requirements.

### Polling relay compatibility path

The existing Windows transport remains valuable where transparent reverse tunneling is unavailable, undesirable or unsupported by the caller/provider.

Its local contract is already provider-neutral:

```text
agent-platform.exe
  -> HTTPS POST {agent_action: poll}
  <- relay-request-v1 task or no task
  -> local policy-gated execution
  -> HTTPS POST {agent_action: result}
```

Local configuration stores only the HTTPS `endpoint` and a Secret Store reference. The same local binary can therefore point at different compatible server implementations without provider-specific code.

Current implementations:

- `crates/relay-server`: provider-neutral Rust polling relay suitable for an ordinary Linux host;
- Yandex Function/Object Storage: tested provider-specific polling backend retained as an adapter and acceptance reference.

The Rust relay-server must remain a thin compatibility backend. It must not grow into a custom replacement for MCP SDKs, reverse tunnels, TLS automation or generic cloud orchestration.

### GPT Action compatibility

The private GPT Action/OpenAPI path remains supported where it is the available ChatGPT integration. Its HTTPS target is replaceable. Yandex API Gateway was required by one tested Yandex deployment because of that provider's handling of the incoming `Authorization` header; this is a property of that adapter, not a platform invariant.

### Credentials

For polling relay deployments, two independent credentials remain mandatory:

- remote caller credential -> public relay ingress;
- local agent credential -> stored in Windows Credential Manager and used only by the outbound Windows worker.

For transparent MCP tunnels, authentication follows the standard MCP/public-ingress adapter and must still fail closed before local capability dispatch. Tunnel identity never replaces local Project Binding/policy authorization.

## Stage 4 evidence interpretation

The 2026-08-09 Yandex API Gateway -> Function -> Object Storage -> Windows acceptance proves that **one polling-relay backend implementation** can complete the transport contract. It is historical evidence, not a declaration that Yandex is canonical.

The provider-neutral Rust `relay-server` proves a second server implementation at CI/integration level. Provider portability is fully proved only after the same real remote -> local acceptance is run through at least one non-Yandex deployment path.

Until the final Hosted Chat-originated acceptance passes, remotely exposed local capabilities remain limited to the Stage 4 allowlist.

## Transitional code

The Python package is retained only as a behavioral oracle for Rust parity. It is not the target runtime and should be removed only after a deliberate migration gate proves that the remaining oracle adds less value than its maintenance cost.

Yandex-specific gateway code, deployment scripts and documentation remain as a tested adapter until replacement/deprecation is deliberate. They are not source-of-truth architecture.
