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
        | - caller-native private MCP tunnel
        | - direct/reverse-proxied HTTPS MCP endpoint
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

The concrete HTTP transport/version is negotiated/implemented by the SDK and current MCP specification. Project business logic must remain behind an adapter so a future MCP protocol revision does not rewrite local capability code.

### MCP Apps

MCP Apps is the portable UI layer for MCP tools. It allows a tool to associate a `ui://` resource with the tool and lets compatible hosts render the UI in a sandboxed iframe using the shared `ui/*` JSON-RPC bridge.

Project rule:

- use MCP Apps shared fields/methods for portable UI;
- do not make `window.openai`, Claude-specific bridges, Vercel-specific APIs or another host name the primary UI contract;
- host-specific extensions may be feature-detected only when the shared MCP Apps specification does not cover the capability;
- tools must remain useful without UI so non-rendering MCP clients can still execute the workflow.

This means future dashboards, approval forms, media preview panels, job progress views and artifact inspectors should be designed as MCP Apps when an interactive surface is actually useful.

## Connection profiles

### 1. `mcp-local`

Canonical local protocol profile.

- standard MCP server implemented with `rmcp`;
- loopback/private binding by default;
- local Project Binding and policy remain authoritative;
- only typed allowlisted capabilities are exported;
- MCP Apps resources are optional extensions of selected tools, not a second execution API.

This local server is the stable target that different reachability mechanisms connect to.

### 2. `openai-secure-mcp-tunnel`

Preferred OpenAI-specific private reachability adapter **when the user's OpenAI plan/account and Platform tunnel access support it**.

OpenAI Secure MCP Tunnel is an official outbound-only tunnel client. It runs inside the user's network, long-polls the OpenAI-hosted tunnel control plane, forwards standard MCP JSON-RPC to a private local MCP server, and returns responses through the same path. The local MCP server does not need a public listener or inbound firewall port.

This directly overlaps the networking problem that originally motivated the Yandex polling relay. Therefore:

- do not duplicate OpenAI Secure MCP Tunnel for ChatGPT/Codex when it is available and acceptable to the user;
- keep it outside the Rust core as a deployment adapter;
- do not make it the universal platform transport because it is OpenAI-specific and currently requires OpenAI Platform tunnel identity/runtime credentials;
- preserve a provider-neutral fallback for users/plans that cannot or do not want to use it.

### 3. `generic-tunneled-mcp`

Standard local MCP endpoint published through a mature non-OpenAI tunnel/reverse proxy.

Use this for other MCP hosts or when OpenAI Secure MCP Tunnel is unavailable/inappropriate.

Reference classes, not core dependencies:

- self-hosted reverse tunnel such as **frp** when the operator already has an ordinary VPS;
- managed/self-hosted zero-trust sharing such as **zrok**;
- another host/vendor-native secure MCP tunnel that preserves standard MCP semantics.

The platform must not reimplement NAT traversal, tunnel multiplexing, certificate automation or public routing already supplied by mature products.

### 4. `polling-relay-http-v1`

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

This profile remains useful as a provider-neutral fallback where a standard/private MCP path is unavailable. It is no longer the preferred OpenAI path when Secure MCP Tunnel is available.

## What is and is not interchangeable

"Any HTTP" does **not** mean an arbitrary HTTP endpoint automatically becomes a connector.

A remote path is compatible when it provides one of:

- a standards-compliant MCP endpoint;
- transparent forwarding/tunneling to the local MCP endpoint;
- the project's `polling-relay-http-v1` compatibility contract.

Changing hosting/tunnel provider must not require changing capability names, local policies, artifact/job semantics, or the local execution engine.

## Existing adapters and their status

### Rust relay-server

`crates/relay-server` is a provider-neutral implementation of `polling-relay-http-v1`. It can run on an ordinary Linux host and keeps only short-lived relay state. It remains useful as a fallback/reference backend, but it should not grow into a general tunnel or MCP framework.

### Yandex backend

The Yandex API Gateway / Cloud Function / Object Storage path is retained as a tested deployment adapter and historical Stage 4 acceptance backend. Yandex-specific scripts and templates remain under `gateway/` and `scripts/` but do not define the target architecture.

### GPT Action compatibility

The existing OpenAPI/GPT Action ingress is legacy/compatibility infrastructure for environments where it remains the available ChatGPT integration path. It must not drive new core design now that ChatGPT supports MCP-based apps/plugins and OpenAI has an official private MCP tunnel path.

Do not delete the working GPT Action/Yandex path until the replacement MCP path has passed real acceptance on the user's actual plan.

## Reuse policy

Use mature implementations before building infrastructure:

- MCP protocol/server transport: official `modelcontextprotocol/rust-sdk` (`rmcp`);
- portable embedded UI: MCP Apps specification and its shared metadata/bridge contract;
- private OpenAI reachability: OpenAI Secure MCP Tunnel when available to the user's account/plan and acceptable under the project's cost policy;
- generic NAT/reverse tunnel on own VPS: mature tools such as `frp`;
- managed/self-hosted zero-trust tunnel: mature tools such as `zrok`;
- stdio/SSE/Streamable-HTTP bridging for third-party MCP servers: use an existing MCP proxy only when an actual compatibility need appears;
- custom polling relay: retain as compatibility/fallback, not as the universal answer.

Do not add a generic provider SDK, custom tunnel daemon, message broker, Redis, or cloud abstraction framework to the core.

## Selection rule

Choose the connection path at deployment time:

```text
Can the caller use standard MCP?
  no  -> use a caller-specific compatibility ingress only as needed
  yes -> keep the local server standard MCP

Is there a mature caller-native private MCP tunnel?
  yes -> prefer it if plan/cost/security constraints fit
  no  -> use a mature generic tunnel/reverse proxy

Can neither private-tunnel path be used?
  -> use polling-relay-http-v1 on any compatible HTTPS host
```

For OpenAI specifically:

```text
ChatGPT/Codex + Secure MCP Tunnel available and acceptable
  -> local rmcp server + tunnel-client

Secure MCP Tunnel unavailable because of plan/account/cost constraints
  -> standard public/tunneled MCP if the ChatGPT surface supports it
  -> otherwise retain GPT Action / polling relay compatibility until a better supported path exists
```

Cost, region, plan availability and user preference choose the deployment adapter. They do not change the local platform protocol.

## Migration plan

1. Treat current local `endpoint + secret_ref` polling client as already provider-neutral; do not add provider enums.
2. Stop describing Yandex as the canonical Stage 4 transport in source-of-truth documents.
3. Keep Yandex acceptance evidence as evidence for one backend implementation.
4. Keep the Rust relay-server as the provider-neutral polling-relay reference implementation/fallback.
5. Add a standard local MCP server using official `rmcp` in a separate code change.
6. Make the standard MCP server the common target for ChatGPT/Codex/other MCP clients.
7. Add MCP Apps only for concrete tools that benefit from interactive UI; keep execution usable without UI.
8. Test OpenAI Secure MCP Tunnel on the user's real account/plan before relying on it; do not assume Platform tunnel access from ChatGPT subscription alone.
9. If Secure MCP Tunnel is unavailable, test one non-Yandex generic standard-MCP path rather than writing another tunnel.
10. Remove/deprecate GPT Action/Yandex compatibility only after the replacement path proves the same real Hosted Chat -> Windows round trip.

## Acceptance invariants

A connector/backend is accepted only if it proves:

- no inbound port is required on the user's Windows router/firewall unless the user explicitly chooses direct hosting;
- remote caller cannot bypass local Project Binding/policy/allowlists;
- `local_ping` proves `executed_locally=true`;
- `runtime_self_test` succeeds through the full path;
- disabling/stopping local connectivity produces a structured offline/unavailable result;
- backend replacement requires configuration/deployment change, not changes to local capability code;
- MCP Apps UI, when present, is optional and does not become execution authority;
- plan/API requirements are explicit rather than silently assuming that a ChatGPT subscription includes OpenAI Platform API/tunnel access.
