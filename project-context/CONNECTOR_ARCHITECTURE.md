# Provider-neutral connector architecture

## Purpose

The project does not have a canonical cloud provider or a custom networking stack. Yandex Cloud, an ordinary VPS, a managed container host, an outbound tunnel, and any future hosting option are deployment choices, not platform architecture.

The canonical boundaries are open protocols and local security contracts:

1. **Local execution boundary** — `agent-platform.exe` owns Project Binding, policy, secrets, confirmations, typed capabilities, artifacts and jobs.
2. **Remote tool boundary** — standard MCP is the preferred external tool protocol for MCP-capable callers; the existing OpenAPI action surface is compatibility for the currently proven ChatGPT path.
3. **Portable UI boundary** — MCP Apps is the provider-agnostic UI extension when a capability benefits from interactive UI inside the host.
4. **Reachability boundary** — NAT traversal, public HTTPS, TLS and outbound-only delivery are commodity infrastructure and must use mature tunnel/proxy products rather than project code.
5. **Polling relay boundary** — `relay-request-v1` / `relay-response-v1` plus `poll/result/offline` is retained only as compatibility/fallback where transparent reachability cannot be used or a future independent queue lifecycle is actually required.

No provider or tunnel product name is allowed to become part of the local capability contract.

## Target shape

```text
ChatGPT / Codex / Claude / another client
        |
        | standard MCP
        | OR existing OpenAPI action compatibility
        | + optional MCP Apps UI
        v
mature reachability component
        |
        | public HTTPS tunnel/proxy directly to localhost
        | OR caller-native private tunnel
        | OR self-hosted reverse tunnel/proxy
        | OR polling-relay fallback
        v
loopback local protocol adapter
        |
        v
agent-platform.exe
        |
        v
policy -> typed capability -> local executor
```

The preferred path is the shortest mature path that preserves the security model. A cloud relay is not required merely because the Windows machine is behind NAT.

## What is already solved outside this project

### Standard tool protocol

Use the official Rust MCP SDK (`rmcp`) for the platform's standard MCP server. Do not maintain a hand-written implementation of evolving MCP protocol rules.

### Portable UI

Use MCP Apps shared `ui://` resources and `ui/*` bridge semantics for optional interactive surfaces. Host-specific APIs are optional feature-detected extensions only.

### Secure delivery to localhost

The networking problem is already solved by mature products:

- **OpenAI Secure MCP Tunnel**: outbound HTTPS from a customer-run open-source `tunnel-client`, with queued MCP work forwarded to a configured local stdio/HTTP MCP server. Use only when OpenAI Platform tunnel access is available and private reachability is desired.
- **Tailscale Funnel**: managed public HTTPS endpoint with a stable `*.ts.net` hostname, automatically provisioned TLS and encrypted relay to a local Windows HTTP service. Suitable for personal/development integration when the local endpoint enforces strong application authentication and fail-closed policy.
- **zrok**: Apache-2.0, cross-platform public/private sharing through NAT/firewalls with self-hosting available.
- **Cloudflare Tunnel**: outbound-only public ingress with no inbound ports; optional where regional/network conditions make it reliable.
- **frp / equivalent self-hosted reverse tunnels**: use when the operator already has a VPS and wants full control.

The platform must not implement NAT traversal, tunnel multiplexing, certificate issuance, relay routing or public DNS that these products already provide.

A transparent tunnel can carry either standard MCP or the existing OpenAPI action request. Therefore even the current Plus-compatible action path can, in principle, be:

```text
ChatGPT action/plugin
  -> stable public HTTPS tunnel URL
  -> localhost action adapter on Windows
  -> agent-platform policy + typed execution
```

with no Yandex Function, Object Storage, VPS task database or custom polling protocol in the request path.

## Security boundary

A tunnel solves **reachability and transport encryption**. It does not grant execution authority.

The local adapter remains responsible for:

- strong caller authentication before dispatch;
- bounded request body/concurrency/timeouts;
- Project Binding;
- exact tool/capability allowlists;
- policy/risk evaluation;
- one-use confirmations for external side effects;
- secret ACLs;
- audit/result contracts.

For public native MCP plugins that access private data or take actions, follow MCP authorization requirements rather than inventing a parallel auth protocol. For the legacy OpenAPI action compatibility path, the existing high-entropy API-key model can remain until that path is retired.

## Connection profiles

### `mcp-local`

Canonical local protocol profile:

- standard MCP server implemented with `rmcp`;
- loopback binding by default;
- Project Binding/policy remain authoritative;
- only typed allowlisted capabilities are exported;
- MCP Apps resources are optional UI, never execution authority.

### `direct-public-tunnel`

Preferred near-term migration profile for the user's current ChatGPT setup when a public endpoint is acceptable.

A mature tunnel publishes the loopback adapter directly. No project-owned relay state exists in the middle.

First acceptance candidate: Tailscale Funnel because it supports Windows, stable HTTPS names and all pricing plans. zrok is the open-source/self-hostable alternative. The selected tunnel is an operator choice, not a dependency.

### `public-mcp-https`

For public/production MCP, deploy a stable public HTTPS Streamable HTTP endpoint. OpenAI public plugin submission explicitly requires a stable publicly reachable MCP endpoint; development/private tunnels are not a substitute for published production hosting.

### `openai-secure-mcp-tunnel`

Optional OpenAI-specific private reachability. Use when the MCP server should remain private and the user's Platform/workspace tunnel access permits it. It is not required for public HTTPS MCP and not assumed to be part of ChatGPT subscription billing.

OpenAI's tunnel also includes a narrowly scoped Harpoon MCP server for configured private REST targets. This reinforces the design rule that the project should not build a general private HTTP bridge merely to reach a small set of local endpoints.

### `polling-relay-http-v1`

Legacy compatibility/fallback implemented today by the Windows worker and Rust/Yandex relay backends.

Keep it because it is already tested and may still help where all transparent tunnels are blocked or if an independent queue lifecycle later becomes a real requirement. Do not expand it into the preferred architecture.

## What the existing ChatGPT/Yandex test proves

On 2026-08-06, the installed ChatGPT integration `Music Video MCP Yandex Test` successfully executed `local_ping` through the Yandex-hosted path and returned a response from the local Windows agent (`ID182019`, Windows 11, agent `0.2.1`) back into ChatGPT.

Therefore Hosted Chat -> remote integration -> Windows execution -> Hosted Chat is proved. Stage 4 is complete.

A later offline result on 2026-08-09 is valid offline behavior, not a failed historical acceptance.

The historical connection metadata is not sufficient to claim that this call used today's native MCP Streamable HTTP path, so native `/mcp` remains a migration test rather than a Stage 4 gate.

## Selection rule

```text
Can the caller reach a normal public HTTPS endpoint?
  yes -> expose the local adapter through a mature tunnel/proxy or stable hosted endpoint
         -> no custom relay
  no  -> continue

Does the caller provide a private outbound tunnel?
  yes -> use it if account/cost/security constraints fit
  no  -> use another mature reverse tunnel

Are transparent tunnels unavailable/blocked, or is an independent queue lifecycle required?
  yes -> polling-relay-http-v1 fallback
```

Protocol is independent of reachability:

```text
native MCP available -> /mcp via rmcp
legacy/current ChatGPT action path -> OpenAPI action adapter
```

Both can use the same mature HTTPS tunnel and the same local policy/execution core.

## Migration plan

1. Preserve the already-proved Yandex path only as rollback evidence; stop treating it as target infrastructure.
2. Implement one loopback local server adapter in the Rust core, with shared tool dispatch behind protocol-specific adapters.
3. Add standard MCP using official `rmcp`.
4. Keep a minimal OpenAPI action-compatible endpoint for the user's currently proven Plus plugin path until native MCP is accepted on that account.
5. Expose the loopback server directly through a mature public HTTPS tunnel and prove ChatGPT -> tunnel -> Windows -> ChatGPT without Yandex/VPS relay state.
6. Test native `/mcp` from the user's actual ChatGPT plugin surface when developer-mode access permits it.
7. Add MCP Apps only for concrete interactive tools.
8. Test OpenAI Secure MCP Tunnel only if private OpenAI reachability is useful and available.
9. After direct-tunnel and native-MCP acceptance, demote `relay-server`/Yandex deployment assets to legacy/fallback and consider removal in a separate compatibility decision.

## Acceptance invariants

A connector path is accepted only if:

- no inbound router/firewall port is required unless explicitly chosen;
- transport is HTTPS/encrypted;
- unauthenticated requests cannot reach local capability dispatch;
- remote caller cannot bypass Project Binding/policy/allowlists;
- `local_ping` proves real local execution;
- `runtime_self_test` succeeds when the agent is online;
- stopping the local adapter/tunnel produces a clean unavailable/offline result;
- changing tunnel/hosting provider requires configuration/deployment changes only;
- optional MCP Apps UI never becomes execution authority.
