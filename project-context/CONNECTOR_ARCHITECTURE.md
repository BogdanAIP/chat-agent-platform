# Provider-neutral connector architecture

## Purpose

The project does not have a canonical cloud provider. Yandex Cloud, an ordinary VPS, a managed container host, a reverse tunnel, and any future hosting option are deployment choices, not platform architecture.

The canonical boundaries are protocols and contracts:

1. **Local execution boundary** — `agent-platform.exe` owns Project Binding, policy, secrets, confirmations, typed capabilities, artifacts and jobs.
2. **Remote tool boundary** — standard MCP Streamable HTTP is the preferred external protocol for MCP-capable callers.
3. **Polling relay boundary** — `relay-request-v1` / `relay-response-v1` plus `poll/result/offline` remains a compatibility transport for environments where the local machine cannot be reached through a normal reverse tunnel or where serverless request/response hosting is deliberately used.
4. **Network publication** — tunnel, reverse proxy, VPS, serverless relay or provider-specific ingress is replaceable deployment infrastructure.

No provider name is allowed to become part of the local capability contract.

## Target shape

```text
ChatGPT / Codex / another MCP client
        |
        | MCP Streamable HTTP 2026-07-28
        v
provider-neutral public ingress
        |
        | one of:
        | - direct HTTPS
        | - reverse tunnel (frp / zrok / supported vendor tunnel)
        | - reverse proxy on any VPS/container host
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

The preferred path is the shortest one that preserves the security model. A separate cloud relay is not required when a trustworthy outbound reverse tunnel can expose the local MCP endpoint safely.

## Connection profiles

### 1. `mcp-http`

Preferred protocol profile for MCP-capable clients.

- one standard Streamable HTTP MCP endpoint;
- protocol implementation should use the official Rust MCP SDK (`rmcp`) instead of maintaining a second hand-written MCP stack;
- local service binds to loopback by default;
- authentication and Origin validation remain fail-closed;
- the public endpoint may be provided by any reverse proxy/tunnel/host that preserves HTTP semantics.

The MCP 2026-07-28 transport is stateless at the protocol level: each JSON-RPC message is sent as its own POST and protocol sessions/standalone GET stream are removed. This makes ordinary HTTP proxies and replaceable ingress practical.

### 2. `tunneled-mcp-http`

Same MCP endpoint, published through an outbound tunnel from the user machine.

Recommended mature options:

- **frp** — default self-hosted option when the operator already has any VPS. It is a mature Apache-2.0 reverse proxy designed to expose services behind NAT/firewalls and supports HTTP/HTTPS/TCP.
- **zrok** — optional managed or self-hosted zero-trust sharing path. It is Apache-2.0, cross-platform and works through NAT/firewalls without opening inbound ports on the user machine.
- **vendor-native secure tunnel** — optional when the caller platform provides one and the user's product plan supports it. It must remain an edge integration, never a core dependency.

The platform must not reimplement NAT traversal, tunnel multiplexing, certificate automation or public routing already supplied by these projects.

### 3. `polling-relay-http-v1`

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

This profile is useful when a reverse tunnel is unavailable, undesirable, or unsupported by the caller. It is not the canonical cloud architecture.

## What is and is not interchangeable

"Any HTTP" means any deployment capable of preserving one of the supported contracts. It does **not** mean an arbitrary static web endpoint automatically becomes a connector.

A remote path is compatible when it provides one of:

- standard MCP Streamable HTTP;
- transparent HTTP forwarding to a standard MCP endpoint;
- the project's `polling-relay-http-v1` compatibility contract.

Changing hosting provider must not require changing capability names, local policies, artifact/job semantics, or the local execution engine.

## Existing adapters and their status

### Rust relay-server

`crates/relay-server` is a provider-neutral implementation of `polling-relay-http-v1`. It can run on an ordinary Linux host and keeps only short-lived relay state. It remains useful as a fallback/compatibility backend, but it should not grow into a general tunnel or MCP framework.

### Yandex backend

The Yandex API Gateway / Cloud Function / Object Storage path is retained as a tested deployment adapter and historical Stage 4 acceptance backend. Yandex-specific scripts and templates remain under `gateway/` and `scripts/` but do not define the target architecture.

### GPT Action compatibility

The existing OpenAPI/GPT Action ingress remains a compatibility surface for ChatGPT environments where that is the available integration path. It does not define the transport architecture and can point at any compatible HTTPS backend.

## Reuse policy

Use mature implementations before building infrastructure:

- MCP protocol/Streamable HTTP: official `modelcontextprotocol/rust-sdk` (`rmcp`);
- NAT/reverse tunnel on own VPS: `frp`;
- managed/self-hosted zero-trust tunnel: `zrok`;
- stdio/SSE/Streamable-HTTP bridging for third-party MCP servers: use an existing MCP proxy only when an actual compatibility need appears;
- custom polling relay: retain only because serverless/outbound-poll scenarios are materially different from a transparent reverse tunnel.

Do not add a generic provider SDK, tunnel daemon, message broker, Redis, or cloud abstraction framework to the core.

## Selection rule

Choose the connection path at deployment time:

```text
Can the caller use standard remote MCP?
  yes -> expose local MCP via the safest available direct/tunnel path
  no  -> use caller-specific compatibility ingress (for example GPT Action)

Can an outbound reverse tunnel be used?
  yes -> prefer transparent tunneled MCP; no custom relay needed
  no  -> use polling-relay-http-v1 on any compatible HTTPS host
```

Cost, region, availability and user preference choose the deployment backend. They do not change the platform protocol.

## Migration plan

1. Treat current local `endpoint + secret_ref` polling client as already provider-neutral; do not add provider enums.
2. Stop describing Yandex as the canonical Stage 4 transport in source-of-truth documents.
3. Keep Yandex acceptance evidence as evidence for one backend implementation.
4. Keep the Rust relay-server as the provider-neutral polling-relay reference implementation.
5. Add a standard local MCP Streamable HTTP server using `rmcp` in a separate change set.
6. Add tunnel deployment recipes only as thin profiles around mature external tools; do not embed/rewrite those tools.
7. Run the same remote allowlist and online/offline acceptance against at least one non-Yandex path before declaring provider portability proven end-to-end.

## Acceptance invariants

A connector/backend is accepted only if it proves:

- no inbound port is required on the user's Windows router/firewall unless the user explicitly chooses direct hosting;
- remote and local-agent credentials remain separate where a polling relay is used;
- remote caller cannot bypass local Project Binding/policy/allowlists;
- `local_ping` proves `executed_locally=true`;
- `runtime_self_test` succeeds through the full path;
- disabling/stopping local connectivity produces a structured offline/unavailable result;
- backend replacement requires configuration change, not changes to local capability code.
