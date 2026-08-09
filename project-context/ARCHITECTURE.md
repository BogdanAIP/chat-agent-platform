# Architecture

## Target architecture

Chat является primary intelligence. Один локальный Rust binary `agent-platform.exe` превращает намерение Chat в проверяемое выполнение через explicit Project Binding, versioned contracts и fail-closed policy. Зрелые программы и сетевые компоненты остаются заменяемыми edge-инструментами; они не становятся core dependency без необходимости.

Канонического cloud provider нет. Каноничны protocol/security boundaries и открытые MCP contracts.

```text
ChatGPT / Codex / Claude / another MCP-capable caller
        |
        | standard MCP 2026-07-28
        | + optional MCP Apps UI
        v
replaceable reachability layer
        |
        | caller-native private MCP tunnel
        | OR direct/reverse-proxied HTTPS MCP
        | OR generic mature reverse tunnel
        | OR polling-relay compatibility backend
        v
local MCP boundary or outbound polling adapter
        |
        v
agent-platform.exe
        |
        v
Project Binding -> policy -> typed capability -> local executor
```

Examples of replaceable reachability choices include OpenAI Secure MCP Tunnel where available, an own VPS/reverse proxy, a managed container host, frp/zrok-class reverse tunnels, the Rust `relay-server`, and the existing Yandex backend. None of them defines the platform contract.

GitHub остаётся source/project-context каналом для Chat/Codex и не заменяет runtime transport.

Detailed connector boundaries and selection rules: `project-context/CONNECTOR_ARCHITECTURE.md`.

## Core invariants

### One local core, not a service zoo

Project policy, artifact identity, job state, secret ACL and confirmation authority live in the Rust core. Redis, database, message broker, separate workflow engine, VPS and permanent supervisor are not baseline dependencies.

A new process/service is allowed only when an independent lifecycle requirement proves that in-process/file-backed state is insufficient. Network publication/private reachability should reuse mature vendor-native or open-source tunnel/proxy software rather than be reimplemented in the platform.

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
- MCP: use the official Rust MCP SDK rather than expanding a hand-written standards implementation.
- MCP UI: use MCP Apps shared `ui://` / `ui/*` contracts first; host-specific bridges are optional extensions only.
- NAT/private reachability: use mature caller-native/open-source tunnel products; do not build another tunnel stack.

## Provider-neutral connector boundary

### Standard MCP boundary

For MCP-capable callers the target interface is standard MCP. MCP protocol details are an external standard, not project business logic. The target Rust implementation should therefore use the official `rmcp` SDK and keep project-specific authorization/tool dispatch behind that adapter.

The MCP `2026-07-28` architecture is intentionally friendly to ordinary HTTP infrastructure and first-class extensions. Hosting choice must not leak into capability names, Project Binding, policy, jobs or artifacts.

### Portable UI: MCP Apps

When a tool benefits from an interactive surface, use MCP Apps rather than a ChatGPT-only UI contract.

```text
typed MCP tool
  -> optional _meta.ui.resourceUri
  -> ui:// HTML resource
  -> compatible host renders sandboxed UI
  -> ui/* JSON-RPC bridge for tool/input/result/context interaction
```

The same tool must remain useful without UI. Future dashboards, job/progress views, artifact/media inspectors and approval/configuration forms are candidates for MCP Apps only when the UI materially helps.

OpenAI-specific `window.openai` methods or another host-specific API may be feature-detected for capabilities the shared standard does not cover, but they must not become the portable execution contract.

### Preferred OpenAI private path: Secure MCP Tunnel when available

OpenAI now provides Secure MCP Tunnel for supported OpenAI products. A customer-run `tunnel-client` stays inside the private network, makes outbound HTTPS connections to OpenAI, receives queued MCP work, forwards JSON-RPC to a local stdio/HTTP MCP server, and returns responses through the same tunnel.

For ChatGPT/Codex this directly overlaps the problem that originally motivated our custom Yandex polling relay. Therefore, when the user's actual OpenAI account/plan and cost policy support Secure MCP Tunnel, prefer:

```text
ChatGPT / Codex
  -> OpenAI-hosted MCP tunnel endpoint
  -> outbound tunnel-client on Windows/private network
  -> loopback local rmcp MCP server
  -> agent-platform policy + typed execution
```

No public listener, VPS, Yandex function or third-party tunnel is needed in that path.

Secure MCP Tunnel is still an OpenAI-specific deployment adapter, not the universal core. It currently depends on OpenAI Platform tunnel identity/runtime credentials, so the architecture must not assume that a ChatGPT subscription alone provides or pays for this access.

### Generic private/remote MCP path

For other MCP hosts, or when OpenAI Secure MCP Tunnel is unavailable/inappropriate, expose the same local MCP server through mature infrastructure:

```text
remote MCP caller
  -> HTTPS MCP endpoint
  -> mature reverse tunnel/proxy
  -> loopback local MCP server
  -> agent-platform policy + typed execution
```

This path does not need a custom task database or rendezvous relay. frp is a self-hosted reference when the operator already has any ordinary VPS; zrok is an optional managed/self-hosted zero-trust class. Equivalent mature vendor-native tunnels are allowed.

### Polling relay compatibility path

The existing Windows transport remains valuable where standard/private MCP reachability is unavailable, undesirable or unsupported by the caller/provider.

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

The Rust relay-server must remain a thin compatibility backend. It must not grow into a custom replacement for MCP SDKs, Secure MCP Tunnel, reverse tunnels, TLS automation or generic cloud orchestration.

### GPT Action compatibility

The private GPT Action/OpenAPI path remains working compatibility infrastructure. It should no longer drive new core design now that MCP Apps/standard MCP are the portable target and OpenAI has an official private MCP tunnel option.

Do not delete the GPT Action/Yandex path until a replacement standard MCP path passes real acceptance on the user's actual ChatGPT plan/account. Yandex API Gateway was required by that specific Yandex deployment because of its Authorization-header behavior; this is not a platform invariant.

### Credentials

For polling relay deployments, two independent credentials remain mandatory:

- remote caller credential -> public relay ingress;
- local agent credential -> stored in Windows Credential Manager and used only by the outbound Windows worker.

For standard MCP tunnels, transport authentication follows the selected MCP/tunnel adapter and must still fail closed before local capability dispatch. Tunnel identity never replaces local Project Binding/policy authorization.

## Stage 4 evidence interpretation

The 2026-08-09 Yandex API Gateway -> Function -> Object Storage -> Windows acceptance proves that **one polling-relay backend implementation** can complete the transport contract. It is historical evidence, not a declaration that Yandex is canonical.

The provider-neutral Rust `relay-server` proves a second server implementation at CI/integration level. Provider portability is fully proved only after the same real remote -> local acceptance is run through at least one non-Yandex deployment path.

The preferred next real acceptance should test the standard local MCP boundary first and then the best reachability adapter actually available to the user's account: OpenAI Secure MCP Tunnel if available/acceptable; otherwise a generic standard-MCP path. This avoids building another custom network layer.

Until the final Hosted Chat-originated acceptance passes, remotely exposed local capabilities remain limited to the Stage 4 allowlist.

## Transitional code

The Python package is retained only as a behavioral oracle for Rust parity. It is not the target runtime and should be removed only after a deliberate migration gate proves that the remaining oracle adds less value than its maintenance cost.

Yandex-specific gateway code, deployment scripts and documentation remain as a tested adapter until replacement/deprecation is deliberate. They are not source-of-truth architecture.
