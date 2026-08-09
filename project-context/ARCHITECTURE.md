# Architecture

## Target architecture

Chat является primary intelligence. Один локальный Rust binary `agent-platform.exe` превращает намерение Chat в проверяемое выполнение через explicit Project Binding, versioned contracts и fail-closed policy. Зрелые программы и сетевые компоненты остаются заменяемыми edge-инструментами; они не становятся core dependency без необходимости.

Канонического cloud provider нет. Каноничны protocol/security boundaries и открытые MCP contracts.

```text
ChatGPT / Codex / Claude / another MCP-capable caller
        |
        | standard MCP
        | + optional MCP Apps UI
        v
replaceable reachability layer
        |
        | public HTTPS MCP
        | OR caller-native private MCP tunnel
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

Examples of replaceable reachability choices include an ordinary public HTTPS endpoint, OpenAI Secure MCP Tunnel when private reachability is useful and available, an own VPS/reverse proxy, a managed container host, frp/zrok-class reverse tunnels, the Rust `relay-server`, and the existing Yandex backend. None of them defines the platform contract.

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

For MCP-capable callers the target interface is standard MCP. MCP protocol details are an external standard, not project business logic. The target Rust implementation should use the official `rmcp` SDK and keep project-specific authorization/tool dispatch behind that adapter.

Hosting choice must not leak into capability names, Project Binding, policy, jobs or artifacts.

### Portable UI: MCP Apps

When a tool benefits from an interactive surface, use MCP Apps rather than a ChatGPT-only UI contract.

```text
typed MCP tool
  -> optional _meta.ui.resourceUri
  -> ui:// HTML resource
  -> compatible host renders sandboxed UI
  -> ui/* bridge for tool/input/result/context interaction
```

The same tool must remain useful without UI. Future dashboards, job/progress views, artifact/media inspectors and approval/configuration forms are candidates for MCP Apps only when the UI materially helps.

Host-specific UI methods may be feature-detected for capabilities the shared standard does not cover, but they must not become the portable execution contract.

### Primary remote path: public standard MCP HTTPS

Current OpenAI plugin developer documentation explicitly supports a public HTTPS Streamable HTTP MCP endpoint, normally `/mcp`, as a direct connection method. Therefore the primary portability target is:

```text
ChatGPT Work / Codex / other MCP client
  -> public HTTPS /mcp
  -> standard rmcp server
  -> agent-platform policy + typed execution
```

The public endpoint may be an ordinary VPS/reverse proxy, managed container host or mature reverse tunnel. The platform owns none of those hosting products.

### Optional OpenAI private path: Secure MCP Tunnel

OpenAI Secure MCP Tunnel is useful when the local MCP server should remain private. A customer-run `tunnel-client` makes outbound HTTPS connections to OpenAI, receives MCP work and forwards it to a local stdio/HTTP MCP server.

It is **not required** when a public HTTPS MCP endpoint is acceptable. It is also OpenAI-specific and depends on separate OpenAI Platform tunnel/runtime credentials, so a ChatGPT subscription must not be assumed to include or pay for it.

Treat Secure MCP Tunnel as a deployment adapter selected for private reachability, never as the core architecture.

### Generic private/remote MCP path

For other MCP hosts, or when a public endpoint needs a transparent path to a local loopback server, use mature infrastructure:

```text
remote MCP caller
  -> HTTPS MCP endpoint
  -> mature reverse tunnel/proxy
  -> loopback local MCP server
  -> agent-platform policy + typed execution
```

frp is a self-hosted reference when the operator already has an ordinary VPS; zrok is an optional managed/self-hosted zero-trust class. Equivalent mature tools remain allowed.

### Polling relay compatibility path

The existing Windows transport remains valuable where standard MCP reachability is unavailable, undesirable or unsupported.

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

### GPT Action / legacy app compatibility

The existing OpenAPI/GPT Action-compatible Yandex path remains working compatibility infrastructure. It should no longer drive new core design.

Do not delete it until a replacement standard MCP path passes real acceptance on the user's actual ChatGPT surface. Yandex API Gateway requirements are properties of that adapter, not platform invariants.

## Stage 4 evidence interpretation

Stage 4's original Hosted Chat -> local execution requirement is complete.

On 2026-08-06, the installed ChatGPT integration `Music Video MCP Yandex Test` successfully executed `local_ping` and returned the real local Windows agent response (`ID182019`, Windows 11, agent `0.2.1`) back into ChatGPT. This proves the Hosted Chat -> remote integration -> Windows -> Hosted Chat round trip.

On 2026-08-09, the current Yandex polling backend separately passed `local_ping`, `runtime_self_test`, controlled write/read, cleanup and clean shutdown. A later ChatGPT-originated offline test correctly returned `agent_offline` while the local agent was stopped.

The provider-neutral Rust `relay-server` proves another backend implementation at CI/integration level.

What is **not** yet proved is that the historical installed integration used today's standard MCP Streamable HTTP `/mcp` connection. That is a connector migration question, not an unfinished Stage 4 gate.

## Connector migration gates

Before deprecating Yandex/GPT Action compatibility:

1. implement the standard local MCP server using current official `rmcp`;
2. expose it through one normal public HTTPS `/mcp` endpoint;
3. add/call that endpoint from the user's real ChatGPT Work/plugin surface;
4. prove one non-Yandex remote -> Windows round trip;
5. only then decide whether legacy polling/Yandex infrastructure can be removed.

Secure MCP Tunnel may be tested separately if private reachability is useful. It is not a prerequisite for steps 1–4.

## Transitional code

The Python package is retained only as a behavioral oracle for Rust parity. It is not the target runtime and should be removed only after a deliberate migration gate proves that the remaining oracle adds less value than its maintenance cost.

Yandex-specific gateway code, deployment scripts and documentation remain as a tested adapter until replacement/deprecation is deliberate. They are not source-of-truth architecture.
