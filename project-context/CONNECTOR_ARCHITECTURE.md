# Provider-neutral connector architecture

## Purpose

The project does not have a canonical cloud provider. Yandex Cloud, an ordinary VPS, a managed container host, a vendor-native private tunnel, and any future hosting option are deployment choices, not platform architecture.

The canonical boundaries are open protocols and local security contracts:

1. **Local execution boundary** — `agent-platform.exe` owns Project Binding, policy, secrets, confirmations, typed capabilities, artifacts and jobs.
2. **Remote tool boundary** — standard MCP is the preferred external tool protocol for MCP-capable callers.
3. **Portable UI boundary** — MCP Apps is the provider-agnostic UI extension when a capability benefits from interactive UI inside the host.
4. **Private reachability boundary** — use a mature caller-native/private tunnel when available; do not reimplement tunnel infrastructure in the platform.
5. **Polling relay boundary** — `relay-request-v1` / `relay-response-v1` plus `poll/result/offline` remains a compatibility transport for environments where standard MCP reachability is unavailable or where serverless request/response hosting is deliberately used.

No provider name is allowed to become part of the local capability contract.

## Target shape

```text
ChatGPT / Codex / Claude / another MCP client
        |
        | standard MCP
        | + optional MCP Apps UI metadata/resources
        v
replaceable reachability layer
        |
        | one of:
        | - public HTTPS MCP endpoint
        | - caller-native private MCP tunnel
        | - mature third-party/self-hosted reverse tunnel
        | - polling-relay compatibility adapter
        v
local MCP boundary / relay adapter
        |
        v
agent-platform.exe
        |
        v
policy -> typed capability -> local executor
```

The preferred path is the shortest mature path that preserves the security model and does not introduce an unnecessary network operator.

## Open standards we should adopt instead of recreating

### Core MCP

For MCP-capable callers, the platform should expose a standard MCP endpoint and rely on the official Rust MCP SDK (`rmcp`) rather than maintaining a hand-written implementation of evolving MCP protocol details.

The concrete HTTP transport/version is implemented and negotiated by the SDK/current MCP specification. Project business logic must remain behind an adapter so a future MCP protocol revision does not rewrite local capability code.

### MCP Apps

MCP Apps is the portable UI layer for MCP tools. It allows a tool to associate a `ui://` resource with the tool and lets compatible hosts render the UI in a sandboxed iframe using the shared `ui/*` bridge.

Project rule:

- use MCP Apps shared fields/methods for portable UI;
- do not make `window.openai`, Claude-specific bridges, Vercel-specific APIs or another host name the primary UI contract;
- host-specific extensions may be feature-detected only when the shared MCP Apps specification does not cover the capability;
- tools must remain useful without UI so non-rendering MCP clients can still execute the workflow.

Future dashboards, approval forms, media preview panels, job progress views and artifact inspectors should therefore use MCP Apps when an interactive surface is actually useful.

## Connection profiles

### 1. `mcp-local`

Canonical local protocol profile.

- standard MCP server implemented with `rmcp`;
- loopback/private binding by default;
- local Project Binding and policy remain authoritative;
- only typed allowlisted capabilities are exported;
- MCP Apps resources are optional extensions of selected tools, not a second execution API.

This local server is the stable target that different reachability mechanisms connect to.

### 2. `public-mcp-https`

Preferred portable remote profile when the caller accepts a normal remote MCP server.

OpenAI's current plugin development flow accepts a public HTTPS Streamable HTTP MCP endpoint (normally `/mcp`) directly. Therefore an OpenAI-specific tunnel is not required when a stable HTTPS endpoint is already available and acceptable.

The endpoint may be supplied by an ordinary VPS/reverse proxy, a managed container host, or a mature reverse tunnel. The platform does not care which one as long as standard MCP HTTP semantics and authentication are preserved.

### 3. `openai-secure-mcp-tunnel`

Optional OpenAI-specific private reachability adapter when the user's account and OpenAI Platform tunnel access support it.

OpenAI Secure MCP Tunnel is an outbound-only tunnel client. It runs inside the user's network, long-polls the OpenAI-hosted tunnel control plane, forwards standard MCP JSON-RPC to a private local MCP server, and returns responses through the same path. The local MCP server does not need a public listener or inbound firewall port.

This directly overlaps the networking problem that originally motivated the Yandex polling relay, but it is **not** the canonical OpenAI path and is not required for a public HTTPS MCP plugin connection.

Rules:

- use it when private reachability is materially preferable and the user's account/Platform access permits it;
- keep it outside the Rust core as a deployment adapter;
- do not assume a ChatGPT subscription includes Platform tunnel credentials;
- preserve a provider-neutral fallback.

### 4. `generic-tunneled-mcp`

Standard local MCP endpoint published through a mature non-OpenAI tunnel/reverse proxy.

Reference classes, not core dependencies:

- self-hosted reverse tunnel such as **frp** when the operator already has an ordinary VPS;
- managed/self-hosted zero-trust sharing such as **zrok**;
- another host/vendor-native secure MCP tunnel that preserves standard MCP semantics.

The platform must not reimplement NAT traversal, tunnel multiplexing, certificate automation or public routing already supplied by mature products.

### 5. `polling-relay-http-v1`

Compatibility profile implemented today by the local Windows agent.

The local agent is already provider-neutral:

- configuration stores only `endpoint` + `secret_ref`;
- any public `https://` endpoint is accepted;
- outbound requests use the same `X-Agent-Token` and JSON contract;
- operations are `poll`, `result` and `offline`;
- task execution remains local and policy-gated.

Server implementations can therefore be swapped without changing the Windows runtime contract:

- current Rust `relay-server` on an ordinary VPS;
- current Yandex Function/Object Storage implementation;
- a future serverless implementation on another provider;
- any compatible implementation that passes the same acceptance suite.

This profile remains useful as a provider-neutral fallback where a standard/private MCP path is unavailable. It should not grow into a custom replacement for standard MCP networking.

## What the existing ChatGPT/Yandex test already proves

The project already has real Hosted Chat evidence that must not be lost between sessions.

On 2026-08-06, the installed ChatGPT integration `Music Video MCP Yandex Test` successfully executed `local_ping` through the Yandex-hosted gateway and returned a response from the local Windows agent (`ID182019`, Windows 11, agent `0.2.1`, message `Проверка локального агента`) back into ChatGPT. This proves the functional round trip:

```text
ChatGPT
  -> installed plugin/app tool
  -> public Yandex gateway
  -> outbound local-agent path
  -> Windows execution
  -> response back to ChatGPT
```

A later 2026-08-09 `runtime_self_test` reported `agent_offline`; that is expected offline behavior and does not invalidate the earlier successful round trip.

The current ChatGPT control plane also reports this installed integration with app-specific `Allow all actions` permission. Therefore the project must not infer from generic plan documentation that this user's real ChatGPT account is read-only.

However, this evidence does **not by itself prove that the installed integration used the current standard MCP Streamable HTTP `/mcp` path**. The earlier Yandex gateway had compatibility surfaces, and the exact historical connection metadata is not available in the repository. Treat these as two separate facts:

1. **Hosted Chat -> Yandex -> Windows -> Hosted Chat is proved.**
2. **Native standard MCP `/mcp` on the user's current ChatGPT Plus/Work surface still needs one direct acceptance test.**

That second test is a migration/portability gate, not an excuse to keep Stage 4's original Hosted Chat round-trip marked incomplete.

## Existing adapters and their status

### Rust relay-server

`crates/relay-server` is a provider-neutral implementation of `polling-relay-http-v1`. It can run on an ordinary Linux host and keeps only short-lived relay state. It remains useful as a fallback/reference backend, but it should not grow into a general tunnel or MCP framework.

### Yandex backend

The Yandex API Gateway / Cloud Function / Object Storage path is retained as a tested deployment adapter and historical Stage 4 acceptance backend. Yandex-specific scripts and templates remain under `gateway/` and `scripts/` but do not define the target architecture.

### GPT Action / legacy app compatibility

The existing OpenAPI/GPT Action-compatible ingress is legacy/compatibility infrastructure. It must not drive new core design now that the target interface is standard MCP.

Do not delete the working Yandex compatibility path until the replacement standard MCP path has passed real acceptance on the user's actual ChatGPT surface.

## Reuse policy

Use mature implementations before building infrastructure:

- MCP protocol/server transport: official `modelcontextprotocol/rust-sdk` (`rmcp`);
- portable embedded UI: MCP Apps specification and its shared metadata/bridge contract;
- public remote MCP: ordinary HTTPS Streamable HTTP endpoint;
- private OpenAI reachability: OpenAI Secure MCP Tunnel when actually useful and available;
- generic NAT/reverse tunnel on own VPS: mature tools such as `frp`;
- managed/self-hosted zero-trust tunnel: mature tools such as `zrok`;
- stdio/SSE/Streamable-HTTP bridging for third-party MCP servers: use an existing MCP proxy only when an actual compatibility need appears;
- custom polling relay: retain as compatibility/fallback, not as the universal answer.

Do not add a generic provider SDK, custom tunnel daemon, message broker, Redis, or cloud abstraction framework to the core.

## Selection rule

Choose the connection path at deployment time:

```text
Can the caller use standard remote MCP over public HTTPS?
  yes -> use the standard /mcp endpoint; choose any compatible hosting/tunnel
  no  -> continue below

Does the caller provide a mature private MCP tunnel?
  yes -> use it if account/cost/security constraints fit
  no  -> use a mature generic tunnel/reverse proxy

Can neither standard tunnel path be used?
  -> use polling-relay-http-v1 on any compatible HTTPS host
```

For OpenAI specifically:

```text
ChatGPT Work/plugin surface accepts our public standard /mcp endpoint
  -> use public/tunneled standard MCP; no OpenAI tunnel required

Public endpoint undesirable + Secure MCP Tunnel available
  -> local rmcp server + tunnel-client

Neither available on the user's actual surface
  -> retain the already-proved plugin/Yandex compatibility path while investigating supported alternatives
```

Cost, region, plan availability and user preference choose the deployment adapter. They do not change the local platform protocol.

## Migration plan

1. Treat current local `endpoint + secret_ref` polling client as already provider-neutral; do not add provider enums.
2. Record the 2026-08-06 ChatGPT -> plugin -> Yandex -> Windows successful round trip as completed Stage 4 evidence.
3. Keep Yandex acceptance evidence as evidence for one backend implementation, not as canonical architecture.
4. Keep the Rust relay-server as the provider-neutral polling-relay reference implementation/fallback.
5. Add a standard local MCP server using official `rmcp` in a separate code change.
6. Expose that server through one normal public HTTPS `/mcp` endpoint and test it directly from the user's real ChatGPT Work/plugin surface.
7. If that succeeds, use the same MCP server as the common target for ChatGPT/Codex/other MCP clients.
8. Add MCP Apps only for concrete tools that benefit from interactive UI; keep execution usable without UI.
9. Test Secure MCP Tunnel only as an optional private-connection profile, not as a prerequisite.
10. Run one non-Yandex remote -> Windows acceptance before claiming provider portability end-to-end.
11. Remove/deprecate GPT Action/Yandex compatibility only after the replacement standard MCP path proves the same real Hosted Chat -> Windows round trip.

## Acceptance invariants

A connector/backend is accepted only if it proves:

- no inbound port is required on the user's Windows router/firewall unless the user explicitly chooses direct hosting;
- remote caller cannot bypass local Project Binding/policy/allowlists;
- `local_ping` proves real local execution;
- `runtime_self_test` succeeds through the full path when the agent is online;
- disabling/stopping local connectivity produces a structured offline/unavailable result;
- backend replacement requires configuration/deployment change, not changes to local capability code;
- MCP Apps UI, when present, is optional and does not become execution authority;
- plan/API requirements are explicit rather than silently assuming that a ChatGPT subscription includes OpenAI Platform API/tunnel access.
